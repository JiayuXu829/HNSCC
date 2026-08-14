# U2/V1 development cross-validation and V0-vs-V1 complexity-gate audit

**Audit date:** 2026-08-14  
**Study:** PATTERN-Surv-HN  
**Stage:** U2/V1 development cross-validation  
**Analysis label:** `post_lock_exploratory`  
**Final frozen decision:** `V1_DOES_NOT_EARN_COMPLEXITY`

## 1. Authorization and scope

The researcher approved U1.4 and explicitly authorized U2/V1 development-only cross-validation and the prespecified V0-vs-V1 complexity gate. The authorized cohort was restricted to eligible HANCOCK `official_training` records. Official-test outcomes and all external outcomes remained sealed. V2, calibration bridge, Global Value Router labels/actions, router training, and external validation were not authorized.

The development estimand contained 610 eligible patients and 173 events. The U2 protocol and gate were written before formal execution:

| Frozen artifact | SHA256 |
|---|---|
| `frozen_u2_v1_development_cv_spec.yaml` | `32A5FA433B03D8A80B7D0E2676A6DB1FFC30FE602F09A4A1E0B1336CB85AD4C4` |
| `frozen_v0_v1_complexity_gate.yaml` | `70F79547E6452DF8D9F45C3881A2970EA1C27EFB47AC5C2961FEF3EA16220FA3` |
| frozen V0 OOF reference | `B58C713DA7D98546AED8B581BD942A1DA3F81ED7FBF28053051AFE59FDFEF141` |

No gate threshold was changed after result inspection.

## 2. Frozen design executed

- outer repeated CV: 5 folds × seeds 17, 29, 43, 71, 101;
- inner CV: 3 folds;
- exact V0 outer assignments and fold-specific selected clinical-anchor candidates reused;
- fixed 3,225-parameter `Clinical_Residual_Deep_Sets_Cox` architecture;
- final residual head initialized to zero;
- inner search restricted to residual penalties 0.01/0.1 and checkpoints 0/25/50/100/200;
- CPU float64 PyTorch, Adam, learning rate 0.003, weight decay `1e-4`, gradient clipping 5.0;
- fold-bound refitting of clinical, blood, ICD, and TMA preprocessing;
- training-fold Breslow baseline only for 24-month absolute risk;
- supported acquisition pattern gate: `n >= 30` and events `>= 10`.

The implementation reindexed modality frames to the master patient contract before fold-bound preprocessing. This preserved all-NaN placeholders for absent modalities while fitting statistics only from observed training-fold values.

## 3. OOF completeness and structural reconstruction

| Check | Result |
|---|---:|
| expected / observed OOF rows | 3,050 / 3,050 |
| unique patients per seed | 610 for all 5 seeds |
| outer folds per seed | 0–4, complete |
| nonfinite numeric OOF values | 0 |
| max V0 score reconstruction error | `4.44e-16` |
| max V0 risk reconstruction error | `9.71e-17` |
| empty-set residual max error | `0.0` |
| clinical fallback fused-score max error | `0.0` |
| V0/V1 coverage | 100% / 100% |
| trainable parameters | 3,225 |

The patient-level OOF file is stored only under the git-ignored predictions root. The tracked JSON contains aggregate folds, seeds, patterns, gate results, hashes, and governance flags; its recursive sensitive-key guard rejects patient identifier keys.

## 4. Inner-selection behavior

Across 25 outer folds:

| residual penalty | steps | selected folds |
|---:|---:|---:|
| 0.01 | 25 | 3 |
| 0.1 | 0 | 10 |
| 0.1 | 25 | 7 |
| 0.1 | 50 | 5 |

The zero-step checkpoint was selected in 10/25 folds. Because the final residual head starts at zero, these selections retain exact V0-equivalent residual behavior. Scientifically, the inner procedure frequently preferred no learned fusion correction over the trained V1 residual.

## 5. Frozen complexity-gate result

### 5.1 Coverage and structural gates

```text
V0 coverage                         1.000000  PASS
V1 coverage                         1.000000  PASS
fallback residual max error         0.0       PASS
fallback fused max error            0.0       PASS
parameter count                     3,225     PASS (ceiling 50,000)
```

### 5.2 Safety gate

| Safety requirement | Frozen threshold | Observed | Result |
|---|---:|---:|---|
| mean delta IPCW Brier24, V1−V0 | `<= +0.005` | `+0.001801` | PASS |
| worst supported-pattern Brier regret | `<= +0.020` | `+0.023779` | **FAIL** |
| mean absolute CITL deterioration | `<= 0.10` | `+0.003924` | PASS |
| mean calibration-slope error deterioration | `<= 0.15` | `+0.213075` | **FAIL** |

The worst supported-pattern regret occurred for acquisition pattern `101` under seed 29 (`n=43`, 13 events): Brier24 changed from 0.147956 for V0 to 0.171735 for V1, a regret of `+0.023779`. This exceeded the frozen safety limit.

### 5.3 Incremental-value gate

| Qualifying path | Frozen requirement | Observed | Result |
|---|---|---|---|
| probability error | mean Brier delta `<= -0.002` and at least 3 improving seeds | `+0.001801`; 2/5 seeds | **FAIL** |
| discrimination | mean Uno-C delta `>= +0.01` and at least 3 improving seeds | `+0.002116`; 3/5 seeds | **FAIL** effect size |

Although Uno C moved in the favorable direction in 3/5 seeds, the mean gain was only `+0.002116`, below the frozen `+0.01` effect-size requirement. Directional stability alone therefore did not qualify V1.

### 5.4 Final decision

```text
coverage gate                      PASS
structural gate                    PASS
safety gate                        FAIL
incremental-value gate             FAIL
all required gates                 FAIL
final decision                     V1_DOES_NOT_EARN_COMPLEXITY
```

Under the frozen rule, V0 remains the current core backbone. Post-hoc threshold relaxation, V1 promotion, or automatic V2 escalation is prohibited.

## 6. Reproducibility and testing

Formal output hashes:

```text
aggregate audit SHA256
4066C2F0CD3D58061EDA15CD5CDBF7902F0BCA5E4B906D494F82596D4CFFFD1A

patient OOF SHA256
81F2369B5469167139D2A1B85F549E89690449A40A0A8878864F098B920134CE
```

An independent complete rerun wrote to a separate git-ignored directory. Its patient OOF SHA256 exactly matched the formal output. After normalizing only the intentionally different output path, the complete aggregate-audit payload also matched exactly.

```text
PATTERN U1–U2 tests                         40 passed
related Phase 2/3 tests                     23 passed
Phase 6 registered-file integrity guard      1 passed
full repository                            140 passed / 1 inherited failure
pip check                                    PASS
targeted Ruff                                PASS
```

The sole full-suite failure remained `tests/test_phase6_statistics.py::Phase6StatisticsTests::test_outcomes_refuse_access_before_consumption`. It reflects the pre-existing consumed Phase 6 authorization state: the test expects pre-consumption refusal, while the repository state is already post-consumption. U2 did not alter Phase 6 registered files, and the dedicated registered-file integrity guard passed.

## 7. Governance and claim boundary

| Item | U2 state |
|---|---|
| official-test outcomes derived/exposed/evaluated | no |
| external outcomes used | no |
| V2 trained | no |
| calibration bridge trained | no |
| router labels created | no |
| router trained | no |
| coverage reduced to improve results | no |
| tracked artifacts aggregate-only | yes |
| patient-level OOF tracked | no |

Supported claims are limited to internal, post-lock exploratory development evidence that V1 preserves full coverage and exact fallback but fails the frozen complexity gate. U2 does **not** support fusion superiority, external generalization, transportability, calibration-bridge benefit, routing benefit, or clinical utility.

## 8. Audit conclusion

**U2 execution is complete, but V1 is rejected at the frozen complexity gate.** The scientifically correct action is to retain V0 unless the researcher separately authorizes a newly preregistered diagnostic or redesign stage. Stop at `U2_V1_DEVELOPMENT_CV_APPROVAL_ONLY`.
