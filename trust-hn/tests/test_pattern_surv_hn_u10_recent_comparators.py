from __future__ import annotations

import numpy as np
import torch

from trust_hn.pattern_surv_hn.u10_recent_comparators import (
    _BilinearFusion,
    _EarlyFusion,
    _hazard_nll_rows,
    _HeterogeneousAlignedFusion,
    _MaskedAttentionFusion,
    _risks_from_logits,
    _RuffiniIntermediateFusion,
)


def test_recent_comparator_hazard_loss_is_finite() -> None:
    logits = torch.zeros((4, 3), dtype=torch.float64, requires_grad=True)
    bins = torch.tensor([0, 1, 2, 2], dtype=torch.long)
    event = torch.tensor([True, False, True, False])
    loss = _hazard_nll_rows(logits, bins, event).mean()
    loss.backward()
    assert torch.isfinite(loss)
    assert torch.isfinite(logits.grad).all()


def test_recent_comparator_forward_shapes_and_bounds() -> None:
    clinical = torch.zeros((5, 4), dtype=torch.float64)
    modalities = (
        torch.zeros((5, 3), dtype=torch.float64),
        torch.zeros((5, 2), dtype=torch.float64),
        torch.zeros((5, 6), dtype=torch.float64),
    )
    active = torch.tensor(
        [[True, True, True], [True, False, True], [False, False, False]] * 2,
        dtype=torch.bool,
    )[:5]
    dimensions = [4, 3, 2, 6]
    ruffini = _RuffiniIntermediateFusion(dimensions, 8, 4)
    haf = _HeterogeneousAlignedFusion(dimensions, 8, 6, 4)
    early = _EarlyFusion(dimensions, 8, 4)
    attention = _MaskedAttentionFusion(dimensions, 8, 4)
    bilinear = _BilinearFusion(dimensions, 8, 4)
    for model in (ruffini, haf, early, attention, bilinear):
        logits = model(clinical, modalities, active)
        assert logits.shape == (5, 4)
        score, risk = _risks_from_logits(logits, np.asarray([1, 2, 3, 4]), 2.5)
        assert score.shape == (5,)
        assert risk.shape == (5,)
        assert np.all((risk >= 0.0) & (risk <= 1.0))
