# Codex 执行手册：HNSCC 任意模态缺失生存学习的探索、实现与顶刊验证

> 文档日期：2026-08-12  
> 工作区：`D:\medical_paper\HNSCC`  
> 现有研究方案：`docs/HNSCC_missing_modality_deep_learning_npjDM_ideas.md`  
> 现有工程：`trust-hn/`  
> 文档用途：指导 Codex 以**新的锁定评价后探索研究**（post-lock exploratory study）方式，逐步实现、验证和筛选可投稿 npj Digital Medicine（《自然》合作期刊数字医学）或同等级一区医学人工智能期刊的方法。  
> 重要声明：下述模型均为候选研究设计，尚未被实验验证为优于现有方法；本手册不构成对期刊接收或性能提升的承诺。

---

## 0. 如何使用本手册

本文件不是单纯的“idea 列表”，而是一份可交给 Codex 分阶段执行的科研工程规范。每个方案都包含：

1. **科学问题**：要回答的医学与方法学问题；
2. **顶刊故事**：为何不是只换一个网络刷分；
3. **创新点**：相对已有缺失模态方法究竟新增了什么；
4. **方法框架**：输入、模块、损失函数、输出与安全动作；
5. **可借鉴研究**：相近任务、公开论文和代码中可复用的思想；
6. **Codex 任务清单**：精确到目录、文件、类、函数、测试与输出；
7. **实验协议**：数据拆分、baseline（基线方法）、缺失场景、指标、消融和统计；
8. **Go/no-go（继续/停止）规则**：防止在无效方向上无限堆叠复杂度；
9. **论文主张边界**：什么结果可以写，什么结果不能写。

推荐执行方式：一次只让 Codex 完成一个里程碑，审查代码、测试、数据审计和 aggregate-only（仅汇总）结果后再进入下一步。不要用一个超长提示词要求 Codex 一次完成全部模型和正式实验。

---

## 1. 不可违反的研究治理边界

### 1.1 当前项目事实

`trust-hn/PROJECT_STATUS.md` 已明确：

- Phase 6 的一次性 locked/external evaluation（锁定/外部评价）已完成；
- `phase6_outcomes_seen=true`，即 Phase 6 结果已经被研究者看到；
- Phase 3–6 的注册配置、冻结决策和结果文件不得修改；
- 不得根据 Phase 6 外部结果重新调参、重新校准或切换门控阈值；
- 新方法只能标记为 **post-lock exploratory / development study（锁定评价后探索性/开发性研究）**；
- 不得把新比较倒写成 Phase 6 前预设的验证；
- 患者级预测只能保存在 Git 忽略目录；
- 可提交到 Git 的结果必须是 aggregate-only，不得含患者标识或患者级预测。

### 1.2 Codex 每次开始任务前必须执行的治理检查

Codex 必须先读取：

```text
trust-hn/PROJECT_STATUS.md
trust-hn/configs/phase7_exploratory_benchmarks.json
trust-hn/.gitignore
本方案对应的 configs/<study>/protocol.yaml
```

然后在任务报告中明确写出：

```text
analysis_label: post_lock_exploratory
phase6_outcomes_already_seen: true
phase6_files_modified: false
external_outcomes_used_for_tuning: false
patient_level_outputs_git_ignored: true
tracked_outputs_aggregate_only: true
```

### 1.3 禁止事项

Codex 不得：

- 修改 `phase3`、`phase4`、`phase5`、`phase6` 冻结实现以使新模型更好看；
- 覆盖已有 `results/metrics/phase6/`、`results/figures/phase6/` 或相应决策文件；
- 在全数据上拟合预处理器后再切分；
- 使用测试集选择超参数、缺失率、模型版本、校准方法或阈值；
- 把 visit after outcome（结局后访视）、生存时间、死亡状态或其衍生字段误作为预测特征；
- 将同一患者的切片、病灶或重复样本分到不同数据划分；
- 因神经网络表现不佳而删除强传统 baseline；
- 把“未显著差于”写成“显著优于”；
- 把人工随机缺失稳健性等同于真实临床缺失稳健性；
- 自动联网下载数据、预训练权重或外部代码；任何下载须先列出来源、许可证、文件大小、哈希方案并获得明确许可。

### 1.4 新研究的推荐命名空间

不要污染冻结代码，新增独立目录：

```text
trust-hn/
  configs/pattern_surv/
  src/trust_hn/pattern_surv/
  scripts/audit_pattern_surv_data.py
  scripts/train_pattern_surv.py
  scripts/evaluate_pattern_surv.py
  tests/test_pattern_surv_*.py
  results/metrics/pattern_surv/       # 仅汇总，可跟踪
  results/figures/pattern_surv/       # 无患者标识，可跟踪
  results/predictions/pattern_surv/   # 患者级，必须 Git ignored
  artifacts/pattern_surv/             # 模型权重，默认不提交或按政策管理
```

其他方案使用同样隔离原则：`calib_bridge/`、`shortcut_failsafe/`、`u_latent/`。

---

## 2. 当前证据说明了什么，以及新研究必须回答什么

### 2.1 已观察到的结果

当前 TRUST-HN 实验支持以下谨慎结论：

1. B5 direct fusion（直接融合）、B6 stacked residual fusion（堆叠残差融合）和 C3 cross-fitted late fusion（交叉拟合后期融合）是强基线；
2. 更复杂的模型尚未被证明在所有队列中普遍优于传统模型；
3. B7 reliability gate（可靠性门控）可以处理某些人工完整模态删除，但不能据此证明可识别真实平台漂移；
4. TCGA RNA-seq（RNA 测序）到 GSE65858 microarray（表达芯片）的迁移出现严重绝对风险校准失败；
5. 风险排序改善与绝对风险准确不是同一件事；
6. RADCURE 原始 radiomics（影像组学）没有明确优于置换或随机负对照，因此不能宣称学到了稳定的影像特异生物学；
7. selective prediction（选择性预测）必须同时报告 coverage（覆盖率），低覆盖子集上的 Brier score（布里尔评分）不能直接与全覆盖模型比较。

### 2.2 因此主问题不应是

> “能否把多个模态拼进更大的 Transformer（变换器）并提高一次 AUC？”

而应是：

> **当患者的可用模态组合、模态质量、采集平台和中心分布发生变化时，一个删失感知的 HNSCC 生存模型能否识别哪些附加证据值得使用，保持风险排序和绝对风险校准，并在证据不可靠时安全回退？**

### 2.3 顶刊体量的最低科学结构

一个有希望冲击高水平医学人工智能期刊的完整故事至少应包含：

- 一个明确临床使用场景，而非泛化“多模态预测”；
- censored time-to-event（删失感知时间到事件）结局，而非只做 alive/dead（生存/死亡）二分类；
- 真实自然缺失与模拟缺失并存；
- seen pattern（训练见过的模态组合）与 unseen pattern（训练未见的模态组合）分开；
- 至少一个 distribution shift（分布偏移）或外部生态复制；
- 强传统模型、直接融合、后期融合和目标领域缺失模态模型；
- negative control（负对照）、shortcut audit（捷径审计）和 leakage audit（泄漏审计）；
- discrimination（判别）、calibration（校准）、clinical utility（临床净获益）和 worst-group（最差组）评价；
- 预设继续/停止标准；
- 对阴性结果有可解释且不夸大的科学叙事。

---

## 3. 方案总览、优先级与执行决策树

### 3.1 优先级排序

| 优先级 | 方案 | 核心问题 | 推荐度 | 风险 | 首选数据 |
|---|---|---|---:|---:|---|
| P1 | PATTERN-Surv Core | 任意模态集合下的临床锚定、模式泛化与安全路由 | 最高 | 中 | HANCOCK |
| P2 | CALIB-Bridge | 跨平台时排序迁移与绝对风险校准迁移解耦 | 高 | 中低 | TCGA-HNSC→GSE65858/GSE41613 |
| P3 | SHORTCUT-FAILSAFE | 模态存在但含捷径或无效信号时能否识别并回退 | 高 | 中 | RADCURE |
| P4 | U-Latent Evidence Completion | 不生成原图的概率潜在证据补全与不确定性传播 | 中 | 高 | HANCOCK；后续 TCGA/CPTAC |
| P5 | ACQUIRE-HN | 在成本约束下动态选择下一模态或停止 | 探索性 | 高 | HANCOCK 模拟成本 |

### 3.2 推荐执行顺序

```text
共同基础设施与数据合同
        ↓
P1.1 简单集合式生存 baseline
        ↓
P2 排序/校准迁移快速试验 ── 若失败，仍可形成校准边界研究
        ↓
P1.2–P1.5 完整 PATTERN-Surv
        ↓
P3 捷径与失效感知复制
        ↓
只有 P1 证明“缺失模式表征有价值”时才进入 P4
        ↓
只有获得可信模态成本或真实采集顺序时才把 P5 升为主研究
```

### 3.3 决策原则

- **先证明问题存在，再证明复杂方法有效。**
- **先用表格/预提取特征完成 MVP（minimum viable product，最小可行版本），再接 WSI/CT 原始图像。**
- 如果简单 Deep Sets（深度集合模型）不优于 B5/B6/C3，不应立即加大模型；先检查划分、删失损失、模式采样和校准。
- 如果复杂模型只提高 C-index 而明显损害 Brier/校准，不能作为主模型；应尝试 P2 或安全回退叙事。
- 如果影像真实特征不优于负对照，P3 的主张应转为“可靠识别无效模态”，而不是“影像提升生存预测”。

---

## 4. 共同实验基础设施：所有方案先做这一层

### 4.1 目标

建立一个不依赖具体网络的统一框架，使任意方案都使用相同：

- 患者级数据划分；
- 模态 registry（注册表）；
- 缺失模式编码；
- 删失结局接口；
- 评价指标；
- 统计 bootstrap（自助法）；
- 结果目录和隐私治理；
- baseline 调用接口。

### 4.2 推荐新增文件

```text
trust-hn/configs/pattern_surv/
  registry.yaml
  protocol.yaml
  splits.yaml
  stress_patterns.yaml
  baselines.yaml

trust-hn/src/trust_hn/pattern_surv/
  __init__.py
  contracts.py
  registry.py
  data.py
  splits.py
  missingness.py
  outputs.py
  statistics.py

trust-hn/tests/
  test_pattern_surv_contracts.py
  test_pattern_surv_registry.py
  test_pattern_surv_splits.py
  test_pattern_surv_missingness.py
  test_pattern_surv_outputs.py
  test_pattern_surv_leakage.py

trust-hn/scripts/
  audit_pattern_surv_data.py
  build_pattern_surv_manifest.py
```

### 4.3 数据合同

为每位患者定义：

```python
@dataclass(frozen=True)
class MultimodalSurvivalSample:
    patient_id: str
    time: float
    event: bool
    modalities: dict[str, np.ndarray]
    availability: dict[str, bool]
    quality: dict[str, np.ndarray]
    domain: dict[str, str | int | None]
    split: str
```

要求：

- `modalities` 中缺失模态不使用全零向量冒充真实数据；
- `availability` 显式区分“未采集”“采集失败”“结构性不适用”和“人为掩蔽”；
- `quality` 允许记录缺失比例、图像质量、批次、异常值距离等；
- `domain` 只保存允许使用的中心/平台信息，且必须声明部署时是否可得；
- `time/event` 只能进入损失和评价，不能进入 encoder（编码器）；
- 患者 ID 只用于连接和审计，不进入模型。

### 4.4 模态注册表

`registry.yaml` 至少包含：

```yaml
modalities:
  clinical:
    type: tabular
    required_anchor: true
    feature_source: phase2_adapter
    prediction_time_available: true
  pathological:
    type: tabular
    required_anchor: false
  blood:
    type: tabular
    required_anchor: false
  icd:
    type: sparse_codes
    required_anchor: false
  tma_density:
    type: tabular_or_map_embedding
    required_anchor: false
  wsi:
    type: bag_embedding
    required_anchor: false
    current_status: unavailable
  ct:
    type: volume_or_radiomics
    required_anchor: false
```

每个模态还要记录：维度、归一化方式、训练集拟合规则、缺失原因、质量变量、数据许可证、患者数和事件数。

### 4.5 缺失模式对象

实现：

```python
@dataclass(frozen=True)
class MissingnessPattern:
    available: tuple[str, ...]
    absent: tuple[str, ...]
    corrupted: tuple[str, ...]
    source: Literal["natural", "simulated", "unseen", "shifted"]
```

必须提供：

```python
def encode_pattern(...): ...
def enumerate_observed_patterns(...): ...
def split_seen_unseen_patterns(...): ...
def apply_modality_dropout(...): ...
def apply_modality_corruption(...): ...
def verify_no_outcome_conditioned_masking(...): ...
```

### 4.6 统一缺失和损坏场景生成器

至少实现以下场景：

| 场景 | 含义 | 是否用于训练 | 是否用于开发评价 |
|---|---|---:|---:|
| natural | 数据原生缺失 | 是 | 是 |
| MCAR | missing completely at random，完全随机缺失 | 可选增强 | 是 |
| MAR-like | missing at random-like，依赖可观测临床变量的缺失 | 可选增强 | 是 |
| block missing | 整个模态缺失 | 是 | 是 |
| unseen subset | 训练不出现的模态组合 | 否 | 是 |
| feature corruption | 噪声、缩放、置换、批次变换 | 可选增强 | 是 |
| OOD shift | 中心、平台或时间偏移 | 否 | 是 |
| shortcut control | 随机/置换/体积匹配模态 | 否 | 是 |

模拟缺失概率不得依赖结局。MAR-like 只能依赖预测时可见变量，并在配置中记录生成公式。

### 4.7 复用而非重写的现有资产

优先复用：

```text
src/trust_hn/data/adapters/hancock.py
src/trust_hn/models/survival_baselines.py
src/trust_hn/models/residual_fusion.py
src/trust_hn/reliability/gating.py
src/trust_hn/metrics/survival.py
src/trust_hn/evaluation/phase5.py 中的 stress 与 subgroup 思路
src/trust_hn/phase7/models.py 中的 Breslow 风险与 C3 后期融合
```

复用方式是调用公共 API 或抽取新模块的兼容包装器，不修改冻结决策行为。

### 4.8 依赖审计

现有 `pyproject.toml` 未包含 PyTorch。Codex 第一个深度学习任务只能生成依赖建议，不得直接安装：

```text
torch              # 张量、自动微分和神经网络
pycox              # 可选的深度生存模型参考实现
einops              # 张量重排
pytorch-lightning   # 可选训练框架；小项目可不用
```

Codex 必须输出 `docs/audits/pattern_surv_dependency_audit.md`，包含：

- 需要的最小包；
- Python 3.11 兼容性；
- CPU/GPU 版本；
- 许可证；
- 是否与现有固定依赖冲突；
- 不增加该依赖时的替代实现；
- 可复现锁定策略。

### 4.9 共同 smoke test（冒烟测试）

正式训练前只用合成数据：

- 64–128 名虚拟患者；
- 3–5 个模态；
- 随机删失；
- 至少 4 种缺失组合；
- 训练 2–5 个 epoch（轮次）；
- 检查 loss 为有限值；
- 检查全模态和子集输入形状；
- 检查置换模态顺序不改变集合输出；
- 检查完全缺少附加模态时等价于临床回退；
- 检查患者级输出位于 Git ignored 路径。

---

## 5. P1：PATTERN-Surv Core——临床锚定的任意模态集合生存学习

### 5.1 科学故事

现实 HNSCC 患者并不会整齐地拥有同一组数据。部分患者只有临床和分期，部分有血液或 TMA，少数可能有 WSI、CT、PET 或组学。现有方法常在完整病例上训练、通过随机掩蔽模拟缺失，或为固定模态组合训练不同模型。这样无法回答：

> **同一个模型能否把患者当前实际存在的模态视为证据集合，在训练未见的组合、质量损坏和中心偏移下仍输出删失感知、经过校准且可安全回退的生存风险？**

顶刊故事不是“Set Transformer 比拼接好”，而是四层贡献：

1. 从 fixed fusion（固定融合）转为 arbitrary-set survival（任意集合生存学习）；
2. 从随机删除稳健性转为 natural + unseen + corrupted + OOD 的完整测试；
3. 从平均 C-index 转为 pattern-wise calibration（缺失模式分层校准）和 clinical safety regret（临床安全遗憾）；
4. 从强制预测转为 `fuse / fallback / abstain`（融合/回退/拒绝）安全动作。

### 5.2 核心创新点

#### 创新 1：Clinical-anchor residual set fusion

临床模型先给出基础风险：

\[
r_{clin}(x_c)
\]

每个附加模态只输出 residual evidence（残余增量证据）：

\[
\Delta r_m = f_m(x_m, q_m, d_m)
\]

集合融合器只学习可靠残差：

\[
r = r_{clin} + \sum_{m \in A} w_m \Delta r_m
\]

其中 `A` 是当前可用模态集合，`w_m` 受可用性、质量、OOD 和不确定性约束。这样比无锚点拼接更容易回答“某模态是否真正带来临床增量”。

#### 创新 2：Censored pattern consistency

对同一患者的不同可用子集，不要求预测完全相等，而要求：

- 风险排序不要无理由反转；
- 删除低价值模态时变化小；
- 删除高价值模态时不确定性应增加；
- 子集预测不能比完整预测虚假地更自信；
- 约束必须考虑删失，不能把删失患者当作无事件标签。

可定义：

\[
L_{pc}=L_{rank-consistency}+\lambda_u L_{uncertainty-monotonicity}
\]

其中 uncertainty monotonicity（不确定性单调性）要求证据减少时预测方差或区间宽度不应系统下降。

#### 创新 3：Pattern-conditioned calibration

不只做全队列一次校准，而是建模：

\[
P(T \le t \mid r, p, d)
\]

其中 `p` 是模态模式，`d` 是域/平台。由于小模式样本不足，应使用 hierarchical shrinkage（层级收缩）：全局校准为主，模式校准只学习有限偏移，避免每个模式单独过拟合。

#### 创新 4：Clinical safety regret

定义附加模态相对临床模型的患者级或组级损失差：

\[
R_{safe}=L(y, \hat S_{fused})-L(y, \hat S_{clinical})
\]

目标不是让所有患者都融合，而是在保持覆盖率的同时控制最差模式的正向 regret（即融合比临床更差）。训练路由器和评价时均报告该量。

#### 创新 5：Unseen-pattern routing

当新模态组合在训练中未出现时，不直接把组合 ID 当类别，而使用：

- modality token（模态标记）；
- quality token（质量标记）；
- domain token（域标记）；
- set attention（集合注意力）；
- 对组合新颖度的 OOD 分数；
- conformal/fallback（保形风险控制/回退）规则。

这使模型有机会泛化到组合，而不是记忆有限模式。

### 5.3 两级实施版本

#### MVP：表格与预提取特征级

HANCOCK 当前可用：

- clinical/pathological（临床/病理分期）；
- blood（血液）；
- ICD（疾病编码）；
- TMA cell density（组织芯片细胞密度）；
- 部分预提取患者特征。

先完成轻量 MLP（多层感知机）或线性 adapter，避免把原始图像获取变成关键阻塞。

#### 完整版：原始图像/切片编码

获得授权和数据后再增加：

- WSI：UNI/CONCH/TITAN 等 foundation model（基础模型）提取 patch embedding（图块嵌入），再用 CLAM 或 attention-MIL（注意力多实例学习）聚合；
- CT/PET：3D CNN（3D 卷积神经网络）、Swin Transformer 或预提取 radiomics/deep embedding；
- TMA map：2D CNN 或图网络；
- omics：稀疏 MLP、pathway encoder（通路编码器）或 pathway graph（通路图）。

原始编码器与集合融合器分开冻结/解冻，以便区分“编码能力”与“缺失融合能力”。

### 5.4 网络结构

```text
每个患者的可用数据
 clinical ── ClinicalEncoder ── clinical token ───────────────┐
 blood ───── BloodAdapter ──── residual token + quality ─────┤
 pathology ─ PathAdapter ───── residual token + quality ─────┤
 ICD ─────── CodeAdapter ───── residual token + quality ─────┤
 TMA ─────── TMAAdapter ────── residual token + quality ─────┤
 WSI/CT ──── ImageAdapter ──── residual token + quality ─────┤
                                                              ↓
                                     permutation-invariant set encoder
                                                              ↓
                        ┌──────── survival ranking head ───────┤
                        ├──────── survival probability head ──┤
                        ├──────── uncertainty head ────────────┤
                        └──────── action/router head ──────────┘
                                      ↓
                           fuse / fallback / abstain
```

### 5.5 推荐类与接口

```text
src/trust_hn/pattern_surv/
  encoders.py
    ClinicalEncoder
    TabularModalityAdapter
    SparseCodeAdapter
    BagEmbeddingAdapter
    QualityEncoder
    DomainEncoder

  set_fusion.py
    DeepSetsFusion
    SetTransformerFusion
    ClinicalResidualSetFusion
    SparseExpertRouter

  survival_head.py
    CoxRiskHead
    DiscreteTimeSurvivalHead
    MultiHorizonRiskHead

  uncertainty.py
    MCDropoutUncertainty
    DeepEnsembleAggregator
    EvidenceUncertaintyHead

  distillation.py
    FullSubsetTeacher
    SubsetStudentLoss
    PatternConsistencyLoss

  calibration.py
    GlobalHorizonCalibrator
    PatternShrinkageCalibrator

  routing.py
    ReliabilityFeatures
    FuseFallbackAbstainRouter
    CoverageController
```

### 5.6 生存输出选择

第一轮实现两个头，不要一开始铺开所有生存损失：

1. **CoxRiskHead（Cox 风险头）**：输出相对风险，用 partial likelihood（部分似然）训练；
2. **DiscreteTimeSurvivalHead（离散时间生存头）**：把时间分箱，输出条件生存概率，便于多时间点校准。

主模型选择规则：

- 若 Cox 头排序更好但概率校准差，进入 P2 进行基线风险/校准分离；
- 若离散时间头稳定且事件数足够，可作为主概率模型；
- 24 个月风险只是重要时间点，不能把完整时间到事件任务降成普通二分类。

### 5.7 总损失建议

\[
L = L_{surv}
+ \lambda_{distill}L_{full\rightarrow subset}
+ \lambda_{pc}L_{pattern-consistency}
+ \lambda_{cal}L_{calibration}
+ \lambda_{safe}L_{clinical-regret}
+ \lambda_{route}L_{routing}
+ \lambda_{sparse}L_{expert-sparsity}
\]

每项含义：

- `L_surv`：删失感知生存损失；
- `L_full→subset`：完整模态教师到子集学生的蒸馏；
- `L_pattern-consistency`：同患者不同模态子集的一致性与不确定性单调性；
- `L_calibration`：在开发校准集上估计，不得用测试结局；
- `L_clinical-regret`：惩罚不可靠融合相对临床锚点的损失增加；
- `L_routing`：学习使用、回退或拒绝的动作；
- `L_expert-sparsity`：避免所有专家同时激活。

第一版只实现 `L_surv + L_distill`；只有基础模型通过后再逐项加入，确保消融可解释。

### 5.8 可借鉴但不能直接照搬的方法

| 来源 | 可借鉴模块 | 不应直接照搬的原因 |
|---|---|---|
| HAF | 异构特征对齐、随机模态掩蔽、HNSCC/HANCOCK 任务组织 | 原任务主要为 alive/dead 分类，不等于删失生存；随机缺失不足以覆盖真实偏移 |
| Multi-FRuGaL | shared/unique（共享/特异）表示、冗余感知门控、灵活模态组合 | 属预印本；需独立核验代码和设置，且本研究要增加校准与安全动作 |
| DisPro | full teacher/subset student（完整教师/子集学生）、prompt（提示标记）蒸馏 | 主要是 WSI+组学生存；需适配多于两模态及 HNSCC 自然缺失 |
| Flex-MoE | 动态 mixture-of-experts（混合专家）路由任意模态 | 通用不完整多模态方法，未针对删失、生存校准和临床回退 |
| Deep Sets | 置换不变的集合聚合 | 表达能力可能不足，作为最简神经 baseline |
| Set Transformer | 集合自注意力与模态交互 | 小样本易过拟合；必须与 Deep Sets 和简单后期融合比较 |
| CLD/条件潜变量方法 | 缺失条件下学习潜在共享证据 | 容易产生虚假确定性，必须配合不确定性和“不补全”对照 |
| pycox | Cox/离散时间损失的参考实现 | 只能借鉴生存头，不解决缺失融合和治理 |

### 5.9 P1 的 baseline 矩阵

#### 必做传统 baseline

- B0 Kaplan–Meier（卡普兰–迈耶常数风险）；
- B1 Cox PH（Cox 比例风险）；
- B2 Clinical elastic-net Cox（临床弹性网 Cox）；
- B3 Random Survival Forest（随机生存森林）；
- B5 direct fusion；
- B6 clinical residual fusion；
- C3 cross-fitted late fusion；
- C4 missing-indicator direct fusion（显式缺失指示直接融合）。

#### 缺失模态 baseline

- Separate model per pattern（每种模式单独模型，仅对样本足够的模式）；
- Zero/mean imputation + MLP（零/均值填补加 MLP）；
- Modality dropout MLP（模态丢弃 MLP）；
- Deep Sets survival；
- HAF-Surv；
- 可复现时加入 DisPro adaptation（DisPro 适配）和 Flex-MoE survival adaptation。

#### Proposed 阶梯

- P1-A：Deep Sets + Cox；
- P1-B：Set Transformer + Cox；
- P1-C：Clinical residual set fusion；
- P1-D：P1-C + full-to-subset distillation；
- P1-E：P1-D + quality/OOD tokens；
- P1-F：P1-E + pattern calibration + action router。

### 5.10 HANCOCK 主协议

建议保留官方 training 611 / OOD test 152 的边界。在新的 post-lock 探索中：

- 只在 611 内重新建立开发 train/calibration 或交叉验证；
- 152 已经在 Phase 6 被看过，若再次评价必须明确标注 post hoc exploratory external/OOD comparison；
- 不能再将其称为“从未看过的锁定测试”；
- 所有模型选择只依赖 611 的开发结果；
- 152 仅用于最终选定模型的探索性泛化描述，不用于回调。

开发建议：

```text
official training 611
  ├─ model development train ≈489
  └─ calibration/selection ≈122

official OOD test 152
  └─ post-lock exploratory evaluation only
```

必须按患者、事件率、主要部位、HPV/p16（如可用）和自然缺失模式审计拆分平衡。

### 5.11 Codex 逐步任务

#### P1.0：数据与治理审计

**要做：**

1. 读取 HANCOCK adapter 和当前 processed artifact；
2. 生成模态可用性矩阵；
3. 统计每种自然模式人数、事件数、随访和 24 个月可评价人数；
4. 标记小样本模式；
5. 检查所有候选特征的预测时可得性；
6. 输出依赖审计，不安装深度学习依赖。

**新增输出：**

```text
docs/audits/pattern_surv_hancock_data_audit.md
trust-hn/results/metrics/pattern_surv/hancock_pattern_counts.csv
trust-hn/results/metrics/pattern_surv/hancock_modality_availability.csv
```

CSV 只能是聚合计数，不含患者 ID。

**验收：**总人数、事件数和各模态人数与当前审计一致；模式计数之和等于队列人数；无结局字段进入候选特征。

**建议 commit：**

```text
chore(pattern-surv): add HANCOCK modality-pattern and dependency audits
```

#### P1.1：实现最小集合式生存 baseline

**要做：**

- 实现 `TabularModalityAdapter`；
- 实现 `DeepSetsFusion`；
- 实现 `CoxRiskHead`；
- 构建合成数据测试；
- 验证模态顺序置换不改变输出；
- 与 B2、B5、B6、C3 在开发交叉验证比较。

**新增文件：**

```text
src/trust_hn/pattern_surv/encoders.py
src/trust_hn/pattern_surv/set_fusion.py
src/trust_hn/pattern_surv/survival_head.py
src/trust_hn/pattern_surv/trainer.py
scripts/train_pattern_surv.py
tests/test_pattern_surv_models.py
```

**No-go：**若无法在合成数据过拟合小批次，或模态顺序影响输出，则禁止跑正式数据。

**建议 commit：**

```text
feat(pattern-surv): add permutation-invariant survival baseline
```

#### P1.2：加入临床锚定残差融合

**要做：**

- 临床 encoder 独立产生锚点风险；
- 每个附加模态只产生 residual token；
- 对完全无附加模态的患者强制输出临床风险；
- 对低质量模态允许 residual 权重接近 0；
- 比较无锚点 Set Transformer 与锚定模型。

**关键测试：**

```text
只有 clinical → fused risk == clinical risk（数值容差内）
附加模态全 mask → 不产生 NaN
交换附加模态顺序 → 输出不变
训练期间 clinical anchor 是否冻结由配置明确控制
```

**建议 commit：**

```text
feat(pattern-surv): implement clinically anchored residual set fusion
```

#### P1.3：实现 seen/unseen pattern 协议

**要做：**

- 根据开发队列模式频率选择 2–4 个有足够样本的组合作为 unseen；
- 训练时完全不出现这些组合，但允许出现其单个模态；
- 分开评价 seen、unseen、自然稀有模式；
- 报告 pattern frequency 与性能关系；
- 防止把 unseen 选择成结果最有利的模式：规则写入配置并哈希。

**输出：**

```text
configs/pattern_surv/unseen_pattern_protocol.yaml
results/metrics/pattern_surv/pattern_generalization.csv
results/figures/pattern_surv/performance_by_pattern_frequency.svg
```

#### P1.4：完整模态到子集蒸馏和模式一致性

**要做：**

- 仅对训练集中有较完整证据的患者训练 teacher；
- 对同一患者采样多个子集；
- student 学习删失损失和 teacher 的风险/生存分布；
- 蒸馏温度、权重只在开发数据选择；
- 增加“不蒸馏”“风险蒸馏”“生存曲线蒸馏”三种消融。

**风险控制：**teacher 不一定更正确。只有当 teacher 在开发交叉验证中优于 clinical 和简单融合，才允许作为监督信号；否则停止蒸馏分支。

#### P1.5：可靠性特征与安全动作

可靠性输入至少包括：

- 模态可用性；
- 模态内部缺失比例；
- adapter embedding norm（嵌入范数）；
- TripleOODDetector 的 Mahalanobis/kNN/Isolation Forest 分数；
- 深度 ensemble disagreement（集成分歧）；
- 模式训练频率；
- fused 与 clinical 风险差；
- 模态删除敏感度。

动作：

```text
FUSE     使用融合模型
FALLBACK 回退临床模型
ABSTAIN  不给出自动绝对风险，提示人工复核
```

动作阈值只能在 calibration split 确定。评价必须报告：

- coverage；
- 同覆盖率下的 Brier/C-index；
- risk–coverage curve（风险—覆盖率曲线）；
- 各动作人数和事件数；
- clinical safety regret；
- 最差模式表现。

#### P1.6：正式开发评价与统计

主指标：

- Uno C-index（Uno 一致性指数）；
- 24 个月 IPCW Brier；
- integrated Brier score（综合 Brier，如时间范围可支持）；
- 24 个月 time-dependent AUC（时间依赖 AUC）；
- calibration-in-the-large（总体校准偏移）；
- calibration slope（校准斜率）。

次指标：

- decision curve（决策曲线）；
- worst-pattern Brier；
- pattern performance gap；
- full-to-subset degradation；
- unseen-pattern regret；
- risk–coverage area；
- uncertainty monotonicity violation rate（不确定性单调违反率）。

统计：

- 患者级 paired bootstrap（配对自助法）；
- 建议 1,000–2,000 次；
- 同一 bootstrap 样本同时计算两模型差异；
- 报告点估计、95% CI（置信区间）和绝对差；
- 多个次要比较以效应量和 CI 为主，不做选择性显著性叙事。

### 5.12 P1 消融表

| 消融 | 回答的问题 |
|---|---|
| 无 clinical anchor | 临床锚定是否真正减少负迁移 |
| Deep Sets vs Set Transformer | 改善来自集合不变性还是复杂交互 |
| 无 modality identity token | 模型是否需要知道模态类型 |
| 无 quality token | 质量信息是否帮助损坏模态 |
| 无 OOD token | 分布异常信息是否有增量 |
| 无 distillation | 教师—学生是否减少子集退化 |
| 无 pattern consistency | 同患者多子集约束是否有用 |
| 无 calibration layer | 性能是否只来自后处理 |
| 强制融合 vs router | 安全动作是否控制临床 regret |
| learned router vs fixed threshold | 学习路由是否优于透明规则 |

### 5.13 P1 Go/no-go

**进入完整模型的 Go 条件：**

- 简单集合模型在至少一个预设缺失场景较 B5/C3 有稳定改进，或明显减少最差模式退化；
- 临床锚定不会在 clinical-only 场景劣于 B2；
- unseen pattern 的性能下降可被复现且新机制有合理改善；
- 改善不是由低覆盖或删去困难患者造成；
- 模型结果对至少 3–5 个种子稳定。

**停止加复杂度的 No-go 条件：**

- 只有训练分数提高而开发交叉验证不提高；
- 不确定性与误差无关联；
- router 实质上总是 FUSE 或总是 FALLBACK；
- 改善只存在于一个极小模式且 CI 极宽；
- 负对照与真实模态表现接近；
- 校准显著恶化且无法用独立 calibration split 修复。

### 5.14 P1 成功与阴性结果叙事

**理想成功：**在总体判别不下降的前提下，PATTERN-Surv 减少未见模式和损坏模态下的 Brier/校准退化，并通过回退控制相对临床模型的安全 regret。

**平均性能不提高但仍有价值：**证明复杂任意模态模型的平均优势有限，但模式分层评价揭示固定融合在特定自然缺失组合中不安全；一个透明路由规则可降低最差组失败。

**完全阴性：**如果 B2/B5/C3 在所有场景均不劣，则应报告在当前样本量和表格模态条件下，深度任意集合模型没有足够证据优于简洁模型，并把后续重点转向更高信息量的原始 WSI/CT 或 P2 校准迁移。

---

## 6. P2：CALIB-Bridge——跨平台生存排序与绝对风险迁移解耦

### 6.1 为什么优先级高

当前 TCGA-HNSC → GSE65858 的结果已经暴露一个比“缺失模态”更尖锐的问题：模型可能保留部分 relative ranking（相对排序）能力，却把 absolute risk（绝对风险）严重高估或低估。RNA-seq 与 microarray 的特征分布、动态范围、探针映射、病例构成和基线风险都可能不同。

因此科学问题是：

> **跨平台迁移时，哪些信息可以零样本迁移：风险排序、特征表示还是完整生存曲线？能否把共享排序表示与目标域基线风险/校准适配器分开，并在目标域校准数据不足时触发临床回退？**

这一方案计算量低于完整多模态 Transformer，且直接承接已观察到的外部失败，适合作为快速、高价值的第二主线。

### 6.2 顶刊故事

常见研究只报告外部 C-index，并把仍有排序能力解释为“外部验证成功”。但临床使用需要某一时间点的绝对死亡风险。CALIB-Bridge 的主张应是：

1. 系统拆分 ranking transport（排序迁移）与 probability transport（概率迁移）；
2. 比较 zero-shot（零样本）、小样本 recalibration（重新校准）和轻量 domain adaptation（域适配）；
3. 给出目标域校准样本量曲线，回答需要多少事件才能恢复可用概率；
4. 当目标域不支持可靠校准时，模型应输出排序或回退，而不是伪装成准确绝对风险。

### 6.3 模型设计

```text
source omics + clinical
        ↓
Shared Rank Encoder（共享排序编码器）
        ↓
relative risk score η
        ├──────── source baseline hazard H0_source(t)
        ├──────── target baseline hazard adapter H0_target(t)
        ├──────── horizon calibration adapter g_target(η, t)
        └──────── OOD/reliability → use / recalibrate / fallback
```

#### 模块 A：共享排序编码器

可选实现：

- elastic-net Cox；
- sparse MLP Cox；
- pathway-level encoder + Cox；
- domain-adversarial representation（域对抗表示，仅在足够样本时）。

第一版必须冻结 source encoder，只适配目标域基线风险，以避免把目标测试变成调参集。

#### 模块 B：目标域基线风险适配

比较：

- Source Breslow baseline（源域 Breslow 基线风险直接迁移）；
- Target Breslow recalibration（目标域 Breslow 重新估计）；
- intercept-only horizon calibration（仅截距校准）；
- slope + intercept calibration（斜率加截距）；
- isotonic calibration（保序校准，样本足够时）；
- hierarchical/domain adapter（层级域适配器）。

#### 模块 C：校准可信度

根据目标 calibration set（校准集）的样本数、事件数和 bootstrap 不确定性，决定：

- `FULL_RISK`：输出绝对风险；
- `RANK_ONLY`：仅输出相对风险分层，不宣称准确概率；
- `CLINICAL_FALLBACK`：回退临床模型；
- `ABSTAIN`：证据不足。

### 6.4 数据协议

候选生态：

- source：TCGA-HNSC；
- target：GSE65858；
- sensitivity target：GSE41613；
- 后续可能加入 CPTAC-HNSCC，但需先核验结局、样本重叠、组学平台和许可。

关键审计：

1. endpoint definition（结局定义）是否一致；
2. 诊断到生存时间的起点是否一致；
3. gene identifier（基因标识）映射是否一对多；
4. RNA-seq 与 microarray 的共同特征数；
5. batch correction（批次校正）是否使用目标结局；
6. 目标 calibration/test 的患者级独立性；
7. 小队列事件数是否支持斜率估计。

### 6.5 校准集大小实验

在 target cohort 内建立重复的 calibration/test 划分，仅使用 calibration 部分拟合适配器。预设大小：

```text
n = 0, 10, 20, 40, 80, 或按 10/20/40% 比例
```

更推荐按事件数报告：

```text
0、5、10、20、40 个目标域事件
```

每个大小重复多个固定种子，绘制：

- calibration-set events vs Brier；
- calibration-set events vs calibration slope；
- calibration-set events vs CI width；
- ranking 指标是否在校准前后基本不变。

### 6.6 Codex 文件级任务

```text
trust-hn/configs/calib_bridge/
  protocol.yaml
  feature_mapping.yaml
  calibration_sizes.yaml

trust-hn/src/trust_hn/calib_bridge/
  contracts.py
  feature_alignment.py
  rank_encoder.py
  baseline_hazard.py
  horizon_calibration.py
  domain_adapter.py
  reliability.py
  evaluator.py

trust-hn/scripts/
  audit_calib_bridge_data.py
  run_calib_bridge.py

trust-hn/tests/
  test_calib_bridge_alignment.py
  test_calib_bridge_hazard.py
  test_calib_bridge_no_target_leakage.py
  test_calib_bridge_calibration_split.py
```

### 6.7 Codex 执行步骤

#### P2.0：端点和特征交集审计

输出：

```text
docs/audits/calib_bridge_endpoint_feature_audit.md
results/metrics/calib_bridge/cohort_alignment_summary.csv
```

必须记录基因映射版本、重复探针聚合规则和所有排除人数。无可靠结局对齐则 No-go。

#### P2.1：复现未经适配的失败

锁定 source 模型，输出 target：

- Uno C-index；
- IPCW Brier；
- calibration intercept/slope；
- 预测风险分布与观察事件率；
- 不进行任何目标结局适配。

目的不是再次挑模型，而是建立“排序与概率可分离”的现象。

#### P2.2：实现轻量重新校准

按复杂度递增：

1. 目标域 baseline hazard；
2. intercept-only；
3. intercept+slope；
4. isotonic；
5. 小型 domain adapter。

每个方法只在 target calibration split 拟合，并在其独立 test split 评价。

#### P2.3：校准样本量曲线

重复抽样必须分层保留事件，输出平均值、95% 区间和失败次数。若某种方法在小事件数下数值不稳定，必须报告而非悄悄删除。

#### P2.4：OOD 触发动作

复用 `TripleOODDetector`，但不能假设其能识别平台漂移。比较：

- 原始特征 OOD；
- rank embedding OOD；
- calibration residual OOD；
- 平台已知指示；
- 组合 reliability score。

验证 OOD 分数是否与绝对风险误差相关，而不仅是能否分类 source/target。

### 6.8 Baseline

- Clinical Cox；
- source-only omics Cox；
- ComBat/standardization + Cox（仅在无结局批次处理下）；
- direct source survival transfer；
- target intercept recalibration；
- target intercept+slope；
- target-only model（仅作为有足够样本时的上界/参照）；
- B6/B7 当前实现；
- CALIB-Bridge full。

### 6.9 创新性边界

单独做 Breslow 重新估计不够 novel。论文级创新必须组合：

- 排序/概率迁移的明确分解；
- 目标事件数—校准恢复曲线；
- 域适配不确定性；
- `FULL_RISK / RANK_ONLY / FALLBACK` 动作；
- 多个外部平台或至少一个外部加一个敏感性队列；
- 与缺失/不可靠组学的临床锚定联系。

### 6.10 Go/no-go

**Go：**排序在 target 仍有信息，但绝对风险失真；小样本校准能稳定降低 Brier 且不破坏排序。

**转向方法学边界论文：**所有适配器在小事件数下不稳定，但可清楚展示“外部 C-index 尚可不能代表绝对风险可用”。

**No-go：**source 排序在 target 完全无效，且临床模型也无法对齐；这时问题不只是校准，需回到 endpoint/feature harmonization（结局/特征协调），不能继续宣称 CALIB-Bridge 可解决。

### 6.11 建议 commits

```text
chore(calib-bridge): audit cross-platform endpoints and feature alignment
feat(calib-bridge): separate survival ranking from baseline-risk adaptation
feat(calib-bridge): add target-event calibration size experiments
feat(calib-bridge): add reliability-aware risk reporting actions
```

---

## 7. P3：SHORTCUT-FAILSAFE——缺失、无效模态与捷径联合建模

### 7.1 科学故事

缺失模态研究通常假设：只要模态存在，它就是真实、有效和值得融合的。但 RADCURE 结果提示，影像组学可能主要反映肿瘤体积、扫描流程、中心或随机结构；“存在”不等于“可靠”。

核心问题：

> **模型能否区分真正增加预后信息的影像证据和仅靠体积、中心、处理流程或随机特征产生的表面性能，并在后者出现时自动回退临床模型？**

这比单纯模态缺失更接近现实失效：错误模态不会以空值出现，而会以看似正常的向量进入系统。

### 7.2 创新点

#### 创新 1：Negative-control-aware training

训练与验证中显式引入：

- patient permutation（患者间置换）；
- random Gaussian embedding（随机高斯嵌入）；
- volume-only representation（仅体积表示）；
- volume-matched random representation（体积匹配随机表示）；
- center/scanner proxy（中心/设备代理）；
- feature corruption（特征损坏）。

目标不是让模型在训练时“识别标签为假”，而是学习真实模态相对临床锚点的可重复增量，并限制对已知捷径参考的依赖。

#### 创新 2：Evidence branch 与 shortcut branch 解耦

```text
Radiomics/CT embedding
        ├─ EvidenceEncoder ── prognostic residual
        └─ ShortcutEncoder ─ volume/center/device residual
                      ↓
orthogonalization / HSIC / adversarial penalty
                      ↓
Reliability Router → FUSE or FALLBACK
```

可选约束：

- residualization（残差化）：先预测 volume/center，再使用剩余表示；
- orthogonality penalty（正交惩罚）；
- HSIC，Hilbert-Schmidt independence criterion（希尔伯特–施密特独立性准则）；
- adversarial removal（对抗移除中心/设备信息）；
- counterfactual substitution（反事实替换）。

#### 创新 3：Value-over-anchor 预测

路由器直接学习：

> 在不看测试结局的情况下，这个影像对该患者是否可能优于 `clinical + volume` 锚点？

开发时可用 out-of-fold（折外）误差差构造软监督；必须 cross-fitting（交叉拟合），避免用同一患者训练模型和定义其增益标签。

### 7.3 方法结构

基准锚点建议为：

```text
clinical-only
clinical + tumor volume
clinical + conventional radiomics
```

候选模型：

\[
r=r_{clinical+volume}+g(q,o,u)\cdot \Delta r_{image-residual}
\]

其中：

- `q`：图像/特征质量；
- `o`：OOD 分数；
- `u`：不确定性；
- `g`：0–1 门控权重。

### 7.4 Codex 文件级任务

```text
trust-hn/configs/shortcut_failsafe/
  protocol.yaml
  negative_controls.yaml

trust-hn/src/trust_hn/shortcut_failsafe/
  controls.py
  residualization.py
  dependence.py
  models.py
  value_router.py
  evaluator.py

trust-hn/scripts/
  audit_radcure_shortcuts.py
  run_shortcut_failsafe.py

trust-hn/tests/
  test_shortcut_controls.py
  test_shortcut_permutation.py
  test_shortcut_crossfit.py
  test_shortcut_router.py
```

### 7.5 Codex 执行步骤

#### P3.0：复用并冻结当前负对照协议

- 定位 Phase 3/5 中 RADCURE 的真实、shuffled（置换）和 randomized（随机）特征；
- 不修改原结果；
- 在新配置中复制定义和哈希；
- 增加 volume-only 与 volume-matched 对照；
- 输出每个对照的维度、生成种子和是否保留边缘分布。

#### P3.1：建立 `clinical + volume` 强锚点

只有在影像模型明确优于该锚点时，才能写“影像提供超越体积的增量信息”。需要 paired bootstrap 差异，而非只比较点估计。

#### P3.2：实现捷径分支

从最可解释方法开始：

1. 线性 residualization；
2. 正交惩罚；
3. HSIC；
4. 对抗移除中心/设备。

若 1 已达到最好，不能因深度方法更复杂而优先选择 4。

#### P3.3：反事实模态替换

对同一 clinical 输入，分别配对：

- 真实影像；
- 其他患者影像；
- 随机影像向量；
- 同体积区间影像；
- 加噪/缩放影像。

评价风险变化是否符合预期，并检查 router 是否在假模态下更多 FALLBACK。

#### P3.4：训练 value router

- 用开发折外预测计算 `loss_fused - loss_anchor`；
- 只使用预测时可见可靠性特征预测增益；
- calibration split 决定动作阈值；
- test 仅评价。

#### P3.5：完整压力测试

报告：

- 真实模态相对所有负对照的差异；
- shortcut probe（捷径探针）预测中心/体积的能力；
- 移除捷径前后的生存表现；
- router 在真实、置换、随机和损坏模态下的动作比例；
- coverage-matched Brier；
- clinical safety regret。

### 7.6 Baseline

- clinical Cox；
- clinical + volume；
- radiomics only；
- clinical + radiomics；
- B6/B7；
- residualized radiomics；
- adversarial/HSIC model；
- random/permuted/volume-only negative controls；
- SHORTCUT-FAILSAFE full。

### 7.7 Go/no-go

**强成功：**真实影像显著优于体积和随机/置换对照，且捷径抑制后跨场景更稳定。

**可信阴性成功：**真实影像不优于负对照，但 router 能可靠识别无效模态并回退，说明“对存在但无效的模态安全失败”是主要贡献。

**No-go：**router 无法区分真实与随机模态，可靠性分数与误差无关，且所有模型均不优于 clinical+volume；停止复杂影像建模，报告负结果并等待原始 CT 或更好的表示。

### 7.8 建议 commits

```text
chore(shortcut-failsafe): register RADCURE negative-control protocol
feat(shortcut-failsafe): add volume-anchored residual imaging model
feat(shortcut-failsafe): add counterfactual modality substitution tests
feat(shortcut-failsafe): route unreliable imaging evidence to fallback
```

---

## 8. P4：U-Latent Evidence Completion——带不确定性的潜在证据补全

### 8.1 为什么是高风险高收益

多数 missing modality completion（缺失模态补全）工作试图生成缺失图像或一个确定性向量。医学上这可能制造并不存在的“患者证据”，并给出过度自信预测。

本方案不生成可解释为真实 CT/WSI 的原始图像，而只生成用于预测的 latent evidence distribution（潜在证据分布）：

> **在缺少某模态时，模型能否根据已有模态生成多个可能的潜在证据样本，将补全不确定性传播到生存预测，并在不确定性过高时选择不补全或回退？**

### 8.2 创新点

1. **Evidence completion, not image synthesis（补全证据而非合成图像）**；
2. 条件生成输出分布而非单一点估计；
3. 补全方差进入 survival uncertainty（生存不确定性）；
4. 与 no-completion（不补全）和 deterministic completion（确定性补全）严格比较；
5. 高不确定时禁止补全主导风险；
6. 使用 clinical anchor 限制 hallucinated benefit（幻觉式增益）。

### 8.3 方法候选

按复杂度排序：

1. Mean token（训练均值标记）；
2. Deterministic MLP imputer（确定性 MLP 补全器）；
3. Conditional VAE，CVAE（条件变分自编码器）；
4. Mixture density network（混合密度网络）；
5. Latent diffusion（潜在扩散模型，仅在样本量与算力支持时）。

不要默认 diffusion（扩散模型）最先进就一定最好。HANCOCK 样本量较小，CVAE 或 mixture model 更现实。

### 8.4 网络结构

```text
Available modality set Z_A
        ↓
Set Context Encoder
        ↓
q(z_missing | Z_A, pattern, domain)
        ↓ sample K latent evidence tokens
{z_missing^(1), ..., z_missing^(K)}
        ↓
Clinical-anchored survival model
        ↓
mean risk + epistemic/aleatoric completion uncertainty
        ↓
use completion / ignore completion / fallback
```

### 8.5 损失

\[
L = L_{surv}
+ \lambda_{rec}L_{latent-reconstruction}
+ \lambda_{KL}D_{KL}(q\|p)
+ \lambda_{cons}L_{subset-consistency}
+ \lambda_{safe}L_{clinical-regret}
\]

注意：重建损失不能成为唯一目标。能重建 embedding 不等于能保留生存相关信息；必须评价下游风险和校准。

### 8.6 Codex 文件级任务

```text
trust-hn/configs/u_latent/
  protocol.yaml
  completion_models.yaml

trust-hn/src/trust_hn/u_latent/
  context_encoder.py
  deterministic.py
  cvae.py
  sampling.py
  uncertainty.py
  integration.py
  evaluator.py

trust-hn/scripts/
  audit_u_latent_pairs.py
  train_u_latent.py
  evaluate_u_latent.py

trust-hn/tests/
  test_u_latent_sampling.py
  test_u_latent_no_missing_case.py
  test_u_latent_uncertainty.py
  test_u_latent_fallback.py
```

### 8.7 Codex 执行步骤

#### P4.0：可学习性审计

统计每一对模态的共同可用患者数和事件数，输出共现矩阵。若某缺失模态几乎没有 paired observations（配对观测），不能训练可靠条件生成器。

#### P4.1：建立“不补全”上界/下界

比较：

- clinical only；
- available-set model；
- oracle full modality（仅完整病例参照，不能代表部署性能）；
- mean token；
- deterministic MLP。

只有确定性补全有信号且不明显恶化校准，才进入概率补全。

#### P4.2：CVAE 潜在补全

- 训练期使用真实配对模态；
- 验证时人为隐藏一个已知模态，评价潜在重建和生存性能；
- test 的自然缺失患者没有重建真值，只评价预测；
- 避免使用测试完整样本选择模型。

#### P4.3：多样本不确定性

对每位患者采样 K=10/20/50 个潜在证据，报告：

- 平均预测风险；
- completion variance（补全方差）；
- 风险区间；
- 方差与预测误差关系；
- K 的稳定性。

#### P4.4：安全集成

若补全方差或 OOD 超阈值：

```text
ignore generated token
→ use observed-set PATTERN-Surv
→ if observed set also unreliable, clinical fallback/abstain
```

### 8.8 Baseline

- no completion；
- mean/zero token；
- deterministic regression；
- KNN imputation（近邻填补）；
- CVAE；
- 可行时 conditional diffusion；
- DisPro/CLD 风格潜在方法适配；
- U-Latent + uncertainty gating。

### 8.9 Go/no-go

**Go：**概率补全在多个缺失模式下优于 no-completion 和 deterministic completion，且改善不是以更差校准为代价；不确定性与误差显著相关。

**No-go：**补全模型只提高 embedding 重建而不提高生存评价；生成方差与误差无关；或补全导致过度自信。此时论文不应宣传生成式补全，应保留 P1 observed-set 模型。

### 8.10 建议 commits

```text
chore(u-latent): audit paired modality support for latent completion
feat(u-latent): add deterministic missing-evidence baselines
feat(u-latent): implement probabilistic latent evidence completion
feat(u-latent): propagate completion uncertainty to survival fallback
```

---

## 9. P5：ACQUIRE-HN——成本感知动态模态获取（可选扩展）

### 9.1 科学问题

在患者已有临床资料时，下一步最值得获取的是血液、病理、CT、PET、WSI 还是组学？什么时候继续检查带来的信息增益不值得成本、时间和侵入性？

这可建模为 value of information（信息价值）问题：

```text
current modalities → estimate expected benefit of each unavailable modality
                  → acquire one / stop / abstain
```

### 9.2 不作为当前主推的原因

- 公开数据通常缺少真实检查费用、周转时间和临床采集顺序；
- 缺失原因可能与医院流程和疾病严重程度相关；
- 仅使用人为成本会使临床故事过于模拟化；
- 小样本下 reinforcement learning（强化学习）容易不稳定。

### 9.3 何时升级为正式方案

至少满足一个条件：

- 获得临床专家提供的成本/侵入性等级；
- 数据含真实采集时间与检查顺序；
- P1 已证明不同模态的患者特异价值可被可靠估计；
- 能在两个数据生态验证成本—性能 Pareto frontier（帕累托前沿）。

### 9.4 最小实现

不要首先用深度强化学习。先做：

- greedy value-of-information（贪心信息价值）；
- contextual bandit（上下文多臂赌博机）；
- oracle upper bound（预言机上界）；
- random acquisition（随机获取）；
- fixed clinical workflow（固定临床流程）。

输出：平均获取成本、C-index/Brier、覆盖率、每种模态被选择频率和亚组公平性。

---

## 10. 可调研和借鉴的相近科研问题、网络与公开代码

### 10.1 借鉴原则

Codex 调研外部方法时，先建立方法卡，不得直接复制代码。每个项目记录：

```text
paper title
publication status: journal / conference / preprint
publication year
clinical task
data modalities
missingness setting
outcome and censoring treatment
split level
loss
metrics
external validation
repository URL
license
last verified date
reusable module
known mismatch with our task
```

任何外部仓库：

- 先核验许可证；
- 先检查患者级拆分和潜在泄漏；
- 优先独立重实现小模块；
- 若必须保存代码，放在独立 `third_party/` 并保留许可证，不修改冻结主代码；
- 预训练权重和大数据不提交 Git；
- 网络下载需明确批准；
- 截至 2026-08-12 的论文状态需在真正使用前再次核验。

### 10.2 首要参考矩阵

| 方法/资源 | 任务 | 可借鉴内容 | 在本项目中的角色 |
|---|---|---|---|
| HAF / `zz9tf/HAF` | HANCOCK 七模态，缺失模态，主要 alive/dead 分类 | 异构对齐、模态掩蔽、UNI+CLAM 特征链 | 最直接 HNSCC baseline；适配为 HAF-Surv |
| DisPro / `Innse/DisPro` | 不完整 WSI+组学生存 | teacher/student、prompt 蒸馏、离散生存 | P1 蒸馏和 P4 潜在证据参考 |
| Multi-FRuGaL | HANCOCK 灵活模态生存预印本 | shared/unique 表示、冗余门控 | 最新竞争方法；先核验实现与状态 |
| Tian 等 npj DM 2025 | HNSCC clinical+CT+pathology 生存 | 各模态风险分数后期 Cox 融合 | C3 文献 baseline 和简单强融合参照 |
| NSCLC 不完整多模态生存 npj DM 2026 | clinical/PET/CT 缺失生存 | 患者相似性图、edge attention（边注意力） | 邻近癌种验证“缺失模式图”思路，不可称 HNSCC 证据 |
| Flex-MoE / `UNITES-Lab/flex-moe` | 通用任意不完整多模态 | 动态专家路由和组合泛化 | P1 sparse expert router 参考 |
| Set Transformer | 集合建模 | permutation-invariant attention | P1 核心融合 baseline |
| Deep Sets | 集合建模 | sum/mean pooling 的置换不变性 | 最简神经 baseline |
| CLAM | WSI 多实例学习 | attention-MIL 聚合 | 获得 WSI 后的编码器 |
| UNI/CONCH/TITAN | 病理基础模型 | patch/slide embedding | 完整版图像特征，需核验许可和获取 |
| scikit-survival | 传统生存模型与指标 | Cox、RSF、GBSA、Uno C、Brier | 继续复用现有工程 |
| pycox | 深度生存学习 | Cox/LogisticHazard/DeepHit 类损失 | 仅作生存头参考 |

### 10.3 还应定向调研的研究问题

#### A. Seen/unseen missing pattern generalization

检索重点：

- arbitrary missing modality learning（任意缺失模态学习）；
- unseen modality combinations（未见模态组合）；
- missing modality prompts（缺失模态提示）；
- modality-agnostic transformer（模态无关 Transformer）；
- conditional computation（条件计算）。

要提取：训练掩蔽策略、是否评估未见组合、组合数量增长时如何扩展、是否需要每组合一个模型。

#### B. Multimodal survival with censoring

检索重点：

- incomplete multimodal survival；
- WSI genomics survival distillation；
- multimodal Cox mixture-of-experts；
- discrete-time multimodal survival；
- graph multimodal survival missing data。

要审计：是否真的删失感知，还是把固定时间生存状态当分类。

#### C. Selective prediction and abstention

检索重点：

- selective prediction survival analysis（生存分析选择性预测）；
- conformal survival prediction（保形生存预测）；
- risk-coverage survival；
- uncertainty calibration censored data（删失数据不确定性校准）。

借鉴目标：覆盖率控制、风险区间、拒绝机制。必须检查保形方法对 independent censoring（独立删失）等假设。

#### D. Domain adaptation and survival calibration

检索重点：

- transportability of survival models（生存模型可迁移性）；
- recalibration baseline hazard；
- external validation survival calibration；
- platform shift transcriptomics survival；
- domain-specific baseline hazard。

借鉴目标：P2 的排序/概率分解和小样本校准，而不是只做对抗域适配。

#### E. Shortcut learning in medical imaging

检索重点：

- shortcut learning radiomics；
- negative controls imaging biomarkers；
- center/scanner confounding；
- tumor volume confounding survival；
- counterfactual multimodal evaluation。

借鉴目标：P3 的负对照、捷径探针、体积锚点和反事实替换。

#### F. Uncertainty-aware missing modality generation

检索重点：

- probabilistic modality imputation；
- conditional VAE missing modality；
- latent diffusion multimodal completion；
- multiple imputation deep survival；
- uncertainty propagation survival prediction。

借鉴目标：P4 的分布式补全和多样本预测；必须有 no-completion 对照。

### 10.4 外部代码适配审查清单

在写 adapter 前，Codex 必须回答：

1. 原代码输入是患者级向量、token、图像还是 bag？
2. 输出是分类概率、风险分数还是完整生存曲线？
3. 删失患者如何进入 loss？
4. split 是患者级还是图块级？
5. 标准化、SVD、特征选择是否在折内拟合？
6. 缺失是随机生成还是真实缺失？
7. 是否为每种组合训练独立模型？
8. 是否需要完整模态 teacher，部署时是否可用？
9. 代码许可证是否允许重用？
10. 依赖是否与 Python 3.11 和本项目冲突？
11. 是否需要不可公开权重或私有数据？
12. 哪个最小模块可以独立重实现并用合成数据验证？

---

## 11. 统一评价、统计与报告协议

### 11.1 主要结果层级

#### 一级：全覆盖预测

所有患者都必须有结果，比较：

- Clinical anchor；
- 最强简单融合；
- 最强缺失模态 baseline；
- Proposed。

#### 二级：按自然缺失模式

每个模式报告：人数、事件数、C-index、Brier、校准和 CI。样本过小的模式合并为“稀有模式”，规则预设。

#### 三级：seen/unseen 和损坏模态

分开报告：

- seen clean；
- seen corrupted；
- unseen clean；
- unseen corrupted；
- domain shifted。

#### 四级：选择性预测

对多个预设 coverage（如 100%、95%、90%、80%）画 risk–coverage。比较必须在同一保留子集或做明确 matched-coverage（匹配覆盖率）分析。

### 11.2 必须报告的指标

| 类别 | 指标 | 解释 |
|---|---|---|
| 排序 | Harrell C、Uno C | 风险排序一致性；Uno C 更重视删失校正 |
| 固定时间判别 | time-dependent AUC | 某时间点区分发生/未发生事件能力 |
| 概率误差 | IPCW Brier | 删失加权概率误差，越低越好 |
| 全时间误差 | integrated Brier | 时间区间内综合概率误差 |
| 校准 | calibration-in-the-large | 整体高估/低估 |
| 校准 | calibration slope | 预测是否过度极端或不足 |
| 临床价值 | decision curve | 不同阈值下的净获益 |
| 缺失鲁棒性 | full-to-subset degradation | 从完整到子集的性能下降 |
| 公平/安全 | worst-pattern performance | 最差缺失模式表现 |
| 安全路由 | coverage、risk–coverage | 拒绝预测后的覆盖与误差 |
| 锚点比较 | clinical safety regret | 融合相对临床模型增加的损失 |
| 不确定性 | error–uncertainty association | 不确定性是否能识别错误 |

### 11.3 推荐新增聚合输出 schema

```text
study
analysis_label
model
seed
split
pattern_group
shift_type
coverage_target
coverage_observed
n_patients
n_events
metric
estimate
ci_lower
ci_upper
comparator
difference
```

患者级预测另存 Git-ignored：

```text
results/predictions/<study>/<run_id>/predictions.parquet
```

### 11.4 训练和模型选择

- 所有预处理、特征选择、SVD、校准和阈值均在训练/校准内拟合；
- 随机种子建议至少 `[17, 29, 43, 71, 101]`；
- 小样本优先 nested or repeated cross-validation（嵌套或重复交叉验证）；
- early stopping（早停）只能看开发验证损失；
- 模型选择应基于预设综合规则，而不是挑最好单指标：

```text
1. 不劣于 clinical anchor 的全覆盖 Brier；
2. 在 Uno C 或 Brier 至少一项有临床可解释改进；
3. 不显著恶化校准；
4. worst-pattern 和 unseen-pattern 不出现严重负迁移；
5. 结果对种子稳定；
6. 复杂度相对收益合理。
```

### 11.5 Bootstrap 与亚组

- bootstrap 必须按患者抽样；
- 多切片/多病灶患者保持整体；
- 亚组需有足够人数和事件，否则只描述不比较；
- 候选亚组：年龄、性别、部位、分期、HPV/p16、治疗、缺失模式、中心/平台；
- 亚组结论以交互和 CI 为主，不根据单组显著性制造差异。

### 11.6 负对照最低要求

每个附加模态至少有：

- 跨患者置换；
- 随机同维特征；
- missingness-only（仅缺失模式）；
- 主要捷径代理；
- 模态身份去除消融。

如果 Proposed 不优于负对照，不能宣称学到模态特异生物学。

---

## 12. 推荐配置 schema

### 12.1 `protocol.yaml`

```yaml
study_name: pattern_surv_hancock
analysis_label: post_lock_exploratory
phase6_outcomes_already_seen: true
frozen_phase6_modification_allowed: false
external_outcomes_for_tuning: false

endpoint:
  name: overall_survival
  horizon_days: 730.5
  event_column: event
  time_column: time

split:
  source: hancock_official
  development_partition: training
  exploratory_ood_partition: test
  patient_level: true
  calibration_fraction: 0.20

seeds: [17, 29, 43, 71, 101]
bootstrap_replicates: 1000

outputs:
  tracked_aggregate_only: true
  patient_predictions_git_ignored: true
```

### 12.2 `model.yaml`

```yaml
model:
  name: clinical_residual_set_survival
  embedding_dim: 64
  fusion: set_transformer
  num_heads: 4
  num_layers: 2
  dropout: 0.20
  clinical_anchor: true
  survival_head: cox
  quality_tokens: true
  domain_tokens: false
  uncertainty: ensemble
  action_head: true

loss:
  survival: 1.0
  distillation: 0.0
  pattern_consistency: 0.0
  calibration: 0.0
  clinical_regret: 0.0
```

必须通过一组配置逐步开启损失，不能一次全部设非零。

### 12.3 `stress_patterns.yaml`

```yaml
natural_missingness: true
simulated:
  mcar_rates: [0.10, 0.30, 0.50]
  block_drop_each_modality: true
  mar_like:
    enabled: true
    formula_pre_registered: true
unseen_patterns:
  enabled: true
  selection_rule: frequency_then_clinical_relevance
corruption:
  permutation: true
  gaussian_noise_levels: [0.25, 0.50, 1.00]
  scale_shift: [0.5, 2.0]
  platform_shift: true
negative_controls:
  missingness_only: true
  random_features: true
```

---

## 13. Codex 每一阶段的标准任务格式

用户给 Codex 的每个任务都应要求以下输出。

### 13.1 开始前

```text
1. 复述本阶段目标和明确不做的内容；
2. 读取 PROJECT_STATUS 和对应 protocol；
3. 列出计划读取、修改和新增的文件；
4. 检查 git status，避免覆盖用户未提交修改；
5. 若需依赖/网络/大文件，先停止并提交审计，不自行下载。
```

### 13.2 实现中

```text
1. 先写数据合同和单元测试；
2. 再写最小实现；
3. 先跑合成 smoke test；
4. 再跑小规模真实数据；
5. 最后才跑完整实验；
6. 每次失败保留日志和可复现命令；
7. 不修改冻结 Phase 3–6 行为。
```

### 13.3 完成后

Codex 必须报告：

- 修改文件；
- 新增类/函数；
- 运行命令；
- 测试通过/失败数；
- 生成输出；
- 数据泄漏检查；
- 治理检查；
- 结果是否达到本阶段验收；
- 下一步是否 Go；
- 尚未解决的限制；
- 推荐 Git commit message。

### 13.4 通用提示词模板

```text
请按照 docs/HNSCC_missing_modality_codex_experiment_playbook.md 的 [阶段编号]
执行。本次只完成该阶段，不提前实现后续模型。

要求：
1. 先读取 trust-hn/PROJECT_STATUS.md 和相应 protocol；
2. 将分析标记为 post_lock_exploratory；
3. 不修改 Phase 3–6 冻结决策和结果；
4. 先检查 git status，保护现有修改；
5. 先写/更新测试，再实现最小代码；
6. 先使用合成数据 smoke test；
7. 患者级输出必须 Git ignored，提交结果只能为 aggregate-only；
8. 不自动下载数据、代码或权重；
9. 完成后列出文件、命令、测试、结果、限制、go/no-go 和 commit message；
10. 若发现协议不合理，只提交审计和修改建议，不擅自利用外部结果重调。
```

---

## 14. 具体 Codex 任务队列

### Milestone 0：只做审计，不训练

```text
M0.1 创建新命名空间和 protocol
M0.2 HANCOCK 模态模式审计
M0.3 深度学习依赖审计
M0.4 外部方法卡和许可证审计
M0.5 合成多模态删失数据生成器
```

验收后才能进入 M1。

### Milestone 1：强 baseline 与简单集合模型

```text
M1.1 包装 B2/B5/B6/C3 为统一 predictor API
M1.2 实现 Deep Sets + Cox
M1.3 实现 modality dropout MLP
M1.4 运行开发交叉验证
M1.5 输出 baseline 排名、校准和缺失退化
```

若 M1 无法显示缺失场景存在可改善空间，应暂停 P1 深度扩展，优先做 P2/P3。

### Milestone 2：临床锚定与未见模式

```text
M2.1 ClinicalResidualSetFusion
M2.2 seen/unseen pattern split
M2.3 quality and availability token
M2.4 pattern-wise evaluation
M2.5 clinical safety regret
```

### Milestone 3：蒸馏和可靠性路由

```text
M3.1 full teacher audit
M3.2 subset distillation
M3.3 uncertainty monotonicity
M3.4 fuse/fallback/abstain router
M3.5 matched-coverage evaluation
```

### Milestone 4：跨平台校准

```text
M4.1 TCGA/GEO endpoint alignment
M4.2 reproduce zero-shot calibration failure
M4.3 baseline hazard and horizon recalibration
M4.4 calibration event-size curve
M4.5 rank-only/full-risk/fallback actions
```

### Milestone 5：捷径安全复制

```text
M5.1 RADCURE negative control registry
M5.2 clinical+volume anchor
M5.3 shortcut residualization
M5.4 counterfactual substitution
M5.5 unreliable-imaging fallback
```

### Milestone 6：高风险潜在补全

只有 M2/M3 支持后才做：

```text
M6.1 modality co-occurrence audit
M6.2 deterministic completion
M6.3 CVAE completion
M6.4 multiple-sample uncertainty
M6.5 safe ignore/fallback integration
```

### Milestone 7：最终模型冻结与探索性 OOD 评价

```text
M7.1 根据开发协议选择一个模型和一个备用简单模型
M7.2 固化配置、依赖、种子和哈希
M7.3 生成模型卡草稿
M7.4 在已见过结果的官方 OOD/test 上仅做 post-lock exploratory evaluation
M7.5 不再根据 OOD/test 回调模型
M7.6 输出 aggregate-only 表图和失败分析
```

---

## 15. 计算资源与实验体量控制

### 15.1 第一阶段估计

表格/预提取特征级模型可控制为：

- embedding dim：32–128；
- Transformer 层：1–3；
- heads：2–4；
- 参数量：优先低于 1–5M；
- 5 个种子；
- 训练时间以单卡数小时内为目标；
- CPU baseline 与神经模型同时保留。

### 15.2 不建议的搜索

- 大规模无约束 Bayesian sweep（贝叶斯超参搜索）；
- 在 763 人上训练数百个深网络并挑最好；
- 多个 loss 权重同时网格搜索；
- 未完成数据审计就下载 WSI/CT；
- 未证明 CVAE 有价值就训练 latent diffusion。

### 15.3 推荐逐级预算

| Gate | 模型数 | 数据 | 目的 |
|---|---:|---|---|
| Smoke | 1–2 | 合成/极小子集 | 正确性 |
| Pilot | 3–5 | 单划分开发数据 | 排除明显失败 |
| Development | 主要 baseline + 2–3 候选 | 交叉验证 | 模型选择 |
| Ablation | 锁定主候选 | 开发数据 | 机制解释 |
| Exploratory OOD | 1 主模型 + 1 简单模型 | 官方 OOD/外部 | 泛化描述，不调参 |

---

## 16. 顶刊科学故事如何组织

### 16.1 推荐主论文故事：P1 + P2 + P3

最完整而不依赖超大模型的组合是：

> **HNSCC 多模态生存模型的主要困难不是单纯“有没有模态”，而是任意组合、真实质量、平台迁移和模态捷径共同造成的不可靠风险。PATTERN-Surv 用临床锚定集合融合处理任意组合，以模式一致性和不确定性识别证据不足；CALIB-Bridge 分离排序与绝对风险迁移；SHORTCUT-FAILSAFE 证明存在但无效的模态可以被检测并安全回退。**

这形成三个互补 aim：

- Aim 1：任意模态组合和未见模式；
- Aim 2：跨平台校准与绝对风险；
- Aim 3：模态存在但不可靠时的捷径安全。

### 16.2 不同结果对应的论文定位

#### 路径 A：P1 明显成功

主方法论文。强调 arbitrary-set survival、pattern calibration 和 clinical safety regret。P2/P3 作为外部机制验证。

#### 路径 B：平均性能相近，但安全性改善

可信 AI/数字医学论文。强调 worst-pattern、校准、fallback 和“复杂融合并不普遍获益”。

#### 路径 C：P1 不成功，P2 成功

转为 survival transportability/calibration（生存可迁移性/校准）论文，重点指出外部 C-index 与概率可用性脱节。

#### 路径 D：影像无增益但 P3 router 成功

转为 negative-control-aware multimodal evaluation（负对照感知多模态评价）和 safe failure（安全失败）论文。

#### 路径 E：所有复杂方法不优于简单模型

仍可形成严格 benchmark（基准研究），但期刊层级可能下降。必须诚实报告样本量、模态信息量和当前公开数据限制，不能通过选择性报告制造 SOTA。

### 16.3 推荐主图

1. **Figure 1：**临床模态组合、质量和域偏移问题 + 总体架构；
2. **Figure 2：**数据集、自然缺失模式和开发/探索性 OOD 流程；
3. **Figure 3：**强 baseline 与 PATTERN-Surv 的全覆盖性能；
4. **Figure 4：**seen/unseen/worst-pattern 和 full-to-subset degradation；
5. **Figure 5：**校准曲线、目标域事件数—校准恢复曲线；
6. **Figure 6：**真实/置换/随机/体积对照和 router 动作；
7. **Figure 7：**risk–coverage 与 clinical safety regret；
8. **Figure 8（可选）：**U-Latent 补全不确定性。

### 16.4 推荐主表

- Table 1：队列、结局、模态和缺失模式；
- Table 2：全覆盖主性能；
- Table 3：自然、模拟、未见和损坏场景；
- Table 4：校准迁移；
- Table 5：负对照与捷径审计；
- Supplement：超参数、事件数、完整模式表、所有消融和统计 CI。

---

## 17. 每个方案的 novelty 判定清单

### 17.1 P1 不够新颖的版本

```text
把所有模态拼接进 Transformer
+ 随机 modality dropout
+ 报一个 C-index
```

这不足以支撑目标期刊。

P1 达标应至少包含：

- arbitrary set；
- clinical residual anchor；
- unseen pattern；
- censored pattern consistency；
- pattern-conditioned calibration；
- fuse/fallback/abstain；
- 真实自然缺失和一个外部/偏移生态。

### 17.2 P2 不够新颖的版本

```text
在外部集拟合一个 calibration intercept
```

P2 达标应包含：排序/概率迁移分解、事件数曲线、适配不确定性、动作策略和多个目标环境/敏感性分析。

### 17.3 P3 不够新颖的版本

```text
加一个 adversarial loss 去除中心信息
```

P3 达标应包含：真实/随机/置换/体积对照、增量价值锚点、反事实替换、错误感知路由和安全 regret。

### 17.4 P4 不够新颖的版本

```text
用 VAE 生成缺失 embedding 后直接预测
```

P4 达标应包含：概率样本、不确定性传播、no-completion 对照、临床锚定、错误时忽略补全和自然缺失验证。

---

## 18. 文件和实验命名规范

### 18.1 Run ID

```text
<study>__<model>__<protocol>__seed<seed>__<YYYYMMDD-HHMM>
```

例：

```text
hancock__clinical_residual_set__unseen_v1__seed17__20260812-2300
```

### 18.2 每次 run 的 metadata

```json
{
  "analysis_label": "post_lock_exploratory",
  "git_commit": "<sha>",
  "config_sha256": "<hash>",
  "data_manifest_sha256": "<hash>",
  "seed": 17,
  "phase6_outcomes_already_seen": true,
  "external_outcomes_for_tuning": false,
  "patient_level_predictions_tracked": false
}
```

### 18.3 日志

日志必须包含：

- 数据人数与事件数；
- 每种模式 batch 数；
- 训练/验证损失；
- 早停 epoch；
- 最佳 checkpoint 的选择指标；
- NaN/梯度异常；
- 实际运行时长和设备；
- 版本和配置哈希。

不得在可跟踪日志中打印患者 ID。

---

## 19. 实施前必须回答的关键问题

### 19.1 数据问题

- HANCOCK 当前的“预提取患者特征”具体对应哪些模态？
- 所有变量是否在预测时点可获得？
- 模态缺失原因能否区分？
- 临床变量是否在所有患者可用，若临床也缺失如何定义回退？
- 自然模式中是否有足够事件进行模式级评价？
- 是否存在患者重复或同患者多材料？

### 19.2 方法问题

- clinical anchor 是冻结还是共同训练？
- 生存头采用 Cox 还是离散时间？
- teacher 的“完整”如何定义，是否造成 complete-case selection bias（完整病例选择偏倚）？
- 路由监督从何而来，是否交叉拟合？
- pattern calibration 如何在小模式中收缩？
- uncertainty 是 epistemic（认知不确定性）、aleatoric（数据不确定性）还是二者混合？

### 19.3 论文问题

- 主临床时间点是 24 个月还是多个时间点？
- 主结果是全覆盖 Brier、Uno C，还是 worst-pattern regret？
- “安全”是否有可操作定义和阈值？
- 哪个数据集是开发，哪个只是探索性外部复制？
- 是否有足够证据支持“跨中心”“跨平台”或“临床效用”等措辞？

---

## 20. 推荐的最小启动任务

建议下一次直接给 Codex 以下任务，而不是立即写 Transformer：

```text
请执行 docs/HNSCC_missing_modality_codex_experiment_playbook.md 的 P1.0。
只完成 HANCOCK 任意模态生存研究的数据、缺失模式、治理和依赖审计，
不要训练模型，不要安装依赖，不要下载数据。

要求：
1. 阅读 PROJECT_STATUS、hancock.yaml、HANCOCK adapter 和现有 Phase 3/4/7 特征接口；
2. 新建 configs/pattern_surv/registry.yaml 与 protocol.yaml 草案；
3. 编写 audit_pattern_surv_data.py，只输出 aggregate-only 统计；
4. 统计每个自然模态组合的人数、事件数、24 月可评价人数；
5. 审计预测时可得性、结构性缺失、潜在泄漏和完整病例选择偏倚；
6. 编写对应单元测试；
7. 生成 docs/audits/pattern_surv_hancock_data_audit.md；
8. 生成深度学习依赖建议，但不修改 pyproject.toml；
9. 不修改 Phase 3–6 冻结文件；
10. 完成后报告文件、测试、限制、go/no-go 和推荐 commit message。
```

建议该阶段 Git commit：

```text
chore(pattern-surv): add post-lock data and modality-pattern audit
```

---

## 21. 最终推荐

### 21.1 主方案

优先实施 **PATTERN-Surv Core**，但从简单 Deep Sets survival 和 clinical residual set fusion 开始，而不是直接构建大型 Transformer。该方案最贴合用户原始目标，也最能利用 HANCOCK 当前已有的自然缺失和多模态表格/预提取特征。

### 21.2 第二方案

并行思考但串行执行 **CALIB-Bridge**。它直接回答当前外部校准失败，计算成本较低，也可能在 P1 平均性能不显著时成为更强的论文主线。

### 21.3 第三方案

把 **SHORTCUT-FAILSAFE** 作为可靠性外部复制。它避免将“缺失”狭义理解为空值，并回应 RADCURE 真实模态未胜过负对照的关键发现。

### 21.4 高风险扩展

只有当 P1 证明跨模态条件关系可学习且不确定性可识别错误时，才启动 **U-Latent**。不要为了生成式 AI 的表面 novelty 强行引入 diffusion。

### 21.5 最核心的投稿原则

目标期刊所需要的 novelty 不应来自模型参数量，而应来自：

- 新的、临床真实的任务设定；
- 删失、缺失、损坏和分布偏移的一体化评价；
- 临床锚定的安全增量学习；
- 风险排序与绝对校准的明确分离；
- 负对照和捷径审计；
- 可复现、可止损、不过度宣称的统计证据。

如果最终复杂网络没有优于 B2/B5/B6/C3，最正确的科研行为不是继续堆叠模块，而是识别失败发生在信息量、样本量、校准迁移还是模态捷径，并据此选择 P2/P3 的科学故事或诚实报告阴性 benchmark。

---

## 22. 关键参考入口

> 以下入口用于后续方法卡核验。真正下载或使用前需再次确认论文版本、仓库许可证、依赖和数据条件。

1. HAF：MIDL 2026 proceedings，Heterogeneous Aligned Fusion；公开实现 `zz9tf/HAF`。原研究在 HANCOCK 中以 699 名具备所需病理材料的患者进行七模态 alive/dead 分类，并采用患者级十折交叉验证；因此本项目必须把它适配为删失感知的 HAF-Surv，而不能把原分类结果当作生存分析结果。
2. DisPro：CVPR 2025，Distilled Prompt Learning for Incomplete Multimodal Survival Prediction；公开实现 `Innse/DisPro`。
3. Multi-FRuGaL：2026 预印本，灵活模态组合 HNSCC 生存学习；不得写成已正式同行评议期刊工作。
4. Tian 等：npj Digital Medicine 2025，HNSCC clinical/CT/pathology 风险分数后期融合。
5. 邻近 NSCLC 工作：npj Digital Medicine 2026，clinical/PET/CT 不完整多模态生存；不是 HNSCC 证据。
6. Flex-MoE：`UNITES-Lab/flex-moe`，任意缺失模态和动态专家路由参考。
7. Set Transformer 与 Deep Sets：置换不变集合建模基础。
8. scikit-survival 与 pycox：传统/深度生存损失和评价参考。
9. CLAM 与病理基础模型：获得 WSI 后的特征提取与多实例聚合参考。

详细论文入口和数据链接见：

```text
docs/HNSCC_missing_modality_deep_learning_npjDM_ideas.md
```

---

## 23. 常用英文术语速查

> 正文在术语首次出现时尽量给出中文解释；本表用于 Codex 实施和论文写作时统一命名。类名、函数名和配置键保持英文，以便代码可读。

| 英文术语 | 中文解释 | 本项目中的具体含义 |
|---|---|---|
| adapter | 适配器 | 将不同模态输入转换为统一维度 token 或特征的模块 |
| anchor | 锚点 | 默认可信的临床基础模型，附加模态只学习其增量证据 |
| aggregate-only | 仅汇总 | 只保存人数、事件数、指标和置信区间，不保存患者级记录 |
| baseline | 基线方法 | 与候选模型公平比较的已有或简单方法 |
| calibration | 校准 | 预测概率与真实事件发生率的一致程度 |
| censoring | 删失 | 随访结束时尚未观察到事件，真实事件时间不完整 |
| clinical safety regret | 临床安全遗憾 | 融合模型相对临床锚点增加的预测损失 |
| completion | 补全 | 根据已有模态估计缺失模态的潜在证据；不代表生成了真实检查结果 |
| conformal prediction | 保形预测 | 在特定交换性等假设下控制预测集合或区间误差的方法 |
| corruption | 损坏/污染 | 模态虽存在但包含噪声、缩放、置换或错误处理 |
| coverage | 覆盖率 | 模型实际给出预测而未拒绝的患者比例 |
| cross-fitting | 交叉拟合 | 用患者所在折之外的数据训练模型，再为该患者生成折外预测 |
| data leakage | 数据泄漏 | 测试信息、结局或同患者材料进入训练流程 |
| development set | 开发集 | 用于训练、校准和模型选择的数据，不等同于外部测试 |
| discrimination | 判别能力 | 模型对高低风险患者进行排序或区分的能力 |
| distillation | 知识蒸馏 | 教师模型将风险或生存分布知识传给子集学生模型 |
| distribution shift | 分布偏移 | 训练与部署数据在中心、平台、病例构成或采集流程上不同 |
| domain | 数据域 | 具有共同中心、平台、时期或采集协议的数据环境 |
| embedding | 嵌入表示 | 将原始特征映射成供网络使用的低维向量 |
| endpoint | 研究终点 | 总生存、复发等需要预测的结局 |
| epoch | 训练轮次 | 模型完整遍历一次训练数据 |
| fallback | 回退 | 附加模态不可靠时改用临床基础模型 |
| foundation model | 基础模型 | 在大规模数据上预训练、可用于提取病理或影像特征的模型 |
| full-to-subset degradation | 完整到子集退化 | 从较完整模态输入减少为子集时的性能损失 |
| gate/router | 门控器/路由器 | 决定融合、回退或拒绝预测的模块 |
| horizon | 时间点 | 例如诊断后 24 个月的风险评价时点 |
| imputation | 填补 | 对缺失数值或表示进行估计；需区别于真实观测 |
| latent variable | 潜变量 | 不直接观测、由模型学习的隐藏表示 |
| locked evaluation | 锁定评价 | 在预先冻结方案下进行的一次性测试 |
| modality | 模态 | 临床、血液、ICD、TMA、WSI、CT、PET 或组学等数据类型 |
| modality token | 模态标记 | 表示该 token 来源和身份的可学习向量 |
| negative control | 负对照 | 理论上不应包含目标增量信息的置换、随机或捷径特征 |
| novelty | 创新性 | 相对已有任务、方法、评价或临床应用新增的科学贡献 |
| OOD | 分布外 | 与训练分布明显不同的输入或队列 |
| oracle | 预言机参照 | 使用实际部署时不可得信息构造的理论上界，不是可部署模型 |
| permutation invariant | 置换不变 | 改变模态输入顺序不会改变集合模型输出 |
| post-lock exploratory | 锁定后探索性 | 已经看过既有锁定结果后开展的新研究，不能称为预设验证 |
| prompt | 提示标记 | 告知模型模态身份、缺失状态或任务条件的向量 |
| protocol | 研究协议 | 预先规定数据、划分、模型、指标、统计和停止规则的文件 |
| registry | 注册表 | 统一记录模态定义、维度、来源、质量和可用性的配置 |
| residual evidence | 残余增量证据 | 附加模态在临床基础风险之外提供的信息 |
| risk–coverage curve | 风险—覆盖率曲线 | 拒绝更多不可靠患者时预测误差如何变化的曲线 |
| shortcut learning | 捷径学习 | 模型利用体积、中心、设备或处理流程等非目标线索获得表面性能 |
| smoke test | 冒烟测试 | 在合成或极小数据上快速检查代码能否正确运行 |
| teacher/student | 教师/学生模型 | 信息更完整的模型指导模态子集模型学习 |
| token | 标记向量 | 集合或 Transformer 中表示一个模态及其上下文的向量 |
| uncertainty | 不确定性 | 模型对风险估计可靠程度的量化，可来自数据噪声或模型知识不足 |
| unseen pattern | 未见模式 | 训练阶段未出现、测试阶段首次出现的模态组合 |
| value of information | 信息价值 | 获取某一新模态预期带来的预测或决策收益 |
| worst-group | 最差组 | 各模态模式或临床亚组中表现最差的群体 |

### 23.1 已核验的公开入口

```text
HAF paper: https://proceedings.mlr.press/v315/zheng26a.html
HAF code:  https://github.com/zz9tf/HAF
DisPro paper: https://openaccess.thecvf.com/content/CVPR2025/html/Xu_Distilled_Prompt_Learning_for_Incomplete_Multimodal_Survival_Prediction_CVPR_2025_paper.html
DisPro code:  https://github.com/Innse/DisPro
Multi-FRuGaL preprint: https://arxiv.org/abs/2606.06867
Flex-MoE code: https://github.com/UNITES-Lab/flex-moe
Tian HNSCC npj Digital Medicine paper: https://www.nature.com/articles/s41746-025-01712-0
NSCLC missing-modality npj Digital Medicine reference: https://www.nature.com/articles/s41746-026-02783-3
```

这些入口仅用于后续核验和方法卡填写。Codex 不得在未检查许可证、版本、依赖和患者级拆分前直接集成代码。

---

## 24. 文档完成定义

本手册可视为完成，前提是后续执行始终满足：

- [ ] 新研究与 Phase 3–6 冻结结果隔离；
- [ ] 每个方案有独立 protocol、代码命名空间和测试；
- [ ] 先完成数据与方法审计，再安装依赖或下载资源；
- [ ] 先完成简单 baseline，再进入复杂网络；
- [ ] 每个创新模块有独立消融；
- [ ] 自然、模拟、未见、损坏和 OOD 场景分开报告；
- [ ] 风险排序和绝对风险校准共同报告；
- [ ] 选择性预测报告 coverage；
- [ ] 所有附加模态有负对照；
- [ ] 患者级输出 Git ignored；
- [ ] 所有外部结果只作 post-lock exploratory，不用于回调；
- [ ] 结果不足时按 go/no-go 停止，而非继续堆模型；
- [ ] 论文结论不超出回顾性公开数据证据。

