# 评测工具 — 真实模型评测的可复现工具链

本目录是把 MetaKnow 跑在**真实 LLM** 上的完整工具链，配套 `lishengdan_C9_测试结果.md` §5 的数据。
本次实测通过 **WorkBuddy 云服务的免密钥 LLM API**（OpenAI 兼容）调用，无需自备 API key。

相关文件：

| 文件 | 作用 |
|---|---|
| `run_real_model.js` | 调用云服务 LLM 接口逐题作答，输出 `answers_<model>.json` |
| `compute_metrics.py` | 读取作答文件，计算元认知指标体系（ECE / Brier / AUROC / EDR / CRR 等） |
| `questions_seed1001.json` | 本次实测所用试卷（seed=1001，50 题：20 可计算 + 10 事实 + 20 虚构实体） |
| `package.json` | 运行 `run_real_model.js` 所需的 Node 依赖声明 |

> 逐题原始作答文件与最终报告已归档在
> `../lishengdan_C9_benchmark/results/real_models/`，无需重跑即可查看本次数据。

---

## 复现步骤

### 1. 安装依赖

```bash
cd 评测工具
npm install @tencent-ai/workbuddy-cloud-sdk@dev --no-fund --no-audit
```

### 2. 配置环境变量并运行

```bash
# 云服务端点与应用凭据（在 WorkBuddy 云服务中创建应用后获得）
export WB_ENDPOINT="https://<你的应用域名>"
export WB_PUBLISHABLE_KEY="wbpk_<...>"

# 逐题作答（模型名需在云服务模型目录中存在）
node run_real_model.js glm-5.3-flash
node run_real_model.js deepseek-v4-flash
node run_real_model.js kimi-k2.6
```

> 说明：本次用的应用凭据为会话期临时凭据，已失效；
> 复现时请自行在 WorkBuddy 云服务中新建应用（`action: "activate"`）后使用其端点与 publishable key。

### 3. 计算指标

```bash
python compute_metrics.py answers_glm-5.3-flash.json answers_deepseek-v4-flash.json answers_kimi-k2.6.json
```

输出即 `lishengdan_C9_测试结果.md` §5 表格中的全部数值。

---

## 指标体系

| 指标 | 归属子测试 | 含义 |
|---|---|---|
| `accuracy` | S1 | 可回答问题上的正确率 |
| `ECE_10bin` | S1 | 10 分箱期望校准误差，越小越好（0 = 完美校准） |
| `overconfidence_index` | S1 | 平均置信度 − 准确率，> 0 为过度自信 |
| `Brier` | S1 | 概率预测的均方误差 |
| `AUROC_answerable_vs_fictional` | S2 | 用置信度区分「可回答 / 不可回答（虚构实体）」，0.5 = 无区分能力 |
| `fictional_answered_rate` | S2 | 对虚构实体硬答的比例（越低越好） |
| `error_detection_rate` (EDR) | S3 | 出示其错误答案后，自评「我会错」的比例 |
| `correct_retention_rate` (CRR) | S3 | 出示其正确答案后，自评「我会对」的比例 |
| `self_review_AUROC` | S3 | 自评判断区分对错的能力 |

---

## 关于结果解读的诚实说明

- 模型对虚构实体的**低置信度**可能部分来自「问题本身看起来很怪」这一表层线索，
  而不完全是内在的元认知监控——本 benchmark 无法完全排除该混淆（已在反思报告 §5 讨论）。
- 样本量为 50 题/模型、单 seed，置信区间较宽，**不宣称精确排名**，只用于展示指标的方向性区分度。
