"""体裁字数门槛轴：每一页标了 `status: published` 的读者页，正文中文字数必须 ≥ 所在体裁的下界。

判据不是这里定的。体裁→下界那张表读自读者能看到的那一页
`docs/14-templates/style-guide.md` 第八节：判据按行取「体裁名（`type: 键`）| 数字或不限」，
规范改了数字判据跟着改；那一节被删掉、行数读不满、或**没有一个类型键绑上**，判据报
「尺子断了」（GUIDE-BLIND，退出码 2），不许读成「全书合格」。

为什么要有这条轴（第 86 轮，先量后建）：第八节写的是硬要求——「不达标不得标 published」，
但它落在 196 个读者页上，之前一个字都没有机器管着。首趟量到两件事：
1. 那张表五行里 **0 行**写了 frontmatter 用的 `type:` 键，也就是说这条硬要求当时根本无法判定；
2. 全站实际在用四个 `type`（knowledge/resource/index/lab），而表里连 `lab` 这个体裁都没有。
两者都在本轮的正文改动里修（表每行钉上类型键 + 补实验型一行），修完这条轴才真的能当判据用。

口径（钉死，可复算）：
- 字数 = 正文里 CJK 表意文字（`一-鿿`）的个数，与第八节那句「正文中文字数」同口径；
- 围栏块整块剔除：读者看到的 JSON/文本块是数据契约不是论证，把它算进字数等于让作者拿贴图凑字数。
  这个口径今天不是躲缺陷的出口，但它是**一只有待命后果的闸门**，所以实测过：按本轮真正执行的
  那三档地板（knowledge 600 / resource 150 / lab 1200），196 页里判决随「围栏算不算」翻转的是 **0 页**；
  而把规范里那档执行不到的原理型 1200 拿来硬判，会有 **12 页**翻（正文 1138～1195、含围栏 1204～1307）。
  也就是说：口径一旦变成承重的那根梁（子体裁键落地那天），这 12 页要重新量，不能沿用今天的读数。
- 只有 `status: published` 受这条管；`draft`/`reviewing` 是规范自己给的合规出口。
- 同一 `type` 绑多个体裁时取下界里最宽（最低）的那档当硬地板：`knowledge` 同时是原理型 1200 /
  概念型 600 / 实战型 900，frontmatter 里没有字段能区分这三型，所以判 600，并把「原理型那一档
  现在不可判」的页数如实打出来（BLIND=…）。要不要给知识页加一个子体裁键，是产品决定，移交操作者。

用法：
  python tools/checks/check_genre_floors.py            # 全站，离线
  python tools/checks/check_genre_floors.py --selftest # 10 条控制项（8 条种缺陷 + 2 条锚点）
"""
import argparse
import io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(REPO, "docs")
GUIDE_REL = os.path.join("14-templates", "style-guide.md")
CJK = re.compile(r"[一-鿿]")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
NAV_FILES = ("SUMMARY.md", "MANIFEST.md")
# 尺子自己的地板：读不满这些就不许报「0 问题」
FLOOR_ROWS = 4
FLOOR_BOUND = 3
FLOOR_PAGES = 180


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def guide_rows(text=None):
    """第八节那张表的行：[(体裁名, type 键或 None, 下界整数或 None 表示不限)]。读不到返回 []。"""
    text = read(os.path.join(DOCS, GUIDE_REL)) if text is None else text
    m = re.search(r"^## 八、.*?(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return []
    rows = []
    for line in m.group(0).split("\n"):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 2 or c[0] in ("体裁", "") or set(c[0]) <= set("-: "):
            continue
        if c[1] not in ("不限",) and not c[1].isdigit():
            continue
        key = re.search(r"`type:\s*(\w+)`", line)
        rows.append((c[0], key.group(1) if key else None,
                     None if c[1] == "不限" else int(c[1])))
    return rows


def split_front(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1) if m else ""), (text[m.end():] if m else text)


def prose_cjk(body):
    out, infence = [], False
    for line in body.split("\n"):
        if FENCE.match(line):
            infence = not infence
            continue
        if not infence:
            out.append(line)
    return len(CJK.findall("\n".join(out)))


def pages(docs=None):
    docs = DOCS if docs is None else docs
    rows = []
    for dirpath, dirs, filenames in os.walk(docs):
        dirs[:] = [d for d in dirs if d != ".gitbook"]
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, docs).replace("\\", "/")
            if rel in NAV_FILES:
                continue
            fm, body = split_front(read(path))
            ty = re.search(r"^type:\s*(\w+)", fm, re.M)
            st = re.search(r"^status:\s*(\w+)", fm, re.M)
            rows.append((rel, ty.group(1) if ty else None,
                         st.group(1) if st else None, prose_cjk(body), bool(fm)))
    return rows


def floors_by_key(rows):
    """type 键 → 硬地板（同键多体裁取最低的数字档）；只有「不限」的键记为 None（受管但免检）。"""
    out = {}
    for _genre, key, floor in rows:
        if not key:
            continue
        cur = out.get(key, "unset")
        if cur == "unset":
            out[key] = floor
        elif cur is None:
            out[key] = floor            # 「不限」遇到数字档：数字更严，取数字
        elif floor is not None:
            out[key] = min(cur, floor)  # 都是数字：取最低，判据不替规范发明更严的线
    return out


def grade(docs=None, min_pub=FLOOR_PAGES):
    """[(桶, 消息)], 统计。桶为空即全书合格；GUIDE-BLIND/SCAN-BLIND 由调用方按退出码 2 处理。"""
    docs = DOCS if docs is None else docs
    grows = guide_rows(read(os.path.join(docs, GUIDE_REL)))
    bound = [r for r in grows if r[1]]
    if len(grows) < FLOOR_ROWS or len(bound) < FLOOR_BOUND:
        return [("GUIDE-BLIND", "第八节那张表读到 %d 行、其中 %d 行钉了 `type:` 键"
                                "（地板 %d/%d）——尺子断了，不许读成全书合格"
                 % (len(grows), len(bound), FLOOR_ROWS, FLOOR_BOUND))], {}
    floors = floors_by_key(grows)
    bad, stats = [], {"pages": 0, "published": 0, "graded": 0, "blind": 0, "free": 0}
    hi = max([f for _g, k, f in grows if k == "knowledge" and f] or [0])
    for rel, ty, st, n, has_fm in pages(docs):
        stats["pages"] += 1
        if not has_fm:
            bad.append(("NOFRONTMATTER", "%s 没有 frontmatter，体裁无从判定" % rel))
            continue
        if st != "published":
            continue
        stats["published"] += 1
        if ty not in floors:
            bad.append(("UNBOUND-TYPE", "%s 用了 `type: %s`，但第八节那张表里没有任何一行钉住这个键"
                        % (rel, ty)))
            continue
        floor = floors[ty]
        if floor is None:
            stats["free"] += 1          # 规范自己写「不限」：受管，但这一轴不判字数
            continue
        stats["graded"] += 1
        if n < floor:
            bad.append(("BELOW", "%s 正文中文字数 %d < 该体裁下界 %d（`type: %s`，status 却是 published）"
                        % (rel, n, floor, ty)))
        elif ty == "knowledge" and n < hi:
            stats["blind"] += 1         # 原理型那一档判不到：如实报数，不当成合格
    if stats["published"] < min_pub:
        bad.append(("SCAN-BLIND", "这一趟只数到 %d 页 published（地板 %d）——扫描本身断了，"
                                  "不许读成「全书合格」" % (stats["published"], min_pub)))
    return bad, stats


def run():
    bad, s = grade()
    print("genre-floor leg: pages=%d published=%d graded=%d 免检(不限)=%d 不可判(同键高档)=%d | %s"
          % (s.get("pages", 0), s.get("published", 0), s.get("graded", 0),
             s.get("free", 0), s.get("blind", 0),
             "problems=%d" % len(bad)))
    for bucket, msg in sorted(bad):
        print("   %-14s %s" % (bucket, msg))
    if any(b in ("GUIDE-BLIND", "SCAN-BLIND") for b, _ in bad):
        return 2
    return 1 if bad else 0


def book(rows_md, pages_md):
    """在临时目录里搭一本只有几页的小书：{相对路径: 正文}，规范页用 rows_md。"""
    d = tempfile.mkdtemp(prefix="genre")
    os.makedirs(os.path.join(d, "14-templates"))
    guide = ("---\ntype: index\nstatus: published\n---\n"
             "## 八、篇幅与\"发布\"门槛\n\n| 体裁 | 正文中文字数下限 | 说明 |\n|---|---|---|\n"
             + rows_md + "\n\n## 九、写作检查清单\n")
    with io.open(os.path.join(d, "14-templates", "style-guide.md"), "w", encoding="utf-8") as f:
        f.write(guide)
    for rel, body in pages_md.items():
        p = os.path.join(d, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        fm, _, rest = body.partition("@@")
        with io.open(p, "w", encoding="utf-8") as f:
            f.write("---\n%s\n---\n%s" % (fm, rest))
    return d


def selftest():
    """10 条控制：8 条把尺子弄坏或把缺陷藏进去必须被抓，2 条锚定「合规范本必须绿」。"""
    ok = []

    PUB = "type: %s\nstatus: published@@"
    TINY = PUB % "knowledge" + "正文很短"
    GOOD = PUB % "knowledge" + "字" * 700
    RES = PUB % "resource" + "字" * 200

    def rows(with_lab=True, bind=True, floor=1200):
        b = lambda k: ("（`type: %s`）" % k) if bind else ""
        out = ("| 原理型%s | %d | 含公式与推导 |\n"
               "| 概念型%s | 600 | |\n"
               "| 实战型%s | 900 | 含数据契约与分步演示 |\n"
               "| 资源卡片%s | 150 | 但推荐理由必须具体 |\n"
               "| 索引/导航页%s | 不限 | |" % (b("knowledge"), floor, b("knowledge"),
                                              b("knowledge"), b("resource"), b("index")))
        return out + ("\n| 实验型%s | 1200 | 含动手步骤与真实运行记录 |" % b("lab") if with_lab else "")

    def buckets(d):
        return {b for b, _ in grade(d, 0)[0]}

    # A 种缺陷：一页 knowledge 只有 4 个字，却标 published
    d = book(rows(), {"01/x.md": TINY, "01/y.md": GOOD, "13/z.md": RES})
    ok.append(("A 薄页必须抓到", "BELOW" in buckets(d)))
    # B 种缺陷：用一个表里没钉住的 type
    d = book(rows(with_lab=False), {"01/x.md": PUB % "lab" + "字" * 2000})
    ok.append(("B 未绑定的 type 必须抓到", "UNBOUND-TYPE" in buckets(d)))
    # C 种缺陷：规范整节被删 → 尺子断了，而不是 0 问题
    d = book("# 没有第八节的规范\n正文\n", {"01/x.md": GOOD})
    ok.append(("C 规范被删必须报断尺", buckets(d) == {"GUIDE-BLIND"}))
    # D 种缺陷：表还在但每行都不写 `type:` 键（本轮之前的真实状态）
    d = book(rows(bind=False), {"01/x.md": TINY})
    ok.append(("D 表没绑类型键必须报断尺", buckets(d) == {"GUIDE-BLIND"}))
    # E 种缺陷：把 1200 字塞进围栏里冒充正文
    fence = PUB % "knowledge" + "\n```text\n%s\n```\n外面只有几个字\n" % ("\n字" * 1300)
    d = book(rows(), {"01/x.md": fence})
    ok.append(("E 贴一屏代码凑字数不算正文", "BELOW" in buckets(d)))
    # F 种缺陷：不标 published 就不受这条管（规范自己给的出口）
    d = book(rows(), {"01/x.md": "type: knowledge\nstatus: draft@@字"})
    ok.append(("F draft 页是合规出口，不判", buckets(d) == set()))
    # G 种缺陷：没有 frontmatter 的页不能悄悄滑过去
    d = book(rows(), {"01/x.md": "@@%s" % ("字" * 2000)})
    ok.append(("G 缺 frontmatter 必须抓到", "NOFRONTMATTER" in buckets(d)))
    # H 锚点：合规范本必须全绿，且「不限」那一档确实被记成免检而不是判过
    d = book(rows(), {"01/x.md": GOOD, "13/z.md": RES, "00/i.md": PUB % "index" + "三个字"})
    bad, s = grade(d, 0)
    ok.append(("H 合规范本必须 0 问题", bad == [] and s["free"] == 2 and s["graded"] == 2))
    # I 锚点：地板取同键最低档（knowledge 判 600 而不是 1200），别替规范发明更严的规则
    d = book(rows(), {"01/x.md": PUB % "knowledge" + "字" * 650})
    ok.append(("I 同键多体裁取最低下界", grade(d, 0)[0] == []))
    # J 种缺陷：扫描断掉（一页都没数到）必须报「尺子断了」，不许报全书合格
    d = book(rows(), {})
    ok.append(("J 空扫描必须报断尺", "SCAN-BLIND" in {b for b, _ in grade(d)[0]}))
    print("%d checks, %d not caught" % (len(ok), sum(1 for _, v in ok if not v)))
    for name, v in ok:
        print("   %-4s %s" % ("ok" if v else "MISS", name))
    return 0 if all(v for _, v in ok) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    return selftest() if args.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
