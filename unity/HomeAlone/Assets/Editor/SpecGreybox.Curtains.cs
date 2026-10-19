using System.IO;
using Newtonsoft.Json.Linq;
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
        // Buzz's room (tools/house/hifi_buzz_curtains.py; Buzz TRIAL 2): the film's grey pleated panels over a white sheer on a brass rod,
        // modelled above the UPPER floor (placed at 0, not gy)
        var grey = Cloth("HiFi_DrapeGrey", new Color(0.35f, 0.355f, 0.35f), false, 0.8f, null);   // film 530: neutral grey (linear ~0.10)
        var bz = PlaceHiFi(root, 0f, "BuzzCurtains", new Dictionary<string, Material> { ["SH_Hem"] = hem, ["SH_Voile"] = voile, ["BZ_Drape"] = grey, ["BZ_Brass"] = BrassMat() });
        // the parents' bedroom (tools/house/hifi_parents_dressing.py; TRIAL 1, Oct 18): film 2648's slate damask panels and swag valance over a lace sheer
        var damask = Cloth("HiFi_DrapeDamask", new Color(0.42f, 0.43f, 0.45f), false, 0.8f, null);   // film 2648 slate grey-blue; build 1 (0.55/0.58/0.64) read sky blue, build 2 (0.36/0.39/0.45) royal blue
        var pc = PlaceHiFi(root, 0f, "ParentsDressing", new Dictionary<string, Material> { ["SH_Hem"] = hem, ["SH_Voile"] = voile, ["PB_Damask"] = damask, ["PB_Brass"] = BrassMat(), ["PB_Screen"] = SpecTexMat("HiFi_ParentsScreen", "spec/dressing/parents_screen.png"), ["PB_Shade"] = Glow("HiFi_ShadeParentsBlack", new Color(0.03f, 0.03f, 0.03f), 0f, 0.6f), ["PB_ShadeIn"] = Glow("HiFi_ShadeParentsIn", new Color(0.92f, 0.72f, 0.45f), 700f, 0.3f), ["PB_Bulb"] = Glow("HiFi_BulbParents", new Color(1f, 0.92f, 0.80f), 4000f, 0.5f) });
        // the bedside lamps' light (user walk note Oct 18 20:44): a warm point light in each shade (the black shell blocks it but its open top and bottom, so
        // it throws up and down like the film's), off by day (Daylight() moves it into the night layer via Upstairs/ParentsFixtures)
        var pfx = Child(root, "ParentsFixtures");
        var pj = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/parents.json"));
        if (File.Exists(pj))
            foreach (var bx in JObject.Parse(File.ReadAllText(pj))["boxes"])
                if (((string)bx["name"]).StartsWith("parents_nightstand"))
                    AddLamp(pfx, "ParentsLamp_" + ((string)bx["name"]).Substring(19), new Vector3(((float)bx["x"][0] + (float)bx["x"][1]) / 2, (float)bx["y"][1] + 0.48f, ((float)bx["z"][0] + (float)bx["z"][1]) / 2), 0f, 450f, 2700f);
        foreach (var gg in new[] { g, bz, pc })
            if (gg != null)
                foreach (var r in gg.GetComponentsInChildren<MeshRenderer>())
                {
                    string pmn = r.sharedMaterial != null ? r.sharedMaterial.name : "";
                    bool clear = r.sharedMaterial == voile || r.sharedMaterial == hem || pmn == "HiFi_ShadeParentsIn" || pmn == "HiFi_BulbParents";   // the lamp's liner and bulb sit round its light
                    r.shadowCastingMode = clear ? ShadowCastingMode.Off : ShadowCastingMode.On;
                    r.gameObject.isStatic = !clear;
                }
    }

    static Material Glow(string n, Color c, float nits, float smooth)
    {   // a lamp shade or bulb: its own light at night (HouseNightMode darkens "HiFi_Shade*"/"HiFi_Bulb*" by day)
        var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetColor("_EmissiveColor", c * nits);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); return m;
    }
}
