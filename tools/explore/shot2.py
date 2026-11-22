import ctypes, time, sys
from ctypes import wintypes
from PIL import ImageGrab

user32 = ctypes.windll.user32
SW_MINIMIZE = 6
SW_RESTORE = 9

def wins():
    out = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        if not user32.IsWindowVisible(h):
            return True
        n = user32.GetWindowTextLengthW(h)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(h, buf, n + 1)
            r = wintypes.RECT()
            user32.GetWindowRect(h, ctypes.byref(r))
            out.append((h, buf.value, (r.left, r.top, r.right, r.bottom)))
        return True
    user32.EnumWindows(cb, 0)
    return out

allw = wins()
game = [w for w in allw if w[1] == "Zen Trails"]
print("game:", game)
if not game:
    sys.exit("game window missing")

gh = game[0][0]
# minimize everything else that is large/visible
for h, t, r in allw:
    if h != gh and (r[2] - r[0]) > 400 and (r[3] - r[1]) > 300:
        user32.ShowWindow(h, SW_MINIMIZE)
time.sleep(0.8)

user32.ShowWindow(gh, SW_RESTORE)
# foreground lock workaround
user32.keybd_event(0x12, 0, 0, 0)
user32.keybd_event(0x12, 0, 2, 0)
user32.SetForegroundWindow(gh)
user32.BringWindowToTop(gh)
time.sleep(2.5)

r = wintypes.RECT()
user32.GetWindowRect(gh, ctypes.byref(r))
im = ImageGrab.grab() if (r.right - r.left) >= 1900 else ImageGrab.grab(
    bbox=(r.left, r.top, r.right, r.bottom))
im.save(sys.argv[1] if len(sys.argv) > 1 else "shot_win.png")
print("saved", im.size, "rect", (r.left, r.top, r.right, r.bottom))
