"""Versioned Phase 2 patient-level contract and split utilities."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable, Protocol

from trust_hn.data.contracts import DataContractError


class CohortRole(str, Enum):
    DEVELOPMENT = "development"
    HELD_OUT = "held_out"
    EXTERNAL = "external"
    SENSITIVITY = "sensitivity"


class SplitRole(str, Enum):
    TRAIN = "train"
    CALIBRATION = "calibration"
    SEALED_TEST = "sealed_test"
    EXTERNAL_TEST = "external_test"
    SENSITIVITY = "sensitivity"
    EXCLUDED = "excluded"


class EndpointStatus(str, Enum):
    USABLE = "usable"
    EARLY_CENSORED = "early_censored"
    SEALED = "sealed"
    UNRESOLVED = "unresolved"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class PatientRecord:
    study: str
    cohort_role: CohortRole
    native_id: str
    split_role: SplitRole
    eligible: bool
    exclusion_reason: str | None
    index_date_definition: str
    duration_days: float | None
    event: int | None
    endpoint_name: str
    endpoint_status: EndpointStatus
    age: float | None
    sex: str | None
    site: str | None
    stage: str | None
    hpv: str | None
    treatment: str | None
    clinical_features_available: bool
    modality_features_available: bool
    source_row_number: int
    provenance: tuple[str, ...]
    age_group: str | None = None
    smoking: str | None = None

    def to_private_dict(self) -> dict[str, object]:
        values = asdict(self)
        values["cohort_role"] = self.cohort_role.value
        values["split_role"] = self.split_role.value
        values["endpoint_status"] = self.endpoint_status.value
        values["provenance"] = " | ".join(self.provenance)
        return values

    def to_public_dict(self) -> dict[str, object]:
        values = self.to_private_dict()
        values.pop("native_id")
        values.pop("source_row_number")
        return values


@dataclass(frozen=True)
class ValidationReport:
    study: str
    records: int
    eligible: int
    sealed: int
    endpoint_usable: int


class DatasetAdapter(Protocol):
    study: str

    def load_records(self) -> list[PatientRecord]: ...

    def source_paths(self) -> tuple[object, ...]: ...


def deterministic_development_split(
    native_ids: Iterable[str], calibration_fraction: float, salt: str
) -> dict[str, SplitRole]:
    """Create an exact-size, order-invariant split using IDs only, never outcomes."""
    if not 0 <= calibration_fraction < 1:
        raise DataContractError("calibration_fraction must be in [0, 1)")
    ids = [str(value) for value in native_ids]
    if len(ids) != len(set(ids)):
        raise DataContractError("native_ids must be unique before deterministic splitting")
    ranked = sorted(
        ids,
        key=lambda value: hashlib.sha256(f"{salt}\0{value}".encode("utf-8")).hexdigest(),
    )
    n_calibration = int(len(ranked) * calibration_fraction)
    if calibration_fraction > 0 and len(ranked) > 1:
        n_calibration = max(1, n_calibration)
    calibration = set(ranked[:n_calibration])
    return {
        native_id: (
            SplitRole.CALIBRATION if native_id in calibration else SplitRole.TRAIN
        )
        for native_id in ids
    }


def validate_patient_records(records: Iterable[PatientRecord]) -> ValidationReport:
    rows = list(records)
    if not rows:
        raise DataContractError("adapter returned no records")
    studies = {row.study for row in rows}
    if len(studies) != 1:
        raise DataContractError(f"validation requires one study at a time: {sorted(studies)}")
    seen: set[str] = set()
    for row in rows:
        if not row.study or not row.native_id:
            raise DataContractError("study and native_id must be non-empty")
        if row.native_id in seen:
            raise DataContractError(f"duplicate native_id in {row.study}: {row.native_id}")
        seen.add(row.native_id)
        if row.source_row_number < 1:
            raise DataContractError("source_row_number must be positive")
        if row.event not in (None, 0, 1):
            raise DataContractError(f"invalid event for {row.native_id}")
        if row.duration_days is not None and row.duration_days < 0:
            raise DataContractError(f"negative duration for {row.native_id}")
        if (row.duration_days is None) != (row.event is None):
            raise DataContractError(f"duration/event must be jointly present or absent: {row.native_id}")
        if row.endpoint_status == EndpointStatus.SEALED and (
            row.duration_days is not None or row.event is not None
        ):
            raise DataContractError(f"sealed outcome exposed for {row.native_id}")
        if row.split_role in {SplitRole.SEALED_TEST, SplitRole.EXTERNAL_TEST} and (
            row.duration_days is not None or row.event is not None
        ):
            raise DataContractError(f"test/external outcome exposed for {row.native_id}")
        if row.eligible and row.exclusion_reason is not None:
            raise DataContractError(f"eligible row has exclusion_reason: {row.native_id}")
        if not row.eligible and not row.exclusion_reason:
            raise DataContractError(f"excluded row lacks reason: {row.native_id}")
    return ValidationReport(
        study=next(iter(studies)),
        records=len(rows),
        eligible=sum(row.eligible for row in rows),
        sealed=sum(row.endpoint_status == EndpointStatus.SEALED for row in rows),
        endpoint_usable=sum(row.endpoint_status == EndpointStatus.USABLE for row in rows),
    )
