using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    // Material-only overrides: the source GLB and collision meshes stay untouched.
    [MenuItem("HomeAlone/Reference/Apply Foyer Finishes")]
    public static void ApplyIntactFoyerFinishes()
    {
        if(EditorApplication.isPlaying) throw new InvalidOperationException("Leave Play mode first.");
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if(scene.path!=IntactScene) throw new InvalidOperationException("Open IntactHouseReference first.");
        const string folder="Assets/Materials/IntactFoyer";
        if(!AssetDatabase.IsValidFolder(folder)) AssetDatabase.CreateFolder("Assets/Materials","IntactFoyer");
        var paper=FoyerFinish("Damask",Color.white,.12f,"Assets/Textures/MarinaFoyerDamask.png",1.35f);
        var paint=FoyerFinish("IvoryPaint",new Color(.92f,.90f,.84f),.32f);
        var carpet=FoyerFinish("BurgundyRunner",new Color(.32f,.018f,.032f),.05f);
        var wood=FoyerFinish("DarkWood",new Color(.48f,.32f,.23f),.35f,"Assets/Textures/wood_floor_diff.jpg",2.4f);
        var root=GameObject.Find("IntactGLB");
        foreach(var id in new[]{102,141,147,178,179,199,202}) FoyerAssign(root,id,paper);
        foreach(var id in new[]{140,177,209,222,234}) FoyerAssign(root,id,paint);
        FoyerAssign(root,212,carpet);
        FoyerAssign(root,211,wood);
        AssetDatabase.SaveAssets(); EditorSceneManager.SaveScene(scene);
    }

    static Material FoyerFinish(string name,Color color,float smooth,string texture=null,float repeat=1)
    {
        string path="Assets/Materials/IntactFoyer/"+name+".mat";
        var m=AssetDatabase.LoadAssetAtPath<Material>(path);
        if(!m){m=new Material(Shader.Find("HDRP/Lit"));AssetDatabase.CreateAsset(m,path);}
        m.SetColor("_BaseColor",color);m.SetFloat("_Smoothness",smooth);
        if(texture!=null)
        {
            m.SetTexture("_BaseColorMap",AssetDatabase.LoadAssetAtPath<Texture2D>(texture));
            m.SetFloat("_UVBase",5);m.SetFloat("_TexWorldScale",1/repeat);
            m.EnableKeyword("_MAPPING_TRIPLANAR");
        }
        HDMaterial.ValidateMaterial(m);EditorUtility.SetDirty(m);return m;
    }

    static void FoyerAssign(GameObject root,int id,Material finish)
    {
        var node=root.GetComponentsInChildren<MeshFilter>().Single(m=>m.name=="object"+id);
        // Always split from the original collider mesh, making repeat application idempotent.
        var source=node.GetComponent<MeshCollider>().sharedMesh;
        if(source.subMeshCount!=1)throw new InvalidOperationException("Unexpected original submeshes: "+node.name);
        var vertices=source.vertices;var indices=source.triangles;
        var local=new System.Collections.Generic.List<int>();var other=new System.Collections.Generic.List<int>();
        for(int i=0;i<indices.Length;i+=3)
        {
            var p=node.transform.TransformPoint((vertices[indices[i]]+vertices[indices[i+1]]+vertices[indices[i+2]])/3);
            bool foyer=p.x>=-1.3f&&p.x<=4.85f&&p.z>=-.3f&&p.z<=10.8f&&p.y>=1.3f&&p.y<=8.4f;
            var list=foyer?local:other;list.AddRange(new[]{indices[i],indices[i+1],indices[i+2]});
        }
        if(local.Count==0)throw new InvalidOperationException("No foyer faces: "+node.name);
        var mesh=UnityEngine.Object.Instantiate(source);mesh.name=node.name+"_FoyerFinish";
        mesh.subMeshCount=2;mesh.SetTriangles(other,0);mesh.SetTriangles(local,1);
        if(mesh.triangles.Length!=indices.Length)throw new InvalidOperationException("Finish changed triangle count.");
        string path="Assets/Materials/IntactFoyer/"+mesh.name+".asset";
        var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(saved){saved.Clear();EditorUtility.CopySerialized(mesh,saved);UnityEngine.Object.DestroyImmediate(mesh);mesh=saved;}
        else AssetDatabase.CreateAsset(mesh,path);
        var renderer=node.GetComponent<MeshRenderer>();var original=renderer.sharedMaterials[0];
        node.sharedMesh=mesh;renderer.sharedMaterials=new[]{original,finish};
    }
}
