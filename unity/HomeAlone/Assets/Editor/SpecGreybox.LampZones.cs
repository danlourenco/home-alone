using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// LAMP ZONES (perf pass 1, Oct 20): a cached point lamp's redraw (a door or paint can moving, ShadowRefresh) renders every caster in its
// 7-9 m range into 6 cube faces: ~25 M triangles, including the rooms behind its walls, the floors above and below and the yard, none
// of which can change its map (a wall stands nearer the lamp). Each shadowed lamp gets a ZONE (one of ZoneBits, k-means on lamp
// positions), and its shadow casters become the renderers some lamp of its zone can see: HDRP shadow layers (linkShadowLayers off, the
// lamp's renderingLayerMask = its zone bit; the casters carry the zone bits of the zones that see them, beside their lighting bits).
// Lighting is untouched: the lamps' light layers stay as they were, and the added bits are ones no light, probe or decal lights by.
//   "can see": one of up to 64 points (a grid over the renderer's bounds grown 5 cm, <= 0.5 m apart) is reached by a line from the lamp
//   without crossing a shadow-casting collider (the same test ShadowRefresh.Sees uses for moving pieces). Conservative: walls with no
//   collider never block, so their far side stays in.
// Standalone report on a saved scene: -executeMethod SpecGreybox.LampZonesScene (Library/LampZones.txt; scene not saved).
public static partial class SpecGreybox
{
    static readonly int[] ZoneBits = { 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 };   // bit 3 (8) is LayerOutside (the moon)

    public static void LampZonesScene()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity", OpenSceneMode.Single);
        var r = LampZones(apply: false);
        File.WriteAllText("Library/LampZones.txt", r); Debug.Log(r);
    }

    static readonly RaycastHit[] lampHits = new RaycastHit[32];
    static bool LampReach(Vector3 o, Vector3 p)
    {
        var d = p - o; float len = d.magnitude; if (len < 1e-3f) return true;
        int n = Physics.RaycastNonAlloc(o, d / len, lampHits, len - 0.02f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
        if (n == lampHits.Length) return true;
        for (int i = 0; i < n; i++)
        {
            var r = lampHits[i].collider.GetComponent<Renderer>();
            if (r && r.enabled && r.shadowCastingMode != ShadowCastingMode.Off) return false;
        }
        return true;
    }
    // can the lamp see any of up to 64 points of the renderer's bounds (grown 5 cm, <= 0.5 m apart) past the shadow-casting colliders?
    static bool LampSees(Light l, Renderer r)
    {
        var b = r.bounds; b.Expand(0.10f); var o = l.transform.position;
        if (b.SqrDistance(o) >= l.range * l.range) return false;
        if (b.Contains(o) || LampReach(o, b.center)) return true;
        int nx = Mathf.Clamp(Mathf.CeilToInt(b.size.x / 0.5f) + 1, 2, 4), ny = Mathf.Clamp(Mathf.CeilToInt(b.size.y / 0.5f) + 1, 2, 4), nz = Mathf.Clamp(Mathf.CeilToInt(b.size.z / 0.5f) + 1, 2, 4);
        for (int x = 0; x < nx; x++) for (int y = 0; y < ny; y++) for (int z = 0; z < nz; z++)
                {
                    var p = b.min + Vector3.Scale(b.size, new Vector3(x / (nx - 1f), y / (ny - 1f), z / (nz - 1f)));
                    if (l.type == LightType.Spot && Vector3.Angle(l.transform.forward, p - o) > l.spotAngle * 0.5f + 5f) continue;
                    if (LampReach(o, p)) return true;
                }
        return false;
    }

    static string LampZones(bool apply)
    {
        var t0 = System.Diagnostics.Stopwatch.StartNew();
        var mode = Object.FindAnyObjectByType<HouseNightMode>(FindObjectsInactive.Include);
        bool wasNight = mode && mode.nightLayer && mode.nightLayer.activeSelf;
        if (mode && mode.nightLayer) mode.nightLayer.SetActive(true);
        Physics.SyncTransforms();
        var lamps = Object.FindObjectsByType<Light>().Where(l => l.isActiveAndEnabled && l.type != LightType.Directional && l.shadows != LightShadows.None
            && l.lightmapBakeType != LightmapBakeType.Baked && l.GetComponent<HDAdditionalLightData>() is HDAdditionalLightData hd && hd.shadowUpdateMode == ShadowUpdateMode.OnDemand).ToList();
        // casters a lamp draws today: shadow-casting renderers on the lamps' default light layer (bit 0)
        // (every renderer type, inactive ones too: the rope, the climbing dummy, pieces HouseSplit hides; only bits are added)
        var casters = Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include).Where(r => r.shadowCastingMode != ShadowCastingMode.Off
            && (r.renderingLayerMask & 1u) != 0).ToList();
        long Tris(Renderer r)
        {
            var mf = r.GetComponent<MeshFilter>(); var m = r is SkinnedMeshRenderer s ? s.sharedMesh : mf ? mf.sharedMesh : null; long t = 0;
            if (m) for (int i = 0; i < m.subMeshCount; i++) t += m.GetIndexCount(i) / 3;
            return t;
        }
        var tris = casters.ToDictionary(r => r, Tris);
        // moving pieces: every lamp keeps them (their bounds change; ShadowRefresh decides when to redraw)
        var moving = new HashSet<Renderer>(Object.FindObjectsByType<EntranceDoor>(FindObjectsInactive.Include).SelectMany(d => d.GetComponentsInChildren<Renderer>(true))
            .Concat(Object.FindObjectsByType<SwingDoor>(FindObjectsInactive.Include).SelectMany(d => d.GetComponentsInChildren<Renderer>(true)))
            .Concat(Object.FindObjectsByType<TrunkLid>(FindObjectsInactive.Include).SelectMany(d => d.GetComponentsInChildren<Renderer>(true)))
            .Concat(Object.FindObjectsByType<PaintCanTrap>(FindObjectsInactive.Include).SelectMany(d => d.GetComponentsInChildren<Renderer>(true)
                .Concat(d.dummy ? d.dummy.GetComponentsInChildren<Renderer>(true) : new Renderer[0]))));
        var seen = new Dictionary<Light, HashSet<Renderer>>(); long before = 0, after = 0;
        foreach (var l in lamps)
        {
            var inRange = casters.Where(r => r.bounds.SqrDistance(l.transform.position) < l.range * l.range).ToList();
            before += inRange.Sum(r => tris[r]) * (l.type == LightType.Point ? 6 : 1);
            seen[l] = new HashSet<Renderer>(inRange.Where(r => moving.Contains(r) || LampSees(l, r)));
        }
        // zones: greedy agglomerative clustering. Start with a zone per lamp; merge the two zones whose union costs least (cost of a zone:
        // over its lamps, the triangles of the zone's seen casters inside each lamp's range x cube faces) until ZoneBits zones are left
        int k = Mathf.Min(ZoneBits.Length, lamps.Count), N = casters.Count, W = (N + 63) / 64;
        var idx = new Dictionary<Renderer, int>(); for (int i = 0; i < N; i++) idx[casters[i]] = i;
        var triArr = casters.Select(r => tris[r]).ToArray();
        ulong[] Bits(IEnumerable<Renderer> rs) { var b = new ulong[W]; foreach (var r in rs) { int i = idx[r]; b[i >> 6] |= 1UL << (i & 63); } return b; }
        var seenB = lamps.Select(l => Bits(seen[l])).ToArray();
        var rangeB = lamps.Select(l => Bits(casters.Where(r => r.bounds.SqrDistance(l.transform.position) < l.range * l.range))).ToArray();
        var faces = lamps.Select(l => l.type == LightType.Point ? 6L : 1L).ToArray();
        long Cost(List<int> members, ulong[] u)
        {
            long c = 0;
            foreach (int m in members)
                for (int w = 0; w < W; w++) { ulong x = u[w] & rangeB[m][w]; for (int t = 0; x != 0; t++, x >>= 1) if ((x & 1UL) != 0) c += triArr[(w << 6) + t] * faces[m]; }
            return c;
        }
        ulong[] Or(ulong[] a, ulong[] b) { var o = new ulong[W]; for (int w = 0; w < W; w++) o[w] = a[w] | b[w]; return o; }
        var cl = Enumerable.Range(0, lamps.Count).Select(i => (members: new List<int> { i }, u: seenB[i], cost: 0L)).ToList();
        for (int i = 0; i < cl.Count; i++) cl[i] = (cl[i].members, cl[i].u, Cost(cl[i].members, cl[i].u));
        while (cl.Count > k)
        {
            long best = long.MaxValue; int bi = -1, bj = -1;
            for (int i = 0; i < cl.Count; i++)
                for (int j = i + 1; j < cl.Count; j++)
                {
                    var m = cl[i].members.Concat(cl[j].members).ToList();
                    long d = Cost(m, Or(cl[i].u, cl[j].u)) - cl[i].cost - cl[j].cost;
                    if (d < best) { best = d; bi = i; bj = j; }
                }
            var mm = cl[bi].members.Concat(cl[bj].members).ToList(); var uu = Or(cl[bi].u, cl[bj].u);
            cl[bi] = (mm, uu, Cost(mm, uu)); cl.RemoveAt(bj);
        }
        var zone = new Dictionary<Light, int>();
        for (int z = 0; z < cl.Count; z++) foreach (int m in cl[z].members) zone[lamps[m]] = z;
        var zoneSet = Enumerable.Range(0, k).Select(i => new HashSet<Renderer>(lamps.Where(l => zone[l] == i).SelectMany(l => seen[l]))).ToList();
        foreach (var l in lamps)
        {
            var zs = zoneSet[zone[l]];
            after += casters.Where(r => zs.Contains(r) && r.bounds.SqrDistance(l.transform.position) < l.range * l.range).Sum(r => tris[r]) * (l.type == LightType.Point ? 6 : 1);
        }
        long ideal = lamps.Sum(l => seen[l].Sum(r => tris[r]) * (l.type == LightType.Point ? 6L : 1L));   // one layer per lamp (no zones)
        int tagged = 0;
        if (apply)
        {
            foreach (var r in casters)
            {
                uint bits = 0; for (int i = 0; i < k; i++) if (zoneSet[i].Contains(r) || moving.Contains(r)) bits |= 1u << ZoneBits[i];   // moving pieces: every zone
                r.renderingLayerMask |= bits; if (bits != 0) tagged++;
            }
            foreach (var l in lamps)
            {
                var hd = l.GetComponent<HDAdditionalLightData>(); hd.linkShadowLayers = false; l.renderingLayerMask = 1 << ZoneBits[zone[l]];
            }
        }
        if (mode && mode.nightLayer) mode.nightLayer.SetActive(wasNight);
        string worst = string.Join(", ", lamps.OrderByDescending(l => seen[l].Sum(r => tris[r])).Take(5).Select(l => $"{l.name} z{zone[l]}"));
        return $"LampZones{(apply ? "" : " (report only)")}: {lamps.Count} cached shadowed lamps in {k} zones; casters a full redraw of every lamp draws {before / 1e6:F0} M -> {after / 1e6:F0} M triangles " +
               $"(-{100 - 100.0 * after / System.Math.Max(before, 1):F0}%; a zone per lamp would be {ideal / 1e6:F0} M); {tagged} of {casters.Count} casters seen by some zone ({t0.Elapsed.TotalSeconds:F1} s). Most seen: {worst}\n";
    }
}
