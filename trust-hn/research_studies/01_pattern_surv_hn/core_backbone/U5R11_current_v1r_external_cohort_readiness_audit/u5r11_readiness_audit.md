# U5R11 current-V1R external cohort readiness audit

## Scope

This stage was executed on 2026-08-27 before any new outcome access. It is a feasibility/readiness experiment, not a performance evaluation. Only frozen protocol metadata and source manifests were inspected; no patient-level rows or outcome columns were read.

## Frozen eligibility for a formal confirmation

A candidate must provide the current PATTERN-Surv-HN V1R prediction contract: the postoperative clinical-pathological anchor plus the optional blood, ICD and TMA cell-density modalities. The current V1R model and the fixed bridge must be sealed before opening outcomes. Legacy B6 predictions cannot substitute for current V1R predictions.

## Result

No locally available cohort meets both requirements:

- HANCOCK OOD is compatible with current V1R, but its outcomes were already opened for the prior raw-V1R confirmation and subsequent bridge characterizations.
- RADCURE has clinical/radiomics artifacts but not the frozen V1R blood/ICD/TMA contract, and its outcomes were used historically.
- GSE65858 and GSE41613 have transcriptomic/legacy-B6 artifacts, not current V1R inputs or predictions; their outcomes were used historically.
- TCGA-HNSC has expression and clinical metadata but no current-V1R-compatible multimodal prediction artifact; untouched status was not certified in this audit.

Therefore, the count of certified outcome-untouched current-V1R-compatible cohorts is **zero**. No current-V1R bridge prediction or metric was generated, and no result is added to the positive manuscript-material directory.

## Claim boundary

This is not evidence that the bridge fails. It is evidence that the current local data inventory cannot support the requested formal confirmation without a new compatible cohort. The next valid experiment is cohort acquisition/designation, pre-outcome freezing of current-V1R prediction generation plus the fixed bridge and estimands, prediction sealing, and only then outcome evaluation.
