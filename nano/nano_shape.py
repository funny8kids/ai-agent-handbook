# -*- coding: utf-8 -*-
"""第 22 章附录：形状扫描 —— 同一份代码、同一批种子，把候选形状各跑一遍真训练 + 真采样。

这不是逐页复跑物（七个形状一轮要二十来分钟，读者不该为一张表等这么久），它是「为什么冻结配置
长这样」的出处：表里每一行都是 nano_train.py 与 nano_sample.py 在一份临时副本上真跑出来的。
判据只把本文件的 stdout 当作记录逐字回核，不重跑它。

stdout 只打机器无关的列（参数量、loss、3-gram 命中率、判定）；每个形状的实际秒数走 stderr，
因为「这台机器跑多少秒」不能进逐字节复现的那份记录。

一轮跑不完不要紧：每个形状算完就落进行帐（系统临时目录），下次只补没算过的，
`--report` 从行帐把整张表打出来。

Run:  python nano_shape.py             （补算行帐里还缺的形状）
      python nano_shape.py --only 2,5   （只算第 2、5 个候选）
      python nano_shape.py --report     （不跑，只从行帐打表）
"""
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import gptnano as G

G.utf8_out()
HERE = os.path.dirname(os.path.abspath(__file__))
# 行帐落在仓库里（不是系统临时目录）：它是「为什么冻结配置长这样」的持久出处，页面贴的扫描表
# 由它现读现打；读者拿到仓库就能 `--report`，不必为此再跑一小时。
JOURNAL = os.path.join(HERE, "out", "shape_rows.txt")

# 候选形状。全部落在 spec.md 的预算边界内（n_layer<=2, d_model<=40, block_size<=24, steps<=800）。
# 最后一条是本轮之前用过的形状，留在表里作为对照：采样页最差一段就是它量出 40.8% 的那一次。
CANDIDATES = [
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 8, "train_steps": 800, "lr": 0.025},
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 8, "train_steps": 700, "lr": 0.030},
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 6, "train_steps": 800, "lr": 0.030},
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 4, "train_steps": 800, "lr": 0.035},
    {"d_model": 8, "d_ff": 16, "block_size": 24, "batch_size": 8, "train_steps": 800, "lr": 0.030},
    {"d_model": 12, "d_ff": 24, "block_size": 20, "batch_size": 8, "train_steps": 700, "lr": 0.030},
    {"d_model": 24, "d_ff": 64, "block_size": 20, "batch_size": 4, "train_steps": 300, "lr": 0.030},
    # 第二批：第一批 7 个形状的最差一段全在 60% 线下（最好 58.3%），而绊住的永远是温度 1.0 那四条腿。
    # 于是围着「预算内最省的步数」扫学习率与退火尾巴——lr 越高、尾段越冷，权重越尖，抽样越不容易离轨。
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 8, "train_steps": 700, "lr": 0.035},
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 8, "train_steps": 700, "lr": 0.045},
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 8, "train_steps": 600, "lr": 0.045,
     "warmup_steps": 60},
    {"d_model": 12, "d_ff": 24, "block_size": 24, "batch_size": 8, "train_steps": 700, "lr": 0.035,
     "min_lr_frac": 0.02},
]

# 锚点全部照抄 nano_train.py / nano_sample.py 里真实打印的行，不自己造句。
TAIL_MEAN = re.compile(r"末段均值 = ([\d.]+)\s+达标线 = ([\d.]+)\s+判定 = (\w+)")
HOLDOUT = re.compile(r"留出集 loss = ([\d.]+)\s+困惑度 = ([\d.]+)")
PARAMS = re.compile(r"参数量 (\d+)\s+词表")
ARM = re.compile(r"3-gram 命中语料 \d+/\d+ = ([\d.]+)%")
WORST = re.compile(r"最差一段 ([\d.]+)% -> (\w+)")
TEMP_MIN = re.compile(r"温度 1\.0 最低 ([\d.]+)%")
SECS = re.compile(r"总耗时 ([\d.]+) 秒")


def shape_of(c):
    label = "d%-3d df%-3d T%-2d B%-d steps%-4d lr%-6g" % (
        c["d_model"], c["d_ff"], c["block_size"], c["batch_size"], c["train_steps"], c["lr"])
    extra = [k for k in sorted(c) if k not in
             ("d_model", "d_ff", "block_size", "batch_size", "train_steps", "lr")]
    return label + ("".join(" %s=%g" % (k, c[k]) for k in extra) if extra else "")


def measure(c):
    """把三份真脚本复制进临时目录，追加一行 CONFIG.update()，然后原样跑训练与采样。"""
    tmp = tempfile.mkdtemp(prefix="nano_shape_")
    try:
        for name in ("gptnano.py", "nano_train.py", "nano_sample.py"):
            shutil.copyfile(os.path.join(HERE, name), os.path.join(tmp, name))
        with open(os.path.join(tmp, "gptnano.py"), "a", encoding="utf-8") as f:
            f.write("\nCONFIG.update(%r)\n" % c)
        t0 = time.time()
        tr = subprocess.run([sys.executable, "nano_train.py"], cwd=tmp, capture_output=True,
                            text=True, encoding="utf-8")
        assert tr.returncode == 0, "nano_train 失败 %s:\n%s" % (shape_of(c), tr.stderr[-800:])
        secs = time.time() - t0
        t1 = time.time()
        sa = subprocess.run([sys.executable, "nano_sample.py"], cwd=tmp, capture_output=True,
                            text=True, encoding="utf-8")
        assert sa.returncode == 0, "nano_sample 失败 %s:\n%s" % (shape_of(c), sa.stdout[-800:])
        ssecs = time.time() - t1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = tr.stdout + sa.stdout
    got = {k: r.search(out) for k, r in (("tail", TAIL_MEAN), ("hold", HOLDOUT), ("par", PARAMS),
                                         ("worst", WORST), ("temp", TEMP_MIN))}
    for key, m in got.items():
        assert m, "训练/采样记录里没有 %s 那一行（%s）" % (key, shape_of(c))
    arms = [float(a) for a in ARM.findall(out)]
    assert len(arms) == 8, "期望 8 段命中率，实际 %d（%s）" % (len(arms), shape_of(c))
    ms = SECS.search(tr.stderr)
    assert ms, "stderr 里没有总耗时那一行"
    G.eprint("  %-30s 训练 %.1f 秒 + 采样 %.1f 秒 -> 总耗时 %s 秒（预算 %.0f）" % (
        shape_of(c), secs, ssecs, ms.group(1), G.BUDGET_S))
    return "|".join([shape_of(c), str(int(got["par"].group(1))), got["tail"].group(1),
                     got["tail"].group(3), got["hold"].group(1), got["hold"].group(2),
                     got["temp"].group(1), got["worst"].group(1), got["worst"].group(2),
                     " ".join("%.1f" % a for a in arms)])


def read_journal():
    rows = {}
    if os.path.isfile(JOURNAL):
        with open(JOURNAL, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 11:          # 1 row index + the 10 fields measure() returns
                    rows[int(parts[0])] = parts[1:]
    return rows


def append_journal(i, body):
    rows = read_journal()
    rows[i] = body.split("|")        # store fields, not the raw line: joining a str re-splits it
    with open(JOURNAL, "w", encoding="utf-8") as f:
        for n in sorted(rows):
            f.write("%d|%s\n" % (n, "|".join(rows[n])))
    back = read_journal()
    assert back.get(i) == rows[i], "行帐写回读不出来：第 %d 行" % i


def report(rows):
    print("形状扫描：每个形状都是 nano_train.py + nano_sample.py 在临时副本上真跑（同一批种子、同一个语料）")
    print("冻结的达标线：末段 loss <= 0.70 x ln V = %.6f，最差一段 3-gram 命中率 >= 60.0%%，训练预算 %.0f 秒" % (
        0.70 * math.log(36), G.BUDGET_S))
    print()
    print("%-33s %6s %8s %8s %8s %8s %s" % ("形状", "参数量", "末段loss", "留出loss",
                                            "温度最低", "最差一段", "两条线"))
    passed = []
    for i in sorted(rows):
        shape, par, tail, tail_ok, hold, ppl, temp, worst, worst_ok, _arms = rows[i]
        ok = "过" if (tail_ok == "OK" and float(worst) >= 60.0) else "MISS"
        if ok == "过":
            passed.append(shape.strip())
        print("%-33s %6s %8s %8s %7s%% %7s%% %s" % (
            shape, par, tail, hold, temp, worst, ok))
    print()
    print("逐段 3-gram 命中率（前 4 段贪心、后 4 段温度 1.0，同一个提示配对）")
    for i in sorted(rows):
        print("  %-33s %s" % (rows[i][0], rows[i][9]))
    print()
    print("实际秒数在 stderr（机器相关，不进这份记录）；预算判定由判据自己计时")
    print("两条线都过的形状: %s" % ("；".join(passed) if passed else "无"))


if "--report" in sys.argv:
    rows = read_journal()
    assert len(rows) == len(CANDIDATES), "行帐只有 %d/%d 个形状，还不能出表" % (
        len(rows), len(CANDIDATES))
    report(rows)
    sys.exit(0)

want = list(range(1, len(CANDIDATES) + 1))
if "--only" in sys.argv:
    want = [int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")]
have = read_journal()
for i in want:
    if i in have:
        G.eprint("[%d] %s 已在行帐，跳过" % (i, shape_of(CANDIDATES[i - 1])))
        continue
    G.eprint("[%d/%d] %s" % (i, len(CANDIDATES), shape_of(CANDIDATES[i - 1])))
    append_journal(i, measure(CANDIDATES[i - 1]))

rows = read_journal()
G.eprint("行帐进度: %d/%d" % (len(rows), len(CANDIDATES)))
if len(rows) == len(CANDIDATES):
    report(rows)
