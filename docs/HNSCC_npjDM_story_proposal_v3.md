# 面向 npj Digital Medicine 的 HNSCC 可信预后 AI 研究故事 v3

> 版本日期：2026-08-06  
> 前提：完全使用公开数据；不下载大规模原始 CT/WSI；模型轻量；主线从“单队列影像组学审计”升级为“多队列、跨模态的临床可靠性框架”。

## 1. 为什么第二版故事仍然偏小

第二版提出用 RADCURE 的真实影像组学特征、肿瘤体积和负对照特征，检验 CT 预后模型是否依赖捷径。这个问题本身正确，但若单独投稿，编辑可能将其理解为：

- 对一个既有公开数据集的二次分析；
- 对“影像组学是否只是肿瘤体积替代物”的复核；
- 一个单中心、单模态、缺乏独立机构验证的预后模型；
- 主要贡献是统计审计，而不是新的数字医疗系统。

这与 npj Digital Medicine 更常见的论文叙事存在差距。该刊关注具有临床应用指向、经过验证的 AI 和数字医疗方法，并通常不考虑单纯套用现成模型、纯观察性或小规模初步研究。因此，论文不能只回答“负对照能否预测”，而应回答一个更广泛、更贴近临床部署的问题：

> **当患者模态不完整、数据分布发生变化、附加模态可能携带捷径时，HNSCC 预后 AI 应如何判断自己是否可信，并决定使用附加模态、回退到临床模型还是拒绝自动预测？**

官方定位：[npj Digital Medicine aims and scope](https://www.nature.com/npjdigitalmed/aims)。

## 2. 升级后的论文定位

### 推荐标题

首选：

**Trustworthy prognostic artificial intelligence for head and neck squamous cell carcinoma under shortcut learning, missing modalities and distribution shift**

中文：

**面向捷径学习、模态缺失与分布偏移的头颈鳞癌可信预后人工智能**

方法名可暂定为：

**TRUST-HN：a resource-efficient reliability-gated prognostic framework for head and neck cancer**

备选标题：

1. **A resource-efficient and modality-agnostic reliability framework for prognostic AI in head and neck cancer**
2. **Knowing when not to predict: uncertainty-gated multimodal prognosis in head and neck squamous cell carcinoma**
3. **Beyond discrimination: shortcut-aware and selectively calibrated survival prediction in head and neck cancer**

### 一句话论文主张

> 预后 AI 的临床价值不只取决于平均判别能力，还取决于模型能否识别无效模态、检测分布偏移、保持绝对风险校准，并在不可靠病例中安全回退或拒绝预测。

### 论文类型

不是“新的 HNSCC 影像组学签名”，而是：

- 一项多队列、跨模态的数字医学方法研究；
- 一个可以包裹在不同轻量生存模型外的可靠性层；
- 一套从附加模态增量价值、捷径审计、OOD检测到临床回退的完整验证框架；
- 一个公开、可复现、低资源可部署的 HNSCC 风险分层原型。

## 3. Background：按论文 Introduction 的方式讲故事

### 3.1 临床背景

HNSCC 是一个高度异质的疾病集合。原发部位、HPV/p16 状态、吸烟、体能状态、T/N 分期和治疗方式均与结局相关。即使处于相同临床分期，患者的复发和生存仍可能明显不同。因此，治疗前风险分层可以支持：

- 临床试验分层和入组；
- 随访强度设计；
- 营养、康复及支持治疗资源配置；
- 在多学科讨论中识别需要进一步检查或人工复核的患者。

本研究不直接推荐某种治疗，也不声称模型可以替代肿瘤委员会；研究目标是提供经过校准的风险信息及其可信度。

### 3.2 技术背景

目前 HNSCC 预后研究不断加入 CT、病理、转录组和临床信息。多模态模型通常假设更多数据会产生更准确的预测，但公开研究已经提示：

- 临床特征在多个肿瘤生存任务中往往是最强的单一模态；
- 多模态融合不一定稳定超过临床模型；
- 复杂影像特征可能主要编码肿瘤体积、采集设备或处理流程；
- 内部测试中的高判别力不能保证新医院、新时间段或新患者亚组中的校准；
- 大多数模型被迫对每名患者给出风险，即使该患者明显偏离训练分布。

npj Digital Medicine 已发表研究显示，隐藏的数据采集偏倚可导致内部性能高估，并提出无需外部数据估计泛化能力的方法；该研究在 13 个数据集上发现捷径学习可能造成明显性能高估。这说明“检测模型何时不可信”本身就是该刊认可的重要数字医学问题，而不只是附属分析。

参考：[Shortcut learning in medical AI hinders generalization](https://www.nature.com/articles/s41746-024-01118-4)。

### 3.3 HNSCC 中尚未解决的问题

HNSCC 公开队列尤其适合研究这一问题，因为：

1. 不同队列来自放疗、手术和分子研究场景，分布差异显著；
2. HPV、原发部位和治疗方式造成明显的生物学与临床异质性；
3. 可用模态高度不完整——有的患者有 CT，有的有病理或转录组；
4. 影像组学中肿瘤体积是已知强预测因素，也是潜在捷径；
5. 当前研究主要比较 C-index/AUC，很少系统评价校准、风险覆盖、回退策略和临床净获益。

因此，真正未解决的临床 AI 问题并非“能否再提高 0.02 的 AUC”，而是：

> **附加模态什么时候提供了超越常规临床资料的可靠信息，什么时候应被模型忽略，以及系统如何向临床人员表达这种不确定性？**

## 4. Motivation：为什么这个研究值得做

### 4.1 从“模型中心”转向“临床决策中心”

传统开发流程是：收集尽可能多的模态—融合—输出风险。我们的研究流程是：

1. 先用临床常规信息建立最低可用的风险锚点；
2. 再判断 CT、病理、血液或分子模态是否带来患者级增量信息；
3. 检测该患者是否偏离训练分布；
4. 估计风险不确定性；
5. 在附加模态不可靠时回退到临床模型，在整体输入不可靠时拒绝自动预测。

这更接近真实数字医疗系统，因为现实世界不会保证所有患者都具有完整、同质、高质量的多模态数据。

### 4.2 从“平均性能”转向“安全失败”

即使两个模型平均 AUC 相同，其中一个能在高风险失败前发出警告，也更适合临床部署。本研究把以下指标提升为主要结果：

- 绝对风险校准；
- 分布偏移下的最差亚组表现；
- 固定自动覆盖率下的预测误差；
- 回退/拒绝策略带来的净获益；
- 附加模态相对临床模型的患者级增量价值。

### 4.3 从“大模型竞赛”转向“资源公平”

如果可靠性提升依赖数十亿参数模型和数百 GB 数据，其可复现性和普及性有限。本研究刻意使用预提取特征、Cox、梯度提升、小型 MLP 和轻量 OOD 检测器，检验：

> 在不增加大型模型和私有数据的前提下，是否可以通过更合理的建模与验证机制获得更可信的数字医学系统？

这构成论文的第二层社会和方法学意义：可信 AI 不应只属于拥有大型私有队列和高算力的中心。

## 5. 研究目标与假设

### Primary objective

开发并验证一个**临床锚定、捷径感知、偏移检测和不确定性门控**的轻量 HNSCC 预后框架，在输入模态不完整或发生分布偏移时，能够选择：

- 使用临床 + 附加模态风险；
- 回退至临床锚定风险；
- 拒绝自动预测并提示人工复核。

### Secondary objectives

1. 定量评估影像、病理/血液和转录组信息相对临床基线的增量价值；
2. 检验负对照特征、模态随机置换和缺失模态是否暴露捷径学习；
3. 比较强制预测与不确定性门控预测在校准、最差亚组误差和临床净获益方面的差异；
4. 验证同一可靠性原则能否跨放疗、手术和分子队列复现。

### 预设假设

- H1：常规多模态模型在分布内数据上的判别力可能较高，但在负对照、缺失模态和 OOD 测试中出现明显校准下降。
- H2：以临床模型为锚点、只学习附加模态残余价值，可减少模型对单一强捷径的依赖。
- H3：联合使用 OOD 分数、预测区间宽度和捷径敏感度的可靠性门控，在固定覆盖率下可降低 Brier score 和最差亚组校准误差。
- H4：在附加模态不可靠时回退至临床模型，比强制多模态融合获得更稳定的决策净获益。

## 6. TRUST-HN 框架

### 6.1 模块一：Clinical anchor

先使用预测时点常规可获得变量建立临床锚定模型，例如：

- 年龄、性别；
- ECOG/体能状态；
- 原发部位；
- T、N、总体分期；
- HPV/p16；
- 吸烟；
- 已知的治疗计划变量。

主模型为 elastic-net Cox 或离散时间生存模型。临床锚点代表在没有可靠附加模态时系统仍可提供的最低风险估计。

### 6.2 模块二：Residual modality learner

附加模态模型不从头重复预测全部风险，而是学习临床锚点未解释的残余信息：

- CT：PyRadiomics或公开深度特征；
- HANCOCK：病理、血液、编码文本和TMA预提取特征；
- 转录组：通路活性分数。

可使用带 clinical-risk offset 的 Cox/离散时间模型，或预测临床模型残差。这样直接回答“附加模态是否有增量价值”，也减少模型仅复制分期和肿瘤体积的可能。

### 6.3 模块三：Shortcut audit

对每种附加模态建立与其结构相匹配的负对照：

- RADCURE：随机体素和打乱体素的公开负对照影像组学；
- HANCOCK：患者间模态置换、去除特定模态、仅保留缺失模式；
- 转录组：在训练集内进行基因/通路置换，并保留批次结构；
- 所有数据：比较真实模态、体积/缺失模式和负对照所产生的风险分数。

输出不是简单的“有没有显著性”，而是患者级 shortcut sensitivity score：当输入模态被替换为负对照或体积被匹配时，预测变化多大。

### 6.4 模块四：Shift detector

使用低成本方法检测患者是否偏离训练分布：

- shrinkage Mahalanobis distance；
- k-nearest-neighbour distance；
- Isolation Forest；
- 轻量自编码器，仅作敏感性分析。

OOD 分数只能使用输入特征计算，不能利用测试结局。阈值在验证集或模拟偏移数据中确定。

### 6.5 模块五：Uncertainty calibration

- Bootstrap或深度集成估计模型不确定性；
- 交叉拟合的 conformal survival intervals；
- 24个月绝对风险校准；
- 不确定性必须与真实错误相关，而不只是区间更宽。

### 6.6 模块六：Reliability gate

最终门控综合：

- OOD 分数；
- 预测区间宽度；
- shortcut sensitivity；
- 模态缺失或异常标志。

输出三种状态：

1. **Augment**：附加模态可靠，输出融合风险；
2. **Fallback**：附加模态不可靠，输出临床锚定风险；
3. **Abstain**：全部输入或整体预测不可靠，提示人工复核。

门控应使用简单逻辑回归、梯度提升或预设阈值，不需要大型神经网络。

## 7. 多队列验证设计

### Study 1：RADCURE——捷径学习与主要临床任务

临床场景：根治性 RT/CRT 前风险分层。  
主要终点：24个月OS。  
次要终点：完整OS。  
输入：临床、GTVp体积、真实PyRadiomics、负对照特征、可审计的预提取深度特征。  
验证：RADCURE challenge锁定测试或时间测试。  
主要作用：开发TRUST-HN并验证肿瘤体积/负对照捷径。

RADCURE包含3,346例患者；原始CT约333 GB，但本研究只使用临床表和公开处理后特征。[TCIA](https://wiki.cancerimagingarchive.net/pages/viewpage.action?pageId=70226325)；[ORCESTRA](https://www.orcestra.ca/radiomicset/6746454c0c5b69993c6cbe21)。

### Study 2：HANCOCK——模态缺失与OOD验证

临床场景：手术后复发和生存风险评估。  
终点：OS和复发；优先使用time-to-event，如果时间戳完整。  
输入：官方预提取的人口学、病理、血液、ICD和TMA特征。  
验证：官方分布内、分布外和口咽癌完全留出测试。  
压力测试：随机模态缺失、结构性缺失、只保留临床模态。  
主要作用：检验可靠性门控是否能从影像组学场景迁移至多模态真实世界数据。

HANCOCK包含763例，并公开了预提取特征和OOD划分：[Nature Communications数据论文](https://www.nature.com/articles/s41467-025-62386-6)；[代码](https://github.com/ankilab/HANCOCK_MultimodalDataset)。

### Study 3：TCGA-HNSC→GSE65858——跨平台迁移

临床场景：分子风险分层。  
主要终点：OS。  
训练：TCGA-HNSC。  
外部测试：GSE65858的270个质控后HNSCC样本。  
敏感性验证：GSE41613的97名HPV阴性OSCC，仅用于匹配人群和终点可比时。  
输入：临床变量和rank/pathway-based表达评分，不直接迁移原始基因表达尺度。  
主要作用：检验框架在RNA-seq→芯片的真实平台偏移中，能否识别失配、保持校准或安全拒绝。

公开数据：[GSE65858](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE65858)；[GSE41613](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE41613)。

### 重要表述边界

三个study并不是把不同变量强行输入同一个模型，也不是声称RADCURE模型可以直接用于手术患者。它们分别训练场景特异的预后模型，共同验证同一套可靠性原则：

> 临床锚定、残余增量学习、捷径审计、偏移检测、不确定性校准和安全回退。

因此论文声称的是**方法框架的跨模态可迁移性**，不是一个参数完全共享的“万能HNSCC模型”。

## 8. 模型与算力

模型组合：

- Elastic-net Cox；
- Random Survival Forest；
- XGBoost-Cox/AFT；
- 参数量<100万的小型离散时间MLP；
- 简单 stacking，仅在验证集学习权重。

资源策略：

- RADCURE不下载原始CT；
- HANCOCK不下载WSI，只使用官方特征；
- TCGA/GEO只下载表达矩阵和临床表；
- 总数据预计显著低于几十GB；
- 传统模型可在CPU完成；GPU仅用于小MLP；
- 主要计算消耗来自嵌套验证和bootstrap，而不是大模型训练。

## 9. 主要评价指标

### Dataset-specific performance

- Uno C-index；
- 24个月time-dependent AUC；
- IPCW Brier score和integrated Brier score；
- calibration-in-the-large、校准斜率和校准曲线；
- decision curve net benefit。

### Trustworthiness endpoints

- 在固定80%和90%自动覆盖率下的Brier score；
- risk–coverage curve及其面积；
- OOD检测AUROC/AUPRC；
- 分布内与分布外校准差；
- 最差亚组Brier score和校准误差；
- Fallback相对强制融合的净获益；
- 不确定性与绝对预测误差的相关性；
- 负对照特征模型相对真实特征模型的性能保留比例。

### 预设主比较

1. 强制多模态融合 vs TRUST-HN门控；
2. 临床锚点 vs 临床锚点+可靠附加模态；
3. 真实附加模态 vs 负对照/置换模态；
4. 随机拆分 vs 时间/OOD/外部测试；
5. 全覆盖预测 vs 固定覆盖率选择性预测。

## 10. 论文预期结果的叙事顺序

一篇好的 npj Digital Medicine 稿件不应从“我们设计了某网络”开始，而应按下面顺序讲结果：

### Result 1：常规模型在内部数据上看起来有效

临床、附加模态和常规融合模型在分布内测试中具有一定判别能力，为后续可靠性分析建立合理基线。

### Result 2：判别力掩盖了不同类型的失败

- RADCURE中，负对照或肿瘤体积可重现部分影像预测能力；
- HANCOCK中，模态缺失和口咽癌留出导致校准下降；
- TCGA→GEO中，平台偏移使风险尺度失配；
- 部分情况下AUC下降不大，但绝对风险和临床净获益明显变差。

这是论文的关键“问题发现”。

### Result 3：临床锚定和残余学习减少无效融合

附加模态只有在提供超出临床变量的信息时才进入最终风险；模型不再因为维度更高而自动偏向影像或组学。

### Result 4：可靠性分数能够提前识别高错误病例

OOD、预测区间和捷径敏感度与测试误差相关；高不确定性病例在各队列具有更差校准。

### Result 5：回退与拒绝策略改善安全性和净获益

在固定自动覆盖率下，TRUST-HN降低Brier score和最差亚组误差；当附加模态不可靠时，回退临床锚点优于强制融合。

### Result 6：同一原则跨模态复现

虽然三个临床场景和模态不同，临床锚定—增量判断—可靠性门控在影像组学、多模态临床病理和跨平台转录组中表现出一致方向。

## 11. 摘要草案

### Background

Artificial intelligence models integrating imaging, pathological and molecular data have shown promise for prognostic stratification in head and neck squamous cell carcinoma. However, apparent improvements in discrimination may arise from tumour volume, data acquisition biases or patterns of missingness, while most models continue to produce predictions for patients who differ substantially from their development data. A clinically useful prognostic system should therefore determine not only patient risk, but also whether an additional modality is informative and whether the resulting prediction is reliable.

### Methods

We developed TRUST-HN, a resource-efficient prognostic framework combining a clinical anchor model, residual modality learning, shortcut testing, distribution-shift detection, survival calibration and uncertainty-guided fallback or abstention. The framework was evaluated in three publicly available head and neck cancer settings: pretreatment CT radiomics and negative-control features from RADCURE; structured, pathological, blood and tissue-microarray features with predefined in-distribution and out-of-distribution splits from HANCOCK; and cross-platform transcriptomic survival modelling from TCGA-HNSC to GSE65858. Models were trained separately for each clinical setting using penalized Cox regression, survival forests, gradient boosting and small neural networks. Performance was evaluated using time-dependent discrimination, Brier scores, calibration, decision-curve analysis and risk–coverage curves.

### Anticipated results narrative

Conventional fusion models are expected to retain reasonable discrimination in internal validation while showing heterogeneous shortcut dependence and calibration deterioration under negative controls, missing modalities and distribution shift. TRUST-HN is designed to identify high-error cases, preserve the clinical anchor when an added modality is unreliable, and reduce prediction error at prespecified coverage levels without requiring large foundation models or private institutional data.

### Interpretation

This study will test whether reliability-gated rather than compulsory multimodal fusion provides a safer and more reproducible strategy for prognostic AI in heterogeneous head and neck cancer data. The resulting framework, code and evaluation protocol are intended to support transparent assessment of deployment readiness in settings where external data, complete modalities and high computational resources are limited.

最终摘要必须根据真实结果改写，不能把预期结果提前写成已证明事实。

## 12. Introduction末段模板

> In this study, we hypothesized that the clinical utility of prognostic artificial intelligence in HNSCC could be improved by explicitly separating baseline clinical risk from the incremental contribution of additional modalities and by withholding multimodal predictions when shortcut dependence, distribution shift or predictive uncertainty is high. We therefore developed TRUST-HN, a resource-efficient framework integrating clinical anchoring, residual modality learning, shortcut testing, shift detection, survival calibration and selective prediction. We evaluated the framework across publicly available radiomic, clinicopathological and transcriptomic HNSCC cohorts representing definitive radiotherapy, surgical and cross-platform molecular settings. Rather than seeking a universally shared predictor across heterogeneous cohorts, we tested whether a common reliability strategy could consistently identify when modality augmentation was beneficial, when fallback to clinical risk was safer and when automated prediction should be withheld.

## 13. 图表结构

### Figure 1：临床问题和TRUST-HN流程

患者资料→临床锚点→附加模态残余模型→捷径/OOD/不确定性检测→Augment、Fallback或Abstain。

### Figure 2：三个公开研究场景

RADCURE放疗前CT、HANCOCK手术多模态、TCGA→GEO转录组迁移；展示纳排、样本量、模态、终点和验证类型。

### Figure 3：隐藏失败模式

真实特征与负对照、ID与OOD、完整与缺失模态、RNA-seq与芯片之间的判别和校准差异。

### Figure 4：可靠性门控

错误率随OOD分数/区间宽度变化；risk–coverage curves；模型拒绝病例示例。

### Figure 5：临床增量价值

临床锚点、强制融合和TRUST-HN的校准、Brier和DCA比较。

### Figure 6：跨队列一致性

以森林图汇总各数据集的Brier改善、最差亚组校准改善和固定覆盖率性能。

## 14. 哪些结果才足以支撑 npj Digital Medicine

满足以下大部分条件，故事才真正成立：

- 至少两个独立数据生态中，强制融合在OOD/缺失条件下出现可量化失效；
- 可靠性分数与真实误差稳定相关，而不只是检测数据集标签；
- 门控在预设80%或90%覆盖率下改善Brier或校准；
- 回退策略优于简单拒绝和始终使用临床模型；
- 改善不仅存在于随机拆分，也存在于HANCOCK OOD和TCGA→GEO外部迁移；
- 提供临床净获益，而不只是AUC；
- 模型、阈值、分析方案和代码可完整复现；
- 对不同HPV、部位、性别和年龄亚组报告公平性与覆盖率。

如果只有RADCURE负对照结果，而HANCOCK和TCGA→GEO没有复现可靠性门控价值，论文应回退为专科影像组学/医学物理方向，不宜继续以 npj Digital Medicine 为唯一目标。

## 15. 这版故事相对第二版真正扩大的地方

| 第二版 | npj DM重构版 |
|---|---|
| 单一RADCURE影像组学审计 | 三个公开数据生态的可靠性框架验证 |
| 体积和负对照是核心终点 | 捷径、模态缺失、OOD、平台偏移共同构成临床失败模式 |
| 输出一个生存模型 | 输出风险、可信度、回退/拒绝决策 |
| 关注影像是否有增量价值 | 关注附加模态何时值得使用、何时不应使用 |
| 单一数据集的方法结论 | 跨影像、临床病理和转录组的方法学结论 |
| 可能被视为影像组学复核 | 定位为可信、资源友好的数字医学系统 |

## 16. 可行性和诚实评价

- 数据与算力可行性：**9/10**。全部可在特征或表达矩阵层完成。
- 工程可行性：**8/10**。需要统一生存评价和可靠性接口，但模型很轻。
- 故事完整性：**8/10**。三个study分别覆盖捷径、缺失/OOD和真正外部平台偏移。
- 方法新颖性：**7/10**。单项技术并非全新，创新在于临床锚定、残余增量、可靠性门控的整合及跨模态验证。
- npj Digital Medicine匹配度：从第二版约**6/10**提高到约**7–8/10**。
- 最大限制：三个队列不是同一模型的直接外部验证；公开数据仍为回顾性，无法证明真实前瞻性临床效益。

最重要的写作原则是：

> 不把论文包装成“万能多模态大模型”，而是把它写成一个能够识别自身适用边界、在不可靠输入下安全降级的数字医学框架。

这既能扩大故事层级，又不超出公开数据和小算力的现实条件。
