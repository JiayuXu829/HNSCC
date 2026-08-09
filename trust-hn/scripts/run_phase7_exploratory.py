from __future__ import annotations

import argparse
from pathlib import Path

from trust_hn.phase7.runner import (
    evaluate_external_benchmark,
    finalize_phase7_receipt,
    generate_external_predictions,
    run_all,
    run_development_benchmark,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the explicitly post-hoc exploratory Phase 7 comparator benchmark."
    )
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--stage",
        choices=("all", "development", "predict-external", "evaluate-external", "finalize"),
        default="all",
    )
    args = parser.parse_args()
    root = args.project_root.resolve()
    if args.stage == "all":
        receipt = run_all(root)
        print(f"Phase 7 status: {receipt['status']}")
    elif args.stage == "development":
        _, summary = run_development_benchmark(root)
        print(f"Development summary rows: {len(summary)}")
    elif args.stage == "predict-external":
        predictions = generate_external_predictions(root)
        print(f"Aggregate external prediction rows: {len(predictions)}")
    elif args.stage == "evaluate-external":
        metrics, comparisons = evaluate_external_benchmark(root)
        print(f"External metrics: {len(metrics)}; paired comparisons: {len(comparisons)}")
    else:
        receipt = finalize_phase7_receipt(root)
        print(f"Phase 7 status: {receipt['status']}")


if __name__ == "__main__":
    main()
