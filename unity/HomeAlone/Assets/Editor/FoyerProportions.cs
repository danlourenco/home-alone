using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    // Trial dimensions, not measurements. Adjust this blockout before registering bedrooms again.
    const float TrialFlightWidth = 1.5f, TrialHallWidth = 1.8f;
    const float TrialOpeningFront = 5.05f; // Headroom-derived trial edge, not an image measurement.
    const string ProportionScene = "Assets/Scenes/FoyerProportions.unity";

    [MenuItem("HomeAlone/Interior/Build Foyer Proportions")]
    public static void BuildFoyerProportions()
    {
        if (EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)
            throw new InvalidOperationException("Leave Play mode and save the scene before building the blockout.");
        EditorSceneManager.OpenScene(ConnectedStudyScene);
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ProportionScene);
        var house = GameObject.Find("House");
        var main = house.transform.Find("MainStairStudy");
        Material Neutral(string name, Color color)
        {
            string path = "Assets/Materials/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (!material)
            {
                material = new Material(AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/WhiteTrim.mat"));
                material.name = name; material.SetColor("_BaseColor", color);
                AssetDatabase.CreateAsset(material, path);
            }
            return material;
        }
        var wall = Neutral("BlockoutWall",new Color(.72f,.72f,.69f));
        var floor = Neutral("BlockoutFloor",new Color(.28f,.32f,.34f));
        mCherry = floor; mTrim = wall;
        var lower = main.Find("Lower");
        float factor = TrialFlightWidth / 1.25f;
        lower.localScale = new Vector3(factor,1,1);
        lower.position = new Vector3(9.15f*(1-factor),0,0);
        main.Find("StairEnclosureBase").position += Vector3.right*(TrialFlightWidth-1.25f);
        main.Find("MainReturnTurn").localScale = new Vector3(TrialHallWidth/1.64f,1,1);
        float inner = 13.28f-TrialHallWidth, flightEdge=9.15f+TrialFlightWidth;
        foreach (var t in main.Cast<Transform>().ToArray())
        {
            if (t.name=="Handrail" || t.name=="Baluster") UnityEngine.Object.DestroyImmediate(t.gameObject);
            else if (t.name=="Gallery" || t.name=="GallerySoffit")
            {
                var p=t.position; p.x=(inner+13.28f)/2; p.z=(TrialOpeningFront+7.26f)/2; t.position=p;
                var scale=t.localScale; scale.x=TrialHallWidth; scale.z=7.26f-TrialOpeningFront; t.localScale=scale;
            }
        }
        // Full-width front floor replaces the oversized void; the side gallery starts at its rear edge.
        Slab(main.gameObject,"FrontUpperFloor",9.15f,13.28f,.2f,TrialOpeningFront,StudyUpper-.25f,.25f,floor);
        Slab(main.gameObject,"FrontFoyerCeiling",9.15f,13.28f,.2f,TrialOpeningFront,StudyUpper-.27f,.02f,wall);
        StudyGuard(main.gameObject,new Vector3(9.15f,StudyUpper,TrialOpeningFront),new Vector3(inner,StudyUpper,TrialOpeningFront));
        StudyGuard(main.gameObject,new Vector3(flightEdge,0,3.7f),new Vector3(flightEdge,StudyLanding,8.5f));
        StudyGuard(main.gameObject,new Vector3(inner,StudyUpper,TrialOpeningFront),new Vector3(inner,StudyUpper,7.26f));
        StudyGuard(main.gameObject,new Vector3(flightEdge,StudyLanding,8.5f),new Vector3(inner,StudyLanding,8.5f));
        // Remove furniture/detail distractions while retaining ground-room collision boundaries.
        foreach(var t in house.GetComponentsInChildren<Transform>().Where(t=>t.name.EndsWith("Detail") || t.name.StartsWith("Hutch")).ToArray())
            t.gameObject.SetActive(false);
        foreach(var r in house.GetComponentsInChildren<MeshRenderer>())
        {
            if(r.sharedMaterial && r.sharedMaterial.name=="Glass") continue;
            r.sharedMaterial = r.name.Contains("Floor") || r.name=="Tread" || r.name=="Runner" || r.name=="Handrail" || r.name=="Gallery" || r.name=="RearLanding" ? floor : wall;
        }
        Physics.SyncTransforms(); AssetDatabase.SaveAssets();
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ProportionScene);
        Debug.Log("Plain foyer trial: main flight 1.50 m, side hall 1.80 m; original 2.68/3.35 m levels retained provisionally. Rejected upstairs fit is absent.");
    }

    const string CentralHallScene = "Assets/Scenes/CentralHall.unity";
    const float HallFront = 3.15f; // 1.90 m to the established opening edge; no floor or stair changes.

    [MenuItem("HomeAlone/Interior/Build Central Hall")]
    public static void BuildCentralHall()
    {
        if (EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)
            throw new InvalidOperationException("Leave Play mode and save the scene before building the central hall.");
        EditorSceneManager.OpenScene(ProportionScene);
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), CentralHallScene);
        var core = Child(GameObject.Find("House"), "CentralHall");
        matWall = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/BlockoutWall.mat");
        if (!matWall) throw new InvalidOperationException("Build Foyer Proportions first.");
        // Reuse the existing full-width floor and enclosing foyer walls, avoiding duplicate room shells.
        // Bathroom occupies the front-centre in an L around the linen closet; dimensions remain a trial.
        Wall(core, "BathroomAndLinenHallWall", false, HallFront-T, HallFront, 9.15f, 13.28f, StudyUpper, 2.6f,
            new[] { Op("bathroom_entry", false, HallFront, 10.3f, 11.3f, 0, 2.15f),
                    Op("linen_entry", false, HallFront, 12.15f, 13.15f, 0, 2.15f) });
        Box(core, "LinenSide", 11.9f, 12.06f, 1.63f, HallFront-T, StudyUpper, StudyUpper+2.6f, matWall);
        Box(core, "LinenFront", 12.06f, 13.28f, 1.63f, 1.79f, StudyUpper, StudyUpper+2.6f, matWall);
        Physics.SyncTransforms();
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), CentralHallScene);
        Debug.Log("Central hall saved: 1.90 m wall-to-opening depth, 1.00 m bathroom and linen openings. Main stairs and front floor unchanged; no bedrooms added.");
    }

    [MenuItem("HomeAlone/Interior/Check Central Hall")]
    public static string CheckCentralHall()
    {
        if (!EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().path != CentralHallScene)
            throw new InvalidOperationException("Open CentralHall and enter Play mode.");
        // Check both sides of the cross-hall, not just a centre line that could mask another pinch.
        var route = new[] {
            new Vector3(9.9f,0,3.2f),new Vector3(9.9f,StudyLanding,9.3f),
            new Vector3(12.4f,StudyLanding,9.3f),new Vector3(12.4f,StudyUpper,6.7f),
            new Vector3(12.7f,StudyUpper,3.65f),new Vector3(9.65f,StudyUpper,3.65f),
            new Vector3(9.65f,StudyUpper,4.55f),new Vector3(12.7f,StudyUpper,4.55f),
            new Vector3(10.8f,StudyUpper,4.05f),new Vector3(10.8f,StudyUpper,2.4f),
            new Vector3(10.8f,StudyUpper,.85f),new Vector3(12.65f,StudyUpper,.85f),
            new Vector3(10.8f,StudyUpper,.85f),new Vector3(10.8f,StudyUpper,4.05f),
            new Vector3(12.65f,StudyUpper,4.05f),new Vector3(12.65f,StudyUpper,2.35f),
            new Vector3(12.65f,StudyUpper,4.05f),new Vector3(12.4f,StudyUpper,6.7f),
            new Vector3(12.4f,StudyLanding,9.3f),new Vector3(9.9f,StudyLanding,9.3f),
            new Vector3(9.9f,0,3.2f),new Vector3(11.35f,0,3.2f),new Vector3(11.35f,0,10.6f)
        };
        return WalkStudyRoute(route,"CentralHall");
    }

    [MenuItem("HomeAlone/Interior/Check Foyer Proportions")]
    public static string CheckFoyerProportions()
    {
        if (!EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().path != ProportionScene)
            throw new InvalidOperationException("Open FoyerProportions and enter Play mode.");
        if(GameObject.Find("House/UpperInterior")) throw new InvalidOperationException("Rejected upstairs fit is still active.");
        var gallery=GameObject.Find("House/MainStairStudy/Gallery").GetComponent<Renderer>().bounds;
        if(Mathf.Abs(gallery.size.x-TrialHallWidth)>.001f) throw new InvalidOperationException("Wrong trial hall width.");
        var ceiling=GameObject.Find("House/MainStairStudy/FrontFoyerCeiling").GetComponent<Collider>();
        float minimum=float.PositiveInfinity;
        // Sample across every covered step, including just before the opening edge.
        for(float z=3.71f;z<TrialOpeningFront;z+=.01f)
        {
            float treadTop=(Mathf.Floor((z-3.7f)/.3f)+1)*StudyRise+.02f;
            if(!ceiling.Raycast(new Ray(new Vector3(9.9f,treadTop,z),Vector3.up),out var hit,4f))
                throw new InvalidOperationException("Front ceiling missing above covered flight.");
            minimum=Mathf.Min(minimum,hit.distance);
        }
        if(minimum<2.1f) throw new InvalidOperationException($"Insufficient stair headroom: {minimum:F3} m");
        Debug.Log($"Front opening at Z {TrialOpeningFront:F2}; minimum sampled vertical headroom {minimum:F3} m.");
        // Exercises ascent/descent plus the usable width of the hall and broad rear landing.
        var route=new[] {
            new Vector3(9.9f,0,3.2f),new Vector3(9.9f,StudyLanding,9.3f),
            new Vector3(12.4f,StudyLanding,9.3f),new Vector3(12.4f,StudyUpper,6.7f),
            new Vector3(11.9f,StudyUpper,6.5f),new Vector3(11.9f,StudyUpper,4.5f),
            new Vector3(9.6f,StudyUpper,4.5f),new Vector3(9.6f,StudyUpper,.8f),
            new Vector3(12.85f,StudyUpper,.8f),new Vector3(11.9f,StudyUpper,2f),
            new Vector3(12.85f,StudyUpper,2f),new Vector3(12.85f,StudyUpper,6.5f),
            new Vector3(12.4f,StudyUpper,6.7f),new Vector3(12.4f,StudyLanding,9.3f),
            new Vector3(9.9f,StudyLanding,9.3f),new Vector3(9.9f,0,3.2f),
            new Vector3(11.35f,0,3.2f),new Vector3(11.35f,0,10.6f)
        };
        return WalkStudyRoute(route,"FoyerProportions");
    }
}
