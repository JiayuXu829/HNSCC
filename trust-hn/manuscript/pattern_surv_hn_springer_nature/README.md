# PATTERN-Surv-HN Springer Nature manuscript

This directory is the current publication-facing manuscript workspace for an Article-style submission to *npj Digital Medicine* or a related Nature Portfolio/Springer Nature journal.

## Files

- `main.tex` — current Springer Nature `sn-nature` manuscript.
- `main.pdf` — compiled 15-page article preview.
- `references.bib` — working bibliography; verify every record against the primary source before submission.
- `generate_figures.py` — reproducible aggregate-only figure generator.
- `figures/` — publication-facing PDFs, 600-dpi PNGs, editable figure sources and `figure_manifest.json`.
- `supplementary.md` — authoritative editable source for the Supplementary Information.
- `generate_supplementary.py` — converts the markdown source into the same Springer Nature LaTeX template used by `main.tex`.
- `supplementary.tex`, `supplementary.pdf` — generated submission-facing Supplementary Information files.
- `MANUSCRIPT_NOTES_zh-CN.md`, `Q1_NPJDM_WRITING_BENCHMARK_2026_zh-CN.md` — editorial notes.
- `sn-jnl.cls`, `sn-nature.bst` — local Springer Nature template files.

## Build workflow

```powershell
D:\medical_paper\HNSCC\trust-hn\.venv\Scripts\python.exe .\generate_figures.py
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
D:\medical_paper\HNSCC\trust-hn\.venv\Scripts\python.exe .\generate_supplementary.py
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex
```

Edit `supplementary.md`, rather than generated `supplementary.tex`, when changing supplement wording or tables. The generator preserves the Nature-template preamble, converts the eight numbered supplementary tables to long tables and handles aggregate-artifact hashes without patient-level output.

## Current evidence architecture (1 October 2026)

The manuscript reports:

- HANCOCK acquisition/usability contract and development cohort flow.
- Repeated nested V1R development (610 patients; 173 deaths).
- U5R7 development-only calibration bridge.
- Locked outcome-untouched raw-V1R HANCOCK confirmation (152 patients; 40 events).
- Independent two-centre retrospective external validation of frozen CAM/SCRF predictions (125 patients; 59 deaths), with paired 95% intervals favouring SCRF for Uno C, AUC, Harrell C and IPCW Brier score.
- U5R8 locked secondary post-unseal bridge readout, identifying cohort-level probability recalibration as the next step for transportable absolute-risk output.
- U6R1 reliability-aware routing, U7R2 RADCURE characterization, U8 TCGA T1R replication and U8E GEO characterization.

The principal HANCOCK confirmation intervals cross zero, whereas the independent external-validation intervals exclude the null in the favourable direction. External calibration slope remains above one, and the transfer package lacks a timestamped prediction-seal receipt. The draft therefore claims retrospective external validation of incremental performance, but not prospective confirmation, calibration transport, clinical utility or deployment readiness. RADCURE, TCGA and GEO remain complementary benchmarking, method-transfer and platform-transport analyses.

## Figure inventory

- Main Fig. 1: author-provided architecture (PPTX/PDF/PNG).
- Main Fig. 2: cohort flow, acquisition/usability and pattern support.
- Main Fig. 3: V1R development performance, seed stability and safety.
- Main Fig. 4: U5R7 bridge and U5R8 post-unseal transport check.
- Main Fig. 5: locked raw-V1R confirmation forest plot.
- Main Fig. 6: independent external validation, usability patterns, coverage and calibration.
- Extended Data Figs. 1–4: router, RADCURE, TCGA T1R and GEO analyses.

All generated figures read aggregate JSON artifacts only. The Supplementary Information uses the same Springer Nature class as the main article and contains Supplementary Note 1, combined Supplementary Methods and Results, and Supplementary Tables 1–8. Patient-level predictions remain outside version control.

## Before journal submission

1. Replace remaining author, ethics, accession, archive, funding and CRediT `TBD` fields.
2. Verify every bibliography entry against the primary source.
3. Review every figure and supplementary table visually at 100% and 200% zoom.
4. Add the completed TRIPOD+AI checklist and PROBAST+AI assessment.
5. Add exact dataset accessions/versions and the public code/data DOI.
6. Update the generative-AI disclosure with the exact tool/version and journal wording.
7. Follow the target journal portal's current figure-source and LaTeX packaging instructions; embed `main.bbl` if required.
