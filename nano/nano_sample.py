# -*- coding: utf-8 -*-
"""第 22 章 第 6 页：采样 —— 从训练好的权重里贪心和按分布抽样，各生成一段能读的文本。

达标线：不少于 4 段、每段生成长度 >= 200 字符、续写里至少 60% 的 3-gram 在语料中出现过、
贪心与温度 1.0 的续写必须不同。

Run:  python nano_sample.py      （需要 nano/weights_alice.json，由 nano_train.py 产出）
"""
import math
import os
import sys

import gptnano as G

G.utf8_out()
if not os.path.isfile(G.default_ckpt()):
    print("缺少检查点 nano/weights_alice.json，请先运行 python nano_train.py")
    sys.exit(1)

text = G.read_corpus()
tok = G.build_tokenizer(text)
p = G.load_params(G.default_ckpt())
V, T = tok["vocab_size"], G.CONFIG["block_size"]
N = 220
print("权重来源 nano/weights_alice.json   词表 %d   上下文窗口 %d   每段生成 %d 个字符" % (V, T, N))
print("每步都从头重算整段前向，故意不用 KV Cache：省下的正是第 7 页要算的那笔账")
print()

prompts = ["alice was beginning to get very", "the rabbit went straight on in",
           "there was nothing so very", "she was considering in her own"]
CUT = 60
segs = []
for kind, temp in (("贪心", 0.0), ("温度 1.0", 1.0)):
    for k, pr in enumerate(prompts):
        out = G.generate(p, tok, text, pr, N, temp, seed=7 + k)
        gen = out[len(pr):]
        hits, tot = G.char3gram_rate(gen, text)
        head, ht = G.char3gram_rate(gen[:CUT], text)
        tail, tt = G.char3gram_rate(gen[-CUT:], text)
        segs.append((kind, pr, gen, hits / tot, head / ht, tail / tt))
        print("[%s #%d] 提示 %r" % (kind, k + 1, pr))
        print("  生成 %d 字符: %s" % (len(gen), gen))
        head_rate, tail_rate = head / ht, tail / tt
        delta = 100.0 * (tail_rate - head_rate)
        if abs(delta) < 0.05:
            obs = "头尾持平，这一段没有漂移"
        elif delta < 0:
            obs = "越生成越离轨，尾段掉了 %.1f 个点" % (-delta)
        else:
            obs = "尾段反而更贴语料，多了 %.1f 个点" % delta
        print("  3-gram 命中语料 %d/%d = %.1f%%   头 %d 字符 %.1f%% -> 尾 %d 字符 %.1f%%（%s）" % (
            hits, tot, 100.0 * hits / tot, CUT, 100.0 * head_rate,
            CUT, 100.0 * tail_rate, obs))
        print()

MIN_SEGS, MIN_CHARS, MIN_GRAM = 4, 200, 0.60      # 冻在 spec.md 的采样那一行
ok_segs = len(segs) >= MIN_SEGS and all(len(s[2]) >= MIN_CHARS for s in segs)
ok_grams = all(s[3] >= MIN_GRAM for s in segs)
greedy = [s for s in segs if s[0] == "贪心"]
sampled = [s for s in segs if s[0] == "温度 1.0"]
diff = [i for i in range(len(greedy)) if greedy[i][2] != sampled[i][2]]
print("判定（达标线：≥%d 段、每段 ≥%d 字符、每段 3-gram ≥%.0f%%、贪心与温度 1.0 不同）:"
      % (MIN_SEGS, MIN_CHARS, 100 * MIN_GRAM))
print("  段数 %d   每段长度 %s -> %s" % (
    len(segs), " ".join(str(len(s[2])) for s in segs), "OK" if ok_segs else "MISS"))
print("  贪心最低 %.1f%%   温度 1.0 最低 %.1f%%   最差一段 %.1f%% -> %s" % (
    100.0 * min(s[3] for s in greedy), 100.0 * min(s[3] for s in sampled),
    100.0 * min(s[3] for s in segs), "OK" if ok_grams else "MISS"))
print("  贪心与温度 1.0 不同的段数 %d / %d -> %s" % (
    len(diff), len(greedy), "OK" if len(diff) == len(greedy) else "MISS"))
for i in diff:
    a, b = greedy[i][2], sampled[i][2]
    fork = next((j for j in range(min(len(a), len(b))) if a[j] != b[j]), None)
    print("    同提示 #%d 从第 %s 个字符开始分叉：贪心 %r  抽样 %r" % (
        i + 1, fork, a[fork:fork + 12] if fork is not None else "",
        b[fork:fork + 12] if fork is not None else ""))
print()

print("温度对分布做了什么（同一个位置，词表前 6 项概率）")
_, st0 = G.forward(p, [G.encode(prompts[0][:T], tok)], None)
last = st0["logits"][-1]
pr0 = G.softmax(last)
prt = G.softmax([x / 1.0 for x in last])
print("  贪心用的原始 softmax: %s" % " ".join("%.5f" % x for x in pr0[:6]))
print("  温度 1.0 之后:        %s（温度 1 是恒等，用来确认口径没写错）" % (
    " ".join("%.5f" % x for x in prt[:6])))
for temp in (0.5, 2.0):
    pt = G.softmax([x / temp for x in last])
    ent = -sum(w * math.log(w) for w in pt if w > 0)
    print("  温度 %s: 最大概率 %.5f  熵 %.4f nats（越高越敢换词，也越容易跑飞）" % (temp, max(pt), ent))
print("  贪心的最大概率 %.5f -> 温度越低，长文本越容易塌进重复循环" % max(pr0))
