---
tags: [memory, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 记忆压缩、遗忘与摘要

> **一句话**：窗口迟早会满，所以 Agent 必须学会「忘记」：压缩（保留要点）、摘要（浓缩历史）、遗忘（主动淘汰）——这是长任务 Agent 的生存技能。
> **难度**：进阶
> **标签**：`#memory` `#engineering`

## 先看结论

- 三种策略：截断（最粗暴）、摘要（信息浓缩）、结构化外存（放外部按需检索）——生产系统三者混用
- 压缩触发时机：水位线（如 80%）或每 N 轮定时
- 压缩的黄金对象是**工具输出**：占上下文 60–90%，且多数历史工具结果不再需要全文
- 不可压缩的核心区：system prompt、最近几轮对话、当前任务状态

## 压缩流水线

```mermaid
flowchart LR
  A[上下文水位监测] -- 达到阈值 --> B[选择压缩对象<br/>旧工具输出/久远对话]
  B --> C[生成摘要<br/>保留决策与结论]
  C --> D[原文外存<br/>可按需检索回]
  D --> E[替换原文为摘要]
```

## 源码案例

**三家 harness 的三种答案**（案例深拆见 [编程 Agent](../12-applications/coding-agent.md)）：

- **Claude Code：三档压缩体系**（逆向分析，[架构深拆](https://gist.github.com/yanchuk/0c47dd351c2805236e44ec3935e9095d)）
  - auto-compact：窗口将满时整体摘要压缩，保留目标、决策、未完成项
  - microcompact：细粒度替换单个旧工具输出
  - snip：更小的局部裁剪
  - 配套「工具使用摘要」——用一次摘要代替多次工具调用的原始输出
- **Pi：三条机制守水位**（[earendil-works/pi](https://github.com/earendil-works/pi)）：截断、摘要、微压缩，全部嵌在 agentLoop 内随水位自动触发；被压缩的原始消息仍在 JSONL 会话文件里，可回溯——「压缩 ≠ 丢失」
- **DeepSeek Harness：投影式「遗忘」**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：append-only 日志永远保留全量事件，模型上下文只是日志的「投影」——遗忘发生在投影层，历史层永不丢失，回放/审计/取证全都可能。这是架构上最优雅的「记忆分层」

## 最佳实践

- 摘要 prompt 要点：保留用户目标、关键决策、失败尝试教训、当前进度；丢弃过程细节
- 压缩前后各做一次「任务状态」结构化检查（Todo 清单），防止压缩吃掉关键 TODO
- 高风险操作（改过的文件路径、已部署配置）永不压缩进模糊摘要

## 常见误区

- ❌ 依赖超长窗口不压缩：成本、延迟、注意力衰减三重惩罚，压缩永远有价值
- ❌ 摘要丢掉「失败记录」：失败教训恰恰是自我改进的原料（→ [Reflexion](../04-prompt-reasoning/reflexion.md)）
- ❌ 压缩不可逆：像 DSH 那样保留原始事件流，压缩才敢激进

## 小练习

一个爬虫 Agent 跑 3 小时、200 轮，每轮工具输出 2K token。设计它的压缩策略：水位线多少？什么保留？摘要模板写出来。

## 相关知识点

- [上下文工程](context-engineering.md)
- [Agent 状态管理](../02-agent-basics/state-management.md)
