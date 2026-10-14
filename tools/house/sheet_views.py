"""Per-room comparison sheet: matching camera pairs in the September model (IntactHouseReference, native units,
0.774 m/unit) and the latest grey-box (Greybox_Upstairs, metres). Render-only; reads the spec, writes view lists.
  (a) just inside the room's main doorway looking at its far corner; (b) from that far corner looking back at the doorway.
  Eye 1.30 m above that room's floor, aim point 1.0 m above it, vfov 60, 1920x1080, insets 0.5 m from walls.
Grey-box doors/corners come from spec/house_spec*.json (world x = spec x, z = -spec z, ground floor y = floor_y_m).
September rooms are hand-identified from plan sections (tools/survey/glb_section.py) and checked render by render.
usage: uv run python tools/house/sheet_views.py   then RenderViews twice (see cameras.json "render").
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "spec/captures/sheet"
EYE, AIM, INSET, VFOV = 1.30, 1.0, 0.5, 60
M = 0.774                       # September model metres per native unit
UP_F, GR_F = 5.22, 1.31         # September floor heights (native)


def lr(inward, p, q):
    """'L' or 'R': side of point q relative to p when facing along inward (Unity left-handed, y up: right = (fz, -fx))."""
    rx, rz = inward[1], -inward[0]
    return "R" if (q[0] - p[0]) * rx + (q[1] - p[1]) * rz > 0 else "L"


def pair(door, inward, corner, toward, floor_y, unit):
    """door/corner/toward in world plan (x, z); unit = metres per world unit. Returns (a, b) view dicts."""
    k = INSET / unit
    a_pos = (door[0] + inward[0] * k, door[1] + inward[1] * k)
    c_pos = (corner[0] + math.copysign(k, toward[0] - corner[0]), corner[1] + math.copysign(k, toward[1] - corner[1]))
    y_eye, y_aim = floor_y + EYE / unit, floor_y + AIM / unit
    r = lambda v: round(v, 3)
    a = {"pos": [r(a_pos[0]), r(y_eye), r(a_pos[1])], "look_at": [r(corner[0]), r(y_aim), r(corner[1])]}
    b = {"pos": [r(c_pos[0]), r(y_eye), r(c_pos[1])], "look_at": [r(door[0]), r(y_aim), r(door[1])]}
    return a, b


# ---------- grey-box from the spec ----------
def grey_rooms():
    out = {}
    for f in ("house_spec.json", "house_spec.ground.json"):
        s = json.loads((ROOT / "spec" / f).read_text())
        fy = s["floor_y_m"]
        spaces = {sp["name"]: [(p[0], -p[1]) for p in sp["polygon_xz"]] for sp in s["spaces"]}
        out[f] = (fy, spaces, s["doors"])
    return out


def grey_door(doors, room, other):
    d = next(d for d in doors if set(d["between"]) == {room, other} and d["kind"] in ("door", "arch", "open"))
    c, lo, hi = d["wall_coord_spec"], *d["span_spec"]
    if d["spec_axis"] == "z":      # wall is the line spec z = c, door spans x
        return ((lo + hi) / 2, -c), "z"
    return (c, -(lo + hi) / 2), "x"


def grey_view(fy, poly, doors, room, other, corner=None):
    (dx, dz), ax = grey_door(doors, room, other)
    cx, cz = sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)
    if ax == "z":
        inward = (0, 1 if cz > dz else -1); door = (dx, dz + 0.07 * inward[1])
    else:
        inward = (1 if cx > dx else -1, 0); door = (dx + 0.07 * inward[0], dz)
    if corner is None:                 # farthest polygon vertex from the door
        corner = max(poly, key=lambda p: math.dist(p, door))
    return door, inward, corner, (cx, cz), fy


GREY = {   # room: (spec file, room, doorway's other side[, explicit corner (world x, z)])
    "parents_bedroom": ("house_spec.json", "parents_bedroom", "hall_end"),
    "parents_bath": ("house_spec.json", "parents_bath", "parents_bedroom"),
    "kevin_jeff_room": ("house_spec.json", "kevin_jeff_room", "hall_end"),
    "girls_room_a": ("house_spec.json", "girls_room_a", "hall_end"),
    "girls_room_b": ("house_spec.json", "girls_room_b", "hall_corridor_south"),
    "hall_bath": ("house_spec.json", "hall_bath", "hall_corridor"),
    "buzz_room": ("house_spec.json", "buzz_room", "hall_corridor"),
    "den": ("house_spec.ground.json", "den", "living_room"),
    "living_room": ("house_spec.ground.json", "living_room", "foyer"),
    "foyer": ("house_spec.ground.json", "foyer", "vestibule"),
    "dining_room": ("house_spec.ground.json", "dining_room", "foyer"),
    "sunroom": ("house_spec.ground.json", "sunroom", "dining_room"),
    "kitchen": ("house_spec.ground.json", "kitchen", "dining_room"),
    "vestibule": ("house_spec.ground.json", "vestibule", "foyer"),
}


# ---------- September model (native units, Unity x = Blender X, Unity z = Blender Y) ----------
# room: (door centre (x, z) on the room-side face, inward unit vector, far corner (x, z) inner faces, room centre, floor y)
# Same functional doorway and corner as the grey-box (the house is rotated: grey +x (front) = Sept -z, grey +z = Sept +x).
SEPT_NOTE = {
    "parents_bath": "Sept bath is L-shaped; corner taken in the main room, the tub alcove (X 10.86..12.5 native) is to the right of it",
    "kitchen": "doorway differs: Sept's foyer-end dining door opens into the back-stair bay, which is open to the kitchen/breakfast room (the grey-box door also lands beside the back stair); Sept has a second, direct dining->kitchen door at X 9.0",
    "living_room": "looks broken in Sept: a loose dark door-leaf-like panel stands near the far corner and partly blocks view b",
    "hall_bath": "Sept bath door opens off a small hall bay that also serves Buzz's door",
    "buzz_room": "Sept layout is turned 90 deg relative to Marina's (DEVIATIONS 'Old model'); doorway and corner picked by function (door at the shelves-wall corner, far corner at the front window / desk wall)",
    "foyer": "Sept foyer's rear-north corner is the closet front at native z 9.12 (the closet behind it is not the foyer)",
    "girls_room_a": "room not present in the September model: its position (rear, at the hall end beside the parents' bath) is the back-stair hall there. The only other bedroom-like space, the upper west wing entered through girls_room_b, is rendered separately as upper_west_wing",
    "parents_bedroom": "view b stands beside the four-poster bed, which fills the near foreground",
}
SEPT = {
    "parents_bedroom": ((8.91, 3.31), (1, 0), (14.80, 7.29), (11.8, 3.2), UP_F),
    "parents_bath": ((10.05, 7.46), (0, 1), (10.86, 10.77), (9.6, 9.1), UP_F),   # main room; tub alcove X 10.86..12.5 beyond
    "kevin_jeff_room": ((5.94, 2.01), (0, -1), (9.86, -2.30), (7.4, -0.1), UP_F),
    "girls_room_a": None,   # no counterpart: that spot (rear, hall end, by the parents' bath) is the back-stair hall here
    "girls_room_b": ((-2.29, 4.67), (0, 1), (-6.09, 10.77), (-3.6, 7.7), UP_F),
    "hall_bath": ((-0.11, -0.04), (0, -1), (4.35, -2.30), (1.7, -1.2), UP_F),
    "buzz_room": ((-1.16, 0.98), (-1, 0), (-6.09, -2.30), (-3.6, -0.2), UP_F),
    "den": ((-6.28, 1.36), (-1, 0), (-11.03, 7.98), (-8.6, 3.5), GR_F),
    "living_room": ((-1.16, 1.36), (-1, 0), (-6.09, 10.77), (-3.6, 4.2), GR_F),
    "foyer": ((1.98, 0.2), (0, 1), (4.73, 9.12), (1.9, 5.0), GR_F),
    "dining_room": ((5.10, 1.36), (1, 0), (9.86, 7.29), (7.5, 2.5), GR_F),
    "sunroom": ((9.86, 1.36), (1, 0), (14.80, 7.29), (12.3, 3.2), GR_F),
    "kitchen": ((5.74, 7.46), (0, 1), (15.56, 17.92), (11.0, 12.5), GR_F),
    "vestibule": ((1.98, -0.04), (0, -1), (-0.97, -2.30), (1.9, -1.2), GR_F),
}

def view(room, model, v, pos, look, note=""):
    return {"name": f"../sheet/{room}-{model}-{v}", "room": room, "model": model, "view": v,
            "pos": [round(c, 3) for c in pos], "look_at": [round(c, 3) for c in look], "vfov": VFOV, "note": note}


def build():
    g = grey_rooms()
    views = []
    for name, (f, room, other, *cn) in GREY.items():
        fy, spaces, doors = g[f]
        door, inward, corner, cen, fy = grey_view(fy, spaces[room], doors, room, other, cn[0] if cn else None)
        a, b = pair(door, inward, corner, cen, fy, 1.0)
        side = lr(inward, door, corner)
        views += [view(name, "latest", "a", a["pos"], a["look_at"], f"doorway to {other}; far corner on the {side} entering"),
                  view(name, "latest", "b", b["pos"], b["look_at"], f"far corner ({side}) back to the doorway to {other}")]
        extra = ("; " + SEPT_NOTE[name]) if name in SEPT_NOTE else ""
        if SEPT[name] is None:
            views += [dict(room=name, model="sept", view=v, note=SEPT_NOTE[name], rendered=False) for v in "ab"]
            continue
        sd, si, sc, scen, sf = SEPT[name]
        a, b = pair(sd, si, sc, scen, sf, M)
        views += [view(name, "sept", "a", a["pos"], a["look_at"], f"same functional doorway; far corner on the {lr(si, sd, sc)} entering" + extra),
                  view(name, "sept", "b", b["pos"], b["look_at"], "far corner back to the doorway" + extra)]
    for v in SPECIAL:
        views.append(view(*v))
    return views


E, A = EYE / M, AIM / M   # September eye / aim heights in native units
GF, UF = -2.535, 0.0      # grey-box floor heights
SPECIAL = [
    # main upstairs hall, end to end: parents' door end -> attic door end, and back
    ("hall_corridor", "latest", "a", (6.06, UF + EYE, -5.97), (6.49, UF + AIM, -13.52), "from the parents'-door end (hall_end) looking along the hall to the attic door"),
    ("hall_corridor", "latest", "b", (6.49, UF + EYE, -13.02), (6.06, UF + AIM, -5.47), "from the attic-door end looking back to the parents' door"),
    ("hall_corridor", "sept", "a", (8.91 - INSET / M, UP_F + E, 3.31), (-3.21, UP_F + A, 3.31), "from the parents'-door end looking along the hall to the attic door"),
    ("hall_corridor", "sept", "b", (-3.21 + INSET / M, UP_F + E, 3.31), (8.91, UP_F + A, 3.31), "from the attic-door end looking back to the parents' door"),
    # main stair: 1.7 m in front of the first riser on the flight centreline looking at the landing; and from the landing down the flight
    ("main_stair", "latest", "a", (4.472 + 1.7, GF + EYE, -10.801), (0.79, -0.338 + AIM, -10.801), "foyer, 1.7 m before the first riser, looking up flight 1 to the half landing"),
    ("main_stair", "latest", "b", (0.79, -0.338 + EYE, -10.801), (4.472, GF + AIM, -10.801), "half landing (2 risers below the upper floor) looking down flight 1"),
    ("main_stair", "sept", "a", (0.115, GR_F + E, 4.15 - 1.7 / M), (0.115, 4.45 + A, 9.42), "foyer, 1.7 m before the first riser, looking up flight 1 to the half landing"),
    ("main_stair", "sept", "b", (0.115, 4.45 + E, 9.42), (0.115, GR_F + A, 4.15), "half landing (4 risers below the upper floor here) looking down flight 1"),
    # September only
    # the attic stair rises west from the hall's west end; its top is at native x -8.85
    ("attic", "sept", "a", (-9.2, 8.55 + E, 3.3), (5.0, 8.55 + A, 9.0), "top of the attic stair, turned to look east into the attic at its far (rear, east-partition) corner. Grey-box: room not present (it stops at the attic-stair door)"),
    ("attic", "sept", "b", (5.0 - INSET / M, 8.55 + E, 9.0 - INSET / M), (-9.2, 8.55 + A, 3.3), "far corner back to the attic stair top. Grey-box: room not present"),
    ("upper_west_wing", "sept", "a", (-6.3 - INSET / M, UP_F + E, 6.43), (-11.03, UP_F + A, -0.91), "Sept only: west-wing room over the den, entered through girls_room_b; possible stand-in for girls_room_a but not where Marina's girls_room_a is"),
    ("upper_west_wing", "sept", "b", (-11.03 + INSET / M, UP_F + E, -0.91 + INSET / M), (-6.3, UP_F + A, 6.43), "Sept only: far corner back to the door from girls_room_b"),
    ("basement", "sept", "a", (5.6, -2.23 + E, 10.0), (-6.0, -2.23 + A, -2.0), "near the foot of the basement stair looking across the basement to the front-west. Grey-box: room not present"),
    ("basement", "sept", "b", (3.0, -2.23 + E, 4.0), (3.0, -2.23 + A, -6.0), "looking straight at the front perimeter: there is no perimeter wall, the crawl space is open to the snow outside. Grey-box: room not present"),
]


if __name__ == "__main__":
    views = build()
    OUT.mkdir(parents=True, exist_ok=True)
    rooms = {v["room"] for v in views}
    for r in sorted(rooms):          # rooms with no grey-box counterpart
        if not any(v["room"] == r and v["model"] == "latest" for v in views):
            views += [dict(room=r, model="latest", view=x, note="room not present in this model", rendered=False) for x in "ab"]
    for v in views:
        if "pos" in v:
            v["file"] = f"{v['room']}-{v['model']}-{v['view']}.png"
    for m in ("sept", "latest"):
        (OUT / f"views-{m}.json").write_text(json.dumps([v for v in views if v["model"] == m and "pos" in v], indent=1))
    meta = {"note": "Per-room matched cameras. pos/look_at are Unity world coordinates of each model's scene "
                    "(sept: IntactHouseReference, native units, 0.774 m/unit; latest: Greybox_Upstairs, metres). "
                    "Eye 1.30 m above the room floor, aim 1.0 m above it, vfov 60, 1920x1080, 0.5 m insets. "
                    "Lighting: render-only camera fill light + fixed exposure (RenderViews -fill 3000 -ev 7.5), nothing saved.",
            "render": ["Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderViews -quit -logFile - "
                       f"-scene {sc} -views $PWD/spec/captures/sheet/views-{m}.json -fill 3000 -ev 7.5"
                       for sc, m in (("IntactHouseReference", "sept"), ("Greybox_Upstairs", "latest"))],
            "views": sorted(({k: v[k] for k in v if k != "name"} for v in views), key=lambda v: (v["room"], v["model"], v["view"]))}
    (OUT / "cameras.json").write_text(json.dumps(meta, indent=1))
    print(len(views), "entries")
