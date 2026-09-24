"""Round 62: does GitBook's own wide layout actually give the diagrams the column they need?

Background: the live-copy A/B in check_live_column.py returned a NULL (adding `layout-wide` to the
ancestors of <main> in a downloaded copy did not widen the column). The shipped CSS explains why the
mechanism is subtle: the utilities are gated behind `body:has(.layout-wide)`, e.g.

    body:has(.layout-wide) .layout-wide\\:max-w-6xl{max-width:72rem}

This script answers the question with the platform's OWN stylesheets rather than a guess. The four
CSS files named by the live page are downloaded verbatim and served from localhost (this sandbox's
Edge has no external network), applied to the real `<main class=...>` string read from the live
page, with the book's widest authored diagram (1116px natural) inside. Nothing is hand-styled: the
only thing the probe does is add the site's own `layout-wide` class to an element in <body>, which
is what `body:has(...)` keys on.

Controls, both inside the same <main>: a 500px box and a 1100px box must read 500 and 1100, or the
ruler is clamping and every number below is meaningless. A third guard checks that the downloaded
sheets really define `.max-w-3xl{` and `layout-wide\:max-w-6xl` - an earlier revision fetched four
identical 11kB 404 pages and still printed a confident reading.

Usage:
    python tools/checks/check_wide_layout_ab.py
"""
import io
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8")
import check_mermaid_geometry as G
import check_widget_visibility_live as wl

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
PAGE = wl.SITE + "/01-ai-basics/ai-history"
WIDEST = ("12-applications/README.md", 1)          # 1116px natural - the book's widest diagram
RID = 1

html = wl.fetch(PAGE)
m = re.search(r'<main[^>]*class="([^"]+)"', html)
assert m, "no <main class=...> on the live page - the assumption under test is gone"
MAIN_CLASS = m.group(1)
print("live <main class>:", MAIN_CLASS[:160])
assert "max-w-3xl" in MAIN_CLASS and "layout-wide:max-w-6xl" in MAIN_CLASS, "markup changed"

found = re.findall(r'href="((?:https?://[^"]+)?/_next/static/css/[^"]+\.css)"', html)
seen, sheets = set(), []
for u in found:                      # document order matters: these sheets cascade
    if u not in seen:
        seen.add(u)
        sheets.append(u)
assert sheets, "no stylesheet hrefs found - cannot run this leg"
print("stylesheets named by the live page:", len(sheets))
print("live <body class>:", (re.search(r'<body[^>]*class="([^"]*)"', html) or [None, "(none)"])[1][:200])

srcs = [b["src"] for b in G.authored_blocks() if (b["page"], b["i"]) == WIDEST]
assert len(srcs) == 1, "widest diagram not found: %r" % srcs
SRC = json.dumps(srcs[0])

PROBE = """
<script>
(function(){
  var RID=__RID__, out=[];
  function w(el){return el?Math.round(el.getBoundingClientRect().width):null;}
  function post(){
    navigator.sendBeacon('/report', JSON.stringify({id:RID, done:true, snaps:out,
      ctl:{narrow:w(document.querySelector('[data-ctl=narrow]')),
           wide:w(document.querySelector('[data-ctl=wide]'))}}));
  }
  function snap(tag){
    var main=document.querySelector('main'), cell=document.getElementById('cell');
    var s=cell.querySelector('svg'), t=cell.querySelector('g.node text,.nodeLabel,text');
    var cs=(s&&t)?parseFloat(getComputedStyle(t).fontSize):null;
    var nat=(s&&s.viewBox&&s.viewBox.baseVal.width)?Math.round(s.viewBox.baseVal.width):null;
    var painted=(s?Math.round(s.getBoundingClientRect().width):null);
    // The CSS font-size is 16px in BOTH layouts; what a reader sees is that size times the
    // scale-down the SVG takes. Reporting the raw number here once made a 768px column look like
    // it still had 16px labels, so the effective size is what gets printed.
    var eff=(cs&&nat&&painted)?Math.round(cs*painted*100/nat)/100:null;
    out.push({tag:tag, main:w(main), cssMax:main?getComputedStyle(main).maxWidth:null,
              cell:w(cell), svg:painted, natural:nat,
              sw:cell?cell.scrollWidth:null, font:eff,
              svgWidthAttr:s?s.getAttribute('width'):null,
              svgStyle:s?(s.getAttribute('style')||'').slice(0,80):null});
  }
  function go(){
    snap('as-is');
    // the site's own variant marker: `body:has(.layout-wide)` keys on a descendant, so toggle that
    // and let the shipped CSS do every part of the work.
    document.querySelectorAll('[data-wide]').forEach(function(n){n.classList.add('layout-wide');});
    document.documentElement.classList.add('layout-wide');
    document.body.classList.add('layout-wide');
    void document.body.offsetWidth;
    snap('layout-wide');
    post();
  }
  mermaid.initialize({startOnLoad:false, securityLevel:'loose'});
  mermaid.render('w', __SRC__).then(function(r){
    // paint it before measuring: an earlier revision resolved the render and then measured an empty
    // .cell, which printed svg painted=None and still produced a confident-looking verdict.
    document.getElementById('cell').innerHTML = r.svg;
    go();
  }, function(e){
    out.push({err:String(e && e.message || e).slice(0,160)}); post();
  });
})();
</script>
"""

js = G.find_bundle(None)
assert js, "no mermaid bundle - this leg cannot run"
print("bundle:", js, "version", G.bundle_version(io.open(js, encoding="utf-8", errors="replace").read()))
srv = G.Server(js)
wide_rules = narrow_rules = 0
try:
    for href in sheets:
        url = href if href.startswith("http") else wl.SITE + href
        css = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
        name = os.path.basename(href)
        io.open(os.path.join(srv.root, name), "wb").write(css)
        text = css.decode("utf-8", "replace")
        assert "tailwindcss" in text[:200] or text.lstrip().startswith("@") or "{" in text[:200], \
            "%s is not a stylesheet (%r) - the fetch went wrong, not the site" % (name, text[:60])
        wide_rules += text.count("layout-wide\\:max-w-6xl")
        narrow_rules += text.count(".max-w-3xl{")
        print("  saved %-26s %7d B  layout-wide:*=%d  layout-wide:max-w-6xl=%d  .max-w-3xl{=%d"
              % (name, len(css), text.count("layout-wide"), text.count("layout-wide\\:max-w-6xl"),
                 text.count(".max-w-3xl{")))
    assert narrow_rules and wide_rules, (
        "vacuity: none of the %d downloaded sheets defines the utilities under test "
        "(.max-w-3xl{=%d, layout-wide:max-w-6xl=%d). Without them the fixture would still read "
        "500/1100 on the controls and a full-width <main>, i.e. a clean-looking no-op."
        % (len(sheets), narrow_rules, wide_rules))
    links = "".join('<link rel="stylesheet" href="/%s">' % os.path.basename(h) for h in sheets)
    probe = PROBE.replace("__RID__", str(RID)).replace("__SRC__", SRC)
    fixture = ("<!doctype html><html><head><meta charset='utf-8'>" + links +
               "<style>body{margin:0}</style></head><body>"
               '<div id="app"><main class="@@MAIN@@">'
               "<div data-ctl='narrow' style='width:500px'>ctl</div>"
               "<div data-ctl='wide' style='width:1100px'>ctl</div>"
               "<div id='cell' class='cell' style='overflow-x:auto'></div>"
               "<div data-wide class='anchor'></div>"
               "</main></div>"
               "<script src='/mermaid.min.js'></script>" + probe +
               "<script src='/hold?rid=@@RID@@'></script></body></html>")
    # @@TOKENS@@, not %-formatting: an earlier revision ran the whole document through `% (...)` and
    # Mermaid's `%%{init}%%` directive came back as `%{init}%`, so the render failed on the markup of
    # the probe rather than on the site.
    fixture = fixture.replace("@@MAIN@@", MAIN_CLASS).replace("@@RID@@", str(RID))
    io.open(os.path.join(srv.root, "wide.html"), "w", encoding="utf-8").write(fixture)
    srv.hold(RID, 120)
    proc = srv.render("wide.html", ["--dump-dom"])
    try:
        rep = srv.wait(RID, 150, proc)
    finally:
        G.Server.stop(proc)
finally:
    srv.close()

print("\ncontrols (must read 500 / 1100):", (rep or {}).get("ctl"))
snaps = (rep or {}).get("snaps") or []
if not snaps:
    print("NO REPORT - the harness produced nothing, which is not a verdict")
    sys.exit(2)
for s in snaps:
    if s.get("err"):
        print("  render failed:", s["err"])
        sys.exit(2)
    print("  %-12s main=%-6s (computed max-width %s) cell=%-6s svg painted=%-6s natural=%-6s "
          "scrollW=%-6s label font=%s" %
          (s["tag"], s["main"], s["cssMax"], s["cell"], s["svg"], s["natural"], s["sw"], s["font"]))
    print("      svg width attr=%r style=%r" % (s["svgWidthAttr"], s["svgStyle"]))

ctl = (rep or {}).get("ctl") or {}
assert ctl.get("narrow") == 500, "ruler is blind: 500px box read %s" % ctl
assert ctl.get("wide") == 1100, "ruler clamps: 1100px box read %s" % ctl
a = snaps[0]
b = snaps[-1]
# The CSS-applied control: `.max-w-3xl` from the platform's own sheet must bind here, or the whole
# fixture is running styleless and a "wide layout did nothing" reading would be meaningless.
assert a["main"] and 700 <= a["main"] <= 768, (
    "as-is <main> read %spx, not the 768px the live site reports -> the downloaded CSS never "
    "applied in this fixture, so this run can say nothing about the wide layout" % a["main"])
print("  css-applied control: as-is main = %spx (max-width %s) matches the live default column" %
      (a["main"], a["cssMax"]))
print("\n-- verdict --")
print("  as-is column=%s -> wide-layout column=%s (delta %s)" % (a["main"], b["main"],
                                                                 (b["main"] or 0) - (a["main"] or 0)))
if b["main"] == a["main"]:
    print("  NULL: the platform's own CSS did not widen the column even with layout-wide present.")
elif b["cell"] and a["natural"] and b["cell"] >= a["natural"]:
    print("  the %dpx diagram fits at %dpx -> B does zero the scaled-diagram count"
          % (a["natural"], b["cell"]))
else:
    print("  partial: diagram natural %s vs wide cell %s -> still scaled to %s"
          % (a["natural"], b["cell"], round((b["svg"] or 0) / (a["natural"] or 1), 2)))
