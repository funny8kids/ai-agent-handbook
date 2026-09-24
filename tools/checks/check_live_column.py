# -*- coding: utf-8 -*-
"""Live content-column axis: is the width the Mermaid geometry axis assumes the width a reader gets?

Why this file exists (round 62). check_mermaid_geometry.py has judged all 217 diagrams against
`COLUMN = 1120` since round 58, and docs/README.md claims the widest one (1116px) "线上不会被缩放".
1120 is exactly max-w-6xl (1152) minus padding, i.e. the WIDE layout. Measured live, the space
publishes `<main class="... max-w-3xl layout-wide:max-w-6xl ... layout-default">`: a reader in the
default layout gets 768px, so every diagram between 769 and 1116px is being scaled down by the
browser (round 27 measured the consequence once already: "缩到 42%，16px 的字只剩 6.7px").

Two things are measured, because they answer different questions:
  asis    the column the reader gets right now, at several window widths.
  +wide   what the column would become if the space were switched to GitBook's wide layout. This
          is an A/B on a COPY of the live page with the site's own `layout-wide` class added to
          the ancestors of <main>; the site's CSS does the work, nothing is hand-styled. If the
          number does not move, the variant is anchored somewhere else and the toggle is the only
          way to know - that is reported as a null, not as a pass.

Guards, each of which caught a real reading while this file was written:
  * control box 500px  -> must read ~500. A selector scoped to `main` on a page without `<main>`
    returned 0 and looked like "a clean page with nothing in it".
  * control box 1600px -> must read ~1600. Without this, "every page reads 768" would also be
    consistent with a ruler that clamps whatever it measures to one number.
  * spread across pages must be small, or the measurement is landing on a child element, not on
    the column.
  * a page that never hydrates is a harness failure, not a verdict (round 56: Mermaid containers
    stay aria-busy in this sandbox, so nothing here waits for a diagram to paint).
  * round 73 added the hydrated live leg (`hydrated_leg`), because the copy leg has a structural
    blind spot: the site's client router has no route for a localhost file name, so a copy renders
    the article with no chapter sidebar and no page TOC beside it, and <main> gets its full 768px
    cap. On the live URL those two panels (288px + 256px) are open by default and the same window
    leaves the article 608px. Both numbers are printed; the gap is an `AWAITING-DECISION` line, not
    a problem this axis can fix by editing itself.
  * round 73 also fixed a contamination bug of its own making: measurement order matters. A probe
    that plants a 960px control box inside a figure's own wrapper stretches that shrink-to-fit
    wrapper, and the figure measured afterwards then reads natural-size instead of column-size -
    which is how "GitBook hands wide figures a horizontal scrollbar" got reported once before being
    caught. `HYDRATED_PROBE` therefore reads the page first and plants its controls last.

Usage:
    python tools/checks/check_live_column.py
    python tools/checks/check_live_column.py --pages 5 --assume 1120
    python tools/checks/check_live_column.py --no-hydrated      # Edge/copy leg only
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_widget_visibility_live as wl            # noqa: E402  llms.txt index + retrying fetch
from check_mermaid_geometry import (COLUMN, EDGE_CANDIDATES, Server)  # noqa: E402  assumption under test

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
VIEWPORTS = [1024, 1280]        # the widest window this sandbox can actually get (see `run`)
SPREAD_TOL = 16                 # px of disagreement between pages before the selector is suspect
# Why 1024/1280 is enough: the cap being tested (max-w-3xl = 768px, max-w-6xl = 1152px) is a
# CSS max-width, so once the window is wider than the cap the reading is the cap and is the same
# for a 1440 or 1920 reader. Measured here, requests above ~1280 come back as innerWidth 1250,
# so a "column at vw=1920" printed from this machine would be a fabricated viewport.
WIDE_NEEDS = 1152 + 520         # a window this wide is needed before max-w-6xl could bind here
# The breakpoints a reader actually arrives at. Read off the LIVE page rather than a copy, because a
# copy is measured with the site's client router unable to resolve a localhost file name: round 73
# found the copy renders the article with no navigation furniture beside it, so <main> gets its full
# 768px cap there, while the live page at the same window puts a 288px chapter sidebar and a 256px
# page TOC beside the article and leaves it 608px. `is_mobile` is the phone case the Edge leg cannot
# ask for at all (this sandbox's Edge clamps innerWidth at ~504px minimum).
HYDRATED_AT = [(1024, False), (1280, False), (1440, False), (1920, False), (390, True)]


def probe_script(rid, port, modes, min_paragraphs=4):
    """Measure the column once per mode. `modes` is a list of (name, add-layout-wide?)."""
    return """
<script>
(function () {
  var RID = %r, API = 'http://127.0.0.1:%d', MODES = %s, MINP = %d;
  function w(el) { return el ? Math.round(el.getBoundingClientRect().width) : null; }
  function root() { return document.querySelector('main'); }
  function measure() {
    var m = root();
    if (!m) return null;
    var ps = m.querySelectorAll('p'), widest = 0;
    for (var i = 0; i < ps.length; i++) { var x = w(ps[i]); if (x > widest) widest = x; }
    // The control page authors two boxes on purpose: one narrow, one wide. Reading them
    // separately is what proves the ruler is not returning one number for everything.
    var ctl = {};
    [].forEach.call(document.querySelectorAll('[data-ctl]'), function (e) {
      ctl[e.getAttribute('data-ctl')] = w(e);
    });
    return {para: widest, main: w(m), paragraphs: ps.length, ctl: ctl,
            h1: w(m.querySelector('h1')),
            caps: String(m.className).replace(/\\s+/g, ' ').slice(0, 220)};
  }
  function setWide(on) {
    if (!on) return;
    // the site's own variant selector is `layout-wide:`; it is authored as an ancestor class, so
    // add it where an ancestor lives. Nothing is styled by hand.
    [document.documentElement, document.body].forEach(function (n) {
      if (n) { n.classList.add('layout-wide'); }
    });
    var m = root();
    if (m) { m.classList.add('layout-wide'); if (m.parentElement) m.parentElement.classList.add('layout-wide'); }
  }
  function report(extra) {
    var out = {id: RID, done: true, viewport: [innerWidth, innerHeight], modes: extra};
    var x = new XMLHttpRequest();
    x.open('POST', API + '/report', false); x.send(JSON.stringify(out));
    var h = new XMLHttpRequest(); h.open('GET', API + '/hold?rid=' + RID, false);
    try { h.send(); } catch (e) {}
  }
  var tries = 0;
  function poll() {
    var first = measure();
    // A live page is only "hydrated enough" when it has prose; a control page has one paragraph
    // by construction, so the threshold is a parameter rather than a constant.
    if (first && first.para > 0 && first.paragraphs >= MINP) {
      var got = {}, wideMarked = null;
      MODES.forEach(function (mode) {
        setWide(mode[1]);
        var m = measure();
        // reflow is synchronous for getBoundingClientRect, but the class change may need a frame
        got[mode[0]] = m;
        if (mode[1]) wideMarked = /layout-wide/.test(String(root().parentElement.className));
      });
      report(Object.keys(got).map(function (k) {
        return {mode: k, mark: wideMarked, m: got[k]};
      }));
      return;
    }
    if (tries++ > 20) { report([]); return; }
    setTimeout(poll, 500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', poll);
  else poll();
})();
</script>
""" % (rid, port, json.dumps(modes), min_paragraphs)


def fixture(inject):
    """A page we author, carrying the same probe the live pages carry.

    A control that does not run the real measurement code is not a control: an earlier revision of
    this function built the boxes but never injected the script, so a beacon-less run could only
    pass by reading someone else's report.
    """
    return ("<html><head><style>main{display:block} .box{margin:0}</style></head><body>"
            "<main><div class='box' data-ctl='narrow' style='width:500px'><p>paragraph one</p>"
            "<p>paragraph two</p><p>paragraph three</p><p>paragraph four</p></div>"
            "<div class='box' data-ctl='wide' style='width:1100px'><p>wide control paragraph</p></div>"
            "</main>" + inject + "</body></html>")


def live_copy(html, site, inject):
    html = re.sub(r"<head[^>]*>", lambda m: m.group(0) + '<base href="%s/">' % site, html, count=1)
    html = re.sub(r'\b(src|href)="(/[^"]*)"', lambda m: '%s="%s%s"' % (m.group(1), site, m.group(2)), html)
    return html.replace("</body>", inject + "</body>", 1)


def diagram_pages(n):
    """Local pages that author Mermaid, mapped to live URLs through the site's own index."""
    entries = wl.llms_entries()
    index, ambiguous = wl.page_index(entries)
    assert not ambiguous, "ambiguous published titles make the title join unsafe: %s" % sorted(ambiguous)
    by_title = {wl.norm(t): u for t, u in entries}
    out = []
    for dirpath, _, filenames in os.walk(wl.DOCS):
        if "14-templates" in dirpath.replace("\\", "/"):
            continue
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            text = io.open(path, encoding="utf-8").read()
            if not re.search(r"^```mermaid", text, flags=re.M):
                continue
            m = re.search(r"^# (.+)$", text, flags=re.M)
            if not m:
                continue
            url = index.get(wl.norm(m.group(1).strip()))
            if url:
                out.append((path.replace(wl.DOCS + os.sep, "").replace("\\", "/"),
                            url[:-3] if url.endswith(".md") else url))
    assert len(out) >= n, "vacuity: only %d Mermaid pages resolved to a live URL" % len(out)
    return out[:n], len(out)


def shoot(srv, name, vw, height=1200):
    """One Edge run with EXACTLY one --window-size.

    Server.edge passes its own --window-size before `extra`, and Chromium does not
    reliably take the later one: a control box authored at 1600px came back measuring 1250px, i.e.
    the viewport we thought we asked for. A column read at the wrong viewport is a fabricated
    number, so this axis owns its browser flags and then asserts on innerWidth (see `run`).
    """
    exe = next((p for p in EDGE_CANDIDATES if os.path.isfile(p)), None)
    if not exe:
        raise SystemExit("no Microsoft Edge found - the column axis needs a real renderer")
    cmd = [exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
           "--user-data-dir=" + srv.new_profile(), "--window-size=%d,%d" % (vw, height),
           srv.url(name)]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run(srv, name, vw, rid, timeout=70):
    proc = shoot(srv, name, vw)
    rep = srv.wait(rid, timeout, proc)
    Server.stop(proc)
    if rep and rep.get("viewport"):
        got = rep["viewport"][0]
        # headless reserves a scrollbar gutter; anything bigger means we measured another viewport
        assert vw - 60 <= got <= vw + 5, "asked for vw=%d, browser reported %d" % (vw, got)
    return rep


HYDRATED_PROBE = r"""
() => {
  const w = el => Math.round(el.getBoundingClientRect().width);
  const main = document.querySelector('main');
  if (!main) return null;
  let para = 0;
  for (const p of main.querySelectorAll('p')) para = Math.max(para, w(p));
  const panels = [...document.querySelectorAll('aside,nav')].filter(e => w(e) > 40)
      .map(e => e.tagName.toLowerCase() + '.' +
                String(e.className).split(/\s+/)[0] + '=' + w(e) +
                (e.getAttribute('aria-label') ? '(' + e.getAttribute('aria-label') + ')' : ''));
  const phantom = !!document.getElementById('r73-no-such-element');
  // The controls are planted AFTER the reading above, and that order is load-bearing: in round 73 a
  // 960px control appended into a figure's own wrapper stretched that shrink-to-fit wrapper to 960,
  // and the figure measured beside it then read natural-size instead of column-size. A ruler that
  // contaminates what it measures is worse than one that is blind.
  const ctl = {};
  for (const px of [200, 960]) {
    const d = document.createElement('div');
    d.style.cssText = 'width:' + px + 'px;height:6px';
    main.appendChild(d);
    ctl['plant-' + px] = w(d);
    d.remove();
  }
  return {vw: innerWidth, main: w(main), para: para, panels: panels, ctl: ctl, phantom: phantom};
}
"""


def hydrated_leg(urls):
    """Read the column off the LIVE page as the reader's browser lays it out, per breakpoint.

    Returns (rows, note). `rows` is {vw: [reading per page]}; `note` is a harness limit that must be
    printed rather than swallowed - a leg that quietly returns nothing reads as "no problem found".
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {}, "playwright is not installed, so the hydrated live column could not be read"
    rows = {}
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        try:
            for vw, mobile in HYDRATED_AT:
                got = []
                for rel, url in urls:
                    ctx = br.new_context(viewport={"width": vw, "height": 900}, is_mobile=mobile,
                                         device_scale_factor=3 if mobile else 1)
                    pg = ctx.new_page()
                    try:
                        pg.goto(url, wait_until="networkidle", timeout=90000)
                    except Exception as exc:
                        print("  hydrated %s @%d: load failed (%s)" % (rel, vw, str(exc)[:60]))
                        ctx.close()
                        continue
                    pg.wait_for_timeout(2500)      # GitBook lays the panels out after hydration
                    rep = pg.evaluate(HYDRATED_PROBE)
                    ctx.close()
                    if not rep:
                        print("  hydrated %s @%d: no <main> laid out" % (rel, vw))
                        continue
                    # Playwright sets the viewport exactly, so a reading from another window width is
                    # a bug rather than a browser clamp: this leg must not inherit the Edge excuse.
                    assert abs(rep["vw"] - vw) <= 3, "asked for vw=%d, page reported %d" % (vw, rep["vw"])
                    assert abs(rep["ctl"]["plant-200"] - 200) <= 2 and \
                        abs(rep["ctl"]["plant-960"] - 960) <= 2, \
                        "the ruler clamps: planted 200/960 boxes read %s" % rep["ctl"]
                    assert not rep["phantom"], "a phantom element id matched on the live page"
                    rep["page"] = rel
                    got.append(rep)
                if got:
                    rows[vw] = got
        finally:
            br.close()
    return rows, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=3)
    print("note: this sandbox's Edge clamps innerWidth at ~1250px, so a vw=1920 reading cannot be"
          " faked here; the caps under test are CSS max-widths, which are viewport-independent once"
          " the window is wider than the cap.")
    ap.add_argument("--assume", type=int, default=COLUMN,
                    help="the column the Mermaid geometry axis assumes (check_mermaid_geometry.COLUMN)")
    ap.add_argument("--all-viewports", action="store_true")
    ap.add_argument("--no-hydrated", action="store_true",
                    help="skip the live-page leg (Playwright); the copy leg alone cannot see the "
                         "navigation panels that squeeze a reader's column")
    args = ap.parse_args()
    viewports = VIEWPORTS + [1280, 2560] if args.all_viewports else VIEWPORTS

    modes = [("asis", False), ("wide", True)]
    dummy = os.path.join(tempfile.gettempdir(), "livecol-none.js")
    io.open(dummy, "w", encoding="utf-8").write("// the column axis loads no engine\n")
    srv = Server(js_path=dummy)
    rid = 0
    try:
        # ---- guards on our own ruler -------------------------------------------------
        rid += 1
        name = "col-ctl-%d.html" % rid
        ctl_probe = probe_script(rid, srv.port, modes, min_paragraphs=4)
        io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(fixture(ctl_probe))
        rep = run(srv, name, 1280, rid)
        assert rep and rep["modes"], "control run reported nothing - the harness is broken, not the site"
        boxes = {m["mode"]: m["m"].get("ctl", {}) for m in rep["modes"] if m["m"]}
        assert boxes.get("asis", {}).get("narrow") == 500, "ruler is blind: 500px box read %s" % boxes
        # the wide box is what a clamping ruler would fail: same code path, authored 1100
        assert boxes["asis"].get("wide") == 1100, "ruler clamps: 1100px box read %s" % boxes
        print("controls ok: one probe read a 500px box as %s and an 1100px box as %s - the column "
              "number below is a reading, not what the ruler returns for everything"
              % (boxes["asis"]["narrow"], boxes["asis"]["wide"]))

        # ---- the live site -----------------------------------------------------------
        pages, total = diagram_pages(args.pages)
        print("pages=%d (of %d Mermaid pages resolvable through llms.txt) viewports=%s assume=%dpx"
              % (len(pages), total, viewports, args.assume))
        asis, wide = {}, {}
        problems = []
        for rel, url in pages:
            html = wl.fetch(url) if url.startswith("http") else wl.fetch(wl.SITE + "/" + url)
            for vw in viewports:
                rid += 1
                name = "col-live-%d.html" % rid
                io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(
                    live_copy(html, wl.SITE, probe_script(rid, srv.port, modes)))
                rep = run(srv, name, vw, rid)
                if not rep or not rep["modes"]:
                    problems.append("NOHYDRATE %s @%d (harness/CDN, not a content verdict)" % (rel, vw))
                    continue
                m = {e["mode"]: e for e in rep["modes"]}
                if not m.get("asis", {}).get("m"):
                    problems.append("EMPTY %s @%d viewport=%s" % (rel, vw, rep["viewport"]))
                    continue
                a, wd = m["asis"]["m"]["para"], (m.get("wide") or {}).get("m", {}).get("para")
                asis.setdefault(vw, []).append((rel, a))
                wide.setdefault(vw, []).append((rel, wd))
                print("  %-46s vw=%-5d column=%-5s wide-layout=%-5s main=%s ps=%s"
                      % (rel, rep["viewport"][0], a, wd, m["asis"]["m"]["main"],
                         m["asis"]["m"]["paragraphs"]))

        # ---- the same site, laid out by the reader's own browser ----------------------
        hyd, hyd_note = {}, None
        if not args.no_hydrated:
            hyd, hyd_note = hydrated_leg(pages)
            print("\nhydrated live leg: %d breakpoints read on the live URL (no copy involved)"
                  % len(hyd))
            for vw in sorted(hyd):
                vals = [r["para"] for r in hyd[vw]]
                r0 = hyd[vw][0]
                print("  vw=%-5d column=%-5s (pages: %s)  panels beside the article: %s"
                      % (vw, sorted(set(vals)), len(vals), "; ".join(r0["panels"][:3])))
    finally:
        srv.srv.shutdown()

    print("\n-- verdict --")
    low = None
    for vw, rows in sorted(asis.items()):
        vals = [v for _, v in rows]
        spread = max(vals) - min(vals)
        status = "OK" if spread <= SPREAD_TOL else "SPREAD"
        print("  vw=%-5d column=%s spread=%dpx selector=%s" % (vw, sorted(set(vals)), spread, status))
        if status == "SPREAD":
            problems.append("SPREAD vw=%d columns=%s (measuring a child, not the column)" % (vw, vals))
        low = min(vals) if low is None else min(low, min(vals))
    if low is None:
        print("  no live reading at all -> refusing to report a pass")
        return 2
    print("  narrowest reader column measured: %dpx; geometry axis assumes %dpx" % (low, args.assume))

    # ---- copy vs live, and the phone case -------------------------------------------
    # Reported rather than counted as a problem: this axis now sees both numbers, and closing the gap
    # is a content/product decision (redraw the figures for a narrower column, or switch the space to
    # GitBook's wide layout) and not something the ruler can fix by editing itself. What it must not
    # do is go quiet - a green with no mention of the narrower column would let every downstream axis
    # keep certifying against the wider one.
    advisories = []
    if hyd_note:
        print("  hydrated leg skipped: %s" % hyd_note)
    desktop = [vw for vw, mobile in HYDRATED_AT if not mobile]
    for vw in sorted(desktop):
        if vw not in hyd:
            continue
        h = min(r["para"] for r in hyd[vw])
        print("  live desktop vw=%-5d reader column=%d" % (vw, h))
        if vw in asis:
            c = min(v for _, v in asis[vw])
            if c - h > SPREAD_TOL:
                advisories.append(
                    "COPY-OPTIMISTIC vw=%d: the copy lays the article out at %dpx while the live page"
                    " gives its reader %dpx (%dpx eaten by the navigation panels) - an axis that reads"
                    " the copy over-states the reader's room by that much" % (vw, c, h, c - h))
    for vw, mobile in HYDRATED_AT:
        if mobile and vw in hyd:
            print("  phone vw=%-5d reader column=%s (pinch-zoom belongs to the reader, so this is"
                  " context rather than a bar)" % (vw, sorted({r["para"] for r in hyd[vw]})))

    for vw, rows in sorted(wide.items()):
        vals = [v for _, v in rows if v]
        base = sorted({v for _, v in asis[vw]})
        if vals and max(vals) > max(base) + SPREAD_TOL:
            print("  wide layout at vw=%d would give %s (vs %s as-is)" % (vw, sorted(set(vals)), base))
        elif vals:
            print("  wide layout at vw=%d did not widen the column here (%s) -> the toggle still has"
                  " to be tested in the editor" % (vw, sorted(set(vals))))
    if low < args.assume:
        problems.append("COLUMN-MISMATCH: readers get %dpx but the Mermaid axis assumes %dpx -> "
                        "re-run it with --column %d" % (low, args.assume, low))
    for p in problems:
        print("  -", p)
    for a in advisories:
        print("  AWAITING-DECISION:", a)
    print("problems=%d  awaiting-decision=%d" % (len(problems), len(advisories)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
