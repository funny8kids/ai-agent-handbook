"""GitBook block-tag pairing check over every page in docs/.

Tokens are matched exactly by name, so {% endstep %} and {% endstepper %} can never be
conflated. Reports unclosed openers, closers with no opener, and nesting-order violations.
Carries its own controls: a phantom that must fail, plus regressions for the two blind
spots this judge had when it was written (a '%' inside an attribute, and inline-code
mentions of tag syntax).
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


def main():
    problems, pages = 0, 0
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            pages += 1
            errs = scan(io.open(p, encoding="utf-8").read())
            if errs:
                problems += len(errs)
                print("%s (%d problem(s))" % (os.path.relpath(p, ROOT).replace("\\", "/"), len(errs)))
                for e in errs:
                    print("   ", e)

    ph = scan('A\n{% hint style="info" %}\nB\n{% endhint %}\nC\n{% tab title="x" %}\nD\n{% endtabs %}\n')
    assert len(ph) >= 2, "PHANTOM CONTROL FAILED (judge is blind): %s" % ph
    pct = scan('{% tabs %}\n{% tab title="长度惩罚 b：0.75、容差 ±1% 容差" %}\nbody\n{% endtab %}\n{% endtabs %}\n')
    assert not pct, "'%' IN TITLE REGRESSION FAILED: %s" % pct
    inl = scan('写成 `{% hint style="info" %}` 一行即可\n')
    assert not inl, "INLINE-CODE IGNORE REGRESSION FAILED: %s" % inl
    print("controls ok (phantom=%d, pct-title=0, inline-code=0)" % len(ph))
    print("pages=%d problems=%d" % (pages, problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
