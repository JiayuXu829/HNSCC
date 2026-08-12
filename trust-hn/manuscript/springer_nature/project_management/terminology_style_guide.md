# TRUST-HN WP3 中英术语与命名规范

**版本日期：** 2026-08-12  
**状态：** Abstract、正文、图表、图注和 Supplement 的统一写作接口；不是完整论文正文。  
**原则：** 方法代码用于可追溯，科学角色用于叙事；二者首次出现时绑定，之后不能互换或漂移。

## 1. 项目与疾病名称

| 情境 | 首选英文 | 首选中文 | 规则 |
|---|---|---|---|
| 框架 | TRUST-HN framework | TRUST-HN 框架 | TRUST-HN 指完整原则：clinical anchoring、conditional fusion、reliability assessment、fallback 和 abstention；不是 B6 或 B7 的单独别名。 |
| 组织学明确的总体人群 | head and neck squamous cell carcinoma (HNSCC) | 头颈部鳞状细胞癌（HNSCC） | 首次使用全称。 |
| 标题或跨队列范围需保守时 | head and neck cancer | 头颈癌 | 当前首选标题使用该范围；正文描述具体队列时优先 HNSCC。 |
| 受限敏感性队列 | HPV-negative oral squamous cell carcinoma (OSCC) | HPV 阴性口腔鳞状细胞癌（OSCC） | GSE41613 的每个实质性描述均需保留该限定。 |

## 2. 核心科学术语

| 首选英文 | 首选中文 | 定义/首次使用 | 禁止或慎用替代说法 |
|---|---|---|---|
| clinical anchor | 临床锚点 | B2 clinical elastic-net Cox；所有多模态增量价值的参照。 | 不写 gold standard、ground truth model、always-best model。 |
| additional modality | 附加模态 | 相对于临床锚点加入的影像组学、血液/TMA 或转录组信息。 | 不统一写 omics，因为 RADCURE/HANCOCK 并非都属组学。 |
| conditional incremental value | 条件性增量价值 | 附加模态相对于 B2 的收益依赖队列生态与转移条件。 | 不写 inherent superiority、intrinsic benefit。 |
| direct forced fusion | 直接强制融合 | B5 的 clinical-plus-modality direct concatenation。 | compulsory fusion 可用于解释，但全文首选 forced fusion；不得把 B6 简化为 B5。 |
| stacked residual fusion | 堆叠残差融合 | B6：交叉拟合 B2 锚点评分加训练来源模态表示的弹性网 Cox 生存学习器。 | 不写 fixed-offset Cox 或 modality residual only。 |
| reliability-aware gating | 可靠性感知门控 | B7 使用与结局无关的可靠性分量和冻结阈值分配动作。 | 不写 safety gate、clinical triage gate。 |
| reliability gate | 可靠性门控 | B7 的简写；首次出现应与 reliability-gated selective prediction 绑定。 | 不把 reliability score 与 gate action 混为同义词。 |
| selective prediction | 选择性预测 | B7 可对部分病例不发出预测。 | 不写 patient selection 或 treatment selection。 |
| non-abstained coverage | 非弃权覆盖率 | 获得 AUGMENT 或 FALLBACK 风险的比例。 | 不写 data coverage、modality coverage、usable-case rate。 |
| identical non-abstained subset | 相同非弃权患者子集 | B7 与 B6/B2 公平直接比较使用的共同病例集合。 | 不写 matched cohort，除非明确不是匹配设计。 |
| data ecosystem | 数据生态 | 队列、来源、预测时点、模态、平台、预处理和转移条件的组合。 | 不等同于单一 modality。 |
| failure boundary | 失败边界 | 模型增益、校准或门控不再成立的观察条件。 | 不写 safety boundary 或 causal boundary。 |
| calibration failure | 校准失败 | 结合 IPCW Brier、calibration-in-the-large、slope 和平均风险描述。 | 不仅凭 C-index/AUC 判断。 |
| auditability / auditable | 可审计性 / 可审计 | 显式呈现参照、覆盖率、动作、配对比较及反证。 | 不等同于 trustworthy、safe、explainable。 |

## 3. B7 动作词典

所有动作在英文稿中保持大写等宽或小型大写风格：`AUGMENT`、`FALLBACK`、`ABSTAIN`。

| 动作 | 统一中文 | 算法定义 | 写作边界 |
|---|---|---|---|
| `AUGMENT` | 增强 | 临床输入未触发弃权，附加模态可用且未超过模态不可靠性阈值；输出 B6 风险。 | 不是“建议使用多模态治疗决策”。 |
| `FALLBACK` | 回退 | 临床输入未触发弃权，但模态缺失或模态不可靠性超过阈值；输出 B2 临床锚点风险。 | 不是临床降级、治疗回退或安全处置。 |
| `ABSTAIN` | 弃权 | 临床不可靠性超过阈值；不发出最终风险。动作优先级高于 FALLBACK。 | 不是拒绝治疗、转诊或临床不确定性结论。 |

标准英文句：

> B7 assigned algorithmic `AUGMENT`, `FALLBACK`, or `ABSTAIN` actions; these actions were retrospective model outputs rather than clinical decisions.

## 4. 队列角色术语

| 队列 | 必须使用的英文角色 | 中文角色 | 不可使用 |
|---|---|---|---|
| RADCURE | prespecified locked retrospective test | 预设锁定回顾性测试 | prospective validation；不加限定的 external validation |
| HANCOCK | prespecified retrospective out-of-distribution (OOD) test | 预设回顾性分布外（OOD）测试 | independent institutional validation |
| TCGA-HNSC | transcriptomic development and calibration cohort; no independent Phase 6 test | 转录组开发与校准队列；无独立 Phase 6 测试 | TCGA external/locked validation |
| GSE65858 | prespecified retrospective cross-platform external test | 预设回顾性跨平台外部测试 | outcome-guided harmonized validation；universal transportability |
| GSE41613 | restricted retrospective HPV-negative OSCC sensitivity analysis | 受限回顾性 HPV 阴性 OSCC 敏感性分析 | validation cohort；general HNSCC external validation |
| `inner_hancock` | known-overlap workflow and bias simulation; not validation | 已知重叠的流程与偏倚模拟；不是验证 | independent/private/institutional/external validation；当前正文队列 |

**显示名固定：** 正文显示名使用 `RADCURE`、`HANCOCK`、`TCGA-HNSC`、`GSE65858`、`GSE41613`。除数据来源说明外，不在每次出现时添加 `GEO` 前缀。代码/文件名中的 `inner_hancock` 保持小写下划线；其说明性显示名只用于治理文档。

## 5. 分析性质和证据等级

| 英文 | 中文 | 使用要求 |
|---|---|---|
| prespecified retrospective evaluation | 预设回顾性评价 | Phase 6 总称，可细化为 locked/OOD/external/sensitivity。 |
| one-time outcome access | 一次性结局访问 | 强调冻结治理；不可转写为 prospective lock。 |
| development/calibration evidence only | 仅开发/校准证据 | Phase 3–5 的模型开发结果。 |
| post hoc exploratory | 事后探索性 | Phase 7 每个实质性描述必须同句或同段保留该词组。 |
| retrospective exploratory decision-curve analysis | 回顾性探索性决策曲线分析 | DCA 的固定限定。 |
| negative control | 负对照 | RADCURE 打乱/随机化影像组学或 N0；不能自动证明机制。 |
| sensitivity analysis | 敏感性分析 | GSE41613、80%/100% gate profiles 等必须说清对象。 |

## 6. 指标和统计术语

| 首选英文 | 首选中文 | 备注 |
|---|---|---|
| IPCW Brier score | IPCW Brier 评分 | 首次展开 inverse-probability-of-censoring weighting。 |
| Harrell’s C-index | Harrell C 指数 | 正文和图轴可写 Harrell C-index。 |
| Uno’s C-index | Uno C 指数 | 正文和图轴可写 Uno C-index。 |
| 24-month time-dependent AUC | 24 个月时间依赖 AUC | 不写 ROC-AUC 而省略时间窗。 |
| calibration-in-the-large | 总体校准偏差（calibration-in-the-large） | 首次中英并列；后续英文稿保留标准术语。 |
| calibration slope | 校准斜率 | 理想值 1。 |
| paired bootstrap 95% confidence interval | 配对 bootstrap 95% 置信区间 | 不用显著/不显著替代区间。 |
| net benefit | 净获益 | 仅用于 DCA 数学指标；不得扩展为患者/治疗获益。 |

## 7. 模型命名规则

1. 首次出现写“代码 + 科学名称”，例如：`B2 clinical elastic-net Cox anchor`。
2. 同一段后续可写 `B2` 或 `clinical anchor`，但不能改用未定义别名。
3. `TRUST-HN` 是框架；`B6` 是 TRUST-HN stacked residual fusion；`B7` 是 TRUST-HN reliability-gated selective prediction。
4. 不单独写“the TRUST-HN model”指代 B6 或 B7；需明确方法代码。
5. B0–B7、M0、N0 的完整方法清单进入 Supplement；正文只保留主叙事需要的 B2/B6/B7 及必要 B5。
6. C1–C4 的实质性陈述必须写为“Phase 7 post hoc exploratory comparator(s)”。

## 8. 高风险措辞：允许、需限定、禁止

### 允许

- cohort-dependent gains
- conditional incremental value
- failure boundaries
- favourable retrospective point estimate
- calibration failure
- made forced-fusion risk visible
- did not consistently outperform
- requires independent prospective evaluation

### 必须限定

- **validation**：只在精确队列角色中使用 retrospective locked/OOD/external evaluation/validation，且不能暗示前瞻性。
- **robust/robustness**：只可描述某个具体压力测试或结果，不能写 universal robustness。
- **benefit**：仅可写 metric-level net benefit（DCA）并立即限定为 exploratory；不得写 patient/treatment benefit。
- **improvement/superiority**：需要相同指标、相同患者集合和 95% CI；B7 必须同时报告 coverage。
- **independent**：GSE65858 可说明其为外部数据来源，但不得把 `inner_hancock` 或 GSE41613 写成独立验证。

### 禁止作为支持性结论

- prospective validation / prospectively validated
- universal robustness / universally generalizable
- clinically useful / clinical utility established
- deployment-ready / deployable threshold / safe threshold
- patient benefit / treatment benefit
- universal winner / best model across cohorts
- radiomics-specific biological signal
- one shared universal HNSCC model
- clinical decision for `AUGMENT`/`FALLBACK`/`ABSTAIN`

## 9. Phase 8 / `inner_hancock` 当前边界

- 当前 Abstract、Introduction、Results、Discussion、Methods、标题、主图表和主表均不出现 Phase 8 结果。
- WP3 仅保留一行治理词典，防止未来误用。
- 若以后另行批准进入 Supplement，只允许：**known-overlap workflow and bias simulation; not validation**。
- 不得通过同义替换绕过边界，例如 pseudo-private validation、internal validation、private cohort、institutional test。

## 10. 一致性检查清单

在每轮正文或图表提交前核对：

- [ ] 队列显示名与 `cohort_dictionary.csv` 完全一致。
- [ ] 首次出现的方法代码与 `method_dictionary.csv` 名称一致。
- [ ] B7 绝对指标伴随 non-abstained coverage。
- [ ] B7 直接比较注明 identical non-abstained subset 和 evaluated n。
- [ ] Phase 7 同段出现 post hoc exploratory。
- [ ] GSE41613 同段出现 HPV-negative OSCC sensitivity analysis。
- [ ] DCA 同段否定 established clinical utility/patient benefit。
- [ ] `inner_hancock` 未进入当前正文或主图表。
