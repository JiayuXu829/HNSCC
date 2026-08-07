"""Generate Phase 1 audit artifacts from a delimited patient-level table."""

from __future__ import annotations

import argparse
from pathlib import Path

from trust_hn.data.profile import run_profile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    summary = run_profile(args.table, args.spec, args.output_dir)
    print(f"rows={summary['n_rows']} columns={summary['n_columns']} go_no_go={summary['go_no_go']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())