# Step U5/V1R calibration bridge independent review completed

**Review date:** 2026-08-26  
**Status:** `U5_V1R_CALIBRATION_BRIDGE_FAILURE_REVIEW_COMPLETED`  
**Reviewer scope:** protocol, runner, aggregate artifacts, audit and stage report  
**Analysis label:** `post_hoc_exploratory_rescue`

## Review question

Was the U5/V1R calibration bridge candidate executed according to its frozen development-only protocol, and does the resulting failure support stopping the candidate before confirmation application?

## Independent checks

| Check | Finding | Result |
|---|---|---|
| Frozen protocol identified before execution | `frozen_calibration_bridge_protocol.yaml` is present and marked `FROZEN_BEFORE_EXECUTION` | PASS |
| Development-only source | Runner reads only the development V1R repeated nested OOF prediction artifact | PASS |
| Confirmation isolation | Runner contains no confirmation-cohort read, fit, refit or outcome-tuning path | PASS |
| Cross-fitting | Each held-out outer fold is evaluated with parameters fitted on the other folds within the same seed | PASS |
| Pattern support rules | Pattern-specific adjustments use the frozen 50/15 intercept and 100/25 slope gates | PASS |
| Leading-zero pattern preservation | CSV loading explicitly uses string dtype for `acquisition_pattern` and `usable_pattern`; aggregate results retain `001`, `010`, etc. | PASS |
| Deterministic rerun | Aggregate result hash matches the recorded rerun hash | PASS |
| Brier safety boundary | Delta `+0.008274` exceeds `+0.005` | FAIL as intended safety rejection |
| Slope diagnostic | Slope changes `0.826123 → 0.192238`, away from target 1 | FAIL as intended safety rejection |
| Coverage / removal | Coverage preserved; no patient removal | PASS |
| Router / clinical actions | No router labels, router, or clinical actions created | PASS |

## Review conclusion

The diagnostic result is internally consistent and reproducible. The current bridge candidate should remain stopped and must not be applied to the confirmation cohort. The failure is attributable to the calibration bridge candidate, not to the already retained V1R backbone. Raw V1R absolute-risk output remains the approved output for the completed V1R development and locked confirmation analyses.

The V1R-positive manuscript directory was not updated with the failed bridge result. No change is made to the V1R paper narrative or to the original V1 failure audit.

## Next authorization boundary

The next step requires researcher approval for any revised calibration bridge protocol. A revised candidate must be separately named, frozen before execution and evaluated on development data only. Confirmation outcomes may not be used for tuning, refitting, support-rule changes or selective removal.
