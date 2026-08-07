# 头颈鳞癌与计算模型结合的研究选题初步材料（v1）

检索日期：2026-08-06  
目标期刊：优先考虑 *npj Digital Medicine*（npj DM）  
范围：头颈鳞状细胞癌（HNSCC），并纳入口腔鳞癌（OSCC）、头颈癌前病变及放疗后心脑血管并发症等高度相关研究。

## 一、先给结论

如果目标是 *npj Digital Medicine*，仅仅“在 TCGA-HNSC 上筛基因，再比较若干机器学习模型”或“在一个公开影像集上换一个网络提高 AUC”已经明显不够。该刊官网明确说明，通常不考虑使用现成 AI 工具的小规模初步研究、纯观察性研究和缺乏临床应用验证的工作；其关注的是经过验证、能够改变临床流程或决策的数字医学方法。[npj Digital Medicine aims and scope](https://www.nature.com/npjdigitalmed/aims)

近期高水平论文呈现出五个共同趋势：

1. 从单一模态转向 CT/PET、全视野病理、临床变量、实验室检查、文本和组学的多模态融合；
2. 从“诊断分类”转向预后、复发、远处转移和治疗获益等临床决策终点；
3. 强调真正独立的多中心外部验证，而不只是随机划分或普通交叉验证；
4. 不仅报告 AUC/C-index，还考察校准、临床净获益、亚组公平性、域偏移和模型拒判；
5. 提供数据、代码、在线工具或可复现的工作流。

因此，本材料最推荐的首轮选题是：

> **开发一个能够接收任意可用模态、可识别域外病例并给出校准不确定性的 HNSCC 治疗前生存/复发风险模型，在多个公开队列上进行留一队列外部验证。**

它不是重复已有“CT+WSI+临床”融合，而是解决真实部署中的两个核心问题：不同医院可获得的模态不一致，以及模型面对新医院/新人群时是否知道“自己不确定”。

需要坦率说明：完全依赖公开回顾性数据可以完成高质量方法学论文和多队列验证，但若要显著提高 *npj Digital Medicine* 的命中率，最好再增加一个本地医院外部队列，或做 3–6 个月的前瞻性静默验证/医生决策实验。不能保证任何方案一定发表。

## 二、代表性官网论文与研究方向

### 1. npj Digital Medicine

#### 1.1 Tian 等，2025：CT、病理与临床联合预测预后及术后放疗获益

论文：[Multimodal fusion model for prognostic prediction and radiotherapy response assessment in head and neck squamous cell carcinoma](https://www.nature.com/articles/s41746-025-01712-0)

- 任务：预测 HNSCC 的总生存（OS）、无病生存（DFS）及术后放疗相关获益。
- 数据：共 1,087 例，多个中国中心；另含 56 例 TCIA 病例用于跨人群测试。主要院内数据并未完全公开，TCIA/TCGA 为公开或研究申请数据。
- 模型：3D ResNet50 提取 CT 表型；预训练 ResNet50 加注意力多实例学习提取 WSI 表型；最后用 Cox 模型融合影像签名和临床特征。
- 结果：内部测试 OS/DFS C-index 约为 0.745/0.741；外部队列 OS C-index 约为 0.682–0.717；TCIA OS C-index 降至 0.636，清楚显示跨域性能下降。
- 启示：多模态通常优于单模态，但真正困难的是跨中心泛化；“放疗获益”分析还必须进一步处理治疗选择偏倚和因果推断问题。

#### 1.2 Sun 等，2026：呼气 VOC 与唾液微生物组的无创 OSCC 检测

论文：[Rapid and noninvasive artificial intelligence-assisted diagnostic method for oral squamous cell carcinoma](https://www.nature.com/articles/s41746-026-02527-3)

- 任务：用呼气挥发性有机化合物（VOC）和唾液宏基因组区分 OSCC 与健康对照。
- 数据：发现队列 222 人，独立外部队列 83 人；38.74% 为早期患者。原始数据主要在补充材料或需联系作者，模型代码公开。
- 模型：AutoGluon 比较多种算法，VOC 侧以 LightGBM 表现较好；微生物组侧比较逻辑回归、梯度提升、XGBoost、LightGBM、随机森林；进一步做多组学融合、SHAP 和在线预测平台。
- 结果：外部验证 ROC-AUC 0.92。
- 启示：npj DM 看重“临床采集方案 + 独立验证 + 可解释生物标志物 + 可使用的软件平台”，而不只是算法本身。

#### 1.3 Shakeel 等，2026：跨样本类型迁移和合成数据用于唾液头颈癌检测

论文：[Leveraging population-scale proteomic data with deep learning for head and neck cancer detection in saliva](https://www.nature.com/articles/s41746-026-02658-7)

- 任务：利用大型血浆蛋白组训练模型，零微调迁移到小型唾液头颈癌数据。
- 数据：UK Biobank 13,208 个泛癌病例和 39,806 个对照；外部 SensOrPass 唾液队列 156 人（64 个病例）。两类数据都需要申请，不属于直接匿名下载；代码公开。
- 模型：VAE 生成 10,000 个合成癌症样本以缓解类别不平衡；CNN-Synth 进行跨样本类型迁移；并与 elastic-net、SVM、XGBoost 等比较。
- 结果：CNN-Synth 外部 AUC 0.88，高于不使用合成样本的模型（AUC 不超过 0.77）。
- 启示：小病种可以借助大型相关人群预训练，但必须把外部队列完全留作测试，并认真评估合成数据是否只复制边缘分布而扭曲高阶相关性。

#### 1.4 Kalra 等，2020：基于 TCGA 的病理图像检索和“虚拟同行评议”

论文：[Pan-cancer diagnostic consensus through searching archival histopathology images using artificial intelligence](https://www.nature.com/articles/s41746-020-0238-2)

- 任务：把待诊断 WSI 与大型历史病理库检索匹配，通过近邻病例形成诊断共识。
- 数据：TCGA 30,072 张 WSI，实际处理 29,120 张；其中 HNSCC 约 473 名患者。
- 模型：组织切片分块、k-means 选取代表性 mosaic、预训练 CNN 提特征、二值条形码索引和相似图像检索。
- 启示：可检索的相似病例和证据图块可能比单一黑箱概率更便于病理医生核查；后续可与现代病理基础模型和不确定性估计结合。

### 2. Nature Communications

#### 2.1 Dörrich 等，2025：HANCOCK 多模态公开数据集

论文：[A multimodal dataset for precision oncology in head and neck cancer](https://www.nature.com/articles/s41467-025-62386-6)

- 数据：763 名头颈癌患者，包含人口学、病理、术前血液检查、手术记录文本、H&E WSI、TMA 免疫染色、复发和生存结局。
- 模型：104 维患者向量、UMAP、随机森林；病理侧使用 CLAM 多实例学习及基础模型特征。
- 结果：复发和生存预测最高平均 AUC 约 0.79；特意构造分布内、分布外及“全部口咽癌作为测试集”的划分，结果显示域外性能明显下降。
- 数据状态：HANCOCK 可公开获取，并计划镜像到 TCIA；处理代码以 Apache 2.0 许可公开。
- 价值：这是本项目最值得优先下载的数据，因为它同时提供多模态、终点、公开代码和显式域偏移设置。

#### 2.2 Wang 等，2023：细胞空间图预测口腔癌前病变恶变

论文：[Deep learning of cell spatial organizations identifies clinically relevant insights in tissue images](https://www.nature.com/articles/s41467-023-43172-8)

- 任务：用细胞核形态和细胞—细胞空间关系预测口腔潜在恶性病变（OPMD）是否进展为 OSCC。
- 数据：训练集 OPMD1 仅 23 人（17 个长期不进展、6 个较早进展）；独立测试 OPMD2 53 人。数据为受控访问，代码公开。
- 模型：Ceograph 图神经网络，把细胞作为节点，核形态、细胞类型、距离和平行度作为节点/边特征。
- 结果：测试集中高风险组恶变风险更高（HR 3.17），24/50 个月 AUC 分别为 0.915/0.797。
- 启示：细胞空间组织比简单 WSI 分类更有病理解释性，但样本量很小；可用公开大队列做自监督预训练，再用本地 OPMD 队列验证。

#### 2.3 Kürten 等，2021：HNSCC 单细胞免疫微环境图谱

论文：[Investigating immune and non-immune cell interactions in head and neck tumors by single-cell RNA sequencing](https://www.nature.com/articles/s41467-021-27619-4)

- 数据：6 个 HPV 阳性和 12 个 HPV 阴性 HNSCC 肿瘤及匹配外周血，共 134,606 个细胞；公开 GEO 编号 GSE164690。
- 方向：HPV 相关细胞状态、成纤维细胞亚型、巨噬细胞 PD-L1 表达、受体—配体互作及免疫逃逸。
- 价值：可作为病理模型的“生物学教师”，用于定义免疫/基质签名，而不宜把 18 名患者直接当作患者级深度模型训练集。

#### 2.4 Choi 等，2023：从正常、白斑、原发癌到转移的单细胞进展轨迹

论文：[Single-cell transcriptome profiling of the stepwise progression of head and neck cancer](https://www.nature.com/articles/s41467-023-36691-x)

- 方向：刻画正常组织、白斑、原发 HNSCC 和转移的逐步演化；识别 LGALS7B 恶性细胞、CXCL8 成纤维细胞、COL1A1–CD44 互作和 LAIR2 调节性 T 细胞。
- 价值：可为“癌前病变恶变预测”或“WSI 预测侵袭/转移微环境”的标签和机制解释提供依据。

### 3. Medicina

#### Suárez 等，2025：ChatGPT-4o 识别口腔临床照片

论文：[ChatGPT in Oral Pathology: Bright Promise or Diagnostic Mirage](https://www.mdpi.com/1648-9144/61/10/1744)

- 任务：仅凭口腔临床照片识别 OSCC、口腔白斑和口腔扁平苔藓。
- 数据：先筛出 23 张可疑图片，每张向 ChatGPT-4o 重复询问 30 次，共 690 次回答；真实阳性实际上只有 2 个 OSCC、3 个白斑和 4 个扁平苔藓病例。图片不公开，仅可联系作者。
- 结果：OSCC AUC 0.81、特异度约 97.1%，但敏感度只有 65%；整体准确率主要被大量真阴性抬高。
- 关键评价：这是探索性可行性研究，不足以支持临床使用。未来研究应把任务定义为“是否需要紧急转诊/活检”的高敏感度分诊，并进行患者级、多中心、前瞻性比较，而不是重复调用次数级的伪样本统计。

### 4. JACC: CardioOncology

JACC: CardioOncology 中直接针对 HNSCC 建模的原始论文较少，但它提示了一个常被头颈肿瘤 AI 忽略的重要方向：颈部放疗后的颈动脉狭窄、卒中和自主神经功能障碍。

#### 4.1 2021 国际共识：放射治疗的心血管表现

论文：[Cardiovascular Manifestations From Therapeutic Radiation](https://www.jacc.org/doi/10.1016/j.jaccao.2021.06.003)

- 结论：头颈放疗后颈动脉狭窄和脑血管事件风险增加；高风险患者可在放疗后约 1 年开始颈动脉超声，并每 3–5 年复查；随访 CT 还应检查颈动脉钙化。
- 对计算研究的启示：可把治疗计划剂量、颈动脉自动分割、基线钙化和传统心血管危险因素联合，建立晚期血管毒性风险模型。

#### 4.2 Sen 等，2026：肿瘤心脏病风险模型的方法学要求

论文：[Risk Prediction in Cardio-Oncology: Conceptual and Methodological Considerations](https://www.jacc.org/doi/10.1016/j.jaccao.2026.01.006)

- 强调任务、起始时间点和预测窗口必须对应具体临床决策；要处理癌症死亡竞争风险、治疗相关的 immortal-time bias、适应证混杂、低事件率、校准和临床净获益。
- 对本项目的启示：无论做生存、放疗获益还是卒中风险，必须先固定 index date，只允许使用该时点前已知变量，不能把复发、后续治疗或随访信息倒灌进基线模型。

## 三、可使用的公开或研究申请数据

| 数据集 | 规模与模态 | 可做任务 | 获取状态与注意事项 |
|---|---|---|---|
| HANCOCK | 763 人；临床、病理、血液、手术文本、H&E WSI、TMA、复发/生存 | 复发、OS、病理表型、多模态缺失学习 | 公开；[论文及数据说明](https://www.nature.com/articles/s41467-025-62386-6) |
| RADCURE | 3,346 人；放疗计划 CT、RTSTRUCT、人口学、治疗和随访 | OS、复发/控制、CT 风险建模、域泛化 | 临床表公开，影像受 NIH/TCIA 受控访问；[TCIA RADCURE](https://wiki.cancerimagingarchive.net/pages/viewpage.action?pageId=70226325) |
| Head-Neck-PET-CT | 298 个影像病例；四中心 FDG-PET/CT、RTSTRUCT/RTDOSE/RTPLAN，300 人临床表 | 局部区域复发、远处转移、OS、PET/CT 外部验证 | 临床表 CC BY；影像需签 TCIA restricted agreement；[TCIA 页面](https://wiki.cancerimagingarchive.net/display/Public/Head-Neck-PET-CT) |
| TCGA-HNSC | 528 个表征病例；临床、RNA-seq、突变、拷贝数、甲基化、WSI 等 | OS、分子亚型、HPV、形态—组学蒸馏 | 派生数据和 WSI 大多开放；部分原始/胚系数据受控；[NCI 页面](https://www.cancer.gov/ccg/research/genome-sequencing/tcga/studied-cancers) |
| CPTAC-HNSCC | 当前页面列出 112 人、390 张 WSI；154 人有 CT/MR/PET；另有蛋白组/基因组 | 病理—蛋白组、影像—组学、外部验证 | WSI 较易获取；头颈影像为受控访问；[TCIA CPTAC-HNSCC](https://www.cancerimagingarchive.net/collection/cptac-hnscc/) |
| GSE65858 | 270 个 HNSCC 肿瘤表达谱，含 HPV/TP53、淋巴结和生存信息 | 组学外部验证、HPV/转移签名 | 公开；[GEO GSE65858](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE65858) |
| GSE103322 | 约 5,902 个细胞的经典 HNSCC 单细胞数据 | 细胞类型签名、肿瘤微环境解释 | 公开；可与 TCGA bulk/WSI 连接 |
| GSE164690 | 18 名 HNSCC 患者、134,606 个细胞，含 HPV 状态和匹配血液 | 免疫/基质签名、细胞互作、HPV 生物学 | 公开；[GEO GSE164690](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE164690) |
| OpenKBP | 340 名头颈放疗病例（200 训练、100 测试、40 验证） | 放疗剂量预测、OAR 保护 | 公开竞赛数据；不适合直接做长期临床结局 |
| UK Biobank / SensOrPass | UKB 蛋白组 53,014 人；SensOrPass 唾液 156 人 | 蛋白组迁移、非侵入筛查 | 均需正式申请，并非直接公开下载 |

“公开数据”应再细分为：直接开放、需点击协议、需数据使用协议/伦理申请、仅通信作者提供。论文中不能把这些状态混写。

## 四、第一轮推荐的五个 idea

### Idea 1（首选）：面向真实缺失模态和域偏移的 HNSCC 风险模型

**一句话：**不同医院可能只有 CT、只有病理，或只有临床数据；模型应接收任意可用组合，在新医院上保持校准，并对不可靠病例主动拒判。

- 任务：治疗前预测 2 年 OS；有一致标签的队列再预测 2 年复发/远处转移。
- 数据：RADCURE、HANCOCK 为主要训练资源；Head-Neck-PET-CT、TCGA-HNSC、CPTAC-HNSCC 做留一队列外部验证。
- 模型：CT/PET 3D encoder + WSI 病理基础模型/注意力 MIL + tabular Transformer/Cox；用带模态掩码的 gated mixture-of-experts 或 Set Transformer 融合；用深度集成和 conformal prediction 给出不确定性与拒判。
- 创新点：不是简单融合，而是“any-modality + external-domain + calibrated abstention”。
- 可行性：高；最主要风险是不同队列终点定义和起始时间不一致。

### Idea 2：从 H&E 中蒸馏单细胞免疫/基质状态的可解释预后模型

**一句话：**用单细胞和 bulk 组学定义免疫、CAF、TLS、EMT 等生物学教师标签，再训练 WSI 模型从常规 H&E 中估计这些状态并预测复发。

- 数据：TCGA-HNSC WSI+RNA；CPTAC-HNSCC WSI+蛋白组；GSE103322/GSE164690 提供细胞签名；HANCOCK 做外部生存/复发验证。
- 模型：CONCH/UNI/DINOv2 patch encoder，attention MIL 或细胞图 GNN，多任务学习同时预测免疫签名和生存。
- 创新点：输出可核查的“虚拟微环境指标”，而不是单一黑箱风险分数。
- 可行性：中高；需认真处理不同平台间的标签迁移和批次效应。

### Idea 3：高敏感度、会拒判的口腔癌智能手机分诊系统

**一句话：**将任务从“精确诊断是哪一种口腔病”改为“是否需要 2 周内专科转诊/活检”，比较视觉基础模型、多模态大模型和医生。

- 数据：公开临床照片只能用于预训练/初测；要冲击 npj DM，最好建立多中心、连续入组的本地智能手机图像队列，保留病理金标准。
- 模型：医学视觉语言模型 + 结构化临床信息；深度集成/共形分类控制漏诊率；输出差异诊断和拒判。
- 主要指标：固定 95% 或 98% 敏感度下的特异度、NPV、转诊负担、亚组公平性和医生—AI 工作流效果。
- 可行性：中；临床意义强，但公开数据不足是主要瓶颈。

### Idea 4：多模态因果模型预测术后放疗/放化疗的个体治疗获益

**一句话：**不再把“高风险”误当作“治疗有效”，而是估计每名患者接受与不接受辅助治疗的反事实结局差异。

- 数据：HANCOCK 作为初步探索；TCGA 的治疗记录可做敏感性分析；最好有本地多中心手术队列进行验证。
- 模型：causal forest、TARNet/DragonNet、doubly robust learner；WSI/临床表型作为协变量；使用倾向评分、负对照和未测混杂敏感性分析。
- 可行性：中等偏低；创新性高，但治疗指征混杂、positivity 和标签完整性要求很高。

### Idea 5：颈部放疗后颈动脉损伤/卒中风险的影像—剂量模型

**一句话：**自动分割颈动脉，量化基线钙化和实际剂量，预测放疗后的颈动脉狭窄或脑血管事件。

- 数据：RADCURE、Head-Neck-PET-CT 可提供 CT/剂量/结构预训练，但公开数据通常缺少长期超声狭窄或卒中结局；必须链接本地长期随访或行政数据库。
- 模型：nnU-Net/TotalSegmentator 类颈动脉分割，剂量—体积特征，竞争风险模型或动态生存模型。
- 可行性：当前偏低；一旦有随访结局，跨 HNSCC 与 cardio-oncology 的原创性很强。

## 五、首选 Idea 的可执行研究定义

### 5.1 暂定题目

**HNSCC-MOSAIC: An uncertainty-aware any-modality survival model for head and neck squamous cell carcinoma across heterogeneous clinical cohorts**

中文：**HNSCC-MOSAIC：跨异质临床队列、可处理任意缺失模态并量化不确定性的头颈鳞癌生存模型。**

### 5.2 明确任务

- 目标人群：成年、初诊、病理证实的 HNSCC 患者。
- Index date：首次根治性治疗决策日；所有输入必须在该日之前可获得。
- 主要输入：年龄、性别、原发部位、T/N/M、HPV/p16、吸烟饮酒、治疗前 CT/PET、诊断或手术 H&E WSI。实验室检查仅在对应队列中作为可选模态。
- 主要输出：从 index date 起的个体化 OS 风险曲线，预先指定 24 个月为主要时间点。
- 次要输出：24 个月复发或远处转移风险；若不同数据集定义无法可靠统一，则只在标签一致的影像队列中进行。
- 安全输出：模型置信区间、域外分数和“需要人工复核/拒绝预测”标志。
- 临床比较对象：TNM/HPV 分层、Cox elastic-net、随机生存森林、单模态模型、普通晚期融合模型。

### 5.3 数据分工

1. **RADCURE（n=3,346）**：CT 与临床表型的主训练队列，内部应尽量按年份或治疗阶段做时间外验证，而不是随机打散。
2. **HANCOCK（n=763）**：WSI、临床、血液和文本的多模态训练/验证；保留论文既有的分布内与分布外设置，避免直接复现原工作。
3. **Head-Neck-PET-CT（影像 n=298，临床 n=300，四中心）**：完全锁定的 CT/PET 外部测试，重点评估局部复发、远处转移和跨中心校准。
4. **TCGA-HNSC（528 cases）**：WSI+临床外部测试，并用于形态—组学机制解释；不得把同一患者的多个切片分到训练和测试两侧。
5. **CPTAC-HNSCC（112 人有 WSI，154 人有放射影像）**：小型但模态丰富的独立泛化与生物学验证队列。

在正式建模前必须先做一张“字段—定义—时间点—缺失率—可否跨队列统一”的数据字典。若 OS 起算点、复发定义或 HPV 状态无法一致，就要降级为分层任务，而不是强行拼接。

### 5.4 模型结构

#### 基础编码器

- CT/PET：以肿瘤和区域淋巴结 ROI 为中心的 3D ResNet 或 Swin Transformer；RTSTRUCT 可直接提供训练期 ROI，另建立自动分割敏感性分析。
- WSI：优先使用公开或可合法申请权重的病理基础模型提取 patch embedding，再用 attention-MIL/TransMIL 汇聚；保留轻量级 ResNet50-MIL 作为公平基线。
- 临床表格：Cox elastic-net 为首要统计基线；神经网络侧使用 FT-Transformer 或带缺失指示器的 MLP。
- 文本：第一版不把手术记录作为必须模态；第二版可使用本地部署的临床文本 encoder，避免因翻译与语言造成额外偏差。

#### 任意模态融合

- 每个 encoder 输出同维度患者 embedding；
- 使用带 modality mask 的 gated mixture-of-experts 或 Set Transformer；
- 训练时随机 modality dropout，使模型学习 CT-only、WSI-only、clinical-only 及组合输入；
- 以共有临床变量作为跨队列锚点，加入 cohort-adversarial 或 distributionally robust loss，减少模型记住数据集来源。

#### 生存与不确定性

- 主生存头：离散时间 hazard 或 Cox-Time；如结局允许，使用 competing-risk DeepHit 区分癌症相关死亡和其他死亡。
- 不确定性：5 个独立随机种子的 deep ensemble；在锁定校准集上做 conformal survival interval。
- 拒判：预先设定风险覆盖率曲线，报告在保留 100%、90%、80% 病例时的性能和错误率，而不是事后选择最好阈值。

### 5.5 评价方案

- 区分度：Harrell/Uno C-index、时间依赖 AUC；
- 校准：24 个月校准曲线、calibration-in-the-large、校准斜率、integrated Brier score；
- 临床价值：decision-curve analysis，比较 TNM/HPV 与模型的净获益；
- 可靠性：leave-one-cohort-out 外部验证、域偏移检测、选择性预测 risk–coverage curve；
- 公平性：至少按性别、年龄、原发部位、HPV/p16、治疗方式和队列报告性能与校准；
- 增量价值：不仅比较 P 值，还报告相对 TNM/临床基线的 C-index 增量、Brier score 改善和 bootstrap 95% CI；
- 复现性：预注册主要终点和分析计划；公开患者 ID manifest、预处理代码、冻结模型权重和环境文件。

### 5.6 必须避免的数据泄漏

- 不能把复发时间、复发状态、后续治疗或随访信息作为“治疗前 OS 预测”的输入；已有部分 OSCC 研究把 time-to-recurrence 放入 OS 模型，临床使用时不可能提前知道该变量。
- 多张 WSI、多个扫描或同一患者不同时间点必须保持在同一数据划分中。
- 特征选择、归一化、缺失值填补和阈值选择只能在训练/校准数据中完成。
- 如果影像 ROI 来自治疗后或人工使用结局信息修订的轮廓，不能进入治疗前模型。
- “高风险组接受放疗后生存更好”不是个体治疗获益的充分证据；如声称治疗效应，应采用明确的因果设计。

### 5.7 使其更接近 npj Digital Medicine 的加强项

公开数据版本完成后，优先增加以下任一项：

1. 一个完全独立的本地医院队列，模型和阈值在解盲前冻结；
2. 前瞻性静默验证，观察真实连续病例中的覆盖率、校准漂移和拒判原因；
3. 医生—AI 读者研究，检验模型是否改善风险分层、决策一致性和用时；
4. 一个可部署的研究原型，展示不同模态缺失时的风险变化和不确定性，而不只提供 notebook。

## 六、建议下一步细化的顺序

下一轮最值得先回答三个问题：

1. 团队是否有本地 HNSCC 队列、可用模态和伦理审批条件；
2. 更偏向放疗人群、手术人群，还是所有初诊 HNSCC；
3. 可用算力是否支持数百 GB CT/WSI，或需要先做临床表格+预提取 embedding 的轻量版本。

确认后，可以继续形成：研究假设、纳排标准、变量表、统计分析计划、模型图、训练/验证划分、消融实验、样本量与事件数评估、论文标题/摘要框架和 6–12 个月执行时间表。
