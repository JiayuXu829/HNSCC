"""Endpoint construction with explicit censoring semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HorizonStatus(str, Enum):
    EVENT_BY_HORIZON = "event_by_horizon"
    EVENT_FREE_AT_HORIZON = "event_free_at_horizon"
    CENSORED_BEFORE_HORIZON = "censored_before_horizon"


@dataclass(frozen=True)
class HorizonOutcome:
    status: HorizonStatus
    binary_label: int | None
    evaluable_as_binary: bool


def classify_horizon_outcome(
    duration_days: float,
    event: int,
    horizon_days: float = 730.5,
) -> HorizonOutcome:
    """Classify a time-to-event record at a horizon without mislabeling early censoring.

    Death/event on or before the horizon is positive. A person observed beyond the
    horizon is negative regardless of a later event. A non-event censored before
    the horizon has unknown binary status and must not be coded as negative.
    """
    if duration_days < 0:
        raise ValueError("duration_days must be non-negative")
    if event not in (0, 1):
        raise ValueError("event must be 0 or 1")
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive")

    if event == 1 and duration_days <= horizon_days:
        return HorizonOutcome(HorizonStatus.EVENT_BY_HORIZON, 1, True)
    if duration_days >= horizon_days:
        return HorizonOutcome(HorizonStatus.EVENT_FREE_AT_HORIZON, 0, True)
    return HorizonOutcome(HorizonStatus.CENSORED_BEFORE_HORIZON, None, False)