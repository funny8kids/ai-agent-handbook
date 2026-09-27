# -*- coding: utf-8 -*-
"""The model this chapter writes from scratch: a character-level GPT, standard library only.

No third-party import is allowed anywhere in `nano/`: `check_lab_runnability.py` runs every
`nano/nano_*.py` on a bare interpreter, and 「零依赖、零 API key、本机直接跑」 is one of the three
hard rules this chapter inherits from chapter 19.

Two conventions worth knowing before reading the maths:

* Weight matrices are stored **by output column** (`W[j][i]` = weight from input `i` to output `j`),
  so a linear layer is one `sum(map(mul, x, W[j]))` dot product per output unit. Measured on this
  machine that spelling is about 2x the throughput of accumulating over rows — the budget page keeps
  the real numbers.
* Every quantity a page quotes is machine-independent (counts, shapes, losses, perplexities, ids).
  Wall-clock is printed to **stderr** only, so stdout stays byte-identical across runs, which is what
  the reproducibility judge compares.

Run a script, not this module: `nano_tokenizer.py`, `nano_forward.py`, `nano_budget.py`,
`nano_backward.py`, `nano_train.py`, `nano_sample.py`, `nano_export.py`.
"""
import hashlib
import json
import math
import os
import random
import sys
import unicodedata
from operator import mul

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# --------------------------------------------------------------------------- config
# Frozen before the first run; the chapter's own bound (spec.md) is n_layer<=2, d_model<=40,
# block_size<=24, train_steps<=800, and a training run inside the 120 s reproducibility budget.
# These six numbers are not a taste call: `nano_shape.py` ran 11 in-bounds shapes through the real
# train+sample scripts, and this is the only one that clears both the 60% sampling line and the
# 120 s budget (worst segment 61.0%, 1.0 point of margin -- the sweep table says so out loud).
CONFIG = {
    "n_layer": 2,
    "n_head": 2,
    "d_model": 12,
    "d_ff": 24,
    "block_size": 24,
    "batch_size": 8,
    "train_steps": 700,
    "lr": 0.045,
    "warmup_steps": 30,
    "min_lr_frac": 0.1,
    "beta1": 0.9,
    "beta2": 0.999,
    "adam_eps": 1e-8,
    "init_std": 0.02,
    "seed": 20260927,
    "log_every": 10,
    "val_windows": 12,
    "ckpt_sig_digits": 9,
    "corpus_chars": 1656,
    "holdout_frac": 0.1,
}
BOUNDS = {"n_layer": 2, "d_model": 40, "block_size": 24, "train_steps": 800}
BUDGET_S = 120.0

ALLOWED = set("abcdefghijklmnopqrstuvwxyz .,;:!?'\"()-\n")
RAW_SOURCE = "https://www.gutenberg.org/files/11/11-0.txt"
RAW_TEXT = """\
Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to
do: once or twice she had peeped into the book her sister was reading, but it had no pictures or
conversations in it, "and what is the use of a book," thought Alice, "without pictures or
conversations?" So she was considering in her own mind (as well as she could, for the hot day made
her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the
trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close
by her. There was nothing so very remarkable in that; nor did Alice think it so very much out of the
way to hear the Rabbit say to itself, "Oh dear! Oh dear! I shall be too late!" When the Rabbit
actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice
started to her feet, for it flashed across her mind that she had never before seen a rabbit with
either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across
the field after it, and was just in time to see it pop down a large rabbit-hole under the hedge. In
another moment down went Alice after it, never once considering how in the world she was to get out
again. The rabbit went straight on in front of her for some way, and then suddenly dived down under
the hedge. Alice followed, without stopping to think even for a moment, and found herself in a very
deep hole, falling slowly down, with a dull thud at the bottom. It was very dark in there, and she
had plenty of time to look about her and to wonder what was going to happen next.
"""


def normalize(raw=RAW_TEXT, cutoff=None):
    cutoff = CONFIG["corpus_chars"] if cutoff is None else cutoff
    out, prev_space = [], False
    for c in raw.lower():
        c = "\n" if c == "\n" else (" " if c.isspace() else c)
        if c not in ALLOWED:
            continue
        if c == " " and prev_space:
            continue
        prev_space = c == " "
        out.append(c)
        if len(out) >= cutoff:
            break
    return "".join(out)


def read_corpus():
    """The model's data is derived from `RAW_TEXT` on every run: a stale cached corpus must never
    get to decide what the reproducibility check reproduces. `nano_tokenizer.py` writes
    `out/corpus.txt` as an artifact, and the 达标 judge re-derives it to compare."""
    return normalize()


# --------------------------------------------------------------------------- tokenizer
def build_tokenizer(text):
    chars = sorted(set(text))
    return {"vocab": chars,
            "stoi": {c: i for i, c in enumerate(chars)},
            "itos": chars,
            "vocab_size": len(chars),
            "chars": len(text)}


def encode(text, tok):
    return [tok["stoi"][c] for c in text]


def decode(ids, tok):
    return "".join(tok["itos"][i] for i in ids)


# --------------------------------------------------------------------------- small maths
def dot(a, b):
    return sum(map(mul, a, b))


def softmax(xs):
    m = max(xs)
    e = [math.exp(x - m) for x in xs]
    s = sum(e)
    return [v / s for v in e]


def logsumexp(xs):
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs))


def gelu(x):
    return 0.5 * x * (1.0 + math.erf(x / math.sqrt(2.0)))


def gelu_grad(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0))) + \
        x * math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def linear(cols, bias, rows):
    """y[m][j] = dot(rows[m], cols[j]) + bias[j]."""
    return [[dot(r, w) + b for w, b in zip(cols, bias)] for r in rows]


def linear_backward(cols, rows, dy):
    """Returns (dx, dcols, dbias) for `linear`."""
    n_out, n_in = len(cols), len(cols[0])
    dcols = [[0.0] * n_in for _ in range(n_out)]
    dbias = [0.0] * n_out
    dx = []
    for r, m in zip(rows, dy):
        row = [0.0] * n_in
        for j, v in enumerate(m):
            if v:
                dbias[j] += v
                w = cols[j]
                row = [a + v * b for a, b in zip(row, w)]
                dj = dcols[j]
                dcols[j] = [a + v * b for a, b in zip(dj, r)]
        dx.append(row)
    return dx, dcols, dbias


def layernorm(rows, gamma, beta):
    d = len(gamma)
    out, cache = [], []
    for v in rows:
        mu = sum(v) / d
        var = sum((x - mu) ** 2 for x in v) / d
        std = math.sqrt(var + 1e-5)
        hat = [(x - mu) / std for x in v]
        cache.append((hat, std))
        out.append([h * g + b for h, g, b in zip(hat, gamma, beta)])
    return out, cache


def layernorm_backward(dy, cache, gamma):
    d = len(gamma)
    dx, dg, db = [], [0.0] * d, [0.0] * d
    for m, (hat, std) in zip(dy, cache):
        dhat = [a * g for a, g in zip(m, gamma)]
        mean_dhat = sum(dhat) / d
        mean_dhat_hat = sum(a * b for a, b in zip(dhat, hat)) / d
        dx.append([(a - mean_dhat - h * mean_dhat_hat) / std
                   for a, h in zip(dhat, hat)])
        dg = [s + m_i * h for s, m_i, h in zip(dg, m, hat)]
        db = [s + m_i for s, m_i in zip(db, m)]
    return dx, dg, db


def flatten(rows):
    out = []
    for r in rows:
        out.extend(r)
    return out


# --------------------------------------------------------------------------- parameters
def init_params(vocab_size, seed=None, std=None):
    rng = random.Random(CONFIG["seed"] if seed is None else seed)
    d, T = CONFIG["d_model"], CONFIG["block_size"]
    df, std = CONFIG["d_ff"], CONFIG["init_std"] if std is None else std

    def mat(n_in, n_out):
        return [[rng.gauss(0.0, std) for _ in range(n_in)] for _ in range(n_out)]

    def block():
        return {"ln1_g": [1.0] * d, "ln1_b": [0.0] * d,
                "qkv": mat(d, 3 * d), "qkv_b": [0.0] * (3 * d),
                "proj": mat(d, d), "proj_b": [0.0] * d,
                "ln2_g": [1.0] * d, "ln2_b": [0.0] * d,
                "fc1": mat(d, df), "fc1_b": [0.0] * df,
                "fc2": mat(df, d), "fc2_b": [0.0] * d}

    p = {"wte": mat(d, vocab_size), "wpe": mat(d, T),
         "lnf_g": [1.0] * d, "lnf_b": [0.0] * d,
         "lm_head": mat(d, vocab_size), "lm_b": [0.0] * vocab_size}
    for i in range(CONFIG["n_layer"]):
        p["b%d" % i] = block()
    return p


def n_leaves(q):
    if isinstance(q, dict):
        return sum(n_leaves(v) for v in q.values())
    return sum(n_leaves(x) for x in q) if isinstance(q, list) else 1


def count_params(p):
    return sum(n_leaves(v) for v in p.values())


def zeros_like(q):
    """Gradient buffers take their shape from the parameters, never from the current batch."""
    if isinstance(q, dict):
        return {k: zeros_like(v) for k, v in q.items()}
    return [zeros_like(x) for x in q] if isinstance(q, list) else 0.0


def param_breakdown(p):
    """(label, formula, count) rows that must sum to count_params(p) exactly.

    The count column is derived from the dimension names only, so the judge's comparison against
    `count_params(p)` is a real cross-check rather than the same walk printed twice.
    """
    d, T, V = CONFIG["d_model"], CONFIG["block_size"], len(p["wte"])
    df, L = CONFIG["d_ff"], CONFIG["n_layer"]
    blk_ln = 4 * d                                  # ln1_g/b and ln2_g/b
    blk_attn = 3 * d * d + 3 * d + d * d + d        # qkv(+bias) and proj(+bias)
    blk_mlp = 2 * d * df + df + d                   # fc1/fc2 and their biases
    blk = blk_ln + blk_attn + blk_mlp
    rows = [("token 嵌入 wte", "V x d = %d x %d" % (V, d), V * d),
            ("位置嵌入 wpe", "T x d = %d x %d" % (T, d), T * d),
            ("层归一化 x%d 块" % L, "4 x d x %d 块" % L, 4 * d * L),
            ("注意力 qkv+proj x%d" % L, "(3 d^2 + 3 d + d^2 + d) x %d" % L, blk_attn * L),
            ("前馈 fc1+fc2 x%d" % L, "(2 d x d_ff + d_ff + d) x %d" % L, blk_mlp * L),
            ("终层 layernorm", "2 x d", 2 * d),
            ("输出投影 lm_head", "d x V = %d x %d" % (d, V), d * V),
            ("输出偏置 lm_b", "V = %d" % V, V)]
    return rows


# --------------------------------------------------------------------------- attention
def attention_forward(qkv_rows, B, T):
    """qkv_rows: flattened (B*T) rows of width 3d. Returns (out_rows, cache)."""
    d, nh = CONFIG["d_model"], CONFIG["n_head"]
    dh = d // nh
    out = [[0.0] * d for _ in range(B * T)]
    heads = []
    for i in range(B * T):
        row = qkv_rows[i]
        q = [row[h * dh:(h + 1) * dh] for h in range(nh)]
        k = [row[d + h * dh:d + (h + 1) * dh] for h in range(nh)]
        v = [row[2 * d + h * dh:2 * d + (h + 1) * dh] for h in range(nh)]
        heads.append((q, k, v))
    scale = 1.0 / math.sqrt(dh)
    probs = [[None] * nh for _ in range(B * T)]
    for h in range(nh):
        for i in range(B * T):
            t = i % T
            q, k, v = heads[i]
            sc = [dot(q[h], heads[j][1][h]) * scale for j in range(i - t, i + 1)]
            pr = softmax(sc)
            probs[i][h] = pr
            acc = out[i][h * dh:(h + 1) * dh]
            for j, w in zip(range(t + 1), pr):
                if w:
                    acc = [a + w * b for a, b in zip(acc, heads[i - t + j][2][h])]
            out[i][h * dh:(h + 1) * dh] = acc
    return out, {"heads": heads, "probs": probs, "scale": scale}


def attention_backward(dy, cache, B, T):
    """Grad wrt the qkv rows. Rows are per-position, so head slices stay inside one row."""
    d, nh = CONFIG["d_model"], CONFIG["n_head"]
    dh = d // nh
    heads, probs, scale = cache["heads"], cache["probs"], cache["scale"]
    dqkv = [[0.0] * (3 * d) for _ in range(B * T)]
    for h in range(nh):
        # ds[i][j] = p * (do_i . v_j - sum_k p * (do_i . v_k))   (softmax backward)
        ds = []
        for i in range(B * T):
            t = i % T
            do = dy[i][h * dh:(h + 1) * dh]
            pr = probs[i][h]
            dps = [dot(do, heads[i - t + j][2][h]) for j in range(t + 1)]
            c = sum(w * dp for w, dp in zip(pr, dps))
            ds.append([w * (dp - c) for w, dp in zip(pr, dps)])
        for i in range(B * T):
            t = i % T
            base = i - t
            do = dy[i][h * dh:(h + 1) * dh]
            pr, row, q = probs[i][h], ds[i], heads[i][0][h]
            for j, w in enumerate(pr):
                if w:                                   # dv_j += p_ij * do_i
                    tgt = dqkv[base + j]
                    off = 2 * d + h * dh
                    for m in range(dh):
                        tgt[off + m] += w * do[m]
            dq = [0.0] * dh
            for j, s in enumerate(row):
                if s:                                   # dk_j += ds_ij * q_i * scale
                    tgt = dqkv[base + j]
                    off = d + h * dh
                    for m in range(dh):
                        tgt[off + m] += s * q[m] * scale
                        dq[m] += s * heads[base + j][1][h][m] * scale
            tgt = dqkv[i]
            for m in range(dh):                         # dq_i += sum_j ds_ij * k_j * scale
                tgt[h * dh + m] += dq[m]
    return dqkv


# --------------------------------------------------------------------------- forward / backward
def forward(p, xb, yb=None):
    """xb: B rows of `block_size` input ids; yb: the same rows shifted by one. Returns (loss, cache)."""
    B, T = len(xb), len(xb[0])
    h, cache = [], []
    for r in range(B):
        for t in range(T):
            h.append([a + b for a, b in zip(p["wte"][xb[r][t]], p["wpe"][t])])
    for li in range(CONFIG["n_layer"]):
        blk = p["b%d" % li]
        a, ln1 = layernorm(h, blk["ln1_g"], blk["ln1_b"])
        qkv = linear(blk["qkv"], blk["qkv_b"], a)
        ao, ac = attention_forward(qkv, B, T)
        pr = linear(blk["proj"], blk["proj_b"], ao)
        h = [[x + y for x, y in zip(hh, pp)] for hh, pp in zip(h, pr)]
        b, ln2 = layernorm(h, blk["ln2_g"], blk["ln2_b"])
        f1 = linear(blk["fc1"], blk["fc1_b"], b)
        g = [[gelu(x) for x in row] for row in f1]
        f2 = linear(blk["fc2"], blk["fc2_b"], g)
        h = [[x + y for x, y in zip(hh, ff)] for hh, ff in zip(h, f2)]
        cache.append({"a": a, "ln1": ln1, "attn": ac, "ao": ao,
                      "b": b, "ln2": ln2, "f1": f1, "g": g})
    xn, lnf = layernorm(h, p["lnf_g"], p["lnf_b"])
    logits = linear(p["lm_head"], p["lm_b"], xn)
    cache.append({"xn": xn, "lnf": lnf})
    loss = None
    if yb is not None:
        tg = flatten([row[:T] for row in yb])
        loss = sum(-lg[t] + logsumexp(lg) for lg, t in zip(logits, tg)) / len(logits)
    return loss, {"logits": logits, "blocks": cache, "B": B, "T": T, "xb": xb,
                  "targets": flatten([row[:T] for row in yb]) if yb else None}


def backward(p, st, drop=None):
    """Hand-derived gradients of the mean cross-entropy computed by `forward`.

    `drop` leaves one gradient term out on purpose. Only the backward page uses it: a gradient check
    that never fails on a planted missing term is a check that cannot see anything.
    """
    B, T = st["B"], st["T"]
    d, V = CONFIG["d_model"], len(p["wte"])
    df = CONFIG["d_ff"]
    n = float(B * T)
    g = zeros_like(p)

    dlog = []
    for lg, t_id in zip(st["logits"], st["targets"]):
        pr = softmax(lg)
        pr[t_id] -= 1.0
        dlog.append([v / n for v in pr])

    last = st["blocks"][-1]
    dxn, dw_lm, db_lm = linear_backward(p["lm_head"], last["xn"], dlog)
    g["lm_head"], g["lm_b"] = ([[0.0] * d for _ in range(V)] if drop == "lm_head" else dw_lm), db_lm
    dh, g["lnf_g"], g["lnf_b"] = layernorm_backward(dxn, last["lnf"], p["lnf_g"])

    for li in range(CONFIG["n_layer"] - 1, -1, -1):
        blk, gb, c = p["b%d" % li], g["b%d" % li], st["blocks"][li]
        # h_out = h_mid + fc2(gelu(fc1(LN2(h_mid))))  ->  split the gradient into skip and MLP path
        dx_fc2, gb["fc2"], gb["fc2_b"] = linear_backward(blk["fc2"], c["g"], dh)
        if drop == "fc2":
            gb["fc2"] = [[0.0] * df for _ in range(d)]
        df1 = [[a * gelu_grad(x) for a, x in zip(row, pre)]
               for row, pre in zip(dx_fc2, c["f1"])]
        dx_fc1, gb["fc1"], gb["fc1_b"] = linear_backward(blk["fc1"], c["b"], df1)
        d_ln2 = layernorm_backward(dx_fc1, c["ln2"], blk["ln2_g"])
        dh_mid = [[a + b for a, b in zip(x, y)] for x, y in zip(dh, d_ln2[0])]
        gb["ln2_g"], gb["ln2_b"] = d_ln2[1], d_ln2[2]
        # h_mid = h_in + proj(attention(qkv(LN1(h_in))))
        dx_proj, gb["proj"], gb["proj_b"] = linear_backward(blk["proj"], c["ao"], dh_mid)
        dqkv = attention_backward(dx_proj, c["attn"], B, T)
        if drop == "attention":
            dqkv = [[0.0] * (3 * d) for _ in range(B * T)]
        dx_qkv, gb["qkv"], gb["qkv_b"] = linear_backward(blk["qkv"], c["a"], dqkv)
        dx_ln1, gb["ln1_g"], gb["ln1_b"] = layernorm_backward(dx_qkv, c["ln1"], blk["ln1_g"])
        # h_mid = h_in + proj(...): the gradient reaches h_in both through LN1 and through the skip
        dh = [[a + b for a, b in zip(x, y)] for x, y in zip(dh_mid, dx_ln1)]

    for r in range(B):
        for t in range(T):
            v, w, e = dh[r * T + t], g["wte"][st["xb"][r][t]], g["wpe"][t]
            for m in range(d):
                w[m] += v[m]
                e[m] += v[m]
    return g


def gradcheck(p, xb, yb, eps=1e-4, drop=None):
    """Central-difference check of `backward` against the loss itself.

    Returns (max_rel_error, rows). A sampled parameter is (path, index) and
    rel = |analytic - numeric| / (|analytic| + |numeric| + 1e-9).
    """
    loss0, st = forward(p, xb, yb)
    ana = backward(p, st, drop=drop)
    rels, rows = [], []
    for path, i, j in sample_params(p, xb):
        par = get_path(p, path)
        orig = par[i] if j is None else par[i][j]
        set_leaf(p, path, i, j, orig + eps)
        up = forward(p, xb, yb)[0]
        set_leaf(p, path, i, j, orig - eps)
        dn = forward(p, xb, yb)[0]
        set_leaf(p, path, i, j, orig)
        numeric = (up - dn) / (2 * eps)
        a = get_leaf(ana, path, i, j)
        rel = abs(a - numeric) / (abs(a) + abs(numeric) + 1e-9)
        rels.append(rel)
        label = ".".join(path) + ("[%d]" % i if j is None else "[%d][%d]" % (i, j))
        rows.append((label, a, numeric, rel))
    assert loss0 == forward(p, xb, yb)[0], "gradcheck disturbed the parameters"
    return max(rels), rows


def sample_params(p, xb=None):
    """One leaf per parameter array, so every module is represented in the gradient check.

    The embedding rows are picked from ids the batch actually contains: a row that never appears
    has zero gradient on both sides, which would pass without checking anything.
    """
    used = sorted(set(flatten(xb))) if xb else []
    picks = []
    for path, arr in leaf_arrays(p):
        if path == ("wte",) and used:
            i = used[len(used) // 2]
        elif path == ("wpe",) and xb:
            i = min(len(arr) - 1, (len(xb[0]) - 1) // 2)
        else:
            i = len(arr) // 3
        if isinstance(arr[i], list):
            picks.append((path, i, len(arr[i]) // 3))
        else:
            picks.append((path, i, None))
    return picks


def leaf_arrays(p, path=()):
    if isinstance(p, dict):
        for k, v in p.items():
            for it in leaf_arrays(v, path + (k,)):
                yield it
    elif p and isinstance(p[0], list):
        yield path, p
    else:
        yield path, p


def get_path(p, path):
    for k in path:
        p = p[k]
    return p


def get_leaf(g, path, i, j):
    v = get_path(g, path)
    return v[i] if j is None else v[i][j]


def set_leaf(p, path, i, j, value):
    arr = get_path(p, path)
    if j is None:
        arr[i] = value
    else:
        arr[i][j] = value


# --------------------------------------------------------------------------- optimiser
def lr_at(step, total=None):
    """Linear warmup then cosine decay to `min_lr_frac` of the peak.

    Both halves carry weight at this scale: a few-hundred-step run cannot afford an early
    overshoot (hence warmup) nor a flat end (hence decay), and every loss number this chapter
    prints is measured under this schedule.
    """
    total = CONFIG["train_steps"] if total is None else total
    warm = min(1.0, step / max(1, CONFIG["warmup_steps"]))
    cos = 0.5 * (1.0 + math.cos(math.pi * (step - 1) / max(1, total)))
    peak, floor = CONFIG["lr"], CONFIG["min_lr_frac"]
    return peak * (floor + (1 - floor) * cos) * warm


def adam(p, g, state, lr=None):
    state["t"] = state.get("t", 0) + 1
    t = state["t"]
    lr = CONFIG["lr"] if lr is None else lr
    b1, b2, eps = CONFIG["beta1"], CONFIG["beta2"], CONFIG["adam_eps"]

    def walk(par, grd, path):
        if isinstance(par[0], list):
            for i, (a, b) in enumerate(zip(par, grd)):
                walk(a, b, path + (i,))
            return
        key = ".".join(map(str, path))
        mv = state.get(key)
        if mv is None:
            mv = state[key] = ([0.0] * len(par), [0.0] * len(par))
        m, v = mv
        for i, (pv, gv) in enumerate(zip(par, grd)):
            mi = m[i] = b1 * m[i] + (1 - b1) * gv
            vi = v[i] = b2 * v[i] + (1 - b2) * gv * gv
            par[i] = pv - lr * (mi / (1 - b1 ** t)) / (math.sqrt(vi / (1 - b2 ** t)) + eps)

    for k, v in p.items():
        if isinstance(v, dict):
            for kk in v:
                walk(v[kk], g[k][kk], (k, kk))
        else:
            walk(v, g[k], (k,))


# --------------------------------------------------------------------------- data
def windows(ids, which, rng, count=None):
    """Sliding random windows over the id stream; `which='val'` uses the held-out tail."""
    T = CONFIG["block_size"] + 1
    cut = int(len(ids) * (1.0 - CONFIG["holdout_frac"]))
    lo, hi = (0, cut - T) if which == "train" else (cut, len(ids) - T)
    hi = max(hi, lo)
    for _ in range(CONFIG["batch_size"] if count is None else count):
        s = rng.randrange(lo, hi + 1)
        yield ids[s:s + T]


def fixed_batch(tok, text, seed=101):
    rng = random.Random(seed)
    ids = encode(text, tok)
    rows = list(windows(ids, "train", rng))
    return [r[:-1] for r in rows], [r[1:] for r in rows]


def val_loss(p, tok, text, seed=202, count=None):
    rng = random.Random(seed)
    ids = encode(text, tok)
    count = CONFIG["val_windows"] if count is None else count
    rows = list(windows(ids, "val", rng, count))
    tot, n = 0.0, 0
    for r in rows:
        l, _ = forward(p, [r[:-1]], [r[1:]])
        tot += l
        n += 1
    return tot / n


def loss_of(p, xb, yb):
    return forward(p, xb, yb)[0]


def training_step(p, tok, text, rng, state, step=None):
    """One step: sample windows, forward, hand-written backward, Adam at the scheduled lr.

    Returns the minibatch loss, which is what the 训练 log rows carry.
    """
    ids = encode(text, tok)
    rows = list(windows(ids, "train", rng))
    xb, yb = [r[:-1] for r in rows], [r[1:] for r in rows]
    loss, st = forward(p, xb, yb)
    lr = CONFIG["lr"] if step is None else lr_at(step)
    adam(p, backward(p, st), state, lr=lr)
    return loss


# --------------------------------------------------------------------------- generation
def char3gram_rate(sample, text):
    """Share of the sample's 3-character windows that occur in the training text: a machine-
    independent proxy for「学到了拼写」, and the bar the sampling page has to clear."""
    grams = set(text[i:i + 3] for i in range(len(text) - 2))
    hits = sum(1 for i in range(len(sample) - 2) if sample[i:i + 3] in grams)
    return hits, max(1, len(sample) - 2)


def generate(p, tok, text, prompt, n_tokens, temperature, seed=7):
    rng = random.Random(seed)
    ids = encode(prompt, tok)
    T = CONFIG["block_size"]
    for _ in range(n_tokens):
        ctx = ids[-T:]
        ctx = [0] * (T - len(ctx)) + ctx
        _, st = forward(p, [ctx], None)
        # forward flattens B rows of T positions into B*T rows, so the last row *is* the next token's
        # distribution over the whole vocabulary.
        last = st["logits"][-1]
        if temperature <= 0:
            nxt = max(range(len(last)), key=lambda i: last[i])
        else:
            pr = softmax([x / temperature for x in last])
            u, acc, nxt = rng.random(), 0.0, len(pr) - 1
            for i, w in enumerate(pr):
                acc += w
                if u <= acc:
                    nxt = i
                    break
        ids.append(nxt)
    return decode(ids, tok)


# --------------------------------------------------------------------------- checkpoint
def _round(v, sig):
    if isinstance(v, dict):
        return {k: _round(x, sig) for k, x in v.items()}
    if isinstance(v, list):
        return [_round(x, sig) for x in v]
    return float("%.*g" % (sig, v)) if math.isfinite(v) else v


def blob(p):
    return json.dumps({"config": CONFIG, "params": p}, separators=(",", ":"), sort_keys=True)


def save_params(p, path, sig=None):
    data = blob(_round(p, CONFIG["ckpt_sig_digits"] if sig is None else sig))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    return hashlib.sha256(data.encode("utf-8")).hexdigest(), len(data)


def load_params(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["params"]


def default_ckpt():
    return os.path.join(HERE, "weights_alice.json")


def eprint(*a):
    """Machine-dependent readings (wall clock, throughput) go to stderr, never into stdout."""
    print(*a, file=sys.stderr)


def pad(s, w):
    """Right-pad to *display* width. The records are pasted into a monospace block, where a CJK
    glyph occupies two cells -- `%-20s` counts code points and leaves every Chinese table crooked."""
    width = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)
    return s + " " * max(0, w - width)


def utf8_out():
    """Force UTF-8 on both streams: the committed transcripts are UTF-8 and the judge decodes them
    as UTF-8, while this machine's console default is cp936, which would mangle every CJK label."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
