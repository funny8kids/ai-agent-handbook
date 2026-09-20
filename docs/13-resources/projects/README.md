---
tags: [resource, project]
type: index
status: published
updated: 2026-09-20
---

# 开源项目索引

{% hint style="info" %}
**一句话**：AI Agent 相关开源项目总览，按 11 类整理，收录 323 个；star 数与许可为 **2026-09** 观测值。
{% endhint %}

{% hint style="tip" %}
**提示**：star 数只反映关注度，不反映质量与适配度；选型请结合活跃度与你的场景实测。表中 star 与许可为 **2026-09** 的观测值，会随时间变化。
{% endhint %}

## 深入卡片

下面几个项目在本手册中有单独的深读卡片：

[LangChain](langchain.md) · [LangGraph](langgraph.md) · [AutoGen](autogen.md) · [CrewAI](crewai.md) · [OpenHands](openhands.md) · [DeepSeek Harness](deepseek-harness.md) · [Pi Agent](pi.md)

## Agent 框架与编排

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 14.6 万 | MIT | Python | Python 全家桶框架；抽象层多、上手快但生产要自己收残局——先读 LangGraph 的思路再用它 |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | 8.2 万 | MIT | Python | 字节跳动的深度研究长任务编排；沙箱与多角色分工值得读源码，但它是参考实现不是开箱产品 |
| [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm) | 6.6 万 | MIT | JavaScript | 本地优先的一体化 RAG 桌面全家桶；个人知识库零门槛，生产要精细控制的话能调的余地有限 |
| [pathwaycom/llm-app](https://github.com/pathwaycom/llm-app) | 5.9 万 | MIT | Jupyter Notebook | Pathway 的实时增量 RAG 模板；"流式更新索引"思路独一份，但模板偏演示，别指望直接上生产 |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 4.1 万 | MIT | Python | 状态图式 Agent 编排，生产级框架的首选；checkpoint 与 human-in-the-loop 设计可直接学，文档零散要花时间补 |
| [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 3.9 万 | MIT | TypeScript | Claude Code 的多智能体编排插件；借 Claude Code 当内核体验团队分工，不是独立框架 |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | 3.8 万 | MIT | Python | 斯坦福的"声明式提示"框架，自动优化 prompt 与权重；学习曲线陡，适合写得起评测的研究型团队 |
| [conductor-oss/conductor](https://github.com/conductor-oss/conductor) | 3.2 万 | Apache-2.0 | Java | Netflix 系事件驱动工作流引擎，持久化执行与重试状态管理是工业级；对纯 LLM 新手偏重量级 |
| [ComposioHQ/composio](https://github.com/ComposioHQ/composio) | 3.0 万 | MIT | TypeScript | 托管的 SaaS 工具授权与调用中枢；快速接第三方 API 最省事，但多一层代理依赖，注意厂商锁定 |
| [simstudioai/sim](https://github.com/simstudioai/sim) | 3.0 万 | Apache-2.0 | TypeScript | 可视化 agent 工作流工作台；做演示和快速原型好看，复杂逻辑迟早撞到天花板回到写代码 |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 2.9 万 | MIT | Python | OpenAI 官方轻量多 Agent 库、swarm 的继任者；handoff + guardrails + tracing 一站式，但深度功能与 OpenAI 生态绑定 |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | 2.9 万 | Apache-2.0 | Python | HF 的极简 code agent 库，让模型写 Python 而非 JSON 调工具；上手惊艳，生产要自己补护栏与状态管理 |
| [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) | 2.9 万 | MIT | C# | 微软企业级 Agent SDK，多语言覆盖；企业集成强，但 API 更名震荡史沉重，选型先理清与 AutoGen/Agent Framework 的血缘 |
| [deepset-ai/haystack](https://github.com/deepset-ai/haystack) | 2.6 万 | Apache-2.0 | Python | deepset 的管线式架构，搜索/RAG 场景工程成熟稳定；Agent 表达力比 LangGraph 保守，适合重工程轻花活的团队 |
| [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) | 2.4 万 | NOASSERTION | Jupyter Notebook | 50+ tutorials and implementations for Generative AI Agent techniques, from basic conversational bots to comp… |
| [yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi) | 2.2 万 | NOASSERTION | Python | 概念验证鼻祖，代码已被作者弃置，读思路可以别依赖 |
| [jina-ai/serve](https://github.com/jina-ai/serve) | 2.2 万 | Apache-2.0 | Python | ☁️ Build multimodal AI applications with cloud-native stack |
| [coze-dev/coze-studio](https://github.com/coze-dev/coze-studio) | 2.2 万 | Apache-2.0 | TypeScript | An AI agent development platform with all-in-one visual tools, simplifying agent creation, debugging, and de… |
| [NirDiamant/agents-towards-production](https://github.com/NirDiamant/agents-towards-production) | 2.1 万 | NOASSERTION | Jupyter Notebook | End-to-end, code-first tutorials for building production-grade GenAI agents. From prototype to enterprise de… |
| [TransformerOptimus/SuperAGI](https://github.com/TransformerOptimus/SuperAGI) | 1.8 万 | MIT | Python | <⚡️> SuperAGI - A dev-first open source autonomous AI agent framework. Enabling developers to build, manage … |
| [HKUDS/DeepCode](https://github.com/HKUDS/DeepCode) | 1.7 万 | MIT | Python | "DeepCode: Open Agentic Coding (Agent Harness & Loop Engineering & Multi-Agent Orchestration)" |
| [GreyDGL/PentestGPT](https://github.com/GreyDGL/PentestGPT) | 1.5 万 | MIT | Python | Automated Penetration Testing Agentic Framework Powered by Large Language Models |
| [microsoft/agent-framework](https://github.com/microsoft/agent-framework) | 1.3 万 | MIT | Python | A framework for building, orchestrating and deploying AI agents and multi-agent workflows with support for P… |
| [simular-ai/Agent-S](https://github.com/simular-ai/Agent-S) | 1.2 万 | Apache-2.0 | Python | Agent S: an open agentic framework that uses computers like a human |
| [dataelement/bisheng](https://github.com/dataelement/bisheng) | 1.2 万 | Apache-2.0 | Python | BISHENG is an open LLM devops platform for next generation Enterprise AI applications. Powerful and comprehe… |
| [The-Pocket/PocketFlow](https://github.com/The-Pocket/PocketFlow) | 1.1 万 | MIT | Python | Pocket Flow: 100-line LLM framework. Let Agents build Agents! |
| [microsoft/magentic-ui](https://github.com/microsoft/magentic-ui) | 1.0 万 | MIT | Python | MagenticLite is an experimental agent that works across the browser and local file system |
| [yzhao062/pyod](https://github.com/yzhao062/pyod) | 9,997 | BSD-2-Clause | Python | A Python library for anomaly detection across tabular, time series, graph, text, image, and audio data. 60+ … |
| [omnigent-ai/omnigent](https://github.com/omnigent-ai/omnigent) | 9,822 | Apache-2.0 | Python | Omnigent is an open-source AI agent framework and meta-harness: orchestrate Claude Code, Codex, Cursor, Pi, … |
| [adongwanai/AgentGuide](https://github.com/adongwanai/AgentGuide) | 9,411 | NOASSERTION | MDX | https://adongwanai.github.io/AgentGuide / AI Agent开发指南 / LangGraph实战 / 高级RAG / 转行大模型 / 大模型面试 / 算法工程师 / 面试题库 … |
| [iflytek/astron-agent](https://github.com/iflytek/astron-agent) | 8,980 | Apache-2.0 | Java | Enterprise-grade, commercial-friendly agentic workflow platform for building next-generation SuperAgents. |
| [bentoml/BentoML](https://github.com/bentoml/BentoML) | 8,834 | Apache-2.0 | Python | The easiest way to serve AI apps and models - Build Model Inference APIs, Job queues, LLM apps, Multi-model … |
| [alvinunreal/oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim) | 8,771 | MIT | TypeScript | Lean, fine tuned Opencode multi agent suite · Mix any models · Auto delegate tasks |
| [rocketride-org/rocketride-server](https://github.com/rocketride-org/rocketride-server) | 8,441 | MIT | Python | High-performance AI pipeline engine with a C++ core and 50+ Python-extensible nodes. Build, debug, and scale… |

## 编程 Agent 与 Harness

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | 25.6 万 | MIT | JavaScript | The agent harness performance optimization system. Skills, instincts, memory, security, and research-first d… |
| [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | 21.9 万 | MIT | TypeScript | DeepSeek Harness: Everything is a Plugin. |
| [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) | 14.3 万 | GPL-3.0 | — | 主流 AI 编程工具的系统提示词合集；读别人的提示词是长进最快的方式，注意 GPL 且别直接抄段落 |
| [farion1231/cc-switch](https://github.com/farion1231/cc-switch) | 13.2 万 | MIT | Rust | 一键切换 Claude Code / Codex 等供应商配置的桌面工具；纯效率件与 Agent 本身无关，改配置前备份好原文件 |
| [openai/codex](https://github.com/openai/codex) | 12.3 万 | Apache-2.0 | Rust | OpenAI 官方终端编程 Agent；与自家订阅深度绑定，审批与沙箱策略要按团队规范调校再用 |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | 10.7 万 | Apache-2.0 | TypeScript | Gemini 官方终端 Agent；免费额度与超长上下文是卖点，功能堆叠快、稳定性要实测后再托付关键任务 |
| [earendil-works/pi](https://github.com/earendil-works/pi) | 10.4 万 | MIT | TypeScript | 极简 Agent 工具箱：统一 LLM API、agent loop、TUI；学 harness 原理的一流教材，生态与文档偏个人项目级 |
| [nexu-io/open-design](https://github.com/nexu-io/open-design) | 9.5 万 | Apache-2.0 | TypeScript | 🎨 Best DeepSeek Harness Design Plugin. The open-source Claude Design alternative. 🖥️ Local-first desktop app… |
| [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | 9.4 万 | Apache-2.0 | JavaScript | Persistent Context Across Sessions for Every Agent –  Captures everything your agent does during sessions, c… |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 9.3 万 | MIT | JavaScript | Addy Osmani 整理的工程化 skills 集；可直接插拔使用，质量参差、挑贴合自己团队规范的用 |
| [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | 7.2 万 | MIT | TypeScript | 🌊 The original agent meta-harness. Deploy intelligent multi-player swarms, coordinate autonomous workflows, … |
| [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) | 7.1 万 | Apache-2.0 | Python | Compress tool outputs, logs, files, and RAG chunks before they reach the LLM. 20% fewer tokens for coding ag… |
| [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | 7.0 万 | MIT | C | Pre-indexed code knowledge graph, auto syncs on code changes, for Claude Code, Codex, Gemini, Cursor, OpenCo… |
| [cline/cline](https://github.com/cline/cline) | 6.8 万 | Apache-2.0 | TypeScript | VS Code 审批式编程 Agent 鼻祖；Plan/Act 分离安全感强，但逐步确认的流程 token 消耗出名地大 |
| [stablyai/orca](https://github.com/stablyai/orca) | 6.6 万 | MIT | TypeScript | Orca is the ADE for working with a fleet of parallel agents. Run any coding agent with your own subscription… |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 5.4 万 | NOASSERTION | Python | A hand-picked collection of the finest of resources for the most awesome of agents, Claude Code, the undispu… |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 4.9 万 | MIT | JavaScript | Marketing skills for Claude Code and AI agents. CRO, copywriting, SEO, analytics, and growth engineering. |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 4.9 万 | Apache-2.0 | Python | 终端结对编程老将，git 自动提交与 diff 管理是标杆；repo-map 上下文设计值得读源码借鉴 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 4.4 万 | MIT | Python | Turn any AI agent into an AI Scientist. The #1 Agent Skills library for science, used by 190,000+ scientists… |
| [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | 4.3 万 | MIT | C | High-performance code intelligence MCP server. Indexes codebases into a persistent knowledge graph — average… |
| [luongnv89/claude-howto](https://github.com/luongnv89/claude-howto) | 4.1 万 | MIT | Python | A visual, example-driven guide to Claude Code — from basic concepts to advanced agents, with copy-paste temp… |
| [ToolJet/ToolJet](https://github.com/ToolJet/ToolJet) | 4.1 万 | AGPL-3.0 | JavaScript | Open-source foundation of ToolJet AI - the enterprise app generation platform for internal tools, dashboards… |
| [wshobson/agents](https://github.com/wshobson/agents) | 4.0 万 | MIT | Python | Multi-harness agentic plugin marketplace for Claude Code, Codex, Cursor, OpenCode, GitHub Copilot, and Googl… |
| [herdrdev/herdr](https://github.com/herdrdev/herdr) | 3.7 万 | Apache-2.0 | Rust | the runtime your coding agents live on |
| [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) | 3.6 万 | MIT | Python | A skill to stop your coding agent from burying the answer. ADHD-friendly output. |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 3.4 万 | MIT | — | A curated collection of 1000+ agent skills from official dev teams and the community, compatible with Claude… |
| [iOfficeAI/AionUi](https://github.com/iOfficeAI/AionUi) | 3.3 万 | Apache-2.0 | TypeScript | Open-source 24/7 Cowork app for OpenClaw, Hermes, Claude Code, Codex, OpenCode and 20+ more CLI Agent / Cust… |
| [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) | 3.3 万 | Apache-2.0 | Python | 817 structured cybersecurity skills for AI agents · Mapped to 6 frameworks: MITRE ATT&CK, NIST CSF 2.0, MITR… |
| [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | 3.0 万 | MIT | TypeScript | ⌥ Coding agent with the IDE wired in |
| [oraios/serena](https://github.com/oraios/serena) | 2.9 万 | MIT | Python | A powerful MCP toolkit for coding, providing semantic retrieval and editing capabilities  - the IDE for your… |
| [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) | 2.9 万 | MIT | JavaScript | Create beautiful slides on the web using a coding agent's frontend skills |
| [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | 2.8 万 | Apache-2.0 | TypeScript | #1 Persistent memory for AI coding agents based on real-world benchmarks |
| [BloopAI/vibe-kanban](https://github.com/BloopAI/vibe-kanban) | 2.8 万 | Apache-2.0 | Rust | Get 10X more out of Claude Code, Codex or any coding agent |
| [google-labs-code/design.md](https://github.com/google-labs-code/design.md) | 2.8 万 | Apache-2.0 | TypeScript | A format specification for describing a visual identity to coding agents. DESIGN.md gives agents a persisten… |

## 多智能体

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 10.4 万 | Apache-2.0 | Python | 多智能体辩论式交易框架；当论文演示读可以，真金白银接上去三思 |
| [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) | 7.0 万 | MIT | Python | 角色扮演软件公司 SOP 的多智能体流水线；分工思想值得借鉴，抽象层层叠叠读源码吃力 |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 6.1 万 | CC-BY-4.0 | Python | 微软对话式多智能体框架；API 历经大改并与 Semantic Kernel 合流进新 Agent Framework，选型先认清版本脉络 |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 5.8 万 | MIT | Python | 角色 + 任务式编队编排入门款；跑 demo 极快，生产级精细控制不如图式方案 |
| [OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev) | 3.4 万 | Apache-2.0 | Python | 模拟软件瀑布流聊天开发的学术项目；教学演示定位，别拿去交付真软件 |
| [openai/swarm](https://github.com/openai/swarm) | 2.2 万 | MIT | Python | OpenAI 的教学级 handoff 库，继任者 Agents SDK 出来后已停止演进；读 routines/handoff 概念，新项目别用 |
| [SolaceLabs/solace-agent-mesh](https://github.com/SolaceLabs/solace-agent-mesh) | 4,933 | Apache-2.0 | Python | An event-driven framework designed to build and orchestrate multi-agent AI systems. It enables seamless inte… |
| [LantaoYu/MARL-Papers](https://github.com/LantaoYu/MARL-Papers) | 4,878 | NOASSERTION | — | Paper list of multi-agent reinforcement learning (MARL) |
| [VRSEN/agency-swarm](https://github.com/VRSEN/agency-swarm) | 4,555 | MIT | Python | Reliable Multi-Agent Orchestration Framework |
| [SkyworkAI/DeepResearchAgent](https://github.com/SkyworkAI/DeepResearchAgent) | 3,536 | MIT | Python | DeepResearchAgent is a hierarchical multi-agent system designed not only for deep research tasks but also fo… |
| [Farama-Foundation/PettingZoo](https://github.com/Farama-Foundation/PettingZoo) | 3,512 | MIT | Python | A standard API for multi-agent reinforcement learning environments, with popular reference environments and … |
| [neomjs/neo](https://github.com/neomjs/neo) | 3,271 | MIT | JavaScript | Neo.mjs is a self-evolving software organism: a professional end-to-end AI engineering team whose cross-mode… |
| [bradygaster/squad](https://github.com/bradygaster/squad) | 3,167 | MIT | TypeScript | Squad: AI agent teams for any project |
| [wanikua/danghuangshang](https://github.com/wanikua/danghuangshang) | 2,700 | MIT | TypeScript | Open-source multi-agent collaboration system inspired by Chinese governance — deploy and coordinate speciali… |
| [nikmcfly/MiroFish-Offline](https://github.com/nikmcfly/MiroFish-Offline) | 2,503 | AGPL-3.0 | Python | Offline multi-agent simulation & prediction engine. English fork of MiroFish with Neo4j + Ollama local stack. |
| [ZJU-FAST-Lab/ego-planner-swarm](https://github.com/ZJU-FAST-Lab/ego-planner-swarm) | 2,171 | GPL-3.0 | C++ | An efficient single/multi-agent trajectory planner for multicopters. |
| [zi-yue-1129/DATAGEN](https://github.com/zi-yue-1129/DATAGEN) | 1,798 | MIT | Python | DATAGEN: AI-driven multi-agent research assistant automating hypothesis generation, data analysis, and repor… |
| [asinghcsu/AgenticRAG-Survey](https://github.com/asinghcsu/AgenticRAG-Survey) | 1,726 | NOASSERTION | — | Agentic-RAG explores advanced Retrieval-Augmented Generation systems enhanced with AI LLM agents. |
| [langchain-ai/langgraph-swarm-py](https://github.com/langchain-ai/langgraph-swarm-py) | 1,561 | MIT | Python | For your multi-agent needs |
| [win4r/ClawTeam-OpenClaw](https://github.com/win4r/ClawTeam-OpenClaw) | 1,451 | MIT | Python | ClawTeam fork fully adapted for OpenClaw — multi-agent swarm coordination with OpenClaw as the default agent |
| [datawhalechina/hugging-multi-agent](https://github.com/datawhalechina/hugging-multi-agent) | 1,414 | NOASSERTION | CSS | A tutorial based on MetaGPT to quickly help you understand the concept of agent and muti-agent and get start… |
| [oxwhirl/smac](https://github.com/oxwhirl/smac) | 1,367 | MIT | Python | SMAC: The StarCraft Multi-Agent Challenge |
| [uluckyXH/OpenMOSS](https://github.com/uluckyXH/OpenMOSS) | 1,323 | MIT | Python | A self-organizing multi-agent collaboration platform for OpenClaw. Multiple AI agents work as an autonomous … |
| [wanxingai/LightAgent](https://github.com/wanxingai/LightAgent) | 1,217 | Apache-2.0 | Python | LightAgent: Lightweight Python framework for OpenAI-compatible agents with tools, memory, guardrails, tracin… |
| [mateaix/mateclaw](https://github.com/mateaix/mateclaw) | 1,095 | Apache-2.0 | Java | 🤖 MateClaw — Your second brain with Multi-Agent Orchestration, MCP Protocol, Skills & Memory, Dream, and Mul… |
| [vstorm-co/pydantic-deepagents](https://github.com/vstorm-co/pydantic-deepagents) | 1,061 | MIT | Python | Open-source, self-hosted Claude Code - a terminal AI assistant and the Python framework behind it. Tool-call… |
| [Yeti-791/Tsec-Hackathon](https://github.com/Yeti-791/Tsec-Hackathon) | 802 | NOASSERTION | Python | 腾讯云智能渗透黑客松 Official repository of Tencent Cloud Intelligent Penetration Hackathon. Showcasing top open-sourc… |
| [proroklab/VectorizedMultiAgentSimulator](https://github.com/proroklab/VectorizedMultiAgentSimulator) | 604 | GPL-3.0 | Python | VMAS is a vectorized differentiable simulator designed for efficient Multi-Agent Reinforcement Learning benc… |
| [vibeeval/vibecosystem](https://github.com/vibeeval/vibecosystem) | 529 | MIT | C# | AI software team for Claude Code - 138 agents, 295 skills, 73 hooks. Self-learning, multi-agent swarm, auton… |

## 记忆与 RAG

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [langgenius/dify](https://github.com/langgenius/dify) | 15.5 万 | NOASSERTION | TypeScript | 低代码 LLMOps 平台，从想法到可演示应用最快；深度定制会撞天花板，多租户 SaaS 商用先看清 license 附加条款 |
| [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | 11.7 万 | Apache-2.0 | Python | Turn any codebase, with its docs, SQL schemas, configs, and PDFs, into a queryable knowledge graph. A /graph… |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 9.0 万 | Apache-2.0 | Go | 深度文档理解是护城河，复杂版式与表格解析真强；部署偏重，小场景用不着整套 |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | 6.5 万 | Apache-2.0 | Python | Agent 记忆层即插即用件，抽取 + 合并思路好；记忆质量必须拿自己的评测集验证再上线 |
| [run-llama/llama_index](https://github.com/run-llama/llama_index) | 5.2 万 | MIT | Python | 数据连接器与索引框架起家，文档/知识库场景对味；接口变动频繁，别被教程锁定在旧 API 上 |
| [milvus-io/milvus](https://github.com/milvus-io/milvus) | 4.6 万 | Apache-2.0 | Go | 大规模分布式向量库老牌；运维组件不少，量级不到十亿用 pgvector/Qdrant 更省心 |
| [facebookresearch/faiss](https://github.com/facebookresearch/faiss) | 4.1 万 | MIT | C++ | 向量检索的库而非数据库；持久化、增删、分片全要自己搭，通常当算法基线或内嵌组件用 |
| [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | 4.0 万 | MIT | Python | 轻量图索引 RAG，论文实现里算好落地的；思路优雅，生产可靠性仍要自证 |
| [chatchat-space/Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat) | 3.9 万 | Apache-2.0 | Python | 中文本地知识库入门标配，部署文档齐；生产要摆脱 LangChain 影子自己重做一层 |
| [volcengine/OpenViking](https://github.com/volcengine/OpenViking) | 3.6 万 | AGPL-3.0 | Python | Self-evolving Context Database for AI Agents. Unify Agent Memory, Knowledge RAG and Skills. |
| [microsoft/graphrag](https://github.com/microsoft/graphrag) | 3.6 万 | MIT | Python | 面向"全局总结式"提问的图 RAG，代价是索引期大量 LLM 调用；不是这类查询就别开这个成本 |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | 3.4 万 | Apache-2.0 | Rust | Rust 写的高性能向量检索，单机部署体验好；多数团队用不着 Milvus 那套集群复杂度 |
| [tirth8205/code-review-graph](https://github.com/tirth8205/code-review-graph) | 3.1 万 | MIT | Python | Local-first code intelligence graph for MCP and CLI. Builds a persistent map of your codebase so AI coding t… |
| [getzep/graphiti](https://github.com/getzep/graphiti) | 3.1 万 | Apache-2.0 | Python | Build Real-Time Knowledge Graphs for AI Agents |
| [topoteretes/cognee](https://github.com/topoteretes/cognee) | 3.1 万 | Apache-2.0 | Python | Cognee is the open-source AI memory platform for agents. Give your AI agents persistent long-term memory acr… |
| [chroma-core/chroma](https://github.com/chroma-core/chroma) | 2.9 万 | Apache-2.0 | Rust | Search infrastructure for AI |
| [TencentCloud/TencentDB-Agent-Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory) | 2.6 万 | NOASSERTION | TypeScript | TencentDB Agent Memory is a team-level memory hub for AI Agents — turning conversations, docs, and code into… |
| [letta-ai/letta](https://github.com/letta-ai/letta) | 2.5 万 | Apache-2.0 | — | Platform for stateful agents: AI with advanced memory that can learn and self-improve over time. |
| [HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything) | 2.3 万 | MIT | Python | "RAG-Anything: All-in-One RAG Framework" |
| [pgvector/pgvector](https://github.com/pgvector/pgvector) | 2.3 万 | NOASSERTION | C | 向量检索长在 Postgres 里，事务与业务数据同库；中小规模的最优解，别为它单独养一套向量数据库 |
| [Tencent/WeKnora](https://github.com/Tencent/WeKnora) | 2.2 万 | NOASSERTION | Go | Open-source LLM knowledge platform: turn raw documents into a queryable RAG, an autonomous reasoning agent, … |
| [weaviate/weaviate](https://github.com/weaviate/weaviate) | 1.7 万 | NOASSERTION | Go | Weaviate is an open-source vector database that stores both objects and vectors, allowing for the combinatio… |
| [memvid/memvid](https://github.com/memvid/memvid) | 1.7 万 | Apache-2.0 | Rust | Memory layer for AI Agents. Replace complex RAG pipelines with a serverless, single-file memory layer. Give … |
| [alibaba/zvec](https://github.com/alibaba/zvec) | 1.6 万 | Apache-2.0 | C++ | A lightweight, lightning-fast, in-process vector database |
| [llmware-ai/llmware](https://github.com/llmware-ai/llmware) | 1.5 万 | Apache-2.0 | Python | Unified framework for building enterprise RAG pipelines with small, specialized models |
| [langchain4j/langchain4j](https://github.com/langchain4j/langchain4j) | 1.3 万 | Apache-2.0 | Java | LangChain4j is an idiomatic, open-source Java library for building LLM-powered applications on the JVM. It o… |
| [InsForge/InsForge](https://github.com/InsForge/InsForge) | 1.3 万 | Apache-2.0 | TypeScript | The all-in-one, open-source backend platform for agentic coding. InsForge gives your coding agent database, … |
| [neuml/txtai](https://github.com/neuml/txtai) | 1.3 万 | Apache-2.0 | Python | 💡 All-in-one AI framework for semantic search, LLM orchestration and language model workflows |
| [vesoft-inc/nebula](https://github.com/vesoft-inc/nebula) | 1.2 万 | Apache-2.0 | C++ | A distributed, fast open-source graph database featuring horizontal scalability and high availability |
| [SciPhi-AI/R2R](https://github.com/SciPhi-AI/R2R) | 7,994 | MIT | Python | SoTA production-ready AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API. |
| [deeplethe/utopia](https://github.com/deeplethe/utopia) | 6,728 | Apache-2.0 | Rust | World's first open-source enterprise world model. |
| [FalkorDB/FalkorDB](https://github.com/FalkorDB/FalkorDB) | 5,990 | NOASSERTION | Rust | A super fast Graph Database uses GraphBLAS under the hood for its sparse adjacency matrix graph representati… |
| [ageerle/ruoyi-ai](https://github.com/ageerle/ruoyi-ai) | 5,687 | MIT | Java | An enterprise AI development framework for building AI agents. It provides unified management of multi-provi… |
| [volcengine/MineContext](https://github.com/volcengine/MineContext) | 5,505 | Apache-2.0 | Python | MineContext is your proactive context-aware AI partner（Context-Engineering+ChatGPT Pulse） |

## 工具与协议

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 9.0 万 | NOASSERTION | TypeScript | 官方参考 MCP server 合集；学协议的正确起点，生产别直接跑未审阅的第三方 server |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | 2.4 万 | MIT | Python | 官方 Python SDK，FastMCP 写法入门顺滑；协议本身还在快速演进，锁好版本 |
| [google/adk-python](https://github.com/google/adk-python) | 2.1 万 | Apache-2.0 | Python | Google 的 code-first Agent 工具箱，评估与部署链路完整；已在 GCP 上最顺，否则处处受绑定 |
| [QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | 1.7 万 | Apache-2.0 | Python | Qwen 官方工具链（function calling / code interpreter / MCP）；配 Qwen 模型最稳，非 Qwen 技术栈不必引入 |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | 1.3 万 | NOASSERTION | TypeScript | 官方 TS SDK；与 python-sdk 同理，API 仍在演进，升级前先看 changelog |
| [hangwin/mcp-chrome](https://github.com/hangwin/mcp-chrome) | 1.2 万 | MIT | TypeScript | 把你已登录的 Chrome 接给 Agent，真实网站自动化能干隔离方案干不了的事；但 Agent 握着你全部会话，安全面很大 |
| [modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) | 9,175 | NOASSERTION | TypeScript | 协议规范本身；写 server/client 前先读它，tools/resources/prompts 三个原语一次搞清少踩坑 |
| [google/adk-go](https://github.com/google/adk-go) | 8,764 | Apache-2.0 | Go | An open-source, code-first Go toolkit for building, evaluating, and deploying sophisticated AI agents with f… |
| [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry) | 7,234 | NOASSERTION | Go | 社区 MCP 注册表，找 server 的正规入口；生态仍鱼龙混杂，接入前自行审查代码 |
| [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp) | 6,630 | Apache-2.0 | TypeScript | Model Context Protocol Server for Mobile Automation and Scraping (iOS, Android, Emulators, Simulators and Re… |
| [getsentry/XcodeBuildMCP](https://github.com/getsentry/XcodeBuildMCP) | 6,363 | MIT | TypeScript | A Model Context Protocol (MCP) server and CLI that provides tools for agent use when working on iOS and macO… |
| [jacob-bd/gemini-notebook-mcp-cli](https://github.com/jacob-bd/gemini-notebook-mcp-cli) | 6,056 | MIT | Python | Programmatic access to Gemini Notebook - via command-line interface (CLI), Model Context Protocol (MCP) serv… |
| [executeautomation/mcp-playwright](https://github.com/executeautomation/mcp-playwright) | 5,644 | MIT | TypeScript | Playwright Model Context Protocol Server - Tool to automate Browsers and APIs in Claude Desktop, Cline, Curs… |
| [nanbingxyz/5ire](https://github.com/nanbingxyz/5ire) | 5,345 | NOASSERTION | TypeScript | 5ire is a cross-platform desktop AI assistant, MCP client. It compatible with major service providers,  supp… |
| [modelcontextprotocol/go-sdk](https://github.com/modelcontextprotocol/go-sdk) | 5,084 | NOASSERTION | Go | The official Go SDK for Model Context Protocol servers and clients. Maintained in collaboration with Google. |
| [aipotheosis-labs/aci](https://github.com/aipotheosis-labs/aci) | 4,888 | Apache-2.0 | Python | ACI.dev is the open source tool-calling platform that hooks up 600+ tools into any agentic IDE or custom AI … |
| [modelcontextprotocol/csharp-sdk](https://github.com/modelcontextprotocol/csharp-sdk) | 4,520 | NOASSERTION | C# | The official C# SDK for Model Context Protocol servers and clients. Maintained in collaboration with Microso… |
| [panaversity/learn-agentic-ai](https://github.com/panaversity/learn-agentic-ai) | 4,357 | MIT | Jupyter Notebook | Learn Agentic AI using Dapr Agentic Cloud Ascent (DACA) Design Pattern and Agent-Native Cloud Technologies: … |
| [wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) | 4,295 | MIT | — | A curated list of Model Context Protocol (MCP) servers |
| [Pimzino/spec-workflow-mcp](https://github.com/Pimzino/spec-workflow-mcp) | 4,288 | GPL-3.0 | TypeScript | A Model Context Protocol (MCP) server that provides structured spec-driven development workflow tools for AI… |
| [haris-musa/excel-mcp-server](https://github.com/haris-musa/excel-mcp-server) | 4,175 | MIT | Python | A Model Context Protocol server for Excel file manipulation |
| [evalstate/fast-agent](https://github.com/evalstate/fast-agent) | 3,918 | Apache-2.0 | Python | Code, Build and Evaluate agents - excellent Model and Skills/MCP/ACP/A2A Support |
| [modelcontextprotocol/java-sdk](https://github.com/modelcontextprotocol/java-sdk) | 3,685 | MIT | Java | The official Java SDK for Model Context Protocol servers and clients. Maintained in collaboration with Sprin… |
| [microsoft/mcp](https://github.com/microsoft/mcp) | 3,659 | MIT | C# | Catalog of official Microsoft MCP (Model Context Protocol) server implementations for AI-powered data access… |
| [opensumi/core](https://github.com/opensumi/core) | 3,657 | MIT | TypeScript | A framework helps you quickly build AI Native IDE products. MCP Client, supports Model Context Protocol (MCP… |
| [off-grid-ai/OGAM](https://github.com/off-grid-ai/OGAM) | 3,075 | MIT | TypeScript | The Swiss Army Knife of Offline AI. Chat, see, speak, and generate images on your phone or Mac — GGUF LLMs, … |
| [zcaceres/markdownify-mcp](https://github.com/zcaceres/markdownify-mcp) | 2,990 | MIT | TypeScript | A Model Context Protocol server for converting almost anything to Markdown |
| [coddingtonbear/obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api) | 2,907 | MIT | TypeScript | A secure REST API and Model Context Protocol (MCP) server for your vault. |
| [liyupi/yu-ai-agent](https://github.com/liyupi/yu-ai-agent) | 2,660 | NOASSERTION | Java | 编程导航 AI 开发实战新项目，基于 Spring Boot 3 + Java 21 + Spring AI 构建 AI 恋爱大师应用和 ReAct 模式自主规划智能体YuManus，覆盖 AI 大模型接入、Spri… |
| [brightdata/brightdata-mcp](https://github.com/brightdata/brightdata-mcp) | 2,636 | MIT | JavaScript | A powerful Model Context Protocol (MCP) server that provides an all-in-one solution for public web access. |
| [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) | 2,605 | Apache-2.0 | JavaScript | The most comprehensive toolkit for Claude Code -- 135 agents, 35 curated skills, 42 commands, 176+ plugins, … |
| [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) | 2,190 | MIT | Python | KiCAD MCP is a Model Context Protocol (MCP) implementation that enables Large Language Models (LLMs) like Cl… |
| [stacklok/toolhive](https://github.com/stacklok/toolhive) | 2,156 | Apache-2.0 | Go | ToolHive is an enterprise-grade platform for running and managing Model Context Protocol (MCP) servers. |
| [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) | 2,147 | MIT | Python | FreeCAD MCP(Model Context Protocol) server |

## 浏览器与 Computer Use

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 11.4 万 | MIT | Python | 最主流的 Python 浏览器 Agent 库；快速做网页自动化很对味，长链任务的成功率与 token 成本都要自己加护栏 |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 3.7 万 | Apache-2.0 | TypeScript | 微软官方浏览器 MCP，无障碍树驱动不用截图；省 token、行为确定，给编程 Agent 配浏览能力首选 |
| [feder-cr/AIHawk](https://github.com/feder-cr/AIHawk) | 3.0 万 | MIT | Python | 投简历自动化出圈后转向通用浏览器自动化；象征意义一直大于实用价值，用前确认最新定位 |
| [browserbase/stagehand](https://github.com/browserbase/stagehand) | 2.4 万 | MIT | TypeScript | Browserbase 的 act/extract/observe 浏览器 SDK；自然语言指令与确定性代码可混写，是要认真上生产的方案 |
| [nanobrowser/nanobrowser](https://github.com/nanobrowser/nanobrowser) | 1.4 万 | Apache-2.0 | TypeScript | Chrome 扩展里的多 Agent 自动化；个人流程玩具级入门，可靠性全看目标网站脸色 |
| [magnitudedev/browser-agent](https://github.com/magnitudedev/browser-agent) | 4,128 | Apache-2.0 | TypeScript | 视觉优先的浏览器 Agent；比 DOM 方案慢且贵，只留给 DOM 拿不到的场景 |
| [showlab/ShowUI](https://github.com/showlab/ShowUI) | 1,898 | Apache-2.0 | Python | [CVPR 2025] Open-source, End-to-end, Vision-Language-Action model for GUI Agent & Computer Use. |
| [mediar-ai/terminator](https://github.com/mediar-ai/terminator) | 1,634 | MIT | Rust | playwright for windows computer use |
| [hyperbrowserai/HyperAgent](https://github.com/hyperbrowserai/HyperAgent) | 1,560 | NOASSERTION | TypeScript | AI Browser Automation |
| [AIPexStudio/AIPex](https://github.com/AIPexStudio/AIPex) | 1,250 | MIT | TypeScript | AIPex: AI browser automation assistant, no migration and privacy first. Alternative to Manus Browser Operato… |
| [browserable/browserable](https://github.com/browserable/browserable) | 1,207 | MIT | JavaScript | Open source and self-hostable browser automation library for AI agents |
| [itbrowser-net/undetectable-fingerprint-browser](https://github.com/itbrowser-net/undetectable-fingerprint-browser) | 865 | NOASSERTION | — | Free open-source Multilogin/Incogniton/Kameleo alternative for fingerprint spoofing (Canvas/WebGL/User-Agent… |
| [LvcidPsyche/auto-browser](https://github.com/LvcidPsyche/auto-browser) | 785 | MIT | Python | Give your AI agent a real browser — with a human in the loop. Open-source MCP-native browser agent. |
| [tiliondev/fortress](https://github.com/tiliondev/fortress) | 483 | NOASSERTION | Python | Stealth Chromium engine that stops scrapers and browser agents from getting blocked, with one line of code c… |

## 可观测、评估与安全

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | 3.4 万 | NOASSERTION | TypeScript | 开源自托管 LLM 观测 + 评测的主力；trace 数据模型要早期定好，中途换平台很痛 |
| [SigNoz/signoz](https://github.com/SigNoz/signoz) | 3.2 万 | NOASSERTION | TypeScript | OTel 原生老牌 APM，infra 监控是主业、AI 观测是新增；Agent 语义评测不是它的活 |
| [mlflow/mlflow](https://github.com/mlflow/mlflow) | 2.8 万 | Apache-2.0 | Python | 老牌 ML 生命周期平台补齐了 genai 追踪；团队已在用会很顺手，纯 Agent 项目单采偏重 |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 2.5 万 | MIT | TypeScript | 配置文件驱动的 prompt/Agent 评测与红队；接 CI 最省事，强在断言模型而非界面体验 |
| [comet-ml/opik](https://github.com/comet-ml/opik) | 2.2 万 | Apache-2.0 | Python | Comet 出的 Agent 调试与评测平台；SDK 接入轻，迭代快、跟文档要走最新版 |
| [openobserve/openobserve](https://github.com/openobserve/openobserve) | 2.2 万 | AGPL-3.0 | TypeScript | 轻量一体化日志/指标/追踪平台，LLM 观测是副业；当基础设施监控选它更对 |
| [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | 1.1 万 | NOASSERTION | Python | Arize 的开源 trace + 评测，notebook 体验好；做离线评测的合适起点，规模大了再看托管方案 |
| [maximhq/bifrost](https://github.com/maximhq/bifrost) | 7,946 | Apache-2.0 | Go | Go 写的高性能 AI 网关；性能宣传语要自己复测，功能面全，可作 LiteLLM 的替代候选 |
| [evidentlyai/evidently](https://github.com/evidentlyai/evidently) | 7,903 | Apache-2.0 | Jupyter Notebook | 老牌 ML 数据分布评测报告框架，LLM 场景是延伸；统计报告视角独一份 |
| [traceloop/openllmetry](https://github.com/traceloop/openllmetry) | 7,427 | Apache-2.0 | Python | OpenTelemetry 的 LLM 埋点规范与工具；已有 OTel 栈接进来丝滑，省得自造 trace 格式 |
| [apache/hertzbeat](https://github.com/apache/hertzbeat) | 7,391 | Apache-2.0 | Java | An AI-powered next-generation open source real-time observability system. |
| [GoogleCloudPlatform/agent-starter-pack](https://github.com/GoogleCloudPlatform/agent-starter-pack) | 6,556 | Apache-2.0 | Python | Ship AI Agents to Google Cloud in minutes, not months. Production-ready templates with built-in CI/CD, evalu… |
| [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit) | 6,232 | MIT | Python | AI Agent Governance Toolkit — Policy enforcement, zero-trust identity, execution sandboxing, and reliability… |
| [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | 6,220 | Apache-2.0 | Python | A full-stack AI Red Teaming platform securing AI ecosystems via Agent Scan, Skills Scan, MCP scan, AI Infra … |
| [Helicone/helicone](https://github.com/Helicone/helicone) | 6,142 | Apache-2.0 | TypeScript | 🧊 Open source LLM observability platform. One line of code to monitor, evaluate, and experiment. YC W23 🍓 |
| [elder-plinius/T3MP3ST](https://github.com/elder-plinius/T3MP3ST) | 6,077 | AGPL-3.0 | TypeScript | autonomous red teaming platform; multi-agent offensive-security meta-harness |
| [Giskard-AI/giskard-oss](https://github.com/Giskard-AI/giskard-oss) | 5,807 | Apache-2.0 | Python | 🐢 Open-Source Evaluation & Testing library for LLM Agents |
| [coze-dev/coze-loop](https://github.com/coze-dev/coze-loop) | 5,714 | Apache-2.0 | Go | Next-generation AI Agent Optimization Platform: Cozeloop addresses challenges in AI agent development by pro… |
| [PurpleAILAB/Decepticon](https://github.com/PurpleAILAB/Decepticon) | 5,480 | Apache-2.0 | Python | Autonomous Hacking Agent for Red Team |
| [latitude-dev/latitude-llm](https://github.com/latitude-dev/latitude-llm) | 4,632 | MIT | TypeScript | Open-source observability for AI agents. Find where your agents fail, dispatch your coding agent to fix it, … |
| [pydantic/logfire](https://github.com/pydantic/logfire) | 4,468 | MIT | Python | AI observability platform for production LLM and agent systems. |
| [deepflowio/deepflow](https://github.com/deepflowio/deepflow) | 4,260 | Apache-2.0 | Go | eBPF Observability - Distributed Tracing and Profiling |
| [truera/trulens](https://github.com/truera/trulens) | 3,544 | MIT | Python | Evaluation and Tracking for LLM Experiments and AI Agents |
| [pezzolabs/pezzo](https://github.com/pezzolabs/pezzo) | 3,271 | Apache-2.0 | TypeScript | 🕹️ Open-source, developer-first LLMOps platform designed to streamline prompt design, version management, in… |
| [HolmesGPT/holmesgpt](https://github.com/HolmesGPT/holmesgpt) | 3,260 | Apache-2.0 | Python | SRE Agent - CNCF Sandbox Project |
| [lmnr-ai/lmnr](https://github.com/lmnr-ai/lmnr) | 3,243 | Apache-2.0 | TypeScript | Laminar - open-source observability platform purpose-built for AI agents. YC S24. |
| [kite-org/kite](https://github.com/kite-org/kite) | 3,125 | Apache-2.0 | TypeScript | 🪁 A lightweight, modern Kubernetes dashboard that unifies multi-cluster and resource management, enterprise-… |
| [confident-ai/deepteam](https://github.com/confident-ai/deepteam) | 2,777 | Apache-2.0 | Python | DeepTeam is a framework to red team LLMs and AI agents. |
| [openlit/openlit](https://github.com/openlit/openlit) | 2,752 | Apache-2.0 | TypeScript | Open-source observability & evaluation platform for AI agents and coding agents. Trace LLMs, tools, prompts,… |
| [yaojingang/yao-meta-skill](https://github.com/yaojingang/yao-meta-skill) | 2,608 | MIT | Python | YAO = Yielding AI Outcomes. A rigorous engineering, evaluation, governance, and portability system for reusa… |
| [FailproofAI/failproofai](https://github.com/FailproofAI/failproofai) | 2,604 | NOASSERTION | MDX | Observability and enforcement for AI agent harnesses. Capture every run and runtime reliability with policy … |
| [Armur-Ai/Pentest-Swarm-AI](https://github.com/Armur-Ai/Pentest-Swarm-AI) | 2,484 | AGPL-3.0 | Go | Autonomous penetration testing using a swarm of AI agents. Orchestrates recon, classification, exploitation,… |
| [uptrain-ai/uptrain](https://github.com/uptrain-ai/uptrain) | 2,365 | Apache-2.0 | Python | UpTrain is an open-source unified platform to evaluate and improve Generative AI applications. We provide gr… |
| [MCPJam/inspector](https://github.com/MCPJam/inspector) | 2,195 | NOASSERTION | TypeScript | Testing and evaluation platform to chat, inspect, and debug MCP servers, MCP apps, and ChatGPT apps. |

## 推理与部署

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [ollama/ollama](https://github.com/ollama/ollama) | 18.1 万 | MIT | Go | 一条命令跑起本地模型的体验之王；个人开发与原型首选，生产高并发要换 vLLM 这类 serving 方案 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | 12.8 万 | MIT | C++ | GGUF 生态的地基，消费级设备推理无对手；多租户高并发 serving 得靠上层引擎 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | 9.1 万 | Apache-2.0 | Python | PagedAttention 出处，自托管高吞吐 serving 的默认答案；单卡小模型的新手用它是杀鸡用牛刀 |
| [unslothai/unsloth](https://github.com/unslothai/unsloth) | 7.6 万 | Apache-2.0 | Python | 显存与速度优化的微调库，本地 UI 降门槛；部分进阶能力在商业托管侧，开源版覆盖主流架构 |
| [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) | 7.5 万 | Apache-2.0 | Python | WebUI + YAML 配置式微调瑞士军刀；从零到 LoRA 的最短路径，科研要细粒度控制下沉到 TRL |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | 5.8 万 | NOASSERTION | Python | 多厂商 OpenAI 兼容代理与预算管控的胶水标准件；自托管部署后版本升级要盯紧 |
| [liguodongiot/llm-action](https://github.com/liguodongiot/llm-action) | 2.5 万 | Apache-2.0 | HTML | 中文大模型工程化实战大合集；训推部署运维体系最全的中文参考之一，当手册查很爽别当教程学 |
| [huggingface/trl](https://github.com/huggingface/trl) | 1.9 万 | Apache-2.0 | Python | HF 的 RL 训练库，PPO/GRPO/DPO 标配；难点从来不在库而在奖励与数据，先把评测建好 |
| [mlc-ai/web-llm](https://github.com/mlc-ai/web-llm) | 1.9 万 | Apache-2.0 | TypeScript | 浏览器内 WebGPU 推理；隐私 demo 与边缘场景好用，模型规模受用户内存硬约束 |
| [stas00/ml-engineering](https://github.com/stas00/ml-engineering) | 1.9 万 | CC-BY-SA-4.0 | Python | Stas 的 ML 工程开源书；集群、分布式训练与调试的实战手册，做 Agent infra 前也该读 |
| [bentoml/OpenLLM](https://github.com/bentoml/OpenLLM) | 1.3 万 | Apache-2.0 | Python | Run any open-source LLMs, such as DeepSeek and Llama, as OpenAI compatible API endpoint in the cloud. |
| [cactus-compute/cactus](https://github.com/cactus-compute/cactus) | 5,996 | NOASSERTION | C++ | Quantization, kernels, runtime and inference engine for mobiles, wearables, smart home and robots. |
| [MakazhanAlpamys/Soup](https://github.com/MakazhanAlpamys/Soup) | 5,984 | Apache-2.0 | Python | Fine-tune LLMs from one YAML. Layer streaming trains an 8B model on a 4 GB laptop GPU. |
| [superduper-io/superduper](https://github.com/superduper-io/superduper) | 5,320 | Apache-2.0 | Python | Superduper: End-to-end framework for building custom AI applications and agents. |
| [tencentmusic/cube-studio](https://github.com/tencentmusic/cube-studio) | 5,074 | NOASSERTION | — | cube studio开源云原生一站式机器学习/深度学习/大模型AI平台，mlops算法链路全流程，算力租赁平台，notebook在线开发，拖拉拽任务流pipeline编排，多机多卡分布式训练，超参搜索，推理服务VG… |
| [Kiln-AI/Kiln](https://github.com/Kiln-AI/Kiln) | 5,054 | NOASSERTION | Python | Build, Evaluate, and Optimize AI Systems. Includes evals, RAG, agents, fine-tuning, synthetic data generatio… |
| [predibase/lorax](https://github.com/predibase/lorax) | 3,829 | Apache-2.0 | Python | Multi-LoRA inference server that scales to 1000s of fine-tuned LLMs |
| [vllm-project/vllm-ascend](https://github.com/vllm-project/vllm-ascend) | 2,791 | Apache-2.0 | C++ | Community maintained hardware plugin for vLLM on Ascend |
| [openlake-project/openlake](https://github.com/openlake-project/openlake) | 2,559 | Apache-2.0 | Rust | OpenLake is a high performance storage engine for efficient LLM inference and GPU Training |
| [data-infra/cube-studio](https://github.com/data-infra/cube-studio) | 2,484 | NOASSERTION | Python | cubestudio开源云原生一站式机器学习/深度学习/大模型AI平台/MaaS/mlops/人工智能平台/训推平台，算法全链路流程，多租户，算力租赁平台，token中转，拖拉拽任务流pipeline编排，多机多卡分… |
| [adithya-s-k/AI-Engineering.academy](https://github.com/adithya-s-k/AI-Engineering.academy) | 2,379 | MIT | Jupyter Notebook | Mastering Applied AI, One Concept at a Time |
| [microsoft/aici](https://github.com/microsoft/aici) | 2,077 | MIT | Rust | AICI: Prompts as (Wasm) Programs |
| [intentee/paddler](https://github.com/intentee/paddler) | 1,668 | Apache-2.0 | Rust | Open-source LLM/VLM load balancer and serving platform for self-hosting LLMs (and VLMs) at scale 🏓🦙 Alternat… |
| [AtomicBot-ai/Atomic-Chat](https://github.com/AtomicBot-ai/Atomic-Chat) | 1,456 | NOASSERTION | TypeScript | Local AI app and inference engine for agents. Run open-weight LLMs locally — private, 100% offline on your c… |
| [ZJU-REAL/ClawGUI](https://github.com/ZJU-REAL/ClawGUI) | 1,340 | Apache-2.0 | Python | Build, Evaluate, and Deploy GUI Agents — online RL training, standardized benchmarks, and real-device deploy… |
| [alibaba/rtp-llm](https://github.com/alibaba/rtp-llm) | 1,333 | Apache-2.0 | Python | RTP-LLM: Alibaba's high-performance LLM inference engine for diverse applications. |
| [jmaczan/tiny-vllm](https://github.com/jmaczan/tiny-vllm) | 1,102 | Apache-2.0 | C++ | Build your own high performance LLM inference engine in C++ and CUDA - a smaller version of vLLM |
| [mit-han-lab/TinyChatEngine](https://github.com/mit-han-lab/TinyChatEngine) | 962 | MIT | C++ | TinyChatEngine: On-Device LLM Inference Library |
| [zhihu/ZhiLight](https://github.com/zhihu/ZhiLight) | 908 | Apache-2.0 | C++ | A highly optimized LLM inference acceleration engine for Llama and its variants. |
| [helixml/helix](https://github.com/helixml/helix) | 805 | NOASSERTION | Go | ♾️ Private Agent Fleet with Spec Coding. Each agent gets their own GPU-accelerated desktop. Run Claude, Code… |
| [pegainfer-project/pegainfer](https://github.com/pegainfer-project/pegainfer) | 679 | Apache-2.0 | Rust | Pure Rust + CUDA LLM inference engine — no PyTorch, OpenAI-compatible, serves Qwen3 to Kimi-K2 |
| [GURPREETKAURJETHRA/END-TO-END-GENERATIVE-AI-PROJECTS](https://github.com/GURPREETKAURJETHRA/END-TO-END-GENERATIVE-AI-PROJECTS) | 633 | MIT | — | End to End Generative AI Industry Projects on LLM Models with Deployment_Awesome LLM Projects |
| [warpfront/hipfire](https://github.com/warpfront/hipfire) | 618 | NOASSERTION | Rust | RDNA-native LLM inference engine in Rust. |
| [yassa9/qwen600](https://github.com/yassa9/qwen600) | 560 | MIT | Cuda | Static suckless single batch CUDA-only qwen3-0.6B mini inference engine |

## 沙箱与运行时

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [firecracker-microvm/firecracker](https://github.com/firecracker-microvm/firecracker) | 3.7 万 | Apache-2.0 | Rust | AWS 的 microVM 底座，serverless 沙箱的隔离答案；快照与编排层要自己搭，不是开箱 Agent 沙箱 |
| [trycua/cua](https://github.com/trycua/cua) | 2.2 万 | MIT | HTML | 做 computer-use 训练/评测跨 OS 车队的前瞻项目；方向对但还很早期，别当成熟 infra 用 |
| [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | 1.4 万 | Apache-2.0 | Python | Agent 代码执行云沙箱的热门选择，SDK 体验丝滑；核心能力托管在服务侧，自托管边界要先看清 |
| [agent-infra/sandbox](https://github.com/agent-infra/sandbox) | 5,883 | Apache-2.0 | Python | 单 Docker 容器打包浏览器 + Shell + MCP + VSCode；起步方便跑一体实验，跑不可信代码时单容器隔离不够看 |
| [e2b-dev/open-computer-use](https://github.com/e2b-dev/open-computer-use) | 2,249 | Apache-2.0 | Python | E2B 官方 computer-use 示例；价值在读桌面 loop 与动作空间的工程做法，不是拿来即用的产品 |
| [abshkbh/arrakis](https://github.com/abshkbh/arrakis) | 871 | AGPL-3.0 | Go | A fully customizable and self-hosted sandboxing solution for AI agent code execution and computer use. It fe… |
| [e2b-dev/surf](https://github.com/e2b-dev/surf) | 863 | Apache-2.0 | TypeScript | Surf is a computer use AI agent powered by OpenAI that interacts with a E2B's virtual desktop environment th… |
| [open-gitagent/clawless](https://github.com/open-gitagent/clawless) | 534 | MIT | TypeScript | ClawLess — A serverless browser-based runtime for Claw AI Agents powered by WebContainers |

## 基准、数据集与论文

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [OpenBMB/ToolBench](https://github.com/OpenBMB/ToolBench) | 5,736 | Apache-2.0 | Python | 工具调用数据集的早期经典；造数据的方法论有史料价值，数据本身质量参差 |
| [THUDM/AgentBench](https://github.com/THUDM/AgentBench) | 3,722 | Apache-2.0 | Python | 多环境 Agent 一体考核的经典基准；强模型上已趋饱和，更适合当回归对照而非追前沿 |
| [Meirtz/Awesome-Context-Engineering](https://github.com/Meirtz/Awesome-Context-Engineering) | 3,299 | MIT | — | 上下文工程综述配套论文清单；找文献高效，观点结论要打折读 |
| [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) | 3,127 | Apache-2.0 | Python | arXiv 文献流的 MCP server；研究型 Agent 的常备件，配自己的向量库检索体验更好 |
| [yilewang/llm-for-zotero](https://github.com/yilewang/llm-for-zotero) | 2,940 | AGPL-3.0 | TypeScript | 给自己的 Zotero 文库加 Agent 问答；个人科研很友好，AGPL 许可商用嵌入要谨慎 |
| [luo-junyu/Awesome-Agent-Papers](https://github.com/luo-junyu/Awesome-Agent-Papers) | 2,850 | NOASSERTION | — | LLM Agent 方法学综述的配套论文库；按方法论分类，系统入场的标配 |
| [Shichun-Liu/Agent-Memory-Paper-List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List) | 2,374 | MIT | — | Agent 记忆综述的配套清单；做记忆方向绕不开的系统入口 |
| [jmiao24/Paper2Agent](https://github.com/jmiao24/Paper2Agent) | 2,353 | MIT | Jupyter Notebook | Paper2Agent is a multi-agent AI system that automatically transforms research papers into interactive AI age… |
| [Xnhyacinth/Awesome-LLM-Long-Context-Modeling](https://github.com/Xnhyacinth/Awesome-LLM-Long-Context-Modeling) | 2,168 | MIT | — | 📰 Must-read papers and blogs on LLM based Long Context Modeling 🔥 |
| [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) | 2,001 | MIT | Python | 模拟用户 + 政策约束的 Tool-Agent-User 交互基准；少数经得起复现检验的 Agent 评测之一 |
| [VoltAgent/awesome-ai-agent-papers](https://github.com/VoltAgent/awesome-ai-agent-papers) | 1,765 | MIT | — | A curated collection of AI agent research papers released in 2026, covering agent engineering, memory, evalu… |
| [trycua/acu](https://github.com/trycua/acu) | 1,748 | NOASSERTION | — | A curated list of resources about AI agents for Computer Use, including research papers, projects, framework… |
| [Barca0412/Introduction-to-Quantitative-Finance](https://github.com/Barca0412/Introduction-to-Quantitative-Finance) | 1,737 | MIT | Python | AI+金融（量化）：1.多因子股票量化框架开源教程 2.学界和业界的经典资料收录 3.AI + 金融的相关工作，包括LLM, Agent, benchmark(evaluation), etc. |
| [bytedance/pasa](https://github.com/bytedance/pasa) | 1,658 | Apache-2.0 | Python | PaSa -- an advanced paper search agent powered by large language models. It can autonomously make a series o… |
| [MLSysOps/MLE-agent](https://github.com/MLSysOps/MLE-agent) | 1,570 | MIT | Python | 🤖 MLE-Agent: Your intelligent companion for seamless AI engineering and research. 🔍 Integrate with arxiv and… |
| [sierra-research/tau-bench](https://github.com/sierra-research/tau-bench) | 1,430 | MIT | Python | Code and Data for Tau-Bench |
| [huhusmang/Awesome-LLMs-for-Vulnerability-Detection](https://github.com/huhusmang/Awesome-LLMs-for-Vulnerability-Detection) | 1,413 | MIT | Python | The community's most comprehensive, continuously-updated index of research on Large Language Models for soft… |
| [tmgthb/Autonomous-Agents](https://github.com/tmgthb/Autonomous-Agents) | 1,374 | MIT | — | Autonomous Agents (LLMs) research papers. Updated Daily. |
| [weitianxin/Awesome-Agentic-Reasoning](https://github.com/weitianxin/Awesome-Agentic-Reasoning) | 1,361 | MIT | — | A curated list of papers and resources based on the survey "Agentic Reasoning for Large Language Models" |
| [AutoTrustAI/PaperGuru-Benchmark](https://github.com/AutoTrustAI/PaperGuru-Benchmark) | 1,324 | NOASSERTION | TeX | Lifecycle-Aware Memory for long-horizon LLM agents — 66.05% on PaperBench, 94.66% on SurveyBench, 10 peer-re… |
| [gokayfem/awesome-vlm-architectures](https://github.com/gokayfem/awesome-vlm-architectures) | 1,309 | CC0-1.0 | Markdown | Curated visual catalog of 155+ vision-language model (VLM/MLLM) architectures: papers, diagrams, training re… |
| [git-disl/awesome-LLM-game-agent-papers](https://github.com/git-disl/awesome-LLM-game-agent-papers) | 959 | NOASSERTION | — | A Survey on Large Language Model-Based Game Agents (ACM CSUR) |
| [microsoft/WindowsAgentArena](https://github.com/microsoft/WindowsAgentArena) | 895 | MIT | Python | Windows Agent Arena (WAA) 🪟 is a scalable OS platform for testing and benchmarking of multi-modal AI agents. |
| [google-research/android_world](https://github.com/google-research/android_world) | 882 | Apache-2.0 | Python | AndroidWorld is an environment and benchmark for autonomous agents |
| [benchflow-ai/awesome-evals](https://github.com/benchflow-ai/awesome-evals) | 873 | NOASSERTION | — | A curated, non-BS library of the best resources for building and evaluating AI agents — papers, blogs, talks… |
| [xlang-ai/OpenCUA](https://github.com/xlang-ai/OpenCUA) | 835 | MIT | Python | [NeurIPS 2025 Spotlight] OpenCUA: Open Foundations for Computer-Use Agents |
| [Ayanami0730/deep_research_bench](https://github.com/Ayanami0730/deep_research_bench) | 827 | Apache-2.0 | Python | DeepResearch Bench: A Comprehensive Benchmark for Deep Research Agents |
| [suyoumo/ClawProBench](https://github.com/suyoumo/ClawProBench) | 823 | Apache-2.0 | Rust | ClawProBench is a live-first benchmark harness for evaluating LLM agents   in the OpenClaw runtime with dete… |
| [Purewhiter/mobilegym](https://github.com/Purewhiter/mobilegym) | 787 | Apache-2.0 | Python | [EMNLP 2026] MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mobile GUI Agent Research ·… |
| [TheAgentCompany/TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) | 776 | MIT | Python | An agent benchmark with tasks in a simulated software company. |
| [HKUSTDial/awesome-data-agents](https://github.com/HKUSTDial/awesome-data-agents) | 736 | NOASSERTION | Python | Continuously updated paper list on advancements in Data Agents. Companion repo to our paper "A Survey of Dat… |
| [TIGER-AI-Lab/ClawBench](https://github.com/TIGER-AI-Lab/ClawBench) | 704 | Apache-2.0 | Python | Open-source benchmark for browser AI agents on daily tasks. |
| [YennNing/Awesome-Code-as-Agent-Harness-Papers](https://github.com/YennNing/Awesome-Code-as-Agent-Harness-Papers) | 681 | MIT | — | A curated list of papers and resources based on the survey "Code as Agent Harness" |
| [facebookresearch/BenchMARL](https://github.com/facebookresearch/BenchMARL) | 659 | MIT | Python | BenchMARL is a library for benchmarking Multi-Agent Reinforcement Learning (MARL). BenchMARL allows to quick… |

## 学习资源与 Awesome

| 项目 | Star(2026-09) | 许可 | 语言 | 说明 |
|---|---|---|---|---|
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | 9.5 万 | MIT | — | MCP server 大列表，找货入口；质量参差，接入前逐个审 |
| [dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide) | 7.8 万 | MIT | MDX | dair-ai 的提示/上下文工程指南；概念准、更新勤，动手落地还得另找项目练 |
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | 7.4 万 | MIT | Jupyter Notebook | 微软 18 课入门课；路子正但偏浅，读完要自己往生产场景跨一步 |
| [rohitg00/ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch) | 5.4 万 | MIT | Python | 从零开始的 AI 工程路线，量大管饱；要挑着学，别收藏了当学过 |
| [bojieli/ai-agent-book](https://github.com/bojieli/ai-agent-book) | 4.6 万 | Apache-2.0 | Python | 中文开源书《深入理解 AI Agent》；体系完整且带按章代码，这类中文材料里的稀缺品 |
| [patchy631/ai-engineering-hub](https://github.com/patchy631/ai-engineering-hub) | 3.7 万 | MIT | Jupyter Notebook | 一篇文章一个可跑项目的 RAG/Agent 教程库；抄改起步快，深究原理要另找材料 |
| [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents) | 3.0 万 | NOASSERTION | — | Agent 大全目录；逛一圈可以，商业化倾向明显、时效一般，选型别只靠它 |
| [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) | 2.6 万 | NOASSERTION | TypeScript | 生产级 Agent 的 12 条工程原则；杂文体但观点可直接落地，反框架炒作必读 |
| [datawhalechina/easy-vibe](https://github.com/datawhalechina/easy-vibe) | 1.9 万 | NOASSERTION | JavaScript | 💻  vibe coding 101｜The first course for AI-native product builders. |
| [awesome-opencode/awesome-opencode](https://github.com/awesome-opencode/awesome-opencode) | 1.0 万 | CC0-1.0 | JavaScript | A curated list of awesome plugins, themes, agents, projects, and resources for https://opencode.ai |
| [WangRongsheng/awesome-LLM-resources](https://github.com/WangRongsheng/awesome-LLM-resources) | 8,945 | Apache-2.0 | — | 🧑‍🚀 全世界最好的LLM资料总结（多模态生成、Agent、辅助编程、AI审稿、数据处理、模型训练、模型推理、o1 模型、MCP、小语言模型、视觉语言模型） / Summary of the world's best… |
| [WenyuChiou/awesome-agentic-ai-zh](https://github.com/WenyuChiou/awesome-agentic-ai-zh) | 6,752 | MIT | Python | A trilingual (繁中 / English / 简中) learning roadmap for agentic AI: from LLM basics to multi-agent systems, wi… |
| [fr0gger/Awesome-GPT-Agents](https://github.com/fr0gger/Awesome-GPT-Agents) | 6,595 | Apache-2.0 | — | A curated list of GPT agents for cybersecurity |
| [tensorchord/Awesome-LLMOps](https://github.com/tensorchord/Awesome-LLMOps) | 5,927 | CC0-1.0 | Shell | An awesome & curated list of best LLMOps tools for developers |
| [0xNyk/awesome-hermes-agent](https://github.com/0xNyk/awesome-hermes-agent) | 5,613 | NOASSERTION | — | Independent directory of useful skills, plugins, memory providers, tools, surfaces, and guides for Nous Rese… |
| [PacktPublishing/LLM-Engineers-Handbook](https://github.com/PacktPublishing/LLM-Engineers-Handbook) | 5,319 | MIT | Python | The LLM's practical guide: From the fundamentals to deploying advanced LLM and RAG apps to AWS using LLMOps … |
| [libukai/awesome-agent-skills](https://github.com/libukai/awesome-agent-skills) | 5,079 | NOASSERTION | — | Agent Skills 终极指南：快速入门、资源推荐、精选技能与实用工具 ｜The Ultimate Guide to Agent Skills: QuickStart, Resources, Features&T… |
| [alvinreal/awesome-opensource-ai](https://github.com/alvinreal/awesome-opensource-ai) | 4,708 | CC0-1.0 | Python | Curated list of the best truly open-source AI projects, models, tools, and infrastructure. Daily updated. |
| [decodingai-magazine/llm-twin-course](https://github.com/decodingai-magazine/llm-twin-course) | 4,384 | MIT | Python | 🤖 𝗟𝗲𝗮𝗿𝗻 for 𝗳𝗿𝗲𝗲 how to 𝗯𝘂𝗶𝗹𝗱 an end-to-end 𝗽𝗿𝗼𝗱𝘂𝗰𝘁𝗶𝗼𝗻-𝗿𝗲𝗮𝗱𝘆 𝗟𝗟𝗠 & 𝗥𝗔𝗚 𝘀𝘆𝘀𝘁𝗲𝗺 using 𝗟𝗟𝗠𝗢𝗽𝘀 best practices: ~… |
| [wesammustafa/Claude-Code-Everything-You-Need-to-Know](https://github.com/wesammustafa/Claude-Code-Everything-You-Need-to-Know) | 2,988 | MIT | Python | A practical Claude Code guide with clear mental models and copy-paste examples — setup, prompt engineering, … |
| [kyrolabs/awesome-agents](https://github.com/kyrolabs/awesome-agents) | 2,806 | NOASSERTION | — | 🤖 Awesome list of AI Agents |
| [webfuse-com/awesome-autoresearch](https://github.com/webfuse-com/awesome-autoresearch) | 2,520 | NOASSERTION | — | A curated list of autonomous improvement loops, research agents, and autoresearch-style systems inspired by … |
| [study8677/awesome-architecture](https://github.com/study8677/awesome-architecture) | 2,300 | MIT | Vue | 🧭 Architecture-first system design: 26 bilingual tutorials, 25 architecture templates, and 6 end-to-end case… |
| [vonzosten/awesome-LangGraph](https://github.com/vonzosten/awesome-LangGraph) | 1,994 | CC0-1.0 | JavaScript | An index of the LangChain + LangGraph ecosystem: concepts, projects, tools, templates, and guides for LLM & … |
| [jim-schwoebel/awesome_ai_agents](https://github.com/jim-schwoebel/awesome_ai_agents) | 1,970 | Apache-2.0 | — | 🤖 A comprehensive list of 1,500+ resources and tools related to AI agents. |
| [thinkwee/AgentsMeetRL](https://github.com/thinkwee/AgentsMeetRL) | 1,837 | NOASSERTION | HTML | Awesome List for Agentic RL |
| [caramaschiHG/awesome-ai-agents-2026](https://github.com/caramaschiHG/awesome-ai-agents-2026) | 1,798 | NOASSERTION | — | 🤖 The most comprehensive list of AI agents, frameworks & tools in 2026. 300+ resources · 20+ categories · Up… |
| [Picrew/awesome-agent-harness](https://github.com/Picrew/awesome-agent-harness) | 1,745 | NOASSERTION | Python | An awesome list of Agent Harness engineering resources, including GitHub projects, tools, benchmarks, and pr… |
| [kaushikb11/awesome-llm-agents](https://github.com/kaushikb11/awesome-llm-agents) | 1,579 | CC0-1.0 | Python | A curated list of awesome LLM agents frameworks. |
| [showlab/Awesome-GUI-Agent](https://github.com/showlab/Awesome-GUI-Agent) | 1,216 | NOASSERTION | — | 💻 A curated list of papers and resources for multi-modal Graphical User Interface (GUI) agents. |
| [dariubs/awesome-workflow-automation](https://github.com/dariubs/awesome-workflow-automation) | 1,214 | MIT | — | A curated list of Workflow Automation  Software, Engines and Tools |
| [scadastrangelove/awesome-ai-security-tools](https://github.com/scadastrangelove/awesome-ai-security-tools) | 1,114 | NOASSERTION | Python | A curated list of public-source, research, and commercial tools for AI security and AI-assisted cybersecurit… |
| [fancyboi999/ai-engineering-from-scratch-zh](https://github.com/fancyboi999/ai-engineering-from-scratch-zh) | 1,052 | MIT | Python | Agent工程师最全学习路径 · 从零精通 AI 工程 · 20 阶段 503 课 · 中文全量翻译 + 配套站点 + 动画讲解视频 · 如何成为 AI Agent 工程师的修成指南 |
| [RUC-NLPIR/Awesome-Long-Horizon-Agents](https://github.com/RUC-NLPIR/Awesome-Long-Horizon-Agents) | 1,012 | MIT | — | The roadmap of long-horizon agents |

## 相关知识点

- [框架与生态](../../09-frameworks/README.md)
- [工具调用与协议](../../05-tool-protocol/README.md)
- [记忆与 RAG](../../06-memory-rag/README.md)

