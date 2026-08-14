# U1.1 Postoperative HANCOCK Data-Contract Audit

**日期：** 2026-08-13
**阶段：** U1.1
**分析标签：** `post_lock_exploratory`
**输出级别：** aggregate-only

## 1. 审计范围

本审计检查术后 endpoint、official-test sealing、anchor/blood/ICD/TMA 边界、acquired/usable/内部缺失的分离、fold-bound preprocessing、禁止 predictor、患者标识泄露，以及 frozen Phase 3–6 完整性。本阶段没有训练或选择模型。

## 2. 人群、split 与 endpoint

| 项目 | n | 已暴露事件数 | 备注 |
|---|---:|---:|---|
| HANCOCK 全部记录 | 763 | — | contract 总数 |
| deterministic train | 489 | 135 | 其中 488 条满足主要术后资格 |
| calibration | 122 | 38 | 全部满足主要术后资格 |
| sealed official test | 152 | 不报告 | duration/event 未派生、未输出 |
| 主要术后分析合格 | 762 | — | development 排除 1 条 duration `<= 0` |
| development 合格 | 610 | 173 | train + calibration |

`sealed_test` 的 `events_exposed` 明确写为 `null`，而不是容易被误解为零事件。

## 3. Predictor boundary

Anchor 固定为 age、sex、smoking、site、grading、p16、resection、pT、pN。Outcome、recurrence/progression/metastasis、adjuvant treatment 和 post-prediction timing 字段未进入 predictor blocks；`primarily_metastasis` 未进入主要 anchor；grading 原始语义值已规范化为 `HPV_OSCC`。

## 4. 模态 availability 与质量

| 模态 | acquired | usable | absent | acquired unusable | usable partial | complete/conditional |
|---|---:|---:|---:|---:|---:|---:|
| Blood | 693 | 683 | 70 | 10 | 79 | 604 complete |
| ICD | 712 | 712 | 51 | 0 | 0 | 712 conditional provenance |
| TMA | 736 | 736 | 27 | 0 | 97 | 639 complete |

Blood 预设特征矩阵有 684 行、284 个 missing cells、604 个 complete rows、1 个 all-null selected-feature row。TMA 有 130 个 missing cells。ICD 数值矩阵无 NaN，但 timing/vocabulary provenance 未解决。

## 5. Acquisition-pattern 修正

基于 raw acquisition 的全部 763 人 pattern：

```text
001=7, 010=4, 011=59, 100=1, 101=43, 110=22, 111=627
```

U0 使用 published blood CSV 时为 `011=60, 111=626`。差异来自 published CSV 曾将一名 raw-blood acquired 患者作为全队列离群值整行删除；U1.1 恢复其 acquisition 状态，并把异常处理推迟到训练折内。这是数据定义纠偏，不是结果驱动选择。

基于 usable 状态的 pattern：

```text
001=8, 010=5, 011=67, 100=1, 101=42, 110=21, 111=619
```

该差异表明 availability mask 不能替代 quality/usable mask。

## 6. Fold purity 与 official-test sealing

测试确认训练统计量只来自声明的 training IDs；calibration ID 混入 fit IDs 会抛出 `DataContractError`；held-out 极端值不会改变训练中位数；raw blood NaN 未在 contract build 阶段全队列填补。

Official test 共 152 条，结构模式均为 `111`。U1.1 不派生其 duration/event，聚合事件字段为 `null`，不用于 preprocessing、模型、阈值、校准或 claim 选择。它未来只能用于 post-lock complete-pattern replication，不能验证自然缺失模式泛化。

## 7. 代码质量与治理验证

| 检查 | 结果 |
|---|---|
| Ruff：新 namespace 与 U1.1 tests | PASS |
| U1.1 targeted tests | PASS，12/12 |
| Phase 2/3 related regression tests | PASS，14/14 |
| full repository suite（补充） | 112 PASS / 1 legacy state-dependent FAIL |
| aggregate JSON parse | PASS |
| identifier-key scan | PASS，0 个 `patient_id/native_id/subject_id` key |
| `pyproject.toml` / `environment.yml` | PASS，无改动 |
| frozen Phase 3–6 manifest | PASS，377/377 逐项哈希一致 |
| manifest SHA256 | `01FD176E338BFF4B09EB23E4DFA5CA455D77091161AE89AD3A9356D60BBB2D10` |

全套测试唯一失败为 `test_outcomes_refuse_access_before_consumption`。该 legacy test 预期 Phase 6 尚未消费授权，但当前 frozen 历史状态已记录 Phase 6 outcome 已消费；失败与 U1.1 新 namespace 无关。U1.1 未修改 frozen test/loader/config，相关 Phase 2/3 回归和全部 U1.1 测试均通过。

```text
analysis_label: post_lock_exploratory
phase6_outcomes_already_seen: true
phase6_files_modified: false
external_outcomes_used_for_tuning: false
patient_level_outputs_git_ignored: true
tracked_outputs_aggregate_only: true
```

## 8. 局限与 Go/no-go

局限：ICD 原始文本缺失；official test 只有 `111`；没有新的 outcome-unseen confirmatory cohort；U1.1 不产生性能、泛化性或临床价值结论；router 的 cross-fitted incremental value labels 尚未生成。

**Technical GO（研究者审批后）：** U1.2/V0 extended clinical-pathological elastic-net Cox anchor。
**NO-GO：** V1、V2、calibration bridge、value router、外部结局选择与任何效果 claim。
