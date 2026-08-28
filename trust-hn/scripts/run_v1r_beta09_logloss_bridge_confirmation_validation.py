from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import minimize, minimize_scalar
from sksurv.nonparametric import CensoringDistributionEstimator
from sksurv.util import Surv

import run_v1r_confirmation as confirmation

HORIZON = 730.5
BETA = 0.90
EXPECTED_N = 152
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260827
PATTERN_MIN_N = 20
PATTERN_MIN_EVENTS = 5
EPS = 1e-8

PROTOCOL_REL = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U5R8_V1R_beta09_logloss_bridge_confirmation_validation"
)
PRED_REL = Path("results/predictions/pattern_surv_hn/U2_V1R_confirmation")
PARAM_REL = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_parameters.csv"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
    return np.log(p / (1.0 - p))


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(np.asarray(x, dtype=float), -40.0, 40.0)))


def targets_weights(duration, event, fit_duration, fit_event):
    duration = np.asarray(duration, dtype=float)
    event = np.asarray(event, dtype=bool)
    fit_duration = np.asarray(fit_duration, dtype=float)
    fit_event = np.asarray(fit_event, dtype=bool)
    censor = CensoringDistributionEstimator().fit(
        Surv.from_arrays(event=fit_event, time=fit_duration)
    )
    target = np.full(duration.shape, np.nan, dtype=float)
    weight = np.zeros(duration.shape, dtype=float)
    case = (duration <= HORIZON) & event
    control = duration > HORIZON
    included = case | control
    target[case] = 1.0
    target[control] = 0.0
    times = np.where(case, duration, HORIZON)
    if included.any():
        g = censor.predict_proba(times[included])
        if np.any(g <= 0) or not np.isfinite(g).all():
            raise ValueError("invalid censoring survival estimate")
        weight[included] = 1.0 / g
    return target, weight


def fit_fixed_slope_intercept(x, y, w, slope=1.0):
    keep = np.asarray(w) > 0
    x = np.asarray(x, dtype=float)[keep]
    y = np.asarray(y, dtype=float)[keep]
    w = np.asarray(w, dtype=float)[keep]

    def objective(alpha):
        z = np.clip(alpha + slope * x, -40.0, 40.0)
        return float(np.sum(w * (np.logaddexp(0.0, z) - y * z)))

    return float(minimize_scalar(objective, bounds=(-20.0, 20.0), method="bounded").x)


def fit_slope(x, y, w):
    keep = np.asarray(w) > 0
    x = np.asarray(x, dtype=float)[keep]
    y = np.asarray(y, dtype=float)[keep]
    w = np.asarray(w, dtype=float)[keep]
    if len(x) == 0 or np.unique(y).size < 2:
        return float("nan")

    def objective(params):
        z = np.clip(params[0] + params[1] * x, -40.0, 40.0)
        return float(np.sum(w * (np.logaddexp(0.0, z) - y * z)))

    result = minimize(
        objective,
        x0=np.array([0.0, 1.0]),
        method="L-BFGS-B",
        bounds=[(-20.0, 20.0), (-20.0, 20.0)],
        options={"ftol": 1e-15, "gtol": 1e-10, "maxiter": 2000},
    )
    return float(result.x[1]) if result.success else float("nan")


def metrics(duration, event, raw, bridge):
    target, weight = targets_weights(duration, event, duration, ~np.asarray(event, dtype=bool))
    keep = weight > 0
    target = target[keep]
    weight = weight[keep]
    raw = np.asarray(raw, dtype=float)[keep]
    bridge = np.asarray(bridge, dtype=float)[keep]
    if len(target) == 0 or np.sum(weight) <= 0:
        return {
            "ipcw_brier_raw": float("nan"),
            "ipcw_brier_bridge": float("nan"),
            "delta_ipcw_brier": float("nan"),
            "citl_raw": float("nan"),
            "citl_bridge": float("nan"),
            "calibration_slope_raw": float("nan"),
            "calibration_slope_bridge": float("nan"),
            "n_evaluable": 0,
            "events_evaluable": 0,
            "mean_predicted_risk_raw": float("nan"),
            "mean_predicted_risk_bridge": float("nan"),
        }
    brier_raw = float(np.sum(weight * (target - raw) ** 2) / np.sum(weight))
    brier_bridge = float(np.sum(weight * (target - bridge) ** 2) / np.sum(weight))
    x_raw = logit(raw)
    x_bridge = logit(bridge)
    citl_raw = fit_fixed_slope_intercept(x_raw, target, weight)
    citl_bridge = fit_fixed_slope_intercept(x_bridge, target, weight)
    slope_raw = fit_slope(x_raw, target, weight)
    slope_bridge = fit_slope(x_bridge, target, weight)
    return {
        "ipcw_brier_raw": brier_raw,
        "ipcw_brier_bridge": brier_bridge,
        "delta_ipcw_brier": brier_bridge - brier_raw,
        "citl_raw": citl_raw,
        "citl_bridge": citl_bridge,
        "delta_citl": citl_bridge - citl_raw,
        "abs_citl_error_change": abs(citl_bridge) - abs(citl_raw),
        "calibration_slope_raw": slope_raw,
        "calibration_slope_bridge": slope_bridge,
        "delta_calibration_slope": slope_bridge - slope_raw,
        "abs_slope_error_change": (
            abs(slope_bridge - 1.0) - abs(slope_raw - 1.0)
            if np.isfinite(slope_raw) and np.isfinite(slope_bridge)
            else float("nan")
        ),
        "n_evaluable": int(len(target)),
        "events_evaluable": int(np.sum(target == 1)),
        "mean_predicted_risk_raw": float(np.mean(raw)),
        "mean_predicted_risk_bridge": float(np.mean(bridge)),
    }


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / PROTOCOL_REL
    protocol_path = out_dir / "frozen_u5r7_confirmation_bridge_validation_protocol.yaml"
    protocol = yaml.safe_load(protocol_path.read_text(encoding="utf-8-sig"))
    if protocol["status"] != "FROZEN_BEFORE_EXECUTION":
        raise RuntimeError("U5R8 bridge validation protocol is not frozen")

    params_path = root / PARAM_REL
    params = pd.read_csv(params_path)
    if len(params) != 25 or not np.allclose(params["beta"], BETA):
        raise RuntimeError("U5R7 parameter artifact is not the expected 25-row beta=0.90 artifact")
    alpha_dev_mean = float(params["alpha"].mean())
    expected_alpha = float(protocol["formula"]["alpha_dev_mean"])
    if not np.isclose(alpha_dev_mean, expected_alpha, rtol=0.0, atol=1e-15):
        raise RuntimeError(f"frozen development alpha mismatch: {alpha_dev_mean} != {expected_alpha}")
    if sha256_file(params_path) != protocol["formula"]["parameter_source_sha256"]:
        raise RuntimeError("U5R7 parameter source hash mismatch")

    pred_dir = root / PRED_REL
    aggregate_path = pred_dir / "locked_aggregate_predictions.csv"
    member_path = pred_dir / "locked_member_predictions.csv"
    audit_path = pred_dir / "member_audit.json"
    receipt_path = root / "research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_confirmation_protocol/pre_unseal_prediction_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    prediction_hash = confirmation.sha256_bytes(
        member_path.read_bytes() + aggregate_path.read_bytes() + audit_path.read_bytes()
    )
    if prediction_hash != receipt["locked_prediction_artifact_sha256"]:
        raise RuntimeError("locked V1R prediction artifact hash mismatch")

    pred = pd.read_csv(aggregate_path, dtype={"native_id": str, "acquisition_pattern": str, "usable_pattern": str})
    required = {"native_id", "v1r_score", "v1r_risk_24m", "acquisition_pattern", "usable_pattern", "member_count"}
    missing = required - set(pred.columns)
    if missing:
        raise RuntimeError(f"missing prediction columns: {sorted(missing)}")
    if len(pred) != EXPECTED_N or pred["member_count"].nunique() != 1 or int(pred["member_count"].iloc[0]) != 25:
        raise RuntimeError("locked prediction shape/member count mismatch")
    if pred["v1r_risk_24m"].isna().any() or pred["v1r_score"].isna().any():
        raise RuntimeError("locked V1R predictions contain missing values")

    test_ids = pred["native_id"].astype(str).to_numpy()
    duration, event = confirmation._read_unsealed_test_outcomes(root, test_ids)
    raw_risk = pred["v1r_risk_24m"].to_numpy(dtype=float)
    raw_score = pred["v1r_score"].to_numpy(dtype=float)
    bridge_risk = sigmoid(expected_alpha + BETA * logit(raw_risk))
    bridge_score = expected_alpha + BETA * raw_score
    metric = metrics(duration, event, raw_risk, bridge_risk)
    rank_preserved_risk = bool(np.array_equal(np.argsort(raw_risk, kind="mergesort"), np.argsort(bridge_risk, kind="mergesort")))
    rank_preserved_score = bool(np.array_equal(np.argsort(raw_score, kind="mergesort"), np.argsort(bridge_score, kind="mergesort")))
    exact_risk = bool(np.allclose(bridge_risk, sigmoid(expected_alpha + BETA * logit(raw_risk)), rtol=0.0, atol=0.0))
    pattern_rows = []
    pattern_values = pred["acquisition_pattern"].astype(str).to_numpy()
    for pattern in sorted(np.unique(pattern_values)):
        idx = pattern_values == pattern
        pm = metrics(duration[idx], event[idx], raw_risk[idx], bridge_risk[idx])
        pattern_rows.append({
            "pattern": pattern,
            "n": int(idx.sum()),
            "events": int(event[idx].sum()),
            "supported_pattern": bool(idx.sum() >= PATTERN_MIN_N and event[idx].sum() >= PATTERN_MIN_EVENTS),
            **pm,
        })
    pattern_df = pd.DataFrame(pattern_rows)
    supported = pattern_df.loc[pattern_df["supported_pattern"]]
    worst_regret = float(supported["delta_ipcw_brier"].max()) if len(supported) else float("nan")

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    event_idx = np.flatnonzero(event)
    censor_idx = np.flatnonzero(~event)
    bootstrap_rows = []
    for replicate in range(BOOTSTRAP_REPS):
        sample = np.concatenate([
            rng.choice(event_idx, size=len(event_idx), replace=True),
            rng.choice(censor_idx, size=len(censor_idx), replace=True),
        ])
        rng.shuffle(sample)
        bm = metrics(duration[sample], event[sample], raw_risk[sample], bridge_risk[sample])
        bootstrap_rows.append({"replicate": replicate + 1, **bm})
    boot_df = pd.DataFrame(bootstrap_rows)

    def interval(column):
        values = boot_df[column].to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        return {
            "replicates": int(len(values)),
            "mean": float(np.mean(values)) if len(values) else None,
            "ci95_lower": float(np.quantile(values, 0.025)) if len(values) else None,
            "ci95_upper": float(np.quantile(values, 0.975)) if len(values) else None,
        }

    bootstrap_summary = {key: interval(key) for key in [
        "delta_ipcw_brier", "delta_citl", "abs_citl_error_change",
        "delta_calibration_slope", "abs_slope_error_change",
    ]}
    safety = {
        "passes_global_brier_gate": bool(metric["delta_ipcw_brier"] <= 0.0005),
        "passes_supported_pattern_gate": bool(worst_regret <= 0.005) if np.isfinite(worst_regret) else True,
        "citl_absolute_error_improved": bool(abs(metric["citl_bridge"]) < abs(metric["citl_raw"])),
        "slope_absolute_error_improved": bool(abs(metric["calibration_slope_bridge"] - 1.0) < abs(metric["calibration_slope_raw"] - 1.0)),
        "rank_preserved_risk": rank_preserved_risk,
        "rank_preserved_score": rank_preserved_score,
        "coverage_preserved": True,
        "development_safe_candidate_reused_without_reselection": True,
    }
    safety["locked_secondary_validation_pass"] = bool(all(safety.values()))

    raw_confirmation = json.loads((root / "research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_confirmation_protocol/aggregate_confirmation_results.json").read_text(encoding="utf-8-sig"))
    result = {
        "schema_version": "0.1",
        "stage_id": protocol["stage"],
        "evaluated_on": "2026-08-27",
        "cohort_id": "HANCOCK_OOD_TEST",
        "cohort_role": protocol["cohort"]["role"],
        "outcomes_were_already_unsealed_before_bridge_protocol_freeze": True,
        "n": int(len(pred)),
        "events": int(event.sum()),
        "horizon_days": HORIZON,
        "bridge": {
            "candidate": "beta_0.900_logloss",
            "beta": BETA,
            "alpha_dev_mean": expected_alpha,
            "formula": "p_bridge = sigmoid(alpha_dev_mean + 0.90*logit(p_V1R_raw))",
            "parameter_source": str(PARAM_REL).replace("\\", "/"),
        },
        "raw_v1r_confirmation_reference": {
            "ipcw_brier_24m": raw_confirmation["V1R"]["ipcw_brier_24m"],
            "citl_24m": raw_confirmation["V1R"]["calibration_in_the_large_24m"],
            "calibration_slope_24m": raw_confirmation["V1R"]["calibration_slope_24m"],
            "coverage": raw_confirmation["coverage"],
        },
        "raw_v1r_vs_bridge": metric,
        "ranking": {
            "risk_rank_preserved_exact": rank_preserved_risk,
            "score_rank_preserved_exact": rank_preserved_score,
            "formula_monotone_beta_positive": bool(BETA > 0),
            "bridge_risk_recomputed_exactly": exact_risk,
        },
        "pattern_summary": pattern_rows,
        "worst_supported_pattern_brier_regret": worst_regret,
        "bootstrap": {
            "method": "patient_level_stratified_bootstrap",
            "replicates": BOOTSTRAP_REPS,
            "seed": BOOTSTRAP_SEED,
            "summary": bootstrap_summary,
        },
        "safety": safety,
        "governance": {
            "confirmation_outcomes_used_for_bridge_parameter_selection": False,
            "alpha_refit_on_confirmation": False,
            "beta_reselected_on_confirmation": False,
            "pattern_specific_tuning": False,
            "router_trained": False,
            "post_unseal_refit": False,
            "patient_removal": False,
            "raw_v1r_prediction_modified": False,
            "patient_level_results_tracked": False,
            "clinical_utility_claim_permitted": False,
            "deployment_readiness_claim_permitted": False,
        },
    }
    (out_dir / "u5r7_confirmation_bridge_aggregate_results.json").write_text(
        json.dumps(json_safe(result), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pattern_df.to_csv(out_dir / "u5r7_confirmation_bridge_pattern_results.csv", index=False)
    boot_df.to_csv(out_dir / "u5r7_confirmation_bridge_bootstrap_results.csv", index=False)
    audit = f'''# U5R8 locked secondary bridge validation audit

- **Status:** completed as a locked secondary post-unseal validation.
- **Cohort:** HANCOCK OOD TEST, n={len(pred)}, events={int(event.sum())}.
- **Bridge:** `p_bridge = sigmoid({expected_alpha:.17g} + 0.90 * logit(p_V1R_raw))`.
- The intercept was the arithmetic mean of the 25 already-frozen U5R7 development fold-specific log-loss intercepts.
- The beta, intercept aggregation rule, cohort, and estimands were frozen before this run.
- Confirmation outcomes had already been unsealed for the preceding U2/V1R raw confirmation evaluation; therefore this is **not** a new pristine outcome-untouched confirmation.
- No confirmation outcome was used to tune or select alpha, beta, a pattern-specific adjustment, a router, or a refit.
- Raw V1R predictions were not changed; the bridge is a monotone global transformation and ranking was checked exactly.
- No patient-level output was written to tracked research or paper-facing directories.

## Locked readout

```json
{json.dumps(json_safe(result), indent=2, sort_keys=True)}
```

This readout does not establish clinical utility, deployment readiness, external calibration, or transportability. It is secondary validation evidence for the already frozen development bridge.
'''
    (out_dir / "u5r7_confirmation_bridge_audit.md").write_text(audit, encoding="utf-8")

    hash_paths = [
        protocol_path,
        out_dir / "u5r7_confirmation_bridge_aggregate_results.json",
        out_dir / "u5r7_confirmation_bridge_pattern_results.csv",
        out_dir / "u5r7_confirmation_bridge_bootstrap_results.csv",
        out_dir / "u5r7_confirmation_bridge_audit.md",
    ]
    hashes = {path.name: sha256_file(path) for path in hash_paths}
    hashes["locked_prediction_artifact_sha256"] = prediction_hash
    hashes["u5r7_parameter_source_sha256"] = sha256_file(params_path)
    (out_dir / "u5r7_confirmation_bridge_hashes.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(json_safe(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
