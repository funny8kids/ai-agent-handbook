---
tags: [engineering, evaluation]
type: knowledge
status: published
updated: 2026-09-10
---

# 🚀 持续评估

> **一句话**：持续评估 = 把「评估集 + 回归测试 + 线上数据回流」接进 CI/CD，让每次 prompt、模型、工具变更都有数据说话——评估不是上线前的一次性动作，是常态化的质量管线。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#engineering` `#evaluation`

## 📌 先看结论

- 三个闭环：提交触发评估（防退化）、定时全量评估（防漂移）、线上失败回流用例（越长越强）
- 评估进 CI 的门槛要低：核心集 < 100 条、分钟级跑完，开发者才愿意每次都跑
- 模型漂移是隐性风险：供应商静默更新模型，定时评估是唯一哨兵
- 指标看板化：成功率、成本、延迟三线趋势图，变更前后的对比一目了然

## 🖼️ 评估闭环

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

## 📦 源码案例

- **LangSmith 的实验管理**（[文档](https://docs.smith.langchain.com/)）：dataset → experiment → 对比视图，每次变更自动生成一份「成绩单」；配 GitHub Actions 可实现 PR 评论里直接显示评估结果——评估进 CI 的最短路径
- **LangFuse + 定时评估**（[GitHub](https://github.com/langfuse/langfuse)）：线上 trace 按比例抽样跑 LLM-judge 评分，趋势入看板——「线上持续评估」的开源自托管方案
- **promptfoo**（[GitHub](https://github.com/promptfoo/promptfoo)）：轻量 prompt 回归工具，YAML 定义用例矩阵（prompt × 模型 × 断言），本地/CI 都能跑——不想上重型平台时的务实选择
- **SWE-bench Verified 的启示**（[仓库](https://github.com/princeton-nlp/SWE-bench)）：500 道人工核验题成为全行业「防作弊」的共同标尺——评估集的质量与可信度本身就是工程资产

## ✅ 最佳实践

- 用例分三档：冒烟（10 条，秒级）、核心（<100 条，CI）、全量（千级，定时）
- 断言分层：硬断言（包含/正则/JSON 校验）优先，LLM-judge 补充主观维度
- 每条失败 trace 一键转用例：从线上到评估集的回流管道是评估体系的「新陈代谢」

## ⚠️ 常见误区

- ❌ 评估集一次构建永不更新：产品演进后老用例失效，要有季度清理机制
- ❌ 只评新功能不跑回归：模型供应商更新就能让你的「稳定 prompt」悄悄退化
- ❌ 用评估集调 prompt 直到全绿：过拟合评估集 ≠ 真实变好，留一个「盲测集」永不参与调优

## 🧪 小练习

为你的 Agent 建 20 条冒烟用例（覆盖：正常流、边界、注入、拒答），接入 CI，故意改坏一个 prompt 看能否被拦住。

## 📚 相关知识点

- [Agent 评估指标](../10-evaluation-safety/evaluation-metrics.md)
- [LangSmith、LangFuse、Phoenix、OpenTelemetry](observability-tools.md)
