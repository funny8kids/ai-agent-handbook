"""Is the published site actually at HEAD? Answer in one number: which changelog round is live.

Why this file exists (round 61): the round was pushed at 13:35 and a fixed 20-poll / 15-minute wait
ended with 4 of 9 anchors still missing. Polling a page for a guessed timeout cannot distinguish
"the platform is slow" from "our change never rendered", so the round had to stay open. The
changelog page carries every round number the repo has ever published, so reading it tells us the
live revision directly — one request, no guessing, and the lag is stated in rounds.

Usage:
    python tools/checks/check_live_sync.py            -> exit 0 when live has caught up with HEAD
    python tools/checks/check_live_sync.py --watch    -> keep polling until it does (or --timeout)

Two legs, because they are not the same question (round 64): the `.md` endpoint and the rendered
page update at different times, and reading only the `.md` lets this gate say "in sync" while the
page a reader opens is still two rounds behind — which is exactly what happened to the changelog
page here, `.md` current and HTML 65+ minutes stale at 9.7 MB. The verdict is the WORSE leg.
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import time
import urllib.request

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="keep polling until live catches up")
    ap.add_argument("--timeout", type=int, default=0, help="--watch budget, seconds")
    args = ap.parse_args()

    local = local_rounds()
    want = max(local) if local else 0
    # Vacuity guard: if the judge cannot see the round history it must not report "in sync".
    assert len(local) >= 50, "only %d round headings parsed locally — the judge is blind" % len(local)
    deadline = time.time() + args.timeout
    while True:
        when, age = head_age()
        if age:
            print("HEAD committed %s, %d min ago" % (when.date(), int(age.total_seconds() // 60)))
        have = None
        print("local newest round=%d" % want)
        for name, url in LEGS:
            try:
                live, size = live_rounds(url)
            except Exception as exc:  # noqa: BLE001
                print("live changelog (%s) unreadable (%s) — no verdict, this is not a site failure"
                      % (name, exc.__class__.__name__))
                return 2
            top = max(live) if live else 0
            have = top if have is None else min(have, top)
            missing = sorted({r for r in local if r > top})
            print("  leg %-4s newest round=%-3d (%d bytes, %d rounds)%s"
                  % (name, top, size, len(live),
                     "" if not missing else "  missing %s" % ", ".join(map(str, missing))))
        if have < want:
            print("not online yet: the reader-visible leg is round %d, HEAD is %d" % (have, want))
        if have >= want or not args.watch or time.time() >= deadline:
            return 0 if have >= want else 1
        print("  ... watching, next probe in 90 s")
        time.sleep(90)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
