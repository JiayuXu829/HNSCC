"""Run TRUST-HN Phase 6 preflight, authorization, or locked evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trust_hn.evaluation.phase6_runner import (
    prepare_phase6_predictions,
    register_authorization,
    run_locked_evaluation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--register-authorization", action="store_true")
    actions.add_argument("--consume-and-run", action="store_true")
    parser.add_argument(
        "--approval-token-file", type=Path, default=Path(".runtime/phase6.token")
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)

    if args.preflight:
        result = prepare_phase6_predictions(
            args.project_root,
            seeds=[17] if args.smoke else None,
            bootstrap_size=1 if args.smoke else None,
        )
    elif args.register_authorization:
        if args.smoke:
            parser.error("--smoke cannot be combined with authorization registration")
        result = register_authorization(args.project_root, args.approval_token_file)
    else:
        if args.smoke:
            parser.error("--smoke cannot be combined with locked evaluation")
        result = run_locked_evaluation(args.project_root, args.approval_token_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
