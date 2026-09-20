---
tags: [frontier, models, agents, 2026]
type: index
status: published
updated: 2026-09-20
---

# 本章导读：2026 前沿

{% hint style="info" %}
**一句话**：2026 年的竞争焦点已从「单模型分数」转向「模型 + 托管 harness + 沙箱 + 企业治理」——本章对齐 2026-09 的真实产品面。
{% endhint %}

## 为什么要单独开这一章

01–17 章讲的是**原理与工程骨架**（循环、协议、记忆、评估、基础设施）。这些骨架稳定，但**模型名、产品名、基准代际**每季度都在换。把易变的前沿内容集中在本章，正文知识页只需链接过来，不必整本追改。

写这一章时（2026-09-12）刚发生的事：

| 时间 | 事件 | 对 Agent 工程的含义 |
|---|---|---|
| 2026-07-24 | Claude Opus 5 | 长时程 Agent 的 Opus 档 |
| 2026-08-27 | Anthropic Model Hardware Standard 研究预览 | Agent 安全操作实体设备的共享规范 |
| 2026-09-01 | Claude Fable 5.1 / Mythos 5.1 | 编码与知识工作新前沿；缓存读降价 |
| 2026-09-09 | **GPT-6 Astra** | computer use / 浏览 / 科研 / 网安 SOTA |
| 2026-09-10 | **OpenAI Agents API** 公测 | 托管 Codex harness：压缩、tool search、子 Agent |
| 2026-09-10 | GPT-Live-1 API | 实时语音 Agent 运行时 |

## 本章地图

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#F0EAFB","primaryBorderColor":"#6D28D9","primaryTextColor":"#1F2937","secondaryColor":"#DFD0F7","tertiaryColor":"#F9F6FD","lineColor":"#AF89EA","actorBkg":"#F3EEFC","actorBorder":"#6D28D9","actorTextColor":"#1F2937","signalColor":"#9969E4","noteBkgColor":"#E5D8F8","noteBorderColor":"#6D28D9","noteTextColor":"#1F2937","labelBoxBkgColor":"#F0EAFB","labelBoxBorderColor":"#6D28D9"}}}%%
flowchart TB
  A[18 前沿] --> B[模型：GPT-6 Astra<br/>Claude Fable/Opus]
  A --> C[运行时：Agents API<br/>Claude Agent SDK]
  A --> D[分类学：模型原生 vs 自建 harness]
  A --> E[产品：通用 Agent / 语音 Agent]
  A --> F[协议栈：MCP + A2A + AG-UI<br/>+ agents.md / Skills]
```

| 页面 | 读完你能 |
|---|---|
| [2026 前沿模型地图](frontier-models-2026.md) | 说清 Astra / Fable 5.1 / Opus 5 各自强在哪、价格与安全档位 |
| [OpenAI Agents API](openai-agents-api.md) | 用一次 API call 起托管 Agent，并理解压缩 / tool search / 子 Agent |
| [Claude Agent SDK](claude-agent-sdk.md) | 分清 Agent SDK / CLI / Client SDK / Managed Agents |
| [模型原生 vs 自建 Harness](model-native-vs-harness.md) | 判断你的场景该买托管 harness 还是自己写循环 |
| [通用 Agent 产品](../12-applications/general-agent-products.md) | 看懂 Manus 类「通用助理」与编程 Agent 的差异 |
| [实时语音 Agent](../12-applications/voice-agent.md) | 理解语音 Agent 的延迟预算与工具打断模型 |
| [2026 协议栈](protocol-stack-2026.md) | 把 MCP / A2A / AG-UI / agents.md / Skills 放进同一张图 |

## 与旧章的关系

- 模型原理仍在 [03 LLM 基础](../03-llm/README.md)
- 工具协议主体仍在 [05 工具调用与协议](../05-tool-protocol/README.md)
- 框架对比仍在 [09 框架与生态](../09-frameworks/README.md)
- 评估方法仍在 [10 评估、安全与对齐](../10-evaluation-safety/README.md)，**2026 基准代际**见本章 [评估 2026](eval-2026.md) 与第 10 章更新页

## 参考资料

- [GPT-6 Astra](https://openai.com/index/gpt-6-astra/)（OpenAI, 2026-09-09）
- [Introducing the Agents API](https://openai.com/index/introducing-the-agents-api/)（OpenAI, 2026-09-10）
- [Claude Fable 5.1 and Mythos 5.1](https://www.anthropic.com/claude-fable-and-mythos-5-1)（Anthropic, 2026-09）
- [Claude Agent SDK overview](https://docs.claude.com/en/api/agent-sdk/overview)
- [Terminal-Bench 4.0](https://www.tbench.ai/)

## 读完能做到

- [ ] 说清 Astra / Fable 5.1 / Opus 5 各自强在哪个场景，以及 Fable 与 Mythos 的防护档位差别
- [ ] 看到任何 2026 榜单数字，先问五件事：任务集版本、harness、effort、防护是否开启、成本
- [ ] 用「循环是否产品差异化」的决策流程，判断自己的场景该买托管 harness 还是自己写循环，并说出各自的代价
- [ ] 分清 Agent SDK / CLI / Client SDK / Managed Agents 四种形态的边界，说明为什么 SDK ≠ 再包一层 Messages API
- [ ] 把 MCP / A2A / AG-UI / agents.md 放进同一张协议栈图的四层，各说一句解决什么问题

## 章末自测

1. **回忆**：2026 协议栈的四个层分别是什么协议、各解决什么？（提示：见 protocol-stack-2026.md）
2. **应用**：一家创业公司要在两周内上线编码助手，无特殊合规要求。按本章决策流程该选托管 harness 还是自研循环？主要代价是什么？（提示：见 model-native-vs-harness.md）
3. **判断**：有人说「Agents API 不过是 chat.completions 套一层壳，不值得用」。按本章对托管 harness 的定义，这句话漏掉了哪些开箱能力？（提示：见 openai-agents-api.md）

