---
tags: [engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 🚀 LangSmith、LangFuse、Phoenix、OpenTelemetry

> **一句话**：四大观测方案：LangSmith（LangChain 生态 SaaS）、LangFuse（开源可自托管）、Phoenix（Arize 开源、评估强）、OpenTelemetry（厂商中立协议）——按「生态绑定与数据主权」选。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#engineering`

## 🧩 选型对比

| 方案 | 类型 | 优势 | 适合 |
|---|---|---|---|
| [LangSmith](https://docs.smith.langchain.com/) | SaaS | 与 LangChain 无缝、评估/数据集/实验管理一体 | LangChain/LangGraph 深度用户 |
| [LangFuse](https://github.com/langfuse/langfuse) | 开源（MIT 核心） | 自托管、成本追踪细、多语言 SDK | 要数据主权 + 全框架 |
| [Phoenix](https://github.com/Arize-ai/phoenix) | 开源 | RAG 评估强（Ragas 集成）、trace 可视化 | RAG 重度项目 |
| [OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | 协议标准 | 厂商中立、接企业现有观测栈 | 大企业统一观测 |

## 📌 先看结论

- 决策第一问：trace 数据能出内网吗？不能 → LangFuse/Phoenix 自托管；能 → SaaS 省心
- 决策第二问：现有观测栈是什么？已有 Datadog/Grafana → 走 OTel 协议接入，别再造孤岛
- 决策第三问：评估是不是刚需？是 → LangSmith/LangFuse 的数据集-实验闭环成熟度最高
- 四者并不互斥：LangFuse/Phoenix 都兼容 OTel 导出，可双轨过渡

## 💻 LangFuse 接入示例（Python）

```python
from langfuse.openai import openai   # 一行替换, 自动 trace

client = openai.OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "解释 MCP"}],
    metadata={"trace_id": task_id},   # 关联业务任务
)
```

## 📦 源码案例

- **Claude Code 的 OTel 支持**（[官方文档](https://docs.anthropic.com/en/docs/claude-code)）：企业可以把 Claude Code 的使用指标、工具调用统计导出到自有 OTel 后端——「开发工具也要接企业观测」的行业信号
- **LangFuse 的成本追踪**（[GitHub](https://github.com/langfuse/langfuse)）：按模型/用户/会话聚合 token 与费用，读它的 `modelUsage` 计算逻辑可理解成本归因设计（→ [缓存与成本优化](caching-cost-optimization.md)）
- **Phoenix 的 RAG 评估视图**（[GitHub](https://github.com/Arize-ai/phoenix)）：检索命中与生成质量的联合 trace 视图——调试「答非所问」时能直接看到「检索就错了」还是「生成跑偏了」

## ✅ 落地清单

- [ ] 每条 trace 带业务维度：user_id、tenant、task_type、prompt/模型版本
- [ ] 失败 trace 自动归档并附错误分类标签
- [ ] 周报指标：任务成功率、P95 延迟、单任务成本、Top 失败模式
- [ ] 观测数据回流评估集的流水线（trace → 用例）

## ⚠️ 常见误区

- ❌ 观测工具 = 接个 SDK 完事：没有业务维度标注的 trace 无法定位「哪类用户受影响」
- ❌ SaaS 观测不计隐私成本：prompt 里可能含 PII，看厂商的数据处理协议，或本地脱敏后再上报
- ❌ 只看单次 trace：价值在聚合——Top 失败模式、成本分布、慢步骤排名

## 🧪 小练习

为你的 Agent 选观测方案并说明决策链（数据主权？现有栈？评估需求？），然后接入并跑一周，输出一份「Top3 失败模式」报告。

## 📚 相关知识点

- [日志、追踪与监控](logging-tracing-monitoring.md)
- [持续评估](continuous-evaluation.md)
