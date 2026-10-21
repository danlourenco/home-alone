"""nb_life: the neighbourhood's street life and Tier 4 horizon (Oct 20 2026; RESUME section 2, step 3). Layout in pure Python, models in
headless Blender (nb_house's Geo + to_blender). Every position names its evidence: F = film frame, C/O/L as in nb_kits, G = guess.

Street life (StreetLife.glb: one prototype mesh per kind, instanced by SpecGreybox.Neighborhood from life_layout.json "items"):
  cars        1980s full-size proxies built to period dimensions (no store model yet: decisions list, purchases): the box Chevrolet Caprice
              (5.4 x 1.95 x 1.42 m) as the film's two police cruisers at the Murphys (11576-11636, navy, red beacon bar; back-projected
              through the film 11581 camera, night scene only) and a parked blue sedan (1888, our side, day); the bandits' Dodge Ram van
              (B-series, 1979-93 body, light blue: 3297, 9540 "RAM" badge) parked by our lamp post (3297)
  poles       wooden utility poles + three wires along OUR side behind the sidewalk (F: 1564 cherry-picker on the line, 1888 wires over
              Lincoln at our frontage, 11581 a wire across the top left); pole spacing G (~44 m), none in the film frontals of our lot
  hydrant     red, on our side (F 3295: a red hydrant by the parkway on the van's approach); position G
  mailbox     the Murphys' white post mailbox (F 11576/11581, back-projected x 57.5 z 7.5 at the lot grade, +-1 m)
  stakes      three white yard stakes with red bows along the Murphys' porch front (F 11581), back-projected
Tier 4 (TreeLine.glb): two rings of bare-tree silhouette cards (nb_textures.tree_cards) at r 165-215 m around the house, heights from
  the lidar canopy statistics (13-24 m, hashed), facing the house; a snow ground annulus r 25-260 m 0.4 m under the lawns (shows only where
  no lawn, lot or street is) so the treeline stands on something; the sky is the HDRP sky / the R 320 dome beyond.
  python3 tools/house/nb_life.py                                    # life_layout.json (+ manifest "street_life", "tier4")
  Blender -b --factory-startup -P tools/house/nb_life.py -- --glb    # + StreetLife.glb, TreeLine.glb
"""
import json
import math
import os
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from nb_house import Geo, UP, add, mul, sub, norm, to_blender  # noqa: E402

MAN_P = ROOT / "spec/neighborhood.json"
OUT = Path(os.environ["NB_OUT"]) if os.environ.get("NB_OUT") else ROOT / "unity/HomeAlone/Assets/Models/Neighborhood"
CENTRE = (3.0, 8.0)          # spec x, z: the house's middle (SpecGreybox.Backdrop DomeCentreXZ)
WALK_Y, LAWN_A, LAWN_B, ROAD_Y = -1.184, -1.334, -1.20, -1.304


def layout():
    cars = [
        {"kind": "Car_CapricePolice", "x": 39.9, "z": 12.2, "heading": [0.5, 0.866], "scene": "night", "src": "F 11581: the near cruiser, wheel contacts back-projected (41.4, 11.8)-(43.1, 13.1) at the road; nose toward +z and the kerb"},
        {"kind": "Car_CapricePolice", "x": 60.3, "z": 18.4, "heading": [0.96, -0.28], "scene": "night", "src": "F 11581: the far cruiser on the Murphys' lawn at the porch's right end, rear to the camera (contacts (57.8, 16.6) (59.3, 19.4) (63.0, 17.3))"},
        {"kind": "Car_RamVan", "x": 31.75, "z": 28.4, "heading": [0.0, -1.0], "scene": "always", "src": "F 3297/3299: the bandits' van stops at our lamp post (z 24.2); parked just past our U-drive's left mouth (z 21.4 +-1.8) so it blocks no drive"},
        {"kind": "Car_Caprice", "x": 31.65, "z": 46.5, "heading": [0.0, 1.0], "scene": "always", "src": "F 1884/1888: a blue full-size sedan parked at our kerb to the left of our house; z G"},
    ]
    props = [{"kind": "Mailbox", "x": 57.5, "z": 7.5, "y": "lot_B0", "src": "F 11576/11581 back-projected"},
             {"kind": "Hydrant", "x": 28.45, "z": -13.5, "y": "walk", "src": "F 3295 (a red hydrant on our side); position G"}]
    for z in (6.3, 9.9, 16.1): props.append({"kind": "YardStake", "x": 59.45, "z": z, "y": "lot_B0", "src": "F 11581 back-projected (frame 845/1030/1412)"})
    poles = [{"x": 28.2, "z": z} for z in (-100.0, -56.0, -12.0, 37.5, 80.0, 122.0)]
    # Tier 4: two rings of cards
    cards = []
    for ring, r0 in enumerate((168.0, 200.0)):
        n = int(2 * math.pi * r0 / (6.5 + ring * 1.5))
        for i in range(n):
            h_ = zlib.crc32(f"{ring}:{i}".encode()); a = 2 * math.pi * (i + (h_ % 100) / 200.0) / n
            r = r0 + (h_ >> 8) % 160 / 10.0 - 8.0
            cards.append({"x": round(CENTRE[0] + r * math.cos(a), 2), "z": round(CENTRE[1] + r * math.sin(a), 2), "h": round(13 + (h_ >> 16) % 110 / 10.0, 1), "v": (h_ >> 4) % 4})
    # the walk boundary (user, Oct 20 via the coordinator): our lot, the stretch of Lincoln (both sidewalks, the road) in front of Marley's,
    # ours and the Murphys', and Marley's and the Murphys' front yards and porches; everything else is backdrop. Our sides sit 2.4 m past
    # the parcel line on the -z side (the MARV route and the side steps run at z -4.3 .. -4.95) and 0.5 m past it on +z.
    boundary = [(-34.16, -6.5), (28.87, -6.5), (46.15, -6.5), (46.15, -2.49), (64.4, -2.49), (64.4, 27.9), (46.15, 27.9), (46.15, 49.55),
                (9.0, 49.55), (9.0, 31.2), (-30.16, 31.1)]
    hedges = [(47.0, -2.25, 64.2, -2.25, "lot_B0"), (47.0, 27.65, 64.2, 27.65, "lot_B0"), (9.6, 49.3, 28.3, 49.3, "lot_A+1")]   # inside the line by 0.25 m
    piles = [(29.6, -6.2, 1.6), (43.4, -6.2, 5.4), (29.6, 49.25, 1.6), (43.4, 49.25, 5.4)]   # x centre, z, length across (x): sidewalks + B parkway
    return {"items": cars + props, "poles": poles, "wire_heights": [8.55, 8.85, 9.15], "cards": cards,
            "boundary": boundary, "hedges": hedges, "piles": piles,
            "boundary_src": "user Oct 20: heroes = our lot, Marley's (lot_A+1), the Murphys' (lot_B0); soft blockers (hedges on the neighbours' side lines, plowed snow piles across the sidewalks at the stretch's ends), invisible walls as the backstop"}


# ---------------------------------------------------------------- prototypes (origin at the ground contact, heading +z)
def car(kind):
    g, glow = Geo(), Geo()
    van = kind == "Car_RamVan"; pol = kind == "Car_CapricePolice"
    body = "NB_car_vanblue" if van else "NB_car_policenavy" if pol else "NB_car_carblue"
    L, W = (5.0, 2.0) if van else (5.4, 1.95)
    ch, gl, ty, tl = "NB_car_chrome", "NB_Glass", "NB_car_tyre", "NB_car_taillight"
    z0 = -L / 2
    if van:
        g.box(body, -W / 2, W / 2, 0.38, 1.15, z0 + 0.15, L / 2, 0.04)                 # lower body
        g.box(body, -W / 2 + 0.03, W / 2 - 0.03, 1.15, 2.02, z0 + 0.95, L / 2 - 0.05, 0.06)   # box
        g.face(body, [(-W / 2 + 0.03, 1.15, z0 + 0.15), (W / 2 - 0.03, 1.15, z0 + 0.15), (W / 2 - 0.03, 1.15, z0 + 0.95), (-W / 2 + 0.03, 1.15, z0 + 0.95)], UP)   # hood
        g.face(gl, [(-W / 2 + 0.08, 1.2, z0 + 0.96), (W / 2 - 0.08, 1.2, z0 + 0.96), (W / 2 - 0.08, 1.85, z0 + 0.94), (-W / 2 + 0.08, 1.85, z0 + 0.94)], (0, 0, -1))
        for sx in (-1, 1): g.face(gl, [(sx * (W / 2 - 0.02), 1.3, z0 + 1.0), (sx * (W / 2 - 0.02), 1.3, z0 + 1.75), (sx * (W / 2 - 0.02), 1.85, z0 + 1.75), (sx * (W / 2 - 0.02), 1.85, z0 + 1.0)], (sx, 0, 0))
        g.box("NB_paint_white", -W / 2 - 0.005, W / 2 + 0.005, 1.25, 1.55, z0 + 2.2, L / 2 - 0.4)   # the plumbing-company side panel (no lettering)
    else:
        g.box(body, -W / 2, W / 2, 0.36, 0.98, z0, L / 2, 0.05)                       # lower body
        a, b = z0 + 1.55, z0 + 3.85
        cab = [(-W / 2 + 0.12, 0.98, a), (W / 2 - 0.12, 0.98, a), (W / 2 - 0.16, 1.42, a + 0.5), (-W / 2 + 0.16, 1.42, a + 0.5)]
        g.face(gl, cab, (0, 0.5, -1))
        g.face(gl, [(-W / 2 + 0.12, 0.98, b), (W / 2 - 0.12, 0.98, b), (W / 2 - 0.16, 1.42, b - 0.35), (-W / 2 + 0.16, 1.42, b - 0.35)], (0, 0.5, 1))
        g.face(body, [(-W / 2 + 0.16, 1.42, a + 0.5), (W / 2 - 0.16, 1.42, a + 0.5), (W / 2 - 0.16, 1.42, b - 0.35), (-W / 2 + 0.16, 1.42, b - 0.35)], UP)
        for sx in (-1, 1):
            g.face(gl, [(sx * (W / 2 - 0.12), 0.98, a), (sx * (W / 2 - 0.12), 0.98, b), (sx * (W / 2 - 0.16), 1.42, b - 0.35), (sx * (W / 2 - 0.16), 1.42, a + 0.5)], (sx, 0.3, 0))
        if pol:
            g.box("NB_paint_white", -W / 2 - 0.004, W / 2 + 0.004, 0.62, 0.74, z0 + 0.6, L / 2 - 0.6)          # the door stripe (11581)
            g.box(ch, -0.65, 0.65, 1.42, 1.50, -0.25, 0.05)                                                    # light bar
            for x in (-0.5, -0.17, 0.17, 0.5):
                glow.box("NB_Beacon", x - 0.09, x + 0.09, 1.50, 1.66, -0.19, -0.01)
            g.box(ch, -0.08, 0.08, 1.50, 1.62, -0.16, -0.04)                                                   # siren
    for sz in (-1, 1):
        g.box(ch, -W / 2 - 0.02, W / 2 + 0.02, 0.36, 0.52, sz * (L / 2 + 0.03) - 0.05, sz * (L / 2 + 0.03) + 0.05, 0.02)   # bumpers
    g.box(tl, -W / 2 + 0.08, -W / 2 + 0.55, 0.62, 0.8, L / 2 - 0.01, L / 2 + 0.01); g.box(tl, W / 2 - 0.55, W / 2 - 0.08, 0.62, 0.8, L / 2 - 0.01, L / 2 + 0.01)
    g.box("NB_car_headlamp", -W / 2 + 0.1, -W / 2 + 0.5, 0.66, 0.8, -L / 2 - 0.01, -L / 2 + 0.01); g.box("NB_car_headlamp", W / 2 - 0.5, W / 2 - 0.1, 0.66, 0.8, -L / 2 - 0.01, -L / 2 + 0.01)
    wb = 1.45 if van else 1.48
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (W / 2 - 0.13), sz * wb; n = 10; r = 0.34
            ring = lambda dx: [(cx + dx, 0.34 + r * math.sin(2 * math.pi * k / n), cz + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
            A, B = ring(-0.11), ring(0.11)
            for k in range(n): g.quad(ty, A[k], A[(k + 1) % n], B[(k + 1) % n], B[k], (0, A[k][1] - 0.34, A[k][2] - cz))
            g.face(ty, B, (1, 0, 0)); g.face(ty, A, (-1, 0, 0))
    return g, glow


def pole():
    g = Geo(); n = 8; M = "NB_paint_brown"
    rings = [[(r * math.cos(2 * math.pi * k / n), y, r * math.sin(2 * math.pi * k / n)) for k in range(n)] for y, r in ((0, 0.15), (10.5, 0.11))]
    for k in range(n): g.quad(M, rings[0][k], rings[0][(k + 1) % n], rings[1][(k + 1) % n], rings[1][k], (rings[0][k][0], 0, rings[0][k][2]))
    g.face(M, rings[1], UP)
    g.box(M, -1.25, 1.25, 9.75, 9.87, -0.06, 0.06, 0.01)              # crossarm across the street (x)
    for x in (-1.0, 0.0, 1.0): g.box("NB_paint_ivory", x - 0.04, x + 0.04, 9.87, 10.02, -0.04, 0.04, 0.005)
    g.box("NB_paint_charcoal", -0.28, 0.0, 7.6, 8.4, 0.12, 0.42, 0.02)   # a pole transformer can (1564)
    return g


def hydrant():
    g = Geo(); n = 12; M = "NB_paint_hydrantred"
    prof = [(0, 0.16), (0.08, 0.16), (0.1, 0.12), (0.62, 0.115), (0.66, 0.14), (0.72, 0.12), (0.82, 0.06), (0.86, 0.02)]
    rings = [[(r * math.cos(2 * math.pi * k / n), y, r * math.sin(2 * math.pi * k / n)) for k in range(n)] for y, r in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(n): g.quad(M, a[k], a[(k + 1) % n], b[(k + 1) % n], b[k], (a[k][0], 0, a[k][2]))
    g.face(M, rings[-1], UP)
    for ax in ((1, 0), (-1, 0), (0, 1)): g.bar(M, (0, 0.48, 0), (ax[0] * 0.22, 0.48, ax[1] * 0.22), 0.09, 0.09, 0.01)
    return g


def mailbox():
    g = Geo(); g.box("NB_paint_white", -0.05, 0.05, 0, 1.05, -0.05, 0.05, 0.005); g.box("NB_paint_white", -0.11, 0.11, 1.05, 1.27, -0.25, 0.25, 0.02)
    g.box("NB_paint_hydrantred", 0.11, 0.13, 1.12, 1.30, 0.05, 0.09)
    return g


def stake():
    g = Geo(); g.box("NB_paint_white", -0.03, 0.03, 0, 0.62, -0.03, 0.03, 0.004); g.box("NB_paint_hydrantred", -0.1, 0.1, 0.48, 0.62, -0.035, 0.035, 0.01)
    return g


def wires(L):
    """Three catenaries per span between consecutive poles (heights wire_heights at the crossarm's -1/0/+1 m), sag 0.45 m."""
    g = Geo(); P = sorted(L["poles"], key=lambda p: p["z"])
    for a, b in zip(P, P[1:]):
        for dx, h in zip((-1.0, 0.0, 1.0), L["wire_heights"]):
            pts = [(a["x"] + dx, WALK_Y + 10.0, a["z"] + (b["z"] - a["z"]) * t / 12) for t in range(13)]
            pts = [(x, y - 0.45 * 4 * (t / 12) * (1 - t / 12), z) for t, (x, y, z) in enumerate(pts)]
            for p0, p1 in zip(pts, pts[1:]): g.bar("NB_paint_black", p0, p1, 0.02, 0.02, 0)
    return g


def treeline(L):
    g = Geo(); cx, cz = CENTRE
    for c in L["cards"]:
        to = norm((cx - c["x"], 0, cz - c["z"])); t = norm((-to[2], 0, to[0])); w = c["h"] * 0.5; y0 = LAWN_A - 0.3
        u0 = c["v"] * 0.25
        p = (c["x"], y0, c["z"]); A, B = add(p, mul(t, -w / 2)), add(p, mul(t, w / 2))
        g.face("NB_TreeCard", [A, B, add(B, (0, c["h"], 0)), add(A, (0, c["h"], 0))], to, [(u0, 0), (u0 + 0.25, 0), (u0 + 0.25, 1), (u0, 1)])
    gr = Geo(); n = 96; y = LAWN_A - 0.4
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        P = lambda r, a: (cx + r * math.cos(a), y, cz + r * math.sin(a))
        for r0, r1 in ((25.0, 90.0), (90.0, 260.0)):
            gr.quad("NB_snow_patchy", P(r0, a0), P(r1, a0), P(r1, a1), P(r0, a1), UP)
    return g, gr


def boundary_dressing(L):
    """Snowy privet hedges on the heroes' side lot lines and plowed snow piles across the sidewalks at the walkable stretch's ends."""
    g = Geo(); rng = __import__("random").Random(5)
    lv = {"lot_B0": LAWN_B + 0.02, "lot_A+1": LAWN_A}
    for x0, z0, x1, z1, lot in L["hedges"]:
        y0 = lv[lot]; L_ = math.hypot(x1 - x0, z1 - z0); n = max(1, int(L_ / 1.2)); ax = norm((x1 - x0, 0, z1 - z0)); side = (-ax[2], 0, ax[0])
        for i in range(n):
            c = add((x0, 0, z0), mul(ax, (i + 0.5) * L_ / n)); h = 1.25 + 0.2 * rng.random(); w = 0.85 + 0.1 * rng.random()
            g.obox("NB_paint_darkgreen", add(c, (0, y0 + h / 2, 0)), ax, UP, side, L_ / n / 2 + 0.05, h / 2, w / 2, 0.12)
            g.obox("NB_snow_ground", add(c, (0, y0 + h + 0.04, 0)), ax, UP, side, L_ / n / 2, 0.06, w / 2 - 0.05, 0.05)
    for x, z, ln in L["piles"]:
        y0 = WALK_Y - 0.02; nu, nv = 12, 4; rx, rz, h = ln / 2 + 0.3, 0.9, 1.1
        rs = [[(x + rx * math.sin(math.pi / 2 * j / nv) * math.cos(2 * math.pi * i / nu) * (0.9 + 0.15 * rng.random()), y0 + h * math.cos(math.pi / 2 * j / nv) * (0.85 + 0.15 * rng.random()) if j < nv else y0,
                z + rz * math.sin(math.pi / 2 * j / nv) * math.sin(2 * math.pi * i / nu)) for i in range(nu)] for j in range(nv + 1)]
        for j in range(nv):
            for i in range(nu):
                a, b, c, d = rs[j][i], rs[j][(i + 1) % nu], rs[j + 1][(i + 1) % nu], rs[j + 1][i]
                g.face("NB_snow_ground", [a, c, d] if j == 0 else [a, b, c, d], (a[0] - x, 1.0, a[2] - z))
    return g


def build_glb(L):
    import bpy
    def export(objs, name):
        root = bpy.data.objects.new(name + "_Root", None); bpy.context.scene.collection.objects.link(root)
        for o in objs: o.parent = root
        bpy.context.view_layer.update()
        for o in bpy.context.scene.collection.objects: o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), export_format="GLB", export_yup=True, use_selection=True, export_materials="EXPORT")
    stats = {}
    bpy.ops.wm.read_factory_settings(use_empty=True); coll = bpy.context.scene.collection; objs = []
    for k in ("Car_Caprice", "Car_CapricePolice", "Car_RamVan"):
        g, gl = car(k); objs.append(to_blender(g, k, coll)); stats[k] = g.tris()
        if gl.m: objs.append(to_blender(gl, k + "_Beacons", coll, smooth=False))
    for k, fn in (("Pole", pole), ("Hydrant", hydrant), ("Mailbox", mailbox), ("YardStake", stake)):
        g = fn(); objs.append(to_blender(g, k, coll)); stats[k] = g.tris()
    w = wires(L); objs.append(to_blender(w, "Wires", coll, smooth=False)); stats["Wires"] = w.tris()
    bd = boundary_dressing(L); objs.append(to_blender(bd, "BoundaryDressing", coll)); stats["BoundaryDressing"] = bd.tris()
    export(objs, "StreetLife")
    bpy.ops.wm.read_factory_settings(use_empty=True); coll = bpy.context.scene.collection
    g, gr = treeline(L); stats["TreeLine_Cards"] = g.tris(); stats["Horizon_Ground"] = gr.tris()
    export([to_blender(g, "TreeLine_Cards", coll, smooth=False), to_blender(gr, "Horizon_Ground", coll, smooth=False)], "TreeLine")
    return stats


def main():
    L = layout()
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "life_layout.json").write_text(json.dumps(L, indent=1))
    if "--glb" in sys.argv:
        st = build_glb(L); print("street life + tier 4 tris", st)
        sp = ROOT / "art/home_alone/references/neighborhood/build_stats.json"; s = json.loads(sp.read_text()) if sp.exists() else {}
        s["life"] = st; sp.write_text(json.dumps(s, indent=1))
    print("life:", len(L["items"]), "items,", len(L["poles"]), "poles,", len(L["cards"]), "tree cards")


if __name__ == "__main__":
    main()
