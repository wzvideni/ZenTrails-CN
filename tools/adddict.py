import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import json, os, re, sys

BASE = paths.ROOT
DATA = paths.TRANSLATION
OUT_DIR = paths.TEXT_DIR
if "--out" in _sys.argv:                          # 打包脚本用它指到临时目录
    OUT_DIR = _sys.argv[_sys.argv.index("--out") + 1]
OUT = os.path.join(OUT_DIR, "zh_extra.txt")

NORM = {
    "\uff0c": ",", "\uff1a": ":", "\uff08": "(", "\uff09": ")", "\uff01": "!",
    "\uff1f": "?", "\uff1b": ";", "\uff0f": "/", "\uff05": "%", "\uff0d": "-",
    "\uff5e": "~", "\u2014": "-", "\u2013": "-", "\u2026": "...",
    "\u201c": "\u300c", "\u201d": "\u300d", "\u2018": "\u300e", "\u2019": "\u300f",
}

atlas = set(json.load(open(os.path.join(DATA, "font_chars.json"))))
ASCII = set(range(0x20, 0x7F))


def normalize(s):
    for k, v in NORM.items():
        s = s.replace(k, v)
    return s


def bad_chars(s):
    out = set()
    for ch in s:
        cp = ord(ch)
        if cp in ASCII or cp in atlas:
            continue
        out.add(ch)
    return out


def esc_key(s):
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")


lines = []
seen = {}
problems = []
for ln in open(os.path.join(DATA, "extra_zh.txt"), encoding="utf-8"):
    ln = ln.rstrip("\n").rstrip("\r")
    if not ln.strip() or ln.startswith("#"):
        continue
    if "\t" not in ln:
        problems.append("no tab: " + ln)
        continue
    k, v = ln.split("\t", 1)
    v = normalize(v.strip())
    if k in seen:
        problems.append("dup key: " + k)
        continue
    seen[k] = v
    bad = bad_chars(v)
    if bad:
        problems.append("BAD GLYPHS %s: %s" % (k, "".join(sorted(bad))))
    if "=" in k:
        problems.append("key has '=': " + k)
        continue
    lines.append("%s=%s" % (esc_key(k), v))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("# 补充词条：图案预设名与零散界面词\n")
    f.write("\n".join(lines))
    f.write("\n")

print("entries:", len(lines))
print("bytes:", os.path.getsize(OUT))
if problems:
    print("PROBLEMS:")
    for p in problems:
        print(" ", p)
