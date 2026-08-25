# PATTERN-Surv-HN Study Status

**最后更新：** 2026-08-19
**当前步骤：** U2/V1R 结果已批准，进入论文映射与确认协议冻结准备
**状态：** `U2_V1R_RESULT_APPROVED_PROVISIONAL_BACKBONE`
**分析标签：** `post_hoc_exploratory_rescue`

## 研究者批准结论

- V1R 被正式认定为成功的 provisional development backbone；
- 论文主线以 V1R 的积极贡献为主：完整覆盖、严格临床回退、判别能力提升、总体 Brier 改善，以及最差支持模式风险处于安全阈值内；
- V0 继续作为 V1R 内部的 clinical fallback anchor，而不再是唯一的 development backbone；
- V1R 的 development gate 结论为 `V1R_EARNS_COMPLEXITY`；
- 原始 V1 的审计记录继续保留，但不作为论文主结果叙事中心。

## V1R 主要积极结果

```text
coverage V0 / V1R                         1.0 / 1.0       PASS
fallback residual/fused error             0.0 / 0.0       PASS
parameter count                           3,225           PASS
mean delta IPCW Brier24                  -0.000407        improvement
worst supported-pattern Brier regret     +0.009848        within safety gate
mean absolute CITL deterioration         +0.008843        within safety gate
mean slope-error deterioration           +0.085784        within safety gate
mean delta Uno C24                       +0.021303        improvement
Uno-C improving seeds                     5 / 5           stable direction
mean delta AUC24                         +0.020488        improvement
```

## 对应论文位置

V1R 对应论文的 **Aim 1：任意模态组合下的删失感知安全融合**，并构成四组件框架中的第二个核心组件：

```text
clinical anchor
→ V1R residual set survival backbone
→ calibration bridge
→ value/reliability router
```

主文应放入：

1. Methods：`Residual set survival backbone`；
2. Results：`Residual fusion improves discrimination while preserving full coverage and safety`；
3. Figure 1：clinical anchor、residual fusion 与 exact fallback 架构；
4. 主结果表：V0 与 V1R 的 Brier、Uno C、AUC、校准和 worst-pattern regret；
5. Discussion：残差收缩使附加模态产生稳定、受控的增量信息。

完整调参网格、逐 seed 结果、scale 分布、复现哈希和原始 V1 历史记录放入 Supplementary Methods/Tables。

## 当前允许的下一步

```text
U2_V1R_CONFIRMATION_PROTOCOL_FREEZE_ONLY
```

可以进行论文内容映射，并制定、冻结 V1R confirmation protocol。未经新审批，仍不得：

- 打开 HANCOCK official-test 结局；
- 使用外部结局进行调参或确认；
- 训练 calibration bridge；
- 创建最终 FUSE/FALLBACK/RANK_ONLY/ABSTAIN actions；
- 训练最终 Global Value Router；
- 声称已经完成外部确认或证明临床效用。
