"""U6R1 patient-level aggregation and reliability-aware router exploration.

Development-only follow-up to U6. Repeated OOF predictions are first aggregated to one
patient-level prediction and prediction-instability features are added as pre-outcome
reliability proxies. A patient-level cross-fitted logistic router selects raw V1R or V0.
No confirmation/external outcomes are read and no deployment claim is permitted.
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
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PRED_REL = Path("results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv")
OUT_REL = Path("research_studies/01_pattern_surv_hn/core_backbone/U6R1_patient_level_router_aggregation_exploration")
HORIZON = 730.5
SEED = 20260828
BOOTSTRAP_REPS = 2000
THRESHOLDS = (0.40, 0.50, 0.60)
N_SPLITS = 5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def km_censor_survival(times, events, query):
    censor = (np.asarray(events, int) == 0).astype(int)
    order = np.argsort(np.asarray(times, float), kind="mergesort")
    t = np.asarray(times, float)[order]
    c = censor[order]
    surv = 1.0
    out_t, out_g = [], []
    n_at_risk = len(t)
    for value in np.unique(t):
        mask = t == value
        d = int(c[mask].sum())
        if n_at_risk > 0 and d:
            surv *= (1.0 - d / n_at_risk)
        out_t.append(float(value))
        out_g.append(float(max(surv, 1e-8)))
        n_at_risk -= int(mask.sum())
    idx = np.searchsorted(np.asarray(out_t), np.asarray(query, float), side="right") - 1
    result = np.ones(len(query), dtype=float)
    valid = idx >= 0
    result[valid] = np.asarray(out_g)[idx[valid]]
    return np.clip(result, 1e-8, 1.0)


def eval_brier(duration, event, risk, weights):
    duration = np.asarray(duration, float)
    event = np.asarray(event, int)
    risk = np.asarray(risk, float)
    weights = np.asarray(weights, float)
    evaluable = ((duration >= HORIZON) | ((duration < HORIZON) & (event == 1))) & np.isfinite(risk)
    y = ((duration[evaluable] < HORIZON) & (event[evaluable] == 1)).astype(float)
    w = weights[evaluable]
    return float(np.sum(w * (y - risk[evaluable]) ** 2) / np.sum(w)), int(evaluable.sum())


def aggregate(frame):
    numeric = ["v0_risk_24m", "v1_risk_24m", "active_token_count", "duration_days", "event"]
    g = frame.groupby("native_id", sort=True)
    out = g[numeric].mean().reset_index()
    # Outcomes/patterns are invariant within patient; use first and assert invariance.
    for col in ("acquisition_pattern", "usable_pattern"):
        nunique = g[col].nunique()
        if int(nunique.max()) != 1:
            raise RuntimeError(f"{col} is not patient-invariant")
        out[col] = g[col].first().values
    for col in ("v0_risk_24m", "v1_risk_24m", "active_token_count"):
        out[col + "_sd"] = g[col].std(ddof=1).fillna(0.0).values
    out["risk_delta"] = out["v1_risk_24m"] - out["v0_risk_24m"]
    out["abs_risk_delta"] = out["risk_delta"].abs()
    out["risk_delta_sd"] = g.apply(lambda x: (x["v1_risk_24m"] - x["v0_risk_24m"]).std(ddof=1), include_groups=False).fillna(0.0).values
    return out.reset_index(drop=True)


def build_features(frame, reliability=True):
    out = pd.DataFrame(index=frame.index)
    for col in ["v0_risk_24m", "v1_risk_24m", "risk_delta", "abs_risk_delta", "active_token_count"]:
        out[col] = frame[col].astype(float)
    if reliability:
        for col in ["v0_risk_24m_sd", "v1_risk_24m_sd", "risk_delta_sd"]:
            out[col] = frame[col].astype(float)
    for col in ("acquisition_pattern", "usable_pattern"):
        out = pd.concat([out, pd.get_dummies(frame[col].astype(str), prefix=col, dtype=float)], axis=1)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def rank_concordance(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    da = a[:, None] - a[None, :]
    db = b[:, None] - b[None, :]
    mask = np.triu(np.ones_like(da, dtype=bool), 1) & (da != 0) & (db != 0)
    return float(np.mean(np.sign(da[mask]) == np.sign(db[mask]))) if mask.any() else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.root.resolve()
    pred_path = root / PRED_REL
    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(pred_path)
    required = {"native_id", "duration_days", "event", "acquisition_pattern", "usable_pattern", "v0_risk_24m", "v1_risk_24m", "active_token_count"}
    missing = required - set(raw.columns)
    if missing:
        raise RuntimeError(f"missing columns: {sorted(missing)}")
    frame = aggregate(raw)
    observable = ((frame.duration_days >= HORIZON) | ((frame.duration_days < HORIZON) & (frame.event == 1))).to_numpy()
    y = ((frame.duration_days < HORIZON) & (frame.event == 1)).astype(int).to_numpy()
    strata = frame.event.astype(int).to_numpy()
    split = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    router_specs = {
        "patient_aggregated_core": False,
        "patient_aggregated_plus_prediction_instability": True,
    }
    q_by_spec = {}
    weights = np.full(len(frame), np.nan)
    fold_id = np.full(len(frame), -1, int)
    fold_rows = []
    for spec, reliability in router_specs.items():
        x = build_features(frame, reliability=reliability)
        q = np.full(len(frame), np.nan)
        for fold, (train_idx, test_idx) in enumerate(split.split(x, strata), start=1):
            train_obs = train_idx[observable[train_idx]]
            if len(np.unique((frame.v1_risk_24m.iloc[train_obs].to_numpy() < 0).astype(int))) < 1:
                raise RuntimeError("unexpected training issue")
            d0 = (y[train_obs] - frame.v0_risk_24m.iloc[train_obs].to_numpy(float)) ** 2
            d1 = (y[train_obs] - frame.v1_risk_24m.iloc[train_obs].to_numpy(float)) ** 2
            label = (d1 < d0).astype(int)
            if len(np.unique(label)) < 2:
                raise RuntimeError("router training fold has one class")
            model = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000, class_weight="balanced", random_state=SEED))
            model.fit(x.iloc[train_obs], label)
            q[test_idx] = model.predict_proba(x.iloc[test_idx])[:, 1]
            if spec == "patient_aggregated_plus_prediction_instability":
                fold_rows.append({"spec": spec, "fold": fold, "train_patients": int(len(train_idx)), "train_observable_patients": int(len(train_obs)), "test_patients": int(len(test_idx)), "mean_q_test": float(q[test_idx].mean())})
        q_by_spec[spec] = q
    # One fold-specific censoring KM per patient; same weights used for all policies/specs.
    for fold, (train_idx, test_idx) in enumerate(split.split(frame, strata), start=1):
        g = km_censor_survival(frame.duration_days.iloc[train_idx], frame.event.iloc[train_idx], np.minimum(frame.duration_days.iloc[test_idx], HORIZON))
        test_d = frame.duration_days.iloc[test_idx].to_numpy(float); test_e = frame.event.iloc[test_idx].to_numpy(int)
        ev = (test_d >= HORIZON) | ((test_d < HORIZON) & (test_e == 1))
        weights[test_idx[ev]] = 1.0 / g[ev]
        fold_id[test_idx] = fold
    if np.any(~np.isfinite(weights[observable])) or np.any(fold_id < 0):
        raise RuntimeError("incomplete weights")

    b0, n_eval = eval_brier(frame.duration_days, frame.event, frame.v0_risk_24m, np.nan_to_num(weights, nan=0.0))
    b1, _ = eval_brier(frame.duration_days, frame.event, frame.v1_risk_24m, np.nan_to_num(weights, nan=0.0))
    rows = [{"spec": "V0_reference", "threshold": np.nan, "fuse_rate": 0.0, "fallback_rate": 1.0, "ipcw_brier": b0, "delta_vs_v0": 0.0, "delta_vs_v1r": b0-b1, "coverage": 1.0, "ranking_vs_v1r": rank_concordance(frame.v0_risk_24m, frame.v1_risk_24m)} , {"spec": "raw_V1R_reference", "threshold": np.nan, "fuse_rate": 1.0, "fallback_rate": 0.0, "ipcw_brier": b1, "delta_vs_v0": b1-b0, "delta_vs_v1r": 0.0, "coverage": 1.0, "ranking_vs_v1r": 1.0}]
    for spec, q in q_by_spec.items():
        for threshold in THRESHOLDS:
            fuse = q >= threshold
            risk = np.where(fuse, frame.v1_risk_24m, frame.v0_risk_24m)
            br, ne = eval_brier(frame.duration_days, frame.event, risk, np.nan_to_num(weights, nan=0.0))
            rows.append({"spec": spec, "threshold": threshold, "fuse_rate": float(fuse.mean()), "fallback_rate": float((~fuse).mean()), "ipcw_brier": br, "delta_vs_v0": br-b0, "delta_vs_v1r": br-b1, "coverage": 1.0, "ranking_vs_v1r": rank_concordance(risk, frame.v1_risk_24m)})
    results = pd.DataFrame(rows)

    # Patient-cluster bootstrap for each policy; fixed cross-fitted q and fixed fold-specific IPCW weights.
    rng = np.random.default_rng(SEED)
    idx = np.arange(len(frame))
    boot_rows = []
    policies = [("V0_reference", None, None), ("raw_V1R_reference", None, None)] + [(s,t,q_by_spec[s]) for s in q_by_spec for t in THRESHOLDS]
    for rep in range(1, BOOTSTRAP_REPS+1):
        sampled = rng.choice(idx, size=len(idx), replace=True)
        for spec, threshold, q in policies:
            if spec == "V0_reference": risk = frame.v0_risk_24m.to_numpy(float)
            elif spec == "raw_V1R_reference": risk = frame.v1_risk_24m.to_numpy(float)
            else: risk = np.where(q >= threshold, frame.v1_risk_24m, frame.v0_risk_24m)
            br,_ = eval_brier(frame.duration_days.to_numpy()[sampled], frame.event.to_numpy()[sampled], risk[sampled], np.nan_to_num(weights[sampled], nan=0.0))
            b0s,_ = eval_brier(frame.duration_days.to_numpy()[sampled], frame.event.to_numpy()[sampled], frame.v0_risk_24m.to_numpy()[sampled], np.nan_to_num(weights[sampled], nan=0.0))
            b1s,_ = eval_brier(frame.duration_days.to_numpy()[sampled], frame.event.to_numpy()[sampled], frame.v1_risk_24m.to_numpy()[sampled], np.nan_to_num(weights[sampled], nan=0.0))
            boot_rows.append({"replicate": rep, "spec": spec, "threshold": threshold, "delta_vs_v0": br-b0s, "delta_vs_v1r": br-b1s})
    boot = pd.DataFrame(boot_rows)
    summary=[]
    for spec, threshold, _ in policies:
        sub=boot[(boot.spec==spec) & (boot.threshold.isna() if pd.isna(threshold) else (boot.threshold==threshold))]
        summary.append({"spec": spec, "threshold": threshold, "delta_vs_v0_ci95_lower": float(sub.delta_vs_v0.quantile(.025)), "delta_vs_v0_ci95_upper": float(sub.delta_vs_v0.quantile(.975)), "delta_vs_v1r_ci95_lower": float(sub.delta_vs_v1r.quantile(.025)), "delta_vs_v1r_ci95_upper": float(sub.delta_vs_v1r.quantile(.975))})

    aggregate_result = {"stage":"U6R1_PATIENT_LEVEL_ROUTER_AGGREGATION_EXPLORATION", "evaluated_on":"2026-08-28", "n_rows_raw":int(len(raw)), "unique_patients":int(len(frame)), "repetitions_per_patient":int(raw.groupby('native_id').size().mode().iloc[0]), "ipcw_evaluable_patients":int(n_eval), "baseline":{"v0_brier":b0,"v1r_brier":b1,"v1r_minus_v0":b1-b0}, "policies":rows, "bootstrap":{"replicates":BOOTSTRAP_REPS,"seed":SEED,"summary":summary}, "ranking_note":"Router selection is not guaranteed to preserve global V1R ranking; ranking concordance is reported descriptively.", "governance":{"official_test_outcomes_read":False,"external_outcomes_read":False,"confirmation_outcomes_read":False,"patient_level_predictions_tracked":False,"confirmatory_claim_permitted":False}, "interpretation":"Development-only exploratory follow-up. Patient-level aggregation and instability proxies were evaluated to reduce repeated-OOF noise; no external or confirmatory inference is permitted."}
    protocol={"schema_version":"0.1","stage":"U6R1_PATIENT_LEVEL_ROUTER_AGGREGATION_EXPLORATION","status":"FROZEN_BEFORE_EXECUTION","frozen_on":"2026-08-28","analysis_label":"development_only_exploration","unit":"one aggregated patient per native_id","features":{"core":["v0_risk_24m","v1_risk_24m","risk_delta","abs_risk_delta","active_token_count","acquisition_pattern","usable_pattern"],"reliability_augmented":["v0_risk_24m_sd","v1_risk_24m_sd","risk_delta_sd"]},"router":"patient-level cross-fitted balanced logistic regression, C=0.5","folds":N_SPLITS,"seed":SEED,"thresholds":list(THRESHOLDS),"actions":{"FUSE":"use patient-aggregated raw V1R risk","FALLBACK":"use patient-aggregated V0 risk"},"prohibited":["official-test/confirmation/external outcome access","bridge refit","patient deletion","post-readout winner selection","deployment claim"]}
    (out/'frozen_u6r1_router_protocol.yaml').write_text(yaml.safe_dump(protocol,sort_keys=False,allow_unicode=True),encoding='utf-8')
    (out/'u6r1_policy_results.csv').write_text(results.to_csv(index=False),encoding='utf-8')
    (out/'u6r1_bootstrap_results.csv').write_text(boot.to_csv(index=False),encoding='utf-8')
    (out/'u6r1_fold_results.csv').write_text(pd.DataFrame(fold_rows).to_csv(index=False),encoding='utf-8')
    (out/'u6r1_aggregate_results.json').write_text(json.dumps(aggregate_result,indent=2,ensure_ascii=False,sort_keys=True,default=str)+'\n',encoding='utf-8')
    audit='''# U6R1 patient-level aggregation router exploration audit\n\n- Repeated development OOF predictions were aggregated to one row per patient before router fitting and policy evaluation.\n- Prediction-instability features were computed from the repeated OOF predictions and used only as pre-outcome reliability proxies.\n- Router fitting was patient-level, five-fold cross-fitted, and development-only.\n- All thresholds 0.40, 0.50 and 0.60 were reported; no confirmation or external outcomes were read.\n- Selection policies always used either raw V1R or V0, retaining 100% coverage.\n\n## Claim boundary\n\nThis is an exploratory development experiment. It may inform a future locked router protocol, but it is not router confirmation, external validation, clinical utility, or deployment evidence.\n'''
    (out/'u6r1_audit.md').write_text(audit,encoding='utf-8')
    to_hash=[out/n for n in ('frozen_u6r1_router_protocol.yaml','u6r1_policy_results.csv','u6r1_bootstrap_results.csv','u6r1_fold_results.csv','u6r1_aggregate_results.json','u6r1_audit.md')]
    hashes={str(p.relative_to(root)).replace('\\','/'):sha256(p) for p in [pred_path,*to_hash]}
    (out/'u6r1_hashes.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(aggregate_result,indent=2,ensure_ascii=False,sort_keys=True,default=str))

if __name__=='__main__':
    main()
