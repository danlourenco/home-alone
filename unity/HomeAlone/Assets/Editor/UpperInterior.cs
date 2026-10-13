using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    const string UpperInteriorScene = "Assets/Scenes/UpperInterior.unity";

    [MenuItem("HomeAlone/Interior/Build Upstairs Layout")]
    public static void BuildUpperInterior()
    {
        if (EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)
            throw new InvalidOperationException("Leave Play mode and save the current scene before building upstairs.");
        EditorSceneManager.OpenScene(ConnectedStudyScene);
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), UpperInteriorScene);
        Material M(string n) => AssetDatabase.LoadAssetAtPath<Material>($"Assets/Materials/{n}.mat")
            ?? throw new InvalidOperationException("Missing material " + n);
        matWall = M("CreamPaint"); matCeil = M("Ceiling"); mOak = M("OakFloor"); mTrim = M("WhiteTrim"); mCherry = M("DarkCherry");
        var house = GameObject.Find("House");
        var upper = Child(house, "UpperInterior");
        // Clockwise registration: X=5.336+0.8*surveyY, Z=11-0.8*surveyX.
        // Uniform scale is a fit hypothesis. Correct mislabelled hall/closet and Buzz/bath boundary.
        Rect R(string n, float x0, float x1, float z0, float z1) => new Rect {name=n,x0=x0,x1=x1,y0=z0,y1=z1};
        var rooms = new[] {
            R("WestBedroom",5.704f,8.99f,6.016f,10.808f),
            R("BuzzBedroom",5.56f,8.99f,.792f,4.16f),
            R("HallBathroom",10.016f,12f,.2f,4.232f),
            R("HallBathroomFront",12f,13.144f,.2f,2.6f),
            R("LinenCloset",12.16f,13.144f,2.76f,4.232f),
            R("KevinBedroom",13.392f,16.808f,.152f,4.28f),
            R("SisterBedroom",13.44f,15.488f,6.016f,10.808f),
            R("SisterBedroomNotch",15.488f,16.168f,8.208f,10.808f),
            R("ParentsEntry",15.648f,17.176f,4.704f,7.984f),
            R("ParentsBedroom",17.176f,20.456f,3.104f,7.984f),
            R("EnsuiteEntry",16.36f,18.6f,8.208f,8.92f),
            R("Ensuite",16.36f,19.776f,8.92f,10.864f),
            R("UpperHall",5.56f,15.648f,4.44f,5.76f)
        };
        var openings = new List<Opening>();
        void Link(string a, string b, bool xWall, float lo, float hi, bool open=false)
        {
            var ra=rooms.First(r=>r.name==a); var rb=rooms.First(r=>r.name==b);
            float at=xWall ? (ra.x1+rb.x0)/2 : (ra.y1+rb.y0)/2;
            openings.Add(Op(a+"_"+b,xWall,at,lo,hi,0,open ? 2.6f : 2.15f));
            // Fill only the threshold between separately traced room faces.
            if (xWall && rb.x0>ra.x1) Slab(upper,"Threshold",ra.x1,rb.x0,lo,hi,StudyUpper-.1f,.1f,mOak);
            if (!xWall && rb.y0>ra.y1) Slab(upper,"Threshold",lo,hi,ra.y1,rb.y0,StudyUpper-.1f,.1f,mOak);
        }
        Link("BuzzBedroom","UpperHall",false,7.8f,8.9f);
        Link("HallBathroom","UpperHall",false,10.5f,11.6f);
        Link("LinenCloset","UpperHall",false,12.27f,13.04f);
        Link("KevinBedroom","UpperHall",false,13.9f,15f);
        Link("UpperHall","WestBedroom",false,7.8f,8.9f);
        Link("UpperHall","SisterBedroom",false,13.9f,15f);
        Link("UpperHall","ParentsEntry",true,4.75f,5.7f);
        Link("ParentsEntry","ParentsBedroom",true,4.704f,7.984f,true);
        Link("ParentsBedroom","EnsuiteEntry",false,17.45f,18.45f);
        Link("EnsuiteEntry","Ensuite",false,16.36f,18.6f,true);
        Link("SisterBedroom","SisterBedroomNotch",true,8.208f,10.808f,true);
        Link("HallBathroom","HallBathroomFront",true,.2f,2.6f,true);
        // An open edge overlooking the stairwell and the side-gallery arrival.
        openings.Add(Op("stair_arrival",false,5.76f,9.15f,13.28f,0,2.6f));
        // Plain window openings; source-specific sash and furnishing work follows layout approval.
        foreach(var n in new[]{"BuzzBedroom","KevinBedroom","HallBathroom"})
        {
            var r=rooms.First(v=>v.name==n); float c=(r.x0+r.x1)/2;
            openings.Add(Op(n+"_window",false,r.y0,c-.55f,c+.55f,.9f,2.2f));
        }
        foreach(var n in new[]{"WestBedroom","SisterBedroom","Ensuite"})
        {
            var r=rooms.First(v=>v.name==n); float c=(r.x0+r.x1)/2;
            openings.Add(Op(n+"_window",false,r.y1,c-.55f,c+.55f,.9f,2.2f));
        }
        openings.Add(Op("parents_window",true,20.456f,4.4f,6.6f,.9f,2.2f));
        foreach(var r in rooms)
            BuildRoom(upper,r,StudyUpper,2.6f,openings,true,true,true,mOak,0);
        var hallFloor=upper.transform.Find("UpperHall/Floor");
        UnityEngine.Object.DestroyImmediate(hallFloor.gameObject);
        FloorWithHole(upper,rooms.First(r=>r.name=="UpperHall"),R("stair_headroom",9.15f,11.64f,5.4f,5.76f),StudyUpper,mOak);
        foreach(var floor in upper.GetComponentsInChildren<MeshRenderer>().Where(r=>r.name=="Floor" || r.name.StartsWith("Floor_")).ToArray())
        {
            var b=floor.bounds;
            Slab(upper,"FloorSoffit",b.min.x,b.max.x,b.min.z,b.max.z,b.min.y-.02f,.02f,matCeil);
            UnityEngine.Object.DestroyImmediate(upper.transform.GetChild(upper.transform.childCount-1).GetComponent<Collider>());
        }
        // Retain the established stairs; shorten the side gallery where the cross-hall takes over.
        var main=house.transform.Find("MainStairStudy").gameObject;
        foreach(var t in main.transform.Cast<Transform>().ToArray())
        {
            var ren=t.GetComponent<Renderer>();
            if(t.name=="Gallery" || t.name=="GallerySoffit" ||
                (t.name=="Baluster" && Mathf.Abs(t.position.y-(StudyUpper+.475f))<.01f) ||
                (t.name=="Handrail" && ren && ren.bounds.min.y>4.2f && ren.bounds.max.z<7.4f))
                UnityEngine.Object.DestroyImmediate(t.gameObject);
        }
        Slab(main,"Gallery",11.64f,13.28f,5.76f,7.26f,StudyUpper-.25f,.25f,mOak);
        Slab(main,"GallerySoffit",11.64f,13.28f,5.76f,7.26f,StudyUpper-.27f,.02f,matCeil);
        StudyGuard(main,new Vector3(11.64f,StudyUpper,5.76f),new Vector3(11.64f,StudyUpper,7.26f));
        StudyGuard(upper,new Vector3(9.15f,StudyUpper,5.4f),new Vector3(11.64f,StudyUpper,5.4f));
        StudyGuard(upper,new Vector3(9.15f,StudyUpper,5.4f),new Vector3(9.15f,StudyUpper,5.76f));
        StudyGuard(upper,new Vector3(11.64f,StudyUpper,5.4f),new Vector3(11.64f,StudyUpper,5.76f));
        var foyer=house.transform.Find("Ground/foyer").gameObject;
        foreach(var t in foyer.transform.Cast<Transform>().Where(t=>t.name=="East" || t.name=="West").ToArray())
            UnityEngine.Object.DestroyImmediate(t.gameObject);
        var g=(JObject)JObject.Parse(File.ReadAllText(SurveyPath))["ground"];
        var ops=ReadOpenings((JObject)g["openings"]);
        ops.RemoveAll(o=>o.name.Contains("breakfast") || o.name.Contains("service_stair"));
        ops.Add(Op("breakfast",true,13.28f,9.05f,10.4f,0,2.3f));
        matWall=M("FoyerDamask");
        foreach(float x in new[]{9.15f,13.28f})
        {
            var side=ops.Where(o=>o.xWall && Mathf.Abs(o.at-x)<.3f).ToList();
            side.Add(Op("upstairs_crosshall",true,x,4.44f,5.76f,StudyUpper,StudyUpper+2.6f));
            Wall(foyer,x<10?"West":"East",true,x<10?x-T:x,x<10?x:x+T,.04f,11.21f,0,5.95f,side);
        }
        SeparateSharedWalls(house); Physics.SyncTransforms();
        Directory.CreateDirectory("Captures/UpperInterior");
        File.WriteAllText("Captures/UpperInterior/layout.json",JsonConvert.SerializeObject(new {registration=new{scale=.8f,xOffset=5.336f,zOffset=11f},rooms},Formatting.Indented));
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),UpperInteriorScene);
        Debug.Log("Upstairs layout saved: clockwise uniform registration, corrected room boundaries, authored hall links; exterior and exact dimensions remain provisional.");
    }

    [MenuItem("HomeAlone/Interior/Check Upstairs Walkthrough")]
    public static string CheckUpperInterior()
    {
        if(!EditorApplication.isPlaying || !GameObject.Find("House/UpperInterior"))
            throw new InvalidOperationException("Open UpperInterior and enter Play mode first.");
        var p=new List<Vector3>{new Vector3(9.76f,0,3.2f),new Vector3(9.76f,StudyLanding,9.2f),new Vector3(12.4f,StudyLanding,9.2f),new Vector3(12.4f,StudyUpper,6.4f),new Vector3(12.4f,StudyUpper,5.1f)};
        void P(float x,float z)=>p.Add(new Vector3(x,StudyUpper,z));
        P(8.35f,4.9f); P(8.35f,7.3f); P(8.35f,4.9f); // west bedroom
        P(8.35f,3f); P(8.35f,4.9f); // Buzz
        P(11.05f,4.9f); P(11.05f,3.5f); P(11.05f,1.5f); P(12.6f,1.5f); P(11.05f,1.5f); P(11.05f,4.9f);
        P(12.65f,5.1f); P(12.65f,3.5f); P(12.65f,5.1f); // linen
        P(14.45f,5.1f); P(14.45f,2.5f); P(14.45f,5.1f); // Kevin
        P(14.45f,7.3f); P(14.45f,9.5f); P(15.8f,9.5f); P(14.45f,9.5f); P(14.45f,5.1f);
        P(16.4f,5.1f); P(18.5f,5.1f); P(17.95f,7.3f); P(17.95f,9.6f); P(17.95f,7.3f); P(18.5f,5.1f); P(16.4f,5.1f); P(12.4f,5.1f);
        P(12.4f,6.4f); p.Add(new Vector3(12.4f,StudyLanding,9.2f)); p.Add(new Vector3(9.76f,StudyLanding,9.2f)); p.Add(new Vector3(9.76f,0,3.2f));
        p.Add(new Vector3(11.3f,0,3.2f)); p.Add(new Vector3(11.3f,0,10.6f));
        return WalkStudyRoute(p.ToArray(),"UpperInterior");
    }
}
