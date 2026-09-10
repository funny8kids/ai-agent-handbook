<div align="center">
  <img src="docs/.gitbook/assets/violet-icon.svg" width="120" alt="AI Agent Handbook">
  <h1>AI Agent 手册</h1>
  <p><b>从原理到生产：</b>LLM 与注意力 · Agent 循环 · 工具协议（MCP/A2A） · 记忆与 RAG · 规划 · 多智能体 · 评估与安全 · 工程化 · AI 基础设施 · 具身智能</p>
  <p>
    <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-7C3AED?style=flat-square"></a>
    <img alt="Pages" src="https://img.shields.io/badge/pages-170-8B5CF6?style=flat-square">
    <img alt="Chapters" src="https://img.shields.io/badge/chapters-17-6D28D9?style=flat-square">
    <img alt="Projects" src="https://img.shields.io/badge/indexed%20projects-323-4C1D95?style=flat-square">
    <img alt="Math" src="https://img.shields.io/badge/pages%20with%20math-93-A78BFA?style=flat-square">
  </p>
</div>

---

这是一本**持续更新的开源 AI Agent 手册 + 资源库**。每一页都要求：原理给出公式与推导、结论给出可点开的出处、案例给出真实源码路径——不做"听起来对"的泛泛之谈。

在线阅读（GitBook 站点）：**VioletNotes Docs**。书内导航见侧边栏；本页直接把精选资源全部铺开。

---

## 先看这 12 个（最省时间的入口）

| 资源 | 一句话 | 类型 |
|---|---|---|
| [ReAct: Synergizing Reasoning and Acting](https://arxiv.org/abs/2210.03629) | 现代 Agent 循环的思想源头：想一步、做一步、看结果 | 论文 |
| [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | 什么时候用工作流、什么时候才该上 Agent 的工程判据 | 博客 |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | Transformer 原始论文，一切 LLM 的底座 | 论文 |
| [DeepSeek-R1](https://arxiv.org/abs/2501.12948) | 用可验证奖励做 RL 训出推理能力，含完整配方 | 论文 |
| [Pi Agent](https://github.com/earendil-works/pi) | 极简 harness 的活教材：统一 LLM API + Agent 循环 + CLI | 开源项目 |
| [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) | 「一切皆插件」的生产级运行时：连 Agent Loop 都可替换 | 开源项目 |
| [Claude Code 系统提示词全集（逆向）](https://github.com/Piebald-AI/claude-code-system-prompts) | 看生产级 Agent 的提示词组装、工具描述与权限约束怎么写 | 源码 |
| [MCP 官方文档](https://modelcontextprotocol.io/docs/learn/architecture) | 工具接入的事实标准：Tools / Resources / Prompts 三原语 | 文档 |
| [Microsoft: AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) | 系统化的免费入门课程，配套代码 | 课程 |
| [SWE-bench](https://www.swebench.com/) | 编程 Agent 的标准考场：真实 issue + 测试判分 | 基准 |
| [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) | Agent 工程化的 12 条原则，框架怀疑论者的解药 | 文章 |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | 全功能开源编程 Agent（原 OpenDevin） | 开源项目 |

---

## Agent 框架与编排

| 项目 | 说明 | Star |
|---|---|---|
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 集成生态最大的 LLM 应用框架，组件统一抽象（Runnable/LCEL） | 14.6 万 |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 用状态图表达 Agent：分支、循环、checkpoint、人工介入 | 4.1 万 |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | 把 prompt 变成「编译产物」，用指标自动优化 | 3.8 万 |
| [ComposioHQ/composio](https://github.com/ComposioHQ/composio) | 1000+ 工具集成，工具检索、鉴权与沙箱工作台 | 3.0 万 |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 少抽象的生产级 Agent SDK：handoff / guardrail / session | 2.9 万 |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | 极简 Agent 库，主张「让模型用代码思考」 | 2.9 万 |
| [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) | 微软企业级 SDK：Kernel + Plugin + 依赖注入 | 2.9 万 |
| [google/adk-python](https://github.com/google/adk-python) | Google 的代码优先 Agent 工具包 | 2.1 万 |

延伸：[框架与生态](docs/09-frameworks/README.md) · [LangChain](docs/09-frameworks/langchain.md) · [LangGraph](docs/09-frameworks/langgraph.md) · [DSPy](docs/09-frameworks/dspy.md)

## 编程 Agent 与 Harness

| 项目 | 说明 | Star |
|---|---|---|
| [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | 生产级插件化 harness：turn/step 状态机 + append-only 事件流 | 21.9 万 |
| [openai/codex](https://github.com/openai/codex) | OpenAI 开源终端编程 Agent（Rust） | 12.3 万 |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | Google 开源终端 Agent | 10.7 万 |
| [earendil-works/pi](https://github.com/earendil-works/pi) | 极简 harness：提供原语而非成品（原 `badlogic/pi-mono`） | 10.4 万 |
| [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | 全功能开源编程 Agent | — |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | Princeton 出品，提出 ACI（Agent-Computer Interface）设计学 | — |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 轻量结对编程，repo-map 上下文方案独树一帜 | — |
| [block/goose](https://github.com/block/goose) | Block 开源的可扩展本地 Agent | — |
| [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Claude Code 提示词全集（社区逆向），最佳 prompt 教材 | — |

延伸：[编程 Agent 案例](docs/12-applications/coding-agent.md) · [工具调用与协议](docs/05-tool-protocol/README.md)

## 多智能体

| 项目 | 说明 | Star |
|---|---|---|
| [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) | 「软件公司」多角色协作范式 | 7.0 万 |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 对话式多 Agent 框架，GroupChat 模式开创者 | 6.1 万 |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 角色化协作：Agent / Task / Crew / Process 声明式组队 | 5.8 万 |
| [OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev) | 多 Agent 协作软件开发 | 3.4 万 |
| [openai/swarm](https://github.com/openai/swarm) | handoff 模式的教学级实现（Agents SDK 前身） | 2.2 万 |
| [VRSEN/agency-swarm](https://github.com/VRSEN/agency-swarm) | 基于 OpenAI Agents SDK 的多 Agent 编排 | 4,555 |

延伸：[多智能体](docs/08-multi-agent/README.md) · [监督者模式](docs/08-multi-agent/supervisor-pattern.md) · [多 Agent 协作](docs/08-multi-agent/multi-agent-collaboration.md) · [辩论、共识与投票](docs/08-multi-agent/debate-consensus-voting.md)

## 记忆与 RAG

| 项目 | 说明 | Star |
|---|---|---|
| [langgenius/dify](https://github.com/langgenius/dify) | LLM 应用与 RAG 平台，可视化编排 | 15.5 万 |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 深度文档理解的 RAG 引擎 | 9.0 万 |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Agent 长期记忆层：提炼事实 + 按用户/会话检索 | 6.5 万 |
| [run-llama/llama_index](https://github.com/run-llama/llama_index) | RAG 管线专家：连接器矩阵 + 句窗/自动合并检索 | 5.2 万 |
| [milvus-io/milvus](https://github.com/milvus-io/milvus) | 分布式向量数据库（亿级） | 4.6 万 |
| [facebookresearch/faiss](https://github.com/facebookresearch/faiss) | Meta 的向量检索算法库，多数向量库的底层引擎 | 4.1 万 |
| [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | 轻量 GraphRAG 替代，建图成本显著更低 | 4.0 万 |
| [microsoft/graphrag](https://github.com/microsoft/graphrag) | 社区检测 + 分层摘要，解决「全局归纳」类问题 | — |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | Rust 向量库，过滤式检索体验最好 | — |
| [pgvector/pgvector](https://github.com/pgvector/pgvector) | PostgreSQL 向量扩展，千万级以内最省事 | — |
| [weaviate/weaviate](https://github.com/weaviate/weaviate) | 模块化向量库，内置混合检索 | — |
| [chroma-core/chroma](https://github.com/chroma-core/chroma) | 十行代码起步的轻量向量库 | — |

延伸：[记忆与 RAG](docs/06-memory-rag/README.md) · [RAG 基础](docs/06-memory-rag/rag-basics.md) · [向量数据库](docs/06-memory-rag/vector-database.md) · [GraphRAG](docs/06-memory-rag/graphrag.md)

## 工具与协议（MCP / A2A）

| 项目 | 说明 | Star |
|---|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 官方 MCP Server 参考实现：文件系统、GitHub、Postgres… | 9.0 万 |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | MCP 官方 Python SDK | 2.4 万 |
| [QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | 带 Function Calling / MCP / Code Interpreter 的 Agent 框架 | 1.7 万 |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | MCP 官方 TypeScript SDK | 1.3 万 |
| [a2aproject/A2A](https://github.com/a2aproject/A2A) | Agent-to-Agent 协议：Agent Card + Task 生命周期 | — |

延伸：[MCP](docs/05-tool-protocol/mcp.md) · [A2A](docs/05-tool-protocol/a2a.md) · [Function Calling](docs/05-tool-protocol/function-calling.md) · [工具权限与沙箱](docs/05-tool-protocol/tool-permission-sandbox.md)

## 浏览器与 Computer Use

| 项目 | 说明 | Star |
|---|---|---|
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 视觉 + DOM 混合浏览器 Agent | 11.4 万 |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 把浏览器操作标准化为 MCP 工具（DOM 路线首选） | 3.7 万 |
| [browserbase/stagehand](https://github.com/browserbase/stagehand) | 浏览器 Agent 的 SDK | 2.4 万 |
| [trycua/cua](https://github.com/trycua/cua) | Computer Use 的开源驱动与跨系统机群 | 2.2 万 |
| [e2b-dev/open-computer-use](https://github.com/e2b-dev/open-computer-use) | 开源 LLM 驱动的计算机操作 | 2,249 |
| [Anthropic: Computer Use 文档](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use) | 截图 → 定位 → 操作的标准范式 | 文档 |

延伸：[Computer Use / Browser Use](docs/05-tool-protocol/computer-use-browser-use.md) · [浏览器自动化](docs/12-applications/browser-automation.md)

## 可观测、评估与安全

| 项目 | 说明 | Star |
|---|---|---|
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | 开源 LLM 可观测：trace、成本、评估、prompt 管理，可自托管 | 3.4 万 |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | prompt 回归测试，YAML 定义用例矩阵 | 2.5 万 |
| [comet-ml/opik](https://github.com/comet-ml/opik) | 开源 LLM 评估与追踪平台 | 2.2 万 |
| [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | RAG 评估强、trace 可视化 | 1.1 万 |
| [explodinggradients/ragas](https://github.com/explodinggradients/ragas) | RAG 专项评估：忠实度、答案相关性、上下文精确率 | — |
| [meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) | Llama Guard 等安全分类模型 | — |
| [OpenTelemetry GenAI 语义约定](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | 厂商中立的 LLM 追踪标准 | 标准 |

延伸：[评估、安全与对齐](docs/10-evaluation-safety/README.md) · [Agent 评估指标](docs/10-evaluation-safety/evaluation-metrics.md) · [可观测性工具](docs/11-engineering/observability-tools.md) · [提示注入](docs/10-evaluation-safety/prompt-injection.md) · [越狱攻击](docs/10-evaluation-safety/jailbreak.md)

## 推理与部署

| 项目 | 说明 | Star |
|---|---|---|
| [ollama/ollama](https://github.com/ollama/ollama) | 一行命令本地跑大模型 | 18.1 万 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | 纯 C/C++ 推理引擎，GGUF 量化事实标准 | 12.8 万 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | PagedAttention + 连续批处理，自托管服务首选 | 9.1 万 |
| [unslothai/unsloth](https://github.com/unslothai/unsloth) | 微调加速，显存占用大幅降低 | 7.6 万 |
| [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) | 100+ 模型的统一微调框架 | 7.5 万 |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | 多模型统一网关：路由、配额、成本记账 | 5.8 万 |
| [huggingface/trl](https://github.com/huggingface/trl) | SFT / DPO / PPO 训练工具箱 | 1.9 万 |

延伸：[推理、量化、蒸馏与部署](docs/03-llm/inference-quantization-deployment.md) · [AI 基础设施](docs/16-ai-infrastructure/README.md)

## 沙箱与运行时

| 项目 | 说明 | Star |
|---|---|---|
| [firecracker-microvm/firecracker](https://github.com/firecracker-microvm/firecracker) | AWS Lambda 同款 microVM，强隔离且启动快 | 3.7 万 |
| [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | 面向 Agent 的代码执行沙箱 | 1.4 万 |
| [agent-infra/sandbox](https://github.com/agent-infra/sandbox) | 浏览器 + Shell + 文件 + MCP + VSCode 的一体化沙箱 | 5,883 |

延伸：[工具权限与沙箱](docs/05-tool-protocol/tool-permission-sandbox.md) · [权限控制与沙箱隔离](docs/10-evaluation-safety/permission-sandbox.md)

## 基准与数据集

| 基准 / 数据集 | 考什么 | 链接 |
|---|---|---|
| SWE-bench | 真实 GitHub issue 修复 | [swebench.com](https://www.swebench.com/) · [精读](docs/13-resources/benchmarks/swe-bench.md) |
| GAIA | 通用助理任务（多步推理 + 工具） | [Hugging Face](https://huggingface.co/datasets/gaia-benchmark/GAIA) · [精读](docs/13-resources/benchmarks/gaia.md) |
| WebArena | 真实网站长程任务 | [webarena.dev](https://webarena.dev/) · [精读](docs/13-resources/benchmarks/webarena.md) |
| AgentBench | 八场景综合能力 | [GitHub](https://github.com/THUDM/AgentBench) |
| ToolBench / BFCL | 工具调用与选择 | [BFCL 榜单](https://gorilla.cs.berkeley.edu/leaderboard) |
| τ-bench | 工具 + 用户模拟 + 策略遵守 | [GitHub](https://github.com/sierra-research/tau-bench) |
| OSWorld | 真实桌面环境操作 | [os-world.github.io](https://os-world.github.io/) |
| Terminal-Bench | 终端任务 | [tbench.ai](https://www.tbench.ai/) |

延伸：[基准测试总览](docs/10-evaluation-safety/benchmarks.md) · [五大基准精读](docs/10-evaluation-safety/agentbench-webarena-swebench-gaia-toolbench.md) · [论文索引](docs/13-resources/papers/README.md) · [数据集](docs/13-resources/datasets/README.md)

## 论文（按主题）

| 主题 | 论文 |
|---|---|
| 架构基础 | [Attention Is All You Need](https://arxiv.org/abs/1706.03762) · [DeepSeek-V3（MLA + MoE）](https://arxiv.org/abs/2412.19437) |
| 推理与提示 | [Chain-of-Thought](https://arxiv.org/abs/2201.11903) · [Self-Consistency](https://arxiv.org/abs/2203.11171) · [Tree of Thoughts](https://arxiv.org/abs/2305.10601) · [Graph of Thoughts](https://arxiv.org/abs/2308.09687) |
| Agent 循环 | [ReAct](https://arxiv.org/abs/2210.03629) · [Reflexion](https://arxiv.org/abs/2303.11366) · [Self-Refine](https://arxiv.org/abs/2303.17651) · [Toolformer](https://arxiv.org/abs/2302.04761) |
| 对齐与训练 | [InstructGPT / RLHF](https://arxiv.org/abs/2203.02155) · [DPO](https://arxiv.org/abs/2305.18290) · [LoRA](https://arxiv.org/abs/2106.09685) · [DeepSeek-R1](https://arxiv.org/abs/2501.12948) |
| 检索与记忆 | [RAG](https://arxiv.org/abs/2005.11401) · [DPR](https://arxiv.org/abs/2004.04906) · [GraphRAG](https://arxiv.org/abs/2404.16130) · [MemGPT](https://arxiv.org/abs/2310.08560) · [HNSW](https://arxiv.org/abs/1603.09320) |
| 评估与安全 | [SWE-bench](https://arxiv.org/abs/2310.06770) · [GAIA](https://arxiv.org/abs/2311.12983) · [RAGAS](https://arxiv.org/abs/2309.15217) · [GCG 越狱](https://arxiv.org/abs/2307.15043) · [间接提示注入](https://arxiv.org/abs/2302.12173) |

## 学习资源与社区

| 资源 | 说明 |
|---|---|
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | 微软官方免费课程（7.4 万 star） |
| [Hugging Face Agents Course](https://huggingface.co/learn/agents-course) | 开源 Agent 认证课程 |
| [LangChain Academy](https://academy.langchain.com) | 官方免费课，含 Deep Research 实现 |
| [DeepLearning.AI 短课](https://www.deeplearning.ai/courses/) | Agents / LangGraph / RAG 系列 |
| [dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | 提示工程系统指南（7.8 万 star） |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | MCP Server 大合集（9.5 万 star） |
| [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents) | Agent 项目大合集 |
| [kyrolabs/awesome-agents](https://github.com/kyrolabs/awesome-agents) | 框架与工具精选 |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Claude Code 生态（命令 / 子代理 / 工具） |
| [Anthropic 工程博客](https://www.anthropic.com/engineering) | 多 Agent、工具设计、上下文工程的一手经验 |
| [Lilian Weng 的博客](https://lilianweng.github.io/) | 「LLM Powered Autonomous Agents」是 Agent 综述经典 |
| [Simon Willison 的博客](https://simonwillison.net/) | 提示注入与 LLM 安全的最佳追踪源 |
| [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/) · [HF Discord](https://hf.co/join/discord) · [LangChain Forum](https://forum.langchain.com/) · [MCP Discussions](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions) | 提问与讨论 |

---

## 这本手册长什么样

- **170 页 / 17 章**，全部达到体裁字数门槛（原理型 ≥1200 字、实战型 ≥900、概念型 ≥600）
- **93 页含数学公式**（KaTeX）：注意力机制、Embedding 与相似度、RLHF/DPO、LoRA、量化、KV 缓存、RAG 指标、ToT 搜索、评估指标、约束解码、幻觉检测、事件溯源、容量规划、提示注入与越狱的风险模型……
- **每篇底部有「参考资料」**，数字与结论都能点回一手来源
- **323 个开源项目索引**（带实测 star 与许可）：[完整索引](docs/13-resources/projects/README.md)
- **17 张自绘 SVG 图示**（部分带 SMIL 动画）：Agent 循环、注意力计算、RAG 管线、多智能体、评估四层、连续批处理、前缀缓存、VLA 回路……
- 全书写作规范见 [风格指南](docs/14-templates/style-guide.md)（emoji 硬预算、公式与出处要求、图片必须放 `docs/.gitbook/assets/`）

**建议读法**：从 [学习路线](docs/00-index/learning-path.md) 选一条（入门 / 开发者 / 研究者 / 平台 Infra / 具身方向），按阶段走；每篇先看「先看结论」，需要细节再往下读。

## 贡献

- 新页面用 [知识点模板](docs/14-templates/knowledge-template.md) 或 [资源模板](docs/14-templates/resource-template.md)，并遵守 [风格指南](docs/14-templates/style-guide.md)
- 新增页面务必登记到 [SUMMARY.md](docs/SUMMARY.md)
- 质量自检：`python scripts/verify-docs.py`（标题 emoji / 断链 / 字数门槛 / 公式 / frontmatter）
- 详见 [贡献指南](docs/99-about/contributing.md)

## 许可证

[MIT](LICENSE)
