---
tags: [llm, basics]
type: index
status: published
updated: 2026-09-10
---

# 🧠 03 LLM 基础

> **一句话**：LLM 是 Agent 的大脑。本章讲清它是什么、怎么被训练出来、怎么被压缩部署——以及这些特性如何约束 Agent 的设计。

## 📌 你将学到

- LLM 的本质：下一个 token 预测器
- Transformer 与 Attention 的直觉理解（不推公式）
- Token、Embedding、上下文窗口——Agent 工程的三个硬约束
- 预训练 → 指令微调 → 偏好对齐的三段式训练管线
- 推理模型的兴起（DeepSeek-R1 一脉）与量化部署

## 为什么 Agent 工程师必须懂 LLM

- **上下文窗口**决定记忆管理策略（→ [上下文工程](../06-memory-rag/context-engineering.md)）
- **概率性输出**决定必须做校验与重试（→ [错误恢复与重试](../07-planning/error-recovery-retry.md)）
- **工具调用能力**（Function Calling）是模型训练出来的，不同模型差异巨大（→ [Function Calling](../05-tool-protocol/function-calling.md)）

## 本站页面

- [LLM 是什么](what-is-llm.md)
- [Transformer 与 Attention](transformer-attention.md)
- [Token、Embedding、上下文窗口](token-embedding-context.md)
- [预训练、微调与指令微调](pretraining-finetuning.md)
- [RLHF、DPO 与对齐](rlhf-dpo-alignment.md)
- [多模态模型](multimodal.md)
- [推理、量化、蒸馏与部署](inference-quantization-deployment.md)
