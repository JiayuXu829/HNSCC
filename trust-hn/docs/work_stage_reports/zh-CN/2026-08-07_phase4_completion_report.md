# TRUST-HN Phase 4 完成报告

**日期：** 2026-08-07  
**阶段：** TRUST-HN 核心开发（B6 残差融合与 B7 可靠性门控）  
**状态：** 已在用户授权的有条件范围内完成；Phase 5 以及锁定/外部评价仍未获授权。  
**配置：** `configs/phase4_trust_hn.json`（`FROZEN_FOR_PHASE4_DEVELOPMENT`）

## 1. 授权边界

用户在审阅 Phase 3 基线结果后授权进入 Phase 4。获授权的工作仅限开发阶段，包括：实现 B6 堆叠残差学习器、三个不使用结局信息的 OOD 检测器、轻量级 bootstrap 不确定性、预先规定的等权可靠性评分，以及 B7 的 AUGMENT/FALLBACK/ABSTAIN 动作。

仅允许使用 HANCOCK 与 TCGA-HNSC 中已冻结的训练行和校准行。以下结局仍被禁止使用且未加载：RADCURE challenge test、HANCOCK OOD test、GSE65858 external test 和 GSE41613 sensitivity cohort。未执行 Phase 5 压力测试、亚组试验、分析冻结或 Phase 6 锁定/外部评价。

由于 ORCESTRA RDS 的模态结构尚未验证，RADCURE B6/B7 仍处于阻塞状态。因此，本阶段不对 RADCURE 的放射组学融合或可靠性门控作出任何结论。

## 2. 使用的开发数据

| 研究 | 训练集 | 校准集 | 附加模态 | Phase 4 状态 |
|---|---:|---:|---|---|
| HANCOCK | 489 | 122 | 基线血液测量加 TMA 细胞密度特征 | 已完成 |
| TCGA-HNSC | 415 | 104 | 19,962 个蛋白编码 `log2(TPM+1)` 表达特征；每个折内仅使用训练数据选择方差最高的 500 个特征 | 已完成 |
| RADCURE | 1,215 | 303 | 在 RDS 验证前，放射组学/GTV 不可用 | 已阻塞 |

各研究分别建模，没有合并为一张患者表。

## 3. 已实现的方法

### 3.1 B2 临床锚点与 B6 堆叠残差学习器

B2 是临床 elastic-net Cox 锚点。在每个外层 OOF 训练划分中，使用内层五折交叉拟合，为每位 B6 训练患者生成临床锚点评分。随后，B6 使用标准化的交叉拟合锚点评分和仅由训练数据得到的模态表征，拟合 elastic-net Cox 生存模型。对外层留出折或校准分区进行预测时，使用在对应完整训练部分上拟合的 B2 模型。

这是主实施文档允许的堆叠残差方案，而不是将临床锚点系数严格固定为 offset 的 Cox 模型。B5 的临床加模态直接拼接仍作为强制融合比较模型。

### 3.2 可靠性指标

所有可靠性指标均统一方向：数值越大表示越不可靠。

临床可靠性使用：

- 在训练数据得到的临床嵌入上计算 shrinkage Mahalanobis 距离、k 近邻距离和 Isolation Forest 分数；
- 由 20 个模型组成的临床 bootstrap 集成的标准差，并在患者级轨迹中保留中位数和 95% 区间宽度；
- B2 与非线性 B3 随机生存森林风险之间的绝对差异。

模态/融合可靠性使用：

- 在训练数据得到的模态嵌入上计算相同的三个 OOD 检测指标；
- 由 20 个模型组成的 B6 bootstrap 集成的标准差，并保留中位数和 95% 区间宽度；
- 确定性的、不依赖结局的模态行置换敏感性；
- 原始模态缺失比例和模态完全缺失标志；
- B6 与 B5 风险之间的绝对差异。

每个原始指标均使用专门的校准可靠性分布转换为经验百分位。三个 OOD 百分位先在各自领域内取平均，然后按照预先规定的等权方式计算临床和模态不可靠性。对于恒定为零的缺失率参考分布，零缺失映射为零不可靠性，而不是被错误映射为最大百分位。

### 3.3 B7 门控

动作优先级冻结为：

1. 当临床不可靠性超过其阈值时，执行 **ABSTAIN**；
2. 否则，当模态完全缺失或模态不可靠性超过其阈值时，执行 **FALLBACK**；
3. 否则，使用 B6 执行 **AUGMENT**。

AUGMENT 的最终风险为 B6 风险；FALLBACK 的最终风险为 B2 临床锚点风险；ABSTAIN 不输出最终风险。预先规定的 80% 和 90% 配置仅使用校准可靠性分位数。没有使用校准结局来优化阈值。

## 4. 执行统计

冻结后的完整运行使用五个外层折、随机种子 `17, 29, 43, 71, 101`，并且每个拟合范围使用 20 个 bootstrap 模型。

- **10 个成功的研究/种子运行**：2 个研究 × 5 个种子；
- **0 个失败运行**；
- **1 个因治理规则而阻塞的条目**：RADCURE B6/B7；
- 完整运行共完成 **1,200 次临床 bootstrap 拟合**和 **1,200 次 B6 bootstrap 拟合**；
- **20 个患者级决策轨迹 CSV 文件**，仅存放在被 Git 忽略的 `results/predictions/phase4/`；
- 未使用任何锁定或外部结局；
- 未使用任何 Phase 5 组件。

在规范完整运行之前，已针对每个获授权研究分别完成隔离的初步 smoke run。两个 smoke 路径均成功，包括高维 TCGA 表达数据路径。

## 5. 专用校准分区上的模型结果

数值为五个预先规定随机种子的均值。在冻结的预处理下，B2 和 B5 的校准拟合是确定性的，因此种子间变异为零；B6 略有变化，因为其交叉拟合锚点训练分数依赖随机种子。

| 研究 | 模型 | IPCW Brier | Harrell C | Uno C | 24 个月 AUC |
|---|---|---:|---:|---:|---:|
| HANCOCK | B2 临床锚点 | 0.1460 | 0.6328 | 0.6597 | 0.6901 |
| HANCOCK | B5 强制融合 | **0.1276** | **0.6948** | **0.7594** | **0.7873** |
| HANCOCK | B6 堆叠残差 | 0.1288 | 0.6756 | 0.7410 | 0.7692 |
| TCGA-HNSC | B2 临床锚点 | **0.2422** | 0.4898 | 0.4611 | 0.4368 |
| TCGA-HNSC | B5 强制融合 | 0.2482 | 0.6104 | 0.6028 | 0.6001 |
| TCGA-HNSC | B6 堆叠残差 | 0.2448 | **0.6182** | **0.6125** | **0.6093** |

解释：

- 在 HANCOCK 中，相比 B2，加入血液/TMA 信息明显有帮助。B5 仍是完整校准队列中表现最强的模型。B6 的 Brier 分数与 B5 接近，但在校准分区上的区分能力没有超过 B5。
- 在 TCGA-HNSC 中，B6 相比 B5 改善了 Brier 和区分能力，但其 Brier 仍略差于 B2。B2 很弱的区分能力与 B6 更好的区分能力说明存在校准与排序之间的权衡，而不是某个模型全面占优。
- 因此，B6 提供了有效的条件融合实现，但 Phase 4 并未证明残差融合普遍优于直接融合。

OOF 均值结果支持同样的混合结论：HANCOCK 的 B6 Harrell C 略高于 B5（`0.6822` 对 `0.6789`），Brier 接近（`0.1057` 对 `0.1052`）；而在 TCGA 中，B6 的 OOF 结果未超过 B5（Brier 为 `0.2261` 对 `0.2239`；Harrell C 为 `0.5949` 对 `0.6025`）。

## 6. 门控行为

### 专用校准分区

| 研究 | 配置 | 实际非弃权覆盖率 | AUGMENT | FALLBACK | ABSTAIN | 选择性 IPCW Brier |
|---|---:|---:|---:|---:|---:|---:|
| HANCOCK | 80% | 0.8033 | 0.6492 | 0.1541 | 0.1967 | 0.1098 |
| HANCOCK | 90% | 0.9016 | 0.8213 | 0.0803 | 0.0984 | 0.1156 |
| TCGA-HNSC | 80% | 0.8096 | 0.6577 | 0.1519 | 0.1904 | 0.2332 |
| TCGA-HNSC | 90% | 0.9038 | 0.8173 | 0.0865 | 0.0962 | 0.2329 |

由于构造方式如此，观察到的校准覆盖率与预先规定的目标非常接近。在 80% 配置下，约 65% 的校准患者使用增强预测，15% 回退，19%–20% 弃权。在 90% 配置下，约 82% 使用增强预测，8%–9% 回退，约 10% 弃权。

选择性 Brier 分数只描述未弃权患者中的性能。由于评价人群不同，不能将其解释为相对于 B2/B5/B6 的普通完整队列性能提升。Phase 5 必须检验在自然缺失、人工模态丢弃、捷径扰动和亚组分布偏移下，可靠性排序是否仍然有意义。

## 7. 输出

纳入跟踪的聚合输出：

- `results/metrics/phase4/model_metrics.csv`；
- `results/metrics/phase4/gate_metrics.csv`；
- `results/metrics/phase4/risk_coverage.csv`；
- `results/metrics/phase4/action_summary.csv`；
- `results/metrics/phase4/thresholds.csv`；
- `results/metrics/phase4/reliability_diagnostics.csv`；
- `results/metrics/phase4/model_status.csv`；
- `results/figures/phase4/model_comparison.svg`；
- `results/figures/phase4/risk_coverage.svg`；
- `results/figures/phase4/action_distribution.svg`；
- `docs/audits/phase4/leakage_audit.md`；
- `docs/audits/phase4/core_findings.md`；
- `results/manifests/phase4_trust_hn_receipt.json`。

患者级轨迹包含 B2/B5/B6 风险、模态增量、原始指标、相对于校准分布的排序、不可靠性分数、两种门控配置、原因和最终门控风险。这些文件继续被 Git 忽略。

收据中记录的冻结配置哈希：

- `phase4_trust_hn.json`：`25322f6b68927f267c98a7d017bca01a6ebe6debd434926b72dd6a2e844abb0d`；
- `phase4_governance.json`：`c34bc832c999dc69539088ad70a927a6278beb9db40426ee4c0f9b4f7bef7de1`。

## 8. 验证

- 完整测试套件：**57 passed**，仅有两个依赖项弃用警告；
- Phase 4 定向测试：**4 passed**；
- `src`、`scripts` 和 `tests` 的 Python 编译检查通过；
- 所有 Phase 4 代码和测试的定向 Ruff 检查通过；
- `git diff --check` 通过；
- 已确认 20 个规范 Phase 4 患者轨迹文件被 Git 忽略；
- 聚合 CSV 表头和拟纳入跟踪的输出内容中，不含被禁止的患者/样本标识符列，也不含可识别的 RADCURE/TCGA/GEO 原生 ID 模式；
- 已对照生成文件验证收据中的哈希。

## 9. 科学结论与下一阶段门槛

Phase 4 已**在授权的有条件范围内完成**。项目现在具备可运行的端到端开发实现，包括临床锚点、堆叠残差融合、不使用结局的 OOD 指标、bootstrap 不确定性、可靠性评分、由校准分布得到的配置，以及 AUGMENT/FALLBACK/ABSTAIN 决策。

当前证据仍然只是开发阶段证据。它不能证明分布偏移下的稳健性、外部有效性、前瞻性有效性、临床效用或可直接部署的最终阈值。RADCURE 的模态依赖型 TRUST-HN 仍处于阻塞状态。

**Phase 5 尚未获授权。** 进入 Phase 5 需要用户作出新的明确决定。Phase 6 锁定/外部评价必须继续保持封存，直到压力测试、分析冻结、不可变哈希和单独的明确授权全部完成。
