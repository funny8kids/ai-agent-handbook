---
tags: [framework]
type: knowledge
status: published
updated: 2026-09-10
---

# LlamaIndex

> **一句话**：LlamaIndex（原 GPT Index）是「数据接入 + 检索」优先的框架：几十种数据连接器与索引结构，做 RAG 和知识型 Agent 的第一选择之一。
> **难度**：入门
> **标签**：`#framework` `#rag`

## 先看结论

- 核心价值：数据连接器（LlamaHub，数百种数据源）+ 丰富的索引结构（向量/树/关键词/知识图谱）+ 开箱即用的 Query Engine
- 与 LangChain 的分工：LangChain 是「应用编排全家桶」，LlamaIndex 是「RAG 管线专家」——生产中两者常混用
- Agent 能力：AgentWorkflow / FunctionAgent 支持工具循环，但复杂多 Agent 编排仍建议 LangGraph
- 进阶组件值得精读：句窗检索、自动合并、混合检索、重排序集成

## 核心概念速查

| 概念 | 作用 | 对应章节 |
|---|---|---|
| Reader / Loader | 从各数据源读文档 | [RAG 基础](../06-memory-rag/rag-basics.md) |
| Node Parser | 切块策略（句窗/层级/语义切块） | [Embedding 与相似度检索](../06-memory-rag/embedding-similarity.md) |
| Index | 组织 chunks 的结构（Vector/KG/Summary） | [向量数据库](../06-memory-rag/vector-database.md) |
| Query Engine | 检索 + 组装 + 生成的封装 | [RAG 基础](../06-memory-rag/rag-basics.md) |
| Retriever | 可插拔的检索策略 | 同上 |

## 最小 RAG（5 行）

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

index = VectorStoreIndex.from_documents(SimpleDirectoryReader("docs/").load_data())
print(index.as_query_engine(similarity_top_k=3).query("年假政策是什么？"))
```

## 源码案例

- **SentenceWindowNodeParser**（[文档](https://docs.llamaindex.ai/)）：检索时以「句」为单位匹配、返回时带上下文窗口——解决「切太碎丢上下文」的经典方案；配合 AutoMergingRetriever 自动合并父块。读这两个类的源码（各约百行）胜过读十篇 RAG 调优博客
- **LlamaHub**（[首页](https://llamahub.ai)）：数百个数据连接器与现成模板——找你的数据源（飞书/Notion/数据库/网盘）是否已有连接器，往往是选型第一站
- **LlamaCloud**：官方托管解析/索引/检索服务——「解析 PDF 质量」这个 RAG 最大痛点被产品化，可作为自建管线的质量基准

## 常见误区

- ❌ LlamaIndex 只能做 RAG：它的 Agent 与工作流能力在持续增强，但编排复杂度天花板低于 LangGraph
- ❌ 默认切块就是最优：默认 1024 token 切块对结构化文档（合同/表格）常常很差，先看 Node Parser 选项
- ❌ 评估缺失：LlamaIndex 集成了 Ragas 等评估（→ [Agent 评估指标](../10-evaluation-safety/evaluation-metrics.md)），别裸奔上线

## 小练习

用 LlamaIndex 对同一批 PDF 分别用默认切块和句窗切块建索引，构造 10 个测试问题对比检索命中率。

## 相关资源

- [LlamaIndex 文档](https://docs.llamaindex.ai/)
- [LlamaIndex GitHub](https://github.com/run-llama/llama_index)

## 相关知识点

- [RAG 基础](../06-memory-rag/rag-basics.md)
- [LangChain](langchain.md)
