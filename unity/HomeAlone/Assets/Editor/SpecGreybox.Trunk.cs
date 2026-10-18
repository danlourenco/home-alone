using System.Linq;
using UnityEditor;
using UnityEngine;

// Buzz's footlocker (the film's hero prop, 2688-2766; TRIAL Oct 17). tools/house/buzz_trunk.py sizes and places it
// (spec/dressing/buzz_trunk.json); tools/house/purchased_trunk.py rebuilds the bought scan (Sketchfab "Worn Black Trunk", CC BY:
// CREDITS.md) hollow with a separate lid into the gitignored Assets/Purchased/Trunk/BuzzTrunk.glb, already in spec position.
// Absent (a clone of the public repo): nothing is placed. "TrunkLid" is its own transform, pivot on the hinge line (closed);
// the body's colliders are a floor and four walls so the inside stays a real box.
public static partial class SpecGreybox
{
    const string TrunkPath = "Assets/Purchased/Trunk/BuzzTrunk.glb";

    static void Trunk(GameObject root)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>(TrunkPath);
        if (a == null) { Debug.Log("Trunk: " + TrunkPath + " not present, no trunk"); return; }
        var g = (GameObject)Object.Instantiate(a, root.transform); g.name = "BuzzTrunk_HiFi";
        // keep the imported root transform: glTFast makes the GLB's single root node (BuzzTrunk, at the spec position) the asset root;
        // zeroing it put the trunk at the origin (build buzztrunk #1)
        foreach (var c in g.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        var brass = BrassMat();
        var lid = g.GetComponentsInChildren<Transform>().First(t => t.name == "TrunkLid");
        var body = g.GetComponentsInChildren<Transform>().First(t => t.name == "TrunkBody");
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            r.sharedMaterials = r.sharedMaterials.Select(m => m != null && m.name.StartsWith("TR_Brass") ? brass : m).ToArray();
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            r.gameObject.isStatic = !r.transform.IsChildOf(lid);   // the lid will move
        }
        Bounds B(Transform t) { var rs = t.GetComponentsInChildren<Renderer>(); return rs.Aggregate(rs[0].bounds, (q, r) => { q.Encapsulate(r.bounds); return q; }); }
        var bb = B(body); const float w = 0.02f;
        void Box(string n, Vector3 c, Vector3 s)
        {
            var o = new GameObject("BuzzCollider_trunk_" + n); o.transform.SetParent(body, true); o.isStatic = true;
            var bc = o.AddComponent<BoxCollider>(); o.transform.position = c; bc.size = s;
        }
        Vector3 mn = bb.min, mx = bb.max, ce = bb.center, sz = bb.size;
        Box("floor", new Vector3(ce.x, mn.y + w / 2, ce.z), new Vector3(sz.x, w, sz.z));
        Box("front", new Vector3(mn.x + w / 2, ce.y, ce.z), new Vector3(w, sz.y, sz.z));
        Box("back", new Vector3(mx.x - w / 2, ce.y, ce.z), new Vector3(w, sz.y, sz.z));
        Box("endA", new Vector3(ce.x, ce.y, mn.z + w / 2), new Vector3(sz.x, sz.y, w));
        Box("endB", new Vector3(ce.x, ce.y, mx.z - w / 2), new Vector3(sz.x, sz.y, w));
        var lb = B(lid); var lc = lid.gameObject.AddComponent<BoxCollider>();
        var ls = lid.InverseTransformVector(lb.size);                          // the trunk may be turned (yaw_deg): size in the lid's axes
        lc.center = lid.InverseTransformPoint(lb.center); lc.size = new Vector3(Mathf.Abs(ls.x), Mathf.Abs(ls.y), Mathf.Abs(ls.z));
        Debug.Log($"Trunk: body {bb.min} .. {bb.max}, lid {lb.min} .. {lb.max}, hinge at {lid.position}");
    }

    // turn the lid about its hinge (its own position, along the box's length) so it rises: used for renders and a later interaction
    public static void OpenTrunkLid(Transform lid, float deg)
    {
        var start = lid.rotation; var up0 = Vector3.Dot(lid.GetComponentInChildren<Renderer>().bounds.center, Vector3.up);
        var b = lid.GetComponentInChildren<Renderer>().bounds.size;
        var axis = b.x >= b.z ? Vector3.right : Vector3.forward;               // the hinge runs along the box's length, whichever way it is turned
        lid.rotation = Quaternion.AngleAxis(deg, axis) * start;
        if (Vector3.Dot(lid.GetComponentInChildren<Renderer>().bounds.center, Vector3.up) < up0) lid.rotation = Quaternion.AngleAxis(-deg, axis) * start;
    }
}
