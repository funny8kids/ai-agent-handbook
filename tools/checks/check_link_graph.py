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
"""
import datetime
import io
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from live_aria_manifest import prose, url_index, norm, h1_of  # noqa: E402  one prose ruler

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
CACHE = os.path.join(HERE, "data", "external_links.json")
NON_BODY = ("SUMMARY.md", "MANIFEST.md")
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
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*",
                                               "Accept-Language": "en,zh-CN",
                                               "Accept-Encoding": "gzip"})
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
                else:
                    return {"verdict": "DEAD" if e.code in DEAD_STATUS else
                            ("BLOCKED" if e.code in BLOCK_STATUS else "HTTP-%d" % e.code),
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


def refresh(external, cache, force_all=False):
    """Probe what the book cites. A cached OK/MOVED/DEAD/SOFT-404 is kept; an inconclusive entry
    is retried, because 'the probe got reset' is not a verdict about the citation."""
    todo = sorted(external) if force_all else [
        u for u in sorted(external) if cache.get(u, {}).get("verdict") not in OK_VERDICTS]
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
    fetch = fetch or (lambda u: urllib.request.urlopen(
        urllib.request.Request(u, headers={"User-Agent": UA}), timeout=TIMEOUT
    ).read().decode("utf-8", "replace"))
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
    return hits


def main():
    argv = sys.argv[1:]
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
    for f in findings:
        print("  " + f)
    hard = [f for f in findings if not f.startswith("ADVISORY")]
    print("FAILED: %d" % len(hard))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
