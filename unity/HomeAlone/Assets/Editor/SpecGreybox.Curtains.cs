using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// Window treatments (tools/house/hifi_sheers.py -> Sheers.glb; DEVIATIONS 41). Cloth is HDRP Lit "Translucent" with a thin-object
// diffusion profile (Assets/Textures/Sheers/SheerDiffusionProfile.asset), so light from behind a panel comes through it
// (the sun, the lamps at night, and baked light sampled on the back side). The sheers are also alpha-blended with the generated
// voile texture (alpha = the weave's cover), double sided, rendered back faces first (self-sorting of the folds), cast no shadow and
// stay out of the bake (BakeLighting drops transparent renderers from GI). The drapes and valance are opaque, static, and shadow.
// HDRP only shades a diffusion profile listed in an active volume's Diffusion Profile List: it is added to the house's global volume.
public static partial class SpecGreybox
{
    const string SheerDir = "Assets/Textures/Sheers";

    static void Curtains(GameObject root, float gy)
    {
        var prof = AssetDatabase.LoadAssetAtPath<DiffusionProfileSettings>(SheerDir + "/SheerDiffusionProfile.asset");
        var gv = root.transform.Find("GlobalVolume")?.GetComponent<Volume>();
        if (prof == null || gv == null) { Debug.LogWarning($"Curtains: profile {prof != null}, global volume {gv != null}"); return; }
        var list = gv.sharedProfile.Add<DiffusionProfileList>(true); list.diffusionProfiles.value = new[] { prof };
        AssetDatabase.AddObjectToAsset(list, gv.sharedProfile); EditorUtility.SetDirty(gv.sharedProfile);

        string tp = SheerDir + "/voile.png";
        if (AssetImporter.GetAtPath(tp) is TextureImporter ti && (!ti.alphaIsTransparency || ti.anisoLevel != 8))
        { ti.alphaIsTransparency = true; ti.anisoLevel = 8; ti.wrapMode = TextureWrapMode.Repeat; ti.mipmapEnabled = true; ti.SaveAndReimport(); }
        var voileTex = AssetDatabase.LoadAssetAtPath<Texture2D>(tp);

        Material Cloth(string n, Color c, bool sheer, float thickness, Texture2D map, float smooth = 0.12f)
        {
            var m = Mat(n, c);
            m.SetFloat("_Smoothness", smooth);
            m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_DoubleSidedNormalMode", 0f);   // flip: the back face is lit as its own side
            m.SetFloat("_SurfaceType", sheer ? 1f : 0f);
            if (sheer) { m.SetFloat("_BlendMode", 0f); m.SetFloat("_TransparentBackfaceEnable", 1f); m.SetFloat("_ReceivesSSRTransparent", 0f); }
            m.SetTexture("_BaseColorMap", map);
            m.SetFloat("_MaterialID", (float)MaterialId.LitTranslucent); m.SetFloat("_Thickness", thickness);   // x the profile's 0-1 mm remap
            HDMaterial.SetDiffusionProfile(m, prof);
            HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m);
            return m;
        }
        var voile = Cloth("HiFi_Voile", new Color(0.96f, 0.95f, 0.92f, 1f), true, 0.15f, voileTex);
        var hem = Cloth("HiFi_VoileHem", new Color(0.96f, 0.95f, 0.92f, 0.93f), true, 0.3f, null);   // the doubled hem and heading
        var ivory = Cloth("HiFi_DrapeIvory", new Color(0.80f, 0.76f, 0.64f), false, 0.8f, null);  // Marina 1124-1128: cream drapes
        var red = Cloth("HiFi_DrapeRed", new Color(0.50f, 0.02f, 0.035f), false, 0.5f, null, 0.45f);   // film 6902/6910: glossy red chintz
        var g = PlaceHiFi(root, gy, "Sheers", new Dictionary<string, Material> { ["SH_Hem"] = hem, ["SH_Voile"] = voile, ["SH_DrapeIvory"] = ivory, ["SH_Red"] = red });
        if (g == null) return;
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            bool clear = r.sharedMaterial == voile || r.sharedMaterial == hem;
            r.shadowCastingMode = clear ? ShadowCastingMode.Off : ShadowCastingMode.On;
            r.gameObject.isStatic = !clear;
        }
    }
}
