# U1.4/V1 Clinical-Residual Deep Sets trainable smoke audit

**Audit date:** 2026-08-14
**Study:** PATTERN-Surv-HN
**Stage:** U1.4/V1 trainable implementation
**Analysis label:** `post_lock_exploratory`

## 1. Authorization and scope

The researcher approved U1.4, including installation and freezing of a project-local PyTorch
dependency, but explicitly withheld authorization for formal development CV. Accordingly, this
stage converted V1 to trainable PyTorch modules and optimized only on deterministic synthetic
survival data. It did not load HANCOCK patients or outcomes.

## 2. Frozen dependency

| Item | Frozen value |
|---|---|
| Python | 3.11.9 |
| PyTorch requested | 2.12.1 |
| installed build | 2.12.1+cpu |
| CUDA build / available | none / false |
| environment | project `.venv` |
| install index | official PyTorch CPU wheel index |
| dependency health | `pip check`: no broken requirements |

The dependency is frozen in `requirements-pytorch-cpu.txt` and
`frozen_pytorch_dependency.yaml`. `pyproject.toml` was deliberately restored unchanged because it
is a registered Phase 6 integrity file. No CUDA package was installed.

## 3. Trainable architecture

The implementation inherits the U1.3 frozen contract without widening the network:

- blood/ICD/TMA adapters for 32/80/8 fold-preprocessed inputs;
- learned modality identity and acquisition/status embeddings;
- linear quality projection;
- shared `phi`, masked-mean pooling, and shared `rho`;
- residual formula `eta_fused = eta_clinical + delta_eta`;
- structural empty-set branch that sets `delta_eta = 0` outside the biased `rho` head.

Parameter count is 3,225, below the frozen 50,000 ceiling.

## 4. Synthetic optimization result

The frozen smoke used 96 synthetic rows, float64 CPU execution, Adam for 250 steps, learning rate
0.01, weight decay 0.0001, and gradient clipping at 5.0.

| Check | Result | Numeric audit |
|---|---|---:|
| CPU-only PyTorch runtime | PASS | 2.12.1+cpu |
| finite initial/final loss | PASS | 3.607239 / 0.605562 |
| finite nonzero first gradient | PASS | global norm 0.0410992 |
| parameter update | PASS | L2 change 13.0111 |
| minimum loss reduction | PASS | 83.2126% >= 20% |
| pre-training permutation invariance | PASS | 1.11e-16 |
| post-training permutation invariance | PASS | 3.55e-15 |
| exact empty-set residual | PASS | 0.0 |
| exact clinical fallback | PASS | 0.0 |
| Cox score-shift invariance | PASS | 0.0 |
| parameter ceiling | PASS | 3,225 <= 50,000 |

All 12 recorded audit checks passed. Two complete command-line reruns produced identical aggregate
JSON with SHA256:

```text
12C3E6F85AFDFA99FC9898AC843EAD439B9A5D2AF4F4085D9260C5D168807C34
```

## 5. Tests and regression

```text
U1.4 targeted tests:                    7 passed
U1.1 + U1.2 + U1.3 + U1.4:            34 passed
related Phase 2/3 regression tests:     23 passed
Phase 6 registered-file guard:           1 passed
full repository:                       134 passed, 1 inherited Phase 6 state failure
Ruff for U1.4 implementation/tests:      PASS
```

The inherited full-suite failure remains:

```text
tests/test_phase6_statistics.py::
Phase6StatisticsTests::test_outcomes_refuse_access_before_consumption
```

It reflects the pre-existing consumed Phase 6 authorization state. U1.4 did not modify the frozen
loader, test, state, or registered decision files. Repository-wide Ruff also reports 218 inherited
legacy violations outside the U1.4 files; targeted U1.4 Ruff is clean.

## 6. Leakage and governance audit

| Guard | Result |
|---|---|
| patient-level data used | no |
| real patient outcomes used | no |
| patient-level output written | no |
| model checkpoint written | no |
| formal development CV | no |
| official-test accessed | no |
| external cohort accessed | no |
| router/calibrator used | no |
| identifier-like keys in tracked audit | no |
| registered Phase 6 files changed | 0 |

## 7. Claim boundary and decision

**PASS ? trainable implementation smoke complete.** This stage establishes that the frozen V1
contract is differentiable, optimizable, deterministic, permutation invariant, and still has exact
clinical fallback after optimization. It does not establish prognostic accuracy, incremental
fusion value, calibration, negative-transfer reduction, routing value, generalization, or clinical
utility.

Stop at `U1_4_V1_TRAINABLE_SMOKE_APPROVAL_ONLY`. Formal HANCOCK development CV belongs to U2 and
must not begin without explicit researcher approval.
