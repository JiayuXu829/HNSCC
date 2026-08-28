# 2026-08-27 — U5R9 frozen bridge panel post-unseal characterization completed

## Objective and boundary

U5R9 evaluated the complete pre-existing frozen bridge panel on HANCOCK OOD TEST without using confirmation outcomes to select, refit, or tune a candidate. The panel contained raw V1R, the conservative U5R4 bounded global bridge, and the U5R7 beta=0.90 log-loss bridge. The panel and parameter-aggregation rules were frozen before execution.

The U2/V1R confirmation outcomes had already been unsealed on August 26, 2026. Consequently, U5R9 is a **locked secondary post-unseal exploratory characterization**, not a new pristine outcome-untouched confirmation. No candidate is promoted or selected for deployment from this stage.

## Frozen transformations

For U5R4, the 25 development fold records were reduced to a single fixed monotone transform by arithmetic averaging of the already frozen effective intercept and slope:

\[
x_{U5R4} = -0.02863319431659357 + 0.978121925546798\,x_{raw}.
\]

For U5R7:

\[
x_{U5R7} = -0.14503379856995471 + 0.90\,x_{raw}.
\]

For both bridges, \(p=\sigma(x)\), and raw V1R predictions were unchanged.

## Results

| Candidate | IPCW Brier24 | Δ Brier vs raw | CITL | Δ CITL | Calibration slope | Δ slope | Ranking | Coverage | All gates |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| Raw V1R | 0.134697 | 0.000000 | +0.156751 | 0.000000 | 1.510335 | 0.000000 | preserved | 100% | reference |
| U5R4 bounded global | 0.134868 | +0.000170 | +0.154789 | −0.001962 | 1.544118 | +0.033782 | exact preserved | 100% | fail: slope |
| U5R7 beta 0.90 log-loss | 0.135782 | +0.001085 | +0.160944 | +0.004194 | 1.678150 | +0.167815 | exact preserved | 100% | fail: Brier, CITL, slope |

The supported-pattern Brier regret was +0.000170 for U5R4 and +0.001085 for U5R7; both were below the predeclared +0.005 boundary. Both bridges retained 100% coverage and exact risk/score ordering because their slopes were positive.

In 2,000 event-stratified patient bootstrap replicates, U5R4 had mean Brier change +0.000179 (95% interval −0.000208 to +0.000540), mean CITL change −0.001975 (95% interval −0.005463 to +0.001612), and mean absolute slope-error change +0.034715 (95% interval −0.016934 to +0.056078; 1,958 finite replicates). U5R7 had mean Brier change +0.001105 (95% interval −0.000764 to +0.002890), mean CITL change +0.004230 (95% interval −0.011616 to +0.021739), and mean absolute slope-error change +0.172794 (95% interval +0.034124 to +0.274532; 1,959 finite replicates).

## Decision

U5R9 confirms a bounded safety pattern but not a deployable calibration bridge:

- The conservative U5R4 bridge remained within the global Brier and supported-pattern regret boundaries and improved point-estimate CITL modestly, but failed the prespecified calibration-slope improvement gate.
- The U5R7 bridge did not reproduce its development-only calibration gains and failed the global Brier, CITL, and slope gates.
- Both bridges preserved the intended structural properties: full coverage and exact ranking preservation.
- Raw V1R remains the only retained primary confirmation readout and the model backbone.

The scientifically useful next step is a genuinely independent outcome-untouched cohort validation with the bridge protocol frozen before outcome access. Repeatedly testing or tuning bridge parameters on HANCOCK OOD TEST is not authorized.

## Artifacts

- Protocol: `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/frozen_u5r9_bridge_panel_protocol.yaml`
- Runner: `scripts/run_v1r_frozen_bridge_panel_post_unseal_characterization.py`
- Aggregate results: `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/u5r9_bridge_panel_aggregate_results.json`
- Candidate results: `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/u5r9_bridge_panel_candidate_results.csv`
- Pattern results: `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/u5r9_bridge_panel_pattern_results.csv`
- Bootstrap results: `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/u5r9_bridge_panel_bootstrap_results.csv`
- Audit: `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/u5r9_bridge_panel_audit.md`
- Hash manifest: `core_backbone/U5R9_frozen_bridge_panel_post_unseal_characterization/u5r9_bridge_panel_hashes.json`

No patient-level outputs were copied into tracked research or paper-facing directories.
