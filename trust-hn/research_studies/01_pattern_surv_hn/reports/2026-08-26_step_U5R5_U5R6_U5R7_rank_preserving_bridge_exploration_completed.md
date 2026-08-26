# 2026-08-26 ? U5R5/U5R6 rank-preserving bridge exploration and U5R7 candidate diagnostic

## Objective

The previous U5R4 candidate was usable but its calibration movement was modest. This step explored whether a strictly rank-preserving global bridge could reduce the IPCW-Brier cost while producing a clearer improvement in CITL and calibration slope.

All work remained development-only. The runner read only repeated nested development OOF predictions, did not read confirmation outcomes, did not refit on confirmation, did not alter V1R predictions, and did not write patient-level tracked outputs.

## Exploration designs

### U5R5: fixed-slope global grid

A positive global slope was fixed over:

```text
0.800, 0.825, 0.850, 0.875, 0.900, 0.925, 0.950, 0.975, 1.000, 1.025
```

For every held-out fold, the intercept was fitted on the other development folds by IPCW-Brier minimization. Every candidate was strictly monotone and preserved ranking.

The only candidate meeting the exploratory Pareto screen (Brier delta <= +0.0005, supported-pattern regret <= +0.005, CITL improvement, slope improvement, ranking preservation) was fixed beta 0.950 under the Brier-intercept objective.

### U5R6: intercept-objective refinement

To seek a better balance, beta values 0.900, 0.925, 0.950, and 0.975 were combined with five intercept objectives: IPCW-Brier, weighted log-loss, and 25/50/75% convex mixtures. This produced multiple Pareto candidates. The strongest low-Brier calibration-direction candidate was:

```text
beta = 0.900
intercept objective = weighted log-loss
candidate = beta_0.900_logloss
```

This selection is explicitly post-hoc exploratory and is not a confirmatory claim.

## U5R7 fixed-candidate diagnostic

U5R7 froze `beta_0.900_logloss` and reran it independently using 5 seeds ? 5 outer folds. The transformation is:

$$x_{candidate}=\alpha_{logloss}+0.90x_{raw},\qquad p_{candidate}=\sigma(x_{candidate}).$$

The slope is positive and global-only, so ranking is preserved exactly within each held-out fold.

Development cohort: 610 patients, 173 events; 2,460 IPCW-evaluable rows and 415 evaluable events.

| Metric | Raw V1R | U5R7 candidate | Change |
|---|---:|---:|---:|
| IPCW Brier24 | 0.126637 | 0.126784 | +0.000147 |
| CITL | +0.011680 | -0.003796 | absolute error change -0.007884 |
| Calibration slope | 0.825887 | 0.881552 | absolute error change -0.055665 |
| Worst supported-pattern Brier regret | ? | +0.004176 | boundary +0.005 |
| Coverage | 100% | 100% | preserved |
| Ranking | ? | preserved | all held-out folds |

Compared with U5R4, the U5R7 development result has a smaller Brier increase (+0.000147 vs +0.000198), a stronger absolute CITL improvement (?0.007884 vs ?0.005858), and a stronger calibration-slope improvement (?0.055665 vs ?0.003408 in absolute slope error). The comparison is exploratory and development-only.

All U5R7 safety gates passed. The deterministic rerun produced identical aggregate and artifact hashes.

## Interpretation and boundary

U5R7 is currently the strongest development-safe candidate found in this bridge exploration, but it is not a confirmed bridge. Raw V1R remains the retained backbone. The result does not establish confirmation performance, absolute-risk validity, clinical utility, router utility, or deployment readiness.

The positive-results manuscript folder remains unchanged. If the candidate is later independently approved and applied under a separately frozen prediction-seal protocol, the bridge can be described in Methods/Supplementary material as a conservative rank-preserving risk-scale layer. It should not yet replace the core V0 ? V1R narrative.

## Artifacts

- U5R5 protocol: `core_backbone/U5R5_V1R_fixed_slope_intercept_bridge_exploration/frozen_fixed_slope_intercept_bridge_exploration_protocol.yaml`
- U5R5 runner: `scripts/run_v1r_fixed_slope_intercept_bridge_exploration.py`
- U5R6 protocol: `core_backbone/U5R6_V1R_citl_slope_balanced_bridge_exploration/frozen_citl_slope_balanced_bridge_exploration_protocol.yaml`
- U5R6 runner: `scripts/run_v1r_citl_slope_balanced_bridge_exploration.py`
- U5R7 protocol: `core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/frozen_beta09_logloss_bridge_candidate_protocol.yaml`
- U5R7 runner: `scripts/run_v1r_selected_beta09_logloss_bridge_diagnostic.py`
- U5R7 aggregate: `core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_aggregate_results.json`
- U5R7 audit: `audits/U5R7_beta09_logloss_bridge_candidate_audit.md`
