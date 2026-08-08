# Phase 5 final frozen configuration

**Frozen on:** 2026-08-07

- Primary model pathway: B2 clinical anchor -> B6 stacked residual fusion -> B7 reliability gate.
- Primary gate variant: `full_equal_weight`.
- Primary coverage profile: `90`.
- Sensitivity profiles: equal-weight 80% and 100%; OOD-only; uncertainty-only; learned nonnegative weights.
- Threshold rule: calibration reliability quantiles only; no outcome optimization.
- Learned gate weights: training OOF prediction errors only.
- Primary endpoint: overall survival at 730.5 days.
- Locked/external outcomes: not opened.
- Phase 6 unseal approval: false.
- Any later change to a frozen decision file invalidates its recorded SHA-256 and requires an explicit amendment; it must not be silently treated as the original freeze.
