---
tags: [tooling]
type: index
status: published
updated: 2026-09-22
---

# 05 工具调用与协议

{% hint style="info" %}
**一句话**：工具是 Agent 的手脚，协议是手脚的接法。本章从 Function Calling 原理讲到 MCP/A2A 两大协议，再到权限、沙箱与 Computer Use。
{% endhint %}

![Function Calling 完整链路](../.gitbook/assets/05-tool-calling.svg)

*《图：编号 1→6 里模型只出现在 2 和 6，中间三步全在你的代码里——权限、沙箱、超时都不由模型决定》*
## 你将学到

- Function Calling 的完整链路：schema 注册 → 模型决策 → 参数解析 → 执行回填
- MCP 为什么被称为「AI 的 USB-C」，以及 Server/Client 架构
- A2A：跨 Agent 的协作协议，与 MCP 如何互补
- 权限模型与沙箱：DeepSeek Harness 的执行流水线、Claude Code 的审批层
- Computer Use：截图 → 定位 → 操作的 GUI 自动化循环
- **2026 协议栈补全**：AG-UI、agents.md / Skills 与 MCP/A2A 的分层，见 [2026 协议栈](../18-frontier-2026/protocol-stack-2026.md)

## 全章地图

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#E7F4F3","primaryBorderColor":"#0D9488","primaryTextColor":"#1F2937","secondaryColor":"#CAE7E5","tertiaryColor":"#F5FBFA","lineColor":"#7AC4BE","actorBkg":"#ECF6F5","actorBorder":"#0D9488","actorTextColor":"#1F2937","signalColor":"#56B4AC","noteBkgColor":"#D3ECEA","noteBorderColor":"#0D9488","noteTextColor":"#1F2937","labelBoxBkgColor":"#E7F4F3","labelBoxBorderColor":"#0D9488"}}}%%
flowchart TD
  A[模型层: Function Calling] --> B[生态层: MCP 工具接入]
  A --> C[Agent 层: Tool Use 策略]
  B --> D[跨 Agent: A2A]
  C --> E[治理: 权限与沙箱]
  E --> F[前沿: Computer Use]
```

*《图：全章只有模型层分出两条边：往生态走是 MCP 接工具、再经 A2A 跨 Agent；往 Agent 走是 Tool Use 策略，必须先过权限与沙箱这一关，才轮得到 Computer Use》*

## 本站页面

- [Function Calling](function-calling.md)
- [Tool Use](tool-use.md)
- [MCP：Model Context Protocol](mcp.md)
- [A2A：Agent-to-Agent](a2a.md)
- [工具权限与沙箱](tool-permission-sandbox.md)
- [浏览器、代码、文件系统工具](browser-code-filesystem-tools.md)
- [Computer Use / Browser Use](computer-use-browser-use.md)

## 读完能做到

- [ ] 画出 Function Calling 的四步往返（给 schema→模型出调用→你执行→回填），并说清「模型不真的执行函数，只出调用意图」
- [ ] 按原子性/无歧义/幂等友好/返回可消化四原则，把一个「15 操作挤在一个大 JSON 参数」的工具拆成原子工具集，标出哪些非幂等
- [ ] 说清 MCP 如何把 M×N 集成降成 M+N，以及 Tools / Resources / Prompts 三原语各管什么
- [ ] 区分 MCP 与 A2A 的分工（工具变手脚 vs Agent 变同事），点出 Agent Card / Task / Message 三构件的用武之地
- [ ] 为「分析上传的 CSV 并生成图表」定执行环境：代码放哪一层沙箱、网络策略是什么、哪些动作要人审

## 章末自测

1. **回忆**：为什么工具 schema 会「每一轮」都占用上下文？这对工具数量和选型意味着什么？（提示：见 function-calling.md、tool-use.md）
2. **应用**：「每月登录网银下载账单并记账」怎么拆成 API + GUI + HITL 的混合方案？哪些步骤必须走 GUI？（提示：见 computer-use-browser-use.md）
3. **判断**：「给 Agent 尽量多塞工具以增强能力」——用工具面治理（选择准确率随工具数下降）评价这个主张。（提示：见 tool-use.md、tool-permission-sandbox.md）

## 本章术语速查

协议和工具的名词最容易混，照页面出场顺序理了一遍，每条只讲分工不讲实现。

| 英文术语 | 中文 | 白话一句话 |
|---|---|---|
| Function Calling | 函数调用 | 给 schema→模型出调用意图→你执行→回填结果的四步往返：模型从头到尾没碰过地面 |
| Schema | 工具描述 | 参数结构加一句说明，既是工具说明书又是隐形路由器，而且每一轮都在吃上下文 |
| Tool Use | 工具使用 | 每步挑哪个工具、怎么组合是门策略学；原子、无歧义、幂等友好、返回可消化是四条设计底线 |
| Idempotency | 幂等 | 跑一遍和跑两遍结果一样；对转账这种非幂等操作，重试就等于重复扣款 |
| Model Context Protocol (MCP) | 模型上下文协议 | 号称「AI 的 USB-C」：把 M 个应用 × N 个工具的接线灾难压成 M+N |
| JSON-RPC 2.0 | （消息格式，通用译名） | MCP 传话用的报文规矩，连上先握手协商能力，再开始正经通信 |
| Tools / Resources / Prompts | MCP 三大原语 | Server 能供的三样货：工具用来动手，资源用来读数据，Prompts 是现成的提示模板 |
| Agent-to-Agent (A2A) | Agent 互通协议 | MCP 把工具变手脚，A2A 把 Agent 变同事：跨厂商地发现、对话、委派任务 |
| Agent Card | 能力名片 | 放在 `/.well-known/agent-card.json` 的自我介绍，先查明对方能干啥再下单，不必读源码 |
| Sandbox | 沙箱 | 跑不可信代码的笼子：隔离强度有梯度，图的就是「被骗了伤害也有上界」 |
| Prompt Injection | 提示注入 | 藏在网页、工具 description 里的「忽略之前的指令」，工具链的头号攻击面 |
| Computer Use | 电脑操作 | 没有 API 时让模型看截图点 GUI：截图→定位→点击，坐标会漂、按平方烧 token，当兜底用 |

