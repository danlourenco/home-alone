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
                Box(parent, "Casing", b[0], b[1], -b[3], -b[2], b[4], b[5], mProp); n++;
            }
        }
        FloorY = keep;
        Debug.Log($"LayCasings: {n} casing pieces from spec/openings.json ({Openings["openings"].Sum(r => r["dropped"].Count())} dropped by recorded decision)");
    }

    // the rough opening a model window is cut to (under its stool), else the measured cut
    static float CutBottom(JToken o) =>
        OpeningsOwnTrim && Openings["openings"].FirstOrDefault(r => (string)r["id"] == "ground:wall_opening:" + (string)o["name"])?["rough"] is JToken rough
            ? (float)rough["y"][0] : (float)o["y"][0];
}
