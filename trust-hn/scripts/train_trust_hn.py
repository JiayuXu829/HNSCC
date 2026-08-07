"""Run the authorized Phase 4 TRUST-HN development experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trust_hn.evaluation.phase4 import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--phase", choices=["phase4"], required=True)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run HANCOCK seed 17 with two bootstrap models under .runtime/phase4_smoke.",
    )
    args = parser.parse_args(argv)
    if args.smoke:
        result = run(
            args.project_root,
            studies=["HANCOCK"],
            seeds=[17],
            bootstrap_size=2,
            output_root=args.project_root / ".runtime/phase4_smoke",
            write_receipt=True,
        )
    else:
        result = run(args.project_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if int(result["failed_runs"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
