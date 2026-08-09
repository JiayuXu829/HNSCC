"""Locked Phase 6 external prediction, outcome loading, and paired statistics."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from trust_hn.data.adapters.radcure import derive_treatment_start_os
from trust_hn.data.adapters.transcriptomics import MONTH_DAYS
from trust_hn.data.phase3_features import StudyData
from trust_hn.data.phase6_data import CohortFeatures
from trust_hn.evaluation.phase3 import (
    NumericMatrixPreprocessor,
    _infer_columns,
    _missingness_matrix,
)
from trust_hn.evaluation.phase5 import StressSystem, _rank_reliability
from trust_hn.metrics.survival import decision_curve_ipcw, evaluate_survival_predictions
from trust_hn.models.survival_baselines import TabularPreprocessor
from trust_hn.reliability.ablations import ablated_unreliability
from trust_hn.reliability.gating import assign_actions, gated_risk, quantile_threshold


@dataclass(frozen=True)
class OutcomeData:
    cohort: str
    ids: np.ndarray
    event: np.ndarray
    time: np.ndarray

    def __post_init__(self) -> None:
        if not (len(self.ids) == len(self.event) == len(self.time)):
            raise ValueError(f"outcome alignment failed for {self.cohort}")
        if len(set(self.ids.astype(str))) != len(self.ids):
            raise ValueError(f"duplicate outcome IDs in {self.cohort}")
        if not np.isfinite(self.time).all() or np.any(self.time < 0):
            raise ValueError(f"invalid survival times in {self.cohort}")


class Phase6StressSystem(StressSystem):
    """StressSystem with the frozen Phase 6 numeric modality preprocessing policy."""

    def _fit_preprocessors(self) -> None:
        clinical_train = self.data.clinical_train
        numeric, categorical = _infer_columns(clinical_train, self.data.study)
        self.clinical_prep = TabularPreprocessor(numeric, categorical).fit(clinical_train)
        self.clinical_train_matrix = self.clinical_prep.transform(clinical_train)
        self.clinical_eval_matrix = self.clinical_prep.transform(self.data.clinical_calibration)
        if self.data.modality_train is None:
            raise ValueError("additional modality unavailable")
        modality_train = self._representation_frame(self.data.modality_train)
        if self.data.study in {"TCGA-HNSC", "RADCURE"}:
            key = (
                "radcure_radiomics_foldwise_variance_top_k"
                if self.data.study == "RADCURE"
                else "tcga_expression_foldwise_variance_top_k"
            )
            self.modality_prep = NumericMatrixPreprocessor(
                top_k=int(self.config.get(key, 500))
            ).fit(modality_train)
        else:
            numeric, categorical = _infer_columns(modality_train, self.data.study)
            self.modality_prep = TabularPreprocessor(numeric, categorical).fit(modality_train)
        self.modality_train_matrix = self.modality_prep.transform(modality_train)


def predict_external(
    system: StressSystem,
    clinical_eval: pd.DataFrame,
    modality_eval_raw: pd.DataFrame,
    *,
    scenario_seed: int,
) -> pd.DataFrame:
    """Predict an arbitrary aligned cohort without mutating development calibration state."""
    required = (
        system.clinical_prep,
        system.modality_prep,
        system.b2,
        system.b3,
        system.b4,
        system.b5,
        system.b6,
        system.clinical_detector,
        system.modality_detector,
        system.clinical_bootstrap,
        system.fusion_bootstrap,
    )
    if any(item is None for item in required):
        raise RuntimeError("Phase 6 system must be fitted")
    if len(clinical_eval) != len(modality_eval_raw):
        raise ValueError("external clinical/modality row counts differ")
    modality_eval = system._representation_frame(modality_eval_raw)
    x_clinical = system.clinical_prep.transform(clinical_eval)  # type: ignore[union-attr]
    x_modality = system.modality_prep.transform(modality_eval)  # type: ignore[union-attr]
    b2 = system.b2.predict(x_clinical)  # type: ignore[union-attr]
    b3 = system.b3.predict(x_clinical)  # type: ignore[union-attr]
    b4 = system.b4.predict(x_modality)  # type: ignore[union-attr]
    b5 = system.b5.predict(np.column_stack([x_clinical, x_modality]))  # type: ignore[union-attr]
    b6 = system.b6.predict(b2.risk_score, x_modality)  # type: ignore[union-attr]
    permutation = np.random.default_rng(scenario_seed + 109).permutation(len(x_modality))
    perturbed = system.b6.predict(b2.risk_score, x_modality[permutation])  # type: ignore[union-attr]
    clinical_ood = system.clinical_detector.score(x_clinical)  # type: ignore[union-attr]
    modality_ood = system.modality_detector.score(x_modality)  # type: ignore[union-attr]
    clinical_ensemble = [
        model.predict(x_clinical).risk_horizon for model in system.clinical_bootstrap or []
    ]
    fusion_ensemble = [
        model.predict(b2.risk_score, x_modality).risk_horizon
        for model in system.fusion_bootstrap or []
    ]
    clinical_summary = system._ensemble_summary(clinical_ensemble, len(x_clinical))
    fusion_summary = system._ensemble_summary(fusion_ensemble, len(x_clinical))
    missingness = _missingness_matrix(modality_eval_raw)
    missing_fraction = (
        missingness.mean(axis=1) if missingness.shape[1] else np.zeros(len(x_clinical))
    )
    frame = pd.DataFrame(
        {
            "b2_score": b2.risk_score,
            "b2_risk": b2.risk_horizon,
            "b3_score": b3.risk_score,
            "b3_risk": b3.risk_horizon,
            "b4_score": b4.risk_score,
            "b4_risk": b4.risk_horizon,
            "b5_score": b5.risk_score,
            "b5_risk": b5.risk_horizon,
            "b6_score": b6.risk_score,
            "b6_risk": b6.risk_horizon,
            "clinical_uncertainty_median": clinical_summary[0],
            "clinical_uncertainty_sd": clinical_summary[1],
            "clinical_uncertainty_lower95": clinical_summary[2],
            "clinical_uncertainty_upper95": clinical_summary[3],
            "clinical_uncertainty_width95": clinical_summary[4],
            "clinical_model_disagreement": np.abs(b2.risk_horizon - b3.risk_horizon),
            "fusion_uncertainty_median": fusion_summary[0],
            "fusion_uncertainty_sd": fusion_summary[1],
            "fusion_uncertainty_lower95": fusion_summary[2],
            "fusion_uncertainty_upper95": fusion_summary[3],
            "fusion_uncertainty_width95": fusion_summary[4],
            "perturbation_sensitivity": np.abs(b6.risk_horizon - perturbed.risk_horizon),
            "modality_missingness": missing_fraction,
            "modality_missing": missing_fraction >= 1.0 - 1e-12,
            "fusion_disagreement": np.abs(b6.risk_horizon - b5.risk_horizon),
            "clinical_ood_mahalanobis": clinical_ood.mahalanobis,
            "clinical_ood_knn": clinical_ood.knn,
            "clinical_ood_isolation_forest": clinical_ood.isolation_forest,
            "modality_ood_mahalanobis": modality_ood.mahalanobis,
            "modality_ood_knn": modality_ood.knn,
            "modality_ood_isolation_forest": modality_ood.isolation_forest,
        }
    )
    if system.m0 is not None and system.m0_variable is not None:
        full_eval = pd.concat(
            [clinical_eval.reset_index(drop=True), modality_eval_raw.reset_index(drop=True)],
            axis=1,
        )
        m0 = system.m0.predict(_missingness_matrix(full_eval)[:, system.m0_variable])
        frame["m0_score"], frame["m0_risk"] = m0.risk_score, m0.risk_horizon
    return frame


def gated_external_predictions(
    system: StressSystem,
    development: StudyData,
    external: CohortFeatures,
    *,
    seed: int,
    coverages: Sequence[float] = (0.8, 0.9, 1.0),
) -> pd.DataFrame:
    if development.modality_calibration is None:
        raise ValueError("development calibration modality is unavailable")
    calibration_raw = predict_external(
        system,
        development.clinical_calibration,
        development.modality_calibration,
        scenario_seed=seed,
    )
    calibration_ranked = _rank_reliability(calibration_raw, calibration_raw)
    external_raw = predict_external(
        system,
        external.clinical,
        external.modality,
        scenario_seed=seed,
    )
    external_ranked = _rank_reliability(external_raw, calibration_raw)
    calibration_clinical, calibration_modality = ablated_unreliability(
        calibration_ranked, "full_equal_weight"
    )
    external_clinical, external_modality = ablated_unreliability(
        external_ranked, "full_equal_weight"
    )
    result = external_ranked.copy()
    for coverage in coverages:
        label = str(round(float(coverage) * 100))
        clinical_threshold = quantile_threshold(calibration_clinical, float(coverage))
        modality_threshold = quantile_threshold(calibration_modality, float(coverage))
        actions, reasons = assign_actions(
            external_clinical,
            external_modality,
            result["modality_missing"].to_numpy(dtype=bool),
            clinical_threshold=clinical_threshold,
            modality_threshold=modality_threshold,
        )
        result[f"b7_action_{label}"] = actions
        result[f"b7_reason_{label}"] = reasons
        result[f"b7_risk_{label}"] = gated_risk(
            result["b2_risk"].to_numpy(dtype=float),
            result["b6_risk"].to_numpy(dtype=float),
            actions,
        )
        result[f"clinical_threshold_{label}"] = clinical_threshold
        result[f"modality_threshold_{label}"] = modality_threshold
    return result


def aggregate_seed_predictions(
    seed_frames: Sequence[pd.DataFrame], *, primary_profile: str = "90"
) -> pd.DataFrame:
    if not seed_frames:
        raise ValueError("at least one seed prediction frame is required")
    lengths = {len(frame) for frame in seed_frames}
    if len(lengths) != 1:
        raise ValueError("seed prediction row counts differ")
    result = pd.DataFrame(index=seed_frames[0].index)
    for model in ("b2", "b4", "b5", "b6"):
        for suffix in ("score", "risk"):
            column = f"{model}_{suffix}"
            result[column] = np.mean(
                np.vstack([frame[column].to_numpy(dtype=float) for frame in seed_frames]),
                axis=0,
            )
    actions = np.vstack(
        [frame[f"b7_action_{primary_profile}"].astype(str).to_numpy() for frame in seed_frames]
    )
    abstain_votes = np.sum(actions == "ABSTAIN", axis=0)
    fallback_votes = np.sum(actions == "FALLBACK", axis=0)
    majority = len(seed_frames) // 2 + 1
    consensus = np.full(actions.shape[1], "AUGMENT", dtype="U8")
    consensus[fallback_votes >= majority] = "FALLBACK"
    consensus[abstain_votes >= majority] = "ABSTAIN"
    seed_risks = np.vstack(
        [frame[f"b7_risk_{primary_profile}"].to_numpy(dtype=float) for frame in seed_frames]
    )
    with np.errstate(invalid="ignore"):
        b7 = np.nanmean(seed_risks, axis=0)
    b7[consensus == "FALLBACK"] = result.loc[consensus == "FALLBACK", "b2_risk"]
    b7[consensus == "ABSTAIN"] = np.nan
    result["b7_action"] = consensus
    result["b7_risk"] = b7
    result["b7_score"] = b7
    result["non_abstaining_seed_count"] = np.sum(np.isfinite(seed_risks), axis=0)
    return result


def _read_geo_characteristics(
    path: Path, wanted: set[str]
) -> tuple[np.ndarray, dict[str, list[str]]]:
    sample_ids: list[str] | None = None
    fields: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.startswith("!Sample_geo_accession"):
                row = next(csv.reader([line.rstrip("\r\n")], delimiter="\t"))
                sample_ids = [value.strip('"') for value in row[1:]]
            elif line.startswith("!Sample_characteristics_ch1"):
                row = next(csv.reader([line.rstrip("\r\n")], delimiter="\t"))
                values = [value.strip('"') for value in row[1:]]
                labels = [value.split(":", 1)[0].strip() for value in values]
                if labels and len(set(labels)) == 1 and labels[0] in wanted:
                    fields[labels[0]] = [
                        value.split(":", 1)[1].strip() if ":" in value else value.strip()
                        for value in values
                    ]
            if line.startswith("!series_matrix_table_begin"):
                break
    if sample_ids is None or set(fields) != wanted:
        raise ValueError(f"required GEO outcomes missing from {path}")
    return np.asarray(sample_ids), fields


def assert_outcome_access_consumed(project_root: Path) -> None:
    path = Path(project_root) / "configs/analysis_freeze.yaml"
    payload = json.loads(path.read_text(encoding="utf-8"))
    unseal = payload.get("test_unseal") or {}
    if payload.get("phase6_outcomes_seen") is not True or unseal.get("consumed") is not True:
        raise PermissionError("Phase 6 outcome authorization has not been consumed")


def _align_outcomes(
    cohort: str,
    source_ids: Sequence[str],
    event: Sequence[bool],
    time: Sequence[float],
    expected_ids: Sequence[str],
) -> OutcomeData:
    frame = pd.DataFrame(
        {
            "native_id": np.asarray(source_ids, dtype=str),
            "event": np.asarray(event, dtype=bool),
            "time": np.asarray(time, dtype=float),
        }
    )
    if frame["native_id"].duplicated().any():
        raise ValueError(f"duplicate source outcomes in {cohort}")
    selected = frame.set_index("native_id").reindex(np.asarray(expected_ids, dtype=str))
    if selected[["event", "time"]].isna().any().any():
        raise ValueError(f"missing frozen outcomes in {cohort}")
    return OutcomeData(
        cohort,
        np.asarray(expected_ids, dtype=str),
        selected["event"].to_numpy(dtype=bool),
        selected["time"].to_numpy(dtype=float),
    )


def load_phase6_outcomes(
    project_root: Path, cohort: str, expected_ids: Sequence[str]
) -> OutcomeData:
    root = Path(project_root)
    assert_outcome_access_consumed(root)
    canonical = cohort.strip().upper()
    if canonical == "RADCURE":
        path = root / (
            "data/interim/radcure/v04_20241219/clinical_csv/"
            "01_RADCURE_TCIA_Clinical_r2_offset.csv"
        )
        frame = pd.read_csv(
            path,
            usecols=["patient_id", "RT Start", "Last FU", "Status", "Date of Death"],
            dtype={"patient_id": "string"},
        )
        pairs = [
            derive_treatment_start_os(str(a), str(b), str(c), str(d) if pd.notna(d) else "")
            for a, b, c, d in frame[
                ["RT Start", "Last FU", "Status", "Date of Death"]
            ].itertuples(index=False, name=None)
        ]
        return _align_outcomes(
            canonical,
            frame["patient_id"].astype(str).str.strip(),
            [bool(pair[1]) for pair in pairs],
            [pair[0] for pair in pairs],
            expected_ids,
        )
    if canonical == "HANCOCK":
        path = next((root / "data/interim/hancock").rglob("features/targets.csv"))
        frame = pd.read_csv(
            path,
            usecols=["patient_id", "survival_status", "days_to_last_information"],
            dtype={"patient_id": "string"},
        )
        ids = frame["patient_id"].astype("string").str.strip().str.zfill(3)
        status = frame["survival_status"].astype(str).str.strip().str.casefold()
        if not status.isin(["living", "deceased"]).all():
            raise ValueError("unrecognized HANCOCK survival status")
        return _align_outcomes(
            canonical,
            ids,
            status.eq("deceased"),
            pd.to_numeric(frame["days_to_last_information"], errors="raise"),
            expected_ids,
        )
    if canonical == "GSE65858":
        path = root / "data/interim/gse65858/geo_2026-06-03/GSE65858_series_matrix.txt"
        ids, fields = _read_geo_characteristics(path, {"os", "os_event"})
        event_text = pd.Series(fields["os_event"]).str.strip().str.casefold()
        if not event_text.isin(["true", "false"]).all():
            raise ValueError("unrecognized GSE65858 event value")
        return _align_outcomes(
            canonical,
            ids,
            event_text.eq("true"),
            pd.to_numeric(pd.Series(fields["os"]), errors="raise"),
            expected_ids,
        )
    if canonical == "GSE41613":
        path = root / "data/interim/gse41613/geo_2026-07-06/GSE41613_series_matrix.txt"
        ids, fields = _read_geo_characteristics(path, {"fu time", "vital"})
        status = pd.Series(fields["vital"]).str.strip()
        valid = status.eq("Alive") | status.str.startswith("Dead")
        if not valid.all():
            raise ValueError("unrecognized GSE41613 vital status")
        return _align_outcomes(
            canonical,
            ids,
            status.str.startswith("Dead"),
            pd.to_numeric(pd.Series(fields["fu time"]), errors="raise") * MONTH_DAYS,
            expected_ids,
        )
    raise ValueError(f"unsupported Phase 6 outcome cohort: {cohort}")


def model_metrics(
    development: StudyData,
    outcomes: OutcomeData,
    predictions: pd.DataFrame,
    *,
    horizon: float,
    survival_floor: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for model in ("b2", "b4", "b5", "b6", "b7"):
        score = predictions[f"{model}_score"].to_numpy(dtype=float)
        risk = predictions[f"{model}_risk"].to_numpy(dtype=float)
        finite = np.isfinite(score) & np.isfinite(risk)
        base = {
            "cohort": outcomes.cohort,
            "model": model.upper(),
            "parent_n": len(outcomes.ids),
            "coverage": float(np.mean(finite)),
        }
        if not finite.any():
            rows.append({**base, "n": 0.0, "events": 0.0, "ipcw_brier": math.nan})
            continue
        metrics = evaluate_survival_predictions(
            development.train_event,
            development.train_time,
            outcomes.event[finite],
            outcomes.time[finite],
            score[finite],
            risk[finite],
            horizon,
            survival_floor=survival_floor,
        )
        rows.append({**base, **metrics})
    return rows


def paired_comparison_metrics(
    development: StudyData,
    outcomes: OutcomeData,
    predictions: pd.DataFrame,
    *,
    horizon: float,
    survival_floor: float,
) -> pd.DataFrame:
    """Point estimates for frozen paired comparisons on identical subsets."""
    b7_mask = np.isfinite(predictions["b7_risk"].to_numpy(dtype=float))
    comparisons = (
        ("B7", "B6", b7_mask),
        ("B7", "B2", b7_mask),
        ("B6", "B5", np.ones(len(outcomes.ids), dtype=bool)),
    )
    metric_names = ("ipcw_brier", "harrell_c", "uno_c", "auc_horizon")
    rows: list[dict[str, object]] = []
    for left, right, eligible in comparisons:
        local = np.flatnonzero(eligible)
        left_values = evaluate_survival_predictions(
            development.train_event, development.train_time,
            outcomes.event[local], outcomes.time[local],
            predictions[f"{left.lower()}_score"].to_numpy(dtype=float)[local],
            predictions[f"{left.lower()}_risk"].to_numpy(dtype=float)[local],
            horizon, survival_floor=survival_floor,
        )
        right_values = evaluate_survival_predictions(
            development.train_event, development.train_time,
            outcomes.event[local], outcomes.time[local],
            predictions[f"{right.lower()}_score"].to_numpy(dtype=float)[local],
            predictions[f"{right.lower()}_risk"].to_numpy(dtype=float)[local],
            horizon, survival_floor=survival_floor,
        )
        row: dict[str, object] = {"comparison": f"{left}_vs_{right}", "n": int(local.size)}
        for metric in metric_names:
            row[f"difference_{metric}"] = left_values[metric] - right_values[metric]
        rows.append(row)
    return pd.DataFrame(rows)


def paired_bootstrap_metrics(
    development: StudyData,
    outcomes: OutcomeData,
    predictions: pd.DataFrame,
    *,
    replicates: int,
    random_state: int,
    horizon: float,
    survival_floor: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Patient-level paired bootstrap using one index draw for every model per replicate."""
    if replicates < 1:
        raise ValueError("bootstrap replicates must be positive")
    rng = np.random.default_rng(random_state)
    model_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []
    b7_mask = np.isfinite(predictions["b7_risk"].to_numpy(dtype=float))
    comparisons = (
        ("B7", "B6", b7_mask),
        ("B7", "B2", b7_mask),
        ("B6", "B5", np.ones(len(outcomes.ids), dtype=bool)),
    )
    metric_names = ("ipcw_brier", "harrell_c", "uno_c", "auc_horizon")
    for replicate in range(replicates):
        indices = rng.integers(0, len(outcomes.ids), size=len(outcomes.ids))
        for model in ("B2", "B4", "B5", "B6", "B7"):
            score = predictions[f"{model.lower()}_score"].to_numpy(dtype=float)[indices]
            risk = predictions[f"{model.lower()}_risk"].to_numpy(dtype=float)[indices]
            finite = np.isfinite(score) & np.isfinite(risk)
            if not finite.any():
                continue
            values = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                outcomes.event[indices][finite],
                outcomes.time[indices][finite],
                score[finite],
                risk[finite],
                horizon,
                survival_floor=survival_floor,
            )
            model_rows.append({"replicate": replicate, "model": model, **values})
        for left, right, eligible in comparisons:
            local = indices[eligible[indices]]
            if local.size == 0:
                continue
            left_score = predictions[f"{left.lower()}_score"].to_numpy(dtype=float)[local]
            left_risk = predictions[f"{left.lower()}_risk"].to_numpy(dtype=float)[local]
            right_score = predictions[f"{right.lower()}_score"].to_numpy(dtype=float)[local]
            right_risk = predictions[f"{right.lower()}_risk"].to_numpy(dtype=float)[local]
            left_values = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                outcomes.event[local],
                outcomes.time[local],
                left_score,
                left_risk,
                horizon,
                survival_floor=survival_floor,
            )
            right_values = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                outcomes.event[local],
                outcomes.time[local],
                right_score,
                right_risk,
                horizon,
                survival_floor=survival_floor,
            )
            row: dict[str, object] = {
                "replicate": replicate,
                "comparison": f"{left}_vs_{right}",
                "n": int(local.size),
            }
            for metric in metric_names:
                row[f"difference_{metric}"] = left_values[metric] - right_values[metric]
            comparison_rows.append(row)
    return pd.DataFrame(model_rows), pd.DataFrame(comparison_rows)


def paired_prediction_set_bootstrap(
    development: StudyData,
    outcomes: OutcomeData,
    reference: pd.DataFrame,
    controls: dict[str, pd.DataFrame],
    *,
    models: Sequence[str],
    replicates: int,
    random_state: int,
    horizon: float,
    survival_floor: float,
) -> pd.DataFrame:
    """Compare aligned prediction sets with shared patient-level resamples."""
    if replicates < 1:
        raise ValueError("bootstrap replicates must be positive")
    n = len(outcomes.ids)
    if len(reference) != n or any(len(frame) != n for frame in controls.values()):
        raise ValueError("prediction-set row counts do not match outcomes")
    rng = np.random.default_rng(random_state)
    metric_names = ("ipcw_brier", "harrell_c", "uno_c", "auc_horizon")
    rows: list[dict[str, object]] = []
    for replicate in range(replicates):
        indices = rng.integers(0, n, size=n)
        for control_name, control in controls.items():
            for model in models:
                prefix = model.lower()
                ref_score = reference[f"{prefix}_score"].to_numpy(dtype=float)
                ref_risk = reference[f"{prefix}_risk"].to_numpy(dtype=float)
                ctl_score = control[f"{prefix}_score"].to_numpy(dtype=float)
                ctl_risk = control[f"{prefix}_risk"].to_numpy(dtype=float)
                eligible = (
                    np.isfinite(ref_score)
                    & np.isfinite(ref_risk)
                    & np.isfinite(ctl_score)
                    & np.isfinite(ctl_risk)
                )
                local = indices[eligible[indices]]
                if local.size == 0:
                    continue
                reference_values = evaluate_survival_predictions(
                    development.train_event,
                    development.train_time,
                    outcomes.event[local],
                    outcomes.time[local],
                    ref_score[local],
                    ref_risk[local],
                    horizon,
                    survival_floor=survival_floor,
                )
                control_values = evaluate_survival_predictions(
                    development.train_event,
                    development.train_time,
                    outcomes.event[local],
                    outcomes.time[local],
                    ctl_score[local],
                    ctl_risk[local],
                    horizon,
                    survival_floor=survival_floor,
                )
                row: dict[str, object] = {
                    "replicate": replicate,
                    "model": model.upper(),
                    "reference_assay": "original",
                    "control_assay": control_name,
                    "n": int(local.size),
                }
                for metric in metric_names:
                    row[f"difference_{metric}"] = (
                        reference_values[metric] - control_values[metric]
                    )
                rows.append(row)
    return pd.DataFrame(rows)


def percentile_intervals(
    bootstrap: pd.DataFrame,
    *,
    group_columns: Sequence[str],
    value_columns: Sequence[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for keys, group in bootstrap.groupby(list(group_columns), dropna=False, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(group_columns, keys, strict=True))
        for column in value_columns:
            values = pd.to_numeric(group[column], errors="coerce").dropna().to_numpy(dtype=float)
            if values.size == 0:
                lower = median = upper = math.nan
            else:
                lower, median, upper = np.quantile(values, [0.025, 0.5, 0.975])
            rows.append(
                {
                    **base,
                    "metric": column,
                    "estimate_bootstrap_median": float(median),
                    "ci_lower_95": float(lower),
                    "ci_upper_95": float(upper),
                    "valid_replicates": int(values.size),
                }
            )
    return pd.DataFrame(rows)


def action_summary(cohort: str, predictions: pd.DataFrame) -> pd.DataFrame:
    counts = predictions["b7_action"].value_counts()
    return pd.DataFrame(
        [
            {
                "cohort": cohort,
                "action": action,
                "count": int(counts.get(action, 0)),
                "rate": float(counts.get(action, 0) / len(predictions)),
                "non_abstention_coverage": float(np.mean(predictions["b7_action"] != "ABSTAIN")),
            }
            for action in ("AUGMENT", "FALLBACK", "ABSTAIN")
        ]
    )


def decision_curve_rows(
    development: StudyData,
    outcomes: OutcomeData,
    predictions: pd.DataFrame,
    *,
    horizon: float,
    thresholds: Sequence[float],
    survival_floor: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for model in ("B2", "B6", "B7"):
        risk = predictions[f"{model.lower()}_risk"].to_numpy(dtype=float)
        finite = np.isfinite(risk)
        for row in decision_curve_ipcw(
            development.train_event,
            development.train_time,
            outcomes.event[finite],
            outcomes.time[finite],
            risk[finite],
            horizon,
            thresholds,
            survival_floor=survival_floor,
        ):
            rows.append({"cohort": outcomes.cohort, "model": model, **row})
    return pd.DataFrame(rows)


def load_phase6_configuration(project_root: Path) -> tuple[dict[str, object], dict[str, object]]:
    root = Path(project_root)
    phase6 = json.loads(
        (root / "configs/phase6_evaluation.json").read_text(encoding="utf-8-sig")
    )
    phase4 = json.loads((root / "configs/phase4_trust_hn.json").read_text(encoding="utf-8-sig"))
    config = {
        **phase4.get("hyperparameters", {}),
        "horizon_days": float(phase6["horizon_days"]),
        "cv_folds": int(phase4["cv_folds"]),
        "radcure_radiomics_foldwise_variance_top_k": int(
            phase6["cohorts"]["RADCURE"]["foldwise_variance_top_k"]
        ),
    }
    return phase6, config
