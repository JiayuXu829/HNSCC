# TRUST-HN Project Status

**Last updated:** 2026-08-08  
**Current gate:** Phase 6 one-time retrospective locked/external evaluation complete; outcomes have been consumed and registered Phase 6 decision files must not be edited.  
**Outcome-guided preprocessing, selection, tuning, gate switching or recalibration performed:** No.

## Phase status

| Phase | Status | Evidence / decision |
|---|---|---|
| 0. Repository and governance | Complete | Repository, governance, reproducibility and sealed-test controls implemented. |
| 1. Data acquisition and audit | Complete with documented conditions | Authorized public artifacts acquired, hashed, audited and frozen. |
| 2. Unified adapters/descriptive analysis | Complete | Unified adapters, endpoint harmonization and aggregate descriptive audits completed. |
| 3. Baselines | Complete | Clinical, modality-only, direct-fusion and negative-control baselines completed. |
| 4. TRUST-HN core | Complete | Residual fusion (B6) and reliability gating (B7) implemented in the development ecosystems. |
| 5. Stress tests and freeze | Complete | 10/10 development runs completed; 7/8 prespecified checks passed; configuration frozen. |
| 6. Locked/external tests | **Complete** | RADCURE locked test, HANCOCK OOD test, GSE65858 external test and GSE41613 sensitivity analysis completed with 2,000 paired bootstrap replicates. |
| 7. Paper | In progress | Phase 6 methods/results, supplement, figure legends and reporting self-assessments drafted; references, author declarations, model card and final journal conversion remain pending. |
| 8. Reproduction/submission | Not started | Public archival release, independent clean-environment reproduction and submission package remain pending. |

## Phase 6 evidence snapshot

- Evaluation cohorts: RADCURE n=626; HANCOCK n=152; GSE65858 n=244; GSE41613 n=97.
- RADCURE B6: Brier `0.0980`, AUC `0.7838`. B7 coverage `93.3%`; on the same retained subset B7 was worse than B6 for Brier (`+0.00382`, 95% CI `+0.00084` to `+0.00718`).
- HANCOCK B6: Brier `0.1122`, AUC `0.8476`. B7 coverage `82.9%`; B7-vs-B6 Brier difference `+0.01058` (95% CI `-0.00947` to `+0.03186`).
- GSE65858: B7 reduced Brier relative to B6 (`-0.00812`) but was substantially worse than B2 (`+0.07294`), showing external calibration failure of transcriptomic fusion.
- GSE41613 is sensitivity evidence only; its B2 comparator was constant/non-discriminating.
- Original RADCURE radiomics did not clearly outperform shuffled or randomized controls; no radiomics-specific signal claim is supported.
- Primary 90% gate coverage: RADCURE `93.3%`, HANCOCK `82.9%`, GSE65858 `94.3%`, GSE41613 `100%`.
- Decision curves did not show a consistent B7 advantage over B6.

## Governance state

1. `phase6_outcomes_seen=true`.
2. `phase6_outcome_access_state=CONSUMED_FOR_LOCKED_EVALUATION`.
3. The one-time authorization was consumed on 2026-08-08.
4. Registered Phase 6 decision files and cohort digests pass hash verification.
5. No Phase 6 outcome-guided retuning, recalibration or threshold switching was performed.
6. Patient-level Phase 6 predictions are confined to Git-ignored `results/predictions/phase6/`.

## Binding interpretation limits

The project supports retrospective locked, OOD and external evaluation statements. It does **not** establish prospective validation, universal shift robustness, a deployable gate threshold, clinical utility, treatment benefit, a single universal model or radiomics-specific biological signal.

Phase 5 limitations remain visible: one HANCOCK noninferiority check failed, row permutation was weakly detected and two exploratory older-patient subgroup flags occurred.

## Verification status

- Registered configuration/decision hashes: 32/32 passed.
- Sealed manifest hash: 1/1 passed.
- Aggregate Phase 6 output hashes: 10/10 passed.
- Patient-level prediction files ignored: 48/48.
- Plaintext-token and aggregate identifier scans: passed.
- Phase 6 Python Ruff: passed.
- Repository-wide Ruff: 267 historical findings, not auto-fixed because earlier code is frozen.
- Tests: 90 passed at the implementation checkpoint. In the final post-consumption state, 89 passed and one frozen pre-consumption refusal test is state-obsolete; an isolated pre-consumption guard simulation passed. See `docs/audits/phase6/phase6_final_audit.md`.

## Next checkpoint

Proceed to Phase 7 only with explicit authorization. Phase 7 should finalize literature-backed Introduction/Discussion, references, model card, data/code statements, prospective validation protocol, Springer Nature LaTeX conversion and submission-quality tables/figures. Phase 6 outcomes must not be used for retuning.
