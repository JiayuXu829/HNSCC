# Phase 3 authorization and boundary

**Authorized by user:** 2026-08-07
**Authorized phase:** Phase 3 baseline models
**Phase 4 authorized:** No
**Sealed/external outcome access authorized:** No

## Interpretation of authorization

The Phase 3 authorization activates development-only baseline work under the recommendation issued at the Phase 2 gate:

- clinical baselines for RADCURE, HANCOCK, and TCGA-HNSC;
- available structured-modality baselines for HANCOCK;
- expression baselines for TCGA-HNSC;
- B0-B5 implementation, OOF predictions, IPCW/Brier/C-index/AUC/calibration/DCA metrics;
- missingness-only and outcome-independent permuted-modality controls;
- training and dedicated calibration partitions only.

RADCURE radiomics remain blocked because the ORCESTRA RDS object has not undergone a validated structural audit. This authorization does not permit bypassing that blocker.

## Explicit prohibitions

- no RADCURE challenge-test outcome use;
- no HANCOCK OOD-test outcome use;
- no GSE65858 or GSE41613 outcome use;
- no Phase 4 residual learner or reliability gate;
- no calibration/gate threshold selection using sealed or external cohorts;
- no final locked/external performance claim.
