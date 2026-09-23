"""Fail if a round entry's `## ` heading disappears from the changelog.

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

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
FILE = os.path.join("docs", "00-index", "changelog.md")


def headings(text):
    return [l.rstrip() for l in text.split("\n") if l.startswith("## ")]


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
    print("controls ok (one lost heading caught / unchanged file clean / numbering gaps ignored)")


def main():
    controls()
    head = subprocess.run(["git", "show", "HEAD:%s" % FILE.replace(os.sep, "/")],
                          capture_output=True, cwd=REPO)
    if head.returncode != 0:
        print("changelog headings: SKIPPED — git could not read HEAD (%s)"
              % head.stderr.decode("utf-8", "replace").strip()[:160])
        return 2
    before = headings(head.stdout.decode("utf-8"))
    path = os.path.join(REPO, FILE)
    after = headings(io.open(path, encoding="utf-8").read())
    assert len(before) >= 40, \
        "vacuity floor: HEAD should carry dozens of round headings, read %d — the comparison is meaningless" % len(before)
    gone = lost(before, after)
    for h in gone[:10]:
        print("  HEADING LOST: %s" % h[:100])
    print("changelog headings: HEAD=%d tree=%d lost=%d" % (len(before), len(after), len(gone)))
    return 1 if gone else 0


if __name__ == "__main__":
    sys.exit(main())
