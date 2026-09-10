---
tags: [framework, multi-agent]
type: knowledge
status: published
updated: 2026-09-10
---

# 🧰 CrewAI

> **一句话**：CrewAI 用「球队隐喻」组织多 Agent：角色（Agent）、任务（Task）、团队（Crew）、流程（Process），上手最快的角色化多 Agent 框架。
> **难度**：⭐️ 入门
> **标签**：`#framework` `#multi-agent`

## 📌 先看结论

- 四个核心抽象：Agent（role/goal/backstory 三件套）、Task（含 expected_output）、Crew（组队）、Process（sequential/hierarchical 流程）
- 卖点是「像组建团队一样写多 Agent」：声明式、易读、教程生态友好
- 层级流程内置经理（ManagerAgent）——[监督者模式](../08-multi-agent/supervisor-pattern.md) 的开箱实现
- 复杂控制流（条件分支、状态机）相对薄弱，重编排场景用 LangGraph

## 💻 最小 Crew

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

## 📦 源码案例

- **backstory 的作用机制**（[GitHub](https://github.com/crewAIInc/crewAI)）：读 CrewAI 拼装 prompt 的源码会发现 role/goal/backstory 被模板化地织入 system prompt——「角色」没有魔法，就是结构化的 prompt 片段（呼应 [角色分配](../08-multi-agent/role-assignment.md) 的三件套定义）
- **hierarchical 流程**：内置 manager_agent 做任务分配与质检，是监督者模式的框架化；对照 LangGraph 的 supervisor 模板，体会「约定俗成的框架 vs 显式的图」两种工程风格
- **Flows（流程化扩展）**：新版 CrewAI 加入 @listen/@router 装饰器的事件流编排，补条件控制流的短板——观察多 Agent 框架普遍向「图/事件流」收敛的趋势

## ⚠️ 常见误区

- ❌ CrewAI = 生产级多 Agent 银弹：它的抽象屏蔽了通信细节，也屏蔽了可观测性——复杂系统要自己补 trace
- ❌ 角色写得天花乱坠就有用：backstory 超过两三句的增量收益很小，工具与验收标准才是关键
- ❌ sequential/hierarchical 之外的自由编排：需要条件循环时早点迁移到图编排框架

## 🧪 小练习

用 CrewAI 搭「旅行规划三人组」（目的地调研/预算控制/行程编排）：写出每个 Agent 的 role/goal/backstory 与 Task 的 expected_output，跑通后评估产出质量。

## 🔗 相关资源

- [CrewAI 文档](https://docs.crewai.com)
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI)

## 📚 相关知识点

- [角色分配](../08-multi-agent/role-assignment.md)
- [监督者模式](../08-multi-agent/supervisor-pattern.md)
