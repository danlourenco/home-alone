using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

/// Builds Assets/Scenes/House.unity from art/home_alone/references/survey/house_survey.json.
/// Combines image-derived survey data with authored adaptations; see the reconciliation evidence ledger.
/// Run: Unity -batchmode -projectPath . -executeMethod SurveyBuilder.Build -quit
public static partial class SurveyBuilder
{
    const float T = SurveyHouse.WallThickness;
    static Material matFloor, matWall, matCeil, matUpper, matAttic, matStair;

    class Rect { public string name; public float x0, x1, y0, y1; public float W => x1 - x0; public float D => y1 - y0; }
    // An opening on a wall line. xWall: wall runs along Z at X = at (opening spans y a..b); else wall along X at Y = at.
    class Opening { public bool xWall; public float at, a, b, sill, head; public string name; }

    static string SurveyPath => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../art/home_alone/references/survey/house_survey.json"));

    [MenuItem("HomeAlone/Build House From Survey")]
    public static void Build()
    {
        var j = JObject.Parse(File.ReadAllText(SurveyPath));
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        MakeMaterials();
        var root = new GameObject("House");

        // ---------- ground floor ----------
        var g = (JObject)j["ground"];
        var rooms = ReadRooms((JObject)g["rooms"]).Where(r => r.name != "closet_off_breakfast").ToList();
        var openings = ReadOpenings((JObject)g["openings"]);
        float ceil = SurveyHouse.GroundCeiling;
        // Openings the wall-top survey could not see (cased openings keep their header), placed from the
        // eye-level frames M15/M18/M23/M24 and the real-house plan (hookedonhouses.net): two doorways from
        // the dining room into the breakfast room with the hutch between them, the closet niche, the
        // breakfast rear window, the window-seat windows, and the front door.
        openings.AddRange(new[] {
            Op("front_door", false, 0.20f, 10.75f, 11.65f, 0, SurveyHouse.DoorHead),
            Op("foyer_rear_arch_door", false, 11.01f, 10.0f, 10.9f, 0, SurveyHouse.DoorHead),
            Op("breakfast_dining_french", false, 6.6f, 17.1f, 18.45f, 0, 2.3f),
            Op("closet_off_breakfast", false, 8.5f, 18.62f, 19.25f, 0, SurveyHouse.DoorHead),
            Op("breakfast_rear_window", false, 12.64f, 14.7f, 15.4f, SurveyHouse.WindowSill, 2.1f),
            Op("window_seat_1_window", true, 22.51f, 13.8f, 14.8f, SurveyHouse.WindowSill, 2.1f),
            Op("window_seat_2_window", true, 22.51f, 11.5f, 12.5f, SurveyHouse.WindowSill, 2.1f),
            Op("fireplace", false, 9.42f, 5.92f, 7.47f, 0, 1.2f),
            Op("living_front_window_w", false, 0.36f, 5.1f, 6.3f, 0.9f, 2.2f),
            Op("living_front_window_e", false, 0.36f, 6.9f, 8.1f, 0.9f, 2.2f),
            Op("dining_front_french_w", false, 0.41f, 14.3f, 15.5f, 0, 2.3f),
            Op("dining_front_french_e", false, 0.41f, 16.3f, 17.5f, 0, 2.3f),
            Op("den_front_window", false, 1.02f, 1.3f, 2.9f, 0.9f, 2.2f),
            Op("den_west_window_s", true, 0.09f, 2.8f, 4.0f, 0.9f, 2.2f),
            Op("den_west_window_n", true, 0.09f, 5.5f, 6.7f, 0.9f, 2.2f),
            Op("sunroom_front_window", false, 1.14f, 19.3f, 21.7f, 0.9f, 2.2f),
            Op("sunroom_east_window_s", true, 22.48f, 2.4f, 3.6f, 0.9f, 2.2f),
            Op("sunroom_east_window_m", true, 22.48f, 4.4f, 5.6f, 0.9f, 2.2f),
            Op("sunroom_east_window_n", true, 22.48f, 6.4f, 7.6f, 0.9f, 2.2f),
            Op("foyer_landing_arch_window", false, 11.01f, 9.6f, 11.4f, 3.3f, 5.2f),
        });
        // The survey's arch at Y 7.49-9.25 was a misread wall face; M20 (17:47) shows the cased opening to the
        // breakfast room at the rear end of the foyer's east wall, and the landing of the service stair sits over it.
        openings.RemoveAll(o => o.name == "foyer_breakfast_arch" || o.name == "breakfast_corridor" || o.name == "service_stair_landing_open");
        openings.Add(Op("foyer_breakfast_door", true, 13.23f, 9.8f, 11.0f, 0, 2.1f));
        foreach (var o in openings) if (o.name.Contains("window") && o.sill < 0.01f) { o.sill = SurveyHouse.WindowSill; }

        var ground = Child(root, "Ground");
        float area = 0;
        var rearZone = new HashSet<string> { "service_stair_bay", "breakfast", "breakfast_extension", "kitchen" };
        foreach (var r in rooms)
        {
            bool sub = r.name == "vestibule" || r.name == "fireplace_recess";
            if (!sub) area += r.W * r.D;
            if (rearZone.Contains(r.name)) continue;   // one open volume, built below
            BuildRoom(ground, r, 0f, ceil, openings.Where(o => o.name != "foyer_landing_arch_window").ToList(), floor: !sub || r.name == "fireplace_recess", walls: true,
                      ceiling: r.name != "foyer", matFloor);
        }
        RearZone(ground, rooms, openings, ceil);
        // Behind the foyer's rear arch Marina models nothing; Muto suggests a bathroom, and the real house
        // has a powder room there. Authored adaptation, sized to the breakfast rear wall line.
        BuildRoom(ground, new Rect { name = "powder_room_adaptation", x0 = 9.3f, x1 = 11.6f, y0 = 11.17f, y1 = 12.64f }, 0f, ceil, openings, true, true, true, matFloor);
        float surveyArea = (float)g["interior_area_m2"];
        Debug.Log($"Ground interior {area:F1} m2 vs survey {surveyArea:F1} m2");
        if (Mathf.Abs(area - surveyArea) / surveyArea > 0.01f) Debug.LogWarning("Ground floor area drifted from the survey by >1%.");

        // Stairs as ramps so the house is walkable. Main stair: foyer west wall, foot Y 3.7 -> landing Y 7.9 at +3.0 m.
        float upperFloorY = ceil + SurveyHouse.FloorStructure;
        Ramp(ground, "MainStairRamp", 9.12f, 10.4f, 3.7f, 7.9f, 0f, upperFloorY, matStair);
        var foyerRect = rooms.First(r => r.name == "foyer");
        var stairWell = new Rect { name = "main_stair_well", x0 = 9.12f, x1 = 10.4f, y0 = 4.4f, y1 = 7.9f };
        var foyerCeil = Child(ground, "foyer_ceiling"); FloorWithHole(foyerCeil, foyerRect, stairWell, ceil + 0.1f, matCeil);

        Slab(ground, "Site", -10f, 35f, -12f, 28f, -3.3f, 0.05f, matFloor);   // fall-catcher under the exterior model's terrain
        Fixtures(ground, (JObject)g["features"]);

        // ---------- upper floor (stacked per the 2026-09-11 decision) ----------
        // Survey rooms are mirrored/scaled onto the ground frame (SurveyHouse.UpperToGround). The hall is then
        // snapped onto the foyer stair (X 9.12..11.0) and run to Y 11.2 so the main stair arrives in it and the
        // attic flight leaves from its rear end; rooms that overlap the hall are trimmed back to its walls.
        var u = (JObject)j["upper"];
        var hallSnap = new Rect { name = "upper_hall", x0 = 9.12f, x1 = 11.7f, y0 = 0.36f, y1 = 11.2f };
        var upRooms = ReadRooms((JObject)u["rooms"]).Where(r => r.name != "main_stair_well" && r.name != "upper_hall").Select(ToGround)
            .Select(r => TrimAgainst(r, hallSnap)).Where(r => r != null && r.W > 0.8f && r.D > 0.8f).ToList();
        upRooms.Add(hallSnap);
        var hall = hallSnap;
        var well = new Rect { name = "main_stair_well", x0 = 9.12f, x1 = 10.4f, y0 = 4.8f, y1 = 7.9f };
        var upOpen = UpperOpenings(upRooms, SurveyHouse.UpperCeiling);
        var upper = Child(root, "Upper");
        float atticY = upperFloorY + SurveyHouse.UpperCeiling + SurveyHouse.FloorStructure;
        var atticWell = new Rect { name = "attic_stair_well", x0 = 9.12f, x1 = 10.25f, y0 = 8.6f, y1 = 11.0f };
        foreach (var r in upRooms)
        {
            if (r.name == "upper_hall")
            {
                BuildRoom(upper, r, upperFloorY, SurveyHouse.UpperCeiling, upOpen.Concat(openings.Where(o => o.name == "foyer_landing_arch_window")).ToList(), floor: false, walls: true, ceiling: false, matUpper, 0f);
                FloorWithHole(upper, r, well, upperFloorY, matUpper);
                // ceiling with the attic well cut out
                var hc = Child(upper, "upper_hall_ceiling"); FloorWithHole(hc, new Rect { name = r.name, x0 = r.x0 - T, x1 = r.x1 + T, y0 = r.y0 - T, y1 = r.y1 + T }, atticWell, upperFloorY + SurveyHouse.UpperCeiling + 0.1f, matCeil);
                // balustrade around the main-stair well
                Box(upper, "WellRail_east", well.x1, well.x1 + 0.08f, well.y0, well.y1, upperFloorY, upperFloorY + 0.95f, matWall);
                Box(upper, "WellRail_south", well.x0, well.x1 + 0.08f, well.y0 - 0.08f, well.y0, upperFloorY, upperFloorY + 0.95f, matWall);
                // attic flight: steep straight run up the west side of the hall's rear end
                Ramp(upper, "AtticStairRamp", atticWell.x0, atticWell.x1, atticWell.y0, atticWell.y1, upperFloorY, atticY, matStair);
                Ramp(upper, "AtticStairRail", atticWell.x1, atticWell.x1 + 0.08f, atticWell.y0, atticWell.y1, upperFloorY + 0.95f, atticY + 0.95f, matWall);
            }
            else BuildRoom(upper, r, upperFloorY, SurveyHouse.UpperCeiling, upOpen, true, true, true, matUpper, 0f);
        }

        // ---------- attic (authored placement over the hall; Marina's attic set has no fixed stacking) ----------
        var a = (JObject)j["attic"];
        float aw = (float)a["room"]["w"], ad = (float)a["room"]["d"];
        var attic = new Rect { name = "attic", x0 = 7.5f, x1 = 7.5f + aw, y0 = 11.5f - ad, y1 = 11.5f };
        var atticGo = Child(root, "Attic");
        BuildRoom(atticGo, attic, atticY, SurveyHouse.AtticCeiling, new List<Opening>(), false, true, true, matAttic, 0f);
        FloorWithHole(atticGo, attic, atticWell, atticY, matAttic);
        Box(atticGo, "WellRail_east", atticWell.x1, atticWell.x1 + 0.08f, atticWell.y0, atticWell.y1, atticY, atticY + 0.95f, matWall);
        Box(atticGo, "WellRail_south", atticWell.x0, atticWell.x1 + 0.08f, atticWell.y0 - 0.08f, atticWell.y0, atticY, atticY + 0.95f, matWall);
        float cx0 = (float)a["chimney"]["x"][0], cx1 = (float)a["chimney"]["x"][1], cd = (float)a["chimney"]["depth_from_rear_wall"];
        Box(atticGo, "Chimney", 7.7f, 7.7f + (cx1 - cx0), attic.y1 - cd, attic.y1, atticY, atticY + SurveyHouse.AtticCeiling, matWall);   // west end, nearest the living-room stack

        // ---------- basement (authored: Marina shows none; Muto places its door off the rear hall) ----------
        // Full basement under the main block, reached by a flight under the main stair, entered from the foyer's
        // rear at Y 7.9 (headroom under the stair soffit is 2.8 m there).
        float baseFloorY = -2.7f, baseH = 2.4f;
        var basement = new Rect { name = "basement", x0 = 4.45f, x1 = 13.07f, y0 = 0.52f, y1 = 10.85f };
        var baseWell = new Rect { name = "basement_stair_well", x0 = 9.12f, x1 = 10.4f, y0 = 3.9f, y1 = 7.9f };
        var baseGo = Child(root, "Basement");
        BuildRoom(baseGo, basement, baseFloorY, baseH, new List<Opening>(), true, true, false, matAttic, 0f);
        var bc = Child(baseGo, "basement_ceiling"); FloorWithHole(bc, new Rect { name = "b", x0 = basement.x0 - T, x1 = basement.x1 + T, y0 = basement.y0 - T, y1 = basement.y1 + T }, baseWell, baseFloorY + baseH + 0.1f, matCeil);
        for (float x = basement.x0 + 2.9f; x < basement.x1 - 1f; x += 2.9f) Box(baseGo, "Column", x - 0.12f, x + 0.12f, 5.5f, 5.74f, baseFloorY, baseFloorY + baseH, matWall);
        // descending flight, frontward under the main stair
        Ramp(baseGo, "BasementStairRamp", baseWell.x0, baseWell.x1, 7.7f, 4.0f, 0f, baseFloorY, matStair);
        // foyer floor hole over it (rebuild the foyer floor), and the spandrel wall + door under the stair
        var foyerGo = root.transform.Find("Ground/foyer").gameObject; var ff = foyerGo.transform.Find("Floor"); if (ff) UnityEngine.Object.DestroyImmediate(ff.gameObject);
        var fh = Child(foyerGo, "FloorWithWell"); FloorWithHole(fh, foyerRect, new Rect { name = "w", x0 = baseWell.x0, x1 = baseWell.x1, y0 = 4.0f, y1 = 7.7f }, 0f, matFloor);
        for (float y = 3.7f; y < 7.9f; y += 0.25f) { float soffit = Mathf.Max(0.05f, upperFloorY * (y - 3.7f) / 4.2f - 0.2f); Box(foyerGo, "Spandrel", 10.4f, 10.5f, y, Mathf.Min(y + 0.25f, 7.9f), 0f, soffit, matWall); }
        Box(foyerGo, "UnderstairFront", 9.12f, 10.5f, 3.7f, 3.75f, 0f, 0.3f, matWall);
        openings.Add(Op("basement_door", false, 7.9f, 9.2f, 10.3f, 0, 2.0f));
        Box(foyerGo, "UnderstairHeader", 9.12f, 10.5f, 7.88f, 7.92f, 2.0f, 2.8f, matWall);

        DetailMaterials();
        DetailFoyer(root, foyerRect, openings, ceil, upperFloorY);
        DetailKitchen(root, rooms, openings, ceil);
        SeparateSharedWalls(root);
        Lighting(root, rooms, upRooms, ceil, upperFloorY);
        Player();
        ExteriorShell.Place(rooms.Where(r => r.name != "vestibule" && r.name != "fireplace_recess").Select(r => (r.x0, r.x1, r.y0, r.y1)).Append((9.3f, 11.6f, 11.17f, 12.64f)).ToArray());

        Directory.CreateDirectory("Assets/Scenes");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        EditorSceneManager.SaveScene(scene, "Assets/Scenes/House.unity");
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene("Assets/Scenes/House.unity", true) };
        AssetDatabase.SaveAssets();
        Debug.Log("House built from survey: Assets/Scenes/House.unity");
        Screenshots();
        WalkCheck();
    }

    // ---------- survey parsing ----------
    static List<Rect> ReadRooms(JObject rooms) => rooms.Properties().Select(p => new Rect {
        name = p.Name, x0 = (float)p.Value["x"][0], x1 = (float)p.Value["x"][1], y0 = (float)p.Value["y"][0], y1 = (float)p.Value["y"][1] }).ToList();

    static List<Opening> ReadOpenings(JObject ops)
    {
        var list = new List<Opening>();
        foreach (var p in ops.Properties())
        {
            string wall = (string)p.Value["wall"];
            bool xWall = wall.StartsWith("x=");
            var o = new Opening { name = p.Name, xWall = xWall, sill = 0, head = SurveyHouse.DoorHead };
            if (xWall) { o.at = (float)p.Value["x_m"]; o.a = (float)p.Value["y_m"][0]; o.b = (float)p.Value["y_m"][1]; }
            else { o.at = (float)p.Value["y_m"]; o.a = (float)p.Value["x_m"][0]; o.b = (float)p.Value["x_m"][1]; }
            if (p.Name.Contains("arch") || p.Name.Contains("cased") || p.Name.Contains("french") || p.Name.Contains("corridor") || p.Name.Contains("double")) o.head = 2.3f;
            list.Add(o);
        }
        return list;
    }
    static Opening Op(string n, bool xWall, float at, float a, float b, float sill, float head) => new Opening { name = n, xWall = xWall, at = at, a = a, b = b, sill = sill, head = head };

    // Cut a room back to the hall's outer wall faces; drop it if the hall swallows it.
    static Rect TrimAgainst(Rect r, Rect hall)
    {
        bool ox = r.x1 > hall.x0 - T && r.x0 < hall.x1 + T, oy = r.y1 > hall.y0 - T && r.y0 < hall.y1 + T;
        if (!(ox && oy)) return r;
        float cx = (r.x0 + r.x1) / 2, hc = (hall.x0 + hall.x1) / 2;
        var t = new Rect { name = r.name, x0 = r.x0, x1 = r.x1, y0 = r.y0, y1 = r.y1 };
        if (cx < hc) t.x1 = Mathf.Min(t.x1, hall.x0 - T); else t.x0 = Mathf.Max(t.x0, hall.x1 + T);
        return t.W > 0.8f ? t : null;
    }
    // Upper-floor frame -> ground frame (mirror + scale), see SurveyHouse.
    static Rect ToGround(Rect r)
    {
        var p = SurveyHouse.UpperToGround(r.x0, r.y0); var q = SurveyHouse.UpperToGround(r.x1, r.y1);
        return new Rect { name = r.name, x0 = Mathf.Min(p.x, q.x), x1 = Mathf.Max(p.x, q.x), y0 = Mathf.Min(p.y, q.y), y1 = Mathf.Max(p.y, q.y) };
    }

    // No upstairs openings are surveyed; connect rooms by adjacency. 'open' pairs are one volume, 'door' pairs get a 0.9 m door.
    static List<Opening> UpperOpenings(List<Rect> rooms, float ceilH)
    {
        var open = new HashSet<string> { "parents_bedroom|parents_bedroom_L", "master_bath|master_bath_L", "girls_room_rear|girls_room_rear_notch" };
        var door = new HashSet<string> { "upper_hall|girls_room_front", "upper_hall|buzz_room", "upper_hall|kevin_jeff_room", "upper_hall|hall_bathroom",
            "upper_hall|girls_room_rear", "upper_hall|linen_closet", "linen_closet|parents_bedroom_L", "master_bath_L|parents_bedroom", "master_bath|parents_bedroom" };
        var list = new List<Opening>();
        for (int i = 0; i < rooms.Count; i++) for (int k = i + 1; k < rooms.Count; k++)
        {
            var A = rooms[i]; var B = rooms[k]; string key = A.name + "|" + B.name, key2 = B.name + "|" + A.name;
            bool isOpen = open.Contains(key) || open.Contains(key2), isDoor = door.Contains(key) || door.Contains(key2);
            if (!isOpen && !isDoor) continue;
            // vertical shared wall?
            foreach (var (la, lb) in new[] { (A.x1, B.x0), (A.x0, B.x1) })
                if (Mathf.Abs(la - lb) <= 0.45f) { float o0 = Mathf.Max(A.y0, B.y0), o1 = Mathf.Min(A.y1, B.y1); if (o1 - o0 > 0.8f) list.Add(Span(key, true, (la + lb) / 2, o0, o1, isOpen, ceilH)); }
            foreach (var (la, lb) in new[] { (A.y1, B.y0), (A.y0, B.y1) })
                if (Mathf.Abs(la - lb) <= 0.45f) { float o0 = Mathf.Max(A.x0, B.x0), o1 = Mathf.Min(A.x1, B.x1); if (o1 - o0 > 0.8f) list.Add(Span(key, false, (la + lb) / 2, o0, o1, isOpen, ceilH)); }
        }
        Debug.Log($"Upper floor: {list.Count} synthetic openings");
        return list;
    }
    static Opening Span(string n, bool xWall, float at, float o0, float o1, bool full, float ceilH)
    {
        if (full) return Op(n, xWall, at, o0, o1, 0, ceilH);
        float c = (o0 + o1) / 2; return Op(n, xWall, at, c - 0.45f, c + 0.45f, 0, SurveyHouse.DoorHead);
    }

    // ---------- geometry ----------
    static void BuildRoom(GameObject parent, Rect r, float floorY, float h, List<Opening> ops, bool floor, bool walls, bool ceiling, Material fm, float wallExtra = SurveyHouse.FloorStructure)
    {
        float wh = h + wallExtra;
        var go = Child(parent, r.name);
        if (floor) Slab(go, "Floor", r.x0, r.x1, r.y0, r.y1, floorY - 0.1f, 0.1f, fm);
        if (ceiling) Slab(go, "Ceiling", r.x0 - T, r.x1 + T, r.y0 - T, r.y1 + T, floorY + h, 0.1f, matCeil);
        if (!walls) return;
        Wall(go, "West", true, r.x0 - T, r.x0, r.y0 - T, r.y1 + T, floorY, wh, ops.Where(o => o.xWall && Mathf.Abs(o.at - r.x0) <= 0.3f));
        Wall(go, "East", true, r.x1, r.x1 + T, r.y0 - T, r.y1 + T, floorY, wh, ops.Where(o => o.xWall && Mathf.Abs(o.at - r.x1) <= 0.3f));
        Wall(go, "Front", false, r.y0 - T, r.y0, r.x0 - T, r.x1 + T, floorY, wh, ops.Where(o => !o.xWall && Mathf.Abs(o.at - r.y0) <= 0.3f));
        Wall(go, "Rear", false, r.y1, r.y1 + T, r.x0 - T, r.x1 + T, floorY, wh, ops.Where(o => !o.xWall && Mathf.Abs(o.at - r.y1) <= 0.3f));
    }

    // Breakfast room + kitchen: one open L-shaped volume (Marina 13:10 overhead; real-house plan). Only
    // exterior and party walls exist; the service stair is an open flight up the west wall to Marina's
    // enclosed landing, behind a handrail rather than a wall.
    static void RearZone(GameObject parent, List<Rect> rooms, List<Opening> ops, float ceilH)
    {
        var go = Child(parent, "BreakfastKitchen"); float h = ceilH + SurveyHouse.FloorStructure;
        Rect k = rooms.First(x => x.name == "kitchen"), b = rooms.First(x => x.name == "breakfast"),
             s = rooms.First(x => x.name == "service_stair_bay"), e = rooms.First(x => x.name == "breakfast_extension");
        foreach (var r in new[] { s, b, e, k })
        {
            Slab(go, "Floor_" + r.name, r.x0, r.x1, r.y0, r.y1, -0.1f, 0.1f, matFloor);
            Slab(go, "Ceiling_" + r.name, r.x0 - T, r.x1 + T, r.y0 - T, r.y1 + T, ceilH, 0.1f, matCeil);
        }
        var none = Enumerable.Empty<Opening>();
        Wall(go, "RearWall_breakfast", false, b.y1, b.y1 + T, s.x0 - T, k.x0 + T, 0, h, ops.Where(o => o.name == "breakfast_rear_window"));
        Wall(go, "WestWall_kitchen", true, k.x0 - T, k.x0, b.y1, k.y1 + T, 0, h, none);
        Wall(go, "RearWall_kitchen", false, k.y1, k.y1 + T, k.x0 - T, k.x1 + T, 0, h, ops.Where(o => o.name.StartsWith("kitchen_back_door") || o.name.StartsWith("kitchen_rear_window")));
        Wall(go, "EastWall_kitchen", true, k.x1, k.x1 + T, k.y0 - T, k.y1 + T, 0, h, ops.Where(o => o.name.StartsWith("window_seat")));
        Wall(go, "SunroomRearWall", false, k.y0 - T, k.y0, e.x1 - T, k.x1 + T, 0, h, ops.Where(o => o.name == "closet_off_breakfast"));
        Wall(go, "SunroomWestWallUpper", true, e.x1 - T, e.x1, b.y0 - T, k.y0, 0, h, none);
        // Thick front wall (survey shows two wall-top bands 6.37-6.53 and 6.68-6.84); this fills the cavity.
        Wall(go, "FrontWall_breakfast", false, b.y0 - 0.31f, b.y0, s.x0 - T, e.x1, 0, h, ops.Where(o => o.name.StartsWith("breakfast_dining")));
        // Closet niche box behind the sunroom rear wall opening.
        Box(go, "ClosetBack", e.x1 - T, 19.25f + T, k.y0 - 0.6f - T, k.y0 - 0.6f, 0, h, matWall);
        Box(go, "ClosetSideE", 19.25f, 19.25f + T, k.y0 - 0.6f, k.y0, 0, h, matWall);   // west side is the sunroom west wall itself
        // Service stair (Marina's overhead: winder at the front, landing platform at the rear; real-house plan
        // agrees): foot at the front end beside the newel, flight rising rearward along the west wall to a
        // landing that spans the rear of the bay at 2.2 m, so the corridor from the foyer passes beneath it.
        // The upper flight turns away from the landing (not modelled; no arrival per Muto).
        float railX = s.x1 - 0.12f, footY = b.y0 + 0.36f, landY = b.y0 + 2.96f, landH = 2.2f;
        Ramp(go, "ServiceStairFlight", s.x0, railX, footY, landY, 0f, landH, matStair);
        Slab(go, "ServiceStairLanding", s.x0, railX, landY, b.y1, landH - 0.2f, 0.2f, matStair);
        Ramp(go, "ServiceStairRail", railX + 0.02f, s.x1, footY, landY, 0.95f, landH + 0.95f, matWall);
        Box(go, "ServiceStairLandingRail", railX + 0.02f, s.x1, landY, b.y1, landH + 0.75f, landH + 0.95f, matWall);
        Box(go, "ServiceStairStringerWall", railX, s.x1, b.y0 + 1.66f, landY, 0, landH, matWall);   // hutch backs onto this
        Box(go, "ServiceStairNewel", railX, s.x1, footY - 0.12f, footY, 0, 1.1f, matUpper);
        Wall(go, "WestWall_stairbay", true, s.x0 - T, s.x0, 11.01f, b.y1 + T, 0, h, none);
    }

    // A wall slab between thickness bounds t0..t1 (X for xWall, else Z), running along s0..s1, cut by openings.
    static void Wall(GameObject parent, string name, bool xWall, float t0, float t1, float s0, float s1, float floorY, float h, IEnumerable<Opening> ops)
    {
        // Partition at every opening edge so vertically stacked/overlapping cuts remain clear.
        var cuts = ops.Where(o => o.b > s0 && o.a < s1 && o.head > 0 && o.sill < h).ToList();
        var xs = cuts.SelectMany(o => new[] { Mathf.Clamp(o.a, s0, s1), Mathf.Clamp(o.b, s0, s1) })
            .Concat(new[] { s0, s1 }).Distinct().OrderBy(v => v).ToArray();
        var ys = cuts.SelectMany(o => new[] { Mathf.Clamp(o.sill, 0, h), Mathf.Clamp(o.head, 0, h) })
            .Concat(new[] { 0f, h }).Distinct().OrderBy(v => v).ToArray();
        for (int x = 0; x < xs.Length - 1; x++)
        for (int y = 0; y < ys.Length - 1; y++)
        {
            float midX = (xs[x] + xs[x + 1]) / 2, midY = (ys[y] + ys[y + 1]) / 2;
            if (cuts.Any(o => midX > o.a && midX < o.b && midY > o.sill && midY < o.head)) continue;
            Seg(parent, name, xWall, t0, t1, xs[x], xs[x + 1], floorY + ys[y], floorY + ys[y + 1]);
        }
    }
    // Two adjacent rooms previously emitted the same full-thickness party wall.
    // Give opposite room faces separate half-slabs; preserve the room-facing planes and total thickness.
    static void SeparateSharedWalls(GameObject root)
    {
        string Side(string name) => name.Split('_')[0];
        var walls = root.GetComponentsInChildren<MeshRenderer>().Where(r =>
            new[] { "West", "East", "Front", "Rear" }.Contains(Side(r.name))).ToArray();
        var split = new System.Collections.Generic.Dictionary<MeshRenderer, (int axis, float min, float max)>();
        for (int i = 0; i < walls.Length; i++)
        for (int j = i + 1; j < walls.Length; j++)
        {
            var a = walls[i]; var b = walls[j];
            string sa = Side(a.name), sb = Side(b.name);
            if (!((sa == "East" && sb == "West") || (sa == "West" && sb == "East") ||
                  (sa == "Front" && sb == "Rear") || (sa == "Rear" && sb == "Front"))) continue;
            int axis = sa == "East" || sa == "West" ? 0 : 2, along = axis == 0 ? 2 : 0;
            var ab = a.bounds; var bb = b.bounds;
            if (Mathf.Min(ab.max[axis], bb.max[axis]) - Mathf.Max(ab.min[axis], bb.min[axis]) < .001f) continue;
            if (Mathf.Min(ab.max.y, bb.max.y) - Mathf.Max(ab.min.y, bb.min.y) < .001f ||
                Mathf.Min(ab.max[along], bb.max[along]) - Mathf.Max(ab.min[along], bb.min[along]) < .001f) continue;
            bool aPositive = sa == "West" || sa == "Front";
            float lo = aPositive ? bb.min[axis] : ab.min[axis], hi = aPositive ? ab.max[axis] : bb.max[axis];
            if (hi <= lo || hi - lo > T + .002f) continue;
            float middle = (lo + hi) / 2;
            split[a] = aPositive ? (axis, middle, hi) : (axis, lo, middle);
            split[b] = aPositive ? (axis, lo, middle) : (axis, middle, hi);
        }
        foreach (var entry in split)
        {
            var wall = entry.Key; var (axis, lo, hi) = entry.Value;
            var size = wall.transform.localScale; var position = wall.transform.position;
            position[axis] = (lo + hi) / 2; size[axis] = hi - lo;
            wall.transform.position = position; wall.transform.localScale = size;
        }
    }

    static void Seg(GameObject p, string n, bool xWall, float t0, float t1, float s0, float s1, float y0, float y1)
    {
        if (xWall) Box(p, n, t0, t1, s0, s1, y0, y1, matWall); else Box(p, n, s0, s1, t0, t1, y0, y1, matWall);
    }
    static void Slab(GameObject p, string n, float x0, float x1, float z0, float z1, float y, float th, Material m) => Box(p, n, x0, x1, z0, z1, y, y + th, m);
    static void FloorWithHole(GameObject p, Rect r, Rect hole, float floorY, Material m)
    {
        float hx0 = Mathf.Max(r.x0, hole.x0), hx1 = Mathf.Min(r.x1, hole.x1), hz0 = Mathf.Max(r.y0, hole.y0), hz1 = Mathf.Min(r.y1, hole.y1);
        if (hz0 > r.y0) Slab(p, "Floor_front", r.x0, r.x1, r.y0, hz0, floorY - 0.1f, 0.1f, m);
        if (hz1 < r.y1) Slab(p, "Floor_rear", r.x0, r.x1, hz1, r.y1, floorY - 0.1f, 0.1f, m);
        if (hx0 > r.x0) Slab(p, "Floor_west", r.x0, hx0, hz0, hz1, floorY - 0.1f, 0.1f, m);
        if (hx1 < r.x1) Slab(p, "Floor_east", hx1, r.x1, hz0, hz1, floorY - 0.1f, 0.1f, m);
    }
    static void Ramp(GameObject p, string n, float x0, float x1, float z0, float z1, float y0, float y1, Material m)
    {
        float len = Mathf.Sqrt((z1 - z0) * (z1 - z0) + (y1 - y0) * (y1 - y0)); float ang = Mathf.Atan2(y1 - y0, z1 - z0) * Mathf.Rad2Deg;
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.name = n; go.transform.parent = p.transform;
        go.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2 - 0.1f, (z0 + z1) / 2);
        go.transform.rotation = Quaternion.Euler(-ang, 0, 0); go.transform.localScale = new Vector3(x1 - x0, 0.2f, len);
        go.GetComponent<Renderer>().sharedMaterial = m; GameObjectUtility.SetStaticEditorFlags(go, (StaticEditorFlags)(-1));
    }
    static void Box(GameObject p, string n, float x0, float x1, float z0, float z1, float y0, float y1, Material m)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.name = n; go.transform.parent = p.transform;
        go.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
        go.transform.localScale = new Vector3(x1 - x0, y1 - y0, z1 - z0);
        go.GetComponent<Renderer>().sharedMaterial = m; GameObjectUtility.SetStaticEditorFlags(go, (StaticEditorFlags)(-1));
    }
    static GameObject Child(GameObject p, string n) { var go = new GameObject(n); go.transform.parent = p.transform; return go; }

    // Surveyed fixed elements as massing boxes (heights are standard, positions from the survey).
    static void Fixtures(GameObject parent, JObject f)
    {
        var fx = Child(parent, "Fixtures"); const float counter = 0.92f, depth = 0.62f;
        float[] ilx = F(f["island_long_leg_x"]), ily = F(f["island_y"]), ifx = F(f["island_L_foot"]), ify = F(f["island_L_y"]);
        Box(fx, "IslandLongLeg", ilx[0], ilx[1], ily[0], ily[1], 0, counter, matWall);
        Box(fx, "IslandLFoot", ifx[0], ifx[1], ify[0], ify[1], 0, counter, matWall);
        // Rear-wall counter run with the sink under the window; fridge at the east end.
        Box(fx, "RearCounter", 18.7f, 21.6f, 16.74f - depth, 16.74f, 0, counter, matWall);
        Box(fx, "Fridge", 21.7f, 22.5f, 16.0f, 16.74f, 0, 1.8f, matStair);
        // East wall: two window seats with counters between (survey: seats centred Y 14.3 and 12.0).
        Box(fx, "WindowSeat1", 22.51f - 0.55f, 22.51f, 13.8f, 14.8f, 0, 0.45f, matStair);
        Box(fx, "WindowSeat2", 22.51f - 0.55f, 22.51f, 11.5f, 12.5f, 0, 0.45f, matStair);
        Box(fx, "EastCounterA", 22.51f - depth, 22.51f, 14.8f, 16.0f, 0, counter, matWall);
        Box(fx, "EastCounterB", 22.51f - depth, 22.51f, 12.5f, 13.8f, 0, counter, matWall);
        Box(fx, "EastCounterC", 22.51f - depth, 22.51f, 8.9f, 11.5f, 0, counter, matWall);
        float[] bt = F(f["breakfast_table"]), dt = F(f["dining_table"]);
        Box(fx, "BreakfastTable", bt[0] - 0.5f, bt[0] + 0.5f, bt[1] - 1.0f, bt[1] + 1.0f, 0.72f, 0.76f, matUpper);
        Box(fx, "DiningTable", dt[0] - 0.55f, dt[0] + 0.55f, dt[1] - 1.2f, dt[1] + 1.2f, 0.72f, 0.76f, matUpper);
        Box(fx, "Hutch", 14.42f, 14.87f, 8.6f, 10.4f, 0, 2.1f, matWall);              // on the stair stringer wall, facing the table (M18/M23)
        Box(fx, "Desk", 18.54f - 0.55f, 18.54f, 7.9f, 8.6f, 0.72f, 0.76f, matUpper);       // against the sunroom's west wall, facing west (M15)
        float[] fp = F(f["living_fireplace"]);
        Box(fx, "FireplaceMantel", fp[0] - 0.9f, fp[0] + 0.9f, 9.35f - 0.2f, 9.35f, 0, 1.3f, matWall);
    }
    static float[] F(JToken t) => t.Select(v => (float)v).ToArray();

    // ---------- materials, lighting, player ----------
    static void MakeMaterials()
    {
        Directory.CreateDirectory("Assets/Materials");
        matFloor = Mat("Floor", new Color(0.55f, 0.42f, 0.30f)); matWall = Mat("Wall", new Color(0.85f, 0.82f, 0.74f));
        matCeil = Mat("Ceiling", new Color(0.92f, 0.92f, 0.90f)); matUpper = Mat("UpperFloor", new Color(0.45f, 0.36f, 0.28f));
        matAttic = Mat("Attic", new Color(0.50f, 0.45f, 0.38f)); matStair = Mat("Stair", new Color(0.55f, 0.12f, 0.12f));
    }
    static Material Mat(string n, Color c)
    {
        string path = $"Assets/Materials/{n}.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("HDRP/Lit")); AssetDatabase.CreateAsset(m, path); }
        m.SetColor("_BaseColor", c); m.SetFloat("_Smoothness", 0.25f); return m;
    }
    static void Lighting(GameObject root, List<Rect> ground, List<Rect> upper, float ceil, float upperFloorY)
    {
        var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.transform.parent = root.transform;
        sun.transform.rotation = Quaternion.Euler(45f, -35f, 0); sun.intensity = 20000f; sun.shadows = LightShadows.Soft; sun.gameObject.AddComponent<HDAdditionalLightData>();
        var lights = Child(root, "RoomLights");
        foreach (var r in ground) RoomLight(lights, r, ceil - 0.3f);
        foreach (var (n, x, z, lm) in new[] { ("island", 20.2f, 13.3f, 3500f), ("sink", 20.2f, 16.0f, 2500f), ("breakfast_pendant", 16.45f, 9.5f, 3000f), ("stair_foot", 14.9f, 7.6f, 1500f) })
        { var l = new GameObject("Light_" + n).AddComponent<Light>(); l.transform.parent = lights.transform; l.transform.position = new Vector3(x, ceil - 0.45f, z); l.type = LightType.Point; l.range = 7f; l.intensity = lm; l.color = new Color(1f, 0.93f, 0.82f); l.gameObject.AddComponent<HDAdditionalLightData>(); }
        RoomLight(lights, new Rect { name = "upper_hall_over_foyer", x0 = 9.12f, x1 = 13.23f, y0 = 0.2f, y1 = 11.01f }, upperFloorY + SurveyHouse.UpperCeiling - 0.3f);
        foreach (var r in upper) RoomLight(lights, r, upperFloorY + SurveyHouse.UpperCeiling - 0.3f);
        float atticFloor = upperFloorY + SurveyHouse.UpperCeiling + SurveyHouse.FloorStructure;
        RoomLight(lights, new Rect { name = "attic_f", x0 = 7.5f, x1 = 12.65f, y0 = 2.4f, y1 = 6.5f }, atticFloor + SurveyHouse.AtticCeiling - 0.3f);
        RoomLight(lights, new Rect { name = "attic_r", x0 = 7.5f, x1 = 12.65f, y0 = 6.5f, y1 = 11.0f }, atticFloor + SurveyHouse.AtticCeiling - 0.3f);
        foreach (var (x, z) in new[] { (6.5f, 3f), (6.5f, 8f), (11f, 3f), (11f, 8f) }) RoomLight(lights, new Rect { name = "basement", x0 = x - 2f, x1 = x + 2f, y0 = z - 2.5f, y1 = z + 2.5f }, -0.6f);

        Directory.CreateDirectory("Assets/Settings");
        var profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, "Assets/Settings/HouseVolume.asset");
        var env = profile.Add<VisualEnvironment>(true); env.skyType.value = (int)SkyType.PhysicallyBased; AssetDatabase.AddObjectToAsset(env, profile);
        var sky = profile.Add<PhysicallyBasedSky>(true); AssetDatabase.AddObjectToAsset(sky, profile);
        var exp = profile.Add<Exposure>(true); exp.mode.value = ExposureMode.Automatic; exp.limitMin.value = 6f; exp.limitMax.value = 12.5f; AssetDatabase.AddObjectToAsset(exp, profile);
        var tone = profile.Add<Tonemapping>(true); tone.mode.value = TonemappingMode.ACES; AssetDatabase.AddObjectToAsset(tone, profile);
        var vol = new GameObject("GlobalVolume").AddComponent<Volume>(); vol.transform.parent = root.transform; vol.isGlobal = true; vol.sharedProfile = profile;
    }
    static void RoomLight(GameObject p, Rect r, float y)
    {
        if (r.W * r.D < 3f) return;
        var l = new GameObject("Light_" + r.name).AddComponent<Light>(); l.transform.parent = p.transform;
        l.transform.position = new Vector3((r.x0 + r.x1) / 2, y, (r.y0 + r.y1) / 2);
        l.type = LightType.Point; l.range = Mathf.Max(r.W, r.D) * 1.2f; l.intensity = 2500f + 120f * r.W * r.D; l.color = new Color(1f, 0.95f, 0.88f);
        l.gameObject.AddComponent<HDAdditionalLightData>();
    }
    static void Player()
    {
        var p = new GameObject("Player"); p.transform.position = SurveyHouse.Spawn;
        var cc = p.AddComponent<CharacterController>(); cc.radius = 0.3f; cc.height = 1.8f; cc.center = new Vector3(0, 0.9f, 0); cc.stepOffset = 0.3f; cc.slopeLimit = 45f;
        var camGo = new GameObject("Camera"); camGo.transform.parent = p.transform; camGo.transform.localPosition = new Vector3(0, 1.65f, 0);
        var cam = camGo.AddComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = 0.05f; camGo.AddComponent<HDAdditionalCameraData>(); camGo.AddComponent<AudioListener>();
        p.AddComponent<FpsController>().cam = camGo.transform;
    }

    // Sweeps the adult capsule (r 0.3, h 1.8) along the ground-floor route against the static colliders.
    // Any blocked segment is logged as an error, so a layout that traps the player fails the build.
    public static void WalkCheck()
    {
        Physics.SyncTransforms();
        var route = new (string, Vector3, Vector3)[] {
            ("vestibule to foyer", P(11.2f, 0.9f), P(11.2f, 6.5f)),
            ("foyer to corridor door", P(11.2f, 6.5f), P(12.9f, 10.4f)),
            ("through corridor under landing", P(12.9f, 10.4f), P(15.2f, 10.9f)),
            ("corridor to behind table", P(15.2f, 10.9f), P(15.3f, 12.0f)),
            ("behind table to kitchen", P(15.3f, 12.0f), P(18.1f, 12.0f)),
            ("kitchen west aisle", P(18.1f, 12.0f), P(18.1f, 15.5f)),
            ("kitchen rear aisle", P(18.1f, 15.5f), P(21.2f, 15.5f)),
            ("kitchen east aisle", P(21.2f, 15.5f), P(21.2f, 10.5f)),
            ("kitchen to table east", P(21.2f, 10.5f), P(17.7f, 11.5f)),
            ("table east side", P(17.7f, 11.5f), P(17.7f, 7.6f)),
            ("breakfast front", P(17.7f, 7.6f), P(15.18f, 7.35f)),
            ("table west aisle past hutch", P(15.18f, 7.35f), P(15.18f, 10.9f)),
            ("french doors to dining", P(17.7f, 7.6f), P(17.7f, 5.0f)),
            ("dining to foyer", P(15.9f, 2.6f), P(11.0f, 2.6f)),
            ("foyer to living", P(11.0f, 2.6f), P(6.6f, 2.7f)),
            ("living to den", P(6.6f, 2.7f), P(2.0f, 2.7f)),
            ("dining to sunroom", P(16.8f, 2.8f), P(20.5f, 2.8f)),
            // vertical circulation: sloped segments run exactly parallel to their ramp, 0.25 m above it
            ("foyer to main stair foot", P(11.0f, 2.6f), P(9.76f, 3.3f)),
            ("main stair up", new Vector3(9.76f, 0.25f, 3.7f), new Vector3(9.76f, 3.25f, 7.9f)),
            ("upper hall rearward", new Vector3(11.1f, 3.05f, 8.2f), new Vector3(11.1f, 3.05f, 10.6f)),
            ("upper hall frontward", new Vector3(11.1f, 3.05f, 8.2f), new Vector3(11.1f, 3.05f, 1.0f)),
            ("landing across to attic side", new Vector3(10.9f, 3.05f, 8.2f), new Vector3(9.68f, 3.05f, 8.2f)),
            ("to attic foot", new Vector3(9.68f, 3.05f, 8.2f), new Vector3(9.68f, 3.05f, 8.45f)),
            ("attic stair up", new Vector3(9.68f, 3.25f, 8.6f), new Vector3(9.68f, 6.1f, 11.0f)),
            ("attic top to side", new Vector3(9.68f, 5.9f, 11.2f), new Vector3(10.9f, 5.9f, 11.2f)),
            ("attic floor", new Vector3(10.9f, 5.9f, 11.2f), new Vector3(10.9f, 5.9f, 3.2f)),
            ("foyer rear to basement door", P(11.2f, 9.5f), P(9.76f, 8.1f)),
            ("basement stair down", new Vector3(9.76f, 0.25f, 7.7f), new Vector3(9.76f, -2.45f, 4.0f)),
            ("basement foot to front", new Vector3(9.76f, -2.65f, 3.6f), new Vector3(6.0f, -2.65f, 2.0f)),
            ("basement floor", new Vector3(6.0f, -2.65f, 2.0f), new Vector3(6.0f, -2.65f, 9.5f)),
        };
        int bad = 0;
        foreach (var (name, a, b) in route)
        {
            var d = b - a; float len = d.magnitude; if (len < 0.01f) continue;
            Vector3 p1 = a + Vector3.up * 0.36f, p2 = a + Vector3.up * 1.5f;   // capsule r 0.3, feet ~6 cm up (stair ramps)
            if (Physics.CapsuleCast(p1, p2, 0.3f, d / len, out var hit, len))
            { Debug.LogError($"WALK CHECK blocked: {name} at {hit.distance:F2} m by {hit.collider.transform.parent?.name}/{hit.collider.name}"); bad++; }
        }
        Debug.Log($"WALK CHECK: {route.Length} segments, {bad} blocked");
    }
    static Vector3 P(float x, float y) => new Vector3(x, 0.02f, y);

    // Eye-level captures so the build can be checked without opening the Editor.
    static void Screenshots()
    {
        var views = new (string, Vector3, Vector3)[] {
            ("kitchen-from-breakfast", new Vector3(15.8f, 1.55f, 9.5f), new Vector3(20.5f, 1.2f, 15.5f)),
            ("foyer-from-entry", new Vector3(11.2f, 1.55f, 1.8f), new Vector3(10.5f, 1.8f, 9.5f)),
            ("living-toward-den", new Vector3(8.5f, 1.55f, 2.6f), new Vector3(1f, 1.2f, 2.6f)),
        };
        var go = new GameObject("ShotCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.fieldOfView = 70f; cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1280, 720, 24); cam.targetTexture = rt;
        string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "../Captures")); Directory.CreateDirectory(dir);
        foreach (var (n, pos, look) in views)
        {
            go.transform.position = pos; go.transform.LookAt(look);
            cam.Render(); RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false); tex.ReadPixels(new UnityEngine.Rect(0, 0, rt.width, rt.height), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(dir, n + ".png"), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
        }
        RenderTexture.active = null; UnityEngine.Object.DestroyImmediate(go); Debug.Log("Captures written to " + dir);
    }
}
