"""props: the props-lane placement tool (Oct 18: prop jobs averaged 37 min, mostly agent steps: finding a model, measuring it,
working out its box, guessing its yaw, writing the entry, a full house build per try). Now: find -> add -> front -> pin, all in the
open editor (no house build). Skill: .claude/skills/change-gate/SKILL.md "Props in 5 minutes".

  python3 tools/house/props.py find dresser pine           owned models (real drawn sizes, w x d x h m at yaw 0) + Poly Haven CC0
  python3 tools/house/props.py get polyhaven rubber_duck_toy   download (1k) -> Assets/Models/PolyHaven/<id>.glb, re-index
  python3 tools/house/props.py add NAME --model PATH|INDEX-NAME --at x,z [--wall C] --back +x|-x|+z|-z|none
          (--floor ground|upper [--y0 Y] | --on PIECE) [--yaw N] [--size w,d,h | --height H] --source "film 296: ..."
          [--hides a,b] [--collide | --no-collide] [--no-refresh]
        writes the store_props.json entry: box = the model's real size (or --size / uniform --height) about --at (spec x,z, the
        footprint centre); --wall C puts the back face 1 cm off the wall plane C; --on PIECE stands it on that piece's top.
        Refuses a duplicate name or a model not in the index. Then places it in the open editor (Refresh Props, seconds).
  python3 tools/house/props.py front NAME...               one contact sheet of each piece seen from its front (from the room, opposite
                                                            `back`; four sides when it has none) -> pin the yaw in one look
  python3 tools/house/props.py pin NAME YAW [NAME YAW...]   write the yaw(s), re-place live
  python3 tools/house/props.py refresh [NAME...]           Home Alone > Refresh Props (changed/new pieces; or the named ones)
  python3 tools/house/props.py index                       rebuild the model-size index from the open editor (sfm-work/props/index.json)
  python3 tools/house/props.py selftest
Spec axes: x = Unity x, z = -Unity z; y0 is above that floor. Editor commands refuse while tools/house/unity_pipeline.sh runs.
Never put personal data in a request: Poly Haven gets the plain User-Agent below and nothing else.
"""
import json
import math
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJ = ROOT / "unity/HomeAlone"
SPEC = ROOT / "spec/dressing/store_props.json"
INDEX = ROOT / "sfm-work/props/index.json"
PH_LIST = ROOT / "sfm-work/props/polyhaven_models.json"
UA = {"User-Agent": "home-alone-house/1.0"}
CLI = Path.home() / ".unity/bin/unity"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
BACK = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+z": (0, 0, -1), "-z": (0, 0, 1)}   # spec axis -> Unity direction


# ---- pure logic (selftest) ----
def footprint(size, yaw, back):
    """(extent along spec x, along spec z) of a model w x d (local x, z) turned by yaw; with no yaw its long side follows the wall
    (StoreProps.Orient does the same)."""
    w, d = size[0], size[1]
    if yaw is not None:
        return (d, w) if round(yaw / 90) % 2 else (w, d)
    if back in ("+x", "-x"):
        return min(w, d), max(w, d)
    if back in ("+z", "-z"):
        return max(w, d), min(w, d)
    raise SystemExit("no --yaw and no --back: give --yaw for a free-standing piece")


def box(size, yaw, back, at, wall=None, gap=0.01):
    ex, ez = footprint(size, yaw, back)
    x0, z0 = at[0] - ex / 2, at[1] - ez / 2
    if wall is not None:
        if back not in BACK:
            raise SystemExit("--wall needs --back")
        if back == "+x": x0 = wall - gap - ex
        if back == "-x": x0 = wall + gap
        if back == "+z": z0 = wall - gap - ez
        if back == "-z": z0 = wall + gap
    return [round(x0, 3), round(x0 + ex, 3)], [round(z0, 3), round(z0 + ez, 3)]


def scaled(native, size=None, height=None):
    if size:
        return list(size)
    k = height / native[2] if height else 1.0
    return [round(v * k, 3) for v in native]


def glue_values(args):
    """'--back -x', '--at -4.8,3.9': argparse reads a value starting with '-' as an option; glue each to its flag."""
    neg = ("--back", "--at", "--wall", "--y0", "--size")
    return [f"{a}={b}" if a in neg else b for a, b in zip([None] + args, args) if b not in neg]


def matches(words, text):
    t = text.lower()
    return all(w.lower() in t for w in words)


# ---- data ----
def load_spec():
    return json.loads(SPEC.read_text())


def save_spec(j):
    SPEC.write_text(json.dumps(j, indent=1, ensure_ascii=False))   # the file's own format (Newtonsoft indent 1, no final newline)


def piece(j, name):
    p = next((p for p in j["pieces"] if p["name"] == name), None)
    if p is None:
        raise SystemExit(f"{name}: not in store_props.json")
    return p


def index():
    if not INDEX.exists():
        print(ev(f'return SpecGreybox.IndexModels("{INDEX}");'))
    return json.loads(INDEX.read_text())["models"]


def model(arg):
    ms = index()
    m = next((m for m in ms if m["path"] == arg), None) or next((m for m in ms if m["name"] == arg), None)
    if m is None:
        raise SystemExit(f"{arg}: not in the model index (props.py find ...; props.py index after importing something new)")
    return m


def polyhaven():
    if not PH_LIST.exists() or time.time() - PH_LIST.stat().st_mtime > 7 * 86400:
        PH_LIST.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request("https://api.polyhaven.com/assets?t=models", headers=UA), timeout=30) as r:
            PH_LIST.write_bytes(r.read())
    return json.loads(PH_LIST.read_text())


# ---- the open editor ----
def editor_free():
    if subprocess.run(["pgrep", "-f", "unity_pipeline.sh"], capture_output=True).stdout.strip():
        raise SystemExit("unity_pipeline.sh is running (a build/load): editor commands wait for it")


def ev(code):
    editor_free()
    out = subprocess.run([str(CLI), "command", "eval", "--code", code], cwd=PROJ, capture_output=True, text=True).stdout
    for line in out.splitlines():
        cols = line.split("\t")
        if len(cols) >= 3 and cols[0] == "eval":
            r = json.loads(cols[2])
            if not r.get("success"):
                raise SystemExit(f"editor eval failed: {r}")
            return r.get("result")
    raise SystemExit(f"no answer from the editor (is it open?): {out[-400:]}")


def refresh(names=()):
    print(ev(f'return SpecGreybox.RefreshProps("{",".join(names)}");' if names else "return SpecGreybox.RefreshProps();"))


# ---- commands ----
def cmd_find(words):
    hits = [m for m in index() if matches(words, m["path"])]
    print(f"owned ({len(hits)}):  w x d x h m at yaw 0")
    for m in hits[:25]:
        odd = "  (raw units: size it with --size/--height)" if max(m["size"]) > 6 else ""   # Sketchfab GLBs come in cm or worse
        print(f"  {m['size'][0]:5.2f} x {m['size'][1]:5.2f} x {m['size'][2]:5.2f}  {m['path']}{odd}")
    try:
        ph = polyhaven()
    except OSError as e:
        print(f"Poly Haven: unreachable ({e})"); return
    hp = [(k, v) for k, v in ph.items() if matches(words, " ".join([k, v["name"], *v.get("tags", []), *v.get("categories", [])]))]
    print(f"Poly Haven CC0 ({len(hp)}):  (props.py get polyhaven ID)")
    for k, v in hp[:15]:
        d = [x / 1000 for x in v.get("dimensions", [0, 0, 0])]
        print(f"  {d[0]:5.2f} x {d[1]:5.2f} x {d[2]:5.2f}  {k}  ({v['name']})")


def cmd_get(src, pid, res="1k"):
    if src != "polyhaven":
        raise SystemExit("get: only 'polyhaven ID' (owned packs are already in the index)")
    with urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{pid}", headers=UA), timeout=30) as r:
        g = json.load(r)["gltf"][res]["gltf"]
    d = ROOT / "sfm-work/polyhaven" / pid
    for rel, f in [(Path(g["url"]).name, g), *g["include"].items()]:
        out = d / rel
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(urllib.request.Request(f["url"], headers=UA), timeout=60) as r:
                out.write_bytes(r.read())
    glb = PROJ / f"Assets/Models/PolyHaven/{pid}.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    expr = ("import bpy,sys; bpy.ops.wm.read_factory_settings(use_empty=True); "
            f"bpy.ops.import_scene.gltf(filepath={str(d / Path(g['url']).name)!r}); "
            f"bpy.ops.export_scene.gltf(filepath={str(glb)!r}, export_format='GLB', export_yup=True)")
    subprocess.run([BLENDER, "-b", "--factory-startup", "--python-expr", expr], check=True, capture_output=True)
    print("wrote", glb.relative_to(ROOT))
    ev("UnityEditor.AssetDatabase.Refresh(); return \"ok\";")
    for _ in range(60):   # wait for the import before indexing it
        if ev("return (UnityEditor.EditorApplication.isCompiling||UnityEditor.EditorApplication.isUpdating)+\"\";") == "False":
            break
        time.sleep(2)
    print(ev(f'return SpecGreybox.IndexModels("{INDEX}");'))
    print(json.dumps(model(f"Assets/Models/PolyHaven/{pid}.glb")))


def cmd_add(a):
    j = load_spec()
    if any(p["name"] == a.name for p in j["pieces"]):
        raise SystemExit(f"{a.name}: already in store_props.json (pin/edit it, or pick another name)")
    m = model(a.model)
    back = "" if a.back == "none" else a.back
    size = scaled(m["size"], a.size and [float(v) for v in a.size.split(",")], a.height)
    at = [float(v) for v in a.at.split(",")]
    x, z = box(size, a.yaw, back, at, a.wall)
    if a.on:
        base = piece(j, a.on)
        floor, y0 = base.get("floor", "ground"), round(base["y0"] + base["height"], 3)
    else:
        if not a.floor:
            raise SystemExit("--floor ground|upper (or --on PIECE)")
        floor, y0 = a.floor, a.y0
    k = size[2] / m["size"][2]
    note = (f"Model {m['size'][0]} x {m['size'][1]} x {m['size'][2]} m ({m['name']})"
            + (", native size" if abs(k - 1) < 1e-3 and size == m["size"] else f", fitted to {size[0]} x {size[1]} x {size[2]}"))
    e = {"name": a.name, "prefab": m["path"], "x": x, "z": z, "y0": y0, "height": size[2], "back": back}
    if a.yaw is not None:
        e["yaw"] = a.yaw
    e["collide"] = a.collide if a.collide is not None else size[2] >= 0.4
    if floor == "upper":
        e["floor"] = "upper"
    e["hides"] = [h for h in (a.hides or "").split(",") if h]
    e["source"] = f"props lane (props.py add, {time.strftime('%b %d')}): {a.source}. {note}."
    j["pieces"].append(e)
    save_spec(j)
    print(json.dumps(e, indent=1))
    if a.yaw is None:
        print("yaw not pinned: props.py front", a.name, "then props.py pin", a.name, "YAW")
    if not a.no_refresh:
        refresh([a.name])


def cmd_pin(args):
    j = load_spec()
    pairs = list(zip(args[::2], args[1::2]))
    for n, y in pairs:
        piece(j, n)["yaw"] = float(y) if "." in y else int(y)
    save_spec(j)
    refresh([n for n, _ in pairs])


def cam_poses(c, s, back):
    """camera (pos, look, near) per view: from the front (opposite `back`), or four sides. Unity coords; near clips whatever stands
    between the camera and the piece (a wall behind the camera position in a small room)."""
    dirs = [(-BACK[back][0], 0, -BACK[back][2])] if back in BACK else [(-1, 0, 0), (1, 0, 0), (0, 0, 1), (0, 0, -1)]
    out = []
    for f in dirs:
        half_depth = abs(f[0]) * s[0] / 2 + abs(f[2]) * s[2] / 2
        span = max(abs(f[2]) * s[0] + abs(f[0]) * s[2], s[1])
        dist = max(0.45, half_depth + 1.25 * span / 2 / math.tan(math.radians(20)))
        pos = (c[0] + f[0] * dist, c[1] + 0.25 * max(s[1], 0.3), c[2] + f[2] * dist)
        out.append((pos, c, max(0.03, dist - half_depth - 0.05), f))
    return out


def cmd_front(names):
    j = load_spec()
    tiles = []
    for n in names:
        p = piece(j, n)
        b = ev(f'return SpecGreybox.PropBounds("{n}");')
        if b == "none":
            print(f"{n}: not in the open scene (props.py refresh {n})"); continue
        v = [float(t) for t in b.split()]
        for i, (pos, look, near, f) in enumerate(cam_poses(v[:3], v[3:], p.get("back", ""))):
            shot = f"front-{n}-{i}"
            args = [*(f"{q:.3f}" for q in (*pos, *look)), "40", f"{near:.3f}", "day"]
            path = subprocess.run([str(ROOT / "tools/house/unity_pipeline.sh"), "cam", shot, *args], capture_output=True, text=True).stdout.strip().splitlines()[-1]
            side = {(-1, 0, 0): "-x", (1, 0, 0): "+x", (0, 0, 1): "-z", (0, 0, -1): "+z"}[f]
            tiles.append((path, f"{n}  yaw {p.get('yaw', 'auto')}  back {p.get('back') or 'none'}  seen from {side}"))
    if not tiles:
        return
    out = ROOT / "spec/captures/props-front.png"
    code = ("import sys,json; from PIL import Image, ImageDraw\n"
            "t=json.loads(sys.argv[2]); W,H=640,360; cols=min(3,len(t)); rows=(len(t)+cols-1)//cols\n"
            "s=Image.new('RGB',(W*cols,(H+24)*rows),'white'); d=ImageDraw.Draw(s)\n"
            "for i,(p,l) in enumerate(t):\n"
            " x,y=(i%cols)*W,(i//cols)*(H+24); s.paste(Image.open(p).convert('RGB').resize((W,H)),(x,y+24)); d.text((x+6,y+6),l,fill='black')\n"
            "s.save(sys.argv[1])")
    subprocess.run(["uv", "run", "-q", "--with", "pillow", "python", "-I", "-c", code, str(out), json.dumps(tiles)], check=True)
    print(out)


def selftest():
    # footprint/box: a 1.0 x 0.5 dresser at yaw 0 / 90, its back 1 cm off a wall
    assert footprint([1.0, 0.5, 0.8], 0, "") == (1.0, 0.5) and footprint([1.0, 0.5, 0.8], 90, "") == (0.5, 1.0)
    assert footprint([1.0, 0.5, 0.8], None, "+x") == (0.5, 1.0) and footprint([0.5, 1.0, 0.8], None, "-z") == (1.0, 0.5)
    assert box([1.0, 0.5, 0.8], 180, "-z", (8.0, 99), wall=3.851) == ([7.5, 8.5], [3.861, 4.361])
    assert box([1.0, 0.5, 0.8], 90, "+x", (99, 5.0), wall=10.13) == ([9.62, 10.12], [4.5, 5.5])
    assert box([0.2, 0.1, 0.3], 0, "", (1, 2)) == ([0.9, 1.1], [1.95, 2.05])
    assert scaled([0.2, 0.3, 0.29], height=0.145) == [0.1, 0.15, 0.145] and scaled([1, 2, 3], size=[4, 5, 6]) == [4, 5, 6]
    try:
        footprint([1, 1, 1], None, ""); raise AssertionError("free-standing without yaw must refuse")
    except SystemExit:
        pass
    assert glue_values(["n", "--back", "-x", "--at", "-4.8,3.9", "--yaw", "90"]) == ["n", "--back=-x", "--at=-4.8,3.9", "--yaw", "90"]
    assert matches(["dresser", "PINE"], "Assets/Pine/Dresser.prefab") and not matches(["oak"], "Assets/Pine/Dresser.prefab")
    # front camera: a back on -z (Unity +z) is seen from Unity -z, looking at the centre; near never past the piece
    (pos, look, near, f), = cam_poses([0, 1, 0], [1.0, 0.8, 0.5], "-z")
    assert f == (0, 0, -1) and pos[2] < -0.25 and near < -pos[2] - 0.05 and len(cam_poses([0, 1, 0], [1, 1, 1], "")) == 4
    # duplicate refusal + index read, on the real spec/index (read-only)
    j = load_spec(); first = j["pieces"][0]["name"]
    class A: name = first
    try:
        cmd_add(A); raise AssertionError("duplicate must refuse")
    except SystemExit as e:
        assert "already" in str(e)
    if INDEX.exists():
        m = model(j["pieces"][0]["prefab"]); assert len(m["size"]) == 3 and all(v > 0 for v in m["size"])
    print("props selftest: ok")


def main():
    import argparse
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); return
    c, rest = sys.argv[1], sys.argv[2:]
    if c == "find": cmd_find(rest)
    elif c == "get": cmd_get(*rest)
    elif c == "pin": cmd_pin(rest)
    elif c == "front": cmd_front(rest)
    elif c == "refresh": refresh(rest)
    elif c == "index": print(ev(f'return SpecGreybox.IndexModels("{INDEX}");'))
    elif c == "selftest": selftest()
    elif c == "add":
        ap = argparse.ArgumentParser(prog="props.py add")
        ap.add_argument("name"); ap.add_argument("--model", required=True); ap.add_argument("--at", required=True)
        ap.add_argument("--wall", type=float); ap.add_argument("--back", required=True, choices=["+x", "-x", "+z", "-z", "none"])
        ap.add_argument("--floor", choices=["ground", "upper"]); ap.add_argument("--y0", type=float, default=0.0); ap.add_argument("--on")
        ap.add_argument("--yaw", type=int); ap.add_argument("--size"); ap.add_argument("--height", type=float)
        ap.add_argument("--source", required=True); ap.add_argument("--hides"); ap.add_argument("--no-refresh", action="store_true")
        ap.add_argument("--collide", dest="collide", action="store_true", default=None); ap.add_argument("--no-collide", dest="collide", action="store_false")
        rest = glue_values(rest)
        cmd_add(ap.parse_args(rest))
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
