using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// The dining room's first furnishing (Oct 18 2026, props lane, overnight; spec/dressing/dining.json): the lace cloth, chandelier, china
// cabinet, painting and brass (tools/house/hifi_dining_props.py -> DiningProps.glb) under DiningFixtures, so the chandelier's light joins
// the night layer and its flame bulbs go dark by day (Daylight); the walk colliders. Table, chairs and sideboard: StoreProps (dining_*).
public static partial class SpecGreybox
{
    static void Dining(GameObject root, float gy)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/dining.json"));
        if (!File.Exists(fp)) return;
        var D = JObject.Parse(File.ReadAllText(fp));
        var g = Child(root, "DiningFixtures");
        var bulb = Mat("HiFi_BulbDining", new Color(1f, 0.92f, 0.80f)); bulb.SetFloat("_Smoothness", 0.5f);
        bulb.SetColor("_EmissiveColor", new Color(1f, 0.92f, 0.80f) * 4000f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(bulb);
        var p = PlaceHiFi(g, gy, "DiningProps", new Dictionary<string, Material> { ["DN_Bulb"] = bulb });
        if (p != null)
            foreach (var r in p.GetComponentsInChildren<MeshRenderer>())
            {
                r.gameObject.isStatic = true;
                if (r.sharedMaterial == bulb || r.name.Contains("Chandelier")) r.shadowCastingMode = ShadowCastingMode.Off;   // its own light sits among the arms
            }
        var ch = D["chandelier"];   // one warm point at the arms' height, as the foyer's fixtures (night layer via Daylight)
        AddLamp(g, "DiningChandelier_Light", new Vector3((float)ch["at"][0], (float)ch["y"][0] + 0.25f, (float)ch["at"][1]), gy, (float)ch["lumens"], (float)ch["kelvin"]);
        var col = Child(root, "DiningColliders"); int n = 0;
        foreach (var c in D["colliders"])
        {
            float x0 = (float)c["x"][0], x1 = (float)c["x"][1], z0 = (float)c["z"][0], z1 = (float)c["z"][1], y0 = (float)c["y"][0], y1 = (float)c["y"][1];
            var o = new GameObject("DiningCollider_" + (string)c["name"]); o.transform.SetParent(col.transform, false); o.isStatic = true;
            o.transform.position = new Vector3((x0 + x1) / 2, gy + (y0 + y1) / 2, -(z0 + z1) / 2);
            o.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, y1 - y0, z1 - z0); n++;
        }
        Debug.Log($"Dining: {(p != null ? "props placed" : "DiningProps.glb missing")}, {n} colliders");
    }
}
