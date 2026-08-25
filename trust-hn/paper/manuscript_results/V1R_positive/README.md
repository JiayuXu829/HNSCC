# V1R positive results for manuscript use

This directory is a publication-facing extract of the **positive V1R development results only**. It contains aggregate, non-patient-identifying values used by the manuscript narrative and the proposed framework figure. Patient-level predictions, the full audit, the original V1 failure record, and uncompleted follow-up experiments are intentionally not copied here.

## Scope

- Cohort: HANCOCK official training ecosystem, 610 eligible patients and 173 deaths.
- Design: repeated nested cross-fitting, five repetition seeds (17, 29, 43, 71, 101), five outer folds and three inner folds.
- Comparator: V0 clinical-pathological anchor.
- Candidate: V1R shrinkage-controlled residual Deep Sets Cox, with 3,225 parameters.
- Primary horizon: 24-month overall-survival risk (730.5 days).
- Coverage: 100% for both V0 and V1R.
- Exact empty-set clinical fallback: verified with zero residual and fused-score error.

## Provenance

The values are transcribed from:

`research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_residual_shrinkage_rescue/aggregate_u2_v1r_rescue_audit.json`

The formal patient-level OOF output remains Git-ignored. Reproducibility receipt: `E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0`.

The analysis is internal development evidence and should not be described as confirmatory superiority, external validation, clinical utility, or deployment readiness.

## Manuscript source-of-truth rule

For subsequent manuscript revisions, use this directory as the controlled publication-facing source of truth for the V1R core narrative. The section-by-section interpretation and claim boundary are recorded in `v1r_paper_narrative_and_section_map.md`. The aggregate metrics are recorded in `v1r_positive_results.csv` and `v1r_positive_results.json`; manuscript-ready claims are in `v1r_manuscript_claims.md`; and the main-figure specification is in `figure1_v1r_framework.md`.

The intended story is: **V0 full-coverage clinical anchor -> shrinkage-controlled V1R residual -> improved discrimination and modestly improved probabilistic accuracy -> exact fallback and bounded pattern-level regret**. Planned calibration, routing, external validation and confirmation must remain labelled as future work until separately approved result extracts are added.