"""Create a reproducible patient-level HANCOCK sample dataset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np


def canonical_patient_id(value: object) -> str:
    text = str(value if value is not None else "").strip()
    if not text:
        return ""
    try:
        number = float(text)
        if number.is_integer():
            text = str(int(number))
    except ValueError:
        pass
    return text.zfill(3)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def filter_json_rows(source: Path, destination: Path, selected: set[str]) -> tuple[int, set[str]]:
    rows = json.loads(source.read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Expected a JSON list of objects: {source}")
    filtered = [row for row in rows if canonical_patient_id(row.get("patient_id")) in selected]
    ids = {canonical_patient_id(row.get("patient_id")) for row in filtered}
    write_json(destination, filtered)
    return len(filtered), ids


def filter_csv_rows(
    source: Path,
    destination: Path,
    selected: set[str],
    id_getter: Callable[[dict[str, str]], str],
) -> tuple[int, set[str]]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8-sig", newline="") as input_handle:
        reader = csv.DictReader(input_handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing CSV header: {source}")
        rows = [row for row in reader if id_getter(row) in selected]
        fieldnames = list(reader.fieldnames)
    with destination.open("w", encoding="utf-8", newline="") as output_handle:
        writer = csv.DictWriter(output_handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    ids = {id_getter(row) for row in rows if id_getter(row)}
    return len(rows), ids


def filter_npz(source: Path, destination: Path, selected: set[str]) -> tuple[int, set[str]]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with np.load(source, allow_pickle=False) as archive:
        keys = [key for key in archive.files if canonical_patient_id(key) in selected]
        arrays = {key: archive[key] for key in keys}
    np.savez_compressed(destination, **arrays)
    return len(keys), {canonical_patient_id(key) for key in keys}


def file_record(
    root: Path,
    path: Path,
    *,
    role: str,
    rows: int | None = None,
    patient_ids: set[str] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "relative_path": path.relative_to(root).as_posix(),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    if rows is not None:
        record["rows_or_members"] = rows
    if patient_ids is not None:
        record["unique_patient_ids"] = len(patient_ids)
    return record


def find_one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one match for {pattern!r}; found {len(matches)}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("data/sample/hancock_135"))
    parser.add_argument("--sample-size", type=int, default=135)
    parser.add_argument("--seed", type=int, default=20260811)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    output_root = args.output
    if not output_root.is_absolute():
        output_root = project_root / output_root
    output_root = output_root.resolve()
    allowed_parent = (project_root / "data" / "sample").resolve()
    if output_root.parent != allowed_parent:
        raise RuntimeError(f"Output must be a direct child of {allowed_parent}")
    if output_root.exists():
        if not args.force:
            raise FileExistsError(f"Output already exists: {output_root}")
        shutil.rmtree(output_root)

    interim_root = project_root / "data" / "interim" / "hancock"
    version_roots = sorted(interim_root.glob("git-*"))
    if len(version_roots) != 1:
        raise RuntimeError(f"Expected one HANCOCK version root; found {len(version_roots)}")
    version_root = version_roots[0]

    clinical_source = find_one(version_root, "clinical_data.json")
    clinical_rows = json.loads(clinical_source.read_text(encoding="utf-8-sig"))
    master_ids = [canonical_patient_id(row["patient_id"]) for row in clinical_rows]
    if len(master_ids) != len(set(master_ids)):
        raise ValueError("Duplicate patient IDs in HANCOCK clinical_data.json")
    if args.sample_size <= 0 or args.sample_size > len(master_ids):
        raise ValueError(f"sample-size must be between 1 and {len(master_ids)}")

    selected = set(random.Random(args.seed).sample(master_ids, args.sample_size))
    selected_sorted = sorted(selected)

    dataset_root = output_root / "Hancock_Dataset"
    structured_out = dataset_root / "StructuredData"
    dictionaries_out = dataset_root / "DataSplits_DataDictionaries"
    tma_raw_out = dataset_root / "TMA_CellDensityMeasurements"
    feature_out = output_root / "HANCOCK_MultimodalDataset" / "features"
    metadata_out = output_root / "metadata"
    files: list[dict[str, Any]] = []
    coverage: dict[str, dict[str, Any]] = {}

    for name in ["clinical_data.json", "pathological_data.json", "blood_data.json"]:
        source = find_one(version_root, name)
        destination = structured_out / name
        count, ids = filter_json_rows(source, destination, selected)
        files.append(
            file_record(
                output_root,
                destination,
                role="structured_patient_data",
                rows=count,
                patient_ids=ids,
            )
        )
        coverage[name] = {
            "rows": count,
            "patients_present": len(ids),
            "patients_missing": sorted(selected - ids),
        }

    reference_source = find_one(version_root, "blood_data_reference_ranges.json")
    reference_destination = structured_out / reference_source.name
    reference_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(reference_source, reference_destination)
    files.append(file_record(output_root, reference_destination, role="field_reference_metadata"))

    for name in [
        "DataDictionary_blood.csv",
        "DataDictionary_clinical.csv",
        "DataDictionary_pathological.csv",
    ]:
        source = find_one(version_root, name)
        destination = dictionaries_out / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        files.append(file_record(output_root, destination, role="field_dictionary"))

    split_counts: dict[str, dict[str, int]] = {}
    for name in [
        "dataset_split_in.json",
        "dataset_split_out.json",
        "dataset_split_Oropharynx.json",
        "dataset_split_treatment_outcome.json",
    ]:
        source = find_one(version_root, name)
        destination = dictionaries_out / name
        count, ids = filter_json_rows(source, destination, selected)
        split_rows = json.loads(destination.read_text(encoding="utf-8"))
        split_counts[name] = dict(
            sorted(Counter(str(row.get("dataset", "")) for row in split_rows).items())
        )
        if count != args.sample_size or ids != selected:
            raise ValueError(f"Official split is incomplete after filtering: {name}")
        files.append(
            file_record(
                output_root, destination, role="official_split", rows=count, patient_ids=ids
            )
        )

    tma_source = find_one(version_root, "TMA_celldensity_measurements.csv")
    tma_destination = tma_raw_out / tma_source.name
    count, ids = filter_csv_rows(
        tma_source, tma_destination, selected, lambda row: canonical_patient_id(row.get("Case ID"))
    )
    files.append(
        file_record(
            output_root, tma_destination, role="raw_tma_cell_density", rows=count, patient_ids=ids
        )
    )
    coverage[tma_source.name] = {
        "rows": count,
        "patients_present": len(ids),
        "patients_missing": sorted(selected - ids),
    }

    source_feature_dir = find_one(version_root, "features")
    if not source_feature_dir.is_dir():
        raise RuntimeError(f"Expected a feature directory: {source_feature_dir}")
    for source in sorted(source_feature_dir.glob("*.csv")):
        destination = feature_out / source.name
        count, ids = filter_csv_rows(
            source, destination, selected, lambda row: canonical_patient_id(row.get("patient_id"))
        )
        files.append(
            file_record(
                output_root,
                destination,
                role="preextracted_feature_table",
                rows=count,
                patient_ids=ids,
            )
        )
        coverage[f"features/{source.name}"] = {
            "rows": count,
            "patients_present": len(ids),
            "patients_missing": sorted(selected - ids),
        }

    for source in sorted(source_feature_dir.glob("*.npz")):
        destination = feature_out / source.name
        count, ids = filter_npz(source, destination, selected)
        files.append(
            file_record(
                output_root,
                destination,
                role="preextracted_tma_embedding",
                rows=count,
                patient_ids=ids,
            )
        )
        coverage[f"features/{source.name}"] = {
            "members": count,
            "patients_present": len(ids),
            "patients_missing": sorted(selected - ids),
        }

    for name in [
        "clinical_data.json",
        "pathological_data.json",
        "features/clinical.csv",
        "features/pathological.csv",
        "features/targets.csv",
    ]:
        if coverage[name]["patients_present"] != args.sample_size:
            raise ValueError(f"Required experiment table lacks selected patients: {name}")

    metadata_out.mkdir(parents=True, exist_ok=True)
    patient_ids_path = metadata_out / "patient_ids.txt"
    patient_ids_path.write_text("\n".join(selected_sorted) + "\n", encoding="utf-8", newline="\n")
    files.append(
        file_record(
            output_root,
            patient_ids_path,
            role="sample_patient_id_inventory",
            rows=args.sample_size,
            patient_ids=selected,
        )
    )

    license_source = project_root / "data" / "manifests" / "hancock" / "license_notes.md"
    if license_source.exists():
        license_destination = metadata_out / "license_notes.md"
        shutil.copy2(license_source, license_destination)
        files.append(
            file_record(output_root, license_destination, role="license_and_citation_notes")
        )

    manifest = {
        "schema_version": "1.0",
        "sample_name": "hancock_135",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_version_root": version_root.relative_to(project_root).as_posix(),
        "selection": {
            "method": "simple random sample without replacement from all 763 clinical patient IDs",
            "random_generator": "Python random.Random (Mersenne Twister)",
            "seed": args.seed,
            "source_patient_count": len(master_ids),
            "sample_patient_count": args.sample_size,
            "selected_patient_ids_sorted": selected_sorted,
        },
        "field_preservation": {
            "json": (
                "Original object keys and values retained for selected patients; "
                "list order follows source files."
            ),
            "csv": (
                "Original headers, column order, and source cell strings retained "
                "for selected rows."
            ),
            "npz": "Original arrays retained unchanged for selected patient keys.",
            "natural_missingness": (
                "Missing source modalities are preserved and listed in coverage."
            ),
        },
        "official_split_counts": split_counts,
        "coverage": coverage,
        "files": sorted(files, key=lambda item: item["relative_path"]),
    }
    write_json(metadata_out / "sample_manifest.json", manifest)

    readme = f"""# HANCOCK 135-patient sample

This dataset is a reproducible simple random sample of **{args.sample_size}**
patients from the 763-patient HANCOCK cohort available in this workspace.

- Random seed: `{args.seed}`
- Sampling: without replacement from `clinical_data.json` patient IDs
- Patient fields/CSV columns: preserved from the HANCOCK sources
- Natural missing modalities: preserved, not imputed

## Layout

- `Hancock_Dataset/StructuredData/`: filtered structured JSON data
- `Hancock_Dataset/DataSplits_DataDictionaries/`: dictionaries and splits
- `Hancock_Dataset/TMA_CellDensityMeasurements/`: filtered raw TMA density rows
- `HANCOCK_MultimodalDataset/features/`: pre-extracted experiment features
- `metadata/patient_ids.txt`: sorted selected patient IDs
- `metadata/sample_manifest.json`: selection, coverage, hashes, and inventory
- `metadata/license_notes.md`: source citation/reuse notes

The workspace does not contain HANCOCK WSI/TMA source imagery or raw text
archives; those were not downloaded under the project data policy. All HANCOCK
data currently used by the TRUST-HN experiments, plus all other acquired
patient-level structured/TMA features, are included.
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    print(f"Created {output_root}")
    print(f"Selected patients: {len(selected)}")
    print(f"Data files inventoried: {len(files)}")
    print(f"Official split_out: {split_counts['dataset_split_out.json']}")


if __name__ == "__main__":
    main()
