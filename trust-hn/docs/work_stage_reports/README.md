# Work-stage reports / 工作阶段报告

This directory preserves dated snapshots of the documents produced during each TRUST-HN work stage. English originals and Chinese translations are kept side by side so that project decisions, verification evidence, scientific boundaries, and next-stage gates remain traceable.

本目录用于保存 TRUST-HN 各工作阶段生成文档的带日期快照。英文原文与中文译文并列保留，以便持续追踪项目决策、验证证据、科学边界和下一阶段门槛。

## Directory layout / 目录结构

- `en/`: English historical snapshots / 英文历史快照。
- `zh-CN/`: faithful Simplified Chinese translations / 忠实的简体中文译本。
- The source files remain in their original project locations; archiving here does not move or replace them. / 原始文件继续保留在项目原路径；此处归档不会移动或替换原文件。

## Report mapping / 报告对应关系

| Document / 文档 | English snapshot / 英文快照 | Chinese translation / 中文译本 | Original source / 原始路径 |
|---|---|---|---|
| Phase 0 completion report / Phase 0 完成报告 | `en/2026-08-07_phase0_completion_report.md` | `zh-CN/2026-08-07_phase0_completion_report.md` | `PHASE0_REPORT.md` |
| Phase 1 progress report / Phase 1 进展报告 | `en/2026-08-07_phase1_progress_report.md` | `zh-CN/2026-08-07_phase1_progress_report.md` | `PHASE1_PROGRESS.md` |
| Phase 1 completion report / Phase 1 完成报告 | `en/2026-08-07_phase1_completion_report.md` | `zh-CN/2026-08-07_phase1_completion_report.md` | `PHASE1_PROGRESS.md`, `PROJECT_STATUS.md`, and Phase 1 audit/manifests |
| Project status / 项目状态 | `en/2026-08-07_project_status.md` | `zh-CN/2026-08-07_project_status.md` | `PROJECT_STATUS.md` |
| Phase 1 acquisition plan / Phase 1 数据获取计划 | `en/2026-08-07_phase1_acquisition_plan.md` | `zh-CN/2026-08-07_phase1_acquisition_plan.md` | `docs/phase1_acquisition_plan.md` |
| Project kickoff decision / 项目启动决策 | `en/2026-08-07_project_kickoff_decision.md` | `zh-CN/2026-08-07_project_kickoff_decision.md` | `docs/decisions/0001_project_kickoff.md` |

## Snapshot policy / 快照规则

- English files are immutable historical snapshots of the source documents at the time shown in the filename. / 英文文件是文件名所示日期时原始文档的历史快照。
- Chinese files preserve the same facts, dates, test counts, paths, identifiers, commands, risks, and gate decisions; code and identifiers remain untranslated where appropriate. / 中文文件保留相同的事实、日期、测试数量、路径、标识符、命令、风险和阶段门槛；代码及标识符按需要保留原文。
- Later changes to source documents do not silently overwrite an existing dated snapshot. Create a new dated pair instead. / 后续修改不得静默覆盖已有日期快照，应创建一组新的带日期中英文文件。
- Naming convention: `YYYY-MM-DD_<document_slug>.md`, using the same filename under `en/` and `zh-CN/`. / 命名规则为 `YYYY-MM-DD_<document_slug>.md`，并在 `en/` 与 `zh-CN/` 中使用相同文件名。

## Current scientific gate / 当前科学门槛

As of 2026-08-07, Phase 1 acquisition and feasibility auditing are complete with documented conditions. A conditional GO is recommended for Phase 2 adapters and descriptive analysis only, but Phase 2 remains unauthorized until explicit user approval. Locked and external outcomes remain unavailable to tuning.

截至 2026-08-07，Phase 1 数据获取与可行性审计已完成，并保留了明确的未决条件。当前建议仅有条件进入 Phase 2 的适配器构建和描述性分析，但在用户明确批准前 Phase 2 仍未获授权；锁定及外部结局仍不得用于调优。