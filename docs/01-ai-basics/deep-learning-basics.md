---
tags: [basics, beginner]
type: knowledge
status: published
updated: 2026-09-10
---

# 深度学习基础

> **一句话**：深度学习用多层神经网络自动学习特征表示——层越深，能表达的概念越抽象。

## 先看结论

- 神经网络 = 矩阵乘法 + 非线性激活，堆很多层
- 「深度」的意义：自动学特征，替代人工特征工程
- 训练靠反向传播 + 梯度下降；推理靠前向计算
- 算力（GPU）+ 数据 + 算法三者齐备，才有 2012 年后的深度学习复兴
- LLM 本质是「超大的 Transformer 深度网络」，详见 [Transformer 与 Attention](../03-llm/transformer-attention.md)

## 核心机制

### 1. 一个神经元在算什么

单个神经元做的是「加权求和 + 激活」：

$$
z=\sigma\!\Big(\sum_{i=1}^{n} w_i x_i+b\Big)=\sigma(\mathbf{w}^\top\mathbf{x}+b)
$$

$$\mathbf{w}$$ 是权重（每个输入的重要程度），$$b$$ 是偏置，$$\sigma$$ 是**非线性**激活函数，常见的有：

$$
\mathrm{ReLU}(z)=\max(0,z),\qquad
\sigma(z)=\frac{1}{1+e^{-z}},\qquad
\tanh(z)=\frac{e^{z}-e^{-z}}{e^{z}+e^{-z}}
$$

**为什么必须有非线性**：若没有 $$\sigma$$，多层线性变换的复合仍是线性变换——一百层等价于一层。非线性是「深度」产生表达力的前提。

### 2. 一层在算什么，为什么叫「表示学习」

把一层写成矩阵形式：$$\mathbf{h}=\sigma(W\mathbf{x}+\mathbf{b})$$，其中 $$W$$ 的每一行是一个神经元。深层堆叠：

$$
\mathbf{h}^{(l)}=\sigma\big(W^{(l)}\mathbf{h}^{(l-1)}+\mathbf{b}^{(l)}\big)
$$

每一层把上一层的表示重新组合成更抽象的特征。识别猫的例子最直观：浅层学「边缘/色块」，中层组合出「耳朵、胡须」，深层形成「猫脸」的抽象。**人不需要告诉它看哪里**——这正是「表示学习」相对传统人工特征工程的根本优势。

### 3. 训练：反向传播就是链式法则

训练要回答「每个参数该往哪个方向调、调多少」，即求损失对参数的梯度。反向传播（backpropagation）本质是微积分的**链式法则**在计算图上的高效应用。对第 $$l$$ 层权重：

$$
\frac{\partial \mathcal{L}}{\partial W^{(l)}}
=\underbrace{\delta^{(l)}}_{\text{本层误差信号}}\,
\big(\mathbf{h}^{(l-1)}\big)^{\top},
\qquad
\delta^{(l)}=\big(W^{(l+1)\top}\delta^{(l+1)}\big)\odot\sigma'\!\big(\mathbf{z}^{(l)}\big)
$$

$$\odot$$ 是逐元素乘积，$$\sigma'$$ 是激活函数的导数。含义是：**误差从输出层逐层往回传，每层用「上层误差」和「本层激活的斜率」算出自己的调整量**，再交给梯度下降更新。这解释了为什么很长一段时间网络训不起来——层数多时 $$\delta$$ 会连乘衰减（梯度消失）；残差连接（$$y=x+F(x)$$，让梯度有直通通路）与 LayerNorm 正是为此发明的。

### 4. 规模化：MoE 与稀疏激活

现代大模型不再「每个 token 都用全部参数」，而是采用**混合专家（MoE）**：把前馈层拆成多个专家，每个 token 只激活其中少数几个：

$$
\mathbf{y}=\sum_{i\in\operatorname{TopK}(\mathbf{g})} g_i\, E_i(\mathbf{x}),
\qquad
\mathbf{g}=\mathrm{softmax}(W_r\mathbf{x})
$$

$$E_i$$ 是第 $$i$$ 个专家网络，$$g_i$$ 是门控权重，TopK 只取权重最大的几个。效果是**参数量（容量）与计算量解耦**：总参数很大，但每个 token 的实际计算量只与激活的专家数成正比。这就是 [DeepSeek-V3](https://arxiv.org/abs/2412.19437) 等在成本上取得优势的结构基础。

## 图示

```mermaid
flowchart LR
  A[输入层<br/>原始数据] --> B[隐藏层 1<br/>学边缘/字符]
  B --> C[隐藏层 2<br/>学局部模式]
  C --> D[隐藏层 N<br/>学抽象概念]
  D --> E[输出层<br/>预测结果]
```

## 核心概念速查

| 概念 | 一句话 | 类比 |
|---|---|---|
| 神经元 | 加权求和 + 激活函数 | 一次「投票 + 门槛」 |
| 激活函数 | 引入非线性，否则再深也只是一层 | 让曲线能拐弯 |
| 反向传播 | 从误差反推每个参数该怎么调 | 考试后逐题复盘归因 |
| 参数量 | 模型里可学习的旋钮个数 | GPT-3 有 1750 亿个旋钮 |
| 残差连接 | 让信息/梯度有直通通路 | 高速公路，缓解梯度消失 |
| MoE 混合专家 | 每次只激活部分参数，容量大、计算省 | 大医院分诊：只挂相关科室 |

## 源码案例

- **DeepSeek-V3**（[论文](https://arxiv.org/abs/2412.19437)）：6710 亿参数的 MoE 模型，每个 token 只激活约 370 亿；配套开源了 FP8 混合精度训练细节，用工程手段把训练成本压到同级别模型的几分之一。读它的技术报告能直观看到「深度学习 = 算法 + 系统工程」
- **llama.cpp**（[GitHub](https://github.com/ggml-org/llama.cpp)）：纯 C/C++ 实现的推理引擎，在笔记本上跑 LLM。想理解「前向计算到底在算什么」，读它的 matmul kernel 比读论文更直接

## 常见误区

- ❌ 神经网络模拟了大脑：只是松散的数学启发，别按脑科学理解
- ❌ 参数越多越聪明：数据质量、训练方法（见 [预训练、微调与指令微调](../03-llm/pretraining-finetuning.md)）同样关键；MoE 也说明「总参数」与「每次计算量」是两回事
- ❌ 深度学习是黑箱所以不能用于严肃场景：可解释性研究（见 [可解释性](../10-evaluation-safety/explainability.md)）与评估体系正在补这一课
- ❌ 加深网络就能变强：没有残差连接与归一化，深层网络反而更难训练

## 小练习

为什么「没有非线性激活函数的一百层网络」等价于「一层的线性网络」？用矩阵复合说明。

## 参考资料

- [Deep Learning](https://www.deeplearningbook.org/)（Goodfellow, Bengio & Courville, 2016）
- [Learning representations by back-propagating errors](https://www.nature.com/articles/323533a0)（Rumelhart, Hinton & Williams, 1986）
- [Deep Residual Learning for Image Recognition](https://arxiv.org/abs/1512.03385)（He et al., 2015，ResNet）
- [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437)（MoE 与 FP8 训练）

## 相关知识点

- [机器学习基础](machine-learning-basics.md)
- [Transformer 与 Attention](../03-llm/transformer-attention.md)
