# Trustworthy prognostic artificial intelligence for head and neck squamous cell carcinoma under shortcut learning, missing modalities and distribution shift

> **Working manuscript after Phase 6.** The numerical Results are linked to frozen aggregate tables. Literature references, author metadata, cohort accession table, ethics wording and journal formatting remain to be finalized in the publication phase. This draft must not be interpreted as a clinical deployment document.

## Abstract

### Background

Multimodal prognostic models may exploit non-transportable shortcuts, fail when additional modalities are unavailable and remain overconfident under distribution shift. We evaluated whether a lightweight reliability layer could identify when an additional modality should augment a clinical risk anchor, when prediction should fall back to that anchor and when automated prediction should be withheld.

### Methods

We conducted a prespecified retrospective evaluation across separate public head and neck cancer data ecosystems. Models were trained separately for each ecosystem and shared a common architecture: a clinical elastic-net Cox anchor (B2), a modality-only model (B4), direct fusion (B5), residual fusion (B6) and a reliability-gated layer (B7) producing AUGMENT, FALLBACK or ABSTAIN actions. The frozen primary gate used equal reliability-component weights at nominal 90% calibration coverage. One-time locked evaluation included RADCURE (n=626), the HANCOCK out-of-distribution test split (n=152), GSE65858 external transcriptomic validation (n=244) and GSE41613 sensitivity analysis (n=97). Primary evaluation at 24 months included IPCW Brier score, Uno C, time-dependent AUC, calibration, coverage, decision curves and 2,000-replicate patient-level paired bootstrap comparisons. RADCURE included prespecified shuffled and randomized radiomic negative controls.

### Results

In RADCURE, B6 achieved an IPCW Brier score of 0.0980 and 24-month AUC of 0.7838. B7 covered 93.3% of patients and had an unpaired selective Brier score of 0.0913, but on the identical retained subset it was worse than B6 for Brier score (difference +0.00382, 95% CI +0.00084 to +0.00718) and AUC (-0.01662, -0.03467 to -0.00053). In HANCOCK, B6 achieved a Brier score of 0.1122 and AUC of 0.8476; B7 covered 82.9%, and its paired Brier difference versus B6 was +0.01058 (-0.00947 to +0.03186). In GSE65858, B7 improved Brier score relative to B6 on retained patients (-0.00812, -0.01584 to -0.00183) but remained substantially worse than the clinical anchor (+0.07294, +0.04250 to +0.10389), indicating poor transport of absolute transcriptomic risk across platforms. Original RADCURE radiomics did not clearly outperform shuffled or randomized controls. Decision curves showed no consistent B7 advantage over B6.

### Conclusions

Fusion transferred well in the RADCURE and HANCOCK settings, but reliability gating did not consistently improve forced fusion and cross-platform transcriptomic calibration failed. The framework provides an auditable method for communicating selective use, fallback and abstention, but the current retrospective evidence does not establish universal shift robustness, prospective validity, clinical utility or deployable gate thresholds.

## Introduction

Clinical prognostic modeling increasingly combines routinely available variables with imaging, pathology, blood biomarkers or molecular measurements. The attraction of multimodal learning is straightforward: an added modality may contain incremental prognostic information. However, a model can also learn cohort-specific correlations, quality-control artifacts or proxies that do not transport to a new hospital, assay or treatment pathway. A system that always forces fusion may therefore be more confident without being more clinically reliable.

TRUST-HN was designed around a clinical anchor rather than the assumption that more data are always beneficial. The framework asks three patient-level questions. First, are the clinical inputs and the anchor prediction sufficiently reliable to permit automated output? Second, is the additional modality available and sufficiently similar to the development distribution? Third, is the fused prediction stable enough to justify using the added modality? The output is one of three states: AUGMENT with the fused model, FALLBACK to the clinical anchor or ABSTAIN from automated prediction.

The project evaluates a common reliability principle in different data ecosystems, not a single universal model with shared parameters. The prespecified settings were pretreatment CT radiomics with shortcut controls, surgical multimodal data with an official OOD split and transcriptomic transfer from RNA sequencing to microarray cohorts. We hypothesized that gating would alter model coverage under shift and missingness and might reduce error relative to compulsory fusion. Equally important, the protocol required reporting failures, including cases where the gate did not outperform fusion or where an additional modality failed external calibration.

## Methods

### Study design and governance

This was a retrospective computational study using public data. Development, calibration, locked-test, OOD-test, external-test and sensitivity roles were defined before the Phase 6 outcomes were accessed. The statistical plan, model configuration, seeds, gate profile, cohort counts and ordered identifier-set digests were hash-frozen. Phase 6 required a one-time authorization whose hash was registered before outcome access. Outcome-free feature loading, alignment and prediction were completed before the authorization was consumed. After unsealing, outcomes could be used only for the prespecified evaluation; they could not be used for preprocessing, feature selection, model selection, hyperparameter tuning, threshold tuning, gate switching or recalibration.

Patient-level outputs were written only to a version-control-ignored directory. Tracked results contain aggregate statistics and figures. The registered decision files were not modified after outcomes were viewed.

### Data ecosystems and evaluation cohorts

RADCURE represented the pretreatment CT-radiomics setting. Its locked retrospective test included 626 patients and 110 observed events in the analyzed outcome table. Original PyRadiomics vectors were evaluated together with prespecified shuffled and randomized assays intended to test whether apparent performance depended on modality-specific structure.

HANCOCK represented a surgical multimodal setting combining structured clinical variables with available blood and tissue-microarray features. The official OOD test comprised 152 patients and 40 events. Missing additional-modality values were retained and handled by preprocessing and the reliability gate rather than by deleting the patient from the frozen cohort.

The transcriptomic setting used a model developed in TCGA-HNSC and evaluated in independent microarray cohorts. GSE65858 was the primary external test (244 patients, 78 events). GSE41613 was a sensitivity cohort (97 patients, 51 events) restricted to a different disease composition and was not treated as general HNSCC validation.

### Outcome and prediction horizon

The primary endpoint was all-cause overall survival at 24 months (730.5 days), with censoring handled through inverse-probability-of-censoring weighting. Cohort-specific source fields and follow-up units were harmonized according to the frozen data adapters. Because index dates and treatment pathways differ across ecosystems, cohorts were not pooled into one patient-level training table.

### Models

B2 was a clinical elastic-net Cox anchor. B4 used only the additional modality. B5 directly concatenated clinical and modality features. B6 was a stacked residual Cox learner that combined a cross-fitted B2 anchor score with a training-derived modality representation. B7 was a decision layer over B2 and B6. It returned ABSTAIN when the clinical input or total prediction was unreliable; otherwise it returned FALLBACK to B2 when the added modality was missing or unreliable, and AUGMENT with B6 when both inputs were acceptable.

Preprocessing was learned only from the relevant training data. Numeric RADCURE radiomic features excluded identifiers, metadata and diagnostic fields and underwent foldwise variance selection capped at 500 features. Transcriptomic transfer used an outcome-independent intersection of uppercase gene symbols, median aggregation of duplicate symbols, within-sample ranks and foldwise variance selection capped at 500 features.

### Reliability estimation and seed aggregation

The frozen primary gate combined the prespecified reliability components with equal weights and nominal 90% calibration coverage. Profiles at 80% and 100% were sensitivity analyses and were not substituted after outcome access. Five frozen seeds (17, 29, 43, 71 and 101) were used. Base-model predictions were averaged across seeds. B7 actions were combined by majority vote with a minimum of three votes and precedence of ABSTAIN, then FALLBACK, then AUGMENT. Consensus fallback predictions used the mean B2 risk; consensus abstentions had no automated B7 risk.

### Statistical analysis

Metrics included 24-month IPCW Brier score, Harrell C, Uno C, time-dependent AUC, calibration-in-the-large, calibration slope, mean predicted risk, coverage and action rates. Decision-curve net benefit was evaluated at thresholds from 0.05 to 0.50. Uncertainty used 2,000 patient-level bootstrap replicates with the same resampled indices for compared models within a cohort. To avoid biased comparison caused by selective abstention, B7-versus-B6 and B7-versus-B2 differences were calculated on the identical B7 non-abstained subset. Negative Brier differences favor B7; positive discrimination differences favor B7.

### Development-stage stress tests retained in interpretation

Before Phase 6, the development program evaluated random cell dropout, measurement noise, location shifts, row permutation, complete modality dropout, study-specific block dropout, gate ablations, coverage profiles and subgroup performance. Ten of ten study-seed runs completed and seven of eight prespecified acceptance checks passed. The primary HANCOCK gate failed clean B7-versus-B6 Brier noninferiority (+0.01550 versus margin +0.01000). Row permutation degraded B6 but only weakly changed fallback/abstention, and two exploratory TCGA-HNSC age >=65 analyses exceeded the 0.03 Brier-regret flag. These findings remained binding limitations during interpretation of Phase 6.

## Results

### Locked RADCURE evaluation

B2 achieved an IPCW Brier score of 0.1091, Uno C of 0.7078 and 24-month AUC of 0.7145. B6 improved these point estimates to 0.0980, 0.7740 and 0.7838, respectively. B7 produced predictions for 584 of 626 patients (93.3% coverage), with selective Brier 0.0913, Uno C 0.7567 and AUC 0.7602.

On the identical 584-patient retained subset, however, B7 was worse than B6: Brier difference +0.00382 (95% CI +0.00084 to +0.00718), Uno C difference -0.01423 (-0.03088 to -0.00067) and AUC difference -0.01662 (-0.03467 to -0.00053). B7 remained better than B2 on this subset for Brier (-0.00489, -0.00795 to -0.00193) and AUC (+0.03720, +0.01086 to +0.06461). Thus, the apparently lower unpaired B7 Brier partly reflected selective coverage rather than superiority to B6.

At the primary gate, 82.1% of patients were assigned AUGMENT, 11.2% FALLBACK and 6.7% ABSTAIN.

### HANCOCK OOD evaluation

B2 achieved Brier 0.1393, Uno C 0.7476 and AUC 0.7864. B6 achieved Brier 0.1122, Uno C 0.8281 and AUC 0.8476. B7 covered 126 of 152 patients (82.9%) and had selective Brier 0.1055, Uno C 0.8249 and AUC 0.8461.

On the retained subset, the B7-versus-B6 Brier difference was +0.01058 (95% CI -0.00947 to +0.03186) and the AUC difference was -0.00625 (-0.09059 to +0.07497). The B7-versus-B2 Brier difference was -0.00723 (-0.01612 to +0.00022). These intervals did not establish a B7 advantage. Actions were 64.5% AUGMENT, 18.4% FALLBACK and 17.1% ABSTAIN, demonstrating increased caution under OOD evaluation but also a substantial reduction in automated coverage.

### Cross-platform transcriptomic evaluation

In GSE65858, B2 achieved Brier 0.1964, Uno C 0.5843 and AUC 0.5893. B6 had modestly higher discrimination (Uno C 0.6066; AUC 0.6035) but substantially worse Brier score (0.2725) and calibration-in-the-large (-1.494). B7 covered 230 of 244 patients (94.3%) and achieved Brier 0.2672, Uno C 0.5892 and AUC 0.5839.

On the retained subset, B7 improved Brier relative to B6 (-0.00812, 95% CI -0.01584 to -0.00183), but was markedly worse than B2 (+0.07294, +0.04250 to +0.10389). Therefore, gating removed some fusion error without repairing the larger cross-platform absolute-risk failure. The primary actions were 92.6% AUGMENT, 1.6% FALLBACK and 5.7% ABSTAIN, indicating that the gate frequently accepted transcriptomic fusion despite poor external calibration.

In GSE41613, B2 was constant and non-discriminating (Uno C and AUC 0.5000). B6 achieved Brier 0.2742 and AUC 0.6377; B7 covered all 97 patients, with Brier 0.2611 and AUC 0.6555. The B7-versus-B6 Brier difference was -0.01314 (-0.03153 to +0.00215). B7-versus-B2 AUC was +0.15551 (+0.02973 to +0.27362), but the deficient clinical comparator and distinct HPV-negative OSCC population limit interpretation.

### Radiomic negative controls

Original RADCURE radiomics did not clearly outperform either the shuffled or randomized assay. All B4/B5/B6/B7 original-minus-control Brier confidence intervals included zero. For B6, original-minus-shuffled Brier was +0.00124 (-0.00105 to +0.00334), and original-minus-randomized Brier was +0.00063 (-0.00200 to +0.00306). For B7, the corresponding differences were -0.00130 (-0.00366 to +0.00078) and -0.00026 (-0.00286 to +0.00238). The results do not support a radiomics-specific biological-signal claim.

### Decision curves and action distributions

Across the prespecified thresholds, B7 did not show a consistent net-benefit advantage. It was below B6 at all evaluated thresholds in RADCURE and HANCOCK and at most thresholds in GSE65858. The action distribution varied substantially by cohort: non-abstention coverage was 93.3% in RADCURE, 82.9% in HANCOCK, 94.3% in GSE65858 and 100% in GSE41613. These retrospective rates describe model behavior but do not define an acceptable clinical workload or safety threshold.

## Discussion

The main finding is not that reliability gating universally improved prognostic accuracy. Instead, Phase 6 showed that fusion and gate behavior were strongly cohort-dependent. Residual fusion transferred well in RADCURE and HANCOCK, whereas the primary gate did not outperform B6 on retained RADCURE patients and produced uncertain differences in HANCOCK. In the independent transcriptomic cohort GSE65858, gating modestly reduced B6 error but failed to detect or correct the larger absolute-risk transport problem. A reliability layer can therefore communicate caution and alter coverage without guaranteeing that accepted fused predictions are calibrated.

The RADCURE negative controls are especially important. Similar performance from original, shuffled and randomized radiomic assays weakens any interpretation that the gains arose from specific tumor-image biology. The model may have relied substantially on the clinical anchor, non-specific distributional information or properties retained by the control construction. This result illustrates why negative controls are required when evaluating shortcut-aware multimodal systems.

The selective-prediction analysis also shows why unpaired B7 metrics can be misleading. B7's lower raw Brier score in several cohorts was calculated only among non-abstained patients. When B7 and B6 were compared on the identical retained subset, B7 was worse in RADCURE. Coverage and performance must therefore be reported together, and abstention cannot be treated as a free removal of difficult patients.

The study has several strengths: prespecified outcome-free preprocessing, explicit cohort roles, hash-registered decision files, one-time unsealing, paired patient-level bootstrap comparisons, tracked negative findings and aggregate-only public-facing outputs. These controls reduce outcome-guided optimism in the locked analyses.

The limitations remain substantial. All data are retrospective. The systems were separately trained within different data ecosystems and do not constitute one universal model. Index dates, predictors, treatments and ascertainment differ across cohorts. Event counts after abstention were limited in some analyses. The primary gate failed one Phase 5 noninferiority criterion, responded weakly to row permutation and did not consistently improve B6 in Phase 6. The transcriptomic gate accepted most GSE65858 patients despite severe calibration degradation. The GSE41613 clinical comparator was non-informative, limiting sensitivity conclusions. No prospective workflow, real-time quality-control process, clinician interaction study, recalibration policy or impact trial has been performed.

Consequently, the results support retrospective validation of a reliability-oriented framework and demonstrate the value of reporting fallback, abstention and negative controls. They do not prove robustness under all distribution shifts, external generalizability of a single model, prospective validity, clinical utility, causal benefit or deployment readiness. Future work should prospectively register a site-specific model and gate, specify operational responses to FALLBACK and ABSTAIN, define acceptable coverage and safety margins, evaluate calibration before impact testing and measure both patient outcomes and clinician workload.

## Data availability

All source datasets are publicly available subject to their original access, citation and redistribution conditions. Final repository accessions, versions, licences and non-redistributable-file boundaries will be listed in the submission-ready data-availability statement. Patient-level derived predictions are not intended for version control; only aggregate evaluation outputs are tracked.

## Code availability

The analysis is implemented in the local `trust-hn` repository with configuration-driven scripts, tests, frozen hashes and aggregate receipts. A public archival release, permanent identifier and clean-environment reproduction instructions remain to be completed before submission. Registered Phase 6 decision files must not be edited after outcome access.

## Ethics and patient involvement

The study used public retrospective datasets and did not recruit participants prospectively. Dataset-specific ethics and consent statements will be reproduced from the primary source documentation in the final manuscript. No patient or public involvement has been documented for the computational study; this will be stated transparently if unchanged.

## Declarations

Funding, conflicts of interest, author contributions and acknowledgements await author-provided information.
