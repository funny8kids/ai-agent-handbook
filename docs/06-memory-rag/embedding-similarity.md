---
tags: [rag, basics]
type: knowledge
status: published
updated: 2026-09-10
---

# Embedding 与相似度检索

> **一句话**：Embedding 把文本变成语义空间中的向量，「找相似」就变成「算距离」——这是语义搜索、RAG、记忆检索的共同地基。

## 问题动机

关键词检索的盲区是「字面不同、意思相同」：「如何部署模型」和「模型怎么上线」一个词都不重合，倒排索引匹配不到。Embedding 把文本映射到向量空间，让语义相近的文本在空间里距离近，检索就从「匹配字符串」变成「找最近邻」。

## 核心机制

### 1. 三种相似度度量

给定两个向量 $$\mathbf{u},\mathbf{v}\in\mathbb{R}^d$$：

**余弦相似度**（最常用，只看方向、不看长度）：

$$
\cos(\mathbf{u},\mathbf{v})=\frac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{u}\|_2\,\|\mathbf{v}\|_2}
=\frac{\sum_{i=1}^{d}u_i v_i}{\sqrt{\sum_{i=1}^{d}u_i^2}\,\sqrt{\sum_{i=1}^{d}v_i^2}}
$$

**内积**（点积）：

$$
\mathbf{u}\cdot\mathbf{v}=\|\mathbf{u}\|_2\|\mathbf{v}\|_2\cos(\mathbf{u},\mathbf{v})
$$

**欧氏距离**：

$$
\|\mathbf{u}-\mathbf{v}\|_2^2=\|\mathbf{u}\|_2^2+\|\mathbf{v}\|_2^2-2\,\mathbf{u}\cdot\mathbf{v}
$$

三者的关系是工程选型的关键：当所有向量都做了 **L2 归一化**（$$\|\mathbf{u}\|_2=\|\mathbf{v}\|_2=1$$）时，余弦相似度等价于内积，欧氏距离随内积单调递减。因此向量库通常预先把向量归一化，然后用内积（MIPS）做检索——这也是为什么「归一化」在向量检索里是默认操作。

### 2. 为什么需要 ANN

精确最近邻要逐个算距离，$$N$$ 个向量、查询 $$Q$$ 次是 $$O(NQd)$$，亿级规模不可接受。近似最近邻（ANN）用索引把复杂度压到亚线性：

- **HNSW**：多层跳表式图，从稀疏顶层粗跳到稠密底层精找，通常用很小的召回损失换取数量级的速度提升
- **IVF**：先用聚类把空间划分成若干桶，查询时只扫最近的几个桶，以召回率换速度

### 3. 混合检索：为什么单靠向量不够

向量擅长语义，但**数字大小、型号、错误码、布尔条件**是它的盲区（「A100 和 H100 哪个贵」语义上几乎不可分）。因此生产标配是关键词检索 + 向量检索融合。关键词侧的事实标准是 BM25：

$$
\text{BM25}(q,d)=\sum_{t\in q}\text{IDF}(t)\cdot
\frac{f(t,d)\cdot(k_1+1)}{f(t,d)+k_1\Big(1-b+b\,\frac{|d|}{\mathrm{avgdl}}\Big)}
$$

其中 $$f(t,d)$$ 是词 $$t$$ 在文档 $$d$$ 中的频次，$$|d|$$ 是文档长度，$$\mathrm{avgdl}$$ 是平均文档长度，$$k_1,b$$ 是可调参数。IDF 抑制高频词的权重，长度归一化防止长文档占优。

两路结果融合最常用 **RRF（Reciprocal Rank Fusion）**，它只看排名、不看分数，因而无需对齐两路的分数量纲：

$$
\text{RRF}(d)=\sum_{r\in R}\frac{1}{k+\mathrm{rank}_r(d)}
$$

$$R$$ 是各路检索器，$$\mathrm{rank}_r(d)$$ 是文档 $$d$$ 在第 $$r$$ 路的排名，$$k$$ 通常取 60。

## 直觉解释

语义空间像一座「意思之城」：意思相近的文本住在同一个街区。「如何部署模型」和「模型怎么上线」措辞不同但住在隔壁；「模型部署」和「军队部署」字面像却相距十万八千里——余弦相似度一眼看穿。

## 最小示例

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-m3")   # 中文友好的开源模型
docs = ["MCP 是工具接入协议", "RAG 用检索增强生成", "向量库存语义向量"]
emb = model.encode(docs, normalize_embeddings=True)   # 归一化后内积=余弦
query = model.encode("什么是RAG", normalize_embeddings=True)
scores = emb @ query                          # 归一化向量的内积即余弦相似度
print(docs[int(np.argmax(scores))])           # → RAG 用检索增强生成
```

## 工程含义

- **召回质量取决于三件事**：切块策略、embedding 模型与检索融合方式。向量库本身不提供「正确性」。
- **「语义近」≠「答案对」**：向量检索找的是相关内容，精确匹配（型号、错误码）仍需关键词，所以混合检索是必须项。
- **选模型看三件事**：你的语言、你的领域、维度与成本预算；跨语言/长文档场景优先看 MTEB/C-MTEB 榜与模型卡上的训练目标（对称 vs 非对称检索）。

## 源码案例

- **FAISS**（[GitHub](https://github.com/facebookresearch/faiss)）：Meta 开源的向量检索库，几乎所有向量库的底层引擎之一——读它的 `IndexHNSW`/`IndexIVF` 文档能理解「为什么向量库能快」
- **BGE-M3**（[论文](https://arxiv.org/abs/2402.03216) / [模型](https://huggingface.co/BAAI/bge-m3)）：同时支持稠密、稀疏、多向量三种检索表示，中文场景常用——理解「一个模型出三路召回」的现代混合检索架构
- **Agent 场景的记忆检索**：Mem0（[GitHub](https://github.com/mem0ai/mem0)）把对话提炼成事实条目再向量化，检索时按用户/会话过滤——「先过滤后检索」的元数据设计比纯向量更准

## 常见误区

- ❌ 向量检索无所不能：数字比较、精确 ID、布尔条件是向量盲区，混合检索是必须
- ❌ 切块（chunk）随便切：切得太碎丢上下文、太粗稀释语义；按结构边界（标题/段落）切 + 保留标题路径是通行做法
- ❌ 只建索引不更新：文档改了索引没改 = 检索到旧知识，增量更新管线要从第一天设计
- ❌ 忘记归一化：混用「原始向量内积」和「余弦」会得到不同排序，工程上统一归一化 + 内积最省心

## 参考资料

- [Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks](https://arxiv.org/abs/1908.10084)（Reimers & Gurevych, 2019）
- [The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)（Robertson & Zaragoza, 2009）
- [Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods](https://dl.acm.org/doi/10.1145/1571941.1572114)（Cormack et al., SIGIR 2009）
- [BGE M3-Embedding](https://arxiv.org/abs/2402.03216)（Chen et al., 2024）

## 相关知识点

- [向量数据库](vector-database.md)
- [RAG 基础](rag-basics.md)
