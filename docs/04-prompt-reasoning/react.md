---
tags: [prompt, agent]
type: knowledge
status: published
updated: 2026-09-10
---

# 💬 ReAct

> **一句话**：ReAct（Reasoning + Acting）让模型交替进行「思考轨迹」和「行动」——想一步、做一步、看结果、再想，是现代 Agent 循环的思想原型。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#prompt` `#agent`

## 📌 先看结论

- 核心洞察：推理为行动提供计划与追踪，行动为推理提供真实反馈——两者缺一都会失败
- 论文数据：HotpotQA/HAL等任务上，ReAct 大幅超越纯推理（CoT-only）与纯行动（Act-only）基线
- 今天所说「Agent 循环」几乎都是 ReAct 的工程化；区别只在「思考写在文本里」还是「内化为专用 token」
- 幻觉链（hallucination）可以被真实工具结果「拉回正轨」——这是 ReAct 比 CoT 抗幻觉的根本原因

## 🖼️ 循环示例

```text
问题: 2026年开源的 DeepSeek Harness 用什么插件框架?

Thought 1: 我需要先搜索 DeepSeek Harness 的发布信息。
Action 1: search["DeepSeek Harness 开源"]
Observation 1: 2026年8月开源，基于 Cordis 插件框架，MIT 协议……

Thought 2: 已获得答案：Cordis。
Action 2: finish["Cordis 插件框架"]
```

## 📦 源码案例

- **Pi：ReAct 的最小工程体**（[badlogic/pi-mono](https://github.com/badlogic/pi-mono)）：agentLoop 把 ReAct 循环压缩到 ~300 行——模型消息里的 tool_use 就是 Action，工具执行结果回填就是 Observation，而「Thought」直接由模型的原生推理承担。读完这个仓库，再厚的框架都不神秘
- **DeepSeek Harness：ReAct 的状态机化**（[agent.ts](https://github.com/deepseek-ai/deepseek-harness)）：Thought/Action/Observation 变成显式事件流——`assistant/message`（含思考与工具调用）、`tool/result` 全部写入 append-only 日志，每一步可回放可审计
- **Claude Code：ReAct + 治理层**（逆向分析，[提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts)）：在循环之上加权限管道（Action 执行前过审批）、TodoWrite（把 Thought 固化成结构化计划）、压缩（Observation 超预算自动摘要）

## ✅ 最佳实践

- Observation 环节清洗工具输出：截断、去噪、错误信息保留原文
- 给「Thought」留空间：别在 system prompt 里禁止模型解释意图
- 失败的 Observation 是金矿：显式提示模型「上次工具报错，换个方法」可显著提升恢复率

## ⚠️ 常见误区

- ❌ ReAct = 框架名：它是论文提出的 prompt 模式，LangChain 的 `ReActAgent` 只是实现之一
- ❌ 思考和行动必须都用文本：推理模型把 Thought 内化了，行为模式仍是 ReAct
- ❌ 只用 ReAct 就够：复杂任务仍需计划工具（TodoWrite）、记忆系统配合，ReAct 只是循环骨架

## 🧪 小练习

用 50 行以内的代码（任意语言）实现一个 ReAct 循环：一个 LLM 调用 + 一个 `calculator` 工具 + 循环。写不出来就对照 Pi 的 agentLoop 读源码。

## 🔗 相关资源

- [ReAct 论文](../13-resources/papers/react.md)
- [Pi Agent 源码](https://github.com/badlogic/pi-mono)

## 📚 相关知识点

- [感知—规划—行动循环](../02-agent-basics/perception-planning-action.md)
- [Chain of Thought](chain-of-thought.md)
