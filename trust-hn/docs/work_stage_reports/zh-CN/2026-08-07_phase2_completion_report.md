# TRUST-HN Phase 2 完成报告

**日期：** 2026-08-07
**阶段：** 统一适配器与符合治理要求的描述性分析
**状态：** 已在用户批准的有条件范围内完成；Phase 3 仍未获授权。
**数据契约：** `2.0 / FROZEN_FOR_PHASE2`

## 1. 授权边界

已授权内容：三个数据集适配器；统一且带版本的患者数据契约；固定队列、终点和拆分定义；Table 1 候选统计；缺失热图；仅限开发集的事件和 Kaplan–Meier 汇总；仅使用协变量的训练集/校准集/测试集构成比较。

未授权且未执行：Phase 3 基线拟合、TRUST-HN 训练、特征或超参数调优、校准拟合、可靠性门控阈值选择，以及锁定/外部结局评价。

含有留出或外部结局列的原始源表曾作为源文件被解析，且 Phase 1 已审计过汇总事件数。但是，官方测试集/外部队列结局没有写入 Phase 2 适配器记录或 Git 跟踪输出，也没有用于预处理、选择、调优、校准、阈值确定或模型评价。这里不声称相关原始文件从未被打开。

## 2. 已交付实现

### 数据契约与治理

已创建：

- `configs/phase2_contract.json`
- `configs/phase2_governance.json`
- `data/schemas/unified_patient_record.schema.json`
- `src/trust_hn/data/contracts_v2.py`

保护措施包括：不可变记录；拒绝重复 ID 和无效终点；仅依据 ID 执行确定性、精确样本量的 SHA-256 训练/校准拆分；拒绝在封存或外部记录中保存结局；公共序列化移除 `native_id` 和 `source_row_number`。

### 适配器与编排

已创建或更新：

- `src/trust_hn/data/adapters/__init__.py`
- `src/trust_hn/data/adapters/radcure.py`
- `src/trust_hn/data/adapters/hancock.py`
- `src/trust_hn/data/adapters/transcriptomics.py`
- `src/trust_hn/data/phase2.py`
- `src/trust_hn/reporting/descriptive.py`
- `scripts/build_dataset.py`
- `configs/radcure.yaml`、`configs/hancock.yaml`、`configs/tcga_geo.yaml`
- `PROJECT_STATUS.md`、`README.md`

已实现 `RadcureAdapter`、`HancockAdapter` 和 `TranscriptomicsAdapter`。数据构建 CLI 仅接受：

```powershell
python3.12 scripts\build_dataset.py --phase phase2
```

该命令不包含 Phase 3 建模路径。

### 测试

已创建：

- `tests/test_phase2_contracts.py`
- `tests/test_phase2_adapters.py`
- `tests/test_phase2_reporting.py`

测试覆盖契约不可变性、封存结局抑制、标识符移除、确定性精确拆分、终点运算、负时长拒绝、队列纳入规则、月到日换算、完整适配器计数、Kaplan–Meier 坐标，以及不使用结局的队列构成比较。

## 3. 固定的队列与终点决策

| 研究 | 源数据/纳入数 | 开发集拆分 | 封存角色 | 固定终点/人群决策 |
|---|---:|---:|---:|---|
| RADCURE | 3,346 / 2,144 | 训练 1,215；校准 303 | 挑战测试 626 | 去空白并忽略大小写后精确等于 `Squamous Cell Carcinoma`；OS = `Last FU - RT Start`，首次放疗分次为起点。 |
| HANCOCK | 763 / 763 | 训练 489；校准 122 | OOD 测试 152 | 从诊断到最后信息/死亡；`survival_status == deceased` 为事件 1。 |
| TCGA-HNSC | 520 / 520 | 训练 416；校准 104 | Phase 2 无封存测试 | 519 个 OS 终点可用、1 个时长未解析；死亡使用最大非负 `days_to_death`，存活使用最大随访日数。 |
| GSE65858 | 270 / 244 | 无 | 外部测试 244 | `Primary AND distant_metastasis == 0 AND treatment != palliative`。 |
| GSE41613 | 97 / 97 | 无 | 敏感性 97 | HPV 阴性 OSCC 敏感性队列；源随访单位为月；`days = months x 30.4375`。 |

补充说明：

- RADCURE 排除 498 例非主要组织学和 704 例主要挑战拆分之外记录。3,346 组 `RT Start`/`Last FU` 均可解析且非负。`Length FU` 以诊断为起点，本阶段不使用。1 条记录的 `Date of Death` 与 `Last FU` 存在 80 天汇总差异，适配器统一使用源定义的 `Last FU`。
- HANCOCK 开发集中有 611 条可用终点记录。
- TCGA 表达特征采用惰性可用性表示，没有物化 `520 x 60,664` 建模矩阵。
- GSE65858 排除原因：非原发 16；远处转移 6；两者同时存在 1；姑息治疗 3。
- GSE41613 不作为一般 HNSCC 外部验证。来源：Chen 等，*Clinical Cancer Research* 2013，PMCID `PMC3593802`，PMID `23319825`。

## 4. 输出

患者级输出仅存在于 Git 忽略路径：

```text
data/interim/phase2/{radcure,hancock,tcga_hnsc,gse65858,gse41613}/adapter_records.csv
```

Git 跟踪的汇总输出：

- `results/metrics/phase2/cohort_flow.csv`
- `results/metrics/phase2/table1_candidates.csv`
- `results/metrics/phase2/missingness_summary.csv`
- `results/metrics/phase2/event_summary_development_only.csv`
- `results/metrics/phase2/kaplan_meier_development_only.csv`
- `results/metrics/phase2/composition_comparison.csv`
- `results/figures/phase2/missingness_heatmap.svg`
- `results/figures/phase2/event_distribution.svg`
- `results/figures/phase2/kaplan_meier_development_only.svg`
- `docs/audits/phase2/endpoint_audit.md`
- `results/manifests/phase2_adapter_receipt.json`

队列构成比较只使用协变量（年龄标准化均差、缺失比例差、分类变量总变差距离），并记录 `outcomes_used=False`。

## 5. 源版本与 SHA-256

| 数据对象/版本 | SHA-256 |
|---|---|
| RADCURE `v04_20241219/01_RADCURE_TCIA_Clinical_r2_offset.csv` | `18068176b5e92fbd57e4879610613ece6d123de3100be3016d22a3d5439eb8e0` |
| HANCOCK targets，Git `521b99b03a94008b28df5c3df4aa5f82aa14b25a` | `c6e8674cb304b1c90d3ea55570359e79ac2353b64ec201e1501726f558c08503` |
| HANCOCK TMA 细胞密度，同一快照 | `fb2468d284e29a067d5d08793de5e52c48978410a0145671cd81381466d48b99` |
| HANCOCK 官方拆分，同一快照 | `75b42a6dbd86207a4803629c3fe580cd18103c688595350abf13b1710ebc051f` |
| HANCOCK 临床 JSON，同一快照 | `355a53661f8e9a6b36dd7a5d66a57b650cd34cd3b87cbf7c91b4806fe7949bb4` |
| HANCOCK 病理 JSON，同一快照 | `9595b3427087bd4922147bf40321559f024c74d52b46c9c6a698c2751eaffaf5` |
| TCGA-HNSC GDC 临床响应 JSON | `df0d8bbd8345acdde6b2286252d07e3a605351fbeb8bb5fd77b1670e273aa72f` |
| TCGA-HNSC STAR-count 清单 TSV | `68b36aea7b8c4befeeaf310de39ab6cb5f6f8832e5af8f24560326b75566a6dc` |
| GSE65858 GEO 快照 `geo_2026-06-03` | `88b303164882ee37fe85170eaf7a71a08781e6809ede640233883b30aad355cd` |
| GSE41613 GEO 快照 `geo_2026-07-06` | `92c9adea26af6e58fbbfc87f74ad46b9aee688cfdce11c2cc2df90f84940ee17` |

契约哈希：

- `phase2_contract.json`：`8ce3633debeca7148c0e11a80bd582821f9a919a7bd3ec7b3bb9207f0ab56d40`
- `phase2_governance.json`：`ae489b5e9cb34ccd855107cf35936fcbcb9ab5a4d147e8aec3c9ee2c318cd952`
- 统一 JSON Schema：`3e76aa29862deade7d7e05f35bb036577d05ce79980f22383a749d737828405b`

所有输出哈希均列于 `results/manifests/phase2_adapter_receipt.json`。

## 6. 验证

执行命令：

```powershell
$env:PYTHONPATH='src;.'
python3.12 -m unittest discover -s tests -v
python3.12 -m compileall -q src scripts tests
python3.12 scripts\build_dataset.py --phase phase2
git check-ignore -v data\interim\phase2\radcure\adapter_records.csv
git diff --check
```

结果：

- **45 项测试全部通过**。
- Python 编译检查通过。
- Phase 2 构建通过并重新生成回执。
- 患者级文件已确认被 Git 忽略。
- Git 跟踪的 Phase 2 输出和报告中，RADCURE、TCGA、GEO 原生 ID 模式命中均为 0。
- Git 跟踪汇总 CSV 表头均不包含 `native_id`、`patient_id`、`sample_id` 或 `source_row_number`。
- HANCOCK ID 是短数字字符串，普通子串扫描不具特异性，因此通过汇总写入器和禁止 ID 列实施结构性保护。

## 7. 风险与 Phase 3 门槛

1. ORCESTRA RDS 尚未通过 R/Rscript 或经验证的解析器检查，RADCURE 放射组学建模继续保持阻塞。
2. 1 个 TCGA-HNSC 病例的 OS 时长未解析，继续排除在依赖终点的汇总之外。
3. 已记录的 RADCURE 80 天日期差异由固定的 `Last FU` 规则统一处理。
4. 跨研究协变量差异只用于描述，不能据此开展外部结局引导的数据协调。
5. Phase 2 证明的是数据准备状态，而不是预测性能、校准、临床效用或可靠性门控有效性。

**建议：在用户明确授权后，有条件进入 Phase 3 的临床与表达组学基线模型。**

**建议：在 ORCESTRA RDS 结构完成验证前，不进入 RADCURE 放射组学基线模型。**

任何 Phase 3 授权均应只涵盖基线实现和开发集内部验证，不应自动授权 TRUST-HN 核心训练、访问封存/外部结局、最终测试，或利用封存队列选择阈值。
