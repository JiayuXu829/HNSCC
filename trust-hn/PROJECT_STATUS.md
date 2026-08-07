# TRUST-HN Project Status

**Last updated:** 2026-08-07
**Current gate:** Phase 3 complete within the user-authorized conditional scope; awaiting explicit review before Phase 4.
**Sealed or external outcomes used for preprocessing, selection, tuning, calibration, thresholds, or evaluation:** No.

## Phase status

| Phase | Status | Evidence / decision |
|---|---|---|
| 0. Repository and governance | Complete | Governance, configuration, templates, acquisition policy, and sealed-test refusal are implemented. |
| 1. Data acquisition and feasibility audit | Complete with conditions | Authorized artifacts acquired, hashed, extracted, audited, manifested, and frozen read-only. |
| 2. Unified adapters and descriptive analysis | Complete with one modeling blocker | Three adapters, unified contract/schema, aggregate descriptive outputs, and frozen development/sealed roles are complete. ORCESTRA RDS structural validation remains required before RADCURE radiomics modeling. |
| 3. Baselines | Complete within authorized conditional scope | 105 successful development-only runs, 0 failures, 10 diagnostic warnings, 3 blocked RADCURE radiomics entries, 210 Git-ignored patient prediction files, aggregate metrics/figures/audits/receipt, and 53 passing tests. |
| 4. TRUST-HN core | Not authorized | Requires explicit user authorization after Phase 3 review. No residual learner, reliability gate, or AUGMENT/FALLBACK/ABSTAIN threshold has been implemented. |
| 5. Stress tests and freeze | Not authorized | Not started. |
| 6. Locked/external tests | Sealed | Must remain unavailable for tuning and may be evaluated only after analysis freeze and explicit approval. |
| 7. Paper | Skeleton only | Phase 3 development findings may inform drafting, but locked/external results and final claims remain unavailable. |
| 8. Reproduction/submission | Not started | Not started. |

## Phase 3 evidence snapshot

- Prespecified five-seed, five-fold patient-level OOF evaluation and dedicated calibration-partition prediction.
- B0 Kaplan-Meier, B1 CoxPH, B2 elastic-net Cox, B3 random survival forest, B4 modality-only elastic-net Cox, B5 direct-fusion elastic-net Cox, M0 missingness-only, and N0 permuted-modality control where authorized and available.
- RADCURE: 25 successful clinical/control runs. Clinical B3 is strongest on calibration (IPCW Brier 0.1380; Harrell C 0.7525; 24-month AUC 0.7969). B4/B5/N0 remain blocked.
- HANCOCK: 40 successful runs. Direct clinical-plus-blood/TMA B5 is strongest on calibration (IPCW Brier 0.1276; Harrell C 0.6948; AUC 0.7873); N0 is near the event-rate reference.
- TCGA-HNSC: 40 successful runs. Expression-only B4 has the best calibration discrimination (Harrell C 0.6266; AUC 0.6293), while clinical B3 has the best Brier (0.2301); direct fusion B5 does not dominate.
- Metrics include IPCW Brier, Harrell/Uno C-index, dynamic AUC, calibration diagnostics, and IPCW decision-curve analysis.
- Patient-level predictions are stored only in Git-ignored `results/predictions/phase3/`; tracked outputs are aggregate-only.
- Receipt: `results/manifests/phase3_baseline_receipt.json`.
- Findings audit: `docs/audits/phase3/baseline_findings.md`.
- Bilingual report: `docs/work_stage_reports/{en,zh-CN}/2026-08-07_phase3_completion_report.md`.

## Governance and interpretation limits

1. RADCURE challenge-test, HANCOCK OOD-test, GSE65858, and GSE41613 outcomes were not used.
2. Preprocessing and TCGA top-500 variance selection were fit inside each OOF training fold; calibration data did not fit model parameters.
3. RADCURE B4/B5/N0 remain unavailable until the ORCESTRA RDS is structurally validated with R/Rscript or another validated parser.
4. Calibration slopes for constant-risk and negative-control models may be undefined or unstable and must not be overinterpreted.
5. Phase 3 decision curves are descriptive; they do not authorize treatment or reliability thresholds.
6. All Phase 3 findings are development-only and are not locked, external, prospective, or clinical-utility evidence.

## Verification status

- Full project tests: **53 passed**; two dependency deprecation warnings only.
- Python compilation: passed.
- Phase 3-targeted Ruff checks: passed.
- Repository-wide Ruff still reports 271 pre-existing style findings in older Phase 0-2 code; no repository-wide Ruff success is claimed.
- Patient prediction ignore rule and tracked-output identifier/header scans: passed.

## Next checkpoint

Review the bilingual Phase 3 completion report and `docs/audits/phase3/baseline_findings.md`, then make an explicit go/no-go decision for Phase 4. A Phase 4 GO would need to define the exact residual-learning, reliability/OOD/uncertainty, and threshold-selection boundary while continuing to prohibit locked/external outcome use until analysis freeze and separate authorization.
