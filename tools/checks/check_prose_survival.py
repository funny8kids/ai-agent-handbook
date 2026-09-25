"""Does every sentence the author wrote reach the reader?

The book has judged what the reader *sees extra* (leaked markup, unrendered formulas, dropped
images, over-wide diagrams) since rounds 56-58, and nothing at all for the opposite failure:
text that exists in `docs/` and is simply **not in the published page**. That class is not
hypothetical — round 59 measured that an escaped backtick silently deletes the rest of a line
from the live page (see `reference-gitbook-platform-facts`), and the round closed it on the
*authoring* side (the `BT` rule in `check_structure.py`) because a judge for the served side
did not exist. So the platform's own known swallowing behaviours (inline code that breaks a
span, a GitBook block the renderer rejects, a `{%% %%}` tag nested where it is not allowed)
were each worth exactly one hand-audit.

The rule, per page: cut the authored file into prose chunks with the SAME tokenizer the repo's
live axes use, and require each chunk to appear, contiguously, in the reader-visible text of
the served page.

口径, and why each piece is there:
  - fences and inline code/math are removed from the authored side and their nodes are removed
    from the served side, so a chunk never straddles a code span. That is deliberate: the
    escaped-backtick defect deletes everything after the bad backtick, and the tail chunk of the
    line is exactly what goes missing.
  - a chunk is a sentence-run split on 。；;！？ — long enough that an accidental substring match
    costs real text, short enough that a finding names the words the reader lost.
  - `##`-and-deeper heading lines are units of their own (`kind` is `heading`). Round 87 left that
    as an open account: no live axis had ever read a published heading, so a section title that
    disappeared from the page — or lost the words that carry its TOC entry — stayed green everywhere.
    A body `# H1` is still excluded, because GitBook drops it and publishes the SUMMARY label in its
    place (measured round 55); `check_nav_h1_sync.py` owns that equality and this judge does not
    duplicate it. A heading shorter than the sentence floor is not graded either: two characters can
    match anywhere in the body, so the leg's resolution limit is 14 normalized characters.
  - `>` blockquote lines are units too (`kind` is `quote`). Round 88 measured what the old skip cost:
    42 such lines on 32 pages, which produce 57 units on 28 of them — prose a reader sees inside a
    styled box, which this judge had walked past since the day it was written. An image line (`![…]`)
    is still skipped: its alt text is not the page's body copy, and the picture itself is another
    axis's object (controls T-U).
  - a bare `<https://…>` autolink ends a unit exactly like a link does: the published page prints
    the address itself between the two halves of the sentence, so a joined unit could never match.
  - a reference with no terminating `;` stays literal text on the authored side, because that is what
    the platform ships: round 84 read the raw HTML behind changelog L128 and found the authored
    `&quot` arriving as `&amp;quot`, i.e. the reader is shown the word `quot`. Python's `unescape`
    decodes that legacy form, so decoding authored source erases characters the reader has.
  - a page that prints its own round history is graded only from the first round its published copy
    provably finished. Round 83 measured the live changelog holding round 79's heading but not the
    close-out prose added to that section after the push — a revision gap no fetch can distinguish,
    so that one section is graded a round late rather than forgiven.
  - that history anchor is a blunt instrument: it says nothing about a page with no round numbers,
    and nothing about an edit made in the round the page already reached (round 87's own addendum
    read `MISS=3` for eight minutes for exactly that reason). So a loss is also excused — as
    `REVISION-BEHIND`, not `MISS` — when the published copy prints, in the gap between the two
    sentences the tree still agrees with, a run containing wording the tree has nowhere at all.
    A revision adds words and then loses old ones; a renderer swallow only makes tree words
    adjacent, so a glued-together run of tree text (what round 88's live mutation control produced)
    can never excuse itself. The excuse is local to that gap and requires both anchors to be unique
    on the page; a swallow one section away stays a `MISS` (controls N-S). `check_live_sync.py`
    owns the lag itself.
  - `body_visible()` (nav-stripped served text) is the target, so a chunk cannot pass by
    matching the sidebar.
  - chunks inside a GitBook widget body (`{% tabs %}`, `{% stepper %}`, ...) are graded, but in a
    separate bucket: those bodies can be appended by hydration rather than shipped in SSR HTML,
    and "the SSR markup has no room for it" is not yet a reader defect. The bucket must stay
    empty to claim the SSR leg covers them; when it is not, name the pages and check them in a
    browser.

  - the homepage sentence that advertises this judge is read back against its own counters
    (`homepage_parity()`): how many pages it claims to walk, and how many planted controls it names.
    Round 87 recorded that as its open account — a scope that shrinks in silence is the one failure
    mode a completeness judge cannot report about itself, and this axis's object is exactly "what
    this file chose to read".

A green here is only as good as the fetch: a page that could not be downloaded proves nothing, so
fetch failures go to their own bucket and exit non-zero, never to "0 problems" (round 59's split).
"""
import argparse
import bisect
import html
import io
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_aria_manifest as LA   # the shared tokenizer: this judge and the parity judge cannot disagree

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")

MIN_CHUNK = 14          # normalized characters, spaces excluded
SENT_END = re.compile(r"[。；;！!？?]")
# Where the published page may not be read as one continuous sentence: the enders, plus the strings
# the platform inserts into the reader's text (its assistant button after every cell and section end,
# its search box, its opener prompts). Round 88's mutation control proved a glued-together run of
# ordinary table cells can otherwise be pointed at as "proof" that a swallowed sentence was only a
# revision gap.
CHROME = re.compile(SENT_END.pattern +
                    r"|gitbook assistant|ask gitbook|powered by gitbook|ctrl\+?[ik]"
                    r"|what should i read next|can you give an example|\bsend\b", re.I)
# A markup name never starts with a digit: round 83 measured the changelog's own prose `（W<420 且 H>380，
# 宽高比 <0.55）`, and a permissive `<...>` pattern deleted `420 且 H` from the authored side, turning a
# perfectly published sentence into a MISS. Entities arrive from the platform already escaped (`&lt;`),
# so the served side loses nothing by the same, stricter rule.
HTML_TAG = re.compile(r"<(?!br\s*/?>)[a-zA-Z/!][^>]*>")
BR = re.compile(r"<br\s*/?>", re.I)
# The two ranges `live_aria_manifest.visible()` deletes before it strips tags, i.e. the parts of a
# served page this judge never reads: script/style/pre/code/annotation payloads, and GitBook's own
# in-page anchor reprint of every heading. Verbatim mirrors, so the mutation control and the judge
# cannot disagree about what "on the reader's screen" means.
OFFPAGE_BLOCK = re.compile(r"<(script|style|pre|code|annotation)\b.*?</\1>", re.S)
OFFPAGE_NAV = re.compile(r'<a\b[^>]*href="#[^"]*"[^>]*>.*?</a>', re.S)
# A reference with no terminating `;` is shipped as literal text by the platform: round 84 read the
# live raw HTML of changelog L128 and found the authored `&quot` arriving as `&amp;quot`, i.e. the
# reader is shown the word `quot`. Python's `html.unescape` decodes that legacy form, so applying it
# to the *authored source* deleted characters the reader really has and the two sides disagreed about
# the same sentence (one MISS on a page whose text is fully published). Decoding on the authored side
# therefore follows the platform: only `;`-terminated references. The served side keeps plain
# `unescape`, because everything the platform escapes it escapes with a `;`.
BARE_REF = re.compile(r"&(?![A-Za-z][A-Za-z0-9]{1,31};|#(?:\d+|[xX][0-9a-fA-F]+);)")
AMP = "\x02"


def decode_as_platform(text):
    return html.unescape(BARE_REF.sub(AMP, text)).replace(AMP, "&")
INLINE_MATH = re.compile(r"\$\$[^$]*\$\$|\$[^$\n]+\$")
LINK = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
# A bare `<https://…>` autolink is not a tag: the reader's page prints the URL itself between the two
# halves of the sentence, so no unit may straddle it (round 83: three such units read as swallows on
# pages whose text is fully present). Whether that address still resolves is `check_link_graph`'s call.
AUTOLINK = re.compile(r"<(?:https?://|mailto:)[^>\s]+>", re.I)
# GitBook terminates a tag with %}, so a bare % inside an attribute is legal; the same tokenizer
# check_widget_pairing uses, so the two rulers cannot disagree about what a widget tag is.
TAG = re.compile(r"\{%-?\s*([a-zA-Z-]+)((?:%(?!\})|[^%])*)%\}")
BLOCK_OPEN = {"hint", "tabs", "tab", "stepper", "step", "details", "columns", "column",
              "card", "expandable", "accordion", "accordion-item", "toggle", "blockquote"}
BLOCK_CLOSE = {"endhint", "endtabs", "endtab", "endstepper", "endstep", "enddetails",
               "endcolumns", "endcolumn", "endcard", "endexpandable", "endaccordion",
               "endaccordion-item", "endtoggle", "endblockquote"}
INLINE_CODE = re.compile(r"``.+?``|`[^`\n]*`")
HOLE = "\x00"            # a place the reader's text is NOT continuous: nothing may straddle it
SKIP_DIRS = ("assets", ".gitbook", "node_modules")


def frontmatter_end(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def chunks(text):
    """[(kind, chunk, line)] for every authored sentence-run a reader should be able to find.

    kind is 'plain' (prose), 'heading' (an `##`-and-deeper title), 'quote' (a `>` blockquote line)
    or 'widget' (a line inside a `{% %}` component body). A chunk never straddles a code span, a formula, a link, a `<br>` or a
    widget tag, because the published page does not print those as plain text either: KaTeX ships
    its own characters between two halves of a sentence, so a joined unit could never match and the
    MISS would be the ruler's, not the reader's. Round 83's first pass on one page read 19 MISS,
    and every single one was a straddle, a fence/formula body or a tag attribute.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    mask, _ = LA.fence_prose_mask(text)
    out, depth, display = [], 0, False
    for n, line in enumerate(lines):
        if n < frontmatter_end(lines) or n >= len(mask) or not mask[n]:
            continue
        s = line.strip()
        if s == "$$":                                   # a display block is not prose
            display = not display
            continue
        if display or not s or s.startswith("!["):
            continue
        heading = quote = False
        if s.startswith(">"):
            # A blockquote is the reader's own sentence, printed inside a styled box. Round 88
            # measured 42 such lines on 32 pages, which produce 57 units on 28 of them —
            # prose this judge had been walking straight past.
            quote = True
            s = re.sub(r"^>+\s*", "", s).strip()
            if not s:
                continue
        if s.startswith("#"):
            # A body `# H1` is deliberately excluded: measured in round 55, GitBook drops it and
            # publishes the SUMMARY label as the reader's heading, so grading it would report the
            # platform's documented swap as a swallow. `check_nav_h1_sync.py` owns that equality.
            if not re.match(r"^#{2,6} +\S", s):
                continue
            heading = True
            s = s.lstrip("#").strip()
        # GitBook numbers an ordered list with CSS, so the "1." the author typed is nowhere in the
        # served text. Round 83 measured this on four pages and every one of their 30 losses was
        # this: a self-test item graded as "the reader never got 1 …" while the item is fully there.
        ordered = re.match(r"^\s*\d+[.)]\s+", s)
        names = [m.group(1) for m in TAG.finditer(INLINE_CODE.sub(" ", s))]
        on_tag_line = bool(names)
        body = TAG.sub(HOLE, LA.strip_code_spans(s, HOLE))
        for name in names:
            if name in BLOCK_CLOSE:
                depth = max(depth - 1, 0)
            elif name in BLOCK_OPEN:
                depth += 1
        body = INLINE_MATH.sub(HOLE, LINK.sub(HOLE, AUTOLINK.sub(HOLE, BR.sub(HOLE, body))))
        body = HTML_TAG.sub(" ", body)
        kind = ("heading" if heading else ("widget" if (depth or on_tag_line)
                                           else ("quote" if quote else "plain")))
        for pi, part in enumerate(body.split(HOLE)):
            for i, piece in enumerate(SENT_END.split(decode_as_platform(part))):
                if pi == 0 and i == 0 and ordered:
                    piece = re.sub(r"^\s*\d+[.)]\s+", " ", piece)
                # `|` is a HOLE, not a space: round 83 found the published page printing its own
                # "gitbook assistant" button label between every table cell, so a whole-row unit can
                # never match a table that is otherwise perfectly readable. One unit per cell.
                piece = re.sub(r"^[-*+\s]|\|", HOLE, piece).replace("\\", HOLE)
                for run in piece.split(HOLE):
                    u = re.sub(r"\s+", " ", LA.norm(run)).strip()
                    if len(u.replace(" ", "")) >= MIN_CHUNK:
                        out.append((kind, u, n + 1))
    return out


def walk(root=DOCS):
    """Every markdown page a reader can be sent to.

    Round 86 close-out measured that `14-templates/` carries three `status: published` pages whose
    H1s all resolve in `LA.url_index()` — including `style-guide.md`, the page that *defines* the
    emphasis rules and the genre-floor table every other judge reads. The old dirpath skip was
    inherited from `live_aria_manifest.build`, where the same filter is only a work-saver (that
    walker keeps pages with widgets/formulas/mermaid, and a scaffold-only page falls out anyway).
    A completeness judge has no such reason to look away. Now the only filter is per-file: no
    published address => nothing to compare, so the row never enters the fetch set (see run()).
    """
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn.endswith(".md") and fn != "SUMMARY.md":
                rows.append(os.path.join(dirpath, fn))
    return sorted(rows)


def served_chunks(html_text):
    # Entities are decoded AFTER tag stripping and BEFORE norm(): the published page ships `"` as
    # `&quot;`, and norm() keeps alphanumerics, so an undecoded entity reaches the comparison as the
    # literal word "quot" and every quoted phrase on the site reads as a swallow (round 83).
    return LA.norm(html.unescape(HTML_TAG.sub(" ", LA.body_visible(html_text))).replace("\\", " "))


ROUND_MENTION = re.compile(r"第\s*(\d+)\s*次")
ROUND_HEADING = re.compile(r"^#{1,6}.*?第\s*(\d+)\s*次")


def served_speech(html_text):
    """The served page as the reader's browser would read it aloud: tags gone, entities decoded."""
    return html.unescape(HTML_TAG.sub(" ", LA.body_visible(html_text)))


def published_cut(text, served_html):
    """The first line this page's PUBLISHED copy provably carries, or None when it cannot say.

    A page that names its rounds can date its own published copy: if the served text's newest
    mention is round N while the file has reached round M, sections newer than N are not swallowed,
    they are unreleased (round 83 measured exactly that on the 18 MB changelog page, pinned at 79
    across six fetches).

    Round N's *own* section is unpinned too. A round's close-out commit edits the section it just
    published, so the reader can hold round N's heading and an older revision of its body; round 83
    caught this directly — the served page printed 读者侧抽查 3 页 6 条针 while HEAD's round-79
    section says 6/6, i.e. the platform shipped round 79's first commit and not its close-out. So
    grading resumes at the next section *older* than N. The cost is honest and small: the newest
    published round's prose is graded one round late.

    The cut comes from the page's own printed text, never from a list of page names, so no page is
    forgiven by name. A history that is not strictly newest-first cannot date itself at all, so it
    gets no cut and is graded in full.
    """
    marks = []
    for n, line in enumerate(text.split("\n")):
        m = ROUND_HEADING.match(line.strip())
        if m:
            marks.append((n + 1, int(m.group(1))))
    if not marks:
        return None
    rounds = [r for _l, r in marks]
    if rounds != sorted(set(rounds), reverse=True):
        return None
    live = [int(x) for x in ROUND_MENTION.findall(served_speech(served_html))]
    newest = max(live) if live else 0
    if newest >= rounds[0]:
        return None                                # the reader is at the newest round: grade all
    return min((l for l, r in marks if r < newest), default=len(text.split("\n")) + 1)


def grade(units, served_norm):
    """[(kind, line, chunk)] that a reader cannot find on the published page, in reading order.

    Whether a loss is a swallow or simply an unpublished revision is the caller's call, made with
    `published_cut()` below — this function only knows present from absent.
    """
    flat = re.sub(r"\s+", " ", served_norm)
    return [(k, ln, u) for k, u, ln in units
            if re.sub(r"\s+", " ", u) not in flat]


def served_only_sentences(html_text, nflat, tree_norm):
    """Published sentences the authored file has nowhere, minus platform chrome.

    The served text is cut on the sentence enders *and* on the strings the platform inserts — the
    "gitbook assistant" label it tacks after every table cell and section end (round 83), its
    search box and its opener prompts. Round 88's live mutation control is what proved this
    necessary: hiding one real sentence let the judge point at a neighbouring piece that read
    `gitbook assistant 8 张真实产品 ui 截图 目录内 url 与访问日期 …`, i.e. a list of ordinary table
    cells glued together by button labels. Cut at the labels, each cell is tree text again and the
    false proof disappears.

    Positions are into `nflat`, the same view the anchors are located in: `LA.norm` turns every run
    of markup/punctuation into one space, so a sentence found here and a sentence found there are
    coordinates in one ruler. Against the punctuated copy a normalized sentence would simply fail
    to be found, and the bucket would silently never fire.
    """
    speech = decode_as_platform(html.unescape(HTML_TAG.sub(" ", LA.body_visible(html_text))))
    out, start = [], 0
    for cut in CHROME.finditer(speech):
        piece, start = speech[start:cut.start()], cut.end()
        u = re.sub(r"\s+", " ", LA.norm(piece)).strip()
        if len(u.replace(" ", "")) < MIN_CHUNK or not says_something_new(u, tree_norm) \
                or nflat.count(u) != 1:
            continue
        out.append((nflat.index(u), u))
    return sorted(out)


def says_something_new(u, tree_norm):
    """Does this published run say a word the authored tree never says anywhere?

    This is what separates the two failures the run's text could evidence:

      - a *revision* — the published page is an older copy of this region, so it carries wording the
        tree has deleted. At least one of its stretches exists nowhere in the tree.
      - a *swallow* — the page is the tree with a hole punched in it, so whatever the page prints
        around the hole is tree text, merely adjacent. Nothing is new; the difference is all
        subtraction.

    Round 88's live mutation control is the case that forced the distinction: hiding one sentence in
    the changelog's figure table glued `8 张真实产品 ui 截图 目录内 …` into a run the tree has nowhere,
    and that run excused the very deletion that produced it. Every word of it came from the tree.

    `LA.norm` leaves one stretch per run of CJK/alphanumerics, so a `token` here is a whole phrase,
    not a character — which is why a two-character floor is enough to keep single digits and letters
    from counting as novelty.
    """
    return any(t not in tree_norm for t in u.split(" ") if len(t) > 1)


def classify(units, flat, html_text, tree_norm):
    """(rows, evidence) for the units a reader cannot find.

    rows are [(kind, line, chunk, verdict, excuser)]; verdict is MISS or REVISION-BEHIND, and an
    excuser is the [(position, sentence)] entry that proved it — the published copy's own older
    wording, carried on the row it excuses rather than printed from the top of the page.

    `published_cut()` dates a page that prints round numbers, and says nothing about a page that
    does not — nor about a same-round close-out edit. Round 87 measured that hole twice on its own
    page: its addendum read `MISS=3` for eight minutes while the served copy still printed the
    previous commit's wording of that very paragraph, and the round anchor had already returned
    None because the reader *was* at round 87.

    So the evidence is made local instead: a loss is an unreleased revision only when the published
    copy prints, in the gap between the two sentences the tree still agrees with, a sentence that
    says something the tree never says anywhere (see `says_something_new`). That is a different
    revision of *this* region, and nothing excuses a swallow one section away — the anchors must be
    unique on the page, or the judge keeps the failure.
    """
    nflat = re.sub(r"\s+", " ", LA.norm(flat))
    present = [re.sub(r"\s+", " ", u) in flat for _k, u, _l in units]
    evidence = served_only_sentences(html_text, nflat, tree_norm)
    rows = []
    for i, (kind, u, ln) in enumerate(units):
        if present[i]:
            continue
        before = next((j for j in range(i - 1, -1, -1) if present[j]), None)
        after = next((j for j in range(i + 1, len(units)) if present[j]), None)
        verdict, excuser = "MISS", None
        if before is not None and after is not None:
            prev_n = re.sub(r"\s+", " ", LA.norm(units[before][1]))
            next_n = re.sub(r"\s+", " ", LA.norm(units[after][1]))
            # A unit present in the punctuated copy is present in this view too, so a unique hit
            # here means the two anchors bracket exactly one region of the published page.
            if nflat.count(prev_n) == 1 and nflat.count(next_n) == 1:
                lo = nflat.index(prev_n) + len(prev_n)
                hi = nflat.index(next_n)
                in_gap = [it for it in evidence if lo <= it[0] < hi]
                if in_gap:
                    verdict, excuser = "REVISION-BEHIND", in_gap[0]
        rows.append((kind, ln, u, verdict, excuser))
    return rows, evidence


def fetch_page(url):
    # A reset connection is noise, not a swallowed sentence, so one retry; a page that survives two
    # attempts is still a bucket of its own and still exits non-zero (round 83 saw two SSL resets).
    err = None
    for _ in range(2):
        try:
            return url, LA.fetch(url), None
        except Exception as exc:                              # noqa: BLE001 - a flaked fetch is a bucket, not a trace
            err = "%s: %s" % (type(exc).__name__, str(exc)[:90])
    return url, "", err


def run(sample=None, workers=6, only=None):
    index = LA.url_index()
    rows, unlabeled = [], []
    for path in walk():
        text = io.open(path, encoding="utf-8").read()
        units = chunks(text)
        if not units:
            continue
        rel = os.path.relpath(path, DOCS).replace("\\", "/")
        if only and only not in rel:
            continue
        url = index.get(LA.norm(LA.h1_of(text)))
        if not url:
            unlabeled.append(rel)
            continue
        rows.append({"page": rel, "url": url, "units": units, "text": text})
    rows.sort(key=lambda r: (-len(r["units"]), r["page"]))
    picked = rows if not sample else rows[:sample]
    _label, _unl = "all", len(unlabeled)
    if sample and only is None:                           # a sample cannot judge the whole site's coverage
        _label, _unl = "sample:%d/%d" % (len(picked), len(rows)), 0
    problems, fetch_fail, pages_lost = [], [], []
    total = sum(len(r["units"]) for r in picked)
    plain = sum(1 for r in picked for k, _u, _l in r["units"] if k == "plain")
    heading = sum(1 for r in picked for k, _u, _l in r["units"] if k == "heading")
    quote = sum(1 for r in picked for k, _u, _l in r["units"] if k == "quote")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        # pool.map keeps the input order, so a row is graded against its own page and one HTML
        # document is held in memory at a time (the changelog alone is 18 MB).
        for r, (_url, served, err) in zip(picked, pool.map(lambda x: fetch_page(x["url"]), picked)):
            if err or not served:
                fetch_fail.append("%s %s" % (r["page"], err or "empty body"))
                continue
            flat = re.sub(r"\s+", " ", served_chunks(served))
            lost = grade(r["units"], flat)
            if not lost:
                continue
            # Two failures look identical, so they are separated by evidence rather than by a guess:
            # `published_cut()` asks the page itself which round it has published. Text above that
            # line is an unreleased revision (round 83: the changelog page pinned at 79 in an 18 MB
            # document, whose round-79 section had since been amended by its own close-out commit);
            # text below it, or on a page with no round history, the renderer swallowed.
            cut = published_cut(r["text"], served)
            rows, _evidence = classify(r["units"], flat, served,
                                        re.sub(r"\s+", " ", LA.norm(r["text"])))
            unreleased = [t for t in rows if cut and t[1] < cut]
            rest = [t for t in rows if not (cut and t[1] < cut)]
            behind = [t for t in rest if t[3] == "REVISION-BEHIND"]
            miss = [t for t in rest if t[3] == "MISS"]
            pages_lost.append((r["page"], len(miss), len(unreleased), len(r["units"]), cut,
                               miss[:3], len(behind), behind[:1]))
            for tag, items in (("MISS", miss), ("REVISION-BEHIND", behind), ("STALE-COPY", unreleased)):
                for kind, ln, u, _v, _exc in items:
                    problems.append("%s %s %s:%d %s" % (tag, kind.upper(), r["page"], ln, u))
    n_miss = sum(p[1] for p in pages_lost)
    n_stale = sum(p[2] for p in pages_lost)
    n_behind = sum(p[6] for p in pages_lost)
    print("prose survival: pages=%d units=%d plain=%d heading=%d quote=%d widget=%d | %s" %
          (len(picked), total, plain, heading, quote, total - plain - heading - quote, _label))
    print("lost sentences: MISS=%d REVISION-BEHIND=%d STALE-COPY=%d | pages-with-MISS=%d "
          "fetch-failures=%d not-listed=%d"
          % (n_miss, n_behind, n_stale, sum(1 for p in pages_lost if p[1]), len(fetch_fail), _unl))
    for pg, nm, ns, nu, cut, sample, nb, bsample in sorted(pages_lost, key=lambda p: (-p[1], -p[6], -p[2]))[:12]:
        print("   %-44s MISS=%-4d behind=%-4d unpublished=%-4d of %d units%s"
              % (pg, nm, nb, ns, nu, "" if not cut else "  (published copy proves nothing below line %d)" % cut))
        for kind, ln, u, _v, _exc in sample:
            print("       %s:%d %s" % (kind.upper(), ln, u[:70]))
        if nb:
            bkind, bln, bu, _v, exc = bsample[0]
            print("       e.g. %s:%d %s" % (bkind.upper(), bln, bu[:60]))
            print("       excused because the published copy prints this instead, and the tree "
                  "has it nowhere (offset %d): %s" % (exc[0], exc[1][:60]))
    for f in fetch_fail[:10]:
        print("   FETCH", f)
    return n_miss, n_stale, len(fetch_fail) + len(unlabeled if _label == "all" else []), n_behind


def control_letters():
    """The control letters this file asserts on, read back out of its own source."""
    src = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    return sorted(set(re.findall(r'errs\.append\("control ([A-Z])', src)))


def homepage_parity():
    """The homepage's two numbers about this judge must be this judge's own numbers.

    Round 87's meta-lesson was that a completeness judge is trusted for a scope nobody measures: its
    视野 shrank by three published pages and every one of its own controls stayed green, because a
    control can only fire inside the text the walker hands it. This is that alarm, and it reads the
    page a reader reads: 「把 N 篇正文。」「N 条种植控制（A–T）」 must equal `len(walk())` and the
    letters asserted above. Adding a page costs nothing; adding a control without telling the reader
    does not pass.
    """
    out = []
    line = next((l for l in io.open(os.path.join(DOCS, "README.md"), encoding="utf-8").read().split("\n")
                 if "check_prose_survival.py" in l), None)
    if line is None:
        return ["homepage: no sentence cites check_prose_survival.py, so its 完整性 claim has no judge"]
    pages = re.search(r"把 (\d+) 篇正文", line)
    if not pages or int(pages.group(1)) != len(walk()):
        out.append("homepage: 「%s 篇正文」 is not this judge's view of %d pages"
                   % (pages and pages.group(1), len(walk())))
    letters = control_letters()
    ctrl = re.search(r"(\d+) 条种植控制（([A-Z])[–-]([A-Z])", line)
    if not ctrl:
        out.append("homepage: the controls must be cited as 「N 条种植控制（A–T）」 so this assertion "
                   "can check them")
    else:
        span = [chr(c) for c in range(ord(ctrl.group(2)), ord(ctrl.group(3)) + 1)]
        if span != letters or int(ctrl.group(1)) != len(letters):
            out.append("homepage: 「%s 条种植控制（%s–%s）」 is not the %d controls asserted here (%s)"
                       % (ctrl.group(1), ctrl.group(2), ctrl.group(3), len(letters),
                          "".join(letters)))
    return out


def controls():
    """Every bucket must be able to fire, and the judge must miss nothing it is shown."""
    errs = []
    served = ("<html><body><article><p>这一句读者应当看到，它完整地发布在页面上。</p>"
              "<pre><code>import os</code></pre><p>被吞掉的后半句不见了</p></article>"
              "<nav>导航里的重复文字 这一句读者应当看到，它完整地发布在页面上。</nav>"
              "</body></html>")
    body = re.sub(r"<nav>.*?</nav>", " ", served, flags=re.S)
    good, bad = chunks("这一句读者应当看到，它完整地发布在页面上。\n被吞掉的后半句也不在这里啊喂。"), served_chunks(body)
    hits = grade(good, bad)
    if len(hits) != 1 or "被吞掉" not in hits[0][2]:
        errs.append("control A: swallowed clause must be the only MISS, got %r" % (hits,))
    fenced = chunks("正文如下，这是一个围栏示例的开场：\n```\n这一段住在围栏里，它绝不该被当成正文judge掉\n```")
    if any("围栏里" in u for _k, u, _l in fenced):
        errs.append("control B: fenced body must not become prose, got %r" % (fenced,))
    w = chunks("{% tabs %}\n{% tab title=\"甲\" %}\n这一段住在组件体内，它需要水合才会出现。\n{% endtab %}\n{% endtabs %}")
    if not w or w[0][0] != "widget":
        errs.append("control C: widget body must be labelled, got %r" % (w,))
    if len(chunks("---\ntitle: 演示\nupdated: 2026-01-01\n---\n这一句才是真正的正文，它必须被计入 units。\n")) != 1:
        errs.append("control D: frontmatter must not be graded as prose")
    # E + F are the two shapes round 83's site-wide pass reported as 1923 swallows: both are the
    # ruler's, and a control that cannot reproduce them would let the next such bug read as content.
    row = "| [x/y](https://github.com/x/y) | 14.6 万 | MIT | Python | 这是一段足够长的框架点评文字。 |\n"
    row_units = chunks(row)
    row_served = ("<table><tbody><tr><td><a>x/y</a><span>gitbook assistant</span></td>"
                  "<td>14.6 万<span>gitbook assistant</span></td><td>MIT</td><td>Python</td>"
                  "<td>这是一段足够长的框架点评文字<span>gitbook assistant</span></td></tr></tbody></table>")
    if [c for k, c, ln in row_units if c not in re.sub(r"\s+", " ", served_chunks(row_served))]:
        errs.append("control E: a table cell must survive the platform's per-cell button text, got %r"
                    % (row_units,))
    quoted = chunks('文档里写着"这一句被引号包住并且足够长以成为单位"，它应当发布在页面上。\n')
    if len(quoted) != 1:
        errs.append("control F: the quoted sentence must be one unit, got %r" % (quoted,))
    ent = '<p>文档里写着 &quot;这一句被引号包住并且足够长以成为单位&quot; ，它应当发布在页面上。</p>'
    if grade(quoted, served_chunks(ent)):
        errs.append("control F: an HTML-quoted sentence must not read as a swallow, got %r"
                    % (grade(quoted, served_chunks(ent)),))
    # K: the semicolon-less reference, which is the mirror image of F. Round 84's post-sync sweep read
    # one MISS on a sentence the reader does have: the authored `&quot` reaches the page as the literal
    # word `quot`, so the authored side must not decode it away. Both directions are asserted — the
    # word survives slicing, and the two sides agree on the shipped HTML.
    bare = chunks("这一句里写着一个不带分号的实体引用 &quot 它后面的汉字也足够长能成为单位。\n")
    if not any("quot" in u for _k, u, _l in bare):
        errs.append("control K: a semicolon-less reference must stay literal text, got %r" % (bare,))
    bare_served = "<p>这一句里写着一个不带分号的实体引用 &amp;quot 它后面的汉字也足够长能成为单位。</p>"
    if grade(bare, served_chunks(bare_served)):
        errs.append("control K: a literal-ampersand sentence must reach the reader intact, got %r"
                    % (grade(bare, served_chunks(bare_served)),))
    blind = served_chunks(bare_served.replace("它后面的汉字也足够长能成为单位", " "))
    if not grade(bare, blind):
        errs.append("control K: hiding the clause after a bare reference must still read as a swallow")
    # L: emphasis markers, pinned in the direction the platform actually goes. Round 86's one site-wide
    # MISS (changelog L75) tempted the ruler to delete `**` from the authored unit; measured on the
    # changelog that "fix" turned 1 MISS into 643, because `served_chunks` replaces every tag with a
    # space, so a normally rendered mid-clause `**x**` really does print `x` with spaces around it. A
    # MISS of that shape is therefore the platform pairing the markers somewhere the author did not —
    # a reader-visible defect in the copy, and it must stay a MISS.
    bold = chunks("这一句读者完整看得到，那条轴**中段加粗的那半句**，前几轮它抓的都是历史欠账。\n")
    if not any("那条轴 中段加粗的那半句" in u for _k, u, _l in bold):
        errs.append("control L: a marker must enter the unit as the space the page prints, got %r" % (bold,))
    bold_served = "<p>这一句读者完整看得到，那条轴<strong>中段加粗的那半句</strong>，前几轮它抓的都是历史欠账。</p>"
    if grade(bold, served_chunks(bold_served)):
        errs.append("control L: a rendered <strong> sentence must not read as a swallow, got %r"
                    % (grade(bold, served_chunks(bold_served)),))
    if not grade(bold, served_chunks(bold_served.replace("中段加粗的那半句", " "))):
        errs.append("control L: hiding the bold clause must still read as a swallow")
    if not grade(bold, served_chunks(bold_served.replace("那条轴<strong>", "那条轴"))):
        errs.append("control L: a bold run the platform opened somewhere else must stay a MISS, "
                    "not be paid for by deleting markers")
    # M: coverage. `walk()` used to `continue` on any dirpath containing `14-templates`, on the
    # premise those files were not on the site. Round 86 close-out measured that premise false:
    # all three files carry `status: published` and their H1s resolve in `LA.url_index()`, so the
    # page that *defines* the emphasis rules had no resident completeness judge. The scan-blind
    # shape a judge can slide back into is "0 pages graded, 0 problems", so pin a positive floor
    # on the templates subset and, more sharply, on the guide itself.
    tpls = [p for p in walk() if "14-templates" in p.replace("\\", "/")]
    if len(tpls) < 3 or not any(p.replace("\\", "/").endswith("14-templates/style-guide.md")
                                for p in tpls):
        errs.append("control M: walk() must cover published 14-templates pages (>=3, incl. "
                    "style-guide.md), got %r" % (tpls,))
    # G: the list marker. H: the pinned-page cut, which must fire on the page's own round text only.
    items = chunks("1. **这是一条足够长的自测清单项目**：说明部分同样足够长\n")
    if not items or items[0][1].startswith("1 "):
        errs.append("control G: an ordered-list marker must not enter the unit, got %r" % (items,))
    # I: a bare autolink prints its own URL between the two halves of the sentence, so it must end a
    # unit. Round 83 measured three such units read as swallows on pages whose text is fully live.
    auto = chunks("这一半句子足够长所以它必然成为单位，地址是 <https://huggingface.co/datasets/EleutherAI/pile> "
                  "那一半也足够长所以它同样成为单位。\n")
    if len(auto) != 2 or any("huggingface" in u for _k, u, _l in auto):
        errs.append("control I: an autolink must end a unit, never join across it, got %r" % (auto,))
    history = ("## 2026-09-25（第 82 次）新round的正文句子甲，它还没有发布出去\n"
               "## 2026-09-24（第 81 次）旧round的正文句子乙，它的收尾补写还没发布\n"
               "## 2026-09-24（第 80 次）更旧round的正文句子丙，它已经在页面上了\n")
    old_copy = "<article>第 81 次 旧round的正文句子乙。第 80 次 更旧round的正文句子丙。</article>"
    # The served copy names round 81, yet round 81's own close-out prose (added after its push) is
    # absent — exactly what round 83 measured on the live changelog. Grading must resume at round 80.
    if published_cut(history, old_copy) != 3:
        errs.append("control H: served copy at round 81 must grade from round 80's heading down, got %r"
                    % published_cut(history, old_copy))
    new_copy = "<article>第 82 次 新round的正文句子甲。第 81 次 旧round的正文句子乙。</article>"
    if published_cut(history, new_copy) is not None:
        errs.append("control H: a current page must not be cut, got %r" % published_cut(history, new_copy))
    if published_cut("正文里没有任何轮次标题的一页文字。\n", "<article>无关</article>") is not None:
        errs.append("control H: a page with no round history has no cut")
    shuffled = ("## 2026-09-24（第 80 次）最旧round的正文句子丙，它已经在页面上了\n"
                "## 2026-09-25（第 82 次）新round的正文句子甲，它还没有发布出去\n")
    if published_cut(shuffled, old_copy) is not None:
        errs.append("control H: a history that is not newest-first must not be cut")
    # J: the angle-bracket trap. Round 83's own changelog prose carries `（W<420 且 H>380）`, and a tag
    # pattern loose enough to match it hides `420 且 H` on the authored side — a published sentence
    # reported as swallowed. Both halves must survive, escaped or not.
    angle = chunks("宽度达标不等于排布合理：把每块的 W×H 一起量出来后，发现 40 个块是「窄高细条」"
                   "（W<420 且 H>380，宽高比 <0.55）。\n")
    if not any("420" in u and "380" in u for _k, u, _l in angle):
        errs.append("control J: prose angle brackets must not be eaten as a tag, got %r" % (angle,))
    angle_served = ("<p>宽度达标不等于排布合理：把每块的 W×H 一起量出来后，发现 40 个块是「窄高细条」"
                    "（W&lt;420 且 H&gt;380，宽高比 &lt;0.55）。</p>")
    if grade(angle, served_chunks(angle_served)):
        errs.append("control J: an escaped-angle-bracket sentence must reach the reader intact, got %r"
                    % (grade(angle, served_chunks(angle_served)),))
    # N/O/P/Q: the third bucket, which must be able to fire AND must not be able to excuse a real
    # loss. Round 87's close-out read `MISS=3` on its own page for eight minutes because the served
    # copy still printed the previous commit's wording of that paragraph; `published_cut()` could
    # not see it, since the page had already published round 87. These four cases are that incident
    # and the three ways an excuse built on it could overreach.
    a = "甲段第一句读者完整看得到，它写得足够长，所以必然成为一个单位。\n"
    bn = "甲段第二句在本次修订里换了新措辞，旧版那句话已经不在树里。\n"
    bo = "甲段第二句从前是一种旧措辞，它此刻还留在已经发布的页面上。\n"
    c = "甲段第三句读者完整看得到，它同样写得足够长以成为一个单位。\n"
    dd = "乙段第一句被渲染器整个吞掉了，读者在页面上找不到它的任何一个字。\n"
    e = "乙段第二句读者完整看得到，它也足够长所以能够成为一个单位。\n"

    def bucketed(authored, printed):
        html = "<article>" + "".join("<p>%s</p>" % s for s in printed) + "</article>"
        flat = re.sub(r"\s+", " ", served_chunks(html))
        return classify(chunks(authored), flat, html, re.sub(r"\s+", " ", LA.norm(authored)))

    rows, evid = bucketed(a + bn + c, [a, bo, c])
    if [(u[:6], v) for _k, _l, u, v, _x in rows] != [("甲段第二句在", "REVISION-BEHIND")] or not evid:
        errs.append("control N: an older revision printed where the tree has new wording must be "
                    "REVISION-BEHIND with evidence, got %r / %r" % (rows, evid))
    if rows[0][4] is None or "从前是一种旧措辞" not in rows[0][4][1]:
        errs.append("control N: an excused row must carry its own proof, got %r" % (rows,))
    rows2, _ = bucketed(a + bn + c, [a, c])
    if [(u[:6], v) for _k, _l, u, v, _x in rows2] != [("甲段第二句在", "MISS")]:
        errs.append("control O: a clause with nothing printed in its gap must stay MISS, got %r" % (rows2,))
    if rows2[0][4] is not None:
        errs.append("control O: a MISS must not claim an excuser, got %r" % (rows2,))
    rows3, evid3 = bucketed(a + bn + c + dd + e, [a, bo, c, e])
    if sorted((u[:6], v) for _k, _l, u, v, _x in rows3) != [("乙段第一句被", "MISS"), ("甲段第二句在", "REVISION-BEHIND")]:
        errs.append("control P: stale text in one region must not excuse a swallow in another, got %r" % (rows3,))
    if evid3 and evid3[0][1] != re.sub(r"\s+", " ", LA.norm(bo)).strip():
        errs.append("control P: the evidence must be the page's own older sentence, got %r" % (evid3[:1],))
    rows4, _ = bucketed(a + bn + c, [a, bo, c, a])
    if [(u[:6], v) for _k, _l, u, v, _x in rows4] != [("甲段第二句在", "MISS")]:
        errs.append("control Q: anchors that occur twice on the page bracket no single region, so "
                    "the loss must stay MISS, got %r" % (rows4,))
    # R: the shape the live page actually produced when round 88 hid one real sentence in the
    # changelog's own figure table. The judge pointed at `gitbook assistant 8 张真实产品 ui 截图
    # 目录内 url 与访问日期 …` as "proof of an older revision" — but that run is ordinary cells
    # glued together by the button label the platform inserts after each one, and every cell is
    # tree text. Cutting at the labels makes each fragment a substring of the tree, and a fragment
    # the tree has cannot excuse anything.
    cells = ("| 这一段是表格里的第一格内容甲 | 这一段是表格里的第二格内容乙 |\n")
    glued = ("<article><table><tbody><tr>"
             "<td>这一段是表格里的第一格内容甲<span>gitbook assistant</span></td>"
             "<td>这一段是表格里的第二格内容乙<span>gitbook assistant</span></td>"
             "</tr></tbody></table></article>")
    glued_flat = re.sub(r"\s+", " ", LA.norm(served_chunks(glued)))
    false_proof = served_only_sentences(glued, glued_flat, re.sub(r"\s+", " ", LA.norm(cells)))
    if false_proof:
        errs.append("control R: cells glued by the assistant label are tree text and must not "
                    "count as an older revision, got %r" % (false_proof,))
    stale_in_table = glued.replace("第一格内容甲", "第一格内容甲从前是这么写的")
    if not served_only_sentences(stale_in_table,
                                 re.sub(r"\s+", " ", LA.norm(served_chunks(stale_in_table))),
                                 re.sub(r"\s+", " ", LA.norm(cells))):
        errs.append("control R: an older cell beside them must still be found — the chrome cut "
                    "must not blind the bucket")
    # S: `says_something_new`, the rule that round 88's live mutation control actually needed. Hiding
    # one sentence in the changelog's figure table made the page read `[tail of the vandalised cell]
    # + [the next cells]` — a run the tree has nowhere, because the deleted words sit inside it. That
    # is a swallow's fingerprint: the page added no words, it only lost them, so every stretch it
    # prints is still tree text. An older revision is the opposite — it prints wording the tree
    # deleted. The synthetic page cannot reproduce the fingerprint (delete anything there and the run
    # stays a substring of the tree), so the rule that decides it is pinned directly, both ways.
    frag_a, frag_b = "这一段是表格里的第一格内容甲在这里", "这一段是表格里的第二格内容乙在这里"
    glued_run, tree_with_gap = "%s %s" % (frag_a, frag_b), "%s 中间被删掉的那一格 %s" % (frag_a, frag_b)
    if says_something_new(LA.norm(glued_run), LA.norm(tree_with_gap)):
        errs.append("control S: two tree fragments glued across a deletion say nothing the tree "
                    "never says, so they must not excuse a loss")
    if not says_something_new(LA.norm(bo), LA.norm(a + bn + c)):
        errs.append("control S: a page's own older sentence must count as new words, or the bucket "
                    "cannot tell a lag from a swallow")
    # T: the heading leg. Before round 88 no live axis had ever read a published section title, so a
    # swallowed `##` — or one that lost the words its 本页目录 entry is built from — stayed green in
    # every judge the repo has. Three shapes must hold at once: a `##` becomes a unit of its own
    # kind, a body `#` never does (measured round 55: GitBook publishes the SUMMARY label there),
    # and a `##` inside a fenced example is not a reader's heading at all.
    heads_doc = ("# 一级标题由平台换成侧栏标签所以这一条永远不是单位\n"
                 "## 二到六级标题必须作为独立单位到达读者的眼睛\n"
                 "正文这一句足够长，它必须仍然按散文单独判一次。\n"
                 "```markdown\n## 围栏里演示的假标题绝不该算作读者的标题\n```\n")
    hu = chunks(heads_doc)
    if [(k, u[:6]) for k, u, _l in hu] != [("heading", "二到六级标题"), ("plain", "正文这一句足")]:
        errs.append("control T: an `##` must become exactly one heading unit beside the prose, got %r"
                    % (hu,))
    if any("一级标题由平台" in u or "围栏里演示" in u for _k, u, _l in hu):
        errs.append("control T: a body `#` and a fenced example title must not become units, got %r"
                    % (hu,))
    on_page = ("<article><h2>二到六级标题必须作为独立单位到达读者的眼睛</h2>"
               "<p>正文这一句足够长，它必须仍然按散文单独判一次。</p>"
               "<h1>一级标题由平台换成侧栏标签所以这一条永远不是单位</h1></article>")
    flat_head = re.sub(r"\s+", " ", served_chunks(on_page))
    if grade(hu, flat_head):
        errs.append("control T: a published heading must read clean, got %r" % (grade(hu, flat_head),))
    hits = grade(hu, re.sub(r"\s+", " ", served_chunks(on_page.replace("<h2>%s</h2>" %
               "二到六级标题必须作为独立单位到达读者的眼睛", ""))))
    if len(hits) != 1 or hits[0][0] != "heading" or "二到六级" not in hits[0][2]:
        errs.append("control T: a swallowed heading must be named as the only loss, got %r" % (hits,))
    # U: the blockquote leg. Round 88 measured 42 `>` lines carrying 57 floor-clearing runs of prose
    # that this judge had walked past since it was written — a sentence inside a styled box is still
    # the reader's sentence. The leg has to gain that prose without gaining the syntax that documents
    # it (`![...]` image lines and a `>` sitting inside a fenced example).
    quote_doc = ("> 引用块里的这句话必须作为独立单位到达读者的眼睛\n"
                 "正文这一句足够长，它必须仍然按散文单独判一次。\n"
                 "![一张图的替代文字并不作为正文出现在读者面前](/assets/nope.svg)\n"
                 "```\n> 围栏里演示的假引用绝不该算作读者的句子\n```\n")
    qu = chunks(quote_doc)
    if [(k, u[:6]) for k, u, _l in qu] != [("quote", "引用块里的这"), ("plain", "正文这一句足")]:
        errs.append("control U: a `>` line must become exactly one quote unit beside the prose, got %r"
                    % (qu,))
    if any("围栏里演示" in u or "替代文字" in u for _k, u, _l in qu):
        errs.append("control U: a fenced example quote and an image alt text must not become units, "
                    "got %r" % (qu,))
    q_page = ("<article><blockquote><p>引用块里的这句话必须作为独立单位到达读者的眼睛</p></blockquote>"
              "<p>正文这一句足够长，它必须仍然按散文单独判一次。</p></article>")
    if grade(qu, re.sub(r"\s+", " ", served_chunks(q_page))):
        errs.append("control U: a published blockquote must read clean, got %r"
                    % (grade(qu, re.sub(r"\s+", " ", served_chunks(q_page))),))
    qhits = grade(qu, re.sub(r"\s+", " ", served_chunks(
        q_page.replace("<p>引用块里的这句话必须作为独立单位到达读者的眼睛</p>", ""))))
    if len(qhits) != 1 or qhits[0][0] != "quote" or "引用块" not in qhits[0][2]:
        errs.append("control U: a swallowed blockquote must be named as the only quote loss, got %r"
                    % (qhits,))
    # V: where a page keeps several copies of the same sentence, and which of them a reader is shown.
    # Round 89's live control found its own accounting wrong here twice: counting raw occurrences
    # treated GitBook's sidebar reprint and the `<script>` editor payload as copies the reader has,
    # so hiding a real plain sentence that only exists in that payload read as "still clean", while a
    # heading whose one body copy was gone looked safe because three invisible copies were left. The
    # contract has three sides and all three are planted here, because on the three pages measured
    # live this round every probe had exactly one reader copy — the multi-copy branch no real page
    # exercises has to be exercised somewhere.
    multi = ("<nav><a href=\"#x\">二到六级标题必须作为独立单位到达读者的眼睛</a></nav>"
             "<article><h2>二到六级标题必须作为独立单位到达读者的眼睛</h2>"
             "<h2>二到六级标题必须作为独立单位到达读者的眼睛</h2>"
             "<p>正文这一句足够长，它必须仍然按散文单独判一次。</p>"
             "<pre>二到六级标题必须作为独立单位到达读者的眼睛</pre></article>")
    invisible = ('<a href="#x">二到六级标题必须作为独立单位到达读者的眼睛</a>',
                 '<pre>二到六级标题必须作为独立单位到达读者的眼睛</pre>')
    only_nav = multi
    for frag in invisible:
        only_nav = only_nav.replace(frag, " ")
    if grade(hu, re.sub(r"\s+", " ", served_chunks(only_nav))):
        errs.append("control V: a page whose sidebar and code copies were emptied but whose two body "
                    "copies stand must read clean, got %r"
                    % (grade(hu, re.sub(r"\s+", " ", served_chunks(only_nav))),))
    no_body = multi.replace("<h2>二到六级标题必须作为独立单位到达读者的眼睛</h2>", "")
    both_out = grade(hu, re.sub(r"\s+", " ", served_chunks(no_body)))
    if len(both_out) != 1 or both_out[0][0] != "heading":
        errs.append("control V: the reader's two body copies gone must name the heading even with the "
                    "sidebar and code copies standing, got %r" % (both_out,))
    one_out = grade(hu, re.sub(r"\s+", " ", served_chunks(
        multi.replace("<h2>二到六级标题必须作为独立单位到达读者的眼睛</h2>", "", 1))))
    if one_out:
        errs.append("control V: one of two reader copies left standing must read clean, got %r"
                    % (one_out,))
    return errs


def mutation_control(page):
    """Take a real served page, hide one real sentence of each unit kind, require the judge to name it.

    Without this, "MISS: {}" on the whole site is only worth as much as the substring test that
    produced it. The deletion happens on the downloaded HTML, never in a repo file.

    Round 88's §八 ① recorded the hole in this very control: it only ever hid a `plain` unit, so the
    two buckets the judge gained that round (`heading`, `quote`) had never been proven to fire on a
    published page. A heading is the harder case because the page prints its own table of contents,
    so the same words exist in more than one place and hiding one copy is not hiding the sentence.
    """
    index = LA.url_index()
    # Match the way `--page` matches: against the same relative, forward-slashed path run() prints.
    # Comparing the argument to raw absolute Windows paths made `--mutate 00-index/changelog` report
    # "no page matches" while the very same string selects that page in a full run.
    hit = next(((os.path.relpath(p, DOCS).replace("\\", "/"), io.open(p, encoding="utf-8").read())
                for p in walk() if page in p.replace("\\", "/")), None)
    if not hit:
        return ["mutation control: no page matches %r" % page]
    rel, text = hit
    url = index.get(LA.norm(LA.h1_of(text)))
    if not url:
        return ["mutation control: %s has no published address" % rel]
    _u, served, err = fetch_page(url)
    if err or not served:
        return ["mutation control could not fetch %s (%s)" % (url, err)]
    units = chunks(text)
    all_units = [(k, u, 1) for k, u, _l in units]
    tree_norm = re.sub(r"\s+", " ", LA.norm(text))
    flat = re.sub(r"\s+", " ", served_chunks(served))
    # "Outside a tag" is not "on the reader's screen". The judge reads `LA.body_visible()`, which also
    # drops `<script>` data blobs, `<pre>/<code>` runs, KaTeX `<annotation>` sources and GitBook's own
    # table-of-contents reprint of every heading. Counting raw occurrences instead picked a plain
    # sentence whose only raw-contiguous copy sits inside a script blob: hiding every copy of it left
    # the reader's page byte-identical where the judge looks, and the control reported that a
    # swallowed sentence "read as clean". These ranges mirror `LA.visible()` so the two judges cannot
    # disagree about what a reader got.
    holes = sorted([m.span() for rx in (OFFPAGE_BLOCK, OFFPAGE_NAV) for m in rx.finditer(served)])
    merged = []
    for a, b in holes:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    hole_start = [a for a, _b in merged]

    def readable(spot):
        j = bisect.bisect_right(hole_start, spot[0]) - 1
        return not (j >= 0 and merged[j][1] >= spot[1])

    def spots_of(probe):
        pat = re.compile("|".join(re.escape(f) for f in sorted({probe, html.escape(probe)},
                                                               key=len, reverse=True)))
        every = [(m.start(), m.end()) for m in pat.finditer(served)]
        return every, [s for s in every if readable(s)]

    def wipe(html_text, drop):
        """Blank out the given raw-HTML spans, leaving the rest of the page untouched."""
        out, shift = html_text, 0
        for start, end in drop:
            out = out[:start - shift] + " " + out[end - shift:]
            shift += end - start - 1
        return out

    errs = []
    for kind in ("plain", "heading", "quote"):
        of_kind = [u for k, u, _l in units if k == kind]
        if not of_kind:
            # Not every page has every kind (a chapter page can ship zero blockquotes). Requiring a
            # quote to hide on such a page would be a defect of this control, not of the site.
            print("mutation control: %s ships no %s unit to hide" % (rel, kind))
            continue
        # Fewest copies first, then longest. The first pass of this control took the *first* token of
        # the longest heading, which on the changelog is `2026` — 1200 copies, i.e. it proved the
        # judge notices when every date on the page vanishes, not when one heading is swallowed.
        # Raw `str.count` ranks (scanning every candidate with a regex turned a 3-minute control into
        # a 10-minute one); only the shortlist is then probed for reader-side copies, because a probe
        # the reader sees as one word but the HTML splits across tags has no copy a text edit hides.
        cands = [(u, p)
                 for u in of_kind if re.sub(r"\s+", " ", u) in flat
                 for p in [max((t for t in u.split(" ") if len(t) >= 3), key=len, default=None) or None]
                 if p and served.count(p)]
        victim = probe = None
        spots = every = []
        for _raw, _n, u, p in sorted((served.count(p), -len(u), u, p) for u, p in cands)[:40]:
            ev, vis = spots_of(p)
            if vis:
                victim, probe, every, spots = u, p, ev, vis
                break
        if probe is None:
            errs.append("mutation control: %s has no %s unit with a probe that reaches the reader as "
                        "one hideable run of characters" % (rel, kind))
            continue
        copies = len(spots)
        off = len(every) - copies
        cut = wipe(served, spots)
        if cut == served:
            errs.append("mutation control could not hide %r inside %s" % (probe[:24], rel))
            continue
        out = grade([(kind, victim, 1)], served_chunks(cut))
        if not out:
            errs.append("mutation control did NOT fire: hiding a real %s on %s read as clean"
                        % (kind, rel))
            continue
        # `grade()` only sees that a sentence went missing; `classify()` decides whether anything is
        # allowed to excuse it. Round 87's lesson is that the excuse is the blind side of a
        # completeness judge, so the real-page control must be graded by the bucketed judge.
        rows, _ev = classify(all_units, re.sub(r"\s+", " ", served_chunks(cut)), cut, tree_norm)
        verdicts = {u: (v, exc) for _k, _l, u, v, exc in rows}
        if verdicts.get(victim, ("clean", None))[0] != "MISS":
            errs.append("mutation control: hiding a real %s on %s was excused as %r"
                        % (kind, rel, verdicts.get(victim)))
            continue
        # The other side of the same contract, and the one a heading needs: the page prints its own
        # table of contents, so the words of a swallowed heading are still on the screen in the
        # sidebar. Deleting ONLY those off-reader copies must change nothing — otherwise this control
        # would be proving that the judge notices the page got shorter, not that a sentence the reader
        # was supposed to get never arrived.
        if off:
            nav_cut = wipe(served, [s for s in every if s not in spots])
            kept = grade([(kind, victim, 1)], served_chunks(nav_cut))
            if kept:
                errs.append("mutation control: %s on %s read as lost after only its %d off-reader "
                            "copies (sidebar/script/code) were hidden, its %d reader copies intact"
                            % (kind, rel, off, copies))
                continue
        # And the direction that keeps the axis honest about position: with several reader copies,
        # leaving one of them standing must read clean. Which one survives matters (a table-of-contents
        # entry can carry the probe without carrying the whole sentence), so each is tried.
        half = ""
        if copies > 1:
            survivors = [i + 1 for i in range(copies)
                         if not grade([(kind, victim, 1)],
                                      served_chunks(wipe(served, spots[:i] + spots[i + 1:])))]
            if not survivors:
                errs.append("mutation control: %s on %s still read as lost with 1 of %d reader copies "
                            "of the probe left on the page (%r)"
                            % (kind, rel, copies, probe[:24]))
                continue
            half = ("; with only reader copy %s of %d left it stays clean"
                    % (",".join(map(str, survivors)), copies))
        print("mutation control: hid a %s (probe %r, %d chars, %d reader copies, %d off-reader copies) "
              "and the judge named it a MISS, not a lag%s"
              % (kind, probe[:24], len(victim), copies, off, half))
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", type=int, default=None, help="grade the N unit-heaviest pages")
    ap.add_argument("--page", help="only pages whose path contains this substring")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mutate", metavar="PAGE", help="hide a real sentence on one published page and require a finding")
    args = ap.parse_args()
    if args.selftest:
        errs = controls() + homepage_parity()
        print("controls: %s" % ("OK, every bucket able to fire" if not errs else "BROKEN"))
        for e in errs:
            print("   ", e)
        return 1 if errs else 0
    if args.mutate:
        errs = mutation_control(args.mutate)
        for e in errs:
            print("   ", e)
        return 1 if errs else 0
    miss, stale, other, behind = run(args.sample, args.workers, args.page)
    if stale or behind:
        # Loud but not this axis's verdict: both mean the published copy is a *different revision*
        # of the text, proven against the page itself rather than guessed from a round number.
        # check_live_sync.py owns the reader-facing lag; red here would be red twice.
        if stale:
            print("NOTE %d lost sentences sit above the round the published page itself reached "
                  "(unpublished revision, see check_live_sync)" % stale)
        if behind:
            print("NOTE %d lost sentences are excused by local evidence: in the same gap the reader "
                  "agrees on, the published copy prints a sentence the tree has nowhere "
                  "(another revision of this region; see check_live_sync)" % behind)
    if miss or other:
        print("FAILED: %d sentences did not reach the reader (plus %d unfetched/unlisted pages)"
              % (miss, other))
        return 1
    print("OK: every graded sentence reaches the reader")
    return 0


if __name__ == "__main__":
    sys.exit(main())
