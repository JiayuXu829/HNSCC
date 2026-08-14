# Approval records

本目录保存 PATTERN-Surv-HN 每个研究阶段的审批记录和当前审批门。

- `U0_APPROVED.md`：方案与数据契约审计已批准。
- `U1_1_APPROVED.md`：术后 HANCOCK 数据契约已批准。
- `U1_2_V0_APPROVED.md`：V0 临床安全锚点已批准。
- `U1_3_V1_SMOKE_APPROVED.md`：V1 结构性 smoke 已批准，并授权 U1.4 与项目内 PyTorch 依赖。
- `U1_4_V1_TRAINABLE_SMOKE_APPROVED.md`：V1 可训练合成优化 smoke 已批准，并授权 U2 development CV 与冻结 complexity gate。
- `U2_V1_DEVELOPMENT_CV_APPROVAL_PENDING.md`：U2 已完成；V1 未通过冻结复杂度门，等待研究者决定保留 V0、授权单独预注册的诊断/消融，或停止当前路线。

审批文件只授权其中明确列出的下一步。当前审批门不自动授权 V2、校准、Global Value Router、official-test 或外部结局评估。
