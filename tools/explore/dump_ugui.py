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
for obj in UnityPy.load(os.path.join(DATA, "globalgamemanagers.assets")).objects:
    if obj.type.name == "MonoScript":
        tt = obj.read_typetree()
        scripts[obj.path_id] = (tt.get("m_ClassName"), tt.get("m_Namespace") or "", tt.get("m_AssemblyName"))

texts = set()
inputs = set()
placeholders = 0
for name in FILES:
    env = UnityPy.load(os.path.join(DATA, name))
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        try:
            scid = struct.unpack_from("<q", raw, 20)[0]
        except Exception:
            continue
        info = scripts.get(scid)
        if not info:
            continue
        cls, ns, asm = info
        full = f"{ns}.{cls}" if ns else cls
        if cls not in ("Text", "TMP_InputField", "TMP_Dropdown", "TextMeshProUGUI"):
            continue
        try:
            tt = obj.read_typetree(gen.get_nodes_up(asm, full))
        except Exception:
            continue
        if cls == "Text":
            v = tt.get("m_Text")
            if isinstance(v, str) and v.strip():
                texts.add(v)
        elif cls == "TMP_InputField":
            for k in ("m_Text", "m_Placeholder"):
                pass
        elif cls == "TMP_Dropdown":
            for o in tt.get("m_Options", []) or []:
                v = o.get("m_Text") if isinstance(o, dict) else None
                if isinstance(v, str) and v.strip():
                    texts.add(v)

print("legacy Text / dropdown unique:", len(texts))
for t in sorted(texts)[:40]:
    print(repr(t[:100]))

# combine with tmp texts + code strings for a grand total
tmp = json.load(open(paths.scratch("tmp_texts.json"), encoding="utf-8"))
us = json.load(open(paths.scratch("asm_us.json"), encoding="utf-8"))
allset = set(tmp) | texts
print("scene total:", len(allset), sum(len(x) for x in allset))
