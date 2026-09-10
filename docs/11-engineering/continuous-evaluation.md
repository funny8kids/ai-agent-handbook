---
tags: [engineering, evaluation]
type: knowledge
status: published
updated: 2026-09-10
---

# 持续评估

> **一句话**：持续评估 = 把「评估集 + 回归测试 + 线上数据回流」接进 CI/CD，让每次 prompt、模型、工具变更都有数据说话——评估不是上线前的一次性动作，是常态化的质量管线。

## 先看结论

- 三个闭环：提交触发评估（防退化）、定时全量评估（防漂移）、线上失败回流用例（越用越强）
- 评估进 CI 的门槛要低：核心集 < 100 条、分钟级跑完，开发者才愿意每次都跑
- **小评估集测不出小退化**：100 条用例的置信区间约 ±10%——要用统计眼光看分数
- 模型漂移是隐性风险：供应商静默更新模型，定时评估是唯一哨兵
- 指标看板化：成功率、成本、延迟三线趋势图

## 核心机制

### 1. 评估集能测出多大的差异

评估分数是一个比例估计，其置信区间宽度约为：

$$
\text{CI}_{95\%}\approx 1.96\sqrt{\frac{p(1-p)}{n}}
$$

以 $n=100$、$p=0.9$ 为例：

$$
1.96\sqrt{\frac{0.9\times0.1}{100}}\approx 0.059
$$

即 **±6 个百分点**。这带来三条非常实用的推论：

- **100 条用例无法可靠区分 92% 与 88%**——差异落在噪声里
- 想检测更小的退化，必须扩大评估集，或改用**成对比较**（同一批用例上做 A/B，看翻转的用例数）
- 报告分数时应带样本量，否则「提升 3%」可能只是换了批用例

$$
n\uparrow \;\Longrightarrow\; \text{CI}\downarrow \;\Longrightarrow\; \text{能分辨的差异更小}
$$

### 2. 三个闭环各防什么

$$
\underbrace{\text{提交触发}}_{\text{防退化}}
\qquad
\underbrace{\text{定时全量}}_{\text{防漂移}}
\qquad
\underbrace{\text{线上回流}}_{\text{越用越强}}
$$

- **防退化**：改 prompt/模型/工具后立即跑核心集，退化则阻断合并
- **防漂移**：模型供应商可能静默更新权重，只有定时评估能发现「同样的 prompt 分数变了」
- **越用越强**：线上失败 trace 一键转为用例，评估集随业务演进

### 3. 警惕对评估集过拟合

反复用同一评估集调 prompt，会把它「刷绿」而不提升真实能力：

$$
\text{评估集分数}\uparrow\;\;\not\Rightarrow\;\;\text{线上表现}\uparrow
$$

对策是保留一个**盲测集（holdout）**，永不参与调优，只在发布前跑一次。这与机器学习里「训练集/验证集/测试集」的纪律完全一致（见 [机器学习基础](../01-ai-basics/machine-learning-basics.md)）。

## 评估闭环

```mermaid
flowchart LR
  A[提交变更<br/>prompt/模型/工具] --> B[CI: 核心评估集<br/>"<100条, 分钟级"]
  B -- 回归 --> X[阻断合并]
  B -- 通过 --> C[合并上线]
  C --> D[线上监控]
  D -- 失败 trace --> E[人工标注<br/>转为新用例]
  E --> B
  B -.定时.-> F[全量评估<br/>防模型漂移]
```

## 工程含义

- **用例分三档**：冒烟（约 10 条，秒级，本地提交前跑）、核心（<100 条，CI）、全量（千级，定时跑）。
- **断言分层**：硬断言（包含/正则/JSON 校验）优先，LLM-judge 只补主观维度——程序化断言既便宜又稳定（见 [Agent 评估指标](../10-evaluation-safety/evaluation-metrics.md)）。
- **回流管道是评估体系的「新陈代谢」**：没有线上失败回流，评估集会逐渐与真实场景脱节。
- **评估本身有成本**：LLM-judge 与全量集都要花钱，按「变更频率 × 重要性」分配评估预算。

## 源码案例

- **LangSmith 的实验管理**（[文档](https://docs.smith.langchain.com/)）：dataset → experiment → 对比视图，每次变更生成一份「成绩单」；配 CI 可在 PR 里直接显示评估结果
- **LangFuse + 定时评估**（[GitHub](https://github.com/langfuse/langfuse)）：线上 trace 按比例抽样跑 LLM-judge 评分，趋势入看板——「线上持续评估」的开源自托管方案
- **promptfoo**（[GitHub](https://github.com/promptfoo/promptfoo)）：轻量 prompt 回归工具，YAML 定义用例矩阵（prompt × 模型 × 断言），本地/CI 都能跑
- **SWE-bench Verified 的启示**（[仓库](https://github.com/princeton-nlp/SWE-bench)）：人工核验过的 500 题成为全行业共同标尺——**评估集的质量与可信度本身就是工程资产**

## 常见误区

- ❌ 评估集一次构建永不更新：产品演进后老用例失效，要有季度清理机制
- ❌ 只评新功能不跑回归：模型供应商更新就能让「稳定 prompt」悄悄退化
- ❌ 用评估集调 prompt 直到全绿：过拟合评估集 ≠ 真实变好，要留盲测集
- ❌ 报告分数不带样本量：100 条用例的 ±6% 波动常被误读为「提升」
- ❌ 全部用 LLM 打分：能用断言就别用 judge，成本与稳定性都更差

## 小练习

为你的 Agent 建 20 条冒烟用例（覆盖：正常流、边界、注入、拒答），接入 CI，故意改坏一个 prompt 看能否被拦住。再计算：以你的核心集规模，能分辨的最小差异是多少个百分点？

## 参考资料

- [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770)（Jimenez et al., 2023）
- [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217)（Es et al., 2023）
- [LangSmith 文档](https://docs.smith.langchain.com/) / [promptfoo](https://github.com/promptfoo/promptfoo)

## 相关知识点

- [Agent 评估指标](../10-evaluation-safety/evaluation-metrics.md)
- [可观测性工具](observability-tools.md)
- [基准测试总览](../10-evaluation-safety/benchmarks.md)
