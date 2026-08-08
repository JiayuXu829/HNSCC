# Phase 5 development findings and interpretation audit

**Date:** 2026-08-07  
**Scope:** Frozen HANCOCK and TCGA-HNSC development train/calibration partitions only.  
**Locked/external outcomes used:** No.

## Execution

- Successful study/seed runs: 10/10.
- Failed runs: 0.
- RADCURE modality-dependent entry: blocked because the ORCESTRA RDS structure remains unvalidated.
- Seeds: 17, 29, 43, 71, 101.
- Bootstrap ensemble size: 20 per fit scope.
- Primary gate: full equal-weight reliability score at nominal 90% calibration coverage.

## Main development results

| Study | B2 clean Brier | B5 clean Brier | B6 clean Brier | Primary B7 selective Brier | Primary B7 coverage |
|---|---:|---:|---:|---:|---:|
| HANCOCK | 0.1460 | 0.1276 | 0.1289 | 0.1177 | 0.9016 |
| TCGA-HNSC | 0.2422 | 0.2482 | 0.2442 | 0.2324 | 0.9038 |

B7 values are calculated only on non-abstained rows. They must not be interpreted as ordinary full-cohort improvements.

## Prespecified acceptance checks

Seven of eight study-level checks passed. The sole failure was HANCOCK clean primary B7 versus B6 on the identical non-abstained subset: Brier difference `+0.01550`, exceeding the noninferiority margin `+0.01000`. The prespecified equal-weight 90% gate remains frozen; the apparently more favorable learned-weight result was not selected post hoc.

Both studies passed complete-modality-dropout recovery: the 100% profile produced a fallback rate of 1.0 and B7 exactly matched B2 Brier. Both also passed the prespecified severe-shift action-response check, which averages location shift and complete modality dropout.

## Negative-control limitation

Row permutation degraded B6 Brier from 0.1289 to 0.1530 in HANCOCK and from 0.2442 to 0.2791 in TCGA-HNSC. However, the primary gate's fallback-plus-abstain rate changed only from 0.167 to 0.174 and from 0.181 to 0.202. Therefore, the current reliability score does not reliably detect every semantic modality-alignment failure. This must be treated as a limitation, not hidden by the aggregate severe-shift acceptance result.

## Subgroup and sensitivity findings

- Exploratory worst-group comparison produced 85 eligible seed/group evaluations. 2 exceeded the 0.03 Brier-regret flag versus B2; both were TCGA-HNSC age >=65 groups (n=34) at seeds 29 and 71, with regrets 0.04881 and 0.03789.
- HANCOCK median-imputation-without-indicators sensitivity caused little clean-data change, but dropout performance remained perturbation-dependent.
- TCGA-HNSC within-sample rank representation yielded mean clean Brier 0.2361 for B4 and 0.2463 for B6; this is a sensitivity analysis and does not replace the frozen primary representation.

## Claim boundary

The completed work supports statements such as: "In development calibration cohorts, the gate responded strongly to complete modality absence and some synthetic perturbations, while preserving an explicit fallback/abstain pathway." It does **not** support claims that robustness under real distribution shift has been proven, that external or prospective validation has been completed, that the threshold is deployment-ready, or that clinical utility has been established.
