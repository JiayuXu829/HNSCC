# Phase 4 leakage and governance audit

## Authorized scope

Phase 4 used only frozen development train/calibration rows from HANCOCK and
TCGA-HNSC. RADCURE B6/B7 remained blocked because the ORCESTRA RDS modality
structure has not been validated. No sealed or external outcome was loaded.

## Leakage controls

- Outer OOF preprocessing, variance selection, OOD fitting, models, and bootstrap
  resampling used outer-training rows only.
- B6 training used inner cross-fitted B2 anchor scores; outer-evaluation and
  calibration outcomes never entered B6 fitting.
- The full-training calibration path fit preprocessing, models, OOD detectors, and
  20-member uncertainty ensembles on development training rows only.
- Reliability components were transformed with calibration-feature empirical ranks.
- Clinical and modality thresholds were prespecified calibration reliability
  quantiles; calibration outcomes were not used to select thresholds.
- Perturbation sensitivity used deterministic outcome-independent row permutations.
- Patient decisions were written only under Git-ignored `results/predictions/phase4/`.
- Intended tracked outputs were checked for identifier headers and known native-ID patterns.

## Run accounting

- Complete study/seed runs: 10
- Failed study/seed runs: 0
- Governance-blocked entries: 1

## Boundary

This is development-stage evidence, not locked or external validation. Phase 5
stress tests, subgroup campaigns, final analysis freeze, and Phase 6 evaluation
remain unauthorized.
