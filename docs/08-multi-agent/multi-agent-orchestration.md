---
tags: [multi-agent, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 👥 多 Agent 编排

> **一句话**：编排 = 决定「几个 Agent、什么拓扑、谁调度、怎么容错」的顶层设计——监督者、群聊、Swarm 都只是编排谱系上的几个点。
> **难度**：⭐️⭐️⭐️ 高级
> **标签**：`#multi-agent` `#engineering`

## 📌 先看结论

- 编排三问：拓扑（谁连谁）、调度（谁决定下一步）、容错（坏了怎么办）
- 生产系统几乎都是**混合编排**：监督者为骨架 + 局部并行 + 关键路径人工节点
- 编排的可观测性比拓扑选择更重要：没有 trace 的多 Agent 系统无法调试
- 框架选型：LangGraph（图编排/状态机）、OpenAI Agents SDK（handoff 网）、CrewAI（角色化）、DeepSeek Harness（插件化编排）——按「你要的拓扑灵活性」选

## 🖼️ 编排谱系

```mermaid
flowchart LR
  A["顺序流水线<br/>固定·最稳"] --> B["监督者/层级<br/>统筹·主流"] --> C["群聊/辩论<br/>发散·贵"] --> D["Swarm/handoff<br/>去中心·轻"] --> E["动态自组<br/>前沿·实验"]
```

## 📦 源码案例

- **DeepSeek Harness：编排即插件**（[仓库](https://github.com/deepseek-ai/deepseek-harness) / [InfoQ 解读](https://www.sohu.com/a/1062640652_122014422)）：Agent Loop、调度（scheduling）、子 Agent 策略全部可插拔；官方明确当前形态是「层级式 Supervisor–Worker 为主，兼容并行、流水线和 Ralph 循环的混合系统」——「编排策略与运行时解耦」是目前最彻底的开源实现
- **Anthropic 研究系统的编排细节**（[工程博客](https://www.anthropic.com/engineering/built-multi-agent-research-system)）：Lead 动态决定并行 Worker 数、子任务分配与「何时停止搜索」；容错采用「Agent 崩溃则重启该子任务而非全局」——编排 = 调度 + 容错的联合设计
- **LangGraph 的编排原语**（[GitHub](https://github.com/langchain-ai/langgraph)）：StateGraph + 条件边 + checkpoint + interrupt 四件套可拼出全部拓扑；官方仓库的 multi-agent 模板族（supervisor / hierarchical / handoff）是编排学习的开源图书馆
- **12-Factor Agents**（[GitHub](https://humanlayer/12-factor-agents)）：第 10–12 条（stateless reducer、launch-pad、contact humans）给出了「不用重框架」的编排原则，适合框架怀疑论者

## ✅ 最佳实践

- 每条 Agent 间通信都有 trace：who→whom、内容摘要、token 成本、耗时
- 全局 token 预算器：Supervisor 派发前查预算，超支触发降级（减并行度/缩范围）
- 失败域隔离：一个 Worker 的崩溃不得拖垮编排队列（重试该子任务、隔离其输出）

## ⚠️ 常见误区

- ❌ 从「要建多 Agent 系统」出发设计：应从「任务需要什么」出发，多数任务单 Agent + 好工具足够
- ❌ 编排逻辑写在 prompt 里：拓扑与调度应是代码/配置（可测试），模型只做节点内决策
- ❌ 无预算失控：多 Agent 的 token 成本增长是乘法级的，没有预算器等于开着水龙头睡觉

## 🧪 小练习

「自动处理 GitHub 仓库的 issue 分类 → 修复 → 测试 → PR」：选一种编排拓扑，画出拓扑与容错策略；估算单 issue 处理的 token 成本区间。

## 🔗 相关资源

- [LangGraph 多 Agent 文档](https://langchain-ai.github.io/langgraph/)

## 📚 相关知识点

- [监督者模式](supervisor-pattern.md)
- [工作流编排](../07-planning/workflow-orchestration.md)
