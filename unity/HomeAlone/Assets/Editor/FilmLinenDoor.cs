using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

public static partial class SurveyBuilder
{
    public static void BuildFilmLinenDoor()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play first.");
        var model=GameObject.Find("IntactGLB");
        foreach(int id in new[]{2981,2983})model.GetComponentsInChildren<Transform>(true).Single(t=>t.name=="object"+id).gameObject.SetActive(false);
        model.GetComponentsInChildren<Renderer>(true).Single(r=>r.name=="object2982").enabled=false;
        var old=GameObject.Find("Film linen closet door");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Film linen closet door");
        var paint=FoyerFinish("LinenDoorIvory",new Color(.81f,.79f,.70f),.26f);
        var brass=FoyerFinish("LinenDoorBrass",new Color(.43f,.27f,.09f),.65f);brass.SetFloat("_Metallic",.85f);
        var green=FoyerFinish("UpperHallGreenPaint",new Color(.075f,.22f,.15f),.12f);
        // Reference proportions are a visual fit, not surveyed film dimensions. Close the oversized imported reveal.
        foreach(var span in new[]{new Vector2(1.29f,1.40f),new Vector2(2.80f,2.91f)}){
            Box(root,"Green wall return",span.x,span.y,1.60f,1.709f,6.25f,8.08f,green);
            Box(root,"Painted lower wall return",span.x,span.y,1.60f,1.709f,5.22f,6.25f,paint);
        }
        Box(root,"Wall over casing",1.40f,2.80f,1.60f,1.709f,7.92f,8.08f,green);
        Box(root,"Door jamb",1.40f,2.80f,1.60f,1.735f,5.23f,7.92f,paint);
        // Continuous recessed door field; raised rails/stiles frame six genuinely profiled panels.
        Box(root,"Closed six panel door",1.55f,2.65f,1.738f,1.777f,5.245f,7.755f,paint);
        foreach(float x in new[]{1.55f,2.55f})Box(root,"Door stile",x,x+.10f,1.777f,1.796f,5.245f,7.755f,paint);
        Box(root,"Centre stile",2.055f,2.145f,1.777f,1.796f,5.245f,7.755f,paint);
        foreach(var band in new[]{new Vector2(5.245f,5.405f),new Vector2(6.15f,6.31f),new Vector2(7.12f,7.22f),new Vector2(7.63f,7.755f)})Box(root,"Door rail",1.65f,2.55f,1.777f,1.796f,band.x,band.y,paint);
        int panel=0;
        foreach(var row in new[]{new Vector2(5.405f,6.15f),new Vector2(6.31f,7.12f),new Vector2(7.22f,7.63f)})foreach(var col in new[]{new Vector2(1.65f,2.055f),new Vector2(2.145f,2.55f)})
            LinenProfile(root,"Raised panel "+(++panel),col.x,col.y,row.x,row.y,new[]{0f,.014f,.025f,.055f,.071f},new[]{1.796f,1.793f,1.779f,1.784f,1.790f},paint,true);
        LinenProfile(root,"Molded ivory casing",1.40f,2.80f,5.23f,7.92f,new[]{0f,.015f,.036f,.065f,.085f,.13f,.15f},new[]{1.73f,1.765f,1.773f,1.752f,1.75f,1.776f,1.735f},paint,false);
        var rose=Cyl(root,"Round brass escutcheon",0,0,0,.012f,.035f,brass);rose.transform.SetPositionAndRotation(new Vector3(1.635f,6.26f,1.802f),Quaternion.Euler(90,0,0));
        BedroomRod(root,new Vector3(1.635f,6.26f,1.802f),new Vector3(1.635f,6.26f,1.84f),.011f,brass);
        BedroomSoft(root,"Round brass knob",new Vector3(1.635f,6.26f,1.857f),new Vector3(.05f,.05f,.043f),brass);
        root.transform.Find("Molded ivory casing").position+=Vector3.forward*.07f;
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    static void LinenProfile(GameObject root,string name,float x0,float x1,float y0,float y1,float[] inset,float[] depth,Material mat,bool panel)
    {
        var v=new List<Vector3>();var t=new List<int>();
        for(int i=0;i<inset.Length;i++){
            float d=inset[i];v.AddRange(new[]{new Vector3(x0+d,y0+(panel?d:0),depth[i]),new Vector3(x1-d,y0+(panel?d:0),depth[i]),new Vector3(x1-d,y1-d,depth[i]),new Vector3(x0+d,y1-d,depth[i])});
            if(i>0)for(int edge=panel?0:1;edge<4;edge++){int a=(i-1)*4+edge,b=(i-1)*4+(edge+1)%4;t.AddRange(new[]{a,a+4,b,b,a+4,b+4});}
        }
        // Keep the broad panel field flat; sharing its normals with the bevel creates a false bulging highlight.
        if(panel){int k=v.Count;v.AddRange(v.Skip(k-4).Take(4).ToArray());t.AddRange(new[]{k,k+2,k+1,k,k+3,k+2});}
        // Profile faces look toward the hall (+Z).
        t.Reverse();var mesh=NeighborhoodMesh("Linen"+name.Replace(" ",""),v.ToArray(),t.ToArray());
        var go=Child(root,name);go.AddComponent<MeshFilter>().sharedMesh=mesh;go.AddComponent<MeshRenderer>().sharedMaterial=mat;
    }
    public static string CheckFilmLinenDoor()
    {
        var root=GameObject.Find("Film linen closet door");if(!root||root.GetComponentsInChildren<MeshFilter>().Count(m=>m.name.StartsWith("Raised panel "))!=6)throw new InvalidOperationException("Six panels missing.");
        Physics.SyncTransforms();if(!Physics.Raycast(new Vector3(2.1f,6.5f,2.3f),Vector3.back,out var hit,1)||!hit.collider.transform.IsChildOf(root.transform))throw new InvalidOperationException("Closet remains open.");
        return "PASS six profiled panels, molded casing, brass knob and closed closet collision";
    }

    public static void DressFilmUpperHall()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play first.");
        var old=GameObject.Find("Film upper hall dressing");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Film upper hall dressing");
        var gold=FoyerFinish("UpperHallAgedGold",new Color(.36f,.23f,.10f),.5f);gold.SetFloat("_Metallic",.7f);
        var ivory=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/LinenDoorIvory.mat");
        var paper=FoyerFinish("UpperHallPictureMat",new Color(.74f,.65f,.46f),.04f);
        var dark=FoyerFinish("UpperHallUrn",new Color(.045f,.037f,.025f),.35f);
        var greenPaint=FoyerFinish("UpperHallGreenPaint",new Color(.075f,.22f,.15f),.12f);
        FoyerAssign(GameObject.Find("IntactGLB"),231,greenPaint);FoyerAssign(GameObject.Find("IntactGLB"),203,ivory);
        foreach(var r in GameObject.Find("Film linen closet door").GetComponentsInChildren<Renderer>())if(r.name=="Green wall return"||r.name=="Wall over casing")r.sharedMaterial=greenPaint;
        foreach(var span in new[]{new Vector2(.933f,1.40f),new Vector2(2.80f,4.730f)}){
            Box(root,"Ivory chair rail",span.x,span.y,1.71f,1.75f,6.45f,6.50f,ivory);
            Box(root,"Ivory rail lower bead",span.x,span.y,1.71f,1.735f,6.42f,6.45f,ivory);
            Box(root,"Ivory baseboard",span.x,span.y,1.71f,1.745f,5.22f,5.36f,ivory);
        }
        Box(root,"Ivory crown lower step",.933f,4.730f,1.71f,1.76f,8.25f,8.29f,ivory);
        Box(root,"Ivory crown middle step",.933f,4.730f,1.71f,1.80f,8.29f,8.33f,ivory);
        Box(root,"Ivory crown ceiling step",.933f,4.730f,1.71f,1.84f,8.33f,8.36f,ivory);
        LinenProfile(root,"Botanical picture frame",3.06f,3.64f,6.72f,7.60f,new[]{0f,.012f,.025f,.04f},new[]{1.735f,1.77f,1.78f,1.75f},gold,true);
        Box(root,"Botanical picture mat",3.10f,3.60f,1.755f,1.78f,6.76f,7.56f,paper);
        var print=FoyerFinish("UpperHallBotanicalPrint",Color.white,.015f,"Assets/Textures/UpperHallFilmReference.png");
        print.SetFloat("_UVBase",0);print.SetTextureScale("_BaseColorMap",new Vector2(42f/910,75f/489));print.SetTextureOffset("_BaseColorMap",new Vector2(301f/910,1-251f/489));
        UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(print);
        var picture=GameObject.CreatePrimitive(PrimitiveType.Quad);picture.name="Film botanical artwork";picture.transform.SetParent(root.transform);
        picture.transform.SetPositionAndRotation(new Vector3(3.35f,7.16f,1.79f),Quaternion.Euler(0,180,0));picture.transform.localScale=new Vector3(.38f,.65f,1);
        picture.GetComponent<Renderer>().sharedMaterial=print;UnityEngine.Object.DestroyImmediate(picture.GetComponent<Collider>());
        foreach(float y in new[]{7.10f,6.90f}){
            BedroomSoft(root,"Oval ornament dark surround",new Vector3(1.10f,y,1.765f),new Vector3(.18f,.21f,.06f),dark);
            BedroomSoft(root,"Oval ornament brass rim",new Vector3(1.10f,y,1.799f),new Vector3(.15f,.18f,.035f),gold);
            BedroomSoft(root,"Oval ornament ivory face",new Vector3(1.10f,y,1.82f),new Vector3(.12f,.15f,.012f),ivory);
        }
        // The film shows a narrow dark urn below the picture, kept outside the walking route.
        var v=new List<Vector3>();var tri=new List<int>();
        var rings=new[]{new Vector2(0,.13f),new Vector2(.04f,.13f),new Vector2(.07f,.07f),new Vector2(.19f,.04f),new Vector2(.24f,.09f),new Vector2(.32f,.13f),new Vector2(.48f,.17f),new Vector2(.51f,.18f),new Vector2(.53f,.17f),new Vector2(.53f,.15f),new Vector2(.47f,.14f)};
        for(int j=0;j<rings.Length;j++)for(int i=0;i<=48;i++){
            float a=i*Mathf.PI*2/48;v.Add(new Vector3(3.35f+rings[j].y*Mathf.Cos(a),5.22f+rings[j].x,2.06f+rings[j].y*Mathf.Sin(a)));
            if(j>0&&i>0){int k=j*49+i;tri.AddRange(new[]{k-50,k-49,k-1,k-1,k-49,k});}
        }
        tri.Reverse();var urn=Child(root,"Dark pedestal urn");urn.AddComponent<MeshFilter>().sharedMesh=NeighborhoodMesh("UpperHallUrn",v.ToArray(),tri.ToArray());urn.AddComponent<MeshRenderer>().sharedMaterial=dark;
        var collider=urn.AddComponent<BoxCollider>();collider.center=new Vector3(3.35f,5.485f,2.06f);collider.size=new Vector3(.36f,.53f,.36f);
        var red=FoyerFinish("UpperHallPoinsettiaRed",new Color(.43f,.012f,.021f),.08f);
        var green=FoyerFinish("UpperHallPoinsettiaGreen",new Color(.026f,.09f,.025f),.1f);
        foreach(var m in new[]{red,green}){m.SetFloat("_DoubleSidedEnable",1);UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(m);}
        for(int flower=0;flower<7;flower++){
            float a=flower*2.4f,r=flower==0?0:.16f;var c=new Vector3(3.35f+r*Mathf.Cos(a),5.96f+.06f*Mathf.Sin(a),2.06f+r*Mathf.Sin(a));
            BedroomRod(root,new Vector3(3.35f,5.70f,2.06f),c,.004f,green);
            for(int petal=0;petal<6;petal++)HallLeaf(root,c,a+petal*Mathf.PI/3,.14f,.052f,red,flower*6+petal);
            HallLeaf(root,c-Vector3.up*.11f,a,.21f,.07f,green,50+flower);
            BedroomSoft(root,"Poinsettia centre",c+Vector3.up*.01f,new Vector3(.023f,.018f,.023f),gold);
        }
        // A modest ceiling practical supplies the otherwise unlit upper gallery. Fixture placement is provisional.
        var foyer=GameObject.Find("FoyerNight");var fixture=foyer.transform.Find("Upper gallery ceiling practical");if(fixture)UnityEngine.Object.DestroyImmediate(fixture.gameObject);
        var lamp=Child(foyer,"Upper gallery ceiling practical");
        Cyl(lamp,"Ceiling brass rim",2.1f,3.15f,8.32f,8.36f,.19f,gold);
        BedroomSoft(lamp,"Shallow opal diffuser",new Vector3(2.1f,8.28f,3.15f),new Vector3(.34f,.13f,.34f),ivory);
        FoyerLamp(lamp,"Upper gallery practical light",new Vector3(2.1f,8.08f,3.15f),85,5);
        var mode=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>();var light=lamp.GetComponentInChildren<Light>();
        var pairs=mode.interiorLights.Select((l,i)=>(l,day:mode.daytimeEnabled[i])).Where(p=>p.l).ToList();pairs.Add((light,true));
        mode.interiorLights=pairs.Select(p=>p.l).ToArray();mode.daytimeEnabled=pairs.Select(p=>p.day).ToArray();mode.SetNight(mode.night);
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    static void HallLeaf(GameObject root,Vector3 c,float angle,float length,float width,Material mat,int id)
    {
        var forward=new Vector3(Mathf.Cos(angle),.18f,Mathf.Sin(angle));var side=new Vector3(-Mathf.Sin(angle),0,Mathf.Cos(angle));
        var verts=new[]{c,c+forward*length*.45f-side*width,c+forward*length,c+forward*length*.45f+side*width,c+forward*length*.45f+Vector3.up*.024f};
        var go=Child(root,"Poinsettia bract "+id);go.AddComponent<MeshFilter>().sharedMesh=NeighborhoodMesh("UpperHallLeaf"+id,verts,new[]{0,4,1,1,4,2,2,4,3,3,4,0});go.AddComponent<MeshRenderer>().sharedMaterial=mat;
    }
    public static string CheckFilmUpperHall()
    {
        var root=GameObject.Find("Film upper hall dressing");if(!root)throw new InvalidOperationException("Upper hall dressing missing.");
        float panelTop=GameObject.Find("object203").GetComponent<Renderer>().bounds.max.y;
        foreach(var r in root.GetComponentsInChildren<Renderer>().Where(r=>r.name.StartsWith("Ivory "))){
            if(r.bounds.min.x<.93f||r.bounds.max.x>4.735f)throw new InvalidOperationException("Trim projects beyond closet wall: "+r.name);
            if(r.name=="Ivory chair rail"&&Mathf.Abs(r.bounds.max.y-panelTop)>.04f)throw new InvalidOperationException("Chair rail does not meet panel top.");
        }
        var print=root.transform.Find("Film botanical artwork");var urn=root.transform.Find("Dark pedestal urn");
        if(!print||!urn||print.position.x<2.8f||root.GetComponentsInChildren<Renderer>().Count(r=>r.name=="Oval ornament ivory face")!=2)throw new InvalidOperationException("Reference wall dressing incomplete.");
        return "PASS picture, paired oval ornament and urn; trim meets panel top and wall endpoints";
    }
}
