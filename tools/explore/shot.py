import ctypes, time, sys
from ctypes import wintypes
from PIL import ImageGrab

user32 = ctypes.windll.user32

def find(title_part="Zen Trails"):
    hwnds = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        n = user32.GetWindowTextLengthW(h)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(h, buf, n + 1)
            r = wintypes.RECT()
            user32.GetWindowRect(h, ctypes.byref(r))
            hwnds.append((h, buf.value, (r.left, r.top, r.right, r.bottom)))
        return True
    user32.EnumWindows(cb, 0)
    return [x for x in hwnds if title_part.lower() in x[1].lower()]

wins = find()
for w in wins:
    print(w)
if not wins:
    print("no window found")
    sys.exit(1)

h = wins[0][0]
user32.ShowWindow(h, 9)       # SW_RESTORE
user32.SetForegroundWindow(h)
time.sleep(1.5)
r = wins[0][2]
im = ImageGrab.grab(bbox=r)
im.save(sys.argv[1] if len(sys.argv) > 1 else "shot_win.png")
print("saved", im.size)
