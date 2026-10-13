using System;
using System.IO;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

public static class BuzzProportionPOC
{
    const string ScenePath="Assets/Scenes/BuzzProportionPOC.unity";
    static Material Finish(string name,Color color)
    {
        const string folder="Assets/Materials/BuzzPOC";
        if(!AssetDatabase.IsValidFolder(folder))AssetDatabase.CreateFolder("Assets/Materials","BuzzPOC");
        string path=folder+"/"+name+".mat";
        var m=AssetDatabase.LoadAssetAtPath<Material>(path);
        if(!m){m=new Material(Shader.Find("HDRP/Unlit"));AssetDatabase.CreateAsset(m,path);}
        m.SetColor("_UnlitColor",color);HDMaterial.ValidateMaterial(m);return m;
    }
    static GameObject Box(string name,Vector3 centre,Vector3 size,Material material)
    {
        var g=GameObject.CreatePrimitive(PrimitiveType.Cube);g.name=name;
        g.transform.position=centre;g.transform.localScale=size;g.GetComponent<Renderer>().sharedMaterial=material;return g;
    }
    [MenuItem("HomeAlone/Marina PoC/Build Buzz study")]
    public static string Build()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play first.");
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)throw new InvalidOperationException("Save existing scene first.");
        var j=JObject.Parse(File.ReadAllText(Path.Combine(Application.dataPath,"../../../art/home_alone/references/buzz-poc/study.json")));
        float w=(float)j["room_width"],d=(float)j["room_depth"],h=(float)j["room_height"],door=(float)j["door_left"],dw=(float)j["door_width"],bed=(float)j["bed_left"],bw=(float)j["bed_width"],bl=(float)j["bed_length"];
        float hz=(float?)j["head_z"]??-.04f,hy=(float?)j["head_height"]??.64f;
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var wall=Finish("Wall",new Color(.68f,.70f,.73f));var floor=Finish("Floor",new Color(.25f,.27f,.29f));
        var ivory=Finish("Door and mattress",new Color(.88f,.88f,.85f));var wood=Finish("Furniture",new Color(.31f,.36f,.40f));
        var green=Finish("Bedding",new Color(.19f,.37f,.29f));var blue=Finish("Window markers",new Color(.37f,.59f,.70f));
        Box("Floor - depth provisional",new Vector3(w/2,-.025f,-d/2),new Vector3(w,.05f,d),floor);
        Box("Bed wall left of door",new Vector3(door/2,h/2,.025f),new Vector3(door,h,.05f),wall);
        Box("Bed wall right of door",new Vector3((door+dw+w)/2,h/2,.025f),new Vector3(w-door-dw,h,.05f),wall);
        Box("Door header",new Vector3(door+dw/2,(1+h)/2,.025f),new Vector3(dw,h-1,.05f),wall);
        Box("Reference door - height one unit",new Vector3(door+dw/2,.5f,-.004f),new Vector3(dw,1,.008f),ivory);
        foreach(float x in new[]{door-.018f,door+dw+.018f})Box("Door casing",new Vector3(x,.5f,-.012f),new Vector3(.036f,1.05f,.025f),ivory);
        Box("Door casing head",new Vector3(door+dw/2,1.025f,-.012f),new Vector3(dw+.072f,.04f,.025f),ivory);
        Box("Shelf side wall",new Vector3(-.025f,h/2,-d/2),new Vector3(.05f,h,d),wall);
        Box("Window side wall",new Vector3(w+.025f,h/2,-d/2),new Vector3(.05f,h,d),wall);
        Box("Opposite wall - depth provisional",new Vector3(w/2,h/2,-d-.025f),new Vector3(w,h,.05f),wall);
        Box("Bed footprint - length provisional",new Vector3(bed+bw/2,.20f,-bl/2-.04f),new Vector3(bw,.12f,bl),wood);
        Box("Mattress",new Vector3(bed+bw/2,.29f,-bl/2-.04f),new Vector3(bw,.06f,bl),ivory);
        Box("Quilt",new Vector3(bed+bw/2,.325f,-bl*.65f-.04f),new Vector3(bw,.012f,bl*.70f),green);
        Box("Headboard - apparent plane estimate",new Vector3(bed+bw/2,hy-.15f,hz),new Vector3(bw,.26f,.025f),wood);
        foreach(float x in new[]{bed,bed+bw})Box("Headpost",new Vector3(x,hy/2,hz-.018f),new Vector3(.035f,hy,.035f),wood);
        Box("Bedside footprint",new Vector3(bed+bw+.18f,.15f,-.19f),new Vector3(.29f,.30f,.28f),wood);
        Box("Dresser footprint - provisional",new Vector3(w-.13f,.29f,-1.22f),new Vector3(.26f,.58f,.35f),wood);
        Box("Desk footprint - provisional",new Vector3(w-.45f,.17f,-d+.14f),new Vector3(.65f,.34f,.28f),wood);
        foreach(float y in new[]{.35f,.62f,.89f})Box("Shelf footprint",new Vector3(.10f,y,-.76f),new Vector3(.20f,.025f,.88f),wood);
        foreach(float z in new[]{-.50f,-1.67f})Box("Window location - provisional",new Vector3(w-.004f,.66f,z),new Vector3(.008f,.72f,.39f),blue);
        Box("Third window on desk wall - position provisional",new Vector3(w-.27f,.66f,-d+.004f),new Vector3(.39f,.72f,.008f),blue);
        var cg=new GameObject("PoC reference camera");var camera=cg.AddComponent<Camera>();cg.tag="MainCamera";
        camera.nearClipPlane=.01f;camera.farClipPlane=30;camera.fieldOfView=(float)j["vertical_fov"];
        var c=(JArray)j["camera"];cg.transform.SetPositionAndRotation(new Vector3((float)c[0],(float)c[1],(float)c[2]),Quaternion.Euler((float)c[4],(float)c[3],(float)c[5]));
        if(j["camera_position"]!=null){var p=(JArray)j["camera_position"];var fw=(JArray)j["camera_forward"];var up=(JArray)j["camera_up"];cg.transform.SetPositionAndRotation(new Vector3((float)p[0],(float)p[1],(float)p[2]),Quaternion.LookRotation(new Vector3((float)fw[0],(float)fw[1],(float)fw[2]),new Vector3((float)up[0],(float)up[1],(float)up[2])));}
        var hd=cg.AddComponent<HDAdditionalCameraData>();hd.antialiasing=HDAdditionalCameraData.AntialiasingMode.None;hd.volumeLayerMask=-1;
        var vg=new GameObject("Neutral exposure");var volume=vg.AddComponent<Volume>();volume.isGlobal=true;
        var profile=new VolumeProfile();var exposure=profile.Add<Exposure>();exposure.mode.Override(ExposureMode.Fixed);exposure.fixedExposure.Override(0);
        const string vp="Assets/Materials/BuzzPOC/Exposure.asset";var saved=AssetDatabase.LoadAssetAtPath<VolumeProfile>(vp);
        if(saved){UnityEngine.Object.DestroyImmediate(profile);profile=saved;}else{AssetDatabase.CreateAsset(profile,vp);AssetDatabase.AddObjectToAsset(exposure,profile);}
        Fog fog;if(!profile.TryGet(out fog)){fog=profile.Add<Fog>();AssetDatabase.AddObjectToAsset(fog,profile);}fog.enabled.Override(false);
        EditorUtility.SetDirty(profile);EditorUtility.SetDirty(fog);volume.sharedProfile=profile;
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),ScenePath);
        return "Saved separate Buzz PoC in door-height units. Width "+w.ToString("F3")+", headboard "+bw.ToString("F3")+"; depth/height/bed length provisional.";
    }
    [MenuItem("HomeAlone/Marina PoC/Build walkable Buzz candidate")]
    public static string BuildWalkable()
    {
        Build();
        // Deliberate scale assumption: one reference-door height = 2.032 metres.
        const float scale=2.032f;
        foreach(var g in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
            if(g.GetComponent<Renderer>()){g.transform.position*=scale;g.transform.localScale*=scale;}
        UnityEngine.Object.DestroyImmediate(GameObject.Find("PoC reference camera"));
        UnityEngine.Object.DestroyImmediate(GameObject.Find("Reference door - height one unit"));
        var floor=Finish("Floor",new Color(.25f,.27f,.29f));
        var ivory=Finish("Door and mattress",new Color(.88f,.88f,.85f));
        var wood=Finish("Furniture",new Color(.31f,.36f,.40f));
        var green=Finish("Bedding",new Color(.19f,.37f,.29f));
        var j=JObject.Parse(File.ReadAllText(Path.Combine(Application.dataPath,"../../../art/home_alone/references/buzz-poc/study.json")));
        float w=(float)j["room_width"]*scale,d=(float)j["room_depth"]*scale,h=(float)j["room_height"]*scale;
        // Working blockout adjustment: retain furniture sizes and give the dresser-side aisle usable clearance.
        const float extraWidth=.25f;
        foreach(var renderer in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)){
            var t=renderer.transform;string n=renderer.name;
            if(n=="Window side wall" || n.StartsWith("Window location") || n.StartsWith("Third window") || n.StartsWith("Dresser footprint"))
                t.position+=Vector3.right*extraWidth;
            if(n.StartsWith("Floor -") || n.StartsWith("Opposite wall -") || n=="Bed wall right of door"){
                t.position+=Vector3.right*(extraWidth/2);t.localScale+=Vector3.right*extraWidth;
            }
        }
        w+=extraWidth;
        float bx=(float)j["bed_left"]*scale,bw=(float)j["bed_width"]*scale,bl=(float)j["bed_length"]*scale;
        Box("Ceiling - estimated",new Vector3(w/2,h+.05f,-d/2),new Vector3(w,.1f,d),ivory);
        Box("Pillow",new Vector3(bx+bw/2,.72f,-.42f),new Vector3(bw*.86f,.16f,.42f),ivory);
        Box("Footboard",new Vector3(bx+bw/2,.42f,-bl-.08f),new Vector3(bw,.60f,.07f),wood);
        Box("Bedside lamp base",new Vector3(bx+bw+.36f,.74f,-.38f),new Vector3(.12f,.28f,.12f),wood);
        Box("Bedside lamp shade",new Vector3(bx+bw+.36f,.93f,-.38f),new Vector3(.32f,.16f,.28f),green);
        var desk=GameObject.Find("Desk footprint - provisional");
        UnityEngine.Object.DestroyImmediate(desk);
        float dx=w-.90f;
        Box("Desk top",new Vector3(dx,.75f,-d+.30f),new Vector3(1.30f,.06f,.60f),wood);
        foreach(float x in new[]{dx-.52f,dx+.52f})Box("Desk pedestal",new Vector3(x,.36f,-d+.30f),new Vector3(.22f,.72f,.54f),wood);
        Box("Chair seat",new Vector3(dx,.45f,-d+1.05f),new Vector3(.45f,.07f,.45f),green);
        Box("Chair back",new Vector3(dx,.68f,-d+1.25f),new Vector3(.45f,.50f,.06f),wood);
        foreach(float x in new[]{dx-.17f,dx+.17f})foreach(float z in new[]{-d+.88f,-d+1.22f})
            Box("Chair leg",new Vector3(x,.22f,z),new Vector3(.045f,.44f,.045f),wood);
        Box("Jordan closet door - reference placeholder",new Vector3(.65f,1.016f,-d+.035f),new Vector3(.82f,2.032f,.04f),green);
        Box("Terrarium footprint",new Vector3(.20f,1.40f,-1.8f),new Vector3(.35f,.32f,.60f),green);
        // Small isolated test apron permits stepping through the original opening; not a proposed hallway.
        Box("Test apron",new Vector3(.65f,-.05f,.65f),new Vector3(1.30f,.1f,1.30f),floor);
        Box("Test apron end",new Vector3(.65f,1.1f,1.30f),new Vector3(1.4f,2.2f,.08f),wood);
        foreach(float x in new[]{-.04f,1.34f})Box("Test apron side",new Vector3(x,1.1f,.65f),new Vector3(.08f,2.2f,1.3f),wood);
        var player=new GameObject("Buzz study walker");player.transform.position=new Vector3(.85f,.04f,-2.7f);
        var cc=player.AddComponent<CharacterController>();cc.radius=.22f;cc.height=1.7f;cc.center=new Vector3(0,.85f,0);cc.skinWidth=.025f;cc.stepOffset=.2f;
        var cameraObject=new GameObject("Walkthrough camera");cameraObject.tag="MainCamera";cameraObject.transform.SetParent(player.transform,false);cameraObject.transform.localPosition=new Vector3(0,1.55f,0);
        var camera=cameraObject.AddComponent<Camera>();camera.fieldOfView=65;camera.nearClipPlane=.03f;camera.farClipPlane=50;
        var hd=cameraObject.AddComponent<HDAdditionalCameraData>();hd.volumeLayerMask=-1;hd.antialiasing=HDAdditionalCameraData.AntialiasingMode.None;
        cameraObject.AddComponent<AudioListener>();
        var fps=player.AddComponent<FpsController>();fps.cam=cameraObject.transform;fps.standHeight=1.7f;fps.walkSpeed=1.8f;fps.sprintSpeed=2.7f;
        Physics.SyncTransforms();
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),"Assets/Scenes/BuzzWalkableCandidate.unity");
        return "Saved walkable candidate: "+w.ToString("F2")+" x "+d.ToString("F2")+" x "+h.ToString("F2")+"m, all provisional; bed "+bw.ToString("F2")+" x "+bl.ToString("F2")+"m.";
    }
    public static string CheckWalkable()
    {
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!="Assets/Scenes/BuzzWalkableCandidate.unity")throw new InvalidOperationException("Open walkable candidate first.");
        var fps=UnityEngine.Object.FindFirstObjectByType<FpsController>();var cc=fps.GetComponent<CharacterController>();
        var start=fps.transform.position;
        // Reserve the full doorway approach, including its casing, before testing a walking route.
        var entryClearance=new Bounds(new Vector3(.57f,1.05f,-.30f),new Vector3(1.10f,2.10f,.60f));
        foreach(var renderer in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            if(renderer.name=="Shelf footprint" && renderer.bounds.Intersects(entryClearance))
                throw new Exception("Shelf intrudes into doorway approach: "+renderer.bounds);
        var route=new[]{new Vector3(.85f,0,-1),new Vector3(.70f,0,.60f),new Vector3(.70f,0,-.50f),new Vector3(.85f,0,-2.70f),new Vector3(1.50f,0,-2.90f),new Vector3(2.55f,0,-2.60f),new Vector3(3.0f,0,-2.60f),new Vector3(3.0f,0,-3.15f),new Vector3(3.0f,0,-2.60f),new Vector3(3.0f,0,-1.20f),new Vector3(3.0f,0,-2.60f),new Vector3(2.55f,0,-2.60f),new Vector3(1.50f,0,-2.90f),new Vector3(.85f,0,-2.70f)};
        try{
            Physics.SyncTransforms();
            for(int i=0;i<route.Length;i++){
                for(int frame=0;frame<600;frame++){
                    var delta=route[i]-fps.transform.position;delta.y=0;
                    if(delta.magnitude<.075f)break;
                    fps.TickMotion(delta,false,false,1f/60f);
                    if(fps.transform.position.y<-.1f)throw new Exception("Floor failure at route "+i);
                }
                var error=route[i]-fps.transform.position;error.y=0;
                if(error.magnitude>.10f)throw new Exception("Blocked route "+i+" at "+fps.transform.position+" remaining "+error.magnitude);
            }
            return "PASS: fourteen waypoint route, doorway out/back, shelves, bed foot, dresser-side bed access and desk approach; 1.7m controller, radius 0.22m.";
        }finally{cc.enabled=false;fps.transform.position=start;cc.enabled=true;}
    }
    [MenuItem("HomeAlone/Marina PoC/Overhead view")]
    public static void Overhead()
    {
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=ScenePath)throw new InvalidOperationException("Open Buzz PoC first.");
        var c=Camera.main;c.orthographic=true;c.orthographicSize=1.3f;c.transform.SetPositionAndRotation(new Vector3(.92f,4,-1.05f),Quaternion.Euler(90,0,0));
    }
}
