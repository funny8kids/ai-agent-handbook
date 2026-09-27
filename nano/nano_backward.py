# -*- coding: utf-8 -*-
"""第 22 章 第 4 页：反向传播的验收 —— 梯度检查，和「故意算错一项」的对照变异。

达标线：抽样参数不少于 12 个，解析梯度的最大相对误差不超过 1e-3；
而故意少算一项的变异必须把最大相对误差推到 1e-1 以上——一条永远不出红的检查等于什么都没检查。

Run:  python nano_backward.py
"""

import gptnano as G

G.utf8_out()
BIG = 0.5          # 用来试探「挪一大步 loss 动不动」的幅度，与差分步长 1e-4 无关
text = G.read_corpus()
tok = G.build_tokenizer(text)
V = tok["vocab_size"]
d, T = G.CONFIG["d_model"], G.CONFIG["block_size"]

p = G.init_params(V)
xb, yb = G.fixed_batch(tok, text)
B = len(xb)
loss0, st = G.forward(p, xb, yb)
print("核对用的批: %d 行 x %d，loss = %.6f" % (B, T, loss0))
print("抽样策略: 每个参数数组取 1 个叶子（%d 个数组 -> %d 个样本），嵌入行取批内出现过的 id" % (
    len(G.sample_params(p, xb)), len(G.sample_params(p, xb))))
print()

mx, rows = G.gradcheck(p, xb, yb)
print("%s %s %s %s" % (G.pad("参数", 26), G.pad("解析梯度", 15), G.pad("数值梯度", 15), "相对误差"))
for label, a, num, rel in rows:
    print("%-26s %+14.6e %+14.6e %10.2e" % (label, a, num, rel))
print()
print("样本数 = %d   最大相对误差 = %.3e   达标线 1e-3 -> %s" % (
    len(rows), mx, "OK" if mx <= 1e-3 else "MISS"))
print("数值梯度两侧都非零的样本 = %d / %d" % (
    sum(1 for _, a, n_, _ in rows if abs(a) > 1e-15 or abs(n_) > 1e-15), len(rows)))
print("检查完 loss 复原 = %.6f（与原值差 %.1e，证明扰动没有留在参数里）" % (
    G.forward(p, xb, yb)[0], abs(G.forward(p, xb, yb)[0] - loss0)))
print()

print("对照变异：故意把一整项梯度置零")
for drop in ("attention", "fc2", "lm_head"):
    dmx, drows = G.gradcheck(p, xb, yb, drop=drop)
    nz = sum(1 for _, a, n_, _ in drows if abs(a) > 1e-15 or abs(n_) > 1e-15)
    top = sorted(drows, key=lambda r: -r[3])[:3]
    print("  drop=%-10s 最大相对误差 %.3e  达标线 1e-1 -> %s  非零样本 %d/%d" % (
        drop, dmx, "OK" if dmx >= 1e-1 else "MISS", nz, len(drows)))
    for label, a, num, rel in top:
        print("      首当其冲 %-20s 解析 %+.4e 数值 %+.4e 相对误差 %.2e" % (label, a, num, rel))
print()

zero_rows = [(label, a, num, rel) for label, a, num, rel in rows
             if abs(a) < 1e-18 and abs(num) < 1e-18]
print("两侧都恰好为 0 的样本（%d 个）: %s" % (len(zero_rows), ", ".join(r[0] for r in zero_rows)))
print("这不是漏检，而是模型的真实性质。把 qkv 偏置的三段各挪 %g，看 loss 动多少:" % BIG)
base = G.forward(p, xb, yb)[0]
qkv_b = G.get_path(p, ("b0", "qkv_b"))
for name, off in (("q 段", 0), ("k 段", d), ("v 段", 2 * d)):
    orig = qkv_b[off]
    G.set_leaf(p, ("b0", "qkv_b"), off, None, orig + BIG)
    moved = G.forward(p, xb, yb)[0]
    G.set_leaf(p, ("b0", "qkv_b"), off, None, orig)
    print("  %s: loss %.12f -> %.12f（差 %+.3e）" % (name, base, moved, moved - base))
print("  给每个位置的 k 加同一个向量，等于给每个查询位置的整行打分加同一个常数，")
print("  而 softmax 对「整行加常数」不变 -> k 段偏置在数学上不可辨识，梯度恒为 0。")
print("  q 段加的是 q+b 再点乘 k_j，随 j 变化所以有效；v 段直接加到输出上加权求和后仍在，也有效。")
print("  反过来看这条检查为什么可信：数值侧是独立用差分算出来的，它一样看到了这个不变性。")
print("复原核对: loss = %.12f（与扰动前差 %.1e）" % (G.forward(p, xb, yb)[0],
                                                abs(G.forward(p, xb, yb)[0] - base)))
