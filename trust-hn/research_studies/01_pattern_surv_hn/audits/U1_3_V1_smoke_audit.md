# U1.3/V1 Clinical-Residual Deep Sets structural smoke audit

**Audit date:** 2026-08-14  
**Study:** PATTERN-Surv-HN  
**Stage:** U1.3/V1 smoke implementation  
**Analysis label:** `post_lock_exploratory`

## 1. Authorized scope

Researcher approval on 2026-08-14 authorized only a structural smoke implementation of the
minimum `Clinical_Residual_Deep_Sets_Cox` backbone. Formal V1 development cross-validation, V2,
new dependency installation, calibration bridge, Global Value Router, and official-test/external
outcome evaluation were not authorized.

PyTorch was not present in the project environment. Therefore, this stage used a deterministic
NumPy reference forward pass and synthetic arrays only. This avoids silently expanding the
approved scope while still testing the architectural contract.

## 2. Frozen structural design

| Component | Frozen smoke design |
|---|---|
| clinical anchor input | scalar V0 clinical score `eta_clinical` |
| varying modalities | blood, ICD, TMA |
| fold-preprocessed dimensions | blood 32; ICD 80; TMA 8 |
| modality adapters | separate linear+tanh adapter for each modality |
| token metadata | modality identity + status + quality |
| status levels | absent, acquired unusable, usable complete, usable partial, conditional provenance |
| quality vector | missing fraction, observed fraction |
| set function | shared `phi`, masked mean pooling, shared `rho` |
| token dimension | 16 |
| hidden dimensions | phi 24; rho 16 |
| residual formula | `eta_fused = eta_clinical + delta_eta` |
| empty-set rule | force `delta_eta = 0` exactly |
| reference parameter count | 3,225; frozen ceiling 50,000 |

The empty-set rule is implemented outside `rho`; therefore an MLP bias cannot alter the
clinical-only prediction. Missing or inactive modalities are excluded from pooling, and non-finite
placeholders are permitted only for inactive rows.

## 3. Structural results

| Check | Result | Numeric audit |
|---|---|---:|
| modality adapters | PASS | 3 modality-specific adapters |
| arbitrary subsets | PASS | finite blood+TMA subset output |
| input-order permutation invariance | PASS | max absolute error 0.0 |
| exact zero residual for empty set | PASS | max absolute error 0.0 |
| exact clinical-only fallback | PASS | max absolute error 0.0 |
| identity encoding | PASS | minimum pairwise distance 3.53665 |
| status encoding | PASS | induced max change 0.0189511 |
| quality encoding | PASS | induced max change 0.0100355 |
| Cox loss finite | PASS | negative partial log likelihood 1.96625 |
| Cox score-shift invariance | PASS | error 2.22e-16 |
| parameter ceiling | PASS | 3,225 <= 50,000 |

The aggregate audit was run twice and produced the same SHA256:

```text
84F875B385933A12CFFE10A0786373648BB6B1D7CF15E0E8C4476C89B5F46731
```

## 4. Tests and regression checks

```text
V1 smoke targeted tests:                 9 passed
U1.1 + U1.2 + U1.3 targeted tests:      27 passed
related Phase 2/3 regression tests:      23 passed
Ruff for PATTERN-Surv-HN scope:          PASS
full repository:                         127 passed, 1 known frozen Phase 6 legacy failure
```

The only full-suite failure remains:

```text
tests/test_phase6_statistics.py::
Phase6StatisticsTests::test_outcomes_refuse_access_before_consumption
```

This is the inherited state-dependent failure caused by previously consumed Phase 6 outcome
authorization. U1.3 did not modify the frozen test, loader, or Phase 6 state.

## 5. Leakage, output, and dependency audit

| Guard | Result |
|---|---|
| patient-level data used by smoke | no |
| patient-level output written | no |
| survival outcomes used | no |
| formal development CV | no |
| official-test accessed | no |
| external cohort accessed | no |
| router/calibrator used | no |
| dependency files modified | no |
| PyTorch installed | no |
| tracked audit contains identifier-like keys | no |
| frozen Phase 3–6 key paths modified | 0 |

## 6. Claim boundary

This stage supports only the claim that the proposed V1 structural contract is implementable:
it accepts heterogeneous modality subsets, is invariant to modality input order, carries identity,
status and quality information, adds evidence as a residual to V0, and falls back exactly to V0
when no additional evidence is active.

It does not support claims about discrimination, calibration, fusion benefit, negative-transfer
reduction, routing benefit, transportability, external generalization, or clinical utility.

## 7. Decision

**PASS — structural smoke complete.** Stop at `U1_3_V1_SMOKE_APPROVAL_ONLY`.

The proposed next step is U1.4/V1 trainable implementation plus synthetic optimization smoke.
Because the project environment has no PyTorch installation, that next step requires explicit
dependency approval. Formal V1 development CV remains a separate U2 approval.
