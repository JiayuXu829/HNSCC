# TRUST-HN Phase 6 Completion Report

**Date:** 2026-08-08  
**Phase:** One-time locked retrospective and external evaluation  
**Decision:** Complete. The prespecified authorization was consumed once, all four frozen cohorts were evaluated, and no outcome-guided retuning was performed.

## 1. Scope and governance

Phase 6 executed the frozen evaluation plan after explicit project-owner authorization. Before outcomes were loaded, the workflow verified the Phase 5 freeze, the Phase 6 decision-file hashes, the sealed cohort counts and ordered-identifier digests, the outcome-free prediction receipt, and the one-time authorization-token hash. The plaintext token remains only in the Git-ignored runtime area and is not reproduced in this report.

The authorization was consumed at `2026-08-08T02:21:33+00:00`. After consumption, the analysis state was changed to `CONSUMED_FOR_LOCKED_EVALUATION`. The registered Phase 6 decision files are now immutable for purposes of deterministic reproduction. Outcomes were not used for preprocessing, feature selection, hyperparameter selection, gate selection, threshold switching, or model retuning.

All tracked Phase 6 outputs are aggregate. Patient-level predictions are restricted to the Git-ignored directory `results/predictions/phase6/`.

## 2. Cohorts and roles

| Cohort | Frozen role | Patients | Interpretation |
|---|---|---:|---|
| RADCURE | Locked retrospective test | 626 | Pretreatment CT-radiomics setting; includes prespecified shuffled and randomized radiomic negative controls. |
| HANCOCK | Retrospective OOD test | 152 | Official out-of-distribution surgical/multimodal split. |
| GSE65858 | Retrospective external test | 244 | Independent cross-platform transcriptomic validation after outcome-independent common-gene harmonization. |
| GSE41613 | Retrospective sensitivity cohort | 97 | HPV-negative OSCC sensitivity analysis; not a general HNSCC external validation cohort. |

All cohort sizes and ordered identifier-set digests matched the sealed manifest.

## 3. Frozen methods

The models were trained separately within each clinical/data ecosystem; this is a test of a shared reliability principle, not one universally shared parameter set.

- **B2:** clinical elastic-net Cox anchor.
- **B4:** additional-modality-only elastic-net Cox model.
- **B5:** direct early fusion of clinical and additional-modality features.
- **B6:** stacked residual elastic-net Cox fusion model using a cross-fitted B2 anchor score and training-derived modality representation.
- **B7:** reliability-gated layer. It returns `AUGMENT` with B6, `FALLBACK` to B2 when the added modality is unreliable or unavailable, and `ABSTAIN` when the clinical input or total prediction is unreliable.

Five frozen seeds (`17, 29, 43, 71, 101`) were used. Base-model risks were averaged arithmetically across seeds. B7 actions were aggregated by majority vote with a minimum of three votes and precedence `ABSTAIN`, then `FALLBACK`, then `AUGMENT`. Consensus fallback risks were replaced by the mean B2 risk, while consensus abstention risks were set to missing.

The primary gate was the prespecified equal-weight gate at nominal 90% calibration coverage. The 80% and 100% profiles were sensitivity analyses. RADCURE used numeric PyRadiomics vectors with foldwise variance selection up to 500 features. The transcriptomic evaluation used within-sample ranks over an outcome-independent intersection of gene symbols, with median aggregation of duplicated gene symbols and foldwise variance selection up to 500 features.

The primary horizon was 24 months (`730.5` days). Evaluation included IPCW Brier score, Harrell C, Uno C, time-dependent AUC, calibration-in-the-large, calibration slope, coverage, action rates, and decision curves. Uncertainty was estimated using 2,000 patient-level paired bootstrap replicates per prespecified analysis. B7-versus-B6 and B7-versus-B2 comparisons were calculated on the identical B7 non-abstained subset.

## 4. Main cohort results

| Cohort | Model | Coverage | IPCW Brier | Uno C | 24-month AUC |
|---|---|---:|---:|---:|---:|
| RADCURE | B2 | 100.0% | 0.1091 | 0.7078 | 0.7145 |
| RADCURE | B6 | 100.0% | 0.0980 | 0.7740 | 0.7838 |
| RADCURE | B7 | 93.3% | 0.0913 | 0.7567 | 0.7602 |
| HANCOCK | B2 | 100.0% | 0.1393 | 0.7476 | 0.7864 |
| HANCOCK | B6 | 100.0% | 0.1122 | 0.8281 | 0.8476 |
| HANCOCK | B7 | 82.9% | 0.1055 | 0.8249 | 0.8461 |
| GSE65858 | B2 | 100.0% | 0.1964 | 0.5843 | 0.5893 |
| GSE65858 | B6 | 100.0% | 0.2725 | 0.6066 | 0.6035 |
| GSE65858 | B7 | 94.3% | 0.2672 | 0.5892 | 0.5839 |
| GSE41613 | B2 | 100.0% | 0.2674 | 0.5000 | 0.5000 |
| GSE41613 | B6 | 100.0% | 0.2742 | 0.6229 | 0.6377 |
| GSE41613 | B7 | 100.0% | 0.2611 | 0.6337 | 0.6555 |

B7's raw cohort-level Brier values are selective metrics and must not be interpreted as ordinary full-cohort improvements. The paired same-subset analyses below are the correct direct comparisons.

## 5. Primary paired comparisons

Differences are B7 minus comparator. Negative Brier differences favor B7; positive AUC differences favor B7.

| Cohort | Comparison | Brier difference (95% CI) | 24-month AUC difference (95% CI) |
|---|---|---:|---:|
| RADCURE | B7 vs B6 | +0.00382 (+0.00084 to +0.00718) | -0.01662 (-0.03467 to -0.00053) |
| RADCURE | B7 vs B2 | -0.00489 (-0.00795 to -0.00193) | +0.03720 (+0.01086 to +0.06461) |
| HANCOCK | B7 vs B6 | +0.01058 (-0.00947 to +0.03186) | -0.00625 (-0.09059 to +0.07497) |
| HANCOCK | B7 vs B2 | -0.00723 (-0.01612 to +0.00022) | +0.08696 (-0.03808 to +0.24154) |
| GSE65858 | B7 vs B6 | -0.00812 (-0.01584 to -0.00183) | -0.01268 (-0.04663 to +0.01344) |
| GSE65858 | B7 vs B2 | +0.07294 (+0.04250 to +0.10389) | +0.02628 (-0.09521 to +0.14885) |
| GSE41613 | B7 vs B6 | -0.01314 (-0.03153 to +0.00215) | +0.01779 (-0.02650 to +0.06057) |
| GSE41613 | B7 vs B2 | -0.00632 (-0.04051 to +0.03008) | +0.15551 (+0.02973 to +0.27362) |

### Interpretation by cohort

- **RADCURE:** B6 transferred well. On retained patients, B7 was significantly worse than B6 for Brier score and 24-month AUC, although it remained better than B2. The lower unpaired B7 cohort-level Brier partly reflects selective coverage and cannot establish gate superiority.
- **HANCOCK:** B6 showed good retrospective OOD discrimination and Brier performance. B7 reduced coverage to 82.9%; paired evidence versus B6 and B2 was imprecise and did not establish an advantage.
- **GSE65858:** B7 reduced some B6 Brier error, but both B6 and B7 were substantially worse calibrated than B2. This is a clear negative external finding for transcriptomic fusion under platform shift.
- **GSE41613:** B7 showed encouraging discrimination, but comparisons were imprecise and B2 was constant/non-discriminating because the available external clinical representation did not differentiate patients. This cohort is sensitivity evidence only.

Decision-curve analysis did not show a consistent B7 net-benefit advantage. B7 was below B6 across all evaluated thresholds in RADCURE and HANCOCK and across most thresholds in GSE65858. These retrospective curves therefore do not establish clinical utility.

## 6. Gate action distribution

At the frozen 90% primary gate:

| Cohort | AUGMENT | FALLBACK | ABSTAIN | Non-abstention coverage |
|---|---:|---:|---:|---:|
| RADCURE | 82.1% | 11.2% | 6.7% | 93.3% |
| HANCOCK | 64.5% | 18.4% | 17.1% | 82.9% |
| GSE65858 | 92.6% | 1.6% | 5.7% | 94.3% |
| GSE41613 | 95.9% | 4.1% | 0.0% | 100.0% |

These are empirical retrospective action distributions. They are not clinically deployable thresholds and have not been prospectively calibrated to workflow capacity, patient safety, or treatment consequences.

## 7. RADCURE negative controls

Original radiomics did not clearly outperform shuffled or randomized controls. For B4, B5, B6, and B7, every original-minus-control Brier confidence interval crossed zero. Key examples were:

- B6 original vs shuffled: `+0.00124` (95% CI `-0.00105` to `+0.00334`).
- B7 original vs shuffled: `-0.00130` (95% CI `-0.00366` to `+0.00078`).
- B6 original vs randomized: `+0.00063` (95% CI `-0.00200` to `+0.00306`).
- B7 original vs randomized: `-0.00026` (95% CI `-0.00286` to `+0.00238`).

This prevents a claim that the transferred performance reflects a specific radiomic biological signal. Clinical information and distributional properties retained by the controls may explain a substantial part of the observed performance.

## 8. Phase 5 limitations that remain binding

Phase 6 does not erase the development-stage limitations:

1. All 10 Phase 5 development runs completed, but only 7 of 8 prespecified checks passed.
2. HANCOCK failed the clean B7-versus-B6 Brier noninferiority check (`+0.01550` versus margin `+0.01000`).
3. Row permutation degraded B6 but produced only a weak rise in fallback/abstention, showing incomplete detection of semantic modality misalignment.
4. Two exploratory TCGA-HNSC age `>=65` subgroup analyses exceeded the 0.03 Brier-regret flag.

## 9. What Phase 6 supports

Supported statements:

- Prespecified retrospective locked validation was completed in RADCURE.
- Prespecified retrospective OOD validation was completed in HANCOCK.
- Prespecified retrospective external validation was completed in GSE65858.
- GSE41613 was evaluated as a retrospective sensitivity cohort.
- A common reliability framework was evaluated across separate modality ecosystems.
- Fusion performance and gate behavior were cohort-dependent.
- Gating altered coverage and sometimes reduced Brier error, but it did not consistently outperform compulsory fusion.

Unsupported statements:

- prospective validation or prospective clinical benefit;
- a clinically deployable gate threshold;
- established clinical utility, causal patient benefit, or treatment impact;
- universal robustness to distribution shift;
- a single shared model across all cohorts;
- proven radiomics-specific biological signal;
- uniform external generalizability or deployment readiness.

## 10. Reproducibility and outputs

Primary commands:

```powershell
.venv\Scripts\python.exe scripts\run_phase6.py --preflight
.venv\Scripts\python.exe scripts\run_phase6.py --register-authorization
.venv\Scripts\python.exe scripts\run_phase6.py --consume-and-run
```

The authorization commands must not be repeated with a new token unless a separately governed deterministic reproduction is explicitly approved. The completed evaluation generated six aggregate metric tables, four aggregate SVG figures, two Phase 6 receipts, and the RADCURE RDS structural receipt. The locked evaluation used 2,000 bootstrap replicates and completed successfully.

Verification at the Phase 6 implementation checkpoint found **90 passing tests**. Check-only Ruff validation passed for the Phase 6 decision files. Repository-wide Ruff still reports 267 historical issues in older frozen files; these were not auto-fixed because that would alter earlier registered code and does not represent a Phase 6 implementation failure.

## 11. Completion decision

Phase 6 is complete as a one-time retrospective locked/external evaluation. It provides mixed evidence: B6 transferred strongly in RADCURE and HANCOCK, B7 changed selective coverage but did not consistently improve forced fusion, transcriptomic fusion failed to calibrate well in GSE65858, and the radiomic negative controls did not support modality-specific signal. These negative and inconsistent findings are mandatory parts of the manuscript.

The next stage should focus on manuscript integration, reporting-guideline completion, model-card/data-code statements, and a prospective validation protocol. It must not retune Phase 6 models or thresholds using the unsealed outcomes.
