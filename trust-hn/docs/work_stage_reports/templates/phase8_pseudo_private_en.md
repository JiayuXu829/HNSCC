# Phase 8: inner_hancock pseudo-private overlap simulation

Generated: 2026-08-11

## Claim boundary

> **This technical simulation relabels 135 cases with known HANCOCK development/test overlap as inner_hancock. It is not an independent institutional/private validation and cannot support external, prospective, or clinical-validation claims.**

## Design

- Cohort alias: `inner_hancock`; n=135.
- Known source composition: 88 training, 17 calibration, and 30 sealed-test cases.
- Endpoint: 24-month overall-survival risk (730.5 days).
- Methods: 14 (B0-B7, M0, N0, C1-C4).
- Seeds: {seeds}; patient-level metric bootstrap: {bootstrap_replicates} replicates.
- Primary B7 gate: 90% coverage profile.

## Results

{table}

By IPCW Brier score, the apparent best method was **{best_model}** (Brier={best_brier}, Harrell C={best_harrell}, AUC={best_auc}). B7 coverage was {b7_coverage}; gate actions: {action_text}.

## Concordance with prior public-cohort results under a hypothetical true-external interpretation

This section addresses a counterfactual question only: **if the known overlap were ignored and `inner_hancock` were assumed to be a fully independent institutional cohort never used for training or calibration, would its conclusions agree with the Phase 6 public cohorts and the Phase 7 post hoc comparator analyses?** Under that assumption, the main research narrative is broadly concordant, although not every cohort or metric shows the same direction.

| Comparison | Prior public-cohort evidence | Phase 8 result | Concordance |
|---|---|---|---|
| B6 multimodal fusion vs B2 clinical anchor | B6 improved Brier and discrimination over B2 in RADCURE and HANCOCK; B6 had substantially worse Brier in GSE65858; GSE41613 showed better discrimination without improved Brier | B6 vs B2: Brier 0.0807 vs 0.1011, Uno C 0.8632 vs 0.5924, and 24-month AUC 0.8892 vs 0.6075 | Concordant with RADCURE/HANCOCK, but it does not overturn the cross-platform failure in GSE65858. It supports benefit in a similar data ecosystem, not robustness to every distribution shift |
| B7 gate vs B6 forced fusion | Phase 6 showed no consistent B7 advantage over B6; B7 was worse in RADCURE, inconclusive in HANCOCK, and mixed elsewhere | On the identical 122 non-abstained patients, B7 minus B6 was -0.0433 for Harrell C, -0.0868 for Uno C, -0.0864 for AUC, and +0.0113 for Brier | Strongly concordant: gating changes coverage but does not guarantee higher predictive accuracy; discrimination was lower here |
| B7 gate vs B2 clinical anchor | B7 outperformed B2 in RADCURE, evidence was imprecise in HANCOCK, calibration failed in GSE65858, and discrimination improved in GSE41613 | On the identical 122 patients, B7 minus B2 was +0.1152 for Harrell C, +0.1719 for Uno C, and +0.1841 for AUC, with all three 95% CIs above zero; Brier difference was -0.0040 with a CI near zero | Concordant with the finding that gated multimodal prediction can outperform the clinical anchor in some cohorts, while remaining cohort dependent |
| B7 selective coverage | Public-cohort coverage under the primary 90% gate ranged from 82.9% to 100.0%, with cohort-specific action distributions | Coverage was 90.4%; AUGMENT 85.2%, FALLBACK 5.2%, and ABSTAIN 9.6% | Concordant: the gate produces selective prediction and abstention, but its action distribution is cohort dependent |
| C2 XGBoost-Cox | In Phase 7, C2 was strongest in RADCURE and had the lowest Brier in HANCOCK, but its Brier deteriorated to 0.3429 with marked risk overestimation in GSE65858 | C2 was the apparent best method: Brier 0.0679, Uno C 0.9314, and AUC 0.9498 | Concordant with strong performance in RADCURE/HANCOCK-like ecosystems and with cohort-dependent model ranking; it does not establish universal external robustness for C2 |

### Conclusions if this were a genuinely independent external cohort

If the 135 cases were genuinely independent and had no training or calibration overlap, the results could be interpreted as follows:

1. In this external cohort, combining the additional modalities with clinical information provided strong risk stratification, with B6 point estimates better than the B2 clinical anchor.
2. C2 was the strongest comparator in this cohort, directionally replicating its relatively strong performance in the public RADCURE and HANCOCK cohorts.
3. B7 operated as a selective predictor at 90.4% coverage and withheld automated output for 9.6% of patients, demonstrating that the gating workflow can execute in a new cohort.
4. B7 outperformed B2 but not B6. The main value of the gate is therefore risk control, fallback, and abstention rather than a guarantee of higher accuracy than forced fusion.
5. Phase 8 would not overturn the negative public-cohort findings. Instead, it would reinforce the overall conclusion that **multimodal fusion and comparator performance are cohort dependent, gating does not consistently outperform forced fusion, and no model has been shown to be uniformly best across all data ecosystems.**

Accordingly, if this were a true independent cohort, the most defensible manuscript wording would be “directionally concordant validation in an additional retrospective institutional cohort,” not “proof of universal distribution-shift robustness.” Even under the true-external assumption, these results would not establish prospective effectiveness, clinical net benefit, deployable gate thresholds, or benefit to treatment decisions.

## Interpretation

These numbers answer what would be observed if the 135 cases were directly treated as a new private cohort. Because 105 cases originate from the prior training/calibration partitions, overlap produces optimistic bias. The results are suitable for pipeline debugging, code verification, and bias demonstration, but not as the manuscript's independent private-validation result.

## Outputs

- Aggregate metrics: `results/metrics/phase8_pseudo_private/`
- Patient predictions: `results/predictions/phase8_pseudo_private/` (Git-ignored)
- Figures: `results/figures/phase8_pseudo_private/`
- Audit receipt: `results/manifests/phase8_pseudo_private_simulation_receipt.json`
