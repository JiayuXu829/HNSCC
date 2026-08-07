# Phase 3 leakage and governance audit

**Scope:** development-only B0-B5/M0/N0 baselines. Phase 4 and sealed/external
 evaluation were not authorized.

## Controls verified by implementation

- Only eligible, endpoint-usable, frozen train/calibration rows are loaded.
- OOF folds use event-stratified patient-level indices inside frozen training data.
- Imputation, encoding, scaling, and TCGA top-500 selection fit within each fold.
- Calibration rows never fit preprocessing, selection, or model parameters.
- Censoring before 24 months receives zero IPCW weight, not a survivor label.
- N0 permutations are outcome-independent and partition-local.
- Patient predictions stay in Git-ignored `results/predictions/phase3/`.
- Tracked metrics, figures, audit, and receipt contain aggregate data only.
- Sealed RADCURE/HANCOCK and external GEO outcomes were not loaded.
- Phase 4 learners, gates, decisions, and threshold optimization were not run.

## Run accounting

- Complete study/model/seed runs: 105
- Complete runs carrying fit diagnostics: 10
- Failed study/model/seed runs: 0
- Governance-blocked model entries: 3
- Aggregate metric rows: 210

## Persistent blocker

RADCURE B4/B5/N0 remain NO-GO because the ORCESTRA RDS structure has not been
validated with R/Rscript or a validated parser.
