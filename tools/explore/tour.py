import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import os
import sys
import time

sys.path.insert(0, paths.TOOLS)
import ctl
import qa

BASE = paths.ROOT


def shot(name):
    p = os.path.join(BASE, name)
    ctl.cap(p)
    return p


def tour(name, path, dump=True, close=True):
    before = shot("_before.png")
    print("OPEN  ", qa.click_exact(path))
    time.sleep(1.4)
    after = shot("%s.png" % name)
    os.system('python "%s\\crop.py" "%s" "%s" "c_%s.png"' % (BASE, before, after, name))
    if dump:
        qa.dump(name)
    if close:
        print("CLOSE ", qa.click_exact(path))
        time.sleep(0.9)
        shot("_before.png")


if __name__ == "__main__":
    tour(sys.argv[1], sys.argv[2], dump=(len(sys.argv) < 4))
