"""Stacked residual survival learner used by TRUST-HN Phase 4."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from sksurv.linear_model import CoxnetSurvivalAnalysis

from trust_hn.models.survival_baselines import SurvivalPrediction


@dataclass
class StackedResidualSurvivalModel:
    """Learn modality-associated residual risk conditional on a clinical anchor score."""

    config: Mapping[str, object]
    model_: CoxnetSurvivalAnalysis | None = None
    anchor_mean_: float = 0.0
    anchor_scale_: float = 1.0
    horizon_: float = 730.5

    def _design(self, anchor_score: np.ndarray, modality: np.ndarray) -> np.ndarray:
        anchor = np.asarray(anchor_score, dtype=float)
        features = np.asarray(modality, dtype=float)
        if anchor.ndim != 1 or features.ndim != 2 or len(anchor) != len(features):
            raise ValueError("anchor and modality shapes are incompatible")
        standardized = (anchor - self.anchor_mean_) / self.anchor_scale_
        matrix = np.column_stack([standardized, features])
        if not np.isfinite(matrix).all():
            raise ValueError("stacked residual design contains non-finite values")
        return matrix

    def fit(
        self,
        anchor_score: np.ndarray,
        modality: np.ndarray,
        outcome: np.ndarray,
        *,
        horizon: float,
    ) -> StackedResidualSurvivalModel:
        anchor = np.asarray(anchor_score, dtype=float)
        self.anchor_mean_ = float(np.mean(anchor))
        self.anchor_scale_ = float(np.std(anchor))
        if not np.isfinite(self.anchor_scale_) or self.anchor_scale_ < 1e-12:
            self.anchor_scale_ = 1.0
        self.horizon_ = float(horizon)
        design = self._design(anchor, modality)
        self.model_ = CoxnetSurvivalAnalysis(
            alphas=[float(self.config.get("coxnet_alpha", 0.05))],
            l1_ratio=float(self.config.get("coxnet_l1_ratio", 0.5)),
            max_iter=int(self.config.get("coxnet_max_iter", 100000)),
            fit_baseline_model=True,
            normalize=False,
        )
        self.model_.fit(design, outcome)
        return self

    def predict(self, anchor_score: np.ndarray, modality: np.ndarray) -> SurvivalPrediction:
        if self.model_ is None:
            raise RuntimeError("stacked residual model must be fitted")
        design = self._design(anchor_score, modality)
        risk_score = np.asarray(self.model_.predict(design), dtype=float)
        functions = self.model_.predict_survival_function(design)
        evaluation_time = min(self.horizon_, float(np.asarray(self.model_.unique_times_)[-1]))
        survival = np.asarray([float(function(evaluation_time)) for function in functions])
        risk_horizon = np.clip(1.0 - survival, 0.0, 1.0)
        return SurvivalPrediction(risk_score=risk_score, risk_horizon=risk_horizon)
