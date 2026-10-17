using System.IO;
using Newtonsoft.Json.Linq;
using UnityEngine;

// Buzz's room furniture (HOUSE-KERNEL step 5, Oct 17 2026, TRIAL 1: layout only; changes/2026-10-17-buzz-layout.json).
// tools/house/buzz_layout.py places every piece against a built face, measured from a corner in Marina's order (spec/dressing/buzz.json
// "pieces"), and writes the boxes they resolve to ("boxes"). This draws those boxes (with colliders: the walk layer); the store models
// (store_props.json buzz_*) hide the box of the same name and keep its collider.
public static partial class SpecGreybox
{
    static void Buzz(GameObject root)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/buzz.json"));
        if (!File.Exists(fp)) return;
        var mats = new System.Collections.Generic.Dictionary<string, Material> {
            ["wood"] = Mat("BuzzWood", new Color(0.36f, 0.24f, 0.15f)),
            ["mattress"] = Mat("BuzzMattress", new Color(0.86f, 0.85f, 0.80f)),
            ["blanket"] = Mat("BuzzBlanket", new Color(0.20f, 0.33f, 0.24f)),
            ["glass"] = Mat("BuzzTank", new Color(0.30f, 0.33f, 0.33f)),
        };
        var g = Child(root, "BuzzFurniture"); float keep = FloorY; FloorY = 0f;   // the upper floor
        foreach (var b in JObject.Parse(File.ReadAllText(fp))["boxes"])
        {
            float V(string k, int i) => (float)b[k][i];
            Box(g, (string)b["name"], V("x", 0), V("x", 1), -V("z", 1), -V("z", 0), V("y", 0), V("y", 1), mats[(string)b["mat"]]);
            // the walk layer on its own object named "*Collider_*", as the den's and living room's: RoomWalk then stands a body at the
            // free point nearest the room's centre instead of skipping a room whose centre holds furniture (build buzz1 #1: skipped)
            var box = g.transform.GetChild(g.transform.childCount - 1); Object.DestroyImmediate(box.GetComponent<Collider>());
            var col = new GameObject("BuzzCollider_" + (string)b["name"]); col.transform.SetParent(g.transform, false); col.isStatic = true;
            col.transform.SetPositionAndRotation(box.position, box.rotation); col.transform.localScale = box.localScale; col.AddComponent<BoxCollider>();
        }
        FloorY = keep;
    }
}
