using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

// The lamps' shadow maps are cached (Editor/SpecGreybox.Shadows.cs): drawn when a lamp turns on, then kept.
//  - Warm(camera), every frame at night (HouseNightMode): a lamp is drawn when it first comes into view and again when the camera
//    first comes within its range. HDRP's own "render on placement" left maps wrong for lamps placed while out of view or far off
//    (measured Oct 16: the den's desk lamp dark and the living room's console lamps blotched after a 19-view batch run; right when
//    redrawn with the camera close by).
//  - Near(bounds): anything that moves (the doors, the paint cans, the dummy, the trunk lid) calls it while it moves. It no longer
//    redraws at once: it QUEUES the lamps that can see the bounds, and Tick (every frame, ShadowRefreshPump) redraws at most
//    MaxPerFrame of them, each at most once per Interval frames, by frames waited x 1/distance^2 to the moving piece; a queued lamp is always drawn once more after the
//    motion stops (the final, at-rest map). Oct 20 (user, in the Mac app: "if i open the door or hit a paint can, the fps becomes
//    laughable again"): every lamp whose range sphere reached the moving bounds redrew all 6 cube faces EVERY frame of the motion,
//    including lamps behind walls and floors whose maps the moving piece can't change.
//    A lamp "can see" the bounds when the bounds are inside its range (and a spot's cone) and a line from the lamp reaches one of 9
//    points of the bounds without crossing a shadow-casting collider (a wall or floor: the moving piece is behind it in the lamp's
//    depth map, so its map can't change). Colliders with no shadow-casting renderer (stops, triggers, shades) never block.
//  - Forget(): the night layer switched; every lamp is drawn afresh when next in view.
public static class ShadowRefresh
{
    public static int Requests;                          // shadow-map redraws asked for (PerfProbe tags the frames)
    public static readonly List<string> Drawn = new List<string>();   // lamps redrawn since PerfProbe last cleared it
    public static int MaxPerFrame = 2, Interval = 4;     // throttle while something moves (PerfProbe -perfshadowq to A/B)
    public static bool Legacy;                           // the pre-Oct 20 behaviour (every lamp in range, every frame): the gate's "before"
    public static int Pending { get { int n = 0; if (pending != null) foreach (var p in pending) if (p) n++; return n; } }
    static HDAdditionalLightData[] lamps;
    static Light[] lights;
    static int[] drawn, lastAt;
    static bool[] pending;
    static float[] weight;   // 1 / distance^2 from the lamp to what moved: near lamps (the visible shadows) redraw more often
    static readonly Plane[] planes = new Plane[6];
    static readonly RaycastHit[] hits = new RaycastHit[16];

    static void Find()
    {
        if (lamps != null && (lamps.Length == 0 || lamps[0])) return;
        lamps = Object.FindObjectsByType<HDAdditionalLightData>(FindObjectsInactive.Include);
        lights = new Light[lamps.Length]; drawn = new int[lamps.Length]; lastAt = new int[lamps.Length]; pending = new bool[lamps.Length]; weight = new float[lamps.Length];
        for (int i = 0; i < lamps.Length; i++) { lights[i] = lamps[i].GetComponent<Light>(); lastAt[i] = int.MinValue / 2; }
    }

    static bool Cached(int i) => lamps[i] && lights[i] && lights[i].isActiveAndEnabled && lights[i].shadows != LightShadows.None && lamps[i].shadowUpdateMode == ShadowUpdateMode.OnDemand;

    static void Draw(int i, int frame) { lamps[i].RequestShadowMapRendering(); Requests++; lastAt[i] = frame; pending[i] = false; Drawn.Add(lights[i].name); }

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
            if ((drawn[i] & 1) == 0 && GeometryUtility.TestPlanesAABB(planes, new Bounds(l.transform.position, Vector3.one * 2f * l.range))) { Draw(i, Time.frameCount); drawn[i] |= 1; }
            if ((drawn[i] & 2) == 0 && (cam.transform.position - l.transform.position).sqrMagnitude < l.range * l.range) { Draw(i, Time.frameCount); drawn[i] |= 2; }
        }
    }

    public static void Near(Bounds b)
    {
        Find();
        for (int i = 0; i < lamps.Length; i++)
        {
            if (!Cached(i) || b.SqrDistance(lights[i].transform.position) >= lights[i].range * lights[i].range) continue;
            if (Legacy) { Draw(i, Time.frameCount); continue; }
            if (!pending[i] && Sees(lights[i], b)) { pending[i] = true; weight[i] = 1f / Mathf.Max(b.SqrDistance(lights[i].transform.position), 0.25f); }
        }
    }

    // the queued redraws for this frame (ShadowRefreshPump.LateUpdate; the editor gate calls it per simulated frame)
    public static void Tick(int frame)
    {
        if (Drawn.Count > 512) Drawn.Clear();   // nobody reading it (no PerfProbe): keep it small
        if (pending == null) return;
        for (int k = 0; k < MaxPerFrame; k++)
        {
            int best = -1;
            for (int i = 0; i < lamps.Length; i++)
                if (pending[i] && frame - lastAt[i] >= Interval && (best < 0 || Score(i, frame) > Score(best, frame))) best = i;
            if (best < 0) return;
            if (Cached(best)) Draw(best, frame); else pending[best] = false;
        }
    }

    static float Score(int i, int frame) => Mathf.Min(frame - lastAt[i], 100000) * weight[i];   // waited x near

    static bool Sees(Light l, Bounds b)
    {
        var o = l.transform.position;
        Vector3 c = b.center, e = b.extents;
        for (int s = 0; s < 9; s++)
        {
            var p = s == 8 ? c : c + Vector3.Scale(e * 0.95f, new Vector3((s & 1) == 0 ? -1 : 1, (s & 2) == 0 ? -1 : 1, (s & 4) == 0 ? -1 : 1));
            var d = p - o; float len = d.magnitude; if (len < 1e-4f) return true;
            if (l.type == LightType.Spot && Vector3.Angle(l.transform.forward, d) > l.spotAngle * 0.5f + 2f) continue;
            if (!Blocked(o, d / len, len, b)) return true;
        }
        return false;
    }

    static bool Blocked(Vector3 o, Vector3 dir, float len, Bounds b)
    {
        int n = Physics.RaycastNonAlloc(o, dir, hits, len, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
        if (n == hits.Length) return false;   // overflow: don't trust it, redraw
        var inner = b; inner.Expand(0.05f);
        for (int i = 0; i < n; i++)
        {
            if (inner.Contains(hits[i].point)) continue;   // the moving piece itself (or what touches it)
            var r = hits[i].collider.GetComponent<Renderer>();
            if (r && r.enabled && r.shadowCastingMode != UnityEngine.Rendering.ShadowCastingMode.Off) return true;
        }
        return false;
    }
}

// drives ShadowRefresh.Tick once per frame in Play (created at scene load; no scene object)
public class ShadowRefreshPump : MonoBehaviour
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Create() { var g = new GameObject("ShadowRefreshPump") { hideFlags = HideFlags.HideAndDontSave }; Object.DontDestroyOnLoad(g); g.AddComponent<ShadowRefreshPump>(); }
    void LateUpdate() => ShadowRefresh.Tick(Time.frameCount);
}
