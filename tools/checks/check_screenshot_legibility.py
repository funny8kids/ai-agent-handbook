# -*- coding: utf-8 -*-
"""Judge whether a real product screenshot is still readable at the width the reader gets.

Why this file exists (round 75). Rounds 68, 70 and 74 each carried the same line in their "left
over" section: the eight third-party UI screenshots are the only figures in the book that no axis
has ever measured. Every other figure is authored markup -- Mermaid (geometry axis) or self-drawn
SVG (six legs) -- so the size of its text is readable off the source. A PNG carries no source: the
glyph size inside it belongs to somebody else's app window, and all this repo controls is how wide
the bitmap gets laid out.

What the reader actually gets, measured live (round 75, real browser, hydrated, both DPRs):
  authored   8 screenshots, 1280 px (one 1040 px) wide bitmaps of a real UI
  painted    608 px -- the platform pins every content image to the column: a 480 px bitmap is
             STRETCHED up to 608 and a 1280 px bitmap SHRUNK to 608, image and wrapper both
  served     the `~gitbook/image` proxy answers 768 px at DPR 1 and only 640 px at DPR 2
So vendor UI text drawn at 13 px reaches the reader at 13 x 608/1280 = 6.2 px. A 2x display does not
rescue it: device pixels make a glyph sharper, never bigger, and the proxy hands over *less* detail
at DPR 2 than at DPR 1.

Verdicts, kept apart by who can act on them:
  SHRUNK-UNDISCLOSED  the bitmap is laid out below authored scale and the figure says nothing about
                      clicking it. Ours to fix, either way: re-author the raster, or tell the reader.
  STRETCHED           a bitmap narrower than the column, blown up. Ours.
  CAP                 the proxy resamples below the authored width. The platform's, so it is reported
                      and never judged (round 73's rule for the column itself).
  COVERAGE            a figure this leg could not attribute to a repo asset, a page whose images
                      never all had a box, or a box that never received a bitmap. Fails the run:
                      "measured nothing" must not read green.

The exemption is two-sided on purpose. Round 75 measured that GitBook's click-to-zoom DOES restore
the bitmap: the lightbox is portalled to <body>, fetches the AUTHORED bytes (naturalWidth 1280, not
the proxy's 640) and paints 1216 px -- scale 0.950 on all seven 1280 px screenshots, 1.000 on the
1040 px one. So a wide screenshot can honestly serve as an overview -- but only if (a) the figure's
own lines tell the reader to click, and (b) `--zoom` measures that the platform still delivers
authored scale. Prose alone cannot buy the exemption, and if the platform ever drops the lightbox
the exemption dies with it, loudly.

Why the prose is not a nicety: at 608 px the MCP Inspector screenshot's own status line reads as
"Weather in Boston: sunny, 14C" to a careful reader. Clicked open it says 24C. The bitmap is the
same; the width was the difference between a legible number and a wrong one.

Controls, because "8/8 flagged" is only a finding if the ruler can also read a clean case:
  * phantoms per asset: re-authored at the column must read clean, at 2x must fire SHRUNK, at half
    must fire STRETCHED -- so the verdict is a scale rule, not a list of eight suspects;
  * the disclosure leg has its own planted pair: a caption that promises the zoom must read told,
    the same caption with the promise removed must read untold (otherwise "told" is a keyword that
    matches the page by accident);
  * the live leg re-asserts its premise (paint == column, wrapper == column) on every figure, so the
    day GitBook gives rasters a scroller this axis says so instead of going quiet;
  * the name matcher is asserted to resolve: a CAP leg that matched nothing reported `cap=0` on its
    first run here while the proxy was serving 640 of 1280. That is a false clean, and it is now a
    selftest case;
  * coverage counts EVERY figure that got a box, and the lightbox read waits for the modal's own
    bitmap. Both were instrument bugs found on the first full run: a natural-width bar under-counted
    three pages at DPR 2 (the proxy shrinks natural width as DPR rises), and reading "the widest
    image on the page" after a click scored the still-present in-column copy -- two honest
    screenshots were convicted of a ZOOM-LIE they did not commit, at exactly the column width;
  * the CAP tally has no size gate of its own (round 75, same lesson one run later): it used to
    share the ≥400 px bar, so the finding went QUIETER as the platform capped harder -- 18 lines on
    one全站 run, 17 on the next, because DPR 2 served one PNG under the bar;
  * a bitmap the browser never handed over (naturalWidth 0) is booked as COVERAGE, never as a CAP.
    Found the same run: two figures read 0 px in-column and one run convicted them of a broken
    click-to-zoom, because clicking a figure whose pixels have not arrived opens nothing. "0 px" is
    a measurement the probe lost, not a width the platform chose -- and a cap list that can be
    padded with zeros is how a policy gets invented out of a timeout;
  * the click is retried (up to 3) on a figure whose bitmap is confirmed loaded, and the attempt
    count is printed. The promise under test is "a pointer on a loaded figure opens the full-size
    view"; a swallowed first click is this probe's problem, and the log has to be able to tell that
    apart from the platform refusing to open.

Usage:
    python tools/checks/check_screenshot_legibility.py                 # offline pre-check
    python tools/checks/check_screenshot_legibility.py --live --zoom   # the standing reading
    python tools/checks/check_screenshot_legibility.py --eyeball mcp   # save the reader's pixels
    python tools/checks/check_screenshot_legibility.py --selftest
"""
import argparse
import io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except AttributeError:
    pass

# Round 73/74: the column a reader at a 1280 window is served. --live re-measures it every run.
COLUMN = 608
MIN_SCALE = 0.90     # painted must stay within 10% of authored, in either direction
CAP_TOL = 0.90       # report when the proxy hands over less than this share of authored width
ZOOM_MIN = 0.90      # the lightbox must paint within 10% of authored width to count as a rescue
RASTER = re.compile(r"!\[[^\]]*\]\(([^)]+\.(?:png|jpe?g))(?:\s+\"[^\"]*\")?\)", re.I)
# What a reader has to be told, in their own language, next to the picture.
ZOOM_PHRASE = re.compile(r"(?:点开|点击|单击|click)[^。！？\n]{0,16}(?:放大|原图|原始尺寸|全图|1[:：]?1)")


def md_files():
    for root, dirs, files in os.walk(DOCS):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for f in sorted(files):
            if f.endswith(".md"):
                yield os.path.join(root, f)


def asset_path(page, ref):
    """Resolve a markdown image ref to a repo file, or None for a remote/absolute source."""
    ref = ref.split("?")[0].strip()
    if ref.startswith(("http://", "https://", "/")):
        return None
    p = os.path.normpath(os.path.join(os.path.dirname(page), ref))
    return p if os.path.isfile(p) else None


def size_of(path):
    from PIL import Image
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (0, 0)


def told(text, ref):
    """Does the page tell the reader, at THIS figure, that clicking gives the full-size view?

    Only the lines belonging to the figure count: the few before the image and the caption/source
    lines after it. A promise printed elsewhere on the page is not a promise about this picture.
    """
    lines = text.splitlines()
    at = next((i for i, ln in enumerate(lines) if ref in ln), None)
    if at is None:
        return False
    window = lines[max(0, at - 4):at] + lines[at + 1:at + 5]
    return bool(ZOOM_PHRASE.search(" ".join(window)))


def figures():
    """[(page, ref, abs path or None, w, h, told)] over every raster figure; page is DOCS-relative.

    DOCS-relative because every live leg (`live_url`, the llms.txt index) takes a docs path; this
    axis' first run learned that by crashing on `docs/docs/05-tool-protocol/mcp.md`.
    """
    out = []
    for page in md_files():
        rel = os.path.relpath(page, DOCS).replace("\\", "/")
        text = io.open(page, encoding="utf-8").read()
        for m in RASTER.finditer(text):
            ref = m.group(1)
            if not re.search(r"\.(?:png|jpe?g)$", ref.split("?")[0], re.I):
                continue
            ap = asset_path(page, ref)
            if ap is None:
                out.append((rel, ref, None, 0, 0, False))
                continue
            w, h = size_of(ap)
            out.append((rel, ref, ap, w, h, told(text, ref)))
    return out


def judge(rows, column, min_scale, problems):
    """Per reference: does the reader get the bitmap at its authored size, and were they told?

    The platform rule round 75 measured at DPR 1 and DPR 2: a content image is pinned to the column
    -- image and wrapper both paint the column whether its own pixels are 480 or 1280. There is no
    horizontal scroller for a raster (round 73 found one for formulas; images get none), so the
    bitmap's own width is the repo's only freedom, and both directions off 1.0 are defects: shrink
    makes the glyphs inside smaller than the app that drew them, stretch makes them soft at the same
    size. Returns {asset key: (w, h, scale, told)} -- last page wins, the phantoms need one row.
    """
    seen = {}
    for page, ref, ap, w, h, is_told in rows:
        if ap is None:
            problems.append("%s: raster figure %r is not a repo asset, so its width cannot be "
                            "audited (remote images are excluded from every figure leg)" % (page, ref))
            continue
        if w <= 0:
            problems.append("%s (%s): the bitmap will not open, so the reader's size is unknown"
                            % (page, ref))
            continue
        scale = column / float(w)
        key = os.path.relpath(ap, REPO).replace("\\", "/")
        prev = seen.get(key)
        # One asset can sit on two pages (round 75: the OpenHands screenshot). Judgements are
        # per reference below, but `seen` feeds the verification leg, which needs to know whether
        # ANY page tells -- otherwise the last page walked decides for both.
        seen[key] = (w, h, scale, is_told or (prev[3] if prev else False))
        if scale < min_scale and not is_told:
            problems.append("SHRUNK-UNDISCLOSED %s (%s): %dx%d authored painted %dpx = scale %.3f, "
                            "and the figure never says it can be clicked open - every glyph inside "
                            "somebody else's UI shrinks with it"
                            % (key, page, w, h, column, scale))
        elif scale > 1.0 / min_scale:
            problems.append("STRETCHED %s (%s): %dpx authored painted %dpx = %.3f - a bitmap blown "
                            "past its own pixels is soft, and the glyphs inside stay the size the "
                            "authoring app drew them" % (key, page, w, column, scale))
    return seen


def cap_line(page, dpr, name, authored_w, served_w, paint):
    """The CAP tally's only gate is the served width itself -- never a natural-width floor.

    That floor was the third instrument bug here: figures under 400 px went uncounted, so the
    finding got quieter as the platform capped harder. A rule whose report shrinks when the
    problem grows is not a rule.
    """
    if served_w >= authored_w * CAP_TOL:
        return None
    if served_w <= 0:
        # Zero is "the browser never handed us a bitmap", which is a coverage gap (the live leg
        # books it there), not a width the platform chose. Round 75 measured it: two figures read
        # 0 px in-column, and a tally that counted those as caps would be reporting a policy that
        # never happened while hiding the fact that the probe saw nothing.
        return None
    return ("%s dpr%d %s: authored %dpx, the browser was handed %dpx for a %dpx paint"
            % (page, dpr, name, authored_w, served_w, paint))


def match_authored(src, authored):
    """(basename, (w, h)) for a served URL, or (None, None).

    Round 68's lesson applies here: the proxy URL is double-encoded (`...%252Ffile.png`), so a
    decoded filename is NOT available, and matching a decoded name silently misses everything --
    which is how this axis' first run printed `cap=0` while the proxy served 640 of 1280. The
    asset's basename appears literally in the encoded URL, so match on that.
    """
    for name, wh in authored.items():
        if name in src:
            return name, wh
    return None, None


def controls(seen, column, min_scale):
    """Differential phantoms, so the verdict is a scale rule and not a list of eight suspects."""
    assert seen, "no raster figures found at all - the extractor is dead, not the site clean"
    cases = 0
    for key, (w, h, _scale, _told) in seen.items():
        ap = os.path.join(REPO, key)
        for width, want in ((column, None), (column * 2, "SHRUNK"), (column // 2, "STRETCHED")):
            j = []
            judge([("phantom", key, ap, width, h, False)], column, min_scale, j)
            if want is None:
                assert not j, "control failed: a %dpx copy of %s still reads dirty: %s" % (column, key, j)
            else:
                assert j and j[0].startswith(want), \
                    "control failed: a %dpx copy of %s did not fire %s (%s)" % (width, key, want, j)
            cases += 1
    print("controls: %d bitmaps x 3 phantoms (at %dpx clean / %dpx SHRUNK / %dpx STRETCHED) = "
          "%d planted cases, all as expected" % (len(seen), column, column * 2, column // 2, cases))
    # Whether any real figure is told is the round's finding, not an instrument check: the told/untold
    # directions are both exercised in --selftest, so an all-untold book must print its problems,
    # not crash here.
    n = sum(1 for v in seen.values() if v[3])
    print("disclosure: %d of %d bitmaps tell the reader the figure opens at full size"
          % (n, len(seen)))


PROBE = r"""
() => {
  const main = document.querySelector('main');
  const rows = [];
  const all = main.querySelectorAll('img');
  all.forEach((im) => {
    const r = im.getBoundingClientRect();
    if (!r.width) return;
    const wr = im.parentElement.getBoundingClientRect();
    rows.push({nat: [im.naturalWidth, im.naturalHeight],
               paint: Math.round(r.width), wrap: Math.round(wr.width),
               src: String(im.currentSrc || im.src || '')});
  });
  return {main: Math.round(main.getBoundingClientRect().width), vw: innerWidth,
          dom: all.length, rows: rows};
}
"""

# The lightbox is portalled to <body>, so anything still inside <main> is the pre-click figure.
# Round 75 learned this the hard way: the first zoom leg reported 608 px for two of the eight
# screenshots -- that was the in-column image, read while the modal's own bytes were still
# decoding. Reading "the widest image on the page" is not a measurement of the lightbox.
ZOOM_READ = r"""
() => {
  const dlg = document.querySelector('[class*="zoom-modal"],[class*="lightbox"]');
  let best = null;
  if (dlg) document.querySelectorAll('img').forEach((im) => {
    if (im.closest('main')) return;
    const r = im.getBoundingClientRect();
    if (r.width >= (best ? best.w : 0))
      best = {w: Math.round(r.width), nat: im.naturalWidth, paint0: Math.round(r.height)};
  });
  return {open: !!dlg, img: best};
}
"""


def read_page(pg, url):
    pg.goto(url, wait_until="domcontentloaded", timeout=45000)
    try:
        pg.wait_for_load_state("networkidle", timeout=8000)      # a hint, not a gate (round 74)
    except Exception:
        pass
    pg.wait_for_timeout(2500)
    pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")   # lazy images need a scroll
    pg.wait_for_timeout(2000)
    pg.evaluate("() => window.scrollTo(0, 0)")
    pg.wait_for_timeout(600)


def live_leg(eyeball, zoom, dprs=(1, 2), limit=None):
    """Ask the reader's own browser what it paints, what bytes the proxy gave it, and what a click gives."""
    import check_widget_visibility_live as wl
    from check_live_formulas import live_url
    from playwright.sync_api import sync_playwright

    rows = figures()
    pages = sorted({p for p, _r, _a, _w, _h, _t in rows})
    if eyeball:
        pages = [p for p in pages if eyeball in p] or pages[:1]
    if limit:
        pages = pages[:limit]
    authored = {os.path.basename(os.path.relpath(a, REPO).replace("\\", "/")): (w, h)
                for p, r, a, w, h, t in rows if a}
    index, ambiguous = wl.page_index(wl.llms_entries())
    assert not ambiguous, "ambiguous published titles: %s" % sorted(ambiguous)
    capped, widths, shots, painted = [], {}, [], []
    stalls, unmatched, zoomed = [], [], {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        for n, page in enumerate(pages, 1):
            url = live_url(page, index)
            for dpr in dprs:
                ctx = br.new_context(viewport={"width": 1280, "height": 1200}, device_scale_factor=dpr)
                try:
                    pg = ctx.new_page()
                    read_page(pg, url)
                    rep = pg.evaluate(PROBE)
                    assert abs(rep["vw"] - 1280) <= 3, "window clamped: %s" % rep["vw"]
                    widths[rep["main"]] = widths.get(rep["main"], 0) + 1
                    # Coverage counts EVERY figure, not the ones whose natural width clears a
                    # threshold: the proxy shrinks natural width as DPR rises (mcp.md's SVG is 960
                    # at DPR 1 and 384 at DPR 2), so a filtered count reported a phantom gap.
                    # Settle before judging: a figure with no box yet, or a box whose bitmap is
                    # still in flight, is a read the probe lost -- not a content finding and not a
                    # clean measurement.
                    for _settle in range(4):
                        if (len(rep["rows"]) >= rep["dom"]
                                and all(r["nat"][0] for r in rep["rows"])):
                            break
                        pg.wait_for_timeout(1500)
                        rep = pg.evaluate(PROBE)
                    if len(rep["rows"]) < rep["dom"]:
                        stalls.append("%s dpr%d: only %d of %d figures had a box - coverage gap, not "
                                      "a clean read" % (page, dpr, len(rep["rows"]), rep["dom"]))
                    big = [r for r in rep["rows"] if r["nat"][0] >= 400]
                    # Every tally below is keyed off the URL match, NOT off a natural-width bar. The
                    # third instrument bug found here was the CAP leg sharing `big`'s 400 px floor:
                    # the finding shrank as the platform capped harder (the same page read cap=18 on
                    # one run, 17 on the next, because DPR 2 served the Inspector PNG under 400 px).
                    for r in rep["rows"]:
                        name, wh = match_authored(r["src"], authored)
                        if name is None:
                            # SVG figures belong to the geometry/legibility family (and the proxy
                            # rasterises them, which round 58's RASTERIZED already covers). Under
                            # 400 px an unmatchable URL is indistinguishable from an icon, so only
                            # report the sizes a figure could have.
                            if (not re.search(r"\.svg(?:%|&|$)", r["src"], re.I)
                                    and r["nat"][0] >= 400):
                                unmatched.append("%s dpr%d: a %dpx figure whose served URL matches no "
                                                 "repo asset (%s)"
                                                 % (page, dpr, r["nat"][0], r["src"][-70:]))
                            continue
                        # Fourth instrument bug: a bitmap the browser never handed over (nat=0, still
                        # decoding) is NOT a width-policy reading, and must not be tallied as a CAP.
                        # It is a coverage gap -- which must fail the run, or "the platform capped 18
                        # of 18" could quietly mean "we never saw 2 of them".
                        if r["nat"][0] == 0:
                            stalls.append("%s dpr%d %s: the figure had a %dpx box but no bitmap - "
                                          "coverage gap, not a cap and not a clean read"
                                          % (page, dpr, name, r["paint"]))
                            continue
                        assert abs(r["paint"] - rep["main"]) <= 2 and abs(r["wrap"] - rep["main"]) <= 2, \
                            ("premise broken on %s (dpr%s): a %dpx-natural figure paints %dpx in a "
                             "%dpx column/wrapper - GitBook no longer pins images to the column, so "
                             "this axis must be re-read before it is trusted"
                             % (page, dpr, r["nat"][0], r["paint"], rep["main"]))
                        painted.append((page, dpr, name, r["nat"][0], r["paint"]))
                        line = cap_line(page, dpr, name, wh[0], r["nat"][0], r["paint"])
                        if line:
                            capped.append(line)
                    if zoom and dpr == max(dprs):
                        zoom_leg(pg, page, authored, zoomed)
                    if eyeball:
                        for i, el in enumerate(pg.query_selector_all("main img")):
                            if el.evaluate("e => e.naturalWidth") < 400:
                                continue
                            path = os.path.join(tempfile.gettempdir(), "reader_%s_dpr%d_%d.png"
                                                % (re.sub(r"\W+", "_", page)[-24:], dpr, i))
                            el.screenshot(path=path)
                            shots.append(path)
                    print("  [%d/%d] %-44s dpr%d main=%d %d/%d figures, %d wide"
                          % (n, len(pages), page, dpr, rep["main"], len(rep["rows"]),
                             rep["dom"], len(big)))
                finally:
                    ctx.close()
        br.close()
    print("live <main> widths seen: %s"
          % ", ".join("%dpx x%d" % (w, c) for w, c in sorted(widths.items())))
    for p, d, name, nat, paint in painted:
        print("  painted   %-44s dpr%d  %-30s nat=%-5d paint=%d" % (p, d, name, nat, paint))
    for name, (ratio, got_w, aw, got_nat) in sorted(zoomed.items()):
        if ratio < 0:      # never print a fake measurement for a leg that measured nothing
            print("  zoom      %-34s authored=%-5d NO LIGHTBOX MEASURED (%d click attempts)"
                  % (name, aw, got_w))
            continue
        print("  zoom      %-34s authored=%d lightbox paints=%d scale=%.3f served nat=%d"
              % (name, aw, got_w, ratio, got_nat))
    if shots:
        print("reader-side pixels (look at these):")
        for s in shots:
            print("  " + s)
    return capped, stalls, unmatched, zoomed


def zoom_leg(pg, page, authored, zoomed):
    """Click each wide raster and measure what the lightbox paints, per asset.

    Poll until the modal's own bitmap has decoded: an unread modal is reported as no rescue, not
    silently scored against the in-column copy. A click is retried because the promise being tested
    is "a pointer on a loaded figure opens the full-size view" -- a swallowed first click is the
    probe's problem, and the attempt count printed below is what tells those two apart.
    """
    targets = []
    for el in pg.query_selector_all("main img"):
        info = el.evaluate("e => ({src: String(e.currentSrc || e.src)})")
        name, wh = match_authored(info["src"], authored)
        if name and wh and wh[0] > COLUMN / ZOOM_MIN:
            targets.append((el, name, wh[0]))
    for el, name, aw in targets:
        el.scroll_into_view_if_needed()
        for _ in range(8):
            if el.evaluate("e => e.complete && e.naturalWidth > 0"):
                break
            pg.wait_for_timeout(700)
        else:
            zoomed[name] = (-1, 0, aw, 0)
            print("  zoom      %-34s in-column bitmap never decoded (%dpx authored) - nothing to "
                  "click" % (name, aw))
            continue
        got, attempts, opened = None, 0, False
        rep = {"open": False}
        for attempts in range(1, 4):
            try:
                el.click()
            except Exception as exc:
                print("  zoom      %-34s CLICK FAILED attempt %d (%s)" % (name, attempts, str(exc)[:40]))
                pg.wait_for_timeout(700)
                continue
            for _attempt in range(4):
                pg.wait_for_timeout(1000)
                rep = pg.evaluate(ZOOM_READ)
                if rep["img"] and rep["img"]["nat"]:
                    got, opened = rep["img"], True
                    break
            if opened:
                break
            pg.keyboard.press("Escape")       # close whatever half-opened state the click left
            pg.wait_for_timeout(600)
        if not opened:
            # Record why: `open` separates "no lightbox at all" from "lightbox whose bitmap never
            # arrived", which are different promises broken in different ways.
            why = "opened, bitmap never decoded" if rep["open"] else "no lightbox opened"
            zoomed[name] = (-1, attempts, aw, 0)
            print("  zoom      %-34s %s after %d click(s) (%dpx authored) - nothing to read"
                  % (name, why, attempts, aw))
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            continue
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(800)
        if attempts > 1:
            # Print the rescue: "it opened on the second click" is the evidence that separates a
            # probe that misfires from a platform that will not deliver the promise.
            print("  zoom      %-34s opened on click #%d" % (name, attempts))
        prev = zoomed.get(name)
        reading = (got["w"] / float(aw), got["w"], aw, got["nat"])
        if prev is None or reading[0] > prev[0]:
            zoomed[name] = reading


def settle(problems, seen, zoomed, live_ran):
    """Turn 'the page promises a zoom' into a verified fact or a finding, never into a free pass."""
    told_assets = {os.path.basename(k): v for k, v in seen.items() if v[3] and v[2] < MIN_SCALE}
    for name, (w, h, scale, _t) in sorted(told_assets.items()):
        got = zoomed.get(name)
        if not live_ran:
            problems.append("UNVERIFIED %s: the figure tells the reader to click it open, but no "
                            "--live --zoom run backs that promise up" % name)
        elif got is None:
            problems.append("ZOOM-MISSING %s: the figure promises a click-to-zoom and the live leg "
                            "never measured one" % name)
        elif got[0] < 0:
            problems.append("ZOOM-MISSING %s: the figure promises a click-to-zoom; the live leg "
                            "clicked it %d time(s) and no lightbox was ever measured" % (name, got[1]))
        elif got[0] < ZOOM_MIN:
            problems.append("ZOOM-LIE %s: the figure promises a click-to-zoom, the lightbox paints "
                            "%.3f of the authored %dpx (%dpx)" % (name, got[0], w, got[1]))
    return told_assets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--column", type=int, default=COLUMN)
    ap.add_argument("--min-scale", type=float, default=MIN_SCALE)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--zoom", action="store_true")
    ap.add_argument("--eyeball", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    problems = []
    rows = figures()
    seen = judge(rows, args.column, args.min_scale, problems)
    controls(seen, args.column, args.min_scale)
    live_ran = bool(args.live or args.zoom or args.eyeball)
    capped = stalls = unmatched = []
    zoomed = {}
    if live_ran:
        capped, stalls, unmatched, zoomed = live_leg(args.eyeball, args.zoom or args.live,
                                                     limit=args.limit)
    told_assets = settle(problems, seen, zoomed, live_ran)
    print("\nraster figures audited: %d unique bitmaps over %d references, column %dpx, floor %.2f"
          % (len(seen), len(rows), args.column, args.min_scale))
    for line in problems:
        print("  PROBLEM " + line)
    for line in capped:
        print("  CAP (reported, not judged - the proxy's width is the platform's to give) " + line)
    for line in stalls + unmatched:
        print("  COVERAGE " + line)
    print("screenshot verdict: figures=%d told-and-verified=%d problems=%d cap=%d coverage=%d"
          % (len(seen), len(told_assets) if live_ran else 0, len(problems), len(capped),
             len(stalls) + len(unmatched)))
    return 1 if (problems or stalls or unmatched) else 0


def selftest():
    """The bar must be satisfiable, and both exemptions must be able to fail."""
    def one(w, is_told=False, h=720):
        ps = []
        judge([("t.md", "a.png", "a.png", w, h, is_told)], 608, MIN_SCALE, ps)
        return ps

    assert not one(608), "an image at exactly the column must pass"
    assert one(1280)[0].startswith("SHRUNK-UNDISCLOSED"), "a 2x-shrunk, untold image must fire"
    # 660 in a 608 column is 0.921, inside the 10% room. 680 was the number I first wrote here and
    # it fires at 0.894: a bar is only a bar if the selftest quotes the ratio, not the intent.
    assert not one(660), "10 pct of shrink is rounding room, not a defect"
    assert one(300)[0].startswith("STRETCHED"), "a bitmap blown up 2x must fire"
    assert not one(1280, True), "a told reader is the exemption, so it must not fire here"
    ps = []
    judge([("t.md", "https://x/a.png", None, 0, 0, False)], 608, MIN_SCALE, ps)
    assert ps and "not a repo asset" in ps[0], "a remote figure must be reported, not skipped"
    ps = []
    judge([("t.md", "a.png", "a.png", 0, 0, False)], 608, MIN_SCALE, ps)
    assert ps and "will not open" in ps[0], "an unreadable bitmap must be a finding, not a skip"
    # the disclosure reader: both directions, on the phrasing the pages actually use
    page = ("前导语\n\n![alt](../a/x.png)\n\n*《图：左栏 A；点开可放大到原始尺寸逐行读》*\n\n"
            "*来源：官方文档。*")
    assert told(page, "../a/x.png"), "a caption that promises the zoom must read told"
    assert not told(page.replace("点开可放大到原始尺寸逐行读", "把左栏 A 摊开给你看"), "../a/x.png"), \
        "the same caption without the promise must read untold"
    # the matcher: the proxy's double-encoding must not be able to make the CAP leg vacuous
    hit = match_authored("https://s/~gitbook/image?url=https%253A%252F%252Fcdn%252F02-x-ui.png",
                         {"02-x-ui.png": (1280, 720)})
    assert hit[0] == "02-x-ui.png", "the proxy URL must resolve to its authored asset: %s" % hit
    assert match_authored("https://s/x/~gitbook/image?url=other", {"02-x-ui.png": (1, 1)})[0] is None, \
        "an unmatchable URL must report, never pass silently"
    # the CAP tally must not be able to go quiet as the platform caps harder
    assert cap_line("p.md", 2, "a.png", 1280, 300, 608), "a 300px copy of a 1280px figure is a cap"
    assert not cap_line("p.md", 1, "a.png", 1280, 1280, 608), "a full-size copy is not a cap"
    assert not cap_line("p.md", 2, "a.png", 1280, 0, 608), \
        "a bitmap that never decoded is a coverage gap; calling it a cap reports a policy that "\
        "never happened and hides that the probe measured nothing"
    # the exemption must be revocable by measurement, in three directions
    seen = {"d/a.png": (1280, 720, 0.475, True)}
    ps = []
    settle(ps, seen, {}, live_ran=False)
    assert ps and ps[0].startswith("UNVERIFIED"), "an unmeasured promise is not a pass: %s" % ps
    ps = []
    settle(ps, seen, {"a.png": (0.95, 1216, 1280, 1280)}, live_ran=True)
    assert not ps, "a measured rescue must pass: %s" % ps
    ps = []
    settle(ps, seen, {"a.png": (0.55, 700, 1280, 768)}, live_ran=True)
    assert ps and ps[0].startswith("ZOOM-LIE"), "a promise the platform does not keep must fire: %s" % ps
    ps = []
    settle(ps, seen, {}, live_ran=True)
    assert ps and ps[0].startswith("ZOOM-MISSING"), "a promised zoom never seen must fire: %s" % ps
    ps = []
    settle(ps, seen, {"a.png": (-1.0, 3, 1280, 0)}, live_ran=True)
    assert (ps and ps[0].startswith("ZOOM-MISSING") and "-1.000" not in ps[0]
            and "3 time" in ps[0]), \
        "a click that never produced a lightbox is 'not measured', not a measurement of -1.000: %s" % ps
    print("selftest: 6 judge cases + told/untold pair + encoded-URL resolution + 3 CAP-tally "
          "directions + 5 exemption directions, all as expected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
