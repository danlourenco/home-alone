using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

// Door faces (walk note 2026-10-17 20:38, Buzz's room: "green vertical hands above the door and the missing header casing"). For every
// door in spec/openings.json, on each face that faces a room, reading the BUILT scene (either casing path, any producer):
//   NO HEAD   rays at the head casing's middle height across the opening meet bare wall or nothing (no casing, no frame)
//   PAINT     a wall within the casing width (lo - 7 cm .. hi + 7 cm, floor to ceiling) shows the OTHER room's finish there and not
//             this room's: a room's finish is the set of wall materials its own walls show (>= 15% of rays from inside its outline)
// Both must read 0. Standalone on a saved scene: Unity -batchmode -projectPath <scratch> -executeMethod SpecGreybox.OpeningFaceCheckScene
// -quit (result in Library/OpeningFaceCheck.txt).
public static partial class SpecGreybox
{
    public static void OpeningFaceCheckScene()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity", OpenSceneMode.Single);
        var r = OpeningFaceCheck();
        File.WriteAllText("Library/OpeningFaceCheck.txt", r); Debug.Log(r);
    }

    static string OpeningFaceCheck()
    {
        var geo = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/geometry.json")));
        var ops = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/openings.json")));
        float gy = (float)geo["ground"]["floor_y"]; const float half = 0.07f, cw = 0.07f;
        var temp = new List<Collider>();
        foreach (var mr in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (mr.enabled && mr.GetComponent<Collider>() == null && mr.GetComponent<MeshFilter>()?.sharedMesh is Mesh mesh)
            { var mc = mr.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mesh; temp.Add(mc); }
        Physics.SyncTransforms();
        // ray from 15 cm in front of the face toward it, at spec (along s on a face of plane c, normal n, axis = the face runs along x or z), height y (world): the wall it meets
        RaycastHit? Ray(string ax, float c, float n, float s, float y, float max)
        {
            float a = c + n * (half + 0.15f);   // 15 cm in front of the face: clear of casing (2 cm) and pack frames (6.5 cm)
            var o = ax == "x" ? new Vector3(s, y, -a) : new Vector3(a, y, -s);
            var d = ax == "x" ? new Vector3(0, 0, n) : new Vector3(-n, 0, 0);
            if (Physics.CheckSphere(o, 0.005f, ~0, QueryTriggerInteraction.Ignore)) return null;
            return Physics.Raycast(o, d, out var h, max, ~0, QueryTriggerInteraction.Ignore) ? h : (RaycastHit?)new RaycastHit();
        }
        string MatOf(RaycastHit h) => h.collider != null && h.collider.name == "Wall" ? h.collider.GetComponent<MeshRenderer>()?.sharedMaterial?.name : null;
        var rooms = new Dictionary<string, (JToken rm, float fy)>();
        foreach (var (st, fy) in new[] { ("upstairs", 0f), ("ground", gy) })
            foreach (var rm in geo[st]["rooms"]) rooms[st + ":" + (string)rm["name"]] = (rm, fy);
        var finish = new Dictionary<string, HashSet<string>>();
        HashSet<string> Finish(string key)
        {   // the wall materials a room's own walls show (rays 10 cm inside its outline toward it, at 0.5 and 1.5 m)
            if (finish.TryGetValue(key, out var f)) return f;
            var (rm, fy) = rooms[key]; var p = rm["poly"].Select(q => new Vector2((float)q[0], (float)q[1])).ToList(); int n = p.Count;
            float area = 0f; for (int i = 0; i < n; i++) area += p[i].x * p[(i + 1) % n].y - p[(i + 1) % n].x * p[i].y;
            float sg = Mathf.Sign(area); var count = new Dictionary<string, int>(); int all = 0;
            for (int i = 0; i < n; i++)
            {
                Vector2 a = p[i], b = p[(i + 1) % n], t = (b - a).normalized, nOut = new(sg * t.y, -sg * t.x); float L = Vector2.Distance(a, b);
                if (Mathf.Abs(t.x) > 1e-4f && Mathf.Abs(t.y) > 1e-4f) continue;
                for (float s = 0.15f; s < L - 0.15f; s += 0.25f)
                    foreach (float y in new[] { 0.5f, 1.5f })
                    {
                        var q = a + t * s - nOut * 0.10f; var o = new Vector3(q.x, fy + y, -q.y); var d = new Vector3(nOut.x, 0, -nOut.y);
                        if (Physics.Raycast(o, d, out var h, 0.14f, ~0, QueryTriggerInteraction.Ignore) && MatOf(h) is string m) { count[m] = count.GetValueOrDefault(m) + 1; all++; }
                    }
            }
            return finish[key] = count.Where(kv => kv.Value >= 0.15f * all).Select(kv => kv.Key).ToHashSet();
        }
        var bad = new List<string>(); int faces = 0, noHead = 0, paint = 0;
        foreach (var r in ops["openings"].Where(r => (string)r["kind"] == "door" && r["model"].Type == JTokenType.Null))
        {
            string st = (string)r["storey"], ax = (string)r["axis"] == "x" ? "z" : "x";   // ax: the axis the face runs along
            float c = (float)r["c"], lo = (float)r["lo"], hi = (float)r["hi"], head = (float)r["head"], m = (lo + hi) / 2, fy = st == "ground" ? gy : 0f;
            string RoomAt(float n)
            {
                float a = c + n * (half + 0.3f); var pt = ax == "x" ? new Vector2(m, a) : new Vector2(a, m);
                return rooms.Where(kv => kv.Key.StartsWith(st + ":") && Inside(kv.Value.rm["poly"].Select(q => new Vector2((float)q[0], (float)q[1])).ToList(), pt)).Select(kv => kv.Key).FirstOrDefault();
            }
            foreach (float n in new[] { -1f, 1f })
            {
                string me = RoomAt(n), other = RoomAt(-n);
                if (me == null || other == null) continue;
                faces++; var room = (float)rooms[me].rm["ceil"]; string id = (string)r["id"], side = me.Split(':')[1] + " face";
                int bare = 0, tot = 0;
                for (float s = lo + 0.03f; s <= hi - 0.03f; s += 0.02f)
                {
                    var h = Ray(ax, c, n, s, fy + head + cw / 2, 0.20f); if (h == null) continue; tot++;
                    var hv = h.Value; if (hv.collider == null || hv.collider.name == "Wall" || hv.distance > 0.148f) bare++;   // nothing proud of the face
                }
                if (tot > 0 && bare > tot / 2) { noHead++; bad.Add($"NO HEAD {id}: {side}, {bare}/{tot} rays at the head casing's height meet bare wall or nothing"); }
                var mine = Finish(me); var theirs = Finish(other).Except(mine).ToHashSet();
                if (theirs.Count == 0) continue;
                var hits = new Dictionary<string, (int k, float s0, float s1, float y0, float y1)>();
                for (float s = lo - cw + 0.005f; s < hi + cw; s += 0.01f)
                    for (float y = 0.02f; y < room - 0.01f; y += 0.02f)
                    {
                        var h = Ray(ax, c, n, s, fy + y, 0.20f);   // reaches 5 cm into the wall, never its far face
                        if (h == null || !(MatOf(h.Value) is string mt) || !theirs.Contains(mt)) continue;
                        var e = hits.TryGetValue(mt, out var e0) ? e0 : (k: 0, s0: 99f, s1: -99f, y0: 99f, y1: -99f);
                        hits[mt] = (e.k + 1, Mathf.Min(e.s0, s), Mathf.Max(e.s1, s), Mathf.Min(e.y0, y), Mathf.Max(e.y1, y));
                    }
                foreach (var kv in hits.Where(kv => kv.Value.k >= 3))
                {
                    paint++; var v = kv.Value;
                    bad.Add($"PAINT   {id}: {side} shows {other.Split(':')[1]}'s {kv.Key} within the casing width ({v.k} rays, spec {ax} {v.s0:F3}-{v.s1:F3}, y {v.y0:F2}-{v.y1:F2})");
                }
            }
        }
        foreach (var col in temp) Object.DestroyImmediate(col);
        Physics.SyncTransforms();
        return $"Opening face check: {faces} door faces, {noHead} without a head casing, {paint} showing the other room's finish within the casing width\n"
               + string.Concat(bad.Take(30).Select(b => b + "\n"));
    }
    // OPENING CLEAR (Oct 20, walk note 06:49 "what's with this wall blocking the doorway?": the hall bath's tile wainscot ran straight across
    // its door; no collider (walk test ok), crossing no other mesh (clash 0), and the review render stood inside the room). For every
    // door, arch and window in spec/openings.json: a grid of rays perpendicular to the wall through the passage, from 0.4 m before one
    // face to 0.4 m past the other (windows: 5 cm, the reveal: a sofa may stand at a window) (doors/arches 0.1 m over the floor to 0.1 m under the head or springing, windows over the glass), tested
    // against every enabled visible mesh (temporary mesh colliders, as OpeningFaceCheck). The opening's own leaf, frame, glass and window
    // dressing (curtains, sheers, lace, blinds) are skipped by name. Standalone: -executeMethod SpecGreybox.OpeningClearCheckScene
    // (Library/OpeningClearCheck.txt).
    public static void OpeningClearCheckScene()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity", OpenSceneMode.Single);
        var r = OpeningClearCheck();
        File.WriteAllText("Library/OpeningClearCheck.txt", r); Debug.Log(r);
    }

    // whole name tokens (split at _ / space / digits / camelCase), so "Panel", "Fireplace" or "PlacedProps" never count as a pane or lace
    static readonly HashSet<string> OwnParts = new HashSet<string> { "door", "doors", "leaf", "window", "windows", "glass", "glazing", "sash",
        "muntin", "muntins", "pane", "panes", "casing", "jamb", "curtain", "curtains", "sheer", "sheers", "lace", "drape", "drapes", "valance",
        "blind", "blinds", "shade", "shades", "voile", "backdrop", "arch" };   // backdrop: a view card outside a window (Buzz's POV)
    // Known, reasoned exceptions (as ClashAllowed): (opening id, renderer name, why). Listed in the report as ALLOWED; anything else fails.
    static readonly (string id, string mesh, string why)[] OpeningClearAllowed = {
        ("upstairs:door:closet_1|kevin_jeff_room:8.074", "KV_GloveLeather", "the boxing gloves hang on the closet door's knob (Marina 380/383): leaf-mounted"),
        ("upstairs:arch:hall_corridor|hall_corridor_south:5.764", "Ficus_Tree_hall", "PRE-EXISTING, review: the hall ficus beside the south arch reaches into its passage (Oct 20 first run)"),
        ("upstairs:arch:hall_corridor|hall_corridor_south:5.764", "Ficus_Pot_hall", "PRE-EXISTING, review: as the ficus"),
        ("upstairs:arch:hall_corridor|hall_corridor_south:5.764", "Poin_hall_urn3", "PRE-EXISTING, review: a poinsettia urn beside the south arch"),
        ("upstairs:arch:hall_corridor|hall_corridor_south:5.764", "Urn", "PRE-EXISTING, review: the urn beside the south arch"),
        ("upstairs:arch:hall_corridor|hall_corridor_south:5.764", "Wood", "PRE-EXISTING, review: the urn's stand (HallDressing)"),
        ("upstairs:arch:hall_corridor|hall_corridor_south:5.764", "Soil", "PRE-EXISTING, review: the urn's soil (HallDressing)"),
        ("ground:arch:foyer|rear_passage:8.855", "Velvet", "PRE-EXISTING, review: the foyer's velvet seat within 0.4 m of the rear passage arch"),
        ("ground:arch:foyer|rear_passage:8.855", "Wood", "PRE-EXISTING, review: the same seat's frame"),
        ("upstairs:window:buzz_room:10.197", "Wall", "PRE-EXISTING, review: one row of rays meets wall inside this window's reveal (cut vs opening data)"),
    };
    static IEnumerable<string> Tokens(string name) =>
        System.Text.RegularExpressions.Regex.Matches(name, "[A-Z]?[a-z]+|[A-Z]+(?![a-z])").Cast<System.Text.RegularExpressions.Match>().Select(m => m.Value.ToLowerInvariant());

    static string OpeningClearCheck()
    {
        var geo = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/geometry.json")));
        var ops = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/openings.json")));
        float gy = (float)geo["ground"]["floor_y"];
        var temp = new List<Collider>();
        foreach (var mr in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (mr.enabled && mr.GetComponent<Collider>() == null && mr.GetComponent<MeshFilter>()?.sharedMesh is Mesh mesh)
            { var mc = mr.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mesh; temp.Add(mc); }
        Physics.SyncTransforms();
        string PathOf(Transform t) { var s = t.name; while (t.parent != null) { t = t.parent; s = t.name + "/" + s; } return s; }
        bool Own(Transform t) { for (; t != null; t = t.parent) if (Tokens(t.name).Any(OwnParts.Contains)) return true; return false; }
        var bad = new List<string>(); var allowed = new List<string>(); int n = 0, nBad = 0;
        foreach (var o in ops["openings"].Where(o => new[] { "door", "arch", "window" }.Contains((string)o["kind"])))
        {
            n++; string ax = (string)o["axis"], kind = (string)o["kind"];
            float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"], head = (float)o["head"], fy = (string)o["storey"] == "ground" ? gy : 0f;
            if (!(o["header"]?["box"] is JArray hb)) { n--; continue; }   // a model assembly with no header (the front door + sidelights): EntranceCheck walks it
            float f0 = ax == "x" ? (float)hb[0] : (float)hb[2], f1 = ax == "x" ? (float)hb[1] : (float)hb[3];
            float y0 = kind == "window" ? (float)o["sill"] + 0.05f : 0.10f;
            float y1 = (kind == "arch" && o["spring"]?.Type == JTokenType.Float ? (float)o["spring"] : head) - (kind == "window" ? 0.05f : 0.10f);
            float reach = kind == "window" ? 0.05f : 0.4f;   // doors/arches: the walked passage; windows: the reveal (furniture may stand at a window)
            float a0 = f0 - reach, len = f1 - f0 + 2 * reach;
            var hitBy = new Dictionary<string, int>();
            for (float s = lo + 0.05f; s <= hi - 0.05f + 1e-4f; s += 0.1f)
                for (float y = y0; y <= y1 + 1e-4f; y += 0.1f)
                {
                    var org = ax == "x" ? new Vector3(a0, fy + y, -s) : new Vector3(s, fy + y, -a0);
                    var dir = ax == "x" ? Vector3.right : Vector3.back;   // spec +x / spec +z
                    foreach (var h in Physics.RaycastAll(org, dir, len, ~0, QueryTriggerInteraction.Ignore))
                    {
                        var r = h.collider.GetComponent<MeshRenderer>();
                        if (r == null || !r.enabled || Own(h.collider.transform)) continue;
                        var k = PathOf(h.collider.transform); hitBy[k] = hitBy.GetValueOrDefault(k) + 1;
                    }
                }
            foreach (var k in hitBy.Keys.ToList())
            {
                var al = OpeningClearAllowed.FirstOrDefault(a => a.id == (string)o["id"] && k.Split('/').Last() == a.mesh);
                if (al.id != null) { allowed.Add($"ALLOWED {(string)o["id"]}: {k} ({hitBy[k]} rays): {al.why}"); hitBy.Remove(k); }
            }
            if (hitBy.Count == 0) continue;
            nBad++;
            bad.Add($"BLOCKS  {(string)o["id"]}: " + string.Join(", ", hitBy.OrderByDescending(kv => kv.Value).Take(4).Select(kv => $"{kv.Key} ({kv.Value} rays)")));
        }
        foreach (var col in temp) Object.DestroyImmediate(col);
        Physics.SyncTransforms();
        return $"Opening clear check: {n} openings, {nBad} with a visible mesh in the passage ({allowed.Count} allowed)\n" + string.Concat(bad.Take(40).Concat(allowed).Select(b => b + "\n"));
    }
}
