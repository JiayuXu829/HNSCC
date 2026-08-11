# WP0 冻结资产登记

**登记日期：** 2026-08-11  
**稿件工程：** `D:\medical_paper\HNSCC\trust-hn\manuscript\springer_nature`  
**原始模板：** `D:\medical_paper\HNSCC\Springer_Nature_LaTeX_Template`（只读参照，未修改）  
**呈现参考：** `D:\medical_paper\HNSCC\main_pj.pdf`（只读参照）

## 1. 冻结规则

1. Phase 6 是已经揭盲并完成的一次性锁定/外部回顾性评价；不得因论文写作重新调参、重新选择门控阈值、重做队列划分或覆盖结果。
2. Phase 7 新增比较方法全部标记为 **post hoc exploratory**，不得写成预设锁定比较。
3. Phase 8 `inner_hancock` 是已知与 HANCOCK 开发/校准/测试分区重叠的 pseudo-private overlap simulation；不得写成独立院内外部验证，也不得进入主文作为独立验证证据。
4. 患者级预测文件保持原位且只读；正文数字优先追溯至聚合 CSV/JSON、95% CI 和执行回执。
5. 论文工作只允许在 `manuscript/springer_nature/` 内新增或修改稿件文件。实验配置、代码、数据清单、结果、图和回执均视为只读证据。

## 2. 登记范围

本次读取并登记 **287** 个证据/参考资产，其中：

- `aggregate_metric`：43 个
- `analysis_configuration`：25 个
- `audit_document`：40 个
- `data_manifest`：15 个
- `execution_receipt`：10 个
- `latex_template_source`：25 个
- `manuscript_or_phase_plan`：5 个
- `master_implementation_plan`：1 个
- `patient_level_prediction`：53 个
- `phase_report`：33 个
- `preexisting_paper_draft`：4 个
- `presentation_reference_pdf`：1 个
- `project_governance`：7 个
- `reporting_checklist`：4 个
- `result_figure`：21 个


详细路径、大小和 SHA-256 见 `evidence_asset_manifest.csv`；读取/解析状态见 `source_reading_log.csv`。

## 3. 哈希核验

- 已执行登记哈希核验：126 条。
- 当前匹配：125 条。
- 非匹配：1 条。
- 唯一预期差异为 Phase 5 回执中的 `configs/analysis_freeze.yaml` 历史哈希；该文件在授权的 Phase 6 揭盲状态更新后发生变化。当前权威 `analysis_freeze.yaml` 内登记的配置、代码、测试和 sealed manifest 哈希全部匹配。
- Phase 6 聚合输出、Phase 6 揭盲前患者级预测、Phase 7 post hoc 输出、Phase 8 overlap-simulation 输出均与各自回执匹配。

逐条结果见 `freeze_verification.csv`。

## 4. 写作时必须保持的证据边界

- 可以：报告 B6 在 RADCURE 与 HANCOCK 的较好回顾性迁移；报告 GSE65858 的跨平台校准失败；报告 B7 改变覆盖率并执行 AUGMENT/FALLBACK/ABSTAIN；报告模型排序具有队列依赖性。
- 必须限定：B7 与比较模型的结论必须绑定队列、相同非弃权患者子集、覆盖率、指标及 95% CI；GSE41613 仅作受限敏感性分析；Phase 7 为事后探索。
- 禁止：普遍稳健性、前瞻性有效性、临床净获益、可部署门控阈值、患者获益、放射组学特异性生物学信号、统一跨生态最优模型、把 Phase 8 模拟结果称为独立院内验证。

## 5. 模板复制策略

复制到稿件工程的仅为 LaTeX 源文件、类文件、参考文献样式和示例图；原模板中的 `.aux/.log/.fls/.fdb_latexmk/.pdf` 等构建产物未复制。`main.tex` 当前仍是模板基线，WP5 才会改造成 TRUST-HN 可编译骨架。
