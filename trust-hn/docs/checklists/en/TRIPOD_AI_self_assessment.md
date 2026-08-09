# TRIPOD+AI Self-assessment for TRUST-HN

**Assessment date:** 2026-08-08  
**Scope:** Current retrospective manuscript package after Phase 6.  
**Status vocabulary:** Complete; Partial; Not yet complete; Not applicable.

This is a project self-assessment, not an independent endorsement. It is organized by reporting topic rather than reproducing the official checklist verbatim.

| Reporting topic | Status | Current evidence or required action |
|---|---|---|
| Title identifies prediction/AI context and condition | Complete | Working title names prognostic AI and HNSCC. |
| Structured abstract reports design, data, outcome, validation, performance and limitations | Partial | Numerical Phase 6 text is drafted; journal format remains pending. |
| Background explains clinical context and intended use | Partial | Retrospective reliability research is clear; exact workflow and target user need final text. |
| Objectives distinguish development, locked, OOD, external and sensitivity analyses | Complete | Cohort roles are explicit and must remain separate. |
| Data sources, repository accessions, dates and provenance | Partial | Local manifests exist; a manuscript-facing accession/version table remains needed. |
| Study setting and eligibility criteria | Partial | Cohort audits exist; final concise tables remain needed. |
| Participant flow and exclusions | Partial | Frozen counts are available; publication flow diagram and exclusion table are pending. |
| Index date, prediction time and outcome horizon | Partial | The 24-month horizon is fixed; ecosystem-specific index dates need prominent reporting. |
| Outcome definition and ascertainment | Partial | OS harmonization is implemented; source-specific ascertainment and censoring prose is pending. |
| Predictor definition and measurement timing | Partial | Feature policies are frozen; temporal availability must be summarized by cohort. |
| Identifier handling and leakage prevention | Complete | Patient splits, hash governance, outcome-free preflight and ignored patient outputs are tested. |
| Sample-size rationale | Partial | Available cohort/event counts are reported; no prospective sample-size calculation was possible. |
| Missing-data handling | Partial | Imputation, indicators and fallback are implemented; assumptions and missingness tables remain pending. |
| Preprocessing and feature selection | Complete | Training-derived, foldwise preprocessing was frozen before Phase 6 outcomes. |
| Model type, fitting and hyperparameters | Complete | B2/B4/B5/B6/B7, seeds and ensembles are documented. |
| Overfitting control/internal validation | Complete | Cross-fitting and fixed development/calibration/test roles are documented. |
| Output definition and prediction calculation | Partial | Risk/action definitions exist; concise end-user algorithm and model card remain pending. |
| Gate thresholds and rationale | Complete for retrospective protocol | Equal-weight nominal 90% gate was prespecified and is not deployable clinically. |
| External validation strategy | Complete | RADCURE locked, HANCOCK OOD, GSE65858 external and GSE41613 sensitivity roles are separated. |
| Performance measures | Complete | Brier, C indices, AUC, calibration, coverage, actions and DCA were prespecified. |
| Confidence intervals/resampling | Complete | 2,000 patient-level paired bootstrap replicates were used. |
| Selective-prediction denominator | Complete | Coverage is reported and B7 comparisons use identical non-abstained subsets. |
| Calibration reporting | Partial | Calibration-in-the-large and slope exist; publication calibration displays remain pending. |
| Clinical utility | Complete as retrospective analysis | DCA was generated, but it does not establish prospective utility. |
| Subgroup/fairness reporting | Partial | Development subgroup analyses and age flags exist; external power is limited. |
| Robustness, missingness and shortcut analyses | Complete | Phase 5 stress tests and Phase 6 RADCURE negative controls include failed findings. |
| Participant/outcome counts per analysis | Complete | Counts, events and B7 retained denominators are in aggregate outputs. |
| Full model specification/executable implementation | Partial | Local code exists; archival public release and stable version are pending. |
| Performance with uncertainty | Complete | Traceable point estimates and bootstrap intervals exist. |
| Model updating/recalibration | Not applicable | No Phase 6 outcome-guided update or recalibration was allowed or performed. |
| Interpretation distinguishes validation types and avoids optimism | Complete | Negative external/control findings and sensitivity-only status are explicit. |
| Limitations | Complete for Phase 6 draft | Retrospective design, gate inconsistency, controls, shift and non-deployability are stated. |
| Generalizability/applicability | Partial | Cohort-specific transportability is discussed; no prospective sites are available. |
| Practice implications/future research | Partial | Prospective validation is proposed; a detailed protocol remains a later deliverable. |
| Protocol/analysis-plan availability | Complete locally | Master plan, freeze and receipts exist; external registration is pending. |
| Data availability | Partial | Provenance exists; accession/licence and redistribution statements require finalization. |
| Code availability | Partial | Local reproducibility exists; public archive, DOI and clean-environment instructions are pending. |
| Funding, conflicts and contributions | Not yet complete | Await author-provided information. |
| Patient/public involvement | Not yet complete | No involvement is documented; this must be stated transparently if unchanged. |

## Overall assessment

Retrospective analytic reporting is substantially complete and auditable, especially for governance, cohort roles, modeling, selective prediction and uncertainty. Publication readiness remains **partial** because participant-flow presentation, manuscript-facing cohort dictionaries, calibration displays, author declarations, public code archiving and final data-access statements are incomplete. No item establishes clinical deployment readiness.
