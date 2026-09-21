# 更新日志

本页记录手册的结构调整与重要内容更新。

## 2026-09-22（第 11 次）真实产品截图上线 + 无图页补齐 + 薄页增厚

全书第一次出现**真实软件界面**：此前 191 张配图全是自绘 SVG 与 Mermaid，读者看不到「这些工具真长什么样」。这一版补上截图，同时清掉三类体检出的短板。

- **8 张真实产品 UI 截图**（`docs/.gitbook/assets/screenshots/`，目录内 `MANIFEST.md` 逐张记录来源 URL 与访问日期）：Langfuse Trace 视图（11 章）、MCP Inspector 协议监控（05 章）、OpenHands Automate（12 章 + 项目页）、Dify 工作流画布（09 章）、Open WebUI 对话与工作区（12 章）、Arize Phoenix Trace Details（11 章）、AutoGen Studio Team Builder（09 章）、LangSmith 实验对比表（10 章）。每张逐项目检：真实产品界面、无 cookie 横幅与遮罩、文字可辨；7 个来源 URL 复核 HTTP 200。**每张图配一段「读这张图的顺序」**，指出面板与本页论点的对应关系，而不是贴完就算。
- **补齐违反「每页有图」自订标准的页面**：[Lab 2](../19-labs/lab2-rag.md) BM25 检索链路、[Lab 3](../19-labs/lab3-mcp.md) MCP 握手时序、[Lab 5](../19-labs/lab5-eval-trace.md) 评测—trace 数据流、[Lab 6](../19-labs/lab6-guardrails.md) 两道护栏决策流，各配一张章色 Mermaid；新图全部经 Edge 真实渲染逐张目检（首版有裁切/留白问题，改扁平 LR 后通过；Lab 2 那张单排 LR 在正文宽度下字号太小，最终改成「离线建库 / 在线问答」双泳道，并把「回答不合格就回查切块」这条虚线显式画出来）。
- **13 章 5 个薄项目页增厚**：[LangGraph](../13-resources/projects/langgraph.md)、[AutoGen](../13-resources/projects/autogen.md)、[CrewAI](../13-resources/projects/crewai.md)、[LangChain](../13-resources/projects/langchain.md)、[OpenHands](../13-resources/projects/openhands.md) 从 575–820 字扩到与其它资源页同密度（架构要点 + 适用场景 + 手写点评 + 真实链接），并把 7 个项目页全部配图；LangChain 页补 3 行 Runnable 管道代码判断协议价值。
- **核心页补最小可跑代码**：[Transformer 与注意力](../03-llm/transformer-attention.md) 新增 12 行 NumPy 单头因果注意力，与正文公式逐项对应，**贴出本机真实运行的权重矩阵输出**，并解释三件事：causal mask 就是「逐字解码」的代码形态、平方级开销长在权重矩阵上（所以 KV 缓存救显存救不了注意力）、softmax 饱和为什么让注意力可视化容易骗人。
- **未能做到的部分如实记录**：LangGraph Studio 与 browser-use 的官方文档页经渲染后 DOM 里只有品牌图，无公开产品截图；CrewAI 文档站的 `crews.png` / `flows.png` 目检是概念示意图（与自绘 Mermaid 等价），故不引入；Langfuse Cloud 官方 demo 工作区跳登录墙，改用其文档内嵌截图。原因写进 MANIFEST，避免后人重复踩。

统计更新：全书配图 **210 张**（168 Mermaid + 34 自绘 SVG + 8 真实截图），提示卡 204 个，187 页 / 19 章不变；168 个 Mermaid 块经真解析器逐块校验 0 失败，无断链回归。

## 2026-09-21（第 10 次）动手实验章 + 门面升级 + 术语速查 + 实战手记

把「只读不练」和「门面朴素」两块最后的短板补齐，四件事一起落地：

- **新增第 19 章「动手实验」**：6 个纯标准库、零 API Key、离线可跑的实验——最小 ReAct 闭环 → 手写迷你 BM25 RAG → 手写迷你 MCP 服务 → 三角色协作 → 评测与 trace → 护栏与接真模型。每个实验含完整代码、**本机 Python 3.13 真实运行输出**、盯三个细节、动手改与排错备忘；MockLLM 与真实模型接口同构，看懂后换真 API 主循环一行不改。已接入 [SUMMARY](../SUMMARY.md) 与 [学习路线](../00-index/learning-path.md)（新增「动手派」路线）
- **门面升级**：自绘仓库封面 `cover-handbook.svg`（1600×900，六段学习旅程）+ GitBook 首页横幅 `banner-home.svg`（1920×480，LLM 推理循环）；[仓库首屏](../../README.md) 与 [在线首页](../README.md) 重排，新增「边学边做」入口
- **4 张高保真工具界面示意**（与既有 SVG 同风格，逐张真实渲染目检）：MCP Inspector 调试台（05）、框架选型五问决策树（09）、Agent 评测发布门禁看板（10）、可观测性三跳定位控制台（11）
- **每章末尾中英术语速查**：核心章节各配 8–12 条术语 + 白话解释；**12 个核心页新增「实战手记」**：运维现场的经验值（轮次收敛区间、trace 采样账单、prompt 约束条数上限、检索失败要到日志认领等），数字全走经验口径、不虚构事故与引用

全书配图达 **191 张**（157 Mermaid + 34 自绘 SVG），提示卡 206 个；全部 Mermaid 经真解析器逐块校验 0 失败，无断链回归。

## 2026-09-20（第 9 次）旗舰概念插图第二批：8 张自绘 SVG 上线

补上「只有框图、没有图册」的最后一块短板，为核心概念页新增 8 张与既有资产同风格的自绘 SVG（960 宽、淡网格第二层背景、章色主色、语义化 SMIL 动效，全部经真实渲染逐张目检）：

| 插图 | 接入页面 | 讲什么 |
|---|---|---|
| 上下文预算 | [Token 与上下文](../03-llm/token-embedding-context.md) | 200k 窗口五段分配 + 压缩前后对照，缓存分界一眼可见 |
| ReAct 闭环 | [ReAct](../04-prompt-reasoning/react.md) | 思考—行动—观察三环，左侧纯 CoT 断链对照、右侧真实轨迹示例 |
| MCP 架构 | [MCP](../05-tool-protocol/mcp.md) | M×N 乱麻 vs M+N 统一协议，Host/Client/Server 与三种原语 |
| 记忆三层 | [记忆类型](../06-memory-rag/memory-types.md) | 工作/情景/语义的沉淀与回填回路 + 遗忘曲线 |
| 规划对比 | [Plan-and-Execute](../07-planning/plan-and-execute.md) | 先谋后动 vs 边想边做双泳道，含重规划回跳与两本账 |
| 协作拓扑 | [多智能体协作](../08-multi-agent/multi-agent-collaboration.md) | Supervisor/Swarm/Group Chat/Pipeline 四宫格与选型底线 |
| Trace 瀑布 | [日志、追踪与监控](../11-engineering/logging-tracing-monitoring.md) | 一次运行的 span 树时间轴，延迟/token/成本/重试四项必录 |
| 编程 Agent 循环 | [编程 Agent](../12-applications/coding-agent.md) | 沙箱内改码—测试—修复闭环，合并权留给人 |

全书配图达 **182 张**（154 Mermaid + 28 自绘 SVG）。

## 2026-09-20（第 8 次）全书 Mermaid 章色配色：告别默认灰白

针对线上抽查发现的「全书图只有黑白框图、图册感弱」做视觉体系升级：

- **154 个 Mermaid 块全部注入 `%%{init}%%` 章色主题**：18 章各配一个主色（02 紫、05 青、09 玫红、10 红……），节点底色统一为主色掺白 90%、连线掺白 45%，一眼可辨所在章节；GitHub 与 GitBook 原生支持该指令
- **门面页补图**：[什么是 AI Agent](../02-agent-basics/what-is-agent.md) 新增「两分钟判断是不是 Agent」决策流程图，全书正文页（除模板页）实现图零空白
- **规范固化**：[风格指南](../14-templates/style-guide.md) 新增「Mermaid 章色配色（硬性要求）」一节——章色表、混色公式、可直接复制的指令示例；写作检查清单同步加一条
- 全部 154 块经真解析器（mermaid@11）逐块校验 0 失败

## 2026-09-20（第 7 次）对标头部开源手册：图文、排版与自测体系升级

以 GitHub 同类头部项目（bojieli/ai-agent-book、microsoft/ai-agents-for-beginners、huggingface/agents-course、datawhalechina/self-llm 等）为参照，补三块短板：

- **图示密度翻倍**：新增约 60 张 Mermaid 内联图，全书达 **154 张 Mermaid + 20 张自绘 SVG**；09 框架、10 评安、11 工程、17 具身、16 基础设施等此前无图的章节全部配齐机制图；资源深读卡（ReAct/Reflexion/Toolformer/SWE-bench/GAIA/WebArena/Langfuse 等）逐张配「一图看懂」
- **排版升级为 GitBook 原生**：183 个「一句话 / 提示 / 注意」引用块全部转为分色 `{% hint %}` 提示卡；模板与风格指南同步改用 hint 写法，贡献指南新增「图文与排版规范」与 good-first-page 清单
- **每章「读完能做到」清单 + 章末自测**：18 章全量落地，清单条目均为可检验行为，自测题按回忆/应用/判断三档并标注答案出处
- **质量闸门**：全部 Mermaid 经真解析器（mermaid@11）逐块校验 0 失败；修复断链 5 处；被修改页面 `updated` 统一为 2026-09-20
- 资源库增补：开源项目索引头部 95 个项目改为手写一句话点评（去掉截断的机器味描述）；博客（16）/ 社区（11）/ Awesome 列表（13）/ 数据集四个索引扩充完成，收录链接逐一在线核验，无法核实的一律剔除

## 2026-09-12（第 6 次）对齐 2026-09 前沿：新增第 18 章

针对审核发现的「模型面/产品面/评估代际滞后、图片覆盖不足」做系统补强：

- **新增 18 2026 前沿**（8 页）：
  - [2026 前沿模型地图](../18-frontier-2026/frontier-models-2026.md)：GPT-6 Astra、Claude Fable 5.1 / Mythos 5.1、Opus 5，含 effort × 防护 × cache 读法
  - [OpenAI Agents API](../18-frontier-2026/openai-agents-api.md)：托管 Codex harness、压缩、tool search、子 Agent
  - [Claude Agent SDK](../18-frontier-2026/claude-agent-sdk.md)：与 CLI / Client SDK / Managed Agents 分界
  - [模型原生 vs 自建 Harness](../18-frontier-2026/model-native-vs-harness.md)：2026 架构分叉与选型流程
  - [Computer Use 2026](../18-frontier-2026/computer-use-2026.md)
  - [评估 2026](../18-frontier-2026/eval-2026.md)：Terminal-Bench 4.0、OSWorld 2.0、τ²、Agents' Last Exam
  - [2026 协议栈](../18-frontier-2026/protocol-stack-2026.md)：MCP + A2A + AG-UI + Skills/agents.md
- **第 10 章**新增 [2026 安全现实](../10-evaluation-safety/safety-incidents-2026.md)；[基准测试总览](../10-evaluation-safety/benchmarks.md) 刷新到 2026 代际
- **第 12 章**新增 [通用 Agent 产品](../12-applications/general-agent-products.md)、[实时语音 Agent](../12-applications/voice-agent.md)
- **第 01 章** [发展简史](../01-ai-basics/ai-history.md) 时间线补 2026-07～09 事件
- 新增 5 张自绘 SVG：模型×harness 矩阵、Agents API 架构、协议栈、评估版图、Computer Use 闸门
- 导航同步：`SUMMARY.md`、总导航、首页必读与主题入口

## 2026-09-10（第 5 次）内容质量修订与全书扩写

针对「模板化、emoji 泛滥、原理不深、引用单一」四类问题做系统性修订，并对全书 70 篇偏薄页面做深度扩写：

- 重写 [风格指南](../14-templates/style-guide.md)：按**体裁分型**（原理型/概念型/实战型/资源卡片），去掉单一模板；新增 emoji 硬预算、公式与出处要求、案例配给、发布字数门槛；并入 16/17 章的 SVG（SMIL）动图规范
- 全局清理 emoji：剥离标题 emoji 与星级难度标记；第 16/17 章 24 个文件一并去 emoji（627 → 163）
- 事实核查（经本地代理联网）：逐条验证外链；修复断链（`humanlayer/12-factor-agents`、`Awesome-RAG`、MCP Discussions 地址等）
- **Pi 仓库已迁移**：`badlogic/pi-mono` → `earendil-works/pi`，全库更新；移除已无法核实的「vLLM pods」等表述
- **DeepSeek Harness 引用经核实为真实**（包路径均存在），删除与主题弱相关的凑数引用
- 约 70 篇原理/概念/实战页补齐机制、公式与论文引用：注意力、Embedding、RLHF/DPO、预训练与 LoRA、量化推理、Token 与上下文预算、RAG 指标、CoT/ToT/GoT/Reflexion/Self-Refine、知识图谱、上下文工程、记忆压缩、幻觉、提示注入/越狱，规划 5 篇、多智能体 7 篇、框架 8 篇、工程化 10 篇、应用 8 篇，以及可解释性、对齐、行业 Agent 等
- **全书 170 页全部达到体裁字数门槛**（原理型 1200 / 实战型 900 / 概念型 600 汉字），含公式页面 93 篇
- 2 个不足 150 字的资源卡片补齐后恢复 `published`
- 新增 7 张自绘 SVG 插图并接入对应章节
- 新增 [开源项目索引](../13-resources/projects/README.md)：323 个项目、11 个分类，star/许可为 2026-09 实测值；后续清理了自动分类混入的跑题条目
- 说明：生成与校验用的辅助脚本已从仓库移除，以保持内容仓库精简

## 2026-09-10（第 4 次）新增 16 AI 基础设施与 17 具身智能

- 新增 **16 AI 基础设施**（11 页）：推理服务化（连续批处理 / PagedAttention / TTFT-TPOT）、前缀缓存与上下文工程、GPU 调度与多租户、训练与微调基础设施、沙箱与执行环境、模型网关与路由、持久化执行与运行时、数据与检索基础设施、可观测性与评估平台、推理经济学与部署形态
- 新增 **17 具身智能**（13 页）：具身闭环定义、机器人基础模型谱系（RT-2 → OpenVLA → π0 → GR00T/Helix/GO-1）、VLA 架构与动作头、动作表示与分层控制、数据引擎、仿真与 Sim-to-Real、世界模型与视频预训练、灵巧操作、人形与腿足运动、评估与基准、硬件实时与安全、Agent ⇄ 机器人桥接（含代码）
- 新增 6 张**可动画的 SVG 图示**（SMIL，GitHub/GitBook 中可直接播放）：连续批处理、前缀缓存、沙箱分层、VLA 循环、动作分块、Sim-to-Real 域随机化
- 双向链接补齐：16/17 ⇄ 03、05、06、10、11、12、13 各相关页；新增 `infrastructure`、`embodied-ai`、`data`、`cost` 四个标签
- 导航同步：`SUMMARY.md`、`docs/README.md`、学习路线（新增「平台/Infra」与「具身方向」两条路线）、术语表新增两组共 29 条

## 2026-09-10（第 3 次） 全书完成

- ✅ 全部 16 章、142 页撰写完成（此前为骨架 + 占位页）
- 案例覆盖三大开源 harness：**Claude Code**（社区逆向：三层 prompt 组装、子 Agent 隔离、三档压缩、权限管道）、**Pi Agent（原 pi-mono）**（极简 harness：4 原子工具、~300 行 agentLoop、JSONL 会话）、**DeepSeek Harness**（一切皆插件：Cordis 框架、turn/step 状态机、append-only 事件流、landlock 沙箱）
- 新增 12 章编程 Agent 页的「三大 harness 横向深拆」对比表
- 全书双向链接（知识点 ⇄ 资源）铺设完成；术语表 60+ 条收录
- 评估章收录五大基准精读（SWE-bench/GAIA/WebArena/AgentBench/ToolBench）

## 2026-09-10（第 2 次）

- 建立统一写作规范：新增 [风格指南](../14-templates/style-guide.md)（emoji 规范、图文规范、先问题后定义、写作检查清单）
- 知识点模板升级为「一句话结论 + 生活类比 + 图 + 例子 + 误区 + 资源」结构，增加 frontmatter（tags/type/status/updated）
- 资源模板增加 frontmatter 与「双向链接」规范（知识点 ⇄ 资源互链）
- 写出第一篇完整示例页：[什么是 AI Agent](../02-agent-basics/what-is-agent.md)
- 新增 `docs/assets/` 图片目录（diagrams / screenshots / covers / icons）
- SUMMARY 章节标题加入模块 emoji；全部占位页升级为新格式（frontmatter + 模块 emoji + 模板指引）

## 2026-09-10

- 初始化全新手册结构：16 个章节、135+ 页面骨架
- 建立导航与索引（总导航、学习路线、标签索引、资源总表、更新日志）
- 建立 13 资源库分类：论文、课程、开源项目、工具、数据集、基准测试、博客、社区、Awesome 列表
- 新增知识点模板与资源模板，统一写作格式
- 迁移 GitBook 配置，内容根目录设为 `docs/`
