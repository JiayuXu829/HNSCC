# U5R10 fixed bridge external secondary characterization completed

**Date:** 2026-08-27  
**Status:** completed as locked post-unseal secondary characterization; not current V1R external confirmation

## Question

Can the frozen U5R7 bridge direction be reproduced in the available external GEO cohorts without refitting or selecting parameters on external outcomes?

## Frozen bridge

\[
p_{bridge}=\operatorname{sigmoid}(-0.14503379856995471+0.90\operatorname{logit}(p_{base})).
\]

The parameter source was the pre-existing 25-fold development-only U5R7 artifact. No external outcome was used to alter alpha, beta, cohort inclusion, or reporting.

## Results

| Cohort | n/events | Base | Bridge | Δ IPCW Brier (bridge−base) | CITL base → bridge | Slope base → bridge | Ranking / coverage |
|---|---:|---:|---:|---:|---:|---:|---|
| GSE65858 | 244/78 | 0.224769 | 0.209071 | −0.015697 | −1.331567 → −1.181249 | 0.608704 → 0.676338 | exact / 100% |
| GSE41613 | 97/51 | 0.204267 | 0.197910 | −0.006357 | −0.571285 → −0.456782 | 0.791168 → 0.879076 | exact / 100% |

The fixed bridge reduced IPCW Brier, reduced absolute CITL error, moved the calibration slope toward 1, and preserved ranking and coverage in both cohorts. In 2,000 patient-level stratified bootstrap replicates, the Brier improvement remained below zero in both cohorts (GSE65858 95% CI −0.019002 to −0.012432; GSE41613 95% CI −0.010730 to −0.002195).

## Critical interpretation boundary

The GEO prediction files used here are legacy Phase 6 `B6` fusion outputs. Their input and prediction definition has not been demonstrated to be identical to the current PATTERN-Surv-HN `V1R` backbone. In addition, the GEO outcomes had already been consumed by the historical Phase 6 evaluation. Accordingly, this result is **positive external characterization of the fixed transform on legacy B6 risk**, not a confirmed external validation of the current V1R bridge.

The result justifies a next, properly confirmatory step: obtain a genuinely outcome-untouched cohort, freeze the current V1R prediction-generation and bridge protocol before outcome access, generate current V1R predictions, and then evaluate the same estimands without refitting.

## Artifacts

- `core_backbone/U5R10_fixed_bridge_external_secondary_characterization/frozen_u5r10_fixed_bridge_external_protocol.yaml`
- `core_backbone/U5R10_fixed_bridge_external_secondary_characterization/u5r10_external_aggregate_results.json`
- `core_backbone/U5R10_fixed_bridge_external_secondary_characterization/u5r10_external_cohort_results.csv`
- `core_backbone/U5R10_fixed_bridge_external_secondary_characterization/u5r10_external_bootstrap_results.csv`
- `core_backbone/U5R10_fixed_bridge_external_secondary_characterization/u5r10_external_audit.md`
- `core_backbone/U5R10_fixed_bridge_external_secondary_characterization/u5r10_external_hashes.json`
- `scripts/run_v1r_fixed_bridge_external_secondary_characterization.py`
