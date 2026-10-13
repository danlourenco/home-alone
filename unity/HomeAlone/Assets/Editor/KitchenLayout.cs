using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

public static partial class SurveyBuilder
{
    // Circulation blockout from the supplied Marina overhead, not measured film furniture.
    public static void AddKitchenLayoutFurniture()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var old=GameObject.Find("Kitchen layout furniture");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Kitchen layout furniture");
        var wood=FoyerFinish("KitchenLayoutWood",new Color(.36f,.20f,.10f),.25f);
        var seat=FoyerFinish("KitchenLayoutSeat",new Color(.58f,.43f,.25f),.15f);
        var table=Child(root,"Breakfast oval table");
        var vertices=new List<Vector3>();var triangles=new List<int>();
        for(int ring=0;ring<2;ring++)for(int i=0;i<48;i++){
            float a=i*Mathf.PI/24;
            vertices.Add(new Vector3(8.8f+.525f*Mathf.Cos(a),2.02f+ring*.055f,10.8f+.525f*Mathf.Sin(a)+(Mathf.Sin(a)>=0?.875f:-.875f)));
        }
        for(int i=0;i<48;i++){
            int j=(i+1)%48;triangles.AddRange(new[]{i,i+48,j,j,i+48,j+48});
            if(i>0&&i<47)triangles.AddRange(new[]{48,48+i+1,48+i,0,i,i+1});
        }
        var top=Child(table,"Rounded tabletop");top.AddComponent<MeshFilter>().sharedMesh=NeighborhoodMesh("BreakfastTable",vertices.ToArray(),triangles.ToArray());
        top.AddComponent<MeshRenderer>().sharedMaterial=wood;top.AddComponent<MeshCollider>().sharedMesh=top.GetComponent<MeshFilter>().sharedMesh;
        foreach(float x in new[]{8.45f,9.15f})foreach(float z in new[]{9.95f,11.65f})Box(table,"Table leg",x-.045f,x+.045f,z-.045f,z+.045f,1.31f,2.02f,wood);
        foreach(float z in new[]{9.95f,10.8f,11.65f}){
            KitchenLayoutChair(root,"Breakfast chair",new Vector3(7.91f,1.31f,z),90,.45f,wood,seat);
            KitchenLayoutChair(root,"Breakfast chair",new Vector3(9.69f,1.31f,z),270,.45f,wood,seat);
        }
        KitchenLayoutChair(root,"Breakfast chair",new Vector3(8.8f,1.31f,9.05f),0,.45f,wood,seat);
        KitchenLayoutChair(root,"Breakfast chair",new Vector3(8.8f,1.31f,12.55f),180,.45f,wood,seat);
        for(int i=0;i<5;i++)KitchenLayoutChair(root,"Island stool",new Vector3(14.25f,1.31f,13.42f+i*.53f),270,.69f,wood,seat);
        for(int i=0;i<3;i++)KitchenLayoutChair(root,"Island stool",new Vector3(12.1f+i*.65f,1.31f,12.25f),0,.69f,wood,seat);
    }
    public static void AlignBreakfastChandelier()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play before aligning the saved fixture.");
        var fixture=GameObject.Find("Breakfast bowl chandelier");
        var rose=fixture.transform.Find("Ceiling rose");
        var offset=new Vector3(8.8f-rose.position.x,0,10.8f-rose.position.z);
        fixture.transform.position+=offset;
        var light=GameObject.Find("Breakfast chandelier light").transform;
        light.position=new Vector3(8.8f,light.position.y,10.8f);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(fixture.scene);
    }
    static void KitchenLayoutChair(GameObject root,string name,Vector3 position,float yaw,float seatHeight,Material wood,Material seat)
    {
        var chair=Child(root,name);
        Box(chair,"Seat",-.22f,.22f,-.22f,.22f,seatHeight,seatHeight+.045f,seat);
        foreach(float x in new[]{-.17f,.17f})foreach(float z in new[]{-.17f,.17f})Box(chair,"Leg",x-.022f,x+.022f,z-.022f,z+.022f,0,seatHeight,wood);
        foreach(float x in new[]{-.19f,.19f})Box(chair,"Back post",x-.023f,x+.023f,-.22f,-.174f,seatHeight,seatHeight+.43f,wood);
        Box(chair,"Back rail",-.19f,.19f,-.22f,-.174f,seatHeight+.35f,seatHeight+.43f,wood);
        for(int i=0;i<3;i++)Box(chair,"Back spindle",-.11f+i*.11f-.012f,-.11f+i*.11f+.012f,-.212f,-.188f,seatHeight+.05f,seatHeight+.35f,wood);
        chair.transform.SetPositionAndRotation(position,Quaternion.Euler(0,yaw,0));
    }
    public static string CheckKitchenLayoutFurniture()
    {
        if(!EditorApplication.isPlaying)throw new InvalidOperationException("Enter Play first.");
        var root=GameObject.Find("Kitchen layout furniture");
        if(!root||root.transform.Cast<Transform>().Count(t=>t.name=="Breakfast chair")!=8||root.transform.Cast<Transform>().Count(t=>t.name=="Island stool")!=8)throw new InvalidOperationException("Incomplete seating blockout.");
        var top=root.GetComponentInChildren<MeshCollider>();
        if(!top.Raycast(new Ray(new Vector3(8.8f,3,10.8f),Vector3.down),out var hit,2)||hit.normal.y<.9f||Mathf.Abs(hit.point.y-2.075f)>.001f)throw new InvalidOperationException("Tabletop collision/winding incorrect.");
        foreach(var t in new[]{GameObject.Find("Breakfast bowl chandelier").transform.Find("Ceiling rose"),GameObject.Find("Breakfast chandelier light").transform})
            if(Vector2.Distance(new Vector2(t.position.x,t.position.z),new Vector2(8.8f,10.8f))>.01f)throw new InvalidOperationException("Breakfast fixture is offset from table.");
        var f=GameObject.Find("Player").GetComponent<FpsController>();var cc=f.GetComponent<CharacterController>();var original=f.transform.position;bool enabled=f.enabled;
        var route=new[]{new Vector3(7.3f,1.31f,8),new Vector3(7.3f,1.31f,13.2f),new Vector3(10.5f,1.31f,13.2f),new Vector3(10.5f,1.31f,10),new Vector3(11,1.31f,10),new Vector3(11,1.31f,16.8f),new Vector3(14.95f,1.31f,16.8f),new Vector3(14.95f,1.31f,11.5f),new Vector3(11,1.31f,11.5f),new Vector3(9.6f,1.31f,8)};
        try{f.enabled=false;cc.enabled=false;f.transform.position=route[0]+Vector3.up*.1f;cc.enabled=true;Physics.SyncTransforms();
            foreach(var p in route){
                for(int i=0;i<1000;i++){var d=p-f.transform.position;d.y=0;if(d.magnitude<.08f)break;f.TickMotion(d,false,false,1f/60);}
                for(int i=0;i<60;i++)f.TickMotion(Vector3.zero,false,false,1f/60);
                if(Vector3.Distance(p,f.transform.position)>.18f||!cc.isGrounded)throw new InvalidOperationException("Seating route blocked at "+f.transform.position+" target "+p);
            }
        }finally{cc.enabled=false;f.transform.position=original;cc.enabled=true;f.enabled=enabled;}
        return "PASS table surface, 8 breakfast chairs, 8 island stools and 10 continuous circulation checkpoints.";
    }
}
