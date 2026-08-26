# U2/V1R confirmation protocol 鈥?freeze record

**status:** `FROZEN_READY_FOR_LOCKED_VALIDATION`
**protocol_frozen_on:** 2026-08-26
**analysis_label:** `pre_registered_outcome_untouched_confirmation`
**candidate:** `V1R`
**comparator:** `V0`
**protocol_sha256:** `1E134D30557D1CC153997F6EBB79E99C2E160F85A9F94BF3BBDD81C2C588BDED`

## Researcher authorization

The researcher explicitly authorized freezing the V1R confirmation protocol and proceeding to locked V0-versus-V1R validation only on an outcome-untouched confirmation cohort. This authorization does **not** authorize opening any already-consumed Phase 6 outcomes or substituting a modality-incompatible dataset.

> Freeze the V1R confirmation protocol, then perform locked V0 vs V1R validation on an outcome-untouched confirmation cohort.

## Freeze decision

The protocol is frozen exactly as specified in `frozen_confirmation_protocol.yaml`:

- V0 is the clinical-pathological anchor and exact fallback.
- V1R is the already-approved shrinkage-controlled residual Deep Sets Cox model.
- The primary estimand is paired delta Uno C at 24 months.
- The key safety estimand is paired delta IPCW Brier at 24 months, with the prespecified +0.005 no-harm boundary.
- The 25-member matched ensemble, preprocessing, hyperparameters, aggregation rules, bootstrap seed and reporting rules are locked.
- No architecture search, hyperparameter reselection, calibration bridge, router, post-unseal refit, selective patient removal or outcome-informed modification is allowed.

## Execution disposition

`FROZEN_READY_FOR_LOCKED_VALIDATION`

The researcher subsequently confirmed that the HANCOCK OOD confirmation cohort is outcome-untouched for this workflow. The cohort is therefore designated as `HANCOCK_OOD_TEST` and the locked validation may proceed under the frozen protocol.

1. the researcher-confirmed outcome-untouched status is recorded before prediction generation; and
2. compatibility with the postoperative HANCOCK-style V1R input contract is verified.

The researcher confirmation overrides the prior **uncertainty block** for this execution only; it does not authorize changing the model, features, hyperparameters, estimands, or safety boundaries.

The HANCOCK OOD test is the same-ecosystem postoperative cohort (n=152) and is now the named confirmation cohort. The previous audit's concern was a governance-record discrepancy, not an observed outcome analysis in this execution. We preserve the discrepancy in the audit trail and do not rewrite the historical Phase 6 record.

Therefore:

- the protocol remains frozen;
- predictions may now be generated without reading confirmation outcomes;
- outcomes may be unsealed only after model, input, code, dependency and prediction hashes are sealed;
- no calibration bridge, router or post-unseal refit is allowed.
See `cohort_eligibility_audit.md` for the candidate-by-candidate audit.

