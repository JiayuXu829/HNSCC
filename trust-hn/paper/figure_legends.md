# Figure legends ? V1R and U5R7 manuscript draft

## Figure 1 | Clinically anchored residual fusion architecture for PATTERN-Surv-HN

**a**, Postoperative clinical-pathological variables are encoded by an elastic-net Cox clinical anchor (V0). **b**, Usable blood, ICD and TMA measurements are represented as unordered modality-specific tokens, each augmented with modality identity, availability/usability status and quality indicators, and processed by a shared permutation-invariant Deep Sets residual encoder. **c**, The residual estimate is shrinkage-controlled and added to the V0 anchor to produce the raw V1R score; residual penalty, optimization checkpoint and fold-specific residual scale are selected within inner cross-validation. **d**, The primary prediction path is raw V1R with full coverage. If no optional modality is usable, the residual is exactly zero and the model returns the V0 prediction. A global monotone calibration bridge is shown as a development-only layer and is not part of the primary locked readout. A reliability-routing module is shown as an optional exploratory concept rather than a validated deployment component.

Source files: `paper/figures/figure1_pattern_surv_hn_framework.pptx`; vector export `paper/figures/figure1_pattern_surv_hn_framework.pdf`; raster export `paper/figures/figure1_pattern_surv_hn_framework.png`.

## Figure 2 | Natural acquisition and usability patterns

Framework placeholder for the HANCOCK availability contract: acquired versus usable blood, ICD and TMA measurements, observed modality combinations, partial inputs and exact clinical fallback. The final panel should distinguish data availability from model usability without implying that rare patterns have independent confirmatory support. The U5R7 bridge is global-only and does not introduce pattern-specific parameters.

## Figure 3 | V1R fusion, U5R7 development calibration and locked confirmation evidence

Suggested panels: paired anchor-to-V1R differences for IPCW Brier, Uno C and time-dependent AUC; seed-level direction of Uno-C change in development; U5R7 raw-versus-bridge CITL and calibration slope; bridge Brier delta and supported-pattern regret against the +0.0005 and +0.005 development gates; coverage and ranking preservation; and locked raw-V1R confirmation point estimates with bootstrap intervals. This is a development-plus-locked-confirmation figure with a clearly separated secondary post-unseal bridge validation; it is not an external-validation, confirmed-bridge or clinical-utility figure.
