# U1 Runbook ? postoperative contract and V0/V1 implementation

**status:** `U1_4_V1_TRAINABLE_SMOKE_COMPLETE_AWAITING_APPROVAL`
**analysis label:** `post_lock_exploratory`

## U1.1 postoperative contract ? approved

- Frozen postoperative estimand and development/test boundary.
- Independent anchor, blood, ICD, and TMA blocks.
- Acquisition, usability, internal missingness, and quality states.
- Fold-bound preprocessing and aggregate-only audit.

## U1.2/V0 clinical safety anchor ? approved

- Extended clinical-pathological elastic-net Cox anchor.
- Repeated nested development OOF evaluation.
- Training-fold preprocessing and baseline survival.
- Exact V0 safety/fallback reference established.

## U1.3/V1 structural smoke ? approved

- Dependency-free deterministic NumPy reference.
- Separate blood, ICD, and TMA adapters.
- Identity, status, and quality encoding.
- Shared `phi`, masked-mean Deep Sets pooling, and shared `rho`.
- Residual formula and exact empty-set clinical fallback.

## U1.4/V1 trainable synthetic smoke ? complete, awaiting approval

- PyTorch 2.12.1+cpu frozen in the project environment.
- Trainable implementation with unchanged 3,225-parameter architecture.
- Differentiable Breslow Cox loss, Adam, and gradient clipping.
- Deterministic 96-row synthetic optimization for 250 steps.
- Finite nonzero gradients, parameter updates, and 83.21% synthetic loss reduction.
- Pre/post-training permutation invariance and exact fallback preserved.
- No patient data, formal development CV, official-test/external outcomes, calibration, or routing.

## Proposed next step, not yet authorized

U2/V1 formal HANCOCK development cross-validation and the V0-vs-V1 complexity gate. Every learned
preprocessing and model fit must remain inside development folds, and official-test/external
outcomes must remain sealed. Explicit researcher approval is required before beginning U2.
