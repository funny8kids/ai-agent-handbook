---
tags: [engineering, infrastructure, advanced]
type: index
status: published
updated: 2026-09-10
---

# 16 AI 基础设施

> **一句话**：Agent 产品的体验上限，往往不在 prompt，而在基础设施——推理引擎决定「多快多贵」，缓存决定「上下文能做多长」，沙箱决定「你敢让 Agent 干什么」，网关与运行时决定「崩了能不能救回来」。

## 先看结论

- **一次 LLM 调用 = 两个瓶颈相反的阶段**：prefill（算力瓶颈，决定 TTFT）与 decode（显存带宽瓶颈，决定 TPOT）。所有推理优化都在对付这两件事，选型前先问自己卡在哪个。
- **缓存是 Agent 的隐形成本杠杆**：Agent 每轮都重发同一份长前缀（system + 工具 + 历史），前缀缓存命中率能把输入成本砍掉一半以上——所以「稳定前缀 + 只追加尾部」是工程纪律，不是微优化。
- **工具执行必须有隔离层**：Agent 会执行模型现写的代码，这等于把 shell 交给一个不可信的实习生。沙箱（容器 / gVisor / microVM）+ 出口网络白名单是底线配置。
- **长任务需要 durable 运行时**：一次跑 40 分钟的 Agent，用「进程内存里 for 循环」必然被一次重启全量报废。checkpoint / 事件重放 / 幂等工具调用是运行时的事，不是业务代码的事。
- **本章面向「要上线的人」**：每页都有选型表 + 可跑的验收动作（压测脚本、命中率观测、故障演练）。

## 技术栈分层地图

| 层 | 解决什么 | 代表方案 | 页面 |
|---|---|---|---|
| ① 推理引擎 | 吞吐 / 延迟 / 显存 | vLLM、SGLang、TensorRT-LLM、LMDeploy、llama.cpp | [推理服务化](inference-serving.md) |
| ② 缓存与上下文 | 重复 prefill、长上下文成本 | PagedAttention、RadixAttention、Prompt Caching | [前缀缓存与上下文工程](prefix-cache-context-engineering.md) |
| ③ 算力与调度 | GPU 分给谁、怎么弹性 | K8s + device plugin / DRA、MIG、Ray、KEDA | [GPU 调度与多租户](gpu-scheduling-multitenancy.md) |
| ④ 训练与微调 | 私有模型、行为定制 | LoRA/QLoRA、FSDP/DeepSpeed、RL/DPO 流水线 | [训练与微调基础设施](training-finetune-infra.md) |
| ⑤ 执行环境 | 安全地跑代码与浏览器 | Docker、gVisor、Firecracker、E2B/Modal | [沙箱与执行环境](sandbox-execution-environments.md) |
| ⑥ 模型接入 | 统一 API、路由、配额、审计 | LiteLLM、Envoy AI Gateway、OpenRouter | [模型网关与路由](model-gateway.md) |
| ⑦ Agent 运行时 | 状态、恢复、并发、重放 | Temporal、Restate、LangGraph checkpoint、队列 | [持久化执行与运行时](agent-runtime-durable-execution.md) |
| ⑧ 数据与检索 | 语料、向量、索引、飞轮 | 对象存储、pgvector/Qdrant/Milvus、湖仓 | [数据与检索基础设施](data-vector-storage.md) |
| ⑨ 可观测与评估 | 知道慢在哪、错在哪 | OTel GenAI、Langfuse、离线评估集、回放 | [可观测性与评估平台](llm-observability-eval-platform.md) |
| ⑩ 成本与形态 | 自研还是买 API | token 经济学、端侧/本地、量化蒸馏 | [推理经济学与部署形态](inference-economics-deployment.md) |

## 动态图示

本章配了三张可动的 SVG（点开页面即可看到动画，仓库文件：`docs/assets/diagrams/`）：

| 图示 | 说明 |
|---|---|
| [连续批处理 vs 静态批处理](../assets/diagrams/16-continuous-batching.svg) | 为什么 decode 阶段 GPU 会被「等最长的那条」拖空 |
| [前缀缓存命中与重算范围](../assets/diagrams/16-prefix-cache.svg) | Agent 多轮对话里，缓存能省掉哪一段、什么改动会让它整段失效 |
| [沙箱分层与出口闸门](../assets/diagrams/16-sandbox-layers.svg) | 一次工具调用穿过 runc / gVisor / microVM 与网络白名单的过程 |

## 阅读建议

- **只想跑起来**：[模型网关](model-gateway.md) → [沙箱](sandbox-execution-environments.md) → [可观测](llm-observability-eval-platform.md)
- **自建推理 / 私有化**：[推理服务化](inference-serving.md) → [GPU 调度](gpu-scheduling-multitenancy.md) → [推理经济学](inference-economics-deployment.md)
- **做平台给别人的 Agent 用**：全部，重点 [持久化执行](agent-runtime-durable-execution.md)
- 与 [11 工程化与可观测性](../11-engineering/README.md) 的分工：11 章讲「应用侧怎么写」，本章讲「下面的平台怎么搭」

## 相关知识点

- [缓存与成本优化](../11-engineering/caching-cost-optimization.md)
- [部署与弹性伸缩](../11-engineering/deployment-scaling.md)
- [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)
- [推理、量化、蒸馏与部署](../03-llm/inference-quantization-deployment.md)
- [17 具身智能](../17-embodied-ai/README.md)（把同一套栈搬到物理世界的形态）
