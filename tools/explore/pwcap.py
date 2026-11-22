import ctypes, sys
from ctypes import wintypes
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
PW_RENDERFULLCONTENT = 0x00000002

def find(part="Zen Trails"):
    res = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        n = user32.GetWindowTextLengthW(h)
        if n:
            b = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(h, b, n + 1)
            if b.value.strip().lower() == part.lower():
                r = wintypes.RECT()
                user32.GetWindowRect(h, ctypes.byref(r))
                res.append((h, b.value, r))
        return True
    user32.EnumWindows(cb, 0)
    return res

w = find()
print("windows:", [(x[0], x[1], (x[2].right, x[2].bottom)) for x in w])
if not w:
    sys.exit("no game window")
h = w[0][0]
r = w[0][2]
W, H = r.right - r.left, r.bottom - r.top

hdc = user32.GetWindowDC(h)
mdc = gdi32.CreateCompatibleDC(hdc)
bmp = gdi32.CreateCompatibleBitmap(hdc, W, H)
gdi32.SelectObject(mdc, bmp)
ok = user32.PrintWindow(h, mdc, PW_RENDERFULLCONTENT)
print("PrintWindow:", ok)

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

bi = BITMAPINFOHEADER()
bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
bi.biWidth = W
bi.biHeight = -H
bi.biPlanes = 1
bi.biBitCount = 32
bi.biCompression = 0
buf = ctypes.create_string_buffer(W * H * 4)
gdi32.GetDIBits(mdc, bmp, 0, H, buf, ctypes.byref(bi), 0)
im = Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1).convert("RGB")
out = sys.argv[1] if len(sys.argv) > 1 else "pw.png"
im.save(out)
print("saved", out, im.size, "extrema", im.getextrema())
gdi32.DeleteObject(bmp)
gdi32.DeleteDC(mdc)
user32.ReleaseDC(h, hdc)
