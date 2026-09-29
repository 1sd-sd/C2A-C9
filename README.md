# C2A / C9 提交成果 —— 衡量 AGI 的认知能力

**作者：** 李圣丹（lishengdan）· Elite 20 Program · SIAS University
**挑战：** C2A（提案）+ C9（实现）— Measuring Progress Toward AGI: Cognitive Abilities
**赛道：** Kaggle Track 2 — Metacognition（元认知）
**提交日期：** 2026-09-29 ｜ 挑战截止：2026-12-31 23:59（北京时间）
**远端仓库：** https://github.com/1sd-sd/C2A-C9

---

## 一句话

**MetaKnow** 用「可证明不存在的虚构实体」把「模型是否知道自己不知道什么」变成可自动评分的指标（AUROC），
三个子测试分别对应 KSTAR 循环中 ΔE 评估的三个环节：置信度校准、认知边界感知、错误监控。

---

## 目录导航

```
C2AC9提交成果/
├── README.md                       ← 本文件（总入口）
├── SUBMISSION.md                   ← 提交对照表：交付物 ↔ 挑战要求
│
├── lishengdan_C2A_proposal.md      ← C2A 提案正文（动机 / 设计 / 人类基线 / 创新与可行性）
├── lishengdan_C2A_AI日志.md         ← C2A 阶段 AI 使用记录（5 轮，含 2 处 AI 事实错误被拦截）
├── lishengdan_C2A_拿来说明.md       ← C2A 借鉴来源逐项说明（9 项）
│
├── lishengdan_C9_task说明.md        ← C9 任务描述 + 指标评分标准 + 防作弊协议
├── lishengdan_C9_测试结果.md        ← 4 个 mock 画像 + 3 个真实前沿模型实测数据
├── lishengdan_C9_反思报告.md        ← AAR 反思（含失败经验与反向举证）
├── lishengdan_C9_AI日志.md          ← C9 阶段 AI 使用记录（6 轮）
├── lishengdan_C9_拿来说明.md        ← C9 实现期借鉴说明
│
├── lishengdan_C9_benchmark/        ← ★ 可运行 Benchmark 代码（零第三方依赖）
│   ├── README.md                   ← 安装 / 运行 / 接入真实模型说明
│   ├── metaknow/                   ← 核心库：generator / metrics / adapters
│   ├── run_benchmark.py            ← 命令行入口
│   ├── test_metaknow.py            ← 22 项单元自测（全部通过）
│   ├── kaggle_benchmark/           ← Kaggle Benchmarks 平台打包版
│   └── results/                    ← 实测结果
│       ├── metaknow_*_seed42.json  ← 4 个 mock 画像报告 + risk-coverage 曲线
│       └── real_models/            ← 3 个真实前沿模型逐题原始数据与报告
│
├── 评测工具/                        ← 真实模型评测的可复现工具链
│   ├── README.md                   ← 复现步骤
│   ├── run_real_model.js           ← 调用 WorkBuddy 云服务免密钥 LLM API
│   ├── compute_metrics.py          ← 结果 → 指标
│   ├── questions_seed1001.json     ← 本次实测所用试卷（50 题）
│   ├── package.json / package-lock.json  ← Node 依赖声明与版本锁定（npm ci 可还原）
│   └── node_modules/               ← 随包附带的依赖（5 MB，开箱可离线运行；不入 git）
│
└── 参考资料/                        ← 挑战原始材料与依据文献
    ├── 挑战说明.md / challenge.json / rubric.json
    ├── C2A-guide（赛道指南）.pdf
    ├── deepmind-AGI认知框架（全文）.pdf / （摘要）.pdf
    └── c2a-starter.zip
```

> 本目录是**自包含交付包**：全部文档、代码、实测原始数据、依据文献与可复现工具链均在内，不依赖任何外部目录。

---

## 核心结果速览

**三个真实前沿模型实测**（seed=1001，各 50 题，80 次调用/模型，0 调用错误）：

| 模型 | S1 准确率 | S1 ECE（校准） | S2 边界感知 AUROC | S3 错误检出率 | S3 正确答案保留率 |
|---|---|---|---|---|---|
| GLM-5.3-Flash | 0.867 | 0.132 | **1.000** | **0.000** | 1.000 |
| DeepSeek-V4-Flash | 0.867 | 0.127 | **1.000** | **0.000** | 1.000 |
| Kimi-K2.6 | 0.667 | 0.317 | **1.000** | **0.000** | 1.000 |

**关键发现：元认知的两个子成分出现极端分离。**

- 「知道自己不知道什么」——**已经完美**：对虚构实体问题，三个模型的置信度仅 0.03–0.05，AUROC = 1.0；
- 「承认自己错了」——**完全失败**：把自己刚答错的答案出示给模型自评，三个模型**无一例外**判定「我是对的」，错误检出率 0.0。

单一准确率指标完全看不到这一模式：准确率相近的两个模型（0.867 vs 0.867），
在置信度校准上 ECE 差 0.005 看似无差，但对不可回答问题的自我认知策略可能完全不同。
这正是 MetaKnow 存在的意义——**把「准确率看不见的元认知」变成可比较的数字**。

---

## 快速验证

```bash
# 1. 跑单元自测（无需任何依赖与网络）
cd lishengdan_C9_benchmark
python test_metaknow.py          # 期望：22 项全部 PASS

# 2. 跑内置 mock 画像，验证评测管线端到端
python run_benchmark.py --model mock-overconfident --seed 42 --out results

# 3. 接入真实模型（OpenAI 兼容接口）
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.openai.com/v1
python run_benchmark.py --model openai:gpt-4o --seed 42 --out results
```

真实模型完整评测链路的复现步骤见 `评测工具/README.md`。

---

## 已知边界（如实披露）

1. **Kaggle 官方比赛窗口已关闭**：官方赛"Measuring Progress Toward AGI - Cognitive Abilities"
   已于 **2026-04-16 截止**（2026-06-01 公布结果），正式参赛提交不再可能。
   MetaKnow 已按 `kaggle-benchmarks` SDK 标准打包（`lishengdan_C9_benchmark/kaggle_benchmark/`），
   可在 Kaggle Benchmarks 平台以**社区基准（Community Benchmark）**形式发布，发布需 Kaggle 账号登录授权。
2. **真实模型样本量有限**：50 题/模型、单 seed，置信区间较宽（见 `lishengdan_C9_测试结果.md` §5.5）。
3. 所有原始数据均随包提供，任何结论都可逐题回溯核对。
