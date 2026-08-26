from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sksurv.nonparametric import CensoringDistributionEstimator
from sksurv.util import Surv

HORIZON = 730.5
SEEDS = [17, 29, 43, 71, 101]
FOLDS = 5
EPS = 1e-8
BETA_MIN = 0.75
BETA_MAX = 1.25
GAMMA = 0.25
EXPECTED_PER_SEED = 610


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
    return np.log(p / (1.0 - p))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(np.asarray(x, dtype=float), -40.0, 40.0)))


def horizon_targets_and_weights(duration, event, fit_duration, fit_event):
    duration = np.asarray(duration, dtype=float)
    event = np.asarray(event, dtype=int).astype(bool)
    fit_duration = np.asarray(fit_duration, dtype=float)
    fit_event = np.asarray(fit_event, dtype=int).astype(bool)
    censor = CensoringDistributionEstimator().fit(Surv.from_arrays(event=fit_event, time=fit_duration))
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
            raise ValueError('non-positive or non-finite censoring survival estimate')
        weight[included] = 1.0 / g
    return target, weight


def fit_brier_base(x, y, w):
    """Fit alpha/beta using IPCW-Brier loss, with the frozen beta bound."""
    keep = np.asarray(w) > 0
    x = np.asarray(x[keep], dtype=float)
    y = np.asarray(y[keep], dtype=float)
    w = np.asarray(w[keep], dtype=float)
    if len(x) == 0 or np.unique(y).size < 2:
        raise ValueError('Brier bridge fit requires evaluable rows with both outcome classes')
    w = w / np.mean(w)

    def objective(params):
        alpha, beta = params
        p = sigmoid(alpha + beta * x)
        return float(np.sum(w * (y - p) ** 2) / np.sum(w))

    def gradient(params):
        alpha, beta = params
        z = np.clip(alpha + beta * x, -40.0, 40.0)
        p = sigmoid(z)
        common = 2.0 * w * (p - y) * p * (1.0 - p) / np.sum(w)
        return np.array([np.sum(common), np.sum(common * x)], dtype=float)

    # Wide, deterministic intercept bound prevents pathological separation while
    # preserving the frozen beta constraint.
    result = minimize(
        objective,
        x0=np.array([0.0, 1.0], dtype=float),
        jac=gradient,
        method='L-BFGS-B',
        bounds=[(-20.0, 20.0), (BETA_MIN, BETA_MAX)],
        options={'ftol': 1e-15, 'gtol': 1e-12, 'maxiter': 2000, 'maxls': 50},
    )
    if not result.success or not np.isfinite(result.fun):
        raise RuntimeError(f'Brier bridge optimization failed: {result.message}')
    alpha, beta = map(float, result.x)
    return {'alpha': alpha, 'beta': beta, 'fit_objective_ipcw_brier': float(result.fun), 'optimizer_success': bool(result.success), 'optimizer_message': str(result.message)}


def transform(x, base):
    alpha, beta = base['alpha'], base['beta']
    return np.asarray(x, dtype=float) + GAMMA * (alpha + beta * np.asarray(x, dtype=float) - np.asarray(x, dtype=float))


def fit_citl(x, y, w):
    keep = w > 0
    x, y, w = np.asarray(x[keep], float), np.asarray(y[keep], float), np.asarray(w[keep], float)
    # Solve a one-parameter intercept-only logistic recalibration with fixed slope 1.
    lo, hi = -20.0, 20.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        p = sigmoid(mid + x)
        score = float(np.sum(w * (y - p)))
        if score > 0:
            lo = mid
        else:
            hi = mid
    return float((lo + hi) / 2.0)


def fit_slope(x, y, w):
    keep = w > 0
    x, y, w = np.asarray(x[keep], float), np.asarray(y[keep], float), np.asarray(w[keep], float)
    if len(x) == 0 or np.unique(y).size < 2:
        return np.nan
    # Deterministic 2-parameter weighted logistic fit for diagnostic calibration slope.
    def objective(params):
        alpha, beta = params
        z = np.clip(alpha + beta * x, -40.0, 40.0)
        return float(np.sum(w * (np.logaddexp(0.0, z) - y * z)))
    result = minimize(objective, [0.0, 1.0], method='L-BFGS-B', bounds=[(-20.0, 20.0), (-20.0, 20.0)], options={'ftol': 1e-15, 'gtol': 1e-10, 'maxiter': 2000})
    return float(result.x[1]) if result.success else np.nan


def metrics(target, weight, raw, candidate):
    keep = np.asarray(weight) > 0
    target, weight = np.asarray(target)[keep], np.asarray(weight, float)[keep]
    raw, candidate = np.asarray(raw, float)[keep], np.asarray(candidate, float)[keep]
    if len(target) == 0 or np.sum(weight) <= 0:
        return {'ipcw_brier_raw': np.nan, 'ipcw_brier_candidate': np.nan, 'delta_ipcw_brier': np.nan, 'citl_raw': np.nan, 'citl_candidate': np.nan, 'abs_citl_error_deterioration': np.nan, 'calibration_slope_raw': np.nan, 'calibration_slope_candidate': np.nan, 'abs_slope_error_deterioration': np.nan, 'n_evaluable': 0, 'events_evaluable': 0}
    brier_raw = float(np.sum(weight * (target - raw) ** 2) / np.sum(weight))
    brier_candidate = float(np.sum(weight * (target - candidate) ** 2) / np.sum(weight))
    x_raw, x_candidate = logit(raw), logit(candidate)
    citl_raw = fit_citl(x_raw, target, weight)
    citl_candidate = fit_citl(x_candidate, target, weight)
    slope_raw = fit_slope(x_raw, target, weight)
    slope_candidate = fit_slope(x_candidate, target, weight)
    return {'ipcw_brier_raw': brier_raw, 'ipcw_brier_candidate': brier_candidate, 'delta_ipcw_brier': brier_candidate - brier_raw, 'citl_raw': citl_raw, 'citl_candidate': citl_candidate, 'abs_citl_error_deterioration': abs(citl_candidate) - abs(citl_raw), 'calibration_slope_raw': slope_raw, 'calibration_slope_candidate': slope_candidate, 'abs_slope_error_deterioration': abs(slope_candidate - 1.0) - abs(slope_raw - 1.0) if np.isfinite(slope_raw) and np.isfinite(slope_candidate) else np.nan, 'n_evaluable': int(len(target)), 'events_evaluable': int(np.sum(target == 1))}


def aggregate_pattern(pattern_df):
    rows = []
    for pattern, group in pattern_df.groupby('pattern', sort=True):
        n = int(group['n_evaluable'].sum())
        events = int(group['events_evaluable'].sum())
        if n == 0:
            continue
        raw = float(np.average(group['ipcw_brier_raw'], weights=group['n_evaluable']))
        candidate = float(np.average(group['ipcw_brier_candidate'], weights=group['n_evaluable']))
        rows.append({'pattern': str(pattern), 'n_evaluable': n, 'events_evaluable': events, 'ipcw_brier_raw': raw, 'ipcw_brier_candidate': candidate, 'delta_ipcw_brier': candidate - raw, 'supported_pattern': bool(n >= 20 and events >= 5)})
    return pd.DataFrame(rows)


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    pred_path = root / 'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv'
    out_dir = root / 'research_studies/01_pattern_surv_hn/core_backbone/U5R4_V1R_bounded_global_bridge_candidate'
    out_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(pred_path, dtype={'acquisition_pattern': str, 'usable_pattern': str})
    required = {'repetition_seed', 'outer_fold', 'duration_days', 'event', 'acquisition_pattern', 'v1_risk_24m'}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f'missing columns: {sorted(missing)}')
    parameter_rows, fold_rows, pattern_rows = [], [], []
    pooled = []
    for seed in SEEDS:
        seed_data = data.loc[data.repetition_seed == seed].copy()
        if len(seed_data) != EXPECTED_PER_SEED:
            raise ValueError(f'seed {seed} has {len(seed_data)} rows, expected {EXPECTED_PER_SEED}')
        for fold in range(FOLDS):
            train = seed_data.loc[seed_data.outer_fold != fold].copy().reset_index(drop=True)
            test = seed_data.loc[seed_data.outer_fold == fold].copy().reset_index(drop=True)
            train_target, train_weight = horizon_targets_and_weights(train.duration_days, train.event, train.duration_days, ~train.event.astype(bool))
            test_target, test_weight = horizon_targets_and_weights(test.duration_days, test.event, train.duration_days, ~train.event.astype(bool))
            x_train = logit(train.v1_risk_24m.to_numpy(float))
            x_test = logit(test.v1_risk_24m.to_numpy(float))
            base = fit_brier_base(x_train, train_target, train_weight)
            parameter_rows.append({'seed': seed, 'outer_fold': fold, **base, 'beta_min': BETA_MIN, 'beta_max': BETA_MAX, 'gamma': GAMMA, 'effective_slope': 1.0 + GAMMA * (base['beta'] - 1.0)})
            candidate = sigmoid(transform(x_test, base))
            raw = test.v1_risk_24m.to_numpy(float)
            m = metrics(test_target, test_weight, raw, candidate)
            rank_preserved = bool(np.array_equal(np.argsort(np.argsort(raw, kind='mergesort'), kind='mergesort'), np.argsort(np.argsort(candidate, kind='mergesort'), kind='mergesort')))
            fold_rows.append({'seed': seed, 'outer_fold': fold, 'candidate': 'bounded_global_full_g0.25', 'gamma': GAMMA, 'beta_effective': 1.0 + GAMMA * (base['beta'] - 1.0), 'rank_preserved': rank_preserved, **m})
            pooled.append((test_target, test_weight, raw, candidate))
            for pattern, idx in test.groupby('acquisition_pattern', sort=True).groups.items():
                idx = np.asarray(list(idx), dtype=int)
                pattern_rows.append({'seed': seed, 'outer_fold': fold, 'pattern': str(pattern), **metrics(test_target[idx], test_weight[idx], raw[idx], candidate[idx])})
    y = np.concatenate([v[0] for v in pooled]); w = np.concatenate([v[1] for v in pooled]); raw = np.concatenate([v[2] for v in pooled]); candidate = np.concatenate([v[3] for v in pooled])
    aggregate = metrics(y, w, raw, candidate)
    pattern_df = pd.DataFrame(pattern_rows)
    pattern_agg = aggregate_pattern(pattern_df)
    worst = float(pattern_agg.loc[pattern_agg.supported_pattern, 'delta_ipcw_brier'].max()) if pattern_agg.supported_pattern.any() else np.nan
    fold_df = pd.DataFrame(fold_rows)
    parameter_df = pd.DataFrame(parameter_rows)
    safety = {
        'coverage_preserved': True,
        'global_delta_ipcw_brier_max': 0.005,
        'supported_pattern_regret_max': 0.020,
        'mean_absolute_citl_error_deterioration_max': 0.10,
        'mean_absolute_slope_error_deterioration_max': 0.15,
        'passes_global_brier_gate': bool(aggregate['delta_ipcw_brier'] <= 0.005),
        'passes_supported_pattern_gate': bool(worst <= 0.020) if np.isfinite(worst) else True,
        'passes_citl_gate': bool(aggregate['abs_citl_error_deterioration'] <= 0.10),
        'passes_slope_gate': bool(np.isfinite(aggregate['abs_slope_error_deterioration']) and aggregate['abs_slope_error_deterioration'] <= 0.15),
        'improves_calibration': bool(abs(aggregate['citl_candidate']) < abs(aggregate['citl_raw']) or aggregate['abs_slope_error_deterioration'] < 0),
        'rank_preservation_all_folds': bool(fold_df['rank_preserved'].all()),
        'strictly_monotone_effective_slope': bool((parameter_df['effective_slope'] > 0).all()),
    }
    safety['development_safe_pass'] = bool(all([safety['coverage_preserved'], safety['passes_global_brier_gate'], safety['passes_supported_pattern_gate'], safety['passes_citl_gate'], safety['passes_slope_gate'], safety['improves_calibration'], safety['rank_preservation_all_folds'], safety['strictly_monotone_effective_slope']]))
    aggregate_payload = {'analysis': 'U5R4 fixed bounded global V1R bridge development-only diagnostic', 'protocol': 'frozen_bounded_global_bridge_candidate_protocol.yaml', 'candidate': 'bounded_global_full_g0.25', 'cohort': 'HANCOCK official training development OOF', 'eligible_n': EXPECTED_PER_SEED, 'events': int(data.loc[data.repetition_seed == SEEDS[0], 'event'].sum()), 'seeds': SEEDS, 'outer_folds': FOLDS, 'aggregate_metrics': aggregate, 'worst_supported_pattern_regret': worst, 'safety': safety, 'confirmation_evaluation_performed': False, 'confirmation_outcomes_used_for_bridge_tuning': False, 'patient_level_outputs': 'not written'}
    (out_dir / 'selected_bridge_aggregate_results.json').write_text(json.dumps(aggregate_payload, indent=2, sort_keys=True), encoding='utf-8')
    fold_df.to_csv(out_dir / 'selected_bridge_fold_results.csv', index=False)
    pattern_agg.to_csv(out_dir / 'selected_bridge_pattern_aggregate_results.csv', index=False)
    parameter_df.to_csv(out_dir / 'selected_bridge_parameters.csv', index=False)
    audit = ['# U5R4 fixed bounded global bridge diagnostic audit', '', '- Status: development-only diagnostic; not confirmation.', '- Candidate: `bounded_global_full_g0.25`.', '- Fit: IPCW-Brier objective on the other development folds only.', '- Constraint: beta in [0.75, 1.25]; gamma fixed at 0.25; global-only; no pattern-specific terms.', '- Confirmation outcomes were not read and no patient-level tracked output was written.', '', '## Results', '', '```json', json.dumps(aggregate_payload, indent=2, sort_keys=True), '```', '', '## Interpretation', '', f"Development-safe candidate gate: {'PASS' if safety['development_safe_pass'] else 'FAIL'}.", 'This result does not authorize confirmation application or deployment claims.', 'Raw V1R remains the retained backbone output.']
    (out_dir / 'selected_bridge_audit.md').write_text('\n'.join(audit) + '\n', encoding='utf-8')
    print(json.dumps(aggregate_payload, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
