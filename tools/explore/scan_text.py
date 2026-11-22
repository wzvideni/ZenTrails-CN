import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import json, os, sys, collections
import UnityPy

GAME = paths.DATA
FILES = ["level0", "level1", "level2", "sharedassets0.assets", "sharedassets1.assets",
         "sharedassets2.assets", "resources.assets", "globalgamemanagers.assets"]

def type_tree_has_text(tt):
    return isinstance(tt, dict) and "m_text" in tt

out = collections.OrderedDict()
per_file = collections.Counter()
scripts = collections.Counter()

for name in FILES:
    p = os.path.join(GAME, name)
    if not os.path.exists(p):
        continue
    env = UnityPy.load(p)
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tt = obj.read_typetree(check_read=False)
        except Exception:
            continue
        if not type_tree_has_text(tt):
            continue
        scripts[tt.get("m_Name", "?")] += 1
        txt = tt.get("m_text")
        if isinstance(txt, str) and txt.strip():
            key = txt
            if key not in out:
                out[key] = {"file": name, "path_id": obj.path_id}
            per_file[name] += 1

print("files:", dict(per_file))
print("monobehaviours with m_text:", len(scripts))
print("unique non-empty texts:", len(out))
total_chars = sum(len(k) for k in out)
print("total chars:", total_chars)
print("non-ascii texts:", sum(1 for k in out if any(ord(c) > 127 for c in k)))

with open(paths.scratch("strings_raw.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

# sample
for k in list(out)[:40]:
    print(repr(k[:120]))
