# 更新日志

本页记录手册的结构调整与重要内容更新。

## 2026-09-10（第 4 次）内容质量修订

针对「模板化、emoji 泛滥、原理不深、引用单一」四类问题做系统性修订：

- 重写 [风格指南](../14-templates/style-guide.md)：改为**按体裁分型**（原理型/概念型/实战型/资源卡片），去掉「每篇必须一句话+图+类比+误区」的硬性模板；新增 emoji 硬预算、公式与出处要求、案例配给（单一项目 ≤10 篇）、发布字数门槛
- 全局清理 emoji：剥离 137 篇的标题 emoji 与星级难度标记（emoji 从 1370 降至 319，其余为 ❌✅⚠️💡 语义标记）
- 事实核查（经本地代理联网）：逐条验证 157 个外链；修复 5 处断链（含 `humanlayer/12-factor-agents`、`Awesome-RAG`、MCP Discussions 地址）
- **Pi 仓库已迁移**：`badlogic/pi-mono` → `earendil-works/pi`，全库 26 处更新；移除已无法核实的「vLLM pods」等表述
- **DeepSeek Harness 引用经核实为真实**（`packages/core/agent-loop`、`packages/plan`、`packages/preset/agent-presets` 等路径均存在），删除 5 处与主题弱相关的凑数引用
- 12 篇核心原理页补齐公式与论文引用：Transformer 注意力、Embedding 相似度、RLHF/DPO、预训练与 LoRA、量化与推理、Token 与上下文预算、RAG 指标、ToT 搜索、评估指标、基准协议、结构化输出（约束解码）、幻觉检测
- 新增 7 张自绘 SVG 插图（学习路线、Agent 循环、注意力计算、Function Calling、RAG 管线、多智能体、评估四层），接入对应章节
- 新增 [开源项目索引](../13-resources/projects/README.md)：329 个项目、11 个分类，star/许可/语言为 2026-09 实测值，由 `scripts/gen-projects.py` 生成可复现

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
