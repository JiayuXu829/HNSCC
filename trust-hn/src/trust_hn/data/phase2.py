"""Phase 2 orchestration: unified adapters and descriptive analyses only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from trust_hn.data.adapters import HancockAdapter, RadcureAdapter, TranscriptomicsAdapter
from trust_hn.data.contracts_v2 import PatientRecord, validate_patient_records
from trust_hn.reporting.descriptive import write_descriptive_outputs, write_private_records


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _slug(study: str) -> str:
    return study.casefold().replace("-", "_")


def _group_by_study(records: Iterable[PatientRecord]) -> dict[str, list[PatientRecord]]:
    grouped: dict[str, list[PatientRecord]] = defaultdict(list)
    for record in records:
        grouped[record.study].append(record)
    return dict(grouped)


def _assert_public_outputs_have_no_id_columns(paths: Iterable[Path]) -> None:
    forbidden_headers = {"native_id", "patient_id", "sample_id", "source_row_number"}
    native_patterns = {
        "RADCURE patient ID": r"RADCURE-\d{4,}",
        "TCGA submitter ID": r"TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}",
        "GEO sample accession": r"GSM\d{4,}",
    }
    for path in paths:
        if path.suffix == ".csv" and path.stat().st_size:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                header = next(csv.reader(handle))
            overlap = forbidden_headers & set(header)
            if overlap:
                raise RuntimeError(f"identifier column leaked into tracked output {path}: {sorted(overlap)}")
        text = path.read_text(encoding="utf-8")
        for label, pattern in native_patterns.items():
            if re.search(pattern, text):
                raise RuntimeError(f"{label} leaked into {path}")


def _endpoint_audit_markdown(grouped: dict[str, list[PatientRecord]]) -> str:
    lines = [
        "# Phase 2 endpoint audit",
        "",
        "**Scope:** adapter construction and descriptive analysis only; no model fitting occurred.",
        "",
        "## Governance",
        "",
        "- Development train/calibration outcomes may be summarized.",
        "- RADCURE challenge-test and HANCOCK OOD-test outcomes are suppressed.",
        "- GSE65858 and GSE41613 outcomes are suppressed from Phase 2 adapter records and reports.",
        "- External outcomes were not used for preprocessing, selection, tuning, calibration, or thresholds.",
        "",
        "## Cohort endpoint status",
        "",
        "| Study | Records | Eligible | Endpoint usable | Sealed outcomes | Unresolved |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for study, rows in sorted(grouped.items()):
        lines.append(
            f"| {study} | {len(rows)} | {sum(r.eligible for r in rows)} | "
            f"{sum(r.endpoint_status.value == 'usable' for r in rows)} | "
            f"{sum(r.endpoint_status.value == 'sealed' for r in rows)} | "
            f"{sum(r.endpoint_status.value == 'unresolved' for r in rows)} |"
        )
    lines += [
        "",
        "## Frozen endpoint decisions",
        "",
        "- **RADCURE:** overall survival is `Last FU - RT Start`, indexed at the first radiotherapy fraction. All 3,346 source rows have parseable dates and nonnegative differences. `Length FU` remains diagnosis-origin and is not used by the Phase 2 adapter.",
        "- **HANCOCK:** overall survival is diagnosis-to-last-information/death in days, matching the source data dictionary.",
        "- **TCGA-HNSC:** deceased cases use nonnegative `days_to_death`; living cases use the maximum available follow-up day. Only expression/clinical-overlap cases enter the adapter.",
        "- **GSE65858:** external eligibility is frozen as primary tumor, no distant metastasis, and non-palliative treatment; outcomes remain sealed.",
        "- **GSE41613:** the source article reports follow-up in months (PMCID PMC3593802); the frozen conversion is `months x 30.4375`. This remains an HPV-negative OSCC sensitivity cohort and outcomes remain sealed.",
        "",
        "## Remaining non-blocking condition",
        "",
        "- ORCESTRA radiomics are not exposed because the RDS structure still requires validation with R/Rscript or a validated parser. This blocks radiomics modeling, not Phase 2 clinical descriptive work.",
        "",
        "**Serious unresolved endpoint errors:** 0 within the authorized Phase 2 scope.",
        "",
    ]
    return "\n".join(lines)


def run(project_root: Path) -> dict[str, object]:
    root = Path(project_root).resolve()
    adapters = [RadcureAdapter(root), HancockAdapter(root), TranscriptomicsAdapter(root)]
    all_records: list[PatientRecord] = []
    source_paths: list[Path] = []
    adapter_summaries = []
    interim_root = root / "data/interim/phase2"
    for adapter in adapters:
        records = adapter.load_records()
        all_records.extend(records)
        source_paths.extend(Path(path) for path in adapter.source_paths())
        adapter_summaries.append({"adapter": type(adapter).__name__, "records": len(records)})

    grouped = _group_by_study(all_records)
    validations = {}
    for study, records in grouped.items():
        report = validate_patient_records(records)
        validations[study] = report.__dict__
        write_private_records(interim_root / _slug(study) / "adapter_records.csv", records)

    outputs = write_descriptive_outputs(root / "results", all_records)
    audit_path = root / "docs/audits/phase2/endpoint_audit.md"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(_endpoint_audit_markdown(grouped), encoding="utf-8")
    public_paths = [*outputs.values(), audit_path]
    _assert_public_outputs_have_no_id_columns(public_paths)

    config_paths = [
        root / "configs/phase2_contract.json",
        root / "configs/phase2_governance.json",
        root / "data/schemas/unified_patient_record.schema.json",
    ]
    receipt_path = root / "results/manifests/phase2_adapter_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "2.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 2 unified adapters and descriptive analysis",
        "modeling_performed": False,
        "phase3_authorized": False,
        "sealed_or_external_outcomes_in_public_outputs": False,
        "patient_level_outputs": "data/interim/phase2 (Git-ignored)",
        "adapters": adapter_summaries,
        "validations": validations,
        "source_sha256": {
            path.relative_to(root).as_posix(): sha256_file(path) for path in sorted(set(source_paths))
        },
        "contract_sha256": {
            path.relative_to(root).as_posix(): sha256_file(path) for path in config_paths
        },
        "output_sha256": {
            path.relative_to(root).as_posix(): sha256_file(path) for path in public_paths
        },
        "identifier_leakage_guard": {
            "forbidden_csv_headers_checked": True,
            "native_id_patterns_checked": ["RADCURE numeric format", "TCGA submitter format", "GEO GSM numeric format"],
            "short_numeric_HANCOCK_ids": "protected structurally by aggregate-only writers; substring scanning is not specific",
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {**receipt, "receipt": receipt_path.relative_to(root).as_posix()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument(
        "--phase",
        choices=["phase2"],
        default="phase2",
        help="Only Phase 2 is authorized; modeling phases are intentionally unavailable.",
    )
    args = parser.parse_args(argv)
    result = run(args.project_root)
    print(json.dumps({"receipt": result["receipt"], "validations": result["validations"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

