"""Round 61 axis: prose that promises a source must hand the reader something to click.

A sentence like 「配置与任务集见官方发布页」 tells the reader to go check a number, then gives no
link — the promise is unfunded even when the same URL sits further down the page in 参考资料,
because the reader is standing in the middle of a paragraph, not at the bottom.

Deliberately narrow, because the obvious wider rule failed measurement. An earlier pass looked
for 'any statistic with no link in its line' and returned 247 lines over 71 pages; reading the
top of that list showed the judge conflated two classes — the book's own engineering rules of
thumb ('输入 token 常是输出的 10–50 倍', nothing to cite) and numbers attributed to somebody else.
Punishing class A would have produced link-spam, i.e. the ruler would have *caused* 灌水. What
remains is the deictic shape below: the sentence names an external document and says 'go see it'.

Exclusions, each with a reason:
  * docs/00-index/ — the changelog legitimately reproduces wording it is criticising.
  * frontmatter, fenced code and inline code — a quoted example of bad markup is not a promise.
  * lines that already carry a link or a bare <https://…> URL — funded, therefore fine.
  * table cells reading 「同上」 — they point at a 出处 column in the same table, not at nothing.

Controls: synthetic hits (one per pattern) + non-hits (常见基准, 错误原文回填, a linked pointer, a
pointer inside inline code), then a real-page mutation control over six shipped pages asserting
the reading moves 0 -> 1 -> 0. Both matter: the first two false cleans in this project's history
came from planting the counterexample where the judge cannot see it (end of file = the excluded
相关知识点 section; line 2 = frontmatter), so the plant goes under the page's first H1.
"""
import io
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOCS = os.path.join(ROOT, "docs")

SKIP_PATH_HINTS = (os.path.join("00-index",), os.path.join(".gitbook", ""), "SUMMARY.md")
LINK = re.compile(r"\[[^\]]*\]\([^)]+\)|<https?://")
SAME_TABLE = re.compile(r"^\|.*同上\s*\|?\s*$")
# A finding needs BOTH halves of the promise: a 'go look' verb AND an external-document noun within
# the same short clause. Each half on its own lit up a real false-positive class in this book:
#   * verb alone — 「详见仓库」 inside a project card whose title already links that repo;
#   * noun alone — 「错误原文回填给模型」, 「常见事故源——文档」, where the words are ordinary nouns.
# So: 见 must not be the tail of 常见/看见/罕见…, the gap must not cross 、）」 (otherwise the
# section name 「参考资料」 reaches an unrelated 官方文档 a dozen characters later), and 文档 is
# deliberately absent from the noun list — it only counts as 官方文档, which 官方 already catches.
# An even earlier draft matched the bare 「页」 and lit up six intra-page navigations
# (「（见本页末尾）」) while adding no real defect.
VERB = r"(?:详见|参见|请见|出处见|链接见|参考|[^常看少未显只百隔本]见)"
NOUN = r"官方|发布页|条款|技术报告|论文|公告|SDK|guidelines|terms"
GAP = r"[^，。、；：！？」』\n]{0,10}?"
POINTER = re.compile(VERB + GAP + "(?:" + NOUN + ")|官方称")


def strip_markup(text):
    body = re.sub(r"^---.*?^---\s*", "", text, count=1, flags=re.S | re.M)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", body)


def scan_text(text):
    """Return (pointer_lines, findings) for one page's authored markdown."""
    hits, problems = 0, []
    for no, line in enumerate(strip_markup(text).splitlines(), 1):
        if not POINTER.search(line):
            continue
        hits += 1
        if LINK.search(line) or SAME_TABLE.match(line.strip()):
            continue
        problems.append("line %d: %s" % (no, line.strip()[:90]))
    return hits, problems


def walk_pages():
    for dirpath, _, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS)
        if any(h in rel_dir for h in (os.path.join("00-index",), ".gitbook")):
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "SUMMARY.md":
                continue
            path = os.path.join(dirpath, fn)
            yield (os.path.relpath(path, DOCS).replace(os.sep, "/"),
                   io.open(path, encoding="utf-8").read())


def run(quiet=False):
    pages, pointers, findings = 0, 0, []
    for rel, text in walk_pages():
        pages += 1
        n, bad = scan_text(text)
        pointers += n
        findings += ["%s %s" % (rel, b) for b in bad]
    assert pages >= 190, "vacuity: only %d pages scanned, the walk is broken" % pages
    if not quiet:
        print("source pointers: pages=%d pointer_lines=%d findings=%d"
              % (pages, pointers, len(findings)))
        for f in findings:
            print("  UNFUNDED " + f)
    return findings


def controls():
    hit_cases = ["- 该项在内部评估中报告为 0%（配置与任务集见官方发布页）",
                 "详见官方文档的 rate limits 一节",
                 "| 标准价 | $10 / $50 | 低于 Astra（见官方页） |",
                 "- 官方称较上一代省约 **47% 时间/任务**",
                 "参见发布公告里的评测设置"]
    clean_cases = ["## 常见基准",
                   "- 校验失败时把错误原文回填给模型，让它自己改",
                   "详见 [Astra 发布页](https://openai.com/index/gpt-6-astra/)",
                   "表格里的 95% 见 `官方发布页` 这个写法示例",
                   "| ARC-AGI-3 99.9% | 同上 |",
                   "价格低于上一代（见参考资料最后一条）",
                   "| 发布/更新时间 | 2025-08 创建；详见仓库 |",
                   "- 稠密向量是 1024 维（见本页末尾）",
                   "- 用检索到的原文核对事实，别信模型记忆",
                   "- 绝不能在 prompt 里写「只参考有权限的文档」。",
                   "2. 必须有「参考资料」小节（可含论文、官方文档、源码），没有则视为未完成。",
                   "只删主库是常见事故源——文档撤了，向量索引还在把它排进 top-3。"]
    for case in hit_cases:
        _, bad = scan_text("# T\n\n" + case + "\n")
        assert bad, "control: unfunded pointer not caught: %r" % case
    for case in clean_cases:
        _, bad = scan_text("# T\n\n" + case + "\n")
        assert not bad, "control: false positive on %r -> %s" % (case, bad)
    return len(hit_cases), len(clean_cases)


def real_page_mutation_control():
    """Plant an unfunded pointer in copies of shipped pages: 0 -> 1 -> 0 findings."""
    pages = [(rel, text) for rel, text in walk_pages()
             if not rel.startswith("14-templates")][:6]
    assert len(pages) == 6, "control: only %d shipped pages available" % len(pages)
    tmp = tempfile.mkdtemp(prefix="r61src-")
    try:
        base = []
        for rel, text in pages:
            _, bad = scan_text(text)
            base.append(len(bad))
        planted = []
        for rel, text in pages:
            lines = text.splitlines()
            for i, ln in enumerate(lines):
                if ln.startswith("# "):
                    lines.insert(i + 1, "\n- 该项在内部评估中报告为 0%（配置与任务集见官方发布页）")
                    break
            else:
                raise AssertionError("control: %s has no H1 to plant under" % rel)
            path = os.path.join(tmp, rel.replace("/", "__"))
            io.open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            _, bad = scan_text("\n".join(lines) + "\n")
            planted.append(len(bad))
        assert all(p == b + 1 for p, b in zip(planted, base)), \
            "control: plant did not add exactly one finding per page: %s vs %s" % (planted, base)
        after = []
        for rel, text in pages:
            _, bad = scan_text(text)
            after.append(len(bad))
        assert all(a == b for a, b in zip(after, base)), "control: un-planting lost the baseline"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return len(pages)


def main():
    n_hit, n_clean = controls()
    n_pages = real_page_mutation_control()
    print("controls ok (%d planted hits caught / %d look-alikes kept clean)" % (n_hit, n_clean))
    print("live mutation ok (0 -> 1 -> 0 findings on %d shipped pages)" % n_pages)
    findings = run()
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
