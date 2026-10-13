using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Furnish Parents Bedroom")]
    public static void FurnishParentsBedroom()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)
            throw new InvalidOperationException("Open IntactHouseReference outside Play.");
        var old=GameObject.Find("ParentsBedroomDetails");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("ParentsBedroomDetails");
        var wood=FoyerFinish("ParentsMahogany",new Color(.25f,.13f,.07f),.35f);
        var red=FoyerFinish("ParentsRedBedding",new Color(.60f,.035f,.045f),.08f);
        var white=FoyerFinish("ParentsIvory",new Color(.94f,.92f,.86f),.28f);
        var stone=FoyerFinish("ParentsHearth",new Color(.045f,.05f,.043f),.2f);
        var black=FoyerFinish("ParentsFirebox",new Color(.009f,.009f,.008f),.05f);
        var green=FoyerFinish("ParentsGreenShade",new Color(.025f,.16f,.08f),.12f);
        var brass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/AntiqueBrass.mat");
        var paper=FoyerFinish("ParentsFloralStripe",Color.white,.1f,"Assets/Textures/kitchen_floral.png",1.15f);
        var model=GameObject.Find("IntactGLB");
        model.GetComponentsInChildren<MeshRenderer>().Single(r=>r.name=="object115").sharedMaterial=paper;
        // Native floor +5.22; bathroom opening is left of the headboard at Z7.29.
        const float floor=5.22f,cx=12.6f;
        var bed=Child(root,"Four-poster bed");
        Box(bed,"Mahogany frame",11.53f,13.67f,4.43f,7.04f,5.48f,5.72f,wood);
        Box(bed,"Ivory mattress",11.58f,13.62f,4.5f,6.98f,5.72f,5.94f,white);
        Box(bed,"Red coverlet",11.55f,13.65f,4.47f,6.98f,5.94f,6.03f,red);
        foreach(float x in new[]{11.55f,13.65f})Box(bed,"Draped red coverlet",x-.035f,x+.035f,4.5f,6.87f,5.61f,5.98f,red);
        foreach(float x in new[]{11.48f,13.72f})foreach(float z in new[]{4.4f,7.08f})
        {
            Cyl(bed,"Tall turned bedpost",x,z,floor,7.85f,.035f,wood);
            Cyl(bed,"Post foot",x,z,floor,5.62f,.05f,wood);
            BedroomSoft(bed,"Post finial",new Vector3(x,7.87f,z),new Vector3(.09f,.13f,.09f),wood);
        }
        foreach(var spec in new[]{(7.03f,6.63f),(4.42f,6.05f)})
        {
            // Curved shoulder silhouette, built as vertical strips rather than a box headboard.
            var v=new System.Collections.Generic.List<Vector3>();var t=new System.Collections.Generic.List<int>();
            for(int i=0;i<=32;i++)
            {
                float u=i/16f-1,top=spec.Item2+.30f*(1-Mathf.Pow(Mathf.Abs(u),6));
                v.Add(new Vector3(cx+u*1.06f,5.65f,spec.Item1));v.Add(new Vector3(cx+u*1.06f,top,spec.Item1));
                if(i<32){int k=i*2;t.AddRange(new[]{k,k+1,k+2,k+1,k+3,k+2});}
            }
            var mesh=new Mesh();mesh.SetVertices(v);mesh.SetTriangles(t,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
            string path="Assets/Materials/IntactFoyer/Parents"+(spec.Item1>6?"Headboard":"Footboard")+".asset";
            var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if(saved){saved.Clear();saved.SetVertices(v);saved.SetTriangles(t,0);saved.RecalculateNormals();saved.RecalculateBounds();EditorUtility.SetDirty(saved);UnityEngine.Object.DestroyImmediate(mesh);mesh=saved;}else AssetDatabase.CreateAsset(mesh,path);
            var board=Child(bed,"Shaped mahogany board");board.AddComponent<MeshFilter>().sharedMesh=mesh;board.AddComponent<MeshRenderer>().sharedMaterial=wood;
        }
        wood.SetFloat("_DoubleSidedEnable",1);UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(wood);EditorUtility.SetDirty(wood);
        foreach(float x in new[]{12.08f,13.12f})BedroomSoft(bed,"Red pillow",new Vector3(x,6.15f,6.66f),new Vector3(.96f,.32f,.51f),red);
        foreach(float x in new[]{10.96f,14.18f})
        {
            var table=Child(root,"Bedside chest");Box(table,"Chest",x-.3f,x+.3f,6.5f,7.04f,floor,5.85f,wood);
            for(int i=0;i<2;i++){float y=5.38f+i*.24f;Box(table,"Drawer",x-.27f,x+.27f,6.47f,6.49f,y,y+.19f,wood);Cyl(table,"Brass knob",x,6.44f,y+.08f,y+.12f,.025f,brass);}
            Cyl(table,"Lamp stem",x,6.76f,5.85f,6.22f,.025f,brass);
            FixtureShade(table,"Parents green lampshade",new Vector3(x,6.1f,6.76f),green,new[]{new Vector2(.20f,0),new Vector2(.14f,.27f)});
        }
        // White mantel on adjoining wall; a dark recess built forward of the intact wall.
        var hearth=Child(root,"White fireplace and hearth");
        Box(hearth,"Dark stone hearth",8.37f,9.15f,5.08f,6.96f,floor,floor+.045f,stone);
        Box(hearth,"Firebox back",8.39f,8.42f,5.40f,6.64f,floor+.04f,6.25f,black);
        foreach(float z in new[]{5.27f,6.65f})Box(hearth,"Stone jamb",8.42f,8.70f,z,z+.13f,floor+.04f,6.37f,stone);
        Box(hearth,"Stone lintel",8.42f,8.70f,5.27f,6.78f,6.25f,6.4f,stone);
        foreach(float z in new[]{5.09f,6.81f})
        {
            Box(hearth,"Ivory pilaster",8.4f,8.78f,z,z+.16f,floor,6.65f,white);
            Box(hearth,"Pilaster capital",8.39f,8.84f,z-.03f,z+.19f,6.32f,6.43f,white);
        }
        Box(hearth,"Paneled frieze",8.4f,8.76f,5.09f,6.97f,6.4f,6.68f,white);
        Box(hearth,"Mantel shelf",8.36f,8.91f,5.01f,7.05f,6.68f,6.77f,white);
        foreach(float z in new[]{5.5f,5.95f,6.4f})
        {
            Cyl(hearth,"Screen upright",8.84f,z,5.27f,5.92f,.009f,brass);
            for(int i=0;i<12;i++)
            {
                float a=i*Mathf.PI/12,b=(i+1)*Mathf.PI/12;
                BedroomRod(hearth,new Vector3(8.84f,5.92f+.20f*Mathf.Sin(a),z+.2f*Mathf.Cos(a)),new Vector3(8.84f,5.92f+.20f*Mathf.Sin(b),z+.2f*Mathf.Cos(b)),.009f,brass);
            }
        }
        for(int i=0;i<3;i++){var log=Cyl(hearth,"Unlit log",8.6f,5.65f+i*.25f,5.12f,5.56f,.065f,wood);log.transform.rotation=Quaternion.Euler(90,0,0);}
        // Seat the firebox in the existing recess (Z5.1–6.45, back X8.34).
        // Surround overlaps its edges at the bedroom wall face X8.91.
        hearth.transform.position+=new Vector3(.2f,0,-.3f);
        // Dressing area and armoire, kept clear of both the entrance and ensuite path.
        var desk=Child(root,"Window dressing table");
        Box(desk,"Desk top",14.12f,14.69f,1.75f,3.15f,5.95f,6.02f,wood);
        foreach(float x in new[]{14.17f,14.63f})foreach(float z in new[]{1.82f,3.08f})Cyl(desk,"Desk leg",x,z,floor,5.95f,.025f,wood);
        Box(desk,"Green stool",13.62f,14.04f,2.16f,2.68f,5.59f,5.69f,green);
        foreach(float x in new[]{13.67f,13.99f})foreach(float z in new[]{2.21f,2.63f})Cyl(desk,"Stool leg",x,z,floor,5.59f,.023f,wood);
        var mirror=FoyerFinish("ParentsMirror",new Color(.65f,.69f,.66f),.98f);
        mirror.SetFloat("_Metallic",1);EditorUtility.SetDirty(mirror);
        BedroomSoft(desk,"Oval mahogany mirror frame",new Vector3(14.58f,6.53f,2.45f),new Vector3(.11f,1.02f,.70f),wood);
        BedroomSoft(desk,"Oval mirror",new Vector3(14.515f,6.53f,2.45f),new Vector3(.025f,.90f,.58f),mirror);
        var chair=Child(root,"Green upholstered chair");
        Box(chair,"Upholstered seat",13.25f,14.05f,.45f,1.2f,5.61f,5.76f,green);
        BedroomSoft(chair,"Rounded upholstered back",new Vector3(13.65f,6.06f,.52f),new Vector3(.85f,.95f,.22f),green);
        foreach(float x in new[]{13.28f,14.02f}){
            Box(chair,"Wood arm",x-.045f,x+.045f,.54f,1.15f,5.96f,6.03f,wood);
            foreach(float z in new[]{.55f,1.1f})Cyl(chair,"Chair leg",x,z,floor,5.96f,.026f,wood);
        }
        // Gathered panels frame the existing window bank; retain daylight through its centre.
        var curtains=Child(root,"Ivory window curtains");
        for(int panel=0;panel<2;panel++)for(int fold=0;fold<9;fold++)
        {
            float z=(panel==0?.65f:4.05f)+fold*.05f;
            BedroomSoft(curtains,"Gathered fabric fold",new Vector3(14.64f,6.67f,z),new Vector3(.12f,2.8f,.075f),white);
        }
        Box(curtains,"Curtain pelmet",14.59f,14.73f,.59f,4.51f,7.91f,8.07f,white);
        var wardrobe=Child(root,"Tall mahogany armoire");Box(wardrobe,"Cabinet",10.3f,11.55f,-.64f,.04f,floor,7.43f,wood);
        Box(wardrobe,"Cornice",10.24f,11.61f,-.68f,.08f,7.43f,7.54f,wood);
        foreach(float x in new[]{10.34f,10.95f})Box(wardrobe,"Raised panel door",x,x+.55f,.045f,.075f,5.35f,7.33f,wood);
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static string CheckParentsBedroom()
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Enter Play first.");
        var fps=GameObject.Find("Player").GetComponent<FpsController>();var cc=fps.GetComponent<CharacterController>();
        var original=fps.transform.position;bool enabled=fps.enabled;
        var route=new[]{new Vector3(10.3f,5.22f,4),new Vector3(14.2f,5.22f,4),new Vector3(14.2f,5.22f,6),
            new Vector3(14.2f,5.22f,4),new Vector3(10.3f,5.22f,4),new Vector3(10.3f,5.22f,6),
            new Vector3(10,5.22f,8),new Vector3(10.3f,5.22f,6),new Vector3(10.3f,5.22f,4),new Vector3(8.5f,5.22f,4)};
        try
        {
            fps.enabled=false;cc.enabled=false;fps.transform.position=new Vector3(8.5f,5.35f,4);cc.enabled=true;Physics.SyncTransforms();
            foreach(var target in route)
            {
                for(int i=0;i<600;i++){var delta=target-fps.transform.position;delta.y=0;if(delta.magnitude<.08f)break;fps.TickMotion(delta,false,false,1f/60);}
                for(int i=0;i<60;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
                if(Vector3.Distance(target,fps.transform.position)>.18f||!cc.isGrounded)
                    throw new InvalidOperationException($"Blocked at {fps.transform.position}, target {target}");
            }
            return "PASS: 10 walking checkpoints, both bed sides, bathroom and bedroom entrance.";
        }
        finally{cc.enabled=false;fps.transform.position=original;cc.enabled=true;fps.enabled=enabled;}
    }
    static void BedroomSoft(GameObject root,string name,Vector3 position,Vector3 scale,Material material)
    {
        var go=GameObject.CreatePrimitive(PrimitiveType.Sphere);go.name=name;go.transform.parent=root.transform;go.transform.position=position;go.transform.localScale=scale;
        go.GetComponent<Renderer>().sharedMaterial=material;UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
    }
    static void BedroomRod(GameObject root,Vector3 a,Vector3 b,float radius,Material material)
    {
        var go=Cyl(root,"Curved brass screen",0,0,0,(b-a).magnitude,radius,material);
        go.transform.position=(a+b)/2;go.transform.rotation=Quaternion.FromToRotation(Vector3.up,(b-a).normalized);
    }
}
