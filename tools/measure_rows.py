import sys
from PIL import Image


def analyze(path, x0=940, x1=1260, y0=340, y1=530, verbose=False):
    im = Image.open(path).convert("RGB")
    px = im.load()

    def dark(x, y):
        r, g, b = px[x, y]
        return r < 130 and g < 140 and b < 150

    # find text bands
    rows = []
    for y in range(y0, y1):
        n = sum(1 for x in range(x0, x1) if dark(x, y))
        if n >= 12:
            if rows and y == rows[-1][1] + 1:
                rows[-1][1] = y
            else:
                rows.append([y, y])

    out = []
    for (a, b) in rows:
        runs = []
        for x in range(x0, x1):
            hit = any(dark(x, y) for y in range(a, b + 1))
            if hit:
                if runs and x == runs[-1][1] + 1:
                    runs[-1][1] = x
                else:
                    runs.append([x, x])
        # merge runs separated by <=3 px (glyph internals)
        merged = []
        for r in runs:
            if merged and r[0] - merged[-1][1] <= 4:
                merged[-1][1] = r[1]
            else:
                merged.append(list(r))
        wide = [r for r in merged if r[1] - r[0] >= 4]
        out.append((a, b, merged, wide))

    for (a, b, merged, wide) in out:
        text_right = max((r[1] for r in wide), default=None)
        text_left = min((r[0] for r in wide), default=None)
        print("band y=%d..%d left=%s right=%s runs=%s" % (a, b, text_left, text_right,
                                                          merged if verbose else len(merged)))


if __name__ == "__main__":
    analyze(sys.argv[1], verbose=len(sys.argv) > 2)
