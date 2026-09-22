"""Regenerate tools/checks/data/traditional_chars.txt from OpenCC's authoritative table.

Run manually only (it touches the network); the checker itself is offline. The written file is
reviewed by check_char_sanity.py's shape controls, so a truncated fetch fails loudly instead of
reading as "the corpus is clean".
"""
import io, os, urllib.request

URL = "https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/TSCharacters.txt"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traditional_chars.txt")

raw = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}),
                             timeout=90).read().decode("utf-8")
rows = [ln for ln in raw.split("\n") if ln and not ln.startswith("#")]
trad = {}
for ln in rows:
    key, _, vals = ln.partition("\t")
    if len(key) != 1:
        continue
    simplified = set(vals.split())
    if simplified and key not in simplified:
        trad[key] = " ".join(sorted(simplified))
with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# Traditional-form characters that have a different simplified form.\n")
    fh.write("# Source: OpenCC data/dictionary/TSCharacters.txt (Apache-2.0)\n")
    fh.write("# From %s\n" % URL)
    fh.write("# One entry per line: <traditional char>\t<simplified form(s)>\n")
    fh.write("# Keys only from that table whose simplified form differs, so characters written\n")
    fh.write("# identically in both standards (台 著 里 生) are absent — they are not defects.\n")
    fh.write("# Regenerate: python tools/checks/data/fetch_traditional_chars.py\n")
    for ch in sorted(trad):
        fh.write("%s\t%s\n" % (ch, trad[ch]))
print("table rows=%d single-char trad keys=%d -> %s" % (len(rows), len(trad), OUT))
