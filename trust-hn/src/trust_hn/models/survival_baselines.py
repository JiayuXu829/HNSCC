"""Prespecified Phase 3 survival baseline models."""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sksurv.ensemble import RandomSurvivalForest
from sksurv.linear_model import CoxnetSurvivalAnalysis, CoxPHSurvivalAnalysis
from sksurv.nonparametric import kaplan_meier_estimator

from trust_hn.metrics.survival import structured_survival as structured_survival


@dataclass(frozen=True)
class SurvivalPrediction:
    risk_score: np.ndarray
    risk_horizon: np.ndarray


class TabularPreprocessor:
    """Small deterministic mixed-type preprocessor fit only on supplied training rows."""

    def __init__(self, numeric: Sequence[str], categorical: Sequence[str]):
        self.numeric = list(numeric)
        self.categorical = list(categorical)
        self.numeric_medians_: dict[str, float] = {}
        self.numeric_means_: dict[str, float] = {}
        self.numeric_scales_: dict[str, float] = {}
        self.category_levels_: dict[str, tuple[str, ...]] = {}
        self.feature_names_: tuple[str, ...] = ()
        self.fitted_ = False

    @staticmethod
    def _clean_category(series: pd.Series) -> pd.Series:
        values = series.astype("string").str.strip()
        values = values.mask(values.isna() | values.eq(""), "Unknown")
        return values.fillna("Unknown")

    def fit(self, frame: pd.DataFrame) -> TabularPreprocessor:
        names: list[str] = []
        for column in self.numeric:
            values = pd.to_numeric(frame.get(column), errors="coerce")
            median = float(values.median()) if values.notna().any() else 0.0
            filled = values.fillna(median).astype(float)
            mean = float(filled.mean())
            scale = float(filled.std(ddof=0))
            if not np.isfinite(scale) or scale < 1e-12:
                scale = 1.0
            self.numeric_medians_[column] = median
            self.numeric_means_[column] = mean
            self.numeric_scales_[column] = scale
            names.extend([column, f"{column}__missing"])
        for column in self.categorical:
            values = self._clean_category(
                frame.get(column, pd.Series(index=frame.index, dtype="string"))
            )
            levels = sorted(set(values.astype(str)) | {"Unknown"})
            self.category_levels_[column] = tuple(levels)
            names.extend(f"{column}=={level}" for level in levels)
        self.feature_names_ = tuple(names)
        self.fitted_ = True
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("preprocessor must be fit before transform")
        columns: list[np.ndarray] = []
        n = len(frame)
        for column in self.numeric:
            raw = pd.to_numeric(frame.get(column), errors="coerce")
            missing = raw.isna().to_numpy(dtype=float)
            filled = raw.fillna(self.numeric_medians_[column]).to_numpy(dtype=float)
            standardized = (filled - self.numeric_means_[column]) / self.numeric_scales_[column]
            columns.extend([standardized, missing])
        for column in self.categorical:
            raw = self._clean_category(
                frame.get(column, pd.Series(index=frame.index, dtype="string"))
            ).astype(str)
            known = set(self.category_levels_[column])
            values = raw.where(raw.isin(known), "Unknown")
            for level in self.category_levels_[column]:
                columns.append((values == level).to_numpy(dtype=float))
        if not columns:
            return np.zeros((n, 0), dtype=float)
        matrix = np.column_stack(columns).astype(float, copy=False)
        if not np.isfinite(matrix).all():
            raise ValueError("preprocessing produced non-finite values")
        return matrix

    def fit_transform(self, frame: pd.DataFrame) -> np.ndarray:
        return self.fit(frame).transform(frame)


def _survival_risk_at_horizon(model: object, x_eval: np.ndarray, horizon: float) -> np.ndarray:
    functions = model.predict_survival_function(x_eval)
    unique_times = np.asarray(model.unique_times_, dtype=float)
    evaluation_time = min(float(horizon), float(unique_times[-1]))
    survival = np.asarray([float(function(evaluation_time)) for function in functions])
    return np.clip(1.0 - survival, 0.0, 1.0)


def _km_risk(y_train: np.ndarray, horizon: float) -> float:
    times, survival = kaplan_meier_estimator(y_train["event"], y_train["time"])
    index = int(np.searchsorted(times, horizon, side="right") - 1)
    probability = 1.0 if index < 0 else float(survival[index])
    return float(np.clip(1.0 - probability, 0.0, 1.0))


def fit_predict_survival_model(
    model_id: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_eval: np.ndarray,
    horizon: float,
    random_state: int,
    config: Mapping[str, object],
) -> SurvivalPrediction:
    """Fit one prespecified model and return ranking plus horizon-risk predictions."""
    if len(y_train) != len(x_train):
        raise ValueError("x_train and y_train lengths differ")
    if model_id == "B0" or (model_id == "M0" and x_train.shape[1] == 0):
        if model_id == "M0":
            warnings.warn(
                "M0 reduced to the Kaplan-Meier baseline because no missingness indicator varied",
                UserWarning,
                stacklevel=2,
            )
        risk = _km_risk(y_train, horizon)
        return SurvivalPrediction(
            risk_score=np.full(len(x_eval), risk, dtype=float),
            risk_horizon=np.full(len(x_eval), risk, dtype=float),
        )
    if x_train.ndim != 2 or x_train.shape[1] == 0:
        raise ValueError(f"{model_id} requires at least one feature")

    if model_id == "B1":
        model = CoxPHSurvivalAnalysis(
            alpha=float(config.get("coxph_alpha", 0.01)),
            n_iter=int(config.get("coxph_n_iter", 1000)),
        )
    elif model_id in {"B2", "B4", "B5", "M0", "N0"}:
        model = CoxnetSurvivalAnalysis(
            alphas=[float(config.get("coxnet_alpha", 0.05))],
            l1_ratio=float(config.get("coxnet_l1_ratio", 0.5)),
            max_iter=int(config.get("coxnet_max_iter", 100000)),
            fit_baseline_model=True,
            normalize=False,
        )
    elif model_id == "B3":
        model = RandomSurvivalForest(
            n_estimators=int(config.get("rsf_n_estimators", 200)),
            min_samples_leaf=int(config.get("rsf_min_samples_leaf", 10)),
            max_features=config.get("rsf_max_features", "sqrt"),
            n_jobs=1,
            random_state=int(random_state),
        )
    else:
        raise ValueError(f"unsupported baseline model: {model_id}")

    model.fit(np.asarray(x_train, dtype=float), y_train)
    risk_score = np.asarray(model.predict(np.asarray(x_eval, dtype=float)), dtype=float)
    risk_horizon = _survival_risk_at_horizon(model, np.asarray(x_eval, dtype=float), horizon)
    return SurvivalPrediction(risk_score=risk_score, risk_horizon=risk_horizon)
