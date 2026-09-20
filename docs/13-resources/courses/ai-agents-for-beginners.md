---
tags: [agent, course, resource]
type: resource
status: published
updated: 2026-09-20
---

# AI Agents for Beginners

{% hint style="info" %}
**一句话**：微软出品的 11 课时开源 Agent 入门课：从基础概念到多 Agent、MCP、Agentic RAG，中文翻译完善，入门首选。
{% endhint %}

| 属性 | 内容 |
|---|---|
| 类型 | 课程 |
| 链接 | <https://github.com/microsoft/ai-agents-for-beginners> |
| 来源 | Microsoft |
| 难度 | 入门 |
| 标签 | `#agent` `#course` |

## 推荐理由

- 结构完整：概念 → 框架 → 设计模式 → MCP → RAG → 规划 → 多 Agent，与本书章节结构高度互补
- 每课配视频 + 代码样例 + 延伸阅读；GitHub 5 万+ Star 的社区验证
- 中文社区翻译完善，零基础友好

## 课程结构一图看懂

11 课的主线与本书章节的呼应：

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#EDEEF0","primaryBorderColor":"#475569","primaryTextColor":"#1F2937","secondaryColor":"#D7DADE","tertiaryColor":"#F8F8F9","lineColor":"#9AA2AD","actorBkg":"#F0F1F3","actorBorder":"#475569","actorTextColor":"#1F2937","signalColor":"#7E8896","noteBkgColor":"#DEE0E4","noteBorderColor":"#475569","noteTextColor":"#1F2937","labelBoxBkgColor":"#EDEEF0","labelBoxBorderColor":"#475569"}}}%%
flowchart TD
    L["11 课时主线"] --> A["概念：Agent 基础与应用场景"]
    A --> B["框架与设计模式：工具使用 / ReAct / 规划"]
    B --> C["进阶：MCP、Agentic RAG"]
    C --> D["收束：多 Agent 协作"]
    D --> E["每课配套：视频 + 代码样例 + 延伸阅读"]
    B -.->|"Lesson 1–5 后"| BK["回读本书 02 Agent 基础做概念校准"]
    C -.->|"Lesson 8"| RAG["配合本书 06 记忆与 RAG"]
```

## 上手建议

1. 学完 Lesson 1–5 后回来读本书 [02 Agent 基础](../../02-agent-basics/README.md) 做概念校准
2. Lesson 8（Agentic RAG）配合本书 [06 记忆与 RAG](../../06-memory-rag/README.md) 食用
3. 每课的代码样例跑一遍比看视频收获大

## 相关知识点

- [学习路线](../../00-index/learning-path.md)
- [什么是 AI Agent](../../02-agent-basics/what-is-agent.md)

