# V1R and U5R7 paper narrative and section map

Updated: 26 August 2026

This file is the controlled publication-facing source of truth for the V1R manuscript narrative. It foregrounds V1R as the multimodal fusion backbone and U5R7 as a separate development-only calibration layer. Raw V1R remains the confirmation output.

## 1. Experiment identity

The manuscript method is **V1R: shrinkage-controlled residual fusion**. It retains the V0 clinical-pathological prediction as an anchor and adds optional blood, ICD and TMA evidence through a residual pathway:

\[
\eta_{\mathrm{V1R},i}=\eta_{\mathrm{V0},i}+\lambda_f\Delta\eta_{\mathrm{res},i}.
\]

U5R7 is not a new backbone. It is a global monotone risk-scale bridge applied to raw V1R in development-only cross-fitting:

\[
x_{\mathrm{bridge}}=\alpha_{\mathrm{logloss},f}+0.90\operatorname{logit}(p_{\mathrm{V1R}}),\qquad p_{\mathrm{bridge}}=\sigma(x_{\mathrm{bridge}}).
\]

If no optional modality is usable, V1R returns the V0 prediction exactly; U5R7 does not alter that fallback.

## 2. Core manuscript story

A full-coverage clinical-pathological anchor is necessary because optional measurements may be absent or unusable. Optional multimodal measurements can nevertheless contain incremental prognostic information. V1R introduces that information as a shrinkage-controlled residual around the clinical anchor, rather than allowing an unconstrained multimodal pathway to rewrite clinical risk. In repeated nested cross-fitting, V1R improved discrimination and primary probabilistic accuracy while preserving 100% coverage, exact clinical fallback and bounded pattern-level regret.

The raw V1R absolute-risk scale showed mild under-dispersion in a separate development diagnostic. U5R7 addressed this with a fixed positive-slope global logit bridge. The bridge moved CITL toward zero and the calibration slope toward one with a small Brier penalty inside the development gate, while preserving ranking and coverage. The primary locked confirmation remains a raw-V1R readout. U5R8 later evaluated the frozen bridge as a secondary post-unseal validation; ranking and coverage were preserved, but Brier, CITL and slope safety gates failed, so the bridge is not promoted to confirmed external calibration.

## 3. Results carried into the manuscript

### Development V1R

- 610 eligible patients and 173 deaths.
- Five repetition seeds (17, 29, 43, 71, 101), five outer folds and three inner folds.
- IPCW Brier24: 0.124745 to 0.124338, delta -0.000407.
- Uno C24: 0.644239 to 0.665542, delta +0.021303; favourable in all five seeds.
- Time-dependent AUC24: 0.662022 to 0.682511, delta +0.020488.
- Harrell C: 0.623021 to 0.633710, delta +0.010690.
- Coverage 100%; exact empty-set fallback error 0.0.
- Worst supported-pattern Brier regret +0.009848, below +0.020.

### Development U5R7 bridge

- Fixed candidate: `beta_0.900_logloss`; beta = 0.90; global-only; weighted-log-loss intercept.
- Bridge diagnostic: 2,460 repeated OOF rows and 415 evaluable events.
- IPCW Brier24: 0.126637 to 0.126784, delta +0.000147.
- CITL: +0.011680 to -0.003796; absolute error change -0.007884.
- Calibration slope: 0.825887 to 0.881552; absolute error change -0.055665.
- Coverage 100%; ranking preserved in all held-out folds.
- Worst supported-pattern Brier regret +0.004176, below +0.005.
- Interpretation: development-only positive calibration-bridge signal.

### Locked confirmation

- 152 patients and 40 events in the researcher-confirmed outcome-untouched HANCOCK OOD cohort.
- Twenty-five matched V0/raw-V1R members; predictions sealed before outcome unmasking; no confirmation tuning or refit.
- Uno C24: 0.782579 to 0.804242, delta +0.021664.
- IPCW Brier24: 0.136412 to 0.131246, delta -0.005166.
- Time-dependent AUC24: 0.801094 to 0.813637, delta +0.012543.
- Harrell C: 0.733253 to 0.752842, delta +0.019589.
- Calibration-in-the-large moved 0.211270 to 0.116482; slope moved 1.945126 to 1.501223.
- Coverage remained 100%; the only supported pattern (`111`) had Brier delta -0.005166.
- Bootstrap intervals crossed zero for delta Uno C and delta IPCW Brier; this is a positive directional raw-V1R confirmation signal, not definitive superiority.
- U5R7 was not part of the primary raw-V1R confirmation estimand; U5R8 secondary post-unseal validation did not pass bridge safety gates.

## 4. Section mapping

### Abstract

Present V1R development discrimination first, then report U5R7 as a separate development-only calibration diagnostic, and finally report raw V1R confirmation with the uncertainty boundary.

### Introduction

Motivate controlled incremental fusion and distinguish ranking/discrimination from absolute-risk calibration.

### Results

1. Establish the full-coverage anchor.
2. Report V1R development cross-fitting and safety/fallback checks.
3. Report the U5R7 development-only calibration bridge, formula and gates.
4. Report the locked raw-V1R outcome-untouched confirmation point estimates.
5. State explicitly that U5R7 remains development-only because the later U5R8 secondary post-unseal validation did not pass its Brier, CITL and slope gates.

### Methods

Describe the V1R residual equation, set pooling, fold-bound preprocessing, inner-CV selection, exact fallback, U5R7 logit bridge and the locked prediction-seal-before-outcome protocol.

### Discussion

Interpret V1R as controlled incremental value and U5R7 as a conservative development risk-scale layer. Do not claim external calibration, transportability, clinical utility or deployment readiness.

### Main figure and tables

Figure 1 should show the anchor, usable modality set, residual encoder, shrinkage, raw V1R output, exact fallback, U5R7 development bridge and separate raw-V1R confirmation readout. The bridge-to-confirmation path should be labelled as secondary post-unseal validation with failed calibration gates; the primary confirmation path remains raw V1R. Table 1 should report development V0/V1R results; Table 2 should report U5R7 development calibration results; Table 3 should report locked raw-V1R confirmation results and bootstrap intervals.

## 5. Controlled-use rule

1. Use this directory for all subsequent manuscript edits.
2. Use only aggregate values stored in the paired development, U5R7 and confirmation extracts.
3. Keep patient-level predictions out of this directory.
4. Keep detailed U5R parameter grids in `paper/manuscript_results/appendix_candidates/`.
5. Do not describe U5R7 as confirmation evidence without a new locked result extract.
6. Keep the exploratory/result-informed status explicit in Methods and Discussion.
