---
tags: [application]
type: index
status: published
updated: 2026-09-10
---

# 12 应用案例

> **一句话**：Agent 落地的难度排序大致是：编程 < 数据分析 < 客服 < 研究 < 行业关键业务——验证手段越客观，Agent 越早可用。本章逐场景拆解模式、代表项目与落地要点。

## 场景地图

| 场景 | 成熟度 | 客观验证 | 代表项目/案例 |
|---|---|---|---|
| [编程 Agent](coding-agent.md) | 高 | 测试通过 | Claude Code、Pi、DeepSeek Harness、OpenHands |
| [数据分析](data-analysis-agent.md) | 高 | SQL/图表正确性 | 各家 Notebook Agent |
| [浏览器自动化](browser-automation.md) | 中 | 任务状态 | Playwright MCP、browser-use |
| [客服 Agent](customer-service-agent.md) | 中 | 解决率人工评 | 分诊+知识库模式 |
| [企业知识库](enterprise-knowledge-base.md) | 高 | 引用准确率 | RAG 全家桶 |
| [研究 Agent](research-agent.md) | 中 | 事实核查 | Anthropic 多 Agent 研究系统 |
| [个人助理](personal-assistant.md) | 中 | 用户满意度 | 各家语音助手 |
| [通用 Agent 产品](general-agent-products.md) | 中高 | 验收清单 | ChatGPT Work / Cowork / 浏览器代办 |
| [实时语音 Agent](voice-agent.md) | 中 | 听感与打断 | GPT-Live-1 等实时 API |
| [RPA](rpa.md) | 中 | 流程完成率 | UI 自动化 + LLM |
| [教育 Agent](education-agent.md) | 中 | 学习效果评估 | 苏格拉底式辅导 |
| [游戏 Agent](game-agent.md) | 早期 | 胜率/行为分 | NPC、自对弈 |
| [行业 Agent](industry-agents.md) | 早期 | 合规+准确率 | 医疗/金融/法律 |

## 阅读建议

- 找「我能抄的作业」：每个场景页都有「可复用的模式」小节
- 编程 Agent 页是全书案例密度最高的一页：**Claude Code、Pi、DeepSeek Harness 三大 harness 的横向深拆**，读懂它就读懂了 Agent 工程的当前形态
- 2026 产品面看 [通用 Agent 产品](general-agent-products.md) 与 [18 前沿章](../18-frontier-2026/README.md)
