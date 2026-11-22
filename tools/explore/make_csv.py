import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import json, re, csv, os

BASE = paths.ROOT
tmp = json.load(open(os.path.join(BASE, "tmp_texts.json"), encoding="utf-8"))
us = json.load(open(os.path.join(BASE, "asm_us.json"), encoding="utf-8"))

SKIP_EXACT = {"_", "?", "X", "x", "A", "B", "G", "H", "R", "S", "V", "W", "HS", "HV", "SV",
              "\u200b", "#FFFFFF", "999", "Vol", "1", "0", "No", "Yes", "y", "n"}
def is_junk(s):
    s2 = s.strip().replace("\u200b", "")
    if not s2:
        return True
    if s2 in SKIP_EXACT:
        return True
    if re.fullmatch(r"[\d\.\-+%/:]+", s2):
        return True
    if re.fullmatch(r"[A-Za-z]", s2):
        return True
    if s2.startswith("#") and len(s2) <= 9:
        return True
    if re.match(r"^(Assets/|Resources/|Managed/|https?://)", s2):
        return True
    if re.fullmatch(r"[\w./\\-]+\.(mat|png|ttf|asset|prefab|dll|mndla)", s2):
        return True
    return False

rows = []
seen = set()
for en, meta in tmp.items():
    if is_junk(en):
        continue
    key = en.strip()
    if key in seen:
        continue
    seen.add(key)
    rows.append(("场景/预制体", key, meta.get("go", ""), meta.get("cls", "")))

code_prose = []
for s in us:
    if is_junk(s):
        continue
    if s.strip() in seen:
        continue
    if not re.search(r"[A-Za-z]{3}", s):
        continue
    if re.fullmatch(r"[\w./\\-]+", s):     # identifiers / keys / paths
        continue
    if re.match(r"^[a-z]+[A-Z]", s):       # camelCase key
        continue
    if s.startswith("1Tut") or s.startswith("00"):
        continue
    code_prose.append(s.strip())

for s in code_prose:
    if s in seen:
        continue
    seen.add(s)
    rows.append(("代码", s, "", ""))

rows.sort(key=lambda r: (r[0], -len(r[1])))

out = os.path.join(BASE, "ZenTrails_文本清单.csv")
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["#", "来源", "英文原文", "中文译文", "对象/字段"])
    for i, (src, en, go, cls) in enumerate(rows, 1):
        w.writerow([i, src, en, "", f"{go} {cls}".strip()])

print("rows:", len(rows))
print("chars:", sum(len(r[1]) for r in rows))
print("scene rows:", sum(1 for r in rows if r[0] == "场景/预制体"), "code rows:", sum(1 for r in rows if r[0] == "代码"))
print("out:", out)
