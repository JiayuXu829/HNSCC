# U5R7 beta 0.90 log-loss bridge candidate audit

**Date:** 2026-08-26  
**Decision:** `DEVELOPMENT_SAFE_EXPLORATORY_CANDIDATE_PASS`

## Frozen specification

- Candidate: `beta_0.900_logloss`.
- Global transformation: `x_candidate = alpha_logloss + 0.90*x_raw`.
- Alpha fitting: weighted log-loss on non-held-out development folds only.
- No pattern-specific terms.
- Strictly monotone; ranking-preserving.
- No confirmation outcomes read or used.

## Results

| Metric | Raw V1R | U5R7 | Change |
|---|---:|---:|---:|
| IPCW Brier24 | 0.126637 | 0.126784 | +0.000147 |
| CITL | +0.011680 | -0.003796 | abs error -0.007884 |
| Calibration slope | 0.825887 | 0.881552 | abs error -0.055665 |
| Worst supported-pattern regret | ? | +0.004176 | PASS |
| Ranking | ? | preserved | PASS |

## Gate outcome

- Brier gate (`<= +0.0005`): **PASS**.
- Supported-pattern gate (`<= +0.005`): **PASS**.
- CITL improvement: **PASS**.
- Slope improvement: **PASS**.
- Ranking preservation: **PASS**.
- Coverage preservation: **PASS**.
- Deterministic rerun: **PASS**.

## Interpretation

U5R7 is the strongest current development-safe bridge candidate because it reduces the Brier cost relative to U5R4 while moving CITL and calibration slope more clearly toward their desired directions. This remains a post-hoc development result, not confirmation evidence. Raw V1R remains retained, and no paper-positive result was changed.

## Integrity hashes

```json
{
  "protocol_sha256": "F21B0949A6AE6048CD4F643AC7209CA8058A7BED1A98F9F4DCC4715776FD0C80",
  "aggregate_sha256": "DA21ABEA07CD4B59838CE1A2AE5F69F5C90E0790944FABEAF95DB17F4F32CDB2",
  "fold_sha256": "1FF8F5688F88ABF177F13FFB576120B89CAD530270A7E8A2BDEB1D3E8782B9FB",
  "pattern_sha256": "F9608FD97C6FA91C89F12474FA61CD8186C62B00D969191A0AE00F5348EE818B",
  "parameters_sha256": "EDFD4427A35754EF61AC82017EA52859E6BAB53AB8B1635EE76D2BBD710993C5",
  "audit_sha256": "5496430B121625EBC47A7B17AE1F5F8507972AD220C8479942D44CD61DBB3C06"
}
```
