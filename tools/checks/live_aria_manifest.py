"""Live structural-parity manifest: what the browser DOM must contain for each page.

Round 56 found that this deployment renders the interactive widgets into real ARIA
controls, and that two of the counts line up EXACTLY with what the markdown author
wrote:
    authored $$-pairs  ==  document.querySelectorAll('.katex').length
    authored {% tabs %} blocks  ==  [role=tab] count
That makes an equality check (not a fuzzy text search) possible on the live site —
worth having, because round 55 proved this platform can silently drop authored
content (it drops the markdown H1) and a dropped formula block would look like
"nothing is wrong" to a text-presence probe.

Why the browser path still exists: the third equality (mermaid) is only answerable there.
Round 57 measured that the server-rendered HTML already carries the tab and KaTeX structures in
exactly the authored quantities — so --headless audits every published page with urllib and no
operator-supplied viewport — but mermaid containers appear only after hydration. --calibrate
re-fetches the URLs a browser actually measured and asserts SSR == DOM, so the shortcut cannot
drift away from what the reader sees without this file failing first.

Measured limitation, recorded so a future round does not report it as a defect: with the in-app
browser closed the page has a 0x0 viewport (visibilityState=hidden), so lazily-rendered pieces
never finish — 6 consecutive pages kept every mermaid container at aria-busy=true with 0 <text>
nodes after scrollIntoView + 4s wait. This judge therefore compares mermaid CONTAINER counts
(hydration created a slot for each authored block) and never claims the diagram painted; that
needs a screenshot, which needs the operator to open the Browser panel once.

Usage:
    python tools/checks/live_aria_manifest.py [--sample N | --all]   # print expectations
    python tools/checks/live_aria_manifest.py --diff live.json       # compare probe output
    python tools/checks/live_aria_manifest.py --headless --all       # tab/katex parity over every
                                                                     # published page, urllib only
    python tools/checks/live_aria_manifest.py --calibrate [live.json]  # SSR vs measured DOM
"""
import io, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(HERE, "..", "..", "docs"))
SITE = "https://violetnotes.gitbook.io/violetnotes-docs"
LLMS = SITE + "/llms.txt"
PROBE = os.path.join(HERE, "live_aria_probe.js")


def norm(s):
    return re.sub(r"[^0-9A-Za-z一-鿿]+", " ", s or "").strip().lower()


def h1_of(text):
    m = re.search(r"^#\s+(.+)$", text, flags=re.M)
    return m.group(1).strip() if m else ""


def outside_fences(text):
    keep, open_ = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            open_ = not open_
            continue
        if not open_:
            keep.append(line)
    return "\n".join(keep)


def strip_code_spans(line):
    """Drop CommonMark inline code spans: a backtick run opens, an equal-length run closes.

    A lazy regex can't express this. The changelog writes fence examples as inline ```text …,
    a run that never closes on its line, and `[^`]*` then swallows up to the NEXT backtick —
    eating a real delimiter on the far side so a whole paragraph read as unpaired.
    """
    out, i, n = [], 0, len(line)
    while i < n:
        if line[i] != "`":
            out.append(line[i])
            i += 1
            continue
        j = i
        while j < n and line[j] == "`":
            j += 1
        run = line[i:j]
        k = line.find(run, j)
        while k != -1 and (line[k - 1] == "`" or line[k + len(run):k + len(run) + 1] == "`"):
            k = line.find(run, k + 1)      # that candidate sits inside a longer run
        if k == -1:
            out.append(run)                # unclosed on this line: literal, not a code span
            i = j
        else:
            out.append(" ")
            i = k + len(run)
    return "".join(out)


def prose(text):
    """What the reader can actually be shown: no fenced blocks, no inline code spans.

    Round 57 proved this matters for an EQUALITY check. docs/README.md documents the formula
    syntax inside backticks, so a raw $$-count claimed it authored a formula the site correctly
    served zero of; the changelog raw-counted 23 against 10 rendered. Counting on prose is the
    same 口径 the repo's formula judge uses, so the two rulers can no longer disagree.
    """
    return "\n".join(strip_code_spans(ln) for ln in outside_fences(text).split("\n"))


def formula_sources(text):
    """[(kind, source)] for every formula the page asks for, plus the defects found.

    One tokenizer, so the live parity axis, the offline sweep and the KaTeX judge can never
    disagree about what the author wrote — the repo has been burned by three rulers reading
    three formula counts (811 / 821 / 834) off the same tree.
    """
    body = prose(text)
    lines = body.split("\n")
    lone = [i for i, ln in enumerate(lines) if ln.strip() == "$$"]
    defects = []
    if len(lone) % 2:
        defects.append("asymmetric display delimiters: %d lone-line $$" % len(lone))
    in_block, out = set(), []
    for a, b in zip(lone[0::2], lone[1::2]):
        src = "\n".join(lines[a + 1:b])
        out.append(("display", src))
        in_block.update(range(a, b + 1))
        nested = [ln for ln in src.split("\n") if "$$" in ln]
        if nested:
            defects.append("NESTED $$ inside a display block (KaTeX eats the pair, the symbol "
                           "loses math-italic): %r" % nested[0].strip()[:70])
    for para in re.split(r"\n\s*\n", "\n".join(ln for i, ln in enumerate(lines)
                                               if i not in in_block)):
        parts = para.split("$$")
        pairs = (len(parts) - 1) // 2          # N delimiters make floor(N/2) formulas, at most
        out += [("inline", src) for src in parts[1::2][:pairs]]
        if (len(parts) - 1) % 2:
            defects.append("unpaired $$ inside one paragraph: %r"
                           % re.sub(r"\s+", " ", para).strip()[:70])
    return out, defects


def formula_counts(text):
    """(formulas the reader should see, defect list) under GitBook's own tokenizer.

    Two rules, both learned by comparing against this site's served HTML:
      * a $$ alone on a line opens/closes a display block, and everything between two such
        delimiters is ONE formula — so a $$ nested inside it never starts a new formula. What it
        does instead was measured with the site's own KaTeX (0.18.7): the pair is swallowed and
        the symbol inside it loses math-italic, i.e. the author's `n` renders in the CJK text
        font. Round 57 first wrote this up as "prints literal $$", which was an inference from
        the pairing rule and is contradicted by the render — see the 第 57 次 entry;
      * the remaining $$ tokens pair up *within one paragraph*. Pairing them across the whole
        page is what made the changelog read 11 against 10 served: it quotes `$$` inside code
        spans, and every such quote flips the global parity while leaving its own paragraph fine.
    A paragraph holding an unpaired delimiter is reported, not silently rounded down — that is
    the same class of authoring bug as the round-53 block whose closing $$ never stood alone.
    """
    sources, defects = formula_sources(text)
    return len(sources), defects


def expect_of(text):
    """Authored counts a correctly rendered page must reproduce in the DOM.

    tabs counts {% tab title="..." %} *items*, not {% tabs %} wrappers: measured live, one page
    with 1 wrapper and 4 items rendered exactly 4 [role=tab] buttons and 4 [role=tabpanel] panels.
    """
    return {
        "tabs": len(re.findall(r"^\s*\{%\s*tab\s+title=", prose(text), flags=re.M)),
        "katex": formula_counts(text)[0],
        "mermaid": len(re.findall(r"^```mermaid", text, flags=re.M)),
    }


def url_index():
    req = urllib.request.Request(LLMS, headers={"User-Agent": "python-urllib"})
    text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    by_title = {}
    for title, url in re.findall(r"\[([^\]]+)\]\((https://[^)\s]+\.md)\)", text):
        by_title.setdefault(norm(title.strip()), []).append(url.strip())
    return {k: v[0][:-3] for k, v in by_title.items() if len(v) == 1}


def build(sample, want_all):
    index = url_index()
    rows = []
    for dirpath, _, filenames in os.walk(DOCS):
        if "14-templates" in dirpath.replace("\\", "/"):
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            exp = expect_of(text)
            if not any(exp.values()):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            url = index.get(norm(h1_of(text)))
            rows.append({"page": rel, "url": url, **exp})
    rows.sort(key=lambda r: (-r["tabs"], -r["katex"], r["page"]))
    # a negative control belongs in every sample: a page that must show 0 tabs
    neg = [r for r in rows if not r["tabs"]]
    head = [r for r in rows if r["tabs"]]
    picked = rows if want_all else (head[:max(sample - 1, 1)] + neg[:1])
    return [r for r in picked if r["url"]], len(rows), index


def parity(entry, exp):
    """Per-page equality verdict. Empty list means the page reproduces what was authored."""
    out = []
    for key in ("tabs", "katex", "mermaid"):
        if entry.get(key) != exp[key]:
            out.append("PARITY %s:%s authored=%s live=%s" % (exp["page"], key, exp[key], entry.get(key)))
    if entry.get("mermaid_unrendered", 0) > exp["mermaid"]:
        out.append("BUSY %s more pending diagrams than authored" % exp["page"])
    if entry.get("leak"):
        out.append("LEAK %s shows literal {%% or %%} to the reader" % exp["page"])
    return out


def classify(entry, exp):
    """Gate a reading on page readiness BEFORE trusting its counts.

    Measured false negative: probing a page in the same call batch as its navigation returned
    tabs/katex correctly but mermaid=0 against 2 authored blocks — the containers are appended
    by hydration, later than the text. Without this gate that artifact reads as "the platform
    dropped two diagrams", which is precisely the class of defect this axis exists to find, so
    a void reading is reported loudly rather than quietly skipped.
    """
    if entry.get("ready") is None:
        return ["UNSTAMPED %s: reading carries no readyState, so hydration is unknown" % exp["page"]]
    if entry.get("ready") != "complete":
        return ["REPROBE %s readyState=%s: DOM not hydrated, every count is void"
                % (exp["page"], entry.get("ready"))]
    return parity(entry, exp)


def ssr_counts(served):
    """Counts the server-rendered HTML exposes, defined to mirror the browser probe.

    Round 56 measured this on 7 published pages: role="tab" and the katex class token
    already appear in the pre-hydration HTML in EXACTLY the authored quantities, so two of
    the three equalities need no browser at all. mermaid does (its container is appended by
    hydration), which is why it is deliberately absent here.

    Token-exact matching, not a substring count: `role="tabpanel"` must not be read as a tab
    and `class="katex-display"` must not be read as a rendered formula.
    """
    tabs = sum(1 for m in re.finditer(r'role="([^"]*)"', served) if "tab" in m.group(1).split())
    katex = sum(1 for m in re.finditer(r'class="([^"]*)"', served) if "katex" in m.group(1).split())
    return {"tabs": tabs, "katex": katex}


def visible(served, drop_nav=False):
    """Reader-visible text of the served HTML, with intentional markup removed.

    Round 57 found three LEAK false positives here: the changelog and a resources page
    *document* {% %} syntax inside code spans, and every KaTeX element ships its own TeX source
    in an <annotation> node — so a page whose formula writes 95\\% leaks "%}" into the raw
    markup while the reader sees "95%". A literal tag outside those nodes is still a leak.

    drop_nav also removes GitBook's own reprint of heading text: every in-page anchor link
    (<a href="#...">, which is what the sidebar and the on-this-page list wrap a heading in).
    The obvious rule was measured and rejected: cutting nav <li> chunks by class left 1 of the
    live changelog's 2 TOC copies standing, because a top-level entry's <li> carries no sidebar
    class — only its child <a> does. Cutting before the code strip is likewise rejected here, and
    the straddle case below is the guard against reintroducing it.
    """
    s = re.sub(r"<(script|style|pre|code|annotation)\b.*?</\1>", " ", served, flags=re.S)
    if drop_nav:
        s = re.sub(r'<a\b[^>]*href="#[^"]*"[^>]*>.*?</a>', " ", s, flags=re.S)
    return re.sub(r"<[^>]+>", " ", s)


def body_visible(served):
    """The same, minus GitBook's own sidebar/TOC copy of every heading."""
    return visible(served, drop_nav=True)


def leak_sites(served):
    """Split bare markup tokens by where a reader can actually see them.

    Round 58 measured the live changelog: 177 literal $$ sit in its HTML, 2 survive visible()'s
    code stripping, and both of those are in the sidebar — GitBook reprints heading text in the
    TOC with inline-code formatting removed, so a marker inside a *heading* is visible navigation
    even when the body copy renders it as code. Same authoring slip, different sight, and the
    message has to name the right mechanism: only a body hit is an unrendered formula.
    """
    body, shown = body_visible(served), visible(served)
    return ([t for t in ("{%", "%}", "$$") if t in body],
            [t for t in ("{%", "%}", "$$") if t not in body and t in shown])


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")


def formula_defects():
    """Every authored formula GitBook cannot render, checked without a browser."""
    out = []
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            path = os.path.join(dirpath, fn)
            text = io.open(path, encoding="utf-8").read()
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            for msg in formula_counts(text)[1]:
                out.append("FORMULA %s: %s" % (rel, msg))
    return out


def headless(rows, workers=8):
    """Full-site parity for the two structures the server already renders.

    Fetched concurrently because 175 pages x ~1.4 MB is minutes of wall-clock otherwise, and a
    run that is slow gets run less often than a defect deserves.
    """
    from concurrent.futures import ThreadPoolExecutor

    def one(r):
        for attempt in (1, 2):                       # one retry: a dropped TLS socket is a
            try:                                      # probe artifact, a pattern is a defect
                return r, fetch(r["url"]), None
            except Exception as exc:
                err = "%s (attempt %d)" % (exc, attempt)
        return r, "", err                             # a failed fetch is a finding, not a skip

    problems, checked, small = [], 0, 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for r, served, exc in pool.map(one, rows):
            if exc is not None:
                problems.append("FETCH %s: %s" % (r["page"], exc))
                continue
            if len(served) < 200000:
                small += 1
                problems.append("SHAPE %s only %d bytes (fallback page?)" % (r["page"], len(served)))
                continue
            checked += 1
            got = ssr_counts(served)
            for key in ("tabs", "katex"):
                if got[key] != r[key]:
                    problems.append("SSR-PARITY %s:%s authored=%s served=%s"
                                    % (r["page"], key, r[key], got[key]))
            shown, nav_only = leak_sites(served)
            for token in shown:
                problems.append("LEAK %s serves literal %r in the body%s"
                                % (r["page"], token,
                                   " (a formula the parser never took)" if token == "$$" else ""))
            for token in nav_only:
                problems.append("LEAK-NAV %s prints literal %r in the page TOC — that marker is "
                                "inside a heading, where GitBook drops code formatting"
                                % (r["page"], token))
    problems += formula_defects()
    print("ssr parity: authored=%d checked=%d problems=%d fallback-pages=%d"
          % (len(rows), checked, len(problems), small))
    for p in problems:
        print("  - " + p)
    return 1 if problems else 0


def calibrate(path):
    """Prove the headless shortcut measures the same thing the browser does.

    --headless is only trustworthy because, on the pages where both were measured, the
    server-rendered tab/katex counts equal the hydrated DOM counts. This re-fetches those
    archived pages and asserts it, so a future change in GitBook's rendering shows up as a
    calibration failure instead of a quietly weakened axis.
    """
    readings = json.load(io.open(path, encoding="utf-8"))
    bad, checked = [], 0
    for entry in readings:
        served = fetch(entry["url"])
        got = ssr_counts(served)
        for key in ("tabs", "katex"):
            checked += 1
            if got[key] != entry[key]:
                bad.append("CALIB %s %s: ssr=%s dom=%s" % (entry["url"], key, got[key], entry[key]))
    print("ssr-vs-dom calibration: pages=%d comparisons=%d mismatches=%d"
          % (len(readings), checked, len(bad)))
    for b in bad:
        print("  - " + b)
    return 1 if bad else 0


def controls():
    assert expect_of('{% tabs %}\n{% tab title="A" %}\nx\n{% tab title="B" %}\ny\n{% endtabs %}\n'
                     '$$a$$\n$$b$$\n```mermaid\nx\n```\n') == {
        "tabs": 2, "katex": 2, "mermaid": 1}, "control: expectation counter miscounted"
    assert expect_of("{% tabs %}\n{% endtabs %}")["tabs"] == 0, \
        "control: an empty wrapper is not a tab the reader can click"
    assert expect_of("{%% raw %%} $$x$$")["katex"] == 1, "control: stray %% must not eat the pair count"
    assert expect_of("no widgets here") == {"tabs": 0, "katex": 0, "mermaid": 0}, "control: empty page"
    # scattered single $ must not be read as formulas: parity is an equality check
    assert expect_of("cost is 5$ and 6$ and 7$")["katex"] == 0, "control: single $ must not pair up"
    exp = {"page": "x.md", "tabs": 4, "katex": 15, "mermaid": 2}
    base = {"tabs": 4, "tabpanels": 4, "katex": 15, "mermaid": 2, "mermaid_unrendered": 2}
    assert parity(dict(base, ready="complete"), exp) == [], "control: a true match must pass"
    void = classify(dict(base, mermaid=0, ready="loading"), exp)
    assert len(void) == 1 and void[0].startswith("REPROBE"), "control: pre-hydration read must be voided"
    real = classify(dict(base, mermaid=0, ready="complete"), exp)
    assert len(real) == 1 and real[0].startswith("PARITY"), "control: a genuinely dropped diagram must still be caught"
    assert parity(dict(base, ready="complete", leak=True), exp)[0].startswith("LEAK"), "control: leak unchecked"
    assert parity(dict(base, ready="complete", mermaid_unrendered=3), exp)[0].startswith("BUSY"), "control: busy floor unchecked"
    print("controls ok (counters, negatives, empty pages, hydration gate)")
    # server-rendered counting must mirror the DOM selectors, token by token
    assert ssr_counts('<div role="tablist"><button role="tab">A</button><div role="tabpanel">x'
                      '</div></div>')["tabs"] == 1, "control: tabpanel/tablist must not count as a tab"
    assert ssr_counts('<span class="katex"><span class="katex-mathml">y</span></span>'
                      '<div class="katex-display">z</div>')["katex"] == 1, \
        "control: katex-display/katex-mathml must not count as extra formulas"
    assert ssr_counts('<p>nothing here</p>') == {"tabs": 0, "katex": 0}, "control: phantom structures"
    # a heading's TOC reprint must not be reported as an unrendered body formula, and a body
    # leak must not be lost just because the same page also has sidebar copy
    nav = ('<div><li class="a sidebar-list-line:b"><a href="#h1">see $$ and {% raw %}</a></li></div>'
           '<article><p>clean body</p></article>')
    assert leak_sites(nav) == ([], ["{%", "%}", "$$"]), "control: TOC copy read as a body leak"
    body = ('<div><li class="a"><a href="#h1">see $$</a></li></div>'
            '<article><p>literal $$ outside code</p></article>')
    assert leak_sites(body) == (["$$"], []), \
        "control: a body leak must stay a body leak with a sidebar on the same page"
    assert leak_sites('<article><code>$$</code><code>{% raw %}</code></article>') == ([], []), \
        "control: markers inside code spans are documentation, not leaks"
    # a nav <a> nested inside a code span must not cut that span open and expose its $$
    straddle = '<article><code>see <a href="#h1">nav</a> $$</code></article>'
    assert leak_sites(straddle) == ([], []), "control: nav cut must not split a code pair"
    assert leak_sites(straddle.replace("<code>", "").replace("</code>", ""))[0] == ["$$"], \
        "control: the same $$ outside a code span must be a body leak"
    # the rule must key on in-page anchors only: a cross-file link is body prose, not nav copy
    assert leak_sites('<article><p>see <a href="../other#x">literal $$ here</a></p></article>')[0] == ["$$"], \
        "control: a cross-page link must not be dropped as nav copy"
    print("ssr controls ok (token-exact tab/katex counting, body/TOC leak split)")
    # the two counting rules round 57 had to learn, kept as executable memory
    assert expect_of("写法 `$$x$$` 只是文档示例\n")["katex"] == 0, \
        "control: markup shown inside a code span is not a formula the reader is served"
    assert expect_of("```json\n{\"a\": \"$$x$$\"}\n```\n")["katex"] == 0, \
        "control: $$ inside a fence must not be counted as a formula"
    assert expect_of('{% tabs %}\n{% tab title="A" %}\n`{% tab title="B" %}`\n{% endtabs %}\n')["tabs"] == 1, \
        "control: a tab example inside a code span must not inflate the tab count"
    assert formula_counts("text\n$$\n\\frac{a}{b}=0\n$$\nmore\n") == (1, []), \
        "control: a well-formed display block must read as clean"
    assert formula_counts("句内 $$x$$ 也算\n$$\na=b\n$$\n")[0] == 2, \
        "control: inline and display formulas must add up, not overwrite each other"
    # pairing is per paragraph: the changelog proved a page-wide pairing flips parity on every
    # quoted `$$`, so a stray delimiter must be caught inside its own paragraph and stop there
    para, d = formula_counts("孤立的 $$ 在这里\n\n式子 $$c=1$$ 在那里\n")
    assert para == 1 and any(x.startswith("unpaired") for x in d), \
        "control: an unpaired $$ must not steal a formula from the next paragraph"
    assert formula_counts("引用写法 `$$` 不计\n\n真正的 $$d=2$$ 计一条\n") == (1, []), \
        "control: a $$ quoted in a code span must not disturb its neighbours"
    nested, d = formula_counts("$$\n\\text{$$n$$ 一大就不可维护}\n$$\n")
    assert d and d[0].startswith("NESTED"), "control: a nested $$ must be named, not quietly counted"
    assert formula_counts("$$\n\\frac{1}{\n")[1], \
        "control: an unclosed delimiter must not read as zero formulas"
    assert "{%" not in visible('<p>write <code>{% hint %}</code> to get a card</p>'), \
        "control: an intentional code span is not a leaked tag"
    # inline-code stripping: an unclosed backtick run is literal text, the closed span is not
    quoted = "写作 ```text 块，再加 `$$` 是重复"
    assert "$$" not in strip_code_spans(quoted) and "```text" in strip_code_spans(quoted), \
        "control: an unclosed fence example must survive while the quoted $$ next to it goes"
    assert "$$" in strip_code_spans("未闭合的 ``` 符号之后 $$x$$ 仍是公式"), \
        "control: a stray backtick run must not delete a real formula"
    assert "%}" not in visible('<span class="katex"><annotation encoding="application/x-tex">'
                               '95\\%</annotation></span>'), \
        "control: KaTeX's own TeX source is hidden from the reader"
    assert "%}" in visible("<p>a stray 95%} in prose</p>"), "control: a real leak must still be caught"
    print("formula/leak controls ok (code spans, nesting, annotation source)")


def diff(live):
    index = url_index()
    expectations = {}
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in filenames:
            if fn.endswith(".md"):
                text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
                rel = norm(h1_of(text))
                if rel in index:
                    expectations[index[rel]] = dict(expect_of(text), page=os.path.relpath(
                        os.path.join(dirpath, fn), DOCS).replace("\\", "/"))
    problems, checked = [], 0
    for entry in live:
        url = entry["url"]
        exp = expectations.get(url)
        if not exp:
            problems.append("NO EXPECTATION for %s" % url)
            continue
        checked += 1
        problems.extend(classify(entry, exp))
    problems += formula_defects()      # browser-free, so this axis never goes quiet
    print("live parity: pages=%d checked=%d problems=%d" % (len(live), checked, len(problems)))
    for p in problems:
        print("  - " + p)
    return 1 if problems else 0


def main():
    args = sys.argv[1:]
    controls()
    if "--calibrate" in args:
        at = args.index("--calibrate") + 1
        default = os.path.join(HERE, "data", "live_aria_round56.json")
        return calibrate(args[at] if at < len(args) and not args[at].startswith("--") else default)
    if "--diff" in args:
        path = args[args.index("--diff") + 1]
        return diff(json.load(io.open(path, encoding="utf-8")))
    want_all = "--all" in args
    sample = int(args[args.index("--sample") + 1]) if "--sample" in args else 6
    rows, total, _ = build(sample, want_all)
    if "--headless" in args:
        return headless(rows)
    print("widget-bearing pages=%d, emitting %d (sample=%s all=%s)" % (total, len(rows), sample, want_all))
    print("# paste these URLs into the browser, run %s, save the JSON, re-run with --diff" % os.path.basename(PROBE))
    print(json.dumps([{"url": r["url"], **{k: r[k] for k in ("tabs", "katex", "mermaid")}, "page": r["page"]}
                      for r in rows], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
