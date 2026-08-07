"""Generate Phase 1 source manifests, license notes, and read-only freezes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def utc_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def write_json_yaml(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def receipts_for(root: Path, study: str, versions: dict[str, str]) -> list[dict[str, Any]]:
    output = []
    for receipt_path in sorted((root / f"data/raw/{study}").glob("*.receipt.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        filename = Path(receipt["relative_path"]).name
        output.append({
            "relative_path": receipt["relative_path"],
            "filename": filename,
            "role": receipt["role"],
            "source_url": receipt["source_url"],
            "version": versions.get(filename, "frozen at retrieval"),
            "retrieved_at_utc": receipt["retrieved_at_utc"],
            "bytes": receipt["bytes"],
            "sha256": receipt["sha256"],
            "immutable": True,
            "receipt": receipt_path.relative_to(root).as_posix(),
        })
    return output


def build_manifests(root: Path) -> dict[str, Any]:
    frozen = json.loads((root / "configs/phase1_sources.json").read_text(encoding="utf-8"))
    versions = {item["filename"]: item.get("version", "frozen at retrieval") for item in frozen["artifacts"]}
    generated = datetime.now(timezone.utc).isoformat()
    audit_path = root / "data/interim/phase1_audit/phase1_audit.json"
    audit_hash = sha256(audit_path)
    manifests: dict[str, Any] = {}

    study_meta = {
        "radcure": {"source_version": "TCIA Version 4 (2024-12-19) and Zenodo DOI 10.5281/zenodo.14226536", "expected_subjects": 3346},
        "hancock": {"source_version": "Git commit 521b99b03a94008b28df5c3df4aa5f82aa14b25a; external ZIP objects retrieved 2026-08-07", "expected_subjects": 763},
        "gse65858": {"source_version": "GEO series matrix server object 2026-06-03; GPL10558 annotation", "expected_subjects": 270},
        "gse41613": {"source_version": "GEO series matrix server object 2026-07-06; GPL570 annotation", "expected_subjects": 97},
    }
    for study, metadata in study_meta.items():
        manifest = {
            "schema_version": "1.0",
            "study": study,
            "generated_at_utc": generated,
            **metadata,
            "phase1_audit": {"relative_path": audit_path.relative_to(root).as_posix(), "sha256": audit_hash},
            "files": receipts_for(root, study, versions),
            "prohibited_material_acquired": False,
        }
        write_json_yaml(root / f"data/manifests/{study}/data_manifest.yaml", manifest)
        manifests[study] = manifest

    summary = json.loads((root / "data/manifests/tcga_hnsc_gdc_download_summary.json").read_text(encoding="utf-8"))
    tcga_files = []
    for item in summary["files"]:
        tcga_files.append({
            "relative_path": item["relative_path"], "filename": Path(item["relative_path"]).name,
            "role": item["role"], "source_url": item["source_url"],
            "version": "GDC Data Release 45.0; STAR - Counts; Primary Tumor; GENCODE v36",
            "retrieved_at_utc": item["retrieved_at_utc"], "bytes": item["bytes"],
            "sha256": item["sha256"], "gdc_md5": item.get("gdc_md5"), "immutable": True,
            "receipt": item.get("receipt"),
        })
    for name, role in [
        ("gdc_star_counts_primary_tumor_response.json", "gdc_query_response"),
        ("gdc_star_counts_primary_tumor_manifest.tsv", "gdc_normalized_manifest"),
        ("gdc_cases_clinical_response.json", "public_clinical_metadata"),
    ]:
        path = root / "data/raw/tcga_hnsc" / name
        tcga_files.append({
            "relative_path": path.relative_to(root).as_posix(), "filename": name, "role": role,
            "source_url": "https://api.gdc.cancer.gov/", "version": "GDC Data Release 45.0; API tag 8.5.0",
            "retrieved_at_utc": utc_mtime(path), "bytes": path.stat().st_size, "sha256": sha256(path),
            "immutable": True, "retrieval_time_basis": "local source-file modification time",
        })
    tcga_manifest = {
        "schema_version": "1.0", "study": "tcga_hnsc", "generated_at_utc": generated,
        "source_version": "GDC Data Release 45.0 - 2025-12-04; API tag 8.5.0; commit 8f7c2a51ab0084b216ad1b62a3fae8b945439c53",
        "selection": {"access": "open", "workflow_type": "STAR - Counts", "sample_type": "Primary Tumor"},
        "expected_expression_files": 520, "expected_expression_cases": 520, "clinical_project_cases": 528,
        "phase1_audit": {"relative_path": audit_path.relative_to(root).as_posix(), "sha256": audit_hash},
        "files": tcga_files, "prohibited_material_acquired": False,
    }
    write_json_yaml(root / "data/manifests/tcga_hnsc/data_manifest.yaml", tcga_manifest)
    manifests["tcga_hnsc"] = tcga_manifest
    return manifests


LICENSE_NOTES = {
"radcure": """# RADCURE / ORCESTRA license and citation notes\n\n**Audit date:** 2026-08-07  \n**Status:** usable for research with attribution; artifact terms remain source-controlled.\n\n- TCIA lists the RADCURE Version 4 clinical XLSX (3,346 subjects) under **CC BY 4.0** and requires the dataset citation with DOI `10.7937/J47W-NM11`.\n- The downloaded CT/DICOM/RTSTRUCT archives were deliberately excluded; TCIA lists those imaging materials under controlled-access rules.\n- Zenodo record `10.5281/zenodo.14226536` lists `RADCURE_READII-RADIOMICS_MAE.RDS` as **CC BY 4.0**. The downloaded MD5 matches the publisher value.\n- Redistribution or publication must credit the creators and source, identify changes, and retain the accession/DOI.\n- This file is a provenance note, not legal advice. Re-check the source pages before public redistribution.\n\nAuthoritative pages:\n- `https://www.cancerimagingarchive.net/collection/radcure/`\n- `https://zenodo.org/records/14226536`\n""",
"hancock": """# HANCOCK license and citation notes\n\n**Audit date:** 2026-08-07  \n**Status:** public research use documented; preserve artifact-level caution.\n\n- The HANCOCK data paper identifies the dataset as publicly available and should be cited as Dörrich et al., *Nature Communications* 16, 7163 (2025), DOI `10.1038/s41467-025-62386-6`.\n- The frozen GitHub repository code is released under **Apache License 2.0**.\n- The TCIA HANCOCK mirror lists the histopathology collection under **CC BY 4.0** and requires data citation DOI `10.7937/rcty-5h16`.\n- The external FAU ZIP files used here do not embed a standalone license file. Therefore, treat structured tables, official splits, and TMA density measurements as citation-required source artifacts and re-confirm portal terms before redistributing copies.\n- No WSI/TMA source images, annotations, core images, or UNI encodings were acquired.\n- This file is a provenance note, not legal advice.\n\nAuthoritative pages:\n- `https://www.nature.com/articles/s41467-025-62386-6`\n- `https://github.com/ankilab/HANCOCK_MultimodalDataset`\n- `https://www.cancerimagingarchive.net/collection/hancock/`\n""",
"tcga_hnsc": """# TCGA-HNSC / GDC data-use notes\n\n**Audit date:** 2026-08-07  \n**Status:** open-access files only.\n\n- All 520 expression files in this acquisition are marked `open` by GDC and use the STAR-counts workflow for Primary Tumor samples.\n- GDC open-data users must not attempt participant re-identification and must acknowledge the dataset/accession and the NIH-designated repository in publications and presentations.\n- Controlled-access genomic files were explicitly prohibited and were not downloaded.\n- Keep TCGA case identifiers inside governed, Git-ignored data areas; tracked reports contain counts and hashes rather than raw ID lists.\n- This file is a provenance note, not legal advice.\n\nAuthoritative pages:\n- `https://gdc.cancer.gov/about-gdc/gdc-policies`\n- `https://gdc.cancer.gov/analyze-data/data-analysis-policies`\n- `https://portal.gdc.cancer.gov/projects/TCGA-HNSC`\n""",
"gse65858": """# GSE65858 / GPL10558 data-use notes\n\n**Audit date:** 2026-08-07  \n**Status:** public processed expression and platform annotation.\n\n- NCBI GEO states that it places no restrictions on use or distribution of GEO data, while warning that submitters may retain patent, copyright, or other rights in submitted material.\n- Cite the GEO repository, accession `GSE65858`, platform `GPL10558`, and the original study publication.\n- Only the processed series matrix and platform annotation were acquired; raw array files were excluded.\n- This file is a provenance note, not legal advice.\n\nAuthoritative pages:\n- `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE65858`\n- `https://www.ncbi.nlm.nih.gov/geo/info/disclaimer.html`\n- `https://www.ncbi.nlm.nih.gov/geo/info/linking.html`\n""",
"gse41613": """# GSE41613 / GPL570 data-use notes\n\n**Audit date:** 2026-08-07  \n**Status:** public processed expression and platform annotation.\n\n- NCBI GEO states that it places no restrictions on use or distribution of GEO data, while warning that submitters may retain patent, copyright, or other rights in submitted material.\n- Cite the GEO repository, accession `GSE41613`, platform `GPL570`, and the original study publication.\n- Only the processed series matrix and platform annotation were acquired; raw CEL files were excluded.\n- This cohort is HPV-negative OSCC and is reserved for sensitivity analysis rather than a general HNSCC external test.\n- This file is a provenance note, not legal advice.\n\nAuthoritative pages:\n- `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE41613`\n- `https://www.ncbi.nlm.nih.gov/geo/info/disclaimer.html`\n- `https://www.ncbi.nlm.nih.gov/geo/info/linking.html`\n""",
}


def write_license_notes(root: Path) -> None:
    for study, text in LICENSE_NOTES.items():
        path = root / f"data/manifests/{study}/license_notes.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def freeze_sources(root: Path) -> dict[str, int]:
    raw_root = root / "data/raw"
    frozen = 0
    skipped_receipts = 0
    skipped_placeholders = 0
    for path in sorted(p for p in raw_root.rglob("*") if p.is_file()):
        if path.name == ".gitkeep":
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
            skipped_placeholders += 1
            continue
        if path.name.endswith(".receipt.json"):
            skipped_receipts += 1
            continue
        os.chmod(path, stat.S_IREAD)
        frozen += 1
    return {
        "source_files_read_only": frozen,
        "mutable_receipts": skipped_receipts,
        "mutable_placeholders": skipped_placeholders,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    manifests = build_manifests(root)
    write_license_notes(root)
    freeze = freeze_sources(root)
    result = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifests": {study: len(manifest["files"]) for study, manifest in manifests.items()},
        **freeze,
    }
    path = root / "data/manifests/phase1_finalization_receipt.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())