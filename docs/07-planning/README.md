---
tags: [planning]
type: index
status: published
updated: 2026-09-20
---

# 07 规划与任务执行

{% hint style="info" %}
**一句话**：会规划才叫「做事」而不是「碰运气」：任务分解、计划-执行分离、子目标管理、工具路由、错误恢复与工作流编排。
{% endhint %}

## 你将学到

- 任务分解的粒度控制：TodoWrite 式任务清单为什么有效
- Plan-and-Execute：先规划后执行 vs 边想边做的取舍
- 子目标与依赖管理：拓扑排序、并行扇出
- 工具选择与路由：工具面太大时怎么选得准
- 错误恢复：重试、降级、回退、换路四板斧
- 工作流编排：什么时候该把「自主」换成「确定性」

## 核心张力

规划系统永远在两极之间找平衡：

```mermaid
flowchart LR
  A["完全预先规划<br/>Plan-and-Execute<br/>✓可控 ✗脆弱"] <-->|"工程光谱"| B["完全动态规划<br/>ReAct 即兴<br/>✓灵活 ✗失控"]
  A <--> C["混合式<br/>动态重规划<br/>生产主流"]
```

## 本站页面

- [任务分解](task-decomposition.md)
- [Plan-and-Execute](plan-and-execute.md)
- [子目标规划](subgoal-planning.md)
- [工具选择与路由](tool-selection-routing.md)
- [错误恢复与重试](error-recovery-retry.md)
- [工作流编排](workflow-orchestration.md)

## 读完能做到

- [ ] 把「为公司官网写一篇产品博客并发布」分解成 6–8 个带机检验收标准的子任务，画出无环 DAG 并标出可并行项
- [ ] 解释 Plan-and-Execute 比 ReAct 更省 token 的结构性原因（ReAct ≈ O(T²) vs 执行步只用局部上下文），并说清何时该触发 replan
- [ ] 给「旧库→新库」数据迁移标出关键路径、哪个子目标失败可跳过、哪个失败必须中止
- [ ] 为 80 个工具设计路由方案（分组 / 延迟加载 / 语义路由），并解释「正确工具没进候选，模型再强也选不对」
- [ ] 按瞬时 / 参数 / 持续 / 能力边界 / 不可逆五类错误，给「并发抓 1000 网页」设计重试与降级，写出退避参数与三重熔断

## 章末自测

1. **回忆**：好子任务的三条标准是什么？为什么「验证任务」（测试、lint、review）本身要作为独立子任务进清单？（提示：见 task-decomposition.md）
2. **应用**：「排查一个未定位的线上 bug」该用 Plan-and-Execute 还是 ReAct？为什么？（提示：见 plan-and-execute.md、workflow-orchestration.md）
3. **判断**：用「下一步可预知吗 × 需要运行时信息吗」两问，判断一个环节该用固定工作流还是自主 Agent，并给一个该用固定流程的例子。（提示：见 workflow-orchestration.md）

