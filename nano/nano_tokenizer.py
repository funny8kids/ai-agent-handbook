# -*- coding: utf-8 -*-
"""第 22 章 第 1 页：字符级分词器 —— 词表、编解码往返、以及它到底把什么交给了模型。

Run:  python nano_tokenizer.py     (标准库, 无依赖, 无网络)
"""
import json
import math
import os

import gptnano as G

G.utf8_out()
text = G.read_corpus()
tok = G.build_tokenizer(text)


def show(s):
    """Print a vocabulary character without letting whitespace disappear into the terminal."""
    return {"\n": "\\n", " ": "\\s"}.get(s, s)


print("语料 CONFIG.corpus_chars = %d  实际归一化后字符数 = %d" % (G.CONFIG["corpus_chars"], len(text)))
print("词表大小 V = %d   (= 语料去重字符数 %d)" % (tok["vocab_size"], len(set(text))))
print("词表(按码位排序): " + " ".join(show(c) for c in tok["vocab"]))
print("码位范围: %d … %d" % (ord(tok["vocab"][0]), ord(tok["vocab"][-1])))
print()

ids = G.encode(text, tok)
print("编码后 id 数 = %d   前 40 个 id: %s" % (len(ids), ids[:40]))
print("往返 decode(encode(x)) == x : %s" % (G.decode(ids, tok) == text))
print("id -> 字符 抽样: " + "  ".join("%d->%s" % (i, show(tok["itos"][i])) for i in (0, 1, 5, 11, 20, 35)))
print()

head = text[:52]
print("例句 %r" % head)
print("逐字符 id: %s" % G.encode(head, tok))
print("解码回来 %r" % G.decode(G.encode(head, tok), tok))
print()

# 词表里真正稀有的字符：它们决定了交叉熵的下界有多低
counts = {}
for c in text:
    counts[c] = counts.get(c, 0) + 1
rare = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]))[:5]
common = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
print("最高频 5 字符: " + "  ".join("%s:%d" % (show(c), n) for c, n in common))
print("最低频 5 字符: " + "  ".join("%s:%d" % (show(c), n) for c, n in rare))
print("只出现 1 次的字符数 = %d" % sum(1 for n in counts.values() if n == 1))
print()

print("一个长度为 %d 的窗口 = %d 个输入 id + %d 个预测目标" % (
    G.CONFIG["block_size"], G.CONFIG["block_size"], G.CONFIG["block_size"]))
print("每步喂给模型的预测数 = batch_size x block_size = %d" % (G.CONFIG["batch_size"] * G.CONFIG["block_size"]))
print("均匀猜测的 loss = ln V = %.6f  (nats/token)" % math.log(tok["vocab_size"]))

os.makedirs(G.OUT, exist_ok=True)
with open(os.path.join(G.OUT, "corpus.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
with open(os.path.join(G.OUT, "vocab.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"vocab": tok["vocab"], "stoi": tok["stoi"]}, f, ensure_ascii=False, sort_keys=True)
    f.write("\n")
print("产物: nano/out/corpus.txt (%d 字符), nano/out/vocab.json (%d 项)" % (len(text), tok["vocab_size"]))
