# V1R development calibration bridge: methods and formulae

## Status and intended use

U5R7 is the publication-facing, development-only calibration-bridge result selected after the U5R5 fixed-slope and U5R6 intercept-objective exploration. It is a **cross-fitted development diagnostic**, not a confirmation-cohort result. The locked confirmation analysis remains the raw V1R analysis because no bridge was applied after confirmation outcomes were unsealed.

The bridge is a risk-scale layer on top of the V1R backbone. It does not retrain the V1R encoder, alter the V0 fallback, create a router, remove patients, or change the ordering of patients.

## Frozen candidate

- Candidate: `beta_0.900_logloss`
- Global slope: 0.90
- Intercept objective: weighted log-loss
- Scope: global-only; no pattern-specific parameters
- Cross-fitting: alpha fitted on non-held-out development folds and evaluated on the held-out fold
- Seeds: 17, 29, 43, 71, 101
- Outer folds: 5 per seed
- Development cohort: 610 eligible patients, 173 events
- Bridge-evaluable repeated OOF rows: 2,460 rows and 415 evaluable events

## Formula

Let \(p_{\mathrm{V1R},i}\) be the raw 24-month V1R risk for patient \(i\). The bridge operates on the logit scale:

\[
x_{\mathrm{raw},i}=\operatorname{logit}(p_{\mathrm{V1R},i}).
\]

\[
x_{\mathrm{bridge},i}=\alpha_{\mathrm{logloss},f}+0.90x_{\mathrm{raw},i}.
\]

\[
p_{\mathrm{bridge},i}=\sigma(x_{\mathrm{bridge},i})
=\frac{1}{1+\exp(-x_{\mathrm{bridge},i})}.
\]

For each held-out outer fold \(f\), only the non-held-out development folds are used to estimate \(\alpha_{\mathrm{logloss},f}\) by weighted log-loss. The positive global slope makes the map strictly monotone:

\[
\frac{\partial p_{\mathrm{bridge}}}{\partial p_{\mathrm{V1R}}}>0.
\]

Therefore, within each held-out fold, the patient ranking is preserved exactly. Since the bridge is global-only, it also applies the same risk-scale rule across supported acquisition patterns.

## Development result

| Metric | Raw V1R | U5R7 bridge | Change | Direction |
|---|---:|---:|---:|---|
| IPCW Brier24 | 0.126637 | 0.126784 | +0.000147 | small increase; within +0.0005 global gate |
| CITL | +0.011680 | -0.003796 | -0.015477 | absolute error improved by 0.007884 |
| Calibration slope | 0.825887 | 0.881552 | +0.055665 | absolute error to 1 improved by 0.055665 |
| Worst supported-pattern Brier regret | ? | +0.004176 | ? | below +0.005 gate |
| Coverage | 100% | 100% | 0 | preserved |
| Ranking | preserved reference | preserved | ? | all held-out folds |

The bridge-evaluable Brier values are the absolute-risk calibration diagnostic over 2,460 repeated OOF rows and 415 evaluable events. They should not be substituted for the primary V0-versus-V1R discrimination table, whose IPCW-Brier estimand is reported separately.

## Interpretation for the manuscript

The positive result is a conservative calibration stabilization: the bridge moves the average calibration-in-the-large closer to zero and the calibration slope closer to one, with only a small development Brier penalty and no loss of coverage or ranking. The result supports describing U5R7 as a **development calibration bridge**. It does not support claims that the bridge has been confirmed, transported, shown clinically useful, or made deployment-ready.
