# U6R1 patient-level aggregation and reliability-aware router exploration completed

**Date:** 2026-08-28  
**Status:** completed; exploratory only, no confirmation/deployment claim

## Why this was the next experiment

U6 showed a small development-only signal for a patient-level FUSE/FALLBACK router, but the router was trained on repeated OOF rows and its point estimate was slightly worse than using raw V1R directly. The next bounded question was whether a more appropriate patient-level unit and pre-outcome prediction-instability features could reduce repeated-OOF noise and make the routing signal more stable.

## Design

- Source: development repeated OOF V1R predictions only; no official-test, confirmation or external outcomes were read.
- Unit of analysis: one row per patient (`native_id`), formed by averaging the five repeated OOF V0 and V1R risks.
- Router: five-fold patient-level cross-fitted balanced logistic regression, fixed `C=0.5`.
- Actions: `FUSE` uses the patient-aggregated raw V1R risk; `FALLBACK` uses the patient-aggregated V0 risk.
- Candidate feature sets were reported together:
  1. patient-aggregated core features;
  2. core features plus repeated-OOF prediction instability (`v0_risk_24m_sd`, `v1_risk_24m_sd`, `risk_delta_sd`).
- Thresholds 0.40, 0.50 and 0.60 were fixed before readout and all were reported.
- Censoring weights were estimated within each held-out training fold. All policies retained 100% coverage.

## Results

The patient-aggregated reference values were:

| Policy | IPCW Brier24 | Relative to V0 |
|---|---:|---:|
| V0 reference | 0.123927 | 0 |
| raw V1R reference | 0.122765 | −0.001162 |

For the reliability-augmented router:

| Threshold | FUSE rate | IPCW Brier24 | Δ vs V0 | Δ vs raw V1R | Rank concordance with raw V1R |
|---:|---:|---:|---:|---:|---:|
| 0.40 | 67.0% | 0.123648 | −0.000279 | +0.000883 | 0.946 |
| 0.50 | 54.8% | 0.123508 | −0.000419 | +0.000743 | 0.938 |
| 0.60 | 42.6% | 0.123421 | −0.000506 | +0.000657 | 0.929 |

The core-only router gave Δ Brier versus V0 from −0.000341 to −0.000416 across the three thresholds. The reliability-augmented version therefore produced the most favourable point estimate at threshold 0.60, but still remained worse than direct raw V1R.

In the 2,000-replicate patient bootstrap, the 95% interval for the best point estimate (reliability-augmented, threshold 0.60) was approximately −0.00162 to +0.00076 for router-minus-V0 Brier. The interval crossed zero. Router selection also did not preserve the exact global V1R ranking; rank concordance was reported descriptively rather than treated as a safety gate.

## Interpretation for the paper story

This experiment strengthens the methodological boundary rather than establishing a new confirmed method result:

> Aggregating repeated OOF predictions at the patient level and adding prediction-instability proxies made the exploratory router signal slightly more favourable against V0, but the gain remained uncertain and smaller than direct raw V1R. Selective routing therefore remains a promising but unconfirmed extension, not the paper's validated backbone.

The result supports the following narrative progression:

```text
clinical anchor → controlled V1R residual fusion → raw-V1R directional confirmation
             → calibration portability boundary → exploratory adaptive routing
```

The router should not be added to `paper/manuscript_results/V1R_positive/` or described as externally validated, clinically useful, ranking-preserving, or deployment-ready. Aggregate details are retained as appendix-candidate material only.

## Next valid step

The scientifically decisive next step remains a genuinely new current-V1R-compatible, outcome-untouched external cohort. Before outcome access, freeze the V1R prediction generator, any router candidate, estimands, bootstrap and exclusions; seal predictions and hashes; then evaluate without refit or threshold selection. Until such a cohort exists, further router tuning is development-only and cannot complete the external-validation portion of the manuscript story.

## Artifacts

- `core_backbone/U6R1_patient_level_router_aggregation_exploration/`
- `scripts/run_u6r1_patient_level_router_aggregation_exploration.py`
- `paper/manuscript_results/appendix_candidates/U6R1_patient_level_router_exploration.md`
