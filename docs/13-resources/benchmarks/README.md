---
tags: [resource, evaluation]
type: index
status: published
updated: 2026-09-10
---

# 🔗 基准测试

> Agent 能力基准的卡片与索引。基准怎么读、怎么用，见 [基准测试总览](../../10-evaluation-safety/benchmarks.md)。

## 收录列表

| 基准 | 考什么 | 卡片 |
|---|---|---|
| SWE-bench | 真实 issue 修复 | [swe-bench.md](swe-bench.md) |
| GAIA | 通用助理任务 | [gaia.md](gaia.md) |
| WebArena | 真实网站长程任务 | [webarena.md](webarena.md) |

## 延伸速查（未建卡）

| 基准 | 考什么 | 链接 |
|---|---|---|
| AgentBench | 八场景综合 | <https://github.com/THUDM/AgentBench> |
| ToolBench / BFCL | 工具调用 | <https://gorilla.cs.berkeley.edu/leaderboard.html> |
| Terminal-Bench | 终端操作 | <https://www.tbench.ai/> |
| OSWorld | 真实桌面环境 | <https://os-world.github.io/> |
| τ-bench | 客服域工具+策略遵守 | <https://github.com/sierra-research/tau-bench> |

## ⚠️ 使用基准的三条纪律

1. 分清「模型成绩」与「harness 成绩」——同一模型换 harness 差 20%+（→ [编程 Agent](../../12-applications/coding-agent.md)）
2. 借协议自建领域内测集，榜单分数不等于你的场景表现
3. 关注数据去污染声明与成本维度
