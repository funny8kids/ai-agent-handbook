# ai-agent-handbook

An open-source AI Agent handbook and curated resource collection covering LLM, RAG, MCP, multi-agent, frameworks, papers, courses, tools, and practical cases.

一本系统化的开源 AI Agent 手册与精选资源库，内容持续建设中。

## 在线阅读

本书通过 GitBook 发布在线版本（站点：VioletNotes Docs）。

## 仓库结构

```text
ai-agent-handbook/
├─ README.md            # GitHub 首页（本文件）
├─ LICENSE              # MIT 许可证
├─ .gitbook.yaml        # GitBook 配置（内容根目录指向 docs/）
├─ gitbook-docs.yaml    # GitBook Docs 站点同步配置
└─ docs/                # GitBook 内容根目录
   ├─ README.md         # 手册首页
   ├─ SUMMARY.md        # 手册目录（GitBook 侧边栏）
   ├─ 00-index/         # 导航与索引（学习路线、标签、资源总表、更新日志）
   ├─ 01-ai-basics/     # AI 基础
   ├─ 02-agent-basics/  # Agent 基础
   ├─ 03-llm/           # LLM 基础
   ├─ 04-prompt-reasoning/  # Prompt 与推理
   ├─ 05-tool-protocol/     # 工具调用与协议（MCP/A2A）
   ├─ 06-memory-rag/        # 记忆与 RAG
   ├─ 07-planning/          # 规划与任务执行
   ├─ 08-multi-agent/       # 多智能体
   ├─ 09-frameworks/        # 框架与生态
   ├─ 10-evaluation-safety/ # 评估、安全与对齐
   ├─ 11-engineering/       # 工程化与可观测性
   ├─ 12-applications/      # 应用案例
   ├─ 13-resources/         # 资源库（论文/课程/项目/工具…）
   ├─ 14-templates/         # 写作模板
   ├─ 15-glossary/          # 术语表
   ├─ 16-ai-infrastructure/ # AI 基础设施（推理/缓存/GPU/沙箱/网关/运行时）
   ├─ 17-embodied-ai/       # 具身智能（VLA/数据/仿真/操作/人形/硬件安全）
   └─ 99-about/             # 贡献指南、许可证
```

## 如何贡献

- 阅读手册中的[贡献指南](docs/99-about/contributing.md)
- 新页面请使用 [知识点模板](docs/14-templates/knowledge-template.md) 或 [资源模板](docs/14-templates/resource-template.md)
- 新增页面务必在 `docs/SUMMARY.md` 中登记

## 许可证

[MIT](LICENSE)
