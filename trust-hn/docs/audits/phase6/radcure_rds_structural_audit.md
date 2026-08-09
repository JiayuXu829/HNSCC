# Phase 6 RADCURE RDS structural audit

Date: 2026-08-08

## Decision

**Conditionally unblocked for Phase 6 before outcome unsealing.** The processed ORCESTRA RDS can be parsed with `rdata==1.1.0`, and the original, shuffled-full, and randomized-sampled-full PyRadiomics assays have identical patient and feature order. FMCIB features remain excluded.

## Aggregate findings

- RDS patients: 2,994
- MultiAssayExperiment experiments: 14
- Selected numerical PyRadiomics features: 1,317
- Feature matrix: 2,994 ? 1,317
- Non-finite selected values: 0
- Phase 2 eligible roles: train 1,215, calibration 303, sealed test 626
- Eligible patients without RDS radiomics: train 61, calibration 21, sealed test 32
- Frozen sealed-test set digest matches the Phase 5 manifest: `8a954d9bb913145994df80c91a2f76c309e81d3ec32652869945744310439000`

## Frozen handling of missing radiomics

The 114 eligible patients without processed radiomics are **not excluded**. They remain in their frozen partitions. Radiomics are represented as fully missing, and the frozen B7 precedence routes them to the clinical B2 fallback unless clinical unreliability requires abstention. This avoids changing the locked cohort after seeing availability.

## Feature policy

Numerical vectors are selected by field name and type only. Patient/study identifiers, UIDs, ROI metadata, diagnostics fields, and all FMCIB/deep-learning experiments are excluded. No outcome was loaded or used in this audit. Patient-level matrices are stored only under `data/processed/`, which is Git-ignored.
