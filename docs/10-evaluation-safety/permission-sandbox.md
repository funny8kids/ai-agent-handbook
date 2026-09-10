---
tags: [safety, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 权限控制与沙箱隔离

> **一句话**：权限是「谁能做什么」的策略层，沙箱是「做坏了烧多大」的隔离层——本页聚焦治理模型与落地清单。

> 原理与沙箱技术梯度见 [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)。

## 先看结论

- 权限模型三要素：主体（哪个 Agent/用户）、客体（文件/API/数据）、动作（读/写/删/外发）——用「策略表」显式管理，别散在 prompt 里
- 审批要分级：按动作可逆性与影响面自动分级（只读自动 / 可逆写后审 / 不可逆必审）
- 沙箱选型按数据敏感度与动作风险，不是越强越好（成本与延迟）
- 审计日志是合规刚需：谁、何时、批准了什么、基于什么策略

## 核心机制

### 1. 权限是「能力集合」，伤害有上界

把一次 Agent 会话拥有的权限写成一个能力集合 $$\mathcal{C}$$，每个元素是一条（客体，动作）对：

$$
\mathcal{C}=\big\{(o,a)\;\big|\;o\in\text{对象},\;a\in\{\text{read},\text{write},\text{delete},\text{send}\}\big\}
$$

核心结论是**伤害上界由权限决定**，而不是由模型行为决定：

$$
\text{max damage}\;\le\;f(\mathcal{C})\;\times\;\text{不可逆性}
$$

因此「最小权限」不是一句口号，而是唯一有确定性的安全手段：无论模型被注入、越狱还是单纯犯错，它能造成的最大破坏都被 $$\mathcal{C}$$ 限制住。**权限最小化的收益是确定的，而 prompt 防御的收益是概率的。**

### 2. 审批分级：按可逆性与影响面

并非所有动作都要人审。分级依据与 [Human-in-the-loop](../02-agent-basics/human-in-the-loop.md) 的判据一致：

$$
\text{审批策略}=g\big(\text{可逆性},\;\text{影响面},\;\text{不确定性}\big)
$$

| 动作类型 | 策略 | 例子 |
|---|---|---|
| 只读 | 自动 | 搜索、读文件 |
| 可逆写 | 域内自动，事后审计 | 改代码（有 git）、写草稿 |
| 不可逆 / 高影响 | 必须事中确认 + 白名单 | 删库、付款、对外发信 |
| 代码执行 | 沙箱内自动，网络默认关 | 跑脚本、装依赖 |

### 3. 纵深防御是乘法

设部署了 $$L$$ 层独立防线，第 $$l$$ 层被绕过的概率为 $$p_l$$，则整体被突破的概率近似：

$$
P(\text{breach})\approx\prod_{l=1}^{L}p_l
$$

这解释了为什么「权限 + 沙箱 + 审批 + 审计」要一起上：任何单层都不够强（例如 $$p_l=0.5$$），但四层串联能把风险压到约 6%。也解释了为什么「在系统提示词里写不要危险操作」几乎没有安全价值——它既不是独立层，也容易被注入绕过（见 [提示注入](prompt-injection.md)）。

### 4. 沙箱梯度：强度 vs 成本

| 层级 | 隔离强度 | 启动/开销 | 适用 |
|---|---|---|---|
| 进程内 + 路径限制 | 弱 | 最低 | 只读、可信脚本 |
| 容器（namespace/cgroup） | 中 | 低 | 一般代码执行 |
| 内核级限制（如 Linux Landlock、seccomp） | 中高 | 低 | 文件/网络细粒度限制 |
| microVM（如 Firecracker） | 高 | 中 | 多租户、不可信代码 |
| 硬件隔离 / 独立主机 | 最高 | 高 | 极高敏感场景 |

选型原则：**按「不可信程度 × 数据敏感度」选，而不是一律上最强**。多数内部 Agent 用「容器 + 默认无网络 + 只读挂载」已足够；只有执行用户提交的代码、或多租户共享时才需要 microVM。

## 权限策略表示例

```yaml
agent: data-analyst
permissions:
  - resource: "warehouse://sales/*"
    actions: [read]
  - resource: "s3://reports/*"
    actions: [read, write]
    require_approval: never
  - resource: "smtp://*"
    actions: [send]
    require_approval: always
    allowed_recipients: ["@company.com"]
sandbox: container   # container | landlock | microvm
budget:
  tokens_per_day: 5_000_000
```

## 源码案例

- **DeepSeek Harness：策略即插件**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：审批、权限、沙箱（`packages/sandbox`）都是工具执行流水线上的可替换环节——同一套 Agent 换 profile 即切换治理强度（个人开发模式 vs 企业合规模式），治理模型与 Agent 逻辑彻底解耦
- **Claude Code 的会话权限记忆**（逆向分析，[提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts)）：allowlist 带 scope（本会话/本项目/全局），危险类目永不静默放行——「权限晋升要显式、要过期」的实操范本
- **microVM 落地参考**：更严格场景看 [Firecracker](https://github.com/firecracker-microvm/firecracker)——AWS Lambda 同款 microVM 技术，隔离强、启动快
- **内核级沙箱**：[Linux Landlock](https://docs.kernel.org/userspace-api/landlock.html) 提供无特权进程即可使用的文件访问限制——适合做「细粒度、低开销」的一层

## 上线检查清单

- [ ] 每个 Agent 有显式策略表（非 prompt 描述）
- [ ] 不可逆动作 100% 人审 + 收件人白名单
- [ ] 代码执行在 ≥ 容器级沙箱，默认无网络
- [ ] 全部动作进 append-only 审计日志
- [ ] token/调用预算熔断配置
- [ ] 权限有 TTL，会话结束回收

## 常见误区

- ❌ 权限写进系统提示词当策略：prompt 可被注入影响，策略必须在执行层强制
- ❌ 一次审批永久授权：权限要带作用域与时效（TTL）
- ❌ 审计日志可改写：append-only + 异地备份，否则合规等于没做
- ❌ 沙箱一律上最强：成本与延迟也是约束，按不可信程度分级
- ❌ 只防「模型坏」不防「模型错」：权限设计要同时覆盖恶意与失误两种情形

## 小练习

给「财务报表 Agent」（读 ERP + 生成报告 + 邮件发送）写完整的权限策略表 YAML，决定沙箱层级，并说明你用纵深防御的哪几层、每层大概能把什么风险压下去。

## 参考资料

- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/)（权限与失控风险）
- [Firecracker microVM](https://github.com/firecracker-microvm/firecracker)（AWS Lambda 同款轻量虚拟化，NSDI 2020 论文）
- [Linux Landlock 文档](https://docs.kernel.org/userspace-api/landlock.html)
- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)

## 相关知识点

- [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)
- [Human-in-the-loop](../02-agent-basics/human-in-the-loop.md)
- [提示注入](prompt-injection.md)
