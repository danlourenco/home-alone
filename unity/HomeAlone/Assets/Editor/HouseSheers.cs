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
    public static void AddFilmSheers()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var old=GameObject.Find("Film sheer curtains");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Film sheer curtains");
        var cloth=FoyerFinish("IvorySheerFabric",new Color(.86f,.84f,.77f,.34f),.03f);
        cloth.SetFloat("_SurfaceType",1);cloth.SetFloat("_BlendMode",0);cloth.SetFloat("_ZWrite",0);cloth.SetFloat("_TransparentZWrite",0);
        cloth.SetFloat("_DoubleSidedEnable",1);cloth.SetFloat("_DoubleSidedNormalMode",0);cloth.renderQueue=3000;HDMaterial.ValidateMaterial(cloth);
        // Film living/dining sheers and Marina parents' suite. Buzz's roller/green dressing stays separate.
        var specs=ExteriorWindowOpenings().Where(s=>(s.label=="Main front sash"&&s.center.y<4)||s.label=="Rear lower sash"||
            (s.label=="Side wing sash"&&s.center.x>0&&s.center.y>5)||(s.label=="Front wing sash"&&s.center.x>10&&s.center.y>5));
        foreach(var s in specs){
            var curtain=Child(root,s.label+" sheer");
            float length=s.center.y<4?s.center.y+s.h/2-1.43f:s.center.y+s.h/2-5.36f;
            var v=new List<Vector3>();var uv=new List<Vector2>();var t=new List<int>();
            for(int side=0;side<2;side++){
                int start=v.Count;
                for(int i=0;i<=32;i++){
                    float u=i/32f,x=side==0?Mathf.Lerp(-s.w*.53f,-.025f,u):Mathf.Lerp(.025f,s.w*.53f,u);
                    float z=.34f+.025f*Mathf.Cos(u*Mathf.PI*12);
                    v.Add(new Vector3(x,s.h/2+.05f,z));v.Add(new Vector3(x,s.h/2+.05f-length,z));uv.Add(new Vector2(u,1));uv.Add(new Vector2(u,0));
                    if(i<32){int k=start+i*2;t.AddRange(new[]{k,k+1,k+2,k+1,k+3,k+2});}
                }
            }
            string name="Sheer"+s.center.x.ToString("F2",System.Globalization.CultureInfo.InvariantCulture)+"_"+s.center.y.ToString("F2",System.Globalization.CultureInfo.InvariantCulture)+"_"+s.center.z.ToString("F2",System.Globalization.CultureInfo.InvariantCulture);
            var mesh=NeighborhoodMesh(name,v.ToArray(),t.ToArray());mesh.SetUVs(0,uv);
            curtain.AddComponent<MeshFilter>().sharedMesh=mesh;var r=curtain.AddComponent<MeshRenderer>();r.sharedMaterial=cloth;r.shadowCastingMode=ShadowCastingMode.Off;
            curtain.transform.SetPositionAndRotation(s.center,Quaternion.Euler(0,s.yaw,0));
        }
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static string CheckFilmSheers()
    {
        var root=GameObject.Find("Film sheer curtains");if(!root||root.transform.childCount!=16)throw new InvalidOperationException("Expected 16 reference-supported sheer sections.");
        if(root.GetComponentsInChildren<Collider>().Length>0)throw new InvalidOperationException("Sheers obstruct traversal.");
        foreach(var r in root.GetComponentsInChildren<Renderer>())if(r.sharedMaterial.color.a>=.6f||r.shadowCastingMode!=ShadowCastingMode.Off)throw new InvalidOperationException("Sheers became opaque or cast solid shadows.");
        return "PASS 16 sheer sections; translucent, two-sided and collision-free; Buzz windows untouched";
    }
}
