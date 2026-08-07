"""Safely materialize reversible Phase 1 interim files without changing raw sources."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
import shutil
import stat
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def safe_extract_zip(source: Path, destination: Path) -> dict[str, object]:
    destination.mkdir(parents=True, exist_ok=True)
    destination_resolved = destination.resolve()
    extracted = 0
    total_bytes = 0
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            normalized = member.filename.replace("\\", "/")
            if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
                raise ValueError(f"absolute ZIP member rejected: {member.filename}")
            target = (destination / normalized).resolve()
            try:
                target.relative_to(destination_resolved)
            except ValueError as exc:
                raise ValueError(f"ZIP path traversal rejected: {member.filename}") from exc
            unix_mode = (member.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(unix_mode):
                raise ValueError(f"ZIP symlink rejected: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.stat().st_size != member.file_size:
                    raise FileExistsError(f"interim extraction mismatch: {target}")
            else:
                with archive.open(member) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
            extracted += 1
            total_bytes += member.file_size
    return {"source": source.name, "files": extracted, "uncompressed_bytes": total_bytes}


def decompress_gzip(source: Path, destination: Path) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return {"source": source.name, "destination": destination.name, "status": "already_present", "bytes": destination.stat().st_size}
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", suffix=".part", delete=False) as out:
            temp = Path(out.name)
            with gzip.open(source, "rb") as inp:
                shutil.copyfileobj(inp, out, 1024 * 1024)
        os.replace(temp, destination)
        return {"source": source.name, "destination": destination.name, "status": "decompressed", "bytes": destination.stat().st_size}
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def column_index(cell_reference: str) -> int:
    letters = re.match(r"[A-Za-z]+", cell_reference)
    if not letters:
        raise ValueError(f"invalid XLSX cell reference: {cell_reference}")
    value = 0
    for character in letters.group(0).upper():
        value = value * 26 + ord(character) - ord("A") + 1
    return value - 1


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t")) for item in root.iter(f"{{{MAIN_NS}}}si")]


def workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in relationships.iter(f"{{{PKG_REL_NS}}}Relationship")}
    output = []
    for sheet in workbook.iter(f"{{{MAIN_NS}}}sheet"):
        relation_id = sheet.attrib[f"{{{REL_NS}}}id"]
        target = targets[relation_id].replace("\\", "/").lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        output.append((sheet.attrib["name"], target))
    return output


def cell_text(cell: ET.Element, strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find(f"{{{MAIN_NS}}}v")
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        return strings[int(value.text)]
    if cell_type == "b":
        return "TRUE" if value.text == "1" else "FALSE"
    return value.text


def convert_xlsx_to_csv(source: Path, destination_dir: Path) -> list[dict[str, object]]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    with zipfile.ZipFile(source) as archive:
        strings = shared_strings(archive)
        for sheet_number, (sheet_name, target) in enumerate(workbook_sheets(archive), start=1):
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", sheet_name).strip("_") or f"sheet_{sheet_number}"
            output = destination_dir / f"{sheet_number:02d}_{safe_name}.csv"
            root = ET.fromstring(archive.read(target))
            rows: list[list[str]] = []
            max_columns = 0
            for row in root.iter(f"{{{MAIN_NS}}}row"):
                values: dict[int, str] = {}
                for cell in row.findall(f"{{{MAIN_NS}}}c"):
                    index = column_index(cell.attrib.get("r", "A1"))
                    values[index] = cell_text(cell, strings)
                width = max(values, default=-1) + 1
                max_columns = max(max_columns, width)
                rows.append([values.get(index, "") for index in range(width)])
            with output.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                for row in rows:
                    writer.writerow(row + [""] * (max_columns - len(row)))
            reports.append({"sheet": sheet_name, "csv": output.name, "rows": len(rows), "columns": max_columns})
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.project_root.resolve()
    raw = root / "data" / "raw"
    interim = root / "data" / "interim"
    report: dict[str, object] = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "operations": []}

    hancock = interim / "hancock" / "git-521b99b03a94008b28df5c3df4aa5f82aa14b25a"
    for archive_name, subdirectory in [
        ("HANCOCK_MultimodalDataset-521b99b03a94008b28df5c3df4aa5f82aa14b25a.zip", "repository"),
        ("StructuredData.zip", "structured_data"),
        ("DataSplits_DataDictionaries.zip", "splits_and_dictionaries"),
        ("TMA_CellDensityMeasurements.zip", "tma_cell_density"),
    ]:
        report["operations"].append(safe_extract_zip(raw / "hancock" / archive_name, hancock / subdirectory))

    radcure = interim / "radcure" / "v04_20241219"
    report["radcure_xlsx"] = convert_xlsx_to_csv(raw / "radcure" / "RADCURE_Clinical_v04_20241219.xlsx", radcure / "clinical_csv")
    radcure.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw / "radcure" / "RADCURE-patient-id-to-OPC-Radiomics-patient-id-mapping.csv", radcure / "RADCURE-patient-id-to-OPC-Radiomics-patient-id-mapping.csv")

    for study, matrix_name, annotation_name, version in [
        ("gse65858", "GSE65858_series_matrix.txt.gz", "GPL10558.annot.gz", "geo_2026-06-03"),
        ("gse41613", "GSE41613_series_matrix.txt.gz", "GPL570.annot.gz", "geo_2026-07-06"),
    ]:
        target = interim / study / version
        report["operations"].append(decompress_gzip(raw / study / matrix_name, target / matrix_name[:-3]))
        report["operations"].append(decompress_gzip(raw / study / annotation_name, target / annotation_name[:-3]))

    report_path = interim / "phase1_extraction_receipt.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
