---
tags: [evaluation, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# AgentBench、WebArena、SWE-bench、GAIA、ToolBench

> **一句话**：五大基准各考一面：SWE-bench 考修真代码、WebArena 考逛真网站、GAIA 考通用助理、AgentBench 考综合、ToolBench 考调工具——合起来是 Agent 能力的全景图。
> **难度**：进阶
> **标签**：`#evaluation`

## 五基准精读

### 1. SWE-bench（编程 Agent 的黄金标准）

| 属性 | 内容 |
|---|---|
| 任务 | 2294 个真实 GitHub issue（Python 仓库），需产出通过测试的 patch |
| 评分 | Fail-to-Pass 测试通过率；Verified 子集经人工核验（500 题） |
| 关键资源 | [官网](https://www.swebench.com/) · [仓库](https://github.com/princeton-nlp/SWE-bench) · SWE-agent（[GitHub](https://github.com/SWE-agent/SWE-agent)） |

读法：对比各系统成绩时必须看 harness——同一模型在 SWE-agent、OpenHands、Claude Code 式 scaffold 下成绩差异巨大；任务描述（issue 文本）也常随 harness 增强（给 Agent 更多测试线索）。

### 2. WebArena（真实网站长程任务）

| 属性 | 内容 |
|---|---|
| 任务 | 812 个任务：购物、论坛、CMS、GitLab 四个自托管真实网站 |
| 评分 | 程序化验证最终环境状态（订单存在/页面状态正确） |
| 关键资源 | [官网](https://webarena.dev/) · [论文](https://arxiv.org/abs/2307.13854) |

读法：长程任务成功率至今不过半，暴露「多步规划 + 状态跟踪」仍是短板；网站 DOM 结构是它的输入假设，迁移到内网系统要重建观测层。

### 3. GAIA（通用助理基准）

| 属性 | 内容 |
|---|---|
| 任务 | 466 个人类几天能做对、AI 难做的题：多步推理、浏览、读文件、算术 |
| 评分 | 精确答案匹配；分 Level 1–3 难度 |
| 关键资源 | [论文](https://arxiv.org/abs/2311.12983) · [仓库](https://huggingface.co/spaces/gaia-benchmark/leaderboard) |

读法：设计哲学「人类容易 AI 难」；Anthropic 的多 Agent 研究系统正是靠「Lead + 并行 Worker + 工具增强」在 GAIA 类任务上拉开差距（[工程博客](https://www.anthropic.com/engineering/built-multi-agent-research-system)）。

### 4. AgentBench（综合能力体检）

| 属性 | 内容 |
|---|---|
| 任务 | 8 个环境：操作系统、数据库、知识图谱、网页浏览、数字游戏等 |
| 评分 | 各环境专用成功率，汇总多维报告 |
| 关键资源 | [论文](https://arxiv.org/abs/2308.03688) · [仓库](https://github.com/THUDM/AgentBench) |

读法：像「体检报告」——能看到某模型「数据库强、网页弱」这样的结构化短板，适合模型选型初筛。

### 5. ToolBench / BFCL（工具调用专精）

| 属性 | 内容 |
|---|---|
| 任务 | ToolBench：1.6 万真实 API 上规划调用链；BFCL（Berkeley Function-Calling Leaderboard）：函数选择+参数填空 |
| 评分 | 调用链可行性、参数准确率 |
| 关键资源 | [ToolLLM 论文](https://arxiv.org/abs/2307.16789) · [BFCL](https://gorilla.cs.berkeley.edu/leaderboard) |

读法：选模型时 BFCL 成绩与「Function Calling 可靠性」直接相关；但要注意 API 数量级——真实业务工具面小得多，高分不自动迁移。

## 核心机制：分数可比性的前提

基准分数只在**三个变量同时固定**时才可比：

$$
\text{可比}\iff\big(\text{模型版本},\;\text{harness},\;\text{预算}\big)\ \text{固定}
$$

- **模型版本**：供应商可能静默更新；比较要记录具体版本与解码参数
- **harness**：同一模型换执行框架，成绩常有可观差异（工具集、上下文构造、重试策略都会影响）
- **预算**：允许的最大步数、token、时间不同，分数不可比——「多跑几步」本身就是一种能力置换

因此读榜单时的正确姿势是：**先看这三项是否对齐，再看分数**。这也是「模型 + harness = Agent」在评测上的直接体现。

另一个常见混淆是**评分协议不同**：程序化验证（如测试通过率）与 LLM 评分是两种尺度，前者客观但只适用于可执行任务，后者覆盖面广但需要报告与人类的一致度（见 [Agent 评估指标](evaluation-metrics.md)）。

## 常见误区

- ❌ 混用成绩比较 harness：模型榜单、harness 榜单要分开看，SWE-bench 上「Claude Code 式系统」与「裸 API」不是一类参赛者
- ❌ 全信 pass@1：部分基准允许重试/多采样，确认协议再比较
- ❌ 忽略成本维度：同等成功率下 token 成本差 10 倍很常见，效率是第二指标

## 小练习

你的场景是「浏览器自动化处理内部审批流」。哪个基准的协议最值得借鉴？模仿它设计 20 个带程序化验证的任务。

## 相关资源

- [基准测试资源汇总](../13-resources/benchmarks/README.md)

## 相关知识点

- [基准测试总览](benchmarks.md)
- [编程 Agent](../12-applications/coding-agent.md)
