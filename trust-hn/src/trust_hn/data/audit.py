"""Phase 1 source-file registration and checksum audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from trust_hn.utils.hashing import sha256_file


def inventory_files(root: Path) -> Iterable[dict[str, object]]:
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        stat = path.stat()
        yield {
            "relative_path": path.relative_to(root).as_posix(),
            "bytes": stat.st_size,
            "sha256": sha256_file(path),
            "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        }


def write_inventory(source_dir: Path, output_csv: Path) -> int:
    rows = list(inventory_files(source_dir))
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["relative_path", "bytes", "sha256", "modified_utc"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory immutable TRUST-HN source files")
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json-summary", type=Path)
    args = parser.parse_args(argv)
    count = write_inventory(args.source_dir, args.output)
    if args.json_summary:
        args.json_summary.parent.mkdir(parents=True, exist_ok=True)
        args.json_summary.write_text(
            json.dumps({"source_dir": str(args.source_dir), "files": count}, indent=2),
            encoding="utf-8",
        )
    print(f"registered_files={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())