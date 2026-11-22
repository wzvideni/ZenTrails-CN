import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import struct, json, io

PATH = paths.ASSEMBLY_CSHARP
raw = open(PATH, "rb").read()

# --- locate #US heap by parsing the CLI metadata root ---
# Find "BSJB" signature
i = raw.find(b"BSJB")
assert i > 0
ver_len = struct.unpack_from("<i", raw, i + 12)[0]
p = i + 16 + ver_len
p += 2  # flags
nstreams = struct.unpack_from("<H", raw, p)[0]
p += 2
heaps = {}
for _ in range(nstreams):
    off, size = struct.unpack_from("<ii", raw, p)
    p += 8
    end = raw.index(b"\x00", p)
    name = raw[p:end].decode()
    p = (end + 4) & ~3
    heaps[name] = raw[i + off: i + off + size]
print({k: len(v) for k, v in heaps.items()})

us = heaps["#US"]
def read_compressed(b, o):
    x = b[o]
    if x & 0x80 == 0:
        return x, o + 1
    if x & 0xC0 == 0x80:
        return ((x & 0x3F) << 8) | b[o + 1], o + 2
    return ((x & 0x1F) << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3], o + 4

strings = []
o = 1
while o < len(us):
    ln, o2 = read_compressed(us, o)
    if ln == 0:
        o = o2
        continue
    if ln & 1:  # trailing flag byte
        ln -= 1
    s = us[o2:o2 + ln].decode("utf-16-le", "replace")
    strings.append(s)
    o = o2 + ln + (1 if (us[o2 - 1] if False else 0) else 0)
    # re-read: length includes flag; advance exactly ln bytes (already trimmed flag)
    o = o2 + ln + ((1 if False else 0))

print("count:", len(strings))
json.dump(strings, open(paths.scratch("asm_us.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("chars:", sum(len(s) for s in strings))
for s in strings[:30]:
    print(repr(s[:110]))
