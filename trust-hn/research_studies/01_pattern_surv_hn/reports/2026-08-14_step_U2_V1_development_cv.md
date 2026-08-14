# PATTERN-Surv-HN U2/V1 development cross-validation report

**Date:** 2026-08-14  
**Status:** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**Analysis label:** `post_lock_exploratory`  
**Frozen decision:** `V1_DOES_NOT_EARN_COMPLEXITY`

## 1. What this stage did

U2 was the first formal patient-level training and comparison stage for the minimum V1 backbone. It used only 610 eligible HANCOCK official-training patients with 173 events. Official-test and external outcomes remained sealed.

The experiment reused V0's exact 5-fold × 5-seed outer cross-validation assignments. Every clinical and modality transform was refitted inside each training fold. A 3-fold inner procedure selected only residual regularization and optimization checkpoint for the fixed 3,225-parameter network. The architecture and gate thresholds were not tuned after seeing results.

## 2. What was produced

- 3,050 complete development OOF rows;
- 610 unique patients in every repetition seed;
- fold-bound V0 and V1 24-month risks;
- overall and supported acquisition-pattern metrics;
- exact V0 reconstruction and empty-modality fallback audits;
- a frozen V0-vs-V1 complexity decision;
- aggregate-only tracked audit and git-ignored patient-level predictions.

The formal patient OOF SHA256 is:

```text
81F2369B5469167139D2A1B85F549E89690449A40A0A8878864F098B920134CE
```

## 3. Main result

V1 passed coverage and structural checks, and its mean Brier deterioration remained within the overall noninferiority tolerance. However, it failed two safety requirements and did not achieve the prespecified incremental-value effect size.

```text
mean delta Brier24, V1−V0                     +0.001801
worst supported-pattern Brier regret           +0.023779  FAIL
mean absolute calibration-slope deterioration  +0.213075  FAIL
mean delta Uno C24, V1−V0                      +0.002116  insufficient
```

The frozen decision is therefore:

```text
V1_DOES_NOT_EARN_COMPLEXITY
```

V0 remains the core backbone at this gate.

## 4. Important failure-boundary evidence

The inner procedure selected optimization step 0 in 10 of 25 outer folds. At step 0, the zero-initialized residual head gives V0-equivalent predictions. This means internal validation often preferred refusing the learned fusion correction rather than applying it.

The worst supported subgroup was acquisition pattern `101` under seed 29 (`n=43`, 13 events), where V1 increased Brier24 by `+0.023779` and reduced Uno C by about `-0.1032` relative to V0. This is precisely the type of pattern-dependent negative transfer that the broader research story seeks to control, but U2 does not yet provide a validated router solution.

## 5. Paper interpretation

This is a scientifically informative negative result, not an implementation failure. It establishes that a small set-based residual fusion backbone can preserve exact fallback and full coverage, but those structural properties alone do not guarantee stable incremental value or calibration safety.

The result does not support presenting V1 as the final method or claiming that multimodal fusion improves HNSCC survival prediction. It may support a failure-boundary or benchmark narrative, but the central method/claim must now be reconsidered before any router work is justified.

## 6. Verification

```text
PATTERN U1–U2 tests                         40 passed
related Phase 2/3 tests                     23 passed
Phase 6 registered-file guard                1 passed
full repository                            140 passed / 1 inherited Phase 6 state failure
pip check                                    PASS
targeted Ruff                                PASS
OOF deterministic rerun                      exact SHA256 match
normalized aggregate payload rerun           exact match
```

The full-suite failure is the same inherited Phase 6 consumed-state mismatch documented in earlier stages. The dedicated registered-file guard passed.

## 7. What was not done

- no official-test outcome was accessed or evaluated;
- no external outcome was accessed or evaluated;
- no V2, calibration bridge, router labels, router actions, or Global Value Router was trained;
- no gate threshold was modified after result inspection;
- no coverage restriction was introduced;
- no external generalization, routing, or clinical-utility claim is supported.

## 8. Next decision requiring approval

This stage stops for researcher approval. The researcher should choose whether to:

1. accept V0 retention and redesign/consolidate the paper around the observed failure boundary;
2. authorize a separately preregistered development-only diagnostic/ablation stage;
3. stop the current backbone line.

No option is authorized automatically. In particular, U2 does not authorize V2, calibration, router development, official-test evaluation, or external validation.
