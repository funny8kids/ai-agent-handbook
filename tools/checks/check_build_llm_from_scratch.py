# -*- coding: utf-8 -*-
"""Round 101 axis: chapter 22 promises 「每一页的数字都有一个能复跑的出处」 -- so the promise is run.

The normative source is `docs/22-build-llm-from-scratch/spec.md`: it freezes the 逐页验收表 (page ->
script), the 达标线 table (page -> threshold), the 判决口径 table (bucket -> disposition) and the
budget bound (`n_layer <= 2` ...). This file reads numbers **out of those tables** -- changing the
table changes the judge, deleting it makes the judge say 「尺子断了」 instead of 「本章合格」. Nothing
here hand-copies a threshold.

Buckets (their meaning *and* their red/pass behaviour come from the spec table, not from this file):
  SPEC      page missing a section / figure / trio, or a 复跑物 path that does not exist
  ARTIFACT  a `text` record a page pasted is not what the script prints today; a table number that
            appears in no record
  CLAIM     a stated quantity disagrees with the script's own account (params, ln V, MACs exact;
            wall-clock within the spec's tolerance); README's frozen config vs gptnano.CONFIG
  XREF      a 「与第 N 章一致」 sentence that has no in-site link, carries an in-site fragment
            (GitBook rewrites CJK headings to pinyin slugs, so no reader can land there), or never
            names a section that really exists on the linked page
  COVERAGE  a table row points at a page that is not there, records dir empty, a spec table or a
            threshold cannot be read -- exit 2, never read as a pass

One deliberate asymmetry, so that the HEAD control can be red at all: when *no* page of the chapter
is published (a fresh worktree), that is a SPEC red; a partially published chapter is a COVERAGE gap.

Run:  python tools/checks/check_build_llm_from_scratch.py            （真跑七个复跑物 + 全部腿）
      python tools/checks/check_build_llm_from_scratch.py --pages-only（不跑训练，RUN 腿记覆盖缺口）
      python tools/checks/check_build_llm_from_scratch.py --selftest   （每桶一个种植反例）
      python tools/checks/check_build_llm_from_scratch.py --head-control（在 HEAD 的 worktree 上复跑：本章未发布，必须整场红）
"""
import glob
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))

from flag_guard import reject_unknown  # noqa: E402  an unparsed flag must not fall through

FLAGS = ("--head-control", "--pages-only", "--selftest")
CHAPTER_DIR = "22-build-llm-from-scratch"
SPEC_NAME = "spec.md"
SCRIPT_TIMEOUT_S = 3600
MIN_ROWS = 8          # the 验收表 has one row per published page; a smaller parse means an empty ruler
RUN_ORDER = ["nano_tokenizer.py", "nano_forward.py", "nano_budget.py", "nano_backward.py",
             "nano_train.py", "nano_sample.py", "nano_export.py"]

norm = lambda s: (s or "").replace("\r\n", "\n").replace("\r", "\n").strip()
CELL = re.compile(r"(?<!\\)\|")
MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
# 全书 19 个章导读的自测/清单条目实测都是 `N. ` 起头（`**N.` 全站 0 处），计数按这个口径来。
ITEM_RE = re.compile(r"^(?:[-*]\s|\d+[.)]\s|\*\*\d+[.)])")


# --------------------------------------------------------------------------- spec parsing
def cells(line):
    t = line.strip()
    if t.startswith("|"):
        t = t[1:]
    if t.endswith("|"):
        t = t[:-1]
    return [c.strip() for c in CELL.split(t)]


def parse_tables(md):
    """Pipe tables -> [(header cells, [row cells])]. Separator rows are dropped."""
    out, cur = [], []
    for ln in md.split("\n"):
        if ln.strip().startswith("|"):
            cur.append(cells(ln))
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = []
    if len(cur) >= 2:
        out.append(cur)
    res = []
    for t in out:
        rows = t[1:]
        if rows and rows[0] and set("".join(rows[0])) <= set("-: "):
            rows = rows[1:]
        res.append((t[0], rows))
    return res


def find_table(tables, header):
    for hdr, rows in tables:
        if [c.replace(" ", "") for c in hdr[:len(header)]] == header:
            return rows
    return None


def page_key(cell, row=()):
    for src in (cell,) + tuple(row):
        m = MD_LINK.search(src)
        if m:
            return os.path.basename(m.group(2).split("#")[0])
        m = re.search(r"`([^`]*\.md)`", src) or re.search(r"([A-Za-z0-9_./-]+\.md)", src)
        if m:
            return os.path.basename(m.group(1))
    return None


def squash(text):
    """节名与句子比较时只剥掉 Markdown 外壳：标题符、强调符、链接方括号、反引号。"""
    return re.sub(r"[\s#*`\[\]（）()「」]", "", text or "")


class Spec(object):
    """Everything this judge obeys, read out of spec.md at run time."""

    def __init__(self, md, path):
        self.path = path
        self.gaps = []           # COVERAGE findings
        self.md = md
        tb = parse_tables(md)
        self.accept = find_table(tb, ["页", "读者能独立验算的东西", "复跑物"])
        self.bars = find_table(tb, ["页", "达标线"])
        self.buckets = find_table(tb, ["桶", "含义", "处置"])
        for name, tbl in ((u"验收表", self.accept), (u"达标线表", self.bars),
                          (u"判决口径表", self.buckets)):
            if tbl is None:
                self.gaps.append(u"规范表读不出：%s（判据不敢在没尺子时说合格）" % name)
        self.bounds = dict((k, int(v)) for k, v in
                           re.findall(r"`([a-z_]+)\s*(?:≤|<=)\s*(\d+)`", md))
        if len(self.bounds) < 4:
            self.gaps.append(u"预算硬线读不出：只解析到 %d 条 `key ≤ value`" % len(self.bounds))
        m = re.search(u"本章色（`#([0-9A-Fa-f]{6})`）", md)
        self.color = m.group(1).upper() if m else None
        if not self.color:
            self.gaps.append(u"章色读不出：正文里没有「本章色（`#rrggbb`）」那句")
        self.disposition = {}
        if self.buckets:
            for row in self.buckets:
                b = re.match(r"`?([A-Z]+)`?", row[0])
                if not b:
                    continue
                d = row[-1]
                self.disposition[b.group(1)] = \
                    "exit2" if (u"退出码" in d or u"不读成通过" in d) else \
                    ("red" if u"红" in d else "undeclared")
        # rows keyed by page basename
        self.rows = {}
        if self.accept is not None:
            for row in self.accept:
                k = page_key(row[0], row)
                if not k:
                    self.gaps.append(u"验收表某行的页读不出：%r" % row[0])
                    continue
                s = re.search(r"`([^`]+\.py)`", row[-1])
                self.rows[k] = {"label": row[0], "check": row[1],
                                "script": os.path.basename(s.group(1)) if s else None,
                                "bar": None}
        if self.bars is not None:
            for row in self.bars:
                k = page_key(row[0], row)
                if not k:
                    self.gaps.append(u"达标线表某行的页读不出：%r" % row[0])
                    continue
                if k not in self.rows:
                    self.gaps.append(u"达标线表里的页 %s 不在验收表里（两张表没对平）" % k)
                    self.rows[k] = {"label": row[0], "check": "", "script": None, "bar": None}
                self.rows[k]["bar"] = row[-1]


# --------------------------------------------------------------------------- the world under test
class World(object):
    """A chapter directory + the transcripts its scripts printed. Pure data, so controls can plant one."""

    def __init__(self, spec, doc_dir, pages, records, fresh, run_secs, config, nano_dir,
                 run_secs_load=None):
        self.spec = spec
        self.doc_dir = doc_dir
        self.pages = pages            # {basename: text} (spec.md excluded)
        self.records = records        # {stem: {"stdout":..,"stderr":..}} committed
        self.fresh = fresh            # {script basename: (rc, stdout, stderr)} or None
        self.run_secs = run_secs      # faster of this pass's two training runs, or None
        self.run_secs_load = run_secs_load   # the slower one: what the same config costs under load
        self.config = config
        self.nano_dir = nano_dir

    def rec(self, script, stream="stdout"):
        if self.fresh is not None and script in self.fresh:
            return norm(self.fresh[script][1 if stream == "stdout" else 2])
        stem = os.path.splitext(script)[0]
        d = self.records.get(stem, {})
        return norm(d.get(stream, ""))

    def all_rec_text(self):
        return "\n".join(self.rec(os.path.basename(r) + ".py") for r in RUN_ORDER)

    def seconds_values(self):
        vals = []
        for s in RUN_ORDER:
            vals += [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*秒", self.rec(s, "stderr"))]
        return vals


def load_config(nano_dir):
    path = os.path.join(nano_dir, "gptnano.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("_gptnano_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.CONFIG)


def run_scripts(nano_dir):
    """Execute every 复跑物 in a throwaway copy of nano/ (train writes a checkpoint into its own
    directory -- measuring must not dirty tracked artifacts).

    The training runs twice anyway (the 达标线 demands byte-identical stdout), so the time budget is
    judged on the faster of those two real runs: wall-clock on this machine measures 83-98 s idle and
    147 s while other work competes for cores, and a reader on a busy laptop would otherwise get a
    red verdict for someone else's CPU. Both readings are printed, and a config that is too expensive
    still reddens (both runs then exceed the line). Returns (fresh, secs, secs_load, gaps, twice).
    """
    sandbox = os.path.join(tempfile.mkdtemp(prefix="r101nano"), "nano")
    shutil.copytree(nano_dir, sandbox, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    fresh, gaps, secs, secs_load = {}, [], None, None
    twice = {}
    try:
        for name in RUN_ORDER:
            script = os.path.join(sandbox, name)
            if not os.path.isfile(script):
                gaps.append(u"复跑物不存在：%s" % name)
                continue
            t0 = time.time()
            p = subprocess.run([sys.executable, name], cwd=sandbox, capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               timeout=SCRIPT_TIMEOUT_S)
            fresh[name] = (p.returncode, p.stdout or "", p.stderr or "")
            if name == "nano_train.py":
                first = time.time() - t0
                p2 = subprocess.run([sys.executable, name], cwd=sandbox, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    timeout=SCRIPT_TIMEOUT_S)
                second = time.time() - t0 - first
                twice["second_stdout"] = p2.stdout or ""
                twice["first_stdout"] = p.stdout or ""
                twice["second_rc"] = p2.returncode
                secs, secs_load = min(first, second), max(first, second)
        sweep = os.path.join(sandbox, "nano_shape.py")
        if os.path.isfile(sweep):
            p = subprocess.run([sys.executable, "nano_shape.py", "--report"], cwd=sandbox,
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=SCRIPT_TIMEOUT_S)
            fresh["nano_shape.py"] = (p.returncode, p.stdout or "", p.stderr or "")
    finally:
        shutil.rmtree(os.path.dirname(sandbox), ignore_errors=True)
    return fresh, secs, secs_load, gaps, twice


# --------------------------------------------------------------------------- legs
def leg_spec(w, f):
    rows, names = w.spec.rows, set(w.pages)
    missing = [k for k in rows if k not in names]
    if rows and len(missing) == len(rows):
        f("SPEC", u"本章一页未发布：验收表里 %d 页全部不在 %s" % (len(rows), CHAPTER_DIR))
        return False
    for k in sorted(missing):
        f("COVERAGE", u"表里某页不存在：%s" % k)
    for k in sorted(names - set(rows)):
        f("SPEC", u"%s 发布了但不在验收表里（读者不知道它有没有出处）" % k)
    for k, row in sorted(rows.items()):
        if k in names and not row["bar"]:
            f("SPEC", u"%s 在验收表里，达标线表里没有它那一行" % k)
        if row["script"] and not os.path.isfile(os.path.join(w.nano_dir, row["script"])):
            f("SPEC", u"%s 的复跑物路径不存在：nano/%s" % (k, row["script"]))
    return True


SECTION_RE = r"^##\s+%s\s*$"


def leg_page_shape(w, f):
    for k, text in sorted(w.pages.items()):
        if not text.startswith("---"):
            f("SPEC", u"%s 没有 frontmatter（体裁/日期没有出处）" % k)
        blocks = re.findall(r"^```mermaid[ \t]*\n(.*?)^```", text, re.S | re.M)
        if not blocks:
            f("SPEC", u"%s 没有 Mermaid 图" % k)
        for b in blocks:
            first = b.strip().split("\n")[0]
            if not first.startswith("%%{init:"):
                f("SPEC", u"%s 有 Mermaid 块缺章色主题指令" % k)
            elif w.spec.color and w.spec.color not in first.upper():
                f("SPEC", u"%s 的图不是本章色 #%s" % (k, w.spec.color))
        if "*《图：" not in text:
            f("SPEC", u"%s 没有读者可见图注" % k)
        refs = re.search(SECTION_RE % u"参考资料" + r"\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        n = len(MD_LINK.findall(refs.group(1))) if refs else 0
        if not refs or n < 3:
            f("SPEC", u"%s 的「参考资料」只有 %d 条链接（房规 ≥3）" % (k, n))
        if k == "README.md":
            leg_trio(w, f, text)


def leg_trio(w, f, text):
    goals = re.search(SECTION_RE % u"读完能做到" + r"\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    bullets = len([x for x in (goals.group(1).split("\n") if goals else [])
                   if ITEM_RE.match(x.strip())])
    if bullets < 3:
        f("SPEC", u"README「读完能做到」只有 %d 条（地板 3）" % bullets)
    quiz = re.search(SECTION_RE % u"章末自测" + r"\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    qs = [x.strip() for x in (quiz.group(1).split("\n") if quiz else []) if ITEM_RE.match(x.strip())]
    if len(qs) < 3:
        f("SPEC", u"README「章末自测」只有 %d 题（地板 3）" % len(qs))
    orphan = [q for q in qs if not re.search(u"见[^\\n]{0,60}?\\.md", q)]
    if orphan:
        f("SPEC", u"README 自测有 %d 题没有可解析的出处页（%s）" % (len(orphan), orphan[0][:28]))
    terms = re.search(SECTION_RE % u"术语速查" + r"\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    rows = parse_tables(terms.group(1))[0][1] if terms and parse_tables(terms.group(1)) else []
    if len(rows) < 10:
        f("SPEC", u"README「术语速查」只有 %d 行（地板 10）" % len(rows))
    thin = [r for r in rows if len(r) < 4 or not all(c.strip() for c in r[:4])]
    if thin:
        f("SPEC", u"术语速查有 %d 行不是英文/中文/白话三格齐" % len(thin))


def leg_run(w, f):
    """The 达标线 rows, with every threshold parsed out of spec.md by bar_for()."""
    if w.fresh is None:
        f("COVERAGE", u"RUN 腿未测量：本轮没有复跑（--pages-only 的绿不是达标线通过的绿）")
        return
    for name, (rc, out, err) in sorted(w.fresh.items()):
        if rc != 0:
            f("ARTIFACT", u"复跑物 %s 退出码 %s：%s" % (name, rc, norm(err)[-140:]))
    for k, row in sorted(w.spec.rows.items()):
        bar = row["bar"]
        if not bar:
            continue
        gaps = BAR_CHECKS.get(k)
        if gaps is None:
            f("COVERAGE", u"达标线表里的页 %s 没有对应的判决代码（新页没落判据）" % k)
            continue
        gaps(w, row, f)


def need(pattern, text, what, f, flags=0):
    m = re.search(pattern, text, flags)
    if not m:
        f("COVERAGE", u"%s 读不出：产物里没有匹配 %r 的行" % (what, pattern[:40]))
    return m


def thr(pattern, bar, what, f, cast=float):
    m = re.search(pattern, bar)
    if not m:
        f("COVERAGE", u"达标线读不出：%s 那一行里没有 %s（改表等于改判据，但得写明白）"
          % (what, pattern[:30]))
        return None
    return cast(m.group(1))


def leg_artifact(w, f):
    """Every `text` fence line a page pastes must be printed by a script today, and every number
    in a page's tables must appear in a record.  A page may quote the shape sweep only if it names
    `nano_shape.py` in its own text -- quoting an artifact you never point at is how a table drifts."""
    for k, text in sorted(w.pages.items()):
        script = w.spec.rows.get(k, {}).get("script")
        named = set(re.findall(r"`nano/([A-Za-z0-9_]+\.py)`|`([A-Za-z0-9_]+\.py)`", text))
        scripts = set(x for pair in named for x in pair if x)
        if script:
            scripts.add(script)
        if k == "README.md":
            scripts.update(x for x in RUN_ORDER)
        allowed = "\n".join([w.rec(s) for s in scripts]) or w.all_rec_text()
        for block in re.findall(r"^```text[ \t]*\n(.*?)^```", text, re.S | re.M):
            for ln in [x for x in block.split("\n") if x.strip()]:
                if norm(ln) not in allowed:
                    f("ARTIFACT", u"%s 贴的记录行在今天的产物里没有逐字命中：%r" % (k, ln.strip()[:60]))
        body = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
        # A table cell may legitimately carry a number whose source is the *standard* (a 达标线
        # copied from spec.md) or a frozen CONFIG value, so those two are allowed witnesses too.
        extra = w.spec.md + " " + " ".join(repr(v) for v in (w.config or {}).values())
        for rows in [r for hdr, r in parse_tables(body)]:
            for row in rows:
                for cell in row[1:]:
                    for tok in re.findall(r"\d[\d,]*\.?\d*", cell):
                        t = tok.replace(",", "")
                        if len(t.replace(".", "")) < 3 and "." not in t:
                            continue
                        if t not in allowed and t not in extra:
                            f("ARTIFACT", u"%s 表格里的数字 %s 在任何产物里都找不到（%r）"
                              % (k, tok, cell[:40]))
    for stem, d in sorted(w.records.items()):
        if stem in ("corpus", "vocab"):
            continue
        script = stem + ".py"
        if w.fresh is not None and script in w.fresh and norm(w.fresh[script][1]) != norm(d.get("stdout", "")):
            f("ARTIFACT", u"nano/out/%s.stdout 与今天真跑的输出不一致（页面贴的是旧账）" % stem)


def leg_claim(w, f):
    """Quantitative statements vs the script's own account. Loss/params/MACs exact; seconds by the
    tolerance the spec's 判决口径 row spells out."""
    cfg = w.config
    if cfg is None:
        f("COVERAGE", u"读不到 gptnano.CONFIG，冻结配置对平腿没测量")
    else:
        for key, bound in sorted(w.spec.bounds.items()):
            if key in cfg and cfg[key] > bound:
                f("CLAIM", u"预算硬线越界：%s = %s > %s（规范来自 spec.md）" % (key, cfg[key], bound))
            elif key not in cfg:
                f("COVERAGE", u"预算硬线里的 %s 不在 CONFIG 里" % key)
    budget = need(r"实测 count_params (\d+)", w.rec("nano_budget.py"), u"参数量账", f)
    params = int(budget.group(1)) if budget else None
    lnv = need(r"ln V = (\d+\.\d+)", w.rec("nano_tokenizer.py"), u"ln V", f)
    for k, text in sorted(w.pages.items()):
        body = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
        if params is not None:
            for m in re.finditer(u"参数量[^0-9\n]{0,8}([0-9][0-9,]{2,})", body):
                if int(m.group(1).replace(",", "")) != params:
                    f("CLAIM", u"%s 写的参数量 %s 与参数账的 %d 对不平" % (k, m.group(1), params))
        if lnv:
            for m in re.finditer(r"[lL]n\s*V\s*=\s*([0-9]+\.[0-9]+)", body):
                if m.group(1) != lnv.group(1):
                    f("CLAIM", u"%s 写的 ln V = %s 与产物里的 %s 对不平" % (k, m.group(1), lnv.group(1)))
        allowed = w.seconds_values()
        if w.run_secs:
            allowed.append(w.run_secs)
        if w.run_secs_load:
            allowed.append(w.run_secs_load)
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*秒", body):
            v = float(m.group(1))
            if not any(abs(v - a) <= 0.35 * max(a, 1e-9) for a in allowed):
                f("CLAIM", u"%s 的耗时 %s 秒落在所有产物的耗时读数 ±35%% 之外（%s）"
                  % (k, m.group(1), " ".join("%.1f" % a for a in sorted(allowed)) or "无读数"))
        if k == "README.md":
            leg_frozen_config(w, f, text, params)


def leg_frozen_config(w, f, text, params):
    blocks = re.findall(r"^```json[ \t]*\n(.*?)^```", text, re.S | re.M)
    if not blocks:
        f("CLAIM", u"README 没有冻结配置 ```json 契约（达标线要求它与 CONFIG 对平）")
        return
    try:
        data = json.loads(blocks[0])
    except ValueError as e:
        f("CLAIM", u"README 的冻结配置 JSON 解析不了：%s" % e)
        return
    flat = {}
    for key, val in data.items():
        if isinstance(val, dict):
            for kk, vv in val.items():
                flat[kk] = vv
        else:
            flat[key] = val
    for key in sorted(flat):
        if w.config is None:
            return
        if key not in w.config:
            f("CLAIM", u"README 冻结配置有 CONFIG 里没有的键 %s" % key)
        elif repr(flat[key]) != repr(w.config[key]) and str(flat[key]) != str(w.config[key]):
            f("CLAIM", u"README 冻结配置 %s = %r 与 CONFIG 的 %r 对不平" % (key, flat[key], w.config[key]))
    if params is not None and w.config.get("n_layer") and \
            str(params) not in text.replace(",", ""):
        f("CLAIM", u"README 没有把参数账的 %d 个参数写给读者" % params)


def leg_xref(w, f):
    # GitBook 把中文标题转成拼音 slug，站内 fragment 落不了地（全书 fragment 引用实测为 0），
    # 所以这一腿要求的是「页面级链接 + 句子里点名被引页真实存在的节名」。
    pat = re.compile(u"第\\s*(\\d{1,2})\\s*章[^\\n]{0,60}?(一致|相同|一样|同源|同一条|同一套|同规矩)")
    for k, text in sorted(w.pages.items()):
        for ln in text.split("\n"):
            m = pat.search(ln)
            if not m or m.group(1) == "22":
                continue
            link = next((x for x in MD_LINK.finditer(ln) if x.group(2).startswith("..")), None)
            if not link:
                f("XREF", u"%s 写了「与第 %s 章…%s」却没有站内链接：%s"
                  % (k, m.group(1), m.group(2), ln[:60]))
                continue
            url = link.group(2)
            if "#" in url:
                f("XREF", u"%s 用了站内 fragment %s：中文标题到读者端是拼音 slug，"
                          u"离线构造不出读者能落的锚点，把节名写进句子即可（全书 fragment 引用实测为 0）"
                  % (k, url))
                continue
            tgt = os.path.normpath(os.path.join(w.doc_dir, url))
            if not os.path.isfile(tgt):
                f("XREF", u"%s 引到不存在的页 %s" % (k, url))
                continue
            heads = [squash(h) for h in re.findall(r"^#{2,4}\s+(.*)$",
                                                   io.open(tgt, encoding="utf-8").read(), re.M)]
            squashed = squash(ln)
            if not any(h and h in squashed for h in heads):
                f("XREF", u"%s 引到 %s 却没有点名该页真有的节名（该页节名：%s）"
                  % (k, os.path.basename(url), u" / ".join(heads[:8])))


# --------------------------------------------------------------------------- per-page bars
def bar_tokenizer(w, row, f):
    rec = w.rec("nano_tokenizer.py")
    m = need(r"词表大小 V = (\d+)\s+\(= 语料去重字符数 (\d+)\)", rec, u"分词词表", f)
    if m and m.group(1) != m.group(2):
        f("ARTIFACT", u"词表大小 %s != 去重字符数 %s" % (m.group(1), m.group(2)))
    a = need(r"实际归一化后字符数 = (\d+)", rec, u"字符数", f)
    b = need(r"编码后 id 数 = (\d+)", rec, u"id 数", f)
    if a and b and a.group(1) != b.group(1):
        f("ARTIFACT", u"序列长度 %s != 字符数 %s" % (b.group(1), a.group(1)))
    c = need(r"往返 decode\(encode\(x\)\) == x : (\w+)", rec, u"解码恒等", f)
    if c and c.group(1) != "True":
        f("ARTIFACT", u"decode(encode(x)) != x")


def bar_forward(w, row, f):
    tol = thr(r"≤\s*(\d+(?:\.\d+)?)\s*%", row["bar"], u"前向 loss 偏差", f)
    one = thr(r"=\s*(1(?:\.\d+)?)(?![\d])", row["bar"], u"注意力行和", f)
    rec = w.rec("nano_forward.py")
    if tol is not None:
        m = need(r"相对偏差\s*=\s*(\d+(?:\.\d+)?)\s*%", rec, u"相对偏差读数", f)
        if m and float(m.group(1)) > tol:
            f("ARTIFACT", u"未训练 loss 偏差 %s%% 超过达标线 %s%%" % (m.group(1), tol))
    if one is not None:
        vals = [float(x) for x in re.findall(u"行和 (\\d+\\.\\d+)", rec)]
        if not vals:
            f("COVERAGE", u"产物里没有注意力行和读数")
        elif any(abs(v - one) > 5e-7 for v in vals):
            f("ARTIFACT", u"注意力行和不等于 %s（最差 %.6f）" % (one, max(abs(v - one) for v in vals)))


def bar_budget(w, row, f):
    want = thr(r"（差\s*(\d+)）", row["bar"], u"参数账求和差", f)
    secs = thr(r"≤?\s*(\d+)\s*秒", row["bar"], u"训练预算秒数", f)
    m = need(u"求和 (\\d+)\\s+vs\\s+实测 count_params (\\d+)\\s+差 (-?\\d+)", w.rec("nano_budget.py"),
             u"分模块参数账", f)
    if m and int(m.group(3)) != (want if want is not None else 0):
        f("ARTIFACT", u"分模块求和与实测差 %s（达标线 %s）" % (m.group(3), want))
    if w.run_secs is None:
        f("COVERAGE", u"训练预算未测量（没跑）")
    elif secs is not None and w.run_secs >= secs:
        f("ARTIFACT", u"同一趟两次实跑 %s / %s 秒，快的那次也没进 %s 秒预算（这台机器确实跑不完这个配置）"
          % ("%.1f" % w.run_secs,
             ("%.1f" % w.run_secs_load) if w.run_secs_load else "-", secs))


def bar_backward(w, row, f):
    n = thr(r"≥\s*(\d+)\s*个参数", row["bar"], u"反向抽样数", f)
    tol = thr(r"≤\s*([0-9.eE+-]+)", row["bar"], u"反向相对误差", f)
    mut = thr(u"变异必须 ≥\\s*([0-9.eE+-]+)", row["bar"], u"少算一项的变异", f)
    rec = w.rec("nano_backward.py")
    m = need(u"样本数 = (\\d+)\\s+最大相对误差 = ([0-9.eE+-]+)", rec, u"gradcheck 汇总", f)
    if m:
        if n is not None and int(m.group(1)) < n:
            f("ARTIFACT", u"抽样 %s 个参数，达标线 ≥%s" % (m.group(1), n))
        if tol is not None and float(m.group(2)) > tol:
            f("ARTIFACT", u"最大相对误差 %s > 达标线 %s" % (m.group(2), tol))
    drops = [float(x) for x in re.findall(u"最大相对误差 ([0-9.eE+-]+)\\s+达标线", rec)]
    if mut is not None:
        if len(drops) < 3:
            f("COVERAGE", u"变异只读出 %d 条，种植的反例没跑全" % len(drops))
        elif min(drops) < mut:
            f("ARTIFACT", u"故意少算一项的最大相对误差只有 %.1e（达标线 ≥%s：这项检查抓不到漏算）"
              % (min(drops), mut))


def bar_train(w, row, f):
    frac = thr(r"≤\s*(0?\.\d+)\s*[·x*]", row["bar"], u"末段 loss 系数", f)
    lines = thr(r"≥\s*(\d+)\s*行", row["bar"], u"loss 记录行数", f)
    lnv = need(r"ln V = (\d+\.\d+)", w.rec("nano_tokenizer.py"), u"ln V", f)
    rec = w.rec("nano_train.py")
    m = need(u"末段均值 = ([0-9.]+)\\s+达标线 = ([0-9.]+)\\s+判定 = (\\w+)", rec, u"末段均值", f)
    if m and frac is not None and lnv:
        bar = float(frac) * float(lnv.group(1))
        if float(m.group(1)) > bar:
            f("ARTIFACT", u"末段 loss %.6f > 达标线 %.6f（%.2f x ln V）" % (float(m.group(1)), bar, float(frac)))
        elif u"判定 = OK" not in rec:
            f("COVERAGE", u"脚本自己没给出 OK/MISS 判定行")
    c = need(u"记录行数 = (\\d+)", rec, u"记录行数", f)
    if c and lines is not None and int(c.group(1)) < lines:
        f("ARTIFACT", u"loss 记录 %s 行，达标线 ≥%s" % (c.group(1), lines))
    if w.twice is None:
        f("COVERAGE", u"逐字节相同未测量（只跑了一次）")
    elif w.twice["first_stdout"] != w.twice["second_stdout"]:
        f("ARTIFACT", u"两次训练 stdout 不逐字节相同（%d vs %d 字节）"
          % (len(w.twice["first_stdout"]), len(w.twice["second_stdout"])))
    elif w.twice["second_rc"] != 0:
        f("ARTIFACT", u"第二遍训练退出码 %s" % w.twice["second_rc"])


def bar_sampling(w, row, f):
    nseg = thr(r"≥\s*(\d+)\s*段", row["bar"], u"采样段数", f)
    nchar = thr(r"≥\s*(\d+)\s*字符", row["bar"], u"每段字符数", f)
    rate = thr(r"≥\s*(\d+(?:\.\d+)?)\s*%", row["bar"], u"3-gram 命中率", f)
    rec = w.rec("nano_sample.py")
    lens = [int(x) for x in re.findall(u"生成 (\\d+) 字符", rec)]
    hits = [float(x) for x in re.findall(u"3-gram 命中语料 \\d+/\\d+ = ([\\d.]+)%", rec)]
    if len(lens) < 2 or len(hits) < 2:
        f("COVERAGE", u"采样只解析到 %d 段长度 / %d 个命中率" % (len(lens), len(hits)))
        return
    if nseg is not None and len(lens) < nseg:
        f("ARTIFACT", u"生成 %d 段，达标线 ≥%s" % (len(lens), nseg))
    if nchar is not None and min(lens) < nchar:
        f("ARTIFACT", u"最短一段 %d 字符，达标线 ≥%s" % (min(lens), nchar))
    if rate is not None and min(hits) < rate:
        f("ARTIFACT", u"最差一段 3-gram 命中 %.1f%%，达标线 ≥%s%%" % (min(hits), rate))
    d = need(u"贪心与温度 1\\.0 不同的段数 (\\d+) / (\\d+)", rec, u"贪心/抽样差异", f)
    if d and d.group(1) != d.group(2):
        f("ARTIFACT", u"贪心与温度 1.0 有 %s/%s 段相同" % (d.group(1), d.group(2)))


def bar_export(w, row, f):
    rec = w.rec("nano_export.py")
    s = re.findall(r"sha256 = ([0-9a-f]{64})", rec)
    if len(s) < 2:
        f("COVERAGE", u"导出只读到 %d 个 sha256 读数" % len(s))
    elif s[0] != s[1]:
        f("ARTIFACT", u"重新序列化后 sha256 变了")
    same = need(u"逐位一致: (\\w+)\\s+最大绝对差 = ([0-9.eE+-]+)", rec, u"重载一致性", f)
    if same and (same.group(1) != "True" or float(same.group(2)) != 0.0):
        f("ARTIFACT", u"重载后 logits 不逐位一致（%s / %s）" % (same.group(1), same.group(2)))
    a = need(u"从文件重载 count_params = (\\d+)", rec, u"重载参数量", f)
    b = need(u"分模块求和\\s*= (\\d+)", rec, u"导出侧求和", f)
    c = need(r"实测 count_params (\d+)", w.rec("nano_budget.py"), u"参数账页参数量", f)
    vals = [int(x.group(1)) for x in (a, b, c) if x]
    if len(set(vals)) != 1:
        f("ARTIFACT", u"参数量三处没对平：%s" % vals)


def bar_readme(w, row, f):
    if "README.md" not in w.pages:
        f("COVERAGE", u"导读页不在手上，三件套与冻结配置未测量")


BAR_CHECKS = {"build-01-tokenizer.md": bar_tokenizer, "build-02-forward.md": bar_forward,
              "build-03-budget.md": bar_budget, "build-04-backward.md": bar_backward,
              "build-05-train.md": bar_train, "build-06-sampling.md": bar_sampling,
              "build-07-export.md": bar_export, "README.md": bar_readme}


# --------------------------------------------------------------------------- driver
def measure(repo, run=True, pages_only=False, inject=None):
    doc = os.path.join(repo, "docs", CHAPTER_DIR)
    nano = os.path.join(repo, "nano")
    spec_path = os.path.join(doc, SPEC_NAME)
    inject = inject or {}
    findings, used = [], set()

    def f(bucket, msg):
        used.add(bucket)
        findings.append((bucket, msg))

    spec_md = inject.get("spec_md", None)
    if spec_md is None:
        if not os.path.isfile(spec_path):
            f("SPEC", u"规范来源 %s/%s 不存在——本章的一切声明没有出处" % (CHAPTER_DIR, SPEC_NAME))
            return findings, {"pages": 0, "rows": 0, "disposition": {}}
        spec_md = norm(io.open(spec_path, encoding="utf-8").read())
    spec = Spec(spec_md, spec_path)
    for g in spec.gaps:
        f("COVERAGE", g)
    pages = inject.get("pages")
    if pages is None:
        pages = {}
        for p in sorted(glob.glob(os.path.join(doc, "*.md"))):
            if os.path.basename(p) != SPEC_NAME:
                pages[os.path.basename(p)] = norm(io.open(p, encoding="utf-8").read())
    records = inject.get("records")
    if records is None:
        records = {}
        for p in sorted(glob.glob(os.path.join(nano, "out", "*.std*"))):
            stem, ext = os.path.splitext(os.path.basename(p))
            records.setdefault(stem, {})[ext.lstrip(".")] = norm(io.open(p, encoding="utf-8").read())
        if not records:
            f("COVERAGE", u"产物目录为空：%s" % os.path.join("nano", "out"))
    fresh, run_secs, gaps, twice = inject.get("fresh"), inject.get("run_secs"), [], inject.get("twice")
    run_secs_load = inject.get("run_secs_load")
    if fresh is None and run and not pages_only and os.path.isdir(nano):
        fresh, run_secs, run_secs_load, gaps, twice = run_scripts(nano)
    for g in gaps:
        f("COVERAGE", g)
    w = World(spec, doc, pages, records, fresh, run_secs,
              inject.get("config", load_config(nano)), nano, run_secs_load)
    w.twice = twice
    alive = leg_spec(w, f)
    if alive:
        leg_page_shape(w, f)
        leg_run(w, f)
        leg_artifact(w, f)
        leg_claim(w, f)
        leg_xref(w, f)
    for b in sorted(used):
        if spec.disposition.get(b, "undeclared") == "undeclared":
            findings.append(("COVERAGE", u"判据用了桶 %s，但判决口径表里没有它" % b))
    return findings, {"pages": len(pages), "rows": len(spec.rows), "buckets": sorted(used),
                      "run_secs": run_secs, "run_secs_load": run_secs_load,
                      "disposition": spec.disposition}


def report(findings, stats):
    secs = stats.get("run_secs")
    load = stats.get("run_secs_load")
    print("chapter-22 judge: pages=%d rows=%d run=%s buckets=%s findings=%d"
          % (stats.get("pages", 0), stats.get("rows", 0),
             ("%.1fs" % secs) if secs else "not-run",
             ",".join(stats.get("buckets", []) or []) or "-", len(findings)))
    if secs and load and load > secs:
        print("  这台机器同一趟的两次实跑：%.1f 秒（判预算用的是这次）/ %.1f 秒（负载读数）" % (secs, load))
    for b, msg in findings:
        print("  %-9s %s" % (b, msg))


def utf8_out():
    """The findings carry CJK and the transcripts are UTF-8; this console defaults to cp936."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def real_main(argv):
    utf8_out()
    if reject_unknown(argv, FLAGS, "check_build_llm_from_scratch"):
        return 2
    if "--selftest" in argv:
        return selftest()
    if "--head-control" in argv:
        return head_control()
    skip = "--pages-only" in argv
    findings, stats = measure(REPO, run=not skip, pages_only=skip)
    # A broken ruler must speak through the same channel as a content defect: COVERAGE, exit 2.
    # An assert here would exit 1 and get read as "the chapter has a bug" instead.
    if stats["rows"] < MIN_ROWS:
        findings.append(("COVERAGE", u"验收表只解析出 %d 行（地板 %d）——判据在量空集"
                         % (stats["rows"], MIN_ROWS)))
    report(findings, stats)
    return verdict(findings, stats)


def verdict(findings, stats):
    disp = stats.get("disposition") or {}
    red = [x for x in findings if disp.get(x[0], "red") == "red"]
    cov = [x for x in findings if disp.get(x[0], "red") != "red"]
    if red:
        return 1
    return 2 if cov else 0


# --------------------------------------------------------------------------- planted controls
# spec.md promises 「判据自带两类反例：每桶都在种植缺陷上真红过一次」。That promise is paid for
# here: one mutation per bucket, each diffed against the *unmutated injected chapter*, so a control
# can never look red simply because the baseline was already red for the same words.
CONTROLS = ["clean-arm", "spec-unreadable", "chapter-unpublished", "no-mermaid", "refs-section-gone",
            "quiz-no-pointer", "fence-digit", "table-cell-number", "params-claim", "seconds-claim",
            "xref-no-link", "xref-fragment", "xref-no-section", "over-budget-train", "missing-page",
            "bucket-undeclared"]


def read_chapter(repo):
    doc = os.path.join(repo, "docs", CHAPTER_DIR)
    pages = {}
    for p in sorted(glob.glob(os.path.join(doc, "*.md"))):
        if os.path.basename(p) != SPEC_NAME:
            pages[os.path.basename(p)] = norm(io.open(p, encoding="utf-8").read())
    return pages, norm(io.open(os.path.join(doc, SPEC_NAME), encoding="utf-8").read())


def fresh_from_records(nano_dir):
    """A stand-in for this pass's transcripts: the committed records, so an arm can inject one
    number (a training wall clock) without inventing a whole chapter's output."""
    fresh = {}
    for name in RUN_ORDER + ["nano_shape.py"]:
        stem = os.path.splitext(name)[0]
        parts = []
        for stream in ("stdout", "stderr"):
            path = os.path.join(nano_dir, "out", stem + "." + stream)
            parts.append(norm(io.open(path, encoding="utf-8").read()) if os.path.isfile(path) else "")
        fresh[name] = (0, parts[0], parts[1])
    return fresh


def ruler_findings(stats):
    """Judge health, reported as COVERAGE so it can never be read as a pass."""
    if stats.get("rows", 0) < MIN_ROWS:
        return [("COVERAGE", u"验收表只解析出 %s 行（地板 %d）——判据在量空集"
                 % (stats.get("rows", 0), MIN_ROWS))]
    return []


def sub1(text, old, new, cid):
    assert text.count(old) == 1, u"%s：变异锚点在页面上出现 %d 次，这个控制等于没种" % (cid, text.count(old))
    return text.replace(old, new, 1)


def selftest():
    utf8_out()
    pages, spec_md = read_chapter(REPO)
    base, bstats = measure(REPO, run=False, pages_only=True,
                           inject={"pages": pages, "spec_md": spec_md})
    base_set, base_code = set(base), verdict(base, bstats)
    out = []

    def arm(cid, pg, sp, bucket, needle, want_code, **extra):
        inj = dict({"pages": pg, "spec_md": sp}, **extra)
        got, stats = measure(REPO, run=False, pages_only=True, inject=inj)
        got = got + ruler_findings(stats)
        new = [x for x in got if x not in base_set]
        code = verdict(got, stats)
        if bucket is None:                      # the control that the arms themselves are honest
            hit, why = (not new), "新增 finding=%d" % len(new)
        else:
            hit = [x for x in new if x[0] == bucket and needle in x[1]]
            why = hit[0][1][:64] if hit else "未落进 %s；新增=%s" % (bucket, [m[:36] for _, m in new[:2]])
        out.append((cid, bool(hit), code == want_code, bucket or "-", code, why))

    def one(name):
        return dict(pages, **{name: pages[name]})

    arm("clean-arm", dict(pages), spec_md, None, None, base_code)
    arm("spec-unreadable", dict(pages), "", "COVERAGE", u"规范表读不出", 1)
    arm("chapter-unpublished", {}, spec_md, "SPEC", u"本章一页未发布", 1)
    t = one("build-02-forward.md")
    cut = re.sub(r"```mermaid[ \t]*\n.*?\n```", "", t["build-02-forward.md"], count=1, flags=re.S)
    assert cut != t["build-02-forward.md"], "no-mermaid：页面上找不到 Mermaid 块"
    t["build-02-forward.md"] = cut
    arm("no-mermaid", t, spec_md, "SPEC", u"没有 Mermaid 图", 1)
    t = sub1(one("build-03-budget.md")["build-03-budget.md"], u"## 参考资料", u"## 参考文献", "refs-section-gone")
    arm("refs-section-gone", dict(pages, **{"build-03-budget.md": t}), spec_md,
        "SPEC", u"「参考资料」只有", 1)
    rd = one("README.md")["README.md"]
    quiz_sec = re.search(SECTION_RE % u"章末自测" + r"\n(.*?)(?=^## |\Z)", rd, re.S | re.M)
    assert quiz_sec, u"quiz-no-pointer：导读里没有「章末自测」节，控制无处可种"
    q6 = [ln for ln in quiz_sec.group(1).split("\n") if ln.startswith(u"6. ")]
    assert len(q6) == 1, u"quiz-no-pointer：自测第 6 题有 %d 行，锚点不唯一" % len(q6)
    t = sub1(rd, q6[0], q6[0].replace(u"（提示：见 ", u"（提示：翻 "), "quiz-no-pointer")
    assert t != rd, u"quiz-no-pointer：这一题里没有「（提示：见 」，变异等于没种"
    arm("quiz-no-pointer", dict(pages, **{"README.md": t}), spec_md, "SPEC", u"没有可解析的出处页", 1)
    t = one("build-05-train.md")["build-05-train.md"]
    m = re.search(r"```text[ \t]*\n(.*?)\n```", t, re.S)
    assert m, "fence-digit：页面上找不到 ```text 记录块"
    lines = m.group(1).split("\n")
    idx = next((i for i, ln in enumerate(lines) if re.search(r"\d", ln)), None)
    assert idx is not None, "fence-digit：记录块里没有可改的数字"
    lines[idx] = re.sub(r"\d", lambda x: "1" if x.group(0) != "1" else "2", lines[idx], count=1)
    assert lines[idx] != m.group(1).split("\n")[idx], "fence-digit：改动没生效"
    t = t.replace(m.group(1), "\n".join(lines), 1)
    arm("fence-digit", dict(pages, **{"build-05-train.md": t}), spec_md,
        "ARTIFACT", u"没有逐字命中", 1)
    t = one("build-03-budget.md")["build-03-budget.md"] + u"\n\n| 控制 | 数 |\n|---|---|\n| 种进去的假读数 | 987654 |\n"
    arm("table-cell-number", dict(pages, **{"build-03-budget.md": t}), spec_md,
        "ARTIFACT", u"表格里的数字 987654", 1)
    t = one("build-03-budget.md")["build-03-budget.md"] + u"\n\n控制：这一句的参数量 3999 是种进去的假账。\n"
    arm("params-claim", dict(pages, **{"build-03-budget.md": t}), spec_md, "CLAIM", u"对不平", 1)
    t = one("build-05-train.md")["build-05-train.md"] + u"\n\n控制：这一句的耗时 999.9 秒落在所有读数之外。\n"
    arm("seconds-claim", dict(pages, **{"build-05-train.md": t}), spec_md, "CLAIM", u"耗时 999.9 秒", 1)
    xref_base = one("build-04-backward.md")["build-04-backward.md"]
    t = xref_base + u"\n\n控制：这一页与第 19 章同一条硬规矩，但没有链接。\n"
    arm("xref-no-link", dict(pages, **{"build-04-backward.md": t}), spec_md, "XREF", u"却没有站内链接", 1)
    t = xref_base + u"\n\n控制：这一页与第 19 章的三条硬规矩同一条规矩，见 " \
        u"[第 19 章动手实验](../19-labs/README.md#三条硬规矩)。\n"
    arm("xref-fragment", dict(pages, **{"build-04-backward.md": t}), spec_md,
        "XREF", u"用了站内 fragment", 1)
    t = xref_base + u"\n\n控制：这一页与第 19 章同一条硬规矩，链接在 " \
        u"[第 19 章的六个实验清单](../19-labs/README.md) 里，但那页没有这个节名。\n"
    arm("xref-no-section", dict(pages, **{"build-04-backward.md": t}), spec_md,
        "XREF", u"却没有点名该页真有的节名", 1)
    t = one("build-04-backward.md")["build-04-backward.md"] + u"\n\n控制：这一页与第 19 章同一条硬规矩，但没有链接。\n"
    # The budget now judges on the faster of two runs, so the estimator needs its own反例: an arm
    # where *both* runs blow the bar must still go ARTIFACT red (a min() that only ever passes is
    # a disconnected knob).
    arm("over-budget-train", dict(pages), spec_md, "ARTIFACT", u"两次实跑", 1,
        fresh=fresh_from_records(os.path.join(REPO, "nano")),
        run_secs=200.0, run_secs_load=260.0,
        twice={"first_stdout": "x", "second_stdout": "x", "second_rc": 0})
    pg = dict(pages)
    pg.pop("build-06-sampling.md")
    arm("missing-page", pg, spec_md, "COVERAGE", u"表里某页不存在：build-06-sampling.md", 2)
    xref_row = [ln for ln in spec_md.split("\n") if ln.startswith(u"| `XREF`")]
    assert len(xref_row) == 1, u"bucket-undeclared：判决口径表里 XREF 行有 %d 条" % len(xref_row)
    arm("bucket-undeclared", dict(pages, **{"build-04-backward.md": t}),
        spec_md.replace(xref_row[0], ""), "COVERAGE", u"判决口径表里没有它", 1)

    for cid, hit, code_ok, bucket, code, why in out:
        print("  %-20s bucket=%-9s exit=%d %-4s %s" % (cid, bucket, code,
                                                       "OK" if (hit and code_ok) else "MISS", why))
    ran = [x[0] for x in out]
    assert ran == CONTROLS, u"控制清单跑漏：实跑 %d 条 / 声明 %d 条（%s）" % (
        len(ran), len(CONTROLS), set(CONTROLS) ^ set(ran))
    assert len(out) == len(CONTROLS), "控制条数与声明不符"
    bad = [x[0] for x in out if not (x[1] and x[2])]
    fired = set(x[3] for x in out if x[3] != "-" and x[1])
    need_buckets = {"SPEC", "ARTIFACT", "CLAIM", "XREF", "COVERAGE"}
    print("controls: ran=%d fired=%d buckets=%s clean-exit=%d"
          % (len(out), len(out) - len(bad), ",".join(sorted(fired)), base_code))
    assert not bad, u"这些控制没有落进自己的桶：%s" % ", ".join(bad)
    assert need_buckets <= fired, u"有桶从没在种植缺陷上红过：%s" % ", ".join(sorted(need_buckets - fired))
    assert base_code == 2, "干净臂必须是 COVERAGE(2)，否则差分失去意义（实为 %d）" % base_code
    return 0


def head_control():
    """The second反例 spec.md promises: run *this* judge over the tree as it stood at HEAD, where
    chapter 22 is not published at all. It must come back red, not dead."""
    utf8_out()
    tmp = os.path.join(tempfile.gettempdir(), "r101-head-control")
    if os.path.isdir(tmp):
        shutil.rmtree(tmp, ignore_errors=True)
    def git(*a):
        return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    p = git("worktree", "add", "--detach", tmp, "HEAD")
    if p.returncode != 0:
        print("worktree add failed: %s" % (p.stderr or p.stdout)[-300:])
        return 2
    try:
        dst = os.path.join(tmp, "tools", "checks")
        shutil.copy(os.path.abspath(__file__), os.path.join(dst, os.path.basename(__file__)))
        q = subprocess.run([sys.executable, os.path.join(dst, os.path.basename(__file__)),
                            "--pages-only"], cwd=tmp, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        out = norm(q.stdout or "")
        print("HEAD control: exit=%d\n%s" % (q.returncode, out))
        assert "Traceback" not in (q.stderr or ""), "判据在 HEAD 树上直接崩了，不是一次红判决"
        assert q.returncode == 1, "HEAD 上一章未发布，判据必须整场红（exit 1），实得 %d" % q.returncode
        assert "SPEC" in out, "HEAD 上的红没有落进 SPEC 桶"
        return 0
    finally:
        r = git("worktree", "remove", "--force", tmp)
        if r.returncode != 0:
            print("NOTE worktree remove failed: %s" % (r.stderr or r.stdout)[-200:])


if __name__ == "__main__":
    sys.exit(real_main(sys.argv[1:]))
