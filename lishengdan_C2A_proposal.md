# C2A Proposal: MetaKnow — 测量"知道自己不知道什么"的元认知基准

# MetaKnow: A Metacognition Benchmark for Measuring "Knowing What You Don't Know" in LLMs

**赛道 / Track:** Track 2 — Metacognition（元认知）
**作者 / Author:** 李圣丹（lishengdan）
**日期 / Date:** 2026-09-29
**挑战 ID:** ch-20260717031352-tlg70p

---

## 1. 赛道选择与动机 / Track Selection & Motivation

### 为什么选择 Metacognition 赛道？/ Why Track 2?

当前 LLM 评估有一个危险的盲区：**我们几乎只测量模型"答对了没有"，从不测量模型"是否知道自己会答错"。** 一个在 MMLU 上拿到 85 分的模型，如果它对答错的 15% 同样报出 95% 的确信度，那它在真实场景（医疗、法律、金融咨询）中比一个只有 75 分但知道自己边界在哪里的模型更危险。

DeepMind 的认知框架（Burnell et al., 2026）将元认知定义为"系统对自身认知过程的知识，以及监控和调控这些过程的能力"，并将其列为评估缺口最大的能力之一。我选择这条赛道的根本动机是：**元认知是所有其他认知能力的"安全阀"**——学习依赖"知道自己没学会"（判断学习，judgments of learning），推理依赖"察觉自己推错了"（错误监控，error monitoring）。元认知缺失的系统，其他能力越强，造成的损害越难被发现。

现有评估的三个具体缺口：

1. **准确率 ≠ 校准度。** 主流榜单只报告准确率，置信度校准（confidence calibration）几乎不被报告，即使报告也只是在既有题库（如 MMLU）上顺带计算——而题库本身已被训练数据污染。
2. **"知道边界"无法用常规题测量。** 测量"知道自己不知道"，必须包含模型**注定答不出**的问题，但常规静态题库无法保证这一点——任何公开题库中的问题都可能（部分）被记忆。
3. **缺乏与认知科学的对接。** 现有 LLM 校准研究很少区分元认知的不同子成分，而认知科学早已将其拆分为元认知知识、元认知监控（含置信度校准、错误监控）、元认知控制（Dunlosky & Metcalfe, 2009）。

### KSTAR 连接 / KSTAR Connection

KSTAR 框架中有一个显式的**偏差修正环节 ΔE**：系统比较预期结果 R′ 与实际结果 R，若 ΔE = R′ − R 持续偏大，说明系统的自我预期失真——这正是元认知缺陷的形式化。KSTAR 循环要健康运转，系统必须：① 对每次行动给出预期（对应**置信度**）；② 在 R 回来后承认偏差（对应**错误监控**）；③ 据此下调或上调自我评估（对应**再校准**）。MetaKnow 的三个子测试恰好逐一测量这三个环节——可以说，MetaKnow 是在静态地测量 KSTAR 循环中"预期是否诚实"这一环。

---

## 2. Benchmark 设计思路 / Benchmark Design

### 2.1 核心设计：三子测试 + 程序化生成"不可答问题"

MetaKnow 由三个子测试构成，全部题目由程序生成或经可复核清单固化，评分全自动：

**S1 置信度校准（Confidence Calibration）——"预期是否诚实"**

- **可计算题（60%）：** 程序化生成的多步算术/逻辑题（如"17 × 23 − 48 ÷ 6 = ?"），答案可验证且必然不在训练数据中（数字随机），测的是"对刚刚算出的结果有多确信"。
- **事实题（40%）：** 固定清单中经交叉核验的跨领域事实题（约 100 题）。
- 模型必须同时输出答案和置信度 c ∈ [0,1]。指标：**ECE**（10 桶期望校准误差）、**Brier 分数**、**过度自信指数**（平均置信度 − 准确率）。

**S2 认知边界探测（Boundary Awareness）——"知道自己不知道什么"**

这是 MetaKnow 的核心创新：**程序化生成"注定不可答"的问题**。生成器组合虚构的专有名词（人物、地名、事件）构造语法完全通顺、但关于一个**不存在实体**的事实性问题，例如：

> "Zorvania 联邦 1998 年通过的《凯尔文-索恩法案》第二修正案的主要起草人是谁？"

"Zorvania""凯尔文-索恩法案"均由生成器随机合成并登记在案，**可证明不存在于任何训练语料**。将 S1 的可计算题（可答）与 S2 的虚构题（不可答）混合呈现，要求模型对每题报告置信度：

- **核心指标：AUROC**——用置信度区分"可答/不可答"的能力。完美元认知 = AUROC 1.0；无元认知 = 0.5。
- **辅助指标：选择性风险曲线**（risk–coverage）与**弃答率**。

**S3 错误监控（Error Monitoring）——"能否察觉自己错了"**

模型先作答，随后被出示自己的答案并被问"这个答案大概率对吗？（是/否 + 置信度）"。指标：**错误检出率**（答错的题中自评"可能错"的比例）与**正确保留率**（答对的题中不自认错的比例，防止策略性全盘自我否定）。

### 2.2 为什么测的是元认知而不是别的？/ Construct Isolation

- S1 的可计算题部分排除了知识记忆的混淆——数值随机生成，模型只能现场计算，测的是对自身**计算过程**的监控；
- S2 的 AUROC 只对"自我边界感知"敏感：一个知识渊博但边界感差的模型在此项得低分，而一个知识一般但校准好的模型得高分——这正是元认知区别于知识量的构念效度；
- S3 是认知科学中的经典范式（error monitoring，Yeung & Summerfield, 2012）的直接 LLM 化。
- 三个子测试的题干格式统一、仅任务不同，可作差分分析（differential item functioning）交叉验证构念纯度。

### 2.3 人类基线考量 / Human Baseline Considerations

| 人群 | S1 可计算题 | S1 事实题 | S2 AUROC | S3 错误检出率 |
|------|------------|-----------|----------|--------------|
| 普通成人 | 准确率 85–95%，ECE 0.03–0.08 | 视领域 30–80% | 0.85–0.95 | 60–80% |
| 受训者（学生） | 准确率 >95%，ECE <0.05 | 更高 | 0.9+ | 70–85% |

人类的预期模式是**清晰的非对称**：对刚完成的计算相当确信（且大体诚实），对虚构实体几乎必然报低置信度（成年人不会假装知道"Zorvania"）。这给 AI 划出了两条基线：S1 的校准误差应低至人类量级（ECE < 0.10），S2 的 AUROC 应显著高于 0.75（区分度下限）。区分度设计上，难度系数可调（计算题步数 2–5 步），确保最强模型不会饱和、弱模型不会全随机。

---

## 3. 预期创新点与可行性 / Innovation & Feasibility

### 3.1 相比现有 benchmark 的创新 / What's New

| 现有方案 | 局限 | MetaKnow 的取舍 |
|---------|------|----------------|
| MMLU + 校准分析 | 题库公开、已被污染；不区分元认知子成分 | 可计算题程序生成，零污染 |
| SimpleQA / LongFact（OpenAI, 2025） | 测事实性幻觉，但虚构实体靠人工构造、规模小 | 生成器无限产题、防作弊可审计 |
| Calibration 研究惯例（ verbalized confidence） | 只做 S1 类校准，不测"知边界"与"错误监控" | 三子测试覆盖论文中元认知的监控三成分 |
| ARC / BIG-Bench | 准确率导向，无自我评估环节 | 全部题目强制报告置信度 |
| KSTAR | 框架层面对应 ΔE，无可执行测量 | S1/S2/S3 直接映射 ΔE 的三个环节 |

**最核心的一句话创新：用"可证明不存在的实体"把'知道自己不知道'变成一个可自动评分的指标（AUROC）。**

### 3.2 可行性 / Feasibility

| 资源 | 方案 | 时间 |
|------|------|------|
| 题目生成器 | Python，模板 + 随机组合，约 300 行 | 1 天 |
| 评分函数 | ECE/Brier/AUROC/风险覆盖曲线，纯标准库 + numpy | 0.5 天 |
| 模型接入 | OpenAI 兼容 API 适配器 + 内置 mock 模型（供无 key 演示） | 1 天 |
| 测试运行 | 2–3 个前沿模型 × 500 题，纯推理调用 | 1–2 天 |
| 文档与 Kaggle 提交 | Community Benchmarks 格式 | 1.5 天 |
| **合计** | | **6–7 天** |

全部文本任务，无 GPU 需求；生成器保证题目可无限重生成（换 seed 即全新试卷），从机制上杜绝"刷题"。风险预案：若前沿模型不配合输出置信度，退路是使用答案 token 的 logprob 作为置信度（已在设计中预留）。

---

## 参考文献 / References

1. Burnell, R. et al. (2026). Measuring Progress Toward AGI: A Cognitive Framework. *Google DeepMind*.
2. Chollet, F. (2019). On the Measure of Intelligence. *arXiv:1911.01547*.
3. Dunlosky, J. & Metcalfe, J. (2009). *Metacognition*. SAGE.
4. Fleming, S.M. & Lau, H.C. (2014). How to measure metacognition. *Frontiers in Human Neuroscience*, 8:443.
5. Hendrycks, D. et al. (2021). Measuring Massive Multitask Language Understanding (MMLU). *ICLR*.
6. Yeung, N. & Summerfield, C. (2012). Metacognition in human decision-making. *Trends in Cognitive Sciences*, 16(3).
7. Jacovi, A. et al. (2023). Stop Uploading Test Data in Plain Text. *EMNLP*.
8. Morris, R.G. et al. (2024). Levels of AGI for Operationalizing Progress on the Path to AGI. *ICML*.
