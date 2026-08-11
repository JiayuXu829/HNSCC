# inner_hancock 数据来源复核与论文策略调整报告

**日期：** 2026-08-11  
**状态：** 来源冲突尚未解除；未改写冻结结果或论文队列性质

## 1. 用户声明

用户说明 `inner_hancock` 是本院私有 HNSCC 队列，并要求将此前全部 HANCOCK 命名改为 `inner_hancock`，同时调整论文策略。

## 2. 本次工作区复核结果

当前目录名确实已经出现：

- `data/raw/inner_hancock/`
- `data/interim/inner_hancock/`
- `data/interim/phase1_audit/inner_hancock/`
- `data/interim/phase2/inner_hancock/`
- `data/manifests/inner_hancock/`

但是，目录中的实际数据资产仍可追溯到此前下载的公开 HANCOCK 数据：

1. `configs/phase1_sources.json` 把相关资产登记为 GitHub `ankilab/HANCOCK_MultimodalDataset` 固定提交，以及 FAU public data portal 的三个公开 ZIP 文件。
2. `data/raw/inner_hancock/*.receipt.json` 仍记录公开来源 URL、下载时间、原始相对路径 `data/raw/hancock/...` 和 SHA-256。
3. 对当前 `data/raw/inner_hancock/` 中四个 ZIP 重新计算 SHA-256，均与公开下载回执完全一致：
   - `DataSplits_DataDictionaries.zip`：匹配；
   - `HANCOCK_MultimodalDataset-...zip`：匹配；
   - `StructuredData.zip`：匹配；
   - `TMA_CellDensityMeasurements.zip`：匹配。
4. 解压目录包含公开 HANCOCK 仓库名称、官方数据拆分和公开结构化数据文件。
5. `data/interim/phase2/inner_hancock/adapter_records.csv` 的时间戳和既有 Phase 2 分析连续一致，没有发现新接入的院内原始数据或新的院内 manifest。
6. 当前 Git 状态显示原 `data/manifests/hancock/data_manifest.yaml` 和 `license_notes.md` 被删除，但没有对应的新院内来源 manifest。删除来源记录不能改变数据本身的来源性质。

因此，现有机器可读证据表明：当前 `inner_hancock` 是原公开 HANCOCK 数据目录的重命名，而不是已经接入并重新分析的独立院内患者队列。

## 3. 本次未执行的修改

为避免科研来源误述，本次没有：

- 把既有 HANCOCK 数值结果声明为院内私有结果；
- 批量替换 Phase 2–7 冻结配置、结果、图表和回执中的 HANCOCK；
- 删除公开 URL、许可证、数据论文引用或下载哈希；
- 把 held-out/OOD test 自动描述为外部或前瞻性院内验证；
- 沿用现有公开数据数值来支持“单中心私有队列验证”。

## 4. 有条件的论文策略调整

如果后续接入的确实是真实院内队列，论文可以调整为：

1. 将队列规范代码设为 `inner_hancock`，论文显示名称使用中性的 **Institutional HNSCC cohort**，避免暴露医院名称；
2. 将其描述为回顾性院内队列，除非有明确前瞻性方案，否则不能写成前瞻性验证；
3. 如果训练集和测试集来自同一医院，即使严格留出，也应写成 internal held-out validation，而不是 external validation；
4. RADCURE、TCGA-HNSC、GSE65858 和 GSE41613继续作为公开跨队列、跨模态或跨平台证据；
5. Methods必须补充伦理审批/豁免、知情同意处理、纳入时间范围、纳排标准、终点定义、随访截点、脱敏流程和数据不可公开原因；
6. Data availability应明确区分公开队列与受伦理/隐私限制的院内队列；
7. 所有使用真实院内数据的 Phase 2–7 实验必须重新运行，并生成新的结果、图表和回执，不能继承当前公开 HANCOCK 数值。

## 5. 解除冲突所需的最小材料

无需在对话中提供任何患者姓名、病历号或直接标识符。只需要在工作区提供以下之一：

- 真实院内数据所在的受控路径；或
- 一个不含患者标识符的院内 manifest/schema，至少列出文件名、样本量、数据模态、时间范围、终点字段和拆分方式。

建议目录：

```text
data/private/inner_hancock/
```

该目录必须加入 Git 忽略，并与当前公开 HANCOCK 资产分开保存。

## 6. 当前结论

在真实院内数据或可审计的院内 manifest 接入前，论文中不能把当前 `inner_hancock` 对应的既有结果写成私有院内数据结果。可以先保留 `inner_hancock` 作为计划中的规范代码名，但历史公开 HANCOCK 结果和来源记录必须保留，且不能通过字符串替换改变证据性质。
