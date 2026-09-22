---
tags: [prompt, advanced]
type: knowledge
status: published
updated: 2026-09-23
---

# Tree of Thoughts

{% hint style="info" %}
**一句话**：ToT 把思考组织成树：每步生成多个候选思路，用评估函数打分后择优继续、失败回溯——像下棋的搜索树，而不是一条道走到黑。
{% endhint %}

## 问题动机

Chain of Thought 是单链的：一旦某一步想错，错误会沿着链条一路传播，且没有机制回头。对需要「搜索」的问题（24 点游戏、规划、谜题），人类会试着走几步、觉得不对就退回换一条路——ToT 把这种「分支 + 评估 + 回溯」形式化成对思维状态的搜索。

## 核心机制

ToT 把推理建模为在「思维状态」上的启发式搜索，四个组件：

**1. 思维分解**：把问题拆成中间状态 $$s$$，每一步是一个「想法」（thought），可解释、可评估。

**2. 想法生成器** $$G$$：从一个状态生成 $$k$$ 个候选：

$$
\{s^{(1)},\dots,s^{(k)}\}\sim G(p_\theta,\,s)
$$

采样（temperature > 0）产生多样性，或用「提出 3 个不同思路」的 prompt 让模型一次给出多个。

**3. 状态评估器** $$V$$：给候选状态打分：

$$
v_i=V(p_\theta,\,s^{(i)})\in[0,1]\quad\text{或}\quad v_i=\frac{\#\{\text{投"sure"的票}\}}{k}
$$

论文里用「值打分」（sure/likely/impossible）或「投票」两种方式；**评估质量是 ToT 的成败关键**——评估器不准则搜索被带偏。

**4. 搜索策略**：BFS 或 DFS，按分数剪枝：

$$
S_{t+1}=\operatorname*{Top\text{-}b}_{s\in\{G(p_\theta,s')\,:\,s'\in S_t\}} V(p_\theta,s)
$$

以宽度 $$b$$、深度 $$d$$ 的 BFS 为例，需要评估的节点数是 $$O(b^d)$$；而 CoT 是 $$b=1$$ 的退化情形（每步只走一个候选、不回溯）。这就是 ToT 用更多推理时计算（test-time compute）换更高成功率的本质。

$$
\underbrace{b=1}_{\text{CoT}}\;\longrightarrow\;\underbrace{b>1,\ \text{可回溯}}_{\text{ToT}}
$$

## 与 CoT 对比

| 维度 | CoT | ToT |
|---|---|---|
| 结构 | 单链 | 树（搜索空间） |
| 错误处理 | 错了就一路错下去 | 评估发现差 → 回溯换路 |
| 需要评估器 | 否 | 是（成败关键） |
| token 成本 | $$1\times$$ | 随 $$b^d$$ 增长（常见 5–20×） |
| 实现复杂度 | 一段 prompt | 需要调度程序 + 评估器 |

## 图示

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#E6F3F9","primaryBorderColor":"#0284C7","primaryTextColor":"#1F2937","secondaryColor":"#C7E4F3","tertiaryColor":"#F5FAFD","lineColor":"#74BBE0","actorBkg":"#EBF5FB","actorBorder":"#0284C7","actorTextColor":"#1F2937","signalColor":"#4EA9D8","noteBkgColor":"#D1E9F5","noteBorderColor":"#0284C7","noteTextColor":"#1F2937","labelBoxBkgColor":"#E6F3F9","labelBoxBorderColor":"#0284C7"}}}%%
flowchart TD
  A[问题] --> B[思路1]
  A --> C[思路2]
  A --> D[思路3]
  B --> E[评估: 7分 保留]
  C --> F[评估: 2分 剪枝]
  D --> G[评估: 6分 保留]
  E --> H[续展 → 得出解]
  G --> I[续展 → 死路, 回溯]
```

*《图：问题一次叉出三条思路各配评估分——2 分当场剪掉，7 分、6 分保留续展，但 6 分那条仍会走到死路再回溯，说明打分只是提前砍掉明显没救的支》*

## 核心实现

调度器的全部行为由五个参数决定：深度、每状态扩展宽度、保留宽度、及格线、以及生成提示本身。它们同时决定成本与「评估器噪声会不会致命」，所以值得先写成一份配置，再看它逐层怎么跑。

```json
{
  "tot_solve": {
    "depth": 3,
    "breadth": 3,
    "beam": 2,
    "threshold": 0.4,
    "init_states": ["problem"],
    "generator_prompt": "{state}\n提出一个下一步，并给出可行性评分(0-1)",
    "candidate_fields": ["text", "score"],
    "sort": "按 score 降序",
    "prune": "取前 beam 个，再丢弃 score < threshold 的",
    "empty_break": "某层剪完为空则提前结束搜索",
    "return": "best(states)"
  },
  "cost_model": {
    "candidates_per_layer": [3, 6, 6],
    "llm_calls_total": 15,
    "cot_equivalent_calls": 3,
    "ratio_vs_cot": 5,
    "layer3_without_pruning": 27
  }
}
```

`breadth=3` 是「每个状态问几次」，`beam=2` 是「每层留几个」，两者不是一回事——把它们混成一个参数是最常见的实现错误。生成与打分合并在同一次调用里（提示词末尾那句「给出可行性评分(0-1)」），这比先生成再单独打分省一半调用，代价是模型给自己的分更宽松（自评偏差见本页末尾）。

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#E6F3F9","primaryBorderColor":"#0284C7","primaryTextColor":"#1F2937","secondaryColor":"#C7E4F3","tertiaryColor":"#F5FAFD","lineColor":"#74BBE0","actorBkg":"#EBF5FB","actorBorder":"#0284C7","actorTextColor":"#1F2937","signalColor":"#4EA9D8","noteBkgColor":"#D1E9F5","noteBorderColor":"#0284C7","noteTextColor":"#1F2937","labelBoxBkgColor":"#E6F3F9","labelBoxBorderColor":"#0284C7"}}}%%
flowchart TD
  S0["第 0 层：1 个问题状态"] --> L1["第 1 层：生成 3 个候选"]
  L1 --> P1["打分排序，留 beam=2"]
  P1 --> L2["第 2 层：2 × 3 = 6 个候选"]
  L2 --> P2["打分排序，留 2"]
  P2 --> L3["第 3 层：2 × 3 = 6 个候选"]
  L3 --> P3["剪枝后取 best(states)"]
```

*《图：beam=2 把每层的存活状态钉在 2 个，15 次调用跑完 3 层；不剪枝时第 3 层要生成 27 个节点》*

按这份配置逐层推演，一次搜索的账目是这样的：

{% stepper %}
{% step %}
#### 第 1 步：只有问题本身，扩展出 3 个候选

`states` 初始是 `[problem]`，一个状态乘 `breadth=3` 得到 3 个候选，每个候选是一次模型调用。假设分数是 0.82、0.61、0.35。
{% endstep %}
{% step %}
#### 第 2 步：先按 beam 截断，再按 threshold 淘汰

降序排列后取前 `beam=2` 个，也就是 0.82 与 0.61；0.35 已经先被 beam 砍掉，`threshold=0.4` 这一轮没有额外作用。**注意顺序**：`scored[:beam]` 在前、过滤在后，所以一个 0.9 与一个 0.2 混在前两名时，0.2 依然会被留下——只要它进了前 2。想要「宁可少留」就得先把 `threshold` 放在截断之前。
{% endstep %}
{% step %}
#### 第 3 步：第 2、3 层各 6 个候选，调用数停在 15

每层存活 2 个状态，于是第 2 层与第 3 层各生成 $$2\times3=6$$ 个候选。总调用 $$3+6+6=15$$，而同样深度（3 步）的 CoT 只需 3 次——**5 倍成本**，正好落在对比表里「常见 5–20×」的下沿。把 `beam` 提到 3（等于不剪枝），账目立刻变成 $$3+9+27=39$$，即 13 倍，且指数项在最后一层最贵。
{% endstep %}
{% step %}
#### 第 4 步：某一层剪空了，搜索就地结束

若某一层的 `beam` 内最高分只有 0.3，低于 `threshold=0.4`，过滤后 `states` 为空，循环 `break`。返回的是**空集上的** `best(states)`——这是一个容易写错的地方：`states` 已被赋值成空列表，上一层的 0.82 / 0.61 那条活路已经不在手里了。正确做法是维护一个 `best_so_far` 变量，与「当前层存活集合」分开保存。
{% endstep %}
{% step %}
#### 第 5 步：深度与宽度都会回头咬评估器

3 层是「问题拆成 3 个中间状态」的结果，不是调参调出来的：拆得越细，评估器有更多机会在早层砍掉正确答案。评估器噪声大时，`beam=2` 的容错只有 1 条——第 4 步那类「整层为空」的概率随之上升。要么用外部验证器给分（跑测试、对答案），要么把 `beam` 提到 3 换回一条活路，代价按上面第 3 步的账算。
{% endstep %}
{% endstepper %}

`beam` 是这里唯一同时拧动成本与鲁棒性的旋钮（点标签切换）：

{% tabs %}
{% tab title="beam=1：贪心，省但脆" %}
每层只留最高分，调用数降到 $$3+3+3=9$$（约为 CoT 的 3 倍）。省下来的预算是真的，风险也是真的：评估器一次看走眼就永久丢失那条分支，回溯机制形同虚设——这是「花了 ToT 的钱、只买到 CoT 的结构」。适合评估器有外部验证器托底、且单层候选确实可比的情况。
{% endtab %}

{% tab title="beam=2：默认折中" %}
15 次调用，5 倍 CoT。留一条备用分支的意义不在「平均更好」，而在**第 4 步那种整层为空的死局能被另一条撑住**。绝大多数「能分步评估、但评估器只是模型自评」的任务，起点应该放在这里。
{% endtab %}

{% tab title="beam=breadth=3：不剪枝" %}
每层存活 3 个，调用 $$3+9+27=39$$，13 倍成本，剪枝退化成纯排序。此时 ToT 的收益主要来自「多路采样 + 最后挑最好」，与 self-consistency 的差别只剩下前缀复用。既然 $$b^d$$ 已经兑现，就不必再宣称自己在做搜索。
{% endtab %}

{% tab title="threshold 抬到 0.6：搜索变窄也更容易空" %}
第 1 层的 0.61 被挡在门外，只剩 0.82 一条——实际退化成 `beam=1`。同时「整层为空」的触发概率上升，第 4 步那个空集陷阱更容易被踩到。抬高及格线只在评估器非常准（有外部验证器）时才划算，否则等于用更高的假阴性率换干净-looking 的树。
{% endtab %}
{% endtabs %}

{% hint style="warning" %}
**注意**：必须限制宽度 $$b$$、深度 $$d$$ 与总预算，否则成本随 $$b^d$$ 爆炸。
{% endhint %}

## 这笔搜索预算花得值不值

ToT 的合理性与否是一道不等式，不是信仰问题。设单条 CoT 的成本为 $$c$$、成功率为 $$p_1$$；ToT 成本约 $$c\cdot b\cdot d$$、成功率为 $$p_T$$：

$$
p_T - p_1 \;>\; \lambda\, c\,(b d - 1)
$$

$$\lambda$$ 是把 token 成本折成「任务失败损失」的换算系数。三条实用判据：

| 判据 | 满足才值得搜 | 不满足时 |
|---|---|---|
| 可分步评估 | 有能提前判断「这步靠谱吗」的信号 | 只能到终点才知道，搜索近似随机漫步 |
| 有外部验证器 | 跑测试、算答案、查约束 | 只能自评，噪声会剪掉好路 |
| 失败很贵 | 重试成本远高于 $$b d$$ 倍 token | 直接 $$n$$ 次独立采样取最优（self-consistency）更省 |

第三行最常被忽略：**「多跑几次挑最好」往往已经吃到 ToT 的大部分收益**。差别在于 ToT 会在中途剪枝、复用前缀，适合深度大、每步昂贵的任务。

## 源码案例

- **LangGraph 的分支-汇聚原语**（[langgraph](https://github.com/langchain-ai/langgraph)）：节点可扇出到多个分支并行生成，再汇聚打分选优——ToT 用图编排原语即可搭建，不必手写搜索循环
- **DeepSeek-R1 的「内化 ToT」**（[论文](https://arxiv.org/abs/2501.12948)）：推理模型的思考链里频繁出现「等一下，换个思路」（Aha moments）——RL 训练让模型在**一条序列内**完成尝试-评估-换路，效果接近显式 ToT 而成本远低。这是「买推理模型还是自己搭 ToT」的现实答案：多数场景前者更划算
- **论文官方实现**：[princeton-nlp/tree-of-thought-llm](https://github.com/princeton-nlp/tree-of-thought-llm) 开源了 24 点游戏等任务的完整搜索代码

## 常见误区

- ❌ ToT 适合一切任务：事实问答、抽取类任务毫无收益，只在「搜索空间大 + 可分步评估」的问题上发力
- ❌ 让模型自己打分就客观：自评存在系统性偏差（偏好自己的思路），必要时用独立模型评估或外部验证器（跑测试、对答案）
- ❌ 回溯无限次：必须限制 $$b$$、$$d$$ 与预算，否则成本爆炸
- ❌ 评估器随便写：评估器噪声大时，搜索反而比单链更差——它会把好路径剪掉

## 小练习

拿一个你手边真实的多步任务（例如「把这张表里金额对不上的行找出来」），先只写评估器：给定一个中间状态，你能不能用一段代码而不是模型判断「这步有希望」？写不出来，就别上 ToT——改用一次 CoT 加人工复核。

## 参考资料

- [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601)（Yao et al., 2023）
- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)（Wei et al., 2022）
- [ToT 官方实现（princeton-nlp）](https://github.com/princeton-nlp/tree-of-thought-llm)

## 相关知识点

- [Chain of Thought](chain-of-thought.md)
- [Graph of Thoughts](graph-of-thoughts.md)
- [推理预算与测试期计算](test-time-compute-reasoning-budget.md)

