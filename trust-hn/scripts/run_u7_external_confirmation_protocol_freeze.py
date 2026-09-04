"""U7 freeze of the future current-V1R external confirmation protocol.

This is a pre-outcome-access readiness/freeze step. It reads only aggregate protocol metadata,
source manifests and aggregate audit outputs; it does not read patient-level rows or outcomes.
No external evaluation is performed because no qualifying local cohort is available.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from datetime import date

import yaml

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "research_studies/01_pattern_surv_hn"
OUT_REL = Path("research_studies/01_pattern_surv_hn/core_backbone/U7_external_confirmation_protocol_freeze")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_any(path: Path):
    with path.open(encoding="utf-8") as f:
        text = f.read()
    try:
        return yaml.safe_load(text)
    except Exception:
        return json.loads(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.root.resolve()
    study = root / "research_studies/01_pattern_surv_hn"
    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)

    v1r_protocol = study / "core_backbone/U2_V1R_confirmation_protocol/frozen_confirmation_protocol.yaml"
    bridge_protocol = study / "core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/frozen_beta09_logloss_bridge_candidate_protocol.yaml"
    router_protocol = study / "core_backbone/U6R1_patient_level_router_aggregation_exploration/frozen_u6r1_router_protocol.yaml"
    readiness = study / "core_backbone/U5R11_current_v1r_external_cohort_readiness_audit/u5r11_readiness_aggregate_results.json"
    cohort_manifest = root / "data/manifests/sealed/phase6_cohort_set_manifest.json"
    for p in (v1r_protocol, bridge_protocol, router_protocol, readiness, cohort_manifest):
        if not p.exists():
            raise FileNotFoundError(p)

    readiness_data = load_any(readiness)
    protocol = {
        "schema_version": "0.1",
        "stage": "U7_CURRENT_V1R_EXTERNAL_CONFIRMATION_PROTOCOL_FREEZE",
        "status": "FROZEN_PENDING_NEW_OUTCOME_UNTOUCHED_COHORT",
        "frozen_on": "2026-09-02",
        "analysis_label": "pre_outcome_access_external_confirmation_readiness",
        "purpose": "Freeze the protocol and intake criteria for the next genuinely independent current-V1R-compatible outcome-untouched external cohort.",
        "current_execution_status": {
            "local_qualifying_cohort_available": False,
            "patient_rows_read_in_this_step": False,
            "outcome_columns_read_in_this_step": False,
            "external_evaluation_executed": False,
            "reason": "U5R11 found zero certified outcome-untouched cohorts compatible with the current V1R input contract."
        },
        "primary_external_estimand": {
            "name": "delta_uno_c_24m",
            "definition": "UnoC24_V1R_minus_UnoC24_V0",
            "favourable_direction": "positive",
            "inference": "paired patient-level bootstrap, 2000 replicates"
        },
        "key_safety_estimand": {
            "name": "delta_ipcw_brier_24m",
            "definition": "IPCW_Brier24_V1R_minus_IPCW_Brier24_V0",
            "favourable_direction": "negative",
            "no_harm_boundary": 0.005
        },
        "secondary_estimands": [
            "time-dependent AUC at 24 months",
            "Harrell C",
            "CITL and calibration slope without refit",
            "supported-pattern worst Brier regret",
            "coverage and exact empty-set fallback"
        ],
        "locked_primary_models": {
            "V0": "reuse frozen clinical-pathological anchor and exact fallback",
            "V1R": "reuse approved shrinkage-controlled residual Deep Sets Cox artifact and matched 25-member ensemble",
            "no_architecture_search": True,
            "no_hyperparameter_reselection": True,
            "no_post_unseal_refit": True
        },
        "secondary_layers": {
            "fixed_bridge": {
                "status": "secondary_only_if_current_V1R_prediction_definition_is_identical",
                "formula": "p_bridge = sigmoid(alpha_dev + 0.90 * logit(p_V1R))",
                "alpha_dev": -0.14503379856995471,
                "beta": 0.9,
                "no_refit": True,
                "not_a_replacement_for_primary_raw_V1R_evaluation": True
            },
            "router": {
                "status": "deferred_exploratory_only",
                "reason": "U6/U6R1 development signals were uncertain and below direct raw V1R; router is not included in the primary external confirmation claim.",
                "no_external_router_claim": True
            }
        },
        "cohort_intake_gate": {
            "must_be_new": True,
            "must_be_outcome_untouched_until_prediction_seal": True,
            "must_match_postoperative_prediction_time_contract": True,
            "must_support_current_v1r_modalities": ["clinical-pathological anchor", "blood", "ICD", "TMA"],
            "must_have_predeclared_endpoint": "overall survival with days-to-event/censoring and death indicator",
            "must_have_documented_provenance": True,
            "must_have_no_prior_use_in_model_or_bridge_tuning": True,
            "ineligible_if_legacy_b6_only": True,
            "ineligible_if_outcomes_previously_consumed": True
        },
        "execution_order": [
            "snapshot and hash cohort manifest",
            "approve this frozen protocol",
            "generate current V0/V1R predictions without reading outcomes",
            "seal predictions, code, dependencies and hashes",
            "independently audit the seal",
            "unseal outcomes",
            "evaluate only the locked estimands and all prespecified safety summaries",
            "report primary raw V1R result before any secondary bridge/router characterization"
        ],
        "prohibited": [
            "using an already-consumed cohort as pristine confirmation",
            "changing V1R architecture or preprocessing after outcome access",
            "fitting or refitting the bridge on external outcomes",
            "training or selecting a router using external outcomes before primary readout",
            "dropping patients because the result is unfavorable",
            "promoting legacy B6 characterization to current V1R confirmation"
        ],
        "source_protocols": {
            "v1r": str(v1r_protocol.relative_to(root)).replace("\\", "/"),
            "fixed_bridge": str(bridge_protocol.relative_to(root)).replace("\\", "/"),
            "router_exploration": str(router_protocol.relative_to(root)).replace("\\", "/"),
            "prior_readiness_audit": str(readiness.relative_to(root)).replace("\\", "/"),
            "sealed_cohort_manifest": str(cohort_manifest.relative_to(root)).replace("\\", "/")
        }
    }

    cohort_table = [
        {"cohort": "HANCOCK OOD", "current_v1r_contract": True, "outcome_untouched_for_new_confirmation": False, "decision": "ineligible_already_consumed", "note": "Used for raw V1R confirmation and post-unseal bridge characterization."},
        {"cohort": "RADCURE", "current_v1r_contract": False, "outcome_untouched_for_new_confirmation": False, "decision": "ineligible_contract_mismatch", "note": "Available artifacts lack the frozen blood/ICD/TMA current-V1R contract."},
        {"cohort": "GSE65858", "current_v1r_contract": False, "outcome_untouched_for_new_confirmation": False, "decision": "ineligible_legacy_prediction_definition", "note": "Legacy B6 risk characterization; historical outcomes already consumed."},
        {"cohort": "GSE41613", "current_v1r_contract": False, "outcome_untouched_for_new_confirmation": False, "decision": "ineligible_legacy_prediction_definition", "note": "Legacy B6 risk characterization; historical outcomes already consumed."},
        {"cohort": "TCGA-HNSC", "current_v1r_contract": False, "outcome_untouched_for_new_confirmation": False, "decision": "ineligible_no_current_v1r_prediction_contract", "note": "Expression/clinical metadata without current-V1R-compatible prediction artifact."}
    ]
    aggregate = {
        "stage": protocol["stage"],
        "evaluated_on": "2026-09-02",
        "local_candidate_cohorts": cohort_table,
        "candidate_cohorts": len(cohort_table),
        "current_v1r_compatible_cohorts": sum(x["current_v1r_contract"] for x in cohort_table),
        "new_outcome_untouched_compatible_cohorts": sum(x["current_v1r_contract"] and x["outcome_untouched_for_new_confirmation"] for x in cohort_table),
        "formal_external_evaluation_executed": False,
        "prediction_generation_executed": False,
        "outcomes_read": False,
        "patient_rows_read": False,
        "decision": "protocol_frozen_pending_new_cohort",
        "paper_narrative_position": "raw V1R directional confirmation is the last completed efficacy step; bridge portability and adaptive routing remain unconfirmed extensions"
    }
    (out / "frozen_u7_external_confirmation_protocol.yaml").write_text(yaml.safe_dump(protocol, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (out / "u7_external_cohort_intake_table.json").write_text(json.dumps(cohort_table, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "u7_external_confirmation_readiness_aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    audit = """# U7 current-V1R external confirmation protocol freeze audit

- This stage froze the protocol and cohort intake gate for a future formal external confirmation.
- Only aggregate protocol metadata, prior aggregate readiness results and sealed cohort-manifest metadata were inspected.
- No patient-level rows or outcome columns were read; no predictions were generated; no external evaluation was executed.
- The primary external claim remains raw V1R versus V0. The fixed bridge is secondary and conditional on an identical current-V1R prediction definition. The router remains deferred exploratory material.
- U5R11 found no currently executable local cohort satisfying both the current-V1R input contract and certified outcome-untouched provenance.

## Claim boundary

This artifact is a protocol/readiness freeze, not an external result. It cannot be cited as evidence of external validity, calibration portability, clinical utility or deployment readiness.
"""
    (out / "u7_external_confirmation_audit.md").write_text(audit, encoding="utf-8")
    report = """# U7 current-V1R external confirmation protocol freeze completed

**Date:** 2026-09-02  
**Status:** protocol frozen; execution pending a qualifying new cohort

## Purpose

U6R1 exhausted the useful local development-only router refinement that can be performed without a new cohort. The next scientifically decisive step is not another post-hoc router search; it is a genuinely independent current-V1R external confirmation. U7 therefore freezes the intake criteria and analysis order before a qualifying cohort is selected.

## Readiness result

The local inventory still contains no cohort that is simultaneously current-V1R-compatible and certified outcome-untouched for a new confirmation. Therefore no patient rows, outcome columns, predictions or external metrics were generated in U7.

## Frozen paper-facing order

1. Primary: locked raw V1R versus V0 discrimination and Brier comparison.
2. Secondary: fixed bridge only if the new cohort uses the identical current-V1R prediction definition; no bridge refit.
3. Exploratory: router remains deferred and cannot be promoted before independent validation.

This freeze completes the protocol-design portion of the story, but not the external-validation result portion.

## Artifacts

- `core_backbone/U7_external_confirmation_protocol_freeze/frozen_u7_external_confirmation_protocol.yaml`
- `core_backbone/U7_external_confirmation_protocol_freeze/u7_external_cohort_intake_table.json`
- `core_backbone/U7_external_confirmation_protocol_freeze/u7_external_confirmation_readiness_aggregate.json`
- `core_backbone/U7_external_confirmation_protocol_freeze/u7_external_confirmation_audit.md`
- `scripts/run_u7_external_confirmation_protocol_freeze.py`
"""
    (study / "reports/2026-09-02_step_U7_external_confirmation_protocol_freeze_completed.md").write_text(report, encoding="utf-8")

    to_hash = [out / n for n in ("frozen_u7_external_confirmation_protocol.yaml", "u7_external_cohort_intake_table.json", "u7_external_confirmation_readiness_aggregate.json", "u7_external_confirmation_audit.md")]
    sources = [v1r_protocol, bridge_protocol, router_protocol, readiness, cohort_manifest]
    hashes = {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in [*sources, *to_hash]}
    (out / "u7_external_confirmation_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

