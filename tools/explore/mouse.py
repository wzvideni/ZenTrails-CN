import ctypes, time
from ctypes import wintypes

user32 = ctypes.windll.user32

# --- SendInput based mouse (hardware-like, spans frames) ---
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_VIRTUALDESK = 0x4000


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_void_p)]


class _INPUTunion(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTunion)]


def _send(flags, dx=0, dy=0):
    inp = INPUT(type=0, u=_INPUTunion(mi=MOUSEINPUT(dx, dy, 0, flags, 0, None)))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def abs_move(x, y):
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    ax = int(x * 65535 / (sw - 1))
    ay = int(y * 65535 / (sh - 1))
    _send(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, ax, ay)


def sclick(x, y, hold=0.07):
    abs_move(x, y)
    time.sleep(0.12)
    _send(MOUSEEVENTF_LEFTDOWN)
    time.sleep(hold)
    _send(MOUSEEVENTF_LEFTUP)
    time.sleep(0.06)


def sdouble(x, y):
    abs_move(x, y)
    time.sleep(0.1)
    for _ in range(2):
        _send(MOUSEEVENTF_LEFTDOWN)
        time.sleep(0.05)
        _send(MOUSEEVENTF_LEFTUP)
        time.sleep(0.05)
