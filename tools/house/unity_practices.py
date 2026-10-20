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
"""
import json, re, subprocess, sys
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


def tracked(keys):
    files = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split())
    return [k for k in keys if k.split("|")[1] in files]


def run():
    found = sorted(set(list(obsolete()) + list(material_access()) + list(foliage()) + list(textures())))
    if "--update-baseline" in sys.argv:
        keep = tracked(found)
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
    print("selftest ok")


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else run())
