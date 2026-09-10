---
tags: [engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 🚀 日志、追踪与监控

> **一句话**：Agent 可观测三件套：结构化日志（发生了什么）、分布式追踪（一次任务的完整链路）、业务监控（成功率和成本曲线）——没有它们，线上问题等于盲猜。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#engineering`

## 📌 先看结论

- Agent 的追踪单位是「一次任务运行」：从用户输入到最终输出的完整轨迹（含每步 prompt、工具调用、token 消耗）
- 事件流架构（append-only 日志）让日志与 trace 合二为一：DSH 的会话日志本身就是可回放的 trace
- 监控要有 Agent 特有指标：任务成功率、平均步数、工具错误率、注入拦截数、单任务成本分布
- PII 进日志前脱敏；trace 保留期限与采样率要定义（全量存成本极高）

## 🧩 三件套分工

| 组件 | 回答的问题 | 落地 |
|---|---|---|
| 日志 | 某一步发生了什么 | 结构化 JSON 事件流 |
| 追踪 | 一次任务全链路 | trace_id 贯穿 + span 层级 |
| 监控 | 系统整体健康 | 指标看板 + 告警 |

## 💻 结构化事件示例

```json
{
  "ts": "2026-09-10T09:30:21Z",
  "trace_id": "task-8f3a",
  "span": "tool_call",
  "agent": "worker-2",
  "tool": "search_docs",
  "args": {"q": "退款政策"},
  "latency_ms": 412,
  "tokens": {"in": 1830, "out": 240},
  "status": "ok"
}
```

## 📦 源码案例

- **DeepSeek Harness：trace 即架构**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：每个事件带 seq 序号与来源（模型/工具/子 Agent/注入），Trajectory 视图按来源过滤——「排查一次失败」= 在事件流上按时间轴重放，无需额外 trace 系统
- **Claude Code 的可观测细节**（逆向分析）：请求级 token 统计与 USD 预算提醒（System Reminder 机制）直接进上下文告知模型——「可观测」甚至喂给 Agent 自己做预算决策；OTel 支持可外接企业观测栈
- **LangFuse 的会话视图**（→ [observability-tools](observability-tools.md)）：trace 按会话聚合、每步显示 prompt 版本与评分——把「评估」也纳入观测闭环
- **OpenTelemetry GenAI 语义约定**（[OTel 文档](https://opentelemetry.io/docs/specs/semconv/gen-ai/)）：正在形成的 LLM 追踪标准（`gen_ai.*` 属性族），选工具时认准兼容性

## ✅ 最佳实践

- trace_id 在入口生成，贯穿模型调用/工具/子 Agent 全链路
- 告警三层：可用性（服务挂）、质量（成功率跌破阈值）、成本（日 token 超预算）
- 每个失败 trace 一键转评估用例（→ [持续评估](continuous-evaluation.md)）——观测与评估闭环

## ⚠️ 常见误区

- ❌ print 调试上生产：非结构化日志无法检索聚合，出事后翻日志像考古
- ❌ 全量记录全量保存：采样 + 分级保留（失败 trace 全存、成功按比例）
- ❌ 只监控技术指标：任务成功率下跌 5% 比延迟抖动重要得多，业务指标才是北极星

## 🧪 小练习

给你的 Agent 加 trace：定义 span 层级（agent_turn → llm_call / tool_call），接入任一观测工具，找出当前「token 成本 Top3 的步骤」。

## 📚 相关知识点

- [LangSmith、LangFuse、Phoenix、OpenTelemetry](observability-tools.md)
- [状态机与事件驱动](state-machine-event-driven.md)
