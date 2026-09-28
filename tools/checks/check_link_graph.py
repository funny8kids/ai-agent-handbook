# -*- coding: utf-8 -*-
"""Reader-facing link graph: does every link a reader can click land somewhere?

Two halves, because the two failure modes are different:

  internal (offline, always runs)   a relative target that no longer exists, a body page that fell
                                    out of SUMMARY.md, a SUMMARY entry pointing at a deleted page.
  external (cached verdicts)        a citation whose URL went dead, moved house, or 200-OKs onto a
                                    "page not found" template.

Rounds 1/13/17/21/22/25 each audited pieces of this with throwaway scripts and none of it survived
in tools/checks, so "断链与孤儿页" was a line in a round plan and nothing else: a link broken by a
later rename stayed invisible until someone happened to re-audit. This is the resident judge for
that axis — the same class as rounds 57/76/77/78/79/80 (an assertion the homepage makes that no
machine can re-run).

Anchor fragments are graded against the PLATFORM, not against a slug rule invented here. Measured
live: GitBook transliterates CJK headings into pinyin (「快速开始 · Quick start」 ->
`kuai-su-kai-shi-quick-start`; 「第 1 步：先立考题——4 道题…」 -> `di-1-bu-xian-li-kao-ti-4-dao-ti-…`),
prefixes a digit-initial heading with `id-`, and gives the page H1 no id at all. Re-implementing
that offline needs a pinyin table and would drift with the platform, so the offline leg does NOT
judge fragments; `--live` asks the target page which ids it actually publishes. That is why
`--live` is this axis's standing read: without it the fragment count is reported, not graded.

External verdicts live in tools/checks/data/external_links.json because a rate-limited probe must
never be able to produce a false green. `--refresh` is the only leg that probes (and it retries
network trouble once after a cooldown: the first pass at 8 workers returned 31
`WinError 10054`/SSL-EOF readings that were the probe's rate, not the book's — round 67's asset leg
made the same mistake). A cited URL with no cached entry is a COVERAGE failure, not a pass.

The tokenizer reads `[label](target)` AND bare `<https://…>` autolinks. That second shape was added
in round 81 after this file's own adoption gate disagreed with a grep over the same pages: the
resource-index tables are built out of autolinks, and 98 clickable occurrences / 54 distinct URLs
(1428→1526 external, 663→717 distinct) were prose to a `[..](..)`-only regex. A judge that cannot
see a link cannot call it dead, and its coverage floors would still read green. Those four numbers
were re-measured after the round's own edits (HEAD's tree through both tokenizers: 1428/663 narrow,
1526/717 wide, 93 URLs cited the autolink way and 54 of them never the narrow way) — a rounding
error in prose here would be exactly the kind of claim this file exists to stop making.

Usage:
  python tools/checks/check_link_graph.py             offline graph + cached verdicts
  python tools/checks/check_link_graph.py --live      + grade anchor fragments on the site
  python tools/checks/check_link_graph.py --refresh   + (re)probe external URLs, throttled
  python tools/checks/check_link_graph.py --selftest  planted phantoms for every bucket
Anything else starting with `--` exits 2 rather than quietly running the default pass.
"""
import datetime
import io
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from live_aria_manifest import prose, url_index, norm, h1_of  # noqa: E402  one prose ruler
from flag_guard import reject_unknown  # noqa: E402  the same rule for every hand-scanned argv
import wire_decode as wire  # noqa: E402  every reader-page read asks for the body compressed

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
CACHE = os.path.join(HERE, "data", "external_links.json")
NON_BODY = ("SUMMARY.md", "MANIFEST.md")
FLAGS = ("--selftest", "--refresh", "--live")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

LINK = re.compile(r"(!?)\[([^\]]*)\]\(\s*(<?[^)\s]+?>?)\s*(?:\"[^\"]*\")?\)")
AUTOLINK = re.compile(r"(?<![!\\`])<(https?://[^<>\s]+|[^<>\s|]+\.md(?:#[^<>\s]*)?|\.{1,2}/[^<>\s]+)>")
HEAD = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", re.M)

# Only some statuses are evidence about the *citation*. The rest are evidence about the host's mood
# or the probe's luck, and get their own bucket instead of a defect verdict.
DEAD_STATUS = {404, 410, 451}
BLOCK_STATUS = {401, 403, 407, 429}
HEAD_RETRY = {400, 405, 406, 501}          # HEAD not understood -> fall back to GET
SHRUG_STATUS = {500, 502, 503, 504}        # the server fell over; this says nothing about the citation
SOFT_TOKENS = ("not found", "notfound", "page not found", "页面不存在", "找不到页面", "does not exist")
# A bare "404" in a title only counts when it stands alone. arXiv titles are their own counterexample:
# 「[2404.06654] RULER: What's the Real Context Size…」 is a live paper the old substring rule read
# as a not-found page, because the submission id contains the digits 4-0-4.
SOFT_404 = re.compile(r"(?<![\d.])404(?![\d.])")
TIMEOUT = 25
THROTTLE = 0.6
COOLDOWN = 15
OK_VERDICTS = ("OK", "MOVED", "DEAD", "SOFT-404")

# Floors: a link judge that scanned nothing must not be able to read as clean. Measured on this
# ruler the round they were written (pages=196, relative=1578, distinct-external=717,
# external occurrences=1526), each set ~15-25% under its reading so real growth is free but a
# silently-narrowing scan trips.
MIN_PAGES = 190
MIN_RELATIVE = 1500
MIN_DISTINCT_EXT = 600
MIN_CITATIONS = 1200


def read(path):
    return io.open(path, encoding="utf-8").read()


def body_pages():
    rows = []
    for dirpath, dirnames, filenames in os.walk(DOCS):
        rel_dir = os.path.relpath(dirpath, DOCS).replace("\\", "/")
        if rel_dir == ".gitbook" or rel_dir.startswith(".gitbook/"):
            continue                       # asset manifests, not reader pages
        for fn in sorted(filenames):
            if fn.endswith(".md") and fn not in NON_BODY:
                rows.append(os.path.join(dirpath, fn))
    return sorted(rows)


def rel_of(path):
    return os.path.relpath(path, DOCS).replace("\\", "/")


def split_target(target):
    path, mark, frag = target.partition("#")
    return path, (frag if mark else "")


def resolve(from_path, path_part):
    """Filesystem path a relative markdown target points at, or None."""
    base = os.path.normpath(os.path.join(os.path.dirname(from_path), path_part))
    for cand in (base, base + ".md"):
        if os.path.isfile(cand):
            return cand
    if os.path.isdir(base):
        for cand in (os.path.join(base, "index.md"), os.path.join(base, "README.md")):
            if os.path.isfile(cand):
                return cand
    return None


def iter_links(path, text=None):
    """[(line_no, is_image, target)] over reader-visible prose only.

    Fences and inline code are stripped with the repo's one prose ruler: the style guide and the
    changelog *document* link syntax, and counting those would flag links no reader can click (the
    round 54/76/79 false-positive class).

    Bare `<https://…>` autolinks count too. The resource index tables are built out of them, and a
    tokenizer that only knew `[label](target)` read 98 clickable links as plain prose — the count
    disagreement that surfaced this during round 81's own adoption gate.
    """
    text = read(path) if text is None else text
    out = []
    for i, line in enumerate(prose(text).replace("\r\n", "\n").split("\n")):
        claimed = []
        for m in LINK.finditer(line):
            claimed.append((m.start(), m.end()))
            target = m.group(3)
            target = target[1:-1] if target.startswith("<") and target.endswith(">") else target
            out.append((i + 1, m.group(1) == "!", target))
        for m in AUTOLINK.finditer(line):
            if any(a <= m.start() < b for a, b in claimed):
                continue                     # already counted as the target of [label](<url>)
            out.append((i + 1, False, m.group(1)))
    return out


def listed_from_summary(summary_path=None):
    """Every body page SUMMARY.md names, resolved the same way a reader's click resolves."""
    summary_path = summary_path or os.path.join(DOCS, "SUMMARY.md")
    listed, bad = set(), []
    for ln, _img, target in iter_links(summary_path):
        path_part, _frag = split_target(target)
        if not path_part or path_part.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        hit = resolve(summary_path, path_part)
        if hit is None:
            bad.append("SUMMARY-BAD %s:%d -> %s (SUMMARY.md lists it, no such file)"
                       % (rel_of(summary_path), ln, target))
        else:
            listed.add(rel_of(hit))
    return listed, bad


def orphan_findings(body_rels, listed):
    """Pure so a control can plant a page without touching the tree."""
    out = []
    for rel in sorted(set(body_rels) - set(listed)):
        out.append("ORPHAN %s is a body page but no SUMMARY.md entry resolves to it" % rel)
    for rel in sorted(set(listed) - set(body_rels)):
        out.append("SUMMARY-STALE %s is in SUMMARY.md but no body page resolves to it" % rel)
    return out


# ---------------------------------------------------------------- internal (offline) --------

def internal_leg():
    pages = body_pages()
    summary = os.path.join(DOCS, "SUMMARY.md")
    listed, findings = listed_from_summary(summary)
    kinds = Counter()
    kinds["nav"] = sum(1 for _l, _i, t in iter_links(summary)
                       if not t.startswith(("http://", "https://", "mailto:", "tel:", "#")))
    anchors = []                                  # (page, line, target, frag, target file)
    external = defaultdict(set)                   # url -> {citing page}
    body_rels = [rel_of(p) for p in pages]

    for p in pages:
        rel = rel_of(p)
        for ln, _img, target in iter_links(p):
            if target.startswith(("http://", "https://")):
                kinds["external"] += 1
                external[target.rstrip(".,;:!?")] .add(rel)
                continue
            if target.startswith(("mailto:", "tel:", "data:")):
                kinds["mailto"] += 1
                continue
            path_part, frag = split_target(target)
            if target.startswith("#"):
                kinds["anchor-in-page"] += 1
                anchors.append((rel, ln, target, frag, p))
                continue
            kinds["relative"] += 1
            hit = resolve(p, path_part)
            if hit is None:
                findings.append("BAD-TARGET %s:%d -> %s (no such file)" % (rel, ln, target))
                continue
            if frag:
                if not hit.endswith(".md"):
                    findings.append("ANCHOR-NONMD %s:%d -> %s (fragment onto a non-markdown target)"
                                    % (rel, ln, target))
                    continue
                kinds["anchor-cross-page"] += 1
                anchors.append((rel, ln, target, frag, hit))

    findings += orphan_findings(body_rels, listed)
    stats = {"pages": len(pages), "listed": len(listed), "kinds": dict(kinds),
             "distinct_external": len(external),
             # two different counts, both useful, deliberately named apart: a page that cites the
             # same paper five times is one citing pair and five link occurrences
             "citing_pairs": sum(len(v) for v in external.values()),
             "occurrences": kinds["external"]}
    return findings, anchors, external, stats


def coverage_findings(stats):
    out = []
    if stats["pages"] < MIN_PAGES:
        out.append("COVERAGE only %d body pages scanned (floor %d)" % (stats["pages"], MIN_PAGES))
    if stats["kinds"].get("relative", 0) < MIN_RELATIVE:
        out.append("COVERAGE only %d relative links scanned (floor %d)"
                   % (stats["kinds"].get("relative", 0), MIN_RELATIVE))
    if stats["distinct_external"] < MIN_DISTINCT_EXT:
        out.append("COVERAGE only %d distinct external URLs (floor %d)"
                   % (stats["distinct_external"], MIN_DISTINCT_EXT))
    if stats["occurrences"] < MIN_CITATIONS:
        out.append("COVERAGE only %d external link occurrences (floor %d)"
                   % (stats["occurrences"], MIN_CITATIONS))
    return out


# ---------------------------------------------------------------- citation coverage --------

# 「每篇知识/资源页都有参考资料，而且里面是真能点开的来源」是首页的一条主张，此前没有任何脚本
# 复跑过它——第 76/77/85/86/99 轮反复踩过同一类账（首页印着一个没有判据的数）。这条腿把它接进本
# 文件，因为「引用了什么外部地址」的抽取器这里已经有一把（`iter_links`：剥围栏与行内代码，
# 认 `[..](..)` 也认裸 `<https://…>`），再造一把只会让两个读数分家。
CITED_TYPES = ("knowledge", "resource")
CITE_SECTION = "参考资料"
REF_CLAIM = re.compile(r"(\d+) 篇知识/资源页全部有「参考资料」[^0-9]{0,40}?(\d+) 条去重后的外部一手来源")


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def cite_sections(body):
    """Yield the raw text of every `## 参考资料` heading block in a page body."""
    heads = [(m.start(), m.group(1).strip()) for m in
             re.finditer(r"^##[ \t]+(.*?)[ \t]*$", body, re.M)]
    for k, (start, title) in enumerate(heads):
        if title != CITE_SECTION:
            continue
        end = heads[k + 1][0] if k + 1 < len(heads) else len(body)
        yield body[start:end]


def citation_leg(pages):
    """-> (findings, pages-in-scope, distinct external sources cited by those sections).

    Pure over the file list it is handed, so a control can plant a page without moving the tree.
    """
    findings, scoped, sources = [], 0, set()
    for path in pages:
        text = read(path)
        fm, body = split_frontmatter(text)
        ty = re.search(r"^type:\s*(\w+)", fm, re.M)
        if not ty or ty.group(1) not in CITED_TYPES:
            continue
        scoped += 1
        secs = list(cite_sections(body))
        cited = [t for sec in secs
                 for _l, _img, t in iter_links(path, sec)
                 if t.startswith(("http://", "https://"))]
        if not secs:
            findings.append("REF-MISSING %s has no ## %s section" % (rel_of(path), CITE_SECTION))
        elif not cited:
            findings.append("REF-EMPTY %s cites no clickable external source in %s"
                            % (rel_of(path), CITE_SECTION))
        sources.update(t.rstrip(".,;:!?") for t in cited)
    return findings, scoped, len(sources)


def homepage_ref_leg(scoped, sources, text=None):
    """Reconcile the homepage's two numbers with the tree. Overstating is a defect; a reading the
    book has simply outgrown is dated prose, not a lie — so `pages`/`sources` are floors, while the
    equality stays on the one thing writing cannot move: `REF-*` findings must be zero."""
    text = read(os.path.join(DOCS, "README.md")) if text is None else text
    m = REF_CLAIM.search(text)
    if not m:
        return ["HOMEPAGE-REF-BLIND the homepage no longer prints the 「N 篇知识/资源页…N 条去重后的"
                "外部一手来源」 reading — the counts are unprinted, not correct"]
    out = []
    for got, want, key in ((int(m.group(1)), scoped, "pages"), (int(m.group(2)), sources, "sources")):
        if got > want:
            out.append("HOMEPAGE-REF-HIGH %s: homepage says %d, tree reads %d (claiming more than "
                       "the scan found)" % (key, got, want))
        elif got < want:
            out.append("ADVISORY HOMEPAGE-REF-DATED %s: homepage says %d, tree has grown to %d — "
                       "re-anchor this round" % (key, got, want))
    return out


# ---------------------------------------------------------------- homepage claim -------------

# The homepage prints this axis's counts, and writing documentation moves several of them (a new
# page adds nav links, a new citation adds occurrences). Round 77's rule applies: a number the
# homepage is obliged to follow the tree with gets parsed out of the homepage and reconciled here,
# so "0 findings" and "the homepage prints a different number" cannot both happen.
CLAIM = re.compile(r"link-graph: (pages=\d+ relative=\d+ external=\d+ distinct=\d+ "
                   r"ok=\d+ blocked=\d+ net=\d+ unchecked=\d+ fragments=\d+)")


def measured(stats, tally, missing, anchors):
    return {"pages": stats["pages"], "relative": stats["kinds"].get("relative", 0),
            "external": stats["occurrences"], "distinct": stats["distinct_external"],
            "ok": tally.get("OK", 0), "blocked": tally.get("BLOCKED", 0),
            "net": tally.get("NET", 0), "unchecked": len(missing), "fragments": len(anchors)}


def homepage_claim_leg(stats, tally, missing, anchors, text=None):
    want = measured(stats, tally, missing, anchors)
    text = read(os.path.join(DOCS, "README.md")) if text is None else text
    m = CLAIM.search(text)
    if not m:
        return ["HOMEPAGE-BLIND the homepage no longer carries this axis's `link-graph:` reading — "
                "the counts are unprinted, not correct"], want
    got = {k: int(v) for k, v in (p.split("=") for p in m.group(1).split())}
    out = []
    for k in sorted(want):
        if got.get(k) != want[k]:
            out.append("HOMEPAGE-BADGE %s: homepage says %s, tree reads %d"
                       % (k, got.get(k), want[k]))
    return out, want


# ---------------------------------------------------------------- external (cached) ---------

def load_cache():
    if os.path.exists(CACHE):
        data = json.load(io.open(CACHE, encoding="utf-8"))
        return data.get("urls", data)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    payload = {"_note": "Verdicts for every external URL cited from docs/**.md, measured by "
                        "tools/checks/check_link_graph.py --refresh. The judge reads these; it "
                        "never invents one. Absent entry = UNCHECKED = coverage failure, not a "
                        "pass.",
               "urls": cache}
    tmp = CACHE + ".tmp"
    json.dump(payload, io.open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              sort_keys=True)
    if os.path.exists(CACHE):
        os.remove(CACHE)
    os.rename(tmp, CACHE)


def _fetch(url, method):
    # Header through the shared seam; the body deliberately is NOT run through wire.decode, because
    # this probe reads 8192 bytes and only wants the status plus the start of the document. A whole
    # page is `get_page_text`'s job — see the round-58 note below about EOFError on a cut member.
    req = urllib.request.Request(url, headers=wire.headers({"User-Agent": UA, "Accept": "*/*",
                                                             "Accept-Language": "en,zh-CN"}))
    req.get_method = lambda: method
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = ""
        if method == "GET":
            raw = r.read(8192)
            if r.headers.get("Content-Encoding") == "gzip":
                # A partial-stream inflate, deliberately: r.read(8192) truncates a compressed body,
                # and gzip.decompress() on truncated bytes raises EOFError — which read as 13
                # PROBE-ERRORs on first run, i.e. the instrument manufacturing outages.
                import zlib
                try:
                    raw = zlib.decompressobj(31).decompress(raw)
                except zlib.error:
                    raw = b""
            body = raw.decode("utf-8", "replace")
        return {"status": r.status, "final": r.geturl(), "body": body}


def get_page_text(url):
    """One whole reader page, inflated if the CDN compressed it. The anchor leg's default fetcher.

    It used to build its own request without `Accept-Encoding`, so it streamed these pages the way
    the round-count legs streamed the changelog — see wire_decode's measured table.
    """
    with urllib.request.urlopen(wire.request(url, {"User-Agent": UA}), timeout=TIMEOUT) as r:
        return wire.decode(r.headers, r.read(), url).decode("utf-8", "replace")


def sniff(res):
    m = re.search(r"<title[^>]*>(.{0,160}?)</title>", (res.get("body") or ""), re.I | re.S)
    title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    low = title.lower()
    hits = [k for k in SOFT_TOKENS if k in low]
    if SOFT_404.search(low):
        hits.append("404")
    return title, hits


def same_site(a, b):
    """www.x.com and x.com are one site; the reader clicks either and lands in the same place.

    The check has to run both ways: the round-81 first pass flagged
    https://www.eleuther.ai/community -> https://eleuther.ai/community/ as a move, because the
    old rule only forgave a redirect that *added* www.
    """
    strip = lambda h: h[4:] if h.startswith("www.") else h  # noqa: E731
    return strip(a.lower()) == strip(b.lower())


def http_error_verdict(code):
    """What a status code says about the *citation*, not about the server that answered.

    Round 101 measured the difference on this repository's own blob URLs: GitHub served 200, then
    a connection reset, then 429, then 503 to the same path within two minutes. The old mapping put
    that last one in `HTTP-503`, which the gate reads as UNREADABLE — a defect finding — so a
    transient server shrug could fail a round over a link that every reader opens fine. NET already
    means 'the probe could not look', so that is where a 5xx belongs; anything odder stays loud.
    """
    if code in DEAD_STATUS:
        return "DEAD"
    if code in BLOCK_STATUS:
        return "BLOCKED"
    if code in SHRUG_STATUS:
        return "NET"
    return "HTTP-%d" % code


def probe(url):
    """One URL -> verdict dict. Trouble is retried once after a cooldown; still-trouble stays
    inconclusive, which the coverage bucket counts and the defect bucket never does.

    HEAD answers "does this path exist". It cannot answer "does the page that arrives say
    Page not found", which is why a 200-OK HEAD is always followed by one small GET: without that,
    the SOFT-404 bucket can only ever fire on the handful of hosts that refuse HEAD.
    """
    host = url.split("/")[2]
    for attempt in range(2):
        try:
            try:
                res = _fetch(url, "HEAD")
                if res["status"] < 400:
                    res = _fetch(url, "GET")          # the title sniff needs a body
            except urllib.error.HTTPError as e:
                if e.code in HEAD_RETRY:
                    res = _fetch(url, "GET")
                elif e.code in SHRUG_STATUS and attempt == 0:
                    time.sleep(COOLDOWN)
                    continue
                else:
                    return {"verdict": http_error_verdict(e.code),
                            "status": e.code, "host": host, "final": url}
            except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError) as e:
                if attempt == 0:
                    time.sleep(COOLDOWN)
                    continue
                return {"verdict": "NET", "status": str(getattr(e, "reason", e))[:80],
                        "host": host, "final": url}
            final = res["final"]
            final_host = final.split("/")[2]
            moved = final_host != host and not same_site(host, final_host)
            title, hits = sniff(res)
            out = {"verdict": "MOVED" if moved else "OK", "status": res["status"], "host": host,
                   "final": final, "title": title[:100]}
            if res["status"] >= 300 and not moved:
                out["verdict"] = "NON2XX-%d" % res["status"]
            if hits:
                out["verdict"] = "SOFT-404"
                out["sniff"] = ",".join(hits)
            return out
        except Exception as e:  # noqa: BLE001 - one bad URL must never lose the run
            if attempt == 0:
                time.sleep(COOLDOWN)
                continue
            return {"verdict": "PROBE-ERROR", "status": repr(e)[:100], "host": host, "final": url}
    return {"verdict": "PROBE-ERROR", "status": "unreachable", "host": host, "final": url}


def our_slug():
    """`owner/repo` of the repository this check runs inside, read off git rather than off a
    constant: the rule is 'a citation into the book's own repo', and a hard-coded name rots the
    day the repo moves. None when there is no origin, which only makes the branch below inert."""
    try:
        out = subprocess.check_output(["git", "-C", REPO, "config", "--get", "remote.origin.url"],
                                      stderr=subprocess.DEVNULL, timeout=15)
    except Exception:  # noqa: BLE001 - no git, no own-repo branch
        return None
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", out.decode("utf-8", "replace").strip())
    return "%s/%s" % (m.group(1), m.group(2)) if m else None


def landed_in_tree(url, slug=None):
    """The repo-relative path a citation points at, when it cites our own repo AND that file is in
    this tree. Otherwise None.

    Round 101 needed this because the chapter's nine pages cite `.../blob/main/nano/*.py`, and the
    cache was harvested the same day, an hour before the push: GitHub answered 404 to a file that
    did not exist yet, `DEAD` is in OK_VERDICTS so `refresh` never asks again, and the axis would
    have reported five dead citations forever over links that are true at every reader since.
    Matching is by the remote's own slug, not by path shape: `torvalds/linux/blob/main/README.md`
    points at a path this tree also has, and it is not ours.
    """
    slug = slug if slug is not None else our_slug()
    if not slug:
        return None
    try:
        parsed = urlparse(url)
        parts = [unquote(p) for p in parsed.path.split("/") if p]
    except ValueError:
        return None
    host = parsed.netloc
    if host == "github.com":
        if len(parts) < 5 or parts[:2] != slug.split("/") or parts[2] not in ("blob", "tree", "raw", "edit"):
            return None
        rest = parts[4:]
    elif host == "raw.githubusercontent.com":
        if len(parts) < 4 or parts[:2] != slug.split("/"):
            return None
        rest = parts[3:]
    else:
        return None
    if not rest or os.path.isabs(rest[-1]):
        return None
    full = os.path.normpath(os.path.join(REPO, *rest))
    if not full.startswith(REPO + os.sep) or not os.path.isfile(full):
        return None
    return os.path.relpath(full, REPO)


def needs_probe(url, cache):
    """Ask the wire again about this citation?

    Not-found verdicts are frozen for everybody else (a dead third-party citation is a content
    decision, and re-probing 780 URLs a round is how the 429s start), but a cached 404 on a file
    the book itself ships is stale by construction the moment that file lands."""
    verdict = (cache.get(url) or {}).get("verdict")
    if verdict not in OK_VERDICTS:
        return True
    return verdict in ("DEAD", "SOFT-404") and landed_in_tree(url) is not None


def refresh(external, cache, force_all=False):
    """Probe what the book cites. A cached OK/MOVED/DEAD/SOFT-404 is kept; an inconclusive entry
    is retried, because 'the probe got reset' is not a verdict about the citation. A cached
    not-found on a file this repo now ships is retried too (`needs_probe`)."""
    todo = sorted(external) if force_all else [u for u in sorted(external) if needs_probe(u, cache)]
    ours = [u for u in todo if landed_in_tree(u)]
    if ours:
        print("  own-repo re-probes: %d cached not-found verdicts point at files this tree ships"
              " (%s)" % (len(ours), ", ".join(os.path.basename(u) for u in ours[:8])), flush=True)
    stamp = datetime.date.today().isoformat()
    if not todo:
        return 0

    def one(u):
        time.sleep(THROTTLE)
        return u, probe(u)

    # Streamed on purpose. `list(pool.map(...))` collected every verdict before writing any, so a
    # seeding run over ~700 URLs that died or was interrupted at probe 690 left the cache empty and
    # the next run started from zero.
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for u, verdict in pool.map(one, todo):
            verdict["checked"] = stamp
            cache[u] = verdict
            done += 1
            if done % 50 == 0:
                save_cache(cache)
                print("  probed %d/%d" % (done, len(todo)), flush=True)
    save_cache(cache)
    return done


def external_leg(external, cache):
    findings = []
    tally = Counter()
    missing = []
    for url in sorted(external):
        entry = cache.get(url)
        if entry is None:
            missing.append(url)
            continue
        verdict = entry["verdict"]
        tally[verdict] += 1
        cited = ", ".join(sorted(external[url])[:3])
        if verdict == "DEAD":
            findings.append("DEAD %s (HTTP %s) cited by %s" % (url, entry.get("status"), cited))
        elif verdict == "SOFT-404":
            findings.append("SOFT-404 %s title=%r cited by %s" % (url, entry.get("title"), cited))
        elif verdict == "MOVED":
            findings.append("MOVED %s -> %s cited by %s" % (url, entry.get("final"), cited))
        elif verdict not in ("OK", "BLOCKED", "NET", "PROBE-ERROR"):
            findings.append("UNREADABLE %s verdict=%s status=%s cited by %s"
                            % (url, verdict, entry.get("status"), cited))
    inconclusive = {k: tally[k] for k in ("BLOCKED", "NET", "PROBE-ERROR") if tally[k]}
    if missing:
        findings.append("UNCHECKED %d of %d cited URLs carry no probe verdict — run --refresh "
                        "(an absent entry is NOT a pass): %s"
                        % (len(missing), len(external), ", ".join(sorted(missing)[:3])))
    return findings, tally, inconclusive, missing


# ---------------------------------------------------------------- live anchor leg ----------

def heading_ids(served):
    return set(re.findall(r'<h[1-6][^>]*\bid="([^"]+)"', served))


def live_anchor_leg(anchors, fetch=None, index=None, title_of=None, read_of=None):
    """Grade each fragment against the ids the platform publishes for the target page.

    Every page gets a positive control (an id this same extractor read off that page must be
    findable) and a phantom control (a ghost fragment must be absent). 'No anchor problems' is only
    worth printing if the probe proved it can see anchors at all. The index/title readers are
    injectable so the controls can run this same code path offline.
    """
    fetch = fetch or get_page_text
    read_of = read_of or read
    title_of = title_of or (lambda path: h1_of(read_of(path)))
    findings = []
    try:
        index = url_index() if index is None else index
    except Exception as e:  # noqa: BLE001
        return ["BLIND llms.txt index unavailable (%r): %d anchors ungraded, not clean"
                % (e, len(anchors))], 0
    by_target = defaultdict(list)
    for rel, ln, target, frag, hit in anchors:
        by_target[hit].append((rel, ln, target, frag))
    graded = 0
    for hit, rows in sorted(by_target.items()):
        url = index.get(norm(title_of(hit)))
        if not url:
            findings.append("BLIND %s has no unique llms.txt entry — its %d anchor(s) ungraded"
                            % (rel_of(hit), len(rows)))
            continue
        try:
            ids = {i.lower() for i in heading_ids(fetch(url))}
        except Exception as e:  # noqa: BLE001
            findings.append("BLIND fetch failed for %s (%r) — anchors ungraded" % (rel_of(hit), e))
            continue
        if not ids:
            findings.append("BLIND %s served HTML exposes 0 heading ids — anchors ungraded"
                            % rel_of(hit))
            continue
        if sorted(ids)[0] not in ids:      # the extractor's own positive control
            findings.append("BLIND positive control failed on %s" % rel_of(hit))
        ghost = "ghost-fragment-not-in-any-heading"
        if ghost in ids:
            findings.append("BLIND phantom control matched on %s" % rel_of(hit))
        for rel, ln, target, frag in rows:
            graded += 1
            if frag.lower() not in ids:
                findings.append("ANCHOR-MISS %s:%d -> %s (target %s publishes %d ids, none is %r)"
                                % (rel, ln, target, rel_of(hit), len(ids), frag))
    return findings, graded


# ---------------------------------------------------------------- controls -----------------

def controls():
    """Each bucket must fire on a planted defect and stay silent on the good shape."""
    hits = Counter()

    # --- BAD-TARGET: a phantom file must fire, a real one must not, on the real tree ---
    tmp = os.path.join(DOCS, "00-index", "_link_control_tmp.md")
    io.open(tmp, "w", encoding="utf-8").write(
        "# 控制页\n\n"
        "- [ghost](no-such-file-xq.md)\n"
        "- [real](changelog.md)\n"
        "- [asset](../.gitbook/assets/02-agent-loop.svg)\n"
        "- [external](https://example.com/a)\n"
        "- [fenced](ignore-me.md)\n"
        "- 自动链接 <https://autolink-xq.example/>\n\n"
        "```\n[inside a fence](in-fence-xq.md)\n<https://in-fence-xq.example/>\n```\n")
    try:
        seen = list(iter_links(tmp))
        assert any("no-such-file-xq" in t for _l, _i, t in seen), "phantom link missed by tokenizer"
        assert not any("in-fence-xq" in t for _l, _i, t in seen), "a link inside a fence is not a link"
        assert any(t == "https://autolink-xq.example/" for _l, _i, t in seen), \
            "a bare <https://…> autolink is clickable prose; the tokenizer missed it"
        assert len(seen) == 6, "the control page has 6 visible links: %s" % seen
        hits["link tokenizer sees prose, skips fences"] = 1
        fired = [t for _l, _i, t in seen
                 if not t.startswith(("http", "#")) and resolve(tmp, split_target(t)[0]) is None]
        assert any("no-such-file-xq" in t for t in fired), "phantom BAD-TARGET must fire: %s" % fired
        assert not any("changelog" in t for t in fired), "a real target must not fire"
        hits["bad-target fires / real target passes"] = 1
    finally:
        os.remove(tmp)
    assert not os.path.exists(tmp)
    assert not any("_link_control_tmp" in rel_of(p) for p in body_pages()), \
        "a control page must not linger in the tree"
    hits["control page leaves no residue"] = 1

    # --- ORPHAN / SUMMARY-STALE: pure arithmetic, both directions ---
    f1 = orphan_findings(["a.md", "b.md"], ["a.md"])
    assert any(f.startswith("ORPHAN b.md") for f in f1) and len(f1) == 1, f1
    f2 = orphan_findings(["a.md"], ["a.md", "gone.md"])
    assert any(f.startswith("SUMMARY-STALE gone.md") for f in f2), f2
    assert orphan_findings(["a.md"], ["a.md"]) == [], "a matched pair must stay silent"
    hits["orphan + stale both directions"] = 1

    # --- external buckets: DEAD/SOFT-404/MOVED fire, BLOCKED+NET are excused ---
    ext = {"https://a.example/": {"x.md"}, "https://b.example/": {"y.md"},
           "https://c.example/": {"z.md"}, "https://d.example/": {"w.md"},
           "https://e.example/": {"v.md"}}
    cache = {"https://a.example/": {"verdict": "OK", "status": 200},
             "https://b.example/": {"verdict": "DEAD", "status": 404},
             "https://c.example/": {"verdict": "BLOCKED", "status": 429},
             "https://d.example/": {"verdict": "SOFT-404", "status": 200, "title": "Page not found"},
             "https://e.example/": {"verdict": "MOVED", "final": "https://new.example/x"}}
    fnd, tally, incon, missing = external_leg(ext, cache)
    assert any(f.startswith("DEAD") for f in fnd), "a 404 citation must be a finding"
    assert any(f.startswith("SOFT-404") for f in fnd), "a not-found title must be a finding"
    assert any(f.startswith("MOVED") for f in fnd), "a host move must be a finding"
    assert not any("BLOCKED" in f or "429" in f for f in fnd), "rate-limit must not be a defect"
    assert incon == {"BLOCKED": 1} and sum(tally.values()) == 5 and not missing
    hits["dead+soft+moved fire, blocked excused"] = 1

    # --- own-repo not-found verdicts go stale when the book ships the file itself (round 101) ---
    slug = our_slug()
    assert slug and "/" in slug, "no origin slug, so the own-repo branch cannot be exercised here"
    ours_ok = "https://github.com/%s/blob/main/docs/SUMMARY.md" % slug
    ours_raw = "https://raw.githubusercontent.com/%s/main/docs/SUMMARY.md" % slug
    ours_gone = "https://github.com/%s/blob/main/docs/no-such-page-here.md" % slug
    assert landed_in_tree(ours_ok, slug) == os.path.join("docs", "SUMMARY.md"), ours_ok
    assert landed_in_tree(ours_raw, slug) == os.path.join("docs", "SUMMARY.md"), ours_raw
    assert landed_in_tree(ours_gone, slug) is None, "a page this tree does not ship must stay frozen"
    assert landed_in_tree("https://github.com/torvalds/linux/blob/main/README.md", slug) is None, \
        "this tree has a README.md too; the rule is the remote's slug, not the path shape"
    assert landed_in_tree("https://example.com/%s/blob/main/docs/SUMMARY.md" % slug, slug) is None, \
        "the same path on another host is not a citation into this repo"
    assert landed_in_tree("https://github.com/%s/blob/main/../../outside.env" % slug, slug) is None, \
        "a traversal-shaped citation must not read as a file inside the repo"

    def dead_of(url, verdict="DEAD"):
        return {url: {"verdict": verdict, "status": 404 if verdict == "DEAD" else 200}}

    assert needs_probe(ours_ok, dead_of(ours_ok)) and needs_probe(ours_raw, dead_of(ours_raw)), \
        "a 404 cached before the push would otherwise stand forever"
    assert needs_probe(ours_ok, dead_of(ours_ok, "SOFT-404")), \
        "a not-found page served at 200 is just as stale as a 404"
    assert not needs_probe(ours_gone, dead_of(ours_gone)), \
        "the repair must not become 're-probe every dead link every round'"
    assert not needs_probe("https://a.example/", dead_of("https://a.example/")), \
        "a third-party 404 is a content decision, not a retry budget"
    assert not needs_probe(ours_ok, {ours_ok: {"verdict": "OK", "status": 200}}), \
        "the live citations must not be re-probed to prove this branch"
    hits["own-repo 404 re-probes, everything else stays frozen"] = 1

    # --- a status code is a verdict on the citation only when it is about the citation (round 101) ---
    assert http_error_verdict(404) == "DEAD" and http_error_verdict(451) == "DEAD", \
        "a not-found and a taken-down page are content findings"
    assert http_error_verdict(429) == "BLOCKED" and http_error_verdict(403) == "BLOCKED", \
        "rate-limit and permission are the already-excused family"
    assert http_error_verdict(503) == "NET" and http_error_verdict(502) == "NET", \
        "this is the branch that reddened a round over a GitHub hiccup"
    assert http_error_verdict(507) == "HTTP-507", \
        "an unexplained status stays loud; the repair is not 'silence every 5xx'"
    shrug = {"https://shrug.example/": {"x.md"}}
    fnd3, _, incon3, _ = external_leg(shrug, {"https://shrug.example/": {"verdict": "NET", "status": 503}})
    assert not fnd3 and incon3 == {"NET": 1}, \
        "a shrug must land in the inconclusive bucket, never in the defect bucket: %s %s" % (fnd3, incon3)
    hits["5xx shrug inconclusive, odd status still a finding"] = 1

    # --- an unknown flag must cost the caller, not silently run the default pass (round 101) ---
    # `--help` used to print a full cached verdict here, exactly the bug round 96 closed in the
    # battery runner. Driven through a real subprocess because the guard is in `main`, not in a
    # predicate: an axis that only *looks* like it validated its flags is what let this survive.
    for bad in ("--help", "--refsh", "--live-no"):
        res = subprocess.run([sys.executable, os.path.abspath(__file__), bad],
                             capture_output=True, timeout=120)
        assert res.returncode == 2 and b"unknown flag" in res.stdout + res.stderr, \
            "`%s` must exit 2, not run the default pass: rc=%s %r" % (
                bad, res.returncode, (res.stdout + res.stderr)[:200])
        assert b"link graph:" not in res.stdout, "`%s` still printed a verdict" % bad
    hits["unknown flag exits 2 instead of printing a verdict"] = 1

    # --- the not-found sniff, both directions (round 81 fired on its own first pass) ---
    live = sniff({"body": "<title>[2404.06654] RULER: What&#39;s the Real Context Size "
                          "of Your Long-Context Language Models?</title>"})
    assert live[1] == [], "an arXiv id contains the digits 4-0-4; a live paper is not a 404: %s" % live
    assert sniff({"body": "<title>404 Page Not Found</title>"})[1], "a real 404 title must fire"
    assert sniff({"body": "<title>Error 404</title>"})[1], "a bare status code must fire"
    assert sniff({"body": "<title>该页面不存在</title>"})[1], "a Chinese not-found title must fire"
    assert sniff({"body": "<title>arXiv:1404.5678 memo</title>"})[1] == []
    hits["soft-404 sniff: arXiv silent, real 404 loud"] = 1

    # --- a host move has to be a move, not a www difference ---
    assert same_site("www.eleuther.ai", "eleuther.ai") and same_site("eleuther.ai", "www.eleuther.ai"), \
        "dropping www is the same site; the old rule only forgave adding it"
    assert not same_site("www.anthropic.com", "discord.com"), "a third-party redirect is a move"
    assert not same_site("docs.smith.langchain.com", "docs.langchain.com"), \
        "a doc-host change must still read as MOVED"
    hits["www-only silent, host change loud"] = 1
    fnd2, _, _, missing2 = external_leg(ext, {"https://a.example/": {"verdict": "OK"}})
    assert len(missing2) == 4 and any(f.startswith("UNCHECKED") for f in fnd2), \
        "unprobed citations must read as a coverage failure"
    hits["coverage bucket fires"] = 1

    # --- coverage floors must fire on a shrunken tree, not on the real one ---
    small = {"pages": 3, "listed": 3, "kinds": {"relative": 5, "external": 5},
             "distinct_external": 4, "citing_pairs": 5, "occurrences": 5}
    assert len(coverage_findings(small)) == 4, "all four floors must be able to speak"
    assert coverage_findings({"pages": MIN_PAGES, "listed": 1,
                              "kinds": {"relative": MIN_RELATIVE},
                              "distinct_external": MIN_DISTINCT_EXT,
                              "occurrences": MIN_CITATIONS}) == []
    hits["coverage floors bite both ways"] = 1

    # --- the live anchor leg must catch a ghost fragment and bless a real one ---
    served = ('<h1>标题</h1><h2 id="di-1-bu-xian-li-kao-ti">第 1 步：立考题</h2>'
              '<h2 id="kai-fa-zhe">开发者</h2>')
    calls = {"n": 0}

    def fake_fetch(_url):
        calls["n"] += 1
        return served

    index = {"控制页": "https://example.invalid/page"}
    title_of = lambda path: "控制页"          # noqa: E731 - the injected page title
    read_of = lambda path: "# 控制页\n"        # noqa: E731 - never called by this leg
    target = os.path.join(DOCS, "t.md")       # a path rel_of() can speak about
    good = [("p.md", 3, "t.md#di-1-bu-xian-li-kao-ti", "di-1-bu-xian-li-kao-ti", target)]
    bad = [("p.md", 3, "t.md#ghost-heading", "ghost-heading", target)]
    for name, rows, want in (("good", good, 0), ("phantom", bad, 1)):
        findings, graded = live_anchor_leg(rows, fetch=fake_fetch, index=index,
                                           title_of=title_of, read_of=read_of)
        assert graded == 1, "%s: anchor never graded (fetches=%d)" % (name, calls["n"])
        assert len([f for f in findings if f.startswith("ANCHOR-MISS")]) == want, \
            "%s: %s" % (name, findings)
    hits["anchor leg: real id passes, ghost fires"] = 1
    assert calls["n"] == 2, "one fetch per target page, not per fragment"
    findings, graded = live_anchor_leg(bad, fetch=fake_fetch, index={},
                                       title_of=title_of, read_of=read_of)
    assert graded == 0 and any(f.startswith("BLIND") for f in findings), \
        "a page with no live URL must read BLIND, not clean"
    hits["unresolvable anchor reads BLIND"] = 1
    findings, graded = live_anchor_leg(bad, fetch=lambda u: "<html>no ids here</html>",
                                       index=index, title_of=title_of, read_of=read_of)
    assert graded == 0 and any("0 heading ids" in f for f in findings), \
        "a page that exposes no ids must read BLIND, not clean"
    hits["id-less page reads BLIND"] = 1

    # --- the homepage prints this axis's reading; that sentence has to be reconciled, not copied --
    st = {"pages": 7, "listed": 7, "kinds": {"relative": 11, "external": 23},
          "distinct_external": 13, "citing_pairs": 20, "occurrences": 23}
    tl = Counter({"OK": 12, "BLOCKED": 1})
    two = [("a.md", 1, "t.md#x", "x", target), ("b.md", 2, "t.md#y", "y", target)]
    claim = ("正文零可执行代码 读数 `link-graph: pages=7 relative=11 external=23 distinct=13 "
             "ok=12 blocked=1 net=0 unchecked=0 fragments=2` 控制")
    out, want = homepage_claim_leg(st, tl, [], two, text=claim)
    assert out == [] and want["fragments"] == 2, "a matching homepage must read clean: %s" % out
    drift = homepage_claim_leg(st, tl, [], two, text=claim.replace("ok=12", "ok=13"))[0]
    assert len(drift) == 1 and drift[0].startswith("HOMEPAGE-BADGE ok"), \
        "one stale number must speak once: %s" % drift
    drift = homepage_claim_leg(st, tl, ["https://x.example/"], two, text=claim)[0]
    assert any(f.startswith("HOMEPAGE-BADGE unchecked") for f in drift), \
        "an unprobed citation must also make the homepage reading wrong, not merely the cache"
    assert homepage_claim_leg(st, tl, [], two, text="a homepage that dropped the reading")[0][0] \
        .startswith("HOMEPAGE-BLIND"), "deleting the sentence must not read as a pass"
    hits["homepage reading reconciled; drift and absence both fire"] = 1

    # --- citation coverage: the 「每篇知识/资源页都有参考资料」 claim, both directions ---
    good, scoped, sources = citation_leg(body_pages())
    assert good == [], "the shipped tree must read clean on citations: %s" % good[:4]
    assert scoped > 150 and sources > 300, \
        "a scan this narrow cannot call the claim clean (pages=%d sources=%d)" % (scoped, sources)
    hits["citation leg reads the real tree, coverage self-reports"] = 1

    pages = {
        # a section with one clickable external source: clean
        "k1": ("type: knowledge\n", "## 参考资料\n\n- [a](https://cite-a.example/)\n"),
        # the same URL cited again from a second page: still one distinct source
        "k2": ("type: knowledge\n", "## 参考资料\n\n- [a again](https://cite-a.example/)\n"),
        # a resource page whose only pointer is internal: the section exists but cites nothing
        "r1": ("type: resource\n", "## 参考资料\n\n- [内部页](changelog.md)\n"),
        # a bare <https://…> autolink is a citation too (the round-81 tokenizer lesson)
        "k3": ("type: knowledge\n", "## 参考资料\n\n- <https://cite-b.example/>\n"),
        # the only URL sits inside a fence: documentation of syntax, not a source
        "k4": ("type: knowledge\n", "## 参考资料\n\n```\nhttps://cite-fenced.example\n```\n"),
        # an empty section followed by an external link in a *later* section
        "k5": ("type: knowledge\n",
               "## 参考资料\n\n- [内部](changelog.md)\n\n## 附录\n\n- [b](https://cite-late.example/)\n"),
        # no such section at all
        "k6": ("type: knowledge\n", "## 相关知识点\n\n- [x](changelog.md)\n"),
        # out of scope: an index page is not required to carry sources
        "i1": ("type: index\n", "## 相关知识点\n\n- [x](changelog.md)\n"),
    }
    tmp = []
    try:
        for name, (fm, body) in pages.items():
            path = os.path.join(DOCS, "00-index", "_cite_%s_tmp.md" % name)
            io.open(path, "w", encoding="utf-8").write("---\n%s---\n\n# 控制页\n\n%s" % (fm, body))
            tmp.append(path)
        fnd, n_scoped, n_src = citation_leg(tmp)
        kinds = {f.split()[0] for f in fnd}
        fired = {f.split()[1] for f in fnd}
        assert "REF-MISSING" in kinds and any("_cite_k6" in f for f in fired), \
            "a page with no 参考资料 section must fire: %s" % fnd
        assert "REF-EMPTY" in kinds and any("_cite_r1" in f for f in fired), \
            "a section with only internal links must fire: %s" % fnd
        assert any("_cite_k4" in f for f in fired), \
            "a URL documented inside a fence is not a citation: %s" % fnd
        assert any("_cite_k5" in f for f in fired), \
            "a link after the NEXT heading must not count as this section's source: %s" % fnd
        assert not any("_cite_k1" in f or "_cite_k2" in f or "_cite_k3" in f for f in fnd), \
            "the three good shapes must stay silent: %s" % fnd
        assert not any("_cite_i1" in f for f in fnd), "an index page is out of scope: %s" % fnd
        assert n_scoped == 7 and n_src == 2, \
            "scope/dedupe miscounted (scoped=%d sources=%d, want 7 knowledge+resource pages " \
            "and 2 distinct URLs)" % (n_scoped, n_src)
        hits["citation leg: 4 defects fire, 3 good shapes silent, scope+dedupe counted"] = 1

        claim = ("**167 篇知识/资源页全部有「参考资料」**（按 frontmatter `type` 统计，不是靠肉眼挑）"
                 "：378 条去重后的外部一手来源逐条点开核对")
        assert homepage_ref_leg(167, 378, text=claim) == [], \
            "a matching homepage must read clean: %s" % homepage_ref_leg(167, 378, text=claim)
        assert any(f.startswith("HOMEPAGE-REF-HIGH pages")
                   for f in homepage_ref_leg(166, 378, text=claim)), "claiming more pages than found must fire"
        assert any(f.startswith("HOMEPAGE-REF-HIGH sources")
                   for f in homepage_ref_leg(167, 377, text=claim)), "claiming more sources than found must fire"
        dated = homepage_ref_leg(168, 380, text=claim)
        assert len(dated) == 2 and all(f.startswith("ADVISORY HOMEPAGE-REF-DATED") for f in dated), \
            "the tree growing past the sentence is dated prose, not a defect: %s" % dated
        assert homepage_ref_leg(167, 378, text="首页把这条统计删掉了")[0] \
            .startswith("HOMEPAGE-REF-BLIND"), "deleting the sentence must not read as a pass"
        hits["homepage citation reading: exact / overstated / dated / absent"] = 1
    finally:
        for path in tmp:
            if os.path.exists(path):
                os.remove(path)
    assert not any("_cite_" in rel_of(p) for p in body_pages()), "citation controls must leave no residue"
    hits["citation control pages leave no residue"] = 1
    return hits


def main():
    argv = sys.argv[1:]
    if reject_unknown(argv, FLAGS, "check_link_graph"):
        # Round 96 made the battery refuse an unknown flag; this ruler reads argv by hand, so it
        # kept the older bug -- `--help` here ran the whole cached pass and printed a verdict as if
        # the leg the caller asked for had run. A typo'd flag must cost the caller, not the reader.
        return 2
    if "--selftest" in argv:
        hits = controls()
        print("controls: %d buckets, every one able to fire" % len(hits))
        return 0

    findings, anchors, external, stats = internal_leg()
    findings += coverage_findings(stats)

    cache = load_cache()
    if "--refresh" in argv:
        n = refresh(external, cache)
        print("refresh: probed %d URLs" % n)
    ext_findings, tally, inconclusive, missing = external_leg(external, cache)
    findings += ext_findings

    graded = 0
    if "--live" in argv:
        live_findings, graded = live_anchor_leg(anchors)
        findings += live_findings

    claim_findings, want = homepage_claim_leg(stats, tally, missing, anchors)
    findings += claim_findings

    ref_findings, ref_pages, ref_sources = citation_leg(body_pages())
    findings += ref_findings
    findings += homepage_ref_leg(ref_pages, ref_sources)

    oldest = min((e.get("checked", "never") for e in cache.values()), default="never")
    print("link graph: pages=%d listed=%d nav-links=%d relative=%d external-links=%d "
          "distinct-external=%d citing-pairs=%d"
          % (stats["pages"], stats["listed"], stats["kinds"].get("nav", 0),
             stats["kinds"].get("relative", 0), stats["occurrences"], stats["distinct_external"],
             stats["citing_pairs"]))
    print("external verdicts: %s" % dict(tally))
    print("external inconclusive=%s unchecked=%d oldest-check=%s" % (inconclusive, len(missing),
                                                                     oldest))
    print("anchors: fragments-seen=%d graded-live=%d" % (len(anchors), graded))
    print("homepage claim: %s" % " ".join("%s=%d" % (k, want[k]) for k in sorted(want)))
    print("citation coverage: knowledge/resource pages=%d ref-findings=%d distinct sources=%d"
          % (ref_pages, len(ref_findings), ref_sources))
    for f in findings:
        print("  " + f)
    hard = [f for f in findings if not f.startswith("ADVISORY")]
    print("FAILED: %d" % len(hard))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
