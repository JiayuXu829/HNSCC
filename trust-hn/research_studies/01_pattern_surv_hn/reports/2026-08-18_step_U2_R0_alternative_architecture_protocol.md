# PATTERN-Surv-HN U2-R0 sequential alternative-architecture protocol report

**Date:** 2026-08-18  
**Status:** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**Analysis label:** `post_lock_exploratory`

## 1. What this stage did

This stage converted the request to try several replacement architectures into a frozen sequential
research plan. It did not assume that another neural network will necessarily improve performance.
Instead, it defined a progression from a low-variance residual stacking control to increasingly
expressive clinical-conditioned and null-expert networks.

## 2. What was frozen

The following order is now prespecified:

```text
R1/CARS     low-variance clinical-anchored residual stacking
R2/CCADS    clinical-conditioned attentive Deep Sets
R3/NE-GRME  null-expert gated residual mixture of experts
R4/CC-RST   conditional residual Set Transformer
```

Every candidate must have its own frozen architecture/hyperparameter specification, structural and
trainable smoke checks, formal development cross-validation, report, and approval gate.

## 3. Why R1 is first

V1 selected its V0-equivalent zero-step checkpoint in 10/25 outer folds. Before increasing neural
complexity, R1 asks a more basic question: can stable modality-specific incremental signal be
extracted using low-variance cross-fitted scores and a strongly regularized residual stacker?

If R1 cannot extract stable value, a larger attention network should not be assumed to solve the
problem. If R1 succeeds, its outputs provide a strong benchmark and possible expert inputs for the
later gated architectures.

## 4. Frozen selection rule

The original V0 complexity gate is reused without threshold relaxation. The first candidate in the
frozen order that passes all coverage, structural, safety, calibration, supported-pattern, and
incremental-value requirements becomes a provisional development backbone.

A failed candidate cannot be rescued by selecting favorable seeds or patterns. Later candidates do
not automatically replace a passing candidate; they require a separately frozen superiority gate.

## 5. What was not done

- no model implementation or optimization;
- no patient-level development prediction;
- no official-test or external-outcome access;
- no calibration bridge;
- no final Global Value Router labels/actions;
- no architecture was declared superior;
- no performance improvement is claimed or guaranteed.

## 6. Next stage requiring approval

The next requested stage is limited to:

```text
U2-R1/CARS frozen specification and smoke implementation
```

That stage will define and structurally validate the low-variance residual stacking candidate. It
will not yet run formal patient-level development CV.

## 7. Validation completed

- both frozen YAML files parse successfully and retain their recorded SHA256 hashes;
- the existing U1-U2 contract/regression suite plus the Phase 6 frozen-file guard completed with
  `41 passed`;
- `git diff --check` reported no whitespace errors;
- no `U+FFFD` or accidental three-question-mark replacement artifacts were found in the U2-R0 files.

Warnings were limited to existing dependency deprecations and the sandboxed inability to write
`.pytest_cache`; no test assertion failed.

