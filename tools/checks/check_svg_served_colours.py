# -*- coding: utf-8 -*-
"""Served-colour parity: did a RECOLOUR actually reach the bytes the reader fetches?

Why this file exists (round 69). `check_svg_sanitizer.py` compares the element and attribute
MULTISET of the served copy against the authored file, which is exactly the right instrument for a
sanitizer that deletes things -- and completely blind to a value change: `fill="#0284c7"` becoming
`fill="#0369a1"` keeps the attribute, so the multiset is identical while the figure the reader gets
is a different drawing. Rounds 64-68 could get away with that because they moved geometry; round 69
moved 30 colours across 12 figures and needed a leg that prices the colours themselves.

What it asserts, per asset: the colour-literal multiset of the served copy EQUALS the authored
file's. Not "the new hexes appear somewhere" -- a revision that merely uses a colour FEWER times
would pass that and mean nothing.

The control leg is the point of the file: a drawing whose colours provably differ from the served
copy is graded against those same bytes and MUST differ. Without it a green run cannot be told apart
from a CDN serving a stale build, since both leave "some blues are present" true. The asset for that
is the first sampled one that is a recolour; when THIS round moved no colours (round 97 edited the
banner's page-count TEXT), the leg falls back to the most recent commit that did move them -- a
control that only exists in recolour rounds is no control, and the old code said so by printing
"THE PROBE IS DEAD" over a perfectly honest run.

Coverage is a separate bucket from findings, per the round-60/67/95 rule: an asset whose fetch never
landed is not a pass. `--min-reached` is a floor on FETCH SUCCESS, not on the size of the round's
work list -- a one-asset round that reaches its one asset prints a SMALL-SAMPLE note and passes,
while 3-of-12 reached stays red. See `coverage_call()` and `--selftest`.

URLs are never guessed: the page address comes from `llms.txt` by published title, and the asset
address is read off the `<img>` on that page (the `~gitbook/image` proxy -- `.gitbook/assets/*` 404s
on the live host).

Usage:
    python tools/checks/check_svg_served_colours.py
    python tools/checks/check_svg_served_colours.py --assets 04-react-loop.svg 08-collab-patterns.svg
    python tools/checks/check_svg_served_colours.py --selftest   # offline: the two legs that could not say NO
"""
import argparse
import collections
import io
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import check_svg_sanitizer as cs                                    # noqa: E402
import check_widget_visibility_live as wl                           # noqa: E402

COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
SWEEP_PAUSE = getattr(cs, "SWEEP_PAUSE", 0.8)


def colours(text):
    """Every colour literal the drawing can carry, lowercased (the proxy may re-case them)."""
    return collections.Counter(m.lower() for m in COLOR.findall(text))


def revision_asset(rev, name):
    p = subprocess.run(["git", "-C", REPO, "show", "%s:docs/.gitbook/assets/%s" % (rev, name)],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return "" if p.returncode else p.stdout.decode("utf-8", "replace")


def sample_and_baseline():
    """(assets to verify, revision they changed FROM).

    Two states have to work, because this axis is run both before and after the recolour commit:
    with the recolours still in the working tree the baseline is HEAD, and once they are committed
    (and a close-out commit has landed on top) the baseline is the parent of the newest commit that
    touched the assets. Guessing "HEAD~1" instead would silently find nothing to verify one commit
    after the round that needed it.
    """
    def lines(*cmd):
        p = subprocess.run(["git", "-C", REPO] + list(cmd), stdout=subprocess.PIPE, check=True)
        return [l for l in p.stdout.decode("utf-8", "replace").splitlines()
                if l.startswith("docs/.gitbook/assets/") and l.endswith(".svg")]

    dirty = lines("diff", "--name-only", "HEAD", "--", "docs/.gitbook/assets")
    if dirty:
        return sorted(os.path.basename(l) for l in dirty), "HEAD"
    p = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%H", "--", "docs/.gitbook/assets"],
                       stdout=subprocess.PIPE, check=True)
    rev = p.stdout.decode().strip()
    assert rev, "no commit has ever touched the assets"
    return sorted(os.path.basename(l) for l in lines("show", "--name-only", "--format=", rev)), rev + "^"


def grade(want, raw):
    """(colours the served copy is missing, colours it carries that the author never wrote)."""
    got = colours(raw)
    return want - got, got - want


def tree_asset(name):
    return io.open(os.path.join(cs.ASSETS, name), encoding="utf-8").read()


def colour_delta(baseline, name):
    """True when `name`'s colour multiset differs between `baseline` and the working tree."""
    prior = revision_asset(baseline, name)
    return bool(prior) and colours(prior) != colours(tree_asset(name))


def historical_control(limit=30):
    """The first (asset, revision) that THIS repo actually recoloured in the past and that still
    hangs on a page. The falsification leg needs a drawing whose colours differ from the served
    copy -- and it must not be a leg that only exists in rounds that happen to recolour."""
    p = subprocess.run(["git", "-C", REPO, "log", "-%d" % limit, "--format=%H",
                        "--", "docs/.gitbook/assets"], stdout=subprocess.PIPE, check=True)
    for rev in p.stdout.decode("utf-8", "replace").split():
        q = subprocess.run(["git", "-C", REPO, "show", "--name-only", "--format=", rev],
                           stdout=subprocess.PIPE, check=True)
        for line in q.stdout.decode("utf-8", "replace").splitlines():
            if not (line.startswith("docs/.gitbook/assets/") and line.endswith(".svg")):
                continue
            name = os.path.basename(line)
            if not os.path.isfile(os.path.join(cs.ASSETS, name)):
                continue
            old = colours(revision_asset(rev + "^", name))
            new = colours(revision_asset(rev, name))
            if old and old != new:
                return name, rev
    return None


def coverage_call(sample_n, reached, min_reached):
    """(passed, note). `--min-reached` prices FETCH SUCCESS, not how many assets a round happened
    to touch: a fully-reached short sample is a note, a sample that could not be fetched is red.

    The two directions are the point (round 97). Before this, one dirty asset + a floor of 10 made
    an honest run read as "the sample was never reached", which is the same exit code as the CDN
    having served nothing -- and a rerun could never clear it.
    """
    if reached == sample_n and sample_n < min_reached:
        return True, ("SMALL-SAMPLE note: this round touches %d asset(s), all reached; the floor "
                      "of %d counts fetch failures, not a short work list" % (sample_n, min_reached))
    if reached < min_reached:
        return False, ("COVERAGE failure (not a content finding): %d reached of %d sampled, floor "
                       "%d -- rerun." % (reached, sample_n, min_reached))
    return True, ""


def selftest():
    """Offline controls for the two legs that round 97 found unable to say NO."""
    ok, note = coverage_call(1, 1, 10)
    assert ok and "SMALL-SAMPLE" in note, "a fully-reached 1-asset sample must not read as coverage failure"
    ok, note = coverage_call(12, 3, 10)
    assert not ok and "COVERAGE" in note, "3 of 12 reached must stay red: %s" % note
    ok, note = coverage_call(12, 12, 10)
    assert ok and not note, "a full sample must read clean without a note"
    ok, note = coverage_call(10, 9, 10)
    assert not ok, "one missing fetch under the floor must stay red"
    # the fallback falsification leg must have something to falsify on THIS repo
    name, rev = historical_control()
    assert name, "no commit in the last 30 asset touches moved a colour -- the control leg is dead"
    assert os.path.isfile(os.path.join(cs.ASSETS, name)), "control %s is not in the tree" % name
    before, after = colours(revision_asset(rev + "^", name)), colours(revision_asset(rev, name))
    assert before and before != after, "control %s@%s does not actually differ in colours" % (name, rev[:8])
    print("selftest: coverage call 4-way + fallback control %s@%s (colours moved %d ways)"
          % (name, rev[:8], len((before - after) + (after - before))))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", nargs="*", default=None)
    ap.add_argument("--min-reached", type=int, default=10)
    ap.add_argument("--control-asset", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    discovered, baseline = sample_and_baseline()
    names = args.assets or discovered
    assert names, ("no asset differs from %s -- nothing to verify (pass --assets to name some)" % baseline)
    index, ambiguous = wl.page_index(wl.llms_entries())
    assert not ambiguous, "ambiguous published titles: %s" % sorted(ambiguous)
    usage = cs.page_usage()

    bad, unreachable, reached = [], [], 0
    for name in names:
        time.sleep(SWEEP_PAUSE)
        authored = io.open(os.path.join(cs.ASSETS, name), encoding="utf-8").read()
        want = colours(authored)
        pages = [p for p in usage.get(name) or [] if p != "README.md"] or usage.get(name) or []
        assert pages, "%s is used by no page in the tree" % name
        try:
            raw, rel = cs.served_copy_cooled(name, index)
        except RuntimeError as exc:
            unreachable.append(name)
            print("  %-38s FETCH-FAILED after cool-down: %s" % (name, str(exc)[:90]))
            continue
        if raw is None:
            unreachable.append(name)
            print("  %-38s NOT-SERVED (no <img> naming it on %s)" % (name, pages[0]))
            continue
        reached += 1
        less, more = grade(want, raw)
        if less or more:
            bad.append(name)
            print("  %-38s DIFFERS  served-short=%s served-extra=%s"
                  % (name, dict(less), dict(more)))
        else:
            old = colours(revision_asset(baseline, name))
            added, retired = want - old, old - want
            print("  %-38s ok  served on %-44s %d colour literals (new=%d retired=%d vs %s)"
                  % (name, rel, sum(want.values()), len(added), len(retired), baseline))

    # Control: grade a DIFFERENT drawing against the same served bytes. If the prior version also
    # reads equal, this axis cannot tell a fresh build from a stale one and its green means nothing.
    #
    # Round 97 taught the second half of this: the leg used to require the SAMPLED asset to be a
    # recolour, so a round that edits an asset's TEXT (the banner's page-count badge) drove the
    # control to "READS CLEAN -- THE PROBE IS DEAD" -- a false alarm about the ruler, not the book.
    # A control that only exists in recolour rounds is not a control; fall back to the last
    # recolour this repo actually shipped and falsify against that.
    control, control_rev = None, baseline
    for name in ([args.control_asset] if args.control_asset else names):
        if colour_delta(baseline, name):
            control, control_rev = name, baseline
            break
    fallback = None if control else historical_control()
    if control:
        prior = revision_asset(control_rev, control)
        assert prior != tree_asset(control), \
            "control asset %s is byte-equal to %s -- the falsification leg is dead" % (control,
                                                                                       control_rev)
    else:
        assert fallback, ("no asset in the sample is a recolour and no past commit recoloured one "
                          "either -- the falsification leg has nothing to falsify")
        control, control_rev = fallback
        prior = revision_asset(control_rev + "^", control)
    raw, _ = cs.served_copy_cooled(control, index)
    less, more = grade(colours(prior), raw or "")
    verdict = "DIFFERS as it must" if (less or more) else "READS CLEAN -- THE PROBE IS DEAD"
    note = "" if control_rev == baseline else \
        "  [no recolour in this round: falsified against the last commit that moved colours]"
    print("control: %s graded as %s -> %s (short %d, extra %d)%s"
          % (control, control_rev, verdict, sum(less.values()), sum(more.values()), note))

    print("\nserved-colour parity: assets=%d reached=%d mismatched=%d unreachable=%d "
          "min-reached=%d" % (len(names), reached, len(bad), len(unreachable), args.min_reached))
    # `--min-reached` prices fetch success, not the size of this round's work list -- see
    # `coverage_call()` for why the two must not share an exit code.
    passed, note = coverage_call(len(names), reached, args.min_reached)
    if note:
        print(note)
    if bad or unreachable or not passed or not (less or more):
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
