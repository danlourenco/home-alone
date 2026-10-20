"""openings: HOUSE-KERNEL step 2 (docs/HOUSE-KERNEL.md, stage 3): every opening (door, arch, window, prop door, the landing window
and the front door assembly) is the source of its casing on each face it is cased on, its header and its limits.

Before (to Oct 17) casing was placed per case in three places that never agreed on purpose: SpecGreybox.Storey laid legs and heads
per opening and dropped any that ran into a wall (a physics test at build time); StoreProps hid the casing a pack door frame replaces;
the landing window and the front door drew their own casing inside their models, which the trim only knew about by a 5 mm physics
probe (front door) or not at all (the landing window: its wall was "panelled by the model" at its own height, STATUS 8t-3).

Each opening record holds:
  pieces  every casing part (leg_lo, leg_hi, head, stool, apron), the cut's liners (liner_lo/hi/head/sill, Oct 20) and mounted piece (prop door, a model's frame) on each face, a box in
          spec x / z and world y, with the face it is on; "by" names who draws it (null = SpecGreybox lays it from this file; a model or
          a store prop otherwise). spec/trim_faces.json cuts every run at these boxes, so the trim ends at the casing by construction.
  dropped casing the opening does NOT carry on a face, with the reason (a recorded decision, never a silent skip): a leg that would run
          into a wall or floor (the next room is no wider than the opening), a face replaced by a pack door frame, a plain arch.
  header  the wall box over the head and the ceilings either side.
  limits  the builder's rules, checked here at data time (seconds, no Unity build):
          head-under-header   the wall over the opening starts at its head (a cut and its header agree)
          sill-on-wall        a window's wall below ends at its sill
          under-ceiling       the head, plus the casing head where cased, stays under the ceiling of the room on that face; an arch's
                              crown under the ceiling of both rooms (catches the Oct 16 arch: crown 2.17 under a 2.155 passage)
          swing-room          a door leaf's swing from closed to open (90 deg) is clear of walls and stair solids, and it rests there
A measurement that breaks a limit is refused: the script exits 1 with the reason and writes nothing.

THE SWITCH: OWN_TRIM (one line). True = SpecGreybox lays the casing from this file, the landing window's panelling comes from the face
trim (hifi_landing_window.py reads it), the wall is cut to the window's rough opening; False = the old per-case paths (casing in
SpecGreybox.Storey, the window model panels its wall, trim_faces's old mounted-piece emulation). Written into spec/openings.json.

  python3 tools/house/openings.py            # -> spec/openings.json (refused, exit 1, if a limit breaks)
  python3 tools/house/openings.py --check    # exit 1 if stale, a limit breaks, or the self-test fails
  python3 tools/house/openings.py --compare <House_WallGrid.unity>   # the built scene's casings vs this file's (old vs new path)
"""
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

OWN_TRIM = True

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "spec/openings.json"
INPUTS = ["spec/geometry.json", "spec/house_spec.json", "spec/house_spec.ground.json", "spec/dressing/store_props.json",
          "spec/dressing/french_doors.json", "spec/dressing/buzz.json", "tools/house/hifi_door.py", "tools/house/openings.py"]
CASING_W, CASING_PROUD, STOOL_PROUD, STOOL_T, HALF, PROP_T = 0.07, 0.02, 0.04, 0.025, 0.07, 0.03   # SpecGreybox consts
LINER_T = 0.012                                  # jamb / head / sill liner board (>= 1 cm proud of the cut face: zfight-check rule 2)
ARCH_MODELS = {"foyer|rear_passage": "FoyerArch",   # SpecGreybox.Arch.cs ArchModels: plain (film), no casing
               # the hall's plastered arches (hifi_hall_arches.py, film 410/2296/10828: no casing); the legs to the spring that
               # stood here were the "random vertical stripe" of walk note 2026-10-17T08:28:50
               "hall_corridor|hall_end": "HallArches", "hall_corridor|hall_corridor_south": "HallArches"}


def load(p):
    return json.loads((ROOT / p).read_text())


G, S, SG = load("spec/geometry.json"), load("spec/house_spec.json"), load("spec/house_spec.ground.json")
PROPS, FD = load("spec/dressing/store_props.json")["pieces"], load("spec/dressing/french_doors.json")
GY = G["ground"]["floor_y"]
STOREYS = [("upstairs", 0.0), ("ground", GY)]   # build order (SpecGreybox.BuildWallGrid): upstairs first


def B(x, z, y, fy=0.0):
    return [x[0], x[1], z[0], z[1], y[0] + fy, y[1] + fy]


def overlap(a, b, shrink=0.0):
    return all(a[2 * i] + shrink < b[2 * i + 1] and b[2 * i] < a[2 * i + 1] - shrink for i in range(3))


def inside(b, p, e=0.0):
    """p = (x, z, y), the box order"""
    return all(b[2 * i] - e <= p[i] <= b[2 * i + 1] + e for i in range(3))


def point_in_poly(pts, x, z):
    c = False
    for (x0, z0), (x1, z1) in zip(pts, pts[1:] + pts[:1]):
        if (z0 > z) != (z1 > z) and x < x0 + (z - z0) * (x1 - x0) / (z1 - z0):
            c = not c
    return c


WALLS = {st: [B(w["x"], w["z"], w["y"], fy) for w in G[st]["walls"]] for st, fy in STOREYS}
FLOORS = {st: [B(f["x"], f["z"], f["y"], fy) for f in G[st]["floor"]] for st, fy in STOREYS}
STAIR_SOLIDS = [B(b["x"], b["z"], b["y"]) for b in S["stair"]["boxes"] + S["attic_stair"]["boxes"] if b["kind"] in ("step", "landing")] + \
               ([B(b["x"], b["z"], b["y"], GY) for b in SG["stair"]["boxes"] if b["kind"] in ("step", "landing")] if SG.get("stair") else [])
# furniture a leaf must clear (plan only: any piece standing on the floor below the head); placed rooms' dressing files
FURNITURE = {"upstairs": [[b["x"][0], b["x"][1], b["z"][0], b["z"][1], -99.0, 99.0]
                          for b in load(ROOT / "spec/dressing/buzz.json")["boxes"] if b["y"][0] < 2.0]}


def room_at(st, x, z):
    return next((r for r in G[st]["rooms"] if point_in_poly([tuple(p) for p in r["poly"]], x, z)), None)


def front_door():
    """The front door assembly's frame (tools/house/hifi_door.py constants, the same numbers its model is built from): pilasters
    with plinths 1 cm wider each side, standing 6.5 cm off the vestibule's front wall face, up to the arch's apex."""
    src = (ROOT / "tools/house/hifi_door.py").read_text()
    num = lambda pat: [float(v) for v in re.search(pat, src).groups()]
    wf, = num(r"\nWF = ([\d.]+)")
    pz0, pz1, pw = num(r"\nPZ0, PZ1, PW = ([\d.]+), ([\d.]+), ([\d.]+)")
    tb, apex = num(r"\nTB, APEX = ([\d.]+), ([\d.]+)")
    return {"id": "ground:front_door", "storey": "ground", "kind": "door", "between": ["vestibule"], "model": "FrontDoor",
            "axis": "x", "c": wf + HALF, "lo": pz0 + pw, "hi": pz1 - pw, "head": tb, "pieces": [
                {"part": "frame", "face": ["z", round(wf, 4), -1], "by": "FrontDoor", "box": [wf - 0.065, wf, pz0 - 0.01, pz1 + 0.01, GY, GY + apex]}],
            "dropped": [], "limits": []}


def landing_window(o):
    """The landing window (spec/house_spec.ground.json wall_openings; hifi_landing_window.py builds it from these numbers): casing legs
    from the stool to the spring line and the band round the fanlight (drawn by the model), the stool's nose and the apron. Its rough
    opening sits under the stool (a stool rests on the wall, it is not let into it: the stool top flush with the cut was the 8t-2 z-fight)."""
    face, cas, sill = o["face"], o["casing_m"], o["sill_m"]
    z0, z1 = o["z_centre"] - o["width_m"] / 2, o["z_centre"] + o["width_m"] / 2
    spring = sill + o["sash_m"] + o["transom_m"]
    stool_t = 0.035
    k = ["z", round(face, 4), 1]
    y = lambda a, b: [GY + a, GY + b]
    pc = lambda part, x0, x1, za, zb, ya, yb: {"part": part, "face": k, "by": "LandingWindow", "box": [x0, x1, za, zb] + y(ya, yb)}
    return {"id": "ground:wall_opening:" + o["name"], "storey": "ground", "kind": "window", "between": ["main_stair_opening"],
            "model": "LandingWindow", "axis": "x", "c": (o["x"][0] + o["x"][1]) / 2, "lo": z0, "hi": z1, "sill": sill,
            "head": spring + o["fan_rise_m"], "stool_t": stool_t,
            "rough": {"x": o["x"], "y": [sill - stool_t, o["y"][1]], "z": o["z"]},
            "pieces": [pc("leg_lo", face, face + 0.02, z0 - cas, z0, sill, spring), pc("leg_hi", face, face + 0.02, z1, z1 + cas, sill, spring),
                       pc("head", face, face + 0.02, z0 - cas, z1 + cas, spring, spring + o["fan_rise_m"] + cas),   # the band's box
                       pc("stool", face, face + 0.07, z0 - cas - 0.03, z1 + cas + 0.03, sill - stool_t, sill),
                       pc("apron", face, face + 0.02, z0 - cas, z1 + cas, sill - 0.13, sill - stool_t)],
            "dropped": [], "limits": []}


def openings():
    """Every opening's record, in SpecGreybox's build order (a casing is tested against the walls and floors built before it)."""
    out, walls_so_far, floors_so_far = [], [], []
    for st, fy in STOREYS:
        walls_so_far += WALLS[st]; floors_so_far += FLOORS[st]
        for o in G[st]["openings"]:
            k, ax, c, lo, hi = o["kind"], o["axis"], o["c"], o["lo"], o["hi"]
            if k in ("open", "rail"):
                continue
            faxis = "x" if ax == "z" else "z"
            key = "|".join(sorted(o["between"]))
            rec = {"id": f"{st}:{k}:{key}:{lo:.3f}", "storey": st, "kind": k, "between": o["between"], "axis": ax, "c": c, "lo": lo, "hi": hi,
                   "head": o.get("height") if k != "window" else o["head"], "sill": o.get("sill"), "spring": o.get("spring"),
                   "model": o.get("model"), "pieces": [], "dropped": [], "limits": []}

            def piece(part, n, f0, f1, s0, s1, y0, y1, by=None):
                a, b2 = min(f0, f1), max(f0, f1)
                box = [s0, s1, a, b2, y0 + fy, y1 + fy] if faxis == "x" else [a, b2, s0, s1, y0 + fy, y1 + fy]
                face = [faxis, round(c + n * HALF, 4), n]
                # a piece that meets a wall beside the opening is scribed to it (cut along the face to the free span), as a carpenter
                # would; it is dropped only when nothing is left or the blocker stands over the opening itself (a floor). Before Oct 17
                # 20:38 the whole piece was dropped, so a leg with no room beside it took the head with it (Buzz's room face)
                i0 = 0 if faxis == "x" else 2; m = (lo + hi) / 2; w0 = box[i0 + 1] - box[i0]
                if part in ("leg_lo", "leg_hi", "head", "stool"):
                    for w in walls_so_far + floors_so_far:
                        if not overlap(box, w, 0.002):
                            continue
                        if w[i0 + 1] <= m: box[i0] = max(box[i0], w[i0 + 1])
                        elif w[i0] >= m: box[i0 + 1] = min(box[i0 + 1], w[i0])
                        else: box[i0] = box[i0 + 1]
                        if box[i0 + 1] - box[i0] < 0.005:
                            rec["dropped"].append({"part": part, "face": face, "reason": "no room for it: a wall or floor stands where it would go (the next room is no wider than the opening)"})
                            return
                pc = {"part": part, "face": face, "by": by, "box": [round(v, 5) for v in box]}
                if box[i0 + 1] - box[i0] < w0 - 1e-6:
                    pc["scribed"] = round(box[i0 + 1] - box[i0], 4)   # width left after scribing to the wall beside it
                rec["pieces"].append(pc)

            def cased(n, head, sill=0.0):
                f0 = c + n * HALF; f1 = f0 + n * CASING_PROUD
                piece("leg_lo", n, f0, f1, lo - CASING_W, lo, sill, head + CASING_W)
                piece("leg_hi", n, f0, f1, hi, hi + CASING_W, sill, head + CASING_W)
                piece("head", n, f0, f1, lo - CASING_W, hi + CASING_W, head, head + CASING_W)

            def lined(y0, head):
                """Jamb liners (walk note 2026-10-20T08:28:52: the hall bath window's reveal showed the wall paper inside the casing;
                every grey-box door and window cut showed its wall's paper or paint on its jambs, head and sill: the Opening face check's
                REVEAL rule). The cut's faces are carpentry: a LINER_T painted board on each jamb, the head and (windows) the sill, through
                the wall's whole thickness, one piece per half (each owned by its face, n). The boards stand IN the wall, behind the cut's
                faces ("in_wall": SpecGreybox.LayCasings carves the wall boxes there), so the measured clear opening stays as it is (lined
                inside the cut, the first build's boards took 2.4 cm off every door and 1.2 cm off its head: new BLOCKED lines at the
                attic door) and the casing laps the boards' edges on the face."""
                for n in (-1, 1):
                    f0, f1 = c, c + n * HALF
                    yb = y0   # the jambs stand on the sill board (or the floor)
                    if y0 > 0:
                        piece("liner_sill", n, f0, f1, lo - LINER_T, hi + LINER_T, y0 - LINER_T, y0)
                    piece("liner_lo", n, f0, f1, lo - LINER_T, lo, yb, head)
                    piece("liner_hi", n, f0, f1, hi, hi + LINER_T, yb, head)
                    piece("liner_head", n, f0, f1, lo - LINER_T, hi + LINER_T, head, head + LINER_T)
                for pc in rec["pieces"]:
                    if pc["part"].startswith("liner"): pc["in_wall"] = True

            if k == "door" or (k == "arch" and o.get("cased")):
                for n in (-1, 1):
                    cased(n, o["height"])
                if k == "door" and not o.get("model"):
                    lined(0.0, o["height"])
            elif k == "arch" and o.get("spring") is not None:
                if key in ARCH_MODELS:
                    for n in (-1, 1):
                        rec["dropped"].append({"part": "casing", "face": [faxis, round(c + n * HALF, 4), n], "reason": f"plain arch: {ARCH_MODELS[key]} model, no casing (film)"})
                    out.append(rec); continue
                n = 1 if ax == "z" else -1   # SpecGreybox.Storey: legs to the spring on one face (world wc - h)
                f0 = c + n * HALF; f1 = f0 + n * CASING_PROUD
                piece("leg_lo", n, f0, f1, lo - CASING_W, lo, 0, o["spring"])
                piece("leg_hi", n, f0, f1, hi, hi + CASING_W, 0, o["spring"])
            elif k == "fake_door":
                for n in (-1, 1):
                    f0 = c + n * HALF
                    piece("prop", n, f0, f0 + n * PROP_T, lo, hi, 0, o["height"], by="SpecGreybox.Storey PropDoor")
            elif k == "window" and o.get("bare") and not o.get("model"):   # a model's sidelight: its frame is the model's, its cut is lined here
                lined(o["sill"], o["head"])
            elif k == "window" and not o.get("bare"):
                n = -o["faces"][0]   # the room's face (faces[0] is the outward side, spec)
                cased(n, o["head"], o["sill"])
                if not o.get("model"):
                    f0 = c + n * HALF
                    piece("stool", n, f0, f0 + n * STOOL_PROUD, lo - CASING_W - 0.025, hi + CASING_W + 0.025, o["sill"] - STOOL_T, o["sill"])
                    lined(o["sill"], o["head"])
            out.append(rec)
    out += [landing_window(o) for o in SG.get("wall_openings", []) if o["name"] == "landing_window"]
    out.append(front_door())
    store_frames(out)
    out += surface_doors()
    return out


def surface_doors():
    """A store-prop door hung ON a wall face, no opening cut (store_props.json "surface": true, e.g. Buzz's fake closet door): its box
    is a mounted frame on the face its `back` is against, so the trim stops at it. kind fake_door: no header or swing limits."""
    out = []
    for p in PROPS:
        if not isinstance(p, dict) or not p.get("surface"):
            continue
        st, fy = ("upstairs", 0.0) if p.get("floor") == "upper" else ("ground", GY)
        b = p["back"]; ax = "z" if b.endswith("z") else "x"   # the axis of the plane the face lies in (openings' "axis")
        span, depth = (p["x"], p["z"]) if ax == "z" else (p["z"], p["x"])
        plane, n = (depth[1], -1) if b.startswith("+") else (depth[0], 1)
        face = ["x" if ax == "z" else "z", round(plane, 4), n]
        out.append({"id": f"{st}:surface_door:{p['name']}", "storey": st, "kind": "fake_door", "between": [], "axis": ax, "c": plane,
                    "lo": span[0], "hi": span[1], "head": p["height"], "sill": None, "spring": None, "model": None,
                    "pieces": [{"part": "frame", "face": face, "by": "store_props:" + p["name"], "box": [round(v, 5) for v in B(p["x"], p["z"], [p["y0"], p["y0"] + p["height"]], fy)]}],
                    "dropped": [], "limits": []})
    return out


def store_frames(recs):
    """A store-prop door frame that replaces generated casing (store_props.json "hides": ["Casing"], StoreProps.cs: renderers named
    Casing touching the prop's box grown 10 cm): those pieces are drawn by the prop, and the face's mounted piece is the prop's box."""
    for p in PROPS:
        if not isinstance(p, dict) or "Casing" not in (p.get("hides") or []):
            continue
        fy = 0.0 if p.get("floor") == "upper" else GY
        pb = [p["x"][0], p["x"][1], p["z"][0], p["z"][1], p["y0"] + fy, p["y0"] + fy + p["height"]]
        reach = [v + (0.1 if i % 2 else -0.1) for i, v in enumerate(pb)]
        for r in recs:
            hit = [pc for pc in r["pieces"] if pc["by"] is None and not pc["part"].startswith("liner") and overlap(pc["box"], reach)]   # a pack frame laps the face, the cut stays lined
            if not hit:
                continue
            for pc in hit:
                r["pieces"].remove(pc)
                r["dropped"].append({"part": pc["part"], "face": pc["face"], "reason": f"replaced by the store prop {p['name']}'s door frame (store_props.json)"})
            r["pieces"].append({"part": "frame", "face": hit[0]["face"], "by": "store_props:" + p["name"], "box": [round(v, 5) for v in pb]})


# ------------------------------------------------------------------------------------------------ limits
def header_of(r):
    """The wall box over the opening's middle (the header) and its storey's walls below the sill."""
    if r["storey"] not in WALLS or r.get("model") in ("FrontDoor", "LandingWindow"):
        return None, None
    fy = dict(STOREYS)[r["storey"]]; m = (r["lo"] + r["hi"]) / 2
    pt = lambda y: (r["c"], m, y + fy) if r["axis"] == "x" else (m, r["c"], y + fy)   # box order: x, z, y
    above = [w for w in WALLS[r["storey"]] if inside(w, pt(r["head"] + 0.01))] if r["head"] else []
    below = [w for w in WALLS[r["storey"]] if r.get("sill") and inside(w, pt(r["sill"] - 0.01))]
    return (above[0] if above else None), (below[0] if below else None)


def leaves():
    """Door leaves in the house's data that swing: (opening id match, hinge s, latch direction, face n the leaf swings to, width)."""
    out = []
    for k, o in enumerate(sorted((q for q in G["ground"]["openings"] if q["between"] == ["dining_room", "kitchen"]), key=lambda q: -q["hi"])):   # SpecGreybox.SwingDoors
        for n in (-1, 1):   # double-acting
            out.append(("ground", o, o["hi"] - 0.005, -1, n, o["hi"] - o["lo"] - 0.01, f"dining swing door {k + 1} (SwingDoor.glb, double-acting)"))
    L = FD["leaf"]
    for pr in FD["pairs"]:
        if pr.get("surface"):
            continue
        q = next(q for q in G["ground"]["openings"] if sorted(q["between"]) == sorted(pr["between"]))
        room = next(r for r in G["ground"]["rooms"] if r["name"] == pr["room"])
        rc = sum(p[1 if q["axis"] == "z" else 0] for p in room["poly"]) / len(room["poly"])
        n = 1 if rc > q["c"] else -1
        w = (q["hi"] - q["lo"] - 2 * L["jamb_t"] - 3 * L["gap"]) / 2
        out.append(("ground", q, q["lo"] + L["jamb_t"] + L["gap"], 1, n, w, f"French pair {'|'.join(pr['between'])} lo leaf"))
        out.append(("ground", q, q["hi"] - L["jamb_t"] - L["gap"], -1, n, w, f"French pair {'|'.join(pr['between'])} hi leaf"))
    bd = next(q for q in G["ground"]["openings"] if q.get("model") == "BackDoor")   # swings in, hinges at the high-z edge (hifi_back_door.py)
    out.append(("ground", bd, bd["hi"] - 0.019, -1, -bd["faces"][0], bd["hi"] - bd["lo"] - 0.044, "back door (BackDoor.glb, swings in)"))
    for p in PROPS:   # store-prop doors with a hinge (StoreProps.cs: open toward `back`, or away with swing "out")
        if not isinstance(p, dict) or "hinge" not in p:
            continue
        st = "upstairs" if p.get("floor") == "upper" else "ground"
        alongx = p["back"].endswith("z")
        span = p["x"] if alongx else p["z"]
        q = min((q for q in G[st]["openings"] if q["axis"] == ("z" if alongx else "x") and q["lo"] < (span[0] + span[1]) / 2 < q["hi"]
                 and abs(q["c"] - ((p["z"] if alongx else p["x"])[0] + (p["z"] if alongx else p["x"])[1]) / 2) < 0.3), key=lambda q: 0, default=None)
        if q is None:
            continue
        n = (1 if p["back"][0] == "+" else -1) * (-1 if p.get("swing") == "out" else 1)
        hs = q["lo"] if p["hinge"] == "lo" else q["hi"]
        out.append((st, q, hs, 1 if p["hinge"] == "lo" else -1, n, q["hi"] - q["lo"] - 0.02, f"store door {p['name']}"))
    return out


def swing_clear(st, o, hinge, latch, n, w):
    """Sample the leaf's sweep (closed -> 90 deg open, its resting place) 1 m above the floor; the first point inside a wall, a stair
    solid or a piece of furniture (FURNITURE, plan), or None."""
    fy = dict(STOREYS)[st]; face = o["c"] + n * HALF
    for deg in range(0, 91, 5):
        t = math.radians(deg)
        for i in range(1, 11):
            r = w * i / 10
            s, a = hinge + latch * r * math.cos(t), face + n * (0.005 + r * math.sin(t))
            p = (a, s, fy + 1.0) if o["axis"] == "x" else (s, a, fy + 1.0)   # box order: x, z, y
            for b in WALLS[st] + STAIR_SOLIDS + FURNITURE.get(st, []):
                if inside(b, p, -0.001):
                    return deg, round(r, 3), [round(v, 3) for v in p]
    return None


def check_limits(recs, leaf_list):
    problems = []
    def lim(r, rule, ok, detail):
        r["limits"].append({"rule": rule, "ok": bool(ok), "detail": detail})
        if not ok:
            problems.append(f"{r['id']}: {rule}: {detail}")
    for r in recs:
        st = r["storey"]
        if st not in WALLS or r["kind"] == "fake_door":
            continue
        fy = dict(STOREYS)[st]; m = (r["lo"] + r["hi"]) / 2
        if r.get("model") in ("FrontDoor", "LandingWindow"):
            # a model's opening: under the ceiling of the room it faces (the stair well's ceiling for the landing window)
            top = r["head"] + (0.09 if r["model"] == "LandingWindow" else 0.0)
            ceil = min(b["y"][0] - GY for b in S["stair"]["boxes"] if b["kind"] == "ceiling") if r["model"] == "LandingWindow" else \
                next(q["ceil"] for q in G["ground"]["rooms"] if q["name"] == "vestibule")
            lim(r, "under-ceiling", top < ceil, f"top {top:.3f} {'under' if top < ceil else 'ABOVE'} the ceiling {ceil:.3f}")
            continue
        hdr, below = header_of(r)
        r["header"] = {"box": hdr, "ceilings": {}}
        lim(r, "head-under-header", hdr is not None and abs(hdr[4] - fy - r["head"]) < 0.002,
            f"head {r['head']:.3f}, the wall over it starts at {hdr[4] - fy:.3f}" if hdr else f"head {r['head']:.3f}: no wall over it")
        if r.get("sill"):
            lim(r, "sill-on-wall", below is not None and abs(below[5] - fy - r["sill"]) < 0.002,
                f"sill {r['sill']:.3f}, the wall below ends at {below[5] - fy:.3f}" if below else f"sill {r['sill']:.3f}: no wall below")
        faces = (-1, 1) if r["kind"] != "window" else ()
        for n in faces or {pc["face"][2] for pc in r["pieces"]}:
            off = HALF + 0.3
            room = room_at(st, r["c"] + n * off, m) if r["axis"] == "x" else room_at(st, m, r["c"] + n * off)
            if room is None:
                continue
            ceil = room["ceil"]; r["header"]["ceilings"][room["name"]] = ceil
            casing = any(pc["face"][2] == n and pc["part"] == "head" for pc in r["pieces"])
            top = r["head"] + (CASING_W if casing else 0.0)
            what = "crown" if r.get("spring") is not None else "head + casing" if casing else "head"
            lim(r, "under-ceiling", top < ceil - 1e-6, f"{what} {top:.3f} {'under' if top < ceil - 1e-6 else 'ABOVE'} {room['name']}'s ceiling {ceil:.3f}")
            if r["kind"] == "door":   # a door is cased over its head on every face that faces a room (walk note 2026-10-17 20:38, Buzz)
                head = [pc for pc in r["pieces"] if pc["face"][2] == n and (pc["part"] == "head" or pc["part"] == "frame")]
                lim(r, "head-cased", head, f"{room['name']} face: " + (f"{head[0]['part']} by {head[0]['by'] or 'SpecGreybox'}" if head else "NO head casing"))
        if r.get("spring") is not None:
            lim(r, "spring-under-crown", r["spring"] < r["head"], f"spring {r['spring']:.3f} under the crown {r['head']:.3f}")
    for st, o, hinge, latch, n, w, what in leaf_list:
        r = next(r for r in recs if r["storey"] == st and abs(r["c"] - o["c"]) < 1e-6 and abs(r["lo"] - o["lo"]) < 1e-6 and r["axis"] == o["axis"])
        hit = swing_clear(st, o, hinge, latch, n, w)
        r.setdefault("swings", []).append({"what": what, "hinge_s": round(hinge, 4), "toward_n": n, "width": round(w, 3)})
        lim(r, "swing-room", hit is None, f"{what}: {w:.2f} m leaf swings clear to 90 deg" if hit is None else
            f"{what}: the leaf hits a wall or stair at {hit[0]} deg, {hit[1]} m from the hinge, spec {hit[2]}")
    return problems


def build(geom=None):
    recs = openings()
    problems = check_limits(recs, leaves())
    return {"note": "Generated by tools/house/openings.py (HOUSE-KERNEL step 2): do not edit. Boxes: spec x, spec z, world y. face = "
                    "[axis the face runs along, its plane (spec), its normal n]. by = who draws the piece (null: SpecGreybox lays it from here).",
            "own_trim": OWN_TRIM, "inputs": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS},
            "openings": recs, "problems": problems}


# ------------------------------------------------------------------------------------------------ self-test: limits refuse what they must
def selftest():
    """The limits on planted mistakes (each must be refused, each with its reason), and the real house passes."""
    global G
    bad, keep = [], G
    try:
        def planted(edit, rule):
            global G
            G = copy.deepcopy(keep); edit(G)
            probs = check_limits(openings(), leaves())
            if not any(rule in p for p in probs):
                bad.append(f"selftest: {rule} did not refuse the planted mistake")
        def arch(g):   # the Oct 16 arch: crown 2.17 under the rear passage's 2.155
            o = next(o for o in g["ground"]["openings"] if sorted(o["between"]) == ["foyer", "rear_passage"]); o["height"] = 2.17
        planted(arch, "under-ceiling")
        def door_tall(g):   # a door whose head is not where its header starts (cut and header disagree)
            next(o for o in g["upstairs"]["openings"] if o["kind"] == "door")["height"] = 2.10
        planted(door_tall, "head-under-header")
        def swing(g):   # the dining swing door's opening moved against the kitchen's back wall: the leaf hits it
            for o in g["ground"]["openings"]:
                if o["between"] == ["dining_room", "kitchen"]:
                    w = [b for b in g["ground"]["walls"] if b["x"][0] < o["c"] < b["x"][1] and b["z"][0] > o["hi"]]
                    if w:
                        z = min(b["z"][0] for b in w); o["hi"], o["lo"] = z + 0.30, z + 0.30 - (o["hi"] - o["lo"])
        planted(swing, "swing-room")
        def bed_in_swing(g):   # a piece of Buzz's furniture standing in his door's swing (store prop buzz_door, hinge lo, into the room)
            o = next(o for o in g["upstairs"]["openings"] if o["between"] == ["buzz_room", "hall_corridor"])
            FURNITURE["upstairs"].append([o["lo"] + 0.3, o["lo"] + 0.5, o["c"] + 0.4, o["c"] + 0.6, -99.0, 99.0])
        try:
            planted(bed_in_swing, "swing-room")
        finally:
            FURNITURE["upstairs"].pop()
    finally:
        G = keep
    return bad


def compare(scene):
    """The scene's Casing boxes (SpecGreybox's, enabled or hidden) vs the pieces this file has SpecGreybox lay: matched within 1 mm,
    moved, only-old, only-new."""
    t = Path(scene).read_text()
    docs = re.split(r"\n--- !u!(\d+) &(\d+)[^\n]*", "\n" + t)
    objs = {docs[i + 1]: (docs[i], docs[i + 2]) for i in range(1, len(docs) - 1, 3)}
    comp = {}
    for k, (cls, body) in objs.items():
        mm = re.search(r"m_GameObject: \{fileID: (\d+)", body)
        if mm:
            comp.setdefault(mm.group(1), {})[cls] = body
    old = []
    for k, (cls, body) in objs.items():
        if cls == "1" and re.search(r"m_Name: Casing\n", body + "\n"):
            tr, mr = comp[k]["4"], comp[k].get("23", "")
            v = lambda s: [float(x) for x in re.search(s + r": \{x: ([-\d.e]+), y: ([-\d.e]+), z: ([-\d.e]+)", tr).groups()]
            p, sc = v("m_LocalPosition"), v("m_LocalScale")
            if re.search(r"m_Enabled: (\d)", mr).group(1) == "1":   # a hidden one (StoreProps "hides") is not seen
                old.append([p[0] - sc[0] / 2, p[0] + sc[0] / 2, -(p[2] + sc[2] / 2), -(p[2] - sc[2] / 2), p[1] - sc[1] / 2, p[1] + sc[1] / 2])
    J = json.loads(OUT.read_text())
    new = [(r["id"], pc) for r in J["openings"] for pc in r["pieces"] if pc["by"] is None and pc["part"] != "prop"]
    used, rows = set(), []
    for rid, pc in new:
        d = [(max(abs(a - b) for a, b in zip(pc["box"], o)), i) for i, o in enumerate(old) if i not in used]
        best = min(d) if d else (9, -1)
        if best[0] < 0.001:
            used.add(best[1]); continue
        rows.append(f"only-new  {rid} {pc['part']} face {pc['face']} box {[round(v, 3) for v in pc['box']]}" + (f" (nearest old {best[0]:.3f} m off)" if best[1] >= 0 else ""))
    rows += [f"only-old  box {[round(v, 3) for v in o]}" for i, o in enumerate(old) if i not in used]
    print(f"casings: old scene {len(old)} visible, new file {len(new)} laid by SpecGreybox, {len(used)} identical (< 1 mm), {len(rows)} differ")
    for r in rows:
        print(" ", r)


if __name__ == "__main__":
    if "--compare" in sys.argv:
        compare(sys.argv[sys.argv.index("--compare") + 1]); sys.exit(0)
    J = build()
    bad = list(J["problems"]) + selftest()
    if "--check" in sys.argv:
        old = json.loads(OUT.read_text()) if OUT.exists() else {}
        stale = {k: v for k, v in old.items()} != json.loads(json.dumps(J))
        print("spec/openings.json " + ("STALE: run python3 tools/house/openings.py" if stale else "up to date"))
        for b in bad: print("FAIL", b)
        sys.exit(1 if stale or bad else 0)
    if J["problems"]:
        print("REFUSED (spec/openings.json not written):")
        for b in J["problems"]: print("  FAIL", b)
        sys.exit(1)
    OUT.write_text(json.dumps(J, indent=0) + "\n")
    n_lim = sum(len(r["limits"]) for r in J["openings"])
    print(f"{len(J['openings'])} openings, {sum(len(r['pieces']) for r in J['openings'])} pieces "
          f"({sum(pc['by'] is None for r in J['openings'] for pc in r['pieces'])} laid by SpecGreybox), "
          f"{sum(len(r['dropped']) for r in J['openings'])} dropped (recorded), {n_lim} limits, 0 broken; own_trim {OWN_TRIM}")
    for b in bad: print("FAIL", b)
    sys.exit(1 if bad else 0)
