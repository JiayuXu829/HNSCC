# TRUST-HN Phase 1 completion report

**Date:** 2026-08-07  
**Phase:** Data acquisition and feasibility audit  
**Decision status:** Conditional GO recommended; Phase 2 remains unauthorized until explicit user approval.

## 1. Scope and governance boundary

Phase 1 acquired and audited only public, protocol-authorized artifacts needed to determine whether the three TRUST-HN studies are technically and scientifically feasible. The work did not construct final modeling matrices, fit models, tune preprocessing, select features using outcomes, calibrate predictions, or inspect held-out outcomes for optimization.

Patient/sample identifier inventories are stored only under Git-ignored `data/interim/phase1_audit/` paths. Tracked manifests and reports contain aggregate counts and hashes, not raw identifier lists.

The following materials were explicitly excluded and were not acquired:

- RADCURE CT, DICOM, RTSTRUCT, and imaging archives;
- HANCOCK WSI/TMA source images, annotations, core images, and UNI encodings;
- controlled-access genomic files;
- GEO raw CEL or FASTQ files.

## 2. Acquired datasets and exact size

| Cohort/source | Authorized content acquired | Audited subjects/samples | Principal acquired size/count |
|---|---|---:|---:|
| RADCURE | Clinical XLSX, ID mapping, ORCESTRA processed-radiomics RDS | 3,346 patients | 3 source artifacts; RDS 842,779,545 bytes |
| HANCOCK | Frozen code snapshot, structured tables, official splits/data dictionaries, pre-extracted TMA cell-density data | 763 patients | 4 source archives |
| TCGA-HNSC | Open-access Primary Tumor STAR-count files plus public clinical/query metadata | 520 expression cases; 528 clinical project cases | 520 expression files; 2,200,875,562 expression bytes |
| GSE65858 | Processed series matrix and GPL10558 annotation | 270 samples | 31,330 matrix feature/probe rows |
| GSE41613 | Processed series matrix and GPL570 annotation | 97 samples | 54,613 matrix feature/probe rows |

The complete `data/raw` inventory contains 1,068 files, including 534 acquired source files, 533 receipt files, and one `.gitkeep` placeholder, totaling 3,128,490,508 bytes (2.914 GiB). All 534 acquired source files are read-only; receipts remain mutable for provenance maintenance.

## 3. Frozen versions and integrity

- **RADCURE clinical:** TCIA Version 4, updated 2024-12-19.
- **ORCESTRA radiomics:** DOI `10.5281/zenodo.14226536`, file `RADCURE_READII-RADIOMICS_MAE.RDS`, 842,779,545 bytes, publisher MD5 `e3d570c4b7e4754681252c55ab7a275a`, SHA-256 `32b06ea1acd7b34dd061edea03400ed482144369f41a2d0a9636201608eebd36`.
- **HANCOCK:** repository commit `521b99b03a94008b28df5c3df4aa5f82aa14b25a`; external FAU objects retrieved on 2026-08-07.
- **GDC:** Data Release 45.0 dated 2025-12-04, API tag 8.5.0, commit `8f7c2a51ab0084b216ad1b62a3fae8b945439c53`.
- **GEO:** processed matrices and platform annotations are frozen with byte counts and SHA-256 values in their per-study manifests.

Per-study manifests are stored under `data/manifests/<study>/data_manifest.yaml`. The consolidated feasibility audit is `data/interim/phase1_audit/phase1_audit.json`, SHA-256 `fcce6ab5eb4c627c764799942523f641936f49e3c30be2f3027658bbc1b6e8e1`.

Final verification parsed 555 JSON files and structurally parsed 17 YAML/YML files, recomputed and matched the byte count and SHA-256 for all 534 manifest entries, confirmed 534/534 acquired source files read-only, found no prohibited acquired-file candidate, and scanned 4,241 governed native identifiers against 34 tracked text files without finding an identifier leak. The complete 30-test suite passed after finalization.

## 4. RADCURE feasibility

The clinical table contains 3,346 rows, 3,346 unique patient identifiers, and no duplicate patient rows. Official challenge labels contain 1,800 training patients, 750 test patients, and 796 patients outside the challenge.

The exact histology label `Squamous Cell Carcinoma` occurs in 2,847 records. A broad descriptive string match for labels containing “squamous” yields 2,906 records across a source field with 41 distinct labels. This broad rule is not approved as the final eligibility definition and must not be used without clinical review.

Metastasis labels are M0 for 3,328 patients, M1 for 2, MX for 2, and missing for 14.

Using the Phase 1 feasibility conversion `Length FU × 365.25` with `Status`, all 3,346 patients have a usable duration/event pair. There are 1,058 deaths over all follow-up. At 24 months, 532 patients died, 2,436 were observed event-free through the horizon, and 378 were censored before the horizon.

Selected clinical missingness includes 1,629 missing HPV values, 32 missing/unknown ECOG values under the audit rule, 50 missing/NA smoking pack-year values, and 45 missing/unknown smoking-status values.

**Critical condition:** the source data dictionary defines `Length FU` from diagnosis to last contact, whereas Study 1 intends a treatment-start index. The time origin must be reconciled before any endpoint adapter or model is finalized.

## 5. HANCOCK feasibility

The master cohort contains 763 patients. Official split counts are:

- in-distribution: training 611, test 152;
- out-of-distribution: training 611, test 152;
- oropharynx holdout: training 432, test 331;
- treatment-outcome split: training 663, test 100.

Each split file covers all 763 patients, contains no duplicates, and assigns no patient to multiple subsets within the same split definition.

Patient coverage is 763 for `clinical.csv`, 763 for `pathological.csv`, 763 for `targets.csv`, 692 for `blood.csv`, 712 for `icd_codes.csv`, and 736 for `tma_cell_density.csv`. NPZ feature coverage ranges from 746 to 760 patients for most markers, with CD163 covering 757 and each archive containing one patient-level NPY member per represented patient.

Overall survival is usable for all 763 patients: 213 deceased and 550 living. At 24 months, 104 deaths occurred, 516 patients were observed event-free, and 143 were censored early.

Recurrence status records 177 yes and 586 no. The recurrence-free survival endpoint contains 303 events, 460 non-events, and no missing duration. Missing `days_to_recurrence` values occur primarily for no-recurrence cases and must be treated as structural rather than ordinary missingness.

## 6. TCGA-HNSC feasibility and expression consistency

The expression manifest contains 520 rows and 520 unique expression cases. The public clinical project set contains 528 cases. All 520 expression cases overlap the clinical set; there are eight clinical-only cases and no expression-only cases. No duplicate expression-case row was found.

Vital status is alive for 304 cases and dead for 224. The feasibility resolver obtains 527 usable duration/event pairs and one missing duration. At 24 months there are 162 deaths, 233 event-free/observed cases, and 132 early-censored cases. This resolver is an audit device, not the final Phase 2 endpoint adapter.

All 520 STAR-count files passed structural consistency checks:

- gene model: GENCODE v36 in 520/520 files;
- 60,664 gene rows in every file;
- one shared header;
- one gene identity/order signature;
- zero malformed files.

The frozen gene identity/order signature is `9b4ff84a4b89cb4c34b9594a5007dcf4565b253ebd658e7c3d38ae8ab535ece3`.

## 7. GEO cohort feasibility

### GSE65858

The series matrix contains 270 samples, 270 matrix columns, and 31,330 feature/probe rows, with no duplicate GEO accessions. Overall survival is usable for all 270 samples: 94 deaths over follow-up; at 24 months, 60 deaths, 173 observed event-free samples, and 37 early-censored samples.

Population metadata identify 253 primary tumors, 14 secondary tumors, and 3 relapses; 263 nonmetastatic and 7 metastatic samples; and 3 palliative-treatment samples. The external-cohort adapter must prespecify whether eligibility is restricted to primary, nonmetastatic, nonpalliative subjects.

### GSE41613

The series matrix contains 97 samples, 97 matrix columns, and 54,613 feature/probe rows, with no duplicate GEO accessions. Follow-up/status fields are available for all 97 samples. Status includes 46 alive, 30 dead from oral cancer, 14 dead from non-oral-cancer causes, and 7 dead from an unknown cause.

The `fu time` unit is not encoded in the series matrix and must be verified from the source publication before endpoint construction. This HPV-negative OSCC cohort remains a sensitivity cohort and must not be presented as general HNSCC external validation.

## 8. Cross-cohort identity audit

Native source identifiers were compared exactly, without prefix removal, fuzzy matching, or cross-cohort normalization. Every off-diagonal overlap count among RADCURE, HANCOCK, TCGA-HNSC, GSE65858, and GSE41613 is zero.

This result supports absence of obvious exact-ID leakage but does not prove that the cohorts share no real-world participants under unrelated identifiers.

## 9. License and citation status

Artifact-level license and citation notes are stored next to each manifest:

- RADCURE clinical data and the downloaded Zenodo RDS are documented as CC BY 4.0 with their required DOI/accession citations.
- HANCOCK code is Apache 2.0; the TCIA mirror lists the collection under CC BY 4.0. The acquired FAU ZIPs do not embed a standalone license, so redistribution terms must be rechecked before sharing copies.
- TCGA-HNSC acquisition is restricted to open GDC files; re-identification is prohibited and repository/project acknowledgment is required.
- GEO processed data are public, but source accession and publication citation remain required, and submitter-retained rights may still apply.

These notes record provenance and are not legal advice.

## 10. Outstanding limitations

1. The ORCESTRA RDS passed byte-size, publisher-MD5, and SHA-256 verification, but its internal feature names, patient coverage, negative-control organization, and scanner/manufacturer metadata have not been authoritatively inspected because the current environment lacks R or a validated RDS parser.
2. RADCURE follow-up origin does not yet match the intended treatment-start index.
3. RADCURE histology eligibility needs a frozen clinical definition.
4. GSE65858 population restrictions need prespecification.
5. GSE41613 follow-up units need publication-level verification.
6. Prediction-time variable availability and final endpoint adapters must be frozen before baseline modeling.

## 11. Phase 1 recommendation and gate

**Recommendation: Conditional GO for Phase 2 adapter construction and descriptive analysis only.**

The recommendation is conditional on explicit user approval and the following governance requirements:

- keep the RADCURE challenge test sealed and do not use its outcomes for any tuning;
- keep GSE65858 and GSE41613 external/sensitivity outcomes unavailable to preprocessing, feature selection, hyperparameter selection, calibration, or reliability-gate thresholds;
- resolve the RADCURE time-origin issue before endpoint finalization;
- install a project-local R runtime or validated parser before radiomics modeling;
- verify the GSE41613 follow-up unit and prespecify GSE65858 eligibility;
- stop again for review after Phase 2 descriptive/adaptor outputs and before baseline modeling.

Phase 2 has **not** been started or authorized by this report.