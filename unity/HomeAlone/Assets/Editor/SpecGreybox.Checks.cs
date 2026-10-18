using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;
using Unity.Collections;

// Surface checks the build runs (walk-test-wallgrid.txt): seams between structural boxes, and z-fighting across every
// visible mesh. Skill: .claude/skills/zfight-check.
public static partial class SpecGreybox
{
    // Seams (Oct 15, user: "walls and ceilings must line up"): every exposed face of the structural boxes (walls, headers,
    // floors, ceilings, stair structure; not trim, rails, props or dressing) against every other one facing the same way.
    //   OVERLAP: coplanar within 1 cm, overlapping, different materials (flicker / z-fighting)
    //   LEDGE:   the same surface continued 0.5-6 cm off its plane, stacked or end to end (a visible step)
    //   GAP:     coplanar but 0.5-10 cm short of meeting along the surface (a slit)
    // A face covered by a touching box (back-to-back walls) is internal and skipped.
    // Rooms as volumes for the seam check: (polygon, floor y, top y). Stairwells span from the floor below to their ceiling.
    static List<(List<Vector2> pts, float y0, float y1)> SeamRooms = new();

    // Z-fighting (user, Oct 16: "we're running into it a lot"): every triangle of every visible mesh in the house (grey-box,
    // dressing, Blender models, fixtures), not just the structural boxes. Two surfaces of different materials that face the
    // same way, lie within 1 cm of the same plane and overlap by more than 50 cm2 (about 7 x 7 cm; smaller contacts are flush mounts
    // such as a fixture canopy on a ceiling or a baluster against a newel), seen from a room, flicker. Rule: an
    // overlay sits >= 1 cm off what it covers, or the covered face is removed. Skill: .claude/skills/zfight-check.
    static string ZFightCheck(params GameObject[] roots)
    {
        bool InRoom(Vector3 q) => SeamRooms.Any(r => q.y > r.y0 + 0.002f && q.y < r.y1 - 0.002f && Inside(r.pts, new Vector2(q.x, q.z)));
        // A point in a window reveal or a wall recess (inside the wall's thickness, outside every room outline) is seen when a clear
        // straight line of up to 0.6 m leads from it into a room (Oct 17: the landing window's stool on the wall top was missed)
        var dirs = new[] { Vector3.right, Vector3.left, Vector3.forward, Vector3.back };
        bool Seen(Vector3 q, Vector3 n)
        {
            if (InRoom(q)) return true;
            foreach (var d in dirs.Append(n))
                for (float s = 0.05f; s <= 0.6f; s += 0.05f)
                    if (InRoom(q + d * s)) { if (!Physics.Raycast(q, d, s, ~0, QueryTriggerInteraction.Ignore)) return true; break; }
            return false;
        }
        var (tris, surf, unreadable) = ZTris(roots);
        // a face is hidden when the point just in front of it is inside a solid: primitive colliders by overlap, meshes (given
        // temporary colliders) by hitting a face from behind
        var temp = new List<Collider>();
        foreach (var r in surf.Select(x => x.r).Distinct())
            if (r.GetComponent<Collider>() == null) { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; temp.Add(mc); }
        Physics.SyncTransforms(); bool back = Physics.queriesHitBackfaces; Physics.queriesHitBackfaces = true;
        bool Hidden(Vector3 at, Vector3 n)
        {
            var q = at + n * 0.004f;
            if (Physics.CheckSphere(q, 0.001f, ~0, QueryTriggerInteraction.Ignore)) return true;
            return Physics.Raycast(q, n, out var h, 3f, ~0, QueryTriggerInteraction.Ignore) && Vector3.Dot(h.normal, n) > 0.5f;
        }
        var pairs = ZPairs(tris, surf, (at, n) => Seen(at + n * 0.02f, n) && !Hidden(at, n));
        Physics.queriesHitBackfaces = back; foreach (var c in temp) Object.DestroyImmediate(c); Physics.SyncTransforms();
        string P(MeshRenderer r) { var t = r.transform; string s = t.name; for (int q = 0; q < 2 && t.parent; q++) { t = t.parent; s = t.name + "/" + s; } return s; }
        var bad = pairs.Where(p => p.Value.area > 0.005f).OrderByDescending(p => p.Value.area).ToList();
        var o = new System.Text.StringBuilder($"Z-fight check: {tris.Count} triangles, {surf.Count} surfaces, {bad.Count} coplanar pairs seen from rooms" + (unreadable.Count > 0 ? $" ({unreadable.Count} meshes NOT checked, unreadable: {string.Join(", ", unreadable.Distinct().Take(12))})" : " (every visible mesh checked)") + "\n");
        foreach (var p in bad.Take(40))
            o.AppendLine($"ZFIGHT  {P(surf[p.Key.Item1].r)} [{surf[p.Key.Item1].m?.name}] vs {P(surf[p.Key.Item2].r)} [{surf[p.Key.Item2].m?.name}]: {p.Value.gap * 1000:F1} mm apart, {p.Value.area:F3} m2, at spec ({p.Value.at.x:F2}, {p.Value.at.y:F2}, {-p.Value.at.z:F2})");
        return o.ToString();
    }

    // every triangle of every visible readable mesh, in world space; a surface is one renderer's submesh, and its triangles are contiguous
    internal static (List<(int s, Vector3 a, Vector3 b, Vector3 c, Vector3 n, float d)>, List<(MeshRenderer r, Material m)>, List<string>) ZTris(GameObject[] roots)
    {
        var tris = new List<(int s, Vector3 a, Vector3 b, Vector3 c, Vector3 n, float d)>(); var surf = new List<(MeshRenderer r, Material m)>();
        var unread = new List<string>();
        foreach (var r in roots.Where(o => o != null).SelectMany(o => o.GetComponentsInChildren<MeshRenderer>()))
        {
            if (!r.enabled || r.shadowCastingMode == ShadowCastingMode.ShadowsOnly) continue;
            var mesh = r.GetComponent<MeshFilter>()?.sharedMesh; if (mesh == null) continue;
            var (v, sub) = ReadMesh(mesh); if (v == null) { unread.Add(r.name); continue; }
            var M = r.transform.localToWorldMatrix; float flip = M.determinant < 0 ? -1f : 1f;   // a mirrored part (store_props "mirror") draws its faces flipped
            for (int i = 0; i < v.Length; i++) v[i] = M.MultiplyPoint3x4(v[i]);
            for (int sm = 0; sm < sub.Length; sm++)
            {
                int sid = surf.Count; surf.Add((r, r.sharedMaterials[Mathf.Min(sm, r.sharedMaterials.Length - 1)]));
                var t = sub[sm];
                for (int k = 0; k < t.Length; k += 3)
                {
                    Vector3 a = v[t[k]], b = v[t[k + 1]], c = v[t[k + 2]]; var cr = Vector3.Cross(b - a, c - a);
                    if (cr.magnitude < 2e-6f) continue;
                    var n = cr.normalized * flip; tris.Add((sid, a, b, c, n, Vector3.Dot(n, a)));
                }
            }
        }
        return (tris, surf, unread);
    }

    // a mesh's vertices and per-submesh triangles, readable or not: an imported model with Read/Write off (25 of them on Oct 17,
    // LandingWindow among them) is read through MeshData, which the Editor allows; null only if even that fails (named in the report)
    internal static (Vector3[] v, int[][] sub) ReadMesh(Mesh mesh)
    {
        if (mesh.isReadable) return (mesh.vertices, Enumerable.Range(0, mesh.subMeshCount).Select(mesh.GetTriangles).ToArray());
        try
        {
            using var md = Mesh.AcquireReadOnlyMeshData(mesh); var d = md[0];
            using var nv = new NativeArray<Vector3>(d.vertexCount, Allocator.Temp); d.GetVertices(nv);
            var sub = new int[d.subMeshCount][];
            for (int sm = 0; sm < sub.Length; sm++)
            {
                if (d.GetSubMesh(sm).topology != MeshTopology.Triangles) { sub[sm] = new int[0]; continue; }
                using var ni = new NativeArray<int>(d.GetSubMesh(sm).indexCount, Allocator.Temp); d.GetIndices(ni, sm); sub[sm] = ni.ToArray();
            }
            return (nv.ToArray(), sub);
        }
        catch (System.Exception) { return (null, null); }
    }

    // Coplanar pairs (check speed, Oct 17: the old loop compared every pair in a plane bucket, O(k^2), 25 min 43 s on 1.2M triangles).
    // Triangles are bucketed by plane exactly as before (normal to 1/50, offset in 1 cm slabs; this slab and the next), then by a
    // 25 cm grid in the plane. A pair is examined only when its in-plane boxes overlap (within 2 cm), once, in the first grid cell
    // they share; a surface's own triangles are contiguous and skipped as a run. Boxes apart by more than 2 cm have no overlap area,
    // so the pairs are the old loop's (proof: old vs new on the built house, zfight-check skill "Check speed").
    // keep(at, n): the overlap point counts (seen from a room, not hidden). raw: every overlapping pair before keep (for the proof).
    internal static Dictionary<(int, int), (float area, float gap, Vector3 at)> ZPairs(List<(int s, Vector3 a, Vector3 b, Vector3 c, Vector3 n, float d)> tris,
        List<(MeshRenderer r, Material m)> surf, System.Func<Vector3, Vector3, bool> keep, Dictionary<(int, int), (float area, float gap, Vector3 at)> raw = null)
    {
        const float Cell = 0.25f, Half = 0.01f;   // grid cell; each box grows by Half on every side (2 cm between boxes)
        var clock = System.Diagnostics.Stopwatch.StartNew();
        (int, int, int, int) Key(Vector3 n, float d) => (Mathf.RoundToInt(n.x * 50), Mathf.RoundToInt(n.y * 50), Mathf.RoundToInt(n.z * 50), Mathf.FloorToInt(d / 0.01f));
        var start = new int[surf.Count]; var end = new int[surf.Count];
        for (int i = tris.Count - 1; i >= 0; i--) start[tris[i].s] = i;
        for (int i = 0; i < tris.Count; i++) end[tris[i].s] = i + 1;
        var mid = new Dictionary<Material, int>(); var mat = surf.Select(x => x.m == null ? -1 : mid.TryGetValue(x.m, out var q) ? q : mid[x.m] = mid.Count).ToArray();   // material as an int
        var basis = new Dictionary<(int, int, int), (Vector3 u, Vector3 w)>();
        var keys = new (int, int, int, int)[tris.Count];
        var bx = new (float u0, float u1, float w0, float w1, int cu0, int cw0, int cu1, int cw1)[tris.Count];
        var grid = new Dictionary<(int, int, int, int, int, int), List<int>>();
        for (int i = 0; i < tris.Count; i++)
        {
            var t = tris[i]; var k = keys[i] = Key(t.n, t.d); var nk = (k.Item1, k.Item2, k.Item3);
            if (t.n.sqrMagnitude < 0.5f) { bx[i].cu0 = 1; bx[i].cu1 = 0; continue; }   // a sliver (Vector3.normalized gave zero): it pairs with nothing (dot 0)
            if (!basis.TryGetValue(nk, out var b))
            {   // one basis per bucket normal, so boxes in a bucket are comparable
                var nn = new Vector3(k.Item1, k.Item2, k.Item3).normalized;
                var u = Vector3.Cross(nn, Mathf.Abs(nn.y) < 0.9f ? Vector3.up : Vector3.right).normalized;
                basis[nk] = b = (u, Vector3.Cross(nn, u));
            }
            float ua = Vector3.Dot(t.a, b.u), ub = Vector3.Dot(t.b, b.u), uc = Vector3.Dot(t.c, b.u);
            float wa = Vector3.Dot(t.a, b.w), wb = Vector3.Dot(t.b, b.w), wc = Vector3.Dot(t.c, b.w);
            float u0 = Mathf.Min(ua, Mathf.Min(ub, uc)) - Half, u1 = Mathf.Max(ua, Mathf.Max(ub, uc)) + Half;
            float w0 = Mathf.Min(wa, Mathf.Min(wb, wc)) - Half, w1 = Mathf.Max(wa, Mathf.Max(wb, wc)) + Half;
            var e = bx[i] = (u0, u1, w0, w1, Mathf.FloorToInt(u0 / Cell), Mathf.FloorToInt(w0 / Cell), Mathf.FloorToInt(u1 / Cell), Mathf.FloorToInt(w1 / Cell));
            for (int cu = e.cu0; cu <= e.cu1; cu++) for (int cw = e.cw0; cw <= e.cw1; cw++)
            {
                var gk = (k.Item1, k.Item2, k.Item3, k.Item4, cu, cw);
                if (!grid.TryGetValue(gk, out var l)) grid[gk] = l = new List<int>(); l.Add(i);   // ascending: i only grows
            }
        }
        var pairs = new Dictionary<(int, int), (float area, float gap, Vector3 at)>();
        long examined = 0, overlaps = 0, visits = 0; float tGrid = (float)clock.Elapsed.TotalSeconds;
        for (int i = 0; i < tris.Count; i++)
        {
            if ((i & 4095) == 0) BudgetGuard();
            var ti = tris[i]; var k = keys[i]; var bi = bx[i]; int s0 = start[ti.s], s1 = end[ti.s];
            for (int dd = 0; dd <= 1; dd++)   // the same and the next 1 cm slab (each pair once)
                for (int cu = bi.cu0; cu <= bi.cu1; cu++) for (int cw = bi.cw0; cw <= bi.cw1; cw++)
                {
                    if (!grid.TryGetValue((k.Item1, k.Item2, k.Item3, k.Item4 + dd, cu, cw), out var l)) continue;
                    int p = dd == 0 ? l.BinarySearch(s1) : 0; if (p < 0) p = ~p;   // same slab: only later surfaces (j > i, not i's own)
                    for (; p < l.Count; p++)
                    {
                        int j = l[p]; visits++;
                        if (j >= s0 && j < s1) { p = l.BinarySearch(s1); p = (p < 0 ? ~p : p) - 1; continue; }   // i's own surface, as a run
                        var bj = bx[j];
                        if (bi.u1 < bj.u0 || bj.u1 < bi.u0 || bi.w1 < bj.w0 || bj.w1 < bi.w0) continue;
                        if (cu != Mathf.Max(bi.cu0, bj.cu0) || cw != Mathf.Max(bi.cw0, bj.cw0)) continue;   // only in the first shared cell
                        var tj = tris[j]; examined++;
                        if (mat[tj.s] == mat[ti.s] || Vector3.Dot(ti.n, tj.n) < 0.999f) continue;
                        float gap = Mathf.Abs(tj.d - ti.d); if (gap >= 0.01f) continue;
                        var (area, at) = Overlap(ti.a, ti.b, ti.c, tj.a, tj.b, tj.c, ti.n);
                        if (area < 1e-5f) continue;
                        overlaps++;
                        var key = ti.s < tj.s ? (ti.s, tj.s) : (tj.s, ti.s);
                        if (raw != null) { raw.TryGetValue(key, out var r0); raw[key] = (r0.area + area, r0.area == 0 ? gap : Mathf.Min(r0.gap, gap), r0.area == 0 ? at : r0.at); }
                        if (!keep(at, ti.n)) continue;
                        pairs.TryGetValue(key, out var acc);
                        pairs[key] = (acc.area + area, acc.area == 0 ? gap : Mathf.Min(acc.gap, gap), acc.area == 0 ? at : acc.at);
                    }
                }
        }
        Debug.Log($"ZPairs: {tris.Count} triangles, {grid.Count} cells (grid {tGrid:F1} s), {visits} list visits, {examined} pairs examined, {overlaps} overlapping, {clock.Elapsed.TotalSeconds:F1} s");
        return pairs;
    }

    // overlap area of two triangles on (nearly) one plane, and a point inside the overlap: project onto the plane, clip one by the other
    // (fixed buffers, no allocation: it runs for every examined pair; same arithmetic as the List version it replaced)
    static readonly Vector2[] OvA = new Vector2[32], OvB = new Vector2[32];
    static (float, Vector3) Overlap(Vector3 a0, Vector3 b0, Vector3 c0, Vector3 a1, Vector3 b1, Vector3 c1, Vector3 n)
    {
        var u = Vector3.Cross(n, Mathf.Abs(n.y) < 0.9f ? Vector3.up : Vector3.right).normalized; var w = Vector3.Cross(n, u);
        Vector2 Pj(Vector3 p) => new Vector2(Vector3.Dot(p, u), Vector3.Dot(p, w));
        float Cr(Vector2 p, Vector2 q, Vector2 r) => (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x);
        var poly = OvA; var outp = OvB; int cnt = 3;
        poly[0] = Pj(a0); poly[1] = Pj(b0); poly[2] = Pj(c0);
        Vector2 k0 = Pj(a1), k1 = Pj(b1), k2 = Pj(c1);
        if (Cr(poly[0], poly[1], poly[2]) < 0) { var x = poly[0]; poly[0] = poly[2]; poly[2] = x; }
        if (Cr(k0, k1, k2) < 0) { var x = k0; k0 = k2; k2 = x; }
        for (int e = 0; e < 3 && cnt > 0; e++)
        {
            Vector2 p = e == 0 ? k0 : e == 1 ? k1 : k2, q = e == 0 ? k1 : e == 1 ? k2 : k0; int m = 0;
            for (int i = 0; i < cnt; i++)
            {
                Vector2 s = poly[i], t = poly[(i + 1) % cnt]; float cs = Cr(p, q, s), ct = Cr(p, q, t);
                if (cs >= 0) outp[m++] = s;
                if ((cs >= 0) != (ct >= 0)) outp[m++] = s + (t - s) * (cs / (cs - ct));
            }
            var sw = poly; poly = outp; outp = sw; cnt = m;
        }
        if (cnt < 3) return (0f, Vector3.zero);
        float area = 0; Vector2 cen = Vector2.zero;
        for (int i = 0; i < cnt; i++) { area += Cr(Vector2.zero, poly[i], poly[(i + 1) % cnt]) / 2; cen += poly[i]; }
        cen /= cnt; float h = Vector3.Dot(a0, n);
        return (Mathf.Abs(area), u * cen.x + w * cen.y + n * h);
    }

    static string SeamCheck(params GameObject[] roots)
    {
        // only surfaces seen from inside a room count: the point just in front of a face must be in a room's open volume
        bool Seen(Vector3 q) => SeamRooms.Any(r => q.y > r.y0 + 0.002f && q.y < r.y1 - 0.002f && Inside(r.pts, new Vector2(q.x, q.z)));
        string[] skip = { "Dressing", "Furniture", "Rail", "Spindle", "spindle", "_cap", "Casing", "PropDoor", "Window", "Glass", "Stool", "Apron", "Light", "Walker", "Outdoors", "Arch_Spandrel", "ShadowCap", "Envelope", "FilmFront", "_tread", "_riser", "stringer", "newel", "_HiFi", "_Gen", "Fixtures", "Trim" };   // generated models and fixtures: the z-fight and clash checks cover them   // an arch's curve is stepped on purpose (grey-box)
        var boxes = roots.Where(r => r != null).SelectMany(r => r.GetComponentsInChildren<MeshRenderer>())
            .Where(m => !skip.Any(k => m.name.Contains(k) || (m.transform.parent != null && m.transform.parent.name.Contains(k)) ||
                                        (m.transform.parent?.parent != null && m.transform.parent.parent.name.Contains(k))))
            .Where(m => Quaternion.Angle(m.transform.rotation, Quaternion.identity) < 0.1f)
            .Select(m => (m, b: m.bounds)).ToList();
        var faces = new List<(int box, int ax, float c, int n, Vector2 lo, Vector2 hi)>();
        for (int i = 0; i < boxes.Count; i++)
            for (int ax = 0; ax < 3; ax++)
            {
                var b = boxes[i].b; int u = (ax + 1) % 3, v = (ax + 2) % 3;
                var lo = new Vector2(b.min[u], b.min[v]); var hi = new Vector2(b.max[u], b.max[v]);
                faces.Add((i, ax, b.min[ax], -1, lo, hi)); faces.Add((i, ax, b.max[ax], 1, lo, hi));
            }
        float Ov(float a0, float a1, float b0, float b1) => Mathf.Min(a1, b1) - Mathf.Max(a0, b0);
        Vector3 P(int ax, float c, float a, float b) { var q = Vector3.zero; q[ax] = c; q[(ax + 1) % 3] = a; q[(ax + 2) % 3] = b; return q; }
        bool Solid(Vector3 q, int not = -1) { for (int k = 0; k < boxes.Count; k++) if (k != not && boxes[k].b.Contains(q)) return true; return false; }
        // internal: the point just outside the face's centre is inside another box (back-to-back walls, a ceiling's edge in a wall)
        var exposed = faces.Where(f => { var q = P(f.ax, f.c + f.n * 0.003f, (f.lo.x + f.hi.x) / 2, (f.lo.y + f.hi.y) / 2); return !Solid(q, f.box) && Seen(q); }).ToList();
        var lines = new List<string>(); int over = 0, ledge = 0, gap = 0;
        string Where(int i) { var c = boxes[i].b.center; return $"{boxes[i].m.transform.parent?.name}/{boxes[i].m.name} at ({c.x:F2}, {c.y:F2}, {-c.z:F2})"; }
        string[] axn = { "x", "y", "z" };
        for (int i = 0; i < exposed.Count; i++)
            for (int j = i + 1; j < exposed.Count; j++)
            {
                var f = exposed[i]; var g = exposed[j];
                if (f.box == g.box || f.ax != g.ax || f.n != g.n) continue;
                float d = Mathf.Abs(f.c - g.c);
                if (d > 0.06f) continue;
                float ou = Ov(f.lo.x, f.hi.x, g.lo.x, g.hi.x), ov = Ov(f.lo.y, f.hi.y, g.lo.y, g.hi.y);
                if (d < 0.01f && ou > 0.05f && ov > 0.05f)
                {
                    if (boxes[f.box].m.sharedMaterial != boxes[g.box].m.sharedMaterial)
                    { over++; if (over <= 40) lines.Add($"OVERLAP {axn[f.ax]}={f.c:F3}/{g.c:F3}: {Where(f.box)} | {Where(g.box)}"); }
                }
                else if (d >= 0.005f && ((ou > 0.05f && Mathf.Abs(ov) < 0.02f && ov <= 0.02f) || (ov > 0.05f && Mathf.Abs(ou) < 0.02f && ou <= 0.02f)))
                { ledge++; if (ledge <= 200) lines.Add($"LEDGE   {axn[f.ax]} {f.c:F3} vs {g.c:F3} ({d * 100:F1} cm): {Where(f.box)} | {Where(g.box)}"); }
                else if (d < 0.005f && ((ou > 0.05f && ov < -0.005f && ov > -0.10f) || (ov > 0.05f && ou < -0.005f && ou > -0.10f)))
                {   // a slit only if it is empty just behind the surface (a wall or slab filling it is a joint, not a gap)
                    bool alongU = ov < 0;
                    float a = alongU ? (Mathf.Max(f.lo.x, g.lo.x) + Mathf.Min(f.hi.x, g.hi.x)) / 2 : (Mathf.Min(f.hi.x, g.hi.x) + Mathf.Max(f.lo.x, g.lo.x)) / 2;
                    float b = alongU ? (Mathf.Min(f.hi.y, g.hi.y) + Mathf.Max(f.lo.y, g.lo.y)) / 2 : (Mathf.Max(f.lo.y, g.lo.y) + Mathf.Min(f.hi.y, g.hi.y)) / 2;
                    if (Solid(P(f.ax, f.c - f.n * 0.01f, a, b)) || !Seen(P(f.ax, f.c + f.n * 0.01f, a, b))) continue;
                    gap++; if (gap <= 200) lines.Add($"GAP     {axn[f.ax]}={f.c:F3} ({-Mathf.Min(ou, ov) * 100:F1} cm): {Where(f.box)} | {Where(g.box)}");
                }
            }
        foreach (var (hp, what) in HoleProbes)   // thresholds and outside corners must be solid (a hole there sees the outdoors)
            if (!Solid(hp)) { gap++; if (gap <= 200) lines.Add($"GAP     hole at {what}: ({hp.x:F2}, {hp.y:F2}, {-hp.z:F2}) is empty"); }
        lines.Insert(0, $"Seam check: {boxes.Count} structural boxes, {over} overlaps (flicker), {ledge} ledges, {gap} gaps");
        return string.Join("\n", lines) + "\n";
    }

    // Leaks: from a 0.5 m grid at eye height in every space (both floors), rays go up and in 16 horizontal directions.
    // A ray that hits nothing within 40 m escaped the house (a hole to the sky or outside). Window glass has a collider,
    // so every escape is a defect. Headroom: on the ground floor, any grid point with < 2.0 m clear above the floor is
    // reported with the object above it; only the main stair's flight 1 (steps, rails) may stand there.

    // Clashes (user, Oct 16 08:40: "the wainscotting clashes with the balusters ... how do we detect these sorts of things"):
    // one part passing THROUGH another, i.e. crossing a surface and coming out more than 2 cm on both sides of it near the
    // crossing. A part that ends inside another (a baluster planted in a tread, a rail into a newel) is a joint, not a clash.
    // Joints that do pass through by construction are listed in ClashAllowed as "piercer|pierced" renderer names.
    static readonly string[] ClashAllowed = {
        "Newels|Treads", "Newels|Runner", "Newels|RisersStringers",   // posts stand through the steps they carry
        "Treads|Newels",                                              // a newel stands on its tread
        "Newels|Rail", "Rail|Newels",                                 // a handrail dies into its newel (runs end at the post's centre)
        "Balusters|RisersStringers", "RisersStringers|Treads",        // balusters into the cut stringer; treads housed in the skirt board
        "StairWallTrim|Treads",                                       // the old path's skirt board (hifi_foyer.py StairWallTrim part)
        "Arch_Spandrel|Arch_Spandrel" };                              // the grey-box arch is stepped slices on purpose
    static string ClashCheck(params GameObject[] roots) => ClashCheck(roots, null, null);
    // found: every crossing pair (piercer, pierced) before the allowed list; raw: edge-through-face hits per pair before the
    // through/visible tests (both for the old-vs-new proof)
    internal static string ClashCheck(GameObject[] roots, Dictionary<(int, int), (int n, Vector3 at)> foundOut, Dictionary<(int, int), int> raw)
    {
        var rs = roots.Where(o => o != null).SelectMany(o => o.GetComponentsInChildren<MeshRenderer>())
            .Where(r => r.enabled && r.shadowCastingMode != ShadowCastingMode.ShadowsOnly && r.GetComponent<MeshFilter>()?.sharedMesh != null).ToList();
        var md = rs.Select(r => ReadMesh(r.GetComponent<MeshFilter>().sharedMesh)).ToList();   // unreadable imports too (via MeshData)
        var unread = rs.Where((r, k) => md[k].v == null).Select(r => r.name).ToList();
        rs = rs.Where((r, k) => md[k].v != null).ToList(); md = md.Where(x => x.v != null).ToList();
        var verts = rs.Select((r, k) => { var v = md[k].v; var M = r.transform.localToWorldMatrix; for (int i = 0; i < v.Length; i++) v[i] = M.MultiplyPoint3x4(v[i]); return v; }).ToList();
        var tris = new List<(int r, Vector3 a, Vector3 b, Vector3 c)>();
        for (int k = 0; k < rs.Count; k++) { var v = verts[k]; foreach (var t in md[k].sub) for (int i = 0; i < t.Length; i += 3) tris.Add((k, v[t[i]], v[t[i + 1]], v[t[i + 2]])); }
        const float cell = 0.1f; var grid = new Dictionary<(int, int, int), List<int>>();
        var box = new (Vector3 lo, Vector3 hi, int x0, int y0, int z0)[tris.Count];
        for (int i = 0; i < tris.Count; i++)
        {
            var t = tris[i]; var lo = Vector3.Min(t.a, Vector3.Min(t.b, t.c)); var hi = Vector3.Max(t.a, Vector3.Max(t.b, t.c));
            box[i] = (lo - Vector3.one * 1e-3f, hi + Vector3.one * 1e-3f, Mathf.FloorToInt(lo.x / cell), Mathf.FloorToInt(lo.y / cell), Mathf.FloorToInt(lo.z / cell));
            if ((hi - lo).magnitude > 4f) continue;   // big planes (whole walls, floors) are pierced only by structure, which the seam check covers
            for (int x = Mathf.FloorToInt(lo.x / cell); x <= Mathf.FloorToInt(hi.x / cell); x++)
                for (int y = Mathf.FloorToInt(lo.y / cell); y <= Mathf.FloorToInt(hi.y / cell); y++)
                    for (int z = Mathf.FloorToInt(lo.z / cell); z <= Mathf.FloorToInt(hi.z / cell); z++)
                    { if (!grid.TryGetValue((x, y, z), out var l)) grid[(x, y, z)] = l = new List<int>(); l.Add(i); }   // ascending
        }
        var rEnd = new int[rs.Count]; for (int i = 0; i < tris.Count; i++) rEnd[tris[i].r] = i + 1;   // a renderer's triangles are contiguous
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
        var vgrid = new Dictionary<int, Dictionary<(int, int, int), List<int>>>();
        (int, int, int) VCell(Vector3 p) => (Mathf.FloorToInt(p.x / 0.06f), Mathf.FloorToInt(p.y / 0.06f), Mathf.FloorToInt(p.z / 0.06f));
        bool Through(int piercer, int pierced, Vector3 at, Vector3 n)
        {   // does the piercer's surface within 6 cm of the crossing reach more than 2 cm past both sides of the pierced part (its
            // face and its far side)? Vertices, not the crossing edge: one long edge spans any thin part. 6 cm keeps a merged
            // mesh's neighbouring pieces (the next tread up) out of the test.
            float mn = 0, mx = 0; var vs = verts[piercer];
            if (!vgrid.TryGetValue(piercer, out var vg))
            {   // the piercer's vertices in 6 cm cells, built once: a crossing reads 27 cells instead of every vertex of a merged mesh
                vgrid[piercer] = vg = new Dictionary<(int, int, int), List<int>>();
                for (int i = 0; i < vs.Length; i++) { var c = VCell(vs[i]); if (!vg.TryGetValue(c, out var cl)) vg[c] = cl = new List<int>(); cl.Add(i); }
            }
            var c0 = VCell(at);
            for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) for (int dz = -1; dz <= 1; dz++)
                if (vg.TryGetValue((c0.Item1 + dx, c0.Item2 + dy, c0.Item3 + dz), out var cl))
                    foreach (int i in cl) { var v = vs[i]; if ((v - at).sqrMagnitude > 0.06f * 0.06f) continue; float sd = Vector3.Dot(v - at, n); mn = Mathf.Min(mn, sd); mx = Mathf.Max(mx, sd); }
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
                && (a.transform.parent.parent?.name == "FoyerFixtures"                                                    // a fixture's own parts (candles in their cups)
                    || a.transform.parent.parent?.name == "StoreProps" || a.transform.parent.parent?.name == "SketchfabProps"
                    || a.transform.parent.parent?.name == "PurchasedRug_HiFi"));   // a bought rug's fringe knotted into its body (purchased_rugs.py)   // ...or a Sketchfab download's (the rifle's tube through its receiver)                                                 // a bought model's own parts (the wreath's bow through its fir tips)
        // each triangle pair once, in the first cell both boxes share (no pair set), only when the boxes meet (a crossing lies in both),
        // never within one renderer (its run is skipped by index); the same pairs as testing every pair of a cell (check speed, Oct 17)
        var found = new Dictionary<(int, int), (int n, Vector3 at)>(); long examined = 0, hits = 0; int cells = 0;
        foreach (var kv in grid)
        {
            if ((cells++ & 1023) == 0) BudgetGuard();
            var l = kv.Value; var (cx, cy, cz) = kv.Key;
            for (int i = 0; i < l.Count; i++)
            {
                int ti = l[i]; var A = tris[ti]; var ba = box[ti];
                int j = l.BinarySearch(rEnd[A.r]); j = j < 0 ? ~j : j;   // later renderers only
                for (; j < l.Count; j++)
                {
                    int tj = l[j]; var bb = box[tj];
                    if (cx != Mathf.Max(ba.x0, bb.x0) || cy != Mathf.Max(ba.y0, bb.y0) || cz != Mathf.Max(ba.z0, bb.z0)) continue;
                    if (ba.hi.x < bb.lo.x || bb.hi.x < ba.lo.x || ba.hi.y < bb.lo.y || bb.hi.y < ba.lo.y || ba.hi.z < bb.lo.z || bb.hi.z < ba.lo.z) continue;
                    var Bt = tris[tj]; examined++;
                    for (int dir = 0; dir < 2; dir++)   // edges of E through face of F
                    {
                        var (E, F) = dir == 0 ? (A, Bt) : (Bt, A); int R = F.r, pr = E.r;
                        var n = Vector3.Cross(F.b - F.a, F.c - F.a).normalized;
                        for (int e = 0; e < 3; e++)
                        {
                            Vector3 e0 = e == 0 ? E.a : e == 1 ? E.b : E.c, e1 = e == 0 ? E.b : e == 1 ? E.c : E.a;
                            if (!SegTri(e0, e1, F.a, F.b, F.c, out var hit)) continue;
                            hits++; if (raw != null) { raw.TryGetValue((pr, R), out var rn); raw[(pr, R)] = rn + 1; }
                            if (Through(pr, R, hit, n) && Visible(pr, hit, n))
                            {
                                var key = (pr, R); found.TryGetValue(key, out var acc); found[key] = (acc.n + 1, acc.n == 0 ? hit : acc.at); break;
                            }
                        }
                    }
                }
            }
        }
        Debug.Log($"ClashCheck: {tris.Count} triangles, {grid.Count} cells, {examined} pairs examined, {hits} edge crossings tested");
        Physics.queriesHitBackfaces = back; foreach (var c in temp) Object.DestroyImmediate(c); Physics.SyncTransforms();
        if (foundOut != null) foreach (var f in found) foundOut[f.Key] = f.Value;
        var bad = found.Where(f => !Allowed(rs[f.Key.Item1], rs[f.Key.Item2])).OrderByDescending(f => f.Value.n).ToList();
        string P(MeshRenderer r) { var t = r.transform; string s = t.name; for (int q = 0; q < 2 && t.parent; q++) { t = t.parent; s = t.name + "/" + s; } return s; }
        var o = new System.Text.StringBuilder($"Clash check: {tris.Count} triangles, {bad.Count} parts passing through another ({found.Count - bad.Count} allowed joints)" + (unread.Count > 0 ? $" ({unread.Count} meshes NOT checked, unreadable: {string.Join(", ", unread.Distinct().Take(12))})" : " (every visible mesh checked)") + "\n");
        foreach (var f in bad.Take(40))
            o.AppendLine($"CLASH   {P(rs[f.Key.Item1])} through {P(rs[f.Key.Item2])}: {f.Value.n} crossings, first at spec ({f.Value.at.x:F2}, {f.Value.at.y:F2}, {-f.Value.at.z:F2})");
        return o.ToString();
    }

    // Import triangle budget (Oct 17: a 628k-triangle rug made the z-fight gate run 27 min): every imported model (bought, CC0 or
    // generated GLB/FBX) used in the house, by asset file, counting each distinct mesh once. Over budget: decimate it or bake the
    // detail to a normal map (artist-pipeline skill), never raise the budget. Must read 0.
    const int ModelTriBudget = 150000;
    static string TriangleBudget(params GameObject[] roots)
    {
        var over = roots.Where(o => o != null).SelectMany(o => o.GetComponentsInChildren<MeshFilter>(true)).Select(f => f.sharedMesh)
            .Where(m => m != null && AssetDatabase.Contains(m)).Distinct()
            .GroupBy(m => AssetDatabase.GetAssetPath(m)).Select(g => (path: g.Key, tris: g.Sum(m => Enumerable.Range(0, m.subMeshCount).Sum(i => (long)m.GetIndexCount(i)) / 3)))
            .Where(x => x.tris > ModelTriBudget).OrderByDescending(x => x.tris).ToList();
        return $"Props triangle budget: {over.Count} models over {ModelTriBudget / 1000}k triangles" + (over.Count > 0 ? " (" + string.Join(", ", over.Select(x => $"{x.path} {x.tris / 1000}k")) + ")" : "") + "\n";
    }

    // Casings come from the same numbers as their opening (user note Oct 16 09:41: a casing placed by hand in the dressing stopped
    // short of the cut and showed into the vestibule): generated around a cut (Openings) or with its door in the spec (the basement
    // door, the back stair's well). A casing in the dressing or a model is a FAIL: make the opening cased instead.
    static string CasingCheck(params GameObject[] roots)
    {
        bool Placed(Transform t) { for (; t != null; t = t.parent) if (t.name == "Dressing" || t.name.EndsWith("_HiFi")) return true; return false; }
        var bad = roots.Where(o => o != null).SelectMany(o => o.GetComponentsInChildren<MeshRenderer>(true))
            .Where(r => r.name.ToLower().Contains("casing") && Placed(r.transform)).Select(r => r.transform.parent.name + "/" + r.name).ToList();
        return $"Casing check: {bad.Count} casings placed apart from their opening" + (bad.Count > 0 ? " (" + string.Join(", ", bad.Take(8)) + ")" : "") + "\n";
    }

    // Trim (user note Oct 16 11:13: a gap in the moulding; Oct 17 08:30: the stair's triangle and the landing's bare north wall, which the
    // room-outline version never looked at). Over EVERY visible face run of the face model (spec/trim_faces.json: room outlines, the main
    // stair's rakes and the landings' edges, merged where they touch; HOUSE-KERNEL step 1), every 2 cm, at each member's middle above
    // the run's line: a ray from 10 cm in front toward the face must meet trim or something mounted on the wall before bare wall; at the
    // wainscot panel's height a wall in the wainscot material is the panel. Points inside something solid are skipped. Bare wall over
    // 3 cm is a GAP. It reads the built scene, never the strips, and runs the same on either trim path, so the two are measured alike.
    static string TrimCheck()
    {
        var j = LoadTrimFaces(); string panelMat = TrimMat().name;
        var temp = new List<Collider>();
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (r.enabled && r.GetComponent<Collider>() == null && r.GetComponent<MeshFilter>()?.sharedMesh is Mesh mesh)
            { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mesh; temp.Add(mc); }
        Physics.SyncTransforms();
        var gaps = new List<string>(); int samples = 0, stairRuns = 0, byModel = 0; float length = 0f;
        foreach (var run in j["runs"])
        {
            string ax = (string)run["axis"], room = (string)run["room"]; float c = (float)run["c"], n = (float)run["n"];
            var pts = run["pts"].Select(p => new Vector2((float)p[0], (float)p[1])).ToList();
            float Line(float s) { for (int i = 0; i + 1 < pts.Count; i++) if (s <= pts[i + 1].x) return pts[i + 1].x - pts[i].x < 1e-6f ? pts[i + 1].y : Mathf.Lerp(pts[i].y, pts[i + 1].y, (s - pts[i].x) / (pts[i + 1].x - pts[i].x)); return pts[pts.Count - 1].y; }
            float s0 = pts[0].x, s1 = pts[pts.Count - 1].x; length += s1 - s0;
            if (room.StartsWith("stair")) stairRuns++; if (run["by"] != null && run["by"].Type != JTokenType.Null) byModel++;
            foreach (var smp in run["samples"])
            {
                float h = (float)smp["h"]; bool panel = smp["panel"] != null && (bool)smp["panel"];
                float g0 = -1f;
                void Close(float s)
                {
                    if (g0 >= 0f && s - g0 > 0.03f)
                    {
                        float m = (g0 + s) / 2; float y = Line(m) + h;
                        var spec = ax == "x" ? new Vector3(m, y, -c) : new Vector3(c, y, -m);
                        gaps.Add($"GAP     {s - g0:F2} m of bare wall {h:F2} above the line of the {room} run at spec ({spec.x:F2}, {spec.y:F2}, {spec.z:F2})");
                    }
                    g0 = -1f;
                }
                for (float s = s0 + 0.03f; s < s1 - 0.03f; s += 0.02f)
                {
                    samples++;
                    float y = Line(s) + h;
                    var o = ax == "x" ? new Vector3(s, y, c + n * 0.10f) : new Vector3(c + n * 0.10f, y, s);
                    var d = ax == "x" ? new Vector3(0, 0, -n) : new Vector3(-n, 0, 0);
                    bool bare = !Physics.CheckSphere(o, 0.005f, ~0, QueryTriggerInteraction.Ignore) && Physics.Raycast(o, d, out var hit, 0.14f, ~0, QueryTriggerInteraction.Ignore)
                                && hit.collider.name == "Wall" && hit.distance > 0.09f
                                && !(panel && hit.collider.GetComponent<MeshRenderer>()?.sharedMaterial?.name == panelMat);
                    if (bare && g0 < 0f) g0 = s; else if (!bare) Close(s);
                }
                Close(s1 - 0.03f);
            }
        }
        foreach (var c in temp) Object.DestroyImmediate(c);
        Physics.SyncTransforms();
        var ends = string.Join(", ", ((JObject)j["ends"]).Properties().Select(p => $"{p.Name} {p.Value}"));
        return $"Trim check: {j["runs"].Count()} face runs ({stairRuns} on the stair and landings, {byModel} panelled by a window model), {length:F1} m, {samples} samples, {gaps.Count} gaps in the baseboard, wainscot or cap rail; run ends: {ends}\n"
               + string.Concat(gaps.Take(30).Select(g => g + "\n"));
    }
}
