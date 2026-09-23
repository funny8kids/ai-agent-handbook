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

The control leg is the point of the file: the previous revision's drawing is graded against the same
served bytes and MUST differ. Without it a green run cannot be told apart from a CDN serving a stale
build, since both leave "some blues are present" true. `--control-asset` names the figure to grade
that way (default: the first one scanned, which is enough -- the failure mode is a whole-site stale
build, not one lagging file).

Coverage is a separate bucket from findings, per the round-60/67 rule: an asset whose fetch never
landed is not a pass, and a run that reaches only part of the sample refuses to claim the tree is
clean (`--min-reached`, default 10).

URLs are never guessed: the page address comes from `llms.txt` by published title, and the asset
address is read off the `<img>` on that page (the `~gitbook/image` proxy -- `.gitbook/assets/*` 404s
on the live host).

Usage:
    python tools/checks/check_svg_served_colours.py
    python tools/checks/check_svg_served_colours.py --assets 04-react-loop.svg 08-collab-patterns.svg
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", nargs="*", default=None)
    ap.add_argument("--min-reached", type=int, default=10)
    ap.add_argument("--control-asset", default=None)
    args = ap.parse_args()

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

    # Control: grade the PREVIOUS drawing against the same served bytes. If it also reads equal,
    # this axis cannot tell a fresh build from a stale one and its green means nothing.
    control = args.control_asset or names[0]
    prior = revision_asset(baseline, control)
    # A control that cannot fail is not a control: if the previous revision is missing or byte-equal,
    # "DIFFERS" would be vacuous and the whole axis would be unreadable as evidence.
    assert prior and prior != io.open(os.path.join(cs.ASSETS, control), encoding="utf-8").read(), \
        "control asset %s has no differing %s revision -- the falsification leg is dead" % (control, baseline)
    raw, _ = cs.served_copy_cooled(control, index)
    less, more = grade(colours(prior), raw or "")
    print("control: %s graded as %s -> %s (short %d, extra %d)"
          % (control, baseline, "DIFFERS as it must" if (less or more) else "READS CLEAN -- THE PROBE IS DEAD",
             sum(less.values()), sum(more.values())))

    print("\nserved-colour parity: assets=%d reached=%d mismatched=%d unreachable=%d "
          "min-reached=%d" % (len(names), reached, len(bad), len(unreachable), args.min_reached))
    if bad or unreachable or reached < args.min_reached or not (less or more):
        if reached < args.min_reached:
            print("COVERAGE failure (not a content finding): the sample was never reached -- rerun.")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
