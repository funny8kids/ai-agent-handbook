# -*- coding: utf-8 -*-
"""Round 65: does the reader actually get what the authored SVG asks for?

The legibility axis (check_svg_legibility.py) reads the authored file and models the column. This
axis reads the *served* file, because GitBook runs the asset through a sanitizer before a reader
ever sees it: it reorders attributes, drops comments, and — the finding that started this — strips
`paint-order`. A `<text>` written as `fill="#075985" stroke="#f8fafc" stroke-width="3.5"
paint-order="stroke"` is a label with a pale halo to the author and, once the attribute is gone, a
15px glyph buried under a 3.5px pale stroke. Three of those labels on `04-react-loop.svg` were
unreadable live while the offline axis kept reporting the figure clean: the axis and the reader
disagreed, and the reader was right.

Two legs, and they answer different questions:

  offline leg  (always, no network) — no authored asset may lean on a feature the platform is
               known to strip. `KNOWN_STRIPPED` is a measured list, not a guess; it fails the run
               so the house style cannot reintroduce a halo that only works locally.
  live leg     (`--no-live` to skip) — fetch each body figure's served copy off a page that carries
               it, and diff element and attribute multisets against the authored file. Anything the
               sanitizer removes is printed; an element count that drops means the reader sees a
               different picture than the one that was drawn.

Controls, because a ruler that cannot fail is not a ruler:
  * classifier selftest: a planted `paint-order` attribute and a planted `paint-order:` CSS
    declaration must both be caught, and a clean asset must produce zero hits.
  * live selftest: the served copy of a figure is asserted to still be SVG (a conversion to PNG
    would parse as nothing here) and to keep the authored viewBox, so a "no stripped attributes"
    verdict cannot come from having compared against garbage.
  * vacuity floor: at least 25 assets must reach the live comparison, or the run fails instead of
    declaring the axis clean off an empty sample.

Usage:
    python tools/checks/check_svg_sanitizer.py [--no-live] [--only NAME.svg ...]
"""
import argparse
import collections
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import check_svg_legibility as A                                    # noqa: E402
import check_widget_visibility_live as wl                           # noqa: E402
import check_live_images as cli                                     # noqa: E402

ASSETS = os.path.join(A.DOCS, ".gitbook", "assets")
# Measured on the live site (round 65): the sanitizer removes these and the drawing changes.
KNOWN_STRIPPED = {
    "paint-order": "halo strokes paint over their own glyphs; draw the halo as a second, "
                   "fill=\"none\" <text> under the label instead",
}
MIN_ASSETS = 25

_USAGE = {}
_LIVE = {}


def page_usage():
    if not _USAGE:
        _USAGE.update(A.page_usage())
    return _USAGE


# ---------------------------------------------------------------- authored-side classifier
def stripped_uses(text):
    """[(feature, where)] for authored markup that leans on a feature the platform strips."""
    hits = []
    for m in re.finditer(r"<[A-Za-z][^>]*\bpaint-order\s*=", text):
        tag = re.search(r"<([A-Za-z]+)", m.group(0)).group(1)
        hits.append(("paint-order", "attribute on <%s>" % tag))
    for m in re.finditer(r"\bpaint-order\s*:", text):
        hits.append(("paint-order", "CSS declaration"))
    return [(f, w) for f, w in hits if f in KNOWN_STRIPPED]


def offline_leg(only=None):
    offenders = {}
    names = sorted(n for n in os.listdir(ASSETS) if n.endswith(".svg"))
    for name in names:
        if only and name not in only:
            continue
        hits = stripped_uses(io.open(os.path.join(ASSETS, name), encoding="utf-8").read())
        if hits:
            offenders[name] = hits
    print("authored assets=%d  relying on a stripped feature=%d" % (len(names), len(offenders)))
    for name, hits in sorted(offenders.items()):
        feat = collections.Counter(f for f, _ in hits)
        print("  %-38s %s" % (name, dict(feat)))
        for f, w in hits:
            print("      %s @ %s -> %s" % (f, w, KNOWN_STRIPPED[f]))
    return offenders


def classifier_selftest():
    planted = ('<svg><text x="1" y="2" fill="#000" stroke="#fff" stroke-width="4" '
               'paint-order="stroke">label</text></svg>')
    css = '<svg><defs><style>.lbl{font-size:12px;paint-order:stroke fill}</style></defs></svg>'
    clean = '<svg><text x="1" y="2" fill="none" stroke="#fff" stroke-width="4">label</text>' \
            '<text x="1" y="2" fill="#000">label</text></svg>'
    assert [f for f, _ in stripped_uses(planted)] == ["paint-order"], \
        "selftest: a planted paint-order attribute went uncaught"
    assert [f for f, _ in stripped_uses(css)] == ["paint-order"], \
        "selftest: a planted paint-order CSS declaration went uncaught"
    assert stripped_uses(clean) == [], "selftest: the two-text halo reads as a defect"
    print("classifier selftest ok: attribute and CSS uses caught, the two-text halo clean")


# ---------------------------------------------------------------- served-side comparison
def live_url_for(rel, index):
    text = io.open(os.path.join(A.DOCS, rel.replace("/", os.sep)), encoding="utf-8").read()
    if rel == "README.md":
        return wl.SITE + "/"
    m = re.search(r"^# (.+)$", text, flags=re.M)
    url = index.get(wl.norm(m.group(1).strip())) or ""
    assert url, "no live URL for %s" % rel
    return url[:-3] if url.endswith(".md") else url


def counts(xml_text):
    root = ET.fromstring(xml_text)
    els, attrs = collections.Counter(), collections.Counter()
    for el in root.iter():
        tag = re.sub(r"^\{.*\}", "", el.tag)
        els[tag] += 1
        for k in el.attrib:
            attrs["%s@%s" % (tag, re.sub(r"^\{.*\}", "", k))] += 1
    return root, els, attrs


def served_copy(name, index):
    """The bytes a reader's browser fetches for this asset, or None when it is not on the page."""
    usage = page_usage().get(name) or []
    pages = [p for p in usage if p != "README.md"] or usage
    for rel in pages:
        if rel not in _LIVE:
            _LIVE[rel] = wl.fetch(live_url_for(rel, index))
        srcs = [s for b, s in cli.content_imgs(_LIVE[rel]) if b == name]
        if srcs:
            return wl.fetch(srcs[0], binary=True).decode("utf-8", "replace"), rel
    return None, None


def live_leg(only=None):
    usage = page_usage()
    names = sorted(n for n in usage if n.endswith(".svg") and os.path.isfile(os.path.join(ASSETS, n)))
    if only:
        names = [n for n in names if n in only]
    index, ambiguous = wl.page_index(wl.llms_entries())
    assert not ambiguous, "ambiguous published titles: %s" % sorted(ambiguous)
    stripped, dropped, checked = collections.Counter(), [], 0
    for name in names:
        raw, rel = served_copy(name, index)
        if raw is None:
            print("  %-38s NOT-SERVED (no <img> naming it on %s)" % (name, rel))
            continue
        try:
            local_root, le, la = counts(io.open(os.path.join(ASSETS, name), encoding="utf-8").read())
            served_root, se, sa = counts(raw)
        except ET.ParseError as exc:
            print("  %-38s NOT-SVG served copy will not parse: %s | head=%r" % (name, exc, raw[:40]))
            dropped.append(name)
            continue
        assert served_root.get("viewBox") == local_root.get("viewBox"), \
            "%s: served viewBox %r != authored %r" % (name, served_root.get("viewBox"),
                                                      local_root.get("viewBox"))
        checked += 1
        lost_attrs = la - sa
        lost_els = le - se
        if lost_attrs or lost_els:
            print("  %-38s lost %d attr use(s) %s, %d element use(s) %s"
                  % (name, sum(lost_attrs.values()), dict(lost_attrs),
                     sum(lost_els.values()), dict(lost_els)))
            for k in lost_attrs:
                stripped[k.split("@")[-1]] += lost_attrs[k]
    print("served copies compared=%d of %d assets" % (checked, len(names)))
    assert checked >= MIN_ASSETS, \
        "only %d served copies reached the comparison (floor %d): the axis read a near-empty sample" \
        % (checked, MIN_ASSETS)
    return stripped, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-live", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    classifier_selftest()
    offenders = offline_leg(args.only)
    stripped = collections.Counter()
    if not args.no_live:
        stripped, dropped = live_leg(args.only)
        new = {k for k in stripped if k not in KNOWN_STRIPPED}
        if new:
            print("\nnewly stripped by the platform: %s" % sorted(new))
            print("  add them to KNOWN_STRIPPED only after confirming the drawing really changed.")
    else:
        dropped = []
        print("live leg skipped (--no-live): the strip list is only as current as the last run")

    print("\n-- verdict --")
    bad = bool(offenders) or bool(stripped) or bool(dropped)
    if offenders:
        print("  FAIL %d authored asset(s) lean on a stripped feature" % len(offenders))
    if stripped:
        print("  FAIL served copies are missing %s" % dict(stripped))
    if dropped:
        print("  FAIL served copies that are not parseable SVG: %s" % dropped)
    if not bad:
        print("  clean: no authored figure depends on markup the reader does not get")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
