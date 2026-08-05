# PRISM-HN v2.0：头颈鳞癌术后多模态复发风险研究详细方案

> **目标期刊**：npj Digital Medicine（首选）；若无法完成独立医院外部验证，可转向医学信息学、计算病理或肿瘤人工智能期刊。  
> **研究类型**：回顾性、多队列、时间到事件预测模型开发与外部验证研究。  
> **核心创新**：训练期特权 IHC 信息蒸馏、缺失模态原生融合、竞争风险建模、外部校准与选择性预测。  
> **文档用途**：研究方案、预注册草案、Codex/代码代理实现规格、论文写作蓝图。  
> **版本**：v2.0，2026-08-05。  
> **基于文档**：`PRISM_HN_npj_Digital_Medicine_research_idea(1).md` v1.0。

---

## 0. 本次审查后的核心结论

原方案的创新主线是成立的，但要达到可发表、可复现和可外部验证的标准，需要做以下关键收敛。

### 0.1 必须修正的问题

1. **区分手术日期、信息可用日期和预测起点**  
   原方案把根治性手术日设为 index date，同时使用手术后才形成的常规病理和 WSI。严格来说，模型并不能在手术瞬间获得这些信息。主分析应采用术后 landmark 设计，避免把术后信息倒置为手术日已知信息。

2. **把一个“大而全模型”拆成明确的部署配置**  
   TCGA-HNSC 和 CPTAC-HNSCC通常不具备 HANCOCK 同款手术全文、实验室和 IHC。外部验证必须针对跨队列共同可获得的输入配置，而不是只把整块模态设为缺失后仍称为同一完整模型的外部验证。

3. **简化主模型损失，避免创新点过多而无法归因**  
   主模型应把特权蒸馏集中到“竞争风险分布蒸馏＋免疫辅助监督”。embedding alignment 和多种 contrastive loss 放入次要消融，而不是全部作为默认主损失。

4. **教师信号必须交叉拟合**  
   学生不能直接蒸馏教师在同一患者上的训练内预测。教师 logits、embedding 或 immune pseudo-label 应通过 out-of-fold teacher 产生，防止训练内过拟合信号被蒸馏到学生。

5. **主要外部结论必须分路线预先定义**  
   - 有独立医院数据：独立医院为主要外部验证，TCGA/CPTAC 为公开数据运输性和生物学验证。  
   - 只有公开数据：HANCOCK 时间外测试为主要性能测试；TCGA 为 endpoint 不完全一致条件下的外部运输性验证，不能过度宣称完全等价复发外部验证。

### 0.2 最终建议的论文主线

> 在完成根治性手术后的病理信息可用时点，开发一个依赖常规临床病理数据和 H&E WSI 的核心竞争风险模型；在 HANCOCK 中利用手术文本、术前实验室和多重 IHC 作为增强信息及训练期特权监督；模型在缺失可选模态时仍可推理，并在时间外队列、TCGA-HNSC、CPTAC-HNSCC及独立医院队列评价区分度、校准、临床净获益、缺失模态鲁棒性与不确定性。

---

## 1. 研究目的、问题和可检验假设

### 1.1 主要研究目的

开发并验证 PRISM-HN，用于预测根治性手术后 HNSCC 患者在未来 24 和 36 个月发生首次复发/进展的累积发生风险，同时把复发前死亡作为竞争事件。

### 1.2 次要研究目的

1. 评估 12、60 个月复发风险，60 个月结果在事件数不足时仅作探索性分析。
2. 评估未复发死亡的累积发生风险。
3. 评估 IHC 特权信息蒸馏能否提高不依赖 IHC 的学生模型性能。
4. 评估文本和术前实验室对常规临床病理＋WSI 的增量价值。
5. 评估模型在真实缺失模态和人工缺失模态下的鲁棒性。
6. 评估外部重校准是否能恢复跨中心校准，而不改变模型排序能力。
7. 检验模型风险表型与 IHC、RNA、蛋白质组和预设生物通路的关联。

### 1.3 主要假设

按预先规定的比较层级检验：

- **H1：外部性能**  
  Core-PRISM 相比 Common-core clinical Cox/Fine-Gray 基线，在主要外部验证队列获得更高的 36 个月 time-dependent AUC 或 cause-specific concordance，并降低 recurrence-CIF integrated Brier score。

- **H2：蒸馏增益**  
  在相同学生输入和相同训练数据下，带交叉拟合 IHC 教师蒸馏的学生模型优于无蒸馏学生模型。

- **H3：缺失鲁棒性**  
  在文本、实验室或 WSI 单一模态缺失条件下，PRISM-HN 相比完整输入的性能下降小于普通拼接模型，并具有更好的校准保持能力。

- **H4：临床效用**  
  在预设的 24/36 个月风险阈值范围内，PRISM-HN 的净获益高于“全部强化随访”“全部常规随访”和临床基线模型。

### 1.4 预设主要比较顺序

为了避免大量消融导致多重比较问题，采用层级检验：

1. Core-PRISM vs common-core clinical baseline；
2. Distilled student vs non-distilled student；
3. Extended-PRISM vs Core-PRISM；
4. PRISM missing-aware fusion vs mean-imputation concatenation；
5. 其余模型和亚组均为次要或探索性分析。

---

## 2. 临床使用场景和预测时点

### 2.1 目标场景

模型用于首次根治性手术后的病理结果已可用于术后 MDT、但辅助治疗尚未开始或尚未完成决策的时点。模型只提供预后风险和监测/复核支持，不直接给出放疗、化疗或免疫治疗推荐。

### 2.2 主分析的 landmark 定义

#### 公共数据主分析

- `surgery_date`：首次根治性局部手术日期。
- `landmark_date`：`surgery_date + 30 days`。
- 纳入患者必须在 landmark 前未发生复发、远处转移或死亡。
- 所有特征必须在 landmark 前形成，并且不能包含 landmark 后发生的结局、治疗完成情况或随访信息。
- 生存时间从 landmark 开始重新计时：

```text
analysis_time = event_or_censor_date - landmark_date
```

使用 30 天 landmark 的原因是常规病理和 WSI 来源于切除标本，通常不是手术瞬间可用。若 HANCOCK 无法可靠构建 30 天 landmark，则必须在 `protocol_deviations.md` 记录，并采用下述敏感性分析。

#### 独立医院优选主分析

如果本地数据包含病理签发日期或术后 MDT 日期：

```text
landmark_date = max(final_pathology_signout_date, surgery_date)
```

要求 landmark 发生在辅助治疗启动前；若病理签发晚于辅助治疗开始，应排除或单独分析。

### 2.3 敏感性时间起点

1. 从手术日开始计时的传统分析；
2. 14 天 landmark；
3. 30 天 landmark；
4. 实际病理签发日 landmark，仅限有精确日期的独立医院队列；
5. 从初始诊断日开始，主要用于与 HANCOCK 原始事件时间体系对照，不作为最终部署分析。

### 2.4 允许使用和禁止使用的信息

**允许：**

- 术前人口学和病史；
- 术前或手术当日实验室结果；
- 首次局部手术记录；
- 切除标本常规病理；
- 原发肿瘤 H&E WSI；
- 训练期教师使用的 IHC/TMA；
- 在 landmark 前已经明确的 HPV/p16、pT、pN、切缘、ENE、PNI、LVI 等。

**禁止：**

- 辅助治疗是否完成；
- 治疗过程中剂量调整、毒性、疗效；
- 复发后实验室、影像和文本；
- 任何包含“后续复发、转移、死亡、姑息治疗”信息的随访记录；
- 由全体数据或外部测试数据拟合的标准化、缺失填补、特征选择或风险阈值。

---

## 3. 模型部署配置

### 3.1 Common-core clinical 变量集

这是所有主要模型和外部队列的最小共同变量集。实际字段以数据审计后的交集为准：

- 年龄；
- 性别；
- 原发部位；
- pT；
- pN；
- 总分期或可由 pT/pN 推导的分期；
- HPV/p16；
- 吸烟状态；
- 诊断或手术年份；
- 变量缺失指示。

不得为了保留更多变量而在外部队列中使用不可靠的手工映射。

### 3.2 Core-PRISM：主要跨队列部署模型

输入：

- common-core clinical；
- 原发肿瘤 H&E WSI；
- WSI QC 和模态可用性信息。

用途：

- 主要外部验证；
- TCGA-HNSC zero-shot 运输性验证；
- CPTAC-HNSCC 次级验证；
- 独立医院主要部署配置。

### 3.3 Extended-PRISM：HANCOCK/本地增强模型

输入：

- Core-PRISM 全部输入；
- 扩展病理变量：切缘、ENE、PNI、LVI、浸润深度、阳性淋巴结数等；
- 术前实验室；
- 手术记录和病史文本。

用途：

- HANCOCK 内部时间外测试；
- 独立医院存在相同模态时的外部验证；
- 分析文本和实验室的增量价值。

### 3.4 Teacher-PRISM：训练期特权模型

输入：

- Extended-PRISM 全部输入；
- IHC/TMA marker tokens；
- 可用的 CD3/CD8 细胞密度或其他可靠定量 IHC 指标。

Teacher-PRISM 不作为临床部署模型，只用于：

- 给学生生成 out-of-fold 竞争风险分布；
- 提供免疫表型辅助标签；
- 定义“使用 IHC 时的性能上限”。

### 3.5 Clinical-only fallback

输入：common-core clinical。  
用途：WSI 无法处理、扫描失败或外部机构暂未数字化时的后备模型。Clinical-only 输出必须单独校准，不能直接复用 Core-PRISM 的校准层。

---

## 4. 数据来源和队列角色

### 4.1 HANCOCK

已公开论文描述 HANCOCK 为 763 例单中心真实世界头颈癌患者，诊断年份为 2005–2019；原发肿瘤 H&E WSI 大约覆盖 701 例，手术报告约 742 例，并包含结构化病理、术前血液、事件时间、淋巴结 WSI 和多重 TMA/IHC。原始研究采用二分类方式预测三年复发和生存，本项目的主要增量是严格时间到事件、缺失模态、全文语义和特权蒸馏。

**主要用途：**

- 模型开发；
- 时间外内部测试；
- IHC 教师训练；
- 文本、实验室和扩展病理增量价值；
- 自然缺失模式分析；
- 官方 OOD split 的次级鲁棒性测试。

### 4.2 TCGA-HNSC

**用途：**

- Core-PRISM zero-shot 外部运输性验证；
- 评估扫描、中心和人群域偏移；
- RNA-seq 关联和通路验证。

**限制：**

- 缺少 HANCOCK 同款手术全文、术前实验室和 IHC；
- DFI/PFI 与 HANCOCK 的首次复发定义不完全等价；
- 手术时点、辅助治疗路径和病理变量完整度可能不同。

因此，TCGA 主分析必须明确标注为“复发/进展运输性验证”或“endpoint-harmonized external validation”，不能隐去 endpoint 差异。

### 4.3 CPTAC-HNSCC

**用途：**

- HPV 阴性高风险亚群的次级外部验证；
- 风险分数与蛋白组、磷酸化组和免疫通路关联；
- 不能用于调参或阈值选择。

事件数不足时仅报告点估计、置信区间和生物学一致性，不作强亚组结论。

### 4.4 独立医院队列

**首选设计：**连续病例、回顾性时间外或前瞻性静默运行。

必须记录：

- 模型输入获得率；
- WSI 无法处理率；
- 低置信度/拒绝率；
- 每位患者总处理时间；
- 人工数据整理耗时；
- 预测结果是否在临床决策前生成；
- 临床医生是否查看结果；
- 若为静默验证，模型输出不得影响治疗。

### 4.5 数据审计后的路线决策

```text
Route A：存在可靠独立医院队列
    主要外部验证 = 独立医院
    TCGA/CPTAC = 公开运输性和生物学验证

Route B：只有公开数据
    主要性能测试 = HANCOCK 时间外测试
    外部运输性验证 = TCGA-HNSC
    次级生物学验证 = CPTAC-HNSCC
    投稿中降低“临床部署验证”措辞
```

---

## 5. 纳入、排除和队列构建

### 5.1 纳入标准

1. 口腔、口咽、下咽或喉部原发鳞状细胞癌；
2. 初次诊断，接受根治性意图的首次局部手术；
3. 可识别手术或首次局部治疗日期；
4. landmark 时仍存活且无复发/进展；
5. 有可计算的事件/删失时间；
6. 至少具有 common-core clinical；
7. Core-PRISM 分析需有可用原发肿瘤 H&E WSI；
8. Teacher 分析需有至少一组有效 IHC/TMA 或可靠 IHC 定量数据。

### 5.2 排除标准

1. 非鳞状细胞癌；
2. 初诊远处转移且非根治性治疗；
3. 复发病例作为首次记录；
4. 既往头颈癌导致 index event 无法确定；
5. 事件发生在 landmark 前；
6. WSI 与 patient ID 无法可靠映射；
7. 负随访时间、事件日期冲突或无法修复的时间顺序错误；
8. 文本明确包含 landmark 后随访或结局信息且无法安全截断；
9. 外部队列无法映射到预先规定的 endpoint 或输入配置。

### 5.3 多原发和多切片处理

- 每名患者仅保留首次符合标准的原发癌作为 index cancer；
- 同一患者多张原发肿瘤 WSI 均保留，由 patient-level pooling 汇总；
- 阳性淋巴结 WSI 不进入 Core-PRISM 主模型，只作为扩展实验，以保证跨队列一致性；
- 同一患者所有模态必须位于同一数据划分。

### 5.4 队列流程文件

Codex 必须输出：

- `cohort_flow_all.csv`；
- `cohort_exclusion_log.csv`；
- `patient_manifest.parquet`；
- `endpoint_mapping.csv`；
- `modality_availability.parquet`；
- `protocol_deviations.md`。

每个排除原因必须是互斥、可审计的代码值。

---

## 6. 结局和 estimand

### 6.1 主要 estimand

在 landmark 时无复发的根治性手术患者中，预测从 landmark 起 24 和 36 个月内首次复发/进展的累积发生概率，复发前全因死亡作为竞争事件。

### 6.2 事件编码

```text
0 = right censoring
1 = first recurrence/progression
2 = death before recurrence/progression
```

事件 1 可包含：

- 局部复发；
- 区域淋巴结复发；
- 远处转移；
- 数据源只能提供 progression 时，纳入复合终点并标记来源。

### 6.3 时间字段优先级

1. 明确的首次复发日期；
2. 明确的首次进展日期；
3. 明确的首次远处转移日期；
4. 若多个事件同日，统一记为事件 1；
5. 死亡发生在事件 1 前，记为事件 2；
6. 死亡发生在事件 1 后，不再是主要竞争事件。

### 6.4 次要结局

- 总生存；
- 局部区域复发；
- 远处转移；
- 12 个月和 60 个月复发 CIF；
- 复发前死亡 CIF；
- 三年二分类仅用于与 HANCOCK 原始研究对照，不作为主要分析。

### 6.5 外部 endpoint harmonization

生成 `endpoint_harmonization_table.md`，至少包含：

| 队列 | 原始 endpoint | 时间起点 | 事件定义 | 与主 endpoint 差异 | 分析角色 |
|---|---|---|---|---|---|
| HANCOCK | recurrence/progression event timeline | surgery/diagnosis relative time | first recurrence/progression | 主定义来源 | 开发/时间外测试 |
| TCGA | DFI/PFI | TCGA standardized origin | recurrence/progression/death rules differ | 不完全等价 | 运输性外部验证 |
| CPTAC | available recurrence/progression/OS | cohort-specific | audit-dependent | 可能不完整 | 次级验证 |
| Local | curated first recurrence | postoperative landmark | protocol-defined | 最接近目标场景 | 主要外部验证 |

---

## 7. 数据划分和防止信息泄漏

### 7.1 HANCOCK 主划分

按诊断/手术年份进行时间划分，不使用随机 8:2 作为主分析。

**自动划分规则：**

1. 按年份升序排列；
2. 最早年份累计约 65% 患者作为 development-train；
3. 接下来约 15% 作为 development-validation/calibration；
4. 最新约 20% 作为 temporal test；
5. 在满足比例的同时，temporal test 应尽量具有至少 40 个复发事件；若不足，向前扩展年份；
6. 划分只由年份、患者数和事件数决定，不根据模型性能调整。

### 7.2 内部交叉验证

在 development-train 内进行 5-fold grouped cross-validation：

- patient-level 分组；
- 尽量按事件类型和原发部位分层；
- 所有预处理器在每个 fold 的训练部分拟合；
- 产生 out-of-fold 预测用于模型选择、蒸馏和校准；
- 不对 temporal test 进行任何调参。

### 7.3 教师交叉拟合

对 IHC 子集进行 K-fold teacher cross-fitting：

```text
for fold k:
    teacher_k 在 IHC subset 除 fold k 外训练
    teacher_k 给 fold k 患者产生 logits/embedding/immune predictions
合并所有 fold 的预测，得到每名患者的 OOF teacher targets
```

最终全 IHC 子集教师仅用于性能上限展示和部署外解释，不用于生成训练内蒸馏标签。

### 7.4 官方 ID/OOD split

HANCOCK 原论文提供基于多模态患者向量的 ID/OOD split。该 split 用于次级鲁棒性分析，不作为主要性能测试，因为其生成过程与完整模态和原始二分类标签有关。

### 7.5 外部队列冻结规则

在首次运行 TCGA/CPTAC/独立医院前，必须冻结：

- 输入变量字典；
- WSI encoder 和 tile pipeline；
- 文本 encoder；
- 模型权重；
- 时间区间；
- 风险计算公式；
- calibration layer；
- 拒绝预测阈值；
- 主要比较和统计代码。

生成 `model_freeze_manifest.json` 和 SHA-256。

---

## 8. 各模态预处理

## 8.1 H&E WSI

### 8.1.1 主分析范围

- 仅使用原发肿瘤切除标本 H&E WSI；
- 使用 HANCOCK 提供的稀疏肿瘤区域标注作为优先 ROI；
- 若外部队列无标注，使用组织检测＋肿瘤感知 MIL，不要求外部人工标注；
- 阳性淋巴结 WSI 单独作为扩展实验。

### 8.1.2 分辨率和切块

- 统一目标分辨率：约 `0.5 µm/pixel`，接近 20×；
- tile size：按 foundation model 官方要求，默认 `256×256`；
- tissue coverage：≥70%；
- 训练每张 slide 最多采样 2,048 tiles；
- 验证/测试固定最多 4,096 tiles；
- 采样随机种子固定并保存坐标；
- 同一患者多张 slide 分别编码，再进行 patient-level attention pooling。

### 8.1.3 WSI QC

对每张 slide 输出：

- tissue area；
- blur score；
- pen/marker estimate；
- fold/bubble estimate；
- saturation/brightness distribution；
-有效 tile 数；
- scanner/mpp；
- QC pass/fail 和具体失败原因。

预设拒绝条件示例：

- 有效组织 tile <100；
- 大面积失焦；
- mpp 无法推断且无法安全恢复；
- 文件损坏或解码失败。

阈值在 development 数据上通过人工抽样确定，之后冻结。

### 8.1.4 病理 encoder 选择

**主模型：**TITAN frozen slide embedding，前提是权重、许可证和官方预处理可稳定复现。  
**稳健性模型：**UNI/UNI2 patch embedding＋ABMIL/CLAM。  
**工程 fallback：**Prov-GigaPath frozen embedding。  
**低水平基线：**ImageNet ResNet50＋ABMIL。

模型选择规则：

- 仅使用 development-validation 比较；
- 主论文最多保留一个主 encoder 和一个预设稳健性 encoder；
- 外部结果不得用于选择 encoder；
- 记录权重来源、版本、许可证、哈希和输入规格。

### 8.1.5 stain robustness

主分析不进行强制 stain normalization。敏感性实验：

- Macenko normalization；
- H&E color jitter；
- scanner-aware augmentation；
- 不同中心分层校准。

## 8.2 手术记录和病史文本

### 8.2.1 文本来源

只使用首次局部手术对应的手术记录和 landmark 前病史。HANCOCK 原始资料同时有德文原文和英文翻译，应保留语言版本字段。

### 8.2.2 清洗

- 删除 header 中的姓名、医生、医院、日期和标识符；
- 将 ICD/OPS code 与自由文本分开编码；
- 去除重复模板段；
- 保留段落类型：history、procedure、findings、reconstruction、complications；
- 自动搜索可能结局泄漏词；
- 人工复核至少 100 份或 10% 文本，以较大者为准。

### 8.2.3 主文本 encoder

- 英文翻译主分析：BiomedBERT 或 Clinical-Longformer；
- 512 token/chunk；
- 每份报告最多 12 个 chunk；
- 超长文档采用头部＋尾部＋均匀抽样，不能只截取前 512 token；
- chunk embedding 经 gated attention 聚合；
- encoder 初始冻结；LoRA 仅在开发集事件数充足时作为次级实验。

### 8.2.4 语言敏感性分析

- 英文翻译文本模型；
- 德文原文＋多语言/德文 encoder；
- ICD/OPS-only；
- TF-IDF＋Elastic Net；
- 自由文本去除 ICD/OPS 后模型。

用于判断模型增益是来自真正语义，还是编码、模板或翻译痕迹。

## 8.3 结构化临床和病理

### 8.3.1 变量分层

- `common_core`：跨队列共同变量；
- `rich_pathology`：HANCOCK/本地扩展病理；
- `treatment_context`：仅用于描述和分层，不进入主要预测模型；
- `prohibited_future`：任何 landmark 后信息。

### 8.3.2 处理规则

- 连续变量：训练 fold median 填补，robust scaling；
- 分类变量：显式 `unknown`；
- 有序变量：有序编码＋缺失 mask；
- 极端值：按训练集 0.5%–99.5% winsorize，仅限明显录入异常；
- 所有映射表在训练 fold 拟合并保存；
- Cox 基线可增加多重插补敏感性分析，但主神经模型保留 missing mask。

## 8.4 术前实验室

HANCOCK 原论文优先选择手术前 1–3 天或手术当日的最新测量，因此主分析应使用“最后一次术前/当日实验室”，而不是泛化为术后 14 天窗口。

预设变量：

- hemoglobin；
- WBC；
- neutrophil；
- lymphocyte；
- platelet；
- creatinine/eGFR；
- sodium、potassium；
- CRP（覆盖率较低，单独处理）；
- NLR、PLR。

CRP 覆盖很低时：

- 不进入主 Extended-PRISM；
- 作为可选扩展变量；
- 报告加入 CRP 后有效样本变化和选择偏倚。

## 8.5 IHC/TMA 特权信息

### 8.5.1 token 构建

每个 token 至少包含：

- marker；
- tumor center/invasion front；
- core index；
- image embedding 或 cell density；
- QC；
- availability mask。

### 8.5.2 定量 IHC

- CD3/CD8：优先使用已验证的 positive cells/mm²；
- 其他 marker：若公开数据无可靠定量结果，使用冻结图像 encoder＋attention pooling；
- 不能把 marker 缺失编码为“阴性”；
- 对跨 marker 数值做 marker-specific log1p 和 robust scaling。

### 8.5.3 免疫辅助任务

主辅助任务：

- CD3/CD8 密度分位数回归或连续值回归；
- immune-hot vs immune-cold；
- HPV/p16 分类。

次要任务：PD-L1、MHC-I、CD163 等，只有标签质量和覆盖率通过审计后加入。

---

## 9. 模型架构

### 9.1 模态编码

统一投影到 `d_model=256`：

```text
z_common      = CommonClinicalEncoder(x_common, mask_common)
z_rich        = RichPathologyEncoder(x_rich, mask_rich)
z_lab         = LaboratoryEncoder(x_lab, mask_lab)
z_text        = TextEncoder(report_chunks)
z_wsi         = WSIEncoder(slides)
z_ihc         = IHCEncoder(marker_tokens)      # teacher only
```

每个模态输出：

- embedding；
- modality type embedding；
- availability；
- QC/quality score；
- cohort/scanner metadata 仅用于域分析，不默认作为预测特征。

### 9.2 缺失模态融合

采用 variable-set masked transformer：

- `[PATIENT]` token；
- 2 层 transformer encoder；
- 4 attention heads；
- feed-forward dimension 512；
- dropout 0.20；
- 缺失模态不提供真实内容 token；
- 额外输入 availability summary，记录哪些模态存在；
- 通过 `[PATIENT]` 输出 patient representation。

主部署模型至少要求 common-core clinical 存在。WSI、文本、实验室和 rich-pathology 可缺失。完全无临床信息的推理仅作工程测试，不作为论文中的临床使用声明。

### 9.3 Modality dropout

训练时只在 development-train 中执行：

```text
P(drop WSI)        = min(max(empirical_missing_wsi, 0.10), 0.40)
P(drop text)       = min(max(empirical_missing_text, 0.15), 0.50)
P(drop labs)       = min(max(empirical_missing_lab, 0.20), 0.60)
P(drop rich path)  = 0.20
P(mask common clinical subblock) = 0.05
```

每个 batch 至少保留 common-core clinical；20% batch 强制生成预设极端配置：

- clinical only；
- clinical＋WSI；
- clinical＋text；
- clinical＋WSI＋text；
- full available routine modalities。

### 9.4 竞争风险离散时间头

初始固定区间：

```text
(0,6], (6,12], (12,18], (18,24], (24,36], (36,48], (48,60], >60 months
```

如果训练集中某区间总事件数过少，则只允许合并相邻晚期区间。时间 bin 的最终边界在训练集冻结，不能使用 validation/test 事件分布决定。

每个区间输出：

```text
p_none(t), p_recurrence(t), p_death(t)
```

三者通过 softmax 归一化。由此计算 event-free survival 和两个 CIF。

### 9.5 主损失

#### 非蒸馏学生

```text
L_student = L_competing_risk_NLL
```

#### 蒸馏学生主配置

```text
L_student = L_competing_risk_NLL
          + λ_hazard * KL(student_event_distribution || teacher_OOF_distribution)
          + λ_immune * L_immune_aux
```

默认：

- temperature = 2.0；
- `λ_hazard ∈ {0.25, 0.5}`；
- `λ_immune ∈ {0.1, 0.2}`。

仅在 development-validation 选择一次。

#### 次要损失消融

- embedding cosine alignment；
- patient-level contrastive alignment；
- ranking loss，权重 0.05；
- pathwise/CIF-oriented auxiliary loss。

这些不能全部默认开启，以保证蒸馏增益可解释。

### 9.6 不确定性和拒绝预测

主方案：5-seed deep ensemble。

输出：

- ensemble mean CIF；
- ensemble SD；
- 预测模型之间的最大差异；
- embedding OOD score；
- WSI QC；
- modality availability。

拒绝规则在 calibration set 冻结：

1. WSI QC fail 且无可用 clinical-only fallback；
2. 必要 common-core 字段不足；
3. ensemble SD 高于 calibration set 第 95 百分位；
4. OOD distance 高于 calibration set 第 99 百分位；
5. 输入出现无法映射的新类别或单位错误。

固定时间点 conformal 风险区间作为探索性分析，需显式处理 horizon 前删失，不能简单套用普通分类 conformal。

---

## 10. 基线模型

### 10.1 临床统计基线

1. AJCC stage-only；
2. cause-specific Cox；
3. Fine-Gray subdistribution model；
4. penalized cause-specific Cox；
5. random survival forest/competing risks forest；
6. gradient boosting survival；
7. DeepHit competing risks。

### 10.2 单模态基线

- common-core clinical-only；
- rich-clinical-only；
- WSI-only；
- text-only；
- laboratory-only；
- IHC-only teacher upper-bound。

### 10.3 多模态基线

- mean/mode imputation＋concatenation MLP；
- missing indicator＋concatenation；
- late fusion；
- complete-case early fusion；
- masked transformer without modality dropout；
- masked transformer without distillation；
- Core-PRISM；
- Extended-PRISM；
- Distilled Extended-PRISM。

### 10.4 不允许作为主要基线的做法

- 删除所有被删失患者后做二分类；
- SMOTE 后训练生存模型；
- tile 作为独立患者样本；
- 测试集上选时间阈值；
- 以 Kaplan–Meier 把竞争死亡当普通删失来估计复发绝对风险。

---

## 11. 训练和超参数设定

### 11.1 训练阶段

#### Stage A：数据和 endpoint 审计

只有 `audit_status=PASS` 才能进入模型训练。

#### Stage B：预计算 embedding

- WSI foundation encoder 冻结；
- 文本 encoder 冻结；
- 保存每张 slide/chunk 的 embedding；
- 保存权重哈希和完整坐标；
- 外部队列使用完全相同 pipeline。

#### Stage C：临床和单模态基线

先证明 endpoint、删失和时间划分合理，再训练融合模型。

#### Stage D：teacher cross-fitting

在 IHC subset 产生 OOF teacher targets。

#### Stage E：学生和融合模型

在全部 development-train 患者上训练，IHC subset 使用 OOF 蒸馏，其余患者仅使用真实结局损失。

#### Stage F：校准、ensemble 和冻结

在独立 validation/calibration 集：

- 选择超参数；
- 拟合固定时间点校准；
- 冻结拒绝阈值；
- 形成五个 seed ensemble；
- 生成 freeze manifest。

### 11.2 默认超参数

| 参数 | 默认值/范围 |
|---|---|
| d_model | 256 |
| fusion layers | 2 |
| attention heads | 4 |
| fusion dropout | 0.20 |
| tabular MLP | 256→128→256 |
| optimizer | AdamW |
| learning rate, fusion/head | 1e-4 |
| learning rate, LoRA | 1e-5 |
| weight decay | 1e-4 |
| batch size | 16–32 patients |
| gradient accumulation | 视显存调整至有效 batch 32 |
| gradient clipping | 1.0 |
| max epochs | 200 |
| early stopping patience | 20 |
| scheduler | cosine decay，5 epoch warmup |
| main early stopping metric | validation recurrence-CIF IBS at 0–36 months |
| ensemble seeds | 11, 29, 47, 83, 101 |
| bootstrap | final analysis 2,000 replicates |
| mixed precision | bf16 优先，fp16 fallback |

### 11.3 超参数搜索预算

每个主要模型家族最多 30 个 Optuna trials，只搜索：

- learning rate；
- dropout；
- fusion layers 1–3；
- distillation weight；
- modality dropout scaling；
- hidden dimension 128/256。

禁止把 foundation encoder、时间起点、endpoint、外部重校准方式全部作为同一个大搜索空间。

### 11.4 过拟合控制

- 大型 encoder 冻结；
- 限制可训练参数量；
- 早停和 weight decay；
- 学习曲线；
- train/validation calibration 对照；
- patient-level bootstrap；
- 模型复杂度随事件数收缩；
- 如果复发事件较少，优先保留 Core-PRISM 和简化蒸馏，不做多头大模型微调。

---

## 12. 发表级实验设定

## 12.1 实验总表

| ID | 实验 | 数据 | 主比较 | 主要输出 | 级别 |
|---|---|---|---|---|---|
| E0 | 数据与 endpoint 审计 | 全队列 | 无 | N、事件、随访、模态覆盖、错误日志 | 必须 |
| E1 | Landmark 敏感性 | HANCOCK/local | 14d vs 30d vs surgery-origin | CIF、事件数、性能变化 | 必须 |
| E2 | 临床统计基线 | HANCOCK temporal test | Cox/Fine-Gray/RSF/DeepHit | AUC、IBS、校准 | 必须 |
| E3 | WSI encoder | HANCOCK dev/test | TITAN vs UNI-MIL vs ResNet | 性能、耗时、QC | 必须 |
| E4 | 文本增量 | HANCOCK | TF-IDF vs BERT；Core vs +text | ΔAUC、ΔIBS、文本泄漏 | 必须 |
| E5 | 模态增量 | HANCOCK | clinical→+WSI→+text→+lab | 增量价值 | 必须 |
| E6 | 融合结构 | HANCOCK | concat/late/set transformer | 完整和缺失性能 | 必须 |
| E7 | 特权蒸馏 | HANCOCK IHC subset | student vs distilled student | Δ性能、免疫一致性 | 核心 |
| E8 | 蒸馏组件消融 | HANCOCK | hazard/immune/embedding/contrastive | 贡献归因 | 必须 |
| E9 | 缺失压力测试 | HANCOCK/外部 | MCAR/MAR/真实缺失 | 性能-缺失曲线 | 核心 |
| E10 | 校准和决策曲线 | temporal/external | raw vs calibrated | slope、CITL、NB | 必须 |
| E11 | TCGA zero-shot | TCGA-HNSC | Core-PRISM vs clinical | 外部运输性 | 必须 |
| E12 | CPTAC 次级验证 | CPTAC | Core risk + omics association | CI、通路关联 | 建议 |
| E13 | Local silent validation | 独立医院 | frozen Core/Extended | 外部性能、拒绝率 | npj 强烈建议 |
| E14 | OOD/选择性预测 | 全测试集 | all vs accepted-only | risk-coverage curve | 核心 |
| E15 | 病理专家审核 | test slides | high vs low attention regions | 一致性和错误类型 | 强烈建议 |
| E16 | 工作流与推理耗时 | local/representative slides | Core vs fallback | 时间、失败率、资源 | 加分 |

## 12.2 E0：数据和 endpoint 审计

必须输出：

- 每个队列 N；
- HNSCC 和手术患者 N；
- landmark 前事件 N；
- 复发事件 N；
- 竞争死亡 N；
- 12/24/36/60 月 at-risk；
- median follow-up，使用 reverse Kaplan–Meier；
- 每种模态覆盖率；
- 每种输入组合频数；
- 每个变量缺失率；
- 时间冲突和 ID 冲突；
- external endpoint mapping 是否通过。

**停止规则：**

- 无可靠事件日期或随访时间；
- 无法区分首次治疗和复发治疗；
- 无法构建至少一个公平的跨队列输入配置；
- temporal test 事件数过少且无法通过年份扩展解决。

## 12.3 E1：landmark 实验

配置：

- M1：surgery-origin；
- M2：14-day landmark；
- M3：30-day landmark；
- M4：actual pathology-signout landmark，若可用。

比较：

- 纳入人数和早期事件排除数；
- 24/36 月 CIF；
- clinical baseline 性能；
- 模型排名是否稳定。

主论文采用预设的 30-day 或 actual-signout landmark，其余进入 Supplement。

## 12.4 E2：临床基线

使用完全相同 common-core clinical：

- cause-specific Cox；
- Fine-Gray；
- penalized Cox；
- RSF competing risk；
- DeepHit tabular。

评价：

- 24/36 月 AUC；
- 0–36 月 IBS；
- calibration-in-the-large；
- calibration slope；
- calibration curve；
- DCA。

目的不是寻找最复杂的临床模型，而是建立可信的强基线。

## 12.5 E3：WSI 模型

固定 common-core clinical 不变，比较：

1. clinical-only；
2. ResNet50-ABMIL；
3. UNI-ABMIL/CLAM；
4. TITAN slide embedding；
5. Core-PRISM 主 encoder。

报告：

- 每张 slide 推理时间；
- 每患者总推理时间；
- GPU 型号和显存；
- 失败 slide 数；
- performance gain；
- stain/scanner 分层。

## 12.6 E4：文本增量

比较：

- TF-IDF＋penalized Cox；
- ICD/OPS-only；
- BERT embedding＋survival head；
- Core-PRISM；
- Core＋text；
- Core＋text，去除 ICD/OPS；
- 英文翻译 vs 德文原文敏感性。

额外检查：

- 文本长度与 pT/pN 的相关；
- 模型是否只读取模板、手术复杂度或 ICD code；
- 结局泄漏关键词移除前后变化；
- text attribution 的人工审核。

## 12.7 E5：模态增量

按固定顺序添加：

```text
C0 = common clinical
C1 = C0 + WSI
C2 = C1 + rich pathology
C3 = C2 + text
C4 = C3 + labs
```

每一步报告 paired ΔAUC、ΔIBS、Δcalibration、Δnet benefit，以及可用样本变化。不能通过删除缺失病例让后续模型看起来更好；所有 missing-aware 模型尽量在同一患者集合比较。

## 12.8 E6：融合结构

所有模型使用相同的预计算 embedding：

- concat MLP；
- late averaging；
- complete-case concat；
- missing indicator concat；
- masked set transformer；
- masked set transformer＋modality dropout。

主要结论看：

- 自然缺失模式；
- 单模态人为缺失；
- 多模态联合缺失；
- 校准变化，而不只是 C-index。

## 12.9 E7/E8：特权蒸馏

### 主比较

- S0：学生，无 IHC；
- T：教师，部署时使用 IHC，仅作上限；
- S1：学生＋OOF hazard distillation；
- S2：学生＋immune auxiliary；
- S3：学生＋hazard distillation＋immune auxiliary，主模型；
- S4：S3＋embedding alignment；
- S5：S3＋contrastive loss。

### 公平比较要求

- S0–S5 输入完全相同；
- 训练患者完全相同；
- random seeds 相同；
- 仅蒸馏损失不同；
- IHC subset 和 non-IHC subset 分别报告；
- 对 IHC subset 的主比较使用 OOF teacher targets。

### 生物学验证

- student predicted immune score vs CD3/CD8 density；
- distilled vs non-distilled student 的相关性差异；
- 风险分数与 immune-hot/cold 的关系；
- 控制 HPV、部位和分期后的部分相关或多变量回归。

## 12.10 E9：缺失模态压力测试

### MCAR

在测试集随机移除文本、WSI、实验室：10%、30%、50%、70%。每个缺失率重复 50 次并报告均值和 95% simulation interval。

### MAR/informative missingness

缺失概率与下列变量相关：

- 年份；
- 中心；
- 分期；
- 原发部位；
- 高龄；
- WSI QC。

使用 logistic missingness generator，参数只由测试设计预设，不看模型结果调整。

### 真实缺失

- HANCOCK 自然模式；
- TCGA 整块文本/lab/IHC 缺失；
- CPTAC 模态差异；
- 独立医院流程缺失。

报告：

- performance vs availability；
- calibration vs availability；
- rejected fraction；
- 与 complete-case 患者的人群差异。

## 12.11 E10：校准和临床效用

### 内部校准

在 calibration set 对 24/36 月 predicted CIF 分别进行：

- calibration-in-the-large；
- slope recalibration；
- 必要时 monotonic isotonic calibration。

主分析优先使用简单 intercept/slope 重校准；只有存在明显非线性时才使用 isotonic。

### 外部分析

必须同时报告：

1. zero-shot raw performance；
2. zero-shot calibration；
3. 小样本更新后的 intercept-only recalibration；
4. intercept＋slope recalibration；
5. recalibrated performance。

不能只报告重校准后的结果。

### 决策曲线

24 和 36 月阈值：10%、15%、20%、25%、30%。  
在竞争风险存在时，observed status 和权重必须按 CIF/IPC weighting 处理。

## 12.12 E11–E13：外部验证

### Core-PRISM 外部输入

仅使用训练时已经定义的 common-core clinical 和 H&E WSI。外部队列缺失的 common-core 字段映射为 unknown，不能用外部结果重新定义变量集。

### 主要比较

- frozen common-core clinical baseline；
- frozen Core-PRISM；
- 若有本地增强模态，frozen Extended-PRISM；
- local recalibration 作为次级结果。

### 外部验证样本量

不要仅使用“至少 100 个事件”作为唯一依据。最终方案应使用 `pmvalsampsize` 或等价方法，根据目标校准斜率、C-statistic、净获益和 CI 宽度进行精度导向的样本量评估。100 个事件和 100 个非事件只能作为起始经验值。

## 12.13 E14：不确定性和选择性预测

按 ensemble uncertainty 从低到高逐步拒绝病例，绘制：

- risk-coverage curve；
- AUC-coverage curve；
- IBS-coverage curve；
- calibration-coverage curve。

报告 100%、95%、90%、80% coverage 时的性能。还要比较 accepted 与 rejected 人群的年龄、性别、部位、分期、中心和模态缺失，避免拒绝机制系统性排除特定亚组。

## 12.14 E15：病理和文本专家审核

### 病理图像

抽取：

- 高风险最高注意力区域；
- 低风险最高注意力区域；
- 随机对照区域；
- 错误高风险和错误低风险病例。

至少两名病理专家盲法评估：

- 肿瘤-间质界面；
- 淋巴细胞浸润；
- 坏死；
- 角化；
- PNI/LVI；
- tumor budding；
- invasive front pattern；
- artifact/spurious region。

报告 Cohen/Fleiss kappa 或 ICC，以及分歧解决流程。

### 文本

临床专家评估 attribution 片段是否：

- 与疾病负荷相关；
- 与手术复杂度相关；
- 属于模板；
- 存在潜在泄漏；
- 可被重新识别。

## 12.15 E16：工作流和耗时

至少在 50–100 名连续患者或代表性 slide 上记录：

- WSI QC 时间；
- embedding 时间；
- 文本处理时间；
- 单患者推理时间；
- GPU/CPU 资源；
- 失败率和重试次数；
- 完整输入、临床＋WSI、clinical-only 三种配置耗时。

---

## 13. 评价指标和统计分析

### 13.1 主要评价时间点

- 24 个月；
- 36 个月。

12 个月为次要，60 个月在风险集足够时报告，否则为探索性。

### 13.2 区分度

- competing-risk time-dependent AUC；
- cause-specific concordance/Uno-type concordance；
- 24/36 月 sensitivity、specificity、PPV、NPV 仅在预设阈值下次要报告。

### 13.3 总体预测误差

- recurrence CIF Brier score；
- 0–36 月 integrated Brier score；
- 0–60 月 IBS 仅在长期风险集足够时报告。

### 13.4 校准

- calibration-in-the-large；
- calibration slope；
- flexible calibration curve；
- observed CIF 使用 Aalen–Johansen/pseudo-values；
- 预测分位组 CIF 图仅用于展示，不替代连续校准曲线。

### 13.5 临床效用

- 24/36 月 decision curve；
- net benefit；
- standardized net benefit；
- 每 100 名患者可减少的不必要强化监测数；
- 阈值范围必须在分析前由临床团队确认。

### 13.6 统计推断

- 2,000 次 patient-level paired bootstrap；
- 同一 bootstrap sample 同时计算两个模型，得到差值 CI；
- 主要比较报告效应差、95% CI 和双侧 p 值；
- 层级主要检验后，其余次要比较采用 Benjamini–Hochberg FDR；
- 亚组不以交互 p>0.05 证明“公平”；
- 小亚组只做描述性分析。

### 13.7 censoring 和 competing event

- censoring weights 仅在训练/评价相应队列估计；
- IPCW 极端权重在预设百分位截断，并做无截断敏感性分析；
- 复发绝对风险使用 CIF，不使用把死亡当普通删失的 Kaplan–Meier 估计；
- 使用 R `riskRegression`/`pec` 或经过单元测试的等价实现作为金标准交叉核验。

### 13.8 模型更新

外部更新按复杂度递增：

1. 不更新；
2. intercept-only；
3. intercept＋slope；
4. 不允许在主要外部队列进行全模型重训后仍称为外部验证。

---

## 14. 亚组、公平性和域偏移

预设亚组：

- HPV/p16；
- 口腔、口咽、下咽、喉；
- pN0/pN+；
- 早期/局部晚期；
- 年龄 <65/≥65；
- 性别；
- 吸烟；
- 年份；
- 扫描仪/中心；
- 模态组合；
- 接受/未接受辅助治疗，仅作分层预后表现，不作因果解释。

每个亚组报告：

- N、事件数、竞争死亡数；
- AUC；
- IBS；
- calibration slope；
- CITL；
- 拒绝率；
- 95% CI。

域偏移分析：

- embedding MMD或Fréchet-like distance；
- scanner/stain distribution；
- clinical covariate standardized mean differences；
- endpoint incidence和censoring distribution；
- performance degradation 与 shift 指标的关联。

---

## 15. 可解释性和生物学验证

### 15.1 病理解释

- attention heatmap 只作为定位线索；
- 进行 top-k tile deletion/occlusion，验证移除高注意力区域是否显著改变风险；
- 与随机区域删除比较；
- 输出错误病例分析，不只展示成功案例。

### 15.2 文本解释

- integrated gradients/token attribution；
- section-level attention；
- 模板依赖检查；
- 去 ICD/OPS 后敏感性；
- 不公开可重新识别文本。

### 15.3 IHC 机制一致性

预设方向：

- CD3/CD8 较高可能与较低复发风险相关；
- CD163 等髓系/免疫抑制指标与高风险关联方向由文献和数据字典预先规定；
- 所有机制分析表述为关联。

统计方法：

- Spearman；
- 线性/有序回归；
- 控制 HPV、部位、pT、pN 的多变量模型；
- FDR 校正。

### 15.4 TCGA/CPTAC 分子关联

预设通路：

- T-cell inflamed/IFN-γ；
- antigen presentation/MHC-I；
- hypoxia；
- EMT；
- cell cycle；
- DNA repair；
- macrophage/myeloid inflammation。

使用 frozen risk score，不根据分子结果重新训练模型。GSVA/GSEA 和多重比较校正进入 Supplement；主文只展示预先规定的核心通路。

---

## 16. 样本量和可行性

### 16.1 数据开发阶段

数据审计后生成：

- 事件数；
- 竞争事件数；
- censoring 分布；
- 预测变量维度；
- learning curve；
- bootstrap optimism；
- 模型稳定性。

对于统计基线，使用 `pmsampsize` 或等价方法评估预测参数复杂度。深度模型不使用“10 events per variable”简单替代，应通过冻结 encoder、低维 embedding、限制可训练参数和 learning curve 控制复杂度。

### 16.2 外部验证

使用 precision-based sample size：

- 目标 calibration slope CI；
- 目标 C-statistic CI；
- 目标 net benefit CI；
- 预期 24/36 月事件率；
- censoring 率；
- predicted risk distribution。

若只有约 100 个事件，可作为初步外部验证，但校准曲线和亚组分析可能仍不精确，必须如实呈现宽 CI。

### 16.3 事件数不足时的降级规则

1. 主要 horizon 限定为 24/36 月；
2. 合并晚期时间 bins；
3. 删除次要辅助头；
4. 不做 LoRA；
5. 主模型只保留 Core-PRISM；
6. IHC 改为免疫辅助预训练，而非完整 survival teacher；
7. CPTAC 只做生物学验证；
8. 亚组仅描述。

---

## 17. 预注册、报告与复现

### 17.1 预注册时点

完成数据字典和 endpoint audit、但在运行任何 temporal test 或外部测试前，在 OSF 或机构注册平台冻结：

- 主要 endpoint；
- landmark；
- 模型配置；
- 主要比较；
- 时间点；
- 评价指标；
- 外部验证路线；
- 排除规则；
- 统计分析计划。

### 17.2 报告规范

- TRIPOD+AI；
- PROBAST+AI 自评；
- CLAIM/相关医学影像 AI 条目作为补充；
- model card；
- data statement；
- code/version manifest；
- foundation model license statement。

### 17.3 复现要求

- Docker/Apptainer；
- 固定 dependency lock；
- 每个实验一个 YAML；
- MLflow/W&B 记录；
- 原始数据不进入 Git；
- patient manifest 和 prediction 文件哈希；
- 结果表从预测文件自动生成，禁止手工录入。

---

## 18. Codex 实现规格补充

### 18.1 建议新增目录

```text
src/prism_hn/
├── landmark/
│   ├── build_landmark.py
│   └── sensitivity.py
├── endpoints/
│   ├── hancock_mapping.py
│   ├── tcga_mapping.py
│   ├── cptac_mapping.py
│   └── harmonization.py
├── distillation/
│   ├── teacher_crossfit.py
│   ├── oof_targets.py
│   └── losses.py
├── calibration/
│   ├── cif_calibration.py
│   ├── recalibration.py
│   └── conformal_exploratory.py
├── statistics/
│   ├── aalen_johansen.py
│   ├── ipcw.py
│   ├── paired_bootstrap.py
│   └── r_crosscheck.py
└── deployment/
    ├── profiles.py
    ├── abstention.py
    └── latency.py
```

### 18.2 实验配置命名

```text
configs/experiment/
├── e00_data_audit.yaml
├── e01_landmark.yaml
├── e02_clinical_baselines.yaml
├── e03_wsi_encoder.yaml
├── e04_text_increment.yaml
├── e05_modality_increment.yaml
├── e06_fusion.yaml
├── e07_distillation_main.yaml
├── e08_distillation_ablation.yaml
├── e09_missingness.yaml
├── e10_calibration_dca.yaml
├── e11_tcga_external.yaml
├── e12_cptac_biology.yaml
├── e13_local_silent.yaml
├── e14_selective_prediction.yaml
├── e15_expert_review.yaml
└── e16_latency.yaml
```

### 18.3 关键单元测试新增

1. landmark 前事件被正确排除；
2. 事件时间从 landmark 正确重置；
3. 教师 OOF target 不来自见过该患者的 teacher fold；
4. 外部数据不触发特征字典重拟合；
5. CIF 单调不减；
6. 每个时间 bin 三状态概率和为 1；
7. CIF＋event-free survival 数值一致；
8. competing risk Brier 与 R 参考实现一致；
9. Aalen–Johansen calibration observed risk 一致；
10. rejected cases 不进入 accepted-only 性能分母；
11. zero-shot 与 recalibrated 结果文件明确分开；
12. 同一预测配置在相同 seed 下可复现。

### 18.4 结果文件格式

每名患者一行：

```text
patient_id
cohort
split
model_id
model_profile
modalities_present
qc_status
abstain_flag
abstain_reason
risk_rec_12
risk_rec_24
risk_rec_36
risk_rec_60
risk_death_12
risk_death_24
risk_death_36
risk_death_60
ensemble_sd_24
ensemble_sd_36
ood_score
event_type
time_months
```

---

## 19. 论文写作提纲

## 19.1 推荐标题

**PRISM-HN: privileged immunohistochemistry distillation and missing-modality-aware multimodal learning for calibrated postoperative recurrence prediction in head and neck squamous cell carcinoma**

如果独立医院静默验证完成，可增加：

**An externally and silently validated ...**

如果只有公开数据，不建议标题使用“clinically deployed”或“real-time clinical tool”。

## 19.2 摘要结构

### Background

- HNSCC 术后复发风险异质；
- 分期不足以个体化风险；
- 现有多模态 AI 常依赖完整或昂贵模态，且忽略删失、竞争风险和校准。

### Methods

- 队列和 postoperative landmark；
- Core/Extended/Teacher 三配置；
- IHC OOF teacher distillation；
- missing-aware set transformer；
- competing-risk CIF；
- temporal and external validation；
- discrimination、calibration、DCA、missingness、uncertainty。

### Results

按固定顺序填入：

- N、事件、随访和模态覆盖；
- 主要外部 Core-PRISM vs clinical baseline；
- 蒸馏增益；
- 24/36 月校准和净获益；
- 缺失模态和拒绝率；
- 生物学一致性；
- 推理耗时。

### Conclusions

强调：

- 外部验证；
- 不完整数据下运行；
- 常规输入部署；
- IHC 只在训练期；
- 仍需前瞻性影响研究；
- 不声称治疗因果获益。

## 19.3 Introduction 提纲

### Paragraph 1：临床问题

- 复发是 HNSCC 根治性治疗失败的重要原因；
- 风险受 HPV、部位、分期、淋巴结、病理浸润和免疫微环境共同影响；
- 临床需要术后 MDT 时点的个体化绝对风险。

### Paragraph 2：现有方法不足

- 分期和常规统计模型信息有限；
- 影像/病理/多模态 AI 已显示潜力；
- 现有研究常使用二分类、删除删失、单中心随机划分、仅报告 AUC/C-index。

### Paragraph 3：现实部署障碍

- IHC、组学、手术文本和实验室并非所有中心均完整；
- 完整病例模型会损失样本并产生选择偏倚；
- 需要校准、缺失鲁棒性和拒绝机制。

### Paragraph 4：本研究贡献

明确列出四点：

1. postoperative landmark competing-risk prediction；
2. Core/Extended deployable profiles；
3. IHC privileged OOF distillation；
4. temporal/external validation with calibration, DCA, missingness and uncertainty。

最后一句给出研究目的和假设。

## 19.4 Results 提纲

### Results 1：Cohort construction and data availability

- 流程图；
- N、事件、随访；
- 模态覆盖；
- landmark 排除；
- 队列差异和 missingness pattern。

**对应 Figure 1、Table 1。**

### Results 2：Clinical and unimodal benchmarks

- clinical statistical baselines；
- WSI-only；
- text-only；
- lab-only；
- 说明 strongest baseline。

**对应 Figure 2A、Supplementary Tables。**

### Results 3：Core and Extended multimodal models

- common clinical→+WSI→+rich pathology→+text→+lab；
- 内部 temporal test；
- 模态增量和样本保持。

**对应 Figure 2B–D、Table 2。**

### Results 4：Privileged IHC distillation improves deployable prediction

- teacher upper bound；
- non-distilled vs distilled；
- OOF teacher；
- 组件消融；
- IHC subset 和全体患者。

**对应 Figure 3。**

### Results 5：External transportability and recalibration

- zero-shot TCGA/local；
- endpoint 和人群差异；
- external discrimination；
- raw calibration；
- intercept/slope recalibration；
- CPTAC 次级结果。

**对应 Figure 4、Table 2。**

### Results 6：Calibration and clinical utility

- 24/36 月 calibration curve；
- DCA；
- risk stratified CIF；
- 每 100 人避免的强化监测。

**对应 Figure 5。**

### Results 7：Robustness to missing modalities and distribution shift

- MCAR/MAR；
- 真实缺失；
- OOD；
- risk-coverage/selective prediction；
- rejected cases 特征。

**对应 Figure 6、Table 3。**

### Results 8：Pathological and biological consistency

- heatmaps and deletion test；
- pathologist review；
- CD3/CD8；
- TCGA/CPTAC pathways；
- 只陈述关联。

**对应 Figure 7。**

### Results 9：Operational feasibility

- 推理时间；
- 失败率；
- clinical-only fallback；
- 静默验证流程。

可放主文简短段落，详细结果进 Supplement。

## 19.5 Methods 提纲

1. Study design and reporting framework；
2. Clinical use case and postoperative landmark；
3. Data sources；
4. Participants and eligibility；
5. Outcome and competing event definitions；
6. Endpoint harmonization；
7. Data partition and external validation strategy；
8. WSI preprocessing and encoders；
9. Text preprocessing and encoders；
10. Clinical/pathology/laboratory preprocessing；
11. IHC/TMA representation；
12. Core, Extended and Teacher model architectures；
13. Teacher cross-fitting and privileged distillation；
14. Competing-risk objective；
15. Missing-modality training；
16. Calibration, uncertainty and abstention；
17. Baseline models；
18. Hyperparameter optimization；
19. Evaluation metrics；
20. Statistical analysis；
21. Missingness and OOD experiments；
22. Explainability and expert review；
23. Molecular pathway analysis；
24. Sample-size considerations；
25. Ethics, data availability and reproducibility。

## 19.6 Discussion 提纲

### Paragraph 1：主要发现

只总结预先规定的主要比较，不堆叠所有指标。

### Paragraph 2：为什么蒸馏有效

讨论 IHC 训练期监督如何让常规 H&E/临床表征学习免疫微环境相关信息，同时避免部署依赖 IHC。

### Paragraph 3：缺失模态和临床部署意义

强调 Core/Extended profiles、真实缺失、fallback 和拒绝预测，而不是声称“任意数据都能准确预测”。

### Paragraph 4：与既有 HNSCC 多模态研究比较

比较 endpoint、外部验证、校准、竞争风险、临床时点和输入可获得性，避免只比较 AUC 数值。

### Paragraph 5：局限性

必须包含：

- HANCOCK 单中心和翻译文本；
- 跨队列 endpoint 不完全一致；
- 回顾性治疗混杂；
- IHC 子集和事件数；
- WSI scanner/domain shift；
- attention 不是因果解释；
- 静默验证不等同于临床效益试验。

### Paragraph 6：下一步

- 前瞻性 silent validation；
- impact study；
- 与 ctDNA/影像动态监测结合；
- target-trial/causal treatment benefit 作为独立研究。

## 19.7 图表安排

### Figure 1

研究流程、landmark、队列、模态缺失矩阵。

### Figure 2

模型架构和临床/单模态/多模态内部性能。

### Figure 3

IHC teacher、OOF distillation、组件消融。

### Figure 4

外部验证 forest plot、zero-shot 和 recalibration。

### Figure 5

24/36 月 calibration 和 decision curve。

### Figure 6

missingness、OOD 和 selective prediction。

### Figure 7

病理 heatmap、删除实验、IHC 和 pathway associations。

### Table 1

队列基线、事件、随访和模态覆盖。

### Table 2

主要模型内部/外部性能和 paired differences。

### Table 3

亚组、公平性、拒绝率和缺失配置。

### Supplement

- 完整数据字典；
- endpoint mapping；
- 全部超参数；
- 训练曲线；
- 全部消融；
- landmark 敏感性；
- 详细外部重校准；
- 专家审核表；
- TRIPOD+AI；
- PROBAST+AI；
- model card；
- 软件和许可证。

---

## 20. 项目阶段、Go/No-Go 和投稿版本

### Phase 0：数据审计

**Go：**事件时间、手术时点、WSI ID 和至少 common-core clinical 可用。  
**No-Go：**无法构建时间到事件 endpoint 或跨队列输入配置。

### Phase 1：临床和单模态基线

**Go：**clinical baseline 在 temporal test 校准合理，WSI/text 至少一个显示稳定增量趋势。  
**调整：**若基线校准极差，先修 endpoint 和 landmark，不增加模型复杂度。

### Phase 2：Core-PRISM

**Go：**Core 在 temporal test 相比 clinical baseline 有稳定性能和校准提升。  
**最低可发表版本：**Core＋时间外测试＋TCGA运输性＋校准＋DCA＋代码。

### Phase 3：IHC 蒸馏

**Go：**IHC subset 事件数足够，OOF teacher 稳定。  
**降级：**只做 immune auxiliary pretraining。

### Phase 4：独立外部/静默验证

完成后才可使用“externally and silently validated”“deployment-oriented”等较强措辞。

### 投稿定位

- **npj Digital Medicine 目标版**：Core/Extended/Teacher、独立医院外部或静默验证、校准、DCA、missingness、abstention、专家审核、workflow timing。  
- **公开数据高质量版**：HANCOCK temporal＋TCGA/CPTAC、完整方法学和复现，但降低临床部署措辞。  
- **最小版**：只做随机划分＋C-index 不建议作为本项目最终交付。

---

## 21. 给 Codex 的最终执行顺序

1. 读取真实数据字典和论文 source data；
2. 生成 `data_audit.md` 和 endpoint harmonization；
3. 构建 14/30-day landmark 并输出敏感性样本量；
4. 冻结 common-core 和 rich-pathology 字段；
5. 建立时间划分；
6. 完成 cause-specific Cox/Fine-Gray 基线；
7. 预计算 WSI 和文本 embedding；
8. 完成 Core-PRISM；
9. 完成 Extended-PRISM；
10. 完成 teacher cross-fitting；
11. 训练 distilled student；
12. 在 validation/calibration 集冻结校准和拒绝规则；
13. 一次性运行 temporal test；
14. 冻结模型 manifest；
15. 一次性运行 TCGA/CPTAC/独立医院；
16. 运行缺失、OOD、解释和生物学实验；
17. 自动生成论文图表、TRIPOD+AI、PROBAST+AI 和 model card。

---

## 22. 参考文献和方法依据（建议纳入论文）

1. Dörrich M, Balk M, Heusinger T, et al. A multimodal dataset for precision oncology in head and neck cancer. *Nature Communications*. 2025;16:7163. doi:10.1038/s41467-025-62386-6.
2. Tian R, Hou F, Zhang H, et al. Multimodal fusion model for prognostic prediction and radiotherapy response assessment in head and neck squamous cell carcinoma. *npj Digital Medicine*. 2025;8:302. doi:10.1038/s41746-025-01712-0.
3. Ding T, Wagner SJ, Song AH, et al. A multimodal whole-slide foundation model for pathology. *Nature Medicine*. 2025;31:3749–3761. doi:10.1038/s41591-025-03982-3.
4. Xu H, Usuyama N, Bagga J, et al. A whole-slide foundation model for digital pathology from real-world data. *Nature*. 2024;630:181–188. doi:10.1038/s41586-024-07441-w.
5. Chen RJ, Ding T, Lu MY, et al. Towards a general-purpose foundation model for computational pathology. *Nature Medicine*. 2024;30:850–862. doi:10.1038/s41591-024-02857-3.
6. Lu MY, Williamson DFK, Chen TY, et al. Data-efficient and weakly supervised computational pathology on whole-slide images. *Nature Biomedical Engineering*. 2021;5:555–570. doi:10.1038/s41551-020-00682-w.
7. Lee C, Zame WR, Yoon J, van der Schaar M. DeepHit: a deep learning approach to survival analysis with competing risks. *AAAI*. 2018.
8. Liu J, Lichtenberg T, Hoadley KA, et al. An integrated TCGA pan-cancer clinical data resource to drive high-quality survival outcome analytics. *Cell*. 2018;173:400–416.e11. doi:10.1016/j.cell.2018.02.052.
9. Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. *BMJ*. 2024;385:e078378. doi:10.1136/bmj-2023-078378.
10. Moons KGM, Damen JAA, Kaul T, et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. *BMJ*. 2025;388:e082505. doi:10.1136/bmj-2024-082505.
11. Riley RD, Snell KIE, Archer L, et al. Evaluation of clinical prediction models (part 3): calculating the sample size required for an external validation study. *BMJ*. 2024;384:e074821. doi:10.1136/bmj-2023-074821.
12. Riley RD, Ensor J, Snell KIE, et al. Calculating the sample size required for developing a clinical prediction model. *BMJ*. 2020;368:m441. doi:10.1136/bmj.m441.
13. Wolbers M, Koller MT, Witteman JCM, Steyerberg EW. Prognostic models with competing risks: methods and application to coronary risk prediction. *Epidemiology*. 2009.
14. Austin PC, Fine JP. Practical recommendations for reporting Fine-Gray model analyses for competing risk data. *Statistics in Medicine*. 2017.
15. van Calster B, McLernon DJ, van Smeden M, Wynants L, Steyerberg EW. Calibration: the Achilles heel of predictive analytics. *BMC Medicine*. 2019.

---

## 23. 最终判断

该方案最有价值的部分不是简单增加更多模态，而是形成一条清晰、可验证的临床和方法学逻辑：

1. 在术后信息真正可用的 landmark 预测绝对复发风险；
2. 用 Core-PRISM 保证跨队列验证公平；
3. 用 Extended-PRISM 检验文本和实验室增量；
4. 用交叉拟合 IHC teacher 提供训练期特权监督；
5. 用 competing-risk CIF、校准、DCA 和外部验证评价临床有效性；
6. 用缺失压力测试、拒绝预测和工作流耗时证明部署可行性。

只要 endpoint audit 通过，并能完成时间外测试和至少一个可信的外部验证，本方案具备发表潜力；若再加入独立医院静默验证和专家审核，才真正接近 npj Digital Medicine 的目标强度。
