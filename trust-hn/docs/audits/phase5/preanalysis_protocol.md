# TRUST-HN Phase 5 prespecified stress-test and analysis-freeze protocol

**Protocol date:** 2026-08-07  
**Authorization:** User-approved Phase 5 only  
**Outcome boundary:** Development training/calibration outcomes only; all Phase 6 locked/external outcomes remain sealed.

## Primary objective

Determine whether the frozen Phase 4 reliability signals respond in the intended direction under prespecified missingness, measurement, shortcut, and distribution perturbations, and whether the reliability-gated policy limits harm relative to compulsory fusion. This phase is a development stress test, not external validation and not proof of universal robustness.

## Frozen primary configuration

- B2 clinical elastic-net Cox anchor.
- B6 stacked residual elastic-net Cox fusion.
- B7 action precedence: clinical unreliable -> ABSTAIN; otherwise modality missing/unreliable -> FALLBACK; otherwise AUGMENT.
- Equal-weight empirical-percentile reliability score.
- Primary gate profile: 90% calibration-derived non-abstention coverage.
- Sensitivity profiles: 80% and 100%.
- Five seeds: 17, 29, 43, 71, 101.
- Twenty bootstrap models per fit scope.
- Twenty-four-month overall-survival horizon (730.5 days).

Thresholds are quantiles of calibration reliability scores. Calibration outcomes will not be used to tune thresholds.

## Prespecified comparisons

1. Clinical anchor B2, modality-only B4, direct fusion B5, residual fusion B6, and gated B7.
2. No gate, OOD-only gate, bootstrap-uncertainty-only gate, full equal-weight gate, and a sensitivity gate whose nonnegative component weights are learned from training OOF errors only.
3. Clean calibration versus artificial cell dropout, block dropout, complete modality dropout, measurement noise, location shift, and row-permutation negative control.
4. HANCOCK natural missingness, blood/TMA block loss, and an outcome-free oropharynx-targeted shortcut perturbation.
5. TCGA gene-level representation versus within-sample rank representation. Hallmark/Reactome comparisons are unavailable because gene-set resources were not frozen before this analysis.
6. Prespecified subgroup and worst-group summaries with minimum n=20 and minimum events=5.

## Perturbation rules

All perturbations are deterministic functions of the frozen seed and are applied only to calibration predictors after fitting preprocessors and models on training rows.

- Random cell dropout: replace 10% or 30% of modality cells with missing values.
- Measurement noise: add zero-mean Gaussian noise with standard deviation 0.5 times the training-column standard deviation.
- Location shift: add one training-column standard deviation to a deterministic 30% of modality columns.
- Row permutation: permute modality rows while retaining clinical rows and outcomes; this is a negative-control shortcut test.
- Complete dropout: set every additional-modality value to missing.
- HANCOCK block dropout: remove blood, TMA, or both blocks in 30% of calibration rows.
- HANCOCK targeted shortcut: remove TMA for the prespecified oropharynx subgroup without using outcomes.

## Metrics

- IPCW Brier score, Harrell C, Uno C, 24-month cumulative/dynamic AUC, calibration-in-the-large, and calibration slope.
- AUGMENT/FALLBACK/ABSTAIN rates and non-abstention coverage.
- Selective metrics calculated only among non-abstained patients, explicitly labeled as selective.
- Perturbation detection: changes in clinical/modality unreliability and fallback/abstention rates relative to clean calibration.
- Subgroup n, events, coverage, Brier score, and worst-group range.

## Acceptance checks

These checks are descriptive development gates, not confirmatory proof.

1. On clean calibration, primary B7 selective Brier is no more than 0.01 worse than B6 on the identical non-abstained subset.
2. Under complete modality dropout, the 100% B7 policy falls back in at least 90% of patients and its full-cohort Brier is no more than 0.01 worse than B2.
3. Severe perturbations increase fallback/abstention response by at least 0.10 relative to clean calibration.
4. Worst-group Brier regret versus B2 greater than 0.03 is flagged exploratorily.

Failures will be reported; the primary threshold will not be switched after seeing results.

## Analysis freeze rule

After all Phase 5 outputs and audits pass, `configs/analysis_freeze.yaml` may be changed from DRAFT to FROZEN with hashes for all decision-bearing configs and aggregate sealed-cohort manifests. The unseal record must remain `approved: false` until a separate explicit Phase 6 authorization and one-time token are provided. No locked/external outcome may be accessed in Phase 5.
