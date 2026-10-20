"""purchased_rugs: the user's two Sketchfab Persian rugs (Oct 17 downloads), decimated, normal-mapped and fitted to the measured rug
boxes. Writes ONLY gitignored files under unity/HomeAlone/Assets/Purchased/ (the downloads are CC BY 4.0: credits in CREDITS.md):
  Purchased/Rugs/<name>_lod.glb   the decimated rug with its normal maps (fitted, spec space as below)
  Purchased/PurchasedRug.glb      the rugs fitted: FrontRug (the Nain, foyer), LivingRug (the Heriz, living room) and Runner (the
                                  foyer floor runner cut from the Heriz photo, below)
Without the downloads the build keeps the generated rugs (hifi_foyer_props.py, hifi_living.py).

Sources (mfb64, Sketchfab, CC BY 4.0; author/licence from each GLB's asset.extras):
  persian_nain_carpet.glb        body 3.99 x 3.06 m x 5 mm (1980 tris, albedo only, 1024 x 2048), fringe 626k tris (~7800 strands)
  fine_persian_heriz_carpet.glb  body 3.86 x 2.87 m x 6 mm (2972 tris, albedo only, 1024 x 1024), fringe 625k tris
628k triangles hung the build's triangle checks on Oct 17 (STATUS 8r). Here:
  - fringe: every 4th strand kept (~1950 a rug; 1.6 mm apart after the fit, still a dense band), each collapse-decimated to ~15
    triangles (FRINGE_TRIS a rug). Decimation alone stops at ~9 triangles a strand (70k) and turns strands into shards. A Cycles
    normal bake from the original strands onto the decimated ones was tried (Oct 18) and dropped: it DARKENED the fringe (the
    source's double-sided strands have inconsistent normals), and the decimated strands read as cords without it
  - body: the source body is a flat 5 mm slab with no pile geometry to bake from, so its normal map is DERIVED from the albedo
    (luminance high-pass as height: knots and motif edges catch the light); stated, not claimed as a bake
Fits (non-uniform, kept rather than cropped: a border-preserving crop truncated the Nain's oval medallion, see
~/.cache/home-alone-2/captures/overnight11-nain-crop-vs-squash.png):
  FrontRug  spec/dressing/foyer_props.json front_rug (x 7.48-8.90, z 8.60-10.72), fringe at the z ends (film 1616, 31). Recoloured
            to the film's palette (Oct 20, nain_film_recolor: green field, cream border, red-brown guards; film 30-35, 1616, 1690). The photo is 1:1.92 (borders to borders); at 1.42 x 2.12 (1:1.49) motifs are 1.28x wide.
  LivingRug spec/dressing/living.json rug (x 2.90-6.56, z 12.45-15.19; the red oriental of Marina f3/f165, film 10600): the Heriz
            is 1:1.345, the box 1:1.336: near-uniform (x0.93 along, x0.95 across). Fringe at the x ends (the long axis), INSIDE the
            box (body shortened by it): beyond x 2.90 it ran through the nutcracker standing at the rug's end (clash gate).
  Runner    spec/dressing/foyer_props.json runner (x 3.65-7.06, z 8.58-9.32; film 1616: red Oriental, dark borders, cream fringe).
            Oct 18, user: the generated runner looked cartoonish beside the bought rugs; "just start off with the rug as is, even if the
            colors aren't perfect". Its photo is the Heriz's cut into runner proportions at ONE scale (nothing stretched): the side
            borders mirror-tiled along, the end border band + corners at each end, the field's medallion band tiled 4x with
            alternate flips (seamless mirror joins); 0.14 m borders. Pile normal derived as above; the Heriz's own fringe strands
            (central 0.74 m of each end, native size) at the runner's ends, outside the box like the generated one, cream (film).
Height: body 2-12 mm above the floor (the generated rugs' top is 12 mm: the living train sits on it), fringe squeezed into the
same 1 cm (overlays >= 1 cm proud: zfight-check).

  /Applications/Blender.app/Contents/MacOS/Blender -b --disable-autoexec --factory-startup -P tools/house/purchased_rugs.py
"""
import json
import tempfile
from pathlib import Path

import bmesh
import bpy
import mathutils
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PUR = ROOT / "unity/HomeAlone/Assets/Purchased"
FRINGE_TRIS = 30000                # per rug, after decimation (body adds 2-3k): two rugs ~65k in one file, budget 150k
KEEP = 4                           # every 4th strand (thin_strands)
Y0, Y1 = 0.002, 0.012              # body bottom / top above the ground floor (spec y)
FP = json.loads((ROOT / "spec/dressing/foyer_props.json").read_text())["front_rug"]
LV = json.loads((ROOT / "spec/dressing/living.json").read_text())["rug"]
FR = json.loads((ROOT / "spec/dressing/foyer_props.json").read_text())["runner"]
RUGS = [  # name, source, spec box, the spec axis the fringed (long) ends lie on, fringe colour (linear) or None = the source's,
          # fringe inside the box (True: the body is shortened by the fringe; the living rug's box ends at the nutcrackers)
    ("FrontRug", "persian_nain_carpet", FP["x"], FP["z"], "z", (0.80, 0.76, 0.66), False),   # front_rug's box is the body (film 1616)
    ("LivingRug", "fine_persian_heriz_carpet", LV["x"], LV["z"], "x", None, True),
]


def coords(o):
    a = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", a); a = a.reshape(-1, 3)
    M = np.array(o.matrix_world); return a @ M[:3, :3].T + M[:3, 3]


def tris(objs):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)


def select(objs, active):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = active


def image_png(name, px, w, h):
    """A packed, non-colour image from a float array (h, w, 4), rows bottom-up as Blender stores them."""
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(px.astype(np.float32).ravel())
    img.file_format = "PNG"; img.pack()
    return img


def pile_normal(albedo, name):
    """Tangent-space normal from the albedo's luminance high-pass (knots, motif edges): OpenGL green (+v up), as glTF expects."""
    w, h = albedo.size
    a = np.empty(w * h * 4, np.float32); albedo.pixels.foreach_get(a); a = a.reshape(h, w, 4)
    lum = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    def blur(x, r):
        k = np.ones(2 * r + 1, np.float32) / (2 * r + 1)
        x = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="wrap"), k, "valid"), 0, x)
        return np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="wrap"), k, "valid"), 1, x)
    hgt = blur(lum - blur(lum, 12), 1)            # motif-scale relief only, no slope across the whole rug
    hgt /= max(1e-6, np.percentile(np.abs(hgt), 98))
    s = 0.6                                       # strength: the pile reads at grazing light, not embossed
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * s
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * s
    n = np.dstack([-dx, -dy, np.ones_like(dx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    out = np.dstack([n * 0.5 + 0.5, np.ones((h, w, 1), np.float32)])
    return image_png(name, out, w, h)


def set_normal(mat, img):
    nt = mat.node_tree; bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])


# The film's front rug (Oct 20): film 30-35 (opening, night, from the landing) show it whole: a DARK GREEN field, all-over floral
# with a small cream/red medallion, a cream-gold border with red motifs between red-brown guards; film 1616/1690 (day) show only its
# near border (cream + red-brown guard: the "cream field" read on Oct 17 was that border). The Nain's design is kept and its colours
# remapped to that palette (nain_film_recolor). Film colours, sRGB as graded: border cream/tan/brown/red and the guard from 1616+1690
# rows 1030-1058 (k-means); the field green from 31/33/34/35 (pixels G >= R in x 420-880, y 640-780), white-balanced night -> day on
# the rug's own undyed fringe (31: x 330-372 y 580-720; 1616: the corner tassels), so it is in the day frames' grading. The targets
# are used RELATIVE to the film's cream (x the Nain's cream albedo): exposure-free. Spread: the night border under the fringe
# balance reads (119, 100, 95) against the day frames' (149, 137, 124), so the green is +-20% in brightness.
def _lin(s): return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
def _srgb(l): return np.where(l <= 0.0031308, l * 12.92, 1.055 * np.clip(l, 0, None) ** (1 / 2.4) - 0.055)
NAIN_K = np.array([(249, 246, 231), (221, 209, 198), (194, 175, 162), (136, 130, 130), (73, 73, 82), (16, 11, 17)]) / 255  # k-means
FILM = {k: np.array(v) / 255 for k, v in dict(cream=(149, 137, 124), tan=(127, 111, 98), brown=(105, 84, 74), guard=(89, 67, 61),
        red=(64, 17, 24), deep=(31, 6, 10), green=(32, 47, 36)).items()}
NAIN_FILM = {  # each Nain colour (NAIN_K order: cream, warm grey, tan, grey, navy, black) -> a film colour, by region
    "field": ("green", "tan", "guard", "cream", "red", "deep"),
    "border": ("cream", "tan", "brown", "guard", "red", "deep"),
    "guard": ("guard", "guard", "red", "red", "deep", "deep"),
}
NAIN_FIELD, NAIN_GUARDS = (172, 276), [((26, 68), (52, 104)), ((146, 238), (172, 276))]  # px insets on the 1024 x 2048 photo


def nain_film_recolor(a, field=NAIN_FIELD, guards=NAIN_GUARDS):
    """a (h, w, 3) sRGB 0-1 (either row order: the regions are mirror-symmetric). field: the field's inset (x, y) px; guards: each
    blue guard band as the insets of its outer and inner edges. Soft nearest-colour remap; within a colour the pixel's luminance
    ratio is kept (knots, wear, photo shading). Outside the outer guard (the photo's margin) is left as is."""
    h, w = a.shape[:2]
    d = ((a[..., None, :] - NAIN_K) ** 2).sum(-1)
    wk = np.exp(-(d - d.min(-1, keepdims=True)) / (2 * 0.06 ** 2)); wk /= wk.sum(-1, keepdims=True)
    Y = np.array([0.2126, 0.7152, 0.0722])
    ratio = np.clip((_lin(a) @ Y)[..., None] / (_lin(NAIN_K) @ Y), 0.5, 1.6)
    scale = _lin(NAIN_K[0]) / _lin(FILM["cream"])
    yy, xx = np.mgrid[:h, :w]; xs, ys = np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)
    rect = lambda x, y: (xs >= x) & (ys >= y)
    region = np.full((h, w), "border", object)
    for (x0, y0), (x1, y1) in guards: region[rect(x0, y0) & ~rect(x1, y1)] = "guard"
    region[rect(*field)] = "field"
    out = a.copy()
    for r, names in NAIN_FILM.items():
        m = (region == r) & rect(*guards[0][0])
        T = np.array([_lin(FILM[n]) * scale for n in names])
        out[m] = _srgb(np.clip((wk[m][..., None] * ratio[m][..., None] * T).sum(1), 0, 1))
    return out


def recolor_front(mat, name):
    """Swap the Nain's albedo for its film recolour (a new packed sRGB PNG: the pile normal was derived from the original first)."""
    tex = next(n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image.colorspace_settings.name != "Non-Color")
    w, h = tex.image.size; assert (w, h) == (1024, 2048), (w, h)   # NAIN_FIELD / NAIN_GUARDS are read off this photo
    a = np.empty(w * h * 4, np.float32); tex.image.pixels.foreach_get(a); a = a.reshape(h, w, 4)[..., :3]
    img = image_png(name, np.dstack([nain_film_recolor(a), np.ones((h, w, 1))]), w, h); img.colorspace_settings.name = "sRGB"
    tex.image = img


def thin_strands(o, keep):
    """Keep every `keep`-th loose part (strand): ~7800 strands at 0.4 mm spacing after the fit is far denser than reads; decimation
    alone stops at ~9 triangles a strand (70k a rug)."""
    me = o.data; nv = len(me.vertices)
    e = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get("vertices", e); e = e.reshape(-1, 2)
    lab = np.arange(nv)
    while True:   # label propagation to the smallest index in each part
        m = np.minimum(lab[e[:, 0]], lab[e[:, 1]])
        new = lab.copy(); np.minimum.at(new, e[:, 0], m); np.minimum.at(new, e[:, 1], m); new = new[new]
        if (new == lab).all(): break
        lab = new
    parts = np.unique(lab); drop = set(parts[np.arange(len(parts)) % keep != 0].tolist())
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if lab[v.index] in drop], context="VERTS")
    bm.to_mesh(me); bm.free(); me.update()
    print(f"  strands {len(parts)} -> {len(parts) - len(drop)}")


def prepare(key, src):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(PUR / "Rugs" / f"{src}.glb"))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in [o for o in bpy.data.objects if o.type != "MESH"]:
        bpy.data.objects.remove(o)
    for o in meshes:   # bake the transforms in: vertices in world space, identity matrices
        o.data.transform(o.matrix_world); o.matrix_world = mathutils.Matrix.Identity(4)
    body = next(o for o in meshes if o.data.materials[0].name == "carpet")
    fr = [o for o in meshes if o is not body]
    n0 = tris(meshes)
    select(fr, fr[0]); bpy.ops.object.join(); low = bpy.context.view_layer.objects.active; low.name = key + "Fringe"
    thin_strands(low, KEEP)
    d = low.modifiers.new("Decimate", "DECIMATE"); d.ratio = FRINGE_TRIS / tris([low])
    select([low], low); bpy.ops.object.modifier_apply(modifier=d.name)
    for o in (body, low):
        while o.data.color_attributes:            # glTFast trips on vertex colours (purchased_plants.py, Oct 16)
            o.data.color_attributes.remove(o.data.color_attributes[0])
    # the body mesh's own UV layer: the second (Heriz TEXCOORD_1) is unused by its material
    while len(body.data.uv_layers) > 1: body.data.uv_layers.remove(body.data.uv_layers[-1])
    # the body's underside is never seen, and 2 mm over the floor it z-fought it (double-sided source, build Oct 18)
    bm = bmesh.new(); bm.from_mesh(body.data); zmin = min(v.co.z for v in bm.verts)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(v.co.z < zmin + 1e-4 for v in f.verts)], context="FACES")
    bm.to_mesh(body.data); bm.free()
    albedo = next(n.image for n in body.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    set_normal(body.data.materials[0], pile_normal(albedo, key + "_pile_normal"))
    if key == "FrontRug": recolor_front(body.data.materials[0], key + "_film_albedo")
    body.name = key + "Body"
    print(f"{key}: {src} {n0} tris -> body {tris([body])} + fringe {tris([low])} = {tris([body, low])}")
    return body, low


def runner_albedo(a, W, L, border_m, width_m, n_field, resize):
    """The Heriz photo a (h, w, 3, rows top-down; its rows are the 3.86 m axis squashed into a square, so stretched x1.345 first)
    cut into a W x L runner image (rows along the runner), every piece at one scale."""
    h0, w0 = a.shape[:2]
    I = resize(a, round(h0 * 1.345), w0)                   # isotropic: motifs at their true proportions
    B0, B1, T0, T1 = 12, 197, 15, 159                      # side border cols / end border rows, outer edge to field (read off the photo)
    s = (W * border_m / width_m) / (B1 - B0)               # out px per source px
    cw, cl = round(W / s), round(L / s)
    bw, bt = B1 - B0, T1 - T0
    fw = cw - 2 * bw
    c = np.zeros((cl, cw, 3), np.float32)
    side = I[T1 + 40:I.shape[0] - T1 - 40, B0:B1]
    strip = np.concatenate([side, side[::-1]] * (cl // (2 * len(side)) + 1))[:cl - 2 * bt]
    c[bt:cl - bt, :bw] = strip; c[bt:cl - bt, cw - bw:] = strip[:, ::-1]
    mid = (w0 - fw) // 2
    end = np.concatenate([I[T0:T1, B0:B1], I[T0:T1, mid:mid + fw], I[T0:T1, B0:B1][:, ::-1]], 1)
    c[:bt] = end; c[cl - bt:] = end[::-1]
    fl = cl - 2 * bt; th = fl // n_field; cy = I.shape[0] // 2
    tile = I[cy - th // 2:cy - th // 2 + th, mid:mid + fw]
    field = np.concatenate([tile if k % 2 == 0 else tile[::-1] for k in range(n_field)])
    c[bt:bt + len(field), bw:cw - bw] = field
    c[bt + len(field):cl - bt, bw:cw - bw] = tile[:fl - len(field)]
    return resize(c, L, W)


def bl_resize(a, h, w):
    """Resample an (h0, w0, 3) top-down array with Blender's Image.scale."""
    h0, w0 = a.shape[:2]
    img = bpy.data.images.new("_rs", w0, h0, alpha=False, float_buffer=True)
    img.pixels.foreach_set(np.dstack([a[::-1], np.ones((h0, w0, 1), np.float32)]).astype(np.float32).ravel())
    img.scale(w, h); out = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(out)
    bpy.data.images.remove(img)
    return out.reshape(h, w, 4)[::-1, :, :3].copy()


def runner(body, fringe):
    """The foyer runner from the prepared Heriz (body: its albedo; fringe: its decimated strands, source space)."""
    X, Z = FR["x"], FR["z"]; Wm = Z[1] - Z[0]; W, L = 512, 2360
    src = next(n.image for n in body.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    sw, sh = src.size; a = np.empty(sw * sh * 4, np.float32); src.pixels.foreach_get(a)
    alb = runner_albedo(a.reshape(sh, sw, 4)[::-1, :, :3], W, L, 0.14, Wm, 4, bl_resize)
    img = image_png("Runner_albedo", np.dstack([alb[::-1], np.ones((L, W, 1), np.float32)]).clip(0, 1), W, L)
    img.colorspace_settings.name = "sRGB"
    m = bpy.data.materials.new("PR_Runner"); m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = img
    m.node_tree.links.new(t.outputs["Color"], bs.inputs["Base Color"])
    set_normal(m, pile_normal(img, "Runner_pile_normal"))
    bs.inputs["Roughness"].default_value = 0.95; bs.inputs["Metallic"].default_value = 0.0
    # body: a 1 cm slab (top + 4 sides; the underside is never seen), Blender = (-x, z, y); v along x, u across z
    (x0, x1), (z0, z1) = X, Z
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    def quad(pts, uvs):
        f = bm.faces.new([bm.verts.new((-x, z, y)) for x, y, z in pts])
        for lp, q in zip(f.loops, uvs): lp[uv].uv = q
    quad([(x0, Y1, z0), (x0, Y1, z1), (x1, Y1, z1), (x1, Y1, z0)], [(0, 0), (1, 0), (1, 1), (0, 1)])
    for (ax, az), (bx, bz) in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))):
        quad([(ax, Y0, az), (bx, Y0, bz), (bx, Y1, bz), (ax, Y1, az)], [(0, 0)] * 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("PR_Runner"); bm.to_mesh(me); bm.free(); me.materials.append(m)
    rb = bpy.data.objects.new("PR_Runner", me); bpy.context.scene.collection.objects.link(rb)
    # fringe: the Heriz strands in the central runner width of each end, native size, moved to the runner's ends
    B = coords(body); blo, bhi = B.min(0), B.max(0); c = (blo + bhi) / 2
    La = int(np.argmax(bhi[:2] - blo[:2])); Wa = 1 - La
    F = coords(fringe); flo, fhi = F.min(0), F.max(0)
    bm = bmesh.new(); bm.from_mesh(fringe.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if abs(v.co[Wa] - c[Wa]) > Wm / 2 - 0.01], context="VERTS")
    bm.to_mesh(fringe.data); bm.free()
    a = coords(fringe)
    # the decimated strands end at the body's edge (tips collapsed): place each end's tips the measured fringe length past the box
    hi = a[:, La] > c[La]; amax, amin = a[hi, La].max(), a[~hi, La].min()
    along = np.where(hi, x1 + FR["fringe"] - (amax - a[:, La]), x0 - FR["fringe"] + (a[:, La] - amin))
    across = (z0 + z1) / 2 + (a[:, Wa] - c[Wa])
    sy = Y0 + (a[:, 2] - flo[2]) / max(fhi[2] - flo[2], 1e-6) * (Y1 - Y0)
    fringe.data.vertices.foreach_set("co", np.column_stack([-along, across, sy]).ravel()); fringe.data.update()
    fm = fringe.data.materials[0]; fm.name = "PR_RunnerFringe"
    fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    fb.inputs["Base Color"].default_value = (0.80, 0.76, 0.66, 1.0); fb.inputs["Roughness"].default_value = 0.95
    fringe.name = "PR_RunnerFringe"
    bpy.data.objects.remove(body)
    pts = np.vstack([coords(rb), coords(fringe)])
    print(f"Runner: {tris([rb, fringe])} tris; spec x {-pts[:, 0].max():.3f}..{-pts[:, 0].min():.3f} z {pts[:, 1].min():.3f}..{pts[:, 1].max():.3f}"
          f" y {pts[:, 2].min():.4f}..{pts[:, 2].max():.4f}")


def export(objs, path):
    select(objs, objs[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True, export_apply=True, use_selection=True)
    print("wrote", path)


def fit(key, body, fringe, X, Z, long_axis, fringe_col, fringe_in_box):
    """Spec point: x, y up, z; Blender = (-x, z, y) (glTF exporter y-up + glTFast's x flip = Unity, Unity z = -spec z)."""
    B = coords(body); blo, bhi = B.min(0), B.max(0)
    F = coords(fringe); flo, fhi = F.min(0), F.max(0)
    L_ax = int(np.argmax(bhi[:2] - blo[:2])); W_ax = 1 - L_ax          # the source's long (fringed) axis
    c = (blo + bhi) / 2
    (La, Lb), (Wa, Wb) = (Z, X) if long_axis == "z" else (X, Z)
    ov = max(blo[L_ax] - flo[L_ax], fhi[L_ax] - bhi[L_ax]) if fringe_in_box else 0.0   # the fringe's reach past the body
    sL, sW = (Lb - La) / (bhi[L_ax] - blo[L_ax] + 2 * ov), (Wb - Wa) / (bhi[W_ax] - blo[W_ax])
    print(f"{key}: source body {np.round(bhi - blo, 3)}; scale along {sL:.3f} across {sW:.3f} (across/along {sW / sL:.3f})")
    for o in (body, fringe):
        a = coords(o)
        along = (La + Lb) / 2 + (a[:, L_ax] - c[L_ax]) * sL
        across = (Wa + Wb) / 2 + (a[:, W_ax] - c[W_ax]) * sW
        sx, sz = (across, along) if long_axis == "z" else (along, across)
        lo, hi = (blo[2], bhi[2]) if o is body else (flo[2], fhi[2])
        sy = Y0 + (a[:, 2] - lo) / max(hi - lo, 1e-6) * (Y1 - Y0)
        out = np.column_stack([-sx, sz, sy])
        o.data.vertices.foreach_set("co", out.ravel()); o.data.update()
        if o is fringe: o.data.shade_smooth()
    for m in (body.data.materials[0], fringe.data.materials[0]):   # wool: matte, not metal
        bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bs.inputs["Roughness"].default_value = 0.95; bs.inputs["Metallic"].default_value = 0.0
    if fringe_col:
        bs = next(n for n in fringe.data.materials[0].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bs.inputs["Base Color"].default_value = (*fringe_col, 1.0)
    body.data.materials[0].name = f"PR_{key}"; fringe.data.materials[0].name = f"PR_{key}Fringe"
    body.name = f"PR_{key}"; fringe.name = f"PR_{key}Fringe"
    pts = np.vstack([coords(body), coords(fringe)])
    print(f"{key} fitted: spec x {-pts[:, 0].max():.3f}..{-pts[:, 0].min():.3f} z {pts[:, 1].min():.3f}..{pts[:, 1].max():.3f}"
          f" y {pts[:, 2].min():.4f}..{pts[:, 2].max():.4f}")


# each rug: decimate + maps, write its _lod.glb, fit it, keep it in a library blend; then one scene with both fitted rugs
lib, TMP = [], tempfile.mkdtemp()
for key, src, X, Z, ax, col, inbox in RUGS:
    body, fringe = prepare(key, src)
    fit(key, body, fringe, X, Z, ax, col, inbox)
    export([body, fringe], PUR / "Rugs" / f"{src}_lod.glb")
    blend = Path(TMP) / f"{key}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend)); lib.append((key, blend))
body, fringe = prepare("Runner", "fine_persian_heriz_carpet")
runner(body, fringe)
blend = Path(TMP) / "Runner.blend"; bpy.ops.wm.save_as_mainfile(filepath=str(blend)); lib.append(("Runner", blend))
bpy.ops.wm.read_factory_settings(use_empty=True)
root = bpy.data.objects.new("PurchasedRug", None); bpy.context.scene.collection.objects.link(root)
objs = []
for key, blend in lib:
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("PR_")]
    g = bpy.data.objects.new(key, None); bpy.context.scene.collection.objects.link(g); g.parent = root
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o); o.parent = g; objs.append(o)
print(f"PurchasedRug: {tris(objs)} triangles in {len(objs)} meshes")
select(objs + [root] + [o for o in bpy.data.objects if o.type == "EMPTY"], root)
bpy.ops.export_scene.gltf(filepath=str(PUR / "PurchasedRug.glb"), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", PUR / "PurchasedRug.glb")
