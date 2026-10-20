using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

// The lamps' shadow maps are cached (Editor/SpecGreybox.Shadows.cs): drawn when a lamp turns on, then kept.
//  - Warm(camera), every frame at night (HouseNightMode): a lamp is drawn when it first comes into view and again when the camera
//    first comes within its range. HDRP's own "render on placement" left maps wrong for lamps placed while out of view or far off
//    (measured Oct 16: the den's desk lamp dark and the living room's console lamps blotched after a 19-view batch run; right when
//    redrawn with the camera close by).
//  - Near(bounds): anything that moves (the swing door, the paint cans, the dummy) calls it while it moves, and every lamp whose
//    range reaches it redraws its map that frame.
//  - Forget(): the night layer switched; every lamp is drawn afresh when next in view.
public static class ShadowRefresh
{
    public static int Requests;   // shadow-map redraws asked for (PerfProbe tags the frames)
    static HDAdditionalLightData[] lamps;
    static Light[] lights;
    static int[] drawn;
    static readonly Plane[] planes = new Plane[6];

    static void Find()
    {
        if (lamps != null && (lamps.Length == 0 || lamps[0])) return;
        lamps = Object.FindObjectsByType<HDAdditionalLightData>(FindObjectsInactive.Include, FindObjectsSortMode.None);
        lights = new Light[lamps.Length]; drawn = new int[lamps.Length];
        for (int i = 0; i < lamps.Length; i++) lights[i] = lamps[i].GetComponent<Light>();
    }

    static bool Cached(int i) => lamps[i] && lights[i] && lights[i].isActiveAndEnabled && lights[i].shadows != LightShadows.None && lamps[i].shadowUpdateMode == ShadowUpdateMode.OnDemand;

    public static void Forget() { if (drawn != null) System.Array.Clear(drawn, 0, drawn.Length); }

    public static void Warm(Camera cam)
    {
        Find(); GeometryUtility.CalculateFrustumPlanes(cam, planes);
        for (int i = 0; i < lamps.Length; i++)
        {
            if (drawn[i] == 3 || !Cached(i)) continue;
            var l = lights[i];
            // once when it first comes into view, and once more when the camera first comes within its range: a map drawn while the
            // camera was far off came out wrong (the living room's console lamps, measured Oct 16); drawn from close by it is right
            if ((drawn[i] & 1) == 0 && GeometryUtility.TestPlanesAABB(planes, new Bounds(l.transform.position, Vector3.one * 2f * l.range))) { { lamps[i].RequestShadowMapRendering(); Requests++; } drawn[i] |= 1; }
            if ((drawn[i] & 2) == 0 && (cam.transform.position - l.transform.position).sqrMagnitude < l.range * l.range) { { lamps[i].RequestShadowMapRendering(); Requests++; } drawn[i] |= 2; }
        }
    }

    public static void Near(Bounds b)
    {
        Find();
        for (int i = 0; i < lamps.Length; i++)
        {
            if (Cached(i) && b.SqrDistance(lights[i].transform.position) < lights[i].range * lights[i].range) { lamps[i].RequestShadowMapRendering(); Requests++; }
        }
    }
}
