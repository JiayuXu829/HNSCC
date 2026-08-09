"""Execution and reporting for the post-hoc Phase 7 comparator benchmark."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import StratifiedKFold

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from trust_hn.data.phase3_features import StudyData
from trust_hn.data.phase6_data import (
    CohortFeatures,
    load_geo_features,
    load_hancock_features,
    load_phase6_development_data,
    load_radcure_features,
)
from trust_hn.evaluation.phase6 import OutcomeData, load_phase6_outcomes
from trust_hn.metrics.survival import evaluate_survival_predictions, structured_survival
from trust_hn.phase7.models import Phase7FeaturePreprocessor, fit_predict_phase7_model
from trust_hn.utils.hashing import sha256_file

matplotlib.rcParams["svg.hashsalt"] = "trust-hn-phase7-exploratory"

METHODS = ("C1", "C2", "C3", "C4")
METRICS = (
    "ipcw_brier",
    "harrell_c",
    "uno_c",
    "auc_horizon",
    "calibration_in_the_large",
    "calibration_slope",
    "mean_predicted_risk",
)


def _atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def load_phase7_config(project_root: Path) -> dict[str, object]:
    path = Path(project_root) / "configs/phase7_exploratory_benchmarks.json"
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("analysis_label") != "post hoc exploratory benchmark":
        raise ValueError("Phase 7 must remain explicitly post hoc exploratory")
    if set(payload.get("new_comparators", {})) != set(METHODS):
        raise ValueError("Phase 7 comparator set differs from the frozen C1-C4 list")
    governance = payload.get("governance", {})
    if not isinstance(governance, Mapping):
        raise ValueError("Phase 7 governance block is missing")
    forbidden_true = (
        "prespecified_locked_comparison",
        "external_outcomes_for_tuning",
        "retune_trust_hn",
        "retune_gate_thresholds",
        "overwrite_phase6_outputs",
    )
    if any(bool(governance.get(key)) for key in forbidden_true):
        raise ValueError("Phase 7 governance permits a prohibited action")
    return payload


def _model_config(config: Mapping[str, object]) -> dict[str, object]:
    hyperparameters = config.get("hyperparameters", {})
    if not isinstance(hyperparameters, Mapping):
        raise ValueError("Phase 7 hyperparameters must be a mapping")
    values = dict(hyperparameters)
    values["cv_folds"] = int(config.get("cv_folds", 5))
    return values


def verify_phase6_frozen_files(project_root: Path) -> dict[str, object]:
    root = Path(project_root)
    freeze = yaml.safe_load((root / "configs/analysis_freeze.yaml").read_text(encoding="utf-8"))
    registered = [str(value) for value in freeze["phase6_registered_decision_files"]]
    expected = freeze["config_sha256"]
    mismatches: list[dict[str, str]] = []
    for relative in registered:
        path = root / relative
        observed = sha256_file(path) if path.exists() else "MISSING"
        wanted = str(expected.get(relative, "UNREGISTERED"))
        if observed != wanted:
            mismatches.append(
                {"path": relative, "expected_sha256": wanted, "observed_sha256": observed}
            )
    return {
        "registered_file_count": len(registered),
        "all_match": not mismatches,
        "mismatches": mismatches,
    }


def aggregate_seed_predictions(frame: pd.DataFrame, seeds: Sequence[int]) -> pd.DataFrame:
    required = {"native_id", "cohort", "model", "seed", "risk_score", "risk_horizon"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"prediction frame lacks columns: {sorted(missing)}")
    wanted = {int(value) for value in seeds}
    if frame.duplicated(["cohort", "model", "native_id", "seed"]).any():
        raise ValueError("duplicate patient/model/seed prediction rows")
    grouped = frame.groupby(["cohort", "model", "native_id"], sort=True, dropna=False)
    for key, local in grouped:
        observed = set(local["seed"].astype(int))
        if observed != wanted or len(local) != len(wanted):
            raise ValueError(f"incomplete seed predictions for {key}: {sorted(observed)}")
    result = (
        grouped[["risk_score", "risk_horizon"]]
        .mean()
        .reset_index()
        .sort_values(["cohort", "model", "native_id"], kind="stable")
        .reset_index(drop=True)
    )
    result["seed_count"] = len(wanted)
    return result


def _metric_row(
    *,
    study: str,
    cohort: str,
    partition: str,
    model: str,
    seed: int | str,
    train_event: np.ndarray,
    train_time: np.ndarray,
    eval_event: np.ndarray,
    eval_time: np.ndarray,
    risk_score: np.ndarray,
    risk_horizon: np.ndarray,
    horizon: float,
    survival_floor: float,
    runtime_seconds: float,
) -> dict[str, object]:
    values = evaluate_survival_predictions(
        train_event,
        train_time,
        eval_event,
        eval_time,
        risk_score,
        risk_horizon,
        horizon,
        survival_floor=survival_floor,
    )
    return {
        "analysis_label": "post hoc exploratory benchmark",
        "study": study,
        "cohort": cohort,
        "partition": partition,
        "model": model,
        "seed": seed,
        "runtime_seconds": runtime_seconds,
        "status": "OK",
        **values,
    }


def _development_model_predictions(
    data: StudyData,
    model: str,
    seed: int,
    config: Mapping[str, object],
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    if data.modality_train is None or data.modality_calibration is None:
        raise ValueError(data.modality_blocker or f"modality unavailable for {data.study}")
    horizon = float(config["horizon_days"])
    survival_floor = float(config.get("survival_floor", 0.05))
    model_config = _model_config(config)
    top_k = int(model_config.get("numeric_modality_top_k", 500))
    y_train = structured_survival(data.train_event, data.train_time)
    event = data.train_event.astype(int)
    folds = min(int(config.get("cv_folds", 5)), int(min(np.sum(event), np.sum(1 - event))))
    if folds < 2:
        raise ValueError(f"insufficient outcome variation for {data.study}")
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=int(seed))
    oof_score = np.full(data.n_train, np.nan, dtype=float)
    oof_risk = np.full(data.n_train, np.nan, dtype=float)
    started = time.perf_counter()
    for fit_indices, validation_indices in splitter.split(data.clinical_train, event):
        preprocessor = Phase7FeaturePreprocessor(data.study, top_k=top_k).fit(
            data.clinical_train.iloc[fit_indices].reset_index(drop=True),
            data.modality_train.iloc[fit_indices].reset_index(drop=True),
        )
        fit_blocks = preprocessor.transform(
            data.clinical_train.iloc[fit_indices].reset_index(drop=True),
            data.modality_train.iloc[fit_indices].reset_index(drop=True),
        )
        validation_blocks = preprocessor.transform(
            data.clinical_train.iloc[validation_indices].reset_index(drop=True),
            data.modality_train.iloc[validation_indices].reset_index(drop=True),
        )
        prediction = fit_predict_phase7_model(
            model,
            fit_blocks,
            y_train[fit_indices],
            validation_blocks,
            horizon,
            int(seed),
            model_config,
        )
        oof_score[validation_indices] = prediction.risk_score
        oof_risk[validation_indices] = prediction.risk_horizon
    if not np.isfinite(oof_score).all() or not np.isfinite(oof_risk).all():
        raise RuntimeError(f"incomplete development OOF predictions for {data.study}/{model}")
    oof_runtime = time.perf_counter() - started

    started = time.perf_counter()
    full_preprocessor = Phase7FeaturePreprocessor(data.study, top_k=top_k).fit(
        data.clinical_train, data.modality_train
    )
    full_train = full_preprocessor.transform(data.clinical_train, data.modality_train)
    calibration = full_preprocessor.transform(data.clinical_calibration, data.modality_calibration)
    calibration_prediction = fit_predict_phase7_model(
        model, full_train, y_train, calibration, horizon, int(seed), model_config
    )
    calibration_runtime = time.perf_counter() - started

    predictions = pd.concat(
        [
            pd.DataFrame(
                {
                    "native_id": data.train_ids.astype(str),
                    "study": data.study,
                    "partition": "development_oof",
                    "model": model,
                    "seed": int(seed),
                    "risk_score": oof_score,
                    "risk_horizon": oof_risk,
                }
            ),
            pd.DataFrame(
                {
                    "native_id": data.calibration_ids.astype(str),
                    "study": data.study,
                    "partition": "calibration",
                    "model": model,
                    "seed": int(seed),
                    "risk_score": calibration_prediction.risk_score,
                    "risk_horizon": calibration_prediction.risk_horizon,
                }
            ),
        ],
        ignore_index=True,
    )
    metrics = [
        _metric_row(
            study=data.study,
            cohort=data.study,
            partition="development_oof",
            model=model,
            seed=seed,
            train_event=data.train_event,
            train_time=data.train_time,
            eval_event=data.train_event,
            eval_time=data.train_time,
            risk_score=oof_score,
            risk_horizon=oof_risk,
            horizon=horizon,
            survival_floor=survival_floor,
            runtime_seconds=oof_runtime,
        ),
        _metric_row(
            study=data.study,
            cohort=data.study,
            partition="calibration",
            model=model,
            seed=seed,
            train_event=data.train_event,
            train_time=data.train_time,
            eval_event=data.calibration_event,
            eval_time=data.calibration_time,
            risk_score=calibration_prediction.risk_score,
            risk_horizon=calibration_prediction.risk_horizon,
            horizon=horizon,
            survival_floor=survival_floor,
            runtime_seconds=calibration_runtime,
        ),
    ]
    return predictions, metrics


def _development_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    columns = ["runtime_seconds", *METRICS]
    means = (
        metrics.groupby(["study", "partition", "model"], sort=True)[columns]
        .mean()
        .add_suffix("_mean")
    )
    stds = (
        metrics.groupby(["study", "partition", "model"], sort=True)[columns]
        .std(ddof=1)
        .add_suffix("_sd")
    )
    counts = metrics.groupby(["study", "partition", "model"], sort=True).size().rename("seeds")
    return pd.concat([counts, means, stds], axis=1).reset_index()


def run_development_benchmark(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(project_root)
    config = load_phase7_config(root)
    prediction_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    for study in [str(value) for value in config["development_studies"]]:
        data = load_phase6_development_data(root, study)
        for seed in [int(value) for value in config["seeds"]]:
            for model in METHODS:
                try:
                    predictions, metrics = _development_model_predictions(data, model, seed, config)
                    prediction_frames.append(predictions)
                    metric_rows.extend(metrics)
                except Exception as exc:
                    metric_rows.append(
                        {
                            "analysis_label": "post hoc exploratory benchmark",
                            "study": data.study,
                            "cohort": data.study,
                            "partition": "FAILED",
                            "model": model,
                            "seed": seed,
                            "runtime_seconds": math.nan,
                            "status": f"FAILED: {type(exc).__name__}: {exc}",
                        }
                    )
    predictions = (
        pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    )
    metrics = pd.DataFrame(metric_rows)
    failed = metrics.loc[metrics["status"].ne("OK")]
    _atomic_csv(
        root / "results/metrics/phase7_exploratory/development_metrics_by_seed.csv", metrics
    )
    if not failed.empty:
        raise RuntimeError(f"Phase 7 development failures: {failed['status'].tolist()}")
    summary = _development_summary(metrics)
    _atomic_csv(
        root / "results/metrics/phase7_exploratory/development_metrics_summary.csv", summary
    )
    _atomic_csv(
        root / "results/predictions/phase7_exploratory/development_predictions.csv",
        predictions,
    )
    _plot_development(
        summary, root / "results/figures/phase7_exploratory/development_comparison.svg"
    )
    return metrics, summary


def _external_bundle(project_root: Path, cohort: str) -> tuple[StudyData, CohortFeatures]:
    root = Path(project_root)
    if cohort == "RADCURE":
        return (
            load_phase6_development_data(root, "RADCURE"),
            load_radcure_features(root, role="sealed_test"),
        )
    if cohort == "HANCOCK":
        return (
            load_phase6_development_data(root, "HANCOCK"),
            load_hancock_features(root, role="sealed_test"),
        )
    return (
        load_phase6_development_data(root, "TCGA-HNSC"),
        load_geo_features(root, cohort, build_cache=True),
    )


def generate_external_predictions(project_root: Path) -> pd.DataFrame:
    """Generate external predictions without loading any external outcome."""

    root = Path(project_root)
    config = load_phase7_config(root)
    model_config = _model_config(config)
    top_k = int(model_config.get("numeric_modality_top_k", 500))
    horizon = float(config["horizon_days"])
    rows: list[pd.DataFrame] = []
    for cohort in [str(value) for value in config["external_cohorts"]]:
        development, features = _external_bundle(root, cohort)
        if development.modality_train is None:
            raise ValueError(f"development modality unavailable for {cohort}")
        outcome = structured_survival(development.train_event, development.train_time)
        for seed in [int(value) for value in config["seeds"]]:
            preprocessor = Phase7FeaturePreprocessor(development.study, top_k=top_k).fit(
                development.clinical_train, development.modality_train
            )
            train_blocks = preprocessor.transform(
                development.clinical_train, development.modality_train
            )
            external_blocks = preprocessor.transform(features.clinical, features.modality)
            for model in METHODS:
                prediction = fit_predict_phase7_model(
                    model,
                    train_blocks,
                    outcome,
                    external_blocks,
                    horizon,
                    seed,
                    model_config,
                )
                rows.append(
                    pd.DataFrame(
                        {
                            "native_id": features.ids.astype(str),
                            "cohort": cohort,
                            "model": model,
                            "seed": seed,
                            "risk_score": prediction.risk_score,
                            "risk_horizon": prediction.risk_horizon,
                        }
                    )
                )
    by_seed = pd.concat(rows, ignore_index=True)
    aggregate = aggregate_seed_predictions(by_seed, [int(value) for value in config["seeds"]])
    prediction_root = root / "results/predictions/phase7_exploratory"
    _atomic_csv(prediction_root / "external_predictions_by_seed.csv", by_seed)
    _atomic_csv(prediction_root / "external_predictions_aggregate.csv", aggregate)
    receipt = {
        "schema_version": "1.0",
        "phase": "Phase 7 outcome-free external prediction generation",
        "analysis_label": "post hoc exploratory benchmark",
        "completed_at": datetime.now(UTC).isoformat(),
        "status": "COMPLETE",
        "outcomes_loaded": False,
        "methods": list(METHODS),
        "seeds": [int(value) for value in config["seeds"]],
        "patient_level_outputs_git_ignored": True,
        "prediction_rows_by_seed": len(by_seed),
        "aggregate_prediction_rows": len(aggregate),
        "config_sha256": sha256_file(root / "configs/phase7_exploratory_benchmarks.json"),
    }
    _atomic_json(root / "results/manifests/phase7_exploratory_prediction_receipt.json", receipt)
    return aggregate


def _read_phase6_reference(project_root: Path, cohort: str, ids: Sequence[str]) -> pd.DataFrame:
    path = (
        Path(project_root)
        / "results/predictions/phase6"
        / f"{cohort.lower()}__original__aggregate90.csv"
    )
    frame = pd.read_csv(path, dtype={"native_id": "string"})
    if frame["native_id"].astype(str).tolist() != [str(value) for value in ids]:
        raise ValueError(f"Phase 6 reference IDs are misaligned for {cohort}")
    return frame


def _prediction_metrics(
    development: StudyData,
    outcomes: OutcomeData,
    score: np.ndarray,
    risk: np.ndarray,
    config: Mapping[str, object],
) -> dict[str, float]:
    return evaluate_survival_predictions(
        development.train_event,
        development.train_time,
        outcomes.event,
        outcomes.time,
        score,
        risk,
        float(config["horizon_days"]),
        survival_floor=float(config.get("survival_floor", 0.05)),
    )


def _paired_external_comparisons(
    project_root: Path,
    aggregate: pd.DataFrame,
    config: Mapping[str, object],
) -> pd.DataFrame:
    replicates = int(config.get("bootstrap_replicates", 1000))
    metric_names = ("ipcw_brier", "harrell_c", "uno_c", "auc_horizon")
    rows: list[dict[str, object]] = []
    for cohort_index, cohort in enumerate([str(value) for value in config["external_cohorts"]]):
        development, features = _external_bundle(project_root, cohort)
        outcomes = load_phase6_outcomes(project_root, cohort, features.ids)
        local = aggregate.loc[aggregate["cohort"].eq(cohort)].copy()
        piv_score = local.pivot(index="native_id", columns="model", values="risk_score")
        piv_risk = local.pivot(index="native_id", columns="model", values="risk_horizon")
        ordered_ids = features.ids.astype(str).tolist()
        piv_score = piv_score.reindex(ordered_ids)
        piv_risk = piv_risk.reindex(ordered_ids)
        if piv_score.isna().any().any() or piv_risk.isna().any().any():
            raise ValueError(f"incomplete aggregate Phase 7 predictions for {cohort}")
        reference = _read_phase6_reference(project_root, cohort, ordered_ids)
        predictions: dict[str, tuple[np.ndarray, np.ndarray]] = {
            model: (
                piv_score[model].to_numpy(dtype=float),
                piv_risk[model].to_numpy(dtype=float),
            )
            for model in METHODS
        }
        for model in ("B5", "B6"):
            predictions[model] = (
                reference[f"{model.lower()}_score"].to_numpy(dtype=float),
                reference[f"{model.lower()}_risk"].to_numpy(dtype=float),
            )
        point = {
            model: _prediction_metrics(development, outcomes, score, risk, config)
            for model, (score, risk) in predictions.items()
        }
        differences: dict[tuple[str, str, str], list[float]] = {
            (method, reference_model, metric): []
            for method in METHODS
            for reference_model in ("B5", "B6")
            for metric in metric_names
        }
        rng = np.random.default_rng(7100 + cohort_index * 101)
        for _ in range(replicates):
            indices = rng.integers(0, len(outcomes.ids), size=len(outcomes.ids))
            sampled_outcomes = OutcomeData(
                cohort,
                np.asarray([f"bootstrap_{position}" for position in range(len(indices))]),
                outcomes.event[indices],
                outcomes.time[indices],
            )
            sampled_metrics: dict[str, dict[str, float]] = {}
            for model, (score, risk) in predictions.items():
                sampled_metrics[model] = _prediction_metrics(
                    development, sampled_outcomes, score[indices], risk[indices], config
                )
            for method in METHODS:
                for reference_model in ("B5", "B6"):
                    for metric in metric_names:
                        difference = (
                            sampled_metrics[method][metric]
                            - sampled_metrics[reference_model][metric]
                        )
                        if np.isfinite(difference):
                            differences[(method, reference_model, metric)].append(difference)
        for key, values in differences.items():
            method, reference_model, metric = key
            array = np.asarray(values, dtype=float)
            point_difference = point[method][metric] - point[reference_model][metric]
            rows.append(
                {
                    "analysis_label": "post hoc exploratory benchmark",
                    "cohort": cohort,
                    "comparison": f"{method}_vs_{reference_model}",
                    "metric": f"difference_{metric}",
                    "point_estimate": point_difference,
                    "bootstrap_median": float(np.median(array)) if array.size else math.nan,
                    "ci_lower_95": float(np.quantile(array, 0.025)) if array.size else math.nan,
                    "ci_upper_95": float(np.quantile(array, 0.975)) if array.size else math.nan,
                    "valid_replicates": int(array.size),
                }
            )
    return pd.DataFrame(rows)


def evaluate_external_benchmark(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(project_root)
    config = load_phase7_config(root)
    prediction_path = (
        root / "results/predictions/phase7_exploratory/external_predictions_aggregate.csv"
    )
    if not prediction_path.exists():
        raise FileNotFoundError("generate outcome-free Phase 7 external predictions first")
    aggregate = pd.read_csv(prediction_path, dtype={"native_id": "string"})
    metric_rows: list[dict[str, object]] = []
    for cohort in [str(value) for value in config["external_cohorts"]]:
        development, features = _external_bundle(root, cohort)
        outcomes = load_phase6_outcomes(root, cohort, features.ids)
        local = aggregate.loc[aggregate["cohort"].eq(cohort)]
        for model in METHODS:
            model_rows = local.loc[local["model"].eq(model)].set_index("native_id")
            model_rows = model_rows.reindex(features.ids.astype(str))
            if model_rows[["risk_score", "risk_horizon"]].isna().any().any():
                raise ValueError(f"incomplete Phase 7 predictions for {cohort}/{model}")
            values = _prediction_metrics(
                development,
                outcomes,
                model_rows["risk_score"].to_numpy(dtype=float),
                model_rows["risk_horizon"].to_numpy(dtype=float),
                config,
            )
            metric_rows.append(
                {
                    "analysis_label": "post hoc exploratory benchmark",
                    "study": development.study,
                    "cohort": cohort,
                    "partition": features.role,
                    "model": model,
                    "seed": "five_seed_mean",
                    "coverage": 1.0,
                    "status": "OK",
                    **values,
                }
            )
    metrics = pd.DataFrame(metric_rows)
    _atomic_csv(root / "results/metrics/phase7_exploratory/external_metrics.csv", metrics)
    phase6 = pd.read_csv(root / "results/metrics/phase6/cohort_metrics.csv")
    phase6.insert(0, "analysis_label", "Phase 6 locked/external evaluation")
    combined = pd.concat([phase6, metrics], ignore_index=True, sort=False)
    _atomic_csv(
        root / "results/metrics/phase7_exploratory/external_benchmark_combined.csv",
        combined,
    )
    comparisons = _paired_external_comparisons(root, aggregate, config)
    _atomic_csv(
        root / "results/metrics/phase7_exploratory/paired_comparisons.csv",
        comparisons,
    )
    _plot_external_comparisons(
        comparisons,
        root / "results/figures/phase7_exploratory/external_comparator_forest.svg",
    )
    return metrics, comparisons


def _plot_development(summary: pd.DataFrame, path: Path) -> None:
    selected = summary.loc[summary["partition"].eq("calibration")].copy()
    studies = list(dict.fromkeys(selected["study"].astype(str)))
    fig, axes = plt.subplots(1, len(studies), figsize=(5 * len(studies), 4), squeeze=False)
    for axis, study in zip(axes[0], studies, strict=True):
        local = selected.loc[selected["study"].eq(study)].set_index("model").reindex(METHODS)
        axis.bar(METHODS, local["ipcw_brier_mean"], color="#4472C4")
        axis.set_title(study)
        axis.set_xlabel("Post-hoc comparator")
        axis.set_ylabel("24-month IPCW Brier (lower is better)")
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("Phase 7 development calibration benchmark")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _plot_external_comparisons(comparisons: pd.DataFrame, path: Path) -> None:
    selected = comparisons.loc[
        comparisons["metric"].eq("difference_ipcw_brier")
        & comparisons["comparison"].str.endswith("_vs_B6")
    ].copy()
    labels = selected["cohort"] + " / " + selected["comparison"]
    y = np.arange(len(selected))
    point = selected["point_estimate"].to_numpy(dtype=float)
    lower = selected["ci_lower_95"].to_numpy(dtype=float)
    upper = selected["ci_upper_95"].to_numpy(dtype=float)
    fig, axis = plt.subplots(figsize=(8, max(5, 0.32 * len(selected))))
    axis.errorbar(
        point,
        y,
        xerr=np.vstack([point - lower, upper - point]),
        fmt="o",
        color="#C00000",
        ecolor="#666666",
        capsize=2,
    )
    axis.axvline(0.0, color="black", linewidth=1)
    axis.set_yticks(y, labels)
    axis.invert_yaxis()
    axis.set_xlabel("IPCW Brier difference: new comparator minus B6 (negative favors comparator)")
    axis.set_title("Post-hoc exploratory paired external comparisons")
    axis.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def finalize_phase7_receipt(project_root: Path) -> dict[str, object]:
    root = Path(project_root)
    verification = verify_phase6_frozen_files(root)
    if not verification["all_match"]:
        raise RuntimeError("one or more registered Phase 6 files changed")
    output_roots = [
        root / "results/metrics/phase7_exploratory",
        root / "results/figures/phase7_exploratory",
    ]
    output_hashes: dict[str, str] = {}
    for directory in output_roots:
        for path in sorted(directory.rglob("*")) if directory.exists() else []:
            if path.is_file():
                output_hashes[path.relative_to(root).as_posix()] = sha256_file(path)
    payload = {
        "schema_version": "1.0",
        "phase": "Phase 7 post-hoc exploratory comparator benchmark",
        "analysis_label": "post hoc exploratory benchmark",
        "completed_at": datetime.now(UTC).isoformat(),
        "status": "COMPLETE",
        "methods_added": list(METHODS),
        "method_count": {
            "total_labeled_approaches": 14,
            "competitive_predictive_baselines_and_comparators": 10,
            "trust_hn_methods": 2,
            "audit_negative_controls": 2,
        },
        "phase6_frozen_file_verification": verification,
        "phase6_outputs_overwritten": False,
        "trust_hn_or_gate_retuned": False,
        "external_outcomes_used_for_tuning": False,
        "patient_level_outputs_git_ignored": True,
        "config_sha256": sha256_file(root / "configs/phase7_exploratory_benchmarks.json"),
        "tracked_output_sha256": output_hashes,
    }
    _atomic_json(root / "results/manifests/phase7_exploratory_receipt.json", payload)
    return payload


def run_all(project_root: Path) -> dict[str, object]:
    run_development_benchmark(project_root)
    generate_external_predictions(project_root)
    evaluate_external_benchmark(project_root)
    return finalize_phase7_receipt(project_root)
