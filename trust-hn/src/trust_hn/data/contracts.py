"""Minimal patient-level data contracts independent of modeling libraries."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


class DataContractError(ValueError):
    """Raised when a dataset violates a prespecified patient-level contract."""


@dataclass(frozen=True)
class SurvivalRecord:
    patient_id: str
    duration_days: float
    event: int

    def validate(self) -> None:
        if not self.patient_id:
            raise DataContractError("patient_id must be non-empty")
        if self.duration_days < 0:
            raise DataContractError(f"negative survival time for {self.patient_id}")
        if self.event not in (0, 1):
            raise DataContractError(f"event must be 0/1 for {self.patient_id}")


def validate_survival_records(records: Iterable[SurvivalRecord]) -> None:
    seen: set[str] = set()
    for record in records:
        record.validate()
        if record.patient_id in seen:
            raise DataContractError(f"duplicate patient_id: {record.patient_id}")
        seen.add(record.patient_id)


def assert_patient_splits_disjoint(splits: Mapping[str, Iterable[str]]) -> None:
    """Ensure no patient occurs in more than one split."""
    owners: dict[str, str] = {}
    for split_name, patient_ids in splits.items():
        for patient_id in patient_ids:
            patient_id = str(patient_id)
            previous = owners.get(patient_id)
            if previous is not None and previous != split_name:
                raise DataContractError(
                    f"patient {patient_id!r} occurs in both {previous!r} and {split_name!r}"
                )
            owners[patient_id] = split_name


def assert_samples_do_not_cross_splits(
    patient_ids: Sequence[str], sample_splits: Sequence[str]
) -> None:
    """Ensure multiple samples belonging to one patient stay in one split."""
    if len(patient_ids) != len(sample_splits):
        raise DataContractError("patient_ids and sample_splits have different lengths")
    observed: dict[str, set[str]] = {}
    for patient_id, split in zip(patient_ids, sample_splits, strict=True):
        observed.setdefault(str(patient_id), set()).add(str(split))
    offenders = {patient: sorted(splits) for patient, splits in observed.items() if len(splits) > 1}
    if offenders:
        raise DataContractError(f"multi-sample patients cross splits: {offenders}")


def split_counts(splits: Mapping[str, Iterable[str]]) -> dict[str, int]:
    return {name: len(list(patient_ids)) for name, patient_ids in splits.items()}


def duplicate_counts(values: Iterable[str]) -> dict[str, int]:
    return {key: count for key, count in Counter(values).items() if count > 1}