# PATTERN-Surv-HN Supplementary Information: V1R development, U5R7 calibration bridge, U5R8 secondary validation, U6R1 router exploration, RADCURE external characterization, U8 transcriptome method replication and U8E GEO characterization

> Updated 20 September 2026. This supplement documents the aggregate results carried into the manuscript from the V1R development, U5R7 development-only bridge, U5R8 locked secondary validation, locked raw-V1R confirmation, U6R1 patient-level router exploration, U7R2 RADCURE external characterization, U8 T1R transcriptome method-replication and U8E GEO characterization stages. Patient-level predictions remain Git-ignored. U5R7 is exploratory development evidence; U5R8 did not pass its bridge safety gates and is not presented as confirmed external calibration or definitive superiority. U6R1 and U7R2 are exploratory and are not presented as external validation. U8 is an internal post-hoc exploratory analysis; U8E is a separately executed post-hoc GEO characterization that provides directionally consistent descriptive evidence while complementing, rather than replacing, the locked confirmation narrative.

## Supplementary Methods S1: V1R cross-fitting

The HANCOCK official-training ecosystem contributed 610 eligible postoperative patients and 173 deaths. Repeated nested cross-fitting used five outer folds, repetition seeds 17, 29, 43, 71 and 101, and three inner folds. V1R retained the clinical-pathological anchor and used a 3,225-parameter residual Deep Sets Cox backbone with residual scale selected inside each inner loop.

For patient \(i\),

\[
\eta_{\mathrm{V1R},i}=\eta_{\mathrm{V0},i}+\lambda_f\Delta\eta_{\mathrm{res},i}.
\]

The inner-loop grids were residual penalties {0.01, 0.1, 1.0}, optimisation checkpoints {0, 10, 25, 50} and residual scales {0.1, 0.2, 0.3, 0.4, 0.5, 1.0}. Preprocessing, model selection and baseline-hazard estimation were confined to the corresponding training fold. Empty optional-modality sets used exact clinical-anchor fallback.

## Supplementary Table S1: Development aggregate result

| Metric | Anchor | V1R | V1R minus anchor | Interpretation |
|---|---:|---:|---:|---|
| IPCW Brier at 24 months | 0.124745 | 0.124338 | -0.000407 | lower probabilistic error |
| Uno C at 24 months | 0.644239 | 0.665542 | +0.021303 | improved discrimination |
| Time-dependent AUC at 24 months | 0.662022 | 0.682511 | +0.020488 | improved time-specific discrimination |
| Harrell C | 0.623021 | 0.633710 | +0.010690 | improved overall ranking |
| Coverage | 100% | 100% | 0 | full coverage preserved |
| Empty-set fallback error | 0 | 0 | 0 | exact clinical fallback |
| Worst supported-pattern Brier regret | reference | +0.009848 | +0.009848 | below +0.020 boundary |
| Uno-C improving seeds | -- | 5/5 | -- | favourable direction across seeds |

## Supplementary Methods S2: Development calibration bridge

U5R7 was frozen as `beta_0.900_logloss` after the U5R5 fixed-slope and U5R6 intercept-objective explorations. It was evaluated only by repeated, cross-fitted development diagnostics. For raw V1R 24-month risk \(p_{\mathrm{V1R}}\),

\[
x_{\mathrm{raw}}=\operatorname{logit}(p_{\mathrm{V1R}}),
\]

\[
x_{\mathrm{bridge}}=\alpha_{\mathrm{logloss},f}+0.90x_{\mathrm{raw}},
\qquad p_{\mathrm{bridge}}=\sigma(x_{\mathrm{bridge}}).
\]

The intercept \(\alpha_{\mathrm{logloss},f}\) was fitted by weighted log-loss using only non-held-out development folds. The bridge was global-only, pattern-agnostic, strictly monotone and rank-preserving. It did not retrain V1R, alter the V0 fallback, change coverage, or train a router. Confirmation outcomes were not used for fitting, tuning or evaluation.

The bridge-evaluable diagnostic contained 2,460 repeated OOF rows and 415 evaluable events. These values are an absolute-risk calibration diagnostic and are not numerically interchangeable with the primary V0-versus-V1R performance table.

## Supplementary Table S2: U5R7 development bridge result

| Metric | Raw V1R | U5R7 bridge | Change | Interpretation |
|---|---:|---:|---:|---|
| IPCW Brier at 24 months | 0.126637 | 0.126784 | +0.000147 | within +0.0005 global gate |
| CITL | +0.011680 | -0.003796 | -0.015477 | absolute error improved by 0.007884 |
| Calibration slope | 0.825887 | 0.881552 | +0.055665 | absolute error improved by 0.055665 |
| Worst supported-pattern Brier regret | reference | +0.004176 | +0.004176 | below +0.005 gate |
| Coverage | 100% | 100% | 0 | preserved |
| Ranking | reference | preserved | -- | all held-out folds |

The bridge moved CITL closer to zero and calibration slope closer to one. Its small positive Brier delta is reported rather than hidden; the candidate passed the development exploratory gates because the global delta was +0.000147 (threshold +0.0005) and worst supported-pattern regret was +0.004176 (threshold +0.005).

## Supplementary Table S3: Locked confirmation aggregate result

| Metric at 24 months | Anchor | Raw V1R | Raw V1R minus anchor | Interpretation |
|---|---:|---:|---:|---|
| Uno C | 0.782579 | 0.804242 | +0.021664 | favourable point estimate |
| IPCW Brier | 0.136412 | 0.131246 | -0.005166 | favourable point estimate |
| Time-dependent AUC | 0.801094 | 0.813637 | +0.012543 | favourable point estimate |
| Harrell C | 0.733253 | 0.752842 | +0.019589 | favourable point estimate |
| Calibration-in-the-large | 0.211270 | 0.116482 | -0.094788 | closer to 0 |
| Calibration slope | 1.945126 | 1.501223 | -0.443903 | closer to 1 |
| Coverage | 100% | 100% | 0 | preserved |

The confirmation cohort contained 152 patients and 40 events. Patient-level stratified bootstrap used 2,000 replicates with seed 20260825. The 95% interval for delta Uno C was -0.025965 to +0.070816 and for delta IPCW Brier was -0.012843 to +0.002171; both crossed zero. The primary confirmation table is raw V1R only. In the subsequent U5R8 locked secondary post-unseal validation, the frozen U5R7 bridge changed IPCW Brier24 from 0.134697 to 0.135782 (delta +0.001085), CITL from +0.156751 to +0.160944, and calibration slope from 1.510335 to 1.678150, while preserving coverage and ranking. The global Brier, CITL and slope gates therefore failed; this readout is not a confirmed bridge result.

## Supplementary Methods S4: Estimands and safety

The paired estimands were

\[
\Delta\mathrm{Brier}_{24}=\mathrm{Brier}_{24}(\mathrm{V1R})-\mathrm{Brier}_{24}(\mathrm{V0}),
\]

and

\[
\Delta\mathrm{UnoC}_{24}=\mathrm{UnoC}_{24}(\mathrm{V1R})-\mathrm{UnoC}_{24}(\mathrm{V0}).
\]

For the bridge, the safety estimand was the largest excess Brier score among supported acquisition patterns, defined by at least 30 patients and 10 events:

\[
\mathcal{R}_{\mathrm{worst}}=\max_{p\in\mathcal{P}_{\mathrm{supported}}}
\{\mathrm{Brier}_{24}(\mathrm{bridge},p)-\mathrm{Brier}_{24}(\mathrm{V1R},p)\}.
\]

Lower Brier and positive discrimination differences favour V1R. Calibration-in-the-large is better when closer to 0 and calibration slope is better when closer to 1. A positive global bridge slope preserves ranking, but ranking preservation alone does not establish calibration validity.

## Supplementary Methods S5: Locked confirmation integrity

The confirmation protocol, input manifest, dependency lock and prediction artifact were frozen before confirmation outcomes were unsealed. Twenty-five matched members were generated using five repetition seeds and five outer folds, with development-fold fitting only. No confirmation-cohort tuning, calibration bridge, post-unseal refit, router, or selective patient removal was performed. Aggregate metrics were evaluated after prediction sealing. The locked prediction artifact SHA256 was `E5DA83BDB3BB97C3488687C78CCF166FBD03059619DD0690E2767CAF8F393FCF`.

## Supplementary Methods S6: Reproducibility and claim boundary

The formal V1R development patient-level OOF SHA256 was `E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0`. The confirmation protocol SHA256 was `1E134D30557D1CC153997F6EBB79E99C2E160F85A9F94BF3BBDD81C2C588BDED`. The U5R7 aggregate source is `research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_aggregate_results.json`. Official-test and external outcomes were not used for U5R7 tuning. The result-informed development status is disclosed in the manuscript; it does not authorize claims of definitive superiority, external calibration, transportability, clinical utility or deployment readiness.

## Supplementary Methods S7: Framework figure specification

The main framework figure should contain: (a) clinical anchor; (b) usable blood, ICD and TMA set tokens; (c) permutation-invariant residual encoder; (d) inner-CV-selected shrinkage; (e) raw V1R fused score; (f) exact clinical fallback for an empty set; (g) completed U5R7 global monotone logit bridge labelled development-only; (h) locked raw-V1R confirmation readout; and (i) a bridge-to-confirmation path labelled secondary post-unseal validation with failed calibration gates, while keeping raw V1R as the primary confirmation readout. Router exploration is documented in S8; clinical-utility analysis remains future work.

## Supplementary Methods S8: U6R1 patient-level router exploration

A value router was explored as a development-only mechanism that selects raw V1R (`FUSE`) or the V0 clinical anchor (`FALLBACK`) per patient. Repeated V0 and V1R OOF predictions were first averaged to one row per patient, then a five-fold patient-level cross-fitted logistic router (fixed `C=0.5`) was trained. A reliability-augmented feature set added the across-repetition SD of V0 risk, V1R risk and risk delta. Thresholds 0.40, 0.50 and 0.60 were fixed before readout and all reported. No official-test, confirmation or external outcomes were read.

Patient-aggregated references: V0 IPCW Brier24 0.123927; raw V1R 0.122765 (delta -0.001162).

| Policy | FUSE rate | IPCW Brier24 | 螖 vs V0 | 螖 vs raw V1R | Rank concordance vs raw V1R |
|---|---:|---:|---:|---:|---:|
| V0 | 0.0% | 0.123927 | 0 | +0.001162 | 0.867 |
| raw V1R | 100.0% | 0.122765 | -0.001162 | 0 | 1.000 |
| core router, q鈮?.40 | 66.1% | 0.123545 | -0.000382 | +0.000780 | 0.945 |
| core router, q鈮?.50 | 54.1% | 0.123511 | -0.000416 | +0.000746 | 0.939 |
| core router, q鈮?.60 | 40.3% | 0.123585 | -0.000341 | +0.000821 | 0.928 |
| reliability router, q鈮?.40 | 67.0% | 0.123648 | -0.000279 | +0.000883 | 0.946 |
| reliability router, q鈮?.50 | 54.8% | 0.123508 | -0.000419 | +0.000743 | 0.938 |
| reliability router, q鈮?.60 | 42.6% | 0.123421 | -0.000506 | +0.000657 | 0.929 |

The best point estimate (reliability router, threshold 0.60) gave 螖 Brier versus V0 of -0.000506; in a 2,000-replicate patient bootstrap the 95% interval was approximately -0.00162 to +0.00076, crossing zero. The router remained worse than raw V1R at the point estimate and did not preserve the exact global V1R ranking. Coverage was 100% for all policies because FALLBACK always returned a V0 prediction.

Interpretation: patient-level aggregation and reliability features slightly improved the exploratory point estimate against V0, but the router remained uncertain and below direct raw V1R. Selective routing is therefore retained as a hypothesis-generating extension, not a validated backbone, ranking-preserving policy, or deployment mechanism.

## Supplementary Methods S9: U7R2 RADCURE external characterization

U7 froze the intake criteria and analysis order for a future formal current-V1R external confirmation before any qualifying cohort was selected. The local inventory contains no cohort that is simultaneously current-V1R-compatible and certified outcome-untouched, so no new external confirmation could be executed. RADCURE was selected as the best available cohort for an honest external characterization of an adapted clinical/radiomics comparator set, explicitly separated from the current-V1R claim.

RADCURE held-out test split: 626 patients, 110 events, 100% coverage.

| Comparator | IPCW Brier | Uno C | 24-month AUC | Harrell C | CITL | Calibration slope |
|---|---:|---:|---:|---:|---:|---:|
| C1 | 0.095801 | 0.806595 | 0.819376 | 0.795924 | -0.097110 | 1.950857 |
| C2 | 0.090683 | 0.806744 | 0.818182 | 0.797862 | -0.044444 | 1.139466 |
| C3 | 0.098469 | 0.771260 | 0.780742 | 0.761632 | -0.099603 | 1.268349 |
| C4 | 0.097403 | 0.779243 | 0.787882 | 0.768812 | -0.074520 | 1.471544 |

RADCURE does not reproduce the frozen current-V1R blood/ICD/TMA input contract, its outcome was previously consumed, and the held-out test split is not a newly acquired outcome-untouched cohort. The comparator set is adapted clinical/radiomics, not the current V1R residual-shrinkage ensemble. These results are therefore descriptive transportability characterization only; they do not constitute formal external validation of current V1R, its fixed bridge, or a router, and no RADCURE outcome was used to tune any model, bridge, router, threshold, or safety gate.

## Supplementary Methods S10: U8 T1R transcriptome residual-shrinkage method replication

U8 was a post-hoc exploratory analysis asking whether the residual-shrinkage design used by V1R can be transferred from the HANCOCK blood/ICD/TMA input contract to a single dense transcriptome modality. It was run only in the TCGA-HNSC development cohort after TCGA outcomes had already been consumed. The purpose was internal method replication, not a new backbone decision and not an external test.

The analysis contained 519 patients and 221 events at a 730.5-day (approximately 24-month) horizon. The clinical anchor (`V0`) was a fold-fitted elastic-net Cox model using seven variables: age, sex, site, stage, HPV status, treatment and smoking. The transcriptome contained 14,417 common genes represented as within-sample gene ranks; in each training fold, variance selection retained the top 500 genes. The residual head was `Linear(500 -> 32) -> Tanh -> Linear(32 -> 1)`, and the fused score was

\[
\eta_{\mathrm{T1R},i}=\eta_{\mathrm{V0},i}+\lambda_f\Delta\eta_{\mathrm{transcriptome},i}.
\]

Repeated nested cross-fitting used five outer folds, three inner folds and repetition seeds 17, 29, 43, 71 and 101. Clinical preprocessing, gene selection, residual fitting, anchor selection, residual-penalty selection, optimization-checkpoint selection, shrinkage-scale selection and Breslow baseline-hazard estimation were confined to the corresponding training fold. The residual penalty, checkpoint and shrinkage scale were selected only by inner CV. The architecture was frozen before execution. The transcriptome residual head contained 16,065 trainable parameters (below the frozen 50,000 ceiling); the complete run produced 2,595 OOF rows with complete coverage and an exact fallback error of 0.0.

### Supplementary Table S10.1: U8 development aggregate result

| Metric | V0 anchor | T1R | T1R minus V0 | Favorable seeds |
|---|---:|---:|---:|---:|
| IPCW Brier at 24 months | 0.221795 | 0.218058 | -0.003737 | 4/5 |
| Harrell C | 0.577281 | 0.605919 | +0.028637 | 5/5 |
| Uno C at 24 months | 0.565199 | 0.597265 | +0.032066 | 5/5 |
| Time-dependent AUC at 24 months | 0.557362 | 0.600236 | +0.042874 | 5/5 |

### Supplementary Table S10.2: U8 per-seed paired changes

| Repetition seed | Delta IPCW Brier at 24 months | Delta Uno C at 24 months |
|---:|---:|---:|
| 17 | -0.004443 | +0.037975 |
| 29 | +0.002714 | +0.006398 |
| 43 | -0.004353 | +0.029370 |
| 71 | -0.006560 | +0.048165 |
| 101 | -0.006045 | +0.038420 |

The frozen exploratory gate required preserved coverage, structural safety, Brier safety, calibration safety and at least one incremental-value path. The observed worst supported-pattern Brier regret was +0.002714 (ceiling +0.020); mean absolute CITL deterioration was +0.049232 (ceiling +0.100); and mean absolute calibration-slope-error deterioration was -0.084226 (ceiling +0.150). Both probability-error and discrimination paths met their seed-stability requirements. The frozen gate therefore returned `T1R_EARNS_COMPLEXITY`, but that decision authorizes only the stated internal exploratory interpretation.

T1R showed a directionally favourable internal exploratory signal, with improved discrimination in all five repetition seeds and a small mean Brier improvement in four of five seeds. Because TCGA outcomes had already been consumed, this analysis does not establish pristine confirmation, confirmatory superiority, external validity, transportability, clinical utility or deployment readiness. It also does not replace the main V1R backbone, the locked raw-V1R confirmation readout, the U5R7 development-only bridge or the failed U5R8 secondary bridge readout. The acquisition-pattern gate collapses to the single transcriptome-present pattern. The GEO application was not part of the U8 development-CV authorization; its subsequent execution as the separately authorized U8E stage is reported in Supplementary Methods S11.

Aggregate provenance is `research_studies/01_pattern_surv_hn/core_backbone/U8_T1R_transcriptome_residual_shrinkage/aggregate_t1r_transcriptome_development_cv_audit.json`. Patient-level U8 OOF predictions remain Git-ignored and are not reproduced in this supplement.
## Supplementary Methods S11: U8E T1R GEO post-hoc cross-cohort characterization

U8 established that residual-shrinkage learning can be adapted to a dense transcriptome modality within the TCGA-HNSC development cohort. U8E extended that observation by asking whether the transcriptomic residual signal retained a favorable direction when the model encountered tumor transcriptomes from independently assembled GEO cohorts.

A single T1R model was fitted on the complete TCGA-HNSC development cohort (`n=519`; 221 events). All selections were completed before application: development-only inner cross-validation selected an elastic-net anchor with alpha 0.05 and L1 ratio 0.1, residual penalty 1.0, optimization checkpoint 10 and residual scale 1.0. The resulting model contained 16,065 trainable parameters and used the frozen `Linear(500 -> 32) -> Tanh -> Linear(32 -> 1)` transcriptome residual head. It was then applied without external refitting, external tuning, threshold selection or outcome-dependent selection to GSE65858 (`n=244`; 78 events) and GSE41613 (`n=97`; 51 events). Coverage was complete in both cohorts.

### Supplementary Table S11.1: U8E aggregate GEO characterization

| Cohort and metric | V0 clinical anchor | T1R | T1R minus V0 |
|---|---:|---:|---:|
| **GSE65858 (n=244; 78 events)** | | | |
| IPCW Brier at 24 months | 0.195207 | 0.195070 | -0.000137 |
| Harrell C | 0.581806 | 0.644868 | +0.063062 |
| Uno C at 24 months | 0.583694 | 0.645818 | +0.062123 |
| Time-dependent AUC at 24 months | 0.588972 | 0.650733 | +0.061762 |
| Calibration in the large at 24 months | -0.763793 | -0.831959 | -0.068166 |
| Calibration slope at 24 months | 1.707442 | 1.941562 | +0.234120 |
| **GSE41613 (n=97; 51 events)** | | | |
| IPCW Brier at 24 months | 0.265712 | 0.258607 | -0.007104 |
| Harrell C | 0.500000 | 0.626361 | +0.126361 |
| Uno C at 24 months | 0.500000 | 0.616039 | +0.116039 |
| Time-dependent AUC at 24 months | 0.500000 | 0.634011 | +0.134011 |
| Calibration in the large at 24 months | -0.273717 | -0.264792 | +0.008925 |
| Calibration slope at 24 months | — | 1.939018 | — |

In GSE65858, T1R improved both the 24-month probability score and every discrimination measure relative to the clinical anchor. The pattern was also apparent in GSE41613, where the applied clinical anchor contained no cross-patient variation and T1R restored patient-level risk ordering, yielding a Harrell C of 0.626 and a 24-month AUC of 0.634. Calibration slopes above one in the T1R analyses indicate that predicted-risk dispersion remained compressed relative to observed outcomes, pointing to cohort-level recalibration as a natural next step for future prospective evaluation.

Across two independently assembled transcriptomic cohorts, the direction of change was favorable for IPCW Brier score, Harrell C, Uno C and time-dependent AUC. This consistency strengthens the biological plausibility of the U8 finding: transcriptome residual learning can identify prognostic structure beyond a conventional clinical anchor and can retain a visible signal after transport across data sources and platforms.

Because GEO outcomes had contributed to earlier Phase 6 analyses, U8E is presented as post-hoc cross-cohort characterization rather than formal external validation. Its role is to enrich the internal U8 signal with concordant descriptive GEO evidence and to motivate evaluation in an outcome-untouched cohort with prospectively frozen predictions. Patient-level U8E predictions remain Git-ignored and are not reproduced here.

Aggregate provenance is `research_studies/01_pattern_surv_hn/core_backbone/U8E_T1R_external_characterization/aggregate_t1r_external_characterization_audit.json`.
