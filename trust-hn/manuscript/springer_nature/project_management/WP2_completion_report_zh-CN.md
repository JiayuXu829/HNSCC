# TRUST-HN WP2 完成报告（故事化修订版）

**版本日期：** 2026-08-12
**工作包：** WP2 — 论证地图与逐段提纲
**状态：** 已完成修订，等待用户在 WP2 提纲审批检查点确认；未进入 WP3。

## 1. 本轮修订回应

本轮根据用户反馈完成四项结构性调整：

1. **标题加入 TRUST-HN。** 首选标题现为：
   **TRUST-HN: Reliability-aware multimodal prognostic modelling reveals cohort-dependent gains and failure boundaries in head and neck cancer**
   TRUST-HN 用于标识完整框架，后半句同时限定真实发现，避免把名称误读为“普遍可信”或“普遍优胜”的性能声明。
2. **核心叙事从实验清单改为学术论证。** 主旨改为：多模态价值相对于临床锚点是条件性的，其成败取决于数据生态与转移条件；TRUST-HN 的贡献是使增强、回退、弃权及失败边界可审计。
3. **Results 由 8 个分散段落合并为 5 个叙事单元。** 积极结果、核心失败、门控局限、反证证据和模型排序反转按因果与论证顺序组织，而不再按实验生成顺序罗列。
4. **Phase 8 移出当前正文计划。** 已删除 `MET-09`，标题、Abstract、Introduction、Results、Discussion、Methods 和主图表计划均不使用 Phase 8。只有边界说明保留：如未来另行批准进入 Supplement，必须称为 known-overlap workflow and bias simulation，明确 not validation。

## 2. 修订后的中心故事

论文不再尝试证明“多模态一定比临床更好”。它首先提出一个更临床、更可检验的问题：在异质性 HNSCC 数据生态中，附加模态何时能在临床锚点上提供可信的增量预后信息？

B6 的结果给出积极但有限的开端：RADCURE 和 HANCOCK 中出现有利点估计。GSE65858 随后构成全文转折：更丰富的跨平台转录组融合没有带来稳定收益，反而出现明显 Brier 和校准失败。这一失败说明，多模态信息的价值受到数据生态和转移条件约束。

B7 因此不是作为“更强模型”出现，而是作为强制融合风险的显式化机制。覆盖率和 AUGMENT/FALLBACK/ABSTAIN 让读者看到模型在何种病例上增强、回退或弃权；但配对结果同时表明，门控并不保证更准。它在 RADCURE 劣于 B6，在 HANCOCK/GSE41613 不确定，在 GSE65858 虽改善 B6，却仍明显劣于临床锚点 B2。

最后，Phase 5 失败、亚组警告、影像组学负对照、探索性 DCA 和 Phase 7 post hoc exploratory 排名反转共同限制过度解释。论文最终贡献不是一个性能冠军，而是一套以临床锚点为参照、明确条件性收益和失败边界的可审计融合原则。

## 3. 修订后的 Results 五单元

1. **RES-01：异质数据生态构成对条件性多模态价值的预设检验。**
2. **RES-02：多模态融合在 RADCURE/HANCOCK 获得增益，却在 GSE65858 失败。**
3. **RES-03：可靠性门控使强制融合风险可见，但不保证更优。**
4. **RES-04：反证分析限制机制、稳健性与临床解释。**
5. **RES-05：Phase 7 post hoc exploratory 比较再次显示生态依赖的模型排序。**

## 4. 修改文件

- `project_management/argument_map.md`
- `project_management/paper_outline_zh-CN.md`
- `project_management/paper_outline_en.md`
- `project_management/WP2_completion_report_zh-CN.md`
- `tools/validate_wp2.py`
- `README.md`

未修改：

- `main.tex`
- `sections/`
- Springer Nature 原模板
- 冻结模型、阈值、队列分区、终点、指标与结果资产

## 5. 证据接口与不可越界声明

- Phase 6：预设、一次性、回顾性锁定/OOD/外部/敏感性评价。
- B7：所有直接比较使用相同非弃权患者子集并同时报告覆盖率。
- GSE41613：仅为 HPV 阴性 OSCC 受限回顾性敏感性分析。
- Phase 7：所有实质性描述均标注 post hoc exploratory。
- DCA：仅为回顾性探索性曲线行为，不能建立 clinical utility、可部署阈值、治疗净获益或患者获益。
- Phase 8：当前正文不纳入。

## 6. 验证命令

```powershell
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp2.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp1.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\verify_evidence_freeze.py
git diff --check
git status --short --untracked-files=all
```

验证结果记录在本轮执行结束后的用户汇报中。

## 7. 剩余 TODO 与下一审批点

1. 用户确认首选标题及其约束性表述。
2. 用户确认“条件性多模态增益”是论文中心主旨。
3. 用户确认五单元 Results 叙事结构。
4. 用户确认 Phase 8 暂不进入正文。
5. 只有以上 WP2 提纲获得批准后，才进入 WP3；本轮不提前撰写完整正文。
