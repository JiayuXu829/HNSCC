# PATTERN-Surv-HN Step U1.2/V0 阶段报告

**完成日期：** 2026-08-14  
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**分析标签：** `post_lock_exploratory`

## 1. 从论文投稿角度，本阶段做了什么

U1.2/V0 建立了整篇论文必须依赖的 clinical-pathological safety anchor。核心故事是：

> 不是让模型在缺失模态时仍然强行融合，而是让模型知道什么时候该融合、什么时候该回退。

其中“回退到什么”不能是一个随意的 clinical-only 模型，而必须是严格 cross-fitted、能输出 24-month absolute risk、校准可审计且在所有患者上有定义的锚点。V0 完成了这一层。

本阶段尚未证明我们的融合方法更好，也未产生四类动作。它为后续论文 claim 建立了比较零点：任何 V1/V2/PATTERN 改进都必须与同一患者、同一 outer fold 下的 V0 OOF 预测比较；当附加证据有害或不可靠时，`FALLBACK` 必须恢复到该锚点。

## 2. 实验设计

- 人群：HANCOCK official training，术后 duration > 0，n=610，events=173；
- endpoint：`days_to_last_information - days_to_first_treatment`，死亡为 event；
- 主要时间点：730.5 days；
- predictors：age、sex、smoking、site、grading、p16、resection、pT、pN；
- model：`CoxnetSurvivalAnalysis` elastic-net Cox，training-fold baseline survival；
- CV：5 seeds × 5 outer folds，outer training 内 3-fold inner selection；
- selection：冻结 12 个 alpha/l1-ratio combinations，以 inner IPCW Brier24 最小为主；
- leakage control：每个 inner/outer fold 独立拟合插补、缩放、missing/unknown level 和 one-hot mapping；
- outputs：3050 行 patient-level repeated OOF 仅保存在 git-ignored 目录，论文研究目录只保留聚合结果。

## 3. 主要结果

| 指标 | mean ± SD across 5 seeds |
|---|---:|
| IPCW Brier24 | 0.1247 ± 0.0015 |
| Harrell C | 0.6230 ± 0.0144 |
| Uno C24 | 0.6442 ± 0.0138 |
| AUC24 | 0.6620 ± 0.0144 |
| Calibration-in-the-large24 | -0.0037 ± 0.0149 |
| Calibration slope24 | 0.9367 ± 0.0792 |

结果的正确解释是：V0 在内部 repeated OOF 中具有中等区分度，24-month calibration 总体偏移较小，适合作为稳定 fallback anchor。不能解释为外部验证、临床迁移性已经证实，或我们的新融合网络已经优于 baseline。

## 4. 对论文故事的意义

1. **明确 safety reference。** 后续 `FALLBACK` 不再是抽象动作，而是返回本阶段定义的 clinical anchor risk/survival。
2. **提供严格增量基线。** V1、直接融合和 router 必须在相同 cross-fitting 框架下计算相对 V0 的个体或聚合增益。
3. **暴露 pattern 风险异质性。** V0 在 `110` pattern 的描述性结果较弱，但样本仅 22/7 events；这提示后续必须报告 worst-pattern safety，不能只报告总体均值。
4. **限制过度复杂化。** V0 已有合理校准，深度融合若只带来很小排序提升却破坏 Brier/calibration，应触发 complexity stop。

## 5. 本阶段没有做什么

- 没有输入 blood、ICD 或 TMA；
- 没有实现 V1 Deep Sets 或 V2 Set Transformer；
- 没有构造 incremental-value labels；
- 没有训练 Global Value Router；
- 没有决定 `FUSE / FALLBACK / RANK_ONLY / ABSTAIN`；
- 没有训练 calibration bridge；
- 没有评估 official test 或外部 outcomes；
- 没有证明跨数据集迁移性或泛化性提升。

## 6. 验证与治理

- Ruff：PASS；
- U1.1 + U1.2 targeted tests：18 PASS；
- Phase 2/3 related regression：23 PASS；
- full suite：118 PASS / 1 个已知 frozen Phase 6 state-dependent legacy FAIL；
- 两次正式执行的 OOF SHA256 完全一致；
- frozen Phase 3–6 key paths 与 dependency files 均未修改；
- official test 152 条结局仍未派生、暴露或评估。

## 7. 局限与投稿风险

1. 这是 outcome-seen 历史工作区中的 post-lock exploratory analysis；
2. 当前只有内部 repeated OOF，没有新 outcome-unseen external validation；
3. pattern metrics 极不平衡，三个小 pattern 只能报告 counts/events；
4. 当前没有 B0/B1/B3、direct fusion、late fusion 或 deep set 的同协议比较；
5. V0 的中等 discrimination 意味着论文最终价值必须来自“选择性利用增量证据并安全回退”，而不能只靠强 clinical baseline 的绝对表现；
6. 非零 one-hot features 的频次仅是稳定性审计，不是因果或生物学解释。

## 8. Go/no-go 和下一步

**本阶段建议：GO，批准 V0 作为 safety anchor。**

若研究者批准，下一步才可进入 **U1.3/V1 smoke implementation**：实现 Clinical-Residual Deep Sets Cox 的最小 permutation-invariant residual backbone，首先只验证 modality adapters、identity/status/quality encoding、任意子集输入、permutation invariance 和 exact clinical-only fallback。是否立即进行正式 V1 development cross-validation，应继续服从独立审批与复杂度门。

未获批准前停止，不启动 V1/V2、calibration bridge 或 router。
