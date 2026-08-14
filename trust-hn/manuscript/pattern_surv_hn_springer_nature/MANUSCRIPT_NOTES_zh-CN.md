# PATTERN-Surv-HN 论文初稿编辑说明（中文）

## 1. 这篇论文现在被组织成什么故事

核心不是“我们做了一个更大的 Transformer，并把 C-index 提高了多少”，而是一个更符合高水平数字医学审稿逻辑的问题：

> 多模态证据并非越多越好。模型应该以稳定的临床病理风险为锚点，仅在额外模态具有可信增量价值时融合；当模态缺失、损坏、跨平台失准或只包含捷径信息时，应回退、只报告排序，或拒绝输出不受支持的绝对风险。

全文围绕四个必要组件展开：

1. postoperative clinical-pathological anchor；
2. residual set survival backbone；
3. pattern/domain calibration bridge；
4. cross-fitted value and reliability router。

相应动作是 `FUSE / FALLBACK / RANK_ONLY / ABSTAIN`。这种叙述比单纯追求平均性能更容易形成“临床问题—方法原则—严格验证—安全边界”的完整贡献链。

## 2. 为什么采用 npj Digital Medicine 风格

初稿按 Nature Portfolio Article 的常见逻辑组织：

- 无小标题的 Introduction；
- Results 使用信息型小标题；
- Discussion 在 Methods 之前；
- Methods 详细到可以冻结实验；
- 单独列出 Data availability、Code availability、Acknowledgements、Author contributions 和 Competing interests；
- 摘要不引用文献，保持约 200 词量级的非结构化叙述；
- 强调透明报告、验证类型、校准、适用性和不过度宣称。

主文目前约 19 页，包含 6 个主图框架和 5 个主表。

## 3. 现在真正已经完成的结果

目前只有 V0 临床病理锚点可作为 PATTERN 新研究的实际结果：

- HANCOCK official-training eligible：n=610，events=173；
- 5 seeds × 5 outer folds × 3 inner folds nested cross-fitting；
- IPCW Brier24：0.1247 ± 0.0015；
- Harrell C：0.6230 ± 0.0144；
- Uno C24：0.6442 ± 0.0138；
- AUC24：0.6620 ± 0.0144；
- calibration-in-the-large：−0.0037 ± 0.0149；
- calibration slope：0.9367 ± 0.0792。

当前只允许解释为：内部 OOF 中等区分度、24 个月平均校准大致可接受，可作为后续 FALLBACK 的探索性安全锚点。

不能据此声称：

- 已解决缺失模态；
- 融合优于临床模型；
- router 有效；
- calibration bridge 有效；
- 已实现外部泛化或临床效用。

## 4. Results 为什么保留大量占位符

一篇冲击一区 10 分左右期刊的稿件，最忌讳在实验未完成时提前写出“预期阳性结果”。因此初稿采用 living manuscript：

- 已完成数字正常写入；
- 未完成数字统一用红色 `TBD`；
- 每个结果小节提前定义比较对象、估计量、图表和什么结果才支持什么结论；
- 同时写明阴性结果将怎样改变论文解释。

这使论文初稿可以直接指导实验，而不会破坏研究治理。

## 5. 主图逻辑

1. **Figure 1：临床场景与完整架构**——说明 prediction time、anchor、set fusion、calibration bridge 和 router。
2. **Figure 2：HANCOCK 自然模态模式**——UpSet 图，区分 acquired、usable 和 internally partial。
3. **Figure 3：缺失/未见组合/损坏鲁棒性**——以 Brier、校准和 worst-pattern regret 为主。
4. **Figure 4：排序迁移与概率迁移分离**——目标域事件数从 0 到 40 的校准恢复曲线。
5. **Figure 5：负对照与 present-but-invalid 模态**——真实 radiomics 对 volume、permuted、Gaussian、volume-matched controls。
6. **Figure 6：risk–coverage、安全后悔与最终 untouched validation**。

## 6. 论文能否达到高影响力标准的关键门槛

方法复杂度不是主要门槛，证据链才是：

- 临床预测时间必须一致且不使用 adjuvant/post-index 变量；
- C3 强简单基线必须被公平比较；
- primary estimand 必须是 full coverage，fallback 患者不能从分母消失；
- selective prediction 必须在同一 retained subset 比较；
- worst-pattern regret 不能被平均值掩盖；
- 模态必须通过 permutation/random/volume-matched 负对照证明特异性；
- 排序与绝对概率必须分开报告；
- 必须有模型完全冻结后的、此前未查看结局的外部或时间外队列，才能支持强外部泛化 claim。

如果最后缺少 untouched cohort，建议将定位收缩为严谨的 post-lock exploratory methodological study，而不是强行使用“externally validated”或“clinically deployable”。

## 7. 下一步实验写作接口

完成每一阶段后，可直接更新以下位置：

- V1/V2：Table 3 和 Figure 3；
- calibration bridge：Figure 4；
- router 与 controls：Figure 5、Figure 6；
- ablation：补充表，并在主文 Results 增加简短小节；
- untouched confirmation：Figure 6e、Table 1 最后一行和 Abstract 的最终结果句。

建议结果表由冻结 aggregate CSV 自动生成 LaTeX，避免人工抄数。

## 8. 投稿前必须由作者补充

- 作者顺序、单位、通信作者；
- 伦理审查/豁免的准确措辞和编号；
- 数据版本、下载日期和 accession；
- 代码仓库、许可证、Zenodo/其他 DOI；
- funding、competing interests、CRediT；
- 精确的软件、硬件和运行时间；
- 最终生成式 AI 使用披露；
- 所有参考文献逐条核验，尤其是最新会议论文记录。
