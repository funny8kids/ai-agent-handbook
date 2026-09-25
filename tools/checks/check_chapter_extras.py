# -*- coding: utf-8 -*-
"""Round 78 axis: the homepage promises 「每章「读完能做到」清单 + 章末自测 + 中英术语速查：
全量覆盖，题目可答、答案有出处」 -- and until now no judge in tools/checks could reproduce any of it.

Same defect class as round 76 (figure captions) and round 77 (widget inventory): a self-descriptive
statistic printed on the first screen with nothing behind it. Here the claim has three parts, so the
gate judges three things per numbered chapter:

  goal     a 「读完能做到」 list with >= MIN_GOAL bullets;
  quiz     a 「章末自测」 with >= MIN_QUESTIONS numbered questions, each one carrying a 出处 pointer
           (「见 some-page.md」 or a Markdown link) that resolves to a file in this repo;
  glossary a 「术语速查」 table with >= MIN_TERMS data rows, each row filling 英文 / 中文 / 白话.

「题目可答」 is what the pointer leg is for: a question that names no source is a question whose
answer the reader cannot go check, and a pointer to a file that does not exist is worse than none.

Run:  python tools/checks/check_chapter_extras.py            (offline readings + controls)
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(HERE, "..", "..", "docs"))

MIN_GOAL = 3
MIN_QUESTIONS = 3
MIN_TERMS = 10

GOAL_H = re.compile(r"^##\s+[^\n]*(?:读完能做到|学完这章)[^\n]*$", re.M)
QUIZ_H = re.compile(r"^##\s+[^\n]*(?:自测|检验|小测|测验)[^\n]*$", re.M)
TERM_H = re.compile(r"^##\s+[^\n]*术语[^\n]*$", re.M)
QUESTION = re.compile(r"^\s*\d+[.、)]\s+(.+)$", re.M)
# 「（提示：见 a.md、b.md）」 / 「见 [X](../y.md)」 / 「参见 official docs」 — the book's pointer shapes
POINTERS = re.compile(r"(?:见|参见|提示[^\n]{0,8}见|详见)\s*([^\n）)]+)")
FILE_MENTION = re.compile(r"([\w./-]+\.md)")
MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)")
CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN = re.compile(r"[A-Za-z]")
# A table cell may contain an escaped pipe (`\|` inside a code span like `prompt \| llm`), and GFM
# renders that as a literal bar. Splitting on every "|" invents columns that do not exist: measured
# on this tree, two honest rows in 09-frameworks and 19-labs read as BAD-ROW that way on the axis'
# first run -- the same class of false signal as round 57's bare `%` inside a tag attribute.
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def cells_of(row):
    return [c.strip().replace("\\|", "|") for c in CELL_SPLIT.split(row.strip().strip("|"))]

# Chapters that legitimately do not carry the triplet. The exemption is not a name on a list -- it is
# funded by a sentence the page itself carries, so it cannot be quietly widened to whatever chapter
# fails next: drop that sentence and the chapter goes red instead of exempt.
# 21-glossary says in its own body 「本章是纯查表页，不出自测题」 (round 78 found it while grading the
# quiz leg), and it IS the book-wide 术语速查, so a per-chapter table there would be the duplicated
# prose round 60 landed an axis against.
EXEMPT_QUIZ = {"21-glossary": "本章是纯查表页，不出自测题"}
EXEMPT_GLOSSARY = {"21-glossary": "the chapter *is* the global glossary; a per-chapter duplicate "
                                  "would re-add prose round 60 judges as duplication"}


def chapter_dirs():
    out = []
    for d in sorted(os.listdir(DOCS)):
        p = os.path.join(DOCS, d)
        if not os.path.isdir(p) or not re.match(r"^\d\d-", d):
            continue
        if d.startswith(("00-", "14-", "99-")):
            continue          # index, templates (deliberate broken examples), about
        out.append((d, p))
    return out


def section_of(text, match):
    m = match.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def resolve(ref, chapter_path):
    """Does this pointer name a file that exists in this repo? Relative to the chapter, to docs/, or by basename."""
    ref = ref.strip().strip("`*")
    if ref.startswith(("http://", "https://", "#", "mailto:")):
        return True
    cands = [os.path.join(chapter_path, ref), os.path.join(DOCS, ref),
             os.path.join(DOCS, ref.lstrip("/"))]
    if any(os.path.isfile(c) for c in cands):
        return True
    base = os.path.basename(ref)
    for dirpath, _, files in os.walk(DOCS):
        if base in files:
            return True
    return False


def judge_chapter(name, path):
    """Find the chapter's own README (where the triplet lives) and grade it."""
    readme = os.path.join(path, "README.md")
    if not os.path.isfile(readme):
        return ["NO-README %s/README.md missing: the triplet cannot be graded" % name], {}
    text = io.open(readme, encoding="utf-8").read()
    findings = []
    tally = {}

    goal = section_of(text, GOAL_H)
    bullets = [l for l in goal.split("\n") if re.match(r"^\s*[-*]\s+\S", l)]
    tally["goal_bullets"] = len(bullets)
    if not goal:
        findings.append("MISSING-GOAL %s has no 「读完能做到」 section" % name)
    elif len(bullets) < MIN_GOAL:
        findings.append("THIN-GOAL %s lists %d items, bar is %d" % (name, len(bullets), MIN_GOAL))

    quiz = section_of(text, QUIZ_H)
    questions = QUESTION.findall(quiz)
    tally["questions"] = len(questions)
    sourced = 0
    if not quiz:
        evidence = EXEMPT_QUIZ.get(name)
        if evidence and evidence in text:
            tally["quiz_exempt"] = 1          # exempt, and the exemption is funded by the page's own words
        elif evidence:
            findings.append("EXEMPT-UNSUPPORTED %s is on the exemption list but its page no longer "
                            "says %r -- either restore the sentence or the chapter owes a 章末自测"
                            % (name, evidence))
        else:
            findings.append("MISSING-QUIZ %s has no 章末自测 section" % name)
    elif len(questions) < MIN_QUESTIONS:
        findings.append("FEW-QUESTIONS %s has %d, bar is %d" % (name, len(questions), MIN_QUESTIONS))
    for q in questions:
        refs = []
        for m in POINTERS.finditer(q):
            refs += FILE_MENTION.findall(m.group(1))
        refs += [t for _, t in MD_LINK.findall(q) if not t.startswith("#")]
        if not refs:
            findings.append("NO-SOURCE %s: a question names no 出处: %s" % (name, q[:48]))
            continue
        dead = [r for r in refs if not resolve(r, path)]
        if dead:
            findings.append("DEAD-SOURCE %s: pointer(s) resolve to no file: %s | %s"
                            % (name, ", ".join(sorted(set(dead))[:3]), q[:40]))
        else:
            sourced += 1
    tally["questions_with_source"] = sourced

    gloss = section_of(text, TERM_H)
    rows = [l for l in gloss.split("\n") if l.strip().startswith("|")]
    data = [r for r in rows if not re.match(r"^\s*\|[\s:|-]+\|\s*$", r)]
    tally["terms"] = max(0, len(data) - (1 if data and re.match(r"^\s*\|\s*英文", data[0]) else 0))
    if name in EXEMPT_GLOSSARY:
        tally["glossary_exempt"] = 1
    elif not gloss:
        findings.append("MISSING-GLOSSARY %s has no 术语速查 section" % name)
    elif len(data) < MIN_TERMS:
        findings.append("THIN-GLOSSARY %s has %d rows, bar is %d" % (name, len(data), MIN_TERMS))
    for r in data[1:]:
        cells = cells_of(r)
        if len(cells) < 3 or not cells[0] or not cells[1] or not cells[2]:
            findings.append("BAD-ROW %s: a term row has an empty cell: %s" % (name, r[:60]))
        elif not LATIN.search(cells[0]) or not CJK.search(cells[1]) or not CJK.search(cells[2]):
            findings.append("BAD-ROW %s: 英文/中文/白话 columns out of shape: %s" % (name, r[:60]))
    return findings, tally


def run():
    findings = []
    totals = dict(goals=0, quizzes=0, quiz_exempt=0, questions=0, sourced=0, glossaries=0,
                  terms=0, chapters=0)
    for name, path in chapter_dirs():
        f, t = judge_chapter(name, path)
        findings += f
        totals["chapters"] += 1
        totals["goals"] += 1 if t.get("goal_bullets", 0) >= MIN_GOAL else 0
        totals["quiz_exempt"] += 1 if t.get("quiz_exempt") else 0
        totals["quizzes"] += 1 if t.get("questions", 0) >= MIN_QUESTIONS else 0
        totals["questions"] += t.get("questions", 0)
        totals["sourced"] += t.get("questions_with_source", 0)
        totals["glossaries"] += 1 if (t.get("terms", 0) >= MIN_TERMS or name in EXEMPT_GLOSSARY) else 0
        totals["terms"] += t.get("terms", 0)
    print("chapter extras: chapters=%d goals=%d quizzes=%d quiz_exempt=%d questions=%d "
          "with_source=%d glossaries=%d terms=%d findings=%d"
          % (totals["chapters"], totals["goals"], totals["quizzes"], totals["quiz_exempt"],
             totals["questions"], totals["sourced"], totals["glossaries"], totals["terms"],
             len(findings)))
    for f in findings:
        print("  " + f)
    return totals, findings


# --------------------------------------------------------------------------- controls
def _write(tmp, name, body):
    d = os.path.join(tmp, name)
    os.makedirs(d, exist_ok=True)
    io.open(os.path.join(d, "README.md"), "w", encoding="utf-8").write(body)
    io.open(os.path.join(d, "target.md"), "w", encoding="utf-8").write("# 目标页\n")
    return d


GOOD = """# 章导读

## 读完能做到

- 说清 A
- 说清 B
- 说清 C

## 章末自测

1. **回忆**：A 是什么？（提示：见 target.md）
2. **应用**：B 怎么用？见 [目标页](target.md)
3. **判断**：C 错在哪？（提示：见 target.md）

## 本章术语速查

| 英文术语 | 中文 | 白话一句话 |
|---|---|---|
""" + "\n".join("| Term %d | 术语%d | 一句白话解释%d |" % (i, i, i) for i in range(1, 13)) + "\n"


def controls():
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="r78ctrl")
    n = 0
    try:
        # positive control: a well-formed chapter must read clean
        d = _write(tmp, "98-good", GOOD)
        f, t = judge_chapter("98-good", d)
        assert not f, "control: a correct chapter was flagged: %s" % f
        assert t["questions_with_source"] == 3 and t["terms"] == 12, t
        n += 2

        # each defect must fire, one at a time, on the same skeleton
        def fires(mutated, tag):
            dd = _write(os.path.join(tmp, "x" + tag), "97-" + tag, mutated)
            got, _ = judge_chapter("97-" + tag, dd)
            assert got, "control blind: %s produced no finding" % tag
            return got

        fires(GOOD.replace("## 章末自测\n", ""), "noquiz")
        fires(GOOD.replace("3. **判断**：C 错在哪？（提示：见 target.md）\n", ""), "fewq")
        fires(GOOD.replace("（提示：见 target.md）", ""), "nosource")
        fires(GOOD.replace("target.md", "no-such-page.md"), "deadsource")
        fires(GOOD.replace("## 读完能做到\n\n- 说清 A\n- 说清 B\n- 说清 C\n", "## 读完能做到\n\n- 只有一个\n"),
              "thingoal")
        fires(GOOD.replace("| Term 12 | 术语12 | 一句白话解释12 |", "| Term 12 | 术语12 |  |"), "emptycell")
        fires(GOOD.replace("| Term 11 | 术语11 |", "| 没有拉丁 | 术语11 |"), "badshape")
        n += 7

        # an exemption must be earned by the page's own sentence, in both directions. Cut the QUIZ
        # section here (not the glossary one -- an earlier version of this control cut the wrong one
        # and "failed" while the judge was reading correctly).
        noquiz = GOOD[:GOOD.index("## 章末自测")] + GOOD[GOOD.index("## 本章术语速查"):]
        with_claim = noquiz + "\n> 本章是纯查表页，不出自测题——取而代之，记住用它的三条路。\n"
        d1 = _write(os.path.join(tmp, "y1"), "96-exempt", with_claim)
        got, t3 = judge_chapter("21-glossary", d1)
        assert not got and t3.get("quiz_exempt") == 1 and t3["questions"] == 0, \
            "control: a chapter carrying the exemption sentence was not exempted: %s %s" % (got, t3)
        d2 = _write(os.path.join(tmp, "y2"), "95-silent", noquiz)
        got2, _ = judge_chapter("21-glossary", d2)
        assert any("EXEMPT-UNSUPPORTED" in g for g in got2), \
            "control blind: exemption survived after its supporting sentence was deleted: %s" % got2
        n += 3

        # and the reverse: an escaped pipe inside a cell is ONE cell. The axis' first run flagged two
        # honest rows this way, so the fix has to be pinned or someone will "simplify" the splitter.
        esc = GOOD.replace("| Term 5 | 术语5 | 一句白话解释5 |",
                           "| Term 5 | 术语5 | 管道写法 `prompt \\| llm` 也是一行 |")
        de = _write(os.path.join(tmp, "z"), "95-esc", esc)
        got, t2 = judge_chapter("95-esc", de)
        assert not got, "control: an escaped pipe split one cell into two: %s" % got
        assert t2["terms"] == 12, t2
        n += 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return n


def main():
    totals, findings = run()
    n = controls()
    print("controls ok (%d planted: clean chapter, 7 defects each caught, exemption both directions, "
          "2 escaped-pipe rows that must stay clean)" % n)
    # Non-vacuity: the homepage says 全量覆盖, so a green that comes from an empty sample is a lie.
    assert totals["chapters"] >= 18, "only %d chapters judged" % totals["chapters"]
    assert totals["questions"] >= 3 * totals["chapters"] - 3, "question count collapsed"
    assert totals["sourced"] == totals["questions"], ("questions without 出处: %d of %d"
                                                      % (totals["questions"] - totals["sourced"],
                                                         totals["questions"]))
    assert totals["terms"] >= 10 * totals["chapters"], "term rows collapsed: %d" % totals["terms"]
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
