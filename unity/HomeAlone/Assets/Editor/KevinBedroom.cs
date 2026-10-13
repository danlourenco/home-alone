using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Furnish Kevin Bedroom")]
    public static void FurnishKevinBedroom()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open IntactHouseReference outside Play.");
        var old=GameObject.Find("KevinBedroomDetails");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("KevinBedroomDetails");
        // Keep the source props, but move them out of the new circulation route.
        var props=GameObject.Find("IntactGLB").GetComponentsInChildren<Renderer>();
        var shoes=props.Single(r=>r.name=="object15");shoes.transform.position+=new Vector3(5.35f,5.33f,-.25f)-shoes.bounds.center;
        var ball=props.Single(r=>r.name=="object0");ball.transform.position+=new Vector3(6.60f,5.40f,-2.02f)-ball.bounds.center;
        var wood=FoyerFinish("KevinHoneyWood",new Color(.43f,.27f,.12f),.3f);
        var green=FoyerFinish("KevinGreenBedding",new Color(.055f,.25f,.13f),.08f);
        var ivory=FoyerFinish("KevinIvory",new Color(.93f,.91f,.81f),.18f);
        var red=FoyerFinish("KevinRustRed",new Color(.52f,.09f,.035f),.2f);
        var blue=FoyerFinish("KevinBookBlue",new Color(.08f,.18f,.28f),.2f);
        var brass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/AntiqueBrass.mat");
        var mirror=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/ParentsMirror.mat");
        var paper=KevinPattern("KevinSmallMotif",false);
        GameObject.Find("IntactGLB").GetComponentsInChildren<MeshRenderer>().Single(r=>r.name=="object81").sharedMaterial=paper;
        GameObject.Find("IntactGLB").GetComponentsInChildren<MeshRenderer>().Single(r=>r.name=="object80").sharedMaterial=paper;
        var plaid=KevinPattern("KevinCurtainCheck",true);
        // Shared bunk beds beside the entry, head against the back wall; floor Y5.21.
        var bed=Child(root,"Wooden bunk beds");
        foreach(float x in new[]{7.08f,8.22f})foreach(float z in new[]{-.46f,1.86f})Box(bed,"Square bedpost",x-.035f,x+.035f,z-.035f,z+.035f,5.22f,7.46f,wood);
        foreach(float y in new[]{5.55f,6.83f}){
            Box(bed,"Bed frame",7.08f,8.22f,-.46f,1.86f,y,y+.12f,wood);
            Box(bed,"Ivory mattress",7.13f,8.17f,-.41f,1.80f,y+.12f,y+.27f,ivory);
            Box(bed,"Green quilt",7.11f,8.19f,-.43f,1.42f,y+.27f,y+.32f,green);
            foreach(float x in new[]{7.105f,8.185f})Box(bed,"Quilt side",x-.018f,x+.018f,-.40f,1.40f,y+.08f,y+.31f,green);
            BedroomSoft(bed,"Ivory pillow",new Vector3(7.65f,y+.36f,1.59f),new Vector3(.83f,.18f,.37f),ivory);
            foreach(float z in new[]{-.46f,1.86f}){
                Box(bed,"End rail",7.10f,8.20f,z-.025f,z+.025f,y+.51f,y+.59f,wood);
                for(int i=0;i<5;i++){float x=7.23f+i*.21f;Box(bed,"End spindle",x,x+.025f,z-.02f,z+.02f,y+.12f,y+.52f,wood);}
            }
        }
        Box(bed,"Upper guard rail",7.07f,7.11f,-.43f,1.84f,7.36f,7.44f,wood);
        Box(bed,"Upper guard beside ladder",8.20f,8.24f,.32f,1.84f,7.36f,7.44f,wood);
        foreach(float z in new[]{-.25f,.21f})Box(bed,"Ladder upright",8.26f,8.31f,z,z+.04f,5.22f,7.14f,wood);
        for(int i=0;i<6;i++){float y=5.43f+i*.28f;Box(bed,"Ladder rung",8.25f,8.32f,-.25f,.25f,y,y+.04f,wood);}
        var dresser=Child(root,"Honey wood dresser");
        Box(dresser,"Dresser body",9.24f,9.76f,.20f,1.72f,5.26f,6.13f,wood);
        Box(dresser,"Dresser top",9.19f,9.81f,.15f,1.77f,6.13f,6.20f,wood);
        for(int i=0;i<3;i++)for(int j=0;j<2;j++){
            float y=5.34f+i*.25f,z=.24f+j*.73f;
            Box(dresser,"Drawer front",9.20f,9.235f,z,z+.66f,y,y+.21f,wood);
            BedroomRod(dresser,new Vector3(9.17f,y+.12f,z+.24f),new Vector3(9.17f,y+.12f,z+.42f),.012f,brass);
        }
        Box(dresser,"Dresser mirror frame",9.77f,9.82f,.30f,1.58f,6.40f,7.36f,wood);
        Box(dresser,"Dresser mirror",9.756f,9.769f,.36f,1.52f,6.46f,7.30f,mirror);
        Cyl(dresser,"Red bedside lamp stem",9.49f,1.40f,6.20f,6.57f,.022f,red);
        FixtureShade(dresser,"Kevin red dome shade",new Vector3(9.49f,6.55f,1.40f),red,new[]{new Vector2(.16f,0),new Vector2(.15f,.06f),new Vector2(.10f,.12f),new Vector2(0,.15f)});
        var desk=Child(root,"Desk at front window");
        Box(desk,"Desk top",8.05f,9.26f,-2.20f,-1.62f,5.96f,6.02f,wood);
        Box(desk,"Drawer pedestal",8.08f,8.44f,-2.16f,-1.65f,5.22f,5.96f,wood);
        foreach(float z in new[]{-2.14f,-1.68f})Box(desk,"Desk leg",9.15f,9.20f,z,z+.045f,5.22f,5.96f,wood);
        for(int i=0;i<3;i++)Box(desk,"Desk drawer",8.10f,8.42f,-1.643f,-1.62f,5.35f+i*.19f,5.50f+i*.19f,wood);
        Box(desk,"Chair seat",8.56f,9.03f,-1.26f,-.81f,5.62f,5.68f,wood);
        foreach(float x in new[]{8.59f,8.99f})foreach(float z in new[]{-1.22f,-.85f})Box(desk,"Chair leg",x,x+.035f,z,z+.035f,5.22f,5.63f,wood);
        for(int i=0;i<4;i++){float x=8.59f+i*.13f;Box(desk,"Chair back spindle",x,x+.027f,-.85f,-.82f,5.68f,6.25f,wood);}
        Box(desk,"Chair crest rail",8.56f,9.04f,-.87f,-.80f,6.23f,6.30f,wood);
        foreach(Transform part in desk.transform)if(part.name.StartsWith("Chair"))part.position+=Vector3.back*.35f;
        Cyl(desk,"Banker lamp stem",9.05f,-1.96f,6.02f,6.32f,.022f,brass);
        BedroomSoft(desk,"Green banker shade",new Vector3(9.05f,6.35f,-1.96f),new Vector3(.36f,.15f,.18f),green);
        Box(desk,"Open notebook",8.61f,8.91f,-1.94f,-1.70f,6.022f,6.038f,ivory);
        var shelf=Child(root,"Low bookcase between windows");
        foreach(float x in new[]{7.04f,7.79f})Box(shelf,"Bookcase side",x,x+.035f,-2.22f,-1.91f,5.22f,6.41f,wood);
        Box(shelf,"Bookcase back",7.04f,7.825f,-2.24f,-2.215f,5.22f,6.41f,wood);
        for(int row=0;row<4;row++){
            float y=5.25f+row*.37f;Box(shelf,"Shelf",7.04f,7.825f,-2.22f,-1.90f,y,y+.035f,wood);
            if(row<3)for(int i=0;i<5;i++){float x=7.11f+i*.10f;Box(shelf,"Book",x,x+.065f,-2.17f,-1.93f,y+.035f,y+.22f+(i%2)*.06f,i%3==0?red:i%3==1?blue:green);}
        }
        foreach(float edge in new[]{5.69f,6.70f,7.99f,9.00f})for(int i=0;i<5;i++){
            float x=edge+i*.035f;
            var fold=Cyl(root,"Checked window curtain",x,-2.19f,5.45f,7.69f,.035f,plaid);fold.transform.localScale=new Vector3(.07f,1.12f,.12f);
        }
        foreach(float cx in new[]{6.27f,8.58f})BedroomRod(root,new Vector3(cx-.67f,7.73f,-2.18f),new Vector3(cx+.67f,7.73f,-2.18f),.018f,wood);
        Box(root,"Toy trunk",5.03f,5.60f,.15f,1.18f,5.22f,5.73f,wood);
        foreach(float z in new[]{.30f,1.0f})Box(root,"Trunk brass strap",5.015f,5.61f,z,z+.035f,5.73f,5.745f,brass);
        var chair=Child(root,"Pale upholstered reading chair");
        Box(chair,"Seat cushion",5.38f,6.12f,-1.90f,-1.23f,5.61f,5.78f,ivory);
        BedroomSoft(chair,"Padded back",new Vector3(5.75f,6.13f,-1.86f),new Vector3(.80f,1.0f,.19f),ivory);
        foreach(float x in new[]{5.40f,6.09f}){
            Box(chair,"Wood arm",x-.03f,x+.03f,-1.85f,-1.26f,5.96f,6.03f,wood);
            foreach(float z in new[]{-1.84f,-1.30f})Cyl(chair,"Leg",x,z,5.22f,5.98f,.024f,wood);
        }
        Box(root,"Pinboard frame",7.02f,7.83f,-2.27f,-2.23f,6.63f,7.27f,wood);
        Box(root,"Pinboard cork",7.06f,7.79f,-2.225f,-2.21f,6.67f,7.23f,FoyerFinish("KevinCork",new Color(.49f,.34f,.18f),.05f));
        for(int i=0;i<4;i++){float x=7.10f+(i%2)*.34f,y=6.72f+(i/2)*.27f;Box(root,"Pinned note",x,x+.22f,-2.205f,-2.20f,y,y+.17f,i==1?blue:ivory);}
        ReconcileKevinWindowFurniture();
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static void ReconcileKevinWindowFurniture()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play before moving saved furniture.");
        var root=GameObject.Find("KevinBedroomDetails").transform;
        // Marina Part 2 5:55–6:25: reading chair adjoins the dresser;
        // desk occupies the opposite window, next to the trunk/entry wall.
        // Keep authored furniture sizes; these are relative placements, not measured film coordinates.
        root.Find("Desk at front window").localPosition=new Vector3(-2.75f,0,0);
        root.Find("Pale upholstered reading chair").localPosition=new Vector3(3.3f,0,0);
        EditorSceneManager.MarkSceneDirty(root.gameObject.scene);
    }
    public static string CheckKevinBedroom()
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Enter Play first.");
        var fps=GameObject.Find("Player").GetComponent<FpsController>();var cc=fps.GetComponent<CharacterController>();
        var original=fps.transform.position;bool enabled=fps.enabled;
        var route=new[]{new Vector3(5.94f,5.22f,1.4f),new Vector3(6.4f,5.22f,.2f),new Vector3(6.6f,5.22f,-1.05f),
            new Vector3(5.9f,5.22f,-.75f),new Vector3(6.6f,5.22f,-1.05f),
            new Vector3(7.6f,5.22f,-1.05f),new Vector3(8.75f,5.22f,-.75f),new Vector3(8.75f,5.22f,.70f),
            new Vector3(9.05f,5.22f,-.70f),new Vector3(8.75f,5.22f,.70f),
            new Vector3(8.75f,5.22f,-.75f),new Vector3(7.6f,5.22f,-1.05f),new Vector3(6.6f,5.22f,-1.05f),
            new Vector3(6.4f,5.22f,.2f),new Vector3(5.94f,5.22f,1.4f),new Vector3(5.94f,5.22f,3.7f)};
        try{
            fps.enabled=false;cc.enabled=false;fps.transform.position=new Vector3(5.94f,5.35f,3.7f);cc.enabled=true;Physics.SyncTransforms();
            foreach(var target in route){
                for(int i=0;i<600;i++){var delta=target-fps.transform.position;delta.y=0;if(delta.magnitude<.08f)break;fps.TickMotion(delta,false,false,1f/60);}
                for(int i=0;i<60;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
                if(Vector3.Distance(target,fps.transform.position)>.18f||!cc.isGrounded)throw new InvalidOperationException($"Blocked at {fps.transform.position}, target {target}");
            }
            return "PASS: 16 Kevin room checkpoints, hall entry/return, bed sides, relocated desk, reading chair and bookcase approaches.";
        }finally{cc.enabled=false;fps.transform.position=original;cc.enabled=true;fps.enabled=enabled;}
    }
    static Material KevinPattern(string name,bool check)
    {
        // Reference-inspired repeat, not a reproduction of the original wallpaper/fabric print.
        string path="Assets/Materials/IntactFoyer/"+name+".asset";
        var tex=AssetDatabase.LoadAssetAtPath<Texture2D>(path);if(!tex){tex=new Texture2D(128,128,TextureFormat.RGBA32,true);AssetDatabase.CreateAsset(tex,path);}
        var pixels=new Color[128*128];
        for(int y=0;y<128;y++)for(int x=0;x<128;x++){
            var color=new Color(.92f,.91f,.83f);
            if(check){if(x%32<4||y%32<4)color=new Color(.56f,.62f,.43f);if(x%32<1||y%32<1)color=new Color(.34f,.43f,.25f);}
            else {float dx=x-64,dy=y-64;if(dx*dx+dy*dy<12)color=new Color(.52f,.19f,.20f);if(Mathf.Abs(dx-4)<2&&Mathf.Abs(dy+5)<2)color=new Color(.24f,.37f,.22f);}
            pixels[y*128+x]=color;
        }
        tex.SetPixels(pixels);tex.Apply();tex.wrapMode=TextureWrapMode.Repeat;EditorUtility.SetDirty(tex);
        return FoyerFinish(name,Color.white,.08f,path,check?.48f:.24f);
    }
}
