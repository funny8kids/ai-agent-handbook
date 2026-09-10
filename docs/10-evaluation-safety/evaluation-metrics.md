---
tags: [evaluation]
type: knowledge
status: published
updated: 2026-09-10
---

# 📊 Agent 评估指标

> **一句话**：Agent 评估四层指标：结果对不对（成功率）、过程好不好（轨迹质量）、贵不贵慢不慢（成本延迟）、稳不稳（鲁棒性）——四层都测才叫评估。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#evaluation`

## 📌 先看结论

- 只看「最终答案对错」会掩盖问题：答对了但烧了 10 万 token、走了 40 步弯路，生产上不可接受
- 轨迹评估是 Agent 特有的：步骤冗余度、工具调用准确率、恢复质量
- LLM-as-judge 可扩展但有偏：位置偏差、长度偏差、自我偏好——用成对比较 + 校准缓解
- 评估集是资产：从第一天开始积累失败案例入集，回归测试防退化

## 🧩 四层指标体系

| 层级 | 指标 | 怎么测 |
|---|---|---|
| 结果层 | 任务成功率、部分完成度、答案质量 | 断言/单测/LLM 评分 |
| 轨迹层 | 步数冗余、工具选择正确率、错误恢复率 | 轨迹对比黄金路径 |
| 效率层 | token 成本、延迟 P50/P95、循环次数 | 计量埋点 |
| 鲁棒层 | 抗注入率、歧义输入表现、超时表现 | 对抗用例集 |

## 📦 源码案例与工具

- **OpenAI Agents SDK 评估**（[文档](https://openai.github.io/openai-agents-python/)）：内置 tracing + evaluation 钩子，Agent 运行即产出可评估轨迹——评估基础设施在 SDK 层的一等公民化
- **LangSmith 评估流**（[文档](https://docs.smith.langchain.com/)）：数据集 + 评估器（规则/LLM judge）+ 实验对比的完整闭环；把每次 prompt 改动变成一次「实验」，指标对比一目了然
- **Ragas**（[GitHub](https://github.com/explodinggradients/ragas)）：RAG 专项评估（忠实度、答案相关性、上下文精确率/召回率）——检索与生成分开打分，对应 [RAG 基础](../06-memory-rag/rag-basics.md) 的分环节评估原则
- **SWE-bench 的启示**（[仓库](https://github.com/princeton-nlp/SWE-bench)）：编程任务用「测试通过」做客观指标——凡是有可执行验证的任务，优先用程序化指标而非 LLM 评分

## ✅ 最佳实践

- 评估集三来源：历史真实 case、边界与对抗构造、线上失败回流
- LLM judge 用成对比较（A vs B 谁好）而非绝对打分，偏差更小
- 指标进 CI：每次 prompt/模型/工具变更跑回归，退化即报警

## ⚠️ 常见误区

- ❌ 用 vibe check 代替评估：「我试了几个例子都挺好」不是评估
- ❌ 数据泄漏：评估集进了 RAG 索引或 few-shot，成绩虚高
- ❌ 只评新不评旧：模型升级后老 case 回归才是防退化的关键

## 🧪 小练习

为「自动回复客户邮件」的 Agent 设计评估：写 10 个用例覆盖四层指标，并规定每层的通过阈值。

## 📚 相关知识点

- [基准测试总览](benchmarks.md)
- [持续评估](../11-engineering/continuous-evaluation.md)
