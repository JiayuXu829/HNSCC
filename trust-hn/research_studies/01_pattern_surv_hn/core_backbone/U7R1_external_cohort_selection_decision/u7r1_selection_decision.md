# U7R1 external cohort selection decision

**Date:** 2026-09-03  
**Decision:** RADCURE selected as the best available cohort for a *secondary external characterization*, not as formal current-V1R confirmation.

## Selection result

| Candidate | Technical compatibility | Provenance for new formal confirmation | Sample size / events | Decision |
|---|---|---|---:|---|
| HANCOCK OOD | Highest; current V1R input contract available | Not eligible; already used for raw-V1R confirmation and bridge characterization | 152 / 40 | Do not reuse as pristine confirmation |
| **RADCURE** | Clinical + radiomics available, but frozen blood/ICD/TMA V1R contract is absent | Not certified as untouched in the current inventory; prior exploratory outcome readout exists | **626 / 110** | **Select for secondary external characterization only** |
| GSE65858 | Legacy transcriptomic/B6 risk only | Historical outcomes already consumed | 244 / 78 | Not current V1R |
| GSE41613 | Legacy transcriptomic/B6 risk only | Historical outcomes already consumed | 97 / 51 | Not current V1R |
| TCGA-HNSC | Expression/clinical metadata | No current V1R prediction contract | n/a | Not current V1R |

## Why RADCURE is selected

RADCURE is the largest available independent cohort with a substantial event count and an existing clinical/radiomics representation. It is therefore the most informative local dataset for a transportability characterization of the clinical anchor and an explicitly adapted clinical/radiomics comparator.

## What this selection does and does not authorize

### Authorized scope

- Freeze a separate exploratory protocol for RADCURE characterization.
- Evaluate only a clearly labelled RADCURE-compatible comparator or anchor-level analysis.
- Report coverage, missingness, prediction distribution, discrimination and IPCW Brier with the post-hoc label.

### Not authorized

- Calling RADCURE a formal external validation of current V1R.
- Pretending radiomics is blood/ICD/TMA or silently substituting modalities.
- Reusing V1R weights with an unrecorded input substitution.
- Claiming the result validates the V1R bridge or router.
- Using RADCURE outcomes to tune V1R, bridge, router, thresholds or safety gates.

## Formal conclusion

If the scientific question is **formal current-V1R external confirmation**, no local cohort can be selected: the correct answer remains “new compatible outcome-untouched cohort required.” If the practical question is **which existing cohort should be used for an honest external characterization now**, the selected cohort is **RADCURE**.

No current-V1R external metric was generated in this selection step.
