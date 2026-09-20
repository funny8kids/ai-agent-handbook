---
tags: [evaluation, safety]
type: index
status: published
updated: 2026-09-20
---

# 10 评估、安全与对齐

{% hint style="info" %}
**一句话**：Agent 不评估 = 裸奔上线；不设防 = 等着被提示注入。本章覆盖评估指标、基准测试、幻觉治理、攻击面防御与对齐安全。
{% endhint %}

![Agent 评估四层指标](../.gitbook/assets/10-eval-layers.svg)

![2026 评估版图](../.gitbook/assets/10-eval-landscape-2026.svg)

> **2026 更新**：基准代际已到 Terminal-Bench 4.0 / OSWorld 2.0 / τ² / Agents' Last Exam，见 [评估 2026](../18-frontier-2026/eval-2026.md)；真实越权事故与 misalignment monitoring 见 [2026 安全现实](safety-incidents-2026.md)。

## 你将学到

- Agent 评估的分层指标：任务成功率、轨迹质量、成本延迟
- 主流基准怎么读：SWE-bench / GAIA / WebArena，以及 **2026 代际**（Terminal-Bench 4.0、OSWorld 2.0）
- 三大安全攻击面：幻觉、提示注入、越狱——各自原理与防御
- 权限沙箱、数据隐私、对齐与可解释性的工程落点
- **2026 安全现实**：能力阈值、确认策略、企业防护与监控

## 全章地图

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#FCE9E9","primaryBorderColor":"#DC2626","primaryTextColor":"#1F2937","secondaryColor":"#F7CFCF","tertiaryColor":"#FEF6F6","lineColor":"#EC8888","actorBkg":"#FCEEEE","actorBorder":"#DC2626","actorTextColor":"#1F2937","signalColor":"#E76767","noteBkgColor":"#F9D8D8","noteBorderColor":"#DC2626","noteTextColor":"#1F2937","labelBoxBkgColor":"#FCE9E9","labelBoxBorderColor":"#DC2626"}}}%%
flowchart LR
  A[评估] --> A1[指标] --> A2[基准]
  B[安全] --> B1[幻觉] --> B2[提示注入] --> B3[越狱]
  C[治理] --> C1[权限沙箱] --> C2[隐私] --> C3[对齐] --> C4[可解释]
```

## 一条主线

评估驱动一切：**没有评估集，安全加固、prompt 优化、模型选型全靠感觉**。建议任何 Agent 项目第一周就建 20 个测试用例（→ [持续评估](../11-engineering/continuous-evaluation.md)）。

## 本站页面

- [Agent 评估指标](evaluation-metrics.md)
- [基准测试总览](benchmarks.md)
- [AgentBench、WebArena、SWE-bench、GAIA、ToolBench](agentbench-webarena-swebench-gaia-toolbench.md)
- [幻觉问题](hallucination.md)
- [提示注入](prompt-injection.md)
- [越狱攻击](jailbreak.md)
- [权限控制与沙箱隔离](permission-sandbox.md)
- [数据隐私](data-privacy.md)
- [对齐与安全](alignment-safety.md)
- [可解释性](explainability.md)
- [2026 安全现实](safety-incidents-2026.md)
- （前沿）[评估 2026](../18-frontier-2026/eval-2026.md)

## 读完能做到

- [ ] 说出 Agent 评估四层（结果 / 轨迹 / 成本延迟 / 鲁棒），并解释为什么「能程序化验证的绝不交给 LLM judge」
- [ ] 读榜单时说清 SWE-bench / GAIA / WebArena 各考什么、怎么算分，以及 pass@1 与 pass@10 为什么不能混着比
- [ ] 用「可验证事实源 + 让模型敢说不知道」设计一条治幻觉清单（枚举 / ID / 日期一律来自工具返回，禁止模型生成）
- [ ] 设计一个注入红队用例，评估三层防线（结构隔离 / 权限最小化 / 审批）各能否拦住，并给出 ASR 估计
- [ ] 为一个财务 Agent 写权限策略表 YAML，按可逆性分级审批，说明选了哪几层沙箱、每层压住什么风险

## 章末自测

1. **回忆**：为什么说「权限最小化的收益是确定的，而 prompt 防御的收益是概率的」？（提示：见 permission-sandbox.md、prompt-injection.md）
2. **应用**：给面向未成年人的教育 Agent 设计越狱防线：输入 / 模型 / 输出 / 监控四层各选一种，并说明为什么还要同时盯 over-refusal。（提示：见 jailbreak.md）
3. **判断**：某模型 SWE-bench 分很高，老板说直接上我们的私有代码库。用「模型 + harness = Agent」和「同一模型不同 harness 成绩可差 20%+」评价这个判断。（提示：见 benchmarks.md）

