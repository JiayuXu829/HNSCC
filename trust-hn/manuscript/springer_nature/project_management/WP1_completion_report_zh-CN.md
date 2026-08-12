# TRUST-HN 论文项目 WP1 完成报告

**日期：** 2026-08-11  
**状态：** WP1 已完成；等待进入 WP2 的检查点确认  
**范围：** 逐行证据地图、允许/禁止声明矩阵及其自动生成与验证；未开始论文正文

## 1. 修改文件

本工作包仅在 `manuscript/springer_nature/` 独立稿件工程内新增或修改下列文件：

- `project_management/evidence_map.csv`：逐行、可追溯的证据地图。
- `project_management/claim_matrix_zh-CN.md`：中文允许/限定/禁止声明矩阵。
- `project_management/claim_matrix_en.md`：英文允许/限定/禁止声明矩阵。
- `tools/generate_wp1_evidence.py`：从冻结结果与治理文件确定性生成证据地图。
- `tools/validate_wp1.py`：验证字段、来源定位、数值、95%CI、声明边界、动作率分母和 Git 写入边界。
- `README.md`：将当前阶段更新为 WP0、WP1 已完成，WP2 尚未开始。
- `project_management/WP1_completion_report_zh-CN.md`：本报告。

## 2. 证据来源

`evidence_map.csv` 共引用 24 个唯一的治理、指标或置信区间来源文件，覆盖：

- Phase 2 队列流程：`results/metrics/phase2/cohort_flow.csv`。
- Phase 4 开发/校准：模型指标、门控指标和动作汇总。
- Phase 5 压力测试：验收检查、运行状态和最差亚组标记。
- Phase 6 锁定分析：队列绝对指标、2000次bootstrap置信区间、配对比较、动作汇总、放射组学负对照和探索性DCA。
- Phase 7：开发汇总、外部指标及事后探索性配对比较。
- Phase 8：已知重叠 `inner_hancock` 模拟的绝对指标、1000次bootstrap置信区间、配对比较和动作汇总。
- 治理锚点：分析冻结配置、Phase 6锁定回执、Phase 7探索性配置和Phase 8已知重叠配置。

CSV 定位使用包含表头在内的1基物理行号；JSON/治理文件使用 JSONPath 风格定位。每个证据行均有唯一 `evidence_id`，并记录来源文件、来源行、声明状态、允许措辞、限制语及后续计划位置。

## 3. 证据地图规模

### 按阶段

| 阶段 | 行数 |
|---|---:|
| Governance | 11 |
| Phase 2 | 26 |
| Phase 4 | 760 |
| Phase 5 | 21 |
| Phase 6 | 416 |
| Phase 7 | 368 |
| Phase 8 | 115 |
| **合计** | **1717** |

### 按声明状态

| 声明状态 | 行数 |
|---|---:|
| `ALLOWED_NEGATIVE_RESULT_NO_MODALITY_SPECIFICITY` | 92 |
| `ALLOWED_WITH_ROLE_QUALIFIER` | 176 |
| `DEVELOPMENT_ONLY` | 781 |
| `EXPLORATORY_NO_CLINICAL_UTILITY` | 90 |
| `GOVERNANCE_BOUNDARY` | 11 |
| `OVERLAP_SIMULATION_ONLY_NOT_VALIDATION` | 115 |
| `POST_HOC_EXPLORATORY_ONLY` | 368 |
| `SENSITIVITY_ONLY` | 84 |
| **合计** | **1717** |

## 4. 生成、验证与冻结校验

在 `D:\medical_paper\HNSCC\trust-hn` 下运行：

```powershell
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\generate_wp1_evidence.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\validate_wp1.py
.\.venv\Scripts\python.exe manuscript\springer_nature\tools\verify_evidence_freeze.py
```

结果：

```text
wrote 1717 rows
WP1 validation: rows=1717, errors=0, warnings=0
checked=287 mismatches=0
```

WP1 未修改 LaTeX 骨架，因此本工作包不需要重新编译模板 PDF；WP0 的模板基线编译结果保持不变。

## 5. 关键质量检查

- Phase 2 将训练、校准、RADCURE锁定测试、HANCOCK回顾性OOD密封测试、GSE65858外部测试和GSE41613敏感性角色分开记录。
- Phase 6 所有 B7 绝对指标和直接比较均携带覆盖率；B7配对比较明确限定在相同非弃权患者子集。
- 配对证据区分父队列人数与实际共同子集人数，例如 RADCURE B7-vs-B6 为 `parent_n=626`、`evaluated_n=584`。
- 动作率使用完整动作汇总人数作为分母，而不是把单一动作计数误作分母；例如 Phase 8 为 `parent_n=evaluated_n=135`。
- Phase 7 全部标记为 `POST_HOC_EXPLORATORY_ONLY`。
- Phase 8 全部标记为 `OVERLAP_SIMULATION_ONLY_NOT_VALIDATION`，并记录88例训练、17例校准及30例既往测试重叠。
- GSE41613 全部维持 HPV阴性OSCC敏感性分析边界。
- DCA 行均包含“不建立临床效用或患者获益”的限制语。
- 放射组学负对照只支持阴性结果，不允许升级为模态特异性生物学声明。

## 6. 允许结论摘要

后续提纲和正文可以在保留限定语、队列角色、覆盖率及95%CI的前提下陈述：

1. RADCURE和HANCOCK中，B6显示了较好的回顾性迁移表现，但结论只限相应锁定/OOD分区。
2. GSE65858暴露了跨平台转录组融合的明显校准失败，不能只选择性报告辨别力。
3. B7可产生AUGMENT、FALLBACK和ABSTAIN并改变覆盖率，但相对B6或B2的结果具有队列依赖性，未显示稳定统一优势。
4. Phase 5八项预设检查中七项通过，HANCOCK的B7-vs-B6 Brier检查失败；这只能作为开发阶段压力测试证据。
5. 放射组学原始特征相对打乱/随机负对照没有清晰优势。
6. 探索性DCA没有显示B7相对B6的一致净获益优势。
7. Phase 7新增方法只能作为事后探索性结果；C2/C3等方法表现随队列改变，不存在跨全部数据生态的统一优胜模型。
8. Phase 8只能作为已知重叠工作流/偏倚模拟，不能作为独立院内验证。
9. 总体结论必须同时呈现正结果、阴性结果和不一致结果。

## 7. 禁止声明摘要

后续任何提纲、图表或正文均不得声称：

- 已完成前瞻性验证或建立前瞻性有效性。
- 已证明所有分布偏移下的普遍稳健性。
- 已建立临床效用、治疗净获益或患者获益。
- 已得到可部署门控阈值或已验证安全的临床动作规则。
- B7、B6、C2、C3或其他方法是跨全部生态的统一最佳模型。
- 当前研究训练了所有HNSCC队列共享同一参数的通用模型。
- 负对照证明了放射组学特异性生物学信号。
- GSE41613构成一般HNSCC外部验证。
- `inner_hancock` 构成独立院内/私有验证。
- 开发压力测试证明了真实部署安全性或所有偏移均可检测。
- 单靠DCA证明可采取临床决策。
- 未经相同非弃权子集比较即可概括B7优越性。

完整逐项规则见中英文声明矩阵，其中包含20组允许/限定声明和12项禁止声明。

## 8. 是否触碰冻结资产

**否。** 本工作包未修改原始 Springer Nature 模板、实验配置、代码、数据、结果、图、回执或任何冻结分析资产。冻结校验再次确认287个登记资产全部匹配，`mismatches=0`。

## 9. 剩余 TODO 与下一检查点

- WP2：建立论文核心论点、论证地图和中英文逐段提纲。
- WP3：建立队列/模态矩阵、方法词典和术语规范。
- WP4：建立主文/补充材料边界以及主图主表蓝图。
- 在提纲和图表检查点通过前，不开始完整正文。

**下一检查点：WP2（论证地图与逐段提纲），不是完整正文。**
