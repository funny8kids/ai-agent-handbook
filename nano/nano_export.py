# -*- coding: utf-8 -*-
"""第 22 章 第 7 页：导出与复现 —— 检查点的字节稳定性、重载后逐位一致的 logits、和真实部署差的那几步。

达标线：同一份参数序列化两次 sha256 相同；从文件重载后 logits 与内存里的逐位一致；
文件里的参数个数与参数账页的实测对平。

Run:  python nano_export.py
"""
import hashlib
import json
import math
import os
import struct
import sys

import gptnano as G

G.utf8_out()
text = G.read_corpus()
tok = G.build_tokenizer(text)
V = tok["vocab_size"]
path = G.default_ckpt()
if not os.path.isfile(path):
    print("缺少检查点 nano/weights_alice.json，请先运行 python nano_train.py")
    sys.exit(1)

with open(path, encoding="utf-8") as f:
    raw = f.read()
stored = json.loads(raw)
p = stored["params"]

print("检查点 nano/weights_alice.json")
print("  字节数 = %d   sha256 = %s" % (len(raw.encode("utf-8")),
                                       hashlib.sha256(raw.encode("utf-8")).hexdigest()))
print("  顶层键 = %s（config 与 params 一起存，读者能核对跑的是哪套配置）" % " ".join(stored.keys()))
print("  文件内 config 的参数量口径: L=%d H=%d d=%d d_ff=%d T=%d V=%d" % (
    stored["config"]["n_layer"], stored["config"]["n_head"], stored["config"]["d_model"],
    stored["config"]["d_ff"], stored["config"]["block_size"], len(p["wte"])))
print()

print("参数个数对平")
counted = G.count_params(p)
breakdown = sum(r[2] for r in G.param_breakdown(p))
print("  从文件重载 count_params = %d" % counted)
print("  分模块求和            = %d" % breakdown)
print("  差 = %d（参数账页要求 0）" % (counted - breakdown))
print("  顶层张量清单: %s" % " ".join(sorted(k for k in p if not k.startswith("b"))))
print("  块内张量清单: %s" % " ".join(sorted(p["b0"].keys())))
print("  每个数组的形状: wte %d x %d, lm_head %d x %d, qkv %d x %d, fc1 %d x %d, fc2 %d x %d" % (
    len(p["wte"]), len(p["wte"][0]), len(p["lm_head"]), len(p["lm_head"][0]),
    len(p["b0"]["qkv"]), len(p["b0"]["qkv"][0]), len(p["b0"]["fc1"]), len(p["b0"]["fc1"][0]),
    len(p["b0"]["fc2"]), len(p["b0"]["fc2"][0])))
print()

xb, yb = G.fixed_batch(tok, text)
lg_mem = G.forward(p, xb, yb)[1]["logits"]
lg_file = G.forward(G.load_params(path), xb, yb)[1]["logits"]
same = lg_mem == lg_file
worst = max(abs(a - b) for ra, rb in zip(lg_mem, lg_file) for a, b in zip(ra, rb))
print("重载后的 logits 逐位一致: %s   最大绝对差 = %.1e" % (same, worst))
print("  （这一条比的是同一份文件的两条读入路径：它证明解析没有非确定性，不证明截断没代价）")
print()

print("截断这一笔：9 位有效数字到底丢了什么（拿一份全新、从未写过盘的参数量）")


def flat(obj):
    if isinstance(obj, (float, int)) and not isinstance(obj, bool):
        return [float(obj)]
    out = []
    if isinstance(obj, dict):
        for k in sorted(obj):
            out += flat(obj[k])
    else:
        for x in obj:
            out += flat(x)
    return out


probe = os.path.join(G.HERE, "out", "trunc_probe.json")
p0 = G.init_params(V)
_, nb0 = G.save_params(p0, probe)
p1 = G.load_params(probe)
v0, v1 = flat(p0), flat(p1)
changed = sum(1 for a, b in zip(v0, v1) if a != b)
abs9 = max(abs(a - b) for a, b in zip(v0, v1))
rel9 = max(abs(a - b) / abs(b) for a, b in zip(v0, v1) if b != 0.0)
v32 = [struct.unpack("<f", struct.pack("<f", x))[0] for x in v0]
rel32 = max(abs(a - b) / abs(b) for a, b in zip(v0, v32) if b != 0.0)
lg0 = G.forward(p0, xb, yb)[1]["logits"]
lg1 = G.forward(p1, xb, yb)[1]["logits"]
abs_out = max(abs(a - b) for ra, rb in zip(lg0, lg1) for a, b in zip(ra, rb))
os.remove(probe)
print("  写盘再读回：%d 个浮点里 %d 个值变了，最大绝对差 %.3e  最大相对差 %.3e" % (
    len(v0), changed, abs9, rel9))
print("  同一批 logits 过这道截断：最大绝对差 %.3e（未训练模型的 logits 本身就是 %.1e 量级）" % (
    abs_out, max(abs(a) for r in lg0 for a in r)))
print("  对照：把同样这份参数强转 fp32 再读回，最大相对差 %.3e" % rel32)
print("  所以 9 位十进制文本比 fp32 二进制更准 %.0f 倍，而 float64 无损往返要 %.0f 位" % (
    rel32 / rel9, math.ceil(math.log10(2 ** 53)) + 1))
print()

again = G.save_params(G.load_params(path), os.path.join(G.HERE, "out", "reexport.json"))
print("重新序列化一次的稳定性")
print("  第一次 sha256 = %s" % hashlib.sha256(raw.encode("utf-8")).hexdigest())
print("  第二次 sha256 = %s" % again[0])
print("  相同: %s   字节数 %d vs %d" % (again[0] == hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                                     len(raw.encode("utf-8")), again[1]))
os.remove(os.path.join(G.HERE, "out", "reexport.json"))
print()

print("推理侧的一小步账：同一句话在有/无 KV Cache 下重算多少")
prompt = "alice was beginning"
ids = G.encode(prompt, tok)
n_new = 8
T = G.CONFIG["block_size"]
d, L = G.CONFIG["d_model"], G.CONFIG["n_layer"]
full = sum(min(T, len(ids) + i) for i in range(n_new))
cache = len(ids) + n_new
print("  提示 %r（%d 字符），再生成 %d 个字符" % (prompt, len(ids), n_new))
print("  不用缓存：每个新字符把整个窗口重算一遍，位置前向次数合计 %d" % full)
print("  用缓存：  只有最新位置需要新算，合计 %d 次，省下 %.1f%%" % (
    cache, 100.0 * (1 - cache / full)))
print("  换来的代价：每层每位置存 k 与 v，%d 个位置 x 2*%d*%d float = %d 个浮点数" % (
    cache, L, d, cache * 2 * L * d))
print("  第 6 页的 generate 故意不用缓存：那样这笔账只能靠说，而不是靠跑")
print()

print("从这份检查点到真部署，还差的是机制而不是神秘感:")
print("  1) 权重转置/命名对齐推理引擎（这里是按输出列存的 list，引擎侧要的是连续 buffer）")
kb = 1024.0
nb = len(raw.encode("utf-8"))
print("  2) 精度：%d 个参数，十进制文本 %d B（%.1f KB）比 fp64 二进制 %.1f KB 大 %.2f 倍，"
      "而 fp32 只需 %.1f KB、int8 只需 %.1f KB —— 从文本到 int8 是 %.0f 倍" % (
          counted, nb, nb / kb, counted * 8 / kb, nb / (counted * 8.0),
          counted * 4 / kb, counted * 1 / kb, nb / (counted * 1.0)))
print("  3) safetensors / GGUF 这类容器格式：把张量元数据与 blob 分开放，加载可以 mmap 且防任意代码执行")
print("  4) 词表与预处理一起打包（第 1 页的 %d 个字符在这里变成真正的麻烦：读者换语料就得换整份权重）" % V)
print("  5) 生成侧补 KV Cache、批量与连续批处理（第 16 章的推理服务讲的就是这三件）")
