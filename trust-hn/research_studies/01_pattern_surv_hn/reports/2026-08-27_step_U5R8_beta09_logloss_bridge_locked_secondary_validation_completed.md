# 2026-08-27 — U5R8 frozen U5R7 bridge locked secondary validation completed

## Objective

Apply the already frozen U5R7 `beta_0.900_logloss` bridge to the sealed aggregate V1R predictions in HANCOCK OOD TEST without using confirmation outcomes for parameter selection, refitting, router training, pattern-specific tuning, or patient removal.

## Important provenance boundary

The preceding U2/V1R raw confirmation evaluation had already unsealed the HANCOCK OOD outcomes on 2026-08-26. Therefore U5R8 is a **locked secondary post-unseal validation**, not a new pristine outcome-untouched confirmation. The bridge protocol was frozen before this U5R8 execution, and all bridge parameters came from the already completed U5R7 development artifact.

The confirmation bridge used the deterministic development-only intercept aggregation:

\[
\alpha_{dev,mean}=\frac{1}{25}\sum_{s=1}^{5}\sum_{f=1}^{5}\alpha_{s,f}=-0.14503379856995471,
\]

\[
p_{bridge}=\sigma\left(-0.14503379856995471+0.90\operatorname{logit}(p_{V1R,raw})\right).
\]

No confirmation outcome was used to select beta or alpha.

## Locked result

| Metric | Raw V1R | U5R7 bridge | Change | Gate/readout |
|---|---:|---:|---:|---|
| IPCW Brier24 | 0.134697 | 0.135782 | +0.001085 | failed strict +0.0005 global bridge gate |
| CITL | +0.156751 | +0.160944 | +0.004194 | absolute error worsened |
| Calibration slope | 1.510335 | 1.678150 | +0.167815 | absolute error to 1 worsened |
| Supported-pattern Brier regret (`111`) | — | +0.001085 | — | passed +0.005 gate |
| Coverage | 100% | 100% | 0 | preserved |
| Ranking | reference | preserved exactly | — | passed |

The cohort contained 152 patients and 40 deaths; the 24-month IPCW estimand had 120 evaluable rows and 26 evaluable events. In 2,000 event-stratified patient bootstrap replicates, the mean bridge-minus-raw Brier change was +0.001099 (95% interval −0.000798 to +0.002800), the mean CITL change was +0.004072 (95% interval −0.012131 to +0.020461), and the mean calibration-slope change was +0.176431 (1,960 finite replicates; 95% interval +0.105278 to +0.279123).

## Decision

The frozen U5R7 bridge **did not pass locked secondary validation** because its global Brier safety gate, CITL absolute-error gate and calibration-slope absolute-error gate all failed on HANCOCK OOD TEST. It did preserve full coverage and exact ranking, and the supported-pattern Brier regret remained below the boundary.

This result does not erase the genuine U5R7 development-only improvement. It limits the claim: U5R7 can remain described as a development calibration-bridge diagnostic, but it must not be described as a confirmed bridge or as transported external calibration. Raw V1R remains the primary locked confirmation output and retained backbone.

## Artifacts

- Protocol: `core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/frozen_u5r7_confirmation_bridge_validation_protocol.yaml`
- Runner: `scripts/run_v1r_beta09_logloss_bridge_confirmation_validation.py`
- Aggregate result: `core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/u5r7_confirmation_bridge_aggregate_results.json`
- Pattern result: `core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/u5r7_confirmation_bridge_pattern_results.csv`
- Bootstrap result: `core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/u5r7_confirmation_bridge_bootstrap_results.csv`
- Audit: `core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/u5r7_confirmation_bridge_audit.md`
- Hashes: `core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/u5r7_confirmation_bridge_hashes.json`

No patient-level outputs were copied into research or paper-facing tracked directories.
