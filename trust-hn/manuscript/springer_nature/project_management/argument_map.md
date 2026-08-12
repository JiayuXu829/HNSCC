# TRUST-HN WP2 Argument Map

**Version date:** 2026-08-12
**Status:** story-driven WP2 planning artifact; not manuscript prose.
**Evidence interface:** `evidence_map.csv` and the bilingual WP1 claim matrices are binding.
**Approval boundary:** this document does not authorize full prose, figure production, changes to `main.tex`, or WP3+ work.

## 1. Provisional titles and short title

### Leading title (provisional)

**TRUST-HN: Reliability-aware multimodal prognostic modelling reveals cohort-dependent gains and failure boundaries in head and neck cancer**

### Alternative title A (provisional)

**TRUST-HN: Clinical anchoring and reliability gating for multimodal prognosis across heterogeneous HNSCC data ecosystems**

### Alternative title B (provisional)

**TRUST-HN: When multimodal prognostic information helps—and fails—across heterogeneous head and neck cancer cohorts**

### Short title (provisional)

**TRUST-HN multimodal prognosis**

### Why TRUST-HN belongs in the title

- TRUST-HN names the complete scientific framework: clinical anchoring, conditional incremental fusion, reliability assessment, fallback, and abstention. It is not merely the label of B6 or B7.
- Naming the framework improves identity and discoverability, but the subtitle must immediately state the actual finding—cohort-dependent gains and failure boundaries—so that “TRUST” is not misread as a claim of universal trustworthiness.
- The title therefore combines **framework identity** with a **restrained empirical conclusion**, rather than advertising a universally superior model.

### Title guardrails

- Do not use unqualified “trustworthy,” “robust,” “validated,” “clinically useful,” or “deployment-ready.”
- Do not frame TRUST-HN as a performance champion.
- Phase 7 is always **post hoc exploratory** and cannot drive a confirmatory title.
- Phase 8 is excluded from the current main-text narrative and title.

## 2. Primary research question

Across heterogeneous retrospective HNSCC data ecosystems, **when does multimodal information add credible prognostic value beyond a clinical anchor, when does transfer fail, and can reliability-aware fallback or abstention make those conditions auditable rather than conceal the failure of forced fusion?**

### Secondary questions

1. Under prespecified Phase 6 locked, OOD, cross-platform external, and restricted sensitivity conditions, where did B6 show favourable incremental point estimates relative to B2, and where did it fail?
2. What did B7 reveal through coverage and AUGMENT/FALLBACK/ABSTAIN behaviour, and did it improve prediction on the **identical non-abstained subset**?
3. Do development stress tests, radiomics negative controls, and exploratory decision curves support stronger interpretations of modality specificity, universal robustness, or clinical utility?
4. Do Phase 7 **post hoc exploratory** comparators preserve the same ranking across ecosystems?
5. Which evidence boundaries must be resolved before prospective evaluation or deployment-oriented threshold selection?

## 3. Central thesis and one-sentence answer

### Central thesis

**Multimodal information is not intrinsically superior to clinical information; its prognostic value is conditional on the data ecosystem and transfer setting. TRUST-HN contributes an auditable way to express that conditionality by anchoring predictions clinically and making augmentation, fallback, and abstention explicit.**

### One-sentence answer to be defended

Across heterogeneous HNSCC data ecosystems, multimodal prognostic gains were conditional rather than universal: TRUST-HN made success and failure conditions visible through clinical anchoring, reliability-aware fallback, and abstention, while the retrospective evidence remained insufficient for universal robustness, deployable thresholds, or clinical utility.

## 4. The scientific story, not an experiment inventory

The paper begins from a translational problem rather than from the model catalogue. In multimodal prognosis, adding data sources can improve prediction, but it can also import missingness, shortcut signals, and platform-specific calibration error. The scientifically relevant question is therefore not “How many modalities can be fused?” or “Which model tops one leaderboard?” It is **when additional modalities provide credible incremental information beyond a stable clinical reference**.

TRUST-HN addresses this question by treating the clinical model as an anchor. B6 represents forced incremental fusion: it asks whether added modality information can improve on that anchor. Phase 6 first supplies encouraging evidence—B6 has favourable retrospective point estimates in RADCURE and HANCOCK. The story then turns at GSE65858, where cross-platform transfer produces substantial Brier and calibration failure despite the richer model. This failure is not an appendix result; it is the observation that gives the framework its scientific necessity.

B7 is then introduced as a response to forced-fusion risk, not as a guaranteed accuracy upgrade. Its scientific value is that it makes the system’s behaviour inspectable through coverage and AUGMENT/FALLBACK/ABSTAIN outputs. The paired results show why the distinction matters: gating is worse than B6 in RADCURE, uncertain in HANCOCK and GSE41613, and improves over B6 in GSE65858 while remaining clearly worse than the clinical anchor B2. Thus, the gate exposes conditional reliability but does not manufacture universal superiority.

The final part of the story actively tries to falsify overinterpretation. The failed Phase 5 check, seed-specific subgroup warnings, radiomics negative controls, and exploratory DCA prevent favourable discrimination from being re-labelled as modality-specific biology, universal shift robustness, or clinical utility. Phase 7 post hoc exploratory comparators further change rank across ecosystems. The conclusion is therefore not that TRUST-HN “wins,” but that **conditional fusion should be judged relative to a clinical anchor, with explicit coverage, fallback, abstention, and failure boundaries**.

## 5. Contribution hierarchy

### Primary scientific contribution

A clinical-anchor formulation of multimodal prognosis in which added modalities are evaluated as **conditional incremental information**, not assumed improvements.

### Reliability contribution

An auditable selective-prediction interface that exposes non-abstained coverage and AUGMENT/FALLBACK/ABSTAIN behaviour, while requiring direct B7 comparisons on the identical non-abstained subset.

### Empirical contribution

Prespecified Phase 6 retrospective evidence that juxtaposes favourable B6 point estimates in RADCURE and HANCOCK with substantial cross-platform failure in GSE65858 and restricted sensitivity evidence in GSE41613.

### Falsification contribution

Development stress tests, subgroup warnings, radiomics negative controls, and exploratory DCA define what the performance results cannot establish.

### Comparative contribution

Phase 7 **post hoc exploratory** comparators show ecosystem-dependent rankings and no universal winner.

### Governance contribution

A strict separation between prespecified Phase 6 evidence and Phase 7 post hoc exploratory evidence. Phase 8 is not part of the current main-text argument.

## 6. Main argument chain

| Node | Scientific move | Primary support | Counterevidence or qualifier | Planned paragraphs |
|---|---|---|---|---|
| A1 | More modalities create an opportunity for incremental prognostic information but also create transfer and calibration risks. | Cohort and modality heterogeneity in C01 and C18 | Do not assume multimodal superiority or modality-specific biology. | `INT-01`, `INT-02`, `DIS-02` |
| A2 | TRUST-HN evaluates added information relative to a clinical anchor and makes reliability actions explicit. | C18; `GOV-ANCHOR-001`, `GOV-ANCHOR-002`, `GOV-ANCHOR-003`, `GOV-ANCHOR-004` | Ecosystems use separate fitted parameters; this is a common principle, not one universal shared-parameter model. | `INT-03`, `MET-03`, `MET-04`, `MET-05` |
| A3 | The cohort roles form a prespecified test of conditional multimodal value under increasingly difficult transfer conditions. | C01, C02; `P2-FLOW-R014`, `P2-FLOW-R015`, `P2-FLOW-R016`, `P2-FLOW-R021`, `P2-FLOW-R022`, `P2-FLOW-R023`, `P2-FLOW-R026`, `P2-FLOW-R027` | Retrospective design; cohort roles must remain distinct. | `RES-01`, `MET-01`, `MET-02` |
| A4 | B6 shows favourable retrospective point estimates in RADCURE and HANCOCK. | C03, C04; `P6-ABS-R002-IPCW-BRIER`, `P6-ABS-R005-IPCW-BRIER`, `P6-ABS-R007-IPCW-BRIER`, `P6-ABS-R010-IPCW-BRIER` | Descriptive within-cohort contrasts do not automatically prove superiority. | `RES-02`, `DIS-01` |
| A5 | GSE65858 reveals that multimodal transfer can fail through severe calibration and Brier degradation. | C05; `P6-ABS-R012-IPCW-BRIER`, `P6-ABS-R015-IPCW-BRIER`, `P6-ABS-R015-CALIBRATION-IN-THE-LARGE`, `P6-ABS-R015-CALIBRATION-SLOPE`, `P6-ABS-R016-IPCW-BRIER` | Calibration failure must accompany any discrimination result. | `RES-02`, `DIS-04` |
| A6 | GSE41613 supplies only a restricted HPV-negative OSCC sensitivity boundary. | C06; `P6-ABS-R017-IPCW-BRIER`, `P6-ABS-R020-IPCW-BRIER`, `P6-ABS-R021-IPCW-BRIER`, `P6-PAIR-R011`, `P6-PAIR-R012` | n=97; not general HNSCC external validation. | `RES-02`, `DIS-06` |
| A7 | B7 makes forced-fusion risk observable through coverage and actions. | C07, C10; `P6-ABS-R006-IPCW-BRIER`, `P6-ABS-R011-IPCW-BRIER`, `P6-ABS-R016-IPCW-BRIER`, `P6-ABS-R021-IPCW-BRIER`, `P6-ACTION-*` | Algorithmic outputs only; not clinical decisions or safety interventions. | `RES-03`, `DIS-03` |
| A8 | Reliability gating does not guarantee better accuracy. | C08, C09; `P6-PAIR-R002`, `P6-PAIR-R005`, `P6-PAIR-R008`, `P6-PAIR-R009`, `P6-PAIR-R011` | Compare on identical non-abstained subsets and co-report coverage. | `RES-03`, `DIS-03` |
| A9 | Falsification analyses reject stronger mechanistic, robustness, and utility interpretations. | C11–C14; `P5-CHECK-R002`, `P5-FLAG-R055`, `P5-FLAG-R071`, `P6-NEG-PAIR-R025`, `P6-NEG-PAIR-R029`, `P6-DCA-*` | Development-only, multiplicity-prone, or exploratory evidence as applicable. | `RES-04`, `DIS-05` |
| A10 | Phase 7 post hoc exploratory methods reproduce ecosystem-dependent rankings. | C15–C17; `P7-EXT-R003-IPCW-BRIER`, `P7-EXT-R007-IPCW-BRIER`, `P7-EXT-R011-IPCW-BRIER`, `P7-EXT-R012-IPCW-BRIER`, `P7-PAIR-R014`, `P7-PAIR-R046`, `P7-PAIR-R086` | No confirmatory universal-best-model claim. | `RES-05`, `DIS-05` |
| A11 | The defensible conclusion is conditional fusion with explicit failure boundaries, not universal multimodal superiority. | C20 synthesis of C03–C18 | No prospective validity, deployable threshold, clinical utility, or patient-benefit claim. | `ABS-04`, `DIS-01`, `DIS-06` |

## 7. Results narrative arc

### RES-01 — Heterogeneous ecosystems form a prespecified test of conditional multimodal value

Establish the cohort roles and explain why same-platform locked testing, retrospective OOD testing, cross-platform external testing, and restricted sensitivity testing jointly interrogate one hypothesis. This paragraph is not a sample-size inventory; its function is to set up escalating transfer difficulty.

### RES-02 — Multimodal fusion gains in RADCURE and HANCOCK but fails in GSE65858

Place positive and failure evidence in the same narrative unit. The reader first sees favourable B6 point estimates in RADCURE and HANCOCK, then encounters the central GSE65858 cross-platform Brier/calibration failure. End with the narrow GSE41613 sensitivity boundary. The unit answers: **multimodal value is conditional on ecosystem**.

### RES-03 — Reliability gating makes forced-fusion risk visible but does not guarantee superiority

Report coverage and action distributions before paired performance. Then show that B7 is worse than B6 in RADCURE, uncertain in HANCOCK and GSE41613, and better than B6 in GSE65858 but still worse than B2. The unit answers: **gating improves auditability, not necessarily accuracy**.

### RES-04 — Falsification analyses limit mechanistic, robustness, and clinical interpretations

Combine the failed Phase 5 check, seed-specific subgroup warnings, radiomics negative controls, and exploratory DCA into one argumentative unit. Each analysis blocks a different overclaim; none is presented as an unrelated side experiment.

### RES-05 — Phase 7 post hoc exploratory comparators reproduce ecosystem-dependent rankings

Use only the contrasts necessary to show that C2 performs strongly in RADCURE/HANCOCK but fails in GSE65858, whereas C3 improves on B6 in GSE65858 without surpassing B2. The unit closes the empirical arc: **there is no universal winner across ecosystems**.

## 8. Counterevidence integration rules

| Favourable observation | Counterevidence that must appear with it | Defensible interpretation |
|---|---|---|
| B6 improves descriptive point estimates in RADCURE/HANCOCK | GSE65858 Brier and calibration failure | Incremental value is ecosystem dependent |
| B7 can fallback or abstain | B7 is worse than B6 in RADCURE and uncertain in two cohorts | Gate behaviour is auditable, not automatically superior |
| B7 improves over B6 in GSE65858 | B7 remains worse than B2 | Partial mitigation does not rescue failed multimodal transfer |
| Radiomics models discriminate | Original-vs-shuffled/randomized CIs cross zero | Modality-specific biological signal is unsupported |
| Decision curves can be plotted | B7 often lies below B6 and analyses are retrospective exploratory | No clinical-utility or deployable-threshold claim |
| C2 or C3 performs strongly in one cohort | Rank reverses in another ecosystem | No universal winner |

## 9. Threat-to-validity table

| Threat | Relevant evidence | Required mitigation in writing | Residual boundary |
|---|---|---|---|
| Retrospective selection and censoring | Phase 6 cohorts | Preserve cohort roles and IPCW/CI reporting | No prospective validity |
| Platform shift | GSE65858 | Report calibration-in-the-large and slope with discrimination | No cross-platform robustness claim |
| Selective-prediction denominator change | B7 | Co-report coverage; identical non-abstained subset | No comparison across unequal patient subsets |
| Model-selection multiplicity | Phase 7 | Same-paragraph post hoc exploratory label | Requires independent confirmation |
| Small restricted sensitivity cohort | GSE41613 | HPV-negative OSCC sensitivity analysis label | Not general HNSCC evidence |
| Subgroup multiplicity and small cells | Phase 5 | Seed-specific exploratory wording | No fairness or causal inference |
| Threshold dependence | B7 and DCA | Put full threshold profiles in Supplement | No safe or deployable threshold |
| Ecosystem-specific fitting | Across cohorts | State separate fitting by ecosystem | Not one universal shared-parameter model |

## 10. Main-text versus Supplement boundary

### Main text

1. Conditional-value research question and clinical-anchor rationale.
2. Cohort roles and prespecified Phase 6 governance.
3. Core B2/B6 evidence showing both favourable transfer and GSE65858 failure.
4. B7 primary 90% coverage, action distribution, and identical non-abstained-subset comparisons.
5. Concise falsification synthesis: Phase 5 failure, subgroup warning, radiomics negative controls, and exploratory DCA.
6. Minimal Phase 7 **post hoc exploratory** comparisons needed to demonstrate ecosystem-dependent ranking.
7. Mixed conclusion centred on auditability and failure boundaries.

### Supplement

1. Full B0–B7, M0/N0, and C1–C4 model definitions and results.
2. Seeds, hyperparameters, calibration details, training diagnostics, and complete cohort flow.
3. Full 80/90/100% gate profiles and action tables.
4. Complete stress tests, subgroup audits, negative controls, DCA thresholds, and Phase 7 post hoc exploratory comparisons.
5. Software environment, commands, model card, and reporting checklists.

### Phase 8 boundary

Phase 8 is excluded from the current Abstract, Introduction, Results, Discussion, Methods, title, and main-display plan. If a later supplementary version is explicitly approved, it may appear only as a **known-overlap workflow and bias simulation**, explicitly **not validation**. It does not support any current main-text claim.

## 11. Paragraph-to-argument crosswalk

| Paragraph | Function | Argument nodes | Principal claims |
|---|---|---|---|
| `ABS-01`–`ABS-04` | Gap, design, mixed result, restrained conclusion | A1–A11 | C01–C18, C20 synthesis |
| `INT-01` | Why “more modalities” is the wrong default question | A1 | Conceptual |
| `INT-02` | Clinical anchor and conditional incremental value | A1, A2 | C18 |
| `INT-03` | TRUST-HN reliability logic | A2 | C18 |
| `INT-04` | Objective and hypotheses | A3–A11 | C02, C20 |
| `RES-01` | Ecosystems as one prespecified transfer test | A2, A3 | C01, C02, C18 |
| `RES-02` | Positive transfer, central failure, sensitivity boundary | A4–A6 | C03–C06 |
| `RES-03` | Coverage, actions, and conditional gate performance | A7, A8 | C07–C10 |
| `RES-04` | Integrated falsification | A9 | C11–C14 |
| `RES-05` | Post hoc comparator rank reversal | A10 | C15–C17 |
| `DIS-01` | Central finding | A4–A11 | C20 |
| `DIS-02` | Meaning of clinical anchoring | A1–A4 | C03, C04, C18 |
| `DIS-03` | Meaning and limits of gating | A7, A8 | C07–C11 |
| `DIS-04` | Cross-platform calibration bottleneck | A5 | C05 |
| `DIS-05` | Why falsification and rank reversal matter | A9, A10 | C11–C17 |
| `DIS-06` | Strengths, limitations, next steps, conclusion | A11 | C18, C20 |
| `MET-01`–`MET-08` | Design, cohorts, models, reliability, evaluation, falsification, exploratory comparisons | A2–A10 | C01–C18 |

## 12. Non-negotiable language constraints

- Phase 6: “prespecified retrospective locked/OOD/external evaluation,” never prospective.
- Phase 7: every substantive mention includes **post hoc exploratory**.
- B7: report coverage with absolute performance and compare directly only on the identical non-abstained subset.
- GSE41613: “restricted retrospective HPV-negative OSCC sensitivity analysis.”
- DCA: “retrospective exploratory curve behaviour”; no clinical-utility, treatment-benefit, or patient-benefit claim.
- AUGMENT/FALLBACK/ABSTAIN: algorithmic outputs only.
- The paper must preserve favourable, negative, and inconsistent findings in the same scientific narrative.
- Phase 8 is not part of the current main-body plan.
