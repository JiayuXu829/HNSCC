# PATTERN-Surv-HN 鈥?Submission readiness checklist

> Updated 20 September 2026. Working checklist tracking what is complete and what remains before journal submission. Not part of the manuscript.

## Complete

### Experiment
- V0 clinical-pathological anchor (full coverage, exact fallback): complete.
- V1R shrinkage-controlled residual fusion + development CV: complete.
- HANCOCK raw-V1R locked confirmation (152 patients / 40 events, directional signal): complete.
- U5R7 development-only calibration bridge: complete (development-only evidence).
- U5R8 locked secondary post-unseal validation (bridge gates failed): complete.
- U6R1 patient-level router exploration: complete (exploratory, uncertain).
- U7 external-confirmation protocol freeze: complete.
- U7R2 RADCURE external characterization: complete (adapted, non-confirmatory).
- U8 T1R transcriptome development CV: complete (internal post-hoc method replication).
- U8E T1R GEO characterization: complete (post-hoc descriptive cross-cohort evidence).
- Reproducibility: targeted pattern_surv_hn suite 41 passed, 0 failed (7 Sep 2026).

### Manuscript
- `manuscript.md`: complete draft; U6R1 + U7R2 exploratory extensions integrated.
- `supplement.md`: complete; S8 (router), S9 (RADCURE), S10 (U8) and S11 (U8E) added.
- `figure_legends.md` + figure framework spec: present.
- `V1R_positive/` source-of-truth files: present.
- `appendix_candidates/` (U5R grids, U6R1, U7R2): present.
- Claim audit: wording is bounded; no unqualified superiority / validation / utility / deployment claims.

## Remaining before submission

### Blocked (external data)
- Formal current-V1R external confirmation: blocked. No local cohort is simultaneously current-V1R-compatible and certified outcome-untouched (U5R11, U7). Requires acquiring a new qualifying cohort; the protocol is already frozen in `U7_external_confirmation_protocol_freeze`.

### Manuscript metadata (not yet written)
- Ethics / IRB statement.
- Dataset access and data-availability statement.
- Code availability statement.
- Author list and contributions.
- Funding and conflicts of interest.
- References.
- Target-journal formatting.

### Figures and tables
- Render Figure 1 from the framework spec (currently textual).
- Finalize Tables 1-3 (development, bridge, confirmation) and supplement tables S1-S3 and S8-S11.
- Confirm every table value against the aggregate JSON artifacts.

### Final checks
- Reporting-guideline compliance (e.g., TRIPOD for prognostic models).
- Statistical review of bootstrap and IPCW implementation.
- Run the full test suite and record the known frozen phase6 legacy failure separately.

