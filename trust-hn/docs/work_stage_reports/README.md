# Work-stage reports / 工作阶段报告

This directory preserves dated snapshots of the documents produced during each TRUST-HN work stage. English originals and faithful Simplified Chinese translations are kept side by side so that project decisions, verification evidence, scientific boundaries, and next-stage gates remain traceable.

本目录保存 TRUST-HN 各工作阶段生成文档的带日期快照。英文原文与忠实的简体中文译文并列保留，以便持续追踪项目决策、验证证据、科学边界和下一阶段门槛。

## Directory layout / 目录结构

- `en/`: English historical snapshots / 英文历史快照。
- `zh-CN/`: faithful Simplified Chinese translations / 忠实的简体中文译本。
- Source files remain in their original project locations; archiving here does not move or replace them. / 原始文件继续保留在项目原路径；此处归档不会移动或替换原文件。

## Report mapping / 报告对应关系

| Document / 文档 | English snapshot / 英文快照 | Chinese translation / 中文译本 | Original source / 原始路径 |
|---|---|---|---|
| Phase 0 completion report / Phase 0 完成报告 | `en/2026-08-07_phase0_completion_report.md` | `zh-CN/2026-08-07_phase0_completion_report.md` | `PHASE0_REPORT.md` |
| Phase 1 progress report / Phase 1 进展报告 | `en/2026-08-07_phase1_progress_report.md` | `zh-CN/2026-08-07_phase1_progress_report.md` | `PHASE1_PROGRESS.md` |
| Phase 1 completion report / Phase 1 完成报告 | `en/2026-08-07_phase1_completion_report.md` | `zh-CN/2026-08-07_phase1_completion_report.md` | `PHASE1_PROGRESS.md`, `PROJECT_STATUS.md`, Phase 1 audits/manifests |
| Phase 2 completion report / Phase 2 完成报告 | `en/2026-08-07_phase2_completion_report.md` | `zh-CN/2026-08-07_phase2_completion_report.md` | Phase 2 contract, adapters, metrics, audit, and receipt |
| Phase 3 completion report / Phase 3 完成报告 | `en/2026-08-07_phase3_completion_report.md` | `zh-CN/2026-08-07_phase3_completion_report.md` | Phase 3 baselines, metrics, leakage/findings audits, figures, and receipt |
| Phase 4 completion report / Phase 4 完成报告 | `en/2026-08-07_phase4_completion_report.md` | `zh-CN/2026-08-07_phase4_completion_report.md` | Phase 4 residual fusion, reliability gate, metrics, audits, figures, and receipt |
| Project status / 项目状态 | `en/2026-08-07_project_status.md` | `zh-CN/2026-08-07_project_status.md` | `PROJECT_STATUS.md` |
| Phase 1 acquisition plan / Phase 1 数据获取计划 | `en/2026-08-07_phase1_acquisition_plan.md` | `zh-CN/2026-08-07_phase1_acquisition_plan.md` | `docs/phase1_acquisition_plan.md` |
| Project kickoff decision / 项目启动决策 | `en/2026-08-07_project_kickoff_decision.md` | `zh-CN/2026-08-07_project_kickoff_decision.md` | `docs/decisions/0001_project_kickoff.md` |

## Snapshot policy / 快照规则

- English files are historical snapshots for the date in the filename. / 英文文件是文件名所示日期的历史快照。
- Chinese files preserve the same facts, dates, test counts, paths, identifiers, commands, risks, and gate decisions. / 中文文件保留相同事实、日期、测试数、路径、标识符、命令、风险和阶段门槛。
- Later changes must not silently overwrite an existing dated pair; create a new dated pair when needed. / 后续修改不得静默覆盖已有日期文件；需要时应创建一组新的带日期中英文文件。
- Naming convention: `YYYY-MM-DD_<document_slug>.md`, with the same filename under `en/` and `zh-CN/`. / 命名规则为 `YYYY-MM-DD_<document_slug>.md`，并在 `en/` 与 `zh-CN/` 下使用相同文件名。

## Current scientific gate / 当前科学门槛

As of 2026-08-07, Phase 4 is complete within its conditional authorization and awaits user review before Phase 5. RADCURE modality-dependent B6/B7 remain blocked until the ORCESTRA RDS structure is validated. Phase 5 is not authorized, and locked/external Phase 6 evaluation remains sealed and unauthorized.

截至 2026-08-07，Phase 4 已在有条件授权范围内完成，当前等待用户审阅后再决定是否进入 Phase 5。在 ORCESTRA RDS 结构完成验证前，RADCURE 模态依赖型 B6/B7 仍处于阻塞状态。Phase 5 尚未获授权，锁定/外部 Phase 6 评价仍保持封存且未获授权。
