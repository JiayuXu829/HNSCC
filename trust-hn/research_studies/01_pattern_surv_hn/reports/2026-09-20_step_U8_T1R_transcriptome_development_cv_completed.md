# U8 T1R transcriptome development cross-validation completed

**Execution date:** 2026-09-20  
**Frozen protocol date:** 2026-09-07  
**Status:** completed as a post-hoc exploratory method-replication experiment  
**Gate decision:** `T1R_EARNS_COMPLEXITY` under the frozen exploratory gate  
**External validation claim:** not established and not claimed

## Objective

U8 tested whether the V1R residual-shrinkage design can be ported to a single dense transcriptome modality. T1R combines a fold-fitted seven-variable elastic-net Cox clinical anchor with a small trainable transcriptome residual head, and selects residual penalty, optimization checkpoint, and shrinkage scale only in inner cross-validation.

```text
TCGA clinical anchor (7 variables, elastic-net Cox)
+ transcriptome residual (fold-bound top-500 gene ranks -> Linear-Tanh-Linear)
+ inner-CV-selected residual shrinkage
= T1R fused risk score
```

The estimand was the TCGA-HNSC development cohort: **519 patients / 221 events**, 24-month horizon (730.5 days), with 14,417 common genes reduced fold-boundedly to 500. Repeated nested cross-fitting used 5 outer folds, 3 inner folds, and seeds 17, 29, 43, 71, and 101.

## Implementation verification

Before execution, the T1R implementation and governance boundaries were covered by `tests/test_pattern_surv_hn_t1r.py`:

- frozen cohort, horizon, architecture, grids, seeds, and parameter ceiling;
- float64 parameter count of 16,065;
- exact clinical fallback when transcriptome is inactive;
- rejection of non-finite values in active transcriptome rows;
- reduced repeated nested-CV completeness, finite predictions, fold-bound fitting, selected-scale containment, and zero fallback error;
- exploratory gate rejection of an exactly equivalent no-increment model;
- confinement of patient-level output to the git-ignored prediction root.

Results:

```text
tests/test_pattern_surv_hn_t1r.py                   6 passed
V1 smoke + development-CV + T1R targeted suite     20 passed
```

## Development results

Across the five repetition seeds:

| Metric | V0 anchor mean | T1R mean | Mean delta (T1R - V0) | Favorable seeds |
|---|---:|---:|---:|---:|
| IPCW Brier 24m | 0.221795 | 0.218058 | **-0.003737** | 4 / 5 |
| Harrell C | 0.577281 | 0.605919 | **+0.028637** | 5 / 5 |
| Uno C 24m | 0.565199 | 0.597265 | **+0.032066** | 5 / 5 |
| cumulative/dynamic AUC 24m | 0.557362 | 0.600236 | **+0.042874** | 5 / 5 |

Per-seed paired deltas:

| Seed | Delta IPCW Brier | Delta Uno C |
|---:|---:|---:|
| 17 | -0.004443 | +0.037975 |
| 29 | +0.002714 | +0.006398 |
| 43 | -0.004353 | +0.029370 |
| 71 | -0.006560 | +0.048165 |
| 101 | -0.006045 | +0.038420 |

The supported transcriptome-present stratum contained all 519 patients and 221 events. Its worst paired Brier regret was **+0.002714**, below the +0.020 ceiling.

## Frozen exploratory gate

```text
V0 coverage                                     1.0  PASS
T1R coverage                                    1.0  PASS
exact absent-residual maximum error             0.0  PASS
exact clinical-fallback maximum error           0.0  PASS
trainable parameter count                      16065 / <=50000  PASS
mean IPCW Brier delta                        -0.003737 / <=+0.005  PASS
worst supported-pattern Brier regret         +0.002714 / <=+0.020  PASS
mean absolute CITL deterioration             +0.049232 / <=+0.100  PASS
mean absolute slope-error deterioration       -0.084226 / <=+0.150  PASS
probability-error incremental path             PASS (4 favorable seeds, >=3)
discrimination incremental path                PASS (5 favorable seeds, >=3)
overall decision                               T1R_EARNS_COMPLEXITY
```

The selected configuration varied across outer folds; selection frequencies are recorded only in the aggregate audit. No architecture or hyperparameter was changed after observing the result.

## Interpretation boundary

This is **not** a pristine confirmation. TCGA outcomes were already consumed in earlier Phase 6 analyses, so U8 is post-hoc and exploratory. The result supports only:

- internal development evidence that the residual-shrinkage pattern is portable to a transcriptome modality;
- an exploratory directional signal of improved discrimination and slightly lower mean IPCW Brier error relative to the clinical anchor.

It does **not** support confirmatory superiority, external generalization, transportability, clinical utility, or deployment readiness. It must not replace the current paper backbone or the existing locked V1R confirmation analysis.

The optional GEO application in `t1r_external_eval.py` was **not executed as part of this development-CV step**. If pursued, it requires a separate explicit post-hoc external-characterization decision; it could not be promoted to formal external validation.

## Output governance

- Aggregate tracked audit: `research_studies/01_pattern_surv_hn/core_backbone/U8_T1R_transcriptome_residual_shrinkage/aggregate_t1r_transcriptome_development_cv_audit.json`
- Patient-level OOF output: `results/predictions/pattern_surv_hn/U8_T1R/t1r_repeated_nested_oof_predictions.csv` (git-ignored)
- OOF rows: 2,595 = 519 patients x 5 seeds
- Coverage audit: each patient appears exactly once per seed; all predictions finite
- Patient OOF SHA-256: `BFEE9B84F1E27400D2C8A9D3573BA7ED72B24F2A1CA0E0DFFC0BB64FA013619C`
- Aggregate sensitive-key scan: passed; no patient identifiers were copied into the tracked audit