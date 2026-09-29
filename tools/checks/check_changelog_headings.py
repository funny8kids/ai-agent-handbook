"""Fail if a round entry's `## ` heading disappears from the changelog, or the log stops reading newest-first.

Why this file exists: the round-59 commit deleted 第 58 次's heading. The entry's body survived, so
every content axis stayed green — 198 pages 0 problems — while a whole round published underneath
the *next* round's title, and 本页目录 lost an entry. Round 53 hit the same trap and the note it
left behind ("compare the heading set against HEAD every round") was a habit, and habits get
forgotten mid-round. This is that check, as code.

The invariant is deliberately not "round numbers are contiguous": the tree legitimately has holes
(36/39/41/43/45/46/49/50 have no entry). Only a heading that exists in HEAD and vanishes from the
working tree is a defect, so the judge reads HEAD through git rather than guessing at numbering.

Usage:
    python tools/checks/check_changelog_headings.py
"""
import io
import os
import re
import subprocess
import sys

from flag_guard import reject_unknown

FLAGS = ()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
FILE = os.path.join("docs", "00-index", "changelog.md")


def headings(text):
    return [l.rstrip() for l in text.split("\n") if l.startswith("## ")]


ROUND = re.compile(r"^#{1,6}.*?第\s*(\d+)\s*次")


def round_numbers(text):
    """[(line, round)] for headings that name a round, in document order.

    Only numbered headings participate: the file's oldest entries predate the round counter, and a
    judge that invented round numbers for them would report the history as scrambled forever.
    """
    out = []
    for n, line in enumerate(text.split("\n"), 1):
        m = ROUND.match(line.strip())
        if m:
            out.append((n, int(m.group(1))))
    return out


def misordered(text):
    """[(line, round, previous_round)] wherever the log stops reading newest-first.

    Two consumers depend on this order, and neither says so out loud. A reader scanning a changelog
    expects the newest work on top. And `check_prose_survival.published_cut()` will not date a page
    whose round headings are not strictly descending — it refuses to excuse text on a history it
    cannot trust — so one misrotated run made the whole 103-round page un-dateable, and round 112's
    six sentences, which had simply not reached the reader's HTML copy yet, were graded as six
    swallowed sentences that gate the exit code.
    """
    marks = round_numbers(text)
    return [(ln, r, marks[i - 1][1]) for i, (ln, r) in enumerate(marks)
            if i and r >= marks[i - 1][1]]


def lost(before, after):
    """Headings present in `before` but gone from `after`, order preserved.

    Accepts raw text or an already-extracted heading list: the first version of this helper took
    only lists, and a control that passed it text compared headings against a set of *characters*
    — so every heading read as lost and the control failed. A judge that can only be fed the right
    shape is a judge that will eventually be fed the wrong one.
    """
    seen = set(headings(after) if isinstance(after, str) else after)
    src = headings(before) if isinstance(before, str) else before
    return [h for h in src if h not in seen]


def controls():
    body = "\n".join(["## 2026-01-01（第 2 次）甲", "", "body 甲", "",
                      "## 2026-01-02（第 3 次）乙", "", "body 乙"])
    dropped = "\n".join(["## 2026-01-01（第 2 次）甲", "", "body 甲", "", "", "body 乙"])
    # The whole point: a deleted heading leaves a well-formed document, so only the set sees it.
    assert len(lost(body, dropped)) == 1, "control: a swallowed heading must be reported as one loss"
    assert not lost(body, body), "control: an unchanged file must read clean"
    assert len(lost(body, "\n".join(body.split("\n")[:4]))) == 1, \
        "control: a deleted trailing entry is a loss too"
    # A gap in numbering is NOT a loss — that is the false positive this judge must never emit.
    assert not lost("## 第 3 次\n## 第 7 次", "## 第 3 次\n## 第 7 次"), \
        "control: non-contiguous round numbers are legal history"
    # The order judge: one misrotated run must name itself, and legal history must stay quiet.
    scrambled = "\n".join(["## 2026-01-01（第 4 次）丁", "", "## 2026-01-01（第 3 次）丙", "",
                           "## 2026-01-01（第 5 次）戊", "", "## 2026-01-01（第 1 次）甲"])
    assert [r for _l, r, _p in misordered(scrambled)] == [5], \
        "control: the run that jumps above its predecessor must be reported: %s" % (
            misordered(scrambled),)
    assert [r for _l, r, _p in misordered("## 第 2 次\n## 第 5 次\n## 第 4 次\n## 第 6 次")] == [5, 6], \
        "control: two separate jumps must report both, not just the first"
    assert not misordered("## 2026-01-03（第 3 次）丙\n\n## 2026-01-02（第 2 次）甲"), \
        "control: a log that reads newest-first must stay quiet: %s" % (
            misordered("## 第 3 次\n## 第 2 次"),)
    assert not misordered("## 第 7 次\n## 第 3 次"), "control: a descending gap is legal history"
    assert len(round_numbers("## 2026-09-10\n\n正文")) == 0, \
        "control: an entry that predates the round counter has no round to order"
    print("controls ok (one lost heading caught / unchanged file clean / numbering gaps ignored"
          " / misrotated run named by round / descending and gap-free history quiet)")


def main():
    if reject_unknown(sys.argv[1:], FLAGS, "check_changelog_headings"):
        return 2
    controls()
    head = subprocess.run(["git", "show", "HEAD:%s" % FILE.replace(os.sep, "/")],
                          capture_output=True, cwd=REPO)
    if head.returncode != 0:
        print("changelog headings: SKIPPED — git could not read HEAD (%s)"
              % head.stderr.decode("utf-8", "replace").strip()[:160])
        return 2
    before = headings(head.stdout.decode("utf-8"))
    path = os.path.join(REPO, FILE)
    tree_text = io.open(path, encoding="utf-8").read()
    after = headings(tree_text)
    assert len(before) >= 40, \
        "vacuity floor: HEAD should carry dozens of round headings, read %d — the comparison is meaningless" % len(before)
    gone = lost(before, after)
    for h in gone[:10]:
        print("  HEADING LOST: %s" % h[:100])
    # Uncapped: a truncated disorder listing would hide exactly the inversions a future round needs,
    # and the count that gates the exit code is printed either way.
    bad = misordered(tree_text)
    for ln, r, prev in bad:
        print("  OUT OF ORDER: line %d is 第 %d 次 directly after 第 %d 次" % (ln, r, prev))
    print("changelog headings: HEAD=%d tree=%d lost=%d order inversions=%d"
          % (len(before), len(after), len(gone), len(bad)))
    return 1 if (gone or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
