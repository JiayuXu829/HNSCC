# PATTERN-Surv-HN Study Status

**最后更新：** 2026-08-14
**当前步骤：** U1.4/V1 trainable implementation — deterministic synthetic optimization smoke
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`
**分析标签：** `post_lock_exploratory`

## 已完成

- [x] U1.3/V1 structural smoke 已于 2026-08-14 获研究者审批。
- [x] 在项目 `.venv` 安装 `PyTorch 2.12.1+cpu`，并在 U1.4 独立 requirements 中冻结。
- [x] 保持 `pyproject.toml` 和 Phase 6 注册文件不变。
- [x] 将 U1.3 的 3,225 参数结构转换为可训练 PyTorch 网络。
- [x] 实现可微 Breslow Cox loss、Adam 优化与 gradient clipping。
- [x] 使用 96 条确定性合成数据完成 250 步优化 smoke。
- [x] 初始 loss 3.607239，最终 loss 0.605562，相对下降 83.21%。
- [x] 验证有限非零梯度、参数更新、训练前后 permutation invariance。
- [x] 验证训练后无 active token 时 `delta_eta = 0` 且严格回退 V0 clinical score。
- [x] 两次完整运行 aggregate SHA256 完全一致。
- [x] U1.4 tests 7 PASS；U1 全部 34 PASS；related Phase 2/3 tests 23 PASS。
- [x] full suite 134 PASS / 1 known frozen Phase 6 state FAIL。
- [x] 无患者数据、真实 outcome、formal CV、official-test、external、router 或 calibrator。

## U1.4 结果

```text
framework                         PyTorch 2.12.1+cpu
synthetic rows                    96
optimization                     Adam, 250 steps
parameter count                  3,225
checks                           12/12 PASS
initial/final Cox loss            3.607239 / 0.605562
relative loss reduction          83.2126%
post-train permutation error     3.55e-15
fallback residual error          0.0
fallback fused error             0.0
aggregate SHA256                 12C3E6F85AFDFA99FC9898AC843EAD439B9A5D2AF4F4085D9260C5D168807C34
```

这些结果只支持 V1 可训练、可优化、置换不变且保持 exact fallback，不支持患者预测性能、融合增益、路由价值、跨数据集泛化或临床效用 claim。

## 当前审批门

等待研究者审阅：

```text
approvals/U1_4_V1_TRAINABLE_SMOKE_APPROVAL_PENDING.md
audits/U1_4_V1_trainable_smoke_audit.md
reports/2026-08-14_step_U1_4_V1_trainable_smoke.md
```

**GO（若明确批准）：** 进入 U2/V1 development cross-validation 与 V0-vs-V1 complexity gate；official-test 和外部结局继续封存。

**NO-GO：** 未审批前训练 HANCOCK 患者级 V1、运行正式 development CV、访问 official-test/外部 outcome，或实现 V2、calibration bridge、Global Value Router。
