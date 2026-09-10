---
tags: [framework, multi-agent]
type: knowledge
status: published
updated: 2026-09-10
---

# AutoGen

> **一句话**：微软的多智能体对话框架（现与 Semantic Kernel 合流为 Microsoft Agent Framework）：让多个 Agent 通过对话协作，GroupChat 模式的开创者。
> **难度**：进阶
> **标签**：`#framework` `#multi-agent`

## 先看结论

- 核心思想：Agent = 能发消息、能执行代码的对话参与者；协作 = 消息流
- 两大贡献：代码执行沙箱内嵌（对话中生成的代码安全执行）与 GroupChat 编排
- 重要变迁：microsoft/autogen（v0.4 重构为事件驱动架构）与 Semantic Kernel 于 2025 年合并为 **Microsoft Agent Framework**（[仓库](https://github.com/microsoft/agent-framework)）；学习新项目用后者，学思想可看两者
- 适合：多 Agent 研究原型、代码生成-执行类任务、对话式协作实验

## 核心概念

| 概念 | 作用 |
|---|---|
| AssistantAgent | 带 LLM 的对话参与者 |
| UserProxy | 代表人类/执行代码的代理 |
| GroupChat + Manager | 共享消息流 + 发言调度 |
| Handoff | 控制权移交（v0.4+） |

## 双 Agent 对话（经典入门例）

```python
from autogen import AssistantAgent, UserProxyAgent

assistant = AssistantAgent("coder", llm_config=llm_cfg)
user = UserProxyAgent("reviewer",
    code_execution_config={"work_dir": "sandbox"})  # 沙箱执行代码
user.initiate_chat(assistant, message="写个脚本统计本目录代码行数并运行验证")
```

## 源码案例

- **GroupChatManager 的发言选择**（[GitHub](https://github.com/microsoft/autogen)）：读它的 `select_speaker` 实现——用 LLM 看消息流选下一个发言者，是 [群聊模式](../08-multi-agent/group-chat.md) 的原型代码；v0.4 重构为 actor 模型式事件驱动，每个 Agent 是独立 actor，消息队列解耦——与 [DeepSeek Harness 的事件流](../02-agent-basics/state-management.md) 异曲同工
- **沙箱执行**：UserProxy 的代码执行配置（Docker/本地/Jupyter）——「模型写代码 → 框架安全执行 → 结果回对话」的完整闭环，呼应 [代码执行工具](../05-tool-protocol/browser-code-filesystem-tools.md)
- **学术论文背书**：AutoGen 论文（[arXiv:2308.08155](https://arxiv.org/abs/2308.08155)）系统评估了双 Agent / 群聊等拓扑在数学、编码、问答任务的效果，是少数有消融实验的多 Agent 框架文献

## 常见误区

- ❌ AutoGen = AutoGPT：完全不同的项目；AutoGPT 是早期自治 Agent 尝试，AutoGen 是微软的多 Agent 框架
- ❌ 用 v0.2 教程学新版本：v0.4 是彻底重构（API 不兼容），看文档认准版本
- ❌ 群聊当生产架构：发言调度不确定性高，生产环境多用其 handoff/工作流形态

## 小练习

用 AutoGen 双 Agent（写代码 + 跑代码）解决「解析一个 CSV 并画图」：观察代码执行-报错-修正的循环，记录它重试了几次、错误信息如何被利用。

## 相关资源

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [AutoGen 论文](https://arxiv.org/abs/2308.08155)

## 相关知识点

- [群聊模式](../08-multi-agent/group-chat.md)
- [Semantic Kernel](semantic-kernel.md)
