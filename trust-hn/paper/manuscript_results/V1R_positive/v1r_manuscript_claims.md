# Manuscript claims supported by the V1R and U5R7 result extracts

## Development V1R claims

1. V1R improved 24-month discrimination over the clinical-pathological anchor in repeated nested cross-fitting.
2. Mean Uno C improved from 0.644239 to 0.665542 (+0.021303), with favourable direction in all five repetition seeds.
3. Mean 24-month time-dependent AUC improved from 0.662022 to 0.682511 (+0.020488).
4. Mean IPCW Brier score improved from 0.124745 to 0.124338 (delta -0.000407).
5. V1R retained 100% prediction coverage and exact clinical fallback when no optional modality was usable.
6. Worst supported-pattern Brier regret was +0.009848, within the prespecified +0.020 safety boundary.

## Development U5R7 bridge claims

7. U5R7 is a fixed global positive-slope logit bridge on raw V1R risk: \(x_{bridge}=\alpha_{logloss}+0.90\operatorname{logit}(p_{V1R})\).
8. The intercept was fitted by IPCW-weighted log-loss inside repeated development cross-fitting; confirmation outcomes were not used.
9. In 2,460 bridge-evaluable repeated OOF rows with 415 evaluable events, IPCW Brier24 changed from 0.126637 to 0.126784 (delta +0.000147).
10. U5R7 moved CITL from +0.011680 to -0.003796 and calibration slope from 0.825887 to 0.881552.
11. The absolute CITL error improved by 0.007884 and the absolute slope error improved by 0.055665.
12. Coverage remained 100%, ranking was preserved in all held-out folds, and worst supported-pattern Brier regret was +0.004176, below the +0.005 exploratory gate.
13. U5R7 is a development-only calibration bridge result; it is not a confirmed external-calibration result. A later U5R8 locked secondary post-unseal validation preserved ranking and coverage but failed the Brier, CITL and calibration-slope safety gates, so the bridge remains development-only.

## Locked confirmation claims

14. In 152 outcome-untouched confirmation patients with 40 events, raw V1R retained 100% coverage and showed favourable point estimates for Uno C, IPCW Brier, time-dependent AUC, Harrell C and calibration summaries.
15. Confirmation Uno C was 0.804242 versus 0.782579 for the anchor; confirmation IPCW Brier was 0.131246 versus 0.136412.
16. Patient-level stratified bootstrap intervals crossed zero for the principal confirmation deltas; the appropriate wording is positive directional confirmation signal, not definitive superiority.
17. U5R7 was not part of the primary raw-V1R confirmation estimand. U5R8 evaluated the frozen bridge only as a secondary post-unseal validation and found no support for promoting it to confirmed calibration.

## Unified interpretation

18. The manuscript method is V1R residual fusion with a separately described U5R7 development calibration layer.
19. Optional multimodal measurements add incremental prognostic information when introduced as a shrinkage-controlled residual around a stable clinical anchor.
20. U5R7 adjusts the development risk scale conservatively without changing ranking, coverage or fallback behaviour.
21. V1R and U5R7 remain exploratory, result-informed analyses and do not establish external generalisation, external calibration, transportability, clinical utility or deployment readiness.
