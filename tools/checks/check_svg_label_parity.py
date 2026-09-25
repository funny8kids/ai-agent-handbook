# -*- coding: utf-8 -*-
"""Prove that redrawing a hand-made SVG deleted no reader-visible text.

A redraw legitimately splits long labels across lines (JSON pretty-print, a two-row status bar) and
may drop the "·" that merely separated two fields once each got its own line. So the hard gate is a
character multiset over *content* glyphs (separators excluded): every glyph painted before must
still be painted somewhere in the new figure.

A rename is a real content change and gets no free pass: it must appear in REWRITES below, the new
wording must actually be present, and the tool prints every rewrite it used. That keeps "I had to
reword it" from becoming the escape hatch that lets a redraw quietly shrink a page.

    python tools/checks/check_svg_label_parity.py                     # every asset changed vs HEAD
    python tools/checks/check_svg_label_parity.py --against HEAD~3
    python tools/checks/check_svg_label_parity.py 11-observability-ui.svg
    python tools/checks/check_svg_label_parity.py --selftest          # instrument before verdict

Exits 1 if any figure dropped a glyph. Nothing about a redraw is "done" until this reads clean.
"""
import argparse
import io
import os
import re
import subprocess
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(REPO, "docs", ".gitbook", "assets")
OUT = os.path.join(REPO, ".tmp-projects", "svg_label_parity.txt")

# old wording -> new wording, with the reason the old one could not survive verbatim.
REWRITES = [
    ("侧板", "底部检查器", "面板从右栏移到底部抽屉：留着「侧板」就对读者说了假话"),
    # The cover banner prints the corpus's page count twice, and that count is a claim about the
    # tree — round 97 added six interview pages, so both labels moved together. The number's honesty
    # is owned by `check_readme_stats.py` (it re-derives the banner badges from the tree); this
    # registry only records that the redraw changed wording rather than losing it.
    ("从原理到生产205页20章", "从原理到生产211页20章", "封面横幅的页数徽章随树走：第 97 轮新增六页面试真题"),
    ("20章205页全景", "20章211页全景", "同一枚徽章在横幅里的第二处画法，与上一行同轮一起改"),
]

SEPARATORS = "·/—-→（）()[]{}:：,，。.、;；!！?？\"'“”‘’|+×"


def norm(text):
    text = (text.replace("&amp;", "&").replace("&lt;", "<")
                .replace("&gt;", ">").replace("&quot;", '"'))
    text = re.sub(r"<[^>]+>", "", text)                       # nested tspans / inline tags
    text = re.sub("[" + re.escape(SEPARATORS) + "]", "", text)
    return re.sub(r"\s", "", text)                            # whitespace, not the letter s


def labels(source):
    return [norm(m.group(1)) for m in re.finditer(r"<text\b[^>]*>(.*?)</text>", source, re.S)]


def diff(old_labels, new_labels):
    """Return (unexplained dropped glyphs, rewrites used)."""
    old, new = "".join(old_labels), "".join(new_labels)
    dropped = Counter(old) - Counter(new)
    used = []
    for src, dst, _why in REWRITES:
        if src not in old or dst not in new:
            continue                                          # this figure never had that wording
        dropped -= Counter(norm(src)) - Counter(norm(dst))
        used.append((src, dst))
    return {k: v for k, v in dropped.items()}, used


def git_show(rev, name):
    r = subprocess.run(["git", "show", "%s:docs/.gitbook/assets/%s" % (rev, name)],
                       cwd=REPO, capture_output=True)
    if r.returncode:
        return None                                           # new asset: nothing was deleted yet
    return r.stdout.decode("utf-8")


def changed_vs(rev):
    r = subprocess.run(["git", "diff", "--name-only", "%s" % rev, "--", "docs/.gitbook/assets"],
                       cwd=REPO, capture_output=True)
    if r.returncode:
        raise SystemExit("git diff %s failed: %s" % (rev, r.stderr.decode("utf-8", "replace")))
    return [os.path.basename(p) for p in r.stdout.decode("utf-8").split() if p.endswith(".svg")]


def selftest():
    """The gate must be able to say NO: prove it on planted counterexamples."""
    assert norm("span 树 · 1（秒）") == "span树1秒", norm("span 树 · 1（秒）")
    log = ["normalizer ok: whitespace and separators go, the letter s stays"]
    a = ["搜索找回运行", "侧板核对该span的输入输出", "命中1284条"]
    ok = ["搜索找回运行", "底部检查器核对该span的输入输出", "命中1,284条", "按traceid搜索"]
    d, used = diff(a, ok)
    assert not d, "declared rewrite still reads as a deletion: %s" % d
    assert used == [("侧板", "底部检查器")], used
    log.append("control 1 ok: declared rewrite + a re-flowed separator reads clean")
    for name, bad in [("dropped a whole clause", ["搜索找回运行", "命中1284条"]),
                      ("shortened a label", ["搜索找回运行", "侧板核对输入输出", "命中1284条"]),
                      ("used an undeclared rename", ["搜索找回运行", "抽屉核对该span的输入输出", "命中1284条"]),
                      ("lost a latin word", ["搜索找回运行", "侧板核对该的输入输出", "命中1284条"])]:
        d, _used = diff(a, bad)
        assert d, "gate is blind to %s" % name
        log.append("counterexample ok: %-22s -> dropped=%s" % (name, "".join(sorted(d))))
    # an instrument that can never fail is worse than no instrument
    d, _u = diff(a, a)
    assert not d
    log.append("identity ok: unchanged labels drop nothing")
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--against", default="HEAD")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    lines = selftest()
    if args.selftest:
        _write(OUT.replace(".txt", "-selftest.txt"), lines)
        return 0

    names = args.names or changed_vs(args.against)
    if not names:
        print("no SVG changed against %s — nothing to audit" % args.against)
        return 0
    lines.append("")
    bad = 0
    for name in names:
        old_src = git_show(args.against, name)
        path = os.path.join(ASSETS, name)
        if not os.path.exists(path):
            lines.append("%-32s DELETED FROM TREE — a figure cannot be removed to pass an axis" % name)
            bad += 1
            continue
        if old_src is None:
            lines.append("%-32s new asset (no %s copy) — not auditable" % (name, args.against))
            continue
        old, new = labels(old_src), labels(io.open(path, encoding="utf-8").read())
        dropped, used = diff(old, new)
        stream = "".join(new)
        lines.append("%-32s labels %d->%d  deleted-glyphs=%s  rewrites=%s  split-labels=%d"
                     % (name, len(old), len(new), "".join(sorted(dropped)) or "none",
                        "; ".join("%s->%s" % u for u in used) or "none",
                        len([t for t in old if t and t not in stream])))
        for src, dst in used:
            why = next(w for s, d, w in REWRITES if s == src)
            lines.append("      REWRITE %s -> %s   (%s)" % (src, dst, why))
        for t in old:
            if t and t not in stream:
                lines.append("      SPLIT %s" % t)
        if dropped:
            bad += 1

    lines.append("\nverdict: figures audited=%d  figures that deleted content=%d" % (len(names), bad))
    _write(OUT, lines)
    return 1 if bad else 0


def _write(path, lines):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    io.open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    text = "\n".join(l.encode("ascii", "backslashreplace").decode("ascii") for l in lines)
    try:
        print(text)
    except UnicodeEncodeError:                                # cp1252 console
        print(text.encode("ascii", "backslashreplace").decode("ascii"))
    print("wrote %s" % path)


if __name__ == "__main__":
    sys.exit(main())
