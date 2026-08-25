# U2/V1R residual-shrinkage rescue audit

**Audit date:** 2026-08-19  
**Status:** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**Analysis label:** `post_hoc_exploratory_rescue`

## Governance finding

The original U2 V1 result and frozen gate were not edited. V1R is a separately named,
result-informed candidate. Official-test and external outcomes were not accessed. Patient-level OOF
outputs remain git-ignored; tracked artifacts are aggregate-only.

## Frozen artifacts

| Artifact | SHA256 |
|---|---|
| `frozen_v1r_rescue_spec.yaml` | `7545E88D2F2DEF3D06CDD546734298F66B524C47538179D9F7E4F6CC1106D0F5` |
| `frozen_v1r_exploratory_gate.yaml` | `9C7BDBDD9B4834F12066BF50D3B75D80B67C975A0BD6D6412D1F2A1B2682DE2D` |
| formal aggregate audit | `449E2E72DC8F42E5B9E2CC4141C721DAD7B34A5E51B28782E3B31318DB171AE1` |
| formal patient OOF | `E43BB6C0D8E2C7F9C8B22A9C416AD752109B926A8526273D88811458CD73BCE0` |

## Gate audit

| Component | Unchanged original U2 threshold applied to V1R | Result |
|---|---:|---|
| V0/V1R coverage | 1.0 / 1.0 | PASS |
| exact fallback errors | 0.0 / 0.0 | PASS |
| parameter count | 3,225 <= 50,000 | PASS |
| mean Brier delta | -0.000407 <= +0.005 | PASS |
| worst supported-pattern regret | +0.009848 <= +0.020 | PASS |
| absolute CITL deterioration | +0.008843 <= 0.10 | PASS |
| slope-error deterioration | +0.085784 <= 0.15 | PASS |
| mean Uno-C delta | +0.021303 >= +0.01 | PASS |
| favorable Uno-C seeds | 5 >= 3 | PASS |

The unchanged original numerical thresholds applied to the new V1R candidate therefore return
`V1R_EARNS_COMPLEXITY`. This does not retroactively alter the original V1 decision.

## Reproducibility audit

- formal OOF rows: 3,050;
- 610 unique patients per seed, exactly once;
- deterministic rerun OOF SHA256: exact match;
- normalized aggregate payload: exact match;
- original V1 post-extension regression OOF SHA256: exact match to the frozen original;
- targeted V1/V1R tests: 23 passed;
- registered Phase 6 frozen-file guard: passed;
- targeted Ruff: passed.

## Risk and claim boundary

The rescue added result-informed selection flexibility: 3 penalties, 4 checkpoints, and 6 residual
scales. Although the residual scales share trained network states, this is a materially broader
inner-selection space than original V1 and can increase optimism. Seed 29 and pattern 101 retain
visible instability. Independent confirmation is mandatory before superiority or clinical claims.

## Audit conclusion

V1R is a reproducible provisional development backbone that passes the unchanged numerical U2
thresholds, but remains post-hoc exploratory. Stop for researcher approval before official-test,
external validation, calibration bridge, or router development.
