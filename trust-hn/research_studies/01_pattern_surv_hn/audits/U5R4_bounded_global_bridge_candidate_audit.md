# U5R4 V1R bounded global bridge candidate audit

**Date:** 2026-08-26  
**Phase:** development-only, post-hoc exploratory rescue  
**Decision:** `DEVELOPMENT_SAFE_EXPLORATORY_CANDIDATE_PASS`

## Scope and data boundary

This audit covers the fixed-candidate diagnostic defined in `core_backbone/U5R4_V1R_bounded_global_bridge_candidate/frozen_bounded_global_bridge_candidate_protocol.yaml`.

The runner read only repeated nested development OOF predictions from the HANCOCK official training cohort (610 eligible patients, 173 events; 5 repetition seeds ? 5 outer folds). It did not read confirmation outcomes, refit on confirmation, write patient-level tracked output, alter V1R predictions, train a router, or update the positive-results manuscript folder.

## Frozen bridge

Let `x_raw = logit(p_V1R)` and fit a single global affine transformation on the other development folds using the IPCW-Brier objective:

$$x_{base}=\alpha_{Brier}+\beta_{Brier}x_{raw},\qquad 0.75\leq\beta_{Brier}\leq1.25.$$ 

The applied bridge is fixed at 25% shrinkage toward identity:

$$x_{bridge}=x_{raw}+0.25(x_{base}-x_{raw}),\qquad p_{bridge}=\operatorname{sigmoid}(x_{bridge}).$$

The effective slope is $1+0.25(\beta_{Brier}-1)\in[0.9375,1.0625]$, so the transformation is strictly monotone and preserves V1R ranking within every held-out fold.

## Aggregate result

| Metric | Raw V1R | U5R4 bridge | Change / interpretation |
|---|---:|---:|---|
| IPCW Brier24 | 0.126637 | 0.126834 | +0.000198; below +0.005 boundary |
| CITL | +0.011680 | +0.005823 | absolute error change -0.005858 |
| Calibration slope | 0.825887 | 0.829295 | absolute error change -0.003408 |
| Evaluated rows | 2460 | 2460 | unchanged |
| Evaluated events | 415 | 415 | unchanged |
| Ranking | preserved | preserved | strict monotonicity confirmed in all folds |
| Worst supported-pattern Brier regret | reference | +0.000758 | below +0.020 boundary |

## Safety-gate result

- Global IPCW-Brier gate: **PASS**.
- Supported-pattern regret gate: **PASS**.
- CITL non-deterioration gate: **PASS**.
- Calibration-slope non-deterioration gate: **PASS**.
- Calibration-direction requirement: **PASS**.
- Ranking preservation and positive effective slope: **PASS**.
- Deterministic rerun: aggregate and artifact hashes matched exactly.

## Interpretation

U5R4 is a usable development-safe bridge candidate, not a confirmed bridge. It provides a conservative, global, rank-preserving risk-scale stabilization layer with small development Brier cost and modest calibration-direction improvement. The result supports moving to an independently reviewed, separately frozen confirmation application protocol; it does not itself authorize confirmation evaluation or deployment claims.

The earlier U5 bridge remains a historical failure review and is not rewritten. Raw V1R remains the retained backbone and clinical fallback behavior is unchanged.

## Integrity hashes

```text
{
  "frozen_protocol_sha256": "5E389A79309CE49E015DBF8A9EA3FA586028A5F17ECB0DDA81D81B31138A6A9C",
  "aggregate_results_sha256": "C4EDDFE618F684C0B8732D40B4BE6BEBE523A2A4AFE02F3909D5C0685B0CE7F0",
  "fold_results_sha256": "710402619A0CB649220FA04DA21ACF4ECF18C8082CCBFEF72E5290BE0121F12D",
  "pattern_results_sha256": "80086EDAC91B5C76B8F3E3A94A7354DBAD53B494F0B4F461A828C3E522CF0C20",
  "parameters_sha256": "1C969469C2E1885C310DC8875EEB1EF357ACC0DFEDB510A659989C4DC0D4B0FA",
  "audit_artifact_sha256": "8218665DA6ACF7E17E6BD0D2F7F3142D150460BA8FB22D2C7FB8351F77E934CD"
}
```
