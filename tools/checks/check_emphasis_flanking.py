"""Can the reader see a stray ``**``? A flanking judge for emphasis the platform never renders.

Round 83 landed `check_prose_survival.py`, and its close-out render of the live
`10-evaluation-safety/hallucination.md` page showed the reader this sentence verbatim:

    这与 RAG 评估里的**忠实度（Faithfulness）**是同一思想。

with the four asterisks standing where bold type should be. The survival axis read that page as
`MISS=0`, and it was right about the words: `LA.norm()` maps every non-alphanumeric, non-CJK
character to a space on BOTH sides of the comparison, so an authored `**` and a leaked `**`
normalize identically. The axis judges "did the text arrive", and a leaked marker is precisely a
case where the text arrives and the markup does not. Nothing in `tools/checks` could see it.

Why the platform refuses to bold it is CommonMark's flanking table, not a GitBook quirk. A
delimiter run can close only if it is *right-flanking*: not preceded by whitespace, and either not
preceded by punctuation or followed by whitespace/punctuation. In `）**是` the closer sits after a
full-width `）` (category Pe) and before a CJK letter, so it is neither, and the pair stays literal.
The mirror case `为**「` cannot open: `「` is punctuation and `为` is not, so the opener is not
left-flanking. Chinese prose that bolds a quoted phrase or a parenthesised term hits both shapes
constantly, which is why the first sweep found 8 published pages and 23 visible markers.

Two legs, because the offline rule is a *prediction* and a prediction needs an oracle:
  - author leg (no network): every `*`/`**` delimiter run in reader-visible prose is classified and
    paired per paragraph. An unpaired run is a marker the reader will see. Fences, inline code,
    display/inline math, link targets and GitBook tag bodies are blanked first, exactly as the
    survival axis blanks them, so a page that *documents* `**` inside code cannot go red.
  - live leg (`--live`): count literal `**` in the reader-visible text of the served page and
    require it to equal the authored prediction for that page. This is the calibration: 23 markers
    on 8 pages measured on 2026-09-25 is what the rule was fitted to, and an author-leg green that
    the live leg contradicts is a tool failure, not a clean.

Out of scope, deliberately: `_`/`__` (the book authors no underscore emphasis and the live sweep
measured `__ = 0`), and single `*`, where a legitimate visible asterisk (`2 * 3`, a footnote mark)
is indistinguishable from a leaked one without intent. Both are named in the printout so a future
round can widen the rule rather than rediscover the gap.
"""
import argparse
import html
import os
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_aria_manifest as LA
import check_prose_survival as PS      # shared tokenizer: the two rulers cannot disagree about prose

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
SKIP_DIRS = PS.SKIP_DIRS

RUN = re.compile(r"(\*+)")
INLINE_CODE = PS.INLINE_CODE
INLINE_MATH = PS.INLINE_MATH
LINK = PS.LINK
TAG = PS.TAG
BLOCK_START = re.compile(r"^(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\[!\[|!\[)")
# A code span, a formula and a link label are WORDS to the renderer, not gaps: the reader's DOM
# holds an atom there (`<code>`, `<span class="katex">`, `<a>`), so `**` next to one is flanked by
# a letter. Blanking them with a space — what the survival axis does, correctly for its purpose —
# made `**`foo`**` read as `** **` and reported 277 false leaks on 2026-09-25.
ATOM = "文"


def frontmatter_end(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def paragraphs(text):
    """[(line_no, paragraph_text)] of reader-visible prose, with code/math/links/tags blanked.

    A paragraph ends at a blank line OR at a block start (heading, list item, quote, table row,
    image): CommonMark closes a paragraph there too, and joining two list items would let a
    `**` in one item pair with a `**` in the next and hide two leaks.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    mask, _ = LA.fence_prose_mask(text)
    fe = frontmatter_end(lines)
    paras, buf, start, display = [], [], None, False
    for n, line in enumerate(lines):
        keep = (n >= fe and n < len(mask) and mask[n])
        s = line.strip()
        if keep and s == "$$":
            display = not display
            s, keep = "", False
        if display:
            s, keep = "", False
        t = s
        if keep:
            t = TAG.sub(" ", INLINE_MATH.sub(ATOM, INLINE_CODE.sub(ATOM, LINK.sub(ATOM, s))))
        boundary = (not keep) or (not t.strip()) or BLOCK_START.match(t.lstrip())
        if boundary and buf:
            paras.append((start, " ".join(buf)))
            buf, start = [], None
        if keep and t.strip():
            if not buf:
                start = n + 1
            buf.append(t.strip())
    if buf:
        paras.append((start, " ".join(buf)))
    return paras


def kind(c):
    if c is None:
        return "edge"
    if c.isspace() or unicodedata.category(c) == "Zs":
        return "ws"
    return "punct" if unicodedata.category(c)[0] == "P" else "word"


def classify(para, m):
    """(can_open, can_close) for one `*` delimiter run, per CommonMark's flanking table."""
    before = para[m.start() - 1] if m.start() else None
    after = para[m.end()] if m.end() < len(para) else None
    b, a = kind(before), kind(after)
    left = a != "ws" and (a != "punct" or b in ("ws", "punct", "edge"))
    right = b != "ws" and (b != "punct" or a in ("ws", "punct", "edge"))
    return left, right


def unpaired(text):
    """[(line, context, why)] for every `*`/`**` run the platform cannot pair."""
    out = []
    for ln, para in paragraphs(text):
        runs, stack = [], []
        for m in RUN.finditer(para):
            if m.start() and para[m.start() - 1] == "\\":
                continue
            length = len(m.group(1))
            if length > 2:
                continue
            if length == 1 and m.start() == 0 and para[1:2].isspace():
                # `* text` is a bullet marker: CommonMark turns it into <li> and the
                # asterisk never reaches the reader, so it is not a delimiter run.
                continue
            left, right = classify(para, m)
            shape = "%s/%s" % (kind(para[m.start() - 1]) if m.start() else "edge",
                               kind(para[m.end()]) if m.end() < len(para) else "edge")
            runs.append(dict(len=length, open=left, close=right, span=m.span(),
                             shape=shape))
        for r in runs:
            if r["close"] and stack and stack[-1]["len"] == r["len"]:
                stack.pop()
                continue
            if r["open"]:
                stack.append(r)
            else:
                out.append((ln, para[max(0, r["span"][0] - 26):r["span"][1] + 26],
                            "LEAF-%s len=%d %s cannot pair" % ("STRONG" if r["len"] == 2 else "EM", r["len"], r["shape"])))
        for r in stack:
            out.append((ln, para[max(0, r["span"][0] - 26):r["span"][1] + 26],
                        "LEAF-%s len=%d %s opener never closes" % ("STRONG" if r["len"] == 2 else "EM", r["len"], r["shape"])))
    return out


def walk():
    for dirpath, dirnames, filenames in os.walk(DOCS):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn.endswith(".md") and fn != "SUMMARY.md":
                yield os.path.join(dirpath, fn)


def rel(path):
    return os.path.relpath(path, DOCS).replace(os.sep, "/")


def visible_markers(served):
    """Literal `**` a reader can see on the served page: code/pre/script/annotation nodes out."""
    text = html.unescape(LA.body_visible(served))
    return [m.start() for m in re.finditer(r"\*\*", text)]


CONTROL_PAGES = [
    # (name, markdown, expected unpaired count) -- every entry is a real shape from this book.
    ("closer-after-fullwidth-paren", "这与 RAG 评估里的**忠实度（Faithfulness）**是同一思想。\n", 2),
    ("opener-before-corner-quote", "因为它们都是**「有副作用、结果不可完全预测」的工具**：\n", 2),
    ("closer-before-cjk-after-corner-quote", "任务开始前定义**「完成」的可验证定义**与最大预算；\n", 2),
    ("legal-cjk-pair", "它是一个**目标**，不是一种方法。\n", 0),
    ("legal-closer-before-punctuation", "审批必须**少而准**，否则会退化。\n", 0),
    ("fence-copy-is-not-prose", "````text\n**示例（x）**文字\n````\n", 0),
    ("inline-code-copy", "读者会看到 `**粗体**` 四个星号原样留着。\n", 0),
    ("bolded-inline-code", "脏数据：**`timestamp_gap`** 卡多相机时间戳断层。\n", 0),
    ("bolded-link-label", "见 [**RAG 基础（入门）**](../06-memory-rag/rag-basics.md) 一节。\n", 0),
    ("math-multiplication-star", "系数 $$a * b$$ 与 $$c * d$$ 都是标量。\n", 0),
    ("list-bullet-asterisk", "* 一条列表项\n* 另一条带 **合法粗体** 的项\n", 0),
    ("pair-must-not-straddle-list-items", "- 第一项**加粗结尾\n- 第二项加粗**结尾\n", 2),
]


def selftest():
    ok = True
    for name, src, want in CONTROL_PAGES:
        got = len(unpaired(src))
        if got != want:
            ok = False
            print("CONTROL FAIL %-30s expected=%d got=%d" % (name, want, got))
            for ln, ctx, why in unpaired(src):
                print("        ", why, repr(ctx))
    # the negative controls must be able to fire: same text, marker moved one char
    fired = len(unpaired("它是一个**目标**，不是。\n"))
    if fired:
        ok = False
        print("CONTROL FAIL legal pair fired (%d)" % fired)
    print("controls: %s" % ("OK, every bucket able to fire" if ok else "BROKEN"))
    return ok


def run(workers=6, live=False):
    rows = []
    for path in walk():
        items = unpaired(open(path, encoding="utf-8").read())
        strong = [x for x in items if "STRONG" in x[2]]
        em = [x for x in items if "EM" in x[2]]
        if strong or em:
            rows.append((path, strong, em))
    # Only a leaked `**` is a reader-visible defect. A lone `*` (globs such as
    # `huggingface.co/*`, `src/*.py`) has no emphasis to fail and renders literally by
    # design, so it is printed as context but never gates the verdict.
    leaks = [r for r in rows if r[1]]
    print("emphasis flanking: pages=%d leaked_strong_markers=%d lone_star_runs=%d (context only)"
          % (len(leaks), sum(len(s) for _p, s, _e in leaks),
             sum(len(e) for _p, _s, e in rows)))
    for path, strong, em in sorted(leaks, key=lambda r: -len(r[1])):
        print("  %-56s strong=%d em=%d" % (rel(path), len(strong), len(em)))
        # A leaked ** is a reader-visible defect, so every one gets named -- a capped
        # print once hid 5 of 8 changelog markers.
        for ln, ctx, why in strong:
            print("      L%-5d %-40s %s" % (ln, why[:40], repr(ctx)))
        for ln, ctx, why in em[:2]:
            print("      L%-5d %-40s %s" % (ln, why[:40], repr(ctx)))
        if len(em) > 2:
            print("      ... %d more lone-* runs (literal in the renderer, not a leak)"
                  % (len(em) - 2))
    if not live:
        print("NOTE author leg only: pass --live to require the served page to agree per page")
        return 0 if not leaks else 1

    index = LA.url_index()
    pages = []
    for path in walk():
        k = LA.norm(LA.h1_of(open(path, encoding="utf-8").read()))
        if k in index:
            pages.append((path, index[k]))
    listed = {rel(p) for p, _u in pages}
    pred = {rel(p): sum(1 for x in unpaired(open(p, encoding="utf-8").read()) if "STRONG" in x[2])
            for p, _u in pages}
    unlisted = {r: n for r, n in
                ((rel(p), sum(1 for x in unpaired(open(p, encoding="utf-8").read()) if "STRONG" in x[2]))
                 for p in walk())
                if n and r not in listed}

    def probe(item):
        path, url = item
        try:
            served = PS.fetch_page(url)[1]
        except Exception as exc:
            return (rel(path), None, str(exc))
        return (rel(path), len(visible_markers(served)), None)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        got = list(pool.map(probe, pages))
    bad, err = [], []
    for r, n, e in got:
        if e:
            err.append((r, e))
        elif n != pred.get(r, 0):
            bad.append((r, pred.get(r, 0), n))
    print("live leg: pages=%d fetch-failures=%d prediction-mismatch=%d served_markers=%d"
          % (len(got), len(err), len(bad), sum(n for _r, n, _e in got if n is not None)))
    for r, p, n in sorted(bad)[:12]:
        print("   MISMATCH %-52s author=%d served=%d" % (r, p, n))
    for r, n in sorted(unlisted.items()):
        print("   NOT-LISTED %-50s author=%d served=? (page is not in the site index)" % (r, n))
    for r, e in err[:5]:
        print("   FETCH %s %s" % (r, e[:80]))
    return 1 if (bad or err or unlisted or leaks) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="require the served page to match the prediction")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 2)
    sys.exit(run(live=args.live))


if __name__ == "__main__":
    main()
