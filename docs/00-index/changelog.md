# 更新日志

本页记录手册的结构调整与重要内容更新。

## 2026-09-10（第 3 次）🎉 全书完成

- ✅ 全部 16 章、142 页撰写完成（此前为骨架 + 占位页）
- 📦 案例覆盖三大开源 harness：**Claude Code**（社区逆向：三层 prompt 组装、子 Agent 隔离、三档压缩、权限管道）、**Pi Agent / pi-mono**（极简 harness：4 原子工具、~300 行 agentLoop、JSONL 会话）、**DeepSeek Harness**（一切皆插件：Cordis 框架、turn/step 状态机、append-only 事件流、landlock 沙箱）
- 🏗️ 新增 12 章编程 Agent 页的「三大 harness 横向深拆」对比表
- 🔗 全书双向链接（知识点 ⇄ 资源）铺设完成；术语表 60+ 条收录
- 📊 评估章收录五大基准精读（SWE-bench/GAIA/WebArena/AgentBench/ToolBench）

## 2026-09-10（第 2 次）

- ✍️ 建立统一写作规范：新增 [风格指南](../14-templates/style-guide.md)（emoji 规范、图文规范、先问题后定义、写作检查清单）
- 🧩 知识点模板升级为「一句话结论 + 生活类比 + 图 + 例子 + 误区 + 资源」结构，增加 frontmatter（tags/type/status/updated）
- 🔗 资源模板增加 frontmatter 与「双向链接」规范（知识点 ⇄ 资源互链）
- 🤖 写出第一篇完整示例页：[什么是 AI Agent](../02-agent-basics/what-is-agent.md)
- 🖼️ 新增 `docs/assets/` 图片目录（diagrams / screenshots / covers / icons）
- 🧭 SUMMARY 章节标题加入模块 emoji；全部占位页升级为新格式（frontmatter + 模块 emoji + 模板指引）

## 2026-09-10

- 🚀 初始化全新手册结构：16 个章节、135+ 页面骨架
- 建立导航与索引（总导航、学习路线、标签索引、资源总表、更新日志）
- 建立 13 资源库分类：论文、课程、开源项目、工具、数据集、基准测试、博客、社区、Awesome 列表
- 新增知识点模板与资源模板，统一写作格式
- 迁移 GitBook 配置，内容根目录设为 `docs/`
