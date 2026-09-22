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

Why this file is a manifest generator and NOT a self-running judge: the live DOM is
only reachable through a browser. The repo's urllib path sees the pre-hydration HTML
(mermaid containers ship empty with aria-busy=true), so a headless fetch cannot
answer "did the widget render". The browser side runs live_aria_probe.js; its JSON is
piped back here with --diff.

Measured limitation, recorded so a future round does not report it as a defect: with
the in-app browser closed the page has a 0x0 viewport (visibilityState=hidden), so
lazily-rendered pieces never finish. Evidence: 6 consecutive pages, every mermaid
container still had aria-busy=true and 0 <text> nodes after scrollIntoView + 4s wait.
Therefore this judge compares mermaid CONTAINER counts (hydration created a slot for
each authored block) and never claims the diagram painted. Screenshot-based visual
review needs the operator to open the Browser panel once.

Usage:
    python tools/checks/live_aria_manifest.py [--sample N | --all]   # print expectations
    python tools/checks/live_aria_manifest.py --diff live.json       # compare probe output
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


def expect_of(text):
    """Authored counts a correctly rendered page must reproduce in the DOM.

    tabs counts {% tab title="..." %} *items*, not {% tabs %} wrappers: measured live, one page
    with 1 wrapper and 4 items rendered exactly 4 [role=tab] buttons and 4 [role=tabpanel] panels.
    """
    return {
        "tabs": len(re.findall(r"^\s*\{%\s*tab\s+title=", text, flags=re.M)),
        "katex": len(re.findall(r"\$\$", text)) // 2,
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
    print("live parity: pages=%d checked=%d problems=%d" % (len(live), checked, len(problems)))
    for p in problems:
        print("  - " + p)
    return 1 if problems else 0


def main():
    args = sys.argv[1:]
    controls()
    if "--diff" in args:
        path = args[args.index("--diff") + 1]
        return diff(json.load(io.open(path, encoding="utf-8")))
    want_all = "--all" in args
    sample = int(args[args.index("--sample") + 1]) if "--sample" in args else 6
    rows, total, _ = build(sample, want_all)
    print("widget-bearing pages=%d, emitting %d (sample=%s all=%s)" % (total, len(rows), sample, want_all))
    print("# paste these URLs into the browser, run %s, save the JSON, re-run with --diff" % os.path.basename(PROBE))
    print(json.dumps([{"url": r["url"], **{k: r[k] for k in ("tabs", "katex", "mermaid")}, "page": r["page"]}
                      for r in rows], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
