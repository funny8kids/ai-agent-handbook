---
tags: [prompt, basics]
type: knowledge
status: published
updated: 2026-09-10
---

# Prompt Engineering

> **一句话**：Prompt Engineering 是给「概率机器」写需求文档——角色、任务、约束、示例、输出格式五要素写清楚，输出质量立竿见影。
> **难度**：入门
> **标签**：`#prompt`

## 先看结论

- 五要素：角色（你是谁）、任务（做什么）、约束（不许做什么）、示例（照这个样子）、格式（输出长什么样）
- 指令放前、参考材料放中、指令尾部重申一次（对抗 lost-in-the-middle）
- 与其堆技巧，不如给例子：2–5 个 few-shot 示例是最稳的杠杆
- Prompt 是代码：要版本管理、要测试、要回归

## 五要素模板

```markdown
# 角色
你是资深后端工程师，负责代码审查。

# 任务
审查以下 diff，找出安全与性能问题。

# 约束
- 只报告确定的问题，不确定的标注「待确认」
- 不要重写整个文件，给出最小修改建议

# 示例
输入: "password = input()" 
输出: {"severity": "high", "issue": "明文密码", "fix": "使用 getpass"}

# 待审查内容
{diff}
```

## 源码案例

**Claude Code 的系统提示词就是最好的教材**（逆向全集：[Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)）：

- **短**：核心指令刻意精炼，规则都是可执行的行为约束（"Do what has been asked; nothing more, nothing less"）
- **模块化注册**：每段指令是独立 section（`systemPromptSection(name, compute)` 工厂函数注册），按模式/场景组装，便于缓存与优先级管理
- **五级优先级**：主循环 / REPL / 编排器 / 子 Agent 各有专属指令段，重叠场景按级别取高者
- **子 Agent 提示词示范「克制」**：General Purpose Agent 的 prompt 反复强调「绝不创建不必要的文件」「只做被要求的事」——约束越明确，Agent 越不跑偏

**Pi 的极简哲学**：system prompt 全部压在 1000 token 内，把「行为规范」交给工具描述与扩展机制——证明 prompt 不是越长越好，越明确越好。

## 最佳实践

- 用 Git 管理 prompt，改动跑回归集（一批固定输入 → 期望输出的用例）
- 让模型先复述任务再执行，可发现理解偏差
- 负面指令改成正面指令：「不要啰嗦」→「每个要点一句话」

## 常见误区

- ❌ 迷信咒语（"thinking step by step" 万能）：对不同模型效果差异大，实测为准
- ❌ 一个 prompt 打天下：主任务、总结、改写应分开，pipeline 化（→ [工作流编排](../07-planning/workflow-orchestration.md)）
- ❌ 忽略工具描述：对 Agent 来说，工具的 description 就是最重要的 prompt（见 [Function Calling](../05-tool-protocol/function-calling.md)）

## 小练习

把「帮我写周报」改写成五要素齐全的 prompt，并设计 3 个回归测试用例。

## 相关知识点

- [结构化输出](structured-output.md)
- [上下文工程](../06-memory-rag/context-engineering.md)
