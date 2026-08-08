# TRUST-HN Project Status

**Last updated:** 2026-08-07
**Current gate:** Phase 5 complete and analysis configuration frozen; Phase 6 locked/external evaluation remains sealed and requires a separate explicit authorization.
**Sealed or external outcomes used for preprocessing, selection, tuning, calibration, thresholds, or evaluation:** No.

## Phase status

| Phase | Status | Evidence / decision |
|---|---|---|
| 0. Repository and governance | Complete | Governance, configuration, audit templates, reproducibility controls, and sealed-test refusal are implemented. |
| 1. Data acquisition and feasibility audit | Complete with conditions | Authorized artifacts were acquired, hashed, extracted, audited, manifested, and frozen read-only. |
| 2. Unified adapters and descriptive analysis | Complete with one modeling blocker | Unified records and aggregate descriptive outputs are complete; ORCESTRA RDS structural validation remains required for RADCURE radiomics. |
| 3. Baselines | Complete within authorized scope | Development-only clinical/modality/fusion baselines and negative controls were completed. |
| 4. TRUST-HN core | Complete within authorized scope | B6 stacked residual fusion and B7 reliability gating were completed for HANCOCK and TCGA-HNSC; RADCURE B6/B7 remained blocked. |
| 5. Stress tests and freeze | **Complete within authorized development-only scope** | 10/10 study-seed runs completed, 0 failed, 1 RADCURE blocker recorded; stress tests, gate ablations, coverage profiles, subgroup/worst-group analyses, sensitivity analyses, sealed cohort digests, and `analysis_freeze.yaml` were produced. |
| 6. Locked/external tests | **Sealed / not authorized** | RADCURE challenge-test, HANCOCK OOD-test, GSE65858, and GSE41613 outcomes remain unused. `test_unseal.approved` is `false`. |
| 7. Paper | Development-stage evidence available | Phase 3?5 methods/results can be drafted, but external robustness, prospective validity, deployability, and clinical utility cannot yet be claimed. |
| 8. Reproduction/submission | Not started | Final locked statistics and manuscript completion remain pending. |

## Phase 5 evidence snapshot

- Frozen design: seeds `17, 29, 43, 71, 101`; 20 bootstrap models per fit scope; coverage profiles 100%, 90%, and 80%; primary gate `full_equal_weight_90`.
- Completed runs: 5 HANCOCK plus 5 TCGA-HNSC; no failed run. RADCURE modality-dependent Phase 5 analysis is explicitly blocked.
- Clean full-cohort IPCW Brier means: HANCOCK B2 `0.1460`, B5 `0.1276`, B6 `0.1289`; TCGA-HNSC B2 `0.2422`, B5 `0.2482`, B6 `0.2442`.
- Primary B7 selective clean Brier/coverage: HANCOCK `0.1177` / `0.9016`; TCGA-HNSC `0.2324` / `0.9038`. These are selective metrics on non-abstained patients, not ordinary full-cohort improvements.
- Prespecified acceptance checks: **7 of 8 passed**. HANCOCK clean same-subset B7-vs-B6 Brier noninferiority failed (`+0.01550`, margin `+0.01000`); this was not used to switch the primary gate.
- Complete modality dropout produced 100% fallback at the 100% profile and exactly reproduced B2 Brier in both studies.
- Row-permutation negative control degraded B6 Brier from `0.1289` to `0.1530` in HANCOCK and `0.2442` to `0.2791` in TCGA-HNSC. The primary gate's fallback/abstain response rose only from `0.167` to `0.174` and `0.181` to `0.202`, respectively, indicating incomplete detection of semantic modality misalignment.
- Exploratory worst-group flagging found 2 of 85 seed/group evaluations above the 0.03 Brier-regret threshold; both were TCGA-HNSC age `>=65` evaluations (n=34) at seeds 29 and 71.
- No calibration-outcome threshold optimization or outcome-guided gate-weight switching was performed.

## Frozen configuration and governance

1. `configs/analysis_freeze.yaml` is `FROZEN` and records exact hashes of decision files plus the aggregate Phase 6 cohort-set manifest.
2. The frozen primary configuration remains `full_equal_weight_90`; learned-weight and 80%/100% profiles are sensitivity analyses.
3. `test_unseal.approved` remains `false`; the locked evaluator refuses execution without a separate approval token and matching hashes.
4. Phase 6 outcome sets are represented only by cohort name, role, count, and one ordered-ID-set SHA-256 digest; no individual identifiers or outcomes are present in tracked manifests.
5. Patient-level Phase 5 traces are confined to Git-ignored `results/predictions/phase5/`.

## Scientific interpretation limits

- Phase 5 provides **development-stage simulated-shift and missingness evidence**, not proof of real-world distribution-shift robustness.
- External validation, prospective validation, clinical utility, treatment impact, and deployment-ready thresholds remain unestablished.
- The HANCOCK clean noninferiority failure and TCGA-HNSC older-group flags must be reported without post hoc configuration switching.
- The weak gate response to row permutation is a material limitation and motivates explicit alignment/integrity checks and Phase 6 external evaluation.

## Verification status

- Canonical Phase 5 run: 10 successful study/seed runs, 0 failures, 1 blocked RADCURE entry.
- Full project unit tests: **64 passed**; two dependency deprecation warnings only.
- Phase 5 targeted Ruff and Python compilation checks: passed.
- Locked evaluation refusal: passed with `test_unseal.approved=false`.
- Patient traces: 10 canonical files, all Git-ignored.
- Final checkpoint passed: every aggregate receipt hash and every analysis-freeze decision/manifest hash matches the current file.
- Aggregate privacy checks passed: no patient/native/sample/subject/case identifier columns or recognizable TCGA/GEO identifiers were found; the sealed Phase 6 manifest contains counts and digests only.
- Deterministic SVG regeneration passed with exact SHA-256 matches for both Phase 5 figures. All intended tracked text files decode as UTF-8; three frozen authoring files retain a UTF-8 BOM and were intentionally not rewritten after freezing.

## Next checkpoint

Review the bilingual Phase 5 completion report and the frozen configuration. Do not run Phase 6 unless the user separately authorizes one-time locked/external evaluation after accepting the disclosed Phase 5 limitations.
