# Figure legends — V1R manuscript draft

## Figure 1 | Clinically anchored shrinkage-controlled residual survival framework

Framework diagram for PATTERN-Surv-HN. A postoperative clinical-pathological anchor (V0) produces a prediction for every eligible patient. Usable blood, ICD and TMA measurements are represented as an unordered set of modality tokens with usability and quality indicators. A permutation-invariant Deep Sets encoder estimates residual evidence beyond V0. An inner-cross-validation-selected residual scale controls the fusion:

\[
\eta_{\mathrm{V1R}}=\eta_{\mathrm{V0}}+\lambda\Delta\eta_{\mathrm{V1}}.
\]

When no optional modality is usable, the residual is set to zero and the model follows the exact V0 clinical fallback path. The completed HANCOCK development readout should annotate 610 patients, 173 deaths, 100% coverage, Uno C24 improvement from 0.6442 to 0.6655, AUC24 improvement from 0.6620 to 0.6825, Brier24 improvement from 0.1247 to 0.1243, five of five favourable Uno-C seeds and worst supported-pattern regret of +0.00985. Calibration bridge, reliability router and outcome-untouched confirmation are shown as downstream modules and labelled planned/future.

## Figure 2 | Natural acquisition and usability patterns

Framework placeholder for the HANCOCK availability contract: acquired versus usable blood, ICD and TMA measurements, observed modality combinations, partial inputs and exact clinical fallback. The final panel should distinguish data availability from model usability without implying that rare patterns have independent confirmatory support.

## Figure 3 | V1R paired development evidence

Suggested panels: paired V0-to-V1R differences for IPCW Brier, Uno C and time-dependent AUC; seed-level direction of Uno-C change; coverage and fallback verification; and supported-pattern Brier regret against the +0.020 safety boundary. This is a development figure, not an external-validation figure.
