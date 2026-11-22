import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import os
import shutil
import sys
import time

ROOT = paths.ROOT
GAME = paths.GAME
BASE = ROOT          # 兼容原有调用
REQ = paths.CLICK_REQ
LOG = paths.CLICK_LOG
DUMP = paths.DUMP_TEXTS
DUMPS = paths.DUMPS
os.makedirs(DUMPS, exist_ok=True)


def click_exact(path):
    with open(REQ, "w", encoding="utf-8", newline="\n") as f:
        f.write("click=" + path + "\n")
    ctl.focus()
    time.sleep(0.15)
    ctl.key(0x7A)
    time.sleep(0.7)
    try:
        return open(LOG, encoding="utf-8").read().strip()
    except OSError:
        return "(no log)"


def click_sub(path):
    with open(REQ, "w", encoding="utf-8", newline="\n") as f:
        f.write("click:" + path + "\n")
    ctl.focus()
    time.sleep(0.15)
    ctl.key(0x7A)
    time.sleep(0.7)
    try:
        return open(LOG, encoding="utf-8").read().strip()
    except OSError:
        return "(no log)"


def dump(label):
    ctl.focus()
    time.sleep(0.15)
    ctl.key(0x78)
    time.sleep(0.9)
    dst = os.path.join(DUMPS, label + ".txt")
    shutil.copy(DUMP, dst)
    return dst


def main():
    for step in sys.argv[1:]:
        kind, _, arg = step.partition(":")
        if kind == "c":
            print("CLICK", arg)
            print(click_exact(arg))
        elif kind == "s":
            print("SUBCLICK", arg)
            print(click_sub(arg))
        elif kind == "k":
            ctl.focus()
            time.sleep(0.15)
            ctl.key(int(arg, 16))
            print("KEY", arg)
        elif kind == "p":
            ctl.cap(os.path.join(BASE, arg))
            print("CAP", arg)
        elif kind == "d":
            print("DUMP", dump(arg))
        elif kind == "w":
            time.sleep(float(arg))
        else:
            print("??", step)


sys.path.insert(0, BASE)
import ctl  # noqa: E402

main()
