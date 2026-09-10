---
tags: [planning, agent]
type: knowledge
status: published
updated: 2026-09-10
---

# 任务分解

> **一句话**：把「做个电商网站」变成「建骨架 → 写商品模型 → 写购物车 → …」，任务分解是规划的第一步，粒度决定成败。

## 先看结论

- 分解过粗：单步太复杂，模型做不好也验不了；过细：上下文浪费、调度开销大
- 好的子任务三标准：**单一职责、可独立验证、失败可局部回滚**
- 结构化的任务清单（如 TodoWrite）优于散落在对话里：可更新状态、可并发、可审计
- 分解的产物是一张**依赖图**，不是一串文本

## 核心机制

### 1. 分解结果是 DAG

把任务分解写成有向图 $G=(V,E)$：

- 节点 $v\in V$：一个子任务
- 边 $(u,v)\in E$：$v$ 依赖 $u$（$u$ 必须先完成）
- 执行顺序是图的**拓扑序**；没有依赖关系的节点可以并行

这一形式化立刻给出两条工程结论：一是**环意味着死锁**（A 依赖 B、B 依赖 A），分解时必须检查无环；二是**关键路径决定最短完成时间**，优化应优先压缩关键路径上的节点。

### 2. 粒度的代价模型

粒度不是越细越好，因为每一步都有固定开销。设子任务数为 $|V|$，总成本近似：

$$
\text{Cost}\;\approx\;
\underbrace{c_{\text{ctx}}\cdot |V|}_{\text{每步上下文/调度开销}}
+\underbrace{c_{\text{verify}}\cdot |V|}_{\text{每步验证开销}}
+\underbrace{\text{失败重做的代价}}_{\text{粒度越粗，重做越贵}}
$$

- $|V|$ 增大 → 前两项线性上升（每步都要一次模型调用与一次验证）
- 粒度过粗 → 单步失败要重做很多工作，且难以验证

**最优点是「能被独立验证的最小步骤」**：既要小到可以机检验收，又要大到不必为琐碎动作付调度成本。

### 3. 可验证性是硬标准

一个子任务是否合格，判断标准是能否写出**机检的完成判据**：

$$
\text{完成}(v)=\mathbb{1}\big[\text{测试通过} \vee \text{文件存在} \vee \text{查询返回预期}\big]
$$

「看起来差不多」「基本实现」不是判据。这条标准带来一个常被忽略的要求：**验证任务本身（测试、lint、review）应当作为独立子任务进入清单**，而不是隐含在实现步骤里。

## 分解示例

```text
❌ 粗: "实现用户系统"
❌ 细: "1.新建文件user.ts 2.写import 3.定义接口字段id 4.定义字段name …"
✅ 恰当: "1.定义User数据模型与校验 2.实现注册/登录接口 3.写单元测试并跑通 4.更新README"
```

## 工程含义

- **滚动分解**：不要一次分解到底。长任务中后期子任务必然过时——先分解前 3 步，边做边补（计划是活的，允许修改并记录原因）。
- **显式标注依赖与可并行性**：有依赖的排序，无依赖的标注可并行扇出（→ [子目标规划](subgoal-planning.md)）。
- **每个子任务带验收标准**：与子任务一起写下「怎么算完成」，否则执行阶段无法判断进展。
- **分解质量可评估**：把「分解结果」当产物测试——给定任务，检查生成的 DAG 是否无环、是否覆盖全部必要步骤、每个节点是否可验证。

## 源码案例

- **Claude Code 的 TodoWrite**（逆向全集：[Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)）：系统提示词用专门 section 教模型「何时建清单、如何标记 in_progress/completed」，并配合运行时提醒保持清单更新——任务清单不是普通文本，而是**有工具支撑的状态管理**（→ [Agent 状态管理](../02-agent-basics/state-management.md)）
- **DeepSeek Harness 的 plan/goal 包**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：`packages/plan` 与 `packages/goal` 独立成包——计划与目标是一等公民，以插件形式参与 Agent 循环；分解结果进入 append-only 事件流，天然获得「计划变更史」
- **经典参考**：[Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091)（Wang et al., 2023）确立「先规划再逐步求解」的 prompt 范式；[HuggingGPT](https://arxiv.org/abs/2303.17580)（Shen et al., 2023）展示了把任务分解后路由给不同模型执行的结构化形态

## 最佳实践

- 分解时同步标注每个子任务的「验收标准」（测试通过 / 页面可见 / 输出包含 X）
- 有依赖关系的子任务显式排序，无依赖的标注可并行
- 计划是活的：执行中发现认知更新，允许修改清单并记录原因

## 常见误区

- ❌ 一次分解到底：长任务中后期子任务必然过时，要滚动分解
- ❌ 分解后不再验证：每个子任务完成必须过验收，否则错误滚雪球
- ❌ 忽略「验证任务」本身：测试、lint、review 应作为独立子任务进清单
- ❌ 只产出文本清单不建依赖关系：无法判断并行度，也无法检测环
- ❌ 把「实现」拆得极细却把「验证」当附带：验证被省略，分解就失去意义

## 小练习

把「为公司官网写一篇产品博客并发布」分解成 6–8 个子任务，画出依赖 DAG，每个标注机检的验收标准与依赖关系，并指出哪些可并行。

## 参考资料

- [Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning](https://arxiv.org/abs/2305.04091)（Wang et al., 2023）
- [HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face](https://arxiv.org/abs/2303.17580)（Shen et al., 2023）
- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)

## 相关知识点

- [Plan-and-Execute](plan-and-execute.md)
- [子目标规划](subgoal-planning.md)
