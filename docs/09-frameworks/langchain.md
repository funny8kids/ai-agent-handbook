---
tags: [framework, basics]
type: knowledge
status: published
updated: 2026-09-10
---

# 🧰 LangChain

> **一句话**：LangChain 是最流行的 LLM 应用开发框架：统一模型/向量库/工具的抽象，配以链条式编排——生态最大，抽象也最多，要「用薄不要用厚」。
> **难度**：⭐️ 入门
> **标签**：`#framework`

## 📌 先看结论

- 核心价值：数百个集成（模型/向量库/加载器）+ 统一抽象（Runnable/LCEL）+ 大量教程
- 定位演变：复杂 Agent 编排已分流给 LangGraph（同门）；LangChain 主攻「应用层组件与集成」
- 争议点：过度抽象层级曾广受批评——v0.3 起 LCEL 与精简 API 改善明显
- 学它最好的方式：把它当「集成速查库」，核心逻辑自己写

## 🧩 核心概念速查

| 概念 | 是什么 | 类比 |
|---|---|---|
| Runnable / LCEL | 组件统一接口 + 管道语法 `chain = prompt \| llm \| parser` | 乐高积木的统一凸点 |
| ChatModel | 各家 LLM 的统一封装 | 万能插座 |
| Tool | 函数 + schema 的注册封装 | 插头标准 |
| Retrievers | 检索器抽象 | 资料的取件口 |

## 💻 最小示例

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template("用一句话解释{topic}")
chain = prompt | ChatOpenAI(model="gpt-4o-mini")
print(chain.invoke({"topic": "MCP 协议"}).content)
```

## 📦 源码案例

- **对照学习**：LangChain 的 `create_react_agent`（约几百行源码）是 [ReAct 循环](../02-agent-basics/perception-planning-action.md) 的框架化实现——读完 Pi 的 agentLoop 再读它，能清楚看到框架在哪几处做了抽象（消息状态管理、工具执行器、回调系统）
- **LangSmith 联动**（→ [LangSmith、LangFuse、Phoenix、OpenTelemetry](../11-engineering/observability-tools.md)）：调试链路的一等公民，trace 粒度到每个 Runnable
- **何时别用**：只需要「模型调用 + 工具循环」的简单 Agent，直接用各家 SDK（或 Pi）更轻

## ⚠️ 常见误区

- ❌ 学 Agent = 学 LangChain：框架是原理的封装，先懂 [02 Agent 基础](../02-agent-basics/README.md) 再用框架
- ❌ 所有逻辑都塞进 chain：复杂控制流交给 LangGraph 或普通 Python，chain 只管线性段
- ❌ 忽略版本变迁：v0.1→v0.3 破坏性变更多次，抄旧教程代码前先看版本

## 🧪 小练习

用 LangChain 搭一个「文档问答」chain：加载 → 切分 → 检索 → 生成。然后回答：哪一段你更想用裸代码写？为什么？

## 🔗 相关资源

- [LangChain 文档](https://python.langchain.com)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)

## 📚 相关知识点

- [LangGraph](langgraph.md)
- [ReAct](../04-prompt-reasoning/react.md)
