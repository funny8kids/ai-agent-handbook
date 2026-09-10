# 更新日志

本页记录手册的结构调整与重要内容更新。

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
