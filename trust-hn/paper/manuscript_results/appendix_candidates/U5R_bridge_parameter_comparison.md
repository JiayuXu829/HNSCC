# Appendix candidate material: U5R bridge parameter comparison

This appendix-candidate file contains aggregate-only comparisons from U5R5 and U5R6. It is not a primary-result table. All candidates were development-only and cross-fitted; no confirmation outcomes were used for candidate selection. `True` in `exploratory_screen_pass` means the candidate passed the exploratory global Brier, supported-pattern, CITL, slope and ranking gates.

## Candidate grid

| Stage | Candidate | beta | Intercept objective | delta Brier24 | CITL candidate | CITL abs-error change | Slope candidate | Slope abs-error change | Worst pattern regret | Screen pass |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| U5R5 | `fixed_beta_0.800` | 0.800 | brier | +0.000088 | -0.030639 | +0.018958 | 0.986353 | -0.160466 | +0.007045 | False |
| U5R5 | `fixed_beta_0.825` | 0.825 | brier | +0.000111 | -0.027246 | +0.015565 | 0.957073 | -0.131186 | +0.006383 | False |
| U5R5 | `fixed_beta_0.850` | 0.850 | brier | +0.000145 | -0.023689 | +0.012009 | 0.929469 | -0.103582 | +0.005747 | False |
| U5R5 | `fixed_beta_0.875` | 0.875 | brier | +0.000188 | -0.019973 | +0.008293 | 0.903401 | -0.077514 | +0.005138 | False |
| U5R5 | `fixed_beta_0.900` | 0.900 | brier | +0.000239 | -0.016098 | +0.004418 | 0.878744 | -0.052857 | +0.004554 | False |
| U5R5 | `fixed_beta_0.925` | 0.925 | brier | +0.000300 | -0.012066 | +0.000386 | 0.855387 | -0.029500 | +0.003996 | False |
| U5R5 | `fixed_beta_0.950` | 0.950 | brier | +0.000369 | -0.007879 | -0.003801 | 0.833228 | -0.007342 | +0.003464 | True |
| U5R5 | `fixed_beta_0.975` | 0.975 | brier | +0.000446 | -0.003538 | -0.008143 | 0.812179 | +0.013708 | +0.002958 | False |
| U5R5 | `fixed_beta_1.000` | 1.000 | brier | +0.000531 | +0.000958 | -0.010723 | 0.792155 | +0.033731 | +0.002477 | False |
| U5R5 | `fixed_beta_1.025` | 1.025 | brier | +0.000623 | +0.005606 | -0.006074 | 0.773085 | +0.052802 | +0.002600 | False |
| U5R6 | `beta_0.900_brier` | 0.900 | brier | +0.000239 | -0.016098 | +0.004418 | 0.878744 | -0.052857 | +0.004554 | False |
| U5R6 | `beta_0.900_mix_25` | 0.900 | mix_25 | +0.000181 | -0.009863 | -0.001818 | 0.881237 | -0.055351 | +0.004304 | True |
| U5R6 | `beta_0.900_mix_50` | 0.900 | mix_50 | +0.000162 | -0.006760 | -0.004920 | 0.881570 | -0.055683 | +0.004231 | True |
| U5R6 | `beta_0.900_mix_75` | 0.900 | mix_75 | +0.000152 | -0.004962 | -0.006719 | 0.881593 | -0.055706 | +0.004196 | True |
| U5R6 | `beta_0.900_logloss` | 0.900 | logloss | +0.000147 | -0.003796 | -0.007884 | 0.881552 | -0.055665 | +0.004176 | True |
| U5R6 | `beta_0.925_brier` | 0.925 | brier | +0.000300 | -0.012066 | +0.000386 | 0.855387 | -0.029500 | +0.003996 | False |
| U5R6 | `beta_0.925_mix_25` | 0.925 | mix_25 | +0.000237 | -0.008068 | -0.003612 | 0.857931 | -0.032045 | +0.003593 | True |
| U5R6 | `beta_0.925_mix_50` | 0.925 | mix_50 | +0.000216 | -0.005933 | -0.005748 | 0.858287 | -0.032400 | +0.003456 | True |
| U5R6 | `beta_0.925_mix_75` | 0.925 | mix_75 | +0.000206 | -0.004675 | -0.007006 | 0.858326 | -0.032440 | +0.003386 | True |
| U5R6 | `beta_0.925_logloss` | 0.925 | logloss | +0.000199 | -0.003854 | -0.007826 | 0.858297 | -0.032411 | +0.003343 | True |
| U5R6 | `beta_0.950_brier` | 0.950 | brier | +0.000369 | -0.007879 | -0.003801 | 0.833228 | -0.007342 | +0.003464 | True |
| U5R6 | `beta_0.950_mix_25` | 0.950 | mix_25 | +0.000301 | -0.006209 | -0.005471 | 0.835818 | -0.009931 | +0.002902 | True |
| U5R6 | `beta_0.950_mix_50` | 0.950 | mix_50 | +0.000279 | -0.005075 | -0.006605 | 0.836194 | -0.010307 | +0.002699 | True |
| U5R6 | `beta_0.950_mix_75` | 0.950 | mix_75 | +0.000267 | -0.004376 | -0.007304 | 0.836249 | -0.010362 | +0.002593 | True |
| U5R6 | `beta_0.950_logloss` | 0.950 | logloss | +0.000261 | -0.003912 | -0.007769 | 0.836231 | -0.010344 | +0.002527 | True |
| U5R6 | `beta_0.975_brier` | 0.975 | brier | +0.000446 | -0.003538 | -0.008143 | 0.812179 | +0.013708 | +0.002958 | False |
| U5R6 | `beta_0.975_mix_25` | 0.975 | mix_25 | +0.000374 | -0.004287 | -0.007393 | 0.814808 | +0.011079 | +0.002231 | False |
| U5R6 | `beta_0.975_mix_50` | 0.975 | mix_50 | +0.000350 | -0.004188 | -0.007492 | 0.815203 | +0.010684 | +0.001960 | False |
| U5R6 | `beta_0.975_mix_75` | 0.975 | mix_75 | +0.000338 | -0.004066 | -0.007615 | 0.815272 | +0.010615 | +0.001817 | False |
| U5R6 | `beta_0.975_logloss` | 0.975 | logloss | +0.000331 | -0.003969 | -0.007711 | 0.815263 | +0.010623 | +0.001727 | False |

## Reading rules

- Lower IPCW Brier is better; a positive delta is a penalty relative to raw V1R.
- CITL is better when closer to 0; a negative absolute-error change means improvement.
- Calibration slope is better when closer to 1; a negative absolute-error change means improvement.
- Positive beta preserves the patient ranking exactly; it does not guarantee absolute-risk calibration.
- U5R7 (`beta_0.900_logloss`) is the selected positive development candidate and is carried into the main manuscript as a development-only bridge result.
- U5R5/U5R6 grid rows remain appendix candidates and should not be described as confirmation evidence.

## Source files

- `research_studies/01_pattern_surv_hn/core_backbone/U5R5_V1R_fixed_slope_intercept_bridge_exploration/fixed_slope_intercept_aggregate_results.csv`
- `research_studies/01_pattern_surv_hn/core_backbone/U5R5_V1R_fixed_slope_intercept_bridge_exploration/fixed_slope_intercept_safety_screen.csv`
- `research_studies/01_pattern_surv_hn/core_backbone/U5R6_V1R_citl_slope_balanced_bridge_exploration/citl_slope_balanced_aggregate_results.csv`
- `research_studies/01_pattern_surv_hn/core_backbone/U5R6_V1R_citl_slope_balanced_bridge_exploration/citl_slope_balanced_safety_screen.csv`
- `research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_aggregate_results.json`
