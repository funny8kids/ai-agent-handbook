---
tags: [application]
type: knowledge
status: published
updated: 2026-09-10
---

# 💼 数据分析 Agent

> **一句话**：数据分析 Agent = 会写 SQL/Python、会看数据、会画图并给出结论的「初级分析师」；成败关键在「数值零幻觉」与「结论可复现」。
> **难度**：⭐️ 入门
> **标签**：`#application`

## 📌 先看结论

- 标准管线：理解问题 → 探查 schema → 写 SQL/代码执行 → 校验结果 → 可视化 → 结论+口径说明
- 铁律：数字必须来自工具执行（SQL 返回、代码输出），禁止模型「口算」——分析场景的幻觉是直接的业务事故
- 语义层（metrics layer）是规模化关键：指标口径统一定义，避免「每个会话算出来的 GMV 不一样」
- 代码解释器（Code Interpreter）模式：让模型写 Python 在沙箱执行，比只靠 SQL 灵活得多

## 🖼️ 管线图

```mermaid
flowchart LR
  Q[业务问题] --> S[语义层/表结构<br/>注入上下文]
  S --> G[生成 SQL/Python]
  G --> X[沙箱执行]
  X -- 报错 --> G2[错误回填自修正]
  G2 --> G
  X --> V{数值合理?<br/>抽样校验}
  V -- 否 --> S2[重写口径]
  S2 --> G
  V -- 是 --> C[可视化+结论+口径]
```

## 📦 源码案例

- **DeepSeek Harness 的 PTC 模式**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：程序化工具调用让模型把「查库 → 清洗 → 统计 → 画图」写成一段 Python 一次执行——数据管线类任务天然适合 PTC：多轮交互变单段代码，中间结果不出沙箱
- **AutoGen 的数据分析 duo**（[microsoft/agent-framework](https://github.com/microsoft/agent-framework)）：经典用法是「分析师 Agent 写代码 + Proxy Agent 沙箱执行」，论文里的数据任务案例多基于此——代码执行-报错-修正循环的教科书
- **Code Interpreter 模式**：OpenAI Advanced Data Analysis 与开源实现（如 [E2B](https://github.com/e2b-dev/E2B) 沙箱）——「执行环境即产品」：文件上传、依赖预装、超时控制都是产品能力
- **语义层工具**：dbt semantic layer / Cube（[GitHub](https://github.com/cube-js/cube)）——把「GMV 怎么算」从 prompt 挪到指标定义，Agent 引用指标而非拼 SQL 口径

## ✅ 落地要点

- Schema 注入精简：几百张表全塞上下文必爆，按问题路由相关表 + 列描述（→ [工具选择与路由](../07-planning/tool-selection-routing.md)）
- 数值校验自动化：总量对账（各维度之和 = 总计）、异常值检测（环比 >10 倍先怀疑）
- 结论强制三件套：数字 + 口径（SQL/代码）+ 不确定性说明

## ⚠️ 常见误区

- ❌ 模型直接回答数据问题：训练数据里没有你的业务数据，「去年营收」它只能编
- ❌ SQL 报错就放弃：报错回填重试（列名错了、类型不匹配）通常 1–2 次内自愈，这是该场景最成熟的自我修正循环
- ❌ 忽略数据新鲜度：Agent 不知道表多久更新一次，口径里必须带数据时间戳

## 🧪 小练习

给 Agent 接一个样例数据库，问「上个月销量 Top5 的产品」：观察它的 SQL 生成-报错-修正过程，记录哪个环节最容易产生错误结论。

## 📚 相关知识点

- [浏览器、代码、文件系统工具](../05-tool-protocol/browser-code-filesystem-tools.md)
- [幻觉问题](../10-evaluation-safety/hallucination.md)
