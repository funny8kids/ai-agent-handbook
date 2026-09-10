---
tags: [mcp, tooling, framework]
type: resource
status: published
updated: 2026-09-10
---

# MCP Servers

> **一句话**：MCP Server 生态是 Agent 工具的「应用商店」：官方与社区维护着数百个现成 Server，覆盖数据库、开发、办公、浏览器等场景。
> **难度**：入门
> **标签**：`#mcp` `#tooling`

| 属性 | 内容 |
|---|---|
| 类型 | 工具生态 |
| 链接 | <https://github.com/modelcontextprotocol/servers> · <https://mcp.so> · <https://github.com/punkpeye/awesome-mcp-servers> |
| 来源 | Anthropic 发起 + 社区 |
| 标签 | `#mcp` `#tooling` |

## 常用 Server 速查

| Server | 能力 | 典型用法 |
|---|---|---|
| filesystem | 受限目录的文件读写 | 让 Agent 安全访问项目文件 |
| github | PR/Issue/仓库操作 | 自动 review、issue 分诊 |
| postgres / sqlite | SQL 查询 | 数据分析 Agent |
| playwright | 浏览器自动化 | 网页操作、端到端测试 |
| slack | 消息收发 | 通知与巡检机器人 |
| memory | 简单知识图谱记忆 | 跨会话记忆实验 |

## 上手建议

1. 先读 [MCP 协议页](../05-tool-protocol/mcp.md) 理解 Tools/Resources/Prompts 三原语
2. 用 Claude Code / DeepSeek Harness / Pi 任一客户端 `add` 一个 filesystem server 跑通
3. 自己写一个 ~50 行的 Server（参考官方 TS/Python SDK），理解注册流程
4. 生产接入前检查：Server 来源可信、走 [权限管道](../05-tool-protocol/tool-permission-sandbox.md)、工具描述无注入风险

## 常见误区

- ❌ Server 装得越多越好：工具面膨胀降低选择准确率（→ [工具选择与路由](../07-planning/tool-selection-routing.md)）
- ❌ 社区 Server 即插即用：恶意 Server 可借工具描述注入指令，供应链审查不可省
- ❌ 把 MCP Server 当微服务调用：它是「给模型用的」，权限、审计按模型行为设计，不按传统 API 设计

## 相关知识点

- [MCP：Model Context Protocol](../05-tool-protocol/mcp.md)
- [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)
