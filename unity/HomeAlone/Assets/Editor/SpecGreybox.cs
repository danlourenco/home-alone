using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

/// Grey-box generator (docs/RECONCILIATION.md, step 3). Reads ONLY spec/house_spec.json (written by
/// tools/house/reconcile.py) and builds Assets/Scenes/Greybox_Upstairs.unity: floors, ceilings, walls with door
/// openings, stair rails, prop doors, an adult-capsule walk test through every door, and checking captures.
/// No geometry constants live here; change the spec, not this file.
/// Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.Build -quit -logFile -
public static class SpecGreybox
{
    const float HalfWall = 0.07f;      // each space builds half of the spec's 14 cm interior wall, outward
    const float ArchHead = 2.20f;      // arches: header height (not measured yet)
    const float RailHeight = 0.95f;
    const float CasingW = 0.07f, CasingProud = 0.02f;   // door trim: 2 3/4 in wide, 3/4 in proud (Marina's doors have it)
    static Material mFloor, mWall, mCeil, mHall, mProp, mRail;

    // "-variant measured" (command line) builds/renders spec/house_spec.measured.json: walls as measured, not thinned.
    static string Variant
    {
        get { var a = System.Environment.GetCommandLineArgs(); int i = System.Array.IndexOf(a, "-variant"); return i >= 0 && i + 1 < a.Length ? a[i + 1] : ""; }
    }
    static string Tag => Variant == "" ? "" : "." + Variant;
    static string SceneTag => Variant == "" ? "" : "_" + Variant;
    static string SpecPath => Path.GetFullPath(Path.Combine(Application.dataPath, $"../../../spec/house_spec{Tag}.json"));
    static string CaptureDir => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures"));

    class Door { public string a, b, kind; public bool alongX; public float coord, lo, hi, height; }
    class Space { public string name, kind, opens; public float ceil; public List<Vector2> pts; }

    static string GroundPath => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.ground.json"));
    static float FloorY;   // vertical offset of the floor being built (ground floor sits at -floor_to_floor); Box adds it

    static (List<Space>, List<Door>) Parse(JObject j)
    {
        var spaces = j["spaces"].Select(s => new Space {
            name = (string)s["name"], kind = (string)s["kind"], ceil = (float)s["ceiling_m"], opens = (string)s["opens"],
            pts = s["polygon_xz"].Select(p => new Vector2((float)p[0], -(float)p[1])).ToList() }).ToList();
        // spec_axis "z": the wall is the line z = coord and the door spans x (and vice versa).
        // The spec's z runs DOWN the overhead image (south); Unity is left-handed, so world z = -spec z keeps the
        // plan un-mirrored (north up, east right when seen from above).
        var doors = j["doors"].Select(d => {
            bool alongX = (string)d["spec_axis"] == "z";
            float c = (float)d["wall_coord_spec"], l = (float)d["span_spec"][0], h = (float)d["span_spec"][1];
            return new Door {
                a = (string)d["between"][0], b = (string)d["between"][1], kind = (string)d["kind"], alongX = alongX,
                coord = alongX ? -c : c, lo = alongX ? l : -h, hi = alongX ? h : -l,
                height = d["height"].Type == JTokenType.Null ? 0f : (float)d["height"] };
        }).ToList();
        return (spaces, doors);
    }

    // holes: openings of the floor above (its stairwells); this floor's ceiling stays open under them
    static void BuildFloor(GameObject root, GameObject ceilings, List<Space> spaces, List<Door> doors, List<Space> holes = null)
    {
        holes ??= new List<Space>();
        foreach (var s in spaces)
        {
            var g = Child(root, s.name);
            if (s.kind != "opening")
            {
                foreach (var (x0, x1, z0, z1) in Cells(s.pts))
                    Box(g, "Floor", x0, x1, z0, z1, -0.2f, 0f, s.kind == "hall" && FloorY == 0f ? mHall : mFloor);   // ground halls: wood (Marina's foyer)
                var hx = holes.SelectMany(h => h.pts.Select(p => p.x)); var hz = holes.SelectMany(h => h.pts.Select(p => p.y));
                foreach (var (x0, x1, z0, z1) in Cells(s.pts, hx, hz))
                    if (!holes.Any(h => Inside(h.pts, new Vector2((x0 + x1) / 2, (z0 + z1) / 2))))
                        Box(ceilings, s.name + "_Ceiling", x0, x1, z0, z1, s.ceil, s.ceil + 0.15f, mCeil);
                Walls(g, s, doors);
            }
            else
            {
                // stairwells build their own walls (doorways, rails and stair heads are cut out), so no side is open to
                // the outside; an "up" stairwell (attic) also has this floor's floor under it
                if (s.opens == "up")
                    foreach (var (x0, x1, z0, z1) in Cells(s.pts)) Box(g, "Floor", x0, x1, z0, z1, -0.2f, 0f, mHall);
                Walls(g, s, doors);
                foreach (var d in doors.Where(d => d.kind == "rail" && (d.a == s.name || d.b == s.name)))
                    Rail(g, d);
            }
        }
        Lights(root, spaces);
    }

    [MenuItem("HomeAlone/Build Greybox From Spec")]
    public static void Build()
    {
        var j = JObject.Parse(File.ReadAllText(SpecPath));
        var (spaces, doors) = Parse(j);
        var gj = File.Exists(GroundPath) ? JObject.Parse(File.ReadAllText(GroundPath)) : null;

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        MakeMaterials();
        FloorY = 0f;
        var root = new GameObject("Upstairs");
        var ceilings = Child(root, "Ceilings");
        BuildFloor(root, ceilings, spaces, doors);
        var stairPath = Stair(root, j["stair"], skipFloorPatch: gj != null);
        string report = "";
        List<Space> gspaces = null; List<Door> gdoors = null; GameObject groot = null, gceil = null;
        if (gj != null)
        {
            (gspaces, gdoors) = Parse(gj);
            FloorY = (float)gj["floor_y_m"];
            groot = new GameObject("Ground"); gceil = Child(groot, "Ceilings");
            BuildFloor(groot, gceil, gspaces, gdoors, spaces.Where(s => s.opens == "down").ToList());
            FloorY = 0f;
        }
        Volume(root);
        Player(spaces.First(s => s.name == "hall_corridor"));

        var player = GameObject.Find("Player"); player.SetActive(false);   // the test bodies walk alone
        Physics.SyncTransforms();
        report += "UPSTAIRS\n" + WalkTest(spaces, doors);
        if (gj != null) { FloorY = (float)gj["floor_y_m"]; report += "GROUND\n" + WalkTest(gspaces, gdoors); FloorY = 0f; }
        report += StairWalk(stairPath);
        report += LeakAndHeadroom(spaces, gspaces, gj != null ? (float)gj["floor_y_m"] : 0f);
        report += "UPSTAIRS " + RoomWalk(spaces, doors);
        if (gj != null) { FloorY = (float)gj["floor_y_m"]; report += "GROUND " + RoomWalk(gspaces, gdoors); FloorY = 0f; }
        player.SetActive(true);
        Furniture(root);   // after the gates: placeholder furniture is for feel walks, not geometry checks
        Directory.CreateDirectory(CaptureDir);
        File.WriteAllText(Path.Combine(CaptureDir, $"walk-test{Tag}.txt"), report);
        if (Variant == "")
        {
            Captures(spaces, ceilings);
            if (gj != null)
            {   // ground plan view: upper floor and ground ceilings hidden
                root.SetActive(false); gceil.SetActive(false);
                PlanShot(gspaces.Concat(spaces).ToList(), "plan-topdown-ground");
                root.SetActive(true); gceil.SetActive(true);
            }
        }
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), $"Assets/Scenes/Greybox_Upstairs{SceneTag}.unity");
        Debug.Log("SpecGreybox: built from " + SpecPath + (gj != null ? " + " + GroundPath : "") + "\n" + report);
    }

    // spec/furniture.json: standard-size placeholder boxes placed from Marina's views (sources in the file)
    static void Furniture(GameObject root)
    {
        var f = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/furniture.json"));
        if (!File.Exists(f)) return;
        var g = Child(root, "Furniture"); var m = Mat("Furniture", new Color(0.36f, 0.24f, 0.15f));
        foreach (var p in JObject.Parse(File.ReadAllText(f))["pieces"])
        {
            float V(string k, int i) => (float)p[k][i];
            Box(g, (string)p["name"], V("x", 0), V("x", 1), -V("z", 1), -V("z", 0), V("y", 0), V("y", 1), m);
        }
    }

    static void PlanShot(List<Space> spaces, string name)
    {
        var go = new GameObject("PlanCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>();
        var rt = new RenderTexture(1600, 1600, 24); cam.targetTexture = rt;
        var all = spaces.SelectMany(s => s.pts).ToList();
        float cx = (all.Min(p => p.x) + all.Max(p => p.x)) / 2, cz = (all.Min(p => p.y) + all.Max(p => p.y)) / 2;
        float span = Mathf.Max(all.Max(p => p.x) - all.Min(p => p.x), all.Max(p => p.y) - all.Min(p => p.y));
        cam.orthographic = true; cam.orthographicSize = span / 2 + 0.6f; cam.farClipPlane = 60f;
        go.transform.position = new Vector3(cx, 20f, cz); go.transform.rotation = Quaternion.LookRotation(Vector3.down, Vector3.forward);
        Shot(cam, rt, name);
        RenderTexture.active = null; Object.DestroyImmediate(go); rt.Release();
    }

    // Rectilinear polygon -> covering rectangles (grid of its own coordinates, keep cells whose centre is inside).
    static IEnumerable<(float, float, float, float)> Cells(List<Vector2> pts, IEnumerable<float> extraX = null, IEnumerable<float> extraZ = null)
    {
        float x0 = pts.Min(p => p.x), x1 = pts.Max(p => p.x), z0 = pts.Min(p => p.y), z1 = pts.Max(p => p.y);
        var xs = pts.Select(p => p.x).Concat((extraX ?? Enumerable.Empty<float>()).Where(v => v > x0 && v < x1)).Distinct().OrderBy(v => v).ToList();
        var zs = pts.Select(p => p.y).Concat((extraZ ?? Enumerable.Empty<float>()).Where(v => v > z0 && v < z1)).Distinct().OrderBy(v => v).ToList();
        for (int i = 0; i + 1 < xs.Count; i++)
            for (int k = 0; k + 1 < zs.Count; k++)
                if (Inside(pts, new Vector2((xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2)))
                    yield return (xs[i], xs[i + 1], zs[k], zs[k + 1]);
    }

    static bool Inside(List<Vector2> poly, Vector2 p)
    {
        bool c = false;
        for (int i = 0, n = poly.Count; i < n; i++)
        {
            Vector2 a = poly[i], b = poly[(i + 1) % n];
            if ((a.y > p.y) != (b.y > p.y) && p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x) c = !c;
        }
        return c;
    }

    // Each edge gets a wall slab just outside the room (HalfWall thick), from floor to the room's ceiling,
    // with doorways cut out. Two neighbours 14 cm apart therefore meet in one full wall.
    static void Walls(GameObject g, Space s, List<Door> doors)
    {
        for (int i = 0, n = s.pts.Count; i < n; i++)
        {
            Vector2 a = s.pts[i], b = s.pts[(i + 1) % n];
            bool alongX = Mathf.Abs(a.y - b.y) < 1e-4f;       // wall line z = const, runs along x
            float coord = alongX ? a.y : a.x;
            float lo = alongX ? Mathf.Min(a.x, b.x) : Mathf.Min(a.y, b.y), hi = alongX ? Mathf.Max(a.x, b.x) : Mathf.Max(a.y, b.y);
            // outward side: probe just off the edge midpoint
            var mid = alongX ? new Vector2((lo + hi) / 2, coord) : new Vector2(coord, (lo + hi) / 2);
            var probe = mid + (alongX ? new Vector2(0, 0.02f) : new Vector2(0.02f, 0));
            float sgn = Inside(s.pts, probe) ? -1f : 1f;
            float t0 = coord, t1 = coord + sgn * HalfWall;

            var cuts = doors.Where(d => (d.a == s.name || d.b == s.name) && d.alongX == alongX
                                        && Mathf.Abs(d.coord - coord) < 0.35f && d.hi > lo && d.lo < hi)
                            .OrderBy(d => d.lo).ToList();
            float cur = lo;
            foreach (var d in cuts)
            {
                if (d.kind == "fake_door") { Prop(g, alongX, t0, t1, sgn, d); continue; }
                float dl = Mathf.Max(d.lo, lo), dh = Mathf.Min(d.hi, hi);
                if (dl > cur) Seg(g, "Wall", alongX, t0, t1, cur, dl, 0f, s.ceil);
                float head = d.kind == "door" ? d.height : d.kind == "arch" ? ArchHead : s.ceil;
                if (head < s.ceil) Seg(g, d.kind + "_Header", alongX, t0, t1, dl, dh, head, s.ceil);
                if (d.kind == "door")
                {   // casing on this room's face: two legs and a head, proud of the wall toward the room
                    float f0 = t0, f1 = t0 - sgn * CasingProud;
                    Trim(g, alongX, f0, f1, dl - CasingW, dl, 0f, head + CasingW);
                    Trim(g, alongX, f0, f1, dh, dh + CasingW, 0f, head + CasingW);
                    Trim(g, alongX, f0, f1, dl - CasingW, dh + CasingW, head, head + CasingW);
                }
                cur = Mathf.Max(cur, dh);
            }
            if (cur < hi) Seg(g, "Wall", alongX, t0, t1, cur, hi, 0f, s.ceil);
        }
    }

    static void Seg(GameObject p, string n, bool alongX, float t0, float t1, float s0, float s1, float y0, float y1)
    {
        float ta = Mathf.Min(t0, t1), tb = Mathf.Max(t0, t1);
        if (alongX) Box(p, n, s0, s1, ta, tb, y0, y1, mWall); else Box(p, n, ta, tb, s0, s1, y0, y1, mWall);
    }

    static void Trim(GameObject p, bool alongX, float t0, float t1, float s0, float s1, float y0, float y1)
    {
        float ta = Mathf.Min(t0, t1), tb = Mathf.Max(t0, t1);
        if (alongX) Box(p, "Casing", s0, s1, ta, tb, y0, y1, mProp); else Box(p, "Casing", ta, tb, s0, s1, y0, y1, mProp);
    }

    static void Prop(GameObject p, bool alongX, float t0, float t1, float sgn, Door d)
    {
        // a door slab 3 cm proud of the wall on the room side; no opening behind it
        float face = t0 - sgn * 0.03f;
        if (alongX) Box(p, "PropDoor", d.lo, d.hi, Mathf.Min(face, t0), Mathf.Max(face, t0), 0f, d.height, mProp);
        else Box(p, "PropDoor", Mathf.Min(face, t0), Mathf.Max(face, t0), d.lo, d.hi, 0f, d.height, mProp);
    }

    static void Rail(GameObject p, Door d)
    {
        var g = Child(p, "Rail");
        if (d.alongX) Box(g, "Rail", d.lo, d.hi, d.coord - 0.03f, d.coord + 0.03f, 0f, RailHeight, mRail);
        else Box(g, "Rail", d.coord - 0.03f, d.coord + 0.03f, d.lo, d.hi, 0f, RailHeight, mRail);
    }

    static void Box(GameObject p, string n, float x0, float x1, float z0, float z1, float y0, float y1, Material m)
    {
        if (x1 - x0 < 1e-3f || z1 - z0 < 1e-3f || y1 - y0 < 1e-3f) return;
        var b = GameObject.CreatePrimitive(PrimitiveType.Cube); b.name = n; b.transform.parent = p.transform;
        b.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2 + FloorY, (z0 + z1) / 2);
        b.transform.localScale = new Vector3(x1 - x0, y1 - y0, z1 - z0);
        b.GetComponent<MeshRenderer>().sharedMaterial = m; b.isStatic = true;
    }

    static GameObject Child(GameObject p, string n) { var c = new GameObject(n); c.transform.parent = p.transform; return c; }

    static void MakeMaterials()
    {
        Directory.CreateDirectory("Assets/Materials/Greybox");
        mFloor = Mat("Floor", new Color(0.50f, 0.40f, 0.30f)); mHall = Mat("HallRunner", new Color(0.45f, 0.10f, 0.10f));
        mWall = Mat("Wall", new Color(0.82f, 0.80f, 0.74f)); mCeil = Mat("Ceiling", new Color(0.92f, 0.92f, 0.90f));
        mProp = Mat("PropDoor", new Color(0.95f, 0.93f, 0.86f)); mRail = Mat("Rail", new Color(0.30f, 0.18f, 0.10f));
    }

    static Material Mat(string n, Color c)
    {
        string path = $"Assets/Materials/Greybox/{n}.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("HDRP/Lit")); AssetDatabase.CreateAsset(m, path); }
        m.SetColor("_BaseColor", c); m.SetFloat("_Smoothness", 0.2f); return m;
    }

    static void Lights(GameObject root, List<Space> spaces)
    {
        var lights = Child(root, "Lights");
        foreach (var s in spaces.Where(s => s.kind != "opening"))
        {
            var (x, z) = (s.pts.Average(p => p.x), s.pts.Average(p => p.y));
            var l = new GameObject("Light_" + s.name).AddComponent<Light>(); l.transform.parent = lights.transform;
            l.transform.position = new Vector3(x, s.ceil - 0.3f + FloorY, z); l.type = LightType.Point; l.range = 8f;
            l.intensity = 900f; l.color = new Color(1f, 0.95f, 0.88f); l.gameObject.AddComponent<HDAdditionalLightData>();
        }
    }

    static void Volume(GameObject root)
    {
        Directory.CreateDirectory("Assets/Settings");
        string vp = "Assets/Settings/GreyboxVolume.asset";
        AssetDatabase.DeleteAsset(vp);
        var profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, vp);
        var env = profile.Add<VisualEnvironment>(true); env.skyType.value = (int)SkyType.PhysicallyBased; AssetDatabase.AddObjectToAsset(env, profile);
        var sky = profile.Add<PhysicallyBasedSky>(true); AssetDatabase.AddObjectToAsset(sky, profile);
        var exp = profile.Add<Exposure>(true); exp.mode.value = ExposureMode.Automatic; exp.limitMin.value = 4f; exp.limitMax.value = 12f; AssetDatabase.AddObjectToAsset(exp, profile);
        var vol = new GameObject("GlobalVolume").AddComponent<Volume>(); vol.transform.parent = root.transform; vol.isGlobal = true; vol.sharedProfile = profile;
    }

    // The main stair: solid steps, landing, rails and well walls as spec boxes (spec z -> world -z); returns the walk path.
    static List<Vector3> Stair(GameObject root, JToken st, bool skipFloorPatch)
    {
        if (st == null || st.Type == JTokenType.Null) return new List<Vector3>();
        var g = Child(root, "MainStair");
        foreach (var b in st["boxes"])
        {
            string kind = (string)b["kind"];
            if (kind == "floor" && skipFloorPatch) continue;   // the ground floor's foyer is built for real
            var m = kind == "rail" ? mRail : kind == "wall" ? mWall : kind == "floor" ? mFloor : kind == "ceiling" ? mCeil : mHall;
            Box(g, (string)b["name"], (float)b["x"][0], (float)b["x"][1], -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0], (float)b["y"][1], m);
        }
        return st["walk_path"].Select(q => new Vector3((float)q[0], (float)q[1], -(float)q[2])).ToList();
    }

    // Both bodies walk the stair path up and back down with a real CharacterController (gravity, 0.3 m step offset).
    // A leg passes when the body ends within 0.15 m of the waypoint (horizontally) and 0.1 m of its floor height.
    static string StairWalk(List<Vector3> path)
    {
        if (path.Count < 2) return "";
        var lines = new List<string>(); int bad = 0;
        foreach (var (name, r, h) in new[] { ("bandit", 0.275f, 1.85f), ("kevin", 0.20f, 1.20f) })
        {
            var go = new GameObject("StairWalker_" + name); var cc = go.AddComponent<CharacterController>();
            cc.radius = r; cc.height = h; cc.center = new Vector3(0, h / 2, 0); cc.stepOffset = 0.3f; cc.skinWidth = 0.02f;
            foreach (var (route, pts) in new[] { ("up", path), ("down", Enumerable.Reverse(path).ToList()) })
            {
                go.transform.position = pts[0] + Vector3.up * 0.05f; Physics.SyncTransforms();
                for (int i = 1; i < pts.Count; i++)
                {
                    Vector3 target = pts[i]; float vy = 0f;
                    for (int t = 0; t < 1500; t++)
                    {
                        var p = go.transform.position; var flat = new Vector3(target.x - p.x, 0, target.z - p.z);
                        if (flat.magnitude < 0.05f) break;
                        vy = cc.isGrounded ? -1f : vy - 9.81f * 0.02f;
                        cc.Move(Vector3.ClampMagnitude(flat, 0.03f) + Vector3.up * vy * 0.02f);
                    }
                    for (int t = 0; t < 25; t++) cc.Move(Vector3.down * 0.05f);   // settle onto the floor
                    var e = go.transform.position; float dxz = new Vector2(e.x - target.x, e.z - target.z).magnitude, dy = Mathf.Abs(e.y - target.y);
                    bool ok = dxz < 0.15f && dy < 0.1f; if (!ok) bad++;
                    string by = "";
                    if (!ok && Physics.CapsuleCast(e + Vector3.up * (r + 0.05f), e + Vector3.up * (h - r), r * 0.98f,
                                                   new Vector3(target.x - e.x, 0, target.z - e.z).normalized, out var hit, 1f))
                        by = $" by {hit.collider.transform.parent?.name}/{hit.collider.name} at ({e.x:F2}, {e.y:F2}, {-e.z:F2}) spec x,y,z";
                    lines.Add($"{(ok ? "ok     " : "BLOCKED")} {name} {route} leg {i}: ended {dxz:F2} m from waypoint, {dy:F2} m off its floor height{by}");
                }
            }
            Object.DestroyImmediate(go);
        }
        lines.Insert(0, $"Stair walk test (both bodies, up and down): {lines.Count} legs, {bad} blocked");
        return string.Join("\n", lines) + "\n";
    }

    // Both bodies walk from 0.5 m inside every doorway of a room to the middle of its widest floor cell and back,
    // with a real CharacterController: every room's interior is reachable, not just its doorway (closets excluded).
    static string RoomWalk(List<Space> spaces, List<Door> doors)
    {
        var lines = new List<string>(); int bad = 0, n = 0;
        foreach (var (name, r, h) in new[] { ("bandit", 0.275f, 1.85f), ("kevin", 0.20f, 1.20f) })
        {
            var go = new GameObject("RoomWalker_" + name); var cc = go.AddComponent<CharacterController>();
            cc.radius = r; cc.height = h; cc.center = new Vector3(0, h / 2, 0); cc.stepOffset = 0.3f; cc.skinWidth = 0.02f;
            foreach (var s in spaces.Where(s => s.kind == "room" || s.kind == "hall"))
            {
                var c = Cells(s.pts).OrderByDescending(q => Mathf.Min(q.Item2 - q.Item1, q.Item4 - q.Item3)).First();
                var mid = new Vector3((c.Item1 + c.Item2) / 2, FloorY, (c.Item3 + c.Item4) / 2);
                foreach (var d in doors.Where(d => (d.a == s.name || d.b == s.name) && (d.kind == "door" || d.kind == "arch" || d.kind == "open")))
                {
                    float m = (d.lo + d.hi) / 2;
                    Vector3 W(float off) => d.alongX ? new Vector3(m, FloorY, d.coord + off) : new Vector3(d.coord + off, FloorY, m);
                    var start = Inside(s.pts, new Vector2(W(0.5f).x, W(0.5f).z)) ? W(0.5f) : W(-0.5f);
                    foreach (var (from, to) in new[] { (start, mid), (mid, start) })
                    {
                        n++;
                        go.transform.position = from + Vector3.up * 0.05f; Physics.SyncTransforms(); float vy = 0;
                        for (int t = 0; t < 1500; t++)
                        {
                            var p = go.transform.position; var flat = new Vector3(to.x - p.x, 0, to.z - p.z);
                            if (flat.magnitude < 0.05f) break;
                            vy = cc.isGrounded ? -1f : vy - 9.81f * 0.02f;
                            cc.Move(Vector3.ClampMagnitude(flat, 0.03f) + Vector3.up * vy * 0.02f);
                        }
                        var e = go.transform.position; float dxz = new Vector2(e.x - to.x, e.z - to.z).magnitude;
                        if (dxz > 0.2f || Mathf.Abs(e.y - to.y) > 0.15f) { bad++; lines.Add($"BLOCKED {name} {s.name} via {d.a}/{d.b}: ended {dxz:F2} m short"); }
                    }
                }
            }
            Object.DestroyImmediate(go);
        }
        lines.Insert(0, $"Room walk test (both bodies, every doorway to room centre and back): {n} legs, {bad} blocked");
        return string.Join("\n", lines) + "\n";
    }

    // Leaks: from a 0.5 m grid at eye height in every space (both floors), rays go up and in 16 horizontal directions.
    // A ray that hits nothing within 40 m escaped the house (a hole to the sky or outside). The grey-box has no windows,
    // so every escape is a defect. Headroom: on the ground floor, any grid point with < 2.0 m clear above the floor is
    // reported with the object above it; only the main stair's flight 1 (steps, rails) may stand there.
    static string LeakAndHeadroom(List<Space> up, List<Space> ground, float gy)
    {
        var lines = new List<string>(); int leaks = 0, low = 0, pts = 0;
        var floors = new List<(List<Space>, float)> { (up, 0f) }; if (ground != null) floors.Add((ground, gy));
        foreach (var (spaces, y0) in floors)
            foreach (var s in spaces.Where(s => s.kind == "room" || s.kind == "hall" || s.kind == "opening"))
            {
                float x0 = s.pts.Min(p => p.x), x1 = s.pts.Max(p => p.x), z0 = s.pts.Min(p => p.y), z1 = s.pts.Max(p => p.y);
                for (float x = x0 + 0.25f; x < x1; x += 0.5f)
                    for (float z = z0 + 0.25f; z < z1; z += 0.5f)
                    {
                        if (!Inside(s.pts, new Vector2(x, z))) continue;
                        pts++;
                        var eye = new Vector3(x, y0 + 1.6f, z);
                        var dirs = new List<Vector3> { Vector3.up };
                        for (int k = 0; k < 16; k++) dirs.Add(Quaternion.Euler(0, k * 22.5f, 0) * Vector3.forward);
                        foreach (var d in dirs)
                            if (!(s.opens == "up" && d == Vector3.up) && !Physics.Raycast(eye, d, 40f))   // attic not built: open above, listed in DEVIATIONS
                            { leaks++; lines.Add($"LEAK    {s.name} at ({x:F1}, {-z:F1}) spec x,z looking {(d == Vector3.up ? "up" : $"toward spec ({d.x:F2}, {-d.z:F2})")}"); break; }
                        if (y0 != gy || s.kind == "opening" || ground == null) continue;
                        if (Physics.Raycast(new Vector3(x, y0 + 0.05f, z), Vector3.up, out var hit, 2.0f))
                        {
                            var n = hit.collider.name;
                            if (n.StartsWith("flight1_") || n.StartsWith("Floor")) continue;
                            low++; if (low <= 12) lines.Add($"LOW     {s.name} at ({x:F1}, {-z:F1}): {hit.distance:F2} m clear under {hit.collider.transform.parent?.name}/{n}");
                        }
                    }
            }
        lines.Insert(0, $"Leak and headroom check: {pts} points, {leaks} leaks, {low} low-headroom points (ground floor, outside flight 1)");
        return string.Join("\n", lines) + "\n";
    }

    // Furniture sizes for tools/house/furniture_check.py (skill room-feel step 2): every renderer whose name names a
    // furniture piece, its world-space size in scene units, and the scene's metres per unit (IntactHouseReference is the
    // downloaded model at native scale: 0.774 m/unit from its 80 in doors; every other scene is metres).
    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.DumpFurniture -quit -logFile - -scene IntactHouseReference
    public static void DumpFurniture()
    {
        var a = System.Environment.GetCommandLineArgs(); int i = System.Array.IndexOf(a, "-scene");
        string scene = i >= 0 ? a[i + 1] : "IntactHouseReference";
        EditorSceneManager.OpenScene($"Assets/Scenes/{scene}.unity");
        float mpu = scene == "IntactHouseReference" ? 2.032f / 2.625f : 1f;
        var keys = new[] { "mattress", "chest", "dresser", "bedside", "nightstand", "desk", "dining table", "sofa", "couch", "door leaf" };
        var rows = new List<string>();
        foreach (var r in Object.FindObjectsByType<Renderer>())
        {
            var n = r.name.ToLowerInvariant();
            if (!keys.Any(k => n.Contains(k)) || n.Contains("drawer") || n.Contains("top")) continue;
            var path = r.transform.parent ? r.transform.parent.name + "/" + r.name : r.name;
            var sz = r.bounds.size;
            rows.Add($"{{\"path\":\"{path}\",\"name\":\"{r.name}\",\"size\":[{sz.x:F3},{sz.y:F3},{sz.z:F3}]}}");
        }
        File.WriteAllText(Path.Combine(CaptureDir, $"furniture-{scene}.json"),
            $"{{\"scene\":\"{scene}\",\"m_per_unit\":{mpu:F4},\"pieces\":[\n" + string.Join(",\n", rows) + "\n]}\n");
    }

    // Lens/eye-height comparison (open item: "the hall feels narrow"): the opening hall view rendered from Marina's own
    // solved camera (hall-s1 frame 135: eye ~1.03 m, vertical FOV ~40 deg), then from the same spot at our adult player's
    // eye (1.65 m, FOV 60) and Kevin's (1.05 m, FOV 60). tools/house/lens_compare.py lays them beside Marina's frame.
    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderLens -quit -logFile -
    public static void RenderLens()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/Greybox_Upstairs.unity");
        var p = JObject.Parse(File.ReadAllText(Path.Combine(CaptureDir, "matched/hall-s1/poses.json")))["poses"][0];
        Vector3 V(JToken t) => new Vector3((float)t[0], (float)t[1], (float)t[2]);
        var pos = V(p["pos"]); var fwd = V(p["forward"]); var up = V(p["up"]);
        var level = new Vector3(fwd.x, 0, fwd.z).normalized;
        var go = new GameObject("LensCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        Directory.CreateDirectory(Path.Combine(CaptureDir, "lens"));
        foreach (var (name, y, fov, look, upv) in new[] {
            ("marina-camera", pos.y, (float)p["vfov"], fwd, up),
            ("player-adult", 1.65f, 60f, level, Vector3.up),
            ("player-kevin", 1.05f, 60f, level, Vector3.up) })
        {
            go.transform.SetPositionAndRotation(new Vector3(pos.x, y, pos.z), Quaternion.LookRotation(look, upv));
            cam.fieldOfView = fov;
            Shot(cam, rt, Path.Combine("lens", name));
        }
        RenderTexture.active = null; Object.DestroyImmediate(go); rt.Release();
    }

    // Named one-off views (spec/captures/views/views.json: [{name, pos, look_at, vfov}], Unity world coordinates).
    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderViews -quit -logFile -
    public static void RenderViews()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/Greybox_Upstairs.unity");
        var go = new GameObject("ViewCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        foreach (var v in JArray.Parse(File.ReadAllText(Path.Combine(CaptureDir, "views/views.json"))))
        {
            Vector3 V(JToken t) => new Vector3((float)t[0], (float)t[1], (float)t[2]);
            // optional "hide": object paths to switch off for this view (e.g. "Upstairs", "Ground/Ceilings")
            var hidden = (v["hide"] ?? new JArray()).Select(h => GameObject.Find((string)h)).Where(o => o).ToList();
            hidden.ForEach(o => o.SetActive(false));
            go.transform.position = V(v["pos"]); go.transform.LookAt(V(v["look_at"])); cam.fieldOfView = (float)v["vfov"];
            Shot(cam, rt, Path.Combine("views", (string)v["name"]));
            hidden.ForEach(o => o.SetActive(true));
        }
        RenderTexture.active = null; Object.DestroyImmediate(go); rt.Release();
    }

    static void Player(Space hall)
    {
        // spawn on the hall's widest floor cell (its vertex average can sit over the stairwell; the gallery is long but narrow)
        var c = Cells(hall.pts).OrderByDescending(q => Mathf.Min(q.Item2 - q.Item1, q.Item4 - q.Item3)).First();
        var (x, z) = ((c.Item1 + c.Item2) / 2, (c.Item3 + c.Item4) / 2);
        var p = new GameObject("Player"); p.transform.position = new Vector3(x, 0.05f, z);
        var cc = p.AddComponent<CharacterController>(); cc.radius = 0.275f; cc.height = 1.85f; cc.center = new Vector3(0, 0.925f, 0); cc.stepOffset = 0.3f;
        var camGo = new GameObject("Camera"); camGo.transform.parent = p.transform; camGo.transform.localPosition = new Vector3(0, 1.7f, 0);
        var cam = camGo.AddComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = 0.05f; camGo.AddComponent<HDAdditionalCameraData>(); camGo.AddComponent<AudioListener>();
        var fc = p.AddComponent<FpsController>(); fc.cam = camGo.transform;
        fc.eyeOffset = fc.standHeight - 1.28f;   // eye 1.28 m = IntactHouseReference's (1.65 units x 0.774), so feel walks compare like with like; adult is 1.65
    }

    // Adult capsule (spec bodies.bandit: diameter 0.55, height 1.85) swept straight through every real door and
    // arch, from 0.45 m inside one space to 0.45 m inside the other (shallow closets fit). Any hit is a failure with its location.
    static string WalkTest(List<Space> spaces, List<Door> doors)
    {
        const float r = 0.275f, h = 1.85f;
        var lines = new List<string>(); int bad = 0, n = 0;
        foreach (var d in doors.Where(d => d.kind == "door" || d.kind == "arch"))
        {
            float c = (d.lo + d.hi) / 2;
            Vector3 P(float off) => d.alongX ? new Vector3(c, 0.06f + FloorY, d.coord + off) : new Vector3(d.coord + off, 0.06f + FloorY, c);
            Vector3 a = P(-0.45f), b = P(0.45f), dir = (b - a).normalized; float len = Vector3.Distance(a, b);
            Vector3 p1 = a + Vector3.up * r, p2 = a + Vector3.up * (h - r);
            n++;
            if (Physics.CapsuleCast(p1, p2, r, dir, out var hit, len))
            { bad++; lines.Add($"BLOCKED {d.a} <-> {d.b} ({d.kind}, {d.hi - d.lo:F2} m) by {hit.collider.transform.parent?.name}/{hit.collider.name} at {hit.distance:F2} m"); }
            else lines.Add($"ok      {d.a} <-> {d.b} ({d.kind}, {d.hi - d.lo:F2} m)");
        }
        lines.Insert(0, $"Adult capsule walk test: {n} openings, {bad} blocked");
        return string.Join("\n", lines) + "\n";
    }

    static void Captures(List<Space> spaces, GameObject ceilings)
    {
        var go = new GameObject("ShotCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1600, 1600, 24); cam.targetTexture = rt;
        var all = spaces.SelectMany(s => s.pts).ToList();
        float cx = (all.Min(p => p.x) + all.Max(p => p.x)) / 2, cz = (all.Min(p => p.y) + all.Max(p => p.y)) / 2;
        float span = Mathf.Max(all.Max(p => p.x) - all.Min(p => p.x), all.Max(p => p.y) - all.Min(p => p.y));

        // 1. plan view, ceilings hidden: z grows downward in the image like the overhead it was traced from
        ceilings.SetActive(false);
        cam.orthographic = true; cam.orthographicSize = span / 2 + 0.6f;
        go.transform.position = new Vector3(cx, 20f, cz); go.transform.rotation = Quaternion.LookRotation(Vector3.down, Vector3.forward);
        Shot(cam, rt, "plan-topdown");
        // 2. oblique bird's-eye, like Marina's overhead
        cam.orthographic = false; cam.fieldOfView = 40f;
        go.transform.position = new Vector3(cx, span * 1.5f, cz - span * 0.55f); go.transform.LookAt(new Vector3(cx, 0, cz), Vector3.forward);
        Shot(cam, rt, "oblique");
        ceilings.SetActive(true);

        // 3. eye level, Marina's opening hall view: north end of the corridor looking down it to the attic door
        var hall = spaces.First(s => s.name == "hall_corridor");
        var leg = spaces.First(s => s.name == "hall_corridor_south");
        cam.fieldOfView = 60f; rt.Release(); rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        float lx = (leg.pts.Min(p => p.x) + leg.pts.Max(p => p.x)) / 2;   // north end = max z (world z = -spec z)
        go.transform.position = new Vector3(lx, 1.6f, hall.pts.Max(p => p.y) - 0.4f);
        go.transform.LookAt(new Vector3(lx, 1.3f, leg.pts.Min(p => p.y)));
        Shot(cam, rt, "eye-hall-to-attic-door");
        RenderTexture.active = null; Object.DestroyImmediate(go); rt.Release();
    }

    // Renders the grey-box from Marina's solved cameras (spec/captures/matched/poses.json, written by
    // tools/house/match_cameras.py poses ...), for the edge comparison in match_cameras.py compare.
    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderMatched -quit -logFile -
    public static void RenderMatched()
    {
        string root = Path.Combine(CaptureDir, "matched");
        EditorSceneManager.OpenScene($"Assets/Scenes/Greybox_Upstairs{SceneTag}.unity");
        // Comparison render = surface-ID image: every box (wall run, header, casing, floor cell, ceiling) gets its own
        // flat unlit colour and all lights are off, so a colour change is exactly a geometric edge (with occlusion),
        // from any viewpoint and independent of lighting or exposure.
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None)) l.gameObject.SetActive(false);
        var unlit = Shader.Find("HDRP/Unlit");
        int k = 0;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.InstanceID))
        {
            var m = new Material(unlit);
            var c = Color.HSVToRGB((k * 0.618034f) % 1f, 0.55f + 0.45f * (k % 2), 0.45f + 0.5f * ((k / 2) % 2)); k++;
            m.SetColor("_UnlitColor", c); r.sharedMaterial = m;
        }
        foreach (var v in Object.FindObjectsByType<Volume>(FindObjectsSortMode.None))
            if (v.sharedProfile.TryGet<Exposure>(out var ex)) { ex.mode.value = ExposureMode.Fixed; ex.fixedExposure.value = 0f; }
        var go = new GameObject("MatchCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        foreach (var clipDir in Directory.GetDirectories(root).Where(d => File.Exists(Path.Combine(d, "poses.json"))))
        {
            var j = JObject.Parse(File.ReadAllText(Path.Combine(clipDir, "poses.json")));
            foreach (var p in j["poses"])
            {
                Vector3 V(JToken t) => new Vector3((float)t[0], (float)t[1], (float)t[2]);
                go.transform.SetPositionAndRotation(V(p["pos"]), Quaternion.LookRotation(V(p["forward"]), V(p["up"])));
                cam.fieldOfView = (float)p["vfov"];
                Directory.CreateDirectory(Path.Combine(clipDir, Variant == "" ? "." : Variant));
                Shot(cam, rt, Path.Combine("matched", Path.GetFileName(clipDir), Variant == "" ? "" : Variant, (string)p["name"]));
            }
        }
        RenderTexture.active = null; Object.DestroyImmediate(go); rt.Release();
        Debug.Log("SpecGreybox: matched renders written under " + root);
    }

    static void Shot(Camera cam, RenderTexture rt, string name)
    {
        cam.Render(); RenderTexture.active = rt;
        var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        tex.ReadPixels(new UnityEngine.Rect(0, 0, rt.width, rt.height), 0, 0); tex.Apply();
        File.WriteAllBytes(Path.Combine(CaptureDir, name + ".png"), tex.EncodeToPNG()); Object.DestroyImmediate(tex);
    }
}
