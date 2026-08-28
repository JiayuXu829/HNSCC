# U5R10 fixed bridge external secondary characterization audit

- Protocol frozen before execution.
- U5R7 alpha/beta were read from the pre-existing 25-fold development artifact; no external refit or candidate selection was performed.
- Both available GEO cohorts were reported in full.
- Outcomes were already consumed in historical Phase 6; this is locked post-unseal characterization, not pristine confirmation.
- GEO files contain legacy Phase 6 B6 predictions, whose definition is not proven identical to current PATTERN-Surv-HN V1R.
- The transform is strictly monotone; ranking and coverage were checked.

## Claim boundary

The results support a reproducible calibration direction for the fixed bridge on legacy B6 transport characterization only. They do not establish current V1R bridge external validity. A genuine V1R confirmation requires a new outcome-untouched cohort and pre-outcome execution of the frozen V1R prediction contract.

## Aggregate results

```text
  cohort   n  events  coverage_raw  coverage_bridge       base_definition     alpha  beta  rank_preserved_risk  rank_preserved_score  ipcw_brier_raw  ipcw_brier_bridge  delta_ipcw_brier  citl_raw  citl_bridge  delta_citl  abs_citl_error_change  calibration_slope_raw  calibration_slope_bridge  delta_calibration_slope  abs_slope_error_change  n_evaluable  events_evaluable  mean_predicted_risk_raw  mean_predicted_risk_bridge  passes_brier_nonharm_gate_0.0005  calibration_citl_improved  calibration_slope_improved  all_directional_checks_pass
GSE65858 244      78           1.0              1.0 legacy_phase6_B6_risk -0.145034   0.9                 True                  True        0.224769           0.209071         -0.015697 -1.331568    -1.181249    0.150318              -0.150318               0.608704                  0.676338                 0.067634               -0.067634          211                46                 0.451905                    0.424126                              True                       True                        True                         True
GSE41613  97      51           1.0              1.0 legacy_phase6_B6_risk -0.145034   0.9                 True                  True        0.204267           0.197910         -0.006357 -0.571285    -0.456782    0.114503              -0.114503               0.791168                  0.879076                 0.087908               -0.087908           97                31                 0.397609                    0.374891                              True                       True                        True                         True
```
