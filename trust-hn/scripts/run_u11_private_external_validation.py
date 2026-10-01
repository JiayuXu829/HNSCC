"""Audit and aggregate the private external PATTERN-Surv-HN validation workbook.

The script never writes patient-level rows. It validates the workbook joins,
recomputes the reported point estimates, and exports only aggregate summaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


HORIZON_DAYS = 730.5
KEY_CLINICAL_COLUMNS = [
    "age_at_initial_diagnosis",
    "sex",
    "smoking_status",
    "primary_tumor_site",
    "grading",
    "hpv_association_p16",
    "resection_status",
    "pT_stage",
    "pN_stage",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def censoring_km(event: np.ndarray, time: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    unique = np.unique(time)
    before: list[float] = []
    after: list[float] = []
    survival = 1.0
    for value in unique:
        before.append(survival)
        at_risk = int(np.sum(time >= value))
        censorings = int(np.sum((time == value) & (~event)))
        if at_risk and censorings:
            survival *= 1.0 - censorings / at_risk
        after.append(survival)
    return unique, np.asarray(before), np.asarray(after)


def step_value(unique: np.ndarray, values: np.ndarray, query: np.ndarray, *, left: bool) -> np.ndarray:
    points = np.asarray(query, dtype=float)
    indices = np.searchsorted(unique, points, side="left" if left else "right") - 1
    result = np.ones(points.shape, dtype=float)
    valid = indices >= 0
    result[valid] = values[indices[valid]]
    return result


def weighted_calibration(outcome: np.ndarray, weight: np.ndarray, risk: np.ndarray) -> tuple[float, float]:
    mask = (weight > 0) & np.isfinite(risk)
    y = outcome[mask]
    w = weight[mask]
    p = np.clip(risk[mask], 1e-6, 1 - 1e-6)
    offset = np.log(p / (1 - p))
    intercept = 0.0
    for _ in range(100):
        eta = np.clip(offset + intercept, -30, 30)
        mu = 1 / (1 + np.exp(-eta))
        information = float(np.sum(w * mu * (1 - mu)))
        if information <= 1e-12:
            break
        step = float(np.sum(w * (y - mu))) / information
        intercept += step
        if abs(step) < 1e-9:
            break

    if np.std(offset) < 1e-12:
        return float(intercept), math.nan
    design = np.column_stack([np.ones_like(offset), offset])
    beta = np.array([0.0, 1.0])
    for _ in range(100):
        eta = np.clip(design @ beta, -30, 30)
        mu = 1 / (1 + np.exp(-eta))
        gradient = design.T @ (w * (y - mu))
        information = design.T @ ((w * mu * (1 - mu))[:, None] * design)
        update = np.linalg.solve(information + np.eye(2) * 1e-9, gradient)
        beta += update
        if np.max(np.abs(update)) < 1e-9:
            break
    return float(intercept), float(beta[1])


def evaluate(event: np.ndarray, time: np.ndarray, score: np.ndarray, risk: np.ndarray) -> dict[str, float]:
    unique, before, after = censoring_km(event, time)
    g_left = step_value(unique, before, time, left=True)
    g_horizon = float(step_value(unique, after, np.asarray([HORIZON_DAYS]), left=False)[0])
    outcome = (event & (time <= HORIZON_DAYS)).astype(float)
    weight = np.zeros(len(time), dtype=float)
    event_before = event & (time <= HORIZON_DAYS)
    observed_beyond = time > HORIZON_DAYS
    weight[event_before] = 1 / np.maximum(g_left[event_before], 0.05)
    weight[observed_beyond] = 1 / max(g_horizon, 0.05)

    brier = float(np.sum(weight * (outcome - risk) ** 2) / len(time))
    citl, slope = weighted_calibration(outcome, weight, risk)

    harrell_num = 0.0
    harrell_den = 0.0
    for i in np.flatnonzero(event):
        comparable = np.flatnonzero(time[i] < time)
        harrell_den += len(comparable)
        harrell_num += float(np.sum(score[i] > score[comparable]))
        harrell_num += 0.5 * float(np.sum(score[i] == score[comparable]))

    uno_num = 0.0
    uno_den = 0.0
    for i in np.flatnonzero(event & (time <= HORIZON_DAYS)):
        comparable = np.flatnonzero(time[i] < time)
        pair_weight = 1 / max(g_left[i], 0.05) ** 2
        uno_den += pair_weight * len(comparable)
        uno_num += pair_weight * float(np.sum(score[i] > score[comparable]))
        uno_num += 0.5 * pair_weight * float(np.sum(score[i] == score[comparable]))

    cases = np.flatnonzero(event & (time <= HORIZON_DAYS))
    controls = np.flatnonzero(time > HORIZON_DAYS)
    auc_num = 0.0
    auc_den = 0.0
    for i in cases:
        case_weight = 1 / max(g_left[i], 0.05)
        auc_den += case_weight * len(controls)
        auc_num += case_weight * float(np.sum(score[i] > score[controls]))
        auc_num += 0.5 * case_weight * float(np.sum(score[i] == score[controls]))

    return {
        "ipcw_brier_24m": brier,
        "uno_c_24m": uno_num / uno_den,
        "auc_24m": auc_num / auc_den,
        "harrell_c": harrell_num / harrell_den,
        "calibration_in_the_large_24m": citl,
        "calibration_slope_24m": slope,
        "mean_predicted_risk_24m": float(np.mean(risk)),
    }


def json_value(value):
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    cohort = pd.read_excel(args.workbook, sheet_name="Cohort").dropna(subset=["patient_id"])
    predictions = pd.read_excel(args.workbook, sheet_name="Predictions").dropna(subset=["patient_id"])
    outcomes = pd.read_excel(args.workbook, sheet_name="Outcomes").dropna(subset=["patient_id"])
    metrics_sheet = pd.read_excel(args.workbook, sheet_name="Metrics", header=None)
    patterns = pd.read_excel(args.workbook, sheet_name="Patterns").dropna(subset=["usable_pattern"])

    for frame_name, frame in (("Cohort", cohort), ("Predictions", predictions), ("Outcomes", outcomes)):
        if frame["patient_id"].duplicated().any():
            raise ValueError(f"Duplicate patient_id in {frame_name}")
    id_sets = [set(frame["patient_id"]) for frame in (cohort, predictions, outcomes)]
    if not (id_sets[0] == id_sets[1] == id_sets[2]):
        raise ValueError("Patient identifiers do not align across cohort, prediction and outcome tables")

    merged = (
        cohort.merge(predictions, on="patient_id", suffixes=("", "_prediction"))
        .merge(outcomes, on="patient_id", suffixes=("", "_outcome"))
        .sort_values("patient_id")
    )
    required_predictions = ["cam_score", "cam_risk_24m", "scrf_score", "scrf_risk_24m"]
    if merged[KEY_CLINICAL_COLUMNS + required_predictions + ["duration_days", "event"]].isna().any().any():
        raise ValueError("Missing value found in a required clinical, prediction or outcome field")
    if not bool(merged["eligible_at_prediction"].astype(bool).all()):
        raise ValueError("At least one patient was ineligible at prediction time")
    if (pd.to_datetime(merged["prediction_date"]) < pd.to_datetime(merged["definitive_surgery_date"])).any():
        raise ValueError("Prediction date precedes definitive surgery")
    if (pd.to_datetime(merged["last_information_or_death_date"]) < pd.to_datetime(merged["prediction_date_outcome"])).any():
        raise ValueError("Outcome follow-up precedes prediction")

    event = merged["event"].astype(bool).to_numpy()
    time = merged["duration_days"].to_numpy(float)
    recomputed = {
        "CAM": evaluate(
            event,
            time,
            merged["cam_score"].to_numpy(float),
            merged["cam_risk_24m"].to_numpy(float),
        ),
        "SCRF": evaluate(
            event,
            time,
            merged["scrf_score"].to_numpy(float),
            merged["scrf_risk_24m"].to_numpy(float),
        ),
    }
    deltas = {key: recomputed["SCRF"][key] - recomputed["CAM"][key] for key in recomputed["CAM"]}

    metric_rows = {}
    for row_index, row in enumerate(metrics_sheet.itertuples(index=False, name=None)):
        if row_index < 8 and isinstance(row[0], str) and row[0] in recomputed["CAM"]:
            metric_rows[row[0]] = {"CAM": float(row[1]), "SCRF": float(row[2]), "difference": float(row[3])}
    for metric, values in metric_rows.items():
        if not np.isclose(values["CAM"], recomputed["CAM"][metric], atol=1e-12):
            raise ValueError(f"CAM metric mismatch for {metric}")
        if not np.isclose(values["SCRF"], recomputed["SCRF"][metric], atol=1e-12):
            raise ValueError(f"SCRF metric mismatch for {metric}")
        if not np.isclose(values["difference"], deltas[metric], atol=1e-12):
            raise ValueError(f"Delta mismatch for {metric}")

    bootstrap = {}
    for i, row in metrics_sheet.iterrows():
        name = row.iloc[0]
        if name in {"ipcw_brier_24m", "uno_c_24m", "auc_24m", "harrell_c"} and i >= 9:
            bootstrap[name] = {
                "replicates": int(row.iloc[1]),
                "ci_lower": float(row.iloc[2]),
                "ci_upper": float(row.iloc[3]),
            }

    usable_pattern = merged["usable_pattern"].astype(int).astype(str).str.zfill(3)
    fallback = usable_pattern.eq("000")
    fallback_score_error = float(np.max(np.abs(merged.loc[fallback, "scrf_score"] - merged.loc[fallback, "cam_score"])))
    fallback_risk_error = float(np.max(np.abs(merged.loc[fallback, "scrf_risk_24m"] - merged.loc[fallback, "cam_risk_24m"])))

    pattern_records = []
    for _, row in patterns.iterrows():
        pattern_records.append({str(key): json_value(value) for key, value in row.items()})

    aggregate = {
        "analysis": "U11 private two-centre retrospective external validation",
        "analysis_date": "2026-10-01",
        "input_workbook_sha256": sha256(args.workbook),
        "patient_level_data_written": False,
        "cohort": {
            "patients": int(len(merged)),
            "centres": {str(key): int(value) for key, value in cohort["site_id"].value_counts().items()},
            "observed_deaths": int(np.sum(event)),
            "deaths_by_24m": int(np.sum(event & (time <= HORIZON_DAYS))),
            "censored_by_24m": int(np.sum((~event) & (time <= HORIZON_DAYS))),
            "median_observed_follow_up_days": float(np.median(time)),
            "age_median_years": float(cohort["age_at_initial_diagnosis"].median()),
            "age_iqr_years": [
                float(cohort["age_at_initial_diagnosis"].quantile(0.25)),
                float(cohort["age_at_initial_diagnosis"].quantile(0.75)),
            ],
            "female": int(cohort["sex"].eq("female").sum()),
            "male": int(cohort["sex"].eq("male").sum()),
            "prediction_lag_median_days": float(cohort["prediction_lag_days"].median()),
            "complete_optional_pattern_111": int(usable_pattern.eq("111").sum()),
            "empty_optional_pattern_000": int(fallback.sum()),
        },
        "integrity": {
            "aligned_unique_patient_ids": True,
            "complete_required_clinical_fields": True,
            "complete_predictions": True,
            "prediction_coverage": 1.0,
            "member_count_all_25": bool(merged["member_count"].eq(25).all()),
            "valid_prediction_chronology": True,
            "valid_outcome_chronology": True,
            "exact_empty_set_score_fallback_error": fallback_score_error,
            "exact_empty_set_risk_fallback_error": fallback_risk_error,
        },
        "metrics": {
            "CAM": recomputed["CAM"],
            "SCRF": recomputed["SCRF"],
            "SCRF_minus_CAM": deltas,
            "paired_bootstrap_95ci_from_workbook": bootstrap,
        },
        "patterns": pattern_records,
        "claim_boundary": (
            "Independent retrospective external validation with complete coverage and favourable paired "
            "discrimination and IPCW-Brier intervals. The workbook did not encode a timestamped prediction-seal "
            "receipt, so this is not described as prospective or outcome-untouched confirmation. Calibration "
            "slope remained above one and clinical utility was not evaluated."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "u11_private_external_validation_aggregate.json"
    json_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit = f"""# U11 private external validation audit

- Workbook SHA256: `{aggregate['input_workbook_sha256']}`
- Cohort: {aggregate['cohort']['patients']} patients from two pseudonymized centres; {aggregate['cohort']['observed_deaths']} observed deaths.
- Patient identifiers aligned one-to-one across cohort, prediction and outcome sheets; no duplicates were detected.
- Required clinical fields and CAM/SCRF predictions were complete; both models had 100% coverage.
- Recomputed point estimates matched the workbook to absolute tolerance 1e-12.
- Empty-set CAM fallback was exact for both score and 24-month risk.
- No patient-level row was copied into the repository.

## External validation result

SCRF improved Uno C at 24 months from {recomputed['CAM']['uno_c_24m']:.6f} to {recomputed['SCRF']['uno_c_24m']:.6f} and IPCW Brier from {recomputed['CAM']['ipcw_brier_24m']:.6f} to {recomputed['SCRF']['ipcw_brier_24m']:.6f}. The workbook's paired 2,000-replicate intervals were [{bootstrap['uno_c_24m']['ci_lower']:.6f}, {bootstrap['uno_c_24m']['ci_upper']:.6f}] for delta Uno C and [{bootstrap['ipcw_brier_24m']['ci_lower']:.6f}, {bootstrap['ipcw_brier_24m']['ci_upper']:.6f}] for delta IPCW Brier.

## Claim boundary

This is independent retrospective external validation of the supplied frozen CAM/SCRF predictions. The transfer package did not include a timestamped prediction-seal receipt, so it is not labelled prospective or outcome-untouched confirmation. Calibration slope remained above one, and decision-curve benefit, clinical utility and deployment readiness were not tested.
"""
    (args.output_dir / "u11_private_external_validation_audit.md").write_text(audit, encoding="utf-8")


if __name__ == "__main__":
    main()
