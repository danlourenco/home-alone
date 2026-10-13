using System;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Refine Film Rear Landing")]
    public static void RefineFilmRearLanding()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Leave Play in IntactHouseReference first.");
        var old=GameObject.Find("Film rear landing");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Film rear landing");
        var paint=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/FrontWindowIvory.mat");
        var paper=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/Damask.mat");
        var glass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/FrontWindowGlass.mat");
        var wood=FoyerFinish("LandingMahogany",new Color(.19f,.07f,.025f),.35f);
        var gold=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/AntiqueBrass.mat");
        var green=FoyerFinish("LandingLeaves",new Color(.035f,.12f,.028f),.10f);
        var red=FoyerFinish("LandingPoinsettia",new Color(.43f,.013f,.023f),.09f);
        var ivory=FoyerFinish("LandingPicturePaper",new Color(.83f,.79f,.65f),.03f);
        // Keep both six-over-six sashes, with the broad common casing and fanlight seen in the film.
        var windows=GameObject.Find("Main front window assemblies").transform.Cast<Transform>().Where(t=>t.name=="Stair landing sash").OrderBy(t=>t.position.x).ToArray();
        if(windows.Length!=2)throw new InvalidOperationException("Expected two landing sashes.");
        for(int i=0;i<2;i++)windows[i].position=new Vector3(1.39f+i*1.32f,6.30f,10.947f);
        // Read the exterior material before clipping; only this opening is changed.
        Material exterior=paint;RaycastHit hit;
        if(Physics.Raycast(new Vector3(2.05f,7.80f,12),Vector3.back,out hit,3)){
            var renderer=hit.collider.GetComponent<Renderer>();if(renderer)exterior=renderer.sharedMaterial;
        }
        var box=new[]{10.65f,10.94f,11.20f}.Select(z=>(new Vector3(2.05f,6.53f,z),2.958f,2.558f,180f,1,1,"Landing opening")).ToList();
        foreach(var mf in GameObject.Find("IntactGLB").GetComponentsInChildren<MeshFilter>()){
            var r=mf.GetComponent<Renderer>();if(!r||!r.bounds.Intersects(new Bounds(new Vector3(2.05f,6.53f,10.94f),new Vector3(3.1f,2.8f,1.2f))))continue;
            var cut=CutWindowTriangles(mf.sharedMesh,mf.transform,box,out int changed);if(changed==0){UnityEngine.Object.DestroyImmediate(cut);continue;}
            string path="Assets/Materials/IntactFoyer/LandingCut_"+mf.name+".asset";var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if(saved){saved.Clear();EditorUtility.CopySerialized(cut,saved);UnityEngine.Object.DestroyImmediate(cut);}else{saved=cut;AssetDatabase.CreateAsset(saved,path);}
            EditorUtility.SetDirty(saved);mf.sharedMesh=saved;
            // Original collider stays: panes remain a physical barrier; stairs and floor are untouched.
        }
        foreach(float x in new[]{.64f,3.46f})Box(root,"Broad ivory side casing",x-.11f,x+.11f,10.68f,11.19f,5.20f,7.27f,paint);
        // Continuous room-side reveals replace the imported window surround, including its oversized recess.
        foreach(var span in new[]{new Vector2(-1.15f,.53f),new Vector2(3.57f,4.85f)}){
            Box(root,"Rear wall wallpaper surround",span.x,span.y,10.665f,10.68f,5.47f,8.36f,paper);
            Box(root,"Rear wall painted lower panel",span.x,span.y,10.66f,10.68f,4.45f,5.47f,paint);
            Box(root,"Rear wall chair rail",span.x,span.y,10.635f,10.66f,5.43f,5.48f,paint);
        }
        Box(root,"Wall below window",.53f,3.57f,10.665f,10.68f,4.45f,5.20f,paint);
        Box(root,"Wall above window",.53f,3.57f,10.665f,10.68f,7.86f,8.36f,paper);
        Box(root,"Window stool",.49f,3.61f,10.57f,11.18f,5.20f,5.31f,paint);
        Box(root,"Common centre mullion",2.015f,2.085f,10.72f,11.17f,5.33f,7.27f,paint);
        Box(root,"Fanlight transom rail",.75f,3.35f,10.72f,11.17f,7.27f,7.33f,paint);
        var fanV=new List<Vector3>{new Vector3(2.05f,7.33f,10.94f)};var fanT=new List<int>();
        var cornerV=new List<Vector3>();var cornerT=new List<int>();
        for(int i=0;i<=40;i++){
            float a=i*Mathf.PI/40;var p=new Vector3(2.05f+1.52f*Mathf.Cos(a),7.27f+.53f*Mathf.Sin(a),10.94f);
            fanV.Add(p);cornerV.Add(new Vector3(p.x,p.y,10.685f));cornerV.Add(new Vector3(p.x,7.86f,10.685f));
            if(i>0){fanT.AddRange(new[]{0,i,i+1});int k=(i-1)*2;cornerT.AddRange(new[]{k,k+1,k+2,k+1,k+3,k+2});}
            if(i<40){float b=(i+1)*Mathf.PI/40;BedroomRod(root,new Vector3(p.x,p.y,10.70f),new Vector3(2.05f+1.52f*Mathf.Cos(b),7.27f+.53f*Mathf.Sin(b),10.70f),.055f,paint);}
        }
        LandingMesh(root,"Arched fanlight glazing",fanV,fanT,glass);
        LandingMesh(root,"Wallpaper above arch",cornerV,cornerT,paper);
        LandingMesh(root,"Exterior above arch",cornerV.Select(v=>new Vector3(v.x,v.y,11.195f)).ToList(),cornerT,exterior);
        for(int i=1;i<6;i++){
            float a=i*Mathf.PI/6;BedroomRod(root,new Vector3(2.05f,7.31f,10.74f),new Vector3(2.05f+1.46f*Mathf.Cos(a),7.27f+.48f*Mathf.Sin(a),10.74f),.012f,paint);
        }
        // Replace the unsupported centre pedestal/lamp with the left-side table and flowers.
        var foyer=GameObject.Find("FoyerNight");
        foreach(Transform child in foyer.transform.Cast<Transform>().ToArray())
            if(child.name=="Landing lamp table" || (child.position.y>4.8f&&child.position.z>9.5f&&new[]{"Lamp base","Lamp stem","Ivory shade","Table lamp"}.Contains(child.name)))UnityEngine.Object.DestroyImmediate(child.gameObject);
        var mode=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>();
        if(mode){var keep=Enumerable.Range(0,mode.interiorLights.Length).Where(i=>mode.interiorLights[i]).ToArray();mode.daytimeEnabled=keep.Select(i=>mode.daytimeEnabled[i]).ToArray();mode.interiorLights=keep.Select(i=>mode.interiorLights[i]).ToArray();}
        var table=Child(root,"Left landing side table");
        // Demilune: the straight rear edge sits against the wall; only the front bows out.
        LandingConsoleSlab(table,"Half round mahogany top",.52f,.42f,5.18f,5.23f,wood);
        LandingConsoleSlab(table,"Curved table apron",.49f,.39f,5.04f,5.18f,wood);
        foreach(float x in new[]{-.71f,.21f})Cyl(table,"Rear table leg",x,10.61f,4.45f,5.10f,.021f,wood);
        foreach(float x in new[]{-.47f,-.03f})Cyl(table,"Front table leg",x,10.29f,4.45f,5.10f,.021f,wood);
        for(int i=0;i<24;i++){
            float a=i*Mathf.PI/24,b=(i+1)*Mathf.PI/24;
            BedroomRod(table,new Vector3(-.25f+.47f*Mathf.Cos(a),4.67f,10.65f-.36f*Mathf.Sin(a)),new Vector3(-.25f+.47f*Mathf.Cos(b),4.67f,10.65f-.36f*Mathf.Sin(b)),.012f,wood);
        }
        Box(table,"Centre drawer face",-.44f,-.06f,10.252f,10.265f,5.065f,5.16f,wood);
        BedroomSoft(table,"Small brass drawer pull",new Vector3(-.25f,5.11f,10.24f),new Vector3(.035f,.02f,.025f),gold);
        Cyl(table,"Small brass planter",-.47f,10.43f,5.23f,5.42f,.10f,gold);
        for(int i=0;i<38;i++){
            float a=i*2.4f,r=.08f+.065f*(i%3),y=5.46f+.12f*Mathf.Sin(i*1.7f);
            BedroomSoft(table,"Trailing green foliage",new Vector3(-.47f+r*Mathf.Cos(a),y,10.43f+r*Mathf.Sin(a)),new Vector3(.10f,.065f,.08f),green);
        }
        var mat=FoyerFinish("LandingRoseMat",new Color(.43f,.21f,.15f),.05f);
        Box(root,"Floral picture gold frame",-.67f,.17f,10.64f,10.69f,5.91f,7.04f,gold);
        Box(root,"Floral picture rose mat",-.65f,.15f,10.625f,10.639f,5.93f,7.02f,mat);
        var print=FoyerFinish("LandingFloralPrint",Color.white,.02f,"Assets/Textures/LandingReference.jpg");
        print.SetFloat("_UVBase",0);
        // Sample the artwork only from Marina's 05:50 reference; retain the full source image.
        print.SetTextureScale("_BaseColorMap",new Vector2(180f/1920f,270f/1080f));
        print.SetTextureOffset("_BaseColorMap",new Vector2(870f/1920f,786f/1080f));
        HDMaterial.ValidateMaterial(print);
        var picture=GameObject.CreatePrimitive(PrimitiveType.Quad);picture.name="Marina landing floral artwork";picture.transform.parent=root.transform;
        picture.transform.position=new Vector3(-.25f,6.475f,10.61f);picture.transform.localScale=new Vector3(.64f,.94f,1);
        picture.GetComponent<Renderer>().sharedMaterial=print;UnityEngine.Object.DestroyImmediate(picture.GetComponent<Collider>());
        foreach(var renderer in root.GetComponentsInChildren<Renderer>())renderer.shadowCastingMode=ShadowCastingMode.Off;
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    static void LandingConsoleSlab(GameObject root,string name,float radius,float depth,float bottom,float top,Material material)
    {
        var v=new List<Vector3>();var t=new List<int>();
        for(int i=0;i<=32;i++){
            float a=i*Mathf.PI/32,x=-.25f+radius*Mathf.Cos(a),z=10.65f-depth*Mathf.Sin(a);
            v.Add(new Vector3(x,bottom,z));v.Add(new Vector3(x,top,z));
            if(i>0){int k=2*(i-1);t.AddRange(new[]{k,k+2,k+1,k+1,k+2,k+3});}
        }
        for(int i=1;i<32;i++)t.AddRange(new[]{0,2*i,2*(i+1),1,2*(i+1)+1,2*i+1});
        t.AddRange(new[]{0,1,64,1,65,64});
        LandingMesh(root,name,v,t,material);
    }
    public static string CheckFilmRearLanding()
    {
        var root=GameObject.Find("Film rear landing");
        if(!root)throw new InvalidOperationException("Landing missing.");
        var mesh=root.GetComponentsInChildren<MeshFilter>().Single(m=>m.name=="Half round mahogany top").sharedMesh;
        if(mesh.vertices.Any(v=>v.z>10.6501f)||Mathf.Abs(mesh.bounds.size.z-.42f)>.001f)throw new InvalidOperationException("Console must have a flat back and shallow rounded front.");
        Physics.SyncTransforms();
        foreach(float x in new[]{-.9f,.3f,3.8f,4.5f}){
            if(!Physics.Raycast(new Vector3(x,5.8f,10.5f),Vector3.forward,out var hit,.2f)||!hit.collider.transform.IsChildOf(root.transform))throw new InvalidOperationException("Missing rear wall at "+x);
        }
        return "PASS flat-backed half-round console and continuous rear wall either side of window";
    }
    static void LandingMesh(GameObject root,string name,List<Vector3> vertices,List<int> triangles,Material material)
    {
        var mesh=new Mesh();mesh.SetVertices(vertices.Concat(vertices).ToList());mesh.SetTriangles(triangles.Concat(triangles.AsEnumerable().Reverse().Select(i=>i+vertices.Count)).ToArray(),0);mesh.RecalculateNormals();mesh.RecalculateBounds();
        string path="Assets/Materials/IntactFoyer/Landing"+name.Replace(" ","")+".asset";var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(saved){saved.Clear();saved.vertices=mesh.vertices;saved.triangles=mesh.triangles;saved.RecalculateNormals();saved.RecalculateBounds();UnityEngine.Object.DestroyImmediate(mesh);mesh=saved;EditorUtility.SetDirty(saved);}else AssetDatabase.CreateAsset(mesh,path);
        var go=Child(root,name);go.AddComponent<MeshFilter>().sharedMesh=mesh;go.AddComponent<MeshRenderer>().sharedMaterial=material;
    }
}
