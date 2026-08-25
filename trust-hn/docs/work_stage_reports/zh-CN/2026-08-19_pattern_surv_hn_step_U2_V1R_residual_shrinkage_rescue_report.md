# PATTERN-Surv-HN 阶段报告：U2/V1R 残差收缩救援

**日期：** 2026-08-19  
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**分析标签：** `post_hoc_exploratory_rescue`

## 结论

这次 V1 救援成功了，但成功的是单独命名的 **V1R**，不是把原始 V1 的失败改写为成功。
原始结论继续保留：`V1_DOES_NOT_EARN_COMPLEXITY`。

V1R 保持原 3,225 参数 Deep Sets 网络，只在每个内层交叉验证中选择残差缩放系数：

```text
V1R = V0 + lambda × V1 residual
lambda ∈ {0.1, 0.2, 0.3, 0.4, 0.5, 1.0}
```

## 主要结果

| 指标 | V1R 结果 | 原始数值门槛 | 判断 |
|---|---:|---:|---|
| 平均 Brier24 差值 | -0.000407 | <= +0.005 | PASS |
| 最差 supported-pattern regret | +0.009848 | <= +0.020 | PASS |
| CITL 绝对恶化 | +0.008843 | <= 0.10 | PASS |
| calibration-slope error 恶化 | +0.085784 | <= 0.15 | PASS |
| 平均 Uno C24 增益 | +0.021303 | >= +0.01 | PASS |
| Uno C 改善 seeds | 5/5 | 至少 3/5 | PASS |

因此，即使不用放宽后的探索门槛，而是把原 U2 的数值阈值原样应用到 V1R，V1R 也通过了。

## 为什么有效

原始 V1 的主要问题是残差修正过强。V1R 让内层 CV 决定该相信多少多模态残差。25 个外层
fold 中有 16 个选择了小于 1 的 scale；step 0 从原 V1 的 10/25 降到 V1R 的 1/25。
这表明额外模态并非完全无信号，而是需要收缩后才能稳定使用。

## 仍需谨慎

- 本方案是在看到原 V1 失败后设计的，属于结果知情的 post-hoc rescue；
- seed 29 的 Brier 仍恶化 +0.003496，校准斜率也不稳定；
- pattern 101 的最差 Brier regret 已降到 +0.009848，但部分 seed 的 Uno C 仍下降；
- 当前证据只能支持“provisional development backbone”，不能支持确认性优越、外部泛化或临床效用。

## 可重复性

正式和独立复跑的患者级 OOF SHA256 完全一致：

```text
E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0
```

新增 scale 功能后，原始 V1 也完整复跑并保持原 SHA256 不变，证明没有篡改旧结果。

## 下一步

建议审批后把 V1R 冻结为临时 development backbone，并单独制定确认协议。未经新审批，仍不得：

- 打开 HANCOCK official-test 结局；
- 使用任何外部结局；
- 训练 calibration bridge 或最终 Global Value Router；
- 宣称 V1R 已经外部验证或具有临床效用。
