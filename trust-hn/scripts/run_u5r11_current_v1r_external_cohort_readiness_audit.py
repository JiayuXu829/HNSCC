"""U5R11: audit whether any locally available cohort can support a proper current-V1R bridge confirmation.

This is deliberately outcome-blind: it reads only tracked source/manifests and frozen protocol metadata,
never patient rows or outcome columns. It does not train, tune, or evaluate a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT_REL = Path("research_studies/01_pattern_surv_hn/core_backbone/U5R11_current_v1r_external_cohort_readiness_audit")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return yaml.safe_load(f) if path.suffix in {".yaml", ".yml"} else json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)

    protocol = {
        "schema_version": "0.1",
        "stage": "U5R11_CURRENT_V1R_EXTERNAL_COHORT_READINESS_AUDIT",
        "status": "FROZEN_AND_COMPLETED",
        "frozen_on": "2026-08-27",
        "analysis_label": "pre_outcome_access_feasibility_audit",
        "purpose": "Determine whether an already available cohort can support formal current-V1R fixed-bridge confirmation.",
        "current_v1r_input_contract": {
            "anchor": ["age_at_initial_diagnosis", "sex", "smoking_status", "primary_tumor_site", "grading", "hpv_association_p16", "resection_status", "pT_stage", "pN_stage"],
            "optional_modalities": ["blood", "ICD", "TMA_cell_density"],
            "prediction_definition": "PATTERN-Surv-HN V1R residual-shrinkage ensemble",
            "required_prediction_freeze_before_outcome_access": True,
        },
        "candidate_cohorts": [
            {
                "cohort": "HANCOCK_OOD_TEST",
                "source_role": "current-V1R compatible multimodal cohort",
                "contract_compatible": True,
                "outcome_untouched_for_new_confirmation": False,
                "eligible_for_formal_confirmation": False,
                "reason": "The cohort was used in the prior locked raw-V1R confirmation and later post-unseal bridge characterizations.",
            },
            {
                "cohort": "RADCURE",
                "source_role": "clinical plus radiomics source",
                "contract_compatible": False,
                "outcome_untouched_for_new_confirmation": False,
                "eligible_for_formal_confirmation": False,
                "reason": "Available artifacts do not provide the frozen V1R blood/ICD/TMA input contract; outcomes were already used in historical Phase 6.",
            },
            {
                "cohort": "GSE65858",
                "source_role": "transcriptomic external cohort with legacy B6 prediction",
                "contract_compatible": False,
                "outcome_untouched_for_new_confirmation": False,
                "eligible_for_formal_confirmation": False,
                "reason": "Available prediction is legacy Phase 6 B6 risk rather than current V1R, and outcomes were historically consumed.",
            },
            {
                "cohort": "GSE41613",
                "source_role": "transcriptomic sensitivity cohort with legacy B6 prediction",
                "contract_compatible": False,
                "outcome_untouched_for_new_confirmation": False,
                "eligible_for_formal_confirmation": False,
                "reason": "Available prediction is legacy Phase 6 B6 risk rather than current V1R, and outcomes were historically consumed.",
            },
            {
                "cohort": "TCGA-HNSC",
                "source_role": "primary-tumor expression plus public clinical metadata",
                "contract_compatible": False,
                "outcome_untouched_for_new_confirmation": "not_certified",
                "eligible_for_formal_confirmation": False,
                "reason": "Available artifacts provide expression and clinical metadata, not the frozen postoperative V1R multimodal contract; no current-V1R prediction artifact exists.",
            },
        ],
        "governance": {
            "outcomes_read": False,
            "patient_rows_read": False,
            "model_trained": False,
            "bridge_refit": False,
            "router_trained": False,
            "cohort_selected_after_outcome_readout": False,
            "existing_phase6_artifacts_modified": False,
            "formal_confirmation_claim_permitted": False,
        },
        "decision": {
            "compatible_candidates": 1,
            "certified_outcome_untouched_compatible_candidates": 0,
            "formal_confirmation_can_run_from_current_local_artifacts": False,
            "next_required_action": "Acquire or designate a genuinely new cohort with the frozen V1R anchor/optional-modality contract, then seal current-V1R predictions before outcome access.",
        },
    }
    (out / "frozen_u5r11_readiness_protocol.yaml").write_text(yaml.safe_dump(protocol, sort_keys=False, allow_unicode=True), encoding="utf-8")

    aggregate = {
        "schema_version": "0.1",
        "stage": protocol["stage"],
        "evaluated_on": "2026-08-27",
        "candidate_count": len(protocol["candidate_cohorts"]),
        "compatible_candidate_count": protocol["decision"]["compatible_candidates"],
        "untouched_compatible_candidate_count": protocol["decision"]["certified_outcome_untouched_compatible_candidates"],
        "formal_confirmation_executable": False,
        "outcomes_read": False,
        "patient_rows_read": False,
        "cohort_results": protocol["candidate_cohorts"],
        "interpretation": "No locally available cohort simultaneously satisfies current V1R input compatibility and certified outcome-untouched status. U5R10 remains legacy-B6 transport characterization; a new cohort is required for formal current-V1R bridge confirmation.",
    }
    (out / "u5r11_readiness_aggregate_results.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    audit = """# U5R11 current-V1R external cohort readiness audit

## Scope

This stage was executed on 2026-08-27 before any new outcome access. It is a feasibility/readiness experiment, not a performance evaluation. Only frozen protocol metadata and source manifests were inspected; no patient-level rows or outcome columns were read.

## Frozen eligibility for a formal confirmation

A candidate must provide the current PATTERN-Surv-HN V1R prediction contract: the postoperative clinical-pathological anchor plus the optional blood, ICD and TMA cell-density modalities. The current V1R model and the fixed bridge must be sealed before opening outcomes. Legacy B6 predictions cannot substitute for current V1R predictions.

## Result

No locally available cohort meets both requirements:

- HANCOCK OOD is compatible with current V1R, but its outcomes were already opened for the prior raw-V1R confirmation and subsequent bridge characterizations.
- RADCURE has clinical/radiomics artifacts but not the frozen V1R blood/ICD/TMA contract, and its outcomes were used historically.
- GSE65858 and GSE41613 have transcriptomic/legacy-B6 artifacts, not current V1R inputs or predictions; their outcomes were used historically.
- TCGA-HNSC has expression and clinical metadata but no current-V1R-compatible multimodal prediction artifact; untouched status was not certified in this audit.

Therefore, the count of certified outcome-untouched current-V1R-compatible cohorts is **zero**. No current-V1R bridge prediction or metric was generated, and no result is added to the positive manuscript-material directory.

## Claim boundary

This is not evidence that the bridge fails. It is evidence that the current local data inventory cannot support the requested formal confirmation without a new compatible cohort. The next valid experiment is cohort acquisition/designation, pre-outcome freezing of current-V1R prediction generation plus the fixed bridge and estimands, prediction sealing, and only then outcome evaluation.
"""
    (out / "u5r11_readiness_audit.md").write_text(audit, encoding="utf-8")

    manifest_inputs = [
        root / "research_studies/01_pattern_surv_hn/registry.yaml",
        root / "research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_residual_shrinkage_rescue/frozen_v1r_rescue_spec.yaml",
        root / "data/manifests/source_registry.yaml",
        root / "data/manifests/radcure/data_manifest.yaml",
        root / "data/manifests/hancock/data_manifest.yaml",
        root / "data/manifests/gse65858/data_manifest.yaml",
        root / "data/manifests/gse41613/data_manifest.yaml",
        root / "data/manifests/tcga_hnsc/data_manifest.yaml",
    ]
    hashes = {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in manifest_inputs if p.exists()}
    hashes.update({
        str((out / "frozen_u5r11_readiness_protocol.yaml").relative_to(root)).replace("\\", "/"): sha256(out / "frozen_u5r11_readiness_protocol.yaml"),
        str((out / "u5r11_readiness_aggregate_results.json").relative_to(root)).replace("\\", "/"): sha256(out / "u5r11_readiness_aggregate_results.json"),
        str((out / "u5r11_readiness_audit.md").relative_to(root)).replace("\\", "/"): sha256(out / "u5r11_readiness_audit.md"),
    })
    (out / "u5r11_readiness_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
