using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;

// HOUSE-KERNEL step 2 (docs/HOUSE-KERNEL.md, stage 3): openings own their casing, header and limits. tools/house/openings.py writes
// spec/openings.json: every opening's casing pieces per face (refused at data time if a limit breaks: head under the header, header
// under the ceiling, a door's swing has room; trim it would cover is a recorded "dropped" decision). This file lays the pieces whose
// "by" is null; models and store props draw the rest. spec/trim_faces.json is cut at the same boxes, so the trim ends at the casing.
// THE SWITCH is openings.py OWN_TRIM (written as "own_trim"): false = the old per-case casing in Storey/ArchTop (Trim()).
public static partial class SpecGreybox
{
    static bool OpeningsOwnTrim;   // set by LoadOpenings (BuildWallGrid only); every other builder keeps the per-case casing
    static JObject Openings;

    static void LoadOpenings()
    {
        var j = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/openings.json")));
        using var sha = System.Security.Cryptography.SHA256.Create();
        foreach (var kv in (JObject)j["inputs"])
        {   // fail closed on stale data (as LoadTrimFaces): the generator's own freshness is openings.py --check
            if (!kv.Key.StartsWith("spec/")) continue;
            var h = string.Concat(sha.ComputeHash(File.ReadAllBytes(Path.Combine(RepoRoot, kv.Key))).Select(b => b.ToString("x2")));
            if (h != (string)kv.Value) throw new System.InvalidOperationException($"spec/openings.json is stale ({kv.Key} changed): run python3 tools/house/openings.py");
        }
        Openings = j; OpeningsOwnTrim = (bool)j["own_trim"];
    }

    // the casing SpecGreybox draws (by null), in each storey's Openings group, named "Casing" as before (the checks and FrenchDoors find it)
    static void LayCasings(GameObject root, GameObject groot)
    {
        if (!OpeningsOwnTrim) return;
        float keep = FloorY; FloorY = 0f; int n = 0;   // boxes are world y
        foreach (var r in Openings["openings"])
        {
            var parent = ((string)r["storey"] == "upstairs" ? root : groot).transform.Find("Openings").gameObject;
            foreach (var pc in r["pieces"].Where(p => p["by"].Type == JTokenType.Null && (string)p["part"] != "prop"))
            {
                var b = pc["box"].Select(v => (float)v).ToArray();   // spec x, spec z, world y
                if (pc["in_wall"] != null) CarveWalls(new Vector3(b[0], b[4], -b[3]), new Vector3(b[1], b[5], -b[2]));   // a jamb liner: the wall gives way
                Box(parent, "Casing", b[0], b[1], -b[3], -b[2], b[4], b[5], mProp); n++;
            }
        }
        FloorY = keep;
        Debug.Log($"LayCasings: {n} casing pieces from spec/openings.json ({Openings["openings"].Sum(r => r["dropped"].Count())} dropped by recorded decision)");
    }

    // a jamb liner stands in the wall behind the cut's face (openings.py `lined`): every Wall box it overlaps is replaced by the pieces
    // round it (copies keep material and collider, as CutWallOpenings), so the cut's face is the liner's painted face, not the wall's paper
    static void CarveWalls(Vector3 lo, Vector3 hi)
    {
        foreach (var r in Object.FindObjectsByType<MeshRenderer>().Where(r => r.name == "Wall").ToList())
        {
            var b = r.bounds;
            if (b.min.x >= hi.x - 1e-4f || b.max.x <= lo.x + 1e-4f || b.min.y >= hi.y - 1e-4f || b.max.y <= lo.y + 1e-4f || b.min.z >= hi.z - 1e-4f || b.max.z <= lo.z + 1e-4f) continue;
            void Piece(Vector3 a, Vector3 c)
            {
                if (c.x - a.x < 1e-3f || c.y - a.y < 1e-3f || c.z - a.z < 1e-3f) return;
                var g = Object.Instantiate(r.gameObject, r.transform.parent); g.name = "Wall";
                g.transform.position = (a + c) / 2; g.transform.localScale = c - a;
            }
            float x0 = Mathf.Max(b.min.x, lo.x), x1 = Mathf.Min(b.max.x, hi.x), y0 = Mathf.Max(b.min.y, lo.y), y1 = Mathf.Min(b.max.y, hi.y);
            Piece(b.min, new Vector3(lo.x, b.max.y, b.max.z)); Piece(new Vector3(hi.x, b.min.y, b.min.z), b.max);
            Piece(new Vector3(x0, b.min.y, b.min.z), new Vector3(x1, lo.y, b.max.z)); Piece(new Vector3(x0, hi.y, b.min.z), new Vector3(x1, b.max.y, b.max.z));
            Piece(new Vector3(x0, y0, b.min.z), new Vector3(x1, y1, lo.z)); Piece(new Vector3(x0, y0, hi.z), new Vector3(x1, y1, b.max.z));
            Object.DestroyImmediate(r.gameObject);
        }
    }

    // the rough opening a model window is cut to (under its stool), else the measured cut
    static float CutBottom(JToken o) =>
        OpeningsOwnTrim && Openings["openings"].FirstOrDefault(r => (string)r["id"] == "ground:wall_opening:" + (string)o["name"])?["rough"] is JToken rough
            ? (float)rough["y"][0] : (float)o["y"][0];
}
