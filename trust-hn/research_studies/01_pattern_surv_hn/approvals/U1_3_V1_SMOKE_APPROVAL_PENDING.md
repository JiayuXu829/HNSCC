# U1.3/V1 Smoke Approval Request

**status:** `PENDING_RESEARCHER_APPROVAL`
**completed_on:** 2026-08-14
**analysis_label:** `post_lock_exploratory`

## Approval object

Dependency-free structural smoke implementation of the minimum
`Clinical_Residual_Deep_Sets_Cox` backbone.

## Checklist

- [ ] Confirm this stage used deterministic synthetic arrays only and did not use patient outcomes.
- [ ] Confirm modality-specific adapters accept blood, ICD, and TMA fold-preprocessed blocks.
- [ ] Confirm modality identity, acquisition/status, and quality encodings are operational.
- [ ] Confirm masked-mean Deep Sets pooling is invariant to modality input order.
- [ ] Confirm arbitrary modality subsets are accepted.
- [ ] Confirm no active modality tokens produce exactly `delta_eta = 0`.
- [ ] Confirm fused score then equals the V0 clinical score exactly.
- [ ] Confirm the Cox partial-likelihood implementation is finite and score-shift invariant.
- [ ] Confirm no PyTorch/dependency installation, model fitting, formal CV, router, calibrator, or outcome evaluation occurred.
- [ ] Confirm smoke results support structural feasibility only, not prognostic performance.

## Aggregate smoke summary

```text
structural checks passed:          10 / 10
permutation max absolute error:    0.0
fallback residual max error:       0.0
fallback fused-score max error:    0.0
Cox shift-invariance error:        2.22e-16
reference parameter count:         3,225
aggregate audit rerun SHA256:      84F875B385933A12CFFE10A0786373648BB6B1D7CF15E0E8C4476C89B5F46731
```

## Supporting artifacts

```text
core_backbone/U1_3_V1_smoke/frozen_v1_smoke_spec.yaml
core_backbone/U1_3_V1_smoke/aggregate_v1_smoke_audit.json
audits/U1_3_V1_smoke_audit.md
reports/2026-08-14_step_U1_3_V1_smoke.md
docs/work_stage_reports/zh-CN/2026-08-14_pattern_surv_hn_step_U1_3_V1_smoke_report.md
```

## Authorization requested next

If approved, the next proposed step is **U1.4/V1 trainable implementation plus synthetic
optimization smoke**. Because PyTorch is absent, this requires separate approval to add a frozen
project-local PyTorch dependency. It still would not authorize formal V1 development CV or any
official-test/external outcome evaluation.

Suggested approval wording:

> 审批 U1.3/V1 smoke，进入 U1.4/V1 trainable implementation，并允许在项目环境中安装和冻结 PyTorch 依赖；暂不进入正式 development CV。
