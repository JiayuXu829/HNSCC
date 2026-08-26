# U5/V1R calibration bridge diagnostic audit

**Audit date:** 2026-08-26  
**Status:** `U5_V1R_CALIBRATION_BRIDGE_DIAGNOSTIC_FAILED`  
**Study:** PATTERN-Surv-HN  
**Analysis label:** `post_hoc_exploratory_rescue`

## 1. Scope and authorization

The frozen U5/V1R calibration bridge protocol was executed only on the HANCOCK official training cohort using development-only cross-fitted diagnostics. The purpose was to test whether a pre-specified global IPCW-weighted logistic recalibration, with support-gated pattern adjustments, could improve V1R 24-month absolute-risk calibration without changing ranking, coverage, fallback behavior or patient inclusion.

The locked confirmation cohort was **not** used for fitting, tuning, support-rule changes or bridge evaluation. No router labels, router model, selective removal rule, or clinical action labels were created.

## 2. Frozen artifacts and reproducibility

| Artifact | SHA256 |
|---|---|
| `frozen_calibration_bridge_protocol.yaml` | `4ED5B73E7BA0265997213616916F26432730A80A2178D6F6C99B449862F54F56` |
| `development_cross_fitted_bridge_results.json` | `1DAF05D7656C6C032E24D9E354CE7226609931E7B53DA1EE68A91F0B03E79476` |
| `development_cross_fitted_bridge_fold_results.csv` | `FF0C0963B68EB2AEE071E2CC48D158A786AE1DC7EE789A3473F426581BAEBB66` |
| `development_bridge_parameters.csv` | `F78FFCDF8E378D974D104566D4DC838CE50CF832AB4A4B8512F8D30AC912604A` |

The deterministic rerun produced the same normalized aggregate result hash:

```text
1DAF05D7656C6C032E24D9E354CE7226609931E7B53DA1EE68A91F0B03E79476
```

## 3. Development cohort and cross-fitting

```text
cohort             HANCOCK official training
eligible patients  610
observed events    173
repetition seeds   17, 29, 43, 71, 101
outer folds        5 per seed
OOF evaluable rows 2,460
OOF evaluable events 415
```

For every held-out outer fold, bridge parameters were fitted only on the remaining development OOF patients within the same repetition seed. No patient contributed to both bridge fitting and its cross-fitted evaluation fold.

## 4. Prespecified safety results

### 4.1 Global aggregate

| Endpoint | Raw V1R | Calibrated candidate | Change | Frozen boundary | Result |
|---|---:|---:|---:|---:|---|
| IPCW Brier24 | 0.126637 | 0.134911 | **+0.008274** | <= +0.005 | **FAIL** |
| CITL | +0.011680 | -0.028169 | closer to 0 | target 0 | mixed |
| Calibration slope | 0.826123 | 0.192238 | farther from 1 | target 1 | **FAIL** |
| Coverage | retained | retained | unchanged | 1.0 | PASS |
| Patient removal | none | none | unchanged | prohibited | PASS |

The candidate reduced the absolute CITL magnitude from approximately 0.0117 to 0.0282 only in the sense of moving the intercept direction toward zero in some summaries; the global aggregate did not establish a reliable calibration improvement because the calibration slope deteriorated sharply. The Brier no-harm boundary was also exceeded.

### 4.2 Pattern-stratified diagnostic

| Acquisition pattern | n | Events | Delta IPCW Brier24 | Slope raw | Slope calibrated |
|---|---:|---:|---:|---:|---:|
| 001 | 30 | 10 | **+0.138194** | 2.3003 | 0.0319 |
| 010 | 5 | 0 | +0.000051 | NA | NA |
| 011 | 280 | 30 | **+0.010950** | 1.6219 | 0.4137 |
| 101 | 200 | 30 | **+0.012580** | 0.4536 | -0.2598 |
| 110 | 70 | 25 | **+0.118746** | 0.6438 | -0.0894 |
| 111 | 1,875 | 320 | +0.001369 | 0.8203 | 0.7853 |

Pattern-specific outputs are diagnostic only. They show that the candidate's harm was concentrated in low-support or heterogeneous acquisition patterns, while the dominant `111` pattern had a smaller but still positive Brier change.

## 5. Decision

The frozen U5/V1R calibration bridge candidate is **stopped at development diagnostics**. It fails the prespecified IPCW-Brier no-harm boundary and produces a calibration slope substantially farther from the ideal value of 1. The candidate is therefore **not authorized for application to the locked confirmation cohort**.

This is a failure of the current calibration bridge design, **not a failure of the V1R backbone**. The raw V1R absolute-risk output remains the retained output for the already completed V1R development and locked confirmation analyses. Existing V1R results and the paper-facing positive-results directory are not rewritten or supplemented with these failed bridge results.

## 6. Governance boundary and next step

The following remain true:

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

The next permitted step is an independent review of this failure and, only with researcher approval, a separately frozen revised bridge protocol. No parameter tuning on confirmation outcomes, router training or clinical-action construction is permitted under this stage.
