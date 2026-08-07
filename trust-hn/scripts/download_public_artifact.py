"""Download one Phase 1 artifact after allowlist and size-policy checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trust_hn.data.acquisition import AcquisitionPolicy, download_public_artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--study", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-bytes", type=int)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs" / "download_policy.json",
    )
    args = parser.parse_args()
    receipt = download_public_artifact(
        url=args.url,
        role=args.role,
        study=args.study,
        filename=args.filename,
        project_root=args.project_root.resolve(),
        policy=AcquisitionPolicy.load(args.policy),
        expected_sha256=args.expected_sha256,
        expected_bytes=args.expected_bytes,
    )
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())