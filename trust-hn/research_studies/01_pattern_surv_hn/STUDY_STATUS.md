# PATTERN-Surv-HN Study Status
**Date:** 2026-08-26
**Current stage:** U5R7 beta 0.90 log-loss bridge development-only result integrated into manuscript; raw V1R retained for confirmation
**Status:** `U5R7_V1R_BETA09_LOGLOSS_BRIDGE_PAPER_INTEGRATION_COMPLETED`
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
confirmation_bridge_evaluation: not_performed
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
