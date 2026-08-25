# U2/V1R residual-shrinkage rescue

This stage does **not** rewrite the original U2 result. The original minimum V1 remains rejected
under its prespecified gate. V1R is a result-informed, post-hoc exploratory rescue that keeps the
same 3,225-parameter Deep Sets architecture but chooses a residual scale inside each inner CV.

The rescue was motivated by a prediction-space sensitivity analysis showing that the unscaled V1
residual was too aggressive: scales around 0.2-0.4 substantially reduced subgroup regret and
calibration-slope deterioration while preserving a small, seed-stable Uno-C signal.

Two decisions are reported after execution:

1. the unchanged original U2 gate;
2. a separately frozen exploratory rescue gate with unchanged safety thresholds and relaxed
   incremental effect-size thresholds.

Official-test and external outcomes remain sealed. A rescue-gate pass cannot be described as the
original V1 passing, confirmatory superiority, or external validation.
