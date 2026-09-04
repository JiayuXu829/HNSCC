# U7R2 RADCURE external characterization completed

**Date:** 2026-09-03  
**Status:** completed as a post-hoc external characterization package; not formal current-V1R external confirmation

## Objective

After selecting RADCURE as the best available local cohort, freeze and package the RADCURE held-out test-split analysis under an explicit clinical/radiomics characterization label. The purpose is to describe transportability signals without silently substituting radiomics for current V1R blood/ICD/TMA inputs.

## Execution and safeguards

The source Phase 7 prediction-generation receipt records `outcomes_loaded: false`, and the Phase 7 completion receipt records that Phase 6 outputs were not overwritten, TRUST-HN/gate thresholds were not retuned, and external outcomes were not used for tuning. U7R2 itself read only tracked aggregate metrics and receipts; it did not read patient-level rows or outcome columns, regenerate predictions, or refit any model.

## Results

RADCURE held-out test split: **626 patients / 110 events**, with **100% coverage**.

| Comparator | IPCW Brier | Uno C | AUC24 | Harrell C | CITL | Slope |
|---|---:|---:|---:|---:|---:|---:|
| C1 | 0.095801 | 0.806595 | 0.819376 | 0.795924 | -0.097110 | 1.950857 |
| C2 | 0.090683 | 0.806744 | 0.818182 | 0.797862 | -0.044444 | 1.139466 |
| C3 | 0.098469 | 0.771260 | 0.780742 | 0.761632 | -0.099603 | 1.268349 |
| C4 | 0.097403 | 0.779243 | 0.787882 | 0.768812 | -0.074520 | 1.471544 |

## Paper interpretation

This result can support an exploratory subsection or appendix describing external transportability of adapted clinical/radiomics comparator models. It cannot support a current-V1R external-validation claim because the RADCURE inputs do not reproduce the frozen V1R blood/ICD/TMA contract, the outcome was previously consumed, and the comparator definitions are not identical to the current V1R residual-shrinkage ensemble.

The core paper narrative therefore remains:

```text
V0 clinical anchor -> V1R residual-shrinkage rescue -> HANCOCK locked directional confirmation
```

RADCURE is an additional, clearly labelled transportability characterization, not a replacement for the missing formal compatible-cohort confirmation.

## Artifacts

- `core_backbone/U7R2_RADCURE_external_characterization/frozen_u7r2_radcure_external_characterization_protocol.yaml`
- `core_backbone/U7R2_RADCURE_external_characterization/u7r2_radcure_external_characterization_aggregate_results.json`
- `core_backbone/U7R2_RADCURE_external_characterization/u7r2_radcure_external_characterization_audit.md`
- `scripts/run_u7r2_radcure_external_characterization.py`
