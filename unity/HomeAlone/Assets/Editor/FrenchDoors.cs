using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;

// The glazed French door pairs (tools/house/hifi_french_doors.py -> FrenchDoors.glb; spec/dressing/french_doors.json;
// changes/2026-10-16-french-doors.json). Places the model, hides the sunroom's prop box renderers (their colliders stay: the
// walk layer is unchanged there) and gives each OPEN leaf a walk-layer box collider at its open_deg (any angle).
public static partial class SpecGreybox
{
    static void FrenchDoors(GameObject root, GameObject groot, float gy, JToken ground)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/french_doors.json"));
        if (!File.Exists(fp)) return;
        var paint = Mat("HiFi_DoorPaint", new Color(0.88f, 0.87f, 0.83f)); paint.SetFloat("_Smoothness", 0.45f);
        var sheer = Mat("HiFi_FrenchSheer", new Color(0.93f, 0.92f, 0.88f)); sheer.SetFloat("_Smoothness", 0.1f);
        var g = PlaceHiFi(root, gy, "FrenchDoors", new Dictionary<string, Material> { ["FD_Paint"] = paint, ["FD_Glass"] = mGlass, ["FD_Brass"] = BrassMat(), ["FD_Sheer"] = sheer });
        if (g != null) foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        var D = JObject.Parse(File.ReadAllText(fp)); var L = D["leaf"];
        float JT = (float)L["jamb_t"], GAP = (float)L["gap"], T = (float)L["t"], head = (float)L["head"];
        var col = new GameObject("FrenchDoorColliders"); col.transform.SetParent(groot.transform, false); int nCol = 0, nHid = 0;
        foreach (var pr in D["pairs"])
        {
            var names = pr["between"].Select(t => (string)t).OrderBy(t => t).ToArray();
            var o = ground["openings"].First(q => q["between"].Select(t => (string)t).OrderBy(t => t).SequenceEqual(names));
            bool alongX = (string)o["axis"] == "z"; float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"];
            var room = ground["rooms"].First(q => (string)q["name"] == (string)pr["room"]);
            float rc = room["poly"].Average(p => (float)p[alongX ? 1 : 0]); float ns = rc > c ? 1f : -1f, face = c + ns * 0.07f;
            Vector3 W(float a, float r, float y) => alongX ? new Vector3(a, gy + y, -(face + ns * r)) : new Vector3(face + ns * r, gy + y, -a);
            if (pr["surface"] != null && (bool)pr["surface"])
            {   // the prop box this pair replaces: hide its renderers (both faces of the wall), keep its colliders
                foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None).Where(r => r.name.StartsWith("PropDoor")))
                {
                    var b = r.bounds.center; float a = alongX ? b.x : -b.z, w = alongX ? -b.z : b.x;
                    if (b.y < gy + 2.5f && a > lo - 0.01f && a < hi + 0.01f && Mathf.Abs(w - c) < 0.2f) { r.enabled = false; nHid++; }
                }
                continue;
            }
            // a casing leg that would lie on the main stair's stringer (the foyer/living opening's foyer face starts where flight 1's
            // side is: Marina 1142 shows the casing butting the stair): hidden, so the two faces don't fight
            // the grey-box main stair keeps its colliders: a leg whose volume (grown 1 cm) meets one of them lies on the stair's side
            var temp = new List<MeshCollider>();   // the detailed stair's stringers as temporary colliders (the grey-box stair stops short)
            var hs = GameObject.Find("Upstairs/MainStair_HiFi");
            if (hs != null) foreach (var mf in hs.GetComponentsInChildren<MeshFilter>().Where(m => m.name.StartsWith("RisersStringers") || m.name.StartsWith("StairWallTrim")))
                { var mc = mf.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mf.sharedMesh; temp.Add(mc); }
            Physics.SyncTransforms();
            foreach (var r in groot.GetComponentsInChildren<MeshRenderer>().Where(r => r.name == "Casing"))
            {
                var b = r.bounds; float a = alongX ? b.center.x : -b.center.z, w = alongX ? -b.center.z : b.center.x;
                bool leg = b.size.y > 1.5f && Mathf.Abs(w - c) < 0.12f && (Mathf.Abs(a - (lo - 0.035f)) < 0.03f || Mathf.Abs(a - (hi + 0.035f)) < 0.03f);
                if (leg && Physics.OverlapBox(b.center, b.extents + Vector3.one * 0.01f).Any(q => temp.Contains(q as MeshCollider) || (q.transform.parent != null && q.transform.parent.name == "MainStair")))
                { r.enabled = false; Debug.Log($"FrenchDoors: casing leg at {b.center} hidden (on the main stair's side)"); }
            }
            foreach (var mc in temp) Object.DestroyImmediate(mc);
            float th = (float)pr["open_deg"] * Mathf.Deg2Rad; if (th <= 0f) continue;
            float width = (hi - lo - 2 * JT - 3 * GAP) / 2, cs = Mathf.Cos(th), sn = Mathf.Sin(th);
            foreach (var (sgn, h) in new[] { (1f, lo + JT + GAP), (-1f, hi - JT - GAP) })
            {   // the leaf as hifi_french_doors.rot builds it: u along the leaf from the hinge, w through its thickness ([0.006, 0.006 + T]),
                // both in (along, into-room); the collider spans u [0.003, width] (90 deg: the leaf standing in the room; 175: folded back)
                Vector2 u = new Vector2(sgn * cs, sn), w = sgn > 0 ? new Vector2(sn, -cs) : new Vector2(-sn, -cs);
                Vector2 m = new Vector2(h, 0f) + u * ((0.003f + width) / 2) + w * (0.006f + T / 2);
                var pc = W(m.x, m.y, (head - JT - GAP) / 2); var pu = W(m.x + u.x, m.y + u.y, 0f) - W(m.x, m.y, 0f); pu.y = 0f;
                var bc = new GameObject("FrenchLeafCollider_" + pr["room"] + "_" + (sgn > 0 ? "lo" : "hi")); bc.transform.SetParent(col.transform, false); bc.isStatic = true;
                bc.transform.SetPositionAndRotation(pc, Quaternion.LookRotation(Vector3.Cross(pu, Vector3.up), Vector3.up));   // local x along the leaf
                bc.AddComponent<BoxCollider>().size = new Vector3(width - 0.003f, head - JT - GAP, T); nCol++;
            }
        }
        Debug.Log($"FrenchDoors: {nCol} leaf colliders, {nHid} prop renderers hidden");
    }
}
