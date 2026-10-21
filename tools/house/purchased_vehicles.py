"""The film's police cruisers and the bandits' van from the user's Sketchfab downloads (CC-BY 4.0, CREDITS.md), Oct 20 2026.

  police  "1987 Chevrolet Caprice Classic (police package)" by Timmy turner Gamers: repainted to the Winnetka livery of film
          11574-11636 (navy, light belt stripe with POLICE on the front fender, the shield on the front door), the source's single
          bar housing replaced by the film's chrome bar (two tall MARS beacons, two round flashers, a siren speaker; red left + blue right by the user's choice, Oct 20: the film's is all red),
          head and tail lamps emissive (the cars are only present at night). Beacon_* nodes: Scripts/PoliceLights.cs.
  van     "Dodge Ram Van (Mk3) Passenger Van" by Nieve5677: the cargo-side glass blanked into body panels, the film's ladder rack and
          roof clutter added (6830), the Oh-Kay Plumbing & Heating livery (6830 passenger side, 3299/5696 driver side), RAM badge.
Both are fitted to period dimensions (DIMS) by a piecewise stretch along the length that keeps the wheels round: the wheel zones
scale with the cross-section, the wheelbase span and the overhangs take up the rest (sources: Roblox-era proportions).
Frame: Blender Z up, nose +Y (= spec +z, nb_life's prototype heading), origin at the ground under the body centre, metres.
Nodes per GLB: <Kind>_LOD0/_LOD1/_LOD2 (one mesh each, a submesh per VEH_* material), police also Beacon_L/R, Flasher_L/R.
Materials VEH_*: plain glTF PBR here; spec/vehicles.json "materials" carries the HDRP Lit settings (clear coat, glass, emission).

  uv run --with numpy --with pillow python -I tools/house/purchased_vehicles.py [police van sedan]   # prep -> textures -> build -> previews -> check
  python3 tools/house/purchased_vehicles.py --check                                                   # the hook's contract on the last build
Sources: sfm-work/purchased/vehicles/*.glb (copies of ~/Downloads, gitignored). Output: unity/HomeAlone/Assets/Purchased/Vehicles
(gitignored), stats + previews in sfm-work/purchased/vehicles/work.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/purchased/vehicles"
WORK = SRC / "work"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/Vehicles"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
GLB = {"police": SRC / "1987_chevrolet_caprice_classic_police_package.glb", "van": SRC / "dodge_ram_van_mk3_passenger_van.glb"}
GLB["sedan"] = GLB["police"]   # nb_life's parked blue sedan (film 1888): the same Caprice, plain paint, no bar
KIND = {"police": "Car_CapricePolice", "van": "Car_RamVan", "sedan": "Car_Caprice"}
# period dimensions (m): 1987-90 Caprice sedan 116.0 in WB, 212.2 in long, 75.4 in wide; Ram Van B250 127.6 in WB, 196.9 in, 79.8 in
DIMS = {"police": {"wb": 2.946, "len": 5.390, "width": 1.915}, "van": {"wb": 3.241, "len": 5.001, "width": 2.027}}
DIMS["sedan"] = DIMS["police"]
TRIS = {"LOD0": 36000, "LOD1": 10000, "LOD2": 2500}
TEX = 2048
SIDE_H = 900           # atlas rows per side; the bottom strip (TEX - 2 * SIDE_H) holds front | rear | top
H_M = 2.25             # metres of height a side region spans
FRONT_Z = (0.3, 1.6)   # metres of height the front / rear regions span

# film colours, linear-ish sRGB picked by eye from the frames (night grade lifts navy; van sampled in daylight 6830)
POLICE_NAVY = (24, 30, 58)
POLICE_STRIPE = (196, 200, 204)
VAN_BLUE = (100, 122, 136)   # 6830 side panels (69,86,93) and (53,70,79) lifted by the snow beside it (168 -> albedo 0.8): a grey blue
SEDAN_BLUE = (62, 88, 132)   # 1888: a mid-blue sedan at our kerb (shade by eye, distant)


# ------------------------------------------------------------------ the atlas mapping (shared by the texture painter and Blender)
def atlas_px(region, a, b, L):
    """(region, coords) -> pixel (x, y) in the TEX atlas, y down. side_r (+X, passenger): a = y (nose right), b = z;
    side_l (-X, driver): a = y (nose left), b = z; front / rear: a = x, b = z; top: a = x, b = y."""
    if region in ("side_r", "side_l"):
        u = (a + L / 2) / L if region == "side_r" else (L / 2 - a) / L
        return u * TEX, (0 if region == "side_r" else SIDE_H) + (1 - b / H_M) * SIDE_H
    strip = TEX - 2 * SIDE_H; w = TEX / 3; x0 = {"front": 0, "rear": w, "top": 2 * w}[region]
    if region == "top":
        return x0 + (a / 2.4 + 0.5) * w, 2 * SIDE_H + (0.5 - b / L) * strip
    t = (b - FRONT_Z[0]) / (FRONT_Z[1] - FRONT_Z[0])
    sgn = 1 if region == "rear" else -1   # front seen from +Y looking -Y: viewer's right is -X
    return x0 + (sgn * a / 2.4 + 0.5) * w, 2 * SIDE_H + (1 - t) * strip


# ------------------------------------------------------------------ Blender side
def load(kind):
    """Import, bake transforms, orient, fit DIMS (piecewise along Y, wheels round), origin at the ground centre. Returns (objs, frame)."""
    import bpy
    import numpy as np
    from mathutils import Matrix, Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(GLB[kind]))
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world = Matrix.Identity(4)
    for o in [o for o in bpy.data.objects if o.type != "MESH"]: bpy.data.objects.remove(o)
    if kind in ("police", "sedan"):   # source: Z up, nose +X
        rot = Matrix.Rotation(math.pi / 2, 4, "Z")
    else:                  # source: up -Y (tyres at y 0), front (amber glass) at -Z
        rot = Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Rotation(-math.pi / 2, 4, "X")
    for o in objs: o.data.transform(rot)
    V = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in objs]); mn, mx = V.min(0), V.max(0)
    for o in objs: o.data.transform(Matrix.Translation(Vector((-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, -mn[2]))))
    V = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in objs]); y0, y1 = V[:, 1].min(), V[:, 1].max()
    # axles: the wheel parts' vertices, split at the body centre
    wheel = [o for o in objs if o.data.materials and o.data.materials[0].name in ("Main1Mtl", "tire")]
    W = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in wheel])
    yr_, yf_ = W[W[:, 1] < 0, 1], W[W[:, 1] > 0, 1]
    ar, af = (yr_.min() + yr_.max()) / 2, (yf_.min() + yf_.max()) / 2           # rear axle (-Y), front axle (+Y)
    rad = (W[:, 2].max() - W[:, 2].min()) / 2
    # the body width (paint only; mirrors excluded) sets the cross-section scale
    paint = [o for o in objs if o.data.materials and o.data.materials[0].name in ("Paint7Mtl", "carpaint")]
    P = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in paint])
    s = DIMS[kind]["width"] / (P[:, 0].max() - P[:, 0].min())
    r = rad * 1.25                                                                 # wheel zone half-length (model units)
    wb, L = DIMS[kind]["wb"], DIMS[kind]["len"]
    k_mid = (wb - 2 * r * s) / ((af - r) - (ar + r))
    k_o = (L - wb - 2 * r * s) / ((ar - r - y0) + (y1 - af - r))
    knots_in = [y0, ar - r, ar + r, af - r, af + r, y1]
    seg = [k_o, s, k_mid, s, k_o]
    knots_out = [0.0]
    for a, b, k in zip(knots_in, knots_in[1:], seg): knots_out.append(knots_out[-1] + (b - a) * k)
    off = knots_out[-1] / 2
    knots_out = [k - off for k in knots_out]
    for o in objs:
        co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        co[:, 1] = np.interp(co[:, 1], knots_in, knots_out); co[:, 0] *= s; co[:, 2] *= s
        o.data.vertices.foreach_set("co", co.ravel()); o.data.update()
    m = lambda y: float(np.interp(y, knots_in, knots_out))
    frame = {"kind": kind, "scale_xz": s, "k_mid": k_mid, "k_overhang": k_o, "rear_axle_y": m(ar), "front_axle_y": m(af),
             "wheel_r": rad * s, "len": knots_out[-1] - knots_out[0], "y0": knots_out[0], "y1": knots_out[-1],
             "height": float((V[:, 2].max()) * s), "width_paint": DIMS[kind]["width"], "src_len_units": float(y1 - y0),
             "src_wb_units": float(af - ar), "map": [knots_in, knots_out]}
    frame["wb"] = frame["front_axle_y"] - frame["rear_axle_y"]
    if kind == "van":   # the B-pillar: the front door's rear edge (source object of the cab doors) in the fitted frame
        cab = next(o for o in objs if o.name == "Object_25")
        frame["b_pillar_y"] = float(min(v.co.y for v in cab.data.vertices))
    else:
        doors = next(o for o in objs if o.name == "Object_21")   # glass: the front door glass's front edge ~ the A-pillar foot
        frame["glass_y"] = [float(min(v.co.y for v in doors.data.vertices)), float(max(v.co.y for v in doors.data.vertices))]
    return objs, frame


def bounds(o):
    import numpy as np
    V = np.array([v.co[:] for v in o.data.vertices]); return V.min(0), V.max(0)


def debug(kind):
    objs, frame = load(kind)
    print("FRAME", json.dumps({k: v for k, v in frame.items() if k != "map"}))
    for o in sorted(objs, key=lambda o: int(o.name.split("_")[1])):
        mn, mx = bounds(o)
        print(f"DBG {o.name:10s} {o.data.materials[0].name if o.data.materials else '-':16s} {len(o.data.polygons):7d}f  min {mn.round(2)} max {mx.round(2)}")


def prep(kind):
    objs, frame = load(kind)
    WORK.mkdir(parents=True, exist_ok=True); (WORK / f"{kind}_frame.json").write_text(json.dumps(frame, indent=1))
    print("FRAME", json.dumps({k: v for k, v in frame.items() if k != "map"}))


# ---------- materials
def mat(name, col=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, img=None, emit=None, emit_img=False, alpha=1.0):
    import bpy
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1.0); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if img is not None:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img if not isinstance(img, (str, Path)) else bpy.data.images.load(str(img))
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if emit_img: nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    if emit is not None:
        if not emit_img: b.inputs["Emission Color"].default_value = (*emit, 1.0)
        b.inputs["Emission Strength"].default_value = 1.0
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    m.diffuse_color = (*col, 1.0)
    return m


def set_mat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
    for p in o.data.polygons: p.material_index = 0


def face_split(o, test, m_true):
    """Faces where test(center, normal) is True get m_true (appended as a second slot)."""
    me = o.data
    if m_true.name not in [x.name for x in me.materials]: me.materials.append(m_true)
    idx = [x.name for x in me.materials].index(m_true.name); n = 0
    for p in me.polygons:
        if test(p.center, p.normal): p.material_index = idx; n += 1
    return n


# ---------- geometry helpers (bmesh primitives into one object per material)
class Kit:
    def __init__(self, name):
        import bmesh
        self.name = name; self.bm = {}; self.bmesh = bmesh

    def get(self, m):
        if m not in self.bm: self.bm[m] = self.bmesh.new()
        return self.bm[m]

    def box(self, m, c, size, rot_z=0.0):
        from mathutils import Matrix, Vector
        bm = self.get(m)
        M = Matrix.Translation(Vector(c)) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Diagonal((*size, 1.0))
        self.bmesh.ops.create_cube(bm, size=1.0, matrix=M)

    def cyl(self, m, c, r1, r2, h, seg=16, axis="Z", cap=True, rot_z=0.0):
        from mathutils import Matrix, Vector
        bm = self.get(m)
        R = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(-math.pi / 2, 4, "X")}[axis]
        M = Matrix.Translation(Vector(c)) @ Matrix.Rotation(rot_z, 4, "Z") @ R
        self.bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=M)

    def sphere(self, m, c, r, seg=12):
        from mathutils import Matrix, Vector
        bm = self.get(m)
        self.bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r, matrix=Matrix.Translation(Vector(c)))

    def objects(self, coll):
        import bpy
        out = []
        for m, bm in self.bm.items():
            me = bpy.data.meshes.new(f"{self.name}_{m.name}"); bm.to_mesh(me); bm.free()
            for p in me.polygons: p.use_smooth = True
            o = bpy.data.objects.new(me.name, me); coll.objects.link(o); set_mat(o, m); out.append(o)
        self.bm = {}
        return out


def project_paint_uv(o, L):
    """Paint faces' UVs from the atlas regions (the livery is painted in metres, atlas_px): by face normal, side / front / rear / top."""
    me = o.data
    uv = me.uv_layers[0] if me.uv_layers else me.uv_layers.new()
    pi = [x.name.startswith("VEH_") and x.name.endswith("_Paint") for x in me.materials]
    for p in me.polygons:
        if not pi[p.material_index]: continue
        n = p.normal
        if abs(n.x) >= 0.5: reg = "side_r" if n.x > 0 else "side_l"
        elif n.y >= 0.5: reg = "front"
        elif n.y <= -0.5: reg = "rear"
        else: reg = "top"
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a, b = (co.y, co.z) if reg.startswith("side") else (co.x, co.z) if reg in ("front", "rear") else (co.x, co.y)
            px, py = atlas_px(reg, a, b, L)
            uv.data[li].uv = (px / TEX, 1 - py / TEX)


def decimate_to(objs, target, weight):
    """Collapse-decimate each object so the total lands near target; weight(o) scales an object's share (interior low)."""
    import bpy
    tri = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    w0 = weight; weight = lambda o: 1e6 if o.name.startswith(("Bar_", "Rack_", "Front_")) else w0(o)
    base = 1.0
    for _ in range(40):
        tot = sum(min(1.0, base * weight(o)) * tri[o.name] if tri[o.name] > 60 else tri[o.name] for o in objs)
        base *= (target / tot) ** 0.9
        if abs(tot - target) < target * 0.02: break
    for o in objs:
        ratio = min(1.0, base * weight(o))
        if tri[o.name] <= 60 or ratio >= 0.999: continue
        md = o.modifiers.new("dec", "DECIMATE"); md.ratio = ratio; md.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.view_layer.objects: x.select_set(x == o)
        bpy.ops.object.modifier_apply(modifier=md.name)


def join(objs, name):
    import bpy
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o


def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def smooth(o, deg=40):
    o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(deg))


def lod_copy(o, name, target, drop=()):
    import bpy
    c = o.copy(); c.data = o.data.copy(); c.name = name; c.data.name = name; bpy.context.scene.collection.objects.link(c)
    if drop:   # remove faces of the dropped materials (interior, underbody) before decimating
        import bmesh
        bm = bmesh.new(); bm.from_mesh(c.data)
        di = {i for i, m in enumerate(c.data.materials) if m.name in drop}
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in di], context="FACES"); bm.to_mesh(c.data); bm.free()
    md = c.modifiers.new("dec", "DECIMATE"); md.ratio = min(1.0, target / max(1, tris(c))); md.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = c
    for x in bpy.context.view_layer.objects: x.select_set(x == c)
    bpy.ops.object.modifier_apply(modifier=md.name)
    return c


# ---------- the cars
def build_police(objs, frame, police=True):
    import bpy
    coll = bpy.context.scene.collection
    by = {o.name: o for o in objs}
    T = lambda n: str(WORK / n)
    tag = "Police" if police else "Sedan"
    paint = mat(f"VEH_{tag}_Paint", (0.02, 0.025, 0.06), 0.35, img=T(f"{tag.lower()}_livery.png"))
    chrome = mat("VEH_Chrome", (0.85, 0.85, 0.86), 0.12, 1.0)
    trim = mat("VEH_TrimBlack", (0.03, 0.03, 0.03), 0.6)
    rubber = mat("VEH_Rubber", (0.025, 0.025, 0.025), 0.85)
    glass = mat("VEH_Glass", (0.02, 0.025, 0.03), 0.05, alpha=0.35)
    lamps = mat(f"VEH_{tag}_Lamps", (1, 1, 1), 0.2, img=by["Object_9"].data.materials[0].node_tree.nodes.get("Image Texture").image, emit=(1, 1, 1) if police else None, emit_img=police)
    beacon = mat("VEH_BeaconRed", (0.8, 0.05, 0.03), 0.15, emit=(1.0, 0.04, 0.02))
    beacon_b = mat("VEH_BeaconBlue", (0.04, 0.12, 0.8), 0.15, emit=(0.05, 0.2, 1.0))   # user Oct 20: red + blue bar (film: all red)
    plate = mat("VEH_Plate", (1, 1, 1), 0.4, img=T("plate.png"))
    keep_tex = lambda o, n, rough=0.6: set_mat(o, mat(n, (1, 1, 1), rough, img=o.data.materials[0].node_tree.nodes.get("Image Texture").image))
    frame["bar_y"] = sum(bounds(by["Object_32"])[i][1] for i in (0, 1)) / 2   # the source bar's centre line
    # the source's bar housing and its lamps, and the duplicate NYPD decal shell (Paintb1 lies on Paint7)
    for n in ("Object_11", "Object_12", "Object_16", "Object_22", "Object_32", "Object_28", "Object_29"):
        bpy.data.objects.remove(by.pop(n))
    roles = {"Object_26": paint, "Object_27": paint, "Object_17": chrome, "Object_18": chrome, "Object_19": rubber, "Object_34": trim,
             "Object_21": glass, "Object_9": lamps, "Object_3": trim, "Object_30": chrome, "Object_31": plate, "Object_8": chrome,
             "Object_10": trim, "Object_23": trim, "Object_4": trim, "Object_6": trim, "Object_7": trim, "Object_5": trim,
             "Object_13": chrome, "Object_14": chrome, "Object_15": trim}
    for n, m in roles.items(): set_mat(by[n], m)
    keep_tex(by["Object_33"], "VEH_Tyre", 0.85)
    keep_tex(by["Object_2"], "VEH_Caprice_Under", 0.8)
    keep_tex(by["Object_20"], "VEH_Caprice_Interior", 0.7)
    keep_tex(by["Object_24"], "VEH_Caprice_Dash", 0.6)
    set_mat(by["Object_25"], mat("VEH_InteriorPlain", (0.05, 0.05, 0.055), 0.8))
    if not police:
        return list(by.values()), [], (lambda o: 0.15 if o.name in ("Object_2", "Object_20", "Object_25", "Object_24") else 1.0), \
            ("VEH_Caprice_Interior", "VEH_InteriorPlain", "VEH_Caprice_Dash", "VEH_Caprice_Under")
    # the film's bar (11590-11630): a chrome rail on two feet across the roof, outer tall MARS beacons, inner round flashers, a
    # centre siren speaker; all red in the film, red (left) + blue (right) by the user's choice. Placed on the old bar's footprint (roof centre, over the B-pillar).
    roof = max(v.co.z for n in ("Object_26", "Object_27") for v in by[n].data.vertices if abs(v.co.x) < 0.4 and abs(v.co.y - frame["bar_y"]) < 0.4)
    yb, zb = frame["bar_y"], roof
    k = Kit("Bar")
    k.box(chrome, (0, yb, zb + 0.10), (1.50, 0.16, 0.035))                  # the rail
    for sx in (-1, 1):
        k.box(chrome, (sx * 0.62, yb, zb + 0.04), (0.06, 0.24, 0.09))       # the feet on the drip rails
        k.cyl(chrome, (sx * 0.62, yb, zb + 0.16), 0.085, 0.085, 0.09, 20)   # MARS base can
        k.cyl(chrome, (sx * 0.30, yb, zb + 0.13), 0.035, 0.035, 0.03, 12)   # flasher stalk
    k.cyl(chrome, (0, yb, zb + 0.15), 0.03, 0.03, 0.06, 12)
    k.cyl(chrome, (0, yb + 0.03, zb + 0.24), 0.11, 0.035, 0.16, 20, axis="Y")   # siren horn, bell to the front
    bar = k.objects(coll)
    beacons = []
    for nm, x, r, h, zc in (("Beacon_L", -0.62, 0.08, 0.17, 0.295), ("Beacon_R", 0.62, 0.08, 0.17, 0.295),
                            ("Flasher_L", -0.30, 0.07, 0.0, 0.215), ("Flasher_R", 0.30, 0.07, 0.0, 0.215)):
        kb = Kit(nm)
        bm_ = beacon if nm.endswith("_L") else beacon_b   # _L = the car's left (driver, -X): red; _R: blue
        if h: kb.cyl(bm_, (x, yb, zb + zc), r, r * 0.92, h, 20); kb.sphere(bm_, (x, yb, zb + zc + h / 2), r * 0.9, 16)
        else: kb.sphere(bm_, (x, yb, zb + zc), r, 16)
        o = kb.objects(coll)[0]; o.name = nm; o.data.name = nm; beacons.append(o)
    body = [o for o in by.values()] + bar
    return body, beacons, (lambda o: 0.15 if o.name in ("Object_2", "Object_20", "Object_25", "Object_24") else 1.0), \
        ("VEH_Caprice_Interior", "VEH_InteriorPlain", "VEH_Caprice_Dash", "VEH_Caprice_Under")


def build_van(objs, frame):
    import bpy
    import numpy as np
    coll = bpy.context.scene.collection
    by = {o.name: o for o in objs}
    paint = mat("VEH_Van_Paint", (0.30, 0.38, 0.50), 0.4, img=str(WORK / "van_livery.png"))
    chrome = mat("VEH_Chrome", (0.85, 0.85, 0.86), 0.12, 1.0)
    satin = mat("VEH_SatinMetal", (0.55, 0.56, 0.57), 0.45, 1.0)
    trim = mat("VEH_TrimBlack", (0.03, 0.03, 0.03), 0.6)
    rubber = mat("VEH_Rubber", (0.025, 0.025, 0.025), 0.85)
    wheel = chrome                                                # 6830/3299: full chrome wheel covers (user review Oct 20)
    glass = mat("VEH_Glass", (0.02, 0.025, 0.03), 0.05, alpha=0.35)
    clear = mat("VEH_LampClear", (0.8, 0.8, 0.8), 0.1)
    amber = mat("VEH_LampAmber", (0.75, 0.30, 0.02), 0.15)
    red = mat("VEH_LampRed", (0.45, 0.03, 0.03), 0.15)
    interior = mat("VEH_InteriorPlain", (0.05, 0.05, 0.055), 0.8)
    for n in ("Object_4", "Object_5", "Object_6", "Object_7"):          # under-floor driveline (no UVs, never seen)
        bpy.data.objects.remove(by.pop(n))
    rolemap = {"carpaint": paint, "black": trim, "chrome": chrome, "clearglass": clear, "mattemetal": satin, "orangeglass": amber,
               "redglass": red, "material": chrome, "tire": rubber, "windowglass": glass, "mirror": chrome, "interior": interior}
    rolemap["orangeglass"] = clear   # the 1994 amber wraparound marker -> the film's clear lens in a chrome corner (6830)
    for o in by.values(): set_mat(o, rolemap[o.data.materials[0].name])
    # wheels (6830): cream-grey painted steel with a small chrome centre cap; the source's rims are chrome discs in the trim parts
    ra, fa, wr = frame["rear_axle_y"], frame["front_axle_y"], frame["wheel_r"]
    def is_rim(c, n):
        d = min(math.hypot(c.y - ra, c.z - wr), math.hypot(c.y - fa, c.z - wr))
        return abs(c.x) > 0.70 and d < wr * 0.62
    nrim = sum(face_split(o, is_rim, wheel) for o in by.values() if o.data.materials[0] in (rubber, chrome, trim))
    print("van rim faces", nrim)
    # the cargo side glass (behind the B-pillar) and its rubber become body panels flush with the side: film 3297/6830/9527
    yb = frame["b_pillar_y"]
    P = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in by.values() if o.data.materials[0] == paint])
    side = P[(P[:, 1] < yb - 0.05) & (P[:, 1] > frame["y0"] + 0.4)]
    def x_side(z):
        sel = side[np.abs(side[:, 2] - z) < 0.03]
        return float(np.abs(sel[:, 0]).max()) if len(sel) else None
    zs = {}
    blanked = 0
    win_z = (1.25, 1.95)
    for o in by.values():
        m0 = o.data.materials[0]
        if m0 not in (glass, trim): continue
        me = o.data; hit = set()
        if paint.name not in [x.name for x in me.materials]: me.materials.append(paint)
        pi = [x.name for x in me.materials].index(paint.name)
        for p in me.polygons:
            c = p.center
            if abs(p.normal.x) > 0.6 and c.y < yb - 0.03 and c.y > frame["y0"] + 0.25 and win_z[0] < c.z < win_z[1] and abs(c.x) > 0.80:
                p.material_index = pi; hit.update(p.vertices); blanked += 1
        for vi in hit:
            v = me.vertices[vi]; zk = round(v.co.z, 2)
            if zk not in zs: zs[zk] = x_side(v.co.z)
            if zs[zk]: v.co.x = math.copysign(zs[zk] - 0.002, v.co.x)
    print("van: blanked", blanked, "cargo-side glass/seal faces")
    front_end(by, frame, coll, chrome, trim, clear)
    # the roof: a ladder rack (galvanised tube) on gutter clamps, the film's load (6830: two black buckets, pipe lengths, boxes)
    roof = float(P[:, 2].max())
    y_a, y_b = yb + 0.55, frame["y0"] + 0.25           # rack from over the windscreen header to the rear
    rack = mat("VEH_RackMetal", (0.62, 0.63, 0.62), 0.45, 1.0)
    pipe = mat("VEH_Pipe", (0.55, 0.35, 0.22), 0.4, 1.0)
    box = mat("VEH_BoxWhite", (0.75, 0.74, 0.70), 0.7)
    k = Kit("Rack")
    zr = roof + 0.09
    ln = y_a - y_b; yc = (y_a + y_b) / 2
    for sx in (-1, 1):
        k.box(rack, (sx * 0.80, yc, zr), (0.035, ln, 0.04))
        for yy in np.linspace(y_b + 0.1, y_a - 0.1, 4): k.box(rack, (sx * 0.84, yy, roof - 0.01), (0.08, 0.06, 0.20))   # clamps to the gutter
    for yy in np.linspace(y_b + 0.05, y_a - 0.05, 7): k.box(rack, (0, yy, zr), (1.64, 0.03, 0.03))
    for sx in (-1, 1): k.box(rack, (sx * 0.80, yc, zr + 0.10), (0.03, ln, 0.03))   # upper rail of the basket sides
    for sx in (-1, 1):
        for yy in np.linspace(y_b + 0.05, y_a - 0.05, 9): k.box(rack, (sx * 0.80, yy, zr + 0.05), (0.02, 0.02, 0.10))
    # the load (6830, 3520, 9527): pipe lengths, an aluminium ladder, buckets (two black, one white, one upturned), cardboard
    # boxes, a tarp humped over a pile, rope lashings. Positions are seeded by eye, not measured.
    rng = np.random.default_rng(3)
    card = mat("VEH_Cardboard", (0.45, 0.33, 0.20), 0.85)
    tarp = mat("VEH_Tarp", (0.16, 0.20, 0.18), 0.8)
    rope = mat("VEH_Rope", (0.62, 0.52, 0.30), 0.9)
    alu = mat("VEH_Aluminium", (0.70, 0.71, 0.72), 0.5, 1.0)
    white = mat("VEH_BucketWhite", (0.78, 0.78, 0.74), 0.5)
    zt = zr + 0.02                                                  # top of the rack's deck bars
    for i in range(9):                                              # pipe: copper and galvanised, lengths and yaws vary
        r = [0.011, 0.016, 0.022, 0.027][i % 4]; L_ = ln * rng.uniform(0.55, 1.0); x = rng.uniform(-0.62, -0.05)
        k.cyl(pipe if i % 3 else rack, (x, yc + rng.uniform(-0.3, 0.3), zt + r + 0.02 * (i // 3)), r, r, L_, 8, axis="Y", rot_z=rng.uniform(-0.04, 0.04))
    lx, ll = 0.38, min(ln - 0.1, 3.2)                               # the ladder on the right of the rack
    for sx in (-0.21, 0.21): k.box(alu, (lx + sx, yc - 0.05, zt + 0.06), (0.025, ll, 0.075))
    for yy in np.arange(-ll / 2 + 0.15, ll / 2 - 0.1, 0.30): k.cyl(alu, (lx, yc - 0.05 + yy, zt + 0.06), 0.015, 0.015, 0.42, 8, axis="X")
    k.cyl(trim, (-0.30, y_a - 0.85, zt + 0.19), 0.15, 0.13, 0.36, 16)          # buckets (5 gal: 0.36 m tall)
    k.cyl(trim, (-0.02, y_a - 0.95, zt + 0.19), 0.15, 0.13, 0.36, 16)
    k.cyl(white, (-0.55, y_b + 1.15, zt + 0.19), 0.13, 0.15, 0.36, 16)         # upturned
    for x, y, sx_, sy_, h, rz in ((0.45, y_a - 0.30, 0.42, 0.30, 0.20, 0.10), (-0.40, y_b + 0.55, 0.36, 0.30, 0.18, -0.15),
                                 (0.10, y_b + 0.45, 0.40, 0.34, 0.26, 0.05), (0.32, y_b + 1.35, 0.30, 0.26, 0.16, -0.30)):
        k.box(card, (x, y, zt + h / 2 + (0.15 if abs(x - lx) < 0.3 else 0)), (sx_, sy_, h), rz)
    # the tarp: a lumpy sheet over the middle of the pile
    import bmesh as _bm
    from mathutils import Matrix as _M
    tb = k.get(tarp); ty, tw, tl = yc - 0.2, 0.9, 1.2
    g = _bm.ops.create_grid(tb, x_segments=14, y_segments=18, size=0.5, matrix=_M.Translation((-0.25, ty, 0)) @ _M.Diagonal((tw, tl, 1, 1)))
    for v in g["verts"]:
        u, w_ = (v.co.x + 0.25) / (tw / 2), (v.co.y - ty) / (tl / 2)
        hump = max(0.0, 1 - u * u) ** 0.5 * max(0.0, 1 - w_ * w_) ** 0.6
        v.co.z = zt + 0.04 + 0.30 * hump + rng.normal(0, 0.012) + 0.03 * math.sin(7 * v.co.y + 3 * v.co.x)
    for yy in (ty - 0.35, ty + 0.35, y_b + 0.5, y_a - 0.6):            # rope lashings across the load
        k.box(rope, (0, yy, zt + 0.30), (1.62, 0.012, 0.012))
    rack_objs = k.objects(coll)
    body = list(by.values()) + rack_objs
    return body, [], (lambda o: 0.04 if o.data.materials[0] == interior else 1.0), ("VEH_InteriorPlain",)


def front_end(by, frame, coll, chrome, trim, clear):
    """The source is a 1994-97 Ram Van (crosshair grille, composite lamps); the film's van (3500-3530) has the 1979-93 face: single
    rectangular sealed-beam headlamps in chrome bezels at the ends of a chrome-framed grille of thin horizontal bars. The 1994 grille,
    its surround and the composite lamps' front faces are cut out and the period face is built in the same opening."""
    import bmesh
    import numpy as np
    yg = max(v.co.y for v in by["Object_9"].data.vertices)
    zcut = max(v.co.z for v in by["Object_21"].data.vertices) - 0.02          # the black valance's top: below it is the bumper
    cut = {"Object_9": lambda c, n: True,
           "Object_34": lambda c, n: c.y > yg - 0.3,
           "Object_37": lambda c, n: n.y > 0.5,
           "Object_35": lambda c, n: c.z > zcut and c.y > yg - 0.3,
           "Object_18": lambda c, n: c.z > zcut and c.y > yg - 0.3 and abs(c.x) < 0.85}
    gone = []
    for name, test in cut.items():
        o = by[name]; bm = bmesh.new(); bm.from_mesh(o.data)
        fs = [f for f in bm.faces if test(f.calc_center_median(), f.normal)]
        if name in ("Object_35", "Object_34"): gone += [v.co.copy() for f in fs for v in f.verts]
        bmesh.ops.delete(bm, geom=fs, context="FACES"); bm.to_mesh(o.data); bm.free()
    G = np.array([v[:] for v in gone]); x1 = float(np.abs(G[:, 0]).max()); z0, z1 = float(G[:, 2].min()), float(G[:, 2].max()); yf = float(G[:, 1].max())
    print(f"van front: opening x +-{x1:.3f}, z {z0:.3f}..{z1:.3f}, face y {yf:.3f}")
    k = Kit("Front"); zc, h = (z0 + z1) / 2, z1 - z0
    k.box(trim, (0, yf - 0.06, zc), (2 * x1, 0.08, h))                                   # backing
    for zz in (z0 + 0.012, z1 - 0.012): k.box(chrome, (0, yf - 0.012, zz), (2 * x1, 0.03, 0.025))   # the surround
    for xx in (-x1 + 0.012, x1 - 0.012): k.box(chrome, (xx, yf - 0.012, zc), (0.025, 0.03, h))
    lw = 0.27                                                                             # headlamp bay width
    for sx in (-1, 1):
        xc = sx * (x1 - lw / 2 - 0.02)
        k.box(chrome, (xc, yf - 0.02, zc), (lw - 0.03, 0.03, h - 0.06))                  # bezel
        k.box(clear, (xc, yf - 0.002, zc), (0.20, 0.02, 0.145))                           # 200 x 142 mm sealed beam
        k.box(chrome, (sx * (x1 - lw - 0.02), yf - 0.015, zc), (0.02, 0.03, h))           # bay divider
    gx = x1 - lw - 0.03
    for i in range(1, 4): k.box(chrome, (0, yf - 0.02, z0 + h * i / 4), (2 * gx, 0.02, 0.012))   # three horizontal bars
    for i in range(-2, 3): k.box(chrome, (gx * i / 2.5, yf - 0.025, zc), (0.012, 0.02, h - 0.03))
    by["Front_kit"] = k.objects(coll)
    for i, o in enumerate(by.pop("Front_kit")): by[f"Front_{i}"] = o


def build(kind):
    import bpy
    objs, frame = load(kind)
    frame.update(json.loads((WORK / f"{kind}_frame.json").read_text()))
    body, beacons, weight, interior_mats = (build_van(objs, frame) if kind == "van" else build_police(objs, frame, kind == "police"))
    src_tris = sum(tris(o) for o in body)
    decimate_to(body, TRIS["LOD0"] - sum(tris(b) for b in beacons), weight)
    name = KIND[kind]
    lod0 = join(body, name + "_LOD0")
    project_paint_uv(lod0, DIMS[kind]["len"] * 1.2)
    smooth(lod0)
    lod1 = lod_copy(lod0, name + "_LOD1", TRIS["LOD1"], drop=interior_mats[1:] if kind != "van" else ())
    lod2 = lod_copy(lod0, name + "_LOD2", TRIS["LOD2"], drop=interior_mats)
    for o in (lod1, lod2): smooth(o)
    for b in beacons: smooth(b, 60)
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    for o in [lod0, lod1, lod2] + beacons: o.parent = root
    stats = {"kind": name, "source_tris": src_tris, "LOD0": tris(lod0) + sum(tris(b) for b in beacons), "LOD1": tris(lod1), "LOD2": tris(lod2),
             "materials": [m.name for m in lod0.data.materials], "frame": {k: v for k, v in frame.items() if k != "map"}}
    import numpy as np
    V = np.array([v.co[:] for v in lod0.data.vertices]); mn, mx = V.min(0), V.max(0)
    stats["bounds"] = {"min": mn.round(3).tolist(), "max": mx.round(3).tolist()}
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in [root, lod0, lod1, lod2] + beacons: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), export_format="GLB", export_yup=True, use_selection=True,
                              export_materials="EXPORT", export_image_format="AUTO")
    import shutil   # the paint's HDRP mask map (R metallic, G AO, A smoothness), picked up by VehiclePrefabs via spec/vehicles.json
    shutil.copy(WORK / f"{kind}_livery_Mask.png", OUT / f"VEH_{kind.capitalize()}_Paint_Mask.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK / f"{name}.blend"))
    (WORK / f"{kind}_stats.json").write_text(json.dumps(stats, indent=1))
    print("STATS", json.dumps(stats))


# ------------------------------------------------------------------ plain Python side: the liveries (PIL, from the frames by eye)
FONTS = "/System/Library/Fonts/Supplemental/"


def _paint(kind):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    fr = json.loads((WORK / f"{kind}_frame.json").read_text()); L = DIMS[kind]["len"] * 1.2
    rng = np.random.default_rng(7)
    base = {"police": POLICE_NAVY, "van": VAN_BLUE, "sedan": SEDAN_BLUE}[kind]
    img = Image.new("RGB", (TEX, TEX), base); d = ImageDraw.Draw(img)
    mask = np.zeros((TEX, TEX, 4), np.uint8); mask[..., 1] = 255; mask[..., 3] = int(255 * (0.35 if kind == "van" else 0.62))   # the van: a dull, weathered clear coat
    px = lambda reg, a, b: atlas_px(reg, a, b, L)
    def font(f, h_m, region="side_r"):
        hp = abs(px(region, 0, 1.0)[1] - px(region, 0, 1.0 + h_m)[1])
        return ImageFont.truetype(FONTS + f, max(8, int(hp * 1.35)))
    def text(region, s, f, h_m, y_c, z_top, fill, outline=None, ow=0, shear=0.0, width_m=None):
        """Text centred at length y_c with cap top at z_top (metres), drawn on its own layer (italic shear), pasted into the region."""
        fnt = font(f, h_m, region)
        bb = d.textbbox((0, 0), s, font=fnt, stroke_width=ow)
        tw, th = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        lay = Image.new("RGBA", (int(tw + abs(shear) * th), th), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.text((20 + (abs(shear) * th if shear > 0 else 0) - bb[0], 20 - bb[1]), s, font=fnt, fill=fill, stroke_width=ow, stroke_fill=outline)
        if shear: lay = lay.transform(lay.size, Image.AFFINE, (1, shear, 0, 0, 1, 0), Image.BICUBIC)
        if width_m:   # squeeze or stretch to the film's measured width
            wpx = abs(px(region, y_c + width_m / 2, 1)[0] - px(region, y_c - width_m / 2, 1)[0])
            lay = lay.resize((int(wpx * lay.width / (tw - 40)), lay.height), Image.LANCZOS)
        cx, ty = px(region, y_c, z_top)
        img.paste(lay, (int(cx - lay.width / 2), int(ty - 20)), lay)
    # grime: road salt up the lower body (both cars; the van much more: 6830), and a little mottling
    for region in (("side_r", "side_l", "front", "rear") if kind != "van" else ("front", "rear")):
        for z in np.arange(0.0, 0.9, 0.01):
            amt = max(0.0, 1 - z / (0.75 if kind == "van" else 0.45)) ** 1.6 * (0.55 if kind == "van" else 0.25)
            if region.startswith("side"): y0_, y1_ = px(region, 0, z)[1], px(region, 0, z + 0.01)[1]
            else: y0_, y1_ = px(region, 0, z)[1], px(region, 0, z + 0.01)[1]
            if not (FRONT_Z[0] <= z <= FRONT_Z[1]) and not region.startswith("side"): continue
            x0 = 0 if region.startswith("side") else px(region, 1.2 * (1 if region == "front" else -1), 0)[0]
            x1 = TEX if region.startswith("side") else px(region, -1.2 * (1 if region == "front" else -1), 0)[0]
            col = tuple(int(c * (1 - amt) + g * amt) for c, g in zip(base, (120, 112, 100)))
            d.rectangle([min(x0, x1), min(y0_, y1_), max(x0, x1), max(y0_, y1_)], fill=col)
            r0, r1 = int(min(y0_, y1_)), int(max(y0_, y1_)) + 1
            mask[r0:r1, int(min(x0, x1)):int(max(x0, x1)), 3] = int(mask[0, 0, 3] * (1 - amt * 0.9))
    if kind == "police":
        fa = fr["front_axle_y"]; g0, g1 = fr["glass_y"]
        for region in ("side_r", "side_l"):
            # the belt stripe: a light band under the beltline, nose to tail (11574-11626)
            z1, z0 = 0.93, 0.83
            a, b = px(region, -L / 2, z1), px(region, L / 2, z0)
            d.rectangle([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], fill=POLICE_STRIPE)
            mask[int(a[1]):int(b[1]), :, 3] = 150
            # POLICE across the stripe on the front fender, just ahead of the front axle (11574: centred over the wheel's front half)
            text(region, "POLICE", "Arial Black.ttf", 0.085, fa + 0.10, 0.925, (238, 240, 244), POLICE_NAVY, 3, width_m=0.62)
            # the Winnetka shield on the front door (point down, top at the stripe): white rim, light blue field, red and white seal
            yc = fa - 1.30; top = 0.86; hw, hh = 0.15, 0.40
            pts = [(yc - hw, top), (yc + hw, top), (yc + hw, top - hh * 0.55), (yc, top - hh), (yc - hw, top - hh * 0.55)]
            P = [px(region, y, z) for y, z in pts]
            d.polygon(P, fill=(236, 240, 244))
            ins = [(yc - hw * 0.8, top - 0.03), (yc + hw * 0.8, top - 0.03), (yc + hw * 0.8, top - hh * 0.55), (yc, top - hh + 0.05), (yc - hw * 0.8, top - hh * 0.55)]
            d.polygon([px(region, y, z) for y, z in ins], fill=(120, 160, 210))
            cx, cy = px(region, yc, top - 0.17); rr = abs(px(region, yc, 0)[1] - px(region, yc, 0.07)[1])
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(170, 30, 36), outline=(240, 240, 240), width=4)
            text(region, "WINNETKA", "Arial Narrow Bold.ttf", 0.028, yc, top - 0.045, (24, 30, 58), width_m=0.2)
        a, b = px("rear", -1.2, 0.95), px("rear", 1.2, 0.85)   # 11630: the band carries on across the tail panel above the lamps
        d.rectangle([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], fill=POLICE_STRIPE)
        plate = Image.new("RGB", (512, 256), (238, 238, 232)); pd = ImageDraw.Draw(plate)   # 11630: "M 30648", Illinois municipal
        pd.rectangle([6, 6, 505, 249], outline=(40, 50, 90), width=6)
        pd.text((256, 40), "LAND OF LINCOLN", font=ImageFont.truetype(FONTS + "Arial Narrow Bold.ttf", 30), fill=(40, 50, 90), anchor="mm")
        pd.text((256, 135), "M 30648", font=ImageFont.truetype(FONTS + "Arial Narrow Bold.ttf", 130), fill=(30, 40, 90), anchor="mm")
        pd.text((256, 222), "ILLINOIS", font=ImageFont.truetype(FONTS + "Arial Narrow Bold.ttf", 30), fill=(40, 50, 90), anchor="mm")
        plate.rotate(180).save(WORK / "plate.png")   # the source's plate UVs run upside down
    elif kind == "van":
        yb, y0 = fr["b_pillar_y"], fr["y0"]
        span = yb - y0                                 # cargo side, B-pillar to tail
        for region, line3 in (("side_r", "“Your Flood Control Experts!”"), ("side_l", "‘Residential Work Is Our Specialty’")):
            yc = yb - span * 0.38                      # 6830: the block's centre ~0.4 of the way from the B-pillar to the tail
            dx = (lambda m: m) if region == "side_r" else (lambda m: -m)   # an offset to the image's right
            text(region, "OH-KAY", "Arial Black.ttf", 0.24, yc, 1.84, (190, 32, 38), (25, 20, 20), 5, shear=-0.22, width_m=1.50)
            text(region, "PLUMBING & HEATING", "DIN Condensed Bold.ttf", 0.16, yc, 1.58, (22, 22, 24), width_m=1.48)
            text(region, line3, "Brush Script.ttf", 0.11, yc, 1.385, (180, 30, 36), (180, 30, 36), 2, width_m=1.36 if region == "side_r" else 1.45)
            text(region, "Call", "Brush Script.ttf", 0.13, yc + dx(-0.30), 1.21, (22, 22, 24), (22, 22, 24), 2, width_m=0.27)
            text(region, "JK5-1350", "Arial Narrow Bold.ttf", 0.115, yc + dx(0.14), 1.20, (22, 22, 24), width_m=0.52)
            # RAM badge on the front fender behind the wheel arch's top, ahead of the door (3299, 6830)
            fa = fr["front_axle_y"]
            bx, by_ = px(region, fa - 0.62, 1.10); bw = abs(px(region, 0.34, 0)[0] - px(region, 0, 0)[0]); bh = abs(px(region, 0, 1)[1] - px(region, 0, 1.065)[1])
            d.rectangle([bx - bw / 2, by_, bx + bw / 2, by_ + bh], fill=(40, 40, 44), outline=(200, 200, 205), width=3)
            text(region, "RAM", "Arial Black.ttf", 0.045, fa - 0.66, 1.093, (215, 215, 220), width_m=0.2)
        # DODGE on the hood's front lip (3510/3520), dark stamped letters
        text("front", "DODGE", "Arial Black.ttf", 0.05, 0.0, 1.12, (40, 44, 52), width_m=0.42)
        # weathering: dirt streaks under the livery's lower edge and rust at the wheel arches are left to the grime band
    noise = rng.normal(0, 3.0, (TEX, TEX, 1)).astype(np.float32)
    a = np.asarray(img, np.float32)
    if kind == "van": a = _van_grime(a, mask, fr, L, rng)
    a = np.clip(a + noise, 0, 255).astype(np.uint8)
    Image.fromarray(a).save(WORK / f"{kind}_livery.png")
    Image.fromarray(mask, "RGBA").save(WORK / f"{kind}_livery_Mask.png")


def render(kind, mode=None):
    """Eevee previews from the built .blend: police at night with the bar lit, the van by overcast day (beside the film: sheet())."""
    import bpy
    from mathutils import Vector
    bpy.ops.wm.open_mainfile(filepath=str(WORK / f"{KIND[kind]}.blend"))
    sc = bpy.context.scene; night = (mode or ("night" if kind == "police" else "day")) == "night"; mode = mode or ""
    for o in sc.objects:
        if o.name.endswith(("_LOD1", "_LOD2")): o.hide_render = True
    sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x, sc.render.resolution_y = 1280, 706
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast" if night else "None"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.02, 1) if night else (0.75, 0.74, 0.78, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.4 if night else 0.8
    me = bpy.data.meshes.new("ground"); me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("ground", me); sc.collection.objects.link(g)
    gm = bpy.data.materials.new("asphalt"); gm.use_nodes = True; b = gm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.03, 0.03, 0.032, 1) if night else (0.08, 0.08, 0.08, 1); b.inputs["Roughness"].default_value = 0.25 if night else 0.8
    me.materials.append(gm)
    def light(t, loc, e, col=(1, 1, 1), size=0.1, rot=None):
        L = bpy.data.lights.new(t + str(len(bpy.data.lights)), t); L.energy = e; L.color = col
        if t == "AREA": L.size = size
        o = bpy.data.objects.new(L.name, L); o.location = loc; sc.collection.objects.link(o)
        if rot: o.rotation_euler = rot
        return o
    for m in bpy.data.materials:   # preview-only emission strengths (Unity's are in spec/vehicles.json)
        if not m.use_nodes or "Principled BSDF" not in m.node_tree.nodes: continue
        bs = m.node_tree.nodes["Principled BSDF"]
        if m.name == "VEH_Police_Lamps": bs.inputs["Emission Strength"].default_value = 6.0 if night else 0.0
        if m.name in ("VEH_BeaconRed", "VEH_BeaconBlue"): bs.inputs["Emission Strength"].default_value = 1.5 if night else 0.0
        if m.name.endswith("_Paint"):   # a clear coat as Unity's HDRP Lit coat mask will add
            bs.inputs["Coat Weight"].default_value = 0.0 if mode == "flat" else (0.2 if "Van" in m.name else 1.0); bs.inputs["Coat Roughness"].default_value = 0.05
            if mode == "flat": bs.inputs["Roughness"].default_value = 0.9
    if night:
        bar = [o for o in sc.objects if o.name.startswith("Beacon_")]
        for o in bar:
            c = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
            light("POINT", c + Vector((0, 0, 0.05)), 600 if o.name.endswith("_L") else 900, (1, 0.05, 0.03) if o.name.endswith("_L") else (0.05, 0.2, 1.0))
        light("AREA", (-7, 6, 6), 900, (1.0, 0.72, 0.45), 4)          # the Murphys' lit porch and C7 strings beyond the car, tungsten
        light("AREA", (8, 9, 7), 500, (1.0, 0.8, 0.6), 2)             # the street lamp behind the camera
        light("AREA", (6, -4, 6), 60, (0.5, 0.6, 1.0), 6)             # the night sky's fill
        light("AREA", (5, 1, 3), 700, (1.0, 0.85, 0.7), 3)           # the film's key from the camera side (11581 lights the car's flank)
        light("AREA", (-5, -1, 3), 400, (1.0, 0.85, 0.7), 3)
        cams = [((3.6, 3.4, 0.8), (0.3, -0.6, 0.8), 24), ((6.5, 0.0, 1.2), (0, 0, 0.75), 30), ((-1.3, -3.6, 1.2), (0.4, -0.5, 1.2), 24)]
    else:
        light("SUN", (0, 0, 10), 1.2, (0.95, 0.95, 1.0), rot=(0.9, 0.2, 2.2))
        if kind != "van": cams = [((4.6, 6.2, 1.05), (0.0, 0.6, 0.65), 35), ((6.5, 0.0, 1.2), (0, 0, 0.75), 30), ((-3.5, -6.5, 1.6), (0, -0.4, 0.9), 35)]
        else: cams = [((7.0, 3.2, 1.25), (0.1, 0.1, 1.05), 35), ((0.0, 8.0, 1.25), (0, 0, 1.1), 35), ((-7.5, 1.5, 1.4), (0, 0, 1.0), 35)]
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    for i, (loc, at, fl) in enumerate(cams):
        cam.location = loc; cam.data.lens = fl
        cam.rotation_euler = (Vector(at) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(WORK / f"{kind}_{'night' if night else 'day'}_{i}.png"); bpy.ops.render.render(write_still=True)


def check():
    """The contract the swap hook relies on, from the build stats: budgets, period length, ground origin, nose +Y (Unity +z)."""
    for k in KIND:
        st = json.loads((WORK / f"{k}_stats.json").read_text()); b = st["bounds"]; f = st["frame"]
        assert st["LOD0"] <= 40000 and st["LOD1"] <= 12000 and st["LOD2"] <= 4000, (k, "tris", st["LOD0"], st["LOD1"], st["LOD2"])
        assert abs((b["max"][1] - b["min"][1]) - DIMS[k]["len"]) < 0.02, (k, "length", b)
        assert abs(f["wb"] - DIMS[k]["wb"]) < 0.01, (k, "wheelbase", f["wb"])
        assert -0.07 < b["min"][2] < 0.01 and abs(b["min"][0] + b["max"][0]) < 0.01, (k, "origin", b)
        assert f["front_axle_y"] > f["rear_axle_y"], (k, "nose must be +Y")
        print(f"check {KIND[k]}: LOD0 {st['LOD0']} LOD1 {st['LOD1']} LOD2 {st['LOD2']}, {b['max'][1] - b['min'][1]:.3f} m long, wb {f['wb']:.3f} OK")


def _van_grime(a, mask, fr, L, rng):
    """6830/3299/9527: the van is dirty: road spray up the sills and around the wheel arches, streaks running down from under the
    rack, an all-over dull film. Applied on the side regions over the lettering (the dirt is on top of the paint)."""
    import numpy as np
    from PIL import Image
    def lowfreq(n, scale):   # smooth noise 0..1
        g = Image.fromarray((rng.random((n, n)) * 255).astype(np.uint8)).resize((TEX, SIDE_H), Image.BICUBIC)
        return np.asarray(g, np.float32) / 255.0
    dirt = np.array([92, 86, 74], np.float32)          # salt-and-mud spray, grey-brown
    streak_col = np.array([58, 60, 58], np.float32)
    cols = np.arange(TEX) / TEX * L
    z = (1 - (np.arange(SIDE_H) + 0.5) / SIDE_H) * H_M
    for r0, sgn in ((0, 1), (SIDE_H, -1)):             # side_r: y = col - L/2; side_l: y = L/2 - col
        y = sgn * (cols - L / 2)
        Y, Z = np.meshgrid(y, z)
        n1, n2 = lowfreq(48, 1), lowfreq(160, 1)
        spray = np.clip(1 - Z / 0.80, 0, 1) ** 1.3 * (0.55 + 0.45 * n2)                     # sills, rising to ~0.8 m
        arch = np.zeros_like(Z)
        for ay in (fr["rear_axle_y"], fr["front_axle_y"]):
            d = np.hypot(Y - ay, Z - fr["wheel_r"])
            arch = np.maximum(arch, np.clip(1 - np.abs(d - fr["wheel_r"] - 0.10) / 0.22, 0, 1) * (Z > 0.25))
        arch *= 0.55 + 0.45 * n2
        st = rng.random(TEX) < 0.10                                                           # streaks below the rack's clamps and rails
        width = np.convolve(st.astype(np.float32), np.ones(5) / 5, "same")
        streak = width[None, :] * np.clip((Z - 1.30) / 0.60, 0, 1) ** 0.7 * (0.5 + 0.5 * n1)
        film = 0.10 + 0.08 * n1                                                               # an all-over dull grey film
        g = np.clip(np.maximum(spray * 0.85, arch * 0.7) + film, 0, 0.9)[..., None]
        sl = slice(r0, r0 + SIDE_H)
        a[sl] = a[sl] * (1 - g) + dirt * g
        s_ = np.clip(streak * 0.45, 0, 0.45)[..., None]
        a[sl] = a[sl] * (1 - s_) + streak_col * s_
        mask[sl, :, 3] = (mask[sl, :, 3] * (1 - 0.8 * g[..., 0])).astype(np.uint8)        # dirt is rough
    return a


def blender(*args):
    subprocess.run([BLENDER, "-b", "--factory-startup", "-P", __file__, "--", *args], check=True)


if __name__ == "__main__":
    if "bpy" in sys.modules:
        argv = sys.argv[sys.argv.index("--") + 1:]
        {"debug": debug, "prep": prep, "build": build, "render": render}[argv[0]](*argv[1:])
    else:
        if sys.argv[1:] == ["--check"]: check(); sys.exit(0)
        kinds = sys.argv[1:] or ["police", "van", "sedan"]   # police first: it paints the plate the sedan shares
        WORK.mkdir(parents=True, exist_ok=True)
        for k in kinds:
            blender("prep", k); _paint(k); blender("build", k); blender("render", k)
        check()
