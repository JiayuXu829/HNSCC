# U1.4/V1 Trainable Smoke Approval Record

**status:** `APPROVED`
**approved_on:** 2026-08-14
**approved_by:** Researcher (chat approval)
**approval_text:** `审批 U1.4/V1 trainable smoke，进入 U2/V1 development cross-validation 与 V0-vs-V1 complexity gate；继续封存 official-test 和外部结局。`
**completed_on:** 2026-08-14
**analysis_label:** `post_lock_exploratory`

## Approval object

Trainable PyTorch implementation and deterministic synthetic optimization smoke of the minimum
`Clinical_Residual_Deep_Sets_Cox` V1 backbone.

## Checklist

- [x] Confirm PyTorch 2.12.1+cpu was installed only in the project `.venv` and frozen in the U1.4 directory.
- [x] Confirm `pyproject.toml` and all registered Phase 6 decision files remain unchanged.
- [x] Confirm U1.4 inherits the frozen U1.3 dimensions and contains 3,225 trainable parameters.
- [x] Confirm gradients are finite/nonzero and parameters update under Adam optimization.
- [x] Confirm synthetic Cox loss decreased from 3.60724 to 0.605562 (83.21% relative reduction).
- [x] Confirm modality-order permutation invariance holds before and after optimization.
- [x] Confirm no active modality token still yields exactly `delta_eta = 0` after optimization.
- [x] Confirm the fused score still equals the clinical score exactly under empty-set fallback.
- [x] Confirm two formal smoke runs produced the same aggregate audit SHA256.
- [x] Confirm no HANCOCK patient training, formal development CV, official-test/external evaluation, router, or calibrator occurred.
- [x] Confirm these results establish trainability only, not prognostic performance or fusion benefit.

## Aggregate smoke summary

```text
checks passed:                         12 / 12
initial synthetic Cox loss:            3.607239
final synthetic Cox loss:              0.605562
relative loss reduction:               83.2126%
first gradient global norm:            0.0410992
parameter L2 change:                   13.0111
post-training permutation max error:   3.55e-15
fallback residual max error:           0.0
fallback fused-score max error:        0.0
parameter count:                       3,225
aggregate audit rerun SHA256:          12C3E6F85AFDFA99FC9898AC843EAD439B9A5D2AF4F4085D9260C5D168807C34
```

## Supporting artifacts

```text
core_backbone/U1_4_V1_trainable_smoke/frozen_v1_trainable_smoke_spec.yaml
core_backbone/U1_4_V1_trainable_smoke/frozen_pytorch_dependency.yaml
core_backbone/U1_4_V1_trainable_smoke/requirements-pytorch-cpu.txt
core_backbone/U1_4_V1_trainable_smoke/aggregate_v1_trainable_smoke_audit.json
audits/U1_4_V1_trainable_smoke_audit.md
reports/2026-08-14_step_U1_4_V1_trainable_smoke.md
docs/work_stage_reports/zh-CN/2026-08-14_pattern_surv_hn_step_U1_4_V1_trainable_smoke_report.md
```

## Authorized next stage

If approved, the proposed next stage is **U2/V1 formal development cross-validation and the
V0-vs-V1 complexity gate**, while continuing to seal official-test and external outcomes. That
stage would train on HANCOCK development patients and therefore requires explicit approval.

Suggested approval wording:

> 审批 U1.4/V1 trainable smoke，进入 U2/V1 development cross-validation 与 V0-vs-V1 complexity gate；继续封存 official-test 和外部结局。

## Approval decision

The researcher approved U1.4 and authorized U2/V1 development-only repeated cross-validation and the prespecified V0-vs-V1 complexity gate. Official-test outcomes, external outcomes, V2, calibration bridge, and the Global Value Router remain unauthorized and sealed.
