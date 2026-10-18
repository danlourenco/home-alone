"""parents_layout: the parents' bedroom, TRIAL 1 (Oct 18, overnight8; changes/2026-10-18-parents-room.json).

Room size: no new solve. Two rulers of different kinds already on file (measurements/rig/rooms.json):
  * door-80in:parents  Marina's parents clip (VGGT, sfm-work/rooms/parents) at the 80 in hall door: 5.23 x 5.23 m
  * rig-height         Marina's camera height as a multiple of a door (tools/house/rig_check.py): 5.11 x 5.08 m
Built 5.281 x 5.324 (spec/geometry.json parents_bedroom bbox): printed below against both; < 5% = same room (no change).

Layout, the headboard wall (x = 3.21, the bath-door wall): Marina 250 s (board still, near frontal on that wall; picks on the
1920-wide grid, scratch b250g.png). The wall's metres along it come from ONE horizontal ruler in the same frame:
the right corner (z = 0, crown corner u 1703) to the bath casing's outer edge (u 189 after the blind pick check, built z 4.344 + 0.07 casing = 4.414);
check: the wall's height in the same frame (crown top v 110 to baseboard foot v 940 = 830 px) at the built 2.50 m ceiling
gives 336 px/m, at the rig's 2.43 m 346 px/m, vs 344.7 from the casing (-2.5% / +0.4%). Pieces in front of the wall are
projected with f = 1428 px (Marina's solved foyer cameras), so the camera stands D = f / k from the wall.
Film check (not a ruler): film 1610's head posts are 713 px apart = 3.56 wallpaper roll widths = 1.90 m at the 21 in roll.
Other walls: Marina 180/184/188/238/244 (window corner, armoire, demilune table) and film 2648 (etagere at the window
corner, the window's dressing), placed by eye against the built faces (props lane positions; logged).

  python3 tools/house/parents_layout.py            # print the checks and the piece table
  python3 tools/house/parents_layout.py --write    # -> spec/dressing/parents.json + parents_* entries of store_props.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEO = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
POLY = next(r for r in GEO["rooms"] if r["name"] == "parents_bedroom")["poly"]
X0, X1 = min(p[0] for p in POLY), max(p[0] for p in POLY)          # 3.21 headboard wall .. 8.491 front wall
Z0, Z1 = min(p[1] for p in POLY), max(p[1] for p in POLY)          # 0 window wall .. 5.324 hall wall
XN, ZN = 6.921, 3.721                                              # the notch (Kevin's room): walls x = 6.921 (z > 3.721), z = 3.721 (x > 6.921)

# ---- Marina 250 s picks (u on 1920 px)
U_CORNER, U_CASING, Z_CASING = 1703, 189, 4.344 + 0.07
V_CEIL, V_FLOOR = 110, 940
F = 1428.0
U_POST = (743, 1405)                     # head posts' centres (left = +z side)
U_NS_L, U_NS_R = (523, 718), (1420, 1645)
K = (U_CORNER - U_CASING) / Z_CASING     # px per metre on the wall plane
D = F / K
ZC = (U_CORNER - 960) / K                # the wall point straight ahead of the camera


def z_at(u, d):
    """u (px) of a point d metres in front of the headboard wall -> z (spec)"""
    return ZC - (u - 960) / (K * D / (D - d))


POSTS = [z_at(u, 0.07) for u in U_POST]
BED_C = sum(POSTS) / 2
SPACING = POSTS[0] - POSTS[1]
POST = 0.104                             # the pack bed's post (purchased_bed.py)
W_OUT = SPACING + POST
L_OUT = 2.20                             # ASSUMED: king length (80 in mattress + frame); Marina 254 s not solved
OFF = 0.015                              # head posts off the paper

# pieces: spec boxes (x, z), y above the upper floor; "store" models fit into them (store_props.json, floor upper)
WOOD, QUILT = "wood", "quilt"
P = []


def piece(name, x, z, h, store=None, yaw=None, back="", source="", collide=False, **kw):
    P.append(dict(name=name, x=[round(x[0], 4), round(x[1], 4)], z=[round(z[0], 4), round(z[1], 4)], h=[0.0, h], store=store,
                  yaw=yaw, back=back, source=source, collide=collide, **kw))


bx = (X0 + OFF, X0 + OFF + L_OUT); bz = (BED_C - W_OUT / 2, BED_C + W_OUT / 2)
piece("parents_bed", bx, bz, 2.15, "Assets/Purchased/ParentsBed/ParentsBed.glb", yaw=90, foot_h=2.15, mattress_top=0.72, post=POST,
      source=f"Marina 250 s head posts at z {POSTS[1]:.3f} / {POSTS[0]:.3f} (spacing {SPACING:.3f}; film 1610 at the 21 in paper roll: 1.90), "
             "headboard on the bath-door wall; length 2.20 ASSUMED (king); finial tops 2.15 on all four posts ASSUMED (film 1602/2648: tall "
             "rice-carved posts, ~0.35 m under the ceiling); mattress top 0.72 ASSUMED; rails' underside 0.48 (kid Kevin's crouch 0.45 + 0.02 fits under)")
ns_d = 0.40
nsR = (round(z_at(U_NS_R[1], 0.22), 3), bz[0] - 0.03)
nsL = (bz[1] + 0.03, round(z_at(U_NS_L[0], 0.22), 3))
for nm, zz in (("parents_nightstand_window", nsR), ("parents_nightstand_bath", nsL)):
    piece(nm, (X0 + 0.01, X0 + 0.01 + ns_d), zz, 0.66, "Assets/Classic Wooden Furniture Pack/Prefabs/BEDSIDE_CAB_01.prefab", back="-x", tint=[0.62, 0.40, 0.34],
          source=f"Marina 250 s (outer edge at its front-face depth; inner edge 3 cm off the bed post); film 1578/2648: dark mahogany "
                 f"chest with brass pulls, top about level with the mattress (0.66 ASSUMED); depth 0.40 to clear the etagere")
# the bedside lamps are generated (tools/house/hifi_parents_dressing.py: film 1610's brass base + black drum shade; the Fadnn lamp's
# yellow glass shade read wrong in build 1)
piece("parents_etagere", (3.63, 4.12), (Z0 + 0.01, Z0 + 0.34), 1.45, "Assets/Classic Wooden Furniture Pack/Prefabs/SHELVES_01.prefab", back="-z",
      source="film 2648/2663 (open dark etagere with books and a hat box at the window corner, left of the side window) and Marina "
             "244/250 (its front-left corner about 0.43 m off the headboard wall at z 0.35 in 250); SHELVES_01 squeezed to 0.49 x 0.33 x 1.45 (film's is a slim turned-post stand)")
piece("parents_armoire", (7.28, 8.43), (ZN - 0.60, ZN - 0.01), 2.05, "Assets/Classic Wooden Furniture Pack/Prefabs/WARDROBE_01.prefab", back="+z", yaw=0, tint=[0.36, 0.24, 0.21],
      source="Marina 180/188/184: dark armoire right of the front windows, against the notch wall (z 3.721) in the front corner; the film never "
             "shows it clearly (Marina only). WARDROBE_01 fitted to 1.15 x 0.59 x 2.05 (her bonnet top ~2.1), stained dark (tint: the pack's oak read light beside her dark armoire)")
piece("parents_window_table", (X1 - 0.47, X1 - 0.02), (1.888, 2.688), 0.70, "Assets/Classic Wooden Furniture Pack/Prefabs/SIDE_TABLE_01.prefab", back="+x",
      source="Marina 238/188: a demilune writing table under the front windows (film 104 s clip: a dressing table on the window wall); "
             "SIDE_TABLE_01 0.80 x 0.45 x 0.70 (centred under the window, clear of the side panels), under the 0.81 sill")
piece("parents_window_chair", (6.85, 7.37), (0.55, 1.04), 0.97, "Assets/Classic Wooden Furniture Pack/Prefabs/CHAIR_01.prefab", yaw=180,
      source="Marina 238/244: green upholstered armchair at the side window beside the floor lamp (film 104/130 s clips: green stool and chair); "
             "CHAIR_01 at native size as a stand-in, facing the room", collide=True)
piece("parents_floor_lamp", (7.45, 7.78), (0.25, 0.63), 1.45, "Assets/Fadnn - Vintage Interior Furniture Pack/Props/Prefabs/HDRP/SM_Lamp_02.prefab", yaw=180,
      source="Marina 238/244 and film 130 s clip: a tall floor lamp with a dark green shade by the window chair; Fadnn SM_Lamp_02 fitted to 1.45")
piece("parents_door_chair", (XN - 0.53, XN - 0.03), (3.85, 4.35), 0.97, "Assets/Classic Wooden Furniture Pack/Prefabs/CHAIR_01.prefab", yaw=270,
      source="Marina 176/180: a maroon armchair by the hall-door wall under two pictures; against the notch wall x 6.921, clear of the hall door's "
             "open leaf (80 deg reaches z ~4.56)", collide=True)


# the hall door's leaf (openings audit: the opening x 5.777-6.547 = 0.770 m clear vs a stock 30 in leaf 0.762; Marina's slab edges
# 0.22 units x 3.465 = 0.762 m, frames 402/407): Door_3 White as the other upstairs doors, the pack frame on the hall face (z 5.4639)
OPEN_LO, OPEN_HI, HALL_FACE = 5.7773, 6.5473, 5.4639
_w = (OPEN_HI - OPEN_LO) * 1.124; _c = (OPEN_LO + OPEN_HI) / 2
_c += 5.7373 - (_c - _w / 2)   # slid 7.7 mm toward the notch: the hall's wainscot cap ends 3 cm off the hall corner (x 5.7073 + its return); a frame edge
                               # 2.2 cm off the corner left the cap 7.7 mm short of it (trim_faces selftest); now the cap meets the frame by rule
piece("parents_door", (_c - _w / 2, _c + _w / 2), (HALL_FACE + 0.005, HALL_FACE + 0.065), 2.087,
      "Assets/Free Wood Door Pack/Prefab/Wood/Door_3/Door_3_White.prefab", back="-z", nobox=True, open=80, hinge="hi",
      source="openings audit: opening 0.770 x 2.032 (stock 30 x 80 in; Marina's slab 0.762 at her 80 in ruler); Door_3 White as girls_a/girls_b/attic/"
             "linen/Buzz (the film's are white six-panel: logged with the hall's DEVIATIONS 63h); the pack frame (leaf x 1.124 wide, x 1.027 tall) replaces "
             "the generated casing on the hall face, 0.5 cm proud. Hinge at the notch end (hi): Marina 180 s shows the knob at the fireplace-side edge; "
             "swings into the room. Open 80 deg AUTHORED (closed in every Marina frame), clear of the door-wall armchair")


def boxes():
    out = []
    for p in P:
        if p.get("nobox"):
            continue
        (x0, x1), (z0, z1), h = p["x"], p["z"], p["h"][1]
        y0 = p.get("y0", 0.0)
        if p["name"] == "parents_bed":   # the walk layer: posts, boards, rails and the deck; the floor under the rails stays free
            pz = (z0, z0 + POST), (z1 - POST, z1); px = (x0, x0 + POST), (x1 - POST, x1)
            for i, zz in enumerate(pz):
                for j, xx in enumerate(px):
                    out.append(dict(name=f"parents_bed_post_{'head' if j == 0 else 'foot'}_{'W' if i == 0 else 'B'}", x=list(xx), y=[0.0, h], z=list(zz), mat=WOOD))
            out.append(dict(name="parents_bed_headboard", x=[x0 + 0.03, x0 + 0.06], y=[0.16, 1.25], z=[z0 + 0.05, z1 - 0.05], mat=WOOD))
            out.append(dict(name="parents_bed_footboard", x=[x1 - 0.06, x1 - 0.03], y=[0.16, 0.70], z=[z0 + 0.05, z1 - 0.05], mat=WOOD))
            for i, zz in enumerate(((z0 + 0.037, z0 + 0.067), (z1 - 0.067, z1 - 0.037))):
                out.append(dict(name=f"parents_bed_rail_{'W' if i == 0 else 'B'}", x=[x0 + POST, x1 - POST], y=[0.48, 0.56], z=list(zz), mat=WOOD))
            out.append(dict(name="parents_bed_mattress", x=[x0 + 0.06, x1 - 0.06], y=[0.56, 0.72], z=[z0 + POST, z1 - POST], mat=QUILT))
            continue
        out.append(dict(name=p["name"], x=[x0, x1], y=[y0, y0 + h], z=[z0, z1], mat=WOOD))
    return [{k: ([round(v, 4) for v in b[k]] if isinstance(b[k], list) else b[k]) for k in b} for b in out]


def check():
    """walk passages for an adult (radius 0.275 + skin 0.02 = 0.59 m clear) between the pieces that bound them"""
    bad = []
    bed = next(p for p in P if p["name"] == "parents_bed")
    gaps = {"bed foot -> front wall pieces (window table)": (X1 - 0.47) - bed["x"][1],
            "bed (bath side) -> bath casing": 3.514 - bed["z"][1],
            "bed (window side) -> window wall": bed["z"][0] - Z0,
            "bed foot -> door chair": (XN - 0.53) - bed["x"][1],
            "armoire front -> window chair": 3.12 - 1.04}
    for k, v in gaps.items():
        print(f"  passage {k}: {v:.3f} m{'' if v >= 0.59 else '  < 0.59 (adult)'}")
        if v < 0.59 and "casing" not in k:
            bad.append(k)
    return bad


def write():
    B = boxes()
    out = {"note": "The parents' bedroom furniture (Oct 18 2026, TRIAL 1; changes/2026-10-18-parents-room.json). Written by tools/house/parents_layout.py "
                   "--write: do not edit 'boxes' by hand. 'pieces' are the spec boxes the store models fit into (store_props.json parents_*); 'boxes' "
                   "are the walk layer (spec x, y above the upper floor, z) drawn by SpecGreybox.Parents, hidden where a store model replaces them.",
           "room": {"built": [round(X1 - X0, 3), round(Z1 - Z0, 3)], "door_80in": [5.23, 5.23], "rig": [5.11, 5.08]},
           "marina_250": {"px_per_m": round(K, 1), "camera_to_wall_m": round(D, 2), "posts_z": [round(v, 3) for v in POSTS]},
           "pieces": P, "boxes": B}
    (ROOT / "spec/dressing/parents.json").write_text(json.dumps(out, indent=1) + "\n")
    sp_path = ROOT / "spec/dressing/store_props.json"; SP = json.loads(sp_path.read_text())
    user = {q["name"]: q for q in SP["pieces"] if q.get("placed_by") == "user"}
    names = {p["name"] for p in P}
    SP["pieces"] = [q for q in SP["pieces"] if q["name"] not in names and not (q["name"].startswith("parents_") and q["name"] not in user)]   # all its own, incl. dropped ones
    for p in P:
        if not p["store"]:
            continue
        hides = ["Casing"] if p.get("nobox") else [b["name"] for b in B if b["name"] == p["name"] or b["name"].startswith(p["name"] + "_")]
        q = {"name": p["name"], "floor": "upper", "prefab": p["store"], "x": p["x"], "z": p["z"], "y0": p.get("y0", 0.0), "height": p["h"][1],
             "hides": hides, "collide": p["collide"], "back": p["back"],
             "source": "Parents' bedroom TRIAL 1 (changes/2026-10-18-parents-room.json; tools/house/parents_layout.py): " + p["source"]}
        if p["yaw"] is not None:
            q["yaw"] = p["yaw"]
        for k in ("open", "hinge", "tint"):
            if k in p:
                q[k] = p[k]
        if p["name"] in user:
            q.update({k: user[p["name"]][k] for k in ("x", "z", "yaw", "back", "placed_by") if k in user[p["name"]]})
        SP["pieces"].append(q)
    sp_path.write_text(json.dumps(SP, indent=1) + "\n")
    return B


if __name__ == "__main__":
    bw, bd = X1 - X0, Z1 - Z0
    print(f"room built {bw:.3f} x {bd:.3f} m (bbox; notch x > {XN}, z > {ZN})")
    for nm, (a, b) in (("door-80in:parents (VGGT)", (5.23, 5.23)), ("rig-height (camera / door)", (5.11, 5.08))):
        print(f"  {nm:28s} {a:.2f} x {b:.2f}: built {100 * (bw / a - 1):+.1f}% / {100 * (bd / b - 1):+.1f}%")
    kv = (V_FLOOR - V_CEIL) / 2.50; kr = (V_FLOOR - V_CEIL) / 2.43
    print(f"Marina 250: {K:.1f} px/m from the bath casing; wall height check {kv:.1f} (2.50 built) / {kr:.1f} (2.43 rig): {100 * (kv / K - 1):+.1f}% / {100 * (kr / K - 1):+.1f}%; camera {D:.2f} m from the wall")
    print(f"head posts z {POSTS[1]:.3f} / {POSTS[0]:.3f}: spacing {SPACING:.3f} (film 1610 at the 21 in roll: 1.90), bed centre {BED_C:.3f}")
    for p in P:
        print(f"  {p['name']:28s} x {p['x']} z {p['z']} h {p['h'][1]}")
    bad = check()
    print("check: " + ("PASS" if not bad else f"{len(bad)} problems: {bad}"))
    if "--write" in sys.argv:
        b = write(); print(f"wrote spec/dressing/parents.json ({len(b)} boxes) and parents_* store_props entries")
