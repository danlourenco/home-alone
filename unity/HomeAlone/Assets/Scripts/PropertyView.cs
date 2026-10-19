using System.Collections.Generic;
using UnityEngine;

/// K hides everything off the McCallister lot (user, Oct 19: "toggle it off to distinguish what should be modeled and what can be
/// rendered by a backdrop"): the WinterNeighborhood (street, neighbours' houses, lots, wires) and any other exterior renderer or light
/// whose centre lies outside the lot. The house, the window/sky domes and the probes are never touched. Made at scene load, no editor setup.
public class PropertyView : MonoBehaviour
{
    // The McCallister lot (user-agreed Oct 19, docs/RESUME.md section 3), spec (x, z): the Cook County parcel's sides and rear
    // (art/home_alone/references/neighborhood/data, tools/house/nb_frame.py) with the front at the public sidewalk's back edge
    // (x 28.87, SpecGreybox.FrontDrive), so the walk piers, the U-drive's mouths and the walk are on it (film 11908/12066; the 2015
    // fence stands there). The parcel's own front line plots at x 27.35.
    static readonly Vector2[] Poly = { new Vector2(-30.16f, 30.58f), new Vector2(28.87f, 30.72f), new Vector2(28.87f, -3.91f), new Vector2(-34.16f, -4.06f) };
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

    // Lot.Contains(world x, z) (SpecGreybox.ExteriorRealism splits the ground meshes with it at build time)
    public sealed class LotShape { public bool Contains(Vector2 worldXZ) => InPoly(worldXZ.x, -worldXZ.y); }
    public static readonly LotShape Lot = new LotShape();
    static bool InPoly(float x, float z)   // spec x, z; even-odd rule
    {
        bool inside = false;
        for (int i = 0, j = Poly.Length - 1; i < Poly.Length; j = i++)
            if ((Poly[i].y > z) != (Poly[j].y > z) && x < (Poly[j].x - Poly[i].x) * (z - Poly[i].y) / (Poly[j].y - Poly[i].y) + Poly[i].x) inside = !inside;
        return inside;
    }
    static bool Off(Vector3 p) => !Lot.Contains(new Vector2(p.x, p.z));
}
