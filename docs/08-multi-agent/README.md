---
tags: [multi-agent]
type: index
status: published
updated: 2026-09-20
---

# 08 多智能体

{% hint style="info" %}
**一句话**：多个 Agent 协作能换來更强的能力面与并行度，代价是通信成本、错误传播与调试复杂度——本章讲清协作模式与治理方法。
{% endhint %}

![Supervisor–Worker 协作](../.gitbook/assets/08-multi-agent.svg)

## 你将学到

- 什么时候真的需要多 Agent（以及什么时候单 Agent 更好）
- 角色分配、通信协议与三种经典拓扑：监督者、群聊、Swarm
- 辩论/共识/投票：用分歧提升质量
- 编排：LangGraph 图编排、DeepSeek Harness 的 Supervisor–Worker、Claude Code 的子 Agent 隔离

## 先泼冷水

Anthropic 与一线实践反复验证：**多 Agent 是最后的手段，不是默认架构**。每加一个 Agent，通信 token、失败模式、调试成本都翻倍。先读完本章再决定要不要「组队」。

## 本站页面

- [多 Agent 协作](multi-agent-collaboration.md)
- [角色分配](role-assignment.md)
- [通信协议](communication-protocol.md)
- [辩论、共识与投票](debate-consensus-voting.md)
- [监督者模式](supervisor-pattern.md)
- [群聊模式](group-chat.md)
- [Swarm](swarm.md)
- [多 Agent 编排](multi-agent-orchestration.md)

## 读完能做到

- [ ] 用 O(n²) 通信边增长和「超过 5 个 Agent 收益常转负」判断一个任务到底该不该拆多 Agent
- [ ] 给三角色（调研 / 写作 / 事实核查）各写出工具面、产出 JSON 格式、两条禁止事项，体现「角色 = 专属指令 + 工具 + 验收」
- [ ] 解释星型拓扑为什么优于点对点，并设计一条带 type / source / artifacts 的类型化消息（引用传递而非塞大产物）
- [ ] 用 Condorcet 陪审团定理说明投票里「独立性」为什么比「数量」重要，以及何时该把投票升级成辩论
- [ ] 给电商客服设计 Swarm 移交图，标出有死循环风险的边、最大跳数兜底，以及交接简报该带哪些字段

## 章末自测

1. **回忆**：多 Agent 的三大收益和三大代价各是什么？判据为什么是「上下文是否互相污染」而不是「任务大不大」？（提示：见 multi-agent-collaboration.md）
2. **应用**：设计「季度财报分析」的 Supervisor：几个 Worker、各自工具面、Worker 只回传什么才不会撑爆中心上下文？（提示：见 supervisor-pattern.md）
3. **判断**：「三个模型辩论一定比一个模型准」——用共同盲区和辩论放大执念两点评价这句话。（提示：见 debate-consensus-voting.md）

