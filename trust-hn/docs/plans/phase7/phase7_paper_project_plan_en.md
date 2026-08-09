# TRUST-HN Phase 7 Paper Project Plan

**Date:** 2026-08-09  
**Scope:** Evidence mapping, argument and outline development, additional exploratory benchmarks, multimodal visualization, manuscript writing, supplementary reporting, and Springer Nature LaTeX production.  
**Governance premise:** Phase 6 outcomes have been observed. Any newly added method is post hoc exploratory, must not be described as prespecified locked validation, and must not modify registered Phase 6 files or overwrite Phase 6 outputs.

## Dataset inventory

The project contains **five named public cohorts in three data ecosystems**: RADCURE (3,346 source/2,144 included; clinical plus CT-derived radiomics), HANCOCK (763; clinical, blood and TMA-derived structured pathology), TCGA-HNSC (520 included, 519 with usable OS; clinical plus RNA-seq), GSE65858 (270 source/244 included; clinical plus microarray transcriptomics), and GSE41613 (97; HPV-negative OSCC transcriptomic sensitivity cohort). These comprise 4,996 source records, 3,768 included records, 2,649 development/calibration records, and 1,119 locked/OOD/external/sensitivity records.

No public cohort may be relabelled as private, institutional, or proprietary. Readable display labels may be used only when the public source remains explicit, for example `Imaging cohort (RADCURE)`. Canonical code keys and provenance must remain unchanged. A true institutional cohort can be added only if genuine local data, authorization, ethics information, eligibility rules and endpoint definitions exist.

## Scientific narrative

The manuscript should not claim universal superiority. Its central argument is that multimodal prognostic gain and reliability gating are cohort dependent. Clinical anchoring and residual fusion transferred reasonably in RADCURE and HANCOCK, whereas transcriptomic fusion showed external calibration failure in GSE65858. Reliability gating changed coverage and enabled fallback/abstention but did not consistently outperform forced fusion. Radiomic negative controls did not establish modality-specific biological signal. The contribution is a transparent framework for clinical anchoring, incremental fusion, reliability assessment and safe degradation, together with an explicit account of where it succeeds and fails.

## Work packages

1. **WP0 Evidence freeze and claim boundaries:** build a result-to-source evidence map, classify prespecified/development/locked/post-hoc analyses, and register Phase 7 exploratory work separately.
2. **WP1 Outline and argument map:** create paragraph-level Abstract, Introduction, Methods, Results, Discussion and Conclusion plans before prose drafting.
3. **WP2 Cohort/modality/method normalization:** finalize cohort roles, modality matrix, endpoints, sample flow and manuscript display labels without changing provenance.
4. **WP3 Exploratory comparators:** retain B0–B7, M0 and N0; add Gradient Boosting Survival Analysis, XGBoost-Cox, late-fusion stacking and a missing-aware direct-fusion baseline. Extra Survival Trees is optional. DeepSurv is optional only if dependencies, compute and reproducibility justify it. Use new Phase 7 config/code/output paths, development-only tuning and explicit post-hoc labels for all new external comparisons.
5. **WP4 Multimodal figures:** create architecture, cohort-flow/modality matrix, development performance, paired external forest plots, risk–coverage/action plots, modality-shift embeddings, and stress/negative-control/calibration/DCA figures. Clinical, radiomic, blood/TMA and transcriptomic modalities each receive at least one interpretable aggregate visualization.
6. **WP5 Tables/statistical package:** prepare four main tables and complete supplementary tables for all models, seeds, calibration, coverage profiles, stress tests, negative controls, subgroups, DCA thresholds, hyperparameters and compute.
7. **WP6 Methods and Results first:** write governance, cohorts, endpoints, preprocessing, models, gate and statistics, followed by cohort flow, locked/OOD/external results, negative controls and utility limitations. Always report B7 coverage and prioritize identical-retained-subset comparisons.
8. **WP7 Introduction, Discussion, Conclusion and Abstract:** write literature-backed framing after the evidence sections; discuss mixed and negative results explicitly; avoid prospective, deployment, universal robustness or clinical-utility claims.
9. **WP8 Supplement/model card/reporting:** finalize Supplementary Information, data dictionary, reproducibility map, model card, TRIPOD+AI, PROBAST+AI, data/code/ethics/declaration text and a prospective validation protocol.
10. **WP9 LaTeX and submission QC:** convert to the Springer Nature template, build BibTeX, compile, verify cross-references and numerical consistency, inspect claim boundaries, and reproduce figures in a clean environment.

## Main display plan

- Figure 1: TRUST-HN clinical problem and architecture.
- Figure 2: Five-cohort flow and modality matrix.
- Figure 3: Development model and calibration comparison.
- Figure 4: Paired locked/OOD/external effect forest plot.
- Figure 5: Reliability, action distribution and risk–coverage.
- Figure 6: Clinical/radiomic/blood-TMA/transcriptomic shift visualization.
- Figure 7: Stress tests, radiomic negative controls, calibration and selected DCA.
- Table 1: Cohort characteristics and flow.
- Table 2: Main model metrics.
- Table 3: Paired differences with confidence intervals.
- Table 4: Coverage, actions, stress tests and key negative findings.

Execution must proceed through review checkpoints: WP0–WP2 and outline approval; exploratory benchmark approval; figure/table review; Methods/Results review; Introduction/Discussion review; supplement/model-card review; final LaTeX and submission QC. Phase 6 outcomes must never be used to retune the primary models or gate thresholds.
