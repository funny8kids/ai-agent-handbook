"""Render every authored formula through real KaTeX and fail on any that throws.

Why this file exists: README declares one authoritative formula judge (「公式数只认这一个判据
脚本」) but that judge had never been committed — it was assembled in a temp directory each
round and evaporated, which is how the same tree ended up reading 811 / 821 / 834 in three
places. This lands it, and it reuses live_aria_manifest.formula_sources() so the count on this
line and the count the live parity axis compares against the served HTML are the same number
by construction, not by agreement.

KaTeX itself is not a repo dependency: it is resolved through NODE/KATEX paths below, matching
the build the round-53 axis aligned to (0.18.x). If nothing resolves, this judge exits with code
2 and says so — a missing renderer must never read as "0 failures".

The last assertion is the one that matters most: a deliberately broken formula is appended and
must be the only failure. Without it, "failures=0" could mean the renderer never ran.

Usage:
    python tools/checks/check_katex_formulas.py [--katex-dir PATH]
"""
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
RENDERER = os.path.join(HERE, "katex_render.mjs")
sys.path.insert(0, HERE)
import live_aria_manifest as L  # noqa: E402  (shared tokenizer: one definition of "authored")

PHANTOM = "\\frac{1}{"            # must be the only failure, proving the renderer fires


def collect():
    items, pages = [], 0
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir.startswith("14-templates"):
            continue                                 # template pages quote markup, per README
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8").read()
            sources, _ = L.formula_sources(text)
            if not sources:
                continue
            pages += 1
            rel = os.path.relpath(os.path.join(dirpath, fn), DOCS).replace("\\", "/")
            for kind, src in sources:
                items.append({"page": rel, "kind": kind, "src": src})
    return pages, items


def main():
    args = sys.argv[1:]
    katex_dir = args[args.index("--katex-dir") + 1] if "--katex-dir" in args else None
    pages, items = collect()
    payload = items + [{"page": "<self-test>", "kind": "display", "src": PHANTOM}]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
        path = fh.name
    env = dict(os.environ)
    if katex_dir:
        env["KATEX_REQUIRE_FROM"] = katex_dir
    try:
        proc = subprocess.run(["node", RENDERER, path], capture_output=True, text=True, env=env)
    finally:
        os.unlink(path)
    if proc.returncode == 2:
        print("katex render: SKIPPED — %s" % json.loads(proc.stdout or "{}").get("skip", proc.stderr[:200]))
        print("  install it (npm i -g katex) or pass --katex-dir <dir containing node_modules/katex>")
        return 2
    if proc.returncode != 0:
        print("katex render: RUNNER FAILED rc=%d\n%s" % (proc.returncode, proc.stderr[:800]))
        return 1
    out = json.loads(proc.stdout)
    real, planted = [f for f in out["failures"] if f["i"] < len(items)], \
                    [f for f in out["failures"] if f["i"] >= len(items)]
    assert len(items) > 500, "vacuity floor: fewer than 500 formulas means the scan missed pages"
    assert planted, "self-test: the planted %r was NOT caught, so a clean run would prove nothing" % PHANTOM
    assert out["total"] == len(payload), "the renderer lost items"
    print("katex render: pages=%d formulas=%d failures=%d version=%s (planted counterexample caught: 1)"
          % (pages, len(items), len(real), out["version"]))
    for f in real[:40]:
        it = items[f["i"]]
        print("  - %s [%s] %s :: %s" % (it["page"], it["kind"], it["src"].strip().replace("\n", " ")[:70], f["msg"]))
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
