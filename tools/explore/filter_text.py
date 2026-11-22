import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import json, re, collections
d = json.load(open(paths.scratch("strings_raw.json"), encoding="utf-8"))

BAD_SUB = ("/", "\\", ".mat", ".png", ".ttf", ".asset", ".prefab", "m_", "Unity", "Packages/",
           "Library/", "Assembly")
def looks_ui(s: str) -> bool:
    if len(s) < 3 or len(s) > 900:
        return False
    if any(b in s for b in BAD_SUB):
        return False
    if re.fullmatch(r"[A-Za-z0-9_\[\] ()+.\-]+", s) and " " not in s and len(s) <= 22:
        # could be a GameObject / property name -- keep only if it has lowercase words mix? drop for now
        return False
    if re.search(r"[A-Za-z]", s) is None:
        return False
    # require at least one space-separated word pair, or punctuation typical of sentences
    if " " in s or len(s) > 18 or any(c in s for c in ".!?,:"):
        return True
    return False

ui = {k: v for k, v in d.items() if looks_ui(k)}
print("ui candidates:", len(ui), "chars:", sum(len(k) for k in ui))
json.dump(ui, open(paths.scratch("strings_ui.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for k in sorted(ui, key=len)[:60]:
    print(repr(k))
