# PATTERN-Surv-HN 阶段报告：U2/V1 development cross-validation 与复杂度门

**日期：** 2026-08-14  
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**冻结结论：** `V1_DOES_NOT_EARN_COMPLEXITY`

## 本阶段做了什么

本阶段第一次在患者级开发数据上正式训练和验证 V1。严格只使用 HANCOCK official-training 中 610 名合格患者、173 个事件；official-test 和所有外部结局继续封存。

实验采用 5 folds × 5 seeds 的外层交叉验证，并完全重用 V0 已冻结的患者划分和各折临床锚点选择。每个外层训练折内部重新拟合临床、blood、ICD、TMA 预处理；内层 3-fold 只选择 residual penalty 和训练 checkpoint，不扩张或搜索 3,225 参数的 V1 架构。

## 得到了什么结果

生成了 3,050 行完整 OOF 预测。每个 seed 都覆盖 610 名唯一患者，没有非有限预测。V0 重建误差小于 `4.44e-16`，无可用附加模态时：

```text
delta_eta = 0
eta_fused = eta_clinical
```

两项误差都严格为 `0.0`，说明 exact fallback 契约在正式训练与交叉验证中仍然成立。

## 冻结复杂度门结论

```text
coverage gate                      PASS
structural gate                    PASS
safety gate                        FAIL
incremental-value gate             FAIL
final decision                     V1_DOES_NOT_EARN_COMPLEXITY
```

关键数值如下：

| 指标 | 冻结要求 | 观察值 | 结果 |
|---|---:|---:|---|
| V0/V1 coverage | 100%/100% | 100%/100% | PASS |
| fallback residual/fused error | 0/0 | 0/0 | PASS |
| 参数量 | ≤50,000 | 3,225 | PASS |
| 平均 Brier24 差值 V1−V0 | ≤+0.005 | +0.001801 | PASS |
| 最坏受支持 pattern Brier regret | ≤+0.020 | +0.023779 | **FAIL** |
| 平均 CITL 恶化 | ≤0.10 | +0.003924 | PASS |
| 平均 calibration-slope error 恶化 | ≤0.15 | +0.213075 | **FAIL** |
| 平均 Uno C24 增益 | ≥+0.01 且至少 3/5 seeds 改善 | +0.002116；3/5 | **FAIL** effect size |

因此 V1 没有在预先冻结的规则下证明其额外复杂度值得保留，当前 backbone 必须回到 **V0 clinical anchor**。

## 最重要的科学信息

25 个外层折中有 10 个选择了 optimization step 0。由于 residual head 是零初始化，step 0 等价于完全不使用 V1 residual，保留 V0 输出。这说明内层验证经常认为“不融合”比学习后的融合修正更安全。

最坏受支持 pattern 是 seed 29 的 `101`（43 人、13 events）：V1 相比 V0 的 Brier24 恶化 `+0.023779`，Uno C 下降约 `-0.1032`。这直接展示了 pattern-dependent negative transfer：即使网络有 exact fallback 结构，只要模态存在并进入融合，仍可能在特定采集模式下伤害预测。

这与我们的核心故事“模型应知道何时融合、何时回退”相关，但当前结果只证明了问题确实存在，并没有证明 Global Value Router 已经解决问题。U2 没有训练 router，也不能把这一步写成 router 的有效性证据。

## 对论文投稿意味着什么

这是一个有效的负结果和停止边界，不是代码失败：

- V1 的结构与训练流程正常；
- 全覆盖与 exact fallback 成立；
- 但融合残差没有获得稳定、足够大的总体增益；
- 支持 pattern 中出现了超阈值负迁移；
- calibration slope 安全性也未通过。

因此暂时不能宣称“V1 多模态融合优于 V0”或“该网络提升跨数据集迁移性与泛化性”。如果继续投稿路线，需要先重新收敛中心方法和 claim，而不能直接向 V2 或 router 扩张。

## 可重复性与测试

```text
正式 OOF SHA256
81F2369B5469167139D2A1B85F549E89690449A40A0A8878864F098B920134CE

正式 aggregate audit SHA256
4066C2F0CD3D58061EDA15CD5CDBF7902F0BCA5E4B906D494F82596D4CFFFD1A
```

独立完整复跑得到完全相同的 OOF SHA256；只归一化不同的输出路径后，完整 aggregate payload 也完全一致。

```text
PATTERN U1–U2 定向测试              40 passed
相关 Phase 2/3                     23 passed
Phase 6 注册文件完整性 guard          1 passed
全仓库                              140 passed / 1 个既有 Phase 6 状态失败
pip check                           PASS
定向 Ruff                           PASS
```

## 下一阶段准备做什么

本阶段不自动进入下一实验。需要您审批后选择：

1. **接受 V0 retention**，重新设计并收敛论文故事；
2. **预注册诊断/消融阶段**，仅使用 development 数据分析 V1 为什么在 pattern `101` 和 calibration 上失败；
3. **停止当前 backbone 路线**。

在新审批前，继续禁止 V2、calibration bridge、Global Value Router、router labels/actions、official-test 和外部结局评估，也禁止结果后修改复杂度门阈值。
