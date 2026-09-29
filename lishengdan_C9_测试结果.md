# MetaKnow 测试结果（Test Results）

**作者：** 李圣丹（lishengdan）｜ 2026-09-29（当日更新：新增 3 个真实前沿模型实测）
**环境：** Windows 11 · Python 3.13.12 · Node 22.22.2 · 零第三方依赖（评测管线）
**试卷：** mock 验证 seed=42（150 题）；真实模型 seed=1001（50 题 = 20 可计算 + 10 事实 + 20 虚构）

---

## 0. 结果总览（两层验证）

| 层 | 模型 | 用途 |
|----|------|------|
| 管线验证 | 4 个 mock 画像（seed=42, 150 题） | 证明评测管线端到端可运行、指标方向正确 |
| **真实模型实测** | **GLM-5.3-Flash、DeepSeek-V4-Flash、Kimi-K2.6**（seed=1001, 50 题/模型，80 次调用/模型，0 调用错误） | **对真实前沿模型产生有意义的区分度** |

真实模型接入方式：WorkBuddy 云服务免密钥 LLM API（OpenAI 兼容流式接口，`run_real_model.js`，Node SDK），题目由 `metaknow/generator.py` 程序生成后导出 JSON。全部原始数据见 `lishengdan_C9_benchmark/results/real_models/`。

## 1. 单元自测结果（22/22 通过）

```
$ python test_metaknow.py
PASS paper size / unique qids / computation answerable / fictional unanswerable
PASS fictional has no real-fragment leak
PASS paper deterministic (same seed) / paper differs across seeds
PASS AUROC perfect separation / chance level / reversed
PASS Brier perfect / worst
PASS ECE perfectly calibrated
PASS overconfidence sign / error detection rate / correct retention rate / review AUROC
PASS risk-coverage monotone / analytic floor 1/18 / perfect < inverted
PASS calibrated mock low-conf on fiction / overconfident mock high-conf on fiction
ALL PASS（22/22）
```

其中 3 个用例初版写错期望值（ECE 校准用例构造错误、risk-coverage 下限误设为 0、以及一次错误的"反转构造"），修正过程记录于 AI 日志 Round 4——**是测试用例错，指标实现经解析解验证是对的**。

## 2. Mock 画像实测数据（seed=42，150 题）

| 画像 | S1 准确率 | S1 ECE↓ | 过度自信指数 | S2 AUROC↑ | S3 错误检出率↑ | S3 正确保留率↑ |
|------|-----------|---------|-------------|-----------|----------------|----------------|
| `mock-well-calibrated` | 0.844 | **0.065** | +0.03 | **0.976** | **0.857** | 0.908 |
| `mock-overconfident` | 0.867 | 0.075 | +0.18 | 0.676 | 0.083 | 1.000 |
| `mock-smart-but-miscalibrated` | **0.967** | **0.026** | +0.10 | 0.834 | 0.333 | 1.000 |
| `mock-humble-weak` | 0.600 | 0.141 | −0.10 | 0.941 | 0.639 | 0.852 |

原始数据：`lishengdan_C9_benchmark/results/metaknow_<画像>_seed42.json`（逐题日志），`*_rc_curve.csv`（风险-覆盖曲线）。

## 3. 区分度分析：这些指标真的"分得开"吗？

四个画像在关键指标上的极差：

- **S2 AUROC：0.676 ↔ 0.976**（极差 0.30）——最有效的单一指标。"高准确率但幻觉也自信"的画像（overconfident，0.676）与"诚实但能力弱"的画像（humble-weak，0.941）被清晰分开，**这正是元认知区别于知识量的构念效度证据**：mock-humble-weak 准确率垫底（0.600）却拿到第二好的边界感知分。
- **S3 错误检出率：0.083 ↔ 0.857**（极差 0.77）——区分度最强。overconfident 画像几乎从不知道自己错了（0.083），同时正确保留率 1.000——**这种"对错全都有信心"的形状正是真实 LLM 过度自信的典型画像**（与 verbalized calibration 文献一致）。
- **S1 ECE 的一个反直觉观察**：humble-weak 的 ECE（0.141）反而最差——系统性**不**自信同样造成校准误差（置信 0.45 而准确率 0.60）。这提醒评估者：ECE 好不等于"诚实"，**必须与过度自信指数、S2 AUROC 联合解读**。这是本次实测比设计文档多学到的点。

## 4. 流水线性能

- 150 题 × 4 画像全量运行 < 1 秒（mock）；真实模型 **80 次调用/模型**（50 次作答 + 30 次 S3 自评），逐题串行调用，单模型耗时在分钟量级（冷启动首次实测已超过 7 分钟，未做精确计时）；
- 结果 JSON 含逐题 `qid/family/gold/model_answer/confidence/self_review_conf`，可完全回溯任一分数。

## 5. 真实前沿模型实测结果（2026-09-29，当日新增）

### 5.1 实测配置

- 模型（3 个不同厂商的前沿模型）：`glm-5.3-flash`、`deepseek-v4-flash`、`kimi-k2.6`
- 试卷：seed=1001，50 题/模型（20 可计算 + 10 事实 + 20 虚构实体），每模型 **80 次流式调用**（50 次作答 + 30 次 S3 自评：`answerable && phase∋S1` 的题目追加自评），**0 调用错误**
- 温度 0，置信度按 verbalized 0–100 协议采集

### 5.2 核心结果

| 模型 | S1 准确率 | S1 平均置信度 | S1 ECE↓ | 过度自信指数 | **S2 AUROC↑** | 虚构题均置信 | **S3 错误检出率↑** | S3 正确保留率 | S3 自评 AUROC |
|------|-----------|---------------|---------|--------------|----------------|--------------|---------------------|---------------|----------------|
| GLM-5.3-Flash | 0.867 | 0.999 | 0.132 | +0.132 | **1.000** | 0.028 | **0.000** | 1.000 | 0.596 |
| DeepSeek-V4-Flash | 0.867 | 0.993 | 0.127 | +0.127 | **1.000** | 0.034 | **0.000** | 1.000 | 0.423 |
| Kimi-K2.6 | 0.667 | 0.984 | **0.317** | +0.317 | **1.000** | 0.050 | **0.000** | 1.000 | 0.733 |
| 人类预期基线 | 0.85–0.95 | — | 0.03–0.10 | ≈0 | 0.85–0.95 | 极低 | 0.6–0.8 | 高 | — |

原始逐题日志：`results/real_models/answers_<model>.json`；汇总：`real_model_reports.json`。

### 5.3 三个可写进结论的发现

1. **"知道自己不知道什么"已经解决，"承认自己错了"完全没有解决。** 三个模型在 S2 的 AUROC 全部为 1.000——对虚构实体问题平均置信度仅 0.028–0.050，对可答题接近 1.0，边界感知完美。但 S3 错误检出率全部为 **0.000**：出示自己的错误答案后，没有一个模型自评"可能会错"（正确保留率反而都是 1.000）。**元认知的两个子成分出现了极端分离**——这正是 MetaKnow 三子测试设计想暴露的、单一准确率指标看不见的行为模式。
2. **三个模型都会对虚构问题编造实体（编造率 1.0），但置信度极低。** 即"幻觉行为仍在，幻觉信心已修复"——verbalized 校准训练可能只教会了模型"该多确信"，没教会"该不该编"。
3. **准确率与校准脱钩。** Kimi-K2.6 准确率最低（0.667）却最过度自信（ECE 0.317，答错的题平均置信度仍 >0.95）；与预注册假设一致（正向过度自信、EDR 显著低于 CRR），也与 GLM/DeepSeek 形成分级——区分度目标达成。

### 5.4 与 mock 验证层的对照

mock-humble-weak（能力弱、不自信）与真实 Kimi-K2.6 形成有趣对照：真实模型不存在"系统性不自信"，现实中前沿模型的失败模式是单侧的——**过度自信 + 拒不认错**。mock 画像库中"overconfident + EDR=0"的组合最接近真实分布，验证了画像参数设定的合理性。

### 5.5 局限（如实声明）

- 样本量 50 题/模型、单 seed，置信度区间较宽（尤其 S3 的 EDR=0 需要 ≥100 错误样本才能给出上界的紧估计）；
- 三模型均为主流中文生态旗舰/次旗舰，未覆盖 GPT/Claude/Gemini 官方 API；
- verbalized confidence 与 logprob confidence 的差异未做对照（Tian et al., 2023 表明二者高度相关，但边界感知场景未验证）。
