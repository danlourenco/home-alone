"""trim_faces: HOUSE-KERNEL step 1 (docs/HOUSE-KERNEL.md, stage 7): baseboard, wainscot panel, cap rail and the stair's skirt, panel
and rail as RUNS along the house's visible wall faces, stairs and landings included, so their joints close by construction.

Before (Oct 16-17) trim came from three places that never met on purpose: room outlines (SpecGreybox.Storey -> LayTrim), the main
stair model's own skirt/panel/rail (hifi_foyer.py, flight 1's wall only) and the landing window model's panelling. The walk notes of
Oct 17 08:30 (a triangle of paper where flight 1's skirt met the landing's, the landing's north wall with no wainscot at all) sat
exactly where one producer stopped and the next began.

The model (read only from the house's own data: spec/geometry.json walls, rooms and openings; the stair boxes; the finishes):
  1. Supports: every finished room's floor along each polygon edge (a wall face), every stair flight's NOSING LINE along each of its
     sides (foot one going in front of the first nosing, top at the next level's nosing), every landing's top along its edges.
  2. Supports on one face line that touch (share a point within 1 cm, or meet across <= 3 cm: a nosing) are merged into ONE chain whose
     line is their upper envelope: the foyer floor, flight 1's rake and the landing are one line on the stair wall; the landing, flight
     2's rake and the upper hall one line on the north wall. A support inside a solid (the floor under the steps) drops out.
  3. Each chain is cut where the face has a mounted piece in front of it (casings and prop doors, generated from the same openings as
     the builder makes them) or no wall behind it, and split where its finish changes. A stair's finish is the room it rises from; it is
     carried along that room's floor from the foot to the run's termination (user note Oct 16 09:34: the skirt and the baseboard met
     short at the foot); at its top it meets the upper room's trim end to end.
  4. Members per finish (profiles unchanged from what the house used): room = baseboard (0.14, or finishes.json baseboard_m; 1.2 cm proud)
     + cap rail (h-0.01..h+0.03, 3 cm proud) over a wainscot (the wall's own lower material); stair = skirt (from the stair's surface:
     treads, landing or floor, so nothing can stand between them, to the line + 0.20; 2.2 cm), raking panel (line + 0.20 .. line + h,
     1.5 cm) and rail (line + h - 0.005 .. + 0.035, 1.5-4.5 cm off the wall).
  5. A face whose wall carries a window MODEL (spec/house_spec.ground.json wall_openings) with its sill under the cap: the cap drops to
     the window's stool and that model panels the wall (the landing window, film 11966/12133); the face is checked, not laid.
Every chain end must terminate at a corner, an opening (or a mounted piece) or another chain: a free end is an error.

  python3 tools/house/trim_faces.py            # -> spec/trim_faces.json (SpecGreybox lays it, the build's Trim check samples it)
  python3 tools/house/trim_faces.py --check    # exit 1 if spec/trim_faces.json is stale (inputs changed) or the self-test fails
Coordinates: computed in spec (x, z) with world y; written in Unity world (z = -spec z).
"""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "spec/trim_faces.json"
INPUTS = ["spec/geometry.json", "spec/house_spec.json", "spec/house_spec.ground.json", "spec/dressing/foyer.json",
          "spec/dressing/finishes.json", "tools/house/trim_faces.py"]
CASING_W, CASING_PROUD, STOOL_PROUD, STOOL_T, HALF = 0.07, 0.02, 0.04, 0.025, 0.07   # SpecGreybox consts (door/window trim, h)
NOSE = 0.025                                     # tread nosing (hifi_foyer.py)
REACH = 0.02                                     # anything mounted within 2 cm in front of a member stops it (LayTrim)
KITCHEN = {"kitchen", "back_stair"}
EPS = 1e-6


def load(p):
    return json.loads((ROOT / p).read_text())


# ------------------------------------------------------------------------------------------------ the house's data
G, S, SG = load("spec/geometry.json"), load("spec/house_spec.json"), load("spec/house_spec.ground.json")
FOY, FIN = load("spec/dressing/foyer.json")["walls"], load("spec/dressing/finishes.json")["rooms"]
GY = G["ground"]["floor_y"]
STOREYS = [("upstairs", 0.0, {"main_stair_opening"}), ("ground", GY, set(FOY["spaces"]))]   # SpecGreybox.BuildWallGrid's papered sets


def B(x, z, y):
    return (x[0], x[1], z[0], z[1], y[0], y[1])   # box in spec x, spec z, world y


WALLS, FLOORS = [], []
for st, fy, _ in STOREYS:
    WALLS += [B(w["x"], w["z"], (w["y"][0] + fy, w["y"][1] + fy)) for w in G[st]["walls"]]
    FLOORS += [B(f["x"], f["z"], (f["y"][0] + fy, f["y"][1] + fy)) for f in G[st]["floor"]]
CUTS = [B(o["x"], o["z"], (o["y"][0] + GY, o["y"][1] + GY)) for o in SG.get("wall_openings", [])]   # SpecGreybox.CutWallOpenings
STAIRS = [("main", S["stair"], 0.0), ("attic", S["attic_stair"], 0.0)] + ([("service", SG["stair"], GY)] if SG.get("stair") else [])
SOLIDS = [B(b["x"], b["z"], (b["y"][0] + fy, b["y"][1] + fy)) for _, s, fy in STAIRS for b in s["boxes"] if b["kind"] in ("step", "landing")]


def inside(b, x, z, y, e=0.0):
    return b[0] - e <= x <= b[1] + e and b[2] - e <= z <= b[3] + e and b[4] - e <= y <= b[5] + e


def wall_at(x, z, y):
    return any(inside(w, x, z, y) for w in WALLS) and not any(c[0] < x < c[1] and c[2] < z < c[3] and c[4] < y < c[5] for c in CUTS)


def solid_at(x, z, y):
    """Inside a wall or a stair's step/landing (strictly: a point on a face is outside)."""
    return any(b[0] + 1e-4 < x < b[1] - 1e-4 and b[2] + 1e-4 < z < b[3] - 1e-4 and b[4] + 1e-4 < y < b[5] - 1e-4 for b in WALLS + SOLIDS)


def overlap(a, b, shrink=0.0):
    return all(a[2 * i] + shrink < b[2 * i + 1] and b[2 * i] < a[2 * i + 1] - shrink for i in range(3))


def point_in_poly(pts, x, z):
    c = False
    for (x0, z0), (x1, z1) in zip(pts, pts[1:] + pts[:1]):
        if (z0 > z) != (z1 > z) and x < x0 + (z - z0) * (x1 - x0) / (z1 - z0):
            c = not c
    return c


def finish_of(st, name, papered):
    """(wainscot h, baseboard) per room: SpecGreybox.Storey's finishOf (papered rooms: foyer.json; painted: finishes.json)."""
    if name in papered:
        return (FOY.get("wainscot_by_space", {}).get(name, FOY["wainscot_m"]), 0.14)
    if name in FIN:
        return (FIN[name]["wainscot_m"], FIN[name].get("baseboard_m", 0.14))
    return None   # kitchen rooms (paper, no wainscot) and grey-box rooms: no trim


ROOMS = []   # (storey, floor y, name, poly, finish)
for st, fy, papered in STOREYS:
    for r in G[st]["rooms"]:
        ROOMS.append((st, fy, r["name"], [tuple(p) for p in r["poly"]], finish_of(st, r["name"], papered)))


def room_at(x, z, y):
    best = None
    for st, fy, name, poly, fin in ROOMS:
        if abs(y - fy) < 0.3 and point_in_poly(poly, x, z):
            best = (name, fin)
    return best


# ------------------------------------------------------------------------------------------------ faces and supports
# a face key: (axis, c, n). axis "x": the face runs along x in the plane spec z = c; "z": along spec z in the plane x = c. n: the
# direction (+-1, along the plane's normal axis) from the wall into the space the face looks into.
def at(key, s, off):
    axis, c, n = key
    return (s, c + n * off) if axis == "x" else (c + n * off, s)


def mounted_pieces():
    """Casings, stools and prop doors as SpecGreybox.Storey makes them (world boxes in spec x/z), minus those its Trim() drops (a piece
    whose volume, 2 mm in, meets a wall or floor built so far: upstairs first, then the ground). Each knows its face key."""
    out, walls_so_far, floors_so_far = [], [], []
    arch_models = {"foyer|rear_passage"}   # SpecGreybox.Arch.cs ArchModels: a generated arch draws its own (no) casing
    for st, fy, _ in STOREYS:
        walls_so_far += [B(w["x"], w["z"], (w["y"][0] + fy, w["y"][1] + fy)) for w in G[st]["walls"]]
        floors_so_far += [B(f["x"], f["z"], (f["y"][0] + fy, f["y"][1] + fy)) for f in G[st]["floor"]]
        for o in G[st]["openings"]:
            k, ax, c, lo, hi = o["kind"], o["axis"], o["c"], o["lo"], o["hi"]
            faxis = "x" if ax == "z" else "z"          # an opening on a z = c wall: its faces run along x

            def piece(kind, f0, f1, s0, s1, y0, y1, n):
                a, b2 = min(f0, f1), max(f0, f1)
                box = (s0, s1, a, b2, y0 + fy, y1 + fy) if faxis == "x" else (a, b2, s0, s1, y0 + fy, y1 + fy)
                if kind == "casing" and any(overlap(box, w, 0.002) for w in walls_so_far + floors_so_far):
                    return                             # Trim(): never into a wall or floor
                out.append((kind, (faxis, round(c + (HALF if n > 0 else -HALF) * 1, 4), n), box))
            if k == "door" or (k == "arch" and o.get("cased")):
                for n in (-1, 1):
                    f0 = c + n * HALF; f1 = f0 + n * CASING_PROUD; head = o["height"]
                    piece("casing", f0, f1, lo - CASING_W, lo, 0, head + CASING_W, n)
                    piece("casing", f0, f1, hi, hi + CASING_W, 0, head + CASING_W, n)
                    piece("casing", f0, f1, lo - CASING_W, hi + CASING_W, head, head + CASING_W, n)
            elif k == "arch" and o.get("spring") is not None:
                if "|".join(sorted(o["between"])) in arch_models:
                    continue
                n = 1 if ax == "z" else -1             # world face wc - h: spec z = c + h on a z wall (z flips), x = c - h on an x wall
                f0 = c + n * HALF; f1 = f0 + n * CASING_PROUD
                piece("casing", f0, f1, lo - CASING_W, lo, 0, o["spring"], n)
                piece("casing", f0, f1, hi, hi + CASING_W, 0, o["spring"], n)
            elif k == "fake_door":
                for n in (-1, 1):
                    f0 = c + n * HALF
                    piece("prop", f0, f0 + n * 0.03, lo, hi, 0, 2.032, n)
            elif k == "window" and not o.get("bare"):
                n = -o["faces"][0]                     # the room's face (faces[0] is the outward side, spec)
                f0 = c + n * HALF; f1 = f0 + n * CASING_PROUD; sill, head = o["sill"], o["head"]
                piece("casing", f0, f1, lo - CASING_W, lo, sill, head + CASING_W, n)
                piece("casing", f0, f1, hi, hi + CASING_W, sill, head + CASING_W, n)
                piece("casing", f0, f1, lo - CASING_W, hi + CASING_W, head, head + CASING_W, n)
                if not o.get("model"):
                    piece("casing", f0, f0 + n * STOOL_PROUD, lo - CASING_W - 0.025, hi + CASING_W + 0.025, sill - STOOL_T, sill, n)
    return out


MOUNTED = mounted_pieces()
OPENING_EDGES = {}   # face line (axis, c) -> s of every opening jamb on it (both faces)
for st, fy, _ in STOREYS:
    for o in G[st]["openings"]:
        ax = "x" if o["axis"] == "z" else "z"
        for n in (-1, 1):
            OPENING_EDGES.setdefault((ax, round(o["c"] + n * HALF, 3)), []).extend([o["lo"], o["hi"]])


class Run:
    """A support's line along one face: pts [(s, y)] ascending in s; label ('room', name, fin) or ('stair', id, lower room, fin);
    corner: for a room edge, (s of its start vertex, +1 convex / -1 reflex, direction of travel) (SpecGreybox's corner rule)."""
    def __init__(self, key, pts, label, corner=None, kind="floor"):
        self.key, self.pts, self.label, self.corner, self.kind = key, sorted(pts), label, corner, kind

    @property
    def s0(self): return self.pts[0][0]

    @property
    def s1(self): return self.pts[-1][0]

    def y(self, s):
        p = self.pts
        if s <= p[0][0]: return p[0][1]
        for (a, ya), (b, yb) in zip(p, p[1:]):
            if a <= s <= b:
                return ya if b - a < EPS else ya + (yb - ya) * (s - a) / (b - a)
        return p[-1][1]


def room_runs():
    runs = []
    for st, fy, name, p, fin in ROOMS:
        if not fin or fin[0] <= 0:
            continue                                   # no wainscot or baseboard: no trim (stair well, kitchen)
        n = len(p); area = sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1] for i in range(n)); sg = math.copysign(1, area)
        def d(i):
            a, b = p[i], p[(i + 1) % n]; L = math.dist(a, b); return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-9 else (0, 0)
        for i in range(n):
            a, b = p[i], p[(i + 1) % n]
            if math.dist(a, b) < 1e-4:
                continue
            t = d(i); ta = d((i - 1) % n); turn = sg * (ta[0] * t[1] - ta[1] * t[0])
            nin = (-sg * t[1], sg * t[0])               # into the room (C#: nOut = (sg*t.y, -sg*t.x))
            if abs(t[1]) < 1e-6:
                key, sa, sb = ("x", round(a[1], 4), round(nin[1])), a[0], b[0]
            elif abs(t[0]) < 1e-6:
                key, sa, sb = ("z", round(a[0], 4), round(nin[0])), a[1], b[1]
            else:
                print(f"trim_faces: {name} edge {i} not axis-aligned: skipped"); continue
            runs.append(Run(key, [(sa, fy), (sb, fy)], ("room", name, fin), (sa, 1 if turn > 1e-3 else -1 if turn < -1e-3 else 0, math.copysign(1, sb - sa))))
    return runs


def stair_runs():
    """Each stair rising from a finished room: its flights' nosing lines and its landings' tops, on every side (a side with no wall
    behind it simply gets no member: the open side)."""
    runs = []
    for sid, s, fy in STAIRS:
        steps = [b for b in s["boxes"] if b["kind"] == "step"]
        if not steps:
            continue
        rise = s["rise_m"]
        b0 = min(steps, key=lambda b: b["y"][1])
        lower = room_at((b0["x"][0] + b0["x"][1]) / 2, (b0["z"][0] + b0["z"][1]) / 2, b0["y"][0] + fy)
        if not lower or not lower[1] or lower[1][0] <= 0.3:
            continue                                   # rises from a room with no wainscot (kitchen, attic): no stair trim
        label = ("stair", sid, lower[0], lower[1])
        flights = {}
        for b in steps:
            flights.setdefault(b["name"].split("_step")[0], []).append(b)
        for fname, st in flights.items():
            st = sorted(st, key=lambda b: b["y"][1])
            if len(st) < 2:
                continue
            cx = [(b["x"][0] + b["x"][1]) / 2 for b in st]; cz = [(b["z"][0] + b["z"][1]) / 2 for b in st]
            along = "x" if abs(cx[-1] - cx[0]) > abs(cz[-1] - cz[0]) else "z"
            up = 1 if (cx if along == "x" else cz)[-1] > (cx if along == "x" else cz)[0] else -1   # rising toward +along?
            lat = "z" if along == "x" else "x"
            if any(abs(b[lat][0] - st[0][lat][0]) > 0.01 or abs(b[lat][1] - st[0][lat][1]) > 0.01 for b in st):
                continue                                # winders: not a straight flight
            front = lambda b: b[along][0] if up > 0 else b[along][1]
            back = lambda b: b[along][1] if up > 0 else b[along][0]
            noses = [(front(b) - up * NOSE, b["y"][1] + fy) for b in st]
            going = abs(st[1][along][0] - st[0][along][0])
            pts = [(noses[0][0] - up * going, noses[0][1] - rise)] + noses + [(back(st[-1]) - up * NOSE, st[-1]["y"][1] + fy + rise)]
            for side in (0, 1):                         # both lateral faces of the flight; normal toward the flight
                c = st[0][lat][side]; n = 1 if side == 0 else -1
                runs.append(Run((along, round(c, 4), n), pts, label, kind="rake"))
        for L in (b for b in s["boxes"] if b["kind"] == "landing"):
            top = L["y"][1] + fy
            for ax, lat in (("x", "z"), ("z", "x")):
                for side in (0, 1):
                    runs.append(Run((ax, round(L[lat][side], 4), 1 if side == 0 else -1), [(L[ax][0], top), (L[ax][1], top)], label, kind="landing"))
    return runs


# ------------------------------------------------------------------------------------------------ merging into chains
def connected(a, b):
    lo, hi = max(a.s0, b.s0), min(a.s1, b.s1)
    if hi < lo:                                         # apart along the face: meet across a gap of at most 3 cm (a nosing)
        if lo - hi > 0.03 + EPS: return False
        l, r = (a, b) if a.s1 <= b.s0 + EPS else (b, a)
        return abs(l.y(l.s1) - r.y(r.s0)) < 0.01
    ss = sorted({lo, hi} | {s for s, _ in a.pts + b.pts if lo <= s <= hi})
    ds = [a.y(s) - b.y(s) for s in ss]
    return any(abs(d) < 0.01 for d in ds) or any(d0 * d1 < 0 for d0, d1 in zip(ds, ds[1:]))


def merge(runs):
    """Connected supports on one face line -> chains: the upper envelope of their lines, each segment labelled by its source."""
    comps, todo = [], list(runs)
    while todo:
        comp = [todo.pop()]; grew = True
        while grew:
            grew = False
            for r in list(todo):
                if any(connected(r, c) for c in comp):
                    comp.append(r); todo.remove(r); grew = True
        comps.append(comp)
    chains = []
    for comp in comps:
        ss = {s for r in comp for s, _ in r.pts}
        for a in comp:                                  # crossings of two supports' lines
            for b in comp:
                if a is b: continue
                for (s0, y0), (s1, y1) in zip(a.pts, a.pts[1:]):
                    if s1 - s0 < EPS: continue
                    d0, d1 = y0 - b.y(s0), y1 - b.y(s1)
                    if d0 * d1 < 0 and max(b.s0, s0) <= min(b.s1, s1):
                        ss.add(s0 + (s1 - s0) * d0 / (d0 - d1))
        ss = sorted(ss)
        def best(s, strict):
            c = [r for r in comp if (r.s0 < s < r.s1 if strict else r.s0 - EPS <= s <= r.s1 + EPS)]
            if not c:                                   # a gap (<= 3 cm): bridge from the left run's end to the right run's start
                l = max((r for r in comp if r.s1 <= s), key=lambda r: r.s1); rr = min((r for r in comp if r.s0 >= s), key=lambda r: r.s0)
                y = l.y(l.s1) + (rr.y(rr.s0) - l.y(l.s1)) * (s - l.s1) / max(rr.s0 - l.s1, EPS)
                return y, (l if l.label[0] == "stair" else rr)
            r = max(c, key=lambda r: (round(r.y(s), 5), r.label[0] == "stair"))
            return r.y(s), r
        pts, segs = [], []
        for s in ss:
            pts.append((s, best(s, False)[0]))
        for s0, s1 in zip(ss, ss[1:]):
            segs.append(best((s0 + s1) / 2, True)[1])
        chains.append({"key": comp[0].key, "pts": pts, "segs": segs, "runs": comp})
    return chains


# ------------------------------------------------------------------------------------------------ members
def members(label):
    """Profiles the house uses (unchanged): (name, bottom(line, surface), top(line), depth from, depth to, check height or None)."""
    if label[0] == "room":
        h, bb = label[2]
        m = [("baseboard", lambda y, sf: y, lambda y: y + bb, 0.0, 0.012)]
        if h > 0.3:
            m.append(("cap", lambda y, sf: y + h - 0.01, lambda y: y + h + 0.03, 0.0, 0.03))
        return m
    h = label[3][0]
    return [("skirt", lambda y, sf: sf, lambda y: y + 0.20, 0.0, 0.022),
            ("panel", lambda y, sf: y + 0.20, lambda y: y + h, 0.0, 0.015),
            ("rail", lambda y, sf: y + h - 0.005, lambda y: y + h + 0.035, 0.015, 0.045)]


def samples(label):
    """Heights above the line the Trim check looks at: each member's middle (the panel's on a flat room wall is the wall's own
    wainscot material)."""
    if label[0] == "room":
        h, bb = label[2]
        return [{"h": round(bb / 2, 3)}] + ([{"h": round((bb + h) / 2, 3), "panel": True}, {"h": round(h + 0.01, 3)}] if h > 0.3 else [])
    h = label[3][0]
    return [{"h": 0.10}, {"h": round((0.20 + h) / 2, 3)}, {"h": round(h + 0.015, 3)}]


def surface(key, s, line_y):
    """The stair's own surface under the line at s, against this face: the highest tread, landing or floor top not above the line."""
    best = -1e9
    for b in SOLIDS + FLOORS:
        x, z = at(key, s, 0.005)
        if b[0] - EPS <= x <= b[1] + EPS and b[2] - EPS <= z <= b[3] + EPS and b[5] <= line_y + 1e-4:
            best = max(best, b[5])
    return best if best > -1e8 else line_y


def window_stool(key, s0, s1, line_y, h):
    """A window model on this face (wall_openings) whose sill is under the cap: (opening name, stool height above the line)."""
    for o in SG.get("wall_openings", []):
        ax = "z" if o["wall"] == "x" else "x"
        if ax != key[0] or abs(o["face"] - key[1]) > 0.01:
            continue
        sill = o["y"][0] + GY
        span = o["z"] if ax == "z" else o["x"]
        if span[0] < s1 and span[1] > s0 and sill - line_y < h:
            return o["name"], sill - line_y
    return None


def blocked(key, s, y0, y1, d1):
    """A mounted piece (casing, stool, prop door) in front of this face within the member's depth + 2 cm, at its height."""
    for kind, mk, box in MOUNTED:
        if mk[0] != key[0] or abs(mk[1] - key[1]) > 0.005 or mk[2] != key[2]:
            continue
        sa, sb = (box[0], box[1]) if key[0] == "x" else (box[2], box[3])
        if sa < s < sb and box[4] < y1 - 0.002 and box[5] > y0 + 0.002:
            fa, fb = (box[2], box[3]) if key[0] == "x" else (box[0], box[1])
            lo, hi = sorted((key[1], key[1] + key[2] * (d1 + REACH)))
            if fa < hi and fb > lo:
                return True
    return False


def lay(key, line, sfun, lo_s, hi_s, mem, corner_start=None):
    """Intervals of [lo_s, hi_s] where member mem can stand: a wall behind it at its middle, nothing solid in front of it, nothing
    mounted on the wall there. 1 cm samples, edges found by bisection to 0.1 mm."""
    name, bot, top, d0, d1 = mem
    def ok(s):
        y = line(s); yb, yt = bot(y, sfun(s, y)), top(y); ym = (yb + yt) / 2
        x, z = at(key, s, -0.004); xf, zf = at(key, s, d1 + 0.005)
        return wall_at(x, z, ym) and not solid_at(xf, zf, ym) and not blocked(key, s, yb, yt, d1)
    def edge(a, b):                                     # ok(a) != ok(b)
        fa = ok(a)
        for _ in range(14):
            m = (a + b) / 2
            if ok(m) == fa: a = m
            else: b = m
        return (a + b) / 2
    n = max(2, int(math.ceil((hi_s - lo_s) / 0.01)))
    xs = [lo_s + (hi_s - lo_s) * (i + 0.5) / n for i in range(n)]
    out, cur = [], None
    prev = None
    for s in xs:
        v = ok(s)
        if v and cur is None:
            cur = lo_s if prev is None else edge(prev, s)
        if not v and cur is not None:
            out.append([cur, edge(prev, s)]); cur = None
        prev = s
    if cur is not None:
        out.append([cur, hi_s])
    return [iv for iv in out if iv[1] - iv[0] >= 0.02]


def open_spans(key, line, s0, s1):
    """Where the chain's face is open at baseboard height (a wall behind, nothing solid or mounted in front): its terminations are
    the ends of these spans (openings, casings, corners)."""
    mem = ("probe", lambda y, sf: y, lambda y: y + 0.14, 0.0, 0.012)
    return lay(key, line, lambda s, y: y, s0, s1, mem)


def build(chains):
    out_runs, strips = [], []
    for ch in chains:
        key, pts, segs = ch["key"], ch["pts"], ch["segs"]
        line = Run(key, pts, None).y
        for a, b in open_spans(key, line, pts[0][0], pts[-1][0]):
            # segments inside this open span, labelled; a stair's finish is carried along the floor of the room it rises from
            part = [(max(s0, a), min(s1, b), sg) for (s0, _), (s1, _), sg in zip(pts, pts[1:], segs) if min(s1, b) - max(s0, a) > EPS]
            lows = {sg.label[2]: sg.label for _, _, sg in part if sg.label[0] == "stair"}
            pieces = []
            for s0, s1, sg in part:
                lab = lows.get(sg.label[1], sg.label) if sg.label[0] == "room" else sg.label
                if pieces and pieces[-1]["label"] == lab:
                    pieces[-1]["s1"] = s1; pieces[-1]["srcs"].append(sg)
                else:
                    pieces.append({"label": lab, "s0": s0, "s1": s1, "srcs": [sg]})
            for pc in pieces:
                lab = pc["label"]
                fin_h = lab[2][0] if lab[0] == "room" else lab[3][0]
                sfun = (lambda s, y, key=key: surface(key, s, y)) if lab[0] == "stair" else (lambda s, y: y)
                corner = next((sg.corner for sg in pc["srcs"] if sg.corner and pc["s0"] - 0.03 <= sg.corner[0] <= pc["s1"] + 0.03), None)
                rec = {"key": key, "label": lab, "s0": pc["s0"], "s1": pc["s1"], "samples": samples(lab), "by": None,
                       "pts": [(pc["s0"], line(pc["s0"]))] + [(s, y) for s, y in pts if pc["s0"] < s < pc["s1"]] + [(pc["s1"], line(pc["s1"]))]}
                out_runs.append(rec)
                stool = window_stool(key, pc["s0"], pc["s1"], line(pc["s0"]), fin_h + 0.03)
                if stool:                                # the window model panels this wall to its stool: checked, not laid
                    rec["by"], rec["samples"] = stool[0], [{"h": 0.10}, {"h": round(stool[1] - 0.045, 3)}]
                    continue
                for mem in members(lab):
                    d = mem[4]
                    for iv in lay(key, line, sfun, pc["s0"], pc["s1"], mem):
                        if corner and corner[1] != 0 and abs(iv[0 if corner[2] > 0 else 1] - corner[0]) < 2e-3 and real_corner(key, corner, line(corner[0])):
                            # SpecGreybox's corner rule at a room edge's start vertex: convex -> start past the depth, reflex -> reach back
                            if corner[2] > 0: iv[0] = corner[0] + corner[1] * d
                            else: iv[1] = corner[0] - corner[1] * d
                        strips.append(strip(key, line, sfun, iv, mem, lab, pts))
    return out_runs, strips


def real_corner(key, corner, y0):
    """The polygon vertex is a wall corner: convex -> a wall stands across the line just before it (inside corner); reflex -> the wall
    behind turns away there (outside corner). At an open boundary (the hall's edge at the stair) the run simply continues."""
    s, kind, dirn = corner
    before, after = s - dirn * 0.005, s + dirn * 0.005
    if kind > 0:
        return solid_at(*at(key, before, 0.02), y0 + 0.07)
    return not wall_at(*at(key, before, -0.004), y0 + 0.07) and wall_at(*at(key, after, -0.004), y0 + 0.07)


def strip(key, line, sfun, iv, mem, lab, pts):
    """Stations [s, bottom, top] at the line's vertices and, for the skirt, at every edge of the surface under it (a riser: two
    bottoms at one s, so the board is scribed to the treads)."""
    name, bot, top, d0, d1 = mem
    s0, s1 = iv
    xs = {s0, s1} | {s for s, _ in pts if s0 < s < s1}
    if name == "skirt":
        xs |= {e for b in SOLIDS + FLOORS for e in ((b[0], b[1]) if key[0] == "x" else (b[2], b[3])) if s0 < e < s1}
    xs = sorted({round(x, 6) for x in xs}); st = []
    for i, s in enumerate(xs):
        y = line(s)
        if name == "skirt":
            bl, br = bot(y, sfun(max(s - 2e-4, s0), y)), bot(y, sfun(min(s + 2e-4, s1), y))
            st.append([s, bl, top(y)])
            if abs(bl - br) > 1e-4:
                st.append([s, br, top(y)])
        else:
            st.append([s, bot(y, None), top(y)])
    flat = all(abs(p[1] - st[0][1]) < 1e-5 and abs(p[2] - st[0][2]) < 1e-5 for p in st)
    return {"name": name, "key": key, "d": [d0, d1], "st": [st[0], st[-1]] if flat else st, "flat": flat, "label": lab}


def jamb(key, s):
    """The run ends on the jamb of an opening in the crossing wall (the arch's or rail's return): the opening's plane is at s and one of
    its edges is on this face's plane."""
    other = "z" if key[0] == "x" else "x"
    return any(ax == other and abs(c - s) < 0.08 and any(abs(e - key[1]) < 0.08 for e in es) for (ax, c), es in OPENING_EDGES.items())


def terminations(out_runs, strips, problems):
    """Every run end: a corner (a wall in front of the line just past it), an opening (a jamb or a mounted piece at it, or no wall
    behind next to a jamb), another run (one ends where another starts, same face or round a corner), or the stair's own open edge."""
    counts = {}
    ends_by_face = {}
    for r in out_runs:
        ends_by_face.setdefault((r["key"][0], r["key"][1]), []).append(r)
    for r in out_runs:
        key = r["key"]; line = Run(key, r["pts"], None).y
        for side, s in (("start", r["s0"]), ("end", r["s1"])):
            out = -1 if side == "start" else 1
            y = line(s) + 0.10
            kind = None
            x, z = at(key, s + out * 0.01, 0.02)
            xb, zb = at(key, s + out * 0.01, -0.004)
            if solid_at(x, z, y):
                kind = "corner"
            elif any(abs(e - s) < 0.08 for e in OPENING_EDGES.get((key[0], round(key[1], 3)), [])) or jamb(key, s) or \
                    any(mk[0] == key[0] and abs(mk[1] - key[1]) < 0.01 and ((box[0] if key[0] == "x" else box[2]) - 0.01 <= s <= (box[1] if key[0] == "x" else box[3]) + 0.01)
                        for _, mk, box in MOUNTED):
                kind = "opening"
            elif any(o is not r and o["key"] == key and (abs(o["s0"] - s) < 0.031 or abs(o["s1"] - s) < 0.031) for o in out_runs):
                kind = "run"
            elif not wall_at(xb, zb, y):
                # the wall turns away (an outside corner: the next face carries on round it) or ends at an open boundary
                x2, z2 = at(key, s + out * 0.01, -0.08)
                kind = "outside-corner" if any(abs(((o["key"][1]) - (s))) < 0.15 and o["key"][0] != key[0] for o in out_runs) else "wall-end"
            else:
                kind = "free"
            counts[kind] = counts.get(kind, 0) + 1
            r.setdefault("ends", []).append(kind)
            if kind in ("free", "wall-end"):
                problems.append(f"{kind:8s} {side} of {r['label'][1]} {r['label'][0]} run on {key} at s {s:.3f}")
    return counts


# ------------------------------------------------------------------------------------------------ output (Unity world)
def world_key(key):
    axis, c, n = key
    return (axis, -c, -n) if axis == "x" else (axis, c, n)   # a run along x: its plane spec z = c is world z = -c


def world_s(key, s):
    return s if key[0] == "x" else -s


def lab_str(lab):
    return f"{lab[0]}:{lab[1]}" if lab[0] == "room" else f"stair:{lab[1]}:{lab[2]}"


def write():
    byface = {}
    for r in room_runs() + stair_runs():
        byface.setdefault(r.key, []).append(r)
    chains = [c for k in sorted(byface, key=str) for c in merge(byface[k])]
    out_runs, strips = build(chains)
    problems = []
    ends = terminations(out_runs, strips, problems)
    J = {"note": "Generated by tools/house/trim_faces.py (HOUSE-KERNEL step 1): do not edit. runs = the visible faces the Trim check samples; "
                 "strips = the trim SpecGreybox lays when TrimFromFaces (world coordinates; axis = the run's direction; c = the face plane; "
                 "n = the face's normal; st = stations [s, bottom, top]; d = depth off the face).",
         "inputs": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS},
         "runs": [], "strips": [], "ends": ends, "problems": problems}
    for r in out_runs:
        ax, c, n = world_key(r["key"])
        pts = sorted([[round(world_s(r["key"], s), 4), round(y, 4)] for s, y in r["pts"]])
        J["runs"].append({"room": lab_str(r["label"]), "axis": ax, "c": round(c, 4), "n": n, "pts": pts, "samples": r["samples"],
                          "by": r["by"], "ends": r.get("ends", [])})
    for sp in strips:
        ax, c, n = world_key(sp["key"])
        st = [[round(world_s(sp["key"], s), 4), round(b, 4), round(t, 4)] for s, b, t in sp["st"]]
        if sp["key"][0] == "z": st = st[::-1]
        J["strips"].append({"name": sp["name"], "room": lab_str(sp["label"]), "axis": ax, "c": round(c, 4), "n": n, "d": sp["d"], "flat": sp["flat"], "st": st})
    return J


def selftest(J):
    """The model's own invariants (cheap, before any Unity build): no free run end; every stair/landing run continuous (one strip per
    member from end to end: no joint inside a run can open); a run that starts where another ends on its face shares the point."""
    bad = list(J["problems"])
    for r in J["runs"]:
        if not r["room"].startswith("stair") or r["by"]:
            continue
        lo, hi = r["pts"][0][0], r["pts"][-1][0]
        for name in ("skirt", "panel", "rail"):
            mine = [s for s in J["strips"] if s["name"] == name and s["axis"] == r["axis"] and abs(s["c"] - r["c"]) < 1e-3 and s["n"] == r["n"]
                    and s["st"][0][0] <= hi + 1e-3 and s["st"][-1][0] >= lo - 1e-3]
            if len(mine) != 1 or mine[0]["st"][0][0] > lo + 1e-3 or mine[0]["st"][-1][0] < hi - 1e-3:
                bad.append(f"{name} on the {r['room']} run {r['axis']} {r['c']} is not one piece from {lo} to {hi}: {[(m['st'][0][0], m['st'][-1][0]) for m in mine]}")
    for s in J["strips"]:
        if any(t[2] < t[1] - 1e-6 for t in s["st"]) or any(b[0] < a[0] - 1e-6 for a, b in zip(s["st"], s["st"][1:])):
            bad.append(f"{s['name']} strip on {s['axis']} {s['c']} has a station out of order or upside down")
    return bad


if __name__ == "__main__":
    J = write()
    bad = selftest(J)
    if "--check" in sys.argv:
        old = json.loads(OUT.read_text()) if OUT.exists() else {}
        stale = old.get("inputs") != J["inputs"] or old.get("strips") != J["strips"] or old.get("runs") != J["runs"]
        print("spec/trim_faces.json " + ("STALE: run python3 tools/house/trim_faces.py" if stale else "up to date"))
        for b in bad: print("FAIL", b)
        sys.exit(1 if stale or bad else 0)
    OUT.write_text(json.dumps(J, indent=0) + "\n")
    print(f"{len(J['runs'])} runs, {len(J['strips'])} strips ({sum(not s['flat'] for s in J['strips'])} raked), ends {J['ends']}")
    for b in bad: print("FAIL", b)
    sys.exit(1 if bad else 0)
