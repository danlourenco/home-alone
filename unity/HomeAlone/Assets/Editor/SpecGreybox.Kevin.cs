using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json.Linq;
using UnityEngine.Rendering.HighDefinition;
using UnityEngine;
using UnityEngine.Rendering;

// Kevin and Jeff's room (TRIAL 1, Oct 18; changes/2026-10-18-kevin-room.json): the generated bunk beds, curtains, wall pieces and props
// (tools/house/hifi_kevin.py -> Models/Foyer/KevinRoom.glb, spec coordinates above the upper floor), the bunk's walk box, and the
// film's two night lamps (spec/dressing/kevin.json lamps; Daylight() moves them into the night layer). Pack furniture: store_props kevin_*.
public static partial class SpecGreybox
{
    static void Kevin(GameObject root)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/kevin.json"));
        if (!File.Exists(fp)) return;
        var K = JObject.Parse(File.ReadAllText(fp));
        var gingham = PaperMat("HiFi_KevinGingham", "spec/dressing/kevin_gingham.png", new Color(0.6f, 0.73f, 0.58f));
        gingham.SetFloat("_DoubleSidedEnable", 1f); gingham.SetFloat("_DoubleSidedNormalMode", 0f); gingham.SetFloat("_Smoothness", 0.1f);
        HDMaterial.ValidateMaterial(gingham);
        var mirror = Mat("HiFi_KevinMirror", new Color(0.85f, 0.87f, 0.88f)); mirror.SetFloat("_Metallic", 1f); mirror.SetFloat("_Smoothness", 0.95f);
        var remap = new Dictionary<string, Material>
        {
            ["KV_Pine"] = TexMat("HiFi_KevinPine", "oak_veneer_01", new Color(1.1f, 0.95f, 0.78f), 0.8f, 0.3f),   // film 296: honey pine (build 1 at 1.0/0.80/0.55 read orange)
            ["KV_QuiltLow"] = PaperMat("HiFi_KevinQuilt", "spec/dressing/kevin_quilt.png", new Color(0.8f, 0.7f, 0.65f)),
            ["KV_QuiltUp"] = Mat("HiFi_KevinQuiltUp", new Color(0.20f, 0.42f, 0.27f)),    // Marina 375/380: green quilt on the upper bunk
            ["KV_Gingham"] = gingham, ["KV_Mirror"] = mirror, ["KV_Brass"] = BrassMat(),
            ["KV_Mattress"] = Mat("HiFi_KevinMattress", new Color(0.88f, 0.87f, 0.83f)), ["KV_Pillow"] = Mat("HiFi_KevinPillow", new Color(0.93f, 0.92f, 0.89f)),
            ["KV_Cork"] = Mat("HiFi_KevinCork", new Color(0.66f, 0.50f, 0.32f)), ["KV_Paper"] = Mat("HiFi_KevinPaper", new Color(0.93f, 0.92f, 0.88f)),
            ["KV_DartBlack"] = Mat("HiFi_KevinDartBlack", new Color(0.08f, 0.08f, 0.08f)), ["KV_DartCream"] = Mat("HiFi_KevinDartCream", new Color(0.88f, 0.82f, 0.66f)),
            ["KV_DartRed"] = Mat("HiFi_KevinDartRed", new Color(0.70f, 0.12f, 0.12f)), ["KV_DartGreen"] = Mat("HiFi_KevinDartGreen", new Color(0.12f, 0.50f, 0.25f)),
            ["KV_Globe"] = Mat("HiFi_KevinGlobe", new Color(0.20f, 0.50f, 0.80f)), ["KV_LampRed"] = Mat("HiFi_KevinLampRed", new Color(0.80f, 0.10f, 0.10f)),
            ["KV_Bulb"] = Mat("HiFi_KevinBulb", new Color(1.0f, 0.95f, 0.85f)), ["KV_Trunk"] = Mat("HiFi_KevinTrunk", new Color(0.72f, 0.65f, 0.45f)),
            ["KV_TrunkBand"] = Mat("HiFi_KevinTrunkBand", new Color(0.55f, 0.40f, 0.24f)), ["KV_Chess"] = Mat("HiFi_KevinChess", new Color(0.72f, 0.56f, 0.36f)),
        };
        var g = PlaceHiFi(root, 0f, "KevinRoom", remap);
        if (g != null)
            foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
            {
                r.shadowCastingMode = r.sharedMaterial != null && r.sharedMaterial.name == "HiFi_KevinBulb" ? ShadowCastingMode.Off : ShadowCastingMode.On;
                r.gameObject.isStatic = true;
            }
        // the bunk's walk box (a solid body: the lower deck's rails stand 0.20 m off the floor, nothing hides under them)
        var B = K["bunk"]; float x0 = (float)B["x"][0], x1 = (float)B["x"][1], z0 = (float)B["z"][0], z1 = (float)B["z"][1], h = (float)B["post_h"];
        var col = new GameObject("KevinCollider_bunk"); col.transform.SetParent(root.transform, false); col.isStatic = true;
        col.transform.position = new Vector3((x0 + x1) / 2, h / 2, -(z0 + z1) / 2);
        col.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, h, z1 - z0);
        var fx = Child(root, "KevinFixtures");
        foreach (var kv in (JObject)K["lamps"])
        {
            var q = kv.Value;
            AddLamp(fx, "KevinLamp_" + kv.Key, new Vector3((float)q["at"][0], (float)q["at"][1], (float)q["at"][2]), 0f, (float)q["lumens"], (float)q["kelvin"]);
        }
    }
}
