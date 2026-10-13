using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public static partial class SurveyBuilder
{
    struct WindowVertex
    {
        public Vector3 p,n;
        public Vector4 t;
        public Vector2 uv,uv2;
        public Color color;
        public static WindowVertex Between(WindowVertex a,WindowVertex b,float t)
        {
            return new WindowVertex{p=Vector3.LerpUnclamped(a.p,b.p,t),n=Vector3.LerpUnclamped(a.n,b.n,t),
                t=Vector4.LerpUnclamped(a.t,b.t,t),uv=Vector2.LerpUnclamped(a.uv,b.uv,t),
                uv2=Vector2.LerpUnclamped(a.uv2,b.uv2,t),color=Color.LerpUnclamped(a.color,b.color,t)};
        }
    }
    // Subtract oriented opening boxes; preserve the outside polygon and interpolate its texture coordinates.
    static Mesh CutWindowTriangles(Mesh source,Transform owner,
        List<(Vector3 center,float w,float h,float yaw,int cols,int rows,string label)> specs,out int changed,float depth=.5f)
    {
        var p=source.vertices;var n=source.normals;var t=source.tangents;var uv=source.uv;var uv2=source.uv2;var colors=source.colors;
        var vertices=new WindowVertex[p.Length];
        for(int i=0;i<p.Length;i++)vertices[i]=new WindowVertex{p=p[i],n=n.Length==p.Length?n[i]:Vector3.up,t=t.Length==p.Length?t[i]:Vector4.zero,
            uv=uv.Length==p.Length?uv[i]:Vector2.zero,uv2=uv2.Length==p.Length?uv2[i]:Vector2.zero,color=colors.Length==p.Length?colors[i]:Color.white};
        var boxes=specs.Select(s=>{
            var matrix=Matrix4x4.TRS(s.center,Quaternion.Euler(s.label=="Sloped roof glazing"?49:0,s.yaw,0),Vector3.one).inverse*owner.localToWorldMatrix;
            return (matrix,extent:new Vector3(s.w/2+.041f,s.h/2+.051f,depth/2));
        }).ToArray();
        var output=new List<WindowVertex>();var submeshes=new List<int[]>();changed=0;
        for(int sm=0;sm<source.subMeshCount;sm++){
            var indices=new List<int>();var ts=source.GetTriangles(sm);
            for(int i=0;i<ts.Length;i+=3){
                var pieces=new List<List<WindowVertex>>{new List<WindowVertex>{vertices[ts[i]],vertices[ts[i+1]],vertices[ts[i+2]]}};
                bool touched=false;
                foreach(var box in boxes){
                    var next=new List<List<WindowVertex>>();
                    foreach(var piece in pieces){
                        // Fast rejection against any separating box plane.
                        bool outside=false;
                        for(int plane=0;plane<6&&!outside;plane++)outside=piece.All(v=>WindowPlane(v.p,box.matrix,box.extent,plane)>0);
                        if(outside){next.Add(piece);continue;}
                        touched=true;var inside=piece;
                        for(int plane=0;plane<6&&inside.Count>=3;plane++){
                            var keep=new List<WindowVertex>();var reject=new List<WindowVertex>();
                            for(int k=0;k<inside.Count;k++){
                                var a=inside[k];var b=inside[(k+1)%inside.Count];
                                float da=WindowPlane(a.p,box.matrix,box.extent,plane),db=WindowPlane(b.p,box.matrix,box.extent,plane);
                                if(da<=0)keep.Add(a);else reject.Add(a);
                                if((da<0&&db>0)||(da>0&&db<0)){
                                    var crossing=WindowVertex.Between(a,b,da/(da-db));keep.Add(crossing);reject.Add(crossing);
                                }
                            }
                            if(reject.Count>=3)next.Add(reject);inside=keep;
                        }
                    }
                    pieces=next;if(pieces.Count==0)break;
                }
                if(touched)changed++;
                foreach(var piece in pieces)for(int k=1;k+1<piece.Count;k++){
                    if(Vector3.Cross(piece[k].p-piece[0].p,piece[k+1].p-piece[0].p).sqrMagnitude<1e-14f)continue;
                    indices.Add(output.Count);output.Add(piece[0]);indices.Add(output.Count);output.Add(piece[k]);indices.Add(output.Count);output.Add(piece[k+1]);
                }
            }
            submeshes.Add(indices.ToArray());
        }
        var mesh=new Mesh{name=source.name+" window cut",indexFormat=UnityEngine.Rendering.IndexFormat.UInt32};
        mesh.SetVertices(output.Select(v=>v.p).ToList());
        if(n.Length>0)mesh.SetNormals(output.Select(v=>v.n.normalized).ToList());
        if(t.Length>0)mesh.SetTangents(output.Select(v=>v.t).ToList());
        if(uv.Length>0)mesh.SetUVs(0,output.Select(v=>v.uv).ToList());
        if(uv2.Length>0)mesh.SetUVs(1,output.Select(v=>v.uv2).ToList());
        if(colors.Length>0)mesh.SetColors(output.Select(v=>v.color).ToList());
        mesh.subMeshCount=submeshes.Count;for(int sm=0;sm<submeshes.Count;sm++)mesh.SetTriangles(submeshes[sm],sm);
        mesh.RecalculateBounds();return mesh;
    }
    public static string CheckWindowClipping()
    {
        var go=new GameObject("Temporary window clipping check");var source=new Mesh();Mesh result=null;
        try{
            source.vertices=new[]{new Vector3(-1,-1,0),new Vector3(1,-1,0),new Vector3(1,1,0),new Vector3(-1,1,0)};
            source.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};source.triangles=new[]{0,1,2,0,2,3};source.RecalculateNormals();
            foreach(bool sloped in new[]{false,true}){
                go.transform.rotation=Quaternion.Euler(sloped?49:0,0,0);
                var boxes=new List<(Vector3 center,float w,float h,float yaw,int cols,int rows,string label)>{(Vector3.zero,1,1,0,2,4,sloped?"Sloped roof glazing":"Test")};
                result=CutWindowTriangles(source,go.transform,boxes,out var changed);
                var vs=result.vertices;var uv=result.uv;var ts=result.triangles;float area=0;
                for(int i=0;i<ts.Length;i+=3)area+=Vector3.Cross(vs[ts[i+1]]-vs[ts[i]],vs[ts[i+2]]-vs[ts[i]]).magnitude/2;
                float expected=4-1.082f*1.102f;
                if(changed!=2||Mathf.Abs(area-expected)>.0001f)throw new System.InvalidOperationException("Window clipping removed the wrong area: "+area);
                for(int i=0;i<vs.Length;i++)if(Vector2.Distance(uv[i],new Vector2((vs[i].x+1)/2,(vs[i].y+1)/2))>.0001f)throw new System.InvalidOperationException("Window clipping changed UV alignment");
                UnityEngine.Object.DestroyImmediate(result);result=null;
            }
            return "PASS crossing-triangle clipping: vertical/sloped area and UV preservation";
        }finally{if(result)UnityEngine.Object.DestroyImmediate(result);UnityEngine.Object.DestroyImmediate(source);UnityEngine.Object.DestroyImmediate(go);}
    }
    static float WindowPlane(Vector3 p,Matrix4x4 matrix,Vector3 extent,int plane)
    {
        var q=matrix.MultiplyPoint3x4(p);int axis=plane/2;return q[axis]*(plane%2==0?1:-1)-extent[axis];
    }
}
