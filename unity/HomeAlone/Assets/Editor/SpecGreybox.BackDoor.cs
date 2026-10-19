using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;

// The kitchen back door as a working door (user Oct 19: "i want to be able to walk out the kitchen door to the exterior"; TRIAL,
// changes/2026-10-19-kitchen-fidelity.json). door-assembly skill: one opening datum (spec/house_spec.ground.json "back_door", the
// one BackDoor.glb is generated from), the frame and threshold stay fixed, every leaf part (BackDoor.glb "Leaf*", the sash
// curtains Sheers.glb "LeafSheer/LeafSheerHem/LeafRed") hangs on one hinge on the leaf's room face at its hinge edge (spec +z,
// three brass hinges seen from inside; film 6902) and swings into the kitchen. The hidden DoorStop box that kept it shut is gone;
// the leaf's own box collider follows the swing. E opens it (EntranceDoor), `locked` refuses for gameplay.
public static partial class SpecGreybox
{
    // hifi_back_door.py's leaf: jamb 19 mm, clearance 3 mm, leaf faces 20-64 mm in from the wall's room face, bottom 11 mm up
    const float BdJamb = 0.019f, BdGap = 0.003f, BdFace0 = 0.02f, BdFace1 = 0.064f, BdBottom = 0.011f;

    static EntranceDoor BackDoorInteractions(GameObject root, float gy)
    {
        var w = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.ground.json"))))
            ["windows"].First(o => (string)o["name"] == "back_door");
        float xi = (float)w["wall_coord_spec"], z0 = (float)w["span_spec"][0], z1 = (float)w["span_spec"][1], head = (float)w["head_m"];
        float zl0 = z0 + BdJamb + BdGap, zl1 = z1 - BdJamb - BdGap, top = head - BdJamb - BdGap, width = zl1 - zl0, thick = BdFace1 - BdFace0;
        var model = GameObject.Find("BackDoor_HiFi");
        if (!model) throw new System.InvalidOperationException("BackDoor_HiFi is missing: the back door must not be built without its leaf");
        var hinge = new GameObject("BackDoorHinge"); hinge.transform.SetParent(root.transform, false);
        hinge.transform.position = new Vector3(xi - BdFace0, gy, -zl1);   // spec z -> world -z; the leaf runs from here toward world +z
        var sheers = GameObject.Find("Sheers_HiFi");
        var parts = model.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Leaf")).ToList();
        if (sheers) parts.AddRange(sheers.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Leaf")));
        if (parts.Count(t => t.IsChildOf(model.transform)) < 4) throw new System.InvalidOperationException($"BackDoor: only {parts.Count} leaf parts (rebuild BackDoor.glb)");
        foreach (var t in parts) t.SetParent(hinge.transform, true);
        foreach (var r in hinge.GetComponentsInChildren<Renderer>(true)) { r.gameObject.isStatic = false; r.renderingLayerMask = LayerHouse; }
        foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None).Where(t => t.name == "DoorStop_BackDoor"))
            foreach (var c in t.GetComponents<Collider>()) Object.DestroyImmediate(c);
        var box = hinge.AddComponent<BoxCollider>();
        box.center = new Vector3(-thick / 2, (BdBottom + top) / 2, width / 2); box.size = new Vector3(thick, top - BdBottom, width);
        var door = hinge.AddComponent<EntranceDoor>(); door.leaf = hinge.transform; door.leafCollider = box;
        door.handleLocal = new Vector3(-thick / 2, 0.89f, width - 0.06f);   // the knob: 0.89 m up, 6 cm in from the latch edge
        door.label = "back door"; door.locked = false;
        door.SetInstant(false);
        Debug.Log($"BackDoor: hinge at spec ({xi - BdFace0:F3}, {zl1:F3}), {parts.Count} leaf parts, leaf {width:F3} x {top - BdBottom:F3} m");
        return door;
    }

    // closed blocks, open clears (and the open leaf stands clear of the kitchen's furniture), locked refuses; from the kitchen side
    static string BackDoorCheck(EntranceDoor door, float gy)
    {
        var w = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.ground.json"))))
            ["windows"].First(o => (string)o["name"] == "back_door");
        float xi = (float)w["wall_coord_spec"], zc = ((float)w["span_spec"][0] + (float)w["span_spec"][1]) / 2;
        bool Blocked(float y) => Physics.Raycast(new Vector3(xi + 0.4f, gy + y, -zc), Vector3.left, 0.9f, ~0, QueryTriggerInteraction.Ignore);
        door.SetInstant(false); bool closed = Blocked(1f) && Blocked(0.3f) && Blocked(1.8f);
        door.SetInstant(true); bool open = !Blocked(1f) && !Blocked(0.3f) && !Blocked(1.8f);
        // the swept leaf at 25/50/75/100 degrees (a clean closed pose cannot show a leaf passing through a wall, casing or counter)
        var c = door.leafCollider; var hits = new System.Collections.Generic.List<string>();
        foreach (float a in new[] { 25f, 50f, 75f, door.openAngle })
        {
            door.leaf.localRotation = Quaternion.Euler(0, a, 0); Physics.SyncTransforms();
            hits.AddRange(Physics.OverlapBox(c.bounds.center, c.size / 2 * 0.98f, c.transform.rotation, ~0, QueryTriggerInteraction.Ignore)
                .Where(h => h != c).Select(h => $"{a:F0} deg: {h.transform.parent?.name}/{h.name}"));
        }
        door.locked = true; door.SetInstant(false); bool locked = !door.SetOpen(true); door.locked = false;
        door.SetInstant(false);
        if (!closed || !open || !locked || hits.Count > 0)
            throw new System.InvalidOperationException($"BackDoor FAIL: closed={closed}, open={open}, locked={locked}, open leaf touches [{string.Join(", ", hits)}]");
        return "Back door check: closed blocks (0.3/1.0/1.8 m), open clears, the open leaf touches nothing, locked refuses open\n";
    }
}
