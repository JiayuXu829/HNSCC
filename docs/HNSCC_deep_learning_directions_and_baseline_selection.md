# HNSCC 深度学习研究方向、任务方法图谱与文献 Baseline 选择

> 文档日期：2026-08-12  
> 适用项目：TRUST-HN 头颈鳞癌可信多模态预后研究  
> 目标期刊语境：`npj Digital Medicine` 及同等级高影响力数字医学、医学影像、肿瘤学期刊

---

## 1. 文档目的与范围

本文件回答三个问题：

1. 在 `npj Digital Medicine` 等高影响力医学期刊中，HNSCC（head and neck squamous cell carcinoma，头颈鳞状细胞癌）相关深度学习研究主要在做哪些任务；
2. 各任务常使用哪些数据模态、网络结构、融合方式和验证设计；
3. 对当前 TRUST-HN 项目，应该选择哪个可执行、可公平比较、又具有明确文献来源的 baseline，并如何把现有结果映射到该 baseline 上验证。

### 1.1 “一区”口径说明

期刊分区会随年份以及 JCR、CAS 等口径变化。本文件不把“一区”当作永久标签，而采用以下分层：

- **核心高影响力证据**：`npj Digital Medicine`、`Nature Communications` 等数字医学或综合医学高影响力期刊中的直接相关研究；
- **高任务相关证据**：HNSCC 队列、任务和方法高度相关的医学影像、病理、肿瘤信息学研究；
- **方法学补充证据**：来自邻近癌种、可迁移到 HNSCC 的缺失模态、融合或生存建模方法；
- **预印本**：仅作为趋势参考，不能与正式同行评议论文等同。

在正式投稿前，应按照投稿当年的最新 JCR/CAS 分区再次核查期刊等级。

### 1.2 纳入边界

本文件重点纳入：

- 疾病为 HNSCC、口咽鳞癌、口腔鳞癌或明确的头颈癌队列；
- 使用 CT、PET/CT、MRI、WSI、TMA、转录组、基因组、临床资料等一种或多种模态；
- 至少使用深度神经网络提取表征，或以深度生存模型作为主要比较方法；
- 任务包括生存、复发、转移、治疗获益、HPV 状态或病理形态表型预测；
- 对外部验证、缺失模态、分布偏移、校准和可信度特别关注。

### 1.3 必须区分的三类“生存预测”

文献中常把不同终点统称为 survival prediction，但其统计含义并不相同：

| 类型 | 标签形式 | 是否利用随访时间 | 是否正确处理删失 | 常用指标 |
|---|---|---:|---:|---|
| 完整 time-to-event 生存分析 | `(time, event)` | 是 | 是 | Harrell/Uno C-index、IPCW Brier、time-dependent AUC、校准 |
| 固定时间结局分类 | 例如“2 年内死亡/复发” | 部分 | 通常不完整，需谨慎处理未满随访者 | AUROC、AUPRC、灵敏度、特异度 |
| 生存状态分类 | 最后随访时 alive/dead | 否或很弱 | 否 | accuracy、AUROC、F1 |

因此，固定 2 年 OS 分类或 alive/dead 分类不能直接称为完整删失感知生存模型，也不能与 Cox、DeepSurv 等 time-to-event 模型不加说明地横向比较。

---

## 2. 执行摘要

### 2.1 HNSCC 深度学习的主要研究方向

目前可概括为七类：

1. **治疗前总体生存、无病生存和风险分层**：临床、CT/PET、病理和组学的单模态或多模态生存预测；
2. **复发、远处转移和局部区域控制**：通常使用固定时间分类、多任务学习或竞争风险相关建模；
3. **放疗/术后放疗获益与治疗反应**：在预后模型基础上探索治疗异质性或治疗获益，但容易受到治疗选择偏倚影响；
4. **HPV/p16 和分子表型预测**：利用 PET/CT、病理和临床资料推断 HPV 状态或其他生物标志物；
5. **淋巴结、分期和病理诊断**：影像检测、分割、分类及病理弱监督学习；
6. **肿瘤形态异质性和微环境表型**：细胞分割、自编码器、聚类、MIL 与生存模型结合；
7. **可信多模态 AI**：处理模态缺失、分布偏移、捷径学习、不确定性、校准、回退和拒绝预测。

### 2.2 最适合当前项目的主文献 baseline

推荐采用 Tian 等在 `npj Digital Medicine` 2025 年 HNSCC 多模态预后研究中的核心融合范式：

> **先分别训练单模态风险编码器，再把临床、CT 和病理的风险分数输入多变量 Cox 模型进行 score-level late fusion。**

当前项目已经实现了这一思想的轻量、严格交叉拟合版本：

> **C3：cross-fitted late-fusion stacking of clinical and modality Cox models**

建议在论文和代码说明中将 C3 命名为：

- `Literature-SCF`：literature-derived score-level Cox fusion；或
- `MM-Cox-SF`：multimodal Cox score fusion。

C3 是对 Tian 论文**融合层思想**的适配复现，不是对其 3D CT 网络和 WSI attention-MIL 编码器的完整复现。

### 2.3 当前结果给出的核心结论

- RADCURE：C3 与直接融合 B5、残差融合 B6 接近；
- HANCOCK：C3 的排序判别略高于 B5/B6，但配对区间仍包含零；
- GSE65858：C3 在主比较模型中获得最好的 Uno C-index 和 24 月 AUC；若纳入 post hoc 的 C2，C2 的 AUC 略高，但 Brier 和校准严重恶化；
- GSE41613：C3 与其他融合方法相近，非线性 C1/C2 在该敏感性队列上判别更高；
- 这说明**融合可提高排序，但不保证跨平台绝对风险可靠**；
- TRUST-HN 的论文价值不应只表述为提高 C-index，而应突出 missing modality、OOD、shortcut audit、校准以及患者级 fallback/abstention。

---

## 3. HNSCC 深度学习研究方向总览

## 3.1 总体生存、无病生存和风险分层

### 临床问题

- 治疗前识别高风险患者；
- 预测 OS、DFS、PFS 或疾病特异性生存；
- 支持临床试验分层、随访强度和多学科讨论；
- 评估附加影像、病理或组学是否提供超越临床变量的增量信息。

### 常见模态

- 临床：年龄、性别、T/N/M 分期、原发部位、HPV/p16、吸烟、ECOG、治疗方式；
- CT/PET：原始体积、肿瘤 ROI、放射组学、深度影像表征；
- 病理：H&E WSI、组织芯片、细胞密度和微环境特征；
- 组学：RNA-seq、表达芯片、DNA 甲基化、突变/CNV；
- 实验室：血常规、生化指标等。

### 常见方法

- 2D/3D ResNet、DenseNet、Swin Transformer；
- 预训练 CT foundation model 或视觉-语言模型作为 frozen/fine-tuned encoder；
- WSI 的 attention-MIL、CLAM、Transformer-MIL；
- Cox PH、elastic-net Cox、Random Survival Forest、GBSA、XGBoost-Cox；
- DeepSurv、DeepCox、离散时间 hazard 网络；
- risk-score late fusion、stacking、early concatenation。

### 主要研究缺口

- 深度影像模型并不稳定优于强临床模型或 clinical + tumor volume；
- 高维模型易学习肿瘤体积、扫描协议或中心来源等捷径；
- 许多工作只报告 C-index/AUC，而不报告绝对风险校准；
- 多模态完整病例分析容易引入选择偏倚；
- 外部队列中的模态缺失和跨平台偏移常未被显式处理。

---

## 3.2 局部复发、远处转移和疾病控制

### 典型任务

- 2 年局部区域控制（LRC）；
- 2 年远处转移（DM）；
- 复发风险或无复发生存；
- 多任务联合预测 OS、LR/LRC 和 DM。

### 典型方法

- 共享 CT/PET 编码器加多个分类头；
- pseudo-volumetric 2.5D CNN；
- CNN + self-attention；
- 多任务 logistic 网络；
- 影像深度特征与临床变量拼接；
- foundation-model embedding + MIL Transformer。

### 方法学注意事项

- 如果终点被转化为 2 年二分类，必须说明对 2 年前删失患者如何处理；
- 若多个终点共享编码器，需要防止把同一患者或同一中心泄漏到训练和测试；
- 多任务学习的收益应与独立单任务模型比较；
- 复发和死亡存在竞争事件时，单纯二分类或普通 Cox 可能不足。

---

## 3.3 治疗反应与治疗获益评估

### 典型任务

- 放疗或术后放疗获益分层；
- 放化疗响应预测；
- 局部控制概率预测；
- 从预后风险进一步探索治疗异质性。

### 常见方法

- 多模态预后风险评分 + 治疗变量交互项；
- 倾向评分或加权后的风险分层；
- 深度表征结合 Cox/分类模型；
- treatment-aware network 或 causal representation learning。

### 主要风险

观察性队列中的“治疗获益”不能仅凭治疗组内外预测差异证明。必须尽可能考虑：

- 治疗指征混杂；
- immortal-time bias；
- stage、切缘、淋巴结和风险因素不平衡；
- treatment × biomarker 交互是否经过独立验证；
- 模型是 prognostic 还是真正 predictive。

因此，当前项目可以把治疗获益作为后续研究方向，不宜在没有严格因果设计时作为主张中心。

---

## 3.4 HPV/p16 与分子表型预测

### 临床任务

- 从 FDG-PET/CT、CT 或病理图像预测 HPV/p16 状态；
- 识别与病毒相关、免疫相关或分子亚型相关的影像表型；
- 在病理或影像信息不完整时提供辅助筛查。

### 方法

- PET/CT CNN 表征；
- 临床变量与深度影像特征拼接；
- logistic regression、MLP 或集成分类器；
- 多中心训练与外部分类验证。

### 与当前项目的关系

HPV 状态预测是**生物标志物分类任务**，不属于生存 baseline。但 HPV/p16 是重要的临床锚点和分层变量，可用于：

- 临床 Cox baseline；
- 亚组性能和 worst-group audit；
- 检查模型是否只学习口咽部位或中心分布；
- 设计 targeted distribution shift。

---

## 3.5 淋巴结、分期、肿瘤检测与分割

### 常见任务

- 原发灶/GTV 自动分割；
- 淋巴结转移检测和分类；
- T/N 分期预测；
- 病理切片肿瘤区域检测、分级和组织学分类。

### 常见方法

- 3D U-Net、nnU-Net；
- 2D/3D CNN 检测器；
- vision transformer；
- 弱监督 WSI MIL；
- 多尺度图像网络。

### 与预后研究的衔接

这类任务可产生：

- 肿瘤体积、形状和位置；
- 淋巴结负荷；
- 病理肿瘤比例和微环境表型；
- 深度 embedding。

但预后论文必须检验这些特征是否提供超越分期和肿瘤体积的增量信息，不能把分割精度直接等同于预后价值。

---

## 3.6 病理形态异质性和肿瘤微环境

### 典型任务

- 从 WSI/TMA 提取形态或细胞空间特征；
- 量化肿瘤细胞形态多样性；
- 识别免疫、间质、坏死和肿瘤区域；
- 将形态异质性与生存相关联。

### 常见方法

- StarDist 等细胞核检测/分割；
- convolutional autoencoder 学习细胞形态 embedding；
- 聚类和异质性指数；
- ResNet、UNI、TITAN 等 patch encoder；
- CLAM/attention-MIL/Transformer-MIL；
- 最终使用 Cox、RSF 或分类模型预测结局。

### 方法学问题

- 病理切片多、患者少，必须按患者划分；
- tile 级随机划分会产生严重泄漏；
- 扫描仪、染色批次和组织来源可成为中心捷径；
- WSI foundation model 更强并不意味着生存预测一定更好；
- 热图解释只能说明 attention/贡献分布，不能证明因果机制。

---

## 3.7 缺失模态、OOD、捷径学习与可信 AI

这是最适合 TRUST-HN 的增量方向。

### 临床现实

- 并非每位患者都有完整 CT、WSI、RNA、血液或 HPV 信息；
- 不同医院的采集设备、预处理和人群构成不同；
- 单一模态可能在某些患者中质量不足或完全缺失；
- 一个在平均意义上表现好的融合模型，可能在特定亚组严重失准。

### 方法方向

- modality dropout；
- masked/self-attention fusion；
- mixture-of-experts；
- 单模态教师—学生蒸馏；
- missingness indicator；
- late fusion 和可用模态组合；
- OOD score、ensemble uncertainty；
- conformal prediction；
- selective prediction、fallback 和 abstention；
- negative control、permuted modality、shortcut audit。

### 当前证据缺口

HNSCC 多模态论文通常集中于完整病例上的平均性能，较少同时完成：

1. 缺失模态压力测试；
2. 跨机构/跨平台外部验证；
3. 绝对风险校准；
4. 负对照和捷径检查；
5. 患者级回退或拒绝；
6. coverage–performance 曲线。

这正是 TRUST-HN 相对既有工作最清晰的研究空间。

---

## 4. 按模态总结深度学习方法

## 4.1 CT、PET/CT 和 MRI

| 方法类别 | 输入 | 代表结构 | 优点 | 主要风险 |
|---|---|---|---|---|
| 2D CNN | 单切片或关键切片 | ResNet、DenseNet | 资源较低、易训练 | 丢失三维上下文，切片选择偏倚 |
| 2.5D/pseudo-volume | 相邻切片或多视图 | CNN + attention | 兼顾资源和空间信息 | 仍不是完整 3D 表征 |
| 3D CNN | 肿瘤 ROI 或全体积 | 3D ResNet、3D DenseNet | 保留体积上下文 | 样本效率低，易过拟合中心协议 |
| ViT/Swin | 2D/3D patch | ViT、SwinViT | 长程依赖和预训练能力 | 小样本时不稳定，算力较高 |
| Foundation encoder + MIL | 多个体积/切块 embedding | CT-FM、视觉-语言模型、MIL Transformer | 降低从头训练需求 | 预训练域差异、embedding 捷径 |
| Radiomics + DL | ROI 放射组学 + CNN feature | Cox/RSF/GBSA/stacking | 易解释并可做体积审计 | 特征高度相关、扫描协议敏感 |

建议至少保留 `clinical-only`、`tumor-volume-only/clinical+volume`、`radiomics-only` 和 `clinical+radiomics` 对照，防止把深度模型收益误认为复杂视觉表征的独有贡献。

## 4.2 WSI 和 TMA

典型流程：

1. 组织检测和背景去除；
2. 将 WSI 切成 tile；
3. 用 ImageNet ResNet 或病理 foundation model 提取 tile embedding；
4. 用 mean/max pooling、attention-MIL、CLAM 或 Transformer 聚合；
5. 输出分类概率、风险分数或 Cox hazard；
6. 在患者层面评估。

更公平的比较应固定：

- 同样的患者划分；
- 同样的 tile 数与采样策略；
- 相同的 survival head；
- 是否冻结 encoder；
- 是否使用外部预训练；
- 是否进行 stain normalization。

## 4.3 转录组和其他组学

常见策略：

- 高变基因筛选 + elastic-net Cox；
- pathway score + Cox/RSF；
- MLP/autoencoder 降维 + Cox head；
- DeepSurv；
- 图网络或 pathway-aware network；
- 与临床或病理 embedding 融合。

HNSCC 跨队列组学验证的关键不是把训练集拟合得更复杂，而是处理：

- RNA-seq 与表达芯片的平台差异；
- 探针—基因映射；
- 批次效应；
- 缺失基因；
- 尺度和归一化变化；
- 队列生物学构成差异。

当前 TCGA-HNSC → GSE65858/GSE41613 结果已经表明，判别和绝对校准可在跨平台时明显分离。

## 4.4 临床结构化数据

深度 MLP 未必优于：

- Cox PH；
- elastic-net Cox；
- Random Survival Forest；
- GBSA；
- XGBoost-Cox。

在患者数有限、临床变量较少的场景，传统生存模型通常是更稳定、更容易校准的强 baseline。深度模型必须证明增量价值，而不能只与 Kaplan–Meier 或单变量 Cox 比较。

---

## 5. 多模态融合方法图谱

| 融合层级 | 实现方式 | 优点 | 局限 | 对当前项目的适配度 |
|---|---|---|---|---|
| Early fusion | 原始/预提取特征直接拼接 | 简单、端到端优化方便 | 维度失衡、缺失模态困难、易过拟合 | 已有 B5/C1/C2/C4 |
| Intermediate fusion | 各 encoder embedding 进入共享注意力/Transformer | 可学习跨模态交互 | 需要较大完整多模态样本 | 当前资源下不优先 |
| Late probability fusion | 平均或加权单模态概率 | 易处理不同 encoder | 概率校准和时间维度可能不一致 | 中等 |
| Score-level Cox fusion | 单模态风险分数进入多变量 Cox | 轻量、可解释、与生存数据兼容 | 依赖单模态分数质量；校准仍可能漂移 | **最高，C3** |
| Stacking | OOF 单模态预测训练二层 learner | 防止二层训练泄漏，可扩展 | 流程必须严格 cross-fit | **最高，C3/B6** |
| Residual fusion | 临床风险为锚，附加模态仅学习增量残差 | 强调临床增量价值 | 需要定义和验证残差机制 | **当前主方法 B6** |
| Missing-aware fusion | mask、modality dropout、MoE 或显式缺失指标 | 适合现实不完整数据 | 训练组合多，小样本易不稳定 | C4/B7 及后续扩展 |
| Reliability-gated fusion | 根据 OOD/不确定性选择融合、回退或拒绝 | 贴近部署安全 | 需要独立冻结阈值和 coverage 报告 | **当前主方法 B7** |

---

## 6. 代表性研究与可借鉴点

> 注：表中“深度学习”可能位于编码器层，而最终生存头可能是 Cox、RSF 等传统模型。不能因为前端使用 CNN 就把整个流程称为端到端深度生存网络。

| 研究 | 期刊/年份 | 癌种与队列 | 任务 | 模态 | 主要方法 | 验证特点 | 对本项目的启示 |
|---|---|---|---|---|---|---|---|
| Tian et al., *Multimodal fusion model for prognostic prediction and radiotherapy response assessment in HNSCC* | npj Digital Medicine, 2025 | HNSCC，多中心，总样本约 1087 | OS、DFS、术后放疗获益探索 | 临床 + CT + H&E WSI | CT：3D ResNet50；WSI：ResNet50 tile encoder + attention-MIL；单模态风险分数进入多变量 Cox | 多个外部测试集；多模态外部 OS C-index 约 0.71–0.72 | **主文献 baseline**：复现 score-level Cox fusion，而非必须重训全部大模型 |
| *Multi-institutional Prognostic Modeling in Head and Neck Cancer: Evaluating Impact and Generalizability of Deep Learning and Radiomics* | 高任务相关医学影像研究，2023 | RADCURE 开发/内部测试约 2552，外部约 873 | OS、局部复发、远处转移等；包含固定时间结局/多任务成分 | 临床 EMR + 治疗前 CT/GTV | clinical、radiomics、2D/3D CNN、多任务 logistic 及融合 | 多机构外部验证；clinical + tumor volume 是强模型，内部 AUROC 约 0.823、C-index 约 0.801 | 复杂 CNN 不一定胜过 clinical + volume；必须保留体积强对照 |
| *A multimodal dataset for precision oncology in head and neck cancer*（HANCOCK） | Nature Communications, 2025 | 763 例头颈癌 | 多种临床结局 benchmark | 临床、血液、病理、WSI、TMA | 结构化数据 early fusion + RF；WSI/TMA 使用 CLAM，ResNet18 或 UNI 编码 | ID/OOD、解剖部位留出 | 是重要数据与 OOD 参考；其部分“survival”任务为生存状态分类，不等同完整删失生存 |
| *Improved HPV status prediction in oropharyngeal cancer by combining clinical data and deep learning features in a multimodal model* | npj Digital Medicine, 2023 | 口咽癌，850 例、四队列 | HPV 状态分类 | FDG-PET + 临床 | 深度 PET 特征 + 临床融合分类 | 多队列验证 | 属于分子表型方向；不能作为 OS baseline，但可支持 HPV 分层和 shortcut audit |
| *Cross-institutional outcome prediction for head and neck cancer patients using self-attention neural networks* | 同行评议研究，2022 | 头颈癌跨机构队列 | OS/LR/DM，主要为固定结局预测 | PET/CT + 临床 | pseudo-volumetric CNN + self-attention | 跨机构评估 | 可借鉴多任务和跨机构设计，但需区分固定时间分类与删失生存 |
| *End-to-end prediction of clinical outcomes in HNSCC with foundation model-based MIL* | medRxiv/PMC 预印本，约 2025 | RADCURE | 2 年 OS、LRC、DM | CT | CT-FM、BioMedCLIP、SwinViT embedding + MIL Transformer | 基于公开 RADCURE | 代表 foundation model + MIL 趋势；预印本证据等级较低，不宜作为唯一主 baseline |
| *A stacking ensemble framework integrating radiomics and deep learning for prognostic prediction in head and neck cancer* | 同行评议研究，2025 | 头颈癌 PET/CT 队列 | 预后预测 | PET/CT radiomics + 3D DenseNet121 | Cox、SVM、RSF、DeepCox、DeepSurv + stacking | 报告外部测试 | 支持 stacking；若性能异常高，应重点核查患者划分、特征选择和二层模型是否完全 OOF |
| *Multimodal AI-based pathogenomics improves survival prediction in oral squamous cell carcinoma* | 高相关肿瘤信息学研究，2024 | TCGA 口腔鳞癌 | 生存预测 | 临床 + 病理 + 基因组 | RSF、GBSA、Cox、FastSVM、DeepSurv | TCGA 内部评估 | 传统 RSF 可优于 DeepSurv；不能预设深度生存模型必胜 |
| *Integrative Models of Histopathological Image Features and Omics Data Predict Survival in HNSCC* | 同行评议研究，2020 | TCGA-HNSCC | 生存预测 | 病理图像特征 + omics | 图像特征与 omics 融合，Random Forest | TCGA 内部分析 | 属于早期融合参考；不应误称端到端深度生存研究 |
| *Morphological diversity of cancer cells predicts prognosis across tumor types* | JNCI, 2024 | 泛癌，包含 HNSCC | 生存预测 | H&E 细胞形态 | StarDist + convolutional autoencoder + 形态异质性 + RSF | 跨癌种分析 | 说明“深度表征 + 可解释形态统计 + 传统生存模型”是有效路线 |
| *Handling missing modalities in multimodal survival prediction for NSCLC* | npj Digital Medicine, 2026 | **NSCLC，非 HNSCC**，约 179 例 | 生存预测 | CT + WSI + 临床 | 预训练编码器 + NAIM masked self-attention/Transformer + 生存头 | 5 折交叉验证，独立外部验证有限 | 仅作为 missing-aware 方法学参考，不能当作 HNSCC 实证证据 |

### 6.1 对代表性研究的总体判断

1. **高影响力 HNSCC 多模态研究的融合层未必复杂。** Tian 等最终采用风险分数级 Cox 融合，说明高质量论文的关键不仅是跨模态 Transformer，还包括临床问题、多中心验证和结果解释。
2. **强临床 baseline 非常重要。** RADCURE 研究提示 clinical + tumor volume 可超过复杂 CT CNN。
3. **深度表征不等于深度生存头。** WSI/CT 可用 CNN 编码，但最终使用 Cox/RSF 完成生存建模。
4. **更多模态不保证更可信。** 跨中心、跨平台时，融合可能提高排序同时损害绝对风险校准。
5. **HNSCC 中 missing-aware、fallback 和 abstention 仍相对不足。** 邻近癌种已开始使用 masked attention，但样本量和外部验证仍有限。

---

## 7. Baseline 候选比较

| 候选 | 文献依据 | 是否直接 HNSCC | 是否为删失生存 | 当前数据可执行性 | 主要用途 | 推荐级别 |
|---|---|---:|---:|---:|---|---:|
| Tian 完整 CT+WSI 模型 | npj Digital Medicine 2025 | 是 | 是 | 低：需要原始 CT、WSI、分割与大规模训练 | 完整架构复现 | 不作为当前主 baseline |
| **Tian 式 score-level Cox fusion（C3）** | npj Digital Medicine 2025 | 是 | 是 | **高：已有临床和附加模态风险模型** | 主文献 baseline | **首选** |
| Clinical + tumor volume | RADCURE 多机构研究 | 是 | 研究中含多类终点 | RADCURE 高；其他队列不一定有同构体积 | 影像增量价值强对照 | 必需的任务特异对照 |
| DeepSurv/DeepCox | 多篇 HNSCC/OSCC 研究 | 是 | 是 | 中等 | 检验非线性 survival head | 次要方法 baseline |
| GBSA/XGBoost-Cox（C1/C2） | 通用生存与 HNSCC 相关比较 | 间接/直接均有 | 是 | 高，已完成 | 非线性结构化数据强对照 | 探索性强对照 |
| HANCOCK CLAM/UNI | Nature Communications 2025 | 是 | 原 benchmark 部分为状态分类 | 低至中：需 WSI | WSI/OOD 参考 | 非统一生存 baseline |
| NSCLC missing-aware Transformer | npj Digital Medicine 2026 | 否 | 是 | 低：需 CT+WSI 完整 encoder | 方法学对照 | 不作为主文献 baseline |

### 7.1 推荐决策

采用双层 baseline 体系：

#### 主文献 baseline

**C3 / Literature-SCF：cross-fitted score-level Cox fusion**

- 直接对应 HNSCC `npj Digital Medicine` 文献的融合逻辑；
- 可在 RADCURE、HANCOCK、TCGA-HNSC → GEO 的不同附加模态上复用；
- 不要求重新下载和训练原始 CT/WSI 大模型；
- 能与 B5 直接拼接、B6 残差融合和 B7 可靠性门控公平比较；
- 风险分数维度低，便于解释和诊断跨队列校准失败。

#### 必需强对照

- B2：clinical elastic-net Cox；
- B5：clinical + modality direct-concatenation elastic-net Cox；
- RADCURE 中的 clinical + tumor volume/shape 强对照；
- C1：GBSA；
- C2：XGBoost-Cox；
- B0/B1/B3 作为基础统计和机器学习参照；
- M0/N0 作为缺失模式和置换模态负对照，而非竞争预测模型。

---

## 8. C3 文献 Baseline 的严格实现

当前实现位置：

```text
trust-hn/src/trust_hn/phase7/models.py
```

配置位置：

```text
trust-hn/configs/phase7_exploratory_benchmarks.json
```

### 8.1 训练流程

对每一个 development study：

1. 将训练数据按事件状态分层进行 5 折划分；
2. 每折使用 4/5 数据训练 clinical elastic-net Cox；
3. 对留出 1/5 产生 clinical OOF risk score；
4. 同样训练 modality elastic-net Cox，产生 modality OOF risk score；
5. 合并所有折后得到每位训练患者的两个、且不来自自身训练过程的 OOF 分数；
6. 用 `[clinical_oof, modality_oof]` 拟合带轻度正则的二层 Cox PH；
7. 一级 clinical 和 modality Cox 在完整训练集上重训；
8. 对内部锁定测试集或外部队列生成两个一级风险分数；
9. 把两个分数输入已锁定的二层 Cox，输出排序分数和 24 月绝对风险。

示意：

```text
clinical features ──> cross-fitted Cox ──> clinical risk score ┐
                                                               ├─> meta Cox ─> survival score/risk
modality features ──> cross-fitted Cox ──> modality risk score ┘
```

### 8.2 为什么必须使用 OOF 分数

如果先在全部训练患者上拟合一级模型，再用同一批患者的 in-sample 风险分数训练二层 Cox，二层模型会利用过度乐观的一级预测，形成 stacking leakage。当前 C3 的 cross-fitting 避免了这一问题。

### 8.3 与 Tian 原论文的相同与不同

| 组成 | Tian 等 | 当前 C3 |
|---|---|---|
| 临床编码 | 临床变量/临床风险 | elastic-net Cox 风险分数 |
| CT 编码 | 3D ResNet50 | RADCURE 预提取 radiomics；不同队列为其可用附加模态 |
| WSI 编码 | ResNet50 tile + attention-MIL | 不直接复现；HANCOCK 使用已有结构化/预提取模态 |
| 融合层 | 多变量 Cox 风险融合 | 二层 Cox 风险融合 |
| 防泄漏 | 需依据原文流程判断 | 明确 5 折 cross-fitting/OOF 预测 |
| 外部适配 | 固定模态模型外部测试 | 各 development study 锁定后对应外部测试 |

因此推荐在论文中写为：

> We implemented a literature-derived, cross-fitted score-level Cox fusion comparator inspired by the multimodal risk-fusion strategy of Tian et al.

而不要写成：

> We fully reproduced the Tian et al. CT–WSI model.

---

## 9. 当前项目任务、模型与结果映射

## 9.1 冻结任务

- 主要时间点：24 个月 OS；
- horizon：`730.5` 天；
- 同时保留完整 time-to-event 评价；
- development studies：RADCURE、HANCOCK、TCGA-HNSC；
- 外部/锁定评价：RADCURE、HANCOCK、GSE65858；
- GSE41613：HPV 阴性 OSCC 敏感性队列，不冒充通用 HNSCC 外部验证。

## 9.2 当前模型体系

| 编号 | 模型 | 角色 |
|---|---|---|
| B0 | Kaplan–Meier constant-risk | 最低基线 |
| B1 | Clinical Cox PH | 标准临床统计模型 |
| B2 | Clinical elastic-net Cox | 主要 clinical-only baseline |
| B3 | Clinical Random Survival Forest | 非线性临床 baseline |
| B4 | Additional-modality-only elastic-net Cox | 检验附加模态独立信息 |
| B5 | Clinical + modality direct-concatenation elastic-net Cox | 标准 early fusion |
| B6 | TRUST-HN stacked residual fusion | 当前主要融合方法 |
| B7 | TRUST-HN reliability gate | 回退/拒绝与选择性预测 |
| C1 | GBSA direct fusion | 探索性非线性生存模型 |
| C2 | XGBoost-Cox direct fusion | 探索性非线性生存模型 |
| **C3** | **Cross-fitted late-fusion Cox stacking** | **主文献 baseline** |
| C4 | Missing-aware direct fusion + indicators | 显式缺失指标对照 |
| M0 | Missingness-only Cox | 缺失模式审计 |
| N0 | Permuted-modality negative control | 捷径/无效模态负对照 |

> Phase 7 的 C1–C4 在配置中明确标记为 `post hoc exploratory benchmark`。论文中必须保留该治理标签，不能将其追溯性描述为预先锁定的 primary comparison。

---

## 10. 现有结果：C3 与主要模型的验证

### 10.1 RADCURE 锁定测试集

`n=626`，死亡事件 `110`。

| 模型 | IPCW Brier ↓ | Uno C ↑ | 24 月 AUC ↑ | Coverage |
|---|---:|---:|---:|---:|
| B2 clinical-only | 0.1091 | 0.7078 | 0.7145 | 1.000 |
| B5 direct fusion | **0.0974** | **0.7792** | **0.7879** | 1.000 |
| B6 residual fusion | 0.0980 | 0.7740 | 0.7838 | 1.000 |
| B7 reliability gate | 0.0913 | 0.7567 | 0.7602 | 0.933 |
| **C3 Literature-SCF** | 0.0985 | 0.7713 | 0.7807 | 1.000 |

解释：

- C3 在点估计上优于 clinical-only B2；
- C3 与 B5/B6 非常接近，没有显示明确优势；
- C3 vs B6 的 Uno C 差为 `-0.0028`，95% paired-bootstrap CI `[-0.0084, 0.0024]`；
- C3 vs B6 的 Brier 差为 `+0.0004`，95% CI `[-0.0009, 0.0018]`；
- B7 的 Brier 只在 93.3% 被接纳患者上计算，不能与全覆盖模型不加说明地直接排序。

### 10.2 HANCOCK 锁定测试集

`n=152`，死亡事件 `40`。

| 模型 | IPCW Brier ↓ | Uno C ↑ | 24 月 AUC ↑ | Coverage |
|---|---:|---:|---:|---:|
| B2 clinical-only | 0.1393 | 0.7476 | 0.7864 | 1.000 |
| B5 direct fusion | 0.1120 | 0.8207 | 0.8412 | 1.000 |
| B6 residual fusion | 0.1122 | 0.8281 | 0.8476 | 1.000 |
| B7 reliability gate | 0.1055 | 0.8249 | 0.8461 | 0.829 |
| **C3 Literature-SCF** | **0.1096** | **0.8340** | **0.8534** | 1.000 |

解释：

- C3 的 Uno C 和 24 月 AUC 为全覆盖线性融合模型中最高；
- C3 vs B6 的 Uno C 差为 `+0.0058`，95% CI `[-0.0076, 0.0178]`；
- C3 vs B6 的 Brier 差为 `-0.0026`，95% CI `[-0.0068, 0.0024]`；
- 区间包含零，因此应表述为“数值上略优/相近”，而不是显著胜出；
- B7 只有 82.9% coverage，选择性 Brier 仍需与 coverage–risk 共同解释。

### 10.3 GSE65858 外部跨平台测试

`n=244`，死亡事件 `78`。

| 模型 | IPCW Brier ↓ | Uno C ↑ | 24 月 AUC ↑ | 平均预测风险 |
|---|---:|---:|---:|---:|
| B2 clinical-only | **0.1964** | 0.5843 | 0.5893 | 0.3125 |
| B5 direct fusion | 0.2811 | 0.6114 | 0.6094 | 0.4538 |
| B6 residual fusion | 0.2725 | 0.6066 | 0.6035 | 0.4418 |
| B7 reliability gate | 0.2672 | 0.5892 | 0.5839 | 0.4289 |
| **C3 Literature-SCF** | 0.2050 | **0.6431** | **0.6472** | 0.3445 |

C3 的 calibration-in-the-large 为约 `-0.9395`。

解释：

- C3 在点估计上改善了跨平台队列中的排序判别；在 B2/B5/B6/B7/C3 主比较集合中 Uno C 和 AUC 最高。若纳入 post hoc C2，C2 的 AUC 略高（0.6542 vs 0.6472），但 Uno C 略低且 Brier 明显更差；
- 与 B5/B6 相比，C3 的 Brier 明显改善：C3 vs B6 为 `-0.0676`，95% CI `[-0.0904, -0.0459]`；
- 但 C3 的 Brier 仍略差于 clinical-only B2；
- 其平均预测风险和 calibration-in-the-large 提示绝对风险仍偏高；
- 因此结论不是“C3 已解决外部泛化”，而是：**late fusion 保留了部分跨平台排序信息，却仍未解决基线风险和绝对校准漂移。**

这是支持 TRUST-HN 研究主张的关键失败案例：

> 判别能力提高，并不代表模型可以在新平台上直接输出可信的患者绝对风险。

### 10.4 GSE41613 敏感性队列

`n=97`，死亡事件 `51`。

| 模型 | IPCW Brier ↓ | Uno C ↑ | 24 月 AUC ↑ |
|---|---:|---:|---:|
| B2 clinical-only | 0.2674 | 0.5000 | 0.5000 |
| B5 direct fusion | 0.2797 | 0.6277 | 0.6431 |
| B6 residual fusion | 0.2742 | 0.6229 | 0.6377 |
| B7 reliability gate | 0.2611 | **0.6337** | **0.6555** |
| **C3 Literature-SCF** | **0.2576** | 0.6261 | 0.6409 |

解释：

- C3 的 Brier 优于 B2/B5/B6，但与 B7 接近；
- C3 的判别与 B5/B6 相近；
- 该队列为 HPV 阴性 OSCC 敏感性验证，不能泛化为全部 HNSCC；
- Phase 7 的 C1/C2 在此队列显示更高判别，但属于 post hoc 探索结果，应作为敏感性比较而非更换主 baseline 的依据。

---

## 11. 非线性探索模型的补充结果

| 队列 | 模型 | IPCW Brier ↓ | Uno C ↑ | 24 月 AUC ↑ | 主要判断 |
|---|---|---:|---:|---:|---|
| RADCURE | C1 GBSA | 0.0958 | 0.8066 | 0.8194 | ID/锁定测试判别强 |
| RADCURE | C2 XGBoost-Cox | **0.0907** | **0.8067** | 0.8182 | 判别和 Brier 均强 |
| HANCOCK | C1 GBSA | 0.1243 | **0.8445** | **0.8835** | 判别最高但校准斜率偏大 |
| HANCOCK | C2 XGBoost-Cox | **0.1037** | 0.8405 | 0.8742 | Brier 较好 |
| GSE65858 | C1 GBSA | 0.2477 | 0.6263 | 0.6359 | 外部表现下降 |
| GSE65858 | C2 XGBoost-Cox | 0.3429 | 0.6379 | **0.6542** | 判别尚可但绝对风险严重失败 |
| GSE65858 | C3 Literature-SCF | **0.2050** | **0.6431** | 0.6472 | 判别与校准折中更合理 |

总体上：

- 非线性直接融合可在内部或同生态测试中获得较高判别；
- 外部跨平台时，C2 出现“C-index 尚可但 Brier 很差”的典型失效；
- 因此 C1/C2 更适合作为复杂模型敏感性比较；
- C3 更适合承担可解释、可复现的文献 baseline 角色。

---

## 12. 建议的正式验证协议

## 12.1 比较顺序

建议按以下层次报告，而不是只展示最终模型：

1. B0：无个体差异的 KM 风险；
2. B1/B2/B3：临床统计与机器学习模型；
3. B4：附加模态单独模型；
4. B5：直接拼接融合；
5. **C3：文献风险分数级 Cox 融合**；
6. B6：临床锚定残差融合；
7. B7：可靠性门控；
8. C1/C2/C4：post hoc 探索性复杂模型；
9. M0/N0：缺失模式与置换负对照。

## 12.2 数据隔离

必须保证：

- 患者级拆分；
- 所有插补、标准化、特征选择均仅在训练折拟合；
- stacking 一级分数必须 OOF；
- 外部队列不参与超参数、阈值或模型选择；
- B7 gate 阈值在 development 阶段冻结；
- 对 Phase 7 结果明确标注 post hoc exploratory；
- 不根据 GSE65858/GSE41613 的结果重新挑选更有利模型。

## 12.3 指标体系

### 主要指标

- Uno C-index：删失感知排序判别；
- 24 月 IPCW Brier：绝对概率误差；
- 24 月 time-dependent AUC；
- calibration-in-the-large；
- calibration slope。

### 选择性预测指标

- coverage；
- 固定 coverage 下的 Brier/C-index；
- risk–coverage curve；
- fallback rate 和 abstention rate；
- 被接纳与被拒绝患者的事件率、亚组构成和 OOD score。

### 临床价值

- 24 月 decision curve analysis；
- 不同阈值下 net benefit；
- 与 treat-all/treat-none 和 clinical-only 比较；
- 不能只以 AUROC/C-index 代表临床价值。

### 不确定性

- 患者配对 bootstrap；
- 报告 95% CI；
- 同一患者上的模型差值应配对计算；
- 小队列/小事件数结果强调区间，不使用过度确定的显著性语言。

## 12.4 压力测试

推荐至少包括：

- 10%/30% random cell dropout；
- complete modality dropout；
- 块级模态缺失；
- measurement noise；
- location/scale shift；
- RNA 表达尺度/平台表示变换；
- row-permutation negative control；
- missingness-only baseline；
- 肿瘤体积/形状 shortcut 对照；
- 解剖部位、HPV 和中心留出。

## 12.5 校准处理原则

- 主要结果优先报告未经外部结局调参的锁定预测；
- 可做仅更新 baseline hazard/intercept 的外部再校准敏感性分析；
- 如做 calibration slope 更新，应与原始模型分开报告；
- 不能使用完整外部测试集重新训练特征权重后仍称“纯外部验证”；
- GSE65858 应重点展示原始校准曲线和再校准后的变化，从而区分 rank transportability 与 absolute-risk transportability。

---

## 13. 建议的论文定位

### 13.1 不建议使用的主张

- “深度学习必然优于传统生存模型”；
- “更多模态总是提高性能”；
- “C3 完整复现了 Tian 的 CT–WSI 网络”；
- “B7 的低 Brier 证明它在全体患者中最佳”；
- “GSE41613 是通用 HNSCC 外部验证”；
- “提高 C-index 即证明临床可部署”；
- “观察性亚组差异证明治疗获益”。

### 13.2 推荐的核心主张

> 在 HNSCC 多模态生存预测中，风险分数级 late fusion 能在部分外部队列保留较好的排序判别，但并不能自动保证绝对风险校准。TRUST-HN 在临床锚定融合基础上进一步审计捷径、模态缺失和分布偏移，并通过患者级 reliability gate 决定使用融合预测、回退临床模型或拒绝自动预测。

### 13.3 与既有文献的差异化

| 既有工作常见重点 | TRUST-HN 增量 |
|---|---|
| 完整多模态病例上的平均 C-index | 自然缺失和人为缺失压力测试 |
| 更复杂的影像/病理 encoder | 资源节约的预提取特征和轻量生存模型 |
| 固定输出一个风险 | fusion / fallback / abstention 三种患者级动作 |
| 仅报告判别 | 判别、Brier、校准、coverage、net benefit 联合评价 |
| 内部随机拆分 | 多队列、跨机构和 RNA 平台偏移 |
| 特征重要性/attention 热图 | missingness-only、permuted modality、体积/形状等负对照 |
| 所有模态同等可信 | OOD 和 uncertainty 驱动的可靠性门控 |

---

## 14. 建议的最小追加分析

在现有结果基础上，优先级最高的追加工作为：

### P0：无需改变模型即可完成

1. 在结果表中正式把 C3 标记为 `Literature-SCF`；
2. 增加 C3 vs B2、B5、B6 的配对 bootstrap 汇总；
3. 分开报告全覆盖模型和选择性 B7；
4. 为 GSE65858 绘制 24 月校准图和 risk distribution；
5. 绘制 discrimination–calibration 二维图，展示高 C-index/差 Brier 的失效；
6. 报告 B7 coverage–risk 曲线，而不是只报单一 coverage；
7. 在表注中声明 Phase 7 为 post hoc exploratory benchmark。

### P1：增强文献可比性

1. RADCURE 加入 tumor-volume-only 与 clinical+volume；
2. 若可得到现成 encoder embedding，增加一个冻结的 CT foundation-model + Cox/MIL 对照；
3. HANCOCK 若能访问 WSI embedding，增加 CLAM/UNI 表征的 score-level fusion；
4. 将 C3 扩展为三分支 `clinical + imaging/pathology + omics`，但仍使用 OOF score stacking；
5. 对 C3 做 modality ablation，检验二层 Cox 是否实际忽略某个模态。

### P2：方法论文增强

1. 为 C3/B5/B6/B7 做外部轻量再校准对照；
2. 加入 conformal/interval uncertainty；
3. 将 reliability gate 与简单规则比较，例如“模态缺失即回退”；
4. 评估固定 80%、90%、100% coverage 下的 worst-group regret；
5. 比较 gate 是否对 HPV、原发部位、性别、年龄或中心造成差异性拒绝。

---

## 15. 最终建议

### 推荐 baseline

> **以 Tian et al. 2025 的单模态风险编码 + score-level Cox fusion 为主文献 baseline，在当前项目中对应 C3：cross-fitted late-fusion Cox stacking。**

### 推荐模型命名

```text
C3 / Literature-SCF
Literature-derived cross-fitted score-level Cox fusion
```

### 推荐比较框架

```text
Clinical anchor (B2)
  ├─ Direct early fusion (B5)
  ├─ Literature score fusion (C3)
  ├─ TRUST-HN residual fusion (B6)
  └─ TRUST-HN reliability gate (B7)
       ├─ fused prediction
       ├─ fallback to clinical
       └─ abstain/manual review
```

### 当前证据支持的结论

1. C3 是直接来自高影响力 HNSCC 多模态预后文献、且当前数据可公平实现的最佳主 baseline；
2. C3 在 RADCURE 与 B6 基本相当，在 HANCOCK 数值上略优；
3. C3 在 GSE65858 获得最好的排序判别，但绝对风险仍失准；
4. 非线性 C1/C2 在同生态数据上更强，却可能在跨平台数据中出现严重校准失败；
5. 现有结果已经支持论文从“谁的 C-index 最高”升级为“何时融合可信、何时应回退或拒绝”；
6. TRUST-HN 最有价值的贡献是把 missing modality、OOD、shortcut、校准和 selective prediction 纳入统一的 HNSCC 生存验证框架。

---

## 16. 参考文献与稳定入口

1. Tian et al. Multimodal fusion model for prognostic prediction and radiotherapy response assessment in head and neck squamous cell carcinoma. *npj Digital Medicine*. 2025.  
   <https://www.nature.com/articles/s41746-025-01712-0>

2. Multi-institutional Prognostic Modeling in Head and Neck Cancer: Evaluating Impact and Generalizability of Deep Learning and Radiomics.  
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC10309070/>

3. A multimodal dataset for precision oncology in head and neck cancer（HANCOCK）. *Nature Communications*. 2025.  
   <https://www.nature.com/articles/s41467-025-62386-6>

4. Improved HPV status prediction in oropharyngeal cancer by combining clinical data and deep learning features in a multimodal model. *npj Digital Medicine*. 2023.  
   <https://www.nature.com/articles/s41746-023-00901-z>

5. Cross-institutional outcome prediction for head and neck cancer patients using self-attention neural networks.  
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC8873259/>

6. End-to-end prediction of clinical outcomes in HNSCC with foundation model-based multiple instance learning. 预印本。  
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC11839013/>

7. A stacking ensemble framework integrating radiomics and deep learning for prognostic prediction in head and neck cancer.  
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC12351975/>

8. Multimodal artificial intelligence-based pathogenomics improves survival prediction in oral squamous cell carcinoma.  
   <https://pubmed.ncbi.nlm.nih.gov/38453964/>

9. Integrative Models of Histopathological Image Features and Omics Data Predict Survival in HNSCC.  
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC7658095/>

10. Morphological diversity of cancer cells predicts prognosis across tumor types. *JNCI*.  
    <https://academic.oup.com/jnci/article/116/4/555/7429400>

11. Handling missing modalities in multimodal survival prediction for non-small cell lung cancer. *npj Digital Medicine*. 2026. **邻近癌种方法学参考，非 HNSCC 证据。**  
    <https://www.nature.com/articles/s41746-026-02783-3>

---

## 17. 项目内证据文件

本文中的当前模型定义与结果来自：

```text
trust-hn/configs/phase3_baselines.json
trust-hn/configs/phase7_exploratory_benchmarks.json
trust-hn/src/trust_hn/phase7/models.py
trust-hn/results/metrics/phase6/cohort_metrics.csv
trust-hn/results/metrics/phase6/paired_comparisons.csv
trust-hn/results/metrics/phase7_exploratory/external_metrics.csv
trust-hn/results/metrics/phase7_exploratory/paired_comparisons.csv
```


