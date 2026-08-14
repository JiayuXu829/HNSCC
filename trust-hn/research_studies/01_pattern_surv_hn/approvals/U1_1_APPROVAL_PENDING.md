# Step U1.1 研究者审批请求

**状态：** `PENDING`
**请求日期：** 2026-08-13
**阶段：** postoperative HANCOCK data contract

## 请求审批内容

请审阅并确认：

- [ ] 术后 endpoint 为 `days_to_last_information - days_to_first_treatment`；
- [ ] clinical-pathological anchor 的 9 个变量及 pathology 属于 anchor；
- [ ] blood / ICD / TMA 是三个独立附加模态；
- [ ] acquired、usable、内部缺失和 provenance status 的定义；
- [ ] raw blood acquired=693、usable=683，以及 U0 pattern 修正；
- [ ] official test 152 条 outcome 全部封存，聚合事件字段不报告；
- [ ] 插补、缩放与类别映射只能在训练折内拟合；
- [ ] ICD 条件性纳入并保留 ICD-excluded sensitivity；
- [ ] U1.1 未训练模型、未生成患者级预测、未修改 frozen Phase 3–6。

## 支持材料

```text
core_backbone/U1_1_data_contract/README.md
core_backbone/U1_1_data_contract/aggregate_contract_audit.json
audits/U1_1_postoperative_hancock_contract_audit.md
reports/2026-08-13_step_U1_1_postoperative_hancock_data_contract.md
```

## 审批后授权范围

若明确批准 U1.1，只授权进入 U1.2/V0：实现并验证 extended postoperative clinical-pathological elastic-net Cox safety anchor。

不自动授权 V1、V2、新依赖安装、calibration bridge、Global Value Router，或使用 official test/外部 outcome 做模型、阈值与 claim 选择。

建议审批措辞：

> 审批 U1.1，进入 U1.2/V0。
