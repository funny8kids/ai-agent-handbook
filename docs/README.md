# AI Agent 手册 · AI Agent Handbook

**从原理到生产**：LLM 与注意力 · Agent 循环 · 工具协议 · 记忆与 RAG · 规划 · 多智能体 · 评估与安全 · 工程化 · AI 基础设施 · 具身智能

**From theory to production**: LLMs & attention · agent loops · tool protocols · memory & RAG · planning · multi-agent · evaluation & safety · engineering · AI infrastructure · embodied AI

> **中文**：一本持续更新的开源 AI Agent 手册与资源库：170 页 / 17 章，93 页含公式推导，323 个开源项目索引。每一页都要求「把话说实」——原理给出公式与推导、结论给出可点开的出处、案例给出真实源码路径。
>
> **English**: A continuously updated, open-source AI Agent handbook and resource library — 170 pages across 17 chapters, 93 of them carrying formulas, plus an index of 323 open-source projects. Every page has to show its work: principles come with derivations, claims link to primary sources, cases point at real source paths.

## 快速开始 · Quick start

| 你是 · You are | 路线 · Route | 通关标准 · Done when |
|---|---|---|
| 只会用 ChatGPT · New to LLMs | 01 → 02 → 03 → 04 | 能讲清「Agent 与 Chatbot 的区别」· explain agent vs chatbot |
| 有开发经验 · Engineer | 02 → 05 → 06 → 09 → 11 | 能写出会调工具、能恢复错误的 Agent · ship an agent with tools & recovery |
| 关注前沿与论文 · Researcher | 04 → 08 → 10 | 能读懂 ReAct 并复现核心循环 · reproduce the ReAct loop |
| 要搭团队底座 · Platform / Infra | 03 → 11 → 16 | 能给出 TTFT/TPOT/缓存命中率/成本基线 · set cost & latency baselines |
| 做机器人或想转具身 · Robotics | 02 → 04 → 17 → 16 | 能跑通「感知→技能→执行」闭环 · close a perceive→skill→act loop |

完整路线、前置知识与自检标准 · Full paths, prerequisites & self-checks：**[学习路线 Learning path](00-index/learning-path.md)**

![学习路线：四个阶段 · Four-stage learning path](.gitbook/assets/00-learning-path.svg)

## 必读 12 个 · Top 12 must-reads

| 资源 · Resource | 一句话 · In one line |
|---|---|
| [ReAct 论文](13-resources/papers/react.md) | 现代 Agent 循环的思想源头 · the origin of the think-act-observe loop |
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | 什么时候用工作流、什么时候才该上 Agent · workflow vs agent, and when |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | Transformer 原始论文，一切 LLM 的底座 · the paper every LLM builds on |
| [DeepSeek-R1](https://arxiv.org/abs/2501.12948) | 用可验证奖励做 RL，训出推理能力 · RL with verifiable rewards |
| [Pi Agent](https://github.com/earendil-works/pi) | 极简 harness 的活教材 · a minimal harness you can read end to end |
| [DeepSeek Harness](13-resources/projects/deepseek-harness.md) | 「一切皆插件」的生产级运行时 · a runtime where everything is a plugin |
| [MCP 官方文档](https://modelcontextprotocol.io/docs/learn/architecture) | 工具接入的事实标准 · the de-facto tool protocol |
| [AI Agents for Beginners](13-resources/courses/ai-agents-for-beginners.md) | 微软官方免费入门课 · Microsoft's free beginner course |
| [SWE-bench](13-resources/benchmarks/swe-bench.md) | 编程 Agent 的标准考场 · the standard arena for coding agents |
| [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) | Agent 工程化的 12 条原则 · 12 principles for production agents |
| [LangGraph](09-frameworks/langgraph.md) | 用状态图表达 Agent：分支、循环、断点恢复 · agents as stateful graphs |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | 全功能开源编程 Agent · a full-featured open-source coding agent |

## 按主题挑资源 · Browse by topic

**框架与编排 · Frameworks** · [LangChain](09-frameworks/langchain.md) · [LangGraph](09-frameworks/langgraph.md) · [AutoGen](09-frameworks/autogen.md) · [CrewAI](09-frameworks/crewai.md) · [DSPy](09-frameworks/dspy.md) · [LlamaIndex](09-frameworks/llamaindex.md) · [Semantic Kernel](09-frameworks/semantic-kernel.md) · [OpenAI Agents SDK](09-frameworks/openai-agents-sdk.md) · [完整项目索引 Full index](13-resources/projects/README.md)

**编程 Agent 与 Harness · Coding agents** · [编程 Agent 案例](12-applications/coding-agent.md) · [deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) · [Pi](https://github.com/earendil-works/pi) · [Codex](https://github.com/openai/codex) · [Gemini CLI](https://github.com/google-gemini/gemini-cli) · [SWE-agent](https://github.com/SWE-agent/SWE-agent) · [Aider](https://github.com/Aider-AI/aider) · [Claude Code 提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts)

**记忆与 RAG · Memory & RAG** · [RAG 基础](06-memory-rag/rag-basics.md) · [Embedding 与相似度](06-memory-rag/embedding-similarity.md) · [向量数据库](06-memory-rag/vector-database.md) · [GraphRAG](06-memory-rag/graphrag.md) · [知识图谱](06-memory-rag/knowledge-graph.md) · [LlamaIndex](https://github.com/run-llama/llama_index) · [RAGFlow](https://github.com/infiniflow/ragflow) · [Mem0](https://github.com/mem0ai/mem0) · [Milvus](https://github.com/milvus-io/milvus) · [Qdrant](https://github.com/qdrant/qdrant) · [pgvector](https://github.com/pgvector/pgvector) · [FAISS](https://github.com/facebookresearch/faiss)

**工具与协议 · Tools & protocols** · [Function Calling](05-tool-protocol/function-calling.md) · [MCP](05-tool-protocol/mcp.md) · [A2A](05-tool-protocol/a2a.md) · [工具权限与沙箱](05-tool-protocol/tool-permission-sandbox.md) · [MCP Servers](https://github.com/modelcontextprotocol/servers) · [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) · [A2A 仓库](https://github.com/a2aproject/A2A)

**浏览器与 Computer Use · Browser & computer use** · [Computer Use / Browser Use](05-tool-protocol/computer-use-browser-use.md) · [browser-use](https://github.com/browser-use/browser-use) · [Playwright MCP](https://github.com/microsoft/playwright-mcp) · [Stagehand](https://github.com/browserbase/stagehand) · [cua](https://github.com/trycua/cua)

**评估、安全与对齐 · Evaluation & safety** · [Agent 评估指标](10-evaluation-safety/evaluation-metrics.md) · [基准测试总览](10-evaluation-safety/benchmarks.md) · [幻觉问题](10-evaluation-safety/hallucination.md) · [提示注入](10-evaluation-safety/prompt-injection.md) · [越狱攻击](10-evaluation-safety/jailbreak.md) · [权限与沙箱](10-evaluation-safety/permission-sandbox.md) · [LangFuse](https://github.com/langfuse/langfuse) · [Phoenix](https://github.com/Arize-ai/phoenix) · [RAGAS](https://github.com/explodinggradients/ragas) · [promptfoo](https://github.com/promptfoo/promptfoo)

**推理与部署 · Inference & deployment** · [推理、量化与部署](03-llm/inference-quantization-deployment.md) · [vLLM](https://github.com/vllm-project/vllm) · [llama.cpp](https://github.com/ggml-org/llama.cpp) · [Ollama](https://github.com/ollama/ollama) · [LiteLLM](https://github.com/BerriAI/litellm) · [unsloth](https://github.com/unslothai/unsloth) · [LlamaFactory](https://github.com/hiyouga/LlamaFactory) · [TRL](https://github.com/huggingface/trl)

**沙箱与运行时 · Sandboxes & runtimes** · [权限控制与沙箱隔离](10-evaluation-safety/permission-sandbox.md) · [E2B](https://github.com/e2b-dev/E2B) · [Firecracker](https://github.com/firecracker-microvm/firecracker) · [agent-infra/sandbox](https://github.com/agent-infra/sandbox)

**基准与数据集 · Benchmarks & datasets** · [SWE-bench](13-resources/benchmarks/swe-bench.md) · [GAIA](13-resources/benchmarks/gaia.md) · [WebArena](13-resources/benchmarks/webarena.md) · [AgentBench](https://github.com/THUDM/AgentBench) · [ToolBench / BFCL](https://gorilla.cs.berkeley.edu/leaderboard) · [τ-bench](https://github.com/sierra-research/tau-bench) · [OSWorld](https://os-world.github.io/) · [数据集索引](13-resources/datasets/README.md)

**论文 · Papers** · [ReAct](https://arxiv.org/abs/2210.03629) · [CoT](https://arxiv.org/abs/2201.11903) · [ToT](https://arxiv.org/abs/2305.10601) · [Reflexion](https://arxiv.org/abs/2303.11366) · [Toolformer](https://arxiv.org/abs/2302.04761) · [InstructGPT / RLHF](https://arxiv.org/abs/2203.02155) · [DPO](https://arxiv.org/abs/2305.18290) · [LoRA](https://arxiv.org/abs/2106.09685) · [RAG](https://arxiv.org/abs/2005.11401) · [GraphRAG](https://arxiv.org/abs/2404.16130) · [MemGPT](https://arxiv.org/abs/2310.08560) · [SWE-bench](https://arxiv.org/abs/2310.06770) · [论文索引](13-resources/papers/README.md)

**课程、博客与社区 · Courses, blogs & communities** · [AI Agents for Beginners](13-resources/courses/README.md) · [LangChain Academy](https://academy.langchain.com) · [HF Agents Course](https://huggingface.co/learn/agents-course) · [Anthropic 工程博客](https://www.anthropic.com/engineering) · [Lilian Weng](https://lilianweng.github.io/) · [Simon Willison](https://simonwillison.net/) · [社区清单](13-resources/communities/README.md) · [Awesome 列表](13-resources/awesome-lists/README.md)

## 关于这本手册 · About this handbook

- **170 页 / 17 章**，全部达到体裁字数门槛 · 170 pages across 17 chapters, all meeting their length bar
- **93 页含数学公式**（KaTeX）· 93 pages carry formulas
- **每篇底部有「参考资料」**，数字与结论都能点回一手来源 · every page ends with references
- **323 个项目索引**（实测 star 与许可）· an index of 323 projects with observed stars and licenses
- **17 张自绘 SVG 图示**（部分带 SMIL 动画）· 17 hand-drawn SVG diagrams

查资料用 [资源总表](00-index/resources-index.md) 与 [标签索引](00-index/tags.md)，术语卡住查 [术语表](15-glossary/README.md)。

Use the [resource index](00-index/resources-index.md) and [tag index](00-index/tags.md) to look things up; the [glossary](15-glossary/README.md) covers terminology.

## 许可证 · License

MIT
