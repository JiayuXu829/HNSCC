# PATTERN-Surv-HN U2/V1R residual-shrinkage rescue report

**Date:** 2026-08-19  
**Status:** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**Analysis label:** `post_hoc_exploratory_rescue`  
**Candidate decision:** `V1R_EARNS_COMPLEXITY`

## 1. Scope and integrity boundary

The original U2 V1 decision remains `V1_DOES_NOT_EARN_COMPLEXITY`. This stage did not edit that
result or its frozen gate. It implemented a result-informed rescue candidate, V1R, using the same
3,225-parameter Clinical Residual Deep Sets Cox architecture with a residual scale selected inside
each inner cross-validation loop.

Official-test and external outcomes remained sealed. Because the rescue design was informed by the
original development result, this is internal exploratory evidence rather than confirmatory proof.

## 2. Rescue design

V1R uses:

```text
eta_V1R = eta_V0 + lambda * delta_eta_V1
```

The inner procedure jointly selected residual penalty, optimization checkpoint, and residual scale.
The frozen scale grid was `0.1, 0.2, 0.3, 0.4, 0.5, 1.0`; the penalty grid was `0.01, 0.1, 1.0`; and
checkpoints were `0, 10, 25, 50`. Every selection remained fold-bound.

The scale distribution across 25 outer folds was:

```text
0.1: 1 fold    0.2: 1 fold    0.3: 5 folds
0.4: 3 folds   0.5: 6 folds   1.0: 9 folds
```

Only 1/25 folds selected step 0, compared with 10/25 for the original V1.

## 3. Main paired development result

```text
coverage V0 / V1R                         1.0 / 1.0       PASS
exact empty-set residual/fallback         0.0 / 0.0       PASS
mean delta IPCW Brier24                  -0.000407        PASS safety
worst supported-pattern Brier regret     +0.009848        PASS
mean absolute CITL deterioration         +0.008843        PASS
mean calibration-slope error worsening   +0.085784        PASS
mean delta Uno C24                       +0.021303        PASS effect size
Uno-C improving seeds                     5 / 5           PASS stability
```

V1R passed every unchanged numerical threshold from the original U2 gate. It also passed the
separately frozen relaxed exploratory rescue gate. The qualifying original-threshold path was
24-month discrimination: mean Uno-C improvement exceeded `+0.01` and was favorable in all five
seeds.

## 4. Important remaining instability

The result is not uniformly favorable. Seed 29 had Brier deterioration of `+0.003496`, and its
calibration slope deteriorated substantially. The worst supported pattern remained pattern `101`
under seed 29, although its Brier regret decreased from the original V1 value `+0.023779` to
`+0.009848`, now below the frozen `+0.020` safety limit. Pattern `101` under seed 101 still had a
negative Uno-C delta of approximately `-0.0542`.

Thus V1R controls the original negative-transfer boundary substantially better, but does not remove
all seed- or pattern-level heterogeneity.

## 5. Reproducibility

The formal patient-level OOF SHA256 was:

```text
E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0
```

A complete independent rerun produced the exact same patient-level SHA256. After normalizing only
the intentionally different output path, the complete aggregate payloads were identical.

The residual-scale extension also reproduced the original frozen V1 output exactly when the default
scale grid was `(1.0,)`:

```text
original V1 OOF SHA256 after extension
81F2369B5469167139D2A1B85F549E89690449A40A0A8878864F098B920134CE
```

## 6. Interpretation for the paper

The defensible development claim is:

> A fold-selected shrinkage of the V1 multimodal residual converted the unstable unscaled fusion
> into a development candidate with full coverage, exact clinical fallback, acceptable calibration
> safety, and seed-stable discrimination gain relative to V0.

It is not defensible to say that the original prespecified V1 passed, or that V1R has confirmed
superiority, external generalization, transportability, or clinical utility. The next step requires
researcher approval and a frozen confirmation protocol before any official-test access.
