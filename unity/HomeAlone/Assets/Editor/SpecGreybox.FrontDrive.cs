using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;
using UnityEditor;
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
    // spec (x, z): kerb (left, joins the garage drive) -> round the lawn -> kerb (right). The mouths are OSM's (ways 1012087264/65);
    // the front run is pulled in to pass 1.5 m off the bottom step, centre x 17.35 (film 1640: the airport vans at the foot of the
    // steps; 2009/2013 photos: the drive at the steps' apron; OSM's run at x 20.5 left a 4.5 m walk strip: changes/2026-10-20-drive-to-steps.json)
    static readonly Vector2[] DriveLine = {
        new Vector2(30.58f, 21.40f), new Vector2(28.65f, 21.41f), new Vector2(24.41f, 21.48f), new Vector2(20.40f, 20.20f), new Vector2(18.10f, 17.20f),
        new Vector2(17.35f, 13.50f), new Vector2(17.35f, 9.72f), new Vector2(17.45f, 6.40f), new Vector2(18.90f, 3.10f), new Vector2(21.70f, 1.45f),
        new Vector2(24.90f, 0.55f), new Vector2(27.28f, -0.51f), new Vector2(28.73f, -1.18f), new Vector2(30.58f, -2.02f) };
    static readonly Vector2[] DriveSpur = { new Vector2(24.41f, 21.48f), new Vector2(23.2f, 21.50f), new Vector2(21.6f, 21.53f) };   // onto the garage drive
    const float StepFootX = 14.05f, WalkBankX0 = 19.65f;   // the bottom riser (FrontBeds: stoopX + 6 treads); the walk banks past the drive
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
        // the ground by weather (walk notes Oct 19 08:48/09:50/12:11; DEVIATIONS 124): one material per state (Sunny, Overcast, Night),
        // swapped at run time by WetGround; built showing Sunny. Asphalt: the street, both drives, the front walk and its connection (one
        // continuous surface; film 1640: the drive at the foot of the steps). Concrete: sidewalks and kerbs (jointed across z: they run
        // along the street) and the apron at the foot of the steps (2013 photo). Warm grey tints from film 1640's drive/snow ratio, toned down.
        string[] states = { "sunny", "overcast", "night" };
        Material[] Set(string n, string id, Color tint, float tile) =>
            states.Select(st => WetMat($"{n}_{char.ToUpper(st[0])}{st.Substring(1)}", $"{id}_{st}", tint, tile: tile, normalId: $"{id}_night")).ToArray();
        var asph = Set("HiFi_ExtAsphalt", "asphalt_wet", new Color(0.95f, 0.92f, 0.87f), 4.0f);
        var concS = Set("HiFi_ExtConcrete", "walk_wet_jz", new Color(1.0f, 0.95f, 0.89f), 3.0f);
        var apronS = Set("HiFi_ExtApron", "walk_wet", new Color(1.0f, 0.93f, 0.88f), 3.0f);   // 2013: pale, a little pink
        Material wet = asph[0], conc = concS[0];
        var stepWet = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Greybox/HiFi_ExtStepStone.mat");   // ExteriorRealism's
        var snow = TexMat("HiFi_ExtGroundSnow", "snow_02_x", new Color(0.95f, 0.97f, 1.0f), 2.2f, 0.40f);
        var brick = TexMat("HiFi_ExtPierBrick", "red_brick_03_x", new Color(0.80f, 0.60f, 0.53f), 1.15f, 0.12f);   // at 1.90 the piers read ~11 cm courses (render): 68 mm
        var stone = TexMat("HiFi_ExtCapStone", "concrete_floor_01_x", new Color(0.80f, 0.77f, 0.70f), 0.9f, 0.35f);   // film 11908: buff limestone caps
        var iron = Mat("HiFi_ExtLanternMetal", new Color(0.015f, 0.015f, 0.014f)); iron.SetFloat("_Metallic", 0.7f); iron.SetFloat("_Smoothness", 0.5f);
        // walk note 2026-10-21T06:45:32 ("the front mailbox feels way too bright, and cheep. same with the pier lights"): film 11908/12030 (overcast,
        // snow) read the mailbox a dull, aged brass (sRGB ~107-115 / 86-92 / 50-72 beside the snow) and the lantern glass a pale frosted grey
        // (~113 / 113 / 110), unlit by day. Was: polished brass 0.86/0.69/0.38, metallic 1, smoothness 0.55 (it mirrored the bright overcast
        // sky: 228/199/109 in the shot) and glass with a pale-yellow BASE colour (1, 0.86, 0.64), so by day it read as a flat yellow pane
        var brass = Mat("HiFi_ExtMailboxBrass", new Color(0.42f, 0.31f, 0.15f)); brass.SetFloat("_Metallic", 0.85f); brass.SetFloat("_Smoothness", 0.32f);
        var glass = AtticGlow("HiFi_ExtPierLanternGlass", new Color(0.58f, 0.58f, 0.56f), 0f, 0.55f);   // frosted, grey by day
        glass.SetColor("_EmissiveColor", new Color(1f, 0.86f, 0.64f) * 650f);   // night only (ShellGlow): film 5545 a warm white globe, not a glare (was 1800)
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
            for (int i = 0; i < ms.Length; i++)
            {
                if (ms[i] == null) continue;
                if (ms[i].name == "Yard_Walk" || ms[i].name == "HiFi_ExtWetRoad" || ms[i].name == "NeighborhoodConcrete" && r.name == "Front walk connection") { ms[i] = wet; hit = true; }
                else if (ms[i].name == "NeighborhoodConcrete") { ms[i] = conc; hit = true; }
                else if (ms[i].name == "Yard_Steps" && stepWet != null) { ms[i] = stepWet; hit = true; }   // any red slab the rebuild left (porch)
            }
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
        foreach (var cc in ext.GetComponentsInChildren<CapsuleCollider>(true))   // a trunk standing in the drive (the run moved Oct 20)
        {
            var q = new Vector2(cc.transform.position.x, -cc.transform.position.z);
            if (DistToLine(main, q) < DriveW / 2 + 0.5f || DistToLine(spur, q) < DriveW / 2 + 0.5f) Debug.LogWarning($"FrontDrive: BLOCKED tree {cc.name} at spec {q} in the drive");
        }
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
            HexBox(lv, lt, c, 0.140f, 0.140f, y + 0.83f, y + 0.85f);                     // roof rim (film 11908: a slim dark cap over the glass, not a wide roof)
            HexBox(lv, lt, c, 0.130f, 0.130f, y + 0.85f, y + 0.94f, 0.03f, 0.03f);        // roof
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
                // the front plate's raised border and the letter slot (film 11908/12066: a framed plate, not a plain box)
                HexBox(mv, mt, mc + new Vector3(0.057f, 0, 0), 0.006f, 0.185f, yg + 0.43f, yg + 0.445f); HexBox(mv, mt, mc + new Vector3(0.057f, 0, 0), 0.006f, 0.185f, yg + 0.675f, yg + 0.69f);
                HexBox(mv, mt, mc + new Vector3(0.057f, 0, 0.175f), 0.006f, 0.01f, yg + 0.445f, yg + 0.675f); HexBox(mv, mt, mc + new Vector3(0.057f, 0, -0.175f), 0.006f, 0.01f, yg + 0.445f, yg + 0.675f);
                HexBox(lv, lt, mc + new Vector3(0.058f, 0, 0), 0.004f, 0.12f, yg + 0.615f, yg + 0.63f);   // slot (dark)
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

        // ---- snowmelt at the shovelled edges (walk note Oct 19 12:11): a wet, darker band where the banks meet the walk and the
        // sidewalks, on the property's frontage (world z -21..2): a down-projected decal on each long edge of each wide (> 0.5 m) slab
        var melt = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Greybox/HiFi_DecalMelt.mat");
        if (melt == null) { melt = new Material(Shader.Find("HDRP/Decal")); AssetDatabase.CreateAsset(melt, "Assets/Materials/Greybox/HiFi_DecalMelt.mat"); }
        const string meltTex = "Assets/Textures/Exterior/melt_edge.png";
        if (AssetImporter.GetAtPath(meltTex) is TextureImporter mti && (!mti.alphaIsTransparency || mti.wrapMode != TextureWrapMode.Clamp)) { mti.alphaIsTransparency = true; mti.wrapMode = TextureWrapMode.Clamp; mti.SaveAndReimport(); }
        melt.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(meltTex)); melt.SetColor("_BaseColor", Color.white);
        melt.SetFloat("_AffectAlbedo", 1f); melt.SetFloat("_AffectNormal", 0f); melt.SetFloat("_AffectSmoothness", 1f); melt.SetFloat("_AffectAO", 0f); melt.SetFloat("_AffectMetal", 0f);
        melt.SetFloat("_Smoothness", 0.95f); melt.SetFloat("_MaskBlendSrc", 0f);   // smoothness blended by the albedo's alpha
        HDMaterial.ValidateMaterial(melt); EditorUtility.SetDirty(melt);
        int melts = 0;
        foreach (var r in ext.GetComponentsInChildren<MeshRenderer>(true))
        {
            bool walk = r.name == "Walk_Front" || r.name == "Front walk connection";
            if (!walk && r.sharedMaterial != conc) continue;
            var b = r.bounds; if (b.center.z < -21f || b.center.z > 2f || b.center.x > 31f) continue;
            bool alongX = b.size.x > b.size.z; float wid = alongX ? b.size.z : b.size.x;
            float a0 = alongX ? b.min.x : b.min.z, a1 = alongX ? b.max.x : b.max.z;
            if (walk) a0 = Mathf.Max(a0, WalkBankX0);   // the walk's banks start past the drive (ExteriorRealism's walk mounds)
            if (wid < 0.5f || a1 - a0 < 1f) continue;   // kerbs, scraps
            foreach (float side in new[] { -1f, 1f })
            {   // local +x points out to the bank (the texture's wet side is u = 1)
                var outward = alongX ? new Vector3(0, 0, side) : new Vector3(side, 0, 0);
                var edge = b.center + outward * (wid / 2f - 0.12f); edge.y = b.max.y;
                if (alongX) edge.x = (a0 + a1) / 2f; else edge.z = (a0 + a1) / 2f;
                var g = new GameObject("Decal_Melt"); g.transform.SetParent(holder.transform, false);
                g.transform.SetPositionAndRotation(edge, Quaternion.LookRotation(Vector3.down, Vector3.Cross(Vector3.down, outward)));
                var p = g.AddComponent<DecalProjector>(); p.material = melt;   // practices: ok (DecalProjector.material is a plain property)
                p.size = new Vector3(0.36f, a1 - a0, 0.40f); p.pivot = Vector3.zero; p.startAngleFade = 40f; p.endAngleFade = 70f; melts++;
            }
        }

        // ---- the apron at the foot of the steps (2013 photo: a short pale concrete strip between the bottom step and the drive), 0.6 m
        // deep, the steps' width, 12 mm over the walk's top (zfight-check rule 2); no collider (the walk's box carries the walking)
        var walkBox = ext.GetComponentsInChildren<MeshRenderer>(true).FirstOrDefault(r => r.name == "Walk_Front");
        if (walkBox != null)
        {
            float ay = walkBox.bounds.max.y + 0.012f, ax0 = StepFootX, ax1 = StepFootX + 0.60f, az0 = -(WalkZ + 0.95f), az1 = -(WalkZ - 0.95f);
            WorldMesh(holder, "Apron_Front", new List<Vector3> { new Vector3(ax0, ay, az0), new Vector3(ax1, ay, az0), new Vector3(ax1, ay, az1), new Vector3(ax0, ay, az1) },
                      new List<int> { 0, 2, 1, 0, 3, 2 }, apronS[0], false, true);
        }

        // ---- the weather switch: every renderer showing one of the state sets
        var sets = new HashSet<Material>(asph.Concat(concS).Concat(apronS));
        var wg = new GameObject("WetGround").AddComponent<WetGround>(); wg.transform.SetParent(holder.transform, false);
        wg.asphalt = asph; wg.concrete = concS; wg.apron = apronS;
        wg.renderers = ext.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.sharedMaterials.Any(m => m != null && sets.Contains(m))).ToArray();

        Debug.Log($"FrontDrive: drive {at.Count / 3} tris on {main.Count + spur.Count} samples, banks {bt.Count / 3} tris, piers + wings + 2 lanterns + mailbox, fence; " +
                  $"{aprons} neighbourhood aprons removed, {retex} surfaces retextured (wet concrete), {melts} snowmelt edge decals, WetGround on {wg.renderers.Length} renderers, garage drive front {(gd != null ? "eased" : "MISSING")}");
    }
}
