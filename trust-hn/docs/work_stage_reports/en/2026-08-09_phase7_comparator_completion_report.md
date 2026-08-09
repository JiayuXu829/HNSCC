# TRUST-HN Phase 7 Additional Comparator Completion Report

**Date:** 2026-08-09  
**Analysis class:** Phase 7 post-hoc exploratory benchmark  
**Status:** Complete

## 1. Purpose

Before manuscript drafting, Phase 7 added representative survival-analysis comparators and completed development and external experiments. Because the Phase 6 locked/external outcomes had already been observed, every new comparison is explicitly labelled post hoc exploratory. These analyses are not Phase 6 prespecified locked comparisons and were not used to retune TRUST-HN, B7 gate thresholds, or primary endpoints.

## 2. Method count

Before Phase 7, the project contained **10 labelled approaches**:

- six conventional predictive baselines, B0-B5;
- two TRUST-HN methods, B6-B7;
- two audit or negative controls, M0 and N0.

Phase 7 added:

- **C1:** Gradient Boosting Survival Analysis with direct clinical-modality fusion;
- **C2:** XGBoost-Cox with direct fusion and a training-only Breslow conversion to 24-month absolute risk;
- **C3:** late-fusion stacking using cross-fitted clinical and modality risk scores;
- **C4:** missing-aware direct-fusion elastic-net Cox with explicit modality-missingness indicators.

The final inventory is **14 labelled approaches**:

- ten conventional predictive baselines/comparators, B0-B5 and C1-C4;
- two TRUST-HN approaches, B6-B7;
- two audit/negative controls, M0-N0.

Further indiscriminate expansion is not recommended. Extra Survival Trees overlaps substantially with the existing Random Survival Forest baseline, while DeepSurv would add a new deep-learning dependency, compute burden, and tuning surface without necessarily improving the evidence base. Either can be reserved for a specific reviewer request.

## 3. Experimental scale

Development evaluation used the frozen training and calibration partitions of RADCURE, HANCOCK, and TCGA-HNSC. Each new method was evaluated with five deterministic seeds using development out-of-fold and frozen calibration predictions. This produced **120 successful metric rows and no failed tasks**.

After methods and hyperparameters were frozen, outcome-free predictions were generated for RADCURE locked test (n=626), HANCOCK OOD test (n=152), GSE65858 external test (n=244), and GSE41613 sensitivity cohort (n=97). External evaluation produced:

- 16 aggregate method-by-cohort metric rows;
- comparisons of C1-C4 against B5 and B6;
- four metrics with 1,000 patient-level paired bootstrap replicates;
- 128 aggregate paired-comparison rows.

## 4. Main results

### RADCURE

C2 XGBoost-Cox was the strongest new comparator: IPCW Brier 0.09068, Uno C 0.80674, and 24-month AUC 0.81818. Relative to B6, the Brier difference was -0.00736 (95% CI -0.01162 to -0.00283) and the Uno C difference was +0.03272 (95% CI +0.00705 to +0.06054). This is a post-hoc exploratory finding and must not be reframed as prespecified model selection.

### HANCOCK

C2 had the lowest Brier score (0.10367), while C1 had the highest Uno C (0.84451). B6 had Brier 0.11219 and Uno C 0.82813. The principal paired confidence intervals for C1/C2 versus B6 crossed zero, so the appropriate interpretation is competitive point-estimate performance rather than confirmed superiority.

### GSE65858

C3 late fusion had the lowest Brier among new methods (0.20499) and Uno C 0.64307. Its Brier difference versus B6 was -0.06755 (95% CI -0.09043 to -0.04585). However, clinical B2 remained better calibrated by Brier (0.19639), C3 had a calibration intercept of -0.93952, and C2 deteriorated to Brier 0.34287 with mean predicted risk 0.54852. Thus, the additional methods do not overturn the original conclusion that cross-platform transcriptomic fusion has material calibration and transportability problems.

### GSE41613

C2 had the lowest Brier (0.24835), while C1 had the highest Uno C (0.69501). Most Brier and Uno C confidence intervals versus B6 crossed zero. With only 97 patients, these estimates remain sensitivity and hypothesis-generating evidence.

### Missing-aware fusion

C4 reproduced B5 numerically across the four external cohorts. Under the present development data and penalty settings, the added missingness features supplied no visible incremental prediction gain. This is a useful negative result but does not establish that missingness modelling is universally ineffective.

## 5. Overall interpretation

1. The four additions provide complementary tree boosting, XGBoost-Cox, late-fusion, and missing-aware comparisons; comparator coverage is now sufficient for manuscript drafting.
2. No method won consistently across all ecosystems; rankings remained cohort-, modality-, and platform-dependent.
3. C2 was strong in RADCURE and competitive in HANCOCK but badly overpredicted risk in GSE65858, demonstrating that discrimination does not replace transportability and calibration assessment.
4. C3 improved upon B6 in GSE65858 Brier error but did not outperform the clinical B2 anchor, supporting the manuscript theme that a clinical anchor and safe degradation remain necessary.
5. The results do not justify claims of universal distribution-shift robustness, prospective validation, deployable thresholds, demonstrated clinical utility, or patient benefit.

## 6. Files and outputs

New configuration, implementation, and tests:

- `configs/phase7_exploratory_benchmarks.json`
- `src/trust_hn/phase7/__init__.py`
- `src/trust_hn/phase7/models.py`
- `src/trust_hn/phase7/runner.py`
- `scripts/run_phase7_exploratory.py`
- `tests/test_phase7_exploratory.py`

Aggregate results:

- `results/metrics/phase7_exploratory/development_metrics_by_seed.csv`
- `results/metrics/phase7_exploratory/development_metrics_summary.csv`
- `results/metrics/phase7_exploratory/external_metrics.csv`
- `results/metrics/phase7_exploratory/external_benchmark_combined.csv`
- `results/metrics/phase7_exploratory/paired_comparisons.csv`
- `results/figures/phase7_exploratory/development_comparison.svg`
- `results/figures/phase7_exploratory/external_comparator_forest.svg`
- `results/manifests/phase7_exploratory_prediction_receipt.json`
- `results/manifests/phase7_exploratory_receipt.json`

Patient-level development and external predictions remain under the Git-ignored `results/predictions/phase7_exploratory/` directory.

## 7. Verification and governance

- Eight new Phase 7 tests passed.
- Ninety-seven project tests passed after deselecting one historical pre-consumption test that conflicts with the current consumed Phase 6 outcome state. Running all 98 tests produces that single state-dependent failure because it still expects outcome access to be refused; the frozen Phase 6 test was not modified.
- Ruff checks passed on all new Phase 7 files.
- All 16 registered Phase 6 files matched their frozen hashes.
- No Phase 6 output was overwritten.
- B6/B7 and gate thresholds were not retuned.
- External outcomes were not used for method selection or tuning.
- All new external comparisons retain the post-hoc exploratory label.

## 8. Next step

The additional comparator requirement before writing is complete. The next project step is to freeze the interpretation boundary, build the dataset-method-metric-figure-claim evidence map, and then construct the manuscript outline and main-text/supplement allocation without further external-outcome-driven model selection or tuning.

