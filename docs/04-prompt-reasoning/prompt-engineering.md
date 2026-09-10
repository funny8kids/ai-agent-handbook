---
tags: [prompt, basics]
type: knowledge
status: published
updated: 2026-09-10
---

# Prompt Engineering

> **一句话**：Prompt Engineering 是给「概率机器」写需求文档——角色、任务、约束、示例、格式五要素写清楚，输出质量立竿见影。

## 先看结论

- 五要素：角色（你是谁）、任务（做什么）、约束（不许做什么）、示例（照这个样子）、格式（输出长什么样）
- 本质上是在**指定条件分布**：prompt 是条件，输出是条件分布下的采样
- 指令放前、参考材料放中、指令尾部重申一次（对抗 lost-in-the-middle）
- 与其堆技巧，不如给例子：2–5 个 few-shot 示例是最稳的杠杆
- Prompt 是代码：要版本管理、要测试、要回归

## 核心机制

### 1. prompt 是「条件」，不是「指令」

模型学到的是条件分布 $P_\theta(y\mid x)$，其中 $x$ 就是你拼出来的整个 prompt。所谓「写好 prompt」，其实是在**构造一个条件 $x$，使得目标输出 $y^*$ 在 $P_\theta(y\mid x)$ 下概率尽可能高**：

$$
x^*=\operatorname*{arg\,max}_{x}\;\log P_\theta\big(y^*\mid x\big)
$$

这个视角能解释几个经验规律：

- 为什么**示例有效**：示例直接改变了条件分布的形状，把「我想要的输出」展示给模型，比用语言描述它更精确
- 为什么**措辞敏感**：不同的 $x$ 落在分布的不同区域，微小改写可能导致输出显著变化——有研究系统量化过这种敏感性
- 为什么**格式约束要显式**：分布里同时存在多种合理输出，不指定格式就会被采样到任意一种

### 2. 位置效应

上下文的信息利用率不是均匀的：模型对**开头**和**结尾**的内容利用更好，中段容易被忽略（lost in the middle）。因此长上下文 prompt 的结构应是：

$$
\big[\text{角色与任务}\big]\;\big[\text{参考材料（长）}\big]\;\big[\text{任务重申 + 输出格式}\big]
$$

把关键指令放在首尾各一次，是低成本且有效的工程手段（原理见 [Transformer 与 Attention](../03-llm/transformer-attention.md) 与 [上下文工程](../06-memory-rag/context-engineering.md)）。

### 3. 零样本、少样本与分解

| 手段 | 做法 | 何时用 |
|---|---|---|
| zero-shot | 只给指令 | 任务常见、模型熟悉 |
| few-shot | 给 2–5 个「输入→输出」示例 | 格式特殊、有隐含判据时最有效 |
| 分解（decomposition） | 把复杂任务拆成多个 prompt 串起来 | 单 prompt 顾此失彼时 |

**few-shot 的关键不是数量而是覆盖**：示例要覆盖典型分支与边界情况，否则模型会模仿到错误的「规律」。若示例与指令冲突，模型往往跟示例走（示例是更强的条件信号）。

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

- **短**：核心指令刻意精炼，规则都是可执行的行为约束（如「只做被要求的事，不多不少」）
- **模块化注册**：每段指令是独立 section，按模式/场景组装，便于缓存与优先级管理
- **分层优先级**：主循环 / 交互层 / 编排层 / 子 Agent 各有专属指令段
- **克制原则**：子 Agent 的 prompt 反复强调「绝不创建不必要的文件」——约束越明确，Agent 越不跑偏

**Pi 的取向**（[仓库](https://github.com/earendil-works/pi)）：把行为规范尽量交给工具描述与扩展机制，而不是堆砌系统提示——「prompt 不是越长越好，越明确越好」。

## 工程含义

- **Prompt 是代码资产**：用 Git 管理、改动跑回归集（一批固定输入 → 期望输出），否则每次「优化」都在赌
- **把可验证的约束下沉到代码**：能用 schema 校验、能用工具约束的，不要只靠 prompt 里的一句「请务必」
- **区分「稳定前缀」与「动态内容」**：静态部分保持字节一致以命中 prompt 缓存（见 [缓存与成本优化](../11-engineering/caching-cost-optimization.md)）
- **负面指令改正面指令**：「不要啰嗦」→「每个要点一句话」，前者只说明禁止什么，后者给出了可执行的目标

## 常见误区

- ❌ 迷信咒语（"think step by step" 万能）：对不同模型效果差异大，实测为准
- ❌ 一个 prompt 打天下：主任务、总结、改写应分开，pipeline 化（→ [工作流编排](../07-planning/workflow-orchestration.md)）
- ❌ 忽略工具描述：对 Agent 来说，工具的 description 就是最重要的 prompt（见 [Function Calling](../05-tool-protocol/function-calling.md)）
- ❌ 用「请务必严格遵守」代替结构化约束：模型对绝对化措辞并不敏感，对格式/校验才敏感
- ❌ Prompt 越写越长：冗长会稀释关键指令，且推高每轮成本

## 小练习

把「帮我写周报」改写成五要素齐全的 prompt，并设计 3 个回归测试用例（输入 + 期望输出特征）。再指出哪一条约束应该下沉为代码校验而不是写在 prompt 里。

## 参考资料

- [The Prompt Report: A Systematic Survey of Prompting Techniques](https://arxiv.org/abs/2406.06608)（Schulhoff et al., 2024）
- [Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design](https://arxiv.org/abs/2310.11324)（Sclar et al., 2023，prompt 敏感性）
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)（Liu et al., 2023）
- [Principled Instructions Are All You Need for Questioning LLaMA-1/2, GPT-3.5/4](https://arxiv.org/abs/2312.16171)（Bsharat et al., 2023）

## 相关知识点

- [结构化输出](structured-output.md)
- [上下文工程](../06-memory-rag/context-engineering.md)
- [Chain of Thought](chain-of-thought.md)
