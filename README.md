<div align="center">

# AI Agent 手册 · AI Agent Handbook

**从原理到生产**：LLM 与注意力 · Agent 循环 · 工具协议 · 记忆与 RAG · 规划 · 多智能体 · 评估与安全 · 工程化 · AI 基础设施 · 具身智能 · 2026 前沿

**From theory to production**: LLMs & attention · agent loops · tool protocols · memory & RAG · planning · multi-agent · evaluation & safety · engineering · AI infrastructure · embodied AI · 2026 frontier

<a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-7C3AED?style=flat-square"></a>
<img alt="Pages" src="https://img.shields.io/badge/pages-178-8B5CF6?style=flat-square">
<img alt="Chapters" src="https://img.shields.io/badge/chapters-18-6D28D9?style=flat-square">
<img alt="Projects" src="https://img.shields.io/badge/indexed%20projects-323-4C1D95?style=flat-square">
<img alt="Math" src="https://img.shields.io/badge/pages%20with%20math-93-A78BFA?style=flat-square">

</div>

---

> **中文**：一本持续更新的开源 AI Agent 手册与资源库：178 页 / 18 章。每一页都要求「把话说实」——原理给出公式与推导、结论给出可点开的出处、案例给出真实源码路径，不做"听起来对"的泛泛之谈。
>
> **English**: A continuously updated, open-source AI Agent handbook and resource library — 178 pages across 18 chapters. Every page has to show its work: principles come with formulas and derivations, claims link to primary sources, and case studies point at real source paths.

在线阅读（GitBook 站点）· Read online on GitBook: **VioletNotes Docs**

---

## 2026 前沿 · Frontier（2026-09）

| 主题 | 页面 |
|---|---|
| GPT-6 Astra · Claude Fable 5.1 / Opus 5 | [前沿模型地图](docs/18-frontier-2026/frontier-models-2026.md) |
| OpenAI Agents API（托管 Codex harness） | [Agents API](docs/18-frontier-2026/openai-agents-api.md) |
| Claude Agent SDK | [Agent SDK](docs/18-frontier-2026/claude-agent-sdk.md) |
| 模型原生 harness vs 自建循环 | [分类学](docs/18-frontier-2026/model-native-vs-harness.md) |
| Terminal-Bench 4.0 · OSWorld 2.0 读法 | [评估 2026](docs/18-frontier-2026/eval-2026.md) |
| 真实事故与 misalignment monitoring | [安全 2026](docs/10-evaluation-safety/safety-incidents-2026.md) |

---

## 快速开始 · Quick start

| 你是 · You are | 路线 · Route | 通关标准 · Done when |
|---|---|---|
| 只会用 ChatGPT · New to LLMs | 01 → 02 → 03 → 04 | 能讲清「Agent 与 Chatbot 的区别」· explain agent vs chatbot |
| 有开发经验 · Engineer | 02 → 05 → 06 → 09 → 11 | 能写出会调工具、能恢复错误的 Agent · ship an agent with tools & recovery |
| 关注前沿与论文 · Researcher | 04 → 08 → 10 | 能读懂 ReAct 并复现核心循环 · reproduce the ReAct loop |
| 要搭团队底座 · Platform / Infra | 03 → 11 → 16 | 能给出 TTFT/TPOT/缓存命中率/成本基线 · set cost & latency baselines |
| 做机器人或想转具身 · Robotics | 02 → 04 → 17 → 16 | 能跑通「感知→技能→执行」闭环 · close a perceive→skill→act loop |
| 追前沿与选型 · Frontier / Buyer | 02 → 18 → 10 → 12 | 能读懂 Astra / Agents API / Fable 5.1 对比并做 harness 选型 · pick a 2026 stack |

完整路线与自检标准 · Full paths & self-checks：**[学习路线 Learning path](docs/00-index/learning-path.md)**

---

## 必读 12 个 · Top 12 must-reads

| 资源 · Resource | 一句话 · In one line | 类型 · Type |
|---|---|---|
| [ReAct](https://arxiv.org/abs/2210.03629) | 现代 Agent 循环的思想源头：想一步、做一步、看结果 · the origin of the think-act-observe loop | 论文 Paper |
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | 什么时候用工作流、什么时候才该上 Agent · when to use a workflow vs an agent | 博客 Blog |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | Transformer 原始论文，一切 LLM 的底座 · the paper every LLM builds on | 论文 Paper |
| [DeepSeek-R1](https://arxiv.org/abs/2501.12948) | 用可验证奖励做 RL，训出推理能力 · RL with verifiable rewards for reasoning | 论文 Paper |
| [Pi Agent](https://github.com/earendil-works/pi) | 极简 harness 的活教材 · a minimal harness you can read end to end | 开源 Project |
| [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) | 「一切皆插件」的生产级运行时 · a runtime where everything is a plugin | 开源 Project |
| [Claude Code 系统提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts) | 生产级 Agent 的提示词、工具描述与权限约束怎么写 · how real prompts & tool specs are written | 源码 Source |
| [MCP 官方文档](https://modelcontextprotocol.io/docs/learn/architecture) | 工具接入的事实标准：Tools / Resources / Prompts · the de-facto tool protocol | 文档 Docs |
| [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) | 系统化的免费入门课程 · a free, structured beginner course | 课程 Course |
| [SWE-bench](https://www.swebench.com/) | 编程 Agent 的标准考场：真实 issue + 测试判分 · the standard arena for coding agents | 基准 Benchmark |
| [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) | Agent 工程化的 12 条原则 · 12 principles for production agents | 文章 Article |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | 全功能开源编程 Agent（原 OpenDevin）· full-featured open-source coding agent | 开源 Project |

---

## Agent 框架与编排 · Frameworks & Orchestration

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 集成生态最大的 LLM 应用框架，组件统一抽象 · the largest integration ecosystem with a unified component abstraction | 14.6 万 |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 用状态图表达 Agent：分支、循环、checkpoint、人工介入 · express agents as stateful graphs | 4.1 万 |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | 把 prompt 变成「编译产物」，用指标自动优化 · compile prompts instead of hand-writing them | 3.8 万 |
| [ComposioHQ/composio](https://github.com/ComposioHQ/composio) | 1000+ 工具集成、工具检索、鉴权与沙箱 · 1000+ tools with search, auth and sandboxing | 3.0 万 |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 少抽象的生产级 Agent SDK：handoff / guardrail / session · a lean production SDK | 2.9 万 |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | 极简 Agent 库，主张「让模型用代码思考」· a barebones library: agents that think in code | 2.9 万 |
| [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) | 微软企业级 SDK：Kernel + Plugin + 依赖注入 · Microsoft's enterprise SDK | 2.9 万 |
| [google/adk-python](https://github.com/google/adk-python) | Google 的代码优先 Agent 工具包 · Google's code-first agent toolkit | 2.1 万 |

延伸 · More：[框架与生态 Frameworks](docs/09-frameworks/README.md) · [LangChain](docs/09-frameworks/langchain.md) · [LangGraph](docs/09-frameworks/langgraph.md) · [DSPy](docs/09-frameworks/dspy.md)

## 编程 Agent 与 Harness · Coding Agents & Harnesses

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | turn/step 状态机 + append-only 事件流的插件化 harness · an event-sourced, fully pluggable harness | 21.9 万 |
| [openai/codex](https://github.com/openai/codex) | OpenAI 开源终端编程 Agent（Rust）· an open-source terminal coding agent | 12.3 万 |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | Google 开源终端 Agent · Google's open terminal agent | 10.7 万 |
| [earendil-works/pi](https://github.com/earendil-works/pi) | 极简 harness：提供原语而非成品（原 `badlogic/pi-mono`）· primitives, not a finished product | 10.4 万 |
| [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | 全功能开源编程 Agent · a full-featured open-source coding agent | — |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 提出 ACI（Agent-Computer Interface）设计学 · pioneered the agent-computer interface | — |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 轻量结对编程，repo-map 上下文方案 · lightweight pair programming | — |
| [block/goose](https://github.com/block/goose) | 可扩展的本地 Agent · an extensible local agent | — |
| [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Claude Code 提示词全集（社区逆向）· a reverse-engineered prompt collection | — |

延伸 · More：[编程 Agent 案例 Coding agents](docs/12-applications/coding-agent.md) · [工具调用与协议 Tool protocol](docs/05-tool-protocol/README.md)

## 多智能体 · Multi-Agent

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) | 「软件公司」多角色协作范式 · a multi-role "software company" | 7.0 万 |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 对话式多 Agent 框架，GroupChat 开创者 · the GroupChat pioneer | 6.1 万 |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 角色化协作：Agent / Task / Crew / Process · role-based declarative teams | 5.8 万 |
| [OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev) | 多 Agent 协作软件开发 · multi-agent software development | 3.4 万 |
| [openai/swarm](https://github.com/openai/swarm) | handoff 模式的教学级实现 · a teaching-grade handoff implementation | 2.2 万 |
| [VRSEN/agency-swarm](https://github.com/VRSEN/agency-swarm) | 基于 OpenAI Agents SDK 的多 Agent 编排 · orchestration on top of the Agents SDK | 4,555 |

延伸 · More：[多智能体 Multi-agent](docs/08-multi-agent/README.md) · [监督者模式 Supervisor](docs/08-multi-agent/supervisor-pattern.md) · [辩论与投票 Debate & voting](docs/08-multi-agent/debate-consensus-voting.md)

## 记忆与 RAG · Memory & RAG

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [langgenius/dify](https://github.com/langgenius/dify) | LLM 应用与 RAG 平台，可视化编排 · a visual platform for LLM apps & RAG | 15.5 万 |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 深度文档理解的 RAG 引擎 · a RAG engine with deep document understanding | 9.0 万 |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Agent 长期记忆层 · a long-term memory layer for agents | 6.5 万 |
| [run-llama/llama_index](https://github.com/run-llama/llama_index) | RAG 管线专家：连接器矩阵 + 句窗/自动合并 · the RAG pipeline specialist | 5.2 万 |
| [milvus-io/milvus](https://github.com/milvus-io/milvus) | 分布式向量数据库（亿级）· a distributed vector database | 4.6 万 |
| [facebookresearch/faiss](https://github.com/facebookresearch/faiss) | 向量检索算法库，多数向量库的底层引擎 · the ANN library under many vector DBs | 4.1 万 |
| [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | 轻量 GraphRAG 替代 · a lighter GraphRAG | 4.0 万 |
| [microsoft/graphrag](https://github.com/microsoft/graphrag) | 社区检测 + 分层摘要，解决「全局归纳」· community summaries for global questions | — |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | 过滤式检索体验最好的向量库 · filtered ANN search done right | — |
| [pgvector/pgvector](https://github.com/pgvector/pgvector) | PostgreSQL 向量扩展，千万级以内最省事 · vectors inside Postgres | — |
| [weaviate/weaviate](https://github.com/weaviate/weaviate) | 模块化向量库，内置混合检索 · a modular vector DB with hybrid search | — |
| [chroma-core/chroma](https://github.com/chroma-core/chroma) | 十行代码起步的轻量向量库 · the quickest way to get started | — |

延伸 · More：[记忆与 RAG Memory & RAG](docs/06-memory-rag/README.md) · [RAG 基础](docs/06-memory-rag/rag-basics.md) · [向量数据库 Vector DB](docs/06-memory-rag/vector-database.md) · [GraphRAG](docs/06-memory-rag/graphrag.md)

## 工具与协议 · Tools & Protocols (MCP / A2A)

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 官方 MCP Server 参考实现 · official reference MCP servers | 9.0 万 |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | MCP 官方 Python SDK · the official MCP SDK for Python | 2.4 万 |
| [QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | 带 Function Calling / MCP / Code Interpreter 的框架 · function calling, MCP, code interpreter | 1.7 万 |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | MCP 官方 TypeScript SDK · the official MCP SDK for TypeScript | 1.3 万 |
| [a2aproject/A2A](https://github.com/a2aproject/A2A) | Agent-to-Agent 协议：Agent Card + Task 生命周期 · the agent-to-agent protocol | — |

延伸 · More：[MCP](docs/05-tool-protocol/mcp.md) · [A2A](docs/05-tool-protocol/a2a.md) · [Function Calling](docs/05-tool-protocol/function-calling.md) · [工具权限与沙箱 Sandboxing](docs/05-tool-protocol/tool-permission-sandbox.md)

## 浏览器与 Computer Use · Browser & Computer Use

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 视觉 + DOM 混合浏览器 Agent · a vision + DOM browser agent | 11.4 万 |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 把浏览器操作标准化为 MCP 工具 · browser actions as MCP tools | 3.7 万 |
| [browserbase/stagehand](https://github.com/browserbase/stagehand) | 浏览器 Agent 的 SDK · an SDK for browser agents | 2.4 万 |
| [trycua/cua](https://github.com/trycua/cua) | Computer Use 的开源驱动与跨系统机群 · open drivers for computer use | 2.2 万 |
| [e2b-dev/open-computer-use](https://github.com/e2b-dev/open-computer-use) | 开源 LLM 驱动的计算机操作 · computer use powered by open LLMs | 2,249 |
| [Anthropic: Computer Use](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use) | 截图 → 定位 → 操作的标准范式 · the canonical screenshot-act loop | 文档 Docs |

延伸 · More：[Computer Use / Browser Use](docs/05-tool-protocol/computer-use-browser-use.md) · [浏览器自动化 Browser automation](docs/12-applications/browser-automation.md)

## 可观测、评估与安全 · Observability, Evaluation & Safety

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | 开源 LLM 可观测：trace、成本、评估、prompt 管理 · OSS observability, self-hostable | 3.4 万 |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | prompt 回归测试，YAML 定义用例矩阵 · prompt regression testing | 2.5 万 |
| [comet-ml/opik](https://github.com/comet-ml/opik) | 开源 LLM 评估与追踪平台 · an OSS evaluation & tracing platform | 2.2 万 |
| [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | RAG 评估强、trace 可视化 · strong RAG evaluation and traces | 1.1 万 |
| [explodinggradients/ragas](https://github.com/explodinggradients/ragas) | RAG 专项评估：忠实度、相关性 · RAG-specific metrics | — |
| [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) | Llama Guard 等安全分类模型 · safety classifiers such as Llama Guard | — |
| [OpenTelemetry GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | 厂商中立的 LLM 追踪标准 · vendor-neutral tracing conventions | 标准 Standard |

延伸 · More：[评估、安全与对齐 Evaluation & safety](docs/10-evaluation-safety/README.md) · [评估指标 Metrics](docs/10-evaluation-safety/evaluation-metrics.md) · [提示注入 Prompt injection](docs/10-evaluation-safety/prompt-injection.md) · [越狱 Jailbreak](docs/10-evaluation-safety/jailbreak.md)

## 推理与部署 · Inference & Deployment

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [ollama/ollama](https://github.com/ollama/ollama) | 一行命令本地跑大模型 · run LLMs locally in one command | 18.1 万 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | 纯 C/C++ 推理引擎，GGUF 量化事实标准 · C/C++ inference, the GGUF standard | 12.8 万 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | PagedAttention + 连续批处理，自托管首选 · the default self-hosting backend | 9.1 万 |
| [unslothai/unsloth](https://github.com/unslothai/unsloth) | 微调加速，显存大幅降低 · faster fine-tuning, less VRAM | 7.6 万 |
| [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) | 100+ 模型的统一微调框架 · unified fine-tuning for 100+ models | 7.5 万 |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | 多模型统一网关：路由、配额、成本记账 · one gateway for many models | 5.8 万 |
| [huggingface/trl](https://github.com/huggingface/trl) | SFT / DPO / PPO 训练工具箱 · SFT, DPO and PPO trainers | 1.9 万 |

延伸 · More：[推理与部署 Inference & deployment](docs/03-llm/inference-quantization-deployment.md) · [AI 基础设施 AI infrastructure](docs/16-ai-infrastructure/README.md)

## 沙箱与运行时 · Sandboxes & Runtimes

| 项目 · Project | 说明 · What it is | Star |
|---|---|---|
| [firecracker-microvm/firecracker](https://github.com/firecracker-microvm/firecracker) | AWS Lambda 同款 microVM，强隔离启动快 · microVMs with strong isolation | 3.7 万 |
| [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | 面向 Agent 的代码执行沙箱 · code-execution sandboxes for agents | 1.4 万 |
| [agent-infra/sandbox](https://github.com/agent-infra/sandbox) | 浏览器 + Shell + 文件 + MCP 一体化沙箱 · an all-in-one agent sandbox | 5,883 |

延伸 · More：[工具权限与沙箱 Sandboxing](docs/05-tool-protocol/tool-permission-sandbox.md) · [权限控制与沙箱隔离 Permissions](docs/10-evaluation-safety/permission-sandbox.md)

## 基准与数据集 · Benchmarks & Datasets

| 基准 / 数据集 · Benchmark / Dataset | 考什么 · What it measures | 链接 · Link |
|---|---|---|
| SWE-bench | 真实 GitHub issue 修复 · real issue resolution | [swebench.com](https://www.swebench.com/) · [精读 Read](docs/13-resources/benchmarks/swe-bench.md) |
| GAIA | 通用助理任务（多步推理 + 工具）· general assistant tasks | [Hugging Face](https://huggingface.co/datasets/gaia-benchmark/GAIA) · [精读 Read](docs/13-resources/benchmarks/gaia.md) |
| WebArena | 真实网站长程任务 · long-horizon web tasks | [webarena.dev](https://webarena.dev/) · [精读 Read](docs/13-resources/benchmarks/webarena.md) |
| AgentBench | 八场景综合能力 · eight environments | [GitHub](https://github.com/THUDM/AgentBench) |
| ToolBench / BFCL | 工具调用与选择 · tool calling and selection | [BFCL 榜单 Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard) |
| τ-bench | 工具 + 用户模拟 + 策略遵守 · tool-agent-user interaction | [GitHub](https://github.com/sierra-research/tau-bench) |
| OSWorld | 真实桌面环境操作 · real desktop environments | [os-world.github.io](https://os-world.github.io/) |
| Terminal-Bench | 终端任务 · terminal tasks | [tbench.ai](https://www.tbench.ai/) |

延伸 · More：[基准测试总览 Benchmarks](docs/10-evaluation-safety/benchmarks.md) · [五大基准精读 Five benchmarks](docs/10-evaluation-safety/agentbench-webarena-swebench-gaia-toolbench.md) · [数据集 Datasets](docs/13-resources/datasets/README.md)

## 论文（按主题）· Papers by topic

| 主题 · Topic | 论文 · Papers |
|---|---|
| 架构基础 · Architecture | [Attention Is All You Need](https://arxiv.org/abs/1706.03762) · [DeepSeek-V3 (MLA + MoE)](https://arxiv.org/abs/2412.19437) |
| 推理与提示 · Reasoning & prompting | [Chain-of-Thought](https://arxiv.org/abs/2201.11903) · [Self-Consistency](https://arxiv.org/abs/2203.11171) · [Tree of Thoughts](https://arxiv.org/abs/2305.10601) · [Graph of Thoughts](https://arxiv.org/abs/2308.09687) |
| Agent 循环 · Agent loops | [ReAct](https://arxiv.org/abs/2210.03629) · [Reflexion](https://arxiv.org/abs/2303.11366) · [Self-Refine](https://arxiv.org/abs/2303.17651) · [Toolformer](https://arxiv.org/abs/2302.04761) |
| 对齐与训练 · Alignment & training | [InstructGPT / RLHF](https://arxiv.org/abs/2203.02155) · [DPO](https://arxiv.org/abs/2305.18290) · [LoRA](https://arxiv.org/abs/2106.09685) · [DeepSeek-R1](https://arxiv.org/abs/2501.12948) |
| 检索与记忆 · Retrieval & memory | [RAG](https://arxiv.org/abs/2005.11401) · [DPR](https://arxiv.org/abs/2004.04906) · [GraphRAG](https://arxiv.org/abs/2404.16130) · [MemGPT](https://arxiv.org/abs/2310.08560) · [HNSW](https://arxiv.org/abs/1603.09320) |
| 评估与安全 · Evaluation & safety | [SWE-bench](https://arxiv.org/abs/2310.06770) · [GAIA](https://arxiv.org/abs/2311.12983) · [RAGAS](https://arxiv.org/abs/2309.15217) · [GCG jailbreak](https://arxiv.org/abs/2307.15043) · [Indirect prompt injection](https://arxiv.org/abs/2302.12173) |

## 课程、博客与社区 · Courses, Blogs & Communities

| 资源 · Resource | 说明 · What it is |
|---|---|
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | 微软官方免费课程（7.4 万 star）· Microsoft's free course |
| [Hugging Face Agents Course](https://huggingface.co/learn/agents-course) | 开源 Agent 认证课程 · an open agent course |
| [LangChain Academy](https://academy.langchain.com) | 官方免费课，含 Deep Research 实现 · free courses incl. deep research |
| [DeepLearning.AI 短课 Short courses](https://www.deeplearning.ai/courses/) | Agents / LangGraph / RAG 系列 · agents, LangGraph, RAG |
| [dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | 提示工程系统指南（7.8 万 star）· the systematic prompting guide |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | MCP Server 大合集（9.5 万 star）· the MCP server collection |
| [Anthropic 工程博客 Engineering blog](https://www.anthropic.com/engineering) | 多 Agent、工具设计、上下文工程的一手经验 · first-hand engineering write-ups |
| [Lilian Weng](https://lilianweng.github.io/) | 「LLM Powered Autonomous Agents」是 Agent 综述经典 · the classic agent survey |
| [Simon Willison](https://simonwillison.net/) | 提示注入与 LLM 安全的最佳追踪源 · the best tracker for prompt injection & safety |
| [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/) · [HF Discord](https://hf.co/join/discord) · [LangChain Forum](https://forum.langchain.com/) · [MCP Discussions](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions) | 提问与讨论 · ask questions and discuss |

---

## 许可证 · License

[MIT](LICENSE) © AI Agent Handbook

<sub>本页资源均指向一手来源；star 与许可为 2026-09 观测值，会随时间变化。· All resources link to primary sources; star counts and licenses were observed in 2026-09 and will change over time.</sub>

<sub>前沿事实对齐 2026-09-12：GPT-6 Astra（09-09）、Agents API（09-10）、Claude Fable 5.1（09-01）。</sub>
