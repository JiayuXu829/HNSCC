# PATTERN-Surv-HN Springer Nature manuscript

This directory contains a submission-oriented **living manuscript draft** for an Article-style submission to *npj Digital Medicine* or a related Nature Portfolio/Springer Nature journal.

## Files

- `main.tex` — single-file Springer Nature manuscript using `sn-nature` style.
- `references.bib` — working bibliography; verify every author list, title, issue/page and recent conference record before submission.
- `main.pdf` — compiled preview.
- `MANUSCRIPT_NOTES_zh-CN.md` — Chinese editorial rationale, completed evidence, placeholders and next actions.
- `sn-jnl.cls`, `sn-nature.bst` — copied from the local Springer Nature template.
- `figures/` — reserved for final standalone figure files.

## Build

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The current build succeeds with no unresolved citations/references and no overfull-box warnings. MiKTeX may still print its local package-update reminder.

## Evidence status on 14 August 2026

Completed and reportable:

- HANCOCK postoperative data contract.
- V0 clinical-pathological elastic-net Cox anchor.
- Eligible official-training population: n=610, deaths=173.
- Repeated nested cross-fitting: 5 seeds × 5 outer folds × 3 inner folds.
- Aggregate V0 metrics shown in the manuscript.

Not completed and therefore marked `\TBD{...}`:

- Deep Sets/Set Transformer residual fusion.
- Calibration bridge.
- Cross-fitted value/reliability router.
- Natural/unseen/corrupted pattern comparisons.
- TCGA-to-GEO calibration-event experiments.
- New RADCURE negative-control replication under PATTERN.
- Outcome-untouched external or temporal confirmation.
- Author, funding, ethics, repository and archival metadata.

## Non-negotiable claim boundary

RADCURE, HANCOCK official test, GSE65858 and GSE41613 have previously outcome-seen status. They may support post-lock exploratory analyses but must not be described as newly untouched validation. The manuscript must remain a living scaffold until all frozen analyses are complete.

## Before journal submission

1. Replace every red `TBD` field.
2. Verify all references against primary sources; the 2026 MIDL record is explicitly provisional.
3. Add final standalone figure files and replace boxed placeholders.
4. Add a participant-flow figure and supplementary cohort contract.
5. Complete TRIPOD+AI checklist and PROBAST+AI self-assessment.
6. Freeze model, calibration and routing thresholds before any untouched-cohort outcome access.
7. Add exact data/code archive links, ethics language, CRediT roles, funding and competing interests.
8. Update the generative-AI disclosure with exact tools/versions and the journal policy current at submission.
9. For final Nature Portfolio eJP submission, follow the journal portal's current LaTeX packaging instructions; if requested, embed the generated `.bbl` reference list into the single main `.tex` file.
