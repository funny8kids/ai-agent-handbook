---
tags: [framework, basics]
type: knowledge
status: published
updated: 2026-09-10
---

# LangChain

> **一句话**：LangChain 是最流行的 LLM 应用开发框架：统一模型/向量库/工具的抽象，配以链条式编排——生态最大，抽象也最多，要「用薄不要用厚」。

## 先看结论

- 核心价值：大量集成（模型/向量库/加载器）+ 统一抽象（Runnable/LCEL）+ 丰富的教程与社区
- 定位演变：复杂 Agent 编排已分流给同门的 LangGraph；LangChain 主攻「应用层组件与集成」
- 争议点：抽象层级偏多曾广受批评，近几个版本在持续精简
- 学它最好的方式：把它当「集成速查库」，核心逻辑自己写

## 核心抽象

LangChain 的设计目标是**把异构组件统一成可拼接的接口**，核心是 Runnable 协议与 LCEL 管道语法：

$$
\text{chain}=\text{prompt}\;\big|\;\text{llm}\;\big|\;\text{parser}
$$

`|` 之所以能成立，是因为所有组件都实现了同一套方法（`invoke`/`stream`/`batch`）。这套协议带来三个直接收益：

- **组合性**：任意组件可替换（换模型、换向量库不改链路）
- **可流式**：整条链自动支持流式输出
- **可观测**：每次调用可挂回调，trace 粒度到每个组件（配 LangSmith）

代价是抽象层数多：出问题时需要在「你的代码 → chain → runnable → 具体实现」多层之间定位。

| 概念 | 是什么 | 类比 |
|---|---|---|
| Runnable / LCEL | 组件统一接口 + 管道语法 | 乐高积木的统一凸点 |
| ChatModel | 各家 LLM 的统一封装 | 万能插座 |
| Tool | 函数 + schema 的注册封装 | 插头标准 |
| Retriever | 检索器抽象 | 资料的取件口 |

## 最小示例

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template("用一句话解释{topic}")
chain = prompt | ChatOpenAI(model="gpt-4o-mini")
print(chain.invoke({"topic": "MCP 协议"}).content)
```

## 选型对比

| 维度 | LangChain | LangGraph | 裸 SDK / Pi |
|---|---|---|---|
| 定位 | 组件与集成层 | 复杂编排（状态图） | 最小循环 |
| 学习成本 | 中（抽象多） | 中高（图思维） | 低 |
| 控制流 | 线性链为主 | 图/条件/循环 | 自己写 |
| 集成丰富度 | 最高 | 复用 LangChain | 最少 |
| 适合 | 快速搭建含检索/工具的应用 | 多步骤可审计工作流 | 想彻底理解原理 |

**选型建议**：需要大量现成集成（几十种向量库、加载器）→ LangChain；需要条件分支与断点恢复 → LangGraph；只想跑通一个工具循环 → 裸 SDK 更透明。

## 源码案例

- **对照学习**：LangChain 的 ReAct 式 agent 实现（几百行源码）是 [ReAct 循环](../04-prompt-reasoning/react.md) 的框架化版本——读完最小循环实现再读它，能清楚看到框架在哪几处做了抽象（消息状态管理、工具执行器、回调系统）
- **LangSmith 联动**（→ [可观测性工具](../11-engineering/observability-tools.md)）：调试链路的一等公民，trace 粒度到每个 Runnable
- **何时别用**：只需要「模型调用 + 工具循环」的简单 Agent，直接用各家 SDK 更轻

## 工程含义

- **用薄不用厚**：把 LangChain 限制在「集成适配」层，业务控制流用普通代码或 LangGraph，能显著降低调试难度。
- **固定版本**：该项目迭代快，版本间存在破坏性变更；`requirements` 里锁版本，抄教程前先核对版本。
- **可观测性前置**：接 LangSmith（或 OpenTelemetry 导出）后再写业务，否则多抽象层的 bug 很难定位。

## 常见误区

- ❌ 学 Agent = 学 LangChain：框架是原理的封装，先懂 [Agent 基础](../02-agent-basics/README.md) 再用框架
- ❌ 所有逻辑都塞进 chain：复杂控制流交给 LangGraph 或普通 Python，chain 只管线性段
- ❌ 忽略版本变迁：破坏性变更多次，抄旧教程代码前先看版本
- ❌ 为了「用框架」而用框架：小项目里框架的抽象成本常高于收益

## 小练习

用 LangChain 搭一个「文档问答」chain：加载 → 切分 → 检索 → 生成。然后回答：哪一段你更想用裸代码写？为什么？

## 参考资料

- [LangChain 官方文档](https://python.langchain.com)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)

## 相关知识点

- [LangGraph](langgraph.md)
- [ReAct](../04-prompt-reasoning/react.md)
- [可观测性工具](../11-engineering/observability-tools.md)
