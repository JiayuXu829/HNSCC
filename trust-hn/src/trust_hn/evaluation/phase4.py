"""Phase 4 development-only TRUST-HN residual fusion and reliability gate orchestration."""

from __future__ import annotations

import json
import math
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from trust_hn.data.phase3_features import StudyData, load_phase3_study_data
from trust_hn.evaluation.phase3 import (
    NumericMatrixPreprocessor,
    _assert_aggregate_privacy,
    _infer_columns,
    _missingness_matrix,
    _sha256,
)
from trust_hn.metrics.survival import evaluate_survival_predictions, structured_survival
from trust_hn.models.residual_fusion import StackedResidualSurvivalModel
from trust_hn.models.survival_baselines import (
    SurvivalPrediction,
    TabularPreprocessor,
    fit_predict_survival_model,
)
from trust_hn.reliability.gating import (
    TripleOODDetector,
    assign_actions,
    empirical_percentile,
    equal_weight_score,
    gated_risk,
    quantile_threshold,
)

RAW_RELIABILITY_COLUMNS = (
    "clinical_ood_mahalanobis",
    "clinical_ood_knn",
    "clinical_ood_isolation_forest",
    "clinical_uncertainty_sd",
    "clinical_uncertainty_width95",
    "clinical_model_disagreement",
    "modality_ood_mahalanobis",
    "modality_ood_knn",
    "modality_ood_isolation_forest",
    "fusion_uncertainty_sd",
    "fusion_uncertainty_width95",
    "perturbation_sensitivity",
    "modality_missingness",
    "fusion_disagreement",
)
RANK_SOURCE_COLUMNS = tuple(
    column
    for column in RAW_RELIABILITY_COLUMNS
    if column not in {"clinical_uncertainty_width95", "fusion_uncertainty_width95"}
)


@dataclass(frozen=True)
class BootstrapSummary:
    median: np.ndarray
    sd: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    width: np.ndarray
    successful_models: int
    attempts: int


@dataclass(frozen=True)
class SplitMatrices:
    clinical_fit: np.ndarray
    clinical_eval: np.ndarray
    modality_fit: np.ndarray
    modality_eval: np.ndarray


def _fit_tabular(
    train: pd.DataFrame, evaluation: pd.DataFrame, study: str
) -> tuple[np.ndarray, np.ndarray]:
    numeric, categorical = _infer_columns(train, study)
    preprocessor = TabularPreprocessor(numeric=numeric, categorical=categorical)
    return preprocessor.fit_transform(train), preprocessor.transform(evaluation)


def _split_matrices(
    study: str,
    clinical_fit: pd.DataFrame,
    clinical_eval: pd.DataFrame,
    modality_fit: pd.DataFrame,
    modality_eval: pd.DataFrame,
    config: Mapping[str, object],
) -> SplitMatrices:
    x_clinical_fit, x_clinical_eval = _fit_tabular(clinical_fit, clinical_eval, study)
    if study == "TCGA-HNSC":
        preprocessor = NumericMatrixPreprocessor(
            top_k=int(config.get("tcga_expression_foldwise_variance_top_k", 500))
        )
        x_modality_fit = preprocessor.fit_transform(modality_fit)
        x_modality_eval = preprocessor.transform(modality_eval)
    else:
        x_modality_fit, x_modality_eval = _fit_tabular(modality_fit, modality_eval, study)
    return SplitMatrices(x_clinical_fit, x_clinical_eval, x_modality_fit, x_modality_eval)


def _fit_predict(
    model_id: str,
    x_fit: np.ndarray,
    event_fit: np.ndarray,
    time_fit: np.ndarray,
    x_eval: np.ndarray,
    horizon: float,
    random_state: int,
    config: Mapping[str, object],
) -> SurvivalPrediction:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coefficients are zero.*")
        warnings.filterwarnings("ignore", message=".*did not converge.*")
        return fit_predict_survival_model(
            model_id,
            x_fit,
            structured_survival(event_fit, time_fit),
            x_eval,
            horizon,
            random_state,
            config,
        )


def _cross_fitted_anchor_scores(
    clinical: pd.DataFrame,
    event: np.ndarray,
    time: np.ndarray,
    *,
    study: str,
    folds: int,
    horizon: float,
    random_state: int,
    config: Mapping[str, object],
) -> np.ndarray:
    scores = np.full(len(clinical), np.nan, dtype=float)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_state)
    for fold_index, (fit_indices, eval_indices) in enumerate(
        splitter.split(np.zeros(len(clinical)), event)
    ):
        x_fit, x_eval = _fit_tabular(
            clinical.iloc[fit_indices].reset_index(drop=True),
            clinical.iloc[eval_indices].reset_index(drop=True),
            study,
        )
        prediction = _fit_predict(
            "B2",
            x_fit,
            event[fit_indices],
            time[fit_indices],
            x_eval,
            horizon,
            random_state * 100 + fold_index,
            config,
        )
        scores[eval_indices] = prediction.risk_score
    if not np.isfinite(scores).all():
        raise RuntimeError("inner cross-fitted clinical anchor scores are incomplete")
    return scores


def _bootstrap_summary(
    *,
    n_rows: int,
    event: np.ndarray,
    ensemble_size: int,
    min_unique_fraction: float,
    random_state: int,
    predictor: Callable[[np.ndarray, int], np.ndarray],
) -> BootstrapSummary:
    rng = np.random.default_rng(random_state)
    predictions: list[np.ndarray] = []
    attempts = 0
    max_attempts = max(ensemble_size * 30, 100)
    minimum_unique = max(2, math.ceil(min_unique_fraction * n_rows))
    while len(predictions) < ensemble_size and attempts < max_attempts:
        attempts += 1
        sample = rng.integers(0, n_rows, size=n_rows)
        if np.unique(sample).size < minimum_unique:
            continue
        sampled_event = event[sample]
        if not sampled_event.any() or sampled_event.all():
            continue
        try:
            prediction = np.asarray(predictor(sample, random_state * 1000 + attempts), dtype=float)
        except Exception:
            continue
        if prediction.ndim != 1 or not np.isfinite(prediction).all():
            continue
        predictions.append(prediction)
    if len(predictions) < ensemble_size:
        raise RuntimeError(
            f"bootstrap ensemble incomplete: {len(predictions)}/{ensemble_size} "
            f"models after {attempts} attempts"
        )
    matrix = np.vstack(predictions)
    lower = np.quantile(matrix, 0.025, axis=0)
    upper = np.quantile(matrix, 0.975, axis=0)
    return BootstrapSummary(
        np.median(matrix, axis=0),
        np.std(matrix, axis=0, ddof=1),
        lower,
        upper,
        upper - lower,
        len(predictions),
        attempts,
    )


def _ood_columns(
    prefix: str, detector: TripleOODDetector, values: np.ndarray
) -> dict[str, np.ndarray]:
    scores = detector.score(values)
    return {
        f"{prefix}_ood_mahalanobis": scores.mahalanobis,
        f"{prefix}_ood_knn": scores.knn,
        f"{prefix}_ood_isolation_forest": scores.isolation_forest,
    }


def _fit_split(
    *,
    study: str,
    clinical_fit: pd.DataFrame,
    clinical_eval: pd.DataFrame,
    modality_fit: pd.DataFrame,
    modality_eval: pd.DataFrame,
    event_fit: np.ndarray,
    time_fit: np.ndarray,
    horizon: float,
    folds: int,
    random_state: int,
    config: Mapping[str, object],
    bootstrap_size: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    matrices = _split_matrices(
        study, clinical_fit, clinical_eval, modality_fit, modality_eval, config
    )
    outcome = structured_survival(event_fit, time_fit)
    anchor_training_score = _cross_fitted_anchor_scores(
        clinical_fit,
        event_fit,
        time_fit,
        study=study,
        folds=folds,
        horizon=horizon,
        random_state=random_state + 13,
        config=config,
    )
    b2 = _fit_predict(
        "B2",
        matrices.clinical_fit,
        event_fit,
        time_fit,
        matrices.clinical_eval,
        horizon,
        random_state + 101,
        config,
    )
    b3 = _fit_predict(
        "B3",
        matrices.clinical_fit,
        event_fit,
        time_fit,
        matrices.clinical_eval,
        horizon,
        random_state + 103,
        config,
    )
    b5 = _fit_predict(
        "B5",
        np.column_stack([matrices.clinical_fit, matrices.modality_fit]),
        event_fit,
        time_fit,
        np.column_stack([matrices.clinical_eval, matrices.modality_eval]),
        horizon,
        random_state + 107,
        config,
    )
    b6_model = StackedResidualSurvivalModel(config).fit(
        anchor_training_score, matrices.modality_fit, outcome, horizon=horizon
    )
    b6 = b6_model.predict(b2.risk_score, matrices.modality_eval)
    permutation = np.random.default_rng(random_state + 109).permutation(len(modality_eval))
    perturbed = b6_model.predict(b2.risk_score, matrices.modality_eval[permutation])
    clinical_detector = TripleOODDetector(
        n_neighbors=int(config.get("knn_neighbors", 10)),
        isolation_estimators=int(config.get("isolation_forest_estimators", 200)),
        max_features=int(config.get("ood_embedding_max_features", 50)),
        random_state=random_state + 113,
    ).fit(matrices.clinical_fit)
    modality_detector = TripleOODDetector(
        n_neighbors=int(config.get("knn_neighbors", 10)),
        isolation_estimators=int(config.get("isolation_forest_estimators", 200)),
        max_features=int(config.get("ood_embedding_max_features", 50)),
        random_state=random_state + 127,
    ).fit(matrices.modality_fit)
    minimum_unique = float(config.get("bootstrap_min_unique_fraction", 0.5))
    clinical_bootstrap = _bootstrap_summary(
        n_rows=len(event_fit),
        event=event_fit,
        ensemble_size=bootstrap_size,
        min_unique_fraction=minimum_unique,
        random_state=random_state + 131,
        predictor=lambda sample, state: _fit_predict(
            "B2",
            matrices.clinical_fit[sample],
            event_fit[sample],
            time_fit[sample],
            matrices.clinical_eval,
            horizon,
            state,
            config,
        ).risk_horizon,
    )
    fusion_bootstrap = _bootstrap_summary(
        n_rows=len(event_fit),
        event=event_fit,
        ensemble_size=bootstrap_size,
        min_unique_fraction=minimum_unique,
        random_state=random_state + 137,
        predictor=lambda sample, _state: StackedResidualSurvivalModel(config)
        .fit(
            anchor_training_score[sample],
            matrices.modality_fit[sample],
            outcome[sample],
            horizon=horizon,
        )
        .predict(b2.risk_score, matrices.modality_eval)
        .risk_horizon,
    )
    missingness_matrix = _missingness_matrix(modality_eval)
    missingness_fraction = (
        missingness_matrix.mean(axis=1)
        if missingness_matrix.shape[1]
        else np.zeros(len(modality_eval), dtype=float)
    )
    frame = pd.DataFrame(
        {
            "b2_score": b2.risk_score,
            "b2_risk": b2.risk_horizon,
            "b3_score": b3.risk_score,
            "b3_risk": b3.risk_horizon,
            "b5_score": b5.risk_score,
            "b5_risk": b5.risk_horizon,
            "b6_score": b6.risk_score,
            "b6_risk": b6.risk_horizon,
            "modality_increment": b6.risk_horizon - b2.risk_horizon,
            "clinical_uncertainty_median": clinical_bootstrap.median,
            "clinical_uncertainty_sd": clinical_bootstrap.sd,
            "clinical_uncertainty_lower95": clinical_bootstrap.lower,
            "clinical_uncertainty_upper95": clinical_bootstrap.upper,
            "clinical_uncertainty_width95": clinical_bootstrap.width,
            "clinical_model_disagreement": np.abs(b2.risk_horizon - b3.risk_horizon),
            "fusion_uncertainty_median": fusion_bootstrap.median,
            "fusion_uncertainty_sd": fusion_bootstrap.sd,
            "fusion_uncertainty_lower95": fusion_bootstrap.lower,
            "fusion_uncertainty_upper95": fusion_bootstrap.upper,
            "fusion_uncertainty_width95": fusion_bootstrap.width,
            "perturbation_sensitivity": np.abs(b6.risk_horizon - perturbed.risk_horizon),
            "modality_missingness": missingness_fraction,
            "modality_missing": missingness_fraction >= 1.0 - 1e-12,
            "fusion_disagreement": np.abs(b6.risk_horizon - b5.risk_horizon),
        }
    )
    for name, values in _ood_columns("clinical", clinical_detector, matrices.clinical_eval).items():
        frame[name] = values
    for name, values in _ood_columns("modality", modality_detector, matrices.modality_eval).items():
        frame[name] = values
    diagnostics = {
        "clinical_bootstrap_models": clinical_bootstrap.successful_models,
        "clinical_bootstrap_attempts": clinical_bootstrap.attempts,
        "fusion_bootstrap_models": fusion_bootstrap.successful_models,
        "fusion_bootstrap_attempts": fusion_bootstrap.attempts,
    }
    return frame, diagnostics


def _study_seed_predictions(
    data: StudyData,
    *,
    seed: int,
    horizon: float,
    folds: int,
    config: Mapping[str, object],
    bootstrap_size: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    if data.modality_train is None or data.modality_calibration is None:
        raise ValueError(data.modality_blocker or "additional modality unavailable")
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    oof_parts: list[pd.DataFrame] = []
    aggregate = {
        "clinical_bootstrap_models": 0,
        "clinical_bootstrap_attempts": 0,
        "fusion_bootstrap_models": 0,
        "fusion_bootstrap_attempts": 0,
    }
    for fold_index, (fit_indices, eval_indices) in enumerate(
        splitter.split(np.zeros(data.n_train), data.train_event)
    ):
        frame, diagnostics = _fit_split(
            study=data.study,
            clinical_fit=data.clinical_train.iloc[fit_indices].reset_index(drop=True),
            clinical_eval=data.clinical_train.iloc[eval_indices].reset_index(drop=True),
            modality_fit=data.modality_train.iloc[fit_indices].reset_index(drop=True),
            modality_eval=data.modality_train.iloc[eval_indices].reset_index(drop=True),
            event_fit=data.train_event[fit_indices],
            time_fit=data.train_time[fit_indices],
            horizon=horizon,
            folds=folds,
            random_state=seed * 100 + fold_index,
            config=config,
            bootstrap_size=bootstrap_size,
        )
        frame["row_index"] = eval_indices
        frame["fold"] = fold_index
        oof_parts.append(frame)
        for key, value in diagnostics.items():
            aggregate[key] += value
    oof = pd.concat(oof_parts, ignore_index=True).sort_values("row_index").reset_index(drop=True)
    if not np.array_equal(oof["row_index"].to_numpy(), np.arange(data.n_train)):
        raise RuntimeError("OOF row coverage is incomplete")
    calibration, diagnostics = _fit_split(
        study=data.study,
        clinical_fit=data.clinical_train,
        clinical_eval=data.clinical_calibration,
        modality_fit=data.modality_train,
        modality_eval=data.modality_calibration,
        event_fit=data.train_event,
        time_fit=data.train_time,
        horizon=horizon,
        folds=folds,
        random_state=seed * 1000 + 911,
        config=config,
        bootstrap_size=bootstrap_size,
    )
    calibration["row_index"] = np.arange(len(data.calibration_ids))
    calibration["fold"] = -1
    for key, value in diagnostics.items():
        aggregate[key] += value
    return oof, calibration, aggregate


def _add_reliability_ranks(
    frame: pd.DataFrame, calibration_reference: pd.DataFrame
) -> pd.DataFrame:
    ranked = frame.copy()
    for column in RANK_SOURCE_COLUMNS:
        ranked[f"rank_{column}"] = empirical_percentile(
            ranked[column].to_numpy(dtype=float),
            calibration_reference[column].to_numpy(dtype=float),
        )
    ranked["clinical_ood_rank"] = equal_weight_score(
        ranked["rank_clinical_ood_mahalanobis"],
        ranked["rank_clinical_ood_knn"],
        ranked["rank_clinical_ood_isolation_forest"],
    )
    ranked["modality_ood_rank"] = equal_weight_score(
        ranked["rank_modality_ood_mahalanobis"],
        ranked["rank_modality_ood_knn"],
        ranked["rank_modality_ood_isolation_forest"],
    )
    ranked["clinical_unreliability"] = equal_weight_score(
        ranked["clinical_ood_rank"],
        ranked["rank_clinical_uncertainty_sd"],
        ranked["rank_clinical_model_disagreement"],
    )
    ranked["modality_unreliability"] = equal_weight_score(
        ranked["modality_ood_rank"],
        ranked["rank_fusion_uncertainty_sd"],
        ranked["rank_perturbation_sensitivity"],
        ranked["rank_modality_missingness"],
        ranked["rank_fusion_disagreement"],
    )
    return ranked


def _profile_label(coverage: float) -> str:
    return f"{round(coverage * 100)}"


def _thresholds(calibration: pd.DataFrame, coverages: Sequence[float]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for coverage in coverages:
        clinical_threshold = quantile_threshold(
            calibration["clinical_unreliability"].to_numpy(dtype=float), coverage
        )
        retained = calibration["clinical_unreliability"].to_numpy(dtype=float) <= clinical_threshold
        available = ~calibration["modality_missing"].to_numpy(dtype=bool)
        reference = calibration.loc[retained & available, "modality_unreliability"].to_numpy(
            dtype=float
        )
        if reference.size == 0:
            reference = calibration["modality_unreliability"].to_numpy(dtype=float)
        rows.append(
            {
                "target_coverage": float(coverage),
                "clinical_threshold": clinical_threshold,
                "modality_threshold": quantile_threshold(reference, coverage),
                "calibration_reference_n": float(len(calibration)),
                "modality_reference_n": float(len(reference)),
            }
        )
    return rows


def _apply_profiles(
    frame: pd.DataFrame, threshold_rows: Sequence[Mapping[str, float]]
) -> pd.DataFrame:
    result = frame.copy()
    for row in threshold_rows:
        label = _profile_label(float(row["target_coverage"]))
        actions, reasons = assign_actions(
            result["clinical_unreliability"].to_numpy(dtype=float),
            result["modality_unreliability"].to_numpy(dtype=float),
            result["modality_missing"].to_numpy(dtype=bool),
            clinical_threshold=float(row["clinical_threshold"]),
            modality_threshold=float(row["modality_threshold"]),
        )
        result[f"action_{label}"] = actions
        result[f"reason_{label}"] = reasons
        result[f"gated_risk_{label}"] = gated_risk(
            result["b2_risk"].to_numpy(dtype=float),
            result["b6_risk"].to_numpy(dtype=float),
            actions,
        )
    return result


def _metric_row(
    *,
    data: StudyData,
    partition: str,
    model: str,
    seed: int,
    risk_score: np.ndarray,
    risk_horizon: np.ndarray,
    horizon: float,
    survival_floor: float,
) -> dict[str, object]:
    if partition == "oof":
        event, time = data.train_event, data.train_time
    else:
        event, time = data.calibration_event, data.calibration_time
    finite = np.isfinite(risk_score) & np.isfinite(risk_horizon)
    base = {"study": data.study, "partition": partition, "model": model, "seed": seed}
    if not finite.any():
        return {
            **base,
            "n": 0.0,
            "events": 0.0,
            "ipcw_evaluable_weight": 0.0,
            "ipcw_brier": math.nan,
            "harrell_c": math.nan,
            "uno_c": math.nan,
            "auc_horizon": math.nan,
            "calibration_in_the_large": math.nan,
            "calibration_slope": math.nan,
            "mean_predicted_risk": math.nan,
        }
    metrics = evaluate_survival_predictions(
        data.train_event,
        data.train_time,
        event[finite],
        time[finite],
        np.asarray(risk_score, dtype=float)[finite],
        np.asarray(risk_horizon, dtype=float)[finite],
        horizon,
        survival_floor=survival_floor,
    )
    return {**base, **metrics}


def _action_rows(
    study: str, partition: str, seed: int, frame: pd.DataFrame, coverages: Sequence[float]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    n = max(1, len(frame))
    for coverage in coverages:
        label = _profile_label(coverage)
        actions = frame[f"action_{label}"]
        counts = actions.value_counts()
        for action in ("AUGMENT", "FALLBACK", "ABSTAIN"):
            count = int(counts.get(action, 0))
            rows.append(
                {
                    "study": study,
                    "partition": partition,
                    "seed": seed,
                    "profile": label,
                    "target_coverage": coverage,
                    "action": action,
                    "count": count,
                    "rate": count / n,
                    "non_abstention_coverage": float((actions != "ABSTAIN").mean()),
                }
            )
    return rows


def _diagnostic_rows(
    study: str, partition: str, seed: int, frame: pd.DataFrame
) -> list[dict[str, object]]:
    indicators = [
        *RAW_RELIABILITY_COLUMNS,
        "clinical_ood_rank",
        "modality_ood_rank",
        "clinical_unreliability",
        "modality_unreliability",
    ]
    rows: list[dict[str, object]] = []
    for indicator in indicators:
        values = frame[indicator].to_numpy(dtype=float)
        rows.append(
            {
                "study": study,
                "partition": partition,
                "seed": seed,
                "indicator": indicator,
                "mean": float(np.mean(values)),
                "sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "median": float(np.median(values)),
                "q90": float(np.quantile(values, 0.9)),
                "max": float(np.max(values)),
            }
        )
    return rows


def _attach_trace_metadata(
    frame: pd.DataFrame,
    ids: np.ndarray,
    event: np.ndarray,
    time: np.ndarray,
    study: str,
    seed: int,
    partition: str,
) -> pd.DataFrame:
    result = frame.copy()
    result.insert(0, "duration_days", time)
    result.insert(0, "event", event.astype(int))
    result.insert(0, "patient_id", ids)
    result.insert(0, "partition", partition)
    result.insert(0, "seed", seed)
    result.insert(0, "study", study)
    return result


def _plot_model_comparison(metrics: pd.DataFrame, path: Path) -> None:
    summary = metrics.groupby(["study", "partition", "model"])["ipcw_brier"].mean().reset_index()
    studies = list(summary["study"].drop_duplicates())
    fig, axes = plt.subplots(1, len(studies), figsize=(6 * len(studies), 4.5), squeeze=False)
    for axis, study in zip(axes[0], studies, strict=False):
        local = summary.loc[summary["study"].eq(study) & summary["partition"].eq("calibration")]
        axis.bar(local["model"], local["ipcw_brier"])
        axis.set_title(study)
        axis.set_xlabel("Model")
        axis.set_ylabel("24-month IPCW Brier score")
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("Phase 4 calibration model comparison")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def _plot_risk_coverage(rows: pd.DataFrame, path: Path) -> None:
    mean = rows.groupby(["study", "partition", "target_coverage"], as_index=False)[
        ["observed_coverage", "ipcw_brier"]
    ].mean()
    studies = list(mean["study"].drop_duplicates())
    fig, axes = plt.subplots(1, len(studies), figsize=(6 * len(studies), 4.5), squeeze=False)
    for axis, study in zip(axes[0], studies, strict=False):
        local = mean.loc[mean["study"].eq(study) & mean["partition"].eq("calibration")]
        axis.plot(local["observed_coverage"], local["ipcw_brier"], marker="o")
        axis.set_title(study)
        axis.set_xlabel("Observed non-abstention coverage")
        axis.set_ylabel("Selective IPCW Brier score")
        axis.grid(alpha=0.25)
    fig.suptitle("Phase 4 calibration risk-coverage")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def _plot_actions(actions: pd.DataFrame, path: Path) -> None:
    local = actions.loc[actions["partition"].eq("calibration")]
    mean = local.groupby(["study", "profile", "action"], as_index=False)["rate"].mean()
    studies = list(mean["study"].drop_duplicates())
    fig, axes = plt.subplots(1, len(studies), figsize=(6 * len(studies), 4.5), squeeze=False)
    colors = {"AUGMENT": "#4C78A8", "FALLBACK": "#F2CF5B", "ABSTAIN": "#E45756"}
    for axis, study in zip(axes[0], studies, strict=False):
        subset = mean.loc[mean["study"].eq(study)]
        profiles = sorted(subset["profile"].unique())
        bottom = np.zeros(len(profiles), dtype=float)
        for action in ("AUGMENT", "FALLBACK", "ABSTAIN"):
            values = np.asarray(
                [
                    subset.loc[
                        subset["profile"].eq(profile) & subset["action"].eq(action), "rate"
                    ].iloc[0]
                    for profile in profiles
                ]
            )
            axis.bar(profiles, values, bottom=bottom, label=action, color=colors[action])
            bottom += values
        axis.set_title(study)
        axis.set_xlabel("Prespecified profile (%)")
        axis.set_ylabel("Action rate")
        axis.set_ylim(0, 1)
        axis.legend(fontsize=8)
    fig.suptitle("Phase 4 calibration gate actions")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def _leakage_audit(status: pd.DataFrame, bootstrap_size: int) -> str:
    complete = int(status["status"].eq("complete").sum()) if not status.empty else 0
    failed = int(status["status"].eq("failed").sum()) if not status.empty else 0
    blocked = int(status["status"].eq("blocked").sum()) if not status.empty else 0
    return f"""# Phase 4 leakage and governance audit

## Authorized scope

Phase 4 used only frozen development train/calibration rows from HANCOCK and
TCGA-HNSC. RADCURE B6/B7 remained blocked because the ORCESTRA RDS modality
structure has not been validated. No sealed or external outcome was loaded.

## Leakage controls

- Outer OOF preprocessing, variance selection, OOD fitting, models, and bootstrap
  resampling used outer-training rows only.
- B6 training used inner cross-fitted B2 anchor scores; outer-evaluation and
  calibration outcomes never entered B6 fitting.
- The full-training calibration path fit preprocessing, models, OOD detectors, and
  {bootstrap_size}-member uncertainty ensembles on development training rows only.
- Reliability components were transformed with calibration-feature empirical ranks.
- Clinical and modality thresholds were prespecified calibration reliability
  quantiles; calibration outcomes were not used to select thresholds.
- Perturbation sensitivity used deterministic outcome-independent row permutations.
- Patient decisions were written only under Git-ignored `results/predictions/phase4/`.
- Intended tracked outputs were checked for identifier headers and known native-ID patterns.

## Run accounting

- Complete study/seed runs: {complete}
- Failed study/seed runs: {failed}
- Governance-blocked entries: {blocked}

## Boundary

This is development-stage evidence, not locked or external validation. Phase 5
stress tests, subgroup campaigns, final analysis freeze, and Phase 6 evaluation
remain unauthorized.
"""


def _core_findings(model_metrics: pd.DataFrame, gate_metrics: pd.DataFrame) -> str:
    def value(study: str, model: str, column: str) -> float:
        selected = model_metrics.loc[
            model_metrics["study"].eq(study)
            & model_metrics["partition"].eq("calibration")
            & model_metrics["model"].eq(model),
            column,
        ]
        return float(selected.mean()) if len(selected) else math.nan

    lines = [
        "# Phase 4 core development findings",
        "",
        "These findings are development/calibration observations only. "
        "They are not sealed or external performance claims.",
        "",
        "## Mean calibration performance over prespecified seeds",
        "",
        "| Study | Model | IPCW Brier | Harrell C | 24-month AUC |",
        "|---|---|---:|---:|---:|",
    ]
    for study in ("HANCOCK", "TCGA-HNSC"):
        for model in ("B2", "B5", "B6"):
            lines.append(
                f"| {study} | {model} | {value(study, model, 'ipcw_brier'):.4f} | "
                f"{value(study, model, 'harrell_c'):.4f} | "
                f"{value(study, model, 'auc_horizon'):.4f} |"
            )
    lines.extend(["", "## Reliability gate", ""])
    for study in ("HANCOCK", "TCGA-HNSC"):
        subset = gate_metrics.loc[
            gate_metrics["study"].eq(study) & gate_metrics["partition"].eq("calibration")
        ]
        for profile in ("80", "90"):
            row = subset.loc[subset["profile"].eq(profile)]
            if len(row):
                lines.append(
                    f"- {study} B7-{profile}: mean observed non-abstention coverage "
                    f"{row['observed_coverage'].mean():.3f}; selective IPCW Brier "
                    f"{row['ipcw_brier'].mean():.4f}."
                )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "B6 is a stacked residual learner rather than a strict fixed-coefficient Cox offset. "
            "The gate uses equal-weight prespecified indicators and outcome-free "
            "calibration quantiles. "
            "Any robustness claim requires separately authorized Phase 5 stress tests "
            "and Phase 6 locked/external evaluation.",
            "",
        ]
    )
    return "\n".join(lines)


def run(
    project_root: Path,
    *,
    studies: Sequence[str] | None = None,
    seeds: Sequence[int] | None = None,
    bootstrap_size: int | None = None,
    output_root: Path | None = None,
    write_receipt: bool = True,
) -> dict[str, object]:
    root = Path(project_root).resolve()
    config_path = root / "configs/phase4_trust_hn.json"
    governance_path = root / "configs/phase4_governance.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    governance = json.loads(governance_path.read_text(encoding="utf-8-sig"))
    if config.get("status") != "FROZEN_FOR_PHASE4_DEVELOPMENT":
        raise RuntimeError("Phase 4 configuration is not frozen for development")
    if bool(config.get("sealed_outcomes_authorized")) or bool(
        config.get("external_outcomes_authorized")
    ):
        raise RuntimeError("Phase 4 runner refuses sealed/external outcome authorization")
    if bool(governance.get("test_unseal_allowed")):
        raise RuntimeError("Phase 4 governance must keep test unsealing disabled")

    selected_studies = list(studies or ["HANCOCK", "TCGA-HNSC"])
    selected_seeds = [int(value) for value in (seeds or config["seeds"])]
    horizon = float(config["horizon_days"])
    folds = int(config["cv_folds"])
    hyper = dict(config["hyperparameters"])
    ensemble_size = int(
        bootstrap_size if bootstrap_size is not None else hyper.get("bootstrap_ensemble_size", 20)
    )
    coverages = [float(value) for value in config["reliability"]["coverage_profiles"]]
    risk_grid = [float(value) for value in config["reliability"]["risk_coverage_grid"]]
    survival_floor = float(hyper.get("ipcw_survival_floor", 0.05))

    base = Path(output_root).resolve() if output_root is not None else root
    metrics_root = base / "results/metrics/phase4"
    figure_root = base / "results/figures/phase4"
    prediction_root = base / "results/predictions/phase4"
    audit_root = base / "docs/audits/phase4"
    for directory in (metrics_root, figure_root, prediction_root, audit_root):
        directory.mkdir(parents=True, exist_ok=True)

    model_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []
    risk_coverage_rows: list[dict[str, object]] = []
    action_rows: list[dict[str, object]] = []
    threshold_rows: list[dict[str, object]] = []
    diagnostic_rows: list[dict[str, object]] = []
    status_rows: list[dict[str, object]] = [
        {
            "study": "RADCURE",
            "seed": "",
            "status": "blocked",
            "reason": config["study_scope"]["RADCURE"]["reason"],
            "clinical_bootstrap_models": 0,
            "clinical_bootstrap_attempts": 0,
            "fusion_bootstrap_models": 0,
            "fusion_bootstrap_attempts": 0,
        }
    ]

    for study in selected_studies:
        data = load_phase3_study_data(root, study, build_expression=study == "TCGA-HNSC")
        for seed in selected_seeds:
            try:
                oof_raw, calibration_raw, bootstrap_diagnostics = _study_seed_predictions(
                    data,
                    seed=seed,
                    horizon=horizon,
                    folds=folds,
                    config=hyper,
                    bootstrap_size=ensemble_size,
                )
                calibration = _add_reliability_ranks(calibration_raw, calibration_raw)
                oof = _add_reliability_ranks(oof_raw, calibration_raw)
                local_thresholds = _thresholds(calibration, coverages)
                oof = _apply_profiles(oof, local_thresholds)
                calibration = _apply_profiles(calibration, local_thresholds)

                for partition, frame in (("oof", oof), ("calibration", calibration)):
                    for model, score_column, risk_column in (
                        ("B2", "b2_score", "b2_risk"),
                        ("B5", "b5_score", "b5_risk"),
                        ("B6", "b6_score", "b6_risk"),
                    ):
                        model_rows.append(
                            _metric_row(
                                data=data,
                                partition=partition,
                                model=model,
                                seed=seed,
                                risk_score=frame[score_column].to_numpy(dtype=float),
                                risk_horizon=frame[risk_column].to_numpy(dtype=float),
                                horizon=horizon,
                                survival_floor=survival_floor,
                            )
                        )
                    action_rows.extend(_action_rows(data.study, partition, seed, frame, coverages))
                    diagnostic_rows.extend(_diagnostic_rows(data.study, partition, seed, frame))
                    for coverage in coverages:
                        label = _profile_label(coverage)
                        metrics = _metric_row(
                            data=data,
                            partition=partition,
                            model=f"B7-{label}",
                            seed=seed,
                            risk_score=frame[f"gated_risk_{label}"].to_numpy(dtype=float),
                            risk_horizon=frame[f"gated_risk_{label}"].to_numpy(dtype=float),
                            horizon=horizon,
                            survival_floor=survival_floor,
                        )
                        gate_rows.append(
                            {
                                **metrics,
                                "profile": label,
                                "target_coverage": coverage,
                                "observed_coverage": float(
                                    (frame[f"action_{label}"] != "ABSTAIN").mean()
                                ),
                                "augmentation_rate": float(
                                    (frame[f"action_{label}"] == "AUGMENT").mean()
                                ),
                                "fallback_rate": float(
                                    (frame[f"action_{label}"] == "FALLBACK").mean()
                                ),
                                "abstention_rate": float(
                                    (frame[f"action_{label}"] == "ABSTAIN").mean()
                                ),
                            }
                        )

                for row in local_thresholds:
                    threshold_rows.append({"study": data.study, "seed": seed, **row})
                for coverage in risk_grid:
                    threshold = _thresholds(calibration, [coverage])[0]
                    for partition, frame in (("oof", oof), ("calibration", calibration)):
                        temporary = _apply_profiles(frame, [threshold])
                        label = _profile_label(coverage)
                        actions = temporary[f"action_{label}"]
                        final_risk = temporary[f"gated_risk_{label}"].to_numpy(dtype=float)
                        metrics = _metric_row(
                            data=data,
                            partition=partition,
                            model=f"B7-RC-{label}",
                            seed=seed,
                            risk_score=final_risk,
                            risk_horizon=final_risk,
                            horizon=horizon,
                            survival_floor=survival_floor,
                        )
                        risk_coverage_rows.append(
                            {
                                "study": data.study,
                                "partition": partition,
                                "seed": seed,
                                "target_coverage": coverage,
                                "observed_coverage": float((actions != "ABSTAIN").mean()),
                                "augmentation_rate": float((actions == "AUGMENT").mean()),
                                "fallback_rate": float((actions == "FALLBACK").mean()),
                                "abstention_rate": float((actions == "ABSTAIN").mean()),
                                "ipcw_brier": metrics["ipcw_brier"],
                                "harrell_c": metrics["harrell_c"],
                                "auc_horizon": metrics["auc_horizon"],
                            }
                        )

                slug = data.study.casefold().replace("-", "_")
                _attach_trace_metadata(
                    oof,
                    data.train_ids,
                    data.train_event,
                    data.train_time,
                    data.study,
                    seed,
                    "oof",
                ).to_csv(prediction_root / f"{slug}_seed{seed}_oof.csv", index=False)
                _attach_trace_metadata(
                    calibration,
                    data.calibration_ids,
                    data.calibration_event,
                    data.calibration_time,
                    data.study,
                    seed,
                    "calibration",
                ).to_csv(prediction_root / f"{slug}_seed{seed}_calibration.csv", index=False)
                status_rows.append(
                    {
                        "study": data.study,
                        "seed": seed,
                        "status": "complete",
                        "reason": "",
                        **bootstrap_diagnostics,
                    }
                )
            except Exception as exc:
                status_rows.append(
                    {
                        "study": data.study,
                        "seed": seed,
                        "status": "failed",
                        "reason": f"{type(exc).__name__}: {exc}",
                        "clinical_bootstrap_models": 0,
                        "clinical_bootstrap_attempts": 0,
                        "fusion_bootstrap_models": 0,
                        "fusion_bootstrap_attempts": 0,
                    }
                )

    outputs = {
        "model_metrics": metrics_root / "model_metrics.csv",
        "gate_metrics": metrics_root / "gate_metrics.csv",
        "risk_coverage": metrics_root / "risk_coverage.csv",
        "action_summary": metrics_root / "action_summary.csv",
        "thresholds": metrics_root / "thresholds.csv",
        "reliability_diagnostics": metrics_root / "reliability_diagnostics.csv",
        "model_status": metrics_root / "model_status.csv",
    }
    frames = {
        "model_metrics": pd.DataFrame(model_rows),
        "gate_metrics": pd.DataFrame(gate_rows),
        "risk_coverage": pd.DataFrame(risk_coverage_rows),
        "action_summary": pd.DataFrame(action_rows),
        "thresholds": pd.DataFrame(threshold_rows),
        "reliability_diagnostics": pd.DataFrame(diagnostic_rows),
        "model_status": pd.DataFrame(status_rows),
    }
    for name, path in outputs.items():
        frames[name].to_csv(path, index=False)

    figure_paths = {
        "model_comparison": figure_root / "model_comparison.svg",
        "risk_coverage": figure_root / "risk_coverage.svg",
        "action_distribution": figure_root / "action_distribution.svg",
    }
    if not frames["model_metrics"].empty:
        _plot_model_comparison(frames["model_metrics"], figure_paths["model_comparison"])
    if not frames["risk_coverage"].empty:
        _plot_risk_coverage(frames["risk_coverage"], figure_paths["risk_coverage"])
    if not frames["action_summary"].empty:
        _plot_actions(frames["action_summary"], figure_paths["action_distribution"])

    leakage_path = audit_root / "leakage_audit.md"
    findings_path = audit_root / "core_findings.md"
    leakage_path.write_text(_leakage_audit(frames["model_status"], ensemble_size), encoding="utf-8")
    findings_path.write_text(
        _core_findings(frames["model_metrics"], frames["gate_metrics"]), encoding="utf-8"
    )
    public_paths = [
        *outputs.values(),
        *[path for path in figure_paths.values() if path.exists()],
        leakage_path,
        findings_path,
    ]
    _assert_aggregate_privacy(public_paths)
    successful = int(frames["model_status"]["status"].eq("complete").sum())
    failed = int(frames["model_status"]["status"].eq("failed").sum())
    blocked = int(frames["model_status"]["status"].eq("blocked").sum())
    receipt = {
        "schema_version": "4.0",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "phase": "Phase 4 TRUST-HN core development",
        "studies": selected_studies,
        "horizon_days": horizon,
        "cv_folds": folds,
        "seeds": selected_seeds,
        "bootstrap_ensemble_size": ensemble_size,
        "successful_runs": successful,
        "failed_runs": failed,
        "blocked_entries": blocked,
        "patient_prediction_directory": prediction_root.relative_to(base).as_posix()
        + " (Git-ignored for canonical project run)",
        "sealed_or_external_outcomes_used": False,
        "phase5_components_used": False,
        "config_sha256": {
            config_path.relative_to(root).as_posix(): _sha256(config_path),
            governance_path.relative_to(root).as_posix(): _sha256(governance_path),
        },
        "aggregate_output_sha256": {
            path.relative_to(base).as_posix(): _sha256(path) for path in public_paths
        },
    }
    if write_receipt:
        receipt_path = base / "results/manifests/phase4_trust_hn_receipt.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        receipt["receipt"] = receipt_path.relative_to(base).as_posix()
    return receipt
