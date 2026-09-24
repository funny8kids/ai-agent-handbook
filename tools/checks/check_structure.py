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
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_aria_manifest import fence_blocks, fence_openings, fence_prose_mask  # noqa: E402  one fence ruler

DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs"))
KEYS = ("tags", "type", "status", "updated")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
# Round 54's operator directive: reader pages carry no executable code — where a reader would have to
# run something, the page gives a `{% stepper %}` / `{% tabs %}` walkthrough or a real JSON contract.
# Nothing in tools/checks enforced it until round 79, so the homepage's 「正文零可执行代码」 was a
# sentence no machine could falsify (the same class as rounds 57/76/77/78). The allowlist is the set
# the tree actually measures: mermaid 217, json 79, text 52, markdown 10, yaml 10, no-info 10.
DATA_FENCE_LANGS = frozenset(("mermaid", "json", "yaml", "text", "markdown", "jsonc", "json5", ""))
FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^#\s+(.+?)\s*$", re.M)
HEAD = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", re.M)
# GitBook reprints heading text in the sidebar and the on-this-page list with inline-code
# formatting dropped, so a marker anywhere in a heading reaches the reader as bare markup even
# when the body copy renders it as code. Round 58 measured exactly that on the live changelog.
NAV_TOKENS = ("{%", "%}", "$$")
# A backslash cannot escape a backtick *inside* a code span: the span closes at the first
# backtick and the delimiters it strands pair up as a formula. Round 59 measured that on the
# live changelog: `<code>` held "字面 \" , the two stranded $$ became an EMPTY KaTeX span, and
# the clause between them vanished from the reader-visible page — while 0 literal $$ stayed, so
# the live leak scan and the KaTeX count parity are both blind to it. Only this authored-side
# rule sees the class at all, which is why it belongs here rather than in a browser.
BACKTICK_ESC = re.compile(r"\\`")
# GitBook's nav file and the asset manifest are real files but not published pages.
NOT_A_PAGE = ("SUMMARY.md", "MANIFEST.md")


def outside_fences(text):
    """Blank fenced regions (and the fence lines), and report whether the tail left a fence open.

    The rules live in `live_aria_manifest.fence_prose_mask` on purpose: this file, that one and the
    formula/figure/prose-duplication judges all need the same fence map, and round 57 learned what
    two tokenizers do to a corpus — the same tree ends up with two defensible readings. The old
    local copy closed a fence on ANY same-character line, so a 4-backtick example containing ```
    blocks mis-mapped 13 lines on one template page (round 79).
    """
    lines = text.replace("\r\n", "\n").split("\n")
    mask, balanced = fence_prose_mask(text)
    return "\n".join(l if keep else "" for l, keep in zip(lines, mask)), balanced


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
    # The fence walk has to run on the page with frontmatter stripped too, or a template's own YAML
    # block counts as an opener; `text[m.end():]` is the same cut `body` was built from.
    for ln, lang, blk, closed in fence_blocks(text[m.end():] if m else text):
        if lang not in DATA_FENCE_LANGS:
            problems.append("CODEFENCE %s: body-line %d opens a fence tagged %r — reader pages carry "
                            "no executable code; use a stepper/tabs walkthrough or a json/yaml/text "
                            "contract instead" % (rel, ln, lang))
        if lang == "json":
            # The homepage promises every data contract 「每份都过 json.loads」. A contract with a
            # trailing comma is worse than no contract: the reader copies it into a request and gets
            # a parse error they cannot see coming, and the page looks like it taught them something.
            try:
                json.loads(blk)
            except ValueError as e:
                problems.append("JSONCONTRACT %s: the json block opened at body-line %d does not "
                                "parse: %s" % (rel, ln, str(e)[:90]))
    h1 = H1.findall(body)
    if len(h1) != 1:
        problems.append("H1 %s has %d fence-free H1 lines %r" % (rel, len(h1), h1[:3]))
    for h in HEAD.findall(body):
        hit = [t for t in NAV_TOKENS if t in h]
        if hit:
            problems.append("HEAD %s heading text carries %s — the TOC reprints headings without "
                            "code formatting, so the marker reads as bare markup: %r"
                            % (rel, "/".join(hit), h[:60]))
    for i, line in enumerate(body.split("\n"), 1):
        if BACKTICK_ESC.search(line):
            problems.append("BT %s:body-line %d uses an escaped backtick — inside a code span a "
                            "backslash cannot escape the delimiter, so the span closes early and "
                            "the delimiters it strands become an empty formula that swallows the "
                            "text between them: %r" % (rel, i, line.strip()[:60]))
    return problems


def run_controls():
    good = """---
tags: [x]
type: knowledge
status: published
updated: 2026-09-23
---

# 真标题

```text
# 启动服务
echo hi
```
"""
    assert scan("a.md", good) == [], "control: a fence-free page with an in-fence heading failed: %s" \
        % scan("a.md", good)
    # an executable fence must be caught wherever it sits, and the data languages must not be
    for lang in ("python", "bash", "js", "sql", "console"):
        bad = good.replace("```text", "```%s" % lang)
        assert any(p.startswith("CODEFENCE") for p in scan("a.md", bad)), \
            "control: an executable fence tagged %r passed the house rule" % lang
    for lang in ("text", "json", "yaml", "markdown", "mermaid", ""):
        ok = good.replace("```text", "```%s" % lang)
        assert not any(p.startswith("CODEFENCE") for p in scan("a.md", ok)), \
            "control: the data fence %r was rejected: %s" % (lang, scan("a.md", ok))
    # the fence walk itself: a 4-backtick example containing ``` blocks must NOT close early, or the
    # example's content is read as prose and the prose after it is read as fenced
    nested = good + "\n````markdown\n### 例\n```json\n{}\n```\n### 这段仍在示例里\n````\n\n## 真的正文标题\n"
    mask, balanced = fence_prose_mask(nested)
    lines = nested.split("\n")
    idx = lambda t: next(i for i, l in enumerate(lines) if l.strip() == t)
    assert balanced, "control: a properly nested fence pair read as unclosed"
    assert not mask[idx("### 这段仍在示例里")], \
        "control: a line inside a 4-backtick example was read as prose"
    assert mask[idx("## 真的正文标题")], \
        "control: prose after the example's real closer was read as fenced"
    assert [info for _n, info in fence_openings(nested)] == ["text", "markdown"], \
        "control: the nested ``` example inside the 4-backtick block counted as an opener: %s" \
        % fence_openings(nested)
    # Differential on a page that really ships: knowledge-template.md nests ``` examples inside a
    # ````markdown block. The pre-round-79 walker closes the outer block at the first inner fence, so
    # it mis-maps 13 lines; the platform was checked before believing either (the served markup wraps
    # those lines in `highlight-line` spans, i.e. GitBook agrees with CommonMark).
    def old_mask(text):
        mask, tok = [], None
        for line in text.split("\n"):
            m = FENCE.match(line)
            if m:
                t = m.group(1)[0] * 3
                if tok is None:
                    tok = t
                elif t == tok:
                    tok = None
                mask.append(False)
                continue
            mask.append(tok is None)
        return mask

    tpl = os.path.join(DOCS, "14-templates", "knowledge-template.md")
    if os.path.isfile(tpl):
        with open(tpl, "rb") as fh:
            ttext = fh.read().decode("utf-8").replace("\r\n", "\n")
        tlines = ttext.split("\n")
        om, nm = old_mask(ttext), fence_prose_mask(ttext)[0]
        d = [i for i, (a, b) in enumerate(zip(om, nm)) if a != b]
        assert d, "control: the two walkers agree on the shipped template, so this proves nothing"
        assert any("平方膨胀" in tlines[i] for i in d), \
            "control: the disagreeing lines are not the nested example: %r" % [tlines[i][:30] for i in d[:3]]
    probe = good + "\n````markdown\n```json\n{}\n```\n### 示例里的标题 `$$x$$`\n````\n"
    assert not any(p.startswith("HEAD") for p in scan("a.md", probe)), \
        "control: a heading that only exists inside a 4-backtick example was flagged as TOC markup"
    assert not fence_prose_mask(probe)[0][[i for i, l in enumerate(probe.split("\n"))
                                          if l.strip() == "{}"][0]], \
        "control: the nested example's own content read as prose under the fixed walker"
    real_heading = good + "\n### 正文里的标题 `$$x$$`\n"
    assert any(p.startswith("HEAD") for p in scan("a.md", real_heading)), \
        "control: the same line in plain prose must be flagged"
    assert any(p.startswith("H1") for p in scan("a.md", good + "\n# 第二个标题\n")), \
        "control: a second real H1 went uncounted"
    # a data contract that does not parse must be named, and a well-formed one must not be
    broken = good + '\n```json\n{"a": 1,}\n```\n'
    assert any(p.startswith("JSONCONTRACT") for p in scan("a.md", broken)), \
        "control: a json block with a trailing comma passed as a contract"
    assert not any(p.startswith("JSONCONTRACT")
                   for p in scan("a.md", good + '\n```json\n{"a": 1}\n```\n')), \
        "control: a valid json contract was rejected"
    # and the nested case again: a json example inside a 4-backtick template block is example text,
    # so it must NOT be held to the contract rule (the platform serves it as code the reader copies
    # at their own risk, and the older walker's early close would have read it as a live contract)
    assert not any(p.startswith("JSONCONTRACT") for p in scan("a.md", probe)), \
        "control: an example json block nested in a template was judged as a real contract"
    assert any("type" in p for p in scan("a.md", good.replace("type: knowledge\n", ""))), \
        "control: a missing frontmatter key went uncounted"
    assert any(p.startswith("FENCE") for p in scan("a.md", good + "\n```\n")), \
        "control: an unclosed fence went uncounted"
    assert any(p.startswith("HEAD") for p in scan("a.md", good + "\n### 写法 `$$x$$` 的坑\n")), \
        "control: a marker in heading text (even in inline code) prints bare in the TOC"
    assert not any(p.startswith("HEAD") for p in scan("a.md", good + "\n```\n### 写法 $$x$$\n```\n")), \
        "control: the same marker inside a fence is not a heading the TOC reprints"
    assert any(p.startswith("BT") for p in scan("a.md", good + "\n- 例：`写法 \\`x\\`` 的坑\n")), \
        "control: an escaped backtick closes the span early and strands the marker outside it"
    assert not any(p.startswith("BT") for p in scan("a.md", good + "\n```\n`写法 \\`x\\`` 的坑\n```\n")), \
        "control: the same escape inside a fence is example text, not markup"
    assert any("frontmatter" in p for p in scan("a.md", "# 无 frontmatter\n")), \
        "control: a page without frontmatter passed"
    assert scan("SUMMARY.md", "# Summary\n") == [], "control: SUMMARY.md held to the page rules"
    print("controls: in-fence heading ignored / real second H1, missing key, unclosed fence caught"
          " / TOC-reprinted marker and escaped backtick flagged, in-fence copies of both accepted"
          " / executable fences flagged in 5 languages and 6 data tags accepted"
          " / nested 4-backtick example walked without closing early")


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
    # The fence inventory is printed because the homepage quotes it: 「正文零可执行代码」 plus the
    # per-language counts. A number README quotes must be reproducible by the same run that greens.
    langs, contracts, unclosed = {}, 0, 0
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            with open(os.path.join(dirpath, fn), "rb") as fh:
                t = fh.read().decode("utf-8").replace("\r\n", "\n")
            fm = FM.match(t)
            for _ln, lang, _blk, closed in fence_blocks(t[fm.end():] if fm else t):
                langs[lang or "(no tag)"] = langs.get(lang or "(no tag)", 0) + 1
                unclosed += 0 if closed else 1
                contracts += 1 if lang == "json" else 0
    print("fences: %s | executable-tagged=%d json contracts parsed=%d unclosed=%d"
          % (" ".join("%s=%d" % kv for kv in sorted(langs.items(), key=lambda kv: -kv[1])),
             sum(v for k, v in langs.items() if k not in DATA_FENCE_LANGS and k != "(no tag)"),
             contracts, unclosed))
    print("pages scanned=%d problems=%d" % (n, len(problems)))
    for p in problems[:40]:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
