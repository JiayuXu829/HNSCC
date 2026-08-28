# U6 cross-fitted value-router development exploration completed

**Date:** 2026-08-27  
**Status:** completed; exploratory only, no confirmation/deployment claim

## Question

Can patient-level incremental value be predicted from development-only V1R/V0 outputs so that the method uses V1R when it is likely safer and falls back to the clinical anchor otherwise?

## Design

A standardized logistic value router was trained using only repeated development OOF predictions. The label was 1 when V1R had lower IPCW-observable individual squared error than V0. All repeated rows for a patient were kept in the same held-out router fold using five-fold `StratifiedGroupKFold`. Censoring Kaplan–Meier weights were estimated inside each training fold. The router used only `FUSE` (raw V1R) and `FALLBACK` (V0); it did not use the bridge, did not abstain, and did not delete patients. Thresholds 0.40, 0.50 and 0.60 were frozen and all reported.

## Results

| Policy | FUSE rate | IPCW Brier | Δ vs V0 | Δ vs raw V1R |
|---|---:|---:|---:|---:|
| Raw V1R reference | 100.0% | 0.124561 | −0.000408 | reference |
| V0 reference | 0.0% | 0.124968 | reference | +0.000408 |
| q ≥ 0.40 → FUSE else FALLBACK | 61.2% | 0.124619 | −0.000349 | +0.000059 |
| q ≥ 0.50 → FUSE else FALLBACK | 58.1% | 0.124619 | −0.000350 | +0.000058 |
| q ≥ 0.60 → FUSE else FALLBACK | 56.2% | 0.124622 | −0.000346 | +0.000062 |

All policies retained 100% coverage. In a 2,000-replicate patient-cluster bootstrap, the 95% intervals for router-minus-V0 Brier crossed zero for all three thresholds (lower/upper bounds approximately −0.00159 to +0.00093).

## Interpretation

The cross-fitted router produced a small, consistent point-estimate improvement over V0 across prespecified thresholds, suggesting that incremental value is not entirely unstructured and that fallback can protect against some harmful V1R updates. However, the gain is not statistically separated from zero in the development cluster bootstrap and is slightly worse than raw V1R at the point estimate. Therefore this is a **hypothesis-generating router signal**, not a confirmed router result. It should not be added to the paper's core efficacy narrative or treated as deployment-ready.

## Governance

No official-test or external outcome was read. The bridge was not refit; raw V1R predictions were not modified; no patient was removed; and no threshold was selected after seeing held-out results.

## Artifacts

- `core_backbone/U6_cross_fitted_value_router_exploration/frozen_u6_router_protocol.yaml`
- `core_backbone/U6_cross_fitted_value_router_exploration/u6_router_aggregate_results.json`
- `core_backbone/U6_cross_fitted_value_router_exploration/u6_router_policy_results.csv`
- `core_backbone/U6_cross_fitted_value_router_exploration/u6_router_bootstrap_results.csv`
- `core_backbone/U6_cross_fitted_value_router_exploration/u6_router_fold_results.csv`
- `core_backbone/U6_cross_fitted_value_router_exploration/u6_router_audit.md`
- `core_backbone/U6_cross_fitted_value_router_exploration/u6_router_hashes.json`
- `scripts/run_u6_cross_fitted_value_router_exploration.py`
