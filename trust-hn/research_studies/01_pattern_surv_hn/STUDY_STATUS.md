# PATTERN-Surv-HN Study Status

**最后更新：** 2026-08-13
**当前步骤：** U1.1 — postoperative HANCOCK data contract
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`
**分析标签：** `post_lock_exploratory`

## U0 审批

- [x] 研究者于 2026-08-13 批准 U0-D01–U0-D09。
- [x] 审批记录：`approvals/U0_APPROVED.md`。
- [x] 原授权只覆盖 U1.1 数据契约，不包含模型训练。

## U1.1 完成情况

- [x] 建立独立 postoperative HANCOCK patient x modality contract。
- [x] 分离 anchor、blood、ICD、TMA 数据块。
- [x] 区分 acquisition、usable、within-modality missingness 与 provenance status。
- [x] 封存 official-test duration/event，聚合事件字段为 `null`。
- [x] raw blood 从 0–14 天时间窗重建，不做全队列插补或离群值删除。
- [x] 提供 numeric 与 mixed-type fold-bound preprocessing。
- [x] Ruff 通过；U1.1 tests 12/12；相关回归 tests 14/14。
- [x] 全仓补充测试 112 PASS / 1 个 frozen Phase 6 状态依赖旧测试 FAIL，已在报告解释且未修改冻结资产。
- [x] aggregate-only audit 不含患者标识 key。
- [x] frozen Phase 3–6 清单 377/377 哈希一致。
- [x] 完成 U1.1 README、审计和阶段报告。

## 当前审批门

等待研究者审批 `approvals/U1_1_APPROVAL_PENDING.md`。

**GO：** 仅允许审阅和审批 U1.1。
**NO-GO：** 审批前启动 U1.2/V0，或启动 V1/V2、新依赖安装、calibration bridge、value router、外部结局选择。

若 U1.1 获批，下一步是 U1.2/V0 extended postoperative clinical-pathological elastic-net Cox safety anchor。该步骤完成后仍需单独审批，不能自动进入 V1。
