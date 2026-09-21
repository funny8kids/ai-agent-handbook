---
tags: [engineering]
type: index
status: published
updated: 2026-09-20
---

# 11 工程化与可观测性

{% hint style="info" %}
**一句话**：从 Demo 到生产隔着一条工程鸿沟：编排、状态机、工具注册、追踪监控、错误处理、部署扩容、成本优化、持续评估——本章就是过桥的图纸。
{% endhint %}

## 你将学到

- Agent 生产架构的参考分层与模式选择
- 状态机与事件驱动：为什么「append-only 事件流」正在成为主流
- 工具注册中心：工具的版本、鉴权与生命周期管理
- LangSmith/LangFuse/Phoenix/OpenTelemetry 的选型与落地
- 错误处理、部署扩缩容、缓存成本与持续评估的工程清单

## 一张参考架构

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#F9E9FB","primaryBorderColor":"#C026D3","primaryTextColor":"#1F2937","secondaryColor":"#F1CFF5","tertiaryColor":"#FCF6FD","lineColor":"#DC88E7","actorBkg":"#FAEEFB","actorBorder":"#C026D3","actorTextColor":"#1F2937","signalColor":"#D367E0","noteBkgColor":"#F4D8F7","noteBorderColor":"#C026D3","noteTextColor":"#1F2937","labelBoxBkgColor":"#F9E9FB","labelBoxBorderColor":"#C026D3"}}}%%
flowchart TB
  U[客户端] --> GW[网关/鉴权/限流]
  GW --> ORCH[编排层<br/>状态机/队列]
  ORCH --> AG[Agent 运行时<br/>循环+工具]
  AG --> LLM[模型层<br/>缓存/路由/降级]
  AG --> T[工具层<br/>注册中心/沙箱]
  AG --> OBS[可观测层<br/>trace/指标/审计]
  ORCH --> S[(状态存储<br/>事件流)]
```

## 延伸必读

- [12-Factor Agents](https://github.com/humanlayer/12-factor-agents)——Agent 工程化的 12 条原则，本章多个小节与之呼应
- [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)——编排模式的工程共识

## 本站页面

- [Agent 工作流编排](workflow-orchestration.md)
- [状态机与事件驱动](state-machine-event-driven.md)
- [工具注册中心](tool-registry.md)
- [日志、追踪与监控](logging-tracing-monitoring.md)
- [LangSmith、LangFuse、Phoenix、OpenTelemetry](observability-tools.md)
- [错误处理、重试与降级](error-handling-retry-fallback.md)
- [部署与扩缩容](deployment-scaling.md)
- [缓存与成本优化](caching-cost-optimization.md)
- [持续评估](continuous-evaluation.md)

## 读完能做到

- [ ] 定义 5 个核心事件类型（user_input / assistant_message / tool_call / tool_result / turn_end），实现「从事件重放出当前上下文」，并加一个每 20 事件生成快照的机制
- [ ] 给 Agent 加 trace：定义 span 层级（agent_turn→llm_call/tool_call），按四个黄金信号建一版看板，并找出当前 token 成本 Top3 的步骤
- [ ] 用成本公式估算单任务成本，说清为什么缓存命中要求「前缀字节级一致」、动态内容为什么要后置到 prompt 尾部
- [ ] 画出完整降级链（主模型→备模型→缩水任务→人工信箱），每级写触发条件与用户话术，并解释非幂等操作为什么绝不自动重试
- [ ] 为核心评估集做规模测算：n=100、p=0.9 时 95% 置信区间约 ±6pp，据此判断能否分辨 92% 与 88%

## 章末自测

1. **回忆**：事件溯源为什么要求 fold（投影）是纯函数？哪些「不确定输入」必须也写成事件？（提示：见 state-machine-event-driven.md）
2. **应用**：为什么「只监控 CPU 和延迟」是错的？哪个指标才是 Agent 的北极星，最早的退化信号又是什么？（提示：见 logging-tracing-monitoring.md）
3. **判断**：「自托管一定比 API 省钱」「小模型单价低所以一律用小模型」——用总账公式和「失败重试反而更贵」的成本—质量权衡各反驳一句。（提示：见 caching-cost-optimization.md、deployment-scaling.md）

## 本章术语速查

工程化黑话大半是从分布式系统和体检室借来的，见过原词之后，会发现它们比中文译名还亲切些。

| 英文术语 | 中文 | 白话一句话 |
|---|---|---|
| Event Sourcing | 事件溯源 | 不记「现在是什么」，记每一步「发生了什么」；想恢复现场，把事件流从头放一遍就行。 |
| Append-only | 只追加 | 账本只能往后写、从不改旧账；写错了？再追加一条更正事件，错账原样留着当证据。 |
| Reducer | 投影函数 | 把事件流「压缩」成当前状态的那个纯函数，同样的事件重放必须得同样的结果，不然恢复就成开盲盒。 |
| Trace | 调用链路 | 一次任务从用户进来货到最终答案出去的全过程收据。 |
| Span | 链路中的一节 | 收据上的分项条目：这段是调模型，那段是调工具，各自带起止时间和花费。 |
| OpenTelemetry | 开放遥测标准 | 行业统一的埋线尺子，大家照同一套规范装仪表，监控后台想换就换。 |
| P95 | 95 分位延迟 | 95% 的请求都比这个值快；看的是倒霉的那 5%，平均值会骗人，分位数不会。 |
| CircuitBreaker | 熔断器 | 连续失败就拉闸止损，冷却一阵再放个探路请求试试；别让一个卡住的下游被锤到死。 |
| Fallback | 降级 | 主模型挂了换备模型，备模型不行就砍任务范围，再不行投人工信箱——提前铺好的一整条退路。 |
| Prompt caching | 提示词缓存 | 开头一模一样的内容每轮重发，模型认得就不重复算钱；所以往开头塞个时间戳，整段缓存全白费。 |
| Checkpoint | 检查点 | 长任务走一段存个档，崩了从存档点接着跑，而不是从头再来一遍。 |

