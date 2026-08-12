# TRUST-HN WP2 Paragraph-Level Paper Outline (English)

**Version date:** 2026-08-12
**Status:** story-driven WP2 outline; not submission-ready manuscript prose.
**Constraint:** all result numbers and claims are governed by `evidence_map.csv`, `claim_matrix_en.md`, and `argument_map.md`.
**Approval boundary:** no full prose, changes to `main.tex`, WP3 work, or figure production are authorized until this outline is approved.

## 0. Title, short title, and central question

- **Leading provisional title:** TRUST-HN: Reliability-aware multimodal prognostic modelling reveals cohort-dependent gains and failure boundaries in head and neck cancer
- **Alternative title A:** TRUST-HN: Clinical anchoring and reliability gating for multimodal prognosis across heterogeneous HNSCC data ecosystems
- **Alternative title B:** TRUST-HN: When multimodal prognostic information helps—and fails—across heterogeneous head and neck cancer cohorts
- **Provisional short title:** TRUST-HN multimodal prognosis
- **Central question:** Across heterogeneous retrospective HNSCC data ecosystems, when does multimodal information add credible prognostic value beyond a clinical anchor, when does transfer fail, and can reliability-aware fallback or abstention make those conditions explicit?
- **Central thesis:** Multimodal information is not intrinsically superior to clinical information; its prognostic value is conditional on the data ecosystem and transfer setting. TRUST-HN contributes an auditable formulation of those conditional gains through clinical anchoring, reliability-aware augmentation, fallback, and abstention.

## 1. Abstract functional units

### ABS-01 — Background and scientific gap

- **Question answered:** Why is adding more modalities not a sufficient objective for multimodal HNSCC prognosis?
- **Core content:** Additional modalities may add information but may also introduce missingness, shortcut signals, platform differences, and calibration error; the relevant question is when they improve on a clinical anchor.
- **Evidence interface:** C01 and C18.
- **Limitation:** Do not presuppose multimodal superiority or modality-specific biological signal.

### ABS-02 — Design and analytical logic

- **Question answered:** How did TRUST-HN test conditional incremental value?
- **Core content:** B2 served as the clinical anchor, B6 as forced incremental fusion, and B7 as reliability-aware selective prediction. They were evaluated in prespecified Phase 6 retrospective locked, OOD, cross-platform external, and restricted sensitivity settings using 2,000 paired bootstrap replicates.
- **Evidence interface:** C01, C02, C18; `GOV-ANCHOR-001`, `GOV-ANCHOR-002`, `GOV-ANCHOR-003`, `GOV-ANCHOR-004`.
- **Limitation:** Not prospective; models were fitted separately by ecosystem rather than as one universal shared-parameter HNSCC model.

### ABS-03 — Principal mixed results

- **Question answered:** Where did multimodal fusion help, where did it fail, and did gating rescue it?
- **Core content:** B6 showed favourable retrospective point estimates in RADCURE and HANCOCK, but GSE65858 exposed substantial cross-platform Brier and calibration failure. B7 changed coverage and action distributions without consistently outperforming B6 and remained clearly worse than B2 in GSE65858.
- **Evidence interface:** C03–C10; `P6-ABS-R002-IPCW-BRIER`, `P6-ABS-R005-IPCW-BRIER`, `P6-ABS-R007-IPCW-BRIER`, `P6-ABS-R010-IPCW-BRIER`, `P6-ABS-R012-IPCW-BRIER`, `P6-ABS-R015-IPCW-BRIER`, `P6-PAIR-R002`, `P6-PAIR-R005`, `P6-PAIR-R008`, `P6-PAIR-R009`, `P6-PAIR-R011`.
- **Limitation:** Co-report B7 coverage; GSE41613 is restricted to an HPV-negative OSCC sensitivity analysis.

### ABS-04 — Restrained conclusion

- **Question answered:** What contribution does the evidence support?
- **Core content:** TRUST-HN makes conditional multimodal gains and failure boundaries auditable rather than establishing a universally superior or deployable model. Falsification analyses and Phase 7 post hoc exploratory comparisons further constrain overinterpretation.
- **Evidence interface:** C11–C18 and C20; `P5-CHECK-R002`, `P6-NEG-PAIR-R025`, `P6-DCA-*`, `P7-EXT-R003-IPCW-BRIER`, `P7-EXT-R011-IPCW-BRIER`, `P7-EXT-R012-IPCW-BRIER`.
- **Limitation:** No universal robustness, prospective validity, deployable threshold, clinical utility, or patient-benefit claim.

## 2. Introduction paragraph plan

### INT-01 — From “more modalities” to credible incremental value

- **Paragraph task:** Establish that HNSCC prognostic data are heterogeneous and that adding modalities cannot be assumed to yield transferable gains.
- **Narrative function:** Reframe the problem from technical accumulation to conditional value beyond a clinical reference.
- **Limitation:** Do not preview a performance winner or imply intrinsic multimodal superiority.

### INT-02 — Why a clinical anchor is necessary

- **Paragraph task:** Explain that clinical data are comparatively available and interpretable and provide the reference required to decide whether additional modalities contribute genuine incremental information.
- **Narrative function:** Define B2 as the scientific anchor, not merely one baseline among many.
- **Evidence interface:** C18.
- **Limitation:** The clinical anchor is not presumed universally best; it is the reference that every incremental claim must confront.

### INT-03 — TRUST-HN as a reliability design principle

- **Paragraph task:** Introduce clinical anchoring, incremental/residual fusion, reliability assessment, and AUGMENT/FALLBACK/ABSTAIN algorithmic outputs.
- **Narrative function:** Explain why the framework contains both B6 and B7: B6 tests forced fusion, whereas B7 reveals when forced fusion should not be trusted automatically.
- **Evidence interface:** C18; `GOV-ANCHOR-001`, `GOV-ANCHOR-002`, `GOV-ANCHOR-003`, `GOV-ANCHOR-004`.
- **Limitation:** The actions are algorithmic behaviours, not clinical decisions or treatment recommendations.

### INT-04 — Study objectives and intended contribution

- **Paragraph task:** State the objectives: evaluate conditional multimodal value, cross-ecosystem failure, the auditability of reliability gating, and falsification evidence that limits stronger claims.
- **Narrative function:** Establish the question order used by the five Results units rather than list experiments chronologically.
- **Evidence interface:** C02 and C20.
- **Limitation:** Phase 7 must be labelled post hoc exploratory.

## 3. Results narrative structure

> **Writing rule:** Results will not follow the order in which Phase 2, 5, 6, and 7 files were generated. They will advance one argument: where incremental value appeared, where it failed, what gating revealed, which interpretations were falsified, and whether rankings remained stable across ecosystems.

### RES-01 — Heterogeneous ecosystems form a prespecified test of conditional multimodal value

- **Question answered:** Why do the cohorts jointly test one scientific hypothesis rather than represent unrelated datasets?
- **Claim IDs:** C01, C02, C18.
- **Linked evidence_id values:** `P2-FLOW-R014`, `P2-FLOW-R015`, `P2-FLOW-R016`, `P2-FLOW-R021`, `P2-FLOW-R022`, `P2-FLOW-R023`, `P2-FLOW-R026`, `P2-FLOW-R027`, `GOV-ANCHOR-001`, `GOV-ANCHOR-002`, `GOV-ANCHOR-003`, `GOV-ANCHOR-004`.
- **Cohort role:** RADCURE was the same-ecosystem locked test; HANCOCK was retrospective OOD; GSE65858 was cross-platform external testing; GSE41613 was a restricted sensitivity analysis; TCGA-HNSC was transcriptomic development/calibration only.
- **Analysis nature:** Prespecified one-time Phase 6 retrospective locked/OOD/external/sensitivity evaluation.
- **Sample size:** RADCURE 1,215/303/626; HANCOCK 489/122/152; TCGA-HNSC 416/104; GSE65858 n=244; GSE41613 n=97.
- **Coverage:** B7 performance coverage is intentionally deferred to RES-03.
- **95% CI:** Not applicable to this design and cohort-flow unit.
- **Core interpretation:** The cohort roles create escalating transfer difficulty and therefore make ecosystem dependence of multimodal gains the unifying test.
- **Mandatory negative/limiting evidence:** Keep training, calibration, and test roles separate; models were fitted by ecosystem and do not constitute one universal shared-parameter model.
- **Provisional display:** Figure 1 for the framework and Figure 2/Table 1 for cohort flow and roles.
- **Destination:** Core roles and sample sizes in the main text; complete eligibility, exclusions, missingness, and endpoint accounting in Supplement.

### RES-02 — Multimodal fusion gains in RADCURE and HANCOCK but fails in GSE65858

- **Question answered:** Did B6 retain incremental value across data ecosystems?
- **Claim IDs:** C03, C04, C05, C06.
- **Linked evidence_id values:** `P6-ABS-R002-IPCW-BRIER`, `P6-ABS-R005-IPCW-BRIER`, `P6-ABS-R007-IPCW-BRIER`, `P6-ABS-R010-IPCW-BRIER`, `P6-ABS-R012-IPCW-BRIER`, `P6-ABS-R015-IPCW-BRIER`, `P6-ABS-R015-CALIBRATION-IN-THE-LARGE`, `P6-ABS-R015-CALIBRATION-SLOPE`, `P6-ABS-R016-IPCW-BRIER`, `P6-ABS-R016-CALIBRATION-IN-THE-LARGE`, `P6-ABS-R016-CALIBRATION-SLOPE`, `P6-ABS-R017-IPCW-BRIER`, `P6-ABS-R020-IPCW-BRIER`, `P6-ABS-R021-IPCW-BRIER`.
- **Cohort role:** RADCURE locked testing, HANCOCK retrospective OOD testing, GSE65858 cross-platform external testing, and restricted retrospective GSE41613 HPV-negative OSCC sensitivity analysis.
- **Analysis nature:** Prespecified Phase 6 retrospective absolute performance evaluation; the RADCURE B2/B6 absolute contrast is descriptive.
- **Sample size:** RADCURE n=626; HANCOCK n=152; GSE65858 n=244; GSE41613 n=97.
- **Coverage:** B2 and B6 had 100% coverage; any B7 absolute result in this unit must include GSE65858 coverage of 94.3%.
- **95% CI:** Main tables retain 95% CIs for IPCW Brier, Uno C, 24-month AUC, and essential calibration metrics; unpaired absolute contrasts are not converted into definitive superiority claims.
- **Core interpretation:** RADCURE B2/B6 Brier values were 0.1091/0.0980 and HANCOCK values were 0.1393/0.1122, providing the favourable opening. The central turn was GSE65858, where B2/B6/B7 Brier values were 0.1964/0.2725/0.2672; B6 calibration-in-the-large was −1.494 with slope 0.599, and B7 values were −1.548 and 0.560. GSE41613 closes the unit as restricted and uncertain sensitivity evidence.
- **Mandatory negative/limiting evidence:** Any discrimination result in GSE65858 must be accompanied by the calibration failure; GSE41613 is not general HNSCC external validation.
- **Provisional display:** Figure 3 for cross-ecosystem absolute performance and calibration, plus Table 2.
- **Destination:** Core B2/B6/B7 metrics in the main text; complete model and metric panels in Supplement.

### RES-03 — Reliability gating makes forced-fusion risk visible but does not guarantee superiority

- **Question answered:** What did B7 add, and did it outperform B6 on the same patients?
- **Claim IDs:** C07, C08, C09, C10.
- **Linked evidence_id values:** `P6-ABS-R006-IPCW-BRIER`, `P6-ABS-R011-IPCW-BRIER`, `P6-ABS-R016-IPCW-BRIER`, `P6-ABS-R021-IPCW-BRIER`, `P6-PAIR-R002`, `P6-PAIR-R003`, `P6-PAIR-R005`, `P6-PAIR-R006`, `P6-PAIR-R008`, `P6-PAIR-R009`, `P6-PAIR-R011`, `P6-PAIR-R012`, `P6-ACTION-*`.
- **Cohort role:** All four Phase 6 evaluation cohorts under the primary 90% gate profile.
- **Analysis nature:** Prespecified selective-prediction analysis; every direct comparison uses the identical non-abstained subset.
- **Sample size:** RADCURE 584/626; HANCOCK 126/152; GSE65858 230/244; GSE41613 97/97.
- **Coverage:** 93.3%, 82.9%, 94.3%, and 100.0%. AUGMENT/FALLBACK/ABSTAIN proportions were 82.1/11.2/6.7% in RADCURE, 64.5/18.4/17.1% in HANCOCK, 92.6/1.6/5.7% in GSE65858, and 95.9/4.1/0% in GSE41613.
- **95% CI:** Paired B7-minus-B6 Brier differences were +0.00382 (+0.00084 to +0.00718) in RADCURE, +0.01058 (−0.00947 to +0.03186) in HANCOCK, −0.00812 (−0.01584 to −0.00183) in GSE65858, and −0.01314 (−0.03153 to +0.00215) in GSE41613. GSE65858 B7-minus-B2 was +0.07294 (+0.04250 to +0.10389).
- **Core interpretation:** The gate succeeded mainly by exposing coverage and actions, not by guaranteeing improved accuracy: B7 was worse than B6 in RADCURE, uncertain in HANCOCK and GSE41613, and better than B6 in GSE65858 while remaining clearly worse than clinical anchor B2.
- **Mandatory negative/limiting evidence:** Do not compare unequal patient sets; negative Brier differences favour the first-listed model; algorithmic actions are not clinical decisions.
- **Provisional display:** Figure 4 for risk–coverage and actions, and Table 3 for paired differences.
- **Destination:** Primary 90% profile in the main text; 80% and 100% profiles and full action tables in Supplement.

### RES-04 — Falsification analyses limit mechanistic, robustness, and clinical interpretations

- **Question answered:** Can favourable performance be interpreted as modality specificity, universal robustness, or clinical utility?
- **Claim IDs:** C11, C12, C13, C14.
- **Linked evidence_id values:** `P5-CHECK-R002`, `P5-CHECK-R003`, `P5-CHECK-R004`, `P5-CHECK-R005`, `P5-CHECK-R006`, `P5-CHECK-R007`, `P5-CHECK-R008`, `P5-CHECK-R009`, `P5-FLAG-R055`, `P5-FLAG-R071`, `P6-NEG-PAIR-R025`, `P6-NEG-PAIR-R029`, `P6-NEG-PAIR-R041`, `P6-NEG-PAIR-R045`, `P6-DCA-*`.
- **Cohort role:** Phase 5 development stress testing and subgroup audit; RADCURE radiomics negative controls; retrospective exploratory DCA across four evaluation cohorts.
- **Analysis nature:** Development stress tests, exploratory subgroup checks, prespecified negative controls, and retrospective exploratory decision-curve analysis.
- **Sample size:** Phase 5 denominators follow the development files; the TCGA-HNSC age ≥65 warning cells had n=34; DCA used evaluable cases in each cohort.
- **Coverage:** Subgroup warning coverage was 82.4% and 76.5%; negative controls and DCA retain the corresponding model coverage.
- **95% CI:** B6 original-minus-shuffled Brier was +0.00124 with a CI crossing zero and B7 was −0.00130 with a CI crossing zero; B6 original-minus-randomized was +0.00063 with a CI crossing zero and B7 was −0.00026 with a CI crossing zero.
- **Core interpretation:** The HANCOCK clean B7-minus-B6 check was +0.01550 and failed the ≤0.01 criterion; age-subgroup warnings were seed-specific and exploratory; original radiomics did not clearly outperform shuffled or randomized controls; B7 was below B6 at 10/10 RADCURE, 10/10 HANCOCK, 8/10 GSE65858, and 0/10 GSE41613 DCA thresholds.
- **Mandatory negative/limiting evidence:** These analyses preclude claims of modality-specific biology, universal robustness, clinical utility, deployable thresholds, or patient benefit. DCA does not establish clinical utility.
- **Provisional display:** A compact falsification panel in Table 4; full stress, negative-control, and DCA displays in Supplement.
- **Destination:** Only findings that directly constrain the central thesis in the main text; complete diagnostic inventories in Supplement.

### RES-05 — Phase 7 post hoc exploratory comparators reproduce ecosystem-dependent rankings

- **Question answered:** Did stronger added comparators become universal winners across ecosystems?
- **Claim IDs:** C15, C16, C17.
- **Linked evidence_id values:** `P7-EXT-R003-IPCW-BRIER`, `P7-EXT-R007-IPCW-BRIER`, `P7-EXT-R011-IPCW-BRIER`, `P7-EXT-R011-CALIBRATION-IN-THE-LARGE`, `P7-EXT-R012-IPCW-BRIER`, `P7-PAIR-R014`, `P7-PAIR-R046`, `P7-PAIR-R086`, `P6-ABS-R012-IPCW-BRIER`.
- **Cohort role:** Added comparisons on the established RADCURE, HANCOCK, and GSE65858 test partitions.
- **Analysis nature:** Phase 7 **post hoc exploratory**, outside the prespecified Phase 6 locked comparison set.
- **Sample size:** RADCURE n=626; HANCOCK n=152; GSE65858 n=244.
- **Coverage:** The listed C2/C3 and B2/B6 comparisons had 100% coverage and are not mixed with B7 selective subsets.
- **95% CI:** RADCURE C2-minus-B6 was −0.00736 (−0.01162 to −0.00283); HANCOCK was −0.00852 (−0.02388 to +0.00686); GSE65858 C3-minus-B6 was −0.06755 (−0.09043 to −0.04585).
- **Core interpretation:** C2 Brier was 0.09068 in RADCURE and 0.10367 in HANCOCK but deteriorated to 0.34287 in GSE65858 with calibration-in-the-large −1.935. C3 reached 0.20499 in GSE65858 and improved on B6, but B2 remained lower at 0.19639. Rankings changed by ecosystem, leaving no universal winner.
- **Mandatory negative/limiting evidence:** Use post hoc exploratory in the same paragraph; do not turn one-cohort performance into confirmatory global superiority.
- **Provisional display:** Minimal comparator set in Table 4 or a ranking panel integrated into Figure 3.
- **Destination:** Only C2/C3 contrasts needed for the no-universal-winner conclusion in the main text; complete C1–C4 results in Supplement.

## 4. Discussion paragraph plan

### DIS-01 — Central finding: multimodal gains were conditional

- **Paragraph task:** State that the favourable RADCURE/HANCOCK results and GSE65858 failure jointly demonstrate ecosystem-dependent multimodal value.
- **Evidence interface:** C03–C06 and C20.
- **Limitation:** Do not frame TRUST-HN as the overall winning model.

### DIS-02 — Clinical anchoring as a design principle

- **Paragraph task:** Explain how the clinical anchor converts model ranking into a test of incremental value and provides the fallback reference when transfer is unreliable.
- **Evidence interface:** C03, C04, C18.
- **Limitation:** The clinical anchor itself still requires external and prospective assessment.

### DIS-03 — Gating succeeds through visibility, not guaranteed accuracy

- **Paragraph task:** Explain why coverage, fallback, and abstention improve auditability while directly acknowledging worse RADCURE performance, uncertainty in two cohorts, and only partial mitigation in GSE65858.
- **Evidence interface:** C07–C11.
- **Limitation:** The 90% profile is not a deployable safety threshold; actions are not clinical advice.

### DIS-04 — GSE65858 identifies cross-platform calibration as a translational bottleneck

- **Paragraph task:** Treat cross-platform calibration failure as the paper’s central turn and translational implication rather than an ancillary negative result.
- **Evidence interface:** C05.
- **Limitation:** One external cohort cannot represent every platform, but discrimination cannot be used to obscure absolute-risk distortion.

### DIS-05 — Why falsification and post hoc comparisons strengthen the thesis

- **Paragraph task:** Explain how stress tests, negative controls, DCA, and Phase 7 post hoc exploratory rank reversal jointly constrain mechanistic, universal, and clinical interpretations.
- **Evidence interface:** C11–C17.
- **Limitation:** Each analysis retains its development-only, exploratory, or multiplicity boundary.

### DIS-06 — Strengths, limitations, next steps, and conclusion

- **Paragraph task:** Summarize strengths in prespecified governance, multi-ecosystem testing, and explicit falsification; acknowledge retrospective design, ecosystem-specific fitting, small sensitivity evidence, and absent deployable thresholds; propose independent prospective calibration, preregistered gating, and workflow evaluation.
- **Evidence interface:** C18 and C20.
- **Limitation:** Conclude with an auditable principle of conditional fusion, not clinical utility or patient benefit.

## 5. Methods paragraph plan

### MET-01 — Study design, endpoint, and governance

- **Question answered:** What endpoint was evaluated under which prespecified rules?
- **Core content:** Retrospective multi-cohort design; 24-month overall survival; one-time Phase 6 locked/OOD/external/sensitivity evaluation; 2,000 paired bootstrap replicates.
- **Evidence interface:** C02; `GOV-ANCHOR-001`, `GOV-ANCHOR-002`, `GOV-ANCHOR-003`, `GOV-ANCHOR-004`.
- **Limitation:** Not prospective and no outcome-guided Phase 6 tuning language.

### MET-02 — Cohorts, roles, and participant flow

- **Question answered:** Why was each cohort included and what role did it serve?
- **Core content:** Define development, calibration, locked testing, OOD, cross-platform external, and restricted sensitivity roles for RADCURE, HANCOCK, TCGA-HNSC, GSE65858, and GSE41613.
- **Evidence interface:** C01; `P2-FLOW-R002`–`P2-FLOW-R027`.
- **Limitation:** GSE41613 is an HPV-negative OSCC sensitivity analysis only.

### MET-03 — Data ecosystems, modalities, and preprocessing

- **Question answered:** How were clinical, radiomic, and transcriptomic inputs handled?
- **Core content:** Describe ecosystem-specific preprocessing, missingness handling, and variable interfaces, with all incremental modelling beginning from the B2 clinical anchor.
- **Evidence interface:** C18 and frozen configurations.
- **Limitation:** Do not imply shared parameters or fully homogeneous modality representations across ecosystems.

### MET-04 — Clinical anchor and incremental/residual fusion

- **Question answered:** How were B2, B6, and essential baselines defined?
- **Core content:** Define B2 as the clinical anchor and B6 as forced fusion of incremental/residual modality information; retain only definitions needed to understand the main argument.
- **Evidence interface:** C18 and frozen Phase 4 model definitions.
- **Limitation:** Full 24-model definitions, hyperparameters, and seeds belong in Supplement.

### MET-05 — Reliability scoring and AUGMENT/FALLBACK/ABSTAIN

- **Question answered:** How did B7 generate selective predictions?
- **Core content:** Define reliability scoring, the primary 90% profile, non-abstained coverage, and the three algorithmic action classes.
- **Evidence interface:** C07, C10; `GOV-ANCHOR-002`.
- **Limitation:** The 90% profile is not a clinically safe or deployable threshold; 80% and 100% profiles belong in Supplement.

### MET-06 — Absolute performance, calibration, and paired comparisons

- **Question answered:** How were performance and fair B7 comparisons assessed?
- **Core content:** IPCW Brier, Harrell/Uno C, 24-month AUC, calibration-in-the-large, and slope; paired bootstrap 95% CIs; all direct B7 comparisons on the identical non-abstained subset with coverage.
- **Evidence interface:** C03–C10; `P6-ABS-*`, `P6-PAIR-*`.
- **Limitation:** Negative Brier differences favour the first-listed model; unpaired absolute contrasts are not confirmatory superiority tests.

### MET-07 — Stress tests, subgroup audit, negative controls, and DCA

- **Question answered:** How were shift, shortcut signals, and decision-curve behaviour examined?
- **Core content:** Phase 5 criteria, seed-level worst-group audit, RADCURE shuffled/randomized controls, and retrospective exploratory DCA.
- **Evidence interface:** C11–C14; `P5-CHECK-*`, `P5-FLAG-*`, `P6-NEG-*`, `P6-DCA-*`.
- **Limitation:** Development stress testing cannot establish universal robustness; DCA cannot establish clinical utility or patient benefit.

### MET-08 — Phase 7 post hoc exploratory comparisons

- **Question answered:** How were C1–C4 added comparisons implemented and governed?
- **Core content:** Phase 7 post hoc exploratory benchmarks and paired bootstrap on the same test partitions, explicitly outside the prespecified Phase 6 locked analysis.
- **Evidence interface:** C15–C17; `GOV-ANCHOR-005`, `GOV-ANCHOR-006`, `P7-EXT-*`, `P7-PAIR-*`.
- **Limitation:** No confirmatory superiority or universal-best-model conclusion.

## 6. Fixed main-text versus Supplement boundary

### Main text

- Conditional incremental-value question, clinical anchoring, and the TRUST-HN framework.
- Cohort roles and prespecified Phase 6 governance.
- Favourable RADCURE/HANCOCK B2/B6 evidence and central GSE65858 failure in one narrative.
- Restricted GSE41613 sensitivity boundary.
- B7 primary 90% coverage, actions, and identical non-abstained-subset comparisons.
- Concise falsification conclusions and the minimal Phase 7 post hoc exploratory evidence needed to show rank reversal.

### Supplement

- Full models, seeds, hyperparameters, calibration details, and training diagnostics.
- Complete participant flow, missingness, exclusions, and endpoint accounting.
- Full 80/90/100% gates, action tables, stress tests, subgroup audits, negative controls, DCA, and Phase 7 post hoc exploratory comparisons.
- Software environment, reproducibility commands, model card, and reporting checklists.

### Phase 8 boundary

Phase 8 is excluded from the current title, Abstract, Introduction, Results, Discussion, Methods, and main-display plan. If explicitly approved later for Supplement, it may only be described as a **known-overlap workflow and bias simulation**, explicitly **not validation**.

## 7. WP2 stop point

This file reaches only the revised outline-approval checkpoint. Until user approval:

- do not draft full Abstract/Introduction/Results/Discussion/Methods prose;
- do not modify `main.tex` or `sections/`;
- do not enter WP3, WP4, or later work packages;
- do not change any frozen model, threshold, cohort partition, endpoint, or result.
