# -*- coding: utf-8 -*-
"""Measured SVG label geometry: does a label fit the box it was written into?

Why this file exists (round 66). `check_svg_legibility.py` answers one question about a hand-drawn
figure — how big does the type reach the reader — and it is answered from the source, offline. It
cannot see the other failure mode of the same 32 figures: a label whose glyphs run past the card they
belong to, two labels printed on top of each other, a connector routed straight through a heading.
Those are geometry, and geometry needs the layout engine.

The first attempt at this axis estimated glyph widths from character classes
(`.tmp-projects/r66_fit_probe.py`) and was thrown away: on the current tree it reported 563
"collisions" on a figure that renders clean, because it ignored ancestor `transform` and
`text-anchor`. An instrument that fails that check cannot call anything a defect. This one asks
Chromium what it actually painted: every `<text>` is measured with `getBBox()` (tight glyph bounds,
no stroke) and mapped through `getScreenCTM()` into the figure's own viewBox units, so the reading is
exact, transform-aware and anchor-aware. Boxes come from `<rect>`, strokes from stroked
fill:none `<line>/<path>/<polyline>` sampled along their real length.

Judgements (all in viewBox units, `PAD` px of slack before anything counts):
  * BURST      — a label's edge is > PAD outside the container it belongs to.
  * COLLIDE    — two labels with different strings overlap by > PAD in x and > 45% of the shorter
                 glyph height in y. Two-layer halos (identical strings, same place, the portable
                 replacement for the `paint-order` the GitBook sanitizer strips) are skipped.
  * OFFCANVAS  — a label leaves the viewBox.
  * STRIKE     — a connector passes through a label's glyph box (inside it by > PAD on both sides).
                 Two exemptions, both real painting: a haloed label (white underlay stroke, the
                 portable replacement for the `paint-order` GitBook strips), and a label sitting on
                 an opaque pill `<rect>` painted after the wire and before the text — paint order is
                 measured, not assumed. A label the author put ON a lane on purpose (a gate marker
                 sitting on the road it blocks) is exempted by naming it in the source:
                     <!-- fit:strike-ok  ✕ -->
  * CLEARANCE  — reported, never fatal: the label ends within PAD of its container's edge. Round 66's
                 baseline was mostly this kind of noise, which is why the fatal bar is "outside the
                 box", not "close to the box".

Guards:
  * planted counterexamples: one dirty plant per fatal kind must produce exactly that kind, and a
    clean plant built from the remedies this round actually used (two-line split, snake layout, halo
    pair over a curve, pill label over a wire, symbol centred on the lane it blocks) must produce
    nothing. Without the clean plant "flags everything" and "finds the defect" read the same.
  * vacuity floors (whole-tree sweep only): at least 25 figures measured and at least 400 labels,
    and a figure that fails to measure is an error rather than a skipped line.

Readings. Round 66 baseline, 32 in-body figures / 1011 measured labels: 8 fatal problems over 4
figures — 17-vla-loop 3 (two connectors and a feedback arc printed straight through labels),
16-sandbox-layers 2 (the left return gutter through the band heading; the gate ✕ on its own lane,
which is intent and is now declared), 05-mcp-architecture 2 (both false positives, killed by the
paint-order rule above), 06-rag-pipeline 1 (the dashed return drop through a retrieval caption). The
estimated probe this file replaced reported 563 "collisions" on this same tree.

Usage:
    python tools/checks/check_svg_fit.py                      # every in-body figure
    python tools/checks/check_svg_fit.py 08-multi-agent.svg   # named figures only
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
ASSETS = os.path.join(DOCS, ".gitbook", "assets")
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import check_svg_legibility as leg                                      # noqa: E402
from check_mermaid_geometry import (browser, headless_flags)                  # noqa: E402

COLUMN = 768          # the reader column `<main>` reports; host width, see the note below
PAD = 2.0             # viewBox px of slack before an edge counts as outside
MIN_FIGURES = 25
MIN_TEXTS = 400
STRIKE_OK_RE = re.compile(r"<!--\s*fit:strike-ok\s+(.*?)-->")
FATAL = ("BURST", "COLLIDE", "OFFCANVAS", "STRIKE")

# The host is 768 wide because that is where the reader sees the figure, but every box is mapped back
# into viewBox units, so the numbers below are authored units and the scale cancels out.
PAGE = """<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;background:#fff}#host{width:%(column)dpx}</style>
<div id="host">%(svg)s</div>
<script>
(function () {
  var svg = document.querySelector('#host svg');
  if (!svg) { report({error:'no svg parsed'}); return; }
  var vb = (svg.getAttribute('viewBox') || '').trim().split(/\\s+/).map(Number);
  var rootInv = svg.getScreenCTM().inverse();
  function boxOf(el) {                       // getBBox -> this element's screen CTM -> viewBox units
    var b;
    try { b = el.getBBox(); } catch (e) { return null; }
    if (!b.width && !b.height) return null;
    var m = el.getScreenCTM();
    if (!m) return null;
    var p1 = new DOMPoint(b.x, b.y).matrixTransform(m).matrixTransform(rootInv);
    var p2 = new DOMPoint(b.x + b.width, b.y + b.height).matrixTransform(m).matrixTransform(rootInv);
    return [Math.min(p1.x, p2.x), Math.min(p1.y, p2.y), Math.max(p1.x, p2.x), Math.max(p1.y, p2.y)];
  }
  function ptsOf(el) {                       // sample a real stroke along its own length
    var L = 0;
    try { L = el.getTotalLength(); } catch (e) { return null; }
    if (!L || !isFinite(L)) return null;
    var n = Math.max(8, Math.min(700, Math.ceil(L / 2)));
    var m = el.getScreenCTM(), out = [];
    for (var k = 0; k <= n; k++) {
      var p = el.getPointAtLength(L * k / n).matrixTransform(m).matrixTransform(rootInv);
      out.push([p.x, p.y]);
    }
    return out;
  }
  function light(rgb) {                      // "#fff" / "rgb(255,255,255)" -> a halo colour?
    var t = (rgb || '').replace(/\\s+/g, ''), d = null;
    if (t.charAt(0) === '#') d = [1, t];
    else { var mm = t.match(/rgb\\(([^)]*)\\)/); if (mm) d = [2, mm[1]]; }
    if (!d) return false;
    var c;
    if (d[0] === 1) {
      var h = d[1].slice(1);
      if (h.length === 3) h = h.charAt(0)+h.charAt(0)+h.charAt(1)+h.charAt(1)+h.charAt(2)+h.charAt(2);
      c = [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
    } else c = d[1].split(',').slice(0,3).map(Number);
    return c.length === 3 && c[0] >= 200 && c[1] >= 200 && c[2] >= 200;
  }
  var out = {viewBox: vb, texts: [], rects: [], strokes: []};
  var nodes = svg.querySelectorAll('*');
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i], t = el.tagName.toLowerCase(), cs = getComputedStyle(el);
    if (t === 'text' || t === 'tspan') {
      if (t === 'tspan' && el.parentNode && el.parentNode.tagName.toLowerCase() === 'text') continue;
      var tb = boxOf(el);
      if (tb) out.texts.push({s: (el.textContent || '').replace(/\\s+/g, ' ').trim(), b: tb, i: i,
                              fs: parseFloat(cs.fontSize) || 0,
                              halo: (light(cs.stroke) && parseFloat(cs.strokeWidth) >= 2) ? 1 : 0});
    } else if (t === 'rect') {
      var rb = boxOf(el);
      var fo = (parseFloat(cs.fillOpacity) || 0) * (parseFloat(cs.opacity) || 1);
      if (rb && (rb[2] - rb[0]) > 1 && (rb[3] - rb[1]) > 1)
        out.rects.push({b: rb, i: i, plate: (cs.fill !== 'none' && fo >= 0.9) ? 1 : 0});
    } else if (t === 'line' || t === 'path' || t === 'polyline') {
      var sw = parseFloat(cs.strokeWidth) || 0;
      if (cs.stroke === 'none' || cs.fill !== 'none' || sw <= 0) continue;
      var sp = ptsOf(el);
      if (sp) out.strokes.push({p: sp, w: sw, i: i});
    }
  }
  report(out);
  function report(o) {
    var pre = document.createElement('pre');
    pre.textContent = '@@JSON@@' + JSON.stringify(o) + '@@END@@';
    document.body.appendChild(pre);
  }
})();
</script>
"""


def measure(svg_text, column=COLUMN):
    """Return (data, None) or (None, reason). One Edge launch per figure."""
    # Edge keeps a WebView2 log handle inside --user-data-dir after the process is gone, and on
    # Windows that makes the teardown raise mid-sweep: the axis died at figure 12 of 32 with a
    # PermissionError and no verdict, which reads like a content failure. Losing a temp directory
    # is cheap; losing the run is not.
    with tempfile.TemporaryDirectory(prefix="svgfit", ignore_cleanup_errors=True) as tmp:
        io.open(os.path.join(tmp, "page.html"), "w", encoding="utf-8").write(
            PAGE % {"svg": svg_text, "column": column})
        exe = browser()
        cmd = [exe] + headless_flags(exe) + [
            "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--user-data-dir=" + os.path.join(tmp, "p"), "--window-size=900,1400",
            "--virtual-time-budget=4000", "--dump-dom",
            "file:///" + os.path.join(tmp, "page.html").replace("\\", "/")]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=240)
        # --dump-dom serialises the page source too, so the sentinel appears twice: once inside the
        # <script> text, once in the node the script appended. The appended one is the last.
        dom = p.stdout.decode("utf-8", "replace")
        at = dom.rfind("@@JSON@@")
        end = dom.find("@@END@@", at + 1) if at >= 0 else -1
        if at < 0 or end < 0:
            return None, "no report (rc=%d)" % p.returncode
        data = json.loads(_html.unescape(dom[at + len("@@JSON@@"):end]))
        if data.get("error"):
            return None, data["error"]
        if len(data.get("viewBox") or []) != 4 or not data["viewBox"][2]:
            return None, "no usable viewBox"
        return data, None


def containers(rects, bx):
    # The label's left edge must start INSIDE the box with real margin. A label that only touches a
    # border is not that box's text: ⑤ 全绿？ in 12-coding-agent-loop sits flush on the work-area
    # card's right edge (x0 == box right) and a +-1 tolerance invented a 56px "burst" for it.
    hits = [r for r in rects
            if r["b"][0] + 3 <= bx[0] <= r["b"][2] - 3
            and r["b"][1] - 1 <= (bx[1] + bx[3]) / 2 <= r["b"][3] + 1]
    return sorted(hits, key=lambda r: (r["b"][2] - r["b"][0]) * (r["b"][3] - r["b"][1]))


def inside(b, p, pad):
    return b[0] + pad < p[0] < b[2] - pad and b[1] + pad < p[1] < b[3] - pad


def plated(rects, stroke, text, p):
    """Is the crossing point hidden by an opaque plate painted between the wire and the label?

    The house remedy for "a connector has to run under a word" is a pill: an opaque `<rect>` drawn
    after the connector and before the `<text>`. `05-mcp-architecture` does exactly that for both of
    its transport labels, and the wire is genuinely invisible under them. Without paint order the
    axis calls those two a defect; with it, a wire that really does cross live glyphs still fails
    (`plant-strike` has no plate and must stay caught).
    """
    return any(r["plate"] and stroke["i"] < r["i"] < text["i"] and inside(r["b"], p, 1.0)
               for r in rects)


def classify(data, source=""):
    """-> (fatal problems, clearance notes, n_texts, n_rects, n_strokes)."""
    cw, ch = data["viewBox"][2], data["viewBox"][3]
    ok_strings = set()
    for m in STRIKE_OK_RE.finditer(source):
        ok_strings |= {s.strip() for s in re.split(r"[,，、\s]+", m.group(1)) if s.strip()}
    problems, notes = [], []
    texts = [t for t in data["texts"] if t["s"]]
    haloed = {t["s"] for t in texts if t.get("halo")}

    for t in texts:
        b = t["b"]
        cs = containers(data["rects"], b)
        if cs:
            r = cs[0]["b"]
            over = {"right": b[2] - r[2], "left": r[0] - b[0],
                    "bottom": b[3] - r[3], "top": r[1] - b[1]}
            side, mag = max(over.items(), key=lambda kv: kv[1])
            if mag > PAD:
                problems.append(("BURST", round(mag, 1),
                                 "%s   [%s by %.0fpx | box x=%.0f w=%.0f y=%.0f h=%.0f | text x0=%.0f "
                                 "x1=%.0f y=%.0f..%.0f]"
                                 % (t["s"][:36], side, mag, r[0], r[2] - r[0], r[1], r[3] - r[1],
                                    b[0], b[2], b[1], b[3])))
            elif min(abs(over["right"]), abs(over["left"])) <= PAD:
                notes.append("CLEARANCE %s: %s" % (round(over["right"], 1), t["s"][:30]))
        if b[2] > cw + PAD or b[0] < -PAD or b[3] > ch + PAD or b[1] < -PAD:
            problems.append(("OFFCANVAS", round(max(b[2] - cw, -b[0], b[3] - ch, -b[1]), 1),
                             t["s"][:40]))

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, c = texts[i], texts[j]
            if a["s"] == c["s"]:      # two-layer halo: same string, same place, by design
                continue
            ab, cb = a["b"], c["b"]
            ox = min(ab[2], cb[2]) - max(ab[0], cb[0])
            oy = min(ab[3], cb[3]) - max(ab[1], cb[1])
            if ox > PAD and oy > 0.45 * min(ab[3] - ab[1], cb[3] - cb[1]):
                problems.append(("COLLIDE", round(ox, 1), a["s"][:22] + " / " + c["s"][:22]))

    for t in texts:
        if t.get("halo") or t["s"] in haloed or t["s"] in ok_strings:
            continue
        for st in data["strokes"]:
            hit = next((p for p in st["p"] if inside(t["b"], p, PAD)
                        and not plated(data["rects"], st, t, p)), None)
            if hit:
                problems.append(("STRIKE", round(min(t["b"][3] - t["b"][1],
                                                     t["b"][2] - t["b"][0]) / 2.0, 1),
                                 "%s   [stroke through glyph box x=%.0f..%.0f y=%.0f..%.0f]"
                                 % (t["s"][:36], t["b"][0], t["b"][2], t["b"][1], t["b"][3])))
                break
    return problems, notes, len(texts), len(data["rects"]), len(data["strokes"])


# ---------------------------------------------------------------- plants
PLANT_BURST = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 120" width="300" height="120"
 font-size="17"><rect width="300" height="120" fill="#fff"/>
 <rect x="20" y="20" width="120" height="60" fill="#e0e7ff" stroke="#6366f1"/>
 <text x="30" y="55">这一行标签明显超出了卡片右边界</text></svg>"""

PLANT_COLLIDE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 120" width="300" height="120"
 font-size="17"><rect width="300" height="120" fill="#fff"/>
 <text x="20" y="55">左侧标签文字</text><text x="34" y="57">右侧标签文字</text></svg>"""

PLANT_STRIKE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 120" width="300" height="120"
 font-size="17"><rect width="300" height="120" fill="#fff"/>
 <text x="20" y="60">连接线从字上穿过</text>
 <path d="M10 52 H280" fill="none" stroke="#7c3aed" stroke-width="2"/></svg>"""

PLANT_OFFCANVAS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 120" width="300" height="120"
 font-size="17"><rect width="300" height="120" fill="#fff"/>
 <text x="215" y="60">这一段超出了画布右边界</text></svg>"""

# Every remedy this round actually used, in one figure: a two-line split that fits its card, a halo
# pair over a curve, a symbol centred on the lane it blocks, and a snake layout.
PLANT_CLEAN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300"
 font-size="15"><rect width="300" height="300" fill="#fff"/>
 <!-- fit:strike-ok ✕ -->
 <rect x="16" y="16" width="180" height="70" rx="8" fill="#e0e7ff" stroke="#6366f1"/>
 <text x="28" y="44">分成两行的第一行</text>
 <text x="28" y="68">分成两行的第二行</text>
 <path d="M16 150 H284 V230 H120" fill="none" stroke="#7c3aed" stroke-width="2"/>
 <text x="150" y="200" fill="none" stroke="#ffffff" stroke-width="5" font-weight="700">回流</text>
 <text x="150" y="200" fill="#0f172a" font-weight="700">回流</text>
 <path d="M290 30 V120" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="5 4"/>
 <text x="281" y="80" fill="#dc2626" font-size="18" font-weight="700">✕</text>
 <path d="M200 265 H284" fill="none" stroke="#0d9488" stroke-width="2.4"/>
 <rect x="206" y="250" width="72" height="26" rx="13" fill="#ffffff" stroke="#0d9488" stroke-width="1.4"/>
 <text x="214" y="268" fill="#0f766e" font-weight="700">胶囊标签</text></svg>"""

PLANTS = [("plant-burst.svg", PLANT_BURST, {"BURST"}),
          ("plant-collide.svg", PLANT_COLLIDE, {"COLLIDE"}),
          ("plant-strike.svg", PLANT_STRIKE, {"STRIKE"}),
          ("plant-offcanvas.svg", PLANT_OFFCANVAS, {"OFFCANVAS"}),
          ("plant-clean.svg", PLANT_CLEAN, set())]


def run_plants():
    for name, svg, want in PLANTS:
        data, err = measure(svg)
        assert not err, "%s failed to measure: %s" % (name, err)
        probs, notes, nt, _nr, _ns = classify(data, svg)
        kinds = {k for k, _m, _s in probs}
        # A dirty plant may legitimately trip a second kind (a label that leaves the canvas is also
        # outside the full-canvas background rect, which is a container like any other), so the
        # assertion is "its own kind is there". The clean plant is the one that must stay exact:
        # without it "flags everything" and "finds the defect" read the same.
        assert want <= kinds if want else not kinds, \
            "%s should flag %s, flagged %s (%s)" \
            % (name, sorted(want) or "nothing", sorted(kinds),
               "; ".join("%s %s" % (k, s[:30]) for k, _m, s in probs))
        assert nt >= 1, "%s measured no text at all" % name
    print("plants ok: 4 planted defects each caught by their own kind, 1 clean remedy figure "
          "(two-line split + halo pair + pill label over a wire + symbol on its lane + snake) flags 0")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="asset file names; default: every in-body figure")
    ap.add_argument("--column", type=int, default=COLUMN)
    ap.add_argument("--no-plants", action="store_true")
    ap.add_argument("--show-clearance", action="store_true")
    args = ap.parse_args()

    if not args.no_plants:
        run_plants()

    names = args.names
    if not names:
        usage = leg.page_usage()
        names = [n for n in sorted(usage) if n.endswith(".svg")
                 and os.path.isfile(os.path.join(ASSETS, n))]
    total, clear, per_figure = 0, 0, []
    for name in names:
        source = io.open(os.path.join(ASSETS, name), encoding="utf-8").read()
        data, err = measure(source, args.column)
        if err:
            print("%-42s MEASURE-FAIL %s" % (name, err))
            return 2
        probs, notes, nt, nr, ns = classify(data, source)
        total += len(probs)
        clear += len(notes)
        per_figure.append((len(probs), name, nt, nr, ns, data["viewBox"]))
        print("%-42s viewBox=%gx%g texts=%3d rects=%3d strokes=%3d problems=%d"
              % (name, data["viewBox"][2], data["viewBox"][3], nt, nr, ns, len(probs)))
        for kind, mag, s in sorted(probs, key=lambda p: -p[1])[:8]:
            print("      %-10s %-7s %s" % (kind, mag, s))
        if args.show_clearance:
            for n in notes:
                print("      %s" % n)

    texts = sum(p[2] for p in per_figure)
    if not args.names:      # the floors guard the whole-tree sweep, not a named spot check
        assert len(per_figure) >= MIN_FIGURES, \
            "only %d figures measured (floor %d) — the sweep is vacuous" % (len(per_figure), MIN_FIGURES)
        assert texts >= MIN_TEXTS, \
            "only %d labels measured (floor %d) — the sweep is vacuous" % (texts, MIN_TEXTS)

    dirty = sorted(per_figure, reverse=True)
    print("\n-- verdict (column %dpx, PAD %.0fpx, %d figures, %d labels) --"
          % (args.column, PAD, len(per_figure), texts))
    for n, name, nt, _nr, _ns, vb in dirty:
        if n:
            print("  %-42s %d problems" % (name, n))
    print("  figures with a fatal problem=%d of %d   total=%d   clearance notes=%d"
          % (sum(1 for p in dirty if p[0]), len(per_figure), total, clear))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
