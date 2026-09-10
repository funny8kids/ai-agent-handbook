---
tags: [tooling]
type: knowledge
status: published
updated: 2026-09-10
---

# 🔌 Tool Use

> **一句话**：Tool Use 是比 Function Calling 更宏观的话题：如何设计工具集、控制工具面、路由选择与组合调用，让 Agent 「手」够用且不乱摸。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#tooling`

## 📌 先看结论

- 工具设计的四个原则：原子性（一件事）、无歧义（名字和描述自解释）、幂等友好（失败可重试）、返回可消化（结构化 + 截断）
- 工具面控制：数量多 → 分组/延迟加载/动态注入（MCP 动态开启关闭）
- 组合调用：串行依赖、并行无依赖、程序化组合（PTC：让模型写代码一次执行多步）
- 工具结果的「可观察性」决定模型下一步质量：报错要含上下文

## 🧩 工具集设计清单

| 原则 | 反例 | 正例 |
|---|---|---|
| 原子性 | `manage_user(action="create/delete/update")` | `create_user` / `delete_user` 分开 |
| 无歧义 | `get_data` | `get_order_by_id` |
| 参数扁平 | 5 层嵌套对象 | 一层字段 + 枚举 |
| 结果干净 | 返回 500 行原始 HTML | 返回提炼后的 JSON + 截断说明 |

## 📦 源码案例

**三家 harness 的工具哲学对比**（案例深拆见 [编程 Agent](../12-applications/coding-agent.md)）：

| 项目 | 内置工具数 | 哲学 | 关键机制 |
|---|---|---|---|
| Pi | 4 个原子工具（read/write/edit/bash） | Unix 哲学：少而正交，能力靠组合 | 按需让 Agent 自写扩展并热加载 |
| Claude Code | ~27 个内置 | 覆盖全 + 延迟加载 | ToolSearch 先列名再取 schema；子 Agent 工具面隔离 |
| DeepSeek Harness | 插件化，模式可切 | 工具面 = 可插拔策略 | 标准/极简/PTC 三种工具模式一键切换 |

- **Claude Code 的 Grep/Read/Bash 分工**：搜索用 Grep（ripgrep 加持）、已知路径用 Read、复杂管道用 Bash——工具描述里明确分工边界，模型选择准确率因此大增
- **DeepSeek Harness 的 PTC 模式**：模型写一段 Python 把「查 API → 过滤 → 写文件」组合成一次执行——多轮工具调用变一轮代码执行，省 token 且确定性强，是 Tool Use 的下一代形态（Programmatic Tool Calling）

## ⚠️ 常见误区

- ❌ 万能工具：一个工具 20 个可选参数 = 20 个出错点，拆开
- ❌ 工具结果直接塞回：5000 行的 `ls -R` 输出会毁掉上下文预算，先截断/摘要
- ❌ 忽略并发：并行调用同一文件系统工具会产生竞态，要串行化或加锁

## 🧪 小练习

把「CRM 管理工具」（一个大 JSON 参数含 15 个操作）重构成原子工具集，并列出每个工具的 description 要点。

## 📚 相关知识点

- [Function Calling](function-calling.md)
- [工具选择与路由](../07-planning/tool-selection-routing.md)
- [MCP](mcp.md)
