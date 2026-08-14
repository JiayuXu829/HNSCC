# U1 Runbook — postoperative contract and V0/V1 implementation

**status:** `U1_3_V1_SMOKE_COMPLETE_AWAITING_APPROVAL`
**analysis label:** `post_lock_exploratory`

## U1.1 postoperative contract — approved

- Frozen postoperative estimand and development/test boundary.
- Independent anchor, blood, ICD, and TMA blocks.
- Acquisition, usability, internal missingness, and quality states.
- Fold-bound preprocessing and aggregate-only audit.

## U1.2/V0 clinical safety anchor — approved

- Extended clinical-pathological elastic-net Cox anchor.
- Repeated nested development OOF evaluation.
- Training-fold preprocessing and baseline survival.
- Exact V0 safety/fallback reference established.

## U1.3/V1 structural smoke — complete, awaiting approval

- Deterministic NumPy structural reference; no new dependency.
- Modality-specific adapters for blood, ICD, and TMA.
- Identity, status, and quality encoding.
- Masked-mean permutation-invariant Deep Sets pooling.
- Arbitrary subset input.
- Residual score `eta_fused = eta_clinical + delta_eta`.
- Exact `delta_eta = 0` and exact clinical fallback when no token is active.
- Synthetic Cox partial-likelihood smoke only; no model fitting or patient outcomes.

## Proposed next step, not yet authorized

U1.4/V1 trainable implementation and synthetic optimization smoke, conditional on explicit
project-local PyTorch dependency approval. Formal V1 development cross-validation belongs to U2
and requires another approval.
