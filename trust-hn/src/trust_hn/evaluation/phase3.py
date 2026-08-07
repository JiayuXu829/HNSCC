"""Phase 3 development-only baseline experiment orchestration."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import warnings
from collections.abc import Mapping, Sequence
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
from trust_hn.metrics.survival import (
    decision_curve_ipcw,
    evaluate_survival_predictions,
    structured_survival,
)
from trust_hn.models.survival_baselines import TabularPreprocessor, fit_predict_survival_model


@dataclass
class NumericMatrixPreprocessor:
    top_k: int | None = None
    medians_: np.ndarray | None = None
    selected_: np.ndarray | None = None
    means_: np.ndarray | None = None
    scales_: np.ndarray | None = None

    def fit(self, frame: pd.DataFrame) -> NumericMatrixPreprocessor:
        matrix = frame.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            medians = np.nanmedian(matrix, axis=0)
        medians = np.where(np.isfinite(medians), medians, 0.0).astype(np.float32)
        filled = np.where(np.isnan(matrix), medians, matrix)
        variances = np.var(filled, axis=0, dtype=np.float64)
        valid = np.flatnonzero(np.isfinite(variances) & (variances > 1e-12))
        if valid.size == 0:
            raise ValueError("no nonconstant numeric features in training partition")
        if self.top_k is not None and valid.size > self.top_k:
            order = np.argsort(variances[valid], kind="stable")[-self.top_k :]
            valid = valid[order]
        selected = filled[:, valid]
        means = selected.mean(axis=0, dtype=np.float64)
        scales = selected.std(axis=0, dtype=np.float64)
        scales = np.where(np.isfinite(scales) & (scales > 1e-12), scales, 1.0)
        self.medians_ = medians
        self.selected_ = valid
        self.means_ = means
        self.scales_ = scales
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        if (
            self.medians_ is None
            or self.selected_ is None
            or self.means_ is None
            or self.scales_ is None
        ):
            raise RuntimeError("numeric preprocessor must be fitted")
        matrix = frame.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
        if matrix.shape[1] != self.medians_.size:
            raise ValueError("numeric feature count changed between fit and transform")
        filled = np.where(np.isnan(matrix), self.medians_, matrix)
        result = (filled[:, self.selected_] - self.means_) / self.scales_
        if not np.isfinite(result).all():
            raise ValueError("numeric preprocessing produced non-finite values")
        return result.astype(float, copy=False)

    def fit_transform(self, frame: pd.DataFrame) -> np.ndarray:
        return self.fit(frame).transform(frame)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _infer_columns(frame: pd.DataFrame, study: str) -> tuple[list[str], list[str]]:
    categorical_overrides = {
        "HANCOCK": {
            "sex",
            "primarily_metastasis",
            "smoking_status",
            "perinodal_invasion",
            "lymphovascular_invasion_L",
            "vascular_invasion_V",
            "perineural_invasion_Pn",
            "carcinoma_in_situ",
            "primary_tumor_site",
            "grading",
            "hpv_association_p16",
            "resection_status",
            "resection_status_carcinoma_in_situ",
            "histologic_type",
            "pT_stage",
            "pN_stage",
        },
        "RADCURE": {
            "sex",
            "site",
            "subsite",
            "stage",
            "t_stage",
            "n_stage",
            "m_stage",
            "hpv",
            "treatment",
            "smoking",
            "ecog",
            "contrast_enhanced",
        },
        "TCGA-HNSC": {"sex", "site", "stage", "hpv", "treatment", "smoking"},
    }
    categorical = [
        column for column in frame.columns if column in categorical_overrides.get(study, set())
    ]
    numeric = [column for column in frame.columns if column not in categorical]
    return numeric, categorical


def _tabular_matrices(
    train: pd.DataFrame, evaluation: pd.DataFrame, study: str
) -> tuple[np.ndarray, np.ndarray]:
    numeric, categorical = _infer_columns(train, study)
    prep = TabularPreprocessor(numeric=numeric, categorical=categorical)
    return prep.fit_transform(train), prep.transform(evaluation)


def _missingness_matrix(frame: pd.DataFrame) -> np.ndarray:
    columns: list[np.ndarray] = []
    missing_tokens = {"", "unknown", "not reported", "not tested", "na", "n/a", "nan", "none"}
    for column in frame.columns:
        series = frame[column]
        missing = series.isna().to_numpy()
        if not pd.api.types.is_numeric_dtype(series):
            text = series.astype("string").str.strip().str.casefold()
            missing |= text.isin(missing_tokens).fillna(True).to_numpy()
        columns.append(missing.astype(float))
    return np.column_stack(columns) if columns else np.zeros((len(frame), 0), dtype=float)


def _fit_missingness(
    train: pd.DataFrame, evaluation: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    train_matrix = _missingness_matrix(train)
    evaluation_matrix = _missingness_matrix(evaluation)
    variable = np.var(train_matrix, axis=0) > 1e-12
    if not np.any(variable):
        return np.zeros((len(train), 0)), np.zeros((len(evaluation), 0))
    return train_matrix[:, variable], evaluation_matrix[:, variable]


def _permuted(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(frame))
    return frame.iloc[order].reset_index(drop=True)


def _assemble_features(
    data: StudyData,
    model_id: str,
    train_indices: np.ndarray,
    eval_indices: np.ndarray,
    seed: int,
    config: Mapping[str, object],
) -> tuple[np.ndarray, np.ndarray]:
    clinical_train = data.clinical_train.iloc[train_indices].reset_index(drop=True)
    clinical_eval = data.clinical_train.iloc[eval_indices].reset_index(drop=True)
    if model_id == "B0":
        return np.zeros((len(train_indices), 0)), np.zeros((len(eval_indices), 0))
    if model_id in {"B1", "B2", "B3"}:
        return _tabular_matrices(clinical_train, clinical_eval, data.study)
    modality = data.modality_train
    if model_id in {"B4", "B5", "N0"} and modality is None:
        raise ValueError(data.modality_blocker or "additional modality unavailable")
    if model_id == "M0":
        full_train = clinical_train
        full_eval = clinical_eval
        if modality is not None:
            full_train = pd.concat(
                [full_train, modality.iloc[train_indices].reset_index(drop=True)], axis=1
            )
            full_eval = pd.concat(
                [full_eval, modality.iloc[eval_indices].reset_index(drop=True)], axis=1
            )
        return _fit_missingness(full_train, full_eval)

    assert modality is not None
    modality_train = modality.iloc[train_indices].reset_index(drop=True)
    modality_eval = modality.iloc[eval_indices].reset_index(drop=True)
    if model_id == "N0":
        modality_train = _permuted(modality_train, seed * 1009 + 17)
        modality_eval = _permuted(modality_eval, seed * 1013 + 29)
    if data.study == "TCGA-HNSC":
        top_k = int(config.get("tcga_expression_foldwise_variance_top_k", 500))
        modality_prep = NumericMatrixPreprocessor(top_k=top_k)
        modality_train_matrix = modality_prep.fit_transform(modality_train)
        modality_eval_matrix = modality_prep.transform(modality_eval)
    else:
        modality_train_matrix, modality_eval_matrix = _tabular_matrices(
            modality_train, modality_eval, data.study
        )
    if model_id in {"B4", "N0"}:
        return modality_train_matrix, modality_eval_matrix
    clinical_train_matrix, clinical_eval_matrix = _tabular_matrices(
        clinical_train, clinical_eval, data.study
    )
    return (
        np.column_stack([clinical_train_matrix, modality_train_matrix]),
        np.column_stack([clinical_eval_matrix, modality_eval_matrix]),
    )


def _assemble_calibration_features(
    data: StudyData, model_id: str, seed: int, config: Mapping[str, object]
) -> tuple[np.ndarray, np.ndarray]:
    clinical_train = data.clinical_train
    clinical_eval = data.clinical_calibration
    if model_id == "B0":
        return np.zeros((len(clinical_train), 0)), np.zeros((len(clinical_eval), 0))
    if model_id in {"B1", "B2", "B3"}:
        return _tabular_matrices(clinical_train, clinical_eval, data.study)
    modality_train = data.modality_train
    modality_eval = data.modality_calibration
    if model_id in {"B4", "B5", "N0"} and (modality_train is None or modality_eval is None):
        raise ValueError(data.modality_blocker or "additional modality unavailable")
    if model_id == "M0":
        full_train = clinical_train
        full_eval = clinical_eval
        if modality_train is not None and modality_eval is not None:
            full_train = pd.concat([full_train, modality_train], axis=1)
            full_eval = pd.concat([full_eval, modality_eval], axis=1)
        return _fit_missingness(full_train, full_eval)
    assert modality_train is not None and modality_eval is not None
    if model_id == "N0":
        modality_train = _permuted(modality_train, seed * 2003 + 31)
        modality_eval = _permuted(modality_eval, seed * 2011 + 37)
    if data.study == "TCGA-HNSC":
        prep = NumericMatrixPreprocessor(
            top_k=int(config.get("tcga_expression_foldwise_variance_top_k", 500))
        )
        train_modality_matrix = prep.fit_transform(modality_train)
        eval_modality_matrix = prep.transform(modality_eval)
    else:
        train_modality_matrix, eval_modality_matrix = _tabular_matrices(
            modality_train, modality_eval, data.study
        )
    if model_id in {"B4", "N0"}:
        return train_modality_matrix, eval_modality_matrix
    train_clinical_matrix, eval_clinical_matrix = _tabular_matrices(
        clinical_train, clinical_eval, data.study
    )
    return (
        np.column_stack([train_clinical_matrix, train_modality_matrix]),
        np.column_stack([eval_clinical_matrix, eval_modality_matrix]),
    )


def _fit_with_diagnostics(
    model_id: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_eval: np.ndarray,
    horizon: float,
    random_state: int,
    config: Mapping[str, object],
):
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        prediction = fit_predict_survival_model(
            model_id,
            x_train,
            y_train,
            x_eval,
            horizon,
            random_state,
            config,
        )
    relevant = sorted(
        {
            str(item.message)
            for item in captured
            if (
                "coefficients are zero" in str(item.message)
                or "did not converge" in str(item.message)
                or "missingness indicator varied" in str(item.message)
            )
        }
    )
    return prediction, relevant


def _metric_row(
    data: StudyData,
    partition: str,
    model_id: str,
    seed: int,
    risk_score: np.ndarray,
    risk_horizon: np.ndarray,
    horizon: float,
    survival_floor: float,
) -> dict[str, object]:
    if partition == "oof":
        eval_event, eval_time = data.train_event, data.train_time
    else:
        eval_event, eval_time = data.calibration_event, data.calibration_time
    metrics = evaluate_survival_predictions(
        data.train_event,
        data.train_time,
        eval_event,
        eval_time,
        risk_score,
        risk_horizon,
        horizon,
        survival_floor=survival_floor,
    )
    return {"study": data.study, "model": model_id, "seed": seed, "partition": partition, **metrics}


def _prediction_frame(
    ids: Sequence[str],
    event: np.ndarray,
    time: np.ndarray,
    risk_score: np.ndarray,
    risk_horizon: np.ndarray,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": ids,
            "event": event.astype(int),
            "duration_days": time,
            "risk_score": risk_score,
            "risk_horizon": risk_horizon,
        }
    )


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _stability(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return pd.DataFrame()
    value_columns = [
        "ipcw_brier",
        "harrell_c",
        "uno_c",
        "auc_horizon",
        "calibration_in_the_large",
        "calibration_slope",
        "mean_predicted_risk",
    ]
    grouped = metrics.groupby(["study", "model", "partition"], dropna=False)[value_columns]
    means = grouped.mean().add_suffix("_mean")
    stds = grouped.std(ddof=1).add_suffix("_sd")
    counts = grouped.size().rename("successful_seeds")
    return pd.concat([means, stds, counts], axis=1).reset_index()


def _plot_metric_comparison(metrics: pd.DataFrame, partition: str, path: Path) -> None:
    subset = metrics.loc[metrics["partition"].eq(partition)].copy()
    summary = subset.groupby(["study", "model"])["ipcw_brier"].agg(["mean", "std"]).reset_index()
    studies = list(summary["study"].drop_duplicates())
    fig, axes = plt.subplots(
        1, max(1, len(studies)), figsize=(5.2 * max(1, len(studies)), 4.5), squeeze=False
    )
    for axis, study in zip(axes[0], studies, strict=False):
        local = summary.loc[summary["study"].eq(study)]
        axis.bar(local["model"], local["mean"], yerr=local["std"].fillna(0), capsize=3)
        axis.set_title(study)
        axis.set_xlabel("Prespecified baseline")
        axis.set_ylabel("24-month IPCW Brier score")
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle(f"Phase 3 {partition.upper()} development performance (mean +/- SD over seeds)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def _plot_dca(dca: pd.DataFrame, path: Path) -> None:
    mean = dca.groupby(["study", "model", "partition", "threshold"], as_index=False)[
        "net_benefit_model"
    ].mean()
    studies = list(mean["study"].drop_duplicates())
    fig, axes = plt.subplots(
        1, max(1, len(studies)), figsize=(5.2 * max(1, len(studies)), 4.5), squeeze=False
    )
    for axis, study in zip(axes[0], studies, strict=False):
        local = mean.loc[(mean["study"].eq(study)) & (mean["partition"].eq("calibration"))]
        for model, rows in local.groupby("model"):
            axis.plot(rows["threshold"], rows["net_benefit_model"], marker="o", ms=2.5, label=model)
        axis.axhline(0, color="black", lw=0.8)
        axis.set_title(study)
        axis.set_xlabel("Risk threshold")
        axis.set_ylabel("IPCW net benefit")
        axis.grid(alpha=0.25)
        axis.legend(fontsize=7, ncol=2)
    fig.suptitle("Phase 3 calibration-partition decision curves")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)


def _assert_aggregate_privacy(paths: Sequence[Path]) -> None:
    forbidden_headers = {"native_id", "patient_id", "sample_id", "source_row_number"}
    patterns = [r"RADCURE-\d{4,}", r"TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}", r"GSM\d{4,}"]
    for path in paths:
        if path.suffix == ".csv" and path.stat().st_size:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                headers = set(next(csv.reader(handle)))
            if headers & forbidden_headers:
                raise RuntimeError(f"identifier header leaked to tracked output {path}")
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if re.search(pattern, text):
                raise RuntimeError(f"patient identifier pattern leaked to tracked output {path}")


def _leakage_audit(status: pd.DataFrame, metrics: pd.DataFrame) -> str:
    completed = int(status["status"].str.startswith("complete").sum()) if not status.empty else 0
    warned = int(status["status"].eq("complete_with_warning").sum()) if not status.empty else 0
    failed = int(status["status"].eq("failed").sum()) if not status.empty else 0
    blocked = int(status["status"].eq("blocked").sum()) if not status.empty else 0
    return f"""# Phase 3 leakage and governance audit

**Scope:** development-only B0-B5/M0/N0 baselines. Phase 4 and sealed/external
 evaluation were not authorized.

## Controls verified by implementation

- Only eligible, endpoint-usable, frozen train/calibration rows are loaded.
- OOF folds use event-stratified patient-level indices inside frozen training data.
- Imputation, encoding, scaling, and TCGA top-500 selection fit within each fold.
- Calibration rows never fit preprocessing, selection, or model parameters.
- Censoring before 24 months receives zero IPCW weight, not a survivor label.
- N0 permutations are outcome-independent and partition-local.
- Patient predictions stay in Git-ignored `results/predictions/phase3/`.
- Tracked metrics, figures, audit, and receipt contain aggregate data only.
- Sealed RADCURE/HANCOCK and external GEO outcomes were not loaded.
- Phase 4 learners, gates, decisions, and threshold optimization were not run.

## Run accounting

- Complete study/model/seed runs: {completed}
- Complete runs carrying fit diagnostics: {warned}
- Failed study/model/seed runs: {failed}
- Governance-blocked model entries: {blocked}
- Aggregate metric rows: {len(metrics)}

## Persistent blocker

RADCURE B4/B5/N0 remain NO-GO because the ORCESTRA RDS structure has not been
validated with R/Rscript or a validated parser.
"""


def run(project_root: Path) -> dict[str, object]:
    root = Path(project_root).resolve()
    config_path = root / "configs/phase3_baselines.json"
    governance_path = root / "configs/phase3_governance.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    governance = json.loads(governance_path.read_text(encoding="utf-8-sig"))
    if (
        config.get("phase4_authorized")
        or config.get("sealed_outcomes_authorized")
        or config.get("external_outcomes_authorized")
    ):
        raise RuntimeError("Phase 3 configuration violates the authorized boundary")
    if governance.get("test_unseal_allowed"):
        raise RuntimeError("Phase 3 governance unexpectedly allows test unsealing")

    horizon = float(config["horizon_days"])
    folds = int(config["cv_folds"])
    seeds = [int(value) for value in config["seeds"]]
    hyper = dict(config["hyperparameters"])
    floor = float(hyper["ipcw_survival_floor"])
    thresholds = [float(value) for value in hyper["dca_thresholds"]]
    prediction_root = root / "results/predictions/phase3"
    metric_root = root / "results/metrics/phase3"
    figure_root = root / "results/figures/phase3"
    prediction_root.mkdir(parents=True, exist_ok=True)
    metric_root.mkdir(parents=True, exist_ok=True)

    metric_rows: list[dict[str, object]] = []
    dca_rows: list[dict[str, object]] = []
    status_rows: list[dict[str, object]] = []
    studies = ["RADCURE", "HANCOCK", "TCGA-HNSC"]
    for study in studies:
        data = load_phase3_study_data(root, study, build_expression=study == "TCGA-HNSC")
        scope = config["study_scope"][study]
        for blocked_model in scope.get("blocked_models", []):
            status_rows.append(
                {
                    "study": study,
                    "model": blocked_model,
                    "seed": "",
                    "status": "blocked",
                    "reason": scope["blocker"],
                }
            )
        for model_id in scope["models"]:
            for seed in seeds:
                try:
                    run_warnings: set[str] = set()
                    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
                    oof_score = np.full(data.n_train, np.nan)
                    oof_risk = np.full(data.n_train, np.nan)
                    for fold_index, (fit_indices, eval_indices) in enumerate(
                        splitter.split(np.zeros(data.n_train), data.train_event)
                    ):
                        x_fit, x_eval = _assemble_features(
                            data,
                            model_id,
                            fit_indices,
                            eval_indices,
                            seed * 100 + fold_index,
                            hyper,
                        )
                        prediction, fit_warnings = _fit_with_diagnostics(
                            model_id,
                            x_fit,
                            structured_survival(
                                data.train_event[fit_indices], data.train_time[fit_indices]
                            ),
                            x_eval,
                            horizon,
                            seed * 100 + fold_index,
                            hyper,
                        )
                        run_warnings.update(fit_warnings)
                        oof_score[eval_indices] = prediction.risk_score
                        oof_risk[eval_indices] = prediction.risk_horizon
                    if not np.isfinite(oof_score).all() or not np.isfinite(oof_risk).all():
                        raise RuntimeError("OOF predictions are incomplete or non-finite")
                    x_train, x_calibration = _assemble_calibration_features(
                        data, model_id, seed, hyper
                    )
                    calibration_prediction, fit_warnings = _fit_with_diagnostics(
                        model_id,
                        x_train,
                        structured_survival(data.train_event, data.train_time),
                        x_calibration,
                        horizon,
                        seed,
                        hyper,
                    )
                    run_warnings.update(fit_warnings)
                    oof_row = _metric_row(
                        data, "oof", model_id, seed, oof_score, oof_risk, horizon, floor
                    )
                    calibration_row = _metric_row(
                        data,
                        "calibration",
                        model_id,
                        seed,
                        calibration_prediction.risk_score,
                        calibration_prediction.risk_horizon,
                        horizon,
                        floor,
                    )
                    metric_rows.extend([oof_row, calibration_row])
                    for partition, event, time, risk in [
                        ("oof", data.train_event, data.train_time, oof_risk),
                        (
                            "calibration",
                            data.calibration_event,
                            data.calibration_time,
                            calibration_prediction.risk_horizon,
                        ),
                    ]:
                        for row in decision_curve_ipcw(
                            data.train_event,
                            data.train_time,
                            event,
                            time,
                            risk,
                            horizon,
                            thresholds,
                            survival_floor=floor,
                        ):
                            dca_rows.append(
                                {
                                    "study": study,
                                    "model": model_id,
                                    "seed": seed,
                                    "partition": partition,
                                    **row,
                                }
                            )
                    slug = study.casefold().replace("-", "_")
                    _prediction_frame(
                        data.train_ids, data.train_event, data.train_time, oof_score, oof_risk
                    ).to_csv(prediction_root / f"{slug}_{model_id}_seed{seed}_oof.csv", index=False)
                    _prediction_frame(
                        data.calibration_ids,
                        data.calibration_event,
                        data.calibration_time,
                        calibration_prediction.risk_score,
                        calibration_prediction.risk_horizon,
                    ).to_csv(
                        prediction_root / f"{slug}_{model_id}_seed{seed}_calibration.csv",
                        index=False,
                    )
                    status_rows.append(
                        {
                            "study": study,
                            "model": model_id,
                            "seed": seed,
                            "status": ("complete_with_warning" if run_warnings else "complete"),
                            "reason": " | ".join(sorted(run_warnings)),
                        }
                    )
                except Exception as exc:
                    status_rows.append(
                        {
                            "study": study,
                            "model": model_id,
                            "seed": seed,
                            "status": "failed",
                            "reason": f"{type(exc).__name__}: {exc}",
                        }
                    )

    metrics = pd.DataFrame(metric_rows)
    dca = pd.DataFrame(dca_rows)
    status = pd.DataFrame(status_rows)
    oof_path = metric_root / "oof_metrics.csv"
    calibration_path = metric_root / "calibration_metrics.csv"
    stability_path = metric_root / "stability_summary.csv"
    status_path = metric_root / "model_status.csv"
    dca_path = metric_root / "decision_curve.csv"
    metrics.loc[metrics["partition"].eq("oof")].drop(columns="partition").to_csv(
        oof_path, index=False
    )
    metrics.loc[metrics["partition"].eq("calibration")].drop(columns="partition").to_csv(
        calibration_path, index=False
    )
    _stability(metrics).to_csv(stability_path, index=False)
    status.to_csv(status_path, index=False)
    dca.to_csv(dca_path, index=False)

    oof_figure = figure_root / "oof_metric_comparison.svg"
    calibration_figure = figure_root / "calibration_metric_comparison.svg"
    dca_figure = figure_root / "decision_curve.svg"
    _plot_metric_comparison(metrics, "oof", oof_figure)
    _plot_metric_comparison(metrics, "calibration", calibration_figure)
    _plot_dca(dca, dca_figure)

    audit_path = root / "docs/audits/phase3/leakage_audit.md"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(_leakage_audit(status, metrics), encoding="utf-8")
    public_paths = [
        oof_path,
        calibration_path,
        stability_path,
        status_path,
        dca_path,
        oof_figure,
        calibration_figure,
        dca_figure,
        audit_path,
    ]
    _assert_aggregate_privacy(public_paths)

    receipt_path = root / "results/manifests/phase3_baseline_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "3.0",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "phase": "Phase 3 development-only baselines",
        "horizon_days": horizon,
        "cv_folds": folds,
        "seeds": seeds,
        "successful_runs": int(status["status"].str.startswith("complete").sum()),
        "successful_runs_with_warnings": int(status["status"].eq("complete_with_warning").sum()),
        "failed_runs": int(status["status"].eq("failed").sum()),
        "blocked_entries": int(status["status"].eq("blocked").sum()),
        "patient_prediction_directory": "results/predictions/phase3 (Git-ignored)",
        "sealed_or_external_outcomes_used": False,
        "phase4_components_used": False,
        "config_sha256": {
            config_path.relative_to(root).as_posix(): _sha256(config_path),
            governance_path.relative_to(root).as_posix(): _sha256(governance_path),
        },
        "aggregate_output_sha256": {
            path.relative_to(root).as_posix(): _sha256(path) for path in public_paths
        },
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {**receipt, "receipt": receipt_path.relative_to(root).as_posix()}
