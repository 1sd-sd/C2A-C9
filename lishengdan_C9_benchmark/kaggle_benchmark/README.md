# MetaKnow · Kaggle Community Benchmark 打包

本目录将 MetaKnow 元认知基准按 **Kaggle Benchmarks 平台**标准打包（SDK：`pip install kaggle-benchmarks`，Apache-2.0）。

## 与官方比赛的关系（重要）

- 官方比赛 ["Measuring Progress Toward AGI - Cognitive Abilities"](https://www.kaggle.com/competitions/kaggle-measuring-agi) 的提交窗口为 **2026-03-17 → 2026-04-16**，已于本提交撰写时（2026-09-29）**关闭**，结果已于 2026-06-01 公布。正式参赛已不可能。
- 因此本打包的定位是：以 **Community Benchmark（社区基准）** 形式在 Kaggle Benchmarks 平台公开发布 MetaKnow，使其成为社区可复用的认知评估工具——这也是官方比赛采用的同一平台与 SDK。

## 文件

| 文件 | 说明 |
|------|------|
| `metaknow_kaggle.py` | kaggle-benchmarks SDK 任务定义（3 类任务 + 全卷聚合任务） |
| `questions_seed1001.json` | seed=1001 的 50 题试卷（与真实模型实测同一张卷，可复现） |

## 发布步骤（需要 Kaggle 账号）

```bash
pip install kaggle-benchmarks
# 登录（二选一）：
#   a) kaggle.json API token 放到 ~/.kaggle/kaggle.json
#   b) 首次运行时的浏览器 OAuth 流程

# 1. 本地导出试卷（可复现）
python metaknow_kaggle.py

# 2. 本地对任意模型试跑
kbench run metaknow_kaggle.py --llm <model-id>

# 3. 发布为社区基准
#    kaggle.com -> Benchmarks -> New Benchmark
#    附件：metaknow_kaggle.py + ../metaknow/（generator.py, metrics.py, adapters.py）
#    Track: Metacognition
#    描述：直接复用 ../README.md 与 ../lishengdan_C9_task说明.md 的内容
```

## 已有实测成绩（见 `../results/real_models/`）

发布时建议在基准描述中附上三个前沿模型的实测：S2 边界感知 AUROC = 1.000（三模型一致）、S3 错误检出率 = 0.000（三模型一致）、S1 ECE 0.127–0.317（严重过度自信）。
