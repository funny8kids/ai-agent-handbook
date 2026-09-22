"""Standing check: no traditional-form characters in reader-visible prose.

Why this axis exists (measured, round 56): two IME slips shipped to the live site —
`模型被騙着…` in 05-tool-protocol/tool-permission-sandbox.md and `能换來更强的能力面` in
08-multi-agent/README.md. Both sit in hint cards, i.e. the first line a reader scans on a page,
and a stray traditional character in a mainland-Chinese book reads as untended machine output.

The character set is not hand-written: it is OpenCC's authoritative TSCharacters table, filtered
to single-character keys whose simplified form differs (tools/checks/data/
fetch_traditional_chars.py). That filter is why the ruler has no false-positive class of
"characters written identically in both standards" — 台, 著, 里, 生 are simply not in the table.

Scope: fenced blocks and inline code are excluded (a captured CLI transcript or a quoted
upstream title may legitimately carry traditional forms). Prose, tables, headings, link text and
Mermaid labels are all judged.

Usage:  python tools/checks/check_char_sanity.py [--report]
"""
import io, os, re, sys
from collections import Counter

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOCS = os.path.join(REPO, "docs")
TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "traditional_chars.txt")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE = re.compile(r"`[^`\n]*`")
CJK = re.compile(r"[㐀-鿿]")


def load_table():
    trad = {}
    for ln in io.open(TABLE, encoding="utf-8").read().split("\n"):
        if not ln or ln.startswith("#"):
            continue
        ch, _, simp = ln.partition("\t")
        if ch:
            trad[ch] = simp.strip()
    return trad


def visible_prose(text):
    """Lines outside fenced blocks, with inline code removed — the reader-visible surface."""
    out, open_tok = [], None
    for line in text.replace("\r\n", "\n").split("\n"):
        m = FENCE.match(line)
        if m:
            tok = m.group(1)[0] * 3
            open_tok = None if open_tok else tok
            out.append("")
            continue
        out.append("" if open_tok else INLINE.sub("", line))
    return "\n".join(out)


def scan(text, trad):
    hits = Counter()
    for i, line in enumerate(visible_prose(text).split("\n"), 1):
        for ch in line:
            if ch in trad:
                hits[(ch, i)] += 1
    return hits


def run_controls(trad):
    """The ruler and its own data must be checked before the corpus is believed."""
    assert len(trad) >= 3000, "vacuity: traditional table only has %d entries" % len(trad)
    assert trad.get("騙") == "骗" and trad.get("來") == "来", \
        "control: the two characters this round actually fixed are not in the table"
    for same_form in ("台", "著", "里", "生"):
        assert same_form not in trad, \
            "control: %s is written the same in both standards and must not be flagged" % same_form
    sample = ("提示注入使「模型被騙着用合法权限做坏事」\n"
              "```\n围栏里的 說 应当被忽略\n```\n"
              "行内代码里的 `說` 同样不算\n"
              "协作能换來更强的能力面\n")
    got = scan(sample, trad)
    assert {(c, i) for c, i in got} == {("騙", 1), ("來", 6)}, \
        "control: expected exactly the two prose slips, got %s" % (dict(got),)
    assert "說" in trad, "control: the sample's fenced character is not traditional at all"
    assert scan("```\n說\n```\n`說` 普通文本里没有繁体\n", trad) == {}, \
        "control: fenced or inline-code text was judged"
    assert scan("权限最小化是最后防线，被骗着执行也不该发生", trad) == {}, \
        "control: the simplified forms must not be flagged"
    print("controls: table=%d entries, prose slip caught, fenced/inline-code ignored, "
          "simplified forms and same-form chars refused" % len(trad))


def main():
    trad = load_table()
    run_controls(trad)
    files, total_cjk, findings = 0, 0, []
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            text = io.open(path, encoding="utf-8").read()
            files += 1
            prose = visible_prose(text)
            total_cjk += len(CJK.findall(prose))
            for (ch, line_no), _ in sorted(scan(prose, trad).items()):
                line = prose.split("\n")[line_no - 1]
                k = line.index(ch)
                findings.append("%s:%d  %s → %s  …%s…"
                                % (rel, line_no, ch, trad[ch], line[max(0, k - 18):k + 18]))
    assert files >= 190, "vacuity: only %d pages scanned" % files
    assert total_cjk >= 200000, \
        "vacuity: only %d CJK chars reached the judge, the strip is eating real prose" % total_cjk
    print("pages=%d prose CJK chars=%d traditional-form findings=%d"
          % (files, total_cjk, len(findings)))
    for f in findings:
        print("  -", f)
    print("problems=%d" % len(findings))
    return 1 if findings and "--report" not in sys.argv else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
