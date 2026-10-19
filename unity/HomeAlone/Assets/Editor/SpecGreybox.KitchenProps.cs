using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// The kitchen's pot rack and pans, bar stools and counter dressing (tools/house/hifi_kitchen_props.py -> KitchenProps.glb, spec
// coordinates above the ground floor; spec/dressing/kitchen.json "wares"; Oct 19 kitchen fidelity). Each KP_* material becomes an
// HDRP Lit material with the GLB's own colour, metallic and roughness; enamel and glazed ceramic get a clear coat (the film's red
// pans and kettle read glossy), glass is the house glass. The stools' walk colliders are kitchen.json "colliders" (stool_*).
public static partial class SpecGreybox
{
    static void KitchenProps(GameObject root, float gy)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/KitchenProps.glb");
        if (a == null) { Debug.LogWarning("KitchenProps: missing KitchenProps.glb"); return; }
        var remap = new Dictionary<string, Material>();
        foreach (var m in AssetDatabase.LoadAllAssetsAtPath("Assets/Models/Foyer/KitchenProps.glb").OfType<Material>().Where(m => m.name.StartsWith("KP_")))
        {
            if (m.name == "KP_Glass") { remap[m.name] = mGlass; continue; }
            var c = m.HasProperty("baseColorFactor") ? m.GetColor("baseColorFactor") : Color.grey;
            var n = Mat("HiFi_" + m.name, c);
            n.SetFloat("_Metallic", m.HasProperty("metallicFactor") ? m.GetFloat("metallicFactor") : 0f);
            n.SetFloat("_Smoothness", 1f - (m.HasProperty("roughnessFactor") ? m.GetFloat("roughnessFactor") : 0.5f));
            if (m.name == "KP_RedEnamel" || m.name == "KP_Ceramic") { n.SetFloat("_MaterialID", 1f); n.SetFloat("_CoatMask", 1f); }
            if (m.name == "KP_Pine") n = KnottyPine();
            if (m.name.StartsWith("KP_Fridge"))   // the fridge door's papers (hifi_kitchen_gallery.py fridge_<i>.png; Oct 19 props-quality)
            {
                n.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>($"Assets/Textures/Kitchen/fridge_{m.name.Substring(9)}.png"));
                n.SetColor("_BaseColor", Color.white); n.SetFloat("_UVBase", 0f);
            }
            UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(n); EditorUtility.SetDirty(n);
            remap[m.name] = n;
        }
        var g = PlaceHiFi(root, gy, "KitchenProps", null);   // one mesh per object with several materials: remapped slot by slot here
        if (g == null) return;
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            r.sharedMaterials = r.sharedMaterials.Select(m => m != null && remap.TryGetValue(m.name.Replace(" (Instance)", ""), out var n) ? n : m).ToArray();
            r.gameObject.isStatic = true; r.shadowCastingMode = ShadowCastingMode.On;
        }
        Debug.Log($"KitchenProps: {g.GetComponentsInChildren<MeshRenderer>().Length} parts, {remap.Count} materials");
    }
}
