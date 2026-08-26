from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sksurv.nonparametric import CensoringDistributionEstimator
from sksurv.util import Surv

HORIZON = 730.5
SEEDS = [17, 29, 43, 71, 101]
FOLDS = 5
EPS = 1e-8
EXPECTED_PER_SEED = 610
BETA_GRID = [0.80, 0.825, 0.85, 0.875, 0.90, 0.925, 0.95, 0.975, 1.0, 1.025]


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


def fit_brier_intercept(x, y, w, beta):
    keep = np.asarray(w) > 0
    x = np.asarray(x[keep], float)
    y = np.asarray(y[keep], float)
    w = np.asarray(w[keep], float)
    if len(x) == 0 or np.unique(y).size < 2:
        raise ValueError('fixed-slope bridge requires both outcome classes')

    def objective(alpha):
        p = sigmoid(alpha + beta * x)
        return float(np.sum(w * (y - p) ** 2) / np.sum(w))

    result = minimize_scalar(objective, bounds=(-20.0, 20.0), method='bounded', options={'xatol': 1e-13, 'maxiter': 2000})
    if not result.success or not np.isfinite(result.fun):
        raise RuntimeError(f'intercept optimization failed: {result.message}')
    return float(result.x), float(result.fun)


def fit_citl(x, y, w):
    keep = w > 0
    x, y, w = np.asarray(x[keep], float), np.asarray(y[keep], float), np.asarray(w[keep], float)
    lo, hi = -20.0, 20.0
    for _ in range(120):
        mid = (lo + hi) / 2.0
        score = float(np.sum(w * (y - sigmoid(mid + x))))
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
    from scipy.optimize import minimize
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
        return {
            'ipcw_brier_raw': np.nan, 'ipcw_brier_candidate': np.nan, 'delta_ipcw_brier': np.nan,
            'citl_raw': np.nan, 'citl_candidate': np.nan, 'abs_citl_error_deterioration': np.nan,
            'calibration_slope_raw': np.nan, 'calibration_slope_candidate': np.nan,
            'abs_slope_error_deterioration': np.nan, 'n_evaluable': 0, 'events_evaluable': 0,
        }
    brier_raw = float(np.sum(weight * (target - raw) ** 2) / np.sum(weight))
    brier_candidate = float(np.sum(weight * (target - candidate) ** 2) / np.sum(weight))
    x_raw, x_candidate = logit(raw), logit(candidate)
    citl_raw, citl_candidate = fit_citl(x_raw, target, weight), fit_citl(x_candidate, target, weight)
    slope_raw, slope_candidate = fit_slope(x_raw, target, weight), fit_slope(x_candidate, target, weight)
    return {
        'ipcw_brier_raw': brier_raw,
        'ipcw_brier_candidate': brier_candidate,
        'delta_ipcw_brier': brier_candidate - brier_raw,
        'citl_raw': citl_raw,
        'citl_candidate': citl_candidate,
        'abs_citl_error_deterioration': abs(citl_candidate) - abs(citl_raw),
        'calibration_slope_raw': slope_raw,
        'calibration_slope_candidate': slope_candidate,
        'abs_slope_error_deterioration': abs(slope_candidate - 1.0) - abs(slope_raw - 1.0) if np.isfinite(slope_raw) and np.isfinite(slope_candidate) else np.nan,
        'n_evaluable': int(len(target)),
        'events_evaluable': int(np.sum(target == 1)),
    }


def main():
    root = Path(__file__).resolve().parents[1]
    pred_path = root / 'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv'
    out_dir = root / 'research_studies/01_pattern_surv_hn/core_backbone/U5R5_V1R_fixed_slope_intercept_bridge_exploration'
    out_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(pred_path, dtype={'acquisition_pattern': str, 'usable_pattern': str})
    required = {'repetition_seed', 'outer_fold', 'duration_days', 'event', 'acquisition_pattern', 'v1_risk_24m'}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f'missing columns: {sorted(missing)}')
    candidates = [{'candidate': f'fixed_beta_{b:.3f}', 'beta': b} for b in BETA_GRID]
    fold_rows, pattern_rows, parameter_rows = [], [], []
    pooled = {c['candidate']: [] for c in candidates}
    for seed in SEEDS:
        seed_data = data.loc[data.repetition_seed == seed].copy()
        if len(seed_data) != EXPECTED_PER_SEED:
            raise ValueError(f'seed {seed} has {len(seed_data)} rows, expected {EXPECTED_PER_SEED}')
        for fold in range(FOLDS):
            train = seed_data.loc[seed_data.outer_fold != fold].copy().reset_index(drop=True)
            test = seed_data.loc[seed_data.outer_fold == fold].copy().reset_index(drop=True)
            train_y, train_w = horizon_targets_and_weights(train.duration_days, train.event, train.duration_days, ~train.event.astype(bool))
            test_y, test_w = horizon_targets_and_weights(test.duration_days, test.event, train.duration_days, ~train.event.astype(bool))
            x_train, x_test = logit(train.v1_risk_24m.to_numpy(float)), logit(test.v1_risk_24m.to_numpy(float))
            raw = test.v1_risk_24m.to_numpy(float)
            for spec in candidates:
                alpha, fit_loss = fit_brier_intercept(x_train, train_y, train_w, spec['beta'])
                x_candidate = alpha + spec['beta'] * x_test
                candidate = sigmoid(x_candidate)
                m = metrics(test_y, test_w, raw, candidate)
                rank_preserved = bool(np.array_equal(np.argsort(raw, kind='mergesort'), np.argsort(candidate, kind='mergesort')))
                fold_rows.append({'candidate': spec['candidate'], 'beta': spec['beta'], 'alpha': alpha, 'fit_ipcw_brier': fit_loss, 'seed': seed, 'outer_fold': fold, 'rank_preserved': rank_preserved, **m})
                pooled[spec['candidate']].append((test_y, test_w, raw, candidate))
                for pattern, idx in test.groupby('acquisition_pattern', sort=True).groups.items():
                    idx = np.asarray(list(idx), dtype=int)
                    pattern_rows.append({'candidate': spec['candidate'], 'beta': spec['beta'], 'seed': seed, 'outer_fold': fold, 'pattern': str(pattern), **metrics(test_y[idx], test_w[idx], raw[idx], candidate[idx])})
                parameter_rows.append({'candidate': spec['candidate'], 'beta': spec['beta'], 'alpha': alpha, 'seed': seed, 'outer_fold': fold, 'fit_ipcw_brier': fit_loss, 'effective_slope': spec['beta']})
    fold_df = pd.DataFrame(fold_rows)
    pattern_df = pd.DataFrame(pattern_rows)
    parameter_df = pd.DataFrame(parameter_rows)
    agg_rows = []
    for spec in candidates:
        ys, ws, raws, cals = zip(*pooled[spec['candidate']])
        agg_rows.append({'candidate': spec['candidate'], 'beta': spec['beta'], **metrics(np.concatenate(ys), np.concatenate(ws), np.concatenate(raws), np.concatenate(cals)), 'coverage': 1.0, 'rank_preservation_all_folds': bool(fold_df.loc[fold_df.candidate == spec['candidate'], 'rank_preserved'].all())})
    agg_df = pd.DataFrame(agg_rows)
    pattern_agg_rows = []
    for (candidate, pattern), group in pattern_df.groupby(['candidate', 'pattern'], sort=True):
        n = int(group.n_evaluable.sum()); e = int(group.events_evaluable.sum())
        if n == 0:
            continue
        valid = group.loc[group.n_evaluable > 0].copy()
        raw_b = float(np.average(valid.ipcw_brier_raw, weights=valid.n_evaluable)); cal_b = float(np.average(valid.ipcw_brier_candidate, weights=valid.n_evaluable))
        pattern_agg_rows.append({'candidate': candidate, 'pattern': pattern, 'n_evaluable': n, 'events_evaluable': e, 'ipcw_brier_raw': raw_b, 'ipcw_brier_candidate': cal_b, 'delta_ipcw_brier': cal_b - raw_b, 'supported_pattern': bool(n >= 20 and e >= 5)})
    pattern_agg_df = pd.DataFrame(pattern_agg_rows)
    safety_rows = []
    for _, row in agg_df.iterrows():
        pats = pattern_agg_df[(pattern_agg_df.candidate == row.candidate) & pattern_agg_df.supported_pattern]
        worst = float(pats.delta_ipcw_brier.max()) if len(pats) else np.nan
        safety_rows.append({'candidate': row.candidate, 'beta': row.beta, 'delta_ipcw_brier': row.delta_ipcw_brier, 'worst_supported_pattern_regret': worst, 'abs_citl_error_deterioration': row.abs_citl_error_deterioration, 'abs_slope_error_deterioration': row.abs_slope_error_deterioration, 'passes_brier_strict': bool(row.delta_ipcw_brier <= 0.0005), 'passes_pattern': bool(worst <= 0.005) if np.isfinite(worst) else True, 'citl_improved': bool(abs(row.citl_candidate) < abs(row.citl_raw)), 'slope_improved': bool(abs(row.calibration_slope_candidate - 1.0) < abs(row.calibration_slope_raw - 1.0)), 'rank_preserved': bool(row.rank_preservation_all_folds)})
    safety_df = pd.DataFrame(safety_rows)
    agg_df.to_csv(out_dir / 'fixed_slope_intercept_aggregate_results.csv', index=False)
    fold_df.to_csv(out_dir / 'fixed_slope_intercept_fold_results.csv', index=False)
    pattern_agg_df.to_csv(out_dir / 'fixed_slope_intercept_pattern_aggregate_results.csv', index=False)
    parameter_df.to_csv(out_dir / 'fixed_slope_intercept_parameters.csv', index=False)
    safety_df.to_csv(out_dir / 'fixed_slope_intercept_safety_screen.csv', index=False)
    summary = {'analysis': 'U5R5 rank-preserving fixed-slope global bridge exploration', 'protocol': 'frozen_fixed_slope_intercept_bridge_exploration_protocol.yaml', 'candidate_count': len(candidates), 'beta_grid': BETA_GRID, 'cohort': 'HANCOCK official training development OOF', 'confirmation_evaluation_performed': False, 'confirmation_outcomes_used_for_bridge_tuning': False, 'patient_level_outputs': 'not written', 'pareto_candidates': safety_df.loc[(safety_df.passes_brier_strict) & (safety_df.passes_pattern) & (safety_df.citl_improved) & (safety_df.slope_improved) & (safety_df.rank_preserved)].to_dict(orient='records')}
    (out_dir / 'fixed_slope_intercept_exploration_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
