import os as _os, sys as _sys
_sys.path.insert(0, os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
import paths  # noqa: E402  仓库/游戏目录的统一约定（见 tools/paths.py）

import ctl, time, shutil, os, sys

DUMP = paths.DUMP_TEXTS
OUT = paths.DUMPS
os.makedirs(OUT, exist_ok=True)


def dump(label):
    """Press F9 in-game and copy the dump to dumps/<label>.txt"""
    ctl.key(0x78)  # F9
    time.sleep(0.8)
    if os.path.exists(DUMP):
        dst = os.path.join(OUT, label + '.txt')
        shutil.copyfile(DUMP, dst)
        print('dump ->', dst, os.path.getsize(dst))
    else:
        print('!! no dump file')


def run(steps):
    for s in steps:
        parts = s.split(':')
        op = parts[0]
        if op == 'click':
            ctl.click(int(parts[1]), int(parts[2]))
        elif op == 'key':
            ctl.key(int(parts[1], 16))
        elif op == 'cap':
            ctl.cap(parts[1])
        elif op == 'dump':
            dump(parts[1])
        elif op == 'wait':
            time.sleep(float(parts[1]))


if __name__ == '__main__':
    run(sys.argv[1:])
