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
  - heading lines (`#`, `##`, ...) are not units: `check_nav_h1_sync.py` already judges those,
    and GitBook reprints heading text in its own TOC, which would let the body hide a gap.
  - a bare `<https://…>` autolink ends a unit exactly like a link does: the published page prints
    the address itself between the two halves of the sentence, so a joined unit could never match.
  - a page that prints its own round history is graded only from the first round its published copy
    provably finished. Round 83 measured the live changelog holding round 79's heading but not the
    close-out prose added to that section after the push — a revision gap no fetch can distinguish,
    so that one section is graded a round late rather than forgiven.
  - `body_visible()` (nav-stripped served text) is the target, so a chunk cannot pass by
    matching the sidebar.
  - chunks inside a GitBook widget body (`{% tabs %}`, `{% stepper %}`, ...) are graded, but in a
    separate bucket: those bodies can be appended by hydration rather than shipped in SSR HTML,
    and "the SSR markup has no room for it" is not yet a reader defect. The bucket must stay
    empty to claim the SSR leg covers them; when it is not, name the pages and check them in a
    browser.

A green here is only as good as the fetch: a page that could not be downloaded proves nothing, so
fetch failures go to their own bucket and exit non-zero, never to "0 problems" (round 59's split).
"""
import argparse
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
# A markup name never starts with a digit: round 83 measured the changelog's own prose `（W<420 且 H>380，
# 宽高比 <0.55）`, and a permissive `<...>` pattern deleted `420 且 H` from the authored side, turning a
# perfectly published sentence into a MISS. Entities arrive from the platform already escaped (`&lt;`),
# so the served side loses nothing by the same, stricter rule.
HTML_TAG = re.compile(r"<(?!br\s*/?>)[a-zA-Z/!][^>]*>")
BR = re.compile(r"<br\s*/?>", re.I)
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
    """[(kind, chunk, line)] for every authored prose sentence-run; kind is 'plain' or 'widget'.

    A chunk never straddles a code span, a formula, a link, a `<br>` or a widget tag, because the
    published page does not print those as plain text either: KaTeX ships its own characters
    between two halves of a sentence, so a joined unit could never match and the MISS would be
    the ruler's, not the reader's. Round 83's first pass on one page read 19 MISS, and every
    single one was a straddle, a fence/formula body or a tag attribute.
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
        if display or not s or s.startswith(("#", ">")) or s.startswith("!["):
            continue
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
        kind = "widget" if (depth or on_tag_line) else "plain"
        for pi, part in enumerate(body.split(HOLE)):
            for i, piece in enumerate(SENT_END.split(html.unescape(part))):
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

    `14-templates/` is excluded for the same reason `live_aria_manifest.build` excludes it: those
    files are authoring scaffolding and are not in the published site, so "the page has no
    published address" is their correct shape, not a finding.
    """
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "14-templates" in dirpath.replace("\\", "/"):
            continue
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
            stale = [x for x in lost if cut and x[1] < cut]
            miss = [x for x in lost if not (cut and x[1] < cut)]
            pages_lost.append((r["page"], len(miss), len(stale), len(r["units"]), cut, miss[:3]))
            for tag, items in (("MISS", miss), ("STALE-COPY", stale)):
                for kind, ln, u in items:
                    problems.append("%s %s %s:%d %s" % (tag, kind.upper(), r["page"], ln, u))
    n_miss = sum(p[1] for p in pages_lost)
    n_stale = sum(p[2] for p in pages_lost)
    print("prose survival: pages=%d units=%d plain=%d widget=%d | %s" %
          (len(picked), total, plain, total - plain, _label))
    print("lost sentences: MISS=%d STALE-COPY=%d | pages-with-MISS=%d fetch-failures=%d not-listed=%d"
          % (n_miss, n_stale, sum(1 for p in pages_lost if p[1]), len(fetch_fail), _unl))
    for pg, nm, ns, nu, cut, sample in sorted(pages_lost, key=lambda p: (-p[1], -p[2]))[:12]:
        print("   %-44s MISS=%-4d unpublished=%-4d of %d units%s"
              % (pg, nm, ns, nu, "" if not cut else "  (published copy proves nothing below line %d)" % cut))
        for kind, ln, u in sample:
            print("       %s:%d %s" % (kind.upper(), ln, u[:70]))
    for f in fetch_fail[:10]:
        print("   FETCH", f)
    return n_miss, n_stale, len(fetch_fail) + len(unlabeled if _label == "all" else [])


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
    return errs


def mutation_control(page):
    """Take a real served page, hide one real sentence in the served HTML, require the judge to name it.

    Without this, "MISS: {}" on the whole site is only worth as much as the substring test that
    produced it. The deletion happens on the downloaded HTML, never in a repo file.
    """
    index = LA.url_index()
    hit = next(((os.path.relpath(p, DOCS).replace("\\", "/"), io.open(p, encoding="utf-8").read())
                for p in walk() if page in p), None)
    if not hit:
        return ["mutation control: no page matches %r" % page]
    rel, text = hit
    url = index.get(LA.norm(LA.h1_of(text)))
    if not url:
        return ["mutation control: %s has no published address" % rel]
    _u, served, err = fetch_page(url)
    if err or not served:
        return ["mutation control could not fetch %s (%s)" % (url, err)]
    units = [u for k, u, _ in chunks(text) if k == "plain"]
    flat = re.sub(r"\s+", " ", served_chunks(served))
    victim = next((u for u in sorted(units, key=len, reverse=True)
                   if re.sub(r"\s+", " ", u) in flat), None)
    if not victim:
        return ["mutation control: no authored sentence of %s is on its own page" % rel]
    probe = victim.split(" ")[0]
    cut = served.replace(probe, " ", 1) if probe in served else served.replace(html.escape(probe), " ", 1)
    if cut == served:
        return ["mutation control could not hide %r inside %s" % (probe[:24], rel)]
    out = grade([("plain", victim, 1)], served_chunks(cut))
    if not out:
        return ["mutation control did NOT fire: hiding real text on %s read as clean" % rel]
    print("mutation control: hid %r on %s and the judge named it (%d chars)" % (probe[:24], rel, len(victim)))
    return []


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", type=int, default=None, help="grade the N unit-heaviest pages")
    ap.add_argument("--page", help="only pages whose path contains this substring")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mutate", metavar="PAGE", help="hide a real sentence on one published page and require a finding")
    args = ap.parse_args()
    if args.selftest:
        errs = controls()
        print("controls: %s" % ("OK, every bucket able to fire" if not errs else "BROKEN"))
        for e in errs:
            print("   ", e)
        return 1 if errs else 0
    if args.mutate:
        errs = mutation_control(args.mutate)
        for e in errs:
            print("   ", e)
        return 1 if errs else 0
    miss, stale, other = run(args.sample, args.workers, args.page)
    if stale:
        # Loud but not this axis's verdict: the platform has not published that revision, which
        # check_live_sync.py reports as the reader-facing lag it is. Red here would be red twice.
        print("NOTE %d lost sentences sit above the round the published page itself reached "
              "(unpublished revision, see check_live_sync)" % stale)
    if miss or other:
        print("FAILED: %d sentences did not reach the reader (plus %d unfetched/unlisted pages)"
              % (miss, other))
        return 1
    print("OK: every graded sentence reaches the reader")
    return 0


if __name__ == "__main__":
    sys.exit(main())
