"""Render every authored Mermaid with the engine the site actually loads, and measure each one.

Why this file exists (round 58): docs/README.md has claimed, in every round since 21, that
"全书 217 张 Mermaid 图经真解析器逐块校验…最宽 1116px…与线上同版本". None of that was reproducible
from the repo — the sweep was an ad-hoc script living in a chat transcript, so the standing claim
could not be re-checked by anyone, including me. Same defect class as the formula judge that round
57 landed. This file makes the claim re-measurable in one command.

What it measures, in the order the pitfalls were learned:

  alignment  the local bundle's own reported version must equal the version the published page
             loads (read from its `<script>`). Round 15 lost a whole round to this: local
             mermaid 12.0.0 and live 11.14.0 disagree on how unconnected subgraphs lay out, so
             "0 超宽" measured on the wrong engine was local self-deception. Now the ruler refuses
             to report numbers until the engines match.
  parse      a block that will not render is a hard failure — stronger than a parser call, because
             it is the same pipeline the reader's browser runs.
  width      viewBox width vs the reader's content column, plus what the browser ends up painting.
             Mermaid ships every diagram with `useMaxWidth: true` — the SVG carries
             `width="100%"` and `style="max-width: <natural>px"` — so a diagram wider than the
             column is SCALED DOWN to fit it and its labels shrink with it (1108px authored in the
             live 768px column paints 16px text at 11.1px), while a narrower one is untouched. The
             wrapper's `overflow-x-auto` never gets a scrollable child, so nothing scrolls to save
             the reader: over-wide means illegible, and `--font-floor` is what judges that.
  height     reported, not judged: a tall diagram only costs scrolling (max measured 1689px),
             while a wide one costs legibility.

What the default run then prints about the OTHER two reader faces (report-only, one derivation each
— see laptop_reading): the 608px laptop column (round 73) and the 342px box a phone reader is given
(round 107, measured live at vw=390: `<main>` 358, and GitBook's mermaid wrapper keeps 342 of it for
the svg). Judging against 768 is the book's certified bar because README quotes that column; the two
narrower readings exist so a future round cannot mistake "clean at 768" for "readable on a phone".

Two planted counterexamples ride along on every run (one unparsable source, one fan-out that must
blow past the column) and MUST be caught. Without them "0 超宽、0 失败" would also be what a silent
no-op prints — see the project's no-silent-zero rule. Those two ride *through* the browser, so they
cannot catch a browser that renders nothing (round 81: six axes went blind in one run that way);
the preflight's own controls are `--engine-selftest`.

Rendering is local and offline on purpose: the headless engine in this sandbox has no external
network, so the engine is served from 127.0.0.1 together with the fixture, and each batch beacons
its measurements back over HTTP (see fixture_html for why --dump-dom was dropped). Which engine is
used is decided by `browser()`, not by a remembered path.

Usage:
    python tools/checks/check_mermaid_geometry.py --mermaid-js <dir-with-node_modules>
    python tools/checks/check_mermaid_geometry.py --eyeball 04-prompt-reasoning/react.md
        -> writes a PNG of that page's diagrams for a real rendered look
    python tools/checks/check_mermaid_geometry.py --selftest
        -> runs this axis's planted control arms (ink guard + accepted-debt ledger) and exits
    python tools/checks/check_mermaid_geometry.py --engine-selftest
        -> proves the engine preflight refuses a browser that hands back no DOM
"""
import argparse
import functools
import glob
import http.server
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(HERE, "..", "..", "docs"))
SITE = "https://violetnotes.gitbook.io/violetnotes-docs"
# The column a reader actually gets. 1120 was believed from round 24 to round 61 and is the WIDE
# layout's number; `tools/checks/check_live_column.py` measured the live default at 768px
# (`<main class="max-w-3xl layout-wide:max-w-6xl">`, and `layout-wide` is off by default). Judging
# against 1120 certified 102 scaled-down diagrams as clean.
COLUMN = 768
# Round 73: the same `<main>` on the LIVE page at a 1280px window, once the 288px chapter sidebar and
# the 256px page TOC mount beside the article. 768 is a >=1440 reader's column. Re-measured every run
# by `check_svg_legibility.py`'s laptop leg (Playwright on the live URL); this axis keeps the number
# rather than importing it, because importing would make the two files a cycle.
COLUMN_LAPTOP = 608
# Round 107: the phone reader's own box, measured live at vw=390 — `<main>` comes back 358 wide and
# the diagram sits inside GitBook's mermaid wrapper, whose own padding leaves the svg 342. Not the
# column minus a guess: 358 was the column and 342 is what the diagram is actually given.
# Round 108: `check_live_column.py`'s phone diagram leg re-reads this box on the live page every run
# and reddens PHONE-DIAG-BOX if the platform stops giving the diagram 342 of the 358.
COLUMN_PHONE = 342
LABEL_BAR = 12.0                    # px; the bar check_svg_legibility.py certifies SVG labels at
# Round 62: what GitBook's `layout-wide` actually leaves a diagram — 1152px `<main>` minus the ~61px
# inset the default column measured at. The homepage quotes it, so the wide-layout reading below is
# judged against this number and not against 1152.
WIDE_COLUMN = 1091
HOMEPAGE = os.path.join(DOCS, "README.md")
HOME_MARK = "Mermaid 图经真解析器逐块校验"   # identifies the homepage bullet this axis owns
WINDOW = 1280                       # fixture viewport: the cell has to fit inside it
SHOT_BUDGET = 20000                # virtual ms the --eyeball screenshot is allowed to paint in
EDGE_CANDIDATES = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
# Round 82: this machine's Edge stopped answering --dump-dom (rc=0, stdout 0 bytes, across six flag
# variants), and six render axes went blind in the same run. The lesson is not "use another path" —
# it is that a launcher must *prove* its engine renders before any threshold is read from it. So
# the engine is now chosen by a sentinel probe, and Playwright's CLI-mode Chromium
# (chrome-headless-shell) is a candidate: it answers --dump-dom / --screenshot /
# --virtual-time-budget, which is the whole flag surface these axes use.
SHELL_GLOBS = [os.path.join(root, "chromium_headless_shell-*", "*", "chrome-headless-shell.exe")
               for root in [os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
                            os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright")]
               if root]
SENTINEL = "@@ENGINE@@"


def engine_candidates():
    """An explicit override is the engine under test, alone; otherwise Edge, then shells (newest first).

    Exclusive on purpose. A reader who pins `HANDBOOK_BROWSER` to measure one build must not get a
    silently different one, and the launcher's own blind-engine control (see `engine_selftest`)
    depends on the pinned path being the only thing tried.
    """
    if os.environ.get("HANDBOOK_BROWSER"):
        return [os.environ["HANDBOOK_BROWSER"]]
    out = [p for p in EDGE_CANDIDATES if os.path.isfile(p)]
    for pattern in SHELL_GLOBS:
        if "*" in pattern:
            out += sorted(glob.glob(pattern), reverse=True)
    seen, uniq = set(), []
    for path in out:
        if path and os.path.isfile(path) and path not in seen:
            seen.add(path)
            uniq.append(path)
    return uniq


def headless_flags(exe):
    """The shell is headless by construction; a full Chrome/Edge binary needs the switch."""
    return [] if "headless-shell" in os.path.basename(exe).lower() else ["--headless=new"]


def engine_alive(exe, timeout=90):
    """True only if this binary hands back a rendered DOM containing the sentinel."""
    with tempfile.TemporaryDirectory(prefix="engine", ignore_cleanup_errors=True) as tmp:
        page = os.path.join(tmp, "probe.html")
        open(page, "w", encoding="utf-8").write(
            "<!doctype html><meta charset='utf-8'><body><pre>%s</pre></body>" % SENTINEL)
        cmd = [exe] + headless_flags(exe) + [
            "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--user-data-dir=" + os.path.join(tmp, "p"), "--window-size=900,600", "--dump-dom",
            "file:///" + page.replace("\\", "/")]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  timeout=timeout)
        except (subprocess.TimeoutExpired, OSError):
            # OSError is a real branch: `HANDBOOK_BROWSER` is a path the operator points at, and a
            # path that is not an executable must be *skipped* like a blind engine, not crash the run.
            return False
        return SENTINEL in proc.stdout.decode("utf-8", "replace")


_RESOLVED = []


def browser():
    """The first engine that proves it renders, cached for the run. No engine is a loud exit."""
    if _RESOLVED:
        return _RESOLVED[0]
    tried = []
    for exe in engine_candidates():
        if engine_alive(exe):
            _RESOLVED.append(exe)
            # Recorded on stderr so every axis says which engine produced its numbers: an engine
            # switch moves thresholds, and a reading with no engine attached cannot be re-anchored.
            sys.stderr.write("# engine: %s\n" % exe)
            return exe
        tried.append(os.path.basename(exe))
    raise SystemExit(
        "no headless browser answers --dump-dom (tried: %s). Set HANDBOOK_BROWSER to a working "
        "engine: a blind renderer must exit, not report 0 problems."
        % (", ".join(tried) if tried else "nothing installed"))


ENGINE_SELFTEST = """
import os, sys
sys.path.insert(0, %r)
os.environ['HANDBOOK_BROWSER'] = sys.argv[1]
import check_mermaid_geometry as m
print('ACCEPTED', m.browser())
"""


def engine_selftest():
    """The launcher's own controls, because every other plant here rides the engine it is checking.

    Round 81 lost six render axes at once to an engine that exited 0 and handed back no DOM, and not
    one plant caught it: the planted counterexamples all *measure through* that engine, so a blind
    one makes them measure nothing. These legs pin the preflight itself: the engine that answers is
    accepted, and the two shapes a browser goes blind in (exit 0 with an empty stdout -- this
    machine's Edge -- and a path that is not an executable at all) must end the run, not print zeros.
    """
    real = browser()                       # resolved here; the three legs run in fresh processes
    blind = os.path.join(tempfile.gettempdir(), "handbook-blind-engine.cmd")
    open(blind, "w", encoding="ascii").write(
        "@echo off\r\nrem exits 0 and prints no DOM: the shape a dead headless browser makes\r\n"
        "exit /b 0\r\n")
    fake = os.path.join(tempfile.gettempdir(), "handbook-not-an-executable.py")
    open(fake, "w", encoding="ascii").write("print('not an executable')\n")
    for path, why in ((blind, "an engine that exits 0 with an empty stdout"),
                      (fake, "a path that is not an executable at all")):
        proc = subprocess.run([sys.executable, "-c", ENGINE_SELFTEST % HERE, path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        err = proc.stderr.decode("utf-8", "replace")
        assert proc.returncode != 0 and "no headless browser" in err, \
            "%s was accepted by the preflight (rc=%s, stdout=%r, stderr=%r): a blind engine would " \
            "print 0 problems" % (why, proc.returncode, proc.stdout[-120:], err[-200:])
    pinned = subprocess.run([sys.executable, "-c", ENGINE_SELFTEST % HERE, real],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    assert pinned.returncode == 0 and \
        os.path.basename(real) in pinned.stdout.decode("utf-8", "replace"), \
        "the working engine was refused by its own preflight (rc=%s, stderr=%r)" % (
            pinned.returncode, pinned.stderr.decode("utf-8", "replace")[-200:])
    print("engine preflight controls ok: the working engine is accepted; empty-DOM and "
          "not-an-executable are both refused with an exit, never a 0-problems reading")
    return 0


CONTROL_WIDE = ("flowchart LR\n"
                "  A1[分支一 的很长很长标签文字] --> A2[分支二 的很长很长标签文字] --> "
                "A3[分支三 的很长很长标签文字] --> A4[分支四 的很长很长标签文字] --> "
                "A5[分支五 的很长很长标签文字] --> A6[分支六 的很长很长标签文字] --> "
                "A7[分支七 的很长很长标签文字] --> A8[分支八 的很长很长标签文字]\n")
CONTROL_BROKEN = "graph TD\n  A[起点] -->\n"


def mermaid_blocks(text):
    """[src] for each ```mermaid fence, found with the same fence state machine the suite uses.

    A fence that merely *mentions* mermaid in prose (`​```markdown` examples in docs/README.md) is
    not a diagram, and a diagram inside a ```text fence is not one either — hence the info-string
    test on the opening token, not a DOTALL regex over the page.
    """
    out, open_tok, cur = [], None, None
    for line in text.split("\n"):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})(\w*)", line)
        if m:
            tok = m.group(1)[0] * 3
            if open_tok is None:
                open_tok, cur = tok, ([] if m.group(2) == "mermaid" else None)
            else:
                if tok == open_tok:
                    if cur is not None:
                        out.append("\n".join(cur))
                    open_tok, cur = None, None
                else:
                    if cur is not None:
                        cur.append(line)
                continue
            continue
        if cur is not None:
            cur.append(line)
    return out


def authored_blocks():
    rows = []
    for dirpath, dirs, filenames in os.walk(DOCS):
        if "14-templates" in dirpath.replace("\\", "/"):
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            for i, src in enumerate(mermaid_blocks(open(path, encoding="utf-8").read()), 1):
                rows.append({"page": rel, "i": i, "src": src})
    return rows


def find_bundle(arg):
    """Path to mermaid's self-contained bundle, or None. Never report a PASS without one."""
    if arg and os.path.isfile(arg):
        return arg
    roots = [arg, os.getcwd(), tempfile.gettempdir()] if arg else [os.getcwd(), tempfile.gettempdir()]
    for root in [r for r in roots if r]:
        for cand in (os.path.join(root, "mermaid.min.js"),
                     os.path.join(root, "node_modules", "mermaid", "dist", "mermaid.min.js"),
                     os.path.join(root, "mm58", "node_modules", "mermaid", "dist", "mermaid.min.js")):
            if os.path.isfile(cand):
                return cand
    return None


def bundle_version(js):
    m = re.search(r'version:"(\d+\.\d+\.\d+)"', js)
    return m.group(1) if m else ""


def live_version():
    """The mermaid version the published site loads, read from its own markup."""
    sys.path.insert(0, HERE)
    import check_widget_visibility_live as wl
    html = wl.fetch(SITE + "/03-llm-ji-chu/transformer-attention")
    hits = re.findall(r"mermaid@(\d+\.\d+\.\d+)", html)
    return hits[0] if hits else ""


def fixture_html(srcs, rid, budget, mode="dump", column=COLUMN):
    """One page: the engine loaded from localhost, then every diagram rendered in order.

    Results come back over an HTTP beacon to /report instead of through --dump-dom, and the two
    mechanisms that were tried first both failed measurably: a 40-block fixture under
    --virtual-time-budget dumped 3.2 MB of source with a couple of <svg> in it and no completion
    marker (Chrome fast-forwards virtual time through pending timers, so the per-diagram watchdog
    was part of the cost), and the same fixture with no budget and no latch produced no report at
    all. Either way the failure mode was loud — 0 of 40 reported, not 40 silent zero-widths — which
    is the property this design keeps: an unfinished sweep raises, it never reports a clean site.

    `mode` is 'dump' (geometry sweep) or 'shot' (--eyeball PNG). Only dump mode installs the
    per-diagram watchdog and the latch below: shot mode waits on --virtual-time-budget so the
    screenshot fires after painting, and a pending 20 s timer would fast-forward that budget.
    """
    fail = ("d.setAttribute('data-fail',rec.fail)" if mode == "dump" else "d.textContent=rec.fail")
    run = ("(i)=>Promise.race([mermaid.render('m'+i,items[i]),hang()])" if mode == "dump"
           else "(i)=>mermaid.render('m'+i,items[i])")
    # In shot mode `limit` is a virtual-time deadline and the screenshot fires at SHOT_BUDGET, so
    # the safety beacon has to go out before that — a beacon flushed by process exit is not a beacon.
    limit = SHOT_BUDGET * 3 // 4 if mode == "shot" else budget
    # Headless Chrome exits once the document has loaded, and an async render loop does not count
    # as loading. So the page pulls one last script that the server refuses to answer until the
    # report lands: load stays pending, real time runs, the diagrams render. Without the latch a
    # 40-block batch produced no report at all.
    hold = "<script src='/hold?rid=%%HOLDRID%%'></script>" if mode == "dump" else ""
    return ("<!doctype html><meta charset='utf-8'>"
            "<style>body{margin:0;background:#fff}.cell{width:%%COLUMN%%px;overflow-x:auto}</style>"
            "<script src='/mermaid.min.js'></script><div id='out'></div><script>"
            "const items=%%ITEMS%%;const rid=%%RID%%;const limit=%%BUDGET%%;"
            "let done=false;const cells=[];"
            "mermaid.initialize({startOnLoad:false,securityLevel:'loose'});"
            "const post=()=>{navigator.sendBeacon('/report',JSON.stringify({id:rid,done:done,cells:cells}));};"
            "const hang=()=>new Promise((_,rej)=>setTimeout(()=>rej(Error('HANG>'+limit+'ms')),limit));"
            "const run=%%RUN%%;"
            "(async()=>{const o=document.getElementById('out');"
            "for(let i=0;i<items.length;i++){const d=document.createElement('div');d.className='cell';"
            "o.appendChild(d);const rec={i:i,w:null,h:null,fail:null,rw:null,sw:null,fs:null,wa:null,st:null};cells.push(rec);"
            "try{const r=await run(i);d.innerHTML=r.svg;"
            "const m=r.svg.match(/viewBox=.([-\\d.]+) ([-\\d.]+) ([-\\d.]+) ([-\\d.]+)./);"
            "if(m){rec.w=parseFloat(m[3]);rec.h=parseFloat(m[4]);"
            "const s=d.querySelector('svg'),t=d.querySelector('g.node text,.nodeLabel,text');"
            "rec.wa=s.getAttribute('width');rec.st=(s.getAttribute('style')||'').slice(0,70);"
            "rec.rw=Math.round(s.getBoundingClientRect().width);rec.sw=d.scrollWidth;"
            "if(t){const f=parseFloat(getComputedStyle(t).fontSize);"
            "if(f){rec.fs=Math.round(f*rec.rw/rec.w*100)/100;}}}"
            "else{rec.fail='rendered with no viewBox';%%FAIL%%}}"
            "catch(e){rec.fail=String(e.message).slice(0,140);%%FAIL2%%}}"
            "done=true;post();"
            "setTimeout(()=>{try{window.close();}catch(e){}},80);})();"
            "setTimeout(()=>{if(!done)post();},limit);"
            "</script>" + hold).replace("%%COLUMN%%", str(column)) \
                        .replace("%%ITEMS%%", json.dumps(srcs)) \
                        .replace("%%RID%%", str(rid)) \
                        .replace("%%HOLDRID%%", str(rid)) \
                        .replace("%%BUDGET%%", str(limit)) \
                        .replace("%%RUN%%", run) \
                        .replace("%%FAIL%%", fail) \
                        .replace("%%FAIL2%%", fail)


class Server:
    """localhost, because the fixture must load as a document, not as file:// (Edge blocks it).

    Doubles as the results mailbox: the page beacons its per-diagram measurements back here, which
    is what lets the sweep finish in real time instead of guessing when to dump the DOM.
    """

    class _Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _reply(self):
            self.send_response(204)
            self.end_headers()

        def do_GET(self):
            m = re.match(r"/hold\?rid=(\d+)", self.path)
            if m:
                held = getattr(self.server, "holds", {}).get(int(m.group(1)))
                if held:
                    held.wait(self.server.hold_seconds)
                self._reply()
                return
            super().do_GET()

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            try:
                report = json.loads(body.decode("utf-8"))
                self.server.reports.append(report)
                held = getattr(self.server, "holds", {}).get(report.get("id"))
                if held:
                    held.set()   # partial or not: the watchdog report means "stop waiting"
            except Exception as exc:
                self.server.bad.append(str(exc))
            self._reply()

    def __init__(self, js_path):
        self.root = tempfile.mkdtemp(prefix="mmd58-")
        # Anything the handler touches has to live on the HTTPServer, not on this wrapper: the
        # request threads see `self.server` only. Measured the hard way — a latch that was missing
        # there raised AttributeError inside do_GET, and the sweep read that as "0 of 40 rendered".
        self.reports = []
        self.bad = []
        self.holds = {}
        self.hold_seconds = 30
        # The bundle is served as its own file. Inlining 3.2 MB per fixture works for one diagram
        # and costs ~17 MB of re-parsed script across a full sweep for no benefit.
        shutil.copyfile(js_path, os.path.join(self.root, "mermaid.min.js"))
        # directory= is required: the handler resolves its root from the *request thread's* cwd, so
        # a chdir here would serve the repo and answer 404 for fixture.html.
        self.srv = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(self._Quiet, directory=self.root))
        self.srv.reports = self.reports
        self.srv.bad = self.bad
        self.srv.holds = self.holds
        self.srv.hold_seconds = self.hold_seconds
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.n = 0

    def new_profile(self):
        """A fresh profile per Edge run: Chromium refuses a user-data-dir another instance holds."""
        self.n += 1
        path = os.path.join(self.root, "profile%d" % self.n)
        os.makedirs(path, exist_ok=True)
        return path

    def url(self, name):
        return "http://127.0.0.1:%d/%s" % (self.port, name)

    def hold(self, rid, seconds):
        """Arm the load-blocking latch for one fixture; the report for that rid releases it."""
        self.srv.hold_seconds = seconds
        self.holds[rid] = threading.Event()

    def wait(self, rid, seconds, proc=None):
        """The completed report for this fixture, or the last partial one once `seconds` expire."""
        deadline = time.time() + seconds
        best = None
        while time.time() < deadline:
            for p in self.reports:
                if p.get("id") == rid and (best is None or (p.get("done") and not best.get("done"))):
                    best = p
            if best and best.get("done"):
                return best
            if proc is not None and proc.poll() is not None:
                return best      # the browser is gone; nothing further will be beaconed
            time.sleep(0.15)
        return best

    def render(self, name, extra=(), height=1400, window=None):
        """One headless browser run owned by this process — terminate() only ever touches our own PID.

        `window` is here because a caller that lays out a *copy of a reader's page* has to own the
        viewport: the site's article column is a CSS max-width next to two navigation panels, so the
        number such a leg asserts on only exists at one window width (see check_live_column's
        `COPY_VIEWPORT`). Chromium is not reliable about a later `--window-size`, so this is the only
        place the flag goes.
        """
        exe = browser()
        cmd = [exe] + headless_flags(exe) + [
            "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--user-data-dir=" + self.new_profile(),
            "--window-size=%d,%d" % (window or max(WINDOW, COLUMN), height)]
        return subprocess.Popen(cmd + list(extra) + [self.url(name)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def stop(proc, grace=20):
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(grace)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(grace)

    def close(self):
        self.srv.shutdown()


def render_batch(srv, blocks, budget, rid, shot=None, column=COLUMN):
    """One Edge pass over a batch of blocks; returns the per-diagram cells in authoring order."""
    name = "fixture%d.html" % rid
    if not shot:
        srv.hold(rid, budget / 1000 + 30)
    open(os.path.join(srv.root, name), "w", encoding="utf-8").write(
        fixture_html([b["src"] for b in blocks], rid, budget, "shot" if shot else "dump", column))
    if shot:
        # A screenshot fires when Chrome's *virtual* time runs out, so this mode waits for Edge to
        # exit by itself; the sweep mode is held open by the latch and stops when the report lands.
        proc = srv.render(name, ["--virtual-time-budget=%d" % SHOT_BUDGET, "--screenshot=" + shot],
                        min(900 * len(blocks), 9000))
        try:
            proc.wait(SHOT_BUDGET / 1000 + 120)
        except subprocess.TimeoutExpired:
            pass
    else:
        proc = srv.render(name, ["--dump-dom"])
    try:
        report = srv.wait(rid, 20 if shot else budget / 1000 + 25, None if shot else proc)
    finally:
        Server.stop(proc)
        srv.holds.pop(rid, None)
    cells = (report or {}).get("cells") or []
    if len(cells) != len(blocks):
        raise SystemExit(
            "only %d/%d diagrams reported for fixture%d (%s). The ruler timed out, it did not "
            "measure 0-widths — raise --budget (real ms) or lower --batch."
            % (len(cells), len(blocks), rid, "no report at all" if not report
               else "last failure: %s" % str(cells[-1].get("fail"))[:80]))
    return cells


def render(srv, blocks, budget, batch, column=COLUMN):
    cells = []
    for start in range(0, len(blocks), batch):
        cells += render_batch(srv, blocks[start:start + batch], budget,
                              start // batch + 1, column=column)
    return cells


# Round 113 (2026-09-29), operator ruling: 「保持现状，只留账」 for the diagrams still wider than the
# reader's 768px column. Accepted debt is loud but never gates — the same division `check_link_graph`
# makes between BLOCKED (a debt) and DEAD (the book's disease). Two things keep this from becoming a
# mute switch: the ruling names diagrams by identity, so a NEW over-wide one reddens the run even if
# the total count drops, and the homepage sentence still has to print this run's over-wide tally
# (`homepage_numbers` counts it from the measurement, not from `problems`).
ACCEPTED_OVERWIDE = frozenset("""
01-ai-basics/README.md#1
02-agent-basics/core-components.md#1
03-llm/README.md#1
03-llm/multimodal.md#1
03-llm/token-embedding-context.md#1
04-prompt-reasoning/react.md#1
05-tool-protocol/function-calling.md#1
05-tool-protocol/mcp.md#1
07-planning/error-recovery-retry.md#1
09-frameworks/README.md#1
09-frameworks/autogen.md#1
09-frameworks/mcp-servers.md#1
09-frameworks/openai-agents-sdk.md#1
10-evaluation-safety/alignment-safety.md#2
10-evaluation-safety/evaluation-metrics.md#1
10-evaluation-safety/explainability.md#1
10-evaluation-safety/prompt-injection.md#1
10-evaluation-safety/safety-incidents-2026.md#1
10-evaluation-safety/safety-incidents-2026.md#2
11-engineering/agent-failure-playbook.md#1
11-engineering/caching-cost-optimization.md#2
11-engineering/deployment-scaling.md#1
11-engineering/error-handling-retry-fallback.md#1
11-engineering/logging-tracing-monitoring.md#1
11-engineering/observability-tools.md#2
11-engineering/tool-registry.md#2
11-engineering/workflow-orchestration.md#1
12-applications/research-agent.md#1
12-applications/voice-agent.md#2
13-resources/benchmarks/gaia.md#1
13-resources/papers/react.md#1
13-resources/projects/README.md#1
13-resources/projects/autogen.md#1
13-resources/projects/deepseek-harness.md#1
13-resources/projects/pi.md#1
16-ai-infrastructure/inference-economics-deployment.md#1
16-ai-infrastructure/llm-observability-eval-platform.md#1
16-ai-infrastructure/model-gateway.md#1
16-ai-infrastructure/model-gateway.md#2
17-embodied-ai/data-engine.md#1
17-embodied-ai/simulation-sim2real.md#2
17-embodied-ai/vla-models.md#2
18-frontier-2026/claude-agent-sdk.md#1
18-frontier-2026/computer-use-2026.md#1
18-frontier-2026/openai-agents-api.md#2
18-frontier-2026/protocol-stack-2026.md#1
18-frontier-2026/system-one-decision-models.md#1
19-labs/lab4-multi-agent.md#1
19-labs/lab5-eval-trace.md#1
""".split())

RULING = "operator ruling 2026-09-29（第 113 轮）：保持现状，只留账"


def debt_readings(accepted, laid, column=COLUMN):
    """The accepted-debt ledger against this run: what it still owes, and what it already paid.

    An entry that stopped being over-wide is reported, not gated — the ledger has to be pruned by a
    human who decides the diagram is really fixed, and a fixed diagram must never cost a round its
    green light.
    """
    if column != COLUMN:
        return [], []
    over = {"%s#%d" % (x["row"]["page"], x["row"]["i"]) for x in laid if x["w"] > column}
    paid = sorted(ACCEPTED_OVERWIDE - over)
    return accepted, paid


def debt_controls():
    """Both directions of the accepted-debt split must be able to speak, offline and every run.

    A one-sided control would only ever prove the list mutes: so the same planted width must be
    accepted under a listed identity and must gate under an identity the ruling never named, and a
    listed diagram measured under the bar must produce neither.
    """
    def cell(w):
        return {"w": w, "h": 40, "rw": min(w, COLUMN), "sw": w, "fs": 16.0}

    listed = sorted(ACCEPTED_OVERWIDE)[0] if ACCEPTED_OVERWIDE else None
    if listed is None:
        # An empty ledger is not the same reading as a paid-off one: it also silences this axis's
        # whole over-wide branch, so it has to say so instead of crashing or reporting 0 problems.
        return (["the debt ledger is empty — either every entry was really fixed (then delete the "
                 "ruling too) or the gate was cleared to force green"], 0)
    page, _, idx = listed.rpartition("#")
    rows = [{"page": page, "i": int(idx), "src": ""},
            {"page": "never/ruled.md", "i": 1, "src": ""},
            {"page": page, "i": int(idx), "src": ""}]
    cells = [cell(COLUMN + 100), cell(COLUMN + 100), cell(COLUMN - 100)]
    problems, _, _, _, _, accepted = judge(rows, cells, COLUMN, 0.0)
    bad = []
    checks = 0

    def expect(ok, line):
        nonlocal checks
        checks += 1
        if not ok:
            bad.append(line)

    expect([a[0] for a in accepted] == [listed],
           "accepted leg is dead: a listed over-wide diagram was not filed as debt (%r)" % accepted)
    expect(any(p.startswith("OVERWIDE never/ruled.md#1") for p in problems),
           "debt list is a mute switch: an over-wide diagram the ruling never named did not gate (%r)"
           % problems)
    expect(not [p for p in problems if p.startswith("OVERWIDE") and "never/ruled" not in p],
           "a listed diagram over-wide was also gated (%r)" % problems)
    problems2, _, _, _, _, accepted2 = judge(rows[:1], cells[2:], COLUMN, 0.0)
    expect(not problems2 and not accepted2,
           "a listed diagram under the bar must say nothing (%r %r)" % (problems2, accepted2))
    _, paid = debt_readings([], [{"row": rows[0], "w": COLUMN - 100}], COLUMN)
    expect(listed in paid, "ACCEPTED-FIXED is dead: a listed diagram measured under the bar was not named")
    expect(all(re.match(r"^[\w./-]+#\d+$", i) for i in ACCEPTED_OVERWIDE),
           "the debt ledger holds a malformed identity")
    return bad, checks


def judge(rows, cells, column=COLUMN, floor=0.0):
    """FAILED / OVERWIDE / ILLEGIBLE for real pages, plus the two planted controls that must be caught.

    Width alone is a proxy. What a reader actually loses when a diagram is wider than the column is
    label size, so `floor` judges the font size the browser ends up painting (`fs`, measured, not
    computed from the assumed column). With floor=0 the judgement stays width-only, which is what
    the historic 1120px runs did.

    An over-wide diagram named by `ACCEPTED_OVERWIDE` lands in `accepted` instead of `problems`:
    loud, printed every run, never gating. Everything else about this function is unchanged.
    """
    problems, widths, heights, controls, laid, accepted = [], [], [], [], [], []
    for row, c in zip(rows, cells):
        w, h = c["w"], c["h"]
        if row["page"] == "CONTROL":
            kind = "OK"
            if w is None:
                kind = "FAILED" if row["i"] == 2 else "MISS"
            elif w > column:
                kind = "OVERWIDE" if row["i"] == 1 else "MISS"
            controls.append("wide->%s(%s)" % (kind, "w=%s" % w if w else h or ""))
            if row["i"] == 1 and (w is None or w <= column):
                problems.append("CONTROL-DEAD: the planted over-wide diagram did not exceed %dpx" % column)
            if row["i"] == 2 and w is not None:
                problems.append("CONTROL-DEAD: the planted unparsable diagram rendered anyway")
            continue
        if w is None:
            problems.append("FAILED %s#%d: %s" % (row["page"], row["i"], str(c["fail"])[:110]))
            continue
        widths.append(w)
        heights.append(h)
        scale = (c["rw"] / w) if c.get("rw") and w else 1.0
        scrolls = bool(c.get("sw") and c["sw"] > column + 1)
        laid.append({"row": row, "w": w, "h": h, "rw": c.get("rw"), "scale": scale,
                     "font": c.get("fs"), "scrolls": scrolls})
        if w > column:
            ident = "%s#%d" % (row["page"], row["i"])
            if column == COLUMN and ident in ACCEPTED_OVERWIDE:
                accepted.append((ident, w))
            else:
                problems.append("OVERWIDE %s#%d: %.0fpx > 正文列宽 %dpx"
                                % (row["page"], row["i"], w, column))
        if floor and c.get("fs") and c["fs"] < floor:
            problems.append("ILLEGIBLE %s#%d: 标签实绘 %.1fpx < %.1fpx（自然 %.0fpx 挤进 %dpx，"
                            "缩放 %.2f%s）" % (row["page"], row["i"], c["fs"], floor, w, column,
                                            round(scale, 2), "，容器横向滚动" if scrolls else ""))
    return problems, widths, heights, controls, laid, accepted


def derived_fonts(laid, column, target):
    """The smallest label each diagram paints in some *other* column, from this run's measured paint.

    Mermaid scales a too-wide diagram uniformly, so a label painted at F px inside a `column` box is
    painted at F * min(1, target/w) / min(1, column/w) in a `target` box, where w is the natural width
    this run measured in the browser. Round 73 checked that derivation against a real 608px render of
    every diagram: painted fonts matched to 0.1% and the under-bar count differed by the single
    diagram sitting 0.006px from the bar. So a count derived this way is a bar-crossing tally, not a
    per-diagram judgement, and `--column <target>` remains the way to render for real.
    """
    pairs = []
    for x in laid:
        if not x["font"] or not x["w"]:
            continue
        s_here = min(1.0, column / x["w"])
        pairs.append((x, x["font"] * min(1.0, target / x["w"]) / s_here))
    return pairs


def laptop_reading(laid, column, target=COLUMN_LAPTOP, who="laptop"):
    """What the same diagrams cost a reader in another column, derived from this run's measured paint.

    Called twice by the default run: once for the 608px laptop column (round 73) and once for the
    342px box a phone reader is given (round 107). Same arithmetic, same report-only status, because
    in both cases the fix is a content decision about the diagrams, not a ruler's.

    See derived_fonts for the arithmetic and the round 73 check behind it. Report-only: redrawing the
    book's diagrams for 608px is a content decision, not a ruler's.
    """
    pairs = derived_fonts(laid, column, target)
    if not pairs:
        print("  %s reading: no diagram reported a painted font, so nothing to derive" % who)
        return pairs
    below = [p for p in pairs if p[1] < LABEL_BAR]
    here = [p for p in pairs if p[0]["font"] < LABEL_BAR]
    print("%s reading (the same diagrams in the %dpx column a %s reader gets, derived from this run's"
          " paint): %d of %d paint their smallest label below %.0fpx, vs %d at %dpx"
          % (who, target, who, len(below), len(pairs), LABEL_BAR, len(here), column))
    worst = min(pairs, key=lambda q: q[1])
    print("  worst: %s #%d natural %.0fpx -> smallest label %.1fpx at %dpx, %.1fpx at %dpx"
          % (worst[0]["row"]["page"], worst[0]["row"]["i"], worst[0]["w"], worst[0]["font"], column,
             worst[1], target))
    print("  not counted as findings: redrawing diagrams for %dpx is a content decision, see round"
          " 73's log entry%s"
          % (target, " (the column axis re-measures %d on the live page every run)" % target
             if target == COLUMN_LAPTOP else
             ". Both boxes are now re-measured on the live page: the 608px one by the column axis's"
             " hydrated leg, this one by its phone diagram leg (round 108), which reads the diagram"
             " svg's painted width inside the %dpx column and reddens PHONE-DIAG-BOX if the %dpx"
             " constant below stops matching" % (COLUMN_PHONE, COLUMN_PHONE)))
    if target == COLUMN_LAPTOP:
        print("  accuracy of the line above: derived from this run's paint, and checked against a real"
              " 608px render in round 73 - painted fonts match to 0.1%, the under-bar count to within"
              " the one diagram sitting 0.006px from the bar, so it is a tally and not a per-diagram"
              " judgement")
    else:
        print("  accuracy of the line above: the %dpx box is a live measurement, not the column minus a"
              " guess -- round 107 read vw=390 and found the reader's column at 358 with the diagram"
              " box 342 inside it (the wrapper's own padding), and re-checked the derivation against two"
              " diagrams painted on that live page (what-is-agent#1 and machine-learning-basics#1,"
              " within 0.1px of this arithmetic). Redrawing a diagram moves both sides together." % target)
    return pairs


# ---- round 109: the homepage's geometry sentence pays for its own numbers -----------------------
# Every figure in that bullet used to be hand-copied from a run nobody re-ran. It rotted for 47
# rounds (the page claimed "104 张超宽" long after the axis started printing a different number),
# and round 109 re-anchored it by hand *again* — so the same class of lie shipped for one more turn.
# The clause patterns are copied out of the homepage's own sentences: reword or delete one and this
# axis reddens HOMEPAGE-BLIND instead of silently dropping the check.
HOME_BLOCKS = r"全书 (\d+) 张 Mermaid 图经真解析器逐块校验"
HOME_MAXW = r"最宽 (\d+)px"
HOME_CLAUSE = (r"按真实列宽重跑全站：(\d+) 张超宽、(\d+) 张被缩小、\*\*(\d+) 张能横向滚动\*\*，"
               r"(\d+) 张标签实绘 <12px、最小 \*\*([\d.]+)px\*\*")
HOME_CHOICE = r"把 (\d+) 张压回 768"
HOME_WIDE = r"按它复跑全站还剩 \*\*(\d+) 张\*\*轻微超宽（(\d+)–(\d+)px，最小标签 ([\d.]+)px）"
HOME_CLEAR = r"「(\d+) 张 <12px」清零"
HOME_MIN_NUMBERS = 13          # how much of the sentence this axis claims to have judged


def home_line(text):
    """The one homepage bullet this axis owns. The gate judges that line, never the whole file."""
    lines = [ln for ln in text.splitlines() if HOME_MARK in ln]
    return lines[0] if len(lines) == 1 else None


def homepage_numbers(rows, widths, problems, scaled, scrolling, laid, column):
    """This run's readings, in the units the homepage writes them in."""
    fonts = [x["font"] for x in laid if x["font"]]
    over = sorted([x["w"] for x in laid if x["w"] > WIDE_COLUMN])
    wide_fonts = [v for _, v in derived_fonts(laid, column, WIDE_COLUMN)]
    return {
        "blocks": len(rows),
        "maxw": int(round(max(widths))),
        "overwide": len([x for x in laid if x["w"] > column]),
        "scaled": len(scaled),
        "scrolling": len(scrolling),
        "under12": len([f for f in fonts if f < LABEL_BAR]),
        "minfont": round(min(fonts), 1),
        "wide_count": len(over),
        "wide_lo": int(round(min(over))) if over else 0,
        "wide_hi": int(round(max(over))) if over else int(round(max(widths))),
        "wide_minfont": round(min(wide_fonts), 1) if wide_fonts else 0.0,
        "wide_under12": len([v for v in wide_fonts if v < LABEL_BAR]),
    }


def homepage_tally(numbers, text):
    """(findings, judged): compare the homepage's geometry sentence against this run.

    Scoped to the one bullet this axis owns — a gate over the whole file would fire on any bullet's
    number and its silence would never mean "checked". Judged short of HOME_MIN_NUMBERS is itself a
    finding, so a sentence that stops containing the clauses reddens instead of reading green.
    """
    findings, judged = [], []
    line = home_line(text)
    if line is None:
        return (["HOMEPAGE-BLIND bullet: docs/README.md no longer has exactly one bullet carrying "
                 "「%s」, so this axis has nothing to judge" % HOME_MARK], judged)

    def want(label, pattern, groups):
        m = re.search(pattern, line)
        if not m:
            findings.append("HOMEPAGE-BLIND %s: 首页那句「%s」里找不到这段字：%s…"
                            % (label, HOME_MARK, pattern[:24]))
            return
        for idx, value in groups:
            judged.append(label)
            got = m.group(idx)
            if abs(float(got) - float(value)) > 0.5:
                findings.append("HOMEPAGE-BADGE %s: 首页印 %s，判据这一趟量到 %s" % (label, got, value))

    want("block-count", HOME_BLOCKS, [(1, numbers["blocks"])])
    for m in re.finditer(HOME_MAXW, line):
        judged.append("max-width")
        if abs(float(m.group(1)) - numbers["maxw"]) > 0.5:
            findings.append("HOMEPAGE-BADGE max-width: 首页印 %s，判据这一趟量到 %d"
                            % (m.group(1), numbers["maxw"]))
    want("column-%d" % COLUMN, HOME_CLAUSE,
         [(1, numbers["overwide"]), (2, numbers["scaled"]), (3, numbers["scrolling"]),
          (4, numbers["under12"]), (5, numbers["minfont"])])
    want("overwide-restated", HOME_CHOICE, [(1, numbers["overwide"])])
    want("wide-layout", HOME_WIDE, [(1, numbers["wide_count"]), (2, numbers["wide_lo"]),
                                    (3, numbers["wide_hi"]), (4, numbers["wide_minfont"])])
    want("wide-clears", HOME_CLEAR, [(1, numbers["under12"])])
    if numbers["wide_under12"]:
        findings.append("HOMEPAGE-STILL-UNDER: 首页说宽版布局下「<12px」清零，实测在 %dpx 格子里还有 "
                        "%d 张低于 %gpx" % (WIDE_COLUMN, numbers["wide_under12"], LABEL_BAR))
    if len(judged) < HOME_MIN_NUMBERS:
        findings.append("HOMEPAGE-BLIND coverage: 这句里只判到 %d 个数（%s），期望 >= %d"
                        % (len(judged), " ".join(sorted(set(judged))), HOME_MIN_NUMBERS))
    return findings, judged


def _bump(pattern, idx, delta, text):
    """Move one number inside a matched clause — the planted way to be wrong."""
    m = re.search(pattern, text)
    assert m, "a control needs %s… to match the homepage" % pattern[:24]
    s, e = m.span(idx)
    val = m.group(idx)
    new = str(int(val) + delta) if "." not in val else "%.1f" % (float(val) + delta)
    assert new != val
    return text[:s] + new + text[e:]


def _swap(text, old, new, count=1):
    assert old in text, "control has nothing to grab: %r is not in the homepage" % old[:40]
    return text.replace(old, new, count)


def _out_of_scope(text, home_line):
    """Bump the first number that is NOT on the geometry bullet. Returns None if none exists."""
    lines = text.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if i == home_line:
            continue
        m = re.search(r"\d+", ln)
        if m:
            s, e = m.span()
            return "".join(lines[:i]) + ln[:s] + "9" * (e - s) + ln[e:] + "".join(lines[i + 1:])
    return None


def homepage_controls(numbers, text):
    """Each planted lie must name its own bucket; an out-of-scope edit must stay quiet.

    Run against the real homepage text with the real numbers, so a control that only fires because
    the pattern was written for a made-up string cannot pass.
    """
    m = re.search(HOME_CLAUSE, text)
    assert m, "controls need the live clause first: HOME_CLAUSE does not match docs/README.md"
    n = re.search(HOME_WIDE, text)
    assert n, "controls need the live wide-layout clause"
    blocks = re.search(HOME_BLOCKS, text)
    assert blocks, "controls need the live block-count clause"
    cases = [
        ("wrong overwide count", _bump(HOME_CLAUSE, 1, 47, text), "HOMEPAGE-BADGE column-"),
        ("wrong scaled count", _bump(HOME_CLAUSE, 2, 3, text), "HOMEPAGE-BADGE column-"),
        ("wrong scroller count", _bump(HOME_CLAUSE, 3, 1, text), "HOMEPAGE-BADGE column-"),
        ("wrong under-bar count", _bump(HOME_CLAUSE, 4, 11, text), "HOMEPAGE-BADGE column-"),
        ("wrong smallest label", _bump(HOME_CLAUSE, 5, 4.0, text), "HOMEPAGE-BADGE column-"),
        ("stale restatement", _bump(HOME_CHOICE, 1, 47, text), "HOMEPAGE-BADGE overwide-restated"),
        ("wrong wide count", _bump(HOME_WIDE, 1, 8, text), "HOMEPAGE-BADGE wide-layout"),
        ("wrong wide label", _bump(HOME_WIDE, 4, 4.0, text), "HOMEPAGE-BADGE wide-layout"),
        ("wrong clear claim", _bump(HOME_CLEAR, 1, 11, text), "HOMEPAGE-BADGE wide-clears"),
        ("clause deleted", _swap(text, m.group(0), ""), "HOMEPAGE-BLIND"),
        ("wide clause deleted", _swap(text, n.group(0), ""), "HOMEPAGE-BLIND"),
        ("sentence reworded", _swap(text, blocks.group(0), "全书的 Mermaid 图都过了真解析器"),
         "HOMEPAGE-BLIND"),
        ("whole bullet gone", _swap(text, home_line(text) + "\n", ""), "HOMEPAGE-BLIND"),
    ]
    bad = []
    for name, mutated, expect in cases:
        found, _ = homepage_tally(numbers, mutated)
        if not any(expect in line for line in found):
            bad.append("%s: planted %s, gate said %s" % (name, expect, found[:2] or "nothing"))
    # The scope control: this axis owns one sentence, so a number anywhere else in the file moving
    # must not be able to redden it — otherwise a green "0 mismatches" is really "0 matches".
    home_idx = next(i for i, ln in enumerate(text.splitlines()) if HOME_MARK in ln)
    elsewhere = _out_of_scope(text, home_idx)
    assert elsewhere is not None, "no out-of-scope number to plant the scope control on"
    quiet, _ = homepage_tally(numbers, elsewhere)
    cases.append(("another bullet's number moved", elsewhere, ""))
    if quiet:
        bad.append("out-of-scope edit reddened the gate: %s" % quiet[:2])
    return len(cases), bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mermaid-js", help="directory holding node_modules/mermaid, or the bundle itself")
    ap.add_argument("--budget", type=int, default=90000,
                    help="real milliseconds a single batch may take before it is called unfinished")
    ap.add_argument("--batch", type=int, default=40,
                    help="blocks per fixture page — one page of 217 exhausts the virtual-time budget")
    ap.add_argument("--skip-alignment", action="store_true", help="offline runs only; a real check compares engines")
    ap.add_argument("--column", type=int, default=COLUMN,
                    help="content column the reader actually gets, px. Round 62 measured the live "
                         "default at 768 (1152 only in GitBook's wide layout), which is now the "
                         "default here; pass --column 1120 to reproduce the historic reading.")
    ap.add_argument("--widths", type=int, default=0, metavar="N",
                    help="also print the N widest authored diagrams with their scale vs --column")
    ap.add_argument("--phone-worst", type=int, default=0, metavar="N",
                    help="print the N diagrams whose smallest label is painted smallest in the %dpx "
                         "phone box, worst first. Round 109's work list: the phone leg of "
                         "check_live_column.py proves the box, this says which diagrams to redraw."
                         % COLUMN_PHONE)
    ap.add_argument("--font-floor", type=float, default=0.0, metavar="PX",
                    help="judge legibility, not just width: fail any diagram whose label is painted "
                         "smaller than PX in the --column container. 0 keeps the historic width-only "
                         "verdict. The reader's body text is 16px; round 62 measures what a diagram "
                         "label actually costs them.")
    ap.add_argument("--eyeball", metavar="PAGE", help="render one page's diagrams to a PNG and exit")
    ap.add_argument("--selftest", action="store_true",
                    help="run this axis's planted control arms (eyeball ink guard + accepted-debt "
                         "ledger) and exit; `run_battery.py --selftests` discovers it by this flag")
    ap.add_argument("--engine-selftest", action="store_true",
                    help="check only that the launcher's engine preflight has teeth: it accepts a "
                         "browser that renders and refuses one that exits 0 without a DOM")
    args = ap.parse_args()

    if args.engine_selftest:
        return engine_selftest()

    rows = authored_blocks()
    print("authored mermaid blocks=%d across %d pages"
          % (len(rows), len({r["page"] for r in rows})))
    assert len(rows) >= 200, "vacuity: extractor only found %d blocks" % len(rows)

    if args.selftest:
        # Both control helpers return (failure lines, checks) — same shape, so the arithmetic below
        # cannot read a list as a count (which is exactly how this handler first crashed).
        ink_bad, ink_checks = ink_controls()
        debt_bad, debt_checks = debt_controls()
        for line in ink_bad + debt_bad:
            print("CONTROL-FAILED: %s" % line)
        print("controls: ink %d of %d, debt %d of %d, %d failed"
              % (ink_checks - len(ink_bad), ink_checks,
                 debt_checks - len(debt_bad), debt_checks,
                 len(ink_bad) + len(debt_bad)))
        sys.exit(1 if (ink_bad or debt_bad) else 0)
    if args.eyeball:
        rel = os.path.normpath(os.path.join(DOCS, args.eyeball.replace("\\", "/")))
        src = open(rel, encoding="utf-8").read()
        blocks = [{"page": args.eyeball, "i": i, "src": s} for i, s in enumerate(mermaid_blocks(src), 1)]
        if not blocks:
            sys.exit("no mermaid blocks in %s" % args.eyeball)
        js = find_bundle(args.mermaid_js)
        sys.exit(eyeball(js, blocks, args.budget))

    js = find_bundle(args.mermaid_js)
    if not js:
        print("SKIP: no mermaid bundle. Install once with\n"
              "  npm install mermaid@11.14.0 --prefix <dir>\nand pass --mermaid-js <dir>. "
              "Refusing to report 0 problems without an engine.")
        return 2
    local = bundle_version(open(js, encoding="utf-8").read())
    if args.skip_alignment:
        print("engine %s (alignment NOT checked — offline run)" % (local or "unknown"))
    else:
        live = live_version()
        print("engine alignment: local=%s live=%s" % (local, live))
        if not local or not live or local != live:
            print("MISALIGNED: measuring geometry with a different engine than the reader's browser "
                  "is how round 14 reported a clean site that was 1712px wide. Install the live version.")
            return 2

    planted = [{"page": "CONTROL", "i": 1, "src": CONTROL_WIDE},
               {"page": "CONTROL", "i": 2, "src": CONTROL_BROKEN}]
    srv = Server(js)
    try:
        cells = render(srv, rows + planted, args.budget, args.batch, args.column)
    finally:
        srv.close()
    problems, widths, heights, controls, laid, accepted = judge(rows + planted, cells, args.column,
                                                                args.font_floor)
    accepted_rows, paid_rows = debt_readings(accepted, laid, args.column)
    debt_bad, debt_checks = debt_controls()
    for line in debt_bad:
        problems.append("DEBT-CONTROL " + line)
    print("rendered=%d/%d authored diagrams  max width=%.0fpx  max height=%.0fpx (column %dpx)"
          % (len(widths), len(rows), max(widths), max(heights), args.column))
    print("planted counterexamples: %s" % ", ".join(controls))
    if args.column == COLUMN:
        # The debt stays on the record every run: a count the reader's homepage prints, the widest
        # still owing, and a named line for anything the ledger has outlived.
        print("  accepted debt (%s): %d of %d entries over %dpx, loud and not gating; %d new"
              % (RULING, len(accepted_rows), len(ACCEPTED_OVERWIDE), COLUMN,
                 len([p for p in problems if p.startswith("OVERWIDE")])))
        print("  debt controls: %d of %d able to fire (both directions: a listed diagram is debt, "
              "an unlisted one gates)" % (debt_checks - len(debt_bad), debt_checks))
        for line in paid_rows:
            print("  NOTE ACCEPTED-FIXED %s 已经不超宽了，把它从名单里删掉（这条不卡退出码）" % line)
    # The instrument has to answer before the content does: if nothing in the sweep is scaled and
    # nothing scrolls, a "0 ILLEGIBLE" reading would be a silent zero rather than a measurement.
    scaled = [x for x in laid if x["scale"] < 0.985]
    scrolling = [x for x in laid if x["scrolls"]]
    print("  laid out in a %dpx column: %d scaled down, %d in a horizontal scroller, "
          "%d neither (fonts: min %.1fpx  median %.1fpx)"
          % (args.column, len(scaled), len(scrolling),
             len([x for x in laid if x["scale"] >= 0.985 and not x["scrolls"]]),
             min([x["font"] for x in laid if x["font"]] or [0]),
             sorted([x["font"] for x in laid if x["font"]] or [0])[len(
                 [x for x in laid if x["font"]]) // 2]))
    if args.column == COLUMN:
        lap = laptop_reading(laid, args.column)
        phone = laptop_reading(laid, args.column, COLUMN_PHONE, "phone")
        # The two readings come off one derivation, so the narrower column can only ever cost a
        # reader more. If a future edit swaps the targets or drops the min(), the phone tally stops
        # being worse than the laptop's and this dies instead of printing a comfortable number.
        byx = {id(x): v for x, v in lap}
        worse = [(x["row"]["page"], x["row"]["i"], v, byx[id(x)]) for x, v in phone
                 if v > byx[id(x)] + 1e-9]
        assert not worse, "the %dpx reading painted above the %dpx one: %s" % (
            COLUMN_PHONE, COLUMN_LAPTOP, worse[:3])
        assert (len([1 for _, v in phone if v < LABEL_BAR])
                >= len([1 for _, v in lap if v < LABEL_BAR])), \
            "a narrower column cannot flag fewer under-bar diagrams"
        if args.phone_worst:
            order = sorted(phone, key=lambda q: q[1])
            assert len(order) >= args.phone_worst, \
                "vacuity: only %d diagrams carry a painted label, asked for %d" % (
                    len(order), args.phone_worst)
            print("  phone work list, worst %d of %d under %gpx (the label a 342px box paints, and "
                  "what the same run paints at the two wider boxes):"
                  % (args.phone_worst, len([1 for _, v in order if v < LABEL_BAR]), LABEL_BAR))
            for x, v in order[:args.phone_worst]:
                print("     %-52s #%d natural %5.0fpx -> 342px %4.1fpx  608px %4.1fpx  768px %4.1fpx"
                      % (x["row"]["page"], x["row"]["i"], x["w"], v, byx[id(x)], x["font"] or 0))
        # The homepage prints this axis's tallies for the reader, so they have to be the same number.
        home_text = open(HOMEPAGE, encoding="utf-8").read()
        numbers = homepage_numbers(rows, widths, problems, scaled, scrolling, laid, args.column)
        home_findings, judged = homepage_tally(numbers, home_text)
        assert len(judged) >= HOME_MIN_NUMBERS, \
            "vacuity: the homepage gate judged %d numbers %s, expected >= %d" % (
                len(judged), sorted(set(judged)), HOME_MIN_NUMBERS)
        try:
            total, dead = homepage_controls(numbers, home_text)
        except AssertionError as exc:
            total, dead = 0, ["the controls never ran: %s" % exc]
        problems.extend(home_findings)
        for line in dead:
            problems.append("HOME-CONTROL %s" % line)
        print("homepage tally: %d numbers judged out of the sentence this axis owns, %d of %d "
              "planted lies caught (%s)"
              % (len(judged), total - len(dead), total,
                 " ".join("%s=%s" % (k, numbers[k]) for k in
                          ("blocks", "maxw", "overwide", "scaled", "scrolling", "under12",
                           "minfont", "wide_count", "wide_lo", "wide_hi", "wide_minfont"))))
    else:
        print("homepage tally: NOT JUDGED — this run laid the diagrams out in a %dpx column, while "
              "the sentence on docs/README.md is anchored on the %dpx one. Run without --column to "
              "judge it." % (args.column, COLUMN))
    # The two extremes by name, so a future round can judge them without re-running anything:
    # "max width 1116px" is only useful if you know which diagram is at 1116 and how close it is.
    ranked = sorted(((x["row"], x["w"], x["h"], x) for x in laid), key=lambda t: -t[1])
    for r, w, h, x in ranked[:3]:
        print("  widest  %-56s #%d  %.0fx%.0fpx" % (r["page"], r["i"], w, h))
    for r, w, h, x in sorted(ranked, key=lambda t: -t[2])[:3]:
        print("  tallest %-56s #%d  %.0fx%.0fpx" % (r["page"], r["i"], w, h))
    if args.widths:
        over = [t for t in ranked if t[1] > args.column]
        print("  width distribution vs %dpx: %d of %d diagrams exceed it"
              % (args.column, len(over), len(ranked)))
        for band in (900, 800, 768, 720, 640):
            print("     >%-5d %3d" % (band, len([t for t in ranked if t[1] > band])))
        for r, w, h, x in ranked[:args.widths]:
            print("     %-56s #%d %5.0fpx -> painted %5spx (scale %.2f) label %.1fpx %s"
                  % (r["page"], r["i"], w, x["rw"], x["scale"], x["font"] or 0,
                     "SCROLLS" if x["scrolls"] else ""))
    if args.font_floor:
        byfont = sorted([x for x in laid if x["font"]], key=lambda x: x["font"])
        for x in byfont[:args.widths or 10]:
            print("     smallest-label %-52s #%d %5.1fpx (natural %.0f, painted %s)"
                  % (x["row"]["page"], x["row"]["i"], x["font"], x["w"], x["rw"]))
    for p in problems[:30]:
        print("  -", p)
    if len(problems) > 30:
        # A capped list must not be able to hide a whole finding class. Round 110 hit this: 54 of the
        # 56 problems were OVERWIDE lines, so the two homepage findings never reached the printout,
        # and "13 of 14 planted lies caught" had no named reason next to it.
        hidden = problems[30:]
        kinds = {}
        for p in hidden:
            kinds[p.split(" ")[0]] = kinds.get(p.split(" ")[0], 0) + 1
        print("  - … %d more not printed: %s" % (len(hidden), ", ".join(
            "%s x%d" % (k, v) for k, v in sorted(kinds.items()))))
        for p in [q for q in hidden if not q.startswith("OVERWIDE")]:
            print("  -", p)
    print("problems=%d" % len(problems))
    return 1 if problems else 0


# Round 120's named debt, fixed in round 121: `--eyeball` used to verdict its own PNG by
# `os.path.getsize() > 20000`. Size is neither necessary nor sufficient for "the reader would see a
# diagram" — `.tmp-projects/r120_comm.png` is a clean 1280x900 render of the stacked star /
# point-to-point diagram and weighs 15,442 bytes, so the axis exited 1 with no reason line, while a
# mostly-empty wide canvas would have passed. The quantity the guard means is ink coverage.
PNG_SIG = b"\x89PNG\r\n\x1a\n"
INK_DELTA = 30            # a pixel is ink when it differs from the page's own background by more than this
INK_MIN_FRACTION = 0.0003  # pinned by the controls below, which print every arm's measured fraction
INK_MAX_SAMPLED = 400000  # the loop is O(pixels); a diagram paints thousands of px, so thinning is safe


def _png_rows(data):
    """(width, height, channels, rows) for a non-interlaced 8-bit PNG; anything else raises.

    Refusing is part of the contract: a half-read file reporting "almost no ink" would file a broken
    engine as a blank diagram, which is the same blind spot the byte threshold had.
    """
    if not data.startswith(PNG_SIG):
        raise ValueError("not a PNG")
    pos, idat, ihdr = 8, [], None
    while pos + 12 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        if ln + 12 > len(data) - pos:
            raise ValueError("truncated %s chunk" % kind.decode("ascii", "replace"))
        if kind == b"IHDR":
            ihdr = data[pos + 8:pos + 8 + ln]
        elif kind == b"IDAT":
            idat.append(data[pos + 8:pos + 8 + ln])
        elif kind == b"IEND":
            break
        pos += 12 + ln
    if not ihdr or not idat:
        raise ValueError("no IHDR/IDAT")
    width, height, depth, ctype, _comp, _filt, interlace = struct.unpack(">IIBBBBB", ihdr[:13])
    if depth != 8 or interlace != 0 or ctype not in (0, 2, 6):
        raise ValueError("unsupported PNG (depth=%d color=%d interlace=%d)" % (depth, ctype, interlace))
    channels = {0: 1, 2: 3, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = width * channels
    if len(raw) != (stride + 1) * height:
        raise ValueError("decoded %d bytes, need %d" % (len(raw), (stride + 1) * height))
    rows, prev = [], bytearray(stride)
    for y in range(height):
        base = y * (stride + 1)
        ft = raw[base]
        line = bytearray(raw[base + 1:base + 1 + stride])
        if ft == 1:
            for x in range(channels, stride):
                line[x] = (line[x] + line[x - channels]) & 0xFF
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ft == 3:
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif ft == 4:
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                b, c = prev[x], (prev[x - channels] if x >= channels else 0)
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 0xFF
        elif ft != 0:
            raise ValueError("bad filter type %d on row %d" % (ft, y))
        rows.append(bytes(line))
        prev = line
    return width, height, channels, rows


def ink_fraction(path):
    """Share of sampled pixels differing from the page's top-left pixel (its own background).

    Background-relative, not "non-white", so a diagram painted on a tinted canvas cannot measure zero
    and get a correct render refused.
    """
    with open(path, "rb") as fh:
        width, height, channels, rows = _png_rows(fh.read())
    bg = rows[0][:channels]
    step = max(1, int((width * height) / INK_MAX_SAMPLED) + 1) if width * height > INK_MAX_SAMPLED else 1
    ink = seen = 0
    for y in range(0, height, step):
        row = rows[y]
        for x in range(0, width, step):
            o = x * channels
            seen += 1
            if any(abs(row[o + i] - bg[i]) > INK_DELTA for i in range(channels)):
                ink += 1
    if not seen:
        raise ValueError("no pixels sampled (%dx%d step %d)" % (width, height, step))
    return ink / seen, seen


def _write_png(path, width, height, paint):
    """Minimal 8-bit RGB encoder (filter 0) so the planted controls are real PNG bytes, not mocks."""
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(paint(x, y))

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    with open(path, "wb") as fh:
        fh.write(PNG_SIG)
        fh.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        fh.write(chunk(b"IDAT", zlib.compress(bytes(rows), 6)))
        fh.write(chunk(b"IEND", b""))


def eyeball_verdict(path):
    """(ok, printed reason) — ink decides, the byte size is reported but never judged."""
    if not os.path.isfile(path):
        return False, "no PNG written"
    try:
        frac, seen = ink_fraction(path)
    except (ValueError, OSError) as exc:
        return False, "PNG unreadable (%s), so no ink verdict" % exc
    return frac >= INK_MIN_FRACTION, "ink=%.4f%% of %d sampled px (bar %.4f%%)" % (
        100 * frac, seen, 100 * INK_MIN_FRACTION)


def ink_controls():
    """(failure lines, checks) for the ink guard, same shape as debt_controls(): two arms that must
    pass by content, four that must refuse, and the two narrow-on-wide arms the byte rule got wrong.
    A missing real artifact is reported, never counted as ok."""
    tmp = tempfile.mkdtemp(prefix="mmdink")
    inked = lambda x, y: (31, 41, 55) if 100 <= x < 260 and 80 <= y < 240 else (255, 255, 255)
    shape = os.path.join(tmp, "shape.png")
    _write_png(shape, 640, 480, inked)
    tinted = os.path.join(tmp, "tinted.png")
    _write_png(tinted, 640, 480, lambda x, y: (31, 41, 55) if 100 <= x < 260 and 80 <= y < 240
               else (240, 244, 248))
    blank = os.path.join(tmp, "blank.png")
    _write_png(blank, 640, 480, lambda x, y: (255, 255, 255))
    dot = os.path.join(tmp, "dot.png")
    _write_png(dot, 640, 480, lambda x, y: (0, 0, 0) if (x, y) == (10, 10) else (255, 255, 255))
    cut = os.path.join(tmp, "cut.png")
    with open(shape, "rb") as fh:
        half = fh.read()[:1200]
    with open(cut, "wb") as fh:
        fh.write(half)
    arms = [("painted block on white must pass", shape, True, None),
            ("painted block on a tinted canvas must pass", tinted, True, None),
            ("all-white page must be refused", blank, False, None),
            ("one stray pixel must be refused", dot, False, None),
            ("a truncated PNG must refuse, not report blank", cut, False, "unreadable"),
            # The screenshot engine on this machine is known to exit 0 without writing the file,
            # so "no file at all" has to be a refusal rather than a reading.
            ("an engine that wrote no PNG must be refused", os.path.join(tmp, "never-written.png"),
             False, "no PNG written")]
    bad, checks, lines = 0, 0, []
    for name, path, want, needle in arms:
        ok, line = eyeball_verdict(path)
        checks += 1
        if ok != want or (needle and needle not in line):
            bad += 1
            lines.append("  CONTROL FAILED %s: got ok=%s (%s)" % (name, ok, line))
    frac_blank, _ = ink_fraction(blank)
    frac_dot, _ = ink_fraction(dot)
    frac_shape, _ = ink_fraction(shape)
    frac_tinted, _ = ink_fraction(tinted)
    print("ink bar %.4f%% sits between the refused arms (blank %.4f%%, dot %.4f%%) and the painted "
          "arms (white %.4f%%, tinted %.4f%%)"
          % (100 * INK_MIN_FRACTION, 100 * frac_blank, 100 * frac_dot, 100 * frac_shape, 100 * frac_tinted))
    # A large canvas holding a small diagram is the case the byte rule got wrong in both directions,
    # and this arm regenerates it so the proof does not depend on any round's leftover file.
    wide_empty = os.path.join(tmp, "wide-empty.png")
    _write_png(wide_empty, 1280, 900, lambda x, y: (31, 41, 55) if 100 <= x < 260 and 80 <= y < 240
               else (255, 255, 255))
    size = os.path.getsize(wide_empty)
    ok, line = eyeball_verdict(wide_empty)
    checks += 1
    if not ok or size > 20000:
        bad += 1
        lines.append("  CONTROL FAILED generated narrow-on-wide arm: ok=%s size=%d (%s)" % (ok, size, line))
    else:
        print("generated arm the byte rule would refuse: %d bytes (<= 20000) yet %s" % (size, line))
    narrow = os.path.join(HERE, "..", "..", ".tmp-projects", "r120_comm.png")
    if os.path.isfile(narrow):
        size = os.path.getsize(narrow)
        ok, line = eyeball_verdict(narrow)
        checks += 1
        if not ok or size > 20000:
            bad += 1
            lines.append("  CONTROL FAILED narrow real render: ok=%s size=%d (%s)" % (ok, size, line))
        else:
            print("the arm the old byte rule ate: %s bytes (<= 20000) yet %s" % (size, line))
    else:
        print("  NOTE round-120 narrow render is not on disk (%s) - that arm did not run" % narrow)
    assert bad == len(lines), "ink control counter and its failure list disagree (%d vs %d)" % (bad, len(lines))
    return lines, checks


def eyeball(js_path, blocks, budget):
    """Real rendered PNG of one page's diagrams — the 目检 artifact, reproducible on demand."""
    if not js_path:
        print("SKIP: no mermaid bundle (see --mermaid-js)")
        return 2
    ink_fail, checks = ink_controls()
    for entry in ink_fail:
        print(entry)
    print("ink controls %d of %d able to fire" % (checks - len(ink_fail), checks))
    if ink_fail:
        return 1
    out = os.path.join(tempfile.gettempdir(), "mmd58_eyeball.png")
    if os.path.isfile(out):
        os.remove(out)
    srv = Server(js_path)
    try:
        cells = render_batch(srv, blocks, budget, 1, shot=out)
    finally:
        srv.close()
    failed = [(b["i"], c["fail"]) for b, c in zip(blocks, cells) if c["w"] is None]
    size = os.path.getsize(out) if os.path.isfile(out) else -1
    ok, line = eyeball_verdict(out) if size > 0 else (False, "no PNG written (%d bytes)" % size)
    print("eyeball PNG: %s (%s bytes, %d diagrams, %s; source=%s)"
          % (out, size, len(blocks), line, " ".join(b["page"] for b in blocks)[:60]))
    for i, msg in failed:
        print("  render failed #%d: %s" % (i, msg))
    if failed:
        return 1
    if not ok:
        print("EYEBALL-NO-INK: %s — the engine painted no diagram a reader could see" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
