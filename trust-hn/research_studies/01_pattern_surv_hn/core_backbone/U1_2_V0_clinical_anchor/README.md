# U1.2/V0 — Clinical-Pathological Elastic-Net Cox Safety Anchor

**阶段状态：** 实现与 repeated nested cross-fitting 完成，等待研究者审批  
**分析标签：** `post_lock_exploratory`

本目录隔离保存 PATTERN-Surv-HN 的 V0 安全锚点规范与 aggregate-only 审计。V0 使用 9 个术后 clinical-pathological anchor 变量，在 HANCOCK official-training 合格人群内执行 5 seeds × 5 outer folds、3 inner folds 的 nested cross-fitting。

## 核心实现

```text
src/trust_hn/pattern_surv_hn/v0_clinical_anchor.py
tests/test_pattern_surv_hn_v0.py
```

## 关键约束

- 每个 inner/outer training fold 独立拟合插补、缩放和类别映射；
- Cox baseline survival 仅由对应 training fold 拟合；
- official-test outcome 未派生、未暴露、未评估；
- patient-level OOF 仅写入 git-ignored `results/predictions/pattern_surv_hn/U1_2_V0/`；
- 本阶段未训练 V1/V2、calibration bridge 或 Global Value Router。

## 聚合结果

```text
IPCW Brier24          0.1247 ± 0.0015
Harrell C             0.6230 ± 0.0144
Uno C24               0.6442 ± 0.0138
AUC24                 0.6620 ± 0.0144
Calibration-in-large -0.0037 ± 0.0149
Calibration slope     0.9367 ± 0.0792
```

完整结果与治理审计见 `aggregate_v0_audit.json` 和 `../../audits/U1_2_V0_clinical_anchor_audit.md`。当前停在 `U1_2_V0_APPROVAL_ONLY`，不得自动进入 V1。
