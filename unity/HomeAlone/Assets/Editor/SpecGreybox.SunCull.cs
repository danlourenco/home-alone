using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

// SUN CULL (perf pass 1, Oct 20): by day the sun's 4 cascades redraw every caster in range each frame (street day 28 k casters, 31-48 M
// triangles at the slow day poses). Many small interior pieces can never be sunlit: the walls, floors, roofs and the shell already
// shade every point of them, for every sun the weather uses. Taking such a piece out of the sun's casters changes no pixel: any point
// behind it along a sun ray is behind the same wall. So:
//   candidates = interior renderers with every side under 1.5 m (props, fixtures, chairs); blockers = every other opaque caster (the
//            shell, the outdoors, walls, floors, ceilings, big furniture), which all stay casters, so culling the candidates together
//            is exact;
//   culled   = a candidate whose every sample point (a 4x4x4 grid over its bounds grown 5 cm) is shaded by the blockers for every sun
//            direction (HouseWeather sunny / morning, each its centre and +-0.5 deg; overcast, its 40 deg disc as centre + 4 rim
//            points) and both of StoreyShadows' layer masks, and that no light lit by day with shadows can see (LampSees: its cached
//            map would lose the piece).
// Alpha-clipped and transparent casters never block (leaf cards, sheers have holes). The blockers are tested on temporary
// MeshColliders on a spare physics layer (31), so no gameplay collider takes part.
// Runtime: HouseNightMode.sunlessCasters cast no shadows by day (SetNight(false)) and get their own mode back at night.
public static partial class SpecGreybox
{
    const int SunCullLayer = 31;

    // a small interior piece (every side under 1.5 m: props, fixtures, chairs, lamps): the sun cascades' bulk by triangle count
    static bool Candidate(Renderer r) { var s = r.bounds.size; return s.x < 1.5f && s.y < 1.5f && s.z < 1.5f && r.shadowCastingMode != ShadowCastingMode.ShadowsOnly; }

    static string SunCull(HouseNightMode mode)
    {
        var t0 = System.Diagnostics.Stopwatch.StartNew();
        var ss = Object.FindObjectsByType<StoreyShadows>(FindObjectsInactive.Include).FirstOrDefault();
        var weather = Object.FindObjectsByType<HouseWeather>(FindObjectsInactive.Include).FirstOrDefault();
        if (ss == null || weather == null) return "SunCull: skipped (no StoreyShadows / HouseWeather)\n";
        bool Outer(Renderer r)
        {
            // alpha-clipped or transparent casters (leaf cards, sheers) have holes the sun gets through: never a blocker
            if (r.sharedMaterials.Any(m => m == null || m.HasProperty("_AlphaCutoffEnable") && m.GetFloat("_AlphaCutoffEnable") > 0.5f || m.HasProperty("_SurfaceType") && m.GetFloat("_SurfaceType") > 0.5f)) return false;
            // everything that stays a sun caster: the shell, the outdoors, and every interior piece too big to be a candidate (walls,
            // floors, ceilings, stairs, big furniture). Candidates are tested against these only, so taking them all out at once is exact
            if (r.shadowCastingMode == ShadowCastingMode.ShadowsOnly) return true;
            for (var q = r.transform; q; q = q.parent) if (q.name == "HouseShell" || q.parent == null && q.name == "Exterior") return true;
            return !Candidate(r);
        }
        var all = Object.FindObjectsByType<MeshRenderer>().Where(r => r.enabled && r.gameObject.activeInHierarchy && r.shadowCastingMode != ShadowCastingMode.Off).ToList();
        var outer = all.Where(Outer).ToList(); var outerSet = new HashSet<Renderer>(outer);
        var temp = new List<GameObject>();
        foreach (var r in outer)
        {
            var mf = r.GetComponent<MeshFilter>(); var mesh = mf ? mf.sharedMesh : null; if (mesh == null) continue;
            var g = new GameObject("SunCullCollider") { layer = SunCullLayer, hideFlags = HideFlags.HideAndDontSave };
            g.transform.SetPositionAndRotation(r.transform.position, r.transform.rotation); g.transform.localScale = r.transform.lossyScale;
            g.AddComponent<MeshCollider>().sharedMesh = mesh; temp.Add(g);
            sunCullMask[g.GetComponent<MeshCollider>()] = r.renderingLayerMask;
        }
        Physics.SyncTransforms();

        // sun directions (toward the sun), every weather state
        var dirs = new List<Vector3>();
        void Disc(HouseWeather.Look k, float radiusDeg)
        {
            var c = HouseWeather.ToSun(k.az, k.el, weather.frontAzimuth); dirs.Add(c);
            var u = Vector3.Cross(c, Vector3.up).normalized; var v = Vector3.Cross(c, u);
            foreach (var a in new[] { 0f, 90f, 180f, 270f }) dirs.Add(Quaternion.AngleAxis(radiusDeg, Quaternion.AngleAxis(a, c) * u) * c);
        }
        Disc(weather.sunny, 0.5f); Disc(weather.morning, 0.5f); Disc(weather.overcast, 20f);

        // lights on by day that cast shadows (cached lamps outside the night layer): a piece one of them can see keeps casting
        var dayLamps = Object.FindObjectsByType<Light>().Where(l => l.isActiveAndEnabled && l.type != LightType.Directional && l.shadows != LightShadows.None
            && l.lightmapBakeType != LightmapBakeType.Baked).ToList();
        uint[] masks = { ss.groundMask, ss.upperMask };
        var hits = new RaycastHit[32];
        bool Shaded(Vector3 p, Vector3 d, uint mask)
        {
            int n = Physics.RaycastNonAlloc(p + d * 60f, -d, hits, 60f, 1 << SunCullLayer, QueryTriggerInteraction.Ignore);   // from the sun's side: a point inside a shell piece is met on its sun face
            if (n == hits.Length) return false;
            for (int i = 0; i < n; i++) if (sunCullMask.TryGetValue(hits[i].collider, out var m) && (m & mask) != 0) return true;
            return false;
        }
        var culled = new List<Renderer>(); long rays = 0;
        foreach (var r in all)
        {
            if (outerSet.Contains(r) || r.transform.root.name == "Exterior" || !Candidate(r)) continue;
            var b = r.bounds; b.Expand(0.10f);
            if (dayLamps.Any(l => LampSees(l, r))) continue;   // a lamp lit by day draws it into its cached map
            bool lit = false;
            for (int i = 0; i < 64 && !lit; i++)
            {
                var p = b.min + Vector3.Scale(b.size, new Vector3(i % 4, i / 4 % 4, i / 16) / 3f);
                foreach (var d in dirs) { foreach (var m in masks) { rays++; if (!Shaded(p, d, m)) { lit = true; break; } } if (lit) break; }
            }
            if (!lit) culled.Add(r);
        }
        foreach (var g in temp) Object.DestroyImmediate(g);
        sunCullMask.Clear(); Physics.SyncTransforms();
        mode.sunlessCasters = culled.ToArray(); mode.sunlessModes = culled.Select(r => r.shadowCastingMode).ToArray();
        long tris = culled.Sum(r => { var mf = r.GetComponent<MeshFilter>(); var m = mf ? mf.sharedMesh : null; long t = 0; if (m) for (int s = 0; s < m.subMeshCount; s++) t += m.GetIndexCount(s) / 3; return t; });
        return $"SunCull: {culled.Count} of {all.Count - outer.Count} interior casters never sunlit (shell of {outer.Count}; {dirs.Count} sun directions x 2 storey masks, {rays / 1e6:F1} M rays, {t0.Elapsed.TotalSeconds:F1} s): " +
               $"{tris / 1e6:F2} M triangles out of the sun's cascades by day\n";
    }
    static readonly Dictionary<Collider, uint> sunCullMask = new();
}
