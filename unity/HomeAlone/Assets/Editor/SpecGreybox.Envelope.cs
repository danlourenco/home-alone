using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// The house's light-tight envelope (user, Oct 16: "the whole point of this rebuild was ... tight seals"). The grey-box walls are 14 cm
// and the ceilings 15 cm with no roof; a low sun read through them at every joint (shadow-map bias). A real brick house's outer wall is
// ~0.3 m and it has a roof. Generated from the spec, never placed by hand: a shadows-only skin outside every exterior wall face (closing
// round corners, over wall tops and under wall feet), a shadows-only lid over every ceiling with no storey above it, and every opening
// (windows, doors, wall_openings) cut back out so the sun still comes in through the glass. No colliders; the gates skip them.
// Checked by EnvelopeCheck.
public static partial class SpecGreybox
{
    const float SkinT = 0.25f, LidT = 0.4f, LidOver = 0.15f;

    struct Slab { public Vector3 lo, hi; public Slab(Vector3 a, Vector3 b) { lo = Vector3.Min(a, b); hi = Vector3.Max(a, b); } }

    static Slab SpecSlab(JToken b, float fy) => new Slab(new Vector3((float)b["x"][0], (float)b["y"][0] + fy, -(float)b["z"][1]),
                                                         new Vector3((float)b["x"][1], (float)b["y"][1] + fy, -(float)b["z"][0]));

    static bool In(Slab s, Vector3 p, float e = 0f) => p.x > s.lo.x - e && p.x < s.hi.x + e && p.y > s.lo.y - e && p.y < s.hi.y + e && p.z > s.lo.z - e && p.z < s.hi.z + e;

    // a slab minus a box: up to six pieces round it
    static IEnumerable<Slab> Minus(Slab s, Slab h)
    {
        if (h.lo.x >= s.hi.x || h.hi.x <= s.lo.x || h.lo.y >= s.hi.y || h.hi.y <= s.lo.y || h.lo.z >= s.hi.z || h.hi.z <= s.lo.z) { yield return s; yield break; }
        float x0 = Mathf.Max(s.lo.x, h.lo.x), x1 = Mathf.Min(s.hi.x, h.hi.x), y0 = Mathf.Max(s.lo.y, h.lo.y), y1 = Mathf.Min(s.hi.y, h.hi.y);
        if (h.lo.x > s.lo.x) yield return new Slab(s.lo, new Vector3(h.lo.x, s.hi.y, s.hi.z));
        if (h.hi.x < s.hi.x) yield return new Slab(new Vector3(h.hi.x, s.lo.y, s.lo.z), s.hi);
        if (h.lo.y > s.lo.y) yield return new Slab(new Vector3(x0, s.lo.y, s.lo.z), new Vector3(x1, h.lo.y, s.hi.z));
        if (h.hi.y < s.hi.y) yield return new Slab(new Vector3(x0, h.hi.y, s.lo.z), new Vector3(x1, s.hi.y, s.hi.z));
        if (h.lo.z > s.lo.z) yield return new Slab(new Vector3(x0, y0, s.lo.z), new Vector3(x1, y1, h.lo.z));
        if (h.hi.z < s.hi.z) yield return new Slab(new Vector3(x0, y0, h.hi.z), new Vector3(x1, y1, s.hi.z));
    }

    static void Envelope(GameObject root, JObject geo, JToken atticBoxes, JToken wallOpenings, JToken ceilingOpenings, float gy)
    {
        var storeys = new[] { ((JObject)geo["upstairs"], 0f), ((JObject)geo["ground"], gy) };
        var walls = storeys.SelectMany(s => s.Item1["walls"].Select(b => SpecSlab(b, s.Item2)))
            .Concat(atticBoxes.Where(b => (string)b["kind"] == "wall").Select(b => SpecSlab(b, 0f))).ToList();
        var solids = walls.Concat(storeys.SelectMany(s => s.Item1["ceilings"].Concat(s.Item1["floor"]).Select(b => SpecSlab(b, s.Item2)))).ToList();
        var rooms = EnvelopeRooms(geo, atticBoxes, gy);
        // a ceiling opening's recess (the back stair rises into one, DEVIATIONS 40) is framed like a small room: 14 cm walls round it from
        // the ceiling to its top and a ceiling over it; its own linings are 2 cm boards. Where it stands under no upstairs room they are
        // what keeps the sun out
        var framing = new List<Slab>();
        float gCeil = gy + geo["ground"]["ceilings"].Min(c => (float)c["y"][0]);
        if (ceilingOpenings != null)
            foreach (var h in ceilingOpenings)
            {
                float x0 = (float)h["x"][0], x1 = (float)h["x"][1], z0 = -(float)h["z"][1], z1 = -(float)h["z"][0], top = gy + (float)h["top"]; const float t = 0.14f;
                framing.Add(new Slab(new Vector3(x0 - t, gCeil, z0 - t), new Vector3(x0, top, z1 + t)));
                framing.Add(new Slab(new Vector3(x1, gCeil, z0 - t), new Vector3(x1 + t, top, z1 + t)));
                framing.Add(new Slab(new Vector3(x0, gCeil, z0 - t), new Vector3(x1, top, z0)));
                framing.Add(new Slab(new Vector3(x0, gCeil, z1), new Vector3(x1, top, z1 + t)));
                framing.Add(new Slab(new Vector3(x0 - t, top, z0 - t), new Vector3(x1 + t, top + 0.15f, z1 + t)));   // its ceiling
            }
        solids.AddRange(framing);   // skinned where they face out, like any wall
        bool Room(Vector3 p) => rooms.Any(r => p.y > r.y0 && p.y < r.y1 && Inside(r.pts, new Vector2(p.x, p.z)));
        bool Outside(Vector3 p) => !Room(p) && !solids.Any(s => In(s, p));

        var skins = new List<Slab>();
        foreach (var w in solids)   // walls, and the floor plates' and ceilings' edges (the band between the storeys)
        {
            float ym = (w.lo.y + w.hi.y) / 2;
            foreach (int ax in new[] { 0, 2 })        // the face's normal axis: x or z
                foreach (int sd in new[] { -1, 1 })
                {
                    int al = 2 - ax;                      // along the face
                    float face = sd < 0 ? w.lo[ax] : w.hi[ax], a0 = w.lo[al], a1 = w.hi[al];
                    Vector3 At(float a, float off, float y) { var v = new Vector3(0, y, 0); v[ax] = face + sd * off; v[al] = a; return v; }
                    bool Ext(float a) => Outside(At(a, 0.03f, ym));
                    // runs of exterior face, 1 cm steps; a run reaching the face's end turns the corner by the skin's thickness
                    float r0 = a0; bool on = Ext(a0 + 0.005f);
                    void Lay(float s0, float s1)
                    {
                        if (s1 - s0 < 0.005f) return;
                        if (s0 <= a0 + 1e-4f) s0 -= SkinT; if (s1 >= a1 - 1e-4f) s1 += SkinT;
                        float y0 = Outside(At((s0 + s1) / 2, 0.03f, w.lo.y - 0.05f)) ? w.lo.y - SkinT : w.lo.y;
                        float y1 = Outside(At((s0 + s1) / 2, 0.03f, w.hi.y + 0.05f)) ? w.hi.y + SkinT : w.hi.y;
                        Vector3 p = At(s0, 0f, y0), q = At(s1, SkinT, y1);
                        skins.Add(new Slab(p, q));
                    }
                    for (float a = a0 + 0.01f; a < a1; a += 0.01f) { bool x = Ext(Mathf.Min(a + 0.005f, a1 - 0.001f)); if (x != on) { if (on) Lay(r0, a); r0 = a; on = x; } }
                    if (on) Lay(r0, a1);
                }
        }
        // lids: every ceiling (and the attic shaft's cap) with nothing of the storey above over it, past the walls by LidOver
        var upFloor = geo["upstairs"]["floor"].Select(b => SpecSlab(b, 0f)).ToList();
        var lids = new List<Slab>();
        foreach (var (st, fy) in storeys)
            foreach (var c in st["ceilings"].Concat(fy == 0f ? atticBoxes.Where(b => (string)b["kind"] == "ceiling") : Enumerable.Empty<JToken>()))
            {
                var s = SpecSlab(c, fy);
                IEnumerable<Slab> lid = new[] { new Slab(new Vector3(s.lo.x - LidOver, s.hi.y, s.lo.z - LidOver), new Vector3(s.hi.x + LidOver, s.hi.y + LidT, s.hi.z + LidOver)) };
                if (fy != 0f)   // a ground ceiling under the upstairs floor plate is that floor's underside: no lid in the upstairs rooms
                    foreach (var f in upFloor) { var h = new Slab(new Vector3(f.lo.x, f.lo.y - 1f, f.lo.z), new Vector3(f.hi.x, f.hi.y + 1f, f.hi.z)); lid = lid.SelectMany(l => Minus(l, h)).ToList(); }
                lids.AddRange(lid);
            }
        foreach (var f in framing.Where((_, i) => i % 5 == 4))
            lids.Add(new Slab(new Vector3(f.lo.x - LidOver, f.hi.y, f.lo.z - LidOver), new Vector3(f.hi.x + LidOver, f.hi.y + LidT, f.hi.z + LidOver)));
        lids.AddRange(framing);   // the framing itself casts
        // the floor framing: between the ground ceilings' tops and the upstairs floor plate the spec leaves a band (~0.24 m) open to
        // every joint round it (the back stair's recess is lined with 2 cm boards only). A carpenter's floor is joists, solid: filled
        // under every upstairs floor plate down to the lowest ground ceiling, then clipped out of the rooms like everything else
        float band0 = gy + geo["ground"]["rooms"].Min(r => (float)r["ceil"]);
        foreach (var f in upFloor)   // over the ground floor only: past its front the upstairs overhangs the film's flush front (DEVIATIONS 1)
            foreach (var gf in GroundFootprint(geo, gy))
            {
                float x0 = Mathf.Max(f.lo.x, gf.lo.x), x1 = Mathf.Min(f.hi.x, gf.hi.x), z0 = Mathf.Max(f.lo.z, gf.lo.z), z1 = Mathf.Min(f.hi.z, gf.hi.z);
                if (x1 - x0 > 1e-3f && z1 - z0 > 1e-3f) lids.Add(new Slab(new Vector3(x0, band0, z0), new Vector3(x1, f.lo.y, z1)));
            }
        // openings cut back out of the skins: through the wall line, 0.45 m either side (wall half-thickness + skin + margin)
        var holes = new List<Slab>();
        foreach (var (st, fy) in storeys)
            foreach (var o in st["openings"])
            {
                bool alongX = (string)o["axis"] == "z"; float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"];
                foreach (var cut in o["cuts"])
                {
                    float y0 = (float)cut[0] + fy, y1 = (float)cut[1] + fy;
                    holes.Add(alongX ? new Slab(new Vector3(lo, y0, -c - 0.45f), new Vector3(hi, y1, -c + 0.45f))
                                     : new Slab(new Vector3(c - 0.45f, y0, -hi), new Vector3(c + 0.45f, y1, -lo)));
                }
            }
        if (wallOpenings != null)
            foreach (var o in wallOpenings)
            {
                var s = SpecSlab(o, gy);
                holes.Add(new Slab(s.lo - new Vector3(0.45f, 0f, 0f), s.hi + new Vector3(0.45f, 0f, 0f)));   // x: the wall's thickness (face at x)
            }
        foreach (var o in atticBoxes.Where(b => (string)b["kind"] == "opening"))   // the attic dormer's window (its wall faces x)
        {
            var s = SpecSlab(o, 0f);
            holes.Add(new Slab(s.lo - new Vector3(0.45f, 0f, 0f), s.hi + new Vector3(0.45f, 0f, 0f)));
        }
        foreach (var h in holes) skins = skins.SelectMany(s => Minus(s, h)).ToList();
        // never inside a room: corner turns and lid overhangs are clipped to the rooms' volumes (an invisible caster in a room is a shadow)
        var cells = new List<Slab>();
        foreach (var r in rooms)
        {
            var xs = r.pts.Select(v => v.x).Distinct().OrderBy(v => v).ToList(); var zs = r.pts.Select(v => v.y).Distinct().OrderBy(v => v).ToList();
            for (int i = 0; i + 1 < xs.Count; i++) for (int k = 0; k + 1 < zs.Count; k++)
                if (Inside(r.pts, new Vector2((xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2)))
                    cells.Add(new Slab(new Vector3(xs[i], r.y0, zs[k]), new Vector3(xs[i + 1], r.y1, zs[k + 1])));
        }
        foreach (var h in cells) { skins = skins.SelectMany(s => Minus(s, h)).ToList(); lids = lids.SelectMany(s => Minus(s, h)).ToList(); }

        var g = Child(root, "Envelope");
        float fySave = FloorY; FloorY = 0f;
        foreach (var s in skins.Concat(lids))
        {
            int before = g.transform.childCount;
            Box(g, "Envelope", s.lo.x, s.hi.x, s.lo.z, s.hi.z, s.lo.y, s.hi.y, mCeil);
            if (g.transform.childCount == before) continue;   // a sliver under 1 mm: not built
            var t = g.transform.GetChild(before).gameObject;
            Object.DestroyImmediate(t.GetComponent<Collider>());
            t.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.ShadowsOnly;
        }
        FloorY = fySave;
        Debug.Log($"Envelope: {skins.Count} skins, {lids.Count} lids, {holes.Count} openings cut");
    }

    // rooms as volumes (world): each storey's polygons to their ceilings; the attic stair's room runs on up its shaft to the cap, a
    // stair well down to the floor below
    internal static List<(string name, List<Vector2> pts, float y0, float y1)> EnvelopeRooms(JObject geo, JToken atticBoxes, float gy)
    {
        var cap = atticBoxes.Where(b => (string)b["kind"] == "ceiling").Select(b => SpecSlab(b, 0f)).ToList();
        return new[] { ((JObject)geo["upstairs"], 0f), ((JObject)geo["ground"], gy) }.SelectMany(s => s.Item1["rooms"].Select(r =>
        {
            var pts = r["poly"].Select(q => new Vector2((float)q[0], -(float)q[1])).ToList(); float y1 = s.Item2 + (float)r["ceil"];
            if (s.Item2 == 0f && (string)r["name"] == "attic_stair") foreach (var c in cap) y1 = Mathf.Max(y1, c.lo.y);   // the shaft runs up into the attic
            return ((string)r["name"], pts, y0: (string)r["opens"] == "down" ? gy : s.Item2, y1);   // a stair well is one space from the floor below (as SeamRooms)
        })).Concat(atticBoxes.Where(b => (string)b["kind"] == "room").Select(b =>   // the attic itself (SpecGreybox.Attic)
            ((string)b["name"], b["poly"].Select(q => new Vector2((float)q[0], -(float)q[1])).ToList(), (float)b["y"][0], (float)b["y"][1]))).ToList();
    }

    // Envelope check: from points just inside every room's wall-ceiling joint and wall foot, rays toward the sky (elevations 5-70 deg,
    // 24 azimuths) that leave the house through something opaque must pass at least 0.3 m of shadow caster; less is where a low sun
    // reads through (shadow-map bias). Rays that leave through an opening (nothing hit) are sun through a window, and pass; rays whose
    // last caster opens into another room or a doorway are an inner wall, not the envelope, and are skipped; so are points within 0.5 m of an
    // outside opening (rays clipping a jamb or a sill: the edge of its sun patch, not a leak, which runs the length of a joint). Only the
    // structure counts as caster (walls, ceilings, floors, the envelope): sash bars and doors are thin on purpose.
    static string EnvelopeCheck(JObject geo, JToken atticBoxes, JToken wallOpenings, float gy)
    {
        var temp = new List<Collider>();
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (r.enabled && r.shadowCastingMode != ShadowCastingMode.Off && r.GetComponent<Collider>() == null && r.GetComponent<MeshFilter>()?.sharedMesh is Mesh mesh)
            { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mesh; temp.Add(mc); }
        Physics.SyncTransforms();
        bool Caster(Collider c)
        {   // the house's structure: what the envelope must make thick (sash bars, doors and stair parts are thin on purpose)
            var r = c.GetComponent<MeshRenderer>(); var n = c.name; var top = c.transform.root.name;
            return r != null && r.enabled && r.shadowCastingMode != ShadowCastingMode.Off && (top == "Upstairs" || top == "Ground")
                && (n == "Wall" || n == "Ceiling" || n == "Envelope" || n.StartsWith("Floor"));
        }
        var rooms = EnvelopeRooms(geo, atticBoxes, gy);
        var doorways = new List<Slab>();   // every opening's volume through its wall: open air between two rooms or to the outside
        foreach (var (st, fy) in new[] { ((JObject)geo["upstairs"], 0f), ((JObject)geo["ground"], gy) })
            foreach (var o in st["openings"])
                foreach (var cut in o["cuts"])
                {
                    float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"], y0 = (float)cut[0] + fy, y1 = (float)cut[1] + fy;
                    doorways.Add((string)o["axis"] == "z" ? new Slab(new Vector3(lo, y0, -c - 0.2f), new Vector3(hi, y1, -c + 0.2f))
                                                          : new Slab(new Vector3(c - 0.2f, y0, -hi), new Vector3(c + 0.2f, y1, -lo)));
                }
        bool Room(Vector3 v) => rooms.Any(r => v.y > r.y0 && v.y < r.y1 && Inside(r.pts, new Vector2(v.x, v.z))) || doorways.Any(dw => In(dw, v));
        var dirs = new List<Vector3>();
        foreach (float el in new[] { 5f, 15f, 30f, 50f, 70f }) for (int k = 0; k < 24; k++)
            { float az = k * 15f * Mathf.Deg2Rad, e = el * Mathf.Deg2Rad; dirs.Add(new Vector3(Mathf.Cos(az) * Mathf.Cos(e), Mathf.Sin(e), Mathf.Sin(az) * Mathf.Cos(e))); }
        // openings as plan rectangles (world x, z) on their storey: a point within 0.5 m of one is at the edge of its sun patch
        var openings = new List<(float fy, Vector2 lo, Vector2 hi)>();
        foreach (var (st, fy) in new[] { ((JObject)geo["upstairs"], 0f), ((JObject)geo["ground"], gy) })
            foreach (var o in st["openings"].Where(q => q["between"].Count() == 1))   // to the outside
            {
                float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"];
                openings.Add((string)o["axis"] == "z" ? (fy, new Vector2(lo, -c - 0.1f), new Vector2(hi, -c + 0.1f)) : (fy, new Vector2(c - 0.1f, -hi), new Vector2(c + 0.1f, -lo)));
            }
        if (wallOpenings != null)
            foreach (var o in wallOpenings)
            {
                var w = SpecSlab(o, gy);
                foreach (var fy in new[] { 0f, gy }) if (w.hi.y > fy && w.lo.y < fy + 3f) openings.Add((fy, new Vector2(w.lo.x - 0.1f, w.lo.z), new Vector2(w.hi.x + 0.1f, w.hi.z)));
            }
        int pts = 0; var thin = new List<string>();
        foreach (var (st, fy) in new[] { ((JObject)geo["upstairs"], 0f), ((JObject)geo["ground"], gy) })
            foreach (var rm in st["rooms"])
            {
                var p = rm["poly"].Select(q => new Vector2((float)q[0], -(float)q[1])).ToList(); int n = p.Count; float ceil = (float)rm["ceil"];
                float area = 0f; for (int i = 0; i < n; i++) area += p[i].x * p[(i + 1) % n].y - p[(i + 1) % n].x * p[i].y;
                float sg = Mathf.Sign(area);
                for (int i = 0; i < n; i++)
                {
                    Vector2 a = p[i], b = p[(i + 1) % n]; float L = Vector2.Distance(a, b); if (L < 0.1f) continue;
                    Vector2 t = (b - a) / L, nOut = new Vector2(sg * t.y, -sg * t.x);
                    for (float s = 0.05f; s < L - 0.04f; s += 0.25f)
                        foreach (float y in new[] { ceil - 0.03f, 0.03f })
                        {
                            var q = a + t * s - nOut * 0.03f; var o = new Vector3(q.x, fy + y, q.y);
                            if (openings.Any(op => op.fy == fy && Vector2.Distance(new Vector2(Mathf.Clamp(q.x, op.lo.x, op.hi.x), Mathf.Clamp(q.y, op.lo.y, op.hi.y)), q) < 0.5f)) continue;
                            if (Physics.CheckSphere(o, 0.01f, ~0, QueryTriggerInteraction.Ignore)) continue;   // inside something (a step, a cabinet)
                            pts++; float worst = float.MaxValue; string via = "";
                            foreach (var d in dirs)
                            {
                                if (Vector2.Dot(new Vector2(d.x, d.z), nOut) < 0f && y < 0.1f) continue;   // the foot's rays go out through its own wall
                                const float R = 8f;
                                if (!Physics.RaycastAll(o, d, R, ~0, QueryTriggerInteraction.Ignore).Any(h => Caster(h.collider))) continue;   // out through an opening
                                var back = Physics.RaycastAll(o + d * R, -d, R, ~0, QueryTriggerInteraction.Ignore).Where(h => Caster(h.collider)).OrderBy(h => h.distance).FirstOrDefault();
                                if (back.collider == null) continue;
                                if (Room(back.point + d * 0.05f)) continue;   // its last crossing is an inner wall lit from another room: not the envelope
                                float depth = R - back.distance;   // from the point to the caster surface nearest the sun
                                if (depth < worst) { worst = depth; via = $"{back.collider.transform.parent?.name}/{back.collider.name}, out at spec ({back.point.x:F2}, {back.point.y:F2}, {-back.point.z:F2}) toward ({d.x:F2}, {d.y:F2}, {-d.z:F2})"; }
                            }
                            if (worst < 0.3f) thin.Add($"THIN    {(string)rm["name"]} at spec ({o.x:F2}, {o.y:F2}, {-o.z:F2}): {worst:F2} m of caster toward the sky, last {via}");
                        }
                }
            }
        foreach (var c in temp) Object.DestroyImmediate(c);
        Physics.SyncTransforms();
        return $"Envelope check: {pts} points at room joints, {thin.Count} see the sky through < 0.3 m of shadow caster\n" + string.Concat(thin.Take(30).Select(x => x + "\n"));
    }

    // The film's day light (user, Oct 16: chose "the film's set lighting" over physical window light). The interiors were a lit set: soft,
    // even, warm-neutral light from above, walls as bright as the frame's mean, windows blown out. Each room gets ceiling-wide rectangle
    // lights, one per rectangular cell of its outline, in the day layer and BAKED only (into the day's probes: no runtime cost, dark at
    // night). FillNits and FillKelvin are solved against matched film frames by tools/house/film_light_match.py. DEVIATIONS 44.
    // 300 -> 600 nits (Oct 17, changes/2026-10-17-filmfill-baked.json): until then the fills were ALSO drawn in real time (the bake left them
    // recorded as not baked, BakeLighting.CheckBakedLights), so 300 was tuned on double light; baked only, 600 gives back the same level.
    const float FillNits = 600f, FillKelvin = 5200f;

    static void FilmFill(GameObject dayLayer, JObject geo, JToken atticBoxes, float gy)
    {
        var g = Child(dayLayer, "FilmFill"); int n = 0;
        foreach (var r in EnvelopeRooms(geo, atticBoxes, gy))
        {
            var xs = r.pts.Select(v => v.x).Distinct().OrderBy(v => v).ToList(); var zs = r.pts.Select(v => v.y).Distinct().OrderBy(v => v).ToList();
            for (int i = 0; i + 1 < xs.Count; i++) for (int k = 0; k + 1 < zs.Count; k++)
            {
                float x0 = xs[i], x1 = xs[i + 1], z0 = zs[k], z1 = zs[k + 1];
                if (!Inside(r.pts, new Vector2((x0 + x1) / 2, (z0 + z1) / 2))) continue;
                var l = new GameObject("FilmFill_" + r.name).AddComponent<Light>(); l.transform.SetParent(g.transform, false);
                l.transform.position = new Vector3((x0 + x1) / 2, r.y1 - 0.02f, (z0 + z1) / 2);
                l.transform.rotation = Quaternion.Euler(90f, 0f, 0f);   // facing down
                l.gameObject.AddComponent<HDAdditionalLightData>();      // first: adding it resets the light
                l.type = LightType.Rectangle; l.areaSize = new Vector2(Mathf.Max(x1 - x0 - 0.1f, 0.1f), Mathf.Max(z1 - z0 - 0.1f, 0.1f));
                l.lightmapBakeType = LightmapBakeType.Baked; l.lightUnit = LightUnit.Nits; l.intensity = FillNits;
                l.useColorTemperature = true; l.colorTemperature = FillKelvin; l.color = Color.white; l.shadows = LightShadows.Soft;
                n++;
            }
        }
        Debug.Log($"FilmFill: {n} ceiling fills at {FillNits} nits, {FillKelvin} K");
    }

    // the ground floor's footprint (its floor plate, walls included), world rectangles
    static List<Slab> GroundFootprint(JObject geo, float gy) => geo["ground"]["floor"].Select(b => SpecSlab(b, gy)).ToList();

    static bool OverFootprint(List<Slab> fp, float x, float z, float grow) => fp.Any(f => x > f.lo.x - grow && x < f.hi.x + grow && z > f.lo.z - grow && z < f.hi.z + grow);

    // Stop-gap for the upstairs overhang (user, Oct 16: the lighting now, the split later; tasks/wall-grid-plan.md). Marina's upstairs
    // front rooms stick out 1.2-1.5 m past the film's flush front and shaded the ground floor's front windows (893 of 2210 sun points).
    // Light only, no geometry moves and nothing is hidden:
    //  - FilmFront: a shadows-only shell standing in for the film's flush upper storey. The ground floor's outer faces are carried up to
    //    the roof (0.25 m, corners turned), with a roof over the footprint and every opening of either storey cut out. Rendering layer 2.
    //  - every upstairs piece reaching past the footprint (more than the skin) is moved to rendering layer 1.
    //  - the sun's shadows (StoreyShadows) come from layers 0 + 2 while the player is on the ground floor, and 0 + 1 from the stair up.
    //  - the bake takes the house as built: the strip with its own walls, this shell left out (BakeLighting; Oct 17: baking the strip
    //    open and invalidating its probes left probe cells with no valid probe: bands of outdoor light along the front rooms' joints).
    public const uint LayerHouse = 1, LayerOverhang = 2, LayerFilmFront = 4;

    static void FilmFront(GameObject root, JObject geo, JToken wallOpenings, float gy)
    {
        var fp = GroundFootprint(geo, gy);
        var gWalls = geo["ground"]["walls"].Select(b => SpecSlab(b, gy)).ToList();
        float top = geo["upstairs"]["ceilings"].Max(c => (float)c["y"][1]) + LidT;
        var skins = new List<Slab>();
        foreach (var w in gWalls)
            foreach (int ax in new[] { 0, 2 })
                foreach (int sd in new[] { -1, 1 })
                {
                    int al = 2 - ax; float face = sd < 0 ? w.lo[ax] : w.hi[ax], a0 = w.lo[al], a1 = w.hi[al];
                    Vector3 At(float a, float off, float y) { var v = new Vector3(0, y, 0); v[ax] = face + sd * off; v[al] = a; return v; }
                    bool Out(float a) { var q = At(a, 0.03f, 0f); return !OverFootprint(fp, q.x, q.z, 0f); }
                    float r0 = a0; bool on = Out(a0 + 0.005f);
                    void Lay(float s0, float s1)
                    {
                        if (s1 - s0 < 0.005f) return;
                        skins.Add(new Slab(At(s0 - SkinT, 0f, gy + 2.0f), At(s1 + SkinT, SkinT, top)));
                    }
                    for (float a = a0 + 0.01f; a < a1; a += 0.01f) { bool x = Out(Mathf.Min(a + 0.005f, a1 - 0.001f)); if (x != on) { if (on) Lay(r0, a); r0 = a; on = x; } }
                    if (on) Lay(r0, a1);
                }
        foreach (var f in fp) skins.Add(new Slab(new Vector3(f.lo.x - LidOver, top - LidT, f.lo.z - LidOver), new Vector3(f.hi.x + LidOver, top, f.hi.z + LidOver)));
        // every opening of both storeys (and the landing window) cut back out, through 0.45 m either side of its wall line
        foreach (var (st, fy) in new[] { ((JObject)geo["upstairs"], 0f), ((JObject)geo["ground"], gy) })
            foreach (var o in st["openings"])
            {
                bool alongX = (string)o["axis"] == "z"; float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"];
                foreach (var cut in o["cuts"])
                {
                    float y0 = (float)cut[0] + fy, y1 = (float)cut[1] + fy;
                    var h = alongX ? new Slab(new Vector3(lo, y0, -c - 0.45f), new Vector3(hi, y1, -c + 0.45f)) : new Slab(new Vector3(c - 0.45f, y0, -hi), new Vector3(c + 0.45f, y1, -lo));
                    skins = skins.SelectMany(q => Minus(q, h)).ToList();
                }
            }
        if (wallOpenings != null)
            foreach (var o in wallOpenings) { var w = SpecSlab(o, gy); var h = new Slab(w.lo - new Vector3(0.45f, 0, 0), w.hi + new Vector3(0.45f, 0, 0)); skins = skins.SelectMany(q => Minus(q, h)).ToList(); }
        var g = Child(root, "FilmFront"); float fySave = FloorY; FloorY = 0f;
        foreach (var q in skins)
        {
            int before = g.transform.childCount;
            Box(g, "FilmFront", q.lo.x, q.hi.x, q.lo.z, q.hi.z, q.lo.y, q.hi.y, mCeil);
            if (g.transform.childCount == before) continue;
            var t = g.transform.GetChild(before).gameObject; Object.DestroyImmediate(t.GetComponent<Collider>());
            var r = t.GetComponent<MeshRenderer>(); r.shadowCastingMode = ShadowCastingMode.ShadowsOnly; r.renderingLayerMask = LayerFilmFront;
        }
        FloorY = fySave;
        // the overhang: upstairs pieces reaching past the footprint by more than the skin
        int tagged = 0;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
        {
            if (r.transform.root.name == "Ground" || r.name == "FilmFront" || r.transform.root.name == "Exterior") continue;
            var b = r.bounds; if (b.min.y < gy + 2.75f) continue;   // the ground storey's own skins, lids and fill sit lower
            bool past = false;
            for (int i = 0; i <= 4 && !past; i++) for (int k = 0; k <= 4 && !past; k++)
            {
                float x = Mathf.Lerp(b.min.x, b.max.x, i / 4f), z = Mathf.Lerp(b.min.z, b.max.z, k / 4f);
                past = !OverFootprint(fp, x, z, SkinT + 0.05f);
            }
            if (past) { r.renderingLayerMask = LayerOverhang; tagged++; }
        }
        Debug.Log($"FilmFront: {skins.Count} shell pieces; {tagged} upstairs pieces tagged as the overhang");
    }
}
