# TRUST-HN Phase 7 新增对比方法实验完成报告

**日期：** 2026-08-09  
**阶段性质：** Phase 7 事后探索性基准（post hoc exploratory benchmark）  
**状态：** 完成

## 1. 本阶段回答的问题

在论文正式写作前，本阶段补充了更具代表性的生存分析对比方法，并完成开发集和外部队列实验。由于 Phase 6 的锁定/外部结局已经查看，所有新增方法均明确标记为“事后探索性”，不能描述为 Phase 6 预设的锁定比较，也不能用于重新调整 TRUST-HN、B7 门控阈值或主要终点。

## 2. 方法数量

### 补充前

共有 **10 个带编号方法**：

- 6 个常规预测基线：B0–B5；
- 2 个 TRUST-HN 方法：B6–B7；
- 2 个审计或负对照：M0、N0。

若只计算与 TRUST-HN 竞争的常规预测基线，则补充前为 **6 个**。

### 本阶段新增

- **C1：Gradient Boosting Survival Analysis**，临床与附加模态直接融合；
- **C2：XGBoost-Cox**，临床与附加模态直接融合，并使用训练集 Breslow 基线风险转换24个月绝对风险；
- **C3：Late-fusion stacking**，临床模型和模态模型分别拟合，使用交叉拟合风险分数训练后期融合元模型；
- **C4：Missing-aware direct fusion**，直接融合 Cox 模型中显式加入模态缺失指示、缺失比例和全模态缺失标志。

### 补充后

共有 **14 个带编号方法**：

- 10 个常规预测基线/新增竞争方法：B0–B5、C1–C4；
- 2 个 TRUST-HN 方法：B6–B7；
- 2 个审计或负对照：M0、N0。

当前不建议继续无目的增加模型。Extra Survival Trees 与已有 B3 Random Survival Forest 信息重叠较大；DeepSurv 需要新增深度学习依赖、算力和额外调参，而且不一定提高论文证据质量。若审稿人明确要求，可作为后续补充，而不应在当前阶段继续扩展“模型动物园”。

## 3. 实验设计和规模

### 开发阶段

使用冻结的开发训练/校准分区：

- RADCURE：CT影像组学生态；
- HANCOCK：血液与TMA结构化病理生态；
- TCGA-HNSC：RNA-seq转录组生态。

每个方法采用5个确定性随机种子，在开发训练集生成严格的折外预测，并在冻结校准集评价。共得到：

- 3个开发数据集；
- 4个新增方法；
- 2个评价分区；
- 5个随机种子；
- 合计 **120 行成功指标结果，0个失败任务**。

### 外部事后探索评价

方法和超参数冻结后，先在不读取外部结局的条件下生成预测，再加载已经消费的 Phase 6 结局进行评价：

- RADCURE locked test，n=626；
- HANCOCK OOD test，n=152；
- GSE65858 external test，n=244；
- GSE41613 sensitivity cohort，n=97。

外部结果包括：

- 4个队列 × 4个新增方法 = **16行汇总指标**；
- C1–C4分别与B5和B6比较；
- 4项指标、每项1000次患者级配对bootstrap；
- 合计 **128行配对比较结果**。

## 4. 主要结果

### 4.1 RADCURE

C2 XGBoost-Cox 是新增方法中表现最强者：

- IPCW Brier = 0.09068；
- Uno C = 0.80674；
- 24个月AUC = 0.81818。

相对 B6：

- Brier差值 = -0.00736，95% CI -0.01162至-0.00283；
- Uno C差值 = +0.03272，95% CI +0.00705至+0.06054。

这是明确的事后探索性结果，说明在该影像组学生态中，非线性提升树直接融合值得作为强基线保留；不能据此重选 Phase 6 主模型或把 C2 描述为预设优胜模型。

### 4.2 HANCOCK

- C2获得最低Brier：0.10367；
- C1获得最高Uno C：0.84451；
- B6的Brier和Uno C分别为0.11219和0.82813。

但C1/C2相对B6的主要配对置信区间均跨越零。因此只能表述为点估计改善或竞争性表现，不能声称确定优于B6。

### 4.3 GSE65858

C3后期融合在新增方法中校准误差最低：

- Brier = 0.20499；
- Uno C = 0.64307；
- 相对B6的Brier差值 = -0.06755，95% CI -0.09043至-0.04585。

但是：

- 临床B2的Brier为0.19639，仍优于C3；
- C3校准截距为-0.93952，平均预测风险为0.34455；
- C2的Brier恶化至0.34287，平均预测风险0.54852。

因此新增比较没有推翻原结论：跨平台转录组融合仍存在明显校准和迁移问题。C3改善了B6的融合形式，但没有稳定超越临床锚点B2。

### 4.4 GSE41613

- C2获得最低Brier：0.24835；
- C1获得最高Uno C：0.69501；
- 但C1、C2和C3相对B6的Brier或Uno C置信区间大多跨越零。

该队列样本量仅97例，因此这些点估计只能作为敏感性和假设生成证据。

### 4.5 C4缺失感知融合

C4在四个外部队列的结果与B5数值一致。现有训练数据中的附加缺失变量没有产生可见的额外预测增益。这是一个有价值的阴性结果：简单加入缺失标志不足以自动改善直接融合，但不能推广为所有缺失机制下均无效。

## 5. 总体研究结论

1. 新增的四种方法提供了树提升、XGBoost-Cox、后期融合和缺失感知融合四类互补比较，当前方法覆盖已经足以进入论文写作。
2. 没有一个新增方法在全部生态中统一获胜；模型排序明显依赖队列、模态和平台。
3. C2在RADCURE中表现强，并在HANCOCK中具有较好点估计，但在GSE65858中出现严重风险高估，说明强判别能力不能替代跨平台校准验证。
4. C3在GSE65858中显著降低了相对B6的Brier误差，但仍未优于临床B2，支持“临床锚点和安全降级仍然必要”的论文主线。
5. 新结果不能支持“已证明统一分布偏移稳健性”“已完成前瞻性验证”“门控阈值可临床部署”或“已证明临床效用”等声明。

## 6. 新增文件和输出

### 配置、代码和测试

- `configs/phase7_exploratory_benchmarks.json`
- `src/trust_hn/phase7/__init__.py`
- `src/trust_hn/phase7/models.py`
- `src/trust_hn/phase7/runner.py`
- `scripts/run_phase7_exploratory.py`
- `tests/test_phase7_exploratory.py`

### 汇总级结果

- `results/metrics/phase7_exploratory/development_metrics_by_seed.csv`
- `results/metrics/phase7_exploratory/development_metrics_summary.csv`
- `results/metrics/phase7_exploratory/external_metrics.csv`
- `results/metrics/phase7_exploratory/external_benchmark_combined.csv`
- `results/metrics/phase7_exploratory/paired_comparisons.csv`

### 图和回执

- `results/figures/phase7_exploratory/development_comparison.svg`
- `results/figures/phase7_exploratory/external_comparator_forest.svg`
- `results/manifests/phase7_exploratory_prediction_receipt.json`
- `results/manifests/phase7_exploratory_receipt.json`

患者级开发和外部预测保存在 `results/predictions/phase7_exploratory/`，该目录由Git忽略。

## 7. 质量与治理检查

- 新增Phase 7测试：8项通过；
- 排除一个与当前“Phase 6结局已消费”状态冲突的历史前消费测试后，全项目97项测试通过；直接运行全部98项时，该历史测试仍错误地期待结局访问被拒绝，因此出现1项状态性失败，未修改冻结的Phase 6测试文件；
- 新增文件Ruff检查：通过；
- Phase 6登记文件：16/16哈希匹配；
- Phase 6结果未覆盖；
- B6/B7和门控阈值未重新调整；
- 外部结局未用于选择新增方法或调参；
- 所有新增外部比较均保留“post hoc exploratory”标签。

## 8. 下一步

新增对比实验已经满足进入论文写作前的比较方法要求。下一步应冻结结果解释边界，建立“数据集—方法—指标—图表—允许结论”的论文证据地图，然后开始论文提纲和主文/补充材料分配，不再根据外部结果继续挑选或调参。

