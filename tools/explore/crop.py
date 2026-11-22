import sys
from PIL import Image, ImageChops


def crop(before, after, out, pad=8):
    a = Image.open(before).convert("RGB")
    b = Image.open(after).convert("RGB")
    if a.size != b.size:
        b.save(out)
        return
    d = ImageChops.difference(a, b).convert("L")
    # ignore tiny animation noise
    d = d.point(lambda v: 255 if v > 24 else 0)
    box = d.getbbox()
    if not box:
        b.save(out)
        print("no change", out)
        return
    l, t, r, bo = box
    l = max(0, l - pad); t = max(0, t - pad)
    r = min(b.size[0], r + pad); bo = min(b.size[1], bo + pad)
    if (r - l) < 60: r = min(b.size[0], l + 60)
    if (bo - t) < 40: bo = min(b.size[1], t + 40)
    b.crop((l, t, r, bo)).save(out)
    print("%s  box=%s  size=%dx%d" % (out, (l, t, r, bo), r - l, bo - t))


if __name__ == "__main__":
    args = sys.argv[1:]
    for i in range(0, len(args), 3):
        crop(args[i], args[i + 1], args[i + 2])
