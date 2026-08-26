# U5R4 fixed bounded global bridge diagnostic audit

- Status: development-only diagnostic; not confirmation.
- Candidate: `bounded_global_full_g0.25`.
- Fit: IPCW-Brier objective on the other development folds only.
- Constraint: beta in [0.75, 1.25]; gamma fixed at 0.25; global-only; no pattern-specific terms.
- Confirmation outcomes were not read and no patient-level tracked output was written.

## Results

```json
{
  "aggregate_metrics": {
    "abs_citl_error_deterioration": -0.00585768548158061,
    "abs_slope_error_deterioration": -0.003408209504892068,
    "calibration_slope_candidate": 0.8292949166819198,
    "calibration_slope_raw": 0.8258867071770277,
    "citl_candidate": 0.005822613213227856,
    "citl_raw": 0.011680298694808466,
    "delta_ipcw_brier": 0.00019774680506068343,
    "events_evaluable": 415,
    "ipcw_brier_candidate": 0.12683437736359268,
    "ipcw_brier_raw": 0.126636630558532,
    "n_evaluable": 2460
  },
  "analysis": "U5R4 fixed bounded global V1R bridge development-only diagnostic",
  "candidate": "bounded_global_full_g0.25",
  "cohort": "HANCOCK official training development OOF",
  "confirmation_evaluation_performed": false,
  "confirmation_outcomes_used_for_bridge_tuning": false,
  "eligible_n": 610,
  "events": 173,
  "outer_folds": 5,
  "patient_level_outputs": "not written",
  "protocol": "frozen_bounded_global_bridge_candidate_protocol.yaml",
  "safety": {
    "coverage_preserved": true,
    "development_safe_pass": true,
    "global_delta_ipcw_brier_max": 0.005,
    "improves_calibration": true,
    "mean_absolute_citl_error_deterioration_max": 0.1,
    "mean_absolute_slope_error_deterioration_max": 0.15,
    "passes_citl_gate": true,
    "passes_global_brier_gate": true,
    "passes_slope_gate": true,
    "passes_supported_pattern_gate": true,
    "rank_preservation_all_folds": true,
    "strictly_monotone_effective_slope": true,
    "supported_pattern_regret_max": 0.02
  },
  "seeds": [
    17,
    29,
    43,
    71,
    101
  ],
  "worst_supported_pattern_regret": 0.0007584845396440554
}
```

## Interpretation

Development-safe candidate gate: PASS.
This result does not authorize confirmation application or deployment claims.
Raw V1R remains the retained backbone output.
