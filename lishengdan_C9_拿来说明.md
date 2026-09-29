# 拿来说明（Steering & Borrowing Statement）— C9 实现版

**挑战：** C9 — Benchmark 实现
**作者：** 李圣丹（lishengdan）
**对应提案：** `lishengdan_C2A_proposal.md`（设计期拿来说明见 `lishengdan_C2A_拿来说明.md`，此处记录**实现期**的借鉴与改动）

---

## 1. 代码与协议层面的借鉴

| 来源 | 拿了什么 | 落地在哪 | 改了什么 |
|------|---------|---------|---------|
| **LM Evaluation Harness / BIG-Bench** 的评测工程惯例 | "题目生成 → 模型适配层 → 指标层 → 报告层"四层解耦；逐题 JSON 日志全量落盘 | `generator.py / adapters.py / metrics.py / run_benchmark.py` 的模块划分 | 不依赖其框架本身（零第三方依赖，纯标准库），只借架构 |
| **OpenAI API 协议** | chat/completions 调用格式与 JSON 模式 | `adapters.py::OpenAICompatibleAdapter`（urllib 直连） | 用环境变量配置，兼容 OpenAI/DeepSeek/Qwen/Ollama/vLLM 任意端点，而非绑定单一厂商 |
| **Tian et al. (2023) Just Ask for Calibration** | verbalized confidence 主协议（让模型直接报告 0–100 置信度） | `run_benchmark.py` 作答 JSON schema 中的 `confidence` 字段 | 保留 logprob 作为退路的说明，但未实现（列为局限） |
| **SimpleQA（OpenAI, 2025）** | 虚构实体提问（fake-entity probing）思路 | `generator.py::gen_fictional` | 人工造物 → 程序生成器：音节随机合成专名 + 真实词片段黑名单过滤 + seed 复现审计；用途从"测幻觉率"改为"测边界感知 AUROC" |
| **GSM8K 类程序化数学题生成** | 随机操作数、答案可验证的生成模式 | `generator.py::gen_computation`（一元方程/多步算术/模运算三型） | 题目同时采集答案与置信度，从测执行功能转向测校准 |
| **scikit-learn / torchmetrics 的指标定义** | ECE（Naeini et al. 2015 等宽 10 桶）、Brier、AUROC（Mann-Whitney U 平均秩处理并列）的**标准定义** | `metrics.py`（自行实现，非 import） | 用解析解验证：test_metaknow.py 中 AUROC 完美/随机/反转、Brier 0/1、ECE 完美校准、risk-coverage 下限 1/18 全部对得上解析值 |
| **认知科学 error monitoring 范式**（Yeung & Summerfield, 2012） | "作答后立即自评"的任务结构 | `run_benchmark.py` S3 流程 | 增加正确保留率（CRR）联合报告——堵住"策略性全盘认错"刷分漏洞（实现期新增，提案未预见） |

## 2. 提案 → 实现的差异（如实记录）

| 提案设想 | 实现结果 | 原因 |
|---------|---------|------|
| 事实题约 100 题 | 30 题 | 时间盒内完成人工交叉核验的上限；后续可扩 |
| 判分含 LLM-judge 兜底 | 未实现，先用归一化子串匹配 | 判分器须保持零依赖、可被他人独立运行，不引入 API 依赖；列为已知局限（README §4）。该取舍与后续获得 API 通道无关，保持不变 |
| logprob 置信度退路 | 未实现 | 同上，verbalized 为主协议 |
| "2–3 个前沿模型实测" | **已完成**（3 个模型 × 50 题，0 调用错误） | 原环境无 API key；后改走 WorkBuddy 云服务免密钥 LLM API 落地（测试结果 §5）。模型数达标，样本量 50 题/模型低于预注册的 450 题，已在 §5.5 如实声明 |
| 难度梯度 difficulty 1–3 | 已实现（`--difficulty` 经 build_paper 参数） | — |

## 3. 未借鉴与原因（同 C2A，重申）

- 不 import MMLU/BIG-Bench 公开题库（污染）；
- 不引入任何校准**训练**方法（测量与手段分离）；
- 不使用 TruthfulQA 任务（构念不同）。

## 4. 致谢式总结

MetaKnow 的每一层都有出处：**架构**来自 LM Eval Harness 惯例，**协议**来自 Tian et al.，**虚构实体**来自 SimpleQA，**指标**来自 Naeini/Fleming-Lau 的标准定义，**任务结构**来自认知科学范式。本工作的增量是：三成分拆分的任务集、可审计的程序化不可答题生成、以及 EDR/CRR 联合报告的防刷分设计。
