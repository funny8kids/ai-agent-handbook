---
tags: [evaluation]
type: knowledge
status: published
updated: 2026-09-10
---

# 📊 基准测试总览

> **一句话**：基准测试是 Agent 能力的「标准化考场」——看懂每个基准考什么、怎么算分、有什么局限，才不会被榜单牵着走。
> **难度**：⭐️ 入门
> **标签**：`#evaluation`

## 📌 先看结论

- 基准三要素：任务集、执行环境、评分协议；差异全在这三件事
- Agent 基准两大类：能力型（抽象任务）与环境型（真实/模拟环境交互）
- 榜单分数 ≠ 你的场景表现：任务分布、工具可用性、上下文构造都会造成巨大差异
- 最佳用法：借协议自建领域内测集（→ [Agent 评估指标](evaluation-metrics.md)）

## 🧩 主流基准一览

| 基准 | 考什么 | 环境 | 深入页面 |
|---|---|---|---|
| SWE-bench / Verified | 真实 GitHub issue 修复 | 真实代码库+测试 | [详页](agentbench-webarena-swebench-gaia-toolbench.md) |
| GAIA | 通用助理任务（多步推理+工具） | 受控工具环境 | 同上 |
| WebArena | 真实网站长程任务 | 自托管网站沙箱 | 同上 |
| AgentBench | 八场景综合能力 | 多环境 | 同上 |
| ToolBench / BFCL | 工具调用与选择 | API 沙箱 | 同上 |
| Terminal-Bench / OSWorld | 终端/桌面操作 | 真实 OS 环境 | — |
| τ-bench | 工具+用户模拟+策略遵守 | 客服域 | — |

## 🍜 生活类比

榜单像「驾校科目考试」：SWE-bench 是「给你一辆真车去修真路」，GAIA 是「给地图让你送三件快递」，WebArena 是「在模拟城市里完成一天的差事」——驾照高分不等于能开你所在城市的晚高峰。

## ⚠️ 常见误区

- ❌ 刷榜即能力：SWE-bench 高分模型在你的私有代码库上可能水土不服（上下文构造、内部工具链差异）
- ❌ 忽略 harness 差异：同一模型不同 harness 成绩可差 20%+——Claude Code、OpenHands、Pi 跑同一基准结果不同，**模型 + harness = Agent**（这正是 DeepSeek 开源 harness 的语境）
- ❌ 数据污染：基准题目混进训练数据，分数虚高；看基准要查去重声明

## 🧪 小练习

你的 Agent 是「内部 IT 工单处理」。上述哪个基准的协议最适合改造为你的内测集？借用它的什么评分设计？

## 📚 相关知识点

- [Agent 评估指标](evaluation-metrics.md)
- [基准测试资源](../13-resources/benchmarks/README.md)
