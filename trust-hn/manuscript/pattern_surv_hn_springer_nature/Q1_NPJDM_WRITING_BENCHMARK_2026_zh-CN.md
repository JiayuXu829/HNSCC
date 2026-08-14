# 2026 年 Q1 / npj Digital Medicine 写作与实验组织基准

> 调研日期：2026-08-14  
> 用途：指导 PATTERN-Surv-HN living manuscript 的标题、故事线、Results 层级与实验冻结。  
> 注意：这是写作和证据组织基准，不代表期刊接收承诺，也不以影响因子替代科学质量。

## 1. 本轮重点对照的近期论文

1. Tian et al. *Multimodal fusion model for prognostic prediction and radiotherapy response assessment in head and neck squamous cell carcinoma*. npj Digital Medicine, 2025, 8:302. DOI: 10.1038/s41746-025-01712-0。
2. Ruffini et al. *Handling missing modalities in multimodal survival prediction for non-small cell lung cancer*. npj Digital Medicine, 2026, 9:281. DOI: 10.1038/s41746-026-02783-3。
3. Zheng et al. *Heterogeneous Aligned Fusion for Survival Prediction with Incomplete Multimodal Data*. Proceedings of MLHC 2026, PMLR 298:1373–1396。
4. Xu et al. *Distilled Prompt Learning for Incomplete Multimodal Survival Prediction*. CVPR 2025。
5. Ong Ly et al. *Shortcut learning in medical AI hinders generalization*. Scientific Reports, 2024, 14:124. DOI: 10.1038/s41598-023-49902-0。
6. TRIPOD+AI 与 PROBAST+AI，用于检查预测时点、数据流、验证类型、性能指标、偏倚和适用性。

## 2. 高水平标题的共同结构

近期高水平医学 AI 原始研究的标题通常采用以下三种结构：

- **临床任务 + 关键挑战 + 疾病场景**：例如 missing modalities + survival prediction + NSCLC；
- **可验证的主要发现 + 临床任务 + 多中心证据**：仅在结果已经足够强时使用 improves/enables/outperforms；
- **方法名 + 明确用途**：方法品牌只有在容易记忆且正文贡献清晰时才放入标题。

不推荐：novel、robust、trustworthy、clinically deployable、universally generalizable 等无法由当前证据直接支持的形容词。

本稿标题由较宽泛的 “learning from incomplete and unreliable evidence” 收紧为：

> **Clinically anchored multimodal survival prediction under missing, shifted and shortcut-prone evidence in head and neck cancer**

它明确给出：临床锚定、任务、三个失败轴和疾病，同时避免提前宣称模型已经 improved 或 externally validated。

## 3. 一篇高水平论文需要一条而不是五条主故事

推荐的一句话故事：

> 多模态预测的关键不是如何强制融合更多输入，而是何时允许可选证据改变一个始终可用的临床预测。

由此形成“1–3–4”结构：

- **一个框架**：临床锚定的 residual multimodal survival prediction；
- **三个可证伪挑战**：missing/unusable、shifted calibration、shortcut-prone observed evidence；
- **四种输出动作**：FUSE、FALLBACK、RANK_ONLY、ABSTAIN。

HANCOCK、TCGA–GEO 和 RADCURE 不能写成三个松散的数据集案例，而应分别成为上述三个失败机制的证据工具。Future untouched cohort 单独承担最终确认，不能与 outcome-seen 队列混写。

## 4. 章节组织基准

### Introduction：五段完成

1. 临床决策问题及 intended use；
2. 一个组织性矛盾：recorded data 不等于 trustworthy evidence；
3. 直接相关工作及其已解决的问题；
4. 尚未解决的概率、选择性预测和 shortcut 评价缺口；
5. 本文框架、三个挑战、四个动作、primary claim 和 claim boundary。

### Results：按证据升级，而不是按算法模块说明

1. 研究人群、队列角色和证据架构；
2. 自然 acquisition/usability 形成的真实缺失问题；
3. 临床锚点作为 full-coverage reference；
4. PATTERN 对强基线和近期同任务方法的 primary comparison；
5. 自然/未见/损坏模式 falsification；
6. ranking 与 probability transport；
7. present-but-invalid negative controls；
8. matched-coverage routing；
9. frozen untouched confirmation。

每个最终 Results 小节采用四句骨架：

1. 本节回答什么问题；
2. 主效应值、95% CI、样本数/事件数；
3. 关键敏感性或失败模式；
4. 仅在证据允许范围内解释，不重复 Methods。

### Discussion：先回答，再比较，再限制

1. 第一段直接回答 primary question；
2. 与最接近的方法比较，说明不是“另一个 fusion block”；
3. 解释 anchor、residualisation、calibration bridge 和 router 的临床含义；
4. 讨论阴性结果和 falsification；
5. strengths；
6. limitations；
7. translation roadmap，不写超出证据的部署结论。

## 5. 实验应形成证据阶梯

- **Stage A：data contract + anchor freeze**；
- **Stage B：primary full-coverage comparison**，至少包括 C3、HAF、unanchored set model、anchored set model、PATTERN policy；
- **Stage C：falsification**，包括 rare natural patterns、unseen combinations、corruption、calibration transfer、negative controls；
- **Stage D：outcome-untouched confirmation**。

Gatekeeping：

- Primary Brier 差异不成功，不宣称总体 superiority；
- worst-pattern regret 越过 no-harm margin，不宣称可靠性；
- 低 coverage 才获得优势，不宣称临床安全性；
- 排序可迁移但校准失败，只能输出 rank-only；
- 没有 Stage D，不写 strong external generalization。

## 6. 最容易被审稿人质疑的地方

1. **研究过宽**：用一个 primary HANCOCK claim 和两个机制性验证轴收束；
2. **缺少最新直接竞品**：HAF 必须在 HANCOCK 上作为近期 comparator，DPLSurv 在输入兼容时复现；
3. **只报 C-index**：primary 采用 censoring-aware Brier，同时报告 calibration；
4. **选择性预测偷换分母**：matched retained subset + subgroup coverage；
5. **把 outcome-seen cohort 写成新外部验证**：明确 post-lock exploratory；
6. **复杂模型收益来自参数量**：强简单基线、参数量/训练预算匹配、ablation；
7. **高维模态只是 shortcut**：permutation、Gaussian、volume-matched controls；
8. **Methods 很完整但 Results 像研究计划**：实验冻结后删除 living-manuscript 语言，用效应值和 CI 替换所有 TBD。

## 7. 本轮已落实的稿件修改

- 收紧标题；
- 重写摘要为“临床缺口—框架—证据架构—已完成结果—primary TBD—临床意义”；
- 重写 Introduction，补入 2026 年直接 missing-modality survival 竞品；
- Results 小标题改为信息型、可形成 claim 的标题；
- 引入“一个框架、三个 falsification challenges、四种输出”；
- 增加 evidence ladder 和 claim gatekeeping；
- 将 HAF 加入 HANCOCK 必做 comparator；
- Discussion 明确本研究贡献不只是新的 fusion block；
- 修正 2026 MLHC/PMLR 文献元数据；
- 新增 2026 npj Digital Medicine missing-modality 论文和医学 shortcut 文献。
