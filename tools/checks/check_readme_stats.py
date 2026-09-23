"""Reconcile the GitHub README badges + prose counts with the actual docs/ tree.

Every number a reader sees on the first screen is re-derived here from the file tree, so a
round that adds pages or figures without touching the badges fails this check.

Scope rules (deliberately explicit — the book's stats are methodology-sensitive):
  pages      all docs/**.md minus SUMMARY.md and asset MANIFEST.md files
  chapters   numbered top-level dirs 01..NN, excluding 00-* (index) and 99-* (about)
  math       pages with >=1 paired $$...$$ after stripping fenced code AND inline code;
             the authoritative *formula* count is the katex render judge, not this ruler
  figures    mermaid blocks + distinct SVG/PNG assets actually referenced by body pages
  labs       docs/19-labs/labN-*.md
  shots      distinct PNGs under assets/screenshots/

Controls: a non-vacuity floor per metric, one hit control (a hand-picked page each ruler
must see) and one phantom control (a mutated README must be flagged). A metric that
measures 0 while the floor expects content is an error, not a pass.

Three surfaces are reconciled, not two: the GitHub README, the GitBook homepage prose, and the
cover banner SVG. The last one is an image, so nothing above ever read its numbers and it stated a
page count nine rounds out of date (round 64) — its claims are parsed out of the <text> nodes and
the phantom control replays that exact staleness.
"""
import os
import re
import sys

REPO = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + "/../..")
DOCS = os.path.join(REPO, "docs")
README = os.path.join(REPO, "README.md")

NON_BODY = ("SUMMARY.md", "MANIFEST.md")
INLINE_CODE = re.compile(r"``.+?``|`[^`\n]*`")
FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def body_pages():
    pages = []
    for dirpath, dirnames, filenames in os.walk(DOCS):
        if "14-templates" in dirpath.replace("\\", "/").split("/"):
            continue
        for fn in filenames:
            if fn.endswith(".md") and fn not in NON_BODY:
                pages.append(os.path.join(dirpath, fn))
    return sorted(pages)


def all_md():
    return sorted(os.path.join(d, f) for d, _, fs in os.walk(DOCS) for f in fs
                  if f.endswith(".md"))


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def outside_fences(text):
    out, open_tok = [], None
    for line in text.split("\n"):
        m = FENCE_LINE.match(line)
        if m:
            tok = m.group(1)[0] * 3
            if open_tok is None:
                open_tok = tok
            elif line.strip().startswith(open_tok) and line.strip().rstrip("`~") == "":
                open_tok = None
            out.append("")
            continue
        out.append("" if open_tok else line)
    return "\n".join(out)


def math_pairs(text):
    """Paired block-level $$...$$ outside code fences and inline code spans."""
    stripped = INLINE_CODE.sub("", outside_fences(text))
    return [m for m in re.findall(r"\$\$(.*?)\$\$", stripped, flags=re.S) if m.strip()]


def measure():
    stats = {}
    md = all_md()
    stats["pages"] = len([p for p in md if os.path.basename(p) not in NON_BODY])
    stats["chapters"] = len([d for d in os.listdir(DOCS)
                             if re.fullmatch(r"(?!00|99)\d{2}-[^/]+", d)
                             and os.path.isdir(os.path.join(DOCS, d))])

    stats["math"] = sum(1 for p in body_pages() if math_pairs(read(p)))

    mermaid = 0
    svg_ref, png_ref, ghost_ref = set(), set(), set()
    for p in body_pages():
        text = read(p)
        mermaid += len(re.findall(r"^ {0,3}```mermaid", text, flags=re.M))
        rel_dir = os.path.relpath(os.path.dirname(p), DOCS).replace("\\", "/")
        for src in IMG.findall(text):
            if "?" in src:
                src = src.split("?")[0]
            if not (src.endswith(".svg") or src.endswith(".png")):
                continue
            norm = os.path.normpath(os.path.join(rel_dir, src)).replace("\\", "/")
            # A reference to an asset that isn't on disk is a teaching example, not a figure
            # (the changelog quotes `../.gitbook/assets/xxx.svg` as a negative sample).
            if not os.path.isfile(os.path.join(DOCS, norm)):
                ghost_ref.add(norm)
                continue
            (svg_ref if src.endswith(".svg") else png_ref).add(norm)
    stats["figures"] = mermaid + len(svg_ref) + len(png_ref)
    stats["mermaid"], stats["svg"], stats["png"] = mermaid, len(svg_ref), len(png_ref)
    stats["ghosts"] = len(ghost_ref)

    stats["labs"] = len([p for p in os.listdir(os.path.join(DOCS, "19-labs"))
                         if re.fullmatch(r"lab\d+-.*\.md", p)])
    shot_dir = os.path.join(DOCS, ".gitbook", "assets", "screenshots")
    stats["shots"] = len([f for f in os.listdir(shot_dir) if f.endswith(".png")])
    return stats


# --- the README side: badges carry alt text, prose states the page/chapter count once ---

BADGE = re.compile(r'alt="(Pages|Chapters|Projects|Math|Labs|Figures|Real UI screenshots)"\s+'
                   r'src="https://img\.shields\.io/badge/[a-z%0-9]+-(\d+)-')
PROSE = re.compile(r"(\d+) 页 / (\d+) 章")
PROSE_EN = re.compile(r"(\d+) pages across (\d+) chapters")

KEY_OF_ALT = {"Pages": "pages", "Chapters": "chapters", "Projects": None,
              "Math": "math", "Labs": "labs", "Figures": "figures",
              "Real UI screenshots": "shots"}


def readme_claims(text):
    claims = {KEY_OF_ALT[a]: int(n) for a, n in BADGE.findall(text) if KEY_OF_ALT[a]}
    zh, en = PROSE.search(text), PROSE_EN.search(text)
    return claims, zh, en


def check(stats, readme_text, quiet=False):
    claims, zh, en = readme_claims(readme_text)
    problems = []
    if len(claims) < 5:
        problems.append("badge parser found only %d of the >=5 expected badges: %s"
                        % (len(claims), sorted(claims)))
    for key, want in sorted(claims.items()):
        got = stats[key]
        tag = "%s badge=%d measured=%d" % (key, want, got)
        if not quiet:
            print("  %-28s %s" % (tag, "ok" if want == got else "MISMATCH"))
        if want != got:
            problems.append(tag)
    for label, m in (("zh prose", zh), ("en prose", en)):
        if not m:
            problems.append("%s: no page/chapter count found in README" % label)
            continue
        got_pages, got_ch = int(m.group(1)), int(m.group(2))
        tag = "%s pages=%d chapters=%d" % (label, got_pages, got_ch)
        ok = got_pages == stats["pages"] and got_ch == stats["chapters"]
        if not quiet:
            print("  %-28s %s" % (tag, "ok" if ok else "MISMATCH"))
        if not ok:
            problems.append("%s (measured pages=%d chapters=%d)" % (tag, stats["pages"], stats["chapters"]))
    return problems


FLOORS = {"pages": 150, "chapters": 15, "math": 50, "figures": 150, "labs": 5, "shots": 5}

# The GitBook homepage restates the same numbers in prose; it must not drift from the badges.
HOMEPAGE_CLAIMS = [
    ("pages", re.compile(r"\*\*(\d+) 页 / \d+ 章\*\*")),
    ("chapters", re.compile(r"\*\*\d+ 页 / (\d+) 章\*\*")),
    ("math", re.compile(r"\*\*(\d+) 篇页面含 KaTeX 公式")),
    ("mermaid", re.compile(r"全书 (\d+) 张 Mermaid 图")),
    ("figures", re.compile(r"\*\*(\d+) 张页内配图\*\*")),
    ("mermaid", re.compile(r"页内配图\*\*：(\d+) 个 Mermaid 内联图")),
    ("svg", re.compile(r"\+\s*(\d+) 张页内自绘 SVG")),
    ("shots", re.compile(r"\+\s*\*\*(\d+) 张真实产品界面截图")),
]
HOMEPAGE = os.path.join(DOCS, "README.md")


def check_homepage(stats, text=None, quiet=False):
    text = read(HOMEPAGE) if text is None else text
    problems, seen = [], 0
    for key, pat in HOMEPAGE_CLAIMS:
        m = pat.search(text)
        if not m:
            problems.append("homepage: claim pattern %r no longer matches" % pat.pattern)
            continue
        seen += 1
        want, got = int(m.group(1)), stats[key]
        tag = "homepage %s=%d measured=%d" % (key, want, got)
        if not quiet:
            print("  %-40s %s" % (tag, "ok" if want == got else "MISMATCH"))
        if want != got:
            problems.append(tag)
    assert seen >= len(HOMEPAGE_CLAIMS) - 1, "homepage parser is vacuous"
    return problems


# The cover banner states the same two numbers as prose, but it is an image: no parser above ever
# read it, so it kept saying "187 页" for nine rounds under a page whose own headline said 196.
# Round 64's live screenshot of the homepage is what caught it.
BANNER = os.path.join(DOCS, ".gitbook", "assets", "banner-home.svg")
BANNER_TEXT = re.compile(r">([^<>]*)<")
BANNER_CLAIMS = [
    ("pages", re.compile(r"(\d+) 页 / \d+ 章")),
    ("chapters", re.compile(r"\d+ 页 / (\d+) 章")),
    ("chapters", re.compile(r"(\d+) 章 · \d+ 页全景")),
    ("pages", re.compile(r"\d+ 章 · (\d+) 页全景")),
]


def check_banner(stats, text=None, quiet=False):
    text = read(BANNER) if text is None else text
    # Only the drawn strings are claims — x="196" is a coordinate, not a page count.
    body = " ".join(BANNER_TEXT.findall(text))
    problems, seen = [], 0
    for key, pat in BANNER_CLAIMS:
        m = pat.search(body)
        if not m:
            problems.append("banner: claim pattern %r no longer matches" % pat.pattern)
            continue
        seen += 1
        want, got = int(m.group(1)), stats[key]
        tag = "banner %s=%d measured=%d" % (key, want, got)
        if not quiet:
            print("  %-40s %s" % (tag, "ok" if want == got else "MISMATCH"))
        if want != got:
            problems.append(tag)
    assert seen == len(BANNER_CLAIMS), "banner parser is vacuous (%d of %d)" % (seen, len(BANNER_CLAIMS))
    return problems


HIT_CONTROLS = [
    ("docs/03-llm/transformer-attention.md", "math"),
    ("docs/19-labs/lab1-react.md", "pages"),
    ("docs/.gitbook/assets/screenshots", "shots"),
]


def run_controls(stats):
    for key, floor in FLOORS.items():
        assert stats[key] >= floor, "vacuity: %s measured %d below floor %d" % (key, stats[key], floor)
    assert stats["ghosts"] >= 1, \
        "ghost-asset control lost: no nonexistent image reference is being excluded"
    bad = read(README).replace("pages-196", "pages-999", 1)
    bad = bad.replace("196 页 / 19 章", "1 页 / 1 章", 1)
    problems = check(stats, bad, quiet=True)
    assert any("pages badge=999" in p for p in problems), \
        "phantom control failed: a bogus page badge was not flagged (%s)" % problems
    assert any("zh prose" in p for p in problems), \
        "phantom control failed: a bogus prose page count was not flagged (%s)" % problems
    assert len(readme_claims(read(README))[0]) >= 5, \
        "badge parser is broken on the real README — controls would be meaningless"
    home_bad = read(HOMEPAGE).replace("**257 张页内配图**", "**999 张页内配图**", 1)
    hp = check_homepage(stats, home_bad, quiet=True)
    assert any("homepage figures=999" in p for p in hp), \
        "phantom control failed: a bogus homepage figure count slipped through (%s)" % hp
    # The control replays this round's actual defect: the banner said 187 while the tree said 196.
    ban_bad = read(BANNER).replace("196 页", "187 页")
    bp = check_banner(stats, ban_bad, quiet=True)
    assert sum(1 for p in bp if p.startswith("banner pages")) == 2, \
        "phantom control failed: a stale banner page count was not flagged in both places (%s)" % bp
    for rel, metric in HIT_CONTROLS:
        path = os.path.join(REPO, rel)
        if metric == "shots":
            assert os.path.isdir(path) and stats["shots"] > 0, "hit control lost %s" % rel
            continue
        assert os.path.isfile(path), "hit control missing %s" % rel
        stripped = math_pairs(read(path))
        if metric == "math":
            assert stripped, "hit control: %s should count as a math page" % rel
    print("controls: floors ok, ghost refs excluded, 4 phantoms flagged, hit controls found")


def main():
    stats = measure()
    print("measured:", ", ".join("%s=%d" % kv for kv in sorted(stats.items())))
    run_controls(stats)
    problems = check(stats, read(README)) + check_homepage(stats) + check_banner(stats)
    if problems:
        print("\nREADME/homepage/banner are out of sync with the tree:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nREADME, homepage and cover banner match the tree on every axis.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
