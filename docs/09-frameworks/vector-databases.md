---
tags: [rag, framework]
type: resource
status: published
updated: 2026-09-10
---

# 🧰 向量数据库生态

> **一句话**：从嵌入式库到分布式集群，向量数据库生态已覆盖各种规模——原则是「从最小可用开始」，别为不存在的规模付复杂度。
> **难度**：⭐️ 入门
> **标签**：`#rag` `#engineering`

| 属性 | 内容 |
|---|---|
| 类型 | 基础设施生态 |
| 代表 | pgvector、Qdrant、Milvus、Chroma、Weaviate、FAISS |
| 标签 | `#rag` `#vector-db` |

## 🌟 生态地图

```mermaid
flowchart LR
  A["原型/单机<br/>Chroma · FAISS"] --> B["中小生产<br/>pgvector · Qdrant"]
  B --> C["亿级分布式<br/>Milvus · 云服务"]
  C -.性能敏感自研.-> D["算法库直嵌<br/>FAISS · usearch"]
```

## 选型决策树

| 你的情况 | 推荐 | 理由 |
|---|---|---|
| 原型、<10 万向量 | Chroma / FAISS | 零运维，五行代码 |
| 已有 PostgreSQL | pgvector | 事务/备份/权限全复用 |
| 需要强过滤 + 混合检索 | Qdrant / Weaviate | 元数据过滤与 RRF 成熟 |
| 亿级、多租户、云原生 | Milvus / 托管服务 | 分布式与弹性 |
| 嵌入自有引擎 | FAISS / usearch | 库不是服务，完全可控 |

## 📦 源码案例

- **pgvector 的 HNSW 索引**（[GitHub](https://github.com/pgvector/pgvector)）：`CREATE INDEX USING hnsw` 一行开启；读它的 README 了解 `ef_search` 精度-速度权衡——最常见的「够用且不倒」方案
- **Qdrant 的 payload 过滤**（[GitHub](https://github.com/qdrant/qdrant)）：过滤与向量检索联合优化（而非先过滤后检索的粗暴两步），多租户场景的性能关键
- **FAISS**（[GitHub](https://github.com/facebookresearch/faiss)）：工业向量检索的算法源头，IndexIVF/HNSW/PQ 的参考实现；向量数据库的底层多数致敬或直接使用它

## ⚠️ 常见误区

- ❌ 从 Milvus 集群起步：百万级以下单机方案绰绰有余，分布式运维是真实的持续成本
- ❌ 只测写入不测查询：召回质量（recall@k）与 P99 延迟才是 SLA，容量规划基于查询模式
- ❌ 忽略重排：向量库召回 Top-50 后接 Reranker 通常显著提升最终质量（→ [RAG 基础](../06-memory-rag/rag-basics.md)）

## 📚 相关知识点

- [向量数据库](../06-memory-rag/vector-database.md)
- [Embedding 与相似度检索](../06-memory-rag/embedding-similarity.md)
