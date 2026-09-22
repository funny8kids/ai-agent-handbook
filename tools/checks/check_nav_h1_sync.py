"""Standing check: every page's published title must be the page's own H1.

Platform fact this checker encodes (measured on the live deployment, round 55): GitBook renders
the SUMMARY.md link text as BOTH <title> and the visible <h1>, and drops the markdown H1 of the
body entirely. Evidence: docs/19-labs/lab4-multi-agent.md is authored as
「# Lab 4：三角色协作（Planner / Executor / Reviewer）」 while the published page read
<title>Lab 4 三角色协作</title> / <h1>Lab 4 三角色协作</h1> — verbatim the SUMMARY label of the
time — and the parenthetical appeared nowhere in the served HTML. So the sidebar label is not
just navigation text: it is the page's heading.

Therefore any label that is not the page's H1 silently becomes the reader-visible title. Chapter landing pages published <h1>本章导读</h1> and the
homepage published <h1>首页</h1> for exactly this reason.

Rule: norm(SUMMARY label) == norm(body H1). norm() collapses punctuation, which is a defensive
allowance — measured on the live site the label is published verbatim, colons and brackets
included. Fixes go on the SUMMARY side (labels carry the full title); nothing is deleted.

Usage:  python tools/checks/check_nav_h1_sync.py [--report]
"""
import os
import re
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOCS = os.path.join(REPO, "docs")
SUMMARY = os.path.join(DOCS, "SUMMARY.md")

ENTRY = re.compile(r"^\s*\*\s*\[([^\]]+)\]\(([^)\s]+)\)\s*$")
H1 = re.compile(r"^#\s+(.+?)\s*$", re.M)


def norm(s):
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", s or "").strip().lower()


def entries():
    out = []
    for line in open(SUMMARY, encoding="utf-8").read().split("\n"):
        m = ENTRY.match(line)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def h1_of(path):
    text = open(path, encoding="utf-8").read()
    m = H1.search(text)
    return m.group(1).strip() if m else ""


def audit():
    """Return (rows, problems) where rows = [(rel, label, h1)] for every registered page."""
    rows, problems = [], []
    seen = set()
    for label, rel in entries():
        path = os.path.join(DOCS, rel.replace("/", os.sep))
        if rel in seen:
            problems.append("DUP entry for %s" % rel)
        seen.add(rel)
        if not os.path.isfile(path):
            problems.append("MISSING %s referenced by SUMMARY" % rel)
            continue
        h1 = h1_of(path)
        rows.append((rel, label, h1))
        if not h1:
            problems.append("NOH1 %s has no markdown H1" % rel)
        elif norm(h1) != norm(label):
            problems.append("TITLE %s nav=%r h1=%r" % (rel, label, h1))
    problems += duplicate_titles(rows)
    known = {os.path.relpath(os.path.join(dp, fn), DOCS).replace("\\", "/")
             for dp, _, fns in os.walk(DOCS) for fn in fns if fn.endswith(".md")}
    known -= {"SUMMARY.md", "asset-MANIFEST.md"}
    for rel in sorted(known - seen):
        if os.path.basename(rel) == "MANIFEST.md":
            continue
        problems.append("ORPHAN %s is not registered in SUMMARY" % rel)
    return rows, problems


def duplicate_titles(rows):
    """Two pages must not publish the same title.

    Because the label *is* the published <title>/<h1>, a repeated label means the sidebar, the
    browser tab, site search results and llms.txt all show the same words for two different
    pages — a reader cannot tell a framework chapter from the resource entry it points to. This
    axis is invisible to the label-vs-H1 compare above, which only ever looks at one page at a
    time. Fix by qualifying both titles, never by deleting a page.
    """
    by_label = {}
    for rel, label, _ in rows:
        by_label.setdefault(norm(label), []).append(rel)
    out = []
    for key, rels in sorted(by_label.items()):
        if len(rels) > 1:
            out.append("SAMETITLE %s" % " == ".join(rels))
    return out


def run_controls(rows, problems):
    """The ruler must not be silently vacuous: hit control + phantom control."""
    assert len(rows) >= 190, "vacuity: only %d SUMMARY entries parsed" % len(rows)
    assert any(r[0] == "README.md" for r in rows), \
        "control: homepage entry not parsed, so the label/H1 compare is unreachable"
    # hit control: a punctuation-only difference must not read as a divergence (defensive slack).
    assert norm("Lab 4：三角色协作（Planner / Executor / Reviewer）") == \
        norm("Lab 4 三角色协作 Planner Executor Reviewer"), \
        "control: normaliser rejects a punctuation-only difference"
    # phantom control: a genuinely different title must still read as a divergence.
    assert norm("本章导读") != norm("06 记忆与 RAG") != norm("完全不同的标题"), \
        "control: normaliser equates two different titles (ruler too loose)"
    # duplicate-title axis: hit control (a real repeat must surface) + phantom (qualifiers clear it)
    hits = duplicate_titles([("09-frameworks/langchain.md", "LangChain", "LangChain"),
                             ("13-resources/projects/langchain.md", "LangChain", "LangChain"),
                             ("09-frameworks/x.md", "LangChain：框架用法与选型", "h"),
                             ("13-resources/projects/x.md", "LangChain：项目档案与点评", "h")])
    assert hits == ["SAMETITLE 09-frameworks/langchain.md == 13-resources/projects/langchain.md"], \
        "control: duplicate-title axis does not work: %s" % hits
    assert not duplicate_titles([("a.md", "LangChain：框架用法与选型", "h"),
                                 ("b.md", "LangGraph：框架用法与选型", "h")]), \
        "control: distinct titles reported as duplicates"
    diverged = [p for p in problems if p.startswith("TITLE")]
    same = [p for p in problems if p.startswith("SAMETITLE")]
    print("controls: entries=%d TITLE-findings=%d SAMETITLE-findings=%d, punctuation-only difference accepted / "
          "different title rejected / repeated title caught"
          % (len(rows), len(diverged), len(same)))


def main():
    rows, problems = audit()
    run_controls(rows, problems)
    print("SUMMARY labels audited against page H1: %d pages" % len(rows))
    for p in problems:
        print("  -", p)
    print("problems=%d" % len(problems))
    return 1 if problems and "--report" not in sys.argv else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
