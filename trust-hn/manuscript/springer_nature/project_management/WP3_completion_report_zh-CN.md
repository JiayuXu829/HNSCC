# TRUST-HN WP3 完成报告

**版本日期：** 2026-08-12  
**工作包：** WP3 — 数据集、方法、终点、术语与数值写作规范化  
**状态：** 已完成，等待用户审批；**未进入 WP4**。

## 1. 完成内容

WP3 已把后续学术写作所需的命名和数据表达固定为可审计接口，避免 Abstract、正文、图表和 Supplement 在队列角色、方法名称、终点、覆盖率或差值方向上发生漂移。

本工作包完成：

1. 固定 RADCURE、HANCOCK、TCGA-HNSC、GSE65858、GSE41613 的论文显示名、数据来源性质、研究人群、模态背景、开发/评价角色、Phase 6 样本量和时间起点。
2. 对 `inner_hancock` 建立独立治理行：当前稿件排除；若未来另行批准，仅能称为 **known-overlap workflow and bias simulation; not validation**。
3. 从冻结配置和实现中核实并固定 B0–B7、M0、N0、C1–C4 的精确定义、输入、模型家族、科学角色、稿件用途和禁止解释。
4. 固定主要终点为 **24-month overall survival (24-month OS; 730.5 days)**，并统一各队列时间起点、全因死亡事件、早期删失、IPCW 及校准指标描述。
5. 明确区分三类 bootstrap：Phase 6 的 2,000 次患者级配对 bootstrap、Phase 7 post hoc exploratory 的 1,000 次患者级配对 bootstrap，以及可靠性不确定性组件的 20 模型 bootstrap ensemble。
6. 固定核心术语：clinical anchor、direct forced fusion、stacked residual fusion、reliability-aware gating、selective prediction、non-abstained coverage、fallback 和 abstention。
7. 固定数值精度、真正负号、显式正号、95% CI 写法、缺失/不可估类别和图表规则。
8. 固定所有配对差值为 **first-listed model minus second-listed model**；负 IPCW Brier 差值有利于前列模型。
9. 固定 B7 报告规则：绝对指标必须伴随 coverage；直接比较必须使用 identical non-abstained subset，并报告 evaluated n、coverage、差值及 95% CI。

## 2. 修改文件

新增：

- `project_management/cohort_dictionary.csv`
- `project_management/method_dictionary.csv`
- `project_management/endpoint_variable_dictionary.md`
- `project_management/terminology_style_guide.md`
- `project_management/numeric_reporting_standard.md`
- `project_management/WP3_completion_report_zh-CN.md`
- `tools/validate_wp3.py`

更新：

- `README.md`

未修改：

- `main.tex`
- `sections/`
- Springer Nature 原始模板
- `configs/`、`src/`、`data/`、`results/`、既有审计/阶段报告
- 模型、超参数、随机种子、门控阈值、队列分区、终点、结局或冻结结果

## 3. 证据与数据来源

WP3 只读取既有冻结证据，没有重新运行实验或生成新统计结果。主要来源：

- `docs/plans/manuscript_project/MANUSCRIPT_PROJECT_PLAN_zh-CN.md`
- `docs/plans/manuscript_project/CODEX_MANUSCRIPT_EXECUTION_BRIEF_zh-CN.md`
- `docs/audits/phase2/endpoint_audit.md`
- `docs/audits/phase3/baseline_findings.md`
- `docs/audits/phase4/core_findings.md`
- `docs/work_stage_reports/en/2026-08-07_phase2_completion_report.md`
- `docs/work_stage_reports/en/2026-08-07_phase3_completion_report.md`
- `docs/work_stage_reports/en/2026-08-07_phase4_completion_report.md`
- `docs/work_stage_reports/en/2026-08-08_phase6_report.md`
- `docs/work_stage_reports/en/2026-08-09_phase7_comparator_completion_report.md`
- `configs/phase3_baselines.json`
- `configs/phase4_trust_hn.json`
- `configs/phase6_evaluation.json`
- `configs/phase7_exploratory_benchmarks.json`
- `src/trust_hn/evaluation/endpoints.py`
- `src/trust_hn/metrics/survival.py`
- `src/trust_hn/models/residual_fusion.py`
- `src/trust_hn/reliability/gating.py`
- `src/trust_hn/phase7/models.py`
- `project_management/evidence_map.csv`
- `project_management/argument_map.md`
- `project_management/paper_outline_zh-CN.md`
- `project_management/paper_outline_en.md`

## 4. 关键标准化决定

### 4.1 队列显示名

正文固定使用：`RADCURE`、`HANCOCK`、`TCGA-HNSC`、`GSE65858`、`GSE41613`。`GEO` 仅在首次数据来源说明中使用，不作为每次出现的显示名前缀。

### 4.2 方法叙事

- B2：clinical elastic-net Cox **clinical anchor**。
- B5：direct clinical-plus-modality **forced-fusion comparator**。
- B6：TRUST-HN **stacked residual fusion**，不是固定系数 offset Cox。
- B7：TRUST-HN **reliability-gated selective prediction**，通过 AUGMENT/FALLBACK/ABSTAIN 使强制融合风险可见。
- C1–C4：全部为 Phase 7 **post hoc exploratory** comparators。

### 4.3 终点和删失

研究共享 24 个月（730.5 天）OS 预测时间窗，但时间起点按各数据源冻结定义，不能写成完全统一 index date。时间窗前删失者不作为 24 个月存活者；IPCW 评价权重为零。

### 4.4 数值表达

- Brier/C-index/AUC：默认 4 位小数。
- calibration-in-the-large/slope：默认 3 位小数。
- coverage/action rate：1 位百分比，包括 `0.0%` 和 `100.0%`。
- 配对差值与 CI：默认 5 位小数并保留显式正负号。
- 所有比较方向为前列模型减后列模型。

## 5. 允许声明

- 多模态信息相对于临床锚点的增量价值具有队列和转移条件依赖性。
- B6 在 RADCURE/HANCOCK 出现有利的回顾性点估计，而 GSE65858 出现明显跨平台绝对风险和校准失败。
- B7 改变非弃权覆盖率并执行算法性 AUGMENT/FALLBACK/ABSTAIN，但不保证优于 B6 或 B2。
- Phase 7 post hoc exploratory 比较显示模型排序随数据生态改变。
- TRUST-HN 的当前贡献是可审计地表达增强、回退、弃权及失败边界。

## 6. 禁止声明

- prospective validation 或 prospective clinical benefit；
- universal robustness、universal generalizability 或一个共享参数的通用模型；
- clinically useful、clinical utility established、deployment-ready 或 safe/deployable threshold；
- patient benefit、treatment benefit；
- radiomics-specific biological signal；
- C1–C4 的确认性优效或普遍最佳；
- GSE41613 为一般 HNSCC 外部验证；
- `inner_hancock` 为独立、私有、院内或外部验证；
- 将 AUGMENT/FALLBACK/ABSTAIN 写成临床决策。

## 7. 验证命令

```powershell
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp3.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp2.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp1.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\verify_evidence_freeze.py
git diff --check
git status --short --untracked-files=all
```

最终验证结果：

```text
WP3 validation: cohorts=6, methods=14, errors=0, warnings=0
WP2 validation: evidence_refs=235, errors=0, warnings=0
WP1 validation: rows=1717, errors=0, warnings=0
checked=287 mismatches=0
git diff --check: passed (README 仅有 LF/CRLF 工作区提示，无空白错误)
```

额外编码完整性检查确认：两个 CSV 字典中无字面问号或 Unicode replacement character，校验器已加入对此类编码损坏的防回归检查。

## 8. 冻结资产状态

**冻结资产未被修改。** WP3 只在 `manuscript/springer_nature/` 内新增或更新项目管理文件与校验器。没有重新读取结局进行新分析，没有重新计算点估计/CI，没有修改证据地图或已批准 WP2 叙事。

## 9. 剩余 TODO

1. WP4 根据已批准的五单元 Results 故事建立主图、主表和 Supplement 蓝图。
2. WP4 必须使用本 WP 的队列显示名、方法名、数值精度和 B7 比较规则。
3. 修订原计划中含 Phase 8 的旧式图表建议：当前 WP4 不为 Phase 8 设计正文图表。
4. 颜色、图形编码、主表列结构及每个 display 的 evidence_id 仍待 WP4 冻结。
5. 完整正文、`main.tex` 重构和图表制作尚未开始。

## 10. 下一审查点

请用户审批 WP3 的：

- 队列角色和显示名；
- B0–B7/M0/N0/C1–C4 定义；
- 24-month OS、删失与 IPCW 写法；
- B7 coverage/相同非弃权子集规则；
- 数值精度与比较方向；
- `inner_hancock` 当前排除边界。

只有获得批准后才进入 **WP4：主图、主表和补充图表蓝图**；本轮未进入 WP4。
