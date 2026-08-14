# PATTERN-Surv-HN Study Status

**最后更新：** 2026-08-14
**当前步骤：** U1.3/V1 smoke implementation — Clinical-Residual Deep Sets structural contract
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`
**分析标签：** `post_lock_exploratory`

## 已完成

- [x] U1.2/V0 已于 2026-08-14 获研究者审批。
- [x] 冻结 V1 structural smoke specification：blood 32、ICD 80、TMA 8。
- [x] 实现 modality-specific adapters、identity/status/quality encoding。
- [x] 实现 shared phi、masked-mean pooling 与 shared rho residual head。
- [x] 验证任意模态子集输入与模态顺序 permutation invariance。
- [x] 验证无 active token 时 `delta_eta = 0`，输出严格等于 V0 clinical score。
- [x] 验证 Breslow Cox partial likelihood 有限且 score-shift invariant。
- [x] 合成 smoke 10/10 checks PASS；两次运行 aggregate SHA256 完全一致。
- [x] V1 tests 9 PASS；U1 tests 27 PASS；related Phase 2/3 tests 23 PASS。
- [x] full suite 127 PASS / 1 known frozen Phase 6 legacy FAIL。
- [x] 无 patient data、outcome、official-test、external、router、calibrator 或 dependency installation。

## 结构性 smoke 结果

```text
reference framework              NumPy, fixed deterministic weights
synthetic rows                   7
parameter count                  3,225
structural checks                10/10 PASS
permutation max abs error        0.0
fallback residual max error      0.0
fallback fused max error         0.0
Cox shift-invariance error       2.22e-16
```

这些结果只支持 V1 网络结构、置换不变性和 exact fallback 可实现，不支持预测性能、融合增益、跨数据集泛化、路由价值或临床效用 claim。

## 当前审批门

等待研究者审阅：

```text
approvals/U1_3_V1_SMOKE_APPROVAL_PENDING.md
audits/U1_3_V1_smoke_audit.md
reports/2026-08-14_step_U1_3_V1_smoke.md
```

**GO（若明确批准）：** 进入 U1.4/V1 trainable implementation + synthetic optimization smoke，并单独批准、冻结项目环境 PyTorch 依赖。

**NO-GO：** 未审批前安装依赖、训练患者级 V1、运行正式 development CV、V2、calibration bridge、Global Value Router、official-test/外部 outcome 评估。
