# TRUST-HN Springer Nature manuscript project

This is the independent manuscript workspace required by the execution brief. The original template at `D:\medical_paper\HNSCC\Springer_Nature_LaTeX_Template` is treated as read-only and was not modified.

## Current stage

- Completed: **WP0 — manuscript directory and read-only evidence baseline**
- Not started: WP1–WP12
- Manuscript prose has **not** been drafted.
- No model, hyperparameter, calibration rule, threshold, cohort partition, outcome, or frozen result was changed.

## Directory layout

- `main.tex`: working copy of the Springer Nature example article; it will be converted into the TRUST-HN skeleton in WP5.
- `sections/`: future main-text section files.
- `figures/`, `tables/`: manuscript-native figure/table assets only; frozen result figures remain in `results/`.
- `supplement/`, `checklists/`: supplementary manuscript and reporting checklists.
- `project_management/`: evidence inventory, freeze verification, and WP reports.
- `tools/verify_evidence_freeze.py`: repeatable integrity check.
- `build/`: LaTeX build output.

## Build commands

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

```powershell
latexmk -C -outdir=build main.tex
```

The current `main.tex` is only the copied template baseline. Scientific restructuring begins at WP5 after the outline and figure/table checkpoints.
