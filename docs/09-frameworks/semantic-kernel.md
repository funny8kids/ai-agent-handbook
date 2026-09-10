---
tags: [framework]
type: knowledge
status: published
updated: 2026-09-10
---

# 🧰 Semantic Kernel

> **一句话**：微软的企业级 LLM SDK（C#/Python/Java 三栖）：以「插件 + 规划器」为核心，深度集成 Azure 生态——微软技术栈企业的默认选择。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#framework`

## 📌 先看结论

- 定位：面向企业 .NET 生态的 LLM 编排 SDK，强调依赖注入、可观测、 Responsible AI
- 核心抽象：Kernel（内核）+ Plugin（原生函数/提示函数）+ Planner（规划器）+ Memory
- 与 AutoGen 的关系：2025 年起两者合并演进的成果即 **Microsoft Agent Framework**——新项目优先看后者；SK 自身在维护态持续服务存量企业
- 特色：Process Framework（类型化事件驱动工作流）与对 Azure OpenAI / Azure AI Search 的一线集成

## 🧩 核心概念

| 概念 | 作用 | 类比 |
|---|---|---|
| Kernel | 配置、服务、插件的容器 | Spring 容器 |
| Plugin / Function | 原生代码或提示词封装的能力 | 带注解的接口方法 |
| Planner | 按目标选函数生成执行计划 | 调度员 |
| Agent Framework | SK+AutoGen 合流后的多 Agent 框架 | 合并后的新版本 |

## 💻 C# 最小示例

```csharp
var builder = Kernel.CreateBuilder();
builder.AddAzureOpenAIChatCompletion(deployment, endpoint, key);
var kernel = builder.Build();
kernel.ImportPluginFromFunctions("weather",
    [KernelFunctionFactory.CreateFromMethod(GetWeather, "查询天气")]);

var result = await kernel.InvokePromptAsync(
    "台北今天天气如何？需要时调用工具。");
```

## 📦 源码案例

- **Planner 的演进**（[GitHub](https://github.com/microsoft/semantic-kernel)）：从早期 ActionPlanner/SequentialPlanner 到 Handlebars/Stepwise Planner，最终收敛到 Function Call 自动路由——「让模型直接选函数」取代「专门规划器生成 DSL 计划」，这个演进史本身就是 [工具选择与路由](../07-planning/tool-selection-routing.md) 的行业缩影
- **Process Framework**：类型化事件 + 步骤的工作流框架，读它的「订单处理」示例可见「事件驱动的确定性编排 + LLM 步骤」的混合范式（呼应 [工作流编排](../07-planning/workflow-orchestration.md)）
- **与 Agent Framework 的关系**：[microsoft/agent-framework](https://github.com/microsoft/agent-framework) 是 SK 与 AutoGen 合流的新家——企业存量代码维护在 SK，新多 Agent 项目官方推荐 Agent Framework

## ⚠️ 常见误区

- ❌ Semantic Kernel 是 Python 优先框架：它最强的生态在 .NET；Python 侧 LangChain/AutoGen 生态更大
- ❌ Planner 什么都能规划：早期 Planner 生成的计划脆弱易错（模型幻觉 DSL），这正是行业转向 Function Calling 的原因
- ❌ 混淆 SK 与 Agent Framework：关注 microsoft/agent-framework 获取多 Agent 新特性

## 🧪 小练习

如果你的团队是 .NET 技术栈：设计一个「工单自动分派」的 Kernel 插件集（查询工单/查员工负载/分派/通知），并用 InvokePrompt 串起来。

## 🔗 相关资源

- [Semantic Kernel 文档](https://learn.microsoft.com/semantic-kernel/)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)

## 📚 相关知识点

- [AutoGen](autogen.md)
- [OpenAI Agents SDK](openai-agents-sdk.md)
