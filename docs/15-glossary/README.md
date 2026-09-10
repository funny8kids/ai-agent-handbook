---
tags: [basics, resource]
type: index
status: published
updated: 2026-09-10
---

# 术语表

> 中英文术语速查。术语按主题分组，第一次出现在对应页面会给出中英文对照。

## Agent 基础

| 术语 | 英文 | 一句话解释 |
|---|---|---|
| 智能体 | Agent | 能自主规划、调用工具、根据反馈调整以完成目标的 AI 系统 |
| 大语言模型 | LLM（Large Language Model） | 海量文本上训练的下一个 token 预测器 |
| 智能体框架 | Agent Harness | 包裹模型的工程脚手架：循环、工具、权限、状态 |
| 提示工程 | Prompt Engineering | 设计输入以稳定引导模型输出的方法 |
| 上下文工程 | Context Engineering | 决定「每次调用上下文里放什么」的系统工程 |
| 人在回路 | Human-in-the-loop（HITL） | 在关键节点安排人类审批/纠偏的机制 |
| 自主性等级 | Autonomy Levels | 从「只建议」到「全自动」的放权光谱 |

## 模型与训练

| 术语 | 英文 | 一句话解释 |
|---|---|---|
| Token | Token | 文本的最小切分单位，计费与窗口的单位 |
| 嵌入 | Embedding | 文本的语义向量表示 |
| 上下文窗口 | Context Window | 模型一次可见的最大 token 数 |
| 注意力 | Attention | Transformer 中 token 间交换信息的机制 |
| 混合专家 | MoE（Mixture of Experts） | 每 token 只激活部分专家参数的稀疏架构 |
| 指令微调 | SFT（Supervised Fine-Tuning） | 用问答对教模型跟随指令 |
| 人类反馈强化学习 | RLHF | 用人类偏好训练奖励模型再强化学习 |
| 直接偏好优化 | DPO（Direct Preference Optimization） | 从偏好对直接学习的免 RL 对齐方法 |
| 幻觉 | Hallucination | 模型编造看似合理但错误的内容 |
| 推理模型 | Reasoning Model | 通过 RL 学会长思考链的模型（o1/R1 类） |
| 量化 | Quantization | 降低权重数值精度以压缩模型 |

## 工具与协议

| 术语 | 英文 | 一句话解释 |
|---|---|---|
| 函数调用 | Function Calling | 模型输出结构化函数调用意图的能力 |
| 模型上下文协议 | MCP（Model Context Protocol） | 模型与工具/数据源的统一接入协议 |
| 智能体间协议 | A2A（Agent-to-Agent） | 跨 Agent 发现与协作的开放协议 |
| 工具描述 | Tool Description | 工具的「说明书」，模型选择工具的依据 |
| 沙箱 | Sandbox | 限制 Agent 执行副作用的环境隔离 |
| 程序化工具调用 | PTC（Programmatic Tool Calling） | 模型写代码组合多轮工具调用 |
| 计算机使用 | Computer Use | 模型看截图操作图形界面的能力 |

## 记忆与检索

| 术语 | 英文 | 一句话解释 |
|---|---|---|
| 检索增强生成 | RAG（Retrieval-Augmented Generation） | 先检索资料再生成回答 |
| 向量数据库 | Vector Database | 存 Embedding 并做近邻搜索的数据库 |
| 重排序 | Rerank | 用精排模型对召回结果二次排序 |
| 知识图谱 | Knowledge Graph | 实体-关系网络的知识表示 |
| 图检索增强 | GraphRAG | 用知识图谱增强的 RAG |
| 会话压缩 | Compaction | 把历史对话摘要化以释放上下文空间 |
| 事件溯源 | Event Sourcing | 以不可变事件序列存储状态的架构 |

## 多智能体与工程

| 术语 | 英文 | 一句话解释 |
|---|---|---|
| 监督者模式 | Supervisor Pattern | 协调者拆解派发、工作者执行的多 Agent 架构 |
| 移交 | Handoff | Agent 间直接传递控制权 |
| 群聊模式 | Group Chat | 多 Agent 共享消息流协作的形态 |
| 提示注入 | Prompt Injection | 恶意指令藏进内容劫持 Agent 行为 |
| 越狱 | Jailbreak | 绕过模型安全对齐的攻击 |
| 可观测性 | Observability | 日志、追踪、监控构成的系统透明度 |
| 规范博弈 | Reward Hacking | 钻奖励定义空子达成字面目标 |
| 基准测试 | Benchmark | 标准化的能力评估任务集 |
