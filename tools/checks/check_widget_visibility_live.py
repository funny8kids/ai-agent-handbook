"""Live check: GitBook must render {% stepper %} / {% tabs %} bodies, not leak the tags.

Local pairing (tools/checks/check_widget_pairing.py) proves the source is balanced; it cannot
prove the platform turned the bodies into widgets. This walks the published pages, pulls the
rendered HTML for each, and asserts three things per page:

  shape     the response is a real page (size floor + the page's own H1 present), so a
            GitBook fallback page can never read as "0 leaks, all markers found"
  leakage   no literal "{%" or "%}" survives into the served HTML
  presence  every step/tab title, and a body snippet from each widget, is in the served markup

URLs come from the site's own llms.txt — never constructed by hand. `--all` sweeps every
widget page; the default samples the labs plus a spread of chapter pages.

Usage:  python tools/checks/check_widget_visibility_live.py [--all] [--sample N]
"""
import html
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

SITE = "https://violetnotes.gitbook.io/violetnotes-docs"
LLMS = SITE + "/llms.txt"
DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs"))
UA = {"User-Agent": "Mozilla/5.0 (handbook self-check)"}

TOKEN = re.compile(r"\{%-?\s*(stepper|step|tabs|tab)\b((?:%(?!\})|[^%])*)%\}")
TITLE_ATTR = re.compile(r'title\s*=\s*"([^"]+)"')


def fetch(url, binary=False, tries=4):
    """GitBook's CDN closes TLS connections at will mid-sweep; retry before blaming the page."""
    last = None
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            return data if binary else data.decode("utf-8", "replace")
        except (urllib.error.URLError, OSError) as exc:
            last = exc
            if n == tries - 1:
                break
            time.sleep(2 * (n + 1))
    raise RuntimeError("fetch failed after %d tries: %s (%s)" % (tries, url, last))


def llms_urls():
    text = fetch(LLMS)
    return re.findall(r"\((https://[^)\s]+\.md)\)", text)


def tail(rel_path):
    """A page's path below its chapter directory, lowercased — the part GitBook keeps verbatim.

    Measured on llms.txt: GitBook transliterates the chapter directory to pinyin
    (`09-frameworks/langchain.md` -> `09-kuang-jia-yu-sheng-tai/langchain.md`) but publishes every
    deeper segment unchanged (`13-resources/projects/langchain.md` ->
    `13-zi-yuan-ku/projects/langchain.md`). Matching on the basename alone collided those two
    pages and silently dropped 5 of the 54 widget pages from live coverage; matching on the tail
    separates them without ever constructing a URL. The tail's length also carries the segment
    count, so `docs/README.md` (tail ()) can never match a chapter README (`00-index/README.md`,
    tail ("readme.md",)) -- that one has no published tail and stays a skip.
    """
    return tuple(s.lower() for s in rel_path.replace("\\", "/").split("/")[1:])


def page_index(urls):
    """Map a published page tail to its live URL. Ambiguous tails are dropped, never guessed."""
    by_tail = {}
    for u in urls:
        rel = u[len(SITE) + 1:] if u.startswith(SITE) else os.path.basename(u)
        by_tail.setdefault(tail(rel), []).append(u)
    return {k: v[0] for k, v in by_tail.items() if len(v) == 1}


def widget_pages():
    pages = []
    for dirpath, _, filenames in os.walk(DOCS):
        if "14-templates" in dirpath.replace("\\", "/"):
            continue
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8").read()
            widgets = extract_widgets(text)
            if widgets:
                pages.append((path, os.path.splitext(fn)[0], text, widgets))
    return pages


def outside_fences(text):
    out, open_tok = [], None
    for line in text.split("\n"):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            tok = m.group(1)[0] * 3
            open_tok = None if open_tok else tok
            out.append("")
            continue
        out.append("" if open_tok else line)
    return "\n".join(out)


CLOSE = re.compile(r"^\{%-?\s*(end[a-z-]+)")
SKIP_BODY = re.compile(r"^(\{|`|\||>|!\[|\+\+|$)")


def snippet_of(body_lines):
    """First plain-prose line of a step/tab body — the string the reader must see rendered.

    Skipped: lines with inline code (GitBook emits separate <code> nodes, so a raw substring
    compare breaks on content that renders fine), lines with `**` bold, and lines carrying a
    displayed formula (dollar-dollar or backslash-paren delimiters) — KaTeX rewrites those, so
    the source text is not what the page shows.
    """
    for line in body_lines:
        if SKIP_BODY.match(line) or any(t in line for t in ("`", "**", "$$", r"\(")):
            continue
        clean = re.sub(r"^#{1,6}\s*", "", line).strip()
        if len(clean) >= 8:
            return clean[:28]
    return ""


def extract_widgets(text):
    """Return [(kind, title, snippet)] for every step/tab: steppers are untitled in house style.

    A widget is recorded even when no clean snippet can be taken from its body (that body may be
    all inline code); the live check just skips the body assertion for those instead of quietly
    shrinking the widget count.
    """
    items, group = [], None
    current = None

    def commit():
        nonlocal current
        if current is not None:
            items.append((current[0], current[1], snippet_of(current[2])))
            current = None

    for line in outside_fences(text).split("\n"):
        stripped = line.strip()
        if stripped.startswith("{%"):
            close = CLOSE.match(stripped)
            if close:
                commit()
                if close.group(1) in ("endstepper", "endtabs"):
                    group = None
                continue
            m = TOKEN.match(stripped)
            if m:
                commit()
                kind = m.group(1)
                if kind in ("stepper", "tabs"):
                    group = kind
                elif kind in ("step", "tab"):
                    attr = TITLE_ATTR.search(m.group(2))
                    current = [group, attr.group(1) if attr else "", []]
                continue
        if group and current is not None and stripped:
            current[2].append(stripped)
    commit()
    return items


def norm(s):
    return re.sub(r"[^0-9A-Za-z一-鿿]+", " ", s or "").strip().lower()


def visible_controls():
    served = ('<h1>Lab 1：最小 ReAct 闭环</h1><div class="x"><script>var a="起点：模型的上下文里只有问题";</script>'
              '<p>起点：模型的上下文里只有问题，往后是正文。</p></div>')
    body = visible(served)
    assert norm("Lab 1：最小 ReAct 闭环") in body, "control: punctuation-insensitive compare broken"
    assert norm("起点：模型的上下文里只有问题") in body, "control: body probe lost a present string"
    assert norm("这段文字在页面上根本不存在啊啊啊啊") not in body, "control: phantom string matched"
    assert "var a=" not in body, "control: <script> content leaked into visible text"
    print("visibility controls: markup/entities stripped, script rejected, phantom rejected")


def h1_of(text):
    m = re.search(r"^#\s+(.+)$", text, flags=re.M)
    return m.group(1).strip() if m else ""


def visible(served):
    """Reader-visible text: markup stripped and entities decoded.

    norm() also collapses punctuation. Measured on this deployment the platform publishes the
    SUMMARY label verbatim (colons and brackets survive), so that collapsing is a defensive
    allowance, not a workaround for a rewrite — and tools/checks/check_nav_h1_sync.py is what
    guarantees label == page H1 in the first place.
    """
    txt = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", served, flags=re.S | re.I)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", txt))
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", txt).strip().lower()


def check_page(url, text, widgets):
    served = fetch(url[:-3] if url.endswith(".md") else url)
    problems = []
    body = visible(served)
    title = norm(h1_of(text))
    if len(served) < 200000 or not title or title not in body:
        return ["SHAPE %s bytes=%d h1=%r found=%s"
                % (url, len(served), h1_of(text), bool(title and title in body))]
    for token in ("{%", "%}"):
        n = served.count(token)
        if n:
            problems.append("LEAK %r x%d in %s" % (token, n, url))
    for kind, t, snippet in widgets:
        if t and norm(t) not in body:
            problems.append("MISSING %s title %r in %s" % (kind, t[:40], url))
        s = norm(snippet)
        if len(s) >= 10 and s[:24] not in body:
            problems.append("MISSING %s body %r in %s" % (kind, snippet[:20], url))
    return problems


def pick(pages, want_all, sample):
    labs = [p for p in pages if "/19-labs/" in p[0].replace("\\", "/")]
    rest = [p for p in pages if p not in labs]
    random.Random(20260923).shuffle(rest)
    return pages if want_all else (labs + rest)[:max(sample, len(labs))]


EXTRACT_SAMPLE = r"""{% stepper %}
{% step %}

#### 第一步：真实标题文字长度足够

正文说明。
{% endstep %}
{% endstepper %}

{% tabs %}
{% tab title="分支 A" %}

四项延迟全付：$$L_{\text{e2e}} = \sum_i L_i$$

这里是标签页里的正文内容。
{% endtab %}
{% endtabs %}

{% stepper %}
{% step %}

`这一步的正文只有一行行内代码`
{% endstep %}
{% endstepper %}
"""

EXTRACT_PHANTOM = """```markdown
{% stepper %}
{% step %}

#### 围栏里的示例不该被当成真组件

{% endstep %}
{% endstepper %}
```
"""


def page_index_controls():
    """The tail matcher must separate same-named pages and never invent a URL."""
    urls = [SITE + "/readme.md",
            SITE + "/09-kuang-jia-yu-sheng-tai/langchain.md",
            SITE + "/13-zi-yuan-ku/projects/langchain.md"]
    idx = page_index(urls)
    assert idx.get(tail("README.md")) == urls[0], "control: homepage tail did not resolve"
    assert idx.get(tail("09-frameworks/langchain.md")) == urls[1], \
        "control: chapter page did not resolve through its pinyin directory"
    assert idx.get(tail("13-resources/projects/langchain.md")) == urls[2], \
        "control: same-named pages were not told apart"
    assert idx.get(tail("00-index/README.md")) is None, \
        "control: a chapter README resolved to the homepage"
    collide = page_index(urls + [SITE + "/16-yy/langchain.md"])
    assert all(tail(r) not in collide for r in ("09-frameworks/langchain.md",
                                                "16-ai-infrastructure/langchain.md")), \
        "control: an ambiguous tail resolved anyway"
    print("url-index controls: same-named pages separated, chapter README and ambiguous tails refused")


def run_extractor_controls():
    got = extract_widgets(EXTRACT_SAMPLE)
    assert [k for k, _, _ in got] == ["stepper", "tabs", "stepper"], \
        "control: sample widgets mis-parsed %s" % (got,)
    assert got[0][1] == "" and got[0][2].startswith("第一步"), got
    assert got[1][1] == "分支 A" and got[1][2].startswith("这里是标签页"), got
    assert got[2] == ("stepper", "", ""), \
        "control: an inline-code-only step must still count, with no body assertion: %r" % (got[2],)
    assert extract_widgets(EXTRACT_PHANTOM) == [], "phantom: a fenced example counted as a widget"
    print("extractor controls: 3 widgets parsed (incl. the snippet-less one), fenced phantom ignored")


def main():
    args = sys.argv[1:]
    run_extractor_controls()
    page_index_controls()
    visible_controls()
    want_all = "--all" in args
    sample = int(args[args.index("--sample") + 1]) if "--sample" in args else 10

    pages = widget_pages()
    total_widgets = sum(len(w) for _, _, _, w in pages)
    steps = sum(1 for _, _, _, w in pages for k, _, _ in w if k == "stepper")
    tabs = total_widgets - steps
    print("widget pages locally=%d titled widgets=%d (steps=%d tabs=%d)"
          % (len(pages), total_widgets, steps, tabs))
    # Floors against the house counts (54 groups / 279 steps, 52 groups / 195 tabs); only
    # titled widgets with body text are collected here, so these sit a little below those.
    assert steps >= 270 and tabs >= 190, \
        "vacuity: extractor found steps=%d tabs=%d" % (steps, tabs)
    if "--dry" in args:
        for path, stem, _, w in pages[:6]:
            print("  dry %-24s %s" % (stem, [k + ":" + t[:18] for k, t, _ in w][:4]))
        print("dry run: extractor sane, no network touched")
        return 0

    index = page_index(llms_urls())
    assert len(index) >= 180, "vacuity: live url index only resolved %d pages" % len(index)
    checked = missing_url = checked_props = 0
    problems = []
    for path, stem, text, widgets in pick(pages, want_all, sample):
        rel = os.path.relpath(path, DOCS)
        url = index.get(tail(rel))
        if not url:
            missing_url += 1
            print("  skip (no unambiguous live url): %s" % rel.replace("\\", "/"))
            continue
        errs = check_page(url, text, widgets)
        checked += 1
        checked_props += len(widgets)
        print("  %-40s widgets=%d %s" % (stem, len(widgets), "ok" if not errs else "PROBLEMS"))
        problems += errs
    assert checked >= 5, "vacuity: only %d pages were actually checked" % checked
    print("\nchecked=%d skipped(no url)=%d widget-props(checked pages only)=%d problems=%d"
          % (checked, missing_url, checked_props, len(problems)))
    for p in problems[:40]:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
