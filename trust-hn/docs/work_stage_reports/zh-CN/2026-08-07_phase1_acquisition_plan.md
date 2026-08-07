# Phase 1 数据获取计划

**状态：** 网络执行正在等待明确批准。  
**需要记录的获取日期：** 实际下载时的 UTC 时间戳。

## 安全边界

只下载公开的临床或结构化表格、处理后特征矩阵、表达矩阵、数据字典和官方拆分文件。不得下载 RADCURE 影像、HANCOCK WSI/TMA 原始图像或受控访问基因组数据。

## Study 1：RADCURE + ORCESTRA

1. 从 TCIA 数据集合页面下载小型 RADCURE 临床电子表格，集合 DOI 为 `10.7937/J47W-NM11`。
2. 解析并下载方案中记录的 ORCESTRA 处理后 radiomic set，Zenodo DOI 为 `10.5281/zenodo.8332910`。
3. 记录 ORCESTRA 对象的确切版本，并核验其中是否包含 PyRadiomics、GTV 体积、随机体素特征、置乱体素特征、challenge split、扫描仪/年份变量以及 FMCIB 特征。
4. 不得下载约333 GB的完整影像归档，也不得下载约95 GB的 OPC 影像子集。

## Study 2：HANCOCK

1. 对采用 Apache-2.0 许可证的官方分析代码仓库进行快照或克隆。
2. 只从官方项目下载页面获取 `StructuredData`（约7 MB）、`DataSplits_DataDictionaries`（小于1 MB）和 `TMA_CellDensityMeasurements`（小于1 MB）。
3. 使用代码仓库 `features/` 目录中提供的已提取多模态患者向量。
4. 初始阶段跳过约100 MB的自由文本归档；只有在无法解释预提取文本特征时才考虑加入。
5. Phase 1 主审计不得下载 TMA/WSI、肿瘤标注、提取后的组织芯图像或约9 GB的 UNI 编码。

## Study 3：TCGA-HNSC、GSE65858和GSE41613

1. 从 GDC 下载开放访问、统一处理的 TCGA-HNSC 表达数据和临床文件，并冻结 GDC 数据发布版本及工作流元数据。
2. 下载 GSE65858 和 GSE41613 的 GEO series matrix 与平台注释。
3. 保留源数据的归一化元数据；不得先合并所有跨平台数据再执行 ComBat。
4. 可以解析外部队列结局以进行终点审计，但不得利用这些结局选择基因或通路、超参数、校准方法或门控阈值。

## 下载后必须执行的操作

- 将源文件设置为只读。
- 计算 SHA-256 和文件字节数。
- 填写每个数据集的 `data_manifest.yaml` 和 `license_notes.md`。
- 只允许解压到 `data/interim/<study>/<version>/`。
- 建立患者级 ID 清单，并立即检查患者重叠。
- 在根据真实字段完成核验前，所有人群、终点和特征声明均保留为 `pending`。