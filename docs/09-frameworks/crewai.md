---
tags: [framework, multi-agent]
type: knowledge
status: published
updated: 2026-09-10
---

# CrewAI

> **一句话**：CrewAI 用「球队隐喻」组织多 Agent：角色（Agent）、任务（Task）、团队（Crew）、流程（Process），上手最快的角色化多 Agent 框架。

## 先看结论

- 四个核心抽象：Agent（role/goal/backstory）、Task（含 expected_output）、Crew（组队）、Process（sequential/hierarchical）
- 卖点是「像组建团队一样写多 Agent」：声明式、易读、教程生态友好
- 层级流程内置经理（Manager），是 [监督者模式](../08-multi-agent/supervisor-pattern.md) 的开箱实现
- 复杂控制流（条件分支、状态机）相对薄弱，重编排场景用 LangGraph

## 核心抽象

CrewAI 的设计判断是：**多 Agent 的难点在于「把角色和任务说清楚」，而不是控制流**。于是它提供了四个声明式抽象，把「组队」变成填空题：

$$
\text{Crew}=\big(\{\text{Agent}_i\},\;\{\text{Task}_j\},\;\text{Process}\big)
$$

- **Agent**：`role`（是谁）、`goal`（要什么）、`backstory`（背景）三件套，本质是**结构化的 prompt 片段**
- **Task**：`description` + `expected_output` + `context`（依赖哪些前序任务）
- **Process**：`sequential`（按任务顺序）或 `hierarchical`（经理分配与质检）

**关键理解**：`expected_output` 是这套抽象里最值钱的字段——它把「验收标准」显式写进任务定义，直接对应 [任务分解](../07-planning/task-decomposition.md) 里「可机检完成判据」的要求。

## 最小 Crew

```python
from crewai import Agent, Task, Crew

researcher = Agent(role="调研员", goal="收集竞品定价信息",
    backstory="资深市场分析师", tools=[search_tool])
writer = Agent(role="撰稿人", goal="写出决策建议",
    backstory="商业专栏作者")

t1 = Task(description="调研3个竞品定价", agent=researcher,
          expected_output="定价对比表")
t2 = Task(description="基于调研写建议", agent=writer,
          expected_output="500字建议", context=[t1])

Crew(agents=[researcher, writer], tasks=[t1, t2],
     process="sequential").kickoff()
```

## 选型对比

| 维度 | CrewAI | AutoGen | LangGraph |
|---|---|---|---|
| 抽象方式 | 角色/任务声明式 | 对话参与者 | 状态图 |
| 上手速度 | 最快 | 中 | 中高 |
| 控制流灵活性 | 低（顺序/层级） | 中（消息流） | 高（任意图） |
| 可观测性 | 需自行补 trace | 中 | 强（图级） |
| 适合 | 角色化流水线、快速原型 | 代码执行闭环、研究 | 复杂可审计编排 |

**选型建议**：任务能拆成「几个角色按顺序做几件事」→ CrewAI 最快；需要条件分支/循环/断点恢复 → LangGraph；需要模型写代码并执行 → AutoGen/Agent Framework。

## 源码案例

- **backstory 的作用机制**（[GitHub](https://github.com/crewAIInc/crewAI)）：读它拼装 prompt 的源码会发现 role/goal/backstory 被模板化地织入 system prompt——「角色」没有魔法，就是结构化的 prompt 片段（呼应 [角色分配](../08-multi-agent/role-assignment.md)）
- **hierarchical 流程**：内置经理做任务分配与质检，是监督者模式的框架化；对照 LangGraph 的 supervisor 模板，可体会「约定俗成的框架 vs 显式图」两种工程风格
- **Flows**：新版加入事件流式编排装饰器，补条件控制流的短板——也反映多 Agent 框架普遍向「图/事件流」收敛的趋势

## 常见误区

- ❌ CrewAI = 生产级多 Agent 银弹：它的抽象屏蔽了通信细节，也屏蔽了可观测性——复杂系统要自己补 trace
- ❌ 角色写得天花乱坠就有用：backstory 过长增量收益很小，工具与验收标准才是关键
- ❌ 需要自由编排还硬用：需要条件/循环时早点迁移到图编排框架
- ❌ 不写 expected_output：验收标准缺失，任务完成与否只能靠模型自述

## 小练习

用 CrewAI 搭「旅行规划三人组」（目的地调研/预算控制/行程编排）：写出每个 Agent 的 role/goal/backstory 与 Task 的 expected_output，跑通后评估产出质量，并指出哪个 Task 的 expected_output 最难写。

## 参考资料

- [CrewAI 官方文档](https://docs.crewai.com)
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI)
- [多 Agent 编排](../08-multi-agent/multi-agent-orchestration.md)

## 相关知识点

- [角色分配](../08-multi-agent/role-assignment.md)
- [监督者模式](../08-multi-agent/supervisor-pattern.md)
- [任务分解](../07-planning/task-decomposition.md)
