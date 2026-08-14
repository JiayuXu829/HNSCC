# U2/V1 Development CV Approval Request

**status:** `PENDING_RESEARCHER_DECISION`  
**requested_on:** 2026-08-14  
**analysis_label:** `post_lock_exploratory`  
**frozen_gate_decision:** `V1_DOES_NOT_EARN_COMPLEXITY`

## Approval object

Review completion of U2/V1 repeated development cross-validation and accept or reject the frozen V0-vs-V1 complexity-gate decision.

## Required findings to acknowledge

- [ ] U2 used only 610 eligible HANCOCK official-training patients and 173 events.
- [ ] V1 achieved 100% coverage and exact empty-modality clinical fallback.
- [ ] V1 used 3,225 trainable parameters and reproduced the frozen V0 OOF anchor to numerical precision.
- [ ] Mean Brier24 deterioration was within the overall noninferiority tolerance.
- [ ] The supported-pattern Brier-regret safety check failed (`+0.023779 > +0.020`).
- [ ] The calibration-slope safety check failed (`+0.213075 > +0.15`).
- [ ] Neither prespecified incremental-value path passed.
- [ ] The frozen final decision is `V1_DOES_NOT_EARN_COMPLEXITY`.
- [ ] V0 must remain the current core backbone unless a new stage is separately preregistered and approved.
- [ ] Official-test/external outcomes, V2, calibration bridge, and Global Value Router remain unauthorized.

## Researcher decision required

Choose and explicitly authorize one of the following; no option is automatic:

1. **Accept V0 retention and request paper/method redesign.** Consolidate the claim around the demonstrated failure boundary before defining further experiments.
2. **Authorize a separately preregistered development-only diagnostic/ablation stage.** This may investigate why V1 fails for supported patterns and calibration, but may not change the frozen U2 gate or access official-test/external outcomes.
3. **Stop the current backbone line.** Preserve U2 as a negative result and perform no further method development.

## Explicitly not authorized by approval of completion alone

- post-hoc gate-threshold changes;
- promotion of V1 despite the failed gate;
- V2 or wider architecture search;
- calibration bridge fitting;
- Global Value Router labels, actions, or training;
- official-test evaluation;
- external-outcome evaluation;
- claims of fusion superiority, transportability, routing benefit, or clinical utility.

## Suggested approval wording for option 2

> 审批 U2/V1 development CV 完成并接受 `V1_DOES_NOT_EARN_COMPLEXITY`；保留 V0 为当前 backbone。授权另行冻结 U2-D1 development-only failure diagnostic/ablation 方案；继续封存 official-test、外部结局、V2、calibration bridge 和 Global Value Router。
