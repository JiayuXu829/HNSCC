"""Development-only post-hoc V1 residual-shrinkage rescue evaluation."""
from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
import yaml

from trust_hn.pattern_surv_hn.v0_clinical_anchor import assert_aggregate_only
from trust_hn.pattern_surv_hn.v1_development_cv import (
    DEFAULT_ARCHITECTURE_SPEC_RELATIVE,
    DEFAULT_GATE_RELATIVE,
    DEFAULT_V0_OOF_RELATIVE,
    DEFAULT_V0_SPEC_RELATIVE,
    _json_safe,
    _sha256,
    apply_complexity_gate,
    run_u2_experiment,
)

ANALYSIS_DATE = "2026-08-19"
DEFAULT_RESCUE_DIR = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U2_V1R_residual_shrinkage_rescue"
)
DEFAULT_RESCUE_SPEC = DEFAULT_RESCUE_DIR / "frozen_v1r_rescue_spec.yaml"
DEFAULT_RESCUE_GATE = DEFAULT_RESCUE_DIR / "frozen_v1r_exploratory_gate.yaml"
DEFAULT_RESCUE_AUDIT = DEFAULT_RESCUE_DIR / "aggregate_u2_v1r_rescue_audit.json"
DEFAULT_RESCUE_OUTPUT = Path("results/predictions/pattern_surv_hn/U2_V1R")


def _relabel_v1_result_as_v1r(result: dict) -> dict:
    relabeled = copy.deepcopy(result)
    decision = relabeled.get("decision")
    if decision == "V1_EARNS_COMPLEXITY":
        relabeled["decision"] = "V1R_EARNS_COMPLEXITY"
    elif decision == "V1_DOES_NOT_EARN_COMPLEXITY":
        relabeled["decision"] = "V1R_DOES_NOT_EARN_COMPLEXITY"
    return relabeled


def run_v1r_rescue(
    project_root: Path,
    *,
    spec_path: Path | None = None,
    rescue_gate_path: Path | None = None,
    original_gate_path: Path | None = None,
    patient_output_dir: Path | None = None,
    aggregate_audit_path: Path | None = None,
    verbose: bool = False,
) -> dict:
    root = Path(project_root).resolve()
    spec_path = Path(spec_path or root / DEFAULT_RESCUE_SPEC).resolve()
    rescue_gate_path = Path(rescue_gate_path or root / DEFAULT_RESCUE_GATE).resolve()
    original_gate_path = Path(original_gate_path or root / DEFAULT_GATE_RELATIVE).resolve()
    patient_output_dir = Path(patient_output_dir or root / DEFAULT_RESCUE_OUTPUT).resolve()
    aggregate_audit_path = Path(aggregate_audit_path or root / DEFAULT_RESCUE_AUDIT).resolve()

    payload = run_u2_experiment(
        root,
        spec_path=spec_path,
        gate_path=rescue_gate_path,
        v0_spec_path=root / DEFAULT_V0_SPEC_RELATIVE,
        architecture_spec_path=root / DEFAULT_ARCHITECTURE_SPEC_RELATIVE,
        v0_oof_path=root / DEFAULT_V0_OOF_RELATIVE,
        patient_output_dir=patient_output_dir,
        aggregate_audit_path=aggregate_audit_path,
        verbose=verbose,
    )
    oof_path = patient_output_dir / "v1_repeated_nested_oof_predictions.csv"
    oof = pd.read_csv(oof_path, dtype={"native_id": str, "acquisition_pattern": str})
    original_gate = yaml.safe_load(original_gate_path.read_text(encoding="utf-8-sig"))
    original_result = _relabel_v1_result_as_v1r(
        apply_complexity_gate(oof, payload["results"], original_gate)
    )
    rescue_result = _relabel_v1_result_as_v1r(payload["complexity_gate"])

    payload.update({
        "stage_id": "U2_V1R_RESIDUAL_SHRINKAGE_RESCUE_CV",
        "analysis_label": "post_hoc_exploratory_rescue",
        "completed_on": ANALYSIS_DATE,
        "model": {
            "id": "V1R",
            "name": "Clinical_Residual_Deep_Sets_Cox_inner_selected_shrinkage",
            "parameter_count": int(payload["results"]["parameter_count"]),
            "clinical_anchor": "U1.2_V0",
            "architecture_same_as_original_V1": True,
            "residual_scale_selected_inside_inner_CV": True,
        },
        "complexity_gate": {
            "unchanged_original_U2_thresholds_applied_to_V1R": original_result,
            "post_hoc_exploratory_rescue_gate_applied_to_V1R": rescue_result,
            "original_U2_V1_decision_preserved": "V1_DOES_NOT_EARN_COMPLEXITY",
        },
        "governance": {
            **payload["governance"],
            "result_informed_rescue_design": True,
            "original_U2_decision_preserved": True,
            "confirmatory_claim_allowed": False,
            "official_test_outcomes_derived_exposed_or_evaluated": False,
            "external_outcomes_used": False,
        },
        "artifacts": {
            **payload["artifacts"],
            "frozen_rescue_spec": spec_path.relative_to(root).as_posix(),
            "frozen_rescue_spec_sha256": _sha256(spec_path),
            "frozen_rescue_gate": rescue_gate_path.relative_to(root).as_posix(),
            "frozen_rescue_gate_sha256": _sha256(rescue_gate_path),
            "original_frozen_gate": original_gate_path.relative_to(root).as_posix(),
            "original_frozen_gate_sha256": _sha256(original_gate_path),
            "patient_oof_sha256": _sha256(oof_path),
        },
        "limitations": [
            "The original prespecified U2 V1 failure remains unchanged.",
            (
                "The rescue design and exploratory gate were informed by the original "
                "development result."
            ),
            (
                "A rescue-gate pass is not confirmatory evidence and cannot be called an "
                "original-gate pass."
            ),
            "Official-test and external outcomes remained sealed and unused.",
            (
                "Independent confirmation is required before superiority, generalization, or "
                "utility claims."
            ),
        ],
    })
    safe_payload = _json_safe(payload)
    assert_aggregate_only(safe_payload)
    aggregate_audit_path.write_text(
        json.dumps(safe_payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return safe_payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--rescue-gate", type=Path)
    parser.add_argument("--original-gate", type=Path)
    parser.add_argument("--patient-output-dir", type=Path)
    parser.add_argument("--aggregate-audit", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    result = run_v1r_rescue(
        args.project_root,
        spec_path=args.spec,
        rescue_gate_path=args.rescue_gate,
        original_gate_path=args.original_gate,
        patient_output_dir=args.patient_output_dir,
        aggregate_audit_path=args.aggregate_audit,
        verbose=args.verbose,
    )
    print(json.dumps(result["complexity_gate"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
