# PATTERN-Surv-HN U1.2/V0 工作阶段报告

**日期：** 2026-08-14  
**阶段结论：** V0 clinical-pathological safety anchor 已完成，等待审批。

## 这个阶段干了什么

我们把论文中的“安全回退”落实成了一个可执行的模型，而不是停留在概念上。V0 是术后 extended clinical-pathological elastic-net Cox，输入 9 个标准临床/病理变量，为所有合格患者输出：

- continuous survival ranking score；
- 730.5-day death risk；
- 730.5-day survival probability。

在 HANCOCK official-training 合格人群 n=610/events=173 内，完成 5 seeds × 5 outer folds × 3 inner folds 的 nested cross-fitting。所有预处理、类别映射、超参数选择和 baseline survival 均限制在对应 training fold。产生的 3050 行 repeated OOF 预测只写入 git-ignored 目录。

## 得到了什么

V0 的 5-seed 聚合结果：

```text
IPCW Brier24          0.1247 ± 0.0015
Harrell C             0.6230 ± 0.0144
Uno C24               0.6442 ± 0.0138
AUC24                 0.6620 ± 0.0144
Calibration-in-large -0.0037 ± 0.0149
Calibration slope     0.9367 ± 0.0792
```

这说明 V0 在内部 OOF 中具有中等排序能力和总体可接受的 24-month calibration，可以作为后续 `FALLBACK` 的安全参考。但这不是融合模型结果，不能声称 missing-modality handling、跨数据集迁移或 router 有效。

## 为什么论文需要这一步

后续网络的 residual prediction 将写成：

```text
eta_fused = eta_clinical + delta_eta
```

因此 `eta_clinical` 必须先被严格定义和验证。V0 也将用于：

1. 衡量每名患者融合相对临床锚点的增量价值；
2. 定义 `FALLBACK` 动作的实际输出；
3. 计算 full-coverage 和 worst-pattern safety regret；
4. 判断深度 backbone 是否带来值得复杂化的增益。

## 验证情况

- U1.1 + U1.2 tests：18 PASS；
- related Phase 2/3 tests：23 PASS；
- full suite：118 PASS / 1 known frozen Phase 6 legacy state failure；
- 两次正式运行的 OOF SHA256 完全一致；
- official-test outcome、external outcome、router 和 V1/V2 均未使用；
- dependency files 与 frozen Phase 3–6 key paths 未修改。

## 下个阶段准备干什么

若本阶段获批，建议进入 **U1.3/V1 smoke implementation**，只先完成最小 Clinical-Residual Deep Sets Cox 的结构验证：

1. blood/ICD/TMA modality-specific adapters；
2. modality identity、acquisition/usable/status/quality encoding；
3. permutation-invariant Deep Sets pooling；
4. residual Cox score `eta_clinical + delta_eta`；
5. 无附加 token 时与 V0 score/survival 数值一致；
6. 任意 modality subset 和 permutation invariance 单元测试；
7. 暂不训练 router，不做 calibration bridge，不进入 V2。

U1.2/V0 现在停止，等待研究者审批。
