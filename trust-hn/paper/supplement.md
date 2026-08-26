# PATTERN-Surv-HN Supplementary Information: V1R development, U5R7 calibration bridge and locked confirmation

> Updated 26 August 2026. This supplement documents the aggregate results carried into the manuscript from the V1R development, U5R7 development-only bridge and locked confirmation stages. Patient-level predictions remain Git-ignored. U5R7 is exploratory development evidence and is not presented as confirmed external calibration or definitive superiority.

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

The confirmation cohort contained 152 patients and 40 events. Patient-level stratified bootstrap used 2,000 replicates with seed 20260825. The 95% interval for delta Uno C was -0.025965 to +0.070816 and for delta IPCW Brier was -0.012843 to +0.002171; both crossed zero. The confirmation table is raw V1R only; U5R7 was not applied.

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

The main framework figure should contain: (a) clinical anchor; (b) usable blood, ICD and TMA set tokens; (c) permutation-invariant residual encoder; (d) inner-CV-selected shrinkage; (e) raw V1R fused score; (f) exact clinical fallback for an empty set; (g) completed U5R7 global monotone logit bridge labelled development-only; (h) locked raw-V1R confirmation readout; and (i) a bridge-to-confirmation path labelled pending a separately frozen protocol. Router and clinical-utility modules remain future work.
