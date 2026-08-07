# Phase 3 development-only baseline findings

**Date:** 2026-08-07  
**Scope:** B0-B5/M0/N0 development baselines using frozen training and dedicated calibration partitions only.  
**Evidence class:** Development and calibration evidence only; not locked, external, or prospective validation.

## 1. Model key and run design

- **B0:** Kaplan-Meier constant-risk baseline.
- **B1:** clinical Cox proportional-hazards model.
- **B2:** clinical elastic-net Cox model.
- **B3:** clinical random survival forest.
- **B4:** available additional-modality-only elastic-net Cox model.
- **B5:** clinical plus additional-modality direct-concatenation elastic-net Cox model.
- **M0:** missingness-indicator-only control.
- **N0:** outcome-independent permuted-modality negative control.

Each available study/model combination was run with five prespecified seeds (`17`, `29`, `43`, `71`, `101`) and five-fold patient-level OOF prediction. Preprocessing and, for TCGA-HNSC, top-500 expression variance selection were fit inside each OOF training fold. A model refit on the full training partition generated predictions for the dedicated calibration partition. Metrics include 24-month IPCW Brier score, Harrell and Uno concordance, dynamic AUC, calibration-in-the-large/slope, and IPCW decision-curve analysis.

Run accounting: **105 successful study/model/seed runs, 0 failures, 10 completed runs with diagnostic warnings, and 3 governance-blocked model entries**. The 10 warnings are five RADCURE M0 zero-coefficient fits and five TCGA-HNSC M0 reductions to B0 because no missingness indicator varied. RADCURE B4, B5, and N0 remain blocked pending validated ORCESTRA RDS structural inspection.

## 2. Dedicated calibration-partition results

Values are means across five seeds. Lower IPCW Brier is better; higher concordance and AUC are better.

### RADCURE

| Model | IPCW Brier | Harrell C | Uno C | 24-month AUC |
|---|---:|---:|---:|---:|
| B0 | 0.1629 | 0.5000 | 0.5000 | 0.5000 |
| B1 | 0.1394 | 0.7348 | 0.7675 | 0.7908 |
| B2 | 0.1431 | 0.7328 | 0.7357 | 0.7609 |
| B3 | **0.1380** | **0.7525** | **0.7700** | **0.7969** |
| M0 | 0.1626 | 0.5639 | 0.5805 | 0.5932 |

The clinical models substantially outperform the event-rate and missingness controls. B3 has the best mean calibration-partition Brier, concordance, and AUC among the authorized models. These findings support the value of structured clinical information but do **not** answer whether radiomics adds value: B4, B5, and N0 could not be run without validated access to the ORCESTRA radiomics structure.

### HANCOCK

| Model | IPCW Brier | Harrell C | Uno C | 24-month AUC |
|---|---:|---:|---:|---:|
| B0 | 0.1512 | 0.5000 | 0.5000 | 0.5000 |
| B1 | 0.1538 | 0.5162 | 0.5798 | 0.6111 |
| B2 | 0.1460 | 0.6328 | 0.6597 | 0.6901 |
| B3 | 0.1406 | 0.6473 | 0.6739 | 0.7100 |
| B4 | 0.1292 | 0.6306 | 0.6881 | 0.7018 |
| B5 | **0.1276** | **0.6948** | **0.7594** | **0.7873** |
| M0 | 0.1498 | 0.6137 | 0.6565 | 0.6686 |
| N0 | 0.1513 | 0.5281 | 0.5290 | 0.5292 |

B5, the direct clinical-plus-blood/TMA fusion model, shows the strongest calibration-partition results and improves over both B2 and B3. B4 also improves Brier relative to the clinical-only models, although its Harrell C is below B3. N0 remains close to the B0 event-rate reference, indicating that outcome-independent row permutation does not reproduce the B5 gain. M0 contains modest prognostic signal, but its results remain materially below B5, so missingness alone does not explain the observed direct-fusion performance.

### TCGA-HNSC

| Model | IPCW Brier | Harrell C | Uno C | 24-month AUC |
|---|---:|---:|---:|---:|
| B0 | 0.2349 | 0.5000 | 0.5000 | 0.5000 |
| B1 | 0.2515 | 0.5971 | 0.5856 | 0.5741 |
| B2 | 0.2422 | 0.4898 | 0.4611 | 0.4368 |
| B3 | **0.2301** | 0.6107 | 0.6152 | 0.6219 |
| B4 | 0.2382 | **0.6266** | **0.6275** | **0.6293** |
| B5 | 0.2482 | 0.6104 | 0.6028 | 0.6001 |
| M0 | 0.2349 | 0.5000 | 0.5000 | 0.5000 |
| N0 | 0.2488 | 0.5114 | 0.5020 | 0.4963 |

The expression-only B4 model has the best mean discrimination, while clinical B3 has the best mean 24-month Brier score. Direct concatenation in B5 does not dominate either component: its Brier score is worse than B0 and B3, and its discrimination is lower than B4. Thus, expression carries prognostic ranking information, but compulsory direct fusion does not consistently translate that information into better absolute 24-month risk prediction. This study-specific tradeoff supports evaluating reliability-aware modality use in a later phase, but it is not itself evidence that a Phase 4 gate will work.

## 3. OOF findings

The training-partition OOF results broadly support the calibration observations while also showing that rankings are not identical across partitions:

- RADCURE B3: IPCW Brier `0.1367`, Harrell C `0.7424`, Uno C `0.7787`, AUC `0.8063`.
- HANCOCK B3 has the lowest OOF Brier (`0.1037`), whereas B5 has Brier `0.1052` and AUC `0.7473`. On the dedicated calibration partition, B5 becomes the strongest model, so the B3/B5 comparison should not be reduced to one metric or one partition.
- TCGA-HNSC B2 and B3 have OOF Brier values `0.2207` and `0.2214`; B5 reaches the highest OOF AUC (`0.6280`) but has Brier `0.2239`. On calibration, B4 has the best discrimination and B3 the best Brier.
- N0 is near chance or materially worse in HANCOCK and TCGA-HNSC, consistent with the intended negative-control behavior.

## 4. Calibration and decision-curve cautions

Calibration intercepts and slopes are retained in the aggregate result files, but they should not be overinterpreted for constant-risk or negative-control models. A constant prediction has no estimable calibration slope, and weak/degenerate predictors can produce unstable or extreme slopes. The Phase 3 decision curves are exploratory development/calibration diagnostics only; no decision threshold, reliability threshold, augmentation rule, fallback rule, or abstention rule was selected.

## 5. Governance interpretation

- No RADCURE challenge-test, HANCOCK OOD-test, GSE65858, or GSE41613 outcome was loaded for model fitting or evaluation.
- Patient-level OOF and calibration predictions are confined to Git-ignored `results/predictions/phase3/`.
- Tracked outputs are aggregate metrics, figures, audits, and the hashed receipt.
- Phase 4 residual learning and reliability/OOD/uncertainty gates were not implemented or run.

## 6. Phase 3 conclusion

Phase 3 is complete within the authorized conditional scope. It establishes three development-only observations: clinical baselines are strong in RADCURE; structured blood/TMA fusion is promising in HANCOCK; and TCGA-HNSC expression improves discrimination without making direct fusion uniformly superior in Brier score. These observations motivate—but do not validate—the planned TRUST-HN reliability framework.

Phase 4 remains unauthorized. Before any Phase 4 work, the user should review these results, the persistent RADCURE radiomics blocker, and the fact that no locked or external performance evidence has yet been generated.
