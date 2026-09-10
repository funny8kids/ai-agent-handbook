---
tags: [framework, agent]
type: resource
status: published
updated: 2026-09-10
---

# Pi Agent（earendil-works/pi）

> **一句话**：极简路线的开源 Agent harness——用最小的原语（统一 LLM API + Agent 循环 + TUI + 编码 CLI）把「Agent 本质」讲清楚。

| 属性 | 内容 |
|---|---|
| 类型 | 开源项目（Agent harness / 工具包） |
| 链接 | <https://github.com/earendil-works/pi> · [官网](https://pi.dev) |
| 来源/作者 | earendil-works（原 `badlogic/pi-mono`，2026 年更名迁移） |
| 发布/更新时间 | 2025-08 创建；详见仓库 |
| 许可 | MIT |
| 活跃度 | 约 10.4 万 star（2026-09 观测）；最近提交 2026-09 |
| 语言 | TypeScript |
| 难度 | 进阶 |
| 标签 | `#framework` `#agent` |

## 推荐理由

它代表与「大而全框架」相反的一条路线：**提供原语，而非成品**。仓库的包划分本身就是一份设计宣言：

- `packages/coding-agent`（`@earendil-works/pi-coding-agent`）：交互式编码 Agent CLI
- `packages/agent`（`pi-agent-core`）：带工具调用与状态管理的 Agent 运行时
- `packages/ai`（`pi-ai`）：统一多 provider LLM API（OpenAI / Anthropic / Google …）
- `packages/tui`（`pi-tui`）：终端 UI 库
- `packages/chord`、`packages/telemetry`：应用组合运行时与厂商中立的可观测契约

**什么时候值得读**：想知道「一个 Agent 循环最小需要什么」时，从上到下读一遍比读任何教程都直接。

> **注意**：本项目在 2026 年从 `badlogic/pi-mono` 更名为 `earendil-works/pi` 并重构了包结构。旧链接会自动跳转，但**具体的内部实现细节（如循环行数、工具数量）请以当前仓库与 pi.dev 文档为准**——本书已删除此前无法核实的相关表述。

## 上手建议

1. 从 README 的包表格入手，按 `pi-ai` → `pi-agent-core` → `pi-coding-agent` 的顺序理解分层
2. 想了解本项目的设计理念，读官网 [pi.dev](https://pi.dev) 与文档
3. 前置知识：[Agent 核心组件](../../02-agent-basics/core-components.md)、[感知—规划—行动循环](../../02-agent-basics/perception-planning-action.md)
4. 对照阅读：[DeepSeek Harness](deepseek-harness.md)（平台化路线）——两条路线正好构成光谱两端

## 参考资料

- [仓库](https://github.com/earendil-works/pi)
- [官网与文档](https://pi.dev)

## 相关知识点

- [Agent 核心组件](../../02-agent-basics/core-components.md)
- [感知—规划—行动循环](../../02-agent-basics/perception-planning-action.md)
- [ReAct](../../04-prompt-reasoning/react.md)
- [编程 Agent](../../12-applications/coding-agent.md)
