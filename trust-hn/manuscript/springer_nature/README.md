# TRUST-HN Springer Nature manuscript project

This is the independent manuscript workspace required by the execution brief. The original template at `D:\medical_paper\HNSCC\Springer_Nature_LaTeX_Template` is treated as read-only and was not modified.

## Current stage

- Completed and approved: **WP0 — manuscript directory and read-only evidence baseline**.
- Completed and approved: **WP1 — row-level evidence map and bilingual claim matrices**.
- Completed and approved: **WP2 — story-driven argument map and paragraph-level outline**.
- Completed, awaiting approval: **WP3 — cohort, method, endpoint, terminology, and numeric-reporting standards**.
- Approved thesis: multimodal prognostic gains are conditional on the data ecosystem; TRUST-HN makes augmentation, fallback, abstention, and failure boundaries auditable relative to a clinical anchor.
- Approved Results plan contains **five narrative units**, not an experiment-by-experiment inventory.
- Phase 8 is excluded from the current main-text plan; any future use requires separate approval and Supplement-only known-overlap workflow/bias-simulation wording, explicitly not validation.
- Manuscript prose has **not** been drafted, and `main.tex` has not been restructured.
- No model, hyperparameter, calibration rule, threshold, cohort partition, outcome, or frozen result was changed.
- WP4 figure/table blueprint work has not started and requires the next user approval.

## WP3 writing interfaces

- `project_management/cohort_dictionary.csv`: binding cohort display names, source nature, population scope, modalities, analysis roles, sample sizes, time origins, and prohibited wording.
- `project_management/method_dictionary.csv`: binding definitions for B0–B7, M0, N0, and C1–C4.
- `project_management/endpoint_variable_dictionary.md`: 24-month OS, cohort-specific time origins, censoring, IPCW, bootstrap, metric, variable-group, and missing-value rules.
- `project_management/terminology_style_guide.md`: bilingual scientific vocabulary, abbreviations, B7 action meanings, cohort-role wording, and high-risk claim boundaries.
- `project_management/numeric_reporting_standard.md`: decimal precision, percentages, signs, confidence intervals, comparison direction, B7 coverage/subset reporting, and display conventions.
- `tools/validate_wp3.py`: validates the WP3 dictionaries, terminology/numeric contracts, Phase 7/Phase 8 boundaries, B7 rules, and Git write scope.

## Directory layout

- `main.tex`: working copy of the Springer Nature example article; conversion into the TRUST-HN skeleton remains scheduled for WP5.
- `sections/`: future main-text section files.
- `figures/`, `tables/`: manuscript-native figure/table assets only; frozen result figures remain in `results/`.
- `supplement/`, `checklists/`: supplementary manuscript and reporting checklists.
- `project_management/`: evidence inventory, freeze verification, WP reports, `evidence_map.csv`, bilingual claim matrices, argument map, bilingual outlines, and WP3 writing dictionaries.
- `tools/verify_evidence_freeze.py`: repeatable frozen-evidence integrity check.
- `tools/generate_wp1_evidence.py`: deterministic generator for the WP1 evidence map.
- `tools/validate_wp1.py`: source-locator, claim-boundary, denominator, CI, and Git-boundary validation for WP1.
- `tools/validate_wp2.py`: validates bilingual story structure, evidence/claim IDs, title and thesis requirements, B7 subset/coverage rules, Phase 7 labelling, Phase 8 main-body exclusion, high-risk wording, and Git boundaries.
- `tools/validate_wp3.py`: validates cohort/method completeness, endpoint semantics, terminology, numeric standards, completion reporting, and WP3 write boundaries.
- `project_management/argument_map.md`: titles, central thesis, scientific story, contribution hierarchy, argument/counterevidence chain, validity threats, and main/Supplement boundary.
- `project_management/paper_outline_zh-CN.md` and `paper_outline_en.md`: synchronized plans containing 4 Abstract, 4 Introduction, 5 Results, 6 Discussion, and 8 Methods units.
- `build/`: LaTeX build output.

## Validation commands

```powershell
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp3.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp2.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp1.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\verify_evidence_freeze.py
```

## Build commands

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

```powershell
latexmk -C -outdir=build main.tex
```

The current `main.tex` remains the copied template baseline. Scientific restructuring begins at WP5 after the required terminology and figure/table checkpoints.
