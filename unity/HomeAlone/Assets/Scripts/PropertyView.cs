using System.Collections.Generic;
using UnityEngine;

/// K hides everything off the McCallister lot (user, Oct 19: "toggle it off to distinguish what should be modeled and what can be
/// rendered by a backdrop"): the WinterNeighborhood (street, neighbours' houses, lots, wires) and any other exterior renderer or light
/// whose centre lies outside the lot. The house, the window/sky domes and the probes are never touched. Made at scene load, no editor setup.
public class PropertyView : MonoBehaviour
{
    // ponytail: the lot is a world-space box, the registered GLB site (the model's own lot) without its street strip (object248, x > 22).
    // No parcel survey yet; replace with the Cook County parcel polygon if the edges matter.
    static readonly Rect Lot = Rect.MinMaxRect(-22f, -38f, 23f, 7f);   // x min/max, z min/max (front = +x, the street side)
    bool hidden;
    readonly List<Renderer> renderers = new List<Renderer>();
    readonly List<Light> lights = new List<Light>();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Make() { if (GameObject.Find("Exterior") != null) new GameObject("Property view - press K").AddComponent<PropertyView>(); }

    void Update()
    {
        if (!Input.GetKeyDown(KeyCode.K)) return;
        if (!hidden)
        {
            renderers.Clear(); lights.Clear();
            var ext = GameObject.Find("Exterior");
            if (ext == null) return;
            var hood = ext.transform.Find("WinterNeighborhood");
            foreach (var r in ext.GetComponentsInChildren<Renderer>())
                if (r.enabled && (hood != null && r.transform.IsChildOf(hood) || Off(r.bounds.center))) { r.enabled = false; renderers.Add(r); }
            foreach (var l in ext.GetComponentsInChildren<Light>())
                if (l.enabled && (hood != null && l.transform.IsChildOf(hood) || Off(l.transform.position))) { l.enabled = false; lights.Add(l); }
            foreach (var l in FindObjectsByType<Light>(FindObjectsSortMode.None))   // lamp posts and the like parented outside Exterior
                if (l.type != LightType.Directional && l.enabled && Off(l.transform.position) && !lights.Contains(l)) { l.enabled = false; lights.Add(l); }
        }
        else
        {
            foreach (var r in renderers) if (r) r.enabled = true;
            foreach (var l in lights) if (l) l.enabled = true;
        }
        hidden = !hidden;
    }

    static bool Off(Vector3 p) => !Lot.Contains(new Vector2(p.x, p.z));
}
