# U5R8 locked secondary bridge validation audit

- **Status:** completed as a locked secondary post-unseal validation.
- **Cohort:** HANCOCK OOD TEST, n=152, events=40.
- **Bridge:** `p_bridge = sigmoid(-0.14503379856995471 + 0.90 * logit(p_V1R_raw))`.
- The intercept was the arithmetic mean of the 25 already-frozen U5R7 development fold-specific log-loss intercepts.
- The beta, intercept aggregation rule, cohort, and estimands were frozen before this run.
- Confirmation outcomes had already been unsealed for the preceding U2/V1R raw confirmation evaluation; therefore this is **not** a new pristine outcome-untouched confirmation.
- No confirmation outcome was used to tune or select alpha, beta, a pattern-specific adjustment, a router, or a refit.
- Raw V1R predictions were not changed; the bridge is a monotone global transformation and ranking was checked exactly.
- No patient-level output was written to tracked research or paper-facing directories.

## Locked readout

```json
{
  "bootstrap": {
    "method": "patient_level_stratified_bootstrap",
    "replicates": 2000,
    "seed": 20260827,
    "summary": {
      "abs_citl_error_change": {
        "ci95_lower": -0.018989598470775776,
        "ci95_upper": 0.016554524020894745,
        "mean": 0.000552388111240901,
        "replicates": 2000
      },
      "abs_slope_error_change": {
        "ci95_lower": 0.0002730539536367545,
        "ci95_upper": 0.2791226908146553,
        "mean": 0.17129786415587725,
        "replicates": 1960
      },
      "delta_calibration_slope": {
        "ci95_lower": 0.10527757695130453,
        "ci95_upper": 0.2791226908146553,
        "mean": 0.17643123278637918,
        "replicates": 1960
      },
      "delta_citl": {
        "ci95_lower": -0.01213146053663589,
        "ci95_upper": 0.02046086947500906,
        "mean": 0.004072358642265406,
        "replicates": 2000
      },
      "delta_ipcw_brier": {
        "ci95_lower": -0.0007977289571666879,
        "ci95_upper": 0.0027995397549528374,
        "mean": 0.0010986836486849652,
        "replicates": 2000
      }
    }
  },
  "bridge": {
    "alpha_dev_mean": -0.1450337985699547,
    "beta": 0.9,
    "candidate": "beta_0.900_logloss",
    "formula": "p_bridge = sigmoid(alpha_dev_mean + 0.90*logit(p_V1R_raw))",
    "parameter_source": "research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_parameters.csv"
  },
  "cohort_id": "HANCOCK_OOD_TEST",
  "cohort_role": "locked_secondary_validation_of_frozen_development_bridge",
  "evaluated_on": "2026-08-27",
  "events": 40,
  "governance": {
    "alpha_refit_on_confirmation": false,
    "beta_reselected_on_confirmation": false,
    "clinical_utility_claim_permitted": false,
    "confirmation_outcomes_used_for_bridge_parameter_selection": false,
    "deployment_readiness_claim_permitted": false,
    "patient_level_results_tracked": false,
    "patient_removal": false,
    "pattern_specific_tuning": false,
    "post_unseal_refit": false,
    "raw_v1r_prediction_modified": false,
    "router_trained": false
  },
  "horizon_days": 730.5,
  "n": 152,
  "outcomes_were_already_unsealed_before_bridge_protocol_freeze": true,
  "pattern_summary": [
    {
      "abs_citl_error_change": 0.004193869266130662,
      "abs_slope_error_change": 0.16781503882198923,
      "calibration_slope_bridge": 1.6781502918245472,
      "calibration_slope_raw": 1.510335253002558,
      "citl_bridge": 0.16094441769005133,
      "citl_raw": 0.15675054842392067,
      "delta_calibration_slope": 0.16781503882198923,
      "delta_citl": 0.004193869266130662,
      "delta_ipcw_brier": 0.0010845289567504302,
      "events": 40,
      "events_evaluable": 26,
      "ipcw_brier_bridge": 0.13578194779242755,
      "ipcw_brier_raw": 0.13469741883567712,
      "mean_predicted_risk_bridge": 0.17887973922491202,
      "mean_predicted_risk_raw": 0.18013644676904442,
      "n": 152,
      "n_evaluable": 120,
      "pattern": "111",
      "supported_pattern": true
    }
  ],
  "ranking": {
    "bridge_risk_recomputed_exactly": true,
    "formula_monotone_beta_positive": true,
    "risk_rank_preserved_exact": true,
    "score_rank_preserved_exact": true
  },
  "raw_v1r_confirmation_reference": {
    "calibration_slope_24m": 1.5012234930948178,
    "citl_24m": 0.11648189899363745,
    "coverage": 1.0,
    "ipcw_brier_24m": 0.13124573097600542
  },
  "raw_v1r_vs_bridge": {
    "abs_citl_error_change": 0.004193869266130662,
    "abs_slope_error_change": 0.16781503882198923,
    "calibration_slope_bridge": 1.6781502918245472,
    "calibration_slope_raw": 1.510335253002558,
    "citl_bridge": 0.16094441769005133,
    "citl_raw": 0.15675054842392067,
    "delta_calibration_slope": 0.16781503882198923,
    "delta_citl": 0.004193869266130662,
    "delta_ipcw_brier": 0.0010845289567504302,
    "events_evaluable": 26,
    "ipcw_brier_bridge": 0.13578194779242755,
    "ipcw_brier_raw": 0.13469741883567712,
    "mean_predicted_risk_bridge": 0.17887973922491202,
    "mean_predicted_risk_raw": 0.18013644676904442,
    "n_evaluable": 120
  },
  "safety": {
    "citl_absolute_error_improved": false,
    "coverage_preserved": true,
    "development_safe_candidate_reused_without_reselection": true,
    "locked_secondary_validation_pass": false,
    "passes_global_brier_gate": false,
    "passes_supported_pattern_gate": true,
    "rank_preserved_risk": true,
    "rank_preserved_score": true,
    "slope_absolute_error_improved": false
  },
  "schema_version": "0.1",
  "stage_id": "U5R8_V1R_BETA09_LOGLOSS_BRIDGE_LOCKED_POST_UNSEAL_VALIDATION",
  "worst_supported_pattern_brier_regret": 0.0010845289567504302
}
```

This readout does not establish clinical utility, deployment readiness, external calibration, or transportability. It is secondary validation evidence for the already frozen development bridge.
