"""章色配色轴：每张 Mermaid 图的第一行必须是所在章节的 `%%{init}%%`，取章色，按固定公式掺白。

判据不是这里定的。色表（21 章 → 主色）、掺白公式（`primaryColor` 90% / `secondaryColor` 78% /
`lineColor` 45%）和 `primaryTextColor` 的字面值，全部从读者能看到的那一页
`docs/14-templates/style-guide.md`「Mermaid 章色配色（硬性要求）」现解析出来——规范改了，判据跟着改；
规范那一节被删掉或改得读不出表，判据报「尺子断了」而不是「0 问题」。
公式的取整口径先拿规范自己给的那行 02 章示例对平（示例必须被公式逐字符复现），再拿去量全书。

比字符串更硬的一条是**读者能不能看见**：标签色与它所在底板的 WCAG 对比度必须 ≥ 4.5:1（本书自绘图
一直用的就是 `check_svg_phase_legibility` 那两档：小字 4.5、大字 3.0；Mermaid 默认节点标签 16px，
属小字档）。第 85 轮首趟就是被这条抓出来的：一页把三个文字变量都设成了本章最浅的那级掺白，
量到 4 组 1.00–1.19:1 的标签。

用法：
  python tools/checks/check_mermaid_palette.py                    # 作者侧，离线
  python tools/checks/check_mermaid_palette.py --selftest         # 13 条控制项（8 条种缺陷 + 2 条锚点 + 3 条线上腿的尺子）
  python tools/checks/check_mermaid_palette.py --live 8           # 线上抽样：发出的颜色就是写的颜色

线上腿的口径（第 85 轮首跑就是它自己判瞎）：读者页面并不原样打印那一行，而是把它嵌在编辑器
文档的 JSON 里，引号全部带反斜杠转义。所以比较前先剥掉转义反斜杠；命中与否之外还钉两条反向控制
（改过一处章色的幽灵指令必须不命中、别页的指令行必须不命中），否则「全命中」与「什么都匹配」读起来一样。
抽样里一条都没命中时报 LIVE-BLIND 退出 2（要么没同步要么尺子坏了），不读成内容通过，也不读成缺陷。
"""
import argparse
import io
import json
import os
import re
import sys

DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs"))
GUIDE_REL = "14-templates/style-guide.md"
BAR = 4.5                     # WCAG 1.4.3 AA, small text — the house's own bar for figures
PAIRS = [("primaryTextColor", "primaryColor"), ("primaryTextColor", "tertiaryColor"),
         ("actorTextColor", "actorBkg"), ("noteTextColor", "noteBkgColor")]
# 反空转地板：尺子读不出这些量就是尺子坏了，不是书变好了
FLOOR_BLOCKS = 200
FLOOR_CHAPTERS = 20
FLOOR_PAIRS = 600


def read(path):
    return io.open(path, encoding="utf-8").read()


def mermaid_blocks(text):
    """```mermaid 围栏里的源码，用本书同一套围栏状态机取（行内代码与 ```text 里的写法示例不算图）。"""
    out, tok, cur = [], None, None
    for line in text.split("\n"):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})(\w*)", line)
        if m:
            t = m.group(1)[0] * 3
            if tok is None:
                tok, cur = t, ([] if m.group(2) == "mermaid" else None)
            else:
                if t == tok:
                    if cur is not None:
                        out.append("\n".join(cur))
                    tok, cur = None, None
                elif cur is not None:
                    cur.append(line)
            continue
        if cur is not None:
            cur.append(line)
    return out


def guide_rules():
    """(色表, 掺白公式, primaryTextColor 字面值, 规范自己那行示例) — 全部读自读者可见的那一页。"""
    text = read(os.path.join(DOCS, *GUIDE_REL.split("/")))
    cells = re.findall(r"\s*(\d\d)\s+[^|]*?\|\s*`(#[0-9A-Fa-f]{6})`\s*(?=\||$)", text)
    palette = {int(n): c.upper() for n, c in cells}
    form = {k: int(v) / 100.0 for k, v in re.findall(r"`(\w+)`\s*=\s*(?:主色)?掺白\s*(\d+)%", text)}
    ink = re.search(r"`primaryTextColor`\s*=\s*`(#[0-9A-Fa-f]{6})`", text)
    example = re.search(r"^%%\{init:\s*(\{.*\})\}%%$", text, re.M)
    return palette, form, (ink.group(1).upper() if ink else None), (example.group(1) if example else None)


def mix(color, white):
    """掺白 `white` 成：结果 = 白*white + 主色*(1-white)，四舍五入取半进位（与全书 217 块一致）。"""
    ch = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(v * (1 - white) + 255 * white + 0.5) for v in ch)


def lum(color):
    ch = [int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    ch = [(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4) for v in ch]
    return ch[0] * 0.2126 + ch[1] * 0.7152 + ch[2] * 0.0722


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def chapter_of(rel):
    return int(rel[:2]) if rel[:2].isdigit() else None


def grade(src, palette, form, ink, page="?"):
    """一块图的判决列表。找不到章色不判（NOCHAPTER 由调用方按页处理）。"""
    first = src.split("\n", 1)[0].strip() if src else ""
    if not first.startswith("%%{init:"):
        return [("MISS", "%s 的 ```mermaid 块第一行不是章色指令，而是 %r" % (page, first[:36]))]
    m = re.match(r"^%%\{init:\s*(\{.*\})\}%%$", first)
    if not m:
        return [("UNPARSE", "%s 的章色指令行读不出 JSON（行尾必须收在 }%%%% 上）: %r"
                 % (page, first[:60]))]
    try:
        j = json.loads(m.group(1))
    except ValueError as e:
        return [("UNPARSE", "%s 的章色指令不是合法 JSON: %s" % (page, str(e)[:70]))]
    chap = chapter_of(page)
    base = palette.get(chap)
    if base is None:
        return [("NOCHAPTER", "%s 所在章 %s 不在规范色表里（规范那页改了表要先补这里）" % (page, chap))]
    tv = j.get("themeVariables") or {}
    out = []
    if j.get("theme") != "base":
        out.append(("THEME", "%s theme=%r，规范要求 theme\":\"base\"（章色靠手工掺白，不用内置主题）"
                    % (page, j.get("theme"))))
    if (tv.get("primaryBorderColor") or "").upper() != base:
        out.append(("WRONGBASE", "%s primaryBorderColor=%s，规范色表里 %02d 章主色是 %s"
                    % (page, tv.get("primaryBorderColor"), chap, base)))
    for key, white in sorted(form.items()):
        got = (tv.get(key) or "").upper()
        want = mix(base, white)
        if got != want:
            out.append(("FORMULA", "%s %s=%s，按规范掺白 %d%% 应为 %s"
                        % (page, key, got, int(white * 100), want)))
    if ink and (tv.get("primaryTextColor") or "").upper() != ink:
        out.append(("TEXTCOLOR", "%s primaryTextColor=%s，规范钉的是 %s"
                    % (page, tv.get("primaryTextColor"), ink)))
    for t, b in PAIRS:
        tc, bc = (tv.get(t) or "").upper(), (tv.get(b) or "").upper()
        if len(tc) == 7 and len(bc) == 7:
            q = ratio(tc, bc)
            if q < BAR:
                out.append(("CONTRAST", "%s %s 压在 %s 上只有 %.2f:1（小字档地板 %.1f:1，读者读不到标签）"
                            % (page, t, bc, q, BAR)))
    return out


def pairs_graded(src):
    m = re.match(r"^%%\{init:\s*(\{.*\})\}%%$", (src or "").split("\n", 1)[0].strip())
    if not m:
        return 0
    try:
        tv = (json.loads(m.group(1)).get("themeVariables") or {})
    except ValueError:
        return 0
    return sum(1 for t, b in PAIRS
               if len((tv.get(t) or "").upper()) == 7 and len((tv.get(b) or "").upper()) == 7)


def blocks():
    rows = []
    for dirpath, dirs, filenames in os.walk(DOCS):
        dirs[:] = [d for d in dirs if d != ".gitbook"]
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            if rel in ("SUMMARY.md", "MANIFEST.md"):
                continue                      # 导航与资产清单不是读者页
            for i, src in enumerate(mermaid_blocks(read(path)), 1):
                rows.append((rel, i, src))
    return rows


def run():
    palette, form, ink, example = guide_rules()
    if len(palette) < FLOOR_CHAPTERS or not form or not ink or not example:
        print("GUIDE-RULES 规范那一页读不出色表/公式/字面值（读到 %d 章、公式 %d 条）——"
              "这是尺子断了，不是全书合格" % (len(palette), len(form)))
        return 2
    ex_tv = (json.loads(example).get("themeVariables") or {})
    bad_anchor = [(k, ex_tv.get(k), mix(palette[2], w))
                  for k, w in sorted(form.items()) if ex_tv.get(k) != mix(palette[2], w)]
    if bad_anchor:
        print("SELF-ANCHOR 公式复现不了规范自己给的 02 章示例：%s" % bad_anchor)
        return 2
    rows, findings, npairs = blocks(), [], 0
    for rel, i, src in rows:
        npairs += pairs_graded(src)
        for bucket, msg in grade(src, palette, form, ink, rel):
            findings.append((bucket, msg))
    tally = {}
    for b, _m in findings:
        tally[b] = tally.get(b, 0) + 1
    below = [b for b, n in (("blocks", len(rows)), ("pairs", npairs))
             if n < {"blocks": FLOOR_BLOCKS, "pairs": FLOOR_PAIRS}[b]]
    print("mermaid palette: blocks=%d chapters=%d formula=%s ink=%s contrast-pairs=%d | %s"
          % (len(rows), len(palette),
             ",".join("%s%d%%" % (k, int(v * 100)) for k, v in sorted(form.items())),
             ink, npairs,
             " ".join("%s=%d" % (b, tally.get(b, 0)) for b in
                      ("MISS", "UNPARSE", "THEME", "NOCHAPTER", "WRONGBASE",
                       "FORMULA", "TEXTCOLOR", "CONTRAST"))))
    for _b, msg in findings[:20]:
        print("   " + msg)
    if len(findings) > 20:
        print("   ... 另有 %d 条" % (len(findings) - 20))
    if below:
        print("FLOOR 读数低于地板（%s）——分母掉了说明尺子坏了，不判绿" % ",".join(below))
        return 2
    return 1 if findings else 0


LIVE_PAGE = "06-memory-rag/long-context-degradation.md"
PHANTOM = "#0E0E0E"  # 全书没用了这个色；指令行里拿它替换一处就该找不到


def flatten(html):
    """读者页面把作者写的指令行嵌在编辑器文档 JSON 里，引号全部带反斜杠转义
    （\\"theme\\"），所以「原样子串」在这张页面上永远不可能命中——先剥掉转义反斜杠
    再比。判决的对象不变：这一整行（含全部键名与九个色值）必须真的到了读者手里。"""
    return html.replace("\\", "")


def live(n):
    """线上腿：读者拿到的那一页里，图的颜色指令就是文件里写的那一行（平台不改写、不丢失）。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import live_aria_manifest as LA
    palette, form, ink, _ex = guide_rules()
    idx = LA.url_index()
    rows = blocks()
    pages = []
    for rel, _i, _s in rows:
        if rel not in pages:
            pages.append(rel)
    want = [LIVE_PAGE] + [p for p in pages if p != LIVE_PAGE][:n - 1]
    bad, blind, checked, hit = [], [], 0, 0
    for rel in want:
        h1 = re.search(r"^# (.+)$", read(os.path.join(DOCS, *rel.split("/"))), re.M)
        url = idx.get(LA.norm(h1.group(1).strip())) if h1 else None
        if not url:
            bad.append("NOT-LISTED %s" % rel)
            continue
        served = LA.fetch(url)
        if not served or h1.group(1).strip() not in served:
            # 连本页标题都没有：这一页什么都没证明，不许读成「指令丢了」
            blind.append("FETCH/STALE %s" % rel)
            continue
        flat = flatten(served)
        for r2, i, src in rows:
            if r2 != rel:
                continue
            line = src.split("\n", 1)[0].strip()
            checked += 1
            if line in flat:
                hit += 1
                ghost = line.replace(re.search(r"#\w\w\w\w\w\w", line).group(0), PHANTOM)
                if ghost in flat:
                    bad.append("PHANTOM-HIT %s#%d 改色后的幽灵指令也命中，等式判不出东西" % (rel, i))
            else:
                bad.append("DIRECTIVE-AWOL %s#%d 线上这一页里找不到作者写的章色指令行" % (rel, i))
            for bucket, msg in grade(src, palette, form, ink, rel):
                if bucket == "CONTRAST":
                    tv = json.loads(re.match(r"^%%\{init:\s*(\{.*\})\}%%$", line).group(1)
                                    )["themeVariables"]
                    if (tv.get("primaryTextColor") or "").upper() in flat:
                        bad.append("READER-INVISIBLE %s#%d 低对比的标签色确实发到了读者页面上"
                                   % (rel, i))
    print("live palette leg: pages=%d directives-checked=%d hit=%d fetch-blind=%d problems=%d"
          % (len(want), checked, hit, len(blind), len(bad)))
    for x in (blind + bad)[:10]:
        print("   " + x)
    if checked and not hit:
        print("   LIVE-BLIND 一条指令都没命中：要么站点没同步，要么这条腿找错了字符串——"
              "先跑 check_live_sync 定同步，再重读这条腿，不许读成内容通过")
        return 2
    return 1 if bad or blind or checked < n else 0


def selftest():
    palette, form, ink, example = guide_rules()
    base6 = palette[6]
    fails = []
    planted = []

    def check(name, cond, detail=""):
        planted.append(name)
        if cond:
            return
        fails.append("%s %s" % (name, detail))

    def body(tv, extra="flowchart TD\n A-->B"):
        # 拼接而不是 % 格式化：串里的 `%%` 会被 % 格式化吃掉一个百分号，种出来的指令行第一行就少一个 `%`
        return "%%{init: " + json.dumps({"theme": "base", "themeVariables": tv},
                                        separators=(",", ":")) + "}%%\n" + extra

    def directive_of(src):
        return json.loads(re.match(r"^%%\{init:\s*(\{.*\})\}%%$",
                                   src.split("\n", 1)[0]).group(1))["themeVariables"]

    real = [s for r, _i, s in blocks() if r == LIVE_PAGE]
    fixed = grade(real[0], palette, form, ink, LIVE_PAGE) if real else [("MISS", "样本页没有图")]
    check("A 修好的真块必须判绿", fixed == [], "got=%s" % fixed[:2])
    check("B 缺指令行要报 MISS",
          grade("flowchart TD\n A-->B", palette, form, ink, "06-x/y.md")[0][0] == "MISS")
    tv = dict(directive_of(real[0]))
    tv["primaryBorderColor"] = palette[7]
    check("C 拿别章主色要报 WRONGBASE",
          any(b == "WRONGBASE" for b, _m in grade(body(tv), palette, form, ink, "06-x/y.md")))
    tv = dict(directive_of(real[0]))
    tv["lineColor"] = mix(base6, 0.5)
    check("D 掺白比例差一档要报 FORMULA",
          any(b == "FORMULA" for b, _m in grade(body(tv), palette, form, ink, "06-x/y.md")))
    # E/F 两条分开：可读但不是规范字面值的墨色只该动 TEXTCOLOR，不该动 CONTRAST
    tv = dict(directive_of(real[0]))
    tv["primaryTextColor"] = "#374151"
    got3 = [b for b, _m in grade(body(tv), palette, form, ink, "06-x/y.md")]
    check("E 可读但非规范的墨色只报 TEXTCOLOR", got3 == ["TEXTCOLOR"], "got=%s" % got3)
    # G/H 第 85 轮那个真实缺陷：三个文字变量都设成本章最浅掺白
    tv = dict(directive_of(real[0]))
    for k in ("primaryTextColor", "actorTextColor", "noteTextColor"):
        tv[k] = mix(base6, 0.96)
    got5 = [b for b, _m in grade(body(tv), palette, form, ink, "06-x/y.md")]
    check("H 白底白字必须同时报 TEXTCOLOR 与 CONTRAST",
          "CONTRAST" in got5 and "TEXTCOLOR" in got5, "got=%s" % got5)
    check("I 不在色表里的章要报 NOCHAPTER",
          grade(body(directive_of(real[0])), palette, form, ink, "20-newpage/x.md")[0][0]
          == "NOCHAPTER")
    check("J 读不出的指令行要报 UNPARSE",
          grade('%%{init: {"theme":"base",}%%\nflowchart TD', palette, form, ink,
                "06-x/y.md")[0][0] == "UNPARSE")
    dark = json.dumps({"theme": "dark", "themeVariables": directive_of(real[0])},
                      separators=(",", ":"))
    check("F theme 不是 base 要报 THEME",
          any(b == "THEME" for b, _m in
              grade("%%{init: " + dark + "}%%\nflowchart TD", palette, form, ink, "06-x/y.md")))
    check("K 公式必须复现规范自己给的示例行",
          all((json.loads(example).get("themeVariables") or {}).get(k) == mix(palette[2], w)
              for k, w in form.items()))
    # L/M/N 是线上腿的尺子控制：读者页面把指令行嵌在编辑器文档 JSON 里（引号带反斜杠），
    # 第 85 轮那版腿拿原样子串去比，于是把 6 页全报成 DIRECTIVE-AWOL——包括本轮没碰过的页。
    line0 = real[0].split("\n", 1)[0].strip()
    escaped_blob = '{"nodes":[{"text":"%s"}]' % line0.replace('"', '\\"')
    check("L 转义过的读者页面必须命中（旧尺子在这里判瞎）",
          line0 in flatten(escaped_blob) and line0 not in escaped_blob)
    ghost = line0.replace(re.search(r"#\w\w\w\w\w\w", line0).group(0), PHANTOM)
    check("M 改过一处章色的幽灵指令不得命中", ghost not in flatten(escaped_blob))
    other = [s.split("\n", 1)[0].strip() for r, _i, s in blocks() if r != LIVE_PAGE]
    check("N 别页的指令行不得在本页命中",
          all(o not in flatten(escaped_blob) for o in other if o != line0))
    print("mermaid palette controls: %d checks, %d not caught"
          % (len(planted), len(fails)))
    for f in fails:
        print("   " + f)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--live", type=int, default=0, metavar="N",
                    help="抽样 N 页读者页面，核对发出的章色指令行")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.live:
        sys.exit(live(a.live))
    sys.exit(run())


if __name__ == "__main__":
    main()
