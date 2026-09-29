# MetaKnow 测试结果（Test Results）

**作者：** 李圣丹（lishengdan）｜ 2026-09-29
**环境：** Windows 11 · Python 3.13.12 · 零第三方依赖
**试卷：** seed=42，共 150 题（60 可计算 + 30 事实 + 60 虚构实体）

---

## 0. 诚实声明（先读这一段）

**本次提交的四个"模型"均为内置 mock 画像**（`metaknow/adapters.py::mock_profiles`），即按预设参数模拟作答的**流水线验证工具**。它们证明的是：**评测管线端到端可运行、指标能产生预期方向的区分度**。它们**不是**任何真实 LLM 的成绩。

未跑真实模型的原因：评测机无 API key 且无法注册 Kaggle 账号完成正式提交。真实模型的接入只需三条环境变量（见 README），协议、判分、指标代码全部就绪——这也是"可复现、可独立使用"部分的验收方式：**任何人拿到代码，填入 key 即可复现同规格实验**。

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

- 150 题 × 4 画像全量运行 < 1 秒（mock）；真实模型约 150×2 次调用/模型（答案 + 自评），估算 < 20 分钟/模型；
- 结果 JSON 含逐题 `qid/family/gold/model_answer/confidence/self_review_conf`，可完全回溯任一分数。

## 5. 真实模型测试的计划（未完成部分的补偿设计）

1. **优先级**：DeepSeek-chat（成本最低）→ GPT-4o-mini → GPT-4o / Claude（前沿对照）；
2. **样本量**：每模型 seed=42/43/44 三张试卷（450 题），报告 mean±std；
3. **预期（预注册式假设，防 HARKing）**：真实前沿模型 S2 AUROC 落在 0.6–0.8（对虚构实体存在部分过度自信）、S1 过度自信指数为正、S3 EDR 显著低于 CRR（"对错误更宽容"）。若与预期不符，本身就是值得报告的发现。
