import ctypes, sys, time
from ctypes import wintypes
from PIL import Image
import ctl

user32 = ctypes.windll.user32
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

def post_click(cx, cy):
    h = ctl.game_hwnd()
    lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
    user32.PostMessageW(h, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.1)
    user32.PostMessageW(h, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.12)
    user32.PostMessageW(h, WM_LBUTTONUP, 0, lp)
    print("post-click", cx, cy)

if __name__ == "__main__":
    x, y = int(sys.argv[1]), int(sys.argv[2])
    post_click(x, y)
    time.sleep(1.8)
    ctl.cap(sys.argv[3] if len(sys.argv) > 3 else "pc.png")
