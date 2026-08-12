# TRUST-HN WP3 数值与数据报告规范

**版本日期：** 2026-08-12  
**状态：** WP3 冻结写作接口；适用于正文、表格、图、图注和 Supplement。  
**基本原则：** 冻结 CSV/JSON 保留全精度；稿件按本规范显示，不反向覆盖源结果。

## 1. 通用格式

| 内容 | 统一格式 | 示例 |
|---|---|---|
| 样本量 | `n=626`；分数形式用 `584/626` | `n=584 (93.3% coverage)` |
| 多个总体样本量 | 在列头或句中绑定队列 | `RADCURE (n=626)` |
| 百分比 | 1 位小数，包括 0 和 100 | `0.0%`, `93.3%`, `100.0%` |
| 置信区间 | `95% CI lower to upper` | `95% CI −0.01584 to −0.00183` |
| 范围连接 | 英文用 `to`；表头可用 en dash | 不使用含糊连字符 `-0.01--0.00` |
| 负号 | 使用真正的 Unicode minus `−` | `−1.494` |
| 明确方向差值 | 保留正号 `+` 或负号 `−` | `+0.00382` |
| 小数点 | 英文句点 | `0.0980`，不用 `0,0980` |
| 千位分隔 | 样本/重复次数用逗号 | `2,000 replicates` |
| 极小 p 值 | 原则上不新增；如冻结且必要写 `<0.001` | 不写 `p=0.000` |

## 2. 指标精度

| 指标 | 正文/主表默认精度 | 理由与例外 |
|---|---:|---|
| IPCW Brier score | 4 位小数 | 例如 `0.0980`。摘要可在版面受限时保持 4 位，不建议降至 3 位掩盖小效应。 |
| Harrell C-index | 4 位小数 | 与冻结主要结果一致。 |
| Uno C-index | 4 位小数 | 与 Brier/AUC 并列时统一。 |
| 24-month time-dependent AUC | 4 位小数 | 不与百分制混用。 |
| calibration-in-the-large | 3 位小数 | 例如 `−1.494`。 |
| calibration slope | 3 位小数 | 例如 `0.599`。 |
| mean predicted risk | 4 位小数或 1 位百分比 | 同一表内保持一致。 |
| coverage/action rates | 1 位百分比 | `93.3%`；包括 `100.0%`。 |
| paired metric difference | 5 位小数 | 小效应需保留方向和精度。 |
| paired difference 95% CI | 与差值相同精度 | `+0.00084 to +0.00718`。 |
| DCA threshold/net benefit | 阈值 2 位；净获益按源表足够精度 | 主文不强调单一阈值优效。 |
| seed SD | 4–5 位，跟随主指标量级 | 仅开发/Phase 7 需要；不冒充患者级 CI。 |

**四舍五入规则：** 只在最终显示层四舍五入。所有模型差值、置信区间和排序都从冻结源值读取，不得由已四舍五入的正文值重新相减。

## 3. 比较方向

### 3.1 固定定义

所有配对差值定义为：

> **first-listed model minus second-listed model**  
> **前列模型减后列模型**

例如 `B7−B6` 是 B7 指标减 B6 指标，而不是“改善量”。

### 3.2 方向解释

| 指标 | 负差值 | 正差值 |
|---|---|---|
| IPCW Brier | 有利于前列模型 | 有利于后列模型 |
| calibration error 的绝对值（如另行定义） | 需明确所用变换 | 需明确所用变换 |
| Harrell C / Uno C / AUC | 有利于后列模型 | 有利于前列模型 |

正文首次报告配对森林图时必须加一句：

> Differences were calculated as the first-listed model minus the second-listed model; negative IPCW Brier differences therefore favoured the first-listed model.

不得将 `B7−B6 = +0.00382` 写成“B7 improved Brier by 0.00382”。

## 4. B7 专用报告规则

### 4.1 绝对指标

B7 的每个绝对性能陈述必须同时给出：

1. 队列；
2. primary 90% gate 或明确的 sensitivity profile；
3. non-abstained coverage；
4. evaluated n（主表或同句可读取）；
5. 指标和 95% CI（若冻结源提供）。

示例：

> In RADCURE, B7 had an IPCW Brier score of 0.0913 at 93.3% non-abstained coverage (n=584).

该绝对选择性 Brier 不得与 B6 全队列 Brier 直接相减后宣称优效。

### 4.2 直接比较

B7 与 B6/B2 的直接比较必须：

- 使用 identical non-abstained subset；
- 报告 evaluated n 和 coverage；
- 报告“前列减后列”的点估计与 95% CI；
- 不用 CI 是否跨零之外的单词替代完整区间。

推荐句式：

> On the identical non-abstained subset (n=230; coverage 94.3%), the B7−B6 IPCW Brier difference was −0.00812 (95% CI −0.01584 to −0.00183).

### 4.3 动作比例

- `AUGMENT + FALLBACK + ABSTAIN = 100.0%`，容许显示层因四舍五入产生 0.1 个百分点误差。
- `non-abstained coverage = AUGMENT + FALLBACK`，用未四舍五入计数计算后显示为 1 位小数。
- 动作按固定顺序列出：`AUGMENT/FALLBACK/ABSTAIN`。

## 5. 95% CI 与不确定性

- Phase 6：2,000 次患者级配对 bootstrap；主结果优先报告点估计和 95% CI。
- Phase 7：1,000 次患者级配对 bootstrap，且必须标注 **post hoc exploratory**。
- 开发阶段五种子均值/SD 与患者级 95% CI 是不同不确定性来源，不得并列而不说明。
- 若 CI 跨零，写“the 95% CI included zero”或“the estimate was uncertain”；不要只写“not significant”。
- 若 CI 不跨零，仍不自动使用“clinically meaningful”或“confirmed superiority”；需考虑分析性质和指标方向。
- 不生成新 p 值，不从 CI 反推 p 值。

## 6. 绝对指标与校准的共同报告

- GSE65858 的判别指标不得脱离 IPCW Brier、calibration-in-the-large 和 calibration slope 单独称为成功转移。
- 当 Brier 与 C-index/AUC 排名冲突时，明确写为 discrimination–calibration trade-off，不选择性隐藏其中一类指标。
- calibration-in-the-large 理想值 0、slope 理想值 1；不可仅写“well calibrated”而不给数字或图。
- 常数/退化预测的 slope 为 not estimable 时应保留 `NE`/`not estimable`，不可填 0。

## 7. 表格规则

1. 每个表明确 cohort role、analysis nature、n、endpoint 和 horizon。
2. 模型行使用方法代码和短名称，例如 `B2, clinical anchor`。
3. B7 行单设 coverage 列；非 B7 模型可写 `100.0%`（若全队列均有预测）或 `NA—not applicable`，但同表需定义。
4. Phase 7 表题或方法列写明 `post hoc exploratory`。
5. GSE41613 表头或脚注明确 `restricted HPV-negative OSCC sensitivity analysis`。
6. 单元格不可用空白表达不可用；使用：
   - `NA` = not available；
   - `NE` = not estimable；
   - `NR` = not reported in this display；
   - `—` = not applicable，且表注说明。
7. 粗体只用于预先说明的阅读辅助，不暗示全局胜者；不因 Phase 7 事后排序自动加“best”。
8. 同一表中同一指标保持相同小数位。

## 8. 图形规则

- 轴标签包括时间窗和指标方向，例如 `24-month IPCW Brier difference (first − second)`。
- 森林图零线含义必须在图注解释。
- coverage 图的 x 轴明确为 `Non-abstained coverage (%)`，不是 sample retention。
- B7 action 配色在所有图中保持固定，建议顺序和图例为 AUGMENT、FALLBACK、ABSTAIN；WP4 再冻结具体颜色。
- 误差条注明 95% CI 和 bootstrap 次数/分析性质。
- 图中数字可比正文少 1 位小数以避免拥挤，但数据标签、补充表和图注必须可追溯；禁止因视觉简化改变排序或符号。
- DCA 图注必须写“retrospective exploratory”并否定 established clinical utility。

## 9. 文本范例

### 合规：积极但有限

> B6 yielded lower IPCW Brier point estimates than the B2 clinical anchor in RADCURE (0.0980 versus 0.1091) and HANCOCK (0.1122 versus 0.1393), whereas cross-platform transfer to GSE65858 deteriorated absolute-risk accuracy (0.2725 versus 0.1964).

此句描述点估计，不把非配对绝对值写成确认性优效。

### 合规：B7 配对比较

> On the identical non-abstained RADCURE subset (n=584; coverage 93.3%), the B7−B6 IPCW Brier difference was +0.00382 (95% CI +0.00084 to +0.00718), favouring B6.

### 合规：Phase 7

> In the Phase 7 post hoc exploratory analysis, C2 had a lower RADCURE IPCW Brier score than B6 (difference −0.00736, 95% CI −0.01162 to −0.00283), but its ranking did not transfer consistently across ecosystems.

### 不合规

- “B7 improved performance from 0.0980 to 0.0913”——比较了不同患者集合且未报 coverage。
- “GSE41613 externally validated TRUST-HN”——队列角色错误。
- “C2 was the best model”——忽略 post hoc 性质和生态排序反转。
- “The 90% safety threshold rejected unsafe patients”——将算法阈值与动作临床化。
- “DCA proved clinical benefit”——超出回顾性探索性曲线证据。

## 10. 核心数字的规范化显示示例

| 队列/比较 | 规范显示 |
|---|---|
| RADCURE B2/B6 | `0.1091/0.0980` |
| HANCOCK B2/B6 | `0.1393/0.1122` |
| GSE65858 B2/B6/B7 | `0.1964/0.2725/0.2672`; B7 coverage `94.3%` |
| GSE65858 B6 calibration | calibration-in-the-large `−1.494`; slope `0.599` |
| RADCURE B7−B6 | `+0.00382 (95% CI +0.00084 to +0.00718); n=584; coverage 93.3%` |
| GSE65858 B7−B6 | `−0.00812 (95% CI −0.01584 to −0.00183); n=230; coverage 94.3%` |
| GSE65858 B7−B2 | `+0.07294 (95% CI +0.04250 to +0.10389); n=230; coverage 94.3%` |

这些示例是显示规范，不替代 `evidence_map.csv` 或冻结结果表。
