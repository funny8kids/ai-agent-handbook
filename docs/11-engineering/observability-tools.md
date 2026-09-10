---
tags: [engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# LangSmith、LangFuse、Phoenix、OpenTelemetry

> **一句话**：四大观测方案：LangSmith（LangChain 生态 SaaS）、LangFuse（开源可自托管）、Phoenix（Arize 开源、评估强）、OpenTelemetry（厂商中立协议）——按「生态绑定与数据主权」选。

## 先看结论

- 决策第一问：trace 数据能出内网吗？不能 → 自托管；能 → SaaS 省心
- 决策第二问：现有观测栈是什么？已有 Datadog/Grafana → 走 OTel 协议接入，别再造孤岛
- 决策第三问：评估是不是刚需？是 → 数据集-实验闭环的成熟度最重要
- 四者并不互斥：多个方案都兼容 OTel 导出，可双轨过渡

## 核心机制

### 1. 一张 trace 应该长什么样

观测 Agent 与观测普通服务最大的不同是：**一次用户请求对应一棵嵌套的调用树**，而不是一条平坦的时间线。

$$
\text{trace}=\underbrace{\text{agent run}}_{\text{一次任务}}
\to\underbrace{\text{llm call}}_{\text{模型调用}}
+\underbrace{\text{tool exec}}_{\text{工具执行}}
+\underbrace{\text{sub-agent}}_{\text{子 Agent}}
$$

每一层都是一个 **span**，带自己的起止时间、输入输出与元数据。于是「为什么这次答错了」可以逐层定位：是检索没召回、工具报错、还是模型自己跑偏。

### 2. 用 OTel 语义约定描述 GenAI

OpenTelemetry 为 GenAI 定义了**语义约定**（semantic conventions），规定 span 与属性的命名，使不同厂商的实现可互操作。核心属性覆盖三类信息：

| 类别 | 典型属性 | 用途 |
|---|---|---|
| 操作 | 操作类型（聊天/工具执行/Agent 调用） | 区分 span 种类 |
| 模型 | 供应商、模型名、请求参数 | 成本归因与对比 |
| 用量 | 输入 token、输出 token | 计费与优化 |

**为什么要用约定的属性名而不是自定义**：只有这样，换成另一套后端（或自建）时 trace 仍然可读，评估与成本分析工具也能直接复用。这是「协议优先于工具」在可观测性上的体现。

### 3. 采样：全量采集会破产

Agent 的 trace 又大又贵（每次都含完整 prompt 与工具输出）。全量保留不现实，需要采样：

$$
\text{保留 trace 数}\approx \text{总量}\times r\qquad(r=\text{采样率})
$$

两种策略各有取舍：

| 策略 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| 头部采样 | 请求进入时按比例决定 | 实现简单、成本可控 | 会漏掉罕见错误 |
| 尾部采样 | 先收集，按结果决定留不留 | 能保住全部错误与慢请求 | 需要缓冲、实现复杂 |

**推荐组合**：错误与超时的 trace **全留**，成功请求按低比例采样。这样既控制成本，又不丢最有价值的诊断样本。

### 4. 成本归因

要让成本可优化，必须把 token 用量按维度聚合：

$$
\text{Cost}=\sum_{\text{模型}}\big(c_{\text{in}}T_{\text{in}}+c_{\text{out}}T_{\text{out}}\big)
$$

聚合维度至少要有：用户/租户、任务类型、prompt 版本、模型。有了这些维度才能回答「哪个功能最烧钱」「哪次 prompt 改动让成本翻倍」（见 [缓存与成本优化](caching-cost-optimization.md)）。

## 选型对比

| 方案 | 类型 | 优势 | 适合 |
|---|---|---|---|
| [LangSmith](https://docs.smith.langchain.com/) | SaaS | 与 LangChain 无缝、评估/数据集/实验管理一体 | LangChain/LangGraph 深度用户 |
| [LangFuse](https://github.com/langfuse/langfuse) | 开源（MIT 核心） | 自托管、成本追踪细、多语言 SDK | 要数据主权 + 全框架 |
| [Phoenix](https://github.com/Arize-ai/phoenix) | 开源 | RAG 评估强、trace 可视化 | RAG 重度项目 |
| [OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | 协议标准 | 厂商中立、接企业现有观测栈 | 大企业统一观测 |

## LangFuse 接入示例（Python）

```python
from langfuse.openai import openai   # 一行替换, 自动 trace

client = openai.OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "解释 MCP"}],
    metadata={"trace_id": task_id},   # 关联业务任务
)
```

## 源码案例

- **Claude Code 的 OTel 支持**（[官方文档](https://docs.anthropic.com/en/docs/claude-code)）：企业可把使用指标、工具调用统计导出到自有 OTel 后端——「开发工具也要接企业观测」的行业信号
- **LangFuse 的成本追踪**（[GitHub](https://github.com/langfuse/langfuse)）：按模型/用户/会话聚合 token 与费用，读它的用量计算逻辑可理解成本归因设计
- **Phoenix 的 RAG 评估视图**（[GitHub](https://github.com/Arize-ai/phoenix)）：检索命中与生成质量的联合 trace 视图——调试「答非所问」时能直接看到是「检索就错了」还是「生成跑偏了」

## 落地清单

- [ ] 每条 trace 带业务维度：user_id、tenant、task_type、prompt/模型版本
- [ ] 错误与超时 trace 全留，成功请求采样
- [ ] 失败 trace 自动归档并附错误分类标签
- [ ] 周报指标：任务成功率、P95 延迟、单任务成本、Top 失败模式
- [ ] trace → 评估集的回流流水线（见 [持续评估](continuous-evaluation.md)）

## 常见误区

- ❌ 观测工具 = 接个 SDK 完事：没有业务维度标注的 trace 无法定位「哪类用户受影响」
- ❌ 全量采集：trace 里含完整 prompt 与工具输出，成本会失控
- ❌ SaaS 观测不计隐私成本：prompt 可能含 PII，要看厂商数据处理协议，或本地脱敏后再上报
- ❌ 只看单次 trace：价值在聚合——Top 失败模式、成本分布、慢步骤排名
- ❌ 自定义属性名：脱离 OTel 语义约定会锁死后端选择

## 小练习

为你的 Agent 选观测方案并说明决策链（数据主权？现有栈？评估需求？），设计 trace 的维度与采样策略，然后接入选型方案跑一周，输出一份「Top3 失败模式 + 成本 Top3 功能」报告。

## 参考资料

- [OpenTelemetry GenAI 语义约定](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [LangFuse](https://github.com/langfuse/langfuse) / [Phoenix](https://github.com/Arize-ai/phoenix) / [LangSmith](https://docs.smith.langchain.com/)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

## 相关知识点

- [日志、追踪与监控](logging-tracing-monitoring.md)
- [持续评估](continuous-evaluation.md)
- [缓存与成本优化](caching-cost-optimization.md)
