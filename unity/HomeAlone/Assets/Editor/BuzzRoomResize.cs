using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// Buzz's room in the old model (IntactHouseReference) resized to Marina's proportions (user decision, Oct 13; docs/DEVIATIONS.md O1/O2):
//   north (shelves) wall +0.39 native (0.30 m) into the over-wide hall band; the attic stairwell and its door move with it;
//   west (desk) wall -0.68 native (0.53 m) into the side wing for its full length, side window and desk wall furniture with it.
// September method: the GLB asset is untouched; wall faces are moved by shifting their vertex planes (texture stays), the old
// exterior recess siding is clipped and the overhang rebuilt from boxes. Re-runnable: resized meshes carry "BuzzResize" in their name.
public static partial class SurveyBuilder
{
    public const float BuzzShiftX=-0.68f, BuzzShiftZ=0.39f;
    const string ResizeRoot="BuzzRoomResize";

    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SurveyBuilder.ResizeBuzzRoomBatch -quit -logFile -
    public static void ResizeBuzzRoomBatch(){EditorSceneManager.OpenScene(IntactScene);ResizeBuzzRoom();}
    [MenuItem("HomeAlone/Reference/Resize Buzz Room to Marina")]
    public static void ResizeBuzzRoom()
    {
        if(EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var glb=GameObject.Find("IntactGLB");
        if(GameObject.Find(ResizeRoot))UnityEngine.Object.DestroyImmediate(GameObject.Find(ResizeRoot));
        float dx=BuzzShiftX,dz=BuzzShiftZ;
        // (axis, plane lo/hi, other-axis ranges, delta, optional object filter). World coordinates, upper floor only (y 4.9-8.7).
        var exterior=new HashSet<string>{"object227","object229","object213","object20"};
        var skip=new HashSet<string>{"object206","object2989","object2990","object2991","object2993","object2994","object2995","object3002","object156"};
        var rules=new List<(int axis,float lo,float hi,float oLo,float oHi,float d,string[] only)>{
            (0,-6.12f,-6.06f,-2.8f,2.5f,dx,null),                      // room-side west face, ceiling/floor edges
            (0,-6.36f,-6.26f,-2.8f,2.30f,dx,null),                     // wing-side face, reveals, soffit edge
            (0,-6.36f,-6.26f,2.30f,2.35f,dx,new[]{"object52","object54","object211"}),   // wing room NE corner
            (2,1.865f,1.895f,-6.6f,-1.1f,dz,null),                     // room-side north face
            (2,2.04f,2.09f,-6.6f,-0.9f,dz,null),                       // hall-side face, wainscot, corridor west face end
            (2,0.25f,1.82f,-1.25f,-0.93f,dz,null),                     // the door opening, casing and header in the east wall stay at the corner
            (2,2.31f,2.33f,-8.7f,-3.1f,dz,null),(2,2.52f,2.54f,-8.7f,-3.1f,dz,null),      // attic stairwell south walls + band corner
            (2,4.01f,4.03f,-8.7f,-3.1f,dz,null),(2,4.14f,4.16f,-8.7f,-3.1f,dz,null),(2,4.22f,4.25f,-8.7f,-3.1f,dz,null)}; // stairwell north walls
        // Re-runnable: a mesh already resized is rebuilt from what it was made from (the window cut, else the GLB mesh);
        // FurnishBuzzBedroom re-applies its shelf-fragment cut on top afterwards.
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/ThirdParty/HomeAloneExterior/HomeAloneExterior.glb");
        var originals=prefab.GetComponentsInChildren<MeshFilter>(true).ToDictionary(m=>m.name,m=>m.sharedMesh);
        int movedMeshes=0,movedVerts=0,cutTris=0;
        foreach(var mf in glb.GetComponentsInChildren<MeshFilter>(true)){
            var mesh=mf.sharedMesh;if(!mesh||skip.Contains(mf.name))continue;
            if(mesh.name.Contains("BuzzResize"))mesh=AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Materials/IntactFoyer/FrontWindowCut_"+mf.name+".asset")??originals[mf.name];
            Mesh result=null;
            if(exterior.Contains(mf.name)){
                // old recess siding, trims, the wing-front face and its inside corner, inside the new overhang volume: x -7.14..-6.25, y 5.22..8.6, z -2.75..-0.85
                result=CutWindowTriangles(mesh,mf.transform,new List<(Vector3,float,float,float,int,int,string)>{(new Vector3(-6.695f,6.91f,-1.80f),0.808f,3.278f,0,1,1,"Buzz overhang")},out int n,1.90f);
                if(n==0){UnityEngine.Object.DestroyImmediate(result);continue;}
                cutTris+=n;
            }else{
                var v=mesh.vertices;bool any=false;
                for(int i=0;i<v.Length;i++){
                    var w=mf.transform.TransformPoint(v[i]);if(w.y<4.9f||w.y>8.7f)continue;
                    var w0=w;
                    foreach(var r in rules){
                        if(r.only!=null&&!r.only.Contains(mf.name))continue;
                        float a=w0[r.axis],o=w0[r.axis==0?2:0];
                        if(a>=r.lo&&a<=r.hi&&o>=r.oLo&&o<=r.oHi)w[r.axis]+=r.d;
                    }
                    if(w!=w0){v[i]=mf.transform.InverseTransformPoint(w);any=true;movedVerts++;}
                }
                if(!any)continue;
                result=UnityEngine.Object.Instantiate(mesh);result.vertices=v;result.RecalculateBounds();
            }
            result.name=mesh.name+" BuzzResize";
            string path="Assets/Materials/IntactFoyer/BuzzResize_"+mf.name+".asset";var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if(saved){EditorUtility.CopySerialized(result,saved);UnityEngine.Object.DestroyImmediate(result);}else{saved=result;AssetDatabase.CreateAsset(saved,path);}
            EditorUtility.SetDirty(saved);mf.sharedMesh=saved;var mc=mf.GetComponent<MeshCollider>();if(mc)mc.sharedMesh=saved;movedMeshes++;
        }
        // Whole objects: the attic-stair door and Buzz's own door (+dz), the desk chair (dx), the side sash assembly (dx). A marker child makes this re-runnable.
        foreach(var (id,delta) in new[]{(2993,new Vector3(0,0,dz)),(2994,new Vector3(0,0,dz)),(2995,new Vector3(0,0,dz)),(2989,new Vector3(0,0,dz)),(2990,new Vector3(0,0,dz)),(2991,new Vector3(0,0,dz)),(8,new Vector3(dx,0,0))}){
            var t=glb.transform.GetComponentsInChildren<Transform>(true).Single(x=>x.name=="object"+id);
            if(t.Find("BuzzResizeMoved"))continue;t.position+=delta;new GameObject("BuzzResizeMoved").transform.parent=t;
        }
        var sash=GameObject.Find("Main front window assemblies").transform.Cast<Transform>().SingleOrDefault(t=>Mathf.Abs(t.position.x+6.285f)<.01f&&Mathf.Abs(t.position.z+1.803f)<.01f);
        if(sash)sash.position+=new Vector3(dx,0,0);
        // Overhang exterior (upper floor only; the ground-floor wall below stays): west face with the window hole, front and wing returns, soffit, cap.
        var root=new GameObject(ResizeRoot);var siding=glb.GetComponentsInChildren<Renderer>(true).Single(r=>r.name=="object227").sharedMaterial;
        float x0=-6.47f+dx-.01f,x1=x0+.18f;   // new exterior face -7.16, wall 0.18 thick (-6.98); the room face is at -6.77
        Box(root,"Overhang west face below sill",x0,x1,-2.70f,-1.26f,5.22f,5.83f,siding);
        Box(root,"Overhang west face above head",x0,x1,-2.70f,-1.26f,7.45f,8.56f,siding);
        Box(root,"Overhang west face front pier",x0,x1,-2.70f,-2.24f,5.83f,7.45f,siding);
        Box(root,"Overhang west face wing pier",x0,x1,-1.37f,-1.26f,5.83f,7.45f,siding);
        Box(root,"Overhang front return",x0,-6.47f,-2.70f,-2.33f,5.22f,8.56f,siding);
        Box(root,"Overhang wing return",x0,x1,-1.26f,-0.91f,5.22f,8.56f,siding);   // to the wing's interior face; the wall hollow behind it stays enclosed
        Box(root,"Overhang soffit",x0,-6.47f,-2.70f,-1.10f,5.08f,5.22f,siding);
        Box(root,"Overhang cap",x0,-6.47f,-2.70f,-1.10f,8.56f,8.60f,siding);
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
        Debug.Log($"Buzz room resized: {movedMeshes} meshes, {movedVerts} vertices moved, {cutTris} exterior triangles clipped.");
    }

    // glb_section-style rays against the live scene: the room, the hall band, the corridor and the wing, in metres.
    // Run: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SurveyBuilder.CheckBuzzRoomSizeBatch -quit -logFile - [-inject]
    // -inject puts a wall back 0.19 native (15 cm) south of the new north face; the check must FAIL on it.
    public static void CheckBuzzRoomSizeBatch()
    {
        EditorSceneManager.OpenScene(IntactScene);bool inject=Environment.GetCommandLineArgs().Contains("-inject");
        GameObject bad=null;
        if(inject){bad=GameObject.CreatePrimitive(PrimitiveType.Cube);bad.name="INJECTED wall";bad.transform.position=new Vector3(-3.6f,6.8f,2.08f);bad.transform.localScale=new Vector3(5.6f,3.1f,.1f);
            // injected hole: the room shell and the overhang boxes stop blocking rays
            foreach(var c in GameObject.Find("IntactGLB").GetComponentsInChildren<MeshCollider>().Where(c=>c.name=="object50"))c.enabled=false;
            foreach(var c in GameObject.Find(ResizeRoot).GetComponentsInChildren<Collider>())c.enabled=false;}
        Physics.SyncTransforms();
        const float U=2.032f/2.625f;var log=new System.Text.StringBuilder();bool ok=true;
        // triggers are lighting volumes (e.g. "Foyer night camera exposure"), not geometry
        float Hit(Vector3 from,Vector3 dir){if(!Physics.Raycast(from,dir,out var h,30f,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))return float.NaN;log.Append($"[{h.collider.name}] ");return dir.x!=0?h.point.x:h.point.z;}
        // rays at y 7.6 (1.84 m up) clear the furniture; a NaN expectation is not checked
        void Span(string what,Vector3 from,bool alongX,float expectLo,float expectHi,float targetM){
            var lo=Hit(from,alongX?Vector3.left:Vector3.back);var hi=Hit(from,alongX?Vector3.right:Vector3.forward);
            bool pass=(float.IsNaN(expectLo)||Mathf.Abs(lo-expectLo)<.05f)&&(float.IsNaN(expectHi)||Mathf.Abs(hi-expectHi)<.05f);ok&=pass;
            log.AppendLine($"{(pass?"PASS":"FAIL")} {what}: {lo:F2}..{hi:F2} native = {(hi-lo)*U:F2} m (expected {expectLo:F2}..{expectHi:F2}, Marina {targetM:F2} m)");
        }
        Span("Buzz room door wall to desk wall",new Vector3(-3.9f,7.6f,0),true,-6.09f+BuzzShiftX,-1.16f,4.35f);
        Span("Buzz room shelves wall to front windows",new Vector3(-1.8f,7.6f,0),false,-2.30f,1.88f+BuzzShiftZ,3.49f);
        Span("hall band north of Buzz (east of its bedroom door)",new Vector3(-1.4f,7.6f,3.45f),false,2.05f+BuzzShiftZ,4.50f,1.35f);
        Span("corridor east of Buzz's door, west face (south of the door)",new Vector3(0,7.6f,0.2f),true,-0.98f,float.NaN,1.14f);
        Span("corridor east of Buzz's door, east face",new Vector3(0,7.6f,1.0f),true,float.NaN,0.90f,1.14f);
        Span("Buzz's door opening along the east wall (frame jambs, from inside)",new Vector3(-1.2f,6.6f,1.05f+BuzzShiftZ),false,0.38f+BuzzShiftZ,1.69f+BuzzShiftZ,float.NaN);
        Span("wing south room, east wall",new Vector3(-8.0f,7.6f,1.0f),true,float.NaN,-6.28f+BuzzShiftX,float.NaN);
        // enclosure: ray fans from inside must always hit something within 30 native (the house is ~35 long; windows carry
        // glazing colliders, so a miss is a hole to the sky). Rays through doorways cross the hall and still hit its far walls.
        foreach(var (name,from) in new[]{("Buzz room",new Vector3(-3.9f,6.6f,0)),("Buzz new strip at the side window",new Vector3(-6.5f,6.6f,-1.8f)),("hall band",new Vector3(-2.3f,6.6f,3.45f)),("wing south room",new Vector3(-8.0f,6.6f,1.0f))}){
            int miss=0;string first="";
            for(int i=0;i<400;i++){float y=1-2f*(i+.5f)/400,r=Mathf.Sqrt(1-y*y),t=i*2.399963f;var d=new Vector3(r*Mathf.Cos(t),y,r*Mathf.Sin(t));
                if(!Physics.Raycast(from,d,30f,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore)){if(miss==0)first=d.ToString("F2");miss++;}}
            bool pass=miss==0;ok&=pass;log.AppendLine($"{(pass?"PASS":"FAIL")} enclosure from {name}: {miss}/400 rays escape{(miss>0?" (first "+first+")":"")}");
        }
        Directory.CreateDirectory("../../spec/captures");File.WriteAllText("../../spec/captures/buzz-room-size"+(inject?"-inject":"")+".txt",log.ToString());Debug.Log(log.ToString());
        if(bad)UnityEngine.Object.DestroyImmediate(bad);
        if(!ok)throw new InvalidOperationException("Buzz room size/enclosure check FAILED\n"+log);
    }

    // Play-mode checks without the editor UI: enter Play, run CheckBuzzBedroom + CheckIntactMainStairs, write the result, exit.
    // Run (no -quit): Unity -batchmode -projectPath unity/HomeAlone -executeMethod SurveyBuilder.PlayChecksBatch -logFile -
    public static void PlayChecksBatch(){EditorSceneManager.OpenScene(IntactScene);SessionState.SetBool("BuzzPlayChecks",true);EditorApplication.EnterPlaymode();}
    [InitializeOnLoadMethod] static void PlayChecksHook()
    {
        if(!SessionState.GetBool("BuzzPlayChecks",false))return;
        EditorApplication.playModeStateChanged+=s=>{if(s==PlayModeStateChange.EnteredPlayMode)EditorApplication.delayCall+=RunPlayChecks;};
        if(EditorApplication.isPlaying)EditorApplication.delayCall+=RunPlayChecks;
    }
    static void RunPlayChecks()
    {
        if(!SessionState.GetBool("BuzzPlayChecks",false))return;SessionState.SetBool("BuzzPlayChecks",false);
        var log=new System.Text.StringBuilder();bool ok=true;
        foreach(var check in new Func<string>[]{CheckBuzzBedroom,CheckIntactMainStairs,CheckBuzzWindows}){
            try{log.AppendLine(check());}catch(Exception e){ok=false;log.AppendLine("FAIL "+check.Method.Name+": "+e.Message);}
        }
        Directory.CreateDirectory("../../spec/captures");File.WriteAllText("../../spec/captures/buzz-play-checks.txt",log.ToString());Debug.Log(log.ToString());
        EditorApplication.Exit(ok?0:1);
    }
}
