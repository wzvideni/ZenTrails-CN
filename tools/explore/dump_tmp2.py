import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import os, struct, json, collections
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

DATA = paths.DATA
FILES = ["level0", "level1", "level2", "sharedassets0.assets", "sharedassets1.assets",
         "sharedassets2.assets", "resources.assets"]

gen = TypeTreeGenerator("2019.1.8f1")
gen.load_local_dll_folder(os.path.join(DATA, "Managed"))

# script path_id -> (class, ns, asm)
scripts = {}
env = UnityPy.load(os.path.join(DATA, "globalgamemanagers.assets"))
for obj in env.objects:
    if obj.type.name == "MonoScript":
        tt = obj.read_typetree()
        scripts[obj.path_id] = (tt.get("m_ClassName"), tt.get("m_Namespace") or "",
                                tt.get("m_AssemblyName"))
print("scripts:", len(scripts))

def read_pptr(raw, off):
    return struct.unpack_from("<iq", raw, off)

def read_string(raw, off):
    ln, = struct.unpack_from("<i", raw, off)
    return raw[off + 4:off + 4 + ln].decode("utf-8", "replace")

results = []
unresolved = 0
errors = collections.Counter()
classes = collections.Counter()

for name in FILES:
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        continue
    env = UnityPy.load(p)
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        try:
            _, scid = read_pptr(raw, 16)
            go_name = read_string(raw, 28)
        except Exception:
            continue
        info = scripts.get(scid)
        if not info:
            unresolved += 1
            continue
        cls, ns, asm = info
        fullname = f"{ns}.{cls}" if ns else cls
        classes[fullname] += 1
        if "TMP" not in cls and "Text" not in cls:
            continue
        try:
            tt = obj.read_typetree(gen.get_nodes_up(asm, fullname))
        except Exception as e:
            errors[f"{fullname}:{type(e).__name__}"] += 1
            continue
        if isinstance(tt, dict):
            results.append({"file": name, "path_id": obj.path_id, "class": fullname,
                            "go": go_name, "text": tt.get("m_text")})

print("unresolved scripts:", unresolved)
print("classes:", classes.most_common(12))
print("errors:", errors.most_common(5))
print("text objects:", len(results))
texts = collections.OrderedDict()
for r in results:
    t = r.get("text")
    if isinstance(t, str) and t.strip():
        texts.setdefault(t, {"file": r["file"], "go": r["go"], "cls": r["class"]})
print("unique:", len(texts), "chars:", sum(len(k) for k in texts))
json.dump(results, open(paths.scratch("tmp_objects.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(texts, open(paths.scratch("tmp_texts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k in list(texts)[:20]:
    print(repr(k[:100]))
