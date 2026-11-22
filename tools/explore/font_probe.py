import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import UnityPy, os, sys, io

BUNDLE = paths.FONT_BUNDLE

env = UnityPy.load(BUNDLE)
chars = set()
fonts = []
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        tt = obj.read_typetree(check_read=False)
    except Exception:
        continue
    ct = tt.get("m_CharacterTable")
    if ct:
        fonts.append((tt.get("m_Name"), len(ct)))
        for c in ct:
            try:
                chars.add(int(c.get("m_Unicode")))
            except Exception:
                pass
print("font assets:", fonts)
print("total chars in atlas:", len(chars))

probe = {
    "，U+FF0C": 0xFF0C, "。U+3002": 0x3002, "：U+FF1A": 0xFF1A, "（U+FF08": 0xFF08,
    "）U+FF09": 0xFF09, "、U+3001": 0x3001, "！U+FF01": 0xFF01, "？U+FF1F": 0xFF1F,
    "「U+300C": 0x300C, "」U+300D": 0x300D, "…U+2026": 0x2026, "—U+2014": 0x2014,
    "·U+00B7": 0x00B7, "“U+201C": 0x201C, "”U+201D": 0x201D, "你": 0x4F60, "的": 0x7684,
    "开": 0x5F00, "始": 0x59CB, "％U+FF05": 0xFF05, "－U+FF0D": 0xFF0D, "～U+FF5E": 0xFF5E,
}
for k, v in probe.items():
    print(f"  {k}: {'YES' if v in chars else 'MISSING'}")

missing_sample = [c for c in chars if c > 0x2000][:20]
print("sample cjk codepoints present:", [hex(c) for c in missing_sample])
