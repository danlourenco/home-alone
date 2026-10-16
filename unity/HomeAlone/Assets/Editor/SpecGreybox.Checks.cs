using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

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
        bool Seen(Vector3 q) => SeamRooms.Any(r => q.y > r.y0 + 0.002f && q.y < r.y1 - 0.002f && Inside(r.pts, new Vector2(q.x, q.z)));
        var tris = new List<(int s, Vector3 a, Vector3 b, Vector3 c, Vector3 n, float d)>(); var surf = new List<(MeshRenderer r, Material m)>();
        int unreadable = 0;
        foreach (var r in roots.Where(o => o != null).SelectMany(o => o.GetComponentsInChildren<MeshRenderer>()))
        {
            if (!r.enabled || r.shadowCastingMode == ShadowCastingMode.ShadowsOnly) continue;
            var mesh = r.GetComponent<MeshFilter>()?.sharedMesh; if (mesh == null) continue;
            if (!mesh.isReadable) { unreadable++; continue; }
            var v = mesh.vertices; var M = r.transform.localToWorldMatrix;
            for (int i = 0; i < v.Length; i++) v[i] = M.MultiplyPoint3x4(v[i]);
            for (int sm = 0; sm < mesh.subMeshCount; sm++)
            {
                int sid = surf.Count; surf.Add((r, r.sharedMaterials[Mathf.Min(sm, r.sharedMaterials.Length - 1)]));
                var t = mesh.GetTriangles(sm);
                for (int k = 0; k < t.Length; k += 3)
                {
                    Vector3 a = v[t[k]], b = v[t[k + 1]], c = v[t[k + 2]]; var cr = Vector3.Cross(b - a, c - a);
                    if (cr.magnitude < 2e-6f) continue;
                    var n = cr.normalized; tris.Add((sid, a, b, c, n, Vector3.Dot(n, a)));
                }
            }
        }
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
                    var (area, at) = Overlap(ti.a, ti.b, ti.c, tj.a, tj.b, tj.c, ti.n);
                    if (area < 1e-5f || !Seen(at + ti.n * 0.02f) || Hidden(at, ti.n)) continue;
                    var key = ti.s < tj.s ? (ti.s, tj.s) : (tj.s, ti.s);
                    pairs.TryGetValue(key, out var acc);
                    pairs[key] = (acc.area + area, acc.area == 0 ? gap : Mathf.Min(acc.gap, gap), acc.area == 0 ? at : acc.at);
                }
            }
        }
        Physics.queriesHitBackfaces = back; foreach (var c in temp) Object.DestroyImmediate(c); Physics.SyncTransforms();
        string P(MeshRenderer r) { var t = r.transform; string s = t.name; for (int q = 0; q < 2 && t.parent; q++) { t = t.parent; s = t.name + "/" + s; } return s; }
        var bad = pairs.Where(p => p.Value.area > 0.005f).OrderByDescending(p => p.Value.area).ToList();
        var o = new System.Text.StringBuilder($"Z-fight check: {tris.Count} triangles, {surf.Count} surfaces, {bad.Count} coplanar pairs seen from rooms" + (unreadable > 0 ? $" ({unreadable} unreadable meshes skipped)" : "") + "\n");
        foreach (var p in bad.Take(40))
            o.AppendLine($"ZFIGHT  {P(surf[p.Key.Item1].r)} [{surf[p.Key.Item1].m?.name}] vs {P(surf[p.Key.Item2].r)} [{surf[p.Key.Item2].m?.name}]: {p.Value.gap * 1000:F1} mm apart, {p.Value.area:F3} m2, at spec ({p.Value.at.x:F2}, {p.Value.at.y:F2}, {-p.Value.at.z:F2})");
        return o.ToString();
    }

    // overlap area of two triangles on (nearly) one plane, and a point inside the overlap: project onto the plane, clip one by the other
    static (float, Vector3) Overlap(Vector3 a0, Vector3 b0, Vector3 c0, Vector3 a1, Vector3 b1, Vector3 c1, Vector3 n)
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

    static string SeamCheck(params GameObject[] roots)
    {
        // only surfaces seen from inside a room count: the point just in front of a face must be in a room's open volume
        bool Seen(Vector3 q) => SeamRooms.Any(r => q.y > r.y0 + 0.002f && q.y < r.y1 - 0.002f && Inside(r.pts, new Vector2(q.x, q.z)));
        string[] skip = { "Dressing", "Furniture", "Rail", "Spindle", "spindle", "_cap", "Casing", "PropDoor", "Window", "Glass", "Stool", "Apron", "Light", "Walker", "Outdoors", "Arch_Spandrel", "ShadowCap", "Envelope", "_tread", "_riser", "stringer", "newel", "_HiFi", "Fixtures", "Trim" };   // generated models and fixtures: the z-fight and clash checks cover them   // an arch's curve is stepped on purpose (grey-box)
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
        "Arch_Spandrel|Arch_Spandrel" };                              // the grey-box arch is stepped slices on purpose
    static string ClashCheck(params GameObject[] roots)
    {
        var rs = roots.Where(o => o != null).SelectMany(o => o.GetComponentsInChildren<MeshRenderer>())
            .Where(r => r.enabled && r.shadowCastingMode != ShadowCastingMode.ShadowsOnly && r.GetComponent<MeshFilter>()?.sharedMesh is Mesh m && m.isReadable).ToList();
        var verts = rs.Select(r => { var v = r.GetComponent<MeshFilter>().sharedMesh.vertices; var M = r.transform.localToWorldMatrix; for (int i = 0; i < v.Length; i++) v[i] = M.MultiplyPoint3x4(v[i]); return v; }).ToList();
        var tris = new List<(int r, Vector3 a, Vector3 b, Vector3 c)>();
        for (int k = 0; k < rs.Count; k++) { var t = rs[k].GetComponent<MeshFilter>().sharedMesh.triangles; var v = verts[k]; for (int i = 0; i < t.Length; i += 3) tris.Add((k, v[t[i]], v[t[i + 1]], v[t[i + 2]])); }
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
                            if (SegTri(e0, e1, F.a, F.b, F.c, out var hit) && Through(pr, R, hit, n) && Visible(pr, hit, n))
                            {
                                var key = (pr, R); found.TryGetValue(key, out var acc); found[key] = (acc.n + 1, acc.n == 0 ? hit : acc.at); break;
                            }
                    }
                }
        Physics.queriesHitBackfaces = back; foreach (var c in temp) Object.DestroyImmediate(c); Physics.SyncTransforms();
        var bad = found.Where(f => !Allowed(rs[f.Key.Item1], rs[f.Key.Item2])).OrderByDescending(f => f.Value.n).ToList();
        string P(MeshRenderer r) { var t = r.transform; string s = t.name; for (int q = 0; q < 2 && t.parent; q++) { t = t.parent; s = t.name + "/" + s; } return s; }
        var o = new System.Text.StringBuilder($"Clash check: {tris.Count} triangles, {bad.Count} parts passing through another ({found.Count - bad.Count} allowed joints)\n");
        foreach (var f in bad.Take(40))
            o.AppendLine($"CLASH   {P(rs[f.Key.Item1])} through {P(rs[f.Key.Item2])}: {f.Value.n} crossings, first at spec ({f.Value.at.x:F2}, {f.Value.at.y:F2}, {-f.Value.at.z:F2})");
        return o.ToString();
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

    // Trim (user note Oct 16 11:13: a gap in the moulding): along every finished room's outline, every 2 cm at the baseboard's and the
    // cap rail's height, a ray from 10 cm inside the room toward the wall must meet trim or something mounted on the wall (a casing,
    // a door, the stair) before bare wall; points inside something solid are skipped. Bare wall over 3 cm long is a GAP. Reads the built scene, not the trim's own runs.
    static List<(List<Vector2> pts, float floorY, float h)> TrimRooms = new();

    static string TrimCheck()
    {
        var temp = new List<Collider>();
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (r.enabled && r.GetComponent<Collider>() == null && r.GetComponent<MeshFilter>()?.sharedMesh is Mesh mesh)
            { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mesh; temp.Add(mc); }
        Physics.SyncTransforms();
        var gaps = new List<string>(); int samples = 0;
        foreach (var (p, fy, h) in TrimRooms)
        {
            int n = p.Count; float area = 0f;
            for (int i = 0; i < n; i++) area += p[i].x * p[(i + 1) % n].y - p[(i + 1) % n].x * p[i].y;
            float sg = Mathf.Sign(area);
            var heights = h > 0.3f ? new[] { 0.07f, h + 0.01f } : new[] { 0.07f };
            for (int i = 0; i < n; i++)
            {
                Vector2 a = p[i], b = p[(i + 1) % n]; float L = Vector2.Distance(a, b); if (L < 0.1f) continue;
                Vector2 t = (b - a) / L, nOut = new Vector2(sg * t.y, -sg * t.x);
                foreach (float y in heights)
                {
                    float g0 = -1f;
                    void Close(float s) { if (g0 >= 0f && s - g0 > 0.03f) { var m = a + t * (g0 + s) / 2; gaps.Add($"GAP     {s - g0:F2} m of bare wall at y {y:F2} by spec ({m.x:F2}, {fy:F2}, {-m.y:F2})"); } g0 = -1f; }
                    for (float s = 0.03f; s < L - 0.03f; s += 0.02f)
                    {
                        samples++;
                        var q = a + t * s; var o = new Vector3(q.x - nOut.x * 0.10f, fy + y, q.y - nOut.y * 0.10f);
                        // a sample point inside something solid (the stair's steps: their grey-box colliders stay) is not seen from the room
                        bool bare = !Physics.CheckSphere(o, 0.005f, ~0, QueryTriggerInteraction.Ignore) && Physics.Raycast(o, new Vector3(nOut.x, 0f, nOut.y), out var hit, 0.14f, ~0, QueryTriggerInteraction.Ignore)
                                    && hit.collider.name == "Wall" && hit.distance > 0.09f;
                        if (bare && g0 < 0f) g0 = s; else if (!bare) Close(s);
                    }
                    Close(L - 0.03f);
                }
            }
        }
        foreach (var c in temp) Object.DestroyImmediate(c);
        Physics.SyncTransforms();
        return $"Trim check: {TrimRooms.Count} finished rooms, {samples} samples, {gaps.Count} gaps in the baseboard or cap rail\n" + string.Concat(gaps.Take(30).Select(g => g + "\n"));
    }
}
