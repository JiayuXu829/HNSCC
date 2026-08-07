# TRUST-HN Phase 4 completion report

**Date:** 2026-08-07  
**Phase:** TRUST-HN core development (B6 residual fusion and B7 reliability gate)  
**Status:** Complete within the user-authorized conditional scope; Phase 5 and locked/external evaluation remain unauthorized.  
**Configuration:** `configs/phase4_trust_hn.json` (`FROZEN_FOR_PHASE4_DEVELOPMENT`)

## 1. Authorized boundary

The user authorized Phase 4 after reviewing the Phase 3 baseline results. The authorized work covered development-only implementation of the B6 stacked residual learner, three outcome-free OOD detectors, lightweight bootstrap uncertainty, prespecified equal-weight reliability scores, and B7 AUGMENT/FALLBACK/ABSTAIN actions.

Only frozen training and calibration rows from HANCOCK and TCGA-HNSC were authorized. The following outcomes remained prohibited and were not loaded: RADCURE challenge test, HANCOCK OOD test, GSE65858 external test, and GSE41613 sensitivity cohort. Phase 5 stress tests, subgroup campaigns, analysis freeze, and Phase 6 locked/external evaluation were not performed.

RADCURE B6/B7 remained blocked because the ORCESTRA RDS modality structure has not been validated. This phase therefore makes no radiomics-fusion or reliability-gate claim for RADCURE.

## 2. Development data used

| Study | Training | Calibration | Additional modality | Phase 4 status |
|---|---:|---:|---|---|
| HANCOCK | 489 | 122 | Baseline blood measurements plus TMA cell-density features | Complete |
| TCGA-HNSC | 415 | 104 | 19,962 protein-coding `log2(TPM+1)` expression features; fold-local top-500 variance selection | Complete |
| RADCURE | 1,215 | 303 | Radiomics/GTV unavailable pending RDS validation | Blocked |

The studies were modeled separately and were not pooled into one patient table.

## 3. Implemented method

### 3.1 B2 clinical anchor and B6 stacked residual learner

B2 is the clinical elastic-net Cox anchor. For every outer OOF training split, inner five-fold cross-fitting generated a clinical anchor score for each B6 training patient. B6 then fit an elastic-net Cox survival model to the standardized cross-fitted anchor score plus the training-derived modality representation. Prediction for an outer held-out fold or the calibration partition used the B2 model fitted on the corresponding complete training portion.

This is the stacked residual option allowed by the master implementation document. It is not a strict Cox model with the clinical anchor coefficient fixed as an offset. B5 direct clinical-plus-modality concatenation remained the compulsory-fusion comparator.

### 3.2 Reliability indicators

All reliability indicators were oriented so that larger values meant greater unreliability.

Clinical reliability used:

- shrinkage Mahalanobis distance, k-nearest-neighbor distance, and Isolation Forest score on training-derived clinical embeddings;
- standard deviation from a 20-model clinical bootstrap ensemble, with median and 95% interval width retained in patient traces;
- absolute disagreement between B2 and the nonlinear B3 random-survival-forest risk.

Modality/fusion reliability used:

- the same three OOD detectors on training-derived modality embeddings;
- standard deviation from a 20-model B6 bootstrap ensemble, with median and 95% interval width retained;
- deterministic outcome-independent modality row-permutation sensitivity;
- raw modality missingness fraction and complete-modality-missing flag;
- absolute B6-versus-B5 risk disagreement.

Each raw indicator was converted to an empirical percentile using the dedicated calibration reliability distribution. The three OOD percentiles were first averaged within their domain. Clinical and modality unreliability were then calculated as prespecified equal-weight means. Constant zero-missingness references map to zero unreliability rather than an artificial maximum percentile.

### 3.3 B7 gate

The action precedence was frozen as:

1. **ABSTAIN** when clinical unreliability exceeds its threshold;
2. otherwise **FALLBACK** when the modality is completely missing or modality unreliability exceeds its threshold;
3. otherwise **AUGMENT** with B6.

For AUGMENT, final risk is the B6 risk; for FALLBACK, final risk is the B2 clinical-anchor risk; for ABSTAIN, no final risk is emitted. Prespecified 80% and 90% profiles used calibration reliability quantiles only. Calibration outcomes were not used to optimize thresholds.

## 4. Execution accounting

The frozen full run used five outer folds, seeds `17, 29, 43, 71, 101`, and 20 bootstrap models per fit scope.

- **10 successful study/seed runs**: 2 studies x 5 seeds;
- **0 failed runs**;
- **1 governance-blocked entry**: RADCURE B6/B7;
- **1,200 successful clinical bootstrap fits** and **1,200 successful B6 bootstrap fits** across the full run;
- **20 patient-level decision-trace CSV files**, stored only in Git-ignored `results/predictions/phase4/`;
- no sealed or external outcomes used;
- no Phase 5 component used.

A preliminary isolated smoke run was completed for each authorized study before the canonical full run. Both smoke paths succeeded, including the high-dimensional TCGA expression path.

## 5. Model results on the dedicated calibration partitions

Values are means over five prespecified seeds. B2 and B5 calibration fits are deterministic under the frozen preprocessing and therefore have zero seed variation; B6 varies slightly because its cross-fitted anchor training scores depend on the seed.

| Study | Model | IPCW Brier | Harrell C | Uno C | 24-month AUC |
|---|---|---:|---:|---:|---:|
| HANCOCK | B2 clinical anchor | 0.1460 | 0.6328 | 0.6597 | 0.6901 |
| HANCOCK | B5 forced fusion | **0.1276** | **0.6948** | **0.7594** | **0.7873** |
| HANCOCK | B6 stacked residual | 0.1288 | 0.6756 | 0.7410 | 0.7692 |
| TCGA-HNSC | B2 clinical anchor | **0.2422** | 0.4898 | 0.4611 | 0.4368 |
| TCGA-HNSC | B5 forced fusion | 0.2482 | 0.6104 | 0.6028 | 0.6001 |
| TCGA-HNSC | B6 stacked residual | 0.2448 | **0.6182** | **0.6125** | **0.6093** |

Interpretation:

- In HANCOCK, adding blood/TMA information clearly helps relative to B2. B5 remains the strongest full-cohort calibration model. B6 is close in Brier score but does not surpass B5 discrimination on the calibration partition.
- In TCGA-HNSC, B6 improves Brier and discrimination relative to B5, but its Brier remains slightly worse than B2. The very weak B2 discrimination and better B6 discrimination demonstrate a calibration-versus-ranking trade-off rather than uniform superiority.
- B6 therefore provides a valid conditional-fusion implementation, but Phase 4 does not establish that residual fusion is universally better than direct fusion.

Mean OOF results support the same mixed picture: HANCOCK B6 has slightly higher Harrell C than B5 (`0.6822` versus `0.6789`) with similar Brier (`0.1057` versus `0.1052`), whereas TCGA B6 does not beat B5 OOF (`0.2261` versus `0.2239` Brier; `0.5949` versus `0.6025` Harrell C).

## 6. Gate behavior

### Dedicated calibration partitions

| Study | Profile | Observed non-abstention coverage | AUGMENT | FALLBACK | ABSTAIN | Selective IPCW Brier |
|---|---:|---:|---:|---:|---:|---:|
| HANCOCK | 80% | 0.8033 | 0.6492 | 0.1541 | 0.1967 | 0.1098 |
| HANCOCK | 90% | 0.9016 | 0.8213 | 0.0803 | 0.0984 | 0.1156 |
| TCGA-HNSC | 80% | 0.8096 | 0.6577 | 0.1519 | 0.1904 | 0.2332 |
| TCGA-HNSC | 90% | 0.9038 | 0.8173 | 0.0865 | 0.0962 | 0.2329 |

The observed calibration coverages closely match the prespecified targets by construction. At the 80% profile, approximately 65% of calibration patients were augmented, 15% fell back, and 19-20% were abstained. At the 90% profile, approximately 82% were augmented, 8-9% fell back, and about 10% were abstained.

Selective Brier scores describe performance only among non-abstained patients. They must not be interpreted as ordinary full-cohort improvements over B2/B5/B6 because the evaluated populations differ. Phase 5 must test whether the reliability ordering remains meaningful under natural missingness, artificial dropout, shortcut perturbations, and subgroup shifts.

## 7. Outputs

Tracked aggregate outputs:

- `results/metrics/phase4/model_metrics.csv`;
- `results/metrics/phase4/gate_metrics.csv`;
- `results/metrics/phase4/risk_coverage.csv`;
- `results/metrics/phase4/action_summary.csv`;
- `results/metrics/phase4/thresholds.csv`;
- `results/metrics/phase4/reliability_diagnostics.csv`;
- `results/metrics/phase4/model_status.csv`;
- `results/figures/phase4/model_comparison.svg`;
- `results/figures/phase4/risk_coverage.svg`;
- `results/figures/phase4/action_distribution.svg`;
- `docs/audits/phase4/leakage_audit.md`;
- `docs/audits/phase4/core_findings.md`;
- `results/manifests/phase4_trust_hn_receipt.json`.

Patient-level traces contain B2/B5/B6 risks, modality increments, raw indicators, calibration-referenced ranks, unreliability scores, both gate profiles, reasons, and final gated risks. They remain Git-ignored.

Frozen configuration hashes recorded in the receipt:

- `phase4_trust_hn.json`: `25322f6b68927f267c98a7d017bca01a6ebe6debd434926b72dd6a2e844abb0d`;
- `phase4_governance.json`: `c34bc832c999dc69539088ad70a927a6278beb9db40426ee4c0f9b4f7bef7de1`.

## 8. Verification

- Full test suite: **57 passed**, with two dependency deprecation warnings only;
- Phase 4 targeted tests: **4 passed**;
- Python compilation of `src`, `scripts`, and `tests`: passed;
- targeted Ruff checks for all Phase 4 code and tests: passed;
- `git diff --check`: passed;
- 20 canonical Phase 4 patient trace files confirmed Git-ignored;
- aggregate CSV headers and tracked-output contents contain no prohibited patient/sample identifier columns or recognized RADCURE/TCGA/GEO native-ID patterns;
- receipt hashes were verified against the generated files.

## 9. Scientific conclusion and next gate

Phase 4 is **complete within the authorized conditional scope**. The project now has a working end-to-end development implementation of the clinical anchor, stacked residual fusion, outcome-free OOD indicators, bootstrap uncertainty, reliability scoring, calibration-derived profiles, and AUGMENT/FALLBACK/ABSTAIN decisions.

The current evidence is still development-stage evidence. It does not establish robustness under shift, external validity, prospective validity, clinical utility, or a final deployable threshold. RADCURE modality-dependent TRUST-HN remains blocked.

**Phase 5 is not authorized.** Entering Phase 5 requires a new explicit user decision. Phase 6 locked/external evaluation must remain sealed until stress testing, analysis freeze, immutable hashes, and separate explicit approval are complete.
