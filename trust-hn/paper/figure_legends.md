# Figure legends ? V1R and U5R7 manuscript draft

## Figure 1 | Clinically anchored shrinkage-controlled residual survival framework with development calibration bridge

Framework diagram for PATTERN-Surv-HN. A postoperative clinical-pathological anchor produces a prediction for every eligible patient. Usable blood, ICD and TMA measurements are represented as an unordered set of modality tokens with usability and quality indicators. A permutation-invariant Deep Sets encoder estimates residual evidence beyond the anchor. Inner cross-validation selects the residual scale, and the raw V1R fusion is \(\eta_{V1R}=\eta_{V0}+\lambda\Delta\eta_{res}\). When no optional modality is usable, the residual is set to zero and the model follows the exact clinical-anchor fallback path. A separate U5R7 module then applies a fixed positive-slope global logit bridge, \(x_{bridge}=\alpha_{logloss}+0.90\operatorname{logit}(p_{V1R})\), for a development-only cross-fitted calibration diagnostic. The bridge is strictly monotone and rank-preserving. The final branch shows the locked confirmation readout for raw V1R only; bridge application to confirmation is labelled pending a separately frozen protocol. The confirmation panel is labelled positive directional point-estimate evidence because bootstrap intervals crossed zero for the principal deltas.

## Figure 2 | Natural acquisition and usability patterns

Framework placeholder for the HANCOCK availability contract: acquired versus usable blood, ICD and TMA measurements, observed modality combinations, partial inputs and exact clinical fallback. The final panel should distinguish data availability from model usability without implying that rare patterns have independent confirmatory support. The U5R7 bridge is global-only and does not introduce pattern-specific parameters.

## Figure 3 | V1R fusion, U5R7 development calibration and locked confirmation evidence

Suggested panels: paired anchor-to-V1R differences for IPCW Brier, Uno C and time-dependent AUC; seed-level direction of Uno-C change in development; U5R7 raw-versus-bridge CITL and calibration slope; bridge Brier delta and supported-pattern regret against the +0.0005 and +0.005 development gates; coverage and ranking preservation; and locked raw-V1R confirmation point estimates with bootstrap intervals. This is a development-plus-locked-confirmation figure, not an external-validation, confirmed-bridge or clinical-utility figure.
