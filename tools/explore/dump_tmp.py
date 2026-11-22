import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import os, struct, json, collections
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

GAME_ROOT = paths.GAME
DATA = os.path.join(GAME_ROOT, "Zen Trails_Data")
FILES = ["level0", "level1", "level2", "sharedassets0.assets", "sharedassets1.assets",
         "sharedassets2.assets", "resources.assets", "globalgamemanagers.assets"]

gen = TypeTreeGenerator("2019.1.8f1")
gen.load_local_dll_folder(os.path.join(DATA, "Managed"))

def read_pptr(raw, off):
    file_id, path_id = struct.unpack_from("<iq", raw, off)
    return file_id, path_id

def read_string(raw, off):
    ln, = struct.unpack_from("<i", raw, off)
    s = raw[off + 4:off + 4 + ln].decode("utf-8", "replace")
    nxt = (off + 4 + ln + 3) & ~3
    return s, nxt

results = []          # (file, path_id, class, name, text)
class_counter = collections.Counter()
errors = collections.Counter()

for name in FILES:
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        continue
    env = UnityPy.load(p)
    scripts = {}
    for obj in env.objects:
        if obj.type.name == "MonoScript":
            try:
                tt = obj.read_typetree()
            except Exception:
                continue
            scripts[obj.path_id] = (tt.get("m_ClassName"), tt.get("m_Namespace") or "",
                                    tt.get("m_AssemblyName"))
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        try:
            _, go_id = read_pptr(raw, 0)
            # m_Enabled byte + 3 align, then m_Script
            _, script_id = read_pptr(raw, 16)
            go_name, _ = read_string(raw, 28)
        except Exception:
            continue
        cls, ns, asm = scripts.get(script_id, (None, None, None))
        if not cls:
            continue
        class_counter[f"{asm}:{ns}.{cls}"] += 1
        fullname = f"{ns}.{cls}" if ns else cls
        try:
            nodes = gen.get_nodes_up(asm, fullname)
            tt = obj.read_typetree(nodes)
        except Exception as e:
            errors[f"{fullname}: {type(e).__name__}"] += 1
            continue
        if isinstance(tt, dict) and "m_text" in tt:
            results.append({"file": name, "path_id": obj.path_id, "class": fullname,
                            "go": go_name, "text": tt["m_text"],
                            "font": (tt.get("m_fontAsset") or {}) if isinstance(tt.get("m_fontAsset"), dict) else None})

print("classes seen:", class_counter.most_common(25))
print("errors:", errors.most_common(10))
print("objects with m_text:", len(results))
texts = collections.OrderedDict()
for r in results:
    t = r["text"]
    if isinstance(t, str) and t.strip():
        texts.setdefault(t, r)
print("unique non-empty:", len(texts), "chars:", sum(len(k) for k in texts))

json.dump(results, open(paths.scratch("tmp_objects.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump(texts, open(paths.scratch("tmp_texts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for k in list(texts)[:25]:
    print(repr(k[:100]))
