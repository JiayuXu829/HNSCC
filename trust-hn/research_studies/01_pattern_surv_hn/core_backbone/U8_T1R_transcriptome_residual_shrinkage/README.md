# U8 / T1R transcriptome residual-shrinkage

## Status

`U8_T1R_TRANSCRIPTOME_DEVELOPMENT_CV_COMPLETED_POST_HOC`

The frozen TCGA development cross-validation was executed on 2026-09-20. The frozen exploratory complexity gate passed with `T1R_EARNS_COMPLEXITY`. This is internal post-hoc method-replication evidence only, not confirmation or external validation.

## Frozen files

- `frozen_t1r_transcriptome_spec.yaml`
- `frozen_t1r_exploratory_gate.yaml`

## Tracked aggregate output

- `aggregate_t1r_transcriptome_development_cv_audit.json`

Patient-level OOF predictions remain under the git-ignored directory `results/predictions/pattern_surv_hn/U8_T1R/`.

## Method summary

T1R uses a fold-fitted seven-variable elastic-net Cox clinical anchor plus a two-layer Tanh transcriptome residual head over fold-bound variance-selected top-500 gene ranks. Outer folds select residual penalty, checkpoint, and shrinkage only through inner CV.

## Completed report

- `research_studies/01_pattern_surv_hn/reports/2026-09-20_step_U8_T1R_transcriptome_development_cv_completed.md`

The GEO application script was not part of the completed U8 development-CV authorization. It was subsequently executed as the separately authorized U8E post-hoc characterization stage; see `../U8E_T1R_external_characterization/`. That separate stage remains descriptive and non-confirmatory because the GEO outcomes were already consumed in prior work.
## Related external characterization

- `../U8E_T1R_external_characterization/`
- `../../reports/2026-09-20_step_U8E_T1R_external_characterization_completed.md`

