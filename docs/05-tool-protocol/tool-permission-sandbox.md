---
tags: [safety, tooling, engineering]
type: knowledge
status: published
updated: 2026-09-22
---

# 工具权限与沙箱

{% hint style="info" %}
**一句话**：权限决定「Agent 能不能做」，沙箱决定「做坏了影响多大」——两者合起来是 Agent 安全的承重墙。
  **难度**：进阶
  **标签**：`#safety` `#tooling`
{% endhint %}

## 先看结论

- 权限三问：谁授权（allowlist/策略）？何时拦（执行前管道）？留什么痕（审计日志）？
- 沙箱梯度：进程内 → 容器 → 内核级隔离（Landlock/seccomp）→ 独立虚拟机，隔离强度与成本递增
- 提示注入使「模型被騙着用合法权限做坏事」成为主要攻击面（→ [提示注入](../10-evaluation-safety/prompt-injection.md)），权限最小化是最后防线
- 网络出口控制比文件系统更常被忽视：数据外泄多半走网络

## 执行流水线

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#E7F4F3","primaryBorderColor":"#0D9488","primaryTextColor":"#1F2937","secondaryColor":"#CAE7E5","tertiaryColor":"#F5FBFA","lineColor":"#7AC4BE","actorBkg":"#ECF6F5","actorBorder":"#0D9488","actorTextColor":"#1F2937","signalColor":"#56B4AC","noteBkgColor":"#D3ECEA","noteBorderColor":"#0D9488","noteTextColor":"#1F2937","labelBoxBkgColor":"#E7F4F3","labelBoxBorderColor":"#0D9488"}}}%%
flowchart LR
  A[模型发出 tool-call] --> B["Hook 拦截<br/>人工/自动审批"]
  B --> C["权限检查<br/>allowlist/限额"]
  C --> D["沙箱执行<br/>受限 FS/网络/超时"]
  D --> E[改写与审计记录]
```

*《图：五个方框一条直线，没有旁路——模型发出的 tool-call 要落到沙箱，先得被 Hook 拦一次、再被 allowlist 问一次》*

## 沙箱技术梯度

| 层级 | 技术 | 防住 | 防不住 |
|---|---|---|---|
| 进程内 | 语言级 try/catch、资源限制 | 崩溃 | 恶意代码、文件破坏 |
| 容器 | Docker + 只读挂载 + 网络策略 | 文件系统破坏、横向移动 | 内核漏洞 |
| 内核级 | Landlock、seccomp、Windows AppContainer | 文件/网络细粒度管控 | 内核 0day |
| 虚拟机 | Firecracker microVM、gVisor | 几乎一切 | 性能开销 |

## 源码案例

- **DeepSeek Harness：流水线 + landlock-run**（[仓库](https://github.com/deepseek-ai/deepseek-harness)）：内置沙箱基于 Linux **Landlock**（内核级、无守护进程、细粒度文件访问规则）；整个执行前检查链（Hook → 审批 → 权限 → 沙箱 → 超时）本身就是插件——安全策略从「写死在代码」变成「可替换的配置」
- **Claude Code 的权限模式**（逆向分析，[提示词全集](https://github.com/Piebald-AI/claude-code-system-prompts)）：allowlist 记忆（"本会话不再询问 npm test"）+ 危险命令确认策略（安装、删除、push 类必须解释原因并确认）+ 可选沙箱模式；其经验是**审批疲劳管理**——高频安全操作自动放行，低频高危操作才打断用户
- **Pi 的 YOLO + 外置沙箱**：默认无审批，官方立场是「宿主级沙箱由用户自选工具兜底」——说明了同一安全目标下「审批优先」与「隔离优先」两条路线的取舍

## 最佳实践

- 默认拒绝（deny by default），按需开洞；allowlist 要带过期与会话作用域
- 工作目录隔离：Agent 只能写项目目录，home 与系统路径只读
- 网络出口白名单：只允许工具声明的域名；egress 审计常驻
- 所有执行留痕：who/when/what/参数/结果，可回放（append-only 日志是现成方案）

## 核心机制：权限即代码，伤害有上界

权限的本质是一个**能力集合**，每次工具调用都在消耗其中一项：

$$
\mathcal{C}=\big\{(o,a)\;\big|\;o\in\text{对象},\;a\in\{\text{read},\text{write},\text{delete},\text{send},\text{execute}\}\big\}
$$

核心结论是：**最大伤害由权限决定，而不是由模型行为决定**。

$$
\text{max damage}\;\le\;f(\mathcal{C})\times\text{不可逆性}
$$

因此「权限最小化」是可证明有效的唯一手段——无论模型被注入、越狱还是单纯犯错，都突破不了 $$\mathcal{C}$$ 的边界；而 prompt 层的防御只是概率性的。

执行流水线的每个环节对应一类风险，缺一即留口子：

| 环节 | 拦截的风险 |
|---|---|
| Hook 拦截 | 可程序化识别的非法调用 |
| 审批 | 高风险/不可逆动作 |
| 权限检查 | 越权访问 |
| 沙箱 | 越界执行（文件/网络） |
| 超时 | 资源耗尽与挂死 |

**默认拒绝（deny by default）是基线**：未显式授权的动作一律不执行，而不是「未禁止即可执行」。这条原则把安全从「穷举黑名单」变成「白名单授权」，在 Agent 这种动作空间开放的场景里尤其关键。

## 常见误区

- ❌ 沙箱是可选优化：联网 Agent 没有沙箱 = 把 shell 交给所有网页内容
- ❌ 容器 = 绝对安全：容器逃逸与内核共享问题真实存在，高危场景上 microVM
- ❌ 审批一次永久放行：权限提升要有时效，会话结束即回收

## 小练习

为一个「自动分析用户上传 CSV 并生成图表」的 Agent 设计执行环境：代码执行放哪一层沙箱？网络策略是什么？哪些动作需要人工审批？

## 参考资料

- [Claude Code 系统提示词全集（权限与确认策略的现网写法）](https://github.com/Piebald-AI/claude-code-system-prompts)
- [E2B（面向不可信代码执行的 microVM 沙箱）](https://github.com/e2b-dev/E2B)
- [gVisor（用户态内核做 syscall 拦截）](https://gvisor.dev/)
- [Firecracker（冷启动毫秒级的微 VM，多租户执行池的底座）](https://firecracker-microvm.github.io/)
- [Linux landlock 文档（文件系统权限的最小化）](https://docs.kernel.org/userspace-api/landlock.html)

## 相关知识点

- [提示注入](../10-evaluation-safety/prompt-injection.md)
- [权限控制与沙箱隔离](../10-evaluation-safety/permission-sandbox.md)
- [Human-in-the-loop](../02-agent-basics/human-in-the-loop.md)

