---
tags: [framework, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# DSPy

> **一句话**：DSPy（Declarative Self-improving Python）把 prompt 从「手写咒语」变成「编译产物」：声明输入输出 + 少量样例，框架自动优化提示词——「prompt 工程的程序化」。
> **难度**：高级
> **标签**：`#framework`

## 先看结论

- 核心思想：写「签名（Signature）」声明模块做什么 → 用优化器（Optimizer）在指标上自动搜出最佳 prompt/few-shot 组合
- 价值：prompt 随模型升级自动重新优化；换模型不用重写咒语，重新编译即可
- 关键前提：必须有**评估集与指标**——没有 metric 就没有优化，这是它倒逼的工程习惯
- 适用：管线型任务（RAG、抽取、分类）质量优化；不适合：探索型 Agent 循环

## 核心概念

| 概念 | 作用 | 类比 |
|---|---|---|
| Signature | 声明式接口：输入/输出字段 | 函数签名 |
| Module | 组合签名的程序结构（ChainOfThought/ReAct） | 标准库组件 |
| Optimizer | 用 metric 自动调 prompt/few-shot | 编译器优化器 |
| Metric | 打分函数（精确匹配/LLM 评分） | 单元测试断言 |

## 最小示例

```python
import dspy

class QA(dspy.Signature):
    """根据上下文回答问题"""
    context: str = dspy.InputField()
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

rag = dspy.ChainOfThought(QA)

trainset = [dspy.Example(context=c, question=q, answer=a) ...]
optimizer = dspy.MIPROv2(metric=exact_match, auto="light")
rag_optimized = optimizer.compile(rag, trainset=trainset)
# rag_optimized 里是自动搜索出的 prompt 与 few-shot 组合
```

## 源码案例

- **dspy.ReAct**（[GitHub](https://github.com/stanfordnlp/dspy)）：DSPy 内置 ReAct 模块——声明工具与签名，推理循环由框架展开；对照 [ReAct 原始论文实现](../04-prompt-reasoning/react.md)，体会「手写模板」与「编译生成模板」的差别
- **MIPROv2 优化器**：贝叶斯搜索 prompt 指令 + few-shot 组合，读它的 `compile` 流程（提案-评估-选择）能理解「prompt 搜索空间」如何被系统化探索
- **学术背书**：DSPy 论文（[arXiv:2310.03714](https://arxiv.org/abs/2310.03714)）报告：相同管线经编译后，在多任务上超过手写 prompt 的基线，且换模型时质量保持稳定

## 常见误区

- ❌ DSPy 会「自动」变好：metric 设计决定优化上限，垃圾指标优化出垃圾 prompt
- ❌ 适合一切场景：开放对话、创意生成难以定义 metric，编译无从谈起
- ❌ 拿来即用不读产物：编译出的 prompt 要人工审查——自动优化也可能搜出「应试技巧」式的 prompt

## 小练习

把你的「工单分类」手写 prompt 迁移到 DSPy：定义 Signature，标注 30 条训练样例，跑 MIPROv2 编译，对比手写版的准确率。

## 相关资源

- [DSPy 文档](https://dspy.ai)
- [DSPy 论文](https://arxiv.org/abs/2310.03714)

## 相关知识点

- [Prompt Engineering](../04-prompt-reasoning/prompt-engineering.md)
- [持续评估](../11-engineering/continuous-evaluation.md)
