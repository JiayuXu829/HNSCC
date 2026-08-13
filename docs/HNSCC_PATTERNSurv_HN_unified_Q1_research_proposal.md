# PATTERN-Surv-HN：面向不完整与不可靠多模态的临床锚定生存学习

> **统一研究方案 v1.0**  
> **日期：** 2026-08-13  
> **目标期刊层级：** 医学人工智能、数字医学或肿瘤信息学一区、影响因子约 10 分及以上期刊的研究体量  
> **研究性质：** `post_lock_exploratory`（锁定评价后探索性/开发性研究）  
> **重要说明：** 本文档定义的是达到高影响力期刊审稿标准所需的科学结构，不承诺特定期刊、分区、影响因子或接收结果。

---

## 1. 一句话收敛我们的研究 idea

不再把 PATTERN-Surv、CALIB-Bridge、SHORTCUT-FAILSAFE、U-Latent 和 ACQUIRE-HN 当成五篇彼此分散的方法论文，而是收敛为：

> **一个主模型、一个临床命题、三个互补验证维度。**

统一主模型命名为：

> **PATTERN-Surv-HN：clinically anchored, reliability-calibrated set survival learning for incomplete and unreliable multimodal evidence。**

中文可表述为：

> **面向不完整及不可靠多模态证据的临床锚定、可靠性校准集合生存模型。**

统一研究命题为：

> 在真实 HNSCC 临床场景中，患者可能缺少某些模态，也可能拥有“形式上存在但实际无效、损坏或跨平台失准”的模态。模型的目标不是无条件融合所有数据，而是以临床风险为安全锚点，判断附加证据是否具有患者特异的增量价值，在任意模态组合下保持删失感知的风险预测，并在证据不可靠时回退或拒绝输出虚假的绝对风险。

三个验证维度分别回答：

1. **组合可靠性：** 自然缺失、模拟缺失及训练未见的模态组合；
2. **概率可靠性：** 跨平台时风险排序与绝对风险校准的分离；
3. **证据可靠性：** 模态存在但主要包含体积、中心、设备或随机捷径时的安全失败。

原 P2 和 P3 不再作为独立主模型，而成为 PATTERN-Surv-HN 的两个关键可靠性验证轴；P4 和 P5 降级为条件性扩展或未来工作。

---

## 2. 推荐论文标题

### 2.1 首选英文标题

**Clinically anchored survival learning from incomplete and unreliable multimodal evidence in head and neck cancer**

### 2.2 方法导向标题

**PATTERN-Surv-HN: reliability-calibrated set survival learning under missing modalities, platform shift, and shortcut evidence**

### 2.3 临床可信 AI 导向标题

**When should multimodal evidence be trusted? Safe survival prediction under missing, shifted, and non-informative modalities in head and neck cancer**

### 2.4 中文工作标题

**头颈鳞癌不完整与不可靠多模态证据下的临床锚定安全生存预测**

首选标题应避免直接声称“universally robust”“clinically deployable”或“prospectively validated”，除非后续确实获得新的前瞻性或从未查看过的外部验证。

---

## 3. 研究背景

### 3.1 HNSCC 多模态预后研究的临床现实

HNSCC 的生存风险受到年龄、分期、原发部位、HPV/p16 状态、治疗方案、血液指标、影像表型、病理微环境和分子特征等多层因素影响。多模态模型理论上能够整合这些互补证据，但真实临床数据并不满足“每位患者拥有完全相同模态”的理想假设：

- 部分患者只有临床和病理资料；
- 部分患者具有血液或 TMA 信息；
- WSI、CT、PET 或组学只覆盖患者子集；
- 缺失可能来自未采集、技术失败、结构性不适用或医院流程；
- 即使模态存在，也可能受到平台、批次、中心、设备、分割体积或处理流程影响；
- 不同模态组合的患者可能代表不同的临床选择过程，而不是随机缺失。

因此，完整病例拼接、均值填补或随机 modality dropout 不能充分代表真实部署问题。

### 3.2 当前文献常见的三个不足

#### 不足一：把“缺失”简化为随机遮蔽

许多缺失模态研究在完整病例上训练，然后随机删除一个输入。该设计无法回答：

- 自然缺失是否与病例构成相关；
- 训练未出现的新模态组合能否泛化；
- 小样本缺失模式是否出现严重校准偏差；
- 模态存在但发生损坏时模型是否仍盲目使用。

#### 不足二：把排序能力等同于概率可靠性

生存模型可能保持较好的 C-index，即仍能区分谁相对更危险，但同时系统性高估或低估某一时间点的绝对风险。临床决策需要“24 个月死亡风险是多少”，而不仅是患者排序。

当前项目 TCGA-HNSC 到 GSE65858 的结果已经表明：跨 RNA-seq 和 microarray 平台时，排序信息和绝对风险概率可以明显脱节。

#### 不足三：默认“模态存在即有价值”

真实影像或组学向量可能主要编码：

- 肿瘤体积；
- 中心或设备；
- 图像处理流程；
- 批次；
- 缺失模式本身；
- 高维随机结构。

当前 RADCURE 负对照结果提示，原始 radiomics 未明确优于置换或随机对照，因此不能把融合性能改善直接解释为稳定的影像生物学信号。

### 3.3 现有 TRUST-HN 结果带来的研究转向

现有结果更支持以下事实：

1. B5 direct fusion、B6 residual fusion 和 C3 score-level late fusion 已经是强基线；
2. 更复杂模型尚未被证明能在所有队列普遍胜出；
3. 人工完整模态删除可被当前门控识别，但真实平台偏移尚未被可靠识别；
4. 风险排序改善不等于绝对风险准确；
5. selective prediction 必须与 coverage 同时报告；
6. 影像增益必须超过体积和随机/置换负对照，才能支持模态特异性解释。

因此，新论文最重要的问题不是：

> “能否设计一个更大的多模态 Transformer 获得最高 C-index？”

而是：

> **模型如何识别何时应该相信附加模态，何时应该回退到临床模型，以及何时只能提供风险排序而不能提供绝对风险？**

---

## 4. 核心科学问题

### 4.1 主要科学问题

在具有删失结局的 HNSCC 多模态数据中，一个以临床风险为锚点的集合模型，能否在自然缺失、未见模态组合、输入损坏、跨平台偏移和无效模态下：

1. 利用真正有价值的附加证据；
2. 避免附加证据引起的负迁移；
3. 保持风险排序与绝对风险校准；
4. 在证据不足时执行可解释的 `FUSE / FALLBACK / RANK_ONLY / ABSTAIN` 动作？

### 4.2 临床使用场景

建议将主场景固定为：

> **初始诊断或手术后、进入后续治疗决策前的总体生存风险评估。**

主终点：

- overall survival，OS；
- 完整 `(time, event)` 时间到事件结局；
- 24 个月风险作为主要临床时间点；
- 不将 24 个月生存状态简单转换为普通二分类。

预测时间点必须在数据审计中锁定。只有预测时已经可获得的临床、病理、血液、影像或组学特征可以进入模型。

---

## 5. 科学假设

## 5.1 总体中心假设

> **相较于无条件拼接或固定后期融合，临床锚定的残差集合生存学习能够从任意可用模态集合中提取增量证据；结合模式/域校准和交叉拟合的价值路由后，模型能够减少最差缺失模式、未见组合、平台偏移和无效模态引起的临床负迁移，而不依赖降低覆盖率制造表面优势。**

## 5.2 可检验的分假设

### H1：自然缺失模式具有临床和预后异质性

不同自然模态组合的患者在病例构成、事件率、随访和预测难度上存在差异；固定融合模型的误差会随模态模式而系统变化。

**可证伪条件：** 各模式间性能和校准差异很小，且缺失模式不能预测误差或病例构成。

### H2：集合建模可改善未见组合泛化

将附加模态表示为带有模态身份、可用性和质量信息的无序 token 集合，比固定拼接、均值填补或每模式独立模型更能泛化到训练未见的组合。

**主要比较：** PATTERN-Surv-HN core vs B5、C3、C4、modality-dropout MLP、Deep Sets survival。

**可证伪条件：** 未见模式下没有稳定改善，或改善仅来自某个极小模式。

### H3：临床锚定能够减少有害融合

令附加模态只学习超过临床锚点的 residual evidence，并在附加模态缺失时严格退化为临床预测，可降低模型在低质量或无效模态下相对临床模型的 Brier regret。

**可证伪条件：** clinical-only 场景不等价于 clinical anchor，或锚定模型在多数模式中比无锚点融合更差。

### H4：排序迁移与绝对风险迁移可以分离

跨平台时，共享风险表示可能保留相对排序能力，但源域基线风险不能直接迁移。冻结排序编码器后，使用独立目标校准集估计轻量基线风险/截距/斜率适配器，可改善 Brier 和校准而基本不改变排序。

**可证伪条件：** 目标域排序完全失效，或小样本重新校准持续不稳定且不能降低概率误差。

### H5：模态可用性不等于模态可信度

真实模态、患者间置换、随机同维向量、体积特征及损坏特征会产生不同的可重复增量价值。可靠性特征应能预测融合相对临床锚点的个体或组级收益。

**可证伪条件：** 真实模态与负对照表现接近，同时 router 也不能区分何时融合有害。

### H6：价值路由可在匹配覆盖率下减少安全 regret

使用严格交叉拟合产生的折外损失差作为软监督，路由器可在不查看测试结局的情况下选择融合或回退，并在相同覆盖率、相同患者子集上降低 Brier 或 worst-pattern regret。

**可证伪条件：** router 几乎总选同一动作、不确定性与误差无关，或优势完全由删除困难患者造成。

### H7：复杂度收益主要来自可靠性机制，而非参数量

如果模型有效，改善应能通过 clinical anchor、pattern calibration、quality/OOD 信息和 value router 的消融解释，而不是仅由更大网络产生。

**可证伪条件：** 简单 C3/B5 与完整模型无差异，或消融不能定位任何有效模块。

---

## 6. 统一方法：PATTERN-Surv-HN

## 6.1 设计原则

1. **临床模型始终是安全锚点，而不是一个普通 token；**
2. **附加模态只学习临床风险之外的残余证据；**
3. **输入是任意长度的模态 token 集合，不使用固定模态位置拼接；**
4. **缺失、损坏、域偏移和不确定性显式进入可靠性估计；**
5. **风险排序与绝对概率校准分开建模；**
6. **路由器的监督必须来自训练数据的折外预测；**
7. **模型必须能在没有附加模态时严格回退临床预测；**
8. **患者级预测全部进入 Git-ignored 目录，跟踪结果仅为汇总统计。**

## 6.2 总体架构

```text
Prediction-time clinical variables
        ↓
Clinical Anchor Encoder
        ↓
clinical risk ηc + clinical survival Sc(t)
        │
        ├───────────────────────────────────────────────┐
        │                                               │
Available non-clinical modalities                       │
  pathology / blood / ICD / TMA / CT / WSI / omics     │
        ↓                                               │
Modality-specific adapters                              │
        ↓                                               │
residual token + modality ID + availability             │
+ quality + domain/OOD + uncertainty                    │
        ↓                                               │
Residual Set Transformer                                │
        ↓                                               │
patient-specific residual evidence Δη                   │
        ↓                                               │
raw fused score ηf = ηc + Δη                            │
        ↓                                               │
Pattern/Domain Calibration Bridge                       │
        ↓                                               │
absolute survival curve Sf(t)                           │
        │                                               │
        └──────── Reliability / Value Router ◄──────────┘
                          ↓
          FUSE / FALLBACK / RANK_ONLY / ABSTAIN
```

---

## 7. Backbone 设计

## 7.1 主干选择原则

HANCOCK 的样本量和事件数不足以支持大规模端到端 Transformer 搜索，因此主 backbone 应满足：

- 参数量可控，优先低于 1–2M；
- 能处理 3–7 个异构模态 token；
- 对模态输入顺序置换不敏感；
- 能自然接受任意子集；
- 允许 clinical-only 严格回退；
- 与 Deep Sets 和简单融合进行公平比较；
- 原始图像编码能力与缺失融合能力分开验证。

## 7.2 Clinical Anchor Encoder

### 首选实现

使用训练折内拟合的 **clinical elastic-net Cox** 作为稳定锚点：

\[
\eta_c = f_c(x_c)
\]

并通过训练集 Breslow baseline hazard 得到：

\[
S_c(t\mid x_c)=\exp[-H_{0,c}(t)\exp(\eta_c)]
\]

临床锚点优先复用现有 B2 实现。其优点是：

- 小样本下稳定；
- 与既有研究直接可比；
- 易于解释临床增量；
- 不会因深度临床 encoder 过拟合而夸大融合收益。

### 敏感性实现

可增加一个小型 clinical MLP-Cox，但不作为默认锚点。若 MLP 未稳定优于 elastic-net Cox，应保留 Cox 锚点。

### 临床锚点变量定义

应在数据审计后固定两套层级：

1. **Minimal clinical anchor：** 年龄、性别、吸烟、原发部位及预测时可得临床分期；
2. **Extended clinical-pathological anchor：** 在手术后预测场景中加入 pT、pN、病理分期、HPV/p16 等。

主场景只能选择其中一套；另一套作为敏感性分析，避免 pathology 同时进入 anchor 和附加模态造成重复信息。

## 7.3 Modality-specific Adapters

所有 adapter 输出统一维度 `d=64` 的 residual token。

### 表格模态

适用于 blood、pathological、TMA density、radiomics、omics pathway features：

```text
fold-specific imputation/scaling
→ Linear(input_dim, 128)
→ GELU
→ LayerNorm
→ Dropout(0.20)
→ Linear(128, 64)
```

预处理器只在训练折拟合。缺失模态不使用全零向量伪装为观测值，而是不生成该模态 token。

### ICD/稀疏编码模态

```text
code vocabulary learned on training fold
→ embedding bag / sparse linear projection
→ 64-dimensional token
```

### WSI 扩展

若后续获得许可和已有 embedding：

```text
frozen pathology foundation encoder
→ patch embeddings
→ attention-MIL/CLAM aggregation
→ 64-dimensional patient token
```

WSI 编码器的加入属于高影响力增强，但不是 PATTERN-Surv-HN 的核心 novelty。应先冻结 encoder，单独评价融合层；只有数据量允许时才有限解冻。

### CT/PET 扩展

优先级：

1. 已审计 radiomics；
2. 冻结的 3D encoder embedding；
3. 端到端 3D CNN/Swin，仅在样本和算力充分时。

必须同时保留 tumor-volume-only 和 clinical+volume baseline。

## 7.4 Token 构成

每个附加模态 token 为：

\[
z_m = e_m(x_m) + e_{id}(m) + e_q(q_m) + e_d(d_m) + e_a(a_m)
\]

其中：

- `e_m(x_m)`：模态内容表示；
- `e_id(m)`：模态身份；
- `e_q(q_m)`：质量指标；
- `e_d(d_m)`：中心、平台或允许使用的域信息；
- `e_a(a_m)`：自然观测、技术失败、人工掩蔽或损坏状态。

域信息只有在部署时可获得且协议允许时才能进入模型；否则只用于 OOD 审计，不能作为预测特征。

## 7.5 Residual Set Transformer

### 主模型

采用轻量 Set Transformer：

```text
embedding dimension: 64
self-attention blocks: 2
attention heads: 4
feed-forward dimension: 128
modality-token dropout: 0.20
pooling: clinical-query attention pooling
```

临床风险不作为普通模态与其他 token 对等竞争，而是作为 query，询问当前证据集合：

> 哪些附加证据能够在该患者的临床风险基础上提供可信增量？

集合输出为残差：

\[
\Delta\eta = f_{set}(\{z_m:m\in A\},\eta_c)
\]

原始融合风险：

\[
\eta_f=\eta_c+\Delta\eta
\]

### 最小 baseline

使用 Deep Sets：

\[
\Delta\eta=\rho\left(\frac{1}{|A|}\sum_{m\in A}\phi(z_m)\right)
\]

如果 Set Transformer 不稳定优于 Deep Sets，主模型应选择更简单的 Deep Sets 版本，而不是因模型更复杂而强行保留 Transformer。

## 7.6 Survival Backbone

### 主排序头

Cox partial likelihood：

\[
L_{cox}=-\sum_{i:\delta_i=1}
\left[\eta_i-\log\sum_{j:t_j\ge t_i}\exp(\eta_j)\right]
\]

Cox 头用于学习完整时间到事件排序，不把删失患者误标为“未死亡”。

### 绝对风险输出

使用训练数据估计 Breslow baseline hazard：

\[
S_f(t\mid x)=\exp[-H_{0,train}(t)\exp(\eta_f)]
\]

24 个月风险为：

\[
R_{24}=1-S_f(730.5\mid x)
\]

### 可选离散时间敏感性头

如果事件数和时间分布允许，可增加 8–12 个时间区间的离散 hazard head，用于检验结论是否依赖 Cox 比例风险假设。但它不应与 Cox 头同时大规模调参。

## 7.7 Pattern/Domain Calibration Bridge

为避免每个小模式单独校准过拟合，采用层级收缩的轻量适配：

\[
\text{logit}\{R_t^*(x)\}
=\alpha_{global,t}+\alpha_{pattern,t}+\alpha_{domain,t}
+\beta_{pattern/domain,t}\,\text{logit}\{R_t(x)\}
\]

约束：

- 模式和域参数向全局参数收缩；
- 小模式只允许截距偏移，样本充分后才估计斜率；
- 所有参数只在 calibration split 拟合；
- 外部 test 结局不参与模型或阈值选择；
- 目标域事件过少时禁止输出未经支持的精确绝对风险。

该模块把原 CALIB-Bridge 收敛为主模型的概率可靠性层，而不是另起一个大网络。

## 7.8 Reliability and Value Router

### 路由输入

只使用预测时可见或训练折内生成的特征：

- 当前模态集合；
- 模态内部缺失比例；
- 训练中的模式频率；
- adapter embedding norm；
- Mahalanobis、kNN 和 Isolation Forest OOD 分数；
- 多种子/ensemble prediction disagreement；
- clinical 与 fused 风险差；
- 删除单个模态后的风险敏感度；
- calibration adapter 的不确定性；
- 负对照相似度或 shortcut probe 分数。

### 路由监督

在训练数据内使用 nested cross-fitting：

1. 外层训练折拟合 clinical anchor 和 fused model；
2. 对外层留出患者产生折外预测；
3. 计算删失感知的个体 IPCW loss 差：

\[
y_{value,i}=L_{anchor,i}-L_{fused,i}
\]

4. 路由器学习预测 `y_value > 0` 的概率或期望增益；
5. 阈值只在独立 calibration split 固定；
6. 测试患者从不参与其增益标签构造。

### 动作定义

- `FUSE`：附加证据预计具有正增量，输出校准后的融合风险；
- `FALLBACK`：附加证据不可靠，输出临床锚点风险；
- `RANK_ONLY`：排序可能可迁移，但目标域绝对风险校准证据不足；
- `ABSTAIN`：患者同时超出融合模型和临床锚点的支持范围，不自动输出绝对风险。

主分析必须保持 100% 患者有 clinical anchor 或明确动作结果。选择性分析应同时报告 coverage，不能只报告被保留患者的好看指标。

---

## 8. 分阶段训练策略

为避免一次加入过多损失造成不可解释性，模型按四阶段训练。

### Stage A：临床锚点

- 训练 B2 clinical elastic-net Cox；
- 产生 cross-fitted clinical risk；
- 冻结主要超参数和预处理；
- 验证 24 月概率和完整时间排序。

### Stage B：残差集合融合

首版损失：

\[
L_B=L_{cox}+\lambda_{res}\|\Delta\eta\|_2^2
\]

目的：先证明集合模型能够训练、clinical-only 严格回退、模态顺序不影响结果。

### Stage C：模式一致性

在同一训练患者上采样多个观测子集：

\[
L_C=L_B+\lambda_{pc}L_{pattern-consistency}
\]

约束重点：

- 删除低价值模态不应造成无理由风险反转；
- 证据减少时 ensemble/删除敏感性不确定性不应系统下降；
- 不要求所有子集风险完全相同，以免抹去真实模态增量。

完整模态 teacher 蒸馏仅作为条件性消融。只有 teacher 在开发交叉验证中优于 clinical 和简单融合时才启用。

### Stage D：校准和路由

- 冻结风险编码器；
- 在 calibration split 拟合 pattern/domain calibrator；
- 使用训练折外损失差训练 value router；
- 固定 FUSE/FALLBACK/RANK_ONLY/ABSTAIN 阈值；
- test 只做一次评价，不再回调。

这种分阶段训练比把七种损失一次相加更可复现，也更容易通过消融证明每个贡献。

---

## 9. 研究设计总览

## 9.1 Study 1：HANCOCK 任意模态组合主研究

### 目的

验证自然缺失、训练未见组合和输入损坏下的 clinical-anchor residual set survival。

### 数据角色

- 总队列：763；
- 官方 training：611，用于新的开发、交叉验证和 calibration；
- 官方 test：152，已在 Phase 6 查看，只能作为 post-lock exploratory OOD 描述；
- 不得将 152 称为新的 untouched locked test；
- 不得根据 152 调整模型、阈值或损失权重。

### 模态

首轮 MVP：

- clinical；
- pathological；
- blood；
- ICD；
- TMA cell density；
- 已存在且经审计的患者级预提取特征。

WSI/TMA 原始图像不作为首轮阻塞项。

### 关键实验

1. 自然模态模式描述；
2. observed pattern 交叉验证；
3. unseen combination holdout；
4. MCAR/MAR-like/block dropout；
5. 特征噪声、缩放、置换和批次模拟；
6. full-to-subset degradation；
7. clinical safety regret；
8. FUSE/FALLBACK/ABSTAIN 的 risk–coverage。

## 9.2 Study 2：跨平台排序—概率迁移验证

### 目的

验证 PATTERN-Surv-HN 的风险表示和 calibration bridge 能否区分：

- 排序可以迁移；
- 绝对风险不可直接迁移；
- 少量目标域事件是否足以恢复概率校准；
- 何时只能输出 RANK_ONLY。

### 数据生态

- source：TCGA-HNSC；
- target：GSE65858；
- sensitivity target：GSE41613；
- 上述外部结果已被查看，全部标记为 post-lock exploratory；
- 未来高影响力确认应增加一个新的、此前未查看结局的外部/时间队列。

### 校准样本量设计

按目标域事件数预设：

```text
0、5、10、20、40 events
```

每个大小使用固定种子重复分层抽样；calibration 子集拟合适配器，独立 test 子集评价。

### 比较方法

1. source Breslow 直接迁移；
2. target baseline hazard；
3. intercept-only；
4. intercept + slope；
5. isotonic，仅在事件数充分时；
6. PATTERN-Surv-HN calibration bridge；
7. target-only model，作为样本充分时的参照上界。

## 9.3 Study 3：RADCURE 无效模态与捷径安全复制

### 目的

验证“模态存在但不可信”是否可被识别，并检验影像是否提供超过临床与肿瘤体积的增量。

### 数据角色

- Phase 6 RADCURE 评价 n=626；
- 结果已被查看，本研究只能作为 post-lock exploratory mechanism replication；
- 在开始前必须追踪并冻结 radiomics 来源、特征定义、体积变量、置换与随机对照生成方式和哈希。

### 对照

- clinical only；
- volume only；
- clinical + volume；
- radiomics only；
- clinical + radiomics；
- clinical + volume + radiomics；
- patient-permuted radiomics；
- Gaussian random features；
- volume-matched random features；
- corrupted/scaled radiomics。

### 关键评价

- 真实影像是否超过 clinical + volume；
- 真实影像是否超过所有负对照；
- shortcut probe 预测体积/中心/设备的能力；
- router 在真实、置换、随机和损坏模态下的动作比例；
- matched-coverage Brier；
- relative-to-anchor safety regret。

## 9.4 Study 4：新的真正外部确认队列

如果目标是一区约 10 分及以上期刊，建议把以下内容视为提升论文可信度的关键条件，而非装饰：

> 增加一个在本研究方案和模型冻结后才访问结局的独立外部、时间外或机构外队列。

可行方向需另行做数据和许可证审计，例如：

- 新的 HNSCC 多模态公开队列；
- 与 TCGA/GEO 不同平台的外部组学队列；
- 具有临床和 CT/PET 的外部放疗队列；
- 合作机构的时间外回顾性队列；
- 前瞻性静默验证。

在没有新 untouched external validation 的情况下，论文仍可形成严格的 post-lock benchmark 或方法学研究，但“外部验证”和“临床可迁移性”的 claim 必须明显收缩。

---

## 10. Baseline 体系

## 10.1 必做传统和现有强基线

| 类别 | 模型 | 作用 |
|---|---|---|
| 临床锚点 | B0 Kaplan–Meier | 常数风险下界 |
| 临床锚点 | B1 Cox PH | 传统基线 |
| 临床锚点 | B2 clinical elastic-net Cox | 主要安全锚点 |
| 非线性传统 | B3 Random Survival Forest | 非线性临床比较 |
| 单模态 | B4 modality-only Cox | 检验模态自身信号 |
| 早期融合 | B5 direct fusion Cox | 强简单融合 |
| 残差融合 | B6 TRUST-HN residual fusion | 现有方法比较 |
| 门控 | B7 TRUST-HN gate | 现有安全动作比较 |
| 文献融合 | C3 cross-fitted score-level Cox fusion | 主要文献 baseline |
| 缺失指示 | C4 missing-aware direct fusion | 缺失机制比较 |

C3 是主方法比较的核心，因为它代表简单、稳定且与高影响力 HNSCC 多模态文献一致的 score-level late fusion。

## 10.2 缺失模态 baseline

- separate model per sufficiently large pattern；
- mean/zero imputation + MLP；
- explicit missing indicators + MLP/Cox；
- modality dropout MLP；
- Deep Sets + Cox；
- Set Transformer + Cox；
- HAF-Surv adaptation；
- 在许可证和可复现性允许时，加入 DisPro 或 Flex-MoE 的生存适配。

外部方法必须先完成许可证、患者级拆分、删失损失和预处理泄漏审计，不直接复制代码。

## 10.3 负对照

每个主要附加模态至少包含：

1. 跨患者置换；
2. 同维随机特征；
3. missingness-only；
4. 主要捷径代理；
5. 去除模态身份 token；
6. 质量变量随机化。

如果 proposed model 不优于负对照，不得声称学到模态特异生物学。

---

## 11. 缺失、损坏和偏移场景

| 场景 | 说明 | 训练可见 | 评价 |
|---|---|---:|---:|
| Natural | 原始数据自然缺失 | 是 | 主分析 |
| MCAR | 完全随机删除模态 | 可作增强 | 压力测试 |
| MAR-like | 仅依赖预测时可见临床变量的缺失 | 可作增强 | 压力测试 |
| Block dropout | 整个模态删除 | 是 | 主压力测试 |
| Unseen subset | 训练完全不出现某些组合 | 否 | 核心泛化测试 |
| Feature noise | 加噪 | 可选 | 损坏测试 |
| Scale/location shift | 缩放或位置偏移 | 可选 | 损坏测试 |
| Patient permutation | 患者间模态置换 | 否 | 负对照 |
| Platform shift | RNA-seq→microarray 等 | 否 | 域迁移 |
| Center/time shift | 中心或时间偏移 | 否 | OOD/外部 |

任何模拟缺失概率不得依赖结局。MAR-like 公式必须预先写入配置并哈希。

---

## 12. 主要终点、estimand 与指标

## 12.1 建议的共同主要 estimand

为了避免“平均 C-index 略高”成为唯一目标，建议设置两个共同主要 estimand：

### Primary estimand 1：全覆盖 24 月概率误差

\[
\Delta Brier_{24}
=Brier_{24}(PATTERN)-Brier_{24}(C3)
\]

所有患者均保留；FALLBACK 患者使用 clinical anchor 风险。负值代表 PATTERN-Surv-HN 更好。

### Primary estimand 2：最差模式临床安全 regret

\[
WorstPatternRegret
=\max_p\{Brier_{24,PATTERN,p}-Brier_{24,Clinical,p}\}
\]

该指标直接检验模型是否在某个缺失模式中比临床锚点明显更有害。

### 选择性预测 estimand

在固定 coverage 100%、95%、90%、80% 下比较：

- matched-subset IPCW Brier；
- Uno C-index；
- risk–coverage area；
- 各模式和临床亚组的实际 coverage。

## 12.2 必须报告的指标

### 判别

- Harrell C-index；
- Uno C-index；
- 24 月 time-dependent AUC。

### 概率与校准

- 24 月 IPCW Brier；
- integrated Brier score；
- calibration-in-the-large；
- calibration slope；
- 分模式 calibration curve。

### 稳健性与安全

- full-to-subset degradation；
- seen/unseen pattern gap；
- worst-pattern Brier；
- clinical safety regret；
- error–uncertainty association；
- uncertainty monotonicity violation rate；
- coverage 和 risk–coverage curve；
- FUSE/FALLBACK/RANK_ONLY/ABSTAIN 分布。

### 潜在临床价值

- decision curve analysis；
- 固定阈值下 net benefit；
- 不同动作下患者数和事件数。

决策曲线只能解释为潜在决策价值，不等同于前瞻性临床效用。

---

## 13. 数据划分与模型选择

## 13.1 HANCOCK 开发协议

```text
Official training n=611
  ├─ outer repeated/nested cross-validation
  │    ├─ inner model training
  │    └─ inner validation/hyperparameter selection
  └─ dedicated calibration partition or cross-fitted calibration

Official test n=152
  └─ post-lock exploratory OOD description only
```

所有预处理、特征选择、缺失填补、SVD、校准和阈值均在对应训练/校准部分拟合。

## 13.2 随机种子

固定：

```text
[17, 29, 43, 71, 101]
```

报告每个种子的结果与汇总分布，不能只选择最佳种子。

## 13.3 超参数控制

推荐只搜索：

```text
embedding_dim: [32, 64, 128]
set_layers: [1, 2]
attention_heads: [2, 4]
dropout: [0.10, 0.20, 0.30]
residual_penalty: small prespecified grid
pattern_consistency_weight: [0, low, medium]
```

不进行数百组无约束 sweep，不同时网格搜索所有 loss 权重。

## 13.4 模型选择规则

按层级判断：

1. 全覆盖 Brier 不明显劣于 B2/C3；
2. Uno C 或 Brier 至少一项有稳定、临床可解释的改进；
3. calibration 不明显恶化；
4. worst-pattern 和 unseen-pattern 不出现严重负迁移；
5. 结果在 3–5 个种子中方向稳定；
6. 改善不是由降低 coverage 造成；
7. 复杂模型只有在优于简单模型时才保留。

---

## 14. 统计分析

## 14.1 配对 Bootstrap

- 按患者抽样；
- 同一 bootstrap 样本同时计算两个模型；
- 建议 2,000 次用于最终表；
- 报告模型差异、95% CI 和绝对效应；
- 多切片或多病灶患者整体抽样。

## 14.2 模式级分析

仅对满足预设阈值的模式单独报告，例如：

```text
n ≥ 30 且 events ≥ 10
```

其余模式按事先规则合并为 rare-pattern，不根据结果临时合并。

## 14.3 多重比较

采用层级分析：

1. 先检验两个共同主要 estimand；
2. 再解释排序、校准和 unseen-pattern 次要指标；
3. 消融和亚组以效应量及 CI 为主；
4. 不根据单个亚组显著性制造结论。

## 14.4 亚组

候选亚组：

- 年龄；
- 性别；
- 原发部位；
- 分期；
- HPV/p16；
- 治疗；
- 自然缺失模式；
- 中心/平台。

选择性预测还必须报告各亚组 coverage，防止模型通过系统拒绝某类患者获得更好平均指标。

---

## 15. 核心消融实验

| 消融 | 回答的问题 |
|---|---|
| 去除 clinical anchor | 改善是否来自临床锚定与负迁移控制 |
| Deep Sets vs Set Transformer | 改善来自集合不变性还是复杂交互 |
| 直接预测总风险 vs residual risk | residual 参数化是否关键 |
| 去除 modality identity | 模型是否需要知道 token 来源 |
| 去除 availability/status token | 缺失原因编码是否有价值 |
| 去除 quality token | 输入质量是否帮助损坏模态识别 |
| 去除 OOD/domain features | 平台/中心异常信息是否有增量 |
| 去除 pattern consistency | 同患者多子集约束是否有用 |
| 无 calibration bridge | 排序改善是否以概率失准为代价 |
| global vs pattern shrinkage calibration | 模式校准是否需要层级收缩 |
| 强制 FUSE vs fixed rule vs learned router | 学习路由是否优于透明规则 |
| 去除 negative-control features | router 是否依赖捷径审计信息 |
| 无 teacher distillation | 蒸馏是否真正减少子集退化 |

蒸馏不是核心模块。若 teacher 不优于简单融合，该消融分支直接停止。

---

## 16. 贡献与创新性

## 16.1 贡献 1：将“缺失模态”扩展为“不完整且不可靠证据”

现有研究常只处理空缺输入。本研究统一评价：

- 自然缺失；
- 未见组合；
- 特征损坏；
- 跨平台失准；
- 模态存在但包含捷径或随机信号。

这是临床任务定义和评价框架层面的主要创新。

## 16.2 贡献 2：临床锚定的残差集合生存学习

与无条件拼接不同，附加模态只能对临床风险提供 residual evidence；完全无附加模态时模型严格退化为 clinical anchor。该设计把“预测准确”转化为“附加模态是否产生可证明的临床增量”。

## 16.3 贡献 3：模式/域校准与风险排序分离

模型不把较高 C-index 解释为可用的绝对风险，而是显式区分：

- shared ranking representation；
- baseline hazard；
- pattern/domain-specific probability calibration；
- 校准证据不足时的 RANK_ONLY 动作。

## 16.4 贡献 4：基于折外患者价值的安全路由

路由器不只预测 OOD，而是直接学习：

> 当前附加模态相对临床锚点是否可能降低该患者的删失感知预测损失？

通过 cross-fitting 构造监督，避免同一患者既训练融合模型又给自己定义收益标签。

## 16.5 贡献 5：负对照感知的多模态生存评价

真实模态必须与置换、随机、missingness-only、体积和中心/设备代理比较。即使模型不能证明模态特异性增益，只要能可靠识别无效证据并回退，也可形成可信的 safe-failure 结论。

## 16.6 贡献 6：从平均性能转向最差模式和匹配覆盖率

研究主要评价 full-coverage Brier、worst-pattern regret、unseen-pattern degradation 和 matched-coverage risk，而不是只报告平均 C-index 或拒绝后的小子集性能。

---

## 17. 达到一区约 10 分及以上期刊体量的条件判断

## 17.1 当前方案的潜在贡献度评分

| 维度 | 当前设计潜力 | 说明 |
|---|---:|---|
| 临床问题重要性 | 5/5 | HNSCC 多模态不完整、平台偏移和安全回退具有真实临床意义 |
| 方法新颖性 | 4/5 | 单个 Set Transformer 不新，但 clinical anchor + pattern calibration + value routing 的组合有明确新意 |
| 评价创新性 | 5/5 | natural/unseen/corrupted/OOD/shortcut 与 survival calibration 的统一评价较强 |
| 统计严谨性 | 5/5 | 删失感知、交叉拟合、配对 bootstrap、coverage matching 和负对照 |
| 外部验证强度 | 当前 2.5/5 | 既有外部结局已看过；若新增 untouched external cohort，可提升至 4.5/5 |
| 临床可解释性 | 4/5 | clinical anchor、residual value、fallback 和 rank-only 动作可解释 |
| 可复现性 | 5/5 | 现有工程已有冻结配置、哈希、aggregate-only 和患者级输出治理 |

### 综合判断

- **只做一个 Set Transformer，并在 HANCOCK 内部报告更高 C-index：不够。**
- **完成 P1 的自然/未见模式、校准、负迁移和 matched-coverage：可形成较强方法论文。**
- **再加入跨平台排序—概率分离和 RADCURE 负对照机制复制：达到高影响力数字医学论文的科学体量。**
- **若再增加一个真正未查看结局的外部或时间外验证：更接近一区约 10 分以上期刊的可信度要求。**

期刊接收仍取决于实际效应、外部验证、数据质量、写作和审稿判断，不能由方法设计保证。

## 17.2 明显不足、不可作为主论文的版本

- 只在一个随机划分上比较 AUC/C-index；
- 只使用人工随机缺失；
- 不报告自然模式和未见组合；
- 不报告 Brier 与校准；
- 将 selective subset 与全覆盖模型直接比较；
- 没有 clinical + volume 和随机/置换负对照；
- 使用外部 test 选择阈值；
- 没有强传统 baseline；
- 把 post-lock 结果描述成预设锁定验证；
- 模型模块很多但没有独立消融。

## 17.3 推荐的最低可投稿版本

至少包括：

1. HANCOCK 611 的嵌套/重复开发评价；
2. B2、B5、B6、C3、C4、Deep Sets 和 Set Transformer；
3. natural、block missing、unseen subset 和 corruption；
4. Uno C、IPCW Brier、校准和 worst-pattern；
5. clinical-anchor residual fusion；
6. pattern calibration；
7. fixed-rule 与 learned router；
8. matched-coverage 评价；
9. 负对照；
10. 已查看外部队列仅作 post-lock exploratory 机制复制。

## 17.4 推荐的高影响力完整版

在最低版本基础上增加：

1. 新的 untouched external/temporal cohort；
2. 至少一种冻结 WSI 或 CT deep embedding；
3. 跨平台 calibration-event curve；
4. RADCURE clinical+volume 与 volume-matched controls；
5. 多时间点校准或 integrated Brier；
6. 风险—覆盖率和亚组 coverage；
7. prospective silent validation protocol 或模型卡；
8. 完整代码、配置、数据字典和可复现运行清单。

---

## 18. 预期结果路径与论文 claim 边界

## 18.1 路径 A：总体和安全性均成功

若 PATTERN-Surv-HN 在全覆盖 Brier、unseen pattern 和 worst-pattern regret 上稳定优于 C3/B5，同时不损害校准，可主张：

> 临床锚定的集合生存学习能够在任意模态组合中利用可信增量证据，并减少不完整或损坏模态造成的负迁移。

## 18.2 路径 B：平均性能相近，但安全性改善

若总体 C-index/Brier 与 C3 接近，但 worst-pattern、corruption 和 safety regret 改善，可主张：

> 复杂融合的平均性能优势有限，但可靠性校准和临床回退减少了特定缺失模式下的有害预测。

这仍是可信 AI/数字医学方向的有效论文故事。

## 18.3 路径 C：P1 不明显成功，但跨平台校准成功

可将主线转为：

> 外部生存模型的排序迁移不代表绝对风险可迁移；少量目标域事件可用于恢复或判定概率可用性。

此时 PATTERN-Surv core 作为框架背景，calibration bridge 成为主要结果。

## 18.4 路径 D：影像没有特异增益，但安全失败成功

如果真实 radiomics 不优于 clinical+volume 或负对照，但 router 在假/损坏影像下可靠回退，可主张：

> 多模态模型必须证明附加证据超过捷径对照；在证据无效时安全失败本身比表面融合增益更重要。

## 18.5 路径 E：所有复杂方法不优于简单模型

应诚实报告：

> 在当前样本量、事件数和表格/预提取模态条件下，没有足够证据证明深度任意集合模型优于临床 Cox、直接融合或交叉拟合后期融合。

这时停止堆叠模型，将结论定位为严格 benchmark 和失败边界，不宣传新模型优越性。

---

## 19. Go/no-go 标准

### 进入完整 PATTERN-Surv-HN 的 Go 条件

- 合成数据上能过拟合小批次；
- 模态顺序置换不改变输出；
- clinical-only 与 clinical anchor 数值等价；
- 简单集合模型至少在一个预设缺失场景改善 B5/C3，或明显减少 worst-pattern degradation；
- 结果在至少 3 个种子方向稳定；
- 改善不依赖降低 coverage。

### 停止增加复杂度的条件

- 训练分数提高但开发交叉验证不提高；
- Deep Sets 与 Set Transformer 无稳定差异；
- uncertainty 与误差不相关；
- router 总是 FUSE 或总是 FALLBACK；
- 改善只出现在一个极小模式；
- 真实模态与负对照接近；
- 校准显著恶化且独立 calibration split 无法修复；
- teacher 不优于简单融合；
- 确定性补全没有下游生存价值。

### P4 和 P5 的处理

- **U-Latent：** 不进入主论文第一轮。只有 P1 证明跨模态条件关系可学习、成对模态事件数足够且 deterministic completion 有下游价值时，才作为扩展；
- **ACQUIRE-HN：** 没有可信成本、侵入性或真实采集顺序时只保留未来工作，不实现深度强化学习。

---

## 20. 推荐主图和主表

## 20.1 主图

### Figure 1：临床问题与模型架构

- 自然缺失、损坏、平台偏移和无效模态；
- clinical anchor；
- residual set fusion；
- pattern/domain calibration；
- FUSE/FALLBACK/RANK_ONLY/ABSTAIN。

### Figure 2：HANCOCK 模态模式图

- 模态可用性 UpSet plot；
- 各模式人数和事件数；
- 模式频率与 Brier/Uno C 关系。

### Figure 3：自然、未见和损坏模式性能

- overall 与 worst-pattern；
- full-to-subset degradation；
- PATTERN vs C3/B5/Deep Sets。

### Figure 4：跨平台排序—校准分离

- C-index 与 Brier 二维图；
- calibration-event size curve；
- zero-shot、recalibrated 和 RANK_ONLY 动作。

### Figure 5：负对照与安全路由

- true、volume、permuted、random、corrupted 模态；
- 动作分布；
- matched-coverage regret。

### Figure 6：风险—覆盖率和外部复制

- risk–coverage curves；
- 亚组 coverage；
- 新 untouched external cohort 的最终结果（若获得）。

## 20.2 主表

1. 队列、终点、模态和缺失模式描述；
2. 主模型与强 baseline 的全覆盖指标；
3. natural/seen/unseen/corrupted/OOD 分层结果；
4. 主要消融；
5. 跨平台校准事件数实验；
6. RADCURE 负对照和 clinical+volume 比较；
7. 外部验证及 claim 边界。

---

## 21. 推荐论文结构

### Introduction

1. HNSCC 预后需要多层证据；
2. 真实患者的模态组合不完整且非随机；
3. 模态存在不代表可靠；
4. 现有工作偏重随机缺失和排序指标；
5. 提出 clinical-anchor、pattern calibration 和 value routing 的统一研究问题。

### Results

1. 自然模态缺失与病例异质性；
2. 强简单融合与集合模型基线；
3. clinical-anchor residual fusion；
4. unseen/corrupted pattern；
5. pattern calibration 和 safety regret；
6. 跨平台排序—概率分离；
7. RADCURE 负对照与安全失败；
8. 外部/时间外验证；
9. 消融、亚组和 coverage。

### Discussion

1. 主要贡献不是平均 C-index，而是识别何时融合可信；
2. 排序与概率的临床含义不同；
3. 模态缺失与模态无效需要统一考虑；
4. clinical fallback 的价值和局限；
5. 回顾性、post-lock、小样本和自然缺失原因不完整等限制；
6. 前瞻性静默验证和原始影像扩展。

---

## 22. 治理与可复现要求

所有实验必须记录：

```text
analysis_label: post_lock_exploratory
phase6_outcomes_already_seen: true
phase6_files_modified: false
external_outcomes_used_for_tuning: false
patient_level_outputs_git_ignored: true
tracked_outputs_aggregate_only: true
```

强制规则：

- 不修改 Phase 3–6 冻结配置、实现和结果；
- 所有新方法进入独立命名空间；
- 模型和阈值只由开发/校准数据选择；
- 已查看的官方 test/OOD 只作探索性描述；
- 患者级预测保存到 `trust-hn/results/predictions/<study>/`；
- Git 跟踪结果只能为 aggregate-only；
- 不自动下载数据、代码或权重；
- 每一步完成后生成 report 并等待审批；
- 阴性结果触发停止规则，而不是继续堆模型。

---

## 23. 最终 Specific Aims

### Aim 1：任意模态组合下的删失感知安全融合

开发临床锚定的 residual set survival backbone，在 HANCOCK 自然缺失、模拟缺失和训练未见组合中，与临床 Cox、直接融合、score-level late fusion 和缺失模态深度 baseline 比较。

### Aim 2：分离风险排序迁移与绝对风险迁移

在 TCGA-HNSC 到 GEO 跨平台生态中，冻结风险排序表示，评价目标域 baseline hazard、截距/斜率适配和事件数—校准恢复关系，并建立 FULL_RISK/RANK_ONLY/FALLBACK 动作。

### Aim 3：验证模态存在但无效时的安全失败

在 RADCURE 中加入 clinical+volume、置换、随机和体积匹配负对照，检验真实影像增量的特异性，并评价 value router 是否能在无效或损坏模态下回退临床锚点。

### Aim 4：独立外部确认

在模型、预处理、校准规则和动作阈值完全冻结后，在一个新的、此前未查看结局的外部或时间外 HNSCC 队列中评价总体性能、校准、最差模式和覆盖率。

Aim 4 是高影响力投稿的重要增强项；若不能完成，必须将外部泛化 claim 收缩为 post-lock exploratory replication。

---

## 24. 最终推荐

本项目应停止继续扩展成多个相互竞争的 idea，统一为以下论文主线：

> **PATTERN-Surv-HN 不是为了证明复杂神经网络在所有患者中都比简单模型更准确，而是为了建立一种临床锚定的证据使用原则：有价值时融合，不可靠时回退，排序可迁移但概率不可靠时只报告分层，并用负对照证明模型没有把“模态存在”误认为“模态有效”。**

主方法仅保留四个必要组件：

1. clinical anchor；
2. residual set survival backbone；
3. pattern/domain calibration bridge；
4. cross-fitted reliability/value router。

主实验仅保留三个互补维度：

1. HANCOCK：任意组合与自然缺失；
2. TCGA→GEO：跨平台排序与概率；
3. RADCURE：存在但无效的影像证据。

P4 概率潜在补全和 P5 动态模态获取不进入当前主论文，除非核心结果明确支持且不会稀释主要故事。

在该收敛方案下，论文的高水平贡献来自：

- 临床真实问题的重新定义；
- 删失、缺失、损坏、校准和捷径的统一评价；
- 临床锚定的安全增量学习；
- 排序与绝对概率的明确分离；
- 匹配覆盖率、最差模式和负对照证据；
- 新 untouched external validation 所提供的可信度。

这比同时实现多个生成模型、路由模型和 acquisition 模型更聚焦，也更符合高影响力医学人工智能期刊对临床问题、验证深度、统计严谨性和不过度宣称的要求。

---

## 25. 本地依据文件

本方案由以下现有项目文件收敛形成：

```text
docs/HNSCC_missing_modality_codex_experiment_playbook.md
docs/HNSCC_missing_modality_deep_learning_npjDM_ideas.md
docs/HNSCC_deep_learning_directions_and_baseline_selection.md
docs/TRUST_HN_experimental_findings_plain_language_summary.md
trust-hn/PROJECT_STATUS.md
trust-hn/configs/phase7_exploratory_benchmarks.json
trust-hn/configs/hancock.yaml
trust-hn/src/trust_hn/models/survival_baselines.py
trust-hn/src/trust_hn/models/residual_fusion.py
trust-hn/src/trust_hn/phase7/models.py
trust-hn/src/trust_hn/metrics/survival.py
```
