# -*- coding: utf-8 -*-
"""第 22 章 第 5 页：真训练 —— 冻结步数的 Adam，loss 记录逐行落地，末段必须达到冻结的达标线。

达标线（写代码之前冻在 spec.md 里）：末段 loss <= 0.70 x ln V，记录不少于 20 行，
两次运行的 stdout 逐字节相同。墙钟时间一律走 stderr：把「这台机器跑了多少秒」打进 stdout，
逐字节复现立刻变成假话。

Run:  python nano_train.py
"""
import math
import random
import time

import gptnano as G

G.utf8_out()
text = G.read_corpus()
tok = G.build_tokenizer(text)
V = tok["vocab_size"]
C, L, B, S = G.CONFIG["d_model"], G.CONFIG["n_layer"], G.CONFIG["batch_size"], G.CONFIG["train_steps"]
LOG = G.CONFIG["log_every"]
lnV, BAR = math.log(V), 0.70 * math.log(V)

xb0, yb0 = G.fixed_batch(tok, text)
p = G.init_params(V)
base = G.loss_of(p, xb0, yb0)

print("配置: L=%d H=%d d=%d d_ff=%d T=%d B=%d steps=%d 峰值 lr=%g warmup=%d cos 衰减到 %g" % (
    L, G.CONFIG["n_head"], C, G.CONFIG["d_ff"], G.CONFIG["block_size"], B, S,
    G.CONFIG["lr"], G.CONFIG["warmup_steps"], G.CONFIG["min_lr_frac"]))
print("参数量 %d   词表 %d   语料 %d 字符   每步 %d 个预测" % (
    G.count_params(p), V, len(text), B * G.CONFIG["block_size"]))
print("达标线: 末段 loss <= 0.70 x ln V = %.6f nats/token" % BAR)
print("对照: 未训练模型同一批 loss = %.6f（贴着 ln V，只会均匀猜测）" % base)
print()

rng = random.Random(G.CONFIG["seed"])
state = {}
records = []
t0 = time.time()
print("%6s %10s %9s %9s" % ("step", "lr", "loss", "ppl"))
for step in range(1, S + 1):
    loss = G.training_step(p, tok, text, rng, state, step)
    if step % LOG == 0 or step == 1:
        records.append((step, G.lr_at(step), loss))
        print("%6d %10.5f %9.4f %9.4f" % (step, G.lr_at(step), loss, math.exp(loss)))
    G.eprint("  step %3d  %.2f s" % (step, time.time() - t0))
print()

tail = [r[2] for r in records][-10:]
mean_tail = sum(tail) / len(tail)
print("记录行数 = %d（达标线 20 行）" % len(records))
print("末段 10 行 loss: %s" % " ".join("%.4f" % x for x in tail))
print("末段均值 = %.6f   达标线 = %.6f   判定 = %s" % (
    mean_tail, BAR, "OK" if mean_tail <= BAR else "MISS"))
print("相对未训练: %.4f -> %.4f，下降 %.2f%%" % (base, mean_tail, 100.0 * (base - mean_tail) / base))
vl = G.val_loss(p, tok, text)
print("留出集 loss = %.6f   困惑度 = %.4f（尾部 %d%%，%d 个窗口，固定种子）" % (
    vl, math.exp(vl), int(100 * G.CONFIG["holdout_frac"]), G.CONFIG["val_windows"]))
print()

digest, size = G.save_params(p, G.default_ckpt())
print("检查点 nano/weights_alice.json: sha256 = %s" % digest)
print("           字节数 = %d   参数个数 = %d   序列化保留 %d 位有效数字" % (
    size, G.count_params(p), G.CONFIG["ckpt_sig_digits"]))
again = G.loss_of(G.load_params(G.default_ckpt()), xb0, yb0)
inmem = G.loss_of(p, xb0, yb0)
print("重读检查点再前向 loss = %.9f，内存里未截断的那份 = %.9f，差 %.1e" % (again, inmem, abs(again - inmem)))
print("  （这 %.1e 就是 %d 位有效数字截断的代价。第 7 页比较的是「文件里的值」对「文件重载后的值」，"
      "那才是逐位一致）" % (abs(again - inmem), G.CONFIG["ckpt_sig_digits"]))
G.eprint("  总耗时 %.1f 秒（预算 %.0f 秒，判据自己计时）" % (time.time() - t0, G.BUDGET_S))
