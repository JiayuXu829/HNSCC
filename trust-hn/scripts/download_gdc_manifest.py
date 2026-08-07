"""Download the frozen open-access GDC file manifest with resume and MD5 checks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trust_hn.data.acquisition import AcquisitionPolicy, AcquisitionPolicyError, download_public_artifact


def md5_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.md5()  # noqa: S324 - GDC publishes MD5 for transfer-integrity checks.
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        raise ValueError("GDC manifest is empty")
    required = {
        "file_id", "file_name", "md5sum", "file_size", "access",
        "workflow_type", "case_submitter_ids", "sample_types",
    }
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"GDC manifest missing columns: {sorted(missing)}")
    seen: set[str] = set()
    for row in rows:
        file_id = row["file_id"]
        if not file_id or file_id in seen:
            raise ValueError(f"missing or duplicate GDC file_id: {file_id!r}")
        seen.add(file_id)
        if row["access"] != "open":
            raise AcquisitionPolicyError(f"non-open GDC file rejected: {file_id}")
        if row["workflow_type"] != "STAR - Counts":
            raise AcquisitionPolicyError(f"unexpected workflow rejected: {file_id}")
        if row["sample_types"] != "Primary Tumor":
            raise AcquisitionPolicyError(f"non-primary-tumor sample rejected: {file_id}")
        if Path(row["file_name"]).name != row["file_name"]:
            raise AcquisitionPolicyError(f"unsafe GDC file name: {row['file_name']!r}")
        if int(row["file_size"]) <= 0:
            raise ValueError(f"invalid GDC file size: {file_id}")
    return rows


def destination_name(row: dict[str, str]) -> str:
    return f"{row['file_id']}__{row['file_name']}"


def download_one(
    row: dict[str, str], project_root: Path, policy: AcquisitionPolicy
) -> dict[str, Any]:
    filename = destination_name(row)
    receipt = download_public_artifact(
        url=f"https://api.gdc.cancer.gov/data/{row['file_id']}",
        role="processed_expression",
        study="tcga_hnsc",
        filename=filename,
        project_root=project_root,
        policy=policy,
        expected_bytes=int(row["file_size"]),
    )
    path = project_root / str(receipt["relative_path"])
    observed_md5 = md5_file(path)
    expected_md5 = row["md5sum"].lower()
    if observed_md5 != expected_md5:
        raise AcquisitionPolicyError(
            f"GDC MD5 mismatch for {row['file_id']}: {observed_md5} != {expected_md5}"
        )
    path.chmod(stat.S_IREAD)
    receipt.update(
        {
            "file_id": row["file_id"],
            "file_name": row["file_name"],
            "gdc_md5": observed_md5,
            "case_submitter_ids": row["case_submitter_ids"],
            "sample_types": row["sample_types"],
        }
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=Path(__file__).resolve().parents[1] / "configs" / "download_policy.json")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    policy = AcquisitionPolicy.load(args.policy)
    rows = load_frozen_rows(args.manifest)
    planned_bytes = sum(int(row["file_size"]) for row in rows)
    if planned_bytes > policy.max_planned_total_bytes:
        raise AcquisitionPolicyError("GDC manifest exceeds total Phase 1 size ceiling")
    if args.workers < 1 or args.workers > 16:
        raise ValueError("workers must be between 1 and 16")

    receipts: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(download_one, row, project_root, policy): row for row in rows}
        completed = 0
        for future in as_completed(futures):
            row = futures[future]
            try:
                receipts.append(future.result())
            except Exception as exc:  # preserve all failures for a resumable rerun
                failures.append({"file_id": row["file_id"], "error": repr(exc)})
            completed += 1
            if completed % 25 == 0 or completed == len(rows):
                print(f"completed={completed}/{len(rows)} failures={len(failures)}", flush=True)

    receipts.sort(key=lambda item: str(item["file_id"]))
    summary = {
        "schema_version": "1.0",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest": args.manifest.as_posix(),
        "requested_files": len(rows),
        "verified_files": len(receipts),
        "planned_bytes": planned_bytes,
        "verified_bytes": sum(int(item["bytes"]) for item in receipts),
        "failures": failures,
        "files": receipts,
    }
    output = args.summary_output or project_root / "data" / "manifests" / "tcga_hnsc_gdc_download_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in summary if key != "files"}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
