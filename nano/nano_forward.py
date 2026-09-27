# -*- coding: utf-8 -*-
"""第 22 章 第 2 页：前向传播 —— 形状链、中间量、以及未训练模型应当给出的 loss。

Run:  python nano_forward.py
"""
import math

import gptnano as G

G.utf8_out()
text = G.read_corpus()
tok = G.build_tokenizer(text)
ids = G.encode(text, tok)
V = tok["vocab_size"]
d, nh = G.CONFIG["d_model"], G.CONFIG["n_head"]
T, L, B = G.CONFIG["block_size"], G.CONFIG["n_layer"], G.CONFIG["batch_size"]
dh = d // nh


def show(s):
    return {"\n": "\\n", " ": "\\s"}.get(s, s)


print("配置: n_layer=%d n_head=%d d_model=%d d_ff=%d block_size=%d batch_size=%d vocab=%d" % (
    L, nh, d, G.CONFIG["d_ff"], T, B, V))
print("d_head = d_model / n_head = %d / %d = %d" % (d, nh, dh))
print()

xb, yb = G.fixed_batch(tok, text)
print("xb: %d 行 x %d 个输入 id" % (len(xb), len(xb[0])))
print("yb: %d 行 x %d 个目标 id" % (len(yb), len(yb[0])))
print("第 0 行输入 -> %r" % G.decode(xb[0], tok))
print("第 0 行目标 -> %r" % G.decode(yb[0], tok))
shift = sum(1 for r in range(B) for t in range(T - 1) if yb[r][t] == xb[r][t + 1])
print("行内右移核对 yb[r][t] == xb[r][t+1]: 命中 %d / %d" % (shift, B * (T - 1)))
print("  (每行剩下那 1 个目标是窗口外的下一个字符，所以输入看不到它)")
print()

p = G.init_params(V)
loss, st = G.forward(p, xb, yb)
blocks = st["blocks"]
N = B * T
print("形状链（每一行的宽度就是这个中间张量的行列数，读者可以对着代码数）")
SHAPE_W = 20
print("%s%d x %d   (B*T 个位置向量)" % (G.pad("嵌入相加后 h:", SHAPE_W), N, d))
for li, c in enumerate(blocks[:L]):
    print("%s%d x %d" % (G.pad("块 %d  LN1 输出 a:" % li, SHAPE_W), len(c["a"]), len(c["a"][0])))
    print("%s%d x %d   (q/k/v 各 %d 列并排)" % (
        G.pad("块 %d  qkv 线性输出:" % li, SHAPE_W), N, 3 * d, d))
    print("%s%d x %d" % (G.pad("块 %d  注意力后 ao:" % li, SHAPE_W), len(c["ao"]), len(c["ao"][0])))
    print("%s%d x %d" % (G.pad("块 %d  LN2 输出 b:" % li, SHAPE_W), len(c["b"]), len(c["b"][0])))
    print("%s%d x %d   -> gelu 后 g: %d x %d" % (
        G.pad("块 %d  fc1 输出 f1:" % li, SHAPE_W), len(c["f1"]), len(c["f1"][0]),
        len(c["g"]), len(c["g"][0])))
print("%s%d x %d" % (G.pad("终层 LN 输出 xn:", SHAPE_W), len(blocks[-1]["xn"]), len(blocks[-1]["xn"][0])))
print("%s%d x %d   (每个位置一个词表分布)" % (
    G.pad("logits:", SHAPE_W), len(st["logits"]), len(st["logits"][0])))
print("%s%d" % (G.pad("目标 target id 数:", SHAPE_W), len(st["targets"])))
print()

row = st["logits"][0]
pr = G.softmax(row)
print("位置 0 的 logits 前 6 项: %s" % " ".join("%.4f" % x for x in row[:6]))
print("位置 0 的 softmax 前 6 项: %s" % " ".join("%.6f" % x for x in pr[:6]))
print("该行概率和 = %.6f  (达标线 1.000000)" % sum(pr))
sums = [sum(G.softmax(lg)) for lg in st["logits"]]
print("%d 行的概率和: 最小 %.6f 最大 %.6f" % (len(sums), min(sums), max(sums)))
top = sorted(range(V), key=lambda i: -row[i])[:5]
print("未训练模型对位置 0 最看好的 5 个字符: %s" % " ".join(
    "%s(%.4f)" % (show(tok["itos"][i]), row[i]) for i in top))
print()

print("LayerNorm 之后每行应满足 mean=0, var=1（乘 gamma 加 beta 之前）：抽样 3 行")
for i in (0, 1, N - 1):
    hat, std = blocks[0]["ln1"][i]
    print("  行 %2d: mean(hat)=%+.9f  mean(hat^2)=%.6f  std=%.6f" % (
        i, sum(hat) / d, sum(x * x for x in hat) / d, std))
var0 = blocks[0]["ln1"][0][1] ** 2 - 1e-5
print("  行 0 的真实方差 %.3e，而 eps=1e-5 与它同量级 -> mean(hat^2)=%.6f 而不是 1" % (var0,
      sum(x * x for x in blocks[0]["ln1"][0][0]) / d))
print("  （这就是「小激活 + 固定 eps」为什么会让归一化打折扣：未训练时激活本来就极小）")
print()

print("因果掩码后的注意力权重（块 0 头 0；查询 t 只能看 0..t，所以行长 = t+1）")
for t in range(5):
    w = blocks[0]["attn"]["probs"][t][0]
    print("  查询 t=%d: %s | 行和 %.6f" % (t, " ".join("%.4f" % x for x in w), sum(w)))
print("缩放 1/sqrt(d_head) = 1/sqrt(%d) = %.9f" % (dh, blocks[0]["attn"]["scale"]))
print()

hd = blocks[0]["attn"]["heads"]
scale = blocks[0]["attn"]["scale"]
raw = sum(a * b for a, b in zip(hd[3][0][0], hd[0][1][0]))
print("可手算核对的一笔：位置 3 的 q(头 0) 与位置 0 的 k(头 0) 点积 = %.6f" % raw)
print("  乘缩放 %.9f -> %.6f；该查询位置 softmax 后对位置 0 的权重 = %.6f" % (
    scale, raw * scale, blocks[0]["attn"]["probs"][3][0][0]))
print("  位置 3 的行长 = %d（只覆盖 0..3），未来位置没有进入 softmax" % len(
    blocks[0]["attn"]["probs"][3][0]))
print()

lnV = math.log(V)
print("未训练 loss = %.6f nats/token" % loss)
print("均匀猜测   = ln V = %.6f" % lnV)
print("相对偏差   = %.4f%%  (达标线 2%%)" % (100.0 * abs(loss - lnV) / lnV))
print("困惑度 exp(loss) = %.4f   词表大小 = %d" % (math.exp(loss), V))
print()
print("（分模块参数账在 nano_budget.py：这一页只把形状链走到 logits，参数从哪儿来是第 3 页的账）")
