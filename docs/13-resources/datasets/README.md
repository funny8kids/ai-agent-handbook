---
tags: [resource, evaluation]
type: index
status: published
updated: 2026-09-10
---

# 🔗 数据集

> Agent 训练与评估相关的公开数据集索引。

## 常用数据集速查

| 数据集 | 用途 | 链接 |
|---|---|---|
| SWE-bench 任务集 | 编程 Agent 评估（2294 真实 issue） | <https://www.swebench.com/> |
| WebArena 网站 + 任务 | 网页 Agent 评估环境 | <https://webarena.dev/> |
| GAIA 验证集 | 通用助理评估（Hugging Face 托管） | <https://huggingface.co/datasets/gaia-benchmark/GAIA> |
| ToolBench API 语料 | 工具调用训练/评估（1.6 万 API） | <https://github.com/OpenBMB/ToolBench> |
| AgentBench 环境 | 八场景综合评估 | <https://github.com/THUDM/AgentBench> |
| ALFWorld | 具身指令任务（Reflexion 等论文用） | <https://alfworld.github.io/> |
| WebShop | 网购任务环境（ReAct 论文用） | <https://webshop-pnlp.github.io/> |
| HotpotQA | 多跳问答（ReAct 论文用） | <https://hotpotqa.github.io/> |

## 使用提示

- 评估用数据集注意**去污染**：确认未混入模型训练数据
- 训练自己的 Agent 模型可参考 DeepSeek-R1 的蒸馏数据思路（[论文](https://arxiv.org/abs/2501.12948)）
- 构建领域内测集时借鉴这些数据集的任务定义与评分协议（→ [基准测试](../benchmarks/README.md)）
