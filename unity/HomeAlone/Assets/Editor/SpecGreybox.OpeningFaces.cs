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
}
