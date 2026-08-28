# U6 cross-fitted value-router exploration audit

- The router was trained only from development repeated OOF predictions.
- Patient IDs were used only as grouping keys; all repeated rows for a patient stayed in one held-out fold.
- The target label was formed only on IPCW-observable development rows and indicated whether V1R had lower individual squared error than V0.
- Censoring Kaplan-Meier weights were fitted separately inside each router training fold.
- All three thresholds (0.40, 0.50, 0.60) were prespecified and reported; no threshold was selected after held-out readout.
- No confirmation or external outcomes were read, no bridge was refit, no raw V1R prediction was changed, and no patient was deleted.

## Claim boundary

This stage is a development-only hypothesis-generating router experiment. It can inform whether patient-level incremental value is predictable, but it is not external validation, confirmation, clinical utility, or deployment evidence.

## Results

See `u6_router_policy_results.csv` and `u6_router_aggregate_results.json`. The router always falls back to V0 rather than abstaining, so coverage is 100% by construction. A favorable development OOF Brier result, if present, must be treated as exploratory because router labels and model fitting use development outcomes under cross-fitting.
