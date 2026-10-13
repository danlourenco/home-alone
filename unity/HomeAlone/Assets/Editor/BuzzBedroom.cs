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
    [MenuItem("HomeAlone/Reference/Furnish Buzz Bedroom")]
    public static void FurnishBuzzBedroom()
    {
        if(EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var old=GameObject.Find("BuzzBedroomDetails");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("BuzzBedroomDetails");
        var wood=FoyerFinish("BuzzWalnut",new Color(.52f,.36f,.20f),.26f,"Assets/Textures/wood_floor_diff.jpg",.8f);
        var green=FoyerFinish("BuzzGreenCloth",new Color(.09f,.20f,.105f),.06f);
        var ivory=FoyerFinish("BuzzIvory",new Color(.88f,.86f,.77f),.12f);
        var black=FoyerFinish("BuzzBlack",new Color(.018f,.022f,.02f),.2f);
        var red=FoyerFinish("BuzzRed",new Color(.5f,.025f,.035f),.2f);
        var brass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/AntiqueBrass.mat");
        // Film/reference anchors: headboard east, shelves north, desk/Jordan west, dresser south.
        var source=GameObject.Find("IntactGLB").GetComponentsInChildren<Renderer>();
        source.Single(r=>r.name=="object242").enabled=false;
        source.Single(r=>r.name=="object43").enabled=false;
        var wall=source.Single(r=>r.name=="object50").sharedMaterial;
        // Close the unsupported side-wing doorway. Wing remains accessible from the rear bedroom.
        Box(root,"Film desk wall - former side wing doorway",-6.285f,-6.10f,.20f,1.56f,5.22f,8.0f,wall);
        foreach(var r in source.Where(r=>r.name=="object24"||r.name=="object25"))r.transform.position+=new Vector3(-5.86f,6.13f,-.48f)-r.bounds.center;
        var bed=Child(root,"Buzz wooden bed");
        Box(bed,"Bed frame",-4.70f,-3.40f,-1.04f,1.34f,5.49f,5.65f,wood);
        Box(bed,"Mattress",-4.66f,-3.44f,-1.00f,1.30f,5.65f,5.87f,ivory);
        Box(bed,"Green quilt",-4.68f,-3.42f,-1.01f,.76f,5.87f,5.92f,green);
        foreach(float x in new[]{-4.68f,-3.42f})Box(bed,"Quilt drop",x-.018f,x+.018f,-.97f,.75f,5.62f,5.91f,green);
        BedroomSoft(bed,"Pillow",new Vector3(-4.05f,6.01f,1.03f),new Vector3(1.03f,.24f,.43f),ivory);
        foreach(float x in new[]{-4.73f,-3.37f})foreach(float z in new[]{-1.08f,1.38f}){
            float top=z>0?6.75f:6.11f;
            Cyl(bed,"Turned bedpost",x,z,5.22f,top,.035f,wood);
            BedroomSoft(bed,"Post finial",new Vector3(x,top,z),new Vector3(.12f,.16f,.12f),wood);
        }
        foreach(float z in new[]{-1.08f,1.38f}){
            float top=z>0?6.45f:5.99f;
            Box(bed,"Shaped board centre",-4.40f,-3.70f,z-.035f,z+.035f,5.64f,top+.11f,wood);
            Box(bed,"Board shoulders",-4.73f,-3.37f,z-.03f,z+.03f,top-.16f,top,wood);
            for(int i=0;i<7;i++)Cyl(bed,"Board spindle",-4.64f+i*.20f,z,5.64f,top-.14f,.016f,wood);
        }
        // Marina Part 2 0:50: offset toward hall, preserving bed size; inferred, not surveyed.
        bed.transform.SetPositionAndRotation(new Vector3(-2.85f,0,-4.15f),Quaternion.Euler(0,90,0));
        var beside=Child(root,"Buzz bedside table and lamp");
        Box(beside,"Bedside cabinet",-3.14f,-2.52f,.91f,1.54f,5.22f,5.91f,wood);
        for(int i=0;i<2;i++)Box(beside,"Bedside drawer",-3.10f,-2.56f,.88f,.90f,5.32f+i*.26f,5.54f+i*.26f,wood);
        Cyl(beside,"Bedside lamp",-2.82f,1.19f,5.92f,6.30f,.025f,brass);
        FixtureShade(beside,"Green bedside shade",new Vector3(-2.82f,6.20f,1.19f),green,new[]{new Vector2(.21f,0),new Vector2(.13f,.23f)});
        beside.transform.position=new Vector3(1.10f,0,-2.59f);
        var dresser=Child(root,"Window chest of drawers");
        Box(dresser,"Chest",-3.91f,-3.19f,-2.21f,-1.74f,5.22f,6.25f,wood);
        Box(dresser,"Chest top",-3.95f,-3.15f,-2.24f,-1.70f,6.25f,6.30f,wood);
        for(int i=0;i<4;i++){
            float y=5.30f+i*.23f;Box(dresser,"Drawer",-3.87f,-3.23f,-1.73f,-1.70f,y,y+.19f,wood);
            BedroomRod(dresser,new Vector3(-3.69f,y+.09f,-1.68f),new Vector3(-3.43f,y+.09f,-1.68f),.01f,brass);
        }
        // West-wall shelves above the source desk, with the terrarium on the lowest shelf.
        var shelves=Child(root,"Buzz display shelves");
        foreach(float z in new[]{-1.95f,-1.15f,-.35f})Box(shelves,"Shelf standard",-6.04f,-5.98f,z-.025f,z+.025f,5.48f,7.70f,wood);
        foreach(float y in new[]{5.63f,6.255f,6.99f,7.66f})Box(shelves,"Display shelf",-6.05f,-5.61f,-2.08f,-.24f,y,y+.035f,wood);
        for(int row=0;row<3;row++)for(int i=0;i<5;i++){
            float y=(row==0?5.675f:7.035f),z=-1.94f+i*.30f;
            if(row==2)break;
            Box(shelves,"Board game box",-6.0f,-5.66f,z,z+.24f,y,y+.07f+(i%2)*.04f,i%2==0?red:green);
        }
        for(int i=0;i<4;i++){
            float z=-1.91f+i*.42f;
            Cyl(shelves,"Trophy base",-5.81f,z,7.70f,7.74f,.07f,black);
            Cyl(shelves,"Trophy stem",-5.81f,z,7.74f,7.88f,.014f,brass);
            BedroomSoft(shelves,"Trophy cup",new Vector3(-5.81f,7.88f,z),new Vector3(.11f,.11f,.10f),brass);
        }
        shelves.transform.localScale=new Vector3(1,1,1.7f);
        shelves.transform.SetPositionAndRotation(new Vector3(-1.864f,0,-4.30f),Quaternion.Euler(0,90,0));
        BuzzPicture(root,"Ice T poster","BedWallReference.jpg",new UnityEngine.Rect(1190f/1920,1-540f/1080,190f/1920,335f/1080),new Vector3(-1.33f,7.14f,-1.12f),new Vector2(.64f,1.0f),90);
        BuzzPicture(root,"Basketball poster","SportsReference.jpg",new UnityEngine.Rect(1030f/1920,1-290f/1080,300f/1920,290f/1080),new Vector3(-3.55f,7.08f,-2.25f),new Vector2(.70f,.72f),180);
        BuzzPicture(root,"Desk bulletin board","DeskReference.jpg",new UnityEngine.Rect(560f/1920,1-505f/1080,730f/1920,490f/1080),new Vector3(-6.075f,7.13f,-.35f),new Vector2(1.10f,.76f),270);
        Box(root,"Desk papers",-5.98f,-5.68f,-.95f,-.72f,6.08f,6.10f,ivory);
        Cyl(root,"Bulls red wastebasket",-1.60f,-1.90f,5.22f,5.64f,.16f,red);
        Box(root,"Basketball backboard",-1.35f,-1.32f,-1.86f,-1.25f,6.5f,6.98f,ivory);
        for(int i=0;i<24;i++){
            float a=i*Mathf.PI/12,b=(i+1)*Mathf.PI/12;
            BedroomRod(root,new Vector3(-1.51f+.13f*Mathf.Cos(a),6.56f,-1.55f+.13f*Mathf.Sin(a)),new Vector3(-1.51f+.13f*Mathf.Cos(b),6.56f,-1.55f+.13f*Mathf.Sin(b)),.009f,red);
        }
        // Remove only the old detached shelf fragments within this room from the combined prop mesh.
        foreach(var id in new[]{130,182,184,196,203,204,213,217,221,223,227,229,231,2924}){
            var mf=source.Single(r=>r.name=="object"+id).GetComponent<MeshFilter>();
            var cut=CutWindowTriangles(mf.sharedMesh,mf.transform,new List<(Vector3,float,float,float,int,int,string)>{(new Vector3(-3.7f,6.65f,1.65f),4.4f,2f,0,1,1,"Old Buzz shelf fragments")},out var removed);
            if(removed==0){UnityEngine.Object.DestroyImmediate(cut);continue;}
            string cutPath="Assets/Materials/IntactFoyer/BuzzOldShelfCut_"+id+".asset";var savedCut=AssetDatabase.LoadAssetAtPath<Mesh>(cutPath);
            if(savedCut){EditorUtility.CopySerialized(cut,savedCut);UnityEngine.Object.DestroyImmediate(cut);}else{savedCut=cut;AssetDatabase.CreateAsset(savedCut,cutPath);}
            EditorUtility.SetDirty(savedCut);mf.sharedMesh=savedCut;mf.GetComponent<MeshCollider>().sharedMesh=savedCut;
        }
        AddBuzzJordan(root);
        AddBuzzTerrarium(root);
        DressBuzzWindows();
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static void DressBuzzWindows()
    {
        if(EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var room=GameObject.Find("BuzzBedroomDetails");
        if(!room)throw new InvalidOperationException("Furnish Buzz first.");
        // Replace the old front-only dressing; leave furniture and imported openings intact.
        foreach(Transform child in room.transform.Cast<Transform>().ToArray())
            if(child.name=="Buzz window interiors"||child.name=="Green curtain fold"||
               (child.name=="Curved brass screen"&&child.position.y>7.7f&&child.position.z< -2f))
                UnityEngine.Object.DestroyImmediate(child.gameObject);
        var root=Child(room,"Buzz window interiors");
        var trim=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/FrontWindowIvory.mat");
        var cloth=FoyerFinish("BuzzCurtainCloth",new Color(.09f,.20f,.105f),.06f);
        cloth.SetFloat("_DoubleSidedEnable",1);HDMaterial.ValidateMaterial(cloth);
        var wood=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/BuzzWalnut.mat");
        var specs=ExteriorWindowOpenings().Where(s=>s.center.x> -7&&s.center.x<0&&s.center.y>6&&s.center.y<7&&s.center.z<0).ToArray();
        if(specs.Length!=3||!trim||!wood)throw new InvalidOperationException("Expected three Buzz windows and existing trim materials.");
        for(int index=0;index<specs.Length;index++){
            var s=specs[index];float w=s.w/2,h=s.h/2;
            var window=Child(root,"Buzz interior window "+index);
            foreach(float side in new[]{-1f,1f}){
                float x=side*w;
                Box(window,"Ivory reveal",x-.019f,x+.019f,.14f,.205f,-h+.03f,h-.03f,trim);
                x=side*(w+.055f);
                Box(window,"Interior casing",x-.055f,x+.055f,.205f,.245f,-h,h+.03f,trim);
            }
            Box(window,"Head reveal",-w,w,.14f,.205f,h-.03f,h+.03f,trim);
            Box(window,"Casing head",-w-.11f,w+.11f,.205f,.245f,h+.03f,h+.13f,trim);
            Box(window,"Interior sill",-w-.13f,w+.13f,.14f,.31f,-h-.035f,-h+.025f,trim);
            Box(window,"Sill apron",-w-.08f,w+.08f,.205f,.24f,-h-.13f,-h-.035f,trim);
            BedroomRod(window,new Vector3(-w-.32f,h+.18f,.33f),new Vector3(w+.32f,h+.18f,.33f),.017f,wood);
            var vertices=new List<Vector3>();var triangles=new List<int>();
            foreach(float side in new[]{-1f,1f}){
                int start=vertices.Count;
                for(int i=0;i<=24;i++){
                    float u=i/24f,x=side*(w-.035f+u*.29f),z=.33f+.025f*Mathf.Cos(u*Mathf.PI*10);
                    vertices.Add(new Vector3(x,h+.15f,z));vertices.Add(new Vector3(x,-h-.075f,z));
                    if(i<24){int k=start+i*2;triangles.AddRange(new[]{k,k+1,k+2,k+1,k+3,k+2});}
                }
            }
            var curtains=Child(window,"Green pleated curtains");
            curtains.AddComponent<MeshFilter>().sharedMesh=NeighborhoodMesh("BuzzWindowCurtain"+index,vertices.ToArray(),triangles.ToArray());
            curtains.AddComponent<MeshRenderer>().sharedMaterial=cloth;
            // Dressing must not add invisible obstacles or enter the existing lightmap atlas.
            foreach(var c in window.GetComponentsInChildren<Collider>())UnityEngine.Object.DestroyImmediate(c);
            foreach(var r in window.GetComponentsInChildren<Renderer>())GameObjectUtility.SetStaticEditorFlags(r.gameObject,0);
            window.transform.SetPositionAndRotation(s.center,Quaternion.Euler(0,s.yaw,0));
        }
    }
    public static string CheckBuzzWindows()
    {
        var root=GameObject.Find("BuzzBedroomDetails/Buzz window interiors");
        if(!root||root.transform.childCount!=3||root.GetComponentsInChildren<Collider>().Length!=0)throw new InvalidOperationException("Incomplete or obstructing Buzz window dressing.");
        var sills=root.GetComponentsInChildren<Renderer>().Where(r=>r.name=="Interior sill").ToArray();
        if(sills.Length!=3||sills.Max(r=>r.bounds.max.y)-sills.Min(r=>r.bounds.max.y)>.003f)throw new InvalidOperationException("Buzz sill elevations differ.");
        foreach(Transform window in root.transform)
            if(!window.Find("Green pleated curtains")||window.GetComponentsInChildren<Renderer>().Count(r=>r.name=="Interior casing")!=2)throw new InvalidOperationException("Missing Buzz curtain or casing.");
        return "PASS three dressed windows, aligned interior sills within 3mm, no dressing colliders. "+CheckFrontWindows();
    }
    static Material BuzzPrint(string file)
    {
        var mat=FoyerFinish("BuzzPrint"+file.Replace(".jpg",""),Color.white,.03f,"Assets/Textures/Buzz/"+file);
        mat.SetFloat("_UVBase",0);mat.SetTextureScale("_BaseColorMap",Vector2.one);mat.SetFloat("_DoubleSidedEnable",1);HDMaterial.ValidateMaterial(mat);return mat;
    }
    static void BuzzPicture(GameObject root,string name,string file,UnityEngine.Rect uv,Vector3 pos,Vector2 size,float yaw)
    {
        var go=GameObject.CreatePrimitive(PrimitiveType.Quad);go.name=name;go.transform.parent=root.transform;
        go.transform.SetPositionAndRotation(pos,Quaternion.Euler(0,yaw,0));go.transform.localScale=new Vector3(size.x,size.y,1);
        UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
        var mat=BuzzPrint(file);go.GetComponent<Renderer>().sharedMaterial=mat;
        // Keep each print crop serialized with the scene.
        string path="Assets/Materials/IntactFoyer/Buzz"+name.Replace(" ","")+".mat";
        var saved=AssetDatabase.LoadAssetAtPath<Material>(path);if(!saved){saved=new Material(mat);AssetDatabase.CreateAsset(saved,path);}else EditorUtility.CopySerialized(mat,saved);
        saved.SetTextureScale("_BaseColorMap",uv.size);saved.SetTextureOffset("_BaseColorMap",uv.position);EditorUtility.SetDirty(saved);go.GetComponent<Renderer>().sharedMaterial=saved;go.GetComponent<Renderer>().SetPropertyBlock(null);
    }
    static void AddBuzzJordan(GameObject root)
    {
        // Trace the photographed 1987 standee silhouette in texture pixels; preserve the leg gap.
        var v=new List<Vector3>();var uv=new List<Vector2>();var t=new List<int>();
        void Strip(float[,] rows){int start=v.Count;for(int i=0;i<rows.GetLength(0);i++)for(int side=1;side<=2;side++){
            float x=rows[i,side],y=rows[i,0];v.Add(new Vector3((x-355)/1380f*2.01f,(1540-y)/1380f*2.01f,0));uv.Add(new Vector2(x/714f,1-y/1600f));
        }for(int i=0;i<rows.GetLength(0)-1;i++){int k=start+i*2;t.AddRange(new[]{k,k+2,k+1,k+1,k+2,k+3});}}
        Strip(new float[,]{{162,398,425},{177,373,446},{206,361,464},{245,351,474},{277,353,475},{320,369,461},{343,342,471},{366,289,520},{403,248,561},{460,226,583},{525,203,606},{575,174,610},{635,144,601},{695,124,565},{727,111,551},{770,99,539},{813,109,543},{858,155,550},{884,254,552},{916,281,544},{940,335,494}});
        Strip(new float[,]{{884,264,417},{940,274,389},{1000,277,371},{1100,265,350},{1200,260,338},{1305,268,320},{1370,269,324},{1430,254,331},{1500,240,320},{1538,251,306}});
        Strip(new float[,]{{884,414,550},{940,432,550},{1000,450,549},{1100,469,551},{1200,486,560},{1305,501,555},{1370,504,557},{1430,493,568},{1480,492,594},{1500,515,598}});
        var mesh=new Mesh();mesh.SetVertices(v);mesh.SetUVs(0,uv);mesh.SetTriangles(t,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
        const string path="Assets/Materials/IntactFoyer/BuzzJordanSilhouette.asset";var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(saved){EditorUtility.CopySerialized(mesh,saved);UnityEngine.Object.DestroyImmediate(mesh);mesh=saved;}else AssetDatabase.CreateAsset(mesh,path);
        var go=Child(root,"Michael Jordan cutout");go.AddComponent<MeshFilter>().sharedMesh=mesh;go.AddComponent<MeshRenderer>().sharedMaterial=BuzzPrint("Jordan.jpg");
        go.transform.SetPositionAndRotation(new Vector3(-6.055f,5.23f,1.15f),Quaternion.Euler(0,270,0));
        Box(root,"Cutout support foot",-6.06f,-5.90f,.96f,1.34f,5.22f,5.25f,FoyerFinish("BuzzCardboard",new Color(.30f,.23f,.13f),.02f));
    }
    static void AddBuzzTerrarium(GameObject root)
    {
        var tank=Child(root,"Buzz tarantula terrarium");
        var rim=FoyerFinish("BuzzTankRim",new Color(.015f,.022f,.021f),.3f);
        var earth=FoyerFinish("BuzzSoil",new Color(.16f,.085f,.035f),.02f);
        var glass=FoyerFinish("BuzzTankGlass",new Color(.85f,.93f,.91f,.055f),.85f);
        glass.SetFloat("_SurfaceType",1);glass.SetFloat("_ZWrite",0);glass.SetFloat("_TransparentZWrite",0);glass.SetFloat("_DoubleSidedEnable",1);HDMaterial.ValidateMaterial(glass);
        Box(tank,"Tank base",-.46f,.46f,-.22f,.22f,0,.035f,rim);
        Box(tank,"Soil substrate",-.44f,.44f,-.20f,.20f,.035f,.07f,earth);
        foreach(float y in new[]{.03f,.48f}){
            foreach(float z in new[]{-.215f,.215f})Box(tank,"Long frame",-.46f,.46f,z-.012f,z+.012f,y,y+.023f,rim);
            foreach(float x in new[]{-.448f,.448f})Box(tank,"End frame",x-.012f,x+.012f,-.20f,.20f,y,y+.023f,rim);
        }
        foreach(float x in new[]{-.448f,.448f})foreach(float z in new[]{-.215f,.215f})Box(tank,"Glass corner",x-.01f,x+.01f,z-.01f,z+.01f,.05f,.48f,rim);
        // Single-surface panes avoid doubled transparent faces and have no collision/shadows.
        foreach(var spec in new[]{(new Vector3(0,.265f,-.215f),new Vector2(.88f,.43f),0f),(new Vector3(0,.265f,.215f),new Vector2(.88f,.43f),180f),(new Vector3(-.448f,.265f,0),new Vector2(.40f,.43f),90f),(new Vector3(.448f,.265f,0),new Vector2(.40f,.43f),270f)}){
            var pane=GameObject.CreatePrimitive(PrimitiveType.Quad);pane.name="Terrarium glass";pane.transform.parent=tank.transform;
            pane.transform.SetPositionAndRotation(spec.Item1,Quaternion.Euler(0,spec.Item3,0));pane.transform.localScale=new Vector3(spec.Item2.x,spec.Item2.y,1);
            UnityEngine.Object.DestroyImmediate(pane.GetComponent<Collider>());pane.GetComponent<Renderer>().sharedMaterial=glass;pane.GetComponent<Renderer>().shadowCastingMode=ShadowCastingMode.Off;
        }
        for(int i=0;i<14;i++){float x=-.42f+i*.065f;Box(tank,"Ventilated lid",x,x+.002f,-.20f,.20f,.501f,.503f,rim);}
        BedroomSoft(tank,"Cork hide",new Vector3(.31f,.13f,.105f),new Vector3(.20f,.13f,.15f),earth);
        Cyl(tank,"Shallow water dish",-.31f,.115f,.07f,.082f,.05f,rim);
        var spider=Child(tank,"Tarantula");var body=FoyerFinish("TarantulaUmber",new Color(.065f,.029f,.014f),.06f);
        var knee=FoyerFinish("TarantulaKnee",new Color(.26f,.105f,.035f),.08f);
        BedroomSoft(spider,"Furry abdomen",new Vector3(0,.034f,-.035f),new Vector3(.061f,.049f,.08f),body);
        BedroomSoft(spider,"Cephalothorax",new Vector3(0,.034f,.018f),new Vector3(.048f,.030f,.050f),body);
        var animation=spider.AddComponent<TerrariumTarantula>();animation.legs=new Transform[8];
        for(int i=0;i<8;i++){
            float side=i<4?-1:1,z=.041f-(i%4)*.021f;
            var leg=Child(spider,"Leg "+(i+1));animation.legs[i]=leg.transform;
            var hip=new Vector3(side*.018f,.029f,z);var joint=new Vector3(side*.070f,.055f,z+(1.5f-i%4)*.022f);var foot=new Vector3(side*.098f,.003f,z+(1.5f-i%4)*.036f);
            BedroomRod(leg,hip,joint,.006f,body);BedroomRod(leg,joint,foot,.0038f,body);
            BedroomSoft(leg,"Rust knee hairs",joint,new Vector3(.014f,.015f,.014f),knee);
        }
        foreach(float x in new[]{-.012f,.012f})BedroomRod(spider,new Vector3(x,.026f,.035f),new Vector3(x*1.6f,.012f,.064f),.004f,body);
        foreach(var c in tank.GetComponentsInChildren<Collider>())UnityEngine.Object.DestroyImmediate(c);
        animation.Pose(0);spider.transform.localPosition+=Vector3.up*.07f;
        // Patrol uses a separate floor parent so the animation stays above the substrate.
        var habitat=Child(tank,"Spider substrate origin");habitat.transform.localPosition=new Vector3(0,.07f,0);spider.transform.SetParent(habitat.transform,false);animation.Pose(0);
        tank.transform.SetPositionAndRotation(new Vector3(-4.73f,6.29f,1.50f),Quaternion.Euler(0,180,0));
    }
    public static string CheckBuzzBedroom()
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Enter Play first.");
        var root=GameObject.Find("BuzzBedroomDetails");var spider=root.GetComponentInChildren<TerrariumTarantula>();
        if(!root.transform.Find("Michael Jordan cutout")||spider==null||spider.legs.Length!=8)throw new InvalidOperationException("Missing signature Buzz props.");
        var position=spider.transform.localPosition;var rotation=spider.transform.localRotation;
        try{for(int i=0;i<600;i++){spider.Pose(i*.1f);foreach(var r in spider.GetComponentsInChildren<Renderer>()){
            var local=spider.transform.parent.InverseTransformPoint(r.bounds.center);
            if(Mathf.Abs(local.x)>.43f||Mathf.Abs(local.z)>.20f||local.y<0)throw new InvalidOperationException("Spider left terrarium.");
        }}spider.Pose(0);var start=spider.transform.localPosition;spider.Pose(4);if(Vector3.Distance(start,spider.transform.localPosition)<.01f)throw new InvalidOperationException("Spider does not move.");}
        finally{spider.transform.localPosition=position;spider.transform.localRotation=rotation;}
        var fps=GameObject.Find("Player").GetComponent<FpsController>();var cc=fps.GetComponent<CharacterController>();var original=fps.transform.position;bool enabled=fps.enabled;
        var route=new[]{new Vector3(-.50f,5.22f,1.04f),new Vector3(-2.05f,5.22f,1.04f),new Vector3(-4.5f,5.22f,.70f),new Vector3(-4.5f,5.22f,-.5f),new Vector3(-4.5f,5.22f,-1.42f),new Vector3(-2.6f,5.22f,-1.38f),new Vector3(-4.5f,5.22f,-1.42f)};
        try{fps.enabled=false;cc.enabled=false;fps.transform.position=route[0]+Vector3.up*.12f;cc.enabled=true;Physics.SyncTransforms();
            foreach(var target in route.Concat(route.Reverse())){
                for(int i=0;i<600;i++){var d=target-fps.transform.position;d.y=0;if(d.magnitude<.08f)break;fps.TickMotion(d,false,false,1f/60);}
                for(int i=0;i<60;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
                if(Vector3.Distance(target,fps.transform.position)>.18f||!cc.isGrounded)throw new InvalidOperationException($"Buzz route blocked at {fps.transform.position}; target {target}");
            }
        }finally{cc.enabled=false;fps.transform.position=original;cc.enabled=true;fps.enabled=enabled;}
        var wingRoute=new[]{new Vector3(-4.8f,5.22f,6.43f),new Vector3(-7.3f,5.22f,6.43f),new Vector3(-8.6f,5.22f,4.8f),new Vector3(-8.6f,5.22f,1f)};
        try{fps.enabled=false;cc.enabled=false;fps.transform.position=wingRoute[0]+Vector3.up*.12f;cc.enabled=true;Physics.SyncTransforms();
            foreach(var target in wingRoute.Concat(wingRoute.Reverse())){
                for(int i=0;i<600;i++){var d=target-fps.transform.position;d.y=0;if(d.magnitude<.08f)break;fps.TickMotion(d,false,false,1f/60);}
                for(int i=0;i<60;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
                if(Vector3.Distance(target,fps.transform.position)>.18f||!cc.isGrounded)throw new InvalidOperationException($"Side wing route blocked at {fps.transform.position}; target {target}");
            }
        }finally{cc.enabled=false;fps.transform.position=original;cc.enabled=true;fps.enabled=enabled;}
        return "PASS side wing alternate entry, Buzz furnishings, Jordan cutout, eight animated legs, 60-second tank containment and 14 walking checkpoints.";
    }
}
