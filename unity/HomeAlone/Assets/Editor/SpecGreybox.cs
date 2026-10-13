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

    static string SpecPath => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.json"));
    static string CaptureDir => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures"));

    class Door { public string a, b, kind; public bool alongX; public float coord, lo, hi, height; }
    class Space { public string name, kind; public float ceil; public List<Vector2> pts; }

    [MenuItem("HomeAlone/Build Greybox From Spec")]
    public static void Build()
    {
        var j = JObject.Parse(File.ReadAllText(SpecPath));
        var spaces = j["spaces"].Select(s => new Space {
            name = (string)s["name"], kind = (string)s["kind"], ceil = (float)s["ceiling_m"],
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

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        MakeMaterials();
        var root = new GameObject("Upstairs");
        var ceilings = Child(root, "Ceilings");
        foreach (var s in spaces)
        {
            var g = Child(root, s.name);
            if (s.kind != "opening")
            {
                foreach (var (x0, x1, z0, z1) in Cells(s.pts))
                {
                    Box(g, "Floor", x0, x1, z0, z1, -0.2f, 0f, s.kind == "hall" ? mHall : mFloor);
                    Box(ceilings, s.name + "_Ceiling", x0, x1, z0, z1, s.ceil, s.ceil + 0.15f, mCeil);
                }
                Walls(g, s, doors);
            }
            else
            {
                // stairwells: enclosed on the sides no room covers; rails where the spec says rail
                foreach (var d in doors.Where(d => d.kind == "rail" && (d.a == s.name || d.b == s.name)))
                    Rail(g, d);
            }
        }
        Lighting(root, spaces);
        Player(spaces.First(s => s.name == "hall_corridor"));

        Physics.SyncTransforms();
        string report = WalkTest(spaces, doors);
        Directory.CreateDirectory(CaptureDir);
        File.WriteAllText(Path.Combine(CaptureDir, "walk-test.txt"), report);
        Captures(spaces, ceilings);
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), "Assets/Scenes/Greybox_Upstairs.unity");
        Debug.Log("SpecGreybox: built from " + SpecPath + "\n" + report);
    }

    // Rectilinear polygon -> covering rectangles (grid of its own coordinates, keep cells whose centre is inside).
    static IEnumerable<(float, float, float, float)> Cells(List<Vector2> pts)
    {
        var xs = pts.Select(p => p.x).Distinct().OrderBy(v => v).ToList();
        var zs = pts.Select(p => p.y).Distinct().OrderBy(v => v).ToList();
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
        b.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
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

    static void Lighting(GameObject root, List<Space> spaces)
    {
        var lights = Child(root, "Lights");
        foreach (var s in spaces.Where(s => s.kind != "opening"))
        {
            var (x, z) = (s.pts.Average(p => p.x), s.pts.Average(p => p.y));
            var l = new GameObject("Light_" + s.name).AddComponent<Light>(); l.transform.parent = lights.transform;
            l.transform.position = new Vector3(x, s.ceil - 0.3f, z); l.type = LightType.Point; l.range = 8f;
            l.intensity = 900f; l.color = new Color(1f, 0.95f, 0.88f); l.gameObject.AddComponent<HDAdditionalLightData>();
        }
        Directory.CreateDirectory("Assets/Settings");
        string vp = "Assets/Settings/GreyboxVolume.asset";
        AssetDatabase.DeleteAsset(vp);
        var profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, vp);
        var env = profile.Add<VisualEnvironment>(true); env.skyType.value = (int)SkyType.PhysicallyBased; AssetDatabase.AddObjectToAsset(env, profile);
        var sky = profile.Add<PhysicallyBasedSky>(true); AssetDatabase.AddObjectToAsset(sky, profile);
        var exp = profile.Add<Exposure>(true); exp.mode.value = ExposureMode.Automatic; exp.limitMin.value = 4f; exp.limitMax.value = 12f; AssetDatabase.AddObjectToAsset(exp, profile);
        var vol = new GameObject("GlobalVolume").AddComponent<Volume>(); vol.transform.parent = root.transform; vol.isGlobal = true; vol.sharedProfile = profile;
    }

    static void Player(Space hall)
    {
        var (x, z) = (hall.pts.Average(p => p.x), hall.pts.Average(p => p.y));
        var p = new GameObject("Player"); p.transform.position = new Vector3(x, 0.05f, z);
        var cc = p.AddComponent<CharacterController>(); cc.radius = 0.275f; cc.height = 1.85f; cc.center = new Vector3(0, 0.925f, 0); cc.stepOffset = 0.3f;
        var camGo = new GameObject("Camera"); camGo.transform.parent = p.transform; camGo.transform.localPosition = new Vector3(0, 1.7f, 0);
        var cam = camGo.AddComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = 0.05f; camGo.AddComponent<HDAdditionalCameraData>(); camGo.AddComponent<AudioListener>();
        p.AddComponent<FpsController>().cam = camGo.transform;
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
            Vector3 P(float off) => d.alongX ? new Vector3(c, 0.06f, d.coord + off) : new Vector3(d.coord + off, 0.06f, c);
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
        EditorSceneManager.OpenScene("Assets/Scenes/Greybox_Upstairs.unity");
        // Comparison lighting: room point lights off (their ceiling hotspots read as false edges); one shadowless
        // directional light from the camera, so each plane gets a flat shade and only geometry makes edges.
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None)) l.gameObject.SetActive(false);
        var head = new GameObject("Headlight").AddComponent<Light>(); head.type = LightType.Directional; head.intensity = 8000f;
        head.shadows = LightShadows.None; head.gameObject.AddComponent<HDAdditionalLightData>();
        var go = new GameObject("MatchCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        foreach (var clipDir in Directory.GetDirectories(root).Where(d => File.Exists(Path.Combine(d, "poses.json"))))
        {
            var j = JObject.Parse(File.ReadAllText(Path.Combine(clipDir, "poses.json")));
            foreach (var p in j["poses"])
            {
                Vector3 V(JToken t) => new Vector3((float)t[0], (float)t[1], (float)t[2]);
                go.transform.SetPositionAndRotation(V(p["pos"]), Quaternion.LookRotation(V(p["forward"]), V(p["up"])));
                head.transform.rotation = Quaternion.LookRotation(V(p["forward"]) + new Vector3(0.25f, -0.35f, 0.15f), Vector3.up);
                cam.fieldOfView = (float)p["vfov"];
                Shot(cam, rt, Path.Combine("matched", Path.GetFileName(clipDir), (string)p["name"]));
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
