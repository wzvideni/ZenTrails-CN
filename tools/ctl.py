import ctypes, sys, time
from ctypes import wintypes
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32
PW = 0x2

def game_hwnd():
    res = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        n = user32.GetWindowTextLengthW(h)
        if n:
            b = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(h, b, n + 1)
            if b.value.strip() == "Zen Trails":
                res.append(h)
        return True
    user32.EnumWindows(cb, 0)
    return res[0] if res else None

def focus():
    h = game_hwnd()
    user32.ShowWindow(h, 9)
    fg = user32.GetForegroundWindow()
    tid_fg = user32.GetWindowThreadProcessId(fg, None)
    tid_me = kernel32.GetCurrentThreadId()
    user32.AttachThreadInput(tid_fg, tid_me, True)
    user32.SetForegroundWindow(h)
    user32.BringWindowToTop(h)
    user32.SetFocus(h)
    user32.AttachThreadInput(tid_fg, tid_me, False)
    time.sleep(0.5)
    print("foreground ok:", user32.GetForegroundWindow() == h)
    return h

def client_rect(h):
    r = wintypes.RECT()
    user32.GetClientRect(h, ctypes.byref(r))
    return r.right - r.left, r.bottom - r.top

def cap(path, crop=True):
    h = game_hwnd()
    W, H = client_rect(h)
    hdc = user32.GetWindowDC(h)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, W, H)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(h, mdc, PW)
    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
    bi = BIH()
    bi.biSize = ctypes.sizeof(BIH); bi.biWidth = W; bi.biHeight = -H
    bi.biPlanes = 1; bi.biBitCount = 32; bi.biCompression = 0
    buf = ctypes.create_string_buffer(W * H * 4)
    gdi32.GetDIBits(mdc, bmp, 0, H, buf, ctypes.byref(bi), 0)
    im = Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1).convert("RGB")
    im.save(path)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(h, hdc)
    print("captured", path, im.size)

def click(cx, cy):
    h = focus()
    pt = wintypes.POINT(int(cx), int(cy))
    user32.ClientToScreen(h, ctypes.byref(pt))
    user32.SetCursorPos(pt.x, pt.y)
    time.sleep(0.2)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.12)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    print("clicked client", cx, cy, "-> screen", pt.x, pt.y)
    time.sleep(1.6)

def drag(x1, y1, x2, y2, right=True, steps=20):
    h = focus()
    p1 = wintypes.POINT(int(x1), int(y1))
    user32.ClientToScreen(h, ctypes.byref(p1))
    down = 0x0008 if right else 0x0002
    up = 0x0010 if right else 0x0004
    user32.SetCursorPos(p1.x, p1.y)
    time.sleep(0.15)
    user32.mouse_event(down, 0, 0, 0, 0)
    time.sleep(0.15)
    for i in range(1, steps + 1):
        cx = int(x1 + (x2 - x1) * i / steps)
        cy = int(y1 + (y2 - y1) * i / steps)
        pt = wintypes.POINT(cx, cy)
        user32.ClientToScreen(h, ctypes.byref(pt))
        user32.SetCursorPos(pt.x, pt.y)
        time.sleep(0.012)
    time.sleep(0.15)
    user32.mouse_event(up, 0, 0, 0, 0)
    print("dragged", x1, y1, "->", x2, y2)
    time.sleep(1.2)


def key(vk):
    h = focus()
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.1)
    user32.keybd_event(vk, 0, 2, 0)
    print("key", hex(vk))
    time.sleep(1.2)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "cap":
        cap(sys.argv[2])
    elif cmd == "click":
        click(int(sys.argv[2]), int(sys.argv[3]))
        if len(sys.argv) > 4:
            cap(sys.argv[4])
    elif cmd == "drag":
        drag(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
        if len(sys.argv) > 6:
            cap(sys.argv[6])
    elif cmd == "key":
        key(int(sys.argv[2], 16))
        if len(sys.argv) > 3:
            cap(sys.argv[3])
    elif cmd == "seq":
        # seq "click:960:585" "cap:a.png" "key:1B" ...
        for step in sys.argv[2:]:
            parts = step.split(":")
            if parts[0] == "click":
                click(int(parts[1]), int(parts[2]))
            elif parts[0] == "key":
                key(int(parts[1], 16))
            elif parts[0] == "cap":
                cap(parts[1])
            elif parts[0] == "wait":
                time.sleep(float(parts[1]))
