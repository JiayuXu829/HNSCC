# TRUST-HN Supplementary Information

> Working supplementary material after Phase 6. All numerical values originate from frozen aggregate outputs under `results/metrics/phase6/`. Patient-level identifiers and predictions are intentionally excluded.

## Supplementary Methods 1: Phase 6 governance

Phase 6 was a one-time retrospective locked/external evaluation. Before outcome access, the pipeline verified: (1) the Phase 5 freeze; (2) hashes of 16 Phase 6 decision files; (3) cohort sizes and ordered identifier-set digests; (4) outcome-free feature/prediction generation; and (5) the registered one-time authorization-token hash. Authorization was consumed on 2026-08-08 at `02:21:33+00:00`. No outcome-guided preprocessing, feature selection, hyperparameter tuning, gate selection, threshold switching, model selection or recalibration was permitted.

The five frozen seeds were 17, 29, 43, 71 and 101. Each fit scope used a 20-model bootstrap uncertainty ensemble. The frozen primary gate was `full_equal_weight_90`; equal-weight profiles at nominal 80% and 100% coverage were sensitivities. Base risks were averaged across seeds. B7 actions used at least three votes with ABSTAIN precedence followed by FALLBACK and AUGMENT.

## Supplementary Table S1: Frozen evaluation cohorts

| Cohort | Role | n | Events | Added-modality setting |
|---|---|---:|---:|---|
| RADCURE | Locked retrospective test | 626 | 110 | PyRadiomics plus shuffled/randomized negative controls |
| HANCOCK | Retrospective OOD test | 152 | 40 | Blood and tissue-microarray/structured multimodal features |
| GSE65858 | Retrospective external test | 244 | 78 | Cross-platform transcriptomics |
| GSE41613 | Retrospective sensitivity | 97 | 51 | Cross-platform transcriptomics in HPV-negative OSCC |

## Supplementary Table S2: Main point estimates

| Cohort | Model | Coverage | Brier | Harrell C | Uno C | AUC | Calibration-in-the-large | Calibration slope |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| RADCURE | B2 | 1.000 | 0.1091 | 0.7012 | 0.7078 | 0.7145 | -0.1409 | 1.4005 |
| RADCURE | B6 | 1.000 | 0.0980 | 0.7636 | 0.7740 | 0.7838 | -0.1433 | 1.3951 |
| RADCURE | B7 | 0.933 | 0.0913 | 0.7457 | 0.7567 | 0.7602 | -0.1931 | 1.4733 |
| HANCOCK | B2 | 1.000 | 0.1393 | 0.7149 | 0.7476 | 0.7864 | 0.3692 | 1.3951 |
| HANCOCK | B6 | 1.000 | 0.1122 | 0.7789 | 0.8281 | 0.8476 | 0.0862 | 1.5149 |
| HANCOCK | B7 | 0.829 | 0.1055 | 0.7724 | 0.8249 | 0.8461 | 0.2566 | 2.4275 |
| GSE65858 | B2 | 1.000 | 0.1964 | 0.5818 | 0.5843 | 0.5893 | -0.7665 | 1.6068 |
| GSE65858 | B6 | 1.000 | 0.2725 | 0.5989 | 0.6066 | 0.6035 | -1.4940 | 0.5992 |
| GSE65858 | B7 | 0.943 | 0.2672 | 0.5789 | 0.5892 | 0.5839 | -1.5481 | 0.5604 |
| GSE41613 | B2 | 1.000 | 0.2674 | 0.5000 | 0.5000 | 0.5000 | -0.2756 | Not estimable |
| GSE41613 | B6 | 1.000 | 0.2742 | 0.6212 | 0.6229 | 0.6377 | -0.6726 | 0.8049 |
| GSE41613 | B7 | 1.000 | 0.2611 | 0.6218 | 0.6337 | 0.6555 | -0.5559 | 0.9892 |

B7 metrics are conditional on non-abstention. They must be interpreted together with coverage and same-subset paired comparisons.

## Supplementary Table S3: B7 paired comparisons on the identical retained subset

| Cohort | Comparator | Retained n | Brier difference (95% CI) | Uno C difference (95% CI) | AUC difference (95% CI) |
|---|---|---:|---:|---:|---:|
| RADCURE | B6 | 584 | +0.00382 (+0.00084, +0.00718) | -0.01423 (-0.03088, -0.00067) | -0.01662 (-0.03467, -0.00053) |
| RADCURE | B2 | 584 | -0.00489 (-0.00795, -0.00193) | +0.03804 (+0.01517, +0.06383) | +0.03720 (+0.01086, +0.06461) |
| HANCOCK | B6 | 126 | +0.01058 (-0.00947, +0.03186) | -0.01726 (-0.08544, +0.04963) | -0.00625 (-0.09059, +0.07497) |
| HANCOCK | B2 | 126 | -0.00723 (-0.01612, +0.00022) | +0.08804 (-0.02147, +0.23258) | +0.08696 (-0.03808, +0.24154) |
| GSE65858 | B6 | 230 | -0.00812 (-0.01584, -0.00183) | -0.01082 (-0.04088, +0.01150) | -0.01268 (-0.04663, +0.01344) |
| GSE65858 | B2 | 230 | +0.07294 (+0.04250, +0.10389) | +0.03227 (-0.07865, +0.14385) | +0.02628 (-0.09521, +0.14885) |
| GSE41613 | B6 | 97 | -0.01314 (-0.03153, +0.00215) | +0.01088 (-0.02852, +0.04910) | +0.01779 (-0.02650, +0.06057) |
| GSE41613 | B2 | 97 | -0.00632 (-0.04051, +0.03008) | +0.13374 (+0.03053, +0.23346) | +0.15551 (+0.02973, +0.27362) |

Differences are B7 minus comparator. Negative Brier and positive discrimination differences favor B7.

## Supplementary Table S4: Primary gate actions

| Cohort | AUGMENT n (%) | FALLBACK n (%) | ABSTAIN n (%) | Coverage |
|---|---:|---:|---:|---:|
| RADCURE | 514 (82.1%) | 70 (11.2%) | 42 (6.7%) | 93.3% |
| HANCOCK | 98 (64.5%) | 28 (18.4%) | 26 (17.1%) | 82.9% |
| GSE65858 | 226 (92.6%) | 4 (1.6%) | 14 (5.7%) | 94.3% |
| GSE41613 | 93 (95.9%) | 4 (4.1%) | 0 (0.0%) | 100.0% |

## Supplementary Table S5: Selected RADCURE radiomic negative controls

| Model | Comparison | Original-minus-control Brier (95% CI) | Interpretation |
|---|---|---:|---|
| B6 | Original vs shuffled | +0.00124 (-0.00105, +0.00334) | No clear superiority of original radiomics |
| B7 | Original vs shuffled | -0.00130 (-0.00366, +0.00078) | No clear superiority of original radiomics |
| B6 | Original vs randomized | +0.00063 (-0.00200, +0.00306) | No clear superiority of original radiomics |
| B7 | Original vs randomized | -0.00026 (-0.00286, +0.00238) | No clear superiority of original radiomics |

All original-minus-control Brier intervals for B4/B5/B6/B7 crossed zero. The negative controls prohibit a radiomics-specific signal claim.

## Supplementary Methods 2: Decision curves

Decision-curve net benefit was evaluated at thresholds 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45 and 0.50. B7 was below B6 at all thresholds in RADCURE and HANCOCK and at most thresholds in GSE65858. Because B7 may abstain and the study did not define a prospective downstream management pathway for abstained patients, these curves are exploratory retrospective evidence rather than proof of clinical utility.

## Supplementary Methods 3: Development-stage stress tests carried forward

Phase 5 included clean data, random cell dropout, measurement noise, partial location shift, row permutation, complete modality dropout, study-specific block dropout, gate ablations, 80%/90%/100% profiles, subgroup analysis and representation/imputation sensitivity. Ten study-seed runs completed. Seven of eight prespecified checks passed. HANCOCK clean B7-versus-B6 Brier noninferiority failed (+0.01550 versus margin +0.01000). Row permutation degraded B6 but only weakly raised fallback/abstention. Two exploratory TCGA-HNSC age >=65 results exceeded a 0.03 Brier-regret flag.

## Supplementary Table S6: Claim boundaries

| Claim | Current status |
|---|---|
| Retrospective RADCURE locked validation | Supported |
| Retrospective HANCOCK OOD validation | Supported |
| Retrospective GSE65858 external validation | Supported |
| GSE41613 sensitivity analysis | Supported, with restricted applicability |
| Gate consistently superior to forced fusion | Not supported |
| Proven robustness under all distribution shifts | Not supported |
| Radiomics-specific biological signal | Not supported |
| Prospective validation | Not completed |
| Clinically deployable gate threshold | Not established |
| Clinical utility or patient benefit | Not established |
| Single universal model across cohorts | Not evaluated |

## Supplementary reproducibility map

| Artifact | Location |
|---|---|
| Cohort metrics | `results/metrics/phase6/cohort_metrics.csv` |
| Bootstrap intervals | `results/metrics/phase6/bootstrap_confidence_intervals.csv` |
| Paired comparisons | `results/metrics/phase6/paired_comparisons.csv` |
| Action summaries | `results/metrics/phase6/action_summary.csv` |
| Negative controls | `results/metrics/phase6/radcure_negative_controls.csv` |
| Decision curves | `results/metrics/phase6/decision_curve.csv` |
| Locked evaluation receipt | `results/manifests/phase6_locked_evaluation_receipt.json` |
| Outcome-free receipt | `results/manifests/phase6_preunseal_prediction_receipt.json` |
| Patient-level predictions | `results/predictions/phase6/` (Git-ignored) |

The implementation checkpoint reported 90 passing tests. Phase 6 decision-file Ruff checks passed. Repository-wide Ruff has 267 historical findings in older frozen code that were intentionally not auto-fixed.
