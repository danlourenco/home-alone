using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// Buzz's hero props (props lane, Oct 17 overnight, not walked): the generated/Poly Haven pieces (tools/house/hifi_buzz_props.py ->
// BuzzProps.glb: the Jordan poster, the Bulls wastebasket, the terrarium, desk and shelf pieces, the footlocker's contents), the owned
// Tarantula pack's spider in the terrarium (TankTarantula.cs walks it) and the Fadnn bat leaning by the shelves. The typewriter and
// books are store_props.json pieces. Packs are gitignored: a missing one is skipped.
public static partial class SpecGreybox
{
    const string TarantulaPrefab = "Assets/Tarantula/Prefabs/Tarantula.prefab";
    const string BatPrefab = "Assets/Fadnn - Vintage Interior Furniture Pack/Props/Prefabs/HDRP/SM_BaseballBat_01.prefab";

    static void BuzzProps(GameObject root)
    {
        // the modelled terrarium replaces the opaque buzz_tank box (its walk collider, a separate object, stays)
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>().Where(r => r.name == "buzz_tank")) r.enabled = false;
        var g = PlaceHiFi(root, 0f, "BuzzProps", new Dictionary<string, Material> { ["BZP_Glass"] = mGlass, ["BZP_Brass"] = BrassMat() });
        if (g != null)
            foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) { r.shadowCastingMode = ShadowCastingMode.On; r.gameObject.isStatic = true; }
        BuzzTarantula(root);
        BuzzBat(root);
    }

    static GameObject PackInstance(GameObject root, string path, string name)
    {
        var pf = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (pf == null) { Debug.Log($"BuzzProps: {path} not present, no {name}"); return null; }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(pf, root.transform);
        PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
        go.name = name;
        foreach (var c in go.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        foreach (var mb in go.GetComponentsInChildren<MonoBehaviour>()) Object.DestroyImmediate(mb);   // the pack's keyboard demo script
        return go;
    }

    static Bounds RendererBounds(GameObject go)
    {
        var rs = go.GetComponentsInChildren<Renderer>();
        return rs.Aggregate(rs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
    }

    // a tarantula at real size (~0.14 m leg span) on the terrarium's soil, materials on HDRP/Lit (the fur shell transparent: its
    // alpha is soft, median 25/255, so a clip would erase it)
    static void BuzzTarantula(GameObject root)
    {
        var go = PackInstance(root, TarantulaPrefab, "BuzzTarantula");
        if (go == null) return;
        foreach (var r in go.GetComponentsInChildren<Renderer>())
        {
            r.sharedMaterials = r.sharedMaterials.Select(m => m != null && m.name.Contains("Fur") ? FurMat(m) : HdrpOrConvert(m)).ToArray();
            r.shadowCastingMode = ShadowCastingMode.On;
        }
        foreach (var sk in go.GetComponentsInChildren<SkinnedMeshRenderer>()) sk.updateWhenOffscreen = true;
        var anim = go.GetComponentInChildren<Animator>(); anim.applyRootMotion = false;
        go.transform.localScale = Vector3.one;
        var b = RendererBounds(go); float span = Mathf.Max(b.size.x, b.size.z);
        go.transform.localScale = Vector3.one * (0.14f / span);
        const float soil = 1.004f + 0.02f + 0.04f;   // buzz_tank y0 + base + soil (hifi_buzz_props.py)
        // the pivot is the clips' ground (the bind-pose mesh stands 0.21 m above it, for the "drop" clip: bounds put it under the shelf, build 1)
        go.transform.localPosition = new Vector3(7.633f, soil, -14.967f); go.transform.localRotation = Quaternion.Euler(0, 200, 0);
        var walk = go.AddComponent<TankTarantula>();
        walk.lo = new Vector3(7.603f, 0, -15.082f); walk.hi = new Vector3(7.663f, 0, -14.852f);   // inside the glass, less ~0.08 for the legs
        Debug.Log($"BuzzProps: tarantula span {span:F3} native -> scale {go.transform.localScale.x:F4}, at {go.transform.position}");
    }

    static Material FurMat(Material m)
    {
        string src = AssetDatabase.GetAssetPath(m), dst = System.IO.Path.ChangeExtension(src, null) + "_HDRP.mat";
        AssetDatabase.DeleteAsset(dst);
        var n = new Material(Shader.Find("HDRP/Lit")) { name = m.name + "_HDRP" };
        n.SetTexture("_BaseColorMap", m.GetTexture("_MainTex"));
        if (m.HasProperty("_BumpMap") && m.GetTexture("_BumpMap") != null) n.SetTexture("_NormalMap", m.GetTexture("_BumpMap"));
        n.SetFloat("_Smoothness", 0.2f);
        n.SetFloat("_SurfaceType", 1f); n.SetFloat("_BlendMode", 0f);   // transparent, alpha blend
        n.SetFloat("_DoubleSidedEnable", 1f); n.SetFloat("_CullMode", 0f);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(n);
        if (src.StartsWith("Assets/")) AssetDatabase.CreateAsset(n, dst);
        return n;
    }

    // the Fadnn bat leaning on the shelves wall (face x 7.473) past the shelves' desk end (z 15.192), barrel down, foot 0.18 m out
    // (Marina 531-535 s: a bat leaning there; film 478: bats by the shelves under the poster)
    static void BuzzBat(GameObject root)
    {
        var go = PackInstance(root, BatPrefab, "buzz_bat");
        if (go == null) return;
        go.transform.localPosition = Vector3.zero; go.transform.localRotation = Quaternion.identity; go.transform.localScale = Vector3.one;
        var b = RendererBounds(go);
        if (b.size.x > b.size.y && b.size.x > b.size.z) go.transform.localRotation = Quaternion.Euler(0, 0, 90);        // long axis upright
        else if (b.size.z > b.size.y) go.transform.localRotation = Quaternion.Euler(90, 0, 0);
        // the barrel (the thicker end) down: mean distance from the axis of the top and bottom fifths of the vertices
        var v = go.GetComponentsInChildren<MeshFilter>().SelectMany(m => m.sharedMesh.vertices.Select(m.transform.TransformPoint)).ToArray();
        b = RendererBounds(go);
        float Thick(System.Func<Vector3, bool> sel) => v.Where(sel).Select(p => new Vector2(p.x - b.center.x, p.z - b.center.z).magnitude).DefaultIfEmpty(0).Average();
        if (Thick(p => p.y > b.max.y - b.size.y * 0.2f) > Thick(p => p.y < b.min.y + b.size.y * 0.2f)) go.transform.localRotation = Quaternion.Euler(180, 0, 0) * go.transform.localRotation;
        float lean = Mathf.Asin(0.18f / b.size.y) * Mathf.Rad2Deg;
        var up = go.transform.localRotation;
        go.transform.localRotation = Quaternion.Euler(0, 0, lean) * up;
        b = RendererBounds(go); var top = b.max.y; var tops = go.GetComponentsInChildren<MeshFilter>().SelectMany(m => m.sharedMesh.vertices.Select(m.transform.TransformPoint)).Where(p => p.y > top - 0.05f);
        if (tops.Average(p => p.x) > b.center.x) go.transform.localRotation = Quaternion.Euler(0, 0, -lean) * up;   // the top must lean toward the wall (-x)
        b = RendererBounds(go);
        go.transform.localPosition += new Vector3(7.473f + 0.004f - b.min.x, 0f - b.min.y, -15.45f - b.center.z);
        foreach (var r in go.GetComponentsInChildren<Renderer>()) { r.sharedMaterials = r.sharedMaterials.Select(HdrpOrConvert).ToArray(); r.gameObject.isStatic = true; }
        b = RendererBounds(go); Debug.Log($"BuzzProps: bat {b.min} .. {b.max}");
    }
}
