using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;

// SPLIT CHECK (walk note 2026-10-20 20:56, standing in the parents' bedroom doorway: "if i stop at just the right time... weird
// artifacts": the exterior roof, gutter and icicles inside the room and its ceiling gone). HouseSplit tested the camera against the
// upstairs ROOM outlines, which leave out every wall's thickness and doorway, so a camera in a doorway was "outside". Samples are taken
// from spec/geometry.json and spec/house_spec.json directly (not from HouseSplit's arrays): through every upstairs door, arch and
// opening (+-0.5 m across the wall, the whole width), through every upstairs wall's thickness, on a 0.25 m grid in every room, and over
// every main-stair and attic-stair tread, landing and floor, at the eyes the player can have (Kevin crouched 0.40, Kevin 1.10, adult 1.65). Every sample
// above switchY must be Upstairs(); with the hysteresis, 5 cm under switchY must stay upstairs once there. Negatives: ground-floor
// rooms and 1 m outside the upstairs floor plate must not be. The old rooms-only test is reported beside it (before/after).
// Standalone on a saved scene: -executeMethod SpecGreybox.SplitCheckScene (Library/SplitCheck.txt).
public static partial class SpecGreybox
{
    public static void SplitCheckScene()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity", OpenSceneMode.Single);
        var r = SplitCheck();
        File.WriteAllText("Library/SplitCheck.txt", r); Debug.Log(r);
    }

    static string SplitCheck()
    {
        var hs = Object.FindObjectsByType<HouseSplit>(FindObjectsInactive.Include).FirstOrDefault();
        if (hs == null) return "Split check: FAIL no HouseSplit\n";
        var geo = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/geometry.json")));
        var spec = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/house_spec.json")));
        var up = geo["upstairs"]; float gy = (float)geo["ground"]["floor_y"];
        float[] eyes = { 0.40f, 1.10f, 1.65f };
        var samples = new List<(string what, Vector3 p)>();   // expected upstairs where p.y > switchY
        void Add(string what, float x, float z, float floorY) { foreach (var e in eyes) samples.Add((what, new Vector3(x, floorY + e, -z))); }
        foreach (var o in up["openings"])
        {
            string k = (string)o["kind"]; if (k == "window" || k == "fake_door" || k == "rail") continue;
            float lo = (float)o["lo"], hi = (float)o["hi"], c = (float)o["c"]; bool az = (string)o["axis"] == "z";
            string what = $"{k} {string.Join("/", o["between"].Select(b => (string)b))}";
            for (int i = 0; i <= 10; i++) for (int j = 0; j <= 20; j++)
            {
                float along = Mathf.Lerp(lo + 0.02f, hi - 0.02f, i / 10f), across = c - 0.5f + j * 0.05f;
                if (az) Add(what, along, across, 0f); else Add(what, across, along, 0f);
            }
        }
        foreach (var w in up["walls"])
        {
            float x0 = (float)w["x"][0], x1 = (float)w["x"][1], z0 = (float)w["z"][0], z1 = (float)w["z"][1];
            for (int i = 0; i <= 4; i++) for (int j = 0; j <= 4; j++) Add($"wall x {x0:F2}-{x1:F2} z {z0:F2}-{z1:F2}", Mathf.Lerp(x0, x1, i / 4f), Mathf.Lerp(z0, z1, j / 4f), 0f);
        }
        bool InPoly(JToken poly, float x, float z)
        {
            var P = poly.Select(q => new Vector2((float)q[0], (float)q[1])).ToArray(); bool c = false;
            for (int i = 0, j = P.Length - 1; i < P.Length; j = i++) if ((P[i].y > z) != (P[j].y > z) && x < (P[j].x - P[i].x) * (z - P[i].y) / (P[j].y - P[i].y) + P[i].x) c = !c;
            return c;
        }
        foreach (var rm in up["rooms"])
        {
            var xs = rm["poly"].Select(q => (float)q[0]).ToList(); var zs = rm["poly"].Select(q => (float)q[1]).ToList();
            for (float x = xs.Min() + 0.05f; x < xs.Max(); x += 0.25f) for (float z = zs.Min() + 0.05f; z < zs.Max(); z += 0.25f)
                if (InPoly(rm["poly"], x, z)) Add("room " + (string)rm["name"], x, z, 0f);
        }
        foreach (var (boxes, name) in new[] { (spec["stair"]["boxes"], "main stair"), (spec["attic_stair"]["boxes"], "attic stair") })
            foreach (var b in boxes.Where(b => new[] { "step", "landing", "floor", "room" }.Contains((string)b["kind"])))   // where a player stands
            {
                float x0 = (float)b["x"][0], x1 = (float)b["x"][1], z0 = (float)b["z"][0], z1 = (float)b["z"][1], top = (float)b["y"][1];
                for (int i = 0; i <= 4; i++) for (int j = 0; j <= 4; j++) Add($"{name} {(string)b["name"]}", Mathf.Lerp(x0 + 0.02f, x1 - 0.02f, i / 4f), Mathf.Lerp(z0 + 0.02f, z1 - 0.02f, j / 4f), top);
            }
        var above = samples.Where(s => s.p.y > hs.switchY).ToList();
        var fails = above.Where(s => !hs.Upstairs(s.p)).ToList();
        var oldOut = above.Count(s => !hs.InEnvelope(new Vector2(s.p.x, s.p.z), 0f, hs.roomPolys));
        // hysteresis: up there, a dip 5 cm under switchY (the walking bob, a crouch on the stair) keeps the upstairs; from below it does not
        var stairTop = samples.Where(s => s.what.StartsWith("main stair") && s.p.y > hs.switchY && s.p.y < hs.switchY + 0.3f).Select(s => new Vector3(s.p.x, hs.switchY - 0.05f, s.p.z)).ToList();
        int hystFail = stairTop.Count(p => !hs.Upstairs(p, true)) + stairTop.Count(p => hs.Upstairs(p, false));
        // negatives: the ground floor's rooms at its eyes, and 1 m outside the upstairs floor plate (the yard, at an upstairs eye)
        var neg = new List<(string what, Vector3 p)>();
        foreach (var rm in geo["ground"]["rooms"])
        {
            var xs = rm["poly"].Select(q => (float)q[0]).ToList(); var zs = rm["poly"].Select(q => (float)q[1]).ToList();
            float cx = (xs.Min() + xs.Max()) / 2, cz = (zs.Min() + zs.Max()) / 2;
            if (InPoly(rm["poly"], cx, cz)) foreach (var e in eyes) neg.Add(("ground " + (string)rm["name"], new Vector3(cx, gy + e, -cz)));
        }
        var fl = up["floor"].ToList();
        float fx0 = fl.Min(f => (float)f["x"][0]), fx1 = fl.Max(f => (float)f["x"][1]), fz0 = fl.Min(f => (float)f["z"][0]), fz1 = fl.Max(f => (float)f["z"][1]);
        for (float z = fz0; z <= fz1; z += 0.5f) { neg.Add(("yard front", new Vector3(fx1 + 1f, 1.65f, -z))); neg.Add(("yard back", new Vector3(fx0 - 1f, 1.65f, -z))); }
        for (float x = fx0; x <= fx1; x += 0.5f) { neg.Add(("yard end", new Vector3(x, 1.65f, -(fz0 - 1f)))); neg.Add(("yard end", new Vector3(x, 1.65f, -(fz1 + 1f)))); }
        var negFails = neg.Where(s => hs.Upstairs(s.p)).ToList();
        var r = $"Split check: {above.Count} upstairs samples above switchY {hs.switchY:F3} (doorways, walls, rooms, stairs; eyes 0.40/1.10/1.65): " +
                $"{fails.Count} not upstairs (rooms-only test, before Oct 20: {oldOut}); hysteresis {hystFail} wrong of {stairTop.Count * 2}; {negFails.Count} of {neg.Count} ground/yard samples upstairs\n";
        foreach (var g in fails.GroupBy(s => s.what).Take(20)) r += $"FAIL split: {g.Key}: {g.Count()} samples not upstairs, e.g. world ({g.First().p.x:F2}, {g.First().p.y:F2}, {g.First().p.z:F2})\n";
        foreach (var g in negFails.GroupBy(s => s.what).Take(10)) r += $"FAIL split: {g.Key}: {g.Count()} samples upstairs, e.g. world ({g.First().p.x:F2}, {g.First().p.y:F2}, {g.First().p.z:F2})\n";
        if (hystFail > 0) r += $"FAIL split: hysteresis at the stair head: {hystFail} samples\n";
        return r;
    }
}
