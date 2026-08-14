# PATTERN-Surv-HN Step U1.1 阶段报告

**完成日期：** 2026-08-13
**阶段：** U1.1 — postoperative HANCOCK data contract
**状态：** 实现与验证完成，等待研究者审批
**分析标签：** `post_lock_exploratory`

## 1. 从论文投稿角度，本阶段做了什么

U1.1 不是训练网络，也不是证明 PATTERN-Surv-HN 优于 baseline。本阶段完成的是论文实验成立之前的测量与数据治理层：把术后预测时间、临床安全锚点、三个附加模态及其缺失/质量状态落实成可执行、可测试且不泄漏的数据契约。

它直接服务核心故事：

> 不是让模型在缺失模态时仍然强行融合，而是让模型知道什么时候该融合、什么时候该回退。

只有先区分“没有采集”“采集但不可用”“部分缺失”和“完整可用”，后续 router 才可能科学地决定 `FUSE / FALLBACK / RANK_ONLY / ABSTAIN`。U1.1 建立了这些输入状态，但尚未训练 router，也没有产生四类动作。

## 2. 已完成实现

新增独立命名空间：

```text
src/trust_hn/pattern_surv_hn/__init__.py
src/trust_hn/pattern_surv_hn/hancock_contract.py
tests/test_pattern_surv_hn_contract.py
```

没有改写 frozen HANCOCK adapter 或 Phase 3 loader。

### 2.1 Endpoint 与 split

```text
duration = days_to_last_information - days_to_first_treatment
event = survival_status == deceased
```

Train=489，calibration=122，official test=152。Development 暴露事件=173；1 条 development 记录因 duration `<= 0` 排除，主要 development 合格 n=610。Official test 的 duration/event 均未派生或输出。

### 2.2 Clinical safety anchor

固定 9 个变量：age、sex、smoking、site、grading、p16、resection、pT、pN。Pathology 正确归入安全 anchor，而不是额外模态；辅助治疗、outcome 与 post-prediction variables 被禁止进入 predictor blocks。

### 2.3 三个独立附加模态

`blood / ICD / TMA` 分开保存，每个模态具有 acquired、usable、internal missingness 和 provenance/quality status，不在入口处强制融合。

### 2.4 Raw blood 与 fold-bound preprocessing

Blood 从 `blood_data.json` 重建 first-treatment 前 0–14 天的 16 个预设特征，不进行全队列插补、缩放或整队列异常值删除。结果为 acquired=693、usable=683、absent=70、acquired_unusable=10、usable_complete=604、usable_partial=79。

实现数值模态和 mixed anchor 的 fold-bound preprocessing，并用 `allowed_fit_ids` 防止 calibration/test IDs 进入拟合。

## 3. 关键纠偏

U0 按 published blood CSV 统计为 `011=60, 111=626`；U1.1 按原始 acquisition 修正为：

```text
001=7, 010=4, 011=59, 100=1, 101=43, 110=22, 111=627
```

原因是 published blood CSV 曾整行删除一名 raw-blood acquired 患者。新 contract 恢复其 acquisition 身份，并把异常处理推迟到训练折内。这是数据定义纠偏，不是效果驱动选择。

Usable pattern 为：

```text
001=8, 010=5, 011=67, 100=1, 101=42, 110=21, 111=619
```

它进一步支持后续方法必须同时建模模态存在性和模态是否真正可用/可靠。

## 4. 测试与治理结果

| 项目 | 结果 |
|---|---|
| Ruff | PASS |
| U1.1 targeted tests | 12/12 PASS |
| Phase 2/3 regression tests | 14/14 PASS |
| official-test sealing | PASS，聚合事件字段为 `null` |
| prohibited predictor boundary | PASS |
| fold-bound fit-ID guard | PASS |
| aggregate-only JSON | PASS，无患者标识 key |
| frozen Phase 3–6 integrity | PASS，377/377，manifest hash 不变 |
| dependency files | PASS，无改动 |
| full repository suite（补充） | 112 PASS / 1 legacy FAIL；失败为已完成 Phase 6 工作区中“仍应拒绝未消费 outcome”旧状态测试，与 U1.1 代码路径无关 |

### 4.1 全测试套件说明

补充运行全仓库测试时得到 112 passed、1 failed。唯一失败是 frozen `tests/test_phase6_statistics.py::test_outcomes_refuse_access_before_consumption`：该测试假定 Phase 6 authorization 尚未消费，但当前历史工作区的 `configs/analysis_freeze.yaml` 已合法记录 `phase6_outcomes_seen=true` 与 `test_unseal.consumed=true`，因此实际 outcome loader 继续到 ID 对齐并返回 `ValueError`，而不是旧测试预期的 `PermissionError`。U1.1 未修改该测试、Phase 6 loader 或 freeze 文件；377 项冻结清单仍逐项一致。为遵守冻结约束，本阶段不修改旧 Phase 6 测试。

## 5. 本阶段没有做什么

没有训练 V0/V1/V2，没有安装新依赖，没有拟合 calibration bridge 或 Global Value Router，没有产生四类路由动作，没有使用 official test 或外部 outcome 做选择，也没有生成患者级预测。因此现在不能声称预测性能、迁移性或泛化性得到提升。

## 6. 局限

1. ICD 只有预提取特征，原始文本和 prediction-time vocabulary provenance 未解决；
2. official test 只有 complete pattern `111`，不能验证自然缺失模式泛化；
3. 已有外部队列均 outcome-seen，confirmatory claim 仍需未来 outcome-unseen cohort；
4. router 的 cross-fitted incremental value labels 尚未产生；
5. 当前只有数据层技术可行性，没有模型比较结果。

## 7. Go/no-go 与下一阶段

**GO（仅在本报告获批后）：** 进入 U1.2/V0，实施 extended postoperative clinical-pathological elastic-net Cox safety anchor。
**NO-GO：** 直接进入 V1/V2、calibration bridge、value router 或外部结局选择。

下一阶段计划：冻结 V0 特征和 elastic-net Cox 搜索空间；在 development population 内执行 nested cross-fitting；所有预处理和基线风险仅在对应训练折拟合；患者级 OOF 预测仅写入 git-ignored predictions 目录；tracked report 只保留聚合判别、24-month Brier、校准和 pattern 分层安全基线。U1.2/V0 结束后再次停止等待审批。

## 8. 审批请求

请确认 U1.1 的数据定义、raw blood 修正、official-test sealing 与 fold-bound preprocessing 是否正确。未获批准前不进入 U1.2/V0。
