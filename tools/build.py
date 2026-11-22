import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import csv, os, re, json

BASE = paths.ROOT
DATA = paths.TRANSLATION
OUT_DIR = paths.TEXT_DIR

rows = list(csv.reader(open(os.path.join(DATA, "ZenTrails_文本清单.csv"), encoding="utf-8-sig")))[1:]
src = {int(r[0]): r[2] for r in rows}

zh = {}
for fn in ("zh_01.txt", "zh_02.txt", "zh_03.txt", "zh_04.txt"):
    for ln in open(os.path.join(DATA, fn), encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.strip():
            continue
        idx, val = ln.split("\t", 1)
        zh[int(idx)] = val

DENY = {63, 79, 82, 83, 84, 86, 87, 88, 89, 90, 91, 92, 94, 98, 100, 105, 106, 107, 108, 109,
        111, 112, 118, 119, 128, 132, 135, 136, 139, 142, 143, 147, 156, 161, 172, 182, 192,
        206, 262, 290, 332, 372, 384, 481, 482}

# 字体图集缺 U+FF00 区块与 U+2018-201F 等，统一替换成图集里存在的字形
NORM = {
    "\uff0c": ",",   # ，-> ,
    "\uff1a": ":",   # ：-> :
    "\uff08": "(",   # （-> (
    "\uff09": ")",   # ）-> )
    "\uff01": "!",   # ！-> !
    "\uff1f": "?",   # ？-> ?
    "\uff1b": ";",   # ；-> ;
    "\uff0f": "/",   # ／-> /
    "\uff05": "%",   # ％-> %
    "\uff0d": "-",   # －-> -
    "\uff5e": "~",   # ～-> ~
    "\u2014": "-",   # —  -> -
    "\u2013": "-",   # –  -> -
    "\u2026": "...", # …  -> ...
    "\u201c": "\u300c",  # “ -> 「
    "\u201d": "\u300d",  # ” -> 」
    "\u2018": "\u300e",  # ‘ -> 『
    "\u2019": "\u300f",  # ’ -> 』
    "\u00b7": "\u00b7",  # ·  保留
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
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\\", "\\\\").replace("\n", "\\n")
    return s

lines = []
missing = []
problems = {}
for idx in sorted(src):
    if idx in DENY:
        continue
    en = src[idx]
    zhv = zh.get(idx)
    if zhv is None:
        missing.append(idx)
        continue
    if zhv.strip() == "SKIP":
        continue
    zhv = normalize(zhv)
    bad = bad_chars(zhv)
    if bad:
        problems[idx] = "".join(sorted(bad))
    lines.append(f"{esc_key(en)}={zhv}")
    if en != en.strip():
        lines.append(f"{esc_key(en.strip())}={zhv}")

print("entries:", len(lines), "missing:", missing)
print("values with unsupported glyphs:", len(problems))
for k, v in list(problems.items())[:30]:
    print("   ", k, v, [hex(ord(c)) for c in v])

bad_lines = [l for l in lines if l.count("=") > 1]
print("lines with extra '=':", len(bad_lines))

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "zhuanti.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

regex = [
    r'r:"^# OF RECURSIONS$"=递归次数',
    r'r:"^SPEED: (.*)$"=速度:$1',
    r'r:"^ZOOM: (.*)$"=缩放:$1',
    r'r:"^MUSIC: (.*)$"=音乐:$1',
    r'r:"^SCOOCH: (.*)$"=微移:$1',
    r'r:"^PAGE: (.*)$"=页:$1',
    r'r:"^MENU: (.*)$"=菜单:$1',
    r'r:"^SET GROUP: (.*)$"=设置组:$1',
    r'r:"^RECALL GROUP: (.*)$"=调出组:$1',
    r'r:"^SORT BY: (.*)$"=排序方式:$1',
    r'r:"^UNDO: (.*)$"=撤销:$1',
    r'r:"^REDO: (.*)$"=重做:$1',
    r'r:"^Uploaded: (.*)$"=上传于:$1',
    r'r:"^(\d+) ENTRIES FOUND ON PAGE (\d+)$"=共 $1 个作品,第 $2 页',
    r'r:"^Size: (.*)$"=大小:$1',
    r'r:"^YOU CAN ONLY UPLOAD ONCE PER 30 SECONDS. TIME REMAINING =(.*)$"=每 30 秒只能上传一次。剩余时间 = $1',
]
with open(os.path.join(OUT_DIR, "zz_regex.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(regex) + "\n")
print("regex entries:", len(regex))
