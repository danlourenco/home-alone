using System.IO;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// The film's vehicles as prefabs for the neighbourhood's swap hook (Oct 20 2026): Assets/Purchased/Vehicles/<kind>.prefab replaces the
// nb_life proxy of that kind. Contract: root at the ground contact, facing Unity +z, metres. The GLBs (CC-BY, CREDITS.md; gitignored,
// a clone without them makes nothing) come from tools/house/purchased_vehicles.py; spec/vehicles.json carries every number here:
// the HDRP Lit settings per VEH_* material (clear-coat paint, chrome, transparent glass, emissive lamps), the LOD screen heights and
// the box collider. Police: PoliceLights on the root (sweeping beacons, red + blue by default or all red as filmed, spec police_bar;
// two unshadowed wash lights; night-only by the hook). The van is night-only too (spec scene).
// Call VehiclePrefabs.Build() from the hook before instancing (cheap: rebuilt each build so spec edits land), or the menu item.
public static class VehiclePrefabs
{
    const string Dir = "Assets/Purchased/Vehicles";

    [MenuItem("HomeAlone/Vehicles/Build prefabs")]
    public static void Build()
    {
        var specPath = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/vehicles.json"));
        if (!File.Exists(specPath)) { Debug.LogWarning("VehiclePrefabs: spec/vehicles.json missing"); return; }
        var spec = JObject.Parse(File.ReadAllText(specPath));
        foreach (var kv in (JObject)spec["kinds"]) Make(kv.Key, (JObject)kv.Value, (JObject)spec["materials"]);
        AssetDatabase.SaveAssets();
    }

    static void Make(string kind, JObject k, JObject mats)
    {
        var glb = AssetDatabase.LoadAssetAtPath<GameObject>($"{Dir}/{kind}.glb");
        if (glb == null) { Debug.Log($"VehiclePrefabs: {kind}.glb not present (gitignored download), no prefab"); return; }
        var root = new GameObject(kind);
        var body = (GameObject)Object.Instantiate(glb, root.transform, false); body.name = kind + "_Model";
        var cache = new System.Collections.Generic.Dictionary<Material, Material>();
        Renderer[] Named(string suffix)
        {
            var list = new System.Collections.Generic.List<Renderer>();
            foreach (var r in body.GetComponentsInChildren<Renderer>(true)) if (r.name.EndsWith(suffix)) list.Add(r);
            return list.ToArray();
        }
        foreach (var r in body.GetComponentsInChildren<Renderer>(true))
        {
            var sm = r.sharedMaterials;
            for (int i = 0; i < sm.Length; i++) sm[i] = Hdrp(sm[i], mats, cache);
            r.sharedMaterials = sm;
        }
        // LODs: beacons ride with LOD0 and LOD1 (at LOD2 distance they are a few pixels; the wash lights still show)
        var beacons = new System.Collections.Generic.List<Renderer>();
        foreach (var r in body.GetComponentsInChildren<Renderer>(true)) if (r.name.StartsWith("Beacon_") || r.name.StartsWith("Flasher_")) beacons.Add(r);
        var lod = (JArray)k["lod_screen"];
        var l0 = new System.Collections.Generic.List<Renderer>(Named("_LOD0")); l0.AddRange(beacons);
        var l1 = new System.Collections.Generic.List<Renderer>(Named("_LOD1")); l1.AddRange(beacons);
        var lg = root.AddComponent<LODGroup>(); lg.fadeMode = LODFadeMode.CrossFade; lg.animateCrossFading = true;
        lg.SetLODs(new[] { new LOD((float)lod[0], l0.ToArray()), new LOD((float)lod[1], l1.ToArray()), new LOD((float)lod[2], Named("_LOD2")) });
        lg.RecalculateBounds();
        foreach (var r in Named("_LOD2")) r.shadowCastingMode = ShadowCastingMode.Off;   // a distant car's shadow: LOD1 ends where it matters
        // one box: the body (mirrors and roof load excluded), from the spec
        var bc = root.AddComponent<BoxCollider>(); var c = (JArray)k["collider"]["center"]; var s = (JArray)k["collider"]["size"];
        bc.center = new Vector3((float)c[0], (float)c[1], (float)c[2]); bc.size = new Vector3((float)s[0], (float)s[1], (float)s[2]);
        if ((bool?)k["police_lights"] == true)
            root.AddComponent<PoliceLights>().bar = (string)k["police_bar"] == "all_red" ? PoliceLights.Bar.AllRed : PoliceLights.Bar.RedBlue;
        var b = new Bounds(); bool any = false;
        foreach (var r in Named("_LOD0")) { if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
        Debug.Log($"VehiclePrefabs: {kind} bounds {b.min:F2} .. {b.max:F2} (nose +z, ground y 0)");
        PrefabUtility.SaveAsPrefabAsset(root, $"{Dir}/{kind}.prefab");
        Object.DestroyImmediate(root);
    }

    // a glTFast material -> a shared HDRP Lit (saved beside the GLBs, gitignored); unnamed/unknown materials keep a plain Lit copy
    static Material Hdrp(Material m, JObject mats, System.Collections.Generic.Dictionary<Material, Material> cache)
    {
        if (m == null) return null;
        if (cache.TryGetValue(m, out var done)) return done;
        string name = m.name.Split(' ')[0];
        string dir = Dir + "/Materials"; if (!AssetDatabase.IsValidFolder(dir)) AssetDatabase.CreateFolder(Dir, "Materials");
        string path = $"{dir}/{name}.mat";
        var n = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (n == null) { n = new Material(Shader.Find("HDRP/Lit")); AssetDatabase.CreateAsset(n, path); }
        else n.shader = Shader.Find("HDRP/Lit");
        var p = mats[name] as JObject ?? new JObject();
        Texture baseMap = m.HasProperty("baseColorTexture") ? m.GetTexture("baseColorTexture") : null;
        Color baseCol = m.HasProperty("baseColorFactor") ? m.GetColor("baseColorFactor") : Color.white;
        if (p["color"] is JArray col) baseCol = new Color((float)col[0], (float)col[1], (float)col[2], col.Count > 3 ? (float)col[3] : 1f);
        n.SetTexture("_BaseColorMap", baseMap); n.SetColor("_BaseColor", baseCol);
        n.SetFloat("_Metallic", (float?)p["metallic"] ?? 0f);
        n.SetFloat("_Smoothness", (float?)p["smooth"] ?? 0.5f);
        n.SetFloat("_CoatMask", (float?)p["coat"] ?? 0f);   // > 0 turns on HDRP Lit's clear coat (_MATERIAL_FEATURE_CLEAR_COAT)
        n.SetTexture("_MaskMap", null);
        if (p["mask"] != null)
        {   // R metallic, G AO, B 0, A smoothness (grime is rougher), linear
            string mp = $"{Dir}/{(string)p["mask"]}";
            if (AssetImporter.GetAtPath(mp) is TextureImporter ti && ti.sRGBTexture) { ti.sRGBTexture = false; ti.SaveAndReimport(); }
            var mt = AssetDatabase.LoadAssetAtPath<Texture2D>(mp);
            if (mt != null) { n.SetTexture("_MaskMap", mt); n.SetFloat("_SmoothnessRemapMin", 0f); n.SetFloat("_SmoothnessRemapMax", 1f); n.SetFloat("_MetallicRemapMax", (float?)p["metallic"] ?? 0f); }
        }
        float nits = (float?)p["emissive_nits"] ?? 0f;
        n.SetTexture("_EmissiveColorMap", nits > 0f && (string)p["emissive_map"] == "base" ? baseMap : null);
        var ec = p["emissive_color"] is JArray e ? new Color((float)e[0], (float)e[1], (float)e[2]) : Color.white;
        n.SetFloat("_UseEmissiveIntensity", 0f); n.SetColor("_EmissiveColor", ec * nits);
        bool glass = (bool?)p["transparent"] == true;
        n.SetFloat("_SurfaceType", glass ? 1f : 0f); n.SetFloat("_BlendMode", 0f); n.SetFloat("_EnableFogOnTransparent", 1f);
        n.SetFloat("_DoubleSidedEnable", 0f);
        n.enableInstancing = true;
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(n);
        EditorUtility.SetDirty(n);
        return cache[m] = n;
    }
}
