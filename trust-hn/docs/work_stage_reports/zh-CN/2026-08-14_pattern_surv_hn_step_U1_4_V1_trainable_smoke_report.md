# PATTERN-Surv-HN 阶段报告：U1.4/V1 可训练实现与合成优化 smoke

**日期：** 2026-08-14
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`

## 本阶段做了什么

本阶段把 U1.3 的固定权重 NumPy 结构参考，转换为真正可训练的 PyTorch 网络，但没有改变
已冻结的 V1 结构：

```text
V0 临床风险 eta_clinical
        +
可用 blood / ICD / TMA token 集合产生的残差 delta_eta
        =
候选融合风险 eta_fused
```

网络仍然包含模态专属 adapter、模态 identity、采集/status、quality 编码、共享 `phi`、
masked-mean pooling 和共享 `rho`。总参数量为 3,225。

项目 `.venv` 已安装并冻结 `PyTorch 2.12.1+cpu`。依赖写入 U1.4 独立 requirements 文件，
没有修改属于 Phase 6 完整性注册对象的 `pyproject.toml`，也没有安装 CUDA 包。

## 关键验证结果

使用 96 条确定性合成生存数据、Adam 250 步完成优化 smoke：

```text
初始 Cox loss                 3.607239
最终 Cox loss                 0.605562
相对下降                      83.2126%
第一次梯度全局范数             0.0410992
参数 L2 变化                  13.0111
训练后 permutation 最大误差   3.55e-15
空 token 残差误差              0.0
clinical fallback 误差         0.0
检查                          12/12 PASS
```

两次完整运行的聚合审计 SHA256 完全相同：

```text
12C3E6F85AFDFA99FC9898AC843EAD439B9A5D2AF4F4085D9260C5D168807C34
```

## 这一步对论文意味着什么

现在可以确认：V1 不仅结构上可实现，而且能够正常反向传播、更新参数和优化 Cox 目标；在训练
之后，模态顺序置换不变性和 exact clinical fallback 仍然成立。

但这仍然不是患者数据上的性能实验。合成 loss 下降只能证明“网络可训练”，不能证明 HNSCC
预测更准、融合有增益、跨数据集泛化更好，也不能证明 router 有价值。

V1 当前输出的是“候选融合风险”。它仍不负责决定 `FUSE`、`FALLBACK`、`RANK_ONLY` 或
`ABSTAIN`。这些动作需要未来正式 cross-fitting 得到的增量价值证据，再由 Global Value Router
学习。

## 治理与测试

```text
U1.4 定向测试                    7 passed
U1.1–U1.4 全部定向测试          34 passed
相关 Phase 2/3                  23 passed
全仓库                         134 passed, 1 个既有 Phase 6 状态失败
U1.4 Ruff                        PASS
Phase 6 注册文件完整性            PASS
pip check                        PASS
```

本阶段没有使用 HANCOCK 患者、真实结局、official-test 或外部队列；没有正式 development CV；
没有保存模型 checkpoint 或患者级输出；没有实现 V2、calibration 或 router。

## 下一阶段准备做什么

建议下一阶段为 **U2/V1 development cross-validation + V0-vs-V1 complexity gate**：

1. 只在 HANCOCK development 数据内部运行正式 cross-fitting；
2. 所有预处理、V1 训练和调参必须严格位于训练折内部；
3. 生成 development OOF 预测；
4. 与 V0 临床锚点比较，判断 V1 是否值得增加复杂度；
5. official-test 和外部结局继续封存；
6. 完成后再次停下审批。

当前必须停在 U1.4 审批门，未获明确批准前不得开始患者级 V1 训练。
