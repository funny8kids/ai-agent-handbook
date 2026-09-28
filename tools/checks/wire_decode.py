"""One HTTP request shape for every leg that reads a reader-visible page.

Why this module exists. Measured on the live changelog page (2026-09-28, HEAD 104):

    request                     wire bytes    time      decoded
    no Accept-Encoding (#1)     7,564,511     65.4 s    7,448,727 chars, ends mid-token 'focus-visibl'
    no Accept-Encoding (#2)    29,235,262     30.7 s    28,239,889 chars, ends '</html>'
    Accept-Encoding: gzip (#1)  1,908,917     12.5 s    28,239,889 chars, ends '</html>'
    Accept-Encoding: gzip (#2)  1,839,679      7.1 s    28,239,889 chars, ends '</html>'

The page ships no Content-Length and no Content-Encoding unless we ask, so an un-advertised GET
streams ~29 MB through one connection and Cloudflare closes it early often enough that round 99
measured 5 of 8 sequential fetches truncated. That is the whole origin of the "short read" refusals
that have blocked every close-out since: the leg was asking for 29 MB of uncompressed HTML, and a
browser never does. When both reads land complete their bodies are character-identical (28,239,889
on both sides), so compression is not a different document — it is the same document on a wire short
enough to finish.

The fix has to be a class fix, because the class is what keeps biting: `live_aria_manifest.fetch`
(feeds the prose-survival, emphasis, aria-parity and palette legs), `check_widget_visibility_live
.fetch` (the column, svg, table, image and sanitizer legs), `check_live_sync.live_rounds` (the
round-count legs) and `check_link_graph`'s anchor-leg default all open their own connections. A leg
that forgets the header is invisible in its own output — it just reads slower and truncates more —
so `selftest()` below also scans those files for the seam instead of trusting them to remember.

Truncation still has to be *refused*, not worked around: `gzip.decompress` raises `EOFError` on a
stream that ends early, and round 58 already recorded what happens when that escapes untyped (13
PROBE-ERRORs read as site outages in `check_link_graph.py`). So a half-inflated body becomes a
`WireError`, which subclasses `urllib.error.URLError` precisely so the retry loops and
fetch-failure buckets that were written around `URLError`/`OSError` keep catching it — a truncated
copy still cannot buy a green.
"""
import gzip
import io
import os
import urllib.error
import urllib.request
import zlib

ACCEPT_ENCODING = "gzip"
# Only what the standard library can inflate without a third-party wheel: advertising `br` would get
# us bodies we cannot read, which is a silent outage rather than a slower one.
HEADERS = {"Accept-Encoding": ACCEPT_ENCODING}

# The legs that read a reader-visible page. Names are checked, not remembered: a new leg joins this
# list by importing `headers`/`decode` below, and `selftest` reddens if one of these stops using it.
WIRE_CALLERS = ("live_aria_manifest.py", "check_widget_visibility_live.py", "check_live_sync.py",
                "check_link_graph.py")
HERE = os.path.dirname(os.path.abspath(__file__))


class WireError(urllib.error.URLError):
    """The body on the wire was not a body we could hand to the judge.

    Named as a URLError so every existing `except (urllib.error.URLError, OSError)` retry and
    fetch-failure bucket treats it as the failed read it is, instead of raising past the bucket and
    becoming a traceback (round 58) or a silent short string (round 91).
    """


def headers(base=None):
    """`base` plus the encoding we can actually inflate — never the other way round."""
    out = dict(base or {})
    out.update(HEADERS)
    return out


def decode(resp_headers, raw, url=""):
    """The document bytes, inflated if the server said it compressed them.

    `resp_headers` may be missing (a file:// read has none) and an unknown encoding is refused rather
    than passed through: compressed bytes decoded as UTF-8 with `errors="replace"` would reach the
    round counter and the needle check as mojibake that *looks* like a short document.
    """
    enc = ""
    try:
        enc = (resp_headers.get("Content-Encoding") or "").strip().lower() if resp_headers else ""
    except AttributeError:
        enc = ""
    if not raw:
        return raw
    if enc in ("", "identity"):
        return raw
    if enc != "gzip":
        raise WireError("unsupported Content-Encoding %r on %s — this leg can only inflate gzip"
                        % (enc, url))
    try:
        body = gzip.decompress(raw)
    except EOFError as exc:
        # The case this whole module exists for: a stream that stops early is not a shorter page.
        raise WireError("gzip body for %s ended early (%s) after %d wire bytes — the document did "
                        "not arrive, so nothing about it can be judged"
                        % (url, exc.__class__.__name__, len(raw)))
    except (OSError, zlib.error) as exc:
        # BadGzipFile and a mid-member CRC/zlib failure name themselves differently from a short
        # read, and a leg that reported "truncated" here would point the follow-up at the CDN.
        raise WireError("gzip body for %s is not a readable gzip member (%s: %s)"
                        % (url, exc.__class__.__name__, str(exc)[:80]))
    if not body:
        raise WireError("gzip body for %s inflated to zero bytes from %d wire bytes" % (url, len(raw)))
    return body


def request(url, base_headers=None):
    """A Request that advertises what it can read. The one seam every leg should build through."""
    return urllib.request.Request(url, headers=headers(base_headers))


def selftest():
    """Four arms on the decoder, one on the seam, and one that proves the knob is connected.

    Bidirectional by construction: each refusal arm is paired with the complete-body arm that must
    stay silent, so the guards cannot pass by being dead.
    """
    errs = []
    doc = "<html><body>第 104 次：读者可见的中文句子。</body></html>".encode("utf-8")
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as fh:
        fh.write(doc)
    packed = buf.getvalue()

    # A: the two bodies that must both land whole.
    if decode({"Content-Encoding": "gzip"}, packed) != doc:
        errs.append("control W-wire A1: a complete gzip body must inflate to the document")
    if decode({}, doc) != doc:
        errs.append("control W-wire A2: an identity body must pass through untouched")
    if decode({"Content-Encoding": "identity"}, doc) != doc:
        errs.append("control W-wire A3: Content-Encoding: identity must not be treated as compressed")

    # B: the three ways the wire can fail. Which message each one gets was measured, not assumed:
    # gzip.decompress raises EOFError on a stream cut before the end marker (both truncations tried),
    # BadGzipFile on plain bytes labelled gzip, and nothing at all on an empty body.
    for what, hdrs, body, expect in (
            ("truncated mid-stream", {"Content-Encoding": "gzip"}, packed[:12], "ended early"),
            ("cut in half", {"Content-Encoding": "gzip"}, packed[:len(packed) // 2], "ended early"),
            ("labelled gzip but not gzip", {"Content-Encoding": "gzip"}, doc,
             "not a readable gzip member"),
            ("an encoding we cannot read", {"Content-Encoding": "br"}, packed,
             "unsupported Content-Encoding")):
        try:
            got = decode(hdrs, body, "https://example.invalid/page")
        except WireError as exc:
            if expect not in str(exc):
                errs.append("control W-wire B: %s must be refused as %r, got %r"
                            % (what, expect, str(exc)[:90]))
        else:
            errs.append("control W-wire B: %s returned %d bytes as if it were the document — a half "
                        "page would be judged instead of refused" % (what, len(got)))

    # C: the empty body stays what it was (a leg's own bucket owns that verdict, not this decoder).
    if decode({"Content-Encoding": "gzip"}, b"") != b"":
        errs.append("control W-wire C: an empty body must not be rewritten into a decompression error")

    # D: headers() adds, never drops, and never advertises something we cannot inflate.
    if headers({"User-Agent": "x"}).get("User-Agent") != "x":
        errs.append("control W-wire D: headers() must not discard the caller's own headers")
    if headers().get("Accept-Encoding") != "gzip":
        errs.append("control W-wire D: the leg must advertise only gzip, which the stdlib can inflate")

    # E: the class gate. A leg that opens its own connection without this module is the same bug the
    # round-99 log recorded as "a coin flip about the wire" — so the seam is required, not advised.
    # The line scan runs unconditionally. It used to be guarded on the file containing no wire call
    # at all, which made it dead for any leg that had adopted the seam partially: a mutation putting
    # ONE request back to a hand-built `headers=UA` stayed green (measured twice this round, on
    # check_link_graph and on live_aria_manifest). One uncompressed request is enough to truncate.
    for name in WIRE_CALLERS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            errs.append("control W-wire E: %s is listed as a page-reading leg but does not exist"
                        % name)
            continue
        src = io.open(path, encoding="utf-8").read()
        if "import wire_decode" not in src:
            errs.append("control W-wire E: %s fetches reader pages without wire_decode — its reads "
                        "stream uncompressed and truncate at the measured rate" % name)
            continue
        bare = [i for i, line in enumerate(src.splitlines(), 1)
                if "urllib.request.Request(" in line and "wire." not in line]
        if bare:
            errs.append("control W-wire E: %s builds a Request without wire.headers()/wire.request()"
                        " at line(s) %s — that request does not advertise gzip, so this leg is the "
                        "one that reads 29 MB" % (name, bare))

    # F: the knob is connected, not just present — the decoder must survive a round trip through the
    # real gzip writer twice over, or a leg could read the same truncated body twice and call it
    # stable.
    if decode({"Content-Encoding": "gzip"}, gzip.compress(doc, 9)) != doc:
        errs.append("control W-wire F: a level-9 gzip body must inflate back to the document")
    return errs
