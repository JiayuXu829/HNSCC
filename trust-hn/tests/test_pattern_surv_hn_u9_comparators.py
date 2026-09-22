from __future__ import annotations

import numpy as np
import torch

from trust_hn.pattern_surv_hn.u9_published_comparators import (
    _discrete_targets,
    _hazard_nll,
    _time_grid,
)


def test_time_grid_and_targets_are_bounded() -> None:
    duration = np.asarray([1, 2, 3, 4, 5, 6], dtype=float)
    edges = _time_grid(duration, 4)
    targets = _discrete_targets(duration, edges)
    assert len(edges) >= 3
    assert targets.min() == 0
    assert targets.max() == len(edges) - 1


def test_multisurv_hazard_nll_is_finite() -> None:
    logits = torch.zeros((4, 3), dtype=torch.float64, requires_grad=True)
    bins = torch.tensor([0, 1, 2, 2], dtype=torch.long)
    event = torch.tensor([True, False, True, False])
    loss = _hazard_nll(logits, bins, event)
    loss.backward()
    assert torch.isfinite(loss)
    assert torch.isfinite(logits.grad).all()
