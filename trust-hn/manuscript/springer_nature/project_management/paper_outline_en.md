# TRUST-HN WP2 Paragraph-Level Paper Outline (English)

**Version date:** 2026-08-12  
**Status:** WP2 outline; not submission-ready manuscript prose.  
**Constraint:** all result numbers and claims are governed by `evidence_map.csv`, `claim_matrix_en.md`, and `argument_map.md`.  
**Approval boundary:** no full prose, WP3 work, or figure production is authorized until this outline is approved.

## 0. Title, short title, and research question

- **Leading provisional title:** Clinical anchoring and reliability-aware multimodal prognostic modelling across heterogeneous head and neck cancer data ecosystems
- **Alternative provisional title:** Cohort-dependent multimodal prognosis and reliability gating in head and neck squamous cell carcinoma
- **Provisional short title:** Reliability-aware multimodal HNSCC prognosis
- **Primary question:** In retrospective HNSCC data ecosystems with different modality availability and distribution shifts, can clinical anchoring and incremental fusion characterize when additional modalities improve 24-month overall-survival prediction, while reliability-aware AUGMENT/FALLBACK/ABSTAIN algorithmic outputs expose failure boundaries of forced fusion?
- **Provisional central conclusion:** Multimodal gains, calibration, and reliability-gating behaviour were cohort dependent; fallback and abstention exposed failure modes of forced fusion, but the current retrospective evidence did not establish universal robustness, deployable thresholds, or clinical utility.

## 1. Abstract paragraph plan

### ABS-01 ? Background and gap

- **Question answered:** Why should reliability and failure boundaries be primary concerns in multimodal HNSCC prognosis?
- **Evidence:** Conceptual background; heterogeneous ecosystems and ecosystem-specific training boundaries in C01 and C18.
- **Core interpretation:** Additional modalities can add information but can also introduce missingness, shortcut signals, platform differences, and calibration risk.
- **Limitation:** Do not assume multimodal superiority or modality-specific biological signal.
- **Provisional display:** Figure 1 (study question and framework), to be finalized in WP4.

### ABS-02 ? Design and methods

- **Question answered:** How were clinical anchoring, incremental fusion, and reliability gating evaluated?
- **Evidence:** C01, C02, C18; `GOV-ANCHOR-001`?`GOV-ANCHOR-004`; Phase 6 cohort roles.
- **Core interpretation:** Ecosystem-specific B2/B6/B7 models were evaluated in prespecified retrospective locked, OOD, cross-platform external, and restricted sensitivity settings, with 2,000 paired bootstrap replicates.
- **Limitation:** Not prospective; not a universal HNSCC model with one shared parameter set.
- **Provisional display:** Figures 1?2 and Table 1.

### ABS-03 ? Principal favourable and failure results

- **Question answered:** Which ecosystems supported B6 transfer, and which exposed failure?
- **Evidence:** C03?C06; core RADCURE/HANCOCK B2/B6 metrics; GSE65858 Brier/calibration; GSE41613 sensitivity findings.
- **Core interpretation:** B6 had favourable descriptive point estimates in RADCURE and HANCOCK, whereas GSE65858 showed substantial cross-platform calibration failure; GSE41613 supplied restricted and uncertain sensitivity evidence only.
- **Limitation:** Absolute point-estimate contrasts are not automatically paired superiority tests; GSE41613 is restricted to HPV-negative OSCC sensitivity analysis.
- **Provisional display:** Figures 3?4 and Table 2.

### ABS-04 ? Gating, negative findings, and comparators

- **Question answered:** Did B7 consistently improve performance, and how did secondary diagnostics constrain interpretation?
- **Evidence:** C07?C17; `P6-PAIR-R002`, `R005`, `R008`, `R011`; negative controls, DCA, and Phase 7 post hoc exploratory results.
- **Core interpretation:** B7 changed coverage and algorithmic action distributions but did not consistently outperform B6 on the identical non-abstained subset; negative controls, DCA, and strong comparators argued against simple claims of modality specificity, clinical utility, or a universal winner.
- **Limitation:** Co-report coverage; DCA cannot establish clinical utility; Phase 7 is post hoc exploratory.
- **Provisional display:** Figures 4?6 and Tables 3?4.

### ABS-05 ? Restrained conclusion

- **Question answered:** What does the evidence support and not support?
- **Evidence:** C20 synthesis of C03?C19.
- **Core interpretation:** The contribution is an auditable clinical-anchor?incremental-fusion?reliability-assessment framework with explicit success and failure boundaries.
- **Limitation:** No universal robustness, prospective validity, deployable threshold, clinical utility, or patient-benefit claim.
- **Provisional display:** None; synthesize the principal displays.

## 2. Introduction paragraph plan

### INT-01 ? Clinical problem and data ecosystems

- **Question answered:** Why is HNSCC prognostic prediction a heterogeneous multi-source problem?
- **Evidence:** External literature to be added in WP8; internal cohort/modality structure supported by C01.
- **Core interpretation:** Clinical, imaging, blood, tissue-microenvironment, and transcriptomic sources may be complementary, but their origins, platforms, and missingness mechanisms differ.
- **Limitation:** This paragraph defines the problem; it does not claim that this study established cross-ecosystem robustness.
- **Provisional display:** Figure 1 conceptual panel.

### INT-02 ? Reliability gap in conventional multimodal modelling

- **Question answered:** Why is discrimination alone insufficient?
- **Evidence:** External literature to be added later; internal anchors C05 and C11?C14.
- **Core interpretation:** Forced fusion can conceal calibration failure, missing modalities, shortcut signals, and selective coverage; evaluation should jointly report Brier score, calibration, coverage, negative controls, and stress tests.
- **Limitation:** Reliability metrics are not equivalent to clinical safety.
- **Provisional display:** Figure 1 reliability pathway.

### INT-03 ? TRUST-HN design logic

- **Question answered:** What is the technical and audit logic of the study?
- **Evidence:** C18; `GOV-ANCHOR-001`?`GOV-ANCHOR-004`.
- **Core interpretation:** B2 provides the clinical anchor, B6 absorbs incremental/residual information, and B7 produces reliability-aware AUGMENT/FALLBACK/ABSTAIN algorithmic outputs under a frozen primary evaluation.
- **Limitation:** Models are trained separately by ecosystem; actions are not treatment, triage, referral, or follow-up recommendations.
- **Provisional display:** Figure 1 architecture.

### INT-04 ? Objectives, hypotheses, and contribution

- **Question answered:** What did the study test?
- **Evidence:** C02, C20, and argument nodes A3?A10.
- **Core interpretation:** Evaluate B6 transfer, B7 coverage?risk behaviour, cross-platform failure, negative controls, and strong comparators; make cohort dependence and failure boundaries the central contribution.
- **Limitation:** Phase 7 is post hoc exploratory; Phase 8 is a known-overlap workflow and bias simulation, not validation.
- **Provisional display:** Figure 1 and study-flow display.

## 3. Results paragraph plan

> **WP1 interface rule:** every Results paragraph below explicitly lists claim IDs, linked evidence IDs, cohort role, analysis nature, sample size, coverage, 95% CI, mandatory co-reported negative/limiting evidence, and main-text-versus-Supplement destination.

### RES-01 ? Cohort composition, analysis roles, and frozen governance

- **Question answered:** Which patients entered development, calibration, locked/OOD/external, or sensitivity roles, and how was the primary evaluation frozen?
- **Claim IDs:** C01, C02, C18.
- **Linked evidence_id values:** `P2-FLOW-R014`, `P2-FLOW-R015`, `P2-FLOW-R016`, `P2-FLOW-R021`, `P2-FLOW-R022`, `P2-FLOW-R023`, `P2-FLOW-R026`, `P2-FLOW-R027`, `P2-FLOW-R011`, `P2-FLOW-R004`, `GOV-ANCHOR-001`, `GOV-ANCHOR-002`, `GOV-ANCHOR-003`, `GOV-ANCHOR-004`.
- **Cohort role:** RADCURE train 1,215/calibration 303/prespecified locked retrospective test 626; HANCOCK train 489/calibration 122/prespecified retrospective OOD sealed test 152; TCGA-HNSC train 416/calibration 104; GSE65858 prespecified retrospective cross-platform external test 244; GSE41613 restricted retrospective HPV-negative OSCC sensitivity cohort 97.
- **Analysis nature:** Cohort definition and governance anchor; one-time prespecified Phase 6 retrospective evaluation.
- **Sample size:** Reported by role above; development and test denominators must not be pooled.
- **Coverage:** Not applicable to cohort flow; model coverage is reported in RES-05.
- **95% CI:** Not applicable to cohort counts and governance fields.
- **Core interpretation:** Analysis roles and freeze status precede result interpretation and prevent development evidence from being represented as external validation.
- **Mandatory negative/limiting evidence:** Not prospective; separately trained ecosystems rather than one shared-parameter universal model; GSE41613 is sensitivity-only.
- **Provisional display:** Main Figure 2 and Table 1; detailed exclusions and missingness in Supplement.
- **Destination:** Core partitions/governance in main text; complete flow in Supplement.

### RES-02 ? Development stress tests supported progression but included a prespecified failure and exploratory warnings

- **Question answered:** Did all pre-freeze reliability stress tests pass?
- **Claim IDs:** C11, C12.
- **Linked evidence_id values:** `P5-CHECK-R002`, `P5-CHECK-R003`, `P5-CHECK-R004`, `P5-CHECK-R005`, `P5-CHECK-R006`, `P5-CHECK-R007`, `P5-CHECK-R008`, `P5-CHECK-R009`, `P5-FLAG-R055`, `P5-FLAG-R071`.
- **Cohort role:** HANCOCK and TCGA-HNSC development/calibration stress testing, not locked external evaluation.
- **Analysis nature:** DEVELOPMENT_STRESS_TEST, including prespecified checks and an exploratory worst-group audit.
- **Sample size:** Eight prespecified checks; each age ?65 flag had n=34.
- **Coverage:** Seed-level flagged coverage was 0.8235 and 0.7647; complete-modality-dropout fallback rate was 1.0 for the 100% profile.
- **95% CI:** No bootstrap 95% CI for acceptance checks or seed-level flags; report as descriptive development evidence.
- **Core interpretation:** Seven of eight checks passed, but the HANCOCK clean B7-vs-B6 Brier check was +0.01550 against a ?0.01 criterion.
- **Mandatory negative/limiting evidence:** Age-subgroup warnings were multiple-comparison, small-sample, and seed-specific; no fairness or causal inference.
- **Provisional display:** Main Table 4 or a concise result box; all seeds and stress levels in Supplement.
- **Destination:** 7/8 summary and failed item in main text; details in Supplement.

### RES-03 ? B6 showed favourable retrospective transfer in RADCURE and HANCOCK

- **Question answered:** How did B6 and the B2 clinical anchor perform in the prespecified locked and OOD cohorts?
- **Claim IDs:** C03, C04.
- **Linked evidence_id values:** `P6-ABS-R002-IPCW-BRIER`, `P6-ABS-R002-UNO-C`, `P6-ABS-R002-AUC-HORIZON`, `P6-ABS-R005-IPCW-BRIER`, `P6-ABS-R005-UNO-C`, `P6-ABS-R005-AUC-HORIZON`, `P6-ABS-R007-IPCW-BRIER`, `P6-ABS-R007-UNO-C`, `P6-ABS-R007-AUC-HORIZON`, `P6-ABS-R010-IPCW-BRIER`, `P6-ABS-R010-UNO-C`, `P6-ABS-R010-AUC-HORIZON`.
- **Cohort role:** RADCURE prespecified locked retrospective test; HANCOCK prespecified retrospective OOD sealed test.
- **Analysis nature:** PRESPECIFIED_LOCKED_RETROSPECTIVE and PRESPECIFIED_OOD_RETROSPECTIVE.
- **Sample size:** RADCURE n=626; HANCOCK n=152; B2/B6 evaluated all patients.
- **Coverage:** B2/B6 coverage 1.0.
- **95% CI:** RADCURE B6 Brier 0.0980 (0.0835?0.1131), Uno C 0.7740 (0.7258?0.8225), AUC 0.7838 (0.7277?0.8369); HANCOCK B6 Brier 0.1122 (0.0814?0.1467), Uno C 0.8281 (0.7543?0.8930), AUC 0.8476 (0.7567?0.9230). Co-report B2 CIs from the linked rows.
- **Core interpretation:** In both ecosystems, B6 had a lower Brier point estimate and higher discrimination point estimates than B2, supporting restrained language of favourable retrospective transfer.
- **Mandatory negative/limiting evidence:** These are within-cohort absolute descriptive contrasts; do not convert unmatched B6-vs-B2 values into a definitive paired superiority test or generalize to all institutions/shifts.
- **Provisional display:** Main Figure 3 forest plot and Table 2.
- **Destination:** Core B2/B6/B7 results in main text; full B0?B7 results in Supplement.

### RES-04 ? GSE65858 exposed cross-platform calibration failure; GSE41613 remained restricted sensitivity evidence

- **Question answered:** Did transcriptomic transfer reproduce multimodal gains?
- **Claim IDs:** C05, C06.
- **Linked evidence_id values:** `P6-ABS-R012-IPCW-BRIER`, `P6-ABS-R015-IPCW-BRIER`, `P6-ABS-R015-CALIBRATION-IN-THE-LARGE`, `P6-ABS-R015-CALIBRATION-SLOPE`, `P6-ABS-R016-IPCW-BRIER`, `P6-ABS-R016-CALIBRATION-IN-THE-LARGE`, `P6-ABS-R016-CALIBRATION-SLOPE`, `P6-ABS-R017-IPCW-BRIER`, `P6-ABS-R017-UNO-C`, `P6-ABS-R017-AUC-HORIZON`, `P6-ABS-R020-IPCW-BRIER`, `P6-ABS-R021-IPCW-BRIER`, `P6-PAIR-R011`, `P6-PAIR-R012`.
- **Cohort role:** GSE65858 prespecified retrospective cross-platform external test; GSE41613 restricted retrospective HPV-negative OSCC sensitivity cohort.
- **Analysis nature:** PRESPECIFIED_EXTERNAL_RETROSPECTIVE and RESTRICTED_SENSITIVITY_ANALYSIS.
- **Sample size:** GSE65858 n=244, with B7 evaluated in n=230; GSE41613 n=97.
- **Coverage:** GSE65858 B7 0.9426; GSE41613 B7 1.0.
- **95% CI:** GSE65858 B2 Brier 0.1964 (0.1756?0.2191), B6 0.2725 (0.2439?0.3011), B7 0.2672 (0.2391?0.2965). GSE41613 B7-vs-B6 ?0.01314 (?0.03153 to +0.00215) and B7-vs-B2 ?0.00632 (?0.04051 to +0.03008). Calibration intercept/slope are point estimates without bootstrap CI.
- **Core interpretation:** B6/B7 showed large negative calibration-in-the-large and attenuated slopes in GSE65858 and worse Brier scores than B2; GSE41613 had a non-discriminating B2 but uncertain Brier improvement. All cited B7 paired differences are evaluated on the identical non-abstained subset.
- **Mandatory negative/limiting evidence:** Any GSE65858 discrimination must be co-reported with calibration failure; GSE41613 is not general HNSCC external validation.
- **Provisional display:** Main Figures 3?4 and Tables 2?3; full calibration plots in Supplement.
- **Destination:** Central failure and sensitivity boundary in main text; full model/calibration detail in Supplement.

### RES-05 ? B7 changed coverage and actions but did not consistently outperform B6 on identical non-abstained subsets

- **Question answered:** Under the primary 90% profile, what coverage/actions did B7 produce and how did paired Brier differences compare with B6 and B2?
- **Claim IDs:** C07, C08, C09, C10.
- **Linked evidence_id values:** `P6-ACTION-R005`, `P6-ACTION-R006`, `P6-ACTION-R007`, `P6-ACTION-R014`, `P6-ACTION-R015`, `P6-ACTION-R016`, `P6-ACTION-R023`, `P6-ACTION-R024`, `P6-ACTION-R025`, `P6-ACTION-R032`, `P6-ACTION-R033`, `P6-ACTION-R034`, `P6-PAIR-R002`, `P6-PAIR-R003`, `P6-PAIR-R005`, `P6-PAIR-R006`, `P6-PAIR-R008`, `P6-PAIR-R009`, `P6-PAIR-R011`, `P6-PAIR-R012`.
- **Cohort role:** RADCURE locked test, HANCOCK OOD sealed test, GSE65858 cross-platform external test, and GSE41613 restricted sensitivity cohort.
- **Analysis nature:** Prespecified Phase 6 retrospective selective prediction; every direct comparison uses the identical non-abstained subset.
- **Sample size:** RADCURE 584/626; HANCOCK 126/152; GSE65858 230/244; GSE41613 97/97.
- **Coverage:** 0.9329, 0.8289, 0.9426, and 1.0000. AUGMENT/FALLBACK/ABSTAIN rates were 82.1/11.2/6.7%, 64.5/18.4/17.1%, 92.6/1.6/5.7%, and 95.9/4.1/0%, respectively.
- **95% CI:** B7-vs-B6 Brier: RADCURE +0.00382 (+0.00084 to +0.00718); HANCOCK +0.01058 (?0.00947 to +0.03186); GSE65858 ?0.00812 (?0.01584 to ?0.00183); GSE41613 ?0.01314 (?0.03153 to +0.00215). Co-report B7-vs-B2 CIs from `P6-PAIR-R003/R006/R009/R012`.
- **Core interpretation:** Selective behaviour differed by ecosystem; fallback and abstention were operationally visible, but selection did not guarantee better accuracy than forced fusion.
- **Mandatory negative/limiting evidence:** B7 was worse than B6 in RADCURE, uncertain in HANCOCK/GSE41613, and better than B6 but clearly worse than B2 in GSE65858. Actions are algorithmic output classes only.
- **Provisional display:** Main Figure 4 risk?coverage/action display and Table 3 paired differences.
- **Destination:** Primary 90% profile in main text; 80/100% profiles and complete action tables in Supplement.

### RES-06 ? Radiomics negative controls did not support a clear original-modality advantage

- **Question answered:** Could apparent RADCURE gains be attributed to specific information in the original radiomics features?
- **Claim IDs:** C13.
- **Linked evidence_id values:** `P6-NEG-PAIR-R017`, `P6-NEG-PAIR-R021`, `P6-NEG-PAIR-R025`, `P6-NEG-PAIR-R029`, `P6-NEG-PAIR-R033`, `P6-NEG-PAIR-R037`, `P6-NEG-PAIR-R041`, `P6-NEG-PAIR-R045`.
- **Cohort role:** Negative-control analysis within the RADCURE prespecified locked retrospective test.
- **Analysis nature:** PRESPECIFIED_LOCKED_RETROSPECTIVE negative-control paired bootstrap.
- **Sample size:** B4?B6 n=626; B7 n=584/626.
- **Coverage:** B4?B6 1.0; B7 0.9329.
- **95% CI:** B6 original-vs-shuffled Brier +0.00124 (?0.00105 to +0.00334), B7 ?0.00130 (?0.00366 to +0.00078); B6 original-vs-randomized +0.00063 (?0.00200 to +0.00306), B7 ?0.00026 (?0.00286 to +0.00238). All B4?B7 Brier-difference CIs crossed zero.
- **Core interpretation:** Original radiomics showed no clear, stable Brier advantage over these controls.
- **Mandatory negative/limiting evidence:** This does not prove absence of all radiomic signal, but it prohibits a claim of demonstrated radiomics-specific biological signal.
- **Provisional display:** Main Figure 5 concise panel; complete metrics in Supplement.
- **Destination:** Conclusion and representative CIs in main text; complete B4?B7 controls in Supplement.

### RES-07 ? Exploratory DCA showed no consistent B7-over-B6 curve advantage

- **Question answered:** Did retrospective decision curves establish stable net-benefit advantage or clinical utility for B7?
- **Claim IDs:** C14.
- **Linked evidence_id values:** `P6-DCA-R022`?`P6-DCA-R031`, `P6-DCA-R052`?`P6-DCA-R061`, `P6-DCA-R082`?`P6-DCA-R091`, `P6-DCA-R112`?`P6-DCA-R121`.
- **Cohort role:** Retrospective exploratory DCA in the four Phase 6 test/sensitivity cohorts.
- **Analysis nature:** EXPLORATORY_NO_CLINICAL_UTILITY.
- **Sample size:** Corresponding test-cohort denominators; B7 curves are conditioned by non-abstained coverage.
- **Coverage:** RADCURE 0.9329; HANCOCK 0.8289; GSE65858 0.9426; GSE41613 1.0.
- **95% CI:** No bootstrap 95% CI in the DCA table; describe threshold-grid curve behaviour only.
- **Core interpretation:** B7 was below B6 at 10/10 RADCURE, 10/10 HANCOCK, 8/10 GSE65858, and 0/10 GSE41613 thresholds, providing no consistent advantage.
- **Mandatory negative/limiting evidence:** DCA does not establish clinical utility, patient benefit, treatment value, or a deployable threshold; thresholds are exploratory.
- **Provisional display:** Main Figure 6 may show selected cohorts or a summary; all curves in Supplement.
- **Destination:** No-consistent-advantage statement and boundary in main text; full curves in Supplement.

### RES-08 ? Phase 7 post hoc exploratory comparisons showed ecosystem-dependent model rankings

- **Question answered:** Did stronger comparators yield one universally superior model?
- **Claim IDs:** C15, C16, C17.
- **Linked evidence_id values:** `GOV-ANCHOR-005`, `GOV-ANCHOR-006`, `P7-EXT-R003-IPCW-BRIER`, `P7-EXT-R007-IPCW-BRIER`, `P7-EXT-R011-IPCW-BRIER`, `P7-EXT-R011-CALIBRATION-IN-THE-LARGE`, `P7-EXT-R012-IPCW-BRIER`, `P7-PAIR-R014`, `P7-PAIR-R046`, `P7-PAIR-R078`, `P7-PAIR-R086`, `P7-PAIR-R026`, `P7-PAIR-R058`, `P7-PAIR-R090`.
- **Cohort role:** Post hoc comparisons on RADCURE locked, HANCOCK OOD, and GSE65858 external test partitions; test roles do not change the post hoc exploratory status.
- **Analysis nature:** Phase 7 **post hoc exploratory** benchmark; not prespecified, locked, primary, or confirmatory.
- **Sample size:** RADCURE n=626; HANCOCK n=152; GSE65858 n=244; listed C2/C3/C4 models had coverage 1.0.
- **Coverage:** 1.0 for the listed non-selective comparators.
- **95% CI:** C2-vs-B6 Brier: RADCURE ?0.00736 (?0.01162 to ?0.00283), HANCOCK ?0.00852 (?0.02388 to +0.00686), GSE65858 +0.07033 (+0.04054 to +0.09848); GSE65858 C3-vs-B6 ?0.06755 (?0.09043 to ?0.04585).
- **Core interpretation:** C2 was strong in RADCURE/HANCOCK but severely miscalibrated in GSE65858; C3 improved on B6 in GSE65858, yet its Brier 0.2050 remained above the Phase 6 B2 value 0.1964. No universal winner existed.
- **Mandatory negative/limiting evidence:** Label every occurrence post hoc exploratory; C4 equalled B5 externally; do not present a single pooled ranking or ?best model.?
- **Provisional display:** A minimal comparator subset in main Figure 3/Table 4; complete comparisons in Supplement.
- **Destination:** Only the evidence needed for the no-universal-winner synthesis in main text; all C1?C4 results in Supplement.

## 4. Discussion paragraph plan

### DIS-01 ? Principal findings

- **Question answered:** What is the most important overall result?
- **Evidence:** C20 synthesis of C03?C17.
- **Core interpretation:** Favourable B6 transfer, GSE65858 failure, inconsistent B7 effects, negative controls, and cohort-dependent comparators must be retained together.
- **Limitation:** Do not compress the mixed evidence into a universal TRUST-HN victory narrative.
- **Provisional display:** Refer to Figures 3?6 and Tables 2?4.

### DIS-02 ? Interpreting B6 findings in RADCURE and HANCOCK

- **Question answered:** Why are these findings still informative?
- **Evidence:** C03, C04, C18.
- **Core interpretation:** Incremental information beyond a clinical anchor produced favourable point estimates in two distinct ecosystems, supporting further study of the framework rather than universal superiority.
- **Limitation:** Retrospective design, ecosystem-specific training, limited institutions/shifts, and descriptive rather than universally paired contrasts.
- **Provisional display:** Figure 3 and Table 2.

### DIS-03 ? The value of gating is failure visibility, not guaranteed accuracy

- **Question answered:** What is the value of B7 if it did not consistently outperform B6?
- **Evidence:** C07?C11; RES-02 and RES-05.
- **Core interpretation:** Coverage, fallback, and abstention make potentially unreliable forced-fusion cases visible; the value is auditability and a safety-degradation hypothesis, not an accuracy guarantee.
- **Limitation:** Worse paired Brier in RADCURE, failed HANCOCK development check, and no clinically validated action workflow.
- **Provisional display:** Figure 4 and Tables 3?4.

### DIS-04 ? GSE65858 identifies cross-platform calibration as a translational bottleneck

- **Question answered:** Why is GSE65858 a central result rather than a peripheral failure?
- **Evidence:** C05 and RES-04.
- **Core interpretation:** Platform change can produce severe overprediction and slope attenuation, preventing discrimination from translating into reliable absolute risk; calibration must be addressed before transfer.
- **Limitation:** One cross-platform cohort cannot represent every platform shift or separate all technical and population mechanisms.
- **Provisional display:** Figures 3?4 and supplementary calibration plots.

### DIS-05 ? Negative controls, stress tests, and modality-specificity boundaries

- **Question answered:** How do falsification tests change interpretation of multimodal gains?
- **Evidence:** C11?C13.
- **Core interpretation:** Lack of clear original-radiomics advantage over shuffled/randomized controls, plus development warnings, suggests that apparent gains may include redundancy, shortcuts, or unstable components.
- **Limitation:** Do not conclude that radiomics has no value; subgroup results are non-confirmatory.
- **Provisional display:** Figure 5 and supplementary stress-test tables.

### DIS-06 ? Strong comparators and the absence of a universal winner

- **Question answered:** What does Phase 7 imply for model selection?
- **Evidence:** C15?C18 and RES-08.
- **Core interpretation:** C2/C3 rankings changed by ecosystem; evaluation must jointly consider calibration, overall error, discrimination, and governance rather than a single leaderboard.
- **Limitation:** All Phase 7 comparisons are post hoc exploratory, with multiplicity and selection risks requiring independent confirmation.
- **Provisional display:** Table 4 and full supplementary comparisons.

### DIS-07 ? Strengths, overall limitations, translation conditions, and conclusion

- **Question answered:** What is the credible contribution, what remains unresolved, and what should happen next?
- **Evidence:** C14, C19, C20; `GOV-ANCHOR-007`?`GOV-ANCHOR-011`.
- **Core interpretation:** Strengths are frozen governance, multi-ecosystem evaluation, selective coverage, negative controls, and explicit failure reporting. Next steps require non-overlapping independent cohorts, prospective workflow evaluation, platform-specific calibration, and preregistered thresholds.
- **Limitation:** Retrospective design, ecosystem-specific parameters, restricted cohorts, and unvalidated clinical actions. Phase 8 is a known-overlap workflow and bias simulation and explicitly not validation; DCA does not establish clinical utility.
- **Provisional display:** No new display; synthesize main results.

## 5. Methods paragraph plan

### MET-01 ? Study design, endpoint, and analytical governance

- **Question answered:** What was the overall design and primary endpoint?
- **Evidence:** C02; `GOV-ANCHOR-001`?`GOV-ANCHOR-004`.
- **Core interpretation:** Retrospective multi-cohort prediction of 24-month overall survival; one-time frozen Phase 6 evaluation with 2,000 paired bootstrap replicates.
- **Limitation:** Explicitly non-prospective and non-interventional.
- **Provisional display:** Figure 1 and supplementary governance checklist.

### MET-02 ? Cohort sources, eligibility, and analysis partitions

- **Question answered:** How did each cohort enter training, calibration, testing, or sensitivity roles?
- **Evidence:** C01; `P2-FLOW-R002`?`P2-FLOW-R027`.
- **Core interpretation:** Define RADCURE, HANCOCK, TCGA-HNSC, GSE65858, and GSE41613 by ecosystem and role.
- **Limitation:** GSE41613 is HPV-negative OSCC sensitivity-only; do not mix development and test denominators.
- **Provisional display:** Figure 2 and Table 1; complete flow in Supplement.

### MET-03 ? Modality preprocessing and the clinical anchor

- **Question answered:** How were clinical and additional modalities standardized and introduced?
- **Evidence:** Frozen configurations and Phase 2?4 records; C18.
- **Core interpretation:** Describe ecosystem-specific handling of clinical, imaging/radiomics, blood/TMA, and transcriptomic data, beginning with the B2 clinical anchor.
- **Limitation:** Parameters differ by ecosystem; no universal shared-parameter model claim.
- **Provisional display:** Figure 1 and supplementary variable dictionary.

### MET-04 ? B0?B7 and incremental/residual fusion

- **Question answered:** How were the baseline models and B6 defined?
- **Evidence:** Frozen Phase 4 model definitions and C18.
- **Core interpretation:** Define B0?B7 at the level required to understand how B6 adds incremental/residual modality information to the clinical anchor.
- **Limitation:** Complete 24-model definitions, hyperparameters, and seeds belong in Supplement.
- **Provisional display:** Figure 1 and supplementary model table.

### MET-05 ? Reliability scoring and AUGMENT/FALLBACK/ABSTAIN

- **Question answered:** How did B7 generate selective predictions?
- **Evidence:** C07, C10; `GOV-ANCHOR-002`; frozen gate configuration.
- **Core interpretation:** Define reliability scoring, the primary 90% profile, non-abstained coverage, and three algorithmic action classes.
- **Limitation:** Not treatment/triage advice; 90% is not a deployable or clinically safe threshold.
- **Provisional display:** Figures 1 and 4; 80/100% profiles in Supplement.

### MET-06 ? Absolute performance, calibration, and paired comparisons

- **Question answered:** How were models evaluated and compared?
- **Evidence:** C03?C09 and Phase 6 metric files.
- **Core interpretation:** Report IPCW Brier, Harrell/Uno C, 24-month AUC, calibration-in-the-large, and slope; use paired bootstrap 95% CIs.
- **Limitation:** Negative Brier differences favour the first model; all B7 direct comparisons use the identical non-abstained subset and co-report coverage.
- **Provisional display:** Figures 3?4 and Tables 2?3.

### MET-07 ? Stress tests, subgroup audits, negative controls, and DCA

- **Question answered:** How were missingness, shift, shortcut signals, and decision-curve behaviour examined?
- **Evidence:** C11?C14.
- **Core interpretation:** Describe Phase 5 acceptance checks, seed-level worst-group audit, RADCURE shuffled/randomized controls, and exploratory DCA.
- **Limitation:** Development-only stress evidence, subgroup multiplicity, and no clinical-utility inference from DCA.
- **Provisional display:** Figures 5?6 and Table 4; complete results in Supplement.

### MET-08 ? Phase 7 post hoc exploratory comparisons

- **Question answered:** How were C1?C4 comparisons implemented and governed?
- **Evidence:** C15?C17; `GOV-ANCHOR-005`, `GOV-ANCHOR-006`.
- **Core interpretation:** All added comparisons are Phase 7 post hoc exploratory benchmarks on the same test partitions with paired bootstrap, outside the prespecified locked analysis.
- **Limitation:** No confirmatory superiority or universal-best-model conclusion.
- **Provisional display:** Table 4; complete comparisons in Supplement.

### MET-09 ? Phase 8 known-overlap simulation and reproducibility boundary

- **Question answered:** What was `inner_hancock` used for, and what can it not establish?
- **Evidence:** C19; `GOV-ANCHOR-007`, `GOV-ANCHOR-008`, `GOV-ANCHOR-009`, `GOV-ANCHOR-010`, `GOV-ANCHOR-011`.
- **Core interpretation:** The n=135 run containing 88 training, 17 calibration, and 30 prior-test overlaps is a known-overlap workflow and bias simulation for code-path and bias demonstration.
- **Limitation:** Explicitly not validation; never independent, private, institutional, external, or prospective validation.
- **Provisional display:** Supplement-only display; no default main-text numerical result.

## 6. Fixed main-text versus Supplement boundary

### Main text

- Research question, architecture, cohort roles, and frozen Phase 6 governance.
- Core B2/B6 results in RADCURE/HANCOCK.
- GSE65858 calibration failure and GSE41613 sensitivity boundary.
- B7 primary 90% coverage, actions, and identical non-abstained-subset comparisons.
- Key Phase 5 failure, negative-control conclusion, and exploratory DCA no-consistent-advantage result.
- Minimal Phase 7 post hoc exploratory comparison set supporting no universal winner.

### Supplement

- All models, seeds, hyperparameters, calibration detail, 80/90/100% gates, and complete action tables.
- Complete stress tests, subgroup audits, negative controls, DCA thresholds, and Phase 7 comparisons.
- All Phase 8 known-overlap workflow and bias simulation results.
- Software, commands, model card, and reporting checklists.

## 7. WP2 stop point

This outline reaches only the user?s outline-approval checkpoint. Until further approval:

- do not draft full Abstract/Introduction/Results/Discussion/Methods prose;
- do not modify `main.tex`;
- do not enter WP3, WP4, or later work packages;
- do not change any frozen model, threshold, cohort partition, or result.
