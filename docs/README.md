![AI Agent 手册](.gitbook/assets/violet-icon.svg)

# AI Agent 手册

**从原理到生产**：LLM 与注意力 · Agent 循环 · 工具协议（MCP/A2A） · 记忆与 RAG · 规划 · 多智能体 · 评估与安全 · 工程化 · AI 基础设施 · 具身智能

> 一本**持续更新的开源 AI Agent 手册 + 资源库**：170 页 / 17 章，93 页含公式推导，329 个开源项目索引。每一页都要求——原理给出公式与推导、结论给出可点开的出处、案例给出真实源码路径。

## 从哪开始

| 你是 | 走这条路线 | 通关标准 |
|---|---|---|
| 只会用 ChatGPT | [入门路线](00-index/learning-path.md)：01 → 02 → 03 → 04 | 能讲清「Agent 和 Chatbot 的区别」 |
| 有开发经验 | [开发者路线](00-index/learning-path.md)：02 → 05 → 06 → 09 → 11 | 能写出会调工具、能恢复错误的 Agent |
| 关注前沿与论文 | [研究者路线](00-index/learning-path.md)：04 → 08 → 10 | 能读懂 ReAct 并复现核心循环 |
| 要搭团队底座 | [平台 / Infra 路线](00-index/learning-path.md)：03 → 11 → 16 | 能给出 TTFT/TPOT/缓存命中率/成本基线 |
| 做机器人或想转具身 | [具身方向](00-index/learning-path.md)：02 → 04 → 17 → 16 | 能跑通「感知→技能→执行」闭环 |

![学习路线：四个阶段](.gitbook/assets/00-learning-path.svg)

## 必读 12 个

| 资源 | 一句话 |
|---|---|
| [ReAct 论文](13-resources/papers/react.md) | 现代 Agent 循环的思想源头：想一步、做一步、看结果 |
| [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | 什么时候用工作流、什么时候才该上 Agent |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | Transformer 原始论文，一切 LLM 的底座 |
| [DeepSeek-R1](https://arxiv.org/abs/2501.12948) | 可验证奖励 + RL 训出推理能力 |
| [Pi Agent](https://github.com/earendil-works/pi) | 极简 harness 的活教材 |
| [DeepSeek Harness](13-resources/projects/deepseek-harness.md) | 「一切皆插件」的生产级运行时 |
| [MCP 官方文档](https://modelcontextprotocol.io/docs/learn/architecture) | 工具接入的事实标准 |
| [AI Agents for Beginners](13-resources/courses/ai-agents-for-beginners.md) | 微软官方免费入门课 |
| [SWE-bench](13-resources/benchmarks/swe-bench.md) | 编程 Agent 的标准考场 |
| [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) | Agent 工程化的 12 条原则 |
| [LangGraph](09-frameworks/langgraph.md) | 用状态图表达 Agent：分支、循环、断点恢复 |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | 全功能开源编程 Agent |

## 按主题挑资源

**框架与编排** · [LangChain](09-frameworks/langchain.md) · [LangGraph](09-frameworks/langgraph.md) · [AutoGen](09-frameworks/autogen.md) · [CrewAI](09-frameworks/crewai.md) · [DSPy](09-frameworks/dspy.md) · [LlamaIndex](09-frameworks/llamaindex.md) · [Semantic Kernel](09-frameworks/semantic-kernel.md) · [OpenAI Agents SDK](09-frameworks/openai-agents-sdk.md) · [完整项目索引](13-resources/projects/README.md)

**编程 Agent / Harness** · [编程 Agent 案例](12-applications/coding-agent.md) · [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) · [earendil-works/pi](https://github.com/earendil-works/pi) · [openai/codex](https://github.com/openai/codex) · [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) · [SWE-agent](https://github.com/SWE-agent/SWE-agent) · [Aider](https://github.com/Aider-AI/aider) · [Claude Code 提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts)

**记忆与 RAG** · [RAG 基础](06-memory-rag/rag-basics.md) · [Embedding 与相似度](06-memory-rag/embedding-similarity.md) · [向量数据库](06-memory-rag/vector-database.md) · [GraphRAG](06-memory-rag/graphrag.md) · [知识图谱](06-memory-rag/knowledge-graph.md) · [LlamaIndex](https://github.com/run-llama/llama_index)、[RAGFlow](https://github.com/infiniflow/ragflow)、[Mem0](https://github.com/mem0ai/mem0)、[milvus](https://github.com/milvus-io/milvus)、[Qdrant](https://github.com/qdrant/qdrant)、[pgvector](https://github.com/pgvector/pgvector)、[FAISS](https://github.com/facebookresearch/faiss)

**工具与协议** · [Function Calling](05-tool-protocol/function-calling.md) · [MCP](05-tool-protocol/mcp.md) · [A2A](05-tool-protocol/a2a.md) · [工具权限与沙箱](05-tool-protocol/tool-permission-sandbox.md) · [MCP Servers](https://github.com/modelcontextprotocol/servers) · [MCP 官方 SDK](https://github.com/modelcontextprotocol/python-sdk) · [A2A 仓库](https://github.com/a2aproject/A2A)

**浏览器与 Computer Use** · [Computer Use / Browser Use](05-tool-protocol/computer-use-browser-use.md) · [browser-use](https://github.com/browser-use/browser-use) · [Playwright MCP](https://github.com/microsoft/playwright-mcp) · [Stagehand](https://github.com/browserbase/stagehand) · [cua](https://github.com/trycua/cua)

**评估、安全与对齐** · [Agent 评估指标](10-evaluation-safety/evaluation-metrics.md) · [基准测试总览](10-evaluation-safety/benchmarks.md) · [幻觉问题](10-evaluation-safety/hallucination.md) · [提示注入](10-evaluation-safety/prompt-injection.md) · [越狱攻击](10-evaluation-safety/jailbreak.md) · [权限与沙箱](10-evaluation-safety/permission-sandbox.md) · [LangFuse](https://github.com/langfuse/langfuse) · [Phoenix](https://github.com/Arize-ai/phoenix) · [RAGAS](https://github.com/explodinggradients/ragas) · [promptfoo](https://github.com/promptfoo/promptfoo)

**推理与部署** · [推理、量化、蒸馏与部署](03-llm/inference-quantization-deployment.md) · [vLLM](https://github.com/vllm-project/vllm) · [llama.cpp](https://github.com/ggml-org/llama.cpp) · [Ollama](https://github.com/ollama/ollama) · [LiteLLM](https://github.com/BerriAI/litellm) · [unsloth](https://github.com/unslothai/unsloth) · [LlamaFactory](https://github.com/hiyouga/LlamaFactory) · [TRL](https://github.com/huggingface/trl)

**沙箱与运行时** · [权限控制与沙箱隔离](10-evaluation-safety/permission-sandbox.md) · [E2B](https://github.com/e2b-dev/E2B) · [Firecracker](https://github.com/firecracker-microvm/firecracker) · [agent-infra/sandbox](https://github.com/agent-infra/sandbox)

**基准与数据集** · [SWE-bench](13-resources/benchmarks/swe-bench.md) · [GAIA](13-resources/benchmarks/gaia.md) · [WebArena](13-resources/benchmarks/webarena.md) · [AgentBench](https://github.com/THUDM/AgentBench) · [ToolBench / BFCL](https://gorilla.cs.berkeley.edu/leaderboard) · [τ-bench](https://github.com/sierra-research/tau-bench) · [OSWorld](https://os-world.github.io/) · [数据集索引](13-resources/datasets/README.md)

**论文** · [ReAct](https://arxiv.org/abs/2210.03629) · [CoT](https://arxiv.org/abs/2201.11903) · [ToT](https://arxiv.org/abs/2305.10601) · [Reflexion](https://arxiv.org/abs/2303.11366) · [Toolformer](https://arxiv.org/abs/2302.04761) · [InstructGPT/RLHF](https://arxiv.org/abs/2203.02155) · [DPO](https://arxiv.org/abs/2305.18290) · [LoRA](https://arxiv.org/abs/2106.09685) · [RAG](https://arxiv.org/abs/2005.11401) · [GraphRAG](https://arxiv.org/abs/2404.16130) · [MemGPT](https://arxiv.org/abs/2310.08560) · [SWE-bench](https://arxiv.org/abs/2310.06770) · [论文索引](13-resources/papers/README.md)

**课程、博客与社区** · [AI Agents for Beginners](13-resources/courses/README.md) · [LangChain Academy](https://academy.langchain.com) · [Hugging Face Agents Course](https://huggingface.co/learn/agents-course) · [Anthropic 工程博客](https://www.anthropic.com/engineering) · [Lilian Weng](https://lilianweng.github.io/) · [Simon Willison](https://simonwillison.net/) · [社区清单](13-resources/communities/README.md) · [Awesome 列表](13-resources/awesome-lists/README.md)

## 这本手册长什么样

- **170 页 / 17 章**，全部达到体裁字数门槛（原理型 ≥1200 字、实战型 ≥900、概念型 ≥600）
- **93 页含数学公式**（KaTeX）：注意力、Embedding、RLHF/DPO、LoRA、量化、KV 缓存、RAG 指标、评估指标、约束解码、幻觉检测、事件溯源、容量规划、提示注入风险模型……
- **每篇底部有「参考资料」**，数字与结论都能点回一手来源
- **329 个项目索引**（实测 star 与许可）：[开源项目索引](13-resources/projects/README.md)
- **17 张自绘 SVG 图示**（部分带 SMIL 动画）

查资料用 [资源总表](00-index/resources-index.md) 与 [标签索引](00-index/tags.md)；术语卡住查 [术语表](15-glossary/README.md)。

## 参与贡献

- 新页面用 [知识点模板](14-templates/knowledge-template.md) 或 [资源模板](14-templates/resource-template.md)，遵守 [风格指南](14-templates/style-guide.md)
- 新增页面登记到 [SUMMARY.md](SUMMARY.md)
- 详见 [贡献指南](99-about/contributing.md)
