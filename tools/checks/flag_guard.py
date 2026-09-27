"""A flag an axis does not parse must cost the caller, not quietly run the default pass.

Round 96 found this in `run_battery.py` (`--help` ran the whole battery), round 101 found the same
shape in `check_link_graph.py` (`--help` printed a complete cached verdict as though the leg the
caller asked for had run). Hand-scanning argv has no default rejection: argparse exits 2 on an
unknown flag, while `if "--x" in args` simply does not match and execution falls through.

The fall-through is worst on the flags that *widen coverage* (`--all`, `--sample`, `--live`,
`--controls`): a mistyped one narrows the judged set back to the default sample, and the axis then
prints its ordinary green reading for work it never did. A reader cannot tell that apart from a
pass, so the refusal has to happen before any leg runs.

An axis uses it as the first statement of its `main`, then picks its own exit code:

    from flag_guard import reject_unknown
    if reject_unknown(sys.argv[1:], FLAGS, os.path.basename(__file__)):
        return 2

2 means "no verdict was produced", which is how the battery already reads a broken instrument
rather than a content defect. `run_battery.py --selftest` drives this rule over the whole directory
instead of trusting a list, so an axis that forgets the guard reddens that control.
"""

import sys


def unknown_flags(argv, known):
    return [a for a in argv if a.startswith("--") and a not in known]


def reject_unknown(argv, known, axis):
    """True when something was refused; the caller must then exit without judging anything."""
    bad = unknown_flags(argv, known)
    if bad:
        print("%s: unknown flag(s): %s; this axis %s"
              % (axis, ", ".join(bad),
                 "takes no flags at all" if not known else "knows only " + ", ".join(sorted(known))),
              file=sys.stderr)
    return bool(bad)
