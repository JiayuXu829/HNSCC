# PROBAST+AI Self-assessment for TRUST-HN

**Assessment date:** 2026-08-08  
**Scope:** Risk-of-bias and applicability self-assessment for the retrospective development and Phase 6 validation evidence.  
**Judgments:** Low concern; Some concerns; High concern; Not applicable.

This is a conservative internal assessment. It is not an independent PROBAST+AI review and does not establish suitability for clinical use.

## Summary judgments

| Domain | Development evidence | Phase 6 validation evidence | Applicability to intended clinical use |
|---|---|---|---|
| Participants/data sources | Some concerns | Some concerns | High concern |
| Predictors/input data | Some concerns | High concern | High concern |
| Outcome | Some concerns | Some concerns | Some concerns |
| Analysis | Some concerns | High concern | High concern |
| Overall | High concern for confirmatory clinical claims | High concern for deployment/utility claims | High concern |

## Domain 1: Participants and data sources

**Judgment: Some concerns for bias; high concern for clinical applicability.**

Strengths include public cohorts, frozen roles/counts, hashed cohort identities, patient-level splitting, no outcome-guided Phase 6 selection, and clear separation of RADCURE locked testing, HANCOCK OOD testing and GEO validation.

Concerns are that all cohorts are retrospective secondary datasets with source-specific selection and historical treatment pathways; modality availability can select different patients; GSE41613 is HPV-negative OSCC rather than general HNSCC; and no prospective consecutive enrollment, workflow sampling or real-time failure capture exists.

## Domain 2: Predictors and input data

**Judgment: Some concerns in development; high concern in external validation and applicability.**

Strengths include training-derived preprocessing frozen before outcome access, documented clinical/modality transformations, explicit fallback for missing modalities, and exclusion of identifiers and diagnostic metadata.

Concerns include materially different measurement pipelines across ecosystems; major GSE65858 calibration failure under platform shift; lack of clear superiority of original RADCURE radiomics over shuffled/randomized controls; incomplete Phase 5 detection of semantic modality misalignment; weak or constant external clinical representations, especially GSE41613 B2; and absence of a prospective assay/scan quality-control workflow.

## Domain 3: Outcome

**Judgment: Some concerns.**

Overall survival is comparatively objective, the 24-month horizon was prespecified, outcome loading was separated from feature preparation, and censoring-aware metrics were used. However, cohorts differ in index date, follow-up construction and documentation; retrospective follow-up may be incomplete or heterogeneous; competing risks were not modeled for the all-cause endpoint; and clinical consequences of errors or abstention have not been prospectively specified.

## Domain 4: Analysis

**Judgment: Some concerns for model-development research; high concern for validation, utility or deployment claims.**

Strengths include a prespecified freeze, one-time authorization, five seeds, 2,000 paired patient-level bootstrap replicates, identical-subset B7 comparisons, retention of negative/failed findings, and no Phase 6 retuning or threshold switching.

Concerns include modest event counts after abstention; population selection by B7; lack of a clinical handling pathway for abstained patients; poor calibration in an important external setting; no allowed external recalibration; no consistent B7 decision-curve advantage; failure of one Phase 5 HANCOCK noninferiority check; lack of consistent Phase 6 superiority over B6; evaluation of separately trained systems rather than one universal model; and no prospective sample-size, impact, usability or implementation study.

## AI/reliability-specific considerations

| Topic | Judgment | Reason |
|---|---|---|
| Data leakage control | Low concern | Outcome-free preflight, frozen hashes and patient-level separation were tested. |
| Hyperparameter/threshold optimism | Low concern for Phase 6 | Configuration was frozen and not switched after outcome access. |
| Dataset shift | High concern | Seen as GSE65858 calibration failure and lower HANCOCK B7 coverage. |
| Hidden shortcuts | High concern | Radiomic controls were not clearly inferior; row permutation was incompletely detected. |
| Missing-modality handling | Some concerns | Complete-dropout fallback worked in development, but prospective failure pathways are untested. |
| Uncertainty/action communication | Some concerns | Actions are implemented, but thresholds and downstream actions are not clinically validated. |
| Fairness/subgroups | Some concerns | Older-patient exploratory flags exist; external subgroup power is limited. |
| Reproducibility | Low-to-some concern | Local tests, receipts and hashes are strong; independent reproduction/public archive are pending. |
| Human factors | High concern | No clinician usability, override, workload or automation-bias evaluation. |
| Clinical impact | High concern | No prospective impact or randomized evaluation. |

## Overall conclusion

TRUST-HN has strong governance for a retrospective computational study, but current evidence has **high risk of bias or indirectness for confirmatory clinical-performance, clinical-utility and deployment claims**. It supports transparent retrospective methodological conclusions, including negative findings. A low-risk, clinically applicable or deployment-ready judgment requires prospective site-specific validation, prespecified handling of abstention and missing modalities, workflow quality control, prespecified recalibration rules and an impact study.
