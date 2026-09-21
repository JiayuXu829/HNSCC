# U8E / T1R GEO post-hoc external characterization

## Status

`U8E_T1R_EXTERNAL_CHARACTERIZATION_SUPPLEMENT_INTEGRATED_POST_HOC`

U8E fitted the frozen T1R construction once on the full TCGA-HNSC development cohort and applied it without refitting or tuning to GSE65858 and GSE41613. Aggregate Brier and discrimination deltas were favorable in both cohorts, but GEO outcomes were previously consumed during Phase 6 and GSE41613 had a constant applied V0 reference. This stage is therefore descriptive post-hoc characterization only—not formal external validation or confirmation.

## Frozen and tracked outputs

- `frozen_u8e_t1r_external_characterization_protocol.yaml`
- `aggregate_t1r_external_characterization_audit.json`
- `research_studies/01_pattern_surv_hn/reports/2026-09-20_step_U8E_T1R_external_characterization_completed.md`
- `research_studies/01_pattern_surv_hn/reports/2026-09-20_step_U8E_paper_supplement_integration_completed.md`

## Untracked patient outputs

Patient-level predictions remain under the Git-ignored directory:

`results/predictions/pattern_surv_hn/U8_T1R_external/`

No patient-level file is copied into this directory or the paper. The aggregate narrative is integrated in `paper/supplement.md` as Supplementary Methods and Table S11.

## Claim boundary

No formal external-validation, confirmatory, clinical-utility, or deployment-readiness claim is permitted. U8E does not replace the existing V1R/HANCOCK confirmation narrative.

