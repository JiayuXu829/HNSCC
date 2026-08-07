"""RADCURE Phase 2 clinical adapter.

Radiomics remain unavailable until the ORCESTRA RDS structure is validated.
Challenge-test outcomes are never materialized by this adapter.
"""

from __future__ import annotations

import csv
from pathlib import Path

from trust_hn.data.contracts_v2 import (
    CohortRole,
    EndpointStatus,
    PatientRecord,
    SplitRole,
    deterministic_development_split,
)


def _optional(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _float_or_none(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def derive_treatment_start_os(
    rt_start: str, last_follow_up: str, status: str, date_of_death: str
) -> tuple[float, int]:
    """Derive OS from first RT fraction to last contact/death.

    Last FU is the source-defined last contact or death date. Date of Death is
    checked for consistency by the audit but is not substituted, avoiding mixed
    time origins. Excel serial dates remain valid under subtraction.
    """
    start = float(rt_start)
    last = float(last_follow_up)
    duration = last - start
    if duration < 0:
        raise ValueError("Last FU precedes RT Start")
    normalized = status.strip().casefold()
    if normalized not in {"alive", "dead"}:
        raise ValueError(f"unrecognized RADCURE status: {status!r}")
    if normalized == "dead" and date_of_death.strip():
        float(date_of_death)
    return duration, int(normalized == "dead")


class RadcureAdapter:
    study = "RADCURE"

    def __init__(self, project_root: Path, calibration_fraction: float = 0.20):
        self.project_root = Path(project_root)
        self.calibration_fraction = calibration_fraction
        self.clinical_path = self.project_root / (
            "data/interim/radcure/v04_20241219/clinical_csv/"
            "01_RADCURE_TCIA_Clinical_r2_offset.csv"
        )

    def source_paths(self) -> tuple[Path, ...]:
        return (self.clinical_path,)

    def load_records(self) -> list[PatientRecord]:
        with self.clinical_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        development_ids = [
            row["patient_id"].strip()
            for row in rows
            if row["Path"].strip().casefold() == "squamous cell carcinoma"
            and row["RADCURE-challenge"].strip() == "training"
        ]
        development_split = deterministic_development_split(
            development_ids, self.calibration_fraction, "TRUST-HN:RADCURE:phase2:v1"
        )
        records: list[PatientRecord] = []
        for row_number, row in enumerate(rows, start=2):
            native_id = row["patient_id"].strip()
            exact_scc = row["Path"].strip().casefold() == "squamous cell carcinoma"
            official = row["RADCURE-challenge"].strip()
            exclusion_reason: str | None = None
            eligible = exact_scc and official in {"training", "test"}
            if not exact_scc:
                exclusion_reason = "histology_not_normalized_exact_invasive_scc"
            elif official == "0":
                exclusion_reason = "outside_primary_challenge_split"
            elif official not in {"training", "test"}:
                exclusion_reason = "unrecognized_challenge_split"

            if eligible and official == "training":
                split_role = development_split[native_id]
                cohort_role = CohortRole.DEVELOPMENT
                duration, event = derive_treatment_start_os(
                    row["RT Start"], row["Last FU"], row["Status"], row["Date of Death"]
                )
                endpoint_status = EndpointStatus.USABLE
            elif eligible and official == "test":
                split_role = SplitRole.SEALED_TEST
                cohort_role = CohortRole.HELD_OUT
                duration = event = None
                endpoint_status = EndpointStatus.SEALED
            else:
                split_role = SplitRole.EXCLUDED
                cohort_role = CohortRole.DEVELOPMENT if official != "test" else CohortRole.HELD_OUT
                duration = event = None
                endpoint_status = EndpointStatus.NOT_APPLICABLE

            records.append(
                PatientRecord(
                    study=self.study,
                    cohort_role=cohort_role,
                    native_id=native_id,
                    split_role=split_role,
                    eligible=eligible,
                    exclusion_reason=exclusion_reason,
                    index_date_definition="first_radiotherapy_fraction",
                    duration_days=duration,
                    event=event,
                    endpoint_name="overall_survival",
                    endpoint_status=endpoint_status,
                    age=_float_or_none(row.get("Age")),
                    sex=_optional(row.get("Sex")),
                    site=_optional(row.get("Ds Site")),
                    stage=_optional(row.get("Stage")),
                    hpv=_optional(row.get("HPV")),
                    treatment=_optional(row.get("Tx Modality")),
                    clinical_features_available=True,
                    modality_features_available=False,
                    source_row_number=row_number,
                    provenance=(
                        self.clinical_path.relative_to(self.project_root).as_posix(),
                        "ORCESTRA RDS intentionally unavailable pending structural audit",
                    ),
                    smoking=_optional(row.get("Smoking Status")),
                )
            )
        return records
