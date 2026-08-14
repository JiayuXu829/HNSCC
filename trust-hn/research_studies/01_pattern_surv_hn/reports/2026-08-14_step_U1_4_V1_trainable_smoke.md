# PATTERN-Surv-HN U1.4/V1 trainable implementation report

**Date:** 2026-08-14
**Status:** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`
**Analysis label:** `post_lock_exploratory`

## 1. What this stage did

U1.4 replaced the fixed NumPy reference weights from U1.3 with a trainable PyTorch implementation
of the same `Clinical_Residual_Deep_Sets_Cox` backbone. The model still takes the V0 clinical score
as its safety anchor and learns only an evidence-dependent residual from the active blood, ICD,
and TMA tokens.

```text
eta_fused = eta_clinical + delta_eta(active modality token set)
```

PyTorch 2.12.1+cpu was installed in the project `.venv` and frozen in an independent U1.4
requirements file. CPU was selected because the model has only 3,225 parameters and deterministic
smoke testing does not justify CUDA compatibility risk.

## 2. What was verified

A deterministic 96-row synthetic survival dataset was used to verify that:

1. the Cox objective differentiates through the adapters, metadata encodings, `phi`, and `rho`;
2. gradients are finite and nonzero;
3. Adam updates parameters and substantially reduces synthetic loss;
4. modality input order does not change the prediction;
5. the empty-token branch remains exact after training;
6. the candidate fused score equals V0 exactly when no additional modality is active.

The Cox loss fell from 3.607239 to 0.605562 in 250 steps, an 83.21% relative reduction. This is an
optimization sanity check, not a prognostic performance result.

## 3. Reproducibility and regression

All 12 aggregate checks passed. Two independent command-line smoke runs produced the identical
SHA256 `12C3E6F85AFDFA99FC9898AC843EAD439B9A5D2AF4F4085D9260C5D168807C34`.

```text
U1.4 targeted tests                   7 passed
all PATTERN U1 tests                 34 passed
related Phase 2/3 tests              23 passed
full repository                    134 passed / 1 inherited Phase 6 state failure
U1.4 Ruff                             PASS
Phase 6 registered-file guard         PASS
pip check                              PASS
```

## 4. Paper interpretation

The V1 backbone is now more than a structural diagram: it is a trainable, small, set-based residual
survival network with a hard clinical fallback contract. The implementation can later serve as the
candidate fusion model evaluated inside formal development cross-fitting.

The core paper story is still incomplete. V1 produces a candidate fused risk score; it does not
decide whether the candidate has sufficient incremental value to justify `FUSE` rather than
`FALLBACK`, `RANK_ONLY`, or `ABSTAIN`. Those actions require cross-fitted value evidence and the
future Global Value Router.

## 5. What was not done

- no HANCOCK patient or real outcome was used in U1.4;
- no formal development cross-validation was run;
- no V0-vs-V1 performance comparison was made;
- no official-test or external outcome was accessed;
- no checkpoint or patient-level output was written;
- no V2, calibration bridge, or Global Value Router was implemented;
- no performance, fusion-benefit, generalization, or clinical-utility claim is supported.

## 6. Proposed next stage

The next scientific stage is **U2/V1 formal development cross-validation plus the V0-vs-V1
complexity gate**. It should place every learned preprocessing and V1 fit inside development folds,
produce development OOF predictions, and determine whether V1 earns its added complexity relative
to V0. Official-test and external outcomes must remain sealed.

**Stop condition:** wait for explicit researcher approval before any patient-level V1 training.
