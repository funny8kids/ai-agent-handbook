---
tags: [index, handbook]
type: index
status: published
updated: 2026-09-23
---

# AI Agent 手册 · AI Agent Handbook

![AI Agent 学习手册 · 从原理到生产](.gitbook/assets/banner-home.svg)

**从原理到生产**：LLM 与注意力 · Agent 循环 · 工具协议 · 记忆与 RAG · 规划 · 多智能体 · 评估与安全 · 工程化 · AI 基础设施 · 具身智能

**From theory to production**: LLMs & attention · agent loops · tool protocols · memory & RAG · planning · multi-agent · evaluation & safety · engineering · AI infrastructure · embodied AI · **2026 frontier**

> **中文**：一本持续更新的开源 AI Agent 手册与资源库：196 页 / 19 章，含 2026-09 前沿（GPT-6 Astra、Agents API、Claude Fable 5.1、System One 决策模型）与 6 个可离线真实运行的动手实验。每一页都要求「把话说实」——原理给出公式与推导、结论给出可点开的出处、流程给成分步演示与可点标签（全书正文不贴可执行代码，接口只给真实字段契约）。
>
> **English**: A continuously updated, open-source AI Agent handbook and resource library — 196 pages across 19 chapters, including a 2026 frontier chapter (GPT-6 Astra, Agents API, Claude Fable 5.1, **System One decision models**), 108 of them carrying rendered formulas, plus 6 offline-runnable hands-on labs and an index of 323 open-source projects. Every page has to show its work: principles come with derivations, claims link to primary sources, and processes are stepped out as interactive walkthroughs rather than pasted code.

## 快速开始 · Quick start

| 你是 · You are | 路线 · Route | 通关标准 · Done when |
|---|---|---|
| 只会用 ChatGPT · New to LLMs | 01 → 02 → 03 → 04 | 能讲清「Agent 与 Chatbot 的区别」· explain agent vs chatbot |
| 有开发经验 · Engineer | 02 → 05 → 06 → 09 → 11 | 能写出会调工具、能恢复错误的 Agent · ship an agent with tools & recovery |
| 关注前沿与论文 · Researcher | 04 → 08 → 10 | 能读懂 ReAct 并复现核心循环 · reproduce the ReAct loop |
| 要搭团队底座 · Platform / Infra | 03 → 11 → 16 | 能给出 TTFT/TPOT/缓存命中率/成本基线 · set cost & latency baselines |
| 做机器人或想转具身 · Robotics | 02 → 04 → 17 → 16 | 能跑通「感知→技能→执行」闭环 · close a perceive→skill→act loop |
| 追前沿与选型 · Frontier / Buyer | 02 → 18 → 10 → 12 | 能读懂 Astra / Agents API / Fable 5.1 对比并做 harness 选型 · pick a 2026 stack |
| 想动手写代码 · Hands-on | 02 → 04 → 06 → 19 | 能离线跑通 6 个实验、把 MockLLM 换成真 API · run all 6 labs offline, then swap in a real model |

完整路线、前置知识与自检标准 · Full paths, prerequisites & self-checks：**[学习路线 Learning path](00-index/learning-path.md)**

![学习路线：四个阶段 · Four-stage learning path](.gitbook/assets/00-learning-path.svg)

*《图：四阶段路线是按「能否自检」切分的——每块底部写着过关标准，达不到就别进下一阶段》*
## 边学边做 · Hands-on labs

第 19 章是 6 个**纯标准库、零 API Key、离线可跑**的动手实验：手写最小 ReAct 闭环 → 迷你 BM25 RAG → 迷你 MCP 服务 → 三角色协作 → 评测与 trace → 护栏与接真模型。页面里不放代码，改成一步步的**分步演示**与**可点标签**（对照组、失败分支都能点开看），配的每一份输出都是本机真跑出来的原文——第 54 轮把这句话逐条复跑核对过：六页共 95 个引用数字，60 个直接对上默认运行，剩下 35 个逐条追查后 33 个用「把改动重新做一遍」复现（lab6 的 3/8=38% 误伤与 2/4 漏防、lab4 的消息数 7→9 与总线 298→303 字、lab3 的 -32601 报文与三工具发现行、lab2 三组标签与两个 b 值的完整排序），2 个是判据假阳性（`"temperature": 0.2` 那类写在 JSON 契约里的字段本就不是运行输出）；核对过程中修掉了 lab3 服务端一处真 bug。脚本自己在仓库 `labs/` 下，六个文件各自自包含，看懂后把 MockLLM 换成真 API 主循环一行不改。

👉 **[进入动手实验 · Start the labs](19-labs/README.md)**

## 必读 12 个 · Top 12 must-reads

| 资源 · Resource | 一句话 · In one line |
|---|---|
| [2026 前沿模型地图](18-frontier-2026/frontier-models-2026.md) | GPT-6 Astra 与 Claude Fable 5.1 怎么比、怎么买 |
| [OpenAI Agents API](18-frontier-2026/openai-agents-api.md) | 托管 Codex harness：压缩 / tool search / 子 Agent |
| [ReAct 论文](13-resources/papers/react.md) | 现代 Agent 循环的思想源头 · the origin of the think-act-observe loop |
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | 什么时候用工作流、什么时候才该上 Agent · workflow vs agent, and when |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | Transformer 原始论文，一切 LLM 的底座 · the paper every LLM builds on |
| [DeepSeek-R1](https://arxiv.org/abs/2501.12948) | 用可验证奖励做 RL，训出推理能力 · RL with verifiable rewards |
| [Pi Agent](https://github.com/earendil-works/pi) | 极简 harness 的活教材 · a minimal harness you can read end to end |
| [Claude Agent SDK](18-frontier-2026/claude-agent-sdk.md) | 把 Claude Code 内核嵌进自己进程 |
| [MCP 官方文档](https://modelcontextprotocol.io/docs/learn/architecture) | 工具接入的事实标准 · the de-facto tool protocol |
| [AI Agents for Beginners](13-resources/courses/ai-agents-for-beginners.md) | 微软官方免费入门课 · Microsoft's free beginner course |
| [SWE-bench](13-resources/benchmarks/swe-bench.md) | 编程 Agent 的标准考场 · the standard arena for coding agents |
| [评估 2026](18-frontier-2026/eval-2026.md) | Terminal-Bench 4.0 / OSWorld 2.0 读榜纪律 |

## 按主题挑资源 · Browse by topic

**2026 前沿 · Frontier** · [本章导读](18-frontier-2026/README.md) · [模型地图](18-frontier-2026/frontier-models-2026.md) · [Agents API](18-frontier-2026/openai-agents-api.md) · [Agent SDK](18-frontier-2026/claude-agent-sdk.md) · [Harness 分类学](18-frontier-2026/model-native-vs-harness.md) · [评估 2026](18-frontier-2026/eval-2026.md) · [安全 2026](10-evaluation-safety/safety-incidents-2026.md)

**框架与编排 · Frameworks** · [LangChain](09-frameworks/langchain.md) · [LangGraph](09-frameworks/langgraph.md) · [AutoGen](09-frameworks/autogen.md) · [CrewAI](09-frameworks/crewai.md) · [DSPy](09-frameworks/dspy.md) · [LlamaIndex](09-frameworks/llamaindex.md) · [Semantic Kernel](09-frameworks/semantic-kernel.md) · [OpenAI Agents SDK](09-frameworks/openai-agents-sdk.md) · [Claude Agent SDK](18-frontier-2026/claude-agent-sdk.md) · [完整项目索引 Full index](13-resources/projects/README.md)

**编程 Agent 与 Harness · Coding agents** · [编程 Agent 案例](12-applications/coding-agent.md) · [deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) · [Pi](https://github.com/earendil-works/pi) · [Codex](https://github.com/openai/codex) · [Gemini CLI](https://github.com/google-gemini/gemini-cli) · [SWE-agent](https://github.com/SWE-agent/SWE-agent) · [Aider](https://github.com/Aider-AI/aider) · [Claude Code 提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts)

**记忆与 RAG · Memory & RAG** · [RAG 基础](06-memory-rag/rag-basics.md) · [Embedding 与相似度](06-memory-rag/embedding-similarity.md) · [向量数据库](06-memory-rag/vector-database.md) · [GraphRAG](06-memory-rag/graphrag.md) · [知识图谱](06-memory-rag/knowledge-graph.md) · [LlamaIndex](https://github.com/run-llama/llama_index) · [RAGFlow](https://github.com/infiniflow/ragflow) · [Mem0](https://github.com/mem0ai/mem0) · [Milvus](https://github.com/milvus-io/milvus) · [Qdrant](https://github.com/qdrant/qdrant) · [pgvector](https://github.com/pgvector/pgvector) · [FAISS](https://github.com/facebookresearch/faiss)

**工具与协议 · Tools & protocols** · [Function Calling](05-tool-protocol/function-calling.md) · [MCP](05-tool-protocol/mcp.md) · [A2A](05-tool-protocol/a2a.md) · [工具权限与沙箱](05-tool-protocol/tool-permission-sandbox.md) · [MCP Servers](https://github.com/modelcontextprotocol/servers) · [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) · [A2A 仓库](https://github.com/a2aproject/A2A)

**浏览器与 Computer Use · Browser & computer use** · [Computer Use / Browser Use](05-tool-protocol/computer-use-browser-use.md) · [Computer Use 2026](18-frontier-2026/computer-use-2026.md) · [通用 Agent 产品](12-applications/general-agent-products.md) · [browser-use](https://github.com/browser-use/browser-use) · [Playwright MCP](https://github.com/microsoft/playwright-mcp) · [Stagehand](https://github.com/browserbase/stagehand) · [cua](https://github.com/trycua/cua)

**评估、安全与对齐 · Evaluation & safety** · [Agent 评估指标](10-evaluation-safety/evaluation-metrics.md) · [基准测试总览](10-evaluation-safety/benchmarks.md) · [评估 2026](18-frontier-2026/eval-2026.md) · [2026 安全现实](10-evaluation-safety/safety-incidents-2026.md) · [幻觉问题](10-evaluation-safety/hallucination.md) · [提示注入](10-evaluation-safety/prompt-injection.md) · [越狱攻击](10-evaluation-safety/jailbreak.md) · [权限与沙箱](10-evaluation-safety/permission-sandbox.md)

**推理与部署 · Inference & deployment** · [推理、量化与部署](03-llm/inference-quantization-deployment.md) · [vLLM](https://github.com/vllm-project/vllm) · [llama.cpp](https://github.com/ggml-org/llama.cpp) · [Ollama](https://github.com/ollama/ollama) · [LiteLLM](https://github.com/BerriAI/litellm) · [unsloth](https://github.com/unslothai/unsloth) · [LlamaFactory](https://github.com/hiyouga/LlamaFactory) · [TRL](https://github.com/huggingface/trl)

**沙箱与运行时 · Sandboxes & runtimes** · [权限控制与沙箱隔离](10-evaluation-safety/permission-sandbox.md) · [E2B](https://github.com/e2b-dev/E2B) · [Firecracker](https://github.com/firecracker-microvm/firecracker) · [agent-infra/sandbox](https://github.com/agent-infra/sandbox)

**基准与数据集 · Benchmarks & datasets** · [SWE-bench](13-resources/benchmarks/swe-bench.md) · [GAIA](13-resources/benchmarks/gaia.md) · [WebArena](13-resources/benchmarks/webarena.md) · [AgentBench](https://github.com/THUDM/AgentBench) · [ToolBench / BFCL](https://gorilla.cs.berkeley.edu/leaderboard) · [τ-bench](https://github.com/sierra-research/tau-bench) · [OSWorld](https://os-world.github.io/) · [数据集索引](13-resources/datasets/README.md)

**论文 · Papers** · [ReAct](https://arxiv.org/abs/2210.03629) · [CoT](https://arxiv.org/abs/2201.11903) · [ToT](https://arxiv.org/abs/2305.10601) · [Reflexion](https://arxiv.org/abs/2303.11366) · [Toolformer](https://arxiv.org/abs/2302.04761) · [InstructGPT / RLHF](https://arxiv.org/abs/2203.02155) · [DPO](https://arxiv.org/abs/2305.18290) · [LoRA](https://arxiv.org/abs/2106.09685) · [RAG](https://arxiv.org/abs/2005.11401) · [GraphRAG](https://arxiv.org/abs/2404.16130) · [MemGPT](https://arxiv.org/abs/2310.08560) · [SWE-bench](https://arxiv.org/abs/2310.06770) · [论文索引](13-resources/papers/README.md)

**课程、博客与社区 · Courses, blogs & communities** · [AI Agents for Beginners](13-resources/courses/README.md) · [LangChain Academy](https://academy.langchain.com) · [HF Agents Course](https://huggingface.co/learn/agents-course) · [Anthropic 工程博客](https://www.anthropic.com/engineering) · [Lilian Weng](https://lilianweng.github.io/) · [Simon Willison](https://simonwillison.net/) · [社区清单](13-resources/communities/README.md) · [Awesome 列表](13-resources/awesome-lists/README.md)

## 关于这本手册 · About this handbook

- **196 页 / 19 章**（含 2026 前沿章 + 6 个离线动手实验）· 196 pages across 19 chapters。口径说清：这 196 是**已发布页面数**（本地 `docs/` 下 `.md` 减 `SUMMARY.md` 与截图清单），含首页与 3 个模板/指南页；纯正文是 193 篇。与线上 `llms.txt` 的页面数一一对过，不是估的
- **108 篇页面含 KaTeX 公式，共 927 条**（判据**已落库可复跑**：`tools/checks/check_katex_formulas.py` + `katex_render.mjs`，与线上结构对平轴**共用同一个分词器**——先剥围栏与行内代码，独占一行的 `$$` 才算展示块，其余 `$$` 在**同一段落内**配对，然后逐条过真 `katex@0.18.7` `renderToString(throwOnError)`（版本钉在 `tools/checks/data/katex/package.json`，第 59 轮起：解析到别的构建就 `exit 2` 不出数——线上不吐 KaTeX 版本号，实测整页 HTML 里 `katex` 只在类名里，所以这条轴钉本地而不是对齐线上），**0 解析失败**；范围是 193 篇正文，含本页与更新日志，模板页代码块里的示例写法不算。把更新日志页排除则是 107 篇 / 917 条（第 60 轮：5 处跨页复述的公式改成指向后 928→927，被指向的权威页一条没动）。公式数**只认这一个判据脚本**的读数——第 56 轮及以前它只存在于临时目录，同一棵树因此同时有过 930 / 931 / 943 三个数，本轮起它进了仓库，那三个读数全部作废）· 108 pages carry rendered formulas
- **数字与结论都能点回一手来源**，文末「参考资料」只放外部来源 · every claim links back to a primary source
- **每章「读完能做到」清单 + 章末自测 + 中英术语速查**：全量覆盖，题目可答、答案有出处
- **251 个 GitBook 原生提示卡 + 54 组分步演示（279 步）+ 52 组可点标签（195 个页签）**：一句话结论 / 易踩的坑 / 风险警示分色呈现，流程与分支结局用交互组件逐步走完（逐文件点数，代码块与行内代码里的写法示例不计入）
- **正文零可执行代码**：需要动手的地方给的是**真实字段契约**（`json`/`yaml`，每份都过 `json.loads`）与分步演示；六个实验的脚本仍在仓库 `labs/` 下可离线真跑，页面按路径指过去。第 54 轮据此清零了 55 页 / 60 块 / 1502 行代码，同时正文净增 12.1 万字符（新增 17.7 万、删除 5.6 万，剥掉 Markdown 符号后按字符计，58 个被改文件）
- **叫读者去看出处的句子，必须给可点的链接**：`tools/checks/check_source_pointers.py` 只认一种句子形状——同一个短句里既有「去看」的动词（`详见`/`参见`/`参考`/`见`，且不能是 `常见`、`看见` 的尾巴）又点了一份外部文件（官方、发布页、条款、论文、公告、SDK…），而这一行没有任何 Markdown 链接。全站读数 `pages=191 pointer_lines=3 findings=0`；同一判据对修复前的 HEAD 读 **5**、修复后读 **0**，真实页变异控制 `0 → 1 → 0`，锚点腿的正控制是**修前那段措辞渲染出 0 个 `<a href>`**（否则「6 个链接都在」与「一个都没渲染」同数）。这条轴是**收窄**出来的：先按「带数字却没链接」扫过一遍，读数 **247 处 / 71 页**，逐条看过才发现它把本书自己的工程经验值（`输入 token 常是输出的 10–50 倍`，根本无从引用）和别人的数字混为一谈——照它改只会逼作者在每句经验值后面挂不相干链接，**判据自己就成了灌水源**。判据内部还常驻 12 条 look-alike 反例（`错误原文回填给模型`、`（可含论文、官方文档、源码）`、`只参考有权限的文档`、`## 常见基准`、「（见本页末尾）」这类同页导航、项目卡片里的「详见仓库」——卡片首行本来就链着那个仓库）
- **全书 217 张 Mermaid 图经真解析器逐块校验**，0 渲染风险；每张图的自然宽度都用**与线上同版本**（mermaid 11.14.0）的引擎实测过，最宽 1116px。**「最宽 1116px，全部落在正文列宽（1120px）内，线上不会被缩放」这句从第 21 轮站到第 61 轮，是假的**：线上读者默认的正文列实测 **768px**（`layout-wide` 才给 1152，而它默认不开），Mermaid 出厂 `useMaxWidth: true`——SVG 带 `width="100%"` + `style="max-width: 自然宽"`，超宽的图连标签一起**缩小**塞进列里。按真实列宽重跑全站：102 张超宽、101 张被缩小、**0 张能横向滚动**，24 张标签实绘 <12px、最小 **11.0px**（正文 16px）。判据**第 58 轮起已落库可复跑**：`tools/checks/check_mermaid_geometry.py` 用无头 Edge 把 217 块**逐块真渲染**并读回 viewBox，引擎版本从线上页面 markup 里读出来与本地断言相等（不等就直接退出，不出数），每轮再埋两张必须被捉住的雷（一张 2420px 的超宽链、一张残缺语法）。判据自己也在第 62 轮被抓到过一次坏的：fixture 里 `--column` 形参没生效、永远按 1120 排版，于是报出「0 张缩放、217 张横向滚动」两条假话——现在同一趟会把 SVG 自己的 `width`/`style` 属性记回来，缩放还是滚动一次跑就能重验；列宽本身由 `tools/checks/check_live_column.py` 在线上量（500px 与 1100px 两个控制盒先自证尺子不夹紧）。把 102 张压回 768、请站点开宽版布局、还是给超宽块加 `useMaxWidth:false` 让它可横滚保住 16px 字，是版式取舍；**第 62 轮操作者选了开宽版布局**，于是拿站点自己的 CSS 在本机复量了那条路给多少：`<main>` 从 768 → **1152**，1116px 那张图实绘从 768（标签 11.01px）→ **1116（标签 16.0px）**；扣掉与默认布局同比例的内缩（默认 768 列实测段落只有 707px，即内缩约 61px），可用格约 **1091px**，按它复跑全站还剩 **14 张**轻微超宽（1092–1116px，最小标签 15.6px），「24 张 <12px」清零。开关在站点设置里、仓库改不到，所以判据 `COLUMN` 仍是 768，等你切完、`check_live_column.py` 线上复跑出 ~1152 再放宽。详见更新日志第 62 次第六节。最高的一张 1689px，只影响滚动不影响可读性，所以**判宽不判高**
- **154 篇知识/资源页全部有「参考资料」**（按 frontmatter `type` 统计，不是靠肉眼挑）：339 条去重后的外部一手来源逐条点开核对（arXiv 编号用 export API 比对论文标题），站内跳转一律不混入该小节
- **323 个项目索引**（实测 star 与许可，头部项目配手写点评）· an index of 323 projects with observed stars and hand-written takes
- **257 张页内配图**：217 个 Mermaid 内联图（全部带章节配色）+ 32 张页内自绘 SVG（含站内横幅与 4 张高保真工具界面示意）+ **8 张真实产品界面截图**（Langfuse、MCP Inspector、OpenHands、Dify、Open WebUI、Arize Phoenix、AutoGen Studio、LangSmith，逐张标注来源 URL 与访问日期）· 257 in-page figures, parser-verified diagrams + real product UI screenshots。按**放置次数**算是 262 处，差的那 5 处是 4 张 SVG 与 1 张截图跨页复用；另有 3 张自绘 SVG（封面与两枚站标）只在站点设置与仓库 README 里用，不在正文页，故不计入配图数
- **215 条读者可见图注**：每张 SVG/截图下方都写了一句「读这张图要带走什么」——因为线上量到 GitBook 会把内容图片的 `alt` **属性清空**（`alt=""`），只在 `<figcaption>` 里把作者写的 alt 印出来（第 58 轮实测，此前这里的说法是半对的）；45 处图片放置里 44 处带注（另 1 处是首页装饰横幅），217 张 Mermaid **171 张带图注、46 张由图前或图后实质引导语解释，逐块量过：0 张裸图**，**没有一张图是「如下图所示」四个字打发的**
- **线上图片真的打得开**：`tools/checks/check_live_images.py` 把本地写的每一张图与**线上页面**实际吐出的 `<img>` 对平（漏图 / 多图 / 图注没到页面 / 图片 404 或非 `image/*` 或小于 200B / SVG 被转成位图丢动画），全站读数 `pages=36 refs=45 唯一资产=40（32 SVG + 8 PNG）problems=0`。绿色是用**线上变异控制**换来的：把一页的作者侧改坏，EXTRA + DROPPED + NOCAPTION 三条必须同时响
- **标题里没有会被当成标记的符号**：GitBook 会把每个标题的文本**再印一遍**放进侧栏与「本页目录」，那一份**丢掉行内代码格式**——所以标题里写 `` `$$` ``，正文看着是代码，目录里读者看到的是裸 `$$`。这条线上量到（更新日志 2 处，SSR 全站对平轴 `authored=174 checked=174` 里唯一的一条 LEAK-NAV），离线由 `check_structure.py` 的 HEAD 判据守住：围栏外的标题行含 `{%`/`%}`/`$$` 即报，修复后读数 2→0，全站 198 页 0 问题
- **更新日志不许吃掉上一轮的条目标题**：`tools/checks/check_changelog_headings.py` 把 HEAD 里那份本页的条目标题集合与工作区比，只报「HEAD 有、工作区没了」。这条是被自己的事故逼出来的：第 59 次的提交吃掉了第 58 次的条目标题，正文还在，所以 198 页结构轴、公式轴全部照绿，而整轮记录会挂到下一轮的标题底下、本页目录少一条。「编号必须连续」这种更聪明的判据量不出来——全站编号本来就有 8 个洞（那几轮做了事没写日志）。真实数据两腿：`HEAD~1` 对坏的那次提交 = **1 条丢失**，对修好的工作区 = **0**；判据内部还有四条反例（吃掉中间一条 / 原样不动 / 删掉尾条 / 编号有洞必须读成干净）
- **线上对平轴的读数分两桶**：`tools/checks/live_aria_manifest.py --all --headless` 把「内容对不平」（SSR-PARITY / LEAK / LEAK-NAV / SHAPE / FORMULA）记进 `problems`，把「这一页压根没抓到」（读超时）另记 `fetch-failures`；**两桶任一非空都 `exit 1`**——没抓到的页面什么都没证明，不能读成绿。分桶之前它们共用一个计数，全站两次复跑先读出 `problems=4` 再读出 `problems=3`、命中的页面还完全不同，而两条里的内容级发现都是 0：同一个数字既能表示"网络抖了一下"又能表示"读者少了一个组件"，下一轮就会有人去修噪声。分桶后 `authored=174 checked=174 problems=0 fetch-failures=0 fallback-pages=0`，这是这条轴第一次读到"0 内容问题 + 0 未检页"。四条常驻反例钉住桶的边界：抖动的 fetch 不得进内容桶、真的对不平不得躲进 fetch 桶、匹配页必须算作已检、缩水页留在内容桶
- **行内代码里不写转义反引号**：反斜杠 escape 不了代码跨度的定界符，跨度会在第一个反引号处提前闭合，被丢下的两个定界符再由 KaTeX 配成一对——**中间那句话渲染成空公式，直接从页面上消失**。这类缺陷线上量不出来（同页 HTML 里 184 个 `$$`，读者可见正文 0 个，LEAK 与 KaTeX 计数对平两条轴都不响），所以闸放在作者侧：`check_structure.py` 的 BT 判据对围栏外含转义反引号的行即报。全站该写法实测只有 1 处（就是上一轮写进更新日志的一句），修后 1→0，198 页 0 问题
- **跨页不重复印同一句话、同一条公式**：`tools/checks/check_prose_duplicates.py`（第 60 轮落库）把 191 篇正文切成「句子 / 公式」单元，两两比字符 6-gram 的 Jaccard 相似度。**两遍**：整单元完全相同走 EXACT（不设上限），近似相同走 NEAR（跳过被 25 个以上单元共享的热门 shingle——不加这道限，一句被 30 页抄时判据反而全哑，第 60 轮的探索版就栽过）。范围剔除更新日志（按设计要引用页面原文）、`SUMMARY.md`（导航标签必须等于页标题）与「参考资料」「相关知识点」两节（引文与互链本就重复）。全站读数 `pages=191 prose_units=7116 formula_units=274 dup=0 near-band(0.72–0.85)=3`（`prose_units` 随正文增长而变，第 60 轮落库时是 7104，第 63 轮复跑是 7117，且本首页自己算一篇——改这段字它就会再动，判据读数只认当前树）；本轮把量到的 **6 条跨页复述公式**改成「白话结论 + 指向权威页」，公式数 928→927，而**被指向的那两页一条定义都没删**。绿色由两组控制撑着：合成语料 5 条反例，外加拿 6 张真实页「种一句话再撤走」的 0→1→0 变化量（第一次种在页尾落进了被排除的「相关知识点」节、第二次种在第 1 行落进了 frontmatter，两次都读出"干净"——那是判据的假阴性，不是内容的清白）。近重复带里剩 3 条、最高 0.778，全是模板页与章索引页互说「收录标准 / 配图要求」的短句，语义上本就该一致，记为 advisory 不判红
- **公式和表格要放进读者真实的那一列，不是设计稿的宽度**：第 63 轮新增两条轴。`tools/checks/check_content_overflow.py` 把 **276 条 display 公式**过真 `katex@0.18.7` 渲染成浏览器 HTML，塞进与线上同款的 `max-w-3xl` + `overflow-x-auto` 盒子里，用无头 Edge 量**墨迹宽**（不是盒子宽——KaTeX 的 `.katex` 是 `display:block`，量盒子永远"放得下"）；修复前 2 条越列（自然宽 **877.7 / 862.7px** > 768），改成 `aligned`  stacked 后复跑 `measured=276 over-column=0 max=766 render-errors=0`，**一个字都没删**。这条轴还推翻了自己最初的假设：原以为居中溢出的**左半边**滚不到（`scrollWidth` 只数末端），实测种一棵 2807px 的雷读出 `lostLeft=0 lostRight=0`——Chromium 把溢出全放在末端且能滚到，所以真实缺陷是**拖拽距离**，`unreachable` 每轮恒为 0 并被常驻断言钉着（哪天不再为 0 就是平台改了行为，先重读前提）。`tools/checks/check_table_overflow.py` 管另一半：GitBook 的表格不是 `<table>`，每格 `min-width: clamp(100px, …)` 而容器 `w-fit` + `overflow-x: visible`（**压根没有横向滚动条**），所以列数 × 100px 一旦超过 768 就直接顶穿正文列——离线量全站 `pages=175 rows=2218 cells=7637 widest=6`（6 列 600px 还在，8 列就是悬崖），浏览器侧在最长不可断 token 的 8 页读回 **2131 格、spill=0、bust=0**。0 是拿控制换的：同一格塞进 65 字符无断点 token，保留平台 `overflow-wrap:anywhere` 读 0 spill、关掉它读 **205~298px** 溢出。这轮还学到一件事并写进判据：带连字符的长文件名**不是**不可断串（浏览器在 `-` 后换行），最初拿它当雷时控制哑火
- **自绘 SVG 的标签到读者眼里还剩几像素**：第 64 轮新增轴 `tools/checks/check_svg_legibility.py`。线上把正文 SVG 画成 `<img style="max-width:100%">`，所以**画布比正文列宽就整张缩小，字跟着缩**（浏览器实测：1920 画布 scale 0.4、960 画布 0.8，`<main>` 768）。有效字号 = authored px × min(1, 列宽/画布宽)，对 32 张正文图、1042 个 `<text>`/`<tspan>`（含从 `<svg>`/`<g>` 继承的字号）逐张量：**32 张全部至少有一个标签低于 12px 门槛，956/1042 个标签命中，最小 5.20px**——最险的是**首页封面横幅**（13px 写在 1920 画布上）。`--column 1152` 复跑得 23 张 / 378 个：**宽版布局只去掉缩小，救不了小字**。等比放大图等于没放大，机械 bump 是渲染出来看的（`03-context-budget.svg` 三版真渲染：×1.25 干净、够到 12px 的 ×1.58 撑破药丸框并撞字），所以**逐张重排文字/画布比例属产品级取舍，本轮 0 改图、轴照旧红**（`exit 1`，不为绿灯降门槛）。判据带两条常驻控制：几何 ruler（种 1920/960/400 三张画布，scale 必须等于 `min(1, 列宽/自然宽)`，列相对断言所以开关一开不用改），和 classifier selftest（真实树里 32/32 张全 FAIL，「见谁都报缺陷」与「量到缺陷」输出长得一样——必须种一张 400 画布的**干净图**读 0 命中，外加一张只该捉住 9.5px、不该捉住 16px 的脏图）。这一轮也被自己的口径骗过一次：`"/." in "/" + rel_dir` 会连内容根一起排除，首页整页被跳过，最险的那张图从统计里消失、轴在 31 张上自称跑完——和 README 的「32 张」对平才把它揪出来。**同一趟线上截图又抓到两条**：① 封面横幅里写着「187 页 / 19 章」，而本页第一行是 196 页——统计轴从没抓到它，因为**它读的是 Markdown，横幅是图片**；已改成 196 并给 `check_readme_stats.py` 加了 banner 腿（只从 `<text>` 节点取数，坐标 `x="196"` 不算声明），反例控制就是重演这次失真（196→187 必须报 2 条）；② 第 61 轮的「上线了吗」门 `check_live_sync.py` 只读 changelog 的 `.md` 端点，而 `.md` 比渲染页先同步——实测 `.md` 已是第 64 次、**同一页 HTML 还停在第 62 次**（9,733,032 字节连查 8 次不变，落后一小时以上）。现在两腿都读、**判决取较差的那条**
- **第 65 轮按这条轴逐张重排**：操作者拍板「分批逐张重排」，批 1 是读数最险的 5 张（首页封面 + `03-context-budget` / `04-react-loop` / `05-mcp-architecture` / `07-plan-vs-react`）。等比缩放中性，所以只有两个自由度：**窄画布**（封面 1920→1280，缩率 0.4→0.6）与**抬字号 + 长画布**（正文图最小字号抬到 15px，0.8 缩率下正好 12.00px；装不下就往高度长，缩放只看宽度所以高度免费）。全站读数 **32 张 / 956 个 → 27 张 / 735 个**（批 1 落库时是 734，同轮批 1c 把一个从没生效的 `<br/>` 换成真的第二行 `<text>`，分母 +1、命中 +1），五张图 223 个越线标签清零，`--column 1152` 的 what-if 23 张 / 378 个 → 18 张 / 204 个；**内容一字未删**（只有 3 处措辞被压短，逐条记在更新日志第 65 次）。轴照旧 `exit 1`，因为还剩 27 张
- **读者拿到的不是仓库里那份 SVG**：GitBook 过资产时跑 sanitizer——重排属性、删注释，并且**剥掉 `paint-order`**、**剥掉 `<animate>` 上取值是 `fill` 的 `attributeName`**。于是 `fill + stroke + paint-order="stroke"` 这种「描边当光晕」的标签在线上变成 3.5px 淡色描边压在 15px 字形上，读者看到一片浅灰残影，而离线字号轴读数完全正常（字号确实是 15px）。第 65 轮线上抽查真渲染才抓到，共 5 处（`04` 3 个、`07` 1 个、`19-lab` CSS 1 个），改成**两层 `<text>`**（底层 `fill="none"` 只画描边，上层只写 `fill`），全是普通表现属性。第二条是**把线上腿跑完 32 张**才现形的：`17-sim2real-domain-randomization` 四个「域随机化」格子写 `<animate attributeName="fill" values="A;B;A">`，到达读者时 `attributeName` 没了 → 没有目标属性 = 动画永不运行，这张图的主题（每格按自己周期换色）在线上死了；同一张图指向 `x`/`opacity` 的 animate 与全站 53 处 `opacity`、11 处 `width` 目标全部存活，所以被剥的不是这个属性而是 `fill` 这个取值（全站恰好 4 处）。同一趟还报出 `<text>…<br/>…</text>`：`<br>` 不是 SVG 元素，**它在本地也从没换出行**（真渲染里那一行字直接压进右侧方框），平台删节点只是把它藏得更彻底——处方不是「绕过 sanitizer」，是改成两个 `<text>`。动画的替代写法用平台确实带的 `opacity` 目标：格子上盖一块同几何、`fill=目标色`、`opacity` 从 0 到 1 的覆盖矩形，且排在前景块之前。断言用**冻一帧再采样**（覆盖矩形设 `opacity="1"`、时变的扫光设 0、删掉所有 `<animate>`）：四格覆盖色与四格前景块色 **8/8 精确命中**——直接截动图会被时变元素污染。判据落库 `tools/checks/check_svg_sanitizer.py`：离线腿（不联网，任何 authored 资产依赖 `KNOWN_STRIPPED`/`STRIPPED_ANIMATE_TARGETS`/`LINEBREAK_TAGS` 里的写法即红）+ 线上腿（逐张取页面上的 `~gitbook/image` 代理地址——`.gitbook/assets/*` 直接 404，拉回服务端副本比对元素与属性多重集，并断言 `viewBox` 相同、副本仍可解析）。控制：selftest 种的属性版与 CSS 版 `paint-order`、`attributeName="fill"` 的 animate、`<br/>` 四种坏写法都必须被抓，两层 text / opacity 覆盖矩形 / 两行 text 三种**修法**必须 0 命中（否则判据会把未来的自己一起锁死）；比对数 <25 直接失败，「干净」不许来自空样本。读数 依赖被剥写法 **1 → 0**、`served copies compared=32 of 32`
- **标签的墨迹真的落在框里、没有压在连线上**：第 66 轮新增轴 `tools/checks/check_svg_fit.py`。第 64/65 轮只量字号，而**缩小之后仍然看得见的字可以是重叠的**——一个标签可以印在别人的方框上，一段说明可以正好躺在回线上，这些「谁都不会响」。这一轮的判据不估字宽：把图内联进本机页面，让无头 Chromium 真排版，对每个 `<text>`/`<tspan>` 取 `getBBox()`（紧墨迹盒）再乘 `getScreenCTM() × 根 CTM⁻¹` 映回**这张图自己的 viewBox 单位**，于是 `transform`、`text-anchor`、缩放全部自己消掉。四种判据：**BURST**（标签边缘越过自己所属容器 >2px）、**COLLIDE**（不同字符串墨迹盒 x 向重叠 >2px 且 y 向 ≥ 短者高 45%）、**OFFCANVAS**、**STRIKE**（`fill:none` 的描边线按 ~2px 采样，任一采样点落进标签墨迹盒）。这条轴是先杀了一个前辈才立起来的：同一棵树，用「按字符类估宽度、忽略 transform」的探测脚本量出 **563 处**碰撞，而真渲染一张都没有——量不准的东西没资格判定美丑。首趟读数 **8 处**（全是 STRIKE），分布在 4 张图：`17-vla-loop` 3 处（反馈回线横穿三个方框、动作块图例印在「伺服 / WBC」卡片上）、`16-sandbox-layers` 2 处、`06-rag-pipeline` 1 处（Top-K 说明压住虚线返回线）、`05-mcp-architecture` 2 处。最后两条是**判据的假阳性**而不是图的缺陷：GitBook 房风用法是「药丸底 <rect> 先画、连线后画、标签最后画」，被不透明底板盖住的采样点不该算刺字——加上 paint-order 底板豁免后 8→6，剩下 6 处逐张改几何（回线绕空泳道、图例上移、标题下移一行），**没有一处靠删文字解决**。全站读数 **8 → 0**（`figures with a fatal problem=0 of 32  total=0  clearance notes=3`，`exit 0`）。绿色同样由控制换回来：四种脏写法各种一棵必须各自被抓，另有一棵 **PLANT_CLEAN** 把本轮引入的全部豁免（两行分框、绕行走廊、两层字光晕、`<!-- fit:strike-ok ✕ -->` 意图豁免、药丸底板）全用一遍，**必须读 0**——不然豁免只是遮罩。那条意图豁免写在 SVG 注释里，而**第 65 轮已经量过 GitBook 会剥掉注释**：所以它只在作者侧生效，读者拿到的图里什么都没有，这正是它该待的位置（判据读的是仓库里那份 authored 资产）。同期回归：字号轴 27 张 / 735 个 → **25 张 / 686 个**（改几何顺手把两处小字挪进空位），结构轴 198 页 0 问题，5 张改动图 768px 真渲染逐张目检。已知盲区（诚实记账，未修）：`STRIKE` 看不见「字压在别人的卡上」这种非描边交叉，列宽仍钉 768，等宽版布局开关落地后要用 `--column 1152` 复跑
- **字号轴批 2＋批 3（第 67 轮）**：操作者批的「分批逐张重排」继续往下走，21 张手绘 SVG 重排后全站越线读数 **25 张 / 686 个 → 3 张 / 214 个**（分母 1089→1096：7 处长标签拆成两行，标签变多而越线变少，**一个字都没删**）。三个自由度各自到位——抬字号＋长画布（920/960 画布最小 15px、980 画布 16px）、拆行（`09-framework-map-ui` 六张卡全部两行）、换宽（`09` 决策胶囊 236→256、卡片 300×60→290×80、画布 560→624；`16-continuous-batching` 整条泳道右移 40px）。本轮另外修掉三条图以外的缺陷：**内在尺寸轴**（`<img>` 里的 SVG 不写 `width`/`height` 时 Chromium 报 naturalWidth 300，轮初 10/32 张缺，补齐后加两腿断言：声明必须等于 viewBox + 删掉声明的幽灵图必须读 `None`）、**字号轴的 `<style>` 盲区**（`19-lab-react-loop-animated.svg` 用类字号被 13px 兜底误报 15 个越线标签，补上真实层叠「内联 style > 类规则 > 表现属性 > 继承」并种一张 9/15/17/20px 四写法的幽灵图，selftest 两棵→三棵；这张图最终 0 改动——先验尺子再下判决）、**动画条压字**（右移后「持续满载」BURST 8px，用画布加高解决而不是挪字）。fit 轴全站 32 张 fatal=0，结构轴 198 页 0 问题，统计三腿对平。**未做**：`05-mcp-inspector-ui` / `11-observability-ui` / `10-eval-console-ui` 三张高密度 UI 示意图剩 214 个越线标签（不是抬字号能救的，行高列宽面板要按 1.25× 一起长＝重画三张 UI，单独一轮）；21 张里只有 8 张过了肉眼，其余 13 张只过了判据；`16-continuous-batching` 两处白字在动画相位里会先于底色出现，**动画时序可见性**这条轴还不存在
- **2026-09 前沿已对齐**：GPT-6 Astra、Agents API、Claude Fable 5.1、System One 决策模型（Jev）、Terminal-Bench 4.0

查资料用 [资源总表](00-index/resources-index.md) 与 [标签索引](00-index/tags.md)，术语卡住查 [术语表](15-glossary/README.md)。

Use the [resource index](00-index/resources-index.md) and [tag index](00-index/tags.md) to look things up; the [glossary](15-glossary/README.md) covers terminology.

## 许可证 · License

MIT
