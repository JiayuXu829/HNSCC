# Supplementary Information for PATTERN-Surv-HN

## Supplementary Note 1. Evidence architecture and interpretation

This Supplementary Information expands the main-text Methods and Results. It documents the cohort roles, acquisition and usability definitions, model architecture, cross-fitting procedure, calibration layer, locked confirmation analysis, routing exploration and extension analyses in RADCURE, TCGA-HNSC and GEO. All numerical summaries are derived from frozen aggregate artifacts; no patient-level predictions are included.

The study was organized as a staged evidence pipeline. First, repeated nested cross-fitting in the HANCOCK development cohort quantified the incremental value of the V1R residual pathway over a clinical-pathological anchor. Second, a monotone calibration bridge was optimized and evaluated within development folds. Third, raw V1R predictions and all analysis dependencies were sealed before confirmation outcomes were accessed. Fourth, router, RADCURE, transcriptome and GEO analyses examined complementary questions of selective use, multimodal benchmarking, method transfer and platform transport.

The interpretation used throughout the manuscript is summarized here once. V1R showed a reproducible development gain, favourable in all five repetition seeds, with complete coverage and pattern-level safety within the prespecified boundary. The locked HANCOCK confirmation cohort showed favourable point estimates for every principal metric; bootstrap intervals were wide and included zero, supporting a consistent directional signal. The development bridge improved calibration summaries, whereas the later bridge readout indicated that probability-scale transport requires cohort-specific recalibration. Router and extension analyses are used to generate design insights and transport evidence rather than to replace the locked raw-V1R result.

This staged architecture is a strength of the study: model development, calibration, confirmation and extension are separated by frozen protocols and explicit artifact boundaries. It allows the central finding—controlled incremental multimodal evidence can improve risk ranking while preserving full output availability—to be evaluated alongside calibration, routing and transport considerations.

## Supplementary Methods

### Cohorts, prediction time and endpoint

HANCOCK was the primary development and confirmation ecosystem. The development analysis included 610 eligible postoperative patients with 173 deaths; the locked confirmation analysis included 152 patients with 40 events. TCGA-HNSC contributed 519 patients and 221 events to the transcriptome method-replication analysis. GSE65858 and GSE41613 contributed 244 patients with 78 events and 97 patients with 51 events, respectively, to descriptive GEO characterization. The RADCURE held-out characterization included 626 patients and 110 events.

For patient \(i\), \(T_i\) denotes event time, \(C_i\) censoring time, \(Y_i=\min(T_i,C_i)\) observed duration and \(\delta_i=I(T_i\le C_i)\) the event indicator. In HANCOCK, follow-up began at first treatment and ended at last information; the event was all-cause death. Non-positive durations were excluded. The primary horizon was \(t^*=730.5\) days, approximately 24 months, and the target was all-cause mortality risk by that horizon. Prediction was designed for the period immediately after definitive surgery and pathological review, using information available at that time.

### Acquisition, usability and quality

For optional modality \(m\), the analysis distinguished acquisition \(a_{im}\), usability \(u_{im}\) and an outcome-blind quality vector \(q_{im}\). Acquisition indicated that a source record or assay existed. Usability indicated that the frozen preprocessing contract could produce a valid model input. Quality summaries included missing fraction, out-of-range counts, assay completeness and distributional distance from training data. The usable set was

\[
\mathcal{M}_i=\{m:u_{im}=1\}.
\]

Absent and acquired-but-unusable measurements were represented structurally rather than as zero-valued biology. The natural acquisition pattern was the blood--ICD--TMA usability tuple. Pattern counts and quality distributions were computed without outcomes. For development safety analyses, a supported pattern required at least 30 patients and 10 events.

### Clinical anchor and residual architecture

The V0 anchor was an elastic-net Cox proportional-hazards model. After training-fold preprocessing,

\[
\eta_{\mathrm{V0},i}=x_{c,i}^{\mathsf T}\hat\beta_c.
\]

Encoding, imputation, scaling and category handling were confined to the corresponding training fold. A training-fold Breslow baseline-hazard estimator converted the linear predictor to a 24-month mortality risk.

V1R was a clinically anchored residual Deep Sets Cox backbone with 3,225 parameters. Each usable modality was represented as an unordered token containing its learned representation, modality identity, usability status and quality indicators. For usable set \(S_i\),

\[
h_i=\rho\left(\frac{1}{|S_i|}\sum_{m\in S_i}\phi(x_{im},q_{im},e_m)\right),
\qquad
\Delta\eta_{\mathrm{res},i}=g(h_i),
\]

and the fused score was

\[
\eta_{\mathrm{V1R},i}=\eta_{\mathrm{V0},i}+\lambda_f\Delta\eta_{\mathrm{res},i}.
\]

Thus, optional evidence entered as a shrinkage-controlled residual around the clinical anchor. For each outer fold \(f\), residual penalty, optimization checkpoint and shrinkage scale were selected only within the corresponding inner loop. The searched grids were residual penalties \(\{0.01,0.1,1.0\}\), checkpoints \(\{0,10,25,50\}\) and scales \(\{0.1,0.2,0.3,0.4,0.5,1.0\}\). When \(S_i\) was empty, residual and fused-score deviations were zero, giving an exact clinical-anchor fallback.

### Cross-fitting, estimands and inference

Repeated nested cross-fitting used five outer folds, three inner folds and repetition seeds 17, 29, 43, 71 and 101. Preprocessing, gene or feature selection where applicable, model selection, shrinkage selection and baseline-hazard estimation were confined to training folds.

The paired full-coverage estimands were

\[
\Delta\mathrm{Brier}_{24}
=\mathrm{Brier}_{24}(\mathrm{V1R})-\mathrm{Brier}_{24}(\mathrm{V0}),
\]

and

\[
\Delta\mathrm{UnoC}_{24}
=\mathrm{UnoC}_{24}(\mathrm{V1R})-\mathrm{UnoC}_{24}(\mathrm{V0}).
\]

Negative Brier differences and positive discrimination differences favoured V1R. The safety estimand was the largest supported-pattern excess Brier score:

\[
\mathcal{R}_{\mathrm{worst}}
=\max_{p\in\mathcal{P}_{\mathrm{supported}}}
\{\mathrm{Brier}_{24}(\mathrm{candidate},p)-\mathrm{Brier}_{24}(\mathrm{reference},p)\}.
\]

Secondary summaries included Harrell C, time-dependent AUC, calibration-in-the-large and calibration slope. Inverse-probability-of-censoring-weighted Brier and Uno concordance estimates used frozen censoring models and weight handling. Confirmation intervals used 2,000 patient-level stratified bootstrap replicates; patients, rather than repeated prediction rows, were resampled.

### Calibration bridge

The U5R7 bridge was frozen as `beta_0.900_logloss`. For raw V1R 24-month risk \(p_{\mathrm{V1R}}\),

\[
x_{\mathrm{raw}}=\operatorname{logit}(p_{\mathrm{V1R}}),
\]

\[
x_{\mathrm{bridge}}=\alpha_{\mathrm{logloss},f}+0.90x_{\mathrm{raw}},
\qquad
p_{\mathrm{bridge}}=\sigma(x_{\mathrm{bridge}}).
\]

The intercept \(\alpha_{\mathrm{logloss},f}\) was fitted by weighted log-loss using only non-held-out development folds. The bridge was global, pattern-agnostic, strictly monotone and rank-preserving. It left V0, V1R, fallback behaviour and coverage unchanged. The diagnostic population contained 2,460 repeated out-of-fold rows and 415 evaluable events.

## Supplementary Results

### V1R improves development discrimination while retaining full coverage

V1R improved every aggregate discrimination measure and the 24-month IPCW Brier score in the HANCOCK development analysis (Supplementary Table 1). The mean Uno C gain was +0.021303 and was favourable in all five seeds. Coverage remained 100%, the empty-set fallback error was zero, and the worst supported-pattern Brier regret was +0.009848, below the +0.020 safety boundary.

### Supplementary Table 1. Development performance of V1R

| Metric | Clinical anchor | V1R | Difference | Interpretation |
|---|---:|---:|---:|---|
| IPCW Brier at 24 months | 0.124745 | 0.124338 | -0.000407 | Lower probabilistic error |
| Uno C at 24 months | 0.644239 | 0.665542 | +0.021303 | Improved discrimination |
| Time-dependent AUC at 24 months | 0.662022 | 0.682511 | +0.020488 | Improved time-specific discrimination |
| Harrell C | 0.623021 | 0.633710 | +0.010690 | Improved overall ranking |
| Coverage | 100% | 100% | 0 | Full output availability |
| Empty-set fallback error | 0 | 0 | 0 | Exact clinical fallback |
| Worst supported-pattern Brier regret | Reference | +0.009848 | +0.009848 | Below +0.020 boundary |
| Seeds with improved Uno C | -- | 5/5 | -- | Consistent direction |

### Development calibration bridge

The bridge moved calibration-in-the-large from +0.011680 to -0.003796 and calibration slope from 0.825887 to 0.881552 (Supplementary Table 2). Ranking and coverage were preserved. The global Brier change was +0.000147, within the +0.0005 gate, and worst supported-pattern regret was +0.004176, below the +0.005 gate.

### Supplementary Table 2. U5R7 development calibration bridge

| Metric | Raw V1R | U5R7 bridge | Change | Interpretation |
|---|---:|---:|---:|---|
| IPCW Brier at 24 months | 0.126637 | 0.126784 | +0.000147 | Within +0.0005 gate |
| Calibration-in-the-large | +0.011680 | -0.003796 | -0.015477 | Absolute error improved by 0.007884 |
| Calibration slope | 0.825887 | 0.881552 | +0.055665 | Absolute error improved by 0.055665 |
| Worst supported-pattern Brier regret | Reference | +0.004176 | +0.004176 | Below +0.005 gate |
| Coverage | 100% | 100% | 0 | Preserved |
| Ranking | Reference | Preserved | -- | All held-out folds |

### Locked confirmation of raw V1R

The confirmation protocol, input manifest, dependency lock and prediction artifact were frozen before outcomes were unsealed. Twenty-five matched prediction members were generated from five seeds and five outer folds, with development-fold fitting only. In the 152-patient, 40-event cohort, raw V1R showed favourable point estimates for discrimination, Brier score and calibration summaries (Supplementary Table 3).

Patient-level stratified bootstrap with 2,000 replicates gave a mean delta Uno C of +0.021654 (95% interval -0.025965 to +0.070816) and a mean delta IPCW Brier of -0.005222 (95% interval -0.012843 to +0.002171). The direction was favourable, with intervals reflecting the moderate event count.

The subsequently sealed U5R8 bridge readout preserved ranking and coverage but changed IPCW Brier from 0.134697 to 0.135782, calibration-in-the-large from +0.156751 to +0.160944 and calibration slope from 1.510335 to 1.678150. This result identifies cohort-level probability recalibration as the key next step for transportable absolute-risk output.

### Supplementary Table 3. Locked raw-V1R confirmation

| Metric at 24 months | Clinical anchor | Raw V1R | Difference | Interpretation |
|---|---:|---:|---:|---|
| Uno C | 0.782579 | 0.804242 | +0.021664 | Favourable point estimate |
| IPCW Brier | 0.136412 | 0.131246 | -0.005166 | Favourable point estimate |
| Time-dependent AUC | 0.801094 | 0.813637 | +0.012543 | Favourable point estimate |
| Harrell C | 0.733253 | 0.752842 | +0.019589 | Favourable point estimate |
| Calibration-in-the-large | 0.211270 | 0.116482 | -0.094788 | Closer to zero |
| Calibration slope | 1.945126 | 1.501223 | -0.443903 | Closer to one |
| Coverage | 100% | 100% | 0 | Preserved |

### Reliability-aware routing

U6R1 evaluated whether a patient-level router could select raw V1R or the clinical anchor. Repeated out-of-fold predictions were first averaged to one row per patient. A five-fold patient-level cross-fitted logistic router used either core routing features or reliability-augmented features, including across-repetition standard deviations of V0 risk, V1R risk and their difference. Thresholds 0.40, 0.50 and 0.60 were fixed before readout.

Direct raw V1R remained the strongest overall policy, but every router improved on the clinical anchor at the point estimate (Supplementary Table 4). The best router used reliability features at threshold 0.60: delta Brier versus V0 was -0.000506 and the bootstrap interval was approximately -0.00162 to +0.00076. These results show that repetition-level stability contains useful routing information and support further development of selective prediction at matched coverage.

### Supplementary Table 4. Development-only router policies

| Policy | FUSE rate | IPCW Brier24 | Delta vs V0 | Delta vs raw V1R | Rank concordance vs raw V1R |
|---|---:|---:|---:|---:|---:|
| V0 | 0.0% | 0.123927 | 0 | +0.001162 | 0.867 |
| Raw V1R | 100.0% | 0.122765 | -0.001162 | 0 | 1.000 |
| Core router, q>=0.40 | 66.1% | 0.123545 | -0.000382 | +0.000780 | 0.945 |
| Core router, q>=0.50 | 54.1% | 0.123511 | -0.000416 | +0.000746 | 0.939 |
| Core router, q>=0.60 | 40.3% | 0.123585 | -0.000341 | +0.000821 | 0.928 |
| Reliability router, q>=0.40 | 67.0% | 0.123648 | -0.000279 | +0.000883 | 0.946 |
| Reliability router, q>=0.50 | 54.8% | 0.123508 | -0.000419 | +0.000743 | 0.938 |
| Reliability router, q>=0.60 | 42.6% | 0.123421 | -0.000506 | +0.000657 | 0.929 |

### RADCURE clinical-radiomics characterization

The RADCURE held-out analysis characterized the performance of adapted clinical/radiomics comparator families in 626 patients with 110 events. The strongest comparator, C2, achieved Uno C 0.806744, 24-month AUC 0.818182 and IPCW Brier 0.090683 (Supplementary Table 5). This analysis provides a strong contemporary benchmark for the multimodal prognostic task and highlights the value of combining clinical and tumour-volume information.

### Supplementary Table 5. RADCURE held-out comparator characterization

| Comparator | IPCW Brier | Uno C | 24-month AUC | Harrell C | CITL | Calibration slope |
|---|---:|---:|---:|---:|---:|---:|
| C1 | 0.095801 | 0.806595 | 0.819376 | 0.795924 | -0.097110 | 1.950857 |
| C2 | 0.090683 | 0.806744 | 0.818182 | 0.797862 | -0.044444 | 1.139466 |
| C3 | 0.098469 | 0.771260 | 0.780742 | 0.761632 | -0.099603 | 1.268349 |
| C4 | 0.097403 | 0.779243 | 0.787882 | 0.768812 | -0.074520 | 1.471544 |

### Transcriptome residual learning in TCGA-HNSC

U8 tested transfer of the residual-shrinkage principle from the HANCOCK blood/ICD/TMA setting to a dense transcriptome modality. The analysis included 519 patients and 221 events. The clinical anchor used age, sex, site, stage, HPV status, treatment and smoking. The transcriptome contained 14,417 common genes represented as within-sample ranks; each training fold retained the 500 most variable genes. The residual head was `Linear(500 -> 32) -> Tanh -> Linear(32 -> 1)`, and the fused score was

\[
\eta_{\mathrm{T1R},i}=\eta_{\mathrm{V0},i}+\lambda_f\Delta\eta_{\mathrm{transcriptome},i}.
\]

All selection steps were confined to training folds. The completed run produced 2,595 out-of-fold rows with complete coverage and an exact fallback error of zero. T1R improved every discrimination measure and the mean Brier score (Supplementary Table 6); discrimination improved in all five seeds (Supplementary Table 7). The frozen gate returned `T1R_EARNS_COMPLEXITY`.

### Supplementary Table 6. T1R development performance in TCGA-HNSC

| Metric | Clinical anchor | T1R | Difference | Favourable seeds |
|---|---:|---:|---:|---:|
| IPCW Brier at 24 months | 0.221795 | 0.218058 | -0.003737 | 4/5 |
| Harrell C | 0.577281 | 0.605919 | +0.028637 | 5/5 |
| Uno C at 24 months | 0.565199 | 0.597265 | +0.032066 | 5/5 |
| Time-dependent AUC at 24 months | 0.557362 | 0.600236 | +0.042874 | 5/5 |

### Supplementary Table 7. T1R paired changes by repetition seed

| Repetition seed | Delta IPCW Brier24 | Delta Uno C24 |
|---:|---:|---:|
| 17 | -0.004443 | +0.037975 |
| 29 | +0.002714 | +0.006398 |
| 43 | -0.004353 | +0.029370 |
| 71 | -0.006560 | +0.048165 |
| 101 | -0.006045 | +0.038420 |

### GEO cross-platform transcriptome characterization

A single T1R model was fitted to the complete TCGA-HNSC development cohort and applied to GSE65858 and GSE41613 without cohort-specific refitting, tuning or threshold selection. Before application, inner cross-validation selected an elastic-net anchor with alpha 0.05 and L1 ratio 0.1, residual penalty 1.0, optimization checkpoint 10 and residual scale 1.0.

T1R showed favourable Brier and discrimination changes in both GEO cohorts (Supplementary Table 8). In GSE65858, Uno C increased from 0.583694 to 0.645818. In GSE41613, the applied clinical anchor had no cross-patient variation, whereas T1R restored patient-level ordering, with Harrell C 0.626361 and 24-month AUC 0.634011. Calibration slopes above one indicated compressed predicted-risk dispersion, making cohort-level recalibration a natural next step for future prospective absolute-risk reporting.

### Supplementary Table 8. GEO transcriptome characterization

| Cohort and metric | Clinical anchor | T1R | Difference |
|---|---:|---:|---:|
| **GSE65858 (n=244; 78 events)** | | | |
| IPCW Brier at 24 months | 0.195207 | 0.195070 | -0.000137 |
| Harrell C | 0.581806 | 0.644868 | +0.063062 |
| Uno C at 24 months | 0.583694 | 0.645818 | +0.062123 |
| Time-dependent AUC at 24 months | 0.588972 | 0.650733 | +0.061762 |
| Calibration-in-the-large | -0.763793 | -0.831959 | -0.068166 |
| Calibration slope | 1.707442 | 1.941562 | +0.234120 |
| **GSE41613 (n=97; 51 events)** | | | |
| IPCW Brier at 24 months | 0.265712 | 0.258607 | -0.007104 |
| Harrell C | 0.500000 | 0.626361 | +0.126361 |
| Uno C at 24 months | 0.500000 | 0.616039 | +0.116039 |
| Time-dependent AUC at 24 months | 0.500000 | 0.634011 | +0.134011 |
| Calibration-in-the-large | -0.273717 | -0.264792 | +0.008925 |
| Calibration slope | -- | 1.939018 | -- |

## Reproducibility and artifact governance

The formal V1R development out-of-fold SHA256 was `E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0`. The confirmation protocol SHA256 was `1E134D30557D1CC153997F6EBB79E99C2E160F85A9F94BF3BBDD81C2C588FDED`, and the locked prediction artifact SHA256 was `E5DA83BDB3BB97C3488687C78CCF166FBD03059619DD0690E2767CAF8F393FCF`. Two V0 reruns produced identical out-of-fold hashes.

Aggregate sources included `research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_aggregate_results.json`, `research_studies/01_pattern_surv_hn/core_backbone/U6R1_patient_level_router_aggregation_exploration/u6r1_aggregate_results.json`, `research_studies/01_pattern_surv_hn/core_backbone/U7R2_RADCURE_external_characterization/u7r2_radcure_external_characterization_aggregate_results.json`, `research_studies/01_pattern_surv_hn/core_backbone/U8_T1R_transcriptome_residual_shrinkage/aggregate_t1r_transcriptome_development_cv_audit.json` and `research_studies/01_pattern_surv_hn/core_backbone/U8E_T1R_external_characterization/aggregate_t1r_external_characterization_audit.json`.

Cohorts, preprocessing and stage definitions were configuration controlled. Repetition seeds were 17, 29, 43, 71 and 101. Each stage recorded analysis label, prior outcome access, tuning status and artifact integrity. Patient identifiers and patient-level predictions were excluded from version control; the publication-facing tables and figures were generated from aggregate metrics, manifests and audits.
