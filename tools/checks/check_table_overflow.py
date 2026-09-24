# -*- coding: utf-8 -*-
"""Table axis: does an authored table's ink ever get painted outside its own cell or column?

Why this file exists (round 63). The display-formula half of the round is in
`check_content_overflow.py`. Tables are the other content that has to live inside the reader's
column, and their failure mode is different in kind: GitBook does not render a `<table>` and gives
the page no horizontal scroller for one. Measured live this round, on the worst-candidate page:

    main = 768px, cell = 153px (a 5-column table, 768/5), cell style =
        width: min-width: clamp(100px, calc((100% - 0px) / 5), 100%)
    cell computed: overflow-wrap: anywhere, word-break: break-word, white-space: pre-wrap
    table container: `flex flex-col min-w-full w-fit`, overflow-x: visible  (NO scroller)

Two consequences, and the axis measures both instead of assuming them:
  * CONTENT SPILL: a cell can hold a run that has no break opportunity in it at all, and the ink
    then leaves the box and paints over the neighbouring column. Whether the platform allows that
    is a fact about one CSS rule, measured live: cells compute to `overflow-wrap: anywhere` +
    `word-break: break-word`, so even a run with nothing to break on stays inside its box. The
    reading across the 8 sampled pages (2131 cells, worst-candidate page a project index whose
    tables alone hold 1670 cells) is 0 spills. The rule is therefore asserted
    every run: if GitBook ever drops it, wide cells start painting over their neighbours and this
    axis goes red. The axis' own control is what pinned this wording: `agentbench-webarena-...md`
    looks like a 46-character unbreakable run but breaks at its hyphens, so `candidates()` is a
    ranking heuristic (longest-looking run), not a proof that a page can spill.
  * COLUMN BUST: each cell has `min-width: 100px`, so a table with N columns cannot be narrower
    than 100*N. At N=8 that is 800px > 768px, and with `overflow-x: visible` + `w-fit` the table
    grows past the reader's column with nothing to scroll it. The widest table this repo authors is
    6 columns (checked offline, `floor_check()`), so there is nothing to fix today — but the floor
    is a real cliff, so the check is part of the axis rather than a paragraph in a changelog.

Sampling rule, stated because it is not a random sample: the browser pass visits the pages holding
the longest looking-unbreakable cell runs (offline prefilter, `candidates()`). "The worst cases
measure clean" is the claim; "all 175 table pages measure clean" would need a run this sandbox
cannot fit in one session, and `--pages all` is there when it can.

Guards:
  * positive control, injected AFTER the real cells are read (so it cannot contaminate them): the
    page's own cell, its text replaced by a long run with no hyphen, slash or space in it, once
    with the platform's breaking left alone (must read 0 spill) and once with
    `overflow-wrap:normal` (must spill). Without the pair, "0 spills" would be indistinguishable
    from a ruler that reads nothing.
  * `<main>` must measure 768 on every page — reported as a problem when it does not, since a page
    that breaks the premise makes that page's widths mean something else. The copy is laid out at
    `COPY_VIEWPORT` (1440px) for that to mean anything: round 82 measured the same page at 593px in
    a 1280 window, because the article column is a max-width sitting beside two navigation panels
    and the panels mount on a copy too.
  * the served markup must still carry `role=cell` + the clamp() min-width; otherwise the axis is
    measuring something other than what this file documents.

Usage:
    python tools/checks/check_table_overflow.py
    python tools/checks/check_table_overflow.py --pages 12
    python tools/checks/check_table_overflow.py --pages all
"""
import argparse
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import check_widget_visibility_live as wl                      # noqa: E402
from check_live_column import live_copy, COPY_VIEWPORT           # noqa: E402  <base>-rewritten page copy
from check_mermaid_geometry import Server                        # noqa: E402  localhost + browser runner

COLUMN_LIVE = 768           # round 62's measurement of <main>; re-asserted every run
CELL_FLOOR = 100            # px: the platform's clamp() floor, read from the served style
SPILL_TOL = 8               # px: one glyph at the cell's 14px text — below this, sub-pixel noise
FENCE = re.compile(r"^\s*(```|~~~)")
ROW = re.compile(r"^\|(.+)\|\s*$")
# A run a browser cannot break on: no space, no CJK (CJK breaks between any two glyphs), and no
# hyphen or slash — measured, those two DO end a line, so they are break opportunities here too.
TOKEN = re.compile(r"[A-Za-z0-9_.:%#&?=+@]{6,}")
BREAKS = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef\s,;)/-]+")
# A run with no break opportunity anywhere: underscores, dots and digits do not let a line break.
# (The first control tried was an authored hyphenated filename, and it measured 0 spill with
# `overflow-wrap:normal` — because a browser ends a line after a hyphen. A control that cannot fail
# is not a control.)
CONTROL_TOKEN = "agent_trajectory_finetuning_pipeline_overview_architecture_v2.png"


def authored_tables():
    """{rel: [(row_no, ncols, [cells])]} for markdown tables outside code fences."""
    pages = {}
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir.startswith("14-templates") or "/." in "/" + rel_dir:
            continue                                  # template pages quote markup, per README;
        for fn in sorted(filenames):                  # .gitbook/ holds asset manifests, not pages
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            path = os.path.join(dirpath, fn)
            rows, fence, n = [], False, 0
            for line in io.open(path, encoding="utf-8").read().splitlines():
                if FENCE.match(line):
                    fence = not fence
                    continue
                if fence:
                    continue
                m = ROW.match(line.strip())
                if not m:
                    continue
                parts = [c.strip() for c in m.group(1).split("|")]
                if all(re.fullmatch(r":?-{2,}:?", p) for p in parts if p):
                    continue                          # the |---|---| separator row
                n += 1
                rows.append((n, len(parts), parts))
            if rows:
                pages[os.path.relpath(path, DOCS).replace("\\", "/")] = rows
    return pages


def unbreakable(cell):
    best = ""
    stripped = re.sub(r"<[^>]+>", "", cell)
    stripped = re.sub(r"`([^`]*)`", r"\1", stripped)
    stripped = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", stripped)
    for chunk in BREAKS.split(stripped):
        for t in TOKEN.findall(chunk):
            if len(t) > len(best):
                best = t
    return best


def floor_check(pages):
    """The 100px x N floor against the reader's column: an offline reading with real teeth."""
    widest = max((ncols for rows in pages.values() for _, ncols, _ in rows), default=0)
    cells = sum(len(c) for rows in pages.values() for _, _, c in rows)
    over = sorted({ncols for rows in pages.values() for _, ncols, _ in rows if ncols * CELL_FLOOR > COLUMN_LIVE})
    print("authored tables: pages=%d rows=%d cells=%d widest=%d columns"
          % (len(pages), sum(len(r) for r in pages.values()), cells, widest))
    print("  min-width floor: %d x %dpx = %dpx vs a %dpx column -> %s"
          % (widest, CELL_FLOOR, widest * CELL_FLOOR, COLUMN_LIVE,
             "FITS" if widest * CELL_FLOOR <= COLUMN_LIVE else "BUSTS THE COLUMN"))
    assert not over, "authored tables with %s columns cannot fit the column (100px/cell floor, " \
                     "no scroller): %s" % (over, [p for p, rows in pages.items()
                                                  for _, nc, _ in rows if nc * CELL_FLOOR > COLUMN_LIVE])
    return widest, cells


def candidates(pages, count):
    """Pages holding the longest unbreakable cell tokens — the ones most able to spill."""
    scored = []
    for rel, rows in pages.items():
        tok = max((unbreakable(c) for _, _, cs in rows for c in cs), key=len, default="")
        scored.append((len(tok), rel, tok))
    scored.sort(reverse=True)
    return [(rel, ln, tok) for ln, rel, tok in (scored if count == "all" else scored[:count])]


def live_url(rel):
    """Local page -> reader's document through the site's own index (never guess a URL)."""
    # Chapter index pages are authored as `.../README.md`, so the suffix is not always missing.
    text = io.open(os.path.join(DOCS, rel.replace("/", os.sep)
                                if rel.endswith(".md") else rel + ".md"), encoding="utf-8").read()
    m = re.search(r"^# (.+)$", text, flags=re.M)
    if not m:
        return ""
    entries = wl.llms_entries()
    index, ambiguous = wl.page_index(entries)
    assert not ambiguous, "ambiguous published titles make the join unsafe: %s" % sorted(ambiguous)
    url = index.get(wl.norm(m.group(1).strip())) or ""
    return url[:-3] if url.endswith(".md") else url      # .md is markup, not the reader's page


PROBE = """
<script>
(function () {
  var RID = @@RID@@, API = 'http://127.0.0.1:@@PORT@@', TOK = @@TOK@@;
  // The absolute API URL is not decoration: the page copy carries <base href="site/">, so a
  // relative '/report' would be posted to the live site and this axis would report nothing.
  function ink(el) {
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), r, out = null;
    while ((r = w.nextNode())) {
      if (!r.nodeValue || !r.nodeValue.trim()) continue;
      // The platform hides an "ask AI" button at `right: full` outside the cell; its text would
      // read as ink far to the left and invent a spill on every cell that has one.
      if (r.parentElement && r.parentElement.checkVisibility &&
          !r.parentElement.checkVisibility({visibilityProperty: true, opacityProperty: true})) continue;
      var rg = document.createRange(); rg.selectNodeContents(r);
      var b = rg.getBoundingClientRect();
      if (!b.width) continue;
      if (!out) out = {l: b.left, rt: b.right};
      else { out.l = Math.min(out.l, b.left); out.rt = Math.max(out.rt, b.right); }
    }
    return out;
  }
  function read(c) {
    var cr = c.getBoundingClientRect(), ik = ink(c), cs = getComputedStyle(c);
    return {cw: Math.round(cr.width), clw: c.clientWidth, sw: c.scrollWidth,
            inkW: ik ? Math.round(ik.rt - ik.l) : 0,
            spillR: ik ? Math.max(0, Math.round(ik.rt - cr.right)) : 0,
            spillL: ik ? Math.max(0, Math.round(cr.left - ik.l)) : 0,
            ow: cs.overflowWrap, wb: cs.wordBreak, ws: cs.whiteSpace,
            txt: (c.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 44)};
  }
  function measure() {
    var sel = '[role=cell],[role=gridcell],[role=columnheader]';
    var cells = [].slice.call(document.querySelectorAll(sel));
    if (cells.length < 4) return null;
    var tables = [].slice.call(document.querySelectorAll('[role=table],[role=grid],[role=treegrid]'));
    var rows = cells.map(function (c) {
      var r = read(c);
      r.t = tables.indexOf(c.closest('[role=table],[role=grid],[role=treegrid]'));
      return r;
    });
    var tin = tables.map(function (t, i) {
      var gr = t.getBoundingClientRect(), cs = getComputedStyle(t);
      var inkR = 0;
      [].forEach.call(t.querySelectorAll(sel), function (c) {
        var k = ink(c); if (k) inkR = Math.max(inkR, k.rt);
      });
      return {i: i, w: Math.round(gr.width), clw: t.clientWidth, sw: t.scrollWidth,
              ox: cs.overflowX, over: inkR ? Math.max(0, Math.round(inkR - gr.right)) : 0,
              cls: String(t.className).slice(0, 90)};
    });
    var m = document.querySelector('main');
    return {main: m ? Math.round(m.getBoundingClientRect().width) : null,
            vw: innerWidth, cells: rows.length, rows: rows, tables: tin,
            style: (cells[0] ? cells[0].getAttribute('style') || '' : '').slice(0, 120)};
  }
  function control(tables) {
    // Injected only AFTER the real reading, because adding a cell re-lays out its whole row. It
    // goes into the cell's own row, not into the table container: the container is flex-COLUMN, so
    // a bare child there would stretch to 768px and the control would "pass" without measuring.
    var t = tables[0];
    if (!t) return {skip: 'no table container to clone into'};
    var src = t.querySelector('[role=cell],[role=columnheader]');
    if (!src || !src.parentElement) return {skip: 'no cell to clone'};
    var out = {};
    ['platform', 'normal'].forEach(function (mode) {
      var c = src.cloneNode(true);
      var host = c.querySelector('p') || c;
      host.textContent = TOK;
      if (mode === 'normal') { c.style.overflowWrap = 'normal'; c.style.wordBreak = 'normal'; }
      src.parentElement.insertBefore(c, src);
      out[mode] = read(c);
      c.parentElement.removeChild(c);
    });
    return out;
  }
  function send(o) {
    o.id = RID; o.done = true;
    var x = new XMLHttpRequest(); x.open('POST', API + '/report', false); x.send(JSON.stringify(o));
    var h = new XMLHttpRequest(); h.open('GET', API + '/hold?rid=' + RID, false);
    try { h.send(); } catch (e) {}
  }
  var tries = 0;
  function poll() {
    var m = null;
    try { m = measure(); } catch (e) { send({fatal: String(e.message).slice(0, 160)}); return; }
    if (m) {
      var tables = [].slice.call(document.querySelectorAll('[role=table],[role=grid],[role=treegrid]'));
      try { m.ctl = control(tables); } catch (e) { m.ctl = {fatal: String(e.message).slice(0, 160)}; }
      send(m);
      return;
    }
    if (tries++ > 20) { send({cells: 0, rows: [], tables: []}); return; }
    setTimeout(poll, 500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', poll);
  else poll();
})();
</script>
"""


def check_control(rep, rel):
    """The ruler must be able to see a spill: the same cell, breaking on and breaking off."""
    ctl = (rep or {}).get("ctl") or {}
    assert not ctl.get("skip") and not ctl.get("fatal"), "control did not run on %s: %s" % (rel, ctl)
    plat, norm = ctl["platform"], ctl["normal"]
    assert plat["spillR"] == 0 and plat["spillL"] == 0, \
        "a %d-char token spills %spx in %s even with the platform's breaking — the CSS rule this " \
        "axis documents is no longer holding: %s" % (len(CONTROL_TOKEN), plat["spillR"], rel, plat)
    # 2px per character is a deliberately weak bar for 14px Latin text (~7px/glyph): the point is
    # that the ruler sees ink leave the box, not that it estimates a font metric.
    assert norm["spillR"] >= 2 * len(CONTROL_TOKEN), \
        "toothless ruler: with overflow-wrap:normal a %d-char unbreakable run spilled only %s px (%s)" \
        % (len(CONTROL_TOKEN), norm["spillR"], norm)
    assert norm["spillR"] > plat["spillR"], \
        "breaking off did not change the reading (%s vs %s) — the ink is not the cell's content" \
        % (norm["spillR"], plat["spillR"])
    return norm["spillR"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="8", help="how many candidate pages to load in a browser")
    ap.add_argument("--no-control", action="store_true", help="skip the injected control (faster re-runs)")
    args = ap.parse_args()
    count = "all" if args.pages == "all" else int(args.pages)

    pages = authored_tables()
    widest, cells = floor_check(pages)
    cand = candidates(pages, count)
    print("browser pass over the %d pages with the longest unbreakable tokens (widest table = %d cols)"
          % (len(cand), widest))

    dummy = os.path.join(tempfile.gettempdir(), "tableaxis-none.js")
    io.open(dummy, "w", encoding="utf-8").write("// this axis loads no engine; it reads the platform's own page\n")
    srv = Server(js_path=dummy)
    rid, problems, measured, spills, floors = 0, [], 0, [], []
    try:
        for rel, toklen, tok in cand:
            url = live_url(rel)
            if not url:
                problems.append("NOURL %s (not reachable through llms.txt)" % rel)
                continue
            html = wl.fetch(url)
            rid += 1
            name = "tbl-%d.html" % rid
            io.open(os.path.join(srv.root, name), "w", encoding="utf-8").write(
                live_copy(html, wl.SITE,
                          PROBE.replace("@@RID@@", str(rid)).replace("@@PORT@@", str(srv.port))
                             .replace("@@TOK@@", json.dumps(CONTROL_TOKEN))))
            srv.hold(rid, 120)
            proc = srv.render(name, [], height=2600, window=COPY_VIEWPORT)
            try:
                rep = srv.wait(rid, 90, proc)
            finally:
                Server.stop(proc)
            if not rep or rep.get("fatal") or rep.get("rows") is None:
                problems.append("NOHYDRATE %s (%s) — harness/CDN, not a content verdict" % (rel, rep))
                continue
            assert rep.get("cells", 0) >= 4, "vacuity: %s reported %s cells" % (rel, rep.get("cells"))
            # The column this axis judges against is a max-width sitting beside two navigation
            # panels, so it only exists at a window wide enough for it: check_live_column measured
            # 593px for the same page at a 1280 window and 768px from 1440 up. Asking for the narrow
            # one and asserting the wide number is how this axis went red on an engine swap.
            assert rep.get("vw") == COPY_VIEWPORT, \
                "asked for a vw=%d window, the copy reported %s — every column number below is then" \
                " read off a different viewport" % (COPY_VIEWPORT, rep.get("vw"))
            if rep.get("main") != COLUMN_LIVE:
                # Reported rather than asserted: one page rendering at another column is a finding
                # about that page, while aborting the run would hide every page after it.
                problems.append("COLUMN %s measured <main>=%s at vw=%d, not the %dpx under test"
                                % (rel, rep.get("main"), COPY_VIEWPORT, COLUMN_LIVE))
            assert "clamp(" in rep.get("style", ""), \
                "%s: cells no longer carry the clamp() min-width the axis documents: %r" % (rel, rep.get("style"))
            broken = [r for r in rep["rows"] if max(r["spillR"], r["spillL"]) > SPILL_TOL]
            bust = [t for t in rep["tables"] if t["w"] > COLUMN_LIVE + SPILL_TOL]
            wrap = sorted({(r["ow"], r["wb"]) for r in rep["rows"]})
            assert any(ow in ("anywhere", "break-word") or wb == "break-word" for ow, wb in wrap), \
                "%s: the platform stopped breaking long words inside cells (%s) — every long token " \
                "in the book now paints over its neighbour" % (rel, wrap)
            measured += rep["cells"]
            spills += [dict(r, page=rel) for r in broken]
            floors += bust
            ctl = "" if args.no_control else " | control spills %dpx with breaking off" % check_control(rep, rel)
            print("  %-52s main=%-4s cells=%-4d tok=%-3d tables=%-2s worst-ink=%-4d spill=%d bust=%d%s"
                  % (rel, rep.get("main"), rep["cells"], toklen, len(rep["tables"]),
                     max(r["inkW"] for r in rep["rows"]), len(broken), len(bust), ctl))
            for r in sorted(broken, key=lambda x: -max(x["spillR"], x["spillL"]))[:5]:
                print("      SPILL t%s cw=%s ink=%s R=%s L=%s %r"
                      % (r.get("t"), r["cw"], r["inkW"], r["spillR"], r["spillL"], r["txt"]))
            for t in bust:
                print("      COLUMN-BUST table %s width=%s over=%s (%s)" % (t["i"], t["w"], t["over"], t["cls"]))
    finally:
        srv.close()

    print("\n-- verdict (%dpx column, %d cells read on %d pages) --" % (COLUMN_LIVE, measured, rid))
    print("  spilling cells=%d   tables wider than the column=%d" % (len(spills), len(floors)))
    for p in problems:
        print("  -", p)
    print("problems=%d" % (len(problems) + len(spills) + len(floors)))
    return 1 if (problems or spills or floors) else 0


if __name__ == "__main__":
    sys.exit(main())
