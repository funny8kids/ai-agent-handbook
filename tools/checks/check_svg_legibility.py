# -*- coding: utf-8 -*-
"""SVG figure legibility: what size does a hand-drawn label reach the reader at?

Why this file exists (round 64). The Mermaid axis proved that a diagram wider than the reader's
column is SCALED down and its labels shrink with it. The 32 in-body SVG figures are the other half
of the book's pictures and nobody had measured them. The live markup says they are in the same
class of problem:

    <img data-testid="zoom-image" alt="" style="max-width:100%;height:auto" src=".../~gitbook/image?...">

so a figure authored on a 960-wide canvas lands in a 768 column at 0.8x, and a 9.5px label is
painted at 7.6px. Both factors are MEASURED here rather than assumed: `<main>` and every figure's
`naturalWidth` vs its painted width come from a real browser on a copy of the live page, and the
font sizes come from the authored SVG with inheritance applied (the root carries `font-size="13"`
and most `<text>` nodes override it).

The arithmetic is invariant under uniform rescaling: tightening a viewBox and scaling the drawing
by the same factor changes nothing. The only in-repo fix is a better text-to-canvas ratio, i.e.
re-authoring the figure — which is why this axis reports per-figure and per-label counts instead of
a single number.

Readings. Round 64 baseline (column 768): 32 authored in-body figures and ALL 32 painted at least
one label under the 12px bar — 956 of 1042 text labels, smallest effective size 5.20px (the homepage
`banner-home.svg`: 13px authored on a 1920 canvas, i.e. 0.4x), per-figure minimums 5.20..10.40px.
Round 65 batch 1 re-authored 5 of them (the banner plus four 960 canvases) onto >= 15px type; the same
axis now reads 27 figures / 735 of 1057 labels, and the 1152 what-if drops from 23 figures / 378
labels to 18 / 204. (The 1057 is 6 above the pre-fix total: 5 because the halo labels that used to be
one `paint-order` text are now two texts each, an invisible `fill="none"` underlay over the visible
glyph, and 1 because a `<br/>` that never broke a line became a real second `<text>`. Both copies are
counted, so the denominator grows and no hit is hidden.) The banner was
fixed by narrowing its canvas 1920 -> 1280 (scale 0.4 -> 0.6) with
22px type; the in-body ones by raising the minimum to 15px (0.8x -> exactly 12.0px) and growing the
canvas HEIGHT so the re-flowed rows fit — height is free, only width sets the scale.
The wide layout the site has not switched to yet takes the 960 canvases to scale 1.0 (they fit an
1152 column), which is why the remaining 27 are still 18 figures deep under the bar there: it removes
the shrink, not the small type. A mechanical text bump was tried and rendered, not argued: at the column the 960
canvas needs ×1.25 to paint labels at their authored size (that variant is clean on the densest figure) and
×1.58 to reach 12px (that variant overflows its boxes and collides). So the bump buys back part of
the loss and the bar still needs per-figure re-authoring — a design call, listed here as an open
finding rather than quietly fixed.

Guards:
  * a ruler pass plants three SVGs (1920 / 960 / 400 viewBox) in the reader's box and requires each
    measured scale to equal min(1, column/natural). Without it, "scale 0.8" would be indistinguishable
    from a probe that reads the container and reports 1.0 for everything.
  * a classifier selftest reads three synthetic SVGs the other way: a 400px canvas whose labels must
    flag nothing (and whose font-size must come from the inherited `<g>`), a 960px canvas that
    must flag its 9.5px label and NOT its 16px one, and a stylesheet-sized 960px canvas that must
    resolve `class`/`<style>`/inline sizes through the real cascade instead of calling them all the
    13px fallback. Every real figure fails the bar, so without a planted CLEAN figure "flags
    everything" and "finds the defect" read the same.
  * the served `<img>` must still carry `max-width:100%` — if GitBook ever stops scaling, the
    premise (and every number in this file) changes, so the axis says so instead of reading clean.
  * `<main>` must measure the column on the sampled copies, and each sampled figure must paint at
    min(canvas, column) on the LIVE page.
  * the copy leg samples the pages that carry the WORST figures (severity order, not path order), and
    requires at least 2 of them to lay out in the browser. A copied page sometimes renders a shell
    because the site's client router has no route for a localhost file name; that page then falls
    back to the served-markup check and says so, but a leg that skips its way to an empty reading is
    not a leg, hence the floor.
  * the laptop leg reads the live URL in a real 1280px viewport, because a copy cannot: round 73
    found the copy lays the article out at the 768px cap while the live page mounts a 288px chapter
    sidebar and a 256px page TOC beside it and leaves the reader 608px. An axis that printed a
    "live" scale of 0.8 while the reader got 0.633 was printing the copy's number.
  * vacuity floor on the offline sweep: at least 25 authored figures.

Usage:
    python tools/checks/check_svg_legibility.py
    python tools/checks/check_svg_legibility.py --column 1152     # wide-layout what-if
    python tools/checks/check_svg_legibility.py --no-live         # offline only
"""
import argparse
import io
import json
import math
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import check_widget_visibility_live as wl                      # noqa: E402
from check_live_column import live_copy                        # noqa: E402
from check_mermaid_geometry import Server                      # noqa: E402

COLUMN_LIVE = 768           # round 62's <main>; re-asserted every run
COLUMN_LAPTOP = 608         # round 73: the same <main> measured on the live page at a 1280 window
# (288px chapter sidebar + 256px page TOC are open by default there, and they are absent from the
# copy this axis's copy leg renders). 768 is what a >=1440 reader gets; 608 is what a laptop reader
# gets. COLUMN_LIVE stays the bar because re-drawing 32 figures for 608 is a product decision - so
# the narrower reading is printed next to the verdict every run rather than quietly certified away.
# `laptop_leg` re-measures this on the live page each run and uses the fresh number; the constant is
# the fallback when Playwright is missing, and a >16px drift prints as STALE-PREMISE.
MIN_LABEL = 12.0            # px: the bar the Mermaid axis uses; body text is 16px
ROOT_FONT = 13.0            # the house SVG template sets font-size on <svg>
FIG_RE = re.compile(r'!\[[^\]]*\]\(([^)\s]+\.svg)')
CLASS_RULE_RE = re.compile(r"\.([A-Za-z0-9_-]+)\s*\{([^}]*)\}")
FS_DECL_RE = re.compile(r"font-size\s*:\s*([\d.]+)px")
SCALE_RE = re.compile(r"scale\(\s*(-?[\d.]+)(?:[\s,]+(-?[\d.]+))?")
MATRIX_RE = re.compile(r"matrix\(\s*(-?[\d.]+)[\s,]+(-?[\d.]+)[\s,]+(-?[\d.]+)[\s,]+(-?[\d.]+)")
CSS_TRANSFORM = re.compile(r'transform\s*:\s*([^;"]+)')


def strip_ns(tag):
    return tag.split("}")[-1]


def css_font_rules(root):
    """[(class, px)] from the figure's <style> blocks, in stylesheet order."""
    rules = []
    for node in root.iter():
        if strip_ns(node.tag) != "style":
            continue
        for sel, body in CLASS_RULE_RE.findall(node.text or ""):
            fs = FS_DECL_RE.search(body)
            if fs:
                rules.append((sel, float(fs.group(1))))
    return rules


def css_size(cls, rules):
    """The px a `class="a b"` element gets: same specificity, so the LAST matching rule wins."""
    px, best = None, -1
    for name in (cls or "").split():
        for i, (sel, size) in enumerate(rules):
            if sel == name and i > best:
                px, best = size, i
    return px


def transform_scale(attr):
    """The linear factor a `transform` applies to type: the SMALLEST axis of every scale()/matrix()
    in it, multiplied together. A non-uniform scale shrinks glyphs by the narrow axis, and several
    transforms compose. rotate()/translate() cost nothing; skew is not used in this book.

    Without this the axis reads a `<g transform="scale(0.95)">` card at its authored px and reports
    a label 5% larger than the reader sees -- `08-collab-patterns.svg` has four such groups.
    """
    if not attr:
        return 1.0
    k = 1.0
    for m in SCALE_RE.finditer(attr):
        sx = abs(float(m.group(1)))
        sy = abs(float(m.group(2) if m.group(2) is not None else m.group(1)))
        k *= min(sx, sy)
    for m in MATRIX_RE.finditer(attr):
        a, b, c, d = (float(m.group(i)) for i in (1, 2, 3, 4))
        k *= min(math.hypot(a, b), math.hypot(c, d))
    return k


def element_scale(node):
    """Scale an element applies to its subtree, from either place it can be written."""
    css = CSS_TRANSFORM.search(node.get("style") or "")
    return transform_scale(node.get("transform")) * transform_scale(css.group(1) if css else "")


def text_sizes(path):
    """[(effective px, character count)] for every <text>/<tspan>, with inheritance applied.

    Cascade, as a browser applies it: inline `style` beats a `<style>` class rule, which beats the
    `font-size` presentation attribute, which beats inheritance. Ignoring the class layer read
    `19-lab-react-loop-animated.svg` as 15 labels at the 13px fallback when its CSS says 15/17/18px.
    "Effective" here means *after the transforms above it in the tree* -- still canvas px, so the
    column ratio is applied on top by the caller.
    """
    root = ET.parse(path).getroot()
    rules = css_font_rules(root)
    out = []

    def walk(node, size, ts):
        for child in list(node):
            if strip_ns(child.tag) in ("style", "defs", "title", "desc"):
                continue
            raw = child.get("font-size")
            s = size
            if raw:
                m = re.match(r"([\d.]+)", raw.strip())
                if m:
                    s = float(m.group(1))
            css = css_size(child.get("class"), rules)
            if css is not None:
                s = css
            inline = FS_DECL_RE.search(child.get("style") or "")
            if inline:
                s = float(inline.group(1))
            k = ts * element_scale(child)
            if strip_ns(child.tag) in ("text", "tspan"):
                txt = "".join(child.itertext()).strip()
                if txt:
                    out.append((round(s * k, 4), len(txt)))
            walk(child, s, k)

    r = re.match(r"([\d.]+)", root.get("font-size") or str(ROOT_FONT))
    walk(root, float(r.group(1)), element_scale(root))
    return out


def viewbox(path):
    text = io.open(path, encoding="utf-8").read()
    m = re.search(r'viewBox="([\d.\-\s]+)"', text)
    if not m:
        return None, None
    v = [float(x) for x in m.group(1).split()]
    return v[2], v[3]


def declared_size(path):
    """The root tag's own width/height, or None: without them the browser calls an SVG 300px wide."""
    m = re.search(r"<svg[^>]*>", io.open(path, encoding="utf-8").read())
    if not m:
        return None
    w = re.search(r'\swidth="([\d.]+)"', m.group(0))
    h = re.search(r'\sheight="([\d.]+)"', m.group(0))
    return (float(w.group(1)), float(h.group(1))) if (w and h) else None


def page_usage():
    """{svg basename: [pages referencing it]} for body pages (14-templates quotes markup)."""
    usage = {}
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        # A `"/." in "/" + rel_dir` test looks equivalent and is not: `docs/README.md` sits in the
        # content root, whose rel_dir is ".", so that form silently dropped the homepage — and with
        # it its hero banner, the one figure on a 1920 canvas that the column shrinks hardest.
        parts = [] if rel_dir == "." else rel_dir.split("/")
        if rel_dir.startswith("14-templates") or any(p.startswith(".") for p in parts):
            continue
        for fn in filenames:
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            for m in FIG_RE.finditer(io.open(os.path.join(dirpath, fn), encoding="utf-8").read()):
                usage.setdefault(os.path.basename(m.group(1)), []).append(rel)
    return usage


def figures(column=COLUMN_LIVE):
    """Every authored SVG the body actually paints, with its canvas and its label sizes."""
    usage = page_usage()
    rows = []
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in sorted(filenames):
            if not fn.endswith(".svg") or fn not in usage:
                continue          # cover / site icons are not body figures
            path = os.path.join(dirpath, fn)
            w, h = viewbox(path)
            if not w:
                continue
            sizes = text_sizes(path)
            if not sizes:
                continue
            scale = min(1.0, column / w)
            rows.append({"asset": fn, "path": path, "vb": (w, h), "scale": scale,
                         "declared": declared_size(path),
                         "labels": len(sizes), "min_fs": min(s for s, _ in sizes),
                         "eff_min": round(min(s for s, _ in sizes) * scale, 2),
                         "below": sum(1 for s, _ in sizes if s * scale < MIN_LABEL),
                         "pages": sorted(set(usage[fn]))})
    assert len(rows) >= 25, "vacuity floor: only %d authored body figures found" % len(rows)
    # A figure that paints at all must state its own size: without width/height the browser calls the
    # SVG 300px wide, so the column stretches it to whatever it likes and every scale reading here --
    # including the live leg's -- is arithmetic on a number the file never chose.
    undeclared = [r["asset"] for r in rows if r["declared"] is None]
    assert not undeclared, \
        "%d body figure(s) declare no width/height on <svg>: %s" % (len(undeclared), undeclared)
    wrong = [(r["asset"], r["declared"], r["vb"]) for r in rows
             if r["declared"] and (abs(r["declared"][0] - r["vb"][0]) > 0.01
                                   or abs(r["declared"][1] - r["vb"][1]) > 0.01)]
    assert not wrong, "declared size disagrees with viewBox: %s" % wrong
    return rows


CLEAN = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200" width="400" height="200">'
         '<g font-size="14"><text x="10" y="40">fits the column</text>'
         '<text x="10" y="80">inherited size<tspan>and a child</tspan></text></g></svg>')
DIRTY = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" width="960" height="540">'
         '<text x="10" y="40" font-size="9.5">small label</text>'
         '<text x="10" y="90" font-size="16">big label</text></svg>')
# Same canvas, sizes set only through a stylesheet: the attribute-blind reader called all three the
# 13px fallback, so a clean figure reported as 16 defects and a 9px one would have read as 10.4px.
CSS = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" width="960" height="540">'
       '<defs><style>.t{fill:#111}.h{font-size:17px}.s{font-size:15px}.bad{font-size:9px}</style></defs>'
       '<text class="t h" x="10" y="40">heading</text>'
       '<text class="t s" x="10" y="90">body copy</text>'
       '<text class="t bad" x="10" y="140">tiny</text>'
       '<text class="t bad" x="10" y="190" font-size="16">attribute loses to class</text>'
       '<text class="t bad" x="10" y="240" style="font-size:20px">inline wins</text></svg>')
# A canvas the column never shrinks, whose only defect is a group that scales its own subtree down.
# `08-collab-patterns.svg` draws four cards this way, so this is the book's own shape, not a guess.
SCALED = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200" width="400" height="200">'
          '<g transform="translate(20,20) scale(0.7)"><text x="10" y="40" font-size="16">shrunk</text></g>'
          '<text x="10" y="120" font-size="13">untouched</text></svg>')


def classifier_selftest():
    """The other half of a control: this axis has never read a CLEAN figure, because none exists.

    Every in-body figure fails the bar, so a detector that flagged everything would look identical
    to the two real readings. Two synthetic canvases pin both directions: a 400px canvas that the
    column never shrinks (and whose size must be inherited through <g> and <tspan>) passes, and a
    960px canvas with a 9.5px label fails on exactly the small label, not the 16px one.

    The expectations below are anchored on COLUMN_LIVE, not on `--column`: they count how many
    labels a phantom trips, and that count is defined by the ratio the phantom was authored against.
    Round 73 found this out by running `--column 608`, which used to die here ("dirty.svg should flag
    1 label(s) at a 608px column, flagged 2") before printing any report - the documented wide-layout
    what-if could not be run at all.
    """
    column = COLUMN_LIVE
    with tempfile.TemporaryDirectory() as d:
        for name, text in (("clean.svg", CLEAN), ("dirty.svg", DIRTY), ("css.svg", CSS)):
            io.open(os.path.join(d, name), "w", encoding="utf-8").write(text)
        clean, dirty = os.path.join(d, "clean.svg"), os.path.join(d, "dirty.svg")
        css = os.path.join(d, "css.svg")
        assert [s for s, _ in text_sizes(clean)] == [14.0, 14.0, 14.0], \
            "inherited font-size is not applied: %s" % text_sizes(clean)
        # the class layer of the cascade, pinned both ways: a stylesheet-sized figure must not read
        # as the 13px fallback, and a class must outrank the presentation attribute it sits beside.
        assert [s for s, _ in text_sizes(css)] == [17.0, 15.0, 9.0, 9.0, 20.0], \
            "font-size from <style>/class/inline misresolved: %s" % text_sizes(css)
        # The intrinsic-size guard needs its own phantom: a copy with width/height removed must read
        # None, or the assertion would pass on a parser that never finds the attribute either.
        assert declared_size(clean) == (400.0, 200.0), "declared size misread"
        bare = os.path.join(d, "bare.svg")
        io.open(bare, "w", encoding="utf-8").write(CLEAN.replace(' width="400" height="200"', ""))
        assert declared_size(bare) is None, "a root with no width/height still read as declared"
        for path, want in ((clean, 0), (dirty, 1), (css, 2)):
            w, _ = viewbox(path)
            scale = min(1.0, column / w)
            got = sum(1 for s, _ in text_sizes(path) if s * scale < MIN_LABEL)
            assert got == want, "%s should flag %d label(s) at a %dpx column, flagged %d" \
                                % (os.path.basename(path), want, column, got)
        # `transform="scale(k)"` is a second, independent shrink the column ratio cannot see. This
        # phantom is the differential: before round 72 the axis read 16.0 and flagged nothing.
        scaled = os.path.join(d, "scaled.svg")
        io.open(scaled, "w", encoding="utf-8").write(SCALED)
        assert [s for s, _ in text_sizes(scaled)] == [11.2, 13.0], \
            "a scale(0.7) ancestor is not folded into the effective size: %s" % text_sizes(scaled)
        w, _ = viewbox(scaled)
        got = sum(1 for s, _ in text_sizes(scaled) if s * min(1.0, column / w) < MIN_LABEL)
        assert got == 1, "the scaled phantom should flag the shrunk label only, flagged %d" % got
        assert transform_scale("translate(54,140) scale(0.95) translate(-62,-144)") == 0.95, \
            "translates must not change the factor"
        assert transform_scale("scale(2) scale(0.5)") == 1.0, "composed scales must multiply"
        assert transform_scale("matrix(2,0,0,0.5,0,0)") == 0.5, "matrix read on the wrong axis"
    print("classifier selftest ok: a 400px canvas reads clean, a 960px one flags its 9.5px label only, "
          "a stylesheet-sized 960px canvas flags its two 9px labels and not its 15/17/20px ones, "
          "and a scale(0.7) ancestor takes a 16px label down to 11.2px")


def offline_report(rows, column):
    """Per-figure effective label size at `column`; the finding is a label bar, not a box bar."""
    worst = []
    for r in rows:
        scale = min(1.0, column / r["vb"][0])
        eff = r["min_fs"] * scale
        n_below = sum(1 for s, _ in text_sizes(r["path"]) if s * scale < MIN_LABEL)
        if n_below:
            worst.append((round(eff, 2), r["asset"], int(r["vb"][0]), r["min_fs"], n_below,
                          r["labels"], len(r["pages"])))
    worst.sort()
    print("authored body figures=%d  canvases=%s"
          % (len(rows), sorted({int(r["vb"][0]) for r in rows})))
    print("labels below %.0fpx at a %dpx column: %d figures, %d of %d text labels"
          % (MIN_LABEL, column, len(worst), sum(w[4] for w in worst),
             sum(r["labels"] for r in rows)))
    for eff, asset, w, fs, n, tot, pages in worst[:12]:
        print("  %-38s viewBox=%-5d fs-min=%-5s -> %5.2fpx  %3d/%3d labels  pages=%d"
              % (asset, w, fs, eff, n, tot, pages))
    return worst


PLANT = {  # name -> (viewBox width, font-size): the ruler's three known answers
    "plant-wide.svg": (1920, 12.0),
    "plant-mid.svg": (960, 12.0),
    "plant-narrow.svg": (400, 12.0),
}


def write_plants(srv):
    for name, (w, fs) in PLANT.items():
        io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d 200" width="%d" height="200">'
            '<rect width="%d" height="200" fill="#eef"/><text x="20" y="110" font-size="%s">label</text>'
            '</svg>' % (w, w, w, fs))


RULER_JS = """
<script>
(function () {
  var RID = @@RID@@, API = 'http://127.0.0.1:@@PORT@@';
  var out = [];
  // concat, not [plants, real]: the latter is one array of two arrays, and a nested element has no
  // `.file`/`.col`, so every row would post undefined keys (JSON drops them) and measure nothing.
  [].concat(@@PLANTS@@, @@REAL@@).forEach(function (p) {
    var box = document.createElement('div');
    box.style.cssText = 'max-width:' + p.col + 'px;width:100%';
    var im = document.createElement('img');
    im.style.cssText = 'max-width:100%;height:auto';   // the rule the platform serves
    im.src = '/' + p.file;
    box.appendChild(im);
    // document.body is null while the parser is still in <head>, so the fixture's <body> element
    // is written before this script and this is a belt to that brace.
    (document.body || document.documentElement).appendChild(box);
    out.push({file: p.file, col: p.col, img: im});
  });
  function send(o, id) {
    // A fatal goes out under its own id: on a copied live page GitBook's own bundle throws a
    // cross-origin "Script error." at us, and a beacon that shared the real id would win the latch,
    // get read as the report, and look exactly like a page with no figure on it.
    var mine = (id === undefined) ? RID : id;
    o.id = mine; o.done = true;
    var x = new XMLHttpRequest(); x.open('POST', API + '/report', false); x.send(JSON.stringify(o));
    if (mine !== RID) return;
    var h = new XMLHttpRequest(); h.open('GET', API + '/hold?rid=' + RID, false);
    try { h.send(); } catch (e) {}
  }
  var tries = 0;
  function poll() {
    var ready = out.every(function (o) { return o.img.naturalWidth > 0; });
    if (ready || tries++ > 24) {
      send({rows: out.map(function (o) {
        return {file: o.file, col: o.col, nat: o.img.naturalWidth,
                painted: Math.round(o.img.getBoundingClientRect().width)};
      })});
      return;
    }
    setTimeout(poll, 400);
  }
  // A silent harness is the worst failure this axis can have: "reported nothing" must never be
  // the message that hides a JS error, so the error itself is beaconed.
  window.onerror = function (msg) { try { send({fatal: String(msg).slice(0, 160)}, RID + 1000); } catch (e) {} };
  poll();
})();
</script>
"""


def fatal_of(srv, rid):
    """The probe's own JS error, if it beaconed one under the fatal id. Never a clean reading."""
    return next((p.get("fatal", "") for p in srv.reports if p.get("id") == rid + 1000), "")


def ruler(srv, rid, column):
    """The ruler must separate a scaled figure from an unscaled one, and read the column back."""
    write_plants(srv)
    plants = [{"file": f, "col": column} for f in PLANT]
    # a real authored figure goes through the same code path, so the ruler measures the book's own
    # assets and not only the plants it was handed
    real = [{"file": "real.svg", "col": column}]
    io.open(os.path.join(srv.root, "ruler-%d.html" % rid), "w", encoding="utf-8").write(
        "<!doctype html><meta charset='utf-8'><style>body{margin:0}</style>" +
        RULER_JS.replace("@@RID@@", str(rid)).replace("@@PORT@@", str(srv.port))
        .replace("@@PLANTS@@", json.dumps(plants)).replace("@@REAL@@", json.dumps(real)) +
        # The latch subresource keeps headless Chrome alive while the poll runs: `--dump-dom` exits
        # at the load event, and an async setTimeout poll has not reported by then. The server
        # releases this request when the report for `rid` lands (same latch the geometry axis uses).
        "<script src='/hold?rid=%d'></script>" % rid)
    srv.hold(rid, 60)
    proc = srv.edge("ruler-%d.html" % rid, ["--dump-dom"], height=900)
    try:
        rep = srv.wait(rid, 45, proc)
    finally:
        Server.stop(proc)
    assert rep and rep.get("rows"), "ruler pass reported nothing — the harness is broken"
    by = {r["file"]: r for r in rep["rows"]}
    assert len(by) == 4, "ruler lost rows: %s" % sorted(by)
    for f in by:
        assert by[f]["nat"], "%s reported naturalWidth=0 (the SVG did not load)" % f
    wide = by["plant-wide.svg"]
    s = lambda r: r["painted"] / r["nat"]
    # Column-relative expectations, so the same ruler is valid at 768 today and at the wide layout's
    # 1152 after the flip: every plant must land on min(1, column/natural), which is the arithmetic
    # the offline leg assumes. A box that ignored `max-width:100%` would paint the 1920 plant at
    # 1920 and break the first row; a box that always shrank would break the narrow one.
    for r in by.values():
        want = min(1.0, column / r["nat"])
        assert abs(s(r) - want) < 0.02, \
            "%s painted %.3f x natural, arithmetic says %.3f in a %dpx box" % (r["file"], s(r), want, column)
    assert wide["painted"] < wide["nat"], \
        "the 1920px plant was not scaled in a %dpx column: no plant here measures a shrink, so the " \
        "ruler could not tell a shrink from none" % column
    return {r["file"]: round(s(r), 3) for r in by.values()}


LIVE_PROBE = """
<script>
(function () {
  var RID = @@RID@@, API = 'http://127.0.0.1:@@PORT@@';
  function figs() {
    var out = [];
    document.querySelectorAll('img').forEach(function (im) {
      var r = im.getBoundingClientRect();
      if (!r.width || !/\\.svg/.test(decodeURIComponent(im.getAttribute('src') || ''))) return;
      out.push({nat: im.naturalWidth, painted: Math.round(r.width),
                style: (im.getAttribute('style') || '').slice(0, 48)});
    });
    return out;
  }
  function send(o, id) {
    var mine = (id === undefined) ? RID : id;
    o.id = mine; o.done = true;
    var x = new XMLHttpRequest(); x.open('POST', API + '/report', false); x.send(JSON.stringify(o));
    if (mine !== RID) return;
    var h = new XMLHttpRequest(); h.open('GET', API + '/hold?rid=' + RID, false);
    try { h.send(); } catch (e) {}
  }
  var tries = 0;
  function poll() {
    var f = figs();
    if ((f.length && f.every(function (x) { return x.nat > 0; })) || tries++ > 24) {
      var m = document.querySelector('main');
      send({main: m ? Math.round(m.getBoundingClientRect().width) : null, figs: f,
            imgs: document.querySelectorAll('img').length});
      return;
    }
    setTimeout(poll, 500);
  }
  // Same reason as the ruler: "reported nothing" must never be the message hiding a JS error.
  window.onerror = function (msg) { try { send({fatal: String(msg).slice(0, 160)}, RID + 1000); } catch (e) {} };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', poll);
  else poll();
})();
</script>
"""


def served_figure_check(rel, html, rows, column):
    """The premise, read off the live markup, for a page whose copy will not hydrate.

    What the browser leg proves is the platform's rule: the figure is an `<img>` carrying
    `max-width:100%`, so a canvas wider than the column is scaled and never given a scroller. That
    much is visible in the served HTML. Where GitBook also spells the paint width into the image API
    (`~gitbook/image?...&width=W`), W is the platform declaring the CSS width it paints at, and it
    has to be min(column, natural).
    """
    found = 0
    for r in rows:
        if rel not in r["pages"]:
            continue
        tags = [t for t in re.findall(r"<img\b[^>]*>", html) if r["asset"] in t]
        assert tags, "the live page %s serves no <img> for %s" % (rel, r["asset"])
        for tag in tags:
            assert "max-width:100%" in tag, \
                "the served <img> for %s on %s no longer carries max-width:100%%: the scaling " \
                "premise of this file is gone" % (r["asset"], rel)
            m = re.search(r"[&?]width=(\d+)", tag)
            if m:
                want = min(column, int(r["vb"][0]))
                assert int(m.group(1)) == want, \
                    "%s is asked for at width=%s, not min(%d, %d)=%s" % (r["asset"], m.group(1),
                                                                        column, int(r["vb"][0]), want)
        found += 1
    assert found, "no figure of this axis's list is on %s" % rel
    print("  served %s: %d figures, each an <img> with max-width:100%%" % (rel, found))


def live_url(rel, index):
    text = io.open(os.path.join(DOCS, rel.replace("/", os.sep)), encoding="utf-8").read()
    m = re.search(r"^# (.+)$", text, flags=re.M)
    assert m, "%s has no H1 to look the published title up by" % rel
    url = index.get(wl.norm(m.group(1).strip())) or ""
    assert url, "no live URL for %s" % rel
    return url[:-3] if url.endswith(".md") else url


def worst_pages(rows, count):
    """The pages that carry the worst figures, in severity order, with their live URLs.

    Severity order, not path order: a sorted() over paths would let `00-index/...` crowd out the
    homepage that carries the 5.2px label.
    """
    index, ambiguous = wl.page_index(wl.llms_entries())
    assert not ambiguous, "ambiguous published titles: %s" % sorted(ambiguous)
    out, seen_pages = [], set()
    for r in sorted(rows, key=lambda r: r["eff_min"]):
        for p in r["pages"]:
            if p not in seen_pages:
                seen_pages.add(p)
                out.append((p, live_url(p, index)))
        if len(out) >= count:
            break
    return out[:count]


def live_leg(srv, rows, column, count=4):
    """Measure the platform's scaling on a copy of the reader's page, on the worst figures' pages.

    Round 73 names this leg for what it is: the HTML is fetched from the live site, but it is laid
    out as a local copy, and a copy has no navigation panels beside the article (the site's client
    router cannot resolve a localhost file name, so the furniture never mounts). So the column this
    leg sees is the copy's 768px cap, not the 608px a laptop reader is given - `laptop_leg` below is
    the leg that reads the reader's own page.
    """
    pages = worst_pages(rows, count)
    seen = []
    measured = 0                       # pages the browser leg actually laid out
    for i, (rel, url) in enumerate(pages):
        # The ruler reports under rid 1 and `wait` returns the first report that matches an id, so
        # reusing 1 here would read back the ruler's rows as a page with no figure on it.
        rid = 10 + i
        name = "svg-%d.html" % rid
        html = wl.fetch(url)
        io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(
            live_copy(html, wl.SITE,
                      LIVE_PROBE.replace("@@RID@@", str(rid)).replace("@@PORT@@", str(srv.port))))
        srv.hold(rid, 120)
        # No `--dump-dom` here (unlike the ruler): that flag exits at the load event, and this page's
        # figure is laid out by hydration afterwards, so the async poll would never report. The
        # synchronous `/hold` fetch inside send() is what keeps this process alive instead.
        proc = srv.edge(name, [], height=1600)
        try:
            rep = srv.wait(rid, 60, proc)
        finally:
            Server.stop(proc)
        if rep and rep.get("main") is None:
            # Which copied page renders a shell varies run to run (the content root hydrated once and
            # `mcp.md` did not, and the other way round): the site's client router has no route for a
            # localhost file name, so hydration is a race this harness does not control. That is a
            # harness limit, not a page defect, so the same premise is read off the served markup —
            # and it is said out loud, not skipped.
            print("  copy leg: %s's copy does not hydrate (no <main>), reading the served markup" % rel)
            served_figure_check(rel, html, rows, column)
            continue
        assert rep and rep.get("figs"), \
            "copy leg read no SVG figure on %s (imgs on page: %s; probe JS error: %r)" \
            % (rel, rep and rep.get("imgs"), fatal_of(srv, rid))
        measured += 1
        assert rep["main"] == column, \
            "<main> measures %s on the copy of %s, not %d — the column this axis is about changed" \
            % (rep["main"], rel, column)
        for f in rep["figs"]:
            assert "max-width:100%" in f["style"], \
                "the served <img> no longer carries max-width:100%% (%s on %s): the scaling " \
                "premise of this file is gone" % (f["style"], rel)
            scale = f["painted"] / f["nat"]
            assert abs(scale - min(1.0, column / f["nat"])) < 0.02, \
                "figure painted %.3f x natural, arithmetic says %.3f (%s on %s)" \
                % (scale, min(1.0, column / f["nat"]), f, rel)
            seen.append((f["nat"], scale))
        print("  copy %s: %d svg figures, scales %s"
              % (rel.split("/")[0], len(rep["figs"]),
                 sorted({round(x[1], 3) for x in seen[-len(rep["figs"]):]})))
    scaled = [x for x in seen if x[1] < 0.99]
    assert measured >= 2, \
        "only %d of the sampled pages laid out in the browser — a leg that skips its way to an " \
        "empty reading is not a leg" % measured
    if any(nat > column for nat, _ in seen):
        assert scaled, \
            "a figure wider than the %dpx column painted without shrinking (%s): the platform's " \
            "rule changed and this file's arithmetic is now wrong" % (column, seen)
    else:
        # No figure is wider than the column, so nothing can shrink here. Say it out loud rather
        # than letting a quiet `scaled=[]` read as a pass: at the wide layout this leg stops
        # discriminating, and only the offline label ratio still carries the finding.
        print("  copy leg: no figure exceeds the %dpx column, so no shrink to measure here" % column)
    return [s for _, s in seen]


LAPTOP_VW = 1280          # the window whose reader gets the narrowest desktop column (round 73)

# Read off the LIVE url, never a copy: a copy loses the 288px chapter sidebar and the 256px page TOC
# that mount beside the article on the real page, and those are exactly what squeezes the column.
# Controls are planted AFTER the reading, and figures are identified by the asset name inside the
# served src (GitBook rewrites it into a `~gitbook/image?...&width=` URL, so an extension match would
# see nothing) - see check_live_column's HYDRATED_PROBE for why the order is load-bearing.
LAPTOP_PROBE = r"""
() => {
  const w = el => Math.round(el.getBoundingClientRect().width);
  const main = document.querySelector('main');
  if (!main) return null;
  const figs = [...main.querySelectorAll('img')].map(i => ({
      src: i.getAttribute('src') || '', nat: i.naturalWidth, painted: w(i)}))
    .filter(f => f.painted > 0);
  const phantom = !!document.getElementById('r73-no-such-element');
  const ctl = {};
  for (const px of [200, 960]) {
    const d = document.createElement('div');
    d.style.cssText = 'width:' + px + 'px;height:6px';
    main.appendChild(d);
    ctl['plant-' + px] = w(d);
    d.remove();
  }
  return {vw: innerWidth, main: w(main), figs: figs, ctl: ctl, phantom: phantom};
}
"""


def laptop_leg(rows, count=3):
    """Measure the reader's actual column and figure scale on the live page, at a laptop window.

    Returns (column, note). This is the leg that turns `COLUMN_LAPTOP` from a remembered number into
    one this run produced: it reads `<main>` and each figure's painted width off the live URL, and
    asserts the figures are column-bound there (painted == min(authored canvas, main)) so the laptop
    reading below is arithmetic on a measured scale rather than an assumed one.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "playwright is not installed, so the live laptop column could not be measured"
    pages = worst_pages(rows, count)
    cols, scales = [], []
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        try:
            for rel, url in pages:
                ctx = br.new_context(viewport={"width": LAPTOP_VW, "height": 900})
                pg = ctx.new_page()
                try:
                    pg.goto(url, wait_until="networkidle", timeout=90000)
                except Exception as exc:
                    print("  laptop leg: %s failed to load (%s)" % (rel, str(exc)[:60]))
                    ctx.close()
                    continue
                pg.wait_for_timeout(2500)      # the panels mount after hydration
                rep = pg.evaluate(LAPTOP_PROBE)
                ctx.close()
                if not rep:
                    print("  laptop leg: %s laid out no <main>" % rel)
                    continue
                assert abs(rep["vw"] - LAPTOP_VW) <= 3, \
                    "asked for vw=%d, the live page reported %d" % (LAPTOP_VW, rep["vw"])
                assert abs(rep["ctl"]["plant-200"] - 200) <= 2 and \
                    abs(rep["ctl"]["plant-960"] - 960) <= 2, \
                    "the ruler clamps on the live page: planted 200/960 boxes read %s" % rep["ctl"]
                assert not rep["phantom"], "a phantom element id matched on the live page"
                cols.append(rep["main"])
                hit = 0
                for r in rows:
                    got = [f for f in rep["figs"] if r["asset"] in f["src"]]
                    for f in got:
                        want = min(float(r["vb"][0]), rep["main"])
                        assert abs(f["painted"] - want) <= 2, \
                            "%s paints %dpx on the live page, not min(canvas %d, column %d)=%d" \
                            % (r["asset"], f["painted"], float(r["vb"][0]), rep["main"], want)
                        scales.append(f["painted"] / float(r["vb"][0]))
                        hit += 1
                print("  laptop %s: <main>=%dpx, %d of this page's figures measured (%s)"
                      % (rel.split("/")[0], rep["main"], hit,
                         ", ".join("%.3f" % s for s in scales[-hit:]) if hit else "none sampled"))
        finally:
            br.close()
    if not cols:
        return None, "no live page laid out for the laptop leg"
    return min(cols), None



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--column", type=int, default=COLUMN_LIVE)
    ap.add_argument("--no-live", action="store_true")
    args = ap.parse_args()

    rows = figures(args.column)
    worst = offline_report(rows, args.column)
    classifier_selftest()

    dummy = os.path.join(tempfile.gettempdir(), "svg-none.js")
    io.open(dummy, "w", encoding="utf-8").write("// this axis loads no bundle\n")
    srv = Server(js_path=dummy)
    shutil_copy_assets(srv, rows)
    scales = ruler(srv, 1, args.column)
    print("ruler ok: 1920/960/400 canvases measure %s / %s / %s in a %dpx box"
          % (scales["plant-wide.svg"], scales["plant-mid.svg"], scales["plant-narrow.svg"],
             args.column))
    if not args.no_live:
        live_leg(srv, rows, args.column)

    # The laptop reading: the same authored figures at the column a 1280-window reader is given once
    # the chapter sidebar and the page TOC mount beside the article. Reported, never counted - the
    # bar this axis certifies against stays COLUMN_LIVE because closing the gap means re-drawing 32
    # figures or switching the space to the wide layout, and neither is a ruler's call.
    if args.column == COLUMN_LIVE:
        col, note, measured_by = COLUMN_LAPTOP, (
            None if not args.no_live else
            "--no-live was passed, so the live laptop column was not re-measured"), "assumed"
        if not args.no_live:
            col_live, note = laptop_leg(rows)
            if col_live:
                col, measured_by = col_live, "measured on the live page this run"
        laptop = figures(col)
        n_fig = sum(1 for r in laptop if r["below"])
        n_lab = sum(r["below"] for r in laptop)
        print("laptop reading (the same figures at the %dpx column a 1280-window reader gets, %s):"
              " %d figures / %d of %d labels below the %.0fpx bar"
              % (col, measured_by, n_fig, n_lab, sum(r["labels"] for r in laptop), MIN_LABEL))
        print("  not counted as findings: re-drawing the book's figures for %dpx is a content"
              " decision, see round 73's log entry" % col)
        if note:
            print("  laptop leg skipped: %s (the %d above is the remembered reading)" % (note, col))
        elif abs(col - COLUMN_LAPTOP) > 16:
            print("  STALE-PREMISE: this file records the laptop column as %dpx but the live page now"
                  " gives %dpx - the reading above used the live number, the constant did not"
                  % (COLUMN_LAPTOP, col))

    print("\n-- verdict (column %dpx, label bar %.0fpx) --" % (args.column, MIN_LABEL))
    print("  figures with a sub-bar label=%d  labels=%d of %d"
          % (len(worst), sum(w[4] for w in worst), sum(r["labels"] for r in rows)))
    print("  pages touched=%d" % len({p for r in rows for p in r["pages"]}))
    return 1 if worst else 0


def shutil_copy_assets(srv, rows):
    """The ruler also measures one of the book's own figures, so it has to be reachable."""
    import shutil
    worst = sorted(rows, key=lambda r: r["eff_min"])[0]
    shutil.copyfile(worst["path"], os.path.join(srv.root, "real.svg"))


if __name__ == "__main__":
    sys.exit(main())
