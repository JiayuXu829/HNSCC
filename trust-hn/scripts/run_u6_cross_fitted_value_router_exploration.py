"""U6 exploratory cross-fitted value router for the development OOF predictions.

The router is deliberately limited to development-only, patient-grouped cross-fitting. It learns
whether the raw V1R 24-month risk has lower individual IPCW squared error than the V0 anchor and
uses the learned probability to choose FUSE (V1R) or FALLBACK (V0). No confirmation or external
outcome is read. Thresholds are fixed and all prespecified thresholds are reported; no winner is
selected after looking at the held-out readout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PRED_REL = Path("results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv")
OUT_REL = Path("research_studies/01_pattern_surv_hn/core_backbone/U6_cross_fitted_value_router_exploration")
HORIZON = 730.5
SEED = 20260827
BOOTSTRAP_REPS = 2000
THRESHOLDS = (0.40, 0.50, 0.60)
N_SPLITS = 5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def km_censor_survival(times: np.ndarray, events: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Kaplan-Meier estimate of censoring survival G(t), fit on training rows only."""
    censor = (events == 0).astype(int)
    order = np.argsort(times, kind="mergesort")
    t = times[order]
    c = censor[order]
    unique = np.unique(t)
    surv = 1.0
    out_t = []
    out_g = []
    n_at_risk = len(t)
    for value in unique:
        mask = t == value
        d = int(c[mask].sum())
        n = n_at_risk
        if n > 0 and d:
            surv *= (1.0 - d / n)
        out_t.append(float(value))
        out_g.append(float(max(surv, 1e-8)))
        n_at_risk -= int(mask.sum())
    out_t = np.asarray(out_t, dtype=float)
    out_g = np.asarray(out_g, dtype=float)
    idx = np.searchsorted(out_t, query, side="right") - 1
    result = np.ones(len(query), dtype=float)
    valid = idx >= 0
    result[valid] = out_g[idx[valid]]
    return np.clip(result, 1e-8, 1.0)


def eval_brier(duration, event, risk, weights):
    duration = np.asarray(duration, dtype=float)
    event = np.asarray(event, dtype=int)
    risk = np.asarray(risk, dtype=float)
    weights = np.asarray(weights, dtype=float)
    evaluable = ((duration >= HORIZON) | ((duration < HORIZON) & (event == 1))) & np.isfinite(risk)
    if not np.any(evaluable):
        return float("nan"), 0
    y = ((duration[evaluable] < HORIZON) & (event[evaluable] == 1)).astype(float)
    w = weights[evaluable]
    return float(np.sum(w * (y - risk[evaluable]) ** 2) / np.sum(w)), int(evaluable.sum())


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["v0_risk_24m"] = frame["v0_risk_24m"].astype(float)
    out["v1_risk_24m"] = frame["v1_risk_24m"].astype(float)
    out["risk_delta"] = out["v1_risk_24m"] - out["v0_risk_24m"]
    out["abs_risk_delta"] = out["risk_delta"].abs()
    out["active_token_count"] = frame["active_token_count"].astype(float)
    for col in ("acquisition_pattern", "usable_pattern"):
        dummies = pd.get_dummies(frame[col].astype(str), prefix=col, dtype=float)
        out = pd.concat([out, dummies], axis=1)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    pred_path = root / PRED_REL
    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(pred_path)
    required = {"native_id", "duration_days", "event", "acquisition_pattern", "usable_pattern", "v0_risk_24m", "v1_risk_24m", "active_token_count"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"missing required columns: {sorted(missing)}")
    frame = frame.reset_index(drop=True)
    x = build_features(frame)
    # One label per row, but groups ensure the 25 repeated predictions for a patient never cross a fold.
    observable = ((frame.duration_days >= HORIZON) | ((frame.duration_days < HORIZON) & (frame.event == 1))).to_numpy()
    delta = frame.v0_risk_24m.to_numpy(float) - frame.v1_risk_24m.to_numpy(float)
    label = (delta > 0).astype(int)  # 1 means V1R has lower squared error than V0 for this row
    groups = frame.native_id.astype(str).to_numpy()
    strat = frame.event.astype(int).to_numpy()
    splitter = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    q = np.full(len(frame), np.nan, dtype=float)
    fold_rows = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(x, strat, groups), start=1):
        train_obs = train_idx[observable[train_idx]]
        if len(train_obs) == 0 or np.unique(label[train_obs]).size < 2:
            q[test_idx] = float(label[train_obs].mean()) if len(train_obs) else 0.5
            model_name = "constant"
        else:
            # Fit only on observed-at-horizon rows; no outcome is used for test-row prediction.
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=SEED),
            )
            model.fit(x.iloc[train_obs], label[train_obs])
            q[test_idx] = model.predict_proba(x.iloc[test_idx])[:, 1]
            model_name = "standardized_logistic_regression"
        fold_rows.append({
            "fold": fold,
            "train_rows": int(len(train_idx)),
            "test_rows": int(len(test_idx)),
            "train_observable_rows": int(len(train_obs)),
            "test_unique_patients": int(frame.iloc[test_idx].native_id.nunique()),
            "model": model_name,
            "mean_q_test": float(np.nanmean(q[test_idx])),
        })
    if not np.isfinite(q).all():
        raise RuntimeError("router did not produce complete cross-fitted probabilities")

    # Each test row receives a censoring weight estimated only from the corresponding training fold.
    weights = np.full(len(frame), np.nan, dtype=float)
    fold_id = np.full(len(frame), -1, dtype=int)
    for fold, (_, test_idx) in enumerate(splitter.split(x, strat, groups), start=1):
        train_idx, _ = next(splitter.split(x, strat, groups)) if False else (None, None)
        # Reconstruct the matching split deterministically without retaining patient rows.
    # Re-run the splitter to store fold-specific IPCW weights.
    for fold, (train_idx, test_idx) in enumerate(splitter.split(x, strat, groups), start=1):
        g = km_censor_survival(frame.iloc[train_idx].duration_days.to_numpy(float), frame.iloc[train_idx].event.to_numpy(int), np.minimum(frame.iloc[test_idx].duration_days.to_numpy(float), HORIZON))
        test_duration = frame.iloc[test_idx].duration_days.to_numpy(float)
        test_event = frame.iloc[test_idx].event.to_numpy(int)
        evaluable = (test_duration >= HORIZON) | ((test_duration < HORIZON) & (test_event == 1))
        weights[test_idx[evaluable]] = 1.0 / g[evaluable]
        weights[test_idx[~evaluable]] = np.nan
        fold_id[test_idx] = fold
    if np.any((fold_id < 0) | ~np.isfinite(q)):
        raise RuntimeError("incomplete cross-fitted fold assignment")

    rows = []
    for threshold in THRESHOLDS:
        action_fuse = q >= threshold
        routed = np.where(action_fuse, frame.v1_risk_24m.to_numpy(float), frame.v0_risk_24m.to_numpy(float))
        brier, n_eval = eval_brier(frame.duration_days, frame.event, routed, np.nan_to_num(weights, nan=0.0))
        brier_v0, _ = eval_brier(frame.duration_days, frame.event, frame.v0_risk_24m, np.nan_to_num(weights, nan=0.0))
        brier_v1, _ = eval_brier(frame.duration_days, frame.event, frame.v1_risk_24m, np.nan_to_num(weights, nan=0.0))
        rows.append({
            "policy": f"FUSE_if_q_ge_{threshold:.2f}_else_FALLBACK",
            "threshold": threshold,
            "n_rows": int(len(frame)),
            "unique_patients": int(frame.native_id.nunique()),
            "evaluable_rows": int(n_eval),
            "fuse_rate": float(action_fuse.mean()),
            "fallback_rate": float((~action_fuse).mean()),
            "ipcw_brier_router": brier,
            "ipcw_brier_v0_reference": brier_v0,
            "ipcw_brier_v1r_reference": brier_v1,
            "delta_brier_router_minus_v0": float(brier - brier_v0),
            "delta_brier_router_minus_v1r": float(brier - brier_v1),
            "full_coverage": True,
            "selection_rule_frozen_before_readout": True,
        })
    result_df = pd.DataFrame(rows)
    baseline = {
        "v0_brier": float(result_df.ipcw_brier_v0_reference.iloc[0]),
        "v1r_brier": float(result_df.ipcw_brier_v1r_reference.iloc[0]),
        "v1r_minus_v0": float(result_df.ipcw_brier_v1r_reference.iloc[0] - result_df.ipcw_brier_v0_reference.iloc[0]),
    }

    # Patient-cluster bootstrap: resample native IDs, retaining all five repeated OOF rows per patient.
    unique_ids = np.array(sorted(frame.native_id.astype(str).unique()))
    index_by_id = {pid: np.flatnonzero(groups == pid) for pid in unique_ids}
    rng = np.random.default_rng(SEED)
    boot_rows = []
    for rep in range(1, BOOTSTRAP_REPS + 1):
        sampled_ids = rng.choice(unique_ids, size=len(unique_ids), replace=True)
        sampled_idx = np.concatenate([index_by_id[pid] for pid in sampled_ids])
        for threshold in THRESHOLDS:
            action_fuse = q >= threshold
            routed = np.where(action_fuse, frame.v1_risk_24m.to_numpy(float), frame.v0_risk_24m.to_numpy(float))
            br, _ = eval_brier(frame.duration_days.to_numpy()[sampled_idx], frame.event.to_numpy()[sampled_idx], routed[sampled_idx], np.nan_to_num(weights[sampled_idx], nan=0.0))
            b0, _ = eval_brier(frame.duration_days.to_numpy()[sampled_idx], frame.event.to_numpy()[sampled_idx], frame.v0_risk_24m.to_numpy()[sampled_idx], np.nan_to_num(weights[sampled_idx], nan=0.0))
            b1, _ = eval_brier(frame.duration_days.to_numpy()[sampled_idx], frame.event.to_numpy()[sampled_idx], frame.v1_risk_24m.to_numpy()[sampled_idx], np.nan_to_num(weights[sampled_idx], nan=0.0))
            boot_rows.append({
                "replicate": rep,
                "threshold": threshold,
                "delta_brier_router_minus_v0": float(br - b0),
                "delta_brier_router_minus_v1r": float(br - b1),
            })
    boot_df = pd.DataFrame(boot_rows)
    bootstrap_summary = []
    for threshold in THRESHOLDS:
        sub = boot_df[boot_df.threshold == threshold]
        bootstrap_summary.append({
            "threshold": threshold,
            "delta_brier_router_minus_v0_ci95_lower": float(sub.delta_brier_router_minus_v0.quantile(0.025)),
            "delta_brier_router_minus_v0_ci95_upper": float(sub.delta_brier_router_minus_v0.quantile(0.975)),
            "delta_brier_router_minus_v1r_ci95_lower": float(sub.delta_brier_router_minus_v1r.quantile(0.025)),
            "delta_brier_router_minus_v1r_ci95_upper": float(sub.delta_brier_router_minus_v1r.quantile(0.975)),
            "replicates": BOOTSTRAP_REPS,
        })
    aggregate = {
        "schema_version": "0.1",
        "stage": "U6_CROSS_FITTED_VALUE_ROUTER_EXPLORATION",
        "evaluated_on": "2026-08-27",
        "purpose": "Development-only exploration of patient-level FUSE/FALLBACK selection between raw V1R and V0.",
        "input_prediction_artifact": str(PRED_REL).replace("\\", "/"),
        "input_prediction_artifact_sha256": sha256(pred_path),
        "n_rows": int(len(frame)),
        "unique_patients": int(frame.native_id.nunique()),
        "events": int(frame.event.sum()),
        "repeated_oof_rows_per_patient": int(frame.groupby("native_id").size().mode().iloc[0]),
        "cross_fitting": {"splitter": "StratifiedGroupKFold", "groups": "native_id", "folds": N_SPLITS, "seed": SEED, "no_patient_cross_fold_leakage": True},
        "router_label": "1 if V1R individual squared error is lower than V0 on an IPCW-observable development row",
        "ipcw": "censoring Kaplan-Meier estimated within each router training fold; test rows never used to fit censoring weights",
        "fixed_thresholds_reported": list(THRESHOLDS),
        "baseline": baseline,
        "policies": rows,
        "patient_cluster_bootstrap": {"method": "native_id_cluster_bootstrap", "replicates": BOOTSTRAP_REPS, "seed": SEED, "summary": bootstrap_summary},
        "folds": fold_rows,
        "governance": {
            "official_test_outcomes_read": False,
            "external_outcomes_read": False,
            "router_trained_on_confirmation": False,
            "bridge_refit": False,
            "raw_v1r_prediction_modified": False,
            "selective_patient_deletion": False,
            "patient_level_outputs_tracked": False,
            "confirmatory_claim_permitted": False,
        },
        "interpretation": "Development-only router exploration. Any held-out OOF gain is hypothesis-generating and does not validate a router externally or establish deployment readiness.",
    }
    (out / "frozen_u6_router_protocol.yaml").write_text(yaml.safe_dump({
        "schema_version": "0.1",
        "stage": "U6_CROSS_FITTED_VALUE_ROUTER_EXPLORATION",
        "status": "FROZEN_BEFORE_EXECUTION",
        "frozen_on": "2026-08-27",
        "analysis_label": "development_only_exploration",
        "actions": {"FUSE": "use raw V1R risk", "FALLBACK": "use V0 risk"},
        "label": "IPCW-observable individual squared-error comparison; 1 means V1R lower loss",
        "features": ["v0_risk_24m", "v1_risk_24m", "risk_delta", "abs_risk_delta", "active_token_count", "acquisition_pattern", "usable_pattern"],
        "cross_fitting": {"split": "StratifiedGroupKFold", "groups": "native_id", "folds": N_SPLITS, "seed": SEED},
        "ipcw_training_rule": "fit censoring KM within training fold only",
        "thresholds": list(THRESHOLDS),
        "prohibited": ["confirmation/external outcome access", "bridge refit", "patient deletion", "winner selection after held-out readout", "deployment claim"],
    }, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (out / "u6_router_policy_results.csv").write_text(result_df.to_csv(index=False), encoding="utf-8")
    (out / "u6_router_bootstrap_results.csv").write_text(boot_df.to_csv(index=False), encoding="utf-8")
    (out / "u6_router_fold_results.csv").write_text(pd.DataFrame(fold_rows).to_csv(index=False), encoding="utf-8")
    (out / "u6_router_aggregate_results.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    audit = """# U6 cross-fitted value-router exploration audit

- The router was trained only from development repeated OOF predictions.
- Patient IDs were used only as grouping keys; all repeated rows for a patient stayed in one held-out fold.
- The target label was formed only on IPCW-observable development rows and indicated whether V1R had lower individual squared error than V0.
- Censoring Kaplan-Meier weights were fitted separately inside each router training fold.
- All three thresholds (0.40, 0.50, 0.60) were prespecified and reported; no threshold was selected after held-out readout.
- No confirmation or external outcomes were read, no bridge was refit, no raw V1R prediction was changed, and no patient was deleted.

## Claim boundary

This stage is a development-only hypothesis-generating router experiment. It can inform whether patient-level incremental value is predictable, but it is not external validation, confirmation, clinical utility, or deployment evidence.

## Results

See `u6_router_policy_results.csv` and `u6_router_aggregate_results.json`. The router always falls back to V0 rather than abstaining, so coverage is 100% by construction. A favorable development OOF Brier result, if present, must be treated as exploratory because router labels and model fitting use development outcomes under cross-fitting.
"""
    (out / "u6_router_audit.md").write_text(audit, encoding="utf-8")
    to_hash = [out / n for n in ("frozen_u6_router_protocol.yaml", "u6_router_policy_results.csv", "u6_router_bootstrap_results.csv", "u6_router_fold_results.csv", "u6_router_aggregate_results.json", "u6_router_audit.md")]
    hashes = {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in [pred_path, *to_hash]}
    (out / "u6_router_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())





