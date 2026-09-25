---
tags: [index, changelog]
type: index
status: published
updated: 2026-09-25
---

# 更新日志

本页记录手册的结构调整与重要内容更新。

## 2026-09-25（第 91 次）第 90 轮 §八 记下的「两个读数差得远」在本轮被量倒：不是平台发了两版，是判据把 UTF-8 解码后的字符数标成了 bytes——同一次抓取实测 337,508 字符 / 623,168 字节，比率 1.846；上一轮预告的那句断言也因此第一次真正可判（`--list-behind` 把 25 条落后单元的页与行号全部印出来）

本轮正文 **0 页知识页改动**：读者可见文字只动本页（新增本节，并在第 90 轮 §八 末尾回补一段）。**没有为过线删掉或加厚任何一页正文**——改动全部在尺子上：`tools/checks/check_live_sync.py`（单位口径 + 控制 U）与 `tools/checks/check_prose_survival.py`（新增 `--list-behind`）。

### 一、上一轮那句断言先要能被判定，才谈得上通过

第 90 轮把收尾账写成「`behind` 里不再出现本节之外的页」。本轮首跑读数：

```text
prose survival: pages=1 units=3966 plain=3671 heading=287 quote=8 widget=0 | all
lost sentences: MISS=0 REVISION-BEHIND=25 STALE-COPY=0 | pages-with-MISS=0 fetch-failures=0 not-listed=0
behind detail: listed=25 of REVISION-BEHIND=25 (full listing)
```

- 这条断言在旧判据下**无法判定**：`run()` 只把每页第 1 条落后单元连同它的豁免证据印出来（`behind[:1]`），其余 24 条只在总数里。所以本轮先补口径，不动判决：`--list-behind` 逐条印 `页:行 种类 单元`，并且自证覆盖面（`listed` 与 `REVISION-BEHIND` 不等时印 `LIST INCOMPLETE`，宁可不给读数也不给半份名单）。
- 判定结果：25 条全部在 `00-index/changelog.md` 这一页上，行号分布 172×1、178×5、192×2、194×4、201×2、203×3、205×1、207×7，而 §八 占第 156–208 行——**「本节之外的页」为 0 条**，断言按它自己的口径通过。
- 17 变 25 不是页面又旧了一截，而是账本自己长厚：`git blame -L 168,208` 把这一段归给第 90 轮的四次提交（`d514095` 10 行、`a5e3e62` 7 行、`0805a59` 20 行、`0115cc6` 4 行），后两次正是当初预告「补写本段自己新增的字也在同一本账里」的那两次收尾提交。

### 二、缺陷：腿线把字符数标成 bytes，于是「同一分钟的两个读数」成了假疑点

第 90 轮记下的「`.md` 直抓 621,559 B，而 md 腿读 336,586 B，两个读数差得远」，本轮在同一条 URL 上一次抓取、两种口径同时打印：

```text
independent md fetch: raw_bytes=623168 decoded_chars=337508
leg md   newest round=90  (337508 chars / 623168 bytes, 154 rounds)
leg html newest round=90  (25108708 chars / 25994905 bytes, 544 rounds)
```

`live_rounds()` 原本 `return [...], len(html)`，而 `html` 是 `.decode("utf-8")` 之后的字符串——打印时却写着 `%d bytes`。更新日志几乎全是汉字，UTF-8 下每个汉字 3 字节，所以字符数天然比字节数小（实测比率 1.846），一个标签错误就凭空造出「1.85 倍的差额」。这不是平台的谜，是判据对自己的读数撒了谎——和第 90 轮那组口径与实测量不一致的缺陷同族，只是这一次落在工具自己的输出上。修法是把两个都印出来（`chars / bytes`），而不是挑一个：字节数用来对上一轮的直抓读数，字符数用来解释为什么 HTML 腿那个 25 MB 量级的说法仍然成立（25,994,905 字节）。

### 三、控制 U：单位口径要能响，而且是离线控制

`check_live_sync.py --selftest` 新增控制 U，它不调网络，而是让 `live_rounds()` 去抓一个 `file:///` 的本地中文样本页，然后要求：轮次解析看到 `[7, 6]`、`chars < bytes`（相等就说明这两个数不是它们各自标签说的东西），并且本文件源码里必须留着 `(%d chars / %d bytes` 这个格式与 `chars, size` 这个实参次序。三条里任何一条被改动——换标签、换次序、把字节数悄悄塞回字符位——控制都会红着报出来，而不是安静地读绿。首跑：`controls: OK, every needle rule able to fire`，`exit=0`。

### 四、`.md` 水位与渲染水位是两条线，本轮把它们分开钉

- `.md`：抓取内容里同时带着三次提交各自的唯一针——`目检三帧`（`0805a59`）、`一条一条串行跑`（`0115cc6`）、`为什么全站只有那 1 条红`（`a5e3e62`）。三条针先用 `git log -S` 证明各自只属于那一次提交，再拿它们判水位，所以读数是：**HEAD 提交 11 分钟后，`.md` 端已经同步到最后一次提交**。
- 渲染页：散文腿的豁免证据同时说明，发布页在同一处仍印着 `a5e3e62` 之前的旧句——即 **HTML 渲染腿落后于 `.md`，且已跨四次提交**。这坐实了第 90 轮 §八 的机制判断（平台发了旧版），也把它从「一次观测」升成「两条水位可以分开测量、并且会分开」。
- 本轮没有为这条差异再建判据：`check_live_sync` 已经各报两条腿，而「25 MB 页按平台自己的节奏翻页」是运营事实不是缺陷。留下的账照旧：切点分辨率（`published_cut`）与 `MISS` 的边界。

### 五、离线电池（提交前，逐条；工作树即本轮将要提交的内容）

| 判据 | 读数 |
| --- | --- |
| `check_structure.py` | `pages scanned=198 problems=0`；围栏 `mermaid=217 text=87 json=80 markdown=11 yaml=10 (no tag)=9`；`executable-tagged=0 json contracts parsed=80 unclosed=0` |
| `check_widget_pairing.py` | `pages=198 problems=0`；`inventory: hint=257 stepper=54 step=279 tabs=52 tab=195` |
| `check_quote_fidelity.py` | `attributed quotes=25 findings=0 verified=23`（`PROSE 14 / FIGURE 1 / RETRACTED-OK 8 / NEGATED 1 / SELF-EVIDENCED 1`） |
| `check_changelog_headings.py` | `HEAD=82 tree=83 lost=0`——多出的 1 条就是本节标题，`lost=0` 说明没有第 90 轮的标题被吃掉 |
| `check_emphasis_flanking.py` | `pages=0 leaked_strong_markers=0 (body=0 outline=0)`；`outline scope: headings=2846 carrying_inline_code=106 whose_flattening_is_markdown_significant=71` |
| `check_char_sanity.py` | `pages=198 prose CJK chars=422629 traditional-form findings=0` |
| `check_katex_formulas.py` | `pages=108 formulas=927 failures=0 version=0.18.7` |
| `check_genre_floors.py` | `pages=196 published=196 graded=159 免检(不限)=37 不可判(同键高档)=40 problems=0` |
| `check_mermaid_palette.py` | `blocks=217 chapters=21 contrast-pairs=868`，八个桶全 0 |
| `check_readme_stats.py` | `banner chapters=19 measured=19`、`banner pages=196 measured=196`，逐条 ok |
| `check_link_graph.py` | `distinct=717 ok=702 blocked=14 net=1 unchecked=0 FAILED: 0` |
| `check_chapter_extras.py` | `chapters=18 goals=18 quizzes=17 quiz_exempt=1 questions=51 with_source=51 findings=0` |
| `check_source_pointers.py` | `pages=191 pointer_lines=3 findings=0`；`live mutation ok (0 -> 1 -> 0 findings on 6 shipped pages)` |
| `check_updated_dates.py` | `reader pages=198 checked=196 exempt=2 problems=0 pending-commit=0 unreadable=0` |
| `check_prose_duplicates.py` | `pages=191 prose_units=7427 formula_units=274 dup=0 near-band=3` |
| 两套控制 | `controls: OK, every bucket able to fire`（散文腿）／`controls: OK, every needle rule able to fire`（同步腿，含本轮新增的控制 U） |

16 条全部 `exit=0`。两点口径值得写下来，免得下一轮误读：

- **强调轴的标题计数会跟着本节长高**：`headings` 从第 90 轮的 2839 变成 2846（本节 7 条标题），`carrying_inline_code` 从 104 变成 106（新标题里有 2 条带行内代码）。而 `whose_flattening_is_markdown_significant` 保持 **71 不变**——这正是第 90 轮那条读者侧缺陷的口径：新写的标题里没有任何一条在展平后会露出 markdown 意义字符。也就是说这两个上涨的分母是「本节自己长出来的字」，不是「缺陷变多」，判据红绿看的是第三个数。
- **散文重复轴本轮不动它就不该动**：`prose_units=7427` 与第 90 轮收尾读数一模一样，因为该轴把 `00-index/` 排除在语料之外（更新日志按设计要引用别的页的句子）。所以本轮没有像第 90 轮那样出现「写文档把自己的分母挪了」——这条等号只在改动落在被排除的页上时成立，不能推广。

真实渲染目检（本地复制稿，768px 读者列宽）：把本节整段单独渲染成 HTML 后用 Edge headless 截图，`rendered html: 6 h3, 2 pre, 4155 chars`，出图 304,125 字节。图里两条 `text` 围栏各自成块、行内代码带底、粗体成粗体，**没有出现任何裸星号**。（这一帧拍在写 §五 之前，所以表格里有没有横向溢出当时还没被看过——§六 收尾那一帧补判。）

### 六、收尾（提交并推送、线上同步之后）

第 1 次提交 `61f4e95` 落地后，三条线上尾腿按串行各跑一次（不并发，避免自己造 FETCH 红）：

```text
HEAD committed 2026-09-25, 21 min ago
local newest round=91
  leg md   newest round=91  (344841 chars / 634527 bytes, 155 rounds)
  leg html newest round=90  (25108708 chars / 25994905 bytes, 544 rounds)  missing 91
  witness: HEAD added no reader-page text outside the changelog — the .md leg is the witness
  NOTE the published changelog PAGE is at round 90: readers opening it are missing 91
```

- **`--list-behind` 的判决**：`behind detail: listed=0 of REVISION-BEHIND=0 (full listing)`，同一跑另有 `MISS=0`、`STALE-COPY=72`、`units=4015 plain=3712 heading=295 quote=8`。第 90 轮 §八 那 17 条（长成 25 条的那批）**归零**，所以 §一 那句「本节之外的页不落进落后桶」不只是本轮可判，而且判过了。
- **72 条 `STALE-COPY` 不是缺陷**：同跑印出的水位线是 `published copy proves nothing below line 283`，也就是渲染页目前只翻到第 89 轮的标题（与 html 腿的 90 一致，差的那一节正是本轮与上一轮）。这些单元高于水位线＝未发布的修订，按第 89 轮的口径大声 NOTE 而不进门闩。
- **强调轴线上腿**：`pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0`，`whose_flattening_is_markdown_significant=71` 不变。

`check_live_sync --watch` 收尾复跑时（HEAD 后 13 分钟）md 腿已经到 91，而 html 腿**没有返回轮次**，印的是 `live changelog (html) unreadable (ValueError) — no verdict, this is not a site failure` 加 `exit=2`——这就是新装的短读门闩在活体上开火。它拦下的是哪种读法，当时看不出来，因为长度是在门闩之后才印的；收尾时把原因一起印出来（`(ValueError: short read (...))`）。

同一条 html 腿在更早一次 `--watch` 的两轮轮询里被**放行**过两次，而两次长度不同：`25108708 chars / 25994905 bytes, 544 rounds` 与 `22643743 chars / 23351607 bytes, 362 rounds`，响应头里都没有 `Content-Length`。两条都干净闭合、都带着最后一行作者写的中文，所以按本轮的口径它们是「整份到达」，只是 CDN 给的副本本身有大小差；被拦住的那一次则无法这样归档。这条区别值得留在页面上：门闩判的是**尾部有没有到齐**，不是字节数等不等于上一次——后者会把上面这种正常波动读成站点故障。

门闩本身（`short_read()` / `tail_needle()`）在 `live_rounds()` 里判两条：HTML 腿要求文档以 `</html>` 结尾，两条腿都要求**本地更新日志最后一行的中文串**出现在抓取结果里。针的实测：`tail_needle()='配置，内容根目录设为'`，在本地 312,097 字符里首次出现在第 312,078 字符（**99.99 %**，全文唯一 1 次）；在线渲染页里出现 3 次（正文 1 次 + 载荷副本 2 次）。拿日期 `2026-09-10` 当针的话，全文有 5 处，且它是最后 5 节共用的日期，所以针落在最后一行而不是最后的标题。

控制 S 是功能控制而不是文本比对：把完整的本地 `.md` 喂给真的 `live_rounds()` 必须不抛，把同一份文档砍掉最后一行必须抛 `ValueError`；再把 `short_read()` 单条判据的三种短读各自验一次（文档中途断掉 / 干净闭合但少最老一节 / `.md` 腿没有 `</html>` 可看）。把门闩改瞎（`short_read` 恒返 `None`）后 `--selftest` 印出 **4 条 control S 红**，恢复后 0 条——即这四条断言都真的能开门。

比率不是常数，这一轮量到两个：`.md` 腿 `634527/344841 = 1.840`（正文以中文为主），渲染页 `25994905/25108708 = 1.035`（一半以上是 ASCII 脚本载荷）。所以 §二 的 1.846 只属于 `.md` 这类文档，任何拿比率当校验的写法都必须先声明是哪条腿。

提交 1 之后重跑那 16 条离线轴，仍然 **16/16 `exit=0`**，两个跟着提交动的数记下：`check_changelog_headings: HEAD=83 tree=83 lost=0`（§五 表里那行 82/83 是提交前拍的，多出的 1 条现已并入 HEAD，等号回来），`check_char_sanity: pages=198 prose CJK chars=423033`（比 §五 表的 422,629 多 404 字，就是本节写下的这些）。

§五 欠下的那一判（表格里有没有横向溢出）在这里补上，两条腿一起：

- **常驻轴读不了这一页**：`check_table_overflow.py` 对 `00-index/changelog.md` 给的是 `NOHYDRATE ... — harness/CDN, not a content verdict`，整跑 `problems=1` 且唯一一条就是它。也就是说这张 25 MB 的页面**溢出轴也拿不到**，与 §一 的轮次水位线是同一个瓶颈的两种表现——是否拆页仍是操作者的取舍，本轮不动它。
- **本节整段重渲**：`rendered html: 6 h3, 3 pre, 11030 chars`（比 §五 那一帧多出 1 个 `pre`，就是本节上面的读数块），出图 820×9000。
- **把 §五 的 16 行表单独按 768 读者列宽渲染并量墨**：`table rows captured=18 (header+sep+16 body)`、`longest row chars=187`、`capture=820x1600 content-rows=24..997 rightmost-ink-x=782 ink-touching-right-edge-rows=0`。最右一滴墨在 x=782，读者列右边界是 24+768=792，且没有任何一行把墨顶到取景框右缘——**表格不溢出，留 10px 余量**。目检同一帧：两列都在列内换行、无裁切、无叠字；左列的判据名被从单词中间断开（`check_widget_pai / ring.py`）是本帧 CSS 的 `word-break:break-all`，不是平台行为，所以它不算缺陷也不算证据，只是别把它读成平台样式。

本轮留下的账：① #132 那条（作者 `**…**` 跨度 vs 线上 `<strong>` 实际范围）仍未量，仍是「先量再决定要不要装第三条腿」；② 短读门闩只判**尾部到齐**，判不出 CDN 两份都完整但大小不同的副本（本轮实测 23,351,607 与 25,994,905 字节同时存在），所以轮次以外的任何字节比较都不能进门闩；③ html 腿停在 90 是第 83 轮定下的口径（大声 NOTE，不 gate），本节写完后它需要再翻页一次才算读者拿得到。


## 2026-09-25（第 90 次）`UNWITNESSED` 那本账挂了五轮，本轮先量它的价再动它：最近 40 次文档修订里 **113 次读者页触碰有 77 次**落进永久红的桶——「只改日期」的修订从此读绿，而「真没同步的页绝不落进这个桶」由控制 W 钉在真实切片跑上，另配一条让切片器失明的变异体 W2

本轮正文 **0 页知识页改动**：读者可见文字只动本页（新增本节）。**没有为过线删掉或加厚任何一页正文**——这轮改的是 `tools/checks/check_live_sync.py` 的判决归属，而它不改任何一行被判决的内容。

### 一、缺陷与它的价：先量「这本账多久踩一次」，再谈改判据

账的来路逐字可查：第 85 轮 §八 第一次写下这条 `UNWITNESSED`（`docs/06-memory-rag/long-context-degradation.md`，那一处只动了 Mermaid 指令行的颜色），并记下「列为第 87 轮第一件事：把『本轮没有读者可见新增』与『追不到文本』分成两桶」；第 86 轮 §八 原样转发；第 87 轮 §十 记「`UNWITNESSED` 桶的分桶仍未动……仍是第 88 轮」；第 88 轮 §九 写「本轮**没做**，仍欠」；第 89 轮 §五 ③ 写「**连续第三轮没做**」。本轮不再口头再欠一次：按「先量再改」的规矩，先离线量出这把永久红到底多久踩一次（不碰网线，只跑切片器）。

```text
recent 40 docs-revs: reader-pages=113 unwitnessable=77
99f6fc3 Round 73: ... 11/11 pages cannot witness
```

113 次读者页触碰里 77 次落进 `UNWITNESSED`——只改 `updated:` 日期、只改 Mermaid 颜色指令、只挪标记位置的修订全都算。它们在旧语义下是**失败行**：`--watch` 会为了一个任何同步都追不动的红把整段轮询预算烧光。上面那次 `99f6fc3`（第 73 轮的主提交）改到的 11 个页面**全部**是这个桶。

### 二、分桶：五个桶，两个纯函数，边界只有一条

旧判据把「无法作证」当失败。本轮把它拆成独立的一档，判决逻辑写成两个可直接喂控制的纯函数（`tools/checks/check_live_sync.py`，下面是函数体的原样摘录）：

```text
def page_bucket(url, needles):      # 抓取之前，证据本身怎么说
    if not url:
        return "NO-URL"
    if not needles:
        return "UNWITNESSED"        # 响，但不进 bad
    return None                     # 有针： fetch 说了算

def page_verdict(needles, lost, phantom):   # 抓取之后，读者文字怎么说
    if phantom:
        return "VACUITY"            # 故意压过 STALE：针自己会应答，正反两向都不能作证
    if lost:
        return "STALE"
    if not needles:
        return "UNWITNESSED"
    return "OK"
```

`witness_leg()` 返回三元组 `(bad, unwitnessable, witnessed)`，`ok = have >= want and not bad` 一字未动——变的只是 `UNWITNESSED` 不再进 `bad`。边界只有一条，而它就是这本账欠的那句「改成桶必须同时新增一条控制，证明『真没同步的页绝不落进那个桶』，否则就是把红改成白」（第 89 轮 §五 ③ 原文）：**`UNWITNESSED` 只能经由空针列表到达**，而针列表唯一的产地是 `needles_from`（自带九条控制）。真加了可打印正文、线上却没有的页，判不出 `STALE` 以外的任何值。

### 三、控制 W 与变异体 W2：边界两头各钉一次

- **W**（`--selftest` 内）：针从**真实切片跑**取，不手搓列表——有针的页必须放行去 fetch；`page_verdict(wns, wns, False)` 必须是 `STALE`；全到位是 `OK`；针自匹配是 `VACUITY`；空针是 `UNWITNESSED`；无地址是 `NO-URL`。并且若真实切片器对一句明显的新散文**产不出针**，控制直接红：那等于边界没被任何真页踩到，`STALE` 会全变成 `UNWITNESSED`。
- **W2**：第 89 轮那句账真正指向的变异体——把 `needles_from` 猴补丁成恒返回 `[]`（即「切片器失明」）。失明之后每一页都必须暴露成 `UNWITNESSED`（门从红变绿，但 cannot-witness 行**照印**），而不是静静地把 11 个真红说成 0 个。
- 两个变异体各跑一遍（在当前代码上重跑，逐字）：强制 `page_bucket` 恒返回 `None` 读出 `controls red: 3`——`a markup-only revision must land in UNWITNESSED, got None`、`an addressable-by-no-page touched file must stay NO-URL/bad, got None`、`a blind slicer must expose itself as UNWITNESSED on every page`；强制 `page_verdict` 恒返回 `"OK"` 读出 `controls red: 2`——`unsynced page WITH needles must verdict STALE, got 'OK'`、`a self-matching needle must verdict VACUITY (overrides STALE), got 'OK'`。撤掉猴补丁后 `--selftest` 回 `controls: OK, every needle rule able to fire`——W 不是摆设。

### 四、同一修订、新旧两份代码：红 → 响而不红（前后对平）

旧代码（`git show HEAD:tools/checks/check_live_sync.py`）在 `--rev 99f6fc3` 上（逐字）：

```text
  leg md   newest round=89  (318813 bytes, 146 rounds)
  UNWITNESSED docs/02-agent-basics/perception-planning-action.md (99f6fc3 added no sliceable text there)
  ...（共 11 行）
  witness: 99f6fc3 added no reader-page text outside the changelog — the .md leg is the witness
not online yet: md leg round 89 vs HEAD 89, witness failures 11   # exit 1
```

`md` 腿已经是本轮最新，这一行却永远追不动——那正是 §一 量的价。新代码同一修订（逐字）：

```text
  leg md   newest round=89  (318813 bytes, 146 rounds)
  leg html newest round=89  (24308344 bytes, 525 rounds)
  UNWITNESSED docs/02-agent-basics/perception-planning-action.md (99f6fc3 added no printable text there — the .md leg is this revision's only witness)
  ...（共 11 行）
  witness: 99f6fc3 added no reader-page text outside the changelog — the .md leg is the witness
  witness: 11 page(s) CANNOT WITNESS 99f6fc3 (round 90's bucket: loud, never green — this revision is only evidenced by the .md leg)
```

exit 0。混合修订（第 75 轮主提交 `b8a253d`，26 页里 7 页有针）复跑：

```text
  witness ok  docs/09-frameworks/README.md                   1/1 added needles live
  witness ok  docs/12-applications/coding-agent.md           2/2 added needles live
  witness ok  docs/README.md                                 3/3 added needles live
  ...（witness ok 共 7 行 / UNWITNESSED 共 19 行）
  witness: 7 reader page(s) b8a253d touched carry b8a253d's added text
  witness: 19 page(s) CANNOT WITNESS b8a253d (round 90's bucket: loud, never green — this revision is only evidenced by the .md leg)
```

exit 0，`witness ok` 与 cannot-witness 并存——桶没有把可作的证吞掉。**FETCH 仍然卡门，本轮实测到**：同一修订首跑抓到 2 条 `FETCH ... URLError` 时 exit 1，逐页行与 `not online yet: ... witness failures 2` 都在；复跑网络恢复即 7/7 全绿。桶只放走「无法作证」，没放走过任何一条真判决。

**本轮的网络返工如实记**：`ConnectionResetError(10054)` 打中过 4 次旧代码运行、2 次新代码运行——全部是两份 changelog 大文档（24 MB 的 HTML 页最重，小文档腿能过）；一次独立单发请求就在失败后几秒成功。因此 §四 的旧代码那次运行用了一层 monkeypatch（md 响应缓存重试、HTML 腿用本轮已录读数代替抓取），被控制的只有抓取重试，witness 逻辑与桶归属逐字未动。

### 五、留下的账与下一步

- **NO-URL 仍按「失败」处理**：本轮只重挂了 `UNWITNESSED`。读者页若地址查不到，两向都不能作证，与「无法作证」不同——那说明判据视野缺一页，重挂成不卡门等于把缺页说成正常。它保持红是有意的，不是漏改。
- **`--rev` 语义没变**：witness 腿仍可指向历史修订；桶改动对「当前 HEAD 是否已上线」这个主用法只有一个后果——日期型修订不再让 `--watch` 白烧预算（§一 的 77/113）。
- 第 89 轮 §五 ④ 那三条本轮一个字没动：`check_live_sync` 的落后判断（HTML 页 lag 仍是 NOTE）、`published_cut` 的切点分辨率、`grade()` 对 `*` 只知位置不知生效。14 归一字符地板照旧。
- **旧代码的 before 读数依赖一层 monkeypatch**（见 §四 末段）：它证明了旧桶把 `UNWITNESSED` 喂进 `bad` 且 `ok` 因此永假，但它不是「网络正常时的一整趟旧代码运行」。下一轮若要在真实网络下复现 before 值，挑只改日期的修订当天跑即可。

### 六、离线电池（提交前，逐条；工作树即本轮将要提交的内容）

| 判据 | 读数 |
| --- | --- |
| `check_structure.py` | `pages scanned=198 problems=0`，`executable-tagged=0`，`json contracts parsed=79 unclosed=0`——**首跑它抓住的是本节自己**：贴判据代码时开了 `python` 围栏，`CODEFENCE 00-index/changelog.md: body-line 25`，改标 `text` 后复跑归零（内容一字没删，房规由第 79 轮那条轴守着） |
| `check_changelog_headings.py` | `HEAD=81 tree=82 lost=0`（新增一节，没弄丢任何旧标题） |
| `check_readme_stats.py` | `banner pages=196 measured=196`，`README, homepage and cover banner match the tree on every axis.` |
| `check_updated_dates.py` | `reader pages=198 checked=196 exempt=2 problems=0 pending-commit=0`（本轮没碰任何读者页的 `updated:`，这正是它该读 0 的形状） |
| `check_char_sanity.py` | `pages=198 prose CJK chars=418893 traditional-form findings=0` |
| `check_widget_pairing.py` | `pages=198 problems=0`，控制 `phantom=3` |
| `check_quote_fidelity.py` | `attributed quotes=25 findings=0 verified=23`——本节引用的第 89 轮 §五 ③ 与第 87 轮 §十 原句都在 `RETRACTED-OK/PROSE` 里对上 |
| `check_katex_formulas.py` | `pages=108 formulas=927 failures=0 version=0.18.7` |
| `check_genre_floors.py` | `pages=196 published=196 graded=159 problems=0` |
| `check_lab_runnability.py` | `labs=6 exit0=6 deterministic=6 records_current=6/6 findings=0` |
| `check_emphasis_flanking.py`（作者腿） | `pages=0 leaked_strong_markers=0`——新增这一节没有往任何页留裸星号 |
| `check_prose_survival.py --selftest` | `controls: OK, every bucket able to fire`（22 条 A–V） |
| `check_live_sync.py --selftest` | `controls: OK, every needle rule able to fire`（9 条切片 + W + W2 + N） |
| `check_link_graph.py` | `ok=702 blocked=14 net=1 unchecked=0 fragments=0 FAILED: 0`，`exit=0` |
| `check_prose_duplicates.py` | `pages=191 prose_units=7424 formula_units=274 dup=0 near-band=3`（近重复三条是索引页转述，advisory 不卡门） |

这两条徽章（链接图 / 跨页重复）按第 86 轮的账**在同一把尺子上随写文档自己挪数**，所以它们的本轮读数记在这里而不是别处；判定挂工作树，而提交后工作树即 `HEAD`，两者同值。

### 七、收尾（提交并推送、线上同步之后）：新桶第一次在真修订上落地，两条网络事实如实记

`dd018c9` 推送后 `check_live_sync.py --watch` 到收敛（最后一次探测，逐字）：

```text
HEAD committed 2026-09-25, 2 min ago
local newest round=90
  leg md   newest round=90  (330545 bytes, 149 rounds)
  leg html newest round=89  (24308344 bytes, 525 rounds)  missing 90
  witness: HEAD added no reader-page text outside the changelog — the .md leg is the witness
  NOTE the published changelog PAGE is at round 89: readers opening it are missing 90
```

`exit=0`，两条探测之间没有任何 UNWITNESSED 行——第 90 轮提交只动更新日志一页，这正是新桶语义下「witness 腿无事可判」应有的形状（旧语义同形：无读者页可碰就不产桶行；变的是有读者页但无新增字的那 77/113）。全站散文判据（重试后的那一趟，逐字）：

```text
lost sentences: MISS=0 REVISION-BEHIND=0 STALE-COPY=47 | pages-with-MISS=0 fetch-failures=0 not-listed=0
   00-index/changelog.md MISS=0 behind=0 unpublished=47 of 3896 units (published copy proves nothing below line 228)
```

`MISS=0 REVISION-BEHIND=0`——收尾断言按第 89 轮定的口径只钉这两条。`STALE-COPY=47` 全部在本页：新写的第 90 次一节坐在渲染页尚未到达的位置上（切点行 228＝第 88 次的标题），也就是 NOTE 那一行的同一件事，不是丢字。**这一趟之前还有一次盲跑**：196 页里 53 页被 `ConnectionResetError(10054)` 打断（`fetch-failures=53`），它一个字判据都没给出——判据没看过的页不是干净的页，冷却 3 分钟后复跑才有上面这组数。同步后对本页重跑活体控制（`--mutate 00-index/changelog`，`exit=0`，逐字）：

```text
mutation control: hid a plain (probe '注入收益从夺取行动转向', 164 chars, 1 reader copies, 2 off-reader copies) and the judge named it a MISS, not a lag
mutation control: hid a heading (probe '先写的估字宽探针被自己的控制判死', 108 chars, 1 reader copies, 3 off-reader copies) and the judge named it a MISS, not a lag
mutation control: hid a quote (probe '与工作树的条目标题', 29 chars, 1 reader copies, 2 off-reader copies) and the judge named it a MISS, not a lag
```

三条探针都落在**已发布**的字上（第 53 轮正文、第 66 轮标题、第 66 轮引用行），账目形状与第 89 轮一致：读者在场恰好 1 份、不在场 2–3 份。强调腿 `--live` 读 `live leg: pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0`——新写的一节没往读者眼前留裸星号。**这句是旧视野下的读数**：当时那条腿只看正文一栏，本页 §八 量出它漏掉了页面目录那一栏，口径已改，同步之后重取的读数记在 §八 末。

**网络返工的两条事实**（都影响下一轮怎么读这条门的红）：其一，本轮 `ConnectionResetError(10054)` 打中过 6 次旧代码运行与 1 次新代码全站跑——**全部在两份 changelog 大文档上**（24 MB 的渲染页最重），同一时刻单发请求与小页面抓取都能过；因此 §四 的旧代码 before 读数经过一层只包 fetch 的 shim（md 缓存重试、html 用本轮已录读数），桶逻辑逐字未跑偏。其二，`.md` 腿 2 分钟追上、渲染页 15 分钟后仍在第 89 次——第 83 轮的「NOTE 不卡门」设计在本轮第一次成为**收尾目检要等的对象**：截图一帧等渲染页发出第 90 次一节再拍，等的过程本身不改判据。

### 八、等截图的这一趟，先等到一条「读者看得见、两条腿都看不见」的裸星号

**目检探针自己也先错了一次。** 第一版探针用 `createTreeWalker(document.body, SHOW_TEXT)` 数页面上字面出现的 `**`，读 `inProse=886`——它把 Next.js 的 `<script>` 载荷也算成了「读者眼前的散文」（抽出来的样本全是 `self.__next_f.push([1,…`）。修法是给 walker 加 `acceptNode`，拒绝 SCRIPT/STYLE/NOSCRIPT/TEMPLATE 子树；同一页改完读 `inCode=97 inProse=1`。**886 → 1 是尺子的错**，而且错在假红那一侧：照这份读数开一张「886 处缺陷」的清单，本轮就会去改一堆根本不存在的东西。

**那 1 处是真的**，位置在页面右侧「On this page」目录里：第 87 轮 §三 那条标题把一对星号写在行内代码里当作被讨论的记号（就是本节上面引号里那个写法，正文栏渲染成代码框），目录栏却把它**重印成纯文本**——反引号被平台去掉了，星号留下。两条独立证据：浏览器 DOM 里那一处的祖先链是 `span < a < li < ul < div < div < div`、`closest('main')` 为空；抓 HTML 数「配成了」四次，一次带 `<code>` 标签（正文）、一次是 `<a href="#…">` 里的裸文本（目录）、两次躺在转义过的 RSC 载荷里。**这是「同一处作者失误、两处视野」**——第 58 轮 `live_aria_manifest.leak_sites` 的注释里为公式写过这句话，强调轴第 84 轮建的时候没有复用那条拆分：作者腿把行内代码空白成一个原子（对正文是对的），live 腿走 `body_visible()`，而那个函数专门丢掉 `<a href="#…">` 锚点。于是两条腿一起对着一处读者每天都路过的字符报绿。

**修法只加视野，不松口径。** 作者腿新增 `heading_paras()`：按平台的方式把标题展平（行内代码取其内容、链接取其标签），再丢进**同一条** flanking 规则——配对逻辑没有第二份（`unpaired(text, paras=...)` 共用原函数）。live 腿改用含目录的那份可见文本。首跑全站：

```text
emphasis flanking: pages=1 leaked_strong_markers=1 (body=0 outline=1) lone_star_runs=1 (context only)
```

`exit=1`。页面级校准（同一份已发布页面，逐字）：作者腿预测「正文 0 + 目录 1」＝1，含目录的 served 字面 `**` ＝1，而旧的只看正文的 served ＝0。**盲区被量成恰好那一个字符**，不是靠估计。

**控制从 12 条扩到 17 条**（`CONTROL_PAGES` 改成「正文期望 / 目录期望」双列）。新增 5 条钉住这条视野的两端：目录确实会印出行内代码里的星号（期望 1）；标题里合法成对的粗体不许误报（0）；`get_weather`、`tool_result` 这类**单下划线标识符**不许被新视野顺手抓进来（0）；围栏里演示用的假标题不进目录视野（0）；标题里的链接展平成标签之后合法对仍然合法（0）。另加一条反向断言：同一句标题若目录规则**不响**，`--selftest` 就是红的—— widened 的规则必须先证明自己抓得住，否则「绿」只是「没在看」。改完标题后全站重读 `pages=0 leaked_strong_markers=0 (body=0 outline=0)`，`controls: OK, every bucket able to fire`。

**为什么全站只有那 1 条红**——分母由判据自己印出来，不靠手算（`check_emphasis_flanking.py` 现在每次都印一行）：

```text
outline scope: headings=2839 carrying_inline_code=104 whose_flattening_is_markdown_significant=71
```

2839 条标题里 104 条带行内代码，展平后含 markdown 意义字符的是 71 条；这 71 条**一条都不产「flanking 表配不上的那一对」**：30 条只有落单星号（第 84 轮就把这类定为「印上下文、不判」——glob 与脚注号在没有意图时和真漏出的星号不可分）、27 条是 `get_weather`、`similarity_top_k` 这类标识符里的单个下划线（不成对就不是强调分隔符）、其余是 `[t]`、`<style>`、`##` 这些形状。这条轴按 flanking 表判而不是按字符黑名单判，所以那 70 条既不需要点名豁免，也不会哪天莫名变红；修复前红的那一条是 71 里唯一真会被印成裸星号的。

**内容侧改的是标题里的记号，不是那一节的字**：§三 的标题改成「平台把『成对星号』配成了『第一个配最后一个』」，正文里用来举例的 `` `**` `` 一律保留（它们渲染为代码，读者看到的是代码框）。

**留下的账三条**：① 改的是一条**已发布**页面上的字，所以同步之前散文腿会把它读成 `REVISION-BEHIND`（第 88 轮建那个桶正是为了这种形状），追平后归零；② 同理强调腿 `--live` 在同步前会读 `prediction-mismatch=1`（线上那 1 个字符还在、预测已经 0），它是「本轮还没发出去」而不是站点缺陷；③ §七 里那句强调腿读数是旧视野下的，本轮之后按新口径重取，记在下面。

**同步之后重取的两条（新口径，逐字）**：

```text
emphasis flanking: pages=0 leaked_strong_markers=0 (body=0 outline=0) lone_star_runs=1 (context only)
outline scope: headings=2839 carrying_inline_code=104 whose_flattening_is_markdown_significant=71
live leg: pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0
```

`prediction-mismatch` 从同步前的 1 落到 0，`served_markers=0`——含目录的那份可见文本里，全站 196 页读者眼前一个裸 `**` 都没有。分母与修复前同一行（2839/104/71）：本轮只改了那一条标题里的记号，没动其他标题的形状。

**目检三帧**（真实渲染页，非本地副本）：① 目录栏里那条标题的整块截图，逐字是「三、唯一一条真的读者侧缺陷：平台把『成对星号』配成了『第一个配最后一个』」，星号不在；② 同一页正文栏滚到该标题处，页面顶部与目录同框；③ 更新日志页首屏，第 90 次的条目标题完整印出。目录那一处的 DOM 证据与像素各取一次（逐字）：

```json
{"text": "三、唯一一条真的读者侧缺陷：平台把「成对星号」配成了「第一个配最后一个」", "has_marker": false,
 "html": "<span class=\"\">三、唯一一条真的读者侧缺陷：平台把「成对星号」配成了「第一个配最后一个」<!-- --></span>"}
```

`html` 里那个 `<span>` 就是旧缺陷的位置：修复前它装的是去掉反引号的裸星号，现在装的是「成对星号」四个汉字。这条轴的判据与眼睛在这一处对上了。

**补写这一段之后，离线电池整条复跑**（逐字关键读数）：`pages scanned=198 problems=0`、`executable-tagged=0`、`json contracts parsed=80 unclosed=0`——§六 那行记的是 79，差的 1 正是本节末尾这个 json 围栏（本节末尾新贴了目录那一处的 DOM 证据）；`changelog headings: HEAD=82 tree=82 lost=0`；`prose duplicates: pages=191 prose_units=7427 ... dup=0 near-band=3`（§六 的 7424 同样只差本节新写的字）；`traditional-form findings=0`；`controls: OK, every bucket able to fire` 与 `controls: OK, every needle rule able to fire`；链接图 `ok=702 blocked=14 FAILED: 0`。全绿，`exit=0`。

**尾腿（推送 `0805a59` 之后，一条一条串行跑，逐字）**：`check_live_sync` `exit=0`，`leg md newest round=90 (336586 bytes, 154 rounds)`、`leg html newest round=90 (25108708 bytes, 544 rounds)`、`witness: HEAD added no reader-page text outside the changelog — the .md leg is the witness`；强调腿 `--live` 在新口径下复读 `pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0`；活体控制 `--mutate 00-index/changelog` `exit=0`，三条探针各藏住一句真实字并被 judge 判成 MISS 而非 lag（plain 159 字／1 份读者副本、heading 118 字／1 份、quote 29 字／1 份，不在场副本 2–3 份）。

**唯一没有归零的是散文腿的 `REVISION-BEHIND=17`**（`MISS=0`、`exit=0`）。判据给出的豁免证据本身就是结论：发布页在同一处缺口里印着「为什么全站 44 条标题只有这 1 条红…」——那是 `a5e3e62` 之前的写法，树里已经没有了，所以这是**平台发了旧版**，不是它吞了句子。同一分钟里 `.md` 端的一次直接抓取已经带着本节补写的字（621,559 B），而 `check_live_sync` 的 md 腿读 336,586 B——两个读数差得远，本轮没有把这件事判成任何结论，只记下来。渲染页停在 25,108,708 B 不动，正是 §七 记过的「25 MB 文档按平台自己的节奏翻页」第二次落地。**下一轮开头要确认的一件事**：这 17 条随页面翻页归零，且补写本段自己新增的字也在同一本账里——断言写成「`behind` 里不再出现本节之外的页」，而不是「`behind=0`」。

**第 91 轮回补本段（不改上面这句写下时的判断）**：那 17 条没有归零，而是长成 25 条；逐条列出后全部落在本节第 172–207 行之内的同一页上，「本节之外的页」为 0 条，所以本段预告的断言按它自己的口径判定通过（旧判据每页只印 1 条例句，这句断言当时根本无法判定，第 91 轮给它补了 `--list-behind`）。而本段那个「两个读数差得远」的疑点，答案是**本段自己把单位读错了**：`check_live_sync` 的腿线一直把 UTF-8 解码后的字符数标成 bytes——同一份 `.md` 在第 91 轮实测 337,508 字符 / 623,168 字节，比率 1.846，两个读数本来就是同一个文档、同一次抓取。上面「没有把这件事判成任何结论」是对的，但把差异记成「差得远」是错的：差的是 1.846 倍单位，不是两版内容。同段的 25,108,708 同样是字符数（HTML 实测 25,994,905 字节），所以「25 MB 文档」的说法没有被推翻。

## 2026-09-25（第 89 次）活体变异控制从「只会藏散文句」长成三种句子都会藏——而且它第一次分清「读者眼前有几份」与「这串字在页面上还有」；顺手量倒第 88 轮收尾那句「一字不差」

本轮正文 **0 页知识页改动**：读者可见文字只动两处——本页新增本节，以及首页那条完整性句按新读数重写（控制条数与字母表、`--mutate` 那条的描述、第 88 轮写错的等号）。**没有为过线删掉或加厚任何一页正文**；改动全部在尺子上（`tools/checks/check_prose_survival.py`）。

### 一、缺陷：第 88 轮 §八 ① 那条账，改造首跑就量出「控制自己算错了副本」

`--mutate` 从只藏 `plain` 扩到三种单元的第一版，在真实发布页上读了三条红（逐字）：

```text
    mutation control could not hide 'agentloop' inside 00-index/changelog.md
    mutation control: heading on 00-index/changelog.md still read as lost with 1 of 4 copies of the probe left on the page ('同一页在真浏览器里被侧栏和页内')
    mutation control: quote on 00-index/changelog.md still read as lost with 1 of 3 copies of the probe left on the page ('随后量的图就读成了原始尺寸')
```

那两行的「4 份 / 3 份」是**控制的账错**：判据读的是 `LA.body_visible()`，它连内容一起删掉 `<script|style|pre|code|annotation>` 与 `<a href="#…">` 两类范围，而那几份里读者眼前只有 1 份。第二条改造换成「不在标签里就算读者看得见」，同一个错倒在反方向，量出来更刺眼：

```text
mutation control: hid a heading (probe '同一页在真浏览器里被侧栏和页内', 117 chars, 4 visible copies) and the judge named it a MISS, not a lag; with 1 of 4 copies left it stays clean
    mutation control did NOT fire: hiding a real plain on 00-index/changelog.md read as clean
```

`did NOT fire` 不是判据漏判——选中的那句真散文**唯一的 raw 连续副本住在 `<script>` 的编辑器负载里**，把它藏掉对判据一个字都没动。也就是说：一条「藏字必须响」的控制，如果它算副本的范围比判据宽，它会先给自己发假绿（第 ① ② 行），再在反向误判时喊狼来了（第 ③ 行）。

### 二、修法：副本按判据自己读的那片文字算，一次给三条判决

`OFFPAGE_BLOCK` 与 `OFFPAGE_NAV` 逐字镜像 `live_aria_manifest.visible()` 的两条删除规则（不是「差不多」，是同一串模式），控制先把它们命中的范围并成「读者不在场」的区间，再数探针的在场副本。三态：

- 藏掉**全部读者在场副本** → `grade()` 必须点名，且 `classify()` 必须判 `MISS`，不许被 `REVISION-BEHIND` 免掉；
- 只藏**读者不在场副本**（侧栏、脚本、代码盒里的那些），读者的副本一根不动 → 必须**全绿**；
- 读者在场副本 > 1 时，逐一试「只留第 i 份」，至少一份要读绿。

真实发布页三趟（每趟 `exit=0`，逐字）：

```text
00-index/changelog.md
  hid a plain (probe '每章内部只有一种主色', 212 chars, 1 reader copies, 2 off-reader copies) and the judge named it a MISS, not a lag
  hid a heading (probe '同一页在真浏览器里被侧栏和页内', 117 chars, 1 reader copies, 3 off-reader copies) and the judge named it a MISS, not a lag
  hid a quote (probe '随后量的图就读成了原始尺寸', 110 chars, 1 reader copies, 2 off-reader copies) and the judge named it a MISS, not a lag
04-prompt-reasoning/chain-of-thought.md
  hid a plain (probe '就是把没算完的步补上', 77 chars, 1 reader copies, 2 off-reader copies) ...
  hid a heading (probe '为什么多写几步就变准', 16 chars, 1 reader copies, 3 off-reader copies) ...
  ships no quote unit to hide
docs/README.md（首页）
  hid a plain (probe '在本机复量了那条路给多少', 42 chars, 1 reader copies, 1 off-reader copies) ...
  hid a heading (probe '按主题挑资源', 22 chars, 1 reader copies, 3 off-reader copies) ...
  hid a quote (probe 'continuously', 507 chars, 1 reader copies, 2 off-reader copies) ...
```

`chain-of-thought` 那一页根本没有 `>` 引用行，所以「这一种单元没得藏」必须报**跳过**而不是报红——一条要求每张页都有引用的控制会把自己的形状当成网站的缺陷。`--selftest` 的 22 条种植控制全绿（`controls: OK, every bucket able to fire`）。

### 三、控制 V：多副本那条分支今天没有真实页踩得到，就钉在合成页上

上面三页里每一个探针都恰好只有 **1 份**读者在场副本，也就是说「留 1 份必须绿」这一支在本轮的网站上从未被执行。补一条离线控制 V：一页同时带 2 份 `<h2>` 正文副本、1 份 `<a href="#">` 侧栏副本、1 份 `<pre>` 副本，三种判决同时钉住——只清侧栏与代码必须全绿，两份正文都清必须**只**点名那一条标题（侧栏还印着同样的字，也不许它免判），清掉一份必须全绿。这条控制是第二节那个口径的守夜人：平台哪天换了侧栏的 DOM 形状，`OFFPAGE_*` 与判据就得一起改，否则 V 先红。

### 四、第 88 轮收尾那句「一字不差」本轮量倒，改在字上而不是内容上

首页第 88 轮写的是：`且 units=13923 与推送前那一趟一字不差`。本轮开工首跑（此时 `docs/` 与第 88 轮收尾那次提交**完全相同**，本轮改动都在 `tools/`）读：

```text
prose survival: pages=196 units=13940 plain=11707 heading=641 quote=57 widget=1535 | all
lost sentences: MISS=0 REVISION-BEHIND=0 STALE-COPY=0 | pages-with-MISS=0 fetch-failures=0 not-listed=0
OK: every graded sentence reaches the reader
```

`units` 差 **17**（`plain` 11691→11707、`heading` 640→641），而那 17 条正是收尾提交自己新写的字。**这条等号本来就不该写成「计数一字不差」**——写文档就能挪动的数，钉子只能钉在判据推不动的地方：`MISS=0` 且 `REVISION-BEHIND=0`。首页已按实测改成这个口径，并把 13940 与它的来路写在原句里（第 75 轮那条「措辞能挪动的数给地板、挪不动的才给等号」的规矩，本轮是**它自己没遵守**）。

### 五、留下的账与下一步

① 第 88 轮 ①（活体控制只藏散文句）**本轮销了**：三种单元都在真实发布页上藏过并判对，另加「只藏侧栏副本不许响」这半边。② **14 归一字符地板**照旧对三条腿一律适用，短标题、短引用不判。③ 第 87 轮记的 `UNWITNESSED` 重挂（把 witness 腿「无法作证」的页改判成桶而不是名单）**连续第三轮没做**，本轮也没给它任何量测——它的性质是**预防性**改造：改成桶必须同时新增一条控制，证明「真没同步的页绝不落进那个桶」，否则就是把红改成白。本轮的预算给了第二节那条能实测出错的控制。④ `check_live_sync` 的落后判断、`published_cut` 的切点分辨率、`grade()` 对 `*` 只知位置不知生效——三条本轮一个字没动。

### 六、收尾（提交并推送、线上同步之后）：活体控制、全站判据、witness 与强调腿各自重读一遍

推送后 `check_live_sync.py --watch` 到收敛（最后一次探测，逐字）：

```text
HEAD committed 2026-09-25, 2 min ago
local newest round=89
  leg md   newest round=89  (318813 bytes, 146 rounds)
  leg html newest round=89  (24208580 bytes, 519 rounds)
  witness ok  docs/README.md                                 3/3 added needles live
  witness: 1 reader page(s) HEAD touched carry HEAD's added text
```

线上全站散文判据（同步收敛后那一趟，逐字）：

```text
prose survival: pages=196 units=13979 plain=11740 heading=647 quote=57 widget=1535 | all
lost sentences: MISS=0 REVISION-BEHIND=0 STALE-COPY=0 | pages-with-MISS=0 fetch-failures=0 not-listed=0
```

`units` 从开工首跑的 13940 涨到 13979（+39），全部是本轮自己写进去的字（第一~五节 + 首页重写），三个桶照旧全零——这正是第四节改过的口径该看到的样子：钉子只在 `MISS=0 / REVISION-BEHIND=0`，不在计数。线上同步后对**本页**重跑活体控制（`--mutate 00-index/changelog`，`exit=0`，逐字）：

```text
mutation control: hid a plain (probe '每张图的提示语各说这一张的原图宽', 193 chars, 1 reader copies, 2 off-reader copies) and the judge named it a MISS, not a lag
mutation control: hid a heading (probe '而句子一个字没动', 112 chars, 1 reader copies, 3 off-reader copies) and the judge named it a MISS, not a lag
mutation control: hid a quote (probe '拿高度算比值会得到', 72 chars, 1 reader copies, 2 off-reader copies) and the judge named it a MISS, not a lag
```

三条探针是同步后页面新命中的候选：第 77 轮标题里的 `而句子一个字没动`、第 75 轮正文里的 `每张图的提示语各说这一张的原图宽`、第 72 轮引用行里的 `拿高度算比值会得到`。账目形状与第二节一致：每句读者在场恰好 1 份、读者不在场 2–3 份。强调腿 `check_emphasis_flanking.py --live` 读 `live leg: pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0`。

真实渲染截图两帧（Edge headless、视口 1280、`--live`）：本页第 89 次一节是线上第一个 `<h2>`，粗体、内联代码与围栏读数盒渲染正常；首页重写句无 `**`、无漏标。**两处目检探针自身的错也如实记账**（是尺子错，不是网站错）：一帧用 `startsWith('第 89 次')` 找节标题，而真实标题以日期开头，报 `target_found False`；另一帧数 `**` 泄漏时把 `<pre>` 与内联代码里的星号算了进去（95/5 个），权威强调轴一律剥掉这些范围，读数是 0。

离线电池（结构、围栏、frontmatter、解析器、changelog 标题、README 统计、日期、`--selftest` 22 条控制）本地与提交前各一遍，全绿；第 89 轮到此收口。

## 2026-09-25（第 88 次）完整性判据这一轮长了三只新眼睛——分得清「平台发的是另一版」与「渲染器吞了字」、读得到章节标题、读得到引用块；而它「到底读了多少页」第一次被首页那句话管住：加了一条控制，首页立刻红

本轮正文 **0 页知识页改动**：读者可见文字只动两处——本页新增本节，以及首页那条完整性句按新读数重写（页数口径、单元读数、控制清单、「留下的账」从三条改为四条）。**没有为过线删掉或加厚任何一页正文**；本轮全部改动都在尺子上（`tools/checks/check_prose_survival.py`、`tools/checks/live_aria_manifest.py` 的一处注释）。

### 一、缺陷：第 87 轮自己记下的三条账，加一条本轮现场量出来的视野缺失

第 87 轮收尾时写在首页的账，逐字是这三条：`published_cut()` 只能按轮次号切、**同轮的改动它判不出**（那一轮自己就因此红过八分钟）；**标题不是单元**（没有任何一条线上轴读过发布稿里的 `##`，一节标题整个消失也能全绿）；以及第 86 轮末尾记下的「**一条判据扫了多少页**」这件事本身没有对平轴。本轮开工先量第四处：`chunks()` 的作者侧扫描器从写下第一天起就整行跳过 `>` 引用块——那些行里的句子**读者看得见**，判据看不见。

### 二、`REVISION-BEHIND`：豁免要有本地证据，而且证据必须只可能是改版造出来的

`published_cut()` 的切点是钝器：它只能说「发布稿印到了第 N 轮」，说不了「这一段是另一版」。所以新增一个桶：一条丢失的句子，如果**发布稿在树与线上都唯一同意的两个锚点之间**，印出了一段**含树里完全没有的词**的连续文本，就判 `REVISION-BEHIND` 而不是 `MISS`。

豁免为什么不会变成新的瞎：判别式卡在「新增词」上。一次改版会先写新句再丢旧句，所以发布稿里必然有树中无处的词；而**渲染器吞句只会把树里已有的词粘在一起**，粘起来的那一句永远自证不了「新措辞」。第 88 轮的活体变异控制正是撞在这条上——它藏掉的是真实句子的开头，剩下的部分全来自树，于是豁免不成立、判 `MISS`。控制 N–U 里四条管这个桶（旧措辞只落在**这一段**缺口才免、缺口空着必须 `MISS`、别段的旧字不许替这段作保、锚点不唯一不给免），并且把 `says_something_new()` 分别钉成常真与常假各跑一遍：**常真时红在 P/R/S 三条，常假时红在 N/P/R/S 四条**（本轮复跑的原话是 `control S: two tree fragments glued across a deletion say nothing the tree never says, so they must not excuse a loss` 与 `control S: a page's own older sentence must count as new words, or the bucket cannot tell a lag from a swallow`）——**这条判别式两头都有东西咬着**，不是一句讲道理的好话。

线上三条 `REVISION-BEHIND` 用 `git` 交叉验过，确认豁免的是**真滞后**而不是吞句：被豁免的那句 `推送后这一行重新回到 那才是收尾要盯的量` 在 `HEAD~1` 有、在 `HEAD` 无，而线上那份更新日志印的正是 `HEAD~1` 那一版。

**收尾条件从本轮起改定**：这条轴要 `MISS=0` **且** `REVISION-BEHIND=0`。以前 `NOTE` 一声就算过的「发布稿落后」现在是红的，只是红法不同（不进 `MISS`、退出码仍由它决定不了同步这一件事，归 `check_live_sync` 那条腿管）。

### 三、`##` 及更深层标题成为单元（控制 T）

先量地板再判，四个数全部是本轮从工作树现量：围栏与 frontmatter 之外的 H2+ 标题行 **2617** 条，其中 **661** 条过 14 归一字符地板，**584** 行至少产出一个单元（32 行因为被链接/代码切成两段所以产出两个），合起来 **634** 个标题单元；**77** 行过了地板却一个单元都不产——那是纯代码或纯链接的短标题，剥离后不足 14 字符。正文里的 `#` **永远不是**单元：第 55 轮量过平台会丢掉正文 H1、把 SUMMARY 标签当作读者看到的标题印出来，那条等式归 `check_nav_h1_sync.py` 管，这条轴不重复判。控制 T 一次钉三态：`##` 产出一个 `heading` 单元、正文 `#` 与围栏里演示的假标题都不产出、发布出去的 `<h2>` 判绿而删掉它必须**只**点名那一条标题。

### 四、`>` 引用块成为单元（控制 U）

本轮现场量到：围栏外 `>` 行 **42** 条、分布在 **32** 页，产出 `quote` 单元 **57** 个、分布在 **28** 页（一行可以产多个单元，也可以一个都不产）。图片行 `![…](…)` 仍然跳过：alt 文本不是正文，图本身是图片轴的对象。控制 U 同样钉三态（`>` 行产一个 `quote`、围栏里演示的假引用与 alt 不产、`<blockquote>` 判绿而删掉段落必须只点名那一条引用）。

全站首跑（新腿落地后、写本节之前的一次复跑）：

```text
prose survival: pages=196 units=13855 plain=11629 heading=634 quote=57 widget=1535 | all
lost sentences: MISS=3 REVISION-BEHIND=20 STALE-COPY=0 | pages-with-MISS=1 fetch-failures=0 not-listed=0
   README.md                                    MISS=3    behind=17   unpublished=0    of 576 units
   00-index/changelog.md                        MISS=0    behind=3    unpublished=0    of 3722 units
```

**691 条新单元（634 标题 + 57 引用）在读者眼前一条都不缺**——两条新腿首跑没有制造一条假红，也没有藏着一条真红。那 3 条 `MISS` 全在 `docs/README.md:95`，就是本轮改首页时**还没推上去**的字：首页没有轮次号历史，`published_cut()` 给不出切点，于是整页全量判，未同步的本地编辑自然读成丢失。这不是本轮的缺陷，是「同步前」的正常形状（第 87 轮同一位置报过 1 条，同步后归零）；`behind` 从 3 涨到 20 也是同一件事——首页那 17 条豁免，是发布稿在本轮改过的那一段里印着树中无处的旧措辞。**线上追上之后，这两个数都必须回落到 `MISS=0 REVISION-BEHIND=0`**，这一趟就是本轮的收尾断言。

上面那串是「本节写完之前」的一次真实复跑原样粘贴。本节与首页那两处改写落定之后，作者侧的同一串读 `pages=196 units=13923 plain=11691 heading=640 quote=57 widget=1535`——多出来的 7 个单元就是这两页自己的字，首页那句引用的正是这后一串，而**权威读数交给推送后的线上尾腿**（它同时跑 `check_live_sync` 与强调标记的 `--live` 腿）。

### 五、覆盖率对平闹钟：`homepage_parity()`（第 87 轮那条账的落地）

判据自己数出「`walk()` 覆盖几页」「我种了几条控制、是哪几个字母」，再读回首页引用它的那一句做比对：写错一个数、少一条控制、字母不连续、或者首页那句被删掉，都直接红。**这条闹钟本轮立刻兑现**：第四节把控制加到 21 条（A–U）之后，`--selftest` 第一件事就是把首页那句「20 条种植控制（A–T）」判红。四处反例各自咬过：从 `walk()` 里抽掉一页、从控制清单里抽掉一条、把字母清单换成不连续的 20 个、把首页那句的数字改成 193 / 11——四个都出声，恢复后基线读 `[]`。**局限写清楚**：它只对首页这一句，其他轴的首页句还没纳入；它管的是「视野与说法对平」，不是「视野够宽」。

### 六、顺手修掉的一条探测器可用性缺陷

`--mutate` 的页面参数与 `--page` 的口径不一致：前者拿用户给的字符串去比**绝对反斜杠路径**，后者比的是**相对正斜杠路径**——于是 `--mutate 00-index/changelog` 报「no page matches」，而同一个字符串在全站趟里正好选中那一页。本轮自己踩到（差点把「控制跑不起来」当成结论）。现在两侧同一口径，复跑读 `mutation control: hid '逐张记录来源' on 00-index/changelog.md and the judge named it a MISS, not a lag (217 chars)`。

### 七、本节自己的字被第 84 轮那条轴捉住两次，改在标记上而不是内容上

写完本节后跑作者腿，`check_emphasis_flanking.py` 读 `pages=1 leaked_strong_markers=2`——两处全在本节第一段：`的**「一条判据…」这件事本身没有对平轴**。` 这个写法里，开场的 `**` 前是汉字、后是中文引号，按 CommonMark 的 flanking 表**开不了对**，于是两个星号会原样印到读者眼前。修法只把标记挪进引号内侧（`「**一条判据扫了多少页**」`），一个字都没删，复跑读 `pages=0 leaked_strong_markers=0 lone_star_runs=1 (context only)`（那 1 处 lone `*` 是 URL 里的 `huggingface.co/*`，上下文而非判决）。**这一条值得记**：第 84 轮那条轴的动机正是「第 83 轮人眼看见、判据看不见」，本轮它第一次在提交前自己出声。

### 八、留下的账与下一步

① **活体变异控制只藏散文句**——标题与引用块的吞句由离线控制 T/U 证明，还没在真实发布页上藏过一条标题（藏 `<h2>` 要先处理它在目录副本里的同一串字，本轮没做，第 89 轮候选）。② **14 归一字符地板**对三条腿一律适用：短标题、短引用不判，77 条过地板却因链接/代码剥离而失格的标题尤其要记住。③ 第 87 轮记的 `UNWITNESSED` 重挂（把 witness 腿的未观测页改判成桶而不是名单）本轮**没做**，仍欠。④ `check_live_sync` 的落后判断没有因为本轮而变松：`REVISION-BEHIND` 只是不再冒充 `MISS`，滞后本身照旧由那条腿报。

### 九、收尾：线上追上之后，那三个数实测归零

`check_live_sync.py --watch` 以退出码 0 收工，两腿各读 `newest round=88`（`md` 313302 字节 / 144 轮，`html` 23902611 字节 / 512 轮），首页 witness 腿 `3/3 added needles live`。**尾腿**：

```text
prose survival: pages=196 units=13923 plain=11691 heading=640 quote=57 widget=1535 | all
lost sentences: MISS=0 REVISION-BEHIND=0 STALE-COPY=0 | pages-with-MISS=0 fetch-failures=0 not-listed=0
OK: every graded sentence reaches the reader
```

推送前那一趟的 `3/17/60` 全部归零，而 `units`、`plain`、`heading`、`quote` 四个数与推送前**一字不差**——本轮新长的 691 条标题与引用单元，在读者一侧既没报出一条假丢失，也没让一条真丢失藏在新增的覆盖面底下。强调标记的 `--live` 腿同趟读 `pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0`。

目检走**线上页**（第 82 轮的规矩：复制稿能测不能截图），三张真实渲染帧各盯本轮改动的一个对象：`00-index/README.md` 那条 `>` 引用以带左竖线的引用框到达读者眼前、句末的冒号也在；更新日志页「第 88 次」那一节的标题粗体生效、右侧目录把 §一–§五 列全；首页那一条 bullet 的加粗正常、没有裸星号。三页 `main` 里字面 `**` 的计数是首页 5 个（5 个都在代码跨度里）、更新日志 93 个（93 个都在代码跨度里）、导读页 0 个，也就是**代码跨度之外一个都没有**，与 `--live` 腿的 `served_markers=0` 各自独立对上。

这两趟目检先把**探针自己的两处错**量了出来，两处都改在探针上、内容一个字没动：① 拿判据的**归一化单元串**去在读者的 `innerText` 里做子串匹配——`norm` 把「——」与「，」折成空格，于是那条 `>` 单元永远匹配不上，第一条引用单元被误报成「没到读者眼前」；改成两侧都只留字母数字与汉字再比。② 数代码跨度里的 `**` 时用了 `main pre, main code`，`<pre>` 里那层 `<code>` 被数了两遍，「代码跨度之外」算出 **-8** 这个物理上不可能的数；只保留最外层节点之后才是 93/93。**如果没有那个负号，第 ② 处会被当成「读者眼前一个裸星号都没有」而直接记成一条绿**——记在这里，是因为这条轴第 83 轮的立轴理由就是「人眼发现了一次尺子的假绿」。

§八 那四条账一字未动。收尾之后首页与更新日志又有了新字，下一轮推送前那趟会再次看到 `REVISION-BEHIND>0`：那是 §八 ① 记下的机制在照章办事，不是这条轴回归。

## 2026-09-25（第 87 次）第 86 轮 §十 现场把 `check_prose_survival.walk()` 的 docstring 前提问倒了：「14-templates/ 不在发布站上」——三份文件全部 `status: published`、H1 都能在 `url_index()` 命中——也就是**载有判据规范的那一页本身，在完整性判据的眼皮底下**；同源第二处（`check_live_sync.head_reader_pages`）也在做同样的排除，第 86 轮主提交对 `style-guide.md` 的读者可见改动**从来没有被 witness 腿追过**

本轮正文 **0 页知识页改动**，只在两把尺子上各撤一处 dirpath 排除 + 各补一条「不许再把这一页装看不见」的控制（M / N），并把第 86 轮主提交的 `style-guide.md` 用新的 witness 腿当场追到 **3/3 needles live**；读者可见文字只动本页（新节 1 个 + 引用改写 2 处 + 第 86 轮标题 1 处）。**没有为过线删掉或加厚任何一页正文**：这条轴修的全是「尺子看不见」。

### 一、缺陷：一处 dirpath skip，两把尺子共用，同一句错前提

`check_prose_survival.walk()` 的旧 docstring 给这条排除的理由，逐字如下（`git show 0b02bf4:tools/checks/check_prose_survival.py` 里 `walk()` 的那三行，原文是英文，所以这里贴原文而不是译述——第 62 轮定下的规矩就是引用不许在「」里改写）：

```text
`14-templates/` is excluded for the same reason `live_aria_manifest.build` excludes it: those
files are authoring scaffolding and are not in the published site, so "the page has no
published address" is their correct shape, not a finding.
```

而**这段前提本轮现场测伪**：

```text
knowledge-template.md | h1: 知识点模板 | in index: True | status: published
resource-template.md  | h1: 资源模板   | in index: True | status: published
style-guide.md        | h1: 风格指南   | in index: True | status: published
```

三份文件都 `status: published`，H1 都命中 `live_aria_manifest.url_index()`（这个 index 就是从 `llms.txt` 建的，是权威地址表）——「页没有已发布地址」的形状**不是**它们的正确形状。也就是**载有「体裁硬下限表」+「强调标记规范」+「Mermaid 章色表」这三条硬要求定义的那一页，本身没被完整性判据扫过**。

同源第二处：`check_live_sync.head_reader_pages` 用 `and "14-templates" not in f` 把这条排除搬到了见证腿，也就是**第 86 轮主提交 `0236613` 里 `style-guide.md` 的读者可见改动从来没进过 witness 集合**——上一轮 §六第 2 条刚写下「尾腿集合必须覆盖自移动计数器」，同一份 docstring 里就藏着第二条「尾腿集合必须覆盖所有已发布页」的破口。

排除前提是从 `live_aria_manifest.build` 抄来的，那里它只是**省一次 fetch**（那个 walker 只保留带 widgets/formulas/mermaid 的页，模板页本来就落不进去）。完整性判据没有这个理由。

### 二、修法：两处 dirpath 排除各撤一行，各加一条控制

1. `check_prose_survival.walk()`：删掉 `if "14-templates" in dirpath: continue`，docstring 换成上面这段事实陈述——下一轮作者想再撤，会读到「为什么不该撤」。
2. `check_live_sync.head_reader_pages()`：把 `"14-templates" not in f` 从条件里摘掉，`00-index/changelog.md` 的排除保留（changelog 有它自己的两条腿，与本轮缺陷无关）。
3. **两处各补一条正向控制**（见 §三），钉住「覆盖不许静默缩回去」。

### 三、控制 M / N：一条一个 walker，跑过变异

`check_prose_survival.py --selftest` 原本 11 条控制全部围绕「切分/判绿/归因会不会漏判」，没有一条问过「扫到了没有」——那正是这类 bug 藏身的地方。控制 **M** 现读 `len([p for p in walk() if "14-templates" in p]) >= 3` 并且必须**包含 `style-guide.md` 本身**（不只数量够，还要具体那一页在）。

`check_live_sync.py --selftest` 的控制 **N** 从 `git log -1 --format=%H -- docs/14-templates/style-guide.md` 现场找最近一次改到规范页的修订（**不硬编码 rev**，不然下一次改这页它就失效），再要求 `head_reader_pages(that_rev)` 输出包含这条路径。

**变异验证**（一次一把尺子）：

| 变异（把判据改回原样） | 翻掉的控制 | 输出 |
|---|---|---|
| `walk()` 里把 dirpath skip 加回来 | 只翻 M | `control M: walk() must cover published 14-templates pages (>=3, incl. style-guide.md), got []` |
| `head_reader_pages()` 里把 `"14-templates" not in f` 加回来 | 只翻 N | `control N: head_reader_pages(0236613) must include docs/14-templates/style-guide.md, got ['docs/README.md']` |

两条各自独立、各只翻自己那一条，且 N 的输出**顺手指出第 86 轮主提交的 SHA**——上一轮那种「我改了规范页但尺子看不见」的失败模式，从此在 selftest 里就能看见。

### 四、首跑读数：视野从 193 页扩到 196 页，新覆盖的 3 页**恰好合规**

撤掉排除后 `check_prose_survival` 全站扫描：

```text
prose survival: pages=196 units=13038 plain=11503 widget=1535 | all
lost sentences: MISS=0 STALE-COPY=0 | pages-with-MISS=0 fetch-failures=0 not-listed=0
OK: every graded sentence reaches the reader
```

对比第 86 轮收尾的旧读数（`pages=193 units=12828`）：**+3 页 +210 units，MISS 仍为 0**。也就是说这三页此前**没有**任何读者拿不到的句子——但那是运气（作者写它们的时候手没有滑），不是「有判据在守」。撤回排除的价值是把「运气好」变成「量出来的没问题」，把「作者下轮把 style-guide 写坏」变成能被下一节 §六第 2 条那一类尾腿当场抓住的事。

`--page 14-templates` 单跑读数 `pages=3 units=182 plain=173 widget=9 MISS=0`，也就是 3 页里 9 个 widget 单元（`{% hint %}` 里那句「按下面模板写」的提示也到了读者手里）。

新覆盖的第 2 条腿（撤 `head_reader_pages` 排除）现场追一次第 86 轮主提交：

```text
witness ok  docs/14-templates/style-guide.md               3/3 added needles live
witness ok  docs/README.md                                 3/3 added needles live
witness: 2 reader page(s) HEAD~1 touched carry HEAD~1's added text
```

——上一轮那条「witness 只报 `README 3/3`」的绿灯，其实漏了同一次提交改的另一半。**本轮不再重跑 §六第 2 条那类尾腿**（`check_live_column` 的 argparse 坑与 `--page 14-templates` 的新探测是同一件事），只在 §六写清下一轮的尾腿要多带一条：witness 已覆盖到规范页，任何改动 `14-templates/*.md` 的那一轮都要现场看它的 3/3 是否兑现。

### 五、离线电池：判据各撤一行排除，读者可见文字只动本页，读数全部保持绿

| 判据 | 读数 |
|---|---|
| `check_structure.py` | `pages scanned=198 problems=0`；`mermaid=217 json=79 text=65 markdown=11 yaml=10 (no tag)=9`，可执行语言 0，79 份 json 契约全解析。`text` 从第 86 轮记录的 60 涨到 65 是**本节自己的围栏**加的 5 块（首跑读数与这一行同趟现场再量，§八 收尾又添一块），这条轴上只有 `executable-tagged=0` 与 `unclosed=0` 是钉死的等式，围栏清单按惯例只报数不锚数 |
| `check_emphasis_flanking.py` | `pages=0 leaked_strong_markers=0 lone_star_runs=1 (context only)` |
| `check_genre_floors.py` | `pages=196 published=196 graded=159 免检(不限)=37 不可判(同键高档)=40 \| problems=0` |
| `check_updated_dates.py` | `reader pages=198 checked=196 exempt=2 problems=0 pending-commit=0 unreadable=0` |
| `check_changelog_headings.py` | `HEAD=78 tree=79 lost=1`（`tree=79` 是新增第 87 次那一节；`lost=1` 是本轮按引用轴要求**改写**了第 86 轮的标题，旧那行在 HEAD 里、树里已删——这条腿对「重写一个轮标题」的预期读数就是 `lost=1`，提交后即归零） |
| `check_prose_survival --selftest` / `check_live_sync --selftest` | `controls: OK`（M / N 两条新控制各跑过变异） |
| `check_quote_fidelity.py`（上表初稿没有这条腿，收尾补跑） | 首跑 `attributed=23 verified=19 findings=2` → 两处引用改完 + 登记一条撤回后 `attributed=25 verified=23 findings=0`，`PROSE` 命中 11→14、`RETRACTED-OK` 7→8（详见本节末） |
| `check_prose_survival --page 00-index/changelog` | 首跑 `units=3420 MISS=0 STALE-COPY=85`（线上发布稿只证到第 242 行，以下全是本轮还没推出的文字，按第 84 轮的语义进 `STALE-COPY` 而不是绿）；§八 收尾那一节写完后同一条腿读 `units=3438 MISS=18 STALE-COPY=0`——**同一个数从 STALE-COPY 变成 MISS**，原因见 §六 最后一条。推送后的尾腿必须回到 MISS=0 |

**这一栏的数字是改过三处才读到的**，如实记下，因为三处都是本轮自己写下的：

1. `text` 围栏从第 86 轮记录的 60 涨到 **65**，差额就是本节自己那 5 块（用 `git show HEAD` 与工作树各数一遍 ` ```text ` 开场：8 → 13）。首跑我在这张表里写的是 60——那是把上一轮的快照当本轮读数抄了一遍，`check_structure.py` 现场再量才露馅。
2. 强调标记轴在 §六 那一行抓到 **1 个读者可见的裸 `**`**（`pages=1 leaked_strong_markers=1`）：`排除本轮**没动**：` 一行里三对星号，第二对把 `**` 卡在「轮」与「没」之间当闭合用了，第三对前面是汉字、后面是全角冒号，两侧条件都不成立，于是原样印到读者眼前。改成「**……排除，本轮没有动**：」——内容一字未动，只挪了标点和重音范围。这是第 84 轮那条轴**连续第二轮抓到当轮作者刚写下的字**（上一轮是 `style-guide.md` 里 1 页 2 枚，本轮是这里 1 页 1 枚）。修的是这一行的字面排版，判据一个字没动。
3. 第三件是**计数器自己挪**：本节往更新日志加字，`--page 00-index/changelog` 那条尾腿的 units 与 STALE-COPY 就跟着涨，上表这两个数是最后一趟现场重量的。第 86 轮 §七把「尾腿集合必须覆盖自移动计数器」写进规范之后，本轮第一次在**同一页内**撞上这条：被量的那页正是写这句话的那页。收尾提交前必须再读一次这两个数，而不是沿用本节初稿。

**另有两处不是数字，是引用轴出声的**——而 §五 上表本来就没列它，本轮收尾补跑才响：`check_quote_fidelity.py` 首跑读 `findings=2`（`attributed quotes=23 verified=19`）。两条都是「写着 + 「」」句式的引用，都不是本轮新写的正文，而是一把常驻尺子从没被要求跑过的那类缺陷：

1. §一 那句 `walk()` docstring 的引用是**中文译述**，而且被引物是 `tools/checks/` 里的 Python docstring——读者拿不到它，引用轴的词表（读者页正文 + 图内文字 + Mermaid 标签）天然查不到。改成围栏贴英文原文（`git show 0b02bf4:tools/checks/check_prose_survival.py` 现场取出那三行），中文解释放在围栏之后。这是第 71 轮「判据看不到出处就是缺陷」的同一类，只不过这次出处是仓库自己的代码。
2. 第 86 轮**那一节的标题**写着「按体裁设硬下限，不达标不得 `published`」，可规范第八节那里写着「不达标不得标 `published`」——多写了一截「按体裁设硬下限」、少打了一个「标」字。这正是第 62 轮定下的「不许在「」里改写」要抓的形状，标题改成原句之后轴绿。
3. 改完标题，本节引用那句**旧的错写法**就成了第 62 轮那一类：原句已从树里删掉，日志留它是为了记录这次删改，所以按规矩登记进 `check_quote_fidelity.py` 的 `RETRACTIONS`（`old` 必须全书再也找不到、`new` 必须在它指向的规范页里找得到，两边都判）。登记之后 `RETRACTED-OK` 从 7 涨到 8，`findings` 保持 0——**没有为了让它绿而放宽「原句必须可查」这条**。

第 2 条还顺带量出一条**覆盖缺口**（写进 §六 当第 88 轮候选）：`chunks()` 不把标题行当单位——现场测过，给一行 `## …` 加一句正文，返回的单位列表里只有那句正文。所以「改坏一个已发布轮的 H2 标题」这件事，线上正文完整性轴是**看不见**的；线上那一侧只有 `check_live_sync` 的轮次号腿会追它，而轮次号没变。本轮这一处标题改动的验证手段因此只有两条：离线引用轴（已绿）+ 下面那张真实渲染图。

### 六、留下的账 & 下一轮第一件事

- **`live_aria_manifest.build()` 里的 `14-templates` 排除，本轮没有动**：它现在只是省一次 fetch（模板页没有 widgets/formulas/mermaid），语义无害；但同一段代码里两条排除的**原因不同**，一条已经死了、另一条还活着，未来谁读到这里都可能一起删掉。第 88 轮把这条 docstring 与 §一 那段话对齐。
- **`UNWITNESSED` 桶的分桶仍未动**（第 86 轮 §八第 1 条留下的账）：`long-context-degradation.md` 那种「本轮只改 Mermaid 指令行颜色」的修订永远进不了 witness——本轮撤 `head_reader_pages` 排除让**这一类**（对模板页的修订）能进，但「没有可切片的中文散文」的那一类**仍需重分桶**。仍是第 88 轮。
- **新的一条覆盖缺口（§五 末力度量出来的）**：`check_prose_survival.chunks()` 不把标题行算作单位，所以「已发布轮的 H2 标题在线上缺一截 / 被人改坏」这类事它判不了，本轮改第 86 轮标题就是靠引用轴 + 渲染图两道验证。第 88 轮候选：标题进单位集合（要和 `check_nav_h1_sync`、`check_changelog_headings` 的口径对齐，别造出第二条重复腿），或明确写进规范「标题由哪条腿管」。
- **`published_cut()` 分不开「本轮稍后会推」与「平台吞了」**（§五 表格最后一行那次 STALE-COPY→MISS 的翻转就是它）：这条腿拿页面自己印的轮次号给发布稿定位，读者侧已经到第 87 轮时它返回 `None` 走全量判，于是收尾那一节 18 句还没上线的文字读成 `MISS=18` 而不是 `STALE-COPY`。语义上不算错（那 18 句读者此刻确实拿不到），但它和真正的吞句共用同一个格子，收尾时被量的数还会随写作进度翻脸。第 88 轮候选：让这条腿拿发布稿尾部与树逐句对，而不是只取轮次号；**不许**用「收尾别看这条腿」这种约定糊过去。
- **移交操作者未动**：`knowledge` 子体裁键、emoji 预算措辞、标题跳级 48/271/53、changelog 分页、图注两档合并、608 列宽 `COLUMN-MISMATCH`、未钉死的 Mermaid 文字变量、**GitHub PAT 撤销轮换**。
- **本轮的元教训**：`check_prose_survival` 从第 83 轮起被 README 当作「读者能不能拿到每一句」的**唯一**判据引用，而它一直有 3 页视而不见——**一个自称为「完整性」的判据，它「不完整」的那部分需要另一条正向控制来钉住，不能靠 docstring 讲道理**。第 88 轮候选：把「一条判据扫了多少页」这件事本身变成一条跨判据的覆盖率对平轴（比如 `walk 覆盖 == status:published 页集合`），任何一把尺子悄悄缩视野都响。

### 七、改动清单

`tools/checks/check_prose_survival.py`（`walk()` 排除撤回 + 控制 M）· `tools/checks/check_live_sync.py`（`head_reader_pages()` 排除撤回 + 控制 N）· 本页 1 节 + §六 那一行的强调标记位置 1 处（内容未动）+ 引用改写 2 处（§一 docstring 引用改成围栏贴原文；第 86 轮标题里那句规范引用改成原句「不达标不得标 `published`」）。首页统计本轮 0 改动：两条自移动计数器（`prose_units`、`link-graph relative`）现场再量仍与首页写的数一致，所以没有需要重新锚定的徽章。

### 八、收尾：撤回的排除在**线上**追一遍，新覆盖的 3 页第一次拿到 served 读数

主提交推上去只用一条判据定音：`git ls-remote refs/heads/main` 与本地 `HEAD` 逐字符相等（退出码不算证据）。之后本轮 Promise 过的尾腿逐条复跑：

```text
leg md   newest round=87  (306060 bytes, 143 rounds)
leg html newest round=87  (23548841 bytes, 508 rounds)
witness: HEAD added no reader-page text outside the changelog — the .md leg is the witness
prose survival: pages=196 units=13124 plain=11589 widget=1535 | all
lost sentences: MISS=0 STALE-COPY=0 | pages-with-MISS=0 fetch-failures=0 not-listed=0
prose survival: pages=3 units=182 plain=173 widget=9 | all      (--page 14-templates)
live leg: pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0
changelog headings: HEAD=79 tree=79 lost=0
```

逐条对上本轮的 Promise：

1. **`--page 14-templates` 那一行是本轮的全部目的**：这三页第一次拿到线上侧完整性读数，规范页的每一句都被证实到了读者手里。§四 那句首跑读数因此不再是本地断言。
2. **`units` 从 §四 的 13038 涨到 13124（+86）**，而 `STALE-COPY` 从 §五 记的 85 归零：§五 第 3 条说的自移动计数器**本轮第一次在线上闭环**——那 86 个单位就是本节自己那批当时还没上线的句子，推送后被发布稿追上，所以尾腿读到的是 `MISS=0 STALE-COPY=0` 而不是 85 条待同步。
3. **`changelog headings` 由 `lost=1` 归零**，与 §五 表格里预告的「提交后即归零」对平：这条腿对「改写一个轮标题」的预期读数就是 1，不是 0。
4. **首页两条自移动计数器复测未动**：`prose_units=7414`、`link-graph relative=1582`，与 `docs/README.md` 印的数逐位相同（`check_link_graph` 的 homepage claim 腿同时报 `pages=196 relative=1582 fragments=0 unchecked=0` 全等），所以 §七 那句首页 0 改动是复测出来的，不是沿用的。
5. **目检腿**：把本节 12–124 行在 900px 列宽里真渲一张 5337px 高的图（Edge headless，`--user-data-dir` 自带 profile），切四片逐片看——§一 的英文围栏渲成代码块且没溢出列宽、§三 变异表和 §五 电池表都没横向溢出、§六 改过标记的那一行粗体范围正确。数裸 `**` 的活没有手写计数器，而是把判据请回来代劳：对整段调 `check_emphasis_flanking.unpaired()` 读空集，再把那一行的标记挪回缺陷形状读 `LEAF-STRONG len=2 word/punct cannot pair`——一次渲图同时证「读者看到的是对的」和「这把尺子看得见错的」。

**本节自己也是移动计数器，而且翻脸比想象快**：这二十来行写完、还没推送时，`--page 00-index/changelog` 从 §五 记的 `MISS=0 STALE-COPY=85` 变成 `units=3438 MISS=18 STALE-COPY=0`——同一批「读者此刻拿不到」的文字，因为换了格子被换了一次名字（原因见 §六 倒数第二条）。收尾提交推上去、线上追上之后，同一条腿读 `MISS=0 STALE-COPY=0`，全站那条读 `pages=196 units=13149 MISS=0`（上面那块转录里的 13124 是主提交那一趟，差的 25 个单位就是本节自己；这三个数按本轮 §五 第 3 条的规矩各归各的趟，写下这一句的手同样在挪它们），`--page 14-templates` 仍是 `pages=3 units=182 MISS=0`。收尾要盯的自始至终只有 `MISS`。


## 2026-09-25（第 86 次）规范写着「不达标不得标 `published`」，而那张表 **5 行里 0 行**钉了 `type:` 键、`type: lab` 的 6 页连一行都没有：落库 `tools/checks/check_genre_floors.py`，首跑不报「0 问题」而报「尺子断了」，把表绑上键之后 196 页全受管

本轮正文动 **2 页**（`14-templates/style-guide.md`：第八节表格 + 第三节新增「实验型」体裁小节 + 口径后果一句），首页 1 条统计，判据 1 个新文件。**没有为过线删掉或加厚任何一页正文**：这条轴修的全是「规矩没法判」。

### 一、为什么开这条轴：全书唯一一条自称「硬性」的门槛，判它的那把尺子根本接不上书

计划书要求每轮覆盖「无图页/薄页（字数与信息密度）」。第 14/15 轮确实按字数增厚过薄页，但那之后的 70 轮里**没有常驻判据**——而 `docs/14-templates/style-guide.md` 第八节写的是硬要求：一张「体裁 → 正文中文字数下限」表，外加「**不达标不得标 `published`**，用 `draft` 或 `reviewing`」。

问题是这张表怎么落到页面上，规范自己没说。第 86 轮先量的就是这件事：**判据要按页找档，只能靠 frontmatter 的 `type`，而表里 5 行没有一行写着 `type` 键**——它写的是「原理型 / 概念型 / 实战型 / 资源卡片 / 索引/导航页」，那是作者口吻的体裁名，不是机器能对齐的字段。更糟的是全站实际在用四个 `type`（`knowledge`/`resource`/`index`/`lab`），而 `lab`（第 13 章那 6 个动手实验页）**在表里根本不存在**。也就是说：这条「硬性要求」当时既没法判、也没法满足，读者信任的那句「不达标不得发布」站在 196 页上，机器一个字都问不出来——第 76/77/78/79/84/85 轮同一类缺陷的第六次。

### 二、首跑读数：断尺要出声，不许读成「全书合格」

```text
genre-floor leg: GUIDE-BLIND 第八节那张表读到 5 行、其中 0 行钉了 `type:` 键（地板 4/3）——尺子断了，不许读成全书合格   (exit 2)
```

判据的规范来源就是读者能看到的那一页（与第 85 轮章色轴同一套架构：判据不自带规范，数字全部现场解析）。所以三种「尺子坏了」各自出声：那一节被删 → `GUIDE-BLIND`；行数读不满 4 或绑定读不满 3 → `GUIDE-BLIND`；`os.walk` 坏掉导致 published 页数低于 180 → `SCAN-BLIND`。这条轴的 `SCAN-BLIND` 是落库当场补的：写第一版时 `FLOOR_PAGES` 声明了却没用，于是一页都扫不到它也会印 `problems=0` 退 0——一个扫不到东西的判据最擅长的就是报绿，控制 J 现在专门钉这件事。

### 三、修法：把表钉到键上，再补上规范漏掉的第六个体裁

1. **6 行每行后面钉一个 `` `type: 键` ``**，判据只认这一处绑定，规范改动自然带动判据；同时把这行要求写进规范自己（「这张表就是判据的规范来源」），下一轮作者想改回散文写法会被这一节挡住。
2. **补上「实验型（`type: lab`）」这一行**，并且第三节也补了它缺失的体裁定义（`### E. 实验型`）：动机一句话 + 分步演示（stepper/tabs，正文不贴可执行代码）+ **真实运行记录** + 常见翻车。第 19 章那 6 页第 54 轮起就是这么写的，规范一直没记——**这是补记既有事实，不是新规矩**。
3. **那一档的下限 1200 是量出来的，不是画到线上**：6 篇 lab 页的正文中文字数是 1313 / 1324 / 1426 / 1480 / 1625 / 1766，最薄那篇（`19-labs/lab3-mcp.md`）距离 1200 还有 **113 字**余量。取 1200 的理由写在表里（一步跑得通的实验，正文要装得下动机、分步与真实记录，与原理型同档）。

修完的读数：

```text
genre-floor leg: pages=196 published=196 graded=159 免检(不限)=37 不可判(同键高档)=40 | problems=0
```

大白话：196 个读者页全部落到这张表底下——159 页真的在比字数，37 页是规范自己写「不限」的索引/导航页，另外 40 页是「过了最低档、但按它们名义所属的那一档还判不了」，这一格如实报数不当合格用（见下一节）。

### 四、口径的后果要先量一遍，别等它承重那天才发现

字数口径是「正文里的中文字符数」，**围栏块整块剔除**（一屏贴来的 JSON 是数据契约不是论证，算进字数等于允许贴图凑数）。这个选择今天承不承重？量了：

- 按本轮真正执行的三档地板（`knowledge` 600 / `resource` 150 / `lab` 1200），196 页里判决随「围栏算不算」翻转的是 **0 页**——所以它现在不是躲缺陷的出口；
- 但把规范里那档**执行不到**的原理型 1200 拿来硬判，会有 **12 页**从合格变不合格（正文 1138～1195、把围栏算进来则 1204～1307）。

这句话已经写进规范第八节：口径今天不承重，子体裁键落地那天它就承重，届时要重量而不是沿用本轮读数。落库前另做过一次「围栏整块剔除 vs 逐行剔除」的取法比对，本轮 0 页受影响，判据取整块（少一个状态机分支）。

`knowledge` 一个键同时套着原理/概念/实战三档，而 frontmatter 里没有字段能分开它们，所以判据按**最低那档 600 字**硬判——判据不替规范发明更严的线。要让 1200 那一档也可判，得先决定加不加子体裁键，这是元数据与版式的决定，移交操作者（见 §七）。

### 五、控制：10 条（8 条把尺子弄坏或把缺陷藏进去 + 2 条锚定「合规范本必须绿」），每条都真做过变异

`--selftest` 读数 `10 checks, 0 not caught`。光「控制全绿」不算证明，所以逐条把判据改坏，看是哪条控制响：

| 变异（把判据改坏的方式） | 翻掉的控制 | 判定 |
|---|---|---|
| M1 不再剔围栏（贴图凑字数放过去） | E | 只翻 E |
| M2 未绑定的 `type` 不再出声 | B | 只翻 B |
| M3 绑定地板降到 0（规范没绑也当合格） | D | 只翻 D |
| M4 不再只看 `published`（把 draft 这个合规出口判成缺陷） | F | 只翻 F |
| M5 取消「扫描断掉」报警（数不到页也报合格） | J | 只翻 J |
| M6 同键下界取最高档（判据替规范发明更严的线） | H、I | **翻了两条** |
| M7 缺 frontmatter 的页不再报 | G | 只翻 G |

M6 如实记：抬高地板不只让「同键取最低」那条锚点响，连「合规范本必须 0 问题」的锚点也一起红——因为把下界抬到 1200 之后，本轮那本只有 700 字的合规范本自己就不合格了。这不是控制写坏了，而是「把尺子调严」必然同时打掉两件事：既打掉「不替规范发明规则」，也打掉「合规范本绿」。第一版这里写成「只翻 I」的期望值，跑出来是 H+I，本轮没有改读数去迁就期望。

### 六、本轮离线电池当场抓到三件事，其中两条不是本轮写的

第 86 轮改的全是规范页与首页，所以收尾跑了一趟离线电池（19 条腿）。三处出声：

1. **强调标记轴抓到本轮自己写的新缺陷**：`14-templates/style-guide.md` 1 页 **2 个**读者可见的裸星号。原因是 §四那段写成了「按 `**最低那档（600）**` 硬判」——闭合那对星号紧跟全角 `）`，按 CommonMark 的 flanking 表右侧条件不成立，配对失败、两颗星原样印到读者眼前。改成「按最低那档（`**600 字**`）」，内容一个字没动。这是第 84 轮那条轴**第一次抓到当轮作者刚写下的字**，前几轮它抓的都是历史欠账。
2. **`link-graph` 的首页徽章在 HEAD 上就已经红了**：`HOMEPAGE-BADGE relative: homepage says 1578, tree reads 1581`（HEAD 快照实测），本轮加了一个站内链接后树读到 1582。同一趟 `check_prose_duplicates` 的自移动计数器也飘着：首页写 7377，HEAD 树里是 7393，工作区 7414。两条都是**第 85 轮收尾时没跑这两条腿**留下的：那一轮自己写的尾腿清单（散文物种、章色 `--live`、强调 `--live`、线上对平、日期、结构、首页统计）恰好不含「会随文档改动自己挪数」的那两条。本轮两处徽章重新锚定，并把「尾腿集合必须覆盖自移动计数器」记进 §七。
3. **字数地板这条轴自己是绿的**：`problems=0`，也就是第 14/15 轮之后这 70 轮里没有一页薄页偷偷发布——这是好消息，但也说明这条轴本轮的价值在**绑定缺口 + 回归护栏**，而不是当场清缺陷（不为凑缺陷去挪阈值）。

`--selftest` 之外，其余各腿读数：结构 `pages scanned=198 problems=0`（围栏 `mermaid=217 json=79 text=60 markdown=11 yaml=10` 无标签 9，可执行语言 0，79 份 json 契约全解析）· 导航标题 `problems=0` · 每章三件套 `chapters=18 goals=18 quizzes=17 questions=51 with_source=51 terms=198 findings=0` · 出处指针 `findings=0` · 繁简字 `findings=0` · 表格溢出 `spilling cells=0 tables=0` · 图注 `captions=215 caption=171 guided=46 findings=0` · 组件清单 `hint=257 stepper=54 step=279 tabs=52 tab=195` · KaTeX `pages=108 formulas=927 failures=0` · labs `labs=6 exit0=6 deterministic=6 records_current=6/6` · 章色 `blocks=217 contrast-pairs=868` 全桶 0 · 更新日志标题 `HEAD=77 tree=77 lost=0`。

### 七、先量后建判死的两条轴，和移交操作者的取舍

- **判死：Mermaid 图体颜色外泄**。想抓「指令行以外另设颜色」（`classDef ... fill:#fff` / 节点内联 `style` / `{fill:...}`）绕过章色轴。全站实测量到 **0 块**这么写——没有样本就不建判据（与第 74、85 轮同一条路）。
- **本轮不当缺陷修的：emoji 预算**。规范写「正文 0 个 emoji」，第一轮粗量报「139 页有 emoji」，这个数字**是错的**，重量按语境分桶之后：带 emoji 的地方 **576 处在列表项里，其中 571 处是行首的 ❌**——那是规范自己规定的「常见误区」写法；另有表格内 55 处、提示卡内 17 处；「散文」桶 22 处里有 21 处是 `SUMMARY.md` 的章节标题（规范第 47 行**明确豁免**它），只有 1 处是首页那个 👉 导航引导；全书 H2/H3 标题里只有 2 枚 emoji（⭐ 难度星，且都在规范自己那一页）。所以真缺陷不是「一堆 emoji 没清」，而是**规范那句「正文 0 个」和全书既成的 ❌/✅/⚠ 用法互相矛盾**——改成「误区与状态记号不算 emoji」还是把 571 处记号换掉，是产品级取舍，本轮 0 改，移交操作者。
- 连同第 85 轮已移交的标题跳级（48 处 h2→h4 / 271 个步骤标题 / 53 页）、608 列宽那条 `COLUMN-MISMATCH`、宽栏开关、图注两档合并、更新日志分页（线上 HTML 那一页 21 MB、多轮滞后）、`knowledge` 子体裁键，一并等操作者定夺。另有一件仓库外的事仍未动：**早前贴在聊天里的 GitHub PAT 需要撤销轮换**。

### 八、留下的账

- **第 85 轮的线上尾腿仍未走完**：`.md` 腿已读到第 85 次（282,918 B / 139 条），**线上 HTML 那一页停在 84**（21,460,674 B），轮询 90 分钟没有追上；而本轮又往同一页加了字。witness 腿另报一条 `UNWITNESSED docs/06-memory-rag/long-context-degradation.md`——第 85 轮那一处只动了 Mermaid 指令行的颜色（frontmatter 之外的读者页正文里没有新增可切片的中文散文），按第 84 轮定的语义「判不了 ≠ 已同步」，所以它进 `UNWITNESSED` 而不是绿。这条桶本轮**没有**动判据（正被轮询的尺子不在跑的时候改），列为第 87 轮第一件事：把「本轮没有读者可见新增」与「追不到文本」分成两桶。
- 只受 ≥4.5:1 底线管的 Mermaid 文字变量（`actorTextColor`/`noteTextColor`/`tertiaryColor`/`signalColor`）仍未进规范——第 85 轮的同一条账，未动。
- 判据只判字数这一维。「薄页」的信息密度（有无公式、有无图、有无步骤）另由别的腿管，`check_genre_floors` 不越界，也不承诺判第三节那些体裁小节「该有哪几段」——那需要小节级判据，下一轮候选。

### 九、改动清单

`tools/checks/check_genre_floors.py`（新增，10 条控制 + 7 条变异验证）· `docs/14-templates/style-guide.md`（§三 新增「实验型」体裁小节；§八 表格 6 行绑定 `type` 键 + 新增实验型一行 + 「本节即判据的规范来源」+ 口径后果；强调标记位置 1 处）· `docs/README.md`（新增 1 条统计；`link-graph` 与 `prose_units` 两处自移动计数器重新锚定）· 本页 1 节。

### 十、收尾（主提交 `0236613` 之后：把 §六第 1 条那处 L75 缺陷改掉 + 把这条误修的路钉在判据里 + 走完第 85 轮尾腿）

**第 85 轮的线上尾腿已追平**（task 收尾清单里挂了两轮的那三条）：`check_live_sync` 现场读到 `leg md newest round=86 (290456 bytes, 141 rounds)` 与 `leg html newest round=86 (22584246 bytes, 500 rounds)`，两腿都在 86；`witness ok docs/README.md 3/3 added needles live`——首页本轮新写的三句都到了读者手里。§八第 1 条的 `UNWITNESSED docs/06-memory-rag/long-context-degradation.md (HEAD~1 added no sliceable text there)` 本轮按承诺**未动尺子**（`--rev HEAD~1` 复测仍在，因为第 85 轮那处真的只改了 Mermaid 指令行颜色），列为第 87 轮第一件事。

**§六第 1 条那处的修法只算了一半**：本轮把 §四的强调标记位置改了，但 `check_prose_survival --page 00-index/changelog` 在**已推的 HEAD** 上仍读到 `units=3304 MISS=1 STALE-COPY=0`——被点名的单元是 §六第 1 条尾部「这是第 84 轮那条轴**第一次抓到当轮作者刚写下的字**，前几轮…」。原因不在这一句，而在同一行前半段那两处把 `**…**` 当示例写的字面量：它们各自让 GitBook 的水合把 `<strong>` 边界挪了一次，第二段挪到了这句正常写法的 `**…**` 两侧，把它该带的空格吃掉了。**修法**是把那两处字面量放进行内代码（`` `**…**` ``）让星号以字面样子给读者，内容一字未改；后半段这一句的正确写法**保留原样**，因为它本来就是合规的。

**这次差点把尺子改错**：我先入为主以为 `MISS=1` 是判据假阳——理由是 `served_chunks` 把标签替成空格，看着像「作者写 bold、页面正常渲染 → 两侧应带空格」——于是动手在 `chunks()` 里把成对的 `**` 从切分单元里删了。**A/B 一跑，同一页 `MISS` 从 1 涨到几百量级**（准确数字已经写进控制 L 的注释里，本轮不再重跑变异）——因为 `<strong>x</strong>` 被替成 ` x ` 是判据**正确**的模型，删掉 `**` 会让所有中段子句系统性假阴。这条「把真 MISS 当假阳 → 修尺子 → 制造假绿」正是 §七那类老账的镜像版本；`check_prose_survival.py` 控制 L 从此钉住它：`a bold run the platform opened somewhere else must stay a MISS, not be paid for by deleting markers`。判据回退到 HEAD 状态（`git diff --stat` 只剩 +18 行的控制 L），`--selftest` 现读 `controls: OK, every bucket able to fire`。

**§八目检补记**：本轮唯一读者可见的新表在 §八（emoji 计数分桶）。真实渲染截图在临时目录 `sec8.png`（194,741 B，1280×1000），目检过：5 行都完整可读、列宽没把中文挤到错位。附带一条**平台事实**：GitBook 水合后的 DOM 里 `document.querySelectorAll('table').length === 0`（表格渲染成 div grid），而 SSR HTML 里确有 `<table>`——未来的浏览器端表格判据不能选 `table`。

**本段提交前的最后一趟离线电池**（全绿；数字全部本段现场再量）：

| 判据 | 读数 |
|---|---|
| `check_structure.py` | `pages scanned=198 problems=0`；围栏 `mermaid=217 json=79 text=60 markdown=11 yaml=10 (no tag)=9`，可执行语言 0，79 份 json 契约全解析 |
| `check_emphasis_flanking.py` | `pages=0 leaked_strong_markers=0 lone_star_runs=1 (context only)` |
| `check_genre_floors.py` | `pages=196 published=196 graded=159 免检(不限)=37 不可判(同键高档)=40 \| problems=0` |
| `check_updated_dates.py` | `reader pages=198 checked=196 exempt=2 problems=0 pending-commit=0 unreadable=0` |
| `check_changelog_headings.py` | `HEAD=78 tree=78 lost=0` |
| `check_prose_duplicates.py` | `pages=191 prose_units=7414 formula_units=274 dup=0 near-band=3` |
| `check_link_graph.py` | `pages=196 relative=1582 distinct=717 ok=702 blocked=14 net=1 unchecked=0 / FAILED: 0` |
| `check_content_overflow.py` | 768 与 608 双扫：两档 `bar=16px drag -> 0 formulas to fix`；608 唯一 `over-column=1` 是 `03-llm/rlhf-dpo-alignment.md`（nat=620.28 drag=12px，在 16px 底线以内） |
| `check_live_sync.py` | 上面第 1 段三条腿 |
| `check_prose_survival.py --page 00-index/changelog` | 对旧 HEAD 的线上页判：`MISS=1`（就是这一处），本段推送之后要读到 `MISS=0` |

两条自移动计数器（`prose_units=7414`、`link-graph relative=1582`）**未飘**，因此本段不再重锚首页两处徽章——这也是 §六第 2 条落进规范里那条「尾腿集合必须覆盖自移动计数器」的第一次回归使用。

**推送后的尾腿（本轮完成条件）**：`prose_survival --page 00-index/changelog` 读到 `MISS=0`、`emphasis_flanking --live`（作者侧刚过 0，线上追平后应为 0）、`live_sync` witness 对新 HEAD。

**发现的判据缺口（第 87 轮候选，本轮未修）**：`check_prose_survival.walk()` 的 docstring 声明「`14-templates/` 里的文件是作者脚手架，不在发布站上」——**这条前提刚被现场测伪**：目录三份文件全部 `status: published`，H1 均在 `live_aria_manifest.url_index()` 命中；`--page 14-templates/style-guide` 读到 `pages=0 units=0`。也就是说载有「体裁硬下限表」与「强调标记规范」的这一页本身**没有**完整性判据在守。与 §八第 1 条（UNWITNESSED 分桶）一起列第 87 轮前两件。


## 2026-09-25（第 85 次）「全书 217 张 Mermaid 都带章色」这句话由谁来复核？此前是**一个人、一次、2026-09-22**——落库 `tools/checks/check_mermaid_palette.py`（判据的规范来源就是读者看到的那一页），首趟量出 **1 页 4 组 1.00–1.19:1 的白底白字**，只改 4 个颜色字面量后 **0**

本轮正文动 **1 页 4 个颜色字面量**（图的节点、连线、文案一个字没改），规范 1 段，首页 1 条统计，判据 1 个新文件。

### 一、为什么开这条轴：一条硬性要求站了 5 轮，复核手段是「有人看过一次」

`docs/14-templates/style-guide.md`「Mermaid 章色配色（硬性要求）」写了三件事：每块第一行必须是 `%%{init: ...}%%`、取所在章主色、掺白比例固定。首页也印着「217 个 Mermaid 内联图（全部带章节配色）」。而 84 轮里 Mermaid 有几何轴（宽/高/字号）、有图注轴、有解析轴，**没有一根尺子问过颜色**——那句「217/217 块带指令，0 块缺失」在规范里明写着自己的量测日期（2026-09-22 手工复核），是第 76/77/78/79/84 轮同一类缺陷的第五次：一句读者会照着信任的话，机器无法证伪。

第 85 轮的判据把这三件事拆成八桶（`MISS`/`UNPARSE`/`THEME`/`NOCHAPTER`/`WRONGBASE`/`FORMULA`/`TEXTCOLOR`/`CONTRAST`），并且**判据不自带规范**：色表、掺白比例、`primaryTextColor` 的字面值全部现场解析自 `style-guide.md` 那一节。规范改了判据跟着改；那一节被删掉或读不出表，判据报 `GUIDE-RULES`「这是尺子断了，不是全书合格」并 `exit 2`。掺白公式先复现规范自己给的那行 02 章示例（`SELF-ANCHOR`，复现不了就不出数），再拿去量全书。全站读数：

```text
mermaid palette: blocks=217 chapters=21 formula=lineColor45%,primaryColor90%,secondaryColor78% ink=#1F2937 contrast-pairs=868 | MISS=0 UNPARSE=0 THEME=0 NOCHAPTER=0 WRONGBASE=0 FORMULA=0 TEXTCOLOR=0 CONTRAST=0
```

也就是说「217/217 带指令」「逐块取所在章主色」「三档掺白对平」这三句从今天起**可复跑**，而不是某人某天的眼睛。

### 二、比字符串更硬的一条：读者能不能看见

配色全对不等于标签读得出来。判据另算 **868 组**「标签色压在它所在底板上」的 WCAG 对比度（4 组配对：`primaryTextColor`×`primaryColor`/`tertiaryColor`、`actorTextColor`×`actorBkg`、`noteTextColor`×`noteBkgColor`），地板 **4.5:1**——沿用自绘图那根轴的小字档（Mermaid 默认节点标签 16px）。

**首趟就是被这条抓出来的**：[长上下文退化与有效上下文窗口](../06-memory-rag/long-context-degradation.md) 那张漏斗图把三个文字变量都设成了本章最浅的一级掺白 `#F5FBF9`，量到 4 组 **1.00 / 1.05 / 1.07 / 1.19:1**（其余 864 组最低 **10.84:1**，所以这不是分布尾部，是白底白字）。线上证据（推送前重量一遍，不抄笔记）：读者那一份 HTML 长 1,212,746 字节，里面 `F5FBF9` 出现 **4** 次、`1F2937` 出现 **0** 次——浅墨确实发到了读者手上。

### 三、修法与断言级验证：只动颜色，前后各真渲染一张

改的是 4 个颜色字面量（`primaryTextColor`/`actorTextColor`/`noteTextColor` → 房规墨色 `#1F2937`），**图与正文一个字没动**。验证不靠字符串对比：同一份漏斗图源（节点、边、文案完全相同）用与线上同版本的引擎真渲染两张 PNG——

| | 自然尺寸 | 落地的墨色像素（相对亮度 <0.15） | 判据读数 |
|---|---|---|---|
| 修复前（HEAD 那一版指令） | 358.5×894px | **0** | `TEXTCOLOR=1 CONTRAST=4` |
| 修复后（工作树） | 358.5×894px | **4457**（近黑 3089） | 全桶 0 |

自然尺寸相等 ⇒ 版式没动；墨色像素 0 → 4457 ⇒ 读者从「看不见标签」变成「看得见」。两张截图逐张目检过：修复前那张只有绿框轮廓，八个节点的中文全部糊成底板色。

### 四、控制：10 条（8 种种植缺陷 + 2 条锚点），落库时这把尺子错过三次

`--selftest` 读数 `mermaid palette controls: 10 checks, 0 not caught`。两条锚点：**修好的真块必须判绿**（正控制，防「判据谁都报缺陷」）、**公式必须逐字符复现规范自己给的示例行**。八种种植里两条是分工边界：`#374151`（可读但不规范）只许报 `TEXTCOLOR`、不许报 `CONTRAST`——否则一次措辞制造两条噪声；`#F5FBF9`（重演本轮真缺陷）必须**双报**，钉住「规范字面值」与「读者看得见」是两件事。另外「拿别章主色」归 `WRONGBASE`、「掺白差一档」归 `FORMULA`、「章不在色表里」归 `NOCHAPTER`，各桶不许互相顶。

三次错全改在尺子上，没有一次改内容：

1. **`%%{init:` 写进 `%` 格式化字符串**会被吃掉一个百分号，种出来的指令行少一个 `%`，于是 5 条控制全部撞进 `MISS` 而不是各自的桶——第一趟的 `5 not caught` 就是这个。改成字符串拼接。
2. **Python 的 `round()` 是「四舍六入五成双」，而全书 217 块用的是半进位**。口径不对时同一棵树凭空多出 **94 个** `OFF_BY_ONE` 假阳性（本轮重量确认：拿 `round()` 复算，94 处与 `mix()` 结果不同）。判一个规范没定义的取整口径，等于把 94 张干净的图报成缺陷。
3. **表格单元格正则把下一格的 `|` 一起吃掉**，色表读不全。现在收在 lookahead 上（`(?=\||$)`），读出 21 章；这一条的兜底是 `FLOOR_CHAPTERS=20`——**读不满就报「尺子断了」，不许读成「全书合格」**，所以哪怕下次换个姿势读歪，它也是出声的失败。

### 五、移交操作者的产品级取舍：标题跳级（本轮先量完，未修）

本轮原计划做「标题层级跳级」轴，量完发现它不是判据问题而是版式决定，记在这里请操作者定：全书 **48 处 h2→h4 跳级**，涉及 **271 个步骤标题 / 53 页**（章末自测清单与分步演示的小标题）。平台腿已验证：GitBook 把作者写的层级 **1:1** 带进 DOM（线上量到 `<h4>` 确实是 h4，另有一枚前导空 `<h5>` 是平台自己加的），所以跳级会真的进读者的辅助技术大纲。唯一的 Markdown 修法是 h4→h3，代价是 **271 个标题的渲染尺寸同时改变**——这是改版式，不是修缺陷，本轮 0 改。也因此这条轴**没有落库**：一条只能靠「全书重排标题」才能变绿的判据，落库等于替操作者预先批准那次重排。

同一趟顺手判死的候选：**「让读者去看第 X 章」却不给链接**的指针轴。扫全站只命中 3 处 `「X」` 形状，逐条读下来全是引号里的术语名而不是章节指针，样本不存在，轴不做（与第 74 轮引用覆盖率分解同一条路：先量再建，量不到样本就不建判据）。

### 六、留下的账

- `--live` 腿是**抽样**（`--live N`），不是穷尽 196 页。这条原本是写错的：它自称核对的是指令行**逐字**出现在读者页面上，而**逐字**这个前提根本不成立——推送后第一次真跑，6 页全部报 `DIRECTIVE-AWOL`，其中 **5 页本轮压根没碰过**，所以那是尺子的病不是书的病。归因量过：读者页面不打印那一行，而是把它嵌在编辑器文档的 JSON 里，引号全部带反斜杠转义（原页面实测 `"text":"%%{init: {\"theme\":\"base\",…`），任何原样子串比对都不可能命中。修在尺子上：比对前先剥转义反斜杠，并补两条**反向**控制钉住「命中」是有判别力的（把一处章色换成全书没用过的 `#0E0E0E` 得到的幽灵指令必须不命中；别页的指令行必须不命中）。控制从 10 条加到 **13 条**，三条新控制各自做过变异验证：把剥转义改回原样 → L 响；把幽灵色换成本页真实色（幽灵==原文）→ M 响；负样本集合不再去掉自身 → N 响；未变异的基线 `13 checks, 0 not caught`。还加了一条 `LIVE-BLIND`：抽样里一条都没命中就退出 2 并说明「要么没同步要么尺子坏了」，**不许读成内容通过**——上一版的失败模式正是把「判不了」印成 6 条内容缺陷。修完复跑 `--live 6`：`pages=6 directives-checked=6 hit=6 fetch-blind=0 problems=0`，样本第一页就是本轮修过的 `06-memory-rag/long-context-degradation.md`，也就是**修复后的那行颜色确实到了读者手里**（比对对象是工作区当前那一行，旧版页面不可能命中它）。
- 规范只钉了 `primaryTextColor` 一个文字变量，`actorTextColor`/`noteTextColor`/`tertiaryColor`/`signalColor` 等键**没有掺白比例可判**——判据不替规范发明规则，这些键只受 ≥4.5:1 那条底线管着。要不要把它们也写进规范，是下一轮的内容决定。
- 对比度腿算的是**作者写的颜色字面量**与 Mermaid 默认 16px 小字档；若某张图显式设了 `fontSize`/大字标签，本轴不会知道（全站当前 0 处显式字号，是盲区不是缺陷）。
- 第 84 轮 §十 的尾巴**没有**在本轮开始时就已经到齐：`check_live_sync` 两腿各读 `newest round=84`、witness 腿 `docs/README.md 3/3 added needles live`，强调轴 `--live` 腿读 `pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0`，这三条都过了；但散文轴仍报更新日志 **32 句**没到读者眼前（`MISS=32 STALE-COPY=0`，前一晚盯 §十 那个小标题原文的轮询也读 `False`）。也就是说线上那份更新日志停在第 84 次的**前半截**——`round=84` 这个标题在场并不等于整节都发出去了，「同步」不能只按标题判定。本轮推送后与第 85 次一起复跑，记在收尾那一节。

### 七、日期轴当场又抓到 7 条 BEHIND：第 84 轮修完正文没告诉读者

`check_updated_dates.py` 是第 75 轮落的判据，当时它预言「第 17 轮手工回填过 80 个失真日期，没判据六个轮次就攒出 17 个」。本轮首跑读到 **7 条 BEHIND**：**6 条是第 84 轮的尾巴**（`01/machine-learning-basics`、`05/browser-code-filesystem-tools`、`06/text-to-sql`、`07/error-recovery-retry`、`07/tool-selection-routing`、`11/agent-failure-playbook`——那一轮挪过这些页的加粗标记，`updated:` 一个字没动，读者看到的仍是 09-22/09-23），第 7 条是本轮自己改的 `14-templates/style-guide.md`。`--fix` 一次写回 → `problems=7 → 0`，`git diff --numstat` 逐页恰好 1/1（**七页正文一个字没动**，脚本自己拦住任何 1/1 之外的页）。这条轴又一次证明它值得常驻：上一轮的收尾把这条漏了过去，而漏的方式正是「改了正文、忘了告诉读者」。

**同一轮推送后又抓到第 8 条，而这条更值得记**：本轮自己修过颜色的 `06-memory-rag/long-context-degradation.md` 仍写着 `updated: 2026-09-22`。首跑没报它，是因为这条轴读的是**提交日期**，而当时那一处还躺在工作区里（轴把它记进 `pending-commit` 桶而不是缺陷桶——一个还没提交的改动谈不上骗读者）。提交之后重跑，`problems=1`：正文今天动了、页面向读者宣布的却是三天前。`--fix` 后 `1 → 0`，`git diff --numstat` 仍是恰好 1/1。**口径因此要说全**：`--fix` 在提交前跑一遍不够，同一轮至少还要在提交后复跑一遍，否则本轮改过的那一页会带着旧日期上线。

### 八、改动清单

正文 1 页（`06-memory-rag/long-context-degradation.md`，4 个颜色字面量）· 规范 1 页（`14-templates/style-guide.md` 那一节改成「本节即判据的规范来源」+ 对比度底线）· 首页 1 条统计（`docs/README.md`）· 判据 1 个新文件（`tools/checks/check_mermaid_palette.py`，含 `--selftest` 与 `--live`）· 日期 7 页各 1 行（其中 6 页是第 84 轮欠的账）。

## 2026-09-25（第 84 次）第 83 轮的收尾截图里读者看见了字面星号——「加粗标记到没到读者手里」这条从来没有判据：落库 `tools/checks/check_emphasis_flanking.py`（两腿 + 一把第三方参照尺），首趟量出 **9 页 24 个**，按 CommonMark 外翻规则逐处只挪标记后 **0**

本轮正文动 **9 个文件 13 处**，全部是 Markdown 标记的位置，**内容一个字没删**；判据 1 个新文件。

### 一、缺陷是眼睛看见的，不是轴量出来的

第 83 轮收尾那次真实渲染目检（`--print-to-pdf` 562,407 B → PyMuPDF 首页 PNG）里，`hallucination.md` 那一页印着：

```text
这与 RAG 评估里的**忠实度（Faithfulness）**是同一思想。
```

同一页的线上原始 HTML 更直接（`r83_leak` 那趟的 repr，未加工）：`<p class="paragraph …">这与 RAG 评估里的**忠实度（Faithfulness）**是同一思想。</p>`——**两颗星号原样在读者眼前**，而第 83 轮那条轴对这一页的读数是 `units=36 MISS=0`。
**它看不见不是巧合，是尺子的性质**：`norm` 把 `*` 归一成空格，两侧同一套归一化，于是「渲染成粗体」和「星号外翻」在散文轴里长得一模一样。散文轴判的是**字到没到**，星号本身不在它的对象里。上一轮留下的那条账（「没有 `<strong>` 覆盖范围的常驻轴」）就是这个缺口的名字。

### 二、判据：CommonMark 的 flanking 表，两腿跑

一条 `**` 只有同时满足左右两侧的条件才能配对（`unicodedata` 的 `P*` 类算标点，全角 `（）「」：。，` 全在内）：

- **能开（left-flanking）**：后一个字符不是空白，且「后一个不是标点 **或** 前一个是空白/标点/行首」；
- **能闭（right-flanking）**：前一个字符不是空白，且「前一个不是标点 **或** 后一个是空白/标点/行尾」。

`*` 与 `**` 用这张表；`_` 的「词内不算边界」附加条件**不适用**（第 83 轮 v1 就是误用了它，量出 3911 条假外翻）。也不管 3 个以上星号——那是另一套语义。

命中形状全是这本书里真实出现的三种：

| 形状 | 例（修复前） | 为什么配不上 |
|---|---|---|
| 闭合侧落在全角 `）` 后、紧贴汉字 | `**忠实度（Faithfulness）**是` | 前一个 `）` 是标点、后一个 `是` 是词 → 既不能闭也不能开 |
| 开启侧卡在汉字与 `「` 之间 | `都是**「有副作用…」的工具**：` | 后一个 `「` 是标点、前一个是词 → 开不了 |
| 闭合侧落在 `。` 之后 | `…再说。**第 54 轮…` | 同一个「既不能闭」的坑，只是发生在句中 |

**两条腿**：作者腿离线预测每页会外翻几个（不联网）；`--live` 腿把每页**预测数**与线上 `body_visible` → `html.unescape` 之后数出来的字面 `**` 逐个对平——**平台才是最终裁判**，预测只是让下一轮能离线复现。被判红的是三桶：`MISMATCH`（预测≠线上）、`NOT-LISTED`（作者侧脏但页面不在站点索引里， served 无从对质）、`FETCH`（没取到页，算未判）。首趟读数：

```text
emphasis flanking: pages=9 leaked_strong_markers=24 lone_star_runs=…
live leg: pages=196 fetch-failures=0 prediction-mismatch=1 served_markers=25
   MISMATCH 00-index/changelog.md author=8 served=9
```

### 三、先证尺子不是新错：第三方参照 + 两处尺子自身的错

外翻是我推的规则，所以第一版判据落库前先按第 82 轮的规矩**锚在参照物上**：本机有 `markdown-it-py 2.2.0`（CommonMark 的另一个独立实现）。拿它当参照，对全书 196 个作者页统计「渲染后仍留在 text 节点里的字面 `**`」——

- **修复前**（对 HEAD 的更新日志原件跑，不是对空树）：`predictor=8 reference=8`，两边都抓得到；
- **修复后**（对当前树跑全站）：`leaked_markers=0 predictor=0 pages=0`，`predictor and reference agree on every authored page`。

同一趟还揪出两处**判据自己的**错，都不是靠调阈值糊过去的：

1. **打印被截断**：每页只印前 3 条，于是更新日志 8 条里 **5 条从来没印出来过**。改成每条 `**` 外翻都点名（`* ` 落单星号仍只作上下文），因为「判据抓到了但不告诉你在哪一行」等于没抓。
2. **退出码挂错对象**：`lone-*` 计数原先参与 `exit 1`。量开之后 23 条里 **22 条是 `* ` 开头的列表标记**（CommonMark 把它变成 `<li>`，星号根本不到读者眼前），另 1 条是 `huggingface.co/*` 这种 glob。所以列表标记在分词阶段就被跳过，**只有 `**` 外翻决定退出码**——否则这条轴永远不可能绿，而一条永远红的轴下一轮就会被人当噪声。
3. 代码/公式/链接标签必须替换成一个**词**（`ATOM = "文"`）而不是空格：留空格时 38 页预测 300 个标记、线上只有 25，277 个是假阳性；换成词占位后 196 页逐页等式成立。控制项常驻：`bolded-inline-code`、`bolded-link-label`、`math-multiplication-star` 三条必须不报。
4. `--selftest` 12 条种植控制（本轮加第 12 条 `list-bullet-asterisk`：`* 一条列表项\n* 另一条带 **合法粗体** 的项` 必须 0）：`controls: OK, every bucket able to fire`。

### 四、13 处修复：只挪标记，不删内容

**8 个读者页**（每页 2 个标记，作者预测与线上 served 全部相等）：`machine-learning-basics.md:48`、`browser-code-filesystem-tools.md:164`、`text-to-sql.md:26`、`error-recovery-retry.md:56`、`tool-selection-routing.md:72`、`hallucination.md:58`、`agent-failure-playbook.md:56`、`style-guide.md:138`；更新日志 4 处（L691 那颗多余空格 `** carried` → `**carried`；L1866、L2046、L2094）。加上 §五 那条组件嵌加粗（L2108）就是 **8 + 4 + 1 = 13 处**——它不在 flanking 命中里，所以那 24 个标记不含它。改法只有三种，**没有一处删字**：

- **把 `**` 收到括号/引号内侧**：`**忠实度（Faithfulness）**是` → `**忠实度**（Faithfulness）是`；`小节统一叫**「参考资料」**` → `小节统一叫「**参考资料**」`。
- **把 `**` 挪过一个词**：`定义**「完成」的可验证定义**与` → `定义「完成」的**可验证定义**与`。
- **补一个全角标点让边界成立**：`落点是**「重试 5 次」…**。` → `落点是：**「重试 5 次」…**。`（`所以，**「…」函数**——`、`其中，**「…」最关键**，` 同）。

断言级验证：作者腿 `leaked_strong_markers` **24 → 0**（`pages=0`），参照尺 0，`--selftest` 仍 `OK`；同时全站复跑 12 条常驻轴，`check_structure problems=0`、`executable-tagged=0`、`unclosed=0`、无标签 `9 → 9`、mermaid/json/markdown/yaml 四类标签逐字未动（`217/79/11/10`）——**唯一变动的是 `text`：52 → 55，多的三个就是本节自己贴读数用的围栏**（新围栏一律打 `text`，所以无标签那条不变）。导航/组件/引用/近重复/链接图/章末三件套/图注/出处/繁简/labs 全部 `findings=0`。

### 五、那 1 处平台与 CommonMark 不一致，是等式腿抓的

`author=8 served=9`：多出来那颗在更新日志 L2192。那一行的写法是「结论：」后开加粗，加粗范围里先塞进一个 hint 组件的行内示例，再接「不是缺陷」与闭合标记——**加粗范围里嵌进一个 GitBook 组件写法时，平台吃掉了开场标记，把闭合标记原样留给读者**。这条不在任何 CommonMark 模型里，所以它只能由「作者预测 == 线上实数」这条等式抓；如果 live 腿只判「线上 > 0」，它会永远隐形。

修法同样是挪标记：现在那一行只有「不是缺陷」四个字在加粗里，组件示例落在加粗之外。**没有**把这条做成判据：机制只有 n=1，而我那把粗扫的正则在一行里有第三个 `**` 时会跨对误配（扫出 22 处，多数是这种假配）。它记在留下的账里，等式腿本身负责兜住下一例。

### 六、线上复验：写这段之前的读数，以及同步后要断言什么

同步前（工作树已修，平台还是旧的）跑第 83 轮那条散文轴：

```text
prose survival: pages=193 units=12483 plain=10957 widget=1526 | MISS=1 STALE-COPY=311
   11-engineering/agent-failure-playbook.md  MISS=1  of 51 units
       PLAIN:56 对策 任务开始前定义 完成 的 可验证定义 与最大预算
```

**唯一那条 MISS 已逐条归因，且不是「轴坏了」**：它是本轮自己改的那一行（把 `**` 从 `「完成」` 前挪到 `可验证定义` 前）。`norm` 把星号归一成空格，所以**标记位置**是散文轴看得见的、而**标记泄漏**看不见——旧文案归一化后是 `定义 完成 的可验证定义`（少一个空格），新文案是 `定义 完成 的 可验证定义`，同步前必然对不上。其余 7 页改完归一化后与线上完全同形（括号、`「」`、星号都落成空格），所以它们不报——这条差异恰好把散文轴的**分辨率边界**量了出来：**它看得见标记挪到哪，看不见标记有没有生效**。

同步后要断言的两条（收尾提交里补实际读数）：`emphasis flanking --live` 的 `prediction-mismatch=0 served_markers=0`，以及散文轴 `MISS=0`。

### 七、留下的账

1. **`.md` 端点是一枚没用起来的第三方信号**：本轮观察到平台对判定为字面的标记会在 `.md` 里写成转义形式（星号前带反斜杠），而真粗体的两个标记保持原样。这等于平台把它自己的解析结论写回了文件——可以拿它当第二条独立裁判，不必只靠「可见文本里数星号」。代价是多一条网络腿，所以先记账。
2. **`_` / `__` 与 3 个以上星号不在对象里**：下划线的词内附加条件、`***x***` 的粗斜体语义，这本书目前没用过（第 83 轮 v1 那次误用除外）。轴只判 `*`/`**`，扩语法时要先加控制项再放开。
3. **组件嵌加粗只有 n=1**：§五 那条是平台与 CommonMark 的分歧，我没有把它写成规则（粗扫正则在同行第三个标记上会跨对误配）。兜底靠等式腿，等第二个真实样本出现再考虑落判据。
4. **作者腿是预测，红不红的最终判据在 `--live`**：不带 `--live` 时这条轴只打印 `NOTE author leg only`，退出码不代表线上干净。
5. **纯标记修订在那条见证腿上永远不能转绿，这是设计而不是缺陷**（收尾时确认）：那一轮没有新增读者可见的文字，就没有针可切，页面只能落 `UNWITNESSED` 并让退出码保持 1。它靠等式腿判同步，不靠这条腿。后续若想让这种轮次也读绿，得先给它换一件可证的事——而不是放宽「判不了」。

### 八、线上复验（收尾提交补写）：承诺的两条都兑现了，而这两趟又踩出**三条尺子**的错

推送后同步可见（`.md` 端点在 02:53:13 出现本轮挪好的标记），三条判决：

```text
emphasis flanking: pages=0 leaked_strong_markers=0 lone_star_runs=1 (context only)
live leg: pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0
prose survival: pages=193 units=12573 plain=11047 widget=1526 | MISS=0 STALE-COPY=0
```

§六 承诺的两条（`prediction-mismatch=0 served_markers=0` 与 `MISS=0`）都成立。`STALE-COPY` 那 311 条同时归零，因为线上那份更新日志已经发到第 84 轮：`check_live_sync` 两腿各读 `newest round=84`（`.md` 271139 字节 / 136 次提及，HTML 21325952 字节 / 483 次提及）。

**收尾这两趟量出的三条错全在量具上，三处也都改在量具上**：

**① 不带分号的实体引用：作者侧解码了平台没有解码的东西。** 复跑第一趟散文轴读 `MISS=1`，红在更新日志第 83 轮第二节第 2 条那句「放最后就会把「引号」读成「&quot 引号 quot」」（写本节之前它在 L128，本节把它自己那条例子加进文件后行号后移，所以这里按节锚而不按行号锚）。取线上原始 HTML 对质：平台那一行写的是 `&amp;quot`——**读者眼前的字与我写的字一个不差**。错在作者侧：Python 的 `html.unescape` 会把不带分号的遗留实体（`&quot`）也解码，于是把读者明明看得见的 `quot` 这个词从单元里删掉，两把侧对同一串字符用了两套规则。修法：作者侧只解码**以分号结尾**的引用（新增 `decode_as_platform`），线上侧保持原样（平台发出的转义一律带分号）。修后对同一棵树复跑：`units` 一字未动（`12573`），只有 `MISS=1 → 0`——**没有单元被新增、拆分或删掉，所以这条修法不可能顺手藏起别的丢失**。常驻控制多一条 K（三向）：`&quot` 必须留在单元里、作者与线上两侧必须对平、把那句的后半藏掉必须照样报吞；把修前的解码装回去跑控制，前两条如期红。范围也没有靠猜：全站扫裸 `&`（后面不接带分号的引用）共 **77 处 / 28 页**，但两套作者侧解码真正读出不同的只有 **2 行 / 1 页**——都在更新日志，一处是第 83 轮第二节那条例子，另一处是本节自己写的例子。
**② 见证腿可以要求一句读者永远看不到的话。** `check_live_sync --rev HEAD~1` 把 `hallucination.md` 判成 `STALE … added lines absent: '2026-09-25'`。那一行是 frontmatter 的 `updated:`，而**平台从不把 frontmatter 印进读者页面**：随机取近六轮改过的 5 个读者页，各自的日期在**含原始 HTML 的整页里 5/5 零命中**。这条针无论同步多完美都不可能绿——它把「本轮没加新散文」误判成「线上还是旧的」。修法不是放宽这个桶，而是给回退针（链接主机、日期）加一道闸门：**这一页的正文里印不印它**；正文起点共用散文轴的 `frontmatter_end`（抽成 `reader_body`），免得两把尺子对「正文从哪起」各说各话。不印就不许当针，页面落回 `UNWITNESSED`（「判不了」而不是「已同步」，第 59 轮的分工）。

**这条账在本轮收尾时又往上追了一行**：闸门最初只包住两条回退针，而**中文散文针那一侧漏了**——一次提交若只改 frontmatter 的 `description:`，那串中文照样会被 `CJK_RUN` 切成针，读者页面同样永远不印它，属于同一个 bug。于是把切针逻辑抽成 `needles_from(added_lines, body)`，**三类针一律过同一道正文闸门**（散文串、链接主机、日期戳），控制项随之从 5 条长到 **7 条**：只住在 frontmatter 的日期、封面地址、`description:` 中文必须都不当针；写在正文里的日期与地址必须当针；正文里新增的一句中文必须当针；一个 stamp 了但正文没印的日期必须不当针。把闸门从散文串那一侧拆掉再跑控制，读 `pre-fix controls: 1 error(s)`，报的正是 `description:` 那条例子（`want=[] got=['这一句只写在元数据里，读者页面上永远']`）——**这条控制不是白加的**。修后实测：`--rev HEAD` 仍 `witness ok` 7 页（没有回归），`hallucination.md` 从 STALE 变 `UNWITNESSED (HEAD added no sliceable text there)`；`--rev HEAD~1` 同一页同桶。**两趟退出码仍是 1，这是有意的**：纯标记修订本来就没有可见证的新文字，那一页由等式腿判（`prediction-mismatch=0 served_markers=0`）；把「不能见证」读成「已同步」正是这条腿要防的事。收尾提交自己会往首页加散文，所以见证腿只能在它之后转绿。

**③ 目检这一腿自己也返工了一次**（第 77 轮那条「目检证据不许是被格式化过的字符串」的又一次现身）。第一趟真渲染两张页：`hallucination` 与 `agent-failure-playbook`，各自的读者可见正文里字面 `**` 都是 **0**，但 `hallucination` 那一趟打印 `hit-pages=[]`——PDF 里没找到我要看的那句。根因在探针而不是页面：我拿作者句子**前 12 个字符**当搜索钥匙，那串里带空格，而 PDF 抽出来的文本空格已被剥掉，于是永远匹配不上。重写成先 `re.sub(r"\s+","",…)` 再搜，第二趟立刻命中。同时那把 `<strong>` 的正则窗口原本截在 24 字符，长一点的粗体根本匹配不到闭合标签，第一趟因此把 `hallucination` 数成 12 个；窗口放宽后真实读数是 **13**。两处都是量的错，不是内容的错，所以都留字在这里而不是悄悄重跑。

第二趟的读数（引擎 `chrome-headless-shell-1234`，逐字符 `repr` 打印）：`hallucination` 页字面 `**` 可见正文 0 / 原始反转义后也是 0，`<strong>` 13 个，其中含「忠实 / Faithfulness」的那一个内文本恰好是 `忠实度`（括号里的英文和后半句都不在粗体里，正是第 83 轮挪标记要的结果），PDF 682,665 字节 / 5 页，命中第 1 页，截图 `r84_halluc2_p1.png`（166,819 字节，1240×1754）——**逐像素看过**：「忠实度」三个字粗、`（Faithfulness）` 不粗、全页无裸星号。`agent-failure-playbook` 页字面 `**` 0，`<strong>` 43 个，PDF 872,796 字节 / 7 页，命中第 2 页，渲染文本 `repr` 为 `「完成」的可验证定义与最大预算；用外部校验器判定是否真达成，而非听模型自`，截图 139,238 字节。

变异控制同趟复跑：在已下载的线上 HTML 里藏掉 `hallucination.md` 一句真散文的开头，判据点名它（`hid '系统提示词强制' … (87 chars)`）——这条腿不会因为修了尺子就听不见真吞字。

### 九、第二次线上复验：这一趟判据把 §八 自己刚写下的字也判了

上一节末尾留了一句还没被证明能发生的话——收尾提交会往首页加散文，所以见证腿只能在它之后转绿。`49e9ff8` 推上去之后串行复跑三条腿（浏览器与线上腿不并行），读数：

```text
prose survival: pages=193 units=12623 plain=11097 widget=1526 | MISS=0 STALE-COPY=0
emphasis flanking --live: pages=196 fetch-failures=0 prediction-mismatch=0 served_markers=0
live sync: local newest round=84
           leg md   newest round=84  (274720 bytes, 136 rounds)
           leg html newest round=84  (21460674 bytes, 483 rounds)
           witness ok  docs/README.md  3/3 added needles live
```

- **等发布那一趟量到「谁先同步」的方向会反过来**。03:23:49 渲染页已经带着 §八 的标题（针是从作者文件里切出来的，不是手抄），而同一趟 `.md` 端点仍读 `False`。本轮早先那一次恰好相反：`.md` 在 02:53:13 先出现标记。所以这条腿的形态不能改：**两条都问，定案只看渲染页**——`.md` 先到不等于已发布，`.md` 落后也不等于没发布。第 61 轮那扇门当初只读 `.md`，就是被这类不对称坑过才改成两腿取较差。
- **见证腿如 §八 预言的那样转绿**：`docs/README.md` 三根针全在线上正文里命中，`witness: 1 reader page(s) HEAD touched carry HEAD's added text`。写下来时它是一件还没有证据的期望，现在它是量出来的。
- **散文轴第一次当场判掉本轮自己写的日志正文**。`units` 12573 → 12623（+50，全部来自收尾提交），而 `published_cut()` 这一趟返回 `None`：线上页面自己报出的最新轮次（84）已经等于树上的最新轮次（84），于是第 83 轮记下的那条「最新一轮的散文晚一轮才判」的账**本轮没有被触发**，§八 那 50 个单元是当场判的，`MISS=0`。这不是把切点放宽换来的——同一个函数在页面还停在旧轮次时照旧给得出切点，控制 H 的两条（旧稿必须给切点、当前页必须不给）就在每一次 `--selftest` 里跑。
- **这条门的 fail-safe 在真实世界响了一次**：第一次跑 `check_live_sync` 时 HTML 腿撞上 `URLError`，判据打印 `live changelog (html) unreadable (URLError) — no verdict, this is not a site failure` 并以 `exit=2` 结束——**它没有把「这一页压根没抓到」读成「已同步」**。重跑同一棵树才是上面那批读数（`exit=0`）。第 59 / 64 轮那次内容桶与覆盖桶的分账在这里第一次兑现价值：一次网络抖动值一次重跑，不值一句「线上没问题」。

留下的账没有新增：§六 那五条原样搬着（最新一轮散文可能晚一轮判——本轮只是恰好没触发；`<strong>` 范围错而句子连续，由这条新轴的等式腿接住；组件嵌加粗只有 n=1，没做成规则；作者腿是预测，红不红最终在 `--live`；纯标记修订在那条见证腿上永远读不绿，这是设计）。

### 十、收尾离线复跑抓到第四条：一条从第 83 轮就红着的引用判决

§九 那三条线上腿跑完之后，把离线轴全部复跑了一遍。八条里七条 `exit=0`（结构 198 页 0 问题、条目标题 `HEAD=76 tree=76 lost=0`、汉字 `prose CJK=400683 findings=0`、组件配平 `hint=257 stepper=54 step=279 tabs=52 tab=195`、README 统计全轴 ok、跨页复述 `dup=0`、导航 `196 页 0 问题`），**引用逐字回核那条读 `exit=1`**。汉字那个数按第 60 轮的规矩只写到最后一次复跑为止：抓红的那一趟读的是 400585，本节随后落的字又把它往上推过——这条轴能引用的从来是差值，不是绝对值。

它红的地方不在本轮写的字里，而在**第 83 轮**那段：`00-index/changelog.md` 写着那句「判据读数只认当前树」——它引的是首页当时的原话，可那句话在第 83 轮自己就被删掉了，读者在任何一页都查不到。这正是第 62 轮立 `RETRACTIONS` 登记册要管的情形（日志引用一句**故意删掉**的话，是为了记录那次删除），当时按规矩应当登记，而第 83 轮没有登记，于是这条判决从那次提交起就一直红着。

修法是按登记册的双向断言补一条，而不是把这句话从日志里抹掉（抹掉等于把第 83 轮那次失真重新藏起来）：`old` 用 `git show b10e40f:docs/README.md` 取回**逐字**原句，`new` 取首页现在那句替换语（`它不许当等号用`），`source` 指向 `docs/README.md`，`billboard=False`（首页已经不再印它，没有哪个版面还许印）。复跑：`findings=1 → 0`、`verified=18 → 19`、`RETRACTED-OK 6 → 7`、控制行的 `retractions=3 → 4`，`--selftest` 23 条断言全过。

**登记不是豁免，这一条量过**：同一份登记用两个假状态喂给判据，两次都必须响——把 `new` 换成一句首页没有的话，读 `UNMATCHED（登记的替换句不在 README.md 里）`；把 `old` 那句话加回首页正文，读 `RETRACTION-NOT-APPLIED ['README.md']`。也就是说这条登记同时被两件事钉住：**旧措辞必须真的死了**，**新措辞必须真的活着**。

同一趟还抓到首页自己的一处不一致：那句「全站读数」印的是 `text=55`，而同一句话的括号里已经解释了它后来动到 56——**引用的绝对值没跟着最后一次复跑走**，正是第 60 轮那条「README 复现不出自己的读数就是缺陷」的形态。已按本轮最后一次复跑改成 `text=57`，并把两次收尾各推一格（55→56、56→57）写在同一句里。这条轴的等号仍然只在 `executable-tagged=0` 与 `unclosed=0` 上。


## 2026-09-25（第 83 次）「每一句正文都真的到了读者眼前」这句从来没有判据——落库 `tools/checks/check_prose_survival.py`，首趟量出 **1923 条到不了读者的句子**，逐条归因之后：**5 处是尺子自己的错，1 处是平台真的把一句话加粗错了 20 个字符**

本轮正文只动 **1 页 1 段**，其余全在 `tools/checks`。

### 一、这条轴判什么，为什么已有的轴判不到它

判据只有一句：**作者写的每一段散文，在读者那一页的可见正文里必须连着出现**。作者侧按句读切成「句子单元」，线上侧走 `body_visible` → 去标签 → `html.unescape` → `norm`，再逐单元做子串比对。

已有的轴都不做这件事：SSR 对平轴比的是**组件与容器的数量**（提示卡、标签、公式各多少个），Mermaid 与图注轴比的是**图**，链接轴比的是**地址**——一句话少半截，这些轴全部照绿。第 76 轮那次「转义反引号把整句渲染成空公式」就是从这条缝里漏出去的，当时靠人眼发现。

最终读数：`prose survival: pages=193 units=12391 plain=10865 widget=1526 | all` + `lost sentences: MISS=1 STALE-COPY=245`（这是本轮最后一次复跑的读数——之后写进日志与首页的字还会推动 `units` 与 `plain`，所以这两个数不许当等号；措辞推不动的那条是「同步完成后 `MISS=0`」）。唯一那条 MISS 是本轮自己改的 `hallucination.md`（见第三节），提交后待平台同步。

### 二、1923 → 2：五趟扫描，四次抓到的是尺子

| 趟 | 单元数 | MISS | 归因 |
|---|---|---|---|
| 首趟 | 12655 | 1923 | 未归因 |
| 第二趟 | 12393 | 536 | 表格/实体/列表标记三条尺子规则落地后 |
| 第三趟 | 12389 | 9 | 按节切点后 |
| 第四趟 | 12391 | 2 | 自动链接判 HOLE 后 |
| 第五趟 | 12391 | 1 | 尖括号规则落地后（剩本轮自己的那条待同步） |

四个尺子 bug 各自都有 served 端证据，不是「调阈值让它变绿」：

1. **GitBook 会在两个表格单元格之间印自己的 `gitbook assistant` 标签**——于是「一句单元跨两个单元格」必然被自己的排版打断。改成一个单元格一个单元（`|` 处判 HOLE）。常驻反例：给真单元格注入 per-cell 按钮文本，句子必须照样存活。
2. **`&quot;` 之类的实体**：比较顺序必须是去标签 → `unescape` → `norm`。放最后就会把「引号」读成「&quot 引号 quot」。
3. **有序列表的序号是 CSS 生成的**，读者侧文本里没有 `1.`：只在单元第一片剥 `^\s*\d+[.)]\s+`，正文里的「2026.」不受影响。
4. **裸 `<https://…>` 自动链接会把自己的 URL 印进正文**——第三趟那 9 条里有 3 条是它，且三条所在页其余文本**全在**。改判 HOLE。
5. **`<(?!br…)[^>]+>` 吃掉了散文里的尖括号**：更新日志自己那句 `（W<420 且 H>380，宽高比 <0.55）` 在**作者侧**被删成 `w 380 宽高比 0 55`。规则改成标签名必须以 `[a-zA-Z/!]` 开头；served 侧同规则安全，因为那边尖括号早已转义成 `&lt;`。

### 三、唯一一条真的读者侧缺陷：平台把「成对星号」配成了「第一个配最后一个」

`hallucination.md` 原句一句话里有两个加粗对、中间还夹一个链接：

```
这与 RAG 评估里的**忠实度（Faithfulness）**是同一思想（见 [RAG 基础](…)）。对应地，还要看**召回**：…
```

线上渲染成 `<strong>忠实度（Faithfulness）是同一思想（见 …）。对应地，还要看</strong>召回`——**20 个从没打算加粗的字符被连带粗化，链接标签也被粗了**。

**先证明它不是尺子的错再改内容**：配对正确时，`**` 归一化后落成的那个空格恰好对上 `</strong>` 的边界。全书 865 行「≥2 个加粗对」的写法（其中 121 行同时带 Markdown 链接）在这种边界判定下**全部判绿**，只有这一行对不上。所以 **没有为它放宽 `*` 的处理**——那会把 865 行的常见情况判坏，还会把这条真缺陷一起藏掉。

修法：一句拆成两句、链接挪到句末独立指路（`两者的检索侧写法见 [RAG 基础](../06-memory-rag/rag-basics.md)`）。指向的文件与原来相同，**内容一个字没删**。

### 四、`published_cut` 第二版：「本轮自己的日志」为什么不能判，以及怎么不靠自觉

第一版按「最后一个已发布的 `第 N 次` 标题行」切，量出来切不准，原因是收尾提交的性质：**下一轮会回来编辑上一轮那一节的文字**。实测线上更新日志页同时印着第 79 次的条目标题**与第 78 次的收尾句** `读者侧抽查 3 页 6 条针全部命中`，而 HEAD 的第 79 次那节已经写成 `6/6`——「页面上有第 79 次的标题」证明不了「第 79 次的正文已发布」。

改成**按节判**：从页面自己印出的轮次序列里，取严格早于线上最新一轮的第一节作为起跑线；历史不是「最新在前」的页面**不给任何切点、全量判**。

代价诚实写出来：**最新一轮的散文晚一轮才被判**。这条不靠自觉兜着——`check_live_sync` 的 md/html 两腿各自报落在第几轮（本轮 `leg md 82 / leg html 79`），并对这一页额外出声：`NOTE the published changelog PAGE is at round 79: readers opening it are missing 80, 81, 82`。

### 五、桶：`MISS` 决定退出码，`STALE-COPY` 大声但不复印别人的判决

245 条「线上还读不到」全部落在更新日志页被 round 79 卡住的那一段（`unpublished=245 of 2944 units`）。它们是第四节那件旧账的**症状**，不是 245 个内容缺陷。若这条轴也判红，等于把 `check_live_sync` 已有的判决复印一遍，而复印的代价是下一轮开始有人把「红」当常态。故 `MISS` + 未取到页 + 未列页决定退出码，`STALE-COPY` 打 NOTE 并指名去哪条轴看那条判决。

### 六、绿色是拿什么换的

- **10 条种植控制**（吞句是唯一 MISS / 围栏体永不作散文 / 组件体必须打标 / frontmatter 不判 / 表格单元在注入按钮文本后仍存活 / `&quot;` 句不算吞 / 有序标记不入单元 / 按节切点四态：生效→第 3 行、当前页→None、无历史→None、非最新在前→None / 自动链接终结单元 / 散文尖括号在原生与转义两侧都存活）。读数 `controls: OK, every bucket able to fire`。
- **变异控制** `--mutate PAGE`：在**已下载的线上 HTML** 里藏掉一句真散文的 8 个字符，要求判据点名它——`hid '检索问题要到日志里认领' on 06-memory-rag/rag-basics.md and the judge named it (99 chars)`。这一条是第二节那五处放宽的唯一辩护：尺子松了之后**仍然抓得住真丢的字**。
- **复用而不是新造**：行内代码剔除沿用第 57 轮那把全站共用的 `strip_code_spans`，本轮给它加 `hole` 形参（留标记而非留空格），句子单元从此不跨一段代码。

### 七、顺带把 `check_live_sync` 的见证腿从 31/34 抬到 34/34

它原先只用「本轮新增的散文串」当针，于是被三类**没写散文**的改动卡住（只改统计数字、只改链接、只改日期）。现在针按次序取：CJK 散文串 ≥16 → 新增链接的主机名 → 新增的 `updated:` 日期。草堆也换成与散文轴同一套顺序（去标签 → `unescape` → `norm`），免得两把尺在同一个缺陷上 disagree。读数 `witness: 34 reader page(s) HEAD~2 touched carry HEAD~2's added text`。

### 八、写本轮日志这件事本身推动了一个首页统计数：无标签围栏 8 → 9

`check_structure.py` 复跑读 `mermaid=217 json=79 text=52 markdown=11 yaml=10 无标签=9 | executable-tagged=0`，而首页那句还印着 `无标签=8`——推手就是上面第三节那段示例（它必须用无标签围栏才能既展示原句又不被当成可执行代码）。这与第 77 轮「解释组件语法的句子必须把语法写进反引号」是同一类：**措辞能推动的计数不配当等号**。首页那句已改成 9，并写明钉的等号是 `executable-tagged=0` 与 `unclosed=0` 这两条措辞推不动的不变量。

**同一趟复跑还揪出第二个数**：`check_prose_duplicates.py` 读 `prose_units=7362`，首页却印着第 63 轮的 **7116**。差了 246 个句子单元、跨 20 轮，而这条轴的这句话下面本来还写着「判据读数只认当前树」——**那句话当时是真的：数会随正文动，但没人回来对过**。第 77 轮那个手抄的 251 之所以危险，就是因为它躲在一条「这数本来就会变」的免责声明后面。首页这一句已改成**本轮最后一次复跑的读数**，并把免责声明改成指明「哪一轮复跑、只到那次为止」；而**改数这件事本身又把它推了两格**（7362→7365），正是「这个数不许当等号」的现场演示。

### 九、留下的账

- **更新日志页 46 万字符 / 2944 个句子单元，线上卡在 round 79**。要不要按年或每 20 轮拆成一节一页，是**产品级取舍**（动的是读者看到的页面结构，不是尺子），本轮只把症状钉成一条 NOTE，页面一个字没动。
- **没有 `<strong>` 覆盖范围的常驻轴**。这次抓到误配对靠的是「整句连不连着」这条钝判据：加粗范围错了顺带把句读打断，所以量得到；而「加粗范围错、句子仍然连续」的写法这条轴看不见。
- 最新一轮散文晚一轮判（第四节）。**同一条账在首页上更硬**：首页没有「第 N 次」标题序列，定不出切点，所以本轮新写的那条 bullet 在同步完成前会被读成 `MISS`（一条真红，而不是 `STALE-COPY` 的灰）——收尾抽查若在同步前跑，这个数必须逐条点名归因，不许当成「轴坏了」。
- 一次性噪声：全站扫描里出现过 1 次 SSL `UNEXPECTED_EOF_WHILE_READING`（`function-calling.md`），该页单跑 `units=68 MISS=0`。**没有做成自动重试**——未取到的页必须算「未判」（fetch-failures 非空即红），不能悄悄变绿。

### 十、收尾：线上复验的真实读数，以及那次目检当场抓到的新类

推送 `ec2ff68` 之后，按第九节那两条账的规矩复验（时刻取本机文件时间，同一趟连续跑出来的）：

| 时刻 | 腿 | 读数 |
|---|---|---|
| 02:11:52 | `.md` 端点针 | 本轮改写的那句在 `.md` 里出现（`needle in md = True`），旧措辞 0 命中。推送前 01:21 那道门还读 `html newest round=79`、缺 80/81/82 |
| 02:12:09 | 单页散文轴 | `pages=1 units=36 plain=34 widget=2`，`MISS=0 STALE-COPY=0` |
| 02:12:37 | `<strong>` 边界 | 页面 12 个 strong，被修的那句读回 `<strong class="font-bold">召回</strong>`；旧缺陷的形状在整页里 0 命中 |
| 02:13:21 → 02:14:03 | 真实渲染目检 | `--print-to-pdf` 562,407 字节 → PyMuPDF 首页 PNG 167,640 字节 |
| 02:14:42 | 线上原始 HTML | 同一页印着 `<p class="paragraph …">这与 RAG 评估里的`＋两颗星号＋`忠实度（Faithfulness）`＋两颗星号＋`是同一思想。</p>` |
| 02:15:09 | 全站复跑 | `pages=193 units=12483 plain=10957 widget=1526`，`MISS=0 STALE-COPY=311`；311 条全在更新日志页（`unpublished=311 of 3010 units`，线上那份证明不了第 365 行以下） |

**这一次目检真的付了钱**：散文轴对那一页读 `MISS=0`——字确实一个字不少地到了读者眼前，而读者在页面上看见的是**裸星号**。也就是「字到了」与「标记生效了」是两件事，前者当场有轴、后者一条都没有。这条新类在**第 84 轮**落成了 `tools/checks/check_emphasis_flanking.py`（含把这一页读成 36 个单元 / `MISS=0` 却量出 2 个泄漏标记的那次归因），第九节第二条账随之销账。

同一趟还顺手记下一条没用的证据：`.md` 端点把这两个**被判定为字面**的星号写成转义形式（每个星号前面多一个反斜杠），而同一页真粗体的那两个字在 `.md` 里保持原样——平台把它自己的解析结论写回了文件。第 84 轮把它记进留下的账，没有立刻做成判据。

## 2026-09-25（第 82 次）六条浏览器轴在同一趟里集体瞎掉——共享启动器从此必须**自证会渲染**；重新锚定时撞破一个记了 20 轮的前提：「复制稿没有导航面板」是引擎读数，不是复制稿的性质

本轮改动全部在 `tools/checks`（8 个文件），**正文 0 页**——所以 README 的统计一个数字都不动（`check_readme_stats` 逐键 `ok`）。

### 一、缺陷在量具上：一个「退出码 0、stdout 空」的浏览器能让六条轴同时报绿

第 81 轮收尾时发现本机 Edge 对 `--dump-dom` 返回 rc=0 而 stdout 0 字节，六种 flag 变体全一样。这条轴体系里所有「0 问题」的读数在那一刻同时失去了意义——**因为种在页面里的反例要穿过浏览器才能被抓住，浏览器不渲染时反例也跟着消失**。所以本轮不是「换个路径」，而是给共享启动器加了一条硬要求：**没证明自己会渲染的引擎，不许进入判决阶段**。

| 落库的东西 | 作用 | 本轮读数 |
|---|---|---|
| `engine_alive(exe)` | 用 `@@ENGINE@@` 哨兵页跑一次真渲染；90s 超时与 `OSError` 都算「瞎」（`HANDBOOK_BROWSER` 指向一个不是可执行文件的路径时必须**跳过**而不是崩） | 通过才继续 |
| `browser()` | 候选顺序 Edge → 各 `chrome-headless-shell`（新在前），第一个自证的胜出并**把引擎名打到 stderr**——换引擎会移动阈值，没署名的读数无法重锚定；全瞎则 `SystemExit`，绝不打印 0 problems | `# engine: …chromium_headless_shell-1234…` |
| `headless_flags(exe)` | shell 本来就 headless，完整 Chrome/Edge 才需要 `--headless=new` | 每轴共用 |
| `--engine-selftest` | 启动器自己的三条腿：会渲染的引擎必须被接受；空 DOM 的引擎与「不是可执行文件」必须**带退出码**被拒 | `engine preflight controls ok` |

**变异测试的顺序值得记**：控制先写完时，那一趟打印的是 `AssertionError: an engine that exits 0 with an empty stdout was accepted by the preflight … a blind engine would print 0 problems`——**发射的是控制抓住启动器，不是启动器抓住控制**。补上哨兵预检后同一条腿才读成上面那行绿。

顺带把这台机器的引擎事实钉进注释：`chrome-headless-shell` 精确遵守 `--window-size`（1024/1280/1440/1455/1500/1600 全部由页面自报的 `innerWidth` 确认），Playwright 的完整 Chromium 在 CLI `--dump-dom` 下 8 个 flag 变体全部 45s 挂死，而旧引擎 Edge 曾把一个 1600px 控制盒夹到 ~1250px。

**换引擎没有移动这条轴的读数**：`check_mermaid_geometry` 在新引擎上 217/217 真渲染、`local=11.14.0 live=11.14.0`、`102 超宽 / 101 缩放 / 0 横向滚动 / 116 原样`、最宽 1116px、最小字号 11.0px 中位 16.0px——与第 62 / 73 轮那笔旧账逐项一致。

### 二、重新锚定第二条轴时，一个 20 轮的老前提塌了

`check_svg_legibility` 的复制稿腿在 vw=1440 读 `<main>=753`，而它断言的是 768——按「先验尺子再下判决」的规矩，先怀疑尺子。一趟阶梯量测（每行都由页面自报 `innerWidth` 确认）：

| 问的 vw | 复制稿 `<main>` | 线上 `<main>` | 差 |
|---|---|---|---|
| 1024 | 609 | 624 | −15 |
| 1280 | 593 | 608 | −15 |
| 1440 | 753 | 768 | −15 |
| 1455 / 1500 / 1600 | 768 | — | 上限在这里才咬合 |

第 73 轮写下的「复制稿挂不上 288px 章节侧栏和 256px 页内 TOC，所以正文独占 768」**是当时那台引擎的读数，不是复制稿的性质**：同一份复制稿在哨兵验证过的 shell 里两个面板都挂上了，差的只是 headless 预留的 15px 经典滚动条槽。本轮把这条从推断升级成直接读数——在复制稿的 SSR DOM 里量 `aside,nav`：`["aside.side-sheet=288","aside.side-sheet=256"]`，与线上腿逐字相同。

修法不是把断言放宽，而是**让每条腿先声明自己问的是哪个窗口，再按那个窗口真给出的列宽判决**：

* `COPY_VIEWPORT = 1500`（上限能咬合的最窄窗口，实测下界 1455 留了余量），`VIEWPORTS` 与两条下游轴的渲染窗口都改挂它；
* 两条下游轴各加 `assert rep["vw"] == COPY_VIEWPORT`——问的窗口与报的窗口不一致时，列宽数字毫无意义；
* 新增 `cap guard`：复制稿在 1500 必须读 768，否则**所有**用 768 当常数的轴先失效，红在常数上而不是红在内容上；
* 新增 `COPY-NOT-LIVE`：同一窗口下复制稿与线上的差必须落在 0–24px（滚动条槽的量级），否则判红。这条专门用来防第 73 轮那个盲区回来——那时复制稿比读者真拿到的列宽**宽 160px**，而下游六条轴都在替读者担保那个宽数；
* `COLUMN-MISMATCH` 从复制稿的 593 改挂线上读数：`readers get 608px (the live page at vw=1280)`。

**门槛没有放松**：内容判决仍在 768 上做（那是上限真正生效处），笔记本读数仍按线上量出的 608 报——本轮换掉的是一条假前提，不是一条严标准。

顺带一条新事实：宽版开关在复制稿的 1280 窗口下把列宽从 593 抬到 **768**（`wide layout at vw=1280 would give [768]`），在 1500 则 as-is 已经饱和在 768——也就是说它到底能不能超过 768，仍要到 `WIDE_NEEDS=1672` 以上的窗口才测得出来。

### 三、目检这一项本轮先失败了一次，而且失败得有价值

给「复制稿也挂面板」配图时，拍到的却是 GitBook 自己的错误边界页（`This page couldn't load` + Reload/Back）。加不加 `--virtual-time-budget` 两张 PNG 字节数完全一样（18062 / 16820），说明**崩溃发生在截图之前**；而探针的读数仍然有效，是因为它跑得更早、读的是服务端渲染好的那份 DOM——`check_svg_legibility` 里那个用独立 id 发报的 `fatal` 信标正是为这件事留的。结论写进了 `HYDRATED_AT` 上方：**复制稿可以量，不可以拍**；目检证据必须来自线上页。

改拍线上页后两张图都成立：vw=1500 `main=768`、vw=1280 `main=608`，两张都带 288/256 两个面板，控制盒 200/960 读准、`phantom=False`。1280 那张肉眼可见左侧章节栏、右侧 ON THIS PAGE、中间被挤窄的正文，与「读者在 1280 笔记本上拿到 608px」这句话对平。

### 四、本轮复跑与留下的账

八条受影响的东西全部在新引擎上重跑：`--engine-selftest`、`check_mermaid_geometry`、`check_svg_legibility`、`check_table_overflow --pages 4`、`check_live_column`、`check_content_overflow`、`check_svg_fit`、`check_svg_phase_legibility`。除两条**已知在等产品取舍**的红之外全部 `exit=0`：

* `check_table_overflow`：4 页 2332 格 `spill=0 bust=0`，`main=768`（本轮之前那 4 页全报 `main=753` 并计 4 条 COLUMN 问题），控制盒仍逐个溢出 267–298px；
* `check_svg_legibility`：32 图 / 1109 标签，768 列下 `0` 张有低于 12px 标签；笔记本 608 列下 32 图 / 1066 标签低于门槛，仍只报不判；
* `check_content_overflow`：276 条公式 `over-column=1`、最大 drag=12px（门槛 16px）、`unreachable=0`、`render-errors=0`；
* 离线结构面：`check_structure` 198 页 `problems=0`（mermaid 217 / json 79 / text 52 / markdown 11 / yaml 10 / 无标签 8，可执行标签 0，json 契约解析 79/79，未闭合 0）、`check_link_graph FAILED: 0`（717 个去重外链全有判决、`oldest-check=2026-09-24`）、`check_char_sanity` 389970 正文汉字 `findings=0`、`check_changelog_headings HEAD=73 tree=74 lost=0`（74 是本轮这条新标题）。

留下的账（都不是本轮能靠改尺子关掉的）：

1. **102 张超宽 Mermaid 仍在等站点那个宽版开关**，`--column 1152 / 608` 的重读也仍未做；本轮新量到「开关在 1280 复制稿上给 768」，但**是否超过 768 要到 ≥1672 窗口才测得出**，这条比上一轮更具体。
2. `check_live_column` 仍 `exit=1`：`COLUMN-MISMATCH readers get 608px`——为 608 重画全书图与收窄超宽图都是版式取舍，按停一停条款等操作者定。
3. 复制稿的 15px 滚动条槽是**这台机器的 headless 配置**给的，不是 GitBook 给的；若哪天换引擎或换平台，`COPY-NOT-LIVE` 的 0–24px 带需要重新量一次而不是照抄。
4. **GitHub PAT 早先贴在聊天里，仍需操作者去 GitHub 撤销轮换**（不是本轮能修的）。

## 2026-09-24（第 81 次）「每条结论都点得回一手来源」这句话被量过六次，六次的量具全用完就扔——落库 `tools/checks/check_link_graph.py`（站内跳转图 + 外部来源缓存判决 + 平台侧锚点腿），首趟量出 **22 个一手来源地址已经搬家（51 处引用 / 34 页，含 1 条 404）**，而另外三类「红」经查是尺子自己的错

本轮新增 2 个文件（判据 + 它的判决缓存 `tools/checks/data/external_links.json`）+ 改 34 个正文页的 51 处引用 + 首页新增一条带读数的统计句 + 本日志。

### 一、同类缺陷第七次，但这条轴以前是被量过的——只是量具不留下来

第 1 / 13 / 17 / 21 / 22 / 25 轮各审过这条轴的一段（断链、孤儿页、锚点、外链健康、元数据词表），用的都是当场写的脚本，没有一份留在 `tools/checks` 里。所以「断链与孤儿页」在 80 轮里实际是**计划书上的一行**，不是一条随时可复跑的判决。这与第 57 / 76 / 77 / 78 / 79 / 80 轮同形状，但更凶：**别的轴要等人挪动内容才失真，这条轴的失真由外部世界自己发生**——某个官方文档换了域名，那句话就从「点得回一手来源」变成假的，而读者比作者先发现。

### 二、判据量什么：三条腿，判决按「这条证据是关于书的，还是关于探测器的」分家

| 腿 | 判决 | 本轮树上 |
|---|---|---|
| 站内（离线，常驻） | `BAD-TARGET` 跳到不存在的文件 / `ORPHAN` 正文页掉出 SUMMARY / `SUMMARY-STALE` SUMMARY 指向已删页 / `ANCHOR-NONMD` 锚点挂在非 markdown 目标 | 0 / 0 / 0 / 0 |
| 外部（读缓存） | `DEAD` 404·410·451、`SOFT-404` 200 但落在「页面不存在」模板、`MOVED` 落到别的主机 | 0 / 0 / 0 |
| 外部 | `UNREADABLE` 5xx、`BLOCKED` 401·403·407·429、`NET` 连接层出事 → **报「判不了」，不报绿** | 0 / 14 / 1 |
| 外部 | `UNCHECKED` 被引用的 URL 缓存里没判决 = 覆盖失败 | **0**（717/717 有判决，`oldest-check=2026-09-24`） |
| 锚点（`--live`） | `ANCHOR-MISS` 目标页真发的 id 里没这个；`BLIND` ×4 = 探针自己瞎了 | 0（本轮 0 条锚点可判，见第五节） |
| 首页那句读数 | `HOMEPAGE-BADGE` 首页印的数与树不等 / `HOMEPAGE-BLIND` 首页把这句删了 | 0 / 0 |
| 覆盖地板 | `COVERAGE` 扫到的页数 / 站内跳转数 / 去重外链数 / 外链处数低于地板 | 0（四条地板各比本轮读数低 15–25%） |

全站读数：`link graph: pages=196 listed=196 nav-links=196 relative=1578 external-links=1526 distinct-external=717 citing-pairs=1275` / `external verdicts: {'OK': 702, 'BLOCKED': 14, 'NET': 1}` / `anchors: fragments-seen=0 graded-live=0` / `homepage claim: blocked=14 distinct=717 external=1526 fragments=0 net=1 ok=702 pages=196 relative=1578 unchecked=0` / `FAILED: 0`；`--selftest` 读数 `controls: 13 buckets, every one able to fire`。

**最后那行是第 76 / 77 轮那条老规矩的又一次落地**：首页要印这条轴的数，那这些数就不许是手抄——判据把首页那句话里的 9 个键**解析出来**与自己的测量逐键对平，错一个数字判 `HOMEPAGE-BADGE`，把整句删掉判 `HOMEPAGE-BLIND`（删句子不是「少写一条统计」，是把这条轴的公开承诺撤了）。

**外部判决存在 JSON 缓存里而不是当场探**，理由与第 58 轮「浏览器轴必须串行」同源：一个被限流的探测器永远可能给出假绿。`--refresh` 只重试「不确定性判决」，`OK / MOVED / DEAD / SOFT-404` 四种确定性判决留着——所以断网也能复跑，而一次 TLS 抖动也不会被写成一本书的缺陷。717 条是**四趟**跑出来的（首趟 8 worker、135 秒、663 条；加宽尺子后逐趟补到 717）。

**站内腿本轮读数是干净的**：`relative=1578` 里 0 处坏目标、0 个孤儿页、0 条 SUMMARY 失真。这条腿的价值不在今天抓到什么，而在它从此是回归线——第 21 / 22 轮那种「改名之后页面掉出导航」的事故，下次会在**当轮**被判红而不是等下一次人工审计。

### 三、22 个搬家地址、51 处引用：一条都没有照抄跳转链

改动前的一次性全量探测（663 个去重地址）读到 **15 条 MOVED + 1 条 DEAD**；把这些结果灌进缓存后，常驻判据自己的第一趟读到 **5 条 findings**（3 条 arXiv `SOFT-404` + 2 条 `MOVED`，其中一条正是第四节那条 www 单边豁免的尺子错）。剩下的 6 条**不是一次出齐的**：首趟 8 worker 的 SSL 抖动把它们读成了 `NET`，`--refresh` 逐趟把 `NET` 桶抽干才现形——第 2 趟 +2、第 3 趟 +2、第 4 趟起归零；其中那两条 Discord 只有加宽分词器之后才被看见，因为它们在索引表里是自动链接形状。最终**归纳成 22 个旧地址 → 22 个新地址，涉及 51 处引用、34 个正文页**（逐页处数从 1 到 3）。最大的一坨是同一家把整套 API 文档从旧域名搬到平台域名：`docs.anthropic.com/…/computer-use` 一条就占 10 处。

**没有一处是「跟着浏览器跳过去就写下来」**。采纳闸门要求：目标 URL 必须自己探到 `200`，**且落点等于自身**（`final.rstrip('/') == target.rstrip('/')`）。这一条拦住的是真东西——`docs.llamaindex.ai` 会跳，但跳到的是新站的**首页**，照抄第一跳等于把「去读 LlamaIndex 的文档」的读者送到一个不是那篇文档的页面。22 个目标逐条过闸（`probe-OK 200 … lands-on-itself=True`），并把服务端 `<title>` 逐条读回比对，例如 `Prompt caching - Claude Platform Docs`、`Best practices for Claude Code - Claude Code Docs`、`Overview - Claude Code Docs`。

**改地址之后又量了标签**：一次性审计把承载这 22 个新地址的 53 行里 61 条链接文字，逐个与 22 个旧主机名比对 → `labels still naming a retired host: 0`。这一趟确实抓到一处文字比 URL 更老：项目卡片里那个「官网 All Hands AI」——公司和项目都改了名，地址本轮换了，标签还留着上一个时代的名字。**唯一一条 DEAD** 也在这批里：一篇 2026 年 9 月的 TechCrunch 报道，作者把日期段写成了 ISO 连字符形状（`2026` 后面用 `-` 而不是 `/`），而这家站的日期是路径分段。这条最险，因为 GitBook 自己的页面 URL 里也带日期，读者扫一眼看不出哪一段是 slug。

**没有为凑改动面去动别的地址**：`www.anthropic.com/engineering` 这类仍然按原样指着——它们探到 200、落点也是自己，搬家的是内容位置而不是引用有效性。

### 四、三类「红」是尺子在骗我，一类是尺子太窄

1. **arXiv 标题里的「404」**：3 条 arXiv 引用被判 `SOFT-404`。反例是自己会说话的——`[2404.06654] RULER: What's the Real Context Size…` 是一篇活论文，投稿编号里就含 `4-0-4` 三个数字。修法：判「未找到」只认**短语**（`not found` / `页面不存在` / `找不到页面` / `does not exist`…），裸 `404` 必须是**独立成词**的数字段。5 条反例常驻 `--selftest`（arXiv 形状的标题必须不出声，`404 Page Not Found`、`Error 404`、`该页面不存在` 必须出声，`arXiv:1404.5678` 必须不出声）。
2. **只往一个方向豁免的 www**：`www.eleuther.ai/community` 被判 `MOVED`，因为跳转只是去掉了 `www`——旧规则只原谅**加** `www` 的那一侧。改成双向同站判定（`same_site()`），并钉三条反例：去掉 `www` 不算搬家、加 `www` 也不算，但 `docs.smith.langchain.com → docs.langchain.com` **必须**算（那是本轮真搬家的一族）。这个地址因此**没有改**。
3. **探测器的速率不是书的状态**：首趟 8 worker 探 663 条，返回 31 条 `WinError 10054` / `SSL UNEXPECTED_EOF`。第 67 轮资产腿犯过同一个错并把结论写进过日志。修法：节流 0.6s、网络类判决冷却后重试一次、并且**网络类永不入库为绿**（缓存里 `NET` 会被每一轮重试）。另有一条 `mcp.so` 报 `HTTP-522`（`UNREADABLE`），重探即 `OK 200`——记成出口抖动，不动内容。
4. **分词器太窄**（不是判错，是看不见）：只认 `[label](target)` 的尺子把整张资源索引表读成散文。本轮的复量结果与首趟一致——**98 处可点跳转 / 54 个去重地址此前不存在于判据的眼里**（窄尺 1428 处 / 663 个 → 宽尺 1526 / 717；另有 93 个地址以自动链接形状出现，其中 54 个只有这一种形状）。**这条是本轮最贵的尺子教训**：一个看不见的链接**永远不可能**被判成死链，而它的覆盖地板照样读绿。撞破它的过程也值得记：判据的采纳闸门说「这条链接不存在」，同一次运行里对同一页的 grep 说它存在。

顺带一条口径修正：本文件顶部注释写 98 处，而 `iter_links` 的注释写 99 处——两个数来自同一趟测量的不同阶段，复量脚本落在临时目录里给出的读数是 98/54，因此把两处统一成 98，并把复量口径写进注释。**同一个数在判据自己的注释里有两个版本**，这与第 56 轮「同一棵树同时有过 930 / 931 / 943」是同一类事故，只是发生在最小的地方。

本轮最后一次自我修正不在判据里，而在**写日志的手上**：把第 81 轮条目插到第 80 轮之上时，覆盖掉了后者的 `## ` 标题整行。正文一个字没丢，但它的 6 个小节全部挂到了错误的轮次下面——按日期翻日志的人会读到「第 81 轮重写了 lab5 的时钟」。抓到它的是第 24 轮落库的 `check_changelog_headings.py`（HEAD 与工作树逐条对标题），首趟读数 `HEAD=72 tree=72 lost=1`；这条判据此前只在自己种下的反例上红过，本轮是它第一次在**真实事故**上发射（恢复后复跑 `HEAD=72 tree=73 lost=0`）。修复刻意不手抄：脚本从 `git show HEAD:` 里按 `第 80 次` 取出那 173 字符的原文插回去——本轮已经在 URL 上量过「显示器会把两种不同字符串印成同一种」，一条人耳无法核对的中文标题是同一风险的放大版。

### 五、锚点腿的空集是量出来的，不是猜出来的

`--live` 读数 `fragments-seen=0 graded-live=0`——**0 不是漏扫，是这本书的锚点引用数本来就是 0**（全书引用的是**文件**，不是文件里的某一节）。三件事把「空集」与「探针失明」分开：

- 同一趟打印 `relative=1578`，证明扫描器在动，只是没有 fragment；
- 这条腿自带 4 条 `BLIND` 判决：目标页必须在 `llms.txt` 里有唯一条目、抓回的 HTML 必须暴露 >0 个 heading id、正控制（本页必定发布的锚点）必须命中、一句从没写过的幽灵 fragment 必须不命中。**平台哪天不再发 id，这条腿会报 BLIND 而不是报绿**；
- 为什么离线不判 fragment：本轮标定过——更新日志页有 252 个标题、服务端发布 243 个 id，而**离线按 CommonMark 直觉造的 slug 命中 0/252**。GitBook 会把中文标题转拼音（`快速开始 · Quick start` → `kuai-su-kai-shi-quick-start`）、给数字开头的标题加 `id-` 前缀、并且**不给页面 H1 发 id**。离线重建这套规则需要一张拼音表，而且会随平台漂移。

### 六、留下了什么

- **15 个被引用的地址判不了**（`BLOCKED` 14 + `NET` 1）：`openai.com/news/`、`www.reddit.com/r/LocalLLaMA/`、`www.iso.org/`、`linux.do/`、`academic.oup.com`、`dl.acm.org` 这类反爬/需登录站，以及本轮新采纳的 `code.claude.com/docs`（本机出口对那台主机的 TLS 还在抖）。**这不是通过**：`--refresh` 每轮都会重试它们，缓存里冻结的只有确定性判决。
- **Discord 那两条改成了邀请码直链**，取舍写在这里：旧地址（`www.anthropic.com/discord`、`hf.co/join/discord`）是官方落地页，现在它们自己跳到 `discord.com/invite/<code>`。直写邀请码少一跳、也更接近读者真正到达的东西；**代价**是这类地址可由社区管理端作废重发，而落地页不会。社区页正文本来就写着「英文即时聊天类（HF / Anthropic / EleutherAI）Discord 链接都会跳到邀请页」，读者知道自己点的是什么。
- **两处刻意不动**：截图清单里 3 处提到旧的 LangSmith 主机——那是「这张图于何年何月从哪个地址截下」的出处记录，改它等于伪造历史；本页同理，**日志写下旧地址的那一刻起，读者侧探针的 OLD 腿就不覆盖这一页**，探针因此只跑改过的正文页。
- **缓存里 721 行 ≠ 717 条在引用的地址**：多出的 4 行是本轮改掉的老地址（它们不再被引用，`--refresh` 也就不会再探）。留着的理由与截图清单一样——那是「本轮曾从这儿搬走」的记录；判据只对**被引用**的 URL 出判决，历史行不参与读数，也不会被误读成「有 4 条搬家没修」。改判决规则时**必须把受影响的行从缓存里删掉再重探**：本轮把 `SOFT-404` 与 `MOVED` 五行的分类改了口径（arXiv、www 两条），如果留着旧行，新尺子永远不会去看它们。
- **`339` 与 `717` 不是打架的两个数**：首页那句「154 篇知识/资源页全部有『参考资料』…339 条去重后的外部一手来源」数的是**各页『参考资料』小节内**的去重来源；这条新轴数的是**全站正文出现过的所有外部 URL**（表格、行内、自动链接都算）。口径各写各的，新首页句子里已经写明范围，免得下一轮把其中一个「修正」成另一个。
- **`yaml` 契约仍未过解析**（与第 79 / 80 轮同因：仓库里没有钉住的 YAML 解析器），本轮不补。
- **收尾电池抓到本轮自己写下的一句假引文**：本节 Discord 那条一开始只抄了社区页那句的一半——`英文即时聊天类的 Discord 链接都会跳到邀请页` 中间被我省掉了原文的一段括号（`（HF / Anthropic / EleutherAI）`），于是那六个字在书里根本不存在。第 55 轮落库的 `check_quote_fidelity.py` 把它读成 `UNMATCHED 00-index/changelog.md:72`，改回逐字一致后 `findings 1 → 0`、`verified 17 → 18`。**日志不豁免于书的规矩**：这一轮的改动是「每条结论都要点得回一手来源」，而新写的日志差一点就引用了一句不存在的话。抓它的不是我的眼睛，是常驻判据——如果没有那条判据，这句假引文会作为「本轮交付说明」上线。
- **本机的浏览器腿现在是瞎的，六条渲染轴本轮没能复跑**：`check_mermaid_geometry` / `check_svg_fit` / `check_svg_legibility` / `check_svg_phase_legibility` 全部报「no report / ruler never ran」，`check_table_overflow` / `check_content_overflow` 的线上腿报 `NOHYDRATE`（8 页各读到 0 个单元格，判据自己把它归为「harness/CDN，不是内容判决」）。Edge 那条不是内容判决，是探测器故障，而且是**量出来的**：同一份最小页面，Edge `--dump-dom` 在六种 flag 组合下（`--disable-gpu` / 加 `--use-angle=d3d11` / 不加、`--headless` 旧模式、`--no-sandbox`、`--no-zygote`）**一律 rc=0、stdout 0 字节、stderr 0 字节**——把 URL 交给一个已在运行的浏览器进程然后自己退出，就是这个签名；而 Playwright 自带的 chromium 在同一台机器上正常（同一趟：DOM 里取到哨兵、截图 8164 字节）。本轮 diff 对这些轴**没有本地输入**：`assets/` 下 0 个文件被改，35 个改动文件里 0 行提到 `mermaid` / `.svg` / `![`（复测见下）。**但「没有输入变化」只是覆盖率论证，不是通过**：这六条轴本轮未复跑，记为缺口；把它们换到 chromium 引擎是下一轮的头号工具项，而换引擎必须先按第 75 轮的规矩重新锚定（引擎版本、字体度量和 `--use-angle` 真 GPU 分支都会挪阈值，未经重锚的新读数不许判红）。**这一句只覆盖那六条常驻轴**：本轮流程要求的「真实渲染截图目检」并没有被省掉——它用 chromium 单独跑了一遍，四个页面、四条腿、四张元素级截图，逐条读数与它顺手抓到的两处见第七节。
- **本轮新暴露的一条覆盖缺口：读者侧真浏览器与判据探针可以对同一个地址给出相反结论，而这条分歧没有判决兜着**。第七节量到的那次地区闸门跳转（浏览器腿 3/3 被 `307` 送到 `claude.com/app-unavailable-in-region`，判据腿 2/2 落在自身）落在采纳闸门的口径之外：`--live` 那条腿只回答「这个 href 在不在读者拿到的 HTML 里」，不追跳转落点。要把这类分歧变成判决，得给读者侧腿加一条「跟随跳转后落在哪」的**抽样**（不是全站 717 条，那会把 CDN 打成限流），而且按第 75 轮的规矩先重锚。本轮不建，记为工具项。
- 前几轮记过、本轮没碰的产品级取舍照旧：宽版布局开关、`--column 1152` 复跑超宽图、lab 页 transcript 逐行等值判据（先给「节选 / 重排 / 交互输入」定形状）、线上正文完整性轴、措辞可读性轴。

### 七、读者侧复核：这一轮改的是链接的**目标**，所以抽查不能读散文

第 80 轮的抽查采的是可见散文。本轮不行——`Anthropic Computer Use` 这个标签改前改后**一模一样**，读散文的探针会自信地报告「一切正常」。所以探针改成解析服务端 HTML 里的 `<a href>`，每页四条腿：`NEW` 新地址必须是 href、`OLD` 旧地址在 href **和整页未转义 HTML** 里都必须为 0、`CONTROL` 本页一直引用的主机必须还在（证明提取器没瞎）、`PHANTOM` 一句从没写过的地址必须不在（证明提取器不是什么都匹配）。

**推送前先跑了一遍当基线**：10 个案、`problems=20`，而每个 FAIL 页的 `control>0`、`phantom=0`——四条腿全部可发射，这条红是内容还没上线，不是探针坏了。这一趟也顺手把第一条版本的一条**假正控制**抓了出来：TechCrunch 那个 needle 原本只写了裸主机名，服务端**旧**页面上就已经命中（`new=1`），因为该页别处也引用这家站；换成带日期路径的完整形状后旧页面读 `new=0`。同时这也是第 80 轮那条「目检证据不许是被格式化过的字符串」的第三次现身：**会话的文件读回显示会把 URL 里的 `/2026/09/18/` 印成连字符形状**，两条不同的 URL 在显示器上长得一模一样——本轮所有 URL 判等改用逐字符 `ord()` 打印与运行时拼接字符串，日志里因此刻意不抄那两条 URL 的原文。

**第 80 轮欠的那次线上复核**也在这节量掉了：`check_live_sync.py` 在本轮开头读到 `HEAD 提交于 108 分钟前 / leg md 最新=80 / leg html 最新=79（缺 80）`。`.md` 端点先同步、读者可见的 HTML 后腿——这与第 74 轮记的那条平台事实一致，本轮把它量成了具体分钟数。推送第 81 轮之后两腿的复跑读数见本节末尾的收尾补记。

**收尾补记（推送之后重跑的读数，逐条来自日志文件而不是记忆）**：`check_updated_dates` 从推送前的 `pending-commit=26` 回到 `reader pages=198 checked=196 exempt=2 problems=0 pending-commit=0 unreadable=0`；`check_changelog_headings` 读到 `HEAD=73 tree=73 lost=0`；`check_live_sync` 读到 `HEAD 提交于 21 分钟前 / leg md 最新=81（128 轮）/ leg html 最新=79（439 轮）缺 80、81`，末行仍是 `not online yet`。**最后这行不许被读成「第 81 轮没上线」**：本轮的读者侧 href 探针在 10 个改过的正文页的**服务端 HTML** 上读到 `pages=10 problems=0`（每页 `new>=1 / old=0 / control>0 / phantom=0`），滞后的只有更新日志这一页自己的 HTML——下一节把「按页同步」量成了具体形状。

**真渲染目检这一趟换了引擎**：Edge 那条腿是瞎的（第六节），所以按第 75 轮的规矩临时用 Playwright 自带的 chromium 跑读者侧渲染（`--use-angle=d3d11`、1280 视口、每页等 6 秒水合），并把本轮改过的四个正文页各量四条腿。读数 `pages=4 problems=0 shots=4`：
- `12-applications/rpa.md`：新地址 2 个锚点（一页可以引用同一目标两次，这是第一版探针没料到的）、旧地址 0、控制主机 5，作者文件里的 2 条标签全部到达读者（`Anthropic 文档` 124×20、`Anthropic Computer Use` 201×20）；
- `13-resources/communities/README.md`：自动链接 1 个锚点、以 URL 自身为文字（121×59，在窄列里折成三行）、旧地址 0、控制 1；
- `09-frameworks/llamaindex.md`：2 个锚点（`文档` 46×20 / `LlamaIndex 官方文档` 169×20）、旧地址 0、控制 1；
- `README.md`：`OSWorld` 1 个锚点、旧地址 0、控制 34。

四张元素级截图逐张看过：紫色链接文字带外链箭头，标签与作者文件逐字一致。**这一趟也顺手抓到两处，一处是工具错，一处不是**——见下两段。

**目检抓到的第一处是探针自己的错**：截图选择器写的是 `a[href*='<路径最后一段>']`，而 llamaindex 那条 URL 的最后一段是 `framework`，侧栏的 `09 框架与生态 · 本章导读` 也含这个词——于是那张 PNG 拍下来的是导航，不是引用。锚点腿本身没错（它匹配完整 fragment），但**图片是证据**，而一条没人核对过的选择器足以让一张「目检通过」的截图指向另一个元素。修法是选完整 fragment，并加一条断言：被拍下来的那个元素必须是这一趟报告过的锚点之一、其文字必须等于作者文件里的某个标签。重拍两页 `problems=0`。

**目检抓到的第二处不是错，是两条腿对同一个地址给出相反且都可复现的读数**：本轮采纳的 `platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool`，判据腿（urllib，带 UA/Accept/Accept-Language/Accept-Encoding）在同一分钟内 2/2 次落在自身、`200`、服务端 `<title>` 为 `Computer use tool - Claude Platform Docs`；浏览器腿 3/3 次被 `307` 送到 `claude.com/app-unavailable-in-region`。第三组对照排除了 HTTP 头这一层解释：用 urllib 带上浏览器 UA + `Sec-Fetch-Mode: navigate` 仍然落在自身，裸请求 `403`，只带 UA 的那次 TLS 直接断流。所以分歧在**客户端指纹层**——CDN 把无头浏览器当 app 导航、按地区闸门处理，而把 Python 客户端放行到文档。**本轮不改这条引用**：旧地址是同一套文档的上一个家，换回去只会更糟；但这条量到的分歧说明采纳闸门的「落点等于自身」是**判据腿口径**，于是它进了第六节的遗留清单，而不是被写成一句「读者应该没问题」。



## 2026-09-24（第 80 次）「六个实验的脚本仍在仓库 `labs/` 下可离线真跑」这句也被真跑了一遍才敢写——落库 `tools/checks/check_lab_runnability.py`，第一趟就抓到 `lab5` 的瀑布图每次漂一格（第 54 轮当时记成「非种子能定」），本轮改成模拟时钟，并把页面里那三段引文一起重生成

本轮新增 1 个判据文件 + 改 `labs/lab5_eval_trace.py` 一处 + 重生成 `labs/out/lab5.out` + 改 `docs/19-labs/lab5-eval-trace.md` 三段引文 + 改 `docs/README.md` 一条统计句 + 本日志。

### 一、同类缺陷第六次；这条主张的是行为，所以只能真跑

第 57 / 76 / 77 / 78 / 79 轮量的是「树上有什么」，这一条主张的是「跑起来会怎样」：首页与六个实验页都写着脚本可离线真跑、页面里贴的是真跑原样。`tools/checks` 里搜不到任何执行过它们的代码——判这类主张没有捷径，只能把六个脚本各跑两遍。

### 二、判据量什么

`tools/checks/check_lab_runnability.py`，每个脚本在 `labs/` 的**临时副本**里连跑两遍（脚本会往当前目录写 `traces.jsonl`，就地跑会把仓库弄脏）：

| 判决 | 含义 | 本轮树上 |
|---|---|---|
| `LAB-EXIT` | 退出码非 0 | 0 |
| `LAB-EMPTY` | 退出 0 但 stdout 一个字没有（「跑通了」不能是空话） | 0 |
| `LAB-NONDETERMINISTIC` | 两遍 stdout 逐字节不同 | **首跑 1 → 修完 0** |
| `OUT-STALE` | `labs/out/labN.out` 那份入库记录 ≠ 今天重跑的输出 | 0（6/6 相符） |
| `PAGE-NO-SCRIPT` | 实验页没有点名它对应的脚本 | 0（6/6） |

读数：`labs=6 exit0=6 deterministic=6 stdout_lines=141 worst=0.63s pages=6 pages_naming_script=6 records_current=6/6 findings=0`。六个脚本全部跑完只要 0.63 秒，所以这条判据可以常驻每一轮。

### 三、首跑抓到的一处真缺陷：`lab5` 的瀑布图每次漂一格

`agent_solve()` 里 `start` 读的是 `time.perf_counter()`，而 `dur` 由 `random.seed(42)` 钉死。`time.sleep(dur)` 每次返回得比 `dur` 晚几微秒，这些余量累进 `start`，于是瀑布图的**缩进**逐次不同——两遍输出差 1 字节、一行差 1 个空格。第 54 轮的日志当时就记了这条：「lab5 只有瀑布图一行的前导空格漂移（`start` 读真实时钟，非种子能定）」，页面里也留了一句提醒读者「别去对那串 16 位小数」。

本轮把它判成可修的：span 是**顺序**发生的，所以 `start` 本就该等于「上一条的 `start + dur`」——改用模拟时钟后既完全可复现，也更符合这张图想教的东西（真实时钟那点余量对读者理解 span 契约没有任何信息量）。

### 四、代码改了，页面引文必须跟着改

`lab5-eval-trace.md` 里三段是「真跑原样」：`traces.jsonl` 第 1 行、瀑布图整块、以及那句「`start` 每次跑都不一样」。改完脚本后前两段随之一变（`start` 变成 `0.0 / 0.0228 / 0.0753`，`c1 answer` 的条长按新时钟重算为 5 格），第三段从「提醒读者别去对」改写成**历史交代**：为什么第 54 轮只能那么写、本轮改了什么、现在这串小数是可以对的。**没有把旧的提醒悄悄删掉了事**。六份入库记录逐份与今天重跑的输出对过：只有 `lab5.out` 两行变化，其余五份一字不差——这一条是量出来的，不是「应该没变」的推测。

### 五、控制与一次自我修正

- **6 条种植控制**：一份干净脚本（含相符的入库记录）必须全不报；退出码 3、只退出不出声、未播种随机、**一份与今天输出不符的入库记录**必须各自被抓。
- **本轮第一次「六份记录全过期」是我自己量错的**：我用一段一次性命令比对时拿的是子进程的**原始字节**，而 Windows 会把 `print()` 的 `\n` 在管道上翻成 `\r\n`——五份明明相符的记录被判成过期。判据里显式做了换行归一化（`norm_newlines`），并把这条写进注释，免得下一个人以为归一化是多余的好心。**症状记下来**：如果一次改动让「所有」同类对象同时变红，先怀疑比较口径，再怀疑内容。
- **第二次自我修正发生在目检那一步，而且差一点就写出一条假缺陷**：我把线上瀑布图那一行的上下文用 `re.sub(r"\s+", " ", …)` 折叠空白后打印，看起来像「平台把前导空格吞了、这张图对读者根本不成其为图」。重测时改成直接写 `repr()`：服务端原文是 `'  c1 answer                    |####| 28ms'`，前导 2 格、内部对齐空格**一格不少**，与作者文件逐字一致。**教训**：目检证据里凡是被格式化过的字符串都不算证据——先看原文（`repr` / 原始字节），再决定要不要写进日志。这条与本轮第一条是同一个形状：**两次「红」都是我的输出层在骗我**。
- **目检（本地真渲染 608px 列）**：改过的两段（trace 第 1 行与瀑布图）单独排一页截图看过——等宽字体、前导与内部空格全部保留、13 条 span 按开始时间阶梯排开，`c1 answer` 的条长随新时钟从 4 格变 5 格。这张图的意义（横位置＝什么时候开始）在读者那一列里是成立的。

### 六、留下了什么

- **候选轴「页面里贴的 transcript 必须逐行等于真跑输出」被量过，判定为现在不能建**：六页 126 行 `text` 引文里有 40 行按整行不在今天的输出里。逐条看下去分三类——① 读者自己输入的那一行（脚本非交互跑时根本不打印）；② 页面对 JSON 做了换行重排（脚本输出是单行）；③ 页面只节选中间几步。三类都**不是**内容造假，但都需要判据先认识「节选 / 重排 / 交互输入」这三种形状才能判。按第 74 轮的先例（一个候选被测量判死，本身就是交付），这条不进判据；要做就先给这三类定形状，别用一行包含关系硬判。
- **`yaml` 契约仍未过解析**（与第 79 轮同因：没有钉在仓库里的 YAML 解析器），本轮不补。
- **`lab5` 之外五个脚本没有随机性问题**，但它们的可复现性现在由判据兜着：任何一轮引入未播种随机都会立刻 `LAB-NONDETERMINISTIC`。
- 前几轮记过、本轮没碰的产品级取舍照旧：宽版布局开关、`--column 1152` 复跑超宽图、线上正文完整性轴、措辞可读性轴。

### 七、线上复核（这一节当时没写，量于第 81 轮收尾）

第 80 轮推送后没有写读者侧证据，日志因此停在「本地目检」。这一节把它补上，并且刻意**不从记忆里取 needle**：needle 由 `git show 81477a1` 的新增行与删除行当场切出来（第 78 轮那次 MISS 就是照着截图手抄的），切之前先按 markdown 语法字符（`*`、反引号、方括号）断开——否则一条含 `**加粗**` 的 needle 只可能在 HTML 腿上 MISS，因为读者拿到的是标签而不是星号。第一版正是这样：它切出一条 1531 字符、满是星号的 needle。

四条腿 = 2 页 × 2 端点（读者可见 HTML 与 `.md` 端点），每页三条判决：`NEW` 必须出现、`OLD` 必须为 0、`CONTROL`（本轮之前就在页上的字符串）必须 >0。读数 `problems=0`：

- `19-labs/lab5-eval-trace.md`：HTML `new=1 old=0 control=34`，`.md` `new=1 old=0 control=4`。`NEW` 是改后那三段 span 的完整 JSON 片段（222 字符，`plan` 的 `start` 现在是 `0.0`），`OLD` 是改前那一段（238 字符，`start` 是 16 位真实时钟小数）。**服务端确实换了**，读者不会再读到那一串小数；页面里那句改写后的历史交代同样在 HTML 里。
- `README.md`：HTML `new=3 old=0 control=58`，`.md` `new=1 old=0 control=9`（首页那条统计句；HTML 读到 3 次是服务端把同一句同时放进正文与页面数据，不是重复发布）。

顺带把第 74 轮那条平台事实量成了具体形状：**HTML 同步是按页的**。第 81 轮收尾时更新日志那一页的 HTML 腿仍停在 79（`leg html 最新=79 缺 80、81`），而第 80 轮真正改到的这两个正文页 HTML 已经是新的。所以 `check_live_sync.py` 报 `not online yet` 时，先分清是哪一页没上线，再决定要不要动内容——这一条也因此写进了第 81 轮的收尾补记。



## 2026-09-24（第 79 次）首页那句「正文零可执行代码（每份契约都过 `json.loads`）」同样没有判据——补上 `CODEFENCE` 与 `JSONCONTRACT` 两条判决时，先发现**两条判决脚下的围栏分词器是错的**：它把「任意一行同字符围栏」当闭合，而 CommonMark 要求闭合行不带标签且不短于开场

本轮改 3 个判据文件（`check_structure.py` 两条新判决 + `live_aria_manifest.py` 分词器修正与两个新入口）+ 改 `docs/README.md` 一条统计句 + 本日志。**读者页正文 0 处改动**。

### 一、同类缺陷第五次；这次连「已经修好的那条房规」都没人守着

第 54 轮按操作者的决定清掉了正文里所有可执行代码（55 页 / 60 块 / 1502 行），此后首页一直写着「正文零可执行代码」和「每份都过 `json.loads`」。第 79 轮在 `tools/checks` 里搜 `EXECUTABLE` / `fence_lang` / `可执行`：**一条判决都没有**。也就是说这条房规靠每轮自觉维持了 25 轮——任何人加一个 ```python 块，全站判据会照常全绿。这类缺陷的形状到这里第五次：57（判据不在仓库）、61（让读者看出处却不给链接）、76（图注三个数）、77（组件清单五个数）、78（每章三件套）、79（一条房规）。

### 二、修尺子在前，加判决在后

新判决依赖「哪些行在围栏里」这个映射，而这个映射仓库里有**两份实现**（`check_structure.outside_fences` 与 `live_aria_manifest.outside_fences`），两份都写错了同一条：

| 规则 | CommonMark / 平台 | 旧尺子 |
|---|---|---|
| 闭合行能不能带语言标签 | **不能**（带标签的行是内容） | 无视标签 |
| 闭合行长度 | **≥ 开场行**（4 个反引号的块不能被 3 个闭合） | 一律归一到 3，见同字符就闭合 |

后果不是理论问题：`14-templates/knowledge-template.md` 用四个反引号包住「含三个反引号示例的模板」，旧尺子在示例内部第一个 ``` 处就把大块关掉，**13 行读反**——示例的内容被当正文（可能凭空生判决），大块后半段真正的正文被当示例（可能吞掉判决）。

**改之前先问读者那一侧**：抓线上那张页面，看被争议的那几行在什么元素里——服务端把它们包在 `highlight-line` / `highlight-line-content` 里，即**平台按 CommonMark 渲染，不按旧尺子**。方向定了才动手。

修法是把规则收进**一处**（`live_aria_manifest.fence_prose_mask`，另配 `fence_blocks` 供需要块内容的判据用），`check_structure` 改为委托，两份实现合成一份。第 71 轮那句教训（两把围栏尺 = 同一棵树两个读数）这次是提前用上的。

### 三、两条新判决与全站读数

- `CODEFENCE`：围栏语言标签不在数据白名单（`mermaid`/`json`/`yaml`/`text`/`markdown`/无标签）内即判红。
- `JSONCONTRACT`：每个 `json` 块必须真过 `json.loads`。这条把首页那句「每份都过解析」从好话变成读数：**79 份全部解析通过**。
- 全站读数（判据自己打印）：`fences: mermaid=217 json=79 text=52 markdown=11 yaml=10 (no tag)=8 | executable-tagged=0 json contracts parsed=79 unclosed=0`，`pages scanned=198 problems=0`。
- 顺带一条只有修好的尺子才判对的：**模板页里那个示例 json 不该被当成真契约**。旧尺子以为大块在示例中间就闭合了，会把这段示例文本当成读者要抄的契约；新尺子知道它还在大块里，不判。

### 四、控制：两侧都要响，还要证明新尺子不是白改

- **语言标签**：`python`/`bash`/`js`/`sql`/`console` 五种必须被抓；`text`/`json`/`yaml`/`markdown`/`mermaid`/无标签六种必须不抓。
- **契约**：带尾逗号的 json 必须被抓，合法的必须不抓。
- **分词器差分（关键的一条）**：判据在**真实页**上同时跑新旧两把尺子，断言两者确实读数不同、且差异落在嵌套示例那几行（`平方膨胀…`）。这条断言的意义是：将来有人把规则「简化」回去，控制会先红，而不是留下一个安静少扫 13 行的尺子。
- **嵌套形状**：四反引号块内的三反引号行不得被当成开场（`fence_blocks` 只应报出 `text` 与 `markdown` 两个开场），示例内部的标题不得被 `HEAD` 判成 TOC 泄漏，而同样一行写在正文里必须被抓。
- **回归**：分词器一改，读它的判据全跑一遍——公式 `pages=108 formulas=927 failures=0 @0.18.7`、图注 `pages=197 diagrams=217 placements=45 captions=215 quoted=8 findings=0`、跨页重复、引用回核、字符、导航、组件配平与清单、每章三件套、表格/正文溢出、日期、changelog 标题、README 统计，15 条离线腿全部 exit 0。
- **诚实到位的一句：这次修尺子没有改变任何一条判决**。第 78 轮那批读数原样复现（唯一按设计变化的就是本轮新打印的围栏计数行；正文 CJK 总量 380044 → 381759 是本轮写字自己加上去的 +1715 字，属于每轮都会动的分母）。那 13 行读反的文本恰好不含任何下游判据 keyed 的东西（标题、`$$`、转义反引号、图片引用），所以旧尺子的错误一直没被看见。本轮修它的理由不是「今天有判决错了」，而是：① 新加的两条判决**必须**建立在正确的块映射上，否则 `JSONCONTRACT` 会把模板里的示例 json 当成读者要抄的契约去判；② 这类错误是潜伏的——下一次有人在嵌套示例里写一个带 `$$` 的标题，判决就会指错地方。**别把「修了没让数变」当成白修**，也别反过来把它吹成「抓到重大缺陷」。

### 五、留下了什么

- **`markdown` 与「无标签」两种围栏本轮第一次被计入白名单**：白名单是**量出来的**（这 6 种就是树上实际存在的全部标签），不是先验规定。将来引入新数据语言要先加进白名单并给理由，否则 `CODEFENCE` 会直接红——这是有意的摩擦。
- **`yaml` 块没有过解析**：环境里没有可靠的 YAML 解析器可钉版本（第 59 轮公式引擎的教训是「解析器版本必须钉在仓库里」），所以宁可不判也不假判。要做的话，先钉一个与平台一致的解析器再谈。
- **`unclosed=0` 是这次才真正可信的**：旧尺子的闭合规则会自己制造「已闭合」的假象，所以它报出的平衡从来不算证据。
- **`labs/` 六个脚本「可离线真跑」这句仍未判**：本轮判的是正文与契约，脚本运行是另一条轴（要跑真 Python 并比对 `labs/out/`），留下轮。
- 前几轮记过、本轮没碰的产品级取舍照旧：宽版布局开关、`--column 1152` 复跑超宽图、线上正文完整性轴、措辞可读性轴。

### 六、线上复核（本轮收尾）

- **同步门**：推送后约 1 分钟，`check_live_sync.py` 两腿同时到第 79 次（`exit=0`）。
- **读者侧抽查 6/6**：首页那条改写过的统计句取 3 段、本日志第 79 次标题取 3 段，全部在发布页的可见正文里读到；每页另配一句从没写过的幽灵文本，全部读不到。本地渲染目检：改写后的首页那条项目在读者 608px 列里排版正常（粗体、行内代码都渲染，没有漏出 Markdown 记号）。
- **抽查探针本身改了一处设计，因为第 78 轮被它骗过一次**：那轮报的 1 条 MISS 是我**照渲染截图手抄**针时把「这章」抄成「本章」——同音、同义、差一个字，长得就像内容缺陷。本轮起探针**从作者文件里按位置切片取针**（三个分位各取 18 字），抄写这一步在流程里不存在了，这类错误也就没有了入口。

## 2026-09-24（第 78 次）首页那句「每章三件套：全量覆盖，题目可答、答案有出处」同样没有判据——落库 `tools/checks/check_chapter_extras.py`，51 道题的出处腿全过，但首跑抓到三处：两行合法术语被尺子切成坏行（转义竖线），一行术语的中文列真的没有中文

本轮新增 1 个判据文件 + 改 `docs/README.md` 一条统计句 + 改正文 1 行（`19-labs` 术语表）+ 本日志。

### 一、同类缺陷第四次现身，而且这一次它藏在一句「全量覆盖」里

第 57 轮（公式判据不在仓库）、第 76 轮（图注三个数没有判据）、第 77 轮（组件清单 251 早已失真）之后，首页还剩一句主张从来没有脚本产出过它：**「每章『读完能做到』清单 + 章末自测 + 中英术语速查：全量覆盖，题目可答、答案有出处」**。这句话比前几句更值得量，因为它同时主张**覆盖**（每章都有）与**质量**（题目可答、答案有出处），而这两件事都需要判决词而不是形容词。

### 二、判据量什么

每章的 `README.md` 三条腿，阈值写死在文件顶部（`MIN_GOAL=3 / MIN_QUESTIONS=3 / MIN_TERMS=10`）：

| 判决 | 含义 | 本轮树上 |
|---|---|---|
| `MISSING-GOAL` / `THIN-GOAL` | 没有「读完能做到」，或条目少于 3 | 0 |
| `MISSING-QUIZ` / `FEW-QUESTIONS` | 没有章末自测，或少于 3 题 | 0（1 章按页面原句豁免，见第四节） |
| `NO-SOURCE` | 一道题没点任何出处 | **0 / 51** |
| `DEAD-SOURCE` | 点了出处但那个文件在仓库里不存在 | **0** |
| `MISSING-GLOSSARY` / `THIN-GLOSSARY` | 没有术语速查，或行数少于 10 | 0 |
| `BAD-ROW` | 术语行有空列，或英/中/白三列形状不对 | 首跑 2 → 修尺子后 1 → 补内容后 **0** |
| `EXEMPT-UNSUPPORTED` | 挂在豁免名单上，但页面里支撑豁免的那句话不见了 | 0（控制腿让它必须能响） |

`with_source=51` 是这句话里最硬的部分：51 道题**每一道**都点了出处，而且指向的文件都在仓库里——「题目可答、答案有出处」本轮第一次被机器读出来。

### 三、首跑三处，两假一真

- **假的两处是同一把尺子的错**：`09-frameworks` 与 `19-labs` 各有一行术语被判 `BAD-ROW`，理由「列数不对」；实际那两行的白话列里写着**带反斜杠转义的竖线**（GFM 里那是单元格内的一个字符，不是分隔符），而我的切分写成了「逢竖线就切」，于是 3 列被切成 5 列。改成只切未转义的分隔符，并常驻一条反例：带转义竖线的行必须读干净、且行数不许变。这与第 57 轮「标签属性里的裸 `%` 截断了块标签」、第 25 轮「行内代码里的写法示例被当成真链接」是同一类——**分隔符级别的错误总是伪装成内容级别的缺陷**。
- **真的一处是一行没有中文的中文列**：`19-labs` 术语表里 `JSON-RPC 2.0` 那一行，中文列原样写着光杆的 `JSON-RPC`。全书 198 行里**只有这一行**中文列不含中文字符，而本书对「没有通用译名」早有既定写法（`BM25 | （关键词检索评分，通用译名）`）。按那个格式补成「JSON 远程过程调用（通用译名）」——**加字不改义**，那一行的白话列本来就写着「一行一条 JSON 的远程喊话规矩」。

### 四、豁免不许是一张名单，要钉在页面自己那句话上

`15-glossary` 没有章末自测。查页面发现它**早就写着**：「本章是纯查表页，不出自测题——取而代之，记住用它的三条路」。所以这不是缺陷，是一个已经做过的产品决定；缺陷在于判据如果只把章名写进 `EXEMPT_QUIZ`，那它就成了一张可以随手加名的白名单。于是豁免改成**由页面原句支撑**：名单里记的是那句话本身，判据要求页面正文包含它才免判；把它删掉，这一章立刻从「豁免」变成 `EXEMPT-UNSUPPORTED`。控制腿双向钉住：带那句话 → 0 判决且 `quiz_exempt=1`；不带 → 必须响。

**没有为了让 17 变 18 而给术语章塞一道自测题**——那正是「为凑指标动内容」的反面，而页面自己那句话就是它不该有题的证据。

### 五、控制与本轮的自我修正

- **14 条种植反例**：一份完全合规的章页必须读干净（正控制，含 3 题 3 出处 12 行术语）；7 条各自必须被抓（缺自测、题数不足、题没出处、指向不存在的文件、目标清单太薄、术语行留空列、中英形状错位）；豁免两个方向；转义竖线两条（必须读干净、行数不许变）。
- **本轮第一次红是红在控制上**：那条「豁免」控制一开始切错了小节——它切掉的是术语段而不是自测段，于是被判据正确判成「仍有 3 题」，而我的断言在等 `quiz_exempt=1`。修的是控制并在代码里留了话，免得下一个人再切错一次。
- **读数**：`chapters=18 goals=18 quizzes=17 quiz_exempt=1 questions=51 with_source=51 glossaries=18 terms=198 findings=0`，`controls ok (14 planted…)`，exit 0。

### 六、留下了什么

- **阈值 3 / 3 / 10 是一次判断而不是测量**：全站实际读数是每题 3 问、每章 11–14 行术语，所以这三条线今天一条都没裁到内容——它们是回归线，防的是未来某轮把某章的自测删剩两题。改阈值必须同时改反例。
- **「出处」只判**文件存在，不判那一页是否真的回答了这个问题（那需要语义判断，属于第 68 轮记过的「措辞可读性」那条还没做的轴）。
- **`goals=18 / quizzes=17 / glossaries=18` 只判章导读页**（`NN-名/README.md`）；章内其它页不承担三件套，这是房规而不是遗漏。
- **`terms=198` 不含 `15-glossary` 自己的那张全书总表**（它按主题分节、没有「术语速查」这一节标题），所以 198 是「每章小表」的数，不是「全书术语总量」。两个数若要一起报，得先给总表定一条判据。
- 前几轮记过、本轮没碰的产品级取舍照旧：宽版布局开关、`--column 1152` 复跑超宽图、线上正文完整性轴、措辞可读性轴。

### 七、线上复核（本轮收尾）

- **同步门**：`check_live_sync.py` 两腿都翻到第 78 次——`.md` 腿第 2 次轮询就到位，渲染 HTML 腿到第 7 次（推送后约 13 分钟）才跟上，`exit=0`。又一次说明**两腿必须分别量**：只看 `.md` 会把「GitBook 拉到了」当成「读者拿到了」。
- **读者侧抽查**：3 页 6 条针全部命中——`19-labs` 那行改过的中文译名、它上下那句白话解释、`15-glossary` 页面里那句豁免原话（判据依赖的就是这一句，所以它到不到读者手里不是无关紧要）、首页新增的「17 章章末自测共 51 题」与判据文件名；每页另配一句从没写过的幽灵文本，全部读不到（探针不瞎）。
- **第一次抽查报了 1 条 MISS，错在探针**：我把针抄成了「**本**章的术语都是…」，作者文件里写的是「**这**章的…」。先在仓库文件里 grep 到原句、确认差异在探针一侧，再改针重跑得到 6/6。**抄针要从文件复制，不要从渲染图上看**——截图里那两个字我读错了，而读错的方式恰好是最不容易自查的那种（同音、同义、字形相近）。


## 2026-09-24（第 77 次）首页那句「251 个提示卡 + 54 组分步演示（279 步）+ 52 组标签（195 个页签）」里，只有 251 是错的——它是第 54 轮一次手抄，此后 20 多轮树长到 257 而句子一个字没动。落库 inventory 腿（并进既有的配平判据，不新开一把尺），其余四个数原样复现

本轮新增 1 条判据腿（`tools/checks/check_widget_pairing.py` 的 inventory 部分）+ 改 `docs/README.md` 一条统计句 + 本日志。**读者页 0 处改动**。

### 一、这类缺陷第三次现身，前两次都记在同一本书里

「README 印着一个 `tools/checks` 里没有任何脚本能产出的数」不是新问题：

- 第 57 轮：README 引用的公式判据**压根不在仓库里**，同一棵树同时有过 930 / 931 / 943 三个数；
- 第 76 轮（同一天前半段）：图注那句 215 / 171 / 46 从来没有判据，落库成 `check_figure_explanations.py`；
- 本轮：组件清单句的四个数里，**一个已经失真**（提示卡 251 → 实测 257），另外四个（54 / 279 / 52 / 195）恰好还跟着树。

第三点值得单独说清，因为它比「数抄错了」更危险：**五个数里四个是对的**，所以任何「抽查一下这行」的人工复核都会通过——抽查看见的是那几个还没漂移的数，而漂移的那一个读起来同样自信。这类缺陷不可能靠读首页发现，只能靠让判据去读首页。

### 二、判据量什么，以及为什么不新开一个文件

- **同一把尺**：inventory 腿复用配平腿（同一文件里那把 `TOKEN` + `in_fence_flags` + `INLINE_CODE`）走完一遍树，按标签名点数**开启标签**。若另写一个正则计数器，同一棵树就会有两个都能自圆其说的数——第 57 轮那三个公式数就是这么来的。
- **它读的是首页那句话本身**：判据用一个正则把句子里的五个数字解析出来（提示卡 / 分步演示组 / 步 / 标签组 / 页签），再与树对平。句子被改写成别的形状时判据直接失败并要求重指正则，**不会**因为读不到而静默变绿。
- **等号与地板的分工**（第 76 轮刚立下的规矩，本轮立刻套用）：句子里那五个数钉**等号**——首页有义务跟着树走，读者抄不走它，因为数就印在句子里；`hint ≥ 250`、`stepper ≥ 50` 这类总量钉**地板**，它们会随页面增删移动，钉等号就是给正常的写作收税。
- **口径要证明它咬得动**：句子声明「代码块与行内代码里的写法示例不计入」，判据就把同一棵树**不剥**围栏与行内代码再数一遍，断言两者之差大于 0 并打印（提示卡 23、分步演示组 8、标签组 11、页签 7、步骤 6、可展开块 1）。不这么做的话，「排除示例」这句可以悄悄失效而读数完全不变。

### 三、量到多少，改了什么

- 判据首跑（改首页之前）：`AssertionError: README inventory disagrees with the tree (claimed, measured): hint 251 vs 257`——**五个数里只有一条红**，其余四条一次对上。这正是本轮想要的形状：缺陷是具体的一个数字，不是一句「统计不可信」。
- 修法只有把 251 改成 257 并补上判据指向与口径读数。**没有为了让别的数不变而动任何一页正文**：五个读数里四个本来就对，唯一的改动在首页那一行。
- 点数读数（写本日志之前那一趟，判据与独立脚本各跑一遍、结果相同）：`inventory: hint=257 stepper=54 step=279 tabs=52 tab=195 | excluded quoted-in-markup mentions: hint=23 stepper=8 tabs=11 tab=7 step=6 | pages carrying a widget=189`，同一文件配平腿 `pages=198 problems=0`，exit 0。五个主读数到此为止全部与首页那句相等；**后面那串「排除了多少」不是稳定的**，见 §四 最后一条。

### 四、控制：8 条种植 + 一次独立口径交叉

- **8 条种植反例**（全部常驻判据内部）：真实一处提示卡必须被点（正控制）；围栏里的一处必须不点；行内代码里的一处必须不点；`endhint/endtabs/endtab/endstepper/endstep` 五个结束标签合起来必须读成 0 次开启；`{% tabs %}` 套两个 `{% tab %}` 必须读成 1 组 2 页签；`{%- hint -%}` 这种空位控制写法必须照点；标题属性里含裸 `%`（`title="±1% 容差"`）必须照点而不被截断；一个 `stepper` 套两个 `step` 必须读成 1 组 2 步。前两条与第四条是**排除侧**（多算就会虚高），第五条是**归属侧**（组与成员混数）。
- **交叉验证不是第二把尺而是第二种数法**：另写的手写围栏状态机（只剥围栏、不剥行内代码）读 277，判据读 257，差的 20 处分布在 18 行里——**18 行逐行看过**（本首页 1 行、更新日志 16 行、贡献指南 1 行，行号是本轮改动前的），每一行都是在解释这套语法时把标签写进反引号的写法示例。两个数因此不是分歧而是同一条口径的两端：读者会遇见的卡片 257，树里出现过的标签文本 277。
- **写这段字本身推动了三条「被排除的示例数」**：判据首跑读 `hint=23 tabs=11 tab=7`，等本轮把这些语法写进反引号做示范之后再读 **24 / 12 / 8**。五个主读数一个没动（257 / 54 / 279 / 52 / 195），因为示例本来就落在排除侧——**被推动的是「排除了多少」这一个数**。于是首页那句最终**没有印**这五个排除数，只写「由判据自己逐名打印」并给理由。第 76 轮立下的「措辞能推动的数不配当等号」到这里长出一条推论：**措辞能推动的数连印在首页都不配，只配一个指向判据的指针**——否则本轮就是亲手又造了一个第 54 轮那种会慢慢发假的数字。
- **配平腿本来就是这套标签的守门人**：它一直读 `pages=198 problems=0`，所以本轮不是新发现一处结构问题，而是给一个已有 0 问题的结构补上「印在首页的那个总数」这一层。

### 五、留下了什么

- **inventory 只回答「首页那句与树对不对平」**，不回答「读者有没有真的看见一个可折叠卡」。后者是 `check_widget_visibility_live.py` 的轴（它读组件标题与正文片段是否出现在线上页面），两条腿各管一件事，不要把本轮的 257 读成「257 个组件已在线上渲染」。
- **`pages carrying a widget=189` 只是打印，没有断言**：它会随写作上下移动，且首页那句话没印它。真要判它，得先定「带组件的页数」这条口径归谁管。
- **步数与页签数只数开启标签**，不数 GitBook 渲染后实际生成的步骤 DOM。线上那一层已由可见性轴覆盖，此处不重复抓取。
- **「作者写的 `updated:` 与页面角标那个平台时间差多少」这条候选轴本轮没做**，理由与读数记在第 76 次附记的最后一节。
- 前几轮记过、本轮没碰的产品级取舍照旧：宽版布局开关、`--column 1152` 复跑超宽图、线上正文完整性轴、措辞可读性轴（第 68 轮那条「长文问答·跌」）。

## 2026-09-24（第 76 次）首页那句「217 张 Mermaid 里 171 张带图注、46 张靠引导语、0 张裸图」从来没有判据能复现——落库 `tools/checks/check_figure_explanations.py`，一并量图片放置侧的 45/44/1 与图注总数 215。这一轮**读者页正文零改动**，红的是尺子：新轴首跑先自己造了 27 条假裸图，`--live` 腿又把 8 条完好到达读者的图注报成丢失，最后它把**自己那条落库说明**数成了又一处图片放置

本轮新增 1 个判据文件（`tools/checks/check_figure_explanations.py`）+ 改 `docs/README.md` 一条统计句 + 本日志。**读者页 0 处改动**，所以 217 / 171 / 46 / 45 / 215 五个数改前改后完全相同——这句话本身就是本轮的主张：它们以前只是首页上的一句人话，现在是一台可复跑的机器读出来的。

### 一、这类缺陷我们修过两次，每次都忘在别处

「README 印着一个数，而 `tools/checks` 里没有任何脚本能产出它」不是新问题：

- 第 57 轮：README 引用的公式判据**压根不在仓库里**，同一棵树因此同时有过 930 / 931 / 943 三个公式数；
- 第 61 轮：叫读者「配置与任务集见官方发布页」却不给链接——承诺没有兑现；
- 本轮：图注覆盖的那三个数从第 54 轮起就以今天的写法站在首页上（「带图注 / 引导语」的说法更早，第 16 轮就有），而判据从没进过仓库。

判据不在，失真就是**静默**的：后一轮挪动一个图块，句子照样读得很自信。而图注这一类比公式更容易悄悄烂掉——它靠「这一行在围栏的哪一边」这种位置关系成立，正是最容易被重排破坏的那种结构。

### 二、判据量什么

对**每个围栏图块**给一个判决，对**每处图片放置**给一个判决：

```
CAPTION   紧挨围栏（前或后）有一行 *《图：…》*                     → 覆盖
GUIDED    否则紧挨围栏有一段实质正文                                → 覆盖
BARE      两者皆无                                                  → 缺陷
VAPID / VAPID-CAPTION  载体只有指示词（如下图所示、见图、下图为…）  → 缺陷
THIN-CAPTION  有图注但信息量不够                                    → 缺陷
NO-EXPLANATION / VAPID-IMAGE-CAPTION  图片放置侧对应的两种缺陷       → 缺陷
IMAGE-CAPTION  图片放置带着能到达页面的图注                        → 覆盖
DECORATIVE     闭集豁免，全站 1 处（首页封面横幅，文件在盘上验过）  → 不判
QUOTED         行内代码或围栏里的图片写法：那是示例不是读者见的图   → 不判（钉地板 ≥7）
UNRESOLVED     没被引号包住、又指向不存在文件的图片引用             → 缺陷
全站读数  pages=197 diagrams=217 placements=45 captions=215
          caption=171 guided=46 image-caption=44 decorative=1 quoted=8 findings=0
```

三条口径是判断，写下来好让人反驳：

1. **「实质」有条线的门槛，但这条线今天没在裁决任何东西**：载体剥掉 Markdown 符号与标点后，信息单元（汉字/字母/数字）≥12 才算正文。实测本树 46 条 GUIDED 载体**最短 23**、171 条图注最短 29，而**以指示词开头的行全站 0 行**——也就是说 12 与 23 之间是空的，门槛设成 12 还是 20，本轮读数一字不变。它的身份因此是**防回归的线**（钉住的是未来某轮写下的短载体与「如下图所示」），不是给已有 217 张图分类的分界线。把一条当前不生效的线写成量出来的分界，等于给首页再添一句读着精确的假话——那正是本轮要修的东西。
2. **标题、列表项、表格行、`{% hint %}`、引用块、另一张图都不算载体**。标题说出的是主题不是解读；列表项自带自己的主张，把它们当引导语等于允许一个项目符号列表冒充一句解释。
3. **指示词买不到覆盖**。本书首页明写「没有一张图是『如下图所示』四个字打发的」，那这句话就得能被证伪，所以 `VAPID` 是缺陷判决而不是覆盖。

豁免是闭集且每条都在盘上验过存在：装饰位只有 1 处（首页封面横幅）。写法示例则有 **8 处**（本轮之前 7 处，多出的一处正是下面第三节记录这条豁免时写下的那句示范），且**每一处都被引号包着**（更新日志与样式指南互相示范 `![alt](../.gitbook/assets/xxx.svg)` 的写法），所以**没被引号包住、又解析不到文件的引用 = 0 处**——后者现在直接是缺陷判决 `UNRESOLVED`，而不是豁免。这一桶因此钉**地板（≥7）不钉等号**：解释一条规则的句子必须引用那条规则的语法，钉等号等于对「把这条规则写下来」收税，而删掉一个字就能改绿——那正是本书最不该有的那种绿。真正把「读者见的图塞进反引号躲判据」拦在外面的是两道等号：`placements == 45`（藏掉一处放置，这个数立刻变小）和「被引号包住的图片写法，alt 只可能是 `alt` 或空」（真图注不会长成占位符）。这条边界是本轮现场学来的，见第三节第三条。

### 三、这一轮三次把尺子判成红，红的是尺子

- **首跑 27 条「裸图」，27/27 全是假的**。找「围栏前那一行」时，脚本从**闭合围栏**往回走，于是把图内最后一个节点定义（`Q3 -->|"是，循环里带反馈"| R4["Agent"]`）当成了正文——它读起来确实像一句话。改成读**开围栏**之前那条非空行后，读数精确复现首页的 217/171/46/0。这条假红现在常驻成控制：`plant_bare` 的图**故意**以一行长得像散文的节点定义结尾。
- **`--live` 腿把 8 条图注全报成 LOST，而线上 HTML 里图注确实在**（`<i class="font-italic">《图：AI 的概念收窄到 ML 再到 DL…》</i>`）。原因是比较两侧不对称：探针拿带标点的原文去比 `wl.visible()` 的输出，而后者把 `《`、`：` 和每个标签边界都换成空格——任何图注都不可能匹配。修法不是把 `[:24]` 前缀调长，是两侧走同一套归一化（保留字母数字与汉字、连空格一起去掉），并把这条理由钉成断言：**重演修前那种比较，必须读不中**。
- **判据被自己的落库说明判红**：把这条轴写进日志时，我在正文里用反引号引了一句 `![alt](../.gitbook/assets/xxx.svg)` 来解释「解析不到文件的引用算写法示例」这条豁免。下一次跑轴：`only 7 markup examples` —— 轴把**自己那条说明**数成了第 7 处图片放置。修法不是改措辞（那句话正是读者该看懂的东西），是补上第二个门：行内代码。围栏早已跳过，行内代码跨度此前没跳——而第 57 轮起仓库里就有一份 CommonMark 正确的分词器（`live_aria_manifest.strip_code_spans`，专门处理「反引号成串开、等长成串闭」和行内未闭合的连跑反引号），所以这里复用它而不是再写一个正则。修完再量，原来那 6 条「未解析引用」**全部**本来就在反引号里：真正的口径不是「6 处示例被宽容」，而是「7 处示例都规规矩矩被引号包着，而**没被包住的死路径 0 处**」。于是那条豁免被收紧成两种判决：被引用的写法记 `QUOTED`（数量钉**地板 ≥7**，不钉等号，理由见第二节；且 alt 只能是 `''` 或 `'alt'`——「在反引号里」不能给一张真图买免死），没被引用又指向不存在的文件记 `UNRESOLVED` 并判红。控制腿同时补上双向：反引号里的示例必须**不**判、把同一处引用的反引号去掉必须照判 `NO-EXPLANATION`。**等号该钉在哪一侧，本轮是又量了一次才定下来的**：改首页那段说明时把一处行内示例写进去，`QUOTED` 读到 9，删掉它回到 8——一个措辞就能推动的数不配当等号；而把同一处引用的反引号去掉，`placements` 立刻 45→46、判据马上响，能钉等号的是它。
- 修完之后这条腿还要能自证不瞎：每页先拿**这一页必定发布的 H1** 做正控制（找不到 → 报 `BLIND` 探针故障，而不是 8 条丢图注），再用一句这本书从没写过的幽灵文本做反控制；`pages` 与 `captions` 两个计数各有一道地板，防止「一个图注都没比」也读成绿。

### 四、真实页变异控制：6/7，那 1 页不是漏网

`--live` 之外还有落地前最关键的一条：拿 7 张真页的副本，各删掉一条图注，该页 findings 必须 `0 → 1 → 0`。6 页如期暴露；第 7 页（`00-index/learning-path.md`）删掉图注后仍读 GUIDED——那张图**同时**有一段实质引导语兜底，判成覆盖是对的。控制腿因此只把「图注是唯一载体」的块算进断言，并打印 `6/7 pages tried`：一个把所有正确行为都算成功的控制，等于没有控制。

19 条种植反例（图块侧 7 + 图片侧 9 + `--live` 腿自身 3）双向钉着：裸图与指示词必须被抓，图注与实质引导语必须**不**被抓；图片侧从 7 长到 9，长出的两条正是第三节第三条那对（反引号里的示例必须**不**判 / 去掉反引号必须照判）。（**同日附记**：这条腿当天又被补了一次，反例因此从 19 长到 **23**，多出 4 条全在线上腿——见下面第六节。本节以下凡是「3 条线上反例」「12 页 13 条图注」的读数都记录的是当时那一次，不追改。）

### 五、留下了什么

- **`--live` 只抽 12 页 13 条图注**，不是全站 171 条。作者侧的覆盖判断是全覆盖的，线上侧只回答「写下的图注会不会被平台吞掉」这一件事；要变成全站腿，得先解决每页 1.1 MB 的抓取成本（第 67 轮资产轴记过的节流教训同样适用）。**这条「只抽 12 页」当天就作废了**：图片那一半补成穷尽，而同一趟里图块侧顺带比到 42 条（图注与图片说明常常同页），见第六节。
- **图注的「两级」结构还没做**：目前一句图注既要说清「这张图讲什么」又要说清「读它要带走什么」，长图常常撑不住。做成两级（短标签 + 一句结论）是版式取舍，留给操作者。
- **GUIDED 的排除表是一次判断而不是测量**：如果哪天有人认为「小节标题 + 图」这种排版也该算覆盖，改的是 `neighbour_kind()` 里那五个前缀，且必须同时改反例（`heading_is_not_a_carrier`）。
- **197 页里含 `SUMMARY.md` 与本日志**。本日志按设计会引用页面原文，但它没有图块和读者图片放置（示例引用记进 `QUOTED` 那一桶，且必须被引号包住），所以留在分母里不影响覆盖判决。不过「改这段字不会动任何数」这句好话本轮被自己推翻了：它动的正是 `QUOTED` 那个数——见第三节第三条末尾，那也是这一桶只钉地板的原因。
- 前几轮记过、本轮没碰的产品级取舍照旧：宽版布局开关、`--column 1152` 复跑 102 张超宽图、线上正文完整性轴、措辞可读性轴（第 68 轮那条「长文问答·跌」）。

### 六、同日附记：这条腿补上图片那一半，而第 75 轮那次抽查的 18 条 MISS 全部出在尺子与断言本身

补完上面五节之后，第 75 轮遗留的那次线上抽查才跑起来（它的 `--live` 依赖本轮这把尺子先落库），它报 `problems=18`：9 页 × 两条，**每条都 MISS，无一例外**。逐条查下来，18 条里没有一条是书的问题。

- **9 条「读图提示没到读者眼里」是尺子的错**，而且和本轮第三节第二条是**同一个 bug 的第二次现身**：那次抽查拿带 `「」：、。` 与小数点的原文去比 `wl.visible()` 的输出，而后者把每个非「数字/拉丁/CJK」串换成空格。用同一套归一化比两侧，9 条**全部在场**。这轮之后图注侧两种到达形状（`<i>` 段落、`<figcaption>`）各有各的种植反例，其中一条专门钉「不许退回未归一化的比较」。
- **9 条「线上页广告了自己的更新日期」是断言本身没据**——而这 9 条 MISS 顺带量出一条更基本的事实：**读者在那张渲染页上看不到我们写的 `updated:`**。同一趟抓的完整 HTML 里，`05-tool-protocol/mcp` 的角标是 `Last updated <time dateTime="2026-09-24T08:17:28.905Z">`，可见文字是**相对时间**「1 hour ago」；`02-agent-basics/what-is-agent` 是 `dateTime="2026-09-22T15:47:19.595Z"` → 「1 day ago」。两个 `dateTime` 是**平台自己的每页修订时间**（mcp 那个正好落在第 76 轮部署的那一分钟），而作者写的 ISO 原文在两页的可见正文里都读不到（原始 HTML 里 ISO 形状 27 次、可见正文 0 次）。所以那条抽查不是「没找到」，是**断言了一件平台从没做过的事**：它的前提是「页面会印作者这个字段」，而前提不成立。
- **同一条实测订正第 75 轮的一句话**：本轮第五节记的 17 页「最后更新」失真「向读者报了一个假的『最后更新』」——严格讲读者看到的角标来自平台时间，改不改这个字段都不影响它（第 17 轮日志里那句「仓库写什么都不影响右上角那个日期」是同一个测量的另一半，本轮第一次把它接到这条轴上）。规则仍然该留，理由换成量到的那个：`updated:` 是 **`.md` 端点**的答案，而本书把 `.md` 当成正式读者出口（首页与全书都指向它），写错就是那份答案错，不是页面角标错。判据 `check_updated_dates.py` 顶部那句「GitBook prints that field to the reader」已按实测改写。
- **而本轮自己差点把这条写成一句新的假话**：第一次归因时我引用了一条从上下文带过来的旧读数（「整份 HTML 里 `2026` 出现 0 次、没有任何 updated 字样、没有 `<time>`」），它和第二次实测正面冲突——同一张页原始 HTML 里 `2026` 命中 **72** 次、`Last updated` 原始 3 次 / 可见 1 次、ISO 日期 27 次。第二次是对的，依据不是「哪次跑得晚」，而是**回去读了那份日志的原文**而不是手里那句总结。写成一句话交给下一个人：**旧读数要进入新断言，必须先重跑或重读**。
- **图片那一半从此有线上判据**：`live_captions()` 不再只抽 12 页图注，而是**穷尽比对 36 张带图片说明的页面 / 44 条读者可见说明**，图块侧在同一趟里顺带比到 42 条。图片侧此前一条线上判据都没有：离线的图片轴只问「`<img>` 元素有没有被平台丢掉」，本轴的图注半边只看 Mermaid，而「这张图缩到 0.475 倍、想看清请点开」这类话恰好**全部住在图片侧**——第 75 轮新写的 9 条如此，全站 44 条也如此。
- **读数**（`--live`，exit 0）：`pages=48 captions=86 diagram=42 image=44/44 on 36 image pages still-absent=0 problems=0`；离线读数与前面五节完全相同（`pages=197 diagrams=217 placements=45 captions=215 caption=171 guided=46 image-caption=44 decorative=1 quoted=8 findings=0`）。**改的是尺子不是书**：读者页正文仍然 0 处改动，首页只有那条统计句的判据描述跟着变（含反例数 19 → 23）。
- **新增的 4 条线上反例**：`<figcaption>` 形状必须能匹配、该页 H1 必须能匹配、幽灵文本必须不匹配、以及「未归一化的比较必须判不出来」（最后一条把本轮这次错钉成回归线——谁把 `crush()` 当成多余的好心删掉，它会立刻变红）。
- **地板而不是等号**：图块/图片两条比较数各设地板（`diagram>=4`、`image>=4`），因为措辞会推动它们；真正的**等号钉在「图片那一半是穷尽的」**（`image_checked == 树上全部 IMAGE-CAPTION`）——这条不随措辞动，也正是「线上腿悄悄退回只看图块」那种半盲状态唯一拦得住的地方。第 76 轮前半段刚记下「措辞能推动的数不配当等号」，这一节是它第一次立刻派上用场。
- **未做**：图块侧仍不穷尽（42/171，其余靠 `check_live_ssr_parity` 的容器对平与 `check_live_images` 的元素对平覆盖，二者都不读图注文字）；**「作者写的 `updated:` 与页面角标那个平台时间差多少」没有线上腿**——本轮量到两者今天恰好一致（mcp 的 `dateTime` 就是第 76 轮部署那一分钟），但一致不等于有判据。它是一根现成的轴：拉每张页面 `<time dateTime>` 的日期，与本仓库 frontmatter 比，差超过 N 天就报（读者在页面上看到「3 天前」而 `.md` 说「2026-09-22」，是同一页的两个答案）。本轮不做是因为它要新开一趟全站抓取、而且要先定 N 的语义（部署时间差 ≠ 正文时间差），不是没看见。


## 2026-09-24（第 75 次）8 张真实产品 PNG 第一次被量：它们全是 1280px 位图被平台钉进 608px 正文列，读者拿到的缩放是 0.475——落库判据 `tools/checks/check_screenshot_legibility.py`，并把「点开可放大」从一句好话变成一条要线上复测才许豁免的规则。给这些页改日期时又量出第二类缺陷：17 页向读者报的「最后更新」早于它们最后一次真实正文改动，第二条判据 `check_updated_dates.py` 落库

本轮动正文 9 页（8 张截图、9 处引用）+ 只改日期行 17 页（`--fix` 写回的 BEHIND 17 条），判据新增 2 个文件：`tools/checks/check_screenshot_legibility.py`、`tools/checks/check_updated_dates.py`。README 统计数字不动（196 页 / 19 章 / 217 Mermaid / 32 SVG / 8 截图）——**一张图都没删、没裁、没重排，17 页正文一字未动**，这一点下面要解释，因为它是本轮唯一带取舍的决定。

### 一、这条轴为什么存在：PNG 没有源码，别家 UI 的字号量不到

第 68、70、74 轮的「留下什么」里都抄过同一句话：8 张第三方产品截图是唯一没有任何轴量过内容的图。其余每一条图都是自家写的标记——Mermaid 有几何轴、手绘 SVG 有六条腿——**字号可以从源码读出来**。PNG 没有源码：图里那行 13px 是别人的 app 画的，我们唯一能决定的是这张位图被排多宽。

线上实测（真实浏览器、水合完、两个 DPR 都跑）给出的答案是：

```
authored   8 张，1280px 宽（其中一张 1040px）的真实 UI 位图
painted    608px —— 平台把每一张内容图钉在列宽上：480px 的放大到 608，1280px 的缩到 608，
           图和它的 wrapper 都是 608；光栅图没有横向滚动条（第 73 轮那条属于 display 公式）
served     ~gitbook/image 代理在 DPR 1 给 768px，在 DPR 2 只给 640px
```

于是厂商 UI 里 13px 的文字到读者眼睛是 `13 × 608/1280 = 6.2px`。**2x 屏救不了**：设备像素让字形更锐，不会让它更大，而代理在 DPR 2 反而交得更少。目检那 608px 的真实像素时还撞见一件更能说明问题的事：MCP Inspector 截图里那行状态文字，缩到 608px 后我读成「sunny, **14**°C」，点开放大读的是「sunny, **24**°C」——同一张位图，宽度就是「看清」和「读错」的分界。

### 二、修法不是裁图，是把平台已经给的东西写成可判的事实

先量了读者点一下会发生什么：GitBook 的 lightbox 挂在 `<body>` 上，取的是 **authored 字节**（naturalWidth 1280，不是代理的 640），画 **1216px**。7 张 1280px 的缩放 0.950，那张 1040px 的 1.000，**8/8 成立**。

所以「把 8 张截图裁成 608px 宽的局部」这条路的代价被量出来了：图注写的是整屏的读数（左树 1.00s→0.54s、五条并行会话的标签、Random 稳在 0.5），裁掉就没得读，违反「不为凑指标删内容」和「图丑就 art-direct 不是删掉」。改判据为**两侧都要**：

- **SHRUNK-UNDISCLOSED**：位图排在 authored 缩放 0.90 以下，**且图自己的那几行没告诉读者可以点开** → 判红。本轮 9 处引用全部命中（0.475 ×8、0.585 ×1），修法是在每张图的图注后补一行「读图提示」，把这张图自己的缩放比和补救动作一起写给读者——**一张图都没删、没裁、没重排**。
- **STRETCHED**：比列还窄的位图被放大 → 判红（本轮 0 处）。
- **CAP**：代理交出的宽度低于 authored → **只报不判**（第 73 轮对列宽的同一口径），因为那是平台给的，改判据改不出来。修完尺子之后它是一条**稳定读数**：`cap=18`，正好 9 处引用 × 2 个 DPR，两遍全站复跑同为 18（第一遍它读成 17，是第三节第三条那个 bug；读数会随缺陷变严重而变小的规则不是规则）。其中 9 条是 DPR 1 只给 768px，另外 9 条是 DPR 2 只给 640px（那张 1040px 竖版给 520px）——2x 屏交出的位图比 1x 屏还窄。
- 豁免**不能被文字单独买到**：`--live --zoom` 必须真的量到 lightbox 画回 authored 缩放，否则 `UNVERIFIED`（只写了字没跑线上）/ `ZOOM-MISSING`（线上没量到）/ `ZOOM-LIE`（量到了但 <0.90）三种判决照样判红。所以这条轴的常驻读法是 `--live --zoom`，离线跑必然不绿——这是设计，不是没修完。

### 三、尺子自己的四个 bug，全部是同一条 `--live --zoom` 反复跑出来的

第一次 `--live --zoom`：`problems=2 coverage=3`。两条都是假案，而且都是**我读错了自己的探针**；另外两条是复跑之间和"把 18/17 问个清楚"的那一趟冒出来的（见下面第三、四条）。

- **ZOOM-LIE 两例是探针退化**。点开之后我量的是「页面上最宽的那张 ≥400px 的图」，而 lightbox 里那张图此刻还没解码完（naturalWidth=0，被 ≥400 筛掉），于是探针回头把**仍在原位的那张 608px 列内图**当成了放大结果——恰好等于列宽，读数 0.475/0.585。改成：只认 `<main>` 之外、且必须等到 `[class*="zoom-modal"]` 里的位图真的解码出来（最多轮询 6 次），读不到就明确分「弹窗没开」与「开了但位图没到」。
- **coverage 三例是阈值假警**。覆盖账按 naturalWidth≥400 数图，而代理给的 naturalWidth 随 DPR **变小**（mcp.md 的手绘 SVG 在 DPR 1 是 960、DPR 2 是 384），于是 DPR 2 天然少数一张。改成按「DOM 里有几张图 / 几张拿到了盒子」记账，与 DPR 无关。
- **第三条是复跑之间冒出来的**：修完之后两遍全站读数 `cap=18` 与 `cap=17` 不一致，而 CAP 是一条**只报不判**的腿，没人会被它逼着改什么——正因如此它更容易糊过去。查下去是同一道闸的第二次咬人：CAP 计数复用了 `big`（naturalWidth≥400）那个筛子，于是**平台压得越狠、这条打印越安静**（DPR 2 把 Inspector 那张 PNG 交到 400px 以下，那一趟它就不在账上了）。一条会随缺陷变严重而变小声的规则不是规则。现在 CAP 与「这张图是不是仓库里的资产」一样只看 URL 匹配，尺寸闸只留给目检截图用；常驻反例两向：300px 的 1280px 副本必须记进 CAP，原尺寸副本必须不记。

- **第四条是决定「CAP 到底是 18 还是 17」的那一趟跑出来的**，而且它同时解释了第二节那条豁免腿为什么会被二次冤枉。把尺寸闸拆掉之后，CAP 开始吃到 `naturalWidth=0` 的行（同一趟里 Inspector 与 autogen 各读到一次 0px）。可 `0px` **不是平台选的宽度，是探针没等到位图**：把它记进 CAP 等于替平台编了一条从没发生过的取图策略，还把「我什么都没看见」记成一条正常读数。同一趟它还污染了豁免腿——点的是两张**像素还没到的图**，GitBook 不给这种图开弹窗，于是两张诚实的截图第二次被判成 ZOOM-LIE，判决文本印出来的数是 `scale=-1.000`（哨兵值被当成实测比例）。四处一起改：① 判据前先 settle 轮询（最多 4×1.5s），等到每张图**既有盒子也拿到位图**；② 等不到位图的行进**覆盖桶**判红，明写「这是没量到，既不是 cap 也不是干净」；③ `cap_line()` 见 0px 直接返回 None（纯函数，所以这条能种成常驻反例）；④ 点击前先确认 `complete && naturalWidth > 0`，再最多做 3 次真指针点击，**第几次点开会打印出来**——「第二次才开」是探针的事，「三次都不开」才是平台没兑现，判据不许把前者写成后者；哨兵值从此走 `ZOOM-MISSING`（带点击次数），不再冒充一个测量。**这条重试不是保险丝，是当场用上的**：修完后的确认趟里 `06-arize-phoenix-trace-ui` 打印 `opened on click #2`——位图明明已经解码，第一次指针点击仍然会被吞掉，所以「没开弹窗」在旧探针那里可以仅仅意味着「我点歪了一次」。

修完的正式读数（修完之后连跑两遍，两桶都空才算）：两遍都是 `figures=8 told-and-verified=8 problems=0 cap=18 coverage=0`、`exit=0`——CAP 现在是一条**稳定读数**而不是区间（18 = 9 处引用 × 2 个 DPR，无一漏计）；`live <main> widths seen: 608px x18`。独立第二个探针（另写的目检脚本，取 `<main>` 外最宽图并截图存证）给出同一组数：05-openwebui 1040/1040=1.000、06-arize-phoenix 与 02-mcp-inspector 1216/1280=0.950。

### 四、控制样本与回归

**本轮的修复被另一条轴当场抓住**：第一版「读图提示」我在 8 张 1280px 的图上用了同一句话，`check_prose_duplicates.py`（第 60 轮落库的跨页重复轴）立刻报 `DUP-EXACT prose x8 pages`——判据之间是互相看着的，新轴的红不是老轴的绿灯换来的。改成**逐张写自己的数**：每张图的提示语各说这一张的原图宽、排进列后剩多少（要么比例 0.475/0.585，要么那行字的实际像素约 6px），以及点开之后具体要读什么（Inspector 的 41ms/43ms 流水、Dify 右侧抽屉的取值、Phoenix 的 1.00s→0.54s、Langfuse 那 7K 对 6、Open WebUI 是 1040×1082 竖版缩到 0.585）。复跑 `dup=0`，近重复带仍是你来之前那 3 条，`prose_units=7285`（这批提示语本身就是新单元，所以分母随正文长——第 60 轮那条轴早就写明这个数只认当前树）。

`--selftest` 钉住判据方向：608px 干净 / 1280px 必须 fire SHRUNK / 660px（0.921）必须放过 / 300px 必须 fire STRETCHED / 1280px 但已 told 必须放过 / 远程图必须报不能跳过；`told()` 在同一句图注上双向各一次（有承诺读到 told、删掉承诺读到 untold）；代理双重编码 URL 必须能解析回资产（解析不到也必须报），否则 CAP 腿会像首跑那样把 640/1280 报成 `cap=0`；CAP 记账三向（300px 的 1280px 副本必须记 / 原尺寸副本必须不记 / **0px 不许冒充 cap**）；豁免可撤销五方向 UNVERIFIED / ZOOM-MISSING（没点着）/ ZOOM-MISSING 哨兵（点 3 次没开，判决必须带次数且**不许出现负数比例**）/ ZOOM-LIE（量到了但 <0.90）/ 实测通过。全站差分：8 张资产 × 3 个幻影（重排到列宽=干净、2 倍=SHRUNK、一半=STRETCHED）= **24 个种植用例全部符合预期**，所以「8/8 命中」是一条缩放规则而不是八个嫌疑犯名单。

回归套件全绿：结构 `pages=198 problems=0`、组件配对 `problems=0`、引用回核 `findings=0 verified=14`、字符体检 `problems=0`（正文 CJK 368323——这条计数会被这段日志本身改掉：写完一个数它就动，所以它是当次读数而不是可抄的常量）、KaTeX `pages=108 formulas=927 failures=0`（引擎 0.18.7）、跨页重复 `dup=0 near-band=3`（与本轮前同读数）、SVG sanitizer `served copies compared=32 of 32`、README/首页/封面横幅三腿对平（196 页 / 19 章）、更新日志标题轴 `HEAD=66 tree=67 lost=0`。

### 五、给一张图改日期时顺手量到的第二类缺陷：17 页向读者报了一个假的「最后更新」

本轮给 9 页补 `updated:` 时问了一句：`check_structure.py` 只检查这个键**存在且格式对**，所以一页可以永远印着任何看起来合理的日期。拿 git 一比：**17 篇读者页向读者报的「最后更新」比它们最后一次真实正文改动早 1–2 天**，而每一次都是本仓库自己的轮次留下的——10 页是第 73 轮那次公式重排（`99f6fc3`，改了正文没动键）、1 页是第 74 轮改首页（`b10e40f`）、另外 6 页分别来自第 52/54/63 轮（`2e7b3c3`/`61933ab`/`60a6962`）。**这一类缺陷不是第一次出现**：第 17 轮（`49d1c05`）手工回填过 80 个失真日期，当时没有判据，于是六个轮次之后又攒出 17 个——这就是它该活在脚本里的理由。GitBook 把这个字段画给读者，所以这不是元数据洁癖，是**关于这本书的假陈述**。

落库判据 `tools/checks/check_updated_dates.py`：逐页取 `updated:` 与「最后一次改了除日期键以外任何一行的提交」的日期比。判决两条，**方向对称**：

- **BEHIND**：正文比日期新 → 读者被告知这页比实际上更旧。这就是本轮量到的 17 条。
- **FORWARD**：日期比正文新 → 读者被告知一次没发生过的更新。同样判红，因为**单向规则等于允许一轮只改元数据就把全站的日期「刷新」**。

`--fix` 只写 BEHIND：把 FORWARD 倒回去是改写主张而不是补记事实，而且它常常就是本轮自己那笔尚未提交的正文改动。这条区别带了一对常驻反例：同一行读数，工作树脏时记 `pending-commit`（git 还无法为它作证），干净时必须 fire FORWARD；而 BEHIND 无论脏不脏都照判——未提交的改动不能成为少报日期的借口。

让规则稳定而不是自喂的是**日期-only 提交豁免**：改日期本身就是一笔碰到该文件的提交，如果判据把它算作正文改动，`--fix` 会把自己那笔提交的日期读成新的 `L`，下一轮的 fix 就追着它跑。`body_commit_date()` 因此只看「是否有非 `updated:` 行的改动」。控制腿：相等必干净 / BEHIND、FORWARD、NOKEY、NOCOMMIT 各必须 fire / 豁免页不计入 checked / 只改日期键的合成 diff 不得移动 `L`、含一行正文的合成 diff 必须移动 / 多条提交取最新那条正文提交 / 豁免清单是闭集（改名或新增文件不能悄悄混进去）/ 全站 checked 地板 ≥190。

读数 `reader pages=198 checked=196 exempt=2 problems=17 pending-commit=8`，`--fix` 后 `problems=0`、`exit 1 → 0`。**17 处只改日期行**（`git diff --numstat` 每条都是 1/1，脚本另带 assert 拦住任何 1/1 之外的页），正文一个字没动。那 8 条 `pending-commit` 就是本轮自己改的 9 页中的 8 页（第 9 页 HEAD 已有 09-24 的正文改动，自然相等）。口径注意：`--fix` 下笔时这 17 页每页都恰好 1/1，但落进**整轮** diff 后读作 16 页 1/1 + `05-tool-protocol/mcp.md` 的 3/1——那一页本轮既被补了一行读图提示又被改过日期，3/1 是两笔改动叠在同一页，不是日期那一笔碰了正文。

### 六、留下什么

- **CAP 这条腿只报不判**：代理在 DPR 2 给 640px（那张竖版给 520px）比 DPR 1 的 768px 还少，是平台侧的取图策略，我们改不了；如果哪天它给到 1280，这条打印会自己消失。
- **正文一张图始终没拿到位图，现在会判红而不是少报一条**：这条轴的覆盖桶从此有三笔账（没盒子 / 对不上仓库资产 / 盒子等到位图超时），代价是常驻读法比之前慢（每页最多多等 4×1.5s 让代理把位图解码完）。慢可以接受，看不见不行。
- **点开放大是平台能力，不是我们的**：豁免的代价是这条轴必须长期跑 `--live --zoom`。GitBook 哪天去掉 lightbox，8 张图的豁免会同时变红（`ZOOM-MISSING`），不会静默。
- **正文列宽 608px 本身仍未改**（第 73 轮起就只报不判）。宽版式开关、102 张超宽 Mermaid 在 `--column 1152` 下的重读、图注两级化、线上正文完整性轴、措辞可读性轴、读者侧渲染对比度（第 74 轮点名的下一号候选）继续待操作者拍板。
- 一个 GitHub PAT 曾出现在聊天里，仍需操作者自行轮换，不在仓库可修范围。

## 2026-09-24（第 74 次）第 73 轮的线上复核写在临时脚本里，所以那句「读者看到了」本轮又不能复跑：判据落库 `tools/checks/check_live_formulas.py`（带一条"量不到拖动就自杀"的标定腿）——它首跑就在半路挂死 25 分钟，于是逐页预算、进度打印和「没量到 ≠ 没缺陷」的两桶记账也在同一轮落库；引用轴装上覆盖率分解腿，把 `attributed=16` 之外那 **1752** 个「」串摊开量了一遍，结果是把「引用/术语分类器」这条候选**判死**——两个可疑堆里 50 条逐页读完，全是自家用语与虚构示例句，没有一条是外部引文

本轮动正文 0 页，判据新增 1 个文件、加宽 1 个文件：`tools/checks/check_live_formulas.py`、`tools/checks/check_quote_fidelity.py`（`--buckets`）。README 统计数字不动（196 页 / 19 章 / 217 Mermaid / 32 SVG / 8 截图），但首页公式那条 bullet 补上了第 73 轮的双列读数与 `[t]` 守卫——它此前只描述单列判据，读起来像「768 就是读者那一列」。

### 一、线上腿落库：作者侧拟合与读者侧看见，是两根轴

`check_live_formulas.py` 把第 73 轮那段一次性复核变成一条命令，并加宽到**每一篇作者含 display 公式的页**（106 页 / 276 条），不再只查改过的 11 页。每页判四件事：线上条数 == 仓库作者条数、`.katex-error`、渲染文本里的裸 LaTeX 残留（`[t]` 那一类）、墨迹宽 − 滚动盒宽 ≥ 16px。宽度仍按**墨迹**量（`Range` 夹住 `.katex-html`，`scrollLeft` 两端各取一次再取大），因为 `.katex-display > .katex` 是 `display:block`，量盒子永远"放得下"。

尺子的标定腿是这一轮新加的，也是这条轴和临时脚本最大的区别：**把本页最宽那条公式的滚动盒用脚本改窄 100px，判据必须立刻读出 ≥16px 的拖动**。量不到就 `assert` 死掉——一个悄悄改量盒子的探针，打印的绿灯和真探针一模一样。首跑读数：

```
ruler ok: the 598.13px formula of block #0 squeezed into 498px reads drag=100px
  01-ai-basics/ai-ml-dl.md            main=608  1/1 formulas  widest ink=598.1 in 608px
  ...
live formula verdict: pages=6 checked=13 problems=0
```

三条常驻断言从第 73 轮继承并写死：窗口 `innerWidth` 必须等于要求的 1280、种在页尾的 200/960 控制盒必须分毫不差、KaTeX webfont 必须已加载（回退字体下的宽度全是假数）。控制盒仍然**最后**种。列宽本身按第 73 轮的口径**只报不判**（`live <main> widths seen: 608px x6`），因为列是平台给的，改判据改不出来。

**这条轴第一次跑全站就把自己的第二个缺陷跑了出来**：106 页跑到一半，Playwright 的 node 驱动先退了，父进程永久阻塞在死管道上——25 分钟里 CPU 0.77 秒、日志 0 字节，而「慢」与「死」从外面看完全一样。三条原因都在轴自己身上，本轮全部改掉：

- **没有逐页预算**：`wait_until="networkidle"` 配 90s 超时，一个长轮询的页就能白等 90 秒。现在是 `domcontentloaded`（45s 硬预算）+ 一次**尽力而为**的 idle 等待（8s，失败不判缺陷，它只是提示不是闸）+ 2s 水合沉降；线上条数与仓库不符或字体没加载时**先重读**（最多两次，每次 5s）再下判决，避免把「还没水合完」读成「平台少发了公式」。
- **没有覆盖账**：抓不到的页原来直接混进 `bad`。现在**内容桶**（拖动 / `.katex-error` / 裸 LaTeX / 包裹层不是滚动盒）与**覆盖桶**（`fetch-failures`：超预算、冷却 15s 重试一次仍失败、字体始终没来）分开记账，**任一非空都 `exit 1`**，覆盖桶明写「这不是内容发现，重跑，别读成绿」。第 67 轮在资产轴上记过的同一条教训，这次落在新轴落库的**同一轮**。
- **看不见进度**：逐页打印实测值与本页耗时（`[12m34s]`），输出**行缓冲**，页间节流 0.8s（第 67 轮量过的 CDN 速率）。

`--selftest` 是离线腿，用合成结果钉住桶的边界：干净跑通 = 0、有一页没够着 = **1** 且内容桶保持 0、有真缺陷 = 1 且不许躲进覆盖桶、两桶同时非空 = 1；**空样本必须报**（一页都没够着 / 25 条只量到 4 条都直接 `assert` 死），而 `--limit 8` 这种**抽样**不许被空样本地板误伤（8/106 页、13 条 → 照旧 0）。改完的冒烟跑：`pages=8/8 checked=19 problems=0 fetch-failures=0`，每页约 13 秒。

### 二、覆盖率分解：把一条候选判死，比给它写分类器便宜

第 71/72 轮反复写下「`attributed=16`，全站 2265 个「」串」，并把它列成下一轮的头号候选：给引用和术语做个分类器，把剩下那两千条管起来。本轮先量再建——`check_quote_fidelity.py --buckets` 用**判据自己的正则**（`QUOTE` 要求 ≥6 字）把语料摊开：

| 堆 | 条数 | 是什么 |
| --- | --- | --- |
| GRADED（被动词语法看到并判过） | 6 | 真引用 |
| SHORT-NAME（≤12 字、无句读） | 1350 | 术语名、小节名 |
| SOURCE-NEAR-NO-VERB（附近有「论文/文档/原文…」却没贴动词） | 40 | 逐页读完：自家用语，如「模型 + harness + 工具治理」 |
| SENTENCE-SHAPED（含。！？；） | 10 | 逐页读完：**我们编的示例用户问句**，如「公司的年假政策是什么？」 |
| OTHER | 346 | 长术语/口诀式短语，含本页自己 |

读数 `「…」 strings in prose ... : 1752`，两个"可能藏真引用"的堆各只有几十条，且**打印出来逐条读完没有一条是外部引文**。所以分类器要判的那个缺陷（读者被引着一句查不到的话）在这棵树里量不到样本——候选判死，改成一条常驻的覆盖率腿：以后 `findings=0` 旁边必须同时打印这张表，谁也不能再把它读成「所有引用都核过」。这条腿**不动退出码**（覆盖账不是判决），内部 5 条种植自证：五种写法各必须落进自己那一堆。

### 三、全站线上扫描

**这条轴首跑抓到的七个"缺陷"，全是它自己量得太早。** 第 73 轮的一次性复核把 `deployment-scaling.md`、`observability-tools.md` 等页报出 7 条 `formula not laid out`（探针读到公式零宽）。本轮落库后先做的是**证伪这把尺子**而不是改内容：拿 `.tmp-projects/r74_diag.py` 逐块 dump（`hasHtml/htmlW/rect` + 八层祖先的 `display/visibility/offsetParent`），两张页在 `+2000ms` 沉降后读 **每块 608px、零宽 0 处**——线上没问题，是探针在 KaTeX 排版完成前就按了快门。三条改法把竞态变成可复现的判决：

- **先重读再下判决**：`settled()` 现在对「线上条数与仓库不符 / 字体没来 / 有零宽且无隐藏祖先的块」最多回读两次（每次 5s），把"还没水合完"和"平台少发了公式"分开。`deployment-scaling.md` 在 `read x3` 才拿齐 4 条的盒子，复跑 `problems=0`。
- **隐藏 ≠ 缺陷**：GitBook 把未激活的 `{% tabs %}` 面板用 `display:none` 收起来，里面那条公式**本该**无盒（读者点击才排版）。新增 `CLASSIFY` 分类器沿祖先链找隐藏原因，命中的块记 `hidden` 不判红；判红的是**零宽且无隐藏祖先**（真·空盒）。分类器自己带常驻反例：`display:none` 副本必须读 hidden、被脚本挤成 `width:0` 但留在流里的副本必须读 no-reason——否则"hidden"就成了给空盒子开脱的后门。首跑读数：`classifier ok: a display:none copy reads hidden (display:none), a zero-width in-flow copy reads no-reason`。
- **`hidden` 是独立计数**，与内容桶、覆盖桶三足分立；`--selftest` 里加一条 `code([], [], hidden=7) == 0`，钉住"隐藏永不把干净跑染红"。

全站 106 页 / 276 条 display 公式的完整判决：

```
checked 273 live display formulas on 105 of 106 pages
live <main> widths seen: 608px x105
  FETCH-FAILURE 12-applications/enterprise-knowledge-base.md: KaTeX webfont never loaded, ... — this page was not measured
live formula verdict: pages=105/106 checked=273 hidden=0 problems=0 fetch-failures=1
```

**首趟 `problems=0`、`hidden=0`——第 73 轮那 7 条「没排版」在全站规模下全部消失**（重读逻辑 + 分类器共同把它按水合竞态处理掉了）。唯一响的是**覆盖桶**：`enterprise-knowledge-base.md` 的 KaTeX webfont 在预算内没等到，轴如实记「这页没量到，不是内容发现，重跑别读成绿」并 `exit 1`。单独复跑这一页：`main=608 3/3 formulas widest ink=488.5px，problems=0 fetch-failures=0`（`read` 一次即齐）。所以净判决是 **106/106 页、276 条公式、0 内容缺陷、0 遗留未检页**（那 1 个覆盖缺口是瞬时的、复跑即闭）。`live <main> widths seen: 608px` 在 105 页上无一例外——第 73 轮的「读者那一列是 608 不是 768」在线上全站成立。

### 四、回归读数

本轮改正文 0 页，只动两份文档（README 首页两条 bullet + 本更新日志）与两个判据文件（`check_live_formulas.py` 新增、`check_quote_fidelity.py` 的 `--buckets` 腿）。批量改文档后按规矩重跑离线全家桶，全部照绿：

```
check_structure            pages scanned=198 problems=0
check_changelog_headings   HEAD=65 tree=66 lost=0
check_char_sanity          pages=198 prose CJK chars=365337 traditional-form findings=0
check_prose_duplicates     pages=191 prose_units=7254 formula_units=274 dup=0 near-band(0.72-0.85)=3
```

`prose_units` 从第 73 轮落库的 7237 涨到 7254、CJK 从 363289 涨到 365337，都是本轮首页那两条新 bullet 与更新日志正文贡献的（本首页自己算一篇，改它这些数就动，判据读数只认当前树）；`formula_units` 仍 274（本轮 0 增删公式），近重复带仍 3 条 advisory（模板页互说「收录标准/配图要求」，语义本应一致）。全站 display 公式线上判决（见 §三）：**106/106 页、276 条公式、`problems=0`、`hidden=0`、覆盖桶那 1 个 webfont 超时页复跑即闭**；`--selftest` 六条种植全过。

### 五、留下的账

- **线上公式轴量的是"放得下 + 画出来了 + 没漏排版"，不是"看得清"**：它判条数对平、`.katex-error`、裸 LaTeX 残留、墨迹宽拖动、隐藏/可见分类五件事；**不判**墨色对底板的对比度（那是 SVG 侧第 69/70 轮的相位与配色轴管的，HTML 正文公式没有对应腿）。读者侧**渲染对比度**这条腿仍未建，是下一轮的候选。
- **`<main>` 报 608 不报 768，且只报不判**：列宽是平台给的（第 73 轮已确证），改判据改不出来，所以这一列的值只打印、不参与判决——但它提醒所有作者侧拟合轴：768 不是读者那一列。
- **产品级取舍仍等操作者拍板（带数）**：① 32 张手绘 SVG 按 608/≈350 列重排（authored ≥18.9px 才够 12px 门槛）；② 开 GitBook 宽版布局（`--column 1152` 的 what-if 已读 0 越宽，但公式包裹层是硬 `max-w-3xl`、开了也不加宽）；③ 接受笔记本缩放、把 608 定为作者目标。本轮三选一都没替操作者决定。
- **carried 候选**：102 张超宽 Mermaid 等同一个宽版开关落地后用 `--column 1152` 重读；8 张真实产品 PNG 截图仍没有任何轴量过它们的内容；`10-eval-console-ui` 的「长文问答·跌」措辞像被截断的半句（措辞可读性轴第一个样本）；**GitHub PAT 早先贴在聊天里，仍需操作者去 GitHub 撤销轮换**（不是本轮能修的）。
- **本条轴的覆盖桶仍可能因 CDN 速率触发**：`--selftest` 保证触发时 `exit 1` 且明写"重跑别读成绿"，但没有把它变成自动重扫——重扫是操作者的 `python tools/checks/check_live_formulas.py` 一条命令。

### 六、推送与线上复核

提交 `b10e40f`，SSH 推送 `42f0bb3..b10e40f → main`，`git ls-remote` 读回 `b10e40f0cba…` 与 HEAD 逐字相等——**推送结论只看这条对平**，与历轮口径一致。

本轮 0 改正文页，所以读者拿到的**内容**就是 §三 那趟全站水合扫描量过的状态（106/106 页、276 条公式 `problems=0`），内容侧线上复核已在扫描里完成，无单独改页需复查。还在同步的只有 changelog / README 两份元数据页：`check_live_sync.py` 首探读 `.md` 腿停在第 73 次、`html` 腿停在第 72 次（第 74 次尚未上线）——这与第 73 轮收尾那次同族（发布延迟是每页、随时长的长量）。按既定口径，**changelog 页 HTML 腿的延迟不算本轮未完成**，内容是否上线看上面的水合复核。`.md` 腿到第 74 次后本节读数记入下方。

## 2026-09-24（第 73 次）四条「读者列宽」轴一直在量**复制稿**：同一页在真浏览器里被侧栏和页内 TOC 吃掉 160px（768 → 608），11 条 display 公式在这一列里得横向拖动（最宽 767px、拖 159px）→ **0**；目检另抓到一条 `[t]` 被 KaTeX 当正文画给读者的静默缺陷，如今守卫和反例都落库

本轮动正文 11 页（只重排公式，没删一个字、没短一条式子），动判据 4 个文件：`tools/checks/check_live_column.py`、`check_svg_legibility.py`、`check_mermaid_geometry.py`、`check_content_overflow.py`。README 统计不动（196 页 / 19 章 / 217 Mermaid / 32 SVG / 8 截图；display 公式 276 条——重排前后逐页对齐断言 `len(before)==len(after)` 钉着，一条也没多、没少）。

### 一、缺陷本身：轴量的那个 768 不是读者拿到的 768

第 62 轮立 `check_live_column.py` 时量到 `<main>` = 768，之后所有几何轴都拿 768 当读者列宽。本轮把同一条探针换成**真线上 URL + Playwright 水合**再读一遍，768 只在部分窗口成立：

| 读者窗口 | 复制稿（Edge 腿，历轮唯一读数） | 线上真实列宽 | 被谁吃掉 |
| --- | --- | --- | --- |
| 390（手机） | 量不到（本机 Edge 把 `innerWidth` 夹在 ~504 起） | **358** | 面包屑导航 215px 占位 |
| 1024 | 768 | **624** | 章节侧栏 288px |
| 1280 | 768 | **608** | 章节侧栏 288 + 页内 TOC 256 |
| 1440 / 1920 | 768 | **768** | 面板开着，但 `max-w-3xl` 先到顶 |

复制稿为什么永远 768：站点的客户端路由认不出 localhost 的文件名，导航面板根本不挂载，`<main>` 于是拿到完整的 768 上限。**这是结构性盲区，不是噪声**——凡是自己渲染「抓下来的线上 HTML」的轴，都在把读者的余量往好处报 160px。SVG 轴的缩放读数同批分开：`00-index` 首页图在复制稿里缩到 0.8，在 1280 窗口线上实绘 **0.633**。

判据改动：`check_live_column.py` 加 `hydrated_leg`（5 个断点、URL 从 `llms.txt` 读、不猜），两数并排打印，差值记 `AWAITING-DECISION: COPY-OPTIMISTIC` 而**不记 problem**（列宽是平台给的，改判据改不出来）；本轮复跑 `problems=0 awaiting-decision=2`、`exit=0`。

> 新守卫先咬了自己一口：`HYDRATED_PROBE` 第一版把 960px 控制盒种进图片自己的 wrapper 里，shrink-to-fit 的 wrapper 被撑到 960，**随后量的图就读成了原始尺寸**——于是「GitBook 给宽图配横向滚动条」这条假结论被打印过一次。改法是探针先读页面、最后才种控制盒；这条顺序现在写在代码注释里当断言用。

### 二、公式轴装第二条腿，并把 11 条重排到位

`check_content_overflow.py` 从单列改成一趟扫两列（`--laptop-column`，默认 608，`0` 退回只量认证列）。逐条前后账用 `git show HEAD:` 取旧 LaTeX 重新量，不靠本轮笔记：

| 页面 | 条 | 旧自然宽 / 608 里拖 | 新自然宽 / 拖 |
| --- | --- | --- | --- |
| `02-agent-basics/perception-planning-action.md` | #3 | 767 / **159px** | 431 / 0 |
| `09-frameworks/autogen.md` | #1 | 718 / 110 | 482 / 0 |
| `07-planning/workflow-orchestration.md` | #2 | 691 / 83 | 376 / 0 |
| `12-applications/research-agent.md` | #1 | 673 / 65 | 341 / 0 |
| `12-applications/customer-service-agent.md` | #1 | 662 / 54 | 496 / 0 |
| `12-applications/rpa.md` | #1 | 657 / 49 | 489 / 0 |
| `11-engineering/deployment-scaling.md` | #4 | 652 / 44 | 201 / 0 |
| `06-memory-rag/graphrag.md` | #2 | 643 / 35 | 475 / 0 |
| `05-tool-protocol/function-calling.md` | #2 | 638 / 30 | 372 / 0 |
| `06-memory-rag/rag-basics.md` | #1 | 637 / 29 | 380 / 0 |
| `11-engineering/tool-registry.md` | #2 | 627 / 19 | 483 / 0 |

全站复测（276 条 / 106 页，`katex@0.18.7`，`render-errors=0`）：

```
-- verdict (column 768px …) --  over-column=0  at-or-above bar(16 px drag)=0  unreachable=0
-- verdict (column 608px …) --  over-column=1  at-or-above bar(16 px drag)=0  unreachable=0
   natural width (px): min=71 p50=341 p90=511 p99=597 max=620
   headroom: 4 formulas use more than 95% of the column
     (ai-ml-dl=598, benchmarks=597, tool-permission-sandbox=597, pretraining-finetuning=586)
```

修法一律是 `aligned` / `cases` 换行重排，**没有一条靠删项或缩写凑数**（脚本断言「重排后自然宽变大的条数 = 0」）。认证列仍是 768（README 引的就是它），608 是作者该对齐的更严读数——本轮之前，一条卡着 768 写出来的式子可以静静地在笔记本用户那儿多拖两个字。

**留下的一条例外**（诚实记在这里）：`03-llm/rlhf-dpo-alignment.md` 的 DPO 损失在 608 列里自然宽 620.28px、拖 12px，未达 16px 门槛所以判绿。它是那条公式的唯一一次没被动过：为一行 12px 把业界通用式拆成两行，代价大于收益。

### 三、目检抓到的静默缺陷：`[t]` 被当成正文画给读者

`06-memory-rag/graphrag.md` 里那条 `\begin{aligned}[t]`（套在 `cases` 内）**解析零报错**、`render-errors=0` 照样绿，浏览器却把 `[t]` 两个字符老老实实画在每条分支前面。amsmath 的环境选项 KaTeX 根本不实现——这类缺陷只在「看一眼渲染」时露脸，276 条批量渲染图本轮逐张目检才逮到它（同一条上另一次尝试用 `hphantom` 只把 627 降到 616，仍超 608，也是第二条腿打印全部越线读数才看见的）。

落库成守卫：`STRAY_RE` + `stray_markup()` 只读 `class="katex-html"` 之后的纯文本（`.katex-mathml` 里带 `<annotation>` 存 LaTeX 源码，扫它会让全书每条公式都中招——这条写在注释里）；`ruler()` 常驻反例 `PLANT_OPT` 种一条 `[t]` 环境选项，断言守卫必须捉住，同时断言一条干净公式**不能**被捉。读数：`stray-markup control ok: a planted amsmath '[t]' option paints '[t]' as text and the guard sees it; a clean formula does not`。守卫进退出码：`stray` 非空即 `exit 1`。

### 四、另外两条轴同批改上「笔记本读数」，但都只报不判

| 轴 | 768 列（判据） | 608 列（只打印） |
| --- | --- | --- |
| `check_svg_legibility.py` | `0 张图 / 1109 个标签` 越 12px 线 | **32 张图 / 1066 个标签**越线（缩放 0.633、0.475） |
| `check_mermaid_geometry.py` | 24 张图最小标签 <12px | **91 / 217 张**；最宽 `12-applications/README.md#1` 1116px → 768 里 11.0px、608 里 **8.7px** |

两条都明写 `not counted as findings`：为 608 重画全书 32 张手绘图、或收窄 102 张超宽 Mermaid，是版式取舍，按停一停条款等操作者定。Mermaid 那条 608 读数由本轮渲染推导，并已与真 608 渲染对平（实绘字号差 0.1%，越线计数只差 1 张卡在门槛 0.006px 上的图），所以它是账、不是逐图判词。

### 五、结构回归与统计口径

批量改 11 页公式后全部离线轴复跑：`check_structure` 198 页 `problems=0`、`check_katex_formulas` 927 条 `failures=0`（引擎对齐 0.18.7）、`check_char_sanity` 36 万正文汉字 `findings=0`、`check_nav_h1_sync` 196 页 `problems=0`、`check_changelog_headings` `HEAD=64 tree=64 lost=0`、`check_source_pointers` 191 页 `findings=0`、`check_prose_duplicates` `dup=0`（近重复带 3 条仍是模板对，旧账）、`check_table_overflow` 2368 格 `spill=0 bust=0 problems=0`、`check_readme_stats` 全部 `ok`。`check_mermaid_geometry` 仍 `exit=1 problems=102`——第 62 轮那笔等站点开关的旧账，本轮 217/217 真渲染、`local=11.14.0 live=11.14.0`、分布 `101 缩放 / 0 横向滚动 / 116 原样` 与旧账逐项一致，不是回归。

### 六、留下的账与下一步

1. **产品级取舍（要操作者定，三条路都量过）**：(a) 为 608/手机 358 列重画 32 张手绘 SVG（作者字号得 ≥18.9px）；(b) 开 GitBook 宽版布局（`--column 1152` what-if 读数 `over-wide=0`，但公式 wrapper 是硬 `max-w-3xl`，不跟着变宽）；(c) 接受笔记本上的缩小现状，只把 608 当作者目标列。
2. 102 张超宽 Mermaid 仍在等同一个开关；静态相位腿只有 1 个相位；8 张 PNG 截图仍没有任何轴读它们。
3. 未做：公式轴的 358px（手机列）没有装成第三条腿——手机读者本就可以捏合放大，先当背景不当判据；跨页重复正文剩 ~2250 个「」串需要引用/术语分类器。
4. 复现命令：
   ```
   python tools/checks/check_content_overflow.py            # 两列一趟扫完，exit 0
   python tools/checks/check_live_column.py                 # hydrated 腿：358/624/608/768/768
   python tools/checks/check_svg_legibility.py              # 768 判绿 + 608 只报
   python tools/checks/check_mermaid_geometry.py            # problems=102 = 第 62 轮旧账
   ```

### 七、收尾补记：线上水合页面逐条复核，以及本轮的发布延迟读数

离线判据全绿不等于线上读者看到了。本轮的 11 页改动最后用 **Playwright 打真线上 URL** 复量一遍（URL 从 `llms.txt` 解析，不猜）：

| 断言 | 读数 |
| --- | --- |
| 抽查页数 / display 公式条数 | **11 页 / 29 条**（每页线上条数与仓库作者条数逐页对齐） |
| 线上 `<main>` 宽 | 11 页全部 **608**，与 §一 表格的 1280 窗口读数一致 |
| 拖动 ≥16px / `.katex-error` / 渲染文本里的 `[t]` | **0 / 0 / 0**，`problems=0` |
| 尺子锚点 | 种在页尾的 200px / 960px 控制盒线上读数 **200 / 960 分毫不差**；KaTeX webfont 已加载（否则宽度是回退字体的假数） |
| 目检 | 每页最宽公式各出一张真图；`graphrag` 那页 4 条**全部**单独出图，含 §三 那条旧 `[t]` 缺陷式——线上画的是完整大括号 + 两行分支，无残留字符 |

发布延迟本轮又走成长腿：推送后 18 分钟复探，`.md` 腿已带第 73 次，**changelog 页的读者可见 HTML 腿仍是第 72 次**（`missing 73`）。这与第 59 轮（75 分钟）同族、与第 68 轮（约 1 分钟）不同，所以口径不变：**推送结论只看 `git ls-remote` 哈希 == HEAD**（本轮 `99f6fc3` 已对平），内容页是否上线看上面的水合复核，changelog 页的 HTML 腿延迟不算本轮未完成。

## 2026-09-24（第 72 次）两把尺子各自量不到的那一半：字号轴**看不见图内部的 `scale(k)`**（全站 1127 个标签里 1 个中招，读数 12.80px → 12.16px，浏览器逐像素认了），引用轴**把「动词必须贴着引号」当成了引用的定义**（被归因的引用 12 → 15）；引用轴另外装上「自证」和「否定式引用」两个新桶——`findings=0` 从今往后不再被读成「所有引用都核过」

本轮动正文 0 页、0 张图，判据改动 2 个文件：`tools/checks/check_svg_legibility.py`、`tools/checks/check_quote_fidelity.py`。README 统计不动（196 页 / 19 章没变）。顺带把第 71 轮 §八 那段线上记录改对了：当时写「读者可见那条腿本轮没跟上」，第 24 次探测证明它跟上了（HEAD 之后约 40 分钟），日志不该留下一句比实测更悲观的话。

### 一、字号轴把「画布缩放」当成了唯一的缩放

第 71 轮 §七 第 4 条点名的就是它：有效字号 = 作者字号 × min(1, 列宽/viewBox 宽)，这个式子里没有 SVG **自己内部**的缩放。而 `<g transform="translate(54,140) scale(0.95) translate(-62,-144)">` 是房规里为了把徽章塞进格子常用的手法——它把整组内容连字一起缩了，轴看不见。

改法是 `transform_scale()` / `element_scale()`：沿祖先链把每个 `scale()` / `matrix()` 的**最小轴**乘起来（取最小是因为压扁文字的是短轴），`style="transform:…"` 里的也算。

| 量什么 | 读数 |
| --- | --- |
| 落在被缩放组里的标签 | **1127 个里 1 个**（`08-collab-patterns.svg` 的「主管」徽章） |
| 那个标签的作者字号 | 16.00 → **15.20** px |
| 768px 读者列里画出来 | 12.80 → **12.16** px（门槛 12.0） |
| 判决 | 不变：`0 张图 / 1109 个标签越线` |

所以这条**不是修缺陷，是补一条会咬人的守卫**：那个徽章离门槛只有 0.16px，下次谁再给它加一层 `scale(0.9)`，旧尺子会照样报绿灯。分类器多种子第 10 张现在钉着这个分支：`a scale(0.7) ancestor takes a 16px label down to 11.2px`。

**目检用浏览器量，不用我的算术**：把真图内联进 768px 宽的盒子，旁边再放一张同 viewBox、同 `translate/scale` 构造的对照图（16px 缩放 / 15.2px 不缩放 / 16px 不缩放三个样本），让 Edge 报 `getBoundingClientRect()`：

```
逐字宽度  plain-16px 12.850 | scale(0.95) 12.160 | plain-15.2px 12.160 | 真图那个徽章 12.164
```

`scale(0.95)×16px` 与 `15.2px` 是**同一笔像素**，真图那个徽章和它们也同一笔——轴现在的说法和浏览器一致。

> 这一腿差点自欺：文字盒子的 **height 是行盒**，浏览器取整（16 与 17），拿高度算比值会得到 0.941 这种看着像 0.95 又不是的假数。宽度是墨迹推进、连续的，所以断言全部改用宽度，比值只当参考。

线上腿复跑 `check_svg_legibility.py`（不带 `--no-live`）`exit=0`：`<main>` 仍是 768，960 画布的图在线上确实按 0.8 缩（`live 02-agent-basics: scales [0.8]`）。

### 二、引用轴把「动词贴着引号」当成了引用存在的条件

旧判据是 `ATTR = VERB + \s* + QUOTE`：动词和引号之间只许有空白。于是 `图注：「…」`、`结论原文是「…」` 这类句子——中间隔一个冒号或系动词——在轴眼里只是「一句带引号的话」，**根本不提问**。按第 71 轮 §七 第 1 条定的规矩先量再修：沿用现有动词表、把间隔放宽到 ≤3 字，全站这样的引用有 2 处（本轮 §八 那段补完之后是 3 处）。

改法是 `GAP = r"[\s，、：:是为的“”\"']{0,3}"`：**被归因的引用 12 → 15**，`findings` 仍是 0。三条新账全部逐字落位：

| 位置 | 句子 | 归因到 |
| --- | --- | --- |
| `14-templates/style-guide.md:…` | `图注：图下方空一行写 …` | 房规本身，不涉外部 |
| `00-index/changelog.md:1164/1165` | 第 55 轮那两条 `页面上的图注原文是…` | `19-labs/lab1-react.md`、`16-ai-infrastructure/prefix-cache-context-engineering.md`（逐字） |
| `18-frontier-2026/system-one-decision-models.md:107` | `结论原文是「promising, but early」` | 见第三节 |

**间隔不是越宽越好，这一条是变异测试量出来的**：把 `GAP` 换成 `.{0,3}`（不看词表、只看长度），轴的读数变成 `attributed quotes=19 findings=2`。那两条红的都是**日志在复述自己已经改掉的错**——`原句抄成了「最宽 1116px…」`、`被吃掉的第 58 次标题（「上一轮把公式判据落了库」）`——正是本文件 scope rule 拒绝担保的那类。所以那个字符表是校准出来的，不是随手列的：内容词（`抄成了`、`（`）一旦能填进间隔，动词就不真正「拥有」那个引号了。

9 个变异体现在全部被 `--selftest` 抓住（GAP 三种、否定分支三种、自证分支三种）。其中两个是**第一轮活下来、逼我补种子的**：`negation window 12→400` 与 `evidence check always fails`——前者说明我只钉了间隔词表没钉窗口，后者说明跨文件取证那条腿没有专属反例。

### 三、`findings=0` 之前把两种「轴其实没检查」混在 PASS 里报

加宽动词间隔之所以值得配两个新桶，是因为新收进来的引用暴露了这条轴的循环论证：

- **SELF-EVIDENCED**——引号里的话在全站只出现在**它自己那一句**里。知识页引用外部原文就是这个形状：旧判据等于「在自己的引号里找到了自己的引用」，白拿一个 `PROSE`。本轮 1 条。
- **NEGATED**——句子说的是**没有**一处写着它（`09-frameworks/llamaindex.md:142`：这份契约里没有任何一处写着 …）。旧判据对它是**反的**：它要求那句话在树里找得到，而作者的主张恰恰是它不在。存在证明不了、不存在也证明不了（语料是手册，不是 LlamaIndex 的文档）。今天它靠自证侥幸没红；下一句诚实的「文档里没写「X」」就会红。本轮 1 条。

摘要行因此多了两个数：`attributed quotes=15 findings=0 verified=13`，两个新桶逐条打印，谁也不能把它们读成「核过了」。

那条 SELF-EVIDENCED 的外部引用手工补核了一次（离线轴到不了的地方，按页面自己列出的参考链接抓 LangChain 那篇）：原文确实是 `The results are promising, but early.`，同一行表格里的每个数字也都对得上——5 条固定轨迹、每条 100 次共 500 次判定、与人类标注一致率 100%/99.8%/96.4%/80.0%、单次 $0.00035、总计 $0.34 vs $28.17。**SELF-EVIDENCED 不是指控，是这条脚本在说「这一条我没查」。**

### 四、回归读数（同一棵树 `096126f` + 本轮两个判据文件，正文与图都没动）

| 腿 | 读数 |
| --- | --- |
| `check_quote_fidelity --selftest` | `23 assertions, 12 groups` 全对 |
| `check_quote_fidelity`（写完本条目**之前**） | `sources=230 attributed quotes=15 findings=0 verified=13 {FIGURE 1, RETRACTED-OK 6, PROSE 6, NEGATED 1, SELF-EVIDENCED 1}` |
| `check_quote_fidelity`（写完本条目**之后**，本轮末读数） | `sources=230 attributed quotes=16 findings=0 verified=14 {FIGURE 1, RETRACTED-OK 6, PROSE 7, NEGATED 1, SELF-EVIDENCED 1}`。多出来那 1 条是本条目第二节表格里 `system-one-decision-models.md:107` 那一行的英文引用——它归因到正文页，跨文件命中所以判 `PROSE`，也就是这条日志被自己新写下的话核了一次。（这一行的数字**不能再含被引号包住的原文**，否则它一边记录读数一边把读数改掉——本行本身因此写成不带括号的指称。） |
| `check_svg_legibility --no-live` | `labels below 12px at a 768px column: 0 figures, 0 of 1109`；分类器 4 种子里含 scale 那一张 |
| `check_svg_legibility`（含线上腿） | `exit=0`，`<main>=768`，960 画布 scales `[0.8]` |
| `check_svg_phase_legibility --selftest` / `--mode all` | `25/25`；`findings: 0 label(s) across 0 figure(s)`，`swept 1063 labels over 456 phases`，未定价 0 |
| 其余 9 条离线腿 | `check_structure 198 页 problems=0`、`check_nav_h1_sync problems=0`、`check_readme_stats`（README/首页/横幅三口径全对）、`check_char_sanity problems=0`、`check_katex_formulas 108 页 927 式 failures=0`、`check_prose_duplicates exit=0`（3 对 0.73–0.78 的近重复， informational）、`check_source_pointers 191 页 findings=0`、`check_widget_pairing 198 页 problems=0`、`check_changelog_headings HEAD=63 tree=63 lost=0` |
| 附带复跑 | `check_svg_fit figures with a fatal problem=0 of 32`、`check_content_overflow bar=16px drag -> 0 formulas to fix` |

### 五、留下什么

1. **覆盖率仍然要连着分母读**：markdown 里 ≥6 字的 「…」 串 **2265** 个，被归因语法看见 **15** 个（0.66%；本轮末复读 16 个，多出来的那条是本条目自己写下的引用——这条轴量的是包括它自己在内的树）。绝大多数是术语名和小节名，不是引用；但把剩下的分类需要一个判据，而以误报为主的轴没人会信——这条第 71 轮就挂着，本轮没有动它。
2. `NEGATED` 的 12 字窗口**对今天的语料不承重**：把窗口放宽到 400 字，本轮整棵树读数一模一样（`verified=13`，即「写完本条目之前」那一行的口径）。它是保险，不是当前判决——这一点写在这里，免得后来人以为它在挑毛病。
3. `SELF-EVIDENCED` 的正解是内容侧的：外部原文该配可抓的链接和明确的「以下为原文」标位，而不是让判据去猜。本轮只把它标出来，没改页面。
4. 动词表还是闭合词表（本轮新收的 3 条靠的是间隔，不是新动词）。表外动词 = 静默漏检，同第 71 轮第 3 条。
5. 8 张真实产品截图（PNG）里的字仍然没有任何一根轴能读：图内文字腿只覆盖自绘 SVG。
6. 第 71 轮那本账原样：102 张超宽 mermaid 在等站点那个开关；静态腿只有 1 个相位；宽版（`--column 1152`）与移动宽度未重测。

### 六、线上抽查（推送 `06411f0` 之后）

本轮没改正文也没改图，改的是两根尺子和这条日志，所以线上腿只挑两件真会翻车的事量。

**发布延迟**：推送后第一次探测两条腿都还是第 71 次（md 184,267 B / 99 条、html 14,347,202 B / 359 条），约 2 分钟后第二次探测两条腿同时到第 72 次（md 193,716 B / 104 条、html 14,955,706 B / 375 条）。和第 59、61 轮量到的节奏一致：**先旧后新，一两分钟内追平**，所以推送完立刻读线上一定读到旧的。

**新尺子那个 `scale()` 项在读者那边是不是真的**：这条假设不成立的话，第 72 轮报的 12.16px 就是纸面上的。取承载那张图的页面（`08-multi-agent/multi-agent-collaboration.md`）上 `img` 自己写出的代理地址（不猜 URL），拉回读者真正拿到的字节：9,169 B，24 个标签，用同一套 cascade 重算——最小标签画布尺寸 15.00px、768 列里 12.00px，和作者那份**逐个相等**；`scale(0.95)` 也确实在返回的字节里。`check_svg_sanitizer --only` 那条轴同向：元素/属性多重集无差异，`relying on a stripped feature=0`。结论：平台没有把 transform 剥掉，12.16px 是读者看到的。

**真实渲染目检**：把那份线上取回的 SVG 放进 768px 列、`max-width:100%`，Edge headless 以 1x 截图。四种协作拓扑的四个卡片、中间那条红底反白结论、以及被 0.95 缩过的 主管 徽标都清晰可读，没有压框、没有叠字。

（这一节刻意不写任何被引号包住的原文：本条目一写引用，第四条表的读数就跟着动。）

## 2026-09-24（第 71 次）引用回核轴补上它一直读不到的两类字：**画在图里的标签**和 **Mermaid 节点标签**，登记旧措辞改成「旧句消失 + 新句在位」两侧断言；修尺子时又挖出它自己的围栏状态机 bug（会把图后面的整段正文吞掉）——同一棵树上手改前后 `unmatched 3 → 0`

本轮动正文 0 页、0 张图，判据改动 1 个文件 `tools/checks/check_quote_fidelity.py`。README 统计不动。

### 一、为什么它值一整轮，而不是第 70 轮的一条备注

第 70 轮收尾时这条轴是红的，而且红在**上一轮自己写的日志行**上。本轮在 `d400aa8` 这棵树上当场复跑 HEAD 版脚本，读数是 `content pages=197 attributed quotes=10 unmatched=3`（第 70 轮条目里记的是 9/2：每往日志里加一句带 「」 的话，这条轴的分母就跟着长，9/2 是写完那段条目**之前**的读数；多的那一条是同一个图内标签在 `changelog.md:71` 与 `:384` 各出现一次）。三条红没有一条是日志说错了话，全部是**尺子看不见**：

- 两条 `标题「拉财报数据/生成报告」`——这句话第 65 轮就被压短重排成图里那两个格子，脚本要判它，得能读 `<text>` 节点，而旧语料只收 markdown 围栏外的正文。
- 一条 `写着「从原理到生产：187 页/19 章」`——第 64 轮**删掉**的假话。旧登记只会要求「README 还印着它」（那是公告牌：把假话印在旁边挂着判决的地方），对一张图里的旧措辞这条豁免无话可说。

一条量不到的引用不是「中性」，是**假阴性**：它让 `findings=0` 读起来像「所有引用都对」。

### 二、语料加宽到三类字

| 源族 | 旧语料 | 本轮 | 为什么该收 |
| --- | --- | --- | --- |
| markdown 正文（围栏外） | 收 | 收 | 引用主体 |
| 自绘 SVG 的 `<text>`/`<tspan>` | **不收** | 收 | 第 64 轮不得不给横幅单独开一条 banner 腿——只活在图里的页数失真了九轮 |
| ```mermaid 节点标签 | **不收** | 收 | 围栏对正文要剥（示例代码不是断言），但 mermaid 围栏是**用另一种语法画的图** |
| `python`/`bash` 等示例代码 | 不收 | 仍不收 | 命中一段示例代码不等于读者在正文里被告知过 |

第三类不是「多收点字」，它带一条规则：**同源拼接**。`「拉财报 / 出报告」` 指的是 `4 拉财报` 和 `5 出报告` 两个格子——人指图就是这么指的。所以拼接的每一段必须落在**同一个源**里；跨两张图各凑一段不算证据。反例 `亮起来的一格 / 反向传播普及`、`拉财报 / 反向传播普及` 两段都在树里、但从不同时出现在一个源里，必须被拒（`join=2` 那条控制就是它）。

同批次还立了三条**差分**控制：图内控制必须**不在**正文和 mermaid 里、mermaid 控制必须**不在**正文里。否则「绿了」只证明正文腿很宽，不证明新分支被走到。

### 三、登记旧措辞从单侧改成两侧

每条登记现在必须写全 `old / new / source / billboard / round / why`：`old` 必须**哪儿都找不到**（只有 `billboard` 那一处可以留着），`new` 必须**在 `source` 那个文件里找得到**。三条登记全部有 git 出处（第 62 轮 1120→768、第 65 轮 `07-plan-vs-react` 重排、第 64 轮横幅 187→196）。判决顺序也定了：**先查登记，再查命中**——反过来，公告牌那一次合法 find 就会把一条登记洗白成普通引用，豁免吃掉断言。

### 四、修尺子的过程中发现它还在骗人（本轮最值钱的一条）

第一版把「剥 mermaid 围栏」和「剥所有围栏」写成两个独立正则，它们互相打架：先删掉 ```` ```mermaid ```` 那两行，剩下 ``` 行的**奇偶就变了**，正文腿于是把图后面一整段当成代码吞进肚子里。后果不是少收几个字，是**真引用被报成 UNMATCHED**——`16-ai-infrastructure/prefix-cache-context-engineering.md:34` 那句命中率从 20% 提到 80% 就是这么丢的（`HIT CONTROL BROKEN (prose)`，第一次跑就撞上）。

- 空转地板先把这件事量出来：带 mermaid 的页数 **172 → 158**，14 页的图被当成没图。
- 改成一次线性扫描的三桶状态机（正文 / mermaid 体 / 其他围栏），并按 CommonMark 认闭合：**只有不带 info 的 ``` 才是闭合**。
- 这条 bug 现在有种植反例守着。`--selftest` 第 9、10 张：图后面那段正文必须还在语料里、图里的字不许漏进正文、没闭合的围栏不许回头吃掉它上面的正文。变异测试（把那一行替换回错版再跑 selftest）确认它真的响：`MUTANT CAUGHT by selftest: prose under a diagram was swallowed by the fence state`。

### 五、目检：登记的新措辞不能只信脚本

按读者列宽 768px 真渲染两张被登记的图，逐张看过：

- `.tmp-projects/r71_shot_07plan.png`（`07-plan-vs-react.svg`）：第 4、5 格确实画着「拉财报」「出报告」，全图找不到「拉财报数据」「生成报告」；
- `.tmp-projects/r71_shot_banner.png`（`banner-home.svg`）：「从原理到生产 · 196 页 / 19 章」与「19 章 · 196 页全景」在位，「187 页」已经不在图上。

### 六、读数与回归

同一棵树（`d400aa8`，正文与图都没动）先跑 HEAD 版脚本、再跑本轮版脚本：

| 脚本 | 语料 | 被归因的引用 | 红 |
| --- | --- | --- | --- |
| HEAD（第 70 轮版） | 197 页 markdown 正文 | 10 | **3** |
| 本轮版（写完本条目之前） | 197 页正文+mermaid + 33 张图 = 230 源 | 10 | **0**（`PROSE 5 / RETRACTED-OK 4 / FIGURE 1`） |
| 本轮版（写完本条目之后） | 同上 | **12** | **0**（`PROSE 5 / RETRACTED-OK 6 / FIGURE 1`） |

分母从 10 长到 12 是本条目自己造成的：它引用了那两句被删掉的旧措辞。这正是第一节里 9/2 变成 10/3 的同一个机制——**这条轴每轮都会把自己刚写下的话纳入判决**，所以「清零」之后必须连分母一起报，否则读不出「少问了两个问题」和「两个问题都有答案」的区别。

- 控制：`hit=2 figure=1 mermaid=1 phantom=3 join=2 retractions=3` 全过；`--selftest` 10 张种植判据全对；变异测试 1 次（把闭合规则改回错版，必须被抓住）。
- 离线全量回归 14 条腿全部 `exit=0`：`check_structure 198 页 problems=0`、`check_nav_h1_sync 196 页 problems=0`、`check_readme_stats`（README/首页/横幅三个口径全对，196 页 / 19 章）、`check_char_sanity 198 页 355775 字 findings=0`、`check_katex_formulas 108 页 927 式 failures=0`、`check_prose_duplicates`、`check_quote_fidelity`（含 `--selftest`）、`check_source_pointers 191 页 findings=0`、`check_widget_pairing 198 页 problems=0`、`check_changelog_headings HEAD=62 tree=63 lost=0`、`check_svg_label_parity`（本轮无 SVG 变动）、`check_svg_phase_legibility --selftest 25/25` 与 `--mode all`（1063 标签 / 456 相位 findings=0、未定价 0）。
- 浏览器腿沿用第 70 轮：本轮 0 页正文、0 张图变动，唯一被改的视觉事实是那两张登记图的**读法**，已按第五节真渲染目检。


### 七、留下什么

1. **这条轴的覆盖率本轮第一次量出来：markdown 里 2249 个 「…」 串，被归因语法看见的是 10 个（0.4%）。** 绝大多数 「」 是术语名和小节名而不是引用，所以这不是 bug；但从今往后 `findings=0` 必须连着这个分母一起读。把剩下的分成「引用」和「名词」要一个分类器，而一条以误报为主的轴没人会信——列为下一轮候选（先量再修）。
2. 8 张真实产品截图（PNG）里的字仍然没有任何一根轴能读：图内文字腿只覆盖自绘 SVG。
3. 归因动词是闭合词表（本轮实际命中的只有 4 个：`写着` 6、`标题` 2、`图注` 1、`页面里` 1）。新写法用了表外的动词就是**静默漏检**，这条和上一条同因。
4. 第 70 轮留下的账原样不动：102 张超宽 mermaid 在等站点那个开关；静态腿只有 1 个相位；`check_svg_legibility` 仍看不见 `transform="scale(k)"`；宽版与移动宽度未重测。

### 八、线上腿（提交推送后补测）

推送 `6a68dd4` 后按流程 (5) 做线上抽查，三条腿：

| 腿 | 判据 | 读数 |
| --- | --- | --- |
| 服务副本配色 | `check_svg_served_colours.py`（读者拿到的 SVG 字节 vs 树里） | `assets=17 reached=17 mismatched=0 unreachable=0`，控制 `00-learning-path.svg` 按 `d400aa87^` 判为 **DIFFERS**（缺 8 个色、多 8 个色）——它必须不同，否则说明比的是旧副本 |
| 服务副本图内文字 | 临时腿：把第 65/64 轮登记的**新**措辞在被代理的 SVG 字节里逐条找回来，同时确认**旧**措辞不在 | `assets=2 findings=0`（`拉财报`/`出报告` 在位，`拉财报数据`/`生成报告` 不在；横幅 `196 页` 在位，`187 页` 不在） |
| 真机渲染目检 | Edge headless 抓线上整页 | 首页 `.tmp-projects/r71_live_home.png`：横幅读作「从原理到生产 · 196 页 / 19 章」、第 70 轮改过色的章节胶囊逐枚可辨；`11-engineering/logging-tracing-monitoring` 整页 `.tmp-projects/r71_live_11.png`（1280×12000）按色块密度切带后目检 band 3：第 68 轮重画的可观测性控制台示意图**在读者列宽里原样画出**，`状态·错误`/`耗时·大于 5 秒`/`查财报 超时` 与那枚红 `×` 全部清晰、无裁切，两级图注都在 |

**读者可见那条腿一度没跟上，第 24 次探测追平**：`check_live_sync.py` 连测 23 次 / 38 分钟，`.md` 腿已经是第 71 次而 HTML 腿仍停在第 69 次（字节数一直锁在 12,879,630）；第 24 次探测（HEAD 之后约 40 分钟）读到 `leg md newest round=71 (184,267 B) / leg html newest round=71 (14,347,202 B, 359 rounds)`——**本轮线上抽查到此全部通过**。这不是推送失败（`git ls-remote` 的 `refs/heads/main` 与本地 HEAD 同哈希），而是第 59 轮量过的同一种每页独立滞后（那次 75 分钟），只是又一次证明**它没有常数**。上面那张整页截图是在追平之前画的，因此是「第 69 次那一版页面」；本轮 0 页正文变动，被抽查的两张图分别在第 68、70 轮就已上线，所以目检仍然有效。

**这一腿里我自己踩的两个坑，值得留在日志里**（都属于第 62 轮「404 页也照样打印自信数字」那一类）：

1. 想单独给一张图出线上截图时，我拿 `SITE + "/.gitbook/assets/名字"` 拼了 URL——Edge 老老实实画了一张 **84,827 字节、`rc=0`** 的「Page not found」。字节数和退出码都不证明拿到了图。
2. 页面里 `<img>` 的 src 是平台代理地址，且 `&` 在标记里是 `&amp;`；照原样请求得到 `HTTP 400 Missing url/sign parameters`。**必须先 unescape**，且判「是不是 SVG」要看响应头几个字节，不能看文件名。

因为这两条，独立的「单图线上腿」并回了整页截图这条腿——页面级证据本来就更强。


## 2026-09-24（第 70 次）配色轴补齐另一半：18 张**静态**图从没被量过颜色（567 个标签），越线 115 个 → **0 个**；然后把尺子加严三次（元素级归因 / 渐变墨定价 / 渐变底板逐点插值），每加严一次都重新量出真缺陷（25 个、7 个）并清零


本轮动正文 0 页、手绘 SVG 17 张（三批共 121 处作者写的颜色字面量，落在 95 行上），判据改动 1 个文件 `tools/checks/check_svg_phase_legibility.py`。README 统计不动（页数/图数/张数一项都没变，只改已有图的颜色）。

### 一、这条轴补的是第 69 轮自己留下的缺口

第 69 轮那条轴是**动画相位**轴，`MIN_FIGURES=10` 只扫了 14 张会动的图。也就是说：全站 32 张手绘 SVG 里，**18 张静态图（567 个标签）从来没被任何一根轴量过配色**——字号轴量它们多大，几何轴量它们撞不撞框，但没有一根轴问过「这行字坐在什么底上」。本轮把轴开成 `--mode {animated,static,all}`，静态腿一遍扫完（静态图只有 1 个相位，所以 567 标签 = 567×1 次判决），门槛沿用第 69 轮落地的 WCAG 1.4.3 分档（小字 4.5 / 大字 3.0），并加了 `MIN_STATIC=12` 的空转地板。

第一遍读数：**115 个标签越线，分布在 15 张图上**，全部是 `DARK`（稳态越线，不是相位专属），另有 1 个标签**根本没被定价**。

### 二、读数是怎么走的

| 趟次 | 判决范围 | 越线标签 / 越线图 | 未定价 / 覆盖缺口 |
| --- | --- | --- | --- |
| 静态腿第一遍（`--mode all`） | 1063 标签 / 32 图 | **115** / 15 | 1 / 0 |
| 补上「未定价必须算覆盖缺口」后 | 同上 | 115 / 15 | 0 / **1** |
| 美术批 1（92 处字面量）后 | 同上 | **0** / 0 | 0 / 0 |
| 尺子加严：轴对齐渐变底板逐点插值 | 同上 | **25** / 9（3 相位专属 / 22 稳态） | 0 / 0 |
| 美术批 2（22 处 stop）后 | 同上 | **0** / 0 | 0 / 0 |
| 尺子加严：对角线渐变也插值 | 同上 | **7** / 5（5 相位专属 / 2 稳态） | 0 / 0 |
| 美术批 3（7 处墨色）后 | 同上 | **0** / 0 | 0 / 0 |

分母始终是 1063 个标签、456 个相位、93190 个探针点。这张表的重点不是「清零」，是**中间那两行加严**：一份已经绿了的图，把尺子换准之后又量出 25 个、再量出 7 个。第 69 轮的清零是拿「给底板最有利的那一端」定价换来的，本轮把这笔账还上了。

### 三、尺子加严了三次，每一次都种了反例

1. **元素级归因**。旧判决只说「这个标签 3.79」，答不出**是谁**把它压暗的。现在每行带 `[on rect#51 a=1.00 rgb(138,84,241) fill="url(#gGen)"]` 与 `[ink g#52 fill="#FFFFFF" inherited]` 两段：哪一层板、什么 alpha、服务器 id，以及墨色是**从哪个祖先继承**来的。没有这两段，25 个新越线里有一多半没法归因（`06-rag-pipeline` 的「重排」是板暗，`12-coding-agent-loop` 的「否·最多 N 轮修复」是墨浅，改的不是同一个东西）。顺带把「引用悬空的面板」从静默跳过改成**必须计数的未定价**，把「量不到的图」改成带行号的 fatal beacon——一个量不了的板不许被读成通过。
2. **墨色本身是服务器时要定价**。标签自己的 `fill` 是 `url(#…)` 时旧尺子读不出颜色，`banner-home` 那处还会抛异常让整趟没有判决。现在按服务器最有利一端定价，并明确记为一次猜测（全站 6 个点）。
3. **底板渐变改成逐点插值**，这是本轮真正的加严。旧规则：一块渐变板取「离墨色亮度最远」的那个 stop——**读者永远拿不到这个宽免**，因为白字是压在板的**中段**上的。新规则：`objectBoundingBox` 的 `linearGradient` 按渐变轴投影到标签的 6 个探针点上，在相邻 stop 之间线性插出该点的实际颜色（含 stop 自己的 alpha），再往上合成。第 69 轮那条「DARK 判决永远不可能是服务器画法的锅」从此只对**量不动的**服务器成立。

   反例是四张种植图，两两成对：`PLANT_GRAD_MID`（竖向浅→深，白字压中段，必须响）、`PLANT_GRAD_DIAG`（同色标改成对角线，也必须响）、`PLANT_GRAD_RADIAL`、`PLANT_GRAD_USERSPACE`（这两张**必须仍走有利 stop 分支并计为 guess**）。第二项防的是「只修了轴对齐就以为全修了」，后两项防的是把插值套到没有轴的服务器上——`radialGradient` 根本没有 `x1/y1/x2/y2`，硬读就会**凭空造一条水平扫**，交回一个自信的错数，那比不量更坏。`--selftest` 从 16 张种植图涨到 25 张，25/25 判对。

对角线这一条不是顺手加的：先量了全站作者写的 `linearGradient`，**91 个里 21 个是对角线**，而且每张图恰好一个（房风格的那层 wash）。也就是说每个坐在这层 wash 上的副标题，第 69 轮以来都是猜的。

### 四、把「多少判决是猜的」变成一条打印出来的账

加严之前没法回答这个问题，所以本轮起每图打印 `N judged pt, M guessed`，总计再按类拆（一个点可以同时属于多类）：

| | 判定点 | 靠有利 stop 定价 | 其中图案板 | 其中量不动的渐变板 | 其中渐变墨 |
| --- | --- | --- | --- | --- | --- |
| 批 1 之后 | 93190 | 52542（56.4%） | 51624 | 52261 | 6 |
| 批 3 之后 | 93190 | 51630（**55.4%**） | 51624 | **3167** | 6 |

渐变板这一类降了 94%，但总猜点几乎没动——因为剩下的**几乎全是房风格那条发丝网格**（`<pattern>`  tile，51624 个点）。这一项本轮**没有**继续加严：图案 tile 是 0.7px 线 @ 0.22–0.5 alpha 的稀疏网格，按 tile 定价是**有界偏差**（最坏情况是把线当成全铺），而把图案也逐点解析要连 `patternUnits`/`patternTransform`/tile 原点一起处理，收益是几万个点里那点余量。这条账留在每图输出里，将来谁要动它都有基线。

### 五、美术改的是什么，以及要留名的取舍

三批的规则不同，别混着看：批 1 是**浅色 tint 上的深墨不够深**（改墨）；批 2 是**白字压在一块中段太亮的渐变板上**（改板，沿该色相往深处走，且同一渐变两个 stop 不许落在同一档）；批 3 是**插值之后才现形的浅灰副标题**（`slate-500 → slate-600`，7 处）。

- 批 2 里最典型的是 `03-attention`：K/V/softmax 三颗胶囊原来是亮玫红/亮绿/浅长春花，白字全在 3.2–4.0；现在是深绯/深绿/深靛，白字实了，色相身份没换。`05-mcp-architecture` 两块 Client 面板、`09-framework-map-ui` 顶部「怎么选」胶囊、`10-eval-layers` 四条层带、`12-coding-agent-loop` 的「开 PR」卡、`03-context-budget` 的「RAG 检索块」同理。
- 取舍 1：`10-eval-layers` 的琥珀层现在偏棕。和第 69 轮那颗琥珀胶囊是同一个方向，四条层带被拉齐到同一重量之后反而更像一套。
- 取舍 2：`03-context-budget` 与 `05-mcp-architecture` 里带字的青色块走的是 **cyan-700 房风格兄弟色**，比旁边无字的图例 chip 深两档——同一页上会出现两种青，是「有字的板」和「色标 chip」的分工，不是不一致。
- 不许拿删字换绿灯：本轮另落一条断言，把 95 行改动抹掉所有十六进制字面量后必须与原文**逐行完全相同**（结果：非颜色差异 0），并且 17 张图的标签数与文本游程数逐个对平（`labels 1063` 改前改后不变）。

### 六、回归与目检

- 断言级（配色轴本体）：`--mode all` 三批读数为 115→0、25→0、7→0，未定价 0、覆盖缺口 0；`--selftest` 25/25（种植图 25 张全判对）；`check_structure` 198 页 problems=0；颜色字面量断言如上。
- 回归（浏览器腿，逐条串行跑，读的是每条轴自己的退出码而不是包装脚本的）：`check_svg_fit` 退出 0，32 张图 0 张有致命问题；`check_svg_legibility` 退出 0，32 页；`check_svg_sanitizer` 退出 0，没有一张图依赖读者拿不到的标记；`check_content_overflow` 退出 0，16px 门槛下 0 条公式要修。本轮改的 17 张图全在这几条轴的扫描范围内。
- **`check_mermaid_geometry` 退出 1，`problems=102`——这是第 62 轮那笔在等站点开关的旧账，不是本轮回归**。判据先自证再定案：本轮 0 张 Mermaid 被改（动的是手绘 SVG 资产），217/217 真渲染、引擎对齐断言 `local=11.14.0 live=11.14.0`、分布仍是 `101 缩放 / 0 横向滚动 / 116 原样`，与第 62 轮逐项对上；102 行全部是 `OVERWIDE`（自然宽 >768px），`ILLEGIBLE` 为 0 是因为该臂要显式传 `--font-floor`（默认只判宽，第 62 轮那次 126 是带 `--font-floor 12` 的读数）。三条修法（重排 / 等宽版开关 / 加横向滚动）都是版式取舍，按停一停条款继续等操作者定。
- **`check_quote_fidelity` 退出 1，`attributed quotes=9 unmatched=2`——本轮回归抓到的旧账，不是本轮改出来的**。两条 UNMATCHED 都在更新日志自己的老条目里（第 64、65 轮那两段），HEAD 上就是红的，本轮只是把它们读出来：① 一句引的是**手绘图里被改掉的旧标签**（`07-plan-vs-react.svg` 步骤 4/5 原标题「拉财报数据 / 生成报告」压成「拉财报 / 出报告」）——它同时踩了两个坑：这句话当轮就被替换掉了（属于该登记的旧措辞），而且图里的字根本不在 `.md` 语料里（这条轴的覆盖面写小了，即使旧标签还在图上也查不到）；② 另一句引的是**当轮改掉之前的旧横幅文字**（封面横幅「从原理到生产：**187 页** / 19 章」，当天就改成 196），逐字回核必然红——这正是第 62 轮 `RETRACTED` 登记表要解决的那一类，但那套机制的控制项要求「README 至今仍然印着这句话」，横幅这一条不符合（README 是用自己的话转述缺陷，没有逐字印）。两条都属于**尺子的口径缺口**，不是内容缺陷，也不是本轮引入；修法（把 `<text>` 节点收进语料 + 让登记条目自带「旧句已消失、新句在位」两侧断言）单独开一轮做，别塞进本轮的配色故事里。
- 目检：`.tmp-projects/r71_ab.py` 把 17 张图按 HEAD 与工作树**并排**渲染在同一页（两列各 760px，读者那一列宽），逐张看过——白字确实从「糊」变「实」，没有一张丢字形、没有一处版式位移。

### 七、留下什么

- **51624 个探针点仍是按 tile 猜的**（房风格发丝网格），本轮决定不做图案逐点解析，理由与代价写在第四节。
- **墨色一侧的有利端宽免没有改**：标签墨色本身是渐变/图案时仍取最有利一端（全站 6 个点）。改它要先把「字形的墨是怎么铺的」这件事建模，收益远小于图案板。
- 第 69 轮清零后剩下的薄边还在：十余行读数落在 4.51–4.60 之间，是**踩线读数**不是富余读数。
- 静态腿只有 1 个相位，所以它量不到任何相位类缺陷——那一类仍只有 14 张动画图被覆盖，这是轴的定义而不是本轮的漏项。
- 未做（与第 69 轮同批 carried）：`check_svg_legibility.py` 仍忽略 `transform="scale(k)"`；文字压在 foreignObject 卡片上时 STROKE 臂看不见；宽版布局（1120 列）与移动宽度未重测；读者侧线上渲染那半截 leg 还没落进 `tools/checks/`。
- 第 62 轮那 102 张超宽 Mermaid 图仍在等站点开关（本轮回归属复跑，读数一字不差）。
- **`check_quote_fidelity` 的两条 UNMATCHED 留给下一轮单独修**（第六节末条已把根因写实：语料要收 `<text>` 节点，登记旧措辞要变成「旧句消失 + 新句在位」的两侧断言）。不在本轮顺手改：本轮的故事是配色轴，混进第二条轴的判据改动会让「这轮到底动了什么」说不清。

### 八、本轮另外探过的两条腿（负结果也记，别让它只存在于对话里）

- **薄页 / 信息密度 / 无图页**：临时探针 `.tmp-projects/r71_density.py`（正文 = 去掉围栏、行内码与 HTML 注释；信息量 = 标题 + 列表项 + 表格行 + 围栏 + Mermaid + 图片 + KaTeX + 提示卡 + 站内链；一张图 = 一个 Mermaid 块或一处图片引用，房规「每页有图」是把 Mermaid 算进去的）。167 页读数：中文字数 `p10=456 / p50=1324 / p90=2516`，信息量 `p10=34 / p50=58 / p90=74`，图数 `p50=1 / max=5`。**无图页只有 5 个**，且都合法：`00-index/resources-index.md`、`00-index/tags.md`、`14-templates/` 的两张模板本身、`99-about/license.md`。**prose<700 的 19 页**里 11 页是 `13-resources/` 的条目卡（短点评 + 提示卡 + 一手外链就是它的形态），其余是指南页与模板。→ 本轮这条轴量不到可修缺陷，也就没有为凑字数注水。
  - 这条腿一开始量错过一次，值得记：探针第一版只把 `![]()` 当图，报「136 页无图」，与全站房规直接冲突。冲突的是尺子不是内容——改成 Mermaid 块也算一张图之后才是 5 页。**先证明尺子能给出可能的读数，再拿读数去判内容。**
- **`transform` 盲区值不值得单开一轮**：实测全站带 `transform` 的 SVG 文本标签只有 **2 处**，而且都是旋转不是缩放。`check_svg_legibility.py` 忽略 `scale(k)` 那条老账在真图上是零暴露面，不值得为它写判据，继续挂在 carried 里。

## 2026-09-24（第 69 次）新轴：动画**相位**里的可读性——静态帧量不到的那一类（字在某几帧是白底白字、被面板埋住），14 张动画图 496 标签 × 438 相位全扫；接入 WCAG 1.4.3 大小字分档后小字档越线 66 个 → **0 个**

本轮动正文 0 页、手绘 SVG 12 张（墨色 16 处 + 底板 14 处，全部断言式改写），新增判据 1 个文件 `tools/checks/check_svg_phase_legibility.py`，另外修掉一条判据的真 harness bug（`check_svg_fit.py`）。

### 一、这条轴抓的是什么事

此前每一根 SVG 轴都只看**一瞬间**：字号轴拿作者写的 px 比读者那一列，几何轴在冻结帧里量标签框。可 32 张图里有 14 张在动（100 个 `<animate>` 节点），而动画有静态帧根本显示不出的看不见法子：

- 一根在长的条（`values="0;300;300"`）在白条底下的白字——**条没到位之前那行字是白压白**；
- 一块淡入的遮罩矩形压在标签上——标签有半个周期被埋着；
- 一块面板自己的 `opacity` / `fill-opacity` 在动——读者的底色是晚到的。

「把相位冻住」这件事是**量出来的**，不是假设的（`.tmp-projects/r69_smil_driver.py`）：`pauseAnimations()` + `setCurrentTime(t)` 用 `setTimeout` 步进、**并且必须带 `--virtual-time-budget`**，才能正好落在作者写的坡道上（一条 0→100 / 2s 的条在 t=1.0 读 50、t=1.9 读 95）。没有这个 flag 整页一条 beacon 都不回；用 `requestAnimationFrame` 步进的话，25 相位的扫描只跑到第 1 帧。

判决算的是**读者真拿到的那个堆栈**，自底向上合成：页面的白，然后标签之下每个绘制面（各自 alpha 再乘上祖先 `opacity`——半透明面板是一层真实的部分覆盖，所以要合成而不是跳过），最后墨色盖上去，按 WCAG 相对亮度算对比度。渐变按 `<stop>` 定价、图案按 tile 定价，取**离墨色亮度最远**的那一端，也就是给标签最有利的一次读数：这样 DARK 判决永远不可能是服务器画法的锅，这类行记为 `approx`。代价写在「诚实边界」里。引用悬空（id 不存在）的面板是**未定价**且必须计数——一个量不了的板不许被读成通过。

埋没是**两臂**测试，两条阈值都是在这棵树上量出来的而不是挑的：`--buried`（一个标签 6 个探针点里同一相位被藏住的占比）与 `--steady`（一个点在整个周期保持被藏的占比）。用播放头扫过一个被裁切的标签，6 点里藏 2 点、39 相位里只中 1 相位；一个旅行的数据包 6 点里藏 1 点、35 相位里中 6 个——这俩是编排，不是缺陷。而 `04-react-loop` 的中心圆盘在 **25/25 个可探测相位**都咬掉一个徽章字形——那是真的 z 序缺陷。**单用任何一臂都会把这两类判错其中一类。** `COVERED` 报的是标签**上面**那层板，不是下面那层。

标签自己在淡入的时候不作对比度判决：它的 alpha 低于 `--presence`（默认 0.60）的相位一律豁免并计数，这样「它正在淡入」和「它根本看不见」还分得开。因为每一帧都采样，判决能说清缺陷是不是相位专属：`PHASE-ONLY`（最好的一帧过线、最差的一帧不过——静态帧那几根轴完全看不见它）或 `DARK`（稳态越线，作为**顺带抓到**报出来，因为没有任何旧轴量过颜色）。

### 二、读数是怎么走的

先以门槛 3.00 扫（`--json` 落盘，控制台 CJK 会糊，数字仍可读）：

| 趟次 | 越线图 | 越线标签 / 总标签 |
| --- | --- | --- |
| 轮初第一遍（bar 3.00） | 9 | **45**（3 相位专属 / 39 稳态 / 3 埋没） |
| 美术批 A 后 | 8 | 43 |
| 美术批 B 后 | 5 | 21 |
| 尺子改掉图案 tile 定价后（批 C） | 0 | **0** |
| 同一份清零图上门槛灵敏度 | — | 3.00→0，3.50→**8**，4.50→**66** |
| 换成分档尺子（小字 4.5 / 大字 3.0） | 12 | 66（6 相位专属 / 60 稳态） |
| D1 只改墨色（16 处 / 12 个文件） | 6 | 22（4 / 18） |
| D2 改底板（14 处 / 6 个文件） | 0 | **0**（未定价 0、覆盖缺口 0） |

分母是 14 张动画图、496 个标签、438 个相位总扫描。清零之后的门槛灵敏度那一行是这条轴的**反证腿**：读数 0 不是因为尺子不设门槛。

### 三、尺子自己改了两处，每处都种了反例

1. **图案 tile 按自身 `opacity` 折算**。房风格的发丝网格是 0.7px 线 @ 0.22–0.5；按全强度定价等于宣称 `06-memory-tiers` 里每一个标签都坐在一块不透光的石板板上——**5 个假 DARK**。不加这条它永远绿不了；加了之后必须还有反例钉住它不许松，所以种了一张不透明图案 `PLANT_TILE`（必须响）。
2. **WCAG 1.4.3 的大小字分档**。`SCALE = svg.getBoundingClientRect().width / viewBox 宽`（960 画布在 768 列里是 0.8，`16-batching` 的 920 画布是 0.8375），落地 px = 计算字号 × 缩率；≥24px，或 ≥18.66px 且字重 ≥700，门槛 3.0，否则 4.5。**这一条改动把轴从 43 个判决变成 43 + 66**——不分档就是拿错门槛做判决。四张档位幽灵图各钉一头（16px→4.5 必须响、24px→3.0 必须静、20px 粗体→3.0 必须静、800px 画布缩到 400 宿主里的 30px = 落地 15px→4.5 必须响）。

另外两处诚实性守卫：时间尺推不动的图（`begin="indefinite"`）必须报**尺子瞎了**（RULER BLIND），绝不报干净；`--selftest` 现在给 16 张种植图打分，全部判对（本轮日志 `r69_selftest_d2.log`）。每图还有一条活体检查：第一个 `<animate>` 下的节点在周期三个不同点读数必须不同，否则那张图是**覆盖缺口**而不是通过。`MIN_FIGURES=10` 是空转地板——子集跑（`--assets`）不许声称全站干净。

顺带修掉一条**真 bug**，而且它长得像内容失败：`check_svg_fit.py` 在 Windows 上跑到第 12/32 张就死在 `PermissionError [WinError 32]`——Edge 进程已经退出，但还在 `--user-data-dir` 里留着一个 WebView2 日志句柄，临时目录删不掉，于是整趟没有判决。丢一个临时目录很便宜，丢一趟判决不是：改成 `ignore_cleanup_errors=True` 并写明原因，重跑 32 张 / 1063 标签 fatal=0。

### 四、`--presence` 当过旋钮试，最后留在 0.60

两条 α 脉冲标签（`16-sandbox-layers` 的 ✕、`17-action-chunking` 的「丢弃剩余动作 → 立刻重推」）在 0.60 豁免线上最好也只能读到 3.55，因为它们发来的墨色是 red-900 `#7f1d1d`。把豁免线抬到 0.75 能让它们"过"，但那是拿尺子换绿灯：**它会把将来落在 0.60–0.75 之间的每一个淡入标签悄悄免掉**。正解是改墨色——red-950 `#450a0a`，实测在门槛没动的前提下升到 **4.56 / 4.78**。薄边还是要说清：这两行是**踩在 0.60 那条线上**取到的读数，不是富余读数。

### 五、美术改的是什么，以及两个方向的取舍

规则在这一轮落成了文字：**带字的底板必须坐在该色相的 -700/-800 档**（房风格兄弟色是 indigo-700 `#4338ca`、cyan-700 `#0e7490`）。白字要板亮度 ≤0.1833 才有 4.5:1，而浅色 tint 墨（`#e0f2fe` / `#fff7ed` / `#d1fae5`）比这更紧（≤ ~0.155–0.165）。

- D2（改板）之后：`03` 输出 3.77→**7.68**、10%≈20k 3.32→**6.78**；`04` 三张卡的中英标签 3.00–4.10 → **5.48–7.68**、序号 1/3 → 5.93/5.48；`08` 主管与中心带 3.56→**7.31**；`16-batching` 两处 4.00/3.60 → **5.78/5.60**。
- `16-continuous-batching` 那两处走的是**相反方向**：底从 `#3b82f6`/`#8b5cf6` 改成浅蓝浅紫（`#60a5fa`/`#a78bfa`），白字改成深色墨压在浅底上——不是每个修复都往深处走，因为第 67 轮记的那句「白字先于底色出现」本质是**墨与板同向**的问题。
- 取舍要留名：`04` 的琥珀胶囊现在读起来偏棕，`08` 更赤陶。为了可读性接受这两处，图本身也逐张看过（见下节）。

### 六、回归与目检

- **相位轴自身**：清零 + 16/16 种植判对 + 每图活体检查 + 空转地板；`unpriced=0`、`coverage=0`，且 PRESENCE / BURIED / STEADY 三条阈值一条都没放松。
- **七条回归轴全绿**：结构轴 198 页 0 问题；fit 轴 32 张 / 1063 标签 fatal=0（teardown 修好后才跑通）；字号轴 0 of 1109 低于 12px；label-parity 轴 12 张审计 0 删字；sanitizer 轴干净；跨页重复轴 dup=0（近重带 3 条是 advisory）；统计轴各口径对平（196 页 / 实量 196）。
- **真渲染目检**：8 张相位截图（`03`、`04`、`08`、`16-batching`、`16-sandbox` 两个相位、`17-action-chunking` 两个相位）逐张看，最差相位也过眼。

### 七、线上复核：读者那一份字节确实带着本轮的新配色

推送后量三件事（新判据落库 `tools/checks/check_svg_served_colours.py`；目检腿 `.tmp-projects/r69_live_pages.py`、`r69_live_paint.py`）：

- **12 张改动图的色值多重集，服务端副本与 authored 逐字相等**（`reached 12 of 12, mismatched 0`，最多的一张 123 个色值字面量）。为什么还要新落一条腿：sanitizer 轴比的是**元素与属性多重集**，`fill` 从 `#0284c7` 变成 `#0369a1` 对它完全隐形——属性还在，值换了。第 64–68 轮能量够，因为那几轮动的是几何；这一轮一次动 30 处颜色，必须有一条**给颜色定价**的腿。判据是**相等**而不是"新色出现了"：只比出现与否，会把"新版只是少用了几次某色"读成通过。反证腿：**把改动前的那份画法拿去和同一份服务端字节比，立刻 DIFFERS**（轴默认取首张扫描资产，`03` 读短 14 / 多 14；`04` 是短 19 / 多 19），所以这个绿说的是"读者拿到了第 69 轮"，不是"页面上恰好也有点蓝"；控制腿还会先断言**上一版与本版必须不同**，否则"立刻 DIFFERS"是句空话。覆盖与判决分桶（`--min-reached 10`）：没抓到的资产不算通过，样本没够着就不许声称全站干净。**比对的基线不再写死 `HEAD~1`**：本轮的改动一旦提交、上面又压了一条收尾提交，`HEAD~1` 就变成"什么都没改"，那条腿会静悄悄地量不到任何东西。现在的判据是工作区脏就比 `HEAD`、干净就比**最近一次动过资产的提交**的父本；两个分支都实测过（脏分支现场改一处色值后基线确实变成 `HEAD`、样本只有那一张，收尾复跑则落到 `af4516e^` 并列出 12 张）。顺带一个坑：探针第一次写的替换色 `#0e7490` 在第 69 轮已经从那幅图退役了，写入等于没写，于是"基线还是 `HEAD~1`"看起来像分支坏了——**先断言要替换的字面量确实存在**，才分得清是工具不对还是探针自己空转。
- **更新日志页线上已发出**：解析出的地址（从发布标题查，不猜）读到的标题序列**顶格就是第 69 次**，第 68 次紧随其后。
- **真渲染目检**：`08` 与 `16` 两张整页 1280px 截图（`08` 的赤陶主管盘与中心带、`16` 的浅蓝请求条 + 深墨标签都在线上到位），另把 `04` 的**服务端副本**内联进 768px 宿主真排版一张——三张卡的白字（「还缺什么？要不要调工具」「生成并发起 一次工具调用」「真实世界 返回的结果」）在线上清晰。

这一腿也量到两件工具边界，记下来免得下轮重踩：**headless Edge 带 `--virtual-time-budget` 直取 `react` 整页会挂死**（无限 SMIL 时钟让虚拟时间永不 settle；同批的 `08`/`16` 两页正常出图），而**浏览器 MCP 这边 `innerWidth/innerHeight` 读到 0×0**，页面里的 `<img>` 于是排成 12×9——那条腿能读 `naturalWidth`（`04` 报 960×700，正是 authored viewBox），但**不能用来做宽度判决**。

### 八、留下了什么（未做，按可实测性排序）

1. **相位轴只覆盖 14 张动画图**。另外 18 张没有相位可扫，所以这不是漏扫；但「静态图上的颜色」目前只被这条轴的 DARK 顺带管着，没有独立的静态颜色轴。
2. **渐变底板的定价偏乐观**：一条渐变板通过这里，不等于它自己最亮那个 stop 也过门槛。这个偏置只能**漏判**、不会**误判**，但它确实是漏判的口子。
3. `[on ...]` 报的是扫描时最后检查的那层板，**不一定**是最差相位之下的那层。
4. 两条 α 脉冲行只在 presence 边缘过（4.56 / 4.78）。
5. `--shots` 的相位截图按虚拟时间推算，是近似值——它给肉眼用，不做判决。
6. 上一轮未做项原样保留：13 张只过了尺子没过肉眼；字号轴仍不看 `transform="scale(k)"`；`STRIKE` 看不见「字压在别人的卡上」；`check_table_overflow.py --pages all` 与移动宽度读数；**宽版布局开关还没落地**（`<main>` 实测仍 768），它一开这条轴的 `COLUMN=768` 也要跟着重读；读者侧浏览器腿还没落库；`10` 的「长文问答·跌」措辞可读性轴。

## 2026-09-24（第 68 次）字号轴批 4·收口：最后 3 张高密度 UI 示意图整张重画，全站越线标签 3 张 / 214 个 → **0 张 / 0 个**，并为此落库一条「重画不许删字」的判据

本轮动正文 0 页、手绘 SVG 3 张，新增判据 1 个文件 `tools/checks/check_svg_label_parity.py`。

### 一、读数是怎么走的

| 趟次 | 越线图 | 越线标签 / 总标签 |
| --- | --- | --- |
| 轮初（第 67 次收口） | 3 | 214 / 1096 |
| 重画 `11-observability-ui` | 2 | 138 |
| 本轮收口 | **0** | **0 / 1109** |

分母 1096 → 1109 是重排**加出来**的 13 个标签：05 的连接状态条拆成两行、左侧服务器列表补了一枚「共 4 个」计数、10 的「回归用例数」把括号限定语单独成行。**没有为凑绿灯删掉一个字**，而且这一次「没删」不再是自我声明，是一条能读数的轴（见第三节）。

### 二、这三张为什么只能整张重画

它们原来是 960×560：缩率 0.8，要把 12px 门槛抬回线上，最小字号得写到 15px，而面板里的行高列宽是按 12px 排的——**抬字号等于撞框**。第 67 轮的其余 21 张靠「抬字号＋长画布＋拆行」就够，这三张不够，所以换了第四个自由度：**把画布宽度直接改成读者那一列的 768px**。缩率于是正好 1.0，作者写几个像素读者就看见几个像素，高度想长多长都免费（724 / 724 / 674）。代价是每张的几何全部重排：`05-mcp-inspector-ui` 55 个标签、`10-eval-console-ui` 69 个、`11-observability-ui` 65 个，逐个重定坐标。全站画布集合现在是 768 / 920 / 960 / 980 / 1280。

两处「一行真装不下」的解法值得记下来，因为它们**不能被字号轴看出来**：

- `05` 底部状态条三句话按 12.5px 量需 ≈729px，可用只有 666px。我第一次的改法是把「最近调用 42 ms」删了——**新轴当场报出来**，改判成两行状态条（横条 598..652），四件事全留。
- `11` 搜索框占位语被压短，丢了 "trace" 和「搜索」两个词。解法不是缩字，是**把搜索框搬进窗口标题栏**再重排筛选器胶囊——位置也是自由度。

### 三、新判据：重画不许删字（`tools/checks/check_svg_label_parity.py`）

「一字未删」这句话以前只能靠作者自觉。它把判据对准**内容字形多重集**：先把标签里的嵌套标签、实体、分隔符（`·/—→（）:，。、|+×` 等）和空白全部剥掉，再要求 `旧字形集合 − 新字形集合 = ∅`。为什么用字形集而不是标签集合：重画合法地把长标签拆成多行（JSON 逐行缩进、两行状态条），逐标签比对会把这类改动读成删除。拆行、换标点都不放过字形，**改名却会**，所以改名没有免费通道：必须写进 `REWRITES` 并给理由，且新词必须真的在图上，判据每用一次就打印一次——不然「我这里不得不改个说法」就成了让重画悄悄瘦页的逃生门。

控制腿（每种都必须被抓住，另有一腿证明尺子不会永远绿）：整句删掉、标签缩字、**未声明的改名**、丢一个拉丁词，四种坏写法各自报；同一份标签自比必须读 0；声明过的改写必须读干净。本轮唯一一次改写是 `侧板 → 底部检查器`——那块面板从右栏搬到了底部抽屉，留着「侧板」就对读者说了假话，所以它是**该改**且**必须留痕**。

这条轴在自己身上也抓到东西，而且抓到两次：

- **抓到自己一个真 bug**：`re.escape` 作用在含 `"\\s"` 的字符类上，会让判据把**字母 `s` 当成空白剥掉**——输出里出现「pan 树」「decription」，而 `deleted-glyphs` 里全是空格。这会让任何丢 `s` 的删字隐身。改成剥完分隔符再单独跑一次 `\s`，并加了一条显式断言 `norm("span 树 · 1（秒）") == "span树1秒"` 把它钉住。
- **抓到三页文案的标点失真**：`05` 底注原本以「。」收句，被我换成「——」；恢复原句并在后面补新句。

读数：`figures audited=3  figures that deleted content=0`（`05` 42→55 标签、`10` 67→69、`11` 65→65）。

### 四、回归与目检

- **几何轴全树**（`check_svg_fit.py`，浏览器量真墨迹）：`figures with a fatal problem=0 of 32  total=0  clearance notes=1`，三张新图 `problems=0`；种植的 4 处缺陷各自被抓住、干净修法读 0。
- **字号轴**：`figures with a sub-bar label=0  labels=0 of 1109  pages touched=32`，三条常驻控制（分类器三种脏字号、几何尺子 0.4/0.8/1.0、内在尺寸两腿）与线上腿全过。
- **结构轴 198 页 0 问题**；统计三腿对平（196 页 / 19 章 / 217 Mermaid / 32 SVG / 8 截图 / 257 图 / 108 公式，README、首页、封面横幅一致）。
- **真渲染目检**：三张各出一张 768px 本宿主页截图逐张看，无压字、无溢出、连线不刺字。

### 五、留下了什么（未做，按可实测性排序）

1. **13 张图只过了尺子没过肉眼**（第 67 轮批 2/3 的其余部分）：判据说干净不等于好看，这条差下一次目检。
2. **动画相位可见性轴还不存在**：`16-continuous-batching` 两处白字在动画相位里会先于底色出现（第 67 轮记的），字号与几何轴都量不到「哪一帧字看不见」。
3. **字号轴不看 `transform` 缩放**：现在的算法读 `viewBox` 缩率，若作者给某个 `<g>` 加 `transform="scale(k)"`，作者写的 px ≠ 落地的 px。全站目前无人这么写，所以是盲区而非缺陷。
4. **宽版布局开关还没开**（操作者说「我这就去开」，但 `<main>` 实测仍 768）：落地后 `--column 1152` 的 what-if 读数要重跑，本轮的 768 画布决策在新列宽下会变成「不缩小但仍有富余」。
5. `STRIKE` 看不见「字压在别人的卡上」这种非描边交叉；`check_table_overflow.py --pages all` 与移动宽度读数仍未做。
6. **第六节那条读者侧浏览器腿还没落库**：它现在是一次性探针（`.tmp-projects/r68_live_check.py`，页名写死三张）。要常驻得补 selftest（种一张线上仍是旧画布的假页面、一条没 `max-width:100%` 的假 `<img>`）并接进 `tools/checks/`，否则下一轮重排又要重写一遍——第 57 轮就记过「README 引用的判据不在仓库里」这一类账。

### 六、线上复核：读者拿到的那一份字节，量出来同样是 1.000

推送后对三张改动页各做一次**读者侧**量测（`.tmp-projects/r68_live_check.py`）。它量的不是「本地页面在浏览器里长什么样」，而是**线上代理地址返回的 SVG 本身**：从 `llms.txt` 解析页面 URL（不猜），取页面上那条 `<img>` 的 `~gitbook/image` 地址，把服务端副本内联进一个 768px 的宿主让真 Chromium 排版。为什么不让浏览器直接跑线上页的副本：第 64 轮就量过，GitBook 页的副本在 localhost 不会 hydrate（客户端路由没有这个文件名），`<main>` 根本不排版——那是量具的边界，不是页面的缺陷。

- **先证明这把尺子能说不**：`HEAD~1` 的 `05` 画布是 960×560，与今天的 768×724 不等，所以「线上还是上一版构建」这条判断**装得上去就一定响**。三页读到的服务端 viewBox 分别是 `(768,724)`、`(768,674)`、`(768,724)`，**与 authored 完全相等** → 读者拿到的确实是本轮重排后的画布。
- **平台自己报出的绘制宽度**：三页的代理地址都带顶层 `width=768`，正好等于 `min(768 列宽, 768 画布)`——绘制宽度由平台声明，不再靠推断。
- **真排版读数**：`painted 768x724 / 768x674 / 768x724`，**缩率 1.000**，宽高比与服务端 viewBox 一致到 0.002。这一条把本轮的核心主张（作者写几个像素，读者就看见几个像素）从仓库里的算术换成了**读者字节上的实测**。
- **三张 768px 截图逐张目检**：无压字、无越框；`05` 的两行状态条在线上确实带着「最近调用 42 ms」——就是第一次改法悄悄删掉的那句；`11` 的搜索框在标题栏里读完整占位语「按 trace id / 会话 / 关键词搜索」。

这条腿自己也是修过两轮才绿的，两次都是量具的错，都记下来：

- 手写 `urllib.parse.unquote(src)` 去解代理地址，CDN 直接 **400 Bad Request**：GitBook 的 `src` 是**实体编码 + 内层 url 参数双重百分号编码**，可请求的形式只能 `html.unescape`，把 `%252F` 解成 `%2F` 就破坏了代理自己的签名。仓库里的 `check_live_images.content_imgs` **早就知道这件事**（它的 selftest 把这个实体 bug 钉成 hit control），所以正解是**复用已落库的轴**，不是再实现一遍解码。
- 探针回传的 JSON 少了信箱用来配对的 `id` 字段，于是三页全部读成「browser leg read nothing — coverage gap, not a pass」并 `exit 1`。这条腿**把自己的空样本报成失败而不是绿**，是它该有的行为；补上 `id` 后三页齐。
- 顺带一条假警报：第一版在**原始 `<img>` 标签**上找 `width=`，而线上写的是 `&amp;width=768`，读不到就打印「declares no width= param」。判据读的是可请求形式，改完三页都报出 768。

目检还抓到一件**任何尺子都量不到**的事：`10-eval-console-ui` 第四根柱的标签写「长文问答·跌」。它是 `HEAD~1` 就有的旧写法，不是本轮引入，字号与几何两条轴都判它干净，只有人眼看得出「·跌」像被截断的半句话。本轮不改（改措辞要动 `REWRITES` 并重新过三张图），记为**措辞可读性**这条轴的第一个样本。

## 2026-09-24（第 67 次）开工·字号轴批 2＋批 3：21 张手绘 SVG 逐张重排，全站越线标签 25 张 / 686 个 → 3 张 / 214 个（顺手补上「没声明内在尺寸」与「尺子读不到 `<style>`」两条轴）

本轮动正文 0 页、手绘 SVG 21 张，判据改 1 个文件 `tools/checks/check_svg_legibility.py`。

### 一、读数是怎么走的

| 趟次 | 越线图 | 越线标签 / 总标签 |
| --- | --- | --- |
| 轮初（第 66 次收口） | 25 | 686 |
| 批 2 前半 | 20 → 18 → 14 → 11 | 549 → 502 → 407 → 373 |
| 尺子修正（见第三节 2） | 10 | 358 / 1089 |
| 本轮收口 | **3** | **214 / 1096** |

分母从 1089 涨到 1096：重排把 7 处「一行装不下的长标签」拆成两行，标签**变多**而越线**变少**——没有为凑绿灯删掉一个字。`17-vla-loop`、`16-prefix-cache`、`18-model-harness-matrix` 三张是整张重画（原几何装不下 15px），文案逐条保留。

### 二、只有三个自由度，本轮分别用在哪

- **抬字号 + 长画布**：920 画布最小 15px、960 画布 15px、980 画布 16px（缩率 0.835 / 0.8 / 0.784，过线后分别读到 12.53 / 12.00 / 12.54px）。缩放只看宽度，所以高度免费。
- **拆行**：卡片文案超出可用宽就拆两行——`10-eval-landscape-2026` 的「partial vs strict / 必须分清」、`09-framework-map-ui` 六张范式卡全部拆两行、`05-tool-calling` 的循环提示卡。
- **换宽**：`09-framework-map-ui` 决策胶囊 236→256、卡片 300×60→290×80、画布 560→624；`00-learning-path` 四张 204→212 且正文左缩进 24→16；`16-continuous-batching` 整条泳道右移 40px，把右侧注记改成 `text-anchor="end"` 挂到轨道末端。

### 三、这轮真正修掉的是三条「图以外」的缺陷

1. **内在尺寸轴**（本轮新增判据）：`<img>` 加载的 SVG 若根节点没写 `width`/`height`，Chromium 报的 naturalWidth 是 300——轮初 **10/32 张没声明**，全部补齐。常驻断言两腿：`declared_size()` 必须与 `viewBox` 逐轴相等，另外种一棵「把 width/height 删掉」的幽灵图必须读成 `None`。
2. **尺子读不到 `<style>` 里的类字号**（第 66 轮记在「已知盲区」）：`19-lab-react-loop-animated.svg` 写 `.h{17px}/.s{15px}`，被 13px 兜底读成 15 个越线标签。本轮给 `text_sizes()` 补上真正的层叠（内联 `style` > `<style>` 类规则 > `font-size` 表现属性 > 继承），反例是一张同时含 9 / 15 / 17 / 20px 四种写法的幽灵图——必须只捉住两个 9px，selftest 从两棵变三棵。修完读数 11 张 / 373 → 10 张 / 358，**这张图一个字节都没改**：先验尺子，再下判决。
3. **判据差点被自己躲过去**：`16-continuous-batching` 右移后「持续满载」压在 slot 4 的条上（BURST 8px）。处方是画布 470→490 并把该节 GPU 行下移 20px，不是挪字。

### 四、验证

- 21 张全部过 `check_svg_fit.py`：全站 **32 张 fatal=0**（clearance notes 3→1）。
- 真渲染 768px 逐张目检 **8 张**（`17-vla-loop`、`16-prefix-cache`、`18-model-harness-matrix`、`16-continuous-batching`、`10-eval-landscape-2026`、`00-learning-path`、`05-tool-calling`、`09-framework-map-ui`）；其余 13 张本轮只过了判据、没过肉眼，记在第五节。
- 结构轴 198 页 0 问题；README / 首页 / 封面横幅三条统计腿全轴对平（`svg=32`、`figures=257`、`mermaid=217`、`math=108` 均未变）。

### 五、留下什么（不粉饰）

- 还剩 **3 张高密度 UI 示意图**：`05-mcp-inspector-ui` 75/77、`11-observability-ui` 76/77、`10-eval-console-ui` 63/67，共 214 个标签。它们不是「抬字号」能救的——整张是界面复刻，行高、列宽、面板尺寸要按 1.25× 一起长，等于重画三张 UI，批 3 单独一轮做。
- `16-continuous-batching` 里「decode 到 EOS」「新请求补位」两处白字压在动画条上：静态帧读 0，但条宽从 0 长起的相位里字会先于底色出现。**动画时序可见性**这条轴还没有。
- 13 张改动图缺肉眼目检；等宽版布局开关仍未落地（`<main>` 实测还是 768），落地后字号轴、fit 轴、Mermaid 几何轴都要用 `--column 1152` 复跑。

### 六、线上复核（提交 `5fb438c` 并推送之后）——这一节里修的是判据自己的一个缺陷

同步门两腿都读到第 67 次（`.md` 156,646 字节 / HTML 11,690,328 字节）。随后 `check_svg_sanitizer.py` 的线上腿**连续三次跑不完**：三次都在扫描第 30 个资产附近被 CDN 掐断连接（`WinError 10054`），三个不同的资产各死一次。先量仪器再定罪：把死掉那条 URL 单独抓一次，**第一次就返回 5,234 字节 `image/svg+xml`**，`dpr=1`／`width=384` 变体同样正常——所以既不是这张图也不是这个 URL，是我们自己的请求速率。

判据原来的行为有两个真缺陷：① 整条腿 `raise` 出去，扫描到此为止；② 「比过 30 张、还有 5 张没够着」与「35 张全干净」在输出里长得一样（只有 `checked>=25` 这道地板，而 30>25 照样过关）。这正是第 60 轮记过的规矩要防的事——**没抓到的页面什么都没证明，不能读成绿**。改法：

- 扫描节流 0.8s／资产，失败后先冷却 15s 重试一次（`served_copy_cooled`），`wl.fetch` 的退避从 4 次改成累计 5 次；
- **两桶分开**：内容桶（`stripped` / `dropped` / 新增 `mismatched`）与覆盖桶（`fetch-failures`），**任一非空都 `exit 1`**，覆盖桶单独打印「这不是内容发现，重跑，别读成绿」；
- 顺带把「served viewBox ≠ authored」从 `assert`（一响就掐断整趟）改成记账，一次运行能看完全部 32 张；
- 两条控制：`coverage_selftest` 拿合成读数钉住桶的边界（35/35 绿、**30/35＋5 次失败必须红**、空样本红、`--only` 不被全树地板误伤）；`.tmp-projects/r67b_bucket_test.py` 用真循环演一遍——把两张图的传输层换成「必失败」，两张都进覆盖桶、内容桶保持 0、判决读红；再演「两张里死一张」，那张成功的正常比完，判决仍读红。

复跑读数：`served copies compared=32 of 32  fetch-failures=0`、判决 clean；线上图片轴 `pages=36 refs=45 唯一资产=40（32 SVG + 8 PNG）problems=0`；**线上侧 fit 判决**（把读者拿到的字节喂给第 66 轮那把尺子）8 张重排图 `problems=0`，且 served viewBox 就是本轮新画布（`09` 960×624、`00` 960×556、`10-eval-landscape` 920×404）——这条同时排掉「线上还是上一版构建」。目检 3 张**线上 served 副本**在 768 列里的真渲染截图（`09-framework-map-ui`、`00-learning-path`、`05-tool-calling`），标签清晰、无压线无越框。`check_live_column.py` 复跑：vw=1024/1280 两档 `<main>` 仍是 768，等宽版开关依旧没生效。

## 2026-09-23（第 66 次）开工·把「浏览器量出来的」SVG 标签几何轴落库：真实墨迹盒 vs 它自己的容器 / 邻居 / 画布 / 连接线，全站 32 张 8 个致命问题 → 0（先写的估字宽探针被自己的控制判死，整支丢掉）

本轮动正文 0 页、手绘 SVG 5 张（`08-multi-agent`、`16-sandbox-layers`、`19-lab-react-loop-animated` 是第 65 轮批 1 的余量；`06-rag-pipeline`、`17-vla-loop` 只改连线走向与标签落点，**一个字都没删**），判据新增 1 个文件 `tools/checks/check_svg_fit.py`。

### 一、这条轴量的是第 64/65 轮那把尺子看不见的东西

字号轴只回答「字到读者眼里多大」，答不了「字有没有装进它自己的框、有没有压在邻居上、有没有被连接线碾过」。

第一版探针（`.tmp-projects/r66_fit_probe.py`）按字符类别估字宽：在当前树上量出 **563 个「撞字」**，而其中一张 UI 示意图肉眼渲染干干净净——它既不认祖先 `transform`，也不认 `text-anchor`。按「先验尺子、再下判决」的规矩它被判死刑，只留作反面注脚。判决全部换成浏览器实测：`getBBox()` 取真实墨迹盒，`getScreenCTM()` 映回这张图自己的 viewBox 单位，所以读数就是作者单位、缩放自动抵消；线段用 `getPointAtLength()` 沿真实长度采样。全站基线：**32 张 / 1011 个标签 → 8 个致命问题 / 4 张**。

### 二、四类判决，本轮抓到的 8 处全是第四类

| 判决 | 判据（单位＝作者 px，PAD=2 的余量先扣掉） | 本轮 |
| --- | --- | --- |
| BURST | 标签边缘超出所属容器 > 2px | 0 |
| COLLIDE | 不同字符串墨迹盒 x 向重叠 > 2px 且 y 向压过矮者的 45% | 0 |
| OFFCANVAS | 标签出画布 | 0 |
| STRIKE | 连接线穿过墨迹盒（两侧各深入 > 2px） | **8** |

STRIKE 这一类以前不在任何尺子上：

1. **`17-vla-loop` 3 处**：快系统→动作块缓冲的贝塞尔从「安全层」标题上碾过；伺服→物理世界的反馈大弧横穿整排卡片、压住「动作块缓冲（滚动重规划）」；缓冲图例那行 11px 小字直接印在「伺服 / WBC」卡上。修法：走线改穿 542↔566 那道 24px 柱间沟；反馈弧改走卡片下方 y=216 的空带、从底部合回物理世界（闭环语义反而更对了）；图例移到缓冲卡正上方，riser 让位。
2. **`16-sandbox-layers` 2 处**：左侧回流管线 x=50 的竖段穿过「隔离层（按威胁模型选档）」标题——标题挪到 x=100、整条带下移 8px、回流横段上抬到 y=176；出口闸门那个 ✕ 本来就压在它拦停的车道上，**这是意图不是缺陷**，用源码注释 `<!-- fit:strike-ok ✕ -->` 显式声明——注释必须点名字符串，不允许整图豁免。（这条豁免写在注释里而**第 65 轮已量过 GitBook 会剥注释**：所以它只在作者侧生效，读者那份图里什么都没有，这正是它该待的位置——判据读的是仓库里 authored 的那份。）
3. **`06-rag-pipeline` 1 处**：虚线回流在 x=723 的下探段穿过「检索 Top-K 候选（如 50）」尾部，标签左移到 x=505。
4. **`05-mcp-architecture` 2 处：假阳性，改的是尺子不是图。** 两个传输标签本来就写在白底胶囊 `<rect>` 里，胶囊画在连线之后、文字之前，读者根本看不见那根线。判据因此加一条**漆序**规则：不透明矩形若 `idx(线) < idx(板) < idx(字)` 且盖住交点即豁免；`plant-strike` 没有胶囊，照旧必须被抓（常驻控制）。

### 三、控制：这条轴既能红，也能绿

* 4 颗种雷：BURST / COLLIDE / OFFCANVAS / STRIKE 各种一颗，各自必须被自己那一类捉住（脏图允许顺带触发第二类，例如出画布的标签必然也超出全画布背景框）。
* 1 颗种干净：本轮真正用过的修法全挤进一张图——两行拆分、蛇形四格、白晕双层标签压在曲线上、胶囊标签压线、✕ 停在自己车道上——**必须 0 命中**。真实树里 32/32 张在字号轴上全都不干净，没有这张干净图，「见谁都报缺陷」和「量到缺陷」输出长得一样。
* 空转下限：整树扫必须 ≥25 张、≥400 个标签（点名抽查不启用），任何一张测不出来直接 `exit 2`，绝不当「跳过」。
* 容器归属：标签左边缘要真落在框内（±3px）才算这个框的字。`12-coding-agent-loop` 的「⑤ 全绿？」正好贴在工作区卡右边缘，±1 容差给它凭空造出 56px「撑破」。

### 四、前后读数

* 新轴：`32 figures / 1011 labels / problems 8 → 0`，`exit 0`；另有 3 条 clearance（贴边但不越界）只报不红。
* 第 64/65 轮那把字号轴同树复跑（`--no-live`）：**27 张 / 735 个 → 25 张 / 686 个**（分母 1057 → 1059）。本轮清掉的是 `08-multi-agent` 的 27 个和 `19-lab-react-loop-animated` 的 22 个：08 把 10~14px 全钳到 15px、带说明拆成两行；19 把 `<style>` 里的类字号抬到 17/15px，画布 340 → 400，四格改成 2×2 蛇形。
* 顺手记一条**口径盲区**：`check_svg_legibility.py` 只遍历属性、不读 `<style>`，所以看不见 CSS 类里的字号；`19-lab-react-loop-animated` 是 32 张里唯一用类样式的，它那 22 个小标签是靠浏览器实测才被数的。盲区记在案、**没顺手改**（改完要重跑全站基线，属另一轮）。
* 结构校验：`pages scanned=198 problems=0`。目检：5 张改过的图全部在 768 盒里真渲染过（08 / 19 / 16 / 17 / 06）。

### 五、留下什么

1. 字号轴还剩 **25 张 / 686 个** 标签在 12px 以下，批 2 从 `11-trace-waterfall`、`12-coding-agent-loop`、`16-prefix-cache`（8.62~8.80px）起。
2. STRIKE 只认描边，**不认「字印在另一张卡上」**：`17-vla-loop` 那行图例原本压在伺服卡上，是目检抓的，不是轴抓的。把「文本盒 vs 非容器矩形」变成判决是下一条待立轴。
3. 采样步长 2px：一根斜线若恰好没有采样点落进内缩 2px 的字盒会漏报；本轮 8 处没有一处靠运气。
4. 宽版布局仍未生效（`<main>` 实测还是 768），落地后要重跑 `check_svg_fit.py --column 1152`。
5. 未做：`check_table_overflow.py --pages all`、移动端宽度读数、图注两级合并、线上正文完整性轴、`check_svg_sanitizer.py` 三张被剥特性表合并。

### 六、线上复核（提交 `85a26c8` 并推送之后）

* 发布门此刻读**未上线**：`.md` 腿已经是第 66 次（152,897 字节 / 84 轮），而读者可见的 HTML 腿还停在第 65 次——就是第 64 轮记下的那条行为（`.md` 先同步，判决取较差的那条腿）。**没有把它读成绿。**
* 图片资产走另一条管道，读者副本已经能取到。`.tmp-projects/r66_live_fit.py` 对 5 张图各跑三条腿：① **只存在于 HEAD 版本的几何标记**（`17` 的三段新走线＋新箭头 polygon、`16` 的 `x="100"` 标题与 `M500 170 V176 …` 回流段、`06` 的 `x="505"`）逐条命中；② 把 **fit 轴跑在读者字节上**：5/5 `problems=0`；③ viewBox / 最小字号 / 标签数与 HEAD 相等。旧副本不可能过①，所以这不是「抓到了图」而是「抓到了新版图」。
* 一次判据假警报值得记进工具箱：第一版脚本直接抓 llms 条目里的地址，那些地址带 `.md` 后缀，返回的是**原始 Markdown**、里面压根没有 `<img>`，于是 5 张图齐刷刷读成 `NOT-ON-PAGE`。剥掉后缀才有页面。（第 65 轮的 helper 早就剥了——抄作业要抄全。）
* 豁免的下游行为顺手量了一次（`.tmp-projects/r66_waiver_leg.py`）：读者副本里 `fit:strike-ok` 字样**不存在**（注释被剥，与第 65 轮的清单一致）；同一份读者字节**不带**豁免跑 fit 读 1 处 STRIKE（那个 ✕）、带作者侧豁免读 0。所以这条豁免是**承重的**，而且只能活在作者侧——判据读 authored 文件，读者拿到的图里没有它。
* 目检：5 张读者副本各自在 768 盒里真渲染过（`.tmp-projects/r66_live_*.png`）——`16` 的标题与回流线分开了、`06` 的 Top-K 说明离开了下探段、`17` 的图例回到缓冲卡上方、`19` 的药丸标签仍然盖住回线。这里也踩了一次自己的坑：读者副本带着 `width="960"`，塞进 768 的宿主会**溢出**而不是缩放（线上是 `<img style="max-width:100%">` 才缩的），第一遍截图右半边被切掉；补上 `svg{width:100%}` 才是读者看到的那张。

## 2026-09-23（第 65 次）开工·逐张重排手绘 SVG 的文字/画布比例：批 1 五张全部过线（223 个低于 12px 的标签清零），全站读数 32 张 / 956 个 → 27 张 / 735 个；线上抽查另抓到一条离线量不到的新轴——GitBook 的 sanitizer 会剥掉 `paint-order` 与 `attributeName="fill"`，5 个「描边当光晕」的标签在读者眼里被自己的描边糊掉、4 个「域随机化」格子对读者永远不换色（已修，判据落库 `check_svg_sanitizer.py`）

本轮动正文 0 页、手绘 SVG 7 张（首页封面 + 4 张正文图重排；`19-lab-react-loop-animated` 只改光晕写法；`17-sim2real-domain-randomization` 改动画写法 + 一个假换行），判据 3 个文件（`check_svg_legibility.py` 的账目段；新增 `check_svg_sanitizer.py`，它自己在本轮内被线上实测扩了两条规则）。第 64 轮把这条轴立起来之后，操作者定了三件事：**32 张分批逐张重排**、**更新日志页不拆（保持单页）**、**宽版布局去开**。本轮就是批 1；宽版那条复测过仍未生效（见五.3）。线上抽查又开出一条新轴，见六。

> 本节标题在本轮内被改过一次（`734 个` → `735 个`、补上第二条发现），因为批 1c 动了那张图的标签数。`check_changelog_headings.py` 在那次提交之前会如实报 `lost=1`——它比的是 HEAD 与工作树的条目标题，正文没丢，提交即消。这是第 59 轮那条守卫在按设计工作，不是误报。

### 一、修法只有两个自由度

等比缩放是中性变换（画布和字一起放大，比值不变，第 64 轮已证），所以每张图能动的只有：

1. **窄画布**：封面 `banner-home.svg` 从 1920×480 改成 **1280×540**，缩率 0.4 → **0.6**，配 22px 起的字 → 落纸 **13.20px**。
2. **抬字号 + 长画布**：4 张 960 画布的正文图把最小字号抬到 **15px**（0.8 缩率下正好 **12.00px**），装不下的部分**往高度里长**（540 → 680 / 700 / 700 / 776）。缩放只看宽度，所以「加高」是免费的，代价只是页面变长。

### 二、五张图的前后读数（同一把尺子，`HEAD` 版与工作树版各测一遍）

| 图 | 画布 前 → 后 | 缩率 | 低于 12px 的标签 前 → 后 | 最小有效字号 前 → 后 |
| --- | --- | --- | --- | --- |
| banner-home | 1920×480 → 1280×540 | 0.40 → 0.60 | 20/21 → **0/22** | 5.20 → **13.20px** |
| 03-context-budget | 960×540 → 960×700 | 0.80 | 64/65 → **0/62** | 7.60 → **12.00px** |
| 04-react-loop | 960×540 → 960×700 | 0.80 | 43/45 → **0/52** | 7.60 → **12.00px** |
| 05-mcp-architecture | 960×540 → 960×680 | 0.80 | 49/51 → **0/54** | 7.60 → **12.00px** |
| 07-plan-vs-react | 960×540 → 960×776 | 0.80 | 47/48 → **0/49** | 7.60 → **12.00px** |

全站：**32 张 / 956 个 → 27 张 / 734 个**（Δ 正好是这五张的 223 个；标签总数 1042 → 1056，其中 +5 是六.2 那处光晕改法把 1 个 `<text>` 拆成 2 个——底下一层 `fill="none"` 只画描边，看不见但照旧计入，不为绿灯开后门。六.5 之后这条读数变成 27 张 / 735 个）。`--column 1152` 的宽版 what-if 同步从 23 张 / 378 个降到 **18 张 / 204 个**。轴本身照旧退出码 1（还有 27 张没过），门槛没有往下挪一寸。

### 三、目检抓到的三处（每张都在 768 盒里真渲染过，不是纸上算的）

1. **`04-react-loop`**：右侧轨迹卡最后一格（Final Answer）**探出卡片下沿 14px**，且 ① 号徽标压住「final answer → 退出」胶囊的下边框。修法：两张侧卡加高到 452，Final Answer 格改成三行，胶囊整体上移。
2. **`05-mcp-architecture`**：原图 6 个原语小格只有 102px 宽，15px 的 `read_file · search` 一定撑框。改成 130px 格 × 三行（名称 / 释义 / 示例），示例内的分隔点去掉空格（`read_file·search`）；Server 卡从 352 加宽到 442，Host 卡收窄到 272，中间留出 190px 的传输标签走廊。
3. **`07-plan-vs-react`**：「一次性产出的 5 步计划（快照）」和泳道标题在同一行会撞字（挪到标题右侧同行）；步骤 4 的红色 ✗ 和「4 拉财报」压字（两行文字基线各下移 6px，✗ 留在格内上沿）；7 个 100px 小格装不下 15px 的「Observation 观察」，改成**两行四列的蛇形链**（4+4 格、每格 204px），回跳用一条带流动虚线的长弧从第一行末尾绕到第二行开头。

### 四、内容没删，但有三处措辞被压短（记清楚）

- `05`：Host 副标题从一行拆成两行（「AI 应用 / Agent 运行时」+「内嵌多个 MCP Client」）；传输胶囊「Streamable HTTP · 远程」去掉「· 远程」——同一张 Server 卡右上角的徽章本来就写着「远程服务」，信息不丢。
- `07`：步骤 4 / 5 的标题「拉财报数据 / 生成报告」压成「拉财报 / 出报告」以进 90px 的格；执行器说明从 4 行改成 5 行、多出一行「所以更省 token」。

### 五、harness 与平台读数

1. **无头 Edge 的 `--screenshot=<相对路径>` 会 rc=0 却不落盘**（图写进了 Edge 自己的 CWD）。渲染脚本现在一律先 `os.path.abspath` 再传，并且每次打印 `bytes=`：只判返回码会把「根本没截到图」当成「截到了」。
2. **改完 SVG 先跑一遍 XML 解析**：五张图 `ET.parse` 全过，`<text>` 节点数 22 / 62 / 52 / 54 / 49 与轴读到的标签数对平。手绘 SVG 没有 Markdown 结构校验兜着，塌了半句话不会有人红。
3. **宽版布局仍未生效**：本轮 `check_live_column.py` 复测 2 页 × 2 视口，`vw=994 → 768`、`vw=1250 → 768`，`column=[768] spread=0px problems=0`。所以批 1 全部按 768 列重排；开关真落地后这条轴要按 1152 复跑一次（那时 960 画布 1:1 落纸，15px 字变成 15px）。

### 六、线上抽查抓到一条离线量不到的新轴：平台会把 `paint-order` 和 `attributeName="fill"` 剥掉

批 1 的五张图推上去之后，按老规矩去线上核。资产字节先到（约 40 秒），`viewBox`、最小字号、`<text>` 数三项与 HEAD 全部对平（banner 1280×540/22px/22、03 960×700/15px/62、04 960×700/15px/52、05 960×680/15px/54、07 960×776/15px/49）。**但把线上拉回来的 SVG 直接塞进 768 盒渲染，字却糊了。**

1. **机制**：`04-react-loop` 环上三个标签、`07-plan-vs-react` 回跳弧上的一个标签，写的是 `fill="#075985" stroke="#f8fafc" stroke-width="3.5" paint-order="stroke"`——作者眼里是「字 + 淡色光晕」，因为 `paint-order` 让描边先画、字形盖在上面。GitBook 的 sanitizer 过一遍资产时会**重排属性、删注释、并且剥掉 `paint-order`**（线上副本里 `paint-order` 计数 3 → 0，其余属性都在）。属性一没，绘制顺序退回默认「fill 后 stroke」，3.5px 的淡色描边直接压在 15px 字形上，读者看到的是两处几乎不可读的浅灰残影。第 64 轮那把尺子量的是 authored 文件的字号与缩率，**这条缺陷它看不见**：字号确实 15px，只是不成人形。
2. **修法**：不用 `paint-order`，光晕改成**两层 text**——底层 `fill="none" stroke="#f8fafc" stroke-width="3.5" stroke-linejoin="round"`，上层只写 `fill`。全是普通表现属性，sanitizer 无从下手。`19-lab-react-loop-animated` 的 `.lbl` 同理拆成 `.lbl` + `.lblhalo` 两个类（CSS 里的 `paint-order` 一样会被剥）。文字内容一字未删。
3. **判据落库 `tools/checks/check_svg_sanitizer.py`**（两条腿）：
   - 离线腿（不联网，进日常门）：任何 authored 资产用到 `KNOWN_STRIPPED` 里的特性就红。`KNOWN_STRIPPED` 是从线上量出来的实测表，目前只有 `paint-order` 一条，附了「改成两层 text」的处方。
   - 线上腿：逐张取正文图在真页面上的 `~gitbook/image` 代理地址（`.gitbook/assets/*` 直接 404，读者拿到的从来不是原路径），拉回服务端副本，比对**元素与属性两个多重集**；`viewBox` 必须与 authored 相同，副本必须还能当 XML 解析。
   - 三条控制：判据 selftest 种一个带 `paint-order` 属性的标签和一个 CSS 写法，两者都必须被抓，两层 text 的干净写法必须 0 命中；线上腿的「干净」不能来自空样本，比对数 <25 直接断言失败；`viewBox` 断言保证「没有属性被剥」不是拿垃圾跟垃圾比。
   - 本轮读数：离线腿 authored 资产 35 张、依赖被剥特性 **1 → 0**（`19-lab` 修完）；线上腿在修之前如实报出 `04`/`07`/`19` 三张的 `text@paint-order` 丢失——也就是说这条轴先证明自己能红，再证明树是干净的。
4. **把线上腿跑完 32 张，又抓到第二条，而且性质相反**：`17-sim2real-domain-randomization.svg` 报「丢了 4 个 `animate@attributeName`、1 个元素」。拉回服务端副本逐字看：
   - 四个「域随机化」格子的动画写的是 `<animate attributeName="fill" values="#fde68a;#bfdbfe;#fde68a">`，线上到达时 `attributeName` 被删（`values`/`dur`/`repeatCount` 都还在）。没有 `attributeName` 的 `<animate>` 没有目标属性，于是**这张图的主题——同一张网格里每格按自己的周期换色——对读者永远不会发生**，格子焊死在起始色。同一张图里指向 `x` 与 `opacity` 的两个 animate 完好无损，全站另外 53 处 `opacity`、11 处 `width`、10 处 `stroke-dashoffset` 目标也全部存活：**被剥的不是 `attributeName` 这个属性，而是 `fill` 这一个取值**（全站 `attributeName="fill"` 一共 4 处，就是这 4 处）。
   - 那条「丢的元素」是 `<text>zero-shot 或<br/>少量真机微调</text>` 里的 `<br/>`。`<br>` 不是 SVG 元素：它在本地**从来没换出行**（真渲染截图里那一行字直接压进右侧「真实世界」方框），sanitizer 删掉节点后文字照样连成一行。所以这条不是「平台弄坏了作者的东西」，是**作者写了一个不存在的写法，平台顺手把它藏了起来**——两种账都得记，但处方不同：前者换成平台确实带的 `opacity` 目标，后者换成两个 `<text>`。
   - 修法（文字一字未删）：每格后面加一块同几何、`fill=目标色`、`opacity="0"` 的覆盖矩形，动画改成 `<animate attributeName="opacity" values="0;1;0">`，覆盖矩形排在格子的前景块**之前**，所以机器人和阴影照旧压在上面。`opacity` 是这条轴当场验证过能活着到读者的目标。
   - 断言不是靠眼睛：把四个覆盖矩形冻结成 `opacity="1"`、把扫光矩形冻结成 `opacity="0"`、删掉所有 `<animate>` 后渲染，再按像素采样——四格覆盖色分别读到 `#bfdbfe`/`#dcfce7`/`#fde68a`/`#f1f5f9`，四格前景块分别读到 `(14,165,233)`/`(249,115,22)`/`(225,29,72)`/`(168,85,247)`，**8/8 命中**。截图时刻用了 `--virtual-time-budget`，但扫光本身是时变的，所以「冻一帧再采样」比直接截动图可靠。
   - 判据跟着加两条离线规则（`STRIPPED_ANIMATE_TARGETS = {"fill"}`、`LINEBREAK_TAGS = {"br"}`）与两条常驻反例：种一个 `attributeName="fill"` 的 animate、种一个 `<br/>`，都必须被抓；`opacity` 覆盖矩形与两行 `<text>` 两种**修法写法**必须 0 命中（否则判据会把未来的自己一起锁死）。
   - **线上腿的全树读数（本轮收尾跑的，约 7 分钟、32 张全中）**：`authored assets=35 依赖被剥特性=0` → `served copies compared=32 of 32 assets` → `clean: no authored figure depends on markup the reader does not get`，**退出码 0**。这条轴从落库到全树第一次绿，中间红了两次，两次的红都是真缺陷（`paint-order`、`animate@fill`），不是噪声。
5. **改完这张图，可读性轴的分母动了**：标签总数 1056 → **1057**（`<br/>` 变成真的第二行 `<text>`），命中 734 → **735**，因为这一行是 12px 写在 980 画布上、落纸 9.4px。`--column 1152` 的宽版 what-if 命中数不变（18 张 / 204 个），1152 列下 980 画布 1:1，这行刚好够线。**这张图仍在批 2 的 27 张名单里**，本轮只修「读者拿到的与作者画的不一样」，不顺手做重排。

### 七、留下的

- 还有 **27 张**正文图在门槛下。最险的六张：`11-trace-waterfall`、`12-coding-agent-loop`、`16-sandbox-layers`（都是 8.00px），`03-attention`、`06-memory-tiers`、`08-collab-patterns`（8.40px）。批 2 从 8.00px 这三张开始。
- **`KNOWN_STRIPPED` 只有 `paint-order` 一条，另外两条规则住在别的表里**（`STRIPPED_ANIMATE_TARGETS`、`LINEBREAK_TAGS`）。三张表在离线腿里等价生效，但只有第一张带处方文案；下次再量到新的被剥写法，应该并成一张表，别再开第四个变量。
- **`labs/out/lab{1,2,4,6}.out` 长期显示为「已修改」，但内容与 HEAD 逐字节相同**（`git hash-object` 与索引 blob 一致，`git diff` 零输出）。这是重跑实验只动 mtime 留下的 stat-cache 假象，不是待提交的改动——别再为它开一轮。
- **上线的两条腿会轮流落后**：第 64 轮是 `.md` 领先、HTML 落后两轮；本轮推送后 3 分钟复测是 **HTML 已到第 65 次、`.md` 还停在 64**。所以「哪条腿先新」没有规律，`check_live_sync.py` 取较差判决的设计是对的，别把它改回单腿。
- 更新日志页按操作者的决定**保持单页**，249KB / 渲染 10MB 那条账原样留着。
- 未做：`check_table_overflow.py --pages all`、移动端宽度读数、图注两级合并、线上正文完整性轴。

## 2026-09-23（第 64 次）新轴·「自绘 SVG 标签到读者眼里还剩几像素」：32/32 张正文图都有低于 12px 的标签，956/1042 个标签命中，最小 5.20px（首页封面）；机械放大字号已渲染验证（×1.25 不塌、×1.58 撞版），属产品级取舍，本轮不动图。线上抽查另抓到两条：封面横幅页数失真（187→196，已修并落判据）、「是否已上线」的门只读了 `.md` 端点（渲染页还差两轮，已改成两腿取较差）

本轮动正文 0 页、封面资产 1 处（横幅里的页数），落库判据 3 个文件（新增 `check_svg_legibility.py`；`check_readme_stats.py` 加 banner 腿；`check_live_sync.py` 改成两腿判决）。第 62 轮量了 Mermaid、第 63 轮量了公式和表格，书里剩下的一大类像素从来没被量过：**35 个手绘 SVG 资产**，其中正文真正用到的 **32 张**。

### 一、轴与读数

1. **口径**：从正文页扫 `![](...svg)` 引用（`14-templates` 照 README 排除，封面和站内图标不算正文图），对每张图用 ElementTree 走一遍 `<text>`/`<tspan>` 并**把继承的 `font-size` 算上**（房规模板在 `<svg>` 上写 `font-size="13"`，多数节点自己覆盖），共 **1042 个文字标签**。有效字号 = authored px × min(1, 列宽 / viewBox 宽)。
2. **机制是量出来的，不是推的**：线上把 SVG 画成 `<img data-testid="zoom-image" style="max-width:100%;height:auto">`。按严重度取最险的 4 页，把线上页面副本从 localhost 发进无头 Edge，探针读 `naturalWidth` 与落纸宽：**1920 → 0.4，960 → 0.8**，`<main>` 768（宽版布局仍未生效）。所以一张 9.5px 的标签到读者眼里是 **7.6px**。
3. **缺陷**：**32 张里 32 张**至少有一个标签低于 12px 门槛，**956/1042 个标签**命中；各图最小有效字号落在 **5.20~10.40px**。最险的一张不是正文图而是**首页封面 `banner-home.svg`**：1920 画布进 768 列只有 0.4 倍，13px 的 authored 字落纸 **5.20px**（21 个标签里 20 个中招）。脚本按 eff_min 排序逐张列出，最险的前 12 张最小标签都不超过 8.62px。
4. **方案 B 救不了这一轴**：`--column 1152` 复跑，读数从「32 张 / 956 个」降到 **23 张 / 378 个**。宽版布局只是把 0.8 的缩拿掉（960 画布在 1152 列里 1:1 落纸），**9.5px 的小字还是 9.5px**，而 1920 的封面仍缩到 0.6。这条轴的账不是开关能结的。

### 二、尺子的三条控制（真实树里 32/32 全 FAIL，所以必须种一张「干净」的）

1. **ruler（几何）**：种 1920 / 960 / 400 三张画布进读者列宽的盒子，每张的 scale 必须等于 `min(1, 列宽/自然宽)`。768 下回到 0.4 / 0.8 / 1.0，1152 下回到 0.6 / 1.0 / 1.0——断言是列相对的，开关一开尺子不用改。没有它，「0.8」和「探针读容器恒返回 1.0」长得一样。
2. **classifier selftest（判据）**：种一张 400 画布、字号从 `<g>` 继承的**干净图**（必须 0 命中），和一张 960 画布上 9.5px + 16px 两个标签的脏图（必须只命中 9.5px 那个）。真实树里没有一张图过关，所以「见谁都报缺陷」和「量到缺陷」的输出无法区分——能通过的对照才算对照。
3. **前提断言**：线上 `<img>` 必须还带 `max-width:100%`，`<main>` 必须等于 `--column`，正文图数 ≥25 的防空跑，且浏览器腿至少要有 2 页真排出图来。平台哪天不再缩放，轴会红，不会悄悄把 32 张读成「全部 1:1、没有缺陷」。

### 三、机械放大字号：试了，而且是渲染出来看的

等比缩放救不了这条轴（画布和字一起放大，比值不变），唯一的仓库内修法是提高**文字对画布**的比例。拿最密的一张 `03-context-budget.svg` 在 768 盒里真渲染了三版：

- **×1.25**（把 960 画布的标签抬回 authored 尺寸，即取消 0.8 的缩）：胶囊框、底部注记、时间轴刻度全部没塌，目检干净。
- **×1.58**（真正够到 12px 门槛）：`稳定前缀 8% ≈16k` 撑出药丸框，底部「预算纪律…」一行和 `1800k`、`约 80%` 互相压字。**够到门槛的那一版把版式撞坏了。**
- 所以机械 bump 只能把有效字号抬到 9.5~13（轴照旧红），要过 12px 门槛得逐张重排文字与画布的比例——32 张手绘图的版式改动是产品级取舍，按目标约定先汇报、先落尺子，不动图。本轮正文与资产 0 改动。

### 四、harness 与口径教训（五条都是本轮真踩的）

- **`--dump-dom` 在 load 事件就退**：异步 `setTimeout` 轮询来不及报，ruler 靠一个 `/hold?rid=` 阻塞子资源续命，live leg 反过来必须**去掉**这个 flag（页面靠 hydration 才排版出图）。
- **report id 会串**：live leg 复用 ruler 的 `rid=1`，`wait` 扫到第一条同 id 的报告就返回，于是把尺子的读数当成「线上这张页没有图」。两条腿的 id 现在错开（10 起）。
- **`window.onerror` 会捕到平台自己 bundle 的错**：线上页副本在 localhost 上抛跨源 `Script error.`，fatal 若和真报告共用 id，就会抢先把 latch 放掉、把真读数挤掉。fatal 现在走 `rid+1000` 且不碰 latch，只在断言失败时作为诊断打出来。
- **一行 `"/." in "/" + rel_dir` 吃掉过整张最险的图**：判定「是否在子目录里」的这两种写法看着等价，其实不同——内容根的 `rel_dir` 是 `"."`，于是 `docs/README.md` 被整页跳过，连带它的封面横幅（全站唯一 1920 画布、有效字号 5.20px 的那张）从统计里消失，轴在 31 张上自称跑完。修法是显式 `rel_dir == "."` 分支 + 「31 还是 32」和 README 统计对平。另外：**线上页副本哪一页不 hydration 是每轮随机的**（客户端路由没有 localhost 文件名的路由），所以「读不到 `<main>`」不报错而是改读服务端 HTML 并明说，同时保留 ≥2 页浏览器排版的地板，防止整条腿滑成空读。

- **推送这道门也会误判**：收盘补账时显式 `git push git@…` 被拒 `cannot lock ref 'refs/heads/main': is at 3008046 but expected c8a7388`——远端其实**已经在这个提交上了**。而 `git status -sb` 当时报 `ahead 7`，看着像七轮没推上去。两条读数都对：本仓库习惯**显式推 URL**，这种推法不更新 `refs/remotes/origin/main`，所以 ahead 计数只反映上一次 fetch 的快照，永远会谎报落后。判「推上去了没有」只能读 `git ls-remote <ssh-url> main` 与本地 HEAD 比 hash（本轮实测两侧同为 `3008046`，线上门随后两腿到 64、退出码 0）。这条和五.2 是同一个教训的两面：**门要看被量对象本身，不能看本地缓存的影子。**

### 五、线上抽查抓到的第二批缺陷（两条都是量出来的，不是目测）

1. **封面横幅的页数是假的**：用无头 Edge 以 1280 视口截了线上首页，横幅上写着「从原理到生产：**187 页** / 19 章」和「19 章 · **187 页全景**」，而同一页正文第一行是 **196 页**。全站统计轴 `check_readme_stats.py` 一直没抓到它，原因很单纯：**它读的是 Markdown，横幅是图片**。改成 196 后在 768 盒里真渲染复看：两处文字都没撑框、没换行。落库的修法不是改完就算：`check_readme_stats.py` 新增 banner 腿，只从 `<text>` 节点里取数（`x="196"` 是坐标不是声明，不能算），读 4 条声明（页数×2、章数×2）；反例控制**重演本轮这个缺陷**——把 196 改回 187 必须报 2 条 `banner pages` MISMATCH，只报 1 条说明另一处没被读到。修前该腿读数 2 MISMATCH，修后 `banner pages=196 chapters=19` 全 ok。
2. **「上线了吗」这道门只看了一条腿**：第 61 轮写的 `check_live_sync.py` 读线上 changelog 的 **`.md` 端点**来判断 HEAD 是否已发布，而 `.md` 比渲染页先同步（这条第 59 轮就记过账）。本轮实测：`.md` 已经读到第 64 次，**同一页的 HTML 还停在第 62 次**——9,733,032 字节，连查 8 次一个字节没变，落后 HEAD 一小时以上。于是这道门会在读者根本还没看到新内容时说「已同步」。现在两条腿都读，**判决取较差的那条**，并分别打印各腿的最新轮次；复跑读数 `leg md newest=64 / leg html newest=62 missing 63, 64`，红得对了。

3. **收盘复测（两腿都到 64，横幅资产已同步）**：推送后把这道门挂着轮询——第 3~6 次仍是 `len=9733032 r63=False r64=False`，**第 7 次跳到 `len=10240845`，63、64 两轮的轮次标题同时出现**，`SYNCED`。也就是说渲染腿不是坏了，而是**慢**：一次更新要等十几分钟到一小时以上，正文页约 1 分钟。门最终读数 `local newest round=64 / leg md newest round=64 (140715 bytes, 80 rounds) / leg html newest round=64 (10240845 bytes, 295 rounds)`，退出码 0。封面横幅走的是另一条路：`~gitbook/image` 资产约 **40 秒**就到达，线上拉回来 6802 字节，`187` 不存在、`196` 存在；再以 1280 视口重截线上首页目检，横幅两行都读「196 页 / 19 章」「19 章 · 196 页全景」，无撑框无换行。对比着记：**同一轮里同一批字节，资产 40 秒、渲染页 20+ 分钟**——所以「查资产」和「查页面」不能共用一个等待时间。另留一眼：截图上封面那些 5.20px 的小标签在读者列宽下确实糊成一团，这是六.1 那条待取舍最直白的证据。

### 六、留下的取舍与未做

- **32 张正文 SVG 的有效字号仍全部低于 12px**：本轮的开放缺陷，等的是一次改版式决策（宽版开关 + 是否逐张重排文字/画布比例 + 首页封面是否改成窄画布），已向操作者汇报。轴的退出码故意保持 1（红）：读数真实，门槛不能为了绿灯往下挪。
- **更新日志页本身可能已经太大**：249KB Markdown → 9.7MB 渲染页，是全站最重的一页，而它的渲染腿比正文页慢得多（见五.2）。拆成「近 10 轮 + 存档页」能治新鲜度，但那是信息架构改动（新增页、动导航、改「详见更新日志第 N 次」的指向），按约定先问操作者，不自己动。
- **行内公式轴**：探过了——651 条行内式、最长 90 字符，表格内 16 条最长 19 字符，而 `.katex-display>.katex{white-space:nowrap}` 只管 display 那条路，行内本来就能折行。暂不落库。
- **102 张超宽 Mermaid 图仍在等站点开关**（本轮 4 页 `<main>` 复测还是 768px）。
- 未做：`check_table_overflow.py --pages all`、移动端宽度读数、图注两级合并、线上正文完整性轴。

## 2026-09-23（第 63 次）新轴·「正文内容在 768 列里的真实下场」：276 条 display 公式量出 2 条超列（已改 stacked）；负结果——居中的超宽公式其实滚得到；表格 2131 格 0 溢出

本轮动正文 2 页，落库判据 3 个文件（新增 `check_content_overflow.py`、`katex_render_html.mjs`、`check_table_overflow.py`）。第 62 轮量清了「读者拿到的列宽是 768」，本轮第一次去量**装进这条列里的内容**：公式和表格。它们和 Mermaid 图是同一类尺寸问题，机制却完全相反，所以判据也完全不同。

### 一、公式轴：量到的缺陷不是「看不见」，是「得拖」

1. **口径**：276 条 authored display 公式（106 页，`14-templates` 照 README 排除），用钉住的 katex@0.18.7 渲成浏览器真正要画的 HTML，再从 localhost 发给 Edge，塞进 `max-width:768px; overflow-x:auto`——线上 wrapper 的同一组类，不手写样式。墨迹宽用 `Range` 量，因为 `.katex-display>.katex` 是 `display:block`，量元素本身只会量到盒子（ruler 里这条做成了断言：768 盒与 1100 盒的元素宽不同、墨迹宽必须相同）。
2. **一个先立后破的假设**：这条轴最初是为「居中 + `overflow-x-auto` ⇒ `scrollWidth` 只算结束边 ⇒ 左半边永远滚不到」写的。种下的 2807px 反例量出 `lostLeft=0 lostRight=0 maxScroll=2041`——Chromium 把居中超宽的溢出全放在结束侧，滚得到。于是度量改成**拖距** `over = 自然宽 − 可视宽`，`unreachable=0` 作为负结果每轮照打；ruler 两头都断言（反例必须 `drag>0` 且 `lost==0`），平台哪天改了滚动模型会立刻红而不是悄悄对。
3. **方案 B 救不了公式**（本轮断言，不是推测）：线上 math wrapper 的 class 集仍是 `decoration-primary/6 max-w-3xl overflow-x-auto print:break-inside-avoid w-full`，硬 `max-w-3xl` 且**没有 `layout-wide:` 变体**。所以公式唯一的修法是把内容排进列里。
4. **缺陷与修复**：2 条超列——`07-planning/subgoal-planning.md` 自然宽 877.7px、`02-agent-basics/agent-vs-workflow-chatbot-copilot.md` 862.7px，两条都是拿 `\qquad` 把两三句陈述横着串成一行。改成 `aligned` 按 `=`／`→` 对齐换行，**一个字都没删**。复测：276 条全量，max 877→766，over-column 2→0（门槛 16px＝一个字形），`render-errors=0`；解析判据照旧 927 条公式 0 失败、版本 0.18.7。
5. **余量**：`02-agent-basics/perception-planning-action.md` 的终止判据式子 766px，离列宽只剩 2px。没动它——它没过阈值，动它就是凑指标；但轴里加了 headroom 行，每跑必报，下一轮若有人往那条式子里再加一项就会看见红。

### 二、表格轴：0 溢出，但理由和我原想的不一样

1. **结构底**：authored 表格 175 页 / 2218 行 / 7637 格，最宽 6 列。平台给每格 `min-width:100px`，容器是 `flex flex-col min-w-full w-fit` + `overflow-x:visible`（**没有滚动条**），所以 ≥8 列的表必然撑破 768 列。6×100=600 装得下，今天没有可修的，但这条悬崖写成了 `floor_check()` 的断言而不是 changelog 里的一句话。
2. **真渲染**：取「单元格里最长不可断串」排前 8 的页面（`13-resources/projects/README.md` 一张表就 1670 格），把线上页面副本从 localhost 发出去，探针量墨迹越出格子的距离。读数：`<main>` 8/8 全 768px；**2131 格 spill=0**；比列宽的表 0 张。
3. **控制**：同一格塞进 65 字符、无连字符/斜杠/空格的串，保留平台断行 → 0 溢出；把 `overflow-wrap` 关掉 → 溢出 205~298px。尺子有牙，「0 溢出」才成其为读数。
4. **本轮被自己的控制打脸一次**：第一版控制串用的是书里真有的 `agentbench-webarena-swebench-gaia-toolbench.md`（46 字符），关掉断行仍然 0 溢出——**浏览器在连字符后面就能换行**。于是预筛的「不可断串」定义补上连字符与斜杠两个断行点，控制串换成下划线型。记法：控制若不可能失败，就不是控制。
5. **平台侧事实**：单元格计算值 `overflow-wrap:anywhere; word-break:break-word; white-space:pre-wrap`，长标识符是被强断的。这条每跑断言：GitBook 哪天撤掉它，全站长 token 会糊到邻格，轴会红。

### 三、目检（本地 + 线上）

本地 768px 列真渲染 PNG（钉版 KaTeX + 真 webfont，同一条轴用的那套）：两条改后的式子整条在框内、按 `=`／`→` 对齐；同框保留的旧 `\qquad` 形态出现横向滚动条，且句尾在框边被切——「拖」这个度量就是这么来的。

推送后线上抽查（`60a6962`）：两页各两条腿。`.md` 端点已带 `\begin{aligned}`、`\qquad` 全站这两页读 0；读者文档里 KaTeX 的 `<annotation>` 数出 aligned 块各 1 个，`Agent 的收益／代价`、`局部失败／可跳过失败` 四个词都在读者可见正文里，wrapper 仍是 `overflow-x-auto`。真浏览器（无头 Edge，1280 视口）截线上页并裁到公式带目检：两页的 stacked 式子整块在列内、按 `=`／`→` 对齐、**没有横向滚动条、句尾没有被切**。顺带一提，`browser-use` 那个 MCP 浏览器实例的 `innerWidth` 读 0（视口没尺寸），在它上面量出来的 512px 一类的数全是假的——线上几何读数只认自己起的无头 Edge。

### 四、留下的取舍与未做

- **102 张超宽 Mermaid 图仍在等站点开关**：本轮 8 个线上页面复测 `<main>` 还是 768px，宽版布局尚未生效（`check_table_overflow.py` 的 `main=` 列即读数）。开关一开，公式轴要 `--column 1152` 复跑，但公式 wrapper 是硬 `max-w-3xl`、不会跟着变宽——见一.3。
- 未做：手机宽度下的公式/表格读数（本沙箱 Edge `innerWidth` 钳在约 1250px，报 vw=390 的数就是造数）；表格轴默认只跑风险前 8 页，`--pages all` 留给放得下 175 次浏览器启动的一趟；**行内**公式的溢出没量（inline 不套 `overflow-x-auto`，机制不同，另立一轴才诚实）。
- `labs/out/*.out` 四个实验输出文件仍是脏的（跑实验留下的），与本轮无关，不带上提交。

## 2026-09-23（第 62 次）新轴·「读者实际拿到的正文列宽」：1120 是宽版布局的数，默认列宽实测 768；217 张图按真列宽重测，102 张被整体缩小、24 张标签掉到 12px 以下

本轮动正文 0 页，动判据 3 个文件（`check_mermaid_geometry.py` 修尺子、新增 `check_live_column.py`、新增 `check_live_sync.py`），并把 README 里一句从第 21 轮站到本轮的假话改掉。缺陷本身（102 张超宽图）没有动：三条修法都是版式取舍，按目标里的停一停条款留给操作者定。

### 一、量出来的四件事

1. **线上默认正文列宽是 768px，不是 1120px。** 页面 markup 是 `<main class="… max-w-3xl … layout-wide:max-w-6xl …">`，`layout-wide` 默认不在祖先上；段落实测 707px。1120 恰好是 `max-w-6xl`（1152）减内边距，也就是**宽版布局**的列宽——第 24 轮以来一直拿它当默认，README 据此写着「最宽 1116px，全部落在正文列宽（1120px）内，线上不会被缩放」。`.gitbook.yaml` 里没有宽度项（只有 `root` 与 `structure`），所以这条改不动仓库。
2. **超宽的图是被缩小，不是被滚动。** Mermaid 出厂 `useMaxWidth: true`——从线上真正加载的那份运行时（URL 逐字取自线上 markup，`mermaid@11.14.0-zenuml@0.2.2.mjs`，6 465 693 字节）里读出 flowchart/sequence/class/state/er/pie 全是 `useMaxWidth:!0`；渲染出的 SVG 带 `width="100%"` + `style="max-width: <自然宽>px"`。于是容器比自然宽窄时整张图连同标签一起缩，`overflow-x-auto` 那层永远拿不到可滚的子元素。本地同引擎实测：2420px 塞进 768px 格子 → 标签 5.08px；1147px → 10.71px；653px → 16px 不动。
3. **全站重测（引擎断言 `local=11.14.0 live=11.14.0`，217/217 真渲染，两张常驻地雷照旧被捉住）**：自然宽 >768px 的有 **102 张**，其中 **101 张被缩放、0 张横向滚动**；标签实绘最小 **11.0px**（正文 16px，缩放 0.69），中位 16.0px；按 12px 门槛判 ILLEGIBLE **24 张**，`problems=126`。宽度分布 `>640 142 / >720 114 / >768 102 / >800 93 / >900 65`。最宽的三张：`12-applications/README.md#1`、`18-frontier-2026/openai-agents-api.md#2`（各 1116px）、`16-ai-infrastructure/data-vector-storage.md#1`（1112px）。
4. **第 61 轮那次「线上还差一轮」是发布滞后，不是渲染缺陷**：HEAD 提交后 **213 分钟**线上更新日志才吐出新一条编号（`tools/checks/check_live_sync.py` 的读数），4 个新锚点此后全部在线上有 `<a href>`。

### 二、本轮真正的缺陷在尺子上

`check_mermaid_geometry.py` 的 fixture 用 `%%COLUMN%%` 占位，替换时写的却是模块常量而不是 `column` 形参——**传 `--column 768` 仍然排版 1120px 的格子**。修前那一趟报的是「0 张缩放、217 张横向滚动、最小字号 16.0px」，三条全是假的。记法：**固定宽度盒子的 `scrollWidth` 恒 ≥ 盒子宽**，拿它去比一个更小的假设列宽，必然 N/N 全响；读数「217 张全在横向滚动」不是内容结论，是尺子在报警。修完后同一条轴给出的分布（101 缩放 / 0 滚动 / 116 原样）与线上运行时读出的属性互相独立、互相印证。

同趟还把 SVG 自己的 `width` / `style` 属性记回来（`wa` / `st` 两列），「缩放还是滚动」这一分叉从此一次跑就能重验，不必再靠猜。`COLUMN` 默认改为 768，浏览器窗口宽度独立成 `WINDOW=1280`。

### 三、两条新轴落库

- `tools/checks/check_live_column.py`：线上列宽轴。探针同时量最宽段落、`<main>` 宽、标题宽与 class 列表；两个控制盒（500px、1100px）走**同一段探针代码**，先证明尺子不夹紧才承认列数；跨页散布 >16px 判 `SPREAD`（说明量到了子元素而不是列），页面没水合记 `NOHYDRATE` 而不是通过。
- `tools/checks/check_live_sync.py`：以「线上/本地更新日志里最新的 `第 N 次` 编号」判定站点是否已到 HEAD，本地断言 ≥50 条编号防盲判，`--watch` 可等。滞后是发布常态，这条把「先别当缺陷」变成工具。

### 四、目检

本地 768px 列真渲染 PNG：`12-applications/README.md` 那张 1116px 的图整张缩到列宽，节点标签明显小于正文；同一趟里 653px 的 `19-labs/lab6-guardrails.md` 一字未缩。

### 五、留下的取舍与下一轮

**102 张超宽图本轮一张都没动**，因为三条路都是版式取舍，不是能靠阈值判红绿的缺陷：

| 方案 | 做法 | 代价 / 前提 |
|---|---|---|
| A 重排 | 逐张压到 ≤768px（拆图、缩短标签、改纵向） | 最贴合默认列，但要重画 102 张；六层链路压窄会变高，纵向滚动变长 |
| B 开宽版布局 | 在 GitBook 编辑器里把该 space 的布局切到 wide（`layout-wide`，列宽 1152） | 零改内容：最宽 1116 < 1152，217 张一张都不缩。**仓库里做不到**（`.gitbook.yaml` 无此项），需要你点一下，且要先确认这个计划的站点支持宽版布局 |
| C 保字号、改横向滚动 | 给超宽块的 `%%{init}%%` 加 `useMaxWidth:false` | 本轮实测可用：翻开关后 painted=自然宽、标签回到 16.0px、容器 `scrollWidth`=自然宽（即真能滚）。代价是读者要在图内横拖，手机上 1100px 的图要拖 3 屏。注意配置键按图种分（sequence 的键是 `sequence`，写成 `sequenceDiagram` 不生效——本轮就因此漏了一张） |

我的建议是 **B**（一次站点设置解决 217 张、不动一个字的读者可见内容），其次 **C**（仓库侧可复现、字号优先），A 当长期活。**等你定方向，下一轮按选定阈值复跑收口。**

未做与已知边界：手机宽度下这张图会缩到多少没量——本沙箱 Edge 的 `innerWidth` 钳在约 1250px，报一个 vw=390 的读数就是造数，`check_live_column.py` 里已把这条写成注释；`labs/out/*.out` 四个实验输出文件是脏的（跑实验留下的），与本轮无关，提交时不带上。

### 六、补充（操作者选 B 之后）：用站点自己的 CSS 量出「宽版布局到底给多少列」

操作者定了 **B（开宽版布局）**。仓库里改不到这个开关，所以先把「B 到底值多少像素」量成数，而不是停在 1120/1152 的算术猜法上。

做法（已落库为 `tools/checks/check_wide_layout_ab.py`，复跑一条命令即可）：把线上页面 markup 里点名的 4 份 CSS **逐字下载**、从 localhost 发出去（本沙箱 Edge 无外网），套上从线上读来的真实 `<main class="…">` 字符串，里面放本书最宽那张 authored 图（`12-applications/README.md#1`，自然 1116px），探针先原样量一遍，再只往 `<body>` 里一个元素加站点自己的 `layout-wide` 类——选择器是 `body:has(.layout-wide) .layout-wide\:max-w-6xl{max-width:72rem}`，所以加类这一步是站点机制，不是我手写样式。

| 读数 | 默认布局 | 加 `layout-wide` |
|---|---|---|
| `<main>` 宽（计算值 `max-width`） | **768px**（768px） | **1152px**（1152px） |
| 1116px 那张图实绘宽 | 768px（`width="100%"` + `max-width:1116.015625px`） | **1116px**（原样） |
| 图内标签实绘字号 | **11.01px** | **16.0px** |
| 容器 `scrollWidth` | 768（缩，不滚） | 1152（图未溢出） |

控制盒 500px / 1100px 读回 500 / 1100，且默认列必须读回 768（读到 1280 就说明 CSS 根本没生效）——这两条都断言在脚本里。

**并收窄 §五 B 行那句「217 张一张都不缩」**：1152 是 `<main>` 的宽，图真正能用的格子还要减掉内边距。默认布局实测段落 707px vs `<main>` 768px，即横向内缩约 61px；按同一内缩推宽版 = **约 1091px**。以 1091 复跑全站几何轴（`python tools/checks/check_mermaid_geometry.py --column 1091`，217/217 真渲染、引擎对齐断言照旧）：自然宽超限 **14 张**（1092–1116px，全部集中在最宽那批），判为缩放 5 张，标签实绘最小 **15.6px**、中位 16.0px，`problems=14`。也就是说 B 把「24 张标签掉到 12px 以下」这个真正的可读性缺陷一次清零，最坏的十几张也只是从 11px 档回到 15.6px 档的轻微缩放；若要连这 14 张也归零，才需要 A 的局部重排。阈值 `COLUMN` 仍保持 768，等你真在站点上切到宽版、`check_live_column.py` 复跑出 ~1152 之后再动，别提前放宽判据。

补充的两处自身缺陷（同轮记录，不静悄悄改掉）：① 上一轮那份 `check_live_column.py` 是**带着 `TypeError` 提交进仓库的**——探针模板有 4 个 `%` 占位、只传了 3 个参数，本轮补 `min_paragraphs` 后同一趟复跑 3 页 × 2 视口全绿、默认列宽 768 再次确证。教训与第 58 轮那条同型：落库的轴要在落库那趟跑到能输出读数为止。② 本轮这段 A/B 的第一版把整份 HTML 丢进 Python 的 `%` 格式化，于是 Mermaid 的 `%%{init}%%` 被吃掉一个 `%`，渲染直接失败；同趟还有两次「假通过」——CSS 下载成了 404 页面（4 份文件大小一模一样都是 11 164 字节，而控制盒照样读 500/1100），以及 `mermaid.render()` 成功后忘了把 SVG 塞进容器（量出一个自信的 `painted=None`）。三条现在都写成了断言。

**还有一条要认：`bddce32` 是带着一条红轴推上去的。** 提交后复跑判据批处理，`check_quote_fidelity.py` 报 `unmatched=1` 并非零退出——本轮补 §一 那句时把 README 原句抄成了「最宽 1116px，全部落在正文列宽内…」，漏掉 `（1120px）`，而这条轴存在的理由正是「更新日志里加了引号却没回核原文」（第 55 轮为它落库）。两处分开修：① 引号里补成逐字原句；② 这条轴当时无法表达「一句假话已被删掉、更新日志引用它只为记录撤回」——删掉的句子全站再也不存在，逐字回核必然红。于是加了 `RETRACTED` 登记表（句子 → 所在页 + 轮次 + 为什么是假的），登记的引用**反过来断言它已从所有知识页消失**，仍在则报 `RETRACTION-NOT-APPLIED`；README 是唯一豁免位，因为把旧假句和「是假的」并排印在首页正是读者该看到的口径。这条新腿的牙验过：把该句种回 `03-llm/what-is-llm.md` 一级标题下 → `unmatched=1`、退出码 1，撤掉 → 回到 0/0，页面按字节还原（种在 EOF 会落进「相关知识点」而被排除，那是第 60 轮记过的坑）。修后 `content pages=197 attributed quotes=6 unmatched=0`。

## 2026-09-23（第 61 次）新轴·「叫读者去看出处，却没给可点的链接」：判据从 247 处收到 5 处真缺陷，全部补成链接；锚点这条腿用「修前 0 个锚点」证明它自己有牙

本轮动正文 6 页（5 处补链接 + 1 处措辞），新增 1 条判据 `tools/checks/check_source_pointers.py`。没有一处是删内容：5 处都是把**同一页底部已经写着的出处**提到读者站着的那一句里。

### 一、这条轴是五轮收出来的，不是一开始就长这样

| 版本 | 判据形状 | 全站读数 | 为什么废 / 留 |
|---|---|---|---|
| 1 | 带数字（%、倍、ms、万）且本行 ±1 行没有链接 | **247 处 / 71 页** | 废：`输入 token 常是输出的 10–50 倍` 是本书自己的工程经验值，没有外部出处可指。照这条改会**逼出链接灌水**——判据自己成了缺陷源 |
| 2 | 再加外部归属词（官方/论文/报告/发布/文档…） | 18 处 / 12 页 | 废一半：12 处仍是经验值、自造示例、lab 的真跑读数 |
| 3 | 换成「句子让读者去看某份文件」的措辞 | 128 处（去掉已带链接后 75 处） | 废：`把错误原文回填给模型` 里的「原文」是普通名词（一字不差塞回去），不是指针 |
| 4 | 「去看」动词与外部文档名词必须**同句** | 7 处，其中 6 处真缺陷 | 留 |
| 5 | 动词不能是 `常见`/`看见` 的尾巴；短句内不许跨标点吃下半句 | **6 处 → 5 处** | 最终形态：`## 常见基准` 这类假阳性出局 |

### 二、修掉的 5 处 + 1 处措辞

| 页 | 修前（读者看到的话） | 修后 | 链接从哪来 |
|---|---|---|---|
| `10-evaluation-safety/safety-incidents-2026.md` | 「（配置与任务集见官方发布页）」 | 同一句里的 Astra 发布页变成链接 | 该页「参考资料」已有这条 URL |
| `18-frontier-2026/computer-use-2026.md` | 「Astra 官方称较 GPT-5.6 Sol 约 47% 更少时间/任务」 | 句尾补一条发布页链接 | 同上 |
| `18-frontier-2026/frontier-models-2026.md` | 价格行「低于 Astra（见官方页）」 | 「官方页」即链接 | 同上 |
| `18-frontier-2026/claude-agent-sdk.md` | 「集成产品不能自称 Claude Code（见官方 branding guidelines）」 | 改成条款真正禁止的事 + 链到 Legal and compliance | 本轮现查现用：条款写 "You can't use the Claude Code or Anthropic names or logos as part of your own product, feature, or company name"；URL 一并补进该页「参考资料」 |
| `09-frameworks/mcp-servers.md` | 「参考官方 TS/Python SDK」 | 两个 SDK 各自成链 | 仓库内已有这两条 URL（13 章项目索引），本轮逐条打开确认 200 |
| `09-frameworks/README.md` | 自测题提示「见 README 选型心法、langgraph.md」 | 改成「本章开头的『选型心法』小节，以及 LangGraph」并补内链 | 判据不响（这一处 before=0），但章 README 里写「见 README」，读者会以为是站外某个文件 |

### 三、判据落库与它的排除项

`python tools/checks/check_source_pointers.py` → `pages=191 pointer_lines=3 findings=0`。排除项每条都有理由：`docs/00-index/` 的更新日志会复述它正在批评的写法；围栏与行内代码里的写法示例不算承诺；表格里的「同上」吃的是同一张表 出处 那一列的链接，不是没有链接。

- 这条轴**故意窄**：宽判据（第 1、3 版）会把作者推向给经验值硬挂链接，那正是目标里「不灌水」的反面。窄到只认「叫读者去看某份外部文件」这一种句子形状，代价是它管不到「数字没出处」的大类——那个大类本轮量过、判过，结论是不该由判据管。

### 四、断言级验证（三腿，每条都能被证伪）

1. **同一判据喂修前的树**：把 6 个文件在 HEAD 里的版本逐一经 `scan_text()` → `before=5 after=0`（逐文件读数在探针输出里）。没有这条，`findings=0` 与「判据瞎了」是同一个数。
2. **真实页变异控制**：6 张已发布页复制进系统临时目录，在**页内第一个一级标题之下**种一句无链接的指针 → 每页恰好 +1，撤走回基线（`live mutation ok (0 -> 1 -> 0 ...)`）。种在页尾会落进被排除的「相关知识点」、种在第 1 行会落进 frontmatter——第 60 轮踩过的两个假干净，这条判据一开始就避开。
3. **锚点这条腿**：本轮修的就是链接，所以量的不是「文字顺不顺」而是**读者点得到吗**。6 处逐条过 markdown 渲染，期望的 href 必须出现在 `<a href>` 里（6/6 命中）；正控制是**同一个渲染器跑修前的措辞 → 0 个锚点**。再用无头 Edge 按 1120px 正文列宽整段截图（`r61_render_eyeball.png`）逐条看过：6 条都是蓝色下划线、目标正确。截图里那一行表格是裸管道、有序列表从 1 重启——那是**逐行摘出来单独渲染**的产物，不是页面缺陷。

### 五、判据内部的四个 bug，也全是假阳性逼出来的

`常见基准`（动词是「常**见**」的尾巴）、`（可含论文、官方文档、源码）`（跨标点吃到下半句）、`只参考有权限的文档`（引号里的祈使句，不是指针）、以及第一版把裸 `页` 当外部名词——它一次点亮 6 处「（见本页末尾）」这种**同页导航**。四条都写成了判据内部的常驻反例（12 条 look-alike 必须保持干净，5 条真指针必须响）。

### 六、本轮复跑读数（离线轴全绿）

- 结构 `pages=198 problems=0`｜导航 `196 pages problems=0`｜组件配对 `198/0`｜引用逐字回核 `197 页 5 引 unmatched=0`｜汉字 `prose CJK=330896 findings=0`（日志与 README 落笔后的全站读数，可引用的是差值：6 页正文净 **+32**；两页各 -2 / -1，是因为「官方发布页」四个字换成了拉丁站名，不是删内容）｜更新日志条目标题 `HEAD=52 tree=53 lost=0`（第 53 条就是本条，提交后两边同为 53）｜跨页复述 `dup=0 near-band=3`｜公式 `pages=108 formulas=927 failures=0 @katex 0.18.7`｜README 统计全轴 ok。
- 新增外部链接 4 条（1 条 OpenAI、1 条 code.claude.com、2 条 GitHub SDK），逐条实测：GitHub 与 code.claude.com 返回 200；`openai.com/index/gpt-6-astra/` 对本沙箱返回 **403**（该站对非浏览器 UA 设墙），这条 URL 全书已在用 12 处，不是本轮新引入的风险。

### 七、遗留 / 未做（诚实）

- **第 60 轮的闭环补记 `ead64e9` 到本轮开跑仍未上线**：20 次抓取（13:15–13:29）字节数冻结在 `8,931,085`（= 上一份 `ef93a5f` 的渲染），三枚新针全缺、同页控制针在 → 又一次**发布滞后**，不是内容缺陷。观测过的间隔累计：53 秒 / 90 秒 / 3–4 分钟 / 26 分钟 / 75 分钟 / 以及这次 >15 分钟未命中。
- **本轮改动同样待线上复验**：推送后按页抽查 6 个锚点是否真的到了线上页面（本地渲染绿不等于线上绿）。
- **待操作者拍板（本轮不动）**：双层图注是否合并；是否补一条「线上正文完整性」轴；聊天里贴过的 GitHub PAT 需要轮换。

## 2026-09-23（第 60 次）第一次有判据**成对地**量「同一句话、同一条公式在两页各印一遍」：6 条跨页复述的公式全部捉到，全部改成指向而没有删定义；这条新轴自己差点骗了我两次——把反例种到页尾和种到第 1 行，它都读出「干净」

本轮动正文 5 页（净效果：删 6 处跨页复述的展示公式、把它们改成本页白话结论 + 指向权威页），新增 1 条判据 `tools/checks/check_prose_duplicates.py`。

### 一、这条轴为什么现在才有

第 52、55 轮都做过"去重"，但那是**我肉眼看着哪两块像**再去拆——没有一把能两两比较全树的尺子。所以"重复"这件事的口径一直是我记得的那些，而不是量出来的那些。本轮把它变成判据：

- **单元**：围栏外、去掉 frontmatter / HTML 注释 / 链接文字 / 行内数学后的**句子**，以及**整条公式**（独占一行的展示块算一个单元，与公式轴共用同一分词口径）。短于 14 字（正文）/ 10 字（公式）的单元不参与——「用小写命名」「见下表」这类指路短语两两相似度天然高，算进去就是噪声。
- **两遍**：整单元完全相同走 EXACT（哈希分组，不设上限）；近似相同走 NEAR（倒排索引 + 字符 6-gram Jaccard，跳过被 25 个以上单元共享的热门 shingle 以控成本）。**为什么必须两遍**：NEAR 的热门剪枝恰好会在"一句话被 30 页抄"时把那 30 个副本全剪掉——探索版就照实读出了 0。EXACT 一遍兜住最该报警的那种重复。
- **范围剔除，每条都要有理由**：`00-index/`（更新日志按设计要引用页面原文）、`SUMMARY.md`（导航标签**必须**等于页标题，那是另一条轴 `check_nav_h1_sync.py` 规定的）、`参考资料` 与 `相关知识点` 两节（引文和互链本就重复）、链接文字（那是页标题不是正文）。

### 二、量到什么

| 桶 | 读数 | 处置 |
|---|---|---|
| 跨页**完全相同**的公式单元 | **6 条** | 全部改成指向，见第三节 |
| 跨页**完全相同**的正文单元 | 0 | — |
| 近重复带（0.72–0.85） | 3 条，最高 0.778 | 记 advisory 不判红，理由见第四节 |

全站读数：`pages=191 prose_units=7104 formula_units=274 dup=0 near-band(0.72-0.85)=3`（修复后）。

### 三、修法：指向，不是删除

目标里写着"不为凑指标删内容"，所以 6 处一律按同一个模式改：**本页留下自己的推理与结论，把定义式让给权威页，并就地解释这个指标对本页意味着什么**。

| 页 | 删掉的复述 | 页内现在怎么读 | 权威页（一字未动） |
|---|---|---|---|
| `03-llm/token-embedding-context.md` | KV bytes 展示块 | 「KV 缓存随长度线性增长（每 token 每层都要存一份 K 和 V；逐项符号与 GQA/MLA 的影响见 推理、量化与部署 的 KV 缓存公式）」 | `inference-quantization-deployment.md` |
| `03-llm/inference-quantization-deployment.md` | cost 基础式 | 「输入输出分别计价（基础式与符号见 Token、Embedding、上下文窗口 的成本公式），开启缓存后命中的输入部分按更低单价计」+ 本页自己的 cost′ 式 | `token-embedding-context.md` |
| `06-memory-rag/rag-basics.md` | Recall@k、MRR 两个展示块 | 两个指标各一句白话（捞回多少该捞的 / 第一条相关结果排第几）+「Recall@k 决定重排之前有没有料，MRR 决定喂给 LLM 的前几块有没有用」 | `10-evaluation-safety/evaluation-metrics.md` |
| `06-memory-rag/graphrag.md` | 模块度 Q 展示块 | 「模块度 Q 衡量社区内连接是否比随机更密，定义式与符号见 知识图谱」+ 本页对分层社区的解释 | `knowledge-graph.md` |
| `10-evaluation-safety/benchmarks.md` | pass@k 展示块 | 「跑 n 个样本、c 个通过，报告取 k 个至少中一个的无偏估计（定义式见 Agent 评估指标）」+「它衡量能力上限，单次通过率衡量稳定性，两者要分开报」 | `evaluation-metrics.md` |

- **断言级验证**：判据对同一棵树读数 **6 → 0**；公式轴 `pages=108 formulas=927 failures=0`（**928 → 927**）。两个数不矛盾：删了 6 处**跨页复述**，其中 4 处是展示块、同时为把话说清补了行内符号，逐页净变化 `-1 -1 -1 0 +2`。正文汉字 **326333 → 326481**（白话解释比公式源码长，方向与"不删内容"一致；这 148 字全部来自本轮 5 页正文改动，日志与 README 落笔后全站再升到 329138（含第七节的上线复验补记）——这条轴的绝对值每写一次日志就动，可引用的是差值）。
- **权威页一条公式都没少**：`knowledge-graph.md` 19→19、`evaluation-metrics.md` 29→29，实测在同一张表里。

### 四、留下的取舍：3 条近重复为什么不判红

剩的 3 条是 `14-templates/knowledge-template.md ↔ style-guide.md`（都在说「至少 1 张 Mermaid 或自绘 SVG 配图」）、`11-engineering/README.md ↔ logging-tracing-monitoring.md`（章索引页向读者预告该页要做什么）、`13-resources/README.md ↔ resource-template.md`（「一手来源优先」的收录标准）。最高 0.778，低于 0.85 的判红线。

- **章索引页与它引导的页**说同一件事，是**引导**不是灌水；**模板页与房规页**互引同一条要求，是这套规范的两个出口。把它们改到"彼此不像"会直接伤害可读性——所以留痕但不响。
- 这条线是**判出来的**不是猜的：阈值 0.85 之下、advisory 0.72 之上仍要打印，就是为了下一轮能看见自己站在哪儿。

### 五、这条轴自己骗了我两次：反例种错地方 = 假干净

真实页变异控制（拿 6 张已发布页复制到临时目录、种一句话再撤走，断言 `0 → 1 → 0`）第一次跑就"通过"了——**因为种的地方根本不进判据**：

1. 种在**文件末尾** → 落进被排除的「相关知识点」节 → 读数 0，看着像判据失灵，其实是我的反例没进射程。
2. 改成种在**第 1 行之后** → 落进 frontmatter → 还是 0。
3. 现在种在**页内第一个一级标题之下**，且没有一级标题就 `raise`。两次假干净都写进了入库判据的注释里，防止下一个人再踩。

另外三条判据内部的 bug 也是控制逼出来的：把两条相同单元同时喂进 NEAR 时 `findings` 读出 4 而不是 1（EXACT 与 NEAR 重复计数，现在 NEAR 跳过完全相同的对）；跨盘临时目录让 `os.path.relpath` 抛 `ValueError`；控制脚本的临时目录原本在 `tools/checks/` 里（一次宽口径 `git add` 就会把它提交进去），现在改用系统临时目录。

### 六、本轮复跑读数（离线轴全绿 + 真实渲染目检）

- 结构 `pages=198 problems=0`｜导航 `196 pages problems=0`｜组件配对 `198/0`｜引用逐字回核 `197 页 5 引 unmatched=0`｜汉字 `prose CJK=329138 findings=0`（写日志前的 5 页净读数是 326481，见第三节）｜更新日志条目标题 `HEAD=52 tree=52 lost=0`｜公式轴见第三节｜README 统计 10 条轴全 ok。
- **Mermaid 几何**（本轮没动图，这是回归闸）：`authored=217 rendered=217/217 max width=1116px（列宽 1120）problems=0`，引擎对齐 `local=11.14.0 live=11.14.0`，两张埋雷照响（2420px 超宽 + 残缺语法）。
- **真实渲染目检**：无头 Edge 在本沙箱拿不到外部网络，线上截图做不了；改用**本地真引擎整段渲染**——把本轮 5 页被改的 7 个小节按 GitBook 正文列宽（1120px）排版，22 处数学全部过**同一份钉住的 katex@0.18.7** `renderToString(throwOnError)`，截图逐节看过：删掉复述式后小节仍读得出完整论证，指向链接落点正确，留下的公式（KV bytes、cost′、O(n²d)、Resolved）斜体与分式正常。这条腿也带正控制：埋一个真 KaTeX 错误必须抛，否则"22 条都渲染了"和"一条都没渲染"读数一样。
- **仍未了结**：第 59 轮那个记录发布节奏的小提交 `b7122cf` 到本轮开跑（约 26 分钟后）线上更新日志页仍是上一份 `b153628`。用一次性归因探针分清了两件事：抓取与解析正常（同页控制针在、字节数稳定），三枚新指针全缺 → **发布滞后，不是内容缺陷**。与第 59 轮记下的「分钟级到 75 分钟级都出现过」一致。本轮提交后继续复验（结果见第七节：两枚遗留针与本轮三枚针一起命中）。

### 七、上线复验（本轮闭环，顺带关闭上一轮的遗留项）

推送 `ef93a5f` 后**约 90 秒**，两页探针全绿：

- **更新日志页**：本轮 3 枚针 + 第 59 轮遗留的 2 枚 `b7122cf` 针**全部命中**，页面字节 `8,359,647 → 8,931,085`。上一节那句"仍未了结"到此关闭：`b7122cf` 不是没发布，是发得慢。
- **`rag-basics` 页**：本轮新写的 2 枚针命中，同页旧控制针在（能区分"没同步"与"没抓到"）。
- **全站 SSR 对平轴复跑**：`authored=174 checked=174 problems=0 fetch-failures=0 fallback-pages=0`。
- **5 张被改页逐页线上抽查**：本轮新句都在**读者可见正文**里、`aria-busy` 空公式占位 0、裸定界符 0、裸 GitBook 标记 0；并且本轮写下的 5 个指向都解析成**真实已发布 slug**（`…/03-llm-ji-chu/token-embedding-context`、`…/10-ping-gu-an-quan-yu-dui-qi/evaluation-metrics`、`…/06-ji-yi-yu-rag/knowledge-graph` 等）——指向改法最怕的就是链接落点错，这条单独量。
- **这条腿也带正控制**：把第 59 轮实测到的那串缺陷签名（空公式占位 + 裸定界符 + 裸标记）喂进同一个抽取路径，三项必须分别读到 1 / >0 / True，一张健康页必须读 0 / 0 / False。第一版控制把"裸定界符"断言成等于 1，实测读到 **2**——这个计数数的是**出现次数**，一对就是 2。改的是判据口径（写进注释），不是内容。
- **发布滞后不能排程**：同一份 `b7122cf` 在 26 分钟前还读不到，本轮 90 秒就全量命中。观测过的间隔是 53 秒 / 3–4 分钟 / 26 分钟 / 75 分钟——所以"上线后抽查"每轮都得实测，按经验等几分钟会读到假的红或假的绿。

### 八、待操作者拍板（本轮不动）

1. 双层图注（45 处图片放置里，图注与引导语并存时的主次）是否合并成一套口径。
2. 是否补一条「线上正文完整性」轴（把本地正文与线上可见文本逐节对平，专门抓第 59 轮那类"内容被吞"）。
3. 早前贴进对话的 GitHub PAT 仍需撤销/轮换；仓库与提交里都没有它。

## 2026-09-23（第 59 次）四条都是**尺子自己**的问题：一句写进本页的话里有转义反引号，它会让中间那句话从页面上消失，而线上两条轴都不响；另一条判据能拿**错的引擎**报出 0 失败；第三条是本轮提交**自己吃掉了上一轮的条目标题**，而 198 页结构轴照绿；第四条是一个计数同时装了"内容有问题"和"网络抖了一下"，于是这条轴的干净 0 近乎读不到

本轮**知识正文零改动**，动文字的地方只有本页与 `README.md` 的表述；新增 `check_structure.py` 的 BT 判据一条，改掉 SSR 轴的一句提示，并把公式判据的 KaTeX 版本钉进仓库。

### 一、发现：SSR 轴的"作者侧那半"响了一声，响在我自己刚写下的句子

按流程复跑 `live_aria_manifest.py --all --headless` 收第 58 次的尾，读数 `authored=174 checked=169 problems=6`：其中 5 条是 `FETCH ... The read operation timed out (attempt 2)`（瞬时 TLS/超时，复跑即清，与第 58 次第四节那 4 条同类），另 1 条是 `FORMULA 00-index/changelog.md: unpaired $$ inside one paragraph`。

- **它报的段落里看不见定界符**——因为判据先把行内代码剥掉了，而它引的是**整段**（bullet 列表不分空行就算一段），病灶在紧随其后的那一行。定位靠通读那一节三行，不靠读数。
- 病灶就是上一轮那句「修法」（原文如下，围栏里才敢这么印）：

```markdown
- **修法**：改写那 2 个标题（`字面 \`$$\`` → 「字面定界符」；`嵌套 \`$$\`` → 「嵌套了定界符」）。
```

想在一个行内代码里再印一次行内代码，于是给反引号加了反斜杠。**CommonMark 里反斜杠 escape 不了代码跨度内的定界符**，跨度在第一个反引号处就闭合了。

### 二、它到底坏成什么样：三个说法摆在一起，只有一手 HTML 算数

| 谁的说法 | 内容 | 证据 |
|---|---|---|
| 我写那句时以为的 | 读者会看到裸的定界符 | 推的，没测 |
| 作者侧判据说的 | 一段里出现了落单的 `$$` | 分词器读数，对但不够 |
| **线上真正吐出来的** | `<code>` 里只剩「字面 \」（反斜杠原样交给读者）；被丢下的两个 `$$` 把**中间那句**「→ 「字面定界符」；」当成公式，SSR 只留一个**空的** `<span aria-busy="true">`；读者可见文本于是变成「修法：改写那 2 个标题（ `` → 「嵌套了定界符」）。」——**句子的前半没了**，还多出两个裸反引号 | 抓取 `f7f8442` 发布后的更新日志页，逐字节比对 |

- **所以症状是「内容被吞」，不是「标记裸露」**。第 57 轮量到的「变量丢数学斜体」是同一机制的轻症，本轮是重症：吞掉的是一整小句。
- **线上两条轴都看不见它**：同页 HTML 里 `$$` 共 **184** 处，读者可见正文 **0** 处，所以 LEAK 不响；那个空占位让页面**少**一个 `katex` 节点而不是多一个，计数对平也不响。这类缺陷目前只有作者侧的分词器能拦住——本轮把它从"偶尔手跑"变成常驻判据的第三条规则。
- 时间线说清楚：缺陷随 `f7f8442` 于 01:35 推送、约 01:41 被作者侧判据捉住、01:46 抓取确认已在发布页上，修复随本轮推送。它**上过线约十几分钟**。

### 三、修与闸

- 那一行改写为不含转义反引号、也不含裸定界符的说法（「把定界符写成了行内代码——正文那一份看着是代码，目录那一份是裸标记」），原意一字未减。
- `check_structure.py` 新增 **BT 判据**：围栏外的行含转义反引号即报，消息写明机制（跨度提前闭合 → 丢下的定界符配成空公式 → 中间文字消失），并注明这是**只有作者侧看得见**的一类。反例成对：同样的写法出现在围栏内必须不响（房风格页里那些示例写法不能被误伤）。
- **断言级验证**：拿**已提交的上一版**本页跑，BT 计数 **1 → 0**、作者侧 FORMULA **1 → 0**，两条都是 `assert`，不响就 `AssertionError`；全站 `check_structure pages scanned=198 problems=0`。
- 全站扫这个写法**只有 1 处**（`count=1`），不是普遍病灶——但一次就够毁掉一句话。
- SSR 轴那句提示从 `unpaired $$ inside one paragraph` 补成「KaTeX 会把它和页内下一个定界符配成一对，中间那句渲染成空公式」，让下一个人不必再自己推一遍。

### 四、同一轮的第二条：**公式判据能拿错的引擎报出 0 失败**

第 58 次把这条判据落进仓库时，落的是脚本，没落它的依赖。

- 复跑 `check_katex_formulas.py` 第一次就 `SKIPPED — Cannot find module 'katex'`。用 `--katex-dir` 指到临时目录里那份旧 bundle 才跑出数：`pages=108 formulas=928 failures=0`，**版本 0.16.47**——而 README 引的是 `katex@0.18.7`。
- **这条为什么不能照 Mermaid 轴那样"与线上对齐"**（一手测量）：抓已发布页 `03-llm-ji-chu/transformer-attention` 的整页 HTML，`katex` 只出现在类名 `katex` / `katex-display` / `katex-html` / `katex-mathml` 里，`katex\d+\.\d+\.\d+` 与 asset URL 两种模式**都是 0 命中**——站点根本不吐版本号，没有可断言的对象。
- 于是退到能做到的那一档：**钉住本地版本**。`KATEX_VERSION = "0.18.7"`，依赖装到 `tools/checks/data/katex/`（`package.json` 入库、`node_modules/` 进 `.gitignore`），解析到的版本不等于钉住的那个就 `exit 2` 且**不出数**。
- 反例照跑：`--katex-dir` 指向那份 0.16.47 → `OFF-VERSION — … Not emitting numbers`，退出码 2；不带参数 → `pages=108 formulas=928 failures=0 version=0.18.7`，埋雷照响（planted counterexample caught: 1）。
- 读数与第 57、58 次一致（108 页 / 928 条），这次那个旧引擎**恰好**没改变结论——但"恰好"不是判据，缺依赖也不是：README 说一条判据可复跑，就得连它的引擎一起可复跑。

### 五、本轮复跑读数（离线轴全绿）

- `check_structure pages scanned=198 problems=0`——含本轮新增的 BT 判据与它的两条反例（围栏外必响 / 围栏内必不响）；`check_nav_h1_sync 196 页 0`；`check_readme_stats 全轴一致`；`check_widget_pairing 198 页 0`；`check_quote_fidelity 197 页 / 5 条引用 / 0 未匹配`；`check_char_sanity 326333 字 0`；`check_katex_formulas 108 页 / 928 条 / 0 失败 / version=0.18.7`（埋雷照响）；`check_mermaid_geometry 217 块真渲染 problems=0`，最宽 1116px、最高 1689px。
- **真实渲染图目检**：`--eyeball 12-applications/README.md`（全站最宽的那一张，1116×94）出 28 KB PNG——5 节横链、章色紫、中文标签两行都完整无截断、箭头不断。
- 作者侧公式判据：本页 **1 → 0**（同一份文本，改前响、改后不响，两条都是 `assert`）。线上 SSR 对平轴的复跑读数见第八节，旧渲染最终翻转的读数见第九节。

### 六、留给你的取舍

要不要再补一条**线上正文完整性**轴（作者每个段落取前若干字，必须在读者可见文本里找到）。它能兜住这一整类"被平台吃掉"的缺陷（公式吞句、组件吞正文），但 GitBook 对列表与提示卡的改写会让分段对不齐，误报面比现有几条轴大得多。本轮先用作者侧 BT + FORMULA 两道闸兜住，这条重轴做不做由你定。

### 七、收尾时抓到第三条：本轮提交**自己**把上一轮的条目标题吃掉了

- **症状**：写完 59、准备落库时才发现，第 58 次的整段正文还在，它的**条目标题没了**——第 58 次就这样挂在第 59 次的标题底下，本页目录也少一条。git 能指认凶手：`83b0240` 有、`f7f8442` 有、`d9c2388`（本轮提交）没有。**就是我这次新增条目的编辑吃掉的**。
- **为什么所有轴都不响**：第 53 次留过一条同一坑的备忘——"每轮把标题集合与 HEAD 比一次"。它是**习惯**，不是**代码**，于是这一轮就忘了。而"条目编号必须连续"这种看起来更聪明的判据也兜不住：全站实测编号本来就有 8 个洞（36/39/41/43/45/46/49/50 没有条目，那几轮做了事没写日志），把"连续"做成硬判据会得到 8 条假警报，然后有人把它关掉。
- **落库的判据** `tools/checks/check_changelog_headings.py`：拿 HEAD 里那份本页的 `## ` 标题集合与工作区比，**只报"HEAD 有、工作区没了"**，编号不连续一律不响。三条常驻反例（吃掉中间一条 / 原样不动 / 尾部整条删掉）+ 一条假警报反例（编号有洞必须读成干净）+ 空判下限（HEAD 少于 40 条标题就是比对失效）。
- **真实数据上的两条腿**：`git show HEAD~1` 对 `git show HEAD` → **1 条丢失**（正是第 58 次那条，标题原文照抄进报告）；同一份 HEAD~1 对修好的工作区 → **0**。补回的第 58 次标题是从 git 里逐字节取回的，不是我重新打一遍的——重写就会把第 58 次的标题改成另一个样子，那才是二次事故。
- **判据自己也坏了一次**：第一版把整篇正文当标题列表喂进去，反例当场响（读到 6 条"丢失"）。这就是反例留在判据内部的意义：它响在我写完之后、上线之前。

### 八、线上同步补记（推送之后）

- **推送与落地**：`f7f8442..d9c2388` 经 SSH 推出，`git ls-remote` 与本地 HEAD 逐字节相同（10:01）。
- **全站已翻到新修订，唯独这一页没有**。判据不是"过几分钟再看"，而是**两条只在新修订里存在的字串**：门面页（README 那条新规矩）读者可见正文里能查到，**证明第 59 次已经发布**；本页读者可见正文里查不到本轮标题，`7,432,401` 字节的旧文档 11 次轮询 + 5 种 URL 取法（原样 / 末尾斜杠 / 加 `.html` / 带 `?cb=<时间戳>` / 带 `?html=1`）**每次都逐字节一样**，且本轮要修的那处空公式（写在第 58 次条目里的）仍在：空公式占位 1、读者可见正文里裸定界符 0。查询参数不改缓存键，说明这是平台侧按路径钉住的一份旧渲染，不是我这边的代理缓存。
- **因此本轮的诚实结论**：修好的句子**已经在源里、发布通道也走过，但这一页读者暂时还看不到**。全站只有这一页这样；我量到的次大一页是门面页 1.64 MB（相差 4.5 倍，只比了这两页，不是全站排序）。这是**观察到的相关性，不是证到的因果**，我不把"页面太大所以不重建"写成结论。
- **`.md` 端点 10 分钟前就翻新了，HTML 60 分钟没动**：所以"抓 `.md` 看到新内容"只能证明 GitBook **拉到了提交**，证明不了读者看到了。这条已写进门面规矩，今后任何一轮都不能拿 `.md` 当"已上线"。
- **SSR 对平轴复跑**：`authored=174 checked=170 problems=4`——4 条**全是 FETCH 超时**（tree-of-thoughts、agent-to-robot-bridge、memory-compression-forgetting、enterprise-knowledge-base，都是 attempt 2 的瞬时读超时，历史上重跑即恢复），**0 条内容问题**；`fallback-pages=0`。要读到一次干净的 0，需在旧页翻转后复跑。

### 九、旧渲染翻了：第八节记下的那页，第二次推送后**第一次抓就中**

- **时间线**：`d9c2388` 于 10:01 推出后，那份旧文档被逐字节重复了 11 次轮询 / 75 分钟；随后 `f7f8442..d9c2388` 之上的第二次推送（`a9024bf`，补回第 58 次标题 + 新增判据）落地，11:22:57（本地，与第八节同一时钟）抓一次即命中新修订。所以第八节那句"这一页读者暂时还看不到"已被本轮自己的后续动作推翻——**它描述的是当时的观测，不是永久状态**，我留着原文不改，只在此处记翻转。
- **命中判据是字串，不是"看着像新的"**：只存在于 `a9024bf` 的三处（本轮新标题「三条都是」、第七节「自己吃掉了上一轮的条目标题」、第八节「线上同步补记」）在**读者可见正文**里全部为真；被吃掉的第 58 次标题（「上一轮把公式判据落了库」）也回到可见正文里——线上目录不再少一条。（这三处是**当时那一份**修订的判据；本节第四条把标题从"三条"改成"四条"，所以下一次线上翻转要查的字串变成「四条都是」+「旧渲染翻了」。）
- **本轮那处空公式在线上确已消失**：`aria-busy="true"></span>` 占位 **1 → 0**，HTML 里 `$$` 203 处、读者可见正文里 **0** 处（203 是 `a9024bf` 那一份的读数，含本节引用缺陷标记本身）。这条是前三条里唯一需要线上抽查才能收口的一条。
- **代价**：同一页旧文档 7,432,401 B、新文档 8,252,771 B。第八节说的"只比了两页、相关性不是因果"仍然成立，本轮没有新增证据，不升级成结论。
- **复跑抓出第四条尺子问题：`problems` 一个计数装了两类事**。第一次复跑读 `authored=174 checked=170 problems=4`，第二次读 `problems=3`、页面集合还不一样，**两次的内容级发现都是 0**——那几条全是读超时。也就是说"3 个问题"和"网络抖了 3 次"共用一个数字，`problems=0` 在这个链路上近乎读不到，下一轮就会有人去"修"噪声。修法是把两类发现分桶（`tally()`）：`problems` 只装 SSR-PARITY / LEAK / LEAK-NAV / SHAPE / FORMULA，超时另计 `fetch-failures`；**退出码仍然两桶任一非空即 1**（没抓到的页面什么都没证明，不能算绿），但读数可归因了。四条反例进常驻 controls：抖动的 fetch 不得进内容桶、真的对不平不得躲进 fetch 桶、匹配页必须 checked 且两桶皆空、缩水页留在内容桶。
- **分桶后的干净读数（本轮收口）**：`authored=174 checked=174 problems=0 fetch-failures=0 fallback-pages=0`、退出码 0——这条轴**第一次**以"0 内容问题 + 0 未检页"的形式成立；第八节里"要读到一次干净的 0，需在旧页翻转后复跑"那条待办就此了结。
- **抽查里有一条判据读成 `false`，先归因再收口**：抓线上时"只存在于新修订"的三条里，两条纯文本命中的都对（「四条都是」「旧渲染翻了」），但**写在行内代码里**的那条读数串恒不命中。逐字定位后确认它是**提取器的语义**不是页面的缺失：`body_visible()` 会整段剥掉 `<code>`（第 57 轮定的规矩——代码跨度里的 `{%`、`$$` 是文档示例，不是读者看到的泄漏，LEAK 判据靠它才不误报），所以**任何放在行内代码里的字串都不可能出现在"读者可见正文"里**。线上 HTML 原文里这条读数是完整的（`…hyphens-none">authored=174 checked=174 problems=0 fetch-failures=0 fallback-pages=0</code>`）。教训：往后线上门槛字串要挑正文里的，别挑代码里的——这一条已同步进项目备忘。
- **线上收口读数**：新修订第一抓即命中，`aria-busy` 空公式占位 **0**、读者可见正文裸 `$$` **0**，第 58 次条目标题在正文里。
- **本节这条补充自己也是被同一把尺子量的**：推出 `b153628` 后第一抓（11:49:55）仍是 `67f58a4` 那份（8,332,592 B），53 秒后第二抓（11:50:48）已是新文档（8,359,647 B）——本轮的线上门槛字串全部改挑正文里的散文，两条都命中，空公式占位仍 0。所以"旧渲染卡住"的实测节奏是**分钟级到 75 分钟级都出现过**，报"平台没同步"之前至少要跨分钟再抓一次。







## 2026-09-23（第 58 次）把 README 挂在嘴边、却**只存在于聊天记录里**的另外两条判据落进仓库：**线上图片健康**与 **Mermaid 自然宽度**。两条轴跑完全站都是 **0 问题**，所以本轮**一行正文没改**——但落库本身抓出了三件真事：一句 README 的说法只有半对（第一节末）、一把尺子的"0"可以来自四个不同的坏法（第二节）、以及**第一个埋雷反例自己不会撑宽**（第三节）
上一轮把公式判据落了库，本轮按同一套路继续清"README 引用了但仓库里找不到脚本"的宣称。剩下两条：图片（"每页有图、图都打得开"）与几何（"217 张图与线上同版本实测，最宽 1116px"）。

### 一、线上图片轴 `tools/checks/check_live_images.py`：`pages=36 refs=45 唯一资产=40（32 SVG + 8 PNG）problems=0`

- **为什么"文件在磁盘上"不算数**：GitBook 把 `![](.gitbook/assets/x.svg)` 改写成 `~gitbook/image?url=<代理>&sign=<签名>`。本地文件完好无损，线上照样可以 404、返回 HTML 错误页、返回 0 字节；反过来一次陈旧发布也能端出源码里已经删掉的图。两头此前都没人量过。
- **四类判定 + 两条常驻反例**：`DROPPED`（作者写了、页面没有对应 `<img>`）、`EXTRA`（页面多出一张源码没要的）、`NOCAPTION`（alt 没作为可见文字落到页面）、`BROKEN`（非 200 / 非 `image/*` / 小于 200B），外加 `RASTERIZED`（自绘 SVG 被代理成位图——它打得开，所以别的判据看不见动画没了）。
- **平台事实是量出来的，不是猜的**，每一条都曾让探针自己误判：`.md` 端点给的是 Markdown（10 KB）、浏览器 URL 给的是 HTML（1.7 MB），抓错就把 45 张全读成 DROPPED；正文图片是 `<img data-testid="zoom-image">`，站点顶栏另塞 4 枚 `<img alt="Logo">`，直接数 `<img>` 恒多 4；`src` 是实体编码的（`&amp;sign=`），原样请求返回 **HTTP 400**，必须先 `html.unescape`，且资产名在 `url=` 里被**双重 percent-encode**，要解两次。
- **绿色是买来的**：`live_mutation_control()` 拿真实页面（`05-tool-protocol/mcp.md`）的线上 `<img>` 集合，把**作者侧**改坏——多要一张不存在的、少要一张线上真有的、抹掉图注——要求 `EXTRA + DROPPED + NOCAPTION` 三条同时响。不响就是尺子坏了。
- **顺带纠正 README 里半句话**：原文写「GitBook 会剥掉内容图片的 alt」。属性确实被剥（线上是 `alt=""`），但作者写的 alt 会以 `<figcaption class="text-xs text-center …">` **印在图下方**。所以"每张图另写一句可见图注"的规矩不变（我们 alt 与图注都有），理由要改对——README 已按实测改写。
- **本轮未做的取舍**：alt 与正文里那句斜体《图：…》引导在页面上是**两层**（figcaption 一行 + 引导语一段），信息重复但一薄一厚。合并成一层会改变全站 45 处配图的视觉密度，属版式级决定，留给操作者。

### 二、几何轴 `tools/checks/check_mermaid_geometry.py`：`217/217 真渲染、0 失败、最宽 1116px`，README 第 21 轮起的数字**第一次被复现**

- **对齐先于读数**：本地 bundle 自报版本必须等于线上页面 `<script>` 里加载的版本（从已发布 markup 正则读出 `mermaid@11.14.0`）。不等就 `exit 2` 不出数——第 15 轮整轮报废就是因为本地 12.0.0 与线上 11.14.0 对未连接子图的布局判断不同，"0 超宽"量在了错的引擎上。
- **读数**：`authored=217 blocks / 172 pages`（与 README 的 217 逐一对上）、`rendered=217/217`、`max width=1116px`（并列在 `12-applications/README` 与 `18-frontier-2026/openai-agents-api`）、`max height=1689px`（`16-ai-infrastructure/agent-runtime-durable-execution`#2）。**判宽不判高**：超宽会被 GitBook 缩放到标签不可读，超高只多滚一段。
- **真实渲染目检**（本轮的图证）：`--eyeball 04-prompt-reasoning/structured-output.md` 出一张 86 KB PNG，3 张图章色正确、中文标签无截断、TD 长链完整。这条路径今后任何一轮都能重跑，不依赖截图工具。

### 三、这把尺子落地时坏了四次，**每一次都是"读数不可能"暴露的**，没有一次靠肉眼

| # | 症状 | 根因 | 为什么没被当成内容缺陷 |
|---|---|---|---|
| 1 | 40 块的 fixture `--dump-dom` 回吐 3.2 MB 源码、只 2 个 `<svg>`、无完成标记 | `--virtual-time-budget` 会**快进 pending 定时器**，每块的 20s 看门狗都在吃虚拟时间 | — |
| 2 | 去掉虚拟预算后 **0 条报告** | 无头 Chrome 在文档 load 完就退出，async 渲染循环不算 load。解法：页面末尾拉一个服务器**故意不响应**的 `<script src="/hold?rid=N">`，报告到达才放行 | — |
| 3 | 仍然 0 条报告，控制台 `Uncaught SyntaxError` | 生成的 JS 多了一个 `}` | 若把"没报告"读成"宽度 0"，会误报 217 张全坏；判据写的是**报告条数≠块数就 raise**，于是它响成一次工具故障 |
| 4 | `AttributeError` 打在服务器线程里 | 邮箱/闩挂在包装类上，请求线程只看得到 `self.server` | 同上，异常被吞就会退回"0 条报告" |

修好后 **40 块 3.7 秒**，全站 217 块 + 2 张埋雷一次跑完 **51 秒**（含一次向线上页面取引擎版本）。

- **第一个埋雷反例是错的，被自己的反例机制抓住**：原设计用 6 路 `&` 扇出撑宽，实测只有 **556px**——扇出被 mermaid 折成了两列，撑不开。`CONTROL-DEAD` 判定当场报"埋进去的超宽图没有超过 1120"。换成 8 节 LR 长链后 **2420px**，`OVERWIDE` 正常触发。**"0 问题"如果没有任何东西会响，它就只是 0。**
- 另一张埋雷（`graph TD` 里写残缺的 `A[起点] -->`）必须被捉为 `FAILED`，实测捉到并带 mermaid 原始 `Parse error on line 4` 摘要。

### 四、收尾复跑线上对平轴时抓到 1 条真缺陷：**标题里的标记会被目录裸印出来**

推送后按流程复跑 `live_aria_manifest.py --all --headless`（第 56 轮那条 SSR 轴），`authored=174 checked=174 problems=1`。

- **读数本身要先过滤噪声**：第一次跑报 5 条，其中 4 条是 `FETCH ... read operation timed out`——第二次跑全部拉到，属瞬时 TLS/超时，不是内容缺陷；剩 1 条是真的。
- **真缺陷**：`LEAK 00-index/changelog.md serves literal $$`。定位后机制很清楚——GitBook 把**每个标题的文本再印一遍**放进侧栏与「本页目录」，那一份**不带行内代码格式**。所以第 57 轮那条「症状不是『读者看到字面 `$$`』」的标题，正文里看着是代码，**目录里读者看到裸 `$$`**。该页 HTML 里 `$$` 共 177 处，剥掉 `<code>`/`<annotation>` 后只剩 2 处，且两处都在目录副本里。
- **修法**：那 2 个标题把定界符写成了行内代码——正文那一份看着是代码，目录那一份是裸标记。改写后标题只留中文：「字面定界符」「嵌套了定界符」。**正文一字未删**，精确写法仍留在节内的代码示例里；离线复跑该判据 **2 → 0**。

### 五、这条读数是尺子先坏了一次才看见的

同一轮里 SSR 轴的消息把目录副本说成「一条解析器没吃下的公式」——**症状描述错了**，与第 57 轮被推翻的那句话同一类。修判据时连续踩两条：

| # | 试过的规则 | 实测结果 |
|---|---|---|
| 1 | 按 `<li class="*sidebar-list*">` 整块剥目录 | 顶层目录条目的 `<li>` **没有** sidebar 类（类在它的孩子 `<a>` 上），177→2 里只剥掉 1 处，剩下的那处被读成「正文里的裸公式」 |
| 2 | 改按 `<a href="#...">` 剥（目录与标题自锚都是页内锚） | 第一次写的正则要求 `href` 是标签里**最后一个**属性，全站 **0 命中**——GitBook 在 `href` 后面还挂了 `class`/`data-*` |
| 3 | 最终：`<a ... href="#...">…</a>` 任意位置命中 | 更新日志页锚点 166 个、剥掉 4607 字（都是标题副本）；MCP 页 40 个、剥 298 字、无泄漏；那条 LEAK 改判为 `LEAK-NAV`，**只在正文出现时**才叫「解析器没吃下的公式」 |

判据带的反例：目录副本必须判成 nav（不得算正文泄漏）、同一页正文里真泄漏必须仍判 body、代码跨度内的标记必须两头都不响、跨页链接 `<a href="../other#x">` 不得被当目录剥掉；任何一条不响就是 `AssertionError`，不会静默出数。

- **离线侧补了同一道闸**：`check_structure.py` 新增 HEAD 判据——围栏外的标题行含 `{%`/`%}`/`$$` 即报。拿**已提交的旧版**更新日志验：正好响 2 条（就是这 2 个标题）；改后 198 页 `problems=0`。这样同类写法下一轮不必等线上发布才看得见。
- README 新增一条「标题里没有会被当成标记的符号」，把机制、线上读数与离线判据写在一起。

### 六、复跑与未做项

- 离线轴全绿：`check_structure 198 页 problems=0`（含本轮新增的 HEAD 标题判据）、`check_nav_h1_sync 196 页 0`、`check_readme_stats 全轴一致`、`check_widget_pairing 198 页 0`、`check_quote_fidelity 5 条引用 0 未匹配`、`check_char_sanity 319930 字 0`、`check_katex_formulas 108 页 / 928 条 / 0 失败`（埋雷 1 条照响）。
- **知识正文零改动**：本轮动过文字的地方只有本页（第 57 轮的 2 个标题按第五节的机制改写）与 `README.md` 的表述；新增两个 `tools/checks/` 脚本，另在既有两个判据脚本里加规则。
- 仍未做：浏览器内实时截图（沙箱里无头 Edge 无外网，线上侧改用 SSR 抓取 + 图片代理直连）、双层图注是否合并（见第一节）、`git push` 用的 PAT 轮换。


## 2026-09-23（第 57 次）把上一轮的「结构对平」轴**从 7 页扩到全站 174 页且不需要浏览器**：读数 problems=10 → **0**；并第一次把 README 挂在嘴边却从未入库的**公式判据脚本落进仓库**。收尾复跑时**推翻了自己本轮开头的一句话**：那 2 处公式缺陷的症状不是「读者看到字面定界符」，实测是「变量丢了数学斜体」（第二节末）

第 56 轮那条轴只跑到 7 页，因为它假设「线上 DOM 只有浏览器能碰」。本轮没有先去做浏览器的事，而是先去量**服务端吐的 HTML 里到底有没有这两个结构**——结果两条等式（标签页、公式）在 SSR 阶段就已经等于作者写法，于是全站审计变成一次 urllib 抓取。扩覆盖的收益不是数字好看，是它**当场抓出 10 条**。

### 一、全站 SSR 对平：`authored=175 checked=172 problems=10` → `authored=174 checked=174 problems=0`

那 10 条按性质拆成三堆，**只有第一堆该改内容**：

| 堆 | 条数 | 内容 | 处置 |
|---|---|---|---|
| 作者写法错 | 2 | 展示块里嵌套 `$$x$$`：`communication-protocol` 与 `prompt-injection` 各一处。症状见第二节——**不是**「读者看到美元符号」，而是变量丢掉数学斜体 | **改内容** + 给判据加 NESTED 类 |
| 尺子自己的口径错 | 5 | README 1/0、changelog 23/10、3 条 LEAK 假警报 | **先改尺子**，一条正文没动 |
| 探针抖动 | 3 | SSL `UNEXPECTED_EOF`（并发抓取掉连接） | 加一次重试，失败仍记为发现而非跳过 |

- **上面那 2 条的「计数差」也是口径错**（所以它们同时属于前两堆）：报出来的是 `authored=14 served=13`，而 14 是**旧尺子**把嵌套的 `$$n$$` 数成了第 14 条公式。新分词器跑同一份**旧文本**得 13，与线上 13 一致——写法该改，但那条 PARITY 差值本身不是内容缺陷。

- **公式页 175 → 174 不是掉页**：README 首页那 1 条「公式」是它**用行内代码引用的 `$$…$$` 写法本身**，剥掉行内代码后它一个公式都没有——旧尺子把「介绍语法的例子」当成了语法。
- **5 处 SSR 数不对里 3 处是 LEAK 假警报**，根因各不相同：更新日志在**代码跨度里引用** `{% hint %}`；另一页的公式写了 `95\%`，KaTeX 把自己的 TeX 源放进**隐藏的 `<annotation>` 节点**，于是 `%}` 出现在源码里而读者看到的是「95%」。修法：可见性判定统一剥 `code/pre/script/style/annotation`，浏览器探针与 SSR 两条路用同一条规则（探针同时补上 `$$` 这条泄漏检测）。

### 二、抓出来的 2 条写法错：展示公式里嵌套了定界符——**它的症状本节先写错、后改对，改对的过程就是量测**

- **它长什么样**：`$$` 展示块内部又写了一对 `$$n$$`（想强调「n」）。展示块的两个定界符之间**只算一条公式**，所以里面那对不会开启新公式；剩下的问题是渲染器怎么处置它。
- **⚠️ 本节初稿写的是「线上渲染出的文字里原样留着 `$$n$$`」——那句话不成立，本轮撤回。** 它是我从配对规则**推**出来的，不是量出来的。收尾复跑时量了三件事（用**平台同款 KaTeX 0.18.7**，不是我以为的行为）：
  - 把两页的**旧版本源码**（`git show HEAD~1:docs/…`）喂进共用分词器 → `旧文本公式数=13`、`19`，各带 **1 条 NESTED**。**旧文本的 13 与线上当时报的 served=13 相同**，说明平台并没有「提前收尾把残骸吐成正文」；那条 `authored=14` 是旧尺子多算的（见第一节那条）。
  - 用真 KaTeX 分别渲染新旧两块，剥掉标签后数 `$`：旧块 **0 个**、新块 **0 个**；正控制项 `\text{成本 }\$50` 数出 **2 个**（证明计数器打得着，0 不是量具坏了）。→ **美元符号被 `\text{}` 静默吞掉**，读者看不到它。
  - 但确实有一处读者可见的差别：`<mi>` 数学原子数 **旧 2 / 新 3**（两页同此）。旧写法把 `n`、`D` 关进了 `\text{}`，屏幕上那是**正文字体的 n**，不是数学斜体的 *n*——数学排版里正/斜体是有语义的（变量该斜体），所以这仍是要改的缺陷，只是**严重度是排印级，不是「满屏乱码」级**。
- **修法两头都做**：内容侧把 `\text{$$n$$ 一大就不可维护}` 改成 `n\text{ 一大就不可维护}`（斜体 n 回到数学态，汉字留在 `\text{}` 里），另一处同理改成 `D\text{ 中的指令}`；判据侧新增 NESTED 类，并且**分词器改成平台的规则**（见第三节），于是这条轴今后能在**离线**抓住它。
- **红→绿是量出来的**：同一把尺子跑 `HEAD` 版本的这两个文件 → `findings=2`（两条 NESTED，逐条点名到行）；跑修完的工作区 → **0**。推送并同步后再量**线上**（URL 全部经 `llms.txt` 索引解析，不猜）：`authored=13 served-katex=13`、`authored=19 served=19`，可见正文里字面 `$$` **0 处**、`katex-error` 节点 **0 个**，且改好的 LaTeX 源已出现在线上 `.md` 端点上——四项断言全过。

### 三、把「作者写了几个公式」按**平台真实分词规则**重写（本轮最值钱的一条）

旧写法是「数全文 `$$` 出现次数除以 2」。三条实测把它推翻，每条都留下一个可执行控制项：

1. **围栏与行内代码里的写法示例不算**——README 的 1/0、更新日志的 23/10 全由此来。
2. **行内代码要用 CommonMark 的反引号跨度剥，不能用惰性正则**：更新日志会写 ` ```text 块 ` 这种**本行不闭合**的反引号串，`[^`]*` 会一路吃掉到下一个反引号，把隔壁真正的定界符也吞了，于是整段变成「落单」。新剥法按「等长反引号串才闭合」实现，未闭合者留作字面文本。
3. **`$$` 在**同一段落内**配对**，不是全页。更新日志里那段引号密度最高，全页配对会让每个引用的 `$$` 翻转后续奇偶性——这就是 `authored=11 served=10` 的真相。改成段内配对后：该页 10 = 10，而**任何一段留下落单定界符都会单独报一条**（第 53 轮那条收尾 `$$` 没独占一行的 bug 正属于这一类）。

顺带纠一个我自己写错的判据：`^` 开头的标签页正则**漏了 `re.M`**，导致多行页面数出 `tabs=0`。是**控制项当场把它撞红的**（不是我看出来的），这也再次说明「先有能失败的控制项，再谈绿灯可信」。

### 四、公式判据落库：README 引用的那把尺子此前**不在仓库里**

- README 第 89 行写着「公式数**只认这一个判据脚本**」，而那个脚本从第 52 轮到今天**每次都是临时目录里现写、用完蒸发**——这正是同一棵树读出 811 / 821 / 834 的根因。本轮把它落成 `tools/checks/check_katex_formulas.py` + `katex_render.mjs`，并且**复用第三节那一个分词器**（`formula_sources()`），使「离线数几条」与「线上对平几个」不可能再各说各话。
- **全站读数**：`katex render: pages=108 formulas=928 failures=0 version=0.18.7 (planted counterexample caught: 1)`；不含更新日志口径 **107 页 / 918 条**。README 由 **930 → 928**（少掉的 2 条就是第二节那两处嵌套写法：旧尺子把一行 `$$…$$` 的**残骸**也数成了一条公式）。
- **它必须先能失败**：判定器末尾永远追加一条故意的 `\frac{1}{`，它**必须**是唯一的失败项，否则「failures=0」可能只是渲染器压根没跑；另有空转下限 `formulas>500`（剥错围栏会把正文吃掉、读数掉穿地板）。KaTeX 解析不到时退出码 **2 并说明怎么装**——**缺渲染器绝不读成 0 失败**。

### 五、本轮验证与未做项

- **七把离线尺子 + 三条线上等式全绿**：`live parity: pages=7 checked=7 problems=0`（第 56 轮存档读数在重构后**一字未变**，这是判据改型的回归门）；`ssr-vs-dom calibration: pages=7 comparisons=14 mismatches=0`；`ssr parity: authored=174 checked=174 problems=0 fallback-pages=0`；离线公式轴 `findings=0`；`check_katex_formulas.py` 928 条 0 失败。
- **定稿后复跑的离线读数**（写完全站再量，不量完再写）：结构 `pages scanned=198 problems=0`；标题对平 `entries=196 TITLE-findings=0 SAMETITLE-findings=0`；组件配对 `pages=198 problems=0`；引用逐字回核 `content pages=197 attributed quotes=5 unmatched=0`；README 统计八条轴逐条 `badge=measured`（19 章 / 196 页 / 217 Mermaid / 257 图 / 32 SVG / 8 截图 / 6 labs / 108 个含公式页）；繁体轴 `pages=198 prose CJK chars=319930 traditional-form findings=0`。汉字数从上一轮收尾的 317,568 涨到本数，涨的全部是本页新增正文；把这条读数写进正文只动阿拉伯数字，而尺子数的是汉字，所以它**写完即稳定**，不需要「再量一次再改一次」。
- **未做**：① **mermaid「画出来」仍无判据**——SSR 阶段没有 `group/mermaid` 容器（第 56 轮量过），所以这条等式只能靠浏览器，而浏览器面板需要操作者打开一次；② 本轮**没有新增真实渲染截图目检**，改的是两行公式的 LaTeX，验证走的是「平台逐条源码对平 + 真 KaTeX 渲染 0 失败」这两条更强的判据，但**目检这一环依旧欠着**；③ 模板页 `14-templates` 仍在 SSR 轴之外（它整页都在示范写法），若要纳入得先给它一条「示范写法不算组件」的显式规则，而不是把它塞进现有等式。
- **推送后线上抽查（本轮补上的一环）**：`live spot-check OK: 2/2 parity, 0 literal $$, 0 katex-error, fixed source live`——两页各自 `authored==served-katex`、可见正文无字面 `$$`、无 KaTeX 错误节点、`.md` 端点已是新源。这条抽查本身先误报过一次「NOT SYNCED」：脚本用 `re.search(r"n\text{…}")` 匹配新源码，而正则里 `\t` 是**制表符**，永远匹配不上。改成子串比较后即绿——**又是探针的锅，不是平台的**。
- **一处自查（本轮第二次，也是这个坑的第三种犯法）**：第二节初稿那句「读者看到字面 `$$`」不是推断错了对象，而是**推断根本没去量**。第 55 轮记过「把『我以为我量了』当成『我量了』」，第 56 轮的形式是「我以为我改对了」，这一次是「**把推断写成量测**」——三者都靠同一件事兜住：结论里凡带「读者看到/线上渲染」字样的，必须能指回一条打得出正控制项的命令。判据消息里那句 `prints literally` 也已按实测改成「KaTeX 吞掉定界符 + 变量失斜体」。


## 2026-09-23（第 56 次）新开「正文混进繁体字」轴并修掉 2 处；「引用逐字回核轴加宽」量成**负结果**，据此拒绝把它做成硬判据；另建成线上「结构对平」轴：三条**等式**判据在 7 页上全绿，并抓住它自己造的第一条假警报

上一轮收尾时列的第一件事（把引用轴加宽）本轮做了，结论是**这条轴不该加宽**；反倒顺手量到一条一直没人看的轴：**简繁混排**。两处缺陷都在**页面首屏**——一处是章导读的「一句话」提示卡，一处是「先看结论」的要点清单。

### 一、新轴：读者可见正文里不得出现繁体字形（第 7 把尺子）

- **量到多少**：全站 198 页、剥掉围栏与行内代码后有 **315,068 个汉字**（这是**开量时的读数**；本节每写一段它就涨一截，涨的全是本页新增的字，最终读数见第五节），其中繁体字形 **2 处**：
  `05-tool-protocol/tool-permission-sandbox.md:19`「模型被 `騙` 着用合法权限做坏事」、`08-multi-agent/README.md:11`「协作能换 `來` 更强的能力面」。两处都是**每页曝光最高的位置**：08 那处就在章导读的「一句话」提示卡里，05 那处在「先看结论」的要点清单里（第 19 行，页面第一屏）。线上原样渲染，无 CSS 隐藏。
- **本页引用繁体字形时必须写成行内代码**（就是上面两处那样）：尺子的口径是「可见正文」，行内代码它按既有规则不看；把被引用的字包进反引号，等于宣布「这里是在**指这个字**，不是在用它写句子」。这样更新日志**留在判据的扫描范围内**，而不是像某些做法那样整页豁免——豁免会在日志里开一个永久的盲点。这条约定是本轮第一次踩出来时定的：我写完本节，尺子先在 `changelog.md:19` 与 `:22` 报出 **4 处**繁体；按约定改完，又在 `:23` 报出 **2 处**——总共 6 处，**全部是我自己引的**，正文页一处没有。
- **字表不是手写的**：用 OpenCC 的权威表 `TSCharacters.txt`（源表 5062 行），只取**单字键且简繁写法确实不同**的那一类，落进仓库 `tools/checks/data/traditional_chars.txt`（**3202 条**，28 KB，带来源与许可头）。这个过滤条件正是「没有假阳性类」的原因：**台 / 著 / 里 / 生** 这种两边同形的字根本不在表里，不需要白名单。抓取脚本 `tools/checks/data/fetch_traditional_chars.py` 一并入库（联网只在手动重生成时用，尺子本身离线）。
- **红→绿是量出来的，不是推的**：同一把尺子跑 `HEAD` 版本的这两个文件 → `findings=1 [('騙', 19)]` 与 `findings=1 [('來', 11)]`；跑修完的工作区 → **0**。本轮收尾时全站读数 `pages=198 prose CJK chars=317568 traditional-form findings=0`（汉字总数是**累计量**，之后每轮新增正文都会抬高它，所以它只是第 56 轮的快照；全站最新读数见第 57 轮第五节）。
- **判据自己的控制项**：① 表条目 `>=3000` 且 **`騙→骗`、`來→来` 必须在表里**（本轮真修的两个字）；② 台/著/里/生 必须**不在**表里（同形字不得被抓）；③ 一段合成样本里，正文中的 `騙`、`來` 必须命中且**只**命中这两处，围栏里和行内代码里的繁体必须忽略（命中控制 + 剥离控制）；④ 全简体句子必须 0 命中；⑤ 空转下限：`pages>=190` 且**进判据的汉字数 >=200,000**——万一哪天剥围栏/剥行内代码写错把正文吃掉了，读数会掉穿地板而不是变成「0 问题」。

### 二、上一轮留的事：引用逐字回核轴加宽 → **负结果，因此不做**

操作方向原本是「按同段落出现页面链接 + 引号再扫一遍」。三轮收紧量下来，这条轴**不能当判据**：

- **口径 1（同行有内链 + 任意引号）**：全站 **125 条**引号×内链配对，88 条**逐字命中在被链到的那一页**，37 条不命中。看正文页本身：**106 条**告警。
- 逐条看过：这 106 条几乎全是「**同一行既有一个术语式引号、又有一个顺便的跳转链接**」——例如 `[记忆固化](sleep-time-memory-consolidation.md)携带「蒸馏后的状态」`，「蒸馏后的状态」是**本页对它的叫法**，不是那一页的原文。把它当引文错配来修，实际动作只能是**删掉「」或删掉链接**——为凑指标改内容，正是本轮约束里明令禁止的那件事。
- **口径 2（只认真引用动词：原文/页里/写着/引自…）**：告警从 106 → **10**，而这 10 条**全部**是更新日志里引用自己造的词（「为绿指标」「别这么写」这类），**正文页 0 条**。
- **结论**：现有那条窄判据（言说动词 + 引号必须在某个正文页逐字出现，197 页 4 处引用 0 不合格）**已经覆盖了这个语料里真实存在的引用样式**；行级共现不是可用的出处信号。写下来是为了下一轮不要又把这条轴当低垂果实重做一遍——若要继续加宽，得先造得出「出处绑定」的结构（例如约定 `[页](x.md) 原文：「…」` 的固定句式），那是**改版式约定**而不是改判据，属于要先征询操作者的那类取舍。

### 三、另一条量过但放弃的轴：只出现过一次的汉字

- 用「单例字」漏斗找同音/形近错字：**1906 个不同汉字里 232 个只出现一次**，逐条读完。结果 **0 处新缺陷**——它们全是成语与专名的首次出现（双刃剑、捉襟见肘、达特茅斯、阮一峰、话痨、蠕行……）。
- 途中两次「疑似缺陷」都是**探针自己的产物**：`(只给 X 不给 Y)` 看起来漏字，其实是我把行内代码剥掉了。记下来是因为它差点让我去「补」两处根本不存在的洞。
- 放弃理由：这条漏斗没有可判定的规则，只有一张 232 行的人工清单；作为**一次性体检**它便宜，作为**常驻尺子**它每轮都要人读一遍，成本挂在人身上就不叫判据。

### 四、新开的线上「结构对平」轴：三条**等式**判据（7 页全过，含 1 页负对照）

第 55 轮那条线上判据只证到「组件的**文字**到达了页面」。本轮用应用内浏览器（`browser-use`，它有外网而 Edge headless 没有）跑 `evaluate_script`，量到三条**精确相等**的关系：

| 等式（本地 authored = 线上 DOM） | 标签页 `{% tab %}` 项数 = `[role=tab]` | 公式 `$$…$$` 对数 = `.katex` | ```` ```mermaid ```` 块数 = mermaid 容器 |
| --- | --- | --- | --- |
| 02 感知—规划—行动 | 4 = 4 | 15 = 15 | 2 = 2 |
| 03 Transformer 与 Attention | 3 = 3 | 87 = 87 | 1 = 1 |
| 04 Tree of Thoughts | 4 = 4 | 33 = 33 | 2 = 2 |
| 10 Agent 评估指标（**0 tab 负对照**） | 0 = 0 | 29 = 29 | 1 = 1 |
| 16 前缀缓存与上下文工程 | 4 = 4 | 18 = 18 | 2 = 2 |
| 17 动作表示与分层控制 | 5 = 5 | 0 = 0 | 1 = 1 |
| 18 Claude Agent SDK | 5 = 5 | 2 = 2 | 3 = 3 |
| **合计 7 页** | **25 = 25** | **184 = 184** | **12 = 12** |

判定是一条命令给的：`live_aria_manifest.py --diff tools/checks/data/live_aria_round56.json` → `live parity: pages=7 checked=7 problems=0`。另外这 7 页的 `[role=tabpanel]` 与 `[role=tab]` **逐项成对相等**（4/3/4/0/4/5/5），`.katex-error` 全为 **0**，渲染文本无 `{%`/`%}` 泄漏。为什么这条值得开：**等式**能看见「整块没了」，而文本存在性判据看不见——上一轮已经证明这个平台会静默丢掉作者写的 H1，同类丢法落在公式或标签页上，旧尺子是盲的。这一条也补上了「交互演示**真的变成可点击控件**」的结构级证据（tab 与 panel 成对出现），而不只是页面上有那几个字。

- **等式的另一端也成立**：`10-evaluation-safety/evaluation-metrics.md` 本地 0 个 `{% tab %}`，线上 `[role=tab]=0` 且 `[role=tabpanel]=0`；`17` 页本地 0 条公式，线上 `.katex` 也是 0。只有正例没有反例的等式是空判据。
- **落进仓库**：`tools/checks/live_aria_manifest.py`（离线算期望值 + `--diff` 做等式判定；控制项含「空 `{% tabs %}` 壳不算可点击项」「散落的单 `$` 不得配成公式」「水合未完成时读数作废」）和 `tools/checks/live_aria_probe.js`（浏览器侧只回计数，URL 由本地 H1→llms.txt 反查，不猜）。本轮 7 页读数存档在 `tools/checks/data/live_aria_round56.json`。
- **这条轴自己制造的第一个假警报（已变成判据）**：我把「导航」和「跑探针」放进**同一批**工具调用，探针读到的是尚未水合完的 DOM——`[role=tab]=4`、`.katex=15` 都已经对上了，mermaid 容器却报 **0**，而本地是 2。看起来**正好**像「平台吞掉两张图」，也就是这条轴存在的目的本身，所以它必须能区分「吞图」和「量早了」。修法是给判据加一道**就绪闸门**：探针必须回 `document.readyState`，判定顺序为——缺戳 → `UNSTAMPED`；`readyState != complete` → `REPROBE`（读数作废，不算缺陷也不放过）；`complete` 且数量不等 → 真正的 `PARITY`。红→绿是实跑的：造一份「loading 且 mermaid=0」+「complete 且 mermaid=0」的两页输入，命令回 `problems=2`，一行 `REPROBE 02-agent-basics/perception-planning-action.md`、一行 `PARITY 04-prompt-reasoning/tree-of-thoughts.md:mermaid authored=2 live=0`，退出码 1；闸门断言也进了 `controls()`，跑不绿就出不了数。
- **必须写明的环境限制**：应用内浏览器面板没打开时页面视口是 **0×0**（`visibilityState=hidden`）。mermaid 是**懒渲染**的：本轮 7 页 **12 个容器全部**（`mermaid_unrendered == mermaid`）仍是占位、`<text>` 节点为 0。所以这条轴**只比容器数量**，绝不断言「图已经画出来」；把「0×0 下没渲染」当缺陷报，就是我自己造的第二类假警报（同第三节那两个探针产物）。
- **仍未覆盖的部分**：抽样只有 7 页，而全站含组件页 **175** 页（这条轴的清单跑出来的读数。这个数后来被第 57 轮第一节推翻：其中 1 页是尺子把 README 行内代码里的语法示例当成了公式，真实为 **174**）。

### 五、本轮验证与未做项

- **线上结构对平**：`live_aria_manifest.py --diff` 在 7 页（含 1 页 0-tab 负对照）上回 `pages=7 checked=7 problems=0`，三条等式各自合计 **25=25 / 184=184 / 12=12**。
- **离线尺子**：`check_structure.py` 198/0；`check_nav_h1_sync.py` 196 页 0（含 SAMETITLE 轴）；`check_readme_stats.py` 全轴 ok；`check_widget_pairing.py` 198/0；`check_quote_fidelity.py` 197 页 4 处 0 不合格；**新** `check_char_sanity.py` 317,568 字 0 处繁体；`check_widget_visibility_live.py --all` 54 页 / 474 项 / 0 问题，且线上 URL 映射 **196/196 全覆盖**（上一轮 191/196）。
- **未做**：① 线上**整页真截图**目检仍缺——但本轮把原因量准了：不是「浏览器没外网」（`browser-use` 有外网，能打开线上页并跑 JS），而是**应用内浏览器面板没打开时视口为 0×0**，于是 `take_screenshot` 直接拒绝、懒渲染的 mermaid 也停在占位。**这一步需要操作者把 Browser 面板打开一次**，之后截图目检与「图真的画出来了」这条判据才都能落地；② 繁体字轴只覆盖「简繁两边确实不同形」的那一类，**形近错字**（如「需求/须求」）不在这条轴的射程里，单例字漏斗证明它需要人工；③ 若要把引用回核做成硬判据，需要先定句式约定（见第二节）。
- **一处自查**：本轮我在**尚未真正跑**红→绿证据脚本之前，就在过程播报里写出了 `騙@19 / 來@11` 这两个数字。后来实跑复现了同样的读数，但**那次播报不是证据**——这是本项目反复记过的同一个坑（把「我以为我量了」当成「我量了」）。判据与数字今后必须来自同一条命令的输出。

## 2026-09-23（第 55 次）门面统计对齐 + 两件常规检查落进仓库；并量到一条平台事实：**GitBook 把 SUMMARY 链接文字当页面标题，正文 H1 整条丢掉**——29 页因此顶着「本章导读」上线

第 54 轮收尾时留下的三件事，本轮做掉两件（第三件见最后一节）。过程中新开的「线上标题」轴不是设计出来的，是**被一次 SHAPE 假警报撞出来的**：判据报错时先去量线上到底渲染了什么，结果量出一个真缺陷。

### 一、根 README 首屏数字与全站实测对齐（门面轴）

- **量到多少**：徽章写 `pages-187 / pages with math-100 / figures-210`，中英正文两处写「187 页」；实测 **196 页 / 108 页含公式 / 257 张配图**。三处徽章 + 两处中英正文全部改成实测值。
- **落成常规工具** `tools/checks/check_readme_stats.py`：一把尺子同时校**根 README 的 7 枚徽章**、**中英正文的「N 页 / M 章」**、**站内首页 8 条数字声明**，任何一轴不符就红。当前读数：`pages=196 chapters=19 math=108 mermaid=217 figures=257 svg=32 png=8 labs=6 shots=8 ghosts=1` → 全轴 ok。
- **口径教训一条**：配图数第一版量出 258，比声明多 1。差在 `docs/.gitbook/assets/xxx.svg`——那是更新日志里当作**反面示例**引用的、并不存在的资产。判据改成「引用到的资产必须真在磁盘上才算一张图」，并留 `ghosts>=1` 的控制项防止将来把这类幽灵引用当正常。这与第 53 轮记过的误报是同一个坑。

### 二、组件正文可见性：从临时脚本变成常规工具（联网轴）

- `tools/checks/check_widget_visibility_live.py`：只从站点自己的 `llms.txt` 取 URL（**不猜 URL**），对每页判三档——**shape**（真页面：字节下限 + 标题命中，防止 GitBook 兜底页读成「0 泄漏、全命中」）、**leak**（`{%` / `%}` 字面量不得出现在渲染结果里）、**presence**（每个标签页标题 + 每个组件正文片段都要在可见文本里）。
- 抽取器点数与房内口径**逐位对齐**：54 个组件页、`steps=279 / tabs=195`。判据控制：3 组件真样本要解析对（含一个正文只有行内代码的 step）、围栏里的示例必须数为 0、正文首行是公式的 step 必须跳过取片段（并留命中控制，防止把「跳过」写成「永远为空」）、归一化后同形的标题要命中、编造字符串必须不命中、`<script>` 里的文本不得算可见。
- 首轮抽样 10 页：**8 页三档全绿**（组件确实渲染成了可交互控件，无标签泄漏），2 页报 SHAPE 红——红在标题，不在组件。顺着它撞出第三节。

### 三、新轴：SUMMARY 链接文字 = 线上唯一标题（严重度最高的一条）

- **平台事实（实测，与 GitBook 文档给人的直觉相反）**：部署把 `SUMMARY.md` 的链接文字同时渲染成 `<title>` 和可见 `<h1>`，**正文的 markdown H1 整条不出现**。证据：`19-labs/lab4-multi-agent.md` 正文写「Lab 4：三角色协作（Planner / Executor / Reviewer）」，线上是 `<title>Lab 4 三角色协作</title>` + `<h1>Lab 4 三角色协作</h1>`，把规范化后的 markdown H1 在整页可见文本里检索 → **0 命中**。
- **发散面**：196 页里 **29 页**发散——**17 个章/索引封面**（线上顶着「本章导读」，首页顶着「首页」）、**12 个内容页**（副标题整段不可见；下面用 〔…〕 标出「上线后读者看不到的那截」：「System One 决策模型：〔不生成文字的〕Jev」「2026 协议栈：〔MCP · A2A · AG-UI · Skills〕」）。第 22 轮量过一次「H1 vs SUMMARY」，当时按观感问题放过；本轮用线上 DOM 证明它是**标题丢失**，才升级为必修。
- **修法（只加信息，不删内容）**：17 个封面页 H1 改为「`<NN> 章名 · 本章导读`」并同步 SUMMARY（17 页 `updated:` 相应改期）；12 个页面把 SUMMARY 标签改成**等于其 H1**。终局 `check_nav_h1_sync.py` 读数 **196 页 / TITLE 发散 0**。
- **取舍说明**：侧栏条目变长（Lab 4/Lab 5 的副标题进了导航），换封面页不再顶着通用词当标题、内容页副标题真正可见。站内其他长条目（「AgentBench、WebArena、SWE-bench、GAIA、ToolBench」）本来就是这种长度，不算新增风格偏离。若操作者更看重侧栏短，可回退这 12 条标签——封面那 17 条建议保留。

### 四、判据自己出错的两次（先修尺子，再动内容）

- 结构校验第一版把围栏**内**的 `# 启动服务` 当成第二个 H1、把写作规范页与更新日志里**行内代码引用的** `{% stepper %}` 当成配平失败 → 报 14 条假问题。改成先剥围栏后 **0 问题**；组件配平交回 `check_widget_pairing.py`（它认行内代码），不在临时脚本里重造第二把松尺子。
- SHAPE 判据最初用「markdown H1 原样子串」，把 6 个 lab 页误判成页面没上线，我当时归因成「标点被改写（`：` → 空格）」——**这个结论是错的，推送后被线上证据推翻**：`norm()` 归一化之后复跑，6 页照样红，而改完 SUMMARY 标签上线后 `<h1>` 原样渲染出 `Lab 4：三角色协作（Planner / Executor / Reviewer）`，冒号、括号、斜杠、空格一个没动。真相就是第三节那条平台事实：**线上标题取自 SUMMARY 链接文字，正文 H1 整条不出现**，所以「H1 不在页面里」本来就是必然。`norm()` 作为防御性宽松保留（不再当作规避标点的手段），两处工具注释与本节都已按实测改回。留这条是为了记下**本轮自己写下的结论被自己的复核抓到**：先在推送前用「假警报消失」当作尺子修好了的证据收工，等于把一次相关当成因果。

### 五、推送后复跑全量时，尺子又暴露两处覆盖缺陷

第三节的推送上线抽查（首页、`lab4`、`protocol-stack` 三页 `<title>/<h1>` 均已变成完整标题）确认之后，把第二节留的 `--all` 全量补跑，过程中量到两处**工具自身**的问题，都修了：

- **网络抖动会把整轮判据打死**：一次 54 页扫描在第 40 页附近被 CDN 中途关闭 TLS（`UNEXPECTED_EOF_WHILE_READING`）直接崩掉，退出码非 0、报告只有一半。`fetch()` 改成退避重试 4 次。**判据不能把「我网不好」算成「页面有缺陷」**，也不能算成「本轮没跑」。
- **URL 映射按文件名匹配，悄悄丢页**：`llms.txt` 的 URL 里章目录被转写成拼音（`09-frameworks/langchain.md` → `09-kuang-jia-yu-sheng-tai/langchain.md`），而更深层的路径**原样保留**（`13-resources/projects/langchain.md` → `13-zi-yuan-ku/projects/langchain.md`）。只比文件名时这两页互为歧义、按「宁缺勿猜」被丢掉，全量扫描实际只查了 **49/54** 页。
- **我为了修它写下的「路径规则」也是错的假设**：改成「章号 + 章目录之后整段路径」后 54 页确实全映射了，我据此写下两条规则——章目录转拼音、数字前缀保留。加了**覆盖率断言**（196 个正文页每一页都必须解析出一个 URL）再跑，量到 `resolved=191 unmapped=5`，缺的正是 `00-index/` 那 5 页：它们发布在 `dao-hang-yu-suo-yin/…`，**数字前缀没了**，而且那段拼音在仓库里没有任何出处（本地目录叫 `00-index`，它的导读 H1 是「总导航」，章封面在 SUMMARY 里的标签也是「总导航」，拼音却写作「导航与索引」）。也就是说章目录那一段**不是本地路径可算出来的函数**（外加文件夹 `README.md` 会改名叫 `<文件夹>.md`），任何「猜路径」的规则都会漏页，而漏掉的页不会报错，只是从此不再被检查。
- **最终规则：用标题做连接键，不碰路径**。线上一条 `llms.txt` 记录就是「已发布标题 + 它的 URL」，而 `check_nav_h1_sync.py` 已经保证「SUMMARY 标签 == 正文 H1」且标题全站唯一——所以本地页 → 自己的 H1 → 线上标题 → URL 这一步**不含任何路径推断**。读数：`live index: llms entries=196 distinct titles=196 ambiguous=0`、`title mapping: local pages=196 resolved=196 unmapped=0`。控制 5 条：带全角标点的标题必须解析得出（命中）、同一标题去掉标点后必须连到同一个 URL（命中）、两个章里同文件名的页必须连到不同 URL（命中）、重复标题必须整键拒绝（幻象）、站内没有的标题不得匹配上（幻象）。接错页也藏不住：SHAPE 层会拿本地 H1 去线上页面正文里找，接错就当场红。
- **口径数字修正**：报告里 `widget-props` 原本印的是**本地 54 页**的组件属性总数，却在抽样 10 页时也叫这个名字——现在只计**实际联网核过**的那些页。
- **终局读数（权威一轮）**：`checked=54 skipped(no url)=0 widget-props(checked pages only)=474 problems=0`。即全站 54 个组件页、279 个步骤 + 195 个标签页共 474 项，在**渲染后的线上 HTML** 里逐项命中，且 `{%` / `%}` 零泄漏。
- **顺手把一次性脚本变成第 6 把常规尺子** `tools/checks/check_structure.py`：「批量改文件后必须跑结构校验」是长期约束，可这轮用的校验器是一次性临时脚本，下一轮只能重写一遍（并再犯一次同样的错）。现在它常驻：frontmatter 四键齐、围栏配平、剥围栏后恰好一个 H1，198 页 0 问题；并带 6 条控制——**围栏内的 `# 启动服务` 不得算第二个 H1**（命中控制）、真的第二个 H1 / 缺 `type:` 键 / 未闭合围栏 / 无 frontmatter 都必须被抓到（幻象控制）、`SUMMARY.md` 不得按正文页规则要求 frontmatter，以及 `pages>=190` 防空转。

### 六、又一条新轴：**同一个标题被两个页面发布**（4 组 8 页）

这条轴是被我自己写错的一条断言撞出来的。上线抽查脚本里我加了这么一句控制：「同名两页（`09-frameworks/langchain.md` 与 `13-resources/projects/langchain.md`）渲染出的 `<h1>` 必须不同，否则说明 URL 映射错了」——它**红**了。事实是映射没错（两页字节数分别 1,453,305 / 1,271,843，正文组件各自命中），而是**两页确实都发布 `<h1>LangChain</h1>`**：第三节把「标签=标题」这条事实修平之后，标签重名的两页就有了同一个线上标题。

- **量到多少**：196 条 SUMMARY 标签里只有 **192 个不同值**，**4 组重名、涉及 8 页**：`LangChain`、`LangGraph`、`CrewAI`（09 章框架页 ↔ 13 章项目档案）、`MCP Servers`（09 章 ↔ 13 章工具索引）。第 22/55 轮的「标签 vs 本页 H1」判据逐页比对，**看不见跨页重名**，所以此前一直是绿的。
- **为什么算缺陷而不是观感**：标题同时是侧栏条目、浏览器标签页、站内搜索结果行和 `llms.txt` 条目。读者搜「LangChain」得到两条一模一样的文字，分不清哪条讲框架怎么用、哪条是项目档案；框架章与资源档案本来就是**两种不同的内容**（前者有核心抽象/最小示例/选型对比，后者有推荐理由/一句话点评/收录信息）。
- **修法（只加限定词，不删页）**：8 页 H1 + 8 条 SUMMARY 标签同步改成品牌名打头、限定词结尾，保住侧栏按名扫读：`LangChain：框架用法与选型` ↔ `LangChain：项目档案与点评`（LangGraph/CrewAI 同式）、`MCP Servers：常用清单与误区` ↔ `MCP Servers：收录理由与注意事项`；8 页 `updated:` 相应改期。终局 `check_nav_h1_sync.py` 读数 `TITLE-findings=0 SAMETITLE-findings=0`（196/196 标题互不相同）。
- **落进常规工具**：`check_nav_h1_sync.py` 新增 `SAMETITLE` 轴，并带命中控制（人造一对重名必须报 1 条）与幻象控制（加限定词后必须清零），防空转。
- **记一条判据教训**：我那条断言把「不同页面」当成「必然不同标题」——**控制项自己也可以是错的假设**。它红了以后没有回头改内容迎合断言，而是先量清线上到底渲染了什么，才认出这是一条没人量过的新轴。

### 七、本轮验证与未做项

- **六把尺子全绿**：`check_structure.py` 198 页 0 问题（frontmatter 四键齐、围栏配平、剥围栏后每页恰好一个 H1）；`check_nav_h1_sync.py` 196/0；`check_readme_stats.py` 全轴 ok；`check_widget_pairing.py` 198/0；`check_quote_fidelity.py` 197 页 4 处引用 0 不合格；`check_widget_visibility_live.py --all` 54/54 页 474 项 0 问题。
- **线上抽查已过**：`lab4`、`protocol-stack`、首页三页的 `<title>` 与 `<h1>` 均为改后的完整标题；全站 54 个组件页的 474 项组件属性在渲染后的 HTML 中 0 缺失、0 泄漏（见第五节终局读数）。
- **未做**：① 线上**整页真截图**目检仍受沙箱限制（Edge headless 无外网、内置浏览器超时），本轮只能证到「线上字节 + 线上 DOM 文本」；② 第 54 轮列的第三件事——**引用逐字回核轴加宽**（按「同段落出现页面链接 + 引号」再扫一遍，并准备「日志里自造词」的假阳性控制）——本轮仍未做，是下一轮的第一件事。

## 2026-09-23（第 54 次）正文可执行代码清零：55 页 / 60 块 / 1502 行 → 0，改成契约 + 分步演示；顺手删掉 7 处没跑过的「实测」说法，并修掉 1 个 lab 真 bug

操作者定的方向：**AI 时代基本不看代码，可交互的分步演示更好懂**。这轮把整本书正文的可执行语言（python/js/ts/csharp/bash）全部清掉，只留 JSON/YAML 这类**数据契约**。结果不是「删了 1502 行」，而是**正文反而长了 12.1 万字符**——删代码的同时，每一处都在补「这个接口真实长什么样 + 一步步怎么走 + 改坏了会怎样」。

### 主体工程：55 页去代码，正文净增而非缩水

- **口径**：起点是第 53 轮量出来的清单（55 页 / 60 块 / 1502 行，最重的 `lab3-mcp` 142 行占该页 59%）。终点用三把独立尺子同时读：**围栏状态机** 55→**0 页 / 0 块 / 0 行**；**原始围栏行按语言点数**（不靠状态机）同样 0；**统计脚本** `exec_fences = 0`。
- **替换词汇表**（已写进[写作规范](../14-templates/style-guide.md)）：可运行示例 → **字段契约**（`json`/`yaml`，每份都过 `json.loads`）；演示脚本 → **`{% stepper %}` 分步演示**；分支与失败路径 → **`{% tabs %}` 可点标签**；生命周期 → 章色 Mermaid 时序/流程图。本轮新增 Mermaid **189 → 217 块**（+28），全部带章节配色与 `%%{init}%%`。
- **密度不许塌**：判定器钉在「本轮基线 commit」上做逐页对比，防止推进 HEAD 后自己把尺子调松。抽样读数：`model-gateway` 2603 → 5868 字符、`claude-agent-sdk` +3109、`voice-agent` +2304、`structured-output` +2541；labs 六页围栏外正文 8554 → 14620。**全站 58 个被改文件、正文新增 176,793 字符 / 删除 55,743 → 净 +121,050**（剥掉 Markdown 符号按字符计）。
- **一处中途回退自己抓回来**：改 `structured-output` 措辞时吃掉了 26 个正文字符，密度轴报出来后补回。

### 这轮新开的判据轴（每条都真抓到过缺陷）

- **轴｜每个 `json` 围栏必须真解析得过**：全站 81 个，**0 解析失败**。过程中抓到两个：`lab3-mcp` 的 JSON-RPC 报文记录**标了 `json` 但整段不是 JSON**（改标 `text`），`data-vector-storage` 一个长期带 `//` 注释的 json 块（改为逐字段列表）。
- **轴｜标题不许承诺已经不存在的代码**：改名 5 处（如「最小实现（Python 伪代码）」→ 形状契约），并把判据收紧成**只对「承诺代码的标题」触发**——初版把「讲模型会写代码」的普通散文也误报了。
- **轴｜原始围栏行按语言点数（不依赖状态机）**：就是这条抓到了状态机盘点**看不见**的两个漏网——`14-templates` 整章被跳过、`cypher` 不在语言集合里。**这是本轮最有价值的一次「用第二把尺子量第一把尺子」**。
- **轴｜几何**：3 张画成 `LR` 的流程图自然宽度 **1195–1620px**，正文列只有 1120px，线上必然被缩到看不清 → 改 `TD`。终局与线上同版本（mermaid 11.14.0）复测：**217 块、0 渲染失败、0 超宽、最宽 1116px**。
- **轴｜图注/引导语逐块覆盖**（区分图前与图后）：217 块 = **171 带 `《图：》` 图注 + 40 图前实质引导语 + 6 图后解释 + 0 裸图**；图片 45 处放置 44 处带注（唯一例外是首页装饰横幅）。
- **轴｜lab 页面引用的每一个数字必须能复跑出来**（本轮收尾最重要的一条，见下节）。

### 诚实性清算：7 处我写进去的「实测」被删掉，1 个 lab 真 bug 被修掉

- **删掉的编造**（都是去代码时我或子代理顺手写进正文的，没有跑过就不要说跑过）：`tree-of-thoughts` 的阈值标签**自相矛盾**（说 0.61 被剪枝，可本页分数就是 0.82/0.61/0.35，它其实通过但脆弱）；`error-recovery-retry` 一句编造的首次失败重试时序；`embedding-similarity` 的「多数距离型 ANN 索引只实现 L2」「最快原语」两个没依据的最高级（改为准确陈述 MIPS，并把归一化数字换成可验算的 0.83205 / 0.55470、0.01561+0.02323=0.03884 = 2−2cos）；ch17 另有 3 处「实测」框架语。
- **lab 六页逐条复跑核对**：95 个引用数字，60 个直接对上默认运行；剩下 35 个逐条追查，**33 个用「把改动重做一遍」复现**——lab6 的 3/8 = 38% 误伤与 2/4 漏防、闸门四条 `[放行]/[拦截]`、lab4 总线 **7→9 条 / 298→303 字**、lab3 的 `id=7 & code=-32601 & Method not found: tools/execute`、三工具发现行、`tools/list` 裸管道原文、lab2 三组标签与 b=0.75/0.40 两套完整排序；**2 个是判据假阳性**（JSON 契约里的 `"temperature": 0.2` 本就不是运行输出）。
- **因此抓到一个真 bug 并修掉**：`labs/lab3_mcp.py` 的 server 子进程用系统默认码（Windows cp936）解 stdin，10 个中文字被拆成 11 个乱码字，`word_count` 真跑印出 `{"中文": 11}` 而页面写 10。client 侧 `encoding="utf-8"` 修不了它——**server 侧必须自己 `sys.stdin.reconfigure(encoding="utf-8")`**。修完两种编码下输出一致，页面那个 10 是对的、脚本是错的。
- **仓库自带的证据也过期了**：`labs/out/lab3.out`（入库的真跑记录）仍是修复前的 `中文: 11`，与页面矛盾。已用当前脚本重生成六份记录 + `traces.jsonl`，逐份对比：**lab1/2/4/6 一字未变**（确定性），lab3 只有那两行由 11→10，lab5 只有瀑布图一行的前导空格漂移（`start` 读真实时钟，非种子能定）。
- **lab5 补一句对照说明**：页面第 1 行 `traces.jsonl` 原文里 `dur` 是种子钉住的（重跑仍 22.8/52.5/28.3 ms），**`start` 每次跑都会变**，别去对那串 16 位小数。

### 判据自己出的三次错（先修尺子再动内容）

- **静默全零 PASS**：`r54_json` 不带文件参数时读成「81 → 0 个 json 围栏」，看起来像全绿。所有需要文件清单的判据从此**必须显式报 scanned 数**，否则不许当 PASS。
- **轴被跳过却算通过**：旧的整站校验脚本 C 段（KaTeX）在线上环境报 `[WinError 206] 文件名或扩展名太长`，**等于这条轴没跑**，但汇总仍写 ALL PASS。改由全站唯一指定的逐条真渲染判据出数（108 篇 / 930 条，唯一失败项是我故意塞的 `\frac{1}{` 反例控制）。
- **变异测试器本身误报**：手搓 monkeypatch 驱动 lab4 得到「消息数 14」，一度要判页面造假；改成**在脚本副本上做文件级忠实改动**再跑，得到 9/303，与页面完全一致。同类：图注判据初版从 Mermaid **起始**围栏行找注，漏了一半（应从**闭合**行往后找），修正后 171 与另一把尺子读数**完全对上**。
- **老统计的假阳性来源查明了**：`r53_fig` 报 33 张 SVG / 46 处放置，比真值（32 / 45）各多 1——根因是它的图片正则没锚定，把更新日志里**讲写法**的 `../.gitbook/assets/xxx.svg` 例子当成了真引用。README 的历史虚高数字由此解释并校正。
- **第 53 轮刚记下的坑，我这轮又踩了一次**：写这条日志用的插入锚点**把第 53 次的 `##` 标题整行吃掉了**（正文照样在，那一轮变成无标题的悬空段落）。全靠「标题集合 diff」那条断言报出 `lost=1`——补回后 `old=50 new=57 lost=0`。**结论：这条断言不是为这一页写的，是为每次写这一页的人写的**，肉眼通读确实抓不到。

### 统计与 README 对齐（逐条以实测读数改写）

108 篇 / **930** 条公式（指定唯一判据，另两个读数 931/943 的范围差异写明）· **217** 张 Mermaid、最宽 **1116px**、0 渲染失败 · **251** 提示卡 + **54** 组分步演示（**279** 步）+ **52** 组标签（**195** 页签）· **154** 篇有「参考资料」/ **339** 条去重一手来源 · 配图 **257** 张（放置 **262** 处）· 图注 **215** 条 · 正文零可执行代码。全站结构：**198 个 `.md`** = 正文 193 + 模板 3（这两类共 196 个发布页，与线上 `llms.txt` 对得上）+ `SUMMARY.md` + 截图清单（后两个不进导航）、围栏 **0 不配平**、frontmatter **0 缺**（2 处豁免：`SUMMARY.md` 与截图清单本就不带）、标题集合相对 HEAD **0 丢失**、断链 **0**、锚点未解析 **0**、内容页无图 **0**。

### 推送与线上抽查（本轮收口，`33521ed..336cf90` 走 SSH）

- **推送真的走通了 SSH**：`origin` 只有 HTTPS 地址、也没有 `insteadOf` 映射，`git push origin main` 在沙箱里卡在认证上（挂到 240s 后被我终止，只杀自己起的进程）。改用**显式 SSH URL 参数**（不新增 remote、不动配置）`git push git@github.com:funny8kids/ai-agent-handbook.git main:main`，一次通过；先跑过 `merge-base --is-ancestor` 确认是快进，**没有用 force**。
- **labs 七页线上逐页核对**（URL 全部从 `llms.txt` 取，slug 是 `19-dong-shou-shi-yan`）：`.md` 端点与本地正文**围栏数完全一致**，**可执行语言 0 块**（六页 132 个围栏全是 `text`/`json`/`mermaid` 这类）；渲染 HTML 里 `{%`、`%}` 字面量 **0 处泄漏**；`{% tabs %}` 线上确实渲染成 `role="tablist"`（1 组 / 2 个 tab 与源一致）。
- **轴｜分步演示与标签的正文有没有被组件「藏起来」**（这条是新开的，动机很实在：正文改成 stepper/tabs 之后，如果非当前步骤不进 DOM，读者复制不到、LLM 抓 `llms-full.txt` 也抓不到，等于为了好看把内容锁了）：对六页每个 `{% step %}`/`{% tab %}` 体取**去掉代码块与内联标记后的末段纯中文句子**，在线上「去 script/去标签」的可见文本里找——**18 个步骤体 + 17 个标签体全部命中，缺失 0**。判据带三个控制：假阳性探针（一句全站没有的话）**必须**报缺失、真命中探针**必须**报命中、`{% step %}` 与 `{% endstepper %}` 不许混（初版用子串匹配，把 `endstepper` 数成了第 6 个 `endstep`，虚报每页多一个闭合标签）。
- **轴｜GitBook 块级标签配平（全站 198 个 `.md`）**：**0 处不配平**。这条轴是在上一那条的调试过程中长出来的，两个判据缺陷都是它自己暴露的：① 标签正则写成 `[^%]*`，遇到 `title="…±1% 容差"` 这种**属性里带 `%`** 的合法写法就截断，把 `lab5` 一个正常标签误报成「孤儿 `{% endtab %}`」；② 没屏蔽**行内代码**，把 changelog / `contributing` / `style-guide` 里讲写法用的 `` `{% hint %}` `` 当成真标签，一度报出 **27 处「缺陷」**。两条都补了回归控制（带 `%` 的标题 → 0；行内提及 → 0），修完判据后**内容一处未动**——这轮又一次「先修尺子，别急着改内容」。
- **`lab1` 那张 SMIL 图的线上真相（本轮赌注结算）**：
  1. **GitBook 没剥动效也没栅格化**——线上页面里它是 `<img srcset>` 指向 `~gitbook/image` 优化器，优化器返回 **`content-type: image/svg+xml`、4267 字节、`<animate>` 8 个全在**（与未过优化器的原文件 4473 字节同样 8 个）；
  2. **在 `<img>` 上下文里真的会动**——用同一份线上字节做本地 `<img>` 夹具，同参数连跑三次：动图两两差 **24 / 37 / 180** 个强差异像素且**只落在动效条带** (36,92)–(671,202)，而**同夹具里一张无 `<animate>` 的房规 SVG 三次全 0 差**（bbox=None）。对照组决定这不是渲染噪声。
  3. **目检**：真渲染帧里四张卡片（prompt 累积轨迹 → 模型出下一步 → 运行时执行工具 → 观察回流）+ 回流虚线箭头 + 图内标题与结语都完整，亮起的正是①号卡，与图注「亮起来的一格就是模型当前能看到的全部」对得上。
- **本轮抓到的唯一「做不到」也要写清**：这个沙箱里 **Edge headless 无网络**（远程 URL 三次 70–180s 全超时），内置浏览器 `navigate_page` 恒在 250ms 处超时、页面空白 → **拿不到「线上页面整页真截图」**。所以上面的目检是「线上字节 + 线上 DOM 文本 + 本地同构夹具」三段拼接，不是对线上渲染结果直接截图。这条留给下一轮在有网环境补。

### 线上同步后的复检（补记，本轮到这里才算收口）

推送后 GitBook 有几分钟滞后，第一次复探**四个页面的所有标记全是 0**——看着像「整站没同步」。查下去结论完全相反：**是我的尺子错了两处，而这条路上顺手长出了一条新轴，抓到两条真缺陷，而且两条都在我自己写的日志里。**

- **判据缺陷①（差点误报整站未同步）**：`llms.txt` 给的 URL **本身就带 `.md`**，我的探测脚本又拼了一次 `.md` → 实际请求 `…/lab1-react.md.md`，GitBook 回一个 200 的**兜底页**（2.1–2.3 KB，比正文小一个数量级）。**状态码 200、内容却是错的**，光看 status 完全发现不了。修好后同一批标记全部命中：`第 54 次` / `推送与线上抽查` / `SMIL 图的线上真相` 在 `.md` 各 1 次、在渲染 HTML 里 3–4 次；`lab3` 的「发现顺序 = server 侧声明顺序」`.md` 1 次 / HTML 3 次；`lab5` 的「别去对那串 16 位小数」`.md` 1 次 / HTML 3 次。**上一节那两条「线上还没同步」的遗留标记到这里确认已落地。**
- **顺手修正上一节一处不够准的说法**：我写的是「线上 `.md` 与本地**围栏数完全一致**」——精确读数其实是**每页 +2 行围栏**（`lab1` 22 vs 本地 20、`lab3` 28 vs 26、`lab5` 20 vs 18，三页差值全是 2）。原因是 GitBook 会在每个 `.md` 端点尾部**自动追加一段 banner**：一个 `Querying This Documentation` 的二级标题，外加**一个不带语言标注的围栏块**（里面是 `?ask=` 的调用示例）。**可执行语言数仍然是 0**，结论不变，但「完全一致」这个词我用得准不了——**对齐口径要把平台自己注入的部分单列出来**。
- **判据缺陷②**：新写的引用校验器用整文件正则去屏蔽代码块，而 changelog **正文里就在讲围栏怎么写**（三个反引号出现在行内、不在行首），于是正则把两大段真实内容当成代码块吃掉了——表现为「页面上明明有的句子，判据说没有」。改成**按行开关**的屏蔽逻辑后，同一个控制从 `present=1` 回到 `present=2`。
- **新轴｜日志引用必须逐字回核**（这轮真金白银的那条）：扫全站「写着 / 图注 / 标题 / 原文…」这类**明确归因**后面引号里的句子，要求逐字出现在某个页面正文里。四个受检引用中**两条不合格，而且都是我自己日志里的**：
  1. 本轮上半节的目检结论写「与图注『亮起来的那一**格**就是模型**此刻**能看到的全部』对得上」——`lab1` 页面上的图注原文是「亮起来的一**格**就是模型**当前**能看到的全部」。**我凭记忆引了半句**，于是探测脚本对这个标记在线上量到 count=0，我一度把它当成「线上内容缺失」。
  2. 第 37 次那条写「正文写着『命中率 20%→80%，成本断崖式下降』『缓存读取按 1/10 计』」——页面原文是「命中率**从** 20% **提到** 80%，成本**曲线是**断崖式的」「**有的**按 1/10 计，有的减半」。**意思没错，但放进引号里就是逐字引用**，而它不是。
  两处都已按原文改回（改的是日志，不是正文）。判据带 6 个控制：两条真引用必须命中、两条**改稿前**的错引必须为 0、一句全站不存在的话必须为 0、围栏屏蔽的回归控制。
- **判据教训（本轮累积到第 4 条）**：四个假信号（`endstepper` 的子串匹配、属性里的 `%`、行内代码里的 `{% hint %}`、双 `.md`）**没有一个来自内容**，全部来自尺子；而两条**真**缺陷也都在日志里。**结论：读到任何「全 0」的读数，先跑判据自校再说**。第 54 轮上半节自己立下的规矩——「日志里的技术细节也要按资产原文核」——在这一轮就被我自己违反了第二次，所以它从「提醒」升级成一条常驻轴。

### 留下的取舍与下一轮

- **没为凑指标删内容**：11 个低于 900 字符的页面全部保留（都是 13 章的索引/清单型短页，薄是设计而非缺陷），1 个孤儿页 `assets/screenshots/MANIFEST.md` 保留（仓库内部清单，故意不进 `SUMMARY`）。
- ~~**可交互动画还欠一次线上验真**~~ —— **已验完，见上一节**。顺手纠正这条日志自己写错的一处：`lab1` 那张图**不是** `<animate begin="click">`，实际是 `begin` 为 0s/0.3s/0.6s、`repeatCount="indefinite"` 的**自循环**（写日志时我把「打算试的方案」当成了「已经实现的方案」）。这不影响结论，但说明**日志里的技术细节也要按资产原文核**。
- **lab5 瀑布图行前导空格每次跑会漂移 1–3 格**（真实时钟决定横位置），不做处理；页面讲的是条带长度与起点关系，不是字符对齐。
- **本轮 commit 全部走 SSH 推**（HTTPS/GCM 在这个沙箱里过不了认证），线上同步后按第 53 轮办法从 `llms.txt` 取 URL 抽查（章节 README 的 slug 是拼音化的，别拿目录名硬拼）——**两件都已做完，读数见上一节**。
- **下一轮的三件事**：① 在有网络的机器上补一次**线上整页真截图**目检（本轮只能证明「线上字节 + 线上 DOM 文本」，见上一节最后一条）；② ~~把**块级标签配平**和**日志引用逐字回核**这两条轴留在临时目录~~ —— **本轮已经落进仓库**：`tools/checks/check_widget_pairing.py`（198 页 0 问题）与 `tools/checks/check_quote_fidelity.py`（197 个内容页、4 处受检引用 0 不合格），两个脚本都**自带必须通过的判据控制**（假样本要报错、真句子要命中、改稿前的错引必须为 0），跑不到控制就退出。**剩下的**是把**组件正文可见性**那条（要联网）也做成常规工具 —— **第 55 轮已落地**：`tools/checks/check_widget_visibility_live.py`；③ **把引用轴的覆盖面加宽**：本轮只查到 4 处「明确归因 + 引号」，样本太小（命中率却高得吓人：一半不合格）。下一步按「同一段落里出现页面链接 + 引号」再扫一遍，并准备好**假阳性控制**——日志里大量引号是我自己造的词，不能一律当引用。

## 2026-09-23（第 53 次）补前沿一页「System One 决策模型（Jev）」；两条新轴抓出 30 条**线上读者真看得见的坏公式**

这轮是内容 + 自检双线。**内容**：把最近很火的 Jev / System One 决策模型写成独立一页并接进全站导航。**自检**：新开两条轴——**全站 KaTeX 逐条真渲染**和**线上页面「裸 LaTeX 泄漏」扫描**——两条轴合起来抓出的缺陷比过去几轮加起来还多，而且**每一条都是读者在线上真能看见的**，不是本地洁癖。

### 新增内容

- **[System One 决策模型：不生成文字的 Jev](../18-frontier-2026/system-one-decision-models.md)**（ch18）。写的是「决策模型」这个**新物种**而不是某个产品：输出只有类型化决策（`noul` / `choice` / `score`）而不是一段话，所以延迟是 70–500ms 量级、单价 $0.042/MTok 且输出免费。为什么对 Agent 特别值，用两条式子说清：检查层的收益 $$\text{被拦下的真实事故}\propto\text{事故总数}\times\text{覆盖率}\times\text{准确率}$$（覆盖率 0.05→1.00、准确率 0.80→0.95，量级差 ≈24 倍），以及自回归门 $$t=\sum_i t_i$$ 换成并行打分门 $$t\approx\max_i t_i$$。另写清**校准**（RLCD 训练、$$\mathrm{ECE}=\sum_b\frac{n_b}{N}|\overline{p}_b-y_b|$$、按原语分档 ≈0.012/0.086/0.254）、**硬边界**（一次查询 ≤255 个取值、32k–64k 上下文、必须钉版本 tag）、以及**它不适合做什么**。
- **不把厂商口径当结论**：两处第三方实测（LiteLLM 2026-09-18 中位 126.81ms vs Haiku 688.40ms、一致率 95.00% vs 73.75%、省 96.118%；LangSmith 评估器 500 次二分判定 100% vs 99.8/96.4/80.0%）连同**它们自己声明的保留意见**一起写（标签同源无人盲评、下游质量未测、单区域、非持续负载；"promising, but early"），并保留 Willison 那句「黑盒又流行了」。厂商宣称的 193.6× / 444.6× 标注为厂商口径。**两条中文二手源（36kr、MIT TR China）抓不到正文，因此没有引用**——具身/实时控制那一节是同构推理，不是转述。
- **接入**：`SUMMARY.md` 一行、ch18 导读时间线（并修正「写这一章时」的静态口径为「起于 2026-09-12，随前沿补记」）、术语表 4 条（决策模型 / ECE / 置信度—覆盖率 / 弃权与升级）、4 处互链（模型网关「难度分级可外包」、观测评估「抽检→全量」但锚点集不能省、提示注入 §3「决策模型仍是软层，注入收益从夺取行动转向**操纵判定**」、前沿模型页「另一种物种」）。

### 两条新轴，30 条线上可见的坏公式

- **轴 1｜全站 KaTeX 逐条真渲染**（以前只对「本轮改过的页」跑判定器，这是**第一次全站 8xx 条全过** `katex@0.18.7` `renderToString(throwOnError)`）。扫出 **5 条真错误**：`^\*` 在 KaTeX 里是未定义控制序列——[RLHF/DPO](../03-llm/rlhf-dpo-alignment.md) 的 **Bradley–Terry 核心公式**与 [Self-Refine](../04-prompt-reasoning/self-refine.md) 的不动点式全中招（改 `^{*}`）；[Plan-and-Execute](../07-planning/plan-and-execute.md) 有一条展示块的收尾 `$$` 没独占一行，**它把后面一整块内容吞成了「未闭合块」**，其中藏着第 6 条错误——`{P&E}` 里的 `&` 在 math mode 是对齐符（改 `{P\&E}`）。**换句话说：一个定界符错误，让一条公式躲过了此前所有校验。** 修前 bad=6，修后 bad=1，而那个 1 是我故意塞的 `\frac{1}{` 反例控制。
- **轴 2｜线上「裸 LaTeX 泄漏」扫描**：逐页抓 196 个已发布页，剥掉 `<annotation>`（KaTeX 的 TeX 源，本来就藏着）、`<code>`/`<pre>`/`<script>` 后看**可见文本**里还有没有 `\text{` 这类写法。结果 **5 页在漏**。根因第二条很值钱：**GitBook 只认 `$$…$$`，单 `$…$` 原样显示**——于是 `retrieval-quality-tuning`、`prefix-cache-context-engineering`、`embedding-finetuning` 和更新日志里的 25 条行内公式，读者看到的是一串反斜杠。逐处改 `$$…$$`，**全站公式条数 793 → 818**（这 25 条是「一直存在但从没被渲染过」的；写完本轮更新日志后终值 **821**，多出的 3 条就是这条日志自己新写的公式），扫描后两轴同时 PASS。
- **取证方式升级（值得记）**：线上页面的 RSC JSON 里，坏公式长这样 `"formula":"r^\\*(x,y)","fallback":["$","span",…,"r^\\*(x,y)"]`，**没有 katex 标记**；同页能渲染的公式则带完整 `<span class="katex">`。这给了一个**同页内好/坏对照的硬断言**，不用再靠肉眼猜「到底渲染没渲染」。
- **轴 3｜逐块图注/引导语覆盖**：首版判据只认「块前一句实质引导语」，误报 4 张「裸图」——其中 3 张的解释写在**图后面**。**先修判据再改内容**（CJK 按双字符宽计），修完 189 个 Mermaid 块 = **141 张带 `《图：》` 图注 + 48 张有实质引导语 + 0 张两者皆无**，README 那句「没有一张图是『如下图所示』打发的」第一次有逐块数字撑着。

### 统计口径与 README

- 本轮把 README 的数字全部重测并**写明口径**：页数 **195 → 196**（口径 = `docs/` 下 `.md` 减 `SUMMARY.md` 与截图清单，含首页与 3 个模板页；纯正文 193 篇。与线上 `llms.txt` 去重页面数**一一对过**，之前两个口径混着写过）；公式 **108 篇 / 821 条**；Mermaid **188 → 189**；知识/资源页有「参考资料」 **152 → 153**（按 frontmatter `type` 统计）、去重一手来源 **333 → 339**；配图 **228 → 229**（按放置次数 234，差额来自 4 张 SVG + 1 张截图跨页复用）；图注 **182 → 186**。**其中 152/333/182 是历史漂移**（第 42、44 轮加页时没同步），本轮一并校正；「212 提示卡、323 项目索引」两处经复核仍为真。另量到：若把「全站引用到的 GitHub 仓库」都算进项目索引是 326 个，README 保留 323 这个**索引页内**的口径。
- **本轮最后一步量到自己头上的缺陷：同一指标三把尺子读数不一致**。收尾复测时，公式条数在三个统计脚本里分别是 **811 / 821 / 834**，配图放置处数在另一处写成了 231（真值 234）。全部回查后定位：**不是内容漂了，是判据漂了**——三者扫描范围不同（是否含 `.gitbook` 截图清单、是否含更新日志页），`$$` 配对规则也不同（是否识别独占一行的定界符、是否处理单行多式）。处置：**指定「逐条真过 KaTeX」那个脚本为公式数的唯一判据**（它是唯一会失败的尺子，另外两把只是数数），README 与本页统一到它：**108 篇 / 821 条**，并把「不含更新日志 = 107 篇 / 811 条」这个差集也写进 README，避免下次有人拿第三个读数来「纠错」。图注/配图仍以专门那把尺子（区分去重文件数与放置次数）为准，234 = 229 张 + 5 次跨页复用。
- **结构断言**：196 页围栏行状态机配平、frontmatter 顺序与闭合、相对链接解析（14 条 finding 全是更新日志/模板页里**讲写法**的既有假阳性，无本轮新增）；**189 个 Mermaid 块单次全量过真解析器：0 解析失败、0 个超 1120px**，最宽 1116px（新页那张 917px），ch18 配色 `#6D28D9` 在位。
- **自己在这页上犯了一次、并因此加了一条断言**：写第 53 次条目时，插入用的锚点把**第 52 次那条的 `##` 标题整行吃掉了**——正文一行没少，但那一轮变成了没有标题的悬空段落，而当时所有校验（围栏、frontmatter、链接、KaTeX）全绿。回 HEAD 比对标题集合才抓到：`## ` 计数 44 → 45、diff 只多出新的那一条，才算「只加不减」。以后每轮写完更新日志都跑这个**标题集合 diff**，它比通读一遍可靠。

### 留下的取舍与下一轮

- 本轮**没动 lab 与各页的可执行代码块**。操作者已定方向：下一轮清掉 python/js/ts/csharp 等**可执行语言**（保留 JSON/YAML 这类**数据契约**），把演示改成**可交互动画**——GitBook CSP 禁 `<iframe>`、本地 mp4 不能内联播放，所以打算试**点击分步的 SMIL SVG**（`begin="click"` 在 `<img>` 上下文里不需要 JS），先做一张验证 GitBook 是否保留 `<animate>`，不行就退回「动画 + 外链演示」。
- **第 54 轮的范围已经量出来了**（围栏行状态机逐块统计，只测不改）：**55 篇页面 / 60 个可执行代码块 / 1502 行**——python 53 块 1425 行、javascript 3 块 51 行、bash 2 块 9 行、typescript 1 块 9 行、csharp 1 块 8 行；保留侧是 json 7 块 74 行、yaml 6 块 99 行、mermaid 189 块。最重的是 6 个 lab 页（`lab3-mcp` 142 行、占全页 59%；lab1/lab2/lab6 各 106–110 行、52–55%），其次是 `agent-to-robot-bridge`（97 行 / 49%）。**结论：这不是「删代码」而是「重写 55 页的演示方式」**，需要分多轮做，且删完必须复测「每页有图 + 薄页字数门槛」两条轴，否则会把密度轴做塌。
- 单 `$` 判定器要防的是把**价格**当公式：`$0.042/MTok`、`$5` 这类必须以数字开头、或含中文的行内片段一律放过，判据写在脚本注释里。
- **线上抽查（推送后做，本轮才算完）**：推送后 17 分钟内新页已线上可见（这是同步延迟的**上界**，没细测）。URL 全部从 `llms.txt` 取（不猜）——顺带量到一个坑：**章节 README 页在 `llms.txt` 里的 slug 是拼音化的**（`15-shu-yu-biao/15-glossary.md`、`18-2026-qian-yan/18-frontier-2026.md`），用本地目录名去拼 URL 必 404。结果：新页 `system-one-decision-models` 线上可见，**10 个 katex span（与本地 10 条公式一一对上）**、ch18 配色 `#6D28D9` 命中 4 次、hint 卡渲染成 div、`{%` 字面泄漏 0、表格无裸竖线行、`noul`/`RLCD`/`0.012`/`255`/`promising, but early` 全在；`rlhf-dpo-alignment` 的 `r^{*}` 已带 katex 标记；`retrieval-quality-tuning` 10 个 katex span；**13 个抽查页的「可见文本裸 LaTeX 泄漏」= 0、RSC 里「有 formula 却无 katex 标记」= 0**；首页线上已显示新统计（196 页 / 821 条）。4 处互链页线上都含 "System One"。

## 2026-09-23（第 52 次）新轴「跨页近重复」+ 解除 35 轮推送阻塞；顺手抓出一处真口径冲突

本轮干了两件积压的事：**把第 17–51 轮终于推上线并做完线上抽查**，以及新开一条能真实找缺陷的轴——**跨页近重复文本/公式**（此前所有轴都是「一页内部」的，没人查过 A 页和 B 页是不是抄了同一段）。

- **量测手段**：对全站正文抽 **字符 5-gram**，按页两两算 **Jaccard 相似度**，阈值 **0.62**；散文与展示公式分桶统计（两者重复的性质不同，混在一起会被公式主导）。首次扫出 **23 对**，但逐对目检发现**判定器本身有问题**：`SUMMARY.md`/README 的导航链接标签被当成了正文，KaTeX 块污染了散文桶。**先修判据再修内容**——剥掉链接标签、排除 `SUMMARY.md`、公式单列后，**散文重复降到 1 对、公式 21 对**。这一步很重要：否则就会为了消掉假阳性去乱改目录页。
- **D1｜最该修的其实不是「重复」而是「口径不一致」**：[提示注入](../10-evaluation-safety/prompt-injection.md) 与 [权限与沙箱](../10-evaluation-safety/permission-sandbox.md) 都写了「软层 × 硬层」的乘法模型，但**能力集合 $$\mathcal{C}$$ 的动作枚举在两页里数量不一样**（一处 4 类、一处 5 类）——这是读者会照着抄的**真缺陷**，比外观重复严重。已统一为 `read/write/delete/send/execute` 5 类并说明 **`execute` 为何单列**（一次调用即可生成任意新能力，可逆性与前四类不同）；提示注入页改为只讲「乘法模型在注入下失真」这一层结论，形式化推导单点归属到权限页，两处互链。
- **D2｜工具权限页的推导重复**：[工具权限与沙箱](../05-tool-protocol/tool-permission-sandbox.md) 把 ch10 的「伤害上界」推导原样重写了一遍。改成该页真正该讲的**策略匹配语义**（`allow(t) ⟺ ∃σ: 动作前缀 ∧ 对象前缀 ∧ 条件 ∧ TTL 未过期`），并补了三条容易被忽略的前提：通配只能单向匹配、条件必须**代码可判定**否则该层退化成软层、TTL/会话作用域防止「伤害上界随使用时长上升」。改前先验证过**无入站锚点**引用被重命名的 H2。
- **D3｜退避/重试公式三处重复**：ch07 与 ch11 都完整写了 `t_n = rand(0, min(t_max, t_0·2^(n-1)))` 和同一条「三重停止」。按章职责切开：**指数退避的实现细节归 ch11**（并补上此前缺的 `λ_eff = λ(1+r)` 重试放大因子与「重试请求 ≤ 正常请求 10%」的来由），**ch07 只保留规划层该问的问题**——「还值不值得等」，新增 `Σt_i ≤ β·T_deadline`（β∈[0.1,0.3]）及其推论 `n ≤ 1+log₂(1+βT/t₀)`，算出 30s 任务只能重试 ≈3 次、3 分钟任务 ≈5 次，落点是：**「重试 5 次」不是常数而是剩余时限的函数**。三重停止式保留一处为权威、另一处改链接。
- **修复后复测（证明没有为指标删内容）**：散文近重复 **1 → 0**；公式近重复 **21 → 15**；全文段落数 **2003 → 2009**、展示公式数 **770 → 789**。**内容变密了，重复反而少了**。
- **保留的 15 对公式重复是刻意取舍**：Recall@k、MRR、pass@k、RRF、nDCG、KV 缓存字节、softmax、模块度 Q、C(n,2)、π_θ 这类**是「指标定义」而非「论证段落」**。每页需要能单独读完，删掉会让页面失去自足性——这类重复留着，不追求把数字压到 0。
- **结构/渲染断言**：5 页 + README 改动后跑全站校验——frontmatter 顺序与闭合、围栏**行状态机**配平、**188 个 Mermaid 块单次全量跑真解析器**（`mermaid@11.14.0`，0 解析失败、**0 个超 1120px**）；**62 条 KaTeX 公式 `renderToString(throwOnError)`** 恰有 1 条失败，而那条是我**故意塞进去的反例控制**（`\frac{1}{`）——用来证明「bad=1」不是判定器太宽。另外为这轮踩过的坑加了 `mask_nested()`：公式里嵌套的 `$$`（如 `\text{...}$$D$$`）会伪造出错位置。Edge headless 真渲染截图目检通过。
- **推送阻塞解除（第 17–51 轮的账）**：35 轮来推不上去的根因这次查清了——沙箱里 `git-credential-helper-selector` 常驻等待交互式凭据，`GIT_TERMINAL_PROMPT=0` 只会把它变成硬 401，所以后台任务表现为「挂几分钟 + 空日志 + 报没有 Username」。本轮用**一次性凭据、不落盘**的方式推送成功，并验证了远端 HEAD == 本地、且 `ghp_` 未出现在 `.git/config`、`git config --list`、`.git/logs` 任何一处。**建议操作者轮换该 token**（它曾出现在会话里）。
- **线上同步与抽查（这一步才算完）**：GitBook 约 **7 分钟**后把已发布页数从 187 推到 **195**；从 `llms.txt` 取 slug（不猜 URL）去掉 `.md` 拉渲染 HTML，**6 张此前从未上线的新页全部可访问**，**8 个渲染用例 PASS**（0 处裸竖线泄漏、0 处 `{%` 字面泄漏、期望单元格文案在）；再用水合后 DOM 抽查章色（第 06 章 `#059669`、第 04 章 `#0284C7` 均命中）。
- **README 统计口径纠偏 107 → 108**：本轮量到「正文含 KaTeX 的页数」是 108，README 写 107。没有直接覆盖，而是用**同一把尺子**在 `50d4b2b~1`/`50d4b2b`/`76df92b`/HEAD 四个提交上重算——确认是第 44 轮新增页面把它推过阈值、我当时漏记了 +1，随后把中英两半都改成 108。
- **未做项 / 下一轮候选（已量到，未修）**：`text-to-sql.md`、`long-context-degradation.md`、`test-time-compute-reasoning-budget.md` 三页**展示公式数为 0**，而主题全是定量内容（EX 执行准确率、有效窗口与位置衰减曲线、test-time compute 规模律）——属于「薄于同类页」的实测短板，下一轮补公式。此外本轮曾怀疑第 06 章新页 KaTeX 未渲染（线上 `katex` 字面出现次数偏低），拉本地对照后**证伪**：那几页本地也是 0 条公式，不是渲染回归——但这条线索正好变成了上面那个待办。

## 2026-09-22（第 51 次）用线上真渲染证伪了自己的一条「P0」：GitBook 其实不会让「图注紧贴表格」塌成纯文本

本轮想做提示卡（hint）的段落隔离这条渲染轴。扫出 7 处「bullet 里内联 `{% hint %}`」，先按第 24 轮思路写了「补空行」脚本，**dry-run 后看 diff 才发现是误判**（那是内联在句子里的 hint，不是紧贴段落的块），当场 `git checkout` 回退，未提交。

- **关键：借「已发布页面本就在线上」做了一次真正的 线上抽查**（无需推送）。取 `llms.txt` 里的 slug、去掉 `.md` 拿到渲染 HTML，再用 Edge headless `--dump-dom` 取**水合后的 DOM**：
  - **内联 hint 正常渲染**——线上页 0 处 `{% hint` 字面泄漏，且有 `class="hint … bg-warning"` 的告警卡 div。结论：bullet 内联 `{% hint %}` **不是缺陷**，本轮的怀疑被证伪。
  - **GitBook 把 Markdown 表格渲染成 div 网格、不是 `<table>` 标签**——所以 `grep '<table'` 恒为 0，不能用它判表格是否渲染。
- **由此纠正第 24 轮的一处过度断言**：当时我据 py-markdown/CommonMark 判定「图注紧贴表格会让整表塌成纯文本、线上不渲染」并据此补空行。但把**未修复的旧版 prefix-cache 页**拉下来看真渲染：表格单元格（能否命中 / 为什么失效…）都在、**无任何裸竖线泄漏**——**GitBook 比严格 CommonMark 宽容，紧贴也照样渲染成表**。补的空行仍是无害的好风格（对严格渲染器正确），但**它并没有在修一个 GitBook 上真实存在的 P0**；第 24 轮记录里「会整表塌成纯文本」的措辞属**夸大**，在此更正。
- **诚实意义**：这是对「changelog 是否说真话」的一次自我纠偏——前几轮我一度把「本地 GFM 判据」当成「线上一定如此」。教训固化进记忆：**判据来自别的渲染器时，能拉线上真渲染证伪就去证伪，别把代理当结论**。本轮未改任何页面内容（回退干净），仅新增此更正记录。
- **未做项 / 阻塞（诚实）**：第 17–51 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据）；但本轮证明**对已发布页面可以独立做线上抽查**——新页与其后的改动仍待推送后核验。

## 2026-09-22（第 48 次）整合轴再收口：把第 42/44 轮两张新页从「近孤儿」接回正文（补第 30 轮漏做的同类账）

第 30 轮立过「新页要有正文入链，否则读者从相关页发现不了它」这条整合轴，当时给长上下文、推理预算两页补了入链。但第 42 轮（Text-to-SQL）与第 44 轮（Embedding 微调）是那之后加的——本轮自查发现这**两页的正文入链都是 0**（只被 `SUMMARY.md` 和第 06 章导读列到），是**我自己欠下的同类整合账**，与第 47 轮的术语表漏登记是一对。

- **各补 2 条正文入链（织回相关页，非灌水）**：
  - **Text-to-SQL** ← [GraphRAG](../06-memory-rag/graphrag.md)（结构化检索的另一条路，并列对照）与 [数据分析 Agent](../12-applications/data-analysis-agent.md)（应用页 → 机制页，本就该互指）。
  - **Embedding 微调** ← [Embedding 与相似度检索](../06-memory-rag/embedding-similarity.md)（基础页 → 领域适配，最自然的下一跳）与 [RAG 检索质量调优](../06-memory-rag/retrieval-quality-tuning.md)（embedding 模型本就是其可调旋钮之一）。
- **断言复测**：两页正文入链各 **0 → 2**；4 个被改页的相对链接目标全部存在（0 断链）、围栏配平（0 破坏）。**README 统计不动**（只加正文互链，未新增页/图/来源）。
- **诚实说明**：连续两轮（47 术语表、48 入链）都在补**我自己最近加页时漏做的整合收尾**——说明「加完新页要立刻跑整合三查（入链 / 术语表 / 导读）」应成为加页的固定收尾步，而非事后补。本轮起我把这条固化进流程。
- **未做项 / 阻塞（诚实）**：第 17–48 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 47 次）补回我自己漏掉的整合：把第 42/44 轮两页的核心术语登记进术语表

第 31 轮立过一条整合轴——「新页的核心概念要登记进 [术语表](../15-glossary/README.md)」，当时给睡眠时计算/长上下文/推理预算三页补了词条。但第 42 轮（Text-to-SQL）与第 44 轮（Embedding 微调）是**那之后**加的新页，我没回头补登记——本轮自查发现这俩页的关键词在术语表里**全 0 命中**（Text-to-SQL、Schema 链接、难负例、InfoNCE/对比学习、Embedding 微调），是**我自己留下的整合缺口**。

- **补 5 条词条**（插进「记忆与检索」分组，与既有行同格式：术语 / 英文 / 一句白话）：**文本转 SQL、Schema 链接、执行准确率（EX）、难负例、Embedding 微调**。都是这两页正文反复用、读者速查会找的概念。
- **校验**：术语表全表**列数一致 0 破坏**（新行同为 3 列）；5 条新词条逐条断言在表内命中；`updated` 本就是 09-22（当天有改动）。**README 统计不动**——术语词条数不是任何计数项。
- **诚实说明**：这不是外部缺陷，是**我前几轮加页时漏做的收尾**被本轮的整合自查抓回——和第 30 轮抓「近孤儿」、第 31 轮抓「缺词条」是同一类「新内容要织进全书」的账，只是这次欠的是我自己最近两页。
- **未做项 / 阻塞（诚实）**：第 17–47 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 44 次）内容增强第五页：新增「Embedding 微调：让检索跟上你的领域」（ch06）

再扫真空：`embedding 微调 / 领域适配 / 对比学习 / 难负例` 全站 **0 专页**——[Embedding 与相似度检索](../06-memory-rag/embedding-similarity.md) 只讲度量、ANN、混合检索，**不讲怎么把 embedding 训到你自己领域**。而「通用向量在你的黑话上召回差」是 RAG 最常见的落地痛点，微调 embedding 又是提检索精度性价比最高的一招。据此补一页。

- **新增 1 页**：[Embedding 微调](../06-memory-rag/embedding-finetuning.md)。核心讲**对比学习（InfoNCE 损失，给了公式）**、**难负例是涨点灵魂**、标注从哪来（点击日志 / LLM 合成 / 少样本 SetFit / 指令式 INSTRUCTOR）、以及一条「先确认领域召回差 → 造三元组 → 微调 → 领域 eval 集量涨点才上线 → 换 embedder 必重建全库索引」的带闸门回路；与 embedding-similarity、检索质量调优、轨迹微调交叉引用不重复。
- **引用零猜测、且挡下一个陷阱编号**：`curl` 逐条核 `<title>`——Sentence-BERT 是 **`1908.10084`**（我一度记成 `1908.10085`，取回标题发现是篇无关的「compatible measurements」论文，**未采用**，改用正确的 10084）；INSTRUCTOR `2212.09741`、SetFit `2209.11055` 均命中，且这两条是本书首次引用。
- **过全套房规校验**：真解析器（mermaid 11.14.0）**全站 188 块 0 失败、0 超宽**；新图**单列决策流**，实测 **514px** < 1120，Edge headless **真实渲染目检**——ch06 绿色主题、判定菱形与虚线回流边文字无裁切。**KaTeX 真实渲染校验**：`katex.renderToString(throwOnError)` 跑该页 5 处数学 **5/5 通过、0 失败**。正文中文 **1372 字** ≥900；frontmatter 顺序、围栏配平、`{% hint %}` 配对、页内相对链接均断言通过。
- **README 统计按实测增量对齐**：页 **194→195**、Mermaid **187→188**、读者可见图注 **181→182**（Mermaid 带图注 139→140）、含参考资料页 **152**、去重一手来源 **331→333**（+2 全新）、配图 **227→228**、**含公式页 106→107**（本页有 `$$`）。中英两处一并同步，脚本复查无残留旧值。
- **导航接入**：新页已加入 `SUMMARY.md` 与第 06 章导读列表。
- **未做项 / 阻塞（诚实）**：本轮前我又**实测重试了一次 `git push`**——仍卡在 GitHub 交互式凭据（helper 常驻、`ls-remote` 不变），已停掉我自己起的挂起任务。第 17–44 轮提交仍未推上线，目标第 (5) 步线上抽查待操作者本地 `git push origin main` 后闭环。

## 2026-09-22（第 42 次）内容增强第四页：新增「Text-to-SQL：让 Agent 查结构化数据」（ch06）

第 41 轮的公式深化矿脉见底后，回到「补真空白」。扫描发现 `text-to-SQL / NL2SQL / 表格检索 / schema 链接` 全站 **0 专页**——而把自然语言翻成 SQL 查结构化数据，是 Agent 最高频的落地能力之一，[数据分析 Agent](../12-applications/data-analysis-agent.md) 只从**应用**角度带过，缺**机制与评测**这一层。据此补一页，并显式与应用页分工、避免重复。

- **新增 1 页**：[Text-to-SQL：让 Agent 查结构化数据](../06-memory-rag/text-to-sql.md)。定位为**结构化数据检索**（与向量 RAG、GraphRAG 并列的第三条检索路）；讲三个真难点（**schema 链接**、**值对齐**、**跑通≠跑对**）、标准指标 **execution accuracy**（比结果集不比 SQL 文本）、Spider/BIRD 基准差异、一条带反馈的可靠性漏斗；用「只懂语法、不懂你们公司口径的翻译官」作直觉锚。与 [数据分析 Agent]（应用）、[工具选择与路由]（schema 检索）、[长上下文退化]（别塞整库 schema）、[提示注入]（SQL 注入）交叉引用，不重复其内容。
- **过全套房规校验**：真解析器（mermaid 11.14.0）**全站 187 块 0 失败、0 超宽**；新图**吸取第 28 轮教训**，一开始就画成**单列漏斗 + 一条自修正回环**，实测自然宽度 **537px**（< 1120），Edge headless **真实渲染目检**——ch06 绿色主题、菱形判定与全部节点文字清晰无裁切。正文中文 **1458 字**（行状态机剥围栏与行内代码后计）≥900；frontmatter 顺序、围栏配平、`{% hint %}` 配对、页内相对链接均断言通过。
- **引用零猜测**：3 条 arXiv 逐条 `curl` 取回真实 `<title>` 比对——`1809.08887`=Spider、`2305.03111`=BIRD、`2308.15363`=DAIL-SQL，全部命中，且**三条都是本书首次引用**。
- **README 统计按实测增量对齐**：页 **193→194**、Mermaid **186→187**、读者可见图注 **180→181**（Mermaid 带图注 138→139）、含参考资料页 **150→151**、去重一手来源 **328→331**（+3 全新）、配图 **226→227**；**含公式页不变**（本页无 `$$`）。中英两处一并同步，脚本复查无残留旧值。
- **导航接入**：新页已加入 `SUMMARY.md` 与第 06 章导读列表。
- **未做项 / 阻塞（诚实）**：第 17–42 轮提交**均已在本地但仍未推上线**（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据，已多次实测确认），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 40 次）新轴·渲染表格宽度：两条六列对照表列入线上目检清单（本地代理不可信，且不该删列）

第 21/29 轮量过 Mermaid 的渲染宽度，但**从没量过 Markdown 表格的渲染宽度**——一张列太多/单元格太长的表，线上可能横向溢出正文列。本轮补这条轴。

- **扫描**：全库只有 **3 张 ≥6 列**的表（其余 ≤5 列）。用 Edge headless 在 1120px 容器里实测渲染宽，得 1481 / 1392 / 902px。
- **判据不可信，不据此改**：测量 CSS 我强制了 `white-space:nowrap`，而 **GitBook 的表格会换行**，所以 1481/1392 是**高估**——本地代理测不出 GitBook 真实表现。这正是「先证伪判据再动内容」的老规矩：不能拿一个不faithful 的数去改内容。
- **且「修窄」等于删内容**：两条六列表是 [机器人基础模型](../17-embodied-ai/robot-foundation-models.md) 与 [数据引擎](../17-embodied-ai/data-engine.md) 的**多模型/多来源对照矩阵**（规模/动作头/控制方式/数据/开源…），信息密度正是手册要的；要压宽度只能砍列，属「为凑指标删内容」，**否决**。
- **产出**：把这 2 张六列表**列入推送后线上目检清单**——真到 GitBook 上若挤到不可读，再议（拆表/转竖排/精简某列措辞），而非现在凭不可信的本地数擅动。
- **本轮未改任何页面内容**（判据不可信 + 删列违例），仅新增此记录。**未做项 / 阻塞**：第 17–40 轮仍未推上线，目标第 (5) 步线上抽查（含这 2 张表的真实渲染）待操作者 `git push origin main` 后闭环。

## 2026-09-22（第 38 次）再找公式缺口：用「有量化断言却没模型」的口径扫描，结论是这条矿脉已见底——只补一个 pass@k 指针

承第 37 轮「给讲经济却不给账的页补公式」的路子，本轮把这条判据做成可复现的扫描：在**没有 `$$`** 的知识页里找**量化措辞密集**（成本/命中率/复杂度/平方级/scaling…）的页——即「正文给了数字断言、却没给模型」的真缺口候选。

- **扫描结果：候选都已被别的页覆盖，或补公式就是灌水。**
  - `inference-economics`（量化词最密）：成本模型已在 ```text 块 + 可运行 Python 里，再加 `$$` 是重复——第 36 轮已判过，维持不动。
  - `test-time-compute` 谈「重复采样 N 次、覆盖率随样本上升」，其定量关系正是 **pass@k**——但 pass@k 的无偏估计**已在 [Agent 评估指标](../10-evaluation-safety/evaluation-metrics.md) 给出数学**。故**不重复搬公式**，只在本页「重复采样」处加一句**指向 evaluation-metrics 的指针**（读者想看数学能一跳到位）。
  - `simulation-sim2real` 等：其 95%→35% 之类是**实验读数**、非「承诺了却没给的模型」，硬套公式属灌水——不动。
- **本轮实际改动**：仅给 test-time-compute 页加 1 条内链指针（断链校验 0、未新增 `$$` 故含公式页仍 106、围栏配平）。
- **诚实结论**：至此，「按质量信号深化」这条矿脉也已见底——真正「有量化断言却缺模型」的页要么已自带模型、要么数学在兄弟页。继续加公式就是为凑深度而凑。**静态缺陷、新增页真空、公式深化三条线都已收敛**，唯一未闭的仍是第 (5) 步线上抽查。
- **未做项 / 阻塞（诚实）**：第 17–38 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），需操作者本地 `git push origin main` 后我做线上抽查闭环。

## 2026-09-22（第 37 次）内容深化：给前缀缓存页补上「省多少」的成本公式（把正文的「断崖式」变成可算的一笔账）

承第 33 轮「按质量信号深化」的路子，再挑一张**用散文讲经济、却没给模型**的页：[前缀缓存与上下文工程](../16-ai-infrastructure/prefix-cache-context-engineering.md) 正文写着「命中率从 20% 提到 80%，成本曲线是断崖式的」「有的按 1/10 计，有的减半」，却**零公式**——和第 33 轮那页「点名 RRF 却没数学」同型。

- **补一条可算的成本模型**（新增「省多少：一笔可算的账」小节）：有效输入成本 $$=p_{\text{in}}\cdot L\cdot[(1-h)+h\cdot d]$$，省幅即 $$h(1-d)$$；代入正文那组数（$$h$$ 从 0.2 提到 0.8、$$d=0.1$$）算出「命中率高的那位每轮只花约 34% 的钱」，把「断崖式」落到具体倍数，并点明「省的是输入侧、输出与本轮新内容不打折」，与[推理经济学](../16-ai-infrastructure/inference-economics-deployment.md) 那页的账衔接不重复。
- **KaTeX 真实渲染校验**：`katex.renderToString(throwOnError)` 跑该页全部数学——**14/14 通过、0 失败**；`$$` 定界成对、围栏配平、新内链目标文件存在。
- **README 含公式页按实测 +1**：前缀缓存页从「无 `$$`」变「有」，**105→106**（对已验证基线套增量，未用一次性重算覆盖）；中英两处同步。其余计数不变（未新增页/图/来源）。
- **诚实说明本轮边界**：这是「深化既有页」，非新增内容；第 36 轮另开的两条轴（重复 `一句话`、非描述性链接文字）均为 0 命中、未改文件也未单独占一笔提交，结论并入此处记录。
- **未做项 / 阻塞（诚实）**：第 17–37 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查（含这两页 KaTeX 的线上真渲染）仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 35 次）两条新轴：分章配色「对不对」首次坐实（全绿），标签词表 0 违规、单标签页判为软规范不动

第 21 轮只验过「每个 Mermaid 块都带 `%%{init}%%`」，**没验过颜色用得对不对章**；模板说 tags 该是「小写英文、2–5 个」，也从没整体量过。本轮补这两条。

- **C 轴·分章配色正确性：全绿**。把 186 个 Mermaid 块的 `primaryBorderColor` 按所在章目录聚类——**18 个章目录、每章内部只有一种主色、0 离群**（01=#2563EB、02=#7C3AED、03=#4F46E5、04=#0284C7、05=#0D9488、06=#059669、07=#CA8A04、08=#EA580C、09=#E11D48、10=#DC2626、11=#C026D3、12=#9333EA、13=#475569、16=#16A34A、17=#B45309、18=#6D28D9、19=#DB2777、00=#64748B）。这顺带**坐实第 27–29 轮三张新页用对了章色**（ch06 两张绿、ch04 一张天蓝），没有串色。
- **T 轴·标签词表：0 违规、但发现 44 页只有 1 个标签**。全部标签都是小写英文（无大小写/中文/超长违规）——词表干净。另有 44 页 `tags` 只有 1 个（多为章 README 与索引页），低于模板「2–5 个」的建议。判定：这是**软性撰写建议、非读者可见缺陷**（GitBook 标签索引单标签照常工作），为 44 个索引页硬凑第二个标签属**为凑规范而改内容**，**不动**，仅在此留痕。
- **本轮未改任何页面内容**（C 全绿、T 是软规范否决），仅新增此记录。**推送状态未变**：第 17–35 轮仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`。
- **阶段性诚实判断**：本轮起，新开的轴已连续多轮以「全绿或判据/软规范否决」收口——静态可测的高价值短板确已枯竭。真正卡住闭环的仍是那一次推送。

## 2026-09-22（第 34 次）提示卡一致性：删掉 44 页 hint 里重复 frontmatter 的「标签」行（经操作者定夺）

本轮先探「内容深化」的两个候选，都据实否决，再落到一处真实的一致性缺陷：

- **候选①否决**：[推理经济学与部署形态](../16-ai-infrastructure/inference-economics-deployment.md) 被「无 `$$`」误判为缺公式——实则它把成本模型写进了 ```text 块 + 一段可运行 Python，比 KaTeX 更实用；再加 `$$` 是重复灌水，**不动**。
- **真实缺陷**：132 张知识页里 **44 张**的 info-hint 内塞了 `**难度**` 与 `**标签**` 两行，而 [知识页模板](../14-templates/knowledge-template.md) 规定 hint 只放「一句话」。其中 **`**标签**` 行纯粹重复了 frontmatter 的 `tags`**（如 memory-types 既有 `tags: [memory, basics]` 又在 hint 里写 `` **标签**：`#memory` ``），是冗余；`**难度**` 则是模板未规定、但对读者导航有用。
- **产品级取舍 → 已征询操作者**：统一 hint 版式属「改版式框架」，且删难度会丢有用信息、全页加难度又是一百多页工程，故未擅动；经询问，操作者定**只删重复的「标签」行、保留「难度」**。
- **执行与断言校验**：脚本仅匹配「缩进的 `**标签**：` 行」并**先断言其位于 `{% hint %}…{% endhint %}` 内**才删——dry-run 报 44 文件 / 44 行、hint 外 0 处；实改后复测 **围栏配平 0 破、hint 开合配对 0 失衡、hint 内残留「标签」行 0**；抽查 diff 确认只删了那一行、难度与其余内容原样保留。这 44 页 `updated` 本就是 09-22（当天确有改动），无需回填。
- **README 统计不动**：提示卡张数、页数、来源等计数均不受影响（只删 hint 内一行冗余文本），无口径变化，不硬凑。
- **未做项 / 阻塞（诚实）**：第 17–34 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查（含 hint 在 GitBook 里的真实渲染）仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 33 次）内容深化（按质量信号，不按字数）：给检索调优页补上它点名却没写的四个指标公式，并修掉 README 一处自相矛盾

操作者定方向「内容深化」。先做诚实体检：把 `type: knowledge` 页按中文字数排最薄的——**最薄的也有 909 字，且普遍带 公式+代码+Mermaid**。逐张点开 [langchain](../09-frameworks/langchain.md)、[computer-use-2026](../18-frontier-2026/computer-use-2026.md) 确认：它们是**该短的框架/前沿页、结构完整**，硬加字数就是灌水。于是换一条**质量信号**去定位真缺口：**哪些概念页只给定性描述、却漏了该页点名指标的数学**。

- **真缺口命中**：[RAG 检索质量调优](../06-memory-rag/retrieval-quality-tuning.md) 通篇点名 RRF、Recall@k、MRR、nDCG，却**一个公式都没给**——一页讲「怎么衡量检索」却没有度量的算法，是实打实的深度缺陷。
- **补 4 个标准公式**（新增「关键指标的数学」小节）：RRF $$\sum 1/(k+\text{rank})$$、Recall@k、MRR、nDCG@k（含 DCG 折扣式），每条配一句「它在优化什么」的白话，且都嵌进原漏斗语境、非孤立堆公式。
- **KaTeX 真实渲染校验**（不是肉眼猜）：临时装 `katex@0.18.7`，把该页 3 个 `$$…$$` 展示块 + 3 处行内 `$…$` 逐个 `renderToString(throwOnError:true)`——**6/6 通过、0 解析失败**；`$$` 定界符成对（6 个）、围栏配平、原 Mermaid 块未受影响。
- **顺带修掉一处 README 自相矛盾**：英文首屏（第 18 行）写「100 of them carrying formulas」，而统计条目（第 89 行）写「104 页含公式」——同一指标两个数。本轮给上页加了公式，含公式页 **+1**，按「对已验证基线套增量」的房规把两处**统一到 105**（未用一次性重算覆盖绝对值）。
- **诚实记一条口径噪声**：我用「剥围栏+剥行内代码后数 `$$`」的口径重算，得 **104**（改前 103、改后 104），与第 17 轮验证基线 104 差 1——属记忆里点名的「统计口径敏感、一次性重算复现不了基线」的已知 ±1 漂移，故仍按基线套增量到 105，并在此留痕，待下次整体统计复核时对齐。
- **README 其余计数不动**：页数/图数/Mermaid/图注/来源均未变（本轮只在既有页内加公式，未新增页或图）。
- **未做项 / 阻塞（诚实）**：第 17–33 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`；KaTeX 的**线上真渲染**也待推送后一并目检。

## 2026-09-22（第 32 次）15 轮改动后的链接/导航回归闸门：0 断链、0 悬空、0 漏收——并拒绝把「按设计的前向链」误当孤儿去修

第 24–31 轮连改了十几个文件（补图注、加互链、插 3 张新页、动 SUMMARY/导读/术语表）。这轮把目标点名的「断链与孤儿页」轴当**回归闸门**整体重跑一遍，确认没在批量编辑里引入新缺陷。结论：**全绿，无回归**。

- **① 站内相对 `.md` 链接：0 断链**（解析每个链接目标、按所在目录归一化后比对文件树，行内代码里的示例已排除）。
- **② SUMMARY 指向的文件：0 悬空**（每条导航都能落到真实文件）。
- **③ 已存在却未进 SUMMARY 的正文页：0 漏收**——即**每一张内容页都在导航树里，没有真正「不可达」的孤儿**。
- **诚实记录一条「没去动」的判据**：严格量「正文入链为 0」的页有 23 张（多为 13-resources 的资源卡、12 章应用页、第 20 轮知识页）。但它们在 ③ 里已确认**都在 SUMMARY + 章导读里可达**，而本手册的 `相关知识点` 约定本就是**向前指**（第 18 轮已定调：不拿「双向对称」当缺陷去修）。给这些叶子页硬塞回链就是**为凑指标改内容**，故**判据过严、不采纳**，不动。
- **本轮未改任何页面内容**（三条轴全绿、第四条是我主动否决的假想规则），仅新增此记录。**推送状态未变**：第 17–32 轮仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 31 次）整合轴续：把第 27–29 轮三个新概念登记进术语表

承第 30 轮的整合轴，换一个没量的子维度：**新页的核心术语有没有进 [术语表](../15-glossary/README.md)**。术语表是全书的规范词条索引，一个新概念若只在正文出现、词条表里查不到，读者速查时就漏了它。量：`Sleep-time / 有效上下文 / context rot / test-time compute / 推理预算` 在术语表里**全部 0 命中**——三张新页一个词条都没登记。

- **补 5 条词条**（按主题插进对应分组，非灌水、是把已写进正文的概念登记回索引）：模型与训练组加 **有效上下文 / 上下文腐化 / 测试期计算 / 思考预算**，记忆与检索组加 **睡眠时计算**；每条都配英文与一句白话解释，格式与既有行一致。术语表 `updated` 由 09-20 回填为 09-22（当天确有读者可见改动）。
- **校验**：术语表全表**列数一致 0 破坏**（新行与表头同为 3 列）、围栏配平；5 条新词条逐条断言在表内命中。
- **README 统计不动**：术语词条数不是 README 的任何计数项，且未新增页/图/来源，无口径变化——不硬凑。
- **未做项 / 阻塞（诚实）**：第 17–31 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 30 次）整合轴·新页是否真被织进书里：抓出并修掉 2 个「近孤儿」新页

第 27–29 轮连着加了 3 张新页。本轮立一条**整合轴**（不是内容缺陷，是导航质量）：新页若只被 `SUMMARY.md` 和章导读列到、却没有任何**同章正文页**链向它，读者在相关页里就永远「发现」不了它——等于半孤儿。量各新页的**正文入链**（排除 SUMMARY、changelog、章 README、自身）：

- **睡眠时计算**：正文入链 3 条（长上下文页、推理预算页、ch06 导读）——整合良好，不动。
- **长上下文退化**：正文入链 **0**（仅 ch06 导读）——近孤儿。
- **推理预算与测试期计算**：正文入链 **0**（仅 ch04 导读）——近孤儿。
- **修复（织回正文，非灌水）**：给两张近孤儿页各补 **2 条来自最相关正文页的 `相关知识点` 入链**——长上下文退化 ← [上下文工程](../06-memory-rag/context-engineering.md)（正是「为什么别贪多」的互补面）与 [RAG 检索质量调优](../06-memory-rag/retrieval-quality-tuning.md)（Top-k 预算/lost-in-the-middle）；推理预算 ← [Chain of Thought](../04-prompt-reasoning/chain-of-thought.md) 与 [Tree of Thoughts](../04-prompt-reasoning/tree-of-thoughts.md)（这两页本就一句带过 test-time compute，现给出去处）。断言复测：两页正文入链各 **0 → 2**。
- **校验**：4 个被改的正文页围栏配平（0 破坏）、`updated` 仍为 2026-09-22（当天确有读者可见改动）、新链接目标文件均存在。**README 统计不动**——本轮只加正文互链，未新增页/图/图注/来源，任何计数口径都无变化，不硬凑数字。
- **未做项 / 阻塞（诚实）**：第 17–30 轮提交仍未推上线（本沙箱后台 `git push` 无法完成 GitHub 交互式凭据），目标第 (5) 步线上抽查仍未闭环，需操作者本地 `git push origin main`。

## 2026-09-22（第 29 次）内容增强第三页：新增「推理预算与测试期计算」（ch04）

继续补真空。扫描发现 `thinking budget|reasoning effort|test-time compute|思考预算` 只在 [Chain of Thought](../04-prompt-reasoning/chain-of-thought.md) 与 [Tree of Thoughts](../04-prompt-reasoning/tree-of-thoughts.md) 各**一句带过**，**无专页**——而「把『模型该想多久』变成可调算力旋钮」正是 2026 从 train-time 转向 test-time scaling 的核心，也是 Agent 每步都要做的资源分配决策。据此在 ch04 补一页，并与第 28 轮的睡眠时计算配成镜像（一个管查询当口值不值得现场多想，一个管把算力挪到查询前）。

- **新增 1 页**：[推理预算与测试期计算](../04-prompt-reasoning/test-time-compute-reasoning-budget.md)。三种「多花算力换准确率」的形态（内化思考链 / 重复采样 / 迭代修正）统一为同一本质、不同旋钮；effort 档位·思考预算·采样数·修正轮数·升级式路由的**跨厂商旋钮表**；专设一节讲**对 Agent 的特殊含义**（机械步别 overthink、推理模型未必擅长工具调用与严格 JSON、预算要在多步循环里逐环设、测自己的算力-准确率曲线找拐点）。
- **本轮主动吸取第 28 轮教训**：新图一开始就画成**单列决策流**（一个「值得多想吗」判定 + 一个「结果达标吗」升级回环），避免四路扇出超宽；Edge headless 实测自然宽度 **580px**（< 1120），一次到位无返工。
- **过全套房规校验**：真解析器（mermaid 11.14.0，与线上同版本）**全站 186 块 0 失败、0 超宽**；新图**真实渲染目检**——ch04 天蓝主题（#0284C7）、两个菱形判定与全部节点文字清晰无裁切。正文中文 **1513 字**（行状态机剥围栏与行内代码后计，已避开第 28 轮那个 DOTALL 少算的判据坑）；frontmatter 顺序、围栏配平、`{% hint %}` 配对、页内相对链接均断言通过。
- **引用零猜测**：3 条 arXiv 逐条 `curl` 取回真实 `<title>` 比对——`2501.19393`=s1: Simple test-time scaling、`2407.21787`=Large Language Monkeys、`2501.12948`=DeepSeek-R1，全部命中；其中 s1 与 Large Language Monkeys 是本书首次引用（R1 已在 15 页出现）。
- **README 统计按实测增量对齐**：页 **192→193**、Mermaid **185→186**、读者可见图注 **179→180**（Mermaid 带图注 137→138）、含参考资料页 **149→150**、去重一手来源 **326→328**、配图 **225→226**；**含公式页不变**。中英首屏与「全书 Mermaid 校验」条目一并同步，脚本复查无残留旧值。
- **导航接入**：新页已加入 `SUMMARY.md` 与第 04 章导读列表。
- **未做项 / 阻塞（诚实）**：第 17–29 轮提交**均已在本地但仍未推上线**——本沙箱后台 `git push` 无法完成 GitHub 交互式凭据弹窗（已两次实测确认）。目标第 (5) 步线上抽查对第 17–29 轮仍未闭环，需操作者在可见终端执行一次 `git push origin main`。

## 2026-09-22（第 28 次）内容增强第二页：新增「长上下文退化与有效上下文窗口」，并记录一次「自检抓到自家新图超宽」

延续第 27 轮转入的内容增强。再扫一处真空：`context rot|上下文腐化|长上下文退化` 全站 **0 命中**——而「标称 128K/1M ≠ 可用长度、塞得越多越易漏读带偏」是 2026 长上下文模型最常被误用的一点，第 06 章有 context-engineering 与检索调优，却没有一页专讲「**为什么不能贪多**」。据此新增一页。

- **新增 1 页**：[长上下文退化与有效上下文窗口](../06-memory-rag/long-context-degradation.md)。四条退化机制（注意力稀释 / Lost-in-the-Middle 的 U 形 / 位置外推失配 / 干扰项敏感）+ 怎么量（RULER 式合成基准，别用大海捞针自欺，报「达性能门槛的最大长度」而非「可输入上限」）+ 一条「少塞·压好·摆对·外置」的治理漏斗；与上下文工程、检索调优、记忆压缩、睡眠时固化四页显式串联不重复。
- **本轮最该记的一笔——自检抓到自家新图超宽**：新图初版把四条对策从同一节点**扇出成四列并行**，Edge headless 实测自然宽度 **1321px > 正文列宽 1120px**，线上会被缩到看不清。改成**自上而下的单列漏斗**后实测 **358px**，并同步改了图注（「四条并行」→「依次收窄」）。这正是目标第 (1)(3) 步要的「Mermaid 自然宽度 vs 列宽」量测在**新内容上真实兜住了一次回归**，不是走过场。
- **过全套房规校验**：真解析器（mermaid 11.14.0，与线上同版本）**全站 185 块 0 失败、0 超宽**；新图 Edge headless **真实渲染目检**——分章绿色主题、单列漏斗、两条虚线边（标称不等于可用 / 回灌）文字无裁切。正文中文 **1650 字**（用**行状态机**剥围栏与行内代码后计；此前一版计数脚本的围栏正则 `^\1.*$` 在 DOTALL 下误吞到文件尾、把字数少算成 699，已改用状态机复核——判据 bug，非内容问题）。frontmatter 顺序、围栏配平、`{% hint %}` 配对、页内相对链接均断言通过。
- **引用零猜测**：3 条 arXiv 逐条 `curl` 取回真实 `<title>` 比对——`2404.06654`=RULER、`2307.03172`=Lost in the Middle、`2310.06839`=LongLLMLingua；过程中还**挡下一个记错的编号**（`2502.00001` 实为无关的 PageRank 硬件论文，未采用）。其中仅 RULER 是本书首次引用。
- **README 统计按实测增量对齐**：页 **191→192**、Mermaid **184→185**、读者可见图注 **178→179**（Mermaid 带图注 136→137）、含参考资料页 **148→149**、去重一手来源 **325→326**、配图 **224→225**；**含公式页不变**。中英两处首屏与「全书 Mermaid 校验」条目一并同步，脚本复查无残留旧值。
- **导航接入**：新页已加入 `SUMMARY.md` 与第 06 章导读列表。
- **未做项 / 阻塞（诚实）**：第 17–28 轮提交**均已在本地但仍未推上线**——本沙箱后台 `git push` 无法完成 GitHub 交互式凭据弹窗（已两次实测：`ls-remote` 不变、`git-credential-helper-sel` 常驻）。目标第 (5) 步线上抽查对第 17–28 轮仍未闭环，需操作者在可见终端执行一次 `git push origin main`。

## 2026-09-22（第 27 次）转回内容增强：新增「记忆固化与睡眠时计算」页，填一处真空白

静态缺陷自检到第 26 轮已连续证伪，经操作者定方向，本轮**从「找缺陷」转回「补内容」**（同第 20 轮的产品级取舍）。先做覆盖度扫描定位真空：`sleep-time|consolidat|记忆固化|离线整理` 全站 **0 命中**——而 Sleep-time Compute（Letta, 2025）恰是 2026 前沿「把测试期算力挪到空闲期」的代表性范式，第 06 章记忆族（memory-types / memory-compression-forgetting / retrieval-quality-tuning）都缺这一环。据此新增一页。

- **新增 1 页**：[记忆固化与睡眠时计算](../06-memory-rag/sleep-time-memory-consolidation.md)。以「给 Agent 的记忆做物化视图」为主线，讲清三件事——**预推导 / 固化（情景→语义）/ 反思与重建索引**；专设一节讲**触发策略（定时 / 事件驱动 / 成本预算）与失效粒度（依赖追踪）**，点明这本质是缓存一致性问题；与检索调优、上下文工程、记忆压缩三页显式串联，避免重复。
- **过全套房规校验**：真解析器（mermaid 11.14.0，与线上同版本）逐块 parse，**全站 184 块 0 失败**；新图自然宽度实测 **477px**（远低于正文列宽 1120），并用 Edge headless **真实渲染目检**——分章绿色主题正确、六类节点（含柱状存储、六边形睡眠期、虚线失效回灌边）文字无裁切。正文中文 **1171 字**（剥围栏与行内代码后计），远超 900 门槛；frontmatter 四字段顺序、围栏配平、`{% hint %}` 配对、页内相对链接均断言通过。
- **引用零猜测**：3 条 arXiv **逐条先 `curl` 取回真实 `<title>` 比对**——`2504.13171`=Sleep-time Compute、`2304.03442`=Generative Agents、`2310.08560`=MemGPT，全部命中；其中仅 `2504.13171` 是本书首次引用。
- **README 统计按实测增量对齐**：页 **190→191**、Mermaid **183→184**、读者可见图注 **177→178**（其中 Mermaid 带图注 135→136）、含参考资料页 **147→148**、去重一手来源 **324→325**、配图 **223→224**；**含公式页不变**（本页无 `$$`）。中英两处首屏数字与「全书 Mermaid 校验」条目一并同步，脚本复查无残留旧值。
- **导航接入**：新页已加入 `SUMMARY.md` 与第 06 章导读列表，不制造站内孤儿。
- **未做项 / 阻塞（诚实）**：第 17–27 轮提交**均已在本地但仍未推上线**——本沙箱内后台 `git push` 无法完成 GitHub 交互式凭据（GCM）弹窗，已两次实测确认（`ls-remote` 不变、`git-credential-helper-sel` 常驻）。目标第 (5) 步「线上同步后抽查」对第 17–27 轮仍未闭环，需操作者在可见终端执行一次 `git push origin main`。

## 2026-09-22（第 26 次）四条回归轴针对「第 20 轮新增 3 页」复检：全部干净，并纠正/退役了两个会误报的判据

第 20 轮加过 3 张新图与若干页，第 21 轮的全站 Mermaid 宽度证伪是在那之后，但**分章配色指令、代码围栏语言标签、提示卡配对、参考资料齐备性**这四条更细的轴没专门回归过。本轮补上，结论：**无内容缺陷**；两条轴的报警都是判据自身误报——按房规改判据、不动正当内容。

- **G1·183 张 Mermaid 是否都带 `%%{init}%%` 章色指令：0 缺失**。第 20 轮补的 3 张图也都带分章配色指令，无「裸 Mermaid」漏网。
- **G2·内容页是否残留无语言标签的裸代码围栏：0**（围栏状态机逐块判定，非 `%2` 计数）。
- **G3·提示卡 `{% hint %}` / `{% endhint %}` 配对：初报 2 → 判据修正后 0**。changelog 与 contributing 里的 `{% hint style="info" %}` 全是**写在行内反引号里教写法**的示例（贡献指南在讲规范、更新日志在描述某轮改动），我的计数没先剥行内代码/围栏就误配。这正是记忆里点名的「别拿正则硬扫 hint 块」老坑——**先剔代码再配对，0 失衡**。不动那些正当示例。
- **G4·「有引用就得有参考资料」：判据不成立，退役**。6 个 lab 页被报「引用了来源却无 `参考资料` 小节」，但触发原因是我的正则把 lab 指向**源码的 GitHub blob 链接**（`github` 命中）当成了学术引用；lab 页按体例用 `前置阅读` 内链指回机制章，本就无需 `参考资料` 列表。按第 18/21 轮纪律：**新轴先问「这规则书里真有吗」，答案没有就退役，不拿它改内容**——故不据此给 lab 页硬塞参考小节。
- **本轮未改任何页面内容**（G1/G2 全绿、G3/G4 是判据问题），仅新增此记录。**推送状态未变**：第 17–26 轮提交仍卡在 GitHub 交互式凭据（本沙箱内后台 `git push` 无法完成 GCM 弹窗，已实测确认），需操作者在可见终端 `git push origin main`；线上抽查（目标第 (5) 步）待推送落地后闭环。
- **诚实评估（阶段拐点）**：第 21/22/23/25/26 轮连续证伪、第 24 轮是上一次真实缺陷（会塌成文本的表格 + 缺图注）。目标列举的量测维度（Mermaid 宽度/解析、断链/孤儿、frontmatter、薄页密度、统计口径、线上渲染）已系统性覆盖完毕。**在不推送的前提下，静态可测的高价值短板已趋近枯竭**——继续开轴多是否证伪；建议先推送落地、跑完线上抽查，再决定是否转向「内容增强」而非「缺陷自检」。

## 2026-09-22（第 25 次）四条新轴全部证伪：表格列数、空链接文本、页内重复锚点、Mermaid 纵向高度——并诚实记录一次「判据自身」的假阳性

延续第 24 轮「静默破坏渲染」这条线，本轮开四条**没量过的新轴**去证伪。结论：**没有一条量到真实内容缺陷**，但过程里抓出并纠正了一个**判据自身的假阳性**（不改内容，只修尺子）。这几条轴以后不必重复试，故记录负结果。

- **T 轴·表格列数一致性：278 张表 / 0 缺陷**。逐页用状态机跳过代码围栏后，把每个「表头 + 分隔行」识别为表，按未转义 `|`（且不在行内代码里）切格，比对每个数据行与表头列数、分隔行列数是否一致（列数不齐会让 GitBook 整行错位）。**并做负对照**：故意注入一行 2 格的坏表，判据准确报出 `mismatch` —— 证明 0 不是「尺子坏了」而是「确实干净」。
- **L 轴·空/纯空白链接文本：0（且纠正了一次误判）**。初版脚本先把行内代码整体剥离再匹配链接，于是 `[`openai/codex`](url)`、labs 页的 `[`labs/lab1_react.py`](url)`（用行内代码当链接文字，全站合法且常见）被误报成 7 条「空链接」。这是**判据错，不是内容错**——按第 18/23/24 轮纪律，改的是尺子（匹配链接时不再预剥行内代码），不是去动那些正当写法。收紧后**真空链接 0**。
- **S 轴·单页内重复标题锚点：0**。同页两个标题算出同一 slug 会让页内 `#锚点` 跳错；全库 0 处（标题文字足够分散）。
- **H 轴·Mermaid 纵向高度（此前只量过宽度）**：把全站 183 块用**与线上同版本**的 mermaid 11.14.0 一次性 Edge headless 渲染，回收每块 `viewBox` 的宽和高。**宽度回归**：最宽仍 1116px、超 1120 的 0 张（确认第 24 轮补图注未波及任何图，与 README「最宽 1116/1120」一致）。**高度**：最高 1298px（lab6 护栏流程竖排图），超 2500 的 0 张——因为宽度都 < 正文列宽，GitBook 不缩图、文字不糊，只是长图需多滚一段，属可接受的竖排定调，**不是缺陷**。
- **本轮未改任何页面内容**（四条轴均证伪，唯一改动是临时判据脚本）；仅新增此记录。**推送状态未变**：第 17–24 轮共 8 笔提交仍卡在 GitHub 交互式凭据，需操作者 `git push origin main`；线上抽查（目标第 (5) 步）对第 17–25 轮仍待推送落地后才能闭环。

## 2026-09-22（第 24 次）一条新轴「图注段落隔离」：补 12 张缺图注的内容图，顺带揪出 2 张会整表塌成纯文本的表格

前三轮（21/22/23）都在证伪、没有可修缺陷。这轮按操作者「开新一轮更严的自检轴」的指示，把镜头对准**图注**这条房规：GitBook 会剥掉内容图片的 alt，所以 [风格指南](../14-templates/style-guide.md) 硬性要求每张内容图下方必须有一句 `*《图：…》*` 读者可见图注。据此立了两条能量化的轴——**C1 内容图是否都有下方图注**、**新轴·图注段落隔离**（图注行与相邻内容之间必须空一行，否则 CommonMark 会把它们并成同一段）。

- **C1：44 张内容图里 12 张缺下方图注 → 补至 0**。这 12 张全是早几轮加的真实产品截图/工具界面 SVG（MCP Inspector、AutoGen Studio、Dify、Langfuse/Phoenix/LangSmith、OpenHands、Open WebUI 等），当时只写了图前引导语与 `*来源：…*`，漏了房规点名的那句 `*《图：…》*`。逐张补了**带具体机制/取舍**的图注（各自句式不重样，例如把「openpyxl 没装，改用 stdlib zip/XML 解析」点成「环境受限时会自己换路、说明理由」的分水岭）。断言级验证：`r24_c1img.py` 复跑 `images MISSING 图注: 12 → 0`。
- **新轴·图注段落隔离：全库扫出 7 处候选，其中 3 处是真缺陷、4 处是我这条轴自己的假阳性**。真缺陷是图注下一行直接紧贴内容、中间没空行：① [评估章首页](../10-evaluation-safety/README.md) 图注下方紧贴一张 `![]()` 图片——GFM 会把图片当内联塞进图注同一段，两张图糊成一段；②③ [前缀缓存](../16-ai-infrastructure/prefix-cache-context-engineering.md) 与 [沙箱环境](../16-ai-infrastructure/sandbox-execution-environments.md) 两处，图注下方**直接就是表格**——**GFM 表格不能打断段落**，这两张表在 GitBook 上会整个塌成一串 `| 隔离层 | 原理 |` 纯文本、根本不渲染成表格（这是本轮最值钱的一条：不是排版美观问题，是表格消失的功能性 bug）。三处各补一个空行修好。**4 处假阳性按纪律没去「为绿指标」乱改**：图注下方是 `##` 标题 / `>` 引用块 / ```` ``` ```` 代码围栏——这三类在 CommonMark 里本就能合法打断段落，不会合并；我改的是**判据**（把合法打断符加进白名单），不是内容。
- **修复前后各渲染一次坐实**（GFM `markdown`+tables 扩展，真实渲染而非肉眼猜）：同一段「图注＋表格」，**补空行前** 输出 `contains <table>? False`（表格被吞进段落），**补空行后** `True` 且图注独立成 `<p><em>…</em></p>`。这条满足目标第 (3) 步「至少一张真实渲染图目检」。
- **README 统计按实测增量对齐**：读者可见图注 **165 → 177**（口径：42 张内容图全部配注 + 183 张 Mermaid 里 135 张带图注；本轮只加图注文字，未新增任何图片，故配图数 223、页 190、Mermaid 183 全不变）。顺带修正 [docs/README.md](../README.md) 里「每张 SVG/截图下方都写了一句」这句此前对 12 张并不成立的表述——现在字面为真。
- **回归闸门**：本轮改的 13 个文件用围栏状态机逐个判 **13/13 BALANCED**；全树 192 个 md 的 frontmatter 四字段顺序 **0 例外**；**未触碰任何 Mermaid 块**，故第 21 轮「全站 183 块真解析器 0 失败、最宽 ≤1116px」结论对本提交依然成立、无需重跑。
- **未做项 / 阻塞（诚实）**：第 17–24 轮的提交仍卡在 GitHub 交互式凭据（GCM）授权，需操作者本地 `git push origin main` 并批准弹窗；线上同步后对「补了图注的页」和「修了表格的页」的渲染抽查（目标第 (5) 步）仍待推完才能闭环——尤其那两张此前会塌成文本的表格，值得上线后亲眼确认已成表格。

## 2026-09-22（第 23 次）推送前结构闸门：把第 17–22 轮这一批改动整体复检一遍，并修掉一个「会骗人」的围栏配平判据

第 21、22 两轮审计无可修缺陷后，本轮不新增页面，而是对**待推的第 17–22 轮整批**跑一道整体结构闸门（房规要求「批量改文件后必须跑结构校验」），顺带纠正一处量测口径缺陷。全程**未改动任何页面正文/图**，仅新增此记录。

- **192 个 md 整体过闸**：frontmatter 四字段（`tags→type→status→updated`）顺序 **0 违例**；无 frontmatter 的仅 `docs/SUMMARY.md`（导航）与 `docs/.gitbook/assets/screenshots/MANIFEST.md`（资产清单）两个——本就不该有，属设计白名单，非缺陷。
- **纠正一个假阳性判据（重要，记下来别再用错）**：旧「围栏配平」用 ```` ``` ```` **出现次数的奇偶**来判，本轮它把 `14-templates/style-guide.md`、`99-about/contributing.md` 报成「不配平」。但换用**CommonMark 状态机**（行首 3+ 个 `` ` `` 或 `~` 开栏；闭栏须同字符、长度≥开栏、且其后无 info 串）逐行配对后，两文件**均配平**——假阳性来自文件里把 ```` ``` ```` 当作**行内代码示例**写的教学内容（style-guide 13 次 = 5 对真围栏 + 3 处行内示例；contributing 0 对、3 处全在行内代码里）。**奇偶判据既会误报、也会漏报真正的错配**（数量凑成偶数的错误嵌套），已改用状态机为准，并把这条固化进维护口径。此即第 19 轮「宽松扫描误报占位符」教训在围栏维度的翻版：**判据先用已知正/负样本标定，再上库**。
- **未做项 / 阻塞（诚实）**：第 17–23 轮共 **7 笔提交（`49d1c05`→本轮）仍只在本地**。本轮实测：只读 `git ls-remote` 可达、线上 `llms.txt` 返回 200 但**尚未收录**第 20 轮的三页（`git ls-remote` 仍停在上一个已推的 `e2acc5c`）——即 `git push` 仍未落。写推卡在 GitHub 交互式凭据（GCM）弹窗，后台 shell 应答不了（曾观测到 `git-credential-helper-selector` 驻留、push 日志空、远端不动），需操作者本地执行 `git push origin main` 批准弹窗。落库后我再补线上渲染抽查以闭环第 (5) 步。

## 2026-09-22（第 22 次）六条更严的渲染/结构轴：全站表格、图片引用、提示卡词表逐一坐实，仍无可修缺陷

按操作者「开新一轮更严自检轴」的方向，本轮设计 6 条此前没量过的轴（都是**会真影响线上渲染**的：表格错位、破图、提示卡样式失效），每条先**证伪标定**（该抓的抓到、模板里的反面示例不误报）再上库。结论：**渲染/结构五轴全 0，唯一命中的是两条已知的模板教学示例与两个品牌图标源文件，均非缺陷**。

- **T1 Markdown 表格列数不齐：0**。剔除代码围栏与行内代码后，把每段连续的 `|…|` 行当一张表，逐行比对单元格数是否等于表头——全站 **0 处**行列错配（GitBook 表格渲染不会因某行多/少一列而塌陷）。
- **A2 引用的图片在磁盘不存在（破图）：0 真缺陷**。全站非模板页共 **44 处** `![]()` 图片引用，逐条解析相对路径查文件是否存在——**0 处指向缺失文件**。（初版误报 2 处，全在 `14-templates/style-guide.md`：一处是 `` `![alt](…)` `` 行内代码里的**讲格式的示例**、一处是提示卡里教「这样引用才保留动画」的 `![](../.gitbook/assets/xxx.svg)` **负样本**，都不该当真图；据此把「剔除行内代码 + 排除模板」固化进脚本，二次量测得可信的 0。）
- **D1 图片引用跳出 `docs/` 内容根（线上必 404）：0**。与第 18 轮那条「跳出内容根的链接」同源风险，这次专查图片：44 条相对图片引用解析后**全部落在内容根内**。
- **L1 空/坏链接目标 `[text]()`：0**。
- **R1 提示卡 `style` 超出 GitBook 合法集合：0**。全站 `{% hint style=… %}` 仅用到 `info`(189)/`warning`(19)/`tip`(10)，均在合法词表内，不会退化成默认样式。
- **A1 仓库内未被任何 md 引用的资产：2 个，刻意保留**。`.gitbook/assets/` 下 `violet-icon.svg` 与 `violet-icon-badge.svg`（手绘紫罗兰品牌图标，其一 aria 标注「适合 favicon」，`c566c97` 引入）不被任何页面正文引用——因为它们是**站点 Logo/favicon 的源文件**，GitBook 的站标在 dashboard 设置、正文不引用（见第 16 轮「2 张 SVG 作站标不进正文」口径）。删除等于丢掉品牌图标源头，属**产品级取舍**，按「不为凑指标删内容」一律保留，仅在此登记待操作者定夺。（另有 `.gitkeep` 目录占位，属设计。）
- **退役一条不成立的轴（H1 vs SUMMARY 标题一致）**：本想查「页面 H1 与 `SUMMARY.md` 导航标题是否一致」，但本书导航对章导读页**故意**写「本章导读」、而页面 H1 是章节全称——不一致是约定而非缺陷，拿它开工就是为凑指标改内容，故**不立此轴**（延续第 18 轮「新轴先问这规则书里真有吗」的判据）。
- **回归校验**：本轮**未改动任何页面正文/Mermaid/图片**，仅新增此记录；192 个 md 文件 frontmatter 闭合、围栏配对照旧（第 17 轮口径）。
- **未做项 / 阻塞（诚实，与第 20/21 轮同）**：第 17–22 轮共 **6 笔提交（`49d1c05`→本轮）仍只在本地**，未推上线——推送卡在 GitHub 交互式凭据（GCM）授权：本轮实测只读 `git ls-remote` 可达（首试遇 schannel TLS 握手瞬时失败、重试即通），但写 `git push` 挂起且 `git-credential-helper-selector` 进程驻留等弹窗，后台 shell 无法应答，遂停掉自起的挂起进程。流程第 (5) 步「线上同步后抽查」对第 17–22 轮仍未闭环，需操作者本地 `git push origin main` 并批准凭据弹窗。

## 2026-09-22（第 21 次）全站 183 张图一次性离屏渲染 + 四条新审计轴：仍无可修缺陷

第 20 轮补了三页后，本轮先把「Mermaid 自然宽度 vs 正文列宽」这条主渲染轴从**逐页抽测**升级为**全站一次性实测**，再叠加四条没量过的结构轴去证伪。结论：**五路全绿，没有为凑指标而改的内容**；唯一变化是把这条更严的量测手段固化下来。

- **全局宽度回归：183/183 全部渲染成功，超宽 0 张**。把 `docs/`（除 14-templates）里全部 183 个 Mermaid 块抽进一张 HTML，用 Edge headless + 线上同版本 `mermaid@11.14.0` 一次性 `run` 渲染，逐块读回 SVG `viewBox` 宽：**0 块渲染失败**（等于全站解析器 0 失败的更强证据），**0 块 > 正文列宽 1120px**，最宽 **1116px**（12 章 README 的一条横向流水线），30 张落在 1000–1116px 的窄带内但均未越线。第 20 轮新增的三张（383 / 987 / 709px）在全局重测里依旧在阈内，**无超宽回归**。README 首页「最宽 1116px / 1120px」口径与本次实测**逐字吻合**。
- **B1 跨文件锚点失效：0（且此轴为空集）**。全站相对链接里 `](xxx.md#anchor)` 形态命中 **0 条**——本手册跨页引用一律指向文件、不带页内锚点，所以这条轴当前无可测对象；记下空集是为将来若引入 `#anchor` 时有基线。
- **B2 frontmatter 标签词表漂移：0**。抽出全站 `tags:` 用词做词频，新增三页沿用既有词（`llm/training/agents`、`engineering/safety/agents`、`rag/memory/advanced`），未引入孤儿新标签，四字段顺序 `tags→type→status→updated` 全站仍 **0 例外**。
- **B3 知识页房规小节缺失：0**。对 `type: knowledge` 页逐一核 `概念速查 / 常见误区 / 参考资料 / 相关知识点` 四段齐全，三张新页与既有页同样过关。
- **B4 SUMMARY 悬空条目：0**。`SUMMARY.md` 每条链接的目标 `.md` 均真实存在于 `docs/` 内容根内，无指向已删/改名文件的死条目。
- **量测手段自身的一个坑（记下来避免重跑）**：把 183 段 Mermaid 源码嵌进 HTML 时，源码里的 `<br/>`、`<`、`>` 会破坏 DOM、`&` 需转义；且聚合脚本里 `out.join('\n')` 若由 Python 三引号写出，会把 `\n` 变成**真换行**塞进 JS 字符串字面量 → 整段脚本语法错、连 STARTED 标记都不出现，表现为「0 张 SVG 渲染」的假阴性。两处都修好后 183/183 才如实渲染。
- **未做项 / 阻塞（诚实，与第 20 轮同）**：本轮**未改动任何页面内容**，仅新增此记录。第 17–20 轮的提交连同本轮**均只在本地**，尚未推上线——推送卡在 GitHub 交互式凭据（GCM）授权，只读 `git ls-remote` 可达、写 `git-receive-pack` 挂起，非代码问题。流程第 (5) 步「线上同步后抽查」对第 17–21 轮仍未闭环，需操作者本地执行一次 `git push origin main` 并在弹窗批准凭据后方可闭环。

## 2026-09-22（第 20 次）从「修缺陷」转向「补内容」：新增 3 张知识页，填三处真空

第 19 轮五轴全绿、无可修缺陷后，经操作者定方向，本轮**从缺陷自检转向内容增强**——这是产品级取舍，不是补漏。先做覆盖度扫描定位真空：`用轨迹微调 Agent`（全站 0 命中）、`Agent 失败模式图鉴/调试手册`（仅散见于可观测性页）、`RAG 检索质量调优`（rerank/混合检索/切块散在 5+ 页却无专页）。据此新增三页。

- **新增 3 页**：[用轨迹微调 Agent](../03-llm/agent-traj-finetuning.md)（轨迹定义与 loss masking、四种数据来源、SFT→拒绝采样→DPO/RL 三路线、工具泛化）、[Agent 失败模式图鉴与调试手册](../11-engineering/agent-failure-playbook.md)（六类失败按「症状→根因→对策」组织 + 分诊决策图）、[RAG 检索质量调优](../06-memory-rag/retrieval-quality-tuning.md)（切块→混合召回→重排→自我纠错→评估的调优漏斗）。
- **每张都过全套房规校验**：真解析器（mermaid 11.14.0，与线上同版本）逐块 `parse` **3/3 通过**；三张新图用 Edge headless 本地渲染实测自然宽度 **383 / 987 / 709px**，全部 < 正文列宽 1120px、无超宽回归，并截图目检确认章色正确（indigo/fuchsia/green）、文字无裁切；正文中文 **1729 / 1709 / 1551 字**，均远超 900 字门槛；每页 1 张带 `%%{init}%%` 章色 Mermaid + 图注、1 张提示卡、概念速查表、常见误区、参考资料。
- **引用零猜测**：三页共 18 条 arXiv 引用**逐条先 `curl` 取回页面真实 `<title>` 比对**再写入——过程中据此**剔除 1 条记错的编号**（`2407.14491` 实为无关的 3D 论文，非我以为的 ColPali），并纠正 `2005.11401` 是 RAG 原始论文（Lewis 2020）而非 DPR。
- **README 统计按实测增量对齐**（沿用第 17 轮「线上真会渲染」口径）：页 **187→190**、提示卡 **209→212**、Mermaid **180→183**、含参考资料页 **144→147**、读者可见图注 **162→165**、配图 **220→223**、去重一手来源 **316→324**；**含公式页 104 不变**（三页无 `$$`）。增量由脚本对「含/不含新页」两次点数之差得出，非手填。
- **导航接入**：三页已加入 `SUMMARY.md` 与各自章节导读列表，不制造站内孤儿。
- **未做项 / 阻塞（诚实）**：本轮三页 + 第 17/18/19 轮的提交**均已在本地，但仍未推上线**——推送卡在 GitHub 交互式凭据（GCM）授权，非代码问题；流程第 (5) 步「线上同步后抽查」对第 17–20 轮仍未闭环，需操作者本地 `git push origin main` 并批准凭据弹窗。

## 2026-09-22（第 19 次）五轴全绿的诚实记录：本轮没有可实测出的缺陷，但两笔提交卡在鉴权上没上线

按「找不到值得修的缺陷就汇报」的约定，这轮换 5 条**没量过的新轴**去证伪，结论是全部干净、**没有为凑指标而改的内容**。负结果也记，是为了让这些轴以后不必重复试。

- **A1 标题层级跳级：0**。逐页抽正文标题（剔除代码块），检查是否存在 `#`→`###` 这类跨级——全书 0 处，层级连续。
- **A2 跨页雷同 Mermaid：0**。把每个 Mermaid 块去掉分章配色指令后取哈希比对，没有两个页面共用一张「复制粘贴」图（≥40 字符的块），图不是凑数的。
- **A3 内容页残留占位符：0 真缺陷**。宽松扫 `TODO/FIXME/TBD/待补充/占位/xxx/lorem` 命中 31 处，收紧并排除合法用法后仅 2 处，且都是**在教写法的行内示例**（更新日志里描述 14 章负样本的 `` `xxx.svg` ``、Lab2 让读者「每条答案前缀『根据 xxx』」的引用占位范式）——无一是待填的坑。（宽松扫描之所以 31，是因为大小写不敏感把工具名 `TodoWrite`/`Todo 清单` 误配成 `TODO`，属口径噪声。）
- **A4 分章配色规范回归：180/180 全带 `%%{init}%%`**。第 14/27 轮压窄、改向 Mermaid 时有可能丢指令，实测**没有任何一个 Mermaid 块缺失章色指令**。
- **A5 代码围栏语言标注：0 个裸围栏**。非模板内容页里 ```` ``` ```` 开头块全部带语言标签，GitBook 高亮不会退化。
- **未做项 / 阻塞（诚实）**：第 17、18 轮的两笔提交（`49d1c05`、`10c5da7`）**已在本地，但尚未推上线**——推送卡在 GitHub 交互式凭据（GCM）授权，只读 `git ls-remote` 可达、写 `git-receive-pack` 挂起，非代码问题。因此第 17–19 轮流程第 (5) 步「线上同步后抽查」仍未完成，需操作者本地执行一次 `git push origin main` 并在弹窗批准凭据后方可闭环。本轮**未改动任何页面内容**，仅新增此记录。

## 2026-09-22（第 18 次）链接的「语义正确」：一次站内链接体检，只抓到一条真缺陷但把它坐实了

第 17 轮清完外链，这轮把**站内链接与页面结构**拆成 5 条新轴量：站内链接目标/锚点、`相关知识点` 双向性、中文字数密度、孤儿页、SUMMARY 收录，以及一处中文排版扫描。结论是——**大部分报警都是口径问题，不是内容缺陷**，只有 1 条是真要修的，但正因为用了能证伪的量测才没漏掉它。

- **唯一真缺陷：一处跳出 GitBook 内容根的链接**。[更新日志](./changelog.md) 里「门面升级」那条写 `[仓库首屏](../../README.md)`——从 `docs/00-index/` 出发，`../../README.md` 落到**仓库根**那份 README，而 GitBook 的内容根是 `docs/`，这份文件根本不在站上，线上读者点过去就是 404。改成指向仓库在 GitHub 上的地址 `https://github.com/funny8kids/ai-agent-handbook`（该 URL 由 `git remote` 得出并经 GitHub API `200` 核验，非猜测），句子也补了一句「在 GitHub 上，不在站内 `docs/` 内容根里」，让读者知道点出去会离开本站。量测脚本断言：改后 `docs/` 内**跳出内容根的相对链接 0 条**。
- **14-templates 的 2 条"断链"是故意的，不修**：[风格指南](../14-templates/style-guide.md) 的反面示范里写着 `../.gitbook/assets/xxx.svg` 与一个 `[标题](占位)` 示例，是用来教「别这么写」的**负样本**，被链接扫描如实报成 missing 属预期，按房规排除，不动。
- **一条被证伪的"轴"——不立它**：初版量了「`相关知识点` 是否双向」（X 列了 Y、Y 没回列 X），报出 324 处。但本手册的 `相关知识点` 本就是**向前指**的（把读者往更深的机制页/下一步引），双向对称是我凭空加的规则，不是全书约定；拿它当缺陷去"修"就是为凑指标改内容。**判据：新轴先问"这规则书里真有吗"，答案没有就退役，不拿它开工。**
- **其余全绿（且是"复测确认没退化"，不是自夸）**：站内锚点失效 **0**；`type: knowledge` 正文低于 900 中文字的 **0** 页（第 15 轮补到 ≥900 的成果稳住了）；无任何入链的真孤儿页 **0**；已发布页缺 `SUMMARY.md` 条目 **0**；中文排版扫描（弯引号不配对、重复标点、半角逗号夹在中文间、中英粘连缺空格）报出的 **7 处全是假阳性**——ASCII 逗号都在行内代码的 RDF 三元组 `(实体, 任职于, ACME)` 里、其余是 Markdown 链接语法与一处「描述旧错字」的引号示例，逐条看过无一该改。

## 2026-09-22（第 17 次）元数据与统计会不会骗人：把「最后更新」「README 数字」「外链健康」三件事重新量一遍

前 16 轮都在改页面本身，这一轮只查**关于页面的陈述是不是真的**——三条新轴（N=frontmatter 日期、S=README 统计、P=外链健康），每条都先量出偏差再改，不靠感觉。

- **N 轴·「最后更新」失真 79 页 → 0**：一次比对 `git log` 各文件末次提交日 vs frontmatter 的 `updated`，量出 **79 页**写着 09-20，实际当天有十余次提交（补图注、核引用、重排图形、增厚薄页）改过它们。全部回填为 09-22。先把口径写进[风格指南](../14-templates/style-guide.md)第八节并加进第九节检查清单：`updated` =「本页正文最后一次发生读者可见变化的日期」，改字/改图/改图注/改表格都算，只动脚本或 CI 不算。**一个诚实的前提也一并写清**：GitBook 页面右上角的「Last updated」用的是平台自身修订时间，仓库写什么都不影响它（已验证：某页 `updated` 写 09-20，线上仍显示 09-22）——所以这次回填不是为了骗读者，而是让仓库这份元数据能当真，维护者靠它判断「哪页多久没动过」。顺带给两份模板页（[知识页模板](../14-templates/knowledge-template.md)、[资源卡片模板](../14-templates/resource-template.md)）补上它们自己缺的 frontmatter，并把风格指南里「模板页免 frontmatter」的旧豁免改成准确表述（模板正文里那段 YAML 只是围栏示例，模板页本身该有真 frontmatter）。
- **S 轴·README 四处数字与实测不符 → 全部对齐**：脚本 `audit17s` 以「线上真会渲染」为口径重新点数（代码块、行内代码里的写法示例一律不计），量出并改正 README 首页四条：含公式页 **105→104**（有一页的 `$$` 只出现在代码块示例里，线上不渲染）、提示卡 **202→209**、去重后一手来源 **315→316**、配图 **222→220**（把「用作 GitBook 站标、不进正文的 2 张 SVG」从配图数里剔除并注明）。改完 README 的 **11 项统计全部与实测一致**（pages 187 / chapters 19 / formula 104 / hints 209 / mermaid 180 / captions 162 / ref-pages 144 / unique-sources 316 / projects 323 / figures 220 / labs 6）。
- **P 轴·694 条唯一外链复检：硬断 0**：16 路并发把全站外链走一遍，**P0（404/410/401/402）= 0**，无一条内容性死链。首轮有 77 条「无响应」，逐条降并发重探后 **43 条恢复 200**（全是 arxiv，首轮是被并发限流误判）；剩余 **34 条仍是连接层失败**（curl 7/28/35，即 TCP/TLS 连不上，`--max-time 40` 顺序重探与 `WebFetch` 两条独立通路结果一致），且**按主机聚集**：huggingface.co/*、sre.google、aws.amazon.com、reddit、news.ycombinator、mujoco.org、gist、discuss——是本沙箱的**出站网络屏蔽了这些站点**，不是页面死了。这 34 条全是规范里点名的一手来源（gsm8k、SlimPajama-627B、ToolACE、GAIA、bge-m3、mujoco、SRE book、AWS backoff），按「不为凑指标删内容」一律保留，只在此记录其不可达是环境所致。

- **回归校验**：188 个 md 文件 frontmatter **0 未闭合**、代码围栏 **0 不配对**、四字段齐全且顺序（`tags→type→status→updated`）**0 例外**；本次改动**未触碰任何 Mermaid 块**（脚本比对整份 diff，图相关行 0 条），故第 15/16 轮的「解析器 180 块 0 失败、最宽 1116px、竖排 9 张按定调保留」结论对本提交仍然成立、无需重跑；README 统计与实测 0 漂移。本轮 83 个文件、**+109 / −86 行**，其中 79 个文件仅改 `updated` 一行，正文信息**零删除**。

## 2026-09-22（第 16 次）图形有没有被解释：一条平台事实推翻了"图画得对就算完"

本轮的起点是一条**平台行为**：GitBook 渲染正文图片时会**剥掉 alt 文本**，读者在页面上根本看不到它；Mermaid 块更是没有 alt。也就是说前 15 轮里那些写得很好的 alt（「Open WebUI 真实界面：模型选择器、内联渲染的图表…」）对读者等于不存在。据此新建 5 条量测轴（资产健康 L1/L2、图注质量 M1–M5、裸图 F1–F3、图内说明缺失 D2'、章节内导航 I），每条都先用**假想反例**标定（该抓的抓到、不该抓的不抓）再上库。

- **32→1 处"读者看不到解释"的配图**：34 张自绘 SVG / 真实截图里有 32 张只有 alt 没有可见文字，现全部在图下补 `*《图：……》*`；剩 1 处是 `docs/README.md` 的首屏横幅，纯装饰、写进规范的豁免条款。补的是**图本身带不出的那句判断**，例：[仿真与 Sim2Real](../17-embodied-ai/simulation-sim2real.md) 的图注直接点出全章最该记住的数字——无随机化 95%→35%，只随机化视觉仍是 88%→52%，「动力学失配不会被更好的贴图救回来」。
- **99→0 张"裸图"**：180 个 Mermaid 块里 99 张既没有图注、上下也没有一句实质正文（多是紧跟标题出现的）。分 5 批由子 Agent 逐张读图后补写，再用重复度检测（M1）与空话尾缀检测（M2）复查：**重复图注 0 条、"…的流程图/示意图"式空话 0 条**。典型如[提示注入](../10-evaluation-safety/prompt-injection.md)——图注点明"泄漏那两步用的全是 Agent 自己合法的 tool call，攻击者没拿到任何权限，只是往页面返回值里塞了一句话"。现存图注 162 条（132 张 Mermaid + 30 处配图）。
- **48 张图判为"无需补图注"，并把这条规则写进规范**：新轴的第一版只回看**图前**有没有话，误报 6 张——那些图后面就跟着实质正文（如[对齐与安全](../10-evaluation-safety/alignment-safety.md) 图后的"为什么是环不是线：评估→约束→上线→监控→新行为回流成用例"）。把检测改成双向后 **F1/F2/F3 全为 0**。结论固化进[风格指南](../14-templates/style-guide.md)：Mermaid 不强制图注，但**必须被实质文字解释**（图前或图后皆可），而「如下图所示」「见下图」这类**换个图也成立的纯指针不合格**。
- **章节内导航缺口 5→0**：[贡献指南](../99-about/contributing.md) 与[许可证](../99-about/license.md) 此前互不引用（各自在站上孤着一页），现互相链上；[第 18 章目录页](../18-frontier-2026/README.md) 的页面表漏收了 [Computer Use 2026](../18-frontier-2026/computer-use-2026.md) 与 [评估 2026](../18-frontier-2026/eval-2026.md) 两篇——读者从章首页点不到它们，这是真缺口不是量测口径问题，已补两行「读完能做到」式的说明。
- **四条过期量测轴如实退役，不当成"缺陷清零"**：D2（400 字窗口内找图注）会对"用正文解释图"的页面重复计数，退役为 INFO，由更严的 D2' 接管；B2 的阈值原本写 5 条自测题，实测全书 15 个教学章**整齐地都是 3 条**（房规就是 3），阈值改 3——写错阈值测的是"和我不一样的地方"而不是缺陷；G1 原以为术语表页要按章号收录每章术语，实际总表是按主题分组、每章的中英对照在章末「本章术语速查」，改成 G1'（教学章缺该小节＝0）；K（无图注的 Mermaid 块 48）由上面的 F 轴取代。**留下的教训：每条轴都要能被假想反例证伪，也要能被真实语料证伪。**
- **回归校验**：180 块真解析器 `parsed=180 failed=0`；几何与第 15 轮**完全一致**（最宽 1116px、超宽 0、9 张竖条按操作者定调保留）；189 个 md 围栏配对 0 异常、frontmatter 不符房风格仍只有 1 个（截图清单 `MANIFEST.md`，有意保留）；站内链接 1532 条 0 断链；知识页 900 字以下仍为 0；图片资产 L1（引用了但不存在的图）0、L2（存在但没人引用的图）2 张是 GitBook 后台用的站点图标，属有意保留。本轮 118 个文件、**+270 行 / −4 行**（含本条 changelog 与统计行），除 4 行外全部是新增说明文字，未删任何内容。统计同步：`docs/README.md` 增加"162 条读者可见图注"一条。

## 2026-09-22（第 15 次）量测引擎与线上对齐：上一轮的图形结论有一半是错的

本轮第一个缺陷在**工具身上**：本地量测用的是 mermaid 12.0.0，而 GitBook 线上加载的是 `mermaid@11.14.0`（从页面 `<script>` 里读出来的）。两个版本对「`flowchart` 方向 × 互不相连 subgraph」的处理规则**正好相反**，所以第 14 轮那两条"实测规律"站不住。校准做法：抓一张线上已渲染页面的 SVG `viewBox`（497.52×1542.70），与本地同源码渲染结果比对，把本地降到 11.14.0 后得到 498×1543 才算对上。**教训固化为一条前置检查：量测引擎版本必须先证明与线上同版本，再谈规律。**

- **换引擎后同一批 170 块重测，缺陷清单完全变样**：超宽 **0→12 块**（最宽 1712px，线上等于把字缩到 10.4px），上一轮判定的 30 张「竖条」里只有 **14 张**在 11.14 下真的是竖条。也就是说第 14 轮"清零超宽"是本地自欺，线上从没清过。
- **11.14 下重新量出的排布规律**（已全部写进[风格指南](../14-templates/style-guide.md)）：① 宽度由**排数 × 每排节点数**决定，精简标签措辞几乎无效（1244→1174，约 5%），无损合并掉一排才有效（1158→999，约 160px）。② `flowchart TB` + 两个**互不相连**的 subgraph 才是「左右双栏、栏内横向」（1098×244）；同样的源码写 `flowchart LR` 会塌成 349×840 的竖条。③ TB 父图里 subgraph 的 `direction LR` 仍被忽略（加与不加都是 1060×244）。④ TB 父图下**后声明的 subgraph 渲染在左边**，源码顺序与读图顺序相反，图注写「左/右」必须截图复核。
- **超宽 12→0**：能无损并排的就并排——[安全边界](../17-embodied-ai/hardware-realtime-safety.md) 1433→999、[对齐与安全](../10-evaluation-safety/alignment-safety.md) 1410→1029（5 排压成 3 排）、[LangChain 一条链](../09-frameworks/langchain.md) 1206→966（终点节点合并）、[DSPy](../09-frameworks/dspy.md) 1238→1106；其余按 ① 处理或按下一条拆块。全库最宽 1712→**1116px**，180 块有效字号全部 16.0px（无任何缩放）。
- **竖条最严重的 9 张拆成上下两块**：[向量存储](../16-ai-infrastructure/data-vector-storage.md)、[微调基建](../16-ai-infrastructure/training-finetune-infra.md)、[结构化输出](../04-prompt-reasoning/structured-output.md)、[RAG 基础](../06-memory-rag/rag-basics.md)、[LlamaIndex](../09-frameworks/llamaindex.md)、[SWE-bench](../13-resources/benchmarks/swe-bench.md)、[MCP Servers](../13-resources/tools/mcp-servers.md)、[机器人基础模型](../17-embodied-ai/robot-foundation-models.md)、[实验地图](../19-labs/README.md)。被拆掉的跨块连线一律写进图注，信息不丢（例：向量存储的「反馈回流到清洗切块」）。块数 170→180（另 1 张是新增，见下）。
- **两张图有真实的图形完整性 bug**（新写的一版未命名节点 lint 抓出来的，该 lint 误报率太高已弃用，但这两条是真的）：[GoT](../04-prompt-reasoning/graph-of-thoughts.md) 的树图用裸 ID，线上渲染出写着「A1」「A2」的空盒子，现在全部补上标签并按 ④ 重排为 1098×244 的双栏；[Reflexion](../04-prompt-reasoning/reflexion.md) 有一条 `B2 --> C` 的边引用了不存在的节点，Mermaid 会凭空造一个空节点，已删。
- **正文厚度：900 字以下的知识页 7→0**。本轮补的是机制不是字数：[Self-Refine](../04-prompt-reasoning/self-refine.md) 823→1097（反馈来源四档对照 + 选择规则）、[GoT](../04-prompt-reasoning/graph-of-thoughts.md) 837→1055（三种可落地的聚合算子）、[协议栈 2026](../18-frontier-2026/protocol-stack-2026.md) 843→949（判据反读）、[Semantic Kernel](../09-frameworks/semantic-kernel.md) 852→952（迁移成本三处）、[Reflexion](../04-prompt-reasoning/reflexion.md) 874→1014（复盘存哪一层、按失败签名去重）、[OpenAI Agents API](../18-frontier-2026/openai-agents-api.md) 895→958（可移植性要主动测）、[Swarm 交接](../08-multi-agent/swarm.md) 898→1140（一次合格交接的四个字段 + 验收法）。
- **提示卡一致性**：9 个索引页的开头引用块统一改成房风格 `{% hint style="info" %}` **一句话**卡（[总索引](../00-index/README.md)、[资源库](../13-resources/README.md) 下 7 个子索引、[许可证](../99-about/license.md)），文字只做改写与补足，不删信息。脚本对每条替换都断言命中唯一，FAILS: 0。
- **最后一张无图的大页补图**：[开源项目索引](../13-resources/projects/README.md)（3539 字，全库最大的无图页）新增「怎么用这张索引」三分类决策图。
- **上一轮自己造成的损伤，如实记**：第 14 次提交（`4e2d236`）误删了「第 13 次」小节标题，导致那一轮正文挂在第 14 次底下。本轮从 `319412c` 取回原文恢复。
- **回归校验**：180 个 Mermaid 块真解析器 `parsed=180 failed=0`；188 页 0 断链、0 孤儿页、0 页缺 SUMMARY 条目、0 锚点失效；189 个 md 围栏配对 0 异常；frontmatter 不符房风格仍只有 1 个（截图清单 `MANIFEST.md`，有意保留）；统计同步为 README 的 Mermaid 180 / 配图 222 / 最宽 1116px。一个假阳性也记在这里：资产扫描把 `cover-handbook.svg` 报成"未使用"，实际它被仓库根目录 README 引用，是脚本只扫 `docs/` 的口径问题。
- **留下的取舍（要操作者定调）**：仍有 **9 张竖条**未拆——[WebArena](../13-resources/benchmarks/webarena.md) 347×734、[LangGraph](../09-frameworks/langgraph.md) 363×638、[OpenAI Agents API](../18-frontier-2026/openai-agents-api.md) 364×652、[AI 简史](../01-ai-basics/ai-history.md) 370×854、[越狱攻击](../10-evaluation-safety/jailbreak.md) 373×654、[人形机器人运动控制](../17-embodied-ai/humanoid-locomotion.md) 374×830、[工具注册表](../11-engineering/tool-registry.md) 388×504、[通用 Agent 产品](../12-applications/general-agent-products.md) 408×788、[企业知识库](../12-applications/enterprise-knowledge-base.md) 408×884。它们**字号都是满尺寸 16px，读起来不费力**，只是右侧留白多；而且这一批的纵向本身就是语义（时间轴、防御纵深、分层收敛），拆成两块会丢掉"一层压一层"的读法。要不要为版面整齐牺牲这层语义，属产品级取舍，本轮不动。**（2026-09-22 操作者定调：保留竖排，这 9 张结案。）** 其余未做项：14 个无图页全部是 `type: index` 索引页，按规范免图；[基准](../13-resources/benchmarks/README.md)、[数据集](../13-resources/datasets/README.md) 等 4 张表格型索引不为凑字数硬扩；封面/横幅两张 SVG 的自然宽 1600/1920px 是通栏素材，按设计豁免。

## 2026-09-22（第 14 次）正文厚度与图形几何：薄页、超宽图、细条图三类缺陷一起量清

这一轮沿用「先量后改」，并新增两条量纲：知识页正文的中文字数、每张 Mermaid 图的**自然宽×高比例**。上一轮只量了宽度，漏掉了反方向的毛病——图太窄也会毁排版。

- **薄页增厚 12 篇**：最低门槛 600 字、目标线 900 字。低于门槛的 4 篇全部改写：[语音 Agent](../12-applications/voice-agent.md) 424→1376、[Computer Use 2026](../18-frontier-2026/computer-use-2026.md) 362→997、[模型原生 vs Harness](../18-frontier-2026/model-native-vs-harness.md) 451→1365、[协议栈 2026](../18-frontier-2026/protocol-stack-2026.md) 397→902。另外 8 篇补的是机制而非字数：[第 18 章评测](../18-frontier-2026/eval-2026.md) 591→1141（里程碑打分式 + 任务 YAML 模板 + 归因纪律）、[Claude Agent SDK](../18-frontier-2026/claude-agent-sdk.md) →1356（resume/fork 成本式、三环境 `build_options()`）、[事故实录](../10-evaluation-safety/safety-incidents-2026.md) →1265（L0–L3 响应阶梯 + `gate_and_watch()` 伪代码）、[通用 Agent 产品](../12-applications/general-agent-products.md) →1029（验收件三件套 + 托付度公式）、[记忆类型](../06-memory-rag/memory-types.md) →1102（写入/检索/遗忘三操作与衰减打分式）、[角色分配](../08-multi-agent/role-assignment.md) →1073（`worker-artifact-v1` 交接契约、加角色的四问）、[ToT](../04-prompt-reasoning/tree-of-thoughts.md) →1128（预算不等式 `p_T − p_1 > λc(bd−1)`）、[CrewAI](../09-frameworks/crewai.md) →1096（sequential 成本来源与三个杠杆）。全库 900 字以下的知识页从 **19 篇降到 8 篇**；剩下 8 篇 823–898 字，逐篇核对房风格小节齐全（图、源码案例、误区、小练习、参考资料），再写就是凑数，保留原样。
- **超宽图 25→0**：把仍超出正文列宽的 25 张压回列内——LR 长链无损合并到 ≤5 排、扇形图去掉占位根节点、时序图折长消息并缩短参与者别名。全库最宽 1328→1096px。
- **本轮新发现的第二类图形缺陷：细条图**。宽度达标不等于排布合理：把每块的 W×H 一起量出来后，发现 **40 个块是「窄高细条」**（W<420 且 H>380，宽高比 <0.55），线上表现为正文右侧一大片空白。已改造比例最差的 10 张：[MCP Servers 目录](../13-resources/tools/mcp-servers.md) 252×1342→990×533、[微调基建](../16-ai-infrastructure/training-finetune-infra.md) 256×1096→862×516、[结构化输出](../04-prompt-reasoning/structured-output.md) 364×1372→1014×626、[SWE-bench](../13-resources/benchmarks/swe-bench.md) 360×1236→896×611、[向量存储](../16-ai-infrastructure/data-vector-storage.md) 376×1248→956×568、[RAG 基础](../06-memory-rag/rag-basics.md) 304×974→1096×342、[LlamaIndex](../09-frameworks/llamaindex.md) 328×1022→744×438、[动手实验地图](../19-labs/README.md) 168×936→568×470、[角色分配](../08-multi-agent/role-assignment.md) 244×664→1056×112、[第 18 章评测](../18-frontier-2026/eval-2026.md) 360×686→982×219。
- **两条实测出来的 Mermaid 排布规律**（已固化进[风格指南](../14-templates/style-guide.md)）：① `flowchart TB` 的长链必然塌成细条，而 `subgraph … direction LR` 在本 Mermaid 版本被忽略（实测仍渲染成 304×829 的竖排）；唯一有效的做法是父图改 `flowchart LR` 并让两个 subgraph **互不相连**——只要有一条跨排边，dagre 就把两排横向拼接（5 排链一拼就 1600px 以上），被删掉的跨排边改写进图注，信息不丢。② 父图为 LR 时**后声明的 subgraph 渲染在上面**，所以源码里要把逻辑上的第二排写在前面；本次 10 张图全部按此调序并逐张截图复核。
- **失败与回退如实记录**：曾按「最长路径 ≤5 就换 LR」批量翻转 16 张图，实测 **15 张超宽**（最高 2053px、字号被缩到 8.7px），已全部回退，只有第 18 章评测流水线一张成立。教训是 rank 数不等于最长路径——旁支与孤立节点各占一排，这条也写进了风格指南，避免下轮重犯。
- **一处真实错字**：[通用 Agent 产品](../12-applications/general-agent-products.md) 里「付款前停”」引号不配对，改为「付款前停止」。
- **回归校验**：170 个 Mermaid 块真解析器 `parsed=170 failed=0`（较上轮 +2：第 18 章评测流水线图、协议栈时序图），全树宽度复测 **0 超宽**、最宽 1096px、每块有效字号 16.0px；189 个 md 文件围栏配对 0 异常；frontmatter 不符房风格仅 1 个（`.gitbook/assets/screenshots/MANIFEST.md`，有意保留）；知识页缺「参考资料」0；站内链接 1484 条 0 断链，692 条唯一外链逐条核查 0 硬断。统计同步：README 的 Mermaid 168→170、配图 210→212、含公式页 100→105。
- **下一轮待办（需要操作者定调）**：仍有约 30 张图属「窄高细条」（比例 0.34–0.55，如[权限四层楼](../10-evaluation-safety/permission-sandbox.md) 348×1080、[CrewAI 流程](../09-frameworks/crewai.md) 296×1038、[AI 简史](../01-ai-basics/ai-history.md) 360×768）。其中一部分**纵向本身就是语义**（防御纵深、时间轴、层级收敛），拆成两排会丢掉「一层压一层」的读法；要不要为版面整齐牺牲这层语义，属产品级取舍，本轮不动。**（本条与上一条的宽度数字是用 mermaid 12.0.0 量的，与线上版本不一致，已在第 15 轮作废重测：11.14 下真竖条 14 张，拆掉 9 张、保留 9 张；2026-09-22 操作者定调——保留竖排，纵向是语义，版面整齐不值得用它换。今后时间轴/防御纵深/分层收敛类图形同样允许竖排，不再计入待修。）**



## 2026-09-22（第 13 次）出处体检：小节命名、站内链接错位与引用编号核对

前 12 轮都在补图和补内容，这一轮只查一件事：**书里写的出处，是不是真的、对不对得上**。量测方式全部可复现——脚本点数 + 逐条 curl + arXiv export API 比对标题，不用主观判断。结果比预想的糟：问题不在「没写引用」，而在「写了但用错了地方」。

- **一个小节被当两个用**：全库同名小节实际有三种状态——`## 参考资料` 101 篇、`## 相关资源` 26 篇（内容其实是站内跳转）、缺失 12 篇。26 处已全部统一改名为「参考资料」，再把混在里面的 **48 条站内链接**搬到「相关知识点」（21 个文件）。改完的口径是：**「参考资料」只放外部一手来源，站内跳转归「相关知识点」**，两条规则各有一个脚本断言把守（残留 0、混排 0）。
- **补齐真正缺一手来源的页面**：27 个正文页 + 10 个资源页/卡片新增已验证的一手来源（论文编号、官方仓库、协议文档、部署指南）。以「外部一手来源少于 3 条」为阈值，知识+资源页从 **40 篇降到 4 篇**——剩下 4 篇是 Toolformer 论文（官方未释出代码与权重）、Pi / DeepSeek Harness / MCP Servers 目录（一个仓库加一个官网就是它全部的官方入口），给它们挂二手转载才是灌水，故在卡片里写明原因、保留少于 3 条。
- **全站外链健康普查**：669 条唯一 URL 逐条走 16 路并发核查（GitHub 改用 API 绕开限流），**619 条返回 200**；硬断链 2 条已修：LangGraph 项目页里指向已下线的 `langgraph-templates` 仓库，改指官方公告 [Launching LangGraph Templates](https://www.langchain.com/blog/launching-langgraph-templates)；[游戏 Agent](../12-applications/game-agent.md) 里 OpenAI VPT 的研究页 403，改指 [官方仓库](https://github.com/openai/Video-Pre-Training)（两处标签同步改写，不保留对不上号的措辞）。
- **引用编号交叉核对（本轮最有价值的一项）**：把 104 个 arXiv 编号丢给 `export.arxiv.org` 取回真标题，再与标签逐条比对，抓出 **3 处错配**：[主流基准对比](../10-evaluation-safety/agentbench-webarena-swebench-gaia-toolbench.md) 把 SWE-bench 论文挂成了 WebArena 的 `2307.13854`（正解 `2310.06770`，另补 WebArena 自己的条目）；[知识图谱](../06-memory-rag/knowledge-graph.md) 标签写 TransE 却链到 word2vec 的 `1301.3781`（改 `1412.6575`，标题按 API 返回值改写为 *Embedding Entities and Relations…*）；[机器人基础模型](../17-embodied-ai/robot-foundation-models.md) 的 GO-1 标签补出论文真名（AgiBot World Colosseo）。另外差点写进一处新错：Toolformer 的 ACL 2023 会议版编号按记忆填会得到 `2023.acl-long.551`，点开才发现是另一篇表格问答论文，因此该卡片只保留 arXiv 一条。
- **frontmatter 与围栏**：11 个漏标文件补上（6 个实验 → `type: lab`，README/更新日志/贡献/许可 → `type: index`），[推理经济学](../16-ai-infrastructure/inference-economics-deployment.md) 那段无语言标注的公式围栏标成 ```text；不符合房风格（`tags → type → status → updated`）的文件从 15 个降到 3 个——`SUMMARY.md` 与 14 章两份模板示例，属有意保留。
- **规范固化**：[风格指南](../14-templates/style-guide.md) 第五节新增三条硬规则（命名唯一、≥3 条、每条都要实际点开且标题对得上，arXiv 用 export API 核对），资源卡片体裁说明与发布检查清单同步；[资源模板](../14-templates/resource-template.md) 里残留的「相关资源」表述改正。
- **回归校验**：189 个 md 文件围栏配对 0 异常，168 个 Mermaid 块真解析器 `parsed=168 failed=0`，无断链回归，187 页 / 19 章统计不变。
- **本机测不到的部分如实记录**：14 条未能拿到 200 的链接里，7 条是站点反爬 403（`openai.com`、`iso.org`、`dl.acm.org`、`academic.oup.com`、`platform.openai.com`、`wiki.linuxfoundation.org`、`developers.openai.com`），7 条是本机 DNS 被路由器劫持（`sre.google`、`huggingface.co`、`mujoco.org`、`hastie.su.domains` 全部解析到 `192.168.31.1` 后超时）——后者按「unreachable ≠ dead」处理，未删；其中 `sre.google` 两条经搜索引擎确认页面确实在线。**下一轮待办（已用体裁核对过，不是笼统的「补图补字」）**：19 篇知识页正文低于 900 字，其中 4 篇低于本书最低门槛 600 字（[Computer Use 2026](../18-frontier-2026/computer-use-2026.md)、[协议栈 2026](../18-frontier-2026/protocol-stack-2026.md)、[语音 Agent](../12-applications/voice-agent.md)、[模型原生 vs Harness](../18-frontier-2026/model-native-vs-harness.md)），优先增厚这 4 篇；15 个无图页面经逐一体裁核对全部是 `type: index` 的索引页，按规范本就免图，不再为凑指标硬塞。

## 2026-09-22（第 12 次）全库 Mermaid 宽度实测：把被线上缩小的图救回来

修完 Lab 2 那张图后顺手做了一次全库量测：用真 Mermaid 渲染 168 个块，逐块读 SVG 的 `viewBox` 自然宽度，和 GitBook 正文列宽（约 1120px）比对。**结论是这类缺陷不是个例：39 个块比正文列宽还宽**，线上被等比缩小后文字跟着变小——最糟的是[学习路线](../00-index/learning-path.md)那张 15 章横向链，自然宽度 2664px，缩到 42%，16px 的字只剩 **6.7px**，等于摆一张看不清的图。

- **改造 17 个最严重的块**（缩小后字号 ≤13.4px）：长链一律换轴（`flowchart LR` ↔ `flowchart TD`——链长就竖排，同层分支多就横排），[人工智能发展简史](../01-ai-basics/ai-history.md) 的 11 个节点拆成两行时间线并补了读图说明，[Claude Agent SDK](../18-frontier-2026/claude-agent-sdk.md) 的时序图把长消息用 `<br/>` 折行，[框架选型决策流](../09-frameworks/README.md) 精简了分流标签的措辞。节点内容与语义不变，只动排布与折行。
- **量出来的结果**：全库最宽块从 2664px 降到 1328px；被改的 17 块现在最小字号 ≥13.5px（多数恢复满尺寸 16px）。168 块真解析器仍 0 失败，无断链回归，frontmatter 逐文件校验通过。
- **留下的取舍如实写清楚**：还有 25 个块在 1128–1328px 之间（缩小后 13.5–15.9px，可读但不够舒展），没有为了凑指标继续砍节点；另外长链改竖排后图形变成「窄而高」（宽 256–400px、高约 1000px），左右留白偏多——这是拿版面换清晰度的主动选择，比文字糊成一片好。
- **规范固化**：[风格指南](../14-templates/style-guide.md) 新增「排布与可读性」小节与自检项——横向不超过 6 个节点，别指望用 `subgraph` 里的 `direction` 做泳道（一旦有边跨过子图边界，Mermaid 就忽略它），新图必须截**线上**页面判定。

## 2026-09-22（第 11 次）真实产品截图上线 + 无图页补齐 + 薄页增厚

全书第一次出现**真实软件界面**：此前 191 张配图全是自绘 SVG 与 Mermaid，读者看不到「这些工具真长什么样」。这一版补上截图，同时清掉三类体检出的短板。

- **8 张真实产品 UI 截图**（`docs/.gitbook/assets/screenshots/`，目录内 `MANIFEST.md` 逐张记录来源 URL 与访问日期）：Langfuse Trace 视图（11 章）、MCP Inspector 协议监控（05 章）、OpenHands Automate（12 章 + 项目页）、Dify 工作流画布（09 章）、Open WebUI 对话与工作区（12 章）、Arize Phoenix Trace Details（11 章）、AutoGen Studio Team Builder（09 章）、LangSmith 实验对比表（10 章）。每张逐项目检：真实产品界面、无 cookie 横幅与遮罩、文字可辨；7 个来源 URL 复核 HTTP 200。**每张图配一段「读这张图的顺序」**，指出面板与本页论点的对应关系，而不是贴完就算。
- **补齐违反「每页有图」自订标准的页面**：[Lab 2](../19-labs/lab2-rag.md) BM25 检索链路、[Lab 3](../19-labs/lab3-mcp.md) MCP 握手时序、[Lab 5](../19-labs/lab5-eval-trace.md) 评测—trace 数据流、[Lab 6](../19-labs/lab6-guardrails.md) 两道护栏决策流，各配一张章色 Mermaid；新图全部经 Edge 真实渲染逐张目检：Lab 3 用时序图，Lab 2/5/6 用竖排 `flowchart TD`。Lab 2 首版试过单排横向 LR，十个节点被正文宽度压到看不清字号，改回竖排后每张卡片文字都清晰，并把「回答不合格就回查切块与打分」这条虚线显式画了出来。
- **13 章 5 个薄项目页增厚**：[LangGraph](../13-resources/projects/langgraph.md)、[AutoGen](../13-resources/projects/autogen.md)、[CrewAI](../13-resources/projects/crewai.md)、[LangChain](../13-resources/projects/langchain.md)、[OpenHands](../13-resources/projects/openhands.md) 从 575–820 字扩到与其它资源页同密度（架构要点 + 适用场景 + 手写点评 + 真实链接），并把 7 个项目页全部配图；LangChain 页补 3 行 Runnable 管道代码判断协议价值。
- **核心页补最小可跑代码**：[Transformer 与注意力](../03-llm/transformer-attention.md) 新增 12 行 NumPy 单头因果注意力，与正文公式逐项对应，**贴出本机真实运行的权重矩阵输出**，并解释三件事：causal mask 就是「逐字解码」的代码形态、平方级开销长在权重矩阵上（所以 KV 缓存救显存救不了注意力）、softmax 饱和为什么让注意力可视化容易骗人。
- **未能做到的部分如实记录**：LangGraph Studio 与 browser-use 的官方文档页经渲染后 DOM 里只有品牌图，无公开产品截图；CrewAI 文档站的 `crews.png` / `flows.png` 目检是概念示意图（与自绘 Mermaid 等价），故不引入；Langfuse Cloud 官方 demo 工作区跳登录墙，改用其文档内嵌截图。原因写进 MANIFEST，避免后人重复踩。

统计更新：全书配图 **210 张**（168 Mermaid + 34 自绘 SVG + 8 真实截图），187 页 / 19 章不变；168 个 Mermaid 块经真解析器逐块校验 0 失败，无断链回归。提示卡重新逐文件点数：源码里的 hint 标记共 207 处，其中 4 处是 14 章模板代码块里的写法示例、1 处是本文的自指说明，都不会渲染成卡片，**真实提示卡 202 个**——此前两处统计分别写成 206 和 204，均以本次点数为准。

## 2026-09-21（第 10 次）动手实验章 + 门面升级 + 术语速查 + 实战手记

把「只读不练」和「门面朴素」两块最后的短板补齐，四件事一起落地：

- **新增第 19 章「动手实验」**：6 个纯标准库、零 API Key、离线可跑的实验——最小 ReAct 闭环 → 手写迷你 BM25 RAG → 手写迷你 MCP 服务 → 三角色协作 → 评测与 trace → 护栏与接真模型。每个实验含完整代码、**本机 Python 3.13 真实运行输出**、盯三个细节、动手改与排错备忘；MockLLM 与真实模型接口同构，看懂后换真 API 主循环一行不改。已接入 [SUMMARY](../SUMMARY.md) 与 [学习路线](../00-index/learning-path.md)（新增「动手派」路线）
- **门面升级**：自绘仓库封面 `cover-handbook.svg`（1600×900，六段学习旅程）+ GitBook 首页横幅 `banner-home.svg`（1920×480，LLM 推理循环）；[仓库首页](https://github.com/funny8kids/ai-agent-handbook)（在 GitHub 上，不在 GitBook 站内的 `docs/` 内容根里）与 [在线首页](../README.md) 重排，新增「边学边做」入口
- **4 张高保真工具界面示意**（与既有 SVG 同风格，逐张真实渲染目检）：MCP Inspector 调试台（05）、框架选型五问决策树（09）、Agent 评测发布门禁看板（10）、可观测性三跳定位控制台（11）
- **每章末尾中英术语速查**：核心章节各配 8–12 条术语 + 白话解释；**12 个核心页新增「实战手记」**：运维现场的经验值（轮次收敛区间、trace 采样账单、prompt 约束条数上限、检索失败要到日志认领等），数字全走经验口径、不虚构事故与引用

全书配图达 **191 张**（157 Mermaid + 34 自绘 SVG），提示卡 206 个；全部 Mermaid 经真解析器逐块校验 0 失败，无断链回归。

## 2026-09-20（第 9 次）旗舰概念插图第二批：8 张自绘 SVG 上线

补上「只有框图、没有图册」的最后一块短板，为核心概念页新增 8 张与既有资产同风格的自绘 SVG（960 宽、淡网格第二层背景、章色主色、语义化 SMIL 动效，全部经真实渲染逐张目检）：

| 插图 | 接入页面 | 讲什么 |
|---|---|---|
| 上下文预算 | [Token 与上下文](../03-llm/token-embedding-context.md) | 200k 窗口五段分配 + 压缩前后对照，缓存分界一眼可见 |
| ReAct 闭环 | [ReAct](../04-prompt-reasoning/react.md) | 思考—行动—观察三环，左侧纯 CoT 断链对照、右侧真实轨迹示例 |
| MCP 架构 | [MCP](../05-tool-protocol/mcp.md) | M×N 乱麻 vs M+N 统一协议，Host/Client/Server 与三种原语 |
| 记忆三层 | [记忆类型](../06-memory-rag/memory-types.md) | 工作/情景/语义的沉淀与回填回路 + 遗忘曲线 |
| 规划对比 | [Plan-and-Execute](../07-planning/plan-and-execute.md) | 先谋后动 vs 边想边做双泳道，含重规划回跳与两本账 |
| 协作拓扑 | [多智能体协作](../08-multi-agent/multi-agent-collaboration.md) | Supervisor/Swarm/Group Chat/Pipeline 四宫格与选型底线 |
| Trace 瀑布 | [日志、追踪与监控](../11-engineering/logging-tracing-monitoring.md) | 一次运行的 span 树时间轴，延迟/token/成本/重试四项必录 |
| 编程 Agent 循环 | [编程 Agent](../12-applications/coding-agent.md) | 沙箱内改码—测试—修复闭环，合并权留给人 |

全书配图达 **182 张**（154 Mermaid + 28 自绘 SVG）。

## 2026-09-20（第 8 次）全书 Mermaid 章色配色：告别默认灰白

针对线上抽查发现的「全书图只有黑白框图、图册感弱」做视觉体系升级：

- **154 个 Mermaid 块全部注入 `%%{init}%%` 章色主题**：18 章各配一个主色（02 紫、05 青、09 玫红、10 红……），节点底色统一为主色掺白 90%、连线掺白 45%，一眼可辨所在章节；GitHub 与 GitBook 原生支持该指令
- **门面页补图**：[什么是 AI Agent](../02-agent-basics/what-is-agent.md) 新增「两分钟判断是不是 Agent」决策流程图，全书正文页（除模板页）实现图零空白
- **规范固化**：[风格指南](../14-templates/style-guide.md) 新增「Mermaid 章色配色（硬性要求）」一节——章色表、混色公式、可直接复制的指令示例；写作检查清单同步加一条
- 全部 154 块经真解析器（mermaid@11）逐块校验 0 失败

## 2026-09-20（第 7 次）对标头部开源手册：图文、排版与自测体系升级

以 GitHub 同类头部项目（bojieli/ai-agent-book、microsoft/ai-agents-for-beginners、huggingface/agents-course、datawhalechina/self-llm 等）为参照，补三块短板：

- **图示密度翻倍**：新增约 60 张 Mermaid 内联图，全书达 **154 张 Mermaid + 20 张自绘 SVG**；09 框架、10 评安、11 工程、17 具身、16 基础设施等此前无图的章节全部配齐机制图；资源深读卡（ReAct/Reflexion/Toolformer/SWE-bench/GAIA/WebArena/Langfuse 等）逐张配「一图看懂」
- **排版升级为 GitBook 原生**：183 个「一句话 / 提示 / 注意」引用块全部转为分色 `{% hint %}` 提示卡；模板与风格指南同步改用 hint 写法，贡献指南新增「图文与排版规范」与 good-first-page 清单
- **每章「读完能做到」清单 + 章末自测**：18 章全量落地，清单条目均为可检验行为，自测题按回忆/应用/判断三档并标注答案出处
- **质量闸门**：全部 Mermaid 经真解析器（mermaid@11）逐块校验 0 失败；修复断链 5 处；被修改页面 `updated` 统一为 2026-09-20
- 资源库增补：开源项目索引头部 95 个项目改为手写一句话点评（去掉截断的机器味描述）；博客（16）/ 社区（11）/ Awesome 列表（13）/ 数据集四个索引扩充完成，收录链接逐一在线核验，无法核实的一律剔除

## 2026-09-12（第 6 次）对齐 2026-09 前沿：新增第 18 章

针对审核发现的「模型面/产品面/评估代际滞后、图片覆盖不足」做系统补强：

- **新增 18 2026 前沿**（8 页）：
  - [2026 前沿模型地图](../18-frontier-2026/frontier-models-2026.md)：GPT-6 Astra、Claude Fable 5.1 / Mythos 5.1、Opus 5，含 effort × 防护 × cache 读法
  - [OpenAI Agents API](../18-frontier-2026/openai-agents-api.md)：托管 Codex harness、压缩、tool search、子 Agent
  - [Claude Agent SDK](../18-frontier-2026/claude-agent-sdk.md)：与 CLI / Client SDK / Managed Agents 分界
  - [模型原生 vs 自建 Harness](../18-frontier-2026/model-native-vs-harness.md)：2026 架构分叉与选型流程
  - [Computer Use 2026](../18-frontier-2026/computer-use-2026.md)
  - [评估 2026](../18-frontier-2026/eval-2026.md)：Terminal-Bench 4.0、OSWorld 2.0、τ²、Agents' Last Exam
  - [2026 协议栈](../18-frontier-2026/protocol-stack-2026.md)：MCP + A2A + AG-UI + Skills/agents.md
- **第 10 章**新增 [2026 安全现实](../10-evaluation-safety/safety-incidents-2026.md)；[基准测试总览](../10-evaluation-safety/benchmarks.md) 刷新到 2026 代际
- **第 12 章**新增 [通用 Agent 产品](../12-applications/general-agent-products.md)、[实时语音 Agent](../12-applications/voice-agent.md)
- **第 01 章** [发展简史](../01-ai-basics/ai-history.md) 时间线补 2026-07～09 事件
- 新增 5 张自绘 SVG：模型×harness 矩阵、Agents API 架构、协议栈、评估版图、Computer Use 闸门
- 导航同步：`SUMMARY.md`、总导航、首页必读与主题入口

## 2026-09-10（第 5 次）内容质量修订与全书扩写

针对「模板化、emoji 泛滥、原理不深、引用单一」四类问题做系统性修订，并对全书 70 篇偏薄页面做深度扩写：

- 重写 [风格指南](../14-templates/style-guide.md)：按**体裁分型**（原理型/概念型/实战型/资源卡片），去掉单一模板；新增 emoji 硬预算、公式与出处要求、案例配给、发布字数门槛；并入 16/17 章的 SVG（SMIL）动图规范
- 全局清理 emoji：剥离标题 emoji 与星级难度标记；第 16/17 章 24 个文件一并去 emoji（627 → 163）
- 事实核查（经本地代理联网）：逐条验证外链；修复断链（`humanlayer/12-factor-agents`、`Awesome-RAG`、MCP Discussions 地址等）
- **Pi 仓库已迁移**：`badlogic/pi-mono` → `earendil-works/pi`，全库更新；移除已无法核实的「vLLM pods」等表述
- **DeepSeek Harness 引用经核实为真实**（包路径均存在），删除与主题弱相关的凑数引用
- 约 70 篇原理/概念/实战页补齐机制、公式与论文引用：注意力、Embedding、RLHF/DPO、预训练与 LoRA、量化推理、Token 与上下文预算、RAG 指标、CoT/ToT/GoT/Reflexion/Self-Refine、知识图谱、上下文工程、记忆压缩、幻觉、提示注入/越狱，规划 5 篇、多智能体 7 篇、框架 8 篇、工程化 10 篇、应用 8 篇，以及可解释性、对齐、行业 Agent 等
- **全书 170 页全部达到体裁字数门槛**（原理型 1200 / 实战型 900 / 概念型 600 汉字），含公式页面 93 篇
- 2 个不足 150 字的资源卡片补齐后恢复 `published`
- 新增 7 张自绘 SVG 插图并接入对应章节
- 新增 [开源项目索引](../13-resources/projects/README.md)：323 个项目、11 个分类，star/许可为 2026-09 实测值；后续清理了自动分类混入的跑题条目
- 说明：生成与校验用的辅助脚本已从仓库移除，以保持内容仓库精简

## 2026-09-10（第 4 次）新增 16 AI 基础设施与 17 具身智能

- 新增 **16 AI 基础设施**（11 页）：推理服务化（连续批处理 / PagedAttention / TTFT-TPOT）、前缀缓存与上下文工程、GPU 调度与多租户、训练与微调基础设施、沙箱与执行环境、模型网关与路由、持久化执行与运行时、数据与检索基础设施、可观测性与评估平台、推理经济学与部署形态
- 新增 **17 具身智能**（13 页）：具身闭环定义、机器人基础模型谱系（RT-2 → OpenVLA → π0 → GR00T/Helix/GO-1）、VLA 架构与动作头、动作表示与分层控制、数据引擎、仿真与 Sim-to-Real、世界模型与视频预训练、灵巧操作、人形与腿足运动、评估与基准、硬件实时与安全、Agent ⇄ 机器人桥接（含代码）
- 新增 6 张**可动画的 SVG 图示**（SMIL，GitHub/GitBook 中可直接播放）：连续批处理、前缀缓存、沙箱分层、VLA 循环、动作分块、Sim-to-Real 域随机化
- 双向链接补齐：16/17 ⇄ 03、05、06、10、11、12、13 各相关页；新增 `infrastructure`、`embodied-ai`、`data`、`cost` 四个标签
- 导航同步：`SUMMARY.md`、`docs/README.md`、学习路线（新增「平台/Infra」与「具身方向」两条路线）、术语表新增两组共 29 条

## 2026-09-10（第 3 次） 全书完成

- ✅ 全部 16 章、142 页撰写完成（此前为骨架 + 占位页）
- 案例覆盖三大开源 harness：**Claude Code**（社区逆向：三层 prompt 组装、子 Agent 隔离、三档压缩、权限管道）、**Pi Agent（原 pi-mono）**（极简 harness：4 原子工具、~300 行 agentLoop、JSONL 会话）、**DeepSeek Harness**（一切皆插件：Cordis 框架、turn/step 状态机、append-only 事件流、landlock 沙箱）
- 新增 12 章编程 Agent 页的「三大 harness 横向深拆」对比表
- 全书双向链接（知识点 ⇄ 资源）铺设完成；术语表 60+ 条收录
- 评估章收录五大基准精读（SWE-bench/GAIA/WebArena/AgentBench/ToolBench）

## 2026-09-10（第 2 次）

- 建立统一写作规范：新增 [风格指南](../14-templates/style-guide.md)（emoji 规范、图文规范、先问题后定义、写作检查清单）
- 知识点模板升级为「一句话结论 + 生活类比 + 图 + 例子 + 误区 + 资源」结构，增加 frontmatter（tags/type/status/updated）
- 资源模板增加 frontmatter 与「双向链接」规范（知识点 ⇄ 资源互链）
- 写出第一篇完整示例页：[什么是 AI Agent](../02-agent-basics/what-is-agent.md)
- 新增 `docs/assets/` 图片目录（diagrams / screenshots / covers / icons）
- SUMMARY 章节标题加入模块 emoji；全部占位页升级为新格式（frontmatter + 模块 emoji + 模板指引）

## 2026-09-10

- 初始化全新手册结构：16 个章节、135+ 页面骨架
- 建立导航与索引（总导航、学习路线、标签索引、资源总表、更新日志）
- 建立 13 资源库分类：论文、课程、开源项目、工具、数据集、基准测试、博客、社区、Awesome 列表
- 新增知识点模板与资源模板，统一写作格式
- 迁移 GitBook 配置，内容根目录设为 `docs/`
