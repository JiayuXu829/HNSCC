# Figure legends

## Figure 1. Conceptual TRUST-HN reliability framework

The clinical anchor (B2) provides the default prognostic risk. Additional-modality information is modeled separately and through residual fusion (B6). The reliability layer combines clinical-input reliability, modality availability/shift and predictive uncertainty to assign AUGMENT, FALLBACK or ABSTAIN. AUGMENT returns the fused risk, FALLBACK returns the clinical-anchor risk and ABSTAIN withholds an automated risk. This is a retrospective research framework, not a treatment recommendation.

## Figure 2. Phase 6 24-month IPCW Brier scores across evaluation cohorts

Aggregate point estimates for B2, B4, B5, B6 and B7 in RADCURE, HANCOCK, GSE65858 and GSE41613. Lower values indicate lower prediction error. B7 estimates are conditional on non-abstention and therefore must be interpreted with the reported coverage and same-subset paired comparisons. Source: `results/figures/phase6/cohort_brier.svg`.

## Figure 3. Primary gate action distributions

Proportions assigned AUGMENT, FALLBACK and ABSTAIN by the frozen equal-weight nominal 90% gate. Non-abstention coverage was 93.3% in RADCURE, 82.9% in HANCOCK, 94.3% in GSE65858 and 100.0% in GSE41613. The distributions are retrospective empirical behavior and do not establish clinically acceptable thresholds. Source: `results/figures/phase6/action_distribution.svg`.

## Figure 4. Paired Brier-score differences on identical patient subsets

B7-minus-comparator differences and 95% patient-level paired bootstrap confidence intervals. B7-versus-B6 and B7-versus-B2 comparisons use the identical B7 non-abstained subset within each cohort. Negative values favor B7. In RADCURE, B7 was worse than B6 but better than B2. In GSE65858, B7 improved over B6 but remained substantially worse than B2. Source: `results/figures/phase6/paired_brier_differences.svg`.

## Figure 5. Retrospective decision-curve analysis

Net benefit for B2, B6 and B7 at prespecified risk thresholds from 0.05 to 0.50. B7 did not show a consistent advantage and was below B6 across all evaluated thresholds in RADCURE and HANCOCK and across most thresholds in GSE65858. Because the study did not prospectively define management for abstained patients, the curves do not establish clinical utility. Source: `results/figures/phase6/decision_curve.svg`.

## Supplementary Figure S1. Development-stage stress-test overview

Performance, coverage and action response under random missingness, measurement noise, location shift, row permutation, complete modality dropout and study-specific modality-block dropout. Row permutation materially degraded B6 but produced only a weak increase in fallback/abstention, indicating incomplete detection of semantic modality misalignment.

## Supplementary Figure S2. RADCURE radiomic negative controls

Original PyRadiomics predictions compared with shuffled and randomized feature assays. Original radiomics did not clearly outperform either control for B4, B5, B6 or B7; all original-minus-control Brier confidence intervals crossed zero. These results preclude a claim of radiomics-specific biological signal.
