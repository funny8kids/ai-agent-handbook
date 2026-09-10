---
tags: [framework, resource]
type: resource
status: published
updated: 2026-09-10
---

# LangChain

> **一句话**：最流行的 LLM 应用开发框架：数百个集成 + 统一抽象，生态最大的「全家桶」。

| 属性 | 内容 |
|---|---|
| 类型 | 开源项目（框架） |
| 链接 | <https://github.com/langchain-ai/langchain> · [文档](https://python.langchain.com) |
| 来源 | LangChain Inc. |
| 协议 | MIT |
| 难度 | 入门 |
| 标签 | `#framework` |

## 推荐理由

- **集成生态最大**：模型、向量库、文档加载器、工具适配应有尽有，原型速度极快——需要「接一个从没见过的数据源」时，通常已有现成封装
- **统一抽象（Runnable/LCEL）**：组件可替换（换模型、换向量库不改链路），并自动支持流式与批处理
- **调试链路完整**：与 LangSmith（trace/评估）与 LangGraph（复杂编排）构成工具链

## 注意事项

- 抽象层数偏多，出问题时需要在多层之间定位；建议**把它限制在「集成适配」层**，业务控制流自己写或用 LangGraph
- 迭代快、存在破坏性变更，生产环境务必锁版本

## 上手建议

- 复杂编排分流给 [LangGraph](langgraph.md)；LangChain 用作「集成层」
- 对照 [LangChain 知识点](../../09-frameworks/langchain.md) 理解适用边界

## 参考资料

- [LangChain 文档](https://python.langchain.com)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)

## 相关知识点

- [LangChain](../../09-frameworks/langchain.md)
- [LangGraph](langgraph.md)
