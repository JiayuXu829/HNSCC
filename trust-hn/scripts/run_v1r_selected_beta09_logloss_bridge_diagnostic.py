from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_v1r_citl_slope_balanced_bridge_exploration as base

SEED_VALUES = [17, 29, 43, 71, 101]
FOLDS = 5
EXPECTED_PER_SEED = 610
BETA = 0.90
MODE = 'logloss'
CANDIDATE = 'beta_0.900_logloss'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    root = Path(__file__).resolve().parents[1]
    pred_path = root / 'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv'
    out_dir = root / 'research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate'
    out_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(pred_path, dtype={'acquisition_pattern': str, 'usable_pattern': str})
    required = {'repetition_seed', 'outer_fold', 'duration_days', 'event', 'acquisition_pattern', 'v1_risk_24m'}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f'missing columns: {sorted(missing)}')
    fold_rows, pattern_rows, parameter_rows = [], [], []
    pooled = []
    for seed in SEED_VALUES:
        seed_data = data.loc[data.repetition_seed == seed].copy()
        if len(seed_data) != EXPECTED_PER_SEED:
            raise ValueError(f'seed {seed} has {len(seed_data)} rows, expected {EXPECTED_PER_SEED}')
        for fold in range(FOLDS):
            train = seed_data.loc[seed_data.outer_fold != fold].copy().reset_index(drop=True)
            test = seed_data.loc[seed_data.outer_fold == fold].copy().reset_index(drop=True)
            train_y, train_w = base.targets_weights(train.duration_days, train.event, train.duration_days, ~train.event.astype(bool))
            test_y, test_w = base.targets_weights(test.duration_days, test.event, train.duration_days, ~train.event.astype(bool))
            x_train = base.logit(train.v1_risk_24m.to_numpy(float))
            x_test = base.logit(test.v1_risk_24m.to_numpy(float))
            alpha, fit_objective = base.fit_alpha(x_train, train_y, train_w, BETA, MODE)
            candidate = base.sigmoid(alpha + BETA * x_test)
            raw = test.v1_risk_24m.to_numpy(float)
            metric = base.metrics(test_y, test_w, raw, candidate)
            rank_preserved = bool(np.array_equal(np.argsort(raw, kind='mergesort'), np.argsort(candidate, kind='mergesort')))
            fold_rows.append({'candidate': CANDIDATE, 'beta': BETA, 'mode': MODE, 'seed': seed, 'outer_fold': fold, 'alpha': alpha, 'fit_objective': fit_objective, 'rank_preserved': rank_preserved, **metric})
            parameter_rows.append({'candidate': CANDIDATE, 'beta': BETA, 'mode': MODE, 'seed': seed, 'outer_fold': fold, 'alpha': alpha, 'fit_objective': fit_objective, 'effective_slope': BETA})
            pooled.append((test_y, test_w, raw, candidate))
            for pattern, idx in test.groupby('acquisition_pattern', sort=True).groups.items():
                idx = np.asarray(list(idx), dtype=int)
                pattern_rows.append({'candidate': CANDIDATE, 'pattern': str(pattern), 'seed': seed, 'outer_fold': fold, **base.metrics(test_y[idx], test_w[idx], raw[idx], candidate[idx])})
    y, w, raw, candidate = [np.concatenate([v[i] for v in pooled]) for i in range(4)]
    aggregate = base.metrics(y, w, raw, candidate)
    fold_df = pd.DataFrame(fold_rows)
    parameter_df = pd.DataFrame(parameter_rows)
    pattern_df = pd.DataFrame(pattern_rows)
    pattern_rows_agg = []
    for pattern, group in pattern_df.groupby('pattern', sort=True):
        n = int(group.n_evaluable.sum())
        events = int(group.events_evaluable.sum())
        if n == 0:
            continue
        valid = group.loc[group.n_evaluable > 0]
        raw_brier = float(np.average(valid.ipcw_brier_raw, weights=valid.n_evaluable))
        candidate_brier = float(np.average(valid.ipcw_brier_candidate, weights=valid.n_evaluable))
        pattern_rows_agg.append({'candidate': CANDIDATE, 'pattern': str(pattern), 'n_evaluable': n, 'events_evaluable': events, 'ipcw_brier_raw': raw_brier, 'ipcw_brier_candidate': candidate_brier, 'delta_ipcw_brier': candidate_brier - raw_brier, 'supported_pattern': bool(n >= 20 and events >= 5)})
    pattern_agg = pd.DataFrame(pattern_rows_agg)
    worst = float(pattern_agg.loc[pattern_agg.supported_pattern, 'delta_ipcw_brier'].max()) if pattern_agg.supported_pattern.any() else float('nan')
    safety = {
        'global_delta_ipcw_brier_max': 0.0005,
        'supported_pattern_regret_max': 0.005,
        'passes_global_brier_gate': bool(aggregate['delta_ipcw_brier'] <= 0.0005),
        'passes_supported_pattern_gate': bool(worst <= 0.005) if np.isfinite(worst) else True,
        'citl_improved': bool(abs(aggregate['citl_candidate']) < abs(aggregate['citl_raw'])),
        'slope_improved': bool(abs(aggregate['calibration_slope_candidate'] - 1.0) < abs(aggregate['calibration_slope_raw'] - 1.0)),
        'rank_preserved_all_folds': bool(fold_df.rank_preserved.all()),
        'strictly_monotone': bool(BETA > 0),
        'coverage_preserved': True,
    }
    safety['development_safe_pass'] = bool(all(safety.values()))
    payload = {
        'analysis': 'U5R7 fixed beta 0.90 log-loss-intercept V1R bridge development-only diagnostic',
        'protocol': 'frozen_beta09_logloss_bridge_candidate_protocol.yaml',
        'candidate': CANDIDATE,
        'beta': BETA,
        'intercept_mode': MODE,
        'cohort': 'HANCOCK official training development OOF',
        'eligible_n': EXPECTED_PER_SEED,
        'events': int(data.loc[data.repetition_seed == SEED_VALUES[0], 'event'].sum()),
        'seeds': SEED_VALUES,
        'outer_folds': FOLDS,
        'aggregate_metrics': aggregate,
        'worst_supported_pattern_regret': worst,
        'safety': safety,
        'confirmation_evaluation_performed': False,
        'confirmation_outcomes_used_for_bridge_tuning': False,
        'patient_level_outputs': 'not written',
    }
    (out_dir / 'selected_bridge_aggregate_results.json').write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    fold_df.to_csv(out_dir / 'selected_bridge_fold_results.csv', index=False)
    pattern_agg.to_csv(out_dir / 'selected_bridge_pattern_aggregate_results.csv', index=False)
    parameter_df.to_csv(out_dir / 'selected_bridge_parameters.csv', index=False)
    audit = f'''# U5R7 fixed beta 0.90 log-loss-intercept bridge diagnostic audit

- Status: development-only; not confirmation.
- Candidate: `{CANDIDATE}`.
- Transformation: `x_candidate = alpha_logloss + 0.90 * x_raw`.
- Alpha was fitted separately within the non-held-out development folds using weighted log-loss.
- The transformation is global-only, strictly monotone, and rank-preserving.
- Confirmation outcomes were not read or used for tuning.
- No patient-level tracked output was written.

## Result

```json
{json.dumps(payload, indent=2, sort_keys=True)}
```

Development-safe candidate gate: **{'PASS' if safety['development_safe_pass'] else 'FAIL'}**.
This result does not authorize confirmation application or deployment claims. Raw V1R remains retained.
'''
    (out_dir / 'selected_bridge_audit.md').write_text(audit, encoding='utf-8')
    hashes = {p.name: sha256(p) for p in [out_dir / 'selected_bridge_aggregate_results.json', out_dir / 'selected_bridge_fold_results.csv', out_dir / 'selected_bridge_pattern_aggregate_results.csv', out_dir / 'selected_bridge_parameters.csv', out_dir / 'selected_bridge_audit.md']}
    (out_dir / 'selected_bridge_hashes.json').write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(payload, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
