# MetaKnow Benchmark

**MetaKnow** — 一个测量 LLM 元认知（metacognition）的基准：不仅看模型"答对了没有"，更看它**"是否知道自己会答错"**。

- **赛道：** Kaggle "Measuring Progress Toward AGI: Cognitive Abilities" · Track 2 Metacognition
- **课程：** Elite 20 Program · 挑战 C2A/C9（ch-20260717031352-tlg70p）
- **作者：** 李圣丹（lishengdan）
- **理论依据：** Burnell et al. (2026), *Measuring Progress Toward AGI: A Cognitive Framework*（元认知 = 对自身认知过程的监控与调控）；KSTAR 框架的 ΔE（预期−实际偏差）

---

## 1. 测什么：三个子测试

| 子测试 | 测量目标（元认知成分） | 核心指标 | 完美值 |
|--------|----------------------|---------|--------|
| **S1 置信度校准** | 对自己答案的确信度是否诚实（KSTAR ΔE 的"预期"环节） | ECE (10-bin)、Brier、过度自信指数 | ECE → 0 |
| **S2 认知边界感知** | 能否用置信度区分"可答"与"注定不可答"的问题 | **AUROC**、risk–coverage AUC | AUROC → 1.0 |
| **S3 错误监控** | 出示自己的答案后能否察觉错误（KSTAR ΔE 的"承认偏差"环节） | 错误检出率 EDR、正确保留率 CRR | EDR/CRR → 1.0 |

**防污染机制（核心设计）：**
- **可计算题**：随机操作数程序生成（如 `17*23+48-6`），答案必不在训练语料中；
- **虚构实体题**：生成器随机合成不存在的专名（人名/地名/法案），语法通顺但**可证明不可答**，并经真实词片段黑名单过滤；同一 seed 可复现整套试卷，换 seed 即全新试卷；
- **事实题**：30 道人工交叉核验的跨领域常识题。

## 2. 快速开始

```bash
# 零依赖（纯 Python 标准库，>=3.10），无需安装任何包
cd lishengdan_C9_benchmark

# 跑单元自测（22 项断言）
python test_metaknow.py

# 用内置 mock 模型验证完整流水线（无需 API key）
python run_benchmark.py --model mock-well-calibrated --seed 42

# 接入真实模型（任何 OpenAI 兼容端点：OpenAI / DeepSeek / Qwen / Ollama / vLLM ...）
export METAKNOW_API_BASE=https://api.deepseek.com/v1
export METAKNOW_API_KEY=sk-...
export METAKNOW_MODEL=deepseek-chat
python run_benchmark.py --model openai-compatible --seed 42
```

输出（`results/metaknow_<model>_seed<seed>.json` + `*_rc_curve.csv`）包含逐题日志与三子测试得分报告。

### 内置 mock 模型画像（流水线演示用，非真实模型成绩）

| 画像 | 模拟特征 |
|------|---------|
| `mock-well-calibrated` | 能力强且诚实 |
| `mock-overconfident` | 虚构题也高置信度（典型幻觉画像） |
| `mock-smart-but-miscalibrated` | 准确率高但边界感差 |
| `mock-humble-weak` | 能力弱但自我认知尚可 |

> **诚实声明：** mock 模型是按可调参数模拟作答的**流水线验证工具**，其结果只证明评测管线能产生区分度，**不代表任何真实模型的表现**。真实模型成绩需配置 API 后运行 `openai-compatible`。

## 3. 目录结构

```
lishengdan_C9_benchmark/
├── metaknow/
│   ├── __init__.py       # 版本信息
│   ├── generator.py      # 题目生成器（可计算/事实/虚构实体三类）
│   ├── metrics.py        # ECE / Brier / AUROC / risk-coverage / 错误监控
│   └── adapters.py       # MockModel + OpenAI 兼容适配器
├── run_benchmark.py      # CLI 入口（生成试卷→作答→评分→出报告）
├── test_metaknow.py      # 22 项单元自测
├── results/              # seed=42 的 4 个 mock 画像运行结果（JSON+CSV）
└── README.md
```

## 4. 评分协议细节

- **作答格式：** 模型每题须返回 JSON `{"answer": ..., "confidence": 0-100}`；置信度除以 100 进入指标。
- **判分：** 可计算题数值精确匹配；事实题归一化后包含匹配（子串容忍缩写）；虚构题作答即记错。
- **S3 流程：** 复用 S1 可答题，出示原题 + 模型自己的答案，要求自评；`错误检出率 = P(自评会错 | 实际错)`，`正确保留率 = P(自评会对 | 实际对)`（防止策略性全盘认错刷分）。
- **已知局限：** ① 事实题判分对开放表述不够鲁棒，正式比赛版将引入 LLM-judge；② verbalized confidence 可能与 logprob 置信度有差异（Tian et al., 2023 显示两者高度相关）；③ 中文虚构题模板对英文中心化模型或有不公平，计划双语对照。

## 5. 人类基线（预期，待实测校准）

| 指标 | 普通成人预期 |
|------|-------------|
| S1 可计算题 ECE | 0.03–0.10 |
| S2 AUROC | 0.85–0.95（成人几乎必然对虚构专名报低置信） |
| S3 错误检出率 | 0.6–0.8 |

## 6. 复现

```bash
python run_benchmark.py --model mock-well-calibrated --seed 42   # 报告应与 results/ 内同名文件一致
```

试卷、mock 作答、指标全部由 seed 决定，逐字节可复现。
