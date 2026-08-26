from __future__ import annotations

import argparse
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
INTERCEPT_N = 50
INTERCEPT_EVENTS = 15
SLOPE_N = 100
SLOPE_EVENTS = 25
EPS = 1e-8


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
    return np.log(p / (1.0 - p))


def sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(x, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-x))


def horizon_targets_and_weights(duration, event, censor_fit_duration, censor_fit_event):
    duration = np.asarray(duration, dtype=float)
    event = np.asarray(event, dtype=int).astype(bool)
    fit_duration = np.asarray(censor_fit_duration, dtype=float)
    fit_event = np.asarray(censor_fit_event, dtype=int).astype(bool)
    censor_y = Surv.from_arrays(event=fit_event, time=fit_duration)
    censor = CensoringDistributionEstimator().fit(censor_y)
    target = np.full(duration.shape, np.nan, dtype=float)
    weights = np.zeros(duration.shape, dtype=float)
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
        weights[included] = 1.0 / g
    return target, weights, included


def fit_logistic(x, y, w):
    model = LogisticRegression(penalty=None, solver='lbfgs', max_iter=2000)
    model.fit(np.asarray(x).reshape(-1, 1), y.astype(int), sample_weight=w)
    return float(model.intercept_[0]), float(model.coef_[0, 0])


def fit_fixed_slope_intercept(x, y, w, slope):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float)

    def objective(alpha):
        z = np.clip(alpha + slope * x, -40.0, 40.0)
        # negative weighted Bernoulli log likelihood
        return float(np.sum(w * (np.logaddexp(0.0, z) - y * z)))

    return float(minimize_scalar(objective, bounds=(-20.0, 20.0), method='bounded').x)


def fit_bridge(train, pattern):
    mask = np.ones(len(train), dtype=bool) if pattern is None else (train['acquisition_pattern'].astype(str).to_numpy() == pattern)
    subset = train.loc[mask]
    y = subset['_target'].to_numpy()
    w = subset['_weight'].to_numpy()
    x = subset['_x'].to_numpy()
    included = w > 0
    subset = subset.loc[included]
    y, w, x = y[included], w[included], x[included]
    n = len(subset)
    events = int(y @ (w > 0)) if n else 0
    # Count observed horizon events from the unweighted target.
    events = int(np.sum(y == 1))
    if n == 0 or np.unique(y).size < 2:
        return {'kind': 'global', 'alpha': np.nan, 'beta': np.nan, 'n': n, 'events': events}
    global_alpha, global_beta = fit_logistic(x, y, w)
    if pattern is None:
        return {'kind': 'global', 'alpha': global_alpha, 'beta': global_beta, 'n': n, 'events': events}
    if n >= SLOPE_N and events >= SLOPE_EVENTS:
        alpha, beta = fit_logistic(x, y, w)
        return {'kind': 'pattern_slope', 'alpha': alpha, 'beta': beta, 'n': n, 'events': events}
    if n >= INTERCEPT_N and events >= INTERCEPT_EVENTS:
        alpha = fit_fixed_slope_intercept(x, y, w, global_beta)
        return {'kind': 'pattern_intercept', 'alpha': alpha, 'beta': global_beta, 'n': n, 'events': events}
    return {'kind': 'global', 'alpha': global_alpha, 'beta': global_beta, 'n': n, 'events': events}


def apply_bridge(frame, global_bridge, pattern_bridges):
    x = frame['_x'].to_numpy()
    out = np.empty(len(frame), dtype=float)
    patterns = frame['acquisition_pattern'].astype(str).to_numpy()
    for pattern in np.unique(patterns):
        idx = patterns == pattern
        bridge = pattern_bridges.get(pattern, global_bridge)
        if not np.isfinite(bridge['alpha']) or not np.isfinite(bridge['beta']):
            bridge = global_bridge
        out[idx] = sigmoid(bridge['alpha'] + bridge['beta'] * x[idx])
    return out


def evaluate(y, w, raw, calibrated):
    keep = w > 0
    y, w, raw, calibrated = y[keep], w[keep], raw[keep], calibrated[keep]
    def brier(p):
        return float(np.sum(w * (y - p) ** 2) / np.sum(w))
    # Calibration-in-the-large and slope on the evaluation partition.
    x = logit(raw)
    citl = fit_fixed_slope_intercept(x, y, w, 1.0)
    if np.unique(y).size >= 2:
        _, slope = fit_logistic(x, y, w)
        _, cal_slope = fit_logistic(logit(calibrated), y, w)
    else:
        slope, cal_slope = np.nan, np.nan
    cal_citl = fit_fixed_slope_intercept(logit(calibrated), y, w, 1.0)
    return {
        'ipcw_brier_raw': brier(raw),
        'ipcw_brier_calibrated': brier(calibrated),
        'delta_ipcw_brier': brier(calibrated) - brier(raw),
        'citl_raw': citl,
        'citl_calibrated': cal_citl,
        'calibration_slope_raw': slope,
        'calibration_slope_calibrated': cal_slope,
        'n_evaluable': int(len(y)),
        'events_evaluable': int(np.sum(y == 1)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root
    pred_path = root / 'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv'
    out_dir = root / 'research_studies/01_pattern_surv_hn/core_backbone/U5_V1R_calibration_bridge_protocol'
    out_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(pred_path, dtype={'acquisition_pattern': str, 'usable_pattern': str})
    required = {'repetition_seed', 'outer_fold', 'duration_days', 'event', 'acquisition_pattern', 'v1_risk_24m'}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f'missing columns: {sorted(missing)}')
    fold_rows = []
    bridge_rows = []
    all_eval = []
    for seed in SEEDS:
        seed_data = data.loc[data.repetition_seed == seed].copy()
        if len(seed_data) != 610:
            raise ValueError(f'seed {seed} has {len(seed_data)} rows, expected 610')
        for fold in range(FOLDS):
            train = seed_data.loc[seed_data.outer_fold != fold].copy()
            test = seed_data.loc[seed_data.outer_fold == fold].copy()
            train_target, train_weight, train_included = horizon_targets_and_weights(
                train.duration_days, train.event, train.duration_days, ~train.event.astype(bool)
            )
            test_target, test_weight, test_included = horizon_targets_and_weights(
                test.duration_days, test.event, train.duration_days, ~train.event.astype(bool)
            )
            train['_target'], train['_weight'], train['_included'] = train_target, train_weight, train_included
            test['_target'], test['_weight'], test['_included'] = test_target, test_weight, test_included
            train['_x'] = logit(train.v1_risk_24m.to_numpy())
            test['_x'] = logit(test.v1_risk_24m.to_numpy())
            global_bridge = fit_bridge(train, None)
            pattern_bridges = {}
            for pattern in sorted(train.acquisition_pattern.astype(str).unique()):
                pattern_bridges[pattern] = fit_bridge(train, pattern)
                bridge_rows.append({'seed': seed, 'outer_fold': fold, 'pattern': pattern, **pattern_bridges[pattern]})
            calibrated = apply_bridge(test, global_bridge, pattern_bridges)
            metrics = evaluate(test['_target'].to_numpy(), test['_weight'].to_numpy(), test.v1_risk_24m.to_numpy(), calibrated)
            fold_rows.append({'seed': seed, 'outer_fold': fold, **metrics, 'global_alpha': global_bridge['alpha'], 'global_beta': global_bridge['beta']})
            all_eval.append(pd.DataFrame({'seed': seed, 'outer_fold': fold, 'target': test['_target'], 'weight': test['_weight'], 'raw': test.v1_risk_24m, 'calibrated': calibrated, 'pattern': test.acquisition_pattern.astype(str)}))
    fold_df = pd.DataFrame(fold_rows)
    eval_df = pd.concat(all_eval, ignore_index=True)
    metrics = evaluate(eval_df.target.to_numpy(), eval_df.weight.to_numpy(), eval_df.raw.to_numpy(), eval_df.calibrated.to_numpy())
    pattern_summary = []
    for pattern, group in eval_df.groupby('pattern'):
        if (group.weight > 0).sum() == 0:
            continue
        pm = evaluate(group.target.to_numpy(), group.weight.to_numpy(), group.raw.to_numpy(), group.calibrated.to_numpy())
        pattern_summary.append({'pattern': pattern, **pm})
    result = {
        'analysis': 'U5/V1R development-only cross-fitted calibration bridge diagnostics',
        'protocol': 'frozen_calibration_bridge_protocol.yaml',
        'cohort': 'HANCOCK official training',
        'eligible_n': 610,
        'events': 173,
        'seeds': SEEDS,
        'outer_folds': FOLDS,
        'global_aggregate': metrics,
        'fold_aggregate_mean': {k: float(fold_df[k].mean()) for k in metrics if k in fold_df},
        'pattern_aggregate': pattern_summary,
        'support_gates': {'intercept_n': INTERCEPT_N, 'intercept_events': INTERCEPT_EVENTS, 'slope_n': SLOPE_N, 'slope_events': SLOPE_EVENTS},
        'patient_level_outputs': 'stored only in runtime audit and not copied to paper-facing directory',
    }
    (out_dir / 'development_cross_fitted_bridge_results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    fold_df.to_csv(out_dir / 'development_cross_fitted_bridge_fold_results.csv', index=False)
    pd.DataFrame(bridge_rows).to_csv(out_dir / 'development_bridge_parameters.csv', index=False)
    print(json.dumps(result['global_aggregate'], indent=2))


if __name__ == '__main__':
    main()



