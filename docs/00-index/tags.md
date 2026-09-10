---
tags: [basics]
type: index
status: published
updated: 2026-09-10
---

# 🧭 标签索引

> **一句话**：全书统一的标签全集。给页面打标签时从这里取，保证检索一致。

## 标签全集

| 标签 | 含义 | 代表页面 |
|---|---|---|
| `basics` | 基础概念 | [什么是 AI Agent](../02-agent-basics/what-is-agent.md) |
| `agent` | Agent 原理与设计 | [感知—规划—行动循环](../02-agent-basics/perception-planning-action.md) |
| `llm` | 大语言模型 | [LLM 是什么](../03-llm/what-is-llm.md) |
| `prompt` | 提示词与推理模式 | [ReAct](../04-prompt-reasoning/react.md) |
| `tooling` | 工具调用与执行 | [Function Calling](../05-tool-protocol/function-calling.md) |
| `mcp` | MCP 协议相关 | [MCP](../05-tool-protocol/mcp.md) |
| `multi-agent` | 多智能体协作 | [监督者模式](../08-multi-agent/supervisor-pattern.md) |
| `memory` | 记忆机制 | [记忆类型](../06-memory-rag/memory-types.md) |
| `rag` | 检索增强生成 | [RAG 基础](../06-memory-rag/rag-basics.md) |
| `planning` | 规划与任务分解 | [Plan-and-Execute](../07-planning/plan-and-execute.md) |
| `framework` | 框架与生态 | [LangGraph](../09-frameworks/langgraph.md) |
| `evaluation` | 评估与基准 | [SWE-bench](../13-resources/benchmarks/swe-bench.md) |
| `safety` | 安全与对齐 | [提示注入](../10-evaluation-safety/prompt-injection.md) |
| `engineering` | 工程化与可观测 | [缓存与成本优化](../11-engineering/caching-cost-optimization.md) |
| `infrastructure` | AI 基础设施（推理/沙箱/网关/运行时） | [推理服务化](../16-ai-infrastructure/inference-serving.md) |
| `embodied-ai` | 具身智能与机器人 | [VLA 模型架构](../17-embodied-ai/vla-models.md) |
| `data` | 数据采集与治理 | [数据引擎](../17-embodied-ai/data-engine.md) |
| `cost` | 成本与容量 | [推理经济学与部署形态](../16-ai-infrastructure/inference-economics-deployment.md) |
| `application` | 应用案例 | [编程 Agent](../12-applications/coding-agent.md) |
| `resource` | 资源收录 | [资源库说明](../13-resources/README.md) |
| `beginner` | 入门难度 | [AI、ML、DL 的关系](../01-ai-basics/ai-ml-dl.md) |
| `advanced` | 进阶难度 | [RLHF、DPO 与对齐](../03-llm/rlhf-dpo-alignment.md) |

## 使用规范

- 每页 2–5 个标签，写在 frontmatter 的 `tags` 字段
- 全小写英文、连字符分隔，不要自创同义标签（如不要同时用 `agent` 和 `agents`）
- 新标签先在本页登记再使用

## 📚 相关知识点

- [资源总表](resources-index.md)
- [知识点模板](../14-templates/knowledge-template.md)
