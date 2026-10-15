# usage: crop.py img out x0 y0 x1 y1 [scale]   -- gridded zoom crop (grid every 10 px, labels every 50)
import sys
from PIL import Image, ImageDraw
img, out, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
s = int(sys.argv[7]) if len(sys.argv) > 7 else 3
im = Image.open(img).convert("RGB").crop((x0, y0, x1, y1)).resize(((x1-x0)*s, (y1-y0)*s), Image.LANCZOS)
d = ImageDraw.Draw(im)
for x in range((x0//10+1)*10, x1, 10):
    c = (0,255,255) if x % 50 == 0 else (90,90,90)
    if x % 50 == 0 or s >= 4: d.line([((x-x0)*s,0),((x-x0)*s,im.height)], fill=c, width=1)
    if x % 50 == 0: d.text(((x-x0)*s+2, 2), str(x), fill=(255,255,0))
for y in range((y0//10+1)*10, y1, 10):
    c = (0,255,255) if y % 50 == 0 else (90,90,90)
    if y % 50 == 0 or s >= 4: d.line([(0,(y-y0)*s),(im.width,(y-y0)*s)], fill=c, width=1)
    if y % 50 == 0: d.text((2,(y-y0)*s+2), str(y), fill=(255,255,0))
im.save(out)
