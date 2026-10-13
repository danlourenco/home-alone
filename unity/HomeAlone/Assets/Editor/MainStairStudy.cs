using System;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    const string StairStudyScene = "Assets/Scenes/MainStairStudy.unity";
    const float StudyRise = 0.1675f, StudyLanding = 16 * StudyRise, StudyUpper = 20 * StudyRise;

    [MenuItem("HomeAlone/Studies/Build Main Stair Candidate")]
    public static void BuildMainStairStudy()
    {
        if (EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)
            throw new InvalidOperationException("Leave Play mode and save the current scene before building the study.");
        EditorSceneManager.OpenScene("Assets/Scenes/House.unity");
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), StairStudyScene);
        var root = GameObject.Find("House");
        foreach (string n in new[] { "Upper", "Attic", "Basement" }) root.transform.Find(n)?.gameObject.SetActive(false);
        foreach (string n in new[] { "Ground/foyer", "Ground/foyer_ceiling", "Ground/MainStairRamp", "Ground/FoyerDetail", "Ground/vestibule" })
        {
            var old = root.transform.Find(n); if (old) UnityEngine.Object.DestroyImmediate(old.gameObject);
        }
        Material Existing(string n) => AssetDatabase.LoadAssetAtPath<Material>($"Assets/Materials/{n}.mat")
            ?? throw new InvalidOperationException("Missing material: " + n);
        mDamask = Existing("FoyerDamask"); mOak = Existing("OakFloor"); mTrim = Existing("WhiteTrim");
        mCherry = Existing("DarkCherry"); mRunner = Existing("CranberryRunner"); mGlass = Existing("Glass");
        matWall = mDamask; matCeil = Existing("Ceiling");
        var g = (JObject)JObject.Parse(File.ReadAllText(SurveyPath))["ground"];
        var foyer = ReadRooms((JObject)g["rooms"]).First(r => r.name == "foyer");
        var ops = ReadOpenings((JObject)g["openings"]);
        ops.RemoveAll(o => o.name.Contains("breakfast") || o.name.Contains("service_stair") || o.name.Contains("front_door"));
        ops.AddRange(new[] {
            Op("front", false, .2f, 10.15f, 12.25f, 0, 2.5f),
            Op("rear", false, 11.05f, 10.85f, 11.75f, 0, 2.1f),
            Op("breakfast", true, 13.28f, 9.05f, 10.4f, 0, 2.3f),
            Op("landing_window", false, 11.05f, 9.8f, 12.4f, 3.3f, 5.2f)
        });
        var ground = root.transform.Find("Ground").gameObject;
        BuildRoom(ground, foyer, 0, StudyUpper + 2.6f, ops, true, true, true, mOak, 0);
        var study = Child(root, "MainStairStudy");
        Slab(study, "Gallery", 11.64f, 13.28f, 1.62f, 7.26f, StudyUpper - .25f, .25f, mOak);
        Slab(study, "RearLanding", 9.15f, 13.28f, 8.5f, 11.05f, StudyLanding - .2f, .2f, mOak);
        StudyFlight(study, "Lower", new Vector3(9.15f, 0, 3.7f), 16, .3f, 1.25f, false);
        Wall(study, "VestibulePartition", false, 1.46f, 1.62f, 9.15f, 13.28f, 0, 2.75f,
            new[] { Op("vestibule", false, 1.46f, 9.95f, 12.45f, 0, 2.5f) });
        Box(study, "EntranceDoor", 10.65f, 11.75f, .21f, .26f, 0, 2.5f, mTrim);
        Box(study, "EntranceSidelight", 10.15f, 10.65f, .21f, .24f, 0, 2.5f, mGlass);
        Box(study, "EntranceSidelight", 11.75f, 12.25f, .21f, .24f, 0, 2.5f, mGlass);
        Box(study, "RecessDoor", 10.85f, 11.75f, 11.08f, 11.13f, 0, 2.1f, mTrim);
        // Crosswise rear landing; four forward-facing rises return to the side hall.
        var turn = Child(study, "MainReturnTurn");
        StudyFlight(turn, "Turn", Vector3.zero, 4, .31f, 1.64f, false);
        turn.transform.position = new Vector3(13.28f, StudyLanding, 8.5f);
        turn.transform.rotation = Quaternion.Euler(0, 180, 0);
        StudyGuard(study, new Vector3(11.64f, StudyUpper, 1.62f), new Vector3(11.64f, StudyUpper, 7.26f));
        StudyGuard(study, new Vector3(10.4f, StudyLanding, 8.5f), new Vector3(11.64f, StudyLanding, 8.5f));
        // Plain white soffits establish the enclosed volume; decorative trim remains deferred.
        Slab(study, "LandingSoffit", 9.15f, 13.28f, 8.5f, 11.05f, StudyLanding - .22f, .02f, matCeil);
        Slab(study, "GallerySoffit", 11.64f, 13.28f, 1.62f, 7.26f, StudyUpper - .27f, .02f, matCeil);
        matWall = mDamask;
        Wall(study, "RearArch", false, 8.5f, 8.66f, 10.4f, 13.28f, 0, StudyLanding - .22f,
            new[] { Op("recess", false, 8.5f, 10.65f, 12.05f, 0, 2.4f) });
        for (int i = 0; i < 24; i++)
        {
            float x0 = 10.65f + i * 1.4f / 24, x1 = x0 + 1.4f / 24;
            float u = ((x0 + x1) / 2 - 11.35f) / .7f;
            float head = 2.15f + .25f * Mathf.Sqrt(Mathf.Max(0, 1 - u * u));
            Box(study, "ArchCurve", x0, x1, 8.5f, 8.66f, head, 2.4f, mDamask);
        }
        // A continuous triangular spandrel replaces the stepped side silhouette.
        var mesh = new Mesh { name = "Main stair spandrel" };
        mesh.vertices = new[] { new Vector3(10.4f,0,3.7f), new Vector3(10.4f,0,8.5f), new Vector3(10.4f,2.56f,8.5f),
            new Vector3(10.5f,0,3.7f), new Vector3(10.5f,0,8.5f), new Vector3(10.5f,2.56f,8.5f) };
        mesh.triangles = new[] {0,2,1,3,4,5,0,1,4,0,4,3,1,2,5,1,5,4,2,0,3,2,3,5}; mesh.triangles = mesh.triangles.Reverse().ToArray(); mesh.RecalculateNormals();
        const string meshPath = "Assets/Materials/MainStairSpandrel.asset";
        var savedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
        if (savedMesh) { EditorUtility.CopySerialized(mesh, savedMesh); UnityEngine.Object.DestroyImmediate(mesh); mesh = savedMesh; }
        else AssetDatabase.CreateAsset(mesh, meshPath);
        var spandrel = Child(study, "StairEnclosureBase");
        spandrel.AddComponent<MeshFilter>().sharedMesh = mesh;
        spandrel.AddComponent<MeshRenderer>().sharedMaterial = mTrim;
        spandrel.AddComponent<MeshCollider>().sharedMesh = mesh;
        Box(study, "WindowGlass", 9.8f, 12.4f, 11.055f, 11.065f, 3.3f, 5.2f, mGlass);
        AssetDatabase.SaveAssets();
        var player = GameObject.Find("Player"); player.transform.position = SurveyHouse.Spawn;
        SeparateSharedWalls(root);
        Physics.SyncTransforms();
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), StairStudyScene);
        Debug.Log("STAIR STUDY built: main flight + rear landing + east turn; upper level 3.35 m. Other upper storeys disabled in this study only.");
    }

    static void StudyFlight(GameObject parent, string name, Vector3 start, int count, float tread, float width, bool east)
    {
        var flight = Child(parent, name);
        for (int i = 0; i < count; i++)
        {
            float a = i * tread, b = (i + 1) * tread, top = start.y + (i + 1) * StudyRise;
            float x0 = start.x + (east ? a : 0), x1 = start.x + (east ? b : width);
            float z0 = start.z + (east ? 0 : a), z1 = start.z + (east ? width : b);
            Box(flight, "Step", x0, x1, z0, z1, start.y, top, mTrim);
            // Finish meshes are visual; the precise riser/tread boxes supply collision.
            Box(flight, "Tread", x0, x1, z0, z1, top, top + .015f, mCherry);
            UnityEngine.Object.DestroyImmediate(flight.transform.GetChild(flight.transform.childCount - 1).GetComponent<Collider>());
            Box(flight, "Runner", x0 + (east ? 0 : .25f), x1 - (east ? 0 : .25f), z0 + (east ? .25f : 0), z1 - (east ? .25f : 0), top + .015f, top + .02f, mRunner);
            UnityEngine.Object.DestroyImmediate(flight.transform.GetChild(flight.transform.childCount - 1).GetComponent<Collider>());
        }
        var aRail = start + (east ? Vector3.zero : Vector3.right * width);
        var bRail = aRail + (east ? Vector3.right : Vector3.forward) * (count * tread) + Vector3.up * (count * StudyRise);
        StudyGuard(parent, aRail, bRail);
        if (east) StudyGuard(parent, aRail + Vector3.forward * width, bRail + Vector3.forward * width);
    }

    static void StudyGuard(GameObject p, Vector3 a, Vector3 b)
    {
        int n = Mathf.Max(1, Mathf.CeilToInt(Vector3.Distance(a, b) / .16f));
        for (int i = 0; i <= n; i++)
        {
            Vector3 v = Vector3.Lerp(a, b, i / (float)n);
            Box(p, "Baluster", v.x - .02f, v.x + .02f, v.z - .02f, v.z + .02f, v.y, v.y + .95f, mTrim);
        }
        var rail = GameObject.CreatePrimitive(PrimitiveType.Cube); rail.name = "Handrail"; rail.transform.parent = p.transform;
        rail.transform.position = (a + b) / 2 + Vector3.up * .95f;
        rail.transform.rotation = Quaternion.LookRotation(b - a);
        rail.transform.localScale = new Vector3(.075f, .065f, Vector3.Distance(a, b));
        rail.GetComponent<Renderer>().sharedMaterial = mCherry;
    }
    [MenuItem("HomeAlone/Studies/Check Main Stair In Play Mode")]
    public static string CheckMainStairStudy()
    {
        if (!EditorApplication.isPlaying || !GameObject.Find("House/MainStairStudy"))
            throw new InvalidOperationException("Open MainStairStudy and enter Play mode first.");
        // Full continuous round trip, including return downstairs and the passage below the landing.
        var route = new[] {
            new Vector3(10.4f, 0, .9f), new Vector3(10.4f, 0, 2f),
            new Vector3(12f, 0, 2f), new Vector3(12f, 0, .9f), new Vector3(11.3f, 0, 2f),
            new Vector3(9.76f, 0, 3.2f), new Vector3(9.76f, StudyLanding, 9.2f),
            new Vector3(12.4f, StudyLanding, 9.2f), new Vector3(12.4f, StudyUpper, 6.8f),
            new Vector3(12.4f, StudyUpper, 2f), new Vector3(12.4f, StudyUpper, 6.8f),
            new Vector3(12.4f, StudyLanding, 9.2f), new Vector3(9.76f, StudyLanding, 9.2f),
            new Vector3(9.76f, 0, 3.2f), new Vector3(11.3f, 0, 3.2f),
            new Vector3(11.3f, 0, 10.6f), new Vector3(9.75f, 0, 10.6f), new Vector3(11.3f, 0, 10.6f)
        };
        return WalkStudyRoute(route, "MainStairStudy");
    }

    static string WalkStudyRoute(Vector3[] route, string outputFolder)
    {
        var fps = GameObject.Find("Player").GetComponent<FpsController>();
        var cc = fps.GetComponent<CharacterController>();
        var original = fps.transform.position; bool enabled = fps.enabled;
        var log = new System.Text.StringBuilder(); int failures = 0;
        try
        {
            var rearWall = GameObject.Find("House/Ground/foyer").GetComponentsInChildren<Collider>()
                .Where(c => c.name == "Rear").ToArray();
            foreach (var sample in new[] { (y: 1f, solid: false), (y: 2.9f, solid: true), (y: 4f, solid: false) })
            {
                var ray = new Ray(new Vector3(11.3f, sample.y, 10.5f), Vector3.forward);
                bool hit = rearWall.Any(c => c.Raycast(ray, out _, 1f));
                if (hit != sample.solid) throw new InvalidOperationException($"Rear wall opening failed at height {sample.y}");
            }
            log.AppendLine("PASS stacked rear door/window openings and solid wall between them.");
            var shared = GameObject.Find("House/Ground").GetComponentsInChildren<MeshRenderer>()
                .Where(w => (w.name.StartsWith("East") || w.name.StartsWith("West")) &&
                    w.bounds.min.z < 4 && w.bounds.max.z > 4 && w.bounds.min.y < 1.4f && w.bounds.max.y > 1.4f &&
                    w.bounds.min.x >= 13.279f && w.bounds.max.x <= 13.441f).ToArray();
            if (shared.Length != 2 || Mathf.Abs(shared.Sum(w => w.bounds.size.x) - .16f) > .002f ||
                shared.Count(w => Mathf.Abs(w.bounds.min.x - 13.28f) < .001f) != 1)
                throw new InvalidOperationException("Shared foyer/dining wall faces still overlap or thickness changed.");
            log.AppendLine("PASS shared foyer/dining wall: one visible face per room, total thickness 0.16 m.");
            var enclosureRay = new Ray(new Vector3(11.3f, .4f, 6f), Vector3.left);
            if (!GameObject.Find("House/MainStairStudy").GetComponentsInChildren<Collider>()
                .Any(c => c.name == "StairEnclosureBase" && c.Raycast(enclosureRay, out _, 1.2f)))
                throw new InvalidOperationException("Missing solid main-stair enclosure below the flight.");
            log.AppendLine("PASS solid main-stair enclosure below the flight.");
            fps.enabled = false; cc.enabled = false; fps.transform.position = new Vector3(11.2f, .05f, 2.0f); cc.enabled = true;
            Physics.SyncTransforms();
            for (int i = 0; i < 120; i++) fps.TickMotion(Vector3.zero, false, false, 1f / 60);
            foreach (var target in route)
            {
                bool reached = false;
                for (int i = 0; i < 900; i++)
                {
                    var delta = target - fps.transform.position; delta.y = 0;
                    if (delta.magnitude < .06f) { reached = true; break; }
                    fps.TickMotion(delta, false, false, 1f / 60);
                    if (fps.transform.position.y < -.3f) break;
                }
                for (int i = 0; i < 90; i++) fps.TickMotion(Vector3.zero, false, false, 1f / 60);
                bool pass = reached && Mathf.Abs(fps.transform.position.y - target.y) < .13f && cc.isGrounded;
                if (!pass) failures++;
                log.AppendLine($"{(pass ? "PASS" : "FAIL")} target {target} actual {fps.transform.position} grounded={cc.isGrounded}");
                if (!pass) break;
            }
            log.AppendLine($"STAIR STUDY: {failures} failures; real FpsController.TickMotion + CharacterController, 60 Hz, gravity enabled, no jumps.");
            Directory.CreateDirectory("Captures/" + outputFolder);
            File.WriteAllText("Captures/" + outputFolder + "/traversal.txt", log.ToString());
            if (failures > 0) throw new InvalidOperationException(log.ToString());
            Debug.Log(log.ToString()); return log.ToString();
        }
        finally { cc.enabled = false; fps.transform.position = original; cc.enabled = true; fps.enabled = enabled; }
    }

}
