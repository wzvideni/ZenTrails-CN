import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import os
import struct
import json
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

DATA = paths.DATA
FILES = ["level0", "level1", "level2", "sharedassets0.assets", "sharedassets1.assets",
         "sharedassets2.assets", "resources.assets"]
TARGETS = {"WIDTH", "GLOW", "LAYER ORDER", "SPEED", "LENGTH", "ANGLE", "DRAW TRAIL"}

gen = TypeTreeGenerator("2019.1.8f1")
gen.load_local_dll_folder(os.path.join(DATA, "Managed"))

scripts = {}
env = UnityPy.load(os.path.join(DATA, "globalgamemanagers.assets"))
for obj in env.objects:
    if obj.type.name == "MonoScript":
        tt = obj.read_typetree()
        scripts[obj.path_id] = (tt.get("m_ClassName"), tt.get("m_Namespace") or "", tt.get("m_AssemblyName"))
print("scripts:", len(scripts))


def ppid(d):
    if d is None:
        return None
    if isinstance(d, int):
        return d
    if isinstance(d, dict):
        for k in ("path_id", "m_PathID", "PathID"):
            if k in d:
                return d[k]
        for v in d.values():
            if isinstance(v, dict):
                r = ppid(v)
                if r is not None:
                    return r
    return None


report = []
for name in FILES:
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        continue
    env = UnityPy.load(p)
    go_name = {}
    go_comps = {}
    rects = {}
    transform_owner = {}
    for obj in env.objects:
        if obj.type.name == "GameObject":
            try:
                tt = obj.read_typetree()
            except Exception:
                continue
            go_name[obj.path_id] = tt.get("m_Name")
            go_comps[obj.path_id] = [ppid(c) for c in tt.get("m_Component", [])]
        elif obj.type.name in ("RectTransform", "Transform"):
            try:
                tt = obj.read_typetree()
            except Exception:
                continue
            owner = ppid(tt.get("m_GameObject"))
            transform_owner[obj.path_id] = owner
            if obj.type.name == "RectTransform":
                rects[owner] = tt

    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        try:
            _, scid = struct.unpack_from("<iq", raw, 16)
        except Exception:
            continue
        info = scripts.get(scid)
        if not info:
            continue
        cls, ns, asm = info
        if "TMP" not in cls:
            continue
        fullname = f"{ns}.{cls}" if ns else cls
        try:
            tt = obj.read_typetree(gen.get_nodes_up(asm, fullname))
        except Exception:
            continue
        txt = tt.get("m_text")
        if not isinstance(txt, str) or txt.strip() not in TARGETS:
            continue
        gopid = ppid(tt.get("m_GameObject"))
        rt = rects.get(gopid)
        entry = {
            "file": name,
            "text": txt,
            "go": go_name.get(gopid),
            "align": tt.get("m_textAlignment"),
            "hAlign": tt.get("m_HorizontalAlignment"),
            "vAlign": tt.get("m_VerticalAlignment"),
            "fontSize": tt.get("m_fontSize"),
            "margin": tt.get("m_margin"),
            "wrap": tt.get("m_enableWordWrapping"),
        }
        if rt:
            entry["rt"] = {
                "anchoredPosition": rt.get("m_AnchoredPosition"),
                "sizeDelta": rt.get("m_SizeDelta"),
                "pivot": rt.get("m_Pivot"),
                "anchorMin": rt.get("m_AnchorMin"),
                "anchorMax": rt.get("m_AnchorMax"),
            }
            par = ppid(rt.get("m_Father"))
            entry["parent"] = go_name.get(transform_owner.get(par))
        report.append(entry)

for e in report:
    print(json.dumps(e, ensure_ascii=False))
print("total:", len(report))
json.dump(report, open(paths.scratch("layout_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
