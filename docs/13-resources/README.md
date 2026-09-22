---
tags: [resource]
type: index
status: published
updated: 2026-09-22
---

# 13 资源库

{% hint style="info" %}
**一句话**：全书推荐资源的分类收藏地：论文、课程、开源项目、工具、数据集、基准测试、博客、社区、Awesome 列表——每个资源一张卡片页，双向链接回知识点。
{% endhint %}

## 使用说明

- **收录标准**：一手来源（论文/官方仓库/官方文档）优先；有活跃维护或历史里程碑价值
- **卡片格式**：使用 [资源模板](../14-templates/resource-template.md)（frontmatter + 属性表 + 推荐理由 + 上手建议 + 双向链接）
- **总表**：精选资源平铺在 [资源总表](../00-index/resources-index.md)
- 添加新资源后记得在分类 README 汇总表登记

## 分类目录

| 分类 | 内容 | 入口 |
|---|---|---|
| 论文 | ReAct、Toolformer、Reflexion 等奠基工作 | [papers](papers/README.md) |
| 课程 | 系统化免费课程 | [courses](courses/README.md) |
| 开源项目 | harness、框架、编程 Agent；完整项目索引（329 个，11 类） | [projects](projects/README.md) |
| 工具 | MCP Servers、可观测工具 | [tools](tools/README.md) |
| 数据集 | 训练与评估数据 | [datasets](datasets/README.md) |
| 基准测试 | SWE-bench、GAIA、WebArena | [benchmarks](benchmarks/README.md) |
| 博客 | 一手工程经验 | [blogs](blogs/README.md) |
| 社区 | 提问与讨论 | [communities](communities/README.md) |
| Awesome 列表 | 持续更新的资源合集 | [awesome-lists](awesome-lists/README.md) |

## 读完能做到

- [ ] 说出论文区三篇奠基工作各自对应 Agent 的哪根支柱，并按规定顺序读
- [ ] 开源项目选型时不被 star 数绑架，能区分哪些项目有深读卡片、哪些只在索引表里
- [ ] 往资源库加一条新资源：用资源模板建卡、在分类 README 汇总表登记，两步不漏
- [ ] 判断一份资料够不够收录标准（一手来源优先、活跃维护或里程碑价值）

## 章末自测

1. **回忆**：ReAct、Toolformer、Reflexion 三篇分别对应 Agent 的哪三大支柱？（提示：见 papers/README.md）
2. **应用**：你发现一个维护活跃的量化推理库，想收进资源库。按本章规矩要走哪几步、用什么模板？（提示：见本页「使用说明」与 ../14-templates/resource-template.md）
3. **判断**：能否仅凭「14.6 万 star」就把某个框架写进选型结论？还缺哪些判断依据？（提示：见 projects/README.md 的提示框）

## 本章术语速查

资源卡片里全是专有名词，拿到一张新卡，先按这几个词查户口。

| 英文术语 | 中文 | 白话一句话 |
|---|---|---|
| ReAct | 推理+行动 | 「一边想一边干」的开山论文：让模型说一步做一步，给 Agent 循环上了第一次户口。 |
| Toolformer | 工具自我学习模型 | 证明模型能自学何时该按计算器、何时该搜网页的一篇，工具调用线的祖师爷。 |
| Reflexion | 反思 | 干完活让模型自己复盘，带着心得再战一回，自我反思这条路的开山之作。 |
| Benchmark | 基准测试 | 统一考场：SWE-bench、GAIA、WebArena 监考规则各不同，先比卷子再比分数。 |
| Dataset | 数据集 | 训练和评估的口粮，翻卡片先看两样：许可证和规模。 |
| Fine-tuning | 微调 | 拿自家数据接着练一个现成模型，比从头训省钱得多，但也照样能练过拟合。 |
| RLHF | 人类反馈强化学习 | 人来给答案打分，模型照着人类的口味调，后训练阶段的常客。 |
| MCP | 模型上下文协议 | Agent 界的 USB-C：一套接口，工具和数据来源插哪个模型都能用。 |
| Awesome List | 精选资源合集 | 社区维护的目录型清单，值不值得收藏，就看最近半年还有没有人收拾它。 |
| arXiv | 预印本平台 | 论文在同行评审前抢先首发的站点，消息最灵，也最需要挑着读。 |
| Frontmatter | 头部元信息 | 卡片开头用 --- 围住的那栏户口：标签、类型、状态，少了它站内链接就断一片。 |

