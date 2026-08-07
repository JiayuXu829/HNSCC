"""Governance-safe survival metrics for Phase 3 development evaluation."""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
from sksurv.metrics import (
    concordance_index_censored,
    concordance_index_ipcw,
    cumulative_dynamic_auc,
)


def structured_survival(event: Iterable[bool], time: Iterable[float]) -> np.ndarray:
    event_array = np.asarray(event, dtype=bool)
    time_array = np.asarray(time, dtype=float)
    if event_array.shape != time_array.shape:
        raise ValueError("event and time must have identical shapes")
    if np.any(~np.isfinite(time_array)) or np.any(time_array < 0):
        raise ValueError("survival times must be finite and nonnegative")
    return np.array(
        list(zip(event_array, time_array, strict=True)),
        dtype=[("event", "?"), ("time", "<f8")],
    )


def _censoring_km(event: np.ndarray, time: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    event = np.asarray(event, dtype=bool)
    time = np.asarray(time, dtype=float)
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


def _step_value(
    unique: np.ndarray, values: np.ndarray, query: np.ndarray | float, *, left: bool
) -> np.ndarray:
    points = np.asarray(query, dtype=float)
    side = "left" if left else "right"
    indices = np.searchsorted(unique, points, side=side) - 1
    result = np.ones(points.shape, dtype=float)
    valid = indices >= 0
    result[valid] = values[indices[valid]]
    return result


def ipcw_binary_outcomes(
    train_event: Iterable[bool],
    train_time: Iterable[float],
    eval_event: Iterable[bool],
    eval_time: Iterable[float],
    horizon: float,
    survival_floor: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    """Return 24-month death indicators and training-derived IPCW weights.

    Evaluation subjects censored on or before the horizon receive zero weight and are never
    mislabeled as survivors.
    """
    train_event = np.asarray(train_event, dtype=bool)
    train_time = np.asarray(train_time, dtype=float)
    eval_event = np.asarray(eval_event, dtype=bool)
    eval_time = np.asarray(eval_time, dtype=float)
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    unique, before, after = _censoring_km(train_event, train_time)
    outcome = ((eval_event) & (eval_time <= horizon)).astype(float)
    weight = np.zeros(eval_time.shape, dtype=float)

    event_before = eval_event & (eval_time <= horizon)
    observed_beyond = eval_time > horizon
    if np.any(event_before):
        g_left = _step_value(unique, before, eval_time[event_before], left=True)
        weight[event_before] = 1.0 / np.maximum(g_left, survival_floor)
    if np.any(observed_beyond):
        g_horizon = float(_step_value(unique, after, np.asarray([horizon]), left=False)[0])
        weight[observed_beyond] = 1.0 / max(g_horizon, survival_floor)
    return outcome, weight


def _weighted_logistic_calibration(
    outcome: np.ndarray, weight: np.ndarray, risk: np.ndarray
) -> tuple[float, float]:
    mask = (weight > 0) & np.isfinite(risk)
    y = outcome[mask]
    w = weight[mask]
    p = np.clip(risk[mask], 1e-6, 1 - 1e-6)
    if y.size == 0 or np.unique(y).size < 2:
        return math.nan, math.nan
    offset = np.log(p / (1.0 - p))

    intercept = 0.0
    for _ in range(100):
        mu = 1.0 / (1.0 + np.exp(-(offset + intercept)))
        gradient = np.sum(w * (y - mu))
        information = np.sum(w * mu * (1.0 - mu))
        if information <= 1e-12:
            break
        step = gradient / information
        intercept += step
        if abs(step) < 1e-9:
            break

    if float(np.std(offset)) < 1e-12:
        return float(intercept), math.nan
    design = np.column_stack([np.ones_like(offset), offset])
    beta = np.array([0.0, 1.0], dtype=float)
    for _ in range(100):
        eta = np.clip(design @ beta, -30, 30)
        mu = 1.0 / (1.0 + np.exp(-eta))
        gradient = design.T @ (w * (y - mu))
        information = design.T @ ((w * mu * (1.0 - mu))[:, None] * design)
        try:
            step = np.linalg.solve(information + np.eye(2) * 1e-9, gradient)
        except np.linalg.LinAlgError:
            return float(intercept), math.nan
        beta += step
        if float(np.max(np.abs(step))) < 1e-9:
            break
    return float(intercept), float(beta[1])


def evaluate_survival_predictions(
    train_event: Iterable[bool],
    train_time: Iterable[float],
    eval_event: Iterable[bool],
    eval_time: Iterable[float],
    risk_score: Iterable[float],
    risk_horizon: Iterable[float],
    horizon: float,
    survival_floor: float = 0.05,
) -> dict[str, float]:
    train_event = np.asarray(train_event, dtype=bool)
    train_time = np.asarray(train_time, dtype=float)
    eval_event = np.asarray(eval_event, dtype=bool)
    eval_time = np.asarray(eval_time, dtype=float)
    risk_score = np.asarray(risk_score, dtype=float)
    risk_horizon = np.clip(np.asarray(risk_horizon, dtype=float), 0.0, 1.0)
    if not (
        eval_event.shape == eval_time.shape == risk_score.shape == risk_horizon.shape
    ):
        raise ValueError("evaluation arrays must have identical shapes")

    outcome, weight = ipcw_binary_outcomes(
        train_event,
        train_time,
        eval_event,
        eval_time,
        horizon,
        survival_floor=survival_floor,
    )
    denominator = max(1, eval_time.size)
    brier = float(np.sum(weight * (outcome - risk_horizon) ** 2) / denominator)
    intercept, slope = _weighted_logistic_calibration(outcome, weight, risk_horizon)

    try:
        harrell = float(concordance_index_censored(eval_event, eval_time, risk_score)[0])
    except Exception:
        harrell = math.nan
    train_y = structured_survival(train_event, train_time)
    eval_y = structured_survival(eval_event, eval_time)
    tau = min(float(horizon), float(np.nextafter(np.max(train_time), 0.0)))
    try:
        uno = float(concordance_index_ipcw(train_y, eval_y, risk_score, tau=tau)[0])
    except Exception:
        uno = math.nan
    try:
        auc_values, _ = cumulative_dynamic_auc(
            train_y, eval_y, risk_score, np.asarray([float(horizon)])
        )
        auc = float(auc_values[0])
    except Exception:
        auc = math.nan
    return {
        "n": float(eval_time.size),
        "events": float(np.sum(eval_event)),
        "ipcw_evaluable_weight": float(np.sum(weight)),
        "ipcw_brier": brier,
        "harrell_c": harrell,
        "uno_c": uno,
        "auc_horizon": auc,
        "calibration_in_the_large": intercept,
        "calibration_slope": slope,
        "mean_predicted_risk": float(np.mean(risk_horizon)),
    }


def decision_curve_ipcw(
    train_event: Iterable[bool],
    train_time: Iterable[float],
    eval_event: Iterable[bool],
    eval_time: Iterable[float],
    risk_horizon: Iterable[float],
    horizon: float,
    thresholds: Iterable[float],
    survival_floor: float = 0.05,
) -> list[dict[str, float]]:
    outcome, weight = ipcw_binary_outcomes(
        train_event,
        train_time,
        eval_event,
        eval_time,
        horizon,
        survival_floor=survival_floor,
    )
    risk = np.asarray(risk_horizon, dtype=float)
    n = max(1, risk.size)
    rows: list[dict[str, float]] = []
    prevalence = float(np.sum(weight * outcome) / n)
    for threshold in thresholds:
        threshold = float(threshold)
        if not 0 < threshold < 1:
            raise ValueError("DCA thresholds must be in (0, 1)")
        predicted = risk >= threshold
        tp = float(np.sum(weight * outcome * predicted) / n)
        fp = float(np.sum(weight * (1.0 - outcome) * predicted) / n)
        penalty = threshold / (1.0 - threshold)
        rows.append(
            {
                "threshold": threshold,
                "net_benefit_model": tp - fp * penalty,
                "net_benefit_all": prevalence - (1.0 - prevalence) * penalty,
                "net_benefit_none": 0.0,
            }
        )
    return rows
