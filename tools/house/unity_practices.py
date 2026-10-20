#!/usr/bin/env python3
"""unity_practices.py: deterministic Unity 6 / HDRP best-practice checks (user, Oct 20: "if any of those checks can be performed
deterministically with cli tools, build the tool"), so no agent spends inference re-checking them by eye. A RATCHET: violations that
already exist are listed in spec/captures/practices-baseline.json and tolerated; any NEW one fails (preflight runs this).

  python3 tools/house/unity_practices.py                    # report; exit 1 on a violation not in the baseline
  python3 tools/house/unity_practices.py --update-baseline  # accept the current GIT-TRACKED violations (after a deliberate fix)
  python3 tools/house/unity_practices.py --selftest

Checks (static; the scene-level ones, LODGroups / MeshColliders on foliage / material instances, are a build gate in SpecGreybox):
  obsolete   CS0618/CS0612 warnings from csc_check.sh (Unity 6000.6: FindObjectsSortMode, FindFirstObjectByType, spotLightShape...)
  material   `.material` read/written in Scripts/ or Editor/ (instantiates a per-renderer copy: breaks SRP Batcher sharing; use
             .sharedMaterial + MaterialPropertyBlock). A line that isn't a Renderer (DecalProjector.material) says `// practices: ok`
  foliage    a foliage .mat (by name) that is not opaque + alpha-clipped + double-sided (HDRP Lit foliage practice)
  mips       a 2D texture under Textures/ or Models/ imported without mipmaps
  texsize    a texture imported above 4096 (2048 for foliage; 8192 for the 360-degree Backdrop domes, which need it)
  probeatlas the reflection probe atlas budget (HDRP.asset reflectionProbeTexCacheSize) against the baked cube probes of House_WallGrid
             (every lighting scenario's set: across a day/night switch HDRP 17's LRU keeps the last two renders' entries, Oct 20 live
             read: 61 entries = 2 x 30-31 cubes + mirrors, atlas 100% full) plus the realtime planar mirrors in SpecGreybox*.cs.
             Fails above 85% (HEADROOM): the next probe or mirror must not tip it over. Never baselined: over budget logs "No more
             space in Reflection Probe Atlas" and drops reflections. (reflectionCacheCompressed is a no-op in HDRP 17.6: LightLoop.cs
             has the BC6H path commented out; 128 is the smallest cube tier, so the levers are the atlas size and the mirrors.)
  shadowbudget  the real-time shadow budget of House_WallGrid (perf pass 1, Oct 20) against the static rows of the "## BUDGET" table in
             docs/PERFORMANCE.md: shadowed real-time (not Baked, not directional) lights in the scene file, and the sun's cascade
             distance (SpecGreybox.cs SunShadowDistance, the build's scene volume; else the largest maxShadowDistance any profile overrides). The street pose's caster count is
             counted by the build (SpecGreybox.MotionShadow.cs ShadowBudgetCheck) and the frame times by `perf_probe.sh gate`. A
             budget, never baselined.
"""
import json, re, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "unity/HomeAlone/Assets"
BASE = ROOT / "spec/captures/practices-baseline.json"
FOLIAGE = re.compile(r"(?i)(shrub|foliage|hedge|grass|ivy|needle|bush|fern|leaves|plant|denleaf|treeleaf|boxwood|yew)")
NOT_FOLIAGE = re.compile(r"(?i)(core|stem|snow|pot|trunk|bark|soil|urn|stand|bulb|frontleaf|doorleaf|hardware|inside)")
MAT_USE = re.compile(r"\.material\b(?!s)")   # .material, not .materials / .sharedMaterial


def rel(p):
    return str(Path(p).resolve().relative_to(ROOT))


def obsolete():
    out = subprocess.run(["bash", str(ROOT / "tools/house/csc_check.sh")], env={**__import__("os").environ, "CSC_WARNINGS": "1"},
                         capture_output=True, text=True).stdout
    for l in out.splitlines():
        m = re.match(r"(.+?\.cs)\((\d+),\d+\): warning (CS0618|CS0612): '([^']+)'", l)
        if m:   # key on file + API, not the line number: edits above a call must not count as new
            yield f"obsolete|{rel(m.group(1))}|{m.group(4)}"


def material_access():
    for d in ("Scripts", "Editor"):
        for f in sorted((A / d).glob("*.cs")):
            for line in f.read_text(errors="ignore").splitlines():
                code = line.split("//")[0]
                if MAT_USE.search(code) and "practices: ok" not in line:   # e.g. DecalProjector.material is a plain property
                    yield f"material|{rel(f)}|{code.strip()[:80]}"


def mat_flags(text):
    g = lambda k: (re.search(rf"\b{k}: ([\d.]+)", text) or [None, None])[1]
    return g("_AlphaCutoffEnable"), g("_SurfaceType"), g("_DoubleSidedEnable")


def foliage():
    for f in sorted(list(A.glob("Materials/**/*.mat")) + list(A.glob("Models/**/*.mat"))):
        if not FOLIAGE.search(f.stem) or NOT_FOLIAGE.search(f.stem):
            continue
        clip, surf, two = mat_flags(f.read_text(errors="ignore"))
        if not (clip == "1" and surf in (None, "0") and two == "1"):
            yield f"foliage|{rel(f)}|clip={clip} surface={surf} doublesided={two}"


def textures():
    for f in sorted(list(A.glob("Textures/**/*.meta")) + list(A.glob("Models/**/*.meta"))):
        if not re.search(r"\.(png|jpg|jpeg|tga|exr|tif|tiff|psd)\.meta$", f.name, re.I):
            continue
        t = f.read_text(errors="ignore")
        if "textureimporter:" not in t.lower() or re.search(r"textureType: (2|8)\b", t):   # 2 = normal-less GUI? skip GUI(2)/sprite(8)
            continue
        if re.search(r"enableMipMap: 0", t):
            yield f"mips|{rel(f)[:-5]}"
        sizes = [int(s) for s in re.findall(r"maxTextureSize: (\d+)", t)]
        cap = 2048 if FOLIAGE.search(f.name) and not NOT_FOLIAGE.search(f.name) else 4096
        if f.parent.name == "Backdrop" and f.name.startswith("dome_"):
            cap = 8192   # 360-degree photo domes: 8192 px / 360 deg = 23 px per degree, already under the screen's ~42 at 60 deg FOV
        if sizes and max(sizes) > cap:
            yield f"texsize|{rel(f)[:-5]}|{max(sizes)}>{cap}"


def exr_size(f):   # (width, height) from an OpenEXR header's dataWindow (box2i)
    d = f.read_bytes()[:4096]; i = d.index(b"dataWindow\0box2i\0") + 21
    x0, y0, x1, y1 = struct.unpack("<4i", d[i:i + 16]); return x1 - x0 + 1, y1 - y0 + 1


def atlas_need(cube_faces, planar_res):
    """Texels HDRP 17.6 asks of the atlas (ReflectionProbeTextureCache.GetTextureSizeInAtlas): a cube of face F is stored octahedral at
    max(F, 32) x4 (x2 from 512 up), squared; a planar at its resolution, squared. One slot per texture (not per camera: one realtime
    RT per planar probe). Power-of-two squares sorted large-first pack a power-of-two atlas exactly, so area is the whole test."""
    cube = lambda f: (max(f, 32) * (4 if max(f, 32) < 512 else 2)) ** 2
    return sum(cube(f) for f in cube_faces) + sum(r * r for r in planar_res)


HEADROOM = 0.85   # coordinator, Oct 20: 100% with no headroom is not a pass


def probe_atlas(editor_texts=None, hdrp_text=None):
    m = re.search(r"reflectionProbeTexCacheSize: (\d+)", hdrp_text or (A / "Settings/HDRP.asset").read_text())
    v = int(m.group(1)); w, h = (v, v) if v <= 16384 else (v >> 16, v & 0xFFFF)
    faces = [exr_size(f)[1] for f in sorted((A / "Scenes/House_WallGrid").glob("Probe_*.exr"))]   # 6:1 strip: height = face
    if editor_texts is None:
        editor_texts = [f.read_text(errors="ignore") for f in sorted((A / "Editor").glob("SpecGreybox*.cs"))]
    planar = [int(r) for t in editor_texts for r in re.findall(r"PlanarReflectionAtlasResolution\.Resolution(\d+)", t)]
    need = atlas_need(faces, planar)
    vram = w * h * 4 * 1.33 / 2 ** 20   # R11G11B10 (4 B), 1 slice (fabric off), mips: HDRP's GetApproxCacheSizeInByte
    print(f"probe atlas: {len(faces)} baked cubes (all scenarios) + planars {planar} need {need / 1e6:.2f} M of {w}x{h} = "
          f"{w * h / 1e6:.2f} M ({100 * need / (w * h):.0f}%, limit {HEADROOM:.0%}; atlas ~{vram:.0f} MB VRAM)")
    if need > HEADROOM * w * h:
        yield f"probeatlas|unity/HomeAlone/Assets/Settings/HDRP.asset|need {need / 1e6:.2f}M > {HEADROOM:.0%} of {w * h / 1e6:.2f}M"


def static_budget(md=None):
    """{name: limit} from the static-* rows of docs/PERFORMANCE.md's BUDGET table"""
    text = (md or ROOT / "docs/PERFORMANCE.md").read_text(); sec = text[text.index("## BUDGET"):]
    return {m[1]: float(m[2]) for m in re.finditer(r"\|\s*`?(static-[\w-]+)`?\s*\|\s*([\d.]+)\s*\|", sec)}


def scene_shadow_lights(text):
    n = 0
    for d in text.split("\n--- "):
        if not d.startswith("!u!108 "):
            continue
        typ, sh, lm = (int(re.search(p, d).group(1)) for p in (r"\n  m_Type: (\d+)", r"m_Shadows:\n    m_Type: (\d+)", r"\n  m_Lightmapping: (\d+)"))
        n += typ != 1 and sh > 0 and lm != 2   # 1 directional; m_Lightmapping 2 Baked
    return n


def sun_distance(texts):
    return max([float(v) for t in texts for v in re.findall(r"maxShadowDistance:\n    m_OverrideState: 1\n    m_Value: ([\d.]+)", t)] or [0])


def shadow_budget(scene_text=None, profile_texts=None, md=None, code_text=None):
    lim = static_budget(md)
    scene = scene_text or (A / "Scenes/House_WallGrid.unity").read_text(errors="ignore")
    profs = profile_texts or [f.read_text(errors="ignore") for f in list((A / "Settings").glob("*.asset")) + list((A / "HDRPDefaultResources").glob("*.asset"))]
    code = code_text if code_text is not None else (A / "Editor/SpecGreybox.cs").read_text(errors="ignore")
    m = re.search(r"SunShadowDistance = ([\d.]+)f", code)   # the build's GreyboxVolume override (scene volume) beats the default profile
    n, d = scene_shadow_lights(scene), float(m[1]) if m else sun_distance(profs)
    print(f"shadow budget: {n} shadowed real-time lights (limit {lim.get('static-shadowed-lights', '-'):g}), sun cascades {d:g} m (limit {lim.get('static-sun-distance', '-'):g})")
    if n > lim.get("static-shadowed-lights", 1e9):
        yield f"shadowbudget|unity/HomeAlone/Assets/Scenes/House_WallGrid.unity|{n} shadowed real-time lights > {lim['static-shadowed-lights']:g}"
    if d > lim.get("static-sun-distance", 1e9):
        yield f"shadowbudget|unity/HomeAlone/Assets/HDRPDefaultResources/DefaultSettingsVolumeProfile.asset|sun cascades {d:g} m > {lim['static-sun-distance']:g}"


def tracked(keys):
    files = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split())
    return [k for k in keys if k.split("|")[1] in files]


def run():
    found = sorted(set(list(obsolete()) + list(material_access()) + list(foliage()) + list(textures()) + list(probe_atlas()) + list(shadow_budget())))
    if "--update-baseline" in sys.argv:
        keep = [k for k in tracked(found) if not k.startswith(("probeatlas|", "shadowbudget|"))]   # a budget, not a ratchet
        BASE.write_text(json.dumps(keep, indent=0) + "\n")
        print(f"baseline: {len(keep)} existing violations accepted ({len(found) - len(keep)} untracked left out)"); return 0
    base = set(json.loads(BASE.read_text())) if BASE.exists() else set()
    new = [k for k in found if k not in base]
    fixed = len(base - set(found))
    kinds = {}
    for k in found:
        kinds[k.split("|")[0]] = kinds.get(k.split("|")[0], 0) + 1
    print("practices: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + f" (baseline {len(base)}, {fixed} fixed since)")
    for k in new:
        print("  FAIL new " + k)
    if fixed:
        print(f"  ({fixed} baseline entries are fixed: run --update-baseline to lock the gain in)")
    return 1 if new else 0


def selftest():
    assert MAT_USE.search("r.material = m") and not MAT_USE.search("r.sharedMaterial = m") and not MAT_USE.search("r.materials")
    assert mat_flags("_AlphaCutoffEnable: 1\n_SurfaceType: 0\n_DoubleSidedEnable: 1") == ("1", "0", "1")
    assert FOLIAGE.search("HiFi_ExtShrubLeaf") and not NOT_FOLIAGE.search("HiFi_ExtShrubLeaf")
    assert NOT_FOLIAGE.search("HiFi_FrontLeaf_Inside") and NOT_FOLIAGE.search("HiFi_ExtShrubStem")
    t = [f.read_text(errors="ignore") for f in sorted((A / "Editor").glob("SpecGreybox*.cs"))]
    foyer = lambda r: [x.replace("Resolution512", r).replace("Resolution1024", r) if "FoyerMirrorProbe" in x else x for x in t]
    r1024, r512 = foyer("Resolution1024"), foyer("Resolution512")   # the foyer mirror at 1024 (Oct 20) and 512 (the fix)
    assert atlas_need([128], [1024]) == 512 * 512 + 1024 * 1024 and atlas_need([512], []) == 1024 * 1024
    h = (A / "Settings/HDRP.asset").read_text(); big = re.sub(r"reflectionProbeTexCacheSize: \d+", f"reflectionProbeTexCacheSize: {8192 << 16 | 4096}", h)
    small = re.sub(r"reflectionProbeTexCacheSize: \d+", "reflectionProbeTexCacheSize: 4096", h)
    assert list(probe_atlas(r1024, small)) and list(probe_atlas(r512, small)), "4096 atlas: 105% / 100% must fail (85% limit)"
    assert not list(probe_atlas(r512, big)) and not list(probe_atlas(r1024, big)), "8192x4096 atlas: 50% / 52% must pass"
    light = lambda typ, sh, lm: f"!u!108 &1\nLight:\n  m_Type: {typ}\n  m_Shadows:\n    m_Type: {sh}\n  m_Lightmapping: {lm}\n"
    scene = "\n--- ".join(["head", light(2, 2, 1), light(2, 0, 1), light(3, 2, 2), light(1, 2, 1), light(0, 1, 4)])
    assert scene_shadow_lights(scene) == 2, "point mixed shadowed + spot realtime shadowed; not baked area, unshadowed, sun"
    prof = lambda v, o=1: f"  maxShadowDistance:\n    m_OverrideState: {o}\n    m_Value: {v}\n"
    assert sun_distance([prof(150), prof(80)]) == 150 and sun_distance([prof(300, 0), prof(80)]) == 80
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        md = Path(t) / "P.md"; md.write_text("## BUDGET\n| pose | mean ms | rest s |\n| static-shadowed-lights | 1 | - |\n| static-sun-distance | 100 | - |\n")
        assert len(list(shadow_budget(scene, [prof(150)], md, ""))) == 2 and not list(shadow_budget(light(2, 2, 1), [prof(80)], md, ""))
        assert not list(shadow_budget(light(2, 2, 1), [prof(150)], md, "const float SunShadowDistance = 80f;"))
    print("selftest ok")


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else run())
