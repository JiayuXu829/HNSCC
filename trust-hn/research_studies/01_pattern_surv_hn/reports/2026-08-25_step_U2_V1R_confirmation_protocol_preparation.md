# PATTERN-Surv-HN U2/V1R confirmation protocol preparation

**Date:** 25 August 2026  
**Stage:** U2_V1R_CONFIRMATION_PROTOCOL_FREEZE_ONLY  
**Status:** DRAFT_PENDING_RESEARCHER_APPROVAL  
**Analysis label:** pre_registered_outcome_untouched_confirmation

## 1. What was done

The next experiment was translated into a pre-outcome-unseal protocol. No official-test or external outcomes were opened, no new model was trained, no calibration bridge was trained, no router actions were created, and no patient-level confirmation result was generated.

## 2. Next experiment defined

The next executable analysis is a frozen comparison of the approved V1R backbone against V0 on a future postoperative confirmation cohort whose outcomes remain untouched until the prediction artifact and all input/code/dependency hashes are sealed.

Primary estimand: paired delta Uno C at 24 months.  
Key safety estimand: paired delta IPCW Brier at 24 months, with the inherited +0.005 no-harm boundary.  
Mandatory operational checks: 100% coverage, exact empty-set fallback, supported-pattern worst Brier regret and calibration summaries without target recalibration.

The pre-unseal prediction artifact will contain 25 matched V0/V1R model members: five repetition seeds times five outer folds. Each member will reuse its already-selected inner-CV settings, use training-fold preprocessing and Breslow baseline hazards, and be sealed before confirmation outcomes are unmasked. Confirmation risk predictions will be the arithmetic mean of member-specific 24-month risks; ranking scores will be the arithmetic mean of member-specific linear predictors.

## 3. Governance decision

Under the current study registry, only protocol preparation/freeze is authorized. Execution is not authorized until the researcher approves the protocol and a suitable outcome-untouched confirmation cohort is identified and snapshotted.

## 4. Protocol artifact

research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_confirmation_protocol/frozen_confirmation_protocol.yaml

SHA256: DE81D86F21E371482A11235AD7775832D996A2D0AB2EBD1D03AE2C15953AC7A6

Approval request: research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_confirmation_protocol/approval_record.md

## 5. Next gate

After approval, the next implementation step is pre-unseal prediction generation only. The confirmation outcomes must remain sealed until the model artifact, input manifest, code and dependency hashes have been recorded.