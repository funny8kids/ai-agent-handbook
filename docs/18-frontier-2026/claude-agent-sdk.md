---
tags: [claude, agent-sdk, harness, framework]
type: knowledge
status: published
updated: 2026-09-12
---

# Claude Agent SDK

> **一句话**：把 Claude Code 的 agent loop、工具、权限、会话与 Skills 做成 **Python / TypeScript 库**，让你在自己的进程里跑同一套生产级循环。

## 先看结论

- Agent SDK ≠ 再包一层 Messages API：它交付的是 **harness**（循环 + 工具 + 权限 + 压缩 + 子 Agent）
- 与四种形态的分界：SDK（库内循环）/ CLI（交互终端）/ Client SDK（裸 API，自己写循环）/ Managed Agents（托管 REST）
- 能力与 Claude Code 对齐：内置文件与命令工具、Hooks、Subagents、MCP、Permissions、Sessions、Skills/Plugins
- 认证：一般用 API Key；第三方产品不得未经批准提供 claude.ai 登录额度

## 与相邻形态对比

| 你想做什么 | 用 | 原因 |
|---|---|---|
| 在自己应用里跑 Agent，不自己实现工具循环 | **Agent SDK** | Python/TS 库，进程内控制 |
| 终端交互开发 / 一次性任务 | Claude Code CLI | 产品化 TUI |
| 完全自定义循环，直连模型 API | Client SDK / Messages API | 你负责 loop |
| 长时异步、不想管沙箱 | Managed Agents | Anthropic 托管 REST + 沙箱 |

## 核心机制

### 1. 你买到的是「可嵌入的 Claude Code 内核」

```text
你的应用
  └── Agent SDK query(...)
        ├── system prompt / 项目 .claude 配置加载
        ├── agent loop：模型 → 工具 → 观察 → 再模型
        ├── permissions：自动 / 需确认 / 拒绝
        ├── sessions：可恢复、可分叉
        └── subagents / MCP / skills / hooks
```

这与 [OpenAI Agents API](openai-agents-api.md) 的差别是部署形态：SDK 默认 **你的进程、你的环境**；Agents API 默认 **OpenAI 托管 harness + 沙箱**。

### 2. Skills 与项目约定

SDK 会加载与 Claude Code 相同的项目配置目录（如 `.claude/` 与用户级配置），因此：

- 团队可以把「如何跑测试、如何提交 PR」写成 **Skill / Command**
- Agent 在不同仓库行为可复现，而不是每次靠系统提示词人肉调

详见 [2026 协议栈](protocol-stack-2026.md) 中 Skills / agents.md 一节。

### 3. Hooks 与治理

在工具执行前/后、会话关键节点插入自定义代码，实现：

- 强制 lint / 危险命令拦截
- 审计日志
- 与内部审批系统对接

比「只在 prompt 里写不要 rm -rf」可靠一个数量级（见 [权限控制与沙箱隔离](../10-evaluation-safety/permission-sandbox.md)）。

## 可运行示例（Python）

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Find the failing unit test and fix the root cause.",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Bash"],
        permission_mode="acceptEdits",
        cwd="/path/to/repo",
    ),
):
    print(message)
```

> 以官方 SDK 文档为准核对 API 签名；版本迭代较快。

## 常见故障与排查

| 现象 | 原因 | 处理 |
|---|---|---|
| 循环行为与 CLI 不一致 | SDK/CLI 版本或配置目录不同 | 对齐版本；检查 `.claude` 加载 |
| 权限频繁打断 | `permission_mode` 过严或工具集过宽 | 收窄 allowed_tools；分环境配置 |
| 子 Agent 成本爆炸 | 无并发上限、任务拆分过碎 | 限制 subagent 数；共享事实文件 |
| 想在非 Python/TS 使用 | 官方仅 Py/TS 库 | 以 CLI headless（`-p` + JSON 输出）子进程驱动 |

## 工程含义

1. **框架选型多了一极**：09 章的 LangGraph/CrewAI 仍是「你自己拼图」；Agent SDK / Agents API 是「买整机」
2. **治理前移到配置**：Permissions、Hooks、Skills 应进版本库，和代码一起 review
3. **不要品牌误用**：集成产品不能自称 Claude Code（见官方 branding guidelines）

## 参考资料

- [Agent SDK overview](https://docs.claude.com/en/api/agent-sdk/overview)
- [Claude Agent SDK TypeScript](https://github.com/anthropics/claude-agent-sdk-typescript)
- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [A harness for every task（工程博客）](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code)

## 相关知识点

- [OpenAI Agents API](openai-agents-api.md)
- [模型原生 vs 自建 Harness](model-native-vs-harness.md)
- [OpenAI Agents SDK](../09-frameworks/openai-agents-sdk.md)
- [编程 Agent](../12-applications/coding-agent.md)
