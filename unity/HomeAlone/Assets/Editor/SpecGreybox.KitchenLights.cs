using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// The kitchen's wall sconces (gallery pair + the one by the back stair) and the picture gallery with its desk
// (tools/house/hifi_kitchen_lights.py -> KitchenSconces.glb, tools/house/hifi_kitchen_gallery.py -> KitchenGallery.glb;
// spec/dressing/kitchen.json "sconces", "gallery", "desk"). The sconces go under KitchenFixtures, so Daylight() puts their lights on
// the night layer and their shades in the night glow list (off by day: DEVIATIONS 44). Called after KitchenModel.
public static partial class SpecGreybox
{
    static void KitchenSconcesAndGallery(GameObject root, float gy)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/kitchen.json"));
        if (!File.Exists(fp)) return;
        var k = JObject.Parse(File.ReadAllText(fp)); var sc = k["sconces"];
        var fx = root.transform.Find("KitchenFixtures")?.gameObject ?? Child(root, "KitchenFixtures");
        var shade = Mat("HiFi_Shade", new Color(0.95f, 0.92f, 0.86f)); shade.SetFloat("_Smoothness", 0.8f);
        shade.SetColor("_EmissiveColor", new Color(1f, 0.8f, 0.55f) * 300f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(shade);
        if (sc != null)
        {
            var g = PlaceHiFi(root, gy, "KitchenSconces", new Dictionary<string, Material> { ["Light_Brass"] = BrassMat(), ["Light_Shade"] = shade });
            if (g != null)
            {
                g.transform.SetParent(fx.transform, true);
                foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) { r.shadowCastingMode = ShadowCastingMode.Off; r.gameObject.isStatic = true; }
                float reach = (float)sc["reach"];
                foreach (var s in sc["list"])
                {
                    bool wx = (string)s["wall"] == "x"; float at = (float)s["at"], along = (float)s["along"], h = (float)s["h"], o = (float)s["out"];
                    float x = wx ? at + o * reach : along, z = wx ? along : at + o * reach;
                    var l = new GameObject("KitchenSconce_" + (string)s["name"] + "_Light").AddComponent<Light>(); l.transform.SetParent(g.transform, false);
                    l.transform.position = new Vector3(x, gy + h + 0.11f + 0.07f, -z); l.type = LightType.Point; l.range = 6f;
                    l.gameObject.AddComponent<HDAdditionalLightData>();
                    l.lightUnit = LightUnit.Lumen; l.intensity = (float)sc["lumens"]; l.useColorTemperature = true; l.colorTemperature = (float)sc["kelvin"]; l.shadows = LightShadows.Soft;
                }
            }
        }
        if (k["gallery"] == null) return;
        var remap = new Dictionary<string, Material> { ["KG_Brass"] = BrassMat(), ["KG_Wood"] = TexMat("HiFi_DeskOak", "oak_veneer_01", new Color(0.8f, 0.7f, 0.6f), 1.0f, 0.5f) };
        var frame = Mat("HiFi_PictureFrame", new Color(0.25f, 0.14f, 0.07f)); frame.SetFloat("_Smoothness", 0.5f); remap["KG_Frame"] = frame;
        foreach (var f in k["gallery"]["frames"])
        {
            string n = (string)f["name"], png = $"Assets/Textures/Kitchen/gallery_{n}.png";
            var m = Mat("HiFi_Picture_" + n, Color.white); m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(png)); m.SetFloat("_Smoothness", 0.3f);
            m.SetFloat("_UVBase", 0f); HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m); remap["KG_" + n] = m;
        }
        var gal = PlaceHiFi(root, gy, "KitchenGallery", remap);
        if (gal != null) foreach (var r in gal.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        AssetDatabase.SaveAssets();
    }
}
