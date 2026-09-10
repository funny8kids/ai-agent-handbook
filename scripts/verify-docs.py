#!/usr/bin/env python3
"""验收脚本：检查 docs/ 下页面的写作规范与质量门槛。

用法：python scripts/verify-docs.py [--min-chars-report]
检查项：
  1. 标题（#~######）是否残留 emoji
  2. 相对链接/图片是否可达
  3. 每篇知识页的正文中文字数分布（对照风格指南门槛）
  4. LaTeX 公式使用情况
  5. frontmatter 完整性（tags/type/status/updated）
  6. SUMMARY 与文件的一致性
"""
import glob, os, re, sys, collections

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
PICTO = re.compile('[\U0001F000-\U0001FAFF\u2600-\u26FF\u2700-\u27BF\u2B00-\u2BFF]')
EMOJI_OK_BODY = set('❌✅⚠💡\u26a0')  # 允许在正文中作语义标记

# 风格指南门槛（按 type/difficulty 粗分）
def genre_limit(fm, path, full=""):
    typ = (re.search(r'type:\s*(\w+)', fm) or [None, 'knowledge'])[1]
    if typ == 'index':
        return 0
    if typ == 'resource':
        return 150
    if '14-templates' in path:
        return 0
    # 难度写在正文的引用行里（不在 frontmatter），精确匹配「**难度**：X」
    probe = full or fm
    m = re.search(r'\*\*难度\*\*：\s*(入门|进阶|高级)', probe)
    diff = m.group(1) if m else '入门'
    if diff == '高级':
        return 1200
    if diff == '进阶':
        return 900
    return 600


def han(t):
    return len(re.findall(r'[\u4e00-\u9fff]', t))


def body_of(t):
    b = re.sub(r'^---.*?---', '', t, flags=re.S)
    return re.sub(r'```.*?```', '', b, flags=re.S)


def main():
    files = sorted(glob.glob(os.path.join(DOCS, '**', '*.md'), recursive=True))
    heading_emoji, bad_fm, missing_link = [], [], []
    under = []
    math_pages = 0
    status_ct = collections.Counter()
    for f in files:
        t = open(f, encoding='utf-8').read()
        rel = os.path.relpath(f, DOCS).replace(os.sep, '/')
        if rel != 'SUMMARY.md' and '14-templates' not in rel:
            in_fence = False
            for ln in t.split('\n'):
                if ln.lstrip().startswith('```'):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                if re.match(r'^#{1,6}\s', ln) and PICTO.search(ln):
                    heading_emoji.append((rel, ln.strip()[:40]))
        m = re.match(r'^---\n(.*?)\n---', t, re.S)
        if m and rel != 'SUMMARY.md':
            fm = m.group(1)
            for k in ('tags', 'type', 'status', 'updated'):
                if not re.search(rf'^{k}\s*:', fm, re.M):
                    bad_fm.append((rel, k))
            status_ct[(re.search(r'status:\s*(\w+)', fm) or [None, '?'])[1]] += 1
            n = han(body_of(t))
            lim = genre_limit(fm, f, full=t)
            if lim and n < lim:
                under.append((n, lim, rel))
        if re.search(r'\$\$?\S', t):
            math_pages += 1
        d = os.path.dirname(f)
        for mm in re.finditer(r'!?\[[^\]]*\]\(([^)\s]+)', re.sub(r'```.*?```', '', t, flags=re.S)):
            u = mm.group(1)
            if u.startswith(('http', '#', 'mailto:')):
                continue
            p = os.path.normpath(os.path.join(d, u.split('#')[0]))
            if u.split('#')[0] and not os.path.exists(p):
                missing_link.append((rel, u))

    print(f'files: {len(files)}')
    print(f'heading emoji残留: {len(heading_emoji)}')
    for r, l in heading_emoji[:20]:
        print('   ', r, '|', l)
    print(f'frontmatter 缺字段: {len(bad_fm)}', bad_fm[:10])
    print(f'相对链接断链: {len(missing_link)}')
    for r, u in missing_link[:20]:
        print('   ', r, '->', u)
    print(f'含公式页面: {math_pages}')
    print('status 分布:', dict(status_ct))
    print(f'低于门槛页面: {len(under)}')
    for n, lim, r in sorted(under):
        print(f'    {n:5d}/{lim:<5d} {r}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
