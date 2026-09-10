---
tags: [tooling]
type: knowledge
status: published
updated: 2026-09-10
---

# Tool Use

> **一句话**：Tool Use 是比 Function Calling 更宏观的话题：如何设计工具集、控制工具面、路由选择与组合调用，让 Agent 的「手」够用且不乱摸。

## 先看结论

- 工具设计的四个原则：原子性（一件事）、无歧义（名字和描述自解释）、幂等友好（失败可重试）、返回可消化（结构化 + 截断）
- 工具面控制：数量多 → 分组 / 延迟加载 / 动态注入
- 组合调用：串行依赖、并行无依赖、程序化组合（让模型写代码一次执行多步）
- 工具结果的「可观察性」决定模型下一步质量：报错要含上下文
- 工具集大小与模型的选择难度成正比——**精简是能力，不是妥协**

## 核心机制

### 1. 工具选择是一个分类问题

模型在每一步要从工具集 $$T$$ 中选一个（或几个）调用。这本质上是在做分类，而分类准确率随候选数增加而下降。粗略地：

$$
P(\text{选对})\;\text{随}\;|T|\;\text{增大而下降},\qquad
\text{且 schema 成本}\propto |T|
$$

两条推论：一是**工具不是越多越好**，相近功能的工具会互相干扰；二是**拆分工具面**（按场景只暴露相关工具）比「全量给」更准也更省。这就是「延迟加载/动态注入」的动机。

### 2. 四个设计原则及其失效后果

| 原则 | 反例 | 正例 | 违反了会怎样 |
|---|---|---|---|
| 原子性 | `manage_user(action="create/delete/update")` | `create_user` / `delete_user` 分开 | 参数组合爆炸，权限无法细粒度控制 |
| 无歧义 | `get_data` | `get_order_by_id` | 与相近工具混用 |
| 参数扁平 | 5 层嵌套对象 | 一层字段 + 枚举 | 模型漏填、错填 |
| 返回可消化 | 返回 500 行原始 HTML | 提炼后的 JSON + 截断说明 | 吃满上下文预算、稀释注意力 |

**原子性还有一个安全收益**：工具拆得细，权限就能按工具粒度授予（只给 `read_file` 不给 `delete_file`），而不是「给了一个万能工具就等于给了全部权限」。

### 3. 组合调用的三种形态

$$
\underbrace{\text{串行}}_{\text{有依赖，A 的结果是 B 的输入}}
\quad
\underbrace{\text{并行}}_{\text{无依赖，同一轮发出}}
\quad
\underbrace{\text{程序化}}_{\text{模型写一段代码组合多次调用}}
$$

前两种是 Function Calling 的常规用法。第三种（常称 PTC，Programmatic Tool Calling）把「查 API → 过滤 → 写文件」写成一段一次执行的程序，**把多轮交互压成一轮**：省 token、确定性更强，中间结果也不必进上下文。代价是需要在沙箱里执行模型生成的代码——安全要求更高（见 [工具权限与沙箱](tool-permission-sandbox.md)）。

### 4. 错误契约与幂等

工具失败时回填什么，直接决定 Agent 能否自我修正：

| 回填内容 | 模型能否修正 |
|---|---|
| `"error"` | 不能（信息量为零） |
| `"FileNotFoundError: /tmp/a.txt 不存在"` | 能（可换路径或先创建） |
| `"参数 unit 取值非法（应为 celsius/fahrenheit）"` | 能（可改参数重试） |

另一个常被忽略的点是**幂等**：重试安全的工具（查询、`PUT` 式覆盖写）可以放心重试；非幂等的（创建、支付、发消息）必须带幂等键或人工确认，否则「重试」会变成「重复执行」（见 [错误恢复与重试](../07-planning/error-recovery-retry.md)）。

## 工具集设计清单

| 原则 | 反例 | 正例 |
|---|---|---|
| 原子性 | `manage_user(action="create/delete/update")` | `create_user` / `delete_user` 分开 |
| 无歧义 | `get_data` | `get_order_by_id` |
| 参数扁平 | 5 层嵌套对象 | 一层字段 + 枚举 |
| 结果干净 | 返回 500 行原始 HTML | 返回提炼后的 JSON + 截断说明 |

## 源码案例

**三家 harness 的工具哲学对比**（案例深拆见 [编程 Agent](../12-applications/coding-agent.md)）：

| 项目 | 工具面策略 | 哲学 | 关键机制 |
|---|---|---|---|
| Pi（[仓库](https://github.com/earendil-works/pi)） | 精简 | 原语而非成品，能力靠组合与扩展 | 工具以 name + schema + execute 注册（细节以官网为准） |
| Claude Code（社区逆向） | 覆盖面广 + 延迟加载 | 「何时用我/何时别用我」写进描述 | 先列工具名、按需取完整 schema；子 Agent 工具面隔离 |
| DeepSeek Harness（[仓库](https://github.com/deepseek-ai/deepseek-harness)） | 插件化、模式可切 | 工具面 = 可插拔策略 | 执行走统一流水线；支持程序化组合调用 |

- **Claude Code 的搜索/读取/命令分工**：搜索用专用搜索工具、已知路径用读取工具、复杂管道用 shell——**工具描述里明确分工边界**，是选择准确率的关键
- **DeepSeek Harness 的程序化组合**：模型写一段代码把「查 API → 过滤 → 写文件」组合成一次执行——多轮工具调用变一轮代码执行，省 token 且确定性强

## 工程含义

- **结果必须先「消化」再回填**：截断、只留关键字段、附上「已截断」说明，避免一次 `ls -R` 毁掉上下文预算。
- **工具面按阶段变化**：探索阶段只给只读工具，确认后才开放写入工具——工具面是状态机当前阶段的函数。
- **为工具写测试**：schema 校验、错误路径、幂等性都应有用例；工具的可靠性直接决定 Agent 的可靠性。
- **并发要防竞态**：并行调用同一文件系统工具会产生冲突，需要串行化或加锁。

## 常见误区

- ❌ 万能工具：一个工具 20 个可选参数 = 20 个出错点，拆开
- ❌ 工具结果直接塞回：5000 行的目录树输出会毁掉上下文预算，先截断/摘要
- ❌ 忽略并发：并行调用同一文件系统工具会产生竞态，要串行化或加锁
- ❌ 把非幂等工具当幂等用：重试支付/发消息会造成重复副作用
- ❌ 报错只回 "error"：浪费一轮且模型无法修正

## 小练习

把「CRM 管理工具」（一个大 JSON 参数含 15 个操作）重构成原子工具集，列出每个工具的 description 要点，并指出哪些工具非幂等、需要什么幂等策略。

## 参考资料

- [Anthropic: Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761)（Schick et al., 2023）
- [ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs](https://arxiv.org/abs/2307.16789)（Qin et al., 2023）
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)（Yao et al., 2022）

## 相关知识点

- [Function Calling](function-calling.md)
- [工具选择与路由](../07-planning/tool-selection-routing.md)
- [MCP](mcp.md)
