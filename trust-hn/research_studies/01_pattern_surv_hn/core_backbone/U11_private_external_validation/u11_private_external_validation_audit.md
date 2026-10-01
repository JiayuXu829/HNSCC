# U11 private external validation audit

- Workbook SHA256: `9341150581FBF3805D4A7F39C2FEB43A419E12DE2CC7CC5C6ED238E28261A281`
- Cohort: 125 patients from two pseudonymized centres; 59 observed deaths.
- Patient identifiers aligned one-to-one across cohort, prediction and outcome sheets; no duplicates were detected.
- Required clinical fields and CAM/SCRF predictions were complete; both models had 100% coverage.
- Recomputed point estimates matched the workbook to absolute tolerance 1e-12.
- Empty-set CAM fallback was exact for both score and 24-month risk.
- No patient-level row was copied into the repository.

## External validation result

SCRF improved Uno C at 24 months from 0.727700 to 0.796615 and IPCW Brier from 0.121450 to 0.110822. The workbook's paired 2,000-replicate intervals were [0.020752, 0.124547] for delta Uno C and [-0.018537, -0.003465] for delta IPCW Brier.

## Claim boundary

This is independent retrospective external validation of the supplied frozen CAM/SCRF predictions. The transfer package did not include a timestamped prediction-seal receipt, so it is not labelled prospective or outcome-untouched confirmation. Calibration slope remained above one, and decision-curve benefit, clinical utility and deployment readiness were not tested.
