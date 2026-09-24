# -*- coding: utf-8 -*-
"""Judge that a page's advertised `updated:` date is the date its body last changed.

Why this file exists (round 75). The screenshot work needed a frontmatter date bump on nine pages,
and writing that by hand made one question unavoidable: `check_structure.py` checks that the key
EXISTS and parses, so a page can print any plausible date forever. Measured against git on this
tree: **17 reader pages advertise a `最后更新` that is 1-2 days older than the commit that changed
their body** -- every one of them a page this repo's own rounds edited without touching the key:
10 left by round 73's formula re-stack (99f6fc3), 1 by round 74's homepage edit (b10e40f), 6 more by
rounds 52/54/63. This class is not new: round 17 hand-backfilled 80 stale dates in the same field,
and six rounds later 17 more had accumulated -- which is exactly why the rule lives in a script now.
GitBook prints that field to the reader, so this is a reader-visible lie about the book, not a
metadata lint.

The rule is equality, in both directions:
  BEHIND    the body changed after the date the page prints -> the reader is told the page is older
            than it is. This is what the tree actually has.
  FORWARD   the page prints a date newer than its last body change -> the reader is told about an
            edit that never happened. Judged red for the same reason: it is the same field, and a
            one-way rule would let a round "refresh" the whole book by editing metadata.

The date-only-commit exemption is what makes the rule stable instead of self-feeding. Fixing a date
is itself a commit that touches the file; if the axis counted that as a change, the fix commit would
move `L` to its own date and the next round's --fix would chase it. So a commit counts only if it
changes a line other than the `updated:` key -- `body_commit_date()` implements that on `-U0` output.

Controls, planted rather than assumed (see `selftest()`): equal must pass, BEHIND and FORWARD must
each fire, a diff that only rewrites the date key must NOT move the last-body-change date while a
diff with one content line must, a missing key must be reported rather than skipped, the exemption
list must be a closed set (a renamed page cannot quietly join it), and an empty sample must die
rather than print a clean 198-page verdict.

Usage:
    python tools/checks/check_updated_dates.py            # verdict
    python tools/checks/check_updated_dates.py --fix      # write the measured date into each page
    python tools/checks/check_updated_dates.py --selftest
"""
import argparse
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")

DATE_RE = r"\d{4}-\d{2}-\d{2}"
UPDATED_LINE = re.compile(r"^updated: (%s)$" % DATE_RE)
KEY = re.compile(r"^updated: (%s)\s*$" % DATE_RE, re.M)
# Pages that are not reader pages: GitBook's navigation source, and the internal asset inventory
# that lives beside the images. Closed set on purpose -- see selftest's exemption control.
NOT_A_PAGE = {"docs/SUMMARY.md", "docs/.gitbook/assets/screenshots/MANIFEST.md"}
EXEMPT = set(NOT_A_PAGE)


def reader_pages():
    out = []
    for root, dirs, files in os.walk(DOCS):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for name in sorted(files):
            if name.endswith(".md"):
                out.append(os.path.relpath(os.path.join(root, name), REPO).replace("\\", "/"))
    return out


def declared(text):
    m = KEY.search(text)
    return m.group(1) if m else None


def body_commit_date(rel, log=None):
    """Date of the newest commit that changed something other than the `updated:` key.

    `log` is the raw `git log --date=short -U0` output for one file; passed in by the caller so the
    parser can be tested without touching git.
    """
    if log is None:
        p = subprocess.run(["git", "log", "--format=C\t%ad", "--date=short", "-U0", "--", rel],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8")
        if p.returncode != 0:
            return None
        log = p.stdout
    date, lines = None, []
    records = []
    for ln in log.split("\n"):
        if ln.startswith("C\t"):
            if date is not None:
                records.append((date, lines))
            date, lines = ln[2:].strip(), []
            continue
        if date is None:
            continue
        if ln.startswith("@@") or ln.startswith("diff ") or ln.startswith("index "):
            continue
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln[:1] in ("+", "-"):
            body = ln[1:]
            if not UPDATED_LINE.match(body.strip()):
                lines.append(body)
    if date is not None:
        records.append((date, lines))
    for date, lines in records:
        if lines:
            return date
    return None


def judge(rows, dirty=frozenset()):
    """rows: [(rel, declared or None, last body-change date or None)] -> problems, checked, pending.

    `dirty` is the set of paths git reports as modified. FORWARD is suppressed for those and counted
    as `pending` instead: this axis attests the date against COMMIT history, and a body change that
    is only in the working tree is not history yet -- judging it red would mean failing the very
    act of bumping a date in the round that earned it. BEHIND stays judged either way: an
    under-advertised date is not excused by uncommitted work.
    """
    problems, checked, pending = [], 0, []
    for rel, d, last in rows:
        if rel in EXEMPT:
            continue
        checked += 1
        if d is None:
            problems.append("NOKEY     %s: no parseable `updated:` key, so GitBook prints nothing "
                            "and this axis cannot read the page" % rel)
            continue
        if last is None:
            problems.append("NOCOMMIT  %s: no commit changes any line but the date key, so the "
                            "printed date has no evidence behind it" % rel)
            continue
        if d < last:
            problems.append("BEHIND    %s: body last changed %s but the page tells the reader %s"
                            % (rel, last, d))
        elif d > last:
            if rel in dirty:
                pending.append("%s: advertises %s, newer than HEAD's last body change %s"
                               % (rel, d, last))
                continue
            problems.append("FORWARD   %s: page advertises %s, newer than its last body change %s"
                            % (rel, d, last))
    return problems, checked, pending


def fix(rel, date):
    path = os.path.join(REPO, rel)
    lines = io.open(path, encoding="utf-8").read().split("\n")
    assert lines[0].strip() == "---", rel
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    at = [i for i in range(1, end) if lines[i].startswith("updated:")]
    assert len(at) == 1, "%s: %d updated keys" % (rel, len(at))
    lines[at[0]] = "updated: " + date
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))


def selftest():
    def case(rel, d, last):
        return judge([(rel, d, last)])[0]

    assert not case("docs/a.md", "2026-09-24", "2026-09-24"), "an equal date must read clean"
    assert case("docs/a.md", "2026-09-22", "2026-09-24")[0].startswith("BEHIND"), \
        "the tree's real defect must fire"
    assert case("docs/a.md", "2026-09-26", "2026-09-24")[0].startswith("FORWARD"), \
        "metadata-only refresh must not buy a newer date"
    assert case("docs/a.md", None, "2026-09-24")[0].startswith("NOKEY"), "missing key: report, skip"
    assert case("docs/a.md", "2026-09-24", None)[0].startswith("NOCOMMIT"), \
        "an unevidenced date must be a finding, not a pass"
    assert not judge([("docs/SUMMARY.md", "2000-01-01", "2026-09-24")])[0], \
        "the navigation source is not a reader page"
    assert judge([("docs/SUMMARY.md", "2000-01-01", "2026-09-24"),
                  ("docs/a.md", "2026-09-20", "2026-09-24")])[1] == 1, \
        "an exempt page must not be counted as checked"

    # the exemption that keeps --fix from chasing its own tail
    date_only = "\n".join([
        "C\t2026-09-25", "diff --git a/docs/a.md b/docs/a.md", "index 111..222 100644",
        "--- a/docs/a.md", "+++ b/docs/a.md", "@@ -5 +5 @@", "-updated: 2026-09-24",
        "+updated: 2026-09-25", ""])
    assert body_commit_date("docs/a.md", date_only) is None, \
        "a commit that only rewrites the date key must not count as a body change"
    body = date_only.replace("+updated: 2026-09-25", "+- 一条真实正文")
    assert body_commit_date("docs/a.md", body) == "2026-09-25", \
        "one content line must count"
    newest = ("C\t2026-09-26\ndiff\n--- a/docs/a.md\n+++ b/docs/a.md\n@@ -1 +1 @@\n"
              "-old body\n+new body\n") + date_only + body
    assert body_commit_date("docs/a.md", newest) == "2026-09-26", \
        "the newest body commit wins, records are newest-first"
    assert reader_pages() and judge([(p, "2026-09-24", "2026-09-24") for p in reader_pages()])[1] \
        >= 190, "the checked floor must be above 190 reader pages"
    unexempted = {p for p in reader_pages() if p not in EXEMPT}
    assert len(unexempted) >= 190, "too few reader pages walked: %d" % len(unexempted)
    for known in NOT_A_PAGE:
        assert any(known.endswith(os.path.basename(p)) for p in reader_pages()), \
            "exemption lists a page that no longer exists: %s" % known
    # a working-tree bump is not yet history: FORWARD waits for the commit, BEHIND has no excuse
    ps, _checked, pend = judge([("docs/a.md", "2026-09-24", "2026-09-23")], {"docs/a.md"})
    assert not ps and len(pend) == 1, "an uncommitted bump must be pending, not a finding: %s" % ps
    ps, _c, pend = judge([("docs/a.md", "2026-09-22", "2026-09-23")], {"docs/a.md"})
    assert ps and ps[0].startswith("BEHIND") and not pend, \
        "dirtiness must not excuse an under-advertised date: %s" % ps
    print("selftest: equal/BEHIND/FORWARD/NOKEY/NOCOMMIT + exemption + dirty-bump pending pair + "
          "date-only-commit exemption + newest-body-wins + tree floor, all as expected")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    pages = reader_pages()
    rows, unreadable = [], []
    for rel in pages:
        try:
            text = io.open(os.path.join(REPO, rel), encoding="utf-8").read()
        except Exception as exc:
            unreadable.append("%s (%s)" % (rel, exc))
            continue
        rows.append((rel, declared(text), body_commit_date(rel)))
    dirty = {l[3:].replace("\\", "/") for l in subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True,
        encoding="utf-8").stdout.splitlines() if l[:2].strip() and len(l) > 3}
    if args.fix:
        for rel, d, last in rows:
            # Only BEHIND is fixed by writing: rewinding a FORWARD date would delete a claim that is
            # usually just this round's own uncommitted edit, which is a judgement call, not a typo.
            if rel in EXEMPT or last is None or d is None or d >= last:
                continue
            fix(rel, last)
            print("  fix %s: %s -> %s" % (rel, d, last))
        # Re-read from disk: the verdict after a fix must come off the files, not off the plan.
        rows = [(rel, declared(io.open(os.path.join(REPO, rel), encoding="utf-8").read()), last)
                for rel, _d, last in rows]
    problems, checked, pending = judge(rows, dirty)
    print("updated-date verdict: reader pages=%d checked=%d exempt=%d problems=%d pending-commit=%d "
          "unreadable=%d"
          % (len(pages), checked, len(pages) - checked, len(problems), len(pending),
             len(unreadable)))
    if not args.quiet or problems:
        for line in problems:
            print("  PROBLEM " + line)
    for line in pending:
        print("  PENDING (working tree is ahead of HEAD, so git cannot attest this date yet) " + line)
    for line in unreadable:
        print("  COVERAGE unreadable: " + line)
    return 1 if (problems or unreadable) else 0


if __name__ == "__main__":
    sys.exit(main())
