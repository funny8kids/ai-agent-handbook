# -*- coding: utf-8 -*-
"""第 22 章 第 3 页：把账算到能验算 —— 参数量、每步乘加数、激活显存、解码期 KV Cache。

stdout 只打机器无关的账（数量、形状、公式代入结果）；所有墙钟时间走 stderr，
因为「这台机器跑多少秒」不能进入逐字节比对 reproducibility 的那份记录。

Run:  python nano_budget.py
"""
import time

import gptnano as G

G.utf8_out()
text = G.read_corpus()
tok = G.build_tokenizer(text)
V = tok["vocab_size"]
d, nh, T = G.CONFIG["d_model"], G.CONFIG["n_head"], G.CONFIG["block_size"]
df, L, B, S = G.CONFIG["d_ff"], G.CONFIG["n_layer"], G.CONFIG["batch_size"], G.CONFIG["train_steps"]

print("冻结配置（全章同一份）: L=%d H=%d d=%d d_ff=%d T=%d B=%d steps=%d V=%d" % (
    L, nh, d, df, T, B, S, V))
print("边界: n_layer<=%d d_model<=%d block_size<=%d train_steps<=%d，预算 %.0f 秒" % (
    G.BOUNDS["n_layer"], G.BOUNDS["d_model"], G.BOUNDS["block_size"],
    G.BOUNDS["train_steps"], G.BUDGET_S))
print()

p = G.init_params(V)
params = G.count_params(p)
print("分模块参数账（count 列只由维度名算出来，不是把张量再走一遍）")
module_sum = 0
for label, formula, n in G.param_breakdown(p):
    print("  %s%s%d" % (G.pad(label, 18), G.pad(formula, 30), n))
    module_sum += n
print("  求和 %d  vs  实测 count_params %d  差 %d（达标线要求 0）" % (module_sum, params, module_sum - params))
print("数值量按 %d 字节/个（float64）；文本格式的真实代价在第 7 页量" % 8)
print("每 token 前向乘加数 MAC = (每层线性) x L + 2 T d x L + d V，每层线性 = 4 d^2 + 2 d d_ff")
per_layer = 4 * d * d + 2 * d * df
mac_fwd = per_layer * L + (2 * T * d) * L + d * V
print("  每层线性 = 4*%d^2 + 2*%d*%d = %d + %d = %d" % (d, d, df, 4 * d * d, 2 * d * df, per_layer))
print("  注意力侧 4 d^2 = qkv 3 d^2 + proj d^2 = %d + %d" % (3 * d * d, d * d))
print("  前馈侧 2 d d_ff = fc1 d x d_ff + fc2 d_ff x d = %d + %d" % (d * df, df * d))
print("  = %d*%d + 2*%d*%d*%d + %d*%d = %d" % (per_layer, L, T, d, L, d, V, mac_fwd))
print("常见简写「每层 12 d^2」只在 d_ff = 4d 时成立：GPT-2 124M（d=768, d_ff=3072）两者都是 %d，"
      "本章 d_ff=%d=2d，所以 12 d^2=%d 比真实每层 %d 多算 %d（%0.0f%%）" % (
          12 * 768 * 768, df, 12 * d * d, per_layer, 12 * d * d - per_layer,
          100.0 * (12 * d * d - per_layer) / per_layer))
print("每步（B*T 个 token，反向按 2 倍前向）约 %d MAC" % (mac_fwd * B * T * 3))
print("整次训练 %d 步约 %.3e MAC，喂进去的 token 总数 = %d" % (S, mac_fwd * B * T * 3 * S, B * T * S))
print("训练见到的 token 数是语料长度 %d 的 %.1f 倍（所以这是过拟合式的复述，不是预训练）" % (
    len(text), B * T * S / len(text)))
print()

print("激活量（前向要为反向留住的中间量，单位 float）")
act_per_layer = B * T * (d + 3 * d + d + d + df + df)
print("  每块: B*T*(a+qkv+ao+b+f1+g) = %d*%d*(%d+%d+%d+%d+%d+%d) = %d" % (
    B, T, d, 3 * d, d, d, df, df, act_per_layer))
print("  %d 块合计 %d，加 logits %d*%d = %d，总计 %.3e float ≈ %.1f MB（float64）" % (
    L, act_per_layer * L, B * T, V, B * T * V,
    (act_per_layer * L + B * T * V), (act_per_layer * L + B * T * V) * 8 / 1048576.0))
print()

print("解码期 KV Cache：每层每 token 存 k 与 v，各 H*d_head = d 个数")
kv_tok = 2 * L * d
print("  每 token = 2*%d*%d = %d float = %.1f KB（float32）" % (L, d, kv_tok, kv_tok * 4 / 1024.0))
for ctx in (1024, 4096, 32768):
    print("  上下文 %d，单条序列 = %.2f MB" % (ctx, kv_tok * ctx * 4 / 1048576.0))
print("  同一公式换成 GPT-2 124M 的形状（L=12, d=768）：每 token %d float = %.1f KB（float32）" % (
    2 * 12 * 768, 2 * 12 * 768 * 4 / 1024.0))
print()

print("注意力 O(T^2) 与逐位置 FF/O 的两笔账")
for ctx in (T, 512, 4096):
    quad = 2 * ctx * d * L
    lin = per_layer * L
    print("  T=%-5d 注意力打分 %d : 线性层 %d  ->  比值 %.3f" % (ctx, quad, lin, quad / lin))
print("  两条相等的上下文长度 T* = 每层线性 / (2 d) = %d；本章窗口 T=%d 在它左边，"
      "所以二次项还压不过线性项" % (per_layer // (2 * d), T))
print("  （这也是「长上下文才需要 FlashAttention」的算术原因：短窗口里省注意力是省错地方）")
print()

print("同一形状三种点积写法实测吞吐：倍率与秒数都走 stderr，stdout 只留下选中的写法")


def dot_map(a, b):
    return sum(map(G.mul, a, b))


def dot_zip(a, b):
    return sum(x * y for x, y in zip(a, b))


def dot_loop(a, b):
    t = 0.0
    for i in range(len(a)):
        t += a[i] * b[i]
    return t


n = 24
xs = [G.random.Random(0).gauss(0, 1) for _ in range(n)]
styles = [("sum(map(mul,...))", dot_map), ("sum(x*y for ...)", dot_zip), ("for i in range(...)", dot_loop)]
rates = {}
for name, fn in styles:
    reps = 40000
    t0 = time.time()
    for _ in range(reps):
        fn(xs, xs)
    el = time.time() - t0
    rates[name] = reps * n / el / 1e6
    G.eprint("  %-22s %.1f M-MAC/s  (%.3f s / %d 次)" % (name, rates[name], el, reps))
best = max(rates.values())
worst = min(rates.values())
G.eprint("  最快/最慢 = %.2f 倍" % (best / worst))
print("  被选中的写法: sum(map(mul, x, W[j]))，逐输出单元一个点积，权重按输出列存")
print()

print("整步耗时实测：跑 3 步取均值（stderr），并外推 %d 步" % S)
rng = G.random.Random(G.CONFIG["seed"])
state = {}
t0 = time.time()
for step in range(1, 4):
    G.training_step(p, tok, text, rng, state, step)
per = (time.time() - t0) / 3.0
G.eprint("  实测 %.3f s/step -> %d 步 ≈ %.1f s（预算 %.0f s）" % (per, S, per * S, G.BUDGET_S))
G.eprint("  每步 %.3f 秒 / 每 token %.4f 毫秒（外推值，随机器变化）" % (per, per * 1000.0 / (B * T)))
print("  预算判定交给判据自己计时，不信任这里贴出的数")
