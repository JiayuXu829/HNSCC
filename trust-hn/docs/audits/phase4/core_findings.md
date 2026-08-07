# Phase 4 core development findings

These findings are development/calibration observations only. They are not sealed or external performance claims.

## Mean calibration performance over prespecified seeds

| Study | Model | IPCW Brier | Harrell C | 24-month AUC |
|---|---|---:|---:|---:|
| HANCOCK | B2 | 0.1460 | 0.6328 | 0.6901 |
| HANCOCK | B5 | 0.1276 | 0.6948 | 0.7873 |
| HANCOCK | B6 | 0.1288 | 0.6756 | 0.7692 |
| TCGA-HNSC | B2 | 0.2422 | 0.4898 | 0.4368 |
| TCGA-HNSC | B5 | 0.2482 | 0.6104 | 0.6001 |
| TCGA-HNSC | B6 | 0.2448 | 0.6182 | 0.6093 |

## Reliability gate

- HANCOCK B7-80: mean observed non-abstention coverage 0.803; selective IPCW Brier 0.1098.
- HANCOCK B7-90: mean observed non-abstention coverage 0.902; selective IPCW Brier 0.1156.
- TCGA-HNSC B7-80: mean observed non-abstention coverage 0.810; selective IPCW Brier 0.2332.
- TCGA-HNSC B7-90: mean observed non-abstention coverage 0.904; selective IPCW Brier 0.2329.

## Interpretation boundary

B6 is a stacked residual learner rather than a strict fixed-coefficient Cox offset. The gate uses equal-weight prespecified indicators and outcome-free calibration quantiles. Any robustness claim requires separately authorized Phase 5 stress tests and Phase 6 locked/external evaluation.
