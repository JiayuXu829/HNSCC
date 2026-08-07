# Phase 1 progress report

**Date:** 2026-08-07  
**Status:** Phase 1 acquisition and feasibility audit complete with documented conditions; awaiting user go/no-go review before Phase 2.

## Completed scope

- Acquired only authorized public clinical tables, structured data, processed/pre-extracted features, open-access expression, metadata, and platform annotations.
- Downloaded 1,068 raw-area files including 534 acquired source files, 533 receipts, and one `.gitkeep` placeholder, totaling 3,128,490,508 bytes (2.914 GiB).
- Generated SHA-256 receipts and per-study manifests; all 535 source files are read-only while receipts remain mutable.
- Extracted and audited RADCURE, HANCOCK, TCGA-HNSC, GSE65858, and GSE41613 without constructing modeling matrices or tuning models.
- Stored native patient/sample ID inventories only under Git-ignored `data/interim` paths.
- Verified zero off-diagonal exact native-ID overlaps among the five cohorts.

## Cohort feasibility snapshot

- **RADCURE:** 3,346 unique patients; 1,800 challenge training, 750 challenge test, and 796 outside the challenge. All 3,346 have a feasibility OS pair; at 24 months there are 532 deaths, 2,436 observed event-free, and 378 censored early.
- **HANCOCK:** 763 patients. Every official split covers all 763 without duplicate or cross-split assignment. OS is usable for all 763; 213 deaths are recorded. Recurrence-free duration/event fields are complete for all 763.
- **TCGA-HNSC:** 520 Primary Tumor STAR-count files map to 520 cases and all overlap the clinical set; the clinical project has 528 cases. There are 527 usable OS duration/event pairs.
- **GSE65858:** 270 samples and 31,330 matrix feature rows; OS is usable for all 270.
- **GSE41613:** 97 samples and 54,613 matrix feature rows; follow-up/status is present for all 97, but the follow-up-time unit still requires publication-level verification.

## Expression integrity

All 520 TCGA STAR-count files use GENCODE v36, contain 60,664 gene rows, share one header and one gene identity/order signature, and have no malformed file. GSE65858 and GSE41613 matrix column counts match their sample metadata counts.

## Scientific conditions before modeling

1. RADCURE `Length FU` is documented from diagnosis to last contact, while the protocol expects a treatment-start index; this origin mismatch must be resolved.
2. The 842,779,545-byte ORCESTRA RDS passed publisher MD5, size, and SHA-256 checks, but internal structure cannot be authoritatively inspected until a project-local R runtime or validated parser is available.
3. GSE65858 eligibility must be prespecified, particularly primary versus secondary/relapse tumors, metastatic disease, and palliative treatment.
4. The GSE41613 follow-up unit must be verified, and this HPV-negative OSCC cohort must remain a sensitivity cohort.
5. Locked RADCURE challenge-test and external-cohort outcomes must remain unavailable to preprocessing, feature selection, tuning, calibration, and gate-threshold selection.

## Verification

`30` standard-library tests passed after finalization. Final checks parsed 555 JSON and 17 YAML/YML files, matched byte counts and SHA-256 values for all 534 manifest entries, confirmed all 534 acquired source files read-only, found no prohibited acquired-file candidate, and found no governed identifier leak across tracked reports/configs/manifests. Detailed evidence is stored in `data/interim/phase1_audit/phase1_audit.json` and per-study manifests under `data/manifests/`.

## Recommendation

**Conditional GO** for Phase 2 adapter construction and descriptive analysis only, after explicit user approval and under the conditions above. Phase 2 modeling is not yet authorized.