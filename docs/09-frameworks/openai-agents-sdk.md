---
tags: [framework]
type: knowledge
status: published
updated: 2026-09-10
---

# 🧰 OpenAI Agents SDK

> **一句话**：OpenAI 的轻量生产级 Agent SDK（2025 年发布，Swarm 的正式版）：Agent、Handoff、Guardrail、Session 四件套，追求「少抽象、可上线」。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#framework`

## 📌 先看结论

- 三大原语：Agent（指令+工具+移交）、Handoff（控制权移交，[Swarm](../08-multi-agent/swarm.md) 的 SDK 化）、Guardrail（输入/输出并行安检）
- 设计哲学与 Pi 类似：核心循环极简，生产特性（tracing、session、guardrail）做成可选件
- Tracing 内置（兼容 OpenTelemetry），配 [Agent evaluations](../10-evaluation-safety/evaluation-metrics.md) 工具形成闭环
- 支持非 OpenAI 模型（LiteLLM 集成），但最佳体验在 OpenAI 模型（Responses API 原生工具）

## 🧩 四件套速查

| 原语 | 作用 | 对应章节 |
|---|---|---|
| Agent | 指令 + 工具面 + 可移交对象 | [角色分配](../08-multi-agent/role-assignment.md) |
| Handoff | Agent 间控制权转移 | [Swarm](../08-multi-agent/swarm.md) |
| Guardrail | 输入/输出侧安检（并行运行） | [权限控制与沙箱隔离](../10-evaluation-safety/permission-sandbox.md) |
| Session | 自动维护对话历史 | [状态管理](../02-agent-basics/state-management.md) |

## 💻 最小示例

```python
from agents import Agent, Runner

refund = Agent(name="退款专员", instructions="处理退款申请")
tech = Agent(name="技术支持", instructions="解决技术问题")
triage = Agent(name="分诊", instructions="判断意图并移交",
    handoffs=[refund, tech])

result = Runner.run_sync(triage, "我上周买的东西想退款")
print(result.final_output)
```

## 📦 源码案例

- **handoff 的实现深度**（[GitHub](https://github.com/openai/openai-agents-python)）：handoff 被实现为一种特殊工具（`transfer_to_xxx`）——模型「移交」与「调工具」是同一种机制，读完 `run.py` 的 handoff 处理段可彻底理解 [Swarm](../08-multi-agent/swarm.md) 的工程本质；内置回环防护与移交过滤
- **Guardrail 的并行设计**：输入 guardrail 与主 Agent 并行跑（不阻塞），触发即取消主任务——安检不牺牲延迟的工程取舍，值得对照 [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md) 的串行审批链比较
- **Swarm 历史渊源**：实验项目 [openai/swarm](https://github.com/openai/swarm)（2024）是 SDK 的前身，代码仅几百行且明确标注「教学用途」——想看「无框架裸实现」读它，想上生产用 Agents SDK

## ⚠️ 常见误区

- ❌ Agents SDK = 必须 OpenAI 模型：LiteLLM 桥接后可用任意模型，但原生工具（web search、file search）绑定 Responses API
- ❌ Handoff 网可以随便织：移交图带环 + 无跳数限制 = 死循环，SDK 的防护不是借口（→ [Swarm 常见误区](../08-multi-agent/swarm.md)）
- ❌ Guardrail 代替沙箱：guardrail 拦的是「模型输入输出」，管不住工具执行的副作用，两层都要有

## 🧪 小练习

用 Agents SDK 搭二级客服：分诊 → 退款/物流/技术三线 → 人工升级。画出 handoff 图，标出你在哪两个 Agent 间加了 guardrail、为什么。

## 🔗 相关资源

- [OpenAI Agents SDK 文档](https://openai.github.io/openai-agents-python/)
- [openai/swarm（前身）](https://github.com/openai/swarm)

## 📚 相关知识点

- [Swarm](../08-multi-agent/swarm.md)
- [Semantic Kernel](semantic-kernel.md)
