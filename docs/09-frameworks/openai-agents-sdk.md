---
tags: [framework]
type: knowledge
status: published
updated: 2026-09-10
---

# OpenAI Agents SDK

> **一句话**：OpenAI 的轻量生产级 Agent SDK（2025 年发布，Swarm 的正式版）：Agent、Handoff、Guardrail、Session 四件套，追求「少抽象、可上线」。

## 先看结论

- 三大原语：Agent（指令+工具+移交）、Handoff（控制权移交，[Swarm](../08-multi-agent/swarm.md) 的 SDK 化）、Guardrail（输入/输出并行安检）
- 设计哲学与 Pi 类似：核心循环极简，生产特性（tracing、session、guardrail）做成可选件
- Tracing 内置（兼容 OpenTelemetry），配评估工具形成闭环
- 支持非 OpenAI 模型（LiteLLM 集成），但最佳体验在 OpenAI 模型

## 核心抽象

SDK 的核心是一个极简的 Agent 循环，外加三个可选件：

$$
\text{Run}=\text{loop}\big(\underbrace{\text{Agent}}_{\text{指令+工具}},\;\underbrace{\text{Handoff}}_{\text{特殊工具}},\;\underbrace{\text{Guardrail}}_{\text{旁路安检}}\big)
$$

**最精巧的设计是「把 handoff 实现成一个特殊工具」**。模型看到的工具列表里会多出形如 `transfer_to_refund_agent` 的项，因此：

$$
\text{「移交控制权」}=\text{「调用一个工具」}
$$

这一等价让移交**不需要额外的编排机制**——模型按常规工具调用逻辑做决策，框架在执行侧把「调用移交工具」翻译为「切换当前 Agent」。理解这一点，Swarm 模式就没有黑箱了。

| 原语 | 作用 | 对应章节 |
|---|---|---|
| Agent | 指令 + 工具面 + 可移交对象 | [角色分配](../08-multi-agent/role-assignment.md) |
| Handoff | Agent 间控制权转移 | [Swarm](../08-multi-agent/swarm.md) |
| Guardrail | 输入/输出侧安检（并行运行） | [权限控制与沙箱隔离](../10-evaluation-safety/permission-sandbox.md) |
| Session | 自动维护对话历史 | [状态管理](../02-agent-basics/state-management.md) |

**Guardrail 的并行设计**也值得注意：输入安检与主 Agent **并行**执行，一旦触发就取消主任务——这样安检不额外增加延迟。与之相对，权限审批链通常是**串行阻塞**的（因为必须等人类决定）。两种设计对应两类风险：前者防「内容违规」，后者防「动作越权」（见 [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)）。

## 最小示例

```python
from agents import Agent, Runner

refund = Agent(name="退款专员", instructions="处理退款申请")
tech = Agent(name="技术支持", instructions="解决技术问题")
triage = Agent(name="分诊", instructions="判断意图并移交",
    handoffs=[refund, tech])

result = Runner.run_sync(triage, "我上周买的东西想退款")
print(result.final_output)
```

## 选型对比

| 维度 | Agents SDK | LangGraph | AutoGen |
|---|---|---|---|
| 抽象量 | 最少（四件套） | 中（图/状态） | 中（对话参与者） |
| 控制流 | handoff 网 + 循环 | 显式图 | 消息流 |
| 生产特性 | tracing/session/guardrail 内置 | 需配 LangSmith | 需自行补 |
| 模型绑定 | OpenAI 最佳，LiteLLM 可桥接 | 任意 | 任意 |

**选型建议**：以 OpenAI 模型为主、想要「少抽象 + 生产特性齐全」→ Agents SDK；需要复杂可审计控制流 → LangGraph；需要代码执行闭环 → AutoGen。

## 源码案例

- **handoff 的实现深度**（[GitHub](https://github.com/openai/openai-agents-python)）：handoff 被实现为一种特殊工具——模型「移交」与「调工具」是同一种机制，读完其运行循环的 handoff 处理段可彻底理解 [Swarm](../08-multi-agent/swarm.md) 的工程本质；内置回环防护与移交过滤
- **Guardrail 的并行设计**：输入 guardrail 与主 Agent 并行跑（不阻塞），触发即取消主任务——安检不牺牲延迟的工程取舍
- **Swarm 历史渊源**：实验项目 [openai/swarm](https://github.com/openai/swarm)（2024）是 SDK 的前身，代码仅几百行且明确标注「教学用途」——想看「无框架裸实现」读它，想上生产用 Agents SDK

## 工程含义

- **移交图要显式设计**：把 handoff 关系画成有向图，检查环与跳数上限，别依赖模型的「礼貌」。
- **Guardrail 与沙箱分工不同**：guardrail 管「输入输出内容」，管不住工具执行的副作用——两层都要有。
- **Session 简化但不等于记忆管理**：它维护对话历史，但压缩、检索与遗忘仍需自己设计（见 [记忆压缩](../06-memory-rag/memory-compression-forgetting.md)）。

## 常见误区

- ❌ Agents SDK = 必须 OpenAI 模型：LiteLLM 桥接后可用任意模型，但原生工具绑定 Responses API
- ❌ Handoff 网可以随便织：移交图带环 + 无跳数限制 = 死循环，SDK 的防护不是借口
- ❌ Guardrail 代替沙箱：guardrail 拦的是「模型输入输出」，管不住工具执行的副作用
- ❌ 把 Session 当完整记忆方案：它只维护历史，不负责压缩与检索

## 小练习

用 Agents SDK 搭二级客服：分诊 → 退款/物流/技术三线 → 人工升级。画出 handoff 图，标出你在哪两个 Agent 间加了 guardrail、为什么，并指出哪些动作需要串行权限审批。

## 参考资料

- [OpenAI Agents SDK 文档](https://openai.github.io/openai-agents-python/)
- [openai/swarm（前身，教学用途）](https://github.com/openai/swarm)
- [OpenAI Agents SDK GitHub](https://github.com/openai/openai-agents-python)

## 相关知识点

- [Swarm](../08-multi-agent/swarm.md)
- [Semantic Kernel](semantic-kernel.md)
- [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)
