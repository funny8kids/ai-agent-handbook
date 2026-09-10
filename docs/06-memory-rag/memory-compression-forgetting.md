---
tags: [memory, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 记忆压缩、遗忘与摘要

> **一句话**：窗口迟早会满，所以 Agent 必须学会「忘记」：压缩（保留要点）、摘要（浓缩历史）、遗忘（主动淘汰）——这是长任务 Agent 的生存技能。

## 问题动机

长任务 Agent 的上下文会随轮数单调增长：每一轮的工具输出、观察、对话都往里堆。但窗口有上限，注意力成本还是 $O(n^2)$。不做处理，要么请求超限失败，要么成本与延迟失控、关键信息被稀释。因此「怎么忘」不是可选项，而是长任务 Agent 的核心机制。

## 核心机制

### 1. 触发：水位线策略

设当前上下文长度 $|C|$、窗口 $T_{\max}$、阈值比例 $\theta$（常见 0.7–0.8），当

$$
|C| \;\ge\; \theta\,T_{\max}
$$

时触发压缩。也可以叠加「每 $N$ 轮定时压缩」。保留 $\theta<1$ 的余量是为了给压缩本身和后续输出留空间。

### 2. 压缩比与信息损失

压缩就是把原文 $c$ 映射为更短的表示 $c'$，压缩比：

$$
\rho=1-\frac{|c'|}{|c|}
$$

摘要是有损编码：$c'$ 保留的信息量不可能超过原文熵，$I(c;c')\le H(c)$。工程含义是——**必须区分「可丢」与「不可丢」**：

| 类型 | 处理 | 理由 |
|---|---|---|
| 旧工具输出（占上下文 60–90%） | 摘要或截断 | 多数历史结果不再需要全文 |
| 用户目标、关键决策 | 永不压缩 | 丢了任务就偏了 |
| 失败教训 | 保留结论，丢细节 | 是自我改进的原料（→ [Reflexion](../04-prompt-reasoning/reflexion.md)） |
| 文件路径、已部署配置 | 原文保留 | 模糊化会造成危险误操作 |
| 最近 $k$ 轮 | 不压缩 | 时效性最高 |

### 3. 保留哪些：一个「缓存淘汰」问题

把每个条目 $i$ 看成要决定「留还是丢」。理想判据是单位 token 的未来效用：

$$
\text{keep } i \iff \frac{\mathbb{E}\big[\text{future utility}_i\big]}{|i|} \;\ge\;\lambda
$$

这与操作系统的缓存淘汰同构：LFU 近似「重要度」，LRU 近似「时效性」，实践中用**重要度 × 时效**的加权分更稳。不可逆动作相关的信息应给无限权重（永不淘汰）。

### 4. 原文外存：让遗忘可逆

压缩的前提是「将来还能找回来」。把原文写入会话文件/事件日志，需要时按需检索：

$$
\text{上下文}=\text{摘要}(c)\;\;+\;\;\text{可检索的原文存档}
$$

这样压缩才敢激进——「压缩 ≠ 丢失」。DeepSeek Harness 的 append-only 事件流 + 投影正是这一思想的极致形态：历史层永不删，遗忘只发生在投影层。

## 压缩流水线

```mermaid
flowchart LR
  A[上下文水位监测] -- 达到阈值 --> B[选择压缩对象<br/>旧工具输出/久远对话]
  B --> C[生成摘要<br/>保留决策与结论]
  C --> D[原文外存<br/>可按需检索回]
  D --> E[替换原文为摘要]
```

## 工程含义

- **摘要 prompt 要规定保留项**：用户目标、关键决策、失败教训、当前进度；丢弃过程细节。
- **压缩前后做一次结构化状态检查**（Todo 清单），防止压缩吃掉关键 TODO。
- **把压缩当一次可能出错的转换**：压缩后若任务跑偏，要能回滚到原文重来。

## 源码案例

**三家 harness 的三种答案**（案例深拆见 [编程 Agent](../12-applications/coding-agent.md)）：

- **Claude Code：三档压缩体系**（逆向分析，[架构深拆](https://gist.github.com/yanchuk/0c47dd351c2805236e44ec3935e9095d)）：auto-compact（整体摘要，保留目标/决策/未完成项）、microcompact（替换单个旧工具输出）、snip（更小的局部裁剪）；配套「工具使用摘要」
- **Pi：三条机制守水位**（[earendil-works/pi](https://github.com/earendil-works/pi)）：截断、摘要、微压缩，全部嵌在 agentLoop 内随水位自动触发；被压缩的原始消息仍在 JSONL 会话文件里，可回溯
- **DeepSeek Harness：投影式「遗忘」**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：append-only 日志保留全量事件，模型上下文只是日志的「投影」——遗忘发生在投影层，历史层永不丢失，回放/审计/取证都可行

## 常见误区

- ❌ 依赖超长窗口不压缩：成本、延迟、注意力衰减三重惩罚，压缩永远有价值
- ❌ 摘要丢掉「失败记录」：失败教训恰恰是自我改进的原料
- ❌ 压缩不可逆：要像事件流那样保留原文，压缩才敢激进
- ❌ 只按时间淘汰：位置靠后但承载「用户目标」的条目绝不能按 LRU 丢掉

## 小练习

一个爬虫 Agent 跑 3 小时、200 轮，每轮工具输出 2K token。设计它的压缩策略：水位线多少？哪些保留、哪些摘要、哪些丢？摘要模板写出来。

## 参考资料

- [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560)（Packer et al., 2023，分层记忆与换入换出）
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)（Liu et al., 2023）
- [LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression](https://arxiv.org/abs/2310.06839)（Jiang et al., 2023）

## 相关知识点

- [上下文工程](context-engineering.md)
- [Agent 状态管理](../02-agent-basics/state-management.md)
