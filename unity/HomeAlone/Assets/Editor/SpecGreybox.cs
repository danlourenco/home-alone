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
public static partial class SpecGreybox
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

    class Door { public string a, b, kind; public bool alongX; public float coord, lo, hi, height, spring; }
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
                height = d["height"].Type == JTokenType.Null ? 0f : (float)d["height"],
                spring = d["spring"] == null || d["spring"].Type == JTokenType.Null ? 0f : (float)d["spring"] };
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
        foreach (var c in up["ceilings"].Where(c => c["band"] == null))   // each room's floor finish (not under a rail band's ceiling strip)
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
                if (o["bare"] != null) continue;   // the frame belongs to a model (the door's sidelights): glass only
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

    // ---- Wall-grid HOUSE (tasks/wall-grid-plan.md phase 5): both floors from spec/geometry.json, the stair hall one two-storey
    // space (stacked walls, the landing a slab inside it), the stairs and dressing from the spec. Saved as House_WallGrid; the
    // old builder's scene (Greybox_Upstairs) is left as it was. Gates: door walks, stair walks, room walks, seams, leaks,
    // and PEEK (no view from a room you can walk in into a space you cannot: the slots the user found, Oct 15).
    [MenuItem("HomeAlone/Build Wall-Grid House")]
    public static void BuildWallGrid()
    {
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        var j = JObject.Parse(File.ReadAllText(SpecPath)); var gj = JObject.Parse(File.ReadAllText(GroundPath));
        var dp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/foyer.json"));
        Dress = File.Exists(dp) ? JObject.Parse(File.ReadAllText(dp)) : null;
        float gy = (float)gj["floor_y_m"];
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        MakeMaterials(); HoleProbes.Clear(); TrimRuns.Clear(); Windows = new List<Win>();
        LoadOpenings();   // SpecGreybox.Openings.cs: HOUSE-KERNEL step 2 (spec/openings.json; own_trim = the switch)
        Landings = j["stair"]["boxes"].Where(b => (string)b["kind"] == "landing").Select(b => ((float)b["x"][0], (float)b["x"][1],
            -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0])).ToList();
        var paper = Dress != null ? Dress["walls"]["spaces"].Select(n => (string)n).ToHashSet() : new HashSet<string>();
        FloorY = 0f;
        var root = new GameObject("Upstairs");
        var (spaces, doors) = Storey(root, (JObject)geo["upstairs"], new HashSet<string> { "main_stair_opening" }, true);
        FloorY = gy;
        var groot = new GameObject("Ground");
        if (gj["stair"]?["ceiling_openings"] is JArray holes)   // the back stair rises through its ceiling (spec ceiling_openings)
            geo["ground"]["ceilings"] = CutHoles((JArray)geo["ground"]["ceilings"], holes);
        if (gj["basement"]?["floor_openings"] is JArray fholes)   // the basement stair goes down through the ground plate (SpecGreybox.Basement)
            geo["ground"]["floor"] = CutHoles((JArray)geo["ground"]["floor"], fholes);
        var (gspaces, gdoors) = Storey(groot, (JObject)geo["ground"], paper, false);
        LayCasings(root, groot);   // step 2: every opening's casing from its own record (the per-case Trim() calls are off then)
        FloorY = 0f;
        var stairPath = Stair(root, j["stair"], true, stairOnly: true);
        // its shaft and cap close it from above (user, Oct 16: sunlight down the void)
        var atticPath = Stair(root, j["attic_stair"], false, "AtticStair", dress: false, stairOnly: true, keepAbove: 2.4f);
        FloorY = gy;
        var servicePath = new List<Vector3>();
        if (gj["stair"] != null && gj["stair"].Type != JTokenType.Null)   // service stair: its solid steps read as the papered wall under it
            servicePath = Stair(groot, gj["stair"], false, "ServiceStair", dress: false, stairOnly: true, stepMat: KitchenPaper())
                .Select(q => q + Vector3.up * gy).ToList();
        var basementPath = Basement(groot, gj, gy);   // SpecGreybox.Basement.cs: the basement shell (hifi_basement.py; changes/2026-10-18-basement-shell.json)
        Dressing(groot, gy);
        FloorY = 0f;
        Lights(root, spaces); FloorY = gy; Lights(groot, gspaces); FloorY = 0f;
        Volume(root);
        CutWallOpenings(gj["wall_openings"], gy);
        HiFiStair(root, gy);
        HiFiLights(root, gy);
        Hall(root);                    // SpecGreybox.Hall.cs: the upstairs hall's dressing, sconces and plants (spec/dressing/hall.json)
        Trunk(root);                   // SpecGreybox.Trunk.cs: Buzz's footlocker, bought scan rebuilt hollow (spec/dressing/buzz_trunk.json)
        Kevin(root);                   // SpecGreybox.Kevin.cs: Kevin and Jeff's room, bunks/curtains/props + night lamps (hifi_kevin.py; changes/2026-10-18-kevin-room.json)
        Parents(root);                 // SpecGreybox.Buzz.cs: the parents' bedroom furniture boxes (spec/dressing/parents.json; changes/2026-10-18-parents-room.json)
        Attic(root);                   // SpecGreybox.Attic.cs: the attic shell over the attic stair (hifi_attic.py; changes/2026-10-18-attic-shell.json)
        ParentsFireplace(root);        // SpecGreybox.ParentsFireplace.cs: the parents' fireplace (hifi_parents_fireplace.py; changes/2026-10-18-parents-fireplace.json)
        Buzz(root);                    // SpecGreybox.Buzz.cs: Buzz's furniture against the faces (spec/dressing/buzz.json; changes/2026-10-17-buzz-layout.json)
        BuzzProps(root);               // SpecGreybox.BuzzProps.cs: Buzz's hero props (props lane; hifi_buzz_props.py -> BuzzProps.glb, the Tarantula pack, the bat)
        SwingDoors(groot, gy, geo["ground"]);
        FrenchDoors(root, groot, gy, geo["ground"]);   // FrenchDoors.cs: the glazed French door pairs (changes/2026-10-16-french-doors.json)
        StoreProps(root, groot, gy);   // StoreProps.cs: Asset Store furniture in measured boxes (spec/dressing/store_props.json)
        DenScreenPatch();              // SpecGreybox.Den.cs: the video screen over the bought TV's glass (after StoreProps placed it)
        ParentsFloorLamp(root);        // SpecGreybox.Curtains.cs: the parents' floor lamp lit at night (after StoreProps placed it)
        SketchfabProps(root, gy);      // SpecGreybox.Sketchfab.cs: the user's Sketchfab downloads (BB gun, glove, helmet, trophies, corkboard, Hershey, den table)
        if (TrimFromFaces) FaceTrim(groot); else LayTrim(groot, new[] { "PropDoor", "Casing", "FrontDoor_HiFi", "MainStair_HiFi" });   // SpecGreybox.Trim.cs
        Envelope(root, geo, j["attic_stair"]["boxes"], gj["wall_openings"], gj["stair"]?["ceiling_openings"], gy);
        FilmFront(root, geo, gj["wall_openings"], gy);
        Daylight(root, gy);
        FilmFill(GameObject.Find("Upstairs/Daylight/DayLayer"), geo, j["attic_stair"]["boxes"], gy);
        var (spawn, spawnYaw) = FrontDoorSpawn(geo["ground"], j["stair"], gy);
        Player(spawn, spawnYaw);
        ExteriorLook(gy);   // SpecGreybox.ExteriorRealism.cs: outside-only fog/grade/bloom/night exposure, falling snow on the camera
        var entranceDoor = FoyerInteractions(root,gy);
        var backDoor = BackDoorInteractions(root, gy);   // SpecGreybox.BackDoor.cs: the kitchen back door opens (Oct 19)
        FoyerMirror(root,gy);
        var player = GameObject.Find("Player"); player.SetActive(false);
        Physics.SyncTransforms();
        stepName = null; BudgetFails.Clear(); Step("WalkTest");
        string report = "WALL-GRID HOUSE (both floors from spec/geometry.json)\nUPSTAIRS\n" + WalkTest(spaces, doors);
        Step("WalkTest ground");
        FloorY = gy; report += "GROUND\n" + WalkTest(gspaces, gdoors); FloorY = 0f;
        Step("StairWalk");
        backDoor.SetInstant(true); Physics.SyncTransforms();   // the BACK DOOR route walks through it, out and in
        report += StairWalk(stairPath) + StairWalk(atticPath) + StairWalk(servicePath) + (basementPath.Count > 1 ? "BASEMENT (kitchen -> landing -> flight -> outside door -> areaway to grade)\n" + StairWalk(basementPath) : "") + string.Concat(YardRoutes(gy, basementPath).Select(r => r.name + "\n" + StairWalk(r.pts)));
        backDoor.SetInstant(false); Physics.SyncTransforms();
        Step("RenderCheck");
        report += RenderCheck(groot.transform.Find("ServiceStair"));
        var dressing = GameObject.Find("Ground/Dressing"); dressing?.SetActive(false); Physics.SyncTransforms();
        var walkIn = doors.Concat(gdoors).Where(d => d.kind != "fake_door").SelectMany(d => new[] { d.a, d.b }).ToHashSet();
        SeamRooms = spaces.Where(sp => walkIn.Contains(sp.name) || sp.kind == "opening").Select(sp => (sp.pts, sp.opens == "down" ? gy : 0f, sp.ceil)).ToList();
        SeamRooms.AddRange(gspaces.Where(sp => walkIn.Contains(sp.name)).Select(sp => (sp.pts, gy, gy + sp.ceil)));
        File.WriteAllText("Library/SeamRooms.json", new JArray(SeamRooms.Select(r => new JArray(r.y0, r.y1, new JArray(r.pts.Select(p => new JArray(p.x, p.y)))))).ToString());   // to re-run the surface gates on the saved scene (CheckBench)
        Step("SeamCheck");
        report += SeamCheck(root, groot);
        Step("LeakAndHeadroom");
        report += LeakAndHeadroom(spaces, gspaces, gy);
        Step("Peek");
        report += Peek(spaces, gspaces, gy, walkIn);
        Step("RoomWalk upstairs");
        report += "UPSTAIRS " + RoomWalk(spaces, doors);
        Step("RoomWalk ground");
        FloorY = gy; report += "GROUND " + RoomWalk(gspaces, gdoors); FloorY = 0f;
        dressing?.SetActive(true); Physics.SyncTransforms();
        SeamRooms.AddRange(BasementRooms(gy).Select(r => (r.pts, r.y0, r.y1)));   // the surface gates see the basement too
        Step("ZFightCheck");
        report += ZFightCheck(root, groot, GameObject.Find("HouseShell"));   // the exterior skin too: seen from rooms through the windows and
                                                                            // sidelights (Oct 18 21:21: a sidelight's outer sill z-fought; the skin was never checked)
        Step("ClashCheck");
        report += ClashCheck(root, groot);
        Step("CasingCheck");
        report += CasingCheck(root, groot);
        Step("OpeningFaceCheck");
        report += OpeningFaceCheck();   // SpecGreybox.OpeningFaces.cs: every door face has a head casing and only its own room's finish
        Step("ArchFitCheck");
        report += ArchFitCheck();   // SpecGreybox.Arch.cs
        Step("PropsCheck");
        report += PropsCheck() + TriangleBudget(root, groot);   // StoreProps.cs; Checks.cs
        Step("TrimCheck");
        report += TrimCheck();   // over every face run of spec/trim_faces.json, either trim path
        Step("EnvelopeCheck");
        report += EnvelopeCheck(geo, j["attic_stair"]["boxes"], gj["wall_openings"], gy);
        Step(null);
        foreach (var f in BudgetFails) report += f + "\n";
        Traps(root, gy);   // Traps.cs: gameplay rigs (spec/dressing/traps.json), after the gates so none of them sees the rig
        report += EntranceCheck(entranceDoor,gy);
        report += BackDoorCheck(backDoor, gy);
        player.SetActive(true);
        Directory.CreateDirectory(CaptureDir);
        File.WriteAllText(Path.Combine(CaptureDir, "walk-test-wallgrid.txt"), report);
        LimitShadows(root.transform.root.gameObject);   // SpecGreybox.Shadows.cs: real-time shadow budget
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), "Assets/Scenes/House_WallGrid.unity");
        Debug.Log("SpecGreybox.BuildWallGrid\n" + report);
        OpeningsOwnTrim = false;   // the other builders keep their per-case casing
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-views") >= 0) RenderViews();   // renders in the same session (one Unity start)
    }

    // a timestamped line before each build check (they log nothing themselves): a silent build.log then means a stuck check, and names it.
    // Each gate also logs its duration when the next starts, and has a time budget (zfight-check skill "Check speed"): over budget is
    // "BUDGET FAIL <gate>" in the report and build.log (unity_pipeline.sh exits 1); the long loops call BudgetGuard, which stops the
    // build mid-gate instead of leaving it silent for hours. A slow gate is a bug: fix its algorithm, never raise the budget to pass.
    static readonly Dictionary<string, float> GateBudget = new() { ["ZFightCheck"] = 30f, ["ClashCheck"] = 60f };   // s (measured Oct 17: 2.2 s and 15.6 s); others 60
    static string stepName; static readonly System.Diagnostics.Stopwatch stepClock = new(); static readonly List<string> BudgetFails = new();
    static float Budget(string gate) => GateBudget.TryGetValue(gate, out var b) ? b : 60f;
    static void Step(string what)
    {
        if (stepName != null)
        {
            float t = (float)stepClock.Elapsed.TotalSeconds;
            Debug.Log($"[{System.DateTime.Now:HH:mm:ss}] BuildWallGrid: {stepName} done in {t:F1} s (budget {Budget(stepName):F0} s)");
            if (t > Budget(stepName)) { var f = $"BUDGET FAIL {stepName}: {t:F0} s, budget {Budget(stepName):F0} s"; BudgetFails.Add(f); Debug.LogError(f); }
        }
        stepName = what; stepClock.Restart();
        if (what != null) Debug.Log($"[{System.DateTime.Now:HH:mm:ss}] BuildWallGrid: {what}");
    }
    static void BudgetGuard()
    {
        if (stepName != null && stepClock.Elapsed.TotalSeconds > Budget(stepName))
            throw new System.TimeoutException($"BUDGET FAIL {stepName}: still running after {Budget(stepName):F0} s, stopped (a slow check is a bug: zfight-check skill)");
    }

    // One storey from geometry.json at the current FloorY: walls (papered on the faces of the named rooms, over the wainscot),
    // floor plate, ceilings, finishes, door/window trim, prop doors, glass, rails, arch tops. Returns the rooms and openings in
    // the spec's shape for the gates.
    static readonly HashSet<string> KitchenRooms = new HashSet<string> { "kitchen", "back_stair" };
    static readonly Color KitchenWall = new Color(0.88f, 0.84f, 0.72f);

    // Trim (baseboard, wainscot cap) runs along papered faces, world boxes; laid last so they stop at everything on the wall
    static List<(Vector3 lo, Vector3 hi, Material m)> TrimRuns = new();
    // Openings through the walls of both storeys (spec wall_openings, ground-floor metres): every wall box the opening passes through
    // is replaced by the pieces around it (copies keep their material and collider). The window model reads the same numbers.
    static void CutWallOpenings(JToken openings, float gy)
    {
        if (openings == null) return;
        foreach (var o in openings)
        {
            var lo = new Vector3((float)o["x"][0], CutBottom(o) + gy, -(float)o["z"][1]);   // step 2: a model window's rough opening (under its stool)
            var hi = new Vector3((float)o["x"][1], (float)o["y"][1] + gy, -(float)o["z"][0]);
            var hole = new Bounds((lo + hi) / 2, hi - lo);
            int cut = 0;
            foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None).Where(r => r.name == "Wall").ToList())
            {
                var b = r.bounds;
                if (b.min.x >= hi.x - 1e-4f || b.max.x <= lo.x + 1e-4f || b.min.y >= hi.y - 1e-4f || b.max.y <= lo.y + 1e-4f || b.min.z >= hi.z - 1e-4f || b.max.z <= lo.z + 1e-4f) continue;
                void Piece(Vector3 a, Vector3 c)
                {
                    if (c.x - a.x < 1e-3f || c.y - a.y < 1e-3f || c.z - a.z < 1e-3f) return;
                    var g = Object.Instantiate(r.gameObject, r.transform.parent); g.name = "Wall";
                    g.transform.position = (a + c) / 2; g.transform.localScale = c - a;
                }
                // the opening runs through the wall's thickness (x); pieces below, above, and either side (z) of it
                Piece(b.min, new Vector3(b.max.x, lo.y, b.max.z));
                Piece(new Vector3(b.min.x, hi.y, b.min.z), b.max);
                Piece(new Vector3(b.min.x, Mathf.Max(b.min.y, lo.y), b.min.z), new Vector3(b.max.x, Mathf.Min(b.max.y, hi.y), lo.z));
                Piece(new Vector3(b.min.x, Mathf.Max(b.min.y, lo.y), hi.z), new Vector3(b.max.x, Mathf.Min(b.max.y, hi.y), b.max.z));
                Object.DestroyImmediate(r.gameObject); cut++;
            }
            Debug.Log($"CutWallOpenings {(string)o["name"]}: {cut} wall boxes cut");
        }
        Physics.SyncTransforms();
    }

    // The dining room's swing doors (tools/house/hifi_swing_door.py, Marina 228 s) in both dining-kitchen doors, hinged on the jamb
    // nearer the foyer, turned by SwingDoor.cs; no collider (the openings stay walkable, the gates do not change). The second one (the
    // door by the corner, walk note Oct 18 21:20): film 10512 (Harry crosses the kitchen to it), 10534-10536 (he comes through it into
    // the dining room; brass push plate on the leaf)
    static void SwingDoors(GameObject root, float gy, JToken ground)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/SwingDoor.glb");
        var ops = ground["openings"].Where(q => q["between"].Select(t => (string)t).SequenceEqual(new[] { "dining_room", "kitchen" }))
            .OrderByDescending(q => (float)q["hi"]).ToList();
        if (ops.Count == 0 || a == null) { Debug.LogWarning("SwingDoors: no opening or model"); return; }
        for (int i = 0; i < ops.Count; i++)
        {
            var o = ops[i];
            var hinge = new GameObject(i == 0 ? "DiningSwingDoor" : "DiningSwingDoor" + (i + 1)); hinge.transform.SetParent(root.transform, false);
            hinge.transform.position = new Vector3((float)o["c"], gy, -((float)o["hi"] - 0.005f));
            var leaf = (GameObject)Object.Instantiate(a, hinge.transform); leaf.name = "Leaf"; leaf.transform.localPosition = Vector3.zero;
            float w = (float)o["hi"] - (float)o["lo"] - 0.01f;
            leaf.transform.localScale = new Vector3(1f, 1f, w / ((float)ops[0]["hi"] - (float)ops[0]["lo"] - 0.01f));   // the model is built to the first door
            foreach (var c in leaf.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
            foreach (var r in leaf.GetComponentsInChildren<MeshRenderer>())
            {
                if (r.sharedMaterial != null && r.sharedMaterial.name.StartsWith("SD_Brass")) r.sharedMaterial = BrassMat();
                else if (r.sharedMaterial != null && r.sharedMaterial.name.StartsWith("SD_Paint")) r.sharedMaterial = mProp;   // the house's door paint (HDRP/Lit)
            }
            var sd = hinge.AddComponent<SwingDoor>(); sd.leaf = leaf.transform; sd.width = w;
        }
    }

    static void LayTrim(GameObject parent, string[] blockers)
    {   // sampled every 5 mm against the actual surfaces of what is mounted on the wall (doors, casings, the stair's skirt):
        // bounding boxes would cut whole walls (the stair model's box covers most of the hall)
        var g = Child(parent, "Trim");
        bool IsBlocker(Transform t) => blockers.Any(b => t.name.Contains(b) || (t.parent != null && t.parent.name.Contains(b)));
        var temp = new List<Collider>();
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (r.enabled && IsBlocker(r.transform) && r.GetComponent<Collider>() == null && r.GetComponent<MeshFilter>()?.sharedMesh is Mesh mesh)
            { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mesh; temp.Add(mc); }
        Physics.SyncTransforms();
        int laid = 0; const float step = 0.005f;
        foreach (var (lo, hi, m) in TrimRuns)
        {
            bool alongX = hi.x - lo.x > hi.z - lo.z;
            float a = alongX ? lo.x : lo.z, end = alongX ? hi.x : hi.z;
            bool Blocked(float t)
            {
                var c = (lo + hi) / 2; if (alongX) c.x = t; else c.z = t;
                // the cell's full length along the run (a blocker 1 mm into it ends the run there); across, 2 cm either side of the trim:
                // anything mounted on the wall in front of it stops it, not only what it touches (the front door's sidelight frames stand
                // 1.5 cm off the wall, and a baseboard ran on behind them). The wall side holds no blockers.
                const float reach = 0.02f;
                var half = new Vector3(alongX ? step / 2 - 2e-4f : (hi.x - lo.x) / 2 + reach, (hi.y - lo.y) / 2 - 0.002f, alongX ? (hi.z - lo.z) / 2 + reach : step / 2 - 2e-4f);
                return Physics.OverlapBox(c, Vector3.Max(half, Vector3.one * 0.001f), Quaternion.identity, ~0, QueryTriggerInteraction.Ignore).Any(col => IsBlocker(col.transform));
            }
            void Lay(float s0, float s1)
            {
                if (s1 - s0 < 0.02f) return; laid++;
                if (alongX) Box(g, "Trim", s0, s1, lo.z, hi.z, lo.y, hi.y, m); else Box(g, "Trim", lo.x, hi.x, s0, s1, lo.y, hi.y, m);
                g.transform.GetChild(g.transform.childCount - 1).position -= new Vector3(0, FloorY, 0);   // Box adds FloorY; runs are world already
            }
            float start = a; bool open = false;
            for (float t = a + step / 2; t < end; t += step)
            {
                bool free = !Blocked(t);
                if (free && !open) { start = t - step / 2; open = true; }
                if (!free && open) { Lay(start, t - step / 2); open = false; }
            }
            if (open) Lay(start, end);
        }
        foreach (var c in temp) Object.DestroyImmediate(c);
        Physics.SyncTransforms();
        Debug.Log($"LayTrim: {TrimRuns.Count} runs -> {laid} pieces");
        TrimRuns.Clear();
    }

    static (List<Space>, List<Door>) Storey(GameObject root, JObject st, HashSet<string> papered, bool carpetHalls)
    {
        var specLike = new JObject {
            ["spaces"] = new JArray(st["rooms"].Select(r => new JObject { ["name"] = r["name"], ["kind"] = r["kind"], ["opens"] = r["opens"],
                                                                          ["ceiling_m"] = r["ceil"], ["polygon_xz"] = r["poly"] })),
            ["doors"] = new JArray(st["openings"].Where(o => (string)o["kind"] != "window").Select(o => new JObject {
                ["between"] = o["between"], ["kind"] = o["kind"], ["spec_axis"] = o["axis"], ["wall_coord_spec"] = o["c"],
                ["span_spec"] = new JArray(o["lo"], o["hi"]), ["height"] = o["height"], ["spring"] = o["spring"] })) };
        var (spaces, doors) = Parse(specLike);
        var gw = Child(root, "Walls"); var gf = Child(root, "Floor"); var gc = Child(root, "Ceilings"); var go = Child(root, "Openings");
        var paperRooms = spaces.Where(sp => papered.Contains(sp.name)).ToList();
        Material wpMat = null, wsMat = null; float ws = 0f;
        if (Dress != null && paperRooms.Count > 0)
        {
            var w = Dress["walls"]; wpMat = w["wallpaper_texture"] != null ? Wallpaper(w) : DressMat(w["wallpaper"]); wsMat = DressMat(w["wainscot"]); ws = (float)w["wainscot_m"];
        }
        // each room's wall finish: (upper material, wainscot height). Papered rooms (foyer.json walls.spaces) take the foyer paper over a
        // wainscot (wainscot_by_space overrides the house height: the vestibule's low baseboard, the stair well's none); painted rooms
        // come from spec/dressing/finishes.json (the dining room's red over a white wainscot); the kitchen and breakfast area are cream
        // paper with no wainscot; anything else is the plain grey-box wall (upper null). Height 0: the upper finish to the floor, no trim.
        var byRoom = Dress?["walls"]?["wainscot_by_space"] as JObject;
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/finishes.json"));
        var painted = File.Exists(fp) ? (JObject)JObject.Parse(File.ReadAllText(fp))["rooms"] : new JObject();
        var finishOf = new Dictionary<string, (Material upper, float h)>();
        foreach (var sp in spaces)
        {
            if (paperRooms.Contains(sp)) finishOf[sp.name] = (wpMat, byRoom?[sp.name] != null ? (float)byRoom[sp.name] : ws);
            else if (painted[sp.name] is JObject pr) finishOf[sp.name] = (pr["paper"] != null ? PaperMat("Paper_" + sp.name, (string)pr["paper"], DressMat(pr["upper"]).color)   // papered (the living room: SpecGreybox.Living.cs)
                                                                                              : DressMat(pr["upper"], "Paint_" + sp.name), (float)pr["wainscot_m"]);
            else if (KitchenRooms.Contains(sp.name)) finishOf[sp.name] = (KitchenPaper(), 0f);
        }
        if (wsMat == null) wsMat = Mat("Wainscot_White", new Color(0.85f, 0.85f, 0.85f));
        (Material upper, float h) Plain = (null, 0f);
        (Material upper, float h) Fin(float x, float zSpec)
        {
            var r = spaces.FirstOrDefault(q => finishOf.ContainsKey(q.name) && Inside(q.pts, new Vector2(x, -zSpec)));
            return r != null ? finishOf[r.name] : Plain;
        }
        // trim (film 3225, 10248; Marina 228): a baseboard 0.14 m tall 1.2 cm proud and, over a full wainscot, a cap rail 3 cm proud, laid
        // along each finished room's outline (its polygon is the walls' room faces) wherever a wall stands behind it at the trim's height,
        // so it runs on unbroken across every wall box and end-on stretch (user note Oct 16 11:13: a gap where per-box trim stopped short)
        bool WallAt(float x, float z, float y) => st["walls"].Any(w => (float)w["x"][0] <= x && x <= (float)w["x"][1] && (float)w["z"][0] <= z
                                                                   && z <= (float)w["z"][1] && (float)w["y"][0] <= y && y <= (float)w["y"][1]);
        foreach (var rm in st["rooms"])
        {
            if (!finishOf.TryGetValue((string)rm["name"], out var rf) || rf.h <= 0f) continue;   // no wainscot: no trim (stair well, kitchen)
            var p = rm["poly"].Select(q => new Vector2((float)q[0], (float)q[1])).ToList(); int n = p.Count;
            float area = 0f; for (int i = 0; i < n; i++) area += p[i].x * p[(i + 1) % n].y - p[(i + 1) % n].x * p[i].y;
            float sg = Mathf.Sign(area);
            Vector2 Dir(int i) => (p[(i + 1) % n] - p[i]).normalized;
            float Turn(int i) { var a = Dir((i - 1 + n) % n); var b = Dir(i); return sg * (a.x * b.y - a.y * b.x); }   // at vertex i: > 0 convex
            for (int i = 0; i < n; i++)
            {
                Vector2 a = p[i], t = Dir(i), nOut = new Vector2(sg * t.y, -sg * t.x); float L = Vector2.Distance(a, p[(i + 1) % n]);
                if (L < 1e-4f) continue;
                if (Mathf.Abs(t.x) > 1e-4f && Mathf.Abs(t.y) > 1e-4f) { Debug.LogWarning($"Trim: {(string)rm["name"]} edge {i} not axis-aligned"); continue; }
                float turn = Turn(i);
                void Lay(float ya, float yb, float d)
                {   // corners: a convex corner starts this run past the previous run's depth, a reflex one reaches back to close the wrap
                    float s0 = turn > 1e-3f ? d : turn < -1e-3f ? -d : 0f; const float st1 = 0.01f;
                    bool Wall(float s) { s = Mathf.Clamp(s, 0.005f, L - 0.005f); var q = a + t * s + nOut * 0.004f; return WallAt(q.x, q.y, (ya + yb) / 2); }
                    void Add(float u0, float u1)
                    {
                        if (u1 - u0 < 0.02f) return;
                        Vector2 c0 = a + t * u0, c1 = a + t * u1 - nOut * d;   // from the face into the room
                        TrimRuns.Add((new Vector3(Mathf.Min(c0.x, c1.x), ya + FloorY, -Mathf.Max(c0.y, c1.y)),
                                      new Vector3(Mathf.Max(c0.x, c1.x), yb + FloorY, -Mathf.Min(c0.y, c1.y)), wsMat));
                    }
                    float r0 = s0; bool on = Wall(s0);
                    for (float s = s0 + st1; s < L; s += st1) { bool w = Wall(s); if (w != on) { if (on) Add(r0, s); r0 = s; on = w; } }
                    if (on) Add(r0, L);
                }
                Lay(0f, painted[(string)rm["name"]]?["baseboard_m"] is JToken bb ? (float)bb : 0.14f, 0.012f);   // 1 cm shallower than the stair's skirt board, which it meets (finishes.json baseboard_m: the hall's 0.11, film 10819)
                if (rf.h > 0.3f) Lay(rf.h - 0.01f, rf.h + 0.03f, 0.03f);
            }
        }
        void Piece(float x0, float x1, float z0, float z1, float y0, float y1, (Material upper, float h) fin)
        {   // spec z -> world -z; the finish's wainscot below its height, its upper material above
            if (fin.upper == null) { Box(gw, "Wall", x0, x1, -z1, -z0, y0, y1, mWall); return; }
            if (fin.h <= 0f) Box(gw, "Wall", x0, x1, -z1, -z0, y0, y1, fin.upper);
            else if (y0 < fin.h && y1 > fin.h) { Box(gw, "Wall", x0, x1, -z1, -z0, y0, fin.h, wsMat); Box(gw, "Wall", x0, x1, -z1, -z0, fin.h, y1, fin.upper); }
            else Box(gw, "Wall", x0, x1, -z1, -z0, y0, y1, y1 <= fin.h ? wsMat : fin.upper);
        }
        foreach (var b in st["walls"])
        {
            float x0 = (float)b["x"][0], x1 = (float)b["x"][1], z0 = (float)b["z"][0], z1 = (float)b["z"][1], y0 = (float)b["y"][0], y1 = (float)b["y"][1];
            float ym = (y0 + y1) / 2; const float e = 0.02f;
            // which faces border a papered room: split a thin wall down its middle so each side takes its own room's finish
            bool thinX = x1 - x0 <= 0.16f, thinZ = z1 - z0 <= 0.16f;
            float mx = (x0 + x1) / 2, mz = (z0 + z1) / 2;
            // along its length, a thin wall is cut where its sides' rooms change: the stretch running into another wall's
            // thickness borders no room, and papering it showed a paper strip on the next room's face (user note Oct 16 08:11)
            void Runs(float t0, float t1, System.Func<float, ((Material, float), (Material, float))> sides, System.Action<float, float, (Material, float), (Material, float)> piece)
            {
                const float step = 0.01f; float r0 = t0; var cur = sides(t0 + step / 2);
                for (float t = t0 + step; t < t1 - step / 2; t += step)
                {
                    var nx = sides(t + step / 2);
                    if (nx != cur) { piece(r0, t, cur.Item1, cur.Item2); r0 = t; cur = nx; }
                }
                piece(r0, t1, cur.Item1, cur.Item2);
            }
            // a stretch whose long faces border no room (it runs into the next wall's thickness) may still show its end to a room: it
            // takes that room's finish (user note Oct 16 10:48: a plain white strip in the dining room)
            (Material, float) EndFinish((Material, float) f, Vector2 endA, Vector2 endB)
            {
                if (f.Item1 != null) return f;
                var a = Fin(endA.x, endA.y); return a.Item1 != null ? a : Fin(endB.x, endB.y);
            }
            // a stub thin both ways (a pier between an opening and a corner) is split like the thin wall it belongs to: down the
            // thickness whose two faces border rooms. As one "thick piece" it took the hall's teal on Buzz's room face above the door
            // casing (walk note 2026-10-17 20:38)
            if (thinX && thinZ)
            {
                bool zRooms = Fin(mx, z0 - e).upper != null || Fin(mx, z1 + e).upper != null, xRooms = Fin(x0 - e, mz).upper != null || Fin(x1 + e, mz).upper != null;
                if (zRooms && !xRooms) thinX = false; else if (xRooms && !zRooms) thinZ = false;
            }
            if (thinX && !thinZ)
                Runs(z0, z1, z => (Fin(x0 - e, z), Fin(x1 + e, z)), (za, zb, a, c) =>
                {
                    if (a.Item1 == null && c.Item1 == null) { Piece(x0, x1, za, zb, y0, y1, EndFinish(a, new Vector2(mx, za - e), new Vector2(mx, zb + e))); return; }
                    if (a == c) Piece(x0, x1, za, zb, y0, y1, a); else { Piece(x0, mx, za, zb, y0, y1, a); Piece(mx, x1, za, zb, y0, y1, c); }
                });
            else if (thinZ && !thinX)
                Runs(x0, x1, x => (Fin(x, z0 - e), Fin(x, z1 + e)), (xa, xb, a, c) =>
                {
                    if (a.Item1 == null && c.Item1 == null) { Piece(xa, xb, z0, z1, y0, y1, EndFinish(a, new Vector2(xa - e, mz), new Vector2(xb + e, mz))); return; }
                    if (a == c) Piece(xa, xb, z0, z1, y0, y1, a); else { Piece(xa, xb, z0, mz, y0, y1, a); Piece(xa, xb, mz, z1, y0, y1, c); }
                });
            else
            {   // a thick piece (a pier, a wall end): the finish beside it with the tallest wainscot, plain if none
                var f = new[] { Fin(x0 - e, mz), Fin(x1 + e, mz), Fin(mx, z0 - e), Fin(mx, z1 + e) }.Where(q => q.upper != null).ToList();
                Piece(x0, x1, z0, z1, y0, y1, f.Count > 0 ? f.OrderByDescending(q => q.h).First() : Plain);
            }
        }
        foreach (var b in st["floor"])   // the plate, one piece per room carrying its finish (halls carpeted), walls' cells plain
            Box(gf, b["room"] != null && b["room"].Type != JTokenType.Null ? "Floor_" + (string)b["room"] : "FloorPlate", (float)b["x"][0], (float)b["x"][1],
                -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0], (float)b["y"][1],
                b["room"] != null && b["room"].Type != JTokenType.Null && KitchenRooms.Contains((string)b["room"]) ? Mat("Tile_Quarry", new Color(0.50f, 0.24f, 0.14f))
                : (string)b["finish"] == "hall" && carpetHalls ? mHall : mFloor);   // the ground halls (foyer, passage) are wood
        Box3(gc, "Ceiling", st["ceilings"], mCeil);
        foreach (var o in st["openings"])
        {
            string kind = (string)o["kind"]; bool alongX = (string)o["axis"] == "z";
            float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"];
            float wc = alongX ? -c : c, s0 = alongX ? lo : -hi, s1 = alongX ? hi : -lo;
            const float h = 0.07f;
            if (kind == "door" || (kind == "arch" && o["cased"] != null && (bool)o["cased"]))   // a cased opening is trimmed like a door
                foreach (float side in new[] { -1f, 1f })
                {
                    float head = (float)o["height"], f0 = wc + side * h, f1 = f0 + side * CasingProud;
                    Trim(go, alongX, f0, f1, s0 - CasingW, s0, 0f, head + CasingW);
                    Trim(go, alongX, f0, f1, s1, s1 + CasingW, 0f, head + CasingW);
                    Trim(go, alongX, f0, f1, s0 - CasingW, s1 + CasingW, head, head + CasingW);
                }
            else if (kind == "arch" && o["spring"] != null && o["spring"].Type != JTokenType.Null)
            {   // segmental top (stepped slices) and casing legs on both faces
                float spring = (float)o["spring"], crown = (float)o["height"];
                ArchTop(go, alongX, wc - h, wc + h, 1f, s0, s1, spring, crown, crown);
                if (ArchModel(go, o, (x, z) => Fin(x, z).upper ?? mWall) != null)   // SpecGreybox.Arch.cs: the generated arch; slices stay as colliders
                {
                    foreach (Transform t in go.transform) if (t.name == "Arch_Spandrel") t.GetComponent<MeshRenderer>().enabled = false;
                    continue;
                }
                float f0 = wc - h, f1 = f0 - CasingProud;
                Trim(go, alongX, f0, f1, s0 - CasingW, s0, 0f, spring); Trim(go, alongX, f0, f1, s1, s1 + CasingW, 0f, spring);
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
                bool model = o["model"] != null;   // a generated door (BackDoor.glb): leaf, jambs and glass are the model's; casing only here
                var glassBox = go.transform.GetChild(go.transform.childCount - 1).gameObject;
                if (model) { glassBox.name = "DoorStop_" + (string)o["model"]; glassBox.GetComponent<MeshRenderer>().enabled = false; }   // its collider keeps the door shut
                if (o["bare"] != null) continue;   // the frame belongs to a model (the door's sidelights): glass only
                float ow = (float)o["faces"][0] * (alongX ? -1f : 1f), f0 = wc - ow * h, f1 = f0 - ow * CasingProud;
                Trim(go, alongX, f0, f1, s0 - CasingW, s0, sill, whead + CasingW);
                Trim(go, alongX, f0, f1, s1, s1 + CasingW, sill, whead + CasingW);
                Trim(go, alongX, f0, f1, s0 - CasingW, s1 + CasingW, whead, whead + CasingW);
                if (!model) Trim(go, alongX, f0, f0 - ow * StoolProud, s0 - CasingW - 0.025f, s1 + CasingW + 0.025f, sill - StoolT, sill);
            }
        }
        foreach (var d in doors.Where(d => d.kind == "rail")) Rail(go, d);
        return (spaces, doors);
    }

    // PEEK (Oct 15): from eye points in every room you can walk in, rays in all directions; a ray whose first hit lies inside a
    // space you cannot walk into (closed closets, the space under the landing, behind prop doors) looked through a gap.
    static string Peek(List<Space> up, List<Space> ground, float gy, HashSet<string> walkIn)
    {
        var lines = new List<string>(); int n = 0, bad = 0;
        var closed = up.Select(s => (s, 0f)).Concat(ground.Select(s => (s, gy))).Where(t => !walkIn.Contains(t.s.name) && t.s.kind != "opening").ToList();
        var dirs = new List<Vector3>();
        for (int a = -60; a <= 60; a += 20) for (int k = 0; k < 24; k++) dirs.Add(Quaternion.Euler(a, k * 15f, 0) * Vector3.forward);
        foreach (var (spaces, y0) in new[] { (up, 0f), (ground, gy) })
            foreach (var s in spaces.Where(s => walkIn.Contains(s.name)))
            {
                float x0 = s.pts.Min(p => p.x), x1 = s.pts.Max(p => p.x), z0 = s.pts.Min(p => p.y), z1 = s.pts.Max(p => p.y);
                for (float x = x0 + 0.2f; x < x1; x += 0.4f)
                    for (float z = z0 + 0.2f; z < z1; z += 0.4f)
                        foreach (float eh in new[] { 0.6f, 1.6f })
                        {
                            if (!Inside(s.pts, new Vector2(x, z))) continue;
                            var eye = new Vector3(x, y0 + eh, z);
                            if (Physics.CheckSphere(eye, 0.05f)) continue;   // inside furniture or a step
                            foreach (var d in dirs)
                            {
                                n++;
                                if (!Physics.Raycast(eye, d, out var hit, 30f)) continue;
                                var q = hit.point + d * 0.03f;
                                var c = closed.FirstOrDefault(t => q.y > t.Item2 + 0.01f && q.y < t.Item2 + t.s.ceil - 0.01f && Inside(t.s.pts, new Vector2(q.x, q.z)));
                                if (c.s == null) continue;
                                // the ray stopped on a surface inside a closed space: it passed a gap in that space's walls
                                bad++;
                                if (bad <= 40) lines.Add($"PEEK    from {s.name} ({x:F2}, {y0 + eh:F2}, {-z:F2}) into {c.s.name} at ({q.x:F2}, {q.y:F2}, {-q.z:F2}) on {hit.collider.name}");
                            }
                        }
            }
        lines.Insert(0, $"Peek check: {n} rays from rooms you can walk in, {bad} into closed spaces");
        return string.Join("\n", lines) + "\n";
    }

    // ceiling boxes minus rectangular openings ({x, z}): each box a hole overlaps is replaced by the pieces around the hole
    static JArray CutHoles(JArray boxes, JArray holes)
    {
        var cur = boxes.Cast<JObject>().ToList();
        foreach (var h in holes)
        {
            float hx0 = (float)h["x"][0], hx1 = (float)h["x"][1], hz0 = (float)h["z"][0], hz1 = (float)h["z"][1];
            var next = new List<JObject>();
            foreach (var b in cur)
            {
                float x0 = (float)b["x"][0], x1 = (float)b["x"][1], z0 = (float)b["z"][0], z1 = (float)b["z"][1];
                if (hx0 >= x1 || hx1 <= x0 || hz0 >= z1 || hz1 <= z0) { next.Add(b); continue; }
                JObject Piece(float a0, float a1, float c0, float c1) { var q = (JObject)b.DeepClone(); q["x"] = new JArray(a0, a1); q["z"] = new JArray(c0, c1); return q; }
                if (hx0 > x0) next.Add(Piece(x0, hx0, z0, z1));
                if (hx1 < x1) next.Add(Piece(hx1, x1, z0, z1));
                float mx0 = Mathf.Max(x0, hx0), mx1 = Mathf.Min(x1, hx1);
                if (hz0 > z0) next.Add(Piece(mx0, mx1, z0, hz0));
                if (hz1 < z1) next.Add(Piece(mx0, mx1, hz1, z1));
            }
            cur = next;
        }
        return new JArray(cur);
    }

    static void Box3(GameObject p, string n, JToken boxes, Material m)
    {   // geometry boxes in spec coordinates (x, z, y) -> world (z flips)
        foreach (var b in boxes)
            Box(p, n, (float)b["x"][0], (float)b["x"][1], -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0], (float)b["y"][1], m);
    }

    // spec/dressing/foyer.json (tools/house/foyer_dressing.py): finishes and pieces measured from Marina's frames. Finishes
    // (wainscot, wallpaper, stair colours) are applied while building; pieces are added after the gates, like furniture.
    static JObject Dress;
    static Material DressMat(JToken c, string name = null)
    {
        var col = new Color((float)c[0], (float)c[1], (float)c[2]);
        return Mat(name ?? $"Dress_{ColorUtility.ToHtmlStringRGB(col)}", col);
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
    // The foyer's main stair as a detailed model (tools/house/hifi_foyer.py, Blender, from the same spec boxes). The grey-box stair
    // stays as the walking/collision layer: its step, landing and rail renderers are switched off, their colliders kept, so every
    // walk gate is unchanged. Materials are remapped by name to project materials (the spandrel takes the foyer wallpaper).
    // A textured HDRP/Lit material (Poly Haven, CC0; Assets/Textures/PolyHaven/<id>/albedo|normal.jpg) projected TRIPLANAR in world
    // space at "tile" metres per repeat, so neither the generated meshes nor the grey-box boxes need UVs. Tint multiplies the albedo.
    static Material TexMat(string n, string id, Color tint, float tile, float smooth)
    {
        string dir = $"Assets/Textures/PolyHaven/{id}";
        var nrmPath = dir + "/normal.jpg"; var ti = AssetImporter.GetAtPath(nrmPath) as TextureImporter;
        if (ti != null && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; ti.SaveAndReimport(); }
        var m = Mat(n, tint);
        m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dir + "/albedo.jpg"));
        m.SetTexture("_NormalMap", AssetDatabase.LoadAssetAtPath<Texture2D>(nrmPath)); m.SetFloat("_NormalScale", 1f);
        m.SetFloat("_UVBase", 5f); m.SetFloat("_TexWorldScale", 1f / tile); m.SetFloat("_Smoothness", smooth);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m);
        EditorUtility.SetDirty(m); return m;
    }

    // The foyer's fixtures (tools/house/hifi_lights.py) placed from the stills, each with a warm light that stays on (the film's
    // foyer has them lit in daytime): the brass cage lantern on a chain in the vestibule on the front door's axis (sled POV
    // 3220-3229, landing 25), two-arm sconces on the vestibule's front wall either side of the door's sidelights (776-784; the
    // foyer wall beside the inner opening carries only the prints, 3223) and either side of
    // the oval mirror (Marina 1070.5 s). Spec metres above the ground floor; Unity z = -spec z.
    // A generated model (Assets/Models/Foyer/<asset>.glb, spec coordinates above the ground floor) under the ground floor's height;
    // its colliders stripped (the grey-box keeps the walking), materials remapped by name prefix
    static GameObject PlaceHiFi(GameObject root, float gy, string asset, Dictionary<string, Material> remap)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Models/Foyer/{asset}.glb");
        if (a == null) { Debug.LogWarning("PlaceHiFi: missing " + asset); return null; }
        var g = (GameObject)Object.Instantiate(a, root.transform); g.name = asset + "_HiFi"; g.transform.localPosition = new Vector3(0, gy, 0);
        foreach (var c in g.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        if (remap != null)
            foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
                foreach (var kv in remap) if (r.sharedMaterial != null && r.sharedMaterial.name.StartsWith(kv.Key)) r.sharedMaterial = kv.Value;
        return g;
    }

    // a material showing an image from the repo (spec/...), on the mesh's own UVs
    // rooms with the dark hardwood floor: the foyer's (Marina 312 s) and any painted room whose finishes.json entry says "floor": "wood"
    static HashSet<string> WoodFloors()
    {
        var set = new HashSet<string> { "foyer", "vestibule", "rear_passage" };
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/finishes.json"));
        if (File.Exists(fp))
            foreach (var kv in (JObject)JObject.Parse(File.ReadAllText(fp))["rooms"])
                if ((string)kv.Value["floor"] == "wood") set.Add(kv.Key);
        return set;
    }

    static Material SpecTexMat(string name, string specPath)
    {
        string src = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../" + specPath));
        Directory.CreateDirectory("Assets/Textures/Greybox"); string dst = $"Assets/Textures/Greybox/{Path.GetFileName(specPath)}";
        File.Copy(src, dst, true); AssetDatabase.ImportAsset(dst);
        var m = Mat(name, Color.white); m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dst)); m.SetFloat("_Smoothness", 0.15f);
        HDMaterial.ValidateMaterial(m); return m;
    }

    static Material FoilMat()
    {   // the poinsettias' gold foil: brighter and glossier than brass (film 3225, 10248)
        var m = Mat("HiFi_Foil", new Color(0.92f, 0.76f, 0.38f)); m.SetFloat("_Metallic", 0.75f); m.SetFloat("_Smoothness", 0.7f); return m;
    }

    static Material BrassMat()
    {
        // part metallic: full metal only shows its surroundings, and the vestibule is dim, so the film's gold (lamp-lit) read black
        var m = Mat("HiFi_Brass", new Color(0.80f, 0.60f, 0.28f)); m.SetFloat("_Metallic", 0.65f); m.SetFloat("_Smoothness", 0.55f); return m;
    }

    static void HiFiLights(GameObject root, float gy)
    {
        var g = Child(root, "FoyerFixtures");
        var brass = BrassMat();
        var candle = Mat("HiFi_Candle", new Color(0.95f, 0.94f, 0.9f)); candle.SetFloat("_Smoothness", 0.35f);
        var bulb = Mat("HiFi_Bulb", new Color(1f, 0.9f, 0.7f));
        var shade = Mat("HiFi_Shade", new Color(0.95f, 0.92f, 0.86f)); shade.SetFloat("_Smoothness", 0.8f);   // lit glass chimney / opal bowl
        shade.SetColor("_EmissiveColor", new Color(1f, 0.8f, 0.55f) * 300f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(shade);
        bulb.SetColor("_EmissiveColor", new Color(1f, 0.72f, 0.42f) * 2000f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(bulb);
        void Place(string asset, Vector3 specPos, float yRot, float lumens, Vector3 lightOffset)
        {
            var a = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Models/Foyer/{asset}.glb");
            if (a == null) { Debug.LogWarning("HiFiLights: missing " + asset); return; }
            var go = (GameObject)Object.Instantiate(a, g.transform); go.name = asset;
            go.transform.position = new Vector3(specPos.x, specPos.y + gy, -specPos.z); go.transform.rotation = Quaternion.Euler(0, yRot, 0);
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>())
            {
                string n = r.sharedMaterial != null ? r.sharedMaterial.name : "";
                if (n.StartsWith("Light_Glass")) { r.enabled = false; continue; }   // clear glass: the cage reads without it
                r.sharedMaterial = n.StartsWith("Light_Brass") ? brass : n.StartsWith("Light_Candle") ? candle : n.StartsWith("Light_Bulb") ? bulb : n.StartsWith("Light_Shade") ? shade : r.sharedMaterial;
                r.shadowCastingMode = ShadowCastingMode.Off;
                foreach (var c in r.GetComponents<Collider>()) Object.DestroyImmediate(c);
            }
            var rs = go.GetComponentsInChildren<MeshRenderer>().Where(r => r.enabled).ToArray();
            Debug.Log($"HiFiLights {asset} at {go.transform.position}: {rs.Length} renderers" + (rs.Length > 0 ? $", bounds {rs.Aggregate(rs[0].bounds, (b, r) => { b.Encapsulate(r.bounds); return b; })}" : ""));
            var l = new GameObject(asset + "_Light").AddComponent<Light>(); l.transform.parent = go.transform;
            l.transform.localPosition = lightOffset; l.type = LightType.Point; l.range = 7f;
            l.gameObject.AddComponent<HDAdditionalLightData>();
            l.lightUnit = LightUnit.Lumen; l.intensity = lumens; l.useColorTemperature = true; l.colorTemperature = 2700f; l.shadows = LightShadows.Soft;
        }
        // in the foyer just inside the vestibule opening (x 8.948), on the opening's centre line; film 3225 (chain above the
        // opening head) and the 1616 ray from outside the door; hangs from the 2.82 m foyer ceiling to a 1.85 m bottom
        Place("Lantern", new Vector3(8.50f, 2.82f, 9.62f), 0f, 700f, new Vector3(0, -0.8f, 0));
        foreach (float z in new[] { 8.56f, 10.99f }) Place("Sconce", new Vector3(10.13f, 1.57f, z), 180f, 350f, new Vector3(0.15f, 0.25f, 0));   // the vestibule's front wall beside the door surround: back-projected on film 10248 (tools/house/film_solve_10248.py)
        foreach (float x in new[] { 5.15f, 6.18f }) Place("Hurricane", new Vector3(x, 1.62f, 7.778f), 90f, 250f, new Vector3(0.13f, 0.12f, 0));   // glass-chimney pair beside the tall mirror (film 1616, 1689, 10673)
        Place("Dome", new Vector3(2.21f, 2.155f, 9.54f), 0f, 400f, new Vector3(0, -0.15f, 0));   // 600 -> 400 lm Oct 18 (user: "slightly dim the flush mount under the arch on the first floor"); opal ceiling light centred in the rear passage behind the arch (film 21, 10673, IMG_3843)
        Place("Dome", new Vector3(2.28f, 3.026f + 2.4f, 9.60f), 0f, 600f, new Vector3(0, -0.15f, 0));   // ASSUMED (user Oct 17, not in the film): a second opal flush mount on the stair well's ceiling (upstairs main_stair_opening ceil 2.4) over the half landing's centre (x 1.58-2.985, on the landing window's axis); DEVIATIONS 79
    }

    static void HiFiStair(GameObject root, float gy)
    {
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/MainStair.glb");
        if (asset == null) { Debug.LogWarning("HiFiStair: Assets/Models/Foyer/MainStair.glb not imported"); return; }
        var go = (GameObject)Object.Instantiate(asset, root.transform); go.name = "MainStair_HiFi";
        go.transform.localPosition = Vector3.zero; go.transform.localRotation = Quaternion.identity;
        var wood = TexMat("HiFi_Wood", "wood_floor", new Color(0.62f, 0.5f, 0.46f), 1.6f, 0.25f);
        // stair runner: film 1616/10673's deep crimson-burgundy carpet (user Oct 18 "Fix the stair runner too"). Plain colour: the Poly
        // Haven dirty_carpet photo it used is ~3.5% reflectance, so any tint on it rendered near-black
        var runnerM = Mat("HiFi_Runner", new Color(0.30f, 0.028f, 0.062f)); runnerM.SetFloat("_Smoothness", 0.08f);
        {   // carpet pile and weave (user Oct 18: "a carpet like texture"): the dirty_carpet photo as a brightness-neutral detail map
            // (detail_neutral.png: its luminance normalised to mean 0.81, 35% contrast) plus its normal map, so the crimson stays crimson
            const string cd = "Assets/Textures/PolyHaven/dirty_carpet/";
            runnerM.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(cd + "detail_neutral.png")); runnerM.SetTextureScale("_BaseColorMap", new Vector2(2f, 2f));
            var rn = AssetDatabase.LoadAssetAtPath<Texture2D>(cd + "normal.jpg");
            if (rn != null) { runnerM.SetTexture("_NormalMap", rn); runnerM.SetFloat("_NormalScale", 0.6f); runnerM.EnableKeyword("_NORMALMAP"); }
        }
        var tex = new Dictionary<string, Material> { ["Stair_TreadWood"] = wood, ["Stair_RailWood"] = wood, ["Stair_Runner"] = runnerM };
        var cols = new Dictionary<string, Color> { ["Stair_White"] = new Color(0.86f, 0.86f, 0.84f) };
        foreach (var r in go.GetComponentsInChildren<MeshRenderer>())
        {
            var mats = r.sharedMaterials;
            for (int i = 0; i < mats.Length; i++)
            {
                string n = mats[i] != null ? mats[i].name.Split(' ')[0] : "";
                if (n.StartsWith("Stair_Spandrel")) mats[i] = Dress != null ? Wallpaper(Dress["walls"]) : mWall;
                else if (tex.Keys.FirstOrDefault(k => n.StartsWith(k)) is string tk) mats[i] = tex[tk];
                else foreach (var kv in cols) if (n.StartsWith(kv.Key)) { var w = Mat("HiFi_" + kv.Key, kv.Value); w.SetFloat("_Smoothness", 0.55f); mats[i] = w; }
            }
            r.sharedMaterials = mats; r.gameObject.isStatic = true;
            foreach (var c in r.GetComponents<Collider>()) Object.DestroyImmediate(c);   // the grey-box carries collision
        }
        {   // the volute at the foot of flight 1 (hifi_foyer.py, changes/2026-10-18-stair-volute.json) stands proud of the grey-box: its ring
            // of balusters is solid to the rail and the first step's round end is a step, so nobody walks through them
            var rj = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/main_stair_rails.json"))));
            var ft = rj["newels"].First(q => (string)q["name"] == "foot"); float vx = (float)ft["x"], vz = (float)ft["z"], vy0 = (float)ft["y0"], vy1 = (float)ft["y1"];
            var vc = new GameObject("VoluteCollider"); vc.transform.SetParent(go.transform, false); vc.isStatic = true;
            vc.transform.position = new Vector3(vx, (gy + vy1) / 2, -vz); vc.AddComponent<BoxCollider>().size = new Vector3(0.34f, vy1 - gy, 0.34f);
            var bn = new GameObject("VoluteStepCollider"); bn.transform.SetParent(go.transform, false); bn.isStatic = true;
            bn.transform.position = new Vector3(vx + 0.026f, (gy + vy0) / 2, -(vz - 0.02f)); bn.AddComponent<BoxCollider>().size = new Vector3(0.35f, vy0 - gy, 0.36f);   // spec x 6.23-6.58, z 9.87-10.23
        }
        if (TrimFromFaces)   // the stair wall's skirt, raking panel and rail now come from the face model (SpecGreybox.Trim.cs)
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>().Where(r => r.name.StartsWith("StairWallTrim")).ToList()) Object.DestroyImmediate(r.gameObject);
        var gb = root.transform.Find("MainStair");
        Bounds Bo(Transform t, System.Func<MeshRenderer, bool> f) { var rs = t.GetComponentsInChildren<MeshRenderer>().Where(f).ToArray(); var b = rs[0].bounds; foreach (var q in rs) b.Encapsulate(q.bounds); return b; }
        if (gb != null)
            Debug.Log($"HiFiStair bounds: model {Bo(go.transform, r => true)} | grey-box {Bo(gb, r => r.name.StartsWith("flight"))}");
        // hide the grey-box stair and the foyer dressing's stair pieces (runner, handrail, newels), wherever they were built
        // the foyer's floors: the same dark wood (Marina's foyer and passage are dark hardwood)
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (r.name.StartsWith("Floor_") && WoodFloors().Contains(r.name.Substring(6))) r.sharedMaterial = wood;
        // the potted tree (tools/house/hifi_props.py, Poly Haven), on the ground floor; its dressing boxes are hidden
        PlaceHiFi(root, gy, "Tree", null);
        PlaceHiFi(root, gy, "LandingWindow", new Dictionary<string, Material> {   // tools/house/hifi_landing_window.py (film 11966, 12133)
            ["LW_Brass"] = BrassMat(), ["LW_Glass"] = mGlass, ["LW_Paper"] = Dress != null ? Wallpaper(Dress["walls"]) : mWall });
        PlaceHiFi(root, gy, "FrontDoor", new Dictionary<string, Material> { ["Door_Brass"] = BrassMat() });   // tools/house/hifi_door.py (film 10248)
        {   // tools/house/hifi_back_door.py (film 6902; changes/2026-10-16-kitchen-wing.json): the kitchen's back door in its opening
            var sheer = Mat("HiFi_Sheer", new Color(0.93f, 0.92f, 0.88f, 0.45f));
            sheer.SetFloat("_SurfaceType", 1f); sheer.SetFloat("_DoubleSidedEnable", 1f); sheer.SetFloat("_Smoothness", 0.1f); HDMaterial.ValidateMaterial(sheer);
            PlaceHiFi(root, gy, "BackDoor", new Dictionary<string, Material> { ["BD_Brass"] = BrassMat(), ["BD_Glass"] = mGlass, ["BD_Sheer"] = sheer });
        }
        Curtains(root, gy);       // SpecGreybox.Curtains.cs: tools/house/hifi_sheers.py (DEVIATIONS 41)
        Living(root, gy);         // SpecGreybox.Living.cs: tools/house/hifi_living.py + hifi_living_props.py + spec/dressing/living.json (changes/2026-10-16-living-room.json)
        Dining(root, gy);         // SpecGreybox.Dining.cs: tools/house/hifi_dining_props.py + spec/dressing/dining.json (props lane, Oct 18)
        Den(root, gy);            // SpecGreybox.Den.cs: tools/house/hifi_den.py + hifi_den_props.py + spec/dressing/den.json (changes/2026-10-16-den.json)
        KitchenModel(root, gy);   // tools/house/hifi_kitchen.py + spec/dressing/kitchen.json (changes/2026-10-16-kitchen-cabinets.json)
        KitchenSconcesAndGallery(root, gy);   // SpecGreybox.KitchenLights.cs: wall sconces, picture gallery, desk
        KitchenProps(root, gy);   // SpecGreybox.KitchenProps.cs: pot rack + pans, bar stools, counter dressing (hifi_kitchen_props.py; Oct 19)
        {   // tools/house/hifi_breakfast_table.py (changes/2026-10-16-breakfast-table.json): honey oak, Poly Haven oak_veneer_01 tinted to film 2528
            var t = PlaceHiFi(root, gy, "BreakfastTable", new Dictionary<string, Material> { ["BT_Wood"] = TexMat("HiFi_BreakfastOak", "oak_veneer_01", new Color(0.95f, 0.80f, 0.60f), 1.0f, 0.55f)   /* darker honey pine (user photo IMG_4306, Oct 19) */ });
            if (t != null) foreach (var r in t.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        }
        PlaceHiFi(root, gy, "FoyerDressing", new Dictionary<string, Material> {   // tools/house/hifi_dressing.py: stands, poinsettias, prints (film)
            ["Door_Brass"] = BrassMat(), ["Dress_Foil"] = FoilMat(),
            ["Print_Left"] = SpecTexMat("HiFi_PrintLeft", "spec/dressing/prints/print_left.png"),
            ["Print_Right"] = SpecTexMat("HiFi_PrintRight", "spec/dressing/prints/print_right.png") });
        FoyerProps(root, gy);   // SpecGreybox.FoyerProps.cs: tools/house/hifi_foyer_props.py (changes/2026-10-16-foyer-finish.json)
        string[] pre = { "flight1_", "flight2_", "landing", "newel", "tree_crown", "tree_trunk", "tree_pot", "bottom_step", "front_door", "sidelight_",
                         "flower_stand_", "flowers_", "print_" };
        int hidden = 0;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (!r.transform.IsChildOf(go.transform) && r.transform.parent != null && (r.transform.parent.name == "MainStair" || r.transform.parent.name == "Dressing")
                && pre.Any(p => r.name.StartsWith(p))) { r.enabled = false; hidden++; }
        Debug.Log($"HiFiStair: hid {hidden} grey-box/dressing stair renderers");
        // the gallery's grey-box rails (SpecGreybox.Rail: "Rail"/"Spindle" boxes): the model draws the gallery balustrade now
        // (hifi_foyer.py, main_stair_rails.json "covers"); their colliders stay for walking
        int gal = 0;
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>())
        {
            var c = r.bounds.center;
            if ((r.name == "Rail" || r.name == "Spindle") && r.transform.parent != null && r.transform.parent.name == "Rail"
                && c.x > 3.80f && c.x < 5.75f && c.z > -11.50f && c.z < -9.10f) { r.enabled = false; gal++; }
        }
        Debug.Log($"HiFiStair: hid {gal} grey-box gallery rail renderers");
    }

    // The kitchen's cabinets, counters, appliances, seats and island (KitchenCabinets.glb), with their walk-layer colliders: invisible
    // boxes from spec/dressing/kitchen.json "colliders" (the model itself carries none). Wood: Poly Haven cherry_veneer tinted to the
    // film's dark cherry by mean albedo (lin 0.747/0.433/0.230 -> film 6902 0.105/0.012/0.013); tile: generated maps on the model's UVs
    // (tools/house/kitchen_tile_tex.py; 1 UV = 8 tiles of 0.158 m), not triplanar, so the grid follows each counter's front edge.
    static void KitchenModel(GameObject root, float gy)
    {
        string T(string f) => "Assets/Textures/Kitchen/" + f;
        void Imp(string path, bool normal, bool srgb)
        {
            if (AssetImporter.GetAtPath(path) is TextureImporter ti && (ti.textureType == TextureImporterType.NormalMap) != normal | ti.sRGBTexture != srgb)
            { ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default; ti.sRGBTexture = srgb; ti.SaveAndReimport(); }
        }
        Imp(T("tile_normal.png"), true, false); Imp(T("tile_mask.png"), false, false); Imp(T("tile_albedo.png"), false, true);
        var tile = Mat("HiFi_KitchenTile", Color.white);
        tile.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(T("tile_albedo.png")));
        tile.SetTexture("_NormalMap", AssetDatabase.LoadAssetAtPath<Texture2D>(T("tile_normal.png"))); tile.SetFloat("_NormalScale", 1f);
        tile.SetTexture("_MaskMap", AssetDatabase.LoadAssetAtPath<Texture2D>(T("tile_mask.png")));
        tile.SetFloat("_UVBase", 0f); tile.SetFloat("_Metallic", 0f); tile.SetFloat("_SmoothnessRemapMin", 0f); tile.SetFloat("_SmoothnessRemapMax", 1f);
        tile.SetFloat("_AORemapMin", 0f); tile.SetFloat("_AORemapMax", 1f);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(tile); EditorUtility.SetDirty(tile);
        Material Solid(string n, Color c, float smooth, float metal = 0f) { var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", metal); return m; }
        var g = PlaceHiFi(root, gy, "KitchenCabinets", new Dictionary<string, Material> {
            ["KT_Wood"] = TexMat("HiFi_KitchenWood", "cherry_veneer", new Color(0.411f, 0.182f, 0.264f), 1.0f, 0.5f),
            ["KT_Tile"] = tile,
            ["KT_Edge"] = Solid("HiFi_KitchenEdge", new Color(0.16f, 0.38f, 0.59f), 0.85f),
            ["KT_Grout"] = Solid("HiFi_KitchenGrout", new Color(0.80f, 0.78f, 0.74f), 0.2f),
            ["KT_Brass"] = BrassMat(),
            ["KT_Black"] = Solid("HiFi_ApplianceBlack", new Color(0.03f, 0.03f, 0.03f), 0.8f),
            ["KT_Steel"] = Solid("HiFi_Steel", new Color(0.62f, 0.62f, 0.62f), 0.6f, 1f),
            ["KT_Sink"] = Solid("HiFi_SinkEnamel", new Color(0.92f, 0.91f, 0.88f), 0.8f),
            ["KT_Cushion"] = Solid("HiFi_SeatCushion", new Color(0.55f, 0.06f, 0.08f), 0.1f),
            ["KT_Pine"] = KnottyPine(),   // Oct 19: the stacked knotty-pine corner cupboard (film 2116, IMG_4305)
            ["KT_UVPine"] = KnottyPineUV(),   // Oct 19 walk note 14:47 ("looks weird"): the cupboard's grain laid by member (UVs), not triplanar
            ["KT_Dispenser"] = Solid("HiFi_ApplianceSmoke", new Color(0.10f, 0.10f, 0.11f), 0.9f),
            // Oct 19: the generated breakfast hutch (film 2104 = IMG_4305): painted white (the film's warm white, as the live preview), glass, dishes
            ["KT_Paint"] = Solid("HiFi_HutchPaint", new Color(0.80f, 0.79f, 0.74f), 0.45f),
            ["KT_Glass"] = mGlass,
            ["KT_DishRed"] = Solid("HiFi_DishRed", new Color(0.55f, 0.04f, 0.04f), 0.75f),
            ["KT_DishGreen"] = Solid("HiFi_DishGreen", new Color(0.06f, 0.25f, 0.12f), 0.75f),
            ["KT_DishDark"] = Solid("HiFi_DishDark", new Color(0.05f, 0.05f, 0.05f), 0.6f) });
        if (g != null) foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/kitchen.json"));
        if (!File.Exists(fp)) return;
        var col = new GameObject("KitchenColliders"); col.transform.SetParent(root.transform, false); int n = 0;
        foreach (var b in JObject.Parse(File.ReadAllText(fp))["colliders"])
        {
            float x0 = (float)b["x"][0], x1 = (float)b["x"][1], z0 = (float)b["z"][0], z1 = (float)b["z"][1], y0 = (float)b["y"][0], y1 = (float)b["y"][1];
            var c = new GameObject("KitchenCollider_" + (string)b["name"]); c.transform.SetParent(col.transform, false); c.isStatic = true;
            c.transform.position = new Vector3((x0 + x1) / 2, gy + (y0 + y1) / 2, -(z0 + z1) / 2);
            c.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, y1 - y0, z1 - z0); n++;
        }
        Debug.Log($"KitchenModel: {n} colliders");
        KitchenFixtures(root, gy, JObject.Parse(File.ReadAllText(fp)), g);
    }

    // The kitchen's night lights, each from a visible fixture (user, Oct 16: "add necessary light sources fixtures"): a rectangle light
    // under every under-cabinet strip (KitchenCabinets.glb's KT_UnderLight diffusers; film 9812, 10452, 6042, 10448) and the breakfast
    // chandelier (tools/house/hifi_kitchen_lights.py; Marina f197/f261). All join the night layer in Daylight() (off by day, DEVIATIONS 44),
    // and the room's generic ceiling lamps (Light_kitchen, Light_back_stair) are removed there: no light without a fixture.
    // Strengths: tools/house/film_light_match.py --night (film 6042/9812/10452 region ratios).
    public static float UnderCabLumensPerM = 700f, ChandelierLumens = 2000f;
    // knotty pine, honey-toned, satin (film 2116: the corner cupboard, bar stools and desk read a warm orange-honey)
    // the grain only (polyhaven_fetch.py --neutral: the scan's own orange has no blue to tint), coloured to the film's cupboard (film
    // island detail, sRGB 0.72/0.49/0.33 on the lit cupboard face -> tint sRGB 0.88/0.63/0.42 over the 0.8 grain)
    // the same pine on the model's own UVs (hifi_kitchen.py: 1 UV unit = 1 m, grain along each member: up the stiles and panels, along
    // the rails and mouldings); triplanar blended two projections on the cupboard's 39-degree front and smeared the grain (walk note
    // Oct 19 14:47). One repeat = 1.1 m: the scan is 0.74 m, its knots 3-4.5 cm; the film's knots read ~5-7 cm on the cupboard doors
    static Material KnottyPineUV()
    {
        var m = TexMat("HiFi_KnottyPineUV", "coated_pine", new Color(0.88f, 0.63f, 0.42f), 1.1f, 0.45f);
        var n = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Textures/PolyHaven/coated_pine/albedo_neutral.jpg");
        if (n) m.SetTexture("_BaseColorMap", n);
        m.SetFloat("_UVBase", 0f);
        foreach (var t in new[] { "_BaseColorMap", "_NormalMap" }) m.SetTextureScale(t, new Vector2(1f / 1.1f, 1f / 1.1f));
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); EditorUtility.SetDirty(m);
        return m;
    }

    static Material KnottyPine()
    {
        var m = TexMat("HiFi_KnottyPine", "coated_pine", new Color(0.88f, 0.63f, 0.42f), 1.2f, 0.45f);
        var n = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Textures/PolyHaven/coated_pine/albedo_neutral.jpg");
        if (n) { m.SetTexture("_BaseColorMap", n); EditorUtility.SetDirty(m); }
        return m;
    }

    static void KitchenFixtures(GameObject root, float gy, JObject k, GameObject cabinets)
    {
        var g = Child(root, "KitchenFixtures");
        var glowM = Mat("HiFi_UnderCabGlow", new Color(0.95f, 0.95f, 0.92f)); glowM.SetFloat("_Smoothness", 0.5f);
        glowM.SetColor("_EmissiveColor", new Color(1f, 0.97f, 0.92f) * 3000f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(glowM);
        if (cabinets != null)
            foreach (var r in cabinets.GetComponentsInChildren<MeshRenderer>())
                if (r.sharedMaterial != null && r.sharedMaterial.name.StartsWith("KT_UnderLight")) { r.sharedMaterial = glowM; r.shadowCastingMode = ShadowCastingMode.Off; }
        var ul = k["under_lights"]; var std = k["std"];
        if (ul != null)
        {
            float ub = (float)std["upper_bottom"], dt = (float)std["door_t"], inset = (float)ul["inset_front"], depth = (float)ul["depth"], gap = (float)ul["end_gap"];
            float y = gy + ub - (float)ul["housing_h"] - (float)ul["diffuser_h"] - 0.003f;
            foreach (var u in k["uppers"].Where(u => u["bottom"] == null))
            {
                float x0 = (float)u["x"][0], x1 = (float)u["x"][1], z0 = (float)u["z"][0], z1 = (float)u["z"][1]; string f = (string)u["front"];
                bool alongZ = f.EndsWith("x"); float sgn = f.StartsWith("+") ? 1f : -1f;
                float F = alongZ ? (sgn > 0 ? x1 : x0) : (sgn > 0 ? z1 : z0), dc = F - sgn * (dt + inset + depth / 2);
                float a0 = (alongZ ? z0 : x0) + gap, a1 = (alongZ ? z1 : x1) - gap, len = a1 - a0, ac = (a0 + a1) / 2;
                var l = new GameObject("UnderCab_" + (string)u["name"]).AddComponent<Light>(); l.transform.SetParent(g.transform, false);
                l.transform.position = alongZ ? new Vector3(dc, y, -ac) : new Vector3(ac, y, -dc);
                l.transform.rotation = Quaternion.LookRotation(Vector3.down, alongZ ? Vector3.forward : Vector3.right);
                l.gameObject.AddComponent<HDAdditionalLightData>();
                l.type = LightType.Rectangle; l.areaSize = new Vector2(0.04f, len - 0.02f);
                l.lightUnit = LightUnit.Lumen; l.intensity = (ul["lumens_per_m"] != null ? (float)ul["lumens_per_m"] : UnderCabLumensPerM) * len; l.useColorTemperature = true; l.colorTemperature = (float)ul["kelvin"];
                l.shadows = LightShadows.Soft; l.range = 5f;
            }
        }
        var c = k["chandelier"];
        if (c != null)
        {
            var a = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/KitchenChandelier.glb");
            if (a == null) { Debug.LogWarning("KitchenFixtures: missing KitchenChandelier.glb"); return; }
            var brass = BrassMat();
            var shade = Mat("HiFi_Shade", new Color(0.95f, 0.92f, 0.86f)); shade.SetFloat("_Smoothness", 0.8f);
            shade.SetColor("_EmissiveColor", new Color(1f, 0.8f, 0.55f) * 300f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(shade);
            var go = (GameObject)Object.Instantiate(a, g.transform); go.name = "KitchenChandelier";
            float cx = (float)c["x"], cz = (float)c["z"], ceil = (float)c["ceiling"];
            go.transform.position = new Vector3(cx, gy + ceil, -cz);
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>())
            {
                string n = r.sharedMaterial != null ? r.sharedMaterial.name : "";
                r.sharedMaterial = n.StartsWith("Light_Brass") ? brass : n.StartsWith("Light_Shade") ? shade : r.sharedMaterial;
                r.shadowCastingMode = ShadowCastingMode.Off;
                foreach (var col in r.GetComponents<Collider>()) Object.DestroyImmediate(col);
            }
            var l = new GameObject("KitchenChandelier_Light").AddComponent<Light>(); l.transform.SetParent(go.transform, false);
            l.transform.position = new Vector3(cx, gy + (float)c["cup_y"] + 0.07f, -cz); l.type = LightType.Point; l.range = 8f;
            l.gameObject.AddComponent<HDAdditionalLightData>();
            l.lightUnit = LightUnit.Lumen; l.intensity = c["lumens"] != null ? (float)c["lumens"] : ChandelierLumens; l.useColorTemperature = true; l.colorTemperature = (float)c["kelvin"]; l.shadows = LightShadows.Soft;
        }
    }

    // The kitchen's paper as the film shows it (tools/house/film_wallpaper.py --kitchen: one half-drop repeat cut from film 6910,
    // sized against the back-door leaf in film 6902), world-space triplanar at its own width and height; the plain cream if missing
    static Material KitchenPaper()
    {
        var m = Mat("Paper_Kitchen", KitchenWall);
        string src = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/kitchen_wallpaper.png"));
        if (!File.Exists(src)) return m;
        var rep = JObject.Parse(File.ReadAllText(Path.ChangeExtension(src, ".json")))["repeat_m"];
        Directory.CreateDirectory("Assets/Textures/Greybox"); string dst = "Assets/Textures/Greybox/kitchen_wallpaper.png";
        if (!File.Exists(dst) || !File.ReadAllBytes(dst).SequenceEqual(File.ReadAllBytes(src))) { File.Copy(src, dst, true); AssetDatabase.ImportAsset(dst); }
        m.SetColor("_BaseColor", Color.white); m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dst));
        m.SetFloat("_UVBase", 5f); m.SetFloat("_TexWorldScale", 1f); m.SetFloat("_Smoothness", 0.15f);
        m.SetTextureScale("_BaseColorMap", new Vector2(1f / (float)rep[0], 1f / (float)rep[1]));
        HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m); AssetDatabase.SaveAssetIfDirty(m);
        return m;
    }

    static Material Wallpaper(JToken w)
    {
        string src = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../" + (string)w["wallpaper_texture"]));
        Directory.CreateDirectory("Assets/Textures/Greybox"); string dst = "Assets/Textures/Greybox/wallpaper.png";
        File.Copy(src, dst, true); AssetDatabase.ImportAsset(dst);
        var m = Mat("Dress_Wallpaper", Color.white);
        m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dst));
        float rw = (float)w["wallpaper_repeat_m"][0], rh = (float)w["wallpaper_repeat_m"][1];
        m.SetFloat("_UVBase", 5f); m.SetFloat("_TexWorldScale", 1f);         // 5 = triplanar, 1 m per UV unit
        m.SetTextureScale("_BaseColorMap", new Vector2(1f / rw, 1f / rh));      // the repeat's own width and height (not squared)
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
        // cut lines closer than 1 cm merge: a 3 mm cell between them was too thin to build and left a slit in the upper hall's
        // ceiling (walk note Oct 15, 'why is there a gap?': hall vertices at x 5.634 and 5.637)
        List<float> Merge(IEnumerable<float> v) { var o = new List<float>(); foreach (var q in v.OrderBy(q => q)) if (o.Count == 0 || q - o[^1] > 0.01f) o.Add(q); return o; }
        var xs = Merge(pts.Select(p => p.x).Concat((extraX ?? Enumerable.Empty<float>()).Where(v => v > x0 && v < x1)));
        var zs = Merge(pts.Select(p => p.y).Concat((extraZ ?? Enumerable.Empty<float>()).Where(v => v > z0 && v < z1)));
        xs[^1] = x1; zs[^1] = z1;   // keep the outer edges exact
        for (int i = 0; i + 1 < xs.Count; i++)
            for (int k = 0; k + 1 < zs.Count; k++)
                if (Inside(pts, new Vector2((xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2)))
                    yield return (xs[i], xs[i + 1], zs[k], zs[k + 1]);
    }

    internal static bool Inside(List<Vector2> poly, Vector2 p)
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
    // A sliver of wall (< 15 cm) beside a rail or open side stood floor to ceiling like a post (walk note Oct 15: the hall's and
    // the stairwell's traced edges sit 6 cm apart, so the gallery rail stops short of the corner). Built to newel height
    // instead: it still closes the floor edge. The wall-grid rebuild (phase 5) aligns the edges.
    static float Stub(float a, float b, string nextKind, float ceil) =>
        b - a < 0.15f && (nextKind == "rail" || nextKind == "open") ? Mathf.Min(ceil, 1.10f) : ceil;

    static void CornerPosts(GameObject g, Space s, List<Door> doors)
    {
        // no post where the corner ends a rail or an open side: there is no wall to close, and the post stood free from
        // floor to ceiling beside the stair rail (walk note Oct 15)
        bool OnOpenSide(Vector2 v) => doors.Any(d => (d.a == s.name || d.b == s.name) && (d.kind == "rail" || d.kind == "open")
            && (d.alongX ? Mathf.Abs(v.y - d.coord) < 0.1f && v.x > d.lo - 0.1f && v.x < d.hi + 0.1f
                         : Mathf.Abs(v.x - d.coord) < 0.1f && v.y > d.lo - 0.1f && v.y < d.hi + 0.1f));
        foreach (var v in s.pts)
        {
            if (OnOpenSide(v)) continue;
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
        CornerPosts(g, s, doors);
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
                if (dl > cur) Seg(g, "Wall", alongX, t0, t1, cur, dl, 0f, Stub(cur, dl, d.kind, ceil));
                float head = d.kind == "door" ? d.height : d.kind == "arch" ? (d.height > 0 ? d.height : ArchHead) : ceil;
                if (head < ceil) Seg(g, d.kind + "_Header", alongX, t0, t1, dl, dh, head, ceil);
                if (d.kind == "arch" && d.spring > 0 && d.spring < head) ArchTop(g, alongX, t0, t1, sgn, dl, dh, d.spring, head, ceil);
                if (d.kind == "door" && s.kind != "opening")   // a stairwell's face has the flight in it, not trim (attic stair, Oct 15)
                {   // casing on this room's face: two legs and a head, proud of the wall toward the room
                    float f0 = t0, f1 = t0 - sgn * CasingProud;
                    Trim(g, alongX, f0, f1, dl - CasingW, dl, 0f, head + CasingW);
                    Trim(g, alongX, f0, f1, dh, dh + CasingW, 0f, head + CasingW);
                    Trim(g, alongX, f0, f1, dl - CasingW, dh + CasingW, head, head + CasingW);
                }
                cur = Mathf.Max(cur, dh);
            }
            if (cur < hi) Seg(g, "Wall", alongX, t0, t1, cur, hi, 0f, Stub(cur, hi, cuts.LastOrDefault()?.kind, ceil));
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

    // A segmental arch (film 2677/3888, Oct 15): the opening's top between the springline and the crown is a circular
    // segment; the corners outside it are wall, built as thin horizontal slices (grey-box), with casing legs to the
    // springline on this room's face.
    static void ArchTop(GameObject g, bool alongX, float t0, float t1, float sgn, float dl, float dh, float spring, float crown, float top)
    {
        float half = (dh - dl) / 2, mid = (dl + dh) / 2, rise = crown - spring, R = (half * half + rise * rise) / (2 * rise), yc = crown - R;
        const int N = 12;
        for (int i = 0; i < N; i++)
        {
            float y0 = spring + rise * i / N, y1 = Mathf.Min(spring + rise * (i + 1) / N, top), ym = (y0 + y1) / 2;   // same curve both faces; clipped at this side's wall top
            if (y1 <= y0) break;
            float w = Mathf.Sqrt(Mathf.Max(0f, R * R - (ym - yc) * (ym - yc)));   // half-width of the opening at ym
            Seg(g, "Arch_Spandrel", alongX, t0, t1, dl, mid - w, y0, y1);
            Seg(g, "Arch_Spandrel", alongX, t0, t1, mid + w, dh, y0, y1);
        }
        float f0 = t0, f1 = t0 - sgn * CasingProud;
        Trim(g, alongX, f0, f1, dl - CasingW, dl, 0f, spring);
        Trim(g, alongX, f0, f1, dh, dh + CasingW, 0f, spring);
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
        if (OpeningsOwnTrim) return;   // HOUSE-KERNEL step 2: the casing comes from each opening's record (SpecGreybox.Openings.cs LayCasings)
        float ta = Mathf.Min(t0, t1), tb = Mathf.Max(t0, t1);
        // trim never runs into a wall or floor: its faces would lie in theirs and flicker (z-fight gate, Oct 16). This drops the
        // stool and apron of floor-level windows and casing legs where the next room is no wider than the opening.
        var lo = alongX ? new Vector3(s0, y0 + FloorY, ta) : new Vector3(ta, y0 + FloorY, s0);
        var hi = alongX ? new Vector3(s1, y1 + FloorY, tb) : new Vector3(tb, y1 + FloorY, s1);
        Physics.SyncTransforms();
        if (Physics.OverlapBox((lo + hi) / 2, (hi - lo) / 2 - Vector3.one * 0.002f).Any(c => c.name == "Wall" || c.name.StartsWith("Floor"))) return;
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

    // A raking rail: the last box built is turned about its centre. "rise_x": metres it climbs from its +x end to its -x end (spec);
    // "rise_z": from its low-z end to its high-z end (spec z; Unity -z).
    static void Tilt(GameObject g, JToken b)
    {
        if (b["rise_x"] == null && b["rise_z"] == null) return;
        var t = g.transform.GetChild(g.transform.childCount - 1); var sc = t.localScale;
        if (b["rise_x"] != null) { float rx = (float)b["rise_x"]; t.rotation = Quaternion.Euler(0, 0, -Mathf.Atan2(rx, sc.x) * Mathf.Rad2Deg); t.localScale = new Vector3(Mathf.Sqrt(sc.x * sc.x + rx * rx), sc.y, sc.z); }
        if (b["rise_z"] != null) { float rz = (float)b["rise_z"]; t.rotation = Quaternion.Euler(Mathf.Atan2(rz, sc.z) * Mathf.Rad2Deg, 0, 0); t.localScale = new Vector3(sc.x, sc.y, Mathf.Sqrt(sc.z * sc.z + rz * rz)); }
    }

    // A vertical prism over a convex spec-plan polygon [[x, z], ...] from y0 to y1 (winder treads, Oct 15 night). Unity z = -spec z.
    static void Prism(GameObject p, string n, JToken poly, float y0, float y1, Material m)
    {
        var pts = poly.Select(q => new Vector3((float)q[0], 0f, -(float)q[1])).ToList(); int k = pts.Count;
        var c = Vector3.zero; foreach (var q in pts) c += q; c /= k;
        var v = new List<Vector3>(); var t = new List<int>();
        void Quad(Vector3 a, Vector3 b, Vector3 cc, Vector3 d) { int i = v.Count; v.AddRange(new[] { a, b, cc, d }); t.AddRange(new[] { i, i + 1, i + 2, i, i + 2, i + 3 }); }
        float s0 = 0; for (int i = 0; i < k; i++) { var a = pts[i]; var b = pts[(i + 1) % k]; s0 += (b.x - a.x) * (b.z + a.z); }
        if (s0 > 0) pts.Reverse();                                   // one winding for every prism
        for (int i = 0; i < k; i++)
        {
            var a = pts[i]; var b = pts[(i + 1) % k];
            Quad(a + Vector3.up * y0, a + Vector3.up * y1, b + Vector3.up * y1, b + Vector3.up * y0);
        }
        for (int i = 1; i < k - 1; i++)
        {
            int j = v.Count; v.AddRange(new[] { pts[0] + Vector3.up * y1, pts[i + 1] + Vector3.up * y1, pts[i] + Vector3.up * y1 }); t.AddRange(new[] { j, j + 1, j + 2 });
            j = v.Count; v.AddRange(new[] { pts[0] + Vector3.up * y0, pts[i] + Vector3.up * y0, pts[i + 1] + Vector3.up * y0 }); t.AddRange(new[] { j, j + 1, j + 2 });
        }
        // both windings: a face is visible whichever way the plan polygon was listed (Oct 15: one-sided winders rendered inside-out = missing)
        var hull = new Mesh { name = n + "_col" }; hull.SetVertices(v); hull.SetTriangles(new List<int>(t), 0); hull.RecalculateBounds();   // collider: one winding (a doubled mesh fails convex cooking: bodies walked through, Oct 15)
        int nt = t.Count; for (int i = 0; i < nt; i += 3) { t.Add(t[i]); t.Add(t[i + 2]); t.Add(t[i + 1]); }
        var mesh = new Mesh { name = n }; mesh.SetVertices(v); mesh.SetTriangles(t, 0); mesh.RecalculateNormals(); mesh.RecalculateBounds();
        var go = new GameObject(n); go.transform.parent = p.transform; go.transform.position = new Vector3(0, FloorY, 0);
        go.AddComponent<MeshFilter>().sharedMesh = mesh; go.AddComponent<MeshRenderer>().sharedMaterial = m;
        if (!AssetDatabase.IsValidFolder("Assets/Materials/Greybox/Meshes")) AssetDatabase.CreateFolder("Assets/Materials/Greybox", "Meshes");
        AssetDatabase.CreateAsset(mesh, $"Assets/Materials/Greybox/Meshes/{n}.asset");
        AssetDatabase.CreateAsset(hull, $"Assets/Materials/Greybox/Meshes/{n}_col.asset");
        var mc = go.AddComponent<MeshCollider>(); mc.convex = true; mc.sharedMesh = hull; go.isStatic = true;
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
            var hd = l.gameObject.AddComponent<HDAdditionalLightData>();   // first: adding it resets the light's intensity
            // rear_passage 900 -> 450 (Oct 18, user: "slightly dim the flush mount under the arch"): this fill sits on the passage's opal flush
            // mount (HiFiLights "Dome", 600 -> 400) and outshone it; the dome change alone measured no difference through the arch
            l.intensity = s.name == "rear_passage" ? 450f : 900f; l.color = new Color(1f, 0.95f, 0.88f);
            // shadowed (user, Oct 16, night "daylight streaming from outside"): unshadowed lamps lit the snow outside and the next rooms through walls
            l.shadows = LightShadows.Soft; hd.normalBias = 0.1f; hd.SetShadowResolution(512);
        }
    }

    // Winter daylight (user, Oct 15: natural light through the windows for daytime scenes): a low December sun, a snow
    // ground outside the windows, and the room lamps on N (HouseNightMode: day = lamps off). The house's compass bearing is
    // the front faces 227.6 deg (SW): OpenStreetMap's building and Lincoln Avenue (tools/house/house_bearing.py), with the photographers'
    // positions and the film's sunlit front (frame 4382) agreeing; the film was shot here, so this is its orientation. The sun's time is a placeholder (DEVIATIONS 34)
    const float FrontAzimuth = 227.6f;                    // compass bearing the front (+spec x) faces
    // the film's sun (Oct 19): solved from the portico's shadow in 4382 (tools/house/sun_solve.py: az 196.8 [192.6-200.2], el 35.0
    // [28.6-41.1]; ~1 pm in Feb 1990, when the exteriors were shot; DEVIATIONS 34). HouseWeather (O) swaps it for a morning or overcast sun
    const float SunAzimuth = 196.8f, SunElevation = 35f;
    static void Daylight(GameObject root, float groundY)
    {
        var day = Child(root, "Daylight");
        float rel = (SunAzimuth - FrontAzimuth) * Mathf.Deg2Rad, el = SunElevation * Mathf.Deg2Rad;
        var toSun = new Vector3(Mathf.Cos(rel) * Mathf.Cos(el), Mathf.Sin(el), -Mathf.Sin(rel) * Mathf.Cos(el));   // spec +z (right, from inside facing front) -> world -z
        var dayLayer = Child(day, "DayLayer");   // switched off at night (N) with the sun in it
        {   // day grade (user note 09:33, "the color look flat"): the sky's blue bounce made the floor blue and the paper grey; the
            // film's day interiors read warm. A little saturation, in the day layer only
            string dp = "Assets/Settings/DayGrade.asset"; AssetDatabase.DeleteAsset(dp);
            var prof = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(prof, dp);
            // White balance +12 removed (Oct 18, overnight3b): the blue it countered was the room probes not lighting LayerOverhang (Buzz's
            // navy floor) and probe images baked without the fill (BakeLighting); fixed, it only pushed the paper yellow. Without it every
            // film_light_match warmth read moves toward the film (foyer 2677 paper 5.91 -> 4.91 vs film 1.96; 10248 door 1.75 -> 1.58 vs 1.44)
            var ca = prof.Add<ColorAdjustments>(true); ca.saturation.value = 12f; AssetDatabase.AddObjectToAsset(ca, prof);
            var dv = new GameObject("DayGrade").AddComponent<Volume>(); dv.transform.parent = dayLayer.transform; dv.isGlobal = true; dv.priority = 5f; dv.sharedProfile = prof;
        }
        var sun = new GameObject("Sun").AddComponent<Light>(); sun.transform.parent = dayLayer.transform;
        sun.type = LightType.Directional; sun.transform.rotation = Quaternion.LookRotation(-toSun);
        var sunHd = sun.gameObject.AddComponent<HDAdditionalLightData>();   // first: adding it resets the light's intensity
        sun.intensity = 100000f; sun.color = Color.white; sun.shadows = LightShadows.Soft;   // the sky model reddens a low sun; white keeps the snow white
        // light leaking along wall/ceiling joints (user note Oct 15 23:06): a low sun with the default normal bias reads through 14 cm walls
        sunHd.normalBias = 0.1f; sunHd.SetShadowResolution(4096);
        // its shadows come from the storey the player is on (the overhang stop-gap, SpecGreybox.FilmFront): light reaches every layer
        sunHd.linkShadowLayers = false; sunHd.lightlayersMask = UnityEngine.Rendering.HighDefinition.RenderingLayerMask.Everything;
        sun.renderingLayerMask = (int)(LayerHouse | LayerFilmFront);
        var ss = sun.gameObject.AddComponent<StoreyShadows>(); ss.groundMask = LayerHouse | LayerFilmFront; ss.upperMask = LayerHouse | LayerOverhang;
        ss.switchY = groundY + 2.326f + 0.9f;   // the eye 0.9 m above the main stair's landing: past it, the upstairs' own shadows
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))   // both faces cast: a lit back face never leaks
            if (r.sharedMaterial != null && r.sharedMaterial.name == "Glass") r.shadowCastingMode = ShadowCastingMode.Off;   // window panes let the sun in
            // (Oct 19, sun-and-sky: HDRP draws a transparent caster into the shadow map as opaque, so the 45 grey-box panes kept every
            // sun patch out of the rooms; live A/B in the dining room: none with, the film's window patches without)
            else if (r.shadowCastingMode == ShadowCastingMode.On) r.shadowCastingMode = ShadowCastingMode.TwoSided;
        Exterior(groundY);   // the old reference scene's yard and street replace the flat snow plane (user, Oct 16: "weird artifacts")
        var lamps = root.transform.Cast<Transform>().SelectMany(t => t.GetComponentsInChildren<Transform>(true)).FirstOrDefault(t => t.name == "Lights");
        var groundLamps = GameObject.Find("Ground/Lights");   // one night layer: the ground floor's lamps were left on by day
        if (lamps != null && groundLamps != null) foreach (var t in groundLamps.transform.Cast<Transform>().ToList()) t.SetParent(lamps, true);
        // the foyer's fixtures are lamps too: their lights join the night layer and their bulbs and shades go dark by day (user, Oct 16: "shut
        // off the sconces and foyer lighting during the day so i can get a read on it"; they were lit by day and in the day bake)
        Renderer[] glow = new Renderer[0];
        foreach (var fxName in new[] { "Upstairs/FoyerFixtures", "Upstairs/KitchenFixtures", "Upstairs/DenFixtures", "Upstairs/DenBuiltins_HiFi", "Upstairs/LivingFixtures", "Upstairs/LivingBuiltins_HiFi", "Upstairs/DiningFixtures", "Upstairs/HallFixtures", "Upstairs/HallDressing_HiFi", "Upstairs/AtticFixtures", "Upstairs/Attic_HiFi", "Upstairs/KevinFixtures", "Upstairs/ParentsFixtures", "Upstairs/ParentsDressing_HiFi" })   // the kitchen's, the den's and the living room's lamps too
        {
            var fixtures = GameObject.Find(fxName);
            if (lamps == null || fixtures == null) continue;
            foreach (var l in fixtures.GetComponentsInChildren<Light>(true)) l.transform.SetParent(lamps, true);
            glow = glow.Concat(fixtures.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.sharedMaterial != null && (r.sharedMaterial.name.StartsWith("HiFi_Bulb") || r.sharedMaterial.name.StartsWith("HiFi_Shade")))).ToArray();
        }
        var cab = GameObject.Find("Upstairs/KitchenCabinets_HiFi");
        if (lamps != null && cab != null)
        {
            glow = glow.Concat(cab.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.sharedMaterial != null && r.sharedMaterial.name.StartsWith("HiFi_UnderCabGlow"))).ToArray();
            foreach (var n in new[] { "Light_kitchen", "Light_back_stair", "Light_den", "Light_living_room", "Light_dining_room", "Light_kevin_jeff_room" })   // no light without a fixture: the fixtures replace the rooms' generic lamps (the den's: DenLamps)
                foreach (var t in lamps.GetComponentsInChildren<Transform>(true).Where(t => t.name == n).ToList()) Object.DestroyImmediate(t.gameObject);
        }
        if (lamps != null) foreach (var l in ShellLights) if (l) l.transform.SetParent(lamps, true);   // the exterior's night lights (SpecGreybox.Shell)
        WindowBackdrop(dayLayer, lamps != null ? lamps.gameObject : null, groundY);   // SpecGreybox.Backdrop.cs: winter backdrop outside the windows (overnight5)
        var bdl = GameObject.Find("BasementDaylight"); if (bdl != null) bdl.transform.SetParent(dayLayer.transform, true);   // SpecGreybox.Basement: windows glow by day only
        var mode = new GameObject("Day and night - press N").AddComponent<HouseNightMode>(); mode.transform.parent = day.transform; mode.glowRenderers = glow.Concat(ShellGlow).Concat(PropGlow).ToArray();
        mode.nightLayer = lamps != null ? lamps.gameObject : null; mode.dayLayer = dayLayer; mode.interiorLights = new Light[0]; mode.daytimeEnabled = new bool[0];
        if (lamps != null) NightSetCheck(mode);   // SpecGreybox.Shell.cs
        if (lamps != null)   // night sky (user, Oct 16: "when it's nighttime i still see the daylight streaming from outside")
        {
            string np = "Assets/Settings/NightSky.asset"; AssetDatabase.DeleteAsset(np);
            var prof = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(prof, np);
            var env = prof.Add<VisualEnvironment>(true); env.skyType.value = (int)SkyType.Gradient; AssetDatabase.AddObjectToAsset(env, prof);
            var g = prof.Add<GradientSky>(true); AssetDatabase.AddObjectToAsset(g, prof);
            g.top.value = new Color(0.004f, 0.006f, 0.015f); g.middle.value = new Color(0.012f, 0.014f, 0.025f); g.bottom.value = new Color(0.02f, 0.02f, 0.025f);   // a dark winter night, faint snow glow at the horizon
            var nv = new GameObject("NightSky").AddComponent<Volume>(); nv.transform.parent = lamps; nv.isGlobal = true; nv.priority = 10f; nv.sharedProfile = prof;
            lamps.gameObject.SetActive(false);
        }
    }

    // Outside (user, Oct 16: "use the previous models outside snow and background"): the yard, walks and stoop of the downloaded
    // HOME ALONE FINAL.glb and the WinterNeighborhood (street, lots, houses, trees, wires) from IntactHouseReference, without the
    // GLB's house shell (it does not fit the measured rooms). That scene's front door axis is x 1.9, its facade z -2.6, its
    // floor y 1.31, the house facing -z; ours faces +x with the front wall's outer face at x 10.27, door axis spec z 9.716.
    // The GLB is unlicensed (memory exterior-shell-from-downloaded-glb) and not checked against the film: background only.
    static void Exterior(float gy)
    {
        var here = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var src = EditorSceneManager.OpenScene("Assets/Scenes/IntactHouseReference.unity", OpenSceneMode.Additive);
        var ext = new GameObject("Exterior");
        ext.transform.SetPositionAndRotation(new Vector3(10.27f - 2.6f, gy - 1.31f, -9.716f - 1.9f), Quaternion.Euler(0, -90f, 0));
        // the GLB's site, REGISTERED to our house (Oct 18, TRIAL; changes/2026-10-18-yard-registration.json): tools/house/register_glb.py's
        // similarity (s 0.757, 23 facade/stair features) as a world transform; its y was solved for gy -2.996, so it moves with gy
        var reg = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/glb_registration.json"))))["unity_exterior_transform"];
        var site = new GameObject("Site"); site.transform.SetParent(ext.transform, false);
        site.transform.SetPositionAndRotation(new Vector3((float)reg["position"][0], (float)reg["position"][1] + gy + 2.996f, (float)reg["position"][2]), Quaternion.Euler(0, (float)reg["euler_y_deg"], 0));
        site.transform.localScale = Vector3.one * (float)reg["scale"];
        var glb = src.GetRootGameObjects().First(g => g.name == "IntactGLB");
        if (PrefabUtility.IsPartOfPrefabInstance(glb)) PrefabUtility.UnpackPrefabInstance(glb, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
        var house = new Bounds(new Vector3(2.7f, 0, 8.2f), new Vector3(28.7f, 100f, 21.9f));   // the GLB house's footprint (its window assemblies' extent)
        int kept = 0, prop = 0;
        foreach (var r in glb.GetComponentsInChildren<MeshRenderer>().ToList())
        {
            if (!r.enabled || r.name == "object183") continue;   // object183: the treehouse (built to the film by its own job, at the registered GLB position)
            if (r.name == "object257") continue;                 // a rear-yard slab that ran over the areaway's top steps: SpecGreybox.Yard's Grade_RearW
            if (r.name == "object2") continue;                   // a post at the GLB lot's edge, on the front drive's right leg (SpecGreybox.FrontDrive; not in the film)
            if (r.bounds.max.y > 1.35f || house.Contains(new Vector3(r.bounds.center.x, 0, r.bounds.center.z)))
            {   // the property beyond the house (user Oct 18: "a good layout of the property, including the standalone garage"): the GLB
                // merges parts by material, so the garage shares meshes with the house shell; its triangles are cut out by region
                if (PropertyPart(r, site.transform) != null) prop++;
                continue;
            }
            r.transform.SetParent(null, true); UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(r.gameObject, here);
            r.transform.SetParent(site.transform, false); kept++;
        }
        var hood = src.GetRootGameObjects().First(g => g.name == "WinterNeighborhood");
        UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(hood, here); hood.transform.SetParent(ext.transform, false);
        // the neighbourhood keeps its plan; up 0.396 m so its street (top -0.39 local) sits just over the registered front yard (-4.33
        // world): left at the old height the yard slabs buried half the street (DEVIATIONS 93)
        hood.transform.localPosition = Vector3.up * 0.396f;
        // the walk's last 4.5 m (sidewalk to x 24.4, between the piers) is the lot's own walk, not the neighbourhood's: out of the hood so
        // K (PropertyView, which hides the whole hood) keeps it (walk note Oct 19 09:04: the piers stood beside a void)
        foreach (var t in hood.GetComponentsInChildren<Transform>(true).Where(t => t.name == "Front walk connection").ToList()) t.SetParent(ext.transform, true);
        // the reference scene's facade shutters were fitted to the GLB shell's windows: the exterior skin has the film's own (SpecGreybox.Shell)
        foreach (var t in hood.GetComponentsInChildren<Transform>(true).Where(t => t.name == "Front facade shutters").ToList()) Object.DestroyImmediate(t.gameObject);
        EditorSceneManager.CloseScene(src, true);
        Yard(ext, gy, site.GetComponentsInChildren<MeshRenderer>().FirstOrDefault(r => r.name == "object251")?.sharedMaterial ?? mFloor);
        // nothing from outside may stand inside the measured house: the reference scene's facade shutters were fitted to the GLB shell
        // (dropped above), and its upper ones hung 0.8 m inside Buzz's and Kevin's rooms as black boxes (walk note Oct 17 18:10). Every
        // exterior renderer with any of 27 points of its bounds inside a room volume (SpecGreybox.EnvelopeRooms) is removed.
        var geoJ = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        var hsJ = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.json"))));
        var vols = EnvelopeRooms(geoJ, hsJ["attic_stair"]["boxes"], gy);
        var inside = new List<string>();
        foreach (var r in ext.GetComponentsInChildren<Renderer>(true).ToList())
        {
            var b = r.bounds; bool hit = false;
            for (int i = 0; i < 27 && !hit; i++)
            {
                var q = new Vector3(Mathf.Lerp(b.min.x, b.max.x, (i % 3) / 2f), Mathf.Lerp(b.min.y, b.max.y, (i / 3 % 3) / 2f), Mathf.Lerp(b.min.z, b.max.z, (i / 9) / 2f));
                hit = vols.Any(v => q.y > v.y0 && q.y < v.y1 && Inside(v.pts, new Vector2(q.x, q.z)));
            }
            if (hit) { inside.Add(r.transform.parent.name + "/" + r.name); Object.DestroyImmediate(r.gameObject); }
        }
        Debug.Log($"Exterior: {kept} site meshes and {prop} property parts (garage, driveway) from the GLB, {hood.GetComponentsInChildren<Renderer>().Length} neighborhood renderers; " +
                  $"{inside.Count} inside the rooms removed ({string.Join(", ", inside.GroupBy(n => n).Select(q => $"{q.Count()} x {q.Key}"))})");
        ExteriorPlants(ext.transform.Find("Yard").gameObject, gy + 2.996f);   // SpecGreybox.Shell.cs: plants, mini-lights, lamp posts (exterior polish;
                          // after the cull: the strung lights' one mesh spans the front, and the den-front shrubs' boxes touch the den's volume)
        Trees(ext);       // SpecGreybox.Trees.cs: generated bare winter trees replace the stick trees (hifi_bare_trees.py)
        Shell(ext, gy);   // SpecGreybox.Shell.cs: the house's exterior skin (after the cull above: its upper storey crosses Marina's rooms by design)
        ExteriorRealism(ext, gy);   // SpecGreybox.ExteriorRealism.cs: steps, railings, drifts, ground skirt, decals, wet road (changes/2026-10-18-exterior-realism.json)
        FrontDrive(ext, gy);        // SpecGreybox.FrontDrive.cs: the U-drive, the walk piers and wing walls, the garage fence (changes/2026-10-19-front-drive.json)
    }

    // The GLB's garage and driveway (registered with the site): triangles of a GLB renderer whose registered centroid lies in the
    // garage's plot (spec x -8.3..-0.3, z 19.55..28.2: the detached garage behind the den end, film 2515/6810) or, for the driveway
    // meshes (object161/192), anywhere outside our house's footprint, become a new mesh under the Site (same local pose, collider).
    static GameObject PropertyPart(MeshRenderer r, Transform site)
    {
        var mf = r.GetComponent<MeshFilter>(); if (mf == null || mf.sharedMesh == null) return null;
        var m = mf.sharedMesh; var vs = m.vertices; var tr = r.transform;   // tr: the GLB's pose in the reference scene = the Site's local space
        bool drive = r.name == "object161" || r.name == "object192";
        bool Keep(Vector3 a)
        {
            var w = site.TransformPoint(a); float x = w.x, z = -w.z;
            if (x > -8.3f && x < -0.3f && z > 19.55f && z < 28.2f) return true;
            // the driveway beside the den end to the garage only: the GLB's loop across the front lawn (z < 20.2) runs where the film's
            // terraced beds are (4382) and stood 0.41 m over the front walk (yard trial 1)
            return drive && z >= 20.2f;
        }
        var map = new Dictionary<int, int>(); var subs = new List<List<int>>();
        for (int s = 0; s < m.subMeshCount; s++)
        {
            var t = m.GetTriangles(s); var keep = new List<int>();
            for (int i = 0; i < t.Length; i += 3)
                if (Keep(tr.TransformPoint((vs[t[i]] + vs[t[i + 1]] + vs[t[i + 2]]) / 3f)))
                    for (int k = 0; k < 3; k++) { if (!map.TryGetValue(t[i + k], out int j)) map[t[i + k]] = j = map.Count; keep.Add(j); }
            subs.Add(keep);
        }
        if (map.Count == 0) return null;
        var order = map.OrderBy(q => q.Value).Select(q => q.Key).ToArray();
        var nm = new Mesh { name = r.name + "_property", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
        nm.vertices = order.Select(i => vs[i]).ToArray();
        if (m.normals.Length > 0) { var n = m.normals; nm.normals = order.Select(i => n[i]).ToArray(); }
        if (m.uv.Length > 0) { var u = m.uv; nm.uv = order.Select(i => u[i]).ToArray(); }
        if (m.tangents.Length > 0) { var tg = m.tangents; nm.tangents = order.Select(i => tg[i]).ToArray(); }
        var mats = new List<Material>(); nm.subMeshCount = subs.Count(q => q.Count > 0); int si = 0;
        for (int s = 0; s < subs.Count; s++) if (subs[s].Count > 0) { nm.SetTriangles(subs[s], si++); mats.Add(r.sharedMaterials[Mathf.Min(s, r.sharedMaterials.Length - 1)]); }
        nm.RecalculateBounds();
        var go = new GameObject(r.name + "_property"); go.transform.SetParent(site, false);
        go.transform.localPosition = tr.position; go.transform.localRotation = tr.rotation; go.transform.localScale = tr.lossyScale;
        go.AddComponent<MeshFilter>().sharedMesh = nm; go.AddComponent<MeshRenderer>().sharedMaterials = mats.ToArray();
        go.AddComponent<MeshCollider>().sharedMesh = nm; go.isStatic = true;
        return go;
    }

    // Yard grade round the house (Oct 18, TRIAL; changes/2026-10-18-yard-registration.json, DEVIATIONS 93). The registered GLB site
    // is a few snow slabs at three levels: rear yard -3.40, left side -3.59, front yard -4.33 (world; our ground floor -2.996). Its
    // slabs that ran under the house (and the front yard's, which touches the basement) are dropped, so these boxes close the ring
    // between the house and the slabs at the GLB's levels (+1 cm, no coplanar faces), outside every foundation wall; plus what the
    // GLB lacks: the stoop and terrace fill against our front wall, the front steps (film 4382: red steps down through the terraced
    // beds) and walk, steps from the front yard up to the side yard, and the back-door stoop (film 4575). Spec x, z; world y.
    static readonly (string n, float x0, float x1, float z0, float z1, float top)[] YardBoxes = {
        ("Grade_RearA", -9.642f, -5.33f, -1.0f, -0.365f, -3.39f), ("Grade_RearB", -9.642f, -5.33f, 1.305f, 20.6f, -3.39f),   // either side of the areaway
        ("Grade_RearA2", -9.642f, -9.06f, -6.3f, -1.0f, -3.39f),
        ("Grade_RearW", -21.85f, -9.642f, -6.3f, 3.10f, -3.40f),   // replaces the GLB's slab object257, which ran 0.7 m over the areaway's top steps (head height)
        ("Grade_RearC", -5.33f, -1.65f, 4.22f, 20.6f, -3.39f), ("Grade_RearD", -1.65f, -0.13f, 7.78f, 20.6f, -3.39f),
        ("Grade_RearE", -0.13f, 1.44f, 11.57f, 20.6f, -3.39f), ("Grade_RearF", 1.44f, 2.21f, 16.21f, 20.6f, -3.39f),
        ("Grade_DenSide", 2.21f, 9.41f, 20.06f, 20.6f, -4.32f), ("Grade_DenFront", 9.41f, 10.40f, 16.37f, 20.6f, -4.32f),
        ("Grade_Front", 10.40f, 22.5f, -5.4f, 25.0f, -4.32f),                                                           // the GLB's front-yard slab, off the foundation
        // the stoop, front steps, terraced beds and walk: SpecGreybox.Shell's FrontBeds (exterior shell, Oct 18)
        ("Stoop_Back", -6.43f, -5.33f, 1.75f, 3.25f, -3.127f), ("Step_Back", -6.73f, -6.43f, 1.75f, 3.25f, -3.259f),   // sill -2.996: 3 risers of 0.131
    };

    static void Yard(GameObject ext, float gy, Material snow)
    {
        var g = new GameObject("Yard"); g.transform.SetParent(ext.transform, false); g.transform.rotation = Quaternion.identity;
        float d = gy + 2.996f;   // the levels are the registered GLB's at gy -2.996
        var stone = Mat("Yard_Steps", new Color(0.50f, 0.22f, 0.18f));   // film 4382: red steps
        var walk = Mat("Yard_Walk", new Color(0.45f, 0.43f, 0.40f));
        foreach (var b in YardBoxes)
            Box(g, b.n, b.x0, b.x1, -b.z1, -b.z0, b.n.StartsWith("Grade") ? b.top + d - 0.30f : b.x0 > 0 ? -4.35f + d : b.top + d - 0.40f, b.top + d,   // front pieces stand on the front yard
                b.n.StartsWith("Grade") || b.n.StartsWith("Terrace") ? snow : b.n.StartsWith("Path") ? walk : stone);
        FrontBeds(g, d, snow, walk);   // SpecGreybox.Shell.cs
        for (int k = 1; k <= 3; k++)   // front yard (-4.32) up to the side yard (-3.59, GLB slab edge x ~10.46): 4 risers of 0.1825, rising -x;
            // past the sun porch and greenhouse (spec z -3.65..-4.95; SpecGreybox.Shell)
            Box(g, $"Step_Side{k}", k == 3 ? 10.25f : 10.85f + 0.30f * (2 - k), 10.85f + 0.30f * (3 - k), 3.65f, 4.95f, -4.35f + d, -4.32f + 0.1825f * k + d, stone);
    }

    // the outside routes (spec x, world y, spec z): Marv from the street round the left side to the areaway, then the basement path
    // backwards (down the areaway, through the door, across, up the flight, through Kevin's door into the kitchen); the front walk
    // to the front door; the back steps into the kitchen
    static List<(string name, List<Vector3> pts)> YardRoutes(float gy, List<Vector3> basementPath)
    {
        float d = gy + 2.996f;
        List<Vector3> W(params float[] q) => Enumerable.Range(0, q.Length / 3).Select(i => new Vector3(q[3 * i], q[3 * i + 1] + d, -q[3 * i + 2])).ToList();
        // round the sun porch (spec z -3.0..-1.16, x 5.4..9.3) and greenhouse: up the side steps at z -4.3, back to z -1.95 behind the porch
        var marv = W(34.0f, -4.30f, -4.3f, 12.0f, -4.32f, -4.3f, 9.9f, -3.59f, -4.3f, 4.6f, -3.59f, -4.3f, 4.6f, -3.59f, -1.95f, -8.0f, -3.59f, -1.95f, -10.14f, -3.40f, -0.85f);
        marv.AddRange(Enumerable.Reverse(basementPath));
        return new List<(string, List<Vector3>)> {
            ("MARV (street -> left side -> areaway -> basement door -> basement -> stair -> Kevin's door -> kitchen)", marv),
            ("FRONT WALK (street -> walk -> steps -> stoop at the front door; the door is shut by design)", W(34.0f, -4.30f, 9.716f, 20.0f, -4.30f, 9.716f, 14.5f, -4.30f, 9.716f, 10.65f, -3.09f, 9.716f)),
            ("BACK DOOR (yard -> step -> stoop -> through the open back door -> kitchen, and back out)", W(-8.5f, -3.39f, 2.5f, -7.3f, -3.39f, 2.5f, -5.75f, -3.127f, 2.5f, -4.75f, -2.996f, 2.5f, -3.9f, -2.996f, 2.3f)),
        };
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
        // baked bounce light (APV) is looked up 0.25 m out along each surface's normal: a door leaf set in a 14 cm wall read its light
        // from inside the wall (invalid, black) and showed only reflections (Oct 16)
        var pvo = profile.Add<ProbeVolumesOptions>(true); pvo.normalBias.value = 0.25f; AssetDatabase.AddObjectToAsset(pvo, profile);
        var vol = new GameObject("GlobalVolume").AddComponent<Volume>(); vol.transform.parent = root.transform; vol.isGlobal = true; vol.sharedProfile = profile;
    }

    // The main stair: solid steps, landing, rails and well walls as spec boxes (spec z -> world -z); returns the walk path.
    static List<Vector3> Stair(GameObject root, JToken st, bool skipFloorPatch, string child = "MainStair", bool dress = true, bool stairOnly = false, Material stepMat = null, float keepAbove = float.MaxValue)
    {
        if (st == null || st.Type == JTokenType.Null) return new List<Vector3>();
        var g = Child(root, child);
        foreach (var b in st["boxes"])
        {
            string kind = (string)b["kind"];
            if (kind == "room" || kind == "opening") continue;   // the attic's room volume and dormer opening: data for the envelope (SpecGreybox.Attic)
            // the wall grid builds the stair hall itself, up to its storey's ceiling; a shaft above that (the attic stair's) is the stair's own
            if (stairOnly && (kind == "wall" || kind == "ceiling" || kind == "floor") && (float)b["y"][0] < keepAbove - 1e-3f) continue;
            if (kind == "stop")
            {   // an invisible stop: a collider only (where the head room ends)
                Box(g, (string)b["name"], (float)b["x"][0], (float)b["x"][1], -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0], (float)b["y"][1], mWall);
                Object.DestroyImmediate(g.transform.GetChild(g.transform.childCount - 1).GetComponent<MeshRenderer>());
                continue;
            }
            if (kind == "tread" || kind == "newel" || kind == "riser" || kind == "stringer" || kind == "spindle" || kind == "spandrel" || kind == "door_prop" || kind == "casing")
            {   // the back stair (film 912/928/1044): dark wood treads and posts, white risers, stringer and balusters; the papered
                // wall under its high end with the basement door in it
                var pm = kind == "tread" || kind == "newel" ? Mat("Wood_StairDark", new Color(0.24f, 0.12f, 0.07f))
                       : kind == "spandrel" ? (stepMat ?? mWall) : kind == "door_prop" ? mProp : Mat("Paint_StairWhite", new Color(0.9f, 0.9f, 0.87f));
                if (b["poly"] != null) { Prism(g, (string)b["name"], b["poly"], (float)b["y"][0], (float)b["y"][1], pm); continue; }
                Box(g, (string)b["name"], (float)b["x"][0], (float)b["x"][1], -(float)b["z"][1], -(float)b["z"][0], (float)b["y"][0], (float)b["y"][1], pm);
                Tilt(g, b);
                continue;
            }
            if (kind == "floor" && skipFloorPatch) continue;   // the ground floor's foyer is built for real
            var m = kind == "rail" ? mRail : kind == "wall" ? mWall : kind == "floor" || (!dress && kind == "step") ? mFloor : kind == "ceiling" ? mCeil : mHall;   // attic treads: bare wood (film)
            if (stepMat != null && kind == "step") m = stepMat;
            if (b["poly"] != null) { Prism(g, (string)b["name"], b["poly"], (float)b["y"][0], (float)b["y"][1], m); continue; }
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
            Tilt(g, b);
        }
        return st["walk_path"].Select(q => new Vector3((float)q[0], (float)q[1], -(float)q[2])).ToList();
    }

    // Both bodies walk the stair path up and back down with a real CharacterController (gravity, 0.3 m step offset).
    // A leg passes when the body ends within 0.15 m of the waypoint (horizontally) and 0.1 m of its floor height.
    // Every built part must be visible from outside: for each renderer, rays from 6 directions at its bounds must hit it from its own
    // outside (a one-sided mesh wound inside-out passes the walk tests but renders as missing; Oct 15 winders).
    static string RenderCheck(Transform t)
    {
        if (t == null) return "";
        var bad = new List<string>(); int n = 0;
        foreach (var r in t.GetComponentsInChildren<MeshRenderer>())
        {
            var mf = r.GetComponent<MeshFilter>(); if (mf == null || mf.sharedMesh == null) continue; n++;
            var m = mf.sharedMesh; var tr = r.transform; int front = 0, faces = 0;
            var tris = m.triangles; var vs = m.vertices;
            var c = r.bounds.center;
            for (int i = 0; i < tris.Length; i += 3)
            {
                var a = tr.TransformPoint(vs[tris[i]]); var b = tr.TransformPoint(vs[tris[i + 1]]); var d = tr.TransformPoint(vs[tris[i + 2]]);
                var nrm = Vector3.Cross(b - a, d - a); if (nrm.sqrMagnitude < 1e-10f) continue; faces++;
                if (Vector3.Dot(nrm, (a + b + d) / 3 - c) > 0) front++;   // Unity front faces are clockwise: the normal (left-handed) points out
            }
            if (faces > 0 && front * 2 + 4 < faces) bad.Add(r.name);   // double-sided parts sit at half (minus faces through the centre)
        }
        return $"Render check (outward faces, ServiceStair): {n} parts, {bad.Count} inside-out\n" + string.Concat(bad.Select(b => $"INSIDE-OUT {b}\n"));
    }

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
            // spaces whose floor is all stair (the back stair): reached by its foot, not sideways through its balustrades
            Vector3 M0((float, float, float, float) q) => new Vector3((q.Item1 + q.Item2) / 2, FloorY, (q.Item3 + q.Item4) / 2);
            // free = room for the body AND floor under it (Oct 18: the basement stair's opening under the back stair let Kevin 'stand' over the hole)
            bool Free(Vector3 p) => !Physics.CheckCapsule(p + Vector3.up * (r + 0.06f), p + Vector3.up * (h - r), r) && Physics.Raycast(p + Vector3.up * 0.05f, Vector3.down, 0.15f);
            // where a body stands in a cell: its centre, or, when only FURNITURE stands there (walk-layer colliders "*Collider_*": the den's
            // and living room's furniture took their centres, Oct 16), the free point nearest the centre on a 0.25 m grid. A stair still blocks.
            Vector3? Stand((float, float, float, float) q)
            {
                var c0 = M0(q); if (Free(c0)) return c0;
                if (!Physics.OverlapCapsule(c0 + Vector3.up * (r + 0.06f), c0 + Vector3.up * (h - r), r).All(k => k.name.Contains("Collider_") || k.name.EndsWith("_Collider"))) return null;   // store props' walk boxes ("<name>_Collider", StoreProps.cs) are furniture too
                var pts = new List<Vector3>();
                for (float x = q.Item1 + r + 0.05f; x <= q.Item2 - r - 0.05f; x += 0.25f)
                    for (float z = q.Item3 + r + 0.05f; z <= q.Item4 - r - 0.05f; z += 0.25f) pts.Add(new Vector3(x, FloorY, z));
                foreach (var p in pts.OrderBy(p => (p - c0).sqrMagnitude)) if (Free(p)) return p;
                return null;
            }
            var stairFloored = spaces.Where(sp => !Cells(sp.pts).Any(q => Stand(q) != null)).Select(sp => sp.name).ToHashSet();
            foreach (var s in spaces.Where(s => s.kind == "room" || s.kind == "hall"))
            {
                // target: the centre of the largest cell a body can stand in (an L-shaped foyer's largest cell centres on the stair)
                var order = Cells(s.pts).OrderByDescending(q => (q.Item2 - q.Item1) * (q.Item4 - q.Item3)).ToList();
                var at = order.Select(Stand).FirstOrDefault(p => p != null);
                if (at == null) { lines.Add($"skip    {name} {s.name}: no cell to stand in (its floor is a stair)"); continue; }
                var mid = at.Value;
                foreach (var d in doors.Where(d => (d.a == s.name || d.b == s.name) && (d.kind == "door" || d.kind == "arch" || d.kind == "open")))
                {
                    if (d.kind == "open" && stairFloored.Contains(d.a == s.name ? d.b : d.a)) { lines.Add($"skip    {name} {s.name} via {d.a}/{d.b}: the other side is all stair"); continue; }
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
                            if (n.StartsWith("flight1_") || n.StartsWith("service_") || n.StartsWith("Floor")) continue;   // standing on a stair: its own treads are not a ceiling
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

    // Named one-off views (spec/captures/views/views.json: [{name, pos, look_at, vfov, near?, hide?}], Unity world coordinates).
    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderViews -quit -logFile - [-scene IntactHouseReference] [-views views-buzz-old.json]
    public static void RenderViews()
    {
        var a = System.Environment.GetCommandLineArgs(); int si = System.Array.IndexOf(a, "-scene"), vi = System.Array.IndexOf(a, "-views");
        // default: the scene we build (House_WallGrid); the old default Greybox_Upstairs silently rendered a stale house (Oct 16)
        EditorSceneManager.OpenScene($"Assets/Scenes/{(si >= 0 ? a[si + 1] : "House_WallGrid")}.unity");
        var go = new GameObject("ViewCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        // Render-only fill, never saved (the scene is not saved): "-fill <intensity>" hangs a shadowless point light on the
        // camera; "-ev <EV100>" fixes exposure through a temporary top-priority global volume (scene assets untouched).
        int fi = System.Array.IndexOf(a, "-fill"), ei = System.Array.IndexOf(a, "-ev");
        if (System.Array.IndexOf(a, "-night") >= 0)   // "-night": as after pressing N; one frame first so the baked probes are loaded
        { cam.Render(); Object.FindFirstObjectByType<HouseNightMode>()?.SetNight(true); }
        if (fi >= 0)
        {
            var l = new GameObject("FillLight").AddComponent<Light>(); l.transform.SetParent(go.transform, false);
            l.type = LightType.Point; l.range = 25f; l.intensity = float.Parse(a[fi + 1]); l.shadows = LightShadows.None;
            l.gameObject.AddComponent<HDAdditionalLightData>();
        }
        {   // batch renders do not apply the baked room reflection probes, so every surface reflected the raw sky (a blue or grey wash by
            // day that play mode does not have, Oct 16). The sky fallback is off here; judge final lighting from the live play view
            // (unity command capture_game_view --source screen), which has the probes
            var prof = ScriptableObject.CreateInstance<VolumeProfile>(); var ilc = prof.Add<IndirectLightingController>(true);
            ilc.reflectionLightingMultiplier.value = 0f;
            var vol = new GameObject("NoSkyReflect").AddComponent<Volume>(); vol.isGlobal = true; vol.priority = 10001f; vol.sharedProfile = prof;
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
            var lid = v["trunk_lid"] != null ? GameObject.Find("TrunkLid")?.transform : null; var lidRot = lid ? lid.rotation : Quaternion.identity;
            if (lid) OpenTrunkLid(lid, (float)v["trunk_lid"]);   // "trunk_lid": degrees open for this view only (SpecGreybox.Trunk)
            go.transform.position = V(v["pos"]); go.transform.LookAt(V(v["look_at"])); cam.fieldOfView = (float)v["vfov"];
            cam.nearClipPlane = v["near"] != null ? (float)v["near"] : 0.05f;   // film cameras stood outside the front door (long lens)
            var split = Object.FindFirstObjectByType<HouseSplit>(); split?.ApplyFor(go.transform.position);   // the split, as the player would see it from here
            cam.Render(); cam.Render();   // warm-up frames, always: HDRP's first frame has no sky ambient yet
            Shot(cam, rt, Path.Combine("views", (string)v["name"]));
            split?.RestoreAll();
            hidden.ForEach(o => o.SetActive(true));
            if (lid) lid.rotation = lidRot;
        }
        RenderTexture.active = null; Object.DestroyImmediate(go); rt.Release();
    }

    static void Player(Space hall) => Player(HallSpawn(hall), 0f);
    static Vector3 HallSpawn(Space hall)
    {   // the hall's widest floor cell (its vertex average can sit over the stairwell; the gallery is long but narrow)
        var c = Cells(hall.pts).OrderByDescending(q => Mathf.Min(q.Item2 - q.Item1, q.Item4 - q.Item3)).First();
        return new Vector3((c.Item1 + c.Item2) / 2, 0.05f, (c.Item3 + c.Item4) / 2);
    }
    // the house's start (user, Oct 16: "start me in the foyer looking at the staircase as if i've come through the front door"): 0.6 m
    // into the foyer through the vestibule's opening, facing the main stair's first step
    static (Vector3 at, float yaw) FrontDoorSpawn(JToken ground, JToken stair, float gy)
    {
        var o = ground["openings"].First(q => q["between"].Select(t => (string)t).OrderBy(t => t).SequenceEqual(new[] { "foyer", "vestibule" }));
        var at = new Vector3((float)o["c"] - 0.6f, gy + 0.05f, -((float)o["lo"] + (float)o["hi"]) / 2);
        var b = stair["boxes"].First(q => (string)q["name"] == "flight1_step01");
        var foot = new Vector3(((float)b["x"][0] + (float)b["x"][1]) / 2, at.y, -((float)b["z"][0] + (float)b["z"][1]) / 2);
        return (at, Quaternion.LookRotation(foot - at).eulerAngles.y);
    }
    static void Player(Vector3 at, float yaw)
    {
        var p = new GameObject("Player"); p.transform.SetPositionAndRotation(at, Quaternion.Euler(0f, yaw, 0f));
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
            // the centre first; a wide opening may be passed off-centre (the bench beside the widened arch, Oct 15), 10 cm steps
            var cs = new List<float> { (d.lo + d.hi) / 2 };
            for (float t = d.lo + r + 0.05f; t <= d.hi - r - 0.05f; t += 0.1f) cs.Add(t);
            RaycastHit hit = default; bool blocked = true;
            foreach (float c in cs)
            {
                Vector3 P(float off) => d.alongX ? new Vector3(c, 0.06f + FloorY, d.coord + off) : new Vector3(d.coord + off, 0.06f + FloorY, c);
                Vector3 a = P(-0.45f), b = P(0.45f), dir = (b - a).normalized; float len = Vector3.Distance(a, b);
                Vector3 p1 = a + Vector3.up * r, p2 = a + Vector3.up * (h - r);
                RaycastHit hh;
                if (!Physics.CapsuleCast(p1, p2, r, dir, out hh, len)) { blocked = false; break; }
                if (c == cs[0]) hit = hh;
            }
            n++;
            if (blocked)
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
        string fp = Path.Combine(CaptureDir, name + ".png"); Directory.CreateDirectory(Path.GetDirectoryName(fp));   // view names may hold folders
        File.WriteAllBytes(fp, tex.EncodeToPNG()); Object.DestroyImmediate(tex);
    }
}
