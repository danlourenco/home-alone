using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

// Old-vs-new proof for the fast surface gates (Oct 17). Opens the built House_WallGrid scene, restores SeamRooms from the build
// (Library/SeamRooms.json), plants a known z-fight (two coplanar quads on a floor) and a known clash (a rod through a panel), and runs
// the old O(k^2) loops (verbatim copies below) and the new ones on the same triangles. Compares on (pair, area, gap) and (pair, count).
//   Unity -batchmode -projectPath <scratch> -executeMethod SpecGreybox.CheckBench -quit -logFile bench.log [-skipold]
public static partial class SpecGreybox
{
    public static void CheckBench()
    {
        var log = new System.Text.StringBuilder(); void L(string x) { log.AppendLine(x); Debug.Log("CheckBench: " + x); }
        var sw = System.Diagnostics.Stopwatch.StartNew(); float Lap() { float t = (float)sw.Elapsed.TotalSeconds; sw.Restart(); return t; }
        bool skipOld = System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-skipold") >= 0;
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity", OpenSceneMode.Single);
        SeamRooms = JArray.Parse(File.ReadAllText("Library/SeamRooms.json")).Select(r => (((JArray)r[2]).Select(p => new Vector2((float)p[0], (float)p[1])).ToList(), (float)r[0], (float)r[1])).ToList();
        var roots = new[] { GameObject.Find("Upstairs"), GameObject.Find("Ground") };
        L($"scene open {Lap():F1} s, {SeamRooms.Count} rooms");

        // 1. production gates on the house as built
        L(ZFightCheck(roots).Trim() + $"   [new ZFightCheck {Lap():F1} s]");
        L(ClashCheck(roots).Trim() + $"   [new ClashCheck {Lap():F1} s]");
        L(TriangleBudget(roots).Trim());

        // 2. plants, under Ground: two quads on the floor of a walkable ground-floor room (2 and 8 mm up, different materials,
        // overlapping 0.3 x 0.3 m), and a 2 cm rod, 8 cm long, through a 2 cm panel at 1.2 m (the check reads vertices within 6 cm of a crossing)
        float Area(List<Vector2> q) => Mathf.Abs(Enumerable.Range(0, q.Count).Sum(i => q[i].x * q[(i + 1) % q.Count].y - q[(i + 1) % q.Count].x * q[i].y)) / 2;
        Vector2 Cen(List<Vector2> q) => q.Aggregate(Vector2.zero, (a, p) => a + p) / q.Count;
        float gy0 = SeamRooms.Min(r => r.Item2);
        var room = SeamRooms.Where(r => r.Item2 == gy0 && Inside(r.Item1, Cen(r.Item1))).OrderByDescending(r => Area(r.Item1)).First();   // the biggest ground-floor room
        var c = Cen(room.Item1);
        float fy = room.Item2;
        var plant = new GameObject("BenchPlant"); plant.transform.SetParent(roots[1].transform, false);
        Material Mat(Color col) { var m = new Material(Shader.Find("HDRP/Lit")); m.color = col; m.name = "Bench" + col; return m; }
        GameObject Box(string name, Vector3 lo, Vector3 hi, Material m)
        {
            var g = new GameObject(name); g.transform.SetParent(plant.transform, false);
            var mesh = new Mesh(); var v = new List<Vector3>(); var t = new List<int>();
            void F(Vector3 o, Vector3 du, Vector3 dv) { int i = v.Count; v.Add(o); v.Add(o + du); v.Add(o + du + dv); v.Add(o + dv); t.AddRange(new[] { i, i + 2, i + 1, i, i + 3, i + 2 }); }
            var s = hi - lo; Vector3 X = new(s.x, 0, 0), Y = new(0, s.y, 0), Z = new(0, 0, s.z);
            if (s.y == 0) F(lo, X, Z);   // a quad facing up (winding: Unity's clockwise front)
            else { F(lo, X, Z); F(lo + Y, Z, X); F(lo, Y, X); F(lo + Z, X, Y); F(lo, Z, Y); F(lo + X, Y, Z); }
            mesh.SetVertices(v); mesh.SetTriangles(t, 0); mesh.RecalculateNormals();
            g.AddComponent<MeshFilter>().sharedMesh = mesh; g.AddComponent<MeshRenderer>().sharedMaterial = m; return g;
        }
        var qa = Box("PlantQuadA", new Vector3(c.x, fy + 0.002f, c.y), new Vector3(c.x + 0.5f, fy + 0.002f, c.y + 0.5f), Mat(Color.red));
        var qb = Box("PlantQuadB", new Vector3(c.x + 0.2f, fy + 0.008f, c.y + 0.2f), new Vector3(c.x + 0.7f, fy + 0.008f, c.y + 0.7f), Mat(Color.blue));
        Box("PlantPanel", new Vector3(c.x - 0.25f, fy + 1.0f, c.y - 0.01f), new Vector3(c.x + 0.25f, fy + 1.5f, c.y + 0.01f), Mat(Color.green));
        Box("PlantRod", new Vector3(c.x - 0.01f, fy + 1.19f, c.y - 0.04f), new Vector3(c.x + 0.01f, fy + 1.21f, c.y + 0.04f), Mat(Color.yellow));
        Physics.SyncTransforms();
        L($"planted at spec ({c.x:F2}, {fy:F2}, {-c.y:F2})");
        L(ZFightCheck(roots).Split('\n').Where(x => x.StartsWith("Z-fight") || x.Contains("Plant")).Aggregate((a, b) => a + "\n" + b) + $"   [new, planted, {Lap():F1} s]");
        L(ClashCheck(roots).Split('\n').Where(x => x.StartsWith("Clash") || x.Contains("Plant")).Aggregate((a, b) => a + "\n" + b) + $"   [new, planted, {Lap():F1} s]");

        // 3. old vs new on the same triangles and the same tests
        bool Seen(Vector3 q) => SeamRooms.Any(r => q.y > r.y0 + 0.002f && q.y < r.y1 - 0.002f && Inside(r.pts, new Vector2(q.x, q.z)));
        var (tris, surf, unreadable) = ZTris(roots);
        // slivers (normal zero: Vector3.normalized of a cross under 1e-5) pair with nothing in either loop (dot 0 < 0.999); the old loop
        // would spend hours on them (396k in one bucket), so both get the list without them
        int slivers = tris.Count(t => t.n.sqrMagnitude < 0.5f); tris = tris.Where(t => t.n.sqrMagnitude >= 0.5f).ToList(); float tExtract = Lap();
        var temp = new List<Collider>();
        foreach (var r in surf.Select(x => x.r).Distinct())
            if (r.GetComponent<Collider>() == null) { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; temp.Add(mc); }
        Physics.SyncTransforms(); bool back = Physics.queriesHitBackfaces; Physics.queriesHitBackfaces = true; float tCollide = Lap();
        int nSeen = 0, nHidden = 0; double tKeep = 0; var kw = new System.Diagnostics.Stopwatch();
        bool Hidden(Vector3 at, Vector3 n)
        {
            var q = at + n * 0.004f;
            if (Physics.CheckSphere(q, 0.001f, ~0, QueryTriggerInteraction.Ignore)) return true;
            return Physics.Raycast(q, n, out var h, 3f, ~0, QueryTriggerInteraction.Ignore) && Vector3.Dot(h.normal, n) > 0.5f;
        }
        bool Keep(Vector3 at, Vector3 n) { kw.Restart(); nSeen++; bool k = Seen(at + n * 0.02f); if (k) { nHidden++; k = !Hidden(at, n); } tKeep += kw.Elapsed.TotalSeconds; return k; }
        L($"z-fight setup: extract {tExtract:F1} s ({tris.Count} triangles after {slivers} slivers, {surf.Count} surfaces), temp colliders {tCollide:F1} s ({temp.Count})");
        var rawN = new Dictionary<(int, int), (float area, float gap, Vector3 at)>();
        var newP = ZPairs(tris, surf, Keep, rawN); float tNew = Lap();
        L($"new ZPairs {tNew:F1} s (keep tests {tKeep:F1} s: {nSeen} Seen, {nHidden} Hidden): {rawN.Count} raw pairs, {newP.Count} kept");
        if (!skipOld)
        {
            nSeen = nHidden = 0; tKeep = 0;
            var rawO = new Dictionary<(int, int), (float area, float gap, Vector3 at)>();
            var oldP = ZPairsOld(tris, surf, Keep, rawO); float tOld = Lap();
            L($"old ZPairs {tOld:F1} s (keep tests {tKeep:F1} s: {nSeen} Seen, {nHidden} Hidden): {rawO.Count} raw pairs, {oldP.Count} kept");
            L("z-fight raw:  " + Same(rawO, rawN, surf)); L("z-fight kept: " + Same(oldP, newP, surf));
        }
        Physics.queriesHitBackfaces = back; foreach (var col in temp) Object.DestroyImmediate(col); Physics.SyncTransforms(); Lap();
        var crs = roots.SelectMany(o => o.GetComponentsInChildren<MeshRenderer>()).Where(r => r.enabled && r.shadowCastingMode != ShadowCastingMode.ShadowsOnly && r.GetComponent<MeshFilter>()?.sharedMesh != null).ToList();
        string rs2((int, int) k) => $"{crs[k.Item1].name}|{crs[k.Item2].name}";
        var fN = new Dictionary<(int, int), (int n, Vector3 at)>(); var rN = new Dictionary<(int, int), int>();
        ClashCheck(roots, fN, rN); float tcN = Lap(); L($"new ClashCheck {tcN:F1} s: {rN.Count} raw pairs, {fN.Count} found");
        if (!skipOld)
        {
            var fO = new Dictionary<(int, int), (int n, Vector3 at)>(); var rO = new Dictionary<(int, int), int>();
            ClashCheckOld(roots, fO, rO); float tcO = Lap(); L($"old ClashCheck {tcO:F1} s: {rO.Count} raw pairs, {fO.Count} found");
            bool eqR = rO.Count == rN.Count && rO.All(kv => rN.TryGetValue(kv.Key, out var x) && x == kv.Value);
            bool eqF = fO.Count == fN.Count && fO.All(kv => fN.TryGetValue(kv.Key, out var x) && x.n == kv.Value.n);
            foreach (var kv in fO.Where(kv => rs2(kv.Key).Contains("Plant"))) L($"  plant clash old {rs2(kv.Key)}: {kv.Value.n} crossings, new {(fN.TryGetValue(kv.Key, out var z) ? z.n : 0)}");
            L($"clash raw (pair, hits): {(eqR ? "IDENTICAL" : "DIFFERENT")} ({rO.Values.Sum()} hits); clash found (pair, crossings): {(eqF ? "IDENTICAL" : "DIFFERENT")}");
            foreach (var kv in rO.Where(kv => !rN.TryGetValue(kv.Key, out var x) || x != kv.Value).Take(10)) L($"  raw old {rs2(kv.Key)}: {kv.Value} vs new {(rN.TryGetValue(kv.Key, out var y) ? y : 0)}");
            foreach (var kv in rN.Where(kv => !rO.ContainsKey(kv.Key)).Take(10)) L($"  raw only new {rs2(kv.Key)}: {kv.Value}");
            foreach (var kv in fO.Where(kv => !fN.ContainsKey(kv.Key)).Take(10)) L($"  only old: {kv.Key} n={kv.Value.n}");
            foreach (var kv in fN.Where(kv => !fO.ContainsKey(kv.Key)).Take(10)) L($"  only new: {kv.Key} n={kv.Value.n}");
        }
        File.WriteAllText("Library/CheckBench.txt", log.ToString());
    }

    static string Same(Dictionary<(int, int), (float area, float gap, Vector3 at)> o, Dictionary<(int, int), (float area, float gap, Vector3 at)> n, List<(MeshRenderer r, Material m)> surf)
    {
        int onlyO = o.Keys.Count(k => !n.ContainsKey(k)), onlyN = n.Keys.Count(k => !o.ContainsKey(k)), gapD = 0, areaD = 0; double maxRel = 0;
        foreach (var kv in o) if (n.TryGetValue(kv.Key, out var x))
            {   // areas are sums in a different visit order: equal to float rounding
                double rel = System.Math.Abs(x.area - kv.Value.area) / System.Math.Max(1e-6, kv.Value.area); maxRel = System.Math.Max(maxRel, rel);
                if (rel > 1e-4) areaD++; if (x.gap != kv.Value.gap) gapD++;
            }
        var plant = o.Keys.Where(k => surf[k.Item1].r.name.StartsWith("Plant") || surf[k.Item2].r.name.StartsWith("Plant"))
            .Select(k => $"{surf[k.Item1].r.name}|{surf[k.Item2].r.name} {o[k].area:F4}/{(n.TryGetValue(k, out var y) ? y.area : -1):F4} m2 {o[k].gap * 1000:F1}/{(n.ContainsKey(k) ? y.gap * 1000 : -1):F1} mm");
        return $"{(onlyO + onlyN + gapD + areaD == 0 ? "IDENTICAL" : "DIFFERENT")} pairs old {o.Count} new {n.Count}, only old {onlyO}, only new {onlyN}, gap differs {gapD}, area differs {areaD} (max rel {maxRel:E1}); plant: " + string.Join("; ", plant);
    }

    // the z-fight candidate loop as it was before Oct 17 (verbatim but for raw/keep)
    static Dictionary<(int, int), (float area, float gap, Vector3 at)> ZPairsOld(List<(int s, Vector3 a, Vector3 b, Vector3 c, Vector3 n, float d)> tris,
        List<(MeshRenderer r, Material m)> surf, System.Func<Vector3, Vector3, bool> keep, Dictionary<(int, int), (float area, float gap, Vector3 at)> raw)
    {
        (int, int, int, int) Key(Vector3 n, float d) => (Mathf.RoundToInt(n.x * 50), Mathf.RoundToInt(n.y * 50), Mathf.RoundToInt(n.z * 50), Mathf.FloorToInt(d / 0.01f));
        var grid = new Dictionary<(int, int, int, int), List<int>>();
        for (int i = 0; i < tris.Count; i++) { var k = Key(tris[i].n, tris[i].d); if (!grid.TryGetValue(k, out var l)) grid[k] = l = new List<int>(); l.Add(i); }
        var pairs = new Dictionary<(int, int), (float area, float gap, Vector3 at)>();
        for (int i = 0; i < tris.Count; i++)
        {
            var ti = tris[i]; var k = Key(ti.n, ti.d);
            for (int dd = 0; dd <= 1; dd++)   // the same and the next 1 cm slab (each pair once)
            {
                if (!grid.TryGetValue((k.Item1, k.Item2, k.Item3, k.Item4 + dd), out var l)) continue;
                foreach (int j in l)
                {
                    if (dd == 0 && j <= i) continue;
                    var tj = tris[j];
                    if (tj.s == ti.s || surf[tj.s].m == surf[ti.s].m || Vector3.Dot(ti.n, tj.n) < 0.999f) continue;
                    float gap = Mathf.Abs(tj.d - ti.d); if (gap >= 0.01f) continue;
                    var (area, at) = OverlapOld(ti.a, ti.b, ti.c, tj.a, tj.b, tj.c, ti.n);
                    if (area < 1e-5f) continue;
                    var key = ti.s < tj.s ? (ti.s, tj.s) : (tj.s, ti.s);
                    raw.TryGetValue(key, out var r0); raw[key] = (r0.area + area, r0.area == 0 ? gap : Mathf.Min(r0.gap, gap), r0.area == 0 ? at : r0.at);
                    if (!keep(at, ti.n)) continue;
                    pairs.TryGetValue(key, out var acc);
                    pairs[key] = (acc.area + area, acc.area == 0 ? gap : Mathf.Min(acc.gap, gap), acc.area == 0 ? at : acc.at);
                }
            }
        }
        return pairs;
    }

    static (float, Vector3) OverlapOld(Vector3 a0, Vector3 b0, Vector3 c0, Vector3 a1, Vector3 b1, Vector3 c1, Vector3 n)
    {
        var u = Vector3.Cross(n, Mathf.Abs(n.y) < 0.9f ? Vector3.up : Vector3.right).normalized; var w = Vector3.Cross(n, u);
        Vector2 Pj(Vector3 p) => new Vector2(Vector3.Dot(p, u), Vector3.Dot(p, w));
        var poly = new List<Vector2> { Pj(a0), Pj(b0), Pj(c0) }; var clip = new[] { Pj(a1), Pj(b1), Pj(c1) };
        float Cr(Vector2 p, Vector2 q, Vector2 r) => (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x);
        if (Cr(poly[0], poly[1], poly[2]) < 0) poly.Reverse();
        if (Cr(clip[0], clip[1], clip[2]) < 0) System.Array.Reverse(clip);
        for (int e = 0; e < 3 && poly.Count > 0; e++)
        {
            Vector2 p = clip[e], q = clip[(e + 1) % 3]; var outp = new List<Vector2>();
            for (int i = 0; i < poly.Count; i++)
            {
                Vector2 s = poly[i], t = poly[(i + 1) % poly.Count]; float cs = Cr(p, q, s), ct = Cr(p, q, t);
                if (cs >= 0) outp.Add(s);
                if ((cs >= 0) != (ct >= 0)) outp.Add(s + (t - s) * (cs / (cs - ct)));
            }
            poly = outp;
        }
        if (poly.Count < 3) return (0f, Vector3.zero);
        float area = 0; Vector2 cen = Vector2.zero;
        for (int i = 0; i < poly.Count; i++) { area += Cr(Vector2.zero, poly[i], poly[(i + 1) % poly.Count]) / 2; cen += poly[i]; }
        cen /= poly.Count; float h = Vector3.Dot(a0, n);
        return (Mathf.Abs(area), u * cen.x + w * cen.y + n * h);
    }

    static string ClashCheckOld(GameObject[] roots, Dictionary<(int, int), (int n, Vector3 at)> foundOut, Dictionary<(int, int), int> raw)
    {
        var rs = roots.Where(o => o != null).SelectMany(o => o.GetComponentsInChildren<MeshRenderer>())
            .Where(r => r.enabled && r.shadowCastingMode != ShadowCastingMode.ShadowsOnly && r.GetComponent<MeshFilter>()?.sharedMesh != null).ToList();
        // coverage as the new check (unreadable meshes via MeshData), so old vs new compares only the pair search
        var md = rs.Select(r => ReadMesh(r.GetComponent<MeshFilter>().sharedMesh)).ToList();
        rs = rs.Where((r, k) => md[k].v != null).ToList(); md = md.Where(x => x.v != null).ToList();
        var verts = rs.Select((r, k) => { var v = md[k].v; var M = r.transform.localToWorldMatrix; for (int i = 0; i < v.Length; i++) v[i] = M.MultiplyPoint3x4(v[i]); return v; }).ToList();
        var tris = new List<(int r, Vector3 a, Vector3 b, Vector3 c)>();
        for (int k = 0; k < rs.Count; k++) { var v = verts[k]; foreach (var t in md[k].sub) for (int i = 0; i < t.Length; i += 3) tris.Add((k, v[t[i]], v[t[i + 1]], v[t[i + 2]])); }
        const float cell = 0.1f; var grid = new Dictionary<(int, int, int), List<int>>();
        for (int i = 0; i < tris.Count; i++)
        {
            var t = tris[i]; var lo = Vector3.Min(t.a, Vector3.Min(t.b, t.c)); var hi = Vector3.Max(t.a, Vector3.Max(t.b, t.c));
            if ((hi - lo).magnitude > 4f) continue;   // big planes (whole walls, floors) are pierced only by structure, which the seam check covers
            for (int x = Mathf.FloorToInt(lo.x / cell); x <= Mathf.FloorToInt(hi.x / cell); x++)
                for (int y = Mathf.FloorToInt(lo.y / cell); y <= Mathf.FloorToInt(hi.y / cell); y++)
                    for (int z = Mathf.FloorToInt(lo.z / cell); z <= Mathf.FloorToInt(hi.z / cell); z++)
                    { if (!grid.TryGetValue((x, y, z), out var l)) grid[(x, y, z)] = l = new List<int>(); l.Add(i); }
        }
        bool SegTri(Vector3 p, Vector3 q, Vector3 a, Vector3 b, Vector3 c, out Vector3 hit)
        {   // Moller-Trumbore on the segment p-q
            hit = default; var d = q - p; var e1 = b - a; var e2 = c - a; var h = Vector3.Cross(d, e2); float det = Vector3.Dot(e1, h);
            if (Mathf.Abs(det) < 1e-9f) return false;
            const float m = 1e-3f;   // a hit on the face's border is contact, not a crossing
            float f = 1 / det; var s0 = p - a; float u = f * Vector3.Dot(s0, h); if (u < m || u > 1 - m) return false;
            var qv = Vector3.Cross(s0, e1); float w = f * Vector3.Dot(d, qv); if (w < m || u + w > 1 - m) return false;
            float t = f * Vector3.Dot(e2, qv); if (t <= 1e-4f || t >= 1 - 1e-4f) return false;
            hit = p + d * t; return true;
        }
        // the pierced part's thickness at the crossing: the distance to its own far side, behind the crossed face (0 for a panel)
        var temp = new List<Collider>();
        foreach (var r in rs) if (r.GetComponent<Collider>() == null) { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; temp.Add(mc); }
        Physics.SyncTransforms(); bool back = Physics.queriesHitBackfaces; Physics.queriesHitBackfaces = true;
        float Thick(int pierced, Vector3 at, Vector3 n)
        {
            var col = rs[pierced].GetComponent<Collider>(); var ray = new Ray(at - n * 0.001f, -n);
            return col.Raycast(ray, out var h, 1f) ? h.distance : 0f;
        }
        bool Through(int piercer, int pierced, Vector3 at, Vector3 n)
        {   // does the piercer's surface within 6 cm of the crossing reach more than 2 cm past both sides of the pierced part (its
            // face and its far side)? Vertices, not the crossing edge: one long edge spans any thin part. 6 cm keeps a merged
            // mesh's neighbouring pieces (the next tread up) out of the test.
            float mn = 0, mx = 0;
            foreach (var v in verts[piercer]) { if ((v - at).sqrMagnitude > 0.06f * 0.06f) continue; float sd = Vector3.Dot(v - at, n); mn = Mathf.Min(mn, sd); mx = Mathf.Max(mx, sd); }
            return mx > 0.02f && mn < -(Thick(pierced, at, n) + 0.02f);
        }
        bool Visible(int piercer, Vector3 at, Vector3 n)
        {   // the crossing shows when the point just off the pierced face is in a walkable room and inside no other solid
            var q = at + n * 0.005f; var own = rs[piercer].GetComponent<Collider>();
            if (!SeamRooms.Any(r => q.y > r.y0 + 0.002f && q.y < r.y1 - 0.002f && Inside(r.pts, new Vector2(q.x, q.z)))) return false;
            if (Physics.OverlapSphere(q, 0.001f, ~0, QueryTriggerInteraction.Ignore).Any(c => c != own)) return false;
            var hit = Physics.RaycastAll(q, n, 3f, ~0, QueryTriggerInteraction.Ignore).Where(h => h.collider != own).OrderBy(h => h.distance).FirstOrDefault();
            return hit.collider == null || Vector3.Dot(hit.normal, n) <= 0.5f;
        }
        bool Foliage(MeshRenderer r) => new[] { "leaves", "bract" }.Any(w => r.name.ToLower().Contains(w));
        bool Allowed(MeshRenderer a, MeshRenderer b) =>
            ClashAllowed.Contains(a.name + "|" + b.name) || Foliage(a) || Foliage(b)                                // foliage rests against and grows through things
            || (a.name.Contains("newel") && b.name.StartsWith("service_") && !b.name.Contains("spindle"))               // a post stands through the steps it carries
            || (a.transform.parent != null && a.transform.parent == b.transform.parent && a.transform.parent.name != "MainStair_HiFi"
                && a.transform.parent.parent?.name == "FoyerFixtures");                                                     // a fixture's own parts (candles in their cups)
        bool Raw(int pr, int R, Vector3 hit, (int r, Vector3 a, Vector3 b, Vector3 c) E, (int r, Vector3 a, Vector3 b, Vector3 c) F)
        {
            raw.TryGetValue((pr, R), out var rn); raw[(pr, R)] = rn + 1;
            bool In((int r, Vector3 a, Vector3 b, Vector3 c) t) { var lo = Vector3.Min(t.a, Vector3.Min(t.b, t.c)) - Vector3.one * 1e-3f; var hi = Vector3.Max(t.a, Vector3.Max(t.b, t.c)) + Vector3.one * 1e-3f; return hit.x >= lo.x && hit.y >= lo.y && hit.z >= lo.z && hit.x <= hi.x && hit.y <= hi.y && hit.z <= hi.z; }
            if (!In(E) || !In(F)) Debug.Log($"CheckBench: old clash hit OUTSIDE a box (the new loop never tests it): {rs[pr].name}|{rs[R].name} hit {hit:F4} E {E.a:F4} {E.b:F4} {E.c:F4} F {F.a:F4} {F.b:F4} {F.c:F4} inE {In(E)} inF {In(F)}");
            return true;
        }
        var seen = new HashSet<(int, int)>(); var found = new Dictionary<(int, int), (int n, Vector3 at)>();
        foreach (var l in grid.Values)
            for (int i = 0; i < l.Count; i++)
                for (int j = i + 1; j < l.Count; j++)
                {
                    int ti = l[i], tj = l[j]; var A = tris[ti]; var Bt = tris[tj];
                    if (A.r == Bt.r || !seen.Add(ti < tj ? (ti, tj) : (tj, ti))) continue;
                    foreach (var (E, F, R, pr) in new[] { (A, Bt, Bt.r, A.r), (Bt, A, A.r, Bt.r) })   // edges of E through face of F
                    {
                        var n = Vector3.Cross(F.b - F.a, F.c - F.a).normalized;
                        foreach (var (e0, e1) in new[] { (E.a, E.b), (E.b, E.c), (E.c, E.a) })
                            if (SegTri(e0, e1, F.a, F.b, F.c, out var hit) && Raw(pr, R, hit, E, F) && Through(pr, R, hit, n) && Visible(pr, hit, n))
                            {
                                var key = (pr, R); found.TryGetValue(key, out var acc); found[key] = (acc.n + 1, acc.n == 0 ? hit : acc.at); break;
                            }
                    }
                }
        Physics.queriesHitBackfaces = back; foreach (var c in temp) Object.DestroyImmediate(c); Physics.SyncTransforms();
        foreach (var f in found) foundOut[f.Key] = f.Value;
        var bad = found.Where(f => !Allowed(rs[f.Key.Item1], rs[f.Key.Item2])).OrderByDescending(f => f.Value.n).ToList();
        string P(MeshRenderer r) { var t = r.transform; string s = t.name; for (int q = 0; q < 2 && t.parent; q++) { t = t.parent; s = t.name + "/" + s; } return s; }
        var o = new System.Text.StringBuilder($"Clash check: {tris.Count} triangles, {bad.Count} parts passing through another ({found.Count - bad.Count} allowed joints)\n");
        foreach (var f in bad.Take(40))
            o.AppendLine($"CLASH   {P(rs[f.Key.Item1])} through {P(rs[f.Key.Item2])}: {f.Value.n} crossings, first at spec ({f.Value.at.x:F2}, {f.Value.at.y:F2}, {-f.Value.at.z:F2})");
        return o.ToString();
    }

}
