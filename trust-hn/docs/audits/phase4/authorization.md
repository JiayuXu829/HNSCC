# Phase 4 authorization and boundary

**Authorized by user:** 2026-08-07  
**Authorized phase:** Phase 4 TRUST-HN core development  
**Phase 5 authorized:** No  
**Sealed/external outcome access authorized:** No

## Authorized work

- clinical-anchor plus stacked residual modality learner (B6);
- three outcome-free OOD detectors: shrinkage Mahalanobis, kNN distance, and Isolation Forest;
- lightweight bootstrap uncertainty ensembles;
- prespecified equal-weight reliability scores;
- AUGMENT/FALLBACK/ABSTAIN decisions (B7);
- calibration-derived 80% and 90% non-abstention/augmentation eligibility thresholds;
- patient-level decision traces in Git-ignored files;
- aggregate development/calibration metrics and risk-coverage diagnostics;
- synthetic shift tests.

## Conditional study scope

- HANCOCK development train/calibration: authorized.
- TCGA-HNSC development train/calibration: authorized.
- RADCURE clinical anchor may be retained for reference, but B6/B7 remain blocked because the ORCESTRA RDS modality structure is not validated.

## Explicit prohibitions

- no RADCURE challenge-test outcomes;
- no HANCOCK OOD-test outcomes;
- no GSE65858 or GSE41613 outcomes;
- no Phase 5 stress-test/ablation campaign;
- no analysis freeze or final threshold lock for external use;
- no final locked/external performance claim.

Calibration outcomes may be used only to report development-stage performance. Reliability rank mappings and coverage thresholds are selected from calibration reliability indicators without optimizing outcome performance.
