---
tags: [resource]
type: index
status: published
updated: 2026-09-22
---

# 博客

{% hint style="info" %}
**一句话**：一手工程经验的第一来源——这个领域变化太快，博客往往比论文和教材更贴近当下能跑通的做法。
{% endhint %}

## 先读这四篇文章

比订阅整个博客更划算的入口，四篇都还活着（2026-09 逐条验证）：

- [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) —— Anthropic。工作流 vs Agent 的工程共识，全书引用最多的一篇
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system) —— Anthropic。多 Agent 成本/收益/失败模式的一手数据
- [Claude Code: Best practices](https://www.anthropic.com/engineering/claude-code-best-practices) —— Anthropic（现跳转至 code.claude.com 文档）。Coding Agent 的使用方法论
- [DeepSeek Harness 发布解读](https://www.sohu.com/a/1062640652_122014422) —— InfoQ。一切皆插件架构的中文深度报道

## 博客清单

| 博客 | 主要方向 | 为什么值得读 | 链接 |
|---|---|---|---|
| Anthropic Engineering | Agent 工程实践与成本实测 | 官方号里少见会写「哪些方案我们放弃了」的，数字是自己系统跑出来的 | <https://www.anthropic.com/engineering> |
| Simon Willison's Weblog | LLM 安全、工具实测 | 提示注入的第一追踪源，几乎每条都有可复现 demo，不是转述论文 | <https://simonwillison.net/> |
| Lilian Weng | Agent 与后训练机制综述 | 「LLM Powered Autonomous Agents」至今仍是入门碑文，综述功底少人替代 | <https://lilianweng.github.io/> |
| Chip Huyen | AI 系统工程化 | 判断「这个 Demo 离上线还差几步」时最好用，边界条件讲得清楚 | <https://huyenchip.com/blog/> |
| Eugene Yan | 评估设计与生产落地 | 讲指标怎么定讲得比论文老实，评估方案可以直接抄 | <https://eugeneyan.com/> |
| Hamel Husain | 评测集与合成数据 | 自建领域评测集那套流程是干货，附真实项目复盘而非概念图 | <https://hamel.dev/> |
| Sebastian Raschka（Ahead of AI） | 训练原理与论文精读 | 把 RL 后训练的机制讲到能照着搭，适合不想啃综述原文的人 | <https://magazine.sebastianraschka.com/> |
| Nathan Lambert（Interconnects） | 后训练格局与开源模型观察 | 判断「哪家训练路线赢了」时最冷静的一个，有立场但给证据 | <https://www.interconnects.ai/> |
| Thinking Machines Blog | 推理侧系统与 rollout 工程 | 更新慢但每篇都是系统级一手内容，harness 设计能直接借鉴 | <https://www.thinkingmachines.ai/blog/> |
| Robert Kirk | RL 后训练复现记录 | 肯写「这个 trick 不 work」的人不多，读他能省几张卡 | <https://robertkirk.github.io/> |
| LangChain Blog | 框架迭代与 Agent 评估 | 一半是版本公告，剩下讲评估与 trace 的几篇有真东西，挑着读 | <https://www.langchain.com/blog> |
| Hugging Face Blog | 开源模型与训练实操 | 带可跑代码的那批文是宝藏，产品宣传稿直接跳过 | <https://huggingface.co/blog> |
| OpenAI News | 官方模型与 API 动向 | 公告为主、工程细节薄；追新接口时扫一眼就够，别指望方法论 | <https://openai.com/news/> |
| Mario Zechner（badlogic） | 编码 Agent 的 harness 设计 | Pi 的构建日志，代码级取舍全公开，读 [模型原生 vs 自建 Harness](../../18-frontier-2026/model-native-vs-harness.md) 时配着看 | <https://mariozechner.at/> |
| 宝玉（baoyu.io） | 论文与技术博客中译 | 中文圈译得最稳的一人，术语统一，省掉一半检索时间 | <https://baoyu.io/> |
| 阮一峰·科技爱好者周刊 | 中文技术周报 | 广度有余深度不足，当信息扫雷用，别当学习材料 | <https://www.ruanyifeng.com/blog/> |

## 阅读方法

- 官方工程博客（Anthropic/OpenAI/DeepSeek）优先于二手解读
- 读到方法论时问自己：「这个结论在我的场景成立吗？」——多数博客经验有场景边界
- 公告型博客（OpenAI/LangChain）一周扫一次即可，逐日追只会更焦虑
- 个人博客的价值在「失败记录」，只写成果的不必细读
- 把好文章登记到 [资源总表](../../00-index/resources-index.md)
