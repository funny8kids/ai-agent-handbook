# -*- coding: utf-8 -*-
"""Quote-fidelity check: when a page (usually the changelog) says something 写着/标题/图注 「...」,
the quoted text must appear VERBATIM in something the reader actually gets.

Motivation: this round's log quoted two things it had not re-checked against the source — a
figure caption and a paraphrase put inside quotation marks. Both read as factual citations,
and one of them caused a false "the live page lost this content" alarm when a probe marker
built from it came back 0.

Scope rule: the changelog is allowed to reproduce wording it is *criticising*, so it is
excluded from the source-of-truth corpus; it is still scanned for attributed quotes.

WHAT COUNTS AS A SOURCE (round 71 widened this). The corpus used to be markdown prose outside
code fences, which silently made three whole families of honest citation unfalsifiable — and a
citation the ruler cannot look up is a citation the ruler reports as a defect:
  * text DRAWED in a hand-authored figure (`<text>` / `<tspan>` in `docs/.gitbook/assets/*.svg`).
    Half the log's citations are about figures; round 64 even had to invent a separate banner leg in
    `check_readme_stats.py` because a page count that lived only in a drawing went unread for nine
    rounds.
  * node labels inside ```mermaid fences. Fences are stripped for prose purposes (sample code is not
    a claim), but a mermaid body is a drawing written in another syntax.
  * a citation that joins several labels of one figure with a separator (`「拉财报 / 出报告」` for the
    two boxes labelled `4 拉财报` and `5 出报告`). The join is how a human points at a diagram, so each
    part must be present *in the same source*; splitting across two figures proves nothing.
Sample code fences (`python`, `bash`, ...) stay OUT of the corpus: a quote that only matches a code
snippet is not evidence the reader was told that in prose.

Retractions are the one case where "verbatim in the tree" is the wrong demand: when a round deletes
a false sentence from a page and quotes it in the log to record the deletion, no page can still
carry it. Round 62 shipped exactly that and the axis went red on a correct log line. Rather than
loosen the rule, such quotes are registered in RETRACTIONS below and judged by the *opposite*
assertion — the wording must be gone from every source. Round 71 made each entry two-sided: an entry
must also name the wording that REPLACED it and the file that carries it, so the registry cannot
quietly become a place to hide an unverified citation (the old control could only demand that README
still display the deleted sentence, which fits a billboard but not a figure label).

Usage:
    python tools/checks/check_quote_fidelity.py              # grade the tree
    python tools/checks/check_quote_fidelity.py --selftest   # planted sources through the same code
"""
import argparse
import io
import os
import re
import sys

DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs"))
LOG = os.path.join(DOCS, "00-index", "changelog.md")

QUOTE = r"[「“][^」”]{6,}[」”]"
VERB = r"(图注|图说|标题|原文|页里|页面里|写着|叫做|结语|引自|说的是|小标题|副标题|原句)"
ATTR = re.compile(VERB + r"\s*(" + QUOTE + r"+)")
ONE = re.compile(QUOTE)
# a citation of a diagram may join several drawn labels; each part must live in the same source
SPLIT = re.compile(r"[/／·、，,|]")
MIN_PART = 3

SVG_TEXT = re.compile(r"<(?:text|tspan)\b[^>]*>(.*?)</(?:text|tspan)>", re.S)
MER_STRUCT = re.compile(r"(-->|---|-\.-|\|\||subgraph|classDef|linkStyle|style\s|graph\s(TB|LR|TD|RL|BT)|flowchart\s+\w+|^\s*end\s*$)")
MER_CHARS = re.compile(r"[\[\](){}`>\"'<>|/\\]")

# wordings the log quotes ONLY to record that they were replaced: `old` must now be gone from every
# source, `new` must be findable in `source`, and `billboard` marks the one case where README keeps
# printing the false sentence on purpose (next to the verdict that says it is false).
RETRACTIONS = [
    {"old": "最宽 1116px，全部落在正文列宽（1120px）内，线上不会被缩放",
     "new": "正文列实测 **768px**",
     "source": "docs/README.md", "billboard": True, "round": 62,
     "why": "1120 是宽版布局的列宽，默认列宽实测 768"},
    {"old": "拉财报数据 / 生成报告",
     "new": "拉财报 / 出报告",
     "source": "docs/.gitbook/assets/07-plan-vs-react.svg", "billboard": False, "round": 65,
     "why": "15px 标签在 90px 格子里撑框，两步压短重排"},
    {"old": "从原理到生产：**187 页** / 19 章",
     "new": "从原理到生产 · 196 页 / 19 章",
     "source": "docs/.gitbook/assets/banner-home.svg", "billboard": False, "round": 64,
     "why": "横幅是图片，统计轴只读 Markdown，页数失真九轮"},
]

# strings this judge MUST keep finding, each in the source family named by its list
HIT_CONTROLS = [
    "命中率从 20% 提到 80%，成本曲线是断崖式的",
    "亮起来的一格就是模型当前能看到的全部",
]
# findable ONLY inside a drawn figure - a prose-only corpus misses these, so a green run here proves
# the figure branch is loaded and the same-source join rule works
HIT_FIGURE_CONTROLS = [
    "拉财报 / 出报告",
]
# findable ONLY inside a mermaid node label
HIT_MERMAID_CONTROLS = [
    "反向传播普及",
]
# wordings that only ever existed in a draft of the log (misquotes corrected out of it)
PHANTOM_CONTROLS = [
    "命中率 20%→80%，成本断崖式下降",
    "亮起来的那一格就是模型此刻能看到的全部",
    "这句话全站任何页面都不存在只为验证判据",
]
# parts that BOTH exist somewhere in the tree, but never together inside ONE source: the join rule
# must refuse these, otherwise "any two fragments anywhere" would pass as a citation
PHANTOM_JOIN_CONTROLS = [
    "亮起来的一格 / 反向传播普及",
    "拉财报 / 反向传播普及",
]


FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*(\S*)")


def split_fences(text):
    """One pass over the lines -> (prose, mermaid bodies, other fence bodies).

    A pair of independent regexes used to build these, and they disagreed: `prose_blob` deleted the
    mermaid fences first, which changed the parity of the remaining ``` markers, so the prose pass
    swallowed real prose between an odd pair of leftovers. That made a page-level citation read as
    absent (a false UNMATCHED) purely from how a neighbouring diagram happened to be fenced. Here a
    fence is opened and closed once, by the same hand, so the three buckets cannot see each other.
    """
    prose, mer, other, open_ = [], [], [], None
    for line in text.splitlines():
        m = FENCE.match(line)
        if m:
            marker, info = m.group(1), m.group(2).lower()
            if open_ is None:
                open_ = (marker[0], len(marker), info)
            elif marker[0] == open_[0] and len(marker) >= open_[1] and not info:
                # CommonMark: only a bare fence closes one. Reading the info string instead would
                # leave every ```mermaid unterminated, and the whole rest of the page would be
                # filed as diagram text — which is how a real page-level citation went missing.
                open_ = None
            continue
        bucket = mer if open_ and open_[2] == "mermaid" else (other if open_ else prose)
        bucket.append(line)
    return "\n".join(prose), "\n".join(mer), "\n".join(other)


def norm(t):
    return re.sub(r"\s+", "", re.sub(r"[`*_>|]", "", t))


def mermaid_blob(text):
    """Node labels of every mermaid block on a page, as drawn text (arrows/styles/brackets removed)."""
    return norm(MER_STRUCT.sub(" ", MER_CHARS.sub(" ", split_fences(text)[1])))


def prose_blob(text):
    """Everything readable as a claim: sample code and diagrams gone entirely."""
    return norm(split_fences(text)[0])


def read(path):
    return io.open(path, encoding="utf-8").read()


def sources():
    """path -> blob, for every page and figure a reader can actually get (changelog excluded).

    Returns the graded map plus the two families kept apart, because the controls have to prove each
    branch measures something the others cannot: `prose` is markdown outside every fence, `mer` is
    mermaid node labels only.
    """
    out, prose, mer, kinds = {}, {}, {}, {}
    for r, _d, fs in os.walk(DOCS):
        for f in fs:
            p = os.path.join(r, f)
            rel = os.path.relpath(p, DOCS).replace("\\", "/")
            if f.endswith(".md") and p != LOG:
                text = read(p)
                prose[rel] = p1 = prose_blob(text)
                mer[rel] = p2 = mermaid_blob(text)
                out[rel] = p1 + p2
                kinds[rel] = "md+mer" if p2 else "md"
            elif f.endswith(".svg"):
                blob = norm(MER_CHARS.sub(" ", " ".join(SVG_TEXT.findall(read(p)))))
                if blob:
                    out[rel] = blob
                    kinds[rel] = "figure"
    return out, prose, mer, kinds


def match(s, blob):
    """Verbatim, or a join whose every part is drawn inside this one source."""
    if not s:
        return False
    if s in blob:
        return True
    parts = [p for p in SPLIT.split(s) if len(p) >= MIN_PART]
    return len(parts) >= 2 and all(p in blob for p in parts)


def find(s, srcs):
    """Sources carrying this citation. `s` may be raw quoted text — blobs are normalised, so
    comparisons normalise the query too, and every control can be written the way a human reads it."""
    s = norm(s)
    return [p for p, blob in srcs.items() if match(s, blob)]


def grade(s, srcs, billboard="README.md"):
    """Verdict for one citation against a source map: PROSE / FIGURE / RETRACTED-OK /
    RETRACTION-NOT-APPLIED / UNMATCHED, plus the paths that decided it.

    A registered retraction is asked about FIRST: its whole point is that the wording is no longer
    in the tree, so letting an incidental find (a billboard page that still prints the false
    sentence) grade it as an ordinary citation would be the exemption eating the assertion.
    """
    reg = next((e for e in RETRACTIONS if norm(e["old"]) == s), None)
    if reg:
        src = norm_to_rel(reg["source"])
        if src not in srcs:
            return ("UNMATCHED", ["登记指向的文件不在语料里：%s" % reg["source"]])
        if not match(norm(reg["new"]), srcs[src]):
            return ("UNMATCHED", ["登记的替换句不在 %s 里：%r" % (src, reg["new"])])
        still = [p for p in find(s, srcs) if not (reg["billboard"] and p == billboard)]
        if still:
            return ("RETRACTION-NOT-APPLIED", still)
        return ("RETRACTED-OK", [src])
    hit = find(s, srcs)
    if not hit:
        return ("UNMATCHED", [])
    return ("FIGURE" if any(p.endswith(".svg") for p in hit) else "PROSE", hit)


def norm_to_rel(path):
    return os.path.relpath(os.path.join(os.path.dirname(DOCS), path), DOCS).replace("\\", "/")


def controls(srcs, prose, mer, kinds):
    """Every guard in this file has to be shown to bite on the real tree, not just to be present."""
    figs = [p for p in srcs if p.endswith(".svg")]
    assert len(figs) >= 30, "VACUITY: only %d figures indexed; the drawn-text branch measures nothing" % len(figs)
    assert sum(len(srcs[p]) for p in figs) >= 5000, "VACUITY: figure text is empty"
    n_mer = len([p for p, k in kinds.items() if k == "md+mer"])
    assert n_mer >= 150, "VACUITY: mermaid bodies indexed on only %d pages" % n_mer
    print("sources: %d pages (prose+mermaid, %d carrying diagrams) + %d authored figures with drawn text"
          % (len(srcs) - len(figs), n_mer, len(figs)))
    for s in HIT_CONTROLS:
        assert find(s, prose), "HIT CONTROL BROKEN (prose): %s" % s
    for s in HIT_FIGURE_CONTROLS:
        assert any(h.endswith(".svg") for h in find(s, srcs)), \
            "FIGURE CONTROL BROKEN: %s is not drawn in any svg" % s
        assert not find(s, prose) and not find(s, mer), (
            "FIGURE CONTROL NOT DIFFERENTIAL: %s is also in page text, so a green run here says"
            " nothing about the figure branch" % s)
    for s in HIT_MERMAID_CONTROLS:
        assert find(s, mer), "MERMAID CONTROL BROKEN: %s is not in any diagram body" % s
        assert not find(s, prose), (
            "MERMAID CONTROL NOT DIFFERENTIAL: %s is also in prose, so it proves nothing about the"
            " fence branch" % s)
    for s in PHANTOM_CONTROLS:
        assert not find(s, srcs), "PHANTOM CONTROL NOT PHANTOM: %s" % s
    for s in PHANTOM_JOIN_CONTROLS:
        assert not find(s, srcs), (
            "JOIN CONTROL NOT REFUSED: %s matched one source, so the same-source constraint is not"
            " enforced" % s)
    for e in RETRACTIONS:
        src = norm_to_rel(e["source"])
        assert src in srcs, "RETRACTION NAMES A MISSING SOURCE: %s" % e["source"]
        if e["billboard"]:
            assert match(norm(e["old"]), srcs[src]), (
                "BILLBOARD CONTROL BROKEN: %s no longer prints %r, so the exemption exempts nothing"
                % (e["source"], e["old"]))
        else:
            assert not find(norm(e["old"]), srcs), (
                "RETRACTION NOT APPLIED: %r is still findable in the tree" % e["old"])
        assert match(norm(e["new"]), srcs[src]), (
            "RETRACTION CONTROL BROKEN: %s does not carry the replacement %r" % (e["source"], e["new"]))
    print("controls ok (hit=%d figure=%d mermaid=%d phantom=%d join=%d retractions=%d)"
          % (len(HIT_CONTROLS), len(HIT_FIGURE_CONTROLS), len(HIT_MERMAID_CONTROLS),
             len(PHANTOM_CONTROLS), len(PHANTOM_JOIN_CONTROLS), len(RETRACTIONS)))


def selftest():
    """The branches a clean tree never visits, driven through the same grade()/find() code path.

    Round 70's lesson applied here: an exemption no real page triggers must still be shown to bite,
    or the registry is a place to hide unverified citations rather than a judgement.
    """
    e = RETRACTIONS[0]                      # the billboard entry: README prints the false line on
    old, new = norm(e["old"]), norm(e["new"])  # purpose, next to the verdict that says it is false
    # 1. the retracted wording survives in a knowledge page -> the opposite assertion must fire
    kind, detail = grade(old, {"README.md": new, "01-ai-basics/x.md": old})
    assert kind == "RETRACTION-NOT-APPLIED", "planted survival graded %s (%s)" % (kind, detail)
    # 2. the same citation once the wording really is deleted -> the two-sided branch, and it passes
    kind, detail = grade(old, {"README.md": new})
    assert kind == "RETRACTED-OK", "clean retraction graded %s (%s)" % (kind, detail)
    # 3. an entry whose replacement is NOT in the file it names buys no exemption
    kind, detail = grade(old, {"README.md": norm("这里只有别的话")})
    assert kind == "UNMATCHED", "an unverifiable retraction bought %s (%s)" % (kind, detail)
    # 4. an entry naming a file that no longer exists is a finding, not a skip
    kind, detail = grade(old, {})
    assert kind == "UNMATCHED", "a dangling retraction source bought %s (%s)" % (kind, detail)
    # 5. the join rule is per-source: two labels in one figure cite fine, one in each does not
    assert find(norm("拉财报 / 出报告"), {"a.svg": norm("4 拉财报 5 出报告")}), "same-figure join refused"
    assert not find(norm("拉财报 / 出报告"), {"a.svg": norm("4 拉财报"), "b.svg": norm("5 出报告")}), \
        "split citation matched across two different figures"
    # 6. fences stay out of the corpus from both sides: sample code proves nothing, a diagram does
    assert "只在代码里的句子" not in prose_blob("```python\ns = '只在代码里的句子'\n```"), \
        "sample code leaked into the prose corpus"
    assert find(norm("只在图里的句子"), {"p.md": mermaid_blob("```mermaid\nA[只在图里的句子]\n```")}), \
        "mermaid node label not indexed"
    # 9. the bug this round actually hit: a BARE ``` closes a ```mermaid block. Treating the closing
    #    line's (empty) info string as a new block left the diagram open and filed the rest of the
    #    page as drawn text — a real page-level citation graded UNMATCHED because its paragraph
    #    happened to sit under a diagram.
    page = "开头\n```mermaid\nA[只在图里的句子]\n```\n图后面的正文里的句子\n"
    assert "图后面的正文里的句子" in prose_blob(page), "prose under a diagram was swallowed by the fence state"
    assert "只在图里的句子" not in prose_blob(page), "diagram text leaked into the prose corpus"
    assert "只在图里的句子" in mermaid_blob(page), "a diagram after prose is not indexed"
    # an unclosed fence at EOF must not retroactively erase the prose above it either
    assert "开头" in prose_blob("开头\n```python\nx=1\n"), "prose before an unterminated fence vanished"
    print("selftest ok (10 plants graded through grade()/find()/prose_blob())")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="grade planted sources and exit")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        return selftest()

    srcs, prose, mer, kinds = sources()
    controls(srcs, prose, mer, kinds)

    files = [os.path.join(r, f) for r, _d, fs in os.walk(DOCS) for f in fs if f.endswith(".md")]
    checked = bad = 0
    tally = {}
    for p in files:
        rel = os.path.relpath(p, DOCS).replace("\\", "/")
        for i, line in enumerate(read(p).splitlines(), 1):
            for m in ATTR.finditer(line):
                for q in ONE.findall(m.group(2)):
                    s = norm(q.strip("「”“」"))
                    if len(s) < 6:
                        continue
                    checked += 1
                    kind, detail = grade(s, srcs)
                    tally[kind] = tally.get(kind, 0) + 1
                    if kind == "RETRACTION-NOT-APPLIED":
                        bad += 1
                        print("  RETRACTION-NOT-APPLIED %s:%d  「%s」 仍在 %s"
                              % (rel, i, s, detail[:3]))
                    elif kind == "UNMATCHED":
                        bad += 1
                        print("  UNMATCHED %s:%d  %s「%s」  %s" % (rel, i, m.group(1), q[:40], detail[:2]))
    print("content sources=%d  attributed quotes=%d  findings=%d  %s"
          % (len(srcs), checked, bad, tally))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
