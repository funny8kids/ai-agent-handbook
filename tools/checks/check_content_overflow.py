# -*- coding: utf-8 -*-
"""Content-overflow axis: how much of a display formula can a reader actually bring into view.

Why this file exists (round 63). The Mermaid axis proves over-wide *diagrams* get scaled down (the
labels shrink with the picture). Display formulas are the same size problem with the opposite
mechanism, and the difference decides the fix. The live markup is

    <div class="decoration-primary/6 max-w-3xl w-full print:break-inside-avoid overflow-x-auto">
      <span class="katex-display">…

Measured facts this axis is built on, each with its own provenance:
  * the wrapper is `max-w-3xl` + `overflow-x-auto` and carries NO `layout-wide:` variant — checked
    against the live HTML on every run by `live_math_wrappers()` below, which asserts the class
    tokens rather than trusting this paragraph.
  * `max-w-3xl` = 768px of content column: round 62 measured `<main>` at 768 in a real browser
    (`check_live_column.py`), and round 62's A/B (`check_wide_layout_ab.py`) measured the same
    utility's wide-layout sibling against the platform's own CSS.
  * `.katex-display` computes to `display:block; text-align:center` on the live page, and
    `.katex-mathml` to `position:absolute; clip:rect(1px,…)` (read live this round). KaTeX's own
    stylesheet is therefore in force, and the four stylesheets the document names carry ZERO
    `.katex` rules — nothing overrides the centring.

Centred + scrollable was the sharp-looking part of the theory: `scrollWidth` counts content past
the box's END edge, so a symmetric overflow would strand the left half outside the reachable
scroll range — not "the reader has to drag" but "half the equation is never visible". Measured,
that theory is WRONG for Chromium, and this axis keeps the number that says so: the planted 2807px
formula reports `lostLeft=0, lostRight=0` with `maxScroll=2041`, i.e. the browser puts the whole
overflow on the end side and scrolling reaches all of it. The real cost is therefore DRAG DISTANCE
(`over = natural width - client width`): the reader must swipe to read the formula at all, and on a
390px phone a 1400px formula is ~4 swipes. `ruler()` asserts both halves of that every run, so the
axis cannot quietly start reporting lost content again if the platform's scroll model changes.

Fix direction this axis implies: a formula cannot be widened by the site's layout (no wide
variant), so the only in-repo fix is to author it to fit — split it, or move terms into an
`aligned` block. That is why the threshold is the authored width, not the platform's CSS.

Round 73 ran that fix at the column a laptop reader actually gets: `--column 608` (the live `<main>`
at a 1280px window, with the chapter sidebar and page TOC open — see `check_svg_legibility.py`'s
laptop leg, which re-measures it every run). 11 formulas dragged there while 768 was clean; all 11
were re-stacked with `aligned`/`cases`, none shortened. `COLUMN_LIVE` stays 768 as the certified bar
because the book's own README quotes that column; 608 is the stricter reading authors should target.
Both columns are now swept in one pass by default (`--laptop-column 0` for the certified bar alone),
because a per-column verdict was the only way the round-73 fixes stayed honest: a formula authored to
squeeze past 768 could otherwise sit two glyphs over the laptop reader's column and read clean.

Guards, each here because the failure mode is a silent pass:
  * the pinned KaTeX build must answer, or the axis exits rather than printing widths
    (same rule as check_katex_formulas.py, which owns parse failures).
  * the KaTeX webfonts must actually load — metrics come from them, and a fallback-font run would
    print plausible, wrong widths.
  * a ruler pass measures three planted formulas in a 768px AND a 1100px box: the natural width
      must not move with the box (round 62's lesson: a fixed box's `scrollWidth` is always >= the
      box, so comparing the wrong number makes every row fire), the huge plant must register drag
      in BOTH boxes and ZERO unreachable px, the mid plant must drag at 768 and be clean at 1100,
      and the short plant must read clean in both.
  * the live wrapper assertion runs before any sweeping, so a platform change shows up as a red
    calibration, not as a book full of formulas that suddenly "fit".
  * `stray_markup()` reads the painted text of every formula, because a construct KaTeX does not
    implement can parse clean and still print its option verbatim: an amsmath `[t]` on a nested
    `aligned` renders as the two characters a reader sees. `ruler()` plants one and asserts the
    guard catches it, and asserts a clean formula does not trip it.

Usage:
    python tools/checks/check_content_overflow.py
    python tools/checks/check_content_overflow.py --laptop-column 0  # only the certified 768 bar
    python tools/checks/check_content_overflow.py --column 608      # the laptop reader's column
    python tools/checks/check_content_overflow.py --column 1152     # wide-layout what-if
    python tools/checks/check_content_overflow.py --limit 40        # smoke run
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
KATEX_DIST = os.path.join(HERE, "data", "katex", "node_modules", "katex", "dist")
HTML_RENDERER = os.path.join(HERE, "katex_render_html.mjs")
KATEX_VERSION = "0.18.7"        # same pin as check_katex_formulas.py
COLUMN_LIVE = 768               # max-w-3xl, the column a reader gets (round 62 measurement)
COLUMN_LAPTOP = 608             # round 73: the same `<main>` measured live at a 1280px window, i.e.
                                # with the chapter sidebar and page TOC open. `check_svg_legibility`'s
                                # laptop leg re-reads it every run; here it is the second bar, so a
                                # formula authored to squeeze past 768 cannot silently miss it.
BOX_NATURAL = 4000              # a box wide enough that nothing tears in it, so the `nat` read here
                                # is a property of the formula rather than of the column
sys.path.insert(0, HERE)

import live_aria_manifest as L                # noqa: E402  one tokenizer for "authored"
from check_mermaid_geometry import Server     # noqa: E402  localhost fixture + Edge runner

# The findings print Chinese formulas, so a cp936 console would turn the evidence into mojibake.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# planted, labelled by index, never counted as findings. Widths are calibrated against real
# measurements, not guesses: this axis' first ruler run failed because `PLANT_MID`'s predecessor
# (an entropy + 8-greek expression) rendered at 379px and so proved nothing about the 768/1100
# boundary. The ~200px-per-term plant family below lets a mid and a huge row be authored to order.
PLANT_NARROW = "L = \\sum_{i} w_i x_i"
PLANT_MID = " ".join(["f_{%d} = \\mathrm{attn}(q_{%d}, K, V) \\cdot W_{o}" % (i, i) for i in range(5)])
PLANT_HUGE = " ".join(["f_{t} = \\mathrm{attn}(q_{%d}, K, V) \\cdot W_{o}" % i for i in range(14)])

# `[t]` on a nested block is an amsmath alignment option KaTeX does not implement: the formula
# parses clean, so `render-errors=0` says nothing about it, and the reader is served the two
# characters as text. Round 73 shipped one of these in graphrag.md and found it by looking at the
# render, not at the verdict, so the guard below exists to make that check reproducible.
PLANT_OPT = ("\\begin{cases}\\text{a}: \\begin{aligned}[t] &\\text{left}\\\\ "
             "&\\text{right}\\end{aligned}\\end{cases}")

# The inline leg needs a plant that is wide AS AN INLINE SPAN, and one that is nothing. Calibrated
# on measured numbers, not on the display plants: this source paints 1049px of ink at 16px, so it
# must be caught by a 768px column, while `k` paints 10.7px and must not be caught by anything.
PLANT_INLINE_WIDE = ("\\sum_{i=1}^{n}\\theta_i\\,x_i^{(2)}+\\lambda\\,\\mathrm{Reg}"
                     "+\\beta_0\\gamma+\\alpha_1\\delta_2+\\varepsilon_3\\zeta_4+\\eta_5\\vartheta_6"
                     "+\\oint_{\\partial\\Sigma}\\mathbf{B}\\cdot d\\mathbf{l}"
                     "+\\frac{\\partial^2 u}{\\partial t^2}=c^2\\nabla^2 u"
                     "+\\Gamma^{\\mu}_{\\nu\\rho}\\,g_{\\alpha\\beta}\\,R^{\\nu\\rho}_{\\ \\ \\sigma\\tau}"
                     "+\\mathbb{E}_{x\\sim p}\\!\\left[\\log\\frac{q_\\phi(y|x)}{p_\\theta(y|x)}\\right]"
                     "+\\prod_{k=1}^{m}\\int_{\\Omega_k} f_k\\,d\\mu")
PLANT_INLINE_TINY = "k"

TAG_RE = re.compile(r"<[^>]+>")
STRAY_RE = re.compile(r"\[\s*[tbc]\s*\]|\\(?:begin|end)\{|\\hphantom|\\text\{")


def stray_markup(html):
    """The literal junk a reader sees when KaTeX paints an unsupported construct as text."""
    i = html.find('class="katex-html"')
    # Only the HTML branch counts: .katex-mathml carries the LaTeX source in an <annotation> for
    # assistive tech, so scanning it would flag every formula in the book.
    return STRAY_RE.search(TAG_RE.sub("", html[i:] if i >= 0 else html))


def authored_display():
    """[(page, src)] for every authored display formula; 14-templates quotes markup, per README."""
    items = []
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir.startswith("14-templates"):
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            sources, _ = L.formula_sources(text)
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            items += [(rel, src.strip()) for kind, src in sources if kind == "display"]
    assert len(items) > 150, "vacuity floor: only %d display formulas found" % len(items)
    return items


def authored_inline():
    """[(page, src)] for every authored INLINE formula, through the shared tokenizer.

    Round 102. The display leg above enumerates `kind == "display"`, and that is a difference of
    kind, not of size: a display formula is served inside a wrapper that owns `overflow-x:auto`, so
    an over-wide one is a strip a reader can drag; an inline formula sits in a plain paragraph with
    no such wrapper, and KaTeX lays it out as a run of nowrap atom groups that the browser is free
    to break BETWEEN. Measured this round, on the widest inline span in the book (691px of ink): one
    line at 1100px, two at 768 (454+237), two at 608, with the ink never leaving the paragraph. So
    the defect this leg judges is a formula torn in half across the reader's line, and nothing in
    this repo had ever measured one -- not even after 95 spans were moved into that form in a single
    round.

    `live_aria_manifest.formula_sources` is used rather than a local regex because it is the one
    tokenizer the whole repo shares (three rulers once read three different formula counts off the
    same tree), and because its `prose()` already deletes code spans and fenced blocks: the
    changelog quotes `$$…$$` inside backticks to describe this defect, and a reader sees literal
    dollars there, not math. Table cells are deliberately INCLUDED here and measured again: the
    table axis asks whether a cell's ink leaves the CELL, this leg asks whether the same ink can
    even fit a line.
    """
    items = []
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir.startswith("14-templates"):
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            sources, _ = L.formula_sources(text)
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            items += [(rel, src.strip()) for kind, src in sources if kind == "inline"]
    assert len(items) > 300, "vacuity floor: only %d inline formulas found" % len(items)
    return items


WHOLE_LINE_MATH = re.compile(r"^\s*\$\$(.+)\$\$\s*$")


def whole_line_inline():
    """[(page, line, src)] for a `$$…$$` that owns a line of its own but is NOT a display block.

    The author of such a line means a display formula; the platform serves it inline. That was not
    guessed: this round a page whose only formulas are whole-line spans was fetched and paints
    `katex-display` 0 times and `overflow-x-auto` 0 times, while the control page whose formulas are
    fence-delimited paints 3 and 4. So the intent gets no centring and, more importantly, no
    scroller -- and the display leg never enumerates it, because the shared tokenizer, agreeing with
    the platform, classes it as inline.

    Reported, not judged: once `--inline` measures width, the dangerous half of the difference
    (ink outside the paragraph) is caught either way, and what is left is a presentation mismatch
    the author can settle by writing the fence form the rest of the book uses.
    """
    rows = []
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir.startswith("14-templates"):
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            for i, line in enumerate(text.splitlines(), 1):
                m = WHOLE_LINE_MATH.match(line)
                if m and "$$" not in m.group(1):
                    rows.append((rel, i, m.group(1).strip()))
    return rows


INDENT = re.compile(r"^[ \t]+\S")
PAIR = re.compile(r"\$\$(.+?)\$\$")
BULLET = re.compile(r"^[ \t]*[-*+] ")


def continuation_math_lines(lines):
    """Line numbers where an inline `$$…$$` sits on an indented continuation line.

    This is the one inline placement the platform has never been measured on. Census this round,
    over the whole corpus with fences excluded: 155 list-item lines and 302 paragraph lines carry an
    inline pair (both served as `katex` spans, per the live split leg), and exactly ONE indented
    continuation did -- a line this round's own fix produced and then removed. So the rule is not
    "that form is wrong"; it is "nothing here has ever proved what the reader gets", and round 102
    learned what that costs when the answer was `katex=0`.

    A list item's own line stays silent even when it is indented (a nested `- ` item is one of the
    155 precedented forms); only a line that *hangs* under something else is unmeasured. Fences are
    excluded by CommonMark closure (a run of backticks closes only if it is at least as long as the
    one that opened it), because the book's own examples quote markup at the reader.
    """
    hits, open_run = [], 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            run = len(stripped) - len(stripped.lstrip("`"))
            if open_run:
                if run >= open_run:
                    open_run = 0
            else:
                open_run = run
            continue
        if open_run or BULLET.match(line) or not (INDENT.match(line) and PAIR.search(line)):
            continue
        hits.append(i)
    return hits


def continuation_math():
    rows = []
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir.startswith("14-templates"):
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            for ln in continuation_math_lines(io.open(os.path.join(dirpath, fn), encoding="utf-8")
                                              .read().splitlines()):
                rows.append((rel, ln))
    return rows


def locate(page, src):
    """Best-effort `file:line` for an authored source, so a width hit is reachable by eye."""
    text = io.open(os.path.join(DOCS, page), encoding="utf-8").read()
    needle = re.sub(r"\s+", "", src)[:24]
    for i, line in enumerate(text.splitlines(), 1):
        if needle and needle in re.sub(r"\s+", "", line):
            return "%s:%d" % (page, i)
    return page


def render_html(srcs, display=True):
    """KaTeX markup per src, through the pinned build (the axis measures painted HTML).

    `display=False` renders the INLINE build, which is the markup the platform actually serves for
    an inline formula: a bare `<span class="katex">` in the paragraph, with no `overflow-x-auto`
    wrapper above it. `live_math_wrappers()` and `live_inline_split()` hold that claim open.
    """
    if not os.path.isdir(KATEX_DIST):
        raise SystemExit("pinned KaTeX dist missing at %s — npm install --prefix %s/data/katex"
                         % (KATEX_DIST, HERE))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump([{"src": s} for s in srcs], fh, ensure_ascii=False)
        src_path = fh.name
    dst_path = src_path + ".out.json"
    env = dict(os.environ, KATEX_REQUIRE_FROM=os.path.join(HERE, "data", "katex"),
               KATEX_DISPLAY_MODE="1" if display else "0")
    try:
        proc = subprocess.run(["node", HTML_RENDERER, src_path, dst_path],
                              capture_output=True, text=True, env=env)
        if proc.returncode == 2:
            raise SystemExit("katex not resolvable: %s" % proc.stdout[:200])
        if proc.returncode != 0:
            raise SystemExit("html renderer failed rc=%d: %s" % (proc.returncode, proc.stderr[:400]))
        out = json.load(io.open(dst_path, encoding="utf-8"))
    finally:
        for p in (src_path, dst_path):
            if os.path.exists(p):
                os.unlink(p)
    assert out["version"] == KATEX_VERSION, \
        "off-version render: resolved %s, this axis is quoted as %s" % (out["version"], KATEX_VERSION)
    assert out["count"] == len(srcs), "the renderer lost items"
    # The switch is the whole difference between the two legs, so prove the build obeyed it instead
    # of assuming: an ignored env var would silently measure display markup and call it inline.
    assert out.get("display") is display, \
        "renderer ran displayMode=%s while the caller asked for %s" % (out.get("display"), display)
    return out["items"]


WRAP_RE = re.compile(r'<div class="([^"]*overflow-x-auto[^"]*)"><span class="katex-display"')


def live_math_wrappers(url):
    """The wrapper a reader is served, as a class-token set — the platform-change tripwire.

    No browser here on purpose: this axis must be runnable from a plain checkout, and the three
    things it needs from the platform (there IS a scroller, it is capped by max-w-3xl, and nothing
    gives it a wide-layout variant) are all visible in the served class list. The one thing that
    is NOT (the computed centring) was read live this round and is recorded in the docstring.
    """
    import check_widget_visibility_live as wl
    html = wl.fetch(url)
    wraps = WRAP_RE.findall(html)
    assert wraps, "no math wrapper in the served HTML of %s — the platform changed, " \
                  "recalibrate before trusting any width" % url
    kinds = {tuple(sorted(set(w.split()))) for w in wraps}
    for kind in kinds:
        assert "overflow-x-auto" in kind, "wrapper lost its scroller: %s" % (kind,)
        assert "max-w-3xl" in kind, "wrapper is no longer capped at max-w-3xl: %s" % (kind,)
        assert not any(t.startswith("layout-wide") for t in kind), \
            "the math wrapper now has a wide-layout variant — the column under test changed: %s" % (kind,)
    return len(wraps), " | ".join(" ".join(sorted(k)) for k in sorted(kinds))[:160]


def live_inline_split(url, want_display, want_inline):
    """On the reader's page, display markup appears exactly as many times as the author fenced.

    This is the tripwire under the whole `--inline` leg. The leg measures an inline formula inside a
    plain paragraph, and that model came from one reading of one live page: a page whose formulas
    were all whole-line `$$…$$` spans served `class="katex"` 18 times and `katex-display` 0 times,
    while the control page with three fenced blocks served 13 spans and 3 `katex-display`. If the
    platform ever starts wrapping inline formulas in a scroller (or stops wrapping fenced ones), the
    inline widths measured below would describe a document the reader no longer gets, so the counts
    have to disagree loudly instead of quietly.
    """
    import check_widget_visibility_live as wl
    html = wl.fetch(url)
    spans = html.count('class="katex"')
    display = len(re.findall(r'class="katex-display"', html))
    assert display == want_display, \
        "%s: author fenced %d display formulas but the reader is served %d katex-display — the " \
        "display/inline split this leg is built on has changed, re-read it before believing a width" \
        % (url, want_display, display)
    assert spans >= want_display + want_inline, \
        "%s: %d authored formulas but only %d katex spans served — the reader is losing math, and a " \
        "sweep of markup nobody receives proves nothing" % (url, want_display + want_inline, spans)
    return spans, display


MEASURE_JS = """
<script>
(function () {
  var RID = @@RID@@, ITEMS = @@ITEMS@@, COLS = @@COLS@@;
  // One box per (formula, column): max-w-3xl + w-full + overflow-x-auto, i.e. the wrapper the
  // site serves. The centring comes from KaTeX's own .katex-display rule, which the loaded
  // katex.min.css supplies — that is the point of loading it, not hand-styling anything.
  function cell(html, width) {
    var d = document.createElement('div');
    d.style.cssText = 'max-width:' + width + 'px;width:100%;overflow-x:auto';
    d.innerHTML = html;
    document.getElementById('out').appendChild(d);
    return d;
  }
  function ink(k) {
    // KaTeX's display rule is `.katex-display>.katex{display:block;white-space:nowrap}`, so the
    // element's own box is the CONTAINER's width — measuring it would read the box and always
    // "fit". The Range rect is the laid-out text fragments, i.e. the ink, which is what a reader
    // either sees or does not.
    var r = document.createRange();
    r.selectNodeContents(k);
    return r.getBoundingClientRect();
  }
  function probe(d) {
    var k = d.querySelector('.katex-html') || d.querySelector('.katex');
    if (!k) return {err: 'no .katex in the rendered output'};
    var cr = d.getBoundingClientRect(), box = k.getBoundingClientRect();
    var offs = [];
    d.scrollLeft = 0; offs.push(ink(k).left - cr.left);
    d.scrollLeft = 1e5; offs.push(ink(k).left - cr.left);
    var nat = Math.max.apply(null, offs.map(function (l, i) {
      d.scrollLeft = [0, 1e5][i]; return ink(k).width; }));
    var lmin = Math.min(offs[0], offs[1]), lmax = Math.max(offs[0], offs[1]);
    // content pixel s (0..nat) is in view for some reachable scroll iff
    // -lmax <= s <= clientWidth - lmin
    return {nat: Math.round(nat * 100) / 100, box: Math.round(box.width), cw: d.clientWidth,
            sw: d.scrollWidth, ms: d.scrollLeft, lostLeft: Math.max(0, Math.round(-lmax)),
            lostRight: Math.max(0, Math.round(nat - d.clientWidth + lmin))};
  }
  function send(obj) {
    // Synchronous XHR, not sendBeacon: a beacon queued at document teardown is dropped, which is
    // how the first sweep of this axis came back with reports=0 and a browser that had exited.
    var x = new XMLHttpRequest();
    x.open('POST', '/report', false);
    x.send(JSON.stringify(obj));
  }
  function run() {
    // Webfonts are requested only when text that needs them is laid out, so the cells go in
    // FIRST and the measurement waits for the faces. The first version of this checked
    // document.fonts at ready-time and reported KaTeX_Main=false — i.e. it was about to measure
    // fallback-font widths, which are plausible numbers and therefore worse than an error.
    var built = ITEMS.map(function (it) {
      return {i: it.i, err: it.error || null,
              cells: it.error ? [] : COLS.map(function (c) { return {col: c, el: cell(it.html, c)}; })};
    });
    void document.body.offsetWidth;
    var tries = 0;
    (function poll() {
      var ok = document.fonts.check('16px KaTeX_Main') && document.fonts.check('16px KaTeX_Math');
      if (!ok && tries++ < 40) { setTimeout(poll, 150); return; }
      var out = built.map(function (b) {
        var row = {i: b.i, cols: [], err: b.err};
        b.cells.forEach(function (c) {
          try { var p = probe(c.el); p.col = c.col; row.cols.push(p); }
          catch (e) { row.cols.push({col: c.col, err: String(e.message).slice(0, 120)}); }
        });
        return row;
      });
      send({id: RID, done: true, rows: out, fontTries: tries,
            fonts: {status: document.fonts.status, main: document.fonts.check('16px KaTeX_Main'),
                    math: document.fonts.check('16px KaTeX_Math')}});
      var h = new XMLHttpRequest(); h.open('GET', '/hold?rid=' + RID, false);
      try { h.send(); } catch (e) {}
    })();
  }
  run();
})();
</script>
"""


def fixture(rows, cols, rid):
    head = ("<link rel='stylesheet' href='/katex.min.css'>"
            "<style>body{margin:0;font-size:16px;background:#fff}</style>")
    js = (MEASURE_JS.replace("@@RID@@", str(rid))
          .replace("@@ITEMS@@", json.dumps(rows, ensure_ascii=False))
          .replace("@@COLS@@", json.dumps(cols)))
    # The trailing subresource is what keeps headless Chrome alive while the poll runs: an
    # outstanding request holds the document 'loading', and the server releases it when this
    # fixture's report lands. Without it the browser exits at first paint and reports nothing
    # (the geometry axis' fixture uses the same latch for the same reason).
    return ("<!doctype html><meta charset='utf-8'>" + head + "<div id='out'></div>" + js +
            "<script src='/hold?rid=%d'></script>" % rid)


def serve_katex(srv):
    shutil.copyfile(os.path.join(KATEX_DIST, "katex.min.css"),
                    os.path.join(srv.root, "katex.min.css"))
    shutil.copytree(os.path.join(KATEX_DIST, "fonts"), os.path.join(srv.root, "fonts"))


def sweep(srv, rows, cols, rid, budget=90):
    name = "overflow-%d.html" % rid
    io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(fixture(rows, cols, rid))
    srv.hold(rid, budget + 25)
    proc = srv.render(name, ["--dump-dom"])
    try:
        return srv.wait(rid, budget, proc)
    finally:
        Server.stop(proc)


def check_fonts(rep):
    f = (rep or {}).get("fonts") or {}
    assert f.get("main") and f.get("math"), \
        "KaTeX webfonts did not load (%s): widths would be fallback-font numbers" % f


MEASURE_INLINE_JS = """
<script>
(function () {
  var RID = @@RID@@, ITEMS = @@ITEMS@@, COLS = @@COLS@@;
  // A plain paragraph at the reader's column width, Chinese on both sides, exactly as the site
  // serves an inline formula: no `overflow-x-auto` anywhere above it (that wrapper belongs to
  // `.katex-display`). Nothing is hand-styled beyond the width — the nowrap inside each atom group
  // is KaTeX's own `.katex .katex-base` rule, and the break opportunities between those groups are
  // the browser's, which is what this leg turns out to be measuring.
  // The prefix is part of the bar, not decoration: an inline formula is placed after whatever text
  // already filled the line, so a 558px span that fits a *bare* 608px column still tears there
  // (round 103 caught exactly that on the frozen-`CONFIG` line of build-03-budget.md, which had
  // only five characters in front of it in print). `BOX_NATURAL` measures the same source in a
  // 4000px box to get its intrinsic width.
  function cell(html, width) {
    var d = document.createElement('p');
    d.style.cssText = 'max-width:' + width + 'px;width:100%;margin:0';
    d.innerHTML = '该项的复杂度是' + html + '，因此下面给出推导';
    document.getElementById('out').appendChild(d);
    return d;
  }
  function probe(d) {
    var k = d.querySelector('.katex-html') || d.querySelector('.katex');
    if (!k) return {err: 'no .katex painted'};
    var r = document.createRange();
    r.selectNodeContents(k);
    var ink = r.getBoundingClientRect(), dr = d.getBoundingClientRect();
    // `.katex-html`, not `.katex`: the MathML branch is absolutely positioned with a clip, and a
    // Range over the whole span unions it in (measured 1161px of "ink" for a 1037px formula).
    // `frag` is how many line boxes the span occupies, and that is the defect: an inline formula
    // does NOT spill past the paragraph. KaTeX emits one nowrap `.katex-base` per atom group, the
    // browser breaks between those groups, and a span too wide for the column is TORN. Measured
    // this round on the widest inline formula in the book (691px of ink): one fragment at 1100px,
    // two at 768 (454 + 237), two at 608 — and its ink's right edge never passed the paragraph's.
    // `over` is kept because it is the behavioural tripwire: if it ever reads non-zero, the browser
    // or the platform changed and tearing is no longer the failure a reader meets.
    return {nat: Math.round(ink.width * 100) / 100, cw: d.clientWidth,
            frag: k.getClientRects().length,
            over: Math.max(0, Math.round(ink.right - (dr.left + d.clientWidth))),
            lostLeft: Math.max(0, Math.round(dr.left - ink.left))};
  }
  function send(obj) {
    var x = new XMLHttpRequest();
    x.open('POST', '/report', false);
    x.send(JSON.stringify(obj));
  }
  var built = ITEMS.map(function (it) {
    return {i: it.i, err: it.error || null,
            cells: it.error ? [] : COLS.map(function (c) { return {col: c, el: cell(it.html, c)}; })};
  });
  void document.body.offsetWidth;
  var tries = 0;
  (function poll() {
    var ok = document.fonts.check('16px KaTeX_Main') && document.fonts.check('16px KaTeX_Math');
    if (!ok && tries++ < 60) { setTimeout(poll, 150); return; }
    var out = built.map(function (b) {
      var row = {i: b.i, cols: [], err: b.err};
      b.cells.forEach(function (c) {
        try { var p = probe(c.el); p.col = c.col; row.cols.push(p); }
        catch (e) { row.cols.push({col: c.col, err: String(e.message).slice(0, 120)}); }
      });
      return row;
    });
    send({id: RID, done: true, rows: out, fontTries: tries,
          fonts: {status: document.fonts.status, main: document.fonts.check('16px KaTeX_Main'),
                  math: document.fonts.check('16px KaTeX_Math')}});
    var h = new XMLHttpRequest(); h.open('GET', '/hold?rid=' + RID, false);
    try { h.send(); } catch (e) {}
  })();
})();
</script>
"""


def fixture_inline(rows, cols, rid):
    head = ("<link rel='stylesheet' href='/katex.min.css'>"
            "<style>body{margin:0;font-size:16px;background:#fff}</style>")
    js = (MEASURE_INLINE_JS.replace("@@RID@@", str(rid))
          .replace("@@ITEMS@@", json.dumps(rows, ensure_ascii=False))
          .replace("@@COLS@@", json.dumps(cols)))
    return ("<!doctype html><meta charset='utf-8'>" + head + "<div id='out'></div>" + js +
            "<script src='/hold?rid=%d'></script>" % rid)


def sweep_inline(srv, rows, cols, rid, budget=90):
    name = "inline-overflow-%d.html" % rid
    io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(fixture_inline(rows, cols, rid))
    srv.hold(rid, budget + 25)
    proc = srv.render(name, ["--dump-dom"])
    try:
        return srv.wait(rid, budget, proc)
    finally:
        Server.stop(proc)



def ruler(srv, rid):
    """The ruler must read the formula, not the box — and must not invent the defect it was built for.

    The second half is the point of this pass. The axis was written to prove that a centred,
    over-wide formula loses its left half (the classic `scrollWidth` counts only the end edge
    failure). The planted 2807px counterexample measured `lostLeft=0, lostRight=0` with
    `maxScroll=2041`: Chromium puts the overflow entirely on the END side and the scroll reaches
    all of it. So the honest reading is a drag, not lost content — and these controls now pin BOTH
    directions, so the axis cannot quietly start reporting a defect that isn't there.
    """
    plants = [PLANT_NARROW, PLANT_MID, PLANT_HUGE]
    htmls = render_html(plants)
    rows = [{"i": i, "html": h["html"]} for i, h in enumerate(htmls)]
    rep = sweep(srv, rows, [768, 1100], rid, budget=45)
    assert rep and rep.get("rows"), "ruler pass reported nothing — the harness is broken"
    check_fonts(rep)
    by = {r["i"]: {c["col"]: c for c in r["cols"]} for r in rep["rows"]}
    assert len(by) == 3, "ruler lost rows: %s" % sorted(by)
    for i, cols in sorted(by.items()):
        nats = [c["nat"] for c in cols.values()]
        assert max(nats) - min(nats) <= 2, \
            "natural width moved with the box (%s) — measuring the container, not the formula" % nats
    # The element rect is the container's width by construction (.katex is display:block); the ink
    # is not. If they never differed the axis would be reading the box, so prove they do differ.
    big = by[2]
    assert big[768]["box"] <= 770 and big[1100]["box"] >= 1080 and big[768]["nat"] > 1100, \
        "the huge plant does not separate box from ink: %s" % big
    lost = lambda c: c["lostLeft"] + c["lostRight"]
    over = lambda c: max(0, int(round(c["nat"])) - c["cw"])
    assert over(big[768]) > 1000 and over(big[1100]) > 700, \
        "a 2807px formula reports no drag in an 1100px box (%s): the drag metric is toothless" % big
    assert lost(big[768]) == 0 and lost(big[1100]) == 0, \
        "the plant now reads unreachable px (%s) — the platform changed behaviour, re-read this " \
        "axis' premise before trusting any number it prints" % big[768]
    assert over(by[1][768]) > 0 and over(by[1][1100]) == 0, \
        "the mid plant must drag at 768 and fit at 1100: %s" % by[1]
    assert over(by[0][768]) == 0 and lost(by[0][768]) == 0, \
        "a short formula must read clean in both boxes: %s" % by[0]
    # The stray-markup guard has to catch the failure it was written for, and only that failure.
    opt, clean = render_html([PLANT_OPT, PLANT_NARROW])
    hit = stray_markup(opt["html"])
    assert hit, "the planted `[t]` option was not flagged — the stray-markup guard is dead: %s" % opt["html"][:160]
    assert not stray_markup(clean["html"]), \
        "a clean formula flags as stray markup: %s" % clean["html"][:160]
    print("stray-markup control ok: a planted amsmath `[t]` option paints %r and the guard sees it; "
          "a clean formula does not" % hit.group(0))
    print("ruler ok: KaTeX fonts loaded; ink box-independent (element box %dpx at 768 vs %dpx at "
          "1100); plants drag %d/%d/%d px and lose %d px — centred overflow stays reachable"
          % (big[768]["box"], big[1100]["box"], over(by[0][768]), over(by[1][768]),
             over(big[768]), lost(big[768])))


def ruler_inline(srv, rid):
    """The inline leg must see the class it was built for, and nothing else.

    Both directions are pinned, because a new leg fails two different ways: one that cannot see the
    class it was built for is useless, and one that invents it reddens the whole corpus. This pass
    also carries the leg's behavioural premise, measured rather than assumed: a span too wide for
    the column must show MORE THAN ONE line fragment (`frag`) and must NOT push ink past the
    paragraph's right edge (`over`). Those two together are the finding — the reader of a torn
    formula sees it split between atom groups, which is a different defect from a spill and needs a
    different fix.
    """
    htmls = render_html([PLANT_INLINE_TINY, PLANT_INLINE_WIDE], display=False)
    assert '<span class="katex-display"' not in htmls[1]["html"], \
        "displayMode=0 still emitted display markup — the inline leg is measuring the wrong build"
    rows = [{"i": i, "html": h["html"]} for i, h in enumerate(htmls)]
    rep = sweep_inline(srv, rows, [BOX_NATURAL, 1100, 768, 608], rid, budget=45)
    assert rep and rep.get("rows"), "inline ruler pass reported nothing — the harness is broken"
    check_fonts(rep)
    by = {r["i"]: {c["col"]: c for c in r["cols"]} for r in rep["rows"]}
    assert len(by) == 2, "inline ruler lost rows: %s" % sorted(by)
    tiny, wide = by[0], by[1]
    assert tiny[768]["frag"] == 1 and tiny[608]["frag"] == 1, \
        "a one-character formula is torn across lines (%s): the leg invents defects" % tiny
    assert tiny[768]["nat"] < 40, "a one-character formula measured %s px wide" % tiny[768]["nat"]
    nat = wide[BOX_NATURAL]["nat"]
    assert nat > COLUMN_LIVE, \
        "the planted formula paints only %dpx in a %dpx box — the plant is too short to prove " \
        "anything about the columns" % (nat, BOX_NATURAL)
    assert wide[BOX_NATURAL]["frag"] == 1, \
        "the plant tears even in a %dpx box (%s): the natural width is not measurable here" \
        % (BOX_NATURAL, wide[BOX_NATURAL])
    assert wide[768]["frag"] > 1 and wide[608]["frag"] > 1, \
        "a %dpx span sits on one line in a 768px paragraph (%s) — the tear metric is toothless" \
        % (int(nat), wide[768])
    assert wide[608]["frag"] >= wide[768]["frag"], \
        "the narrower column tore the same span into fewer lines (%s): that is not a layout reading" % wide
    for c in (1100, 768, 608):
        assert wide[c]["over"] == 0 and wide[c]["lostLeft"] == 0, \
            "an inline span pushed ink outside the paragraph at %dpx (%s) — the browser or the " \
            "platform changed under this leg: tearing is no longer what a reader meets, re-read it" \
            % (c, wide[c])
    print("inline ruler ok: plant %dpx tears into %d fragments at 768 and %d at 608 while its ink "
          "never leaves the paragraph (over=0 at every column); a 1-char formula stays whole at %spx"
          % (int(nat), wide[768]["frag"], wide[608]["frag"], tiny[768]["nat"]))


def report_inline(col, ms):
    """The inline verdict: formulas a reader sees torn across lines in a paragraph of width `col`."""
    torn = [m for m in ms if m["frag"] > 1]
    print("\n-- verdict (INLINE span, paragraph %dpx, KaTeX %s, measured=%d) --"
          % (col, KATEX_VERSION, len(ms)))
    print("  torn across lines=%d  whole=%d" % (len(torn), len(ms) - len(torn)))
    # The behavioural half of the ruler, printed every run for the same reason the display leg
    # prints `unreachable=0`: if it stops being zero, the model below is not the reader's model.
    print("  ink outside the paragraph: %d px (expected 0 — an over-wide inline span tears between "
          "KaTeX's atom groups, it does not spill)" % sum(m["over"] for m in ms))
    if ms:
        nats = sorted(int(m["nat"]) for m in ms)
        print("  natural ink width (px): min=%d p50=%d p90=%d p99=%d max=%d"
              % (nats[0], nats[len(nats) // 2], nats[int(len(nats) * .9)],
                 nats[min(int(len(nats) * .99), len(nats) - 1)], nats[-1]))
        near = [m for m in ms if m["frag"] == 1 and m["nat"] > 0.95 * col]
        print("  headroom: %d inline sources already use more than 95%% of the paragraph (%s)"
              % (len(near), ["%s=%d" % (locate(m["page"], m["src"]), m["nat"])
                             for m in sorted(near, key=lambda x: -x["nat"])[:6]]))
    print("  the %d torn source(s), worst first by natural width:" % len(torn))
    for m in sorted(torn, key=lambda x: -x["nat"])[:20]:
        print("    %-46s nat=%-7s lines=%-3s %s"
              % (locate(m["page"], m["src"]), m["nat"], m["frag"],
                 m["src"].replace("\n", " ")[:52]))
    print("  bar=one line -> %d sources to fix" % len(torn))
    return torn


def report_column(col, ms, min_over):
    """One column's verdict, printed in full: the book is read at more than one width now."""
    over = [m for m in ms if m["over"] > 0]
    lost = [m for m in ms if m["lost"] > 0]
    hits = [m for m in ms if m["over"] >= min_over]
    print("\n-- verdict (column %dpx, KaTeX %s, measured=%d) --" % (col, KATEX_VERSION, len(ms)))
    print("  over-column=%d  at-or-above bar(%d px drag)=%d  unreachable=%d"
          % (len(over), min_over, len(hits), len(lost)))
    # The negative result is the finding of round 63's calibration, so it prints every run: if it
    # ever becomes non-zero, the centred-scroll model changed and the drag bar is the wrong metric.
    print("  unreachable px across ALL formulas: %d (expected 0 — see `ruler`: Chromium reaches "
          "centred overflow by scrolling, so the cost is drag, not lost content)"
          % sum(m["lost"] for m in ms))
    nats = sorted(int(m["nat"]) for m in ms)
    print("  natural width (px): min=%d p50=%d p90=%d p99=%d max=%d"
          % (nats[0], nats[len(nats) // 2], nats[int(len(nats) * .9)],
             nats[int(len(nats) * .99)], nats[-1]))
    # Reported alongside the bar because it is the number that ages: a book whose worst row sits 2px
    # under the column has no room left for the next formula an author adds.
    near = [m for m in ms if m["over"] == 0 and m["nat"] > 0.95 * col]
    print("  headroom: %d formulas use more than 95%% of the column (%s)"
          % (len(near), ["%s=%d" % (m["page"], m["nat"])
                         for m in sorted(near, key=lambda x: -x["nat"])[:6]]))
    print("  drag distribution: %s" % sorted(
        [(b, sum(1 for m in over if b <= m["over"] < b + 200)) for b in range(0, 2201, 200)],
        key=lambda x: (-x[1], x[0]))[:12])
    print("  worst %d by drag:" % min(20, len(over)))
    for m in sorted(over, key=lambda x: -x["over"])[:20]:
        print("    %-44s nat=%-7s drag=%-6s %s"
              % (m["page"], m["nat"], m["over"], m["src"].replace("\n", " ")[:56]))
    print("  bar=%dpx drag -> %d formulas to fix" % (min_over, len(hits)))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--column", type=int, default=COLUMN_LIVE,
                    help="the primary scroller width swept; 768 is max-w-3xl as measured live "
                         "(round 62), and the column the README quotes")
    ap.add_argument("--laptop-column", type=int, default=COLUMN_LAPTOP,
                    help="a second column swept in the same pass (608 = the live <main> at a 1280 "
                         "window, round 73); 0 measures only --column")
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--limit", type=int, default=0, help="sweep only the first N formulas")
    ap.add_argument("--min-over", type=int, default=16,
                    help="drag px counted as a defect; 16px is the axis' own font size, i.e. one "
                         "glyph — a shorter over is sub-pixel rounding, not something a reader drags")
    ap.add_argument("--no-live", action="store_true", help="skip the served-markup tripwire")
    ap.add_argument("--no-inline", action="store_true",
                    help="skip the inline-span leg (only for reading the display verdict in "
                         "isolation; the battery runs both, and the tripwire below proves the "
                         "display/inline split the inline leg is built on)")
    args = ap.parse_args()

    items = authored_display()
    if args.limit:
        items = items[:args.limit]
    inline_items = [] if args.no_inline else authored_inline()
    cols = [args.column] + ([args.laptop_column]
                            if args.laptop_column and args.laptop_column != args.column else [])
    print("authored display formulas=%d over %d pages | columns swept=%s"
          % (len(items), len({p for p, _ in items}), cols))
    if inline_items:
        print("authored inline formulas=%d (%d distinct sources) over %d pages | "
              "whole-line-but-inline form=%d"
              % (len(inline_items), len({s for _, s in inline_items}),
                 len({p for p, _ in inline_items}), len(whole_line_inline())))
    control_continuation()

    dummy = os.path.join(tempfile.gettempdir(), "overflow-none.js")
    io.open(dummy, "w", encoding="utf-8").write("// this axis loads KaTeX, not Mermaid\n")
    srv = Server(js_path=dummy)
    serve_katex(srv)
    rid = 0
    try:
        import check_widget_visibility_live as wl
        if not args.no_live:
            page = max({p for p, _ in items}, key=lambda p: sum(1 for q, _ in items if q == p))
            text = io.open(os.path.join(DOCS, page), encoding="utf-8").read()
            m = re.search(r"^# (.+)$", text, flags=re.M)
            entries = wl.llms_entries()
            index, ambiguous = wl.page_index(entries)
            assert not ambiguous, "ambiguous published titles: %s" % sorted(ambiguous)
            url = index.get(wl.norm(m.group(1).strip())) or ""
            if url.endswith(".md"):
                url = url[:-3]     # the .md endpoint is markup, not the reader's document
            assert url, "no live URL for the math page %s — the tripwire has nothing to read" % page
            n, kinds = live_math_wrappers(url)
            print("live tripwire ok: %d math wrappers on %s, class set=%s"
                  % (n, page.split("/")[0], kinds))
            if inline_items:
                # A page with BOTH kinds, because the inline leg is built on the claim that the
                # platform hands a fenced block a scroller and hands an inline span nothing.
                di, ii = {}, {}
                for p, _ in items:
                    di[p] = di.get(p, 0) + 1
                for p, _ in inline_items:
                    ii[p] = ii.get(p, 0) + 1
                both = [p for p in di if ii.get(p)]
                assert both, "no page carries both kinds — the split tripwire has nothing to read"
                page2 = max(both, key=lambda p: di[p] + ii[p])
                text2 = io.open(os.path.join(DOCS, page2), encoding="utf-8").read()
                title2 = re.search(r"^# (.+)$", text2, flags=re.M).group(1).strip()
                url2 = index.get(wl.norm(title2)) or ""
                if url2.endswith(".md"):
                    url2 = url2[:-3]
                assert url2, "no live URL for %s" % page2
                spans, disp = live_inline_split(url2, di[page2], ii[page2])
                print("live split ok: %s author=%d display + %d inline, served=%d katex spans "
                      "of which %d katex-display" % (page2, di[page2], ii[page2], spans, disp))
        rid += 1
        ruler(srv, rid)

        htmls = render_html([s for _, s in items])
        stray = [(page, src, stray_markup(h["html"]).group(0))
                 for (page, src), h in zip(items, htmls)
                 if not h.get("error") and stray_markup(h["html"])]
        rows = [{"i": i, "html": h.get("html"), "error": h.get("error")}
                for i, h in enumerate(htmls)]
        allm, errors = [], []
        for s in range(0, len(rows), args.batch):
            batch = rows[s:s + args.batch]
            rid += 1
            rep = sweep(srv, batch, cols, rid)
            assert rep and rep.get("rows"), "batch at %d reported nothing — not a clean sweep" % s
            check_fonts(rep)
            got = {r["i"]: {c["col"]: c for c in r.get("cols", [])} for r in rep["rows"]}
            assert len(got) == len(batch), "batch lost rows (%d of %d)" % (len(got), len(batch))
            for r in batch:
                page, src = items[r["i"]]
                if r.get("error"):
                    errors.append((page, src, r["error"]))
                    continue
                for col in cols:
                    c = got.get(r["i"], {}).get(col)
                    if not c or c.get("err"):
                        errors.append((page, src,
                                       (c or {}).get("err", "no measurement @%d" % col)))
                        continue
                    over = max(0, int(round(c["nat"])) - c["cw"])
                    allm.append({"col": col, "page": page, "src": src, "nat": c["nat"],
                                 "cw": c["cw"], "ms": c["ms"], "over": over,
                                 "lost": c["lostLeft"] + c["lostRight"]})
            print("  swept %d/%d formulas x %d columns (over-column cells so far %d)"
                  % (min(s + args.batch, len(rows)), len(rows), len(cols),
                     sum(1 for m in allm if m["over"] > 0)))

        inline_m, inline_err = [], []
        if inline_items:
            rid += 1
            ruler_inline(srv, rid)
            # One measurement per distinct source: the ink width of a formula is a property of the
            # formula, not of the page it is written on, and the corpus repeats sources a lot.
            first = {}
            for p, src in inline_items:
                first.setdefault(src, p)
            srcs = sorted(first, key=lambda s: (-len(s), s))
            if args.limit:
                srcs = srcs[:args.limit]
            ih = render_html(srcs, display=False)
            irows = [{"i": i, "html": h.get("html"), "error": h.get("error")}
                     for i, h in enumerate(ih)]
            icols = [BOX_NATURAL] + cols
            for s in range(0, len(irows), args.batch):
                batch = irows[s:s + args.batch]
                rid += 1
                rep = sweep_inline(srv, batch, icols, rid)
                assert rep and rep.get("rows"), "inline batch at %d reported nothing — not a clean sweep" % s
                check_fonts(rep)
                got = {r["i"]: {c["col"]: c for c in r.get("cols", [])} for r in rep["rows"]}
                assert len(got) == len(batch), "inline batch lost rows (%d of %d)" % (len(got), len(batch))
                for r in batch:
                    src, page = srcs[r["i"]], first[srcs[r["i"]]]
                    if r.get("error"):
                        inline_err.append((page, src, r["error"]))
                        continue
                    cells = got.get(r["i"], {})
                    for col in cols:
                        c, nat_c = cells.get(col), cells.get(BOX_NATURAL)
                        bad = [(x, (x or {}).get("err", "no measurement @%d" % k))
                               for k, x in ((col, c), (BOX_NATURAL, nat_c)) if not x or x.get("err")]
                        if bad:
                            inline_err.append((page, src, bad[0][1]))
                            continue
                        inline_m.append({"col": col, "page": page, "src": src,
                                         "nat": nat_c["nat"], "frag": c["frag"],
                                         "over": c["over"], "lostLeft": c["lostLeft"],
                                         "cw": c["cw"]})
                print("  swept %d/%d inline sources x %d columns (torn so far %d)"
                      % (min(s + args.batch, len(irows)), len(irows), len(cols),
                         sum(1 for m in inline_m if m["frag"] > 1)))
    finally:
        srv.close()

    for p, s, e in errors:
        print("  RENDER-ERROR %s :: %s :: %s" % (p, s.replace("\n", " ")[:60], e))
    hits = []
    for col in cols:
        hits += report_column(col, [m for m in allm if m["col"] == col], args.min_over)
    for p, s, e in inline_err:
        print("  INLINE-ERROR %s :: %s :: %s" % (p, s.replace("\n", " ")[:60], e))
    for col in cols:
        hits += report_inline(col, [m for m in inline_m if m["col"] == col])
    wl_rows = whole_line_inline()
    if wl_rows:
        print("\n  FORM-WHOLELINE %d: a `$$…$$` that owns its own line but is not a fenced block — "
              "the platform serves it inline (no centring, no scroller, and only the inline leg "
              "measures it). Write the fence form if display was the intent:" % len(wl_rows))
        for p, ln, s in wl_rows:
            print("    FORM-WHOLELINE %s:%d :: %s" % (p, ln, s.replace("\n", " ")[:64]))
    cont_rows = continuation_math()
    print("unmeasured-placement rows=%d (indented continuation line carrying an inline "
          "$$…$$: never served, never measured)" % len(cont_rows))
    for p, ln in cont_rows:
        print("  FORM-CONT %s:%d :: put the formula on the line that carries it (the list item's own "
              "line, or the paragraph's) or into a fenced block — those are the only forms the live "
              "split leg has evidence for" % (p, ln))
    # Print once, not per column: a stray option character is in the authored source, so it is
    # wrong at every width and a second report of it would only double the noise.
    print("\n  render-errors=%d  inline-errors=%d  stray-markup=%d"
          % (len(errors), len(inline_err), len(stray)))
    for p, s, g in stray:
        print("  STRAY-MARKUP %s :: paints %r as text :: %s"
              % (p, g, s.replace("\n", " ")[:70]))
    return 1 if hits or errors or stray or inline_err or cont_rows else 0


def control_continuation():
    """Both directions, because a rule that cannot fire guards nothing and one that misfires reds
    the corpus: the unmeasured placement must be caught on each of the two things it can hang under,
    and the precedented forms beside it must stay silent."""
    phantom_under_bullet = ["- 要点：先写奖励比：$$r(x,y)$$，代入即得",
                            "  $$\\mathcal{L}=-\\log\\sigma(w-l)$$，其中 `Δ` 是差。"]
    phantom_under_paragraph = ["正文里先写 $$r(x,y)$$。",
                               "  接着 $$\\mathcal{L}=-(w-l)$$，其中 `Δ` 是差。"]
    bullet_inline = ["- 要点：先写奖励比：$$r(x,y)$$，代入即得 $$\\mathcal{L}=-(w-l)$$，其中 `Δ` 是差。"]
    nested_bullet = ["- 外层：", "  - 内层把公式写在自己的行上：$$\\mathcal{L}=-(w-l)$$。"]
    paragraph = ["正文里写 $$x=y$$ 是常态。", "", "- 另一条要点。"]
    fenced = ["- 要点：下面这段是给人读的写法示例：", "  ```markdown", "  - 引用里的例子 $$a$$",
              "    $$b$$", "  ```"]
    for name, lines in (("under a bullet", phantom_under_bullet),
                        ("under a paragraph", phantom_under_paragraph)):
        got = continuation_math_lines(lines)
        assert len(got) == 1 and got[0] == 2, \
            "the phantom continuation %s was not caught: %s" % (name, got)
    for name, lines in (("list-item line", bullet_inline), ("nested list item", nested_bullet),
                        ("paragraph", paragraph), ("fenced example", fenced)):
        assert not continuation_math_lines(lines), \
            "the %s form flags as an unmeasured placement: %s" % (name, lines)
    print("continuation-placement control ok: the indented-continuation phantom is caught under both "
          "a bullet and a paragraph, while the 155-line precedent (math on the list item's own line, "
          "nested items included), the 302-line paragraph precedent and a fenced example of the same "
          "markup stay silent")


if __name__ == "__main__":
    sys.exit(main())
