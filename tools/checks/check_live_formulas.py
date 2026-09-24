# -*- coding: utf-8 -*-
"""Measure the display formulas a reader actually gets, on the live page, in a real browser.

Why this file exists (round 74): round 73 fixed 11 formulas that dragged inside the live laptop
column and *proved* the fix by pointing Playwright at the published pages. That proof lived in a
scratch script, so the standing claim "the live page lays our math out" was again not reproducible
from the repo — the same defect class rounds 57 and 58 landed judges for. This is the durable copy,
widened from the 11 touched pages to every page that authors a display formula.

What only a browser can see, and what each leg therefore is:
  authored fit   `check_content_overflow.py` renders the LaTeX we wrote and sweeps two columns.
                 It proves the source fits; it cannot prove the platform shipped it.
  this leg       fetches the reader's own document, hydrates it, and measures the painted formula.
                 Catches a page GitBook rebuilt from stale markup, a formula the platform dropped,
                 a `.katex-error` the offline build does not raise, and a wrapper whose markup
                 changed so the overflow scroller is no longer there to save the reader.
  column         `<main>` is read per page and printed: at a 1280px window the site's own sidebar
                 (288px) and page TOC (256px) leave 608px, not the 768px a copy of the HTML reads
                 (round 73). The column is the platform's to give, so a value away from the
                 certified 768 is reported, never counted as a finding.

Judged per live formula: `.katex-error` present, wrapper markup not the expected scroller, painted
text containing stray LaTeX (`[t]` an unsupported amsmath option leaves in front of the reader,
round 73), or ink wider than its scroller by >= --min-over px.

Ink, not boxes: `.katex-display > .katex { display:block; white-space:nowrap }` makes the element
box equal the container, so `getBoundingClientRect()` on it would always read "fits". The only
honest width is a Range over the formula's contents, sampled at both scroll ends and max'd.

The ruler carries a control that asserts it can SEE a drag: the widest formula on the first page
has its scroller narrowed by script, and the judge must then report the drag. Without that, a probe
that quietly measured boxes would print the same green as a probe that works.

Coverage is kept out of the content bucket on purpose (the lesson round 67 wrote into the sibling
asset axis): a page this run never reached proves nothing, so "loaded 99 of 106, 0 findings" must
not read as clean. Load failures get their own bucket, one cooldown retry, and they still exit 1.
`--selftest` drives that accounting with synthetic results, including the vacuity case, so no
future edit can merge the buckets back together.

Every page gets a bounded budget (load, then a best-effort idle wait, then a settle) and the run
throttles between pages. Round 74's first 106-page sweep died that way and could not be told apart
from a slow one: its browser driver exited while the parent blocked on the dead pipe, no per-page
budget existed to move on, and a page that long-polls can sit out `networkidle`'s whole timeout.
Progress now prints per page as it is measured.

Usage:
    python tools/checks/check_live_formulas.py                  # every page with display math
    python tools/checks/check_live_formulas.py --limit 12       # a fast sample
    python tools/checks/check_live_formulas.py --pages 06-memory-rag/graphrag.md
    python tools/checks/check_live_formulas.py --eyeball 06-memory-rag/graphrag.md
        -> PNG of every formula block on that page, for a human look
    python tools/checks/check_live_formulas.py --selftest       # offline: the bucket accounting
"""
import argparse
import io
import os
import re
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except AttributeError:
    pass

import live_aria_manifest as L                        # noqa: E402
import check_widget_visibility_live as wl             # noqa: E402
import check_content_overflow as CO                   # noqa: E402

VIEWPORT = 1280            # the window round 73 measured the laptop column at
BAR_DEFAULT = 16           # one glyph at KaTeX's own size; less is sub-pixel rounding
GOTO_MS = 45000            # bounded: an unbounded wait is what made round 74's sweep unobservable
IDLE_MS = 8000             # best-effort networkidle; a long-polling page must not eat the budget
SETTLE_MS = 2000           # GitBook mounts the navigation panels after hydration
REHYDRATE_MS = 5000        # second look before a count mismatch becomes a finding
THROTTLE_S = 0.8           # round 67: the CDN slow-walks an unthrottled sweep
COOLDOWN_S = 15            # a failed page is retried once after the rate has had time to relax
# The junk a reader sees when KaTeX paints an unsupported construct as text (mirrors the offline
# axis' STRAY_RE, but reads painted text, so it also catches what only the platform's build shows).
STRAY = re.compile(r"\[\s*[tbc]\s*\]|\\(?:begin|end)\{|\\hphantom|\\text\{")

# Shared by the probe and by the live control, so the two can never drift apart: an element is
# "hidden" when some ancestor up to <main> takes it out of the layout. GitBook does exactly this to
# the inactive panel of {% tabs %}, where a formula is meant to have no box until it is clicked.
CLASSIFY = r"""
  const hiddenReason = (el, root) => {
    for (let e = el; e && e !== root.parentElement; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.display === 'none') return 'display:none' + (e.dataset.gt ? ' ' + e.dataset.gt : '');
      if (cs.visibility === 'hidden' || cs.visibility === 'collapse') return 'visibility:' + cs.visibility;
      if (e.getAttribute('aria-hidden') === 'true') return 'aria-hidden';
    }
    return null;
  };
"""

PROBE = r"""
() => {
  const main = document.querySelector('main');
""" + CLASSIFY + r"""
  const rows = [];
  const measure = (k, wrap) => {
    const r = document.createRange();
    r.selectNodeContents(k);
    wrap.scrollLeft = 0; const a = r.getBoundingClientRect();
    wrap.scrollLeft = 1e5; const b = r.getBoundingClientRect();
    wrap.scrollLeft = 0;
    return Math.round(Math.max(a.width, b.width) * 100) / 100;
  };
  main.querySelectorAll('.katex-display').forEach((d, i) => {
    const wrap = d.parentElement;
    const k = d.querySelector('.katex-html') || d.querySelector('.katex');
    if (!wrap || !k || !/overflow-x-auto/.test(String(wrap.className))) {
      rows.push({i: i, err: 'unexpected math wrapper markup'}); return;
    }
    if (k.clientWidth === 0) {
      rows.push({i: i, hidden: hiddenReason(d, main), err: 'formula has no box yet'}); return;
    }
    rows.push({i: i, nat: measure(k, wrap), cw: wrap.clientWidth,
               box: Math.round(wrap.getBoundingClientRect().width),
               err: !!d.querySelector('.katex-error'),
               text: (k.innerText || '').replace(/\s+/g, ' ').slice(0, 160)});
  });
  // Controls go in LAST: a box planted before the reading would stretch a shrink-to-fit wrapper
  // and make the page's own numbers wrong (round 73 was fooled by exactly this).
  const ctl = {};
  [200, 960].forEach(w => {
    const d = document.createElement('div');
    d.style.cssText = 'position:absolute;left:-9999px;top:0;width:' + w + 'px';
    document.body.appendChild(d);
    ctl['plant-' + w] = Math.round(d.getBoundingClientRect().width);
    d.remove();
  });
  return {main: Math.round(main.getBoundingClientRect().width), n: rows.length, rows: rows,
          vw: innerWidth, ctl: ctl, fonts: document.fonts.check('16px KaTeX_Main')};
}
"""

# The classifier is worth nothing if it cannot tell a hidden panel from a formula that simply never
# painted, so it is planted on the reader's own page and both answers are demanded: a
# `display:none` copy must read hidden, a copy squeezed to zero width but left in flow must not.
CLASSIFY_CONTROL = r"""
() => {
""" + CLASSIFY + r"""
  const main = document.querySelector('main');
  const src = main.querySelector('.katex-display');
  if (!src) return {skipped: 'no formula on this page to clone'};
  const out = {};
  const cases = [['display-none', 'none', null], ['zero-width-visible', '', '0px']];
  for (const [name, disp, width] of cases) {
    const c = src.cloneNode(true);
    c.style.display = disp; c.style.width = width;
    main.appendChild(c);
    const k = c.querySelector('.katex-html') || c.querySelector('.katex');
    out[name] = {boxless: k.clientWidth === 0, reason: hiddenReason(c, main)};
    c.remove();
  }
  out['restored'] = src.parentElement.clientWidth > 0;
  return out;
}
"""


def authored_counts():
    """{page: display formulas the repo authors}, the denominator this leg must match."""
    counts = {}
    for rel, _src in CO.authored_display():
        counts[rel] = counts.get(rel, 0) + 1
    return counts


def live_url(page, index):
    """The reader's URL for a docs page, resolved through llms.txt — never guessed."""
    text = io.open(os.path.join(DOCS, page), encoding="utf-8").read()
    m = re.search(r"^# (.+)$", text, flags=re.M)
    assert m, "%s has no '# ' heading, so its published title cannot be resolved" % page
    url = index.get(wl.norm(m.group(1).strip())) or ""
    if url.endswith(".md"):
        url = url[:-3]          # the .md endpoint is markup, not the document a reader opens
    assert url, "no live HTML URL for %s" % page
    return url


def judge(page, rep, want, bar, bad, reads):
    """Turn one page's measurements into findings; returns (measured, hidden, worst row).

    Only rows with ink count as measured: a formula with no box says nothing about drag. A boxless
    formula inside an inactive GitBook panel is the platform working as designed (the reader has to
    click the tab), so it is reported, not judged — a boxless formula in plain flow is a finding.
    """
    if rep["n"] != want:
        bad.append("%s: the live page carries %d display formulas, the repo authors %d"
                   % (page, rep["n"], want))
    measured = hidden = 0
    worst = None
    for r in rep["rows"]:
        if r.get("err") is True:
            bad.append("%s#%d: .katex-error on the live page" % (page, r["i"]))
            continue
        if "nat" not in r:
            if r.get("hidden"):
                hidden += 1
            else:
                bad.append("%s#%d: %s after %d read(s), with no hidden ancestor — the reader was "
                           "shown an empty box" % (page, r["i"], r["err"], reads))
            continue
        measured += 1
        hit = STRAY.search(r["text"])
        if hit:
            bad.append("%s#%d: paints %r as text on the live page" % (page, r["i"], hit.group(0)))
        drag = r["nat"] - r["cw"]
        if drag >= bar:
            bad.append("%s#%d: drag %dpx at the live column (%.2f ink in %dpx)"
                       % (page, r["i"], int(round(drag)), r["nat"], r["cw"]))
        if worst is None or r["nat"] > worst["nat"]:
            worst = r
    return measured, hidden, worst


def calibrate(pg, rep, bar):
    """Prove the judge can see a drag, by making the column narrower under a real formula."""
    target = max((r for r in rep["rows"] if "nat" in r), key=lambda r: r["nat"], default=None)
    if target is None:
        return "no measured formula to calibrate against"
    # Narrow by a fixed amount rather than to a fixed width, so the control fires whatever the
    # page's own formulas happen to be — a bar the probe could never reach is not a control.
    width = max(1, int(target["nat"]) - 100)
    got = pg.evaluate(
        "({i, width}) => { const d = document.querySelectorAll('main .katex-display')[i];"
        " const w = d.parentElement, k = d.querySelector('.katex-html');"
        " w.style.width = width + 'px';"
        " const r = document.createRange(); r.selectNodeContents(k);"
        " w.scrollLeft = 0; const a = r.getBoundingClientRect();"
        " w.scrollLeft = 1e5; const b = r.getBoundingClientRect();"
        " const nat = Math.max(a.width, b.width); const cw = w.clientWidth;"
        " w.style.width = ''; w.scrollLeft = 0;"
        " return {nat: Math.round(nat * 100) / 100, cw: cw}; }",
        {"i": target["i"], "width": width})
    drag = got["nat"] - got["cw"]
    assert drag >= bar, ("ruler cannot see a drag: a %dpx scroller holding %.2fpx of ink read %+.2f "
                         "— this probe measures boxes, not ink" % (got["cw"], got["nat"], drag))
    return ("ruler ok: the %.2fpx formula of block #%d squeezed into %dpx reads drag=%dpx"
            % (got["nat"], target["i"], got["cw"], int(round(drag))))


def classify_control(pg):
    """Assert the hidden/visible classifier can tell a collapsed panel from an unpainted box.

    Without this, the judge would mark a genuinely-empty formula 'hidden' and let it pass, because
    the classifier and the acceptance rule are written by the same hand.
    """
    out = pg.evaluate(CLASSIFY_CONTROL)
    if out.get("skipped"):
        return "classifier control: %s" % out["skipped"]
    dn, zw = out["display-none"], out["zero-width-visible"]
    assert dn["boxless"] and dn["reason"], (
        "classifier blind: a display:none clone read boxless=%s reason=%r — a hidden panel would "
        "be judged as content" % (dn["boxless"], dn["reason"]))
    assert zw["boxless"] and not zw["reason"], (
        "classifier too eager: a zero-width clone left in flow read reason=%r — an empty box "
        "would be excused as hidden" % zw["reason"])
    assert out["restored"], "classifier control left the page's own formula shrunk"
    return ("classifier ok: a display:none copy reads hidden (%s), a zero-width in-flow copy "
            "reads no-reason — so 'hidden' cannot excuse an empty box" % dn["reason"])


def run(pages, counts, bar, eyeball):
    from playwright.sync_api import sync_playwright
    entries = wl.llms_entries()
    index, ambiguous = wl.page_index(entries)
    assert not ambiguous, "ambiguous published titles: %s" % sorted(ambiguous)
    targets = [(p, live_url(p, index), counts[p]) for p in pages]
    print("%d pages resolve to live URLs (from llms.txt); bar=%dpx drag @ vw=%d"
          % (len(targets), bar, VIEWPORT))
    if eyeball:
        targets = [t for t in targets if eyeball in t[0]] or [
            (eyeball, live_url(eyeball, index), counts.get(eyeball, 0))]
    bad, stalls, cols, shots = [], [], {}, []
    checked = expected = reached = hidden = 0
    out_dir = tempfile.gettempdir()
    t0 = time.time()
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        for n, (page, url, want) in enumerate(targets, 1):
            for attempt in (1, 2):
                try:
                    ctx, pg, rep = open_page(br, url)
                except Exception as exc:
                    if attempt == 1:
                        print("  %s did not load (%s), cooling %ds and retrying once"
                              % (page, str(exc)[:60], COOLDOWN_S))
                        time.sleep(COOLDOWN_S)
                        continue
                    stalls.append("%s: unreachable within the %ds budget (%s)"
                                  % (page, GOTO_MS // 1000, str(exc)[:60]))
                    ctx = None
                break
            if ctx is None:
                time.sleep(THROTTLE_S)
                continue
            try:
                rep, reads = settled(pg, rep, want)
                if not rep["fonts"]:
                    stalls.append("%s: KaTeX webfont never loaded, widths would be fallback — "
                                  "this page was not measured" % page)
                    print("  %-46s FETCH  no math webfont" % page)
                    continue
                assert abs(rep["vw"] - VIEWPORT) <= 3, "asked %d, page says %d" % (VIEWPORT, rep["vw"])
                assert rep["ctl"]["plant-200"] == 200 and rep["ctl"]["plant-960"] == 960, \
                    "the ruler clamps on the live page: %s" % rep["ctl"]
                if n == 1:
                    print("  " + calibrate(pg, rep, bar))
                    print("  " + classify_control(pg))
                got, hid, worst = judge(page, rep, want, bar, bad, reads)
                checked += got
                hidden += hid
                expected += min(want, got + hid)   # a count mismatch is a PROBLEM, not a floor trip
                reached += 1
                cols[rep["main"]] = cols.get(rep["main"], 0) + 1
                if eyeball:
                    blocks = pg.query_selector_all(".katex-display")
                    for j in range(min(len(blocks), rep["n"])):
                        path = os.path.join(out_dir, "live_formula_%s_%d.png"
                                            % (re.sub(r"\W+", "_", page)[-40:], j))
                        blocks[j].screenshot(path=path)
                        shots.append(path)
                elif worst:
                    print("  %-46s main=%d  %d/%d formulas  widest ink=%.1f in %dpx%s  [%dm%02ds]"
                          % (page, rep["main"], got, want, worst["nat"], worst["cw"],
                             "  (read x%d)" % reads if reads > 1 else "",
                             int(time.time() - t0) // 60, int(time.time() - t0) % 60))
                else:
                    # a page that measured nothing used to print nothing at all, and only the
                    # PROBLEM lines at the end betrayed it
                    print("  %-46s main=%d  MEASURED NOTHING (%d rows, %d hidden)%s"
                          % (page, rep["main"], rep["n"], hid,
                             "  (read x%d)" % reads if reads > 1 else ""))
            finally:
                ctx.close()
            time.sleep(THROTTLE_S)              # the CDN slow-walks an unthrottled sweep (round 67)
        br.close()
    if eyeball:
        print("eyeball PNGs (%d):" % len(shots))
        for s in shots:
            print("  " + s)
        return 0
    return account(reached, len(targets), checked, expected, cols, bad, stalls, hidden)


def open_page(br, url):
    """Load one reader page and measure it. Bounded, so a dead transport cannot hang the sweep."""
    ctx = br.new_context(viewport={"width": VIEWPORT, "height": 1200}, device_scale_factor=2)
    try:
        pg = ctx.new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=GOTO_MS)
        try:
            pg.wait_for_load_state("networkidle", timeout=IDLE_MS)   # a hint, not a gate
        except Exception:
            pass
        pg.wait_for_timeout(SETTLE_MS)           # the panels mount after hydration
        return ctx, pg, pg.evaluate(PROBE)
    except Exception:
        ctx.close()
        raise


def settled(pg, rep, want):
    """Re-read while the page disagrees with the repo, lacks the math font, or has an empty box.

    A boxless row that the classifier marks hidden is an inactive {% tabs %} panel working as
    designed — it will never paint until a click — so it must not spin the re-read budget. Only a
    boxless row with no hidden ancestor is worth a second look (it may still be hydrating).
    """
    reads = 1
    def pending():
        if rep["n"] != want or not rep["fonts"]:
            return True
        return any("nat" not in r and not r.get("hidden") and r.get("err") != "unexpected math wrapper markup"
                   for r in rep["rows"])
    while reads <= 2 and pending():
        pg.wait_for_timeout(REHYDRATE_MS)
        rep = pg.evaluate(PROBE)
        reads += 1
    return rep, reads


def account(reached, total, checked, expected, cols, problems, stalls, hidden=0, quiet=False):
    """Content findings and coverage gaps, kept in separate buckets — either one fails the run."""
    lines = ["", "checked %d live display formulas on %d of %d pages" % (checked, reached, total),
             "live <main> widths seen: %s  (the column is the platform's, reported not judged;"
             " 768 is the certified bar)"
             % ", ".join("%dpx x%d" % (w, c) for w, c in sorted(cols.items()))]
    if hidden:
        lines.append("  %d formula(s) had no box but sit in a hidden ancestor (an inactive "
                     "{%% tabs %%} panel, reported not judged — the reader must click to see it)"
                     % hidden)
    lines += ["  PROBLEM %s" % b for b in problems]
    lines += ["  FETCH-FAILURE %s" % s for s in stalls]
    if stalls:
        lines.append("  %d page(s) were never measured: that is a coverage gap, not a content "
                     "finding. Re-run — do not read it as green." % len(stalls))
    lines.append("live formula verdict: pages=%d/%d checked=%d hidden=%d problems=%d fetch-failures=%d"
                 % (reached, total, checked, hidden, len(problems), len(stalls)))
    if not quiet:
        for line in lines:
            print(line)
    assert reached > 0, "vacuity: %d of %d pages were reached, so nothing was measured" % (reached, total)
    assert checked >= min(25, expected), ("vacuity floor: %d of the %d formulas on the reached pages "
                                          "were measured at all" % (checked, expected))
    return 1 if (problems or stalls) else 0


def account_selftest():
    """The two buckets must stay apart, and an empty sample must never read as green."""
    def code(problems, stalls, reached=3, total=3, checked=30, expected=30, hidden=0):
        return account(reached, total, checked, expected, {608: reached},
                       problems, stalls, hidden=hidden, quiet=True)

    assert code([], []) == 0, "a clean sweep must pass"
    # hidden formulas are reported, never judged — they must not turn a clean run red
    assert code([], [], hidden=7) == 0, "a hidden-tab formula must not be a finding"
    # a page this run never reached is not a content finding, and it still fails the run
    assert code([], ["x.md: unreachable"]) == 1, "a coverage gap must not exit 0"
    # ... and a real finding must not hide in the coverage bucket either
    assert code(["y.md: drag 40px"], []) == 1, "a content finding must not exit 0"
    assert code(["y.md: drag 40px"], ["x.md: unreachable"]) == 1, "both buckets at once must fail"
    for reached, total, checked, expected, why in [(0, 5, 0, 0, "no page reached"),
                                                   (5, 5, 4, 25, "measured almost nothing")]:
        try:
            account(reached, total, checked, expected, {}, [], [], quiet=True)
        except AssertionError:
            continue
        raise AssertionError("vacuity floor did not fire: %s" % why)
    # a --limit sample is a partial run, not a vacuous one
    assert code([], [], reached=6, total=106, checked=13, expected=13) == 0, \
        "a sample must not trip the floor"
    print("accounting selftest ok: content and coverage stay in their own buckets, "
          "hidden formulas are reported not judged, an empty sample cannot read green")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="*", default=None, help="docs-relative pages to check")
    ap.add_argument("--limit", type=int, default=0, help="check only the first N pages")
    ap.add_argument("--min-over", type=int, default=BAR_DEFAULT,
                    help="drag px counted as a defect (one glyph at KaTeX's size)")
    ap.add_argument("--eyeball", metavar="PAGE", help="screenshot every formula of one page and exit")
    ap.add_argument("--selftest", action="store_true",
                    help="offline: exercise the coverage/content bucket accounting")
    args = ap.parse_args()

    if args.selftest:
        return account_selftest()
    counts = authored_counts()
    pages = args.pages or sorted(counts)
    for p in pages:
        assert p in counts, "%s authors no display formula (or does not exist)" % p
    if args.limit:
        pages = pages[:args.limit]
    return run(pages, counts, args.min_over, args.eyeball)


if __name__ == "__main__":
    sys.exit(main())
