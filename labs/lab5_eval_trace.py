# -*- coding: utf-8 -*-
"""Lab 5 评测与可观测：给 Lab1 式 Agent 建"考场 + 行车记录仪"。

三件事，正是第 10/11 章的工程落地：
  1) 测试集 + 断言判定 -> pass@1（回归测试的雏形）
  2) 每次运行记录 span（谁、何时、多久）-> 文本版瀑布图
  3) trace 落盘 JSONL -> 事后可用 jq/pandas 复盘

运行：python lab5_eval_trace.py   （会在当前目录生成 traces.jsonl）
"""
import json
import random
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")  # 防 Windows 控制台 GBK 乱码
random.seed(42)  # 固定随机种子：工具耗时可复现，输出才能和书里对上

# ---------- 被测 Agent：简化版 ReAct，带"性格缺陷"供评测抓出来 ----------

def agent_solve(case):
    """返回 (答案, 步骤列表)。故意让'多跳'用例慢一些，制造可观测性素材。"""
    spans, t0 = [], time.perf_counter()
    for step, name in enumerate(["plan", "tool:search", "tool:calc", "answer"]):
        if name == "tool:calc" and not case["needs_calc"]:
            continue
        dur = random.uniform(0.01, 0.03) if name.startswith("plan") \
            else random.uniform(0.05, 0.15) if "search" in name \
            else random.uniform(0.02, 0.05)
        time.sleep(dur)
        spans.append({"step": name, "start": time.perf_counter() - t0 - dur,
                      "dur": dur})
    ans = case["gold"] if case["id"] != 3 else "4200 万元"  # 用例3故意答错（幻觉）
    return ans, spans

# ---------- 测试集：断言要"可机判"，别写'回答质量好' ----------

CASES = [
    {"id": 1, "q": "甲公司营收？", "needs_calc": False, "gold": "4800 万元"},
    {"id": 2, "q": "乙公司营收换算成万元？", "needs_calc": True, "gold": "6200 万元"},
    {"id": 3, "q": "甲公司半年营收（需除以2）？", "needs_calc": True, "gold": "2400 万元"},
    {"id": 4, "q": "甲公司营收加汇率常识？", "needs_calc": False, "gold": "4800 万元"},
]

def run_suite():
    print("=" * 62)
    print("Lab 5：Agent 评测（pass@1）+ 可观测（span 瀑布 + JSONL trace）")
    print("=" * 62)
    results, all_spans = [], []
    for case in CASES:
        ans, spans = agent_solve(case)
        ok = (ans == case["gold"])
        results.append({"id": case["id"], "q": case["q"], "got": ans,
                        "gold": case["gold"], "pass": ok,
                        "cost_ms": round(sum(s["dur"] for s in spans) * 1000)})
        for s in spans:
            all_spans.append({"case": case["id"], **s})
        with open("traces.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"case": case["id"], "answer": ans,
                                "pass": ok, "spans": spans}, ensure_ascii=False) + "\n")

    # ---- 成绩单 ----
    print("\n--- 成绩单 ---")
    print(f"{'用例':4s} {'判定':4s} {'耗时ms':>6s}  答案 vs 期望")
    for r in results:
        print(f"{r['id']:<4d} {'✓' if r['pass'] else '✗':<4s} {r['cost_ms']:>6d}  "
              f"{r['got']} | {r['gold']}")
    p1 = sum(r["pass"] for r in results) / len(results)
    print(f"\npass@1 = {p1:.0%}（{sum(r['pass'] for r in results)}/{len(results)}）"
          f" —— 低于 100% 的每一个 ✗ 都该沉淀为常驻回归用例")

    # ---- 文本版瀑布图：一眼看出时间花在哪 ----
    print("\n--- trace 瀑布（用例:步骤，条长≈耗时）---")
    tmax = max(s["start"] + s["dur"] for s in all_spans) or 1e-9
    for s in all_spans:
        left = int(s["start"] / tmax * 40)
        bar = "#" * max(1, int(s["dur"] / tmax * 40))
        print(f"  c{s['case']} {s['step']:12s} {' ' * left}|{bar}| {s['dur']*1000:.0f}ms")
    print("\n  观察：search 步占了大头 -> 优化方向是缓存/并行，而不是换更快的模型")
    print("  traces.jsonl 已生成：每行一个用例的完整 span 记录，pandas 可直接读")

if __name__ == "__main__":
    import os
    if os.path.exists("traces.jsonl"):
        os.remove("traces.jsonl")  # 每次干净起跑
    run_suite()
