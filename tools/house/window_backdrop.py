"""Window winter backdrops (overnight5, Oct 18): the textures SpecGreybox.Backdrop.cs puts outside the windows.

  dome_day.jpg    Poly Haven "Snowy Park 01" (CC0, Oleksiy Yakovlyev), tonemapped 8K equirect: overcast midday, bare trees, snow.
                  Its blue cast pulled toward neutral (film 12512, the view out the front window on Christmas morning, reads grey).
  dome_night.jpg  the same panorama as a winter night: sky a dark blue gradient with a faint horizon glow, snow dim blue-grey,
                  trees as silhouettes.
  card_night.png  film 5546: the McCallister front at night with its Christmas lights (the film's own street), mirrored so it reads
                  as the house across Lincoln Avenue; the black sky above the roofline is cut out (alpha).
  No day card: no clean daylight frame of the street exists in the film (1564/1650: vans, the cherry picker), and a day version
  made from 5546 (lit windows darkened, lifted 3.5x) read as a posterised mess. By day the park panorama shows instead.

Run: uv run --with numpy --with pillow --with scipy python -I tools/house/window_backdrop.py
"""
import pathlib, urllib.request, sys
import numpy as np
from PIL import Image
from scipy import ndimage

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / "unity/HomeAlone/Assets/Textures/Backdrop"
FILM = REPO / "0-homealone/full/homealone-movie-screencaps.com-%d.jpg"
CACHE = pathlib.Path.home() / ".cache/home-alone-backdrop"
PH = "https://dl.polyhaven.org/file/ph-assets/HDRIs/extra/Tonemapped%20JPG/snowy_park_01.jpg"


def park():
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "snowy_park_01.jpg"
    if not p.exists():   # no login, no personal data in the request
        req = urllib.request.Request(PH, headers={"User-Agent": "home-alone-build"})
        p.write_bytes(urllib.request.urlopen(req).read())
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255.0


def dome(a):
    h, w, _ = a.shape
    # white balance: the photo's snow (0.77, 0.86, 0.99) -> slightly cool neutral (0.88, 0.90, 0.94)
    day = np.clip(a * (np.array([0.88, 0.90, 0.94]) / np.array([0.77, 0.86, 0.99])), 0, 1)
    lum = day.mean(-1)
    row = np.arange(h)[:, None] / h                      # 0 top .. 1 bottom; horizon at 0.5
    sky = (row < 0.52) & (lum > 0.62)                    # bright and above the horizon: overcast sky (trees are darker)
    sky = ndimage.binary_opening(sky, iterations=2)
    soft = ndimage.gaussian_filter(sky.astype(np.float32), 2.0)[..., None]
    # night: a dark blue sky with a faint warm-grey town glow at the horizon; the land at ~10% in blue (moon/streetlight on snow)
    t = np.clip((0.52 - row) / 0.52, 0, 1)[..., None]   # 0 at the horizon .. 1 at the zenith
    sky_col = (1 - t) ** 3 * np.array([0.10, 0.10, 0.14]) + (1 - (1 - t) ** 3) * np.array([0.012, 0.020, 0.055])
    land = lum[..., None] ** 1.3 * np.array([0.10, 0.12, 0.17])
    night = np.broadcast_to(sky_col, day.shape) * soft + land * (1 - soft)
    return day, night


def card():
    a = np.asarray(Image.open(str(FILM) % 5546).convert("RGB")).astype(np.float32) / 255.0
    a = a[:, ::-1]                                       # mirrored: across the street, not a copy of our own front
    mx = a.max(-1)
    # sky: the near-black ABOVE the roofline (traced by hand on the mirrored frame, 960-px scale: eaves, the two dormers, the
    # chimney); dark branch masses there go too (the dome's trees show through), trunks and lit bulbs stay. Below it all is kept
    # (the dark brick and shutters are as dark as the sky)
    roof = np.array([(0, 235), (30, 235), (31, 140), (195, 140), (230, 100), (299, 95), (300, 45), (333, 20), (367, 45), (368, 95),
                     (544, 95), (545, 45), (575, 25), (609, 45), (610, 95), (700, 95), (715, 65), (760, 70), (870, 150), (889, 150),
                     (890, 290), (960, 290)], np.float32) * 2
    h, w = mx.shape
    ry = np.interp(np.arange(w), roof[:, 0], roof[:, 1])
    above = np.arange(h)[:, None] < ry[None, :] - 2
    sky = ndimage.binary_opening(mx < 0.045, iterations=1) & above
    alpha = 1 - ndimage.gaussian_filter(sky.astype(np.float32), 1.0)
    return a, alpha


def save(arr, name, alpha=None, size=None):
    im = Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8))
    if alpha is not None:
        im.putalpha(Image.fromarray((np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint8)))
    if size:
        im = im.resize(size, Image.LANCZOS)
    p = OUT / name
    im.save(p, quality=90) if name.endswith(".jpg") else im.save(p)
    print("wrote", p.relative_to(REPO), im.size)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    day, night = dome(park())
    save(day, "dome_day.jpg")
    save(night, "dome_night.jpg", size=(4096, 2048))
    n, al = card()
    save(n, "card_night.png", al)
    # self-check: the card's sky is cut out above the roof and the facade is kept
    assert al[5].mean() < 0.5 and al[int(al.shape[0] * 0.6)].mean() > 0.9, "card alpha: sky/facade split failed"


if __name__ == "__main__":
    sys.exit(main())
