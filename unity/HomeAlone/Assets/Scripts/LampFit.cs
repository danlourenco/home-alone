using System.Collections.Generic;
using UnityEngine;

// LAMP RANGES FITTED TO ROOMS (Oct 21; user, after fs-nightB: "was great, keep it"; docs/PERFORMANCE.md "Phase B"): at scene load every
// real-time punctual lamp's range becomes its room's extent + Margin (1 m, the doorway margin), never above its own range. Room extent
// = the 90th percentile of 128 rays' hit distances against the colliders (walls, floors, ceilings; the rays out through doorways are
// the top 10%). The same values as PerfProbe's fit=1 variant (fs-nightB: foyer night 23 -> 36 fps, hall 29 -> 45, kitchen 26 -> 32 at
// the 2048x1152 full-screen default). Lamps outdoors keep their range (most rays escape). -nolampfit: the old ranges.
public static class LampFit
{
    public const float Margin = 1f;
    public static readonly Dictionary<Light, float> Original = new();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Fit()
    {
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-nolampfit") >= 0) return;
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Include))
        {
            if (l.type == LightType.Directional || (l.bakingOutput.isBaked && l.bakingOutput.lightmapBakeType == LightmapBakeType.Baked)) continue;   // lightmapBakeType is editor-only
            Original[l] = l.range; l.range = Mathf.Min(l.range, Extent(l.transform.position, l.range) + Margin);
        }
    }

    public static float Extent(Vector3 o, float maxDist)
    {
        var d = new List<float>(128);
        for (int k = 0; k < 128; k++)   // Fibonacci sphere
        {
            float y = 1f - 2f * (k + 0.5f) / 128f, rr = Mathf.Sqrt(1f - y * y), ph = k * 2.39996323f;
            d.Add(Physics.Raycast(o, new Vector3(Mathf.Cos(ph) * rr, y, Mathf.Sin(ph) * rr), out var h, maxDist, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore) ? h.distance : maxDist);
        }
        d.Sort(); return d[(int)(0.9f * (d.Count - 1))];
    }
}
