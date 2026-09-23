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
  width      viewBox width vs the ~1120px content column. Over-wide means GitBook scales the
             diagram down and the labels go unreadable (1321px measured once, 1712px in an older
             round) — the defect this axis exists to catch.
  height     reported, not judged: a tall diagram only costs scrolling (max measured 1298px),
             while a wide one costs legibility.

Two planted counterexamples ride along on every run (one unparsable source, one fan-out that must
blow past 1120) and MUST be caught. Without them "0 超宽、0 失败" would also be what a silent
no-op prints — see the project's no-silent-zero rule.

Rendering is local and offline on purpose: Edge headless in this sandbox has no external network,
so the engine is served from 127.0.0.1 together with the fixture, and each batch beacons its
measurements back over HTTP (see fixture_html for why --dump-dom was dropped).

Usage:
    python tools/checks/check_mermaid_geometry.py --mermaid-js <dir-with-node_modules>
    python tools/checks/check_mermaid_geometry.py --eyeball 04-prompt-reasoning/react.md
        -> writes a PNG of that page's diagrams for a real rendered look
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(HERE, "..", "..", "docs"))
SITE = "https://violetnotes.gitbook.io/violetnotes-docs"
COLUMN = 1120                      # measured content column, px
SHOT_BUDGET = 20000                # virtual ms the --eyeball screenshot is allowed to paint in
EDGE_CANDIDATES = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]

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


def fixture_html(srcs, rid, budget, mode="dump"):
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
            "<style>body{margin:0;background:#fff}.cell{width:%%COLUMN%%px;overflow:hidden}</style>"
            "<script src='/mermaid.min.js'></script><div id='out'></div><script>"
            "const items=%%ITEMS%%;const rid=%%RID%%;const limit=%%BUDGET%%;"
            "let done=false;const cells=[];"
            "mermaid.initialize({startOnLoad:false,securityLevel:'loose'});"
            "const post=()=>{navigator.sendBeacon('/report',JSON.stringify({id:rid,done:done,cells:cells}));};"
            "const hang=()=>new Promise((_,rej)=>setTimeout(()=>rej(Error('HANG>'+limit+'ms')),limit));"
            "const run=%%RUN%%;"
            "(async()=>{const o=document.getElementById('out');"
            "for(let i=0;i<items.length;i++){const d=document.createElement('div');d.className='cell';"
            "o.appendChild(d);const rec={i:i,w:null,h:null,fail:null};cells.push(rec);"
            "try{const r=await run(i);d.innerHTML=r.svg;"
            "const m=r.svg.match(/viewBox=.([-\\d.]+) ([-\\d.]+) ([-\\d.]+) ([-\\d.]+)./);"
            "if(m){rec.w=parseFloat(m[3]);rec.h=parseFloat(m[4]);}"
            "else{rec.fail='rendered with no viewBox';%%FAIL%%}}"
            "catch(e){rec.fail=String(e.message).slice(0,140);%%FAIL2%%}}"
            "done=true;post();"
            "setTimeout(()=>{try{window.close();}catch(e){}},80);})();"
            "setTimeout(()=>{if(!done)post();},limit);"
            "</script>" + hold).replace("%%COLUMN%%", str(COLUMN)) \
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

    def edge(self, name, extra=(), height=1400):
        """One headless Edge run owned by this process — terminate() only ever touches our own PID."""
        exe = next((p for p in EDGE_CANDIDATES if os.path.isfile(p)), None)
        if not exe:
            raise SystemExit("no Microsoft Edge found — the geometry axis needs a real renderer")
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--user-data-dir=" + self.new_profile(), "--window-size=%d,%d" % (COLUMN, height)]
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


def render_batch(srv, blocks, budget, rid, shot=None):
    """One Edge pass over a batch of blocks; returns [(w, h|fail)] in authoring order."""
    name = "fixture%d.html" % rid
    if not shot:
        srv.hold(rid, budget / 1000 + 30)
    open(os.path.join(srv.root, name), "w", encoding="utf-8").write(
        fixture_html([b["src"] for b in blocks], rid, budget, "shot" if shot else "dump"))
    if shot:
        # A screenshot fires when Chrome's *virtual* time runs out, so this mode waits for Edge to
        # exit by itself; the sweep mode is held open by the latch and stops when the report lands.
        proc = srv.edge(name, ["--virtual-time-budget=%d" % SHOT_BUDGET, "--screenshot=" + shot],
                        min(900 * len(blocks), 9000))
        try:
            proc.wait(SHOT_BUDGET / 1000 + 120)
        except subprocess.TimeoutExpired:
            pass
    else:
        proc = srv.edge(name, ["--dump-dom"])
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
    return [(c["w"], c["h"] if c["w"] is not None else c["fail"]) for c in cells]


def render(srv, blocks, budget, batch):
    boxes = []
    for start in range(0, len(blocks), batch):
        boxes += render_batch(srv, blocks[start:start + batch], budget, start // batch + 1)
    return boxes


def judge(rows, boxes):
    """FAILED / OVERWIDE for real pages, plus the two planted controls that must be caught."""
    problems, widths, heights, controls = [], [], [], []
    for row, (w, h) in zip(rows, boxes):
        if row["page"] == "CONTROL":
            kind = "OK"
            if w is None:
                kind = "FAILED" if row["i"] == 2 else "MISS"
            elif w > COLUMN:
                kind = "OVERWIDE" if row["i"] == 1 else "MISS"
            controls.append("wide->%s(%s)" % (kind, "w=%s" % w if w else h or ""))
            if row["i"] == 1 and (w is None or w <= COLUMN):
                problems.append("CONTROL-DEAD: the planted over-wide diagram did not exceed %dpx" % COLUMN)
            if row["i"] == 2 and w is not None:
                problems.append("CONTROL-DEAD: the planted unparsable diagram rendered anyway")
            continue
        if w is None:
            problems.append("FAILED %s#%d: %s" % (row["page"], row["i"], str(h)[:110]))
            continue
        widths.append(w)
        heights.append(h)
        if w > COLUMN:
            problems.append("OVERWIDE %s#%d: %.0fpx > 正文列宽 %dpx" % (row["page"], row["i"], w, COLUMN))
    return problems, widths, heights, controls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mermaid-js", help="directory holding node_modules/mermaid, or the bundle itself")
    ap.add_argument("--budget", type=int, default=90000,
                    help="real milliseconds a single batch may take before it is called unfinished")
    ap.add_argument("--batch", type=int, default=40,
                    help="blocks per fixture page — one page of 217 exhausts the virtual-time budget")
    ap.add_argument("--skip-alignment", action="store_true", help="offline runs only; a real check compares engines")
    ap.add_argument("--eyeball", metavar="PAGE", help="render one page's diagrams to a PNG and exit")
    args = ap.parse_args()

    rows = authored_blocks()
    print("authored mermaid blocks=%d across %d pages"
          % (len(rows), len({r["page"] for r in rows})))
    assert len(rows) >= 200, "vacuity: extractor only found %d blocks" % len(rows)

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
        boxes = render(srv, rows + planted, args.budget, args.batch)
    finally:
        srv.close()
    problems, widths, heights, controls = judge(rows + planted, boxes)
    print("rendered=%d/%d authored diagrams  max width=%.0fpx  max height=%.0fpx (column %dpx)"
          % (len(widths), len(rows), max(widths), max(heights), COLUMN))
    print("planted counterexamples: %s" % ", ".join(controls))
    # The two extremes by name, so a future round can judge them without re-running anything:
    # "max width 1116px" is only useful if you know which diagram is at 1116 and how close it is.
    ranked = sorted(((r, w, h) for r, (w, h) in zip(rows, boxes) if w is not None),
                    key=lambda t: -t[1])
    for r, w, h in ranked[:3]:
        print("  widest  %-56s #%d  %.0fx%.0fpx" % (r["page"], r["i"], w, h))
    for r, w, h in sorted(ranked, key=lambda t: -t[2])[:3]:
        print("  tallest %-56s #%d  %.0fx%.0fpx" % (r["page"], r["i"], w, h))
    for p in problems[:30]:
        print("  -", p)
    print("problems=%d" % len(problems))
    return 1 if problems else 0


def eyeball(js_path, blocks, budget):
    """Real rendered PNG of one page's diagrams — the 目检 artifact, reproducible on demand."""
    if not js_path:
        print("SKIP: no mermaid bundle (see --mermaid-js)")
        return 2
    out = os.path.join(tempfile.gettempdir(), "mmd58_eyeball.png")
    if os.path.isfile(out):
        os.remove(out)
    srv = Server(js_path)
    try:
        boxes = render_batch(srv, blocks, budget, 1, shot=out)
    finally:
        srv.close()
    failed = [(b["i"], h) for b, (w, h) in zip(blocks, boxes) if w is None]
    size = os.path.getsize(out) if os.path.isfile(out) else -1
    print("eyeball PNG: %s (%s bytes, %d diagrams, source=%s)"
          % (out, size, len(blocks), " ".join(b["page"] for b in blocks)[:60]))
    for i, msg in failed:
        print("  render failed #%d: %s" % (i, msg))
    if failed:
        return 1
    return 0 if size > 20000 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
