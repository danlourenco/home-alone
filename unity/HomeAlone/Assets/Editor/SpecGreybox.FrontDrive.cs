using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

// Front U-drive, walk-entrance piers and the garage fence (Oct 19 2026, TRIAL; changes/2026-10-19-front-drive.json, DEVIATIONS 103).
// Generated, not borrowed: the downloaded GLB has the same U and piers, but crude and on its 0.757-scaled parcel (piers 6.4 m short
// of our sidewalk; its drive one apron over the whole lawn).
//  - drive: the real lot's centreline (OSM ways 1012087264/65, mapped by the footprint's front line; spec x,z), 3.6 m wide, the
//    street's wet asphalt, laid 2 cm over whatever is below (raycast; no collider: the walk gates are unchanged), snow banks on both
//    edges, open across the walk, the sidewalk and the garage drive; the garage drive's flat front (0.41 m over the yard) eased down
//  - piers + wing walls (film 11908/12030/12066 proportions, size from the walk: DEVIATIONS 103), lanterns lit at night, a brass
//    mailbox on the right pier; colliders
//  - a stained board fence off the garage's left front corner (film 2513/2515/2525)
//  - surfaces (walk note Oct 19 08:08): the garage drive wet asphalt, sidewalks / kerbs / walk a wet PBR concrete
public static partial class SpecGreybox
{
    static readonly Vector2[] DriveLine = {   // spec (x, z): kerb (left, joins the garage drive) -> round the lawn -> kerb (right)
        new Vector2(30.58f, 21.40f), new Vector2(28.65f, 21.41f), new Vector2(24.41f, 21.48f), new Vector2(21.78f, 18.15f), new Vector2(20.23f, 13.53f),
        new Vector2(20.46f, 9.82f), new Vector2(20.55f, 8.49f), new Vector2(22.66f, 3.86f), new Vector2(25.56f, 1.09f), new Vector2(27.28f, -0.51f),
        new Vector2(28.73f, -1.18f), new Vector2(30.58f, -2.02f) };
    static readonly Vector2[] DriveSpur = { new Vector2(24.41f, 21.48f), new Vector2(23.2f, 21.50f), new Vector2(21.6f, 21.53f) };   // onto the garage drive
    const float DriveW = 3.6f, PierX0 = 28.30f, PierX1 = 28.80f, PierW = 0.50f, PierGap = 1.50f, WalkZ = 9.716f;

    // Catmull-Rom through the points, sampled every 'step' m (spec x,z)
    static List<Vector2> Spline(Vector2[] p, float step)
    {
        var o = new List<Vector2>();
        for (int i = 0; i + 1 < p.Length; i++)
        {
            Vector2 a = p[Mathf.Max(0, i - 1)], b = p[i], c = p[i + 1], d = p[Mathf.Min(p.Length - 1, i + 2)];
            int n = Mathf.Max(1, Mathf.CeilToInt((c - b).magnitude / step));
            for (int k = 0; k < n; k++)
            {
                float t = k / (float)n, t2 = t * t, t3 = t2 * t;
                o.Add(0.5f * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3));
            }
        }
        o.Add(p[p.Length - 1]); return o;
    }

    static float DistToLine(List<Vector2> l, Vector2 q)
    {
        float best = float.MaxValue;
        for (int i = 0; i + 1 < l.Count; i++)
        {
            var ab = l[i + 1] - l[i]; float t = Mathf.Clamp01(Vector2.Dot(q - l[i], ab) / Mathf.Max(1e-6f, ab.sqrMagnitude));
            best = Mathf.Min(best, (l[i] + t * ab - q).magnitude);
        }
        return best;
    }

    // a closed hexahedron (c[0..3] bottom ring, c[4..7] top ring in the same order), flat faces wound outward
    static void Hex(List<Vector3> vs, List<int> tris, Vector3[] c)
    {
        var ctr = c.Aggregate(Vector3.zero, (s, v) => s + v) / 8f;
        void Q(Vector3 a, Vector3 b, Vector3 cc, Vector3 d)
        {
            int i = vs.Count; vs.AddRange(new[] { a, b, cc, d });
            bool flip = Vector3.Dot(Vector3.Cross(b - a, cc - a), (a + b + cc + d) / 4f - ctr) < 0;
            tris.AddRange(flip ? new[] { i, i + 2, i + 1, i, i + 3, i + 2 } : new[] { i, i + 1, i + 2, i, i + 2, i + 3 });
        }
        Q(c[0], c[1], c[2], c[3]); Q(c[4], c[5], c[6], c[7]);
        for (int k = 0; k < 4; k++) { int k2 = (k + 1) % 4; Q(c[k], c[k2], c[4 + k2], c[4 + k]); }
    }
    // axis-aligned box in world coords; top half-size may shrink (a frustum)
    static void HexBox(List<Vector3> vs, List<int> tris, Vector3 c, float hx, float hz, float y0, float y1, float tx = -1, float tz = -1)
    {
        if (tx < 0) tx = hx; if (tz < 0) tz = hz;
        Hex(vs, tris, new[] { new Vector3(c.x - hx, y0, c.z - hz), new Vector3(c.x + hx, y0, c.z - hz), new Vector3(c.x + hx, y0, c.z + hz), new Vector3(c.x - hx, y0, c.z + hz),
                              new Vector3(c.x - tx, y1, c.z - tz), new Vector3(c.x + tx, y1, c.z - tz), new Vector3(c.x + tx, y1, c.z + tz), new Vector3(c.x - tx, y1, c.z + tz) });
    }
    // an n-sided prism (round posts)
    static void Prism(List<Vector3> vs, List<int> tris, Vector3 c, float r, float y0, float y1, int n = 10)
    {
        int b = vs.Count;
        for (int k = 0; k < n; k++)
        {
            float a0 = 2 * Mathf.PI * k / n, a1 = 2 * Mathf.PI * (k + 1) / n;
            var p0 = c + new Vector3(Mathf.Cos(a0) * r, 0, Mathf.Sin(a0) * r); var p1 = c + new Vector3(Mathf.Cos(a1) * r, 0, Mathf.Sin(a1) * r);
            int i = vs.Count; vs.AddRange(new[] { new Vector3(p0.x, y0, p0.z), new Vector3(p1.x, y0, p1.z), new Vector3(p1.x, y1, p1.z), new Vector3(p0.x, y1, p0.z) });
            tris.AddRange(new[] { i, i + 2, i + 1, i, i + 3, i + 2 });
        }
        int top = vs.Count; vs.Add(new Vector3(c.x, y1, c.z));
        for (int k = 0; k < n; k++) { float a = 2 * Mathf.PI * k / n; vs.Add(new Vector3(c.x + Mathf.Cos(a) * r, y1, c.z + Mathf.Sin(a) * r)); }
        for (int k = 0; k < n; k++) tris.AddRange(new[] { top, top + 1 + (k + 1) % n, top + 1 + k });
    }
    // a rounded snow cushion over a rectangle (world centre, half sizes), smooth
    static void Cushion(List<Vector3> vs, List<int> tris, Vector3 c, float hx, float hz, float h, int n = 8)
    {
        int b = vs.Count;
        for (int i = 0; i <= n; i++)
            for (int j = 0; j <= n; j++)
            {
                float u = 2f * i / n - 1f, v = 2f * j / n - 1f, r = Mathf.Pow(Mathf.Pow(Mathf.Abs(u), 4) + Mathf.Pow(Mathf.Abs(v), 4), 0.25f);
                vs.Add(c + new Vector3(u * hx, h * Mathf.Max(0f, 1f - Mathf.Pow(r, 3)) * (0.9f + 0.2f * Mathf.PerlinNoise(c.x * 3 + u, c.z * 3 + v)) - 0.004f, v * hz));
            }
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) { int a = b + i * (n + 1) + j; tris.AddRange(new[] { a, a + 1, a + n + 2, a, a + n + 2, a + n + 1 }); }
    }
    static void BoxCol(GameObject parent, string n, Vector3 c, Vector3 size)
    {
        var g = new GameObject(n); g.transform.SetParent(parent.transform, false); g.transform.position = c; g.isStatic = true;
        g.AddComponent<BoxCollider>().size = size;
    }

    static void FrontDrive(GameObject ext, float gy)
    {
        float d = gy + 2.996f;
        var holder = new GameObject("FrontDrive"); holder.transform.SetParent(ext.transform, true); holder.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
        var wet = TexMat("HiFi_ExtWetRoad", "asphalt_02_x", new Color(0.45f, 0.45f, 0.47f), 4.0f, 0.86f);   // the street's (ExteriorRealism)
        var conc = TexMat("HiFi_ExtWetConcrete", "concrete_floor_01_x", new Color(0.70f, 0.70f, 0.67f), 2.0f, 0.50f);   // damp sidewalk concrete (the worn set read as asphalt: albedo 86/255)
        var snow = TexMat("HiFi_ExtGroundSnow", "snow_02_x", new Color(0.95f, 0.97f, 1.0f), 2.2f, 0.40f);
        var brick = TexMat("HiFi_ExtPierBrick", "red_brick_03_x", new Color(0.80f, 0.60f, 0.53f), 1.15f, 0.12f);   // at 1.90 the piers read ~11 cm courses (render): 68 mm
        var stone = TexMat("HiFi_ExtCapStone", "concrete_floor_01_x", new Color(0.80f, 0.77f, 0.70f), 0.9f, 0.35f);   // film 11908: buff limestone caps
        var iron = Mat("HiFi_ExtLanternMetal", new Color(0.015f, 0.015f, 0.014f)); iron.SetFloat("_Metallic", 0.7f); iron.SetFloat("_Smoothness", 0.5f);
        var brass = Mat("HiFi_ExtMailboxBrass", new Color(0.86f, 0.69f, 0.38f)); brass.SetFloat("_Metallic", 1f); brass.SetFloat("_Smoothness", 0.55f);
        var glass = AtticGlow("HiFi_ExtPierLanternGlass", new Color(1f, 0.86f, 0.64f), 1800f, 0.9f);
        var wood = TexMat("HiFi_ExtFenceWood", "weathered_planks_h", new Color(0.55f, 0.36f, 0.27f), 1.2f, 0.12f);   // film 2513: brown stain

        // ---- surfaces (walk note Oct 19 08:08): drives match the street, the concrete is damp PBR; the neighbourhood's driveway aprons
        // (where neither the film nor OSM has a drive) go
        int aprons = 0, retex = 0;
        foreach (var r in ext.GetComponentsInChildren<MeshRenderer>(true).ToList())
        {
            if (r == null) continue;
            if (r.name == "Driveway street apron") { Object.DestroyImmediate(r.gameObject); aprons++; continue; }
            if (r.name == "object161_property") { r.sharedMaterials = r.sharedMaterials.Select(_ => wet).ToArray(); retex++; continue; }
            var ms = r.sharedMaterials; bool hit = false;
            for (int i = 0; i < ms.Length; i++) if (ms[i] != null && (ms[i].name == "NeighborhoodConcrete" || ms[i].name == "Yard_Walk")) { ms[i] = conc; hit = true; }
            if (hit) { r.sharedMaterials = ms; retex++; }
        }
        // the garage drive's flat front stood 0.41 m over the front yard (-3.94 vs -4.35, x 15-22.3): eased down from x 14 to 2 cm over the
        // yard at its front edge (thickness kept; the front yard is x > 10.4, so nothing beside the den moves)
        var gd = ext.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(f => f.name == "object161_property");
        if (gd != null)
        {
            var m = gd.sharedMesh; var v = m.vertices; var tr = gd.transform;
            for (int i = 0; i < v.Length; i++)
            {
                var w = tr.TransformPoint(v[i]); float t = Mathf.Clamp01((w.x - 14f) / (22.32f - 14f));
                w.y -= t * t * (3f - 2f * t) * 0.39f; v[i] = tr.InverseTransformPoint(w);
            }
            m.vertices = v; m.RecalculateBounds(); m.RecalculateNormals();
            var mc = gd.GetComponent<MeshCollider>(); if (mc != null) { mc.sharedMesh = null; mc.sharedMesh = m; }
        }
        Physics.SyncTransforms();

        // ---- the drive
        float Ground(float x, float z) => Physics.Raycast(new Vector3(x, -2.2f + d, -z), Vector3.down, out var h, 4f) && h.point.y < -3.5f + d ? h.point.y : -4.35f + d;
        var main = Spline(DriveLine, 0.25f); var spur = Spline(DriveSpur, 0.25f);
        const float lift = 0.02f;   // >= 1 cm over the grade and walk (zfight-check rule 2)
        bool OnSidewalk(float x) => x > 28.87f && x < 30.37f;   // the public sidewalk runs through the mouths
        var av = new List<Vector3>(); var at = new List<int>(); var bv = new List<Vector3>(); var bt = new List<int>();
        void Ribbon(List<Vector2> line, List<Vector2> other)
        {
            const int across = 8;
            var rows = new List<Vector3[]>(); var norm = new List<Vector2>();
            for (int i = 0; i < line.Count; i++)
            {
                var tng = (line[Mathf.Min(line.Count - 1, i + 1)] - line[Mathf.Max(0, i - 1)]).normalized; var n = new Vector2(-tng.y, tng.x); norm.Add(n);
                var row = new Vector3[across + 1];
                for (int k = 0; k <= across; k++) { var q = line[i] + n * (DriveW * (k / (float)across - 0.5f)); row[k] = new Vector3(q.x, Ground(q.x, q.y) + lift, -q.y); }
                rows.Add(row);
            }
            for (int i = 0; i + 1 < rows.Count; i++)
                for (int k = 0; k < across; k++)
                {
                    var c = (rows[i][k] + rows[i + 1][k + 1]) / 2f; if (OnSidewalk(c.x)) continue;
                    int b = av.Count; av.AddRange(new[] { rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k] });
                    at.AddRange(new[] { b, b + 1, b + 2, b, b + 2, b + 3 });
                }
            // snow banks on both edges (the plowed and shovelled edge, film 2513/6399), open where they would lie on the walk, the
            // sidewalk, the garage drive or the other ribbon; heights taper over ~1 m into each opening
            foreach (float side in new[] { -1f, 1f })
            {
                var ok = new bool[line.Count];
                for (int i = 0; i < line.Count; i++)
                {
                    var q = line[i] + norm[i] * side * (DriveW / 2 + 0.3f);
                    bool walk = Mathf.Abs(q.y - WalkZ) < 1.2f && q.x < 28.9f, street = q.x > 28.3f;
                    bool onDrive = DistToLine(other, q) < DriveW / 2 + 0.2f || DistToLine(line, q) < DriveW / 2 - 0.05f;
                    bool garage = Physics.Raycast(new Vector3(q.x, -2.2f + d, -q.y), Vector3.down, out var h, 4f) && h.collider.name == "object161_property";
                    ok[i] = !(walk || street || onDrive || garage);
                }
                var amp = new float[line.Count];
                for (int i = 0; i < line.Count; i++) { int good = 0, all = 0; for (int j = i - 4; j <= i + 4; j++) { if (j < 0 || j >= line.Count) continue; all++; if (ok[j]) good++; } amp[i] = ok[i] ? Mathf.SmoothStep(0, 1, good / (float)all) : 0f; }
                const int nw = 6; int start = bv.Count;
                for (int i = 0; i < line.Count; i++)
                    for (int k = 0; k <= nw; k++)
                    {
                        float u = k / (float)nw; var q = line[i] + norm[i] * side * (DriveW / 2 - 0.08f + 0.65f * u);
                        float noise = 0.75f + 0.5f * Mathf.PerlinNoise(q.x * 1.3f + 7f, q.y * 1.3f + 3f);
                        float hgt = 0.14f * amp[i] * noise * Mathf.Pow(Mathf.Max(0f, Mathf.Sin(Mathf.PI * u)), 0.8f);
                        bv.Add(new Vector3(q.x, Ground(q.x, q.y) + lift + 0.004f + hgt, -q.y));
                    }
                for (int i = 0; i + 1 < line.Count; i++)
                {
                    if (amp[i] <= 0f && amp[i + 1] <= 0f) continue;
                    for (int k = 0; k < nw; k++) { int a = start + i * (nw + 1) + k, c = a + nw + 1; bt.AddRange(new[] { a, a + 1, c + 1, a, c + 1, c }); }
                }
            }
        }
        Ribbon(main, spur); Ribbon(spur, main);
        WorldMesh(holder, "FrontDrive_Asphalt", av, at, wet, false, true);
        var banks = WorldMesh(holder, "FrontDrive_SnowBanks", bv, bt, snow, true, true);

        // ---- the walk piers and wing walls (spec x 28.30-28.80, either side of the walk axis)
        var pv = new List<Vector3>(); var pt = new List<int>(); var cv = new List<Vector3>(); var ct = new List<int>();
        var sv = new List<Vector3>(); var st = new List<int>(); var lv = new List<Vector3>(); var lt = new List<int>();
        var gv = new List<Vector3>(); var gt = new List<int>(); var mv = new List<Vector3>(); var mt = new List<int>();
        float px = (PierX0 + PierX1) / 2f;
        const float capTop = 1.04f, capT = 0.15f, capHalf = 0.31f, wingLen = 1.74f, wingHi = 0.84f, wingLo = 0.31f, wingT = 0.32f, wingCapW = 0.40f, wingCapT = 0.07f;
        var lanterns = new List<Vector3>();
        foreach (float s in new[] { 1f, -1f })   // +1: the left pier (spec z > walk), -1: the right (mailbox)
        {
            float zc = WalkZ + s * (PierGap / 2 + PierW / 2);
            float yg = new[] { -PierW / 2, PierW / 2 }.SelectMany(a => new[] { Ground(PierX0, zc + a), Ground(PierX1, zc + a) }).Min();
            var c = new Vector3(px, 0, -zc);
            HexBox(pv, pt, c, PierW / 2, PierW / 2, yg - 0.06f, yg + capTop - capT);                                       // brick shaft
            HexBox(cv, ct, c, capHalf, capHalf, yg + capTop - capT, yg + capTop - 0.055f);                                   // cap: slab
            HexBox(cv, ct, c, capHalf, capHalf, yg + capTop - 0.055f, yg + capTop, capHalf - 0.06f, capHalf - 0.06f);         //      weathered top
            Cushion(sv, st, c + Vector3.up * (yg + capTop), capHalf - 0.07f, capHalf - 0.07f, 0.07f);                      // snow on the cap
            BoxCol(holder, "PierCollider", c + Vector3.up * (yg + (capTop - 0.06f) / 2f), new Vector3(2 * capHalf, capTop + 0.06f, 2 * capHalf));
            // lantern on a short round post (film 11908: post ~0.5 m, glass head ~0.46 m with its roof)
            float y = yg + capTop;
            HexBox(lv, lt, c, 0.08f, 0.08f, y, y + 0.05f, 0.06f, 0.06f);
            Prism(lv, lt, c, 0.035f, y + 0.05f, y + 0.50f);
            HexBox(lv, lt, c, 0.10f, 0.10f, y + 0.50f, y + 0.53f);                       // lantern floor
            HexBox(gv, gt, c, 0.095f, 0.095f, y + 0.53f, y + 0.83f, 0.130f, 0.130f);       // glass, flaring up
            foreach (var (ix, iz) in new[] { (-1, -1), (1, -1), (1, 1), (-1, 1) })       // corner frame bars
            {
                var a = c + new Vector3(ix * 0.10f, y + 0.53f, iz * 0.10f); var b = c + new Vector3(ix * 0.135f, y + 0.83f, iz * 0.135f);
                Hex(lv, lt, new[] { a + new Vector3(-0.012f, 0, -0.012f), a + new Vector3(0.012f, 0, -0.012f), a + new Vector3(0.012f, 0, 0.012f), a + new Vector3(-0.012f, 0, 0.012f),
                                    b + new Vector3(-0.012f, 0, -0.012f), b + new Vector3(0.012f, 0, -0.012f), b + new Vector3(0.012f, 0, 0.012f), b + new Vector3(-0.012f, 0, 0.012f) });
            }
            HexBox(lv, lt, c, 0.155f, 0.155f, y + 0.83f, y + 0.86f);                     // roof rim
            HexBox(lv, lt, c, 0.150f, 0.150f, y + 0.86f, y + 0.96f, 0.03f, 0.03f);        // roof
            Prism(lv, lt, c, 0.018f, y + 0.96f, y + 1.01f, 8);                           // finial
            lanterns.Add(c + Vector3.up * (y + 0.68f));
            // the wing wall: an S from just under the cap to a low level end (film 11908), brick under a stone cap, snow on the cap
            const int N = 22; float z0 = zc + s * PierW / 2;
            float H(float t) { float u = Mathf.Clamp01(t / 0.9f); return wingLo + (wingHi - wingLo) * 0.5f * (1f + Mathf.Cos(Mathf.PI * u)); }
            float wyg = Ground(px, z0 + s * wingLen * 0.5f);
            for (int i = 0; i < N; i++)
            {
                float t0 = i / (float)N, t1 = (i + 1) / (float)N, za = -(z0 + s * wingLen * t0), zb = -(z0 + s * wingLen * t1);
                if (i == 0) za += s * 0.02f;   // 2 cm into the pier (a joint, not a face on its face)
                float ya = yg + H(t0), yb = yg + H(t1);
                Vector3 P(float x, float yy, float z) => new Vector3(x, yy, z);
                Hex(pv, pt, new[] { P(px - wingT / 2, yg - 0.06f, za), P(px + wingT / 2, yg - 0.06f, za), P(px + wingT / 2, yg - 0.06f, zb), P(px - wingT / 2, yg - 0.06f, zb),
                                    P(px - wingT / 2, ya, za), P(px + wingT / 2, ya, za), P(px + wingT / 2, yb, zb), P(px - wingT / 2, yb, zb) });
                float ze = i == N - 1 ? zb - s * 0.03f : zb;   // the cap overhangs the wall's end
                Hex(cv, ct, new[] { P(px - wingCapW / 2, ya, za), P(px + wingCapW / 2, ya, za), P(px + wingCapW / 2, yb, ze), P(px - wingCapW / 2, yb, ze),
                                    P(px - wingCapW / 2, ya + wingCapT, za), P(px + wingCapW / 2, ya + wingCapT, za), P(px + wingCapW / 2, yb + wingCapT, ze), P(px - wingCapW / 2, yb + wingCapT, ze) });
            }
            int sb = sv.Count; const int sx = 4;   // snow strip along the wing cap, crowned across
            for (int i = 0; i <= N; i++)
                for (int k = 0; k <= sx; k++)
                {
                    float t = i / (float)N, u = k / (float)sx * 2f - 1f;
                    sv.Add(new Vector3(px + u * (wingCapW / 2 - 0.035f), yg + H(t) + wingCapT - 0.004f + 0.045f * (1f - u * u * u * u) * (i == 0 || i == N ? 0.3f : 1f), -(z0 + s * wingLen * t)));
                }
            for (int i = 0; i < N; i++) for (int k = 0; k < sx; k++) { int a = sb + i * (sx + 1) + k, e = a + sx + 1; st.AddRange(new[] { a, e, e + 1, a, e + 1, a + 1 }); }
            BoxCol(holder, "WingCollider", new Vector3(px, yg + (wingHi + wingCapT - 0.06f) / 2f, -(z0 + s * wingLen / 2f)), new Vector3(wingCapW, wingHi + wingCapT + 0.06f, wingLen));
            if (s < 0)   // the brass mailbox on the right pier's street face (film 11908/12066), snow on its lid
            {
                var mc = new Vector3(PierX1 + 0.055f, 0, -zc);
                HexBox(mv, mt, mc, 0.055f, 0.19f, yg + 0.42f, yg + 0.70f);
                HexBox(mv, mt, mc + new Vector3(0.008f, 0, 0), 0.068f, 0.20f, yg + 0.70f, yg + 0.725f);
                Cushion(sv, st, mc + Vector3.up * (yg + 0.725f), 0.055f, 0.18f, 0.05f, 6);
            }
        }
        var piers = new GameObject("WalkPiers"); piers.transform.SetParent(holder.transform, false);
        WorldMesh(piers, "Piers_Brick", pv, pt, brick); WorldMesh(piers, "Piers_Caps", cv, ct, stone); WorldMesh(piers, "Piers_Snow", sv, st, snow, true, true);
        WorldMesh(piers, "Piers_LanternMetal", lv, lt, iron); WorldMesh(piers, "Piers_Mailbox", mv, mt, brass);
        var gl = WorldMesh(piers, "Piers_LanternGlass", gv, gt, glass, false); ShellGlow.Add(gl.GetComponent<MeshRenderer>());
        foreach (var l in lanterns) ShellLights.Add(NightLight(piers, "PierLantern", l, 220f, 7f));

        // ---- the garage fence (film 2513/2515/2525): off the garage's left front corner, away from the house; 1.4 m stained boards
        var fv = new List<Vector3>(); var ft = new List<int>();
        const float fx = -0.45f, fz0 = 28.25f, fz1 = 31.25f, fh = 1.40f;
        float fyg = Ground(fx, (fz0 + fz1) / 2f);
        for (float z = fz0 + 0.02f; z + 0.14f <= fz1; z += 0.165f)
            HexBox(fv, ft, new Vector3(fx + 0.01f, 0, -(z + 0.07f)), 0.011f, 0.07f, Ground(fx, z + 0.07f) - 0.05f, Ground(fx, z + 0.07f) + fh);
        foreach (float ry in new[] { 0.25f, 1.15f }) HexBox(fv, ft, new Vector3(fx - 0.035f, 0, -(fz0 + fz1) / 2f), 0.024f, (fz1 - fz0) / 2f, fyg + ry, fyg + ry + 0.09f);
        foreach (float z in new[] { fz0 + 0.05f, (fz0 + fz1) / 2f, fz1 - 0.05f }) HexBox(fv, ft, new Vector3(fx - 0.07f, 0, -z), 0.045f, 0.045f, fyg - 0.10f, fyg + fh + 0.05f);
        WorldMesh(holder, "GarageFence", fv, ft, wood);
        BoxCol(holder, "GarageFenceCollider", new Vector3(fx - 0.03f, fyg + fh / 2f, -(fz0 + fz1) / 2f), new Vector3(0.14f, fh + 0.1f, fz1 - fz0));

        Debug.Log($"FrontDrive: drive {at.Count / 3} tris on {main.Count + spur.Count} samples, banks {bt.Count / 3} tris, piers + wings + 2 lanterns + mailbox, fence; " +
                  $"{aprons} neighbourhood aprons removed, {retex} surfaces retextured, garage drive front {(gd != null ? "eased" : "MISSING")}");
    }
}
