# Step U5/V1R calibration bridge diagnostics completed

**Date:** 2026-08-26  
**Status:** `U5_V1R_CALIBRATION_BRIDGE_DIAGNOSTIC_FAILED`  
**Analysis label:** `post_hoc_exploratory_rescue`

## Summary

The frozen U5/V1R calibration bridge protocol was executed as a development-only, cross-fitted diagnostic. The candidate did not pass the pre-specified safety criteria: IPCW Brier24 worsened by `+0.008274`, exceeding the no-harm boundary of `+0.005`, and the calibration slope moved from `0.826123` to `0.192238`, away from the ideal value of 1.

The candidate is stopped before any confirmation-cohort application. Raw V1R absolute-risk predictions remain retained. This result does not invalidate the V1R backbone or the already sealed V1R locked confirmation; it only rejects this calibration bridge candidate for the current stage.

## Execution record

- Frozen protocol: `core_backbone/U5_V1R_calibration_bridge_protocol/frozen_calibration_bridge_protocol.yaml`
- Development cohort: HANCOCK official training, 610 eligible patients and 173 observed events
- Cross-fitting: 5 repetition seeds × 5 outer folds
- Evaluable cross-fitted rows: 2,460, including 415 events
- Confirmation cohort: not evaluated with the bridge
- Router and clinical actions: not created
- Deterministic rerun: exact normalized aggregate match

## Aggregate result

| Metric | Raw V1R | Calibration candidate | Delta / interpretation |
|---|---:|---:|---|
| IPCW Brier24 | 0.126637 | 0.134911 | +0.008274; safety boundary failed |
| CITL | +0.011680 | -0.028169 | direction moved toward zero in some summaries, but not sufficient |
| Calibration slope | 0.826123 | 0.192238 | worsened relative to target 1 |
| Coverage | 100% | 100% | preserved |

## Scientific interpretation

The frozen bridge did not provide a safe improvement in absolute-risk prediction. Its apparent intercept correction was accompanied by a marked slope distortion and increased Brier loss. Pattern-level diagnostics further showed substantial harm for patterns `001` and `110`, with smaller but positive Brier changes for `011` and `101`. These findings are consistent with an unstable recalibration candidate under sparse and heterogeneous acquisition support.

The bridge therefore remains a **failed development candidate / future redesign item**, not a paper-facing positive result. The paper narrative remains unchanged:

```text
V0 clinical-pathological anchor
→ V1R shrinkage-controlled residual fusion
→ positive development signal
→ positive directional locked confirmation signal
```

The calibration bridge is not included in `trust-hn/paper/manuscript_results/V1R_positive/`.

## Next allowed step

Independent review of the calibration failure is required before any revised bridge protocol can be frozen. A revised design, if approved, must be separately named, pre-specified and evaluated on development data only before any confirmation application. Confirmation outcomes may not be used to tune or refit the bridge.
