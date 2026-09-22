---
tags: [agent, basics]
type: index
status: published
updated: 2026-09-23
---

# 02 Agent 基础 · 本章导读

{% hint style="info" %}
**一句话**：本章回答最核心的问题：Agent 是什么、由什么组成、怎么循环、自主到什么程度、状态放在哪、人什么时候介入。
{% endhint %}

![Agent 核心循环](../.gitbook/assets/02-agent-loop.svg)

*《图：目标进、观察出，四步一圈；LLM 推理、工具、记忆是撑住这一圈的三块底座，不在圈上》*
## 你将学到

- Agent 的定义，以及它和 Chatbot / Workflow / Copilot 的边界
- 五大核心组件：LLM、记忆、工具、规划、执行器
- 感知—规划—行动循环：所有 harness 共同的骨架
- 自主性等级与 Human-in-the-loop 的工程取舍

## 三本必读的「活教材」

学原理最好的方法是对照真实源码，本章案例反复引用三个项目：

| 项目 | 定位 | 读什么 |
|---|---|---|
| [Pi Agent](https://github.com/earendil-works/pi) | 极简 harness | 一个 ~300 行的 agentLoop 把循环本质讲透 |
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

## 读完能做到

- [ ] 不看资料写出最小 Agent 循环伪代码，并说出三个止损开关（轮次上限、token 预算、时间上限）各防哪种失控
- [ ] 用「谁决定下一步 + 谁选工具」两条判据，把 Chatbot / Copilot / Workflow / Agent 分开，并给一个去掉「用户点发送」就改变形态的例子
- [ ] 说清去掉「记忆」组件后 Pi 式 Agent 退化成什么形态，再列出加回记忆要新增的两项工程
- [ ] 按「可逆性 × 影响面 × 不确定性」给一个动作清单排 L0–L4，指出哪些能全自动、哪些必须事前审批
- [ ] 为一个爬虫 Agent 设计状态方案：断点续爬要存哪类状态、放模型上下文还是外部存储、为什么

## 章末自测

1. **回忆**：Agent 与 Workflow 的根本分界是什么？为什么「控制流交给谁」比「有没有聊天界面」更本质？（提示：见 what-is-agent.md、agent-vs-workflow-chatbot-copilot.md）
2. **应用**：给「自动整理相册」的 Agent 排 L0–L4：读取、分类打标、删除重复、上传云盘，哪些能全自动、哪些必须确认？（提示：见 autonomy-levels.md、human-in-the-loop.md）
3. **判断**：「记忆越多 Agent 越聪明」——用状态管理里「上下文 vs 外部存储」的取舍，以及过时记忆的坑害，评价这句话。（提示：见 state-management.md、core-components.md）

## 本章术语速查

本章的名词一半是产品品类、一半是工程黑话，出发前先扫一遍表，读循环时不会卡在词上。

| 英文术语 | 中文 | 白话一句话 |
|---|---|---|
| Agent | 智能体 | 给它目标，它自己决定下一步做什么、用哪个工具，循环到达成为止——有没有聊天框不算数 |
| Chatbot | 聊天机器人 | 问一句答一句，流程全捏在用户手里，模型只负责「生成这一句」 |
| Copilot | 副驾驶 | 你握方向盘，它报路线、补半句，最后拍板采纳的还是你 |
| Workflow | 工作流 | 节点和流转全被开发者写死的流水线：便宜、可测，但应付不了图外的情况 |
| LLM | 大语言模型 | Agent 的大脑，负责推理与决策；记忆、工具、规划、执行器都围着它转 |
| Harness | Agent 执行外壳 | 循环外面的「机房」：管状态、工具、审批。Pi 那 ~300 行 `agentLoop` 是最小标本 |
| Perception–Planning–Action | 感知—规划—行动 | Agent 的心跳：观察→思考→行动→再观察，ReAct 是它的 prompt 化实现 |
| Autonomy Levels (L0–L4) | 自主性等级 | 从「只出主意」到「目标级无人值守」的放权滑杆，按动作的可逆性和可验证性来定档 |
| Kill Switch | 接管通道 | 任何时刻人都能一脚刹停，这是 L3 以上的硬性要求 |
| State Management | 状态管理 | 分清单对话、任务、世界三层状态该塞进上下文窗口还是存到外面，别把记性全押在窗口里 |
| Human-in-the-Loop (HITL) | 人在回路 | 不是去掉人，是把人安在批准、否决、纠偏最值钱的那几个节点上 |

