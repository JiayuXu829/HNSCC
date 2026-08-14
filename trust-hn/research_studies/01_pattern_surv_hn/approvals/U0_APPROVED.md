# Step U0 研究者审批记录

**审批状态：** `APPROVED`  
**审批日期：** 2026-08-13  
**审批人：** Researcher（通过当前对话明确指令“审批进入U1.1”）

## 获批决定

- [x] **U0-D01：** 主要临床场景为根治性手术及标准病理评估完成后、辅助治疗决策尚未作为预测变量时的术后预后预测。
- [x] **U0-D02：** 主要安全锚点为 extended postoperative clinical-pathological elastic-net Cox。
- [x] **U0-D03：** pathology 属于 clinical anchor，不重复作为附加模态。
- [x] **U0-D04：** 主要变化模态及 mask 顺序为 `blood / ICD / TMA`。
- [x] **U0-D05：** exact natural unseen-pattern 的最低支持条件为 `n >= 20` 且总事件数 `>= 5`；U0 审计中满足条件的模式为 `011 / 101 / 110`。
- [x] **U0-D06：** 主要术后 OS 分析排除 postoperative duration `<= 0` 的 1 条记录，并报告聚合排除数；另做 diagnosis-origin OS 敏感性分析。
- [x] **U0-D07：** 先验证 V1 Clinical Residual Deep Sets，再决定是否进入 V2 Set Transformer；复杂度必须由预设指标证明。
- [x] **U0-D08：** 默认 global cross-fitted calibration；pattern intercept 支持门槛 `n=50/events=15`，slope 门槛 `n=100/events=25`；支持不足时回到 global calibration 或 `RANK_ONLY`。
- [x] **U0-D09：** ICD 条件性纳入，明确 vocabulary/timing provenance 局限，并设置排除 ICD 的 strict fold-pure sensitivity analysis。

## 本次授权范围

仅授权执行 **U1.1：postoperative HANCOCK data contract**：

1. 在 PATTERN-Surv-HN 独立命名空间实现 anchor、blood、ICD、TMA 数据块；
2. 实现模态 availability、内部缺失、质量/status、术后 endpoint 和 split role；
3. 提供 fold-bound preprocessing 接口和 raw blood reconstruction；
4. 只产生可追踪的 aggregate-only audit/report；
5. 不修改 frozen Phase 3–6 adapter/loader；
6. 不训练 V0/V1/V2，不安装 PyTorch，不运行 router/calibrator，不用 official test 做选择。

## 审批原文

> 审批进入U1.1
