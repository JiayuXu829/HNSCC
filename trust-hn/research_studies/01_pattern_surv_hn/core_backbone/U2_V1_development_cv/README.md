# U2/V1 development cross-validation and V0-vs-V1 complexity gate

U2 is the first patient-level training stage for the minimum PATTERN-Surv-HN V1 backbone. It is
restricted to the 610 eligible HANCOCK official-training patients and their development outcomes.
The official-test outcomes and all external outcomes remain sealed.

The stage reuses the exact five-by-five V0 outer fold assignments and each fold's already selected
clinical-anchor candidate. Within every outer fold it refits the clinical anchor and all blood,
ICD, and TMA preprocessing on training IDs only. A small nested inner procedure selects only the
residual-score penalty and optimization checkpoint; the 3,225-parameter Deep Sets architecture is
not searched or expanded.

The fused score is `eta_fused = eta_clinical + delta_eta`. The final residual head starts at zero,
and patients with no usable additional modality retain the structural exact fallback
`delta_eta = 0`, so their fused score equals the clinical score exactly. Absolute 24-month risk is
computed using a Breslow baseline hazard estimated from the corresponding training-fold outcomes
and fused training scores only.

`frozen_v0_v1_complexity_gate.yaml` was written before execution. V1 is retained only if it passes
100% coverage, structural fallback, safety/non-inferiority, calibration, supported-pattern regret,
and stable incremental-value requirements. Failure means retaining V0; it does not authorize
post-hoc threshold changes or an expansion to V2.
