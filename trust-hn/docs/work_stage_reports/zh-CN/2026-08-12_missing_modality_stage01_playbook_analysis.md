# 缺失模态研究执行阶段 01 报告：方法手册分析与工程盘点

**报告日期：** 2026-08-12  
**工作区：** `D:\medical_paper\HNSCC`  
**本阶段状态：** 已完成，等待研究者审批  
**本阶段性质：** 只读分析与执行规划；未训练、未安装依赖、未下载资源、未创建任何候选模型

---

## 1. 本阶段目标与明确不做的内容

### 本阶段完成目标

1. 阅读 `docs/HNSCC_missing_modality_codex_experiment_playbook.md`；
2. 读取并核对现有工程治理状态、Phase 7 探索配置和 Git 忽略规则；
3. 盘点当前代码、数据适配器、基线、评价函数和可复用资产；
4. 将手册中的候选方案拆成可逐步审批的独立验证路线；
5. 设计各方案隔离目录、报告制度、验收标准和停止规则；
6. 识别开始实验前必须解决的关键风险。

### 本阶段没有做

- 没有修改 Phase 3–6 的任何代码、配置、决策或结果；
- 没有读取患者级预测文件内容；
- 没有训练模型或重新评价外部队列；
- 没有安装 PyTorch、pycox 或其他新依赖；
- 没有联网下载论文代码、预训练权重或数据；
- 没有创建 P1–P5 的实现目录；目录创建留到下一阶段审批后进行。

---

## 2. 治理检查

```text
analysis_label: post_lock_exploratory
phase6_outcomes_already_seen: true
phase6_files_modified: false
external_outcomes_used_for_tuning: false
patient_level_outputs_git_ignored: true
tracked_outputs_aggregate_only: true
```

核对结果：

- `trust-hn/PROJECT_STATUS.md` 明确 Phase 6 已于 2026-08-08 完成，结果已被研究者看到；
- 新研究只能表述为 `post_lock_exploratory` 或开发性研究；
- 当前 Git 工作树在本阶段开始时为空净状态；
- `trust-hn/results/predictions/*` 已被 `trust-hn/.gitignore` 忽略；
- 如果把患者级预测放到新的自包含实验目录，例如 `research_studies/.../results/predictions/`，当前规则不会自动忽略，因此后续患者级输出必须继续集中写入 `trust-hn/results/predictions/<study>/`，或先单独审批扩展 `.gitignore`；
- Phase 6 已跟踪的配置、脚本、审计和汇总结果均不得覆盖。

---

## 3. 方法手册的核心科学命题

手册真正建议论文回答的不是“更大的 Transformer 是否提高 AUC”，而是：

> 当 HNSCC 患者的可用模态组合、模态质量、采集平台和中心分布变化时，删失感知生存模型能否识别哪些附加证据值得使用，同时保持风险排序和绝对风险校准，并在证据不可靠时安全回退。

论文证据链至少包括：

1. **任意模态组合：** 自然缺失、模拟缺失、训练已见与未见组合；
2. **删失感知生存：** 不把任务降格为简单 alive/dead 分类；
3. **临床锚定：** 附加模态只证明超过 clinical anchor 的增量；
4. **排序与校准分离：** C-index 尚可不代表绝对风险可用；
5. **存在但无效的模态：** 负对照、体积/中心/设备捷径和损坏模态；
6. **安全动作：** FUSE、FALLBACK、ABSTAIN，并同时报告 coverage；
7. **最差组与失败模式：** 不仅报告平均性能；
8. **可止损性：** 每个复杂模块必须由开发数据上的预设 Go/no-go 决定。

推荐的完整主论文组合是 P1 + P2 + P3；P4 为条件性高风险扩展；P5 暂不作为主要实验。

---

## 4. 各方案的独立定位与主要 claim

### P1：PATTERN-Surv Core

**主问题：** 单一模型能否处理临床锚定的任意模态集合，并对未见组合、质量损坏和 OOD 安全泛化？

**允许的核心 claim：**

- clinical residual set fusion 能减少固定融合在特定缺失模式下的负迁移；
- 在同等覆盖率下，模式感知和安全路由可改善 worst-pattern、unseen-pattern 或 corrupted-pattern 的风险/校准；
- 如果平均性能不提高，也可主张透明回退降低临床安全 regret，但不能宣称普遍优于简单基线。

**最关键前置条件：** HANCOCK 必须先恢复为真正的多模态可用性矩阵，而不是当前 Phase 3 的“blood + TMA 合并为一个附加模态”。

### P2：CALIB-Bridge

**主问题：** TCGA RNA-seq 到 GEO microarray 迁移时，相对排序和绝对风险能否被分离处理？

**允许的核心 claim：**

- 外部 C-index 与绝对概率可用性不是同一概念；
- 冻结 source rank encoder 后，用独立 target calibration split 估计基线风险/校准适配器；
- 给出“目标域事件数—校准恢复”曲线，并在证据不足时输出 RANK_ONLY、FALLBACK 或 ABSTAIN。

**最大风险：** GSE65858/GSE41613 已在 Phase 6 被评价，任何新的 calibration/test 划分都必须明确是 post-lock exploratory，且协议需在重新运行前冻结，不能看结果后选择有利的事件数或方法。

### P3：SHORTCUT-FAILSAFE

**主问题：** 模态存在但主要编码体积、中心、设备或随机结构时，模型能否识别无效证据并回退？

**允许的核心 claim：**

- 只有真实影像超过 `clinical + volume` 和负对照，才能声称影像具有超越体积的增量；
- 即使真实影像不优于负对照，只要 router 能在假/损坏模态下可靠回退，仍可形成“安全失败”贡献。

**最大风险：** 早期 Phase 3 配置曾记录 RADCURE radiomics 不可用，但 Phase 6 已存在 RADCURE radiomics 负对照结果。P3.0 必须先追踪后续数据入口、定义、哈希和生成逻辑，不能直接假设早期 blocker 仍有效，也不能修改原负对照。

### P4：U-Latent Evidence Completion

**主问题：** 是否可以只补全“潜在证据分布”，而不伪造原始图像，并把补全不确定性传播到生存风险？

**允许的核心 claim：**

- 概率补全优于 no-completion 和 deterministic completion；
- 补全方差与预测误差相关；
- 高不确定时生成 token 不主导风险，模型回退到 observed-set 或 clinical anchor。

**进入条件：** P1 已证明跨模态关系可学习；成对共现人数/事件数足够；确定性补全至少显示下游生存信号且不恶化校准。

### P5：ACQUIRE-HN

**主问题：** 在成本约束下选择下一个最值得采集的模态。

**当前定位：** 可选探索，不进入首轮主实验。公开数据目前缺少可信真实成本、周转时间和采集顺序；若仅使用人为成本，临床 claim 会过度模拟化。

---

## 5. 现有工程资产盘点

### 可复用资产

- HANCOCK 适配器：`src/trust_hn/data/adapters/hancock.py`；
- Phase 3 特征接口：`src/trust_hn/data/phase3_features.py`；
- 传统生存基线：`src/trust_hn/models/survival_baselines.py`；
- 临床残差融合：`src/trust_hn/models/residual_fusion.py`；
- Phase 7 C3、Breslow 风险等：`src/trust_hn/phase7/models.py`；
- 生存指标：`src/trust_hn/metrics/survival.py`；
- 压力测试、亚组、覆盖率思路：`src/trust_hn/evaluation/phase5.py`；
- 现有依赖已经包含 `scikit-survival` 和 `xgboost` 的 optional survival 组。

### 当前 HANCOCK 事实

根据 `configs/hancock.yaml`：

- 总人数 763；官方 training 611、test 152；
- 死亡事件 213；
- clinical/pathological/target 各 763；
- blood 692；ICD 712；TMA cell density 736；
- 24 月死亡 104；观察超过 24 月且无事件 516；24 月前删失 143。

### 目前不能直接满足 P1 的地方

1. `HancockAdapter` 当前 `PatientRecord` 只将 TMA 暴露为一个 `modality_features_available` 布尔量；
2. Phase 3 的附加模态是 blood 与 TMA 合并后的表格，不是临床、病理、血液、ICD、TMA 分开的集合；
3. 自然缺失原因尚未区分“未采集、采集失败、结构性不适用和人为 masking”；
4. 临床和病理当前在适配器/特征定义中的角色需要重新审计，避免病理信息既被算入 clinical anchor 又作为独立模态重复进入；
5. 模态级预测时可得性、时间字段和潜在 outcome-derived 字段需逐列审核；
6. 原始 WSI、TMA 图像和 UNI encodings 当前配置为禁止下载，首轮只能使用现有结构化/预提取特征。

### 依赖现状

`pyproject.toml` 没有 PyTorch。按手册要求，下一阶段最多创建依赖审计，不能安装。P1.0 数据审计和合成数据合同可以完全在现有 NumPy/Pandas/PyYAML/PyTest 环境中完成。

---

## 6. 建议的方案隔离方式

为兼顾“每个方案单独文件夹”与现有 Python 包结构，采用两层隔离：

### A. 每个方案的研究控制目录

```text
trust-hn/research_studies/
  01_pattern_surv/
    STUDY_STATUS.md
    approvals/
    reports/
    runbooks/
  02_calib_bridge/
    STUDY_STATUS.md
    approvals/
    reports/
    runbooks/
  03_shortcut_failsafe/
    STUDY_STATUS.md
    approvals/
    reports/
    runbooks/
  04_u_latent/
    STUDY_STATUS.md
    approvals/
    reports/
    runbooks/
  05_acquire_hn/
    STUDY_STATUS.md
    approvals/
    reports/
    runbooks/
```

该目录用于记录方案状态、每步报告、审批结论和可复现命令；每次只进入一个方案目录推进。

### B. 与现有工程兼容的独立代码命名空间

以 P1 为例：

```text
configs/pattern_surv/
src/trust_hn/pattern_surv/
scripts/pattern_surv/
tests/pattern_surv/
results/metrics/pattern_surv/       # 仅汇总
results/figures/pattern_surv/       # 无患者标识
results/predictions/pattern_surv/   # 患者级，已受统一 ignore 规则保护
artifacts/pattern_surv/
```

P2–P5 分别使用 `calib_bridge`、`shortcut_failsafe`、`u_latent`、`acquire_hn` 命名空间。这样不会修改冻结模块，也不会让患者级预测落到未被忽略的新路径。

### 审批记录格式

每个步骤生成：

```text
research_studies/<NN_study>/reports/step_<编号>_<名称>.md
research_studies/<NN_study>/approvals/step_<编号>_approval.md
```

由 Codex 生成 report；研究者审批后，再由 Codex记录审批结果并进入下一步。没有明确审批时不提前执行后续步骤。

---

## 7. 建议的总体执行顺序

手册第 3.2 节建议 P2 在 P1 简单 baseline 后快速执行。为了同时满足“每个方案依次单独验证”，建议采用以下串行顺序：

1. **共同基础设施（只服务 P1 起步，但接口可复用）**；
2. **P1-M0/P1.0：HANCOCK 数据、模式、治理和依赖审计**；
3. **P1-M1：强传统 baseline + 简单 Deep Sets 生存模型**；
4. **决策门 A：** 若缺失场景没有可改善空间，暂停 P1 复杂化；
5. **P2：CALIB-Bridge 完整快速验证**；
6. 返回 **P1-M2/M3：临床锚定、未见模式、蒸馏和安全路由**；
7. **P3：SHORTCUT-FAILSAFE**；
8. **决策门 B：** 只有 P1 支持跨模态关系和不确定性，才做 P4；
9. **P4：U-Latent**；
10. **P5：** 仅在获得可信成本/采集顺序后启动；
11. 汇总开发结果，冻结候选模型，再进行一次 post-lock exploratory OOD 描述，不回调。

这样做的原因：P2 计算成本低，能快速判断当前最清晰的外部失败是否来自“排序—校准分离”；但 P1 仍是主方案，需要先完成 P1.0 和简单 baseline，才能知道复杂任意模态模型是否有必要。

---

## 8. 逐步审批队列

以下每一行都是一个独立停止点。每步结束后提交 report，等待审批。

### 全局与 P1

| 步骤 | 内容 | 主要输出 | 审批后才进入 |
|---|---|---|---|
| G0.1 | 方法手册分析与工程盘点 | 本报告 | G0.2 |
| G0.2 | 创建五个研究控制目录、报告模板和状态文件；不实现模型 | 目录骨架、模板、状态表 | P1.0a |
| P1.0a | 冻结 P1 protocol/registry 草案和治理测试 | YAML、schema test | P1.0b |
| P1.0b | 只读盘点 HANCOCK 各模态源文件、列和患者键 | source inventory report | P1.0c |
| P1.0c | 生成自然模态可用性和模式聚合统计 | aggregate CSV、审计报告 | P1.0d |
| P1.0d | 预测时可得性、泄漏、重复患者、完整病例偏倚审计 | leakage/availability report | P1.0e |
| P1.0e | 深度学习依赖和外部方法许可证审计，不安装 | dependency/method cards | P1.0f |
| P1.0f | 合成多模态删失数据合同和测试 | contracts、synthetic generator、tests | P1.1a |
| P1.1a | 统一包装 B2/B5/B6/C3 | predictor API、tests | P1.1b |
| P1.1b | Deep Sets + Cox 合成 smoke test | model/tests/log | P1.1c |
| P1.1c | 小规模真实数据 pilot | aggregate pilot report | P1.1d |
| P1.1d | 5 种子开发交叉验证 | baseline ranking/calibration | P1 Go/no-go |
| P1.2 | ClinicalResidualSetFusion | tests、ablation | P1.3 |
| P1.3 | seen/unseen pattern protocol | frozen YAML/hash、metrics | P1.4 |
| P1.4 | teacher 审计及条件性蒸馏 | distillation ablation | P1.5 |
| P1.5 | quality/OOD/uncertainty 和安全动作 | matched-coverage report | P1.6 |
| P1.6 | 正式开发统计与 P1 冻结 | aggregate tables/figures | P2/主线决策 |

### P2

| 步骤 | 内容 | 停止条件 |
|---|---|---|
| P2.0a | endpoint、起点和样本独立性审计 | 不一致且不可协调则停止 |
| P2.0b | 基因/探针交集和映射审计 | 映射不可靠则停止 |
| P2.1 | 预注册方式复现 zero-shot 排序/校准分离 | 只建立现象，不选模型 |
| P2.2 | baseline hazard、截距、斜率校准 | 仅 target calibration split 拟合 |
| P2.3 | 目标事件数曲线 | 报告数值失败次数 |
| P2.4 | FULL_RISK/RANK_ONLY/FALLBACK 动作 | OOD 分数必须与误差关联 |
| P2.5 | 汇总与冻结 | 不根据探索 test 回调 |

### P3

| 步骤 | 内容 | 停止条件 |
|---|---|---|
| P3.0 | 追踪并冻结 RADCURE 真实/置换/随机特征定义和哈希 | 无法确认来源则不训练 |
| P3.1 | clinical + volume 强锚点 | 作为影像增量最低比较 |
| P3.2 | residualization/orthogonal/HSIC 阶梯 | 简单方法最佳则不强推复杂法 |
| P3.3 | 反事实替换 | 假模态下风险和动作应合理变化 |
| P3.4 | cross-fitted value router | 禁止同一患者自标注增益 |
| P3.5 | 压力测试与冻结 | 与负对照接近则只做安全失败 claim |

### P4

| 步骤 | 内容 | 停止条件 |
|---|---|---|
| P4.0 | 模态成对共现和事件矩阵 | 配对支持不足则停止 |
| P4.1 | no-completion、mean、deterministic 基线 | 无下游信号则停止 |
| P4.2 | CVAE 潜在补全 | 仅在 P4.1 Go 后 |
| P4.3 | K 次采样和误差—方差关系 | 方差无信息则停止 |
| P4.4 | 安全集成和冻结 | 过度自信则回退 observed-set |

### P5

先只做可行性审计。没有真实成本、侵入性等级或采集顺序时，不实现强化学习，不形成主 claim。

---

## 9. 关键风险与本阶段判断

### 风险 1：P1 的“多模态”定义尚未落地

当前代码将 blood 和 TMA 合并，不能直接证明任意多模态组合。必须先重建患者 × 模态可用性矩阵，并明确 clinical/pathological 是否分开。

**判断：** 可继续，但 P1.0 必须先于任何神经模型。

### 风险 2：官方 OOD/外部结果已经被看过

HANCOCK test、GSE65858、GSE41613 和 RADCURE Phase 6 结果不能再称为未见锁定验证。

**判断：** 可继续作为 post-lock exploratory；模型选择仅使用新的开发/校准协议。

### 风险 3：患者级输出路径

新实验根目录的 prediction 子目录不受当前 ignore 规则保护。

**判断：** 采用中央 `results/predictions/<study>/`，避免隐私治理回归。

### 风险 4：深度依赖尚未存在

PyTorch 不在现有环境。

**判断：** P1.0 不需要安装；到 P1.1b 前单独提交依赖审计并等待许可。

### 风险 5：P3 数据状态跨阶段不一致

Phase 3 blocker 与 Phase 6 已完成负对照并存。

**判断：** P3.0 必须做来源追踪，禁止直接复用不明中间产物。

### 风险 6：方案数量过多导致多重尝试和叙事漂移

P1–P5 全部无门槛推进会造成模型堆叠和结果驱动选择。

**判断：** 严格采用 P1/P2/P3 主线和 P4/P5 条件门；每步单独审批。

---

## 10. 本阶段验收结论

### 已满足

- [x] 阅读并拆解方法手册；
- [x] 读取项目状态、Phase 7 探索配置和 Git ignore；
- [x] 检查 Git 工作树；
- [x] 明确 Phase 6 不可修改边界；
- [x] 识别现有基线、指标和适配器可复用资产；
- [x] 为 P1–P5 定义独立研究目录和逐步审批队列；
- [x] 明确每个方案的 claim 边界和 Go/no-go；
- [x] 未安装、未下载、未训练、未访问患者级预测内容。

### 本阶段 Go/no-go

**GO：** 可以进入 G0.2——只创建隔离目录、状态文件、审批模板和报告模板。  
**尚不授权：** P1 数据统计、代码实现、依赖安装或任何模型训练。

---

## 11. 下一阶段准备做什么

若研究者批准本报告，下一阶段 **G0.2** 只执行：

1. 创建 `research_studies/01_pattern_surv` 至 `05_acquire_hn`；
2. 为每个方案创建 `STUDY_STATUS.md`、`reports/`、`approvals/`、`runbooks/`；
3. 创建统一阶段报告模板、审批记录模板和实验元数据模板；
4. 创建各方案 canonical namespace 的空目录或 `.gitkeep`；
5. 检查所有 patient-level prediction 目标路径是否被 Git 忽略；
6. 不创建模型代码，不读取患者结局，不运行实验；
7. 完成后生成 G0.2 report 并再次等待审批。

**建议提交信息：**

```text
docs(missing-modality): add staged post-lock research execution analysis
```
