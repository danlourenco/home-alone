using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// The props tool's editor half (tools/house/props.py; change-gate skill "Props in 5 minutes"): store props placed in the OPEN scene
// without a house build, and the model-size index props.py searches. Oct 18: a prop job averaged 37 min, mostly agent steps and builds.
//   Home Alone > Refresh Props   re-places every store_props.json piece that is new, changed since it was placed, or gone (seconds)
//   SpecGreybox.RefreshProps("a,b")   the same for named pieces (props.py add/pin/refresh call it through `unity command eval`)
//   SpecGreybox.IndexModels(path)     every prefab/model's drawn size at yaw 0 (x, z, y metres) -> JSON (props.py index)
//   SpecGreybox.PropBounds(name)      a placed piece's drawn bounds, "cx cy cz sx sy sz" (props.py front)
// Works in Play too (a preview: Stop throws it away; Refresh again after Stop to place it for Save Prop Placement).
public static partial class SpecGreybox
{
    static string StorePropsPath => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/store_props.json"));

    [MenuItem("Home Alone/Refresh Props")]
    static void RefreshPropsMenu() { var r = RefreshProps(); Debug.Log(r); EditorUtility.DisplayDialog("Refresh Props", r, "OK"); }

    public static string RefreshProps(string names = null)
    {
        var pieces = JObject.Parse(File.ReadAllText(StorePropsPath))["pieces"].ToDictionary(p => (string)p["name"]);
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var up = scene.GetRootGameObjects().FirstOrDefault(g => g.name == "Upstairs");
        var ground = scene.GetRootGameObjects().FirstOrDefault(g => g.name == "Ground");
        if (up == null || ground == null) return "Refresh Props: no Upstairs/Ground roots: open House_WallGrid first";
        GameObject Holder(GameObject r) => r.transform.Find("StoreProps")?.gameObject ?? Child(r, "StoreProps");
        GameObject gUp = Holder(up), gGround = Holder(ground);
        float gy = (float)JObject.Parse(File.ReadAllText(GroundPath))["floor_y_m"];
        var placed = Object.FindObjectsByType<PlacedProp>(FindObjectsInactive.Include, FindObjectsSortMode.None).Where(pp => pp.spec == "store_props").ToList();
        var want = !string.IsNullOrEmpty(names) ? names.Split(',').Select(n => n.Trim()).ToList()
            : pieces.Where(kv => placed.All(pp => pp.name != kv.Key)                                                           // new
                || placed.Any(pp => pp.name == kv.Key && !string.IsNullOrEmpty(pp.src) && pp.src != kv.Value.ToString(Newtonsoft.Json.Formatting.None)))   // changed
                .Select(kv => kv.Key).ToList();
        var log = new System.Text.StringBuilder();
        void Remove(string n)
        {
            foreach (var pp in placed.Where(pp => pp != null && pp.name == n)) Object.DestroyImmediate(pp.gameObject);
            foreach (var h in new[] { gUp, gGround }) for (var t = h.transform.Find(n + "_Collider"); t != null; t = h.transform.Find(n + "_Collider")) Object.DestroyImmediate(t.gameObject);
        }
        if (string.IsNullOrEmpty(names))   // a piece renamed or deleted in the spec leaves the scene too
            foreach (var n in placed.Select(pp => pp.name).Distinct().Where(n => !pieces.ContainsKey(n)).ToList()) { Remove(n); log.AppendLine($"{n}: removed (not in the spec)"); }
        LiveRefresh = true;
        try
        {
            foreach (var n in want)
            {
                if (!pieces.TryGetValue(n, out var p)) { log.AppendLine($"{n}: not in store_props.json"); continue; }
                Remove(n);
                var go = PlaceStoreProp(p, gUp, gGround, gy);
                if (go == null) { log.AppendLine($"{n}: not placed ({p["prefab"]} not imported?)"); continue; }
                var b = go.GetComponentsInChildren<Renderer>().Aggregate((Bounds?)null, (a, r) => { if (a == null) return r.bounds; var q = a.Value; q.Encapsulate(r.bounds); return q; }).Value;
                log.AppendLine($"{n}: placed, yaw {go.GetComponent<PlacedProp>().yaw}, drawn {b.min} .. {b.max}");
            }
        }
        finally { LiveRefresh = false; }
        return $"Refresh Props: {want.Count} piece(s){(EditorApplication.isPlaying ? " (Play: a preview, gone on Stop)" : "")}\n{log}";
    }

    public static string PropBounds(string name)
    {
        var pp = Object.FindObjectsByType<PlacedProp>(FindObjectsSortMode.None).FirstOrDefault(q => q.name == name);
        if (pp == null) return "none";
        var rs = pp.GetComponentsInChildren<Renderer>().Where(r => r.enabled).ToArray();
        var b = rs.Aggregate(rs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
        return string.Join(" ", new[] { b.center.x, b.center.y, b.center.z, b.size.x, b.size.y, b.size.z }.Select(v => v.ToString("F3", System.Globalization.CultureInfo.InvariantCulture)));
    }

    // drawn size at yaw 0, unscaled, as StoreProps measures it (all renderers): [x, z, y] = width, depth, height
    public static string IndexModels(string outPath)
    {
        string[] skip = { "/URP/", "/Built-in", "/BuiltIn", "Assets/Scenes/", "Assets/_Recovery/", "Assets/HDRPDefaultResources/", "/Scenes/", "/Demo" };
        var preview = EditorSceneManager.NewPreviewScene(); var arr = new JArray(); int n = 0;
        try
        {
            foreach (var path in AssetDatabase.FindAssets("t:GameObject", new[] { "Assets" }).Select(AssetDatabase.GUIDToAssetPath).Distinct().OrderBy(p => p))
            {
                if (skip.Any(path.Contains)) continue;
                var a = AssetDatabase.LoadAssetAtPath<GameObject>(path); if (a == null) continue;
                var go = (GameObject)PrefabUtility.InstantiatePrefab(a, preview); n++;
                if (go == null) continue;
                go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity); go.transform.localScale = Vector3.one;
                var rs = go.GetComponentsInChildren<Renderer>();
                if (rs.Length > 0)
                {
                    var b = rs.Aggregate(rs[0].bounds, (q, r) => { q.Encapsulate(r.bounds); return q; });
                    arr.Add(new JObject { ["path"] = path, ["name"] = a.name,
                        ["size"] = new JArray(System.Math.Round(b.size.x, 3), System.Math.Round(b.size.z, 3), System.Math.Round(b.size.y, 3)) });
                }
                Object.DestroyImmediate(go);
            }
        }
        finally { EditorSceneManager.ClosePreviewScene(preview); }
        Directory.CreateDirectory(Path.GetDirectoryName(outPath));
        File.WriteAllText(outPath, new JObject { ["models"] = arr }.ToString());
        return $"indexed {arr.Count} of {n}";
    }
}
