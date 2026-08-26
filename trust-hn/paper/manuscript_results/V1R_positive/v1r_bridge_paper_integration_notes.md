# U5R7 bridge: paper integration notes

## Core story

The manuscript now separates two functions that were previously conflated:

1. **V1R residual fusion** adds optional blood, ICD and TMA evidence around the V0 clinical-pathological anchor and supplies the primary discrimination result.
2. **U5R7 bridge** is a conservative, global, rank-preserving risk-scale layer applied to raw V1R in development-only cross-fitting. It improves calibration direction without changing the ordering, coverage, or fallback logic.

The resulting narrative is:

> A full-coverage clinical anchor is protected by a shrinkage-controlled multimodal residual. V1R improves ranking and time-specific discrimination. Because the raw V1R risk scale showed mild under-dispersion in development, a frozen positive-slope logit bridge (beta = 0.90, weighted-log-loss intercept) was evaluated as a separate calibration layer. The bridge moved CITL toward zero and slope toward one while keeping the Brier penalty within the development gate and preserving ranking and coverage. The locked confirmation readout remains raw V1R; application of the bridge to confirmation is a future separately frozen step.

## Results wording approved for the manuscript

> In a repeated, cross-fitted development-only calibration diagnostic, the selected global bridge used \(x_{bridge}=\alpha_{logloss}+0.90\,\operatorname{logit}(p_{V1R})\). Relative to raw V1R, IPCW Brier24 changed from 0.126637 to 0.126784 (delta +0.000147), while CITL changed from +0.011680 to -0.003796 and calibration slope from 0.825887 to 0.881552. The absolute CITL error improved by 0.007884 and the absolute slope error by 0.055665. Coverage remained 100%, ranking was preserved in every held-out fold, and worst supported-pattern Brier regret was +0.004176, below the +0.005 exploratory gate.

## Claim boundary

- Use ?development-only?, ?cross-fitted?, and ?exploratory calibration bridge? in the Results and Methods.
- Do not call U5R7 a confirmation result.
- Do not apply U5R7 numbers to the confirmation cohort.
- Do not claim clinical utility, external calibration, transportability, or deployment readiness.
- Keep the prior raw V1R confirmation point estimates and bootstrap intervals unchanged.
