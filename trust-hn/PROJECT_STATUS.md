# TRUST-HN Project Status

**Last updated:** 2026-08-07  
**Current gate:** Phase 1 complete with documented unresolved items; awaiting user go/no-go review before Phase 2.  
**Sealed or external outcomes used for tuning:** No.

## Phase status

| Phase | Status | Evidence / decision |
|---|---|---|
| 0. Repository and governance | Complete | Governance, configuration, templates, acquisition policy, and sealed-test refusal are implemented. |
| 1. Data acquisition and feasibility audit | Complete with conditions | Authorized artifacts acquired, hashed, extracted, audited, manifested, and frozen read-only. The ORCESTRA RDS structural audit and several endpoint/population definitions remain explicit conditions. |
| 2. Unified adapters and descriptive analysis | Awaiting authorization | Conditional GO is recommended, but user approval is required before work begins. |
| 3. Baselines | Not authorized | Requires approved adapters, endpoint definitions, and Phase 2 review. |
| 4. TRUST-HN core | Not authorized | Requires baseline review. |
| 5. Stress tests and freeze | Not authorized | Not started. |
| 6. Locked/external tests | Sealed | Must remain unavailable until analysis freeze and explicit approval. |
| 7. Paper | Skeleton only | Results text must remain placeholder until real analyses are complete. |
| 8. Reproduction/submission | Not started | Not started. |

## Phase 1 evidence snapshot

- Raw-area inventory: 1,068 files, 3,128,490,508 bytes (2.914 GiB).
- Source immutability: 534/534 acquired source files read-only; 533 receipt files intentionally mutable.
- RADCURE: 3,346 unique patients.
- HANCOCK: 763 unique patients.
- TCGA-HNSC: 520 open Primary Tumor STAR-count files/cases; 528 clinical project cases.
- GSE65858: 270 samples.
- GSE41613: 97 samples.
- TCGA expression consistency: 520/520 conforming files, GENCODE v36, 60,664 gene rows per file, one gene identity/order signature.
- Exact native-ID overlap between different cohorts: zero.
- Prohibited imaging, controlled genomic data, and GEO raw files acquired: none.
- Automated verification baseline: 30 tests passed.

## Frozen source versions

- RADCURE clinical: TCIA Version 4, updated 2024-12-19.
- ORCESTRA radiomics: DOI `10.5281/zenodo.14226536`; RDS SHA-256 `32b06ea1acd7b34dd061edea03400ed482144369f41a2d0a9636201608eebd36`.
- HANCOCK repository: commit `521b99b03a94008b28df5c3df4aa5f82aa14b25a`.
- GDC: Data Release 45.0 dated 2025-12-04, API tag 8.5.0, commit `8f7c2a51ab0084b216ad1b62a3fae8b945439c53`.
- GEO processed matrices and platform annotations are frozen in per-study manifests.

## Outstanding conditions

1. Align the RADCURE survival time origin with the intended treatment-start index date.
2. Inspect the ORCESTRA RDS structure with a project-local R runtime or validated parser before radiomics modeling.
3. Prespecify GSE65858 population restrictions.
4. Verify the GSE41613 follow-up-time unit and retain it as an HPV-negative OSCC sensitivity cohort.
5. Continue enforcing sealed-test governance and prohibit external-outcome-guided tuning.

## Next checkpoint

Review the Phase 1 completion report and make an explicit go/no-go decision. A GO authorizes only Phase 2 unified adapters and descriptive analyses; it does not authorize baseline or TRUST-HN model tuning, nor access to locked/external outcomes for tuning.