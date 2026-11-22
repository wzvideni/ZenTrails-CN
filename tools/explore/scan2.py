import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import os, struct, json, re, collections

GAME = paths.GAME
FILES = ["Zen Trails_Data/level0", "Zen Trails_Data/level1", "Zen Trails_Data/level2",
         "Zen Trails_Data/sharedassets0.assets", "Zen Trails_Data/sharedassets1.assets",
         "Zen Trails_Data/sharedassets2.assets", "Zen Trails_Data/resources.assets",
         "Zen Trails_Data/globalgamemanagers.assets"]

def scan(path):
    data = open(path, "rb").read()
    n = len(data)
    found = []
    i = 0
    while i < n - 4:
        ln = struct.unpack_from("<i", data, i)[0]
        if 1 <= ln <= 4000 and i + 4 + ln <= n:
            chunk = data[i + 4:i + 4 + ln]
            # printable ascii + common utf8
            ok = True
            try:
                s = chunk.decode("utf-8")
            except UnicodeDecodeError:
                ok = False
                s = None
            if ok and s and all((31 < ord(c) < 127) or c in "\n\t" or ord(c) > 160 for c in s):
                letters = sum(1 for c in s if c.isalpha())
                if letters >= 2 and letters / max(1, len(s)) > 0.45:
                    found.append((i, s))
                    i += 4 + ln
                    i = (i + 3) & ~3
                    continue
        i += 1
    return found

all_texts = collections.OrderedDict()
per_file = {}
for f in FILES:
    p = os.path.join(GAME, f)
    if not os.path.exists(p):
        continue
    res = scan(p)
    per_file[f] = len(res)
    for off, s in res:
        if s not in all_texts:
            all_texts[s] = {"file": os.path.basename(f), "offset": off}

print("per file:", per_file)
print("unique strings:", len(all_texts))
print("total chars:", sum(len(k) for k in all_texts))
lens = sorted(len(k) for k in all_texts)
print("len median:", lens[len(lens)//2], "max:", lens[-1])
json.dump(all_texts, open(paths.scratch("strings_raw.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for k in list(all_texts)[:30]:
    print(repr(k[:110]))
