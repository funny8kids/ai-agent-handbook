---
tags: [llm, safety, advanced]
type: knowledge
status: published
updated: 2026-09-10
---

# RLHF、DPO 与对齐

> **一句话**：对齐（Alignment）让模型输出「有用、诚实、无害」；主流路线是用人类偏好数据做 RLHF 或它的简化版 DPO。

## 问题动机

预训练模型只会「续写」：给它一个问题，它可能继续编出更多问题，而不是回答。SFT 用示范数据教会了「指令跟随」的格式，但**没有告诉模型哪种回答更好**——同样遵循指令，有的回答更helpful、更诚实、更安全。偏好对齐要解决的正是这个「在多个都算合理的回答里偏向人类更认可的那一个」的问题，而人类能比较两个回答的优劣，却很难给绝对分数，所以训练信号天然是**成对偏好**。

## 核心机制

### 1. 奖励模型：把偏好学成一个打分器

偏好数据形如「对同一个问题 $$x$$，回答 $$y_w$$ 优于 $$y_l$$」（$$w$$=winner，$$l$$=loser）。假设存在一个潜在奖励 $$r^\*(x,y)$$，人类偏好由 Bradley–Terry 模型生成：

$$
P(y_w\succ y_l\mid x)=\sigma\big(r^\*(x,y_w)-r^\*(x,y_l)\big)
$$

其中 $$\sigma(z)=1/(1+e^{-z})$$。于是训练奖励模型 $$r_\phi$$ 就是最大化该似然的负对数：

$$
\mathcal{L}_R(\phi)=-\mathbb{E}_{(x,y_w,y_l)\sim\mathcal{D}}\Big[\log\sigma\big(r_\phi(x,y_w)-r_\phi(x,y_l)\big)\Big]
$$

注意：奖励模型学的是**相对偏好**，任意整体加常数不影响损失，所以它的绝对数值没有意义、只有差值有意义。

### 2. RLHF/PPO：用奖励信号优化策略

有了奖励模型，就可以把它当「代理评委」去优化生成策略 $$\pi_\theta$$。但只最大化奖励会出事：模型会找到奖励模型的漏洞，输出人类看不懂但打分极高的文本（reward hacking）。因此加一个 KL 惩罚，把策略拴在 SFT 参考模型 $$\pi_{ref}$$ 附近：

$$
\max_{\pi_\theta}\;\mathbb{E}_{x\sim\mathcal{D},\,y\sim\pi_\theta(\cdot\mid x)}
\Big[\,r_\phi(x,y)\;-\;\beta\,\mathbb{D}_{\mathrm{KL}}\big(\pi_\theta(y\mid x)\,\|\,\pi_{ref}(y\mid x)\big)\Big]
$$

- 第一项：奖励越高越好
- 第二项：$$\beta$$ 控制「偏离参考模型」的代价，防止跑飞；$$\beta$$ 越大越保守
- 用 PPO 求解这个带约束的目标，就是「RLHF 三步」的第三步

### 3. DPO：把两步合并成一步

DPO 的洞察是：上述带 KL 约束的最优解有闭式形式，可以反解出奖励与策略的关系，从而**跳过显式奖励模型和 RL**，直接在偏好对上做类似分类的训练：

$$
\mathcal{L}_{\mathrm{DPO}}(\pi_\theta;\pi_{ref})
=-\mathbb{E}_{(x,y_w,y_l)}\!\left[\log\sigma\!\left(
\beta\log\frac{\pi_\theta(y_w\mid x)}{\pi_{ref}(y_w\mid x)}
-\beta\log\frac{\pi_\theta(y_l\mid x)}{\pi_{ref}(y_l\mid x)}
\right)\right]
$$

直观看：它**提高**好回答相对参考模型的概率、**压低**坏回答的概率。$$\beta$$ 的作用与 RLHF 中一致——约束偏离幅度。DPO 只需一次监督式训练，不需要采样 rollout，因而更稳定、更省算力。

## 概念速查

| 概念 | 一句话 | 类比 |
|---|---|---|
| 奖励模型 | 学出「人类会给这个回答打几分」的代理评委 | 学会猜考官口味 |
| PPO | 用奖励信号微调策略的 RL 算法 | 按评委口味反复练习 |
| KL 约束 | 别偏参考模型太远，防止模型跑飞 | 改革要稳，不许翻天 |
| DPO | 把奖励模型和 RL 合并成一步分类式损失 | 直接从好/坏例子里学，免请评委 |
| GRPO | 去掉 value 网络、用组内相对优势的 PPO 变体 | 同题多答，内部排名定好坏 |

## 直觉解释

奖励模型像一位「学会了考官口味的助教」，PPO 是让学生按助教的打分反复练习，KL 约束则规定「不许为了讨好助教而彻底改掉原来的答题风格」。DPO 则更直接：不请助教，直接把「这份答卷比那份好」的成对例子喂给学生，让他照着调整。

## 工程含义

- **Agent 场景的新对齐面**：工具调用是否规范、何时该停下来问人、拒绝越权操作——这些都不是「文本好不好」，需要新的偏好数据与评估。
- **可验证奖励是 Agent 训练的关键杠杆**：代码是否通过测试、数学答案是否对，是客观、廉价、难被 hack 的奖励信号，比人类主观打分更适合 Agent 能力训练。
- **对齐税**：对齐过度会让模型变啰嗦、过度拒绝；工程上要在 helpfulness 与 safety 之间调权重，并用持续评估监控。

## 源码案例

- **InstructGPT**（[论文](https://arxiv.org/abs/2203.02155)）：RLHF 开山之作，1.3B 对齐后的模型在人类偏好测试中胜过 175B 未对齐模型——「对齐的价值超过规模」的最早实证
- **DeepSeek-R1**（[论文](https://arxiv.org/abs/2501.12948)）：把 RL 从「对齐工具」升级为「能力引擎」——用可验证奖励（数学答案对错、代码测试通过）做 RL，涌现出推理能力。对 Agent 的启示：**工具调用的成败本身就是可验证奖励**
- **trl 库**（[GitHub](https://github.com/huggingface/trl)）：Hugging Face 的 RLHF/DPO/GRPO 训练工具箱，想动手跑通 DPO 从这里开始

## 常见误区

- ❌ 对齐 = 内容审查：核心是「按人类意图行事」，包括听懂模糊指令、及时承认不确定
- ❌ DPO 全面取代 RLHF：偏好强度有连续差异、需要在线探索的场景 RLHF/PPO 仍占优；DeepSeek-R1 用的 GRPO 是 PPO 的变体
- ❌ 对齐是一次性工程：新能力（如工具调用）带来新对齐面，需要持续评估（→ [对齐与安全](../10-evaluation-safety/alignment-safety.md)）

## 参考资料

- [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)（Ouyang et al., 2022，InstructGPT）
- [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://arxiv.org/abs/2305.18290)（Rafailov et al., 2023，DPO）
- [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347)（Schulman et al., 2017，PPO）
- [DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](https://arxiv.org/abs/2402.03300)（GRPO 提出）
- [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948)

## 相关知识点

- [预训练、微调与指令微调](pretraining-finetuning.md)
- [对齐与安全](../10-evaluation-safety/alignment-safety.md)
