# TRUST-HN Phase 5 Completion Report

**Date:** 2026-08-07  
**Phase:** Development stress tests, ablations, subgroup analysis, and analysis freeze  
**Decision:** Complete within the user-authorized development-only scope; Phase 6 remains sealed and unauthorized.

## 1. What Phase 5 completed

Phase 5 implemented and executed the prespecified development-only evaluation program for HANCOCK and TCGA-HNSC. It compared B2/B4/B5/B6, four reliability-gate variants, three coverage profiles (100%, 90%, and 80%), common and study-specific missingness/perturbation scenarios, a row-permutation negative control, subgroup and worst-group analyses, and representation/imputation sensitivities. The workflow then froze the primary configuration and created aggregate Phase 6 cohort-set digests without inspecting locked outcomes.

The canonical run completed all 10 authorized study/seed combinations (2 studies x 5 seeds) with no failure. Each fit scope used 20 bootstrap models. RADCURE modality-dependent analyses were recorded as blocked because the ORCESTRA RDS structure remains unvalidated.

## 2. Frozen method

- **B2:** clinical elastic-net Cox anchor.
- **B4:** modality-only elastic-net Cox model.
- **B5:** direct early fusion of clinical and modality features.
- **B6:** stacked residual elastic-net Cox learner using a cross-fitted B2 anchor score and a training-derived modality representation.
- **B7:** reliability-gated decision layer with precedence: unreliable clinical input -> `ABSTAIN`; otherwise missing/unreliable modality -> `FALLBACK` to B2; otherwise -> `AUGMENT` with B6.

The frozen primary configuration is the **full equal-weight gate at nominal 90% calibration coverage**. The 80% and 100% profiles, OOD-only and uncertainty-only variants, and learned nonnegative weights are sensitivity analyses. Learned weights used training OOF prediction errors only; calibration outcomes were not used to optimize thresholds or choose a more favorable gate.

## 3. Experiments performed

Common scenarios were clean data, 10% and 30% random cell dropout, 0.5-SD measurement noise, 1-SD location shift on a feature subset, row-permutation negative control, and complete modality dropout. HANCOCK additionally tested blood-block dropout, TMA-block dropout, combined blood/TMA dropout, and oropharynx-targeted TMA dropout. TCGA-HNSC additionally tested within-sample rank representation. HANCOCK also tested median imputation without explicit missing indicators.

Subgroup analyses covered sex, age group, site, stage, HPV group, and natural modality missingness subject to minimum n=20 and minimum events=5. All tracked outputs are aggregate; patient-level traces are stored only in a Git-ignored directory.

## 4. Main quantitative findings

| Study | B2 clean Brier | B5 clean Brier | B6 clean Brier | Primary B7 selective Brier | B7 coverage |
|---|---:|---:|---:|---:|---:|
| HANCOCK | 0.1460 | 0.1276 | 0.1289 | 0.1177 | 0.9016 |
| TCGA-HNSC | 0.2422 | 0.2482 | 0.2442 | 0.2324 | 0.9038 |

The B7 values are selective metrics on non-abstained patients and cannot be read as ordinary full-cohort gains.

Seven of eight prespecified study-level acceptance checks passed. HANCOCK failed the clean same-subset B7-versus-B6 Brier noninferiority check: `+0.01550` versus an allowed margin of `+0.01000`. TCGA-HNSC passed the corresponding check with `-0.01329`. Both studies achieved a complete-dropout fallback rate of 1.0 at the 100% profile and exactly reproduced B2 Brier. Both passed the prespecified severe-shift action-response check.

The learned-weight gate looked more favorable on some development metrics, especially in HANCOCK, but it was not promoted because the protocol froze equal-weight 90% as primary and prohibited outcome-guided switching.

## 5. Important negative and subgroup findings

The row-permutation control exposed a material limitation. B6 Brier worsened from 0.1289 to 0.1530 in HANCOCK and from 0.2442 to 0.2791 in TCGA-HNSC. Yet the primary gate's fallback-plus-abstain rate increased only from 0.167 to 0.174 in HANCOCK and from 0.181 to 0.202 in TCGA-HNSC. Thus, the gate handles complete absence well but does not detect every semantic modality-alignment failure.

Among 85 eligible seed/group comparisons, 2 exceeded the exploratory 0.03 Brier-regret threshold versus B2. Both flags occurred in the TCGA-HNSC age >=65 subgroup (n=34) at seeds 29 and 71. This is a stability/fairness signal requiring explicit reporting and later validation, not proof of subgroup harm.

## 6. Freeze and governance outputs

`configs/analysis_freeze.yaml` is now `FROZEN` and records SHA-256 hashes for all decision files plus the aggregate sealed-cohort manifest. The primary gate is `full_equal_weight_90`; primary hypotheses, models, and thresholds are marked frozen. `test_unseal.approved` remains `false`.

The Phase 6 manifest records only cohort name, role, patient count, one ordered-ID-set digest, and source-adapter hash for RADCURE challenge test (626), HANCOCK OOD test (152), GSE65858 external test (244), and GSE41613 sensitivity cohort (97). It contains no individual identifiers or outcomes.

## 7. Verification evidence

- Canonical experiment: 10 successful runs, 0 failed, 1 blocked RADCURE entry.
- Full project test suite: 64 tests passed; two dependency deprecation warnings only.
- Targeted Phase 5 Ruff and compile checks: passed.
- Locked evaluator: confirmed to refuse execution because unseal approval is false.
- Patient traces: 10 canonical files, all Git-ignored.
- Aggregate outputs: 1,585 stress metric rows, 3,240 action rows, 255 subgroup metric rows, 85 worst-group regret rows, and 45 representation-sensitivity rows.

## 8. What may and may not be claimed

Phase 5 supports a cautious development-stage statement that the reliability layer responded to complete modality loss and several synthetic perturbations while providing explicit fallback and abstention. It does not prove robustness under real distribution shift. External validation, prospective validation, deployment-ready thresholds, and clinical utility are still unestablished. The HANCOCK noninferiority failure, weak row-permutation detection, and TCGA older-group flags must remain visible in the manuscript.

## 9. Next gate

Phase 6 must not start automatically. It requires a separate explicit user authorization, an approval token, matching freeze and sealed-manifest hashes, and a one-time locked/external evaluation. Until that authorization is given, all locked and external outcomes remain sealed.
