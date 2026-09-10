---
tags: [safety, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 📊 权限控制与沙箱隔离

> **一句话**：权限是「谁能做什么」的策略层，沙箱是「做坏了烧多大」的隔离层——从产品视角再讲一遍这对组合拳，聚焦治理模型与落地清单。
> **难度**：⭐️⭐️ 进阶
> **标签**：`#safety` `#engineering`

> 原理与沙箱技术梯度见 [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)，本页聚焦**治理视角**。

## 📌 先看结论

- 权限模型三要素：主体（哪个 Agent/用户）、客体（文件/API/数据）、动作（读/写/删/外发）——用「策略表」显式管理，别散在 prompt 里
- 审批要分级：按动作可逆性与影响面自动分级（只读自动 / 可逆写后审 / 不可逆必审）
- 沙箱选型按数据敏感度与动作风险，不是越强越好（成本与延迟）
- 审计日志是合规刚需：谁、何时、批准了什么、基于什么策略

## 🧩 权限策略表示例

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

## 📦 源码案例

- **DeepSeek Harness：策略即插件**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：审批、权限、沙箱（内置 landlock-run）都是工具执行流水线上的可替换环节——同一套 Agent 换 profile 即切换治理强度（个人开发模式 vs 企业合规模式），治理模型与 Agent 逻辑彻底解耦
- **Claude Code 的会话权限记忆**（逆向分析）：allowlist 带 scope（本会话/本项目/全局），危险类目永不静默放行——「权限晋升要显式、要过期」的实操范本
- **Pi 的环境信任模型**：YOLO 默认 + 用户自选宿主沙箱——展示了另一极：把治理责任明确移交给环境配置而非运行时弹窗
- **microVM 落地参考**：Anthropic Computer Use 参考实现用 Docker + 快照重置；更严格场景看 Firecracker（[GitHub](https://github.com/firecracker-microvm/firecracker)）——AWS Lambda 同款 microVM 技术

## ✅ 上线检查清单

- [ ] 每个 Agent 有显式策略表（非 prompt 描述）
- [ ] 不可逆动作 100% 人审 + 收件人白名单
- [ ] 代码执行在 ≥ 容器级沙箱，默认无网络
- [ ] 全部动作进 append-only 审计日志
- [ ] token/调用预算熔断配置
- [ ] 权限有 TTL，会话结束回收

## ⚠️ 常见误区

- ❌ 权限写进系统提示词当策略：prompt 是可被注入影响的（→ [提示注入](prompt-injection.md)），策略必须在执行层强制
- ❌ 一次审批永久授权：权限要带作用域与时效
- ❌ 审计日志可改写：append-only + 异地备份，否则合规等于没做

## 🧪 小练习

给「财务报表 Agent」（读 ERP + 生成报告 + 邮件发送）写完整的权限策略表 YAML，并决定沙箱层级。

## 📚 相关知识点

- [工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md)
- [Human-in-the-loop](../02-agent-basics/human-in-the-loop.md)
