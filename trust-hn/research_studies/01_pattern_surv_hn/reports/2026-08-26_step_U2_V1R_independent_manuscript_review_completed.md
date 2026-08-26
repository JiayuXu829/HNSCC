# Step U2/V1R independent manuscript review completed

**Date:** 2026-08-26  
**Status:** `COMPLETED_WITH_NO_BLOCKING_INCONSISTENCY`

## Review scope

The integrated manuscript was reviewed against the controlled V1R development extract, the locked confirmation aggregate extract, the frozen confirmation protocol and the study registry. The review focused on method identity, numerical consistency, claim strength, outcome-access chronology and publication-facing file hygiene.

## Review findings

### Passed

- The manuscript uses V1R as the only multimodal fusion method and does not contain a standalone unscaled-candidate method reference.
- Development values match `v1r_positive_results.json` and `v1r_positive_results.csv`.
- Locked confirmation values match `v1r_locked_confirmation_positive_results.json` and `aggregate_confirmation_results.json`.
- The V1R residual equation, fold-bound shrinkage selection and exact clinical fallback are stated consistently.
- The manuscript distinguishes development evidence from locked confirmation evidence.
- The confirmation cohort is described as outcome-untouched before prediction sealing, with no confirmation tuning or post-unseal refit.
- Bootstrap intervals crossing zero are explicitly reported; definitive superiority is not claimed.
- Coverage, fallback and pattern-level safety claims are aggregate-only.
- Patient-level predictions remain outside the publication-facing results directory.
- Planned calibration, routing and clinical-utility analyses remain labelled as future work.

### Claim boundary retained

V1R is presented as an exploratory, result-informed provisional backbone. The manuscript does not claim external generalisation, transportability, clinical utility, deployment readiness or definitive superiority.

## Recommended next step

The next analysis should begin only after a separately frozen protocol for the **calibration bridge**. The recommended sequence is:

1. freeze calibration-bridge estimands, inputs, fitting folds, support thresholds and no-harm boundaries;
2. run development-only cross-fitted calibration diagnostics;
3. evaluate the frozen bridge on the locked confirmation predictions only after the prediction artifact and bridge rules are sealed;
4. keep router action creation and clinical-utility claims out of scope until separately approved.

No calibration or router training was executed in this review step.
