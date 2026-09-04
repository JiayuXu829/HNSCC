# U7R2 RADCURE external characterization

## Decision

RADCURE was the preselected best available local dataset for an honest external characterization. This stage packages the already completed Phase 7 comparator benchmark; it is **not** formal current-V1R external confirmation.

## Cohort and provenance

- RADCURE held-out test split: **626 patients / 110 events**.
- The comparator predictions were generated in the source Phase 7 prediction stage before external outcomes were loaded (`outcomes_loaded: false`).
- This packaging step read only tracked aggregate metrics and receipts; it did not read patient rows or outcome columns, regenerate predictions, retune models, or modify Phase 6 files.
- The available RADCURE contract is clinical plus radiomics, not the frozen current-V1R blood/ICD/TMA contract. The cohort outcome was also consumed historically, so it is not a pristine outcome-untouched confirmation cohort.

## Aggregate comparator results

| Comparator | IPCW Brier | Uno C | AUC24 | Harrell C | CITL | Slope | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 | 0.095801 | 0.806595 | 0.819376 | 0.795924 | -0.097110 | 1.950857 | 100.0% |
| C2 | 0.090683 | 0.806744 | 0.818182 | 0.797862 | -0.044444 | 1.139466 | 100.0% |
| C3 | 0.098469 | 0.771260 | 0.780742 | 0.761632 | -0.099603 | 1.268349 | 100.0% |
| C4 | 0.097403 | 0.779243 | 0.787882 | 0.768812 | -0.074520 | 1.471544 | 100.0% |

## Interpretation

The RADCURE analysis can support a manuscript subsection describing external transportability of an adapted clinical/radiomics comparator set. It cannot support the sentence that current V1R was externally validated, because: (1) the RADCURE inputs do not reproduce the frozen V1R blood/ICD/TMA contract; (2) the RADCURE test split is not a newly acquired outcome-untouched cohort; and (3) the Phase 7 comparator definition is not identical to the current V1R residual-shrinkage ensemble.

The result therefore remains separate from the core V1R confirmation narrative and should be reported as exploratory/appendix material unless the manuscript explicitly includes a transportability characterization section. No RADCURE outcome is permitted to tune V1R, bridge, router, thresholds or safety gates.

## Artifacts

- `frozen_u7r2_radcure_external_characterization_protocol.yaml`
- `u7r2_radcure_external_characterization_aggregate_results.json`
- `u7r2_radcure_external_characterization_audit.md`
