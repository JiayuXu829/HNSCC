"""Prespecified Phase 5 reliability-score ablations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

CLINICAL_COMPONENTS = (
    "clinical_ood_rank",
    "rank_clinical_uncertainty_sd",
    "rank_clinical_model_disagreement",
)
MODALITY_COMPONENTS = (
    "modality_ood_rank",
    "rank_fusion_uncertainty_sd",
    "rank_perturbation_sensitivity",
    "rank_modality_missingness",
    "rank_fusion_disagreement",
)


def weighted_score(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    local_weights = np.asarray(weights, dtype=float)
    if matrix.ndim != 2 or local_weights.ndim != 1 or matrix.shape[1] != len(local_weights):
        raise ValueError("weighted score shapes are incompatible")
    if not np.isfinite(matrix).all() or not np.isfinite(local_weights).all():
        raise ValueError("weighted score requires finite inputs")
    if (local_weights < 0).any() or float(local_weights.sum()) <= 0:
        raise ValueError("weights must be nonnegative with positive sum")
    normalized = local_weights / local_weights.sum()
    return np.clip(matrix @ normalized, 0.0, 1.0)


def _column(frame: pd.DataFrame, name: str) -> np.ndarray:
    aliases = {
        "rank_fusion_uncertainty_sd": ("rank_modality_uncertainty_sd",),
    }
    if name in frame:
        return frame[name].to_numpy(dtype=float)
    for alias in aliases.get(name, ()):
        if alias in frame:
            return frame[alias].to_numpy(dtype=float)
    raise KeyError(name)


def component_matrix(frame: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    return np.column_stack([_column(frame, column) for column in columns])


def ablated_unreliability(
    frame: pd.DataFrame,
    variant: str,
    learned_weights: Mapping[str, np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return clinical and modality unreliability for a frozen gate variant."""
    if variant == "full_equal_weight":
        return (
            component_matrix(frame, CLINICAL_COMPONENTS).mean(axis=1),
            component_matrix(frame, MODALITY_COMPONENTS).mean(axis=1),
        )
    if variant == "ood_only":
        return _column(frame, "clinical_ood_rank"), _column(frame, "modality_ood_rank")
    if variant == "uncertainty_only":
        return (
            _column(frame, "rank_clinical_uncertainty_sd"),
            _column(frame, "rank_fusion_uncertainty_sd"),
        )
    if variant == "full_learned_nonnegative":
        if learned_weights is None:
            raise ValueError("learned gate requires frozen training-derived weights")
        return (
            weighted_score(
                component_matrix(frame, CLINICAL_COMPONENTS),
                np.asarray(learned_weights["clinical"], dtype=float),
            ),
            weighted_score(
                component_matrix(frame, MODALITY_COMPONENTS),
                np.asarray(learned_weights["modality"], dtype=float),
            ),
        )
    raise ValueError(f"unsupported gate ablation: {variant}")
