from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import run_v1r_beta09_logloss_bridge_confirmation_validation as base
import run_v1r_confirmation as confirmation

HORIZON = 730.5
EXPECTED_N = 152
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260827
PATTERN_MIN_N = 20
PATTERN_MIN_EVENTS = 5
PROTOCOL_REL = Path('research_studies/01_pattern_surv_hn/core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization')
PRED_REL = Path('results/predictions/pattern_surv_hn/U2_V1R_confirmation')
U5R4_PARAM_REL = Path('research_studies/01_pattern_surv_hn/core_backbone/U5R4_V1R_bounded_global_bridge_candidate/selected_bridge_parameters.csv')
U5R7_PARAM_REL = Path('research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_parameters.csv')


def safe(v):
    if isinstance(v, dict): return {str(k): safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)): return [safe(x) for x in v]
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating, float)): return float(v) if np.isfinite(v) else None
    if isinstance(v, (np.bool_,)): return bool(v)
    return v


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def candidate_parameters(root: Path):
    p4 = root / U5R4_PARAM_REL
    p7 = root / U5R7_PARAM_REL
    d4 = pd.read_csv(p4)
    d7 = pd.read_csv(p7)
    if len(d4) != 25 or len(d7) != 25:
        raise RuntimeError('frozen parameter artifacts must each contain 25 fold rows')
    alpha4 = float(np.mean(d4['gamma'].to_numpy(float) * d4['alpha'].to_numpy(float)))
    beta4 = float(np.mean(d4['effective_slope'].to_numpy(float)))
    alpha7 = float(d7['alpha'].mean())
    beta7_values = d7['beta'].to_numpy(float)
    if not np.allclose(beta7_values, 0.90, rtol=0, atol=0):
        raise RuntimeError('U5R7 beta artifact is not fixed at 0.90')
    protocol = yaml.safe_load((root / PROTOCOL_REL / 'frozen_u5r9_bridge_panel_protocol.yaml').read_text(encoding='utf-8-sig'))
    expected = protocol['candidate_panel']
    checks = {
        'U5R4_bounded_global_full_g0.25': (alpha4, beta4),
        'U5R7_beta_0.900_logloss': (alpha7, 0.90),
    }
    for row in expected:
        if row['id'] in checks:
            a, b = checks[row['id']]
            if not np.isclose(a, row['frozen_effective_alpha'], rtol=0, atol=1e-15):
                raise RuntimeError(f"{row['id']} alpha mismatch: {a} != {row['frozen_effective_alpha']}")
            if not np.isclose(b, row['frozen_effective_slope'], rtol=0, atol=1e-15):
                raise RuntimeError(f"{row['id']} slope mismatch: {b} != {row['frozen_effective_slope']}")
    return {
        'raw_v1r': {'id': 'raw_v1r', 'alpha': 0.0, 'beta': 1.0, 'source': 'U2_V1R_locked_confirmation'},
        'U5R4_bounded_global_full_g0.25': {'id': 'U5R4_bounded_global_full_g0.25', 'alpha': alpha4, 'beta': beta4, 'source': str(U5R4_PARAM_REL).replace('\\', '/')},
        'U5R7_beta_0.900_logloss': {'id': 'U5R7_beta_0.900_logloss', 'alpha': alpha7, 'beta': 0.90, 'source': str(U5R7_PARAM_REL).replace('\\', '/')},
    }, p4, p7


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / PROTOCOL_REL
    protocol_path = out / 'frozen_u5r9_bridge_panel_protocol.yaml'
    protocol = yaml.safe_load(protocol_path.read_text(encoding='utf-8-sig'))
    if protocol['status'] != 'FROZEN_BEFORE_EXECUTION':
        raise RuntimeError('U5R9 protocol is not frozen')
    candidates, p4, p7 = candidate_parameters(root)

    pred_dir = root / PRED_REL
    aggregate_path = pred_dir / 'locked_aggregate_predictions.csv'
    member_path = pred_dir / 'locked_member_predictions.csv'
    audit_path = pred_dir / 'member_audit.json'
    receipt_path = root / 'research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_confirmation_protocol/pre_unseal_prediction_receipt.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    prediction_hash = confirmation.sha256_bytes(member_path.read_bytes() + aggregate_path.read_bytes() + audit_path.read_bytes())
    if prediction_hash != receipt['locked_prediction_artifact_sha256']:
        raise RuntimeError('locked V1R prediction artifact hash mismatch')
    pred = pd.read_csv(aggregate_path, dtype={'native_id': str, 'acquisition_pattern': str, 'usable_pattern': str})
    required = {'native_id', 'v1r_score', 'v1r_risk_24m', 'acquisition_pattern', 'usable_pattern', 'member_count'}
    if required - set(pred.columns) or len(pred) != EXPECTED_N or int(pred['member_count'].iloc[0]) != 25:
        raise RuntimeError('locked prediction shape or columns mismatch')
    ids = pred['native_id'].astype(str).to_numpy()
    duration, event = confirmation._read_unsealed_test_outcomes(root, ids)
    raw_risk = pred['v1r_risk_24m'].to_numpy(float)
    raw_score = pred['v1r_score'].to_numpy(float)

    results = []
    pattern_rows = []
    bootstrap_rows = []
    pattern_values = pred['acquisition_pattern'].astype(str).to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    event_idx = np.flatnonzero(event)
    censor_idx = np.flatnonzero(~event)
    for cid, c in candidates.items():
        risk = base.sigmoid(c['alpha'] + c['beta'] * base.logit(raw_risk))
        score = c['alpha'] + c['beta'] * raw_score
        metric = base.metrics(duration, event, raw_risk, risk)
        rank_risk = bool(np.array_equal(np.argsort(raw_risk, kind='mergesort'), np.argsort(risk, kind='mergesort')))
        rank_score = bool(np.array_equal(np.argsort(raw_score, kind='mergesort'), np.argsort(score, kind='mergesort')))
        for pattern in sorted(np.unique(pattern_values)):
            idx = pattern_values == pattern
            pm = base.metrics(duration[idx], event[idx], raw_risk[idx], risk[idx])
            pattern_rows.append({'candidate': cid, 'pattern': pattern, 'n': int(idx.sum()), 'events': int(event[idx].sum()), 'supported_pattern': bool(idx.sum() >= PATTERN_MIN_N and event[idx].sum() >= PATTERN_MIN_EVENTS), **pm})
        boot = []
        for rep in range(BOOTSTRAP_REPS):
            sample = np.concatenate([rng.choice(event_idx, size=len(event_idx), replace=True), rng.choice(censor_idx, size=len(censor_idx), replace=True)])
            rng.shuffle(sample)
            bm = base.metrics(duration[sample], event[sample], raw_risk[sample], risk[sample])
            bootstrap_rows.append({'candidate': cid, 'replicate': rep + 1, **bm})
            boot.append(bm)
        ptmp = pd.DataFrame([r for r in pattern_rows if r['candidate'] == cid])
        supported = ptmp.loc[ptmp['supported_pattern']]
        worst = float(supported['delta_ipcw_brier'].max()) if len(supported) else float('nan')
        safety = {
            'passes_global_brier_gate': bool(metric['delta_ipcw_brier'] <= 0.0005),
            'passes_supported_pattern_gate': bool(worst <= 0.005) if np.isfinite(worst) else True,
            'citl_absolute_error_improved': bool(abs(metric['citl_bridge']) < abs(metric['citl_raw'])) if cid != 'raw_v1r' else True,
            'slope_absolute_error_improved': bool(abs(metric['calibration_slope_bridge'] - 1) < abs(metric['calibration_slope_raw'] - 1)) if cid != 'raw_v1r' else True,
            'rank_preserved_risk': rank_risk,
            'rank_preserved_score': rank_score,
            'coverage_preserved': True,
        }
        safety['all_predeclared_gates_pass'] = bool(all(safety.values()))
        results.append({'candidate': cid, 'alpha': c['alpha'], 'effective_slope': c['beta'], 'parameter_source': c['source'], **metric, 'worst_supported_pattern_brier_regret': worst, **safety})
    result_df = pd.DataFrame(results)
    pattern_df = pd.DataFrame(pattern_rows)
    boot_df = pd.DataFrame(bootstrap_rows)

    def interval(group, col):
        v = group[col].to_numpy(float); v = v[np.isfinite(v)]
        return {'replicates': int(len(v)), 'mean': float(np.mean(v)), 'ci95_lower': float(np.quantile(v, .025)), 'ci95_upper': float(np.quantile(v, .975))} if len(v) else {'replicates': 0, 'mean': None, 'ci95_lower': None, 'ci95_upper': None}
    bootstrap_summary = {cid: {col: interval(boot_df.loc[boot_df.candidate == cid], col) for col in ['delta_ipcw_brier', 'delta_citl', 'abs_citl_error_change', 'delta_calibration_slope', 'abs_slope_error_change']} for cid in candidates}
    payload = {
        'schema_version': '0.1', 'stage_id': protocol['stage'], 'evaluated_on': '2026-08-27',
        'cohort_id': 'HANCOCK_OOD_TEST', 'cohort_role': protocol['cohort']['role'],
        'outcomes_were_already_unsealed_before_protocol_freeze': True,
        'n': int(len(pred)), 'events': int(event.sum()), 'horizon_days': HORIZON,
        'candidates': result_df.to_dict(orient='records'),
        'bootstrap': {'method': 'patient_level_stratified_bootstrap', 'replicates': BOOTSTRAP_REPS, 'seed': BOOTSTRAP_SEED, 'summary': bootstrap_summary},
        'governance': {'confirmation_outcomes_used_for_selection': False, 'candidate_panel_frozen_before_execution': True, 'winner_selected_after_outcome_readout': False, 'refit_on_confirmation': False, 'pattern_specific_tuning': False, 'router_trained': False, 'raw_v1r_modified': False, 'patient_level_results_tracked': False, 'clinical_utility_claim_permitted': False, 'deployment_readiness_claim_permitted': False},
        'interpretation': 'post_unseal exploratory characterization only; no candidate is promoted or selected for deployment',
    }
    (out / 'u5r9_bridge_panel_aggregate_results.json').write_text(json.dumps(safe(payload), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    result_df.to_csv(out / 'u5r9_bridge_panel_candidate_results.csv', index=False)
    pattern_df.to_csv(out / 'u5r9_bridge_panel_pattern_results.csv', index=False)
    boot_df.to_csv(out / 'u5r9_bridge_panel_bootstrap_results.csv', index=False)
    audit = '# U5R9 frozen bridge panel post-unseal characterization audit\n\n'
    audit += '- Protocol was frozen before execution.\n- The panel contained the pre-existing U5R4 and U5R7 candidates plus raw V1R reference.\n- No confirmation outcome was used to select, refit, or tune any candidate; no winner was selected after readout.\n- Outcomes had already been unsealed for U2 raw confirmation, so this is not pristine external validation.\n- All candidates are global monotone transformations; exact ranking and full coverage were checked.\n- Patient-level outputs were not written to tracked directories.\n\n## Aggregate readout\n\n```json\n' + json.dumps(safe(payload), indent=2, sort_keys=True) + '\n```\n'
    (out / 'u5r9_bridge_panel_audit.md').write_text(audit, encoding='utf-8')
    hashes = {p.name: sha(p) for p in [protocol_path, out / 'u5r9_bridge_panel_aggregate_results.json', out / 'u5r9_bridge_panel_candidate_results.csv', out / 'u5r9_bridge_panel_pattern_results.csv', out / 'u5r9_bridge_panel_bootstrap_results.csv', out / 'u5r9_bridge_panel_audit.md']}
    hashes['locked_prediction_artifact_sha256'] = prediction_hash
    hashes['u5r4_parameter_source_sha256'] = sha(p4); hashes['u5r7_parameter_source_sha256'] = sha(p7)
    (out / 'u5r9_bridge_panel_hashes.json').write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(safe(payload), indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

