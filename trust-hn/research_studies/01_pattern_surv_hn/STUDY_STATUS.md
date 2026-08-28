# PATTERN-Surv-HN Study Status
**Date:** 2026-08-27
**Current stage:** U6 cross-fitted value-router development exploration completed; modest OOF Brier gain, bootstrap intervals cross zero, no router confirmation authorized
**Status:** `U6_CROSS_FITTED_VALUE_ROUTER_EXPLORATION_COMPLETED_EXPLORATORY_ONLY`
**???** `U5_V1R_CALIBRATION_BRIDGE_FAILURE_REVIEW_COMPLETED`
**?????** `post_hoc_exploratory_rescue`

## ???? backbone

- ????????? V1R?
- V0 ??? clinical-pathological anchor ? exact fallback?
- ????? V1 ??????????????????? headline result?
- V1R development ? locked confirmation ??????????????????
- calibration bridge ?????????????? `trust-hn/paper/manuscript_results/V1R_positive/`?

## ???? V1R ??

### Development

```text
cohort                                  HANCOCK official training
eligible patients / events              610 / 173
coverage                                100%
mean delta Uno C24                     +0.021303
mean delta AUC24                       +0.020488
mean delta IPCW Brier24                -0.000407
Uno-C favourable seeds                 5 / 5
worst supported-pattern Brier regret   +0.009848
exact fallback error                   0.0
```

### Locked confirmation

```text
cohort                                  HANCOCK OOD confirmation
patients / events                       152 / 40
coverage                                100%
delta Uno C24                          +0.021664
delta IPCW Brier24                     -0.005166
delta AUC24                            +0.012543
delta Harrell C                        +0.019589
bootstrap intervals                    principal deltas crossed zero
interpretation                         positive directional signal
```

## U5 calibration bridge diagnostics

???????????? development-only?cross-fitted calibration bridge ????? confirmation ???????? V1R ?????

```text
development evaluable rows             2,460
development evaluable events           415
raw IPCW Brier24                       0.126637
calibrated-candidate IPCW Brier24      0.134911
delta IPCW Brier24                     +0.008274  FAIL (boundary +0.005)
raw calibration slope                  0.826123
calibrated-candidate slope             0.192238  FAIL (target 1)
coverage                               preserved
```

????? calibration bridge candidate ?????????? calibration bridge ??????? V1R backbone ???raw V1R absolute-risk output ?????? confirmation cohort ??? bridge?????? router ??? FUSE/FALLBACK/RANK_ONLY/ABSTAIN actions?

?????

- `research_studies/01_pattern_surv_hn/audits/U5_V1R_calibration_bridge_audit.md`
- `research_studies/01_pattern_surv_hn/reports/2026-08-26_step_U5_V1R_calibration_bridge_diagnostics_completed.md`
- `research_studies/01_pattern_surv_hn/reports/2026-08-26_step_U5_V1R_calibration_bridge_failure_independent_review_completed.md`

## ????

```yaml
phase6_outcomes_already_seen: true
phase6_files_modified: false
result_informed_design: true
confirmatory_claims_allowed: false
patient_level_outputs_git_ignored: true
tracked_outputs_aggregate_only: true
confirmation_bridge_evaluation: completed_locked_secondary_post_unseal_validation_failed_safety_gate
router_training: not_performed
clinical_utility_analysis: not_performed
```

## ????????

```text
RESEARCHER_APPROVAL_OF_ANY_REVISED_CALIBRATION_BRIDGE_PROTOCOL
```

?? revised bridge ??????????????? development-only ???????????? confirmation outcomes ??? refit????????? bridge ?????????????

## U5R4 fixed bounded global bridge candidate

A frozen, conservative candidate was independently rerun in development-only cross-fitting. It is global-only, rank-preserving, uses IPCW-Brier fitting with beta constrained to [0.75, 1.25], and shrinks the fitted transformation 25% toward identity.

```text
candidate                               bounded_global_full_g0.25
development cohort                       HANCOCK official training OOF
eligible patients / events               610 / 173
IPCW-evaluable rows / events             2460 / 415
raw IPCW Brier24                         0.126637
U5R4 IPCW Brier24                        0.126834
delta IPCW Brier24                      +0.000198  PASS (boundary +0.005)
raw CITL                                  +0.011680
U5R4 CITL                                 +0.005823
raw calibration slope                    0.825887
U5R4 calibration slope                   0.829295
worst supported-pattern Brier regret     +0.000758  PASS (boundary +0.020)
coverage                                 100% preserved
ranking                                  preserved in all held-out folds
deterministic rerun                      exact artifact hashes matched
```

Interpretation: U5R4 is a development-safe exploratory bridge candidate, not a confirmed bridge. It can be reviewed for a separate locked confirmation application, but the confirmation cohort must not be used for tuning. Raw V1R remains the retained backbone. The paper positive-results folder is unchanged.

Artifacts:

- `core_backbone/U5R4_V1R_bounded_global_bridge_candidate/`
- `audits/U5R4_bounded_global_bridge_candidate_audit.md`
- `reports/2026-08-26_step_U5R4_bounded_global_bridge_candidate_diagnostic_completed.md`

Next allowed step: independent review and researcher approval before any confirmation application.

## U5R7 beta 0.90 log-loss bridge candidate

A further development-only search explored fixed positive global slopes and alternative intercept objectives, always preserving ranking. The strongest current candidate is `beta_0.900_logloss`, with `x_candidate = alpha_logloss + 0.90*x_raw`.

```text
raw IPCW Brier24                       0.126637
U5R7 IPCW Brier24                      0.126784
delta IPCW Brier24                    +0.000147  PASS (strict boundary +0.0005)
raw CITL                                +0.011680
U5R7 CITL                               -0.003796
absolute CITL error change              -0.007884
raw calibration slope                  0.825887
U5R7 calibration slope                 0.881552
absolute slope error change             -0.055665
worst supported-pattern Brier regret    +0.004176  PASS (boundary +0.005)
coverage                                100% preserved
ranking                                 preserved in all held-out folds
development-safe candidate              PASS
deterministic rerun                     exact hash match
```

This is the strongest current **development-safe exploratory** bridge candidate, not a confirmed bridge. Raw V1R remains retained. Confirmation evaluation, router training, clinical utility analysis, and paper-positive-results updates remain unauthorized.

Artifacts:

- `core_backbone/U5R5_V1R_fixed_slope_intercept_bridge_exploration/`
- `core_backbone/U5R6_V1R_citl_slope_balanced_bridge_exploration/`
- `core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/`
- `audits/U5R7_beta09_logloss_bridge_candidate_audit.md`
- `reports/2026-08-26_step_U5R5_U5R6_U5R7_rank_preserving_bridge_exploration_completed.md`


## U5R7 paper integration completed

The selected `beta_0.900_logloss` bridge has been finalized as a **development-only, cross-fitted calibration result** in the publication-facing material. It is explicitly separated from the raw V1R locked confirmation result.

```text
candidate                               beta_0.900_logloss
formula                                 x_bridge = alpha_logloss + 0.90*x_raw
bridge-evaluable rows / events          2460 / 415
raw IPCW Brier24                        0.126637
U5R7 IPCW Brier24                       0.126784
delta IPCW Brier24                     +0.000147  PASS (gate +0.0005)
raw CITL                                +0.011680
U5R7 CITL                               -0.003796
absolute CITL error change              -0.007884
raw calibration slope                   0.825887
U5R7 calibration slope                  0.881552
absolute slope error change             -0.055665
worst supported-pattern regret          +0.004176  PASS (gate +0.005)
coverage                                100% preserved
ranking                                 preserved in all held-out folds
confirmation bridge evaluation          not performed
```

The manuscript now presents V1R as the fusion backbone, U5R7 as a development calibration layer, and raw V1R as the locked confirmation output. Detailed U5R parameter grids are in `paper/manuscript_results/appendix_candidates/`; no patient-level outputs were copied there.

Next allowed step remains a separately frozen and approved confirmation bridge protocol. No confirmation bridge claim, clinical-utility claim, or deployment claim is authorized by this integration.

## U5R8 locked secondary validation of the U5R7 bridge

The previously frozen `beta_0.900_logloss` bridge was applied to the sealed aggregate V1R predictions in HANCOCK OOD TEST using a development-only fixed intercept mean of `-0.14503379856995471` and beta `0.90`. Because the raw U2 confirmation outcomes had already been unsealed on 2026-08-26, this is explicitly a **locked secondary post-unseal validation**, not a new pristine outcome-untouched confirmation.

```text
cohort                                  HANCOCK OOD TEST
patients / events                       152 / 40
IPCW-evaluable rows / events            120 / 26
raw IPCW Brier24                        0.134697
U5R8 bridge IPCW Brier24                0.135782
delta IPCW Brier24                      +0.001085  FAIL (strict gate +0.0005)
raw CITL                                +0.156751
U5R8 bridge CITL                        +0.160944  absolute error worsened
raw calibration slope                   1.510335
U5R8 bridge calibration slope           1.678150  absolute error worsened
worst supported-pattern Brier regret    +0.001085  PASS (gate +0.005)
coverage                                100% preserved
ranking                                 preserved exactly
locked secondary validation             FAIL
```

The bridge preserved the properties it was designed to preserve鈥攃overage and ordering鈥攂ut its development calibration improvement did not reproduce in this cohort. U5R7 remains valid development-only evidence and is not erased; it is not promoted to confirmed external calibration. Raw V1R remains the primary locked confirmation output.

Artifacts:

- `core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/`
- `reports/2026-08-27_step_U5R8_beta09_logloss_bridge_locked_secondary_validation_completed.md`
- `scripts/run_v1r_beta09_logloss_bridge_confirmation_validation.py`

Next allowed step: do not tune the bridge on HANCOCK OOD TEST. Any further bridge exploration must be specified and evaluated using development data only, or evaluated on a genuinely independent pristine cohort with protocol frozen before outcome access.
## U5R9 frozen bridge panel characterization

U5R9 evaluated the already frozen U5R4 conservative bridge and U5R7 beta=0.90 log-loss bridge, together with raw V1R, on HANCOCK OOD TEST. The U2 outcomes had already been unsealed before this protocol was frozen, so this is post-unseal exploratory characterization rather than pristine confirmation.

```text
candidate                         delta IPCW Brier24   CITL          slope       gates
raw V1R                           0.000000             +0.156751     1.510335    reference
U5R4 bounded global               +0.000170             +0.154789     1.544118    FAIL slope
U5R7 beta 0.90 log-loss           +0.001085             +0.160944     1.678150    FAIL Brier/CITL/slope
```

Both bridges preserved 100% coverage and exact ranking, and both remained within the supported-pattern Brier regret boundary of +0.005. U5R4 showed a small point-estimate CITL improvement but did not improve calibration slope toward 1. U5R7 failed all three substantive calibration/safety gates on this cohort. No winner was selected after seeing the outcome metrics; raw V1R remains the primary confirmation output.

Artifacts:

- `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/`
- `reports/2026-08-27_step_U5R9_frozen_bridge_panel_post_unseal_characterization_completed.md`
- `scripts/run_v1r_frozen_bridge_panel_post_unseal_characterization.py`

Next allowed step: stop repeated bridge testing on HANCOCK OOD TEST; use a genuinely independent outcome-untouched cohort with the bridge protocol frozen before outcome access, or conduct only development-only exploration under a new preregistered design.

## U5R10 fixed bridge external secondary characterization

U5R10 applied the frozen U5R7 beta=0.90 log-loss transform to both available GEO cohorts without any external refit or outcome-dependent selection. The fixed transform improved IPCW Brier, absolute CITL error, and calibration-slope error in both cohorts while preserving exact ranking and 100% coverage:

```text
GSE65858 (n=244, events=78): Brier 0.224769 -> 0.209071; delta -0.015697; CITL -1.331567 -> -1.181249; slope 0.608704 -> 0.676338
GSE41613 (n=97, events=51):  Brier 0.204267 -> 0.197910; delta -0.006357; CITL -0.571285 -> -0.456782; slope 0.791168 -> 0.879076
ranking: exact preserved; coverage: 100% preserved in both cohorts
```

This is a positive **post-unseal external characterization of the fixed transform on legacy Phase 6 B6 fusion risk**. The available GEO prediction definition has not been shown to be identical to current PATTERN-Surv-HN V1R, so U5R10 does not establish current V1R bridge external validity and cannot promote the bridge to confirmed deployment status. A new outcome-untouched cohort with current V1R prediction generation frozen before outcome access is still required.

Artifacts:

- `core_backbone/U5R10_fixed_bridge_external_secondary_characterization/`
- `reports/2026-08-27_step_U5R10_fixed_bridge_external_secondary_characterization_completed.md`
- `scripts/run_v1r_fixed_bridge_external_secondary_characterization.py`


## U5R11 current-V1R external cohort readiness audit

U5R11 was executed without reading patient rows or outcome columns. The audit inspected only frozen protocol metadata and source manifests to determine whether a formal current-V1R fixed-bridge confirmation could run from the local inventory.

```text
candidate cohorts                                       5
current-V1R-compatible cohorts                          1 (HANCOCK OOD)
certified outcome-untouched + compatible cohorts         0
formal current-V1R confirmation executable locally      no
```

HANCOCK OOD has the required multimodal contract but was already used for raw-V1R confirmation and post-unseal bridge characterization. RADCURE lacks the frozen blood/ICD/TMA contract; GSE65858 and GSE41613 provide legacy B6 transcriptomic prediction artifacts rather than current V1R; TCGA-HNSC provides expression/clinical artifacts but no current-V1R-compatible prediction contract. No current-V1R bridge prediction or metric was generated, and no negative-readout material was added to the manuscript positive-results directory.

This is a data-readiness constraint, not a bridge failure. The next valid experiment requires a new compatible cohort, pre-outcome freezing of current-V1R prediction generation and the fixed bridge, prediction sealing, and subsequent outcome evaluation.

Artifacts:

- `research_studies/01_pattern_surv_hn/core_backbone/U5R11_current_v1r_external_cohort_readiness_audit/`
- `scripts/run_u5r11_current_v1r_external_cohort_readiness_audit.py`
- `research_studies/01_pattern_surv_hn/reports/2026-08-27_step_U5R11_current_v1r_external_cohort_readiness_audit_completed.md`

## U6 cross-fitted value-router development exploration

U6 trained a patient-grouped cross-fitted logistic value router on development repeated OOF predictions only. It selected `FUSE` (raw V1R) or `FALLBACK` (V0) using a prespecified probability threshold; all thresholds were reported without post-readout winner selection.

```text
rows / unique patients / events                       3,050 / 610 / 865
raw V1R IPCW Brier                                     0.124561
V0 IPCW Brier                                           0.124968
FUSE q>=0.40 router Brier                               0.124619 (delta vs V0 -0.000349)
FUSE q>=0.50 router Brier                               0.124619 (delta vs V0 -0.000350)
FUSE q>=0.60 router Brier                               0.124622 (delta vs V0 -0.000346)
FUSE rate                                               56.2%–61.2%
coverage                                                100%
patient-cluster bootstrap CI for delta vs V0            crossed zero for all thresholds
```

The router shows a small, directionally favourable development signal and preserves full coverage by falling back to V0, but the uncertainty intervals cross zero and the router is not externally validated. It is retained as a hypothesis-generating mechanism, not as a confirmed manuscript backbone or deployment policy.

Artifacts:

- `research_studies/01_pattern_surv_hn/core_backbone/U6_cross_fitted_value_router_exploration/`
- `scripts/run_u6_cross_fitted_value_router_exploration.py`
- `research_studies/01_pattern_surv_hn/reports/2026-08-27_step_U6_cross_fitted_value_router_exploration_completed.md`

