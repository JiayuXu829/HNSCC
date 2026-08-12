# TRUST-HN WP2 Argument Map

**Version date:** 2026-08-12  
**Status:** WP2 planning artifact; not manuscript prose.  
**Evidence interface:** `evidence_map.csv` and bilingual WP1 claim matrices are binding.  
**Approval boundary:** no full prose, figure production, or WP3+ work is authorized by this document.

## 1. Provisional titles and short title

### Leading title (provisional)

**Clinical anchoring and reliability-aware multimodal prognostic modelling across heterogeneous head and neck cancer data ecosystems**

### Alternative title A (provisional)

**Cohort-dependent multimodal prognosis and reliability gating in head and neck squamous cell carcinoma**

### Alternative title B (provisional)

**Reliability-aware fallback and abstention reveal limits of multimodal prognosis across heterogeneous HNSCC cohorts**

### Short title (provisional)

**Reliability-aware multimodal HNSCC prognosis**

### Title guardrails

- Do not use unqualified ?trustworthy,? ?robust,? ?validated,? ?clinically useful,? or ?deployment-ready.?
- Titles remain provisional until Results, Discussion, figures/tables, and Abstract are stabilized.
- Phase 7 and Phase 8 methods/results must not drive an apparently confirmatory title.

## 2. Primary research question

In retrospective HNSCC data ecosystems with different modality availability and distribution shifts, can a clinical-anchor-plus-incremental-fusion framework characterize when additional modalities improve 24-month overall-survival prediction and use reliability-aware AUGMENT/FALLBACK/ABSTAIN behaviour to expose?rather than conceal?failure of forced multimodal fusion?

### Secondary questions

1. How do B2 (clinical anchor), B6 (full incremental fusion), and B7 (reliability-gated selective prediction) behave in prespecified locked, OOD, cross-platform external, and restricted sensitivity settings?
2. Does B7 preserve performance relative to B6 on the **identical non-abstained subset**, and at what coverage?
3. Do negative controls, development stress tests, and exploratory decision curves support modality specificity, general robustness, or clinical utility?
4. Do Phase 7 **post hoc exploratory** comparators reveal a universally superior modelling strategy?
5. What failure boundaries must be resolved before prospective evaluation or deployment-oriented threshold selection?

## 3. One-sentence answer to be defended

Across heterogeneous HNSCC data ecosystems, multimodal prognostic gains and reliability-gating behaviour were strongly cohort dependent; reliability-aware fallback and abstention exposed failure modes of forced fusion, but current retrospective evidence did not establish universal robustness, deployable thresholds, or clinical utility.

## 4. Contribution hierarchy

### Primary contribution

A transparent and auditable reliability framework that combines a clinical anchor, incremental/residual multimodal fusion, reliability assessment, and algorithmic AUGMENT/FALLBACK/ABSTAIN outputs while making coverage and failure boundaries explicit.

### Empirical contribution

A prespecified Phase 6 retrospective evaluation showing relatively favourable B6 transfer in RADCURE and HANCOCK alongside substantial cross-platform calibration failure in GSE65858 and restricted, uncertain evidence in GSE41613.

### Reliability contribution

A selective-prediction analysis showing that B7 changed coverage and action distributions but did not consistently outperform B6 on identical non-abstained subsets.

### Falsification contribution

Negative controls, stress tests, and exploratory DCA constrain interpretation: observed discrimination cannot be equated with radiomics-specific biological signal, universal robustness, clinical utility, or deployment readiness.

### Comparative contribution

Phase 7 **post hoc exploratory** comparators demonstrate cohort-dependent rankings and no universal winner; strong performance in one ecosystem can coexist with calibration failure in another.

### Governance contribution

A strict separation of frozen/prespecified Phase 6 evidence, post hoc exploratory Phase 7 evidence, and Phase 8 known-overlap workflow/bias simulation.

## 5. Main argument chain

| Node | Claim | Primary support | Mandatory counterevidence/qualifier | Planned paragraphs |
|---|---|---|---|---|
| A1 | Additional modalities may add prognostic information but create missingness, shortcut, and platform-shift risks. | Conceptual framing; cohort/modality heterogeneity in C01 and C18 | Do not imply that every modality is beneficial or biologically specific. | `INT-01`, `INT-02`, `DIS-02` |
| A2 | TRUST-HN operationalizes clinical anchoring, incremental/residual fusion, reliability assessment, and selective output behaviour. | C18; governance `GOV-ANCHOR-001`?`GOV-ANCHOR-004` | Separate models were trained for different ecosystems; this is not one universal shared-parameter HNSCC model. | `INT-03`, `MET-03`, `MET-04` |
| A3 | B6 showed favourable retrospective transfer relative to the clinical-anchor point estimates in RADCURE and HANCOCK. | C03?C04; `P6-ABS-R002-*`, `P6-ABS-R005-*`, `P6-ABS-R007-*`, `P6-ABS-R010-*` | Absolute B2/B6 contrasts are descriptive unless a corresponding paired comparison is cited; results do not cover all institutions or shifts. | `RES-03`, `DIS-02` |
| A4 | Cross-platform GSE65858 exposed major calibration failure and worse Brier scores for fusion than B2. | C05; `P6-ABS-R012-IPCW-BRIER`, `P6-ABS-R015-IPCW-BRIER`, `P6-ABS-R016-IPCW-BRIER`, calibration rows | Discrimination must never be reported without calibration and Brier evidence in this cohort. | `RES-04`, `DIS-04` |
| A5 | B7 produced cohort-dependent coverage and AUGMENT/FALLBACK/ABSTAIN actions, but did not consistently improve on B6. | C07?C10; `P6-ACTION-*`; `P6-PAIR-R002`, `R005`, `R008`, `R011` | Every B7 performance statement must report coverage and use the identical non-abstained subset for direct comparison. Actions are algorithmic outputs, not clinical recommendations. | `RES-05`, `DIS-03` |
| A6 | Development stress tests and radiomics negative controls prevent a simple universal-robustness or modality-specificity interpretation. | C11?C13; `P5-CHECK-R002`?`R009`; `P5-FLAG-R055`, `R071`; `P6-NEG-PAIR-R017`?`R048` | Phase 5 is development-only; negative controls do not prove absence of all signal, but do not support a clear original-radiomics advantage. | `RES-02`, `RES-06`, `DIS-05` |
| A7 | Exploratory DCA did not show a consistent B7 advantage over B6. | C14; `P6-DCA-R022`?`R031`, `R052`?`R061`, `R082`?`R091`, `R112`?`R121` | DCA is retrospective and exploratory; it does not establish clinical utility, patient benefit, or deployable thresholds. | `RES-07`, `DIS-07` |
| A8 | Strong Phase 7 comparators were cohort dependent; no universal winner existed. | C15?C17; `P7-EXT-R003-*`, `P7-EXT-R007-*`, `P7-EXT-R011-*`, `P7-EXT-R012-*`; paired rows | Every occurrence must be labelled **post hoc exploratory**; do not merge with Phase 6 confirmatory framing. | `RES-08`, `DIS-06` |
| A9 | Phase 8 is useful only as a known-overlap workflow and bias demonstration. | C19; `GOV-ANCHOR-007`?`011`; selected `P8-*` rows | Not independent, private, institutional, external, or prospective validation; supplementary-only by default. | `MET-09`, `DIS-07`, Supplement |
| A10 | The evidence supports an auditable framework with explicit boundaries, not deployment readiness. | C20 synthesis | Preserve positive, negative, and inconsistent findings together. | `ABS-05`, `DIS-01`, `DIS-07` |

## 6. Quantitative anchors for the main narrative

### RADCURE ? prespecified locked retrospective test

- B2: Brier 0.1091, Uno C 0.7078, 24-month AUC 0.7145 (`P6-ABS-R002-IPCW-BRIER`, `P6-ABS-R002-UNO-C`, `P6-ABS-R002-AUC-HORIZON`).
- B6: Brier 0.0980, Uno C 0.7740, AUC 0.7838 (`P6-ABS-R005-IPCW-BRIER`, `P6-ABS-R005-UNO-C`, `P6-ABS-R005-AUC-HORIZON`).
- B7: coverage 0.9329 (584/626); B7-vs-B6 Brier difference +0.00382 (95% CI +0.00084 to +0.00718); B7-vs-B2 ?0.00489 (?0.00795 to ?0.00193) on the identical non-abstained subset (`P6-PAIR-R002`, `P6-PAIR-R003`).

### HANCOCK ? prespecified retrospective OOD sealed test

- B2: Brier 0.1393, Uno C 0.7476, AUC 0.7864 (`P6-ABS-R007-IPCW-BRIER`, `P6-ABS-R007-UNO-C`, `P6-ABS-R007-AUC-HORIZON`).
- B6: Brier 0.1122, Uno C 0.8281, AUC 0.8476 (`P6-ABS-R010-IPCW-BRIER`, `P6-ABS-R010-UNO-C`, `P6-ABS-R010-AUC-HORIZON`).
- B7: coverage 0.8289 (126/152); B7-vs-B6 +0.01058 (?0.00947 to +0.03186); B7-vs-B2 ?0.00723 (?0.01612 to +0.00022) on the identical non-abstained subset (`P6-PAIR-R005`, `P6-PAIR-R006`).

### GSE65858 ? prespecified retrospective external cross-platform test

- B2 Brier 0.1964; B6 Brier 0.2725, calibration-in-the-large ?1.494, slope 0.599; B7 Brier 0.2672, calibration-in-the-large ?1.548, slope 0.560 with coverage 0.9426 (230/244).
- B7-vs-B6 ?0.00812 (?0.01584 to ?0.00183), but B7-vs-B2 +0.07294 (+0.04250 to +0.10389), on the identical non-abstained subset (`P6-PAIR-R008`, `P6-PAIR-R009`).
- Interpretation: gating modestly improved Brier relative to forced B6 among covered patients, yet both fusion approaches remained substantially worse calibrated/scored than B2.

### GSE41613 ? restricted retrospective HPV-negative OSCC sensitivity cohort

- n=97; B7 coverage 1.0.
- B2 was constant/non-discriminating (Uno C and AUC 0.5); B7-vs-B6 Brier ?0.01314 (?0.03153 to +0.00215) and B7-vs-B2 ?0.00632 (?0.04051 to +0.03008), both uncertain (`P6-PAIR-R011`, `P6-PAIR-R012`).
- Interpretation must remain sensitivity-only and cannot support general HNSCC external validity.

## 7. Counterevidence and negative-result ledger

| Counterevidence | Required interpretation | Forbidden over-interpretation | Planned paragraphs |
|---|---|---|---|
| HANCOCK Phase 5 clean B7-vs-B6 Brier check failed: +0.01550 against ?0.01. | One of eight prespecified development checks failed; gating was not uniformly benign even before locked evaluation. | ?The gate passed all stress tests? or ?proved safe.? | `RES-02`, `DIS-03` |
| TCGA-HNSC age ?65 seed-level flags (n=34; seeds 29 and 71). | Exploratory, small, multiple-comparison and seed-specific warning. | Fairness, subgroup validity, or causal claim. | `RES-02`, Supplement |
| GSE65858 B6/B7 calibration failure. | Cross-platform transcriptomic transfer can dominate apparent discrimination. | Robust cross-platform validity. | `RES-04`, `DIS-04` |
| B7 worse than B6 in RADCURE paired Brier and uncertain in HANCOCK. | Selective behaviour does not guarantee better accuracy. | Universal B7 superiority. | `RES-05`, `DIS-03` |
| Radiomics original-vs-shuffled/randomized Brier CIs cross zero. | No clear original-radiomics advantage in these controls. | Proof of radiomics-specific biology or proof that radiomics is always useless. | `RES-06`, `DIS-05` |
| B7 DCA below B6 at 10/10 RADCURE, 10/10 HANCOCK, and 8/10 GSE65858 thresholds. | No consistent exploratory curve advantage. | Clinical utility, patient benefit, or deployable threshold. | `RES-07` |
| Phase 7 C2 strong in RADCURE/HANCOCK but failed in GSE65858; C3 improved vs B6 there but B2 remained lower. | Rankings depend on ecosystem and calibration. | Universal winner or confirmatory superiority. | `RES-08`, `DIS-06` |
| C4 equalled B5 externally. | Added comparator structure did not yield incremental external benefit in this implementation. | Universal irrelevance of the underlying modality or architecture. | `RES-08`, Supplement |
| Phase 8 includes 88 training, 17 calibration, and 30 prior-test overlaps. | Workflow/bias demonstration only. | Independent validation. | Supplement; at most a brief boundary statement in `DIS-07` |

## 8. Threat-to-validity map

| Threat | Where it enters | Mitigation/diagnostic | Residual limitation |
|---|---|---|---|
| Retrospective selection and dataset shift | All cohorts | Prespecified roles, sealed tests, explicit ecosystem labels | Cannot establish prospective validity or real-world benefit |
| Cross-platform transcriptomic shift | TCGA-HNSC to GSE65858 | External cross-platform test; calibration reporting | No evidence that the present mapping/calibration generalizes to other platforms |
| Missing modalities and selective coverage | B7 | Coverage, action rates, identical non-abstained-subset comparisons | Selective evaluation can change case mix; abstention handling is not clinically validated |
| Shortcut/non-specific radiomic signal | RADCURE | Shuffled and randomized negative controls | Controls are finite and do not fully establish biological mechanism |
| Model-selection multiplicity | Phase 7 | Explicit post hoc exploratory label; cohort-wise reporting | Comparative ranking may be optimistic and requires independent confirmation |
| Small restricted sensitivity cohort | GSE41613 | Sensitivity-only label; CIs | n=97 HPV-negative OSCC cannot represent general HNSCC |
| Subgroup multiplicity and small cells | Phase 5 | Exploratory flagging; seed-level disclosure | No confirmatory fairness inference |
| Threshold dependence | B7 and DCA | 80/90/100% sensitivity analyses in Supplement | No deployable or safe threshold established |
| Data overlap | Phase 8 | Explicit overlap counts and separate reporting | Cannot estimate independent institutional generalization |
| Ecosystem-specific parameters | Across cohorts | Declare separate training by ecosystem | Does not yield one universal shared-parameter HNSCC model |

## 9. Main-text versus Supplement boundary

### Main text

1. Research question, clinical-anchor rationale, and reliability-aware architecture.
2. Cohort roles and sample flow.
3. Phase 6 frozen/prespecified governance.
4. Core B2/B6/B7 absolute results in RADCURE, HANCOCK, GSE65858, and restricted GSE41613 sensitivity analysis.
5. B7 90% profile coverage, action distribution, and identical non-abstained-subset paired comparisons.
6. GSE65858 calibration failure as a central failure boundary.
7. The failed HANCOCK Phase 5 check and concise stress-test qualification.
8. Key radiomics negative-control conclusion.
9. Exploratory DCA summary with explicit no-clinical-utility boundary.
10. Limited Phase 7 post hoc exploratory comparator synthesis demonstrating no universal winner.
11. Mixed overall conclusion.

### Supplement

1. Full B0?B7, M0/N0, and C1?C4 model definitions and results.
2. All development seeds, hyperparameters, calibration details, and training diagnostics.
3. Complete cohort flow, modality availability, missingness, exclusions, and endpoint accounting.
4. Full 80/90/100% gate profiles and action tables.
5. Complete negative controls, stress tests, ablations, and subgroup results.
6. All DCA thresholds and curves.
7. Full Phase 7 post hoc exploratory comparator tables and paired bootstrap results.
8. Entire Phase 8 `inner_hancock` known-overlap workflow and bias simulation, including overlap composition.
9. Software environment, commands, model card, and TRIPOD+AI/PROBAST+AI/STROBE materials.

### Phase 8 rule

Phase 8 is supplementary-only by default. A future main-text sentence may only state that a known-overlap simulation was performed to demonstrate workflow and bias sensitivity; it must not present the exercise as validation.

## 10. Paragraph-to-argument crosswalk

| Paragraph | Function | Argument nodes | Principal claims |
|---|---|---|---|
| `ABS-01`?`ABS-05` | Condense background, design, main mixed results, limits, conclusion | A1?A10 | C01?C20 synthesis |
| `INT-01` | Clinical and modelling problem | A1 | Conceptual |
| `INT-02` | Why reliability and failure reporting matter | A1, A6 | C11?C14 |
| `INT-03` | TRUST-HN design logic | A2 | C18 |
| `INT-04` | Study objective and hypotheses | A3?A10 | C02, C20 |
| `RES-01` | Cohorts and governance | A2 | C01?C02 |
| `RES-02` | Development readiness and stress tests | A6 | C11?C12 |
| `RES-03` | RADCURE/HANCOCK B6 transfer | A3 | C03?C04 |
| `RES-04` | Cross-platform failure and sensitivity boundary | A4 | C05?C06 |
| `RES-05` | B7 coverage/actions/paired comparisons | A5 | C07?C10 |
| `RES-06` | Radiomics negative controls | A6 | C13 |
| `RES-07` | Exploratory DCA | A7 | C14 |
| `RES-08` | Post hoc comparators and model ranking | A8 | C15?C17 |
| `DIS-01` | Principal findings | A3?A10 | C20 |
| `DIS-02` | Meaning of B6 gains | A3 | C03?C04 |
| `DIS-03` | Meaning and limits of gating | A5 | C07?C11 |
| `DIS-04` | Cross-platform calibration failure | A4 | C05 |
| `DIS-05` | Negative controls and specificity | A6 | C12?C13 |
| `DIS-06` | Comparator ranking and no universal winner | A8 | C15?C18 |
| `DIS-07` | Strengths, limitations, translation conditions, conclusion | A7?A10 | C14, C19, C20 |
| `MET-01`?`MET-09` | Design, cohorts, models, reliability, evaluation, governance | A2?A9 | C01?C19 |

## 11. Non-negotiable language constraints

- Phase 6: ?prespecified retrospective locked/OOD/external evaluation,? never prospective.
- Phase 7: every substantive mention includes **post hoc exploratory**.
- Phase 8: ?known-overlap workflow and bias simulation,? explicitly **not validation**.
- B7: report coverage with absolute performance and use the identical non-abstained subset for paired comparisons.
- GSE41613: ?restricted retrospective HPV-negative OSCC sensitivity analysis.?
- DCA: ?retrospective exploratory curve behaviour?; no clinical-utility or patient-benefit claim.
- AUGMENT/FALLBACK/ABSTAIN: algorithmic outputs only.
- The final narrative must preserve favourable, negative, and inconsistent results together.
