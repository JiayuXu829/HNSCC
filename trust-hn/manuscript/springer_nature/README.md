# TRUST-HN Springer Nature manuscript project

This is the independent manuscript workspace required by the execution brief. The original template at `D:\medical_paper\HNSCC\Springer_Nature_LaTeX_Template` is treated as read-only and was not modified.

## Current stage

- Completed and approved: **WP0 — manuscript directory and read-only evidence baseline**.
- Completed and approved: **WP1 — row-level evidence map and bilingual claim matrices**.
- Revised, awaiting approval: **WP2 — story-driven argument map and paragraph-level outline**.
- Current WP2 thesis: multimodal prognostic gains are conditional on the data ecosystem; TRUST-HN makes augmentation, fallback, abstention, and failure boundaries auditable relative to a clinical anchor.
- Current Results plan contains **five narrative units**, not an experiment-by-experiment inventory.
- Phase 8 is excluded from the current main-text plan; any future use requires separate approval and Supplement-only known-overlap simulation wording.
- Manuscript prose has **not** been drafted, and `main.tex` has not been restructured.
- No model, hyperparameter, calibration rule, threshold, cohort partition, outcome, or frozen result was changed.

## Directory layout

- `main.tex`: working copy of the Springer Nature example article; conversion into the TRUST-HN skeleton remains scheduled for WP5.
- `sections/`: future main-text section files.
- `figures/`, `tables/`: manuscript-native figure/table assets only; frozen result figures remain in `results/`.
- `supplement/`, `checklists/`: supplementary manuscript and reporting checklists.
- `project_management/`: evidence inventory, freeze verification, WP reports, `evidence_map.csv`, bilingual claim matrices, argument map, and bilingual outlines.
- `tools/verify_evidence_freeze.py`: repeatable frozen-evidence integrity check.
- `tools/generate_wp1_evidence.py`: deterministic generator for the WP1 evidence map.
- `tools/validate_wp1.py`: source-locator, claim-boundary, denominator, CI, and Git-boundary validation for WP1.
- `tools/validate_wp2.py`: validates bilingual story structure, evidence/claim IDs, title and thesis requirements, B7 subset/coverage rules, Phase 7 labelling, Phase 8 main-body exclusion, high-risk wording, and Git boundaries.
- `project_management/argument_map.md`: titles, central thesis, scientific story, contribution hierarchy, argument/counterevidence chain, validity threats, and main/Supplement boundary.
- `project_management/paper_outline_zh-CN.md` and `paper_outline_en.md`: synchronized plans containing 4 Abstract, 4 Introduction, 5 Results, 6 Discussion, and 8 Methods units.
- `build/`: LaTeX build output.

## Build commands

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

```powershell
latexmk -C -outdir=build main.tex
```

The current `main.tex` remains the copied template baseline. Scientific restructuring begins at WP5 after the required outline and figure/table checkpoints.
