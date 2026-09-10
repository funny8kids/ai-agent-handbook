---
tags: [prompt, agent]
type: knowledge
status: published
updated: 2026-09-10
---

# ReAct

> **一句话**：ReAct（Reasoning + Acting）让模型交替进行「思考轨迹」和「行动」——想一步、做一步、看结果、再想，是现代 Agent 循环的思想原型。

## 先看结论

- 核心洞察：推理为行动提供计划与追踪，行动为推理提供真实反馈——两者缺一都会失败
- 轨迹形式是交替序列：`Thought → Action → Observation → Thought → …`
- 相比纯推理（CoT-only）不易产生幻觉链；相比纯行动（Act-only）更能做多步规划
- 今天所说的「Agent 循环」几乎都是 ReAct 的工程化；区别只在「思考写在文本里」还是「内化为专用 token」

## 核心机制

### 1. 交替序列的形式化

ReAct 把一次任务求解写成交替的轨迹：

$$
\tau=\big(T_1,A_1,O_1,\;T_2,A_2,O_2,\;\dots,\;T_n\big)
$$

- $$T_i$$：**Thought**，模型生成的推理文本（「我需要先查 X」）
- $$A_i$$：**Action**，结构化的工具调用（如 `search["..."]`）
- $$O_i$$：**Observation**，环境/工具返回的真实结果

其中 $$A_i$$ 由 $$T_i$$ 决定，$$T_{i+1}$$ 基于 $$(T_i,A_i,O_i)$$ 继续，而 $$O_i$$ 来自真实世界：

$$
O_i=\mathrm{Env}(A_i)\quad\text{（确定性来源，不是生成出来的）}
$$

这一条把 ReAct 与 CoT 区分开：CoT 的所有中间内容都由模型生成，一旦某步是幻觉，后续推理会建立在错误之上；ReAct 每走一步都被真实结果「拉回正轨」，因此更抗幻觉。

### 2. 为什么必须交替

考虑两种退化情形：

- **只有推理（CoT-only）**：没有外部信息注入，模型无法知道自己错在哪，长链条误差累积
- **只有行动（Act-only）**：不解释目标、不追踪进度，容易在浅层反复试错、缺乏多步规划

ReAct 的观点是二者**互补**：推理负责「规划与追踪」，行动负责「获取事实」。论文在 HotpotQA（多跳问答）、ALFWorld（具身决策）、WebShop（网购）等任务上验证了这一组合优于任一单独形式（[Yao et al., 2022](https://arxiv.org/abs/2210.03629)）。

### 3. 现代形态：思考被内化

在推理模型（o1、DeepSeek-R1 类）中，Thought 不再以可见文本产出，而是由模型在内部完成（或写在单独的 `reasoning_content` 字段）。但**行为模式没变**：仍是「想—做—看—再想」。所以判断一个系统是不是 ReAct，看的是它是否交替「决策与真实观察」，而不是看它有没有输出 Thought 文本。

## 循环示例

```text
问题: 2026年开源的 DeepSeek Harness 用什么插件框架?

Thought 1: 我需要先搜索 DeepSeek Harness 的发布信息。
Action 1: search["DeepSeek Harness 开源"]
Observation 1: 2026年8月开源，基于 Cordis 插件框架，MIT 协议……

Thought 2: 已获得答案。
Action 2: finish["Cordis 插件框架"]
```

## 源码案例

- **Pi：ReAct 的最小工程体**（[earendil-works/pi](https://github.com/earendil-works/pi)）：其 agentLoop 把 ReAct 循环落到工程实现——模型消息里的工具调用就是 Action，工具执行结果回填就是 Observation，而 Thought 由模型的原生推理承担。具体实现见仓库与 pi.dev 文档
- **DeepSeek Harness：ReAct 的状态机化**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：Thought/Action/Observation 变成显式事件流——`assistant/message`（含思考与工具调用）、`tool/result` 全部写入 append-only 日志，每一步可回放可审计
- **Claude Code：ReAct + 治理层**（逆向分析，[提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts)）：在循环之上加权限管道（Action 执行前过审批）、TodoWrite（把 Thought 固化成结构化计划）、压缩（Observation 超预算自动摘要）

## 工程含义

- **Observation 要清洗**：工具输出截断、去噪，但**错误信息要保留原文**——模型靠它修正
- **给 Thought 留空间**：不要在 system prompt 里禁止模型解释意图，那会削弱规划能力
- **失败的 Observation 是金矿**：显式提示「上次工具报错，换个方法」可显著提升恢复率（见 [错误恢复与重试](../07-planning/error-recovery-retry.md)）
- **Action 要可结构化验证**：Action 应是 schema 约束的结构化输出，才能在执行前做权限与参数校验（见 [Function Calling](../05-tool-protocol/function-calling.md)）

## 常见误区

- ❌ ReAct = 框架名：它是论文提出的 prompt 模式，LangChain 的 `ReActAgent` 只是实现之一
- ❌ 思考和行动必须都用文本：推理模型把 Thought 内化了，行为模式仍是 ReAct
- ❌ 只用 ReAct 就够：复杂任务仍需计划工具（TodoWrite）、记忆系统配合，ReAct 只是循环骨架
- ❌ Observation 由模型生成：一旦让模型「想象」工具结果，就退化成 CoT，抗幻觉优势随之消失

## 小练习

用 50 行以内的代码（任意语言）实现一个 ReAct 循环：一个 LLM 调用 + 一个 `calculator` 工具 + 循环。再回答：如果把 Observation 换成「模型自己猜的结果」，会退化成什么？

## 参考资料

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)（Yao et al., 2022）
- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)（Wei et al., 2022）
- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) / [Pi](https://github.com/earendil-works/pi)

## 相关知识点

- [感知—规划—行动循环](../02-agent-basics/perception-planning-action.md)
- [Chain of Thought](chain-of-thought.md)
- [Reflexion](reflexion.md)
