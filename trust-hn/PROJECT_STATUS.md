# TRUST-HN Project Status

**Last updated:** 2026-08-07
**Current gate:** Phase 4 complete within the user-authorized conditional scope; awaiting explicit review before Phase 5.
**Sealed or external outcomes used for preprocessing, selection, tuning, calibration, thresholds, or evaluation:** No.

## Phase status

| Phase | Status | Evidence / decision |
|---|---|---|
| 0. Repository and governance | Complete | Governance, configuration, templates, acquisition policy, and sealed-test refusal are implemented. |
| 1. Data acquisition and feasibility audit | Complete with conditions | Authorized artifacts acquired, hashed, extracted, audited, manifested, and frozen read-only. |
| 2. Unified adapters and descriptive analysis | Complete with one modeling blocker | Three adapters, unified contract/schema, aggregate descriptive outputs, and frozen development/sealed roles are complete. ORCESTRA RDS structural validation remains required before RADCURE radiomics modeling. |
| 3. Baselines | Complete within authorized conditional scope | 105 successful development-only runs, 0 failures, 10 diagnostic warnings, 3 blocked RADCURE radiomics entries, 210 Git-ignored patient prediction files, aggregate metrics/figures/audits/receipt, and 53 passing tests at the Phase 3 checkpoint. |
| 4. TRUST-HN core | Complete within authorized conditional scope | B6 stacked residual fusion and B7 reliability gating completed for HANCOCK and TCGA-HNSC: 10 successful study/seed runs, 0 failures, 1 blocked RADCURE entry, 1,200 clinical plus 1,200 B6 bootstrap fits, 20 Git-ignored decision traces, aggregate outputs, audits, and receipt. |
| 5. Stress tests and freeze | Not authorized | Natural/artificial missingness stress tests, shortcut perturbations, subgroup analysis, ablations, and analysis freeze were not entered. |
| 6. Locked/external tests | Sealed / not authorized | RADCURE challenge-test, HANCOCK OOD-test, GSE65858, and GSE41613 outcomes remain unavailable and unused. |
| 7. Paper | Skeleton only | Development-stage Phase 3 and Phase 4 findings may inform drafting, but robust/external claims and final conclusions remain unavailable. |
| 8. Reproduction/submission | Not started | Not started. |

## Phase 4 evidence snapshot

- Frozen design: five outer folds; seeds `17, 29, 43, 71, 101`; 20 bootstrap models per fit scope; 80% and 90% calibration-derived reliability profiles.
- B6 is an elastic-net Cox stacked residual learner using an inner cross-fitted B2 clinical-anchor score plus a training-derived modality representation; B5 direct fusion remains the comparator.
- B7 applies the frozen precedence `clinical unreliable -> ABSTAIN`, otherwise `modality missing/unreliable -> FALLBACK`, otherwise `AUGMENT`.
- HANCOCK calibration means: B2 Brier/Harrell C `0.1460/0.6328`; B5 `0.1276/0.6948`; B6 `0.1288/0.6756`.
- TCGA-HNSC calibration means: B2 Brier/Harrell C `0.2422/0.4898`; B5 `0.2482/0.6104`; B6 `0.2448/0.6182`.
- Calibration non-abstention coverage was `0.8033/0.9016` for HANCOCK and `0.8096/0.9038` for TCGA-HNSC under the 80%/90% profiles.
- Selective metrics apply only to non-abstained patients and are not ordinary full-cohort improvements.
- Patient-level traces are stored only in Git-ignored `results/predictions/phase4/`; intended tracked outputs are aggregate-only.
- Receipt: `results/manifests/phase4_trust_hn_receipt.json`.
- Findings audit: `docs/audits/phase4/core_findings.md`.
- Bilingual report: `docs/work_stage_reports/{en,zh-CN}/2026-08-07_phase4_completion_report.md`.

## Governance and interpretation limits

1. RADCURE challenge-test, HANCOCK OOD-test, GSE65858, and GSE41613 outcomes were not used.
2. Phase 4 used only frozen HANCOCK and TCGA-HNSC training/calibration rows; the studies were modeled separately.
3. RADCURE B6/B7 remain blocked until the ORCESTRA RDS modality structure is validated with R/Rscript or another validated parser.
4. Reliability thresholds are calibration-distribution quantiles and were not optimized with outcomes.
5. Selective Brier scores must not be compared as ordinary full-cohort improvements because ABSTAIN changes the evaluated population.
6. Phase 4 does not establish robustness under shift, external validity, prospective validity, clinical utility, or a deployable final threshold.
7. Phase 5 and Phase 6 were not entered.

## Verification status

- Full project tests: **57 passed**; two dependency deprecation warnings only.
- Phase 4 targeted tests: **4 passed**.
- Python compilation: passed.
- Phase 4-targeted Ruff checks: passed.
- `git diff --check`: passed at the Phase 4 experiment checkpoint.
- Twenty canonical patient traces confirmed Git-ignored.
- Aggregate identifier/header scans and receipt-hash verification passed at the Phase 4 experiment checkpoint.

## Next checkpoint

Review the bilingual Phase 4 completion report and `docs/audits/phase4/core_findings.md`, then make an explicit go/no-go decision for Phase 5. Phase 5 would test missingness, perturbation, subgroup, and ablation robustness and prepare an analysis freeze. Locked/external Phase 6 outcomes must remain sealed until that work is complete and separately authorized.
