# TRUST-HN WP3 终点与变量写作词典

**版本日期：** 2026-08-12  
**状态：** WP3 冻结写作接口；不是正文。  
**权威接口：** `configs/phase6_evaluation.json`、`docs/audits/phase2/endpoint_audit.md`、`src/trust_hn/evaluation/endpoints.py`、`src/trust_hn/metrics/survival.py`。  
**适用范围：** Abstract、正文、图表、图注、Supplement 和报告清单。

## 1. 主要终点

| 项目 | 统一英文写法 | 统一中文写法 | 冻结定义与写作规则 |
|---|---|---|---|
| 主要终点 | **24-month overall survival (24-month OS)** | **24 个月总体生存（24-month OS）** | 预测时间窗固定为 `730.5` 天。首次出现使用全称与缩写；后文可写 `24-month OS`。不可写成 2-year mortality classification，因为主要分析保留时间-事件和删失信息。 |
| 时间-事件终点 | overall survival time to event | 总体生存时间-事件终点 | `duration_days >= 0`；`event=1` 为全因死亡，`event=0` 为删失。GSE41613 的全部来源 `Dead` 类别均按全因死亡处理。 |
| 时间窗风险 | predicted 24-month mortality risk | 预测 24 个月死亡风险 | 数值范围 0–1。正文使用“risk”，不是“probability of benefit”或“clinical decision”。 |
| 事件截止规则 | death on or before 730.5 days | 在 730.5 天当日或之前死亡 | 记为时间窗内事件。观察超过 730.5 天者在该时间窗内为无事件；较早失访者的二元状态未知。 |

## 2. 各队列时间起点

| 队列 | 统一英文描述 | 统一中文描述 | 禁止替代说法 |
|---|---|---|---|
| RADCURE | OS was measured from the first radiotherapy fraction; duration was `Last FU − RT Start`. | OS 自首次放疗分次起算，时长为 `Last FU − RT Start`。 | 不得使用来源字段 `Length FU` 的诊断起点作为主要分析终点。 |
| HANCOCK | OS was measured from diagnosis to last information or death, in days, following the source data dictionary. | OS 自诊断起至末次信息或死亡，单位为天，遵循来源数据字典。 | 不得无依据统一改写为手术起点。 |
| TCGA-HNSC | For deceased cases, duration used nonnegative `days_to_death`; for living cases, the maximum available follow-up day. | 死亡病例使用非负 `days_to_death`；存活病例使用最大可用随访天数。 | 不得称为治疗起点。 |
| GSE65858 | OS follow-up from the frozen GEO adapter was expressed in days. | 使用冻结 GEO 适配器中的 OS 随访时间并统一为天。 | 不得补写未冻结的临床起点。 |
| GSE41613 | Source follow-up in months was converted as `months × 30.4375 days`. | 来源随访时间以月计，按 `月数 × 30.4375 天` 换算。 | 不得称为一般 HNSCC 队列；不得改用口腔癌特异死亡。 |
| `inner_hancock` | Inherited simulation endpoint semantics; excluded from current manuscript reporting. | 沿用模拟终点语义；当前稿件不报告。 | 不得作为独立队列描述终点或验证。 |

**跨队列写作原则：** 研究共享同一 24 个月预测时间窗和结局类型，但时间起点遵循各数据来源的冻结定义。不得写成“所有队列具有完全相同的 index date”。

## 3. 删失与 24 个月状态

统一三类时间窗状态：

1. `event_by_horizon`：在 730.5 天当日或之前死亡；二元标签为 1。
2. `event_free_at_horizon`：观察达到或超过 730.5 天；二元标签为 0，即使更晚发生死亡。
3. `censored_before_horizon`：在 730.5 天前无死亡而失访；二元状态未知。

写作规则：

- 早期删失者**不得**被编码或描述为 24 个月存活者。
- 在 IPCW 计算中，时间窗前删失者获得零评价权重，而不是被排成“无事件”标签。
- 报告队列流时，应分别列出时间窗内死亡、观察至时间窗且无事件、时间窗前删失；不要将后二者合并为“survivors”。
- `endpoint_status` 的标准类别为 `usable`、`early_censored`、`sealed`、`unresolved` 和 `not_applicable`；正文不要把 sealed/unresolved 当作 missing outcome 的同义词。

## 4. IPCW 定义与统一描述

### 4.1 标准英文句式

> Predictive accuracy at 24 months was assessed using the inverse-probability-of-censoring-weighted (IPCW) Brier score, with censoring weights estimated from the corresponding development training outcomes. Individuals censored on or before the horizon received zero evaluation weight and were not labelled as survivors.

### 4.2 标准中文释义

> 采用逆删失概率加权（IPCW）Brier 评分评价 24 个月绝对风险预测；删失分布由相应数据生态的开发训练结局估计。时间窗当日或之前删失者的评价权重为零，不被标记为存活者。

### 4.3 实现边界

- 主要预测性能指标写为 **IPCW Brier score**；值越低越好。
- 训练队列的反向事件指示用于估计删失 Kaplan–Meier 分布。
- 事件发生于时间窗内时使用事件时间左极限的删失生存概率；观察超过时间窗时使用时间窗处的删失生存概率。
- 冻结实现将删失生存概率下限设为 `0.05`，避免极端权重；该值进入 Methods/Supplement，不在 Abstract 中展开。
- IPCW Brier 的实现分母为被评价预测集合的患者数；因此 B7 选择性指标必须与 coverage 绑定，不能与全队列指标直接作未经配对的优效比较。

## 5. 统计指标词典

| 代码/概念 | 首选英文 | 首选中文 | 方向与边界 |
|---|---|---|---|
| `ipcw_brier` | 24-month IPCW Brier score | 24 个月 IPCW Brier 评分 | 越低越好；主要预测性能焦点。 |
| `harrell_c` | Harrell’s C-index | Harrell C 指数 | 越高越好；可能受删失分布影响。 |
| `uno_c` | Uno’s C-index | Uno C 指数 | 越高越好；使用 IPCW。 |
| `auc_horizon` | 24-month time-dependent AUC | 24 个月时间依赖 AUC | 越高越好；不得替代绝对风险校准。 |
| `calibration_in_the_large` | calibration-in-the-large | 总体校准偏差（calibration-in-the-large） | 首次中英并列；理想值为 0。实现为固定预测 logit 作为 offset 的 IPCW 加权校准截距。 |
| `calibration_slope` | calibration slope | 校准斜率 | 理想值为 1；常数/退化预测时可不可估。 |
| `mean_predicted_risk` | mean predicted 24-month risk | 平均预测 24 个月风险 | 与观察结局和总体校准共同解释。 |
| `coverage` | non-abstained coverage | 非弃权覆盖率 | B7 发出风险预测的比例，即 `AUGMENT + FALLBACK`；不是数据完整率。 |
| action rate | AUGMENT/FALLBACK/ABSTAIN rate | AUGMENT/FALLBACK/ABSTAIN 动作比例 | 三者为算法动作，合计 100%；不是临床决策率。 |
| DCA | retrospective exploratory decision-curve analysis | 回顾性探索性决策曲线分析 | 仅描述曲线行为；不能建立临床效用、治疗获益或患者获益。 |

## 6. Bootstrap 与不确定性

### Phase 6 预设评价

- 标准英文：**2,000 patient-level paired bootstrap replicates**。
- 标准中文：**2,000 次患者级配对 bootstrap 重采样**。
- 同一队列、同一比较中的模型使用相同的重采样患者索引。
- 95% CI 使用 bootstrap 分布的百分位区间。
- B7 与 B6/B2 的配对比较先固定 B7 的相同非弃权患者子集，再在该共同子集中进行患者级配对重采样。

### Phase 7 附加比较

- 标准英文：**1,000 patient-level paired bootstrap replicates in a Phase 7 post hoc exploratory analysis**。
- 必须在同一句或同一实质性陈述中保留 **post hoc exploratory**。
- 不得把 Phase 7 的 1,000 次 bootstrap 写成 Phase 6 预设的不确定性分析。

### 轻量 bootstrap ensemble

- B7 可靠性组件中的 `20-model bootstrap ensemble` 用于模型不确定性估计。
- 它与生成结果 95% CI 的患者级 paired bootstrap 不是同一程序，写作时不得混称。

## 7. 变量组与预测时点原则

| 变量组 | 统一写法 | 写作边界 |
|---|---|---|
| Clinical | clinical variables / structured clinical variables | 只纳入冻结、预测时点可用的变量；结局变量不得作为预测变量。 |
| Pathological | pathological variables | HANCOCK 中与 clinical 并列或写为 clinical/pathological；不得扩展为全切片病理影像。 |
| Blood | baseline blood measurements | 仅 HANCOCK 冻结基线血液变量。 |
| TMA | TMA cell-density features | 为预提取细胞密度特征；不得写为端到端 WSI/TMA 图像模型。 |
| Radiomics | pretreatment CT radiomics | RADCURE 使用数值 PyRadiomics 表征；不可据预测结果推断特异性生物学。 |
| Transcriptomics | RNA-seq transcriptomics / microarray transcriptomics | 必须区分 TCGA-HNSC RNA-seq 与 GEO 微阵列；跨平台迁移需明确说明。 |
| Missingness | modality missingness / explicit missingness indicators | 缺失本身可作为审计信号，但不得假定其因果意义。 |

## 8. 缺失、不可用和不可估的写法

- **not available / 不可用：** 来源未提供或当前病例无该模态。
- **not evaluated / 未评价：** 研究计划未在该队列/分区评价该方法或指标。
- **not applicable / 不适用：** 概念上不适用于该行，例如非 B7 模型的 abstention coverage。
- **not estimable / 不可估：** 数据结构导致统计量无法稳定计算，例如常数预测的校准斜率。
- **governance-blocked / 因治理条件阻断：** 授权阶段因数据结构/冻结条件未运行；不得简写成失败结果。

表格中不得使用空白单元格模糊以上类别；使用 `NA` 时必须在表注中映射到明确类别。

## 9. 本 WP 的权威来源

- `docs/audits/phase2/endpoint_audit.md`
- `docs/work_stage_reports/en/2026-08-07_phase2_completion_report.md`
- `configs/phase3_baselines.json`
- `configs/phase4_trust_hn.json`
- `configs/phase6_evaluation.json`
- `configs/phase7_exploratory_benchmarks.json`
- `src/trust_hn/evaluation/endpoints.py`
- `src/trust_hn/metrics/survival.py`
- `src/trust_hn/evaluation/phase6.py`
