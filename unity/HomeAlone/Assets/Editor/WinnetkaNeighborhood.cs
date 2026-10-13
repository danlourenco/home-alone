using System;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Build Winter Neighborhood")]
    public static void BuildWinterNeighborhood()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open IntactHouseReference outside Play.");
        var old=GameObject.Find("WinterNeighborhood");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("WinterNeighborhood");
        // Only the detached outer snow banks are suppressed; original house/site meshes stay intact.
        var model=GameObject.Find("IntactGLB");
        for(int id=2946;id<=2955;id++){
            var r=model.GetComponentsInChildren<Renderer>().Single(o=>o.name=="object"+id);
            r.enabled=false;r.GetComponent<MeshCollider>().enabled=false;
        }
        var snow=FoyerFinish("NeighborhoodSnow",new Color(.82f,.86f,.88f),.12f);
        var road=FoyerFinish("NeighborhoodAsphalt",new Color(.12f,.13f,.14f),.12f);
        var concrete=FoyerFinish("NeighborhoodConcrete",new Color(.45f,.46f,.44f),.16f);
        var bark=FoyerFinish("NeighborhoodBark",new Color(.15f,.11f,.085f),.10f);
        var green=FoyerFinish("NeighborhoodEvergreen",new Color(.035f,.10f,.06f),.1f);
        var brick=FoyerFinish("NeighborhoodBrick",new Color(.32f,.18f,.13f),.15f);
        var siding=FoyerFinish("NeighborhoodSiding",new Color(.61f,.56f,.45f),.12f);
        var cream=FoyerFinish("NeighborhoodTrim",new Color(.82f,.79f,.68f),.25f);
        var dark=FoyerFinish("NeighborhoodSlate",new Color(.11f,.13f,.14f),.18f);
        var glass=FoyerFinish("NeighborhoodWindow",new Color(.10f,.17f,.21f),.7f);
        // Ground strips exclude the original parcel and basement; north grade follows existing site elevation.
        NeighborhoodGround(root,"West snowy lots",-180,-35,-180,180,snow);
        NeighborhoodGround(root,"East snowy lots",23,180,-180,180,snow);
        NeighborhoodGround(root,"Across street snowy lots",-35,23,-180,-33,snow);
        NeighborhoodGround(root,"Rear snowy lots",-35,23,42,180,snow);
        Box(root,"Lincoln Avenue",-170,170,-31,-23,-.53f,-.39f,road);
        foreach(float z in new[]{-22.7f,-33.5f})Box(root,"Public sidewalk",-170,170,z,z+1.5f,-.43f,-.27f,concrete);
        foreach(float z in new[]{-23.1f,-31.15f})Box(root,"Street curb",-170,170,z,z+.15f,-.45f,-.23f,concrete);
        Box(root,"Front walk connection",.95f,2.85f,-21.2f,-16.7f,-.43f,-.26f,concrete);
        foreach(float x in new[]{-18f,17.6f})Box(root,"Driveway street apron",x-2.1f,x+2.1f,-23.0f,-16.0f,-.43f,-.25f,road);
        // Sidewalk expansion joints stay below walking significance.
        for(int i=-55;i<=55;i++)foreach(float z in new[]{-22.7f,-33.5f})Box(root,"Sidewalk joint",i*3f,i*3f+.018f,z,z+1.5f,-.271f,-.265f,road);
        var homes=new[]{new Vector3(-43,0,2),new Vector3(34,0,4),new Vector3(-72,0,0),new Vector3(65,0,5),new Vector3(-103,0,3),new Vector3(100,0,0),
            new Vector3(-80,0,-51),new Vector3(-47,0,-53),new Vector3(-15,0,-51),new Vector3(19,0,-52),new Vector3(52,0,-54),new Vector3(85,0,-51),
            new Vector3(-32,0,58),new Vector3(2,0,62),new Vector3(34,0,58)};
        for(int i=0;i<homes.Length;i++){
            var p=homes[i];p.y=NeighborhoodGrade(p.z);
            NeighborhoodHouse(root,i,p,p.z< -35?180:0,i%3==0?brick:siding,cream,dark,glass,snow);
            float approach=p.z< -35?-34:-21;
            if(p.z<20)Box(root,"Neighbor front path",p.x-.7f,p.x+.7f,Mathf.Min(p.z,approach),Mathf.Max(p.z,approach),-.43f,-.26f,concrete);
        }
        for(int i=0;i<28;i++){
            float x=-135+i*10.2f,z=i%2==0?-19.6f:-35.5f;
            // Leave original drive exits and central front walk free.
            if(Mathf.Abs(x-1.9f)<3||Mathf.Abs(x+18)<3||Mathf.Abs(x-17.6f)<3)continue;
            NeighborhoodTree(root,i,new Vector3(x,NeighborhoodGrade(z),z),.8f+(i%4)*.13f,bark);
        }
        for(int i=0;i<22;i++){
            float x=-126+i*12,z=i%2==0?28:75;
            if(x> -24&&x<25&&z<40)continue;
            NeighborhoodTree(root,i+31,new Vector3(x,NeighborhoodGrade(z),z),1.05f+(i%3)*.16f,bark);
        }
        NeighborhoodTree(root,90,new Vector3(-13,-.43f,-12),1.18f,bark);
        NeighborhoodTree(root,91,new Vector3(15,-.43f,-11),1.05f,bark);
        foreach(var p in homes)for(int j=0;j<4;j++){
            float z=p.z+(p.z< -35?6:-6),x=p.x-4+j*2.6f;
            BedroomSoft(root,"Snow edged evergreen shrub",new Vector3(x,NeighborhoodGrade(z)+.6f,z),new Vector3(2.2f,1.2f,1.6f),green);
            BedroomSoft(root,"Thin snow on hedge",new Vector3(x,NeighborhoodGrade(z)+1.12f,z),new Vector3(2.05f,.16f,1.45f),snow);
        }
        // Wooden poles and sagging service wires are visible in the public-street references.
        for(int i=-4;i<=4;i++){
            float x=i*32f+8;
            Cyl(root,"Utility pole",x,-20.2f,-.43f,8.4f,.11f,bark);
            Box(root,"Pole crossarm",x-.08f,x+.08f,-21.2f,-19.2f,8.10f,8.22f,bark);
            if(i<4)for(int wire=0;wire<2;wire++)for(int k=0;k<12;k++){
                float a=k/12f,b=(k+1)/12f,z=-20.9f+wire*1.3f;
                NeighborhoodRod(root,"Overhead wire",new Vector3(x+a*32,8.12f-Mathf.Sin(a*Mathf.PI)*.6f,z),new Vector3(x+b*32,8.12f-Mathf.Sin(b*Mathf.PI)*.6f,z),.012f,dark);
            }
        }
        // Real-photo shutter placement, fitted to the existing main front windows only.
        var shutters=Child(root,"Front facade shutters");
        var shutter=FoyerFinish("FrontShutterGreenBlack",new Color(.025f,.04f,.035f),.22f);
        foreach(float y in new[]{2.87f,6.64f})foreach(float x in new[]{-4.77f,-2.49f,6.25f,8.53f})NeighborhoodShutterPair(shutters,x,y,y<4?2.34f:1.62f,y<4?1.14f:.94f,shutter);
        NeighborhoodShutterPair(shutters,1.88f,6.64f,1.62f,1.0f,shutter);
        BuildNeighborhoodBoundary();
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static void BuildNeighborhoodBoundary()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var neighborhood=GameObject.Find("WinterNeighborhood");if(!neighborhood)throw new InvalidOperationException("Build neighborhood first.");
        var old=GameObject.Find("Neighborhood playable boundary");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Neighborhood playable boundary");
        foreach(var s in new[]{(new Vector3(-30,3,4),new Vector3(.5f,30,76)),(new Vector3(23,3,4),new Vector3(.5f,30,76)),
            (new Vector3(-3.5f,3,-34),new Vector3(53.5f,30,.5f)),(new Vector3(-3.5f,3,42),new Vector3(53.5f,30,.5f))}){
            var barrier=Child(root,"Scenery boundary");barrier.transform.position=s.Item1;barrier.AddComponent<BoxCollider>().size=s.Item2;
        }
        // Neighbor houses are set dressing: no interiors, gameplay or physics simulation.
        foreach(Transform house in neighborhood.transform)if(house.name.StartsWith("Neighbor house ")){
            foreach(var c in house.GetComponentsInChildren<Collider>())c.enabled=false;
            foreach(var r in house.GetComponentsInChildren<Renderer>())GameObjectUtility.SetStaticEditorFlags(r.gameObject,StaticEditorFlags.BatchingStatic);
        }
        var hedge=FoyerFinish("BoundaryHedge",new Color(.035f,.075f,.045f),.1f);
        for(int i=0;i<24;i++)foreach(float x in new[]{-30f,23f}){
            float z=-17+i*2.5f;BedroomSoft(root,"Property edge evergreen",new Vector3(x,NeighborhoodGrade(z)+.6f,z),new Vector3(1.3f,1.3f,2.8f),hedge);
        }
        for(int i=0;i<22;i++)BedroomSoft(root,"Rear property evergreen",new Vector3(-30+i*2.5f,1.42f,42),new Vector3(2.8f,1.3f,1.3f),hedge);
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static string CheckNeighborhoodBoundary()
    {
        var root=GameObject.Find("Neighborhood playable boundary");if(!root||root.GetComponentsInChildren<BoxCollider>().Length!=4)throw new InvalidOperationException("Boundary incomplete.");
        Physics.SyncTransforms();
        foreach(var s in new[]{(new Vector3(-28,2,4),Vector3.left),(new Vector3(21,2,4),Vector3.right),
            (new Vector3(0,2,-32),Vector3.back),(new Vector3(0,2,40),Vector3.forward)})
            if(!Physics.Raycast(s.Item1,s.Item2,out var hit,3)||!hit.collider.transform.IsChildOf(root.transform))throw new InvalidOperationException("Scenery boundary gap.");
        var houses=GameObject.Find("WinterNeighborhood").transform.Cast<Transform>().Where(t=>t.name.StartsWith("Neighbor house ")).ToArray();
        if(houses.Length!=15||houses.Any(h=>h.GetComponentsInChildren<Collider>().Any(c=>c.enabled)))throw new InvalidOperationException("Neighbor scenery has active house colliders.");
        return "PASS four closed scenery boundaries; 15 background houses without active colliders";
    }
    public static string CheckWinterNeighborhood()
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Enter Play first.");
        var fps=GameObject.Find("Player").GetComponent<FpsController>();var cc=fps.GetComponent<CharacterController>();
        var original=fps.transform.position;bool enabled=fps.enabled;
        var route=new[]{new Vector3(-20,-.39f,-27),new Vector3(20,-.39f,-27),new Vector3(2,-.39f,-27),
            new Vector3(2,-.27f,-21.8f),new Vector3(-10,-.27f,-21.8f),new Vector3(10,-.27f,-21.8f),new Vector3(2,-.27f,-21.8f),new Vector3(2,-.26f,-18f)};
        try{
            fps.enabled=false;cc.enabled=false;fps.transform.position=new Vector3(2,-.2f,-27);cc.enabled=true;Physics.SyncTransforms();
            foreach(var target in route){
                for(int i=0;i<1200;i++){var delta=target-fps.transform.position;delta.y=0;if(delta.magnitude<.08f)break;fps.TickMotion(delta,false,false,1f/60);}
                for(int i=0;i<60;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
                if(Vector3.Distance(target,fps.transform.position)>.20f||!cc.isGrounded)throw new InvalidOperationException($"Blocked at {fps.transform.position}, target {target}");
            }
            return "PASS: eight street, sidewalk and front-walk controller checkpoints.";
        }finally{cc.enabled=false;fps.transform.position=original;cc.enabled=true;fps.enabled=enabled;}
    }
    static float NeighborhoodGrade(float z){return Mathf.Lerp(-.43f,.82f,Mathf.Clamp01(z/28));}
    static void NeighborhoodGround(GameObject root,string name,float x0,float x1,float z0,float z1,Material material)
    {
        var v=new List<Vector3>();var t=new List<int>();
        for(int i=0;i<=24;i++){
            float z=Mathf.Lerp(z0,z1,i/24f);v.Add(new Vector3(x0,NeighborhoodGrade(z),z));v.Add(new Vector3(x1,NeighborhoodGrade(z),z));
            if(i<24){int k=i*2;t.AddRange(new[]{k,k+2,k+1,k+1,k+2,k+3});}
        }
        var mesh=NeighborhoodMesh(name,v.ToArray(),t.ToArray());var go=Child(root,name);go.AddComponent<MeshFilter>().sharedMesh=mesh;go.AddComponent<MeshRenderer>().sharedMaterial=material;go.AddComponent<MeshCollider>().sharedMesh=mesh;
    }
    static Mesh NeighborhoodMesh(string name,Vector3[] v,int[] t)
    {
        string path="Assets/Materials/IntactFoyer/Neighborhood"+name.Replace(" ","")+".asset";
        var mesh=AssetDatabase.LoadAssetAtPath<Mesh>(path);if(!mesh){mesh=new Mesh();AssetDatabase.CreateAsset(mesh,path);}mesh.Clear();mesh.vertices=v;mesh.triangles=t;mesh.RecalculateNormals();mesh.RecalculateBounds();EditorUtility.SetDirty(mesh);return mesh;
    }
    static void NeighborhoodHouse(GameObject root,int index,Vector3 position,float rotation,Material wall,Material trim,Material roof,Material glass,Material snow)
    {
        var home=Child(root,"Neighbor house "+index);float w=6+(index%3),d=4.5f+(index%2),eave=5.8f+(index%3)*.35f;
        Box(home,"Two storey facade",-w,w,-d,d,0,eave,wall);
        Box(home,"Foundation",-w-.05f,w+.05f,-d-.05f,d+.05f,0,.35f,roof);
        Box(home,"Eaves",-w-.3f,w+.3f,-d-.3f,d+.3f,eave-.12f,eave,trim);
        float ridge=eave+3;
        var mesh=NeighborhoodMesh("Roof"+index,new[]{new Vector3(-w-.35f,eave,-d-.35f),new Vector3(w+.35f,eave,-d-.35f),new Vector3(-w-.35f,eave,d+.35f),new Vector3(w+.35f,eave,d+.35f),new Vector3(-w-.35f,ridge,0),new Vector3(w+.35f,ridge,0)},new[]{0,4,1,1,4,5,2,3,4,3,5,4,0,2,4,1,5,3});
        var roofGo=Child(home,"Snow dusted pitched roof");roofGo.AddComponent<MeshFilter>().sharedMesh=mesh;roofGo.AddComponent<MeshRenderer>().sharedMaterial=index%3==0?roof:snow;
        Box(home,"Brick chimney",w-2,w-1,-.7f,.4f,eave,ridge+.6f,wall);
        for(int floor=0;floor<2;floor++)foreach(float x in new[]{-w*.65f,0,w*.65f}){
            float y=1.0f+floor*2.7f;
            if(floor==0&&x==0){Box(home,"Front door",-.50f,.50f,-d-.05f,-d-.015f,.2f,2.3f,roof);continue;}
            Box(home,"Window casing",x-.63f,x+.63f,-d-.065f,-d-.02f,y,y+1.65f,trim);
            Box(home,"Window glass",x-.53f,x+.53f,-d-.085f,-d-.07f,y+.1f,y+1.55f,glass);
            Box(home,"Window mullion",x-.025f,x+.025f,-d-.095f,-d-.085f,y+.1f,y+1.55f,trim);
            Box(home,"Window meeting rail",x-.55f,x+.55f,-d-.095f,-d-.085f,y+.8f,y+.85f,trim);
        }
        foreach(float x in new[]{-w-.02f,w+.02f})foreach(float z in new[]{-d*.5f,d*.5f})for(int floor=0;floor<2;floor++){
            float y=1+floor*2.7f;Box(home,"Side window trim",x-.025f,x+.025f,z-.57f,z+.57f,y,y+1.6f,trim);
            Box(home,"Side window glass",x-.035f,x+.035f,z-.48f,z+.48f,y+.09f,y+1.51f,glass);
        }
        Box(home,"Porch platform",-1.25f,1.25f,-d-1.4f,-d,.05f,.28f,trim);
        foreach(float x in new[]{-1.07f,1.07f})Cyl(home,"Porch column",x,-d-1.1f,.28f,2.8f,.065f,trim);
        Box(home,"Porch canopy",-1.35f,1.35f,-d-1.5f,-d+.1f,2.8f,3,roof);
        home.transform.SetPositionAndRotation(position,Quaternion.Euler(0,rotation,0));
    }
    static void NeighborhoodShutterPair(GameObject root,float x,float y,float height,float windowWidth,Material material)
    {
        foreach(int side in new[]{-1,1}){
            float cx=x+side*(windowWidth*.5f+.27f);
            Box(root,"Shutter panel",cx-.22f,cx+.22f,-2.75f,-2.67f,y-height*.5f,y+height*.5f,material);
            for(int i=0;i<18;i++){float yy=y-height*.5f+.09f+i*(height-.18f)/18;Box(root,"Louver",cx-.18f,cx+.18f,-2.765f,-2.75f,yy,yy+.022f,material);}
        }
    }
    static void NeighborhoodRod(GameObject root,string name,Vector3 a,Vector3 b,float radius,Material material)
    {
        var go=Cyl(root,name,0,0,0,(b-a).magnitude,radius,material);go.transform.position=(a+b)/2;go.transform.rotation=Quaternion.FromToRotation(Vector3.up,(b-a).normalized);
    }
    static void NeighborhoodTree(GameObject root,int seed,Vector3 position,float scale,Material bark)
    {
        var rng=new System.Random(seed%5+12);var vertices=new List<Vector3>();var triangles=new List<int>();
        Action<Vector3,Vector3,float,float> segment=(a,b,r0,r1)=>{
            Vector3 axis=(b-a).normalized,u=Vector3.Cross(axis,Vector3.right).normalized;if(u.sqrMagnitude<.1f)u=Vector3.Cross(axis,Vector3.forward).normalized;var v=Vector3.Cross(axis,u);
            int start=vertices.Count;for(int j=0;j<2;j++)for(int i=0;i<7;i++){float angle=i*Mathf.PI*2/7;vertices.Add((j==0?a:b)+(u*Mathf.Cos(angle)+v*Mathf.Sin(angle))*(j==0?r0:r1));}
            for(int i=0;i<7;i++){int k=start+i,n=start+(i+1)%7;triangles.AddRange(new[]{k,n,k+7,n,n+7,k+7});}
        };
        segment(Vector3.zero,new Vector3(.15f,5.5f,0),.30f,.17f);
        for(int branch=0;branch<7;branch++){
            float angle=branch*2.4f;var a=new Vector3(.1f,3.5f+branch*.45f,0);var b=a+new Vector3(Mathf.Cos(angle)*3,3+(float)rng.NextDouble()*2,Mathf.Sin(angle)*3);
            segment(a,b,.15f,.055f);
            for(int twig=0;twig<4;twig++){
                float q=angle+twig*.95f;var c=b+new Vector3(Mathf.Cos(q)*1.9f,1.2f+(float)rng.NextDouble()*1.5f,Mathf.Sin(q)*1.9f);segment(b,c,.052f,.015f);
                var end=c+new Vector3(Mathf.Cos(q+.6f),.85f,Mathf.Sin(q+.6f));segment(c,end,.015f,.004f);
            }
        }
        var mesh=NeighborhoodMesh("WinterTree"+(seed%5),vertices.ToArray(),triangles.ToArray());var tree=Child(root,"Mature bare street tree");tree.AddComponent<MeshFilter>().sharedMesh=mesh;tree.AddComponent<MeshRenderer>().sharedMaterial=bark;tree.transform.position=position;tree.transform.localScale=Vector3.one*scale;
        var trunk=tree.AddComponent<CapsuleCollider>();trunk.radius=.32f;trunk.height=5.5f;trunk.center=new Vector3(0,2.75f,0);
    }
}
