"""HANCOCK Phase 2 adapter using structured clinical/pathological data."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from trust_hn.data.contracts_v2 import (
    CohortRole,
    EndpointStatus,
    PatientRecord,
    SplitRole,
    deterministic_development_split,
)


def _by_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row["patient_id"]).strip(): row for row in rows}


def _optional(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _float_or_none(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _treatment_label(row: dict[str, object]) -> str:
    if str(row.get("adjuvant_radiochemotherapy", "")).casefold() == "yes":
        return "surgery + adjuvant radiochemotherapy"
    if str(row.get("adjuvant_radiotherapy", "")).casefold() == "yes":
        return "surgery + adjuvant radiotherapy"
    if str(row.get("adjuvant_systemic_therapy", "")).casefold() == "yes":
        return "surgery + adjuvant systemic therapy"
    return "surgery alone"


class HancockAdapter:
    study = "HANCOCK"

    def __init__(self, project_root: Path, calibration_fraction: float = 0.20):
        self.project_root = Path(project_root)
        self.calibration_fraction = calibration_fraction
        base = self.project_root / "data/interim/hancock"
        self.clinical_path = next(base.rglob("clinical_data.json"))
        self.pathological_path = next(base.rglob("pathological_data.json"))
        self.targets_path = next(base.rglob("features/targets.csv"))
        self.split_path = next(base.rglob("dataset_split_out.json"))
        self.tma_path = next(base.rglob("features/tma_cell_density.csv"))

    def source_paths(self) -> tuple[Path, ...]:
        return (
            self.clinical_path,
            self.pathological_path,
            self.targets_path,
            self.split_path,
            self.tma_path,
        )

    def load_records(self) -> list[PatientRecord]:
        clinical_rows = json.loads(self.clinical_path.read_text(encoding="utf-8-sig"))
        pathological = _by_id(
            json.loads(self.pathological_path.read_text(encoding="utf-8-sig"))
        )
        with self.targets_path.open("r", encoding="utf-8-sig", newline="") as handle:
            targets = _by_id(list(csv.DictReader(handle)))
        split_rows = json.loads(self.split_path.read_text(encoding="utf-8-sig"))
        official = {str(row["patient_id"]): str(row["dataset"]) for row in split_rows}
        with self.tma_path.open("r", encoding="utf-8-sig", newline="") as handle:
            tma_ids = {row["patient_id"].strip() for row in csv.DictReader(handle)}
        development_ids = [
            str(row["patient_id"]).strip()
            for row in clinical_rows
            if official[str(row["patient_id"]).strip()] == "training"
        ]
        development_split = deterministic_development_split(
            development_ids, self.calibration_fraction, "TRUST-HN:HANCOCK:OOD:phase2:v1"
        )
        records: list[PatientRecord] = []
        for row_number, clinical in enumerate(clinical_rows, start=2):
            native_id = str(clinical["patient_id"]).strip()
            path = pathological[native_id]
            target = targets[native_id]
            if official[native_id] == "test":
                split_role = SplitRole.SEALED_TEST
                cohort_role = CohortRole.HELD_OUT
                duration = event = None
                endpoint_status = EndpointStatus.SEALED
            else:
                split_role = development_split[native_id]
                cohort_role = CohortRole.DEVELOPMENT
                duration = float(target["days_to_last_information"])
                event = int(str(target["survival_status"]).strip().casefold() == "deceased")
                endpoint_status = EndpointStatus.USABLE
            stage_parts = [
                value for value in (_optional(path.get("pT_stage")), _optional(path.get("pN_stage"))) if value
            ]
            records.append(
                PatientRecord(
                    study=self.study,
                    cohort_role=cohort_role,
                    native_id=native_id,
                    split_role=split_role,
                    eligible=True,
                    exclusion_reason=None,
                    index_date_definition="initial_diagnosis",
                    duration_days=duration,
                    event=event,
                    endpoint_name="overall_survival",
                    endpoint_status=endpoint_status,
                    age=_float_or_none(clinical.get("age_at_initial_diagnosis")),
                    sex=_optional(clinical.get("sex")),
                    site=_optional(path.get("primary_tumor_site")),
                    stage="/".join(stage_parts) or None,
                    hpv=_optional(path.get("hpv_association_p16")),
                    treatment=_treatment_label(clinical),
                    clinical_features_available=True,
                    modality_features_available=native_id in tma_ids,
                    source_row_number=row_number,
                    provenance=(
                        self.clinical_path.relative_to(self.project_root).as_posix(),
                        self.pathological_path.relative_to(self.project_root).as_posix(),
                        self.targets_path.relative_to(self.project_root).as_posix(),
                        self.split_path.relative_to(self.project_root).as_posix(),
                    ),
                    smoking=_optional(clinical.get("smoking_status")),
                )
            )
        return records


