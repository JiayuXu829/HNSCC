# U6R1 patient-level aggregation router exploration audit

- Repeated development OOF predictions were aggregated to one row per patient before router fitting and policy evaluation.
- Prediction-instability features were computed from the repeated OOF predictions and used only as pre-outcome reliability proxies.
- Router fitting was patient-level, five-fold cross-fitted, and development-only.
- All thresholds 0.40, 0.50 and 0.60 were reported; no confirmation or external outcomes were read.
- Selection policies always used either raw V1R or V0, retaining 100% coverage.

## Claim boundary

This is an exploratory development experiment. It may inform a future locked router protocol, but it is not router confirmation, external validation, clinical utility, or deployment evidence.
