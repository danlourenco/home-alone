"""Reference boards (film frames + footprint outline) for each Tier 1-2 lot: boards/<id>.jpg.  uv run --with numpy --with pillow --with matplotlib python -I tools/house/nb_boards.py"""
import json, io
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]; N = ROOT/"art/home_alone/references/neighborhood"
man = json.load(open(ROOT/"spec/neighborhood.json"))["parcels"]; film = json.load(open(N/"film_index.json"))["parcels"]
FR = ROOT/"0-homealone/full/homealone-movie-screencaps.com-{}.jpg"
(N/"boards").mkdir(exist_ok=True)
for e in man:
    if e["tier"] > 2: continue
    fig, ax = plt.subplots(figsize=(4.2, 4.2), dpi=100)
    ax.add_patch(Polygon([(q[1], q[0]) for q in e["parcel_poly_spec"]], fc="#f4f0e0", ec="#888"))
    for b in e["buildings"]: ax.add_patch(Polygon([(q[1], q[0]) for q in b["footprint_spec"]], fc="#7a5a48" if b["main"] else "#b09a88", ec="k", lw=.6))
    zs = [q[1] for q in e["parcel_poly_spec"]]; xs = [q[0] for q in e["parcel_poly_spec"]]
    ax.set_xlim(max(zs)+2, min(zs)-2); ax.set_ylim(min(xs)-2, max(xs)+2); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(e["id"] + "  (spec +x up; Lincoln is at the top for A, the bottom for B)", fontsize=8)
    for b in e["buildings"][:1]: ax.text(0.02, 0.02, f"{b['area_m2']:.0f} m2  ridge {b['ridge_m']} m (2022 lidar)", transform=ax.transAxes, fontsize=7)
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig); plan = Image.open(buf).convert("RGB")
    fr = e["evidence_frames"][:6]; tw = 400; th = 225
    cols = 3; rows = max(1, (len(fr)+cols-1)//cols)
    W = cols*tw + plan.width; Hh = max(rows*th, plan.height)
    im = Image.new("RGB", (W, Hh), "white"); d = ImageDraw.Draw(im)
    for k, n in enumerate(fr):
        try: t = Image.open(str(FR).format(n)).convert("RGB").resize((tw, th))
        except Exception: continue
        x, y = (k % cols)*tw, (k//cols)*th; im.paste(t, (x, y)); d.rectangle([x, y, x+40, y+11], fill="black"); d.text((x+2, y), str(n), fill="yellow")
    if not fr: d.text((10, 10), "no film frame found", fill="black")
    im.paste(plan, (cols*tw, 0)); im.save(N/"boards"/f"{e['id']}.jpg", quality=82)
    print(e["id"], im.size)
