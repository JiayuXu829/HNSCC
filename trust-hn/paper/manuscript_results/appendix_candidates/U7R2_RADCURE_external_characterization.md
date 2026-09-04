# U7R2 RADCURE external characterization - appendix candidate

## Suggested subsection title

**External transportability characterization under a clinical/radiomics input contract**

## Results

The RADCURE held-out test split included 626 patients and 110 events. The explicitly adapted clinical/radiomics comparator set achieved complete coverage for all evaluated patients:

| Comparator | IPCW Brier (lower better) | Uno C (higher better) | 24-month AUC (higher better) | Harrell C (higher better) | CITL (closer to 0 better) | Calibration slope (closer to 1 better) |
|---|---:|---:|---:|---:|---:|---:|
| C1 | 0.095801 | 0.806595 | 0.819376 | 0.795924 | -0.097110 | 1.950857 |
| C2 | 0.090683 | 0.806744 | 0.818182 | 0.797862 | -0.044444 | 1.139466 |
| C3 | 0.098469 | 0.771260 | 0.780742 | 0.761632 | -0.099603 | 1.268349 |
| C4 | 0.097403 | 0.779243 | 0.787882 | 0.768812 | -0.074520 | 1.471544 |

## Suggested interpretation

RADCURE provided a useful transportability characterization for an adapted clinical/radiomics comparator set, with complete coverage and generally strong discrimination. The results are descriptive and exploratory: RADCURE does not reproduce the frozen current-V1R blood/ICD/TMA input contract, its outcome was previously consumed, and the held-out test split is not a newly acquired outcome-untouched cohort. Accordingly, these findings do not constitute formal external validation of current V1R, its fixed bridge, or a router.

## Reporting boundary

This material should remain outside the core V1R confirmation claim and should not be copied into `V1R_positive/`. It may be used as an appendix candidate or as a separately labelled transportability-characterization subsection. No RADCURE outcome may be used to tune V1R, the bridge, the router, thresholds, or safety gates.

## Source of truth

- `trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U7R2_RADCURE_external_characterization/u7r2_radcure_external_characterization_aggregate_results.json`
- `trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U7R2_RADCURE_external_characterization/u7r2_radcure_external_characterization_audit.md`
