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
from live_aria_manifest import (display_math_blocks, fence_blocks, fence_openings,  # noqa: E402
                                fence_prose_mask)  # one fence ruler, one math ruler

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


# A GFM table row carries exactly the header's number of cells. More than that and the renderer
# drops the extras — the reader silently loses a whole row's content — and the loss is invisible
# offline: the authored file still contains the text, so every offline grep-style guard reads it as
# present. Round 97 measured this on the live 术语速查 page: four rows had been glued two-and-two
# (`… || …`), each hiding its back term — 分组查询注意力/GQA, 稀疏检索/BM25, 令牌桶/Token Bucket and
# 基数树缓存/Radix Tree appeared 0 times in the served body and 1 time in the page's own `.md`, while
# the front terms appeared once. `check_prose_survival.py` caught it only because that page happened
# to be re-fetched; the class is authorable in one keystroke, so it is graded here, on the authored
# side, before push. Cells separated by an ESCAPED pipe (`prompt \| llm`, round 95) are one cell.
# Round 98's screenshot of the same page turned up the sibling class two lines below: rows with no
# header at all, which ship as a paragraph of literal pipes. Both legs live here, both read the same
# table map, and `table_orphans` is why that map had to know about display math too.
PIPE_CELL = re.compile(r"(?<!\\)\|")
TABLE_DELIM = re.compile(r"^\s{0,3}\|[\s:|-]*-[\s:|-]*\|?\s*$")
# A line that LOOKS like a table row: a pipe-flanked run with at least one cell between the pipes.
# Requiring the closing pipe is what keeps display math (`|C| \;\ge\; \theta` on its own line) out.
ROWISH = re.compile(r"^\s{0,3}\|.*\|\s*$")


def row_cells(line):
    """The cells GFM sees in a table row: split on unescaped pipes, leading/trailing pipe dropped."""
    parts = PIPE_CELL.split(line.strip())
    if parts and not parts[0].strip():
        parts = parts[1:]
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return [c.strip() for c in parts]


def find_tables(lines):
    """Locate every GFM table: (header index, cell count, first body row, one past last body row).

    GFM needs the header + delimiter pair; a pipe-flanked run without it is not a table to any
    renderer, so this is the one place that decides which lines are table lines.
    """
    tables, i = [], 0
    while i + 1 < len(lines):
        head, sep = lines[i].strip(), lines[i + 1].strip()
        if (head.startswith("|") and TABLE_DELIM.match(sep)
                and len(row_cells(sep)) == len(row_cells(head))):
            j = i + 2
            while (j < len(lines) and lines[j].strip().startswith("|")
                   and not TABLE_DELIM.match(lines[j].strip())):
                j += 1
            tables.append((i, len(row_cells(head)), i + 2, j))
            i = j
        else:
            i += 1
    return tables


def table_arity(rel, lines, problems):
    """Flag every row whose cell count differs from its own header's. Returns (tables, rows) graded."""
    tables = graded = 0
    for head, ncol, start, end in find_tables(lines):
        tables += 1
        for j in range(start, end):
            row = lines[j].strip()
            graded += 1
            if len(row_cells(row)) != ncol:
                problems.append(
                    "TBLARITY %s:body-line %d is a table row with %d cells under a %d-cell header — the "
                    "renderer drops the extras (the reader never sees that half of the row) or pads the "
                    "missing ones: %r" % (rel, j + 1, len(row_cells(row)), ncol, row[:70]))
    return tables, graded


def table_orphans(rel, lines, problems):
    """Flag pipe-shaped runs no header ever adopted: the reader gets literal `|` text, not a table.

    Round 98 found this by screenshotting the page rather than by grepping it. Two runs of glossary
    rows (5 and 9 lines) sat under a blank seam with no header of their own, so the whole block
    arrived as one paragraph of raw pipes — and the arity leg above could not see it, because it
    only walks rows *inside* a detected table. The block is in the file, the text is searchable, and
    every offline "is this term present" grep reads it as fine; only the render says otherwise.
    """
    owned = set()
    for head, ncol, start, end in find_tables(lines):
        owned.update(range(head, end))
    # A display formula is not a table no matter how many norm bars flank its lines: KaTeX takes
    # `$$ |a| \;\ll\; |b| $$` and the reader never sees a pipe. Same pairing rule as the formula
    # judge, imported rather than re-derived, so the two can never disagree about what is math.
    for a, b in display_math_blocks(lines)[1]:
        owned.update(range(a, b + 1))
    runs, k = [], 0
    while k < len(lines):
        if ROWISH.match(lines[k]) and k not in owned:
            m = k
            while m + 1 < len(lines) and ROWISH.match(lines[m + 1]) and (m + 1) not in owned:
                m += 1
            runs.append((k, m))
            k = m + 1
        else:
            k += 1
    for a, b in runs:
        problems.append(
            "TBLORPHAN %s:body-line %d starts %d pipe row(s) with no header + delimiter above them — "
            "no renderer treats this as a table, so the reader sees the pipes themselves: %r"
            % (rel, a + 1, b - a + 1, lines[a].strip()[:70]))
    return len(runs)


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


def scan(rel, text, counts=None):
    """Problems for one page. `rel` is docs-relative, forward slashes.

    `counts` (optional) collects (rel, tables, rows) so the caller can prove what this page was
    actually graded on — a coverage claim has to come off the same walk that produced the verdict.
    """
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
    tables, rows = table_arity(rel, body.split("\n"), problems)
    orphans = table_orphans(rel, body.split("\n"), problems)
    if counts is not None:
        counts.append((rel, tables, rows, orphans))
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
    # --- table arity: an off-arity row is content the reader never gets, and no offline grep sees it
    tbl = good + """
| 术语 | 英文 | 一句话解释 |
|---|---|---|
| 弃权与升级 | Abstain / Escalate | 置信度不足时不硬判 |
"""
    assert not any(p.startswith("TBLARITY") for p in scan("t.md", tbl)), \
        "control: a well-formed 3-cell table was flagged: %s" % scan("t.md", tbl)
    glued = tbl.replace("不硬判 |\n", "不硬判 || 分组查询注意力 | GQA / MQA | 多个 Q 头共享一份 K/V |\n")
    assert sum(1 for p in scan("t.md", glued) if p.startswith("TBLARITY")) == 1, \
        "control: two rows glued into one 6-cell row passed as a table: %s" % scan("t.md", glued)
    short = tbl.replace("不硬判 |\n", "不硬判 |\n| 只写两格 | Two cells\n")
    assert sum(1 for p in scan("t.md", short) if p.startswith("TBLARITY")) == 1, \
        "control: a 2-cell row under a 3-cell header passed as a table: %s" % scan("t.md", short)
    # an escaped pipe is ONE cell (round 95), so a row that naive splitting reads as 4 cells is clean
    escaped = good + """
| 记法 | 含义 | 例子 |
|---|---|---|
| $$\\|C\\|$$ | 范数 | prompt \\| llm |
"""
    assert not any(p.startswith("TBLARITY") for p in scan("t.md", escaped)), \
        "control: an escaped pipe was counted as a cell boundary: %s" % scan("t.md", escaped)
    # and a line that merely STARTS with a pipe is not a row unless a delimiter row follows it —
    # the display formula `|C| \\ge \\theta T_max` in memory-compression-forgetting.md is math
    mathish = good + "\n$$\n|C| \\;\\ge\\; \\theta\\,T_{\\max}\n$$\n"
    assert not any(p.startswith("TBLARITY") for p in scan("t.md", mathish)), \
        "control: a display-math line was graded as a table row: %s" % scan("t.md", mathish)
    assert not any(p.startswith("TBLORPHAN") for p in scan("t.md", mathish)), \
        "control: display math was flagged as an orphan table run: %s" % scan("t.md", mathish)
    # The sibling class round 98 found by screenshotting instead of grepping: pipe rows with no
    # header of their own. Same authored text, same searchable terms, and the reader gets raw pipes.
    orphan = good + """
| 无头行 A | Headless A | 读者看到的是竖线本身 |
| 无头行 B | Headless B | 因为这段没有表头与分隔行 |
"""
    hits = [p for p in scan("t.md", orphan) if p.startswith("TBLORPHAN")]
    assert len(hits) == 1, "control: a 2-row headerless run gave %d findings, expected 1 (one per run)" \
                           % len(hits)
    headed = orphan.replace("| 无头行 A |", "| 术语 | 英文 | 一句话解释 |\n|---|---|---|\n| 无头行 A |")
    assert not any(p.startswith("TBLORPHAN") for p in scan("t.md", headed)), \
        "control: the same run with a header was still orphan-flagged: %s" % scan("t.md", headed)
    # The judge's own false positive, found on its first full-corpus run: a display formula whose
    # line both opens and closes on a norm bar (`|ctx| ≪ |task|`, supervisor-pattern.md) is pipe-
    # shaped but is math, and the reader gets KaTeX. It must not be convicted.
    normbar = good + "\n$$\n|\\text{a}|\\;\\ll\\;|\\text{b}|\n$$\n"
    assert not any(p.startswith("TBLORPHAN") for p in scan("t.md", normbar)), \
        "control: a display formula flanked by norm bars was flagged as an orphan table: %s" \
        % scan("t.md", normbar)
    sp = os.path.join(DOCS, "08-multi-agent", "supervisor-pattern.md")
    if os.path.isfile(sp):
        with open(sp, "rb") as fh:
            sptext = fh.read().decode("utf-8")
        assert not any(p.startswith("TBLORPHAN") for p in scan("08-multi-agent/supervisor-pattern.md",
                                                               sptext)), \
            "supervisor-pattern's display formulas are being graded as orphan tables: %s" % [
                p for p in scan("08-multi-agent/supervisor-pattern.md", sptext)
                if p.startswith("TBLORPHAN")]
    # The exemption must not be a blanket: on the same page that carries the exempt formula, a real
    # headerless run further down still has to be convicted.
    both = normbar + "\n| 无头行 A | Headless A | 豁免不是免罪符 |\n" \
                     "| 无头行 B | Headless B | 同页的真空段仍要判 |\n"
    assert sum(1 for p in scan("t.md", both) if p.startswith("TBLORPHAN")) == 1, \
        "control: exempting display math also exempted the orphan run on the same page"
    # the shipped page that had the defect: clean now, and the grader demonstrably reads its rows
    gl = os.path.join(DOCS, "21-glossary", "README.md")
    if os.path.isfile(gl):
        with open(gl, "rb") as fh:
            gltext = fh.read().decode("utf-8")
        counts = []
        assert not any(p.startswith("TBLARITY") for p in scan("21-glossary/README.md", gltext, counts)), \
            "the shipped glossary table still has an off-arity row: %s" % [p for p in
                                                                           scan("21-glossary/README.md", gltext)
                                                                           if p.startswith("TBLARITY")]
        assert not any(p.startswith("TBLORPHAN") for p in scan("21-glossary/README.md", gltext)), \
            "the shipped glossary still carries a headerless pipe run the reader sees as text"
        assert counts and counts[0][1] >= 8 and counts[0][2] >= 100, \
            "vacuity: the glossary page graded %s tables/rows, so 'clean' is not coverage" % (counts,)
        # Glue two adjacent shipped rows back together and require the finding. Which two rows is
        # derived from the file (the first two equal-arity data rows it holds), not typed: a
        # hand-copied literal is a second record of the same fact and it drifts.
        gl_lines = gltext.replace("\r\n", "\n").split("\n")
        k = next(i for i in range(len(gl_lines) - 1)
                 if gl_lines[i].startswith("| ") and gl_lines[i + 1].startswith("| ")
                 and not TABLE_DELIM.match(gl_lines[i]) and not TABLE_DELIM.match(gl_lines[i + 1])
                 and len(row_cells(gl_lines[i])) == len(row_cells(gl_lines[i + 1])))
        reglued = "\n".join(gl_lines[:k] + [gl_lines[k] + " || " + gl_lines[k + 1][1:]]
                            + gl_lines[k + 2:])
        hits = [p for p in scan("21-glossary/README.md", reglued) if p.startswith("TBLARITY")]
        assert len(hits) == 1, \
            "control: re-gluing the shipped row gave %d findings, expected exactly 1" % len(hits)
        # And the orphan class on the shipped artifact: strip one table's header + delimiter and
        # require the finding, on the same rows the reader now gets as a table.
        h = next(i for i in range(len(gl_lines) - 1)
                 if gl_lines[i].strip() == "| 术语 | 英文 | 一句话解释 |"
                 and TABLE_DELIM.match(gl_lines[i + 1].strip())
                 and gl_lines[i + 2].startswith("| ") and gl_lines[i + 3].startswith("| "))
        beheaded = "\n".join(gl_lines[:h] + gl_lines[h + 2:])
        hits = [p for p in scan("21-glossary/README.md", beheaded) if p.startswith("TBLORPHAN")]
        assert len(hits) == 1, \
            "control: deleting a shipped table header gave %d orphan findings, expected exactly 1" \
            % len(hits)
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
    counts = []
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            with open(path, "rb") as fh:
                problems += scan(rel, fh.read().decode("utf-8"), counts)
            n += 1
    assert n >= 190, "vacuity: only %d markdown pages were scanned" % n
    # The arity verdict only means something if tables were actually walked: a parser that matches no
    # header/delimiter pair reports "0 off-arity rows" and looks identical to a clean book.
    graded_tables = sum(c[1] for c in counts)
    graded_rows = sum(c[2] for c in counts)
    assert graded_tables >= 200 and graded_rows >= 1500, \
        "vacuity: table arity graded %d tables / %d rows" % (graded_tables, graded_rows)
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
    print("pages scanned=%d tables graded=%d rows graded=%d orphan runs=%d problems=%d"
          % (n, graded_tables, graded_rows, sum(c[3] for c in counts), len(problems)))
    for p in problems[:40]:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
