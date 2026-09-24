# -*- coding: utf-8 -*-
"""Round 80 axis: the homepage says 「六个实验的脚本仍在仓库 labs/ 下可离线真跑，页面按路径指过去」.

Nothing in tools/checks had ever executed a lab. This is the same defect class as rounds 57 / 76 / 77 /
78 / 79 -- a self-descriptive sentence with no machine behind it -- with one difference worth naming:
this claim is about *behaviour*, so the judge has to run the thing rather than read the tree.

What it asserts per lab script, in a throwaway copy of `labs/` (the scripts write into their own
directory, so measuring them must not dirty tracked artifacts):

  LAB-EXIT            the process exits 0;
  LAB-EMPTY           it printed something (an exit 0 with no output proves nothing);
  LAB-NONDETERMINISTIC two consecutive runs print byte-identical stdout -- a reader following the
                      page must see the demo behave the way the page describes it;
  LAB-TIMEOUT         it finishes inside a measured budget (all six run in well under a second);
and per lab page:

  PAGE-NO-SCRIPT      the page names the script file it claims to hand over.

Run:  python tools/checks/check_lab_runnability.py
"""
import glob
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
LAB_DIR = os.path.join(REPO, "labs")
PAGES = os.path.join(REPO, "docs", "19-labs")
BUDGET = 120          # seconds per script; measured worst case this round: 0.6 s
MIN_LABS = 6


def run_twice(script, workdir):
    outs = []
    for _ in range(2):
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, os.path.basename(script)], cwd=workdir,
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=BUDGET)
            outs.append((p.returncode, p.stdout or "", p.stderr or "", time.time() - t0))
        except subprocess.TimeoutExpired:
            outs.append((-1, "", "TIMEOUT after %ds" % BUDGET, time.time() - t0))
    return outs


def norm_newlines(s):
    """Windows translates print()'s "\\n" to "\\r\\n" on a piped stdout; the committed records are LF.

    Without this every record reads stale for a reason that has nothing to do with the lab.
    """
    return (s or "").replace("\r\n", "\n").strip()


def judge(workdir, scripts, pages_dir, records_dir=None):
    findings, stats = [], {"labs": 0, "exit0": 0, "deterministic": 0, "lines": 0, "worst_s": 0.0,
                           "pages": 0, "pages_naming_script": 0, "records": 0, "records_current": 0}
    for script in scripts:
        stats["labs"] += 1
        name = os.path.basename(script)
        (rc1, out1, err1, s1), (rc2, out2, err2, s2) = run_twice(script, workdir)
        stats["worst_s"] = max(stats["worst_s"], s1, s2)
        if rc1 != 0 or rc2 != 0:
            findings.append("LAB-EXIT %s exited %s/%s: %s" % (name, rc1, rc2, (err1 or err2)[-160:]))
            continue
        stats["exit0"] += 1
        if not out1.strip():
            findings.append("LAB-EMPTY %s exited 0 but printed nothing to stdout" % name)
            continue
        if out1 != out2:
            findings.append("LAB-NONDETERMINISTIC %s: two runs differ (%dB vs %dB)"
                            % (name, len(out1), len(out2)))
            continue
        stats["deterministic"] += 1
        stats["lines"] += len(out1.splitlines())
        # The repo keeps a committed transcript per lab under labs/out/. It is the evidence a reader
        # is pointed at, so it has to be what the script prints today -- an earlier round found
        # lab3.out still carrying pre-fix output. A record that drifts is a lie in the tree, not a
        # cosmetic diff.
        if records_dir:
            stem = re.match(r"(lab\d+)", name).group(1)
            rec = os.path.join(records_dir, stem + ".out")
            if os.path.isfile(rec):
                stats["records"] += 1
                committed = io.open(rec, encoding="utf-8", errors="replace").read()
                if norm_newlines(committed) == norm_newlines(out1):
                    stats["records_current"] += 1
                else:
                    findings.append("OUT-STALE labs/out/%s.out does not match a fresh run of %s "
                                    "(committed %d lines vs %d)"
                                    % (stem, name, len(committed.splitlines()), len(out1.splitlines())))
    for page in sorted(glob.glob(os.path.join(pages_dir, "lab*.md"))):
        stats["pages"] += 1
        text = io.open(page, encoding="utf-8").read()
        base = os.path.splitext(os.path.basename(page))[0]          # lab1-react
        stem = base.split("-")[0]                                    # lab1
        names = [os.path.basename(s) for s in scripts
                 if re.match(r"^%s([-_].*)?\.py$" % stem, os.path.basename(s))]
        if names and any(n in text for n in names):
            stats["pages_naming_script"] += 1
        else:
            findings.append("PAGE-NO-SCRIPT %s names none of %s" % (os.path.basename(page), names))
    return findings, stats


def run():
    sandbox = os.path.join(tempfile.mkdtemp(prefix="r80labs"), "labs")
    shutil.copytree(LAB_DIR, sandbox, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    scripts = sorted(glob.glob(os.path.join(sandbox, "lab*.py")))
    try:
        findings, stats = judge(sandbox, scripts, PAGES, os.path.join(LAB_DIR, "out"))
    finally:
        shutil.rmtree(os.path.dirname(sandbox), ignore_errors=True)
    print("lab runnability: labs=%d exit0=%d deterministic=%d stdout_lines=%d worst=%.2fs "
          "pages=%d pages_naming_script=%d records_current=%d/%d findings=%d"
          % (stats["labs"], stats["exit0"], stats["deterministic"], stats["lines"],
             stats["worst_s"], stats["pages"], stats["pages_naming_script"],
             stats["records_current"], stats["records"], len(findings)))
    for f in findings:
        print("  " + f)
    return stats, findings


# --------------------------------------------------------------------------- controls
PLANTS = {
    "lab11_ok.py": "print('step 1')\nprint('step 2')\n",
    "lab12_fails.py": "import sys\nprint('before the crash')\nsys.exit(3)\n",
    "lab13_silent.py": "x = 1 + 1\n",
    "lab14_random.py": "import random\nprint(random.random())\n",
    "lab15_stale.py": "print('the output today')\n",
}


def controls():
    """Each defect must fire on a planted script, and the clean one must not fire at all."""
    work = tempfile.mkdtemp(prefix="r80ctrl")
    rec = os.path.join(work, "out")
    os.makedirs(rec)
    try:
        for name, src in PLANTS.items():
            io.open(os.path.join(work, name), "w", encoding="utf-8").write(src)
        io.open(os.path.join(rec, "lab11.out"), "w", encoding="utf-8").write("step 1\nstep 2\n")
        io.open(os.path.join(rec, "lab15.out"), "w", encoding="utf-8").write("an older run\n")
        scripts = [os.path.join(work, n) for n in sorted(PLANTS)]
        findings, stats = judge(work, scripts, HERE, rec)   # no pages here: page leg sees 0 pages
        got = " ".join(findings)
        assert "LAB-EXIT lab12_fails.py" in got, "control blind: a script exiting 3 passed"
        assert "LAB-EMPTY lab13_silent.py" in got, "control blind: a silent exit-0 script passed"
        assert "LAB-NONDETERMINISTIC lab14_random.py" in got, \
            "control blind: an unseeded random script looked deterministic"
        assert "OUT-STALE labs/out/lab15.out" in got, \
            "control blind: a committed transcript that no longer matches passed"
        assert "lab11" not in got.replace("lab11.out", ""), \
            "control: the clean planted lab (matching record) was flagged: %s" % got
        assert stats["records"] == 2 and stats["records_current"] == 1, stats
        assert stats["exit0"] == 4 and stats["deterministic"] == 2, stats
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 6


def main():
    n = controls()
    stats, findings = run()
    print("controls ok (%d planted: clean lab, exit 3, silent, unseeded-random, "
          "a stale committed transcript, and a matching one that must pass)" % n)
    # Non-vacuity: a green that comes from an empty sample is not green.
    assert stats["labs"] >= MIN_LABS, "only %d lab scripts found under labs/" % stats["labs"]
    assert stats["pages"] >= MIN_LABS, "only %d lab pages found" % stats["pages"]
    assert stats["exit0"] == stats["labs"], "some lab did not run: %d/%d" % (stats["exit0"], stats["labs"])
    assert stats["deterministic"] == stats["labs"], "some lab is not reproducible"
    assert stats["pages_naming_script"] == stats["pages"], "a lab page stopped pointing at its script"
    assert stats["records"] >= MIN_LABS, "only %d committed transcripts found" % stats["records"]
    assert stats["records_current"] == stats["records"], \
        "%d of %d committed transcripts are stale" % (stats["records"] - stats["records_current"],
                                                      stats["records"])
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
