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
    const float StoolProud = 0.04f, StoolT = 0.025f;      // window stool: 1 1/2 in into the room past the casing, 1 in thick
    static Material mFloor, mWall, mCeil, mHall, mProp, mRail, mGlass;

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
    class Win { public string room; public bool alongX; public float coord, lo, hi, sill, head; }
    static List<Win> Windows = new List<Win>();
    class Space { public string name, kind, opens; public float ceil; public List<Vector2> pts; }

    static string GroundPath
    {   // a variant's own ground floor when it has one (stair variants move the ground floor), else the main one
        get { var v = Path.GetFullPath(Path.Combine(Application.dataPath, $"../../../spec/house_spec.ground{Tag}.json"));
              return File.Exists(v) ? v : Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.ground.json")); }
    }
    // a little over the 0.178 m rise: at 0.3 the controller's step-up probe lifted an adult head into the slab edge over
    // flight 1's lower steps (vertical headroom there 2.26 m, Oct 15)
    const float StepOffset = 0.2f;
    // the Player's skin: Unity's default 0.08 padded a 1.8 m body to ~2.0 m and wedged it under the upper floor's edge over
    // flight 1 (2.08 m clear above the nosing line there); Unity's guidance is ~10% of the radius (Oct 15)
    const float PlayerSkin = 0.03f;
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
        // windows: wall_axis "x" = the wall x = coord (runs along z), "z" = the wall z = coord; spec z -> world -z
        Windows = (j["windows"] ?? new JArray()).Select(w => {
            bool alongX = (string)w["wall_axis"] == "z";
            float c = (float)w["wall_coord_spec"], l = (float)w["span_spec"][0], h = (float)w["span_spec"][1];
            return new Win { room = (string)w["room"], alongX = alongX, coord = alongX ? -c : c, lo = alongX ? l : -h, hi = alongX ? h : -l,
                             sill = (float)w["sill_m"], head = (float)w["head_m"] };
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
                    Box(g, "Floor", x0, x1, z0, z1, -0.2f, 0f, Dress != null && FloorY != 0f && Dress["walls"]["spaces"].Any(n => (string)n == s.name)
                        ? DressMat(Dress["walls"]["floor"]) : s.kind == "hall" && FloorY == 0f ? mHall : mFloor);   // ground halls: wood (Marina's foyer)
                // hole edges within 6 cm of a wall line on this floor snap onto it: the stairwell's edges ARE the foyer's walls, traced
                // 0.2-5 cm apart on the two floors (seam check: a ceiling strip along the stair wall)
                float Snap(float v, IEnumerable<float> own) { var o = own.OrderBy(w => Mathf.Abs(w - v)).First(); return Mathf.Abs(o - v) < 0.06f ? o : v; }
                var hx = holes.SelectMany(h => h.pts.Select(p => Snap(p.x, spaces.SelectMany(o => o.pts).Select(q => q.x)))).ToList();
                var hz = holes.SelectMany(h => h.pts.Select(p => Snap(p.y, spaces.SelectMany(o => o.pts).Select(q => q.y)))).ToList();
                foreach (var (x0, x1, z0, z1) in Cells(s.pts, hx, hz))
                    if (x1 - x0 > 0.02f && z1 - z0 > 0.02f && !holes.Any(h => Inside(h.pts, new Vector2((x0 + x1) / 2, (z0 + z1) / 2))))   // no slivers from mm trace offsets
                    {   // stops under the upper floor's slab, and under a landing's underside when it reaches one (seam check)
                        float top = FloorY != 0f ? Mathf.Min(s.ceil + 0.15f, -0.2f - FloorY) : s.ceil + 0.15f;
                        foreach (var L in Landings)
                            if (x1 > L.x0 - 0.1f && x0 < L.x1 + 0.1f && z1 > L.z0 - 0.1f && z0 < L.z1 + 0.1f && FloorY + top > L.y)
                                top = Mathf.Max(s.ceil + 0.005f, L.y - FloorY);
                        Box(ceilings, s.name + "_Ceiling", x0, x1, z0, z1, s.ceil, top, mCeil);
                    }
                Walls(g, s, doors);
                // a balustrade between two rooms (the service stair's open side, Oct 15): built once, by the first-named space
                foreach (var d in doors.Where(d => d.kind == "rail" && d.a == s.name && spaces.Any(o => o.name == d.b && o.kind != "opening")))
                    Rail(g, d);
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

    // Opens the grey-box ready to walk (Play, click the Game view). Launch: Unity -projectPath unity/HomeAlone -executeMethod SpecGreybox.OpenForWalk
    [MenuItem("HomeAlone/Open Greybox For Walk")]
    public static void OpenForWalk() => EditorSceneManager.OpenScene("Assets/Scenes/Greybox_Upstairs.unity");

    [MenuItem("HomeAlone/Build Greybox From Spec")]
    public static void Build()
    {
        var j = JObject.Parse(File.ReadAllText(SpecPath));
        var (spaces, doors) = Parse(j);
        var gj = File.Exists(GroundPath) ? JObject.Parse(File.ReadAllText(GroundPath)) : null;
        var dp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/foyer.json"));
        Dress = File.Exists(dp) ? JObject.Parse(File.ReadAllText(dp)) : null;

        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        MakeMaterials(); HoleProbes.Clear();
        FloorY = 0f;
        var root = new GameObject("Upstairs");
        var ceilings = Child(root, "Ceilings");
        BuildFloor(root, ceilings, spaces, doors);
        var stairPath = Stair(root, j["stair"], skipFloorPatch: gj != null);
        var atticPath = Stair(root, j["attic_stair"], false, "AtticStair", dress: false);   // seen through the open attic door (DEVIATIONS 21)
        string report = "";
        List<Space> gspaces = null; List<Door> gdoors = null; GameObject groot = null, gceil = null;
        if (gj != null)
        {
            (gspaces, gdoors) = Parse(gj);
            FloorY = (float)gj["floor_y_m"];
            Landings = j["stair"]["boxes"].Where(b => (string)b["kind"] == "landing").Select(b => ((float)b["x"][0], (float)b["x"][1],
                -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0])).ToList();
            groot = new GameObject("Ground"); gceil = Child(groot, "Ceilings");
            BuildFloor(groot, gceil, gspaces, gdoors, spaces.Where(s => s.opens == "down").ToList());
            if (gj["stair"] != null && gj["stair"].Type != JTokenType.Null) Stair(groot, gj["stair"], false);   // the service stair (ground-floor y)
            Dressing(groot, FloorY);   // before the gates: the walk tests see its colliders
            FloorY = 0f;
        }
        Volume(root);
        Daylight(root, gj != null ? (float)gj["floor_y_m"] : 0f);
        Player(spaces.First(s => s.name == "hall_corridor"));

        var player = GameObject.Find("Player"); player.SetActive(false);   // the test bodies walk alone
        Physics.SyncTransforms();
        report += "UPSTAIRS\n" + WalkTest(spaces, doors);
        if (gj != null) { FloorY = (float)gj["floor_y_m"]; report += "GROUND\n" + WalkTest(gspaces, gdoors); FloorY = 0f; }
        report += StairWalk(stairPath);
        report += StairWalk(atticPath);
        // structure checks: headroom and room reachability are about the building, so the dressing's furniture is off for them
        var dressing = GameObject.Find("Ground/Dressing"); dressing?.SetActive(false); Physics.SyncTransforms();
        float gfy = gj != null ? (float)gj["floor_y_m"] : 0f;
        SeamRooms = spaces.Select(s => (s.pts, s.opens == "down" ? gfy : 0f, s.ceil)).ToList();
        if (gspaces != null) SeamRooms.AddRange(gspaces.Select(s => (s.pts, gfy, gfy + s.ceil)));
        // closed rooms (no way in: back_hall behind its prop door) are never seen
        var walkIn = doors.Concat(gdoors ?? new List<Door>()).Where(d => d.kind != "fake_door").SelectMany(d => new[] { d.a, d.b }).ToHashSet();
        var all = spaces.Concat(gspaces ?? new List<Space>()).ToList();
        SeamRooms = SeamRooms.Where((r, i) => walkIn.Contains(all[i].name) || all[i].kind == "opening").ToList();
        report += SeamCheck(root, groot);
        report += LeakAndHeadroom(spaces, gspaces, gj != null ? (float)gj["floor_y_m"] : 0f);
        report += "UPSTAIRS " + RoomWalk(spaces, doors);
        if (gj != null) { FloorY = (float)gj["floor_y_m"]; report += "GROUND " + RoomWalk(gspaces, gdoors); FloorY = 0f; }
        dressing?.SetActive(true); Physics.SyncTransforms();
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

    // ---- Wall-grid PILOT (tasks/wall-grid-plan.md phase 3): the upstairs built from spec/geometry.json (tools/house/wall_graph.py
    // --json): walls are the storey's one union, already cut for openings, so nothing here decides geometry. Saved as its own
    // scene (Pilot_WallGrid); the working scene is untouched. Same gates as Build: walk, room walk, seams, leaks.
    [MenuItem("HomeAlone/Build Wall-Grid Pilot")]
    public static void BuildPilot()
    {
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        var up = (JObject)geo["upstairs"];
        // the rooms and openings in the spec's own shape, so the existing gates read them
        var specLike = new JObject {
            ["spaces"] = new JArray(up["rooms"].Select(r => new JObject { ["name"] = r["name"], ["kind"] = r["kind"], ["opens"] = r["opens"],
                                                                          ["ceiling_m"] = r["ceil"], ["polygon_xz"] = r["poly"] })),
            ["doors"] = new JArray(up["openings"].Where(o => (string)o["kind"] != "window").Select(o => new JObject {
                ["between"] = o["between"], ["kind"] = o["kind"], ["spec_axis"] = o["axis"], ["wall_coord_spec"] = o["c"],
                ["span_spec"] = new JArray(o["lo"], o["hi"]), ["height"] = o["height"] })) };
        var (spaces, doors) = Parse(specLike);
        Windows = new List<Win>();
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        MakeMaterials(); HoleProbes.Clear(); FloorY = 0f; Dress = null; WallMat = null;
        var root = new GameObject("Upstairs"); var gw = Child(root, "Walls"); var gf = Child(root, "Floor"); var gc = Child(root, "Ceilings");
        var go = Child(root, "Openings");
        Box3(gw, "Wall", up["walls"], mWall);
        Box3(gf, "FloorPlate", up["floor"], mFloor);
        Box3(gc, "Ceiling", up["ceilings"], mCeil);
        foreach (var c in up["ceilings"])   // each room's floor finish: carpet in the halls, wood elsewhere (3 mm on the plate)
        {
            var room = spaces.First(r => r.name == (string)c["room"]);
            Box(gf, "Finish_" + room.name, (float)c["x"][0], (float)c["x"][1], -(float)c["z"][1], -(float)c["z"][0], 0f, 0.003f, room.kind == "hall" ? mHall : mFloor);
        }
        foreach (var o in up["openings"])
        {
            string kind = (string)o["kind"]; bool alongX = (string)o["axis"] == "z";
            float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"];
            float wc = alongX ? -c : c, s0 = alongX ? lo : -hi, s1 = alongX ? hi : -lo;    // world: wall centre, span
            const float h = 0.07f;
            if (kind == "door")
            {   // casing on both faces, proud away from the wall
                float head = (float)o["height"];
                foreach (float side in new[] { -1f, 1f })
                {
                    float f0 = wc + side * h, f1 = f0 + side * CasingProud;
                    Trim(go, alongX, f0, f1, s0 - CasingW, s0, 0f, head + CasingW);
                    Trim(go, alongX, f0, f1, s1, s1 + CasingW, 0f, head + CasingW);
                    Trim(go, alongX, f0, f1, s0 - CasingW, s1 + CasingW, head, head + CasingW);
                }
            }
            else if (kind == "fake_door")
                foreach (float side in new[] { -1f, 1f })
                {
                    float f0 = wc + side * h, f1 = f0 + side * 0.03f;
                    if (alongX) Box(go, "PropDoor", s0, s1, Mathf.Min(f0, f1), Mathf.Max(f0, f1), 0f, 2.032f, mProp);
                    else Box(go, "PropDoor", Mathf.Min(f0, f1), Mathf.Max(f0, f1), s0, s1, 0f, 2.032f, mProp);
                }
            else if (kind == "window")
            {
                float sill = (float)o["sill"], whead = (float)o["head"], ta = wc - 0.006f, tb = wc + 0.006f;
                if (alongX) Box(go, "Glass", s0, s1, ta, tb, sill, whead, mGlass); else Box(go, "Glass", ta, tb, s0, s1, sill, whead, mGlass);
                float ow = (float)o["faces"][0] * (alongX ? -1f : 1f);           // spec outward -> world (z flips)
                float f0 = wc - ow * h, f1 = f0 - ow * CasingProud;              // the room's face, trim proud into the room
                Trim(go, alongX, f0, f1, s0 - CasingW, s0, sill, whead + CasingW);
                Trim(go, alongX, f0, f1, s1, s1 + CasingW, sill, whead + CasingW);
                Trim(go, alongX, f0, f1, s0 - CasingW, s1 + CasingW, whead, whead + CasingW);
                Trim(go, alongX, f0, f0 - ow * StoolProud, s0 - CasingW - 0.025f, s1 + CasingW + 0.025f, sill - StoolT, sill);
            }
        }
        foreach (var d in doors.Where(d => d.kind == "rail")) Rail(go, d);
        Lights(root, spaces);
        Volume(root);
        Daylight(root, -3.026f);
        Player(spaces.First(s => s.name == "hall_corridor"));
        var player = GameObject.Find("Player"); player.SetActive(false);
        Physics.SyncTransforms();
        string report = "PILOT (upstairs from spec/geometry.json)\n" + WalkTest(spaces, doors);
        var walkIn = doors.Where(d => d.kind != "fake_door").SelectMany(d => new[] { d.a, d.b }).ToHashSet();
        SeamRooms = spaces.Where(sp => walkIn.Contains(sp.name)).Select(sp => (sp.pts, 0f, sp.ceil)).ToList();
        report += SeamCheck(root);
        report += LeakAndHeadroom(spaces.Where(sp => sp.opens != "down").ToList(), null, 0f);
        // the stairwell has no stair in the pilot (upstairs only): walks into it are not part of the pilot
        var well = spaces.Where(sp => sp.opens == "down").Select(sp => sp.name).ToHashSet();
        report += "UPSTAIRS " + RoomWalk(spaces.Where(sp => !well.Contains(sp.name)).ToList(), doors.Where(d => !well.Contains(d.a) && !well.Contains(d.b)).ToList());
        player.SetActive(true);
        Directory.CreateDirectory(CaptureDir);
        File.WriteAllText(Path.Combine(CaptureDir, "walk-test-pilot.txt"), report);
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), "Assets/Scenes/Pilot_WallGrid.unity");
        Debug.Log("SpecGreybox.BuildPilot\n" + report);
    }

    static void Box3(GameObject p, string n, JToken boxes, Material m)
    {   // geometry boxes in spec coordinates (x, z, y) -> world (z flips)
        foreach (var b in boxes)
            Box(p, n, (float)b["x"][0], (float)b["x"][1], -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0], (float)b["y"][1], m);
    }

    // spec/dressing/foyer.json (tools/house/foyer_dressing.py): finishes and pieces measured from Marina's frames. Finishes
    // (wainscot, wallpaper, stair colours) are applied while building; pieces are added after the gates, like furniture.
    static JObject Dress;
    static Material DressMat(JToken c)
    {
        var col = new Color((float)c[0], (float)c[1], (float)c[2]);
        return Mat($"Dress_{ColorUtility.ToHtmlStringRGB(col)}", col);
    }
    static Material WallMat = null, WainscotMat = null; static float Wainscot = 0f;
    static void SetFinish(Space s)
    {   // wall material for this space's walls: the dressing's wallpaper over a wainscot, else the plain grey-box wall
        var w = Dress?["walls"];
        bool on = w != null && FloorY != 0f && w["spaces"].Any(n => (string)n == s.name);
        WallMat = on ? (w["wallpaper_texture"] != null ? Wallpaper(w) : DressMat(w["wallpaper"])) : null; WainscotMat = on ? DressMat(w["wainscot"]) : null;
        Wainscot = on ? (float)w["wainscot_m"] : 0f;
    }

    // Marina's damask, one repeat cut from her frame (foyer_dressing.py), mapped in world units (triplanar) so wall boxes of any
    // size show it at its measured repeat
    static Material Wallpaper(JToken w)
    {
        string src = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../" + (string)w["wallpaper_texture"]));
        Directory.CreateDirectory("Assets/Textures/Greybox"); string dst = "Assets/Textures/Greybox/wallpaper.png";
        File.Copy(src, dst, true); AssetDatabase.ImportAsset(dst);
        var m = Mat("Dress_Wallpaper", Color.white);
        m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dst));
        float rep = ((float)w["wallpaper_repeat_m"][0] + (float)w["wallpaper_repeat_m"][1]) / 2f;
        m.SetFloat("_UVBase", 5f); m.SetFloat("_TexWorldScale", 1f / rep);   // 5 = triplanar
        HDMaterial.ValidateMaterial(m);
        return m;
    }

    static void Dressing(GameObject root, float floorY)
    {
        if (Dress == null) return;
        var g = Child(root, "Dressing"); float keep = FloorY; FloorY = floorY;
        foreach (var p in Dress["pieces"])
        {
            var m = DressMat(p["colour"]); string n = (string)p["name"]; int before = g.transform.childCount;
            if (p["x"] != null)
                Box(g, n, (float)p["x"][0], (float)p["x"][1], -(float)p["z"][1], -(float)p["z"][0], (float)p["y"][0], (float)p["y"][1], m);
            else
            {   // a box along a -> b (sloped stringers, handrail, soffit)
                var a = new Vector3((float)p["a"][0], (float)p["a"][1] + FloorY, -(float)p["a"][2]);
                var b = new Vector3((float)p["b"][0], (float)p["b"][1] + FloorY, -(float)p["b"][2]);
                var c = GameObject.CreatePrimitive(PrimitiveType.Cube); c.name = n; c.transform.parent = g.transform;
                c.transform.position = (a + b) / 2; c.transform.rotation = Quaternion.LookRotation(b - a, Vector3.up);
                c.transform.localScale = new Vector3((float)p["w"], (float)p["t"], (b - a).magnitude);
                c.GetComponent<MeshRenderer>().sharedMaterial = m; c.isStatic = true;
            }
            if (!(bool)p["collide"] && g.transform.childCount > before)
                Object.DestroyImmediate(g.transform.GetChild(g.transform.childCount - 1).GetComponent<Collider>());
        }
        FloorY = keep;
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
    // Stair landings (world x0, x1, z0, z1, underside y): a room wall standing under one stops at its underside, like the
    // enclosure under Marina's landing (Oct 15); otherwise the room's ceiling would push it up through the landing.
    static List<(float x0, float x1, float z0, float z1, float y)> Landings = new();

    static float WallTop(float ceil, bool alongX, float coord, float lo, float hi)
    {
        foreach (var L in Landings)
        {
            // inclusive: a face flush with the landing's front or rear edge stops under it too (the stairwell's own wall
            // carries the rear wall above)
            bool inside = alongX ? coord >= L.z0 - 0.01f && coord <= L.z1 + 0.01f && lo >= L.x0 - 0.1f && hi <= L.x1 + 0.1f
                                 : coord >= L.x0 - 0.01f && coord <= L.x1 + 0.01f && lo >= L.z0 - 0.1f && hi <= L.z1 + 0.1f;   // span: 10 cm past the landing still counts (the foyer wall runs 5 cm past the well edge)
            if (inside && FloorY + ceil > L.y) ceil = Mathf.Min(ceil, L.y - FloorY);
        }
        return ceil;
    }

    static List<(Vector3 p, string what)> HoleProbes = new();

    // Each edge's slab stops at the room's corner, so at an outside corner the two slabs leave a HalfWall-square column
    // open to the outdoors (daylight leaked through it, Oct 15). A post fills the outer quadrant of each convex corner.
    static void CornerPosts(GameObject g, Space s)
    {
        foreach (var v in s.pts)
        {
            var quads = new[] { new Vector2(1, 1), new Vector2(1, -1), new Vector2(-1, 1), new Vector2(-1, -1) };
            var ins = quads.Where(q => Inside(s.pts, v + q * 0.02f)).ToList();
            if (ins.Count != 1) continue;                       // reflex corners: the two slabs already overlap
            var o = -ins[0];
            float x0 = Mathf.Min(v.x, v.x + o.x * HalfWall), x1 = Mathf.Max(v.x, v.x + o.x * HalfWall);
            float z0 = Mathf.Min(v.y, v.y + o.y * HalfWall), z1 = Mathf.Max(v.y, v.y + o.y * HalfWall);
            Box(g, "CornerPost", x0, x1, z0, z1, 0f, s.ceil, mWall);
            HoleProbes.Add((new Vector3((x0 + x1) / 2, FloorY + 1.2f, (z0 + z1) / 2), $"corner {s.name} ({v.x:F2}, {-v.y:F2})"));
        }
    }

    static void Walls(GameObject g, Space s, List<Door> doors)
    {
        SetFinish(s);
        CornerPosts(g, s);
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
            float ceil = WallTop(s.ceil, alongX, coord, lo, hi);

            var cuts = doors.Where(d => (d.a == s.name || d.b == s.name) && d.alongX == alongX
                                        && Mathf.Abs(d.coord - coord) < 0.35f && d.hi > lo && d.lo < hi)
                            .OrderBy(d => d.lo).ToList();
            float cur = lo;
            foreach (var d in cuts)
            {
                if (d.kind == "fake_door") { Prop(g, alongX, t0, t1, sgn, d); continue; }
                float dl = Mathf.Max(d.lo, lo), dh = Mathf.Min(d.hi, hi);
                if (d.kind != "rail" && s.kind != "opening")
                {   // threshold: floor under this half of the wall's thickness (daylight showed the gap, Oct 15)
                    float ta = Mathf.Min(t0, t1), tb = Mathf.Max(t0, t1);
                    if (alongX) Box(g, "Threshold", dl, dh, ta, tb, -0.2f, 0f, mFloor); else Box(g, "Threshold", ta, tb, dl, dh, -0.2f, 0f, mFloor);
                    var tp = alongX ? new Vector3((dl + dh) / 2, FloorY - 0.05f, (t0 + t1) / 2) : new Vector3((t0 + t1) / 2, FloorY - 0.05f, (dl + dh) / 2);
                    HoleProbes.Add((tp, $"threshold {s.name}/{d.a}-{d.b}"));
                }
                if (dl > cur) Seg(g, "Wall", alongX, t0, t1, cur, dl, 0f, ceil);
                float head = d.kind == "door" ? d.height : d.kind == "arch" ? ArchHead : ceil;
                if (head < ceil) Seg(g, d.kind + "_Header", alongX, t0, t1, dl, dh, head, ceil);
                if (d.kind == "door" && s.kind != "opening")   // a stairwell's face has the flight in it, not trim (attic stair, Oct 15)
                {   // casing on this room's face: two legs and a head, proud of the wall toward the room
                    float f0 = t0, f1 = t0 - sgn * CasingProud;
                    Trim(g, alongX, f0, f1, dl - CasingW, dl, 0f, head + CasingW);
                    Trim(g, alongX, f0, f1, dh, dh + CasingW, 0f, head + CasingW);
                    Trim(g, alongX, f0, f1, dl - CasingW, dh + CasingW, head, head + CasingW);
                }
                cur = Mathf.Max(cur, dh);
            }
            if (cur < hi) Seg(g, "Wall", alongX, t0, t1, cur, hi, 0f, ceil);
            foreach (var w in Windows.Where(w => w.room == s.name && w.alongX == alongX && Mathf.Abs(w.coord - coord) < 0.05f))
                Window(g, alongX, t0, t1, sgn, w, ceil);
        }
    }

    // A window replaces its stretch of wall: wall below the sill and above the head, a glass pane in the middle of the
    // wall (it has a collider, so the leak check still sees a closed house), casing on the room face and a stool.
    // The wall run is cut by removing the window's span from the full-height segment built above.
    static void Window(GameObject g, bool alongX, float t0, float t1, float sgn, Win w, float ceil)
    {
        var wg = Child(g, "Window");
        foreach (Transform seg in g.transform.Cast<Transform>().Where(c => c.name == "Wall").ToList())
        {   // split the full-height wall segment that spans the window
            var b = seg.GetComponent<Renderer>().bounds; float s0 = alongX ? b.min.x : b.min.z, s1 = alongX ? b.max.x : b.max.z;
            float tc = alongX ? b.center.z : b.center.x;
            if (Mathf.Abs(tc - (t0 + t1) / 2) > 1e-3f || s0 > w.lo + 1e-4f || s1 < w.hi - 1e-4f) continue;
            Object.DestroyImmediate(seg.gameObject);
            Seg(g, "Wall", alongX, t0, t1, s0, w.lo, 0f, ceil);
            Seg(g, "Wall", alongX, t0, t1, w.hi, s1, 0f, ceil);
            break;
        }
        Seg(wg, "Wall_BelowSill", alongX, t0, t1, w.lo, w.hi, 0f, w.sill);
        Seg(wg, "Wall_AboveHead", alongX, t0, t1, w.lo, w.hi, w.head, ceil);
        float tm = (t0 + t1) / 2, ta = tm - 0.006f, tb = tm + 0.006f;
        if (alongX) Box(wg, "Glass", w.lo, w.hi, ta, tb, w.sill, w.head, mGlass); else Box(wg, "Glass", ta, tb, w.lo, w.hi, w.sill, w.head, mGlass);
        float f0 = t0, f1 = t0 - sgn * CasingProud;
        Trim(wg, alongX, f0, f1, w.lo - CasingW, w.lo, w.sill, w.head + CasingW);
        Trim(wg, alongX, f0, f1, w.hi, w.hi + CasingW, w.sill, w.head + CasingW);
        Trim(wg, alongX, f0, f1, w.lo - CasingW, w.hi + CasingW, w.head, w.head + CasingW);
        Trim(wg, alongX, t1, t0 - sgn * StoolProud, w.lo - CasingW - 0.025f, w.hi + CasingW + 0.025f, w.sill - StoolT, w.sill);   // stool
        Trim(wg, alongX, f0, f1, w.lo - CasingW, w.hi + CasingW, w.sill - StoolT - 0.09f, w.sill - StoolT);                      // apron
    }

    static void Seg(GameObject p, string n, bool alongX, float t0, float t1, float s0, float s1, float y0, float y1)
    {
        float ta = Mathf.Min(t0, t1), tb = Mathf.Max(t0, t1);
        void B(float b0, float b1, Material m) { if (alongX) Box(p, n, s0, s1, ta, tb, b0, b1, m); else Box(p, n, ta, tb, s0, s1, b0, b1, m); }
        if (WallMat == null) { B(y0, y1, mWall); return; }
        if (y0 < Wainscot && y1 > Wainscot) { B(y0, Wainscot, WainscotMat); B(Wainscot, y1, WallMat); }
        else B(y0, y1, y1 <= Wainscot ? WainscotMat : WallMat);
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
        if (d.hi - d.lo < 1.4f) return;
        // a pair (the sunroom's French doors, user Oct 15): the meeting stiles, a dark line down the middle
        float m = (d.lo + d.hi) / 2, f2 = t0 - sgn * 0.04f;
        if (alongX) Box(p, "PropDoor_Meet", m - 0.01f, m + 0.01f, Mathf.Min(f2, t0), Mathf.Max(f2, t0), 0f, d.height, mRail);
        else Box(p, "PropDoor_Meet", Mathf.Min(f2, t0), Mathf.Max(f2, t0), m - 0.01f, m + 0.01f, 0f, d.height, mRail);
    }

    static void Rail(GameObject p, Door d)
    {
        // open balustrade: a 6 cm handrail and 4 cm spindles at most 0.12 m apart (a body still can't pass)
        var g = Child(p, "Rail");
        if (d.alongX) Box(g, "Rail", d.lo, d.hi, d.coord - 0.03f, d.coord + 0.03f, RailHeight - 0.06f, RailHeight, mRail);
        else Box(g, "Rail", d.coord - 0.03f, d.coord + 0.03f, d.lo, d.hi, RailHeight - 0.06f, RailHeight, mRail);
        int k = Mathf.Max(1, Mathf.CeilToInt((d.hi - d.lo) / 0.12f));
        for (int i = 0; i < k; i++)
        {
            float s = d.lo + (i + 0.5f) * (d.hi - d.lo) / k;
            if (d.alongX) Box(g, "Spindle", s - 0.02f, s + 0.02f, d.coord - 0.02f, d.coord + 0.02f, 0f, RailHeight - 0.06f, mRail);
            else Box(g, "Spindle", d.coord - 0.02f, d.coord + 0.02f, s - 0.02f, s + 0.02f, 0f, RailHeight - 0.06f, mRail);
        }
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
        mGlass = Mat("Glass", new Color(0.75f, 0.85f, 0.90f, 0.15f));
        mGlass.SetFloat("_SurfaceType", 1f); mGlass.SetFloat("_Smoothness", 0.95f); HDMaterial.ValidateMaterial(mGlass);
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

    // Winter daylight (user, Oct 15: natural light through the windows for daytime scenes): a low December sun, a snow
    // ground outside the windows, and the room lamps on N (HouseNightMode: day = lamps off). The house's compass bearing is
    // NOT measured yet: FrontAzimuth is a placeholder until the film's daytime exterior shadows (frames 4382, 11908) set it.
    const float FrontAzimuth = 90f;                       // compass bearing the front (+spec x) faces; placeholder, DEVIATIONS 34
    const float SunAzimuth = 155f, SunElevation = 21f;    // Chicago, Dec 21, ~10:30 am
    static void Daylight(GameObject root, float groundY)
    {
        var day = Child(root, "Daylight");
        float rel = (SunAzimuth - FrontAzimuth) * Mathf.Deg2Rad, el = SunElevation * Mathf.Deg2Rad;
        var toSun = new Vector3(Mathf.Cos(rel) * Mathf.Cos(el), Mathf.Sin(el), -Mathf.Sin(rel) * Mathf.Cos(el));   // spec +z (right, from inside facing front) -> world -z
        var sun = new GameObject("Sun").AddComponent<Light>(); sun.transform.parent = day.transform;
        sun.type = LightType.Directional; sun.transform.rotation = Quaternion.LookRotation(-toSun);
        sun.gameObject.AddComponent<HDAdditionalLightData>();   // first: adding it resets the light's intensity
        sun.intensity = 100000f; sun.color = Color.white; sun.shadows = LightShadows.Soft;   // the sky model reddens a low sun; white keeps the snow white
        var snow = GameObject.CreatePrimitive(PrimitiveType.Cube); snow.name = "Outdoors_Snow"; snow.transform.parent = day.transform;
        Object.DestroyImmediate(snow.GetComponent<Collider>());
        snow.transform.position = new Vector3(6f, groundY - 0.12f, -8f); snow.transform.localScale = new Vector3(200f, 0.2f, 200f);   // top 2 cm under the ground floor (hidden by its floor boxes)
        snow.GetComponent<Renderer>().sharedMaterial = Mat("Snow", new Color(0.92f, 0.94f, 0.97f));
        var lamps = root.transform.Cast<Transform>().SelectMany(t => t.GetComponentsInChildren<Transform>(true)).FirstOrDefault(t => t.name == "Lights");
        var mode = new GameObject("Day and night - press N").AddComponent<HouseNightMode>(); mode.transform.parent = day.transform;
        mode.nightLayer = lamps != null ? lamps.gameObject : null; mode.interiorLights = new Light[0]; mode.daytimeEnabled = new bool[0];
        if (lamps != null) lamps.gameObject.SetActive(false);
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
    static List<Vector3> Stair(GameObject root, JToken st, bool skipFloorPatch, string child = "MainStair", bool dress = true)
    {
        if (st == null || st.Type == JTokenType.Null) return new List<Vector3>();
        var g = Child(root, child);
        foreach (var b in st["boxes"])
        {
            string kind = (string)b["kind"];
            if (kind == "floor" && skipFloorPatch) continue;   // the ground floor's foyer is built for real
            var m = kind == "rail" ? mRail : kind == "wall" ? mWall : kind == "floor" || (!dress && kind == "step") ? mFloor : kind == "ceiling" ? mCeil : mHall;   // attic treads: bare wood (film)
            string name = (string)b["name"]; var ds = dress ? Dress?["stair"] : null;
            if (ds != null)
            {
                if (kind == "step") m = DressMat(ds["step"]);
                else if (kind == "landing") m = DressMat(ds["landing"]);
                else if (kind == "wall") m = Dress["walls"]["wallpaper_texture"] != null ? Wallpaper(Dress["walls"]) : DressMat(ds["well_wall"]);
                else if (kind == "rail" && name.Contains("spindle")) m = DressMat(ds["spindle"]);
                if (ds["hide"].Any(h => System.Text.RegularExpressions.Regex.IsMatch(name, "^" + ((string)h).Replace("*", ".*") + "$")))
                {   // hidden: the dressing replaces it, but its collider stays (the walk gates do not change)
                    Box(g, name, (float)b["x"][0], (float)b["x"][1], -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0], (float)b["y"][1], m);
                    Object.DestroyImmediate(g.transform.GetChild(g.transform.childCount - 1).GetComponent<MeshRenderer>());
                    continue;
                }
            }
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
        // "player": the walkable Player itself (FpsController.TickMotion at 60 fps, 1.8 m, its walk speed). The two test bodies
        // missed the user's stall between risers 5 and 6 (Oct 15); this one reproduces it without the ramps.
        foreach (var (name, r, h) in new[] { ("bandit", 0.275f, 1.85f), ("kevin", 0.20f, 1.20f), ("player", 0.275f, 1.8f) })
        {
            var go = new GameObject("StairWalker_" + name); var cc = go.AddComponent<CharacterController>();
            cc.radius = r; cc.height = h; cc.center = new Vector3(0, h / 2, 0); cc.stepOffset = StepOffset; cc.skinWidth = 0.02f;
            var fc = name == "player" ? go.AddComponent<FpsController>() : null;
            if (fc != null) cc.skinWidth = PlayerSkin;   // exactly the Player's settings
            foreach (var (route, pts) in new[] { ("up", path), ("down", Enumerable.Reverse(path).ToList()) })
            {
                go.transform.position = pts[0] + Vector3.up * 0.05f; Physics.SyncTransforms();
                for (int i = 1; i < pts.Count; i++)
                {
                    Vector3 target = pts[i]; float vy = 0f;
                    var from = go.transform.position; int used = 0;
                    for (int t = 0; t < 1500; t++, used++)
                    {
                        var p = go.transform.position; var flat = new Vector3(target.x - p.x, 0, target.z - p.z);
                        if (flat.magnitude < 0.05f) break;
                        if (fc != null) { fc.TickMotion(flat.normalized, false, false, 1f / 60f); continue; }
                        vy = cc.isGrounded ? -1f : vy - 9.81f * 0.02f;
                        cc.Move(Vector3.ClampMagnitude(flat, 3.5f / 60f) + Vector3.up * vy * 0.02f);   // the player's walk speed per frame
                    }
                    for (int t = 0; t < 25; t++) cc.Move(Vector3.down * 0.05f);   // settle onto the floor
                    var e = go.transform.position; float dxz = new Vector2(e.x - target.x, e.z - target.z).magnitude, dy = Mathf.Abs(e.y - target.y);
                    // the player must also not stall: at most 1.5 x the frames a clean walk at its speed needs (+0.5 s)
                    float need = new Vector2(target.x - from.x, target.z - from.z).magnitude / (3.5f / 60f);
                    bool slow = fc != null && used > need * 1.5f + 30;
                    bool ok = dxz < 0.15f && dy < 0.1f && !slow; if (!ok) bad++;
                    string by = "";
                    if (!ok && Physics.CapsuleCast(e + Vector3.up * (r + 0.05f), e + Vector3.up * (h - r), r * 0.98f,
                                                   new Vector3(target.x - e.x, 0, target.z - e.z).normalized, out var hit, 1f))
                        by = $" by {hit.collider.transform.parent?.name}/{hit.collider.name} at ({e.x:F2}, {e.y:F2}, {-e.z:F2}) spec x,y,z";
                    lines.Add($"{(ok ? "ok     " : "BLOCKED")} {name} {route} leg {i}: ended {dxz:F2} m from waypoint, {dy:F2} m off its floor height{by}" +
                              (fc != null ? $", {used} frames (clean walk {need:F0}){(slow ? " STALLED" : "")}" : ""));
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
            cc.radius = r; cc.height = h; cc.center = new Vector3(0, h / 2, 0); cc.stepOffset = StepOffset; cc.skinWidth = 0.02f;
            foreach (var s in spaces.Where(s => s.kind == "room" || s.kind == "hall"))
            {
                // target: the centre of the largest cell a body can stand in (an L-shaped foyer's largest cell centres on the stair)
                Vector3 Mid((float, float, float, float) q) => new Vector3((q.Item1 + q.Item2) / 2, FloorY, (q.Item3 + q.Item4) / 2);
                var order = Cells(s.pts).OrderByDescending(q => (q.Item2 - q.Item1) * (q.Item4 - q.Item3)).ToList();
                var c = order.FirstOrDefault(q => !Physics.CheckCapsule(Mid(q) + Vector3.up * (r + 0.06f), Mid(q) + Vector3.up * (h - r), r));
                if (c == default) { lines.Add($"skip    {name} {s.name}: no cell to stand in (its floor is a stair)"); continue; }
                var mid = Mid(c);
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

    // Seams (Oct 15, user: "walls and ceilings must line up"): every exposed face of the structural boxes (walls, headers,
    // floors, ceilings, stair structure; not trim, rails, props or dressing) against every other one facing the same way.
    //   OVERLAP: coplanar within 1 cm, overlapping, different materials (flicker / z-fighting)
    //   LEDGE:   the same surface continued 0.5-6 cm off its plane, stacked or end to end (a visible step)
    //   GAP:     coplanar but 0.5-10 cm short of meeting along the surface (a slit)
    // A face covered by a touching box (back-to-back walls) is internal and skipped.
    // Rooms as volumes for the seam check: (polygon, floor y, top y). Stairwells span from the floor below to their ceiling.
    static List<(List<Vector2> pts, float y0, float y1)> SeamRooms = new();

    static string SeamCheck(params GameObject[] roots)
    {
        // only surfaces seen from inside a room count: the point just in front of a face must be in a room's open volume
        bool Seen(Vector3 q) => SeamRooms.Any(r => q.y > r.y0 + 0.002f && q.y < r.y1 - 0.002f && Inside(r.pts, new Vector2(q.x, q.z)));
        string[] skip = { "Dressing", "Furniture", "Rail", "Spindle", "spindle", "_cap", "Casing", "PropDoor", "Window", "Glass", "Stool", "Apron", "Light", "Walker", "Outdoors" };
        var boxes = roots.Where(r => r != null).SelectMany(r => r.GetComponentsInChildren<MeshRenderer>())
            .Where(m => !skip.Any(k => m.name.Contains(k) || (m.transform.parent != null && m.transform.parent.name.Contains(k)) ||
                                        (m.transform.parent?.parent != null && m.transform.parent.parent.name.Contains(k))))
            .Where(m => Quaternion.Angle(m.transform.rotation, Quaternion.identity) < 0.1f)
            .Select(m => (m, b: m.bounds)).ToList();
        var faces = new List<(int box, int ax, float c, int n, Vector2 lo, Vector2 hi)>();
        for (int i = 0; i < boxes.Count; i++)
            for (int ax = 0; ax < 3; ax++)
            {
                var b = boxes[i].b; int u = (ax + 1) % 3, v = (ax + 2) % 3;
                var lo = new Vector2(b.min[u], b.min[v]); var hi = new Vector2(b.max[u], b.max[v]);
                faces.Add((i, ax, b.min[ax], -1, lo, hi)); faces.Add((i, ax, b.max[ax], 1, lo, hi));
            }
        float Ov(float a0, float a1, float b0, float b1) => Mathf.Min(a1, b1) - Mathf.Max(a0, b0);
        Vector3 P(int ax, float c, float a, float b) { var q = Vector3.zero; q[ax] = c; q[(ax + 1) % 3] = a; q[(ax + 2) % 3] = b; return q; }
        bool Solid(Vector3 q, int not = -1) { for (int k = 0; k < boxes.Count; k++) if (k != not && boxes[k].b.Contains(q)) return true; return false; }
        // internal: the point just outside the face's centre is inside another box (back-to-back walls, a ceiling's edge in a wall)
        var exposed = faces.Where(f => { var q = P(f.ax, f.c + f.n * 0.003f, (f.lo.x + f.hi.x) / 2, (f.lo.y + f.hi.y) / 2); return !Solid(q, f.box) && Seen(q); }).ToList();
        var lines = new List<string>(); int over = 0, ledge = 0, gap = 0;
        string Where(int i) { var c = boxes[i].b.center; return $"{boxes[i].m.transform.parent?.name}/{boxes[i].m.name} at ({c.x:F2}, {c.y:F2}, {-c.z:F2})"; }
        string[] axn = { "x", "y", "z" };
        for (int i = 0; i < exposed.Count; i++)
            for (int j = i + 1; j < exposed.Count; j++)
            {
                var f = exposed[i]; var g = exposed[j];
                if (f.box == g.box || f.ax != g.ax || f.n != g.n) continue;
                float d = Mathf.Abs(f.c - g.c);
                if (d > 0.06f) continue;
                float ou = Ov(f.lo.x, f.hi.x, g.lo.x, g.hi.x), ov = Ov(f.lo.y, f.hi.y, g.lo.y, g.hi.y);
                if (d < 0.01f && ou > 0.05f && ov > 0.05f)
                {
                    if (boxes[f.box].m.sharedMaterial != boxes[g.box].m.sharedMaterial)
                    { over++; if (over <= 40) lines.Add($"OVERLAP {axn[f.ax]}={f.c:F3}/{g.c:F3}: {Where(f.box)} | {Where(g.box)}"); }
                }
                else if (d >= 0.005f && ((ou > 0.05f && Mathf.Abs(ov) < 0.02f && ov <= 0.02f) || (ov > 0.05f && Mathf.Abs(ou) < 0.02f && ou <= 0.02f)))
                { ledge++; if (ledge <= 200) lines.Add($"LEDGE   {axn[f.ax]} {f.c:F3} vs {g.c:F3} ({d * 100:F1} cm): {Where(f.box)} | {Where(g.box)}"); }
                else if (d < 0.005f && ((ou > 0.05f && ov < -0.005f && ov > -0.10f) || (ov > 0.05f && ou < -0.005f && ou > -0.10f)))
                {   // a slit only if it is empty just behind the surface (a wall or slab filling it is a joint, not a gap)
                    bool alongU = ov < 0;
                    float a = alongU ? (Mathf.Max(f.lo.x, g.lo.x) + Mathf.Min(f.hi.x, g.hi.x)) / 2 : (Mathf.Min(f.hi.x, g.hi.x) + Mathf.Max(f.lo.x, g.lo.x)) / 2;
                    float b = alongU ? (Mathf.Min(f.hi.y, g.hi.y) + Mathf.Max(f.lo.y, g.lo.y)) / 2 : (Mathf.Max(f.lo.y, g.lo.y) + Mathf.Min(f.hi.y, g.hi.y)) / 2;
                    if (Solid(P(f.ax, f.c - f.n * 0.01f, a, b)) || !Seen(P(f.ax, f.c + f.n * 0.01f, a, b))) continue;
                    gap++; if (gap <= 200) lines.Add($"GAP     {axn[f.ax]}={f.c:F3} ({-Mathf.Min(ou, ov) * 100:F1} cm): {Where(f.box)} | {Where(g.box)}");
                }
            }
        foreach (var (hp, what) in HoleProbes)   // thresholds and outside corners must be solid (a hole there sees the outdoors)
            if (!Solid(hp)) { gap++; if (gap <= 200) lines.Add($"GAP     hole at {what}: ({hp.x:F2}, {hp.y:F2}, {-hp.z:F2}) is empty"); }
        lines.Insert(0, $"Seam check: {boxes.Count} structural boxes, {over} overlaps (flicker), {ledge} ledges, {gap} gaps");
        return string.Join("\n", lines) + "\n";
    }

    // Leaks: from a 0.5 m grid at eye height in every space (both floors), rays go up and in 16 horizontal directions.
    // A ray that hits nothing within 40 m escaped the house (a hole to the sky or outside). Window glass has a collider,
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
    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderViews -quit -logFile - [-scene IntactHouseReference] [-views views-buzz-old.json]
    public static void RenderViews()
    {
        var a = System.Environment.GetCommandLineArgs(); int si = System.Array.IndexOf(a, "-scene"), vi = System.Array.IndexOf(a, "-views");
        EditorSceneManager.OpenScene($"Assets/Scenes/{(si >= 0 ? a[si + 1] : "Greybox_Upstairs")}.unity");
        var go = new GameObject("ViewCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        // Render-only fill, never saved (the scene is not saved): "-fill <intensity>" hangs a shadowless point light on the
        // camera; "-ev <EV100>" fixes exposure through a temporary top-priority global volume (scene assets untouched).
        int fi = System.Array.IndexOf(a, "-fill"), ei = System.Array.IndexOf(a, "-ev");
        if (fi >= 0)
        {
            var l = new GameObject("FillLight").AddComponent<Light>(); l.transform.SetParent(go.transform, false);
            l.type = LightType.Point; l.range = 25f; l.intensity = float.Parse(a[fi + 1]); l.shadows = LightShadows.None;
            l.gameObject.AddComponent<HDAdditionalLightData>();
        }
        if (ei >= 0)
        {
            var prof = ScriptableObject.CreateInstance<VolumeProfile>(); var ex = prof.Add<Exposure>(true);
            ex.mode.value = ExposureMode.Fixed; ex.fixedExposure.value = float.Parse(a[ei + 1]);
            var vol = new GameObject("FillExposure").AddComponent<Volume>(); vol.isGlobal = true; vol.priority = 10000f; vol.sharedProfile = prof;
        }
        foreach (var v in JArray.Parse(File.ReadAllText(Path.Combine(CaptureDir, "views", vi >= 0 ? a[vi + 1] : "views.json"))))
        {
            Vector3 V(JToken t) => new Vector3((float)t[0], (float)t[1], (float)t[2]);
            // optional "hide": object paths to switch off for this view (e.g. "Upstairs", "Ground/Ceilings")
            var hidden = (v["hide"] ?? new JArray()).Select(h => GameObject.Find((string)h)).Where(o => o).ToList();
            hidden.ForEach(o => o.SetActive(false));
            go.transform.position = V(v["pos"]); go.transform.LookAt(V(v["look_at"])); cam.fieldOfView = (float)v["vfov"];
            if (fi >= 0 || ei >= 0) cam.Render();   // warm-up frame: HDRP's first frame has no sky ambient yet (came out all brown)
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
        var cc = p.AddComponent<CharacterController>(); cc.radius = 0.275f; cc.height = 1.85f; cc.center = new Vector3(0, 0.925f, 0); cc.stepOffset = StepOffset; cc.skinWidth = PlayerSkin;
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
