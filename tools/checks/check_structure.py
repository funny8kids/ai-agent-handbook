"""Standing structure ruler for every markdown page: frontmatter, fence balance, exactly one H1.

Run this after any batch edit — the house rule is that mass file changes must pass a structure
check before committing. It was a disposable temp script through round 55, which meant the next
round had to re-write it (and re-make its mistakes).

Fence awareness is the whole point. The first pass of this check counted `# 启动服务` inside a
``` block as a second H1, and counted `{% stepper %}` quoted in the style guide as a broken
widget: 14 false problems on a clean tree. Fence *pairing* is still judged here, but widget
tag balance belongs to check_widget_pairing.py, which also understands inline code — a
fence-only strip does not, so re-deriving it here would add a second, looser ruler.

Usage:  python tools/checks/check_structure.py
"""
import os
import re
import sys

DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs"))
KEYS = ("tags", "type", "status", "updated")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^#\s+(.+?)\s*$", re.M)
HEAD = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", re.M)
# GitBook reprints heading text in the sidebar and the on-this-page list with inline-code
# formatting dropped, so a marker anywhere in a heading reaches the reader as bare markup even
# when the body copy renders it as code. Round 58 measured exactly that on the live changelog.
NAV_TOKENS = ("{%", "%}", "$$")
# GitBook's nav file and the asset manifest are real files but not published pages.
NOT_A_PAGE = ("SUMMARY.md", "MANIFEST.md")


def outside_fences(text):
    """Blank out fenced regions (and the fence lines themselves); report unbalanced tails."""
    out, tok = [], None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if m:
            t = m.group(1)[0] * 3
            if tok is None:
                tok = t
            elif t == tok:
                tok = None
            out.append("")
            continue
        out.append("" if tok else line)
    return "\n".join(out), (tok is None)


def scan(rel, text):
    """Problems for one page. `rel` is docs-relative, forward slashes."""
    text = text.replace("\r\n", "\n")  # core.autocrlf=true: the working tree is CRLF by design
    problems = []
    m = FM.match(text)
    if m:
        for k in KEYS:
            if not re.search(r"^%s:" % k, m.group(1), re.M):
                problems.append("FM %s missing key %s" % (rel, k))
    elif os.path.basename(rel) not in NOT_A_PAGE:
        problems.append("FM %s frontmatter missing/unclosed" % rel)
    body, balanced = outside_fences(text[m.end():] if m else text)
    if not balanced:
        return problems + ["FENCE %s unclosed" % rel]
    h1 = H1.findall(body)
    if len(h1) != 1:
        problems.append("H1 %s has %d fence-free H1 lines %r" % (rel, len(h1), h1[:3]))
    for h in HEAD.findall(body):
        hit = [t for t in NAV_TOKENS if t in h]
        if hit:
            problems.append("HEAD %s heading text carries %s — the TOC reprints headings without "
                            "code formatting, so the marker reads as bare markup: %r"
                            % (rel, "/".join(hit), h[:60]))
    return problems


def run_controls():
    good = """---
tags: [x]
type: knowledge
status: published
updated: 2026-09-23
---

# 真标题

```bash
# 启动服务
echo hi
```
"""
    assert scan("a.md", good) == [], "control: a fence-free page with an in-fence heading failed: %s" \
        % scan("a.md", good)
    assert any(p.startswith("H1") for p in scan("a.md", good + "\n# 第二个标题\n")), \
        "control: a second real H1 went uncounted"
    assert any("type" in p for p in scan("a.md", good.replace("type: knowledge\n", ""))), \
        "control: a missing frontmatter key went uncounted"
    assert any(p.startswith("FENCE") for p in scan("a.md", good + "\n```\n")), \
        "control: an unclosed fence went uncounted"
    assert any(p.startswith("HEAD") for p in scan("a.md", good + "\n### 写法 `$$x$$` 的坑\n")), \
        "control: a marker in heading text (even in inline code) prints bare in the TOC"
    assert not any(p.startswith("HEAD") for p in scan("a.md", good + "\n```\n### 写法 $$x$$\n```\n")), \
        "control: the same marker inside a fence is not a heading the TOC reprints"
    assert any("frontmatter" in p for p in scan("a.md", "# 无 frontmatter\n")), \
        "control: a page without frontmatter passed"
    assert scan("SUMMARY.md", "# Summary\n") == [], "control: SUMMARY.md held to the page rules"
    print("controls: in-fence heading ignored / real second H1, missing key, unclosed fence caught")


def main():
    if "-c" in sys.argv or "--controls" in sys.argv:
        run_controls()
        return 0
    run_controls()
    problems, n = [], 0
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            with open(path, "rb") as fh:
                problems += scan(rel, fh.read().decode("utf-8"))
            n += 1
    assert n >= 190, "vacuity: only %d markdown pages were scanned" % n
    print("pages scanned=%d problems=%d" % (n, len(problems)))
    for p in problems[:40]:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
