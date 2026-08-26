# Step U2 ? V1R locked confirmation completed

**Date:** 2026-08-26  
**Cohort:** HANCOCK_OOD_TEST  
**Status:** completed

## Execution

The researcher confirmed before prediction generation that the HANCOCK OOD cohort was outcome-untouched. The frozen protocol was then executed without changing model, features, preprocessing, hyperparameters, estimands, safety boundaries or aggregation. Twenty-five matched V0/V1R members were fit only on development partitions; prediction, input, code, dependency and protocol hashes were sealed before outcome unmasking.

## Aggregate readout

- n=152, events=40, coverage=100%.
- Uno C24: V0 0.782579; V1R 0.804242; delta +0.021664.
- IPCW Brier24: V0 0.136412; V1R 0.131246; delta -0.005166.
- AUC24: V0 0.801094; V1R 0.813637; delta +0.012543.
- Harrell C: V0 0.733253; V1R 0.752842; delta +0.019589.
- Supported acquisition pattern 111: n=152, events=40; Brier delta -0.005166, within the +0.020 boundary.

## Interpretation

This is a positive directional confirmation signal at the prespecified point-estimate level. The 2,000-patient stratified bootstrap intervals cross zero for delta Uno C and delta Brier, so this stage does not establish definitive superiority. The original V1 failure and the post-hoc exploratory status of V1R remain unchanged. No patient-level outputs were copied into the paper-facing results directory.

## Controlled artifacts

- `core_backbone/U2_V1R_confirmation_protocol/aggregate_confirmation_results.json`
- `core_backbone/U2_V1R_confirmation_protocol/confirmation_audit.md`
- `core_backbone/U2_V1R_confirmation_protocol/pre_unseal_prediction_receipt.json`
- `paper/manuscript_results/V1R_positive/v1r_locked_confirmation_positive_results.json`
- `paper/manuscript_results/V1R_positive/v1r_locked_confirmation_positive_results.csv`
- `paper/manuscript_results/V1R_positive/v1r_locked_confirmation_manuscript_claims.md`
