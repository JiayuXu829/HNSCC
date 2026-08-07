"""GDC metadata query helpers for open-access TCGA-HNSC Phase 1 audit."""

from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Mapping, Sequence


class GDCQueryError(RuntimeError):
    pass


def build_post_body(query: Mapping[str, object]) -> bytes:
    payload = {key: value for key, value in query.items() if key != "endpoint"}
    if "filters" in payload and not isinstance(payload["filters"], str):
        payload["filters"] = json.dumps(payload["filters"], separators=(",", ":"))
    return urllib.parse.urlencode(payload).encode("utf-8")


def execute_query(query: Mapping[str, object]) -> dict[str, object]:
    endpoint = str(query.get("endpoint", ""))
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https" or parsed.hostname != "api.gdc.cancer.gov":
        raise GDCQueryError("GDC query endpoint must be https://api.gdc.cancer.gov")
    request = urllib.request.Request(
        endpoint,
        data=build_post_body(query),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "TRUST-HN/0.1 Phase1Audit",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or "data" not in payload:
        raise GDCQueryError("unexpected GDC response")
    return payload


def _flatten_case_ids(cases: object) -> tuple[str, str, str]:
    if not isinstance(cases, list):
        return "", "", ""
    case_ids: list[str] = []
    submitter_ids: list[str] = []
    sample_types: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        if case.get("case_id"):
            case_ids.append(str(case["case_id"]))
        if case.get("submitter_id"):
            submitter_ids.append(str(case["submitter_id"]))
        samples = case.get("samples", [])
        if isinstance(samples, list):
            for sample in samples:
                if isinstance(sample, dict) and sample.get("sample_type"):
                    sample_types.append(str(sample["sample_type"]))
    return ";".join(sorted(set(case_ids))), ";".join(sorted(set(submitter_ids))), ";".join(sorted(set(sample_types)))


def normalize_file_hits(payload: Mapping[str, object]) -> list[dict[str, object]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise GDCQueryError("response data is missing")
    hits = data.get("hits")
    if not isinstance(hits, list):
        raise GDCQueryError("response hits are missing")
    rows = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        case_ids, case_submitter_ids, sample_types = _flatten_case_ids(hit.get("cases"))
        analysis = hit.get("analysis") if isinstance(hit.get("analysis"), dict) else {}
        rows.append(
            {
                "file_id": hit.get("file_id") or hit.get("id") or "",
                "file_name": hit.get("file_name", ""),
                "md5sum": hit.get("md5sum", ""),
                "file_size": hit.get("file_size", ""),
                "data_format": hit.get("data_format", ""),
                "access": hit.get("access", ""),
                "workflow_type": analysis.get("workflow_type", ""),
                "case_ids": case_ids,
                "case_submitter_ids": case_submitter_ids,
                "sample_types": sample_types,
            }
        )
    return sorted(rows, key=lambda row: str(row["file_id"]))


def write_tsv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else [
        "file_id", "file_name", "md5sum", "file_size", "data_format", "access",
        "workflow_type", "case_ids", "case_submitter_ids", "sample_types",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)