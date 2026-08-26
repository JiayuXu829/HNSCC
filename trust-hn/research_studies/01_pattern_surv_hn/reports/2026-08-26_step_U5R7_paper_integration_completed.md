# 2026-08-26 ? U5R7 bridge paper integration completed

## Decision

The U5R7 `beta_0.900_logloss` candidate is finalized as a **development-only, cross-fitted calibration bridge result** for manuscript use. The paper-facing positive-results directory and appendix-candidate directory are now updated. Raw V1R remains the locked confirmation output.

## Result carried into the paper

```text
candidate                               beta_0.900_logloss
formula                                 x_bridge = alpha_logloss + 0.90*x_raw
intercept objective                     weighted log-loss
scope                                   global-only, no pattern-specific parameters
bridge-evaluable rows / events          2460 / 415
raw IPCW Brier24                        0.126637
U5R7 IPCW Brier24                       0.126784
delta IPCW Brier24                     +0.000147  PASS (gate +0.0005)
raw CITL                                +0.011680
U5R7 CITL                               -0.003796
absolute CITL error change              -0.007884
raw calibration slope                   0.825887
U5R7 calibration slope                  0.881552
absolute slope error change             -0.055665
worst supported-pattern regret          +0.004176  PASS (gate +0.005)
coverage                                100% preserved
ranking                                 preserved in all held-out folds
```

## Manuscript integration

- Abstract: U5R7 is reported as a separate development calibration diagnostic.
- Results: a dedicated bridge subsection reports the formula, metrics, gates and interpretation.
- Methods: bridge fitting and monotonicity are specified; confirmation outcomes are explicitly excluded.
- Discussion: the story is separated into V1R fusion, U5R7 development calibration, and raw-V1R confirmation.
- Supplement: U5R7 is reported in a separate supplementary table and method section.
- Figure specification: U5R7 is a completed development module; bridge-to-confirmation remains pending a separately frozen protocol.

## Materials written

### Publication-facing positive folder

`paper/manuscript_results/V1R_positive/`

- `v1r_bridge_positive_results.csv/json`
- `v1r_bridge_methods_and_formulae.md`
- `v1r_bridge_paper_integration_notes.md`
- updated README, claims, narrative map, confirmation claims and framework specification

### Appendix candidates

`paper/manuscript_results/appendix_candidates/`

- `U5R_bridge_parameter_comparison.csv`
- `U5R_bridge_parameter_comparison.md`
- `U5R_bridge_exploration_summary.md`

The appendix contains aggregate-only U5R5/U5R6 parameter comparisons; patient-level outputs were not copied.

## Claim boundary

This integration does not claim that U5R7 has been evaluated in the confirmation cohort. It does not establish external calibration, transportability, clinical utility or deployment readiness. Any confirmation bridge application requires a separately frozen and approved protocol.
