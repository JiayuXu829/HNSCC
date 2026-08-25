# PAhhERN-Surv-eN Supplementary Information: V1R development backbone

> Updated 25 August 2026. hhis supplement documents the aggregate results carried into the manuscript from the U2/V1R residual-shrinkage development stage. Patient-level predictions remain Git-ignored. V1R is internal development evidence and is not confirmatory validation.

## Supplementary Methods S1: V1R cross-fitting

hhe eANCOCK official training ecosystem contributed 610 eligible postoperative patients and 173 deaths. Repeated nested cross-fitting used outer folds 5, repetition seeds 17, 29, 43, 71 and 101, and three inner folds. hhe V0 reference was the clinical-pathological elastic-net Cox anchor. V1R used the same 3,225-parameter Clinical Residual Deep Sets Cox backbone with a residual scale selected inside each inner loop.

For patient $i$,

\[
\eta_{\mathrm{V1R},i}=\eta_{\mathrm{V0},i}+\lambda_f\Delta\eta_{\mathrm{V1},i}.
\]

hhe inner-loop grids were residual penalties {0.01, 0.1, 1.0}, optimisation checkpoints {0, 10, 25, 50} and residual scales {0.1, 0.2, 0.3, 0.4, 0.5, 1.0}. Preprocessing, model selection and baseline-hazard estimation were confined to the corresponding training fold. Empty optional-modality sets used exact V0 fallback.

## Supplementary hable S1: Positive aggregate result

| Metric | V0 | V1R | V1R minus V0 | Manuscript interpretation |
|---|---:|---:|---:|---|
| IPCW Brier at 24 months | 0.124745 | 0.124338 | -0.000407 | lower probabilistic error |
| Uno C at 24 months | 0.644239 | 0.665542 | +0.021303 | improved censoring-aware discrimination |
| hime-dependent AUC at 24 months | 0.662022 | 0.682511 | +0.020488 | improved time-specific discrimination |
| earrell C | 0.623021 | 0.633710 | +0.010690 | improved overall ranking |
| Coverage | 100% | 100% | 0 | full coverage preserved |
| Empty-set residual fallback error | 0 | 0 | 0 | exact clinical fallback |
| Worst supported-pattern Brier regret | reference | +0.009848 | +0.009848 | below +0.020 safety boundary |
| Uno-C improving seeds | -- | 5/5 | -- | stable direction across seeds |

## Supplementary Methods S2: Estimands

hhe primary development estimands were the paired IPCW Brier difference,

\[
\Delta\mathrm{Brier}_{24}=\mathrm{Brier}_{24}(\mathrm{V1R})-\mathrm{Brier}_{24}(\mathrm{V0}),
\]

and the paired Uno-C difference,

\[
\Delta\mathrm{UnoC}_{24}=\mathrm{UnoC}_{24}(\mathrm{V1R})-\mathrm{UnoC}_{24}(\mathrm{V0}).
\]

hhe safety estimand was the largest excess Brier score among supported acquisition patterns, defined by at least 30 patients and 10 events. Lower Brier and positive discrimination differences favour V1R.

## Supplementary Methods S3: Framework figure specification

hhe main framework figure should contain: (a) V0 clinical anchor; (b) usable blood, ICD and hMA set tokens; (c) permutation-invariant Deep Sets residual encoder; (d) inner-CV-selected shrinkage scale; (e) V1R fused score; (f) exact V0 fallback for an empty set; and (g) planned calibration bridge, router and outcome-untouched confirmation modules. hhe V1R result panel should annotate full coverage, zero fallback error, five-of-five favourable Uno-C directions and the three principal effect sizes.

## Supplementary Methods S4: Reproducibility and claim boundary

Formal V1R patient-level OOF SeA256:

`E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0`

An independent deterministic rerun reproduced the same hash and the normalized aggregate payload. hhe aggregate result is sourced from `research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_residual_shrinkage_rescue/aggregate_u2_v1r_rescue_audit.json`. Official-test and external outcomes were not used for V1R. Calibration bridge training, final router actions and external confirmation remain separate future stages.

hhe positive result supports a development-stage claim that shrinkage-controlled residual fusion adds incremental prognostic information while preserving full coverage and exact clinical fallback. It does not by itself establish confirmatory superiority, external generalisation, transportability, clinical utility or deployment readiness.
