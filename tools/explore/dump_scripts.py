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

scripts = {}
env = UnityPy.load(os.path.join(DATA, "globalgamemanagers.assets"))
for obj in env.objects:
    if obj.type.name == "MonoScript":
        tt = obj.read_typetree()
        scripts[obj.path_id] = (tt.get("m_ClassName"), tt.get("m_Namespace") or "", tt.get("m_AssemblyName"))

SKIP_NS = ("UnityEngine", "TMPro", "Unity.", "Facepunch")

def walk(tt, prefix, out):
    if isinstance(tt, dict):
        for k, v in tt.items():
            walk(v, f"{prefix}.{k}" if prefix else k, out)
    elif isinstance(tt, list):
        for i, v in enumerate(tt):
            walk(v, f"{prefix}[{i}]", out)
    elif isinstance(tt, str):
        if tt.strip():
            out.append((prefix, tt))

records = []
class_counter = collections.Counter()
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
            scid = struct.unpack_from("<q", raw, 20)[0]
            ln = struct.unpack_from("<i", raw, 28)[0]
            go_name = raw[32:32 + ln].decode("utf-8", "replace")
        except Exception:
            continue
        info = scripts.get(scid)
        if not info:
            continue
        cls, ns, asm = info
        fullname = f"{ns}.{cls}" if ns else cls
        if any(fullname.startswith(s) for s in SKIP_NS):
            continue
        class_counter[fullname] += 1
        try:
            tt = obj.read_typetree(gen.get_nodes_up(asm, fullname))
        except Exception:
            continue
        out = []
        walk(tt, "", out)
        for key, val in out:
            if key in ("m_Name",):
                continue
            records.append({"file": name, "go": go_name, "cls": fullname, "field": key, "value": val})

print("game classes:", class_counter.most_common(40))
print("string fields:", len(records))
uniq = collections.OrderedDict()
for r in records:
    uniq.setdefault(r["value"], r)
print("unique values:", len(uniq), "chars:", sum(len(k) for k in uniq))
json.dump(records, open(paths.scratch("script_strings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
