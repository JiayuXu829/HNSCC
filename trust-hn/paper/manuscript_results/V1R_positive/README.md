# V1R and U5R7 results for manuscript use

This directory is the controlled, publication-facing source of truth for the manuscript narrative. It contains aggregate-only positive development, development-bridge and locked-confirmation results, manuscript claims, section mapping and the main-figure framework. Patient-level predictions and full audit records remain outside this directory.

## Scope

- **Backbone:** V1R shrinkage-controlled residual Deep Sets Cox around the V0 clinical-pathological anchor.
- **Development V1R:** HANCOCK official-training ecosystem, 610 eligible patients and 173 deaths; five repetition seeds, five outer folds and three inner folds.
- **Development bridge:** U5R7 `beta_0.900_logloss`, a fixed beta 0.90 global logit bridge with an weighted log-loss intercept, evaluated by cross-fitting on 2,460 repeated OOF rows and 415 evaluable events.
- **Locked confirmation:** researcher-confirmed outcome-untouched HANCOCK OOD cohort, 152 patients and 40 events; 25 matched raw V0/V1R members; predictions sealed before outcome unmasking.
- **Coverage:** 100% for V0 and V1R in both completed analyses; U5R7 preserves coverage and exact fallback.
- **Publication rule:** foreground V1R as the fusion backbone; describe U5R7 as a development-only calibration bridge; report the locked confirmation as raw V1R only.

## Provenance

Development V1R values are sourced from `research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_residual_shrinkage_rescue/aggregate_u2_v1r_rescue_audit.json`.

U5R7 values are sourced from `research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_aggregate_results.json` and summarized in `v1r_bridge_positive_results.csv/json`.

Locked confirmation values are sourced from `research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_confirmation_protocol/aggregate_confirmation_results.json`.

The development OOF receipt is `E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0`; the locked prediction artifact is sealed with SHA256 `E5DA83BDB3BB97C3488687C78CCF166FBD03059619DD0690E2767CAF8F393FCF`.

## Claim boundary

The manuscript may describe V1R as the provisional development backbone, U5R7 as a positive development-only calibration-bridge result, and the locked raw-V1R cohort as a positive directional point-estimate signal. It must not describe U5R7 as confirmation, external calibration, definitive superiority, clinical utility, deployment readiness or external generalisation. The bootstrap intervals for the principal confirmation deltas cross zero, and U5R7 has not been applied to confirmation.

## Files

- `v1r_positive_results.csv/json`: primary V1R development aggregate results;
- `v1r_bridge_positive_results.csv/json`: U5R7 development-only aggregate bridge result;
- `v1r_bridge_methods_and_formulae.md`: bridge formula, protocol and interpretation;
- `v1r_bridge_paper_integration_notes.md`: approved manuscript wording and claim boundary;
- `v1r_locked_confirmation_positive_results.csv/json`: locked raw-V1R confirmation aggregate results;
- `v1r_manuscript_claims.md`: claims supported by V1R and U5R7 extracts;
- `v1r_paper_narrative_and_section_map.md`: section-by-section source of truth;
- `figure1_v1r_framework.md`: main-figure framework specification.

Detailed U5R4-U5R6 parameter grids and exploration summaries are stored separately in `paper/manuscript_results/appendix_candidates/`.
