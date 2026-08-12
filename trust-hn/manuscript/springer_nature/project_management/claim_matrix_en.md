# TRUST-HN WP1 Claim Matrix (English)

**Version date:** 2026-08-11  
**Status:** WP1 control document for later outlining, figures, and prose; not manuscript prose.  
**Row-level evidence index:** `project_management/evidence_map.csv`

## 1. Operating rules

1. Every manuscript number must first map to a unique `evidence_id`, source file, physical row, and—where applicable—95% CI source row in `evidence_map.csv`.
2. Phase 6 is the prespecified one-time locked/external retrospective analysis. Manuscript work must not retune, recalibrate, switch thresholds, or alter cohorts.
3. Every Phase 7 result must be labelled **post hoc exploratory** and must not be represented as a prespecified locked comparison.
4. Every Phase 8 `inner_hancock` result is a **known-overlap workflow/bias simulation**, preferably supplementary only; it is not independent institutional, private, or external validation.
5. B7 is selective prediction. Every B7 performance statement requires coverage, and direct comparisons with B6/B2 must use the identical B7 non-abstained subset.
6. GSE41613 is an HPV-negative OSCC sensitivity analysis, not general HNSCC external validation.
7. Decision-curve analysis is retrospective and exploratory; it does not establish clinical utility, clinical net benefit, patient benefit, or treatment value.
8. AUGMENT, FALLBACK, and ABSTAIN are algorithmic output categories, not treatment advice, triage instructions, or deployable workflow thresholds.

## 2. Status vocabulary

| `claim_status` | Meaning | Condition for manuscript use |
|---|---|---|
| `ALLOWED_WITH_ROLE_QUALIFIER` | Reportable retrospective evidence | State cohort, role, metric, sample size/coverage, and analysis nature |
| `DEVELOPMENT_ONLY` | Development, calibration, or development stress testing | Do not call external validation; do not imply precise inference when bootstrap CIs are unavailable |
| `SENSITIVITY_ONLY` | Restricted sensitivity evidence | State the HPV-negative OSCC applicability boundary |
| `POST_HOC_EXPLORATORY_ONLY` | Phase 7 exploratory evidence | Explicitly label every occurrence post hoc exploratory |
| `EXPLORATORY_NO_CLINICAL_UTILITY` | Exploratory DCA | Describe observed curves only; no clinical-utility claim |
| `ALLOWED_NEGATIVE_RESULT_NO_MODALITY_SPECIFICITY` | Negative-control evidence | “No clear superiority” is allowed; modality-specific biological signal is not |
| `OVERLAP_SIMULATION_ONLY_NOT_VALIDATION` | Phase 8 known-overlap simulation | Workflow, bias, and code-behaviour demonstration only |
| `GOVERNANCE_BOUNDARY` | Analysis-governance anchor | Defines interpretation; not model-performance evidence |

## 3. Allowed claims with mandatory qualifiers

| ID | Topic | Manuscript-safe statement | Mandatory qualifier | Core evidence |
|---|---|---|---|---|
| C01 | Cohort composition | RADCURE comprised 1,215 training, 303 calibration, and 626 locked-test cases; HANCOCK comprised 489 training, 122 calibration, and 152 sealed-test cases; TCGA-HNSC comprised 416 training and 104 calibration cases; GSE65858 contributed 244 external-test cases; and GSE41613 contributed 97 sensitivity cases. | Keep development, calibration, and test roles separate. | `P2-FLOW-R014`–`R027`; `cohort_flow.csv` |
| C02 | Phase 6 governance | Phase 6 completed prespecified one-time retrospective locked, OOD, external, and sensitivity evaluations with 2,000 paired bootstrap replicates. | Do not write “prospective”; do not imply outcome-guided tuning. | `GOV-ANCHOR-001`–`004`; Phase 6 receipt |
| C03 | RADCURE | In the RADCURE locked test, B6 had Brier 0.0980, Uno C 0.7740, and 24-month AUC 0.7838; B2 had 0.1091, 0.7078, and 0.7145, respectively. | This is a within-cohort descriptive contrast; do not convert unpaired absolute values into a definitive B6-vs-B2 superiority test. | `P6-ABS-R002-*`, `P6-ABS-R005-*` |
| C04 | HANCOCK | In the retrospective HANCOCK OOD test, B6 had Brier 0.1122, Uno C 0.8281, and 24-month AUC 0.8476; B2 had 0.1393, 0.7476, and 0.7864. | Restricted to this official OOD split; not all institutions or shifts. | `P6-ABS-R007-*`, `P6-ABS-R010-*` |
| C05 | GSE65858 failure boundary | GSE65858 exposed cross-platform transcriptomic calibration failure: B6 had Brier 0.2725, calibration-in-the-large −1.494, and slope 0.599; B7 had Brier 0.2672, calibration-in-the-large −1.548, and slope 0.560; B2 Brier was 0.1964. | Present calibration failure whenever discrimination is discussed; do not selectively report AUC/C indices. | `P6-ABS-R012-*`, `R015-*`, `R016-*` |
| C06 | GSE41613 | In the 97-case GSE41613 sensitivity cohort, B2 was constant/non-discriminating (Uno C and AUC 0.5); B6/B7 had higher discrimination point estimates, but Brier improvement was uncertain. | “HPV-negative OSCC sensitivity analysis” only; not general HNSCC external validation. | `P6-ABS-R017-*`, `R020-*`, `R021-*`; `P6-PAIR-R011`, `R012` |
| C07 | B7 coverage | Observed non-abstention coverage under the primary 90% gate was cohort dependent: 93.3% in RADCURE, 82.9% in HANCOCK, 94.3% in GSE65858, and 100.0% in GSE41613. | Every B7 absolute metric requires the corresponding coverage. | `P6-ABS-R006-*`, `R011-*`, `R016-*`, `R021-*`; Phase 6 actions |
| C08 | B7 vs B6 | B7 did not consistently outperform B6: paired Brier differences were +0.00382 (95% CI +0.00084 to +0.00718; n=584) in RADCURE, +0.01058 (−0.00947 to +0.03186; n=126) in HANCOCK, −0.00812 (−0.01584 to −0.00183; n=230) in GSE65858, and −0.01314 (−0.03153 to +0.00215; n=97) in GSE41613. | Identical non-abstained subsets; negative Brier difference favors the first-listed model; report coverage. | `P6-PAIR-R002`, `R005`, `R008`, `R011` |
| C09 | B7 vs clinical anchor | B7-vs-B2 results were also cohort dependent: paired Brier differences were −0.00489 in RADCURE, −0.00723 with a CI crossing zero in HANCOCK, +0.07294 in GSE65858, and −0.00632 with a CI crossing zero in GSE41613. | Do not summarize this as universal B7 superiority over the clinical model. | `P6-PAIR-R003`, `R006`, `R009`, `R012` |
| C10 | Gate actions | B7 generated AUGMENT, FALLBACK, and ABSTAIN outputs, with action proportions varying by cohort and coverage profile. | Algorithm behaviour only; not a clinical decision or validated safety intervention. | `P6-ACTION-*`; `action_summary.csv` |
| C11 | Phase 5 stress tests | Seven of eight prespecified Phase 5 checks passed. HANCOCK failed the clean B7-vs-B6 Brier noninferiority check (+0.01550 versus margin ≤0.01). Under complete modality dropout, the 100% profiles in HANCOCK and TCGA-HNSC reverted to B2 with fallback rate 1.0. | Development stress testing only; not proof of deployment safety or detection of every shift. | `P5-CHECK-R002`–`R009` |
| C12 | Exploratory subgroup warning | Two seed-level flags occurred in the TCGA-HNSC age ≥65 subgroup during the Phase 5 worst-group audit. | Exploratory, multiplicity-prone, and seed-specific; no fairness or causal claim. | `P5-FLAG-R055`, `P5-FLAG-R071` |
| C13 | Radiomics negative controls | For B4–B7, the 95% CIs for original-radiomics-minus-shuffled/randomized Brier differences crossed zero; original radiomics showed no clear superiority. | A negative result is reportable; radiomics-specific biological signal is not supported. | `P6-NEG-PAIR-*`; `radcure_negative_controls.csv` |
| C14 | Decision curves | Retrospective exploratory DCA showed no consistent B7 net-benefit advantage over B6: B7 was lower at all 10 thresholds in RADCURE and HANCOCK and at 8/10 thresholds in GSE65858. | No clinical utility, deployable threshold, treatment net benefit, or patient benefit claim. | `P6-DCA-*`; `decision_curve.csv` |
| C15 | Phase 7 comparators | Post hoc exploratorily, C2 performed strongly in RADCURE and HANCOCK (Brier 0.0907 and 0.1037) but markedly overpredicted/miscalibrated in GSE65858 (Brier 0.3429; calibration-in-the-large −1.935). | Label post hoc exploratory in the same sentence/paragraph and show the cross-cohort failure. | `P7-EXT-R003-*`, `R007-*`, `R011-*` |
| C16 | GSE65858 exploratory ranking | Among newly added methods in GSE65858, C3 had the lowest Brier (0.2050), but Phase 6 B2 remained lower (0.1964). | Do not call C3 statistically or universally “best” without the appropriate paired analysis and exploratory qualifier. | `P7-EXT-R012-IPCW-BRIER`; `P6-ABS-R012-IPCW-BRIER` |
| C17 | Cohort-dependent ranking | Strong comparators such as C2 excelled in some cohorts, but model rankings changed across data ecosystems; no uniformly winning model was established. | Cross-cohort synthesis, not a pooled treatment-effect estimate. | Phase 6 absolute/paired results; `P7-EXT-*`; `P7-PAIR-*` |
| C18 | Parameter-sharing boundary | Models were trained separately within clinical/modality ecosystems; the study evaluated a common reliability principle, not one universal shared-parameter HNSCC model. | State in Methods and Discussion. | Phase 6 report, frozen configurations, ecosystem-specific training records |
| C19 | Phase 8 | Simulation values may be reported, e.g., B2/B6/B7/C2 Brier 0.1011/0.0807/0.0873/0.0679 and B7 coverage 90.4%. | Immediately state that 135 cases include 88 training-, 17 calibration-, and 30 prior-test-overlap cases; workflow/bias demonstration only, preferably supplementary. | `P8-ABS-R004-*`, `R008-*`, `R009-*`, `R013-*`; `GOV-ANCHOR-007`–`011` |
| C20 | Overall conclusion | Multimodal gains, calibration, and gate behaviour were cohort dependent; fallback and abstention exposed failure modes of forced fusion, but current retrospective evidence did not establish universal robustness, deployable thresholds, or clinical utility. | Preserve positive, negative, and inconsistent findings together. | Synthesis of C03–C19 |

## 4. Wording that is acceptable only with qualification

| Avoid as a bare phrase | Acceptable alternative |
|---|---|
| “validated” | “evaluated in a prespecified retrospective locked/OOD/external analysis,” naming the cohort |
| “external validation” for GSE41613 | “restricted retrospective sensitivity analysis in HPV-negative OSCC” |
| “B7 improved performance” | “B7 changed coverage; on the identical non-abstained subset, the paired difference was …” |
| “robust to distribution shift” | “performance and calibration were cohort dependent, with failure in cross-platform GSE65858 transfer” |
| “clinical net benefit” | “retrospective exploratory decision-curve net-benefit estimate,” immediately followed by the no-clinical-utility boundary |
| “best model” | “lowest point-estimate Brier in this cohort/analysis,” with uncertainty and analysis nature |
| “private/institutional validation” for Phase 8 | “known-overlap pseudo-private workflow and bias simulation” |
| “safe fallback” | “algorithmic fallback behaviour,” without a patient-safety implication |

## 5. Prohibited claims

The following must not appear in the title, abstract, main text, captions, supplement, highlights, or cover letter:

1. TRUST-HN has demonstrated universal robustness across all shifts, platforms, or institutions.
2. This study completed prospective validation, a prospective trial, or real-world deployment validation.
3. The 90% gate—or any gate threshold—is deployable, generalizable, or clinically safe.
4. Decision curves prove clinical utility, clinical net benefit, treatment benefit, or patient benefit.
5. B7 outperforms B6, B2, or other comparators in every cohort.
6. C2, B6, B7, or any method is the universal best model across all ecosystems.
7. Original radiomics proves a radiomics-specific biological signal.
8. Phase 8 `inner_hancock` is independent institutional, private, external, or prospective validation.
9. A single shared parameter set produced a universal HNSCC model across cohorts.
10. AUGMENT/FALLBACK/ABSTAIN constitutes treatment, referral, follow-up, or triage advice.
11. Selective B7 absolute metrics prove improvement when coverage is omitted.
12. Phase 7 post hoc comparisons were prespecified, locked, primary, or confirmatory analyses.

## 6. Interface to WP2

For every planned Results paragraph, WP2 must list the claim ID, linked `evidence_id` values, cohort role, analysis nature, sample size, coverage, 95% CI, mandatory co-reported negative/limiting evidence, and main-text-versus-supplement destination. A result sentence missing any required field cannot progress to full prose.
