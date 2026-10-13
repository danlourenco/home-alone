using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SurveyBuilder
{
    const string IntactScene="Assets/Scenes/IntactHouseReference.unity";
    // Native basement treads were covered by the imported ground slab. Preserve the
    // slab everywhere outside the existing 1.32 m stair width; no historical resizing.
    public static string OpenIntactBasementStairSlab()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play before saving the stair opening.");
        var mf=GameObject.Find("IntactGLB").GetComponentsInChildren<MeshFilter>().Single(m=>m.name=="object250");
        const string path="Assets/Materials/IntactFoyer/BasementStairSlabCut.asset";
        if(AssetDatabase.GetAssetPath(mf.sharedMesh)==path)return "Basement stair slab already cut.";
        var cut=CutWindowTriangles(mf.sharedMesh,mf.transform,
            new System.Collections.Generic.List<(Vector3,float,float,float,int,int,string)>{
                (new Vector3(5.59f,.43f,11.86f),3.918f,1f,90,1,1,"Existing basement stair")},out int changed,1.32f);
        if(changed==0){UnityEngine.Object.DestroyImmediate(cut);throw new InvalidOperationException("No basement slab triangles intersected.");}
        var mesh=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(!mesh){mesh=cut;AssetDatabase.CreateAsset(mesh,path);}
        else{EditorUtility.CopySerialized(cut,mesh);UnityEngine.Object.DestroyImmediate(cut);}
        mf.sharedMesh=mesh;mf.GetComponent<MeshCollider>().sharedMesh=mesh;
        EditorSceneManager.MarkSceneDirty(mf.gameObject.scene);AssetDatabase.SaveAssets();
        return "Opened native basement stair through overlapping slab; clipped triangles: "+changed;
    }
    [MenuItem("HomeAlone/Reference/Open Intact GLB")]
    public static void BuildIntactHouseReference()
    {
        if(EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)
            throw new InvalidOperationException("Leave Play mode and save the scene before opening the reference.");
        EditorSceneManager.OpenScene("Assets/Scenes/CentralHall.unity");
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),IntactScene);
        GameObject.Find("House").SetActive(false);
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/ThirdParty/HomeAloneExterior/HomeAloneExterior.glb");
        if(!prefab)throw new InvalidOperationException("Original GLB prefab is missing.");
        var model=(GameObject)PrefabUtility.InstantiatePrefab(prefab);
        model.name="IntactGLB";model.transform.position=Vector3.zero;
        model.transform.rotation=Quaternion.Euler(0,180,0);model.transform.localScale=Vector3.one;
        // Same leaf/handle pairs used by the original Godot walkthrough; retain frames.
        // The linen closet receives its reference-based closed door below.
        foreach(var id in new[]{2925,2929,2933,2937,2941,2957,2961,2965,2969,2973,2977,2981,2985,2989,2993,2997,3001,3005})
            foreach(var part in new[]{id,id+2})
            {
                var door=model.GetComponentsInChildren<Transform>(true).Single(t=>t.name=="object"+part);
                door.gameObject.SetActive(false);
            }
        foreach(var mf in model.GetComponentsInChildren<MeshFilter>())
        {
            if(!mf.sharedMesh)continue;
            var collider=mf.GetComponent<MeshCollider>();
            if(!collider) collider=mf.gameObject.AddComponent<MeshCollider>();
            collider.sharedMesh=mf.sharedMesh;
        }
        BuildFilmLinenDoor();
        var player=GameObject.Find("Player");var cc=player.GetComponent<CharacterController>();cc.enabled=false;
        player.transform.position=new Vector3(1.9f,1.4f,0);player.transform.rotation=Quaternion.identity;cc.enabled=true;
        player.GetComponent<FpsController>().enabled=true;
        Physics.SyncTransforms();
        if(!Physics.Raycast(new Vector3(1.9f,3f,0),Vector3.down,out var ground,2f) || Mathf.Abs(ground.point.y-1.31f)>.1f)
            throw new InvalidOperationException("Reference spawn has no valid ground-floor collision.");
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),IntactScene);
        Debug.Log("Intact GLB walkthrough saved at native scale, with 18 door leaves and their handles hidden. Frames and source asset retained.");
    }

    [MenuItem("HomeAlone/Reference/Check Intact Main Stairs")]
    public static string CheckIntactMainStairs()
    {
        if(!EditorApplication.isPlaying || !GameObject.Find("IntactGLB"))throw new InvalidOperationException("Enter Play in IntactHouseReference first.");
        var fps=GameObject.Find("Player").GetComponent<FpsController>();var cc=fps.GetComponent<CharacterController>();
        var original=fps.transform.position;var enabled=fps.enabled;var log=new System.Text.StringBuilder();
        var route=new[]{new Vector3(.1f,1.31f,3.7f),new Vector3(.1f,4.45f,8.8f),
            new Vector3(3.55f,4.45f,8.8f),new Vector3(3.55f,5.22f,6.7f),new Vector3(3.55f,5.22f,3.5f),
            new Vector3(.1f,5.22f,3.5f),new Vector3(3.55f,5.22f,3.5f),new Vector3(3.55f,5.22f,6.7f),
            new Vector3(3.55f,4.45f,8.8f),new Vector3(.1f,4.45f,8.8f),new Vector3(.1f,1.31f,3.7f)};
        try
        {
            int expected=GameObject.Find("Brass candle chandelier")?271:273;
            if(GameObject.Find("object2981"))expected+=GameObject.Find("object2981").GetComponents<MeshCollider>().Length+GameObject.Find("object2983").GetComponents<MeshCollider>().Length;
            if(GameObject.Find("IntactGLB").GetComponentsInChildren<MeshCollider>().Length!=expected)
                throw new InvalidOperationException("Unexpected active collider count after hiding doors and fixture placeholders.");
            fps.enabled=false;cc.enabled=false;fps.transform.position=new Vector3(1.9f,1.4f,0);cc.enabled=true;Physics.SyncTransforms();
            for(int i=0;i<180;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
            if(!cc.isGrounded || Mathf.Abs(fps.transform.position.y-1.39f)>.15f)
                throw new InvalidOperationException("Reference spawn does not settle on the floor.");
            log.AppendLine("PASS spawn settles on intact floor.");
            foreach(var target in route)
            {
                bool reached=false;
                for(int i=0;i<900;i++)
                {
                    var delta=target-fps.transform.position;delta.y=0;
                    if(delta.magnitude<.06f){reached=true;break;}
                    fps.TickMotion(delta,false,false,1f/60);
                }
                for(int i=0;i<90;i++)fps.TickMotion(Vector3.zero,false,false,1f/60);
                bool pass=reached&&Mathf.Abs(fps.transform.position.y-target.y)<.15f&&cc.isGrounded;
                log.AppendLine($"{(pass?"PASS":"FAIL")} target {target} actual {fps.transform.position}");
                if(!pass)break;
            }
            System.IO.Directory.CreateDirectory("Captures/IntactHouseReference");
            System.IO.File.WriteAllText("Captures/IntactHouseReference/traversal.txt",log.ToString());
            if(log.ToString().Contains("FAIL"))throw new InvalidOperationException(log.ToString());
            return log.ToString();
        }
        finally{cc.enabled=false;fps.transform.position=original;cc.enabled=true;fps.enabled=enabled;}
    }
}
