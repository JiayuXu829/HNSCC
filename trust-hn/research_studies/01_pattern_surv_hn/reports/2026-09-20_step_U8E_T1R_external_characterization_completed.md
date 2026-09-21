# 2026-09-20 — U8E T1R GEO post-hoc external characterization completed

## Objective

Apply the frozen U8 T1R transcriptome residual-shrinkage construction, fitted once on the full TCGA-HNSC development cohort, without refitting or tuning, to the two available GEO cohorts. The objective is descriptive transport characterization only.

This is **post-hoc descriptive external characterization only**. GEO outcomes were previously consumed during Phase 6. No GEO outcome was used for fitting, model selection, architecture selection, threshold selection, or tuning. It is **not formal external validation**, not confirmation, not a clinical-utility analysis, and not evidence of deployment readiness.

## Frozen application

- Source stage: U8 T1R transcriptome development CV
- Development fit: full TCGA-HNSC development cohort (`n=519`, events `221`)
- External seed: `20260907`
- Clinical anchor: seven-variable elastic-net Cox
- Transcriptome residual head: `Linear(500→32) → Tanh → Linear(32→1)`
- Parameters: `16065`
- Selection source: TCGA development-only inner CV
- Selected anchor: alpha `0.05`, L1 ratio `0.1`
- Selected residual penalty: `1.0`
- Selected optimization checkpoint: step `10`
- Selected residual scale: `1.0`
- GEO refitting: no
- GEO tuning: no

## Aggregate cohort-level results

Lower IPCW Brier is better; higher C/AUC is better. Deltas are T1R minus V0.

### GSE65858 — post-hoc external-test characterization

```text
n / events                         244 / 78
coverage                           100%

V0 IPCW Brier24                    0.195207
T1R IPCW Brier24                   0.195070
delta IPCW Brier24                -0.000137

V0 Harrell C                       0.581806
T1R Harrell C                      0.644868
delta Harrell C                   +0.063062

V0 Uno C24                         0.583694
T1R Uno C24                        0.645818
delta Uno C24                     +0.062123

V0 AUC24                           0.588972
T1R AUC24                          0.650733
delta AUC24                       +0.061762

V0 CITL24                         -0.763793
T1R CITL24                         -0.831959
delta CITL24                       -0.068166

V0 calibration slope24             1.707442
T1R calibration slope24            1.941562
delta calibration slope24         +0.234120
```

T1R showed slightly lower Brier and materially higher cohort-level discrimination in this GEO cohort. Its calibration-in-the-large moved farther from zero and its slope moved farther from 1, so the calibration picture is not uniformly favorable.

### GSE41613 — post-hoc sensitivity characterization

```text
n / events                         97 / 51
coverage                           100%

V0 IPCW Brier24                    0.265712
T1R IPCW Brier24                   0.258607
delta IPCW Brier24                -0.007104

V0 Harrell C                       0.500000
T1R Harrell C                      0.626361
delta Harrell C                   +0.126361

V0 Uno C24                         0.500000
T1R Uno C24                        0.616039
delta Uno C24                     +0.116039

V0 AUC24                           0.500000
T1R AUC24                          0.634011
delta AUC24                       +0.134011

V0 CITL24                         -0.273717
T1R CITL24                         -0.264792
delta CITL24                       +0.008925

V0 calibration slope24             undefined (constant V0 risk)
T1R calibration slope24            1.939018
```

The applied V0 anchor produced a constant risk score in GSE41613, so its discrimination metrics are 0.5 by convention and its calibration slope is undefined. Consequently, the T1R-versus-V0 ranking comparison in this cohort is against a degenerate reference and must not be interpreted as a formal external validation result.

## Interpretation boundary

The direction of the aggregate deltas was favorable for Brier and discrimination in both available GEO cohorts. This is still only a post-hoc descriptive signal. The GEO outcomes had already been seen in prior Phase 6 work, no uncertainty intervals or hypothesis tests were requested, and the GSE41613 reference anchor was constant. Therefore, U8E cannot establish formal external validity, transportability, superiority, clinical utility, or deployment readiness. It also does not replace the V1R/HANCOCK confirmation narrative.

## Implementation and checks

- `ruff check src/trust_hn/pattern_surv_hn/t1r_external_eval.py`: PASS
- `pytest tests/test_pattern_surv_hn_t1r.py -q`: `6 passed`
- Aggregate-only sensitive-key scan: PASS
- Frozen-protocol/aggregate stage alignment: PASS
- Patient prediction Git-ignore checks: PASS for both CSV files
- Patient-level rows: not copied into the paper or research-study directories

## Artifacts and hashes

- Frozen protocol: `research_studies/01_pattern_surv_hn/core_backbone/U8E_T1R_external_characterization/frozen_u8e_t1r_external_characterization_protocol.yaml`
  - SHA-256: `59b076a2368d7d62c4e0629869964e9ad9a9d18c5dcb4fa380cd0d7795795571`
- Aggregate audit: `research_studies/01_pattern_surv_hn/core_backbone/U8E_T1R_external_characterization/aggregate_t1r_external_characterization_audit.json`
  - SHA-256: `e611bb37c18ec00215f472ce72bdbebfb533b847ee0a2c32c82ac97bc593751e`
- Approval receipt: `research_studies/01_pattern_surv_hn/approvals/U8E_T1R_EXTERNAL_CHARACTERIZATION_APPROVED.md`
  - SHA-256: `41906a386339844c1ac3f001336e2f9e4afdc4a81ce959e002e72d2622baf13a`
- Implementation: `src/trust_hn/pattern_surv_hn/t1r_external_eval.py`
  - SHA-256: `a773a9ecabc48a42d3077b46b28ef89a67c90d06187b3544e5052fdaaeaff1f1d`
- Patient outputs remain untracked under `results/predictions/pattern_surv_hn/U8_T1R_external/`
  - GSE65858 SHA-256: `ba6647354f30ebb50bff745d88295f0d3b5143465e59a84b0e6cf8685dce4f3`
  - GSE41613 SHA-256: `2c839417c9851186e9a5fd1a829932471bc5f2bd419ea6281003468d6a28c4b5`

## Paper status

U8E has not yet been integrated into the manuscript or supplement. If integrated later, the safest placement is a short, clearly labelled supplementary section distinct from U8/S10, repeating that GEO outcomes were previously consumed and that this is descriptive characterization rather than external validation.
