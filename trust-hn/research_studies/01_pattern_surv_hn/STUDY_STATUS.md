# PATTERN-Surv-HN Study Status

**最后更新：** 2026-08-14
**当前步骤：** U2/V1 development cross-validation 与 V0-vs-V1 complexity gate
**状态：** `U2_V1_DEVELOPMENT_CV_COMPLETE_AWAITING_APPROVAL`
**分析标签：** `post_lock_exploratory`

## 本阶段已完成

- [x] 记录研究者对 U1.4 的审批，并仅授权 HANCOCK official-training 内部的 U2/V1 development CV。
- [x] 在查看 U2 结果前冻结 development-CV 方案与 V0-vs-V1 complexity gate。
- [x] 仅使用 610 名 HANCOCK official-training 合格患者（173 events）。
- [x] 重用 V0 的 5 folds × 5 seeds 外层划分和各折已选择的临床锚点候选。
- [x] 所有临床、blood、ICD、TMA 预处理均在训练折内重新拟合。
- [x] 内层 3-fold 仅选择 residual penalty 与 optimization checkpoint，不搜索或扩张架构。
- [x] 生成 3,050 行完整 OOF 预测；每个 seed 均为 610 个唯一患者且无非有限预测。
- [x] 验证 V0 OOF 重建误差不超过 `4.44e-16`，空模态 residual/fused fallback 误差均为 `0.0`。
- [x] 完成冻结的 coverage、structural、safety、incremental-value complexity gate。
- [x] 独立完整复跑的 OOF SHA256 完全一致；归一化输出路径后的 aggregate audit payload 完全一致。
- [x] PATTERN U1–U2 tests 40 PASS；相关 Phase 2/3 tests 23 PASS；Phase 6 注册文件 guard PASS。
- [x] full suite 140 PASS / 1 个既有 Phase 6 consumed-state failure；`pip check` 与定向 Ruff PASS。
- [x] official-test 与所有外部结局继续封存；未训练 V2、calibration bridge 或 Global Value Router。

## 冻结门结果

```text
coverage gate                                      PASS
structural fallback/parameter gate                 PASS
safety gate                                        FAIL
incremental-value gate                             FAIL
final decision                                     V1_DOES_NOT_EARN_COMPLEXITY
```

关键数值：

```text
V0 / V1 coverage                                   100% / 100%
parameter count                                    3,225
fallback residual / fused max error                0.0 / 0.0
mean delta IPCW Brier24 (V1 - V0)                  +0.001801  [PASS <= +0.005]
worst supported-pattern Brier regret                +0.023779  [FAIL > +0.020]
mean absolute CITL deterioration                   +0.003924  [PASS <= 0.10]
mean calibration-slope error deterioration         +0.213075  [FAIL > 0.15]
mean delta Uno C24 (V1 - V0)                       +0.002116  [FAIL < +0.01]
Brier-improving seeds                              2/5
Uno-C-improving seeds                              3/5
```

## 当前科学结论

V1 保持了全覆盖、严格 clinical fallback 和总体 Brier 非劣性，但没有在冻结阈值下获得足够、稳定的增量价值，并在受支持 acquisition pattern 的最坏 Brier regret 与 calibration slope 安全项上失败。因此当前核心 backbone 必须保留 **V0 clinical anchor**；不得结果后修改阈值，也不得把 V1 描述为优于 V0。

频繁选择 optimization step 0（25 个外层折中的 10 个）说明，内层 CV 经常更偏好与 V0 完全等价的零残差行为，而不是训练后的模态融合残差。这是本阶段最重要的负结果/停止边界之一。

## 当前审批门

等待研究者审阅：

```text
approvals/U2_V1_DEVELOPMENT_CV_APPROVAL_PENDING.md
audits/U2_V1_development_cv_audit.md
reports/2026-08-14_step_U2_V1_development_cv.md
docs/work_stage_reports/zh-CN/2026-08-14_pattern_surv_hn_step_U2_V1_development_cv_report.md
```

研究者下一步需要在以下方向中作出明确决定：

1. 接受 V0 retention，并据此重新收敛论文方法与 claim；
2. 另行预注册一个仅限 development 数据的诊断/消融阶段，用于解释 V1 失败边界；
3. 停止当前 backbone 路线。

**NO-GO：** 在新的明确审批前，不得进入 V2、calibration bridge、Global Value Router、router label/action、official-test 或外部结局评估，也不得修改已冻结 gate 阈值。
