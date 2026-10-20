using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// The living room (Oct 16 2026, TRIAL; changes/2026-10-16-living-room.json, DEVIATIONS 57-60). The film's paper comes from
// spec/dressing/finishes.json ("paper", PaperMat below) over a 0.14 m baseboard, the dark wood floor likewise. Here: the windows with
// their damask drapes, sheers and valances (tools/house/hifi_living.py -> LivingWindows.glb; the grey-box keeps the casing and hides
// its glass box), the fireplace, piano, lamps, tree and small dressing (LivingBuiltins.glb), the Poly Haven pieces
// (tools/house/hifi_living_props.py -> LivingProps.glb), the lamps' lights and the walk colliders (spec/dressing/living.json).
// The corner chest is an owned pack piece (StoreProps, spec/dressing/store_props.json).
public static partial class SpecGreybox
{
    // a papered room's wall finish (spec/dressing/finishes.json "paper": a repo PNG with its .json "repeat_m"), world-space triplanar
    // at the repeat's own width and height (as KitchenPaper)
    static Material PaperMat(string name, string specPng, Color fallback)
    {
        var m = Mat(name, fallback);
        string src = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../" + specPng));
        if (!File.Exists(src)) return m;
        var rep = JObject.Parse(File.ReadAllText(Path.ChangeExtension(src, ".json")))["repeat_m"];
        Directory.CreateDirectory("Assets/Textures/Greybox"); string dst = "Assets/Textures/Greybox/" + Path.GetFileName(specPng);
        if (!File.Exists(dst) || !File.ReadAllBytes(dst).SequenceEqual(File.ReadAllBytes(src))) { File.Copy(src, dst, true); AssetDatabase.ImportAsset(dst); }
        m.SetColor("_BaseColor", Color.white); m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dst));
        m.SetFloat("_UVBase", 5f); m.SetFloat("_TexWorldScale", 1f); m.SetFloat("_Smoothness", 0.15f);
        m.SetTextureScale("_BaseColorMap", new Vector2(1f / (float)rep[0], 1f / (float)rep[1]));
        HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m); AssetDatabase.SaveAssetIfDirty(m);
        return m;
    }

    static Texture2D LivingTex(string file, bool alpha)
    {
        string p = "Assets/Textures/Living/" + file;
        if (AssetImporter.GetAtPath(p) is TextureImporter ti && (ti.alphaIsTransparency != alpha || ti.anisoLevel != 8))
        { ti.alphaIsTransparency = alpha; ti.anisoLevel = 8; ti.wrapMode = alpha ? TextureWrapMode.Clamp : TextureWrapMode.Repeat; ti.mipmapEnabled = true; ti.SaveAndReimport(); }
        return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
    }

    static void Living(GameObject root, float gy)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/living.json"));
        if (!File.Exists(fp)) return;
        var L = JObject.Parse(File.ReadAllText(fp));
        // cloth: the sheer pass's materials (SpecGreybox.Curtains: voile, hem) and a damask drape, HDRP Lit Translucent like its drapes
        var prof = AssetDatabase.LoadAssetAtPath<DiffusionProfileSettings>(SheerDir + "/SheerDiffusionProfile.asset");
        var damask = Mat("HiFi_LivingDamask", Color.white);
        damask.SetTexture("_BaseColorMap", LivingTex("damask.png", false));
        damask.SetTextureScale("_BaseColorMap", new Vector2(0.5f, 1f / 3f));   // hifi_sheers UVs: 0.20 m of fabric per unit; the repeat is 0.40 x 0.60 m
        damask.SetFloat("_Smoothness", 0.45f); damask.SetFloat("_DoubleSidedEnable", 1f); damask.SetFloat("_DoubleSidedNormalMode", 0f);
        if (prof != null) { damask.SetFloat("_MaterialID", (float)MaterialId.LitTranslucent); damask.SetFloat("_Thickness", 0.9f); HDMaterial.SetDiffusionProfile(damask, prof); }
        HDMaterial.ValidateMaterial(damask); EditorUtility.SetDirty(damask);
        var tie = Mat("HiFi_LivingTie", new Color(0.06f, 0.18f, 0.08f)); tie.SetFloat("_Smoothness", 0.5f);
        var voile = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Greybox/HiFi_Voile.mat");
        var hem = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Greybox/HiFi_VoileHem.mat");
        var remapW = new Dictionary<string, Material> { ["LV_Glass"] = mGlass, ["LV_Brass"] = BrassMat(), ["LV_Damask"] = damask, ["LV_Tie"] = tie };
        if (voile != null) remapW["SH_Voile"] = voile;
        if (hem != null) remapW["SH_Hem"] = hem;
        var w = PlaceHiFi(root, gy, "LivingWindows", remapW);
        if (w != null)
            foreach (var r in w.GetComponentsInChildren<MeshRenderer>())
            {
                bool clear = r.sharedMaterial == voile || r.sharedMaterial == hem;
                r.shadowCastingMode = clear ? ShadowCastingMode.Off : ShadowCastingMode.On; r.gameObject.isStatic = !clear;
            }

        Material Glow(string n, Color c, float nits, float smooth)
        {   // a lamp shade or bulb: its own light at night (HouseNightMode darkens "HiFi_Shade*"/"HiFi_Bulb*" by day)
            var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetColor("_EmissiveColor", c * nits);
            UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); return m;
        }
        Material Solid(string n, Color c, float smooth, float metal = 0f) { var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", metal); return m; }
        Material TwoSided(Material m) { m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_CullMode", 0f); HDMaterial.ValidateMaterial(m); return m; }
        var needles = Mat("HiFi_LivingNeedles", Color.white);
        needles.SetTexture("_BaseColorMap", LivingTex("needles.png", true));
        needles.SetFloat("_AlphaCutoffEnable", 1f); needles.SetFloat("_AlphaCutoff", 0.5f); needles.SetFloat("_Smoothness", 0.25f);
        TwoSided(needles); EditorUtility.SetDirty(needles);
        var rug = Mat("HiFi_LivingRug", Color.white); rug.SetTexture("_BaseColorMap", LivingTex("rug.png", false)); rug.SetFloat("_Smoothness", 0.05f);
        HDMaterial.ValidateMaterial(rug);
        var screen = Mat("HiFi_LivingScreenMesh", new Color(0.03f, 0.03f, 0.03f, 0.55f)); screen.SetFloat("_SurfaceType", 1f); TwoSided(screen);
        var remapB = new Dictionary<string, Material> {
            ["LV_Brass"] = BrassMat(), ["LV_Gilt"] = BrassMat(), ["LV_Gold"] = FoilMat(), ["LV_OrnGold"] = FoilMat(),
            ["LV_Mahogany"] = TexMat("HiFi_LivingMahogany", "cherry_veneer", new Color(0.30f, 0.15f, 0.17f), 1.0f, 0.6f),   // film 5650's dark glossy mahogany
            ["LV_Paint"] = Solid("HiFi_LivingWhite", new Color(0.88f, 0.87f, 0.83f), 0.4f),
            ["LV_KeysWhite"] = Solid("HiFi_PianoKeys", new Color(0.90f, 0.88f, 0.82f), 0.7f),
            ["LV_Needles"] = needles, ["LV_Rug"] = rug, ["LV_ScreenMesh"] = screen,
            ["LV_Leaf"] = TwoSided(Mat("HiFi_LivingLeaf", new Color(0.06f, 0.20f, 0.06f))), ["LV_Porcelain"] = TwoSided(Solid("HiFi_Porcelain", new Color(0.92f, 0.91f, 0.88f), 0.75f)),
            ["LV_Tinsel"] = Solid("HiFi_Tinsel", new Color(0.8f, 0.8f, 0.82f), 0.85f, 0.9f), ["LV_OrnSilver"] = Solid("HiFi_OrnSilver", new Color(0.75f, 0.75f, 0.78f), 0.9f, 0.9f),
            ["LV_OrnRed"] = Solid("HiFi_OrnRed", new Color(0.6f, 0.03f, 0.04f), 0.85f, 0.4f), ["LV_OrnBlue"] = Solid("HiFi_OrnBlue", new Color(0.05f, 0.1f, 0.5f), 0.85f, 0.4f),
            ["LV_ShadeBurgundy"] = Glow("HiFi_ShadeLivingBurgundy", new Color(0.35f, 0.04f, 0.06f), 150f, 0.3f),   // film 10636 (500 read pink at night)
            ["LV_ShadeBlack"] = Glow("HiFi_ShadeLivingBlack", new Color(0.02f, 0.02f, 0.02f), 0f, 0.5f),         // opaque: lights only below and above
            ["LV_ShadeBrass"] = BrassMat(),
            ["LV_Bulb"] = Glow("HiFi_BulbLiving", new Color(1f, 0.92f, 0.80f), 4000f, 0.5f) };
        foreach (var (c, rgb) in new[] { ("Red", new Color(0.9f, 0.05f, 0.05f)), ("Green", new Color(0.05f, 0.8f, 0.1f)), ("Blue", new Color(0.1f, 0.2f, 0.95f)),
                                         ("Orange", new Color(1f, 0.45f, 0.05f)), ("Pink", new Color(0.95f, 0.2f, 0.6f)), ("White", new Color(1f, 0.92f, 0.8f)) })
            remapB["LV_C7" + c] = Glow("HiFi_BulbC7" + c, rgb, 3000f, 0.6f);   // C7 bulbs (film 10600): lit at night only, like every lamp
        var b = PlaceHiFi(root, gy, "LivingBuiltins", remapB);
        if (b != null)
            foreach (var r in b.GetComponentsInChildren<MeshRenderer>())
            {
                string mn = r.sharedMaterial != null ? r.sharedMaterial.name : "";
                if (mn.StartsWith("HiFi_Bulb") || mn == "HiFi_ShadeLivingBurgundy" || mn == "HiFi_ShadeLivingBlack" || mn == "HiFi_LivingScreenMesh") r.shadowCastingMode = ShadowCastingMode.Off;
                r.gameObject.isStatic = true;
            }
        var p = PlaceHiFi(root, gy, "LivingProps", null);
        if (p != null) foreach (var r in p.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;

        // the lamps as lights from their fixtures (living.json lamps), Mixed by BakeLighting (Night scenario); Daylight() moves them into the
        // night layer (off by day) and removes Light_living_room
        var g = Child(root, "LivingFixtures");
        foreach (var kv in (JObject)L["lamps"])
        {
            var q = kv.Value; float x = (float)q["at"][0], y = (float)q["at"][1], z = (float)q["at"][2]; string kind = (string)q["kind"];
            Vector3 at = kind == "banker" ? new Vector3(x, y + 0.26f, z) : kind == "piano" ? new Vector3(x, y + 0.20f, z - 0.15f)
                       : new Vector3(x, y + ((float)q["shade"][2] + (float)q["shade"][3]) / 2f - 0.03f, z);
            AddLamp(g, "LivingLamp_" + kv.Key, at, gy, (float)q["lumens"] * LivingLampScale, (float)q["kelvin"]);
        }
        var t = L["tree"]; float tx = (float)t["at"][0], tz = (float)t["at"][1], tr = (float)t["r"];
        foreach (float h in new[] { 0.8f, 1.5f })   // the tree's lights: two warm points just in front of it (its C7 bulbs glow; HDRP has no area emission here)
        {
            AddLamp(g, "LivingTreeGlow_" + h, new Vector3(tx + tr * 0.9f, h, tz - tr * 0.5f), gy, 120f * LivingLampScale, 2400f);
            g.transform.Find("LivingTreeGlow_" + h).GetComponent<Light>().shadows = LightShadows.None;   // it stands among the needles: unshadowed (the shadow pass, Oct 17)
        }

        var col = Child(root, "LivingColliders"); int n = 0;
        foreach (var c in L["colliders"])
        {
            float x0 = (float)c["x"][0], x1 = (float)c["x"][1], z0 = (float)c["z"][0], z1 = (float)c["z"][1], y0 = (float)c["y"][0], y1 = (float)c["y"][1];
            var o = new GameObject("LivingCollider_" + (string)c["name"]); o.transform.SetParent(col.transform, false); o.isStatic = true;
            o.transform.position = new Vector3((x0 + x1) / 2, gy + (y0 + y1) / 2, -(z0 + z1) / 2);
            o.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, y1 - y0, z1 - z0); n++;
        }
        Debug.Log($"Living: {n} colliders");
    }

    public static float LivingLampScale = 1f;   // calibration knob against the film's night frames (film_light_match.py --living-night)
    static void AddLamp(GameObject parent, string name, Vector3 specAt, float gy, float lumens, float kelvin, float range = 7f)
    {
        var l = new GameObject(name).AddComponent<Light>(); l.transform.SetParent(parent.transform, false);
        l.transform.position = new Vector3(specAt.x, gy + specAt.y, -specAt.z); l.type = LightType.Point; l.range = range;
        l.gameObject.AddComponent<HDAdditionalLightData>();   // first: adding it resets the light's intensity
        l.lightUnit = LightUnit.Lumen; l.intensity = lumens; l.useColorTemperature = true; l.colorTemperature = kelvin;
        l.shadows = LightShadows.Soft;
    }
}
