"""Nested cross-fitted V0 clinical-pathological safety anchor for PATTERN-Surv-HN.

This isolated implementation uses eligible HANCOCK official-training records only, fits all
preprocessing inside the corresponding training fold, and writes patient-level OOF predictions
only below the repository's git-ignored predictions root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import warnings
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import StratifiedKFold
from sksurv.linear_model import CoxnetSurvivalAnalysis
from sksurv.metrics import (
    concordance_index_censored,
    concordance_index_ipcw,
    cumulative_dynamic_auc,
)

from trust_hn.pattern_surv_hn.hancock_contract import (
    ANCHOR_CATEGORICAL_FEATURES,
    ANCHOR_NUMERIC_FEATURES,
    FoldBoundMixedPreprocessor,
    HancockContract,
    HancockContractBuilder,
)

ANALYSIS_DATE = "2026-08-14"
MODEL_ID = "V0"
MODEL_NAME = "extended_postoperative_clinical_pathological_elastic_net_cox"
PATIENT_OUTPUT_RELATIVE = Path("results/predictions/pattern_surv_hn/U1_2_V0")
DEFAULT_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/U1_2_V0_clinical_anchor/frozen_v0_spec.yaml"
)
DEFAULT_AUDIT_RELATIVE = DEFAULT_SPEC_RELATIVE.parent / "aggregate_v0_audit.json"
SENSITIVE_KEYS = frozenset({"native_id", "patient_id", "case_id", "submitter_id"})


@dataclass(frozen=True)
class CoxnetCandidate:
    alpha: float
    l1_ratio: float


@dataclass(frozen=True)
class V0Spec:
    horizon_days: float
    outer_folds: int
    outer_repetition_seeds: tuple[int, ...]
    inner_folds: int
    alpha_grid: tuple[float, ...]
    l1_ratio_grid: tuple[float, ...]
    max_iter: int
    tolerance: float
    pattern_minimum_n: int
    pattern_minimum_events: int

    @classmethod
    def from_yaml(cls, path: Path) -> V0Spec:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
        cross = payload["cross_fitting"]
        hyper = payload["hyperparameter_selection"]
        support = payload["evaluation"]["pattern_metric_support"]
        spec = cls(
            horizon_days=float(payload["endpoint"]["horizon_days"]),
            outer_folds=int(cross["outer_folds"]),
            outer_repetition_seeds=tuple(int(v) for v in cross["outer_repetition_seeds"]),
            inner_folds=int(cross["inner_folds"]),
            alpha_grid=tuple(float(v) for v in hyper["alpha_grid"]),
            l1_ratio_grid=tuple(float(v) for v in hyper["l1_ratio_grid"]),
            max_iter=int(hyper["max_iter"]),
            tolerance=float(hyper["tolerance"]),
            pattern_minimum_n=int(support["minimum_n"]),
            pattern_minimum_events=int(support["minimum_events"]),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        if self.outer_folds < 2 or self.inner_folds < 2:
            raise ValueError("nested cross-fitting requires at least two folds")
        if not self.outer_repetition_seeds:
            raise ValueError("at least one outer repetition seed is required")
        if not self.alpha_grid or any(v <= 0 for v in self.alpha_grid):
            raise ValueError("alpha_grid must contain positive values")
        if not self.l1_ratio_grid or any(not 0 < v <= 1 for v in self.l1_ratio_grid):
            raise ValueError("l1_ratio_grid values must be in (0, 1]")
        if self.pattern_minimum_n < 1 or self.pattern_minimum_events < 1:
            raise ValueError("pattern support thresholds must be positive")

    @property
    def candidates(self) -> tuple[CoxnetCandidate, ...]:
        return tuple(
            CoxnetCandidate(alpha=alpha, l1_ratio=ratio)
            for alpha in self.alpha_grid
            for ratio in self.l1_ratio_grid
        )


@dataclass(frozen=True)
class PreparedFold:
    x_train: np.ndarray
    y_train: np.ndarray
    x_valid: np.ndarray
    y_valid: np.ndarray


@dataclass(frozen=True)
class FittedAnchor:
    model: CoxnetSurvivalAnalysis
    feature_names: tuple[str, ...]


def structured_survival(event: Iterable[bool], time: Iterable[float]) -> np.ndarray:
    event_array = np.asarray(event, dtype=bool)
    time_array = np.asarray(time, dtype=float)
    if event_array.shape != time_array.shape:
        raise ValueError("event and time arrays must have identical shape")
    if np.any(~np.isfinite(time_array)) or np.any(time_array <= 0):
        raise ValueError("V0 survival times must be finite and strictly positive")
    return np.array(
        list(zip(event_array, time_array, strict=True)),
        dtype=[("event", "?"), ("time", "<f8")],
    )


def _censoring_km(event: np.ndarray, time: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
    indices = np.searchsorted(unique, points, side="left" if left else "right") - 1
    result = np.ones(points.shape, dtype=float)
    valid = indices >= 0
    result[valid] = values[indices[valid]]
    return result


def ipcw_binary_outcomes(
    train_y: np.ndarray, eval_y: np.ndarray, horizon: float, survival_floor: float = 0.05
) -> tuple[np.ndarray, np.ndarray]:
    train_event = np.asarray(train_y["event"], dtype=bool)
    train_time = np.asarray(train_y["time"], dtype=float)
    eval_event = np.asarray(eval_y["event"], dtype=bool)
    eval_time = np.asarray(eval_y["time"], dtype=float)
    unique, before, after = _censoring_km(train_event, train_time)
    outcome = (eval_event & (eval_time <= horizon)).astype(float)
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
    y, w = outcome[mask], weight[mask]
    p = np.clip(risk[mask], 1e-6, 1.0 - 1e-6)
    if y.size == 0 or np.unique(y).size < 2:
        return math.nan, math.nan
    offset = np.log(p / (1.0 - p))
    intercept = 0.0
    for _ in range(100):
        eta = np.clip(offset + intercept, -30.0, 30.0)
        mu = 1.0 / (1.0 + np.exp(-eta))
        gradient = float(np.sum(w * (y - mu)))
        information = float(np.sum(w * mu * (1.0 - mu)))
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
        eta = np.clip(design @ beta, -30.0, 30.0)
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


def evaluate_predictions(
    train_y: np.ndarray,
    eval_y: np.ndarray,
    risk_score: Sequence[float],
    risk_horizon: Sequence[float],
    horizon: float,
) -> dict[str, float]:
    score = np.asarray(risk_score, dtype=float)
    risk = np.clip(np.asarray(risk_horizon, dtype=float), 0.0, 1.0)
    if len(eval_y) != len(score) or len(eval_y) != len(risk):
        raise ValueError("prediction and evaluation lengths differ")
    outcome, weight = ipcw_binary_outcomes(train_y, eval_y, horizon)
    brier = float(np.sum(weight * (outcome - risk) ** 2) / max(1, len(eval_y)))
    intercept, slope = _weighted_logistic_calibration(outcome, weight, risk)
    try:
        harrell = float(concordance_index_censored(eval_y["event"], eval_y["time"], score)[0])
    except Exception:
        harrell = math.nan
    tau = min(float(horizon), float(np.nextafter(np.max(train_y["time"]), 0.0)))
    try:
        uno = float(concordance_index_ipcw(train_y, eval_y, score, tau=tau)[0])
    except Exception:
        uno = math.nan
    try:
        auc_values, _ = cumulative_dynamic_auc(train_y, eval_y, score, np.asarray([float(horizon)]))
        auc = float(auc_values[0])
    except Exception:
        auc = math.nan
    return {
        "n": float(len(eval_y)),
        "events": float(np.sum(eval_y["event"])),
        "ipcw_evaluable_weight": float(np.sum(weight)),
        "ipcw_brier_24m": brier,
        "harrell_c": harrell,
        "uno_c_24m": uno,
        "auc_24m": auc,
        "calibration_in_the_large_24m": intercept,
        "calibration_slope_24m": slope,
        "mean_predicted_risk_24m": float(np.mean(risk)),
    }


def _fit_anchor(
    x_train: np.ndarray,
    y_train: np.ndarray,
    candidate: CoxnetCandidate,
    spec: V0Spec,
    feature_names: Sequence[str],
) -> FittedAnchor:
    model = CoxnetSurvivalAnalysis(
        alphas=[candidate.alpha],
        l1_ratio=candidate.l1_ratio,
        max_iter=spec.max_iter,
        tol=spec.tolerance,
        fit_baseline_model=True,
        normalize=False,
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="all coefficients are zero.*")
        model.fit(np.asarray(x_train, dtype=float), y_train)
    return FittedAnchor(model=model, feature_names=tuple(feature_names))


def _predict_anchor(
    fitted: FittedAnchor, x_eval: np.ndarray, horizon: float
) -> tuple[np.ndarray, np.ndarray]:
    matrix = np.asarray(x_eval, dtype=float)
    score = np.asarray(fitted.model.predict(matrix), dtype=float)
    functions = fitted.model.predict_survival_function(matrix)
    evaluation_time = min(float(horizon), float(np.max(fitted.model.unique_times_)))
    survival = np.asarray([float(function(evaluation_time)) for function in functions])
    return score, np.clip(1.0 - survival, 0.0, 1.0)


def _event_stratified_splits(
    event: Sequence[bool], n_splits: int, seed: int
) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    event_array = np.asarray(event, dtype=int)
    if int(np.sum(event_array)) < n_splits or int(np.sum(event_array == 0)) < n_splits:
        raise ValueError("each event stratum must support every requested fold")
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=int(seed))
    dummy = np.zeros(len(event_array), dtype=float)
    splits = tuple((train, valid) for train, valid in splitter.split(dummy, event_array))
    for train, valid in splits:
        if np.unique(event_array[train]).size != 2 or np.unique(event_array[valid]).size != 2:
            raise ValueError("every survival fold must contain events and censorings")
    return splits


def _prepare_inner_folds(
    anchor: pd.DataFrame,
    ids: np.ndarray,
    event: np.ndarray,
    time: np.ndarray,
    spec: V0Spec,
    seed: int,
) -> tuple[PreparedFold, ...]:
    folds: list[PreparedFold] = []
    for train_idx, valid_idx in _event_stratified_splits(event, spec.inner_folds, seed):
        train_ids = ids[train_idx].tolist()
        valid_ids = ids[valid_idx].tolist()
        prep = FoldBoundMixedPreprocessor(
            numeric=ANCHOR_NUMERIC_FEATURES,
            categorical=ANCHOR_CATEGORICAL_FEATURES,
            allowed_fit_ids=set(train_ids),
        )
        train_block = prep.fit_transform(anchor, train_ids)
        valid_block = prep.transform(anchor, valid_ids)
        folds.append(
            PreparedFold(
                x_train=train_block.values,
                y_train=structured_survival(event[train_idx], time[train_idx]),
                x_valid=valid_block.values,
                y_valid=structured_survival(event[valid_idx], time[valid_idx]),
            )
        )
    return tuple(folds)


def _select_candidate(
    prepared: Sequence[PreparedFold], spec: V0Spec
) -> tuple[CoxnetCandidate, list[dict[str, float]]]:
    candidate_rows: list[dict[str, float]] = []
    for candidate in spec.candidates:
        brier_values: list[float] = []
        uno_values: list[float] = []
        failures = 0
        for fold in prepared:
            try:
                fitted = _fit_anchor(
                    fold.x_train,
                    fold.y_train,
                    candidate,
                    spec,
                    feature_names=tuple(f"x{i}" for i in range(fold.x_train.shape[1])),
                )
                score, risk = _predict_anchor(fitted, fold.x_valid, spec.horizon_days)
                metrics = evaluate_predictions(
                    fold.y_train, fold.y_valid, score, risk, spec.horizon_days
                )
                brier_values.append(float(metrics["ipcw_brier_24m"]))
                uno_values.append(float(metrics["uno_c_24m"]))
            except Exception:
                failures += 1
        mean_brier = float(np.mean(brier_values)) if brier_values else math.inf
        finite_uno = [value for value in uno_values if np.isfinite(value)]
        mean_uno = float(np.mean(finite_uno)) if finite_uno else -math.inf
        candidate_rows.append(
            {
                "alpha": candidate.alpha,
                "l1_ratio": candidate.l1_ratio,
                "mean_inner_ipcw_brier_24m": mean_brier,
                "mean_inner_uno_c_24m": mean_uno,
                "successful_inner_folds": float(len(brier_values)),
                "failed_inner_folds": float(failures),
            }
        )
    valid_rows = [
        row
        for row in candidate_rows
        if row["successful_inner_folds"] == float(spec.inner_folds)
        and np.isfinite(row["mean_inner_ipcw_brier_24m"])
    ]
    if not valid_rows:
        raise RuntimeError("all frozen Coxnet candidates failed inner cross-validation")
    winner = min(
        valid_rows,
        key=lambda row: (
            row["mean_inner_ipcw_brier_24m"],
            -row["mean_inner_uno_c_24m"],
            row["alpha"],
            row["l1_ratio"],
        ),
    )
    return CoxnetCandidate(winner["alpha"], winner["l1_ratio"]), candidate_rows


def _development_arrays(
    contract: HancockContract,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    frame = contract.patient_frame().set_index("native_id")
    sealed = frame[frame["official_partition"] == "test"]
    if len(sealed) != 152 or not sealed["outcome_sealed"].all():
        raise RuntimeError("official-test sealing contract is not intact")
    if sealed["duration_days"].notna().any() or sealed["event"].notna().any():
        raise RuntimeError("official-test outcomes were exposed")
    development = frame[(frame["official_partition"] == "training") & frame["eligible"]].copy()
    ids = development.index.to_numpy(dtype=str)
    event = development["event"].to_numpy(dtype=bool)
    time = development["duration_days"].to_numpy(dtype=float)
    patterns = development["acquisition_pattern"].to_numpy(dtype=str)
    if len(ids) != 610 or int(np.sum(event)) != 173:
        raise RuntimeError("development estimand differs from the frozen 610/173 contract")
    return development, ids, event, time, patterns


def nested_cross_fit(
    contract: HancockContract, spec: V0Spec
) -> tuple[pd.DataFrame, dict[str, object]]:
    _, ids, event, time, patterns = _development_arrays(contract)
    anchor = contract.anchor
    rows: list[dict[str, object]] = []
    fold_audit: list[dict[str, object]] = []
    tuning_counter: Counter[tuple[float, float]] = Counter()
    feature_counter: Counter[str] = Counter()

    for repetition_seed in spec.outer_repetition_seeds:
        outer_splits = _event_stratified_splits(event, spec.outer_folds, repetition_seed)
        repetition_seen: list[str] = []
        for outer_fold, (train_idx, valid_idx) in enumerate(outer_splits):
            train_ids = ids[train_idx]
            valid_ids = ids[valid_idx]
            inner_seed = int(repetition_seed * 100 + outer_fold + 1)
            prepared = _prepare_inner_folds(
                anchor, train_ids, event[train_idx], time[train_idx], spec, inner_seed
            )
            selected, candidate_rows = _select_candidate(prepared, spec)
            tuning_counter[(selected.alpha, selected.l1_ratio)] += 1

            prep = FoldBoundMixedPreprocessor(
                numeric=ANCHOR_NUMERIC_FEATURES,
                categorical=ANCHOR_CATEGORICAL_FEATURES,
                allowed_fit_ids=set(train_ids.tolist()),
            )
            train_block = prep.fit_transform(anchor, train_ids.tolist())
            valid_block = prep.transform(anchor, valid_ids.tolist())
            y_train = structured_survival(event[train_idx], time[train_idx])
            y_valid = structured_survival(event[valid_idx], time[valid_idx])
            fitted = _fit_anchor(
                train_block.values, y_train, selected, spec, train_block.feature_names
            )
            score, risk = _predict_anchor(fitted, valid_block.values, spec.horizon_days)
            fold_metrics = evaluate_predictions(y_train, y_valid, score, risk, spec.horizon_days)
            coefficients = np.asarray(fitted.model.coef_).reshape(
                len(train_block.feature_names), -1
            )[:, 0]
            nonzero_mask = np.abs(coefficients) > 1e-12
            for feature_name in np.asarray(train_block.feature_names)[nonzero_mask].tolist():
                feature_counter[str(feature_name)] += 1

            best_inner = next(
                candidate
                for candidate in candidate_rows
                if candidate["alpha"] == selected.alpha
                and candidate["l1_ratio"] == selected.l1_ratio
            )
            fold_audit.append(
                {
                    "repetition_seed": repetition_seed,
                    "outer_fold": outer_fold,
                    "train_n": len(train_idx),
                    "train_events": int(np.sum(event[train_idx])),
                    "validation_n": len(valid_idx),
                    "validation_events": int(np.sum(event[valid_idx])),
                    "selected_alpha": selected.alpha,
                    "selected_l1_ratio": selected.l1_ratio,
                    "selected_inner_ipcw_brier_24m": best_inner["mean_inner_ipcw_brier_24m"],
                    "selected_inner_uno_c_24m": best_inner["mean_inner_uno_c_24m"],
                    "encoded_feature_count": int(train_block.values.shape[1]),
                    "nonzero_coefficient_count": int(np.sum(nonzero_mask)),
                    "metrics": fold_metrics,
                }
            )
            for local_index, global_index in enumerate(valid_idx):
                patient_id = str(ids[global_index])
                repetition_seen.append(patient_id)
                rows.append(
                    {
                        "native_id": patient_id,
                        "repetition_seed": repetition_seed,
                        "outer_fold": outer_fold,
                        "duration_days": float(time[global_index]),
                        "event": int(event[global_index]),
                        "acquisition_pattern": str(patterns[global_index]),
                        "risk_score": float(score[local_index]),
                        "risk_24m": float(risk[local_index]),
                        "survival_24m": float(1.0 - risk[local_index]),
                        "selected_alpha": selected.alpha,
                        "selected_l1_ratio": selected.l1_ratio,
                    }
                )
        if len(repetition_seen) != len(ids) or set(repetition_seen) != set(ids):
            raise RuntimeError(f"OOF coverage failed for repetition seed {repetition_seed}")
        if len(repetition_seen) != len(set(repetition_seen)):
            raise RuntimeError(f"duplicate OOF prediction for repetition seed {repetition_seed}")

    oof = pd.DataFrame(rows).sort_values(
        ["repetition_seed", "outer_fold", "native_id"], ignore_index=True
    )
    full_y = structured_survival(event, time)
    id_to_index = {native_id: index for index, native_id in enumerate(ids)}
    per_seed_metrics: list[dict[str, object]] = []
    pattern_metrics: list[dict[str, object]] = []
    for repetition_seed, group in oof.groupby("repetition_seed", sort=True):
        group = group.set_index("native_id").loc[ids]
        seed_metrics = evaluate_predictions(
            full_y,
            full_y,
            group["risk_score"].to_numpy(dtype=float),
            group["risk_24m"].to_numpy(dtype=float),
            spec.horizon_days,
        )
        per_seed_metrics.append({"repetition_seed": int(repetition_seed), **seed_metrics})
        for pattern, pattern_group in group.groupby("acquisition_pattern", sort=True):
            indices = np.asarray([id_to_index[native_id] for native_id in pattern_group.index])
            n = len(pattern_group)
            events = int(np.sum(event[indices]))
            supported = n >= spec.pattern_minimum_n and events >= spec.pattern_minimum_events
            record: dict[str, object] = {
                "repetition_seed": int(repetition_seed),
                "acquisition_pattern": str(pattern),
                "n": n,
                "events": events,
                "metric_support": supported,
                "interpretation": (
                    "supported_exploratory" if supported else "descriptive_counts_only"
                ),
            }
            if supported:
                record["metrics"] = evaluate_predictions(
                    full_y,
                    structured_survival(event[indices], time[indices]),
                    pattern_group["risk_score"].to_numpy(dtype=float),
                    pattern_group["risk_24m"].to_numpy(dtype=float),
                    spec.horizon_days,
                )
            pattern_metrics.append(record)

    metric_names = (
        "ipcw_brier_24m",
        "harrell_c",
        "uno_c_24m",
        "auc_24m",
        "calibration_in_the_large_24m",
        "calibration_slope_24m",
        "mean_predicted_risk_24m",
    )
    summary: dict[str, dict[str, float]] = {}
    for metric_name in metric_names:
        values = np.asarray(
            [float(row[metric_name]) for row in per_seed_metrics if np.isfinite(row[metric_name])]
        )
        summary[metric_name] = {
            "mean": float(np.mean(values)) if values.size else math.nan,
            "sample_sd": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
            "minimum": float(np.min(values)) if values.size else math.nan,
            "maximum": float(np.max(values)) if values.size else math.nan,
        }

    aggregate = {
        "folds": fold_audit,
        "per_seed_metrics": per_seed_metrics,
        "across_seed_summary": summary,
        "pattern_stratified_metrics": pattern_metrics,
        "hyperparameter_selection_frequency": [
            {"alpha": alpha, "l1_ratio": ratio, "outer_fold_count": count}
            for (alpha, ratio), count in sorted(tuning_counter.items())
        ],
        "nonzero_feature_frequency_across_outer_models": [
            {"feature": feature, "outer_model_count": count}
            for feature, count in sorted(
                feature_counter.items(), key=lambda item: (-item[1], item[0])
            )
        ],
    }
    return oof, aggregate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _json_safe(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating | float):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def assert_aggregate_only(payload: object) -> None:
    def walk(value: object) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).casefold() in SENSITIVE_KEYS:
                    raise ValueError(
                        f"patient identifier key forbidden in aggregate artifact: {key}"
                    )
                walk(item)
        elif isinstance(value, list | tuple):
            for item in value:
                walk(item)

    walk(payload)


def run_v0_experiment(
    project_root: Path,
    *,
    spec_path: Path | None = None,
    patient_output_dir: Path | None = None,
    aggregate_audit_path: Path | None = None,
) -> dict[str, object]:
    root = Path(project_root).resolve()
    spec_path = (root / DEFAULT_SPEC_RELATIVE) if spec_path is None else Path(spec_path).resolve()
    patient_output_dir = (
        root / PATIENT_OUTPUT_RELATIVE
        if patient_output_dir is None
        else Path(patient_output_dir).resolve()
    )
    aggregate_audit_path = (
        root / DEFAULT_AUDIT_RELATIVE
        if aggregate_audit_path is None
        else Path(aggregate_audit_path).resolve()
    )
    allowed_patient_root = (root / "results/predictions/pattern_surv_hn").resolve()
    if allowed_patient_root not in patient_output_dir.parents:
        raise ValueError(
            "patient-level output must remain under results/predictions/pattern_surv_hn"
        )
    research_root = (root / "research_studies").resolve()
    if research_root == patient_output_dir or research_root in patient_output_dir.parents:
        raise ValueError("patient-level output is forbidden in research_studies")

    spec = V0Spec.from_yaml(spec_path)
    contract = HancockContractBuilder(root).build()
    oof, results = nested_cross_fit(contract, spec)
    patient_output_dir.mkdir(parents=True, exist_ok=True)
    oof_path = patient_output_dir / "v0_repeated_nested_oof_predictions.csv"
    oof.to_csv(oof_path, index=False)

    contract_frame = contract.patient_frame(include_identifiers=False)
    payload: dict[str, object] = {
        "schema_version": "0.1",
        "study_id": "pattern_surv_hn",
        "stage_id": "U1_2_V0",
        "analysis_label": "post_lock_exploratory",
        "completed_on": ANALYSIS_DATE,
        "model": {"id": MODEL_ID, "name": MODEL_NAME, "role": "safety_anchor"},
        "estimand": {
            "cohort": "HANCOCK_official_training",
            "eligible_n": 610,
            "events": 173,
            "excluded_nonpositive_postoperative_duration": int(
                (
                    (contract_frame["official_partition"] == "training")
                    & (~contract_frame["eligible"])
                ).sum()
            ),
            "horizon_days": spec.horizon_days,
            "official_test_n_sealed": int((contract_frame["official_partition"] == "test").sum()),
        },
        "features": {
            "numeric": list(ANCHOR_NUMERIC_FEATURES),
            "categorical": list(ANCHOR_CATEGORICAL_FEATURES),
            "pathology_is_anchor": True,
            "additional_modalities_used": [],
        },
        "nested_cross_fitting": {
            "outer_folds": spec.outer_folds,
            "outer_repetition_seeds": list(spec.outer_repetition_seeds),
            "inner_folds": spec.inner_folds,
            "candidate_count": len(spec.candidates),
            "selection_objective": "minimum mean inner-fold IPCW Brier at 730.5 days",
            "preprocessing_fit_inside_training_fold": True,
            "baseline_survival_fit_inside_training_fold": True,
            "pooled_metric_censoring_estimator": (
                "full eligible development cohort at evaluation only; predictions remain OOF"
            ),
            "oof_rows": len(oof),
            "expected_oof_rows": int(610 * len(spec.outer_repetition_seeds)),
        },
        "results": results,
        "calibration_definition": {
            "time_point": "730.5-day binary death risk",
            "censoring_adjustment": ("training-derived inverse probability of censoring weights"),
            "in_the_large": (
                "weighted logistic intercept with predicted logit risk as fixed offset"
            ),
            "slope": "weighted logistic coefficient multiplying predicted logit risk",
            "calibration_bridge_trained": False,
        },
        "governance": {
            "official_test_outcomes_derived_exposed_or_evaluated": False,
            "external_outcomes_used": False,
            "router_labels_created": False,
            "router_trained": False,
            "V1_or_V2_trained": False,
            "new_dependencies_installed": False,
            "tracked_artifacts_aggregate_only": True,
            "patient_level_oof_git_ignored": True,
        },
        "artifacts": {
            "frozen_spec": spec_path.relative_to(root).as_posix(),
            "frozen_spec_sha256": _sha256(spec_path),
            "patient_oof_relative_path": oof_path.relative_to(root).as_posix(),
            "patient_oof_sha256": _sha256(oof_path),
            "patient_oof_tracked": False,
        },
        "limitations": [
            (
                "Results are post-lock exploratory because prior Phase 6 outcomes "
                "had already been seen."
            ),
            "Repeated OOF estimates are internal development estimates, not external validation.",
            "Pattern metrics below the frozen n/event support gate are descriptive only.",
            "V0 evaluates only the safety anchor and cannot establish fusion or routing benefit.",
        ],
    }
    safe_payload = _json_safe(payload)
    assert_aggregate_only(safe_payload)
    aggregate_audit_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_audit_path.write_text(
        json.dumps(safe_payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return safe_payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path, default=None)
    parser.add_argument("--patient-output-dir", type=Path, default=None)
    parser.add_argument("--aggregate-audit", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = run_v0_experiment(
        args.project_root,
        spec_path=args.spec,
        patient_output_dir=args.patient_output_dir,
        aggregate_audit_path=args.aggregate_audit,
    )
    print(json.dumps(payload["results"]["across_seed_summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
