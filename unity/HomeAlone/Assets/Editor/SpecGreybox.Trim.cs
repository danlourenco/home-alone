using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// HOUSE-KERNEL step 1 (docs/HOUSE-KERNEL.md, stage 7): trim from FACES. tools/house/trim_faces.py computes every visible wall face's
// run (room outlines, the main stair's rakes, the landings' edges, merged into one line where they touch) and the baseboard, cap rail,
// skirt, raking panel and rail along it, cut at casings and prop doors made from the same openings: spec/trim_faces.json. This file
// lays those strips and runs the Trim check over those runs. The old path (room outlines -> LayTrim, plus the stair model's own
// skirt/panel/rail) stays behind the switch.
public static partial class SpecGreybox
{
    // THE SWITCH (one line): true = trim from the face model; false = the old outline trim + the stair model's StairWallTrim part.
    const bool TrimFromFaces = true;

    static string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "../../.."));

    // spec/trim_faces.json, refused when any input changed since it was written (fail closed: a stale face model is never laid)
    static JObject LoadTrimFaces()
    {
        var j = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/trim_faces.json")));
        using var sha = System.Security.Cryptography.SHA256.Create();
        foreach (var kv in (JObject)j["inputs"])
        {   // the house's data (spec/; the scratch build copy links only spec/): the generator script's own freshness is trim_faces.py --check
            if (!kv.Key.StartsWith("spec/")) continue;
            var h = string.Concat(sha.ComputeHash(File.ReadAllBytes(Path.Combine(RepoRoot, kv.Key))).Select(b => b.ToString("x2")));
            if (h != (string)kv.Value) throw new System.InvalidOperationException($"spec/trim_faces.json is stale ({kv.Key} changed): run python3 tools/house/trim_faces.py");
        }
        return j;
    }

    static Material TrimMat() => DressMat(Dress["walls"]["wainscot"]);   // the house's trim/wainscot white (Storey's wsMat)

    static void FaceTrim(GameObject groot)
    {
        var j = LoadTrimFaces(); var m = TrimMat();
        TrimRuns.Clear();
        var raked = new List<JToken>();
        foreach (var s in j["strips"])
        {
            if (!(bool)s["flat"]) { raked.Add(s); continue; }
            string ax = (string)s["axis"]; float c = (float)s["c"], n = (float)s["n"], d0 = (float)s["d"][0], d1 = (float)s["d"][1];
            float s0 = (float)s["st"][0][0], s1 = (float)s["st"][1][0], y0 = (float)s["st"][0][1], y1 = (float)s["st"][0][2];
            float w0 = Mathf.Min(c + n * d0, c + n * d1), w1 = Mathf.Max(c + n * d0, c + n * d1);
            TrimRuns.Add(ax == "x" ? (new Vector3(s0, y0, w0), new Vector3(s1, y1, w1), m) : (new Vector3(w0, y0, s0), new Vector3(w1, y1, s1), m));
        }
        // the one wall-mounted model the face model does not know yet (kernel step 2: openings own their trim): the front door's frame
        LayTrim(groot, new[] { "FrontDoor_HiFi" });
        var g = groot.transform.Find("Trim").gameObject;
        foreach (var s in raked) StripMesh(g, s, m);
        Debug.Log($"FaceTrim: {j["strips"].Count()} strips ({raked.Count} raked) from spec/trim_faces.json");
    }

    // A strip along a face: per station interval a prism (front at depth d1, back at d0, sloped top and bottom, ends); a riser's two
    // bottoms at one s make the step. One mesh per strip, no collider (the grey-box carries collision).
    static void StripMesh(GameObject parent, JToken s, Material m)
    {
        string ax = (string)s["axis"]; float c = (float)s["c"], n = (float)s["n"], d0 = (float)s["d"][0], d1 = (float)s["d"][1];
        Vector3 P(float a, float y, float off) { float w = c + n * off; return ax == "x" ? new Vector3(a, y, w) : new Vector3(w, y, a); }
        Vector3 along = ax == "x" ? Vector3.right : Vector3.forward, normal = (ax == "x" ? Vector3.forward : Vector3.right) * n;
        var v = new List<Vector3>(); var t = new List<int>();
        void Quad(Vector3 a, Vector3 b, Vector3 q, Vector3 d, Vector3 outward)
        {
            int i = v.Count; v.Add(a); v.Add(b); v.Add(q); v.Add(d);
            bool flip = Vector3.Dot(Vector3.Cross(b - a, q - a), outward) < 0f;   // Unity: Cross(b-a, c-a) is the front face's normal
            t.AddRange(flip ? new[] { i, i + 2, i + 1, i, i + 3, i + 2 } : new[] { i, i + 1, i + 2, i, i + 2, i + 3 });
        }
        var st = s["st"].Select(p => (a: (float)p[0], b: (float)p[1], tp: (float)p[2])).ToList();
        for (int k = 0; k + 1 < st.Count; k++)
        {
            var A = st[k]; var Bq = st[k + 1];
            if (Bq.a - A.a < 1e-5f) continue;
            Quad(P(A.a, A.b, d1), P(Bq.a, Bq.b, d1), P(Bq.a, Bq.tp, d1), P(A.a, A.tp, d1), normal);     // front
            Quad(P(A.a, A.b, d0), P(Bq.a, Bq.b, d0), P(Bq.a, Bq.tp, d0), P(A.a, A.tp, d0), -normal);    // back (on the wall)
            Quad(P(A.a, A.tp, d0), P(Bq.a, Bq.tp, d0), P(Bq.a, Bq.tp, d1), P(A.a, A.tp, d1), Vector3.up);
            Quad(P(A.a, A.b, d0), P(Bq.a, Bq.b, d0), P(Bq.a, Bq.b, d1), P(A.a, A.b, d1), Vector3.down);
            Quad(P(A.a, A.b, d0), P(A.a, A.tp, d0), P(A.a, A.tp, d1), P(A.a, A.b, d1), -along);
            Quad(P(Bq.a, Bq.b, d0), P(Bq.a, Bq.tp, d0), P(Bq.a, Bq.tp, d1), P(Bq.a, Bq.b, d1), along);
        }
        var mesh = new Mesh { name = "Trim_" + (string)s["name"] }; mesh.SetVertices(v); mesh.SetTriangles(t, 0);
        mesh.RecalculateNormals(); mesh.RecalculateBounds();
        var go = new GameObject("Trim"); go.transform.SetParent(parent.transform, false);
        go.AddComponent<MeshFilter>().sharedMesh = mesh; go.AddComponent<MeshRenderer>().sharedMaterial = m; go.isStatic = true;
    }

    // The Trim check on a SAVED scene (no rebuild), e.g. the old path's committed scene:
    //   Unity -batchmode -projectPath <p> -executeMethod SpecGreybox.TrimCheckScene -quit [-scene House_WallGrid] [-views <file>]
    //   -> spec/captures/trim-check-<scene>.txt (and the views, as RenderViews)
    public static void TrimCheckScene()
    {
        var a = System.Environment.GetCommandLineArgs(); int si = System.Array.IndexOf(a, "-scene");
        string scene = si >= 0 ? a[si + 1] : "House_WallGrid";
        EditorSceneManager.OpenScene($"Assets/Scenes/{scene}.unity");
        Dress = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/dressing/foyer.json")));
        var txt = TrimCheck();
        Directory.CreateDirectory(CaptureDir); File.WriteAllText(Path.Combine(CaptureDir, $"trim-check-{scene}.txt"), txt); Debug.Log(txt);
        if (System.Array.IndexOf(a, "-views") >= 0) RenderViews();
    }
}
