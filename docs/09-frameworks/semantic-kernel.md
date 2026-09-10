---
tags: [framework]
type: knowledge
status: published
updated: 2026-09-10
---

# Semantic Kernel

> **一句话**：微软的企业级 LLM SDK（C#/Python/Java 三栖）：以「插件 + 规划器」为核心，深度集成 Azure 生态——微软技术栈企业的默认选择。

## 先看结论

- 定位：面向企业 .NET 生态的 LLM 编排 SDK，强调依赖注入、可观测、负责任 AI
- 核心抽象：Kernel（内核）+ Plugin（原生函数/提示函数）+ Planner（规划器）+ Memory
- 与 AutoGen 的关系：两者合流演进的成果是 **Microsoft Agent Framework**——新项目优先看后者；SK 自身持续服务存量企业
- 特色：Process Framework（类型化事件驱动工作流）与对 Azure OpenAI / Azure AI Search 的一线集成

## 核心抽象

Semantic Kernel 的设计语言来自**企业应用框架**而非 AI 研究：它把 LLM 能力当作可注入的服务来管理。

$$
\text{Kernel}=\big(\underbrace{\text{Services}}_{\text{模型/记忆等}},\;\underbrace{\text{Plugins}}_{\text{函数集合}},\;\underbrace{\text{Config}}_{\text{注入与策略}}\big)
$$

- **Kernel**：服务容器（类似 Spring 容器），负责解析依赖、统一配置
- **Plugin**：一组函数的集合，函数可以是**原生代码**（C#/Python 方法）或**提示函数**（prompt 模板）——两者在调用侧无差别
- **Planner**：早期负责「按目标生成函数调用计划」

**最值得学的是 Planner 的演进史**：从专用规划器（生成 DSL 计划）→ 到最终由模型的 Function Calling 直接选函数。这条路线是整个行业的缩影——**「让模型直接选工具」取代了「让模型生成计划文本再解析」**，因为后者脆弱、易被幻觉破坏（见 [工具选择与路由](../07-planning/tool-selection-routing.md)）。

| 概念 | 作用 | 类比 |
|---|---|---|
| Kernel | 配置、服务、插件的容器 | Spring 容器 |
| Plugin / Function | 原生代码或提示词封装的能力 | 带注解的接口方法 |
| Planner | 按目标规划（已收敛到函数调用路由） | 调度员 |
| Process Framework | 类型化事件 + 步骤的工作流 | 状态机引擎 |

## C# 最小示例

```csharp
var builder = Kernel.CreateBuilder();
builder.AddAzureOpenAIChatCompletion(deployment, endpoint, key);
var kernel = builder.Build();
kernel.ImportPluginFromFunctions("weather",
    [KernelFunctionFactory.CreateFromMethod(GetWeather, "查询天气")]);

var result = await kernel.InvokePromptAsync(
    "台北今天天气如何？需要时调用工具。");
```

## 选型对比

| 维度 | Semantic Kernel | AutoGen | LangChain |
|---|---|---|---|
| 语言生态 | .NET 最强（含 Java） | Python 优先 | Python 优先 |
| 设计语言 | 企业 DI / 插件 | 对话参与者 | 链式编排 |
| 工作流 | Process Framework | 消息流 | LCEL / LangGraph |
| 适合 | .NET 企业集成、Azure 栈 | 多 Agent 研究/代码执行 | 快速搭建应用 |

**选型建议**：.NET/Java 企业且已在 Azure 生态 → SK；新多 Agent 项目 → 关注 Microsoft Agent Framework；Python 快速原型 → LangChain/AutoGen。

## 源码案例

- **Planner 的演进**（[GitHub](https://github.com/microsoft/semantic-kernel)）：从早期 ActionPlanner/SequentialPlanner 到 Handlebars/Stepwise Planner，最终收敛到 Function Calling 自动路由——「让模型直接选函数」取代「专门规划器生成 DSL 计划」，这段演进史本身就是工具选择与路由的行业缩影
- **Process Framework**：类型化事件 + 步骤的工作流框架，读它的「订单处理」示例可见「事件驱动的确定性编排 + LLM 步骤」的混合范式（呼应 [工作流编排](../11-engineering/workflow-orchestration.md)）
- **与 Agent Framework 的关系**：[microsoft/agent-framework](https://github.com/microsoft/agent-framework) 是 SK 与 AutoGen 合流后的新家——存量企业代码维护在 SK，新多 Agent 项目官方推荐 Agent Framework

## 常见误区

- ❌ Semantic Kernel 是 Python 优先框架：它最强的生态在 .NET；Python 侧 LangChain/AutoGen 生态更大
- ❌ Planner 什么都能规划：早期 Planner 生成的计划脆弱易错（模型幻觉出的 DSL 无法执行），这正是行业转向 Function Calling 的原因
- ❌ 混淆 SK 与 Agent Framework：关注 microsoft/agent-framework 获取多 Agent 新特性
- ❌ 把 Kernel 当全局单例滥用：它是 DI 容器，应按作用域管理，否则测试与多租户隔离都变难

## 小练习

如果你的团队是 .NET 技术栈：设计一个「工单自动分派」的 Kernel 插件集（查询工单/查员工负载/分派/通知），用 InvokePrompt 串起来，并说明每个插件函数的 description 要写什么。

## 参考资料

- [Semantic Kernel 文档](https://learn.microsoft.com/semantic-kernel/)
- [Semantic Kernel GitHub](https://github.com/microsoft/semantic-kernel)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)

## 相关知识点

- [AutoGen](autogen.md)
- [OpenAI Agents SDK](openai-agents-sdk.md)
- [工具选择与路由](../07-planning/tool-selection-routing.md)
