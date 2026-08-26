# Step U5/V1R calibration bridge protocol frozen

**Date:** 2026-08-26  
**Status:** `PROTOCOL_FROZEN_BEFORE_EXECUTION`

## What was frozen

A V1R-only calibration bridge protocol was frozen after completion of the manuscript integration and independent review. The bridge will recalibrate 24-month absolute risk without changing the V1R ranking model, patient coverage, exact clinical fallback or inclusion rules.

The primary bridge is a global IPCW-weighted logistic recalibration:

\[
\operatorname{logit}(p_{\mathrm{cal},i})=\alpha_g+\beta_g\operatorname{logit}(p_{\mathrm{raw},i}).
\]

Pattern-specific intercepts and slopes are allowed only when development OOF support meets the pre-frozen thresholds: at least 50 patients and 15 events for an intercept, and at least 100 patients and 25 events for a slope. Otherwise the global bridge is used.

## Execution boundary

Development fitting is cross-fitted over the existing V1R OOF predictions. The locked confirmation cohort may receive only the frozen bridge after all bridge and prediction artifacts are sealed. No router, selective removal, confirmation tuning or clinical-utility analysis is authorized.

## Frozen artifact

`core_backbone/U5_V1R_calibration_bridge_protocol/frozen_calibration_bridge_protocol.yaml`

## Next immediate action

Implement and run the development-only cross-fitted calibration diagnostics, then audit the result before any frozen bridge application to the confirmation cohort.
