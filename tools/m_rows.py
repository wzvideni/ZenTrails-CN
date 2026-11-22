import sys
from PIL import Image

# measure label glyph extents and value-box left edge for the 3 aesthetic rows
path = sys.argv[1]
x0, x1 = int(sys.argv[2]), int(sys.argv[3])
y0, y1 = int(sys.argv[4]), int(sys.argv[5])
im = Image.open(path).convert("RGB")
px = im.load()


def dark(x, y):
    r, g, b = px[x, y]
    return r < 120 and g < 130 and b < 140


rows = []
for y in range(y0, y1):
    n = sum(1 for x in range(x0, x1) if dark(x, y))
    if n >= 6:
        if rows and y == rows[-1][1] + 1:
            rows[-1][1] = y
        else:
            rows.append([y, y])

for (a, b) in rows:
    runs = []
    for x in range(x0, x1):
        if any(dark(x, y) for y in range(a, b + 1)):
            if runs and x == runs[-1][1] + 1:
                runs[-1][1] = x
            else:
                runs.append([x, x])
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] <= 4:
            merged[-1][1] = r[1]
        else:
            merged.append(list(r))
    print("band y=%d..%d runs=%s" % (a, b, merged))
