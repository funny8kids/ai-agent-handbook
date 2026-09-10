---
tags: [rag, engineering]
type: knowledge
status: published
updated: 2026-09-10
---

# 向量数据库

> **一句话**：向量数据库专门存 Embedding 并做近邻搜索（ANN），是 RAG 与 Agent 记忆的存储引擎；选型看规模、过滤需求与运维成本。
> **难度**：进阶
> **标签**：`#rag` `#engineering`

## 先看结论

- 核心能力：ANN 近似最近邻搜索（HNSW/IVF 等索引），毫秒级在亿级向量中找 Top-K
- 选型四问：数据量多大？要元数据过滤吗？已有 PG/ES 吗？谁运维？
- 亿级以下 + 已有 PostgreSQL → pgvector 起步最省事；别一开始就上重型分布式
- 向量库不提供「正确性」：召回质量取决于切块、embedding 模型与检索策略

## 选型对比

| 产品 | 类型 | 适合 | 一句话点评 |
|---|---|---|---|
| [pgvector](https://github.com/pgvector/pgvector) | PG 扩展 | <千万级、已有 PG | 事务+向量一体，运维零新增 |
| [Qdrant](https://github.com/qdrant/qdrant) | 专用 | Rust 系、过滤强 | 元数据过滤 + 混合检索体验好 |
| [Milvus](https://github.com/milvus-io/milvus) | 分布式 | 亿级、云原生 | 功能全，运维成本高 |
| [Chroma](https://github.com/chroma-core/chroma) | 轻量 | 原型、单机 | 十行代码起步 |
| [Weaviate](https://github.com/weaviate/weaviate) | 专用 | 混合检索 | 模块化 embedding 集成 |
| [FAISS](https://github.com/facebookresearch/faiss) | 库 | 嵌入自研 | 不是服务，是算法库 |

## 查询链路

```mermaid
flowchart LR
  A[查询] --> B[Embedding]
  B --> C[ANN 索引<br/>HNSW/IVF]
  C --> D[候选 Top-50]
  D --> E[元数据过滤<br/>权限/时间/租户]
  E --> F[Rerank 精排]
  F --> G[Top-5 给 LLM]
```

## 源码案例

- **HNSW 跳层导航**：想懂 ANN，读 Qdrant 或 FAISS 文档里的 HNSW 图解——多层跳表式图结构，从顶层粗跳到底层精找，用 1% 精度损失换百倍速度
- **pgvector 的索引选择**（[GitHub](https://github.com/pgvector/pgvector)）：`ivfflat` 建索引快、适合数据相对静止的场景，`hnsw` 查询快、适合高召回在线场景；读它的 README 就能理解两种索引的取舍
- **Qdrant 的过滤式检索**（[GitHub](https://github.com/qdrant/qdrant)）：把元数据过滤下推进 ANN 搜索内部（filterable HNSW），而不是「先取 Top-K 再过滤」——后者在强过滤条件下会召不回足够结果，多租户场景尤其致命

## 常见误区

- ❌ 向量库 = RAG：它只解决「检索」，切块、排序、生成、评估同样是工程大头
- ❌ 一上来上分布式：百万级向量 pgvector/Chroma 毫无压力，运维复杂度是隐性成本
- ❌ 忘记多租户隔离：检索过滤要含权限条件，否则 A 租户能召回 B 租户内容（安全漏洞）

## 小练习

50 万条客服 FAQ + 每日增量 + 按部门权限过滤——选哪个向量库？写出索引结构与查询语句骨架。

## 相关知识点

- [Embedding 与相似度检索](embedding-similarity.md)
- [RAG 基础](rag-basics.md)
