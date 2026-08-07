"""Outcome-free reliability indicators and Phase 4 gate utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.covariance import LedoitWolf
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

Action = Literal["AUGMENT", "FALLBACK", "ABSTAIN"]


@dataclass(frozen=True)
class OODResult:
    mahalanobis: np.ndarray
    knn: np.ndarray
    isolation_forest: np.ndarray


class TripleOODDetector:
    """Three prespecified outcome-free OOD detectors on a training-derived embedding."""

    def __init__(
        self,
        *,
        n_neighbors: int = 10,
        isolation_estimators: int = 200,
        max_features: int = 50,
        random_state: int = 17,
    ) -> None:
        self.n_neighbors = int(n_neighbors)
        self.isolation_estimators = int(isolation_estimators)
        self.max_features = int(max_features)
        self.random_state = int(random_state)
        self.scaler_: StandardScaler | None = None
        self.pca_: PCA | None = None
        self.covariance_: LedoitWolf | None = None
        self.neighbors_: NearestNeighbors | None = None
        self.isolation_: IsolationForest | None = None

    @staticmethod
    def _matrix(values: np.ndarray) -> np.ndarray:
        matrix = np.asarray(values, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
            raise ValueError("OOD detector requires a two-dimensional nonempty matrix")
        if not np.isfinite(matrix).all():
            raise ValueError("OOD detector received non-finite values")
        return matrix

    def fit(self, values: np.ndarray) -> TripleOODDetector:
        matrix = self._matrix(values)
        self.scaler_ = StandardScaler().fit(matrix)
        scaled = self.scaler_.transform(matrix)
        components = min(self.max_features, scaled.shape[1], scaled.shape[0] - 1)
        if components < scaled.shape[1]:
            self.pca_ = PCA(n_components=components, svd_solver="full").fit(scaled)
            embedded = self.pca_.transform(scaled)
        else:
            self.pca_ = None
            embedded = scaled
        self.covariance_ = LedoitWolf().fit(embedded)
        neighbors = min(max(2, self.n_neighbors), len(embedded))
        self.neighbors_ = NearestNeighbors(n_neighbors=neighbors).fit(embedded)
        self.isolation_ = IsolationForest(
            n_estimators=self.isolation_estimators,
            contamination="auto",
            random_state=self.random_state,
            n_jobs=1,
        ).fit(embedded)
        return self

    def _embed(self, values: np.ndarray) -> np.ndarray:
        if (
            self.scaler_ is None
            or self.covariance_ is None
            or self.neighbors_ is None
            or self.isolation_ is None
        ):
            raise RuntimeError("OOD detector must be fitted before scoring")
        matrix = np.asarray(values, dtype=float)
        if matrix.ndim != 2 or not np.isfinite(matrix).all():
            raise ValueError("OOD scoring requires a finite two-dimensional matrix")
        scaled = self.scaler_.transform(matrix)
        return self.pca_.transform(scaled) if self.pca_ is not None else scaled

    def score(self, values: np.ndarray) -> OODResult:
        embedded = self._embed(values)
        assert self.covariance_ is not None
        assert self.neighbors_ is not None
        assert self.isolation_ is not None
        squared = self.covariance_.mahalanobis(embedded)
        distances, _ = self.neighbors_.kneighbors(embedded)
        return OODResult(
            mahalanobis=np.sqrt(np.maximum(squared, 0.0)),
            knn=np.mean(distances, axis=1),
            isolation_forest=-self.isolation_.score_samples(embedded),
        )


def empirical_percentile(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Map high-is-unreliable raw values to calibration-referenced percentiles."""
    values = np.asarray(values, dtype=float)
    reference = np.asarray(reference, dtype=float)
    reference = reference[np.isfinite(reference)]
    if reference.size == 0:
        raise ValueError("rank reference has no finite values")
    ordered = np.sort(reference)
    if ordered[0] == ordered[-1]:
        return np.where(values > ordered[0], 1.0, 0.0)
    ranks = np.searchsorted(ordered, values, side="right") / float(len(ordered))
    return np.clip(ranks, 0.0, 1.0)


def equal_weight_score(*components: np.ndarray) -> np.ndarray:
    if not components:
        raise ValueError("at least one reliability component is required")
    arrays = [np.asarray(component, dtype=float) for component in components]
    if len({array.shape for array in arrays}) != 1:
        raise ValueError("reliability components must have identical shapes")
    matrix = np.column_stack(arrays)
    if not np.isfinite(matrix).all():
        raise ValueError("reliability components must be finite")
    return np.mean(matrix, axis=1)


def quantile_threshold(values: np.ndarray, target_coverage: float) -> float:
    if not 0.0 < target_coverage <= 1.0:
        raise ValueError("target coverage must be in (0, 1]")
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all() or values.size == 0:
        raise ValueError("threshold values must be finite and nonempty")
    return float(np.quantile(values, target_coverage, method="higher"))


def assign_actions(
    clinical_unreliability: np.ndarray,
    modality_unreliability: np.ndarray,
    modality_missing: np.ndarray,
    *,
    clinical_threshold: float,
    modality_threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the prespecified ABSTAIN > FALLBACK > AUGMENT precedence."""
    clinical = np.asarray(clinical_unreliability, dtype=float)
    modality = np.asarray(modality_unreliability, dtype=float)
    missing = np.asarray(modality_missing, dtype=bool)
    if clinical.shape != modality.shape or clinical.shape != missing.shape:
        raise ValueError("gate inputs must have identical shapes")
    actions = np.full(clinical.shape, "AUGMENT", dtype="U8")
    reasons = np.full(clinical.shape, "modality_reliable", dtype="U32")
    fallback = missing | (modality > modality_threshold)
    actions[fallback] = "FALLBACK"
    reasons[missing] = "modality_missing"
    reasons[(~missing) & fallback] = "modality_unreliable"
    abstain = clinical > clinical_threshold
    actions[abstain] = "ABSTAIN"
    reasons[abstain] = "clinical_unreliable"
    return actions, reasons


def gated_risk(
    anchor_risk: np.ndarray, augmented_risk: np.ndarray, actions: np.ndarray
) -> np.ndarray:
    anchor = np.asarray(anchor_risk, dtype=float)
    augmented = np.asarray(augmented_risk, dtype=float)
    actions = np.asarray(actions)
    if anchor.shape != augmented.shape or anchor.shape != actions.shape:
        raise ValueError("risk and action arrays must have identical shapes")
    final = augmented.copy()
    final[actions == "FALLBACK"] = anchor[actions == "FALLBACK"]
    final[actions == "ABSTAIN"] = np.nan
    return final
