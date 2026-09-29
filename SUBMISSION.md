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
| C9 反思报告（`*AAR*`） | `lishengdan_C9_反思报告.md` | ✅ 约 800 字，含失败经验与反向举证 |
| C9 AI 日志（`*AI日志*`） | `lishengdan_C9_AI日志.md` | ✅ 6 轮记录，含"AI 改代码迎合错误测试被人工拦截"案例 |
| C9 拿来说明 | `lishengdan_C9_拿来说明.md` | ✅ 实现期借鉴 + 提案→实现差异如实记录 |

## 2. Benchmark 一句话

**MetaKnow**：用"可证明不存在的实体"把"知道自己不知道什么"变成可自动评分的指标（AUROC），三子测试（置信度校准 / 认知边界 / 错误监控）对应 KSTAR ΔE 的三个环节。

## 3. 已知缺口（如实披露）

1. **未对真实前沿模型实测**：本环境无 API key。管线用 4 个 mock 画像验证端到端可运行且指标区分度符合预期方向；接入真实模型仅需配置 3 个环境变量（见 `lishengdan_C9_benchmark/README.md`）。
2. **未完成 Kaggle 平台正式提交**：需要账号登录的网页操作。全部材料已按 Community Benchmarks 格式备齐。

## 4. 一句话说明（按挑战提交格式）

这是我的 C2A 提案与 C9 实现，选择了 Track 2（元认知能力），欢迎反馈。
