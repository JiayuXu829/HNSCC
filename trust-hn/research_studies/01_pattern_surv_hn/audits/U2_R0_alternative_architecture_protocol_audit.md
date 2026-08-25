# U2-R0 sequential alternative-architecture protocol audit

**Audit date:** 2026-08-18  
**Status:** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`  
**Analysis label:** `post_lock_exploratory`

## Scope

This was a protocol-only stage. It translated the researcher's request to try several alternative
architectures sequentially into a prespecified, auditable order. No model was implemented or
trained, no patient-level predictions were generated, and no official-test or external outcome was
accessed.

## Frozen artifacts

| Artifact | SHA256 |
|---|---|
| `frozen_sequential_architecture_protocol.yaml` | `BE195D834779C40F9D5937DA1A4135AADC8466F4D49A37AFC06B0B5246156227` |
| `frozen_candidate_selection_rules.yaml` | `973C41CFB35C2E6C83D25865E6F950F80D0A192DB631F1636817F58A8E1B5B00` |

Both YAML files parsed successfully after writing.

## Candidate order and rationale

1. **R1/CARS:** low-variance modality-score residual stacking to test whether incremental signal is
   extractable without another neural network.
2. **R2/CCADS:** minimal V1 neural redesign adding clinical context, masked attention, and residual
   shrinkage.
3. **R3/NE-GRME:** separate modality residual experts plus an exact NULL expert that can receive
   weight even when modalities are available.
4. **R4/CC-RST:** a small Set Transformer interaction candidate, conditional on evidence that
   interactions deserve additional complexity.

The sequence moves from low variance to higher representational complexity. It is not permitted to
select the best-looking failed candidate after observing all results.

## Common protection rules

- exact V0 reference and outer folds are reused;
- the frozen V0-vs-candidate complexity gate is not relaxed;
- each smoke and development-CV stage stops for approval;
- official-test and external outcomes remain sealed;
- tracked outputs remain aggregate-only;
- final router actions and calibration bridge remain outside scope;
- the first full development gate pass is provisional, not external confirmation.

## Audit conclusion

The protocol is internally consistent with the U2 negative result and the project's staged approval
governance. The next permissible action, after researcher approval, is only R1/CARS frozen
specification and smoke implementation.

## Final validation

- the two frozen YAML specifications parse successfully;
- SHA256 values match the hashes recorded above;
- PATTERN-Surv-HN U1-U2 regression tests plus the Phase 6 frozen-file guard: `41 passed`;
- `git diff --check` completed without whitespace errors;
- the U2-R0 artifacts were scanned for `U+FFFD` and accidental three-question-mark replacement artifacts, with no hits;
- unrelated changes under `.codex/skills/.system/` were not modified as part of this stage.

