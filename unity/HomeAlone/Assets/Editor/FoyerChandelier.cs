using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    static void FoyerChandelier(GameObject parent,Material brass,Material ivory,bool breakfast=false)
    {
        var source=GameObject.Find("IntactGLB");
        foreach(var id in breakfast?new int[0]:new[]{236,237})
            source.GetComponentsInChildren<Transform>(true).Single(t=>t.name=="object"+id).gameObject.SetActive(false);
        var fixture=Child(parent,breakfast?"Breakfast bowl chandelier":"Brass candle chandelier");
        // Above the open void, between the main flight and upstairs gallery.
        float x=breakfast?8.8f:1.9f,z=breakfast?10.8f:7.2f,y=breakfast?3.55f:5.6f;
        float ceiling=breakfast?4.65f:8.36f;
        Cyl(fixture,"Ceiling rose",x,z,ceiling-.06f,ceiling,.13f,brass);
        Cyl(fixture,"Central stem",x,z,y-.23f,y+.32f,.037f,brass);
        foreach(var band in new[]{(-.23f,.075f),(-.12f,.105f),(.16f,.075f),(.30f,.055f)})
            Cyl(fixture,"Turned brass collar",x,z,y+band.Item1,y+band.Item1+.035f,band.Item2,brass);
        var glow=FoyerFinish("ChandelierBulb",new Color(1,.92f,.76f),.2f);
        glow.SetColor("_EmissiveColor",new Color(1,.72f,.4f)*6);
        HDMaterial.ValidateMaterial(glow);EditorUtility.SetDirty(glow);
        var glass=FoyerFinish("FixtureClearGlass",new Color(.9f,.96f,1,.13f),.85f);
        glass.SetFloat("_SurfaceType",1);glass.SetFloat("_BlendMode",0);glass.renderQueue=3000;HDMaterial.ValidateMaterial(glass);
        var opal=FoyerFinish("FixtureOpalGlass",new Color(.95f,.89f,.75f),.25f);
        opal.SetColor("_EmissiveColor",new Color(1,.82f,.58f)*2);HDMaterial.ValidateMaterial(opal);
        var vertices=new System.Collections.Generic.List<Vector3>();
        var triangles=new System.Collections.Generic.List<int>();
        const int steps=28,sides=8;
        for(int arm=0;arm<6;arm++)
        {
            float angle=arm*Mathf.PI/3;
            var radial=new Vector3(Mathf.Cos(angle),0,Mathf.Sin(angle));
            var side=new Vector3(-radial.z,0,radial.x);
            int start=vertices.Count;
            // Swept brass tube: drops from the hub, curves outward, rises to the candle cup.
            var a=Vector3.up*-.08f;var b=radial*.25f-Vector3.up*.46f;
            var c=radial*.59f-Vector3.up*.40f;var d=radial*.59f+Vector3.up*.10f;
            for(int i=0;i<=steps;i++)
            {
                float t=i/(float)steps,u=1-t;
                var p=u*u*u*a+3*u*u*t*b+3*u*t*t*c+t*t*t*d;
                var tangent=(3*u*u*(b-a)+6*u*t*(c-b)+3*t*t*(d-c)).normalized;
                var normal=Vector3.Cross(tangent,side).normalized;
                for(int j=0;j<sides;j++)
                {
                    float theta=j*2*Mathf.PI/sides;
                    vertices.Add(new Vector3(x,y,z)+p+.018f*(Mathf.Cos(theta)*side+Mathf.Sin(theta)*normal));
                    if(i==steps)continue;
                    int k=start+i*sides+j,n=start+i*sides+(j+1)%sides;
                    triangles.AddRange(new[]{k,n,k+sides,n,n+sides,k+sides});
                }
            }
            var candle=new Vector3(x,y,z)+d;
            Cyl(fixture,"Brass drip cup",candle.x,candle.z,candle.y-.025f,candle.y+.015f,.085f,brass);
            if(breakfast)
                FixtureShade(fixture,"Breakfast opal bowl",candle,opal,new[]{new Vector2(.04f,0),new Vector2(.08f,.025f),new Vector2(.14f,.09f),new Vector2(.20f,.19f),new Vector2(.205f,.23f)});
            else
            {
            Cyl(fixture,"Ivory candle",candle.x,candle.z,candle.y+.015f,candle.y+.23f,.027f,ivory);
            var bulb=GameObject.CreatePrimitive(PrimitiveType.Sphere);bulb.name="Candle bulb";bulb.transform.parent=fixture.transform;
            bulb.transform.position=candle+Vector3.up*.28f;bulb.transform.localScale=new Vector3(.042f,.105f,.042f);
            bulb.GetComponent<Renderer>().sharedMaterial=glow;Object.DestroyImmediate(bulb.GetComponent<Collider>());
                FixtureShade(fixture,"Clear hurricane shade",candle,glass,new[]{new Vector2(.065f,.015f),new Vector2(.105f,.09f),new Vector2(.10f,.25f),new Vector2(.075f,.38f),new Vector2(.08f,.43f)});
            }
        }
        // Alternating oval links connect the central stem to the upper ceiling rose.
        float chainTop=ceiling-.04f;
        float chainBottom=y+.30f;
        int links=Mathf.CeilToInt((chainTop-chainBottom)/.075f);
        for(int link=0;link<links;link++)
        {
            var center=new Vector3(x,Mathf.Lerp(chainBottom+.05f,chainTop-.05f,link/(float)(links-1)),z);
            var horizontal=link%2==0?Vector3.right:Vector3.forward;
            var perpendicular=Vector3.Cross(horizontal,Vector3.up);
            int start=vertices.Count;
            for(int i=0;i<24;i++)for(int j=0;j<8;j++)
            {
                float a=i*2*Mathf.PI/24,b=j*2*Mathf.PI/8;
                var normal=(horizontal*Mathf.Cos(a)+Vector3.up*Mathf.Sin(a)).normalized;
                vertices.Add(center+horizontal*(.027f*Mathf.Cos(a))+Vector3.up*(.05f*Mathf.Sin(a))
                    +.006f*(normal*Mathf.Cos(b)+perpendicular*Mathf.Sin(b)));
                int k=start+i*8+j,n=start+((i+1)%24)*8+j;
                int k1=start+i*8+(j+1)%8,n1=start+((i+1)%24)*8+(j+1)%8;
                triangles.AddRange(new[]{k,k1,n,k1,n1,n});
            }
        }
        var mesh=new Mesh{name="Chandelier curved arms"};mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
        string path="Assets/Materials/IntactFoyer/"+(breakfast?"BreakfastArms":"ChandelierArms")+".asset";
        var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(saved){saved.Clear();saved.vertices=mesh.vertices;saved.triangles=mesh.triangles;saved.RecalculateNormals();saved.RecalculateBounds();saved.UploadMeshData(false);EditorUtility.SetDirty(saved);Object.DestroyImmediate(mesh);mesh=saved;}else AssetDatabase.CreateAsset(mesh,path);
        var arms=Child(fixture,"Curved brass arms and suspension chain");arms.AddComponent<MeshFilter>().sharedMesh=mesh;arms.AddComponent<MeshRenderer>().sharedMaterial=brass;
        FoyerLamp(parent,breakfast?"Breakfast chandelier light":"Stairwell pendant light",new Vector3(x,y+.45f,z),breakfast?130:200,10);
    }
    // Open, double-sided glass surface; no solid caps to block the lamp inside.
    static void FixtureShade(GameObject parent,string name,Vector3 position,Material material,Vector2[] profile)
    {
        var vertices=new System.Collections.Generic.List<Vector3>();var triangles=new System.Collections.Generic.List<int>();
        for(int row=0;row<profile.Length;row++)for(int i=0;i<32;i++)
        {
            float a=i*Mathf.PI/16;vertices.Add(new Vector3(profile[row].x*Mathf.Cos(a),profile[row].y,profile[row].x*Mathf.Sin(a)));
            if(row==profile.Length-1)continue;
            int k=row*32+i,n=row*32+(i+1)%32;
            triangles.AddRange(new[]{k,k+32,n,n,k+32,n+32});
        }
        var mesh=new Mesh{name=name};mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
        string path="Assets/Materials/IntactFoyer/"+name.Replace(" ","")+".asset";
        var saved=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(saved){saved.Clear();saved.vertices=mesh.vertices;saved.triangles=mesh.triangles;saved.RecalculateNormals();saved.RecalculateBounds();saved.UploadMeshData(false);EditorUtility.SetDirty(saved);Object.DestroyImmediate(mesh);mesh=saved;}else AssetDatabase.CreateAsset(mesh,path);
        material.SetFloat("_DoubleSidedEnable",1);HDMaterial.ValidateMaterial(material);EditorUtility.SetDirty(material);
        var go=Child(parent,name);go.transform.position=position;go.AddComponent<MeshFilter>().sharedMesh=mesh;
        var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterial=material;renderer.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;
    }
}
