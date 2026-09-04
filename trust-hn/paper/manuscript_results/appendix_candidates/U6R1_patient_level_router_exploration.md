# U6R1 patient-level router exploration — appendix candidate

**Status:** development-only exploratory material; not a confirmed result.

Repeated V1R OOF predictions were averaged to one row per patient, then a five-fold patient-level cross-fitted logistic router selected raw V1R (`FUSE`) or V0 (`FALLBACK`). A reliability-augmented feature set added the across-repetition SD of V0 risk, V1R risk and risk delta. Thresholds were fixed at 0.40, 0.50 and 0.60.

| Policy | FUSE rate | IPCW Brier24 | Δ vs V0 | Δ vs raw V1R | Rank concordance vs raw V1R |
|---|---:|---:|---:|---:|---:|
| V0 | 0.0% | 0.123927 | 0 | +0.001162 | 0.867 |
| raw V1R | 100.0% | 0.122765 | −0.001162 | 0 | 1.000 |
| core router, q≥0.40 | 66.1% | 0.123545 | −0.000382 | +0.000780 | 0.945 |
| core router, q≥0.50 | 54.1% | 0.123511 | −0.000416 | +0.000746 | 0.939 |
| core router, q≥0.60 | 40.3% | 0.123585 | −0.000341 | +0.000821 | 0.928 |
| reliability router, q≥0.40 | 67.0% | 0.123648 | −0.000279 | +0.000883 | 0.946 |
| reliability router, q≥0.50 | 54.8% | 0.123508 | −0.000419 | +0.000743 | 0.938 |
| reliability router, q≥0.60 | 42.6% | 0.123421 | −0.000506 | +0.000657 | 0.929 |

Best point estimate: reliability router q≥0.60, Δ Brier vs V0 = −0.000506; 2,000-replicate patient bootstrap 95% interval approximately −0.00162 to +0.00076, crossing zero. The router remained worse than raw V1R at the point estimate and did not preserve exact global ranking.

**Claim boundary:** do not place this result in the positive-results source of truth; do not call it router confirmation, external validation, clinical utility, ranking preservation or deployment evidence.

Source artifacts: `research_studies/01_pattern_surv_hn/core_backbone/U6R1_patient_level_router_aggregation_exploration/`.
