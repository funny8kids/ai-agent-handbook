"""Quote-fidelity check: when the changelog (or any page) says a page 写着/图注/标题 「...」,
the quoted text must appear VERBATIM in some content page.

Motivation: this round's log quoted two things it had not re-checked against the source — a
figure caption and a paraphrase put inside quotation marks. Both read as factual citations,
and one of them caused a false "the live page lost this content" alarm when a probe marker
built from it came back 0.

Scope rule: the changelog is allowed to reproduce wording it is *criticising*, so it is
excluded from the source-of-truth corpus; it is still scanned for attributed quotes.

Whole-file ```...``` masking is deliberately NOT a regex: the changelog discusses fence
syntax inline, and a regex there silently swallowed real prose.
"""
import io, os, re, sys

DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs"))
LOG = os.path.join(DOCS, "00-index", "changelog.md")

QUOTE = r"[「“][^」”]{6,}[」”]"
VERB = r"(图注|图说|标题|原文|页里|页面里|写着|叫做|结语|引自|说的是|小标题|副标题|原句)"
ATTR = re.compile(VERB + r"\s*(" + QUOTE + r"+)")
ONE = re.compile(QUOTE)

# strings this judge MUST keep finding in content pages
HIT_CONTROLS = [
    "命中率从 20% 提到 80%，成本曲线是断崖式的",
    "亮起来的一格就是模型当前能看到的全部",
]
# wordings that only ever existed in a draft of the log (misquotes corrected out of it)
PHANTOM_CONTROLS = [
    "命中率 20%→80%，成本断崖式下降",
    "亮起来的那一格就是模型此刻能看到的全部",
    "这句话全站任何页面都不存在只为验证判据",
]


def strip_fences(text):
    keep, open_ = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            open_ = not open_
            continue
        if not open_:
            keep.append(line)
    return "\n".join(keep)


def norm(t):
    return re.sub(r"\s+", "", re.sub(r"[`*_>|]", "", strip_fences(t)))


def main():
    files = [os.path.join(r, f) for r, d, fs in os.walk(DOCS) for f in fs if f.endswith(".md")]
    content = {p: norm(io.open(p, encoding="utf-8").read()) for p in files if p != LOG}

    for s in HIT_CONTROLS:
        assert any(norm(s) in t for t in content.values()), "HIT CONTROL BROKEN: %s" % s
    for s in PHANTOM_CONTROLS:
        assert not any(norm(s) in t for t in content.values()), "PHANTOM CONTROL NOT PHANTOM: %s" % s
    print("controls ok (hit=%d, phantom=%d)" % (len(HIT_CONTROLS), len(PHANTOM_CONTROLS)))

    checked = bad = 0
    for p in files:
        rel = os.path.relpath(p, DOCS).replace("\\", "/")
        for i, line in enumerate(io.open(p, encoding="utf-8").read().splitlines(), 1):
            for m in ATTR.finditer(line):
                for q in ONE.findall(m.group(2)):
                    s = norm(q.strip("「”“」"))
                    if len(s) < 6:
                        continue
                    checked += 1
                    if not any(s in t for t in content.values()):
                        bad += 1
                        print("  UNMATCHED %s:%d  %s「%s」" % (rel, i, m.group(1), s))
    print("content pages=%d attributed quotes=%d unmatched=%d" % (len(content), checked, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
