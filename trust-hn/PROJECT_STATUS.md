# TRUST-HN Project Status

**Last updated:** 2026-08-07
**Current gate:** Phase 2 complete within the user-approved conditional scope; awaiting explicit review before Phase 3.
**Sealed or external outcomes used for preprocessing, selection, tuning, calibration, or thresholds:** No.

## Phase status

| Phase | Status | Evidence / decision |
|---|---|---|
| 0. Repository and governance | Complete | Governance, configuration, templates, acquisition policy, and sealed-test refusal are implemented. |
| 1. Data acquisition and feasibility audit | Complete with conditions | Authorized artifacts acquired, hashed, extracted, audited, manifested, and frozen read-only. |
| 2. Unified adapters and descriptive analysis | Complete with one modeling blocker | Three adapters, unified contract/schema, Table 1 candidates, missingness, event, Kaplan–Meier, and composition-comparison outputs are generated. ORCESTRA RDS structural validation remains required before radiomics modeling. |
| 3. Baselines | Not authorized | Requires explicit user authorization after Phase 2 review. |
| 4. TRUST-HN core | Not authorized | Requires baseline review. |
| 5. Stress tests and freeze | Not authorized | Not started. |
| 6. Locked/external tests | Sealed | Must remain unavailable for tuning and may be evaluated only after analysis freeze and explicit approval. |
| 7. Paper | Skeleton only | Results text must remain placeholder until real analyses are complete. |
| 8. Reproduction/submission | Not started | Not started. |

## Phase 2 evidence snapshot

- Three adapter classes: `RadcureAdapter`, `HancockAdapter`, and `TranscriptomicsAdapter`.
- Unified immutable record contract and JSON Schema v2.0.
- RADCURE: 3,346 source records; 2,144 primary eligible exact invasive SCC records; 1,215 train, 303 calibration, 626 sealed test.
- HANCOCK: 763 eligible records; 489 train, 122 calibration, 152 sealed OOD test.
- TCGA-HNSC: 520 expression/clinical-overlap records; 416 train, 104 calibration; 519 usable OS endpoints and one unresolved duration.
- GSE65858: 270 source samples; 244 frozen primary/nonmetastatic/nonpalliative external-test samples.
- GSE41613: 97 HPV-negative OSCC sensitivity samples; follow-up unit frozen as months and converted by 30.4375 days/month when audited.
- Aggregate outputs include cohort flow, Table 1 candidates, missingness, development-only event summaries, Kaplan–Meier coordinates/SVG, and covariate-only composition comparisons.
- Patient-level adapter records are stored only in Git-ignored `data/interim/phase2/`.
- Automated verification: 45 tests passed after Phase 2 integration.

## Frozen endpoint and population decisions

1. RADCURE OS origin is the first radiotherapy fraction: `Last FU - RT Start`. The diagnosis-origin `Length FU` field is not used by the adapter.
2. RADCURE primary histology uses trimmed, case-insensitive exact equality to `Squamous Cell Carcinoma`; in-situ, verrucous, ambiguous, and non-SCC labels are excluded from the primary cohort.
3. HANCOCK OS is measured from diagnosis to last information/death, matching its data dictionary.
4. GSE65858 external eligibility is `Primary AND distant_metastasis == 0 AND treatment != palliative`.
5. GSE41613 is an HPV-negative OSCC sensitivity cohort. The source article reports follow-up in months; the frozen day conversion is `months x 30.4375`.
6. Test/external outcomes are absent from adapter records and tracked summaries.

## Remaining risks and conditions

1. The ORCESTRA RDS cannot be exposed for radiomics modeling until its structure is validated with R/Rscript or a validated parser.
2. One TCGA-HNSC expression case has unresolved OS duration; it remains in the clinical/expression cohort but is excluded from endpoint-dependent summaries.
3. RADCURE contains one aggregate date-reconciliation discrepancy between `Date of Death` and `Last FU`; the adapter consistently uses source-defined `Last FU` and the discrepancy does not create a negative duration.
4. Cross-study covariate differences are descriptive and do not authorize harmonization choices based on external outcomes.

## Next checkpoint

Review the bilingual Phase 2 completion report and make an explicit go/no-go decision. A GO for Phase 3 would authorize baseline implementation only; it would not authorize TRUST-HN core training, threshold optimization on locked/external outcomes, or final sealed-test evaluation.
