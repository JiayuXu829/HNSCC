# TRUST-HN WP1 声明矩阵（中文）

**版本日期：** 2026-08-11  
**状态：** WP1 工作文件；用于约束后续提纲、图表与正文，不构成正文草稿。  
**逐行证据索引：** `project_management/evidence_map.csv`

## 1. 使用规则

1. 每个进入论文的数字必须先在 `evidence_map.csv` 中找到唯一 `evidence_id`、来源文件、物理行号和（如适用）95%CI来源行。
2. Phase 6 是预设的一次性锁定/外部回顾性分析；不得因写作重新调参、重校准、换阈值或改队列。
3. Phase 7 全部写为 **post hoc exploratory**；不得写成预设锁定比较。
4. Phase 8 `inner_hancock` 全部写为 **known-overlap simulation / workflow and bias demonstration**，优先仅放补充材料；不得称为独立院内、私有或外部验证。
5. B7 是选择性预测。报告其任何性能时必须同时给出覆盖率；与 B6/B2 的直接比较只能使用相同的 B7 非弃权患者子集。
6. GSE41613 只代表 HPV 阴性 OSCC 敏感性分析，不代表一般 HNSCC 外部验证。
7. 决策曲线只作回顾性探索；不得据此声称已建立临床效用、净获益、患者获益或治疗价值。
8. 门控动作 AUGMENT/FALLBACK/ABSTAIN 是算法输出类别，不是治疗建议、分诊指令或可部署工作流阈值。

## 2. 状态词典

| `claim_status` | 含义 | 允许进入正文的条件 |
|---|---|---|
| `ALLOWED_WITH_ROLE_QUALIFIER` | 可报告的回顾性证据 | 必须写明队列、角色、指标、样本量/覆盖率和分析性质 |
| `DEVELOPMENT_ONLY` | 开发、校准或开发压力测试 | 不能写成外部验证；无bootstrap CI时不得暗示精确推断 |
| `SENSITIVITY_ONLY` | 受限敏感性证据 | 必须写明 GSE41613 的 HPV 阴性 OSCC 适用边界 |
| `POST_HOC_EXPLORATORY_ONLY` | Phase 7 事后探索 | 每次出现均需明确标注 post hoc exploratory |
| `EXPLORATORY_NO_CLINICAL_UTILITY` | 探索性DCA | 只能描述曲线/阈值范围内的观察结果，不能声称临床效用 |
| `ALLOWED_NEGATIVE_RESULT_NO_MODALITY_SPECIFICITY` | 负对照阴性结果 | 可写“不支持清晰优势”，不可写模态特异性生物学信号 |
| `OVERLAP_SIMULATION_ONLY_NOT_VALIDATION` | Phase 8 已知重叠模拟 | 仅可作流程、偏倚和代码行为演示，不能作独立验证 |
| `GOVERNANCE_BOUNDARY` | 分析治理锚点 | 只界定分析性质，不是模型性能证据 |

## 3. 可用声明及强制限定

| ID | 类别 | 稿件安全表述 | 强制限定 | 核心证据 |
|---|---|---|---|---|
| C01 | 队列构成 | RADCURE 划分为训练1215、校准303和锁定测试626例；HANCOCK为训练489、校准122和密封测试152例；TCGA-HNSC为训练416、校准104例；GSE65858外部测试244例；GSE41613敏感性队列97例。 | 人数必须按各自角色报告，不得把开发、校准与测试混合。 | `P2-FLOW-R014`–`R027`; `results/metrics/phase2/cohort_flow.csv` |
| C02 | Phase 6治理 | Phase 6 完成了预设的一次性回顾性锁定、OOD、外部和敏感性评价，并使用2000次配对bootstrap。 | 不得写“前瞻性”；不得暗示结局用于调参。 | `GOV-ANCHOR-001`–`004`; Phase 6回执 |
| C03 | RADCURE | 在RADCURE锁定测试中，B6的Brier为0.0980、Uno C为0.7740、24月AUC为0.7838；B2相应为0.1091、0.7078和0.7145。 | 这是队列内描述性对照；不要把未直接配对的B6-vs-B2绝对值写成确定性优越性检验。 | `P6-ABS-R002-*`, `P6-ABS-R005-*` |
| C04 | HANCOCK | 在HANCOCK回顾性OOD测试中，B6的Brier为0.1122、Uno C为0.8281、24月AUC为0.8476；B2相应为0.1393、0.7476和0.7864。 | 只限该官方OOD分区，不代表所有机构或所有分布偏移。 | `P6-ABS-R007-*`, `P6-ABS-R010-*` |
| C05 | GSE65858失败边界 | GSE65858显示跨平台转录组融合发生明显校准失败：B6 Brier 0.2725、整体校准偏差-1.494、斜率0.599；B7 Brier 0.2672、整体校准偏差-1.548、斜率0.560，而B2 Brier为0.1964。 | 必须与任何辨别力结果一起呈现；不得只选择性报告AUC/C指数。 | `P6-ABS-R012-*`, `P6-ABS-R015-*`, `P6-ABS-R016-*` |
| C06 | GSE41613 | 在97例GSE41613敏感性队列中，B2为常数/无辨别模型（Uno C和AUC均0.5）；B6/B7的辨别点估计较高，但Brier改善不确定。 | 只能称“HPV阴性OSCC敏感性分析”；不能称一般HNSCC外部验证。 | `P6-ABS-R017-*`, `P6-ABS-R020-*`, `P6-ABS-R021-*`; `P6-PAIR-R011`, `R012` |
| C07 | B7覆盖率 | 90%主门控的实际非弃权覆盖率具有队列依赖性：RADCURE 93.3%、HANCOCK 82.9%、GSE65858 94.3%、GSE41613 100.0%。 | 报告任何B7绝对性能时必须同时报告相应覆盖率。 | `P6-ABS-R006-*`, `R011-*`, `R016-*`, `R021-*`; Phase 6 action rows |
| C08 | B7配对结果 | B7未稳定优于B6：RADCURE B7-vs-B6 Brier差+0.00382（95%CI +0.00084至+0.00718；n=584）；HANCOCK +0.01058（-0.00947至+0.03186；n=126）；GSE65858 -0.00812（-0.01584至-0.00183；n=230）；GSE41613 -0.01314（-0.03153至+0.00215；n=97）。 | 差值均为相同非弃权子集；Brier负值有利于前列模型；同时给覆盖率。 | `P6-PAIR-R002`, `R005`, `R008`, `R011` |
| C09 | B7相对临床锚点 | B7相对B2的结果同样具有队列依赖性：RADCURE Brier差-0.00489；HANCOCK -0.00723且CI跨0；GSE65858 +0.07294；GSE41613 -0.00632且CI跨0。 | 不得概括为“B7普遍优于临床模型”。 | `P6-PAIR-R003`, `R006`, `R009`, `R012` |
| C10 | 门控动作 | B7能够产生AUGMENT、FALLBACK和ABSTAIN，且动作比例随队列和覆盖方案变化。 | 只描述算法行为；不能解释为临床决策或已验证安全措施。 | `P6-ACTION-*`; `results/metrics/phase6/action_summary.csv` |
| C11 | Phase 5压力测试 | Phase 5共有8项预设检查，7项通过；HANCOCK clean B7-vs-B6 Brier非劣性检查失败（+0.01550，标准≤0.01）。完全模态丢弃时，HANCOCK和TCGA-HNSC的100%方案均回退到B2，fallback rate=1.0。 | 仅为开发阶段压力测试；不能证明真实部署下安全或所有偏移可检测。 | `P5-CHECK-R002`–`R009` |
| C12 | 探索性亚组警示 | Phase 5最差亚组审计在TCGA-HNSC年龄≥65亚组中出现2个种子级标记。 | 探索性、多重比较且种子特异；不得升级为公平性或因果结论。 | `P5-FLAG-R055`, `P5-FLAG-R071` |
| C13 | 放射组学负对照 | RADCURE原始放射组学相对打乱/随机对照的B4–B7配对Brier差值95%CI均跨0；结果不支持原始放射组学具有清晰优势。 | 可写阴性结果；禁止声称已经证明放射组学特异性生物学信号。 | `P6-NEG-PAIR-*`; `radcure_negative_controls.csv` |
| C14 | DCA | 回顾性探索性DCA没有显示B7相对B6的一致净获益优势；RADCURE和HANCOCK的全部10个阈值均低于B6，GSE65858在8/10阈值低于B6。 | 不能声称临床效用、可部署阈值、治疗净获益或患者获益。 | `P6-DCA-*`; `decision_curve.csv` |
| C15 | Phase 7比较方法 | 事后探索性比较中，C2在RADCURE和HANCOCK表现强（Brier分别0.0907和0.1037），但在GSE65858明显失准/过预测（Brier 0.3429，整体校准偏差-1.935）。 | 必须在同一句或同一段标注post hoc exploratory并呈现跨队列失败。 | `P7-EXT-R003-*`, `R007-*`, `R011-*` |
| C16 | GSE65858探索比较 | 在GSE65858新增方法中C3的Brier最低（0.2050），但仍高于Phase 6 B2的0.1964。 | 不得称C3为该队列或全研究的统计学确定“最佳”模型，除非使用适当配对比较并保留事后探索限定。 | `P7-EXT-R012-IPCW-BRIER`; `P6-ABS-R012-IPCW-BRIER` |
| C17 | 模型排序 | C2等强基线在部分队列表现突出，但模型排序随数据生态改变；现有证据不支持跨全部生态的统一优胜模型。 | 这是跨队列综合解释，不是单一总体效应估计。 | Phase 6绝对/配对结果；`P7-EXT-*`; `P7-PAIR-*` |
| C18 | 参数共享边界 | 各临床/模态生态分别训练模型；研究检验共同可靠性原则，而不是所有队列共享同一组参数的通用HNSCC模型。 | Methods和Discussion均应明确。 | Phase 6报告第3节；冻结配置与各生态训练记录 |
| C19 | Phase 8 | `inner_hancock`中可报告流程模拟数值，例如B2/B6/B7/C2 Brier分别为0.1011/0.0807/0.0873/0.0679，B7覆盖率90.4%。 | 必须紧邻说明135例包含88训练、17校准、30既往测试重叠；只能用于流程/偏倚演示，优先补充材料。 | `P8-ABS-R004-*`, `R008-*`, `R009-*`, `R013-*`; `GOV-ANCHOR-007`–`011` |
| C20 | 总体结论 | 多模态增益、校准和门控行为具有明显队列依赖性；可靠性回退/弃权暴露了强制融合的失败边界，但当前回顾性证据没有建立普遍稳健性、可部署阈值或临床效用。 | 必须同时保留正结果、阴性结果和不一致结果。 | C03–C19的综合；不得脱离各队列证据 |

## 4. 只能在限定语境下使用的措辞

| 不建议裸用 | 可接受替代 |
|---|---|
| “validated” | “evaluated in a prespecified retrospective locked/OOD/external analysis”并写明具体队列 |
| “external validation”用于GSE41613 | “restricted retrospective sensitivity analysis in HPV-negative OSCC” |
| “B7 improved performance” | “B7 changed coverage; on the identical non-abstained subset, the paired difference was …” |
| “robust to distribution shift” | “performance and calibration were cohort dependent, with failure in cross-platform GSE65858 transfer” |
| “clinical net benefit” | “retrospective exploratory decision-curve net-benefit estimate”; 紧接“不建立临床效用” |
| “best model” | “lowest point-estimate Brier in this cohort/analysis”; 标明分析性质和不确定性 |
| “private/institutional validation”用于Phase 8 | “known-overlap pseudo-private workflow and bias simulation” |
| “safe fallback” | “algorithmic fallback behaviour”; 不暗示已经验证患者安全 |

## 5. 禁止声明

以下表述不得进入标题、摘要、正文、图注、补充材料、亮点或投稿信：

1. TRUST-HN已在所有分布偏移、平台或机构中证明普遍稳健。
2. 本研究完成了前瞻性验证、前瞻性临床试验或真实世界部署验证。
3. 90%门控或任何其他阈值已经是可部署、可推广或临床安全的阈值。
4. 决策曲线证明了临床效用、临床净获益、治疗获益或患者获益。
5. B7在所有队列中优于B6、B2或其他比较方法。
6. C2、B6、B7或任一方法是跨全部数据生态的统一最佳模型。
7. 原始放射组学结果证明了放射组学特异性生物学信号。
8. Phase 8 `inner_hancock`是独立院内、私有、外部或前瞻性验证。
9. 不同队列使用同一组共享参数，已经得到通用HNSCC模型。
10. AUGMENT/FALLBACK/ABSTAIN等同于治疗、转诊、随访或分诊建议。
11. 仅凭选择性B7绝对指标、不报告覆盖率，就声称性能改善。
12. 把Phase 7事后探索比较写成预设、锁定、主要或验证性分析。

## 6. WP2接口

WP2建立逐段提纲时，每个结果段必须列出：拟用声明ID、对应 `evidence_id`、队列角色、分析性质、样本量、覆盖率、95%CI、必须共现的阴性/限制结果，以及拟放主文还是补充材料。未能完成这些字段的结果句不得进入全文写作。
