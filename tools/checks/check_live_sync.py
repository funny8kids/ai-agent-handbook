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

Round 90 gave "cannot witness" its own bucket (owed since round 87). Round 90's own survey read
77 of 113 reader-page touches across the last 40 docs revisions to be UNWITNESSED — every date
bump and markup-only commit — so as a failure line it was a permanent red no sync can clear, and
`--watch` burned its whole budget polling for it. It is now printed per page plus a summary line
that names the `.md` leg as that revision's only evidence, and the exit code ignores it; STALE /
VACUITY / FETCH / NO-URL keep gating. The boundary the control (W) pins: UNWITNESSED is reachable
ONLY through an empty needle list, so a page whose revision really added printable prose and really
did not ship it can verdict nothing but STALE — "cannot witness" is still never read as "in sync".
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


def tail_needle():
    """Markup-free words from the LAST authored line of the changelog — the document's true tail.

    Round 91 measured why this question is asked: while GitBook rebuilt the changelog, three fetches
    of the same URL read 25,108,708 / 22,643,743 / 12,016,119 characters, and the response carries NO
    Content-Length, so a connection that ends early is indistinguishable from a shorter page — the
    12 M copy "lost" 51 of the 82 round headings, which reads exactly like the platform dropping
    history. A short read always loses the TAIL, and this document is newest-first, so its tail is
    the oldest round. Taking the last line rather than the oldest heading also catches a read that
    stops inside that section, and CJK words survive both endpoints verbatim (`2026-09-10` would
    too, but it is only 1 of the 5 tail dates, so it says less).

    Round 93 caught the one way that reasoning fails: the needle has to be a phrase that occurs
    ONLY at the tail. The 第 91 次 entry quotes the needle it chose, so that phrase appears twice in
    the document — once at 6.7 % — and a copy truncated just past the top of the file would then
    "prove" it arrived whole. So candidates are ranked by strength (the whole markup-free line
    first, then the last CJK run) and the first one that occurs exactly once wins; if none is
    unique, control S still goes red rather than letting the guard pass a short read.
    """
    text = open(LOCAL_CHANGELOG, encoding="utf-8").read()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Backticked runs print inside a code box that the HTML leg rewrites, and a link's target never
    # prints at all — a needle crossing that boundary matches one endpoint and not the other.
    bare = re.sub(r"\s+", " ", CODE_SPAN.sub(" ", LINK_TARGET.sub(r"\1", lines[-1]))).strip(" -•*")
    runs = re.findall(r"[\u4e00-\u9fff]+(?:[，、：（）][\u4e00-\u9fff]+)*", bare)
    for cand in sorted({bare} | set(runs), key=len, reverse=True):
        if text.count(cand) == 1:
            return cand
    return bare


def short_read(text, needle, is_html):
    """Did the whole document arrive? None means yes; a string names why not."""
    if is_html and not text.rstrip().endswith("</html>"):
        return "no closing </html>"
    if needle and needle not in text:
        return "the document's last authored line (%s) is absent" % needle
    return None


def live_rounds(url, tail=None):
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=180).read()
    html = raw.decode("utf-8", "replace")
    reason = short_read(html, tail, not url.endswith(".md"))
    if reason:
        raise ValueError("short read (%s), so no round count is trustworthy" % reason)
    # Round 91: the size used to be reported as `len(html)` under a "bytes" label. The changelog is
    # mostly CJK, so one UTF-8 character costs ~1.85 bytes and that mislabel manufactured a
    # discrepancy round 90's log recorded as unexplained (621,559 B fetched directly vs 336,586
    # "B" here — the same document, two units). Report both, and the ambiguity is gone.
    return [int(r) for r in ROUND.findall(html)], len(html), len(raw)


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


def page_bucket(url, needles):
    """What the EVIDENCE says before any fetch happened — pure, so control W can pin its boundary.

    Round 90's re-bucketing (owed since round 87): a page the revision gave no sliceable
    reader-printable text is UNWITNESSED — a coverage fact, loud but never a sync failure, because
    no amount of waiting makes such a revision witnessable from that page. A page with needles
    returns None: the fetch decides. NO-URL stays a failure — a touched page the judge cannot even
    address proves nothing either way.
    """
    if not url:
        return "NO-URL"
    if not needles:
        return "UNWITNESSED"
    return None


def page_verdict(needles, lost, phantom):
    """What the FETCHED reader text says — the other half of the boundary control W pins.

    The direction round 89 §五③ demanded a proof for: a page that DID add printable text and did
    NOT receive it is STALE and can never be excused into UNWITNESSED — UNWITNESSED is only ever
    reachable through an empty `needles`, and `needles_from` (with its nine controls) is the sole
    producer of that list.
    """
    if phantom:
        return "VACUITY"
    if lost:
        return "STALE"
    if not needles:
        return "UNWITNESSED"
    return "OK"


def witness_leg(rev="HEAD"):
    """Do the reader pages REV changed really carry REV's text on the live site?

    Returns (bad, unwitnessable, witnessed). Round 90 split the middle list out of `bad`: only
    STALE / VACUITY / FETCH / NO-URL keep the gate red; "cannot witness" is printed on its own line
    and can still never be read as "in sync" — such a revision is witnessed by the `.md` leg alone
    (round 59's rule, now with its own bucket instead of a permanent red).
    """
    sys.path.insert(0, HERE)
    import live_aria_manifest as LA
    import unicodedata
    index = LA.url_index()
    bad, unwitnessable, witnessed = [], [], 0
    for rel in head_reader_pages(rev):
        local = os.path.join(os.path.dirname(DOCS), rel)
        if not os.path.exists(local):
            continue
        text = open(local, encoding="utf-8").read()
        url = index.get(LA.norm(LA.h1_of(text)))
        ns = added_needles(local, rev)
        bucket = page_bucket(url, ns)
        if bucket == "NO-URL":
            bad.append("NO-URL %s" % rel)
            continue
        if bucket == "UNWITNESSED":
            unwitnessable.append("UNWITNESSED %s (%s added no printable text there — the .md leg "
                                 "is this revision's only witness)" % (rel, rev))
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
        phantom = (ns[0][:8] + u"墙" + ns[0][9:]) in page
        verdict = page_verdict(ns, lost, phantom)
        if verdict == "VACUITY":
            # Overrides STALE on purpose: a needle whose mutated twin also matched can certify
            # neither presence nor absence, so reporting a loss with it would claim more than
            # the evidence says (the line still lands in `bad` either way — the gate stays red).
            bad.append("VACUITY %s (a needle with one character changed also matched)" % rel)
            continue
        if verdict == "STALE":
            bad.append("STALE %s %d/%d added lines absent: %r" % (rel, len(lost), len(ns), lost[0][:24]))
            continue
        witnessed += 1
        print("  witness ok  %-46s %d/%d added needles live" % (rel, len(ns), len(ns)))
    for line in unwitnessable:
        print("  %s" % line)
    for line in bad:
        print("  %s" % line)
    return bad, unwitnessable, witnessed


def sync_verdict(want, have, blind, bad):
    """One number for the whole run: 0 in sync, 1 the site is behind, 2 this run judged nothing.

    Round 93 found the third state missing. `--watch` did `return 2` the moment a leg could not be
    read, so one truncated copy of the 25 MB changelog page (measured twice in one minute:
    18,900,551 chars with no `</html>`, then 25,108,708 with it) aborted a watch that had minutes of
    budget left — and the run it aborted printed the same `not online yet` sentence a real lag does.
    A leg that did not arrive is not evidence about readers, so it gets its own code and never a
    green: only the `.md` leg can blind the verdict (round 83 demoted the HTML page to a NOTE), and
    the HTML leg can never rescue or reject one.
    """
    if "md" in blind:
        return 2
    return 0 if (have >= want and not bad) else 1


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
        # W: round 90's bucket boundary, both directions — the proof the re-bucketing owed since
        # round 87 ("a page that really did not ship must never land in UNWITNESSED, or red has
        # only been renamed to white"). UNWITNESSED is reachable only through an empty needle list,
        # so the control rides on a REAL slicer run, not a hand-made list.
        wns = needles_from(["这一句新写的正文读者一定会看到，所以它是合法的见证针。"], reader_body(body))
        if page_bucket("https://x/page", wns) is not None:
            errs.append("control W: a page WITH printable additions must proceed to the fetch, got %r"
                        % page_bucket("https://x/page", wns))
        if not wns:
            errs.append("control W: the slicer returned no needle for obvious added prose — "
                        "every STALE would now read UNWITNESSED; the boundary is untested")
        if page_verdict(wns, wns, False) != "STALE":
            errs.append("control W: unsynced page WITH needles must verdict STALE, got %r"
                        % page_verdict(wns, wns, False))
        if page_verdict(wns, [], False) != "OK":
            errs.append("control W: a shipped page must verdict OK, got %r"
                        % page_verdict(wns, [], False))
        if page_verdict(wns, [], True) != "VACUITY":
            errs.append("control W: a self-matching needle must verdict VACUITY (overrides STALE), got %r"
                        % page_verdict(wns, wns, True))
        if page_bucket("https://x/page", []) != "UNWITNESSED":
            errs.append("control W: a markup-only revision must land in UNWITNESSED, got %r"
                        % page_bucket("https://x/page", []))
        if page_bucket(None, wns) != "NO-URL":
            errs.append("control W: an addressable-by-no-page touched file must stay NO-URL/bad, got %r"
                        % page_bucket(None, wns))
        # W2: the mutant the debt note was really about — a slicer gone blind. Patching
        # `needles_from` to always return [] must turn control W red, or the boundary is a
        # decoration the leg never consults.
        saved = globals()["needles_from"]
        try:
            globals()["needles_from"] = lambda *a, **k: []
            blind = needles_from(["这一句新写的正文读者一定会看到，所以它是合法的见证针。"],
                                 reader_body(body))
        finally:
            globals()["needles_from"] = saved
        if blind:
            errs.append("control W2: the monkeypatch did not land — the mutant never ran")
        if page_bucket("https://x/page", blind) != "UNWITNESSED":
            errs.append("control W2: a blind slicer must expose itself as UNWITNESSED on every page "
                        "(the gate then prints its cannot-witness lines LOUD); got %r"
                        % page_bucket("https://x/page", blind))
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
    # U: units. The leg line used to print `len(decoded)` under the word "bytes", and on a CJK-heavy
    # document that is ~1.85x below the real byte count — round 90 read the two numbers as a
    # platform mystery. Fetching a local file proves live_rounds returns (chars, bytes) in that
    # order and proves the printout labels them, so a relabel or a swap cannot re-pass silently.
    with tempfile.TemporaryDirectory(prefix="units", ignore_cleanup_errors=True) as tmp:
        doc = os.path.join(tmp, "u.md")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write("# 记录\n\n第 7 次：读者可见的中文句子。\n第 6 次：另一句中文。\n")
        rounds, chars, size = live_rounds("file:///" + doc.replace("\\", "/"))
        if rounds != [7, 6]:
            errs.append("control U: the round parser itself must see 7 and 6, got %r" % rounds)
        if not chars < size:
            errs.append("control U: CJK text must read as chars(%d) < utf-8 bytes(%d) — a run where "
                        "they are equal proves the two numbers are not what their labels say"
                        % (chars, size))
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        if "(%d chars / %d bytes" not in src or "chars, size" not in src:
            errs.append("control U: the leg line must label both numbers and pass the character "
                        "count first, or the printout is free to lie about its unit again")
    # S: short reads. Round 91 nearly recorded "the platform dropped 51 rounds" as a site failure;
    # it was a connection that ended early in a 25 MB page that ships no Content-Length. Three
    # ways to be short, one control each, plus the assertion that the chosen needle is really at
    # the tail (a needle quoted near the top would let every truncated read pass).
    with tempfile.TemporaryDirectory(prefix="shortread", ignore_cleanup_errors=True) as tmp:
        tail = tail_needle()
        doc = os.path.join(tmp, "s.md")
        text = ("# 记录\n\n第 7 次：读者可见的中文句子。\n第 6 次：另一句中文。\n"
                "- 迁移 GitBook 配置，内容目录设为 `docs/`\n")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write(text)
        url = "file:///" + doc.replace("\\", "/")
        cut = text[:text.index("- 迁移")]
        with open(os.path.join(tmp, "cut.md"), "w", encoding="utf-8") as fh:
            fh.write(cut)
        try:
            whole = live_rounds(url, tail="内容目录设为")
        except Exception as exc:  # noqa: BLE001
            errs.append("control S: a complete document must not read short (%s)" % exc)
            whole = None
        if whole and whole[0] != [7, 6]:
            errs.append("control S: the complete document must still parse rounds 7 and 6, got %r"
                        % (whole[0],))
        try:
            live_rounds("file:///" + os.path.join(tmp, "cut.md").replace("\\", "/"),
                        tail="内容目录设为")
            errs.append("control S: a read that stops before the last authored line must raise, "
                        "but it returned a round count — round 91's 12 M fetch would pass as truth")
        except ValueError:
            pass
        for what, page, needle, is_html, want in (
                ("a clean full HTML page", "<html><body>内容目录设为 x</body></html>", "内容目录设为",
                 True, None),
                ("HTML truncated mid-document", "<html><body>第 7 次", "内容目录设为", True,
                 "no closing </html>"),
                # The case `</html>` alone cannot catch: a well-formed page that simply publishes
                # fewer rounds than the tree has.
                ("HTML that closes cleanly but omits the oldest section",
                 "<html><body>第 7 次：读者可见的中文句子。</body></html>", "内容目录设为", True,
                 "the document's last authored line (内容目录设为) is absent"),
                ("a .md leg that stops early (no </html> to look for)",
                 "<html><body>第 7 次", "内容目录设为", False, "the document's last authored line")):
            got = short_read(page, needle, is_html)
            if want is None:
                if got is not None:
                    errs.append("control S: %s must read as complete, got %r" % (what, got))
            elif got is None or not got.startswith(want):
                errs.append("control S: %s must read short as %r, got %r" % (what, want, got))
        local = open(LOCAL_CHANGELOG, encoding="utf-8").read()
        if not tail or local.find(tail) < 0.9 * len(local):
            errs.append("control S: tail needle %r first appears at %.0f%% of the changelog — a "
                        "needle quoted near the top cannot expose a short read"
                        % (tail, 100.0 * max(0, local.find(tail)) / len(local)))
        if local.count(tail) != 1:
            errs.append("control S: tail needle %r occurs %d times in the changelog — only a phrase "
                        "that exists at the tail can certify the tail arrived" % (tail, local.count(tail)))
        # The exact way round 93 broke this guard: 第 91 次 quoted the needle it had chosen, so the
        # phrase moved from 99.99 % to 6.7 % and every truncated copy over ~7 % read "complete".
        with open(os.path.join(tmp, "quoted.md"), "w", encoding="utf-8") as fh:
            fh.write("# 记录\n\n第 9 次：门闩的针是 `配置，内容根目录设为`，这句写在最上面。\n\n"
                     "第 7 次：读者可见的中文句子。\n第 6 次：另一句中文。\n"
                     "- 迁移 GitBook 配置，内容根目录设为 `docs/`\n")
        saved_path = globals()["LOCAL_CHANGELOG"]
        try:
            globals()["LOCAL_CHANGELOG"] = os.path.join(tmp, "quoted.md")
            picked = tail_needle()
        finally:
            globals()["LOCAL_CHANGELOG"] = saved_path
        if picked == "配置，内容根目录设为":
            errs.append("control S: the slicer still returns the run a newer entry quoted — the "
                        "guard would certify a copy truncated at the quote")
        if open(os.path.join(tmp, "quoted.md"), encoding="utf-8").read().count(picked) != 1:
            errs.append("control S: on the quoted-tail document the slicer picked %r, which is not "
                        "unique there either — falling back to a weak needle must be visible" % picked)
    # X: the three-state verdict this file's own watch loop needed (round 93). The cases are chosen
    # so that the pre-fix behavior — abort the whole watch on ANY unreadable leg — cannot pass:
    # a blind HTML leg must be forgiven (round 83 demoted it to a NOTE), a blind `.md` leg must
    # report "no verdict" rather than "the site is behind", and neither may ever read as 0.
    for what, want, have, blind, bad, expect in (
            ("md current, html short-read: keep watching, this is sync", 93, 93, ["html"], [], 0),
            ("md current, html blind, witness red: the witness still gates", 93, 93, ["html"],
             ["STALE x 1/1"], 1),
            ("md behind, both legs readable: the site is late", 93, 92, [], [], 1),
            ("md itself unreadable: no verdict, never a green and never a lag", 93, 0,
             ["md"], [], 2),
            ("md unreadable AND behind-looking: the blindness wins, no verdict", 93, 0,
             ["md", "html"], [], 2),
            ("nothing to witness and md current is the shipped reading", 93, 93, [], [], 0)):
        got = sync_verdict(want, have, blind, bad)
        if got != expect:
            errs.append("control X: %s must verdict %d, got %d" % (what, expect, got))
    if sync_verdict(93, 93, [], []) == sync_verdict(93, 92, [], []):
        errs.append("control X: a one-round lag must not be indistinguishable from sync")
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        src = fh.read()
    # Anchor on the definition line, not the name: a plain search for the text of this very anchor
    # would land inside this control.
    anchor = re.search(r"^def ma" + r"in\(\):", src, re.M)
    tail_src = src[anchor.start():] if anchor else ""
    if not anchor:
        errs.append("control X: cannot find main() in this file — the source scan is blind")
    if ("return " + "2") in tail_src:
        errs.append("control X: main() must not exit the run on one unreadable leg — only "
                    "sync_verdict may hand out code 2, or a watch aborts on a transient short read")
    if "blind.append(name)" not in tail_src:
        errs.append("control X: an unreadable leg must be recorded in `blind` and skipped, not "
                    "returned from — otherwise one short read aborts the whole watch")
    if '"html" not in blind' not in tail_src:
        errs.append("control X: the lag NOTE must be gated on the html leg being readable; a leg "
                    "that never arrived cannot state what readers are missing")
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
        blind = []
        print("local newest round=%d" % want)
        for name, url in LEGS:
            try:
                live, chars, size = live_rounds(url, tail_needle())
            except Exception as exc:  # noqa: BLE001
                # The reason is the finding: "ValueError" alone cannot distinguish this round's
                # short-read guard from a DNS failure, and the two want opposite follow-ups.
                print("live changelog (%s) unreadable (%s: %s) — no verdict from this leg, this is "
                      "not a site failure" % (name, exc.__class__.__name__, exc))
                blind.append(name)
                continue
            tops[name] = max(live) if live else 0
            missing = sorted({r for r in local if r > tops[name]})
            print("  leg %-4s newest round=%-3d (%d chars / %d bytes, %d rounds)%s"
                  % (name, tops[name], chars, size, len(live),
                     "" if not missing else "  missing %s" % ", ".join(map(str, missing))))
        bad, unwit, witnessed = ([], [], 0) if args.no_witness else witness_leg(args.rev)
        if witnessed:
            print("  witness: %d reader page(s) %s touched carry %s's added text" % (witnessed, args.rev, args.rev))
        elif not args.no_witness:
            print("  witness: %s added no reader-page text outside the changelog — the .md leg is the witness"
                  % args.rev)
        if unwit:
            print("  witness: %d page(s) CANNOT WITNESS %s (round 90's bucket: loud, never green — "
                  "this revision is only evidenced by the .md leg)" % (len(unwit), args.rev))
        lag = tops.get("html", 0)
        if "html" not in blind and lag < want:
            # Round 83 measured this document pinned at round 79 for hours (same etag on six fetches)
            # while the homepage and a knowledge page HEAD had just edited were both current. So the
            # changelog's own HTML page no longer gates the verdict — but the lag is a reader-facing
            # fact and stays printed, never silently forgiven. A leg that could not be read says
            # nothing about what readers are missing, so it must not print a lag either.
            missing = sorted({r for r in local if r > lag})
            print("  NOTE the published changelog PAGE is at round %d: readers opening it are missing %s"
                  % (lag, ", ".join(map(str, missing))))
        have = tops.get("md", 0)
        ok = sync_verdict(want, have, blind, bad) == 0
        if not ok:
            print("not online yet: md leg round %d vs HEAD %d, witness failures %d%s"
                  % (have, want, len(bad),
                     "" if not blind else ", unreadable legs: " + "/".join(blind)))
        if ok or not args.watch or time.time() >= deadline:
            return sync_verdict(want, have, blind, bad)
        print("  ... watching, next probe in 90 s")
        time.sleep(90)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
