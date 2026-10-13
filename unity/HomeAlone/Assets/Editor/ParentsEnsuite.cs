using System;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Furnish Parents Ensuite")]
    public static void FurnishParentsEnsuite()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)
            throw new InvalidOperationException("Open IntactHouseReference outside Play.");
        var old=GameObject.Find("ParentsEnsuiteDetails");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("ParentsEnsuiteDetails");
        var ivory=FoyerFinish("EnsuiteIvory",new Color(.92f,.88f,.79f),.35f);
        var porcelain=FoyerFinish("EnsuitePorcelain",new Color(.96f,.96f,.91f),.75f);
        var pink=FoyerFinish("EnsuiteBlush",new Color(.83f,.73f,.69f),.12f);
        var stone=FoyerFinish("EnsuiteGreenStone",new Color(.025f,.065f,.042f),.7f);
        var towel=FoyerFinish("EnsuiteGreenTowel",new Color(.14f,.30f,.16f),.05f);
        var dark=FoyerFinish("EnsuiteDarkTowel",new Color(.015f,.09f,.035f),.05f);
        var brass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/AntiqueBrass.mat");
        var mirror=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/ParentsMirror.mat");
        EnsuiteFinish(117,pink,p=>p.z>7.30f);
        EnsuiteFinish(139,stone,p=>p.x>8.34f&&p.x<12.15f&&p.z>7.30f&&p.z<10.78f&&p.y>5&&p.y<5.3f);
        EnsuiteFinish(230,ivory,p=>p.x>8.3f&&p.x<9.35f&&p.z>7.30f&&p.z<9.70f&&p.y>5.2f&&p.y<6.3f,true);
        var vanity=Child(root,"Green stone vanity");
        Box(vanity,"Cabinet body",8.35f,8.92f,7.56f,9.64f,5.25f,5.85f,ivory);
        Box(vanity,"Cabinet face",8.92f,8.97f,7.60f,9.60f,5.30f,6.10f,ivory);
        for(int i=0;i<4;i++){
            float z=7.64f+i*.49f;
            Box(vanity,"Raised cabinet panel",8.97f,8.985f,z,z+.44f,5.39f,6.02f,ivory);
            BedroomRod(vanity,new Vector3(9.01f,5.94f,z+.15f),new Vector3(9.01f,5.94f,z+.29f),.012f,brass);
        }
        // Counter mesh surrounds a real oval opening; basin closes below it.
        var v=new List<Vector3>();var tr=new List<int>();
        for(int i=0;i<64;i++){
            float a=i*Mathf.PI/32,c=Mathf.Cos(a),s=Mathf.Sin(a),m=Mathf.Max(Mathf.Abs(c),Mathf.Abs(s));
            v.Add(new Vector3(8.67f+c/m*.31f,6.13f,8.60f+s/m*1.04f));
            v.Add(new Vector3(8.67f+c*.25f,6.13f,8.60f+s*.375f));
            int k=i*2,n=((i+1)%64)*2;tr.AddRange(new[]{k,n,k+1,n,n+1,k+1});
        }
        var mesh=new Mesh();mesh.SetVertices(v);mesh.SetTriangles(tr,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
        string path="Assets/Materials/IntactFoyer/EnsuiteCounter.asset";
        var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(saved){saved.Clear();saved.vertices=mesh.vertices;saved.triangles=mesh.triangles;saved.RecalculateNormals();saved.RecalculateBounds();EditorUtility.SetDirty(saved);UnityEngine.Object.DestroyImmediate(mesh);mesh=saved;}else AssetDatabase.CreateAsset(mesh,path);
        var top=Child(vanity,"Counter with oval sink opening");top.AddComponent<MeshFilter>().sharedMesh=mesh;top.AddComponent<MeshRenderer>().sharedMaterial=stone;
        stone.SetFloat("_DoubleSidedEnable",1);UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(stone);EditorUtility.SetDirty(stone);
        FixtureShade(vanity,"Ensuite inset basin",new Vector3(8.67f,5.88f,8.60f),porcelain,new[]{new Vector2(0,0),new Vector2(.10f,.015f),new Vector2(.20f,.15f),new Vector2(.25f,.257f),new Vector2(.27f,.257f)});
        vanity.transform.Find("Ensuite inset basin").localScale=new Vector3(1,1,1.5f);
        Box(vanity,"Stone backsplash",8.355f,8.39f,7.56f,9.64f,6.13f,6.26f,stone);
        Cyl(vanity,"Brass tap",8.43f,8.60f,6.13f,6.33f,.023f,brass);
        BedroomRod(vanity,new Vector3(8.43f,6.33f,8.60f),new Vector3(8.64f,6.33f,8.60f),.023f,brass);
        foreach(float z in new[]{8.43f,8.77f})Cyl(vanity,"Tap handle",8.43f,z,6.13f,6.23f,.028f,brass);
        Box(vanity,"Large brass mirror frame",8.36f,8.43f,7.75f,9.46f,6.37f,7.77f,brass);
        Box(vanity,"Mirror surface",8.432f,8.44f,7.81f,9.40f,6.43f,7.71f,mirror);
        foreach(float z in new[]{7.45f,9.83f})for(int i=0;i<3;i++){
            float y=6.33f+i*.39f;
            Box(vanity,"Open corner shelf",8.37f,8.73f,z-.16f,z+.16f,y,y+.035f,ivory);
            Box(vanity,"Folded green towel",8.4f,8.68f,z-.13f,z+.13f,y+.04f,y+.12f,towel);
        }
        BuildEnsuiteBathShower(root,porcelain,stone,brass);
        // Layered towels match the film's green-on-green rail arrangement.
        foreach(float z in new[]{8.65f,9.23f}){
            BedroomRod(root,new Vector3(12.01f,6.68f,z-.24f),new Vector3(12.01f,6.68f,z+.24f),.014f,brass);
            Box(root,"Sage bath towel",11.98f,12.01f,z-.21f,z+.21f,6.10f,6.67f,towel);
            Box(root,"Forest green hand towel",11.95f,11.977f,z-.10f,z+.10f,6.13f,6.68f,dark);
        }
        for(int i=0;i<5;i++){
            float z=7.76f+i*.12f;
            Cyl(vanity,"Toiletry bottle",8.65f,z,6.14f,6.28f+(i%2)*.07f,.032f,i%2==0?dark:ivory);
            Cyl(vanity,"Bottle cap",8.65f,z,6.28f+(i%2)*.07f,6.31f+(i%2)*.07f,.024f,brass);
        }
        var opal=FoyerFinish("EnsuiteOpal",new Color(.98f,.94f,.82f),.25f);
        opal.SetColor("_EmissiveColor",new Color(1,.9f,.72f)*2);UnityEngine.Rendering.HighDefinition.HDMaterial.ValidateMaterial(opal);EditorUtility.SetDirty(opal);
        Box(root,"Vanity light brass backplate",8.37f,8.43f,8.24f,8.96f,7.91f,8.08f,brass);
        Box(root,"Vanity opal light",8.435f,8.52f,8.30f,8.90f,7.94f,8.045f,opal);
        FoyerLamp(root,"Warm vanity illumination",new Vector3(8.8f,7.85f,8.6f),180,4);
        var drapes=Child(root,"Ivory bathroom window dressing");
        foreach(float edge in new[]{9.32f,10.56f})for(int i=0;i<5;i++)
            BedroomSoft(drapes,"Gathered curtain fold",new Vector3(edge+i*.037f,6.72f,10.66f),new Vector3(.065f,1.95f,.10f),ivory);
        Box(drapes,"Window valance",9.29f,10.76f,10.61f,10.72f,7.61f,7.76f,ivory);
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    // Outline follows Marina 3:35; envelope remains a provisional fit, not a film measurement.
    static void BuildEnsuiteBathShower(GameObject root,Material porcelain,Material stone,Material brass)
    {
        var bath=Child(root,"Integrated curved bath and shower");
        var outline=new List<Vector2>();
        for(int i=0;i<=32;i++){
            float a=-Mathf.PI/2+i*Mathf.PI/32;
            outline.Add(new Vector2(11.52f-.62f*Mathf.Cos(a),8.89f+.62f*Mathf.Sin(a)));
        }
        outline.Add(new Vector2(12.08f,9.51f));outline.Add(new Vector2(12.08f,8.27f));
        var vertices=new List<Vector3>();var triangles=new List<int>();int n=outline.Count;
        // Outer apron, rim, sloped basin and closed basin floor, with a straight wall-backed edge.
        foreach(var ring in new[]{new Vector2(1,5.22f),new Vector2(1,5.83f),new Vector2(.79f,5.83f),new Vector2(.67f,5.38f)})
            foreach(var p in outline){var q=Vector2.LerpUnclamped(new Vector2(11.55f,8.89f),p,ring.x);vertices.Add(new Vector3(q.x,ring.y,q.y));}
        for(int ring=0;ring<3;ring++)for(int i=0;i<n;i++){
            int a=ring*n+i,b=ring*n+(i+1)%n,c=a+n,d=b+n;
            triangles.AddRange(new[]{a,b,c,b,d,c});
        }
        int centre=vertices.Count;vertices.Add(new Vector3(11.55f,5.38f,8.89f));
        for(int i=0;i<n;i++)triangles.AddRange(new[]{centre,3*n+i,3*n+(i+1)%n});
        var shell=Child(bath,"Curved apron rim and basin");
        var mesh=NeighborhoodMesh("EnsuiteIntegratedBath",vertices.ToArray(),triangles.ToArray());
        shell.AddComponent<MeshFilter>().sharedMesh=mesh;shell.AddComponent<MeshRenderer>().sharedMaterial=porcelain;
        shell.AddComponent<MeshCollider>().sharedMesh=mesh;
        Box(bath,"Back stone upstand",12.08f,12.12f,8.27f,9.55f,5.24f,5.94f,stone);
        Box(bath,"End stone upstand",11.52f,12.08f,9.51f,9.55f,5.24f,5.94f,stone);
        Cyl(bath,"Bath brass spout",11.88f,9.15f,5.83f,6.04f,.024f,brass);
        BedroomRod(bath,new Vector3(11.88f,6.04f,9.15f),new Vector3(11.66f,6.04f,9.15f),.025f,brass);
        foreach(float z in new[]{9f,9.3f})Cyl(bath,"Bath tap handle",11.88f,z,5.83f,5.96f,.028f,brass);
        Box(bath,"Shower tray",10.97f,12.08f,7.39f,8.23f,5.22f,5.265f,porcelain);
        // Shared screen sits on a solid bath-height divider, rather than descending through the bath.
        Box(bath,"Shared bath shower divider",11.52f,12.08f,8.23f,8.27f,5.22f,5.83f,porcelain);
        var glass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/FixtureClearGlass.mat");
        var pane=GameObject.CreatePrimitive(PrimitiveType.Quad);pane.name="Shared glass screen";pane.transform.parent=bath.transform;
        pane.transform.position=new Vector3(11.80f,6.595f,8.25f);pane.transform.localScale=new Vector3(.51f,1.49f,1);
        pane.GetComponent<Renderer>().sharedMaterial=glass;pane.GetComponent<Renderer>().shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;
        foreach(float x in new[]{11.52f,12.08f})Box(bath,"Screen upright",x-.0125f,x+.0125f,8.23f,8.27f,5.83f,7.39f,brass);
        foreach(float y in new[]{5.83f,7.365f})Box(bath,"Screen rail",11.5325f,12.0675f,8.23f,8.27f,y,y+.025f,brass);
        Cyl(bath,"Shower riser",12.05f,7.78f,6.2f,7.27f,.018f,brass);
        BedroomRod(bath,new Vector3(12.05f,7.27f,7.78f),new Vector3(11.78f,7.27f,7.78f),.018f,brass);
        BedroomSoft(bath,"Shower rose",new Vector3(11.78f,7.24f,7.78f),new Vector3(.18f,.035f,.18f),brass);
        BedroomSoft(bath,"Mixer control",new Vector3(12.035f,6.35f,7.78f),new Vector3(.06f,.12f,.12f),brass);
    }
    public static void ReconcileEnsuiteBathShower()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var root=GameObject.Find("ParentsEnsuiteDetails");if(!root)throw new InvalidOperationException("Furnish ensuite first.");
        foreach(string name in new[]{"Rounded bath - provisional fit","Brass framed shower - open entrance","Integrated curved bath and shower"}){
            var old=root.transform.Find(name);if(old)UnityEngine.Object.DestroyImmediate(old.gameObject);
        }
        BuildEnsuiteBathShower(root,AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/EnsuitePorcelain.mat"),
            AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/EnsuiteGreenStone.mat"),AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/AntiqueBrass.mat"));
    }
    public static string CheckParentsEnsuite()
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Enter Play first.");
        var bath=GameObject.Find("ParentsEnsuiteDetails/Integrated curved bath and shower");
        if(!bath)throw new InvalidOperationException("Missing integrated bath.");
        var shell=bath.transform.Find("Curved apron rim and basin").GetComponent<MeshCollider>();
        foreach(var sample in new[]{new Vector3(10.94f,7,8.89f),new Vector3(11.55f,7,8.89f)}){
            if(!shell.Raycast(new Ray(sample,Vector3.down),out var hit,3)||hit.normal.y<.9f||Mathf.Abs(hit.point.y-(sample.x<11?5.83f:5.38f))>.01f)
                throw new InvalidOperationException("Bath rim/basin collision or face winding is incorrect.");
        }
        var fps=GameObject.Find("Player").GetComponent<FpsController>();var cc=fps.GetComponent<CharacterController>();
        var original=fps.transform.position;bool enabled=fps.enabled;
        var route=new[]{new Vector3(10,5.22f,8.3f),new Vector3(10,5.22f,9.8f),new Vector3(9.5f,5.22f,9.8f),
            new Vector3(10,5.22f,9.8f),new Vector3(10.4f,5.22f,8.7f),new Vector3(10.4f,5.22f,7.8f),
            new Vector3(11.4f,5.265f,7.8f),new Vector3(10.4f,5.22f,7.8f),new Vector3(10.3f,5.22f,6)};
        try{
            fps.enabled=false;cc.enabled=false;fps.transform.position=new Vector3(10.3f,5.35f,6);cc.enabled=true;Physics.SyncTransforms();
            foreach(var target in route){
                for(int i=0;i<600;i++){var delta=target-fps.transform.position;delta.y=0;if(delta.magnitude<.08f)break;fps.TickMotion(delta,false,false,1f/60);}
                for(int i=0;i<60;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
                if(Vector3.Distance(target,fps.transform.position)>.18f||!cc.isGrounded)throw new InvalidOperationException($"Blocked at {fps.transform.position}, target {target}");
            }
            return "PASS: 9 ensuite checkpoints, vanity aisle, window, bath approach, shower entry/exit, bedroom return.";
        }finally{cc.enabled=false;fps.transform.position=original;cc.enabled=true;fps.enabled=enabled;}
    }
    static void EnsuiteFinish(int id,Material finish,Func<Vector3,bool> contains,bool hide=false)
    {
        var node=GameObject.Find("IntactGLB").GetComponentsInChildren<MeshFilter>().Single(m=>m.name=="object"+id);
        var source=node.GetComponent<MeshCollider>().sharedMesh;var vertices=source.vertices;var indices=source.triangles;
        var inside=new List<int>();var outside=new List<int>();
        for(int i=0;i<indices.Length;i+=3){var p=node.transform.TransformPoint((vertices[indices[i]]+vertices[indices[i+1]]+vertices[indices[i+2]])/3);(contains(p)?inside:outside).AddRange(new[]{indices[i],indices[i+1],indices[i+2]});}
        if(inside.Count==0)throw new InvalidOperationException("No ensuite faces on "+id);
        string path="Assets/Materials/IntactFoyer/object"+id+"_Ensuite.asset";
        var mesh=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(!mesh){mesh=UnityEngine.Object.Instantiate(source);AssetDatabase.CreateAsset(mesh,path);}
        mesh.Clear();mesh.vertices=vertices;mesh.normals=source.normals;mesh.uv=source.uv;mesh.tangents=source.tangents;mesh.subMeshCount=2;mesh.SetTriangles(outside,0);mesh.SetTriangles(hide?new List<int>():inside,1);mesh.RecalculateBounds();EditorUtility.SetDirty(mesh);
        var r=node.GetComponent<MeshRenderer>();var original=r.sharedMaterials[0];node.sharedMesh=mesh;r.sharedMaterials=new[]{original,finish};
    }
}
