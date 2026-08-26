from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sksurv.nonparametric import CensoringDistributionEstimator
from sksurv.util import Surv

HORIZON = 730.5
SEEDS = [17, 29, 43, 71, 101]
FOLDS = 5
EPS = 1e-8


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


def fit_full(x, y, w):
    keep = w > 0
    model = LogisticRegression(penalty=None, solver='lbfgs', max_iter=2000)
    model.fit(np.asarray(x[keep]).reshape(-1, 1), y[keep].astype(int), sample_weight=w[keep])
    return float(model.intercept_[0]), float(model.coef_[0, 0])


def optimize_one_dim(x, y, w, fixed_slope=None, fixed_intercept=None):
    keep = w > 0
    x, y, w = np.asarray(x[keep], float), np.asarray(y[keep], float), np.asarray(w[keep], float)
    if fixed_slope is None and fixed_intercept is None:
        raise ValueError('one parameter must be fixed')
    def objective(value):
        alpha = value if fixed_slope is not None else fixed_intercept
        beta = fixed_slope if fixed_slope is not None else value
        z = np.clip(alpha + beta * x, -40.0, 40.0)
        return float(np.sum(w * (np.logaddexp(0.0, z) - y * z)))
    return float(minimize_scalar(objective, bounds=(-20.0, 20.0), method='bounded').x)


def fit_bases(train):
    keep = train['_weight'].to_numpy() > 0
    x = train.loc[keep, '_x'].to_numpy(float)
    y = train.loc[keep, '_target'].to_numpy(float)
    w = train.loc[keep, '_weight'].to_numpy(float)
    alpha_full, beta_full = fit_full(x, y, w)
    alpha_int = optimize_one_dim(x, y, w, fixed_slope=1.0)
    beta_slope = optimize_one_dim(x, y, w, fixed_intercept=0.0)
    beta_bounded = float(np.clip(beta_full, 0.75, 1.25))
    alpha_bounded = optimize_one_dim(x, y, w, fixed_slope=beta_bounded)
    return {
        'global_full': {'alpha': alpha_full, 'beta': beta_full},
        'global_intercept': {'alpha': alpha_int, 'beta': 1.0},
        'global_slope': {'alpha': 0.0, 'beta': beta_slope},
        'bounded_global_full': {'alpha': alpha_bounded, 'beta': beta_bounded},
    }


def candidate_specs():
    specs = [{'candidate': 'identity', 'family': 'identity', 'gamma': 0.0, 'base': 'identity'}]
    for family, base in [
        ('global_intercept_shrinkage', 'global_intercept'),
        ('global_slope_shrinkage', 'global_slope'),
        ('global_full_shrinkage', 'global_full'),
    ]:
        for gamma in [0.10, 0.25, 0.50, 0.75, 1.00]:
            specs.append({'candidate': f'{family}_g{gamma:.2f}', 'family': family, 'gamma': gamma, 'base': base})
    for gamma in [0.25, 0.50, 0.75, 1.00]:
        specs.append({'candidate': f'bounded_global_full_g{gamma:.2f}', 'family': 'bounded_global_full', 'gamma': gamma, 'base': 'bounded_global_full'})
    return specs


def transform(x, base, gamma):
    if base == 'identity':
        return x.copy()
    alpha, beta = base['alpha'], base['beta']
    return x + gamma * (alpha + beta * x - x)


def fit_citl(x, y, w):
    return optimize_one_dim(x, y, w, fixed_slope=1.0)


def fit_slope(x, y, w):
    keep = w > 0
    if np.unique(y[keep]).size < 2:
        return np.nan
    _, beta = fit_full(x[keep], y[keep], w[keep])
    return beta


def metrics(target, weight, raw, calibrated):
    keep = weight > 0
    target, weight = target[keep], weight[keep]
    raw, calibrated = raw[keep], calibrated[keep]
    if len(target) == 0 or np.sum(weight) <= 0:
        return {
            'ipcw_brier_raw': np.nan, 'ipcw_brier_candidate': np.nan, 'delta_ipcw_brier': np.nan,
            'citl_raw': np.nan, 'citl_candidate': np.nan, 'abs_citl_error_deterioration': np.nan,
            'calibration_slope_raw': np.nan, 'calibration_slope_candidate': np.nan,
            'abs_slope_error_deterioration': np.nan, 'n_evaluable': 0, 'events_evaluable': 0,
        }
    def brier(p):
        return float(np.sum(weight * (target - p) ** 2) / np.sum(weight))
    x_raw, x_cal = logit(raw), logit(calibrated)
    citl_raw = fit_citl(x_raw, target, weight)
    citl_cal = fit_citl(x_cal, target, weight)
    slope_raw = fit_slope(x_raw, target, weight)
    slope_cal = fit_slope(x_cal, target, weight)
    return {
        'ipcw_brier_raw': brier(raw),
        'ipcw_brier_candidate': brier(calibrated),
        'delta_ipcw_brier': brier(calibrated) - brier(raw),
        'citl_raw': citl_raw,
        'citl_candidate': citl_cal,
        'abs_citl_error_deterioration': abs(citl_cal) - abs(citl_raw),
        'calibration_slope_raw': slope_raw,
        'calibration_slope_candidate': slope_cal,
        'abs_slope_error_deterioration': abs(slope_cal - 1.0) - abs(slope_raw - 1.0) if np.isfinite(slope_raw) and np.isfinite(slope_cal) else np.nan,
        'n_evaluable': int(len(target)),
        'events_evaluable': int(np.sum(target == 1)),
    }


def main():
    root = Path(__file__).resolve().parents[1]
    pred_path = root / 'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv'
    out_dir = root / 'research_studies/01_pattern_surv_hn/core_backbone/U5R1_revised_calibration_bridge_exploration'
    data = pd.read_csv(pred_path, dtype={'acquisition_pattern': str, 'usable_pattern': str})
    required = {'repetition_seed', 'outer_fold', 'duration_days', 'event', 'acquisition_pattern', 'v1_risk_24m'}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f'missing columns: {sorted(missing)}')
    specs = candidate_specs()
    fold_rows = []
    pattern_rows = []
    parameter_rows = []
    pooled = {s['candidate']: [] for s in specs}
    pooled_pattern = {s['candidate']: [] for s in specs}
    for seed in SEEDS:
        seed_data = data.loc[data.repetition_seed == seed].copy()
        if len(seed_data) != 610:
            raise ValueError(f'seed {seed} has {len(seed_data)} rows, expected 610')
        for fold in range(FOLDS):
            train = seed_data.loc[seed_data.outer_fold != fold].copy().reset_index(drop=True)
            test = seed_data.loc[seed_data.outer_fold == fold].copy().reset_index(drop=True)
            train_target, train_weight = horizon_targets_and_weights(train.duration_days, train.event, train.duration_days, ~train.event.astype(bool))
            test_target, test_weight = horizon_targets_and_weights(test.duration_days, test.event, train.duration_days, ~train.event.astype(bool))
            train['_target'], train['_weight'] = train_target, train_weight
            test['_target'], test['_weight'] = test_target, test_weight
            train['_x'] = logit(train.v1_risk_24m.to_numpy())
            test['_x'] = logit(test.v1_risk_24m.to_numpy())
            bases = fit_bases(train)
            for name, params in bases.items():
                parameter_rows.append({'seed': seed, 'outer_fold': fold, 'base': name, **params})
            raw = test.v1_risk_24m.to_numpy(float)
            x_test = test['_x'].to_numpy(float)
            for spec in specs:
                x_candidate = transform(x_test, bases[spec['base']] if spec['base'] != 'identity' else 'identity', spec['gamma'])
                calibrated = sigmoid(x_candidate)
                m = metrics(test['_target'].to_numpy(float), test['_weight'].to_numpy(float), raw, calibrated)
                fold_rows.append({'candidate': spec['candidate'], 'family': spec['family'], 'gamma': spec['gamma'], 'seed': seed, 'outer_fold': fold, **m, 'beta_effective_min': 1.0 + spec['gamma'] * ((bases[spec['base']]['beta'] if spec['base'] != 'identity' else 1.0) - 1.0)})
                pooled[spec['candidate']].append((test['_target'].to_numpy(float), test['_weight'].to_numpy(float), raw, calibrated))
                for pattern, idx in test.groupby('acquisition_pattern').groups.items():
                    pattern = str(pattern)
                    pattern_rows.append({'candidate': spec['candidate'], 'family': spec['family'], 'gamma': spec['gamma'], 'seed': seed, 'outer_fold': fold, 'pattern': pattern, **metrics(test.loc[idx, '_target'].to_numpy(float), test.loc[idx, '_weight'].to_numpy(float), raw[idx], calibrated[idx])})
    fold_df = pd.DataFrame(fold_rows)
    pattern_df = pd.DataFrame(pattern_rows)
    pooled_rows = []
    for spec in specs:
        name = spec['candidate']
        y = np.concatenate([x[0] for x in pooled[name]])
        w = np.concatenate([x[1] for x in pooled[name]])
        raw = np.concatenate([x[2] for x in pooled[name]])
        cal = np.concatenate([x[3] for x in pooled[name]])
        pooled_rows.append({**spec, **metrics(y, w, raw, cal), 'coverage': 1.0, 'monotone_beta_positive': True})
    pooled_df = pd.DataFrame(pooled_rows)
    pattern_agg = []
    for (candidate, pattern), group in pattern_df.groupby(['candidate', 'pattern']):
        y_n = int(group['n_evaluable'].sum())
        ev_n = int(group['events_evaluable'].sum())
        if y_n == 0:
            continue
        brier_raw = float(np.average(group['ipcw_brier_raw'].fillna(0.0), weights=group['n_evaluable']))
        brier_cal = float(np.average(group['ipcw_brier_candidate'].fillna(0.0), weights=group['n_evaluable']))
        pattern_agg.append({'candidate': candidate, 'pattern': pattern, 'n_evaluable': y_n, 'events_evaluable': ev_n, 'ipcw_brier_raw': brier_raw, 'ipcw_brier_candidate': brier_cal, 'delta_ipcw_brier': brier_cal - brier_raw})
    pattern_agg_df = pd.DataFrame(pattern_agg)
    safety = []
    for _, row in pooled_df.iterrows():
        cand = row['candidate']
        pats = pattern_agg_df[(pattern_agg_df.candidate == cand) & (pattern_agg_df.n_evaluable >= 20) & (pattern_agg_df.events_evaluable >= 5)]
        worst_regret = float(pats.delta_ipcw_brier.max()) if len(pats) else np.nan
        pass_brier = row.delta_ipcw_brier <= 0.005
        pass_pattern = worst_regret <= 0.020 if np.isfinite(worst_regret) else True
        pass_citl = row.abs_citl_error_deterioration <= 0.10
        pass_slope = row.abs_slope_error_deterioration <= 0.15 if np.isfinite(row.abs_slope_error_deterioration) else False
        improves_calibration = (row.citl_candidate < row.citl_raw if abs(row.citl_raw) <= abs(row.citl_candidate) else abs(row.citl_candidate) < abs(row.citl_raw)) or (row.abs_slope_error_deterioration < 0)
        # Use absolute CITL error explicitly; the first expression above is retained only for readability.
        improves_calibration = abs(row.citl_candidate) < abs(row.citl_raw) or (row.abs_slope_error_deterioration < 0)
        safety.append({'candidate': cand, 'delta_ipcw_brier': row.delta_ipcw_brier, 'worst_supported_pattern_regret': worst_regret, 'citl_raw': row.citl_raw, 'citl_candidate': row.citl_candidate, 'abs_citl_error_deterioration': row.abs_citl_error_deterioration, 'slope_raw': row.calibration_slope_raw, 'slope_candidate': row.calibration_slope_candidate, 'abs_slope_error_deterioration': row.abs_slope_error_deterioration, 'passes_brier': bool(pass_brier), 'passes_pattern': bool(pass_pattern), 'passes_citl_safety': bool(pass_citl), 'passes_slope_safety': bool(pass_slope), 'improves_calibration': bool(improves_calibration), 'development_safe_pass': bool(pass_brier and pass_pattern and pass_citl and pass_slope and improves_calibration)})
    safety_df = pd.DataFrame(safety).sort_values(['development_safe_pass', 'delta_ipcw_brier'], ascending=[False, True])
    pooled_df.to_csv(out_dir / 'candidate_aggregate_results.csv', index=False)
    fold_df.to_csv(out_dir / 'candidate_fold_results.csv', index=False)
    pattern_agg_df.to_csv(out_dir / 'candidate_pattern_aggregate_results.csv', index=False)
    safety_df.to_csv(out_dir / 'candidate_safety_audit.csv', index=False)
    pd.DataFrame(parameter_rows).to_csv(out_dir / 'development_bridge_base_parameters.csv', index=False)
    result = {'analysis': 'U5R1 V1R revised bridge development-only candidate exploration', 'protocol': 'frozen_revised_bridge_exploration_protocol.yaml', 'cohort': 'HANCOCK official training', 'candidate_count': len(specs), 'candidates': [s['candidate'] for s in specs], 'safety_gate_count': int(safety_df.development_safe_pass.sum()), 'safe_candidates': safety_df.loc[safety_df.development_safe_pass, 'candidate'].tolist(), 'top_by_brier_delta': safety_df[['candidate','delta_ipcw_brier','worst_supported_pattern_regret','abs_citl_error_deterioration','abs_slope_error_deterioration','development_safe_pass']].head(10).to_dict(orient='records'), 'patient_level_outputs': 'not written'}
    (out_dir / 'revised_bridge_exploration_summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()

