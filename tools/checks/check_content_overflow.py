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

Usage:
    python tools/checks/check_content_overflow.py
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


def render_html(srcs):
    """KaTeX markup per src, through the pinned build (the axis measures painted HTML)."""
    if not os.path.isdir(KATEX_DIST):
        raise SystemExit("pinned KaTeX dist missing at %s — npm install --prefix %s/data/katex"
                         % (KATEX_DIST, HERE))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump([{"src": s} for s in srcs], fh, ensure_ascii=False)
        src_path = fh.name
    dst_path = src_path + ".out.json"
    env = dict(os.environ, KATEX_REQUIRE_FROM=os.path.join(HERE, "data", "katex"))
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
    proc = srv.edge(name, ["--dump-dom"])
    try:
        return srv.wait(rid, budget, proc)
    finally:
        Server.stop(proc)


def check_fonts(rep):
    f = (rep or {}).get("fonts") or {}
    assert f.get("main") and f.get("math"), \
        "KaTeX webfonts did not load (%s): widths would be fallback-font numbers" % f


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
    print("ruler ok: KaTeX fonts loaded; ink box-independent (element box %dpx at 768 vs %dpx at "
          "1100); plants drag %d/%d/%d px and lose %d px — centred overflow stays reachable"
          % (big[768]["box"], big[1100]["box"], over(by[0][768]), over(by[1][768]),
             over(big[768]), lost(big[768])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--column", type=int, default=COLUMN_LIVE,
                    help="the scroller's content width; 768 is max-w-3xl as measured live (round 62)")
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--limit", type=int, default=0, help="sweep only the first N formulas")
    ap.add_argument("--min-over", type=int, default=16,
                    help="drag px counted as a defect; 16px is the axis' own font size, i.e. one "
                         "glyph — a shorter over is sub-pixel rounding, not something a reader drags")
    ap.add_argument("--no-live", action="store_true", help="skip the served-markup tripwire")
    args = ap.parse_args()

    items = authored_display()
    if args.limit:
        items = items[:args.limit]
    print("authored display formulas=%d over %d pages" % (len(items), len({p for p, _ in items})))

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
        rid += 1
        ruler(srv, rid)

        htmls = render_html([s for _, s in items])
        rows = [{"i": i, "html": h.get("html"), "error": h.get("error")}
                for i, h in enumerate(htmls)]
        allm, errors = [], []
        for s in range(0, len(rows), args.batch):
            batch = rows[s:s + args.batch]
            rid += 1
            rep = sweep(srv, batch, [args.column], rid)
            assert rep and rep.get("rows"), "batch at %d reported nothing — not a clean sweep" % s
            check_fonts(rep)
            got = {r["i"]: (r["cols"][0] if r.get("cols") else None) for r in rep["rows"]}
            assert len(got) == len(batch), "batch lost rows (%d of %d)" % (len(got), len(batch))
            for r in batch:
                page, src = items[r["i"]]
                if r.get("error"):
                    errors.append((page, src, r["error"]))
                    continue
                c = got.get(r["i"])
                if not c or c.get("err"):
                    errors.append((page, src, (c or {}).get("err", "no measurement")))
                    continue
                over = max(0, int(round(c["nat"])) - c["cw"])
                allm.append({"page": page, "src": src, "nat": c["nat"], "cw": c["cw"],
                             "ms": c["ms"], "over": over,
                             "lost": c["lostLeft"] + c["lostRight"]})
            print("  swept %d/%d formulas (over-column so far %d)"
                  % (min(s + args.batch, len(rows)), len(rows),
                     sum(1 for m in allm if m["over"] > 0)))
    finally:
        srv.close()

    for p, s, e in errors:
        print("  RENDER-ERROR %s :: %s :: %s" % (p, s.replace("\n", " ")[:60], e))
    over = [m for m in allm if m["over"] > 0]
    lost = [m for m in allm if m["lost"] > 0]
    hits = [m for m in allm if m["over"] >= args.min_over]
    print("\n-- verdict (column %dpx, KaTeX %s, measured=%d) --"
          % (args.column, KATEX_VERSION, len(allm)))
    print("  over-column=%d  at-or-above bar(%d px drag)=%d  unreachable=%d  render-errors=%d"
          % (len(over), args.min_over, len(hits), len(lost), len(errors)))
    # The negative result is the finding of this round's calibration, so it prints every run: if it
    # ever becomes non-zero, the centred-scroll model changed and the drag bar is the wrong metric.
    print("  unreachable px across ALL formulas: %d (expected 0 — see `ruler`: Chromium reaches "
          "centred overflow by scrolling, so the cost is drag, not lost content)"
          % sum(m["lost"] for m in allm))
    nats = sorted(int(m["nat"]) for m in allm)
    print("  natural width (px): min=%d p50=%d p90=%d p99=%d max=%d"
          % (nats[0], nats[len(nats) // 2], nats[int(len(nats) * .9)], nats[int(len(nats) * .99)], nats[-1]))
    # Reported alongside the bar because it is the number that ages: a book whose worst row sits 2px
    # under the column has no room left for the next formula an author adds.
    near = [m for m in allm if m["over"] == 0 and m["nat"] > 0.95 * args.column]
    print("  headroom: %d formulas use more than 95%% of the column (%s)"
          % (len(near), ["%s=%d" % (m["page"], m["nat"]) for m in sorted(near, key=lambda x: -x["nat"])[:6]]))
    print("  drag distribution: %s" % sorted(
        [(b, sum(1 for m in over if b <= m["over"] < b + 200)) for b in range(0, 2201, 200)],
        key=lambda x: (-x[1], x[0]))[:12])
    print("  worst %d by drag:" % min(20, len(over)))
    for m in sorted(over, key=lambda x: -x["over"])[:20]:
        print("    %-44s nat=%-7s drag=%-6s %s"
              % (m["page"], m["nat"], m["over"], m["src"].replace("\n", " ")[:56]))
    print("  bar=%dpx drag -> %d formulas to fix" % (args.min_over, len(hits)))
    return 1 if hits or errors else 0


if __name__ == "__main__":
    sys.exit(main())
