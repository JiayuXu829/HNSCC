"""U7R2: freeze and audit the RADCURE external characterization package.

This stage does not claim formal current-V1R external confirmation.  It packages the
already completed Phase 7 outcome-free prediction generation and post-unseal
aggregate evaluation for the preselected RADCURE held-out test split.  Only
aggregate, tracked metrics are read here; no patient-level prediction file is
copied into the research-study directory.
"""

from __future__ import annotations

# ruff: noqa: E501
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT_REL = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/U7R2_RADCURE_external_characterization"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)

    config_path = root / "configs/phase7_exploratory_benchmarks.json"
    receipt_path = root / "results/manifests/phase7_exploratory_receipt.json"
    prediction_receipt_path = root / "results/manifests/phase7_exploratory_prediction_receipt.json"
    metrics_path = root / "results/metrics/phase7_exploratory/external_metrics.csv"
    comparisons_path = root / "results/metrics/phase7_exploratory/paired_comparisons.csv"
    combined_path = root / "results/metrics/phase7_exploratory/external_benchmark_combined.csv"

    required = [
        config_path,
        receipt_path,
        prediction_receipt_path,
        metrics_path,
        comparisons_path,
        combined_path,
    ]
    missing = [
        str(path.relative_to(root)).replace("\\", "/") for path in required if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(f"missing frozen Phase 7 artifact(s): {missing}")

    phase7_receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    prediction_receipt = json.loads(prediction_receipt_path.read_text(encoding="utf-8-sig"))
    metrics = pd.read_csv(metrics_path)
    comparisons = pd.read_csv(comparisons_path)

    rad = metrics.loc[
        metrics["cohort"].astype(str).eq("RADCURE")
        & metrics["analysis_label"].astype(str).eq("post hoc exploratory benchmark")
    ].copy()
    if set(rad["model"].astype(str)) != {"C1", "C2", "C3", "C4"}:
        raise ValueError("RADCURE external characterization must contain exactly C1-C4")
    if rad["n"].nunique() != 1 or int(rad["n"].iloc[0]) != 626:
        raise ValueError("unexpected RADCURE characterization sample count")
    if rad["events"].nunique() != 1 or int(rad["events"].iloc[0]) != 110:
        raise ValueError("unexpected RADCURE characterization event count")
    if not (rad["coverage"].astype(float) == 1.0).all():
        raise ValueError("RADCURE characterization does not have complete coverage")

    rad_pairs = comparisons.loc[
        comparisons["analysis_label"].astype(str).eq("post hoc exploratory benchmark")
        & comparisons["cohort"].astype(str).eq("RADCURE")
        & comparisons["comparison"].astype(str).str.match(r"C[1-4]_vs_B[56]")
    ].copy()

    protocol = {
        "schema_version": "0.1",
        "stage": "U7R2_RADCURE_EXTERNAL_CHARACTERIZATION",
        "status": "FROZEN_AND_COMPLETED",
        "frozen_on": "2026-09-03",
        "analysis_label": "post_hoc_exploratory_external_characterization",
        "purpose": (
            "Characterize transportability of explicitly adapted clinical/radiomics survival comparators "
            "on the RADCURE held-out test split without upgrading the result to current-V1R confirmation."
        ),
        "cohort": {
            "name": "RADCURE",
            "role": "sealed_test",
            "sample_size": 626,
            "events": 110,
            "source_scope": "independent data source relative to HANCOCK, but same-source held-out split for Phase 7 comparator training",
            "data_contract": "clinical plus radiomics; not the frozen V1R blood/ICD/TMA contract",
            "outcome_status": "previously consumed in historical Phase 6; not outcome-untouched",
        },
        "locked_comparison_set": {
            "new_comparators": {
                "C1": "Gradient Boosting Survival Analysis on direct clinical-plus-radiomics features",
                "C2": "XGBoost-Cox on direct clinical-plus-radiomics features",
                "C3": "Cross-fitted late-fusion stacking of clinical and radiomics Cox models",
                "C4": "Missing-aware direct-fusion elastic-net Cox with explicit missingness indicators",
            },
            "references": {
                "B5": "Direct clinical plus modality elastic-net Cox",
                "B6": "Legacy Phase 6 TRUST-HN stacked residual fusion comparator",
            },
            "external_refit": False,
            "external_tuning": False,
            "winner_selection_after_readout": False,
        },
        "locked_estimands": [
            "24-month IPCW Brier (lower is better)",
            "Uno C (higher is better)",
            "Harrell C (higher is better)",
            "24-month time-dependent AUC (higher is better)",
            "calibration-in-the-large: closer to 0 is better",
            "calibration slope: closer to 1 is better",
            "coverage: 1.0 required for complete evaluation",
        ],
        "governance": {
            "patient_rows_read_in_this_packaging_step": False,
            "outcome_columns_read_in_this_packaging_step": False,
            "predictions_regenerated_in_this_packaging_step": False,
            "prediction_generation_outcome_free_in_source_phase": bool(
                prediction_receipt.get("outcomes_loaded") is False
            ),
            "phase7_receipt_complete": phase7_receipt.get("status") == "COMPLETE",
            "phase6_outputs_overwritten": phase7_receipt.get("phase6_outputs_overwritten") is False,
            "trust_hn_or_gate_retuned": phase7_receipt.get("trust_hn_or_gate_retuned") is False,
            "formal_current_v1r_confirmation_claim_permitted": False,
            "bridge_or_router_claim_permitted": False,
        },
        "claim_boundary": {
            "allowed": [
                "RADCURE held-out test-split characterization of adapted clinical/radiomics comparators",
                "descriptive discrimination, calibration and coverage transportability signals",
            ],
            "prohibited": [
                "formal current-V1R external validation",
                "formal current-V1R bridge validation",
                "external router validation",
                "silent substitution of radiomics for blood, ICD or TMA",
                "using RADCURE outcomes to tune or select V1R, bridge, router, thresholds or gates",
            ],
        },
        "source_artifacts": {
            "phase7_config": str(config_path.relative_to(root)).replace("\\", "/"),
            "phase7_prediction_receipt": str(prediction_receipt_path.relative_to(root)).replace(
                "\\", "/"
            ),
            "phase7_metrics": str(metrics_path.relative_to(root)).replace("\\", "/"),
            "phase7_paired_comparisons": str(comparisons_path.relative_to(root)).replace("\\", "/"),
        },
    }
    (out / "frozen_u7r2_radcure_external_characterization_protocol.yaml").write_text(
        yaml.safe_dump(protocol, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    result_rows = rad.sort_values("model").to_dict(orient="records")
    pair_rows = rad_pairs.sort_values(["comparison", "metric"]).to_dict(orient="records")
    aggregate = {
        "schema_version": "0.1",
        "stage": protocol["stage"],
        "completed_on": "2026-09-03",
        "status": "COMPLETE_POST_HOC_CHARACTERIZATION",
        "cohort": "RADCURE",
        "n": 626,
        "events": 110,
        "methods": ["C1", "C2", "C3", "C4"],
        "coverage": 1.0,
        "external_prediction_generation_outcomes_loaded": False,
        "formal_current_v1r_external_validation": False,
        "metrics": result_rows,
        "paired_comparisons_vs_B5_or_B6": pair_rows,
        "interpretation": (
            "The RADCURE held-out split provides a positive and informative transportability characterization "
            "for adapted clinical/radiomics comparators, but it does not validate current V1R because the "
            "input contract and cohort/provenance status are not equivalent."
        ),
    }
    (out / "u7r2_radcure_external_characterization_aggregate_results.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )

    audit = """# U7R2 RADCURE external characterization\n\n## Decision\n\nRADCURE was the preselected best available local dataset for an honest external characterization. This stage packages the already completed Phase 7 comparator benchmark; it is **not** formal current-V1R external confirmation.\n\n## Cohort and provenance\n\n- RADCURE held-out test split: **626 patients / 110 events**.\n- The comparator predictions were generated in the source Phase 7 prediction stage before external outcomes were loaded (`outcomes_loaded: false`).\n- This packaging step read only tracked aggregate metrics and receipts; it did not read patient rows or outcome columns, regenerate predictions, retune models, or modify Phase 6 files.\n- The available RADCURE contract is clinical plus radiomics, not the frozen current-V1R blood/ICD/TMA contract. The cohort outcome was also consumed historically, so it is not a pristine outcome-untouched confirmation cohort.\n\n## Aggregate comparator results\n\n| Comparator | IPCW Brier | Uno C | AUC24 | Harrell C | CITL | Slope | Coverage |\n|---|---:|---:|---:|---:|---:|---:|---:|\n"""
    for row in sorted(result_rows, key=lambda item: str(item["model"])):
        audit += (
            f"| {row['model']} | {float(row['ipcw_brier']):.6f} | {float(row['uno_c']):.6f} | "
            f"{float(row['auc_horizon']):.6f} | {float(row['harrell_c']):.6f} | "
            f"{float(row['calibration_in_the_large']):+.6f} | {float(row['calibration_slope']):.6f} | "
            f"{float(row['coverage']):.1%} |\n"
        )
    audit += """\n## Interpretation\n\nThe RADCURE analysis can support a manuscript subsection describing external transportability of an adapted clinical/radiomics comparator set. It cannot support the sentence that current V1R was externally validated, because: (1) the RADCURE inputs do not reproduce the frozen V1R blood/ICD/TMA contract; (2) the RADCURE test split is not a newly acquired outcome-untouched cohort; and (3) the Phase 7 comparator definition is not identical to the current V1R residual-shrinkage ensemble.\n\nThe result therefore remains separate from the core V1R confirmation narrative and should be reported as exploratory/appendix material unless the manuscript explicitly includes a transportability characterization section. No RADCURE outcome is permitted to tune V1R, bridge, router, thresholds or safety gates.\n\n## Artifacts\n\n- `frozen_u7r2_radcure_external_characterization_protocol.yaml`\n- `u7r2_radcure_external_characterization_aggregate_results.json`\n- `u7r2_radcure_external_characterization_audit.md`\n"""
    (out / "u7r2_radcure_external_characterization_audit.md").write_text(audit, encoding="utf-8")

    hash_paths = [*required,
        out / "frozen_u7r2_radcure_external_characterization_protocol.yaml",
        out / "u7r2_radcure_external_characterization_aggregate_results.json",
        out / "u7r2_radcure_external_characterization_audit.md",
    ]
    hashes = {str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in hash_paths}
    (out / "u7r2_radcure_external_characterization_hashes.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {"stage": protocol["stage"], "status": aggregate["status"], "n": 626, "events": 110},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
