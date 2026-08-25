# V1R paper narrative and section map

Updated: 25 August 2026

This file records how the positive V1R development experiment should be represented in the manuscript. Future manuscript revisions that use V1R evidence should treat this directory, and this file in particular, as the controlled publication-facing source of truth.

## 1. Experiment identity

The experiment documented here is **V1R: shrinkage-controlled residual fusion**. It corresponds to the manuscript's **Level 2 development analysis** and to **Aim 1: safe, censoring-aware fusion under arbitrary usable-modality combinations**.

V1R is not an unconstrained replacement for the clinical model. It retains the V0 clinical-pathological prediction as an anchor and adds optional blood, ICD and TMA evidence through a residual pathway:

\[
\eta_{\mathrm{V1R},i}
=
\eta_{\mathrm{V0},i}
+
\lambda_f\Delta\eta_{\mathrm{V1},i}.
\]

Here, \(f\) indexes the outer cross-validation fold; \(\lambda_f\) is selected only within that fold's inner cross-validation loop; and \(\Delta\eta_{\mathrm{V1},i}\) is the optional-modality residual. If no optional modality is usable, the residual is zero and V1R returns the V0 prediction exactly.

## 2. Core manuscript story

The manuscript should tell the following story:

> A full-coverage clinical-pathological anchor is necessary because optional measurements may be absent or unusable. Optional multimodal measurements can nevertheless contain incremental prognostic information. V1R introduces that information as a shrinkage-controlled residual around the clinical anchor, rather than allowing an unconstrained multimodal model to rewrite clinical risk. In repeated nested cross-fitting, this design improved discrimination and modestly improved probabilistic accuracy while preserving 100% coverage, exact clinical fallback and a bounded worst supported-pattern regret.

The central interpretation is therefore **controlled incremental value**, not compulsory fusion and not replacement of the clinical anchor.

## 3. Positive results carried into the manuscript

The aggregate development results are:

- Cohort: HANCOCK development ecosystem; 610 eligible patients and 173 deaths.
- Repeated nested cross-fitting: five seeds (17, 29, 43, 71, 101), five outer folds and three inner folds.
- V0 and V1R coverage: 100% for both models.
- IPCW Brier score at 24 months: 0.124745 (V0) to 0.124338 (V1R), delta -0.000407.
- Uno C at 24 months: 0.644239 (V0) to 0.665542 (V1R), delta +0.021303.
- Time-dependent AUC at 24 months: 0.662022 (V0) to 0.682511 (V1R), delta +0.020488.
- Harrell C: 0.623021 (V0) to 0.633710 (V1R), delta +0.010690.
- Uno C improved in all five repetition seeds (5/5 favourable directions).
- Empty-set residual fallback error: 0.0.
- Empty-set fused-score fallback error: 0.0.
- Worst supported-pattern Brier regret: +0.009848, below the prespecified +0.020 safety boundary.

These values are the only V1R aggregate values intended for direct use in the current manuscript narrative unless a later controlled result file supersedes them.

## 4. Mapping to manuscript sections

### Abstract

Use V1R as the principal positive development result. Report the cohort size, events, full coverage, Uno C, AUC, IPCW Brier, seed consistency, exact fallback and worst-pattern safety result. Keep the exploratory/development-stage boundary in the same paragraph or immediately after it.

### Introduction

Use V1R to motivate the central design principle: optional modalities should modify a prediction through a controlled residual around a stable clinical anchor, rather than directly replacing the anchor.

### Results: Level 2 / Aim 1

The main result subsection should be titled or framed as:

**Shrinkage-controlled residual fusion improves discrimination while preserving full coverage and safety.**

First establish V0 as the full-coverage clinical reference. Then report the V0-to-V1R comparison. Finally show that the gain was not obtained by deleting patients: both models covered all 610 eligible patients, empty optional sets followed exact V0 fallback, and the worst supported-pattern regret remained under the safety boundary.

### Main results table

Use the V0/V1R paired table from `v1r_positive_results.csv` and `v1r_positive_results.json`. The preferred columns are IPCW Brier24, Uno C24, time-dependent AUC24, Harrell C, coverage and worst supported-pattern regret.

### Main figure

Use the framework in `figure1_v1r_framework.md`: V0 clinical anchor -> usable blood/ICD/TMA set tokens -> permutation-invariant residual encoder -> inner-CV-selected shrinkage -> V1R fusion -> exact V0 fallback -> positive full-coverage readout. Later calibration, router and outcome-untouched confirmation modules must be labelled planned/future, not completed V1R results.

### Discussion

Interpret the result as evidence that optional multimodal measurements can add incremental prognostic information when introduced as a shrinkage-controlled residual. Emphasise that V0 provides operational stability and V1R provides controlled incremental evidence. Do not describe V1R as a final clinical model or as proof that every modality is independently useful.

### Methods and Supplement

Describe the Clinical Residual Deep Sets Cox backbone, the residual formula, fold-specific inner-CV selection of \(\lambda_f\), the paired full-coverage estimands, the supported-pattern safety estimand and the deterministic reproducibility receipt.

## 5. What this experiment does and does not establish

### Supported development claims

- V1R improved internal censoring-aware discrimination relative to V0 under repeated nested cross-fitting.
- The improvement was directionally consistent across all five seeds.
- The result retained full population coverage and exact clinical fallback.
- The observed worst supported-pattern regret remained within the prespecified safety boundary.
- The development evidence supports shrinkage-controlled residual fusion as the central backbone for subsequent reliability and transport analyses.

### Claims that remain out of scope

V1R alone does not establish confirmatory superiority, external generalisation, transportability, clinical utility, deployment readiness, valid external probability calibration, or final patient-level routing. Official-test and external outcomes, calibration-bridge training and final router evaluation remain separate stages.

The original V1 failure must not be rewritten. V1R is a post-hoc exploratory rescue/development backbone and should not be described as passing the original preregistered V1 gate.

## 6. Controlled-use rule for future revisions

For future manuscript edits:

1. Use only the positive aggregate values and claims in this directory for the V1R core narrative.
2. Preserve the V0 anchor -> controlled residual -> full coverage/fallback -> bounded pattern regret logic.
3. Do not copy patient-level predictions into this directory.
4. Do not add negative V1 audit material to this publication-facing folder unless a separate clearly labelled claim-boundary document is needed.
5. Do not promote planned calibration, router, external validation or confirmation modules to completed results without a new approved result extract.
6. If a later V1R rerun changes a value, update the CSV/JSON, claims and this narrative map together, and record the new provenance and hash.