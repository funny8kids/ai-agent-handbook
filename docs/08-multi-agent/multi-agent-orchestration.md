---
tags: [multi-agent, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 多 Agent 编排

> **一句话**：编排 = 决定「几个 Agent、什么拓扑、谁调度、怎么容错」的顶层设计——监督者、群聊、Swarm 都只是编排谱系上的几个点。

## 先看结论

- 编排三问：拓扑（谁连谁）、调度（谁决定下一步）、容错（坏了怎么办）
- 生产系统几乎都是**混合编排**：监督者为骨架 + 局部并行 + 关键路径人工节点
- 成本增长是**乘法级**的（Agent 数 × 轮数 × 单次上下文），必须有全局预算器
- 编排的可观测性比拓扑选择更重要：没有 trace 的多 Agent 系统无法调试

## 核心机制

### 1. 成本是乘法，不是加法

多 Agent 的 token 成本近似：

$$
\text{Cost}\;\approx\;\underbrace{n}_{\text{Agent 数}}\times\underbrace{R}_{\text{轮数}}\times\underbrace{\overline{|\text{ctx}|}}_{\text{单次上下文}}
$$

三项都是相乘关系，所以任何一个失控都会放大成本。**推论**：编排层必须持有全局预算并在派发前检查（见 [缓存与成本优化](../11-engineering/caching-cost-optimization.md)）。Anthropic 的研究系统披露其多 Agent 架构的 token 消耗约为单 Agent 聊天的 15 倍——这是「编排复杂度」的直接价格标签。

### 2. 编排三要素

把编排形式化为一个三元组：

$$
\text{Orchestration}=\big(\underbrace{\text{Topology}}_{\text{谁连谁}},\;
\underbrace{\text{Schedule}}_{\text{谁决定下一步}},\;
\underbrace{\text{FaultModel}}_{\text{坏了怎么办}}\big)
$$

- **Topology**：顺序流水线、监督者/层级、群聊、Swarm——决定通信边数与信息流向
- **Schedule**：静态（写死的图）还是动态（Lead 运行时决定并行数与子任务）；动态更灵活但更难预测成本
- **FaultModel**：失败域如何隔离——「一个 Worker 崩溃重启该子任务」而不是拖垮全局

三者必须一起设计：选了大扇出的拓扑，就必须配预算器；选了动态调度，就必须配可观测性。

### 3. 为什么生产系统都是混合编排

单一拓扑都有明确短板：

| 拓扑 | 短板 |
|---|---|
| 顺序流水线 | 无法处理需要回退/发散的任务 |
| 监督者 | 中心节点是瓶颈与单点 |
| 群聊 | 成本高、收敛慢 |
| Swarm | 无全局视角 |

混合编排的做法是**按阶段选拓扑**：前期调研用监督者并行扇出，方案评审用群聊/辩论，执行阶段用顺序流水线，局部异常时用 handoff 转人工。这正是「编排谱系」的意义——不是选一个点，而是按任务阶段在谱系上移动。

## 编排谱系

```mermaid
flowchart LR
  A["顺序流水线<br/>固定·最稳"] --> B["监督者/层级<br/>统筹·主流"] --> C["群聊/辩论<br/>发散·贵"] --> D["Swarm/handoff<br/>去中心·轻"] --> E["动态自组<br/>前沿·实验"]
```

## 工程含义

- **每条 Agent 间通信都要有 trace**：who→whom、内容摘要、token 成本、耗时。多 Agent 的 bug 大多出在「谁把什么传给了谁」。
- **编排逻辑放代码/配置，不放 prompt**：拓扑与调度应可测试、可版本化；模型只负责节点内的决策。
- **失败域隔离**：Worker 崩溃只重试该子任务并隔离其输出，不影响编排队列。
- **编排可评估**：把「编排决策」本身纳入评估——并行度是否合理、是否出现重复劳动、是否在关键路径上等待。

## 源码案例

- **DeepSeek Harness：编排即插件**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：Agent Loop、调度、子 Agent 策略全部可插拔；官方定位为「层级式 Supervisor–Worker 为主，兼容并行、流水线和可替换循环的混合系统」——「编排策略与运行时解耦」是目前较彻底的开源实现
- **Anthropic 研究系统的编排细节**（[工程博客](https://www.anthropic.com/engineering/built-multi-agent-research-system)）：Lead 动态决定并行 Worker 数、子任务分配与「何时停止搜索」；容错采用「Agent 崩溃则重启该子任务而非全局」——编排 = 调度 + 容错的联合设计
- **LangGraph 的编排原语**（[仓库](https://github.com/langchain-ai/langgraph)）：StateGraph + 条件边 + checkpoint + interrupt 可拼出全部拓扑；官方模板族（supervisor / hierarchical / handoff）是编排学习的开源图书馆
- **12-Factor Agents**（[GitHub](https://github.com/humanlayer/12-factor-agents)）：其中若干条（无状态 reducer、把控制权交给人）给出了「不用重框架」的编排原则，适合框架怀疑论者

## 常见误区

- ❌ 从「要建多 Agent 系统」出发设计：应从「任务需要什么」出发，多数任务单 Agent + 好工具足够
- ❌ 编排逻辑写在 prompt 里：拓扑与调度应是代码/配置（可测试），模型只做节点内决策
- ❌ 无预算失控：多 Agent 的 token 成本增长是乘法级的，没有预算器等于开着水龙头睡觉
- ❌ 只为拓扑选框架：应看框架是否同时解决调度与容错，以及可观测性是否到位
- ❌ 忽略关键路径：并行只压缩非关键路径，优化要盯住关键路径

## 小练习

「自动处理 GitHub 仓库的 issue 分类 → 修复 → 测试 → PR」：选一种编排拓扑，画出拓扑与容错策略，估算单 issue 处理的 token 成本区间，并指出你会把预算器挂在哪一层。

## 参考资料

- [How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)（Anthropic Engineering）
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [12-Factor Agents](https://github.com/humanlayer/12-factor-agents)
- [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657)（Cemri et al., 2025）

## 相关知识点

- [监督者模式](supervisor-pattern.md)
- [通信协议](communication-protocol.md)
- [工作流编排](../11-engineering/workflow-orchestration.md)
