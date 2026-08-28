# U5R11 current-V1R external cohort readiness audit completed

**Date:** 2026-08-27  
**Status:** completed; no executable formal confirmation cohort found

## Objective

Before attempting another external bridge validation, determine whether any locally available cohort simultaneously satisfies the current PATTERN-Surv-HN V1R input contract and certified outcome-untouched provenance.

## Execution safeguards

This was a pre-outcome-access feasibility audit. Only frozen protocol metadata and source manifests were inspected. No patient-level rows, outcome columns, model training, bridge refitting, router training, cohort selection after readout, or modification of any frozen Phase 6 artifact occurred.

## Aggregate result

| Quantity | Result |
|---|---:|
| Candidate cohorts inspected | 5 |
| Current-V1R-compatible cohorts | 1 (HANCOCK OOD) |
| Certified outcome-untouched and compatible cohorts | 0 |
| Formal current-V1R bridge confirmation executable from local artifacts | No |

HANCOCK OOD is compatible with the multimodal V1R contract, but it was already used in the prior raw-V1R confirmation and post-unseal bridge characterizations. RADCURE contains clinical/radiomics artifacts but not the frozen blood/ICD/TMA contract. GSE65858 and GSE41613 contain transcriptomic/legacy-B6 artifacts rather than current V1R inputs or predictions. TCGA-HNSC contains expression and clinical metadata but no current-V1R-compatible prediction artifact.

## Interpretation

The absence of an executable cohort is a data-readiness limitation, not a negative bridge result. U5R10 remains a positive post-unseal characterization of the fixed transform applied to legacy B6 risk, and it cannot be upgraded to formal current-V1R external confirmation on the present inventory.

## Next authorized experiment

Obtain or designate a genuinely new cohort with the frozen postoperative clinical-pathological anchor and optional blood/ICD/TMA modalities. Before opening outcomes, freeze the current-V1R prediction-generation code, frozen bridge parameters, estimands, bootstrap procedure, and all exclusions; seal predictions and hashes; then unseal outcomes and evaluate without refit or selection.

## Artifacts

- `core_backbone/U5R11_current_v1r_external_cohort_readiness_audit/frozen_u5r11_readiness_protocol.yaml`
- `core_backbone/U5R11_current_v1r_external_cohort_readiness_audit/u5r11_readiness_aggregate_results.json`
- `core_backbone/U5R11_current_v1r_external_cohort_readiness_audit/u5r11_readiness_audit.md`
- `core_backbone/U5R11_current_v1r_external_cohort_readiness_audit/u5r11_readiness_hashes.json`
- `scripts/run_u5r11_current_v1r_external_cohort_readiness_audit.py`
