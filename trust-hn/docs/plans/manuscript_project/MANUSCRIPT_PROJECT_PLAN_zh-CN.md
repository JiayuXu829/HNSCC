# TRUST-HN 论文写作完整项目计划

**制定日期：** 2026-08-11  
**目标：** 将现有 Phase 0–8 的数据、方法、锁定实验、事后对比、可视化与限制整合为一篇可投稿的英文医学人工智能论文，并使用 Springer Nature LaTeX 模板完成最终排版和投稿前质控。  
**LaTeX模板：** `D:\medical_paper\HNSCC\Springer_Nature_LaTeX_Template`  
**呈现参考：** `D:\medical_paper\HNSCC\main_pj.pdf`

## 一、最终成品和呈现原则

1. 保留原始 Springer Nature 模板不被破坏，从模板复制一个独立稿件工作目录，例如 `trust-hn/manuscript/springer_nature/`。
2. 最终正文使用英文；项目管理、证据地图、论证地图和阶段报告保留中文版本，必要时同时维护英文版本。
3. 参考 `main_pj.pdf` 的组织和视觉呈现，而不复制其文字或研究内容：A4单栏、简洁摘要页、编号章节、Results置于Methods之前、主图和主表紧随论证、图注完整、正文后集中放声明和补充材料。
4. 建议主文结构：Title page → Abstract → Keywords → Introduction → Results → Discussion → Methods → Declarations → Data availability → Code availability → Author contributions → Competing interests → References；Supplementary Information作为独立文件或附后文件。
5. 所有数字必须可追溯到CSV/JSON结果文件；所有结论必须绑定具体队列、方法、指标、置信区间和分析性质。
6. Phase 6锁定结果与Phase 7事后探索结果必须严格区分。Phase 8的 `inner_hancock` 结果单独报告；当前模拟结果不能替代真正独立院内队列的正式外部验证结论。

## 二、推荐论文核心主线

论文不应写成“TRUST-HN在所有队列中全面胜出”，而应围绕以下逻辑展开：

1. HNSCC预后建模具有多模态信息增益潜力，但附加模态会受到缺失、平台差异、分布偏移和捷径信号影响。
2. TRUST-HN以临床模型为锚点，通过增量/残差融合吸收附加模态信息，并以可靠性门控执行AUGMENT、FALLBACK或ABSTAIN。
3. B6在RADCURE和HANCOCK中表现出较好的回顾性迁移，但跨平台转录组队列GSE65858暴露出明显校准失败。
4. B7能够改变覆盖率并识别部分不可靠样本，但未稳定优于B6；其价值更接近安全降级和风险控制，而不是保证更高准确率。
5. C2等强比较方法在部分队列中表现突出，但在不同数据生态中排序变化明显，没有模型在全部队列统一获胜。
6. 负对照、压力测试和外部结果共同表明：良好的表面辨别力不等于模态特异性、普遍稳健性、临床效用或部署就绪。
7. 论文贡献是提出并系统检验“临床锚定—多模态增量融合—可靠性评估—安全降级”的可审计框架，同时诚实呈现适用场景和失败边界。

建议最终一句话结论：

> Across heterogeneous HNSCC data ecosystems, multimodal prognostic gains and reliability-gating behaviour were strongly cohort dependent; reliability-aware fallback and abstention exposed failure modes of forced fusion, but current retrospective evidence did not establish universal robustness, deployable thresholds, or clinical utility.

## 三、分阶段工作包

### WP0：建立论文项目目录和只读证据基线

任务：

- 从Springer Nature模板复制稿件工程，不直接在原模板上堆叠实验文件；
- 建立 `main.tex`、`references.bib`、`sections/`、`figures/`、`tables/`、`supplement/`、`checklists/` 和 `build/`；
- 登记Phase 6冻结文件、Phase 7探索结果、Phase 8结果及哈希；
- 禁止通过写论文重新调参、重新选择阈值或覆盖既有实验。

交付物：稿件目录、文件清单、构建说明、冻结资产清单。  
审查点：确认模板位置、稿件输出路径和禁止修改的实验资产。

### WP1：证据地图与声明矩阵

任务：

- 建立“数据集—角色—模态—样本量—终点—模型—指标—图表—允许结论”的证据地图；
- 区分开发、校准、锁定测试、OOD、外部、敏感性、事后探索和Phase 8院内/模拟分析；
- 为每一个预期结果句标注来源CSV、具体行、分析性质和95%CI；
- 建立允许、需要限定和禁止的论文声明清单。

交付物：`evidence_map.csv`、`claim_matrix_zh-CN.md`、`claim_matrix_en.md`。  
审查点：任何无法追溯到结果文件的数字或结论不得进入正文。

### WP2：论文论证地图和逐段提纲

任务：

- 确定候选标题、短标题、研究问题和主要贡献；
- 为Abstract、Introduction、Results、Discussion和Methods建立逐段提纲；
- 每段明确“本段回答的问题—使用的证据—核心解释—限制—对应图表”；
- 固定主文和补充材料边界；
- 先完成提纲和论证地图，用户批准后再写完整正文。

交付物：`paper_outline_zh-CN.md`、`paper_outline_en.md`、`argument_map.md`。  
审查点：用户批准主线、标题方向、章节顺序和主图主表方案。

### WP3：数据集、方法和术语规范化

任务：

- 固定每个队列的论文显示名、代码名、数据来源性质和分析角色；
- 统一24个月OS终点、时间起点、删失、IPCW和bootstrap描述；
- 建立B0–B7、M0、N0、C1–C4的方法字典；
- 统一“clinical anchor”“forced fusion”“reliability gate”“fallback”“abstention”“coverage”等术语；
- 对 `inner_hancock` 单独建立论文写作边界，避免将模拟重叠结果误写为真正独立外部验证。

交付物：队列词典、变量/终点词典、方法缩写表、术语表。  
审查点：摘要、正文、图表和补充材料中的命名必须完全一致。

### WP4：主图、主表和补充图表蓝图

建议主文放6–7张图：

1. **Figure 1：研究设计与TRUST-HN框架。** 展示临床锚点、附加模态、B6融合、可靠性评分和AUGMENT/FALLBACK/ABSTAIN路径。
2. **Figure 2：队列流程与模态矩阵。** 展示RADCURE、HANCOCK、TCGA-HNSC、GSE65858、GSE41613及 `inner_hancock` 的样本流、角色和模态。
3. **Figure 3：开发与校准阶段模型表现。** 展示主要模型的Brier、Uno C、AUC和校准结果。
4. **Figure 4：锁定/OOD/外部配对比较森林图。** 重点呈现B7 vs B6、B7 vs B2及关键95%CI。
5. **Figure 5：可靠性门控与选择性预测。** 展示risk–coverage、动作分布、可靠性分层与误差关系。
6. **Figure 6：多模态和分布偏移可视化。** 分面展示临床、CT影像组学、血液/TMA和转录组的分布或低维嵌入。
7. **Figure 7：Phase 8院内队列结果。** 展示14种方法比较、校准、门控动作和与公开队列的方向一致性；如果Phase 8仍是mock，则标为探索/流程验证并移至补充材料。

建议主文放4张表：

1. **Table 1：队列特征、样本量、模态和分析角色。**
2. **Table 2：各队列主要模型的绝对性能和95%CI。**
3. **Table 3：同一患者子集上的配对模型差值和95%CI。**
4. **Table 4：覆盖率、门控动作、压力测试和关键阴性结果。**

补充材料放：全部14种方法、全部随机种子、完整bootstrap区间、80/90/100%门控、亚组、缺失模式、负对照、压力测试、DCA阈值、特征处理、超参数和运行资源。

交付物：`figure_table_plan.md`、图表数据字典、每张图的草图和图注提纲。  
审查点：每张主图必须推动一个核心论点，不能仅为了增加图的数量。

### WP5：搭建Springer Nature LaTeX论文骨架

任务：

- 从 `sn-article.tex` 建立TRUST-HN主稿，不删除模板必须项；
- 按 `main_pj.pdf` 的阅读顺序组织Abstract、Introduction、Results、Discussion、Methods和Declarations；
- 将章节拆分到独立 `.tex` 文件；
- 建立图、表、补充材料和BibTeX引用路径；
- 先使用占位图表和提纲文字完成可编译骨架。

交付物：首个可编译PDF、章节文件、参考文献库和构建日志。  
审查点：骨架必须无致命LaTeX错误，所有图表、公式和章节可交叉引用。

### WP6：先写Methods

Methods建议分为：

1. Study design and reporting framework；
2. Cohorts, inclusion criteria and analysis roles；
3. Outcome definition and prediction horizon；
4. Clinical, radiomic, blood/TMA and transcriptomic preprocessing；
5. Missing-data handling and leakage prevention；
6. Baseline and comparator models B0–B5、C1–C4；
7. TRUST-HN B6 residual fusion；
8. B7 reliability estimation and gating actions；
9. Model training, calibration, freezing and one-time outcome access；
10. Statistical analysis、IPCW、C-index、AUC、calibration、bootstrap、DCA；
11. Negative controls、stress tests、subgroups and sensitivity analyses；
12. Software, reproducibility, ethics and governance。

写作要求：Methods必须足够详细，使读者可以在不接触患者级数据的情况下理解并复现实验逻辑。

### WP7：写Results

Results建议按证据顺序组织：

1. Cohort assembly and modality availability；
2. Development and calibration performance；
3. Locked retrospective evaluation in RADCURE；
4. OOD evaluation in HANCOCK；
5. Cross-platform transcriptomic external evaluation；
6. Post hoc comparator benchmark C1–C4；
7. Reliability gating, selective coverage and paired comparisons；
8. Negative controls, perturbation and missing-modality stress tests；
9. Calibration and decision-curve findings；
10. `inner_hancock` Phase 8结果及其与公开队列的一致性。

写作要求：

- Results只陈述观察结果，不在此处做过度机制解释；
- B7必须同时报告覆盖率和相同保留患者子集上的比较；
- 正结果、阴性结果和不一致结果都必须报告；
- 每个核心数字同时核对CSV和95%CI。

### WP8：写Introduction

建议5段：

1. HNSCC预后分层的临床需求；
2. 临床、影像、病理/血液和转录组多模态建模的潜力；
3. 数据缺失、平台差异、分布偏移、捷径和校准失败的问题；
4. 临床锚定、可靠性评估和安全降级的研究缺口；
5. 本研究的目的、设计、主要假设和贡献。

避免在Introduction提前宣称已经证明稳健性或临床效用。

### WP9：写Discussion、Conclusion、Title和Abstract

Discussion建议7段：

1. 概括主要发现；
2. 解释B6在部分队列中的增益；
3. 解释B7为什么有安全机制价值但未稳定提高准确率；
4. 讨论GSE65858跨平台校准失败；
5. 讨论RADCURE负对照和模态特异性不足；
6. 讨论C2等强基线、模型排序和队列依赖性；
7. 优势、限制、临床转化条件和下一步前瞻性验证。

Conclusion控制为一个克制段落。Abstract最后写，包含背景、目的、设计、主要队列、方法、2–4个最关键数字、阴性结果和谨慎结论。标题和关键词在全文稳定后确定。

### WP10：补充材料和声明文件

Supplement建议包括：

- 队列纳排流程和变量定义；
- 完整模态可用性及缺失率；
- 全部模型定义、超参数和随机种子；
- 全部患者级分析的汇总统计和置信区间；
- 完整校准结果、risk–coverage和DCA；
- 80/90/100%门控敏感性；
- 负对照、压力测试、消融和亚组结果；
- C1–C4事后探索结果；
- Phase 8完整结果及声明边界；
- 软件版本、硬件、运行命令和复现流程；
- Model card、TRIPOD+AI、PROBAST+AI和STROBE清单。

Declarations包括伦理审批/豁免、知情同意、数据可用性、代码可用性、作者贡献、利益冲突、资金和致谢。未知信息使用明确TODO，不得虚构。

### WP11：全文整合与数字审计

任务：

- 建立自动化数字核对脚本，检查正文、表格和图注中的样本量、事件数、指标和CI；
- 检查所有图表是否在正文被引用；
- 检查所有引用是否存在且文献与论点匹配；
- 检查预设/锁定与事后探索标签；
- 检查数据来源、伦理和私有队列表述；
- 检查结论是否超出证据。

交付物：数字审计报告、引用审计报告、声明边界审计报告。

### WP12：最终LaTeX排版和投稿包

任务：

- 按Springer Nature模板完成字体、标题、作者、单位、图表浮动、图注和参考文献格式；
- 参考 `main_pj.pdf` 控制页面密度、图表可读性、章节顺序和补充材料组织；
- 编译主文PDF和Supplement PDF；
- 清理警告、未解析引用、越界表格、低分辨率图片和重复标签；
- 在干净环境执行最终编译；
- 生成投稿清单、cover letter草稿、highlights和图文摘要方案。

完成标准：主文和补充材料可以从干净目录一次性编译；数字、图表、引用、声明和结论边界全部通过检查。

## 四、分步审查顺序

1. 先完成WP0–WP3：证据地图、声明矩阵、术语规范、完整提纲和论证地图；提交用户批准。
2. 批准后完成WP4–WP5：主图主表蓝图和可编译LaTeX骨架；提交用户批准。
3. 然后完成WP6–WP7：Methods和Results；进行第一次全文数字审计。
4. 再完成WP8–WP9：Introduction、Discussion、Conclusion和Abstract；进行论证与声明审计。
5. 完成WP10：Supplement、checklists和Declarations。
6. 最后完成WP11–WP12：全文整合、LaTeX排版、最终PDF和投稿包。

每个工作包结束必须报告：修改文件、使用的数据和结果、运行命令、测试/编译状态、尚存TODO、是否触碰冻结资产、可以和不可以声称的结论，以及下一审查点。未经用户确认，不跨越关键审查点。