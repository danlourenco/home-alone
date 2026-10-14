using System;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Replace Main Front Windows")]
    public static void ReplaceMainFrontWindows()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Leave Play first");
        var old=GameObject.Find("Main front window assemblies");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Main front window assemblies");
        var trim=FoyerFinish("FrontWindowIvory",new Color(.86f,.84f,.76f),.38f);
        var glass=FoyerFinish("FrontWindowGlass",new Color(.82f,.9f,.95f,.08f),.92f);
        glass.SetFloat("_SurfaceType",1);glass.SetFloat("_ZWrite",0);glass.SetFloat("_TransparentZWrite",0);glass.renderQueue=3000;HDMaterial.ValidateMaterial(glass);
        foreach(var spec in ExteriorWindowOpenings()){
            float w=spec.w,h=spec.h;int cols=spec.cols,rows=spec.rows;
            var window=Child(root,spec.label);
            Box(window,"Clear glazing",-w/2,w/2,-.04f,-.03f,-h/2,h/2,glass);
            foreach(float xx in new[]{-w/2,w/2})Box(window,"Recessed jamb",xx-.019f,xx+.019f,-.19f,.14f,-h/2+.03f,h/2-.03f,trim);
            foreach(float yy in new[]{-h/2,h/2})Box(window,"Frame rail",-w/2-.019f,w/2+.019f,-.19f,.14f,yy-.03f,yy+.03f,trim);
            Box(window,"Projecting sill",-w/2-.019f,w/2+.019f,-.26f,.15f,-h/2-.065f,-h/2-.031f,trim);
            for(int c=1;c<cols;c++){
                float xx=-w/2+c*w/cols,thick=cols==4&&c==2?.035f:.012f;
                Box(window,"Vertical glazing bar",xx-thick/2,xx+thick/2,-.13f,.01f,-h/2+.03f,h/2-.03f,trim);
            }
            for(int r=1;r<rows;r++){
                float yy=-h/2+r*h/rows,thick=r==rows/2?.045f:.018f;
                for(int c=0;c<cols;c++){
                    float left=-w/2+c*w/cols+(c==0?.03f:(cols==4&&c==2?.0175f:.006f));
                    float right=-w/2+(c+1)*w/cols-(c==cols-1?.03f:(cols==4&&c+1==2?.0175f:.006f));
                    Box(window,r==rows/2?"Meeting rail":"Horizontal glazing bar",left,right,-.14f,.01f,yy-thick/2,yy+thick/2,trim);
                }
            }
            window.transform.SetPositionAndRotation(spec.center,Quaternion.Euler(spec.label=="Sloped roof glazing"?49:0,spec.yaw,0));
        }
        // Clip crossing triangles as well as contained ones; otherwise old frame fragments remain coplanar with replacements.
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/ThirdParty/HomeAloneExterior/HomeAloneExterior.glb");
        var originals=prefab.GetComponentsInChildren<MeshFilter>(true).ToDictionary(m=>m.name,m=>m.sharedMesh);
        int removed=0;
        foreach(var mf in GameObject.Find("IntactGLB").GetComponentsInChildren<MeshFilter>()){
            if(!originals.TryGetValue(mf.name,out var source)||!source)continue;
            var cut=CutWindowTriangles(source,mf.transform,ExteriorWindowOpenings(),out int count);
            if(count==0){UnityEngine.Object.DestroyImmediate(cut);continue;}
            string path="Assets/Materials/IntactFoyer/FrontWindowCut_"+mf.name+".asset";
            var mesh=AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if(!mesh){mesh=cut;AssetDatabase.CreateAsset(mesh,path);}else{EditorUtility.CopySerialized(cut,mesh);UnityEngine.Object.DestroyImmediate(cut);}
            EditorUtility.SetDirty(mesh);mf.sharedMesh=mesh;removed+=count;
        }
        foreach(var r in GameObject.Find("IntactGLB").GetComponentsInChildren<Renderer>())
            if(new[]{"object3009","object3011","object3013","object3015"}.Contains(r.name))r.enabled=false;
        if(removed==0)throw new InvalidOperationException("No original window triangles found");
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
        Debug.Log("Exterior window assemblies; replaced "+removed+" plane triangles. Pane pattern fitted to photos, dimensions retain GLB openings.");
    }
    // Bounds measured from the adopted model. Front pane patterns use real-house photos;
    // less-visible rear patterns are provisional and retain existing opening dimensions.
    static List<(Vector3 center,float w,float h,float yaw,int cols,int rows,string label)> ExteriorWindowOpenings()
    {
        var specs=new List<(Vector3,float,float,float,int,int,string)>();
        foreach(float y in new[]{2.87f,6.64f})foreach(float x in (y<4?new[]{-4.77f,-2.49f,6.25f,8.53f}:new[]{-4.77f,-2.49f,1.88f,6.25f,8.53f}))
            specs.Add((new Vector3(x,y,-2.47f),y<4?1.14f:.94f,y<4?2.34f:1.62f,0,y<4?4:3,y<4?6:4,"Main front sash"));
        foreach(float x in new[]{-2.486f,6.25f})specs.Add((new Vector3(x,10.128f,-2.391f),1.33f,1.621f,0,3,4,"Front roof dormer"));
        specs.Add((new Vector3(1.882f,10.125f,10.861f),1.33f,1.621f,180,3,4,"Rear roof dormer"));
        foreach(float x in new[]{-8.944f,12.707f})foreach(float y in new[]{3.019f,6.715f})for(int i=0;i<5;i++)
            specs.Add((new Vector3(x+(i-2)*.72f,y,-1.084f),.68f,y<4?1.94f:1.67f,0,2,4,"Front wing sash"));
        foreach(float x in new[]{-11.223f,14.987f})foreach(float y in new[]{3.018f,6.713f})for(int i=0;i<5;i++)
            specs.Add((new Vector3(x,y,2.36f+(i-2)*.698f),.65f,y<4?1.94f:1.67f,x<0?90:270,2,4,"Side wing sash"));
        for(int i=0;i<5;i++)specs.Add((new Vector3(-8.944f+(i-2)*.72f,6.712f,8.157f),.68f,1.67f,180,2,4,"Rear west wing sash"));
        foreach(float x in new[]{-5.24f,-2.202f,10.049f})specs.Add((new Vector3(x,6.784f,10.947f),1.329f,1.621f,180,3,4,"Rear upper sash"));
        foreach(float x in new[]{-5.395f,-2.047f})specs.Add((new Vector3(x,2.904f,10.947f),1.021f,1.621f,180,3,4,"Rear lower sash"));
        foreach(float x in new[]{1.39f,2.71f})specs.Add((new Vector3(x,6.30f,10.947f),1.25f,1.94f,180,3,4,"Stair landing sash"));
        foreach(float x in new[]{-6.285f+BuzzShiftX,10.049f})specs.Add((new Vector3(x,6.642f,-1.803f),.872f,1.621f,x<0?90:270,2,4,"Recessed side sash"));   // Buzz's west wall moved (BuzzRoomResize.cs)
        specs.Add((new Vector3(13.847f,3.171f,18.792f),1.33f,1.375f,180,3,4,"Kitchen rear sash"));
        specs.Add((new Vector3(16.696f,3.173f,14.87f),1.221f,1.376f,270,3,4,"Kitchen side sash"));
        specs.Add((new Vector3(9.479f,3.098f,17.398f),1.046f,1.228f,90,2,4,"Rear service sash"));
        specs.Add((new Vector3(7.864f,3.099f,15.479f),1.329f,1.228f,180,3,4,"Breakfast rear sash"));
        specs.Add((new Vector3(6.701f,6.783f,15.48f),1.33f,1.621f,180,3,4,"Rear upper extension sash"));
        specs.Add((new Vector3(11.378f,2.88f,8.462f),.76f,.786f,180,2,2,"Small rear sash"));
        foreach(float x in new[]{1.20f,1.91f,2.63f})specs.Add((new Vector3(x,10.21f,-1.25f),.64f,2.75f,0,2,4,"Sloped roof glazing"));
        return specs;
    }
    public static string CheckFrontWindows()
    {
        var root=GameObject.Find("Main front window assemblies");
        if(!root||root.transform.childCount!=ExteriorWindowOpenings().Count)throw new InvalidOperationException("Incomplete exterior window assemblies");
        var panes=root.GetComponentsInChildren<Renderer>().Where(r=>r.name=="Clear glazing").ToArray();
        if(panes.Length!=ExteriorWindowOpenings().Count||panes.Any(r=>r.sharedMaterial.GetFloat("_SurfaceType")!=1||r.sharedMaterial.GetColor("_BaseColor").a>.15f))throw new InvalidOperationException("Glazing must remain transparent");
        foreach(var pane in panes)if(!pane.GetComponent<BoxCollider>())throw new InvalidOperationException("Missing physical window barrier");
        foreach(Transform window in root.transform){
            var parts=window.GetComponentsInChildren<BoxCollider>().Where(c=>c.name!="Clear glazing").ToArray();
            for(int a=0;a<parts.Length;a++)for(int b=a+1;b<parts.Length;b++){
                var ca=parts[a];var cb=parts[b];
                var ba=new Bounds(ca.transform.localPosition,Vector3.Scale(ca.size,ca.transform.localScale));
                var bb=new Bounds(cb.transform.localPosition,Vector3.Scale(cb.size,cb.transform.localScale));
                var overlap=Vector3.Min(ba.max,bb.max)-Vector3.Max(ba.min,bb.min);
                if(overlap.x>.00005f&&overlap.y>.00005f&&overlap.z>.00005f)throw new InvalidOperationException("Overlapping window join: "+ca.name+" / "+cb.name);
            }
        }
        return "PASS "+panes.Length+" window assemblies, transparent glazing, physical barriers and non-overlapping frame joints";
    }

}
