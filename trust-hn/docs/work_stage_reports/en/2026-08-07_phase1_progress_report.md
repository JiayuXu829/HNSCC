# Phase 1 progress report

**Date:** 2026-08-07  
**Status:** Acquisition pending; audit infrastructure ready.

## Implemented before acquisition

- HTTPS/domain/artifact-role/size allowlist in `configs/download_policy.json`.
- Atomic downloader with SHA-256 receipt and read-only source-file handling.
- Explicit rejection of raw CT, DICOM, RTSTRUCT, WSI, raw TMA images, and controlled-access genomics.
- GDC open-access TCGA-HNSC STAR-counts query and clinical metadata query specifications.
- GDC response normalizer that produces a file-level manifest without outcome columns.
- CSV/TSV/gzip reader with exact, non-fuzzy field resolution.
- Automatic data dictionary, split-wise missingness, patient overlap count, endpoint validity, event rate, and 24-month censoring audit.
- Study-specific candidate-field specifications that fail on ambiguity instead of guessing.

## Verification

`26` tests pass. Tests cover acquisition-policy refusal, path containment, gzip tables, field ambiguity, event mapping, patient split overlap, early censoring, endpoint summaries, GDC manifest normalization, hashing, and sealed-test governance.

## Scientific limitations of automated audit

Automation cannot decide histology eligibility, prediction-time availability, index-date meaning, treatment intent, or artifact license compatibility. These remain explicitly marked for manual source-field review after acquisition.

## Sealed/external outcomes

Not touched. The current GDC file-manifest normalizer intentionally excludes survival outcomes. GEO and locked RADCURE outcome files have not been downloaded.