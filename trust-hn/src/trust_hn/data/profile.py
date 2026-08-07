"""Generate leakage-conscious Phase 1 audit artifacts from patient-level tables."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from trust_hn.data.tabular import (
    TableAuditError,
    is_missing,
    parse_binary_event,
    parse_nonnegative_float,
    read_delimited,
    resolve_unique_field,
)
from trust_hn.evaluation.endpoints import HorizonStatus, classify_horizon_outcome


@dataclass(frozen=True)
class FieldResolution:
    patient_id: str | None
    split: str | None
    duration: str | None
    event: str | None

    @property
    def endpoint_ready(self) -> bool:
        return self.duration is not None and self.event is not None

    @property
    def split_ready(self) -> bool:
        return self.patient_id is not None and self.split is not None


def infer_type(values: Iterable[str]) -> str:
    observed = [str(value).strip() for value in values if not is_missing(value)]
    if not observed:
        return "unknown_all_missing"
    lowered = {value.lower() for value in observed}
    if lowered <= {"0", "1", "true", "false", "yes", "no"}:
        return "boolean_or_binary"
    try:
        integers = [int(value) for value in observed]
        if all(str(number) == value or f"{number}.0" == value for number, value in zip(integers, observed, strict=True)):
            return "integer"
    except ValueError:
        pass
    try:
        numeric = [float(value) for value in observed]
        if all(math.isfinite(value) for value in numeric):
            return "number"
    except ValueError:
        pass
    unique_fraction = len(set(observed)) / len(observed)
    return "categorical" if len(set(observed)) <= 30 or unique_fraction <= 0.05 else "string"


def resolve_fields(headers: Sequence[str], spec: Mapping[str, object]) -> FieldResolution:
    candidate_map = spec.get("field_candidates", {})
    if not isinstance(candidate_map, dict):
        raise TableAuditError("field_candidates must be a mapping")

    def candidates(role: str) -> list[str]:
        values = candidate_map.get(role, [])
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise TableAuditError(f"field_candidates.{role} must be a list of strings")
        return values

    return FieldResolution(
        patient_id=resolve_unique_field(headers, candidates("patient_id")),
        split=resolve_unique_field(headers, candidates("split")),
        duration=resolve_unique_field(headers, candidates("duration")),
        event=resolve_unique_field(headers, candidates("event")),
    )


def dictionary_rows(headers: Sequence[str], rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    output = []
    for header in headers:
        values = [row.get(header, "") for row in rows]
        nonmissing = [str(value).strip() for value in values if not is_missing(value)]
        examples = sorted(set(nonmissing))[:5]
        output.append(
            {
                "raw_field": header,
                "inferred_type": infer_type(values),
                "n_rows": len(values),
                "n_missing": sum(is_missing(value) for value in values),
                "missing_fraction": (sum(is_missing(value) for value in values) / len(values)) if values else 0.0,
                "n_unique_nonmissing": len(set(nonmissing)),
                "example_values": " | ".join(examples),
                "meaning": "PENDING_MANUAL_REVIEW",
                "unit": "PENDING_MANUAL_REVIEW",
                "prediction_time_available": "PENDING_MANUAL_REVIEW",
            }
        )
    return output


def missingness_rows(
    headers: Sequence[str], rows: Sequence[Mapping[str, str]], split_field: str | None
) -> list[dict[str, object]]:
    groups: dict[str, list[Mapping[str, str]]] = {"ALL": list(rows)}
    if split_field:
        for row in rows:
            split = str(row.get(split_field, "")).strip() or "MISSING_SPLIT"
            groups.setdefault(split, []).append(row)
    output = []
    for split, subset in groups.items():
        for header in headers:
            n_missing = sum(is_missing(row.get(header, "")) for row in subset)
            output.append(
                {
                    "split": split,
                    "variable": header,
                    "n_total": len(subset),
                    "n_missing": n_missing,
                    "missing_fraction": n_missing / len(subset) if subset else 0.0,
                    "structural_missingness": "PENDING_REVIEW",
                    "notes": "",
                }
            )
    return output


def split_summary(
    rows: Sequence[Mapping[str, str]], patient_field: str, split_field: str
) -> dict[str, object]:
    patients_by_split: dict[str, set[str]] = defaultdict(set)
    split_by_patient: dict[str, set[str]] = defaultdict(set)
    missing_patient_rows = 0
    missing_split_rows = 0
    for row in rows:
        patient = str(row.get(patient_field, "")).strip()
        split = str(row.get(split_field, "")).strip()
        if not patient:
            missing_patient_rows += 1
            continue
        if not split:
            missing_split_rows += 1
            continue
        patients_by_split[split].add(patient)
        split_by_patient[patient].add(split)
    overlap_count = sum(len(splits) > 1 for splits in split_by_patient.values())
    return {
        "patient_counts": {key: len(value) for key, value in sorted(patients_by_split.items())},
        "patient_overlap_count": overlap_count,
        "missing_patient_id_rows": missing_patient_rows,
        "missing_split_rows": missing_split_rows,
        "split_values": sorted(patients_by_split),
    }


def endpoint_summary(
    rows: Sequence[Mapping[str, str]],
    duration_field: str,
    event_field: str,
    multiplier_to_days: float,
    event_mapping: Mapping[str, int] | None,
    horizon_days: float,
    split_field: str | None,
) -> dict[str, object]:
    if multiplier_to_days <= 0:
        raise TableAuditError("duration_multiplier_to_days must be positive")
    counts: Counter[str] = Counter()
    invalid_examples: list[str] = []
    duration_days: list[float] = []
    events = 0
    by_split: dict[str, Counter[str]] = defaultdict(Counter)
    for row_number, row in enumerate(rows, start=2):
        split = str(row.get(split_field, "ALL")).strip() if split_field else "ALL"
        split = split or "MISSING_SPLIT"
        try:
            duration = parse_nonnegative_float(row.get(duration_field, ""), duration_field)
            event = parse_binary_event(row.get(event_field, ""), event_mapping)
        except TableAuditError as exc:
            counts["invalid_or_missing"] += 1
            by_split[split]["invalid_or_missing"] += 1
            if len(invalid_examples) < 10:
                invalid_examples.append(f"row {row_number}: {exc}")
            continue
        days = duration * multiplier_to_days
        duration_days.append(days)
        events += event
        outcome = classify_horizon_outcome(days, event, horizon_days)
        counts[outcome.status.value] += 1
        by_split[split][outcome.status.value] += 1
    sorted_days = sorted(duration_days)
    median = None
    if sorted_days:
        middle = len(sorted_days) // 2
        median = sorted_days[middle] if len(sorted_days) % 2 else (sorted_days[middle - 1] + sorted_days[middle]) / 2
    return {
        "n_rows": len(rows),
        "n_valid": len(duration_days),
        "n_events": events,
        "event_fraction_valid": events / len(duration_days) if duration_days else None,
        "median_followup_or_event_days": median,
        "horizon_days": horizon_days,
        "horizon_counts": dict(counts),
        "by_split": {split: dict(counter) for split, counter in sorted(by_split.items())},
        "invalid_examples_without_values": invalid_examples,
        "early_censoring_is_binary_negative": False,
    }


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(
    path: Path,
    title: str,
    resolution: FieldResolution,
    split: Mapping[str, object] | None,
    endpoint: Mapping[str, object] | None,
    warnings: Sequence[str],
) -> None:
    lines = [f"# {title}", "", "**Generated artifact; manual clinical review remains required.**", ""]
    lines += ["## Field resolution", "", "```json", json.dumps(resolution.__dict__, indent=2), "```", ""]
    if split is not None:
        lines += ["## Split audit", "", "```json", json.dumps(split, indent=2), "```", ""]
    if endpoint is not None:
        lines += ["## Endpoint audit", "", "```json", json.dumps(endpoint, indent=2), "```", ""]
    lines += ["## Warnings", ""]
    lines += [f"- {warning}" for warning in warnings] or ["- None generated automatically."]
    lines += ["", "## Governance decision", "", "PENDING_MANUAL_GO_NO_GO", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_profile(table_path: Path, spec_path: Path, output_dir: Path) -> dict[str, object]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise TableAuditError("audit spec must be a JSON object")
    headers, rows = read_delimited(table_path)
    resolution = resolve_fields(headers, spec)
    warnings: list[str] = []
    split = None
    endpoint = None
    if resolution.split_ready:
        split = split_summary(rows, resolution.patient_id, resolution.split)
        if split["patient_overlap_count"]:
            warnings.append("Patients occur in more than one split; this is a blocking error.")
    else:
        warnings.append("Patient ID and/or split field unresolved; split audit is incomplete.")

    if resolution.endpoint_ready:
        event_mapping = spec.get("event_mapping")
        if event_mapping is not None and not isinstance(event_mapping, dict):
            raise TableAuditError("event_mapping must be an object")
        endpoint = endpoint_summary(
            rows=rows,
            duration_field=resolution.duration,
            event_field=resolution.event,
            multiplier_to_days=float(spec.get("duration_multiplier_to_days", 1.0)),
            event_mapping=event_mapping,
            horizon_days=float(spec.get("horizon_days", 730.5)),
            split_field=resolution.split,
        )
        if endpoint["horizon_counts"].get(HorizonStatus.CENSORED_BEFORE_HORIZON.value, 0):
            warnings.append("Early-censored observations are retained as unknown for binary horizon analyses.")
        if endpoint["horizon_counts"].get("invalid_or_missing", 0):
            warnings.append("Some endpoint rows are invalid or missing; inspect source fields before inclusion.")
    else:
        warnings.append("Duration and/or event field unresolved; endpoint audit is incomplete.")

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "data_dictionary_auto.csv", dictionary_rows(headers, rows))
    write_csv(output_dir / "missingness_auto.csv", missingness_rows(headers, rows, resolution.split))
    (output_dir / "field_resolution.json").write_text(
        json.dumps(resolution.__dict__, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "study": spec.get("study", "UNSPECIFIED"),
        "source_table": table_path.name,
        "n_rows": len(rows),
        "n_columns": len(headers),
        "field_resolution": resolution.__dict__,
        "split": split,
        "endpoint": endpoint,
        "warnings": warnings,
        "go_no_go": "PENDING_MANUAL_REVIEW",
    }
    (output_dir / "audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown_report(
        output_dir / "automated_audit.md",
        f"{spec.get('study', 'Study')} automated Phase 1 audit",
        resolution,
        split,
        endpoint,
        warnings,
    )
    return summary