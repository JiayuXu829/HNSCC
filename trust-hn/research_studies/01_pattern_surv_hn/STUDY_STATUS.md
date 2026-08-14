# PATTERN-Surv-HN Study Status

**最后更新：** 2026-08-14
**当前步骤：** U1.2/V0 — extended postoperative clinical-pathological elastic-net Cox safety anchor
**状态：** `COMPLETE_AWAITING_RESEARCHER_APPROVAL`
**分析标签：** `post_lock_exploratory`

## 已完成

- [x] U1.1 数据契约已于 2026-08-14 获研究者审批。
- [x] 冻结 V0 estimand、9 个 anchor variables、5×5 outer repeated CV、3-fold inner selection 和 12 个 Coxnet candidates。
- [x] 实现 fold-pure preprocessing、training-fold baseline survival、continuous risk 与 24-month probability。
- [x] HANCOCK official-training eligible n=610/events=173 完成 repeated nested OOF；3050/3050 rows。
- [x] 两次正式重跑 OOF SHA256 完全一致。
- [x] tracked artifact 仅保存聚合结果；patient-level OOF 位于 git-ignored predictions 目录。
- [x] official-test 152 条 outcome 未派生、未暴露、未评估。
- [x] U1.1+U1.2 tests 18 PASS；related Phase 2/3 tests 23 PASS；full suite 118 PASS / 1 known frozen Phase 6 legacy FAIL。
- [x] dependency files 与 frozen Phase 3–6 key paths 未修改。

## V0 聚合结果

```text
IPCW Brier24          0.1247 ± 0.0015
Harrell C             0.6230 ± 0.0144
Uno C24               0.6442 ± 0.0138
AUC24                 0.6620 ± 0.0144
Calibration-in-large -0.0037 ± 0.0149
Calibration slope     0.9367 ± 0.0792
```

这些结果只支持 V0 作为内部 post-lock exploratory safety anchor，不支持融合增益、外部泛化或临床效用 claim。

## 当前审批门

等待研究者审阅：

```text
approvals/U1_2_V0_APPROVAL_PENDING.md
audits/U1_2_V0_clinical_anchor_audit.md
reports/2026-08-14_step_U1_2_V0_clinical_anchor.md
```

**GO（若明确批准）：** 只进入 U1.3/V1 smoke implementation，验证最小 Clinical-Residual Deep Sets Cox 的结构和 exact fallback。

**NO-GO：** 未审批前启动 V1；或启动正式 V1 development CV、V2、新依赖安装、calibration bridge、Global Value Router、official-test/外部 outcome 评估。