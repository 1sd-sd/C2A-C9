# 提交说明（Submission README）

**挑战：** C2A / C9 — 衡量 AGI 的认知能力（ch-20260717031352-tlg70p）
**作者：** 李圣丹（lishengdan）· Elite 20 Program · SIAS University
**赛道：** Kaggle Track 2 — Metacognition
**提交日期：** 2026-09-29 ｜ 截止日期：2026-12-31 23:59（北京时间）

> 注：本目录的文件名均遵循挑战命名规范 `姓名拼音_C阶段_内容描述.扩展名`。

---

## 1. 交付物对照

| 挑战要求 | 对应文件 | 状态 |
|---|---|---|
| C2A 提案正文（`*proposal*`） | `lishengdan_C2A_proposal.md` | ✅ 四部分齐备（动机/设计/人类基线/创新与可行性），中英双语标题 |
| C2A AI 日志（`*AI日志*`） | `lishengdan_C2A_AI日志.md` | ✅ 5 轮 Prompt→产出→核验记录，含 2 处 AI 事实错误被拦截 |
| C2A 拿来说明 | `lishengdan_C2A_拿来说明.md` | ✅ 9 项借鉴来源，"拿了什么/改了什么/为什么"逐项说明 |
| C9 Benchmark 代码（`*benchmark*`） | `lishengdan_C9_benchmark/` | ✅ 零依赖可运行，含 README、22 项单元自测（全通过）、mock 运行结果 |
| C9 任务说明 | `lishengdan_C9_task说明.md` | ✅ 任务描述 + 全部指标评分标准 + 防作弊协议 |
| C9 测试结果 | `lishengdan_C9_测试结果.md` | ✅ 4 mock 画像 ×150 题实测数据 + 区分度分析（含诚实声明） |
| C9 反思报告（`*AAR*`） | `lishengdan_C9_反思报告_AAR.md` | ✅ 676 字（合规 500–800），含失败经验与反向举证；文件名含 `AAR`，精确匹配交付物清单通配符 `*AAR*` |
| C9 AI 日志（`*AI日志*`） | `lishengdan_C9_AI日志.md` | ✅ 6 轮记录，含"AI 改代码迎合错误测试被人工拦截"案例 |
| C9 拿来说明 | `lishengdan_C9_拿来说明.md` | ✅ 实现期借鉴 + 提案→实现差异如实记录 |

## 2. Benchmark 一句话

**MetaKnow**：用"可证明不存在的实体"把"知道自己不知道什么"变成可自动评分的指标（AUROC），三子测试（置信度校准 / 认知边界 / 错误监控）对应 KSTAR ΔE 的三个环节。

## 3. 已知缺口（如实披露，2026-09-29 更新）

1. ~~未对真实前沿模型实测~~ → **已完成**：GLM-5.3-Flash / DeepSeek-V4-Flash / Kimi-K2.6 三个前沿模型 ×50 题实测（0 调用错误），核心发现：S2 边界感知 AUROC=1.0 但 S3 错误检出率=0.0（极端分离）。见 `lishengdan_C9_测试结果.md` §5 与 `lishengdan_C9_benchmark/results/real_models/`。
2. **Kaggle 平台状态**：官方比赛"Measuring Progress Toward AGI - Cognitive Abilities"已于 2026-04-16 截止提交（2026-06-01 已公布结果），**正式参赛窗口已关闭**。MetaKnow 已按 Kaggle Benchmarks 平台（kaggle-benchmarks SDK）标准打包（见 `lishengdan_C9_benchmark/kaggle_benchmark/`），可随时以社区基准（Community Benchmark）形式发布，发布需要 Kaggle 账号登录授权。
3. 真实模型样本量 50 题/模型、单 seed，置信区间较宽（详见测试结果 §5.5）。

## 4. 一句话说明（按挑战提交格式）

这是我的 C2A 提案与 C9 实现，选择了 Track 2（元认知能力），欢迎反馈。
