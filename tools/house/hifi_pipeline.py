"""hifi_pipeline: the artist pipeline (.claude/skills/artist-pipeline) as a small API for hifi_*.py scripts (run inside Blender).

Kept out of hifi_lib.py on purpose: build_models.py hashes hifi_lib.py into every model's stamp, so an edit there stales and
rebuilds every generated model (glbs the user's open scene and other agents use). A script that uses this module lists it in
its BUILDS entry instead.

  segments(radius, angle)              curve segment count from the facet chord error (<= 0.5 mm; <= 1 mm per metre over 1 m)
  arc(cx, cy, r, a0, a1)               points of a true arc in a plane (that count, or a fine one for the high-poly)
  Mesh / Mesh.sweep(...)               flat faces and mitred profile sweeps in spec coordinates, UV islands in metres
  pack(meshes, ppm, width)             shelf-pack the islands of one material at a texel density (px per metre), 8 px padding
  to_object(mesh, mat, coll, cuts=)    Blender object: welded, cut by planes, smooth by angle, weighted normals
  displace(obj, scale, depth)          high-poly unevenness (plaster 0.5-1 mm, paint 0.2 mm)
  bake(low, high, w, h, cage, ...)     Cycles CPU bakes high -> low: tangent normal (OpenGL +Y, as Unity), AO, convex-edge mask
  scan(id, res)                        Poly Haven CC0 scan maps (sfm-work/polyhaven/<id>, downloaded on first use)
  compose(...)                         PBR maps: scan tinted to a measured albedo, edge wear, AO grime, roughness variation
  lods(obj, ratios)                    decimated copies name_LOD1.. (or state a reason in the export extras)
  export(path, objs, extras)           GLB with the maps (extras carry the gate's targets); Unity PNGs written by write_unity_maps

Coordinates as hifi_lib: spec (x, y up, z) -> Blender (-x, z, y) -> glTF/glTFast -> Unity (x, y, -z).
"""
import json
import math
import sys
import urllib.request
from pathlib import Path

import bpy
import bmesh
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "sfm-work/polyhaven"
CHORD = 0.0005            # target facet chord error (m); the gate (model_quality.py) fails at 1 mm (1 mm per metre over 1 m radius)
MAX_TURN = math.radians(22.5)   # no facet turns more than this (a 90 degree bevel gets >= 4 segments; the gate fails > 30)
PAD = 8                   # UV island padding, px


# ---------------------------------------------------------------- curves
def segments(radius, angle, fine=False):
    """Segments for an arc of `radius` (m) through `angle` (rad): chord error <= CHORD (and <= 0.5 mm per metre over 1 m),
    no facet turning more than MAX_TURN. fine=True (high-poly): 4x, at least one per 4 mm of arc."""
    if radius <= 0 or angle <= 0:
        return 1
    e = min(CHORD, 0.0005 * max(radius, 1.0))
    n = max(math.ceil(angle / (2 * math.acos(max(-1.0, 1 - e / radius)))), math.ceil(angle / MAX_TURN), 1)
    return max(4 * n, math.ceil(radius * angle / 0.004)) if fine else n


def arc(cx, cy, r, a0, a1, fine=False):
    """[(x, y)] on a circle about (cx, cy) from angle a0 to a1 (rad, 0 = +x, counter-clockwise), both ends included."""
    n = segments(r, abs(a1 - a0), fine)
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def rounded(profile, radius, fine=False):
    """A 2-D polyline with the corner at index i replaced by a true round of `radius` where profile[i] is ('r', x, y)."""
    out = []
    for i, p in enumerate(profile):
        if p[0] != "r":
            out.append(p); continue
        a, b, c = profile[i - 1][-2:], p[1:], profile[i + 1][-2:]
        u = np.subtract(a, b) / np.linalg.norm(np.subtract(a, b)); v = np.subtract(c, b) / np.linalg.norm(np.subtract(c, b))
        half = math.acos(max(-1.0, min(1.0, float(u @ v)))) / 2; t = radius / math.tan(half)
        p0, p1 = np.add(b, u * t), np.add(b, v * t); bis = (u + v) / np.linalg.norm(u + v); cen = np.add(b, bis * radius / math.sin(half))
        a0 = math.atan2(p0[1] - cen[1], p0[0] - cen[0]); a1 = math.atan2(p1[1] - cen[1], p1[0] - cen[0])
        if a1 - a0 > math.pi: a1 -= 2 * math.pi
        if a0 - a1 > math.pi: a1 += 2 * math.pi
        out += arc(cen[0], cen[1], radius, a0, a1, fine)
    return [tuple(q[-2:]) for q in out]


def resample(pts, step):
    """Insert points so no segment of the polyline is longer than `step` (high-poly density for displacement)."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, math.ceil(math.dist(a, b) / step))
        out += [tuple(a[j] + (b[j] - a[j]) * k / n for j in range(len(a))) for k in range(1, n + 1)]
    return out


# ---------------------------------------------------------------- meshes with metric UV islands
class Mesh(Part):
    """hifi_lib.Part with UV islands: uv[face] in metres (island-local), isl[face] = island id."""
    def __init__(self, name, mat):
        super().__init__(name, mat); self.isl = {}; self._next = 0

    def island(self):
        self._next += 1; return self._next

    def face(self, pts, toward, uvs=None, island=None):
        super().face(pts, toward, uvs)
        if island is not None:
            self.isl[len(self.f) - 1] = island

    def sweep(self, path, profile, place, toward_fn, cuts=(), u_start=0.0):
        """A profile swept along a 2-D path in a plane, mitred at every vertex.
        path: [(u, y)] in the plane; profile: [(a, h)] with a = across, out to the path's LEFT, h = out of the plane;
        place(u, y, h) -> spec point; toward_fn(du, dy, dh) -> spec direction for an in-plane/out-of-plane vector.
        The material is on the side the profile winds around: each segment's outward normal is (-dh, da) in profile space.
        cuts: path indices where a new UV island starts (kinks). UVs: u along each profile line, v along the profile."""
        n = len(path)
        def left(i, j):   # unit left normal of segment i -> j
            du, dy = path[j][0] - path[i][0], path[j][1] - path[i][1]; L = math.hypot(du, dy); return (-dy / L, du / L)
        rings = []
        for i in range(n):
            if i == 0: m = left(0, 1); s = 1.0
            elif i == n - 1: m = left(n - 2, n - 1); s = 1.0
            else:
                a, b = left(i - 1, i), left(i, i + 1); m = (a[0] + b[0], a[1] + b[1]); L = math.hypot(*m); m = (m[0] / L, m[1] / L)
                s = 1.0 / max(0.2, m[0] * a[0] + m[1] * a[1])
            rings.append([(path[i][0] + m[0] * s * a, path[i][1] + m[1] * s * a, h) for a, h in profile])
        vlen = [0.0]
        for (a0, h0), (a1, h1) in zip(profile, profile[1:]):
            vlen.append(vlen[-1] + math.hypot(a1 - a0, h1 - h0))
        isl = self.island(); ulen = [u_start] * len(profile)
        for i in range(n - 1):
            if i in cuts:
                isl = self.island(); ulen = [0.0] * len(profile)
            r0, r1 = rings[i], rings[i + 1]
            nxt = [ulen[j] + math.dist(r0[j], r1[j]) for j in range(len(profile))]
            du, dy = path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]; L = math.hypot(du, dy); lu, ly = -dy / L, du / L
            for j in range(len(profile) - 1):
                da, dh = profile[j + 1][0] - profile[j][0], profile[j + 1][1] - profile[j][1]
                if math.hypot(da, dh) < 1e-9: continue
                out = (-dh * lu, -dh * ly, da)     # outward: -dh across (in-plane, along the left normal) + da out of the plane
                self.face([place(*r0[j]), place(*r1[j]), place(*r1[j + 1]), place(*r0[j + 1])], toward_fn(*out),
                          [(ulen[j], vlen[j]), (nxt[j], vlen[j]), (nxt[j + 1], vlen[j + 1]), (ulen[j + 1], vlen[j + 1])], isl)
            ulen = nxt
        return rings


def pack(meshes, ppm, width=2048):
    """Shelf-pack every UV island of these meshes (one texture set) at ppm px per metre into `width` px; returns the height
    (a power of two). Islands longer than the width are an error (cut them with Mesh.sweep cuts)."""
    isl = {}
    for mi, m in enumerate(meshes):
        for fi, k in m.isl.items():
            isl.setdefault((mi, k), []).append(fi)
    boxes = []
    for key, faces in isl.items():
        m = meshes[key[0]]; uv = [p for fi in faces for p in m.uv[fi]]
        u0, v0 = min(p[0] for p in uv), min(p[1] for p in uv); u1, v1 = max(p[0] for p in uv), max(p[1] for p in uv)
        rot = (v1 - v0) > (u1 - u0)
        w, h = ((v1 - v0), (u1 - u0)) if rot else ((u1 - u0), (v1 - v0))
        boxes.append((h * ppm, w * ppm, key, faces, u0, v0, rot))
    boxes.sort(key=lambda b: -b[0])
    x = y = shelf = PAD; place = {}
    for hp, wp, key, faces, u0, v0, rot in boxes:
        if wp + 2 * PAD > width:
            raise ValueError(f"UV island {key} is {wp:.0f} px long, over the {width} px texture: add a cut")
        if x + wp + PAD > width:
            x, y = PAD, y + shelf + PAD; shelf = 0
        place[key] = (x, y); x += wp + 2 * PAD; shelf = max(shelf, hp)
    height = 1 << math.ceil(math.log2(y + shelf + PAD))
    for hp, wp, key, faces, u0, v0, rot in boxes:
        ox, oy = place[key]; m = meshes[key[0]]
        for fi in faces:
            m.uv[fi] = [((((p[1] - v0) if rot else (p[0] - u0)) * ppm + ox) / width,
                         (((p[0] - u0) if rot else (p[1] - v0)) * ppm + oy) / height) for p in m.uv[fi]]
    return height


def to_object(mesh, mat, coll, hard_deg=30.0, weld=1e-6, cuts=()):
    """The mesh as a Blender object: vertices welded (UVs stay per corner), cut by `cuts` [(spec point, spec normal)] (the side
    each normal points to is dropped: a moulding dying into a neighbour, a round kept inside its cut), then smooth shading with
    edges sharper than hard_deg split and weighted normals by face area so big faces stay flat and their bevels catch the light."""
    to_b = lambda p: (-p[0], p[2], p[1])
    me = bpy.data.meshes.new(mesh.name); me.from_pydata([to_b(p) for p in mesh.v], [], mesh.f)
    layer = me.uv_layers.new(name="UVMap")
    for fi, uvs in mesh.uv.items():
        for li, loop in enumerate(me.polygons[fi].loop_indices):
            layer.data[loop].uv = uvs[li]
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
    for pt, nrm in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=to_b(pt), plane_no=to_b(nrm), clear_outer=True)
    bm.to_mesh(me); bm.free()
    me.validate(); me.update()
    ob = bpy.data.objects.new(mesh.name, me); coll.objects.link(ob); me.materials.append(mat)
    me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(hard_deg))
    wn = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); wn.keep_sharp = True; wn.mode = "FACE_AREA"
    apply_modifiers(ob)
    return ob


def apply_modifiers(ob):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects: o.select_set(o == ob)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def displace(ob, scale, depth, seed=0):
    """Surface unevenness on a dense high-poly (clouds noise, `scale` m features, 0..depth m OUT along the normals: never into
    the walls it touches, whose AO would then read 0)."""
    tex = bpy.data.textures.new(f"noise_{ob.name}", "CLOUDS"); tex.noise_scale = scale; tex.noise_depth = 2
    m = ob.modifiers.new("Displace", "DISPLACE"); m.texture = tex; m.strength = depth; m.mid_level = 0.0
    m.texture_coords = "GLOBAL"; m.direction = "NORMAL"
    apply_modifiers(ob)


# ---------------------------------------------------------------- baking (Cycles, CPU)
def _img(name, w, h):
    im = bpy.data.images.new(name, w, h, alpha=False, float_buffer=True); im.colorspace_settings.name = "Non-Color"; return im


def _px(im):
    a = np.empty(im.size[0] * im.size[1] * 4, np.float32); im.pixels.foreach_get(a); return a.reshape(im.size[1], im.size[0], 4)


def bake(low, high, w, h, cage, occluders=(), ao_dist=0.25, edge_dist=0.006, samples=64):
    """Bake high -> low: 'normal' (tangent space, OpenGL +Y like Unity/glTF), 'ao' (high + occluders: the walls round it),
    'edge' (convex-edge mask from inside-AO on the high). cage: ray start in front of the low (from the bevel size); rays reach
    2 x cage. Returns float arrays (h, w, 4), row 0 at the bottom (Blender)."""
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.render.bake.margin = PAD; sc.render.bake.use_selected_to_active = True
    sc.render.bake.cage_extrusion = cage; sc.render.bake.max_ray_distance = 2 * cage
    for o in (low,):   # the low never shades or occludes the high's rays
        o.visible_diffuse = o.visible_glossy = o.visible_shadow = o.visible_transmission = o.visible_volume_scatter = False
    lm = low.active_material; lm.use_nodes = True
    node = lm.node_tree.nodes.new("ShaderNodeTexImage"); lm.node_tree.nodes.active = node
    hm = bpy.data.materials.new(high.name + "_bake"); hm.use_nodes = True; high.data.materials.clear(); high.data.materials.append(hm)
    nt = hm.node_tree; nt.nodes.clear(); outn = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion"); inv = nt.nodes.new("ShaderNodeInvert")
    nt.links.new(em.outputs[0], outn.inputs["Surface"])
    for o in bpy.context.view_layer.objects: o.select_set(o in (low, high))
    bpy.context.view_layer.objects.active = low
    res = {}
    def run(kind, **kw):
        im = _img(f"{low.name}_{kind}", w, h); node.image = im
        bpy.ops.object.bake(type="NORMAL" if kind == "normal" else "EMIT", **kw)
        res[kind] = _px(im).copy()
    sc.cycles.samples = 4
    run("normal", normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
    sc.cycles.samples = samples
    for l in list(nt.links):
        if l.to_node == em: nt.links.remove(l)
    ao.inside = False; ao.only_local = False; ao.inputs["Distance"].default_value = ao_dist; ao.samples = 16
    nt.links.new(ao.outputs["AO"], em.inputs["Color"]); run("ao")
    for l in list(nt.links):
        if l.to_node == em: nt.links.remove(l)
    ao.inside = True; ao.only_local = True; ao.inputs["Distance"].default_value = edge_dist
    nt.links.new(ao.outputs["AO"], inv.inputs["Color"]); nt.links.new(inv.outputs[0], em.inputs["Color"]); run("edge")
    lm.node_tree.nodes.remove(node)
    return res


# ---------------------------------------------------------------- scanned materials
def scan(asset, res="1k", maps=("diff", "nor_gl", "rough")):
    """Poly Haven (CC0) maps as float arrays (h, w, 3), raw values (sRGB-encoded for diff). Downloaded once to
    sfm-work/polyhaven/<asset>/ (gitignored) with a generic User-Agent."""
    d = PH / asset; d.mkdir(parents=True, exist_ok=True); out = {}
    for m in maps:
        f = d / f"{asset}_{m}_{res}.jpg"
        if not f.exists():
            url = f"https://dl.polyhaven.org/file/ph-assets/Textures/jpg/{res}/{asset}/{f.name}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            f.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        im = bpy.data.images.load(str(f)); im.colorspace_settings.name = "Non-Color"
        out[m] = _px(im)[..., :3].copy(); bpy.data.images.remove(im)
    return out


def srgb_to_lin(c):
    c = np.asarray(c, np.float32); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(np.asarray(c, np.float32), 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def tile(a, w, h, scan_m, ppm):
    """The scan tiled over an atlas of w x h px at its true size (scan_m metres per repeat) for an atlas of ppm px per metre."""
    sh, sw = a.shape[:2]
    ys = (np.arange(h) / ppm / scan_m * sh).astype(int) % sh; xs = (np.arange(w) / ppm / scan_m * sw).astype(int) % sw
    return a[ys][:, xs]


def compose(maps, sc, albedo_srgb, ppm, scan_m=1.0, variation=0.5, rough=(0.7, 0.08), wear=0.3, grime=0.25):
    """PBR maps (h, w, 4 float, Blender row order) from the bakes and a scan: base = scan luminance variation around the measured
    film albedo, lighter and smoother on convex edges (wear), darker and rougher in occluded crevices (grime); roughness = the
    scan's variation around rough[0] +- rough[1]; normal = bake + the scan's detail (reoriented normal blend)."""
    h, w = maps["normal"].shape[:2]
    alb = srgb_to_lin(tile(sc["diff"], w, h, scan_m, ppm)); lum = alb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    var = lum / max(float(lum.mean()), 1e-4)
    target = srgb_to_lin(albedo_srgb)
    ao = np.clip(maps["ao"][..., 0], 0, 1); edge = np.clip((maps["edge"][..., 0] - 0.05) / 0.5, 0, 1)
    base = target[None, None, :] * (1 + variation * (var[..., None] - 1))
    base *= (1 - grime * (1 - ao) ** 2)[..., None]          # crevices only (the AO map darkens the rest's indirect light)
    base = base * (1 - wear * edge[..., None]) + np.minimum(base * 1.12 + 0.02, 1.0) * (wear * edge[..., None])
    r = tile(sc["rough"], w, h, scan_m, ppm)[..., 0]
    r = rough[0] + rough[1] * (r - r.mean()) / max(float(r.std()), 1e-4) - 0.12 * wear * edge + 0.08 * grime * (1 - ao)
    nb = maps["normal"][..., :3] * 2 - 1; nd = tile(sc["nor_gl"], w, h, scan_m, ppm) * 2 - 1
    t = nb + np.array([0, 0, 1], np.float32); u = nd * np.array([-1, -1, 1], np.float32)          # RNM blend (Barre-Brisebois/Hill)
    n = t * (t * u).sum(-1, keepdims=True) / np.maximum(t[..., 2:3], 1e-4) - u
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    one = np.ones((h, w), np.float32)
    return {"base_lin": np.dstack([np.clip(base, 0, 1), one]), "rough": np.clip(r, 0.05, 1), "ao": ao,
            "normal": np.dstack([n * 0.5 + 0.5, one]), "edge": edge}


def detail_map(sc_hi, size=1024):
    """HDRP detail map from a high-resolution scan: R albedo (0.5 = none), G normal y, B smoothness (0.5 = none), A normal x."""
    a = sc_hi["diff"][:size, :size]; lum = srgb_to_lin(a) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    n = sc_hi["nor_gl"][:size, :size]; r = sc_hi["rough"][:size, :size, 0]
    return np.dstack([np.clip(0.5 + 0.5 * (lum / lum.mean() - 1), 0, 1), n[..., 1], np.clip(0.5 - 0.5 * (r - r.mean()) / max(r.std(), 1e-4) * 0.2, 0, 1), n[..., 0]])


def to_image(name, arr, path=None, colorspace="Non-Color"):
    """A Blender image from a float array (h, w, 1|3|4), values stored as given (Non-Color); saved as PNG when path is given."""
    a = np.asarray(arr, np.float32)
    if a.ndim == 2: a = a[..., None]
    if a.shape[2] == 1: a = np.dstack([a, a, a])
    if a.shape[2] == 3: a = np.dstack([a, np.ones(a.shape[:2], np.float32)])
    im = bpy.data.images.new(name, a.shape[1], a.shape[0], alpha=True); im.colorspace_settings.name = colorspace   # before the pixels
    im.pixels.foreach_set(np.clip(a, 0, 1).ravel())
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        im.filepath_raw = str(path); im.file_format = "PNG"; im.save()
    return im


def pbr_material(name, mp, extras):
    """A glTF-exportable material on the composed maps: base (sRGB), ORM (R occlusion, G roughness, B metal), normal."""
    base = to_image(f"{name}_base", np.dstack([lin_to_srgb(mp["base_lin"][..., :3]), mp["base_lin"][..., 3]]), colorspace="sRGB")
    z = np.zeros_like(mp["rough"]); orm = to_image(f"{name}_orm", np.dstack([mp["ao"], mp["rough"], z]))
    nrm = to_image(f"{name}_normal", mp["normal"])
    for im in (base, orm, nrm): im.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tb = nt.nodes.new("ShaderNodeTexImage"); tb.image = base; nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
    to = nt.nodes.new("ShaderNodeTexImage"); to.image = orm; sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs["Color"]); nt.links.new(sep.outputs["Green"], b.inputs["Roughness"]); nt.links.new(sep.outputs["Blue"], b.inputs["Metallic"])
    grp = bpy.data.node_groups.get("glTF Material Output") or bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
    if "Occlusion" not in [s.name for s in grp.interface.items_tree]:
        grp.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = grp; nt.links.new(sep.outputs["Red"], g.inputs["Occlusion"])
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = nrm; nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    for k, v in extras.items(): m[k] = v
    return m


def write_unity_maps(folder, name, mp, detail, extras):
    """HDRP Lit maps for SpecGreybox.BakedMat: <name>_base (sRGB), _mask (R metal, G AO, B detail mask, A smoothness), _normal,
    _detail, and <name>.json (detail tiling and the gate's targets). Rows flipped to image order by Blender's PNG writer."""
    d = Path(folder); z = np.zeros_like(mp["rough"])
    to_image(f"u_{name}_base", np.dstack([lin_to_srgb(mp["base_lin"][..., :3]), np.ones_like(z)]), d / f"{name}_base.png")
    to_image(f"u_{name}_mask", np.dstack([z, mp["ao"], np.ones_like(z), 1 - mp["rough"]]), d / f"{name}_mask.png")
    to_image(f"u_{name}_normal", mp["normal"], d / f"{name}_normal.png")
    to_image(f"u_{name}_detail", detail, d / f"{name}_detail.png")
    (d / f"{name}.json").write_text(json.dumps(extras, indent=1) + "\n")


# ---------------------------------------------------------------- LODs and export
def lods(ob, ratios=(0.5, 0.2)):
    """Decimated copies name_LOD1, name_LOD2 (collapse, normals kept by the weighted-normal data on the copies)."""
    out = []
    for i, r in enumerate(ratios, 1):
        c = ob.copy(); c.data = ob.data.copy(); c.name = f"{ob.name}_LOD{i}"; ob.users_collection[0].objects.link(c)
        d = c.modifiers.new("Decimate", "DECIMATE"); d.ratio = r; apply_modifiers(c); out.append(c)
    return out


def export(path, objs, extras):
    """GLB of these objects under one root carrying `extras` (artist_pipeline, lod_reason, ...); materials keep theirs."""
    root = bpy.data.objects.new(Path(path).stem + "_Root", None); bpy.context.scene.collection.objects.link(root)
    for k, v in extras.items(): root[k] = v
    for o in objs: o.parent = root
    for o in bpy.context.view_layer.objects: o.select_set(o in objs or o == root)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True, export_apply=True, use_selection=True,
                              export_extras=True, export_tangents=True, export_image_format="AUTO")
