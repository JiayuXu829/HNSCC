# U5/V1R calibration bridge protocol approval

**Status:** `APPROVED_FOR_PROTOCOL_FREEZE_AND_DEVELOPMENT_ONLY_EXECUTION`  
**Date:** 2026-08-26  
**Approved by:** Researcher (chat instruction: continue)  
**Analysis label:** `post_hoc_exploratory_rescue`

## Authorized scope

This approval freezes and permits development-only execution of a V1R calibration bridge. The bridge is a global IPCW-weighted logistic recalibration of the V1R 24-month absolute risk, with pattern-specific intercept and slope adjustments allowed only under support thresholds defined before execution.

The development analysis must be cross-fitted: bridge parameters for each held-out fold are fitted only on the other development OOF patients in the same repetition seed. The confirmation cohort may receive only the frozen development bridge; it may not be used for tuning, refitting, support-rule changes or patient removal.

## Explicitly out of scope

- router-label creation;
- Global Value Router training;
- FUSE/FALLBACK/RANK_ONLY/ABSTAIN actions;
- selective patient removal;
- confirmation-cohort refitting;
- clinical utility, deployment or external-validation claims.

## Frozen source

`core_backbone/U5_V1R_calibration_bridge_protocol/frozen_calibration_bridge_protocol.yaml`
