# -*- coding: utf-8 -*-
"""Lab 2 手写迷你 RAG：切块 -> BM25 检索 -> 带引用的回答。

不装任何向量库、不调任何 API——用最朴素的 BM25 把「检索增强」的
骨架走一遍，你会看清所有框架帮你藏起来的三件事：切块、打分、拼 prompt。

运行：python lab2_rag.py
"""
import math
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")  # 防 Windows 控制台 GBK 乱码

# ---------- 1) 知识库与切块 ----------

CORPUS = {
    "kv-cache": "KV 缓存把历史 token 的 key/value 存下来复用，避免每轮重算整个前缀。它占显存，且随上下文长度线性增长。",
    "context-window": "上下文窗口是模型单次能看到的 token 上限。窗口大不代表记得好：中段信息容易被忽略，即所谓 lost in the middle。",
    "rag": "RAG 把外部知识检索后拼进 prompt，让模型「开卷考试」。它更新知识不用重训模型，代价是检索质量决定上限。",
    "embedding": "Embedding 把文本映射成向量，语义相近则向量距离近。适合召回阶段粗筛，但精确关键词匹配有时反而不如 BM25。",
    "bm25": "BM25 是经典的关键词打分函数：词频越高得分越高，但设饱和上限；文档越长惩罚越大；稀有词权重更高（IDF）。",
    "chunking": "切块策略决定 RAG 的检索粒度：块太大引入噪声，太小丢上下文。常见做法是按标题/句子边界切，并保留重叠窗口。",
    "rerank": "重排（rerank）在粗召回之后，用更强的交叉编码器对 top 候选重新打分，只处理少量候选所以负担得起。",
    "memory": "Agent 的长期记忆通常落在向量库或数据库里，靠检索注入上下文；模型本身没有参数化的持久记忆。",
}

def tokenize(text: str):
    """中文按 2-gram + 英文按单词，够玩具但真实存在这类方案（jieba 是正式版）。"""
    en = re.findall(r"[a-zA-Z]+", text.lower())
    zh = re.sub(r"[^\u4e00-\u9fff]", "", text)
    bigrams = [zh[i:i + 2] for i in range(len(zh) - 1)]
    return en + bigrams

def chunk(doc_id: str, text: str, size: int = 40):
    """按字符数粗切块并保留 10 字重叠——演示 overlap 的作用。"""
    chunks, start = [], 0
    while start < len(text):
        chunks.append((f"{doc_id}#{len(chunks)}", text[start:start + size]))
        start += size - 10
    return chunks

INDEX = []  # [(chunk_id, tokens)]
for did, txt in CORPUS.items():
    for cid, piece in chunk(did, txt):
        INDEX.append((cid, tokenize(piece)))

# ---------- 2) BM25 打分（就是公式本身，没有魔法） ----------

def bm25(query_tokens, k1=1.5, b=0.75):
    N = len(INDEX)
    avg_len = sum(len(t) for _, t in INDEX) / N
    df = {}
    for _, toks in INDEX:
        for w in set(toks):
            df[w] = df.get(w, 0) + 1
    scores = []
    for cid, toks in INDEX:
        s, L = 0.0, len(toks)
        for w in query_tokens:
            if w not in df:
                continue
            tf = toks.count(w)
            idf = math.log(1 + (N - df[w] + 0.5) / (df[w] + 0.5))
            s += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * L / avg_len))
        scores.append((s, cid))
    return sorted(scores, reverse=True)

# ---------- 3) 拼 prompt + "生成"回答 ----------

def answer(question: str, top_k: int = 3, budget: int = 160):
    hits = bm25(tokenize(question))[:top_k]
    context, used = [], 0
    for score, cid in hits:
        if score <= 0:
            break
        doc_id = cid.split("#")[0]
        text = CORPUS[doc_id]               # 演示用：整篇注入；真实系统注入的是切好的块
        if used + len(text) > budget:      # 上下文预算：塞不下就停，这就是工程
            print(f"  [预算不足，丢弃] {cid} (score={score:.2f})")
            continue
        context.append((cid, score, text))
        used += len(text)

    print(f"\n--- 检索结果（预算 {used}/{budget} 字）---")
    for cid, score, text in context:
        print(f"  {score:6.2f}  {cid:12s} {text[:38]}…")

    # MockLLM：真实系统里这里是一次模型调用；我们按「只准引用检索到的块」作答
    lines = [f"  答：根据 {cid.split('#')[0]}：{text}" for cid, _, text in context]
    print("\n--- 带引用的回答 ---")
    for ln in lines:
        print(ln)
    return context

if __name__ == "__main__":
    print("=" * 62)
    print("Lab 2：手写迷你 RAG（BM25 检索 + 引用式回答 + 上下文预算）")
    print("=" * 62)
    q = "KV 缓存和上下文窗口有什么关系？窗口大是不是就不用 RAG 了？"
    print(f"\n问题: {q}")
    answer(q)
    print("\n" + "-" * 62)
    q2 = "切块太大或太小会怎样？"
    print(f"问题: {q2}")
    answer(q2)
