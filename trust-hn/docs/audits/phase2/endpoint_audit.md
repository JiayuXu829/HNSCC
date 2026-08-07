# Phase 2 endpoint audit

**Scope:** adapter construction and descriptive analysis only; no model fitting occurred.

## Governance

- Development train/calibration outcomes may be summarized.
- RADCURE challenge-test and HANCOCK OOD-test outcomes are suppressed.
- GSE65858 and GSE41613 outcomes are suppressed from Phase 2 adapter records and reports.
- External outcomes were not used for preprocessing, selection, tuning, calibration, or thresholds.

## Cohort endpoint status

| Study | Records | Eligible | Endpoint usable | Sealed outcomes | Unresolved |
|---|---:|---:|---:|---:|---:|
| GSE41613 | 97 | 97 | 0 | 97 | 0 |
| GSE65858 | 270 | 244 | 0 | 244 | 0 |
| HANCOCK | 763 | 763 | 611 | 152 | 0 |
| RADCURE | 3346 | 2144 | 1518 | 626 | 0 |
| TCGA-HNSC | 520 | 520 | 519 | 0 | 1 |

## Frozen endpoint decisions

- **RADCURE:** overall survival is `Last FU - RT Start`, indexed at the first radiotherapy fraction. All 3,346 source rows have parseable dates and nonnegative differences. `Length FU` remains diagnosis-origin and is not used by the Phase 2 adapter.
- **HANCOCK:** overall survival is diagnosis-to-last-information/death in days, matching the source data dictionary.
- **TCGA-HNSC:** deceased cases use nonnegative `days_to_death`; living cases use the maximum available follow-up day. Only expression/clinical-overlap cases enter the adapter.
- **GSE65858:** external eligibility is frozen as primary tumor, no distant metastasis, and non-palliative treatment; outcomes remain sealed.
- **GSE41613:** the source article reports follow-up in months (PMCID PMC3593802); the frozen conversion is `months x 30.4375`. This remains an HPV-negative OSCC sensitivity cohort and outcomes remain sealed.

## Remaining non-blocking condition

- ORCESTRA radiomics are not exposed because the RDS structure still requires validation with R/Rscript or a validated parser. This blocks radiomics modeling, not Phase 2 clinical descriptive work.

**Serious unresolved endpoint errors:** 0 within the authorized Phase 2 scope.
