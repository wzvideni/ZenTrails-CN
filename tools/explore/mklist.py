import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import csv, os, json

BASE = paths.ROOT
rows = list(csv.reader(open(os.path.join(BASE, "ZenTrails_文本清单.csv"), encoding="utf-8-sig")))
hdr, rows = rows[0], rows[1:]

out = []
for r in rows:
    idx, src, en, zh, meta = r[0], r[1], r[2], r[3], r[4]
    disp = en.replace("\r\n", "\n").replace("\n", "⏎")
    out.append(f"{idx}\t{src}\t⟦{disp}⟧\t{meta}")

with open(os.path.join(BASE, "list.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("rows:", len(out))
print("chars:", sum(len(r[2]) for r in rows))
