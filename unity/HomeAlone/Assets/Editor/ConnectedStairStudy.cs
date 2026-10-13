using System;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    const string ConnectedStudyScene = "Assets/Scenes/ConnectedStairStudy.unity";
    const float ServiceX = 13.44f, ServiceWidth = 1.18f, ServiceFoot = 10.6f;
    const float ServiceEast = ServiceX + ServiceWidth;

    [MenuItem("HomeAlone/Studies/Build Connected Stair Candidate")]
    public static void BuildConnectedStairStudy()
    {
        if (EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)
            throw new InvalidOperationException("Leave Play mode and save the current scene before building the study.");
        EditorSceneManager.OpenScene(StairStudyScene);
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ConnectedStudyScene);
        Material M(string n) => AssetDatabase.LoadAssetAtPath<Material>($"Assets/Materials/{n}.mat")
            ?? throw new InvalidOperationException("Missing material: " + n);
        mTrim = M("WhiteTrim"); mOak = M("OakFloor"); mCherry = M("DarkCherry"); mRunner = M("CranberryRunner");
        mGlass = M("Glass"); matCeil = M("Ceiling");
        var house = GameObject.Find("House"); var ground = house.transform.Find("Ground");
        var study = Child(house, "ConnectedStairStudy");
        var bk = ground.Find("BreakfastKitchen").gameObject;
        var detail = bk.transform.Find("KitchenDetail");
        void Remove(GameObject p, Func<string, bool> match)
        {
            foreach (var t in p.transform.Cast<Transform>().Where(t => match(t.name)).ToArray())
                UnityEngine.Object.DestroyImmediate(t.gameObject);
        }
        Remove(bk, n => n.StartsWith("ServiceStair") || n == "Ceiling_service_stair_bay" || n.StartsWith("WestWall_stairbay") || n.StartsWith("RearWall_breakfast"));
        Remove(detail.gameObject, n => n.StartsWith("Hutch") || n.Contains("foyer_breakfast_door"));
        foreach (var t in detail.Cast<Transform>().Where(t => t.name == "Casing" &&
            Mathf.Abs(t.position.x - 13.23f) < .01f && t.position.z > 9.7f && t.position.z < 11.2f).ToArray())
            UnityEngine.Object.DestroyImmediate(t.gameObject);
        var r = ReadRooms((JObject)JObject.Parse(File.ReadAllText(SurveyPath))["ground"]["rooms"]).First(x => x.name == "foyer");
        var door = Op("study_foyer_breakfast", true, r.x1, 9.05f, 10.4f, 0, 2.3f);
        // Keep door openings untrimmed until the coupled layout is adopted.
        var dining = ground.Find("dining").gameObject;
        Remove(dining, n => n.StartsWith("Rear"));
        Remove(bk, n => n.StartsWith("FrontWall_breakfast"));
        var diningDoors = new[] { Op("west_dining", false, 6.6f, 14f, 15.2f, 0, 2.3f), Op("east_dining", false, 6.6f, 17.1f, 18.45f, 0, 2.3f) };
        matWall = M("KitchenFloral");
        Wall(bk, "FrontWall_breakfast", false, 6.29f, 6.83f, 13.28f, 18.6f, 0, 3f, diningDoors);
        // Recover Godot's source-visible sequence: hutch, doorway, then stair foot. Metres remain a hypothesis.
        var cream = M("CreamPaint");
        Box(study, "HutchBase", ServiceX, ServiceX + .52f, 7.15f, 8.85f, 0, .9f, cream);
        Box(study, "HutchCounter", ServiceX, ServiceX + .58f, 7.12f, 8.88f, .9f, .94f, cream);
        Box(study, "HutchBack", ServiceX, ServiceX + .06f, 7.15f, 8.85f, 1.25f, 2.45f, cream);
        for (int i = 0; i <= 4; i++) Box(study, "HutchFrame", ServiceX, ServiceX + .35f, 7.15f + i * .425f - .02f, 7.15f + i * .425f + .02f, 1.25f, 2.45f, cream);
        foreach (float y in new[] { 1.25f, 1.85f, 2.45f }) Box(study, "HutchShelf", ServiceX, ServiceX + .35f, 7.13f, 8.87f, y - .02f, y + .02f, cream);
        matWall = M("KitchenFloral");
        Wall(study, "West", true, r.x1, ServiceX, 6.83f, ServiceFoot, 0, 3f, new[] { door });
        // User-approved adaptation: omit the service stair to preserve the parents' suite.
        Box(study, "ClosedServiceBay", r.x1, ServiceEast, ServiceFoot, ServiceFoot + T, 0, 3f, matWall);
        // Source screenshot locates the basement entrance on the bay's breakfast-facing side.
        Wall(study, "BasementBaySide", true, ServiceEast, ServiceEast + T, ServiceFoot, 12.64f, 0, 3f,
            new[] { Op("basement_entry", true, ServiceEast, 11.25f, 12.15f, 0, 2.1f) });
        Box(study, "BasementDoor_DescentPending", ServiceEast + .04f, ServiceEast + .09f, 11.25f, 12.15f, 0, 2.1f, mTrim);
        Slab(study, "ClosedBayCeiling", r.x1, ServiceEast + T, ServiceFoot, 12.64f, 3f, .16f, matCeil);
        Wall(bk, "RearWall_breakfast", false, 12.64f, 12.8f, ServiceEast, 17.5f, 0, 3,
            new[] { Op("breakfast_window", false, 12.64f, 14.7f, 15.4f, .9f, 2.1f) });
        SeparateSharedWalls(house);
        Physics.SyncTransforms();
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ConnectedStudyScene);
        Debug.Log("Interior saved: main stair only; breakfast stair bay closed and invented upstairs connection removed.");
    }
    [MenuItem("HomeAlone/Studies/Check Connected Stairs In Play Mode")]
    public static string CheckConnectedStairStudy()
    {
        if (!EditorApplication.isPlaying || !GameObject.Find("House/ConnectedStairStudy"))
            throw new InvalidOperationException("Open ConnectedStairStudy and enter Play mode first.");
        if (GameObject.Find("House").GetComponentsInChildren<Transform>().Any(t =>
            t.name.StartsWith("ServiceStair") || t.name.Contains("ServiceFlight") || t.name.Contains("ServiceTurn") || t.name == "UpperLink" || t.name == "UpperReturn"))
            throw new InvalidOperationException("Obsolete service stair connection remains.");
        var basement = GameObject.Find("House/ConnectedStairStudy/BasementDoor_DescentPending");
        if (!basement || !basement.GetComponent<Collider>().Raycast(new Ray(new Vector3(15.6f, 1f, 11.7f), Vector3.left), out _, 1.5f))
            throw new InvalidOperationException("Basement entry must face the breakfast room.");
        var loop = new[] {
            new Vector3(11.3f, 0, 9.65f), new Vector3(14.3f, 0, 9.65f), new Vector3(15.1f, 0, 9.65f),
            new Vector3(15.1f, 0, 11.7f), new Vector3(15.1f, 0, 9.65f),
            new Vector3(15.1f, 0, 7.4f), new Vector3(14.6f, 0, 7.4f), new Vector3(14.6f, 0, 5.8f),
            new Vector3(17.6f, 0, 5.8f), new Vector3(17.6f, 0, 7.4f), new Vector3(15.1f, 0, 7.4f),
            new Vector3(15.1f, 0, 9.65f), new Vector3(11.3f, 0, 9.65f)
        };
        return WalkStudyRoute(loop.Concat(loop.Reverse()).ToArray(), "ConnectedStairStudy");
    }

}
