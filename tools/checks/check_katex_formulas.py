"""Render every authored formula through real KaTeX and fail on any that throws.

Why this file exists: README declares one authoritative formula judge (「公式数只认这一个判据
脚本」) but that judge had never been committed — it was assembled in a temp directory each
round and evaporated, which is how the same tree ended up reading 811 / 821 / 834 in three
places. This lands it, and it reuses live_aria_manifest.formula_sources() so the count on this
line and the count the live parity axis compares against the served HTML are the same number
by construction, not by agreement.

KaTeX itself is not committed, but the version is pinned: README quotes a specific build, so a
run against any other build must not print numbers. Round 59 measured why the pin cannot be an
alignment check like the Mermaid axis has — the published HTML carries no KaTeX version at all
(the string "katex" appears only in the class names katex / katex-display / katex-html /
katex-mathml), so there is nothing on the site to read a version off. Pinning locally is the
strongest honest claim. The bundle lives in tools/checks/data/katex (package.json committed,
node_modules ignored); if nothing resolves, this judge exits with code 2 and says so — a missing
renderer must never read as "0 failures".

The last assertion is the one that matters most: a deliberately broken formula is appended and
must be the only failure. Without it, "failures=0" could mean the renderer never ran.

Usage:
    python tools/checks/check_katex_formulas.py [--katex-dir PATH]
    python tools/checks/check_katex_formulas.py --selftest   # the raw-$ predicate's controls only

The second leg is not about KaTeX failing to parse — it is about markup KaTeX never gets. A single
`$...$` span is invisible to the render below (this file's own tokenizer only pairs `$$`), so the
one way to catch it is to read the authored page and ask whether the author meant math.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
FLAGS = ("--katex-dir", "--selftest")
RENDERER = os.path.join(HERE, "katex_render.mjs")
sys.path.insert(0, HERE)
import live_aria_manifest as L  # noqa: E402  (shared tokenizer: one definition of "authored")
from flag_guard import reject_unknown  # noqa: E402  an unparsed flag must not fall through

PHANTOM = "\\frac{1}{"            # must be the only failure, proving the renderer fires
# The build README quotes. An off-version run is a tool failure, not a reading: round 59 found a
# 0.16.47 bundle resolving off the default path and printing failures=0 beside that claim.
KATEX_VERSION = "0.18.7"
BUNDLED = os.path.join(HERE, "data", "katex")


def katex_dir(arg):
    """The pinned bundle's parent directory, or None if it was never installed."""
    if arg:
        return arg
    return BUNDLED if os.path.isdir(os.path.join(BUNDLED, "node_modules", "katex")) else None


def collect():
    items, pages, scanned, raw, unrendered = [], 0, 0, [], []
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir.startswith("14-templates"):
            continue                                 # template pages quote markup, per README
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            scanned += 1
            for ln, span in L.raw_dollar_math(text):
                raw.append((rel, ln, span))
            for kind, ln, frag in L.math_in_unrendered_place(text):
                unrendered.append((rel, ln, kind, frag))
            sources, _ = L.formula_sources(text)
            if not sources:
                continue
            pages += 1
            for kind, src in sources:
                items.append({"page": rel, "kind": kind, "src": src})
    return pages, items, scanned, raw, unrendered


def raw_leg(scanned, raw):
    """Every authored page must ask for math the way the platform reads math.

    The count that has to be read is `scanned=N`: this leg is only a claim if it walked the corpus,
    and the page it failed to cover -- an inline-only formula page -- is exactly the one round 101
    shipped raw `$\\ln V$` markup through.
    """
    assert scanned >= 200, ("vacuity floor: the raw-$ sweep walked %d pages, fewer than a whole book "
                            "-- it is judging a subset it cannot name" % scanned)
    print("raw-$ math: scanned=%d spans=%d (single-$ math never renders on this platform)"
          % (scanned, len(raw)))
    for rel, ln, span in raw[:40]:
        print("  - RAWDOLLAR %s:%d $%s$ -> $$%s$$" % (rel, ln, span.strip(), span.strip()))
    return len(raw)


def unrendered_leg(scanned, hits):
    """A formula the renderer never reaches is not a formula, wherever its delimiters are.

    The companion of the raw-$ leg: that one asks "did the author use the delimiter this platform
    reads", this one asks "is that delimiter somewhere the platform does not render at all". Headings
    are re-printed raw into the page's own table of contents (round 90 and round 94 both measured
    characters surviving there that the body renderer consumes), and a link label carrying math has
    zero precedent in 424 formula-bearing body lines -- round 102's own edit was about to become the
    first, on a question nobody had measured.
    """
    assert scanned >= 200, ("vacuity floor: the unrendered-place sweep walked %d pages, fewer than a "
                            "whole book -- it is judging a subset it cannot name" % scanned)
    print("math in an unrendered place: scanned=%d hits=%d (heading text is re-printed raw into the "
          "page TOC; link labels have no precedent for math in this corpus)" % (scanned, len(hits)))
    for rel, ln, kind, frag in hits[:40]:
        print("  - UNRENDERED %s:%d %s %r -> put it in inline code instead" % (rel, ln, kind, frag))
    return len(hits)


BADGE = re.compile(r"\*\*(\d+) 篇页面含 KaTeX 公式，共 (\d+) 条\*\*")
HOMEPAGE = os.path.join(REPO, "docs", "README.md")


def homepage_badge(text, pages, formulas):
    """The front page quotes this judge's two numbers, so this judge reads them back out.

    「公式数只认这一个判据脚本」was written on the strength of the script being in the repo, but the
    sentence quoting 121 / 1052 was still a hand-copy: round 101 measured that a page count can move
    by writing prose (this round's raw-$ fix alone takes it 121 → 128, because seven pages that
    authored markup the tokenizer ignored now author formulas). Same shape as the link-graph and
    widget badges: parse the shipped sentence, compare, and treat a missing sentence as a coverage
    failure rather than a pass.
    """
    m = BADGE.search(L.prose(text))
    if not m:
        print("  - HOMEPAGE-BLIND docs/README.md no longer carries 「N 篇页面含 KaTeX 公式，共 M 条」;"
              " the sentence this judge is quoted by is gone")
        return 1
    want_pages, want_formulas = int(m.group(1)), int(m.group(2))
    if (want_pages, want_formulas) != (pages, formulas):
        print("  - HOMEPAGE-BADGE docs/README.md quotes %d 篇 / %d 条, this tree reads %d / %d"
              % (want_pages, want_formulas, pages, formulas))
        return 1
    print("homepage badge: pages=%d formulas=%d matches the front page" % (pages, formulas))
    return 0


def selftest():
    """Differential controls for raw_dollar_math and for the front-page badge.

    Both directions are planted: a math span injected into a real page must be the one finding, and
    the corpus's real currency lines must stay silent. Without the second half, a detector that just
    reports nothing would also pass.
    """
    pages, items, scanned, raw, unrendered = collect()
    assert not raw, "the sweep is already red, so a planted control cannot read as +1: %s" % raw[:3]
    assert not unrendered, "the place sweep is already red: %s" % unrendered[:3]
    # the exact pages that carry money in prose: they are the predicate's real negative examples
    money = [r for r in sorted(os.listdir(DOCS)) if r.startswith(("16-", "18-"))]
    for d in money:
        dp = os.path.join(DOCS, d)
        for dirpath, _, files in os.walk(dp):
            for fn in files:
                if fn.endswith(".md"):
                    text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
                    assert not L.raw_dollar_math(text), "%s carries prices and must read clean" % fn
    planted_cases = [
        # the shapes chapter 22 actually shipped before this fix: all must be caught
        ("未训练 loss 落在 $\\ln V$ 的 2% 里", 1),
        ("查询位置 $t$ 只能看 $0..t$", 2),
        ("冻结配置是 $T^*=48$，每层 $8d=96$ 个参数", 2),
        ("一块里三个投影并成一次乘加 $3d = 36$ 列，$qkv$ 与 $dV$ 同理", 3),
        ("激活本来就小（$d=12$），固定 $\\epsilon$ 除以 $\\sqrt{\\sigma^2+\\epsilon}$", 3),
        ("写法松掉的 $ \\ln V $ 同样是字面量", 1),
        ("行内代码里的 `$\\ln V$` 不算公式", 0),
        # the spans chapters 16/18 really contain (prices): every one must stay silent
        ("一个任务毛成本 $1193.67 掉到 $683.38，省 42.8%", 0),
        ("| 标准价 | $10 / $50 | $10 / $50 | 随档位 |", 0),
        ("厂商自报 $0.0077 vs $0.00035**，总计 **", 0),
        ("每千个成功任务 $1193.67 / 千成功任务。命中率", 0),
    ]
    for text, want in planted_cases:
        got = len(L.raw_dollar_math(text))
        assert got == want, "control %r reads %d, wants %d" % (text[:34], got, want)
    # the mutation runs through the same function the judgment runs through, on a real page
    victim = os.path.join(DOCS, "22-build-llm-from-scratch", "build-05-train.md")
    base = io.open(victim, encoding="utf-8").read()
    assert not L.raw_dollar_math(base), "the victim page is not clean, so +1 is unmeasurable"
    mutated = base.replace("\n## ", "\n未训练 loss 落在 $\\ln V$ 的 2% 里。\n\n## ", 1)
    assert mutated != base, "the mutation did not land on the victim page"
    hits = L.raw_dollar_math(mutated)
    assert len(hits) == 1 and hits[0][1] == "\\ln V", "planted span read as %s" % hits
    # the same differential for the second new leg: four shapes must fire, four must not
    place_cases = [
        ("## 交叉熵的起点就是 $$\\ln V$$", [("HEADING", "交叉熵")]),
        ("- [交叉熵与反向：$$\\ln V$$ 的来历](build-04-backward.md)", [("LINK-LABEL", "交叉熵")]),
        ("| [前向](build-02-forward.md) | 未训练 loss 与 $$\\ln V$$ 差 ≤ 2% |", []),
        ("见 $$x\\cdot\\Phi(x)$$ 一节，正文里的公式当然算。", []),
        ("## 用 `$$…$$` 包住才算展示公式", []),
        ("## 一个没有公式的标题", []),
        ("`$$\\ln V$$` 只是把写法写在行内代码里", []),
        ("围栏里的 $$ 不算：\n\n```text\n## 标题 $$x$$\n```\n", []),
    ]
    for text, want in place_cases:
        got = [(kind, frag) for kind, _ln, frag in L.math_in_unrendered_place(text)]
        assert len(got) == len(want) and all(g[0] == w[0] and w[1] in g[1] for g, w in zip(got, want)), \
            "place control %r reads %s, wants %s" % (text[:34], got, want)
    # and the real-page mutation: the four places this round moved OUT of are put back into one
    victim2 = os.path.join(DOCS, "22-build-llm-from-scratch", "build-04-backward.md")
    base2 = io.open(victim2, encoding="utf-8").read()
    assert base2.count("## 交叉熵的起点就是 `ln V`") == 1, "the heading this control re-math-ifies is gone"
    mutated2 = base2.replace("## 交叉熵的起点就是 `ln V`", "## 交叉熵的起点就是 $$\\ln V$$", 1)
    hits2 = L.math_in_unrendered_place(mutated2)
    assert len(hits2) == 1 and hits2[0][0] == "HEADING", "planted heading read as %s" % hits2
    # the front page's equation, all three branches, on the real README's own text. The numbers are
    # substituted rather than asserted: --selftest judges the parser and the comparison, while the
    # default run is what holds the shipped sentence to this tree.
    home = io.open(HOMEPAGE, encoding="utf-8").read()
    quoted = BADGE.search(L.prose(home))
    assert quoted, "docs/README.md carries no 「N 篇页面含 KaTeX 公式，共 M 条」 to control against"
    matched = home.replace(quoted.group(0), "**%d 篇页面含 KaTeX 公式，共 %d 条**" % (pages, len(items)))
    assert homepage_badge(matched, pages, len(items)) == 0, "the judge disagrees with its own numbers"
    for label, probe in (("off-by-one", home.replace(quoted.group(0),
                                                    "**%d 篇页面含 KaTeX 公式，共 %d 条**" % (pages, len(items) - 1))),
                         ("deleted", home.replace(quoted.group(0), "若干公式"))):
        assert homepage_badge(probe, pages, len(items)) == 1, "the %s front page read as clean" % label
    print("katex controls: OK (raw-$ planted=%d cases, unrendered-place planted=%d cases, "
          "badge controls=3, corpus spans=%d, corpus places=%d, scanned=%d, formula items=%d, pages=%d)"
          % (len(planted_cases) + 1, len(place_cases), len(raw), len(unrendered), scanned, len(items), pages))
    return 0


def main():
    args = sys.argv[1:]
    if reject_unknown(args, FLAGS, "check_katex_formulas"):
        return 2
    if "--selftest" in args:
        return selftest()
    kdir = katex_dir(args[args.index("--katex-dir") + 1] if "--katex-dir" in args else None)
    pages, items, scanned, raw, unrendered = collect()
    raw_problems = raw_leg(scanned, raw)
    place_problems = unrendered_leg(scanned, unrendered)
    # before the renderer, so a missing KaTeX bundle cannot swallow the front page's own equation
    badge_problems = homepage_badge(io.open(HOMEPAGE, encoding="utf-8").read(), pages, len(items))
    payload = items + [{"page": "<self-test>", "kind": "display", "src": PHANTOM}]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
        path = fh.name
    env = dict(os.environ)
    if kdir:
        env["KATEX_REQUIRE_FROM"] = kdir
    try:
        proc = subprocess.run(["node", RENDERER, path], capture_output=True, text=True, env=env)
    finally:
        os.unlink(path)
    if proc.returncode == 2:
        print("katex render: SKIPPED — %s" % json.loads(proc.stdout or "{}").get("skip", proc.stderr[:200]))
        print("  install the pinned build once:\n    npm install katex@%s --prefix %s\n"
              "  or pass --katex-dir <dir containing node_modules/katex>" % (KATEX_VERSION, BUNDLED))
        return 2
    if proc.returncode != 0:
        print("katex render: RUNNER FAILED rc=%d\n%s" % (proc.returncode, proc.stderr[:800]))
        return 1
    out = json.loads(proc.stdout)
    if out["version"] != KATEX_VERSION:
        print("katex render: OFF-VERSION — resolved %s, this judge is quoted as katex@%s. "
              "Not emitting numbers: README's formula count is only true for the pinned build."
              % (out["version"], KATEX_VERSION))
        return 2
    real, planted = [f for f in out["failures"] if f["i"] < len(items)], \
                    [f for f in out["failures"] if f["i"] >= len(items)]
    assert len(items) > 500, "vacuity floor: fewer than 500 formulas means the scan missed pages"
    assert planted, "self-test: the planted %r was NOT caught, so a clean run would prove nothing" % PHANTOM
    assert out["total"] == len(payload), "the renderer lost items"
    print("katex render: pages=%d formulas=%d failures=%d version=%s (planted counterexample caught: 1)"
          % (pages, len(items), len(real), out["version"]))
    for f in real[:40]:
        it = items[f["i"]]
        print("  - %s [%s] %s :: %s" % (it["page"], it["kind"], it["src"].strip().replace("\n", " ")[:70], f["msg"]))
    if raw_problems or place_problems or badge_problems:
        print("VERDICT: FAIL — raw-$=%d, unrendered-place=%d, homepage badge=%d, render failures=%d "
              "(a single-$ formula, or a $$ inside a heading or link label, reaches the reader as "
              "literal markup)"
              % (raw_problems, place_problems, badge_problems, len(real)))
        return 1
    if real:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
