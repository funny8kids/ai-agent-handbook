"""Round 92 mechanism: run *every* axis in this directory, so "which axes exist" is a glob.

Why this file exists: `check_figure_explanations.py` is the judge behind the homepage sentence
「217 张 Mermaid，171 张带图注、46 张靠引导语」, and it had not been executed since the round that
landed it. From round 88 onward it raised AssertionError on its own alt-text allow-list, and
because a round's battery is a hand-typed list of names, that exception was never seen — four
rounds of green summaries covered a ruler that measured nothing, and the two guards stacked under
its exception (dead image paths, `placements == 45`) stopped executing with it.

So the bug was the per-round list. This runner takes its work list from the directory: a new axis
is covered the moment it lands, and a stale one cannot quietly drop out.

Usage:
    python tools/checks/run_battery.py --selftest   # prove the work-list discovery still covers the dir
    python tools/checks/run_battery.py                 # everything, default mode per axis
    python tools/checks/run_battery.py --list           # just the discovered work list
    python tools/checks/run_battery.py --only structure --only widget   # substring filter
    python tools/checks/run_battery.py --skip live      # skip the browser legs (fast offline pass)
    python tools/checks/run_battery.py --args --live    # extra args handed to every axis
    python tools/checks/run_battery.py --help           # this usage
Exit code is 0 only when every axis that ran exited 0; a timeout is reported as its own result,
never folded into "passed". A flag this runner does not know is a red exit 2, never a silent
"then run everything" -- round 95 measured `--help` starting a full live sweep for that reason.
"""
import io
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TIMEOUT = int(os.environ.get("BATTERY_TIMEOUT", "3000"))
# The naming rule in this directory is `check_*`, but this one axis predates it and is real (the
# SSR structure parity scan, also the home of the shared inline-code tokenizer). Listing it here is
# what lets the selftest assert that the split covers the directory instead of trusting a glob.
EXTRA_AXES = {"live_aria_manifest"}
# This runner is not a check; running it would re-enter the battery.
EXCUSED = {"run_battery"}


def runnable(name):
    path = os.path.join(HERE, name + ".py")
    return os.path.isfile(path) and "__main__" in io.open(path, encoding="utf-8").read()


def pyfiles():
    return sorted(fn[:-3] for fn in os.listdir(HERE) if fn.endswith(".py"))


def axes():
    """Every runnable file this directory holds, bar the shared modules and the excuses."""
    return [n for n in pyfiles() if (n.startswith("check_") or n in EXTRA_AXES)
            and n not in EXCUSED and runnable(n)]


def unregistered():
    """Runnable files the work list does not cover.

    The selftest insists this stays empty: a new axis that skips the naming rule would otherwise
    join the four-round silence this runner exists to end, and `libs` (no `__main__`) is the only
    legitimate reason not to run a file here.
    """
    work = axes()
    return [n for n in pyfiles() if n not in work and n not in EXCUSED and runnable(n)]


def libs():
    return [n for n in pyfiles() if not runnable(n)]


def child_env():
    """Children write UTF-8 into their logs no matter what the console's code page is.

    Round 97: on this box the code page is cp936, so an axis that prints a CJK reading redirected
    its own log in cp936. The runner then decoded those bytes as UTF-8 with `errors="replace"`,
    got U+FFFD, and the next print raised `UnicodeEncodeError` — killing the pass at axis 15 of 35
    while the axes that never ran sat behind a summary line that had no idea they were missing.
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def emit(stream, name, code, elapsed, reading):
    """One result line, written so that no possible reading can abort the loop.

    Encoding the line to the stream's own codec with `errors="replace"` and back leaves real text
    (CJK included) untouched and turns only the characters the console cannot hold into '?'.
    """
    line = "%-6s %-38s exit=%-4s %3ds  %s" % (
        "ok" if code == 0 else "RED", name, code, elapsed, reading[:110])
    enc = getattr(stream, "encoding", None) or "utf-8"
    stream.write(line.encode(enc, "replace").decode(enc, "replace") + "\n")
    stream.flush()
    return line


def run_one(name, extra, logdir):
    path = os.path.join(HERE, name + ".py")
    log = os.path.join(logdir, name + ".log")
    started = time.time()
    with io.open(log, "wb") as fh:
        try:
            proc = subprocess.Popen([sys.executable, path] + extra, cwd=ROOT,
                                    stdout=fh, stderr=subprocess.STDOUT, env=child_env())
            code = proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            code = "TIMEOUT>%ds" % TIMEOUT
    elapsed = int(time.time() - started)
    reading = ""
    for line in io.open(log, encoding="utf-8", errors="replace").read().splitlines()[::-1]:
        if line.strip():
            reading = line.strip()
            break
    return code, elapsed, log, reading


def selftest():
    """The runner's own guard: work-list discovery must not be able to shrink in silence.

    Both directions are planted — a real axis must be found, and the one shared module in this
    directory must not be run as if it were an axis. The equality is the exhaustiveness of the
    split (every `check_*.py` is either work or excluded), which is the one claim here that prose
    cannot move.
    """
    found = axes()
    assert len(found) >= 30, ("vacuity: only %d axes discovered (%s) — a runner that quietly stops "
                              "finding axes reports green for a shrinking set" % (len(found), found[:3]))
    for known in ("check_structure", "check_figure_explanations", "check_emphasis_flanking",
                  "live_aria_manifest"):
        assert known in found, "the work list lost %s" % known
    assert not unregistered(), ("runnable files are outside the work list: %s" % unregistered())
    assert "check_wide_layout_ab" in libs(), "a shared module is being run as an axis"
    # ...and a filter that matches nothing must not be reportable as a green battery.
    assert not [n for n in found if "no-such-axis" in n], "an empty work list is not a pass"
    assert sorted(found + unregistered() + libs() + sorted(EXCUSED)) == pyfiles(), \
        "the axis/excluded split does not cover the directory"
    # The same rule the work list obeys applies to the flags: input this runner does not understand
    # must be a red exit, not a default. Each of these is what round 95 actually typed or nearly
    # typed; before the guard existed every one of them started the whole battery.
    for typo in (["--help-me"], ["--nope"], ["--only"], ["--skip"], ["--logdir"], ["structure"]):
        try:
            parse_flags(typo)
        except ValueError:
            pass
        else:
            raise AssertionError("parse_flags(%s) was accepted — an unknown flag must not fall "
                                 "through to a full battery" % (typo,))
    assert parse_flags(["--help"])[0] == "help" and parse_flags(["-h"])[0] == "help", \
        "--help must print the usage"
    assert parse_flags([])[0] is None, "no flags is the one legitimate full run"
    assert parse_flags(["--args", "--live", "--not-my-flag"])[1] == ["--live", "--not-my-flag"], \
        "past --args the flags belong to the axes, not to this runner"
    assert parse_flags(["--only", "structure,widget"])[2] == ["structure", "widget"], \
        "a comma list is how a filter gets written by hand"
    assert parse_flags(["--skip", "live", "--logdir", "/tmp/b"])[3:] == (["live"], "/tmp/b")
    # And the loop itself must not be killable by what an axis printed (round 97 killed 20 axes
    # this way). Both directions: the raw reading must raise on a strict console — proving that
    # console really cannot encode it — while `emit` must clear that same console untouched.
    unreadable = "problems=102 未闭合 \ufffd\ufffd"
    strict = io.TextIOWrapper(io.BytesIO(), encoding="ascii", errors="strict")
    try:
        strict.write(unreadable)
        strict.flush()
    except UnicodeEncodeError:
        pass
    else:
        raise AssertionError("the strict console accepted an unencodable reading, so the emit-side "
                             "control below proves nothing")
    emit(strict, "check_x", 0, 1, unreadable)
    strict.flush()
    assert b"problems=102" in strict.buffer.getvalue(), "the reading must still reach the console"
    assert b"\xff" not in strict.buffer.getvalue(), "unencodable characters must become '?', not bytes"
    # The child side of the same bug: axes must be told to write UTF-8, or their logs are in the
    # console's code page and this runner's decode is a guess.
    assert child_env()["PYTHONIOENCODING"] == "utf-8", "children would log in the code page again"
    assert "PYTHONIOENCODING" not in os.environ or os.environ["PYTHONIOENCODING"] != "cp936", \
        "the runner overrides it either way; this line only records the box's default"
    print("battery controls: OK (axes=%d libs=%d unregistered=%d)"
          % (len(found), len(libs()), len(unregistered())))


def parse_flags(argv):
    """(mode, extra, only, skip, logdir). `mode` is None (run), "selftest", "list" or "help".

    An unrecognised flag raises instead of falling through to a full battery: round 95 typed
    `--help` here, got no such option message from nobody, and started every axis in the
    directory - live legs included, which then starved the sync probe that same round. Unknown
    input reading as "the default, run everything" is the silent-green class this file exists to
    end, one level up: the work list stopped being hand-typed, and the flags stayed that way.
    Everything after `--args` is the axes' business and is handed through verbatim.
    """
    mode, extra, only, skip, logdir = None, [], [], [], None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--args":
            extra = argv[i + 1:]
            break
        elif a in ("--only", "--skip"):
            if i + 1 >= len(argv):
                raise ValueError("%s needs a value" % a)
            i += 1
            # Comma-separated as well as repeated: the natural way to write a list by hand must not
            # turn into the failure this file exists to prevent. A whole comma string is not a
            # substring of any axis name, so without the split a one-token list matched nothing and
            # the vacuity guard below fired — loudly, which is the right outcome, but a false red
            # the operator has to debug.
            (only if a == "--only" else skip).extend(s for s in argv[i].split(",") if s)
        elif a == "--logdir":
            if i + 1 >= len(argv):
                raise ValueError("--logdir needs a path")
            i += 1
            logdir = argv[i]
        elif a == "--selftest":
            mode = "selftest"
            break
        elif a == "--list":
            mode = "list"
            break
        elif a in ("-h", "--help"):
            mode = "help"
            break
        else:
            raise ValueError("unknown flag %r for run_battery.py (its own flags stop at --args; "
                             "see --help)" % a)
        i += 1
    return mode, extra, only, skip, logdir


def main():
    try:
        mode, extra, only, skip, logdir = parse_flags(sys.argv[1:])
    except ValueError as e:
        sys.stderr.write("%s\n" % e)
        return 2
    if mode == "help":
        print(__doc__.strip())
        return 0
    if mode == "selftest":
        selftest()
        return 0
    if mode == "list":
        for n in axes():
            print(n)
        print("# shared modules (no __main__): %s" % (", ".join(libs()) or "none"))
        print("# runnable but outside the work list: %s" % (", ".join(unregistered()) or "none"))
        return 0
    logdir = logdir or os.path.join(os.environ.get("TEMP", "/tmp"), "battery")
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    work = [n for n in axes()
            if (not only or any(s in n for s in only)) and not any(s in n for s in skip)]
    bad, codes = [], {}
    for name in work:
        code, elapsed, log, reading = run_one(name, extra, logdir)
        codes[name] = code
        emit(sys.stdout, name, code, elapsed, reading)
        if code != 0:
            bad.append(name)
    # Vacuity guard: a battery that ran nothing is not green, and a filter typo must show up here.
    assert work, "empty work list: the --only/--skip filters matched no axis"
    print("battery: discovered=%d ran=%d non-zero=%d logdir=%s"
          % (len(work), len(codes), len(bad), logdir))
    for n in bad:
        print("  RED %s -> %s" % (n, os.path.join(logdir, n + ".log")))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
