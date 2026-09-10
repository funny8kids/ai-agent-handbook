---
tags: [planning, agent]
type: knowledge
status: published
updated: 2026-09-10
---

# 🗺️ 任务分解

> **一句话**：把「做个电商网站」变成「建骨架 → 写商品模型 → 写购物车 → …」，任务分解是规划的第一步，粒度决定成败。
> **难度**：⭐️ 入门
> **标签**：`#planning`

## 📌 先看结论

- 分解过粗：单步太复杂，模型做不好也验不了；过细：上下文浪费、调度开销大
- 好的子任务三标准：单一职责、可独立验证、失败可局部回滚
- 结构化任务清单（如 TodoWrite）优于散落在对话里：可更新状态、可并发、可审计

## 🖼️ 分解示例

```text
❌ 粗: "实现用户系统"
❌ 细: "1.新建文件user.ts 2.写import 3.定义接口字段id 4.定义字段name …"
✅ 恰当: "1.定义User数据模型与校验 2.实现注册/登录接口 3.写单元测试并跑通 4.更新README"
```

## 📦 源码案例

- **Claude Code 的 TodoWrite**（逆向全集：[Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)）：系统提示词用专门 section 教模型「何时建清单、如何标记 in_progress/completed」，并配合 System Reminder 在上下文里周期提醒「保持清单更新」——任务清单不是普通文本，是**有工具支撑的状态管理**（→ [Agent 状态管理](../02-agent-basics/state-management.md)）
- **DeepSeek Harness 的 plan 包**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：`packages/plan`、`goal` 独立成包——计划与目标是一等公民，以插件形式参与 Agent 循环；任务的分解结果进入 append-only 事件流，天然获得「计划变更史」
- **经典参考**：HuggingGPT / Plan-and-Execute 论文（[arXiv:2305.04091](https://arxiv.org/abs/2305.04091)）确立了「Planner 出计划 → Executor 逐步执行 → Planner 重规划」的结构分解范式

## ✅ 最佳实践

- 分解时同步标注每个子任务的「验收标准」（测试通过/页面可见/输出包含 X）
- 有依赖关系的子任务显式排序，无依赖的标注可并行（→ [子目标规划](subgoal-planning.md)）
- 计划是活的：执行中发现认知更新，允许修改清单并记录原因

## ⚠️ 常见误区

- ❌ 一次分解到底：长任务中后期子任务必然过时，要滚动分解（先分解前 3 步，边做边补）
- ❌ 分解后不再验证：每个子任务完成必须过验收，否则错误滚雪球
- ❌ 忽略「验证任务」本身：测试、lint、review 应作为独立子任务进清单

## 🧪 小练习

把「为公司官网写一篇产品博客并发布」分解成 6–8 个子任务，每个标注验收标准与依赖关系。

## 📚 相关知识点

- [Plan-and-Execute](plan-and-execute.md)
- [子目标规划](subgoal-planning.md)
