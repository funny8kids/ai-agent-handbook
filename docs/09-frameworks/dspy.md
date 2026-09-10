---
tags: [framework, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# DSPy

> **一句话**：DSPy（Declarative Self-improving Python）把 prompt 从「手写咒语」变成「编译产物」：声明输入输出 + 少量样例，框架自动优化提示词——「prompt 工程的程序化」。

## 先看结论

- 核心思想：写「签名（Signature）」声明模块做什么 → 用优化器在指标上自动搜出最佳 prompt/few-shot 组合
- 价值：prompt 随模型升级可自动重新优化；换模型不用重写咒语，重新编译即可
- 关键前提：必须有**评估集与指标**——没有 metric 就没有优化，这是它倒逼的工程习惯
- 适用：管线型任务（RAG、抽取、分类）的质量优化；不适合：探索型 Agent 循环

## 核心抽象

DSPy 的出发点是一个判断：**手写 prompt 的不可复现性来自「把两件事混在一起」**——程序逻辑（做什么）与提示措辞（怎么说）。它把二者拆开：

$$
\underbrace{\text{Signature}}_{\text{声明做什么}}
\;+\;
\underbrace{\text{Module}}_{\text{怎么组合}}
\;\xrightarrow{\text{Optimizer}}\;
\underbrace{p^*}_{\text{自动搜出的提示}}
$$

其中优化目标写得很直白——在评估集上最大化指标：

$$
p^*=\operatorname*{arg\,max}_{p\in\mathcal{P}}\;
\mathbb{E}_{(x,y)\sim\mathcal{D}}\Big[\,m\big(f_p(x),\,y\big)\Big]
$$

- $$\mathcal{P}$$：**提示空间**，包含指令措辞与 few-shot 示例的选择
- $$f_p$$：给定提示 $$p$$ 的完整程序
- $$m$$：指标函数（精确匹配、F1、LLM 评分等）

现代优化器（如 MIPROv2）用「先自举出候选示例、再用贝叶斯搜索在指令 × 示例的组合空间里找高分方案」的方式近似求解。**这条式子是整个框架的钥匙**：优化上限完全由 $$\mathcal{D}$$ 与 $$m$$ 决定——垃圾指标必然优化出垃圾 prompt。

| 概念 | 作用 | 类比 |
|---|---|---|
| Signature | 声明式接口：输入/输出字段 | 函数签名 |
| Module | 组合签名的程序结构（ChainOfThought/ReAct） | 标准库组件 |
| Optimizer | 用 metric 自动调 prompt/few-shot | 编译器优化器 |
| Metric | 打分函数 | 单元测试断言 |

## 最小示例

```python
import dspy

class QA(dspy.Signature):
    """根据上下文回答问题"""
    context: str = dspy.InputField()
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

rag = dspy.ChainOfThought(QA)

trainset = [dspy.Example(context=c, question=q, answer=a) for ...]
optimizer = dspy.MIPROv2(metric=exact_match, auto="light")
rag_optimized = optimizer.compile(rag, trainset=trainset)
# rag_optimized 里是自动搜索出的 prompt 与 few-shot 组合
```

## 选型对比

| 维度 | DSPy | 手写 prompt | LangChain |
|---|---|---|---|
| prompt 来源 | 编译生成 | 人写 | 人写 |
| 换模型成本 | 重新编译 | 重写/重调 | 重写/重调 |
| 前提条件 | 评估集 + 指标 | 无 | 无 |
| 可复现性 | 高（产物可版本化） | 低（措辞敏感） | 低 |
| 适合 | 有明确指标的任务 | 快速试错 | 应用集成 |

**选型建议**：任务有清晰指标（分类准确率、抽取 F1、检索命中率）且会被反复迭代 → DSPy 收益明显；开放式创意任务难以定义 metric → 手写 prompt 更实际。

## 源码案例

- **dspy.ReAct**（[GitHub](https://github.com/stanfordnlp/dspy)）：DSPy 内置 ReAct 模块——声明工具与签名，推理循环由框架展开；对照 [ReAct](../04-prompt-reasoning/react.md)，体会「手写模板」与「编译生成模板」的差别
- **MIPROv2 优化器**：在指令与示例的组合空间上做贝叶斯搜索，读它的「提案-评估-选择」流程能理解 prompt 搜索空间如何被系统化探索
- **学术背书**：DSPy 论文（[arXiv:2310.03714](https://arxiv.org/abs/2310.03714)）报告：相同管线经编译后，在多任务上超过手写 prompt 基线，且换模型时质量更稳定

## 工程含义

- **先有评估集，再谈优化**：DSPy 的最大副作用是逼你建立指标与评估集——这件事本身的价值常超过自动优化。
- **编译产物要审查**：自动搜出的 prompt 应人工过目，确认它学的是「能力」而不是「应试技巧」。
- **编译产物要入库**：把它当代码资产版本化管理，才能追踪「哪次优化带来了提升」。

## 常见误区

- ❌ DSPy 会「自动」变好：metric 设计决定优化上限，垃圾指标优化出垃圾 prompt
- ❌ 适合一切场景：开放对话、创意生成难以定义 metric，编译无从谈起
- ❌ 拿来即用不读产物：自动优化也可能搜出过拟合评估集的 prompt
- ❌ 评估集太小：几十条样例上编译出的 prompt 极易过拟合，泛化要看留出集

## 小练习

把你的「工单分类」手写 prompt 迁移到 DSPy：定义 Signature，标注 30 条训练样例，跑 MIPROv2 编译，对比手写版的准确率，并检查编译出的 prompt 是否只学到了「分类能力」。

## 参考资料

- [DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines](https://arxiv.org/abs/2310.03714)（Khattab et al., 2023）
- [DSPy 官方文档](https://dspy.ai)
- [Prompt Engineering](../04-prompt-reasoning/prompt-engineering.md)

## 相关知识点

- [Prompt Engineering](../04-prompt-reasoning/prompt-engineering.md)
- [持续评估](../11-engineering/continuous-evaluation.md)
- [Agent 评估指标](../10-evaluation-safety/evaluation-metrics.md)
