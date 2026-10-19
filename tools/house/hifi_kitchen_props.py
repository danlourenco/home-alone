"""hifi_kitchen_props: the kitchen's pot rack and its pans, the island bar stools and the counter dressing (user Oct 19: "the kitchen
is missing a lot of detail ... appliances and visual fidelity ... the pans hanging down above the kitchen counters"). One GLB in spec
coordinates above the ground floor (SpecGreybox.KitchenProps places it at gy); every position is in spec/dressing/kitchen.json
"wares" (by eye from the film; the one ruler is the counter: 36 in high, 6 in tile pitch 0.158 m).

  pot rack      film 1050/1146/2116/6044/6900, user photo IMG_4305: a ceiling-hung iron rack over the island's long leg and its hooks
                (Oct 19 props-quality: the pans, stools, kettle and fruit are store props, Poly Haven models recoloured to the film by
                tools/house/kitchen_ph_props.py; this file keeps what no model fits). The film's two rows of
                pans hang handle-up: red enamel casseroles and skillets, black non-stick skillets with spiral-ringed bottoms,
                stainless saucepans. The old reference GLB's rack (objects 4/5/6/198: an octagonal iron frame on four rods, five
                256 px pans) confirms the form; its meshes are too coarse to borrow. Full change gate
                (changes/2026-10-19-kitchen-fidelity.json).
  bar stools    IMG_4305 / film 2116: four pine counter stools along the island's stool side: round dished seat, four splayed
                turned legs, a ring of stretchers. Props lane.
  counter       kettle (red enamel, chrome handle) on the cooktop, pine knife block with black handles, glass spaghetti canister,
                salt and pepper, rolling pin, round cutting board, red bowl of fruit on a green plate, green marble mortar and
                pestle, paper towel holder (film 1050/1074/1146/2116/6044/6056); end run by the back door: white drip coffee maker,
                can opener, four white canisters, toaster (film 10452/6044/9812); white microwave on the counter left of the back
                door (film 6900/9812/10452); papers and a drawing on the fridge (IMG_4306). Props lane.

Every closed part is built with outward faces (lathe/box/sweep through hifi_lib.Part; local frames are proper rotations, so winding
holds); nothing rests closer than 1 cm in the same plane to a surface it overlaps except where it stands on it (zfight-check).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_kitchen_props.py
  -> unity/HomeAlone/Assets/Models/Foyer/KitchenProps.glb
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/KitchenProps.glb"
K = json.loads((ROOT / "spec/dressing/kitchen.json").read_text()); W = K["wares"]; CH = K["std"]["counter_h"]

MATS = {  # name: (rgb, roughness, metallic)
    "KP_Iron": ((0.035, 0.035, 0.035), 0.55, 0.6), "KP_RedEnamel": ((0.62, 0.035, 0.03), 0.18, 0.0),
    "KP_NonStick": ((0.03, 0.03, 0.032), 0.45, 0.2), "KP_Steel": ((0.75, 0.75, 0.74), 0.22, 1.0),
    "KP_Chrome": ((0.85, 0.85, 0.85), 0.08, 1.0), "KP_Pine": ((0.72, 0.48, 0.25), 0.45, 0.0),
    "KP_BlackPlastic": ((0.03, 0.03, 0.03), 0.35, 0.0), "KP_White": ((0.86, 0.85, 0.82), 0.35, 0.0),
    "KP_Ceramic": ((0.9, 0.89, 0.85), 0.12, 0.0), "KP_Glass": ((0.8, 0.85, 0.85), 0.02, 0.0),
    "KP_Pasta": ((0.86, 0.68, 0.32), 0.6, 0.0), "KP_Coffee": ((0.08, 0.04, 0.02), 0.1, 0.0),
    "KP_Smoke": ((0.05, 0.05, 0.06), 0.05, 0.0), "KP_Marble": ((0.12, 0.22, 0.16), 0.15, 0.0),
    "KP_Green": ((0.25, 0.5, 0.32), 0.25, 0.0), "KP_AppleRed": ((0.55, 0.05, 0.04), 0.3, 0.0),
    "KP_AppleGreen": ((0.45, 0.6, 0.15), 0.3, 0.0), "KP_Orange": ((0.85, 0.42, 0.05), 0.45, 0.0),
    "KP_Paper": ((0.9, 0.9, 0.87), 0.8, 0.0), "KP_Yellow": ((0.95, 0.85, 0.35), 0.8, 0.0),
    "KP_Crayon": ((0.15, 0.5, 0.18), 0.8, 0.0), "KP_PhotoRed": ((0.6, 0.2, 0.18), 0.4, 0.0),
}
# parts by (object, material): each physical object (a pan, a stool, the kettle...) is ONE mesh with its materials, so its own
# handle or lid joining its body is not a clash between two renderers (zfight-check: a part's own triangles are skipped)
GROUP = ["Rack"]; PARTS = {}
class _P(dict):
    def __getitem__(self, m):
        k = (GROUP[0], m)
        if k not in PARTS: PARTS[k] = Part(f"{GROUP[0]}_{m[3:]}", m)
        return PARTS[k]
P = _P()
def group(name): GROUP[0] = name


# ---------------------------------------------------------------- local frames
def frame(o, yaw=0.0, tilt_x=0.0, tilt_z=0.0):
    """A proper rotation (yaw about y, then tilts) and origin o: local (x, y, z) -> spec."""
    def rot(v):
        x, y, z = v
        c, s = math.cos(tilt_x), math.sin(tilt_x); y, z = y * c - z * s, y * s + z * c          # about x
        c, s = math.cos(tilt_z), math.sin(tilt_z); x, y = x * c - y * s, x * s + y * c          # about z
        c, s = math.cos(yaw), math.sin(yaw); x, z = x * c + z * s, -x * s + z * c               # about y
        return x, y, z
    return lambda v: tuple(a + b for a, b in zip(o, rot(v)))


def into(part, tf, build):
    """Build in a scratch Part in local coordinates, then move its faces into 'part' through tf (a rotation: winding holds)."""
    t = Part("tmp", part.mat); build(t); i0 = len(part.v)
    part.v += [tf(v) for v in t.v]; part.f += [tuple(i0 + i for i in f) for f in t.f]


def lathe(p, prof, n=40):
    """About the local y axis; prof = [(y, r)] in travel order (outward faces when travelling up the outside). r == 0 ends are
    closed by a fan to the axis (no zero-area cap)."""
    def ring(y, r): return [(r * math.cos(2 * math.pi * k / n), y, r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for (ya, ra), (yb, rb) in zip(prof, prof[1:]):
        a, b = ring(ya, ra), ring(yb, rb)
        for k in range(n):
            k2 = (k + 1) % n
            if ra == 0: p.poly([a[0], b[k], b[k2]][::-1]) if False else p.poly([a[0], b[k], b[k2]])
            elif rb == 0: p.poly([a[k], b[0], a[k2]])
            else: p.quad(a[k], b[k], b[k2], a[k2])


def rod(p, path, r, n=10):
    p.sweep(path, [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)])


# ---------------------------------------------------------------- the pot rack
R = W["pot_rack"]; (rx0, rx1), (rz0, rz1), ry, ceil = R["x"], R["z"], R["y"], R["ceiling"]
B = 0.012                                                            # half the bar (25 mm square iron)
for z in (rz0, rz1):
    P["KP_Iron"].box(rx0, rx1, ry - B, ry + B, z - B, z + B)
for x in (rx0, rx1):
    P["KP_Iron"].box(x - B, x + B, ry - B, ry + B, rz0 + B, rz1 - B)
for x in (rx0 + 0.12, rx1 - 0.12):                                  # the hanging rods to ceiling plates
    for z in (rz0, rz1):
        rod(P["KP_Iron"], [(x, ry + B, z), (x, ceil - 0.012, z)], 0.006)
        P["KP_Iron"].lathe(x, z, ceil - 0.012, [(0, 0.045), (0.0115, 0.045)], n=20)   # plate, 1.15 cm thick, on the ceiling
# pans: R["pans"] = [kind, radius, height, along-x, row (0: near z0, 1: near z1), drop (m below the bar), depth offset (m out)]
for pi, (kind, r, h, ax, row, drop, out) in enumerate(R["pans"]):
    z = rz0 if row == 0 else rz1; sgn = -1.0 if row == 0 else 1.0
    group("Rack")
    hook_y = ry - B - drop
    zo = z + sgn * (0.03 + out)
    rest = 0.010 if kind == "red_casserole" else 0.021          # the hook's tip rests on the loop / the hanging hole's top, not through it
    rod(P["KP_Iron"], [(ax, ry, z), (ax, ry + B + 0.012, z + sgn * 0.012), (ax, ry + B + 0.012, zo), (ax, hook_y + rest, zo)], 0.003)
    # Oct 19 props-quality: the pans themselves are store props (spec/dressing/store_props.json kitchen_pan_NN: Poly Haven brass_pan_01 /
    # pot_enamel_01 recoloured, tools/house/kitchen_ph_props.py), each hung so its hole/loop meets this hook's tip

# bar stools: store props kitchen_stool_N (Poly Haven wooden_stool_01 in the film's pine, Oct 19 props-quality); walk colliders stay in
# kitchen.json "colliders" (stool_*)

# ---------------------------------------------------------------- counter dressing (each on its counter top, CH)
def on(x, z, yaw=0.0, y=CH):
    return frame((x, y, z), yaw=math.radians(yaw))


A = W["items"]
# the kettle: store prop kitchen_kettle (Poly Haven vintage_electric_kettle recoloured red enamel + chrome, Oct 19 props-quality)

group("KnifeBlock"); k = A["knife_block"]; tf = on(*k["at"], k.get("yaw", 0))                 # a wedge, 0.12 x 0.24 x 0.26, slots on the sloped top
def wedge(t):
    t.face([(-0.06, 0.0, -0.12), (0.06, 0.0, -0.12), (0.06, 0.0, 0.12), (-0.06, 0.0, 0.12)], (0, -1, 0))
    prof = [(-0.12, 0.0), (0.12, 0.0), (0.12, 0.10), (-0.05, 0.26), (-0.12, 0.26)]          # (z, y) side profile
    for s in (-0.06, 0.06):
        t.face([(s, y, z) for z, y in prof], (1 if s > 0 else -1, 0, 0))
    for (za, ya), (zb, yb) in zip(prof[1:], prof[2:] + prof[:1]):
        t.face([(-0.06, ya, za), (0.06, ya, za), (0.06, yb, zb), (-0.06, yb, zb)], (0, -(zb - za), yb - ya))
into(P["KP_Pine"], tf, wedge)
for i, (hx, hz) in enumerate(((-0.03, 0.02), (0.0, 0.02), (0.03, 0.02), (-0.015, 0.07), (0.015, 0.07))):
    yb = 0.10 + (0.12 - hz) * (0.16 / 0.17) - 0.01
    into(P["KP_BlackPlastic"], tf, lambda t, hx=hx, hz=hz, yb=yb: rod(t, [(hx, yb, hz), (hx, yb + 0.07, hz + 0.065), (hx, yb + 0.1, hz + 0.093)], 0.011, 10))

group("Spaghetti"); k = A["spaghetti"]; tf = on(*k["at"])
into(P["KP_Glass"], tf, lambda t: lathe(t, [(0.0, 0.0), (0.0, 0.048), (0.27, 0.048), (0.27, 0.044), (0.004, 0.044), (0.004, 0.0)], 32))
into(P["KP_Pasta"], tf, lambda t: lathe(t, [(0.006, 0.0), (0.006, 0.036), (0.255, 0.036), (0.255, 0.0)], 24))
into(P["KP_White"], tf, lambda t: lathe(t, [(0.262, 0.0), (0.262, 0.051), (0.295, 0.051), (0.3, 0.046), (0.3, 0.0)], 32))

for name in ("salt", "pepper"):
    group(name.title()); k = A[name]; tf = on(*k["at"])
    into(P["KP_Glass"], tf, lambda t: lathe(t, [(0.0, 0.0), (0.0, 0.026), (0.08, 0.024), (0.08, 0.0)], 20))
    into(P["KP_Chrome"], tf, lambda t: lathe(t, [(0.08, 0.0), (0.08, 0.025), (0.1, 0.02), (0.105, 0.0)], 20))
    if name == "pepper":
        into(P["KP_Smoke"], tf, lambda t: lathe(t, [(0.004, 0.0), (0.004, 0.021), (0.05, 0.021), (0.05, 0.0)], 16))

group("RollingPin"); k = A["rolling_pin"]; tf = frame((k["at"][0], CH + 0.032, k["at"][1]), yaw=math.radians(k.get("yaw", 0)), tilt_z=math.pi / 2)
into(P["KP_Marble"], tf, lambda t: lathe(t, [(-0.15, 0.0), (-0.15, 0.03), (-0.145, 0.032), (0.145, 0.032), (0.15, 0.03), (0.15, 0.0)], 28))
into(P["KP_Pine"], tf, lambda t: lathe(t, [(-0.25, 0.0), (-0.25, 0.012), (-0.2, 0.014), (-0.15, 0.01), (-0.15, 0.0)], 14))
into(P["KP_Pine"], tf, lambda t: lathe(t, [(0.15, 0.0), (0.15, 0.01), (0.2, 0.014), (0.25, 0.012), (0.25, 0.0)], 14))

group("CuttingBoard"); k = A["cutting_board"]; tf = on(*k["at"])
into(P["KP_Pine"], tf, lambda t: lathe(t, [(0.0, 0.0), (0.0, 0.165), (0.004, 0.17), (0.018, 0.17), (0.022, 0.165), (0.022, 0.0)], 48))

group("FruitBowl"); k = A["fruit_bowl"]; tf = on(*k["at"])
into(P["KP_Green"], tf, lambda t: lathe(t, [(0.0, 0.0), (0.0, 0.08), (0.008, 0.13), (0.02, 0.15), (0.024, 0.145), (0.012, 0.125), (0.008, 0.0)], 40))
into(P["KP_RedEnamel"], tf, lambda t: lathe(t, [(0.008, 0.0), (0.008, 0.055), (0.03, 0.085), (0.075, 0.105), (0.078, 0.1), (0.032, 0.08), (0.016, 0.0)], 40))
# the fruit: store props kitchen_apple_N (Poly Haven food_apple_01, Oct 19 props-quality); the bowl and plate stay here

group("Mortar"); k = A["mortar"]; tf = on(*k["at"])
into(P["KP_Marble"], tf, lambda t: lathe(t, [(0.0, 0.0), (0.0, 0.06), (0.08, 0.065), (0.09, 0.066), (0.09, 0.055), (0.03, 0.045), (0.02, 0.0)], 32))
into(P["KP_Marble"], frame((k["at"][0] + 0.02, CH + 0.03, k["at"][1]), tilt_z=-0.5), lambda t: lathe(t, [(0.0, 0.0), (0.0, 0.02), (0.05, 0.014), (0.15, 0.016), (0.16, 0.0)], 16))

group("PaperTowel"); k = A["paper_towel"]; tf = on(*k["at"])
into(P["KP_White"], tf, lambda t: lathe(t, [(0.0, 0.0), (0.0, 0.08), (0.012, 0.08), (0.012, 0.0)], 32))
into(P["KP_Paper"], tf, lambda t: lathe(t, [(0.014, 0.0), (0.014, 0.06), (0.29, 0.06), (0.29, 0.0)], 32))
into(P["KP_White"], tf, lambda t: lathe(t, [(0.29, 0.0), (0.29, 0.008), (0.33, 0.008), (0.34, 0.016), (0.35, 0.0)], 12))

# end run by the back door (front +x): coffee maker, can opener, four canisters, toaster
group("CoffeeMaker"); k = A["coffee_maker"]; tf = on(*k["at"], 90)                              # local +z = the appliance's front (into the room)
into(P["KP_White"], tf, lambda t: (t.box(-0.11, 0.11, 0.0, 0.035, -0.12, 0.12), t.box(-0.11, 0.11, 0.0, 0.34, -0.12, -0.04), t.box(-0.11, 0.11, 0.28, 0.34, -0.04, 0.10)))
into(P["KP_Glass"], tf, lambda t: lathe(t, [(0.035, 0.0), (0.035, 0.07), (0.14, 0.075), (0.17, 0.05), (0.17, 0.0)], 28))
into(P["KP_Coffee"], tf, lambda t: lathe(t, [(0.045, 0.0), (0.045, 0.055), (0.11, 0.058), (0.11, 0.0)], 24))
into(P["KP_BlackPlastic"], tf, lambda t: (t.box(-0.10, -0.098, 0.25, 0.27, -0.035, 0.09), t.box(0.075, 0.095, 0.06, 0.15, 0.06, 0.1)))
group("CanOpener"); k = A["can_opener"]; tf = on(*k["at"], 90)
into(P["KP_White"], tf, lambda t: t.box(-0.065, 0.065, 0.0, 0.22, -0.07, 0.04))
into(P["KP_Chrome"], tf, lambda t: t.box(-0.04, 0.04, 0.15, 0.17, 0.04, 0.06))
for ci, c in enumerate(A["canisters"]):
    group(f"Canister{ci}")
    tf = on(*c["at"]); r, h = c["r"], c["h"]
    into(P["KP_Ceramic"], tf, lambda t, r=r, h=h: lathe(t, [(0.0, 0.0), (0.0, r - 0.005), (0.004, r), (h, r), (h, 0.0)], 40))
    into(P["KP_Ceramic"], tf, lambda t, r=r, h=h: lathe(t, [(h, 0.0), (h, r + 0.003), (h + 0.015, r + 0.003), (h + 0.022, r * 0.5), (h + 0.022, 0.016), (h + 0.045, 0.014), (h + 0.05, 0.0)], 40))
group("Toaster"); k = A["toaster"]; tf = on(*k["at"], 90)
into(P["KP_White"], tf, lambda t: (t.box(-0.13, 0.13, 0.012, 0.19, -0.075, 0.075)))
into(P["KP_Chrome"], tf, lambda t: (t.box(-0.125, 0.125, 0.0, 0.012, -0.07, 0.07), t.box(-0.10, -0.06, 0.12, 0.135, 0.075, 0.09)))
into(P["KP_Smoke"], tf, lambda t: (t.box(-0.10, 0.10, 0.19, 0.195, -0.04, -0.02), t.box(-0.10, 0.10, 0.19, 0.195, 0.02, 0.04)))

# microwave on the sink run by the back door, door facing +x (film 10452: seen square-on from the room)
group("Microwave"); k = A["microwave"]; tf = on(*k["at"], 90)
into(P["KP_White"], tf, lambda t: (t.box(-0.26, 0.26, 0.012, 0.31, -0.19, 0.17),
                                    t.box(-0.26, -0.03, 0.03, 0.065, 0.17, 0.185), t.box(-0.26, -0.03, 0.265, 0.30, 0.17, 0.185),   # door frame round the window
                                    t.box(-0.26, -0.23, 0.065, 0.265, 0.17, 0.185), t.box(-0.06, -0.03, 0.065, 0.265, 0.17, 0.185),
                                    t.box(0.035, 0.26, 0.03, 0.30, 0.17, 0.185)))
into(P["KP_Smoke"], tf, lambda t: t.box(-0.23, -0.06, 0.065, 0.265, 0.172, 0.175))                     # the window, 1 cm behind the frame
into(P["KP_BlackPlastic"], tf, lambda t: (t.box(-0.03, 0.035, 0.03, 0.30, 0.17, 0.18), t.box(0.07, 0.23, 0.2, 0.27, 0.185, 0.197), t.box(-0.24, 0.24, 0.0, 0.012, -0.17, 0.15)))

# the fridge's papers (IMG_4306: drawings, a photo and notes under magnets on the doors), 1 cm off the door face
group("FridgePapers"); F = next(a for a in K["appliances"] if a["type"] == "fridge"); zf = F["z"][0] - 0.03 - 0.010
for i, (x0, y0, w, h, kind) in enumerate(A["fridge_papers"]):
    # the paper: textured (hifi_kitchen_gallery.py fridge_<i>.png, Oct 19 props-quality), UVs across it; seen from -z (the room)
    m = f"KP_Fridge{i}"; MATS[m] = ((1.0, 1.0, 1.0), 0.75, 0.0)
    P[m].face([(x0, y0, zf), (x0 + w, y0, zf), (x0 + w, y0 + h, zf), (x0, y0 + h, zf)], (0, 0, -1), [(1, 0), (0, 0), (0, 1), (1, 1)])
    P["KP_BlackPlastic"].box(x0 + w / 2 - 0.012, x0 + w / 2 + 0.012, y0 + h - 0.03, y0 + h - 0.006, zf - 0.008, zf)   # magnet

# ---------------------------------------------------------------- export
bpy.ops.wm.read_factory_settings(use_empty=True)
mats = {}
for n, (rgb, rough, metal) in MATS.items():
    m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    mats[n] = m
coll = bpy.context.scene.collection
root = bpy.data.objects.new("KitchenProps_HiFi", None); coll.objects.link(root)
import bmesh
objs = {}
for (g, n), p in PARTS.items():
    if not p.f:
        continue
    ob = p.build(coll, mats)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(ob.data); bm.free()
    objs.setdefault(g, []).append(ob)
for g, obs in objs.items():
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = ob.data.name = g; ob.parent = root
    for poly in ob.data.polygons:
        poly.use_smooth = True
    ob.data.set_sharp_from_angle(angle=math.radians(35))
    # artist-pipeline (Oct 19 props-quality): 1.5 mm bevels on hard edges (knife block, appliances, rack bars, turned steps) so
    # edges catch highlights instead of reading as razor-cut primitives; weighted normals keep the big faces flat
    bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = 0.0015; bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40)
    bv.harden_normals = True; ob.modifiers.new("wn", "WEIGHTED_NORMAL").keep_sharp = True
tris = sum(sum(len(f.vertices) - 2 for f in o.data.polygons) for o in coll.objects if o.type == "MESH")
assert tris < 150000, tris
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, tris, "triangles", len(objs), "objects")
