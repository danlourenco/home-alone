"""exterior_textures: Poly Haven (CC0) PBR sets for the exterior realism pass (Oct 18 2026; changes/2026-10-18-exterior-realism.json).

Downloads each set (plain User-Agent, no personal data) into sfm-work/polyhaven/<id>/ and writes the Unity maps to
unity/HomeAlone/Assets/Textures/PolyHaven/<id>_x/: albedo.jpg, normal.jpg (OpenGL), height.png (16-bit grey, POM) and mask.png
(HDRP mask map: R metallic 0, G ambient occlusion, B detail mask 1, A smoothness = 1 - roughness).

  uv run --with pillow --with numpy python -I tools/house/exterior_textures.py
"""
import io
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "sfm-work/polyhaven"
OUT = ROOT / "unity/HomeAlone/Assets/Textures/PolyHaven"
UA = {"User-Agent": "home-alone-house/1.0"}
SETS = {   # id: (resolution, neutral albedo mean or None). A neutral set is rescaled to that linear mean per channel (grey, variation
    # kept) so SpecGreybox tints it to a measured colour without a tint over 1
    "red_brick_03": ("2k", None),      # facade brick (68 mm courses: tiled per metre in SpecGreybox.Shell)
    "roof_slates_02": ("2k", None),    # roof shingles (tinted to film 4382's dark brown-grey)
    "white_plaster_02": ("1k", 0.80),  # painted trim: subtle roughness variation
    "concrete_floor_01": ("1k", 0.60), # stone sills, caps, step treads (speckled)
    "snow_02": ("2k", 0.85),           # ground snow, drifts, roof snow
    "asphalt_02": ("2k", None),        # the street (wet)
    "brushed_concrete": ("2k", 0.30),  # the front walk, sidewalks, porch slab, step treads: smooth poured slabs (film 4382/10177)
}
# Wet ground by weather (walk notes Oct 19 08:48, 09:50, 12:11; user Oct 20 "let's do it"): the street, drives and front walk (asphalt),
# the sidewalks and kerbs (concrete, jointed across z), the apron at the foot of the steps (concrete) in three states, swapped at run
# time by WetGround (HouseWeather / HouseNightMode): sunny = film 1640 (pale weathered, mostly dry, damp patches), overcast = damper,
# night = film 10162/10170 (dark, wet, glinting, puddles). Per surface one normal (the night's: puddles flat) and per state an albedo
# + mask (AO, smoothness). The steps are one set, always wet (step_wet: concrete_floor_01, the red exposed aggregate).
# Concrete: brushed_concrete (2.5 m scan) at WET_TILE 3.0 m holding two 1.5 m slabs (5 ft US standard: ASSUMED, joints unmeasured).
WET_TILE, SLAB, JOINT = 3.0, 1.5, 0.010   # m
STATES = {   # base wetness, damp-patch area fraction, puddle strength
    "sunny": (0.00, 0.25, 0.0), "overcast": (0.42, 0.55, 0.6), "night": (0.82, 0.0, 1.0)}
ASPHALT_DRY = 0.22   # weathered asphalt's dry linear albedo (film 1640: the drive reads pale grey-tan by day; new asphalt ~0.05)


def _periodic_noise(n, cells, seed):
    """Tileable smooth noise in 0..1 (band-limited white noise by FFT: wraps at the edges by construction)."""
    rng = np.random.default_rng(seed); f = np.fft.fftfreq(n) * n
    k = np.sqrt(f[:, None] ** 2 + f[None, :] ** 2)
    a = np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((n, n))) * np.exp(-(k / cells) ** 2)))
    return (a - a.min()) / (a.max() - a.min())


def wet_slabs():
    for name, srcid, axis, dry, dk in (("asphalt_wet", "asphalt_02_x", None, ASPHALT_DRY, 0.65),
                                       ("walk_wet_jz", "brushed_concrete_x", 0, None, 0.55), ("walk_wet", "brushed_concrete_x", None, None, 0.55)):
        for st in STATES:
            _wet(f"{name}_{st}", OUT / srcid, axis, st, dry, dk, normal=(st == "night"))
    _wet("step_wet", OUT / "concrete_floor_01_x", None, "night", None, 0.50, normal=True, puddles=False)


def _wet(name, src, axis, state, dry_mean, wet_dark, normal, puddles=True):
    """wet_dark: the albedo lost when soaked (porous concrete ~0.5; asphalt's water film reads darker, 0.65)."""
    base, frac, pstr = STATES[state]
    alb = (np.asarray(Image.open(src / "albedo.jpg").convert("RGB"), np.float32) / 255.0) ** 2.2; n = alb.shape[0]
    if dry_mean: alb = np.clip(alb / alb.reshape(-1, 3).mean(0) * dry_mean, 0, 1)    # weathered (oxidised, salt-dusted): paler, grey
    nrm = np.asarray(Image.open(src / "normal.jpg").convert("RGB"), np.float32) / 255.0
    msk = np.asarray(Image.open(src / "mask.png"), np.float32) / 255.0
    h = np.asarray(Image.open(src / "height.png").convert("L"), np.float32) / 255.0
    ao, s_dry = msk[..., 1], msk[..., 3]
    cav = np.clip((h.mean() - h) / max(1e-6, h.std() * 3) + 0.5, 0, 1)                 # low = wetter
    pud_shape = np.clip((_periodic_noise(n, 3.0, 11) - 0.70) / 0.08, 0, 1) * puddles   # ~10% of the area, soft edges
    pud = pud_shape * pstr
    pn = _periodic_noise(n, 5.0, 23); thr = np.quantile(pn, 1 - frac) if frac else 2.0
    patch = np.clip((pn - thr) / 0.04 + 0.5, 0, 1) * 0.9                                # damp patches, frac of the area (sunny/overcast)
    w = np.clip(base + 0.30 * (cav - 0.5) + 0.15 * (_periodic_noise(n, 6.0, 5) - 0.5), 0, 1)
    w = np.maximum(np.maximum(w, patch), pud); jd = np.zeros((n, n), np.float32)
    if axis is not None:
        t = np.arange(n) / n * WET_TILE; d = np.minimum(t % SLAB, SLAB - t % SLAB)       # m to the nearest joint
        g = np.clip(1 - d / (JOINT / 2), 0, 1) ** 0.5                                     # groove profile (1 in the joint)
        damp = np.clip(1 - d / 0.05, 0, 1)                                                # 5 cm damp margin along each joint
        g, damp = (g[::-1, None], damp[::-1, None]) if axis == 0 else (g[None, :], damp[None, :])
        jd = np.broadcast_to(g, (n, n)); w = np.maximum(w, np.maximum(jd, 0.7 * np.broadcast_to(damp, (n, n))))
    dark = 1 - wet_dark * w - 0.12 * pud - 0.25 * jd                                      # soaked: (1 - wet_dark) x dry, a puddle darker
    a = np.clip(alb * dark[..., None], 0, 1)
    s = np.clip(s_dry + (0.96 - s_dry) * w, 0, 1)                                         # wet: up to a water film's 0.96
    o = OUT / name; o.mkdir(parents=True, exist_ok=True)
    Image.fromarray((a ** (1 / 2.2) * 255).astype(np.uint8)).save(o / "albedo.jpg", quality=92)
    m = np.stack([np.zeros_like(s), ao * (1 - 0.5 * jd), np.ones_like(s), s], -1)
    Image.fromarray((m * 255).astype(np.uint8), "RGBA").save(o / "mask.png")
    if normal:   # one per surface, beside its night set; the other states' materials use it too
        nn = nrm + (np.array([0.5, 0.5, 1.0], np.float32) - nrm) * (0.85 * pud_shape)[..., None]   # water fills the puddle: flat
        if axis == 1:   # groove walls from the joint profile: n ~ (-dh/du, -dh/dv, 1), h = -jd; v runs up (row 0 = v 1)
            nn[..., 0] = np.clip(nn[..., 0] + np.gradient(np.asarray(jd, np.float32), axis=1), 0, 1)
        elif axis == 0:
            nn[..., 1] = np.clip(nn[..., 1] - np.gradient(np.asarray(jd, np.float32), axis=0), 0, 1)
        Image.fromarray((np.clip(nn, 0, 1) * 255).astype(np.uint8)).save(o / "normal.jpg", quality=92)
    L = lambda x: float((x.reshape(-1, 3).mean(0)) @ [0.2126, 0.7152, 0.0722])
    print(f"{name:22s} albedo {L(a):.3f} (dry {L(alb):.3f})  smoothness mean {s.mean():.2f} (5-95% {np.percentile(s, 5):.2f}-{np.percentile(s, 95):.2f})")


KEYS = (("Diffuse", "albedo"), ("nor_gl", "normal"), ("Rough", "rough"), ("Displacement", "height"), ("AO", "ao"))


def fetch(aid, res):
    d = RAW / aid; d.mkdir(parents=True, exist_ok=True)
    if all((d / f"{n}.jpg").exists() for _, n in KEYS):
        return d
    j = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{aid}", headers=UA)))
    for k, n in KEYS:
        url = j[k][res]["jpg"]["url"]
        (d / f"{n}.jpg").write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read())
    return d


def main():
    for aid, (res, neutral) in SETS.items():
        d = fetch(aid, res); o = OUT / f"{aid}_x"; o.mkdir(parents=True, exist_ok=True)
        px = {"1k": 1024, "2k": 2048}[res]
        I = lambda n: Image.open(d / f"{n}.jpg").resize((px, px), Image.LANCZOS)
        I("normal").convert("RGB").save(o / "normal.jpg", quality=92)
        alb = I("albedo").convert("RGB")
        if neutral:
            a = (np.asarray(alb, np.float32) / 255.0) ** 2.2; a = np.clip(a / a.reshape(-1, 3).mean(0) * neutral, 0, 1)
            alb = Image.fromarray((a ** (1 / 2.2) * 255).astype(np.uint8))
        alb.save(o / "albedo.jpg", quality=92)
        L = lambda n: np.asarray(I(n).convert("L"), np.float32) / 255.0
        h = L("height"); h = (h - h.min()) / max(1e-6, h.max() - h.min())
        Image.fromarray((h * 255).astype(np.uint8)).save(o / "height.png")
        r, ao = L("rough"), L("ao")
        m = np.stack([np.zeros_like(r), ao, np.ones_like(r), 1.0 - r], -1)
        Image.fromarray((m * 255).astype(np.uint8), "RGBA").save(o / "mask.png")
        print(aid, res, "->", o.relative_to(ROOT), "rough mean %.2f" % r.mean())


def generated():
    """Snowflake sprites and the weathering decals' masks (procedural, no download): Assets/Textures/Exterior/."""
    o = ROOT / "unity/HomeAlone/Assets/Textures/Exterior"; o.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    def disc(n, soft):
        y, x = np.mgrid[0:n, 0:n] / (n - 1) * 2 - 1; r = np.sqrt(x * x + y * y)
        a = np.clip((1 - r) / soft, 0, 1) ** 1.5
        return Image.fromarray(np.dstack([np.full((n, n), 255, np.uint8)] * 3 + [(a * 255).astype(np.uint8)]), "RGBA")
    disc(64, 0.6).save(o / "flake.png"); disc(128, 1.0).save(o / "bokeh.png")
    def noise(h, w, scales):
        acc = np.zeros((h, w))
        for sc, amp in scales:
            g = rng.random((h // sc + 2, w // sc + 2))
            acc += amp * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w + 2 * sc, h + 2 * sc), Image.BICUBIC), float)[sc:sc + h, sc:sc + w] / 255
        return acc / sum(a for _, a in scales)
    # base grime: dark brown, strongest at the bottom (splash-back off the snow/soil), ragged top edge, fading over the height
    h, w = 256, 1024; v = np.linspace(0, 1, h)[:, None]   # PNG row 0 is the top: dark at the bottom
    n = noise(h, w, [(64, 0.5), (16, 0.3), (4, 0.2)])
    a = np.clip((v ** 1.6) * 1.4 * (0.55 + 0.9 * n) - 0.15, 0, 1) * 0.75
    rgb = np.dstack([np.full((h, w), c, np.uint8) for c in (52, 40, 30)])
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), "RGBA").save(o / "grime_base.png")
    # streaks under a sill or gutter outlet: thin vertical runs from the top, fading down, a few stronger
    h, w = 512, 256; cols = noise(1, w, [(8, 0.6), (2, 0.4)])[0] ** 3
    v = np.linspace(1, 0, h)[:, None] ** 1.2; n = noise(h, w, [(32, 0.6), (8, 0.4)])
    a = np.clip(cols[None, :] * 2.2 * v * (0.6 + 0.8 * n), 0, 1) * 0.55
    a *= np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / 30, 0, 1)[None, :]
    rgb = np.dstack([np.full((h, w), c, np.uint8) for c in (45, 38, 32)])
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), "RGBA").save(o / "grime_streak.png")
    # snowmelt at a shovelled edge (SpecGreybox.FrontDrive's Decal_Melt): u across (1 = the snow bank's side), v along the edge;
    # a dark wet band 6-20 cm wide with a ragged inner edge, fading into the walk
    h, w = 1024, 256; u = np.linspace(0, 1, w)[None, :]
    reach = 0.45 + 0.35 * noise(h, 1, [(64, 0.6), (8, 0.4)])                   # (h, 1): how far in from the bank the melt runs
    n = noise(h, w, [(32, 0.5), (8, 0.3), (2, 0.2)])
    a = np.clip((u - (1 - reach)) / reach * 1.6 * (0.7 + 0.6 * n), 0, 1) ** 1.3 * 0.85
    rgb = np.dstack([np.full((h, w), c, np.uint8) for c in (38, 35, 32)])
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), "RGBA").save(o / "melt_edge.png")
    print("generated ->", o.relative_to(ROOT))


if __name__ == "__main__":
    main()
    generated()
    wet_slabs()
