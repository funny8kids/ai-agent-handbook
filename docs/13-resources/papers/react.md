---
tags: [agent, prompt, paper]
type: resource
status: published
updated: 2026-09-20
---

# ReAct 论文

{% hint style="info" %}
**一句话**：提出「推理轨迹 + 行动」交替的 Agent 范式，是几乎所有现代 Agent 循环的思想原型。
{% endhint %}

| 属性 | 内容 |
|---|---|
| 类型 | 论文 |
| 链接 | <https://arxiv.org/abs/2210.03629> |
| 来源 | Yao et al., Princeton + Google Brain |
| 发布 | 2022-10（ICLR 2023） |
| 难度 | 进阶 |
| 标签 | `#agent` `#prompt` |

## 推荐理由

- Agent 领域引用量最高的论文之一，「Agent 循环」的学术起点
- 核心实验对比至今有效：纯推理（CoT-only）会幻觉、纯行动（Act-only）缺规划，两者交替最优
- 提供了 HotpotQA、FEVER、ALFWorld、WebShop 四类任务的完整实验，可信度高

## 机制一图看懂

推理与行动交替的循环，以及它赢在何处：

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#EDEEF0","primaryBorderColor":"#475569","primaryTextColor":"#1F2937","secondaryColor":"#D7DADE","tertiaryColor":"#F8F8F9","lineColor":"#9AA2AD","actorBkg":"#F0F1F3","actorBorder":"#475569","actorTextColor":"#1F2937","signalColor":"#7E8896","noteBkgColor":"#DEE0E4","noteBorderColor":"#475569","noteTextColor":"#1F2937","labelBoxBkgColor":"#EDEEF0","labelBoxBorderColor":"#475569"}}}%%
flowchart TD
    Q["任务：如 HotpotQA 多跳问答"] --> R["ReAct 循环"]
    R --> T["Thought：推理下一步该查什么"]
    T --> A["Action：调用检索等外部接口"]
    A --> O["Observation：读回真实结果，抑制幻觉"]
    O -->|"信息不足，继续"| T
    O -->|"信息足够"| F["Final Answer"]
    Q -.->|"对照组"| B["Act-only：跳过推理直接行动"]
    B --> W["缺规划，复杂任务易失败"]
    Q -.-> C["CoT-only：只推理不调工具"]
    C --> H["缺外部信息，容易幻觉"]
```

## 上手建议

1. 先读 Figure 1（一张图看懂 Thought→Action→Observation）
2. 精读第 2 节的方法定义（仅一页）
3. 对照 [感知—规划—行动循环](../../02-agent-basics/perception-planning-action.md) 与 Pi 的 agentLoop 源码看工程化差异

## 相关知识点

- [ReAct](../../04-prompt-reasoning/react.md)
- [什么是 AI Agent](../../02-agent-basics/what-is-agent.md)

