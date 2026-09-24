"""GitBook block-tag pairing check over every page in docs/, plus the widget inventory the
homepage quotes.

Tokens are matched exactly by name, so {% endstep %} and {% endstepper %} can never be
conflated. Reports unclosed openers, closers with no opener, and nesting-order violations.
Carries its own controls: a phantom that must fail, plus regressions for the two blind
spots this judge had when it was written (a '%' inside an attribute, and inline-code
mentions of tag syntax).

The inventory leg (round 77) exists because docs/README.md advertises "N 个提示卡 + M 组分步
演示（K 步）+ …" and until now nothing in tools/checks could reproduce those digits — the same
defect round 76 landed a judge for (an unfunded README statistic). It read 251 while the tree
held 257, stale since round 54. Counting reuses this file's own tokenizer, so the pairing judge
and the inventory judge cannot disagree about what is a widget.
"""
import io, os, re, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs"))

PAIRS = {"hint": "endhint", "tabs": "endtabs", "tab": "endtab",
         "stepper": "endstepper", "step": "endstep", "details": "enddetails",
         "columns": "endcolumns", "column": "endcolumn", "card": "endcard",
         "expandable": "endexpandable", "accordion": "endaccordion",
         "accordion-item": "endaccordion-item", "toggle": "endtoggle",
         "blockquote": "endblockquote"}
CLOSER_OF = {v: k for k, v in PAIRS.items()}
# GitBook terminates a tag with %}, so a bare % inside an attribute (title="...±1% 容差") is
# legal and must not truncate the match. Inline code spans like `{% hint %}` are prose.
TOKEN = re.compile(r"\{%-?\s*([a-zA-Z-]+)((?:%(?!\})|[^%])*)%\}")
INLINE_CODE = re.compile(r"``.+?``|`[^`\n]*`")


def in_fence_flags(text):
    flags, open_ = [], False
    for line in text.split("\n"):
        if re.match(r"^\s*(```|~~~)", line):
            open_ = not open_
            flags.append(False)
            continue
        flags.append(not open_)
    return flags


def scan(text):
    lines = text.split("\n")
    flags = in_fence_flags(text)
    stack, errs = [], []
    for ln, line in enumerate(lines):
        if ln < len(flags) and not flags[ln]:
            continue
        line = INLINE_CODE.sub(" ", line)
        for m in TOKEN.finditer(line):
            name = m.group(1)
            if name in PAIRS:
                stack.append((name, ln + 1))
            elif name in CLOSER_OF:
                want = CLOSER_OF[name]
                if not stack:
                    errs.append("L%d: {%% %s %%} with no opener" % (ln + 1, name))
                elif stack[-1][0] != want:
                    errs.append("L%d: {%% %s %%} closes {%% %s %%} but innermost open is "
                                "{%% %s %%} (opened L%d)" % (ln + 1, name, want,
                                                             stack[-1][0], stack[-1][1]))
                    idx = next((i for i in range(len(stack) - 1, -1, -1) if stack[i][0] == want), None)
                    if idx is None:
                        errs.append("   -> no matching opener at all for %s" % name)
                    else:
                        del stack[idx:]
                else:
                    stack.pop()
    for name, ln in stack:
        errs.append("L%d: {%% %s %%} never closed" % (ln, name))
    return errs


def count_openings(text):
    """Reader-visible widget openings per tag name — the same walk the pairing judge uses.

    Reusing `in_fence_flags` + `INLINE_CODE` + `TOKEN` here is the point: docs/README.md quotes an
    inventory of these widgets, and a second counter with its own idea of what counts would give the
    homepage two defensible numbers for the same tree (rounds 56-57 lived through exactly that with
    the formula count, which is why one metric gets one judge). Closers are not openings — `endhint`
    is a distinct name in `CLOSER_OF`, so a stray `{% endtabs %}` cannot inflate `tabs`.
    """
    lines = text.split("\n")
    flags = in_fence_flags(text)
    counts = {}
    for ln, line in enumerate(lines):
        if ln < len(flags) and not flags[ln]:
            continue
        for m in TOKEN.finditer(INLINE_CODE.sub(" ", line)):
            if m.group(1) in PAIRS:
                counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts


# The inventory sentence in docs/README.md, in the homepage's own words. The judge parses the number
# out of the prose instead of hard-coding it: that keeps the sentence the thing under test, so moving
# a digit without moving the tree goes red, and rewriting the sentence into a different shape goes
# red too (a judge that silently stops reading the prose is how round 76's statistic stayed stale).
INVENTORY_RE = re.compile(
    r"\*\*(\d+) 个 GitBook 原生提示卡 \+ (\d+) 组分步演示（(\d+) 步）\+ (\d+) 组可点标签（(\d+) 个页签）\*\*")
# Family → (the count the prose names, what the authoring call it). `hint` prose-counts every card
# because each `{% hint %}` is one card; `stepper`/`step` and `tabs`/`tab` are groups and members.
INVENTORY_KEYS = {"hint": "提示卡", "stepper": "分步演示组", "step": "分步演示步",
                  "tabs": "可点标签组", "tab": "页签"}


def inventory_checks(tally, per_page, quoted):
    """Assert the homepage sentence against the tree, and prove the 口径 actually bites."""
    readme = io.open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    m = INVENTORY_RE.search(readme)
    assert m, ("README's widget inventory sentence no longer matches the shape the judge reads — "
               "re-point INVENTORY_RE instead of letting this leg go quiet")
    claimed = dict(zip(INVENTORY_KEYS, [int(g) for g in m.groups()]))
    bad = {k: (claimed[k], tally.get(k, 0)) for k in claimed if claimed[k] != tally.get(k, 0)}
    assert not bad, ("README inventory disagrees with the tree (claimed, measured): %s"
                     % ", ".join("%s %d vs %d" % (k, v[0], v[1]) for k, v in sorted(bad.items())))

    # The prose says 「代码块与行内代码里的写法示例不计入」. Prove that clause is load-bearing rather
    # than decorative: counting the same tree WITHOUT those exclusions must come out higher.
    assert quoted["hint"] > 0, ("the inline/fence exclusion dropped 0 hint mentions — either the "
                               "book stopped quoting hint syntax (then README's clause is stale) or "
                               "the exclusion broke and is silently swallowing reader-visible cards")
    print("inventory: %s | excluded quoted-in-markup mentions: hint=%d stepper=%d tabs=%d tab=%d "
          "step=%d | pages carrying a widget=%d"
          % (" ".join("%s=%d" % (k, tally.get(k, 0)) for k in INVENTORY_KEYS),
             quoted["hint"], quoted["stepper"], quoted["tabs"], quoted["tab"], quoted["step"],
             per_page))
    # Floors: these are counts prose moves (a new page adds a card), so only the direction is pinned.
    assert tally.get("hint", 0) >= 250 and tally.get("stepper", 0) >= 50, \
        "widget inventory fell below the documented floor — pages lost their widgets"
    return 0


def quoted_mentions(text):
    """Openings that exist in raw text but are markup examples, not reader-visible widgets."""
    raw = {}
    for m in TOKEN.finditer(text):
        if m.group(1) in PAIRS:
            raw[m.group(1)] = raw.get(m.group(1), 0) + 1
    return raw


def inventory_controls():
    """The counting leg's own planted cases — each exclusion and each name-confusion that could
    silently inflate the homepage number has to be demonstrated on a synthetic page."""
    assert count_openings('{% hint style="info" %}\nx\n{% endhint %}\n') == {"hint": 1}
    assert count_openings('```text\n{% hint style="info" %}\n{% endhint %}\n```\n') == {}, \
        "control: a hint inside a fence counted as a reader-visible card"
    assert count_openings('写成 `{% hint style="info" %}` 一行即可\n') == {}, \
        "control: an inline-code hint mention counted"
    assert count_openings('{% endhint %}\n{% endtabs %}\n{% endtab %}\n{% endstepper %}\n'
                          '{% endstep %}\n') == {}, "control: a closer counted as an opening"
    assert count_openings('{% tabs %}\n{% tab title="a" %}\nx{% endtab %}\n{% tab title="b" %}'
                          '\ny\n{% endtab %}\n{% endtabs %}\n') == {"tabs": 1, "tab": 2}, \
        "control: group/tab counting drifted"
    assert count_openings('{%- hint style="info" -%}\nx\n{%- endhint -%}\n') == {"hint": 1}, \
        "control: whitespace-control tag not counted"
    assert count_openings('{% hint title="±1% 容差" style="info" %}\nx\n{% endhint %}\n') == {"hint": 1}, \
        "control: a bare % in an attribute truncated the token"
    nested = count_openings('{% stepper %}\n{% step title="a" %}body{% endstep %}\n'
                            '{% step title="b" %}body\n{% endstep %}\n{% endstepper %}\n')
    assert nested == {"stepper": 1, "step": 2}, ("control: nesting changed counts: %s" % nested)
    return 8


def main():
    problems, pages = 0, 0
    tally, quoted, pages_with = {}, {}, 0
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            pages += 1
            text = io.open(p, encoding="utf-8").read()
            counts = count_openings(text)
            if counts:
                pages_with += 1
            for k, v in counts.items():
                tally[k] = tally.get(k, 0) + v
            for k, v in quoted_mentions(text).items():
                quoted[k] = quoted.get(k, 0) + v - counts.get(k, 0)
            errs = scan(text)
            if errs:
                problems += len(errs)
                print("%s (%d problem(s))" % (os.path.relpath(p, ROOT).replace("\\", "/"), len(errs)))
                for e in errs:
                    print("   ", e)

    n_ctrl = inventory_controls()
    inventory_checks(tally, pages_with, quoted)
    ph = scan('A\n{% hint style="info" %}\nB\n{% endhint %}\nC\n{% tab title="x" %}\nD\n{% endtabs %}\n')
    assert len(ph) >= 2, "PHANTOM CONTROL FAILED (judge is blind): %s" % ph
    pct = scan('{% tabs %}\n{% tab title="长度惩罚 b：0.75、容差 ±1% 容差" %}\nbody\n{% endtab %}\n{% endtabs %}\n')
    assert not pct, "'%' IN TITLE REGRESSION FAILED: %s" % pct
    inl = scan('写成 `{% hint style="info" %}` 一行即可\n')
    assert not inl, "INLINE-CODE IGNORE REGRESSION FAILED: %s" % inl
    print("controls ok (phantom=%d, pct-title=0, inline-code=0, inventory=%d)" % (len(ph), n_ctrl))
    print("pages=%d problems=%d" % (pages, problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
