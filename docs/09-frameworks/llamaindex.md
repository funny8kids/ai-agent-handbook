---
tags: [framework]
type: knowledge
status: published
updated: 2026-09-10
---

# LlamaIndex

> **一句话**：LlamaIndex（原 GPT Index）是「数据接入 + 检索」优先的框架：几十种数据连接器与索引结构，做 RAG 和知识型 Agent 的第一选择之一。

## 先看结论

- 核心价值：数据连接器（LlamaHub，数百种数据源）+ 丰富的索引结构（向量/树/关键词/知识图谱）+ 开箱即用的 Query Engine
- 与 LangChain 的分工：LangChain 偏「应用编排全家桶」，LlamaIndex 偏「RAG 管线专家」——生产中两者常混用
- Agent 能力：支持工具循环，但复杂多 Agent 编排仍建议用图编排框架
- 进阶组件值得精读：句窗检索、自动合并、混合检索、重排序集成

## 核心抽象

LlamaIndex 把 RAG 拆成一条**可替换的管线**，每个环节都有明确的抽象：

$$
\text{Reader}\to\text{Node Parser}\to\text{Index}\to\text{Retriever}\to\text{Query Engine}
$$

| 概念 | 作用 | 对应章节 |
|---|---|---|
| Reader / Loader | 从各数据源读文档 | [RAG 基础](../06-memory-rag/rag-basics.md) |
| Node Parser | 切块策略（句窗/层级/语义切块） | [Embedding 与相似度检索](../06-memory-rag/embedding-similarity.md) |
| Index | 组织 chunks 的结构（Vector/KG/Summary） | [向量数据库](../06-memory-rag/vector-database.md) |
| Retriever | 可插拔的检索策略 | [RAG 基础](../06-memory-rag/rag-basics.md) |
| Query Engine | 检索 + 组装 + 生成的封装 | 同上 |

**为什么这个拆分重要**：RAG 的质量瓶颈几乎从不在「向量库选哪个」，而在**切块与检索策略**。把 Node Parser 与 Retriever 做成独立可替换环节，就是为了让你能针对失败模式逐段换零件，而不是被锁死在一条固定管线上。

## 三个关键权衡

| 权衡 | 问题 | LlamaIndex 的解法 |
|---|---|---|
| 切太碎 vs 切太粗 | 碎则丢上下文，粗则稀释语义 | 句窗检索（匹配用句子、返回带窗口） |
| 检索粒度 vs 完整性 | 小块精确但缺上下文 | 自动合并父块（命中子块则返回父块） |
| 语义 vs 精确匹配 | 向量对 ID/型号无能 | 混合检索 + 重排序集成 |

## 最小 RAG（5 行）

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

index = VectorStoreIndex.from_documents(SimpleDirectoryReader("docs/").load_data())
print(index.as_query_engine(similarity_top_k=3).query("年假政策是什么？"))
```

## 源码案例

- **SentenceWindowNodeParser**（[文档](https://docs.llamaindex.ai/)）：检索时以「句」为单位匹配、返回时带上下文窗口——解决「切太碎丢上下文」的经典方案；配合 AutoMergingRetriever 自动合并父块。读这两个组件胜过读十篇 RAG 调优博客
- **LlamaHub**（[首页](https://llamahub.ai)）：数百个数据连接器与现成模板——找你的数据源（飞书/Notion/数据库/网盘）是否已有连接器，往往是选型第一站
- **LlamaCloud**：官方托管的解析/索引/检索服务——把「解析烂 PDF」这个 RAG 最大痛点产品化，可作为自建管线的质量基准

## 选型对比

| 维度 | LlamaIndex | LangChain | 裸代码 |
|---|---|---|---|
| 定位 | RAG 管线 | 通用集成/编排 | 完全自控 |
| 数据连接器 | 最丰富 | 丰富 | 自己写 |
| 高级检索组件 | 强（句窗/自动合并/重排） | 一般 | 自己实现 |
| Agent 编排 | 够用 | 一般 | 随意 |

**选型建议**：以「检索质量」为核心的项目优先 LlamaIndex；需要大量异构集成与复杂编排，LangChain/LangGraph 更合适；研究单点机制时读源码比用框架更有价值。

## 常见误区

- ❌ LlamaIndex 只能做 RAG：它的 Agent 与工作流能力在增强，但编排复杂度天花板低于图编排框架
- ❌ 默认切块就是最优：默认切块对结构化文档（合同/表格）常很差，先看 Node Parser 选项
- ❌ 评估缺失：框架集成了评估工具（→ [Agent 评估指标](../10-evaluation-safety/evaluation-metrics.md)），别裸奔上线
- ❌ 一上来就上复杂度：先用最简管线跑通并测量，再按失败模式换零件

## 小练习

用 LlamaIndex 对同一批 PDF 分别用默认切块和句窗切块建索引，构造 10 个测试问题对比检索命中率（Recall@3），说明差异来自哪一环节。

## 参考资料

- [LlamaIndex 官方文档](https://docs.llamaindex.ai/)
- [LlamaIndex GitHub](https://github.com/run-llama/llama_index)
- [RAG 原始论文](https://arxiv.org/abs/2005.11401)（Lewis et al., 2020）

## 相关知识点

- [RAG 基础](../06-memory-rag/rag-basics.md)
- [LangChain](langchain.md)
- [向量数据库](../06-memory-rag/vector-database.md)
