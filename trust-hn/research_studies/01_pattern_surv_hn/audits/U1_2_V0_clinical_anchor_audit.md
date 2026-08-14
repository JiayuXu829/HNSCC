# U1.2/V0 Clinical Anchor Aggregate Audit

**完成日期：** 2026-08-14  
**阶段：** U1.2/V0  
**模型：** extended postoperative clinical-pathological elastic-net Cox  
**分析标签：** `post_lock_exploratory`  
**输出级别：** aggregate-only

## 1. 审计目的

本审计验证 PATTERN-Surv-HN 的临床安全锚点是否按审批后的术后 estimand、fold-pure preprocessing、nested cross-fitting 和 official-test sealing 要求执行。V0 的角色是后续 `FALLBACK` 动作的稳定参考，不是融合网络，也不产生 `FUSE / FALLBACK / RANK_ONLY / ABSTAIN` 路由标签。

## 2. 冻结 estimand 与输入

| 项目 | 冻结定义 | 实际执行 |
|---|---|---|
| 队列 | HANCOCK official training | PASS |
| 合格样本 | postoperative duration > 0 | n=610 |
| 事件 | survival_status = deceased | 173 |
| 排除 | duration <= 0 | 1 |
| 主要时间点 | 730.5 days | PASS |
| official test | 152 outcomes sealed | 未派生、未暴露、未评估 |
| anchor | age, sex, smoking, site, grading, p16, resection, pT, pN | PASS |
| 额外模态 | none | blood/ICD/TMA 均未进入 V0 |

`primarily_metastasis`、辅助治疗、outcome/follow-up、复发/进展/转移及预测时间之后变量均未进入模型。

## 3. Nested cross-fitting

```text
outer repetitions: 5 seeds [17, 29, 43, 71, 101]
outer folds:       5 per seed
inner folds:       3
candidate grid:    alpha [0.005, 0.01, 0.05, 0.1]
                   l1_ratio [0.1, 0.5, 0.9]
selection:         minimum mean inner-fold IPCW Brier at 730.5 days
OOF coverage:      610 patients × 5 seeds = 3050 rows
```

每个 inner/outer training fold 独立拟合数值插补、标准化、missing indicators、分类 missing/unknown level 和 one-hot mapping。每个 outer model 的 Cox baseline survival 仅由该 outer training fold 拟合。25 个 outer models 的编码维数为 53–56，非零系数为 11–39（平均 27.8）。

Pooled per-seed OOF 指标中的删失分布仅在 evaluation 阶段由全部 610 名合格 development 患者估计；预测本身仍全部为外层折外预测。Outer-fold 审计指标使用对应 outer training fold 的删失分布。

## 4. 主要 OOF 结果

| 指标 | 5-seed mean | SD | min | max |
|---|---:|---:|---:|---:|
| IPCW Brier, 24 m | 0.1247 | 0.0015 | 0.1225 | 0.1264 |
| Harrell C | 0.6230 | 0.0144 | 0.6096 | 0.6445 |
| Uno C, 24 m | 0.6442 | 0.0138 | 0.6217 | 0.6578 |
| time-dependent AUC, 24 m | 0.6620 | 0.0144 | 0.6388 | 0.6765 |
| calibration-in-the-large, 24 m | -0.0037 | 0.0149 | -0.0249 | 0.0136 |
| calibration slope, 24 m | 0.9367 | 0.0792 | 0.8492 | 1.0220 |
| mean predicted 24 m risk | 0.1562 | 0.0022 | 0.1543 | 0.1588 |

Calibration-in-the-large 定义为：以预测 24-month death risk 的 logit 为固定 offset 的 IPCW weighted logistic intercept。Calibration slope 定义为：IPCW weighted logistic regression 中预测 logit risk 的系数。这里没有训练 calibration bridge。

这些数字表明 V0 在内部 repeated OOF 中提供了可用但并非很强的区分度，24-month calibration 的总体偏移接近 0，平均 slope 接近 1。它们只支持“V0 可作为后续安全锚点”的技术判断，不支持外部泛化、临床效用或融合增益 claim。

## 5. 每个 seed 的结果

| Seed | Brier24 | Harrell C | Uno C24 | AUC24 | CITL24 | Slope24 |
|---:|---:|---:|---:|---:|---:|---:|
| 17 | 0.1258 | 0.6101 | 0.6217 | 0.6388 | 0.0051 | 1.0220 |
| 29 | 0.1264 | 0.6234 | 0.6477 | 0.6685 | -0.0110 | 0.8492 |
| 43 | 0.1225 | 0.6445 | 0.6578 | 0.6765 | 0.0136 | 1.0013 |
| 71 | 0.1247 | 0.6275 | 0.6513 | 0.6675 | -0.0012 | 0.8604 |
| 101 | 0.1242 | 0.6096 | 0.6427 | 0.6589 | -0.0249 | 0.9507 |

没有选择最佳 seed；所有预设 seed 均保留并汇总。

## 6. Acquisition-pattern 分层安全基线

下表为 5 seeds 的 OOF 指标均值。支持门固定为 `n >= 20` 且 `events >= 5`。

| Pattern | n | events | 支持 | Brier24 | Harrell C | Uno C24 | AUC24 |
|---|---:|---:|---|---:|---:|---:|---:|
| 001 | 7 | 4 | descriptive only | — | — | — | — |
| 010 | 4 | 0 | descriptive only | — | — | — | — |
| 011 | 58 | 23 | exploratory | 0.0987 | 0.6930 | 0.7209 | 0.7363 |
| 100 | 1 | 0 | descriptive only | — | — | — | — |
| 101 | 43 | 13 | exploratory | 0.1474 | 0.6333 | 0.6221 | 0.6403 |
| 110 | 22 | 7 | exploratory | 0.1744 | 0.5435 | 0.5382 | 0.6097 |
| 111 | 475 | 126 | exploratory | 0.1239 | 0.6073 | 0.6372 | 0.6507 |

V0 不使用 blood/ICD/TMA，因此这些差异不是“缺失模态效应”的因果估计，只是未来比较融合模型安全 regret 时的自然 acquisition-pattern 参考。尤其 `110` 仅 22 人/7 events，结果不稳定，不可单独形成 claim。

## 7. 超参数选择审计

25 个 outer folds 的选择频次：

| alpha | l1_ratio | folds |
|---:|---:|---:|
| 0.005 | 0.1 | 6 |
| 0.005 | 0.5 | 1 |
| 0.005 | 0.9 | 2 |
| 0.01 | 0.1 | 7 |
| 0.01 | 0.5 | 3 |
| 0.01 | 0.9 | 2 |
| 0.05 | 0.1 | 3 |
| 0.10 | 0.1 | 1 |

没有单一组合支配所有 folds，因此后续应继续使用预冻结的 nested selection procedure，而不是根据本次结果挑选一个“最好”的全局 alpha/l1 ratio。

## 8. 可重复性与治理

| 检查 | 结果 |
|---|---|
| 正式 OOF 行数 | 3050/3050 |
| 每 seed 每患者恰好一次 OOF | PASS |
| 两次正式重跑 OOF SHA256 | 完全一致 |
| OOF SHA256 | `B58C713DA7D98546AED8B581BD942A1DA3F81ED7FBF28053051AFE59FDFEF141` |
| patient-level OOF git-ignore | PASS |
| aggregate JSON identifier-key scan | PASS |
| Ruff | PASS |
| U1.1 + U1.2 targeted tests | 18 PASS |
| 相关 Phase 2/3 regression tests | 23 PASS |
| full repository suite | 118 PASS / 1 known frozen Phase 6 legacy FAIL |
| dependency files | 未修改 |
| frozen Phase 3–6 key paths | 0 modified |
| inherited frozen manifest baseline | 377 files; SHA256 `01FD176E338BFF4B09EB23E4DFA5CA455D77091161AE89AD3A9356D60BBB2D10` unchanged by path diff |

全仓唯一失败仍为 `tests/test_phase6_statistics.py::Phase6StatisticsTests::test_outcomes_refuse_access_before_consumption`。它假定 Phase 6 outcome 尚未消费，而历史工作区已合法记录 consumed state；U1.2 未修改该 frozen test、loader 或 config。

## 9. Go/no-go

**Technical GO：** V0 数据边界、nested OOF、24-month absolute risk、校准审计、reproducibility 和 governance 均满足进入下一审批门的条件。

**Scientific conditional GO：** V0 可作为后续 residual fusion 的安全锚点和 `FALLBACK` 输出，但其区分度中等；V1 必须证明在全覆盖 Brier、排序或 worst-pattern safety 上相对 V0 有稳定增益，且不能以小模式或选择性 subset 的好看结果替代全覆盖结果。

**NO-GO without approval：** 不得自动进入 U1.3/V1，不得训练 calibration bridge、Global Value Router 或 V2，不得使用 official-test/外部 outcome 选择方法或 claim。
