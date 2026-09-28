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
  * round 73 added the hydrated live leg (`hydrated_leg`), because a copy has a structural blind
    spot: <main> can be laid out beside navigation panels that only the live URL mounts. Round 73
    measured that as copy=768 vs live=608 and blamed the site's client router; round 82's engine
    swap showed the copy mounts both panels too (see the COPY_VIEWPORT ladder), so the gap that day
    was a *scrollbar gutter*, and the copy at a 1280 window reads 15px narrower than the live page
    rather than 160px wider. Both numbers are still printed, and they are now cross-checked against
    each other (`COPY-NOT-LIVE`), because a copy that stops matching the live page is the failure
    this leg exists to catch.
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
from check_mermaid_geometry import (COLUMN, COLUMN_PHONE, LABEL_BAR, Server, browser,
                                    headless_flags)  # noqa: E402  assumptions under test

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
SPREAD_TOL = 16                 # px of disagreement between pages before the selector is suspect
_WINDOW_NOTES = set()           # (asked, got) pairs already printed this run

# ---------------------------------------------------------------- the copy's column (round 82)
# Round 73 wrote down that a copy of a live page lays the article out at its full 768px cap, because
# the site's client router cannot resolve a localhost file name and so never mounts the 288px chapter
# sidebar and the 256px page TOC beside it. That was an ENGINE reading, not a property of copies: on
# the sentinel-checked chromium shell the same copy mounts both panels. The ladder below is what
# proved it — `<main>` of a copy of `00-index/learning-path.md`, one browser run per row, every row
# confirmed by the page's own reported `innerWidth`:
#     asked vw    copy <main>   live <main>   copy - live
#     1024        609           624           -15
#     1280        593           608           -15
#     1440        753           768           -15
#     1455        768            -             the cap binds here, 15px above where it binds live
#     1500        768            -
#     1600        768            -
# So a copy is the live page minus a 15px classic-scrollbar gutter at every window, and `max-w-3xl`
# (768px) binds on a copy only from 1455px up. Two consequences, both of which a leg that asks a
# 1280 window and asserts 768 gets wrong:
#   * a reader on a 1280-wide laptop gets 608px (or 593 with a classic scrollbar), not 768;
#   * a leg that measures a COPY and asserts the 768 cap must ask a window where the cap can bind at
#     all, and must say which window it asked. That window is COPY_VIEWPORT, and every downstream
#     axis that lays a reader page out now renders at it.
# The old excuse for not asking wider ("this sandbox's Edge clamps innerWidth at ~1250px") is gone
# for the shell: chrome-headless-shell honours `--window-size` to the pixel, measured above. But the
# candidate list puts Edge first, so whenever Edge answers the sentinel *it* runs the ladder — and
# round 101 measured what it does to the flag (`--headless=new`, each size twice):
#     asked vw    Edge reported innerWidth    delta
#     1024        994                         -30
#     1280        1250                        -30
#     1500        1470                        -30
#     1600        1570                        -30
# A deterministic 30px reserve, not a clamp at ~1250 — wide windows work on Edge too. What does not
# hold is asserting the flag value as the viewport: that assertion measures which engine the suite
# happened to pick, so `confirm_window` reads the page's own report and prints the reserve.
#
# Round 104 found the half of that reasoning that was still wrong. Tolerating the reserve is not the
# same as neutralising it: the ladder keyed every copy reading by the width it ASKED, so on Edge an
# asked 1024 became a reading of a 994px page and an asked 1280 a 1250px page. Both sit under
# GitBook's own sidebar breakpoints, and the navigation that spends 400px/672px at 1024/1280 partly
# unmounts below them, so <main> falls through to its 768 cap. Those were the readings this round
# started from (copy leg keyed by ASKED width, live leg keyed by the reader's window):
#     asked vw    copy: window / container / main / mounted sheets    live: window / container / main / sheets
#     1024        994  / 979   / 768 / 0                              1024 / 1024  / 624 / 1 (288)
#     1280        1250 / 1235  / 768 / 1 (288)                        1280 / 1280  / 608 / 2 (288+256)
#     1500        1470 / 1455  / 768 / 2 (288+256)                    1440 / 1440  / 768 / 2 (288+256)
# `<main>` is `flex-basis: 0; max-width: 768px`, and its flex line - not its own parent, which is
# `display: contents` and therefore 0px wide - carries `max-width: 1440px`. So the column is the LINE
# minus what the line's other children spend, capped, and that is what the axis now measures and
# prints on both legs (`flexLine`/`lineWidth` in CENSUS_JS). After the fix, same page, both legs:
#     window      copy: line / main / spent by chrome   live: line / main / spent by chrome
#     1024        1009 / 609 / 400                      1024 / 624 / 400
#     1280        1265 / 593 / 672                      1280 / 608 / 672
#     1500        1440 / 768 / 672 (cap binds)          1440 / 768 / 672 (cap binds)
# The chrome spends the identical 400px/672px on both sides at a matched window, and the only
# difference left is the 15px the copy's own classic scrollbar takes out of the line (1009 = 1024-15,
# 1265 = 1280-15; at 1500 both lines are the same 1440 because the cap binds before the gutter does).
# That is "a copy is the live page minus a scrollbar" restated as a mechanism - round 82 measured it
# correctly on chrome-headless-shell, which honours the flag, and it broke the moment round 101 let
# Edge answer the sentinel. The fix is to ask for `vw + reserve` so the page lays out at the reader's
# width, and to refuse a reading whose reported window is not that width - never to compare across a
# breakpoint. And `window - column` must not be called the navigation cost: at vw=1920 that would
# blame 1152px on the chrome when the line it lives in only ever had 672px to spend.
COPY_VIEWPORT = 1500
COPY_CAP_BINDS_AT = 1455          # the narrowest reported window at which a copy's <main> reaches 768
WINDOW_CLAMP_SLACK = 60           # widest asked-vs-reported gap any engine used here produces (Edge: 30)

# The ladder the copy leg walks: the two laptop windows, and the window where the cap binds. Asking
# only the narrow ones is how this axis spent 20 rounds reporting a copy column it never re-checked
# against the live page.
VIEWPORTS = [1024, 1280, COPY_VIEWPORT]

WIDE_NEEDS = 1152 + 520         # a window this wide is needed before max-w-6xl could bind here
# The breakpoints a reader actually arrives at, read off the LIVE page, and they must include every
# width the copy ladder lays out: a copy is only evidence about a page once a live reading exists at
# the SAME window (see the round-104 table above - the two legs agree to the 15px gutter once they
# meet, and disagree by 160px when one of them has quietly fallen a breakpoint band lower). 1500 is
# in the list for exactly that reason: it is the window every copy-based downstream leg renders at,
# so it is the one width the "is the copy faithful?" verdict has to be argued at on the live page.
# `is_mobile` is the phone case, which the CLI flag set cannot ask for at all.
#
# And a copy must not be screenshotted to "eyeball the premise": round 82 shot one and got GitBook's
# own error boundary ("This page couldn't load", Reload/Back) instead of the article — the bundle
# throws once it hydrates on a copied URL. The copy's numbers survive that because the probe runs
# earlier, on the server-rendered DOM (which is also why `check_svg_legibility` beacons a `fatal`).
# Eyeball evidence for a reader's column has to come from the live page.
HYDRATED_AT = [(1024, False), (1280, False), (1440, False), (COPY_VIEWPORT, False), (1920, False),
               (390, True)]


# The same DOM census runs on both legs, so a copy's column and the live column are comparable down
# to the element that owns the difference. Authored without backslashes: this block is pasted into a
# %-formatted template and into the Playwright probe, and a `\s` would have to be escaped differently
# in each.
CENSUS_JS = """
  function panels() {
    var out = [], all = document.querySelectorAll('aside,nav');
    for (var i = 0; i < all.length; i++) {
      var e = all[i], x = w(e);
      if (x > 40) out.push(e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0]
                            + '=' + x + '/' + getComputedStyle(e).position);
    }
    return out;
  }
  function chain(m) {
    var out = [], n = m, depth = 0;
    while (n && n.tagName && depth < 8) {
      var cs = getComputedStyle(n);
      out.push(n.tagName.toLowerCase() + '.' + String(n.className).split(' ')[0]
               + ' w=' + w(n) + ' max=' + cs.maxWidth + ' pos=' + cs.position
               + ' basis=' + cs.flexBasis);
      n = n.parentElement; depth++;
    }
    return out;
  }
  // `<main>` is basis-0 with a 768 cap, so the reader's column is the line minus what its siblings
  // spend. `siblings` names the DOM-level neighbours; `flexLine` finds the box whose width actually
  // gets divided up, which is the part `vw - column` gets wrong.
  // The flex line that owns <main>. It is NOT main's own parent: the wrappers between them are
  // `display: contents`, which puts a child into the grandparent's layout and leaves the wrapper
  // itself 0px wide. And that line carries `max-width: 1440px`, so at vw=1920 the reader's window
  // is not what gets divided up - `vw - column` would blame 1152px on the navigation when the line
  // only ever had 672px to spend.
  function flexLine(m) {
    var n = m ? m.parentElement : null;
    while (n && n.tagName !== 'BODY') {
      if (getComputedStyle(n).display.indexOf('flex') >= 0) return n;
      n = n.parentElement;
    }
    return null;
  }
  function lineWidth(m) { return w(flexLine(m)); }
  function siblings(m) {
    var p = m.parentElement, out = [];
    if (!p) return out;
    var kids = p.children;
    for (var i = 0; i < kids.length; i++) {
      var e = kids[i], cs = getComputedStyle(e);
      out.push((e === m ? '[main] ' : '') + e.tagName.toLowerCase() + '.'
               + String(e.className).split(' ')[0] + ' w=' + w(e) + ' pos=' + cs.position
               + ' disp=' + cs.display + ' basis=' + cs.flexBasis);
    }
    return out;
  }
"""


def probe_script(rid, port, modes, min_paragraphs=4):
    """Measure the column once per mode. `modes` is a list of (name, add-layout-wide?)."""
    return """
<script>
(function () {
  var RID = %r, API = 'http://127.0.0.1:%d', MODES = %s, MINP = %d;
  function w(el) { return el ? Math.round(el.getBoundingClientRect().width) : null; }
  function root() { return document.querySelector('main'); }
%s
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
    return {para: widest, main: w(m), line: lineWidth(m), paragraphs: ps.length, ctl: ctl,
            panels: panels(), chain: chain(m), siblings: siblings(m),
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
""" % (rid, port, json.dumps(modes), min_paragraphs, CENSUS_JS)


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


def diagram_pages(n, whole=False):
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
    if whole:
        assert out, "vacuity: no Mermaid page resolved to a live URL at all"
        return out, len(out)
    assert len(out) >= n, "vacuity: only %d Mermaid pages resolved to a live URL" % len(out)
    return out[:n], len(out)


def diagram_pages_dense(n):
    """The Mermaid pages that author the most diagrams, in that order.

    The phone leg anchors a subtraction, so it is measured on the pages a phone reader is most
    likely to blame: the walk-order first pages happen to carry one diagram each, which is a
    sample of the top of a page rather than of the book's diagram-dense pages.
    """
    all_pages, total = diagram_pages(0, whole=True)
    def blocks(rel):
        text = io.open(os.path.join(wl.DOCS, rel.replace("/", os.sep)), encoding="utf-8").read()
        return len(re.findall(r"^```mermaid", text, flags=re.M))
    return sorted(all_pages, key=lambda p: -blocks(p[0]))[:n], total


def shoot(srv, name, vw, height=1200):
    """One browser run with EXACTLY one --window-size.

    Server.render passes its own --window-size before `extra`, and Chromium does not reliably take
    the later one: a control box authored at 1600px came back measuring 1250px, i.e. the viewport we
    thought we asked for. A column read at the wrong viewport is a fabricated number, so this axis
    owns its browser flags and then asserts on innerWidth (see `run`).
    """
    exe = browser()
    cmd = [exe] + headless_flags(exe) + [
        "--disable-gpu", "--no-first-run", "--no-default-browser-check",
        "--user-data-dir=" + srv.new_profile(), "--window-size=%d,%d" % (vw, height),
        srv.url(name)]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def confirm_window(asked, got, where, need=None):
    """Pin a column reading to the window the page actually laid out, not to the flag we passed.

    The ladder above was measured on chrome-headless-shell, which honours `--window-size` to the
    pixel. Edge is first in the candidate list and hands back a window 30px narrower at every size
    (round 101, table above), so a leg that asserts the flag value asserts which engine ran — while
    the premise it is there to protect is about the window: the article column only reaches its cap
    from `COPY_CAP_BINDS_AT` up. So this reads the page's own report, tolerates what engines here
    really reserve, says the reserve out loud once, and refuses a reading from a window the caller's
    premise cannot hold in.
    """
    assert got is not None, "%s: the page reported no window width at all (asked vw=%d)" % (where, asked)
    if got != asked:
        key = (asked, got)
        if key not in _WINDOW_NOTES:
            _WINDOW_NOTES.add(key)
            print("  window: %s asked vw=%d, the page laid out %d (%+d) — the flag is not the "
                  "viewport; every guard below reads the report" % (where, asked, got, got - asked))
    assert asked - WINDOW_CLAMP_SLACK <= got <= asked + 5, \
        "%s: asked for a vw=%d window, the page reported %d — more than the %dpx the engines here " \
        "reserve, so this reading came from another viewport" % (where, asked, got, WINDOW_CLAMP_SLACK)
    if need is not None:
        assert got >= need, \
            "%s: this reading needs a laid-out window of at least %dpx for its premise to hold " \
            "(asked %d, reported %d)" % (where, need, asked, got)
    return got


# (asked, reported, premise, must-pass) — every branch of `confirm_window` gets its own arm,
# including the two readings that used to be conflated: the shell's exact 1500 and Edge's 1470.
WINDOW_ARMS = [(COPY_VIEWPORT, COPY_VIEWPORT, None, True),
               (COPY_VIEWPORT, 1470, COPY_CAP_BINDS_AT, True),
               (COPY_VIEWPORT, COPY_CAP_BINDS_AT, COPY_CAP_BINDS_AT, True),
               (COPY_VIEWPORT, COPY_CAP_BINDS_AT - 1, COPY_CAP_BINDS_AT, False),
               (COPY_VIEWPORT, COPY_VIEWPORT - WINDOW_CLAMP_SLACK, None, True),
               (COPY_VIEWPORT, COPY_VIEWPORT - WINDOW_CLAMP_SLACK - 1, None, False),
               (COPY_VIEWPORT, COPY_VIEWPORT + 6, None, False),
               (COPY_VIEWPORT, 900, None, False),
               (COPY_VIEWPORT, None, COPY_CAP_BINDS_AT, False)]


def window_selftest():
    """Drive `confirm_window` over planted engine reports, offline, no browser.

    Round 101 replaced `reported vw == COPY_VIEWPORT` in two sister axes (check_svg_legibility's copy
    leg, check_table_overflow) with this guard, because the machine's Edge lays out 1470px when asked
    for 1500 and the old assert reddened on the engine rather than on the book. A loosened guard has
    to be shown still able to bite, so each branch gets an arm: the exact reading (the shell), the
    real reserve, the widest window that still binds the 768 cap, one pixel below that bar, the
    slack's edge and one past it, a report wider than the flag, an unrelated viewport, and a page
    that reported no window at all.
    """
    passed, reddened = [], []
    for asked, got, need, want in WINDOW_ARMS:
        try:
            confirm_window(asked, got, "arm reported=%s need=%s" % (got, need), need)
            ok, why = True, ""
        except AssertionError as exc:
            ok, why = False, str(exc)
        assert ok == want, "window arm (asked %d, reported %s, need %s) %s: %s" % (
            asked, got, need, "should have passed but reddened" if want else
            "should have reddened but passed", why)
        (passed if ok else reddened).append(got)
    assert len(reddened) == sum(1 for a in WINDOW_ARMS if not a[3]), \
        "vacuity: the red arms are %s, so the guard is not judging them" % reddened
    print("window guard ok: %d of %d planted reports pass (the shell's exact %d and Edge's real %d "
          "at an asked %d), and %d redden — including %s, i.e. the guard is not simply always green"
          % (len(passed), len(WINDOW_ARMS), COPY_VIEWPORT, 1470, COPY_VIEWPORT,
             len(reddened), reddened))


def run(srv, name, vw, rid, timeout=70):
    proc = shoot(srv, name, vw)
    rep = srv.wait(rid, timeout, proc)
    Server.stop(proc)
    if rep and rep.get("viewport"):
        confirm_window(vw, rep["viewport"][0], "copy ladder")
    return rep


def engine_reserve(rep, asked):
    """How many pixels this machine's browser takes off `--window-size` before the page lays out.

    Round 82 established the copy/live relation as "the live page minus a 15px classic-scrollbar
    gutter", and the ladder keyed its readings by the width it ASKED for. Both were true only while
    the engine handed back what it was asked: Edge here reserves 30px, so an asked 1024 lays out at
    994 and an asked 1280 at 1250 - and 994/1250 sit BELOW GitBook's own 1024/1280 sidebar
    breakpoints, so the copy mounts one navigation sheet fewer than the reader does, <main> falls
    through to its 768 cap, and the axis spent the round reporting a 144-160px "copy vs live" gap
    that was really the engine crossing a breakpoint under the ruler's feet. Measuring the reserve
    once, on the control page, lets every ladder run ask for a window the page then reports as the
    reader's width - so copy and live are compared at the same CSS width, which is the only
    comparison the gutter premise is about.
    """
    assert rep and rep.get("viewport"), "no window reported, so no reserve can be measured"
    reserve = asked - rep["viewport"][0]
    assert 0 <= reserve <= WINDOW_CLAMP_SLACK, \
        "the engine reported a window %dpx off the asked %d - outside the %dpx the engines here " \
        "produce, so this run's layout width is unknown" % (rep["viewport"][0], asked,
                                                            WINDOW_CLAMP_SLACK)
    return reserve


# The gutter a saved copy loses to its classic scrollbar, plus the px the engines here vary by. Both
# legs measured on the shell: 609 vs 624 at 1024, 593 vs 608 at 1280, 753 vs 768 at 1440.
GUTTER = 15
ENGINE_VARIANCE = 9


# (asked reader width, window the page reported, may be keyed?) — the second arm is the whole round:
# an asked 1024 that laid out 994 used to be filed as a 1024 reading, and those 30px are exactly the
# distance to GitBook's sidebar breakpoint.
LADDER_ARMS = [(1024, 1024, True), (1024, 994, False), (1280, 1280, True), (1024, 1026, False),
               (1500, 1470, False), (1024, None, False)]


def ladder_key(vw, reported):
    """File a copy reading under the width the PAGE laid out, and only when that is the reader's.

    A copy measured at 994 answers a question about a 994px reader. Keying it as 1024 is what made
    this axis compare a 994px page with a 1024px reader and call the 144px difference a site defect.
    The tolerance is 1px: two pixels cannot cross a breakpoint, while anything larger is an engine
    whose reserve moved between the control run and this one - a reading of unknown width is a
    coverage gap, not a datum.
    """
    if reported is None or abs(reported - vw) > 1:
        return None
    return vw


def column_fidelity(copy, live):
    """One matched-width pair: is this copy the live page minus its scrollbar?

    Called only at a width both legs laid out (see `paired_widths`), which is what makes the old
    ±24 band a real test rather than a comparison across a breakpoint.
    """
    delta = live - copy
    if 0 <= delta <= GUTTER + ENGINE_VARIANCE:
        return None
    if delta < 0:
        return ("COPY-NOT-LIVE: at the same window the copy lays <main> out %dpx WIDER than the "
                "live page (copy=%d live=%d) - the copy has room the reader does not, so every "
                "copy-based leg under-reads the squeeze" % (-delta, copy, live))
    return ("COPY-NOT-LIVE: at the same window the copy is %dpx NARROWER than the live page "
            "(copy=%d live=%d), past the %dpx gutter and the %dpx the engines here vary - the two "
            "are not the same layout" % (-delta, copy, live, GUTTER, ENGINE_VARIANCE))


def paired_widths(copy_rows, live_rows):
    """The widths both legs laid out - the only ones a copy may be compared at.

    Derived from the two readings rather than from a constant, so an engine with a different reserve
    narrows the comparison instead of silently widening it.
    """
    return sorted(set(copy_rows) & set(live_rows))


# (copy, live, expected verdict) at one matched window.
FIDELITY_ARMS = [(609, 624, "ok"), (753, 768, "ok"), (624, 624, "ok"), (600, 624, "ok"),
                 (599, 624, "COPY-NOT-LIVE"), (768, 624, "COPY-NOT-LIVE"),
                 (700, 624, "COPY-NOT-LIVE"), (624, 608, "COPY-NOT-LIVE")]


def fidelity_selftest():
    silent, red = [], []
    for copy, live, want in FIDELITY_ARMS:
        got = column_fidelity(copy, live)
        verdict = "ok" if got is None else got.split(":")[0]
        assert verdict == want, "fidelity arm copy=%d live=%d judged %s, expected %s (%s)" % (
            copy, live, verdict, want, got)
        (red if got else silent).append((copy, live))
    assert silent and len(red) == sum(1 for a in FIDELITY_ARMS if a[2] != "ok"), \
        "vacuity: the fidelity guard reddened %s" % red
    print("fidelity guard ok: %d of %d planted pairs are silent (the shell's real 609-vs-624 and "
          "753-vs-768 gutters) and %d redden (%s) - the reddening set holds a copy wider than its "
          "live page and a copy 1px past the band, so the guard is neither always green nor always red"
          % (len(silent), len(FIDELITY_ARMS), len(red), red))


def ladder_key_selftest():
    keyed, refused = [], []
    for vw, reported, want in LADDER_ARMS:
        got = ladder_key(vw, reported)
        assert (got is not None) == want, "ladder arm (vw=%d, reported=%s) keyed %s, want %s" % (
            vw, reported, got, "a reading" if want else "a refusal")
        (keyed if got else refused).append("%s->%s" % (vw, reported))
    assert len(refused) >= 3, "vacuity: the ladder refused nothing (%s)" % keyed
    print("ladder key ok: %d of %d planted reports are keyed at the reader's width, %d are refused "
          "as coverage gaps (%s) - the 1024->994 refusal is the case that used to be filed as a "
          "1024 reading and reported as a 144px site defect"
          % (len(keyed), len(LADDER_ARMS), len(refused), refused))


# Same control page, driven twice: the reserve is measured, and a planted off-by-a-lot report has to
# be refused rather than compensated into silence.
RESERVE_ARMS = [(1280, 1250, True), (1280, 1280, True), (1280, 1280 - WINDOW_CLAMP_SLACK, True),
                (1280, 1280 - WINDOW_CLAMP_SLACK - 1, False), (1280, 1290, False),
                (1280, None, False)]


def reserve_selftest():
    ok, red = [], []
    for asked, got, want in RESERVE_ARMS:
        rep = {"viewport": [got, 900]} if got is not None else {}
        try:
            engine_reserve(rep, asked)
            good, why = True, ""
        except (AssertionError, TypeError) as exc:
            good, why = False, str(exc)[:70]
        assert good == want, "reserve arm (asked %d, got %s) %s: %s" % (
            asked, got, "should pass" if want else "should refuse", why)
        (ok if good else red).append(got)
    assert len(red) == sum(1 for a in RESERVE_ARMS if not a[2]), \
        "vacuity: the reserve guard only ever reddened %s" % red
    print("reserve guard ok: %d of %d planted engine reports are compensated, %d are refused "
          "(the refusals are %s) - the compensation cannot swallow an arbitrary offset"
          % (len(ok), len(RESERVE_ARMS), len(red), red))


HYDRATED_PROBE = r"""
() => {
  const w = el => Math.round(el.getBoundingClientRect().width);
  const main = document.querySelector('main');
  if (!main) return null;
%s
  let para = 0;
  for (const p of main.querySelectorAll('p')) para = Math.max(para, w(p));
  const panelCensus = panels();
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
  return {vw: innerWidth, main: w(main), para: para, line: lineWidth(main),
          panels: panelCensus,
          chain: chain(main), siblings: siblings(main), ctl: ctl, phantom: phantom};
}
""" % CENSUS_JS


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


# ------------------------------------------------------------- the phone reader's diagram box
# Round 107 measured the 342px box once, by hand, and wrote it into check_mermaid_geometry.py as
# `COLUMN_PHONE`; the prose there said plainly that nothing re-measured it. This leg is that
# re-measurement, and three facts had to be measured on the live page first, because each one
# breaks a leg written from the desktop case:
#   * `main svg` is not a diagram selector. At vw=390 on 00-index/learning-path.md it matched 180
#     element icons (gb-icon, button-leading-icon) before a single diagram appeared.
#   * a diagram's own chain is `div.group/mermaid.relative` (358 = the whole phone column) >
#     `div.cursor-grab.overflow-hidden` (358) > `div.overflow-auto.p-2.[&_svg]:max-w-full` (358,
#     padding 8/8) > `svg width="100%"` painted 342. So the box is that scroll div's CONTENT width,
#     358 - 8 - 8, i.e. a subtraction the platform performs, not a number anyone may re-type.
#   * Mermaid mounts lazily and paints only once the block is scrolled into view. A first pass over
#     eight pages read every container still in its placeholder state: `div.flex.h-24` holding a 32px
#     loader svg (class `h-8 w-8`, viewBox 0 0 128 116, and unlike a diagram NO style.max-width).
#     A leg that measures on arrival measures a spinner - and would report 358 as the box.
PHONE_VW = 390
PHONE_DIAGRAMS_PER_PAGE = 2
PHONE_POLL_TRIES = 24
PHONE_POLL_MS = 500
PHONE_BOX_TOL = 2                 # px; the box is 358-8-8, so a correct reading lands exactly
PHONE_BAR = LABEL_BAR             # px; the same floor the geometry axis reports against

BOX_JS = """
(k) => {
  const c = document.querySelectorAll('[class*="group/mermaid"]')[k];
  if (!c) return null;
  const svg = c.querySelector('svg');
  if (!svg) return {state: 'no-svg'};
  const w = el => Math.round(el.getBoundingClientRect().width);
  const host = svg.parentElement, hs = getComputedStyle(host);
  let minFs = null, nodes = 0;
  const lab = svg.querySelectorAll('text,tspan,.nodeLabel,.label,'
                                   + 'foreignObject div,foreignObject span');
  for (const t of lab) {
    const f = parseFloat(getComputedStyle(t).fontSize);
    nodes++;
    if (isFinite(f) && (minFs === null || f < minFs)) minFs = f;
  }
  return {container: w(c), svg: w(svg), styleMaxW: svg.style.maxWidth || '',
          vb: svg.getAttribute('viewBox') || '', svgCls: String(svg.getAttribute('class') || ''),
          hostTag: host.tagName.toLowerCase(), hostCls: String(host.getAttribute('class') || ''),
          hostClientW: host.clientWidth, padL: hs.paddingLeft, padR: hs.paddingRight,
          hostOverflowX: hs.overflowX, scrollW: host.scrollWidth,
          labelNodes: nodes, minFs: minFs};
}
"""


def _px(text):
    """`1056.66px` -> 1056.66; anything mermaid did not write stays None."""
    try:
        return float(str(text).strip().rstrip("px"))
    except (TypeError, ValueError):
        return None


def _vb_width(vb):
    parts = str(vb or "").split()
    try:
        return float(parts[2]) if len(parts) >= 4 else None
    except ValueError:
        return None


def diagram_reading(facts):
    """(state, reading) for one container. The classification lives in Python, not in the injected
    JS, so --selftest can drive planted readings through it - including the loader state this leg
    exists to refuse."""
    if not facts:
        return "NO-CONTAINER", None
    if facts.get("state") == "no-svg":
        return "NO-SVG", None
    natural = _px(facts.get("styleMaxW"))
    vbw = _vb_width(facts.get("vb"))
    if not natural or not vbw:
        # mermaid writes style.max-width only when it has rendered the diagram, so its absence is
        # the placeholder - not a diagram the phone reader cannot see.
        return "PLACEHOLDER", facts
    pad = (_px(facts.get("padL")) or 0) + (_px(facts.get("padR")) or 0)
    box = facts["hostClientW"] - pad
    scale = facts["svg"] / vbw if vbw else None
    min_fs = facts.get("minFs")
    label = round(min_fs * scale, 2) if min_fs and scale else None
    return "PAINTED", {"box": box, "container": facts["container"], "natural": natural,
                       "vb_width": vbw, "painted": facts["svg"], "scale": scale,
                       "label_px": label, "label_nodes": facts.get("labelNodes", 0),
                       "scroll_w": facts.get("scrollW"), "client_w": facts["hostClientW"],
                       "host_cls": facts.get("hostCls"),
                       "pad": pad, "overflow_x": facts.get("hostOverflowX")}


def phone_verdict(readings, box=COLUMN_PHONE):
    """What a set of painted phone readings says about the platform: (problems, gaps, lines)."""
    problems, gaps, lines = [], [], []
    under = 0
    for r in readings:
        if r["label_px"] is not None and r["label_px"] < PHONE_BAR:
            under += 1
        drifted = abs(r["box"] - box) > PHONE_BOX_TOL
        if drifted:
            problems.append("PHONE-DIAG-BOX: the phone reader is given %dpx for a diagram while"
                            " check_mermaid_geometry judges them against %dpx (round 107's reading)"
                            " - the platform changed the box or the wrapper's padding, so re-anchor"
                            " COLUMN_PHONE on this number before trusting either"
                            % (r["box"], box))
        # The fitted premise is only meaningful on an anchored box: when the platform shrinks the
        # box the svg fills the new box correctly, and every diagram would then report a second,
        # derivative complaint next to the one that actually needs fixing.
        expected = min(box, r["natural"])
        if not drifted and abs(r["painted"] - expected) > PHONE_BOX_TOL:
            problems.append("PHONE-SVG-NOT-FITTED: natural %dpx painted %dpx in a %dpx box (it"
                            " should be %dpx - width:100%% fills the box, max-width caps at natural),"
                            " so the axis no longer knows what the reader's browser did to this"
                            " diagram" % (r["natural"], r["painted"], r["box"], expected))
        # scrollWidth is measured against the wrapper's own clientWidth, not against the box:
        # scrollWidth already contains the padding, so a diagram that fits reports clientWidth
        # exactly (358 here) and would be accused of scrolling by a box-relative bar. This is the
        # difference between "the platform gave the reader a slider" and "the padding is 8px".
        if r["scroll_w"] and r["scroll_w"] > r["client_w"]:
            problems.append("PHONE-SCROLLER: the %s wrapper reports scrollWidth %d against its own"
                            " clientWidth %d, so this diagram is inside something that can scroll"
                            " - the geometry axis's 'over-wide means scaled down, never scrolled'"
                            " premise needs re-testing"
                            % (r["host_cls"][:40], r["scroll_w"], r["client_w"]))
        if not r["label_nodes"]:
            gaps.append("PHONE-BLIND-LABELS: a painted diagram with 0 label nodes (mermaid draws"
                        " node labels as HTML inside foreignObject, so a count of only text/tspan"
                        " reads blind) - its label size is unmeasured, not clean")
        lines.append("      box=%-4d (container %d - wrapper padding %d) natural=%-6d painted=%-4d"
                     " scale=%.3f smallest label=%spx %s  wrapper=%s"
                     % (r["box"], r["container"], r["pad"], r["natural"], r["painted"], r["scale"],
                        r["label_px"], "BELOW-BAR" if r["label_px"] is not None and
                        r["label_px"] < PHONE_BAR else "ok", r["host_cls"][:46]))
    lines.append("   %d of %d painted diagrams sampled here paint their smallest label below %gpx;"
                 " the corpus-wide count is check_mermaid_geometry's phone reading, which this leg"
                 " now anchors on the live page" % (under, len(readings), PHONE_BAR))
    return problems, gaps, lines


def phone_selftest(box=COLUMN_PHONE):
    """Offline: the classifier must refuse a spinner, and each judgement branch must be reachable."""
    painted = {"container": 358, "svg": 342, "styleMaxW": "1056.66px", "vb": "0 0 1056.65625 177",
               "hostTag": "div", "hostCls": "overflow-auto p-2 [&_svg]:max-w-full",
               "hostClientW": 358, "padL": "8px", "padR": "8px", "hostOverflowX": "auto",
               "scrollW": 358, "labelNodes": 41, "minFs": 16}
    loader = {"container": 358, "svg": 32, "styleMaxW": "", "vb": "0 0 128 116",
              "hostTag": "div", "hostCls": "flex h-24 items-center justify-center text-tint",
              "hostClientW": 358, "padL": "0px", "padR": "0px", "hostOverflowX": "visible",
              "scrollW": 358, "labelNodes": 0, "minFs": None}
    arms = [("painted diagram", painted), ("loader placeholder", loader),
            ("container not mounted yet", None), ("mounted, no svg yet", {"state": "no-svg"})]
    states = {name: diagram_reading(f)[0] for name, f in arms}
    assert states["painted diagram"] == "PAINTED", states
    assert states["loader placeholder"] == "PLACEHOLDER", \
        "a spinner would be measured as a diagram: %s" % states
    assert states["container not mounted yet"] == "NO-CONTAINER" and \
        states["mounted, no svg yet"] == "NO-SVG", states
    r = diagram_reading(painted)[1]
    assert r["box"] == box and abs(r["label_px"] - 5.18) < 0.02, r
    problems, gaps, _ = phone_verdict([r], box)
    assert not problems and not gaps, "the honest reading is being accused: %s %s" % (problems, gaps)

    drifted = dict(painted, hostClientW=318, svg=302, scrollW=318)   # the column lost 40px
    problems, _, _ = phone_verdict([diagram_reading(drifted)[1]], box)
    assert any(p.startswith("PHONE-DIAG-BOX") for p in problems), \
        "a 302px box slipped past the anchor check: %s" % problems
    assert all(p.startswith("PHONE-DIAG-BOX") for p in problems), \
        "the box-drift arm also tripped another gate, so it proves nothing about either: %s" % problems

    unfitted = dict(painted, svg=358)                          # svg painted at the CONTAINER width
    problems, _, _ = phone_verdict([diagram_reading(unfitted)[1]], box)
    assert any(p.startswith("PHONE-SVG-NOT-FITTED") for p in problems), \
        "a diagram painted outside its box slipped past: %s" % problems
    assert all(p.startswith("PHONE-SVG-NOT-FITTED") for p in problems), \
        "the not-fitted arm also tripped another gate: %s" % problems

    scrolling = dict(painted, scrollW=1057)                    # a real horizontal scroller appears
    problems, _, _ = phone_verdict([diagram_reading(scrolling)[1]], box)
    assert any(p.startswith("PHONE-SCROLLER") for p in problems), \
        "the 'scaled, never scrolled' premise went untested: %s" % problems
    assert all(p.startswith("PHONE-SCROLLER") for p in problems), \
        "the scroller arm also tripped another gate: %s" % problems

    blind = dict(painted, labelNodes=0)
    _, gaps, _ = phone_verdict([diagram_reading(blind)[1]], box)
    assert any(g.startswith("PHONE-BLIND-LABELS") for g in gaps), \
        "a reading with no labels at all was reported as clean: %s" % gaps

    narrow = dict(painted, styleMaxW="300px", vb="0 0 300 200", svg=300)
    problems, _, _ = phone_verdict([diagram_reading(narrow)[1]], box)
    assert not problems, "a diagram narrower than the box is capped at natural, not stretched: %s" \
        % problems
    print("phone leg ok: a real reading anchors at %dpx (labels %s px), a loader is refused as"
          " PLACEHOLDER, and the four failure arms (box drift %dpx, painted-at-container, a real"
          " scroller, zero label nodes) each name their own gate"
          % (box, r["label_px"], diagram_reading(drifted)[1]["box"]))


def phone_diagram_leg(pages, per_page=PHONE_DIAGRAMS_PER_PAGE):
    """Measure the diagram box a phone reader is given, on the live page, diagram by diagram.

    Returns (rows, gaps, note). Nothing here may go quiet: `pages=3, boxes=0` would otherwise read
    as a clean sweep while the leg measured nothing but spinners.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [], [], ("playwright is not installed, so the phone diagram box was NOT re-measured;"
                        " check_mermaid_geometry still prints its 342px reading, unanchored")
    rows, gaps = [], []
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        for rel, url in pages:
            ctx = br.new_context(viewport={"width": PHONE_VW, "height": 900}, is_mobile=True,
                                 device_scale_factor=3)
            pg = ctx.new_page()
            got = 0
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=90000)
                pg.wait_for_selector('[class*="group/mermaid"]', timeout=45000)
                pg.wait_for_timeout(2000)
                k, seen = 0, 1
                while got < per_page and k < seen + 4:
                    facts, state, reading = None, None, None
                    for _ in range(PHONE_POLL_TRIES):
                        # GitBook mounts a diagram container only when the reader's scroll reaches
                        # it, so "index k is not in the DOM" means "not scrolled far enough" until
                        # the page stops scrolling. Wheeling is the reader's own gesture, and it is
                        # what makes a page's second diagram reachable at all.
                        count = pg.evaluate("() => document.querySelectorAll("
                                            "'[class*=\"group/mermaid\"]').length")
                        seen = max(seen, count)
                        if k < count:
                            pg.evaluate("(k) => {document.querySelectorAll("
                                        "'[class*=\"group/mermaid\"]')[k]"
                                        ".scrollIntoView({block:'center'});}", k)
                        elif not pg.evaluate("() => {const y = window.scrollY;"
                                             " window.scrollBy(0, 900);"
                                             " return Math.round(window.scrollY) !== Math.round(y);}"):
                            break              # bottom of the page, and index k never mounted
                        facts = pg.evaluate(BOX_JS, k)
                        state, reading = diagram_reading(facts)
                        if state == "PAINTED":
                            break
                        pg.wait_for_timeout(PHONE_POLL_MS)
                    if state == "PAINTED":
                        got += 1
                        rows.append(dict(reading, page=rel, index=k))
                    elif state in ("NO-CONTAINER", "NO-SVG"):
                        # The poll scrolled the whole page and index k still is not there: the page
                        # has no further diagram for this leg to read.
                        break
                    else:
                        gaps.append("PHONE-PLACEHOLDER %s #%d (scrolled into view and polled %d x"
                                    " %dms; the container never left its loader state, so this"
                                    " page's box is unmeasured rather than clean)"
                                    % (rel, k, PHONE_POLL_TRIES, PHONE_POLL_MS))
                    k += 1
                if not got:
                    gaps.append("PHONE-NO-DIAGRAM %s: the leg reached the page and painted nothing"
                                " to measure" % rel)
            except Exception as exc:
                gaps.append("PHONE-NOLOAD %s (%s)" % (rel, str(exc)[:70]))
            finally:
                ctx.close()
        br.close()
    return rows, gaps, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--assume", type=int, default=COLUMN,
                    help="the column the Mermaid geometry axis assumes (check_mermaid_geometry.COLUMN)")
    ap.add_argument("--assume-phone", type=int, default=COLUMN_PHONE,
                    help="the diagram box check_mermaid_geometry derives its phone reading from"
                         " (check_mermaid_geometry.COLUMN_PHONE)")
    ap.add_argument("--all-viewports", action="store_true")
    ap.add_argument("--no-hydrated", action="store_true",
                    help="skip the live-page leg (Playwright); the copy leg alone cannot see the "
                         "navigation panels that squeeze a reader's column")
    ap.add_argument("--no-phone", action="store_true",
                    help="skip the phone diagram-box leg; check_mermaid_geometry's 342px reading is"
                         " then unanchored again, exactly the state round 107 left behind")
    ap.add_argument("--phone-pages", type=int, default=2,
                    help="how many diagram-dense pages the phone leg walks (default 2; the pages"
                         " are chosen by how many Mermaid blocks each authors)")
    ap.add_argument("--selftest", action="store_true",
                    help="offline: drive the window guard over planted engine reports and stop")
    args = ap.parse_args()
    if args.selftest:
        window_selftest()
        reserve_selftest()
        ladder_key_selftest()
        fidelity_selftest()
        phone_selftest()
        return 0
    viewports = VIEWPORTS + [1280, 2560] if args.all_viewports else VIEWPORTS

    modes = [("asis", False), ("wide", True)]
    dummy = os.path.join(tempfile.gettempdir(), "livecol-none.js")
    io.open(dummy, "w", encoding="utf-8").write("// the column axis loads no engine\n")
    srv = Server(js_path=dummy)
    rid = 0
    try:
        # ---- guards on our own ruler -------------------------------------------------
        window_selftest()
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
        reserve_selftest()
        phone_selftest()
        reserve = engine_reserve(rep, 1280)
        if reserve:
            print("engine reserve: the control asked vw=1280 and the page reported %d, so every "
                  "ladder run below asks vw+%d and is then keyed by the width the PAGE reported - "
                  "copy and live meet at one CSS width, and a navigation breakpoint cannot sit "
                  "between the two readings" % (rep["viewport"][0], reserve))

        # ---- the live site -----------------------------------------------------------
        pages, total = diagram_pages(args.pages)
        print("pages=%d (of %d Mermaid pages resolvable through llms.txt) viewports=%s assume=%dpx"
              % (len(pages), total, viewports, args.assume))
        asis, wide = {}, {}
        copy_dom = {}
        # `problems` is a statement about the site; `gaps` is a statement about this run. Round 95
        # split them the same way in check_table_overflow after a sweep reported `problems=1` for a
        # page that had never hydrated at all — read as "one content defect among a clean sweep".
        problems, gaps, pair_gaps = [], [], []
        for rel, url in pages:
            html = wl.fetch(url) if url.startswith("http") else wl.fetch(wl.SITE + "/" + url)
            for vw in viewports:
                rid += 1
                name = "col-live-%d.html" % rid
                io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(
                    live_copy(html, wl.SITE, probe_script(rid, srv.port, modes)))
                rep = run(srv, name, vw + reserve, rid)
                if not rep or not rep["modes"]:
                    gaps.append("NOHYDRATE %s @%d (harness/CDN: this page/viewport was never measured,"
                                " which says nothing about its column)" % (rel, vw))
                    continue
                key = ladder_key(vw, rep["viewport"][0])
                if key is None:
                    gaps.append("WINDOW-DRIFT %s: asked the engine for %d to land on a %dpx page "
                                "window, the page reported %d - a copy laid out at another width "
                                "answers another reader, so this reading is dropped rather than "
                                "keyed to %d" % (rel, vw + reserve, vw, rep["viewport"][0], vw))
                    continue
                m = {e["mode"]: e for e in rep["modes"]}
                if not m.get("asis", {}).get("m"):
                    gaps.append("EMPTY %s @%d viewport=%s (the probe ran and read no paragraph box,"
                                " so this reading is missing, not clean)" % (rel, vw, rep["viewport"]))
                    continue
                a, wd = m["asis"]["m"]["para"], (m.get("wide") or {}).get("m", {}).get("para")
                asis.setdefault(key, []).append((rel, a))
                wide.setdefault(key, []).append((rel, wd))
                copy_dom[(key, rel)] = m["asis"]["m"]
                print("  %-46s vw=%-5d column=%-5s wide-layout=%-5s main=%s line=%s ps=%s sheets=%s"
                      % (rel, key, a, wd, m["asis"]["m"]["main"], m["asis"]["m"].get("line"),
                         m["asis"]["m"]["paragraphs"], m["asis"]["m"].get("panels")))

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
                print("        chain(live): %s" % " < ".join(r0["chain"][:6]))
                cd = copy_dom.get((vw, r0["page"]))
                if cd:
                    print("        chain(copy of the same page): %s" % " < ".join(cd["chain"][:6]))

        # ---- round 108's phone diagram box -------------------------------------------
        # The hydrated leg above reads <main> (358 at vw=390); this reads what the diagram is
        # actually GIVEN inside it (342), which is the number check_mermaid_geometry's phone
        # reading is derived from. Kept as its own leg because the two need different waits:
        # a paragraph box exists in the server HTML, a Mermaid diagram only paints once scrolled
        # into view - and measuring the page before that measures a loader icon.
        phone, phone_gaps, phone_note = [], [], None
        if not args.no_phone:
            dense, dense_total = diagram_pages_dense(args.phone_pages)
            phone, phone_gaps, phone_note = phone_diagram_leg(dense)
            print("\nphone diagram leg (live page, vw=%d, up to %d diagram(s) per page): %d painted"
                  " from the %d most diagram-dense of %d Mermaid pages"
                  % (PHONE_VW, PHONE_DIAGRAMS_PER_PAGE, len(phone), len(dense), dense_total))
            for r in phone:
                print("  %-46s #%d" % (r["page"], r["index"]))
                print("      %s" % phone_verdict([r], args.assume_phone)[2][0])
        else:
            phone_note = ("--no-phone was passed, so the %dpx phone diagram box is UNANCHORED this"
                          " run (round 107's one-off reading is still what the geometry axis"
                          " derives from)" % COLUMN_PHONE)
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
    print("  narrowest column on a saved copy: %dpx (viewports %s); geometry axis assumes %dpx"
          % (low, sorted(asis), args.assume))

    # ---- round 82's two premise guards ------------------------------------------------
    # (1) The cap downstream legs judge against has to bind on the copy they ask for. Every axis that
    #     lays a reader page out renders at COPY_VIEWPORT and asserts <main> == its column constant,
    #     so this is where that shared premise is proved once, with the whole ladder in view.
    # (2) A copy has to be the live page at the SAME window, minus its scrollbar. Round 104 moved this
    #     from "same asked vw" to "same laid-out window", because asked was never the width the copy
    #     page used: on Edge an asked 1024 laid out 994, unmounted the navigation, and the guard spent
    #     the round reporting a 144px gap between two pages that were never at the same width. The
    #     judgement itself is `column_fidelity`, driven offline over planted pairs by --selftest.
    if COPY_VIEWPORT in asis:
        cap = min(v for _, v in asis[COPY_VIEWPORT])
        assert cap == args.assume, \
            "the %dpx cap does not bind on a copy at vw=%d: measured %dpx. Every leg that lays a " \
            "reader page out at COPY_VIEWPORT asserts this number, so re-anchor them on the reading " \
            "above before trusting their verdicts" % (args.assume, COPY_VIEWPORT, cap)
        print("  cap guard: a copy at vw=%d lays the article out at %dpx == the %dpx the geometry "
              "axes judge against" % (COPY_VIEWPORT, cap, args.assume))
    met = paired_widths(asis, hyd)
    for vw in met:
        c = min(v for _, v in asis[vw])
        h = min(r["para"] for r in hyd[vw])
        verdict = column_fidelity(c, h)
        if verdict:
            problems.append("vw=%d %s" % (vw, verdict))
        else:
            print("  copy vs live at the same vw=%-5d window: copy=%-4d live=%-4d gutter=%-2dpx "
                  "(a saved copy is the live page minus its classic scrollbar)"
                  % (vw, c, h, h - c))
    if not hyd:
        pair_gaps.append("NO-LIVE-COMPARISON: the live leg read %d widths, so every copy reading"
                         " above is unjudged - a saved page cannot show what its reader gets, and this"
                         " run does not get to report a clean column" % len(hyd))
    for vw in sorted(set(asis) - set(met)):
        pair_gaps.append("NO-LIVE-PARTNER vw=%d: the copy leg laid a page out at this width and the "
                         "live leg never measured it, so nothing here says what a reader at %dpx gets"
                         " - a copy-only reading cannot certify its own column" % (vw, vw))

    # ---- what the reader's window actually spends, and the phone case -----------------
    # Printed, not counted: the navigation cost is a platform fact, and the decision it feeds - whether
    # the book's figures are judged at the 768px a wide reader gets or at the 608px a laptop reader
    # gets - belongs to the operator (it is `COLUMN-MISMATCH` below, and it stays red until chosen).
    # What this loop must not do is go quiet: a green with no mention of the narrower column would let
    # every downstream axis keep certifying against the wider one.
    advisories = []
    if hyd_note:
        print("  hydrated leg skipped: %s" % hyd_note)
    desktop = [vw for vw, mobile in HYDRATED_AT if not mobile]
    for vw in sorted(desktop):
        if vw not in hyd:
            continue
        h = min(r["para"] for r in hyd[vw])
        r0 = hyd[vw][0]
        # `vw - column` would blame the reader's whole window on the navigation, but <main> lives in a
        # flex line capped at 1440px, and the wrappers above it are display:contents (0px). The cost
        # is what THAT line spends on everything except <main> - printed for every desktop breakpoint
        # so a widening of the chrome shows up as a number, not an inference.
        line, box = r0.get("line"), r0.get("main")
        spends = "unknown (no flex line found)" if not line or not box else "%dpx" % (line - box)
        print("  live desktop vw=%-5d reader column=%-4d flex line=%-5s main=%-5s the line spends"
              " %s on everything but the article  sheets=%s"
              % (vw, h, line, box, spends, "; ".join(r0["panels"][:3]) or "none"))
        if line and box:
            assert line - box >= 0, "the flex line (%s) is narrower than its own <main> (%s) at vw=%d" \
                % (line, box, vw)
        if h < args.assume:
            advisories.append(
                "COLUMN-DECISION vw=%d: a reader here gets %dpx, %dpx less than the %dpx the Mermaid,"
                " SVG and overflow legs certify against - which of the two is the book's bar is the"
                " operator's call, and until it is made every copy-based verdict describes a wider"
                " reader than this one" % (vw, h, args.assume - h, args.assume))
    for vw, mobile in HYDRATED_AT:
        if mobile and vw in hyd:
            print("  phone vw=%-5d reader column=%s (pinch-zoom belongs to the reader, so this is"
                  " context rather than a bar)" % (vw, sorted({r["para"] for r in hyd[vw]})))
    # The phone diagram box is judged, not printed as context: `check_mermaid_geometry` derives its
    # phone reading from this subtraction, and a constant that nothing re-measures is how round 107
    # ended up shipping a number it had only read once.
    if phone_note:
        print("  phone leg: %s" % phone_note)
        # An opt-out is judged the same way a broken leg is: the hydrated leg's `--no-hydrated`
        # already lands NO-LIVE-COMPARISON rather than a green, because a flag that silences the
        # only re-measurement of a shipped constant must cost the run its pass.
        pair_gaps.append("PHONE-LEG-BLIND: %s - the geometry axis's 342px phone reading is"
                         " unanchored this run" % phone_note)
    if phone:
        p, g, _ = phone_verdict(phone, args.assume_phone)
        problems.extend(p)
        gaps.extend(g)
        boxes = sorted({r["box"] for r in phone})
        print("  phone diagram box on the live page: %s px in a %s px column, read from %d painted"
              " diagram(s) - this is what check_mermaid_geometry's phone row is derived from"
              % (boxes, sorted({r["container"] for r in phone}), len(phone)))
        if len(boxes) > 1:
            problems.append("PHONE-BOX-SPREAD: the same phone window gave %s for different"
                            " diagrams, so the box is not the one subtraction this leg models"
                            % boxes)
    elif not args.no_phone and not phone_note:
        pair_gaps.append("PHONE-NO-READING: the phone leg ran and painted 0 diagrams, so the %dpx"
                         " box it exists to anchor went unmeasured - that is a coverage failure,"
                         " not a clean sweep" % args.assume_phone)
    for g in phone_gaps:
        pair_gaps.append(g)

    for vw, rows in sorted(wide.items()):
        vals = [v for _, v in rows if v]
        base = sorted({v for _, v in asis[vw]})
        if vals and max(vals) > max(base) + SPREAD_TOL:
            print("  wide layout at vw=%d would give %s (vs %s as-is)" % (vw, sorted(set(vals)), base))
        elif vals:
            print("  wide layout at vw=%d did not widen the column here (%s) -> the toggle still has"
                  " to be tested in the editor" % (vw, sorted(set(vals))))
    on_live = {vw: min(r["para"] for r in hyd[vw]) for vw in desktop if vw in hyd}
    if on_live:
        narrow_vw, narrow = min(on_live.items(), key=lambda kv: kv[1])
        where = "the live page at vw=%d" % narrow_vw
    else:
        narrow, where = low, "a saved copy - the live leg read nothing, so this is the copy's number"
    if narrow < args.assume:
        problems.append("COLUMN-MISMATCH: readers get %dpx (%s) but the Mermaid axis assumes %dpx ->"
                        " re-run it with --column %d" % (narrow, where, args.assume, narrow))
    for p in problems:
        print("  -", p)
    for a in advisories:
        print("  AWAITING-DECISION:", a)
    # Two kinds of gap, and only the first is a page x viewport reading: a width the live leg never
    # measured says nothing about how many readings arrived, it says the copy has no partner to be
    # judged against. Counting one inside the other is how a run can print "readings 9 of 9" next to
    # a tenth complaint.
    intended = len(pages) * len(viewports)
    for g in gaps + pair_gaps:
        print("  COVERAGE-GAP %s" % g)
    if gaps:
        print("  %d of %d page x viewport readings never arrived: re-run serially (browser legs"
              " share one CDN budget). Do not read the problems=0 line below as green."
              % (len(gaps), intended))
    print("problems=%d  coverage-gaps=%d (readings %d of %d)  unpaired-widths=%d"
          "  awaiting-decision=%d"
          % (len(problems), len(gaps), intended - len(gaps), intended, len(pair_gaps),
             len(advisories)))
    return 1 if (problems or gaps or pair_gaps) else 0


if __name__ == "__main__":
    sys.exit(main())
