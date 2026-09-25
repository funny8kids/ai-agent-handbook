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

Round 90 added the second sight. `live_aria_manifest.leak_sites` had known the mechanism since
round 58 for formulas -- GitBook reprints every heading in the page outline with inline-code
formatting removed -- but emphasis judging had only the body rule, which blanks code spans, and a
live leg reading `body_visible()`, which drops exactly those outline anchors. So the author leg and
the live leg agreed on `leaked_strong_markers=0` for a changelog page whose sidebar printed:

    三、唯一一条真的读者侧缺陷：平台把 ** 配成了「第一个配最后一个」

The heading documents `**` inside a code span, which the body renders as a `<code>` box and the
outline renders as navigation copy. The outline is now a judged scope: heading text is flattened
the way GitBook flattens it (code spans unwrapped, link labels kept) and run through the SAME
flanking rule, and the live leg counts the nav-inclusive text. One heading site-wide was red --
the book's own round-87 account of the round-87 bug.

Round 92 added the third leg, because the first two only prove a negative. A page with
`leaked_strong_markers=0` and `prediction-mismatch=0` can still have lost its emphasis: if the
platform consumes the `**` and emits plain text, no marker reaches the reader AND no bold does.
So each authored PAIR now makes a positive claim the served page has to honour -- a `<strong>`
whose text carries that span (see `bold_survived`). The obvious wider form of this judge, byte
extents of authored `**…**` vs `<strong>…</strong>`, was measured and rejected first: on the 12
boldest pages it reported `only-author=207 / only-served=575` while the hazard it was meant to
catch (a served span strictly wider than the author's, i.e. round 83's "first `**` pairs with the
last") measured **0**. The differences were ruler noise: GitBook's own error-banner `<strong>`
lives inside a `<script>` string (`Error in site configuration:`, 2 copies in raw HTML, 0 in
reader-visible text), the outline reprints heading bold, and KaTeX spans flatten differently on
the two sides. Matching by text rather than by extent is immune to all three.

Round 94 found the outline rule under-counting. `--page 00-index/changelog` read `author=0
served=2` on a whole copy, and both markers sat in the sidebar's copy of this book's own round-92
heading. The body had it right -- a code span renders as `<code>`, which `visible_markers` strips
-- but the outline has no code formatting to strip, so the reader navigated by
`作者写的 **…** 到读者页面上到底有没有变粗`. The nav sight had been built by flattening a heading
(backticks gone) and running the SAME flanking rule over it: correct for text the renderer parses,
wrong for text it merely copies, because `**…**` satisfies CommonMark and the pairing rule
swallowed both delimiters. A heading now contributes (a) the runs its non-code text cannot pair and
(b) every literal `**` inside its code spans, counted the same non-overlapping way the served side
counts them. Site-wide sight (b) was worth 2 markers on 1 of 112 code-carrying headings -- the one
this round reworded.
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
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# GitBook's outline prints a heading with the code span's BACKTICKS gone and a link's LABEL kept,
# so flattening has to unwrap both rather than blank them the way the body rule does.
HEADING_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
# A code span, a formula and a link label are WORDS to the renderer, not gaps: the reader's DOM
# holds an atom there (`<code>`, `<span class="katex">`, `<a>`), so `**` next to one is flanked by
# a letter. Blanking them with a space — what the survival axis does, correctly for its purpose —
# made `**`foo`**` read as `** **` and reported 277 false leaks on 2026-09-25.
# The bold leg splits authored text on this sentinel to find the parts it can actually match, so
# the sentinel has to be (a) kept by LA.norm, whose range is [0-9A-Za-z] + U+4E00-U+9FFF, and
# (b) a character no author would type. "文" passed (a) and failed (b) hard: it is inside the word
# 上下文, so `**有效上下文窗口**` split into fragments that matched other text on the page and the
# leg reported a wrong sentence as a correct bold. "丨" (a CJK stroke, U+4E28) is kept by norm and
# appears nowhere in this book -- `selftest` counts it across the corpus and goes red if that dies.
ATOM = "丨"


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


def _heading_rows(text):
    """[(line_no, outline_text, carries_code, code_span_contents)] per published heading.

    `outline_text` is the heading as the sidebar's EMPHASIS rendering sees it: a code span becomes
    one atom and a link loses its target. A code span must not be merged into this string, because
    `unpaired` would let a backticked pair close itself -- see `outline_code_leaks`.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    mask, _ = LA.fence_prose_mask(text)
    fe = frontmatter_end(lines)
    out = []
    for n, line in enumerate(lines):
        if not (n >= fe and n < len(mask) and mask[n]):
            continue
        m = HEADING.match(line.strip())
        if not m:
            continue
        spans = [s.strip("`").strip() for s in INLINE_CODE.findall(m.group(2))]
        flat = INLINE_CODE.sub(ATOM, m.group(2))
        out.append((n + 1, HEADING_LINK.sub(lambda g: g.group(1), flat).strip(),
                    1 if spans else 0, spans))
    return out


def heading_paras(text):
    """[(line_no, heading_text, carried_inline_code)] as the page OUTLINE prints it.

    The body rule blanks a code span to one atom, which is right for `<main>` and wrong for the
    sidebar: there GitBook has already dropped the backticks, so the span's own characters are
    reading text. Those characters are counted by `outline_code_leaks`, not folded in here.
    """
    return [(ln, flat, coded) for ln, flat, coded, _spans in _heading_rows(text)]


NAV_MARKER = re.compile(r"\*\*")


def outline_code_leaks(text):
    """Every literal `**` a heading's inline code puts in the outline -- no flanking, no pairing.

    Round 94 measured the live changelog at `author=0 served=2` with a whole copy fetched. The body
    wraps the span in `<code>`, which `visible_markers` strips, so a backticked `**…**` is invisible
    there; the sidebar has no code formatting to strip, and its raw markup is

        <span class="">三、第三条腿：作者写的 **…** 到读者页面上到底有没有变粗</span>

    so BOTH delimiters of a pair that CommonMark would render as bold still reach the reader.
    Pairing is a question about rendering, and the outline renders nothing: it prints the code
    span's characters. Counting `**` the same non-overlapping way `visible_markers` does is what
    makes this the prediction of the served number rather than a second opinion about it.
    """
    return [(ln, span[max(0, m.start() - 12):m.end() + 12],
             "NAV-CODE-STRONG printed verbatim by the outline")
            for ln, _flat, _coded, spans in _heading_rows(text)
            for span in spans for m in NAV_MARKER.finditer(span)]


def unpaired_paras(paras):
    return unpaired(None, [(ln, flat) for ln, flat, _c in paras])


def outline_leaks(text):
    """Both outline sights together: runs the renderer cannot pair, plus what code spans print."""
    return ([(ln, ctx, why + " [nav]") for ln, ctx, why in unpaired_paras(heading_paras(text))]
            + [(ln, ctx, why + " [nav]") for ln, ctx, why in outline_code_leaks(text)])


def scope_line():
    """How wide the outline sight actually is -- the denominators behind 'only 1 was red'.

    Two populations, because the rule has two sights. A heading whose CODE carries `**` is settled
    by the printer, not by the flanking table, so it counts in `printed_by_code`. The pairing
    population is the headings whose RENDERED text carries markdown-significant characters: an
    identifier (`get_weather`) or a bracket (`[t]`) in code flattens into text the table has
    nothing to pair, which is why it is not in that denominator either.
    """
    heads = coded = sig = literal = 0
    for path in walk():
        rows = _heading_rows(open(path, encoding="utf-8").read())
        heads += len(rows)
        for _ln, flat, has_code, spans in rows:
            coded += has_code
            n_lit = sum(len(NAV_MARKER.findall(s)) for s in spans)
            literal += n_lit
            sig += 1 if any(c in flat for c in "*_[]<>#$~") else 0
    return ("outline scope: headings=%d carrying_inline_code=%d printed_by_code=%d"
            " whose_rendered_text_is_markdown_significant=%d"
            % (heads, coded, literal, sig))


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


def unpaired(text, paras=None):
    """[(line, context, why)] for every `*`/`**` run the platform cannot pair.

    `paras` lets the outline scope (heading_paras) reuse this exact pairing rule instead of a
    second, drift-prone copy of it.
    """
    out = []
    for ln, para in (paras if paras is not None else paragraphs(text)):
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
    """Literal `**` a reader can see on the served page: code/pre/script/annotation nodes out.

    Nav-INCLUSIVE on purpose (round 90): `body_visible` would drop the outline anchors, which is
    precisely where a heading's code span reaches the reader as plain characters.
    """
    text = html.unescape(LA.visible(served))
    return [m.start() for m in re.finditer(r"\*\*", text)]


STRONG_TAG = re.compile(r"<strong[^>]*>(.*?)</strong>", re.S | re.I)
ANY_TAG = re.compile(r"<[^>]+>")
SQUEEZE = re.compile(r"\s+")
# Widget chrome that `visible` still reads as text. Measured on `18-frontier-2026/README` (2026-09-25):
# every heading/cell affordance ships an inline `<svg><title>GitBook Assistant</title></svg>`, 124
# copies on one page, and the reader sees an ICON while the text says "GitBook Assistant". Left in,
# it wedged itself between table cells and broke any comparison spanning a cell -- 279 authored bolds
# were reported as words the page never carried. It is not prose and never was authored.
CHROME = re.compile(r"<(script|style|svg|title|noscript)\b.*?</\1>", re.S | re.I)


def reader_html(served):
    return CHROME.sub(" ", served)


def serve_copy(url, fetch=PS.fetch_page):
    """A served copy whole enough to grade, or a raise — never an empty string.

    `PS.fetch_page` reports both a failed fetch and round 93's short-read refusal as `("", reason)`
    instead of raising. `probe()` catches exceptions, not tuples, so reading the second slot
    directly handed `""` to the marker count: every page the author leg predicts clean stayed clean
    on a copy that carried nothing, and the run looked like a full-site pass.
    """
    _url, text, err = fetch(url)
    if err:
        raise ValueError(err)
    return text


def prose_of(served):
    """The reader's visible sentence text, in the same space-free form `arrival_key` uses.

    `html.unescape` is not optional: the DOM text node says `&quot;`, the browser shows `"`, and
    without the unescape the entity NAME survives normalization as the letters `quot`. That read
    156 authored bolds as "never published" until a `"` was found in the sentence -- the same trap
    the marker leg documents above.
    """
    return SQUEEZE.sub("", LA.norm(html.unescape(LA.visible(reader_html(served)))))


def authored_bold(text):
    """[(line_no, inner, tail)] per PARSED-AS-BOLD pair -- runs the marker leg pairs successfully.

    The first two legs ask "does a `**` reach the reader". A page can answer that with 0 while the
    platform eats the markers and emits plain text -- the reader loses the bold and the literal
    count stays clean. This returns the author's positive claim instead. `tail` is the ~40
    characters that follow the closer: arrival has to be judged on the bold AND its context,
    because a two-character bold word like `放行` exists somewhere on a 25 MB changelog page even
    when the sentence carrying it has not been published yet.
    """
    out = []
    for ln, para in paragraphs(text):
        stack = []
        for m in RUN.finditer(para):
            if m.start() and para[m.start() - 1] == "\\":
                continue
            if len(m.group(1)) != 2:
                continue
            left, right = classify(para, m)
            if right and stack:
                start = stack.pop()
                out.append((ln, para[start:m.start()], para[m.end():m.end() + 40]))
            elif left:
                stack.append(m.end())
    return [(ln, t, tail) for ln, t, tail in out if t.strip()]


def served_strongs(served):
    """Reader-side bold, as normalized space-free text, in document order.

    `reader_html` first: a `<strong>` inside the app-state JSON in a `<script>` payload is a
    developer-tool string, not something the reader sees bold.
    """
    return [SQUEEZE.sub("", LA.norm(html.unescape(ANY_TAG.sub("", m.group(1))))).strip()
            for m in STRONG_TAG.finditer(reader_html(served))]


def arrival_key(inner, tail):
    """The longest atom-free run of `bold + what follows it`, normalized and space-free.

    The words alone cannot prove arrival: `放行`, `的判决` and `16/16` are short, generic, and
    already appear somewhere else on a 25 MB changelog page, so the first site-wide run judged
    three unpublished sentences as if the reader had them and called the missing bold a defect.
    Anchoring on the text that follows the closer is what a reader actually sees, and splitting on
    ATOM keeps a code span in the tail from breaking an otherwise contiguous run.

    Whitespace is squeezed because the two sides cannot agree on it: the authored pair has no gap
    where the `<strong>` tag sits, while the served page's visible-text extractor puts one there,
    so a spaced comparison read a perfectly bold, perfectly delivered sentence as absent.
    """
    parts = [p.strip() for p in LA.norm(inner + tail).split(ATOM) if p.strip()]
    return max((SQUEEZE.sub("", p) for p in parts), key=len) if parts else ""


def bold_state(inner, tail, strongs, prose):
    """'ok' | 'lost' | 'absent' | 'atom' for one authored bold span.

    Only `lost` is this axis's defect, and the distinction is what the third state buys: the first
    site-wide run put 34 spans in the red and ALL of them sat on `00-index/changelog.md`, whose
    published HTML copy was one revision behind (round 91's own text). Those words had not reached
    the reader at all -- that is the survival axis's `MISS`, and it is not evidence about bold.
    `lost` therefore requires the sentence to have arrived (see `arrival_key`): the platform
    consumed the markers and printed plain text.

    Blanked atoms (a code span, a link label, a `$…$` run the author rule treats as math) are gaps
    in what we know, not characters to find: `**$0.0077 vs $0.1985**` is blanked to `丨0.1985` here
    but served as `<strong>$0.0077 vs $0.1985</strong>`. And a fragment must be findable in SOME
    served strong, not one and the same: measured on `09-frameworks/dspy`, a bold that wraps a code
    span arrives SPLIT at the code boundary (`<code><strong>docstring</strong></code><strong>
    不是注释</strong>`), which is the reader's bold and was a 311-span false red before that.
    """
    frags = [f for f in (SQUEEZE.sub("", x) for x in LA.norm(inner).split(ATOM)) if f]
    if not frags:
        return "atom"
    key = arrival_key(inner, tail)
    if not key or key not in prose:
        return "absent"
    return "ok" if all(any(f in s for s in strongs) for f in frags) else "lost"


CONTROL_PAGES = [
    # (name, markdown, expected body leaks, expected outline leaks) -- every entry is a real shape.
    ("closer-after-fullwidth-paren", "这与 RAG 评估里的**忠实度（Faithfulness）**是同一思想。\n", 2, 0),
    ("opener-before-corner-quote", "因为它们都是**「有副作用、结果不可完全预测」的工具**：\n", 2, 0),
    ("closer-before-cjk-after-corner-quote", "任务开始前定义**「完成」的可验证定义**与最大预算；\n", 2, 0),
    ("legal-cjk-pair", "它是一个**目标**，不是一种方法。\n", 0, 0),
    ("legal-closer-before-punctuation", "审批必须**少而准**，否则会退化。\n", 0, 0),
    ("fence-copy-is-not-prose", "````text\n**示例（x）**文字\n````\n", 0, 0),
    ("inline-code-copy", "读者会看到 `**粗体**` 四个星号原样留着。\n", 0, 0),
    ("bolded-inline-code", "脏数据：**`timestamp_gap`** 卡多相机时间戳断层。\n", 0, 0),
    ("bolded-link-label", "见 [**RAG 基础（入门）**](../06-memory-rag/rag-basics.md) 一节。\n", 0, 0),
    ("math-multiplication-star", "系数 $$a * b$$ 与 $$c * d$$ 都是标量。\n", 0, 0),
    ("list-bullet-asterisk", "* 一条列表项\n* 另一条带 **合法粗体** 的项\n", 0, 0),
    ("pair-must-not-straddle-list-items", "- 第一项**加粗结尾\n- 第二项加粗**结尾\n", 2, 0),
    # round 90: the outline prints a heading's code span with the backticks already gone
    ("outline-prints-code-marker",
     "### 三、唯一一条真的读者侧缺陷：平台把 `**` 配成了「第一个配最后一个」\n", 0, 1),
    ("outline-legal-bold-untouched", "## 这是**合法**粗体，不是漏出来的\n", 0, 0),
    ("outline-lone-underscore-identifier", "## 字段 `get_weather` 与 `tool_result` 的差别\n", 0, 0),
    ("outline-code-inside-fence-stays-hidden", "````text\n### 演示 `**`\n````\n", 0, 0),
    ("outline-link-label-unwrapped", "## 见 [**RAG 基础**](../06-memory-rag/rag-basics.md) 一节\n", 0, 0),
    # round 94: the shape that escaped the outline leg for one round -- `**…**` PAIRS under the
    # flanking table, so the pairing sight called it clean, and the sidebar printed both delimiters.
    ("outline-code-pair-printed-verbatim",
     "### 三、第三条腿：作者写的 `**…**` 到读者页面上到底有没有变粗\n", 0, 2),
    # ...and the guard that the new leg is not a blanket "count every asterisk": the same pair
    # outside a code span is real emphasis, renders bold, and reaches the nav as text.
    ("outline-rendered-pair-still-clean", "### 三、第三条腿：作者写的 **…** 到读者页面上有没有变粗\n", 0, 0),
]


def outline_total(src):
    """Both outline sights as one number -- what the live leg has to predict."""
    return len(outline_leaks(src))


HOME_CONTROLS = re.compile(r"(\d+) 条种植控制")


def control_count():
    """What this axis actually asserts: the shape table plus the fetch seam's two directions."""
    return len(CONTROL_PAGES) + 1


def homepage_parity(bullet=None):
    """The homepage's 「N 条种植控制」 about THIS axis must be this axis's own number.

    Round 90 wired exactly this alarm for `check_prose_survival` and stopped there, so the emphasis
    bullet kept a reader-facing count that nothing read: round 94's two new outline controls made it
    stale by the amount of work the round did. `bullet` lets a control feed a doctored sentence --
    an alarm nobody can make ring is not an alarm.
    """
    if bullet is None:
        readme = open(os.path.join(DOCS, "README.md"), encoding="utf-8").read().split("\n")
        bullet = next((l for l in readme if "check_emphasis_flanking.py" in l), None)
        if bullet is None:
            return ["homepage: no sentence cites check_emphasis_flanking.py, so its control "
                    "budget has no judge"]
    m = HOME_CONTROLS.search(bullet)
    if not m:
        return ["homepage: the emphasis bullet must cite 「N 条种植控制」 so this assertion can read it"]
    if int(m.group(1)) != control_count():
        return ["homepage: 「%s 条种植控制」 is not the %d controls asserted here"
                % (m.group(1), control_count())]
    return []


def fetch_seam_control():
    """The live leg must be unable to grade a copy that did not arrive whole. Both directions."""
    ok = True
    whole = "<html><body><p>这一句读者应当看到</p></body></html>"
    for kept, reason in ((whole, None),
                         ("", "short read: no closing </html> (18900551 chars)")):
        def fake(url, kept=kept, reason=reason):
            return (url, kept, reason)
        try:
            got, raised = serve_copy("https://example.invalid/page", fetch=fake), None
        except ValueError as exc:
            got, raised = None, str(exc)
        if reason is None and (raised or got != whole):
            ok = False
            print("CONTROL FAIL complete copy refused or mangled: %r" % (raised,))
        if reason and raised is None:
            ok = False
            print("CONTROL FAIL short copy graded as %r instead of refusing" % (got,))
    return ok


def selftest():
    ok = True
    for name, src, want, want_nav in CONTROL_PAGES:
        got = len(unpaired(src))
        got_nav = outline_total(src)
        if got != want or got_nav != want_nav:
            ok = False
            print("CONTROL FAIL %-38s expected=%d/%d got=%d/%d"
                  % (name, want, want_nav, got, got_nav))
            for ln, ctx, why in unpaired(src):
                print("        body", why, repr(ctx))
            for ln, ctx, why in outline_leaks(src):
                print("        nav ", why, repr(ctx))
    # the negative controls must be able to fire: same text, marker moved one char
    fired = len(unpaired("它是一个**目标**，不是。\n"))
    if fired:
        ok = False
        print("CONTROL FAIL legal pair fired (%d)" % fired)
    # ...and the outline rule must be able to miss: a code span's delimiters have to be counted
    # whether or not the flanking table would pair them.
    for shape, want in (("## 平台把 `**` 配成了\n", 1), ("## 作者写的 `**…**` 变粗了吗\n", 2)):
        silent = outline_total(shape)
        if silent != want:
            ok = False
            print("CONTROL FAIL outline rule unable to fire on %r (%d, want %d)"
                  % (shape, silent, want))
    ok = bold_selftest() and ok
    ok = fetch_seam_control() and ok
    for msg in homepage_parity():
        ok = False
        print("CONTROL FAIL %s" % msg)
    if not homepage_parity("绿色由 %d 条种植控制撑着" % (control_count() + 3)):
        ok = False
        print("CONTROL FAIL a homepage budget off by three read as parity")
    print("controls: %s (%d asserted, the homepage budget for this axis is judged)"
          % ("OK, every bucket able to fire" if ok else "BROKEN", control_count()))
    return ok


BOLD_SRC = "这与检索的**有效上下文窗口**是同一思想。\n"
CODE_SRC = "脏数据：**`timestamp_gap` 字段** 断层。\n"
LAG_SRC = "本轮新增的一句话里有**没送到的粗体**。\n"
# The exact shape the first site-wide run mis-judged: a generic short bold whose word lives on the
# page in other sentences.
GENERIC_SRC = "本轮新加的句子里有**放行**两字。\n"
GENERIC_OLD_SRC = "<p>别的历史段落里写到：放行规则见前文。放行一词早就有。</p>"
GENERIC_PLAIN_SRC = "<p>本轮新加的句子里有放行两字。</p>"
# Real shape: 18-frontier-2026/README's timeline table, where the served page puts an icon widget
# (accessible name "GitBook Assistant") at the end of every cell.
CHROME_SRC = "| **GPT-6** 发布 | computer use 落地 |\n"
CHROME_WIDGET = '<svg width="16" height="16"><title>GitBook Assistant</title><path d="M1 1"/></svg>'
CHROME_OK_SRC = ("<table><tr><td><strong>GPT-6</strong> 发布%s</td><td>computer use 落地</td></tr></table>"
                 % CHROME_WIDGET)
CHROME_EATEN_SRC = ("<table><tr><td>GPT-6 发布%s</td><td>computer use 落地</td></tr></table>"
                    % CHROME_WIDGET)
# Measured on `02-agent-basics/perception-planning-action`: the DOM text node reads
# `回填一句 &quot;error&quot;`, the browser shows plain quotes, and the authored line has no letters
# there at all -- so the two sides only agree once the entity is unescaped.
QUOTE_SRC = '他把**具体错误信息**原样留着，写 "error" 一次。\n'
QUOTE_TAIL = '写 &quot;error&quot; 一次。</p>'
QUOTE_OK_SRC = "<p>他把<strong>具体错误信息</strong>原样留着，" + QUOTE_TAIL
QUOTE_EATEN_SRC = "<p>他把具体错误信息原样留着，" + QUOTE_TAIL


def undelivered(bolds, strongs, prose):
    """[(line, inner)] whose sentence reached the reader but whose bold did not."""
    return [(ln, b) for ln, b, tail in bolds if bold_state(b, tail, strongs, prose) == "lost"]


def lost_bold(src, served):
    """Spans the author bolded and the served page did not deliver."""
    return undelivered(authored_bold(src), served_strongs(served), prose_of(served))


def bold_selftest():
    """The third leg must fire on the one failure the first two legs cannot see.

    `served-eaten` is a page whose markers were consumed and whose bold was NEVER produced: the
    literal-marker count reads 0 and the author prediction reads 0, so legs one and two are green
    while the reader has lost the emphasis. If the new leg cannot fire here it is a decoration.
    The other rows are the counterexamples that keep the leg honest -- shapes the platform serves
    correctly and a naive matcher calls lost (measured: demanding one code-span-free `<strong>`
    node flagged 311 real reader-side bolds before the split serving was found).
    """
    ok = True
    cases = [
        ("served-bold", BOLD_SRC,
         '<p>这与检索的<strong class="font-bold">有效上下文窗口</strong>是同一思想。</p>', "ok"),
        ("served-eaten", BOLD_SRC, "<p>这与检索的有效上下文窗口是同一思想。</p>", "lost"),
        ("served-bold-in-the-wrong-place", BOLD_SRC,
         "<p><strong>这与检索的</strong>有效上下文窗口是同一思想。</p>", "lost"),
        # different WORDS at the bold is a page that never carried this sentence: absent, not lost
        ("served-other-words-bold", BOLD_SRC,
         "<p>这与检索的<strong>失效时间窗口</strong>是同一思想。</p>", "absent"),
        # A two-character bold word is not an arrival proof: `放行` / `的判决` / `16/16` all exist
        # somewhere else on a 25 MB changelog page. These two rows pin the context rule from both
        # sides -- the word alone must NOT count, the whole sentence must still fire.
        ("served-generic-word-but-not-the-sentence", GENERIC_SRC, GENERIC_OLD_SRC, "absent"),
        ("served-generic-sentence-bold-eaten", GENERIC_SRC, GENERIC_PLAIN_SRC, "lost"),
        # A table cell: the platform stamps an icon widget with an accessible NAME between the cell
        # and its neighbour, so "what the reader's text says" and "what the reader sees" diverge.
        ("served-widget-name-after-a-cell", CHROME_SRC, CHROME_OK_SRC, "ok"),
        ("served-widget-name-after-a-cell-eaten", CHROME_SRC, CHROME_EATEN_SRC, "lost"),
        # The DOM says `&quot;`, the browser shows `"`. Reader text must be unescaped before it is
        # compared, or the entity's NAME lands inside the sentence.
        ("served-entity-quotes-around-the-bold", QUOTE_SRC, QUOTE_OK_SRC, "ok"),
        ("served-entity-quotes-bold-eaten", QUOTE_SRC, QUOTE_EATEN_SRC, "lost"),
        ("served-code-then-text-split", CODE_SRC,
         "<p>脏数据：<code><strong>timestamp_gap</strong></code><strong> 字段</strong> 断层。</p>", "ok"),
        ("served-code-inside-strong", CODE_SRC,
         "<p>脏数据：<strong><code>timestamp_gap</code> 字段</strong> 断层。</p>", "ok"),
        ("served-code-eaten-too", CODE_SRC, "<p>脏数据：timestamp_gap 字段 断层。</p>", "lost"),
        # the page simply has not caught up: the words are nowhere, and that is MISS's red not ours
        ("served-page-lags-author", LAG_SRC, "<p>这一页还是上一版，没有这句话。</p>", "absent"),
        ("served-atom-only", "前缀 **`x`** 后缀。\n", "<p>前缀 x 后缀。</p>", "atom"),
    ]
    for name, src, served, want in cases:
        bolds = authored_bold(src)
        if len(bolds) != 1:
            ok = False
            print("CONTROL FAIL bold leg %-26s authored pairs=%d, expected 1" % (name, len(bolds)))
            continue
        got = bold_state(bolds[0][1], bolds[0][2], served_strongs(served), prose_of(served))
        if got != want:
            ok = False
            print("CONTROL FAIL bold leg %-26s expected=%s got=%s" % (name, want, got))
    # the marker leg must be blind to the eaten case, or this new leg proves nothing new
    if visible_markers(cases[1][2]):
        ok = False
        print("CONTROL FAIL bold phantom is already visible to the marker leg")
    # ...and the lost state must be reachable ONLY when the words arrived
    if len(lost_bold(LAG_SRC, "<p>这一页还是上一版，没有这句话。</p>")):
        ok = False
        print("CONTROL FAIL a page behind the author counted as lost bold")
    # the chrome rule has to be load-bearing: judge the same page WITHOUT dropping the widget's
    # accessible name and the sentence stops existing -- if that still reads `ok`, `reader_html`
    # is not being used and the 279-span false `absent` it fixes is back.
    _n, csrc, cserved, _w = [c for c in cases if c[0] == "served-widget-name-after-a-cell"][0]
    _ln, cinner, ctail = authored_bold(csrc)[0]
    raw_prose = SQUEEZE.sub("", LA.norm(LA.visible(cserved)))
    if bold_state(cinner, ctail, served_strongs(cserved), raw_prose) == "ok":
        ok = False
        print("CONTROL FAIL widget-name chrome is not actually being dropped from reader text")
    # ...and the same for the unescape: judge the quote page WITHOUT unescaping and it must stop
    # being able to see its own sentence
    _n, qsrc, qserved, _w = [c for c in cases if c[0] == "served-entity-quotes-around-the-bold"][0]
    _ln, qinner, qtail = authored_bold(qsrc)[0]
    escaped_prose = SQUEEZE.sub("", LA.norm(LA.visible(reader_html(qserved))))
    if bold_state(qinner, qtail, served_strongs(qserved), escaped_prose) == "ok":
        ok = False
        print("CONTROL FAIL HTML entities are not actually being unescaped into reader text")
    # the sentinel has to stay a sentinel: if an author ever types it, fragments split on real text
    typed = sum(open(p, encoding="utf-8").read().count(ATOM) for p in walk())
    if typed:
        ok = False
        print("CONTROL FAIL ATOM sentinel %r is typed by an author (%d times in the corpus)"
              % (ATOM, typed))
    return ok


def leaks_of(src):
    """(strong_runs, em_runs) over BOTH sights a reader has: body prose and the page outline."""
    items = unpaired(src) + outline_leaks(src)
    return ([x for x in items if "STRONG" in x[2]], [x for x in items if "EM" in x[2]])


def run(workers=6, live=False, only=None):
    rows = []
    for path in walk():
        strong, em = leaks_of(open(path, encoding="utf-8").read())
        if strong or em:
            rows.append((path, strong, em))
    # Only a leaked `**` is a reader-visible defect. A lone `*` (globs such as
    # `huggingface.co/*`, `src/*.py`) has no emphasis to fail and renders literally by
    # design, so it is printed as context but never gates the verdict.
    leaks = [r for r in rows if r[1]]
    nav_total = sum(1 for _p, s, _e in leaks for x in s if "[nav]" in x[2])
    print("emphasis flanking: pages=%d leaked_strong_markers=%d (body=%d outline=%d) lone_star_runs=%d (context only)"
          % (len(leaks), sum(len(s) for _p, s, _e in leaks),
             sum(len(s) for _p, s, _e in leaks) - nav_total, nav_total,
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
    print(scope_line())
    if not live:
        print("NOTE author leg only: pass --live to require the served page to agree per page")
        return 0 if not leaks else 1

    index = LA.url_index()
    all_pages = []
    for path in walk():
        k = LA.norm(LA.h1_of(open(path, encoding="utf-8").read()))
        if k in index:
            all_pages.append((path, index[k]))
    # A `--page` run narrows what gets FETCHED, never what the site index is: if `listed`
    # followed the filter, every other leak-bearing page would print NOT-LISTED and gate the
    # exit code for a page this run never meant to grade.
    listed = {rel(p) for p, _u in all_pages}
    # Round 93's account, implemented: the changelog is the one document the CDN reliably
    # truncates (three short reads measured in one round: 9.8 M / 13.8 M / 18.9 M of 27 M), and
    # without a page entry a single re-grade costs a full-site walk. `--page` must be able to
    # name THAT page, so the filter runs after the index lookup rather than instead of it.
    if only:
        want = only.strip("/")
        want = want[len("docs/"):] if want.startswith("docs/") else want
        want = want[:-3] if want.endswith(".md") else want
        pages = [(p, u) for p, u in all_pages if rel(p) in (want, only.strip("/"))]
        if not pages:
            # A filter that matches nothing and prints `pages=0` with a green exit is the
            # blind-ruler shape this repo keeps finding, so a typo is a hard 2, not a 0.
            print("PAGE-NOT-INDEXED %s — %d indexed pages, none matches (exit 2: no verdict)"
                  % (only, len(all_pages)))
            return 2
    else:
        pages = all_pages
    pred = {rel(p): len(leaks_of(open(p, encoding="utf-8").read())[0]) for p, _u in pages}
    bolded = {rel(p): authored_bold(open(p, encoding="utf-8").read()) for p, _u in pages}
    unlisted = {r: n for r, n in
                ((rel(p), len(leaks_of(open(p, encoding="utf-8").read())[0])) for p in walk())
                if n and r not in listed}

    def probe(item):
        path, url = item
        try:
            served = serve_copy(url)
        except Exception as exc:
            return (rel(path), None, None, None, str(exc))
        strongs = served_strongs(served)
        prose = prose_of(served)
        states = [bold_state(b, tail, strongs, prose) for _ln, b, tail in bolded[rel(path)]]
        lost = [(ln, b) for (ln, b, _t), s in zip(bolded[rel(path)], states) if s == "lost"]
        return (rel(path), len(visible_markers(served)), lost,
                (states.count("absent"), states.count("atom")), None)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        got = list(pool.map(probe, pages))
    bad, err, lost, absent, atoms = [], [], [], 0, 0
    for r, n, l, u, e in got:
        if e:
            err.append((r, e))
        else:
            absent += u[0]
            atoms += u[1]
            if n != pred.get(r, 0):
                bad.append((r, pred.get(r, 0), n))
            if l:
                lost.append((r, l))
    print("live leg: pages=%d%s fetch-failures=%d prediction-mismatch=%d served_markers=%d "
          "bold_pages_lost=%d bold_spans_lost=%d (of %d authored pairs) "
          "words_not_in_served_page=%d bold_spans_atom_only=%d"
          % (len(got), (" (single page: %s, of %d indexed)" % (only.strip("/"), len(all_pages)))
             if only else "",
             len(err), len(bad), sum(n for _r, n, _l, _u, _e in got if n is not None),
             len(lost), sum(len(l) for _r, l in lost),
             sum(len(v) for v in bolded.values()), absent, atoms))
    for r, l in sorted(lost, key=lambda x: -len(x[1]))[:12]:
        print("   BOLD-LOST %-52s markers eaten, bold never produced (%d spans)" % (r, len(l)))
        for ln, b in l[:3]:
            print("      L%-5d %s" % (ln, repr(b)[:70]))
    for r, p, n in sorted(bad)[:12]:
        print("   MISMATCH %-52s author=%d served=%d" % (r, p, n))
    for r, n in sorted(unlisted.items()):
        print("   NOT-LISTED %-50s author=%d served=? (page is not in the site index)" % (r, n))
    for r, e in err[:5]:
        print("   FETCH %s %s" % (r, e[:80]))
    return 1 if (bad or err or unlisted or leaks or lost) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="require the served page to match the prediction")
    ap.add_argument("--page", help="fetch only this page (needs --live); a name that is not "
                                   "indexed exits 2 rather than reading green")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        # The single-page entry is only safe if its own failure mode is nailed: an unmatched
        # name must NOT become `pages=0` plus the green exit the full run prints. This calls
        # the live branch, which returns before any fetch when the filter is empty.
        if run(live=True, only="no-such-page-xyzzy.md") != 2:
            print("   CONTROL FAIL --page with an unmatched name must exit 2, not read green")
            sys.exit(2)
        sys.exit(0 if selftest() else 2)
    sys.exit(run(live=args.live, only=args.page))


if __name__ == "__main__":
    main()
