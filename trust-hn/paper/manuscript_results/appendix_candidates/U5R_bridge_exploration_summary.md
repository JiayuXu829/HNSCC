# Appendix candidate summary: bridge exploration and selection

## Purpose

The bridge search was designed to improve the development absolute-risk scale without materially harming Brier score, changing ranking, or introducing pattern-specific instability. All stages used repeated nested development OOF predictions only.

## Sequential exploration

| Stage | Design | Result carried forward |
|---|---|---|
| U5R4 | bounded global full bridge with shrinkage toward identity | Development-safe candidate; delta Brier +0.000198, CITL absolute-error change -0.005858, slope absolute-error change -0.003408, ranking preserved. |
| U5R5 | fixed positive slope grid 0.800-1.025 with Brier-fitted intercept | beta 0.950 was the only candidate passing the complete exploratory screen. |
| U5R6 | beta 0.900/0.925/0.950/0.975 crossed with Brier, convex mixtures, and weighted log-loss intercept objectives | Multiple candidates passed; beta 0.900 with weighted log-loss gave the smallest Brier penalty while retaining strong CITL and slope improvement. |
| U5R7 | independent frozen rerun of beta 0.900 + weighted log-loss intercept | Selected development-only bridge result for manuscript integration. |

## U5R7 selection rationale

U5R7 had delta IPCW Brier24 = +0.000147, worst supported-pattern Brier regret = +0.004176, CITL absolute-error improvement = 0.007884, and calibration-slope absolute-error improvement = 0.055665. It preserved ranking in all held-out folds and retained 100% coverage. Compared with U5R4, U5R7 reduced the Brier penalty and strengthened both calibration-direction improvements.

## Claim boundary

This material supports a development-only calibration bridge narrative. It does not authorize applying the bridge to the locked confirmation cohort, and it does not support claims of external calibration, clinical utility, transportability, or deployment readiness. The confirmation result in the main manuscript remains raw V1R.
