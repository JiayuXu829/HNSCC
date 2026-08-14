# U1.2/V0 Approval Record

**status:** `APPROVED`
**approved_on:** 2026-08-14
**approved_by:** Researcher (chat approval)
**approval_text:** `审批 U1.2/V0，进入 U1.3/V1 smoke implementation。`  
**completed_on:** 2026-08-14  
**analysis_label:** `post_lock_exploratory`

## Approval object

Extended postoperative clinical-pathological elastic-net Cox safety anchor on eligible HANCOCK official-training records, evaluated by frozen repeated nested cross-fitting.

## Checklist

- [x] Confirm estimand: n=610, events=173, one nonpositive postoperative duration excluded.
- [x] Confirm anchor variables: age, sex, smoking, primary site, grading, p16, resection, pT, pN.
- [x] Confirm 5 seeds × 5 outer folds × 3 inner folds and 12-candidate frozen Coxnet grid.
- [x] Confirm every preprocessing and baseline-survival fit occurred inside the corresponding training fold.
- [x] Confirm 3050 OOF rows are patient-level and git-ignored; tracked artifacts are aggregate-only.
- [x] Confirm official-test outcomes were not derived, exposed, or evaluated.
- [x] Confirm the performance interpretation is limited to internal post-lock exploratory evidence.
- [x] Confirm V0 is approved as the safety anchor and fallback reference.

## Aggregate result summary

```text
IPCW Brier24:          0.1247 ± 0.0015
Harrell C:             0.6230 ± 0.0144
Uno C24:               0.6442 ± 0.0138
AUC24:                 0.6620 ± 0.0144
Calibration-in-large: -0.0037 ± 0.0149
Calibration slope:     0.9367 ± 0.0792
```

## Supporting artifacts

```text
core_backbone/U1_2_V0_clinical_anchor/frozen_v0_spec.yaml
core_backbone/U1_2_V0_clinical_anchor/aggregate_v0_audit.json
audits/U1_2_V0_clinical_anchor_audit.md
reports/2026-08-14_step_U1_2_V0_clinical_anchor.md
docs/work_stage_reports/zh-CN/2026-08-14_pattern_surv_hn_step_U1_2_V0_report.md
```

## Authorization if approved

Approval authorizes only **U1.3/V1 smoke implementation** of the minimum Clinical-Residual Deep Sets Cox backbone and its structural tests. It does not automatically authorize formal V1 development cross-validation, V2, dependency installation, calibration bridge, Global Value Router, or official-test/external outcome evaluation.

Suggested approval wording:

> 审批 U1.2/V0，进入 U1.3/V1 smoke implementation。

## Approval decision

The researcher approved the U1.2/V0 safety anchor and authorized only U1.3/V1 smoke
implementation. Formal V1 development cross-validation, V2, dependency installation,
calibration, routing, and official-test/external outcome evaluation remained unauthorized.
