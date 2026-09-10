---
tags: [evaluation]
type: knowledge
status: published
updated: 2026-09-10
---

# 基准测试总览

> **一句话**：基准测试是 Agent 能力的「标准化考场」——看懂每个基准考什么、怎么算分、有什么局限，才不会被榜单牵着走。

## 问题动机

「哪个 Agent 最强」如果没有统一协议就没有答案：任务集不同、环境不同、评分方式不同，分数不可比。基准的价值在于把这三件事固定下来，让不同系统能在同一把尺子下比较；但尺子本身的构造方式，决定了分数能不能外推到你的场景。

## 核心机制

### 1. 基准的三要素

任何一个基准都由三件事定义，差异也全在这三处：

| 要素 | 说明 | 常见差异点 |
|---|---|---|
| 任务集 | 考什么 | 领域、难度分布、是否去重防污染 |
| 执行环境 | 在哪做 | 真实仓库 / 模拟环境 / 受控沙箱 |
| 评分协议 | 怎么算分 | 程序化验证 / 精确匹配 / LLM 评分 |

### 2. 两种典型评分协议

**程序化验证（最可信）**：SWE-bench 的判分是「运行仓库测试」，一个实例被算作解决，当且仅当：

$$
\text{Resolved}=\mathbb{1}\Big[\text{FAIL\_TO\_PASS 全部通过}\;\wedge\;\text{PASS\_TO\_PASS 不回归}\Big]
$$

$$
\text{Resolved Rate}=\frac{\#\{\text{resolved instances}\}}{\#\{\text{all instances}\}}
$$

好处是客观、可复现；代价是任务必须自带可执行验证，且对环境的依赖极重。

**生成式多解评分**：对一题多解的任务用 pass@k（见 [Agent 评估指标](evaluation-metrics.md)）：

$$
\text{pass@}k=\mathbb{E}_{\text{problems}}\left[1-\frac{\dbinom{n-c}{k}}{\dbinom{n}{k}}\right]
$$

**LLM 评分**：用于开放式任务（GAIA 的部分题、对话质量），必须报告与人类的一致度（Cohen's $\kappa$），否则分数不可信。

### 3. 为什么「分数不可比」

同一个模型，换个执行框架（harness）分数可以差很多——工具集、上下文构造、循环实现、重试策略都在受影响。因此比较成绩时至少要固定：

- 模型版本与解码参数（温度、最大步数）
- harness 及其工具集
- 是否允许人工介入、超时与预算

**模型 + harness = Agent**，这是读榜单时最容易忽略的一条。

## 主流基准一览

| 基准 | 考什么 | 环境 | 评分 | 深入页面 |
|---|---|---|---|---|
| SWE-bench / Verified | 真实 GitHub issue 修复 | 真实代码库 + 测试 | 测试通过率 | [详页](agentbench-webarena-swebench-gaia-toolbench.md) |
| GAIA | 通用助理任务（多步推理 + 工具） | 受控工具环境 | 精确匹配 + 人工确认 | 同上 |
| WebArena | 真实网站长程任务 | 自托管网站沙箱 | 程序化状态断言 | 同上 |
| AgentBench | 八场景综合能力 | 多环境 | 各环境自定 | 同上 |
| ToolBench / BFCL | 工具调用与选择 | API 沙箱 | 可执行性 + 匹配 | 同上 |
| Terminal-Bench / OSWorld | 终端/桌面操作 | 真实 OS 环境 | 状态/文件断言 | — |
| τ-bench | 工具 + 用户模拟 + 策略遵守 | 客服域 | 数据库状态 + 策略 | — |

## 直觉解释

榜单像「驾校科目考试」：SWE-bench 是「给你一辆真车去修真路」，GAIA 是「给地图让你送三件快递」，WebArena 是「在模拟城市里完成一天的差事」——驾照高分不等于能开你所在城市的晚高峰。

## 工程含义

- **借协议自建内测集**：直接套用某个基准的「任务格式 + 判分方式」，把任务换成你自己的领域，比追榜单有用得多。
- **关注 harness 敏感性**：选型时用同一模型横评多个 harness（Claude Code / OpenHands / Pi / DeepSeek Harness），差 20%+ 很常见。
- **防数据污染**：基准题目若混进训练数据，分数虚高；看基线报告时要确认去重声明与时间切分。

## 常见误区

- ❌ 刷榜即能力：SWE-bench 高分模型在你的私有代码库上可能水土不服（上下文构造、内部工具链差异）
- ❌ 忽略 harness 差异：同一模型不同 harness 成绩可差 20%+，**模型 + harness = Agent**
- ❌ 只看一个数字：pass@1、pass@10、Resolved Rate 不是一回事，跨报告比较要看清 $k$ 与预算
- ❌ 忽略成本：达到同样分数，token/时延差一个数量级的方案在生产上不是「同一水平」

## 参考资料

- [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770)（Jimenez et al., 2023）
- [GAIA: A Benchmark for General AI Assistants](https://arxiv.org/abs/2311.12983)（Mialon et al., 2023）
- [WebArena: A Realistic Web Environment for Building Autonomous Agents](https://arxiv.org/abs/2307.13854)（Zhou et al., 2023）
- [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688)（Liu et al., 2023）
- [ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs](https://arxiv.org/abs/2307.16789)（Qin et al., 2023）
- [OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments](https://arxiv.org/abs/2404.07972)（Xie et al., 2024）
- [τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains](https://arxiv.org/abs/2406.12045)（Yao et al., 2024）

## 相关知识点

- [Agent 评估指标](evaluation-metrics.md)
- [基准测试资源](../13-resources/benchmarks/README.md)
