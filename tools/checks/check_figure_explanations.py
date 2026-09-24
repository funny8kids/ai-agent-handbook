"""Round 76 axis: every figure must hand the reader something to take away.

The homepage has always printed 「217 张 Mermaid，171 张带图注、46 张由图前或图后实质引导语解释，
逐块量过：0 张裸图」. Those three numbers were true, but nothing in `tools/checks` could reproduce
them — a hand count quoted in prose rots the moment a later round moves a block, and the rot is
silent because the sentence keeps reading confidently. Same class as round 57 (a README-cited judge
that was never in the repo) and round 61 (a sentence promising a source with nothing to click).

What counts, per block, in order:
  * CAPTION     — an italic `*《图：…》*` line directly before or directly after the fence.
  * GUIDED      — otherwise, a substantive prose paragraph adjacent to the fence (either side).
  * BARE        — neither. The reader gets a diagram and no sentence telling them what to read.
A caption or carrier that is only a deictic pointer (「如下图所示」「见图」…) does not buy coverage:
that is the sentence this book explicitly claims no figure relies on, so it is judged as VAPID
rather than counted as guidance.

Not a carrier, by design: headings (a section title names the topic, it does not interpret the
figure), list items and table rows (they carry their own claims and were never the promised
「引导语」), blockquotes and `{% hint %}` openers, and other images.

The first version of this ruler reported 27 bare figures, and every one of them was the ruler's
fault: it walked back from the closing fence to find the "line before", so it read the last node
definition *inside the diagram* as if it were prose. That false-red is now a standing control
(`plant_bare` ends its diagram with a prose-shaped line on purpose). A bar this easy to fail in both
directions earns a counterexample in each direction: 171 of 217 blocks really do carry a caption,
and a block with nothing around it really must read BARE.
"""
import io
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_aria_manifest as lam        # noqa: E402  shared inline-code tokenizer
ROOT = os.path.dirname(os.path.dirname(HERE))
DOCS = os.path.join(ROOT, "docs")

CAPTION = re.compile(r"^\*《图：(.+)》\*\s*$")
# Deictic-only: points at the figure, says nothing about it.
VAPID = re.compile(r"^(如下图|下图所|见下图|如图所|如下所|见图|看下图|下图是|图如下|下图为)")
DIAGRAM_HEAD = re.compile(r"^```mermaid\b")
FENCE_END = re.compile(r"^```\s*$")
# Characters that carry no information when judging how much a sentence actually says.
NOISE = re.compile(r"[`*_\[\]()【】「」《》：:，,。.、;；——（）()\"'!?！？]")
MIN_INFO = 12  # information units below this reads as a pointer, not an explanation

SKIP_DIRS = (os.path.join(".gitbook",),)


def info_units(s):
    return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", NOISE.sub("", s)))


def neighbour_kind(line):
    """Classify the authored line sitting next to a figure, as the reader would meet it."""
    s = line.strip()
    if not s:
        return "blank"
    if CAPTION.match(s):
        return "caption"
    if s.startswith("#"):
        return "heading"
    if s.startswith(("|", "- ", "* ", "+ ")) or re.match(r"^\d+[.)] ", s):
        return "list"
    if s.startswith("{%"):
        return "widget"
    if s.startswith(">"):
        return "quote"
    if s.startswith("![") or s.startswith("```"):
        return "other-figure"
    return "prose" if info_units(s) >= MIN_INFO else "short"


def find_blocks(lines):
    """Yield (open_idx, close_idx) for every top-level ```mermaid fence in the file."""
    i = 0
    while i < len(lines):
        if DIAGRAM_HEAD.match(lines[i].strip()):
            j = i + 1
            while j < len(lines) and not FENCE_END.match(lines[j].strip()):
                j += 1
            if j < len(lines):
                yield i, j
            i = j + 1
        else:
            i += 1


def audit(lines):
    """Return one verdict per mermaid block: (kind, line_no, detail)."""
    out = []
    for i, j in find_blocks(lines):
        b = i - 1
        while b >= 0 and not lines[b].strip():
            b -= 1
        a = j + 1
        while a < len(lines) and not lines[a].strip():
            a += 1
        before = lines[b].strip() if b >= 0 else ""
        after = lines[a].strip() if a < len(lines) else ""
        kb, ka = neighbour_kind(before), neighbour_kind(after)

        cap = None
        if kb == "caption":
            cap = CAPTION.match(before).group(1)
        elif ka == "caption":
            cap = CAPTION.match(after).group(1)

        if cap is not None:
            if VAPID.match(cap.strip()):
                out.append(("VAPID-CAPTION", i + 1, cap[:70]))
            elif info_units(cap) < MIN_INFO:
                out.append(("THIN-CAPTION", i + 1, cap[:70]))
            else:
                out.append(("CAPTION", i + 1, cap[:70]))
            continue

        carriers = [l for k, l in ((kb, before), (ka, after)) if k == "prose"]
        if not carriers:
            out.append(("BARE", i + 1, "before=%s after=%s" % (kb, ka)))
        elif any(not VAPID.match(c.strip()) for c in carriers):
            out.append(("GUIDED", i + 1, max(carriers, key=info_units)[:70]))
        else:
            out.append(("VAPID", i + 1, carriers[0][:70]))
    return out


def walk_pages():
    for dirpath, dirnames, filenames in os.walk(DOCS):
        dirnames[:] = [d for d in dirnames
                       if not os.path.relpath(os.path.join(dirpath, d), DOCS).startswith(SKIP_DIRS)]
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            yield (os.path.relpath(path, DOCS).replace(os.sep, "/"), path,
                   io.open(path, encoding="utf-8").read().splitlines())


FINDING = ("BARE", "VAPID", "VAPID-CAPTION", "THIN-CAPTION", "NO-EXPLANATION",
           "VAPID-IMAGE-CAPTION", "UNRESOLVED")

# Reader-facing images, as opposed to a diagram written in this repo's own markup language.
IMAGE_REF = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)")
# The cover banner is decoration, not a figure: there is nothing for it to "tell" the reader.
# Closed list, checked against files that still exist — a renamed or newly added image cannot buy
# its way out of the rule by looking like this one.
DECORATIVE = {"README.md::.gitbook/assets/banner-home.svg"}
EXAMPLE_ALTS = ("", "alt")  # markup illustrations in the changelog and the style guide


def audit_images(rel, path, lines):
    """One verdict per reader-facing image placement in a page.

    Quoted markup is not a figure. Two doors lead there and both are closed on purpose: a fenced
    block, and an inline code span. The second one is not hypothetical — the day this ruler landed,
    the changelog entry describing it wrote ``![alt](../.gitbook/assets/xxx.svg)`` in backticks to
    explain the first door, and the axis counted a 7th markup example and went red on its own
    documentation (`live_aria_manifest.strip_code_spans` is the repo's CommonMark-correct span
    tokenizer, so the two rulers cannot disagree about what is code).

    A reference that resolves to no file in this repo is likewise a markup example (the style guide
    and the changelog both illustrate the syntax for real, unquoted) — but that escape hatch is
    exactly where a mistyped real path would hide, so the caller pins how many such examples exist
    and what their alt text looks like.
    """
    out = []
    in_fence = False
    for i, raw in enumerate(lines):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = lam.strip_code_spans(raw)
        # A reference the reader never meets: quoted markup, counted so the exemption stays visible
        # rather than becoming a way to make a figure disappear.
        for q in IMAGE_REF.finditer(raw):
            if q.group(0) not in stripped:
                out.append(("QUOTED", i + 1, "%s alt=%r" % (q.group(2), q.group(1)[:20])))
        for m in IMAGE_REF.finditer(stripped):
            alt, target = m.group(1), m.group(2)
            if target.startswith(("http://", "https://")):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path),
                                                     target.replace("/", os.sep)))
            if not os.path.isfile(resolved):
                # Not quoted, not fenced, and pointing at nothing: that is a broken path, not an
                # example. Before this file landed, 6 such refs were read as "documentation
                # examples"; measured again after quoting was handled properly, all 6 (plus the 1
                # this round's own changelog entry added) sit inside inline code, and the count of
                # unquoted ones is 0 — which is the number worth asserting.
                out.append(("UNRESOLVED", i + 1, "%s alt=%r" % (target, alt[:20])))
                continue
            a = i + 1
            while a < len(lines) and not lines[a].strip():
                a += 1
            below = CAPTION.match(lines[a].strip()) if a < len(lines) else None
            b = i - 1
            while b >= 0 and not lines[b].strip():
                b -= 1
            above = CAPTION.match(lines[b].strip()) if b >= 0 else None
            cap = below or above
            if cap is None:
                if "%s::%s" % (rel, target) in DECORATIVE:
                    out.append(("DECORATIVE", i + 1, target))
                else:
                    out.append(("NO-EXPLANATION", i + 1, "%s alt=%r" % (target, alt[:30])))
            elif VAPID.match(cap.group(1).strip()):
                out.append(("VAPID-IMAGE-CAPTION", i + 1, "%s: %s" % (target, cap.group(1)[:50])))
            else:
                out.append(("IMAGE-CAPTION", i + 1, cap.group(1)[:60]))
    return out


def run(quiet=False):
    tally, findings = {}, []
    pages = quoted = 0
    quoted_detail = []
    for rel, path, lines in walk_pages():
        pages += 1
        for kind, no, detail in audit(lines) + audit_images(rel, path, lines):
            tally[kind] = tally.get(kind, 0) + 1
            if kind == "QUOTED":
                quoted += 1
                quoted_detail.append("%s L%d %s" % (rel, no, detail))
            elif kind in FINDING:
                findings.append("%s %s:%d %s" % (kind, rel, no, detail))
    blocks = sum(v for k, v in tally.items() if k in
                 ("CAPTION", "GUIDED", "BARE", "VAPID", "VAPID-CAPTION", "THIN-CAPTION"))
    placements = sum(v for k, v in tally.items() if k in
                     ("IMAGE-CAPTION", "NO-EXPLANATION", "VAPID-IMAGE-CAPTION", "DECORATIVE"))
    for entry in DECORATIVE:
        target = entry.split("::", 1)[1]
        assert os.path.isfile(os.path.join(DOCS, target.replace("/", os.sep))), \
            "exemption %s points at a file that no longer exists" % entry
    assert pages >= 190, "vacuity: only %d pages scanned, the walk is broken" % pages
    assert blocks >= 200, ("vacuity: only %d mermaid blocks parsed, the fence walk is broken"
                           % blocks)
    assert tally.get("CAPTION", 0) >= 150, (
        "floor: only %d captioned blocks — a caption regex that stops matching is a broken ruler, "
        "not 60 bare figures" % tally.get("CAPTION", 0))
    # Every markup example in this book is *quoted* (inline code or a fenced block), so the
    # unquoted-and-unresolvable bucket must stay empty: a mistyped real path lands there and goes
    # red as UNRESOLVED. The quoted bucket is a FLOOR, not an equality, and the reason is this
    # round's own log: the sentence that explains the rule must quote the syntax it explains, so
    # writing it moved the count 7 → 9 and an `== 7` would have been a tax on documenting the axis.
    # What keeps the exemption honest instead is the alt-text test below (a real figure carries a
    # real caption, an example carries `alt` or nothing) plus `placements == 45`: a figure hidden
    # inside backticks would lower that number, and it is pinned as an equality.
    assert quoted >= 7, ("only %d quoted image examples: %s — the count falling means a page stopped "
                         "quoting its own markup, i.e. one of these is now a reader-visible figure "
                         "the axis used to exempt" % (quoted, quoted_detail))
    assert all(e.split(" alt=")[-1].strip() in ("''", "'alt'") for e in quoted_detail), \
        "a quoted image carries real alt text, so it is probably a figure mis-wrapped in code: %s" \
        % quoted_detail
    assert tally.get("UNRESOLVED", 0) == 0, "unquoted image path resolves to no file"
    assert placements == 45, "image placements moved to %d; the homepage figure count needs updating" % placements
    if not quiet:
        order = ["CAPTION", "GUIDED", "BARE", "VAPID", "VAPID-CAPTION", "THIN-CAPTION",
                 "IMAGE-CAPTION", "NO-EXPLANATION", "VAPID-IMAGE-CAPTION", "DECORATIVE", "QUOTED"]
        print("figure explanations: pages=%d diagrams=%d placements=%d captions=%d %s findings=%d"
              % (pages, blocks, placements,
                 tally.get("CAPTION", 0) + tally.get("IMAGE-CAPTION", 0),
                 " ".join("%s=%d" % (k.lower(), tally[k]) for k in order if k in tally),
                 len(findings)))
        for f in findings:
            print("  " + f)
    return tally, findings


# ---------------------------------------------------------------- controls

DIAGRAM = ["```mermaid", "graph LR", "  %%{init}%%", "  A[start] --> B[end]",
           "plain prose-looking tail line with plenty of Chinese words 一二三四五六七八"]


def synth(text):
    return audit(text.splitlines())


def plant_bare():
    """A diagram with nothing around it must read BARE, even though its own last line reads like
    prose — the exact mistake the first version of this ruler made."""
    body = DIAGRAM + ["```"]
    got = synth("# T\n\n" + "\n".join(body) + "\n")
    assert got and got[0][0] == "BARE", "control: bare figure read %s" % got


def plant_caption_below_and_above():
    body = DIAGRAM + ["```", "", "*《图：离线切块与在线检索唯一的接口是向量库》*"]
    got = synth("# T\n\n" + "\n".join(body) + "\n")
    assert got[0][0] == "CAPTION", "control: caption below read %s" % got[0]
    above = ["# T", "", "*《图：离线切块与在线检索唯一的接口是向量库》*", ""] + body[:5] + ["```"]
    got = synth("\n".join(above) + "\n")
    assert got[0][0] == "CAPTION", "control: caption above read %s" % got[0]


def plant_guided():
    lead = "这张图的重点不是节点数量，而是失败回滚那条虚线：报错原文必须回到对话里。"
    body = ["# T", "", lead, ""] + DIAGRAM + ["```", "", "## 下一节"]
    got = synth("\n".join(body) + "\n")
    assert got[0][0] == "GUIDED", "control: prose lead-in read %s" % got[0]


def plant_vapid():
    for line, want in (("*《图：如下图所示》*", "VAPID-CAPTION"),
                       ("*《图：见下图》*", "VAPID-CAPTION")):
        body = ["# T", ""] + DIAGRAM + ["```", "", line]
        got = synth("\n".join(body) + "\n")
        assert got[0][0] == want, "control: pointer caption %r read %s" % (line, got[0])
    body = ["# T", "", "如下图所示。", ""] + DIAGRAM + ["```", "", "## 下一节"]
    got = synth("\n".join(body) + "\n")
    assert got[0][0] in ("BARE", "VAPID"), "control: pointer lead-in read %s" % got[0]


def heading_is_not_a_carrier():
    body = ["# T", "", "## 管线图", ""] + DIAGRAM + ["```", "", "## 下一节"]
    got = synth("\n".join(body) + "\n")
    assert got[0][0] == "BARE", "control: a bare figure framed by two headings read %s" % got[0]


def list_and_widget_are_not_carriers():
    body = ["# T", "", "- 一条列表项，里面写满了看起来足够长的说明文字内容", ""] + DIAGRAM + \
           ["```", "", "{% hint style=\"tip\" %}"]
    got = synth("\n".join(body) + "\n")
    assert got[0][0] == "BARE", "control: list/hint neighbours read %s" % got[0]


def non_mermaid_fence_ignored():
    body = ["# T", "", "```python", "x = 1", "```"]
    assert synth("\n".join(body) + "\n") == [], "control: a python fence was audited as a figure"


def image_leg_controls():
    real = os.path.join(DOCS, "02-agent-basics", "x.md")
    asset = "../.gitbook/assets/02-agent-loop.svg"
    cap = "*《图：循环的四步各自缺了什么》*"

    def verdicts(lines, path=real, rel="02-agent-basics/x.md"):
        return [v[0] for v in audit_images(rel, path, lines)]

    got = verdicts(["# T", "", "![%s](%s)" % ("agent loop", asset), "", cap])
    assert got == ["IMAGE-CAPTION"], "control: captioned image read %s" % got
    got = verdicts(["# T", "", "![%s](%s)" % ("agent loop", asset), "", "## 下一节"])
    assert got == ["NO-EXPLANATION"], "control: uncaptioned image read %s" % got
    got = verdicts(["# T", "", "![%s](%s)" % ("agent loop", asset), "", "*《图：如下图所示》*"])
    assert got == ["VAPID-IMAGE-CAPTION"], "control: pointer caption on an image read %s" % got
    got = verdicts(["# T", "", "![%s](%s)" % ("agent loop", asset)])
    assert got == ["NO-EXPLANATION"], "control: image as the last line read %s" % got
    got = verdicts(["# T", "", "![placeholder](../.gitbook/assets/does-not-exist-zz.svg)"])
    assert got == ["UNRESOLVED"], "control: an unquoted dead path was not judged: %s" % got
    banner = os.path.join(DOCS, "README.md")
    got = [v[0] for v in audit_images("README.md", banner,
                                      ["# T", "", "![AI Agent 学习手册 · 从原理到生产](.gitbook/assets/banner-home.svg)"])]
    assert got == ["DECORATIVE"], "control: the cover banner lost its exemption: %s" % got
    got = verdicts(["# T", "", "```", "![%s](%s)" % ("agent loop", asset), "```", "", "## 下一节"])
    assert got == [], "control: an image inside a fenced example was audited: %s" % got
    # The door this ruler landed on: the round-76 changelog entry quoted the syntax in backticks to
    # explain the fenced-example exemption, and the axis counted its own documentation as a figure.
    got = verdicts(["# T", "", "写法示例只有 6 处（互教的 `![alt](%s)`），不是读者见的图" % asset])
    assert got == ["QUOTED"], "control: a quoted markup example was judged as a figure: %s" % got
    # ...and the exemption must not be buyable: the same reference outside backticks still gets judged
    got = verdicts(["# T", "", "读者见得 ![agent loop](%s)" % asset, "", "## 下一节"])
    assert got == ["NO-EXPLANATION"], "control: quoting markup silenced a real figure: %s" % got
    return 9


def live_leg_controls():
    """The live leg's own comparison, proven satisfiable offline on markup shaped like the SSR.

    Measured shape: GitBook publishes an italic caption as
    `<p ...><i class="font-italic">《图：…》</i></p>` and the figure itself as an inline `<svg>`
    carrying `<style>` and `<foreignObject>` (which is why one 1.1 MB page yields only ~4.8 KB of
    visible text — the diagram's labels live inside the svg and are not judged here).
    """
    sys.path.insert(0, HERE)
    import check_widget_visibility_live as wl

    caption = "图：离线侧——文档切块、向量化后入库；这一步的产物只服务下图的在线链路"
    title = "RAG 检索链路 · 对照页"
    served = ('<html><head><style>.x{color:red}</style></head><body>'
              '<h1>%s</h1><div class="mermaid"><svg><style>.k{}</style>'
              '<foreignObject><div>x</div></foreignObject></svg></div>'
              '<p class="margin-top-05 text-start self-start justify-start">'
              '<i class="font-italic">《%s》</i></p></body></html>' % (title, caption))
    body = crush(wl.visible(served))
    assert crush(caption) in body, "control: the live leg cannot find a caption it was handed"
    assert crush(title) in body, "control: the H1 positive control fails on synthetic SSR markup"
    assert crush("本节不存在的一句对照文本 CTRL76") not in body, "control: phantom matched"
    # Why crush, specifically: the comparison this leg shipped with first is reproduced here and
    # asserted to fail, so nobody "simplifies" the normalisation back into a punctuation match.
    assert caption[:24] not in wl.visible(served), \
        "control: the pre-fix comparison now matches, so the crush rationale is stale"
    return 3


def controls():
    for fn in (plant_bare, plant_caption_below_and_above, plant_guided, plant_vapid,
               heading_is_not_a_carrier, list_and_widget_are_not_carriers,
               non_mermaid_fence_ignored):
        fn()
    n_img = image_leg_controls()
    return 7 + n_img + live_leg_controls()


def real_page_mutation_control():
    """Delete one shipped caption in a copy: that page must gain exactly one BARE finding, and the
    reading must return to baseline when the caption goes back.

    Only caption-only blocks qualify. Dropping a caption from a figure that also has a prose
    neighbour correctly reads GUIDED afterwards — the first draft of this control asserted +1 on
    such a block (00-index/learning-path.md) and failed, which was the control being honest about
    the content, not about the ruler.
    """
    tmp = tempfile.mkdtemp(prefix="r76fig-")
    tried = picked = 0
    try:
        for rel, _path, lines in walk_pages():
            base = audit(lines)
            base_n = sum(1 for v in base if v[0] in FINDING)
            starts = [i for i, v in enumerate(lines) if DIAGRAM_HEAD.match(v.strip())]
            for idx, verdict in enumerate(base):
                if verdict[0] != "CAPTION" or idx >= len(starts):
                    continue
                k = starts[idx]
                while k < len(lines) and not FENCE_END.match(lines[k].strip()):
                    k += 1
                a = k + 1
                while a < len(lines) and not lines[a].strip():
                    a += 1
                if a >= len(lines) or not CAPTION.match(lines[a].strip()):
                    continue
                tried += 1
                mutated = lines[:a] + [""] + lines[a + 1:]
                after = audit(mutated)
                after_n = sum(1 for v in after if v[0] in FINDING)
                if after_n == base_n:
                    continue  # this figure also has a prose carrier; correctly still covered
                assert after_n == base_n + 1, \
                    "control: dropping a caption on %s moved findings %d -> %d" % (rel, base_n, after_n)
                assert sum(1 for v in audit(lines) if v[0] in FINDING) == base_n, \
                    "control: baseline drifted on %s" % rel
                picked += 1
                break
            if picked >= 6:
                break
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert picked == 6, "control: only %d/%d caption drops actually exposed a figure" % (picked, tried)
    return picked, tried


CRUSH_CHARS = re.compile(r"[^0-9a-z\u4e00-\u9fff]+")


def crush(s):
    """Reader-visible comparison form: the character class wl.visible() keeps, spaces removed.

    Both sides of the live caption compare run through this. wl.visible() turns 《, ： and every
    tag boundary into a space, so a probe that keeps the authored punctuation can only ever
    report LOST — which is exactly what this leg's first run did to 8 perfectly good captions.
    """
    return CRUSH_CHARS.sub("", (s or "").lower())


def live_captions(sample=8):
    """Do the authored captions actually reach the reader? Offline text is not the reader's page.

    The captions here are italic prose, which the image axis (`check_live_images.py`, NOCAPTION)
    never looks at — it only pairs `<img>` elements. So this leg joins each sampled page to its
    published address through llms.txt, crushes the served HTML the way a reader's eye does, and
    requires the caption text to be in it.

    The crushing has to be symmetric, and the first run of this leg proves what happens when it is
    not: 8 pages sampled, 8/8 captions reported LOST, while the served HTML verifiably contains
    `<i class="font-italic">《图：AI 的概念收窄到 ML 再到 DL…》</i>`. The ruler compared the
    authored text (punctuation and all) against `wl.visible()`, which replaces every non-CJK/alnum
    run — including 《 , ： and the tag boundaries — with a single space. No caption could ever
    have matched, so the finding was the probe's, not the book's. `crush()` normalises both sides
    the same way and drops spaces entirely, because a space injected at a tag boundary is not
    something the reader's eye stops for.
    """
    sys.path.insert(0, HERE)
    import check_widget_visibility_live as wl

    index, ambiguous = wl.page_index(wl.llms_entries())
    assert not ambiguous, "ambiguous published titles make the join unsafe: %s" % sorted(ambiguous)
    picked, problems, checked, absent = 0, [], 0, 0
    for rel, _path, lines in walk_pages():
        if picked >= sample:
            break
        caps = [v for v in audit(lines) if v[0] == "CAPTION"]
        if not caps:
            continue
        h1 = wl.h1_of("\n".join(lines))
        url = index.get(wl.norm(h1))
        if not url:
            problems.append("NOURL %s (%r) has no published page to check" % (rel, h1))
            continue
        html = wl.fetch(url[:-3] if url.endswith(".md") else url)
        if len(html) < 200000:
            problems.append("SHAPE %s bytes=%d — not a real page" % (rel, len(html)))
            continue
        body = crush(wl.visible(html))
        # Positive control on a string this page certainly publishes; without it a blind probe
        # reports every caption as lost (see live_captions' docstring).
        if crush(h1) not in body:
            problems.append("BLIND %s: the probe cannot even find the page's own H1 %r" % (rel, h1))
            continue
        # control: a sentence this page never authored must read absent
        if crush("本节不存在的一句对照文本 CTRL76") in body:
            problems.append("BLIND live probe on %s matches text that was never authored" % rel)
            continue
        for kind, no, detail in caps:
            checked += 1
            if crush(detail) not in body:
                absent += 1
                problems.append("LOST %s:%d caption never reaches the published page: %s"
                                % (rel, no, detail[:50]))
        picked += 1
    print("live captions: pages=%d captions=%d still-absent=%d problems=%d"
          % (picked, checked, absent, len(problems)))
    for p in problems:
        print("  " + p)
    assert picked >= sample, "live leg sampled only %d pages" % picked
    # Green by silence is not green: the page count alone would still pass if the join found no
    # caption to compare, so the comparison count is floored too.
    assert checked >= sample, "live leg compared only %d captions over %d pages" % (checked, picked)
    return problems


def main():
    n = controls()
    print("controls ok (%d planted cases, both directions: bare must fire, caption/guided must not)" % n)
    pages, tried = real_page_mutation_control()
    print("live mutation ok (dropping a real caption exposes the figure on %d/%d pages tried)"
          % (pages, tried))
    # Both readings print under --live: the offline number is the one README quotes, and a green
    # live leg would otherwise hide a red authored page.
    tally, findings = run()
    if "--live" in sys.argv:
        findings += live_captions(sample=12)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
