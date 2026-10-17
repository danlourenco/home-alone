"""model_quality: the artist pipeline's quality gate (.claude/skills/artist-pipeline) on exported GLBs. Exit 1 on any problem.

A model FAILS on any of:
  facet     a curve facet whose chord error is over 1 mm (1 mm per metre of radius for curves over 1 m): faces meeting at
            0.5-30 degrees are facets of a curve; radius from the facet width and the turn
  edge      an unbevelled convex edge: faces meeting at more than 30 degrees (dihedral < 150) along more than 5 cm
  normal    no normal map, or a flat one (std of its x/y < 0.004)
  maps      a baked material missing base colour, normal, occlusion or metallic-roughness maps
  texel     a textured face under 512 px/m (house interiors: every face is within 3 m of the walk path)
  albedo    the base colour's mean (sRGB) more than the material's albedo_tol from its albedo_srgb (glTF material extras)
  lod       no node named *_LODn and no lod_reason in the root's extras
Materials whose extras say role "system" (a room's wallpaper given by SpecGreybox) are skipped for maps, texel and albedo.
Welding is per primitive: a joint between two materials (paper under a casing) is not an edge of either.

  uv run --with numpy --with pillow python -I tools/house/model_quality.py FILE.glb ...   # every check, per model
  uv run --with numpy --with pillow python -I tools/house/model_quality.py --report        # the build's line (Models/Foyer)
  uv run --with numpy --with pillow python -I tools/house/model_quality.py --selftest      # a stepped arch must fail, a good arch pass
--report gates the models made through the pipeline (root extras artist_pipeline) and counts the rest as predating it.
"""
import io
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "unity/HomeAlone/Assets/Models/Foyer"
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


# ---------------------------------------------------------------- reading
def load(path):
    b = Path(path).read_bytes(); assert b[:4] == b"glTF", path
    n = struct.unpack("<I", b[12:16])[0]; js = json.loads(b[20:20 + n]); binb = b[20 + n + 8:]
    def acc(i):
        a = js["accessors"][i]; bv = js["bufferViews"][a["bufferView"]]; dt = np.dtype(CT[a["componentType"]]); k = NC[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0); stride = bv.get("byteStride", dt.itemsize * k)
        raw = np.frombuffer(binb, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * k, offset=off)
        out = np.lib.stride_tricks.as_strided(raw, (a["count"], dt.itemsize * k), (stride, 1)).copy().view(dt).reshape(a["count"], k)
        return out.astype(np.float64) if dt == np.float32 else out.astype(np.int64)
    imgs = {}
    def image(tex):
        if tex is None: return None
        src = js["textures"][tex["index"]]["source"]
        if src not in imgs:
            bv = js["bufferViews"][js["images"][src]["bufferView"]]; o = bv.get("byteOffset", 0)
            imgs[src] = np.asarray(Image.open(io.BytesIO(binb[o:o + bv["byteLength"]])).convert("RGBA"), np.float64) / 255
        return imgs[src]
    def mat(q):
        q = np.array(q, float); x, y, z, w = q
        return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    prims, names, root_extras = [], [], {}
    def walk(ni, M):
        nd = js["nodes"][ni]; names.append(nd.get("name", ""))
        if "matrix" in nd: L = np.array(nd["matrix"], float).reshape(4, 4).T
        else:
            L = np.eye(4); L[:3, :3] = mat(nd.get("rotation", [0, 0, 0, 1])) * np.array(nd.get("scale", [1, 1, 1])); L[:3, 3] = nd.get("translation", [0, 0, 0])
        W = M @ L
        if not root_extras and nd.get("extras"): root_extras.update(nd["extras"])
        if "mesh" in nd:
            for p in js["meshes"][nd["mesh"]]["primitives"]:
                v = acc(p["attributes"]["POSITION"]); v = v @ W[:3, :3].T + W[:3, 3]
                idx = acc(p["indices"]).ravel() if "indices" in p else np.arange(len(v))
                uv = acc(p["attributes"]["TEXCOORD_0"]) if "TEXCOORD_0" in p["attributes"] else None
                m = js["materials"][p["material"]] if "material" in p else {}
                pbr = m.get("pbrMetallicRoughness", {})
                prims.append(dict(node=nd.get("name", ""), v=v, f=idx.reshape(-1, 3), uv=uv, mat=m.get("name", ""), extras=m.get("extras", {}),
                                  base=image(pbr.get("baseColorTexture")), normal=image(m.get("normalTexture")),
                                  occ=image(m.get("occlusionTexture")), mr=image(pbr.get("metallicRoughnessTexture"))))
        for c in nd.get("children", []): walk(c, W)
    for ni in js["scenes"][js.get("scene", 0)]["nodes"]: walk(ni, np.eye(4))
    return prims, names, root_extras


# ---------------------------------------------------------------- checks
def edges_of(p):
    """Interior edges of the welded primitive: (length, turn angle rad, convex, facet width, alike) where alike = the faces on both
    sides are about as wide (within 3x): a facet of a curve. A small turn between a wide flat and a narrow face is a crease or a
    mitre (a moulding's joint), not a facet."""
    v = p["v"]; key = np.round(v / 1e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True); f = inv.ravel()[p["f"]]
    P = np.zeros((inv.max() + 1, 3)); P[inv.ravel()] = v
    a, b, c = P[f[:, 0]], P[f[:, 1]], P[f[:, 2]]; cr = np.cross(b - a, c - a); ar = np.linalg.norm(cr, axis=1)
    ok = ar > 1e-12; n = np.zeros_like(cr); n[ok] = cr[ok] / ar[ok, None]; cen = (a + b + c) / 3
    em = {}
    for t, tri in enumerate(f):
        if not ok[t]: continue
        for k in range(3):
            i, j, o = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]
            em.setdefault((min(i, j), max(i, j)), []).append((t, o))
    out = []
    for (i, j), ts in em.items():
        if len(ts) != 2: continue
        (t0, o0), (t1, o1) = ts; L = np.linalg.norm(P[i] - P[j])
        if L < 1e-6: continue
        turn = math.acos(max(-1.0, min(1.0, float(n[t0] @ n[t1]))))
        convex = float((cen[t1] - cen[t0]) @ n[t0]) < 1e-9
        e = (P[j] - P[i]) / L
        def dist(o):
            d = P[o] - P[i]; return np.linalg.norm(d - (d @ e) * e)
        w0, w1 = dist(o0), dist(o1)
        out.append((L, turn, convex, min(w0, w1), max(w0, w1) <= 3 * min(w0, w1)))
    return out


def check(path):
    prims, names, rx = load(path); probs = []
    for p in prims:
        tag = f"{p['node']}[{p['mat']}]"
        nfacet = nedge = 0; worst = 0.0
        for L, turn, convex, w, alike in edges_of(p):
            if math.radians(0.5) < turn <= math.radians(30) and w > 1e-6 and alike:
                R = w / (2 * math.sin(turn / 2)); err = R * (1 - math.cos(turn / 2))
                if err > 0.001 * max(R, 1.0): nfacet += 1; worst = max(worst, err)
            elif turn > math.radians(30) and convex and L > 0.05:
                nedge += 1
        if nfacet: probs.append(f"facet   {tag}: {nfacet} curve facets over the chord error (worst {worst * 1000:.1f} mm)")
        if nedge: probs.append(f"edge    {tag}: {nedge} unbevelled convex edges over 5 cm")
        if p["extras"].get("role") == "system":
            continue
        miss = [k for k in ("base", "normal", "occ", "mr") if p[k] is None]
        if miss: probs.append(f"maps    {tag}: missing {', '.join(miss)}")
        if p["normal"] is not None:
            sd = float(p["normal"][..., :2].std(axis=(0, 1)).max())
            if sd < 0.004: probs.append(f"normal  {tag}: flat normal map (std {sd:.4f})")
        elif "normal" not in miss: pass
        img = p["base"] if p["base"] is not None else p["normal"]
        if img is not None and p["uv"] is not None:
            H, W = img.shape[:2]; v, uv, f = p["v"], p["uv"], p["f"]
            wa = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1) / 2
            d1, d2 = uv[f[:, 1]] - uv[f[:, 0]], uv[f[:, 2]] - uv[f[:, 0]]
            ua = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2 * W * H
            big = wa > 1e-6; dens = np.sqrt(ua[big] / wa[big])
            low = int((dens < 512 * 0.95).sum())
            if low: probs.append(f"texel   {tag}: {low} faces under 512 px/m (min {dens.min():.0f})")
        elif img is not None:
            probs.append(f"texel   {tag}: textured but no UVs")
        if p["base"] is not None and p["uv"] is not None and "albedo_srgb" in p["extras"]:
            rng = np.random.default_rng(0); v, uv, f = p["v"], p["uv"], p["f"]
            wa = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1) / 2
            t = rng.choice(len(f), 4000, p=wa / wa.sum()); r1, r2 = rng.random(4000), rng.random(4000); s = np.sqrt(r1)
            q = (1 - s)[:, None] * uv[f[t, 0]] + (s * (1 - r2))[:, None] * uv[f[t, 1]] + (s * r2)[:, None] * uv[f[t, 2]]
            H, W = p["base"].shape[:2]; px = np.clip((q[:, 0] % 1) * W, 0, W - 1).astype(int); py = np.clip((q[:, 1] % 1) * H, 0, H - 1).astype(int)
            mean = p["base"][py, px, :3].mean(0); tgt = np.array(p["extras"]["albedo_srgb"]); tol = p["extras"].get("albedo_tol", 0.06)
            if np.abs(mean - tgt).max() > tol:
                probs.append(f"albedo  {tag}: base mean {np.round(mean, 3).tolist()} vs measured {tgt.tolist()} +-{tol}")
    if not any("_LOD" in n for n in names) and not rx.get("lod_reason"):
        probs.append("lod     no LODs and no lod_reason")
    return probs, rx


# ---------------------------------------------------------------- self-test models
def write_glb(path, parts, root_extras=None):
    """parts: [(name, v (n,3), f (m,3), uv or None, material dict, {key: RGBA uint8 image})]."""
    js = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"name": "root", "children": [], "extras": root_extras or {}}],
          "meshes": [], "materials": [], "accessors": [], "bufferViews": [], "buffers": [], "textures": [], "images": []}
    blob = bytearray()
    def view(data):
        while len(blob) % 4: blob.append(0)
        js["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}); blob.extend(data); return len(js["bufferViews"]) - 1
    def acc(a, ct, typ):
        js["accessors"].append({"bufferView": view(a.tobytes()), "componentType": ct, "count": len(a), "type": typ,
                                **({"min": a.min(0).tolist(), "max": a.max(0).tolist()} if typ == "VEC3" else {})}); return len(js["accessors"]) - 1
    def tex(img):
        bio = io.BytesIO(); Image.fromarray(img).save(bio, "PNG")
        js["images"].append({"bufferView": view(bio.getvalue()), "mimeType": "image/png"}); js["textures"].append({"source": len(js["images"]) - 1})
        return {"index": len(js["textures"]) - 1}
    for name, v, f, uv, m, maps in parts:
        attrs = {"POSITION": acc(np.asarray(v, np.float32), 5126, "VEC3")}
        if uv is not None: attrs["TEXCOORD_0"] = acc(np.asarray(uv, np.float32), 5126, "VEC2")
        mm = dict(m); pbr = {}
        if "base" in maps: pbr["baseColorTexture"] = tex(maps["base"])
        if "orm" in maps: t = tex(maps["orm"]); pbr["metallicRoughnessTexture"] = t; mm["occlusionTexture"] = t
        if "normal" in maps: mm["normalTexture"] = tex(maps["normal"])
        mm["pbrMetallicRoughness"] = pbr; js["materials"].append(mm)
        js["meshes"].append({"primitives": [{"attributes": attrs, "indices": acc(np.asarray(f, np.uint32).ravel(), 5125, "SCALAR"), "material": len(js["materials"]) - 1}]})
        js["nodes"].append({"name": name, "mesh": len(js["meshes"]) - 1}); js["nodes"][0]["children"].append(len(js["nodes"]) - 1)
    js["buffers"].append({"byteLength": len(blob)})
    j = json.dumps(js).encode(); j += b" " * (-len(j) % 4); blob += b"\0" * (-len(blob) % 4)
    Path(path).write_bytes(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(j) + 8 + len(blob)) + struct.pack("<I", len(j)) + b"JSON" + j
                           + struct.pack("<I", len(blob)) + b"BIN\0" + bytes(blob))


def box(x0, x1, y0, y1, z0, z1):
    v = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return v, np.array(f)


def arch_strip(n, R=1.04, half=0.6875, depth=0.14):
    """A segmental soffit strip (open surface: its edges are boundaries) with n facets, metric UVs at 1024 px/m in 2048 x 256."""
    a0 = math.asin(half / R); ang = np.linspace(-a0, a0, n + 1)
    v = [[0.0, R * math.cos(t), R * math.sin(t)] for t in ang] + [[depth, R * math.cos(t), R * math.sin(t)] for t in ang]
    s = R * (ang - ang[0]); uv = [[x * 1024 / 2048, 0.05] for x in s] + [[x * 1024 / 2048, 0.05 + depth * 1024 / 256] for x in s]
    f = [(k, k + 1, n + 2 + k) for k in range(n)] + [(k, n + 2 + k, n + 1 + k) for k in range(n)]
    return np.array(v), np.array(f), np.array(uv)


def selftest():
    tmp = Path(__file__).resolve().parents[2] / "sfm-work/model_quality"; tmp.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(1)
    nrm = np.dstack([128 + rng.integers(-6, 7, (256, 2048, 2)), np.full((256, 2048, 1), 250), np.full((256, 2048, 1), 255)]).astype(np.uint8)
    base = np.dstack([np.full((256, 2048, 3), (235, 235, 230)), np.full((256, 2048, 1), 255)]).astype(np.uint8)
    orm = np.dstack([np.full((256, 2048, 1), 230), np.full((256, 2048, 1), 200), np.zeros((256, 2048, 1)), np.full((256, 2048, 1), 255)]).astype(np.uint8)
    maps = {"base": base, "normal": nrm, "orm": orm}; mat = {"name": "Soffit", "extras": {"role": "baked", "albedo_srgb": [0.92, 0.92, 0.9], "albedo_tol": 0.06}}
    # the grey-box arch: 12 stepped slices per side, plain material (SpecGreybox.ArchTop)
    R, half, sp, cr = 1.039, 0.6875, 1.91, 2.17; yc = cr - R; stepped = []
    for i in range(12):
        y0, y1 = sp + (cr - sp) * i / 12, sp + (cr - sp) * (i + 1) / 12; w = math.sqrt(max(0, R * R - ((y0 + y1) / 2 - yc) ** 2))
        for z0, z1 in ((-half, -w), (w, half)):
            if z1 - z0 > 1e-4: v, f = box(0, 0.14, y0, y1, z0, z1); stepped.append((f"Arch_Spandrel{i}", v, f, None, {"name": "Wall"}, {}))
    write_glb(tmp / "stepped_arch.glb", stepped)
    v, f, uv = arch_strip(24); write_glb(tmp / "good_arch.glb", [("Soffit", v, f, uv, mat, maps)], {"artist_pipeline": 1, "lod_reason": "selftest"})
    v, f, uv = arch_strip(8); write_glb(tmp / "coarse_arch.glb", [("Soffit", v, f, uv, mat, maps)], {"artist_pipeline": 1, "lod_reason": "selftest"})
    flat = dict(maps, normal=np.dstack([np.full((256, 2048, 2), 128), np.full((256, 2048, 2), 255)]).astype(np.uint8))
    v, f, uv = arch_strip(24); write_glb(tmp / "flat_normal.glb", [("Soffit", v, f, uv, mat, flat)], {"artist_pipeline": 1})
    expect = {"stepped_arch.glb": {"edge", "maps", "lod"}, "good_arch.glb": set(), "coarse_arch.glb": {"facet"}, "flat_normal.glb": {"normal", "lod"}}
    ok = True
    for name, want in expect.items():
        probs, _ = check(tmp / name); got = {p.split()[0] for p in probs}
        good = got == want; ok &= good
        print(f"{'ok  ' if good else 'FAIL'} {name}: expected {sorted(want) or 'pass'}, got {sorted(got) or 'pass'}")
        for p in probs[:4]: print("       ", p)
    sys.exit(0 if ok else 1)


def main():
    a = sys.argv[1:]
    if "--selftest" in a: selftest()
    files = [Path(x) for x in a if not x.startswith("--")] or sorted(MODELS.glob("*.glb"))
    report = "--report" in a; bad = 0; gated = 0; lines = []
    for fpath in files:
        probs, rx = check(fpath)
        if report and not rx.get("artist_pipeline"): continue
        gated += 1; bad += len(probs)
        lines.append(f"{'FAIL' if probs else 'ok  '} {fpath.name}: {len(probs)} problems")
        lines += [f"        {p}" for p in probs]
    if report:
        print(f"Quality check: {gated} pipeline models of {len(files)} generated (the rest predate the artist pipeline), {bad} problems")
        print("\n".join(l for l in lines if not l.startswith("ok")))
    else:
        print("\n".join(lines))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
