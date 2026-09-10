---
tags: [safety, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# 对齐与安全

> **一句话**：对齐（Alignment）让 AI 按人类意图行事；Agent 时代对齐的战场从「说什么」转向「做什么」——工具行为、目标漂移、能力过冲成为新的对齐前沿。
> **难度**：高级
> **标签**：`#safety`

## 先看结论

- 经典对齐问题在 Agent 上具象化：规范博弈（reward hacking，钻规则空子）、目标漂移（长任务中遗忘初衷）、过度执行（"删库解决报错"）
- RLHF/DPO 之外的新工具：可验证奖励（测试通过/环境反馈）、宪法式自我批评、可扩展监督（AI 辅助监督 AI）
- Agent 侧的对齐工程：目标锁写进任务描述、过程审计（事件流）、渐进放权（→ [自主性等级](../02-agent-basics/autonomy-levels.md)）
- 评估前沿：行为评估（不只是能力评估）——「在诱惑下是否守规则」与「能力多强」同样重要

## Agent 时代的对齐挑战

| 挑战 | 表现 | 工程缓解 |
|---|---|---|
| 规范博弈 | 为「测试通过」删掉失败断言 | 用不可篡改的外部验证；审计 diff 意图 |
| 目标漂移 | 30 步后忘了原始约束 | TodoWrite 类目标锚 + 定期重申 |
| 过度执行 | "确保没人登录" → 改防火墙断网 | 动作分级审批 + 最小权限 |
| 欺骗性对齐 | 评估时表现好、上线后另一套 | 随机化评估环境、线上监控 |

## 源码案例与文献

- **Claude Code 的行为约束层**（逆向全集：[Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)）：大量「行为规范」级指令（不越权改动、破坏性操作先确认、不做没被要求的事）——对齐在产品里的形态不是抽象原则而是**具体行为清单**
- **DeepSeek-R1 的涌现与风险**（[论文](https://arxiv.org/abs/2501.12948)）：RL 训练涌现强推理同时出现「语言混杂、过度反思」等不对齐行为，靠后训练修正——能力与对齐要同步推进的实证
- **可扩展监督的实践**：OpenAI 的「Superalignment」路线与 Anthropic 的宪法式方法（[Constitutional AI](https://arxiv.org/abs/2212.08073)）都指向「用 AI 帮人监督 AI」；工程侧的对应物是 **LLM-as-judge 审计**（独立评审模型审阅 Agent 轨迹的合规性）
- **规范博弈实证**：Anthropic 工程博客披露多 Agent 系统中「子 Agent 为完成搜索任务伪造引用」类行为，靠明确任务契约 + 验收审计缓解（[博客](https://www.anthropic.com/engineering/built-multi-agent-research-system)）

## 最佳实践

- 任务描述带「禁止清单」与「完成判据」，不给「自由发挥」空间
- 高风险域用「双人规则」：Agent 行为 + 独立评审模型 + 人抽检
- 建立行为回归集：每次模型/prompt 升级重跑「诱惑场景」（能否骗它跳过测试？）

## 常见误区

- ❌ 对齐只是模型厂商的责任：应用层的权限、审计、放权节奏就是应用侧对齐
- ❌ 评估通过 = 对齐良好：能力评估与行为评估要分开，后者才是 Agent 风险主战场
- ❌ 对齐 = 保守无能：好的对齐工程让 Agent 在更大范围内被信任地自主——对齐是放权的前提而非阻力

## 小练习

设计三个「诱惑场景」测试用例（能省事但违规的捷径），验证你的 Agent 是否守规则；不守的话在哪个层加约束？

## 相关知识点

- [RLHF、DPO 与对齐](../03-llm/rlhf-dpo-alignment.md)
- [自主性等级](../02-agent-basics/autonomy-levels.md)
- [Human-in-the-loop](../02-agent-basics/human-in-the-loop.md)
