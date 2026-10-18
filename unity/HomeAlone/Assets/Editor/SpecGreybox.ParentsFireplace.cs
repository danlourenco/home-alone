using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json.Linq;
using UnityEngine;

// The parents' bedroom fireplace (Oct 18 2026, TRIAL; changes/2026-10-18-parents-fireplace.json): tools/house/hifi_parents_fireplace.py ->
// ParentsFireplace.glb (spec coordinates above the upper floor), its painting's canvas from spec/dressing/parents_roses.png, and the walk
// colliders from spec/dressing/parents_fireplace.json (the mantel's body; the 3 cm hearth stays walkable).
public static partial class SpecGreybox
{
    static void ParentsFireplace(GameObject root)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/parents_fireplace.json"));
        if (!File.Exists(fp)) return;
        var J = JObject.Parse(File.ReadAllText(fp));
        var g = PlaceHiFi(root, 0f, "ParentsFireplace", new Dictionary<string, Material> {
            ["PF_Art"] = SpecTexMat("HiFi_ParentsRoses", "spec/dressing/parents_roses.png"), ["PF_Brass"] = BrassMat() });
        if (g != null) foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        var col = Child(root, "ParentsFireplaceColliders"); int n = 0;
        foreach (var c in J["colliders"])
        {
            float x0 = (float)c["x"][0], x1 = (float)c["x"][1], z0 = (float)c["z"][0], z1 = (float)c["z"][1], y0 = (float)c["y"][0], y1 = (float)c["y"][1];
            var o = new GameObject("ParentsCollider_" + (string)c["name"]); o.transform.SetParent(col.transform, false); o.isStatic = true;
            o.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2, -(z0 + z1) / 2);
            o.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, y1 - y0, z1 - z0); n++;
        }
        Debug.Log($"ParentsFireplace: {(g != null ? "placed" : "ParentsFireplace.glb missing")}, {n} colliders");
    }
}
