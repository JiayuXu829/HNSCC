"""Frozen driver for the T1R transcriptome development cross-validation.

Loads the frozen spec and gate, builds the TCGA transcriptome contract, runs the
development cross-fit, applies the exploratory complexity gate, and writes aggregate-only
audit output. Patient-level OOF predictions go to a git-ignored directory.

This is a post-hoc exploratory method-replication study: Phase 6 TCGA outcomes were already
consumed, so the audit is labelled accordingly and no confirmatory or external-validation
claim is permitted.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import torch
import yaml

from trust_hn.pattern_surv_hn.t1r_development_cv import (
    ANALYSIS_DATE,
    MODEL_ID,
    MODEL_NAME,
    T1RSpec,
    apply_t1r_gate,
    development_cross_fit,
)
from trust_hn.pattern_surv_hn.transcriptome_contract import TranscriptomeContract
from trust_hn.pattern_surv_hn.v0_clinical_anchor import assert_aggregate_only
from trust_hn.pattern_surv_hn.v1_development_cv import _json_safe, _sha256

STAGE_ID = "U8_T1R_TRANSCRIPTOME_DEVELOPMENT_CV"
DEFAULT_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U8_T1R_transcriptome_residual_shrinkage/frozen_t1r_transcriptome_spec.yaml"
)
DEFAULT_GATE_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U8_T1R_transcriptome_residual_shrinkage/frozen_t1r_exploratory_gate.yaml"
)
DEFAULT_AUDIT_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U8_T1R_transcriptome_residual_shrinkage/aggregate_t1r_transcriptome_development_cv_audit.json"
)
DEFAULT_PATIENT_OUTPUT_RELATIVE = Path("results/predictions/pattern_surv_hn/U8_T1R")


def _validate_patient_output_root(root: Path, patient_output_dir: Path) -> None:
    allowed_patient_root = (root / "results/predictions/pattern_surv_hn").resolve()
    if allowed_patient_root not in patient_output_dir.parents:
        raise ValueError(
            "patient-level output must remain under results/predictions/pattern_surv_hn"
        )
    research_root = (root / "research_studies").resolve()
    if research_root == patient_output_dir or research_root in patient_output_dir.parents:
        raise ValueError("patient-level output is forbidden in research_studies")


def run_t1r_experiment(
    project_root: Path,
    *,
    spec_path: Path | None = None,
    gate_path: Path | None = None,
    patient_output_dir: Path | None = None,
    aggregate_audit_path: Path | None = None,
    verbose: bool = False,
):
    root = Path(project_root).resolve()
    spec_path = Path(spec_path or root / DEFAULT_SPEC_RELATIVE).resolve()
    gate_path = Path(gate_path or root / DEFAULT_GATE_RELATIVE).resolve()
    patient_output_dir = Path(
        patient_output_dir or root / DEFAULT_PATIENT_OUTPUT_RELATIVE
    ).resolve()
    aggregate_audit_path = Path(
        aggregate_audit_path or root / DEFAULT_AUDIT_RELATIVE
    ).resolve()
    _validate_patient_output_root(root, patient_output_dir)

    spec = T1RSpec.from_yaml(spec_path)
    gate_payload = yaml.safe_load(gate_path.read_text(encoding="utf-8-sig"))
    torch.use_deterministic_algorithms(spec.deterministic_algorithms)
    torch.set_num_threads(1)

    contract = TranscriptomeContract.from_development(root)
    oof, aggregate = development_cross_fit(contract, spec, verbose=verbose)
    gate_result = apply_t1r_gate(oof, aggregate, gate_payload)

    patient_output_dir.mkdir(parents=True, exist_ok=True)
    oof_path = patient_output_dir / "t1r_repeated_nested_oof_predictions.csv"
    oof.to_csv(oof_path, index=False)

    payload = {
        "schema_version": "0.1", "study_id": "pattern_surv_hn",
        "stage_id": STAGE_ID, "analysis_label": "post_hoc_exploratory_rescue",
        "completed_on": ANALYSIS_DATE,
        "model": {
            "id": MODEL_ID, "name": MODEL_NAME,
            "parameter_count": int(aggregate["parameter_count"]),
            "clinical_anchor": "cross_fitted_elastic_net_cox_7_clinical_vars",
            "residual_head": "two_layer_tanh_mlp_over_transcriptome_top_k_genes",
            "shrinkage": "inner_cv_selected_residual_scale_plus_L2_residual_penalty",
        },
        "estimand": {
            "cohort": "TCGA-HNSC_development", "eligible_n": spec.expected_n,
            "events": spec.expected_events, "horizon_days": spec.horizon_days,
            "transcriptome": "within_sample_gene_ranks_common_gene_intersection",
            "top_k": spec.top_k,
        },
        "cross_fitting": {
            "outer_folds": spec.outer_folds,
            "outer_repetition_seeds": list(spec.outer_repetition_seeds),
            "inner_folds": spec.inner_folds, "oof_rows": len(oof),
            "expected_oof_rows": spec.expected_n * len(spec.outer_repetition_seeds),
            "fold_bound_clinical_preprocessing": True,
            "fold_bound_gene_selection": True,
            "training_fold_Breslow_baseline": True,
        },
        "results": aggregate, "complexity_gate": gate_result,
        "governance": {
            "post_hoc_exploratory": True,
            "outcomes_already_consumed": True,
            "confirmatory_claim_allowed": False,
            "external_validation_claim_allowed": False,
            "phase6_outputs_overwritten": False,
            "external_outcomes_used": False,
            "tracked_artifacts_aggregate_only": True,
            "patient_level_oof_git_ignored": True,
        },
        "artifacts": {
            "frozen_spec": spec_path.relative_to(root).as_posix(),
            "frozen_spec_sha256": _sha256(spec_path),
            "frozen_gate": gate_path.relative_to(root).as_posix(),
            "frozen_gate_sha256": _sha256(gate_path),
            "patient_oof_relative_path": oof_path.relative_to(root).as_posix(),
            "patient_oof_sha256": _sha256(oof_path), "patient_oof_tracked": False,
        },
        "limitations": [
            "Post-hoc exploratory method replication; Phase 6 TCGA outcomes were already seen.",
            "Not a pristine locked confirmation and not external validation.",
            "The acquisition-pattern gate collapses to the single transcriptome-present pattern.",
            "Results are internal development estimates only.",
        ],
    }
    safe_payload = _json_safe(payload)
    assert_aggregate_only(safe_payload)
    aggregate_audit_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_audit_path.write_text(
        json.dumps(safe_payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return safe_payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--patient-output-dir", type=Path)
    parser.add_argument("--aggregate-audit", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    result = run_t1r_experiment(
        args.project_root, spec_path=args.spec, gate_path=args.gate,
        patient_output_dir=args.patient_output_dir,
        aggregate_audit_path=args.aggregate_audit, verbose=args.verbose,
    )
    print(json.dumps(result["complexity_gate"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
