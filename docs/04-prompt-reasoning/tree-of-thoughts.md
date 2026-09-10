---
tags: [prompt, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# Tree of Thoughts

> **一句话**：ToT 把思考组织成树：每步生成多个候选思路，用评估函数打分后择优继续、失败回溯——像下棋的搜索树，而不是一条道走到黑。

## 问题动机

Chain of Thought 是单链的：一旦某一步想错，错误会沿着链条一路传播，且没有机制回头。对需要「搜索」的问题（24 点游戏、规划、谜题），人类会试着走几步、觉得不对就退回换一条路——ToT 把这种「分支 + 评估 + 回溯」形式化成对思维状态的搜索。

## 核心机制

ToT 把推理建模为在「思维状态」上的启发式搜索，四个组件：

**1. 思维分解**：把问题拆成中间状态 $s$，每一步是一个「想法」（thought），可解释、可评估。

**2. 想法生成器** $G$：从一个状态生成 $k$ 个候选：

$$
\{s^{(1)},\dots,s^{(k)}\}\sim G(p_\theta,\,s)
$$

采样（temperature > 0）产生多样性，或用「提出 3 个不同思路」的 prompt 让模型一次给出多个。

**3. 状态评估器** $V$：给候选状态打分：

$$
v_i=V(p_\theta,\,s^{(i)})\in[0,1]\quad\text{或}\quad v_i=\frac{\#\{\text{投"sure"的票}\}}{k}
$$

论文里用「值打分」（sure/likely/impossible）或「投票」两种方式；**评估质量是 ToT 的成败关键**——评估器不准则搜索被带偏。

**4. 搜索策略**：BFS 或 DFS，按分数剪枝：

$$
S_{t+1}=\operatorname*{Top\text{-}b}_{s\in\{G(p_\theta,s')\,:\,s'\in S_t\}} V(p_\theta,s)
$$

以宽度 $b$、深度 $d$ 的 BFS 为例，需要评估的节点数是 $O(b^d)$；而 CoT 是 $b=1$ 的退化情形（每步只走一个候选、不回溯）。这就是 ToT 用更多推理时计算（test-time compute）换更高成功率的本质。

$$
\underbrace{b=1}_{\text{CoT}}\;\longrightarrow\;\underbrace{b>1,\ \text{可回溯}}_{\text{ToT}}
$$

## 与 CoT 对比

| 维度 | CoT | ToT |
|---|---|---|
| 结构 | 单链 | 树（搜索空间） |
| 错误处理 | 错了就一路错下去 | 评估发现差 → 回溯换路 |
| 需要评估器 | 否 | 是（成败关键） |
| token 成本 | $1\times$ | 随 $b^d$ 增长（常见 5–20×） |
| 实现复杂度 | 一段 prompt | 需要调度程序 + 评估器 |

## 图示

```mermaid
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

## 核心实现

```python
def tot_solve(problem, depth=3, breadth=3, beam=2, threshold=0.4):
    states = [problem]
    for _ in range(depth):
        # 生成：每个状态扩展出 breadth 个候选
        candidates = [llm(f"{s}\n提出一个下一步，并给出可行性评分(0-1)")
                      for s in states for _ in range(breadth)]
        scored = sorted(candidates, key=lambda c: c.score, reverse=True)
        # 剪枝：只保留分数达标的 beam 个
        states = [c.text for c in scored[:beam] if c.score >= threshold]
        if not states:
            break
    return best(states)
```

> **注意**：必须限制宽度 $b$、深度 $d$ 与总预算，否则成本随 $b^d$ 爆炸。

## 源码案例

- **LangGraph 的分支-汇聚原语**（[langgraph](https://github.com/langchain-ai/langgraph)）：节点可扇出到多个分支并行生成，再汇聚打分选优——ToT 用图编排原语即可搭建，不必手写搜索循环
- **DeepSeek-R1 的「内化 ToT」**（[论文](https://arxiv.org/abs/2501.12948)）：推理模型的思考链里频繁出现「等一下，换个思路」（Aha moments）——RL 训练让模型在**一条序列内**完成尝试-评估-换路，效果接近显式 ToT 而成本远低。这是「买推理模型还是自己搭 ToT」的现实答案：多数场景前者更划算
- **论文官方实现**：[princeton-nlp/tree-of-thought-llm](https://github.com/princeton-nlp/tree-of-thought-llm) 开源了 24 点游戏等任务的完整搜索代码

## 常见误区

- ❌ ToT 适合一切任务：事实问答、抽取类任务毫无收益，只在「搜索空间大 + 可分步评估」的问题上发力
- ❌ 让模型自己打分就客观：自评存在系统性偏差（偏好自己的思路），必要时用独立模型评估或外部验证器（跑测试、对答案）
- ❌ 回溯无限次：必须限制 $b$、$d$ 与预算，否则成本爆炸
- ❌ 评估器随便写：评估器噪声大时，搜索反而比单链更差——它会把好路径剪掉

## 参考资料

- [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601)（Yao et al., 2023）
- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)（Wei et al., 2022）

## 相关知识点

- [Chain of Thought](chain-of-thought.md)
- [Graph of Thoughts](graph-of-thoughts.md)
