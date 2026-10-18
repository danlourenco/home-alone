"""hifi_bare_trees: realistic bare winter trees for the yard and street (Oct 18 2026; decoration, replaces the WinterNeighborhood's
stick trees and the treehouse's stick crown). User: "use realistic assets or 3d models for the bare trees instead of the simple stick
figures". Look from the film: 4382 (front: tall straight trunks, crooked oak limbs high up, a haze of fine twigs), 6810 (rear: forest-
grown trunks, crowns far above the treehouse), 4380-4384, 6399, 9435, 11050; Chicago-suburb December oaks, elms, maples.

Recursive growth (Weber-Penn style, a few knobs per species in SPECIES): a trunk with root flare and a clear bole, limbs at the
species' angles with phyllotaxis, each level bending (crookedness), turning up or drooping (tropism) and tapering, down to fine
twigs. Every branch is ONE continuous tapered tube (parallel-transport rings, smooth normals, bark UVs aspect-correct round the
branch); a child starts on its parent's axis with a radius under the parent's there, so forks have no gaps. Upward faces of limbs
thicker than SNOW_R take the snow material (a light top dusting; no extra geometry, nothing coplanar).

LODs per tree: LOD0 everything; LOD1 drops the twigs (the last level, slightly thickened, carries the haze) and halves rings/segments;
LOD2 trunk + limbs + coarse secondaries. Unity (SpecGreybox.Trees) puts them in a LODGroup.

Objects (spec x, y up, z; tree base at the origin, LOD0 height = ref height; Unity scales to the stick tree's height):
  <species><A|B>_LOD0..2  for species oak, elm, maple, ash
  TreehouseCrown_LOD0..2  the treehouse tree above the cabin, at its WORLD place (spec/dressing/treehouse.json trunk; joins the
                          trunk hifi_treehouse.py builds up to CROWN_JOIN above grade)
Materials: BT_BarkRough (oak, ash: Poly Haven bark_willow_02), BT_BarkBrown (elm, maple, treehouse: bark_brown_02), BT_Snow.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_bare_trees.py
  python3 tools/house/hifi_bare_trees.py --check      # no Blender: growth self-check (fork gaps, budgets, rope clearance)
-> unity/HomeAlone/Assets/Models/Foyer/BareTrees.glb
"""
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/BareTrees.glb"
TH = json.loads((ROOT / "spec/dressing/treehouse.json").read_text())
CROWN_JOIN = 6.8      # m above grade where the treehouse's lathe trunk hands over to the generated tree (cabin roof ~5.6)
SNOW_R = 0.035        # limbs thicker than this (m) get snow on faces whose normal.y > SNOW_NY
SNOW_NY = 0.62
BUDGET = (120000, 25000, 5000)   # triangles per LOD, per tree (perf target: M3 Pro, ~50 trees mostly at LOD1/2)

# Per level (0 trunk .. 4 twigs): n = children per metre of parent, down = angle from the parent (deg) +- var, len = child length
# relative to the parent (level 1: to the tree height), rad = child radius / parent radius there, curv = crookedness per segment,
# trop = upward (+) / droop (-) pull per segment at the base -> tip, seg = segment length (m).
SPECIES = {
    # bur/white oak, forest grown (4382 right, 6810): tall clear bole, few big crooked limbs spreading wide, dense twig haze
    "oak": dict(height=18.0, rbase=0.48, bole=0.42, flare=0.55, shape="spherical", lean=0.03, trunk_top=0.62, trunk_curv=0.05,
                rough=True,
                L=[None,
                   dict(count=9, down=60, var=14, len=0.64, rad=0.62, curv=0.34, trop=(0.035, -0.02), seg=0.45, slope=20),
                   dict(n=1.6, down=48, var=20, len=0.50, rad=0.50, curv=0.32, trop=(0.03, -0.01), seg=0.35),
                   dict(n=2.8, down=45, var=20, len=0.42, rad=0.50, curv=0.30, trop=(0.04, 0.0), seg=0.25),
                   dict(n=3.8, down=42, var=18, len=0.40, rad=0.55, curv=0.25, trop=(0.05, 0.02), seg=0.20)]),
    # American elm (classic vase): trunk splits low into ascending leaders that arch out, tips weeping
    "elm": dict(height=19.0, rbase=0.38, bole=0.27, flare=0.45, shape="vase", lean=0.02, trunk_top=0.33, trunk_curv=0.04,
                rough=False, fork=4,
                L=[None,
                   dict(count=0, down=24, var=8, len=0.72, rad=0.78, curv=0.10, trop=(0.06, -0.05), seg=0.5),
                   dict(n=1.5, down=40, var=15, len=0.42, rad=0.48, curv=0.22, trop=(0.02, -0.05), seg=0.35),
                   dict(n=3.0, down=42, var=18, len=0.40, rad=0.50, curv=0.25, trop=(0.0, -0.04), seg=0.25),
                   dict(n=5.5, down=40, var=18, len=0.36, rad=0.55, curv=0.22, trop=(0.0, -0.03), seg=0.20)]),
    # sugar/silver maple: central trunk most of the way, many ascending limbs, oval crown, dense
    "maple": dict(height=15.0, rbase=0.30, bole=0.24, flare=0.40, shape="flame", lean=0.03, trunk_top=0.86, trunk_curv=0.06,
                  rough=False,
                  L=[None,
                     dict(count=18, down=50, var=10, len=0.56, rad=0.50, curv=0.18, trop=(0.06, 0.01), seg=0.4, slope=24),
                     dict(n=2.0, down=40, var=15, len=0.48, rad=0.50, curv=0.22, trop=(0.04, 0.01), seg=0.3),
                     dict(n=3.4, down=40, var=15, len=0.42, rad=0.50, curv=0.22, trop=(0.04, 0.02), seg=0.22),
                     dict(n=6.0, down=38, var=15, len=0.36, rad=0.55, curv=0.20, trop=(0.05, 0.03), seg=0.18)]),
    # ash / hackberry, the tall straight background trunks (6810): long clear bole, small high crown
    "ash": dict(height=21.0, rbase=0.42, bole=0.55, flare=0.45, shape="spherical", lean=0.02, trunk_top=0.80, trunk_curv=0.03,
                rough=True,
                L=[None,
                   dict(count=8, down=50, var=14, len=0.34, rad=0.50, curv=0.26, trop=(0.04, 0.0), seg=0.45, slope=24),
                   dict(n=1.6, down=44, var=18, len=0.50, rad=0.50, curv=0.28, trop=(0.03, 0.0), seg=0.32),
                   dict(n=3.4, down=42, var=18, len=0.42, rad=0.50, curv=0.26, trop=(0.04, 0.01), seg=0.24),
                   dict(n=6.0, down=40, var=18, len=0.34, rad=0.55, curv=0.22, trop=(0.05, 0.02), seg=0.20)]),
}
TIP_R = [0.03, 0.012, 0.006, 0.0035, 0.0018]    # tip radius per level (m)


# ---------------------------------------------------------------- vector helpers
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    n = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)
def perp(d):
    u = cross(d, (0.0, 1.0, 0.0))
    return norm(u if dot(u, u) > 1e-6 else cross(d, (1.0, 0.0, 0.0)))


def shape_ratio(kind, r):
    """crown envelope (Weber-Penn): r = 0 at the crown's base .. 1 at the top -> relative limb length"""
    if kind == "spherical": return 0.25 + 0.75 * math.sin(math.pi * min(max(r, 0.0), 1.0) * 0.92 + 0.12)
    if kind == "flame": return 0.3 + 0.7 * (r / 0.35 if r < 0.35 else (1 - r) / 0.65)
    return 1.0


class Branch:
    __slots__ = ("pts", "rad", "level", "parent", "t0")

    def __init__(self, level, parent=None, t0=0.0):
        self.pts, self.rad, self.level, self.parent, self.t0 = [], [], level, parent, t0

    def at(self, t):
        """point, radius and direction at fraction t of the arc"""
        f = t * (len(self.pts) - 1); i = min(int(f), len(self.pts) - 2); w = f - i
        p = add(mul(self.pts[i], 1 - w), mul(self.pts[i + 1], w))
        return p, self.rad[i] * (1 - w) + self.rad[i + 1] * w, norm(sub(self.pts[i + 1], self.pts[i]))

    def length(self):
        return sum(math.dist(a, b) for a, b in zip(self.pts, self.pts[1:]))


def grow_tube(br, p0, d, length, r0, tip, seg, curv, trop, rng, floor_y, taper=1.0):
    n = max(3, int(round(length / seg)))
    br.pts, br.rad = [p0], [r0]
    for i in range(1, n + 1):
        t = i / n
        j = (rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))
        up = trop[0] + (trop[1] - trop[0]) * t
        d = norm(add(add(d, mul(j, curv * 0.35)), (0.0, up, 0.0)))
        p = add(br.pts[-1], mul(d, length / n))
        if p[1] < floor_y:                                   # never into the ground / onto the cabin roof: turn up
            d = norm(add(d, (0.0, 0.6, 0.0))); p = add(br.pts[-1], mul(d, length / n))
        br.pts.append(p); br.rad.append(tip + (r0 - tip) * (1 - t) ** taper)
    return br


def grow_children(sp, parent, rng, out, floor_y, tree_h, t_from=0.0):
    lv = parent.level + 1
    if lv > 4: return
    P = sp["L"][lv]; L = parent.length()
    count = P["count"] if lv == 1 else max(1, int(round(P["n"] * L * (1 - t_from)))) if P["n"] else 0
    rot = rng.uniform(0, 2 * math.pi)
    for k in range(count):
        t = t_from + (1 - t_from) * (k + rng.uniform(0.2, 0.8)) / count
        t = min(t, 0.97)
        p, rp, dp = parent.at(t)
        rot += math.radians(137.5 + rng.uniform(-20, 20))
        u = perp(dp); v = cross(dp, u); ax = add(mul(u, math.cos(rot)), mul(v, math.sin(rot)))
        rel = (t - t_from) / max(1 - t_from, 1e-6)
        a = math.radians(P["down"] + rng.uniform(-P["var"], P["var"]) + P.get("slope", 0) * (0.5 - rel))
        d = norm(add(mul(dp, math.cos(a)), mul(ax, math.sin(a))))
        if lv == 1:
            ln = tree_h * P["len"] * shape_ratio(sp["shape"], rel) * rng.uniform(0.8, 1.15)
        else:
            ln = L * P["len"] * (1 - 0.55 * t) * rng.uniform(0.75, 1.2)
        r0 = min(max(rp * P["rad"] * rng.uniform(0.85, 1.1), TIP_R[lv] * 1.6), rp * 0.85)
        if ln < 0.08 or r0 < TIP_R[lv] * 1.05: continue      # parent too thin here for this child
        b = grow_tube(Branch(lv, parent, t), p, d, ln, r0, TIP_R[lv], P["seg"], P["curv"], P["trop"], rng, floor_y)
        out.append(b)
        grow_children(sp, b, rng, out, floor_y, tree_h, 0.12 if lv < 3 else 0.2)


def grow_tree(name, seed, base=(0.0, 0.0, 0.0), h=None, join=None, floor_y=0.4):
    """join = (y0, r0): a crown on an existing trunk (the treehouse): the trunk starts at y0 above base with radius r0, no flare"""
    sp = SPECIES[name]; rng = random.Random(seed)
    H = h or sp["height"] * rng.uniform(0.93, 1.07)
    trunk = Branch(0)
    lean = norm((rng.uniform(-1, 1) * sp["lean"], 1.0, rng.uniform(-1, 1) * sp["lean"]))
    y0 = join[0] if join else -0.35                           # below grade: no gap on sloped lots
    r0 = join[1] if join else sp["rbase"] * H / sp["height"]
    tl = H * sp["trunk_top"] - y0
    grow_tube(trunk, add(base, (0.0, y0, 0.0)), lean, tl, r0, TIP_R[0] * (3.0 if sp.get("fork") else 1.0), 0.6,
              sp["trunk_curv"], (0.0, 0.0), rng, base[1] + floor_y, taper=0.45)
    out = [trunk]
    bole = (H * sp["bole"] - y0) / tl
    if sp.get("fork"):                                       # elm: codominant leaders from the fork, the trunk itself one of them
        P = sp["L"][1]
        for k in range(sp["fork"]):
            t = bole + rng.uniform(-0.03, 0.05)
            p, rp, dp = trunk.at(t)
            az = 2 * math.pi * k / sp["fork"] + rng.uniform(-0.4, 0.4)
            a = math.radians(P["down"] + rng.uniform(-P["var"], P["var"]))
            d = norm((math.sin(a) * math.cos(az), math.cos(a), math.sin(a) * math.sin(az)))
            b = grow_tube(Branch(1, trunk, t), p, d, H * P["len"] * rng.uniform(0.85, 1.1), rp * P["rad"], TIP_R[1],
                          P["seg"], P["curv"], P["trop"], rng, base[1] + floor_y)
            out.append(b); grow_children(sp, b, rng, out, base[1] + floor_y, H, 0.15)
    else:
        grow_children(sp, trunk, rng, out, base[1] + floor_y, H, bole)
    return out, H


# ---------------------------------------------------------------- meshing
def sides_for(r, lod):
    s = 24 if r > 0.25 else 16 if r > 0.15 else 10 if r > 0.07 else 6 if r > 0.03 else 4 if r > 0.008 else 3
    return max(3, s // (1, 2, 3)[lod]) if s > 3 else 3


class Mesh:
    def __init__(self):
        self.v, self.uv, self.f, self.mat = [], [], [], []   # mat: 0 bark, 1 snow

    def tris(self):
        return sum(len(f) - 2 for f in self.f)


def mesh_branch(m, br, lod, flare=None, sides=None, r_scale=1.0):
    step = (1, 2, 3)[lod] if br.level > 0 else 1
    idx = list(range(0, len(br.pts), step))
    if idx[-1] != len(br.pts) - 1: idx.append(len(br.pts) - 1)
    pts = [br.pts[i] for i in idx]; rad = [br.rad[i] * r_scale for i in idx]
    n = sides or sides_for(rad[0], lod)
    reps = max(1, round(2 * math.pi * rad[0] / 0.9))        # bark tiles round the branch (~0.9 m per tile)
    circ = max(2 * math.pi * rad[0], 1e-3)
    T = [norm(sub(pts[min(i + 1, len(pts) - 1)], pts[max(i - 1, 0)])) for i in range(len(pts))]
    N = perp(T[0]); rings = []; s = 0.0
    for i, p in enumerate(pts):
        if i:
            N = norm(sub(N, mul(T[i], dot(N, T[i])))); s += math.dist(pts[i - 1], p)
        B = cross(T[i], N); ring = len(m.v)
        last = i == len(pts) - 1 and br.level > 0
        for k in range(n + 1):
            th = 2 * math.pi * k / n
            r = rad[i] if not last else rad[i] * 0.6
            if flare: r *= flare(p[1] - pts[0][1], th)
            m.v.append(add(p, add(mul(N, r * math.cos(th)), mul(B, r * math.sin(th)))))
            m.uv.append((reps * k / n, s * reps / circ))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            q = (a + k, a + k + 1, b + k + 1, b + k)
            m.f.append(q); m.mat.append(snow_face(m, q, rad[0]))
    if br.level > 0:                                        # pointed tip
        a = rings[-1]; tip = len(m.v)
        m.v.append(add(pts[-1], mul(T[-1], rad[-1] * 2))); m.uv.append((0.5 * reps, (s + rad[-1] * 2) * reps / circ))
        for k in range(n):
            m.f.append((a + k, a + k + 1, tip)); m.mat.append(0)


def snow_face(m, q, r):
    if r < SNOW_R: return 0
    a, b, c = m.v[q[0]], m.v[q[1]], m.v[q[2]]
    nrm = norm(cross(sub(b, a), sub(c, a)))
    return 1 if nrm[1] > SNOW_NY else 0


def trunk_flare(sp):
    amp = sp["flare"]
    def f(h, th):   # root flare with buttress lobes (6810: the base spreads ~0.8 m)
        e = math.exp(-max(h - 0.35, 0.0) / 0.55)
        return 1 + amp * e * (0.55 + 0.45 * max(0.0, math.cos(5 * th + 0.7)) ** 2)
    return f


def mesh_tree(branches, sp, lod, join_sides=None):
    m = Mesh()
    last = 4 if lod == 0 else 3 if lod == 1 else 2
    for b in branches:
        if b.level > last: continue
        if b.level == 0:
            mesh_branch(m, b, 0 if lod < 2 else 1, None if join_sides else trunk_flare(sp), sides=join_sides)
        else:
            # LOD1/2: the new last level carries the dropped twigs' haze a little thicker (ponytail: no twig cards/impostors;
            # add billboards if the street's far trees ever cost too much)
            mesh_branch(m, b, lod, r_scale=1.35 if (lod and b.level == last) else 1.0)
    return m


HOUSE_BOX = ((-9.7, 12.0), (-3.4, 23.7), 7.4)   # spec x, spec z, world y top: the house + exterior shell (Exterior.glb bounds)


def prune(branches, box=HOUSE_BOX, pad=0.4):
    """drop every branch (and what grows from it) that enters the box: a tree beside a house is pruned off the roof and walls"""
    (x0, x1), (z0, z1), ytop = box; gone = set()
    for b in branches:
        if b.level and (id(b.parent) in gone or any(x0 - pad < p[0] < x1 + pad and z0 - pad < p[2] < z1 + pad and p[1] < ytop + pad for p in b.pts)):
            gone.add(id(b))
    return [b for b in branches if id(b) not in gone]


def treehouse_crown():
    K, G = TH["trunk"], TH["site"]["grade_y"]
    tx, tz = K["at"]
    r = K["r"] * 1.0 + 0.008                                 # hifi_treehouse's lathe is K.r at 6-9 m: this tube covers its top
    br, H = grow_tree("oak", 61, base=(tx, G, tz), h=18.5, join=(CROWN_JOIN, r), floor_y=CROWN_JOIN + 0.6)
    br = prune(br)   # the kitchen wing is 3.5 m away: limbs toward the house start above its roof (film 6810: the crown is high)
    # no limbs below the join (the cabin): the oak's bole (0.42 x 18.5 = 7.8 m) already starts them above the roof
    assert all(b.level == 0 or b.pts[0][1] >= G + CROWN_JOIN for b in br), "treehouse crown limb below the join"
    return br


def rope_clearance(branches):
    R = TH["rope"]; a = R["window"]; b = R["trunk"]
    best = 9e9
    for br in branches:
        if br.level == 0: continue
        for p in br.pts[::2]:
            ab = sub(b, a); t = max(0.0, min(1.0, dot(sub(p, a), ab) / dot(ab, ab)))
            best = min(best, math.dist(p, add(a, mul(ab, t))))
    return best


def check(trees):
    """no gaps at forks: a child's first ring lies inside its parent's tube; budgets per LOD"""
    bad = 0
    for name, br, H, ms in trees:
        for b in br:
            if b.parent is None: continue
            p, rp, _ = b.parent.at(b.t0)
            if math.dist(b.pts[0], p) > 1e-6 or b.rad[0] > rp * 0.86 + 1e-9:
                bad += 1
        tris = [m.tris() for m in ms]
        over = [t > lim for t, lim in zip(tris, BUDGET)]
        print(f"{'FAIL' if any(over) else 'ok  '} {name}: {H:.1f} m, {len(br)} branches, tris LOD0/1/2 {tris[0]}/{tris[1]}/{tris[2]}")
        bad += sum(over)
    return bad


def build_all():
    trees = []
    for i, name in enumerate(SPECIES):
        for v, seed in (("A", 11 + i * 7), ("B", 53 + i * 5)):
            br, H = grow_tree(name, seed)
            trees.append((f"{name}{v}", br, H, [mesh_tree(br, SPECIES[name], l) for l in range(3)]))
    cr = treehouse_crown()
    trees.append(("TreehouseCrown", cr, 18.5, [mesh_tree(cr, SPECIES["oak"], l, join_sides=24) for l in range(3)]))
    return trees


def export(trees):
    import bpy
    for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
    coll = bpy.data.collections.new("BareTrees"); bpy.context.scene.collection.children.link(coll)
    def mat(n, rgb, rough):
        m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1.0); b.inputs["Roughness"].default_value = rough; return m
    mats = {"BT_BarkRough": mat("BT_BarkRough", (0.20, 0.18, 0.16), 0.95), "BT_BarkBrown": mat("BT_BarkBrown", (0.22, 0.18, 0.15), 0.95),
            "BT_Snow": mat("BT_Snow", (0.85, 0.87, 0.90), 0.7)}
    to_b = lambda p: (-p[0], p[2], p[1])                     # spec -> Blender (hifi_lib)
    for name, br, H, ms in trees:
        sp = SPECIES.get(name[:-1], {})
        bark = "BT_BarkRough" if sp.get("rough") else "BT_BarkBrown"
        for lod, m in enumerate(ms):
            me = bpy.data.meshes.new(f"{name}_LOD{lod}")
            me.from_pydata([to_b(p) for p in m.v], [], m.f)
            uvl = me.uv_layers.new(name="UVMap")
            loops = [m.uv[i] for f in m.f for i in f]
            uvl.data.foreach_set("uv", [c for uv in loops for c in uv])
            me.materials.append(mats[bark]); me.materials.append(mats["BT_Snow"])
            me.polygons.foreach_set("material_index", m.mat)
            me.polygons.foreach_set("use_smooth", [True] * len(m.f))
            me.update(); me.validate()
            ob = bpy.data.objects.new(f"{name}_LOD{lod}", me); coll.objects.link(ob)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False, export_apply=True)
    print("hifi_bare_trees: wrote", OUT)


if __name__ == "__main__":
    trees = build_all()
    bad = check(trees)
    clr = rope_clearance(trees[-1][1])
    print(f"{'ok  ' if clr > 0.5 else 'FAIL'} treehouse crown: nearest limb to the zipline rope {clr:.2f} m")
    bad += clr <= 0.5
    print("total LOD0 tris (one of each):", sum(t[3][0].tris() for t in trees))
    if "--check" in sys.argv:
        sys.exit(1 if bad else 0)
    export(trees)
