---
tags: [multi-agent]
type: knowledge
status: published
updated: 2026-09-10
---

# 角色分配

> **一句话**：给每个 Agent 一个明确的角色（角色 = 专属 system prompt + 工具面 + 产出格式），角色越具体，协作越有序。
> **难度**：入门
> **标签**：`#multi-agent`

## 先看结论

- 角色 ≠ 起个名字：角色 = 专属指令 + 专属工具集 + 专属验收标准三件套
- 有效角色设计回答三个问题：它看什么（上下文）、能做什么（工具）、交付什么（格式）
- 角色数量最小化：先试「规划者 + 执行者」二元结构，再按需增加
- 「评审」「验证」类角色性价比最高：独立视角是质量杠杆

## 角色设计模板

| 要素 | 规划者 Planner | 执行者 Worker | 评审者 Reviewer |
|---|---|---|---|
| 上下文 | 全局目标+资源清单 | 单个子任务+所需材料 | 产出+验收标准 |
| 工具 | 只读（搜索、读取） | 全量（写入、执行） | 只读 + 测试工具 |
| 产出 | 任务清单（JSON） | 完成的工件 | 通过/驳回+理由 |

## 源码案例

- **Claude Code 的内置角色族**（逆向全集：[Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)）：Plan Agent（只读探索、产出计划）、Explore Agent（大范围检索）、General Purpose Agent（"Do what has been asked; nothing more, nothing less"）——每个角色的 prompt、工具面、行为约束三位一体；还支持用户自定义子 Agent（.claude/agents/ 目录），角色成了可分发的「软件包」
- **CrewAI 的角色三要素**（[GitHub](https://github.com/crewAIInc/crewAI)）：`role`（职位）+ `goal`（目标）+ `backstory`（背景故事）——把角色写成「人物小传」，实证显示 backstory 能稳定引导语气与取舍，是轻量角色化的流行做法
- **DeepSeek Harness 的 Agent preset**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：`packages/preset/agent-presets` 预置不同 Agent 配置（工具面、模型、提示词分区）——角色 = 一份可组合的 preset 声明

## 最佳实践

- 角色 prompt 里写「禁止事项」比「职责清单」更能防跑偏
- 角色间交接要定义「契约」：产出格式（JSON schema）+ 必含字段，下游才能稳定消费
- 评审角色与生成角色用不同模型实例（甚至不同模型），避免同一盲区

## 常见误区

- ❌ 角色扮演病：「你是世界顶级 CEO」这类空泛头衔没有信息量，等于没设角色
- ❌ 角色越多越好：每个角色增加通信与调度成本，能力面可以靠工具增加，不必靠角色数
- ❌ 角色无工具差异化：给评审者写文件的工具，它就开始自己改而不是提意见

## 小练习

为「博客自动生产」设计三角色（调研/写作/事实核查）：每个角色的工具面、产出 JSON 格式、禁止事项各写两条。

## 相关知识点

- [多 Agent 协作](multi-agent-collaboration.md)
- [监督者模式](supervisor-pattern.md)
