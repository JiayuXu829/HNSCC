"""Run the authorized Phase 3 development-only baseline experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trust_hn.evaluation.phase3 import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--phase", choices=["phase3"], required=True)
    args = parser.parse_args(argv)
    result = run(args.project_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
