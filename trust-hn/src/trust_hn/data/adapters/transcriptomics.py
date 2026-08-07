"""TCGA-HNSC/GEO Phase 2 transcriptomics adapter.

Expression is represented lazily through availability flags and source provenance;
no 520 x 60,664 modeling matrix is materialized in Phase 2. GEO outcomes remain
sealed and are not copied into adapter records.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from trust_hn.data.contracts_v2 import (
    CohortRole,
    EndpointStatus,
    PatientRecord,
    SplitRole,
    deterministic_development_split,
)
from trust_hn.data.phase1 import collect_numbers, parse_geo_matrix


MONTH_DAYS = 365.25 / 12.0


def _optional(value: object) -> str | None:
    text = str(value or "").strip()
    if text.casefold() in {"", "na", "n/a", "not reported", "unknown"}:
        return None
    return text


def _float_or_none(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def gse41613_followup_days(months: str) -> float:
    value = float(months)
    if value < 0:
        raise ValueError("follow-up months must be non-negative")
    return value * MONTH_DAYS


def gse65858_primary_eligibility(
    tumor_type: str, distant_metastasis: str, treatment: str
) -> bool:
    return (
        tumor_type.strip().casefold() == "primary"
        and distant_metastasis.strip() == "0"
        and treatment.strip().casefold() != "palliative"
    )


def _tcga_endpoint(case: dict[str, Any]) -> tuple[float | None, int | None]:
    demographic = case.get("demographic") or {}
    vital = str(demographic.get("vital_status") or "").strip().casefold()
    if vital not in {"alive", "dead"}:
        return None, None
    event = int(vital == "dead")
    death = collect_numbers(case, "days_to_death")
    follow = collect_numbers(case, "days_to_last_follow_up") + collect_numbers(
        case, "days_to_follow_up"
    )
    duration = max(death) if event and death else (max(follow) if follow else None)
    if duration is None or duration < 0:
        return None, None
    return duration, event


def _first_primary_diagnosis(case: dict[str, Any]) -> dict[str, Any]:
    diagnoses = list(case.get("diagnoses") or [])
    for diagnosis in diagnoses:
        if diagnosis.get("diagnosis_is_primary_disease") is True:
            return diagnosis
    return diagnoses[0] if diagnoses else {}


class TranscriptomicsAdapter:
    study = "TRANSCRIPTOMICS"

    def __init__(self, project_root: Path, calibration_fraction: float = 0.20):
        self.project_root = Path(project_root)
        self.calibration_fraction = calibration_fraction
        self.tcga_clinical = self.project_root / "data/raw/tcga_hnsc/gdc_cases_clinical_response.json"
        self.tcga_manifest = self.project_root / "data/raw/tcga_hnsc/gdc_star_counts_primary_tumor_manifest.tsv"
        self.gse65858_matrix = self.project_root / (
            "data/interim/gse65858/geo_2026-06-03/GSE65858_series_matrix.txt"
        )
        self.gse41613_matrix = self.project_root / (
            "data/interim/gse41613/geo_2026-07-06/GSE41613_series_matrix.txt"
        )

    def source_paths(self) -> tuple[Path, ...]:
        return (
            self.tcga_clinical,
            self.tcga_manifest,
            self.gse65858_matrix,
            self.gse41613_matrix,
        )

    def load_records(self) -> list[PatientRecord]:
        return [*self._load_tcga(), *self._load_gse65858(), *self._load_gse41613()]

    def _load_tcga(self) -> list[PatientRecord]:
        with self.tcga_manifest.open("r", encoding="utf-8-sig", newline="") as handle:
            manifest = list(csv.DictReader(handle, delimiter="\t"))
        expression_ids = {
            case_id
            for row in manifest
            for case_id in str(row["case_submitter_ids"]).split(";")
            if case_id
        }
        hits = json.loads(self.tcga_clinical.read_text(encoding="utf-8"))["data"]["hits"]
        cases = {str(case["submitter_id"]): case for case in hits}
        ids = sorted(expression_ids & set(cases))
        split = deterministic_development_split(
            ids, self.calibration_fraction, "TRUST-HN:TCGA-HNSC:phase2:v1"
        )
        records: list[PatientRecord] = []
        for row_number, native_id in enumerate(ids, start=2):
            case = cases[native_id]
            demographic = case.get("demographic") or {}
            diagnosis = _first_primary_diagnosis(case)
            duration, event = _tcga_endpoint(case)
            endpoint_status = (
                EndpointStatus.USABLE if duration is not None else EndpointStatus.UNRESOLVED
            )
            records.append(
                PatientRecord(
                    study="TCGA-HNSC",
                    cohort_role=CohortRole.DEVELOPMENT,
                    native_id=native_id,
                    split_role=split[native_id],
                    eligible=True,
                    exclusion_reason=None,
                    index_date_definition="initial_diagnosis",
                    duration_days=duration,
                    event=event,
                    endpoint_name="overall_survival",
                    endpoint_status=endpoint_status,
                    age=_float_or_none(demographic.get("age_at_index")),
                    sex=_optional(demographic.get("sex_at_birth")),
                    site=_optional(diagnosis.get("tissue_or_organ_of_origin")),
                    stage=_optional(
                        diagnosis.get("ajcc_pathologic_stage")
                        or diagnosis.get("ajcc_clinical_stage")
                    ),
                    hpv=None,
                    treatment=_optional(diagnosis.get("prior_treatment")),
                    clinical_features_available=True,
                    modality_features_available=True,
                    source_row_number=row_number,
                    provenance=(
                        self.tcga_clinical.relative_to(self.project_root).as_posix(),
                        self.tcga_manifest.relative_to(self.project_root).as_posix(),
                        "STAR-count expression available lazily; GENCODE v36",
                    ),
                )
            )
        return records

    def _load_gse65858(self) -> list[PatientRecord]:
        parsed = parse_geo_matrix(self.gse65858_matrix)
        chars = parsed["characteristics"]
        records: list[PatientRecord] = []
        for index, native_id in enumerate(parsed["sample_ids"]):
            tumor_type = chars["tumor_type"][index]
            metastasis = chars["distant_metastasis"][index]
            treatment = chars["treatment"][index]
            eligible = gse65858_primary_eligibility(tumor_type, metastasis, treatment)
            reasons = []
            if tumor_type.strip().casefold() != "primary":
                reasons.append("not_primary_tumor")
            if metastasis.strip() != "0":
                reasons.append("distant_metastasis_present")
            if treatment.strip().casefold() == "palliative":
                reasons.append("palliative_treatment")
            records.append(
                PatientRecord(
                    study="GSE65858",
                    cohort_role=CohortRole.EXTERNAL,
                    native_id=native_id,
                    split_role=SplitRole.EXTERNAL_TEST if eligible else SplitRole.EXCLUDED,
                    eligible=eligible,
                    exclusion_reason=None if eligible else ";".join(reasons),
                    index_date_definition="study_defined_primary_tumor_baseline",
                    duration_days=None,
                    event=None,
                    endpoint_name="overall_survival",
                    endpoint_status=EndpointStatus.SEALED if eligible else EndpointStatus.NOT_APPLICABLE,
                    age=_float_or_none(chars["age"][index]),
                    sex=_optional(chars["gender"][index]),
                    site=_optional(chars["tumor_site"][index]),
                    stage=_optional(chars["uicc_stage"][index]),
                    hpv=_optional(chars["hpv16_dna_rna"][index]),
                    treatment=_optional(treatment),
                    clinical_features_available=True,
                    modality_features_available=True,
                    source_row_number=index + 2,
                    provenance=(
                        self.gse65858_matrix.relative_to(self.project_root).as_posix(),
                        "external outcome intentionally suppressed",
                    ),
                    smoking=_optional(chars["smoking"][index]),
                )
            )
        return records

    def _load_gse41613(self) -> list[PatientRecord]:
        parsed = parse_geo_matrix(self.gse41613_matrix)
        chars = parsed["characteristics"]
        records: list[PatientRecord] = []
        for index, native_id in enumerate(parsed["sample_ids"]):
            # Parse only to enforce the frozen month-to-day rule; do not retain outcome.
            gse41613_followup_days(chars["fu time"][index])
            records.append(
                PatientRecord(
                    study="GSE41613",
                    cohort_role=CohortRole.SENSITIVITY,
                    native_id=native_id,
                    split_role=SplitRole.SENSITIVITY,
                    eligible=True,
                    exclusion_reason=None,
                    index_date_definition="study_defined_primary_tumor_baseline",
                    duration_days=None,
                    event=None,
                    endpoint_name="overall_survival",
                    endpoint_status=EndpointStatus.SEALED,
                    age=None,
                    sex=_optional(chars["Sex"][index]),
                    site="Oral cavity",
                    stage=_optional(chars["tumor stage"][index]),
                    hpv="negative",
                    treatment=_optional(chars["treatment"][index]),
                    clinical_features_available=True,
                    modality_features_available=True,
                    source_row_number=index + 2,
                    provenance=(
                        self.gse41613_matrix.relative_to(self.project_root).as_posix(),
                        "follow-up source unit: months; conversion factor 30.4375 days/month",
                        "sensitivity cohort outcome intentionally suppressed",
                    ),
                    age_group=_optional(chars["age"][index]),
                )
            )
        return records
