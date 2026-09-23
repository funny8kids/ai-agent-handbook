"""Live image axis: every authored figure must reach the page, and every served image must load.

Why a new axis (round 58): the parity axis counts formulas and tab widgets, both of which this
platform ships inside the SSR HTML. Images were assumed safe because `check_structure.py` proves
the asset file exists on disk. Existence on disk is not the claim "the reader sees a picture":
GitBook rewrites `![](.gitbook/assets/x.svg)` into `~gitbook/image?url=<proxy>&sign=<sig>`, so a
file that is perfectly present locally can still come back as a 404, an HTML error body, or a
0-byte response on the live site — and a stale publish can serve an image the source no longer
asks for. Nothing measured either direction before this file.

Four judgements, because they fail differently:
  DROPPED  an authored image has no content <img> on the live page naming its asset
  EXTRA    the live page serves an image no local page asks for (stale publish / wrong page)
  NOCAPTION an authored image's alt never reaches the page as visible text (or is empty at all)
  BROKEN   a served image URL does not answer 200 with an image/* body worth looking at

Plus two tripwires that are green by measurement and stay green: WEAKCAPTION (an alt too short to
read as a sentence) and RASTERIZED (an authored .svg served as a bitmap — it loads, so nothing else
would notice the animation the file contains is gone).

Three markup facts, each measured on this deployment before being relied on:
  * the `.md` endpoint serves the page's MARKDOWN (10 KB), the browser URL serves the HTML
    (1.7 MB). Fetching the wrong one makes every image look dropped, so this file strips `.md`
    exactly like check_widget_visibility_live.check_page does.
  * content images are `<img data-testid="zoom-image">`; the site header injects 4 `<img alt="Logo">`
    on every page, so counting raw `<img>` tags over-reports by 4 and would drown DROPPED/EXTRA.
  * the src attribute is entity-encoded (`&amp;sign=…`). Requesting it verbatim returns
    HTTP 400 Bad Request — the proxy needs `html.unescape` first. A naive "the live image 404s!"
    finding here would be the probe's fault, not the site's, so controls() asserts both sides.
    And the alt text is NOT served as alt: the platform empties `alt=""` and prints the author's
    alt inside `<figcaption>` — which is why NOCAPTION compares against visible text, not markup.

Usage:
    python tools/checks/check_live_images.py             # whole site (36 image pages)
    python tools/checks/check_live_images.py --sample 8  # first 8 pages, for a quick look

External images (http(s) targets authored into the page) are skipped, not judged: their
availability belongs to the upstream owner, and folding them in would make the axis
un-red-green-able by construction. Measured: this book authors 0 of them.
"""
import collections
import html
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_aria_manifest as lam             # noqa: E402  shared tokenizer (fences + code spans)
import check_widget_visibility_live as wl    # noqa: E402  llms.txt index + retrying fetch

DOCS = lam.DOCS
SITE = wl.SITE
IMG_MD = re.compile(r'!\[([^\]]*)\]\(<([^>]+)>|!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
IMG_TAG = re.compile(r'<img\b[^>]*>', re.I)
SRC_ATTR = re.compile(r'\bsrc="([^"]+)"', re.I)
ASSET = re.compile(r'([^\s/?&%]+\.(?:svg|png|jpe?g|gif|webp))', re.I)


def authored_images(text):
    """[(basename, alt-text)] for the images the page itself asks for; external targets skipped.

    lam.prose, not just the fence stripper: the changelog discusses the image syntax inside inline
    code (`![]()`), and 3 such mentions counted as authored figures until the shared tokenizer was
    used, inflating this file's own denominator.
    """
    out = []
    for line in lam.prose(text).split("\n"):
        for m in IMG_MD.finditer(line):
            target = (m.group(2) or m.group(4) or "").strip()
            if target.startswith(("http://", "https://", "data:")):
                continue
            name = os.path.basename(urllib.parse.unquote(target.split("?")[0].split("#")[0]))
            out.append((name, (m.group(1) or m.group(3) or "").strip()))
    return out


def image_pages():
    rows = []
    for dirpath, _, filenames in os.walk(DOCS):
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn in ("SUMMARY.md", "MANIFEST.md"):
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8").read()
            imgs = authored_images(text)
            if imgs:
                rows.append({"page": os.path.relpath(path, DOCS).replace("\\", "/"),
                             "h1": wl.h1_of(text), "imgs": [n for n, _ in imgs], "alts": imgs})
    rows.sort(key=lambda r: (-len(r["imgs"]), r["page"]))
    return rows


def asset_of(src):
    """The authored filename behind a GitBook proxy URL, or '' when the markup holds no asset.

    Two decodes, because the URL is nested: the attribute is entity-encoded, and its url= param
    is percent-encoded twice over (…%252F03-attention.svg%3Falt%3Dmedia). One decode leaves
    'spaces%2F…%2F03-attention.svg' — a path-looking string whose basename is wrong.
    """
    query = urllib.parse.urlparse(html.unescape(src)).query
    param = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("url", "")
    m = ASSET.findall(urllib.parse.unquote(urllib.parse.unquote(param)))
    return m[-1].lower() if m else ""


def content_imgs(html_text):
    """[(basename, requestable src)] for the page's own images, header chrome excluded."""
    out = []
    for tag in IMG_TAG.finditer(html_text):
        t = tag.group(0)
        if "zoom-image" not in t:
            continue
        m = SRC_ATTR.search(t)
        if m:
            out.append((asset_of(m.group(1)), html.unescape(m.group(1))))
    return out


def check_image(url, tries=4):
    """(None | reason, content-type) for a served image.

    Retries like wl.fetch does: the round-58 census closed one TLS connection mid-sweep
    (URLError on an SVG that answers image/svg+xml on every other run). A judge that reports the
    CDN's mood as a BROKEN defect gets ignored after the second false alarm, and then the axis is
    dead — so a transport error is retried and only named as itself if it persists.
    """
    last = None
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers=wl.UA)
            with urllib.request.urlopen(req, timeout=60) as resp:
                ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                status, body = resp.status, resp.read()
            if status != 200:
                return "HTTP %s" % status, ctype
            if not ctype.startswith("image/"):
                return "content-type=%r" % ctype, ctype
            if len(body) < 200:
                return "body=%dB" % len(body), ctype
            return None, ctype
        except urllib.error.HTTPError as exc:                     # a 4xx/5xx is the answer, not a flake
            return "HTTP %s" % exc.code, ""
        except Exception as exc:                                   # noqa: BLE001  a probe error is a finding
            last = "%s: %s" % (type(exc).__name__, str(exc)[:60])
            time.sleep(2 * (n + 1))
    return "unreachable after %d tries (%s)" % (tries, last), ""


def compare(page, imgs, served):
    """DROPPED/EXTRA per page, over name multisets (a twice-used figure must not mask a miss)."""
    problems = []
    want, got = collections.Counter(imgs), collections.Counter(b for b, _ in served if b)
    for name in sorted(set(want) | set(got)):
        if want[name] > got[name]:
            problems.append("DROPPED %s: authored ![](%s) x%d, live page names it x%d"
                            % (page, name, want[name], got[name]))
        elif got[name] > want[name]:
            problems.append("EXTRA %s: live page serves %s x%d but the source asks x%d"
                            % (page, name, got[name], want[name]))
    unnamed = [s for b, s in served if not b]
    if unnamed:
        problems.append("UNPARSED %s: %d content <img> whose src names no asset file: %s"
                        % (page, len(unnamed), unnamed[0][:110]))
    return problems


def captions(page, html):
    """NOCAPTION: the alt text must be on the page, because on this platform alt IS the caption.

    Measured in round 58: GitBook serves content images as `<img alt=\"\">` followed by
    `<figcaption class=\"text-xs text-center …\">{作者写的 alt}</figcaption>`. So the house rule
    「每图有图注」 is carried by the alt attribute, and an empty or dropped alt is an invisible
    defect locally — the picture simply prints with no caption. Comparing on wl.visible() makes the
    claim about reader-visible text, not about markup that may never paint.
    """
    problems = []
    body = wl.visible(html)
    for name, alt in page["alts"]:
        key = wl.norm(alt)
        if not key:
            problems.append("NOCAPTION %s: ![](%s) has empty alt, so the live figure prints uncaptioned"
                            % (page["page"], name))
        elif len(key) < 6:
            problems.append("WEAKCAPTION %s: alt %r is too short to read as a caption" % (page["page"], alt))
        elif key[:24] not in body:
            problems.append("NOCAPTION %s: alt %r never reaches the served page as visible text"
                            % (page["page"], alt[:40]))
    return problems


def sweep(pages, resolve=True):
    index, ambiguous = wl.page_index(wl.llms_entries())
    assert not ambiguous, "ambiguous published titles make the title join unsafe: %s" % sorted(ambiguous)
    problems, checked, srcs = [], 0, {}
    for r in pages:
        url = index.get(wl.norm(r["h1"]))
        if not url:
            problems.append("NOURL %s (%r) resolves to no live page, so its images were never checked"
                            % (r["page"], r["h1"]))
            continue
        html = wl.fetch(url[:-3] if url.endswith(".md") else url)
        if len(html) < 200000:
            problems.append("SHAPE %s bytes=%d — not a real page, so its images prove nothing"
                            % (r["page"], len(html)))
            continue
        served = content_imgs(html)
        checked += 1
        problems += compare(r["page"], r["imgs"], served) + captions(r, html)
        for base, src in served:
            srcs[src] = base
    census = collections.Counter()
    broken = []
    if resolve and srcs:
        ordered = sorted(srcs)
        with ThreadPoolExecutor(max_workers=8) as pool:
            for src, (err, ctype) in zip(ordered, pool.map(check_image, ordered)):
                name = srcs[src]
                if err:
                    broken.append("BROKEN %s (%s) -> %s" % (err, name, urllib.parse.unquote(src)[:110]))
                    continue
                census[ctype or "unknown"] += 1
                # An authored .svg served as a bitmap is not BROKEN — it loads, it is legible, and
                # the reader never learns the animation they were promised is gone. The round-58
                # census answered image/svg+xml for every SVG that didn't drop the connection, so
                # this leg is a tripwire against a future proxy change, not a fix list.
                if name.endswith(".svg") and ctype in ("image/png", "image/jpeg", "image/webp"):
                    broken.append("RASTERIZED %s served as %s — the file animates, the reader gets a still"
                                  % (name, ctype))
    return checked, len(srcs), problems + broken, census


def live_mutation_control():
    """Prove DROPPED and EXTRA fire against REAL served markup, not just synthetic strings.

    A synthetic compare() control cannot tell a working parser from one that returns nothing: an
    extractor that found zero images on every page would report zero DROPPED and a clean EXTRA
    column, and the axis would read green forever. So the control takes one live page, insists its
    authored list and its <img> list agree, then doctores only the authored side — a figure removed
    must read EXTRA (the page shows something the source never asked for), a ghost added must read
    DROPPED. Both directions firing on real markup is what makes the site-wide zero meaningful.
    """
    index, _ = wl.page_index(wl.llms_entries())
    page = image_pages()[0]
    url = index.get(wl.norm(page["h1"]))
    assert url, "control page %r has no live URL" % page["page"]
    served = content_imgs(wl.fetch(url[:-3] if url.endswith(".md") else url))
    assert served, "control: %s serves no content <img> at all — the extractor is dead" % page["page"]
    assert compare(page["page"], page["imgs"], served) == [], \
        "control page %s is already dirty: %s" % (page["page"], compare(page["page"], page["imgs"], served)[:2])
    kinds = [p.split()[0] for p in compare(page["page"], page["imgs"][1:], served)]
    assert "EXTRA" in kinds, "control: removing an authored figure did not read EXTRA: %s" % kinds
    kinds = [p.split()[0] for p in compare(page["page"], page["imgs"] + ["r58-ghost.svg"], served)]
    assert "DROPPED" in kinds, "control: a ghost figure did not read DROPPED: %s" % kinds
    # the caption leg against the same real markup: a figure the page never captions must fire
    html = wl.fetch(url[:-3] if url.endswith(".md") else url)
    ghost = dict(page, alts=page["alts"] + [("r58-ghost.svg", "这张图在线上根本不存在")])
    assert any(p.startswith("NOCAPTION") for p in captions(ghost, html)), \
        "control: a caption that is never served read clean"
    print("live mutation control on %s: served=%d agrees clean, and doctored expectations fire "
          "EXTRA + DROPPED + NOCAPTION all three" % (page["page"], len(served)))


def controls():
    assert authored_images('x\n![图 A](../.gitbook/assets/foo-bar.svg)\n![外](https://x/y.png)\n') \
        == [("foo-bar.svg", "图 A")], "control: authored extraction broken"
    assert authored_images("```\n![围栏里的示例](./a.svg)\n```") == [], \
        "control: a fenced example counted as an image"
    assert authored_images('行内代码里的 `![](./ghost.png)` 不是图片') == [], \
        "control: an inline-code mention counted as an image"
    assert authored_images('![带标题](./b.png "说明")') == [("b.png", "带标题")], \
        "control: a titled image ref broke the parse"
    assert authored_images("![尖括号](<./c two.svg>)") == [("c two.svg", "尖括号")], \
        "control: <...> target form not handled"
    assert authored_images("![](./d.svg)")[0] == ("d.svg", ""), \
        "control: an empty alt must survive as empty, it is what NOCAPTION looks for"
    # markup taken from this deployment's own served HTML
    real = ('<img data-testid="zoom-image" alt="" src="https://site/~gitbook/image?url=https%3A%2F%2F'
            'x-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fspace%252Fuploads%252Fgit-blob-abc%252F'
            '03-attention.svg%3Falt%3Dmedia&amp;width=768&amp;sign=d2842dc&amp;sv=3" srcSet="a 400w"/>')
    chrome = '<img alt="Logo" class="block dark:hidden" src="https://site/~gitbook/image?url=logo%252Fbadge.svg&amp;sign=x"/>'
    got = content_imgs(real + chrome)
    assert [b for b, _ in got] == ["03-attention.svg"], \
        "control: header chrome leaked in or the content image was lost: %s" % (got,)
    src = got[0][1]
    # hit control for the entity bug: the requestable src must keep the proxy's own percent-encoding
    # (%252F) while '&amp;' becomes '&', or the CDN answers 400 Bad Request.
    assert "&sign=d2842dc" in src and "%252F03-attention.svg" in src and "&amp;" not in src, \
        "control: src entities mis-decoded, requests would 400: %s" % src
    assert asset_of(real) == "03-attention.svg", "control: asset basename wrong after double decode"
    assert asset_of(html.unescape(real).split('src="')[1].split('"')[0]) == "03-attention.svg", \
        "control: asset_of needs the entity-encoded form only"
    assert content_imgs('<img alt="Logo" src="/a.png">') == [], "control: header chrome counted as content"
    assert content_imgs('<p>no img</p><img alt="x">') == [], "control: an <img> with no src counted"
    # the comparison must catch both directions and stay quiet on a match
    imgs = ["a.svg", "a.svg", "b.png"]
    assert compare("p", imgs, [("a.svg", "s"), ("a.svg", "s"), ("b.png", "s")]) == [], \
        "control: a matching page reported problems"
    kinds = [c.split()[0] for c in compare("p", imgs, [("a.svg", "s"), ("b.png", "s"), ("c.svg", "s")])]
    assert kinds == ["DROPPED", "EXTRA"], "control: dropped/extra not both detected: %s" % kinds
    assert check_image(SITE + "/this-asset-does-not-exist-r58.png")[0], "control: the failing-URL probe passed"
    print("controls: authored extraction (fence/inline-code/title/angle-brackets/external), "
          "content-<img> parsing incl. entity decode, DROPPED+EXTRA both fire, failing-URL probe fires")


def main():
    args = sys.argv[1:]
    controls()
    pages = image_pages()
    total = sum(len(r["imgs"]) for r in pages)
    unique = {b for r in pages for b in r["imgs"]}
    print("authored: image-bearing pages=%d local image refs=%d (unique assets=%d: svg=%d png=%d)"
          % (len(pages), total, len(unique),
             sum(1 for u in unique if u.endswith(".svg")), sum(1 for u in unique if u.endswith(".png"))))
    # Floors under the house counts (32 SVG + 8 PNG figures on disk; 43 asset files overall, some
    # of them site chrome). A drop to double digits means the extractor died, not the content.
    assert len(pages) >= 30 and total >= 40, "vacuity: extractor found pages=%d refs=%d" % (len(pages), total)
    live_mutation_control()
    sample = int(args[args.index("--sample") + 1]) if "--sample" in args else len(pages)
    checked, assets, problems, census = sweep(pages[:sample])
    print("live: pages=%d unique served images=%d census=%s problems=%d"
          % (checked, assets, dict(census), len(problems)))
    for p in problems[:40]:
        print("  -", p)
    assert checked >= 5, "vacuity: only %d pages were actually fetched" % checked
    return 1 if problems else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
