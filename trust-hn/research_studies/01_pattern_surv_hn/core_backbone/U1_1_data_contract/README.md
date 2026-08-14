# U1.1 — Postoperative HANCOCK Data Contract

**状态：** 实现完成，等待研究者审批
**分析标签：** `post_lock_exploratory`
**模型训练：** 未进行

## 1. 阶段目的

U1.1 把 PATTERN-Surv-HN 的术后预测时间、临床安全锚点、三个附加模态及缺失/质量状态落实为独立、可测试的数据入口。本阶段不拟合 V0/V1/V2，不运行 calibration bridge 或 Global Value Router。

核心代码与测试：

```text
src/trust_hn/pattern_surv_hn/hancock_contract.py
tests/test_pattern_surv_hn_contract.py
```

## 2. 术后终点与封存规则

```text
duration_days = days_to_last_information - days_to_first_treatment
event = 1[survival_status == deceased]
```

- official training 中 postoperative duration `<= 0` 的 1 条记录标记为主要分析不合格；
- official test 的 duration/event 在 U1.1 中不派生、不输出；
- `targets.csv` 仅用于核对主患者集合覆盖，sealed-test endpoint 逻辑不读取结局值。

## 3. 数据块边界

Clinical-pathological anchor 固定为：

```text
age_at_initial_diagnosis
sex
smoking_status
primary_tumor_site
grading
hpv_association_p16
resection_status
pT_stage
pN_stage
```

Pathology 属于术后标准照护锚点，不作为额外模态 token。`primarily_metastasis` 暂不进入主要锚点。Outcome、复发/进展/转移、辅助治疗及预测时间之后的变量均禁止作为 predictor。

附加模态顺序固定为 `blood / ICD / TMA`，三个矩阵独立保存，不在数据入口强制拼接。

## 4. Availability 与质量语义

每个模态区分：

- `acquired`：预测时间窗内是否获得该模态；
- `usable`：是否至少有一个有效数值；
- `within-modality missingness`：已获得模态内部的特征缺失；
- `status`：`absent / acquired_unusable / usable_partial / usable_complete / conditional_provenance`。

同时提供基于采集状态的 `acquisition_pattern` 与基于有效值的 `usable_pattern`。因此，后续 router 可以分别利用模态存在性、质量和支持度，而不是把所有 available modality 当成同等可靠。

## 5. 各模态入口

### Blood

主要入口来自原始 `blood_data.json`：固定 16 个 hematology features，只使用 first treatment 前 0–14 天记录，不做全队列插补、缩放或整队列离群值删除，内部 NaN 保留至训练折内预处理。

聚合结果：acquired=693，usable=683，absent=70，acquired_unusable=10，usable_complete=604，usable_partial=79。

### ICD

本地只有预提取的 40 维 `icd_codes.csv`。原始文本缺失，且词表由 available corpus 上的 `CountVectorizer(min_df=3)` 预先产生，因此所有可用 ICD 行标记为 `conditional_provenance`。后续必须报告 ICD-excluded strict fold-pure sensitivity。

### TMA

无 TMA 行表示 modality absence；有行但含 NaN 表示 within-modality missingness。插补、缩放和 missing indicators 必须在训练折内拟合。

## 6. Fold-bound preprocessing

- `FoldBoundBlockPreprocessor`：blood、ICD、TMA 数值块；
- `FoldBoundMixedPreprocessor`：数值与分类混合的 clinical-pathological anchor；
- 中位数、标准化参数、分类水平和 one-hot mapping 只在显式 fit IDs 上拟合；
- `allowed_fit_ids` 可拒绝 calibration/test ID 混入；
- 输出显式 missing indicators，并对 transform 阶段的新类别使用 unknown level。

## 7. 禁止事项与下一审批门

U1.1 禁止使用 official-test outcome、全队列拟合预处理、写入患者级 tracked artifact、修改 frozen Phase 3–6，以及训练任何模型或 router。

当前数据入口已具备进入 U1.2/V0 的技术条件，但只有研究者审批 U1.1 后才允许继续。U1.1 本身不提供任何模型性能或论文效果结论。
