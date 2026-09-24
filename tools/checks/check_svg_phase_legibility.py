# -*- coding: utf-8 -*-
"""Animation-phase legibility: is a label readable in EVERY frame, not just the frozen one?

Why this file exists (round 69). Every earlier SVG axis looks at one instant: the size axis reads
authored px against the reader's column and never renders; the geometry axis measures label boxes in
a frozen frame. 14 of the 32 in-body figures animate (100 `<animate>` nodes), and an animation has
ways to be unreadable that a still frame cannot show:

  * a bar that grows (`<animate attributeName="width" values="0;300;300">`) underneath white text —
    until the bar arrives, that text is white on white;
  * a cover rect that fades in (`opacity 0;0;1;1`) over a label — the label is buried for part of the
    cycle;
  * a panel whose `opacity` / `fill-opacity` is animated — the reader's background arrives late.

Freezing a phase in this headless Edge was measured, not assumed (`.tmp-projects/r69_smil_driver.py`):
`pauseAnimations()` + `setCurrentTime(t)` stepped by `setTimeout` **under `--virtual-time-budget`**
lands exactly on the authored ramp (a 0;100 over 2s bar reads 50 at t=1.0, 95 at t=1.9). Without the
virtual-time flag the page beacons nothing at all, and a `requestAnimationFrame`-stepped loop runs
exactly one frame of a 25-phase sweep.

The colour question is answered by compositing the stack the reader actually gets, bottom-up: the
page's own white, then every painted surface under the label in paint order (each with its own alpha
and its ancestors' `opacity` accumulated — a translucent panel is a real partial layer, so it is
composited and not skipped), then the label's ink over that. A surface filled by an axis-aligned OR
diagonal `objectBoundingBox` linear gradient is resolved AT THE PROBE POINT: the sweep is projected
onto the surface's own box, bracketed by its two surrounding stops, and stop colours and alphas are
lerped and composited — so a label standing on the middle of a light-to-dark pill is priced against
the middle, which is the colour the reader actually gets. Everything else the reader may sit on — a
radial wash, a pattern tile, a `userSpaceOnUse` server — is resolved to its own stops/tiles and priced
against the candidate **farthest in luminance from the ink**, i.e. the most favourable reading the
label could get: a DARK verdict under such a server can never be the server's fault, and those points
are counted `approx` and printed per figure and by kind. The cost of that bias is documented in
"Honest limits" below, and the reason the fallback is a fallback rather than an invention is planted
four ways (`PLANT_GRAD_MID` and `PLANT_GRAD_DIAG` are measured, `PLANT_GRAD_RADIAL` and
`PLANT_GRAD_USERSPACE` refuse to be and say so).
A surface whose reference dangles (no such id) is UNPRICED and counted, because
an unpriceable panel must never be read as a pass. The same rule runs from the other side: a label
painted BY a server (`fill="url(#titlec)"`, which is how the home banner's own title is drawn) is
priced at its most favourable stop and counted `approx`, instead of being left unmeasured.

Burial is a two-arm test, and both thresholds were measured on this tree rather than picked:
`--buried` (share of a label's 6 probe points one phase hides at once) and `--steady` (share of the
cycle a point stays hidden). A playhead sweeping a label clipped 2/6 points in 1 of 39 phases and a
travelling packet 1/6 in 6 of 35 — choreography. The hub disc of 04-react-loop nibbled one badge glyph
in 25 of 25 probeable phases — a z-order defect. Either arm alone gets one of those two wrong.
A COVERED finding names the surface **over** the label, not the one under it.

A label that is itself mid-fade is not a contrast call: while its own alpha is below `--presence`
(default 0.60) the phase is exempted and counted, so "it fades in" and "it is invisible" stay
distinguishable. Round 70 narrowed that exemption to what the sentence actually claims: it applies only
when an `<animate>` on the label or one of its ancestors can move its alpha at all. A permanently
translucent label is not arriving late — it is faint, and that is a verdict — and the 18 static
figures have no phase to sweep, so the old reading let every faint label in them off by default.
Because every phase is sampled, a verdict says whether the defect is phase-specific
(`PHASE-ONLY`: the best frame clears the bar and the worst does not — invisible to the still-frame
axes) or steady (`DARK`, reported as bycatch, since no earlier axis priced colour at all).

Which bar a label answers to is WCAG 1.4.3's own tier, computed per label rather than assumed:
`SCALE = svg.getBoundingClientRect().width / viewBox.width` (the reader's column shrinks a 960-unit
canvas to 0.8, so an authored 16px renders 12.8px), and the bar is 3.0 at >= 24px or >= 18.66px bold,
4.5 otherwise. That single change is what turned this axis from 43 phase findings into 43 + 66: the
extra 66 are steady small-text labels sitting 3.0-4.5:1, i.e. legal under the old flat 3.0 bar and
unreadable at the size the live column actually shows them.

`--presence` was probed as a knob and left at 0.60 on measurement. Two labels fade their own alpha
(the 16-sandbox ✕ pulse, the 17-action-chunking replan row) and at 0.60 they only reach 3.55 with the
red-900 ink they shipped with; the honest fix was the ink (red-950 #450a0a), which lifts them to
4.56 / 4.78 at 0.60 without touching the ruler. Raising the exemption to 0.75 would have cleared them
too, and was rejected: it would have silently exempted every future fade in the 0.60-0.75 band.

Guards:
  * `--selftest` grades twenty-five planted SVGs through the same code path as a real figure: a white label
    over a growing dark bar (must come back PHASE-ONLY), a dark label over a growing light bar
    (silent), a label under a cover rect (COVERED), a label that only fades in (exempted, and the
    selftest asserts the exemption branch actually ran), a label dark in every frame (DARK and
    specifically NOT PHASE-ONLY — that pair is the axis's whole point, so it needs both halves),
    a timeline that cannot advance (`begin="indefinite"`, which must be RULER BLIND, never clean),
    the house hairline grid and an opaque pattern tile (both must price the server, not throw up),
    a glyph in a circle's bbox corner (must NOT read buried), one buried point forever (must), and
    one crossed for a phase (must not), a dangling paint reference (must say "not measured"),
    a faint label with no animation anywhere near it (must be JUDGED, not exempted), a label painted
    by a gradient in both directions (a sweep whose darkest stop clears a white plate must grade
    clean *because it was priced*, and a sweep whose every stop fails its own plate must grade DARK —
    the pair that pins ink-server pricing from both sides), and the same ink sweep landing ON a
    gradient plate (the banner's title: `fill="url(#titlec)"` over the `url(#bgb)` page wash, where
    the reference colour for the plate choice has no literal and a crash there reads as "no figure"
    rather than as a defect — both directions of that stack are planted), and
    four tier plants that pin the size rule from both sides: 16px must answer to 4.5, 24px and
    20px-bold to 3.0, and a 30px label in a 800-unit canvas hosted at 400px must shrink to 15px and
    fall back to 4.5 — the plant that proves the scale factor is applied, not just printed.
  * the plate interpolation is pinned by four plants built from the SAME two stops, the same rect and
    the same white label, so only the paint server differs: `PLANT_GRAD_MID` and `PLANT_GRAD_DIAG`
    (an axis-aligned and a diagonal linear sweep — the middle of the sweep must be measured, so both
    grade DARK and must carry zero `approx` points), `PLANT_GRAD_RADIAL` and `PLANT_GRAD_USERSPACE`
    (the two servers the ruler refuses to price point by point — both must fall back to the favourable
    stop and say so by carrying `approx`). Without the zero-approx half of the pair, a ruler that
    ignored every gradient would still print a clean selftest; without the approx half, a ruler that
    guessed at everything would too.
  * per-figure liveness: the node under the figure's first `<animate>` must read differently at three
    points of the cycle, else the figure is a COVERAGE failure. Only applies where animations exist.
  * vacuity floor: `--mode animated` needs 10 animated figures, `--mode static` needs 12 of the
    never-animated ones, `--mode all` needs both. The static half is what round 69 left unmeasured
    and round 70 found 115 defects in.
  * a label the ruler could not price (its own paint, or a surface under it, is a dangling reference)
    is reported as COVERAGE and fails the run — counting it silently was how a banner title with
    `fill="url(#titlec)"` looked like a pass.
  * every finding carries attribution: the label's document index, the authored attribute painting its
    ink (which may sit on an ancestor `<g>`), and the topmost surface's index plus its own authored
    `fill` / `fill-opacity` / `opacity`. Without it a recolour round has to guess which literal to
    replace, and a global hex swap moves strokes and decorative plates too.

Honest limits: the page background is taken as white (the light theme the live column measures);
a pattern's tiles are composited over white and then scaled by the tile's own `opacity` — the house
grid is a 0.7px hairline at 0.22-0.5, and pricing it at full strength charged every label in
06-memory-tiers as sitting on an opaque slate plate (5 false DARKs, now planted against);
hit-testing asks the geometry (`isPointInFill`) where the element can answer and falls back to the
box for images and uses; a PLATE is priced exactly for any objectBoundingBox linear sweep — a radial
wash, a pattern tile and a `userSpaceOnUse` server still fall back to the stop **farthest in luminance
from the ink**, so a label that passes on one of those is not proof that its own corner of the pill
clears the bar (every such row is counted `approx`, and the count is printed per figure and by kind so
the leniency is measurable rather than folklore); a gradient INK is priced the same favourable way at
every plate, so
a label that passes on a dark stop can still be invisible on its light end; the `[on ...]` note names
the surface examined last
while sweeping, not necessarily the one under the worst phase; and `--shots` screenshots phase ~N by
virtual-time arithmetic, which is approximate (it exists for the eyeball leg, not for verdicts).

Usage:
    python tools/checks/check_svg_phase_legibility.py --selftest
    python tools/checks/check_svg_phase_legibility.py
    python tools/checks/check_svg_phase_legibility.py --assets 16-continuous-batching
    python tools/checks/check_svg_phase_legibility.py --shots 3 --assets 16-continuous-batching
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(REPO, "docs", ".gitbook", "assets")
DOCS = os.path.join(REPO, "docs")
SHOTS = os.path.join(REPO, ".tmp-projects")
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

from check_mermaid_geometry import Server                                  # noqa: E402

SVGNS = "{http://www.w3.org/2000/svg}"
FIG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+\.svg)")
COLUMN = 768        # round 62's <main>: the reader's column, same host width the size axis uses
BAR = 4.5           # WCAG 1.4.3 AA for the text these figures actually render into
BAR_LARGE = 3.0     # ...and the large-text tier: >= 24px, or >= 18.66px at weight >= 700
PRESENCE = 0.60     # below this a label is mid-fade, so the phase is exempted rather than judged
BURIED = 0.5        # share of a label's probe points hidden at once: measured on the real figures, a
                    # passing packet/playhead peaks at 2/6 (33%) and PLANT_COVER buries 6/6. The 04
                    # hub nibbles only 1/6, so it is caught by STEADY below, not by this arm.
STEADY = 0.5        # share of the cycle for which one slot stays hidden: the transient cases were
                    # measured at 1/39 and 6/35 of their phases, the real z-order defect at 25/25
GRID = 24           # uniform samples per cycle, on top of every authored keyTime
TICK = 30           # ms of virtual time per phase; see the driver note above
MIN_FIGURES = 10    # vacuity floor
MIN_STATIC = 12     # ... and for the never-animated half (18 figures today)

PROBE = r"""
(function () {
  var RID = @@RID@@, PORT = @@PORT@@, BAR = @@BAR@@, BAR_LARGE = @@BAR_LARGE@@,
      PRESENCE = @@PRESENCE@@,
      TICK = @@TICK@@, GRID = @@GRID@@, SHOT = @@SHOT@@, BURIED = @@BURIED@@, STEADY = @@STEADY@@;
  var svg = document.querySelector('#host svg');
  function post(o, done) {
    var x = new XMLHttpRequest();
    x.open('POST', 'http://127.0.0.1:' + PORT + '/report', false);
    o.id = RID; o.done = !!done;
    x.send(JSON.stringify(o));
  }
  function hold() {                                  /* the latch keeps the page alive to read */
    var h = new XMLHttpRequest();
    h.open('GET', 'http://127.0.0.1:' + PORT + '/hold?rid=' + RID, false);
    try { h.send(); } catch (e) {}
  }
  /* A fatal beacon must say WHERE it died: "reading 'map'" alone sent me fixing the wrong undefined
     twice in one round, because the probe's own line numbers are invisible from the harness. */
  window.onerror = function (m, src, line, col, err) {
    var at = " @probe:" + line + ":" + col;
    var frames = err && err.stack ? String(err.stack).split("\n").slice(1, 3).join(" < ") : "";
    post({fatal: String(m).slice(0, 200) + at + (frames ? " |" + frames.slice(0, 180) : "")}, true);
    hold();
  };
  if (!svg) { post({fatal: 'no svg in #host'}, true); hold(); return; }

  function num(v) { var n = parseFloat(v); return isNaN(n) ? 0 : n; }
  function secs(v) { return !v ? 0 : (/ms$/.test(v) ? parseFloat(v) / 1000 : (parseFloat(v) || 0)); }

  /* Phase set: every keyTime the author wrote (that is where a state flips) plus a uniform grid.
     A negative `begin` (a figure that starts mid-cycle) is clamped: setCurrentTime() takes document
     time, and a negative phase would silently read as t=0 while being reported as its own instant. */
  function times() {
    var t = {}, total = 0, anims = svg.querySelectorAll('animate, animateTransform');
    for (var i = 0; i < anims.length; i++) {
      var a = anims[i], begin = secs(a.getAttribute('begin')), dur = secs(a.getAttribute('dur'));
      if (!dur) continue;
      total = Math.max(total, begin + dur);
      var kt = (a.getAttribute('keyTimes') || '').split(';');
      for (var k = 0; k < kt.length; k++) t[Math.max(0, begin + dur * num(kt[k]))] = 1;
    }
    total = Math.max(0, total);
    for (var p = 0; p <= GRID; p++) t[total * p / GRID] = 1;
    return Object.keys(t).map(Number).sort(function (x, y) { return x - y; });
  }

  function color(c) {
    if (!c || c === 'none') return null;
    if (/^url\(/.test(c)) return {grad: 1};
    var m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    var v = m[1].split(',').map(Number);
    return {rgb: [v[0], v[1], v[2]], a: v.length > 3 ? v[3] : 1};
  }
  function stacked(el) {                      /* the alpha the reader actually gets for this node */
    var a = 1, n = el;
    while (n && n.nodeType === 1) { a *= parseFloat(getComputedStyle(n).opacity || '1'); n = n.parentNode; }
    return a;
  }
  function over(fg, alpha, bg) {
    return [0, 1, 2].map(function (i) { return alpha * fg[i] + (1 - alpha) * bg[i]; });
  }
  function lum(c) {
    var v = c.map(function (x) { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
    return v[0] * 0.2126 + v[1] * 0.7152 + v[2] * 0.0722;
  }
  function cr(a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }

  /* A paint server is not one colour. Its candidate colours are read from the referenced element
     and a label over it is priced against the candidate FARTHEST from the label's own colour: that
     is the frame most favourable to the label, so a DARK verdict can never be the server's fault.
     Gradients contribute their <stop>s; a <pattern> (the house grid: a hairline path at 0.07 in a
     40px tile) contributes its children's own paints. Ignoring patterns would leave every label in
     7 of the 14 animated figures unpriced, because a full-canvas grid rect sits under all of them. */
  function childPaints(el) {
    var out = [], kids = el.querySelectorAll('rect,circle,ellipse,path,polygon,polyline,image');
    for (var q = 0; q < kids.length; q++) {
      var cc = getComputedStyle(kids[q]);
      /* A tile's own `opacity` scales its paint, and a pattern is usually a hairline grid: the
         house style draws it at 0.22-0.5. Charging it at full strength told us that every label in
         06-memory-tiers sat on an opaque #94a3b8 plate (2.14:1) and that 11's tick row sat on
         #e9d5f5 — 14 findings, all of them the wash of a 0.7px line over paper. */
      var op = parseFloat(cc.opacity);
      var k = isNaN(op) ? 1 : op;
      var f = color(cc.fill), s = color(cc.stroke);
      if (f && !f.grad) {
        var fo = parseFloat(cc.fillOpacity);
        out.push(over(f.rgb, (isNaN(fo) ? 1 : fo) * f.a * k, [255, 255, 255]));
      }
      if (s && !s.grad && parseFloat(cc.strokeWidth) > 0) {
        var so = parseFloat(cc.strokeOpacity);
        out.push(over(s.rgb, (isNaN(so) ? 1 : so) * s.a * k, [255, 255, 255]));
      }
    }
    return out;
  }
  function serverColors(fill) {
    var m = /url\(["']?#([^"')]+)["']?\)/.exec(fill || '');   /* the # is part of the reference */
    if (!m) return null;
    var g = svg.ownerDocument.getElementById(m[1]);
    if (!g) return null;
    var out = [];
    if (/gradient$/i.test(g.tagName)) {
      var stops = [].slice.call(g.querySelectorAll('stop'));
      for (var q = 0; q < stops.length; q++) {
        var css = getComputedStyle(stops[q]), sc = color(css.stopColor);
        var so = parseFloat(css.stopOpacity);
        if (sc && !sc.grad) out.push(over(sc.rgb, isNaN(so) ? 1 : so, [255, 255, 255]));
      }
    } else {
      out = childPaints(g);
    }
    return out.length ? out : null;
  }
  function serverKind(fill) {
    var m = /url\(["']?#([^"')]+)["']?\)/.exec(fill || '');
    var g = m && svg.ownerDocument.getElementById(m[1]);
    return !g ? "?" : (/gradient$/i.test(g.tagName) ? "gradient" : "pattern");
  }
  function bestColor(cands, ink) {
    var best = null, bl = -1;
    for (var q = 0; q < cands.length; q++) {
      var d = Math.abs(lum(cands[q]) - lum(ink));
      if (d > bl) { bl = d; best = cands[q]; }
    }
    return best;
  }

  /* A gradient PLATE is not one colour, and "price it at the stop farthest from the ink" is a
     leniency the reader never gets: a white label centred on a light-over-dark pill sits on the MID
     of that pill, not on its darkest end, and the banner's violet node passed on 5.0:1 while the
     glyphs themselves stood on 3.4:1. So for any objectBoundingBox linear gradient the colour under
     each probe point is interpolated from the stops exactly as the renderer mixes them — including a
     DIAGONAL sweep, which is the house page wash under all 32 figures, so refusing it would leave
     every label in the book priced by a guess. What still falls back to the favourable stop is a
     radial wash and a `userSpaceOnUse` server (whose axis lives in the SVG's own coordinate system,
     not the element's box, and getting that wrong is a confident wrong number), and both stay marked
     `approx`. */
  function gradInfo(fill) {
    var m = /url\(["']?#([^"')]+)["']?\)/.exec(fill || '');
    if (!m) return null;
    var g = svg.ownerDocument.getElementById(m[1]);
    /* Only a LINEAR sweep has an axis to interpolate along. A radialGradient has no x1/y1/x2/y2 at
       all, so reading the linear defaults off it would invent a horizontal sweep and hand back a
       confident wrong number — the worse failure. Radial servers (the banner's and 04-react-loop's
       `glow` washes) stay on the favourable-stop branch below, marked `approx`. */
    if (!g || !/^linearGradient$/i.test(g.tagName)) return null;
    if ((g.getAttribute('gradientUnits') || 'objectBoundingBox') !== 'objectBoundingBox') return null;
    function frac(v, d) { return v === null ? d : (/%$/.test(v) ? num(v) / 100 : num(v)); }
    var x1 = frac(g.getAttribute('x1'), 0), y1 = frac(g.getAttribute('y1'), 0),
        x2 = frac(g.getAttribute('x2'), 1), y2 = frac(g.getAttribute('y2'), 0);
    var stops = [].slice.call(g.querySelectorAll('stop')).map(function (st) {
      var c = color(getComputedStyle(st).stopColor);
      var so = parseFloat(getComputedStyle(st).stopOpacity);
      return {o: frac(st.getAttribute('offset'), 0), rgb: c && c.rgb, a: isNaN(so) ? 1 : so};
    }).filter(function (s) { return s.rgb; }).sort(function (p, q) { return p.o - q.o; });
    /* objectBoundingBox units are fractions of the element's box, so the axis vector has to be
       scaled by that box before it can be projected against screen coordinates. */
    return stops.length > 1 && (x1 !== x2 || y1 !== y2)
        ? {dx: x2 - x1, dy: y2 - y1, stops: stops} : null;
  }
  function gradAt(s, px, py) {
    var st = s.ginfo.stops, k = 0;
    var vx = s.ginfo.dx * (s.x1 - s.x0), vy = s.ginfo.dy * (s.y1 - s.y0);
    var len2 = vx * vx + vy * vy;
    var u = len2 > 0 ? ((px - s.x0) * vx + (py - s.y0) * vy) / len2 : 0;
    u = Math.max(0, Math.min(1, u));
    while (k < st.length - 2 && u > st[k + 1].o) k++;
    var a = st[k], b = st[Math.min(k + 1, st.length - 1)];
    var span = b.o - a.o, f = span > 0 ? Math.max(0, Math.min(1, (u - a.o) / span)) : 0;
    var mix = [0, 1, 2].map(function (i) { return a.rgb[i] + (b.rgb[i] - a.rgb[i]) * f; });
    return over(mix, a.a + (b.a - a.a) * f, [255, 255, 255]);
  }

  var PAINTED = {rect: 1, circle: 1, ellipse: 1, path: 1, polygon: 1, polyline: 1, image: 1, use: 1};
  var all = [].slice.call(svg.querySelectorAll('*'));
  function inDefs(el) {                       /* a clipPath/marker/pattern path is not a surface */
    if (el.closest) return !!el.closest('defs, clipPath, mask, pattern, marker, symbol');
    for (var n = el.parentNode; n && n.nodeType === 1; n = n.parentNode)
      if (/^(defs|clipPath|mask|pattern|marker|symbol)$/.test(n.tagName)) return true;
    return false;
  }
  /* WCAG 1.4.3 sets its own size test, so the bar belongs to a label rather than to the run.
     getComputedStyle reports user units, and these figures author into a 960-wide viewBox that the
     768px column then shrinks: an authored 16px reaches the eye at 12.8 CSS px, which is small text
     and needs 4.5:1. Large text is >= 24px, or >= 18.66px at weight >= 700 (WCAG's own 14pt/18.66px
     and "bold" clause) and keeps the 3:1 bar. */
  var VB = svg.viewBox && svg.viewBox.baseVal;
  var SCALE = (VB && VB.width) ? (svg.getBoundingClientRect().width / VB.width) : 1;
  function tierOf(cs) {
    var px = num(cs.fontSize) * SCALE;
    var w = cs.fontWeight === 'bold' ? 700 : num(cs.fontWeight);
    return {px: Math.round(px * 10) / 10,
            bar: (px >= 24 || (px >= 18.66 && w >= 700)) ? BAR_LARGE : BAR};
  }
  var labels = [].slice.call(svg.querySelectorAll('text')).filter(function (el) {
    return !inDefs(el) && (el.textContent || '').trim();
  }).map(function (el) {
    var t = tierOf(getComputedStyle(el));
    return {el: el, idx: all.indexOf(el), text: (el.textContent || '').trim().slice(0, 24),
            px: t.px, bar: t.bar};
  });

  /* One snapshot of the painted stack per phase: boxes, colours and alphas read once, then every
     "what is under this glyph" question is arithmetic. Without the cache the sweep asks the layout
     engine ~10^7 questions and never finishes a cycle. */
  function snapshot() {
    var out = [];
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (!PAINTED[el.tagName.toLowerCase()] || inDefs(el)) continue;
      var cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      var c = color(cs.fill);
      if (!c) continue;
      var box = el.getBoundingClientRect();
      if (box.width < 0.5 || box.height < 0.5) continue;
      var s = {i: i, tag: el.tagName, el: el, x0: box.left, y0: box.top, x1: box.right,
               y1: box.bottom, grad: c.grad ? 1 : 0, rgb: c.rgb, a: 1};
      s.a = stacked(el) * (c.a || 1) * num(cs.fillOpacity === '' ? 1 : cs.fillOpacity);
      if (c.grad) { s.colors = serverColors(cs.fill); s.ginfo = gradInfo(cs.fill); s.ref = cs.fill;
                    s.kind = serverKind(cs.fill);
                    s.a = stacked(el) * num(cs.fillOpacity === '' ? 1 : cs.fillOpacity); }
      if (s.a < 0.004) continue;
      out.push(s);
    }
    return out;
  }

  /* A circle's bounding box is not its paint. The hub of 04-react-loop is a 92px circle whose bbox
     corner reaches over the step badge beside it, and the axis called that glyph buried in every
     phase although the reader sees it. Geometry nodes answer the point themselves; image/use have
     no fill path, so their box stays the best available answer. */
  function covers(s, px, py) {
    if (px < s.x0 - 0.5 || px > s.x1 + 0.5 || py < s.y0 - 0.5 || py > s.y1 + 0.5) return false;
    var el = s.el;
    if (el.isPointInFill && el.getScreenCTM) {
      try {
        var ctm = el.getScreenCTM();
        if (ctm) return el.isPointInFill(new DOMPoint(px, py).matrixTransform(ctm.inverse()));
      } catch (e) { /* no geometry answer: fall through to the box */ }
    }
    return true;
  }

  var ts = times();
  /* Liveness control: every node the figure animates is signed at three points of the cycle (its
     box, the computed value of the attribute it animates, and its DOM attribute). If not ONE of
     them moves, the ruler is blind — a figure whose first animation is a `stroke-dashoffset` march
     or a `<line x1>` sweep would otherwise be reported blind by a geometry-only sampler. */
  var targets = [], seenT = {};
  var anims = svg.querySelectorAll('animate, animateTransform');
  for (var a = 0; a < anims.length && targets.length < 12; a++) {
    var par = anims[a].parentNode;
    if (par && !seenT[a._k = (par.tagName + '#' + (par.id || a))]) {
      seenT[par.tagName + '#' + (par.id || a)] = 1;
      targets.push({el: par, attr: anims[a].getAttribute('attributeName') || 'transform'});
    }
  }
  var liveAt = {};
  /* Not t=0 and not t=dur: on a repeating cycle both land on the first authored value, so a figure
     whose animation differs only at the boundary would look frozen. */
  [1, Math.floor(ts.length / 2), ts.length - 2].forEach(function (q) {
    if (q >= 0 && q < ts.length) liveAt[ts[q]] = 1;
  });
  var live = [];
  function signature(tg) {
    var b = tg.el.getBoundingClientRect(), cs = getComputedStyle(tg.el), v = cs[tg.attr];
    if (v === undefined) v = String(tg.el.getAttribute(tg.attr));
    return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height),
            String(v).slice(0, 40)].join("|");
  }

  var rows = labels.map(function (o) {
    return {text: o.text, worst: 99, best: -1, at: null, cov: 0, covAt: null, fade: 0,
            px: o.px, bar: o.bar,
            ink: null,
            covFrac: 0, covPts: 0, covAll: 0, covPhases: 0, probed: 0, covBy: null,
            onGrad: 0, ownGrad: 0, panelGrad: 0, judged: 0, approx: 0,
            approxPat: 0, approxGrad: 0, approxInk: 0, amin: 1, amax: 0,
            top: null, unpricedBy: null, inkRgb: null, inkGrad: 0};
  });

  svg.pauseAnimations();
  /* `--presence` exempts a label only while it is genuinely mid-fade. A label whose alpha cannot
     move is not "arriving late" — it is permanently translucent, and that is a contrast call like
     any other. Static figures (no <animate>) have no phase to sweep, so without this a faint label
     there would hide behind the exemption forever.
     Whether alpha CAN move is read off the markup, not measured by a pre-sweep: SMIL values only
     reach getComputedStyle after the browser paints a frame, so a synchronous loop of
     setCurrentTime() reports one constant alpha at every phase. (Measured: the pre-sweep version
     exempted nothing and made PLANT_FADE, a label sweeping 0.00 -> 1.00, read DARK at t=0.)
     Limit, honest: an <animate> that reaches this label's alpha from elsewhere by xlink:href is not
     seen here — no authored figure in this tree does that. */
  var ALPHA_ATTR = {opacity: 1, 'fill-opacity': 1, 'fill': 1, 'stroke-opacity': 1};

  /* Attribution, so a FINDING can be turned into an edit without guessing: computed colour says the
     label is unreadable, but the string to replace is an AUTHORED literal, and it is not always on
     the <text> (a `<g fill="#94a3b8">` paints every child label). `inkSource` therefore walks up to
     the nearest node carrying `fill`, and `top` carries the surface's own literal. Indexes are into
     `all` (document order), which is how the fixing pass points at a node. */
  function lit(el, name) {
    var v = el.getAttribute ? el.getAttribute(name) : null;
    return v === null ? null : name + '="' + v + '"';
  }
  function authored(el) {
    return [lit(el, 'fill'), lit(el, 'fill-opacity'), lit(el, 'opacity')].filter(Boolean).join(" ");
  }
  function inkSource(el) {
    for (var n = el; n && n.nodeType === 1; n = n.parentNode) {
      var v = n.getAttribute ? n.getAttribute('fill') : null;
      if (v !== null) return [n.tagName, all.indexOf(n), 'fill="' + v + '"', n === el ? 1 : 0];
    }
    return null;
  }
  function alphaAnimated(el) {
    for (var n = el; n && n.nodeType === 1; n = n.parentNode) {
      var kids = n.children || [];
      for (var k = 0; k < kids.length; k++) {
        var tg = String(kids[k].tagName || '').toLowerCase();
        if (tg !== 'animate' && tg !== 'set') continue;
        if (ALPHA_ATTR[(kids[k].getAttribute('attributeName') || '').toLowerCase()]) return 1;
      }
    }
    return 0;
  }
  for (var q = 0; q < rows.length; q++) {
    rows[q].varying = alphaAnimated(labels[q].el);
    rows[q].idx = labels[q].idx;
    rows[q].inkFrom = inkSource(labels[q].el);      /* which authored attribute paints this ink */
  }
  function measure(t) {
    var snap = snapshot();
    if (liveAt[t] && live.length < 3) {
      live.push([Math.round(t * 100) / 100].concat(targets.map(signature)));
    }
    for (var n = 0; n < labels.length; n++) {
      var o = labels[n], r = rows[n], cs = getComputedStyle(o.el);
      var box = o.el.getBoundingClientRect();
      if (box.width < 0.5 || box.height < 0.5) continue;
      var fill = color(cs.fill);
      if (!fill) continue;
      /* A label can be painted BY a server too (the home banner's title is `fill="url(#titlec)"`).
         Refusing to price those left the book's own title unmeasured, so the same favourable-candidate
         rule is applied from the ink side: price against the stop farthest from the plate, and count
         the row `approx` so a pass is never read as proof that every stop clears. A reference that
         resolves to nothing stays UNPRICED. */
      var inkServer = fill.grad ? serverColors(cs.fill) : null;
      if (fill.grad && !inkServer) {
        r.onGrad++; r.ownGrad++; r.unpricedBy = ["text", o.idx, cs.fill, authored(o.el)]; continue;
      }
      /* Which colour to bias the PLATE's stop choice with when the ink itself is a sweep: `url()` has
         no fill.rgb, and reading it undefined is what killed the banner probe (the ruler died rather
         than failing, which is the one outcome it must never produce). The reference only picks which
         stop of a gradient plate gets composited, and the ratio below re-picks the ink stop against
         the composed plate, so taking the stop farthest from the white paper these figures author on
         keeps the frame favourable without inventing a contrast. */
      var inkRef = inkServer ? bestColor(inkServer, [255, 255, 255]) : fill.rgb;
      var ta = stacked(o.el) * (inkServer ? 1 : fill.a) * num(cs.fillOpacity === '' ? 1 : cs.fillOpacity);
      r.amin = Math.min(r.amin, ta); r.amax = Math.max(r.amax, ta);
      if (ta < PRESENCE && r.varying) { r.fade++; continue; }   /* mid-fade: exempt, not judged */
      var xs = [box.left + 2, (box.left + box.right) / 2, box.right - 2];
      var ys = [box.top + box.height * 0.35, box.top + box.height * 0.65];
      var pts = 0, covPts = 0, cnt = {}, dims = {};
      for (var i = 0; i < ys.length; i++) {
        for (var j = 0; j < xs.length; j++) {
          var px = xs[j], py = ys[i], bg = [255, 255, 255], cover = 0, grad = 0, approx = 0;
          var ap = 0, ag = 0;                       /* which kind of server made this point a guess */
          for (var k = 0; k < snap.length; k++) {
            var s = snap[k];
            if (s.i === o.idx) continue;
            var inside = covers(s, px, py);
            if (!inside) continue;
            if (s.i < o.idx) {
              if (s.grad && !s.colors) { grad = 1; r.unpricedBy = [s.tag, s.i, s.ref, authored(s.el)]; break; }
              /* The plate's own colour: interpolated at the probe point where the sweep is a simple
                 axis-aligned gradient (what the reader actually sees under the glyph), else the stop
                 farthest from the ink — a guess, so the row is marked `approx`. */
              if (s.ginfo) { bg = over(gradAt(s, px, py), s.a, bg); }
              else if (s.colors) { approx = 1; if (s.kind === "pattern") ap = 1; else ag = 1;
                                   bg = over(bestColor(s.colors, inkRef), s.a, bg); }
              else bg = over(s.rgb, s.a, bg);
              r.top = [s.tag, s.i, Math.round(s.a * 100) / 100, bg.map(Math.round), authored(s.el)];
            } else if (s.a >= 0.95) {
              if (!cover) {
                var key = s.tag + '#' + s.i;
                cnt[key] = (cnt[key] || 0) + 1;
                dims[key] = [s.tag, s.i, Math.round(s.a * 100) / 100,
                             Math.round(s.x1 - s.x0), Math.round(s.y1 - s.y0)];
              }
              cover = 1;
            }
          }
          if (grad) { r.onGrad++; r.panelGrad++; continue; }
          pts++;
          if (approx) { r.approx++; r.approxPat += ap; r.approxGrad += ag; }
          if (cover) {                                   /* buried this phase: not a colour call */
            covPts++;
            r.cov |= 1 << (i * 3 + j);                   /* which of the 6 slots is ever hidden */
            continue;
          }
          if (inkServer) { r.inkGrad++; r.approx++; r.approxInk++; }
          var ink = over(inkServer ? bestColor(inkServer, bg) : fill.rgb, ta, bg), c = cr(ink, bg);
          r.judged++;
          if (c < r.worst) { r.worst = c; r.at = t; r.ink = cs.fill; r.inkRgb = ink.map(Math.round); }
          if (c > r.best) r.best = c;
        }
      }
      if (pts) r.probed++;
      if (covPts) {
        r.covPhases++;
        var frac = pts ? covPts / pts : 1;
        if (frac > r.covFrac) {
          var wk = null, wn = -1;
          for (var key2 in cnt) { if (cnt[key2] > wn) { wn = cnt[key2]; wk = key2; } }
          r.covFrac = frac; r.covPts = covPts; r.covAll = pts; r.covAt = t; r.covBy = dims[wk];
        }
      }
    }
  }

  function report() {
    function slots(m) { var n = 0; for (var b = 0; b < 6; b++) if (m & (1 << b)) n++; return n; }
    post({phases: ts.length, tmax: ts[ts.length - 1], live: live, targets: targets.length,
          labels: labels.length, bar: BAR, barLarge: BAR_LARGE, scale: Math.round(SCALE*1000)/1000,
          presence: PRESENCE,
          rows: rows.map(function (r) {
            var dur = Math.round(100 * r.covPhases / (r.probed || 1)) / 100;
            return {text: r.text, judged: r.judged, worst: Math.round(r.worst * 100) / 100,
                    best: Math.round(r.best * 100) / 100, at: r.at,
                    px: r.px, bar: r.bar, ink: r.ink,
                    cov: slots(r.cov), covPhases: r.covPhases, covPts: r.covPts,
                    covAll: r.covAll, probed: r.probed, covDur: dur,
                    covFrac: Math.round(r.covFrac * 100) / 100,
                    covBy: r.covBy, covAt: r.covAt,
                    fade: r.fade, varying: r.varying, onGrad: r.onGrad, ownGrad: r.ownGrad, panelGrad: r.panelGrad,
                    approx: r.approx, approxPat: r.approxPat, approxGrad: r.approxGrad,
                    approxInk: r.approxInk,
                    amin: Math.round(r.amin * 100) / 100,
                    amax: Math.round(r.amax * 100) / 100, top: r.top,
                    idx: r.idx, inkFrom: r.inkFrom, unpricedBy: r.unpricedBy,
                    inkGrad: r.inkGrad, inkRgb: r.inkRgb,
                    dark: r.judged > 0 && r.worst < r.bar,
                    phaseOnly: r.judged > 0 && r.worst < r.bar && r.best >= r.bar,
                    buried: r.covFrac >= BURIED || dur >= STEADY};
          })}, true);
    hold();
  }

  var i = 0;
  function step() {
    if (SHOT) { /* eyeball leg: leave the figure on the requested frame, then take the screenshot */
      if (i >= Math.min(SHOT, ts.length)) return;
      svg.setCurrentTime(ts[i]);
      setTimeout(function () { if (++i >= Math.min(SHOT, ts.length)) post({shot: ts[i - 1]}, false);
                               step(); }, TICK);
      return;
    }
    if (i >= ts.length) { report(); return; }
    svg.setCurrentTime(ts[i]);
    setTimeout(function () { measure(ts[i]); if (++i % 10 === 0) post({stage: 'progress', i: i,
      of: ts.length}, false); step(); }, TICK);
  }
  step();
})();
"""


def host(src, args, rid, live_port):
    js = (PROBE.replace("@@RID@@", str(rid))
          .replace("@@PORT@@", str(srv_port[0] if live_port else 0))
          .replace("@@BAR@@", str(args.bar)).replace("@@BAR_LARGE@@", str(args.bar_large))
          .replace("@@PRESENCE@@", str(args.presence))
          .replace("@@TICK@@", str(args.tick)).replace("@@GRID@@", str(args.grid))
          .replace("@@BURIED@@", str(args.buried)).replace("@@STEADY@@", str(args.steady))
          .replace("@@SHOT@@", str(args.shots)))
    return ('<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:#fff}'
            '#host{width:%dpx}#host svg{width:100%%;height:auto;display:block}</style>'
            '<div id="host">%s</div><script>%s</script>') % (args.column, src, js)


srv_port = [0]


def animated_figures(mode="animated"):
    """Asset paths of in-body SVG figures, by whether they animate.

    `static` is the half round 69 could not price: 18 of the 32 in-body figures carry no <animate>,
    so no phase exists to sweep and their labels were never checked for contrast by ANY axis (the
    size ruler prices px, the geometry ruler prices boxes -- neither has ever looked at a colour).
    """
    used = set()
    for root, _dirs, files in os.walk(DOCS):
        for f in files:
            if f.endswith(".md"):
                for m in FIG_RE.finditer(io.open(os.path.join(root, f), encoding="utf-8").read()):
                    used.add(os.path.basename(m.group(1)).lower())
    out = []
    for name in sorted(used):
        path = os.path.join(ASSETS, name)
        if not os.path.isfile(path):
            continue
        try:
            root = ET.fromstring(io.open(path, encoding="utf-8").read())
        except ET.ParseError:
            continue
        n = len([e for e in root.iter() if e.tag == SVGNS + "animate"])
        if (n and mode != "static") or (not n and mode != "animated"):
            out.append((name, n))
    return out


def sweep(srv, name, src, args, rid, na=1):
    io.open(os.path.join(srv.root, "phase-%s.html" % rid), "w", encoding="utf-8").write(
        host(src, args, rid, True))
    srv.hold(rid, 150)
    out = os.path.join(SHOTS, "phase-shot-%s.png" % name.replace(".svg", ""))
    if args.shots:
        flags = ["--virtual-time-budget=%d" % (args.shots * args.tick + args.tick * 2),
                 "--screenshot=" + out]
        # A PNG left by an earlier run would make "it exists" a lie about this one.
        for stale in (out, out + ".tmp"):
            if os.path.exists(stale):
                os.remove(stale)
    else:
        flags = ["--dump-dom", "--virtual-time-budget=200000"]
    proc = srv.render("phase-%s.html" % rid, flags, height=args.height)
    try:
        if args.shots:
            try:
                proc.wait(120)
            except subprocess.TimeoutExpired:
                pass
            seen = [r for r in srv.reports if r.get("id") == rid and "shot" in r]
            return {"shot": out, "shot_at": seen[-1]["shot"] if seen else None}
        rep = srv.wait(rid, 200, proc)
    finally:
        Server.stop(proc)
        srv.holds.pop(rid, None)
    if not rep or not rep.get("rows"):
        seen = [r for r in srv.reports if r.get("id") == rid]
        return {"coverage": "%s: no reading (%d beacon(s): %s) — the ruler never ran, which is not a "
                            "pass" % (name, len(seen), json.dumps(seen[-2:])[:220])}
    live = rep.get("live") or []
    cols = range(1, min(len(l) for l in live)) if live else []
    moved = sum(1 for c in cols if len({l[c] for l in live}) > 1)
    rep["moved"] = moved
    if na and (len(live) < 3 or not moved):
        return {"coverage": "%s: RULER BLIND — none of the %d animated node(s) reads differently at "
                            "%d points of the cycle, so the timeline never advanced (signatures %s)"
                % (name, rep.get("targets") or len(cols), len(live),
                   json.dumps([l[0] for l in live]))}
    if not rep.get("phases"):
        return {"coverage": "%s: no phase to measure (0 grid points) — the ruler never ran" % name}
    return rep


def findings(rep, args):
    out = []
    for r in rep["rows"]:
        w = "" if not r["top"] else "  [on %s#%d a=%.2f rgb(%s) %s]" % (
            r["top"][0], r["top"][1], r["top"][2], ",".join(str(v) for v in r["top"][3]),
            (r["top"][4] if len(r["top"]) > 4 else "") or "inherited")
        src = r.get("inkFrom") or []
        if src:
            w += "  [ink %s#%d %s%s]" % (src[0], src[1], src[2], "" if src[3] else " inherited")
        if r.get("inkGrad"):
            w += "  [gradient ink, priced at the stop most favourable to it: rgb(%s)]" % \
                 ",".join(str(v) for v in (r.get("inkRgb") or []))
        if r["dark"]:
            out.append("%-9s %-26s %4.1fpx bar %.2f  worst %.2f @ t=%ss  best %.2f  "
                       "alpha %.2f..%.2f  ink %s%s"
                       % ("PHASE-ONLY" if r["phaseOnly"] else "DARK", esc(r["text"]),
                          r["px"], r["bar"], r["worst"], r["at"], r["best"],
                          r["amin"], r["amax"], r["ink"], w))
        elif r["buried"]:
            by = r["covBy"] or ["?", 0, 0, 0, 0]
            out.append("COVERED   %-26s %d/%d pts buried at once (%d%%) in %d of %d probeable "
                       "phase(s) (%d%%), %d/6 slots ever, worst t=%ss  [under %s#%d a=%.2f "
                       "%dx%d px]"
                       % (esc(r["text"]), r["covPts"], r["covAll"], round(r["covFrac"] * 100),
                          r["covPhases"], r["probed"], round(r["covDur"] * 100), r["cov"],
                          r["covAt"], by[0], by[1], by[2], by[3], by[4]))
    return out


def esc(s):
    return s.encode("unicode_escape").decode("ascii")[:26]


G = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" width="400" height="120"'
G800 = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 120" width="800" height="120"'
PLANTS = [
    ("PLANT_PHASE_ONLY",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#166534">'
     '<animate attributeName="width" values="0;300;300" keyTimes="0;0.5;1" dur="4s" '
     'repeatCount="indefinite"/></rect><text x="160" y="66" text-anchor="middle" fill="#ffffff" '
     'font-size="16">white on a bar that has not arrived</text></svg>' % G, "phase-only"),
    ("PLANT_CLEAN",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#86efac">'
     '<animate attributeName="width" values="0;300;300" keyTimes="0;0.5;1" dur="4s" '
     'repeatCount="indefinite"/></rect><text x="160" y="66" text-anchor="middle" fill="#0f172a" '
     'font-size="16">dark on a bar that has not arrived</text></svg>' % G, "clean"),
    ("PLANT_COVER",
     '<svg %s><text x="10" y="66" fill="#0f172a" font-size="16">a label under a cover</text>'
     '<rect x="0" y="40" width="400" height="40" fill="#ffffff" opacity="0">'
     '<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.5;0.75;1" dur="4s" '
     'repeatCount="indefinite"/></rect></svg>' % G, "covered"),
    ("PLANT_FADE",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#14532d"></rect>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16" opacity="0">'
     'a label that fades in'
     '<animate attributeName="opacity" values="0;1;1" keyTimes="0;0.5;1" dur="4s" '
     'repeatCount="indefinite"/></text></svg>' % G, "clean-fading"),
    # The other side of the same rule, and the one the 18 static figures live on: alpha 0.4 with
    # nothing animating it is not a fade-in, it is a faint label. An exemption that read only
    # `alpha < presence` let these hide; this plant must be priced.
    ("PLANT_FADE_STATIC",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#dbeafe"></rect>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16" opacity="0.4">'
     'permanently translucent</text></svg>' % G, "dark"),
    ("PLANT_STEADY",
     '<svg %s><rect x="10" y="10" width="20" height="100" fill="#166534">'
     '<animate attributeName="width" values="20;120;20" dur="4s" repeatCount="indefinite"/></rect>'
     '<text x="230" y="66" fill="#ffffff" font-size="16">never behind the bar at all</text></svg>'
     % G, "dark"),
    ("PLANT_BLIND",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#166534">'
     '<animate attributeName="width" values="0;300" dur="4s" begin="indefinite"/></rect>'
     '<text x="20" y="66" fill="#0f172a" font-size="16">blind timeline</text></svg>' % G, "blind"),
    # The house grid, verbatim from 06-memory-tiers: a full-canvas rect painted by a <pattern> whose
    # only tile is a 0.7px slate hairline at `opacity="0.25"`. A resolver that only understands
    # gradients calls every label in these figures unpriced; a resolver that prices the tile at full
    # strength calls these #475569 subtitles 2.96:1 dark. Both directions fail loudly here.
    ("PLANT_PATTERN",
     '<svg %s><defs><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
     '<path d="M32 0 L0 0 0 32" fill="none" stroke="#94a3b8" stroke-width="0.7" opacity="0.25"/>'
     '</pattern></defs>'
     '<rect width="400" height="120" fill="url(#grid)" opacity="0.9">'
     '<animate attributeName="opacity" values="0.7;1;0.7" dur="4s" repeatCount="indefinite"/></rect>'
     '<text x="160" y="66" text-anchor="middle" fill="#475569" font-size="16" '
     '>slate on the house grid</text></svg>' % G, "clean"),
    # An opaque pattern tile: pricing the server as "transparent decoration" would read this
    # white-on-white and call it DARK, so only a real resolution grades clean.
    ("PLANT_TILE",
     '<svg %s><defs><pattern id="tile" width="20" height="20" patternUnits="userSpaceOnUse">'
     '<rect width="20" height="20" fill="#0f172a"/></pattern></defs>'
     '<rect width="400" height="120" fill="url(#tile)" opacity="0.9">'
     '<animate attributeName="opacity" values="0.85;1;0.85" dur="4s" repeatCount="indefinite"/></rect>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16" '
     '>white on an opaque tile</text></svg>' % G, "clean"),
    # A dangling paint reference on a SURFACE: what the reader sees is unknowable, so the axis must
    # say "not measured" rather than default the surface to white and report clean.
    # A glyph in the corner of a circle's bounding box is not under the circle. With a box-only test
    # this plant reads "covered"; the hub/badge pair in 04-react-loop is the real case.
    ("PLANT_ARC",
     '<svg %s><text x="250" y="112" fill="#0f172a" font-size="16">a badge beside the hub</text>'
     '<circle cx="200" cy="60" r="55" fill="#166534" opacity="0.9">'
     '<animate attributeName="opacity" values="0.9;1;0.9" dur="4s" repeatCount="indefinite"/>'
     '</circle></svg>' % G, "clean"),
    # The two arms of the burial test, planted on the two real cases this round measured:
    # a hub disc that nibbles one glyph forever (04-react-loop: 1/6 pts, 25 of 25 phases) is a z-order
    # defect even though 5/6 of the label reads; a playhead that sweeps the label for one phase
    # (17-action-chunking: 2/6 pts, 1 of 39 phases) is choreography, not a defect.
    ("PLANT_NIBBLE",
     '<svg %s><text x="10" y="66" fill="#0f172a" font-size="16">a badge nibbled forever</text>'
     '<circle cx="14" cy="60" r="6" fill="#ffffff" opacity="0.95">'
     '<animate attributeName="opacity" values="0.95;1;0.95" dur="4s" '
     'repeatCount="indefinite"/></circle></svg>' % G, "covered"),
    ("PLANT_SWEEP",
     '<svg %s><text x="10" y="66" fill="#0f172a" font-size="16">a label a playhead crosses once'
     '</text><rect x="10" y="46" width="4" height="30" fill="#0f172a">'
     '<animate attributeName="x" values="10;390" dur="4s" repeatCount="indefinite"/></rect></svg>'
     % G, "clean"),
    ("PLANT_UNPRICED",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="url(#nope)" opacity="0.9">'
     '<animate attributeName="opacity" values="0.5;1;0.5" dur="4s" repeatCount="indefinite"/></rect>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16" '
     '>white over a dangling server</text></svg>' % G, "unpriced"),
    # WCAG 1.4.3's own size test. All three plates are the SAME ink on the SAME amber (#ffffff on
    # #d97706 measures 3.19:1, which clears the large-text bar and not the small-text one), so the
    # only thing separating the verdicts is the rendered glyph size. selftest pins the host to the
    # viewBox width, so an authored px is a rendered px unless a plant's viewBox says otherwise.
    ("PLANT_TIER_SMALL",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#d97706"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;360;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16" '
     '>amber plate, 16px</text></svg>' % G, "dark"),
    ("PLANT_TIER_LARGE",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#d97706"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;360;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="160" y="72" text-anchor="middle" fill="#ffffff" font-size="24" '
     '>amber plate 24px</text></svg>' % G, "clean"),
    ("PLANT_TIER_BOLD",
     '<svg %s><rect x="10" y="40" width="300" height="40" fill="#d97706"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;360;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="160" y="70" text-anchor="middle" fill="#ffffff" font-size="20" font-weight="700" '
     '>amber 20 bold</text></svg>' % G, "clean"),
    # ...and the same authored size crossing back under the bar because the column shrinks it: a
    # 30px glyph authored into an 800-unit viewBox in a 400px host renders at 15px. Without the
    # viewBox scale this plant would read large and pass; the real figures all have this ratio.
    ("PLANT_TIER_SHRUNK",
     '<svg %s><rect x="10" y="40" width="380" height="46" fill="#d97706"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;760;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="200" y="72" text-anchor="middle" fill="#ffffff" font-size="30" '
     '>authored 30, rendered 15</text></svg>' % G800, "dark"),
    # The label's OWN paint can be a server too (the home banner's title is `fill="url(#titlec)"`).
    # Both directions get pinned: pricing it (a sweep whose darkest stop clears a white plate must
    # grade clean, not "unpriced") and NOT letting it off the hook (a sweep whose every stop is
    # low-contrast against its own plate must grade dark — exempting gradient ink would hide a real defect).
    ("PLANT_INK_GRAD_CLEAN",
     '<svg %s><defs><linearGradient id="igA" x1="0" y1="0" x2="1" y2="0">'
     '<stop offset="0%%" stop-color="#ffffff"/>'
     '<stop offset="100%%" stop-color="#0f172a"/></linearGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="#ffffff"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;360;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="18" y="66" font-size="16" fill="url(#igA)">gradient ink, dark stop wins</text></svg>'
     % G, "clean"),
    ("PLANT_INK_GRAD_DARK",
     '<svg %s><defs><linearGradient id="igB" x1="0" y1="0" x2="1" y2="0">'
     '<stop offset="0%%" stop-color="#94a3b8"/>'
     '<stop offset="100%%" stop-color="#cbd5e1"/></linearGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="#ffffff"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;360;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="18" y="66" font-size="16" fill="url(#igB)">gradient ink, no stop clears</text></svg>'
     % G, "dark"),
    # Two servers STACKED: a gradient ink over a gradient PLATE — the banner's own title (a url(#titlec)
    # heading on the url(#bgb) page wash). Reading `fill.rgb` of a url() ink as a colour crashed the
    # probe here, and a dead ruler is the one verdict it must never hand out: these two plants run the
    # composite path in both directions, so the crash and a wrongly-lenient pass are both caught.
    ("PLANT_INK_GRAD_ON_GRAD",
     '<svg %s><defs><linearGradient id="pgA" x1="0" y1="0" x2="0" y2="1">'
     '<stop offset="0%%" stop-color="#f8fafc"/>'
     '<stop offset="100%%" stop-color="#94a3b8"/></linearGradient>'
     '<linearGradient id="igC" x1="0" y1="0" x2="1" y2="0">'
     '<stop offset="0%%" stop-color="#cbd5e1"/>'
     '<stop offset="100%%" stop-color="#0f172a"/></linearGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="url(#pgA)"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;360;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="18" y="66" font-size="16" fill="url(#igC)">ink sweep over plate sweep</text></svg>'
     % G, "clean"),
    ("PLANT_INK_GRAD_ON_GRAD_DARK",
     '<svg %s><defs><linearGradient id="pgB" x1="0" y1="0" x2="0" y2="1">'
     '<stop offset="0%%" stop-color="#f1f5f9"/>'
     '<stop offset="100%%" stop-color="#e2e8f0"/></linearGradient>'
     '<linearGradient id="igD" x1="0" y1="0" x2="1" y2="0">'
     '<stop offset="0%%" stop-color="#e2e8f0"/>'
     '<stop offset="100%%" stop-color="#cbd5e1"/></linearGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="url(#pgB)"/>'
     '<circle cx="20" cy="16" r="5" fill="#0f172a">'
     '<animate attributeName="cx" values="20;360;20" dur="4s" repeatCount="indefinite"/></circle>'
     '<text x="18" y="66" font-size="16" fill="url(#igD)">both sweeps agree it is mud</text></svg>'
     % G, "dark"),
    # The pill case the favourable-stop rule used to wave through: a light-over-blue vertical sweep
    # whose DARK end clears 4.5 (5.17:1) while its middle, where a centred label actually sits, does
    # not (2.5:1). Under the old rule this graded clean; the banner's violet node is exactly this
    # shape. The next two plants pin that the general case is measured too, and pin the honest limit:
    # a diagonal sweep is now interpolated like any other (it is the house page wash under every
    # figure), while a `userSpaceOnUse` server still falls back to the favourable stop, marked
    # `approx`, because its axis is not in the element's box and guessing it is a wrong number.
    ("PLANT_GRAD_MID",
     '<svg %s><defs><linearGradient id="pmA" x1="0" y1="0" x2="0" y2="1">'
     '<stop offset="0%%" stop-color="#e0f2fe"/>'
     '<stop offset="100%%" stop-color="#2563eb"/></linearGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="url(#pmA)"/>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16">'
     'dark end clears, middle does not</text></svg>' % G, "dark"),
    ("PLANT_GRAD_DIAG",
     '<svg %s><defs><linearGradient id="pmB" x1="0" y1="0" x2="1" y2="1">'
     '<stop offset="0%%" stop-color="#e0f2fe"/>'
     '<stop offset="100%%" stop-color="#2563eb"/></linearGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="url(#pmB)"/>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16">'
     'diagonal: measured, not guessed</text></svg>' % G, "dark"),
    # Same stops, same label, same rect as PLANT_GRAD_MID — only the SERVER differs. Interpolating a
    # radial sweep along the linear axis defaults (which is what a naive reader of x1/y1/x2/y2 gets,
    # since a radialGradient has no such attributes) would invent a wrong horizontal sweep and grade
    # this `dark`. Refusing to interpolate marks it `approx` instead: an honest blind spot beats a
    # confident wrong number, and this plant is the difference between the two.
    ("PLANT_GRAD_RADIAL",
     '<svg %s><defs><radialGradient id="pmC" cx="50%%" cy="50%%" r="50%%">'
     '<stop offset="0%%" stop-color="#e0f2fe"/>'
     '<stop offset="100%%" stop-color="#2563eb"/></radialGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="url(#pmC)"/>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16">'
     'radial: not interpolated, approx</text></svg>' % G, "clean"),
    ("PLANT_GRAD_USERSPACE",
     '<svg %s><defs><linearGradient id="pmD" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="400" y2="0">'
     '<stop offset="0%%" stop-color="#e0f2fe"/>'
     '<stop offset="100%%" stop-color="#2563eb"/></linearGradient></defs>'
     '<rect x="10" y="40" width="340" height="40" fill="url(#pmD)"/>'
     '<text x="160" y="66" text-anchor="middle" fill="#ffffff" font-size="16">'
     'userSpace: not interpolated, approx</text></svg>' % G, "clean"),
]

# The two fallbacks must be proven by the row carrying `approx`, not by a clean verdict that could
# equally come from the ruler having ignored the server altogether; the measured ones must prove the
# opposite — that no point of their verdict was guessed.
GRAD_EXPECT = {"PLANT_GRAD_MID": 0, "PLANT_GRAD_DIAG": 0,
               "PLANT_GRAD_RADIAL": 1, "PLANT_GRAD_USERSPACE": 1}

# Each tier plant also asserts the size it rendered at and the bar that size selected, so a
# host/viewBox regression cannot silently move a label across the size line. (scale, px, bar key)
TIER_EXPECT = {"PLANT_TIER_SMALL": (1.0, 16, "small"), "PLANT_TIER_LARGE": (1.0, 24, "large"),
               "PLANT_TIER_BOLD": (1.0, 20, "large"), "PLANT_TIER_SHRUNK": (0.5, 15, "small")}


def grade(rep):
    """The verdict word for a plant, read off the same rows a real figure produces."""
    if "coverage" in rep:
        return "blind" if "BLIND" in rep["coverage"] else "no-reading"
    rows = rep["rows"]
    if any(r["buried"] for r in rows):
        return "covered"
    if not any(r["judged"] for r in rows):
        return "unpriced"          # the ruler never got a colour to price against
    dark = [r for r in rows if r["dark"]]
    if not dark:
        return "clean-fading" if any(r["fade"] and r["amin"] < 0.6 for r in rows) else "clean"
    return "phase-only" if any(r["phaseOnly"] for r in dark) else "dark"


def selftest(srv, args):
    args = argparse.Namespace(**vars(args))
    args.shots = 0
    # Plant at the size it is authored: the host is as wide as the plants' viewBox, so a 16px plant
    # is a 16px label and the tier plants test the size rule rather than the column rule.
    args.column = 400
    bad, rid = [], 900
    for name, src, want in PLANTS:
        rid += 1
        # The liveness gate costs a static plant its whole reading, so each plant is swept with its
        # own animate count -- the same predicate run() uses to pick the mode.
        rep = sweep(srv, name, src, args, rid, src.count("<animate"))
        got = grade(rep)
        ok = got == want
        extra = ""
        if name in TIER_EXPECT:
            w_scale, w_px, w_bar = TIER_EXPECT[name]
            w_bar_v = {"small": args.bar, "large": args.bar_large}[w_bar]
            rows = [r for r in rep.get("rows") or [] if r.get("judged")]
            r0 = rows[0] if rows else {}
            ok = (ok and rows and abs(rep.get("scale", 0) - w_scale) < 0.02
                  and abs(r0.get("px", 0) - w_px) < 1.0
                  and abs(r0.get("bar", 0) - w_bar_v) < 0.01)
            extra = "  rendered %spx -> bar %s (want %s) at scale %s" % (
                r0.get("px"), r0.get("bar"), w_bar_v, rep.get("scale"))
        if name.startswith("PLANT_INK_GRAD") and "coverage" not in rep:
            r = (rep.get("rows") or [{}])[0]
            # The verdict has to come from PRICING the ink sweep, not from skipping it: a judged row
            # with inkGrad>0 proves the branch ran, and the row names the stop the verdict rests on.
            ok = (ok and r.get("judged", 0) > 0 and r.get("inkGrad", 0) > 0
                  and r.get("ownGrad", 1) == 0 and r.get("inkRgb"))
            extra = ("  priced %d point(s) as gradient ink (worst %.2f, best %.2f) at stop rgb(%s)"
                     % (r.get("judged", 0), r.get("worst", 0), r.get("best", 0),
                        ",".join(str(v) for v in (r.get("inkRgb") or []))))
        if name in GRAD_EXPECT and "coverage" not in rep:
            r = (rep.get("rows") or [{}])[0]
            # The two plants differ ONLY in the sweep direction, so the verdicts alone cannot tell them
            # apart from a ruler that ignored every gradient plate. `approx` is the discriminator: the
            # axis-aligned sweep must be priced point by point (no guesses), the diagonal one must
            # fall back to the favourable stop and say so.
            want_guess = GRAD_EXPECT[name]
            guessed = r.get("approx", 0)
            judged = r.get("judged", 0)
            ok = (ok and judged > 0 and r.get("inkGrad", 0) == 0
                  and (1 if guessed > 0 else 0) == want_guess)
            extra = ("  %d/%d point(s) priced at the favourable stop, worst %.2f"
                     % (guessed, judged, r.get("worst", 0)))
        if name == "PLANT_FADE" and not ("coverage" in rep):
            r = (rep.get("rows") or [{}])[0]
            # `varying` is what earns the exemption at all: a label whose alpha never moves is
            # permanently translucent and must be judged, not exempted.
            ok = ok and r.get("fade", 0) > 0 and r.get("varying", 0) == 1 \
                and r.get("amin", 1) < args.presence
            extra = ("  exempted %d phase(s), alpha %.2f..%.2f, varying=%s"
                     % (r.get("fade", 0), r.get("amin", 0), r.get("amax", 0), r.get("varying")))
        if name == "PLANT_FADE_STATIC" and "coverage" not in rep:
            r = (rep.get("rows") or [{}])[0]
            # It must be judged BECAUSE nothing animates its alpha; a plant that got its verdict from
            # an exemption would prove the rule backwards.
            ok = ok and r.get("varying", 1) == 0 and r.get("fade", 1) == 0 and r.get("judged", 0) > 0
            extra = ("  alpha %.2f, varying=%s, exempted %d phase(s), judged %d"
                     % (r.get("amin", 0), r.get("varying"), r.get("fade", 0), r.get("judged", 0)))
        if name == "PLANT_NIBBLE" and "coverage" not in rep:
            # It must trip the duration arm specifically; if it tripped the fraction arm the plant
            # would be testing the wrong half of the rule.
            b = [r for r in rep["rows"] if r.get("buried")]
            ok = ok and b and b[0]["covFrac"] < args.buried and b[0]["covDur"] >= args.steady
            extra = "  caught by the duration arm (%.0f%% of phases, %.0f%% at once)" % (
                (b[0]["covDur"] if b else 0) * 100, (b[0]["covFrac"] if b else 0) * 100)
        if name == "PLANT_SWEEP" and "coverage" not in rep:
            # A clean verdict on a plant nobody ever clipped would prove nothing: the clip must be
            # measured and then exempted, so the bar is demonstrably above the transient case.
            m = max([r.get("cov", 0) for r in rep["rows"]] + [0])
            p = max([r.get("covPhases", 0) for r in rep["rows"]] + [0])
            ok = ok and m > 0 and p > 0
            extra = "  %d slot(s) clipped over %d phase(s), exempted" % (m, p)
        print("  selftest %-16s -> %-12s want %-12s %s%s"
              % (name, got, want, "ok" if ok else "FAIL", extra))
        if not ok:
            bad.append("%s graded %s, must be %s%s"
                       % (name, got, want, "; " + "; ".join(findings(rep, args))[:200]
                          if "coverage" not in rep else rep["coverage"]))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", default="", help="comma-separated substring filter")
    ap.add_argument("--mode", choices=("animated", "static", "all"), default="animated",
                    help="which half of the in-body figures to price (default: the animated half "
                         "round 69 measured; `static` is the 18 with no phase to sweep)")
    ap.add_argument("--bar", type=float, default=BAR,
                    help="contrast bar for WCAG small text (labelled individually per row)")
    ap.add_argument("--bar-large", type=float, default=BAR_LARGE,
                    help="contrast bar for WCAG large text (>=24px, or >=18.66px at weight>=700)")
    ap.add_argument("--presence", type=float, default=PRESENCE)
    ap.add_argument("--buried", type=float, default=BURIED,
                    help="share of a label's probe points a surface must hide to be a finding")
    ap.add_argument("--steady", type=float, default=STEADY,
                    help="share of the cycle one probe point must stay hidden to be a finding")
    ap.add_argument("--grid", type=int, default=GRID)
    ap.add_argument("--tick", type=int, default=TICK)
    ap.add_argument("--column", type=int, default=COLUMN)
    ap.add_argument("--height", type=int, default=1200)
    ap.add_argument("--shots", type=int, default=0,
                    help="freeze the ~Nth phase and screenshot it instead of sweeping")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default="", help="dump every label's rows here for triage")
    args = ap.parse_args(argv)
    global srv_port
    dummy = os.path.join(tempfile.gettempdir(), "phase-ruler.js")
    io.open(dummy, "w", encoding="utf-8").write("// no bundle\n")
    srv = Server(js_path=dummy)
    os.remove(dummy)
    srv_port = [srv.port]
    try:
        if args.selftest:
            bad = selftest(srv, args)
            print("SELFTEST %s" % ("ok (%d/%d plants graded right)" % (len(PLANTS), len(PLANTS))
                                   if not bad else "problems=%d" % len(bad)))
            for b in bad:
                print("  " + b)
            return 1 if bad else 0
        return run(srv, args)
    finally:
        srv.srv.shutdown()


def run(srv, args):
    figures = animated_figures(args.mode)
    floor = {"animated": MIN_FIGURES, "static": MIN_STATIC, "all": MIN_FIGURES + MIN_STATIC}[args.mode]
    if args.assets:
        needles = [s.strip().lower() for s in args.assets.split(",") if s.strip()]
        figures = [f for f in figures if any(n in f[0].lower() for n in needles)]
    if not figures:
        print("PHASE AXIS: no %s figure matched %r — a vacuous reading, not a pass"
              % (args.mode, args.assets))
        return 1
    if not args.shots and len(figures) < floor:
        print("PHASE AXIS: only %d %s figures found (floor %d) — detection broke, that is not "
              "cleanliness" % (len(figures), args.mode, floor))
        return 1
    print("phase axis: %d %s figures, bar %.2f small / %.2f large (WCAG 1.4.3), "
          "presence %.2f (only for labels whose own alpha varies), grid %d, column %dpx"
          % (len(figures), args.mode, args.bar, args.bar_large, args.presence, args.grid, args.column))
    content, cover, nlabels, nphase, nunpriced = [], [], 0, 0, 0
    njudged = nguessed = 0
    kind = {"pat": 0, "grad": 0, "ink": 0}
    dump = {}
    tally = {"PHASE-ONLY": 0, "DARK": 0, "COVERED": 0}
    for i, (name, na) in enumerate(figures):
        src = io.open(os.path.join(ASSETS, name), encoding="utf-8").read()
        rep = sweep(srv, name, src, args, i + 1, na)
        if args.shots:
            print("  %-34s shot t=%-6s -> %s %s" % (name, rep.get("shot_at"), rep["shot"],
                                                    "ok" if os.path.exists(rep["shot"]) else "MISSING"))
            continue
        if "coverage" in rep:
            cover.append(rep["coverage"])
            print("  %-34s %2d animate  COVERAGE" % (name, na))
            continue
        fs = findings(rep, args)
        nlabels += rep["labels"]
        nphase += rep["phases"]
        # How much of this figure's verdict rests on a favourable-stop guess. A pass with guesses is
        # not the same claim as a pass measured point by point, so the number goes on the line.
        judged = sum(r["judged"] for r in rep["rows"])
        guessed = sum(r["approx"] for r in rep["rows"])
        njudged += judged
        nguessed += guessed
        for k, v in (("pat", "approxPat"), ("grad", "approxGrad"), ("ink", "approxInk")):
            kind[k] += sum(r.get(v, 0) for r in rep["rows"])
        unpriced = sum(1 for r in rep["rows"] if r["judged"] == 0 and r["onGrad"])
        nunpriced += unpriced
        for r in rep["rows"]:                     # an unpriceable label must never read as a pass
            if r["judged"] or not r["onGrad"]:
                continue
            by = r.get("unpricedBy") or ["?", -1, "", ""]
            cover.append("%-34s UNPRICED    %-26s never priced (paint server %s resolves to nothing "
                         "under it)  [label %s#%d %s]"
                         % (name, esc(r["text"]), by[2] if len(by) > 2 else "?",
                            by[0], by[1] if len(by) > 1 else -1,
                            by[3] if len(by) > 3 else "no authored literal"))
        dump[name] = {"labels": rep["labels"], "phases": rep["phases"], "rows": rep["rows"]}
        for r in fs:
            tally[r.split()[0]] = tally.get(r.split()[0], 0) + 1
            content.append("%-34s %s" % (name, r))
        print("  %-34s %2d animate  %2d labels x %2d phases | %d dark, %d covered, %d unpriced "
              "| %d judged pt, %d guessed"
              % (name, na, rep["labels"], rep["phases"],
                 sum(1 for r in rep["rows"] if r["dark"]),
                 sum(1 for r in rep["rows"] if r["buried"]), unpriced, judged, guessed))
    if args.shots:
        return 0
    if args.json:
        io.open(args.json, "w", encoding="utf-8").write(json.dumps(dump, ensure_ascii=False))
    print("\nfindings: %d label(s) across %d figure(s) — %d phase-only, %d steady-dark, "
          "%d covered; coverage %d; labels left unpriced %d"
          % (len(content), len({c.split()[0] for c in content}),
             tally.get("PHASE-ONLY", 0), tally.get("DARK", 0), tally.get("COVERED", 0),
             len(cover), nunpriced))
    for c in content:
        print("  " + c)
    for c in cover:
        print("  COVERAGE  " + c)
    print("swept %d labels over %d phases total (bar %.2f); %d judged probe point(s), of which "
          "%d (%.1f%%) were priced at a favourable stop rather than measured"
          % (nlabels, nphase, args.bar, njudged, nguessed,
             nguessed * 100.0 / njudged if njudged else 0))
    print("  guesses by kind (a point can carry more than one): pattern plate %d, "
          "non-interpolable gradient plate %d, gradient ink %d"
          % (kind["pat"], kind["grad"], kind["ink"]))
    return 1 if (content or cover) else 0


if __name__ == "__main__":
    sys.exit(main())
