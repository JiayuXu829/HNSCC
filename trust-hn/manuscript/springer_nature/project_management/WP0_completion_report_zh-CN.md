# TRUST-HN 论文项目 WP0 完成报告

**日期：** 2026-08-11  
**状态：** 完成，等待 WP0 审查点确认

## 修改文件

- 新建 `manuscript/springer_nature/` 独立稿件工程。
- 复制 Springer Nature 模板源文件到独立工程，建立 `main.tex`、`references.bib`、`sections/`、`figures/`、`tables/`、`supplement/`、`checklists/`、`build/`。
- 新建 `project_management/evidence_asset_manifest.csv`、`source_reading_log.csv`、`freeze_verification.csv`、`template_source_manifest.csv` 和冻结规则说明。
- 新建可重复运行的 `tools/verify_evidence_freeze.py`。

## 证据来源

已读取并登记 Phase 0–8 中英文阶段报告、主实施文档、项目状态、冻结配置、数据清单、全部聚合指标、结果图、执行回执、患者级 Phase 6–8 预测、既有论文规划/草稿、Springer Nature 模板和 `main_pj.pdf`，共 287 个资产。

## 核验结果

- 当前 `analysis_freeze.yaml` 登记资产全部匹配。
- Phase 6 锁定聚合输出与揭盲前预测全部匹配回执。
- Phase 7 post hoc exploratory 输出全部匹配回执。
- Phase 8 pseudo-private overlap simulation 输出全部匹配回执。
- 发现 1 个有解释的历史哈希差异：Phase 5 回执记录的是 Phase 6 状态更新前的 `analysis_freeze.yaml` 哈希，不代表当前冻结资产被破坏。

## 编译/测试结果

- `tools/verify_evidence_freeze.py`：检查 287 个登记资产，`mismatches=0`。
- 读取/解析日志：287 个资产，解析警告为 0。
- `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex`：成功，生成 12 页模板基线 PDF。
- MiKTeX 仅提示“尚未检查更新”和模板字体替代警告；无致命 LaTeX 错误。
- 编译过程中产生的临时文件已限制在稿件工程并由本地 `.gitignore` 排除；原模板中一度被 MiKTeX 触碰的 5 个历史构建产物已按 Git 基线还原，并再次通过模板哈希核验。

## 剩余 TODO

- WP1：生成逐行可追溯的证据地图和中英文声明矩阵。
- WP2：建立论证地图和中英文逐段提纲。
- WP3：建立队列、终点、方法与术语词典。
- WP4：建立主图主表和补充图表蓝图。

## 是否触碰冻结资产

**否。** 仅在新建稿件目录内写入文件；原始模板、实验配置、代码、数据、结果、图和回执均未修改。

## 下一审查点

请确认：模板源路径、稿件输出路径，以及“实验资产只读、不得重新调参/选阈值/覆盖结果”的规则。确认后进入 WP1。
