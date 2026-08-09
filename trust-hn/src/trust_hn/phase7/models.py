"""Independent Phase 7 survival comparators.

These models are deliberately isolated from frozen Phase 3--6 implementation files.
All feature preprocessing is fitted on the supplied training rows only.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sksurv.ensemble import GradientBoostingSurvivalAnalysis
from sksurv.linear_model import CoxnetSurvivalAnalysis, CoxPHSurvivalAnalysis
from xgboost import XGBRegressor

from trust_hn.evaluation.phase3 import NumericMatrixPreprocessor, _infer_columns
from trust_hn.models.survival_baselines import (
    SurvivalPrediction,
    TabularPreprocessor,
    _survival_risk_at_horizon,
)


@dataclass(frozen=True)
class FeatureBlocks:
    """Aligned clinical, modality, and explicit-missingness feature blocks."""

    clinical: np.ndarray
    modality: np.ndarray
    missing_aware: np.ndarray

    def __post_init__(self) -> None:
        sizes = {len(self.clinical), len(self.modality), len(self.missing_aware)}
        if len(sizes) != 1:
            raise ValueError("Phase 7 feature blocks have inconsistent row counts")
        for values in (self.clinical, self.modality, self.missing_aware):
            if values.ndim != 2 or not np.isfinite(values).all():
                raise ValueError("Phase 7 feature blocks must be finite two-dimensional arrays")


class Phase7FeaturePreprocessor:
    """Training-only preprocessing shared by all Phase 7 comparators."""

    HIGH_DIMENSIONAL_STUDIES: ClassVar[set[str]] = {"RADCURE", "TCGA-HNSC"}
    MISSING_TOKENS: ClassVar[set[str]] = {
        "",
        "unknown",
        "not reported",
        "not tested",
        "na",
        "n/a",
        "nan",
        "none",
    }

    def __init__(self, study: str, *, top_k: int = 500):
        self.study = study.strip().upper().replace("_", "-")
        self.top_k = int(top_k)
        self.clinical_preprocessor: TabularPreprocessor | None = None
        self.modality_preprocessor: TabularPreprocessor | NumericMatrixPreprocessor | None = None
        self.missing_columns_: np.ndarray | None = None
        self.fitted_ = False

    @classmethod
    def _missingness(cls, frame: pd.DataFrame) -> np.ndarray:
        columns: list[np.ndarray] = []
        for column in frame.columns:
            series = frame[column]
            missing = series.isna().to_numpy()
            if not pd.api.types.is_numeric_dtype(series):
                text = series.astype("string").str.strip().str.casefold()
                missing |= text.isin(cls.MISSING_TOKENS).fillna(True).to_numpy()
            columns.append(missing.astype(float))
        if not columns:
            return np.zeros((len(frame), 0), dtype=float)
        return np.column_stack(columns)

    def fit(self, clinical: pd.DataFrame, modality: pd.DataFrame) -> Phase7FeaturePreprocessor:
        if len(clinical) != len(modality):
            raise ValueError("clinical and modality training rows differ")
        clinical_numeric, clinical_categorical = _infer_columns(clinical, self.study)
        self.clinical_preprocessor = TabularPreprocessor(
            clinical_numeric, clinical_categorical
        ).fit(clinical)
        if self.study in self.HIGH_DIMENSIONAL_STUDIES:
            self.modality_preprocessor = NumericMatrixPreprocessor(top_k=self.top_k).fit(modality)
        else:
            modality_numeric, modality_categorical = _infer_columns(modality, self.study)
            self.modality_preprocessor = TabularPreprocessor(
                modality_numeric, modality_categorical
            ).fit(modality)
        missing = self._missingness(modality)
        if missing.shape[1]:
            varying = np.flatnonzero(np.var(missing, axis=0) > 1e-12)
        else:
            varying = np.zeros(0, dtype=int)
        self.missing_columns_ = varying
        self.fitted_ = True
        return self

    def transform(self, clinical: pd.DataFrame, modality: pd.DataFrame) -> FeatureBlocks:
        if (
            not self.fitted_
            or self.clinical_preprocessor is None
            or self.modality_preprocessor is None
            or self.missing_columns_ is None
        ):
            raise RuntimeError("Phase 7 preprocessor must be fitted before transform")
        if len(clinical) != len(modality):
            raise ValueError("clinical and modality evaluation rows differ")
        clinical_matrix = self.clinical_preprocessor.transform(clinical)
        modality_matrix = self.modality_preprocessor.transform(modality)
        raw_missing = self._missingness(modality)
        if raw_missing.shape[1] < len(self.missing_columns_):
            raise ValueError("modality feature count changed between fit and transform")
        selected_missing = raw_missing[:, self.missing_columns_]
        missing_fraction = raw_missing.mean(axis=1, keepdims=True)
        fully_missing = (missing_fraction >= 1.0 - 1e-12).astype(float)
        missing_aware = np.column_stack(
            [modality_matrix, selected_missing, missing_fraction, fully_missing]
        )
        return FeatureBlocks(
            clinical=np.asarray(clinical_matrix, dtype=float),
            modality=np.asarray(modality_matrix, dtype=float),
            missing_aware=np.asarray(missing_aware, dtype=float),
        )

    def fit_transform(self, clinical: pd.DataFrame, modality: pd.DataFrame) -> FeatureBlocks:
        return self.fit(clinical, modality).transform(clinical, modality)


def encode_xgb_cox_labels(event: np.ndarray, time: np.ndarray) -> np.ndarray:
    """Encode events as positive and right-censoring as negative survival times."""

    event_array = np.asarray(event, dtype=bool)
    time_array = np.asarray(time, dtype=float)
    if event_array.shape != time_array.shape:
        raise ValueError("event and time arrays must have identical shapes")
    if not np.isfinite(time_array).all() or np.any(time_array <= 0):
        raise ValueError("XGBoost-Cox requires finite positive survival times")
    return np.where(event_array, time_array, -time_array)


def breslow_risk_at_horizon(
    train_event: np.ndarray,
    train_time: np.ndarray,
    train_margin: np.ndarray,
    eval_margin: np.ndarray,
    horizon: float,
) -> np.ndarray:
    """Convert Cox margins to absolute horizon risk using a training-only Breslow hazard."""

    event = np.asarray(train_event, dtype=bool)
    time = np.asarray(train_time, dtype=float)
    margin = np.asarray(train_margin, dtype=float)
    evaluation = np.asarray(eval_margin, dtype=float)
    if not (event.shape == time.shape == margin.shape):
        raise ValueError("training arrays must have identical shapes")
    if not np.isfinite(time).all() or not np.isfinite(margin).all():
        raise ValueError("Breslow inputs must be finite")
    event_times = np.unique(time[event & (time <= float(horizon))])
    cumulative_hazard = 0.0
    relative_hazard = np.exp(np.clip(margin, -30.0, 30.0))
    for event_time in event_times:
        deaths = int(np.sum(event & np.isclose(time, event_time, rtol=0.0, atol=1e-10)))
        denominator = float(np.sum(relative_hazard[time >= event_time]))
        if deaths and denominator > 0.0:
            cumulative_hazard += deaths / denominator
    eval_hazard = np.exp(np.clip(evaluation, -30.0, 30.0))
    risk = 1.0 - np.exp(-cumulative_hazard * eval_hazard)
    return np.clip(risk, 0.0, 1.0)


def _coxnet(config: Mapping[str, object]) -> CoxnetSurvivalAnalysis:
    return CoxnetSurvivalAnalysis(
        alphas=[float(config.get("coxnet_alpha", 0.05))],
        l1_ratio=float(config.get("coxnet_l1_ratio", 0.5)),
        max_iter=int(config.get("coxnet_max_iter", 100000)),
        fit_baseline_model=True,
        normalize=False,
    )


def _late_fusion_prediction(
    train: FeatureBlocks,
    outcome: np.ndarray,
    evaluation: FeatureBlocks,
    horizon: float,
    random_state: int,
    config: Mapping[str, object],
) -> SurvivalPrediction:
    event = np.asarray(outcome["event"], dtype=bool)
    requested_folds = int(config.get("cv_folds", 5))
    minority = int(min(np.sum(event), np.sum(~event)))
    folds = min(requested_folds, minority)
    if folds < 2:
        raise ValueError("late fusion requires at least two events and two censored observations")
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=int(random_state))
    clinical_oof = np.full(len(outcome), np.nan, dtype=float)
    modality_oof = np.full(len(outcome), np.nan, dtype=float)
    for fit_indices, validation_indices in splitter.split(train.clinical, event.astype(int)):
        clinical_model = _coxnet(config).fit(train.clinical[fit_indices], outcome[fit_indices])
        modality_model = _coxnet(config).fit(train.modality[fit_indices], outcome[fit_indices])
        clinical_oof[validation_indices] = clinical_model.predict(
            train.clinical[validation_indices]
        )
        modality_oof[validation_indices] = modality_model.predict(
            train.modality[validation_indices]
        )
    if not np.isfinite(clinical_oof).all() or not np.isfinite(modality_oof).all():
        raise RuntimeError("late-fusion cross-fitted base predictions are incomplete")
    meta_train = np.column_stack([clinical_oof, modality_oof])
    meta_model = CoxPHSurvivalAnalysis(
        alpha=float(config.get("late_fusion_meta_alpha", 0.01)), n_iter=1000
    ).fit(meta_train, outcome)
    clinical_full = _coxnet(config).fit(train.clinical, outcome)
    modality_full = _coxnet(config).fit(train.modality, outcome)
    meta_eval = np.column_stack(
        [clinical_full.predict(evaluation.clinical), modality_full.predict(evaluation.modality)]
    )
    score = np.asarray(meta_model.predict(meta_eval), dtype=float)
    risk = _survival_risk_at_horizon(meta_model, meta_eval, horizon)
    return SurvivalPrediction(score, risk)


def fit_predict_phase7_model(
    model_id: str,
    train: FeatureBlocks,
    outcome: np.ndarray,
    evaluation: FeatureBlocks,
    horizon: float,
    random_state: int,
    config: Mapping[str, object],
) -> SurvivalPrediction:
    """Fit one frozen Phase 7 comparator and return score and absolute horizon risk."""

    if len(outcome) != len(train.clinical):
        raise ValueError("training outcomes and features differ in length")
    model_id = model_id.strip().upper()
    fused_train = np.column_stack([train.clinical, train.modality])
    fused_eval = np.column_stack([evaluation.clinical, evaluation.modality])

    if model_id == "C1":
        model = GradientBoostingSurvivalAnalysis(
            loss="coxph",
            learning_rate=float(config.get("gbsa_learning_rate", 0.05)),
            n_estimators=int(config.get("gbsa_n_estimators", 150)),
            max_depth=int(config.get("gbsa_max_depth", 2)),
            min_samples_leaf=int(config.get("gbsa_min_samples_leaf", 10)),
            max_features=config.get("gbsa_max_features", "sqrt"),
            random_state=int(random_state),
        ).fit(fused_train, outcome)
        score = np.asarray(model.predict(fused_eval), dtype=float)
        risk = _survival_risk_at_horizon(model, fused_eval, horizon)
    elif model_id == "C2":
        labels = encode_xgb_cox_labels(outcome["event"], outcome["time"])
        model = XGBRegressor(
            objective="survival:cox",
            n_estimators=int(config.get("xgb_n_estimators", 200)),
            learning_rate=float(config.get("xgb_learning_rate", 0.03)),
            max_depth=int(config.get("xgb_max_depth", 3)),
            min_child_weight=float(config.get("xgb_min_child_weight", 5.0)),
            subsample=float(config.get("xgb_subsample", 0.8)),
            colsample_bytree=float(config.get("xgb_colsample_bytree", 0.8)),
            reg_alpha=float(config.get("xgb_reg_alpha", 0.05)),
            reg_lambda=float(config.get("xgb_reg_lambda", 1.0)),
            tree_method=str(config.get("xgb_tree_method", "hist")),
            n_jobs=int(config.get("xgb_n_jobs", 1)),
            random_state=int(random_state),
        ).fit(fused_train, labels, verbose=False)
        train_margin = np.asarray(model.predict(fused_train, output_margin=True), dtype=float)
        score = np.asarray(model.predict(fused_eval, output_margin=True), dtype=float)
        risk = breslow_risk_at_horizon(
            outcome["event"], outcome["time"], train_margin, score, horizon
        )
    elif model_id == "C3":
        return _late_fusion_prediction(train, outcome, evaluation, horizon, random_state, config)
    elif model_id == "C4":
        missing_train = np.column_stack([train.clinical, train.missing_aware])
        missing_eval = np.column_stack([evaluation.clinical, evaluation.missing_aware])
        model = _coxnet(config).fit(missing_train, outcome)
        score = np.asarray(model.predict(missing_eval), dtype=float)
        risk = _survival_risk_at_horizon(model, missing_eval, horizon)
    else:
        raise ValueError(f"unsupported Phase 7 comparator: {model_id}")

    if not np.isfinite(score).all() or not np.isfinite(risk).all():
        raise RuntimeError(f"{model_id} produced non-finite predictions")
    return SurvivalPrediction(np.asarray(score, dtype=float), np.clip(risk, 0.0, 1.0))
