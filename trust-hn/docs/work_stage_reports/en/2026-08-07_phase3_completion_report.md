# TRUST-HN Phase 3 completion report

**Date:** 2026-08-07  
**Phase:** Development-only survival baselines  
**Status:** Complete within the user-authorized conditional scope; Phase 4 remains unauthorized.  
**Configuration:** `configs/phase3_baselines.json` (`FROZEN_FOR_PHASE3_DEVELOPMENT`)

## 1. Authorized boundary

The user authorized Phase 3 baseline implementation after reviewing Phase 2. This authorization covered B0-B5 where the required modality was available, five-seed/five-fold OOF prediction, full-training prediction on the dedicated calibration partition, 24-month IPCW Brier score, Harrell/Uno concordance, dynamic AUC, calibration diagnostics, IPCW decision-curve analysis, and missingness/permuted-modality controls.

The authorization did **not** include Phase 4 residual/offset learning, reliability/OOD/uncertainty gates, AUGMENT/FALLBACK/ABSTAIN threshold selection, RADCURE challenge-test outcomes, HANCOCK OOD-test outcomes, GEO external outcomes, or final locked/external evaluation. None of these prohibited components was used.

RADCURE B4/B5/N0 remained blocked because the ORCESTRA RDS structure has not been validated with R/Rscript or another validated parser.

## 2. Data and model design

Only frozen, eligible, endpoint-usable training and calibration rows were loaded. The study partitions were:

| Study | Training | Calibration | Additional modality in Phase 3 | Sealed/external outcomes used |
|---|---:|---:|---|---|
| RADCURE | 1,215 | 303 | Blocked radiomics/GTV | No |
| HANCOCK | 489 | 122 | Baseline blood plus TMA cell density | No |
| TCGA-HNSC | 416 | 103 endpoint-usable of 104 allocated | Protein-coding expression | No |

TCGA-HNSC expression was cached as a `519 x 19,962` protein-coding `log2(TPM+1)` matrix. Top-500 variance selection was fit separately inside every OOF training fold and on full training only for calibration prediction.

Model definitions:

- B0: Kaplan-Meier constant risk;
- B1: clinical Cox proportional hazards;
- B2: clinical elastic-net Cox;
- B3: clinical random survival forest;
- B4: additional-modality-only elastic-net Cox;
- B5: direct clinical-plus-modality elastic-net Cox;
- M0: missingness-indicator-only control;
- N0: outcome-independent permuted-modality control.

Preprocessing, imputation, encoding, scaling, and feature selection were fit without calibration, sealed, or external outcomes. The censoring distribution for IPCW was derived from training reference data, and subjects censored before 24 months received zero outcome weight rather than being labeled survivors.

## 3. Execution accounting and outputs

Final execution:

- **105 successful study/model/seed runs**;
- **0 failed runs**;
- **10 completed runs with diagnostic warnings**;
- **3 governance-blocked model entries**: RADCURE B4, B5, and N0;
- **210 patient-level prediction CSV files**, stored only in Git-ignored `results/predictions/phase3/`.

The diagnostic warnings were five RADCURE M0 fits with all Cox coefficients zero and five TCGA-HNSC M0 fits that reduced to B0 because no missingness indicator varied.

Tracked aggregate outputs include:

- `results/metrics/phase3/oof_metrics.csv` (105 rows);
- `results/metrics/phase3/calibration_metrics.csv` (105 rows);
- `results/metrics/phase3/stability_summary.csv`;
- `results/metrics/phase3/model_status.csv` (108 rows);
- `results/metrics/phase3/decision_curve.csv` (2,100 rows);
- three SVG comparison/decision-curve figures;
- `docs/audits/phase3/leakage_audit.md`;
- `docs/audits/phase3/baseline_findings.md`;
- `results/manifests/phase3_baseline_receipt.json`.

The receipt records SHA-256 hashes for all generated aggregate experimental outputs. Frozen configuration hashes are:

- `phase3_baselines.json`: `8d18348cf059895a25c3b1a07ea4d670b23fa5a18dfa9809fea64caf40f9822e`;
- `phase3_governance.json`: `ff6a17e96e496f1bc04296980d3965cb03bd0a713612da7014d5f09617df8f5d`.

## 4. Dedicated calibration-partition results

Values are means over five seeds.

### RADCURE

| Model | IPCW Brier | Harrell C | Uno C | 24-month AUC |
|---|---:|---:|---:|---:|
| B0 | 0.1629 | 0.5000 | 0.5000 | 0.5000 |
| B1 | 0.1394 | 0.7348 | 0.7675 | 0.7908 |
| B2 | 0.1431 | 0.7328 | 0.7357 | 0.7609 |
| B3 | **0.1380** | **0.7525** | **0.7700** | **0.7969** |
| M0 | 0.1626 | 0.5639 | 0.5805 | 0.5932 |

Clinical models strongly outperform B0 and M0; B3 is strongest overall. No radiomics conclusion is permitted because B4/B5/N0 were blocked.

### HANCOCK

| Model | IPCW Brier | Harrell C | Uno C | 24-month AUC |
|---|---:|---:|---:|---:|
| B0 | 0.1512 | 0.5000 | 0.5000 | 0.5000 |
| B1 | 0.1538 | 0.5162 | 0.5798 | 0.6111 |
| B2 | 0.1460 | 0.6328 | 0.6597 | 0.6901 |
| B3 | 0.1406 | 0.6473 | 0.6739 | 0.7100 |
| B4 | 0.1292 | 0.6306 | 0.6881 | 0.7018 |
| B5 | **0.1276** | **0.6948** | **0.7594** | **0.7873** |
| M0 | 0.1498 | 0.6137 | 0.6565 | 0.6686 |
| N0 | 0.1513 | 0.5281 | 0.5290 | 0.5292 |

B5 produces a clear calibration-partition improvement over B2/B3. N0 remains near B0, and M0 is below B5, supporting that the observed blood/TMA fusion benefit is not reproduced by row permutation or missingness alone.

### TCGA-HNSC

| Model | IPCW Brier | Harrell C | Uno C | 24-month AUC |
|---|---:|---:|---:|---:|
| B0 | 0.2349 | 0.5000 | 0.5000 | 0.5000 |
| B1 | 0.2515 | 0.5971 | 0.5856 | 0.5741 |
| B2 | 0.2422 | 0.4898 | 0.4611 | 0.4368 |
| B3 | **0.2301** | 0.6107 | 0.6152 | 0.6219 |
| B4 | 0.2382 | **0.6266** | **0.6275** | **0.6293** |
| B5 | 0.2482 | 0.6104 | 0.6028 | 0.6001 |
| M0 | 0.2349 | 0.5000 | 0.5000 | 0.5000 |
| N0 | 0.2488 | 0.5114 | 0.5020 | 0.4963 |

Expression-only B4 improves discrimination, whereas clinical B3 has the best 24-month Brier. B5 worsens Brier relative to B0 and B3 and does not surpass B4 discrimination. This demonstrates a development-only discrimination/absolute-risk tradeoff and supports the premise that compulsory multimodal fusion is not uniformly beneficial.

## 5. OOF highlights and interpretation limits

- RADCURE B3: Brier `0.1367`, Harrell C `0.7424`, AUC `0.8063`.
- HANCOCK B3: Brier `0.1037`; B5: Brier `0.1052`, AUC `0.7473`.
- TCGA-HNSC B2/B3: Brier `0.2207/0.2214`; B5: AUC `0.6280`, Brier `0.2239`.
- N0 controls are near chance or materially worse.

Calibration slopes for constant-risk, weak, and negative-control models can be undefined or unstable and must not be overinterpreted. Decision curves remain descriptive; Phase 3 did not select treatment, reliability, augmentation, fallback, or abstention thresholds.

## 6. Governance, privacy, and verification

The implementation audit confirms fold-local preprocessing/selection, calibration isolation, outcome-independent N0 permutation, training-derived IPCW censoring, and non-use of sealed/external outcomes. Patient-level predictions are Git-ignored, while tracked Phase 3 files contain aggregate data only.

Final verification performed at Phase 3 closeout:

- **53 tests passed**;
- Python compilation passed;
- Ruff passed for all new/modified Phase 3 code and tests;
- patient prediction ignore behavior was confirmed;
- tracked Phase 3 reports/outputs were scanned for native RADCURE, TCGA, and GEO identifier patterns;
- tracked CSV headers were checked for prohibited patient/sample identifier columns.

A repository-wide Ruff scan still reports 271 pre-existing style findings in older Phase 0-2 files. This is legacy style debt and not a Phase 3 model/test failure; no repository-wide Ruff success is claimed.

## 7. Scientific conclusion and next gate

Phase 3 is **conditionally complete** within the authorized scope. The results establish development-only baselines and negative controls but do not provide locked, external, prospective, or clinical-utility validation.

The persistent condition is that RADCURE radiomics B4/B5/N0 cannot be completed until the ORCESTRA RDS structure is validated. Phase 4 remains **not authorized**. Entering Phase 4 requires a new explicit user decision after review of the Phase 3 findings and governance limits.
