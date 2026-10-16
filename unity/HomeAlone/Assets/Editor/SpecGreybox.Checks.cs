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
        string[] skip = { "Dressing", "Furniture", "Rail", "Spindle", "spindle", "_cap", "Casing", "PropDoor", "Window", "Glass", "Stool", "Apron", "Light", "Walker", "Outdoors", "Arch_Spandrel", "ShadowCap", "_tread", "_riser", "stringer", "newel" };   // an arch's curve is stepped on purpose (grey-box)
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
}
