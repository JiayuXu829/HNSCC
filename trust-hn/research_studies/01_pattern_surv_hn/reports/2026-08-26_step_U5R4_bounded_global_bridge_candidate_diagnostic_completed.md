# 2026-08-26 ? U5R4 bounded global bridge candidate diagnostic completed

## Stage

This step followed the U5R1?U5R3 development-only exploration screen. U5R4 froze one candidate before its independent cross-fitted diagnostic rerun: `bounded_global_full_g0.25`.

The purpose was to determine whether a conservative bridge can be made technically usable without damaging the V1R backbone's ranking or development discrimination signal.

## Design

The candidate uses a global logit-affine bridge fitted on the other development folds only. The slope is constrained to `[0.75, 1.25]`, and the fitted transformation is shrunk 25% toward identity. No pattern-specific parameters, router logic, fallback changes, clinical actions, or confirmation outcomes were used.

$$p_{bridge}=\sigma\left[x_{raw}+0.25\left\{\alpha_{Brier}+(\beta_{Brier}-1)x_{raw}\right\}\right].$$

This is a calibration/risk-scale layer, not a new V1R backbone. Its effective slope remains positive, so the V1R ordering is unchanged.

## Exploration context

- **U5R1:** conservative global candidates; the bounded global family was the most promising rank-preserving direction.
- **U5R2:** V0-anchor blending improved some Brier/slope summaries but changed patient ranking, so it is not a calibration-only bridge and was not promoted.
- **U5R3:** direct Brier-optimized monotone shrinkage remained safe but did not improve on the bounded global candidate as a development direction.
- **U5R4:** fixed-candidate independent rerun of the bounded global bridge.

These were post-hoc exploratory rescue analyses. None is a confirmatory result.

## U5R4 result

Development cohort: 610 patients, 173 events; 2,460 IPCW-evaluable rows and 415 evaluable events across 5 seeds ? 5 outer folds.

| Metric | Raw V1R | U5R4 bridge | Change / interpretation |
|---|---:|---:|---|
| IPCW Brier24 | 0.126637 | 0.126834 | +0.000198; below +0.005 boundary |
| CITL | +0.011680 | +0.005823 | absolute error change -0.005858 |
| Calibration slope | 0.825887 | 0.829295 | absolute error change -0.003408 |
| Evaluated rows | 2460 | 2460 | unchanged |
| Evaluated events | 415 | 415 | unchanged |
| Ranking | preserved | preserved | strict monotonicity confirmed in all folds |
| Worst supported-pattern Brier regret | reference | +0.000758 | below +0.020 boundary |

All frozen development safety gates passed. The Brier increase is small relative to the no-harm boundary (+0.005), while CITL and slope move in the desired direction.

## What this means for the paper

This result should not be added to `paper/manuscript_results/V1R_positive/` yet. If later independently approved and confirmed, it can support a Methods/Supplementary description of a conservative risk-scale stabilization layer. At this stage it belongs in the staged development and limitations record, not the positive core claim set.

The paper's core claim remains the V0 ? V1R residual-shrinkage story. U5R4 adds a technically plausible bridge option around that backbone; it does not establish calibrated absolute-risk validity, clinical utility, router performance, or deployment readiness.

## Next allowed step

Independent researcher review of this frozen candidate, followed?only if approved?by a separate locked prediction-seal protocol for confirmation application. Confirmation outcomes must remain untouched until that protocol is frozen.

## Artifacts

- Protocol: `core_backbone/U5R4_V1R_bounded_global_bridge_candidate/frozen_bounded_global_bridge_candidate_protocol.yaml`
- Runner: `scripts/run_v1r_selected_bounded_bridge_diagnostic.py`
- Aggregate: `core_backbone/U5R4_V1R_bounded_global_bridge_candidate/selected_bridge_aggregate_results.json`
- Fold results: `core_backbone/U5R4_V1R_bounded_global_bridge_candidate/selected_bridge_fold_results.csv`
- Pattern results: `core_backbone/U5R4_V1R_bounded_global_bridge_candidate/selected_bridge_pattern_aggregate_results.csv`
- Audit: `audits/U5R4_bounded_global_bridge_candidate_audit.md`
