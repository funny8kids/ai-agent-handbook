---
tags: [framework, multi-agent]
type: knowledge
status: published
updated: 2026-09-10
---

# AutoGen

> **一句话**：微软的多智能体对话框架（现与 Semantic Kernel 合流为 Microsoft Agent Framework）：让多个 Agent 通过对话协作，GroupChat 模式的开创者。

## 先看结论

- 核心思想：Agent = 能发消息、能执行代码的对话参与者；协作 = 消息流
- 两大贡献：代码执行沙箱内嵌（对话中生成的代码安全执行）与 GroupChat 编排
- 重要变迁：`microsoft/autogen` 与 Semantic Kernel 已合流为 **Microsoft Agent Framework**（[仓库](https://github.com/microsoft/agent-framework)）；学新项目用后者，学思想可看两者
- 适合：多 Agent 研究原型、代码生成-执行类任务、对话式协作实验

## 核心抽象

AutoGen 把「协作」简化为一个统一模型：

$$
\text{Agent}=\big(\text{能发消息},\;\text{能接收消息},\;\text{可选：能执行代码}\big)
\Longrightarrow
\text{系统}=\text{消息流}+\text{发言调度}
$$

这个模型的好处是**统一的接口**：人类代理、LLM 代理、工具代理都是「消息参与者」，因此可以自由组合。代价是控制流隐式（谁下一个说话由调度器决定），复杂拓扑不如显式图好调试。

| 概念 | 作用 |
|---|---|
| AssistantAgent | 带 LLM 的对话参与者 |
| UserProxy | 代表人类/执行代码的代理 |
| GroupChat + Manager | 共享消息流 + 发言调度 |
| Handoff | 控制权移交 |

## 双 Agent 对话（经典入门例）

```python
from autogen import AssistantAgent, UserProxyAgent

assistant = AssistantAgent("coder", llm_config=llm_cfg)
user = UserProxyAgent("reviewer",
    code_execution_config={"work_dir": "sandbox"})  # 沙箱执行代码
user.initiate_chat(assistant, message="写个脚本统计本目录代码行数并运行验证")
```

这个例子里包含了 AutoGen 最有价值的设计：**「模型写代码 → 框架安全执行 → 报错信息回填 → 模型修正」的闭环**。代码执行被放在受控目录（`work_dir`）中，避免模型直接操作宿主机。

## 选型对比

| 维度 | AutoGen / Agent Framework | CrewAI | LangGraph |
|---|---|---|---|
| 组织隐喻 | 对话参与者 | 球队角色 | 状态图 |
| 控制流 | 消息流 + 调度器 | 顺序/层级 | 显式图 |
| 代码执行 | 内嵌沙箱（强项） | 需自行接入 | 需自行接入 |
| 调试难度 | 较高（隐式流） | 中 | 低（显式图） |
| 适合 | 代码生成-执行、研究原型 | 角色化快速组队 | 可审计工作流 |

**选型建议**：需要「模型写代码并安全执行」的闭环 → AutoGen/Agent Framework；需要角色化快速组队 → CrewAI；需要严格可审计的控制流 → LangGraph。

## 源码案例

- **GroupChatManager 的发言选择**（[GitHub](https://github.com/microsoft/autogen)）：读它的发言选择实现——用 LLM 看消息流决定下一个发言者，是 [群聊模式](../08-multi-agent/group-chat.md) 的原型代码；后续版本重构为 actor 模型式事件驱动，每个 Agent 是独立 actor，消息队列解耦——与 [状态机与事件驱动](../11-engineering/state-machine-event-driven.md) 的思路相通
- **沙箱执行**：UserProxy 的代码执行配置（Docker/本地/Jupyter）——「模型写代码 → 框架安全执行 → 结果回对话」的完整闭环
- **学术论文背书**：AutoGen 论文（[arXiv:2308.08155](https://arxiv.org/abs/2308.08155)）系统评估了双 Agent / 群聊等拓扑在数学、编码、问答任务上的效果，是少数带消融实验的多 Agent 框架文献

## 常见误区

- ❌ AutoGen = AutoGPT：完全不同的项目；AutoGPT 是早期自治 Agent 尝试，AutoGen 是微软的多 Agent 框架
- ❌ 用旧版教程学新版本：项目经历过彻底重构（API 不兼容），看文档认准版本
- ❌ 群聊当生产架构：发言调度不确定性高，生产环境多用其 handoff/工作流形态
- ❌ 让代码执行默认跑在宿主机：必须用容器/受限目录，否则一次错误生成的代码就可能造成破坏

## 小练习

用 AutoGen 双 Agent（写代码 + 跑代码）解决「解析一个 CSV 并画图」：观察「代码执行 → 报错 → 修正」的循环，记录它重试了几次、错误信息如何被利用。

## 参考资料

- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://arxiv.org/abs/2308.08155)（Wu et al., 2023）
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [AutoGen GitHub（旧仓库）](https://github.com/microsoft/autogen)

## 相关知识点

- [群聊模式](../08-multi-agent/group-chat.md)
- [Semantic Kernel](semantic-kernel.md)
- [通信协议](../08-multi-agent/communication-protocol.md)
