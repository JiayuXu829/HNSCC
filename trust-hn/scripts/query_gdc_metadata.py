"""Query GDC open metadata and freeze the raw response plus normalized file manifest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from trust_hn.data.gdc import execute_query, normalize_file_hits, write_tsv
from trust_hn.utils.hashing import sha256_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-tsv", type=Path)
    args = parser.parse_args()
    query = json.loads(args.query.read_text(encoding="utf-8"))
    payload = execute_query(query)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    rows = []
    if args.output_tsv:
        rows = normalize_file_hits(payload)
        write_tsv(args.output_tsv, rows)
    receipt = {
        "queried_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": query["endpoint"],
        "query_sha256": sha256_file(args.query),
        "response_sha256": sha256_file(args.output_json),
        "hits": len(payload.get("data", {}).get("hits", [])),
        "normalized_rows": len(rows),
    }
    receipt_path = args.output_json.with_suffix(args.output_json.suffix + ".receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())