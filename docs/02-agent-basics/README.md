---
tags: [agent, basics]
type: index
status: published
updated: 2026-09-10
---

# 🤖 02 Agent 基础

> **一句话**：本章回答最核心的问题：Agent 是什么、由什么组成、怎么循环、自主到什么程度、状态放在哪、人什么时候介入。

## 📌 你将学到

- Agent 的定义，以及它和 Chatbot / Workflow / Copilot 的边界
- 五大核心组件：LLM、记忆、工具、规划、执行器
- 感知—规划—行动循环：所有 harness 共同的骨架
- 自主性等级与 Human-in-the-loop 的工程取舍

## 三本必读的「活教材」

学原理最好的方法是对照真实源码，本章案例反复引用三个项目：

| 项目 | 定位 | 读什么 |
|---|---|---|
| [Pi Agent](https://github.com/badlogic/pi-mono) | 极简 harness | 一个 ~300 行的 agentLoop 把循环本质讲透 |
| [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) | 生产级插件化 harness | turn/step 状态机、append-only 事件流 |
| Claude Code | 闭源标杆（社区逆向分析） | 三层 prompt 组装、子 Agent 隔离、上下文压缩 |

深入拆解见 [编程 Agent 案例](../12-applications/coding-agent.md)。

## 本站页面

- [什么是 AI Agent](what-is-agent.md) ✅
- [Agent 与 Workflow、Chatbot、Copilot 的区别](agent-vs-workflow-chatbot-copilot.md)
- [Agent 核心组件](core-components.md)
- [感知—规划—行动循环](perception-planning-action.md)
- [自主性等级](autonomy-levels.md)
- [Agent 状态管理](state-management.md)
- [Human-in-the-loop](human-in-the-loop.md)
