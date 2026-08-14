# PATTERN-Surv-HN 阶段报告：U1.3/V1 结构性 smoke implementation

**日期：** 2026-08-14  
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`

## 本阶段做了什么

本阶段把 V1 的最小网络结构落实为可执行代码：

```text
V0 临床风险 eta_c
    +
Deep Sets 附加模态残差 delta_eta
    =
候选融合风险 eta_f
```

网络包含 blood、ICD、TMA 三个模态专属 adapter，以及 modality identity、status 和 quality
编码。共享 `phi` 编码每个 token，masked mean 对任意模态子集进行置换不变聚合，共享 `rho`
输出残差风险。

最关键的安全约束已经写入网络：当没有 active modality token 时，不经过带 bias 的 `rho`
产生残差，而是强制 `delta_eta = 0`，因此输出与 V0 临床风险完全一致。

由于当前项目环境没有 PyTorch，而且本阶段审批不包含依赖安装，所以使用 NumPy 固定权重和
7条合成数据进行结构测试。没有使用任何患者数据或结局，也没有训练预测模型。

## 结果

- 结构检查：10/10 PASS；
- 模态顺序置换误差：0；
- 无附加模态时残差误差：0；
- clinical-only fallback 误差：0；
- Cox score 平移不变性误差：`2.22e-16`；
- 参数量：3,225；
- 两次重跑的聚合审计 SHA256 完全一致。

测试结果：

```text
V1 smoke tests                 9 passed
U1.1 + U1.2 + U1.3           27 passed
相关 Phase 2/3                23 passed
全仓库                       127 passed, 1个既有冻结 Phase 6 failure
Ruff                           PASS
```

## 论文角度如何理解

这一阶段证明了 V1 的网络接口和核心数学约束可实现：它能够接受任意附加模态子集，不依赖输入
顺序，并且在无附加证据时严格回退 V0。

但 V1 目前只产生“候选融合风险”，还不能决定什么时候 FUSE、什么时候 FALLBACK，也不能产生
`RANK_ONLY` 或 `ABSTAIN`。未来 Global Value Router 才负责这些动作，而 router 的监督必须来自
正式 cross-fitting 后的增量价值证据。

因此，本阶段不能声称预测性能、多模态增益、泛化性或临床效用得到提高。

## 下一阶段准备做什么

建议下一步为 **U1.4/V1 trainable implementation + synthetic optimization smoke**：

1. 审批并冻结项目内 PyTorch 依赖；
2. 将固定权重 NumPy 参考结构转为可训练实现；
3. 实现 Cox loss 反向传播和最小优化循环；
4. 继续验证 permutation invariance 和 exact fallback；
5. 只使用合成数据检查 loss 能否下降；
6. 完成后再次停下审批。

这一步仍不进入正式 V1 development CV。正式 HANCOCK 交叉验证属于 U2，必须另行审批。
