import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import re, sys, io, os, json, glob

TXT = paths.TEXT_DIR

def load_dict():
    keys = {}
    for f in glob.glob(os.path.join(TXT, "*.txt")):
        if os.path.basename(f).startswith("_"):
            continue
        for line in io.open(f, encoding="utf-8-sig"):
            line = line.rstrip("\n").rstrip("\r")
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            if line.startswith('r:"') or line.startswith("r:"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            keys[unesc(k)] = v
    return keys

def unesc(s):
    return s.replace("\\n", "\n").replace("\\r", "\r")

def norm(s):
    # mimic what XUnity/build sees: trimmed
    return s.strip()

CJK = re.compile(r"[\u3400-\u9fff]")
ENG = re.compile(r"[A-Za-z]{2,}")

def analyse(path, dic):
    rows = []
    cur_sec = ""
    for line in io.open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("--") or line.startswith("==="):
            cur_sec = line
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        p, flag = parts[0], parts[1]
        text = unesc("\t".join(parts[2:]))
        if not text.strip():
            continue
        has_cjk = bool(CJK.search(text))
        has_eng = bool(ENG.search(text))
        key = norm(text)
        hit = key in dic
        rows.append(dict(path=p, flag=flag, text=text, cjk=has_cjk, eng=has_eng, hit=hit, sec=cur_sec))
    return rows

def main():
    dic = load_dict()
    allrows = []
    for f in sys.argv[1:]:
        allrows += analyse(f, dic)
    # untranslated: has english letters and no CJK
    bad = [r for r in allrows if r["eng"] and not r["cjk"]]
    # english but key exists in dict -> translation did not apply
    miss_key = [r for r in bad if not r["hit"]]
    key_exists = [r for r in bad if r["hit"]]
    seen = set()
    print("total rows: %d, dict keys: %d" % (len(allrows), len(dic)))
    print("\n== ENGLISH, NO DICT KEY (%d unique) ==" % len({r["text"] for r in miss_key}))
    for r in miss_key:
        t = r["text"].replace("\n", "\\n")
        if t in seen:
            continue
        seen.add(t)
        print("%-6s %-70s | %s" % (r["flag"], t[:70], r["path"][-60:]))
    print("\n== ENGLISH, KEY EXISTS BUT NOT APPLIED (%d unique) ==" % len({r["text"] for r in key_exists}))
    seen = set()
    for r in key_exists:
        t = r["text"].replace("\n", "\\n")
        if t in seen:
            continue
        seen.add(t)
        print("%-6s %-70s | %s" % (r["flag"], t[:70], r["path"][-60:]))
    json.dump(allrows, open(paths.scratch("coverage.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

main()
