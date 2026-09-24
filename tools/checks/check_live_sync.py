"""Is the published site actually at HEAD? Answer in one number: which changelog round is live.

Why this file exists (round 61): the round was pushed at 13:35 and a fixed 20-poll / 15-minute wait
ended with 4 of 9 anchors still missing. Polling a page for a guessed timeout cannot distinguish
"the platform is slow" from "our change never rendered", so the round had to stay open. The
changelog page carries every round number the repo has ever published, so reading it tells us the
live revision directly — one request, no guessing, and the lag is stated in rounds.

Usage:
    python tools/checks/check_live_sync.py            -> exit 0 when live has caught up with HEAD
    python tools/checks/check_live_sync.py --watch    -> keep polling until it does (or --timeout)

Two legs of the changelog, because they are not the same question (round 64): the `.md` endpoint and
the rendered page update at different times, and reading only the `.md` let this gate say "in sync"
while the page a reader opens was still two rounds behind.

Round 83 changed what the verdict may rest on. The rendered changelog page (18 MB, 439 round
mentions) turned out to be pinned: six fetches over hours returned one etag and round 79, while the
`.md` endpoint, the homepage and a knowledge page HEAD had just edited were all current. A document
the platform refreshes on its own schedule cannot gate anything, so it is now a loud NOTE ("readers
opening the changelog page are missing rounds X, Y") and the verdict rests on:
  1. the `.md` endpoint carrying the newest round, and
  2. the WITNESS leg — every reader page the revision changed must contain text that revision ADDED
     (with a phantom needle per page, so a page that "contains" everything is caught).
A revision that only touched the changelog has no reader page to witness, which is stated as such
rather than counted as a pass.
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import time
import urllib.request
from html import unescape

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(HERE, "..", "..", "docs"))
SITE = "https://violetnotes.gitbook.io/violetnotes-docs"
LEGS = (("md", SITE + "/dao-hang-yu-suo-yin/changelog.md"),
        ("html", SITE + "/dao-hang-yu-suo-yin/changelog"))
LOCAL_CHANGELOG = os.path.join(DOCS, "00-index", "changelog.md")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
ROUND = re.compile(r"第 (\d+) 次")


def live_rounds(url):
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=180).read().decode("utf-8", "replace")
    return [int(r) for r in ROUND.findall(html)], len(html)


def local_rounds():
    text = open(LOCAL_CHANGELOG, encoding="utf-8").read()
    return [int(r) for r in ROUND.findall(text)]


def head_age():
    """How long the newest local round has been committed (its own clock, not the shell's)."""
    out = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=os.path.dirname(DOCS),
                         capture_output=True).stdout.decode("utf-8", "replace").strip()
    try:
        when = datetime.datetime.fromisoformat(out)
        return when, (datetime.datetime.now(when.tzinfo) - when)
    except ValueError:
        return None, None


CJK_RUN = re.compile(u"[一-鿿，、：；（）「」\u201c\u201d—…·]{16,}")
# A commit that adds no prose still adds something the reader can be shown: the link it introduced,
# or the day it stamped. Round 83 measured three such pages, and both strings sit in the reader's
# tag-stripped text — `norm()` must not be used as the haystack here because it rewrites `-` to a
# space and would hide every host and date.
URL_ADDED = re.compile(r"https?://([^\s<>)\]\"'，。；、]{10,})")
STAMP = re.compile(r"^(?:updated|last_updated|date):\s*(20\d\d-\d\d-\d\d)", re.M)
# A tag name never starts with a digit, so a needle's own prose `<` cannot open a deletion (round 83
# measured the changelog write `（W<420 且 H>380）` disappear under a loose `<[^>]+>`).
WITNESS_TAG = re.compile(r"<[a-zA-Z/!][^>]*>")
# What a line looks like to a reader is not what it looks like in a diff: backticked runs are
# printed inside a code box that the visibility pipeline drops, and a link's target never prints at
# all — only its label does. Slicing needles out of either yields a needle no reader page can show,
# i.e. a STALE red that no amount of syncing clears (round 84's lesson, applied to the other side).
CODE_SPAN = re.compile(r"`[^`\n]*`")
LINK_TARGET = re.compile(r"\[([^\]]*)\]\(([^)\n]*)\)")


def sliceable(lines):
    """The reader-visible characters of authored lines: code-box contents and link targets removed."""
    raw = "\n".join(lines)
    return LINK_TARGET.sub(r"\1", CODE_SPAN.sub(" ", raw))


def head_reader_pages(rev="HEAD"):
    """`docs/*.md` files REV changed, minus the changelog (that one has its own legs).

    Round 87 dropped the `14-templates` clause: the three files under it all carry
    `status: published`, their H1s resolve in `LA.url_index()`, and `check_prose_survival` now
    grades them — so a revision that edits the style guide or the knowledge template has real
    reader-visible prose that the witness leg must be able to track. The old premise ("authoring
    scaffolding, not on the site") was inherited from `live_aria_manifest.build`, where the same
    skip is only a work-saver because that walker keeps only widget-bearing pages anyway.
    """
    out = subprocess.run(["git", "show", "--name-only", "--format=", rev],
                         cwd=os.path.dirname(DOCS), capture_output=True).stdout
    files = [f.decode("utf-8", "replace").strip().replace("\\", "/") for f in out.splitlines()]
    return [f for f in files
            if f.startswith("docs/") and f.endswith(".md") and "SUMMARY.md" not in f
            and "00-index/changelog.md" not in f]


def reader_body(path):
    """The part of an authored page a reader is actually shown.

    Round 84 measured five reader pages touched by recent rounds: none of their served documents —
    raw HTML included — contained the page's own `updated:` value, because frontmatter is never
    printed. A needle no page prints converts a markup-only revision into a permanent STALE red,
    which is the ruler failing rather than the site; the honest bucket for such a page is
    UNWITNESSED ("cannot witness", never "in sync"). The frontmatter rule is borrowed from
    `check_prose_survival` so the two judges cannot disagree about where prose starts.
    """
    sys.path.insert(0, HERE)
    import check_prose_survival as PS
    lines = open(path, encoding="utf-8").read().split("\n")
    return "\n".join(lines[PS.frontmatter_end(lines):])


def needles_from(added_lines, body, removed_lines=()):
    """Slice witness needles from text the revision INTRODUCTED and the page prints.

    Round 84: every needle — the prose runs as well as the two fallbacks — must survive in `body`,
    because frontmatter is never printed on a reader page. A commit that touches only
    `description:` or `cover:` otherwise yields an invisible needle, which is a STALE red no amount
    of syncing can clear (the same bug item ② caught in the fallbacks, sitting one line higher).

    Round 86 added the other half of the same question. `git show` hands back whole ADDED LINES, and
    a line whose only change is a digit counts as added, so slicing prose off it certifies a
    sentence that was already live one revision ago — a needle that can never fail. A candidate
    therefore also has to be absent from the lines the revision REMOVED. Without that filter the
    homepage's three "live" needles were round 80's text, on a page whose round-86 sentences had
    not reached readers at all.
    """
    raw = sliceable(added_lines)
    old = sliceable(removed_lines)
    text = re.sub(r"[`*_\[\]()#|>-]", " ", raw)
    seen, needles = set(), []
    for r in (x[:18] for x in CJK_RUN.findall(text)):
        if r in old or r in seen:
            continue                     # survived the edit unchanged => witnesses nothing
        seen.add(r)
        if r in body:
            needles.append(r)
    if needles:
        return needles[:3]
    # No printable prose was added: witness the link the commit introduced, or the day it stamped.
    for host in URL_ADDED.findall(raw):
        h = host.rstrip("/.")
        if h and h not in old and h not in needles and h in body:
            needles.append(h)
    stamp = STAMP.search(raw)
    if stamp and stamp.group(1) not in old and stamp.group(1) not in needles \
            and stamp.group(1) in body:
        needles.append(stamp.group(1))
    return needles[:3]


def added_needles(path, rev="HEAD"):
    """Needles sliced from text REV introduced on that page — never from the whole file.

    A needle from an unchanged paragraph is on the published page either way, so it witnesses
    nothing; the added lines are the only text whose presence proves the reader got this revision,
    and the removed lines say which part of them the revision actually wrote (round 86).
    """
    diff = subprocess.run(["git", "show", "--unified=0", "--format=", rev, "--", path],
                          cwd=os.path.dirname(DOCS), capture_output=True).stdout
    lines = diff.decode("utf-8", "replace").splitlines()
    added = [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in lines if l.startswith("-") and not l.startswith("---")]
    return needles_from(added, reader_body(path), removed)


def witness_leg(rev="HEAD"):
    """Do the reader pages REV changed really carry REV's text on the live site?

    Returns (bad, witnessed). A page with no published address, no sliceable needle, or a missing
    needle is a failure: "cannot witness" must never be read as "in sync" (round 59's rule).
    """
    sys.path.insert(0, HERE)
    import live_aria_manifest as LA
    import unicodedata
    index = LA.url_index()
    bad, witnessed = [], 0
    for rel in head_reader_pages(rev):
        local = os.path.join(os.path.dirname(DOCS), rel)
        if not os.path.exists(local):
            continue
        text = open(local, encoding="utf-8").read()
        url = index.get(LA.norm(LA.h1_of(text)))
        ns = added_needles(local, rev)
        if not url:
            bad.append("NO-URL %s" % rel)
            continue
        if not ns:
            bad.append("UNWITNESSED %s (%s added no sliceable text there)" % (rel, rev))
            continue
        try:
            html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
        except Exception as exc:  # noqa: BLE001
            bad.append("FETCH %s %s" % (rel, exc.__class__.__name__))
            continue
        # Tags first, entities after — the order `check_prose_survival` uses, so a `&gt;` inside an
        # attribute can never fake a tag close, and an address or quoted phrase shipped as `&quot;`
        # is read as the characters the reader sees rather than the word "quot" (round 83).
        # Round 86 moved the haystack from the raw document to the reader's text: the served HTML
        # also carries GitBook's editor payload, which embeds the page's NEWEST markdown while the
        # paragraph a reader is shown is still the previous revision's. Matching the raw document
        # certified three round-80 sentences as "live" on a homepage whose round-86 sentences had
        # not arrived — the two faults in one line, since those sentences also survived the edit.
        raw_html = html.decode("utf-8", "replace")
        page = unicodedata.normalize(
            "NFC", unescape(WITNESS_TAG.sub(" ", LA.body_visible(raw_html))))
        lost = [n for n in ns if n not in page]
        phantom = ns[0][:8] + u"墙" + ns[0][9:]
        if phantom in page:
            bad.append("VACUITY %s (a needle with one character changed also matched)" % rel)
        if lost:
            bad.append("STALE %s %d/%d added lines absent: %r" % (rel, len(lost), len(ns), lost[0][:24]))
            continue
        witnessed += 1
        print("  witness ok  %-46s %d/%d added needles live" % (rel, len(ns), len(ns)))
    for line in bad:
        print("  %s" % line)
    return bad, witnessed


def controls():
    """The witness needles must be text a reader can be shown — and must survive when they are."""
    import tempfile
    errs = []
    with tempfile.TemporaryDirectory(prefix="witness", ignore_cleanup_errors=True) as tmp:
        fm = os.path.join(tmp, "a.md")
        open(fm, "w", encoding="utf-8").write(
            "---\ntitle: 演示页\nupdated: 2026-09-25\ncover: https://example.com/cover.png\n"
            "description: 这一句只写在元数据里，读者页面上永远不会看到它。\n---\n\n"
            "# 演示页\n\n这一页的正文里既没有日期也没有地址。\n")
        body = os.path.join(tmp, "b.md")
        open(body, "w", encoding="utf-8").write(
            "---\ntitle: 演示页\nupdated: 2026-09-25\n---\n\n# 演示页\n\n"
            "这一天 2026-09-25 写在正文里，读者看得见它。\n"
            "参考 https://example.com/spec#section 里的说法。\n"
            "这一句新写的正文读者一定会看到，所以它是合法的见证针。\n"
            "这一句是上一版就印在页面上的旧话，本轮只把行尾的数字改成 57。\n"
            "`代码盒子里那句新写的正文，读者页面的可见文字里并没有它，所以它当不了针。`\n")
        prose_run = [x[:18] for x in CJK_RUN.findall(
            "这一句新写的正文读者一定会看到，所以它是合法的见证针。")][0]
        kept_run = [x[:18] for x in CJK_RUN.findall(
            "这一句是上一版就印在页面上的旧话，本轮只把行尾的数字改成 60。")][0]
        assert kept_run in reader_body(body), \
            "control needs the kept sentence on the page: the filter, not the body gate, must exclude it"
        for what, page, added, removed, want in (
                ("a frontmatter date must not be a needle", fm, ["updated: 2026-09-25"], [], []),
                ("a date printed in the body must be a needle",
                 body, ["updated: 2026-09-25"], [], ["2026-09-25"]),
                ("a frontmatter cover address is not reader text",
                 fm, ["cover: https://example.com/cover.png"], [], []),
                ("an address printed in the body must be a needle",
                 body, ["参考 https://example.com/spec#section 里的说法。"], [],
                 ["example.com/spec#section"]),
                ("Chinese that lives only in frontmatter is no needle",
                 fm, ["description: 这一句只写在元数据里，读者页面上永远不会看到它。"], [], []),
                ("new prose the page prints must stay a needle",
                 body, ["这一句新写的正文读者一定会看到，所以它是合法的见证针。"], [], [prose_run]),
                ("ordinary unchanged prose is no witness: the line must come from the revision",
                 body, ["updated: 2031-01-01"], [], []),
                # The two faults round 86 measured on the live homepage, in one control each.
                ("a sentence that merely survived the edit witnesses nothing",
                 body, ["这一句是上一版就印在页面上的旧话，本轮只把行尾的数字改成 60。"],
                 ["这一句是上一版就印在页面上的旧话，本轮只把行尾的数字改成 57。"], []),
                ("prose inside a code box is not reader-visible text",
                 body, ["`代码盒子里那句新写的正文，读者页面的可见文字里并没有它，所以它当不了针。`"],
                 [], [])):
            got = needles_from(added, reader_body(page), removed)
            if got != want:
                errs.append("control: %s (added=%r removed=%r want=%r got=%r)"
                            % (what, added, removed, want, got))
    # N: coverage. `head_reader_pages` used to drop any path under `docs/14-templates/` on the
    # premise those pages were authoring scaffolding. Round 87 measured the premise false (all three
    # are `status: published` with H1s in the URL index), and round 86's own main commit changed
    # `style-guide.md` — a revision whose reader-visible prose the witness leg should have tracked
    # and could not. Look up the newest rev that really touched the guide (via git, so this stays
    # true as history moves) and require it to appear in that rev's reader-page set.
    guide = "docs/14-templates/style-guide.md"
    probe = subprocess.run(["git", "log", "-1", "--format=%H", "--", guide],
                           cwd=os.path.dirname(DOCS), capture_output=True)
    rev = probe.stdout.decode("utf-8", "replace").strip()
    if not rev:
        errs.append("control N: no rev in history touched %s — the coverage probe is blind" % guide)
    elif guide not in head_reader_pages(rev):
        errs.append("control N: head_reader_pages(%s) must include %s, got %r" % (rev[:7], guide, head_reader_pages(rev)))
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="keep polling until live catches up")
    ap.add_argument("--timeout", type=int, default=0, help="--watch budget, seconds")
    ap.add_argument("--no-witness", action="store_true",
                    help="skip the changed-pages leg (cheap, and then only the .md endpoint is judged)")
    ap.add_argument("--rev", default="HEAD",
                    help="which revision's added reader-page text the witness leg looks for "
                         "(a past round works as a positive control for this leg)")
    ap.add_argument("--selftest", action="store_true",
                    help="judge the needle slicer on synthetic pages, no network")
    args = ap.parse_args()

    if args.selftest:
        errs = controls()
        print("controls: %s" % ("OK, every needle rule able to fire" if not errs else "BROKEN"))
        for e in errs:
            print("   ", e)
        return 1 if errs else 0

    local = local_rounds()
    want = max(local) if local else 0
    # Vacuity guard: if the judge cannot see the round history it must not report "in sync".
    assert len(local) >= 50, "only %d round headings parsed locally — the judge is blind" % len(local)
    deadline = time.time() + args.timeout
    while True:
        when, age = head_age()
        if age:
            print("HEAD committed %s, %d min ago" % (when.date(), int(age.total_seconds() // 60)))
        tops = {}
        print("local newest round=%d" % want)
        for name, url in LEGS:
            try:
                live, size = live_rounds(url)
            except Exception as exc:  # noqa: BLE001
                print("live changelog (%s) unreadable (%s) — no verdict, this is not a site failure"
                      % (name, exc.__class__.__name__))
                return 2
            tops[name] = max(live) if live else 0
            missing = sorted({r for r in local if r > tops[name]})
            print("  leg %-4s newest round=%-3d (%d bytes, %d rounds)%s"
                  % (name, tops[name], size, len(live),
                     "" if not missing else "  missing %s" % ", ".join(map(str, missing))))
        bad, witnessed = ([], 0) if args.no_witness else witness_leg(args.rev)
        if witnessed:
            print("  witness: %d reader page(s) %s touched carry %s's added text" % (witnessed, args.rev, args.rev))
        elif not args.no_witness:
            print("  witness: %s added no reader-page text outside the changelog — the .md leg is the witness"
                  % args.rev)
        lag = tops.get("html", 0)
        if lag < want:
            # Round 83 measured this document pinned at round 79 for hours (same etag on six fetches)
            # while the homepage and a knowledge page HEAD had just edited were both current. So the
            # changelog's own HTML page no longer gates the verdict — but the lag is a reader-facing
            # fact and stays printed, never silently forgiven.
            missing = sorted({r for r in local if r > lag})
            print("  NOTE the published changelog PAGE is at round %d: readers opening it are missing %s"
                  % (lag, ", ".join(map(str, missing))))
        have = tops.get("md", 0)
        ok = have >= want and not bad
        if not ok:
            print("not online yet: md leg round %d vs HEAD %d, witness failures %d" % (have, want, len(bad)))
        if ok or not args.watch or time.time() >= deadline:
            return 0 if ok else 1
        print("  ... watching, next probe in 90 s")
        time.sleep(90)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
