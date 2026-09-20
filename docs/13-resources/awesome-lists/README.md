---
tags: [resource]
type: index
status: published
updated: 2026-09-20
---

# Awesome 列表

> 持续维护的资源合集，适合「扫货式」发现新项目。注意 Awesome 列表只负责「全」，不负责「精」——取舍仍靠自己判断。

下面每条都在 2026-09-21 用 GitHub API 逐个查过：链接有效，并记下 star 与最近推送时间。这两个数字比列表里的自我描述更有用——**半年没推的列表，条目就当历史资料读**。

## 推荐列表

| 列表 | 内容 | 点评（含维护状态） | 链接 |
|---|---|---|---|
| awesome-ai-agents | Agent 项目大合集（E2B 维护） | 3.0 万星，事实上的第一入口。缺点是只收「项目」不收方法论，看东西按类别扫，别当选型依据 | <https://github.com/e2b-dev/awesome-ai-agents> |
| awesome-agents | 框架与工具精选（kyrolabs 维护） | 2.8 千星但推送很新，条目比 E2B 那份克制；和上一份重合度高，二选一即可 | <https://github.com/kyrolabs/awesome-agents> |
| awesome-agentic-ai-zh | 三语（繁中/英/简中）Agent 学习路线 | 7.1 千星、当天还在动。中文侧少见的不但收集、还给出阅读顺序的列表，值得置顶 | <https://github.com/WenyuChiou/awesome-agentic-ai-zh> |
| awesome-agent-skills | Agent Skills 合集（VoltAgent） | 3.5 万星，收录 1000+ skill。这类「skills 目录」最近冒出一堆（heilcheng 那份 6.2 千星同题材），质量参差，认准一份跟到底 | <https://github.com/VoltAgent/awesome-agent-skills> |
| awesome-claude-code | Claude Code 生态：命令、子代理、插件 | 更新勤，实操密度高；但里面一半是 prompt 收藏，真正能直接复用的没几条 | <https://github.com/hesreallyhim/awesome-claude-code> |
| awesome-mcp-servers | MCP Server 合集（punkpeye） | 9.5 万星，MCP 生态的第一索引。代价是几乎不筛质量，装之前自己去看该 server 的仓库活跃度 | <https://github.com/punkpeye/awesome-mcp-servers> |
| awesome-mcp-servers（wong2） | MCP Server 精选（wong2） | 4.3 千星，比 punkpeye 短很多但筛过一轮。两份加 appcypher 那份一起看是浪费时间——选一份，剩下的用官方仓库兜底 | <https://github.com/wong2/awesome-mcp-servers> |
| Awesome-RAG | RAG 应用与工程条目 | 1.4 千星、仍在更新。偏「项目清单」，工程细节不如直接读框架文档 | <https://github.com/Danielskry/Awesome-RAG> |
| Awesome-GraphRAG | GraphRAG 论文/基准/实现 | 2.7 千星。要做实体关系检索再来看，普通分块 RAG 用不上；这是少数没被复制烂的细分列表 | <https://github.com/DEEP-PolyU/Awesome-GraphRAG> |
| Awesome-LLM | 开源模型与部署工具 | 老牌长清单，训练/推理工具链齐全；模型本身更新快于列表，选型请以官方仓库 README 为准 | <https://github.com/Hannibal046/Awesome-LLM> |
| awesome-llm-apps | 可跑 LLM/Agent 应用示例（Shubhamsaboo） | star 很高，胜在每条目带可运行代码；代价是同一思路有五六份重复实现，别逐个啃 | <https://github.com/Shubhamsaboo/awesome-llm-apps> |
| awesome-ai-security | LLM/AI 安全资源 | 1.5 千星、本周还在动，攻击面与防御工具都在。同类还有 corca-ai/awesome-llm-security（1.7 千星），那份更全但已停更 | <https://github.com/ottosulin/awesome-ai-security> |
| Awesome-LLMs-Evaluation-Papers | 评估论文分类清单 | 论文侧可用，但停在 2024：Agent 评估这三年变化最大，只当背景阅读，新基准走 [基准测试](../benchmarks/README.md) | <https://github.com/tjunlp-lab/Awesome-LLMs-Evaluation-Papers> |

## 使用建议

- 每月扫一次感兴趣的列表，新项目先看「最近提交时间」与「issue 响应速度」再决定是否投入
- 协议与官方清单优先于 awesome 列表：MCP 官方 server 仓库 <https://github.com/modelcontextprotocol/servers> 比任何合集都准
- 同类列表的重合度普遍在七成以上，「Agent 合集」这一类尤其泛滥（Jenqyang、slavakurilyak、jim-schwoebel 三份同题材，最新的一份胜出即可）
- 值得深读的及时建卡片页（用 [资源模板](../../14-templates/resource-template.md)）并登记到 [资源总表](../../00-index/resources-index.md)
