---
tags: [framework, resource]
type: resource
status: published
updated: 2026-09-10
---

# LangGraph

> **一句话**：把 Agent 表达为状态图的主流编排框架：checkpoint、interrupt、条件边，复杂工作流与多 Agent 的当前首选。

| 属性 | 内容 |
|---|---|
| 类型 | 开源项目（框架） |
| 链接 | <https://github.com/langchain-ai/langgraph> · [文档](https://langchain-ai.github.io/langgraph/) |
| 来源 | LangChain Inc. |
| 协议 | MIT |
| 难度 | 进阶 |
| 标签 | `#framework` `#engineering` |

## 推荐理由

- 官方模板库覆盖监督者/群聊/Plan-and-Execute 等全部主流编排模式——「编排模式的开源图书馆」
- checkpoint 机制提供断点恢复与时间旅行
- 生产案例丰富（Klarna、Uber 等公开分享）

## 上手建议

1. 跑通官方 `plan-and-execute` 模板
2. 对照 [工作流编排](../../07-planning/workflow-orchestration.md) 与 [多 Agent 编排](../../08-multi-agent/multi-agent-orchestration.md) 逐个读模板
3. 生产上线前补齐队列/幂等（框架不提供）

## 相关知识点

- [LangGraph](../../09-frameworks/langgraph.md)
- [状态机与事件驱动](../../11-engineering/state-machine-event-driven.md)
