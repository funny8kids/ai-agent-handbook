---
tags: [multi-agent]
type: knowledge
status: published
updated: 2026-09-22
---

# 角色分配

{% hint style="info" %}
**一句话**：给每个 Agent 一个明确的角色（角色 = 专属 system prompt + 工具面 + 产出格式），角色越具体，协作越有序。
  **难度**：入门
  **标签**：`#multi-agent`
{% endhint %}

## 先看结论

- 角色 ≠ 起个名字：角色 = 专属指令 + 专属工具集 + 专属验收标准三件套
- 有效角色设计回答三个问题：它看什么（上下文）、能做什么（工具）、交付什么（格式）
- 角色数量最小化：先试「规划者 + 执行者」二元结构，再按需增加
- 「评审」「验证」类角色性价比最高：独立视角是质量杠杆
- 角色能不能配合，取决于**交接契约**是否允许它诚实说「我做不下去」

## 角色设计模板

| 要素 | 规划者 Planner | 执行者 Worker | 评审者 Reviewer |
|---|---|---|---|
| 上下文 | 全局目标+资源清单 | 单个子任务+所需材料 | 产出+验收标准 |
| 工具 | 只读（搜索、读取） | 全量（写入、执行） | 只读 + 测试工具 |
| 产出 | 任务清单（JSON） | 完成的工件 | 通过/驳回+理由 |

## 最小三角色的协作流

角色间的箭头就是「交接契约」：产出格式提前定死，下游才能稳定消费。注意评审者只有只读与测试工具——它能挑问题，但不能替执行者改代码：

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#FDEEE7","primaryBorderColor":"#EA580C","primaryTextColor":"#1F2937","secondaryColor":"#FADACA","tertiaryColor":"#FEF8F5","lineColor":"#F3A379","actorBkg":"#FDF2EC","actorBorder":"#EA580C","actorTextColor":"#1F2937","signalColor":"#F08A55","noteBkgColor":"#FBE1D3","noteBorderColor":"#EA580C","noteTextColor":"#1F2937","labelBoxBkgColor":"#FDEEE7","labelBoxBorderColor":"#EA580C"}}}%%
flowchart LR
    P["规划者 Planner<br/>只读工具"] -->|"任务清单"| W["执行者 Worker<br/>全量工具，只做分到的子任务"]
    W -->|"工件"| R["评审者 Reviewer<br/>只读 + 测试工具"]
    R -->|"驳回：附理由"| W
    R -->|"通过"| O["最终交付"]
```

## 交接契约：把「角色间的话」写成可校验格式

协作崩掉的地方极少在「模型不聪明」，而在上游产出的字段下游读不到。契约要包含三段：必填字段、失败时说什么、下游能否据此重试。

```json
{
  "$id": "worker-artifact-v1",
  "required": ["task_id", "status", "changes", "evidence", "open_risks"],
  "properties": {
    "status":      { "enum": ["done", "blocked", "partial"] },
    "changes":     { "type": "array", "items": { "type": "string" } },
    "evidence":    { "type": "array", "description": "测试输出/日志/截图路径" },
    "open_risks":  { "type": "array" }
  }
}
```

```python
def consume(artifact, schema):
    errs = validate(artifact, schema)
    if errs: return send_back(worker, kind="contract_violation", errs=errs)
    if artifact["status"] == "blocked":       # 合法产出，但不是完成
        return escalate(planner, artifact["open_risks"])
    return review(artifact)                    # 交给只读的评审者
```

要点：**`blocked` 是合法状态**，不是错误。没有这一档，执行者会用假装完成来摆脱困境——这是多 Agent 系统最常见的失真模式。

## 什么时候该加一个角色

按顺序问，问到「是」才拆：

1. 是否需要**互斥的工具面**（只读 vs 可写）？→ 拆，这是最硬的理由
2. 是否需要**不同模型或不同 effort 档**？→ 拆（评审用强模型、抽取用便宜模型）
3. 上下文是否会**互相污染**（长检索记录压住判断）？→ 拆，或用子 Agent 隔离
4. 只是「听起来更专业」？→ 不拆，改一条 system prompt 就够

设 $$k$$ 个角色，交接边数约为 $$O(k^2)$$，而能力增益很快饱和——这就是「先试二元结构」的原因。

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

## 参考资料

- [CrewAI（role / goal / backstory 三元组的实现）](https://github.com/crewAIInc/crewAI)
- [MetaGPT 论文（把人类 SOP 编码成角色分工）](https://arxiv.org/abs/2308.00352)
- [AutoGen（以对话为骨架的多 Agent 角色编排）](https://github.com/microsoft/autogen)
- [Claude Code 系统提示词全集（子 Agent 角色描述的实际写法）](https://github.com/Piebald-AI/claude-code-system-prompts)

## 相关知识点

- [多 Agent 协作](multi-agent-collaboration.md)
- [监督者模式](supervisor-pattern.md)

