"""Fail if the same sentence or the same display formula is printed verbatim on two different pages.

Why this file exists: every earlier dedup (rounds 52 and 56) was hand-targeted — someone noticed a
repeated block, patched those two pages, and moved on. `tools/checks/` had no pairwise judge, so a
new duplicate added in any round was invisible to every axis. This is that judge.

Scope, and why each exclusion is an exclusion and not a loophole:
  * `docs/00-index/` — the changelog quotes other pages on purpose.
  * `SUMMARY.md` — `check_nav_h1_sync.py` *requires* its label to equal each page's H1, so every
    SUMMARY pair is mandated by another axis.
  * the `参考资料` / `相关知识点` sections — a citation legitimately appears on every page that uses it.
  * link text — after stripping `[label](url)` a page title no longer counts as prose, otherwise
    every index page "duplicates" the H1 it links to.
  * units shorter than 14 characters (prose) / 10 (formula) — terms, not sentences.

Two passes, because one alone has a blind spot. The NEAR pass runs an inverted index over char
6-grams and skips shingles shared by more than 25 units, which keeps it out of quadratic blowup but
would go silent on a sentence duplicated across 30 pages. The EXACT pass hashes whole normalized
units and has no cap, so the mass-duplicate case is still caught. Both passes cross pages only: a
repeated sentence *inside* one page belongs to a different axis.

Usage:
    python tools/checks/check_prose_duplicates.py            # counts + top offenders
    python tools/checks/check_prose_duplicates.py --top 30    # wider triage dump
"""
import io
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")

SKIP_DIRS = (".git", "assets", "node_modules")
SKIP_PATH_HINTS = (os.path.join("00-index",), "SUMMARY.md")
SKIP_SECTIONS = ("参考资料", "相关知识点")
FENCE = re.compile(r"^[ \t]*(```|~~~)")
INLINE_MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+\$")
MIN_PROSE, MIN_FORMULA = 14, 10
NEAR_T, ADVISORY_T, HOT = 0.85, 0.72, 25


def norm(s):
    """Keep only CJK + alphanumerics: punctuation and LaTeX sugar must not hide a duplicate."""
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", s)


def units(text):
    """Yield (kind, normalized) for prose sentences and display formulas, in reading order."""
    lines = text.split("\n")
    i = 0
    if lines and lines[0].strip() == "---":
        while i + 1 < len(lines) and lines[i + 1].strip() != "---":
            i += 1
        i += 2
    infence, skip, inmath, buf = False, False, False, []
    for line in lines[i:]:
        if FENCE.match(line):
            infence = not infence
            continue
        if infence or line.strip().startswith("<!--"):
            continue
        s = line.strip()
        if s.startswith("## "):
            section = s[3:]
            skip = any(k in section for k in SKIP_SECTIONS)
            continue
        if skip:
            continue
        if s == "$$":                      # display math usually spans several lines: collect it
            if inmath:
                yield ("formula", norm(" ".join(buf)))
                buf, inmath = [], False
            else:
                inmath = True
            continue
        if inmath:
            buf.append(s)
            continue
        if len(s) > 4 and s.startswith("$$") and s.endswith("$$"):
            yield ("formula", norm(s[2:-2]))
            continue
        if not s or s.startswith(("#", "|", ">")):
            continue
        body = INLINE_MATH.sub(" ", s)     # inline math is not prose — `$\longrightarrow$` matched
        for pattern in (r"<[^>]+>", r"\{[%#][^}]*[%#]\}", r"`[^`]*`", r"!?\[[^\]]*\]\([^)]*\)"):
            body = re.sub(pattern, " ", body)
        body = re.sub(r"^[-*+]\s+|^\d+[.)]\s+", "", body)
        for chunk in re.split(r"[。；;]", body):
            u = norm(chunk)
            if len(u) >= MIN_PROSE:
                yield ("prose", u)


def shingles(s, n=6):
    return {s[i:i + n] for i in range(len(s) - n + 1)} if len(s) >= n else {s}


def pages(root=DOCS):
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            p = os.path.join(base, f)
            if any(h in p for h in SKIP_PATH_HINTS):
                continue
            try:
                rel = os.path.relpath(p, REPO)
            except ValueError:                      # a root on another drive has no relative path
                rel = p
            out.append((rel, io.open(p, encoding="utf-8").read()))
    return out


def exact_pairs(by_unit):
    """Whole-unit duplicates across pages — no frequency cap, so mass repeats cannot hide."""
    return sorted((u, sorted(ps)) for u, ps in by_unit.items() if len(ps) > 1)


def near_pairs(items, threshold):
    index = defaultdict(list)
    for idx, u in enumerate(items):
        for sh in shingles(u):
            index[sh].append(idx)
    pairs = {}
    for idxs in index.values():
        if len(idxs) > HOT:
            continue
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                i, j = sorted((idxs[a], idxs[b]))
                pairs[(i, j)] = pairs.get((i, j), 0) + 1
    rows = []
    for (i, j), shared in pairs.items():
        sim = shared / len(shingles(items[i]) | shingles(items[j]))
        if sim >= threshold:
            rows.append((sim, i, j))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return rows


def collect(root=DOCS):
    """-> {kind: [(page, unit)]}: one entry per reader-visible unit, cross-page scope applied."""
    per_kind = {"prose": [], "formula": []}
    for rel, text in pages(root):
        for kind, u in units(text):
            if len(u) >= (MIN_FORMULA if kind == "formula" else MIN_PROSE):
                per_kind[kind].append((rel, u))
    return per_kind


def judge(per_kind):
    """-> (findings, advisory, counts). Findings are DUP-EXACT / DUP-NEAR; advisory never fails."""
    findings, advisory = [], []
    counts = {}
    for kind, sel in per_kind.items():
        counts[kind] = len(sel)
        texts = [u for _, u in sel]
        owner = defaultdict(set)
        for p, u in sel:
            owner[u].add(p)
        for u, ps in exact_pairs(owner):
            findings.append("DUP-EXACT %s x%d pages: %s | %s"
                            % (kind, len(ps), u[:70], ", ".join(sorted(ps)[:4])))
        page_of = [p for p, _ in sel]
        for sim, i, j in near_pairs(texts, ADVISORY_T):
            # intra-page repetition belongs to another axis, and an identical unit is already one
            # DUP-EXACT finding — counting it again per pair would inflate the reading 1 -> 3
            if page_of[i] == page_of[j] or texts[i] == texts[j]:
                continue
            if sim >= NEAR_T:
                findings.append("DUP-NEAR %s %.2f: %s || %s | %s | %s"
                                % (kind, sim, page_of[i], page_of[j], texts[i][:50], texts[j][:50]))
            else:
                advisory.append((sim, kind, page_of[i], page_of[j], texts[i], texts[j]))
    return findings, sorted(advisory, key=lambda r: -r[0]), counts


def controls():
    a = "# 甲页\n\n正文段落里的一句话，它讲的是缓存折扣失效会让成本翻倍。\n\n" \
        "## 参考资料\n\n- 正文段落里的一句话，它讲的是缓存折扣失效会让成本翻倍。\n"
    b = "# 乙页\n\n正文段落里的一句话，它讲的是缓存折扣失效会让成本翻倍。\n\n" \
        "$$\n\\text{cost}=c_{\\text{in}}\\cdot T_{\\text{in}}\n  +c_{\\text{out}}\n$$\n"
    c = "# 丙页\n\n正文段落里的一句话，它讲的是缓存折扣失效会让成本翻倍。\n"
    d = "# 丁页\n\n单步 decode 的耗时里 $$\\longrightarrow$$ 只是箭头，不是句子。\n"
    # the scratch corpus lives outside the repo: a judge that writes its controls into the tree
    # could have them picked up by a broad `git add` mid-round
    tmp = tempfile.mkdtemp(prefix="dup_controls_")
    try:
        for name, text in (("a.md", a), ("b.md", b), ("c.md", c), ("d.md", d)):
            io.open(os.path.join(tmp, name), "w", encoding="utf-8").write(text)
        got = collect(tmp)
        findings, advisory, counts = judge(got)
        assert counts["prose"] == 4, \
            ("control: four pages must yield four prose units — the one inside 参考资料 must stay "
             "out of scope, read %d" % counts["prose"])
        exact = [f for f in findings if "DUP-EXACT prose" in f]
        assert len(exact) == 1 and "x3 pages" in exact[0], \
            "control: a sentence on three pages must be one finding naming all three, read %r" % exact
        assert not any("DUP-EXACT formula" in f for f in findings), \
            "control: a formula printed once must not be a finding"
        assert len(got["formula"]) == 1 and "cost" in got["formula"][0][1], \
            "control: a display formula written across three lines must still be read as one unit"
        assert all("丁页" not in f and "只是箭头" not in f for f in findings), \
            "control: inline math must not become a prose unit that matches itself"
        assert len(findings) == 1, \
            ("control: four pages with one planted repeat must yield exactly one finding, read %r"
             % findings)

        # a 6-gram shared by more than the hot-shingle cap must still be caught by the exact pass
        many = "# p%d\n\n这一句被很多页面抄了一遍，它正是热分片上限会漏掉的那种质量缺陷。\n"
        os.makedirs(os.path.join(tmp, "mass"), exist_ok=True)
        for k in range(HOT + 6):
            io.open(os.path.join(tmp, "mass", "p%d.md" % k), "w", encoding="utf-8").write(many % k)
        mass_findings, mass_advisory, _ = judge(collect(os.path.join(tmp, "mass")))
        assert any("DUP-EXACT" in f for f in mass_findings), \
            "control: a sentence repeated past the hot-shingle cap must not read as clean"
        assert not mass_advisory, \
            "control: the shingle cap may drop near-pairs, but it must not invent advisory noise"
        print("controls ok (cross-page exact prose / citation + nav scope / multi-line formula / "
              "inline math is not prose / mass repeat survives the shingle cap)")

    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


HOME_LINE = "check_prose_duplicates.py"


def homepage_parity(counts, text=None):
    """The homepage sentence that cites this axis must cite this axis's own reading (round 99).

    It had drifted: the page still read 「把 191 篇正文」 and `pages=191 prose_units=7414` while this
    judge measured 206 pages / 8572 units -- fifteen pages shipped in rounds 96-98 and not one
    assertion compared that sentence to a run, in the very sentence that documents how the number
    under it went stale before. Page counts do not move when prose is rewritten, so they get
    equality. Unit counts do -- this homepage is inside its own corpus -- so they get a floor: a
    quoted reading may only be left behind by growth, never overstate the current run.
    """
    corpus = text if text is not None else io.open(os.path.join(DOCS, "README.md"),
                                                   encoding="utf-8").read()
    line = next((l for l in corpus.split("\n") if HOME_LINE in l), None)
    if line is None:
        return ["homepage: no sentence cites %s, so its 跨页不重复 claim has no judge" % HOME_LINE]
    errs = []
    cited = ([int(v) for v in re.findall(r"把 (\d+) 篇正文", line)]
             + [int(v) for v in re.findall(r"pages=(\d+)", line)])
    if not cited:
        errs.append("homepage: the page count must be cited as 「把 N 篇正文」 and 「pages=N」 so this "
                    "assertion can check it")
    elif set(cited) != {counts["pages"]}:
        errs.append("homepage: 「%s」 is not this judge's view of %d pages"
                    % (" / ".join(str(c) for c in sorted(set(cited))), counts["pages"]))
    for tag, key in (("prose_units", "prose"), ("formula_units", "formula")):
        got = [int(v) for v in re.findall(tag + r"=(\d+)", line)]
        if not got:
            errs.append("homepage: %s must be cited as 「%s=N」 so this assertion can check it"
                        % (tag, tag))
        elif max(got) > counts[key]:
            errs.append("homepage: 「%s=%d」 overstates this run's %d -- a dated reading may only be "
                        "left behind by growth; re-run after the last word change"
                        % (tag, max(got), counts[key]))
    return errs


def home_control(counts):
    """Every direction of the parity check above must be able to fire, and the bar must be reachable.

    Round 92's lesson, applied one level down: an alarm nobody has seen ring is a comment. The clean
    line is measured against the judge's own reading, so it cannot be an unreachable bar.
    """
    ok = ("%s 把 %d 篇正文；全站读数 pages=%d prose_units=%d formula_units=%d"
          % (HOME_LINE, counts["pages"], counts["pages"], counts["prose"], counts["formula"]))
    assert homepage_parity(counts, ok) == [], \
        ("control P0: a sentence that cites this run's readings must read clean, read %r"
         % homepage_parity(counts, ok))
    stale = ok.replace("把 %d 篇正文" % counts["pages"], "把 191 篇正文")
    assert any("191" in e for e in homepage_parity(counts, stale)), \
        "control P1: a page count left behind by fifteen shipped pages must be named, not waved through"
    over = ok.replace("prose_units=%d" % counts["prose"], "prose_units=%d" % (counts["prose"] + 1))
    assert any("prose_units" in e for e in homepage_parity(counts, over)), \
        "control P2: a quoted unit reading above this run's must be rejected (it claims more than it measured)"
    under = ok.replace("prose_units=%d" % counts["prose"], "prose_units=%d" % (counts["prose"] - 1))
    assert homepage_parity(counts, under) == [], \
        ("control P3: a quoted unit reading below this run's is a dated record, not a defect -- it is "
         "the pages= figure that must stay exact, got %r" % homepage_parity(counts, under))
    blind = ok.replace("pages=%d" % counts["pages"], "pages 若干").replace(
        "把 %d 篇正文" % counts["pages"], "把许多篇正文")
    assert any("must be cited" in e for e in homepage_parity(counts, blind)), \
        "control P4: a sentence that drops the numbers must be rejected, not read as silence"
    assert homepage_parity(counts, "这一句不提任何判据脚本") != [], \
        "control P5: no citation at all is the loudest failure, not a pass"
    print("homepage parity controls ok (P0 satisfiable / P1 stale pages / P2 overstated / "
          "P3 dated floor / P4 dropped numbers / P5 uncited)")


def real_page_mutation_control():
    """Prove the judge still fires at real page density, not just on the synthetic corpus.

    The synthetic controls above cannot see the hot-shingle cap or the advisory band working against
    thousands of units. This copies six shipped pages to a temp dir, plants one sentence on two of
    them, and requires exactly one new finding that names the plant — then requires the delta to go
    back to zero. The assertion is a *delta*, never "these pages are clean": if the corpus grows a
    duplicate elsewhere, the main reading reports it, and a control must not pre-empt that report.
    """
    names = ["03-llm/token-embedding-context.md", "03-llm/inference-quantization-deployment.md",
             "06-memory-rag/rag-basics.md", "06-memory-rag/graphrag.md",
             "10-evaluation-safety/benchmarks.md", "10-evaluation-safety/evaluation-metrics.md"]
    plant = "判据变异控制：这一句被原样搬到两页上，用来确认轴在真实页面密度下会响，而不是只会读零。"
    tmp = tempfile.mkdtemp(prefix="dup_mut_")
    try:
        for n in names:
            dst = os.path.join(tmp, n.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(DOCS, n), dst)
        base = len(judge(collect(tmp))[0])
        for n in (names[3], names[4]):
            path = os.path.join(tmp, n.replace("/", os.sep))
            lines = io.open(path, encoding="utf-8").read().split("\n")
            # plant under the H1 — not at EOF (a page's trailing 相关知识点 section is out of scope by
            # design) and not at line 1 (these pages open with frontmatter, which is skipped too).
            # Both wrong placements were measured: each one read as a false clean.
            at = [k for k, l in enumerate(lines) if l.startswith("# ")]
            assert at, "live mutation: %s has no H1 to plant under" % n
            lines.insert(at[0] + 1, "\n" + plant + "\n")
            io.open(path, "w", encoding="utf-8").write("\n".join(lines))
        mutated = judge(collect(tmp))[0]
        assert len(mutated) == base + 1, \
            ("live mutation: planting one sentence on two real pages must add exactly one finding, "
             "read base=%d now=%d" % (base, len(mutated)))
        assert any("这一句被原样搬到两页上" in f for f in mutated), \
            ("live mutation: the new finding must name the planted sentence — matched on a span "
             "without punctuation, because the judge reports normalized units")
        for n in (names[3], names[4]):
            shutil.copyfile(os.path.join(DOCS, n), os.path.join(tmp, n.replace("/", os.sep)))
        assert len(judge(collect(tmp))[0]) == base, \
            "live mutation: removing the plant must return the axis to its baseline"
        print("live mutation ok (%d -> %d -> %d findings on six shipped pages)"
              % (base, base + 1, base))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 8
    controls()
    real_page_mutation_control()
    findings, advisory, counts = judge(collect())
    assert counts["prose"] >= 4000 and counts["formula"] >= 200, \
        ("vacuity floor: the corpus should carry thousands of prose units and hundreds of formulas, "
         "read prose=%d formula=%d — a judge that reads almost nothing proves nothing"
         % (counts["prose"], counts["formula"]))
    counts["pages"] = len(pages())
    home = homepage_parity(counts)
    home_control(counts)
    for f in findings[:top]:
        print("  " + f)
    print("prose duplicates: pages=%d prose_units=%d formula_units=%d dup=%d near-band(%.2f-%.2f)=%d"
          % (counts["pages"], counts["prose"], counts["formula"], len(findings),
             ADVISORY_T, NEAR_T, len(advisory)))
    for sim, kind, pa, pb, ua, ub in advisory[:top]:
        print("  [%.3f %s] %s || %s | %s | %s" % (sim, kind, pa, pb, ua[:60], ub[:60]))
    for e in home:
        print("  " + e)
    return 1 if (findings or home) else 0


if __name__ == "__main__":
    sys.exit(main())
