# 2026-09-20 — U8E paper supplement integration completed

## Objective

Integrate the completed U8E GEO characterization into `paper/supplement.md` as a distinct, narrative supplementary section while preserving the required post-hoc interpretation boundary.

## Changes made

- Updated the supplement title to include U8E GEO characterization.
- Updated the supplement overview to describe U8E as separately executed, directionally consistent post-hoc GEO evidence.
- Clarified in S10 that the GEO application was outside the U8 development-CV authorization and is now reported separately in S11.
- Added `Supplementary Methods S11: U8E T1R GEO post-hoc cross-cohort characterization`.
- Added Supplementary Table S11.1 with cohort-level aggregate results only.
- Framed the scientific narrative around cross-cohort retention of the transcriptome residual signal and the opportunity for future cohort-level recalibration and prospective confirmation.
- Preserved the explicit statement that GEO outcomes had contributed to earlier Phase 6 analyses, so U8E is presented as post-hoc characterization rather than formal external validation.
- Did not modify the main manuscript or reproduce any patient-level prediction.

## Editorial approach

The S11 narrative follows the manuscript logic: U8 established internal feasibility of transcriptome residual learning, and U8E asks whether that signal remains directionally visible after transport to independently assembled GEO cohorts. The section emphasizes favorable Brier and discrimination changes in both cohorts, while transparently contextualizing calibration dispersion and the constant clinical anchor in GSE41613. This framing supports biological plausibility without converting U8E into a confirmatory or formal external-validation claim.

## Checks

- Supplementary heading sequence includes S10 followed by S11.
- S11 reports aggregate cohort-level results only.
- No patient identifiers or patient-level prediction rows were added.
- Main manuscript unchanged.
- `paper/supplement.md` SHA-256 after integration:
  `82a35531a290d38a27b5386a44be42a077ea23ea2b3b01abcbe3f8ef242ed662`

## Artifacts

- Supplement: `trust-hn/paper/supplement.md`
- U8E aggregate source: `trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U8E_T1R_external_characterization/aggregate_t1r_external_characterization_audit.json`
- U8E completion report: `trust-hn/research_studies/01_pattern_surv_hn/reports/2026-09-20_step_U8E_T1R_external_characterization_completed.md`
