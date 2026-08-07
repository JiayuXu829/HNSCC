"""Standard-library Phase 1 feasibility audit for frozen TRUST-HN sources.

Patient-level ID inventories are written only beneath Git-ignored data/interim.
No modeling matrices are constructed and no outcomes are used for tuning.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

MISSING = {"", "na", "n/a", "null", "none", "unknown", "not reported", "not available"}
HORIZON_DAYS = 730.5


def is_missing(value: object) -> bool:
    return value is None or str(value).strip().lower() in MISSING


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_ids(path: Path, values: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = sorted({str(value).strip() for value in values if str(value).strip()})
    path.write_text("".join(f"{value}\n" for value in ids), encoding="utf-8")


def duplicate_count(values: Iterable[str]) -> int:
    return sum(count - 1 for count in Counter(values).values() if count > 1)


def count_values(rows: Iterable[Mapping[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "")).strip() for row in rows).items()))


def missing_summary(rows: list[Mapping[str, Any]], fields: Iterable[str]) -> dict[str, dict[str, float | int]]:
    output = {}
    for field in fields:
        missing = sum(is_missing(row.get(field)) for row in rows)
        output[field] = {"n_missing": missing, "missing_fraction": missing / len(rows) if rows else 0.0}
    return output


def horizon_summary(pairs: Iterable[tuple[float, int]], horizon: float = HORIZON_DAYS) -> dict[str, int | float]:
    observed = list(pairs)
    positive = sum(event == 1 and duration <= horizon for duration, event in observed)
    negative = sum(duration >= horizon and not (event == 1 and duration <= horizon) for duration, event in observed)
    early = sum(event == 0 and duration < horizon for duration, event in observed)
    return {
        "horizon_days": horizon,
        "n_endpoint_usable": len(observed),
        "n_events_all_followup": sum(event for _, event in observed),
        "n_event_by_horizon": positive,
        "n_event_free_at_horizon": negative,
        "n_censored_before_horizon": early,
    }


def audit_radcure(root: Path, out: Path) -> tuple[dict[str, Any], set[str]]:
    path = root / "data/interim/radcure/v04_20241219/clinical_csv/01_RADCURE_TCIA_Clinical_r2_offset.csv"
    rows = read_csv(path)
    ids = [row["patient_id"].strip() for row in rows]
    write_ids(out / "radcure/patient_id_inventory.txt", ids)
    pairs = []
    invalid = 0
    for row in rows:
        try:
            duration = float(row["Length FU"]) * 365.25
        except (TypeError, ValueError):
            invalid += 1
            continue
        status = row["Status"].strip().lower()
        if duration < 0 or status not in {"alive", "dead"}:
            invalid += 1
        else:
            pairs.append((duration, int(status == "dead")))
    histology = Counter(row["Path"].strip() for row in rows)
    return {
        "source_table": path.relative_to(root).as_posix(),
        "rows": len(rows),
        "unique_patient_ids": len(set(ids)),
        "duplicate_patient_rows": duplicate_count(ids),
        "challenge_split_counts": count_values(rows, "RADCURE-challenge"),
        "histology": {
            "exact_squamous_cell_carcinoma": histology.get("Squamous Cell Carcinoma", 0),
            "label_contains_squamous": sum(n for label, n in histology.items() if "squamous" in label.lower()),
            "distinct_labels": len(histology),
            "all_label_counts": dict(sorted(histology.items())),
            "warning": "Broad string matching is descriptive only, not a frozen eligibility definition.",
        },
        "metastasis_category_counts": count_values(rows, "M "),
        "treatment_modality_counts": count_values(rows, "Tx Modality"),
        "endpoint_availability": {
            **horizon_summary(pairs),
            "invalid_or_missing_rows": invalid,
            "duration_source": "Length FU multiplied by 365.25",
            "duration_origin": "The dictionary defines diagnosis-to-last-contact, not yet the treatment-start index required by Study 1.",
            "event_source": "Status: Dead=1, Alive=0",
        },
        "selected_missingness": missing_summary(rows, ["ECOG PS", "Smoking PY", "Smoking Status", "Ds Site", "M ", "HPV", "Tx Modality", "Status", "Length FU"]),
        "processed_radiomics_rds": {
            "structural_audit": "pending_authoritative_R_environment",
            "reason": "No R/Rscript or validated RDS parser is available in the Phase 1 runtime.",
            "boundary": "Do not claim feature names, patient coverage, or negative-control structure until authoritative inspection.",
        },
    }, set(ids)


def get_hancock_root(root: Path) -> Path:
    matches = sorted((root / "data/interim/hancock").glob("git-*"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one HANCOCK extraction; found {len(matches)}")
    return matches[0]


def csv_id_audit(path: Path, master: set[str]) -> tuple[dict[str, Any], set[str]]:
    rows = read_csv(path)
    ids = [row["patient_id"].strip() for row in rows]
    unique = set(ids)
    return {
        "rows": len(rows), "unique_patient_ids": len(unique), "duplicate_patient_rows": duplicate_count(ids),
        "overlap_with_master": len(unique & master), "missing_vs_master": len(master - unique),
        "unexpected_vs_master": len(unique - master),
    }, unique


def npz_id_audit(path: Path, master: set[str]) -> tuple[dict[str, Any], set[str]]:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".npy")]
    ids = {Path(name).stem for name in members}
    return {
        "npy_members": len(members), "unique_patient_ids": len(ids), "overlap_with_master": len(ids & master),
        "missing_vs_master": len(master - ids), "unexpected_vs_master": len(ids - master),
        "member_naming": "one <patient_id>.npy member per represented patient",
    }, ids


def json_patient_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"expected list of objects: {path}")
    return rows, [str(row.get("patient_id", "")).strip() for row in rows]


def audit_hancock(root: Path, out: Path) -> tuple[dict[str, Any], set[str]]:
    version_root = get_hancock_root(root)
    clinical_path = next(version_root.rglob("features/clinical.csv"))
    master = {row["patient_id"].strip() for row in read_csv(clinical_path)}
    write_ids(out / "hancock/patient_id_inventory.txt", master)
    features = {}
    for path in sorted(clinical_path.parent.glob("*.csv")):
        features[path.name] = csv_id_audit(path, master)[0]
    for path in sorted(clinical_path.parent.glob("*.npz")):
        features[path.name] = npz_id_audit(path, master)[0]
    structured = {}
    for name in ["clinical_data.json", "pathological_data.json", "blood_data.json"]:
        path = next(version_root.rglob(name))
        rows, ids = json_patient_rows(path)
        unique = set(ids)
        structured[name] = {
            "rows": len(rows), "unique_patient_ids": len(unique),
            "duplicate_rows_beyond_one_per_patient": duplicate_count(ids),
            "overlap_with_master": len(unique & master), "missing_vs_master": len(master - unique),
            "unexpected_vs_master": len(unique - master),
        }
    splits = {}
    for name in ["dataset_split_in.json", "dataset_split_out.json", "dataset_split_Oropharynx.json", "dataset_split_treatment_outcome.json"]:
        path = next(version_root.rglob(name))
        rows, ids = json_patient_rows(path)
        owners: dict[str, set[str]] = {}
        for row in rows:
            owners.setdefault(str(row["patient_id"]), set()).add(str(row.get("dataset", "")))
        unique = set(ids)
        splits[name] = {
            "rows": len(rows), "unique_patient_ids": len(unique), "duplicate_patient_rows": duplicate_count(ids),
            "dataset_counts": count_values(rows, "dataset"),
            "patients_assigned_to_multiple_splits": sum(len(values) > 1 for values in owners.values()),
            "missing_vs_master": len(master - unique), "unexpected_vs_master": len(unique - master),
        }
    targets = read_csv(clinical_path.parent / "targets.csv")
    pairs = []
    for row in targets:
        try:
            duration = float(row["days_to_last_information"])
        except (TypeError, ValueError):
            continue
        status = row["survival_status"].strip().lower()
        if duration >= 0 and status in {"living", "deceased"}:
            pairs.append((duration, int(status == "deceased")))
    return {
        "versioned_extraction": version_root.relative_to(root).as_posix(),
        "master_patient_ids": len(master),
        "feature_file_coverage": features,
        "structured_file_coverage": structured,
        "official_split_audit": splits,
        "endpoint_availability": {
            "overall_survival": {**horizon_summary(pairs), "status_counts": count_values(targets, "survival_status"), "duration_field": "days_to_last_information"},
            "recurrence": {
                "status_counts": count_values(targets, "recurrence"),
                "days_to_recurrence_missing": sum(is_missing(row.get("days_to_recurrence")) for row in targets),
                "rfs_event_counts": count_values(targets, "rfs_event"),
                "days_to_rfs_event_missing": sum(is_missing(row.get("days_to_rfs_event")) for row in targets),
            },
            "selected_missingness": missing_summary(targets, ["recurrence", "days_to_recurrence", "survival_status", "survival_status_with_cause", "days_to_last_information", "rfs_event", "days_to_rfs_event"]),
        },
    }, master


def collect_numbers(value: Any, field: str) -> list[float]:
    numbers = []
    if isinstance(value, dict):
        if field in value and not is_missing(value[field]):
            try:
                number = float(value[field])
                if math.isfinite(number) and number >= 0:
                    numbers.append(number)
            except (TypeError, ValueError):
                pass
        for child in value.values():
            numbers.extend(collect_numbers(child, field))
    elif isinstance(value, list):
        for child in value:
            numbers.extend(collect_numbers(child, field))
    return numbers


def audit_tcga_expression(root: Path) -> dict[str, Any]:
    files = sorted((root / "data/raw/tcga_hnsc").glob("*.rna_seq.augmented_star_gene_counts.tsv"))
    models: Counter[str] = Counter(); headers: Counter[str] = Counter(); row_counts: Counter[int] = Counter(); signatures: Counter[str] = Counter()
    malformed = []
    expected = ["gene_id", "gene_name", "gene_type", "unstranded", "stranded_first", "stranded_second", "tpm_unstranded", "fpkm_unstranded", "fpkm_uq_unstranded"]
    for path in files:
        digest = hashlib.sha256()
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                model = handle.readline().rstrip("\r\n")
                header_line = handle.readline().rstrip("\r\n")
                header = header_line.split("\t")
                count = 0
                for line in handle:
                    fields = line.rstrip("\r\n").split("\t")
                    if len(fields) != len(expected):
                        raise ValueError(f"row has {len(fields)} fields")
                    digest.update("\t".join(fields[:3]).encode("utf-8") + b"\n")
                    count += 1
            models[model] += 1; headers[header_line] += 1; row_counts[count] += 1; signatures[digest.hexdigest()] += 1
            if header != expected:
                malformed.append(path.name)
        except (OSError, UnicodeError, ValueError) as exc:
            malformed.append(f"{path.name}: {exc}")
    return {
        "files_audited": len(files), "gene_model_declarations": dict(sorted(models.items())),
        "distinct_headers": len(headers), "header_counts": dict(sorted(headers.items())),
        "gene_row_count_distribution": {str(k): v for k, v in sorted(row_counts.items())},
        "distinct_gene_identity_order_signatures": len(signatures),
        "gene_identity_order_signature_counts": dict(sorted(signatures.items())),
        "malformed_or_nonconforming_files": malformed,
        "all_files_conform": len(files) == 520 and not malformed and len(models) == len(headers) == len(row_counts) == len(signatures) == 1,
    }


def audit_tcga(root: Path, out: Path) -> tuple[dict[str, Any], set[str]]:
    raw = root / "data/raw/tcga_hnsc"
    manifest = read_csv(raw / "gdc_star_counts_primary_tumor_manifest.tsv", delimiter="\t")
    expression_ids = [value for row in manifest for value in row["case_submitter_ids"].split(";") if value]
    expression = set(expression_ids)
    clinical_rows = json.loads((raw / "gdc_cases_clinical_response.json").read_text(encoding="utf-8"))["data"]["hits"]
    clinical = {str(row["submitter_id"]) for row in clinical_rows}
    write_ids(out / "tcga_hnsc/expression_case_id_inventory.txt", expression)
    write_ids(out / "tcga_hnsc/clinical_case_id_inventory.txt", clinical)
    write_ids(out / "tcga_hnsc/clinical_only_case_id_inventory.txt", clinical - expression)
    pairs = []; missing_duration = 0; invalid_vital = 0; vital_counts: Counter[str] = Counter()
    for case in clinical_rows:
        vital = str((case.get("demographic") or {}).get("vital_status") or "").strip().lower()
        vital_counts[vital] += 1
        if vital not in {"alive", "dead"}:
            invalid_vital += 1; continue
        event = int(vital == "dead")
        death = collect_numbers(case, "days_to_death")
        follow = collect_numbers(case, "days_to_last_follow_up") + collect_numbers(case, "days_to_follow_up")
        duration = max(death) if event and death else (max(follow) if follow else None)
        if duration is None:
            missing_duration += 1
        else:
            pairs.append((duration, event))
    return {
        "gdc_manifest_rows": len(manifest), "unique_expression_cases": len(expression),
        "duplicate_expression_case_rows": duplicate_count(expression_ids), "clinical_project_cases": len(clinical),
        "expression_clinical_overlap": len(expression & clinical), "clinical_only_cases": len(clinical - expression),
        "expression_only_cases": len(expression - clinical),
        "endpoint_availability": {
            **horizon_summary(pairs), "vital_status_counts": dict(sorted(vital_counts.items())),
            "missing_duration_after_resolution": missing_duration, "invalid_vital_status": invalid_vital,
            "duration_resolution": "Dead: maximum nonnegative days_to_death; Alive: maximum days_to_last_follow_up/days_to_follow_up.",
            "warning": "Feasibility resolution only, not the final Phase 2 endpoint adapter.",
        },
        "star_counts_consistency": audit_tcga_expression(root),
    }, expression


def parse_geo_matrix(path: Path) -> dict[str, Any]:
    sample_rows = []; matrix_header = None; matrix_rows = 0; in_table = False
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.startswith("!Sample_"):
                row = next(csv.reader([line.rstrip("\r\n")], delimiter="\t"))
                sample_rows.append((row[0][1:], [value.strip('"') for value in row[1:]]))
            elif line.startswith("!series_matrix_table_begin"):
                matrix_header = next(csv.reader([next(handle).rstrip("\r\n")], delimiter="\t")); in_table = True
            elif line.startswith("!series_matrix_table_end"):
                in_table = False
            elif in_table:
                matrix_rows += 1
    if matrix_header is None:
        raise ValueError(f"matrix header not found: {path}")
    accessions = next(values for key, values in sample_rows if key == "Sample_geo_accession")
    titles = next(values for key, values in sample_rows if key == "Sample_title")
    characteristics = {}
    for key, values in sample_rows:
        if key != "Sample_characteristics_ch1":
            continue
        labels = [value.split(":", 1)[0].strip() if ":" in value else value.strip() for value in values]
        if len(set(labels)) != 1:
            raise ValueError(f"inconsistent characteristic labels: {path.name}")
        label = labels[0]
        characteristics[label] = [value.split(":", 1)[1].strip() if ":" in value else value.strip() for value in values]
    n = len(accessions)
    if len(matrix_header) - 1 != n or len(titles) != n:
        raise ValueError(f"sample/column mismatch: {path.name}")
    summary = {}
    for key, values in sorted(characteristics.items()):
        unique = set(values)
        summary[key] = {
            "n_values": len(values), "n_missing": sum(is_missing(value) for value in values), "n_unique": len(unique),
            "value_counts": dict(sorted(Counter(values).items())) if len(unique) <= 15 else None,
        }
    return {"sample_ids": accessions, "characteristics": characteristics, "summary": {
        "samples": n, "matrix_sample_columns": len(matrix_header) - 1, "matrix_feature_rows": matrix_rows,
        "unique_geo_accessions": len(set(accessions)), "duplicate_geo_accessions": duplicate_count(accessions), "characteristics": summary,
    }}


def geo_endpoints(accession: str, parsed: Mapping[str, Any]) -> dict[str, Any]:
    chars = parsed["characteristics"]
    if accession == "GSE65858":
        pairs = []
        for duration, event in zip(chars.get("os", []), chars.get("os_event", []), strict=True):
            try: d = float(duration)
            except ValueError: continue
            e = event.strip().lower()
            if d >= 0 and e in {"true", "false"}: pairs.append((d, int(e == "true")))
        return {
            **horizon_summary(pairs), "duration_field": "os", "event_field": "os_event", "duration_unit": "days",
            "tumor_type_counts": dict(sorted(Counter(chars.get("tumor_type", [])).items())),
            "treatment_counts": dict(sorted(Counter(chars.get("treatment", [])).items())),
            "distant_metastasis_counts": dict(sorted(Counter(chars.get("distant_metastasis", [])).items())),
        }
    pairs = []
    for duration, status in zip(chars.get("fu time", []), chars.get("vital", []), strict=True):
        try: d = float(duration)
        except ValueError: continue
        if d >= 0 and (status == "Alive" or status.startswith("Dead")): pairs.append((d, int(status.startswith("Dead"))))
    return {
        "n_endpoint_usable": len(pairs), "n_events_all_followup": sum(event for _, event in pairs),
        "duration_field": "fu time", "event_field": "vital (all Dead* mapped to all-cause death for feasibility only)",
        "duration_unit": "not encoded in the series matrix; verify from publication before modeling",
        "vital_status_counts": dict(sorted(Counter(chars.get("vital", [])).items())),
        "population_note": "HPV-negative oral squamous cell carcinoma only; sensitivity cohort, not general HNSCC external test.",
    }


def audit_geo(root: Path, out: Path, accession: str, rel_path: str) -> tuple[dict[str, Any], set[str]]:
    parsed = parse_geo_matrix(root / rel_path)
    ids = set(parsed["sample_ids"])
    write_ids(out / accession.lower() / "sample_id_inventory.txt", ids)
    return {"source_matrix": rel_path, **parsed["summary"], "endpoint_availability": geo_endpoints(accession, parsed)}, ids


def overlap_matrix(cohorts: Mapping[str, set[str]]) -> dict[str, dict[str, int]]:
    return {left: {right: len(cohorts[left] & cohorts[right]) for right in cohorts} for left in cohorts}


def write_overlap_csv(path: Path, matrix: Mapping[str, Mapping[str, int]]) -> None:
    names = list(matrix); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["cohort", *names])
        for name in names: writer.writerow([name, *(matrix[name][other] for other in names)])


def run(root: Path, out: Path) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    radcure, a = audit_radcure(root, out)
    hancock, b = audit_hancock(root, out)
    tcga, c = audit_tcga(root, out)
    gse65858, d = audit_geo(root, out, "GSE65858", "data/interim/gse65858/geo_2026-06-03/GSE65858_series_matrix.txt")
    gse41613, e = audit_geo(root, out, "GSE41613", "data/interim/gse41613/geo_2026-07-06/GSE41613_series_matrix.txt")
    cohorts = {"radcure": a, "hancock": b, "tcga_hnsc_expression": c, "gse65858": d, "gse41613": e}
    overlaps = overlap_matrix(cohorts); write_overlap_csv(out / "cross_cohort_exact_id_overlap.csv", overlaps)
    result = {
        "schema_version": "1.0", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 1 acquisition and feasibility audit",
        "governance": {
            "modeling_performed": False, "sealed_test_outcomes_used_for_tuning": False,
            "patient_id_inventories_location": "data/interim/phase1_audit (Git-ignored)",
            "exact_id_overlap_note": "Native source identifiers compared exactly without cross-cohort normalization.",
        },
        "cohorts": {"radcure": radcure, "hancock": hancock, "tcga_hnsc": tcga, "gse65858": gse65858, "gse41613": gse41613},
        "cross_cohort_exact_id_overlap": overlaps,
        "unresolved_items": [
            "Authoritative structural inspection of the ORCESTRA RDS requires R/Rscript or a validated RDS reader.",
            "RADCURE OS origin is diagnosis; treatment-start alignment must be resolved before Phase 2.",
            "GSE41613 follow-up time unit must be verified from the source publication before endpoint construction.",
            "License/citation notes are documentary feasibility records and are not legal advice.",
        ],
    }
    (out / "phase1_audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    root = args.project_root.resolve(); out = (args.output_root or root / "data/interim/phase1_audit").resolve()
    result = run(root, out)
    print(json.dumps({"output": str(out / "phase1_audit.json"), "cohorts": list(result["cohorts"]), "tcga_expression_files_audited": result["cohorts"]["tcga_hnsc"]["star_counts_consistency"]["files_audited"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())