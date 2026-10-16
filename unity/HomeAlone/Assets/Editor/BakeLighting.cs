using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// Baked bounce light for House_WallGrid (Oct 16): HDRP ray tracing is DirectX 12 only, so on the Mac the light that bounces off
// floors and walls is traced once here and stored in an Adaptive Probe Volume (no lightmap UVs needed). Direct light and
// shadows stay real time (lights become Mixed, Baked Indirect). Two scenarios: "Default" (day: sun on, room lamps off) and
// "Night" (sun off, room lamps on); HouseNightMode (N) switches between them.
//   Unity -batchmode -projectPath ... -executeMethod BakeLighting.Bake -quit
public static class BakeLighting
{
    const string ScenePath = "Assets/Scenes/House_WallGrid.unity";

    public static void Bake()
    {
        var scene = EditorSceneManager.OpenScene(ScenePath);
        var outdoors = GameObject.Find("Exterior");
        var house = new Bounds();
        bool first = true;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
        {
            bool isOut = outdoors != null && r.transform.IsChildOf(outdoors.transform);
            if (r.GetComponentInParent<SwingDoor>() != null) continue;   // moving parts are not static scenery
            GameObjectUtility.SetStaticEditorFlags(r.gameObject, GameObjectUtility.GetStaticEditorFlags(r.gameObject) | StaticEditorFlags.ContributeGI);
            r.receiveGI = ReceiveGI.LightProbes;
            if (isOut || !r.enabled) continue;
            if (first) { house = r.bounds; first = false; } else house.Encapsulate(r.bounds);
        }
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            l.lightmapBakeType = LightmapBakeType.Mixed;

        // probes cover the house only (a global volume would stretch over the 200 m snow plane)
        var old = GameObject.Find("HouseProbeVolume"); if (old) Object.DestroyImmediate(old);
        var pv = new GameObject("HouseProbeVolume").AddComponent<ProbeVolume>();
        pv.mode = ProbeVolume.Mode.Local; pv.transform.position = house.center; pv.size = house.size + Vector3.one;

        // a baked reflection probe in every room, sized to it (spec/geometry.json): with none, glossy surfaces reflect the default sky
        // (a swing door in the dining room read as sky, Oct 16; blue floors before).
        foreach (var o in Object.FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None)) if (o.name.StartsWith("Probe_")) Object.DestroyImmediate(o.gameObject);
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        int probes = 0;
        foreach (var storey in new[] { "ground", "upstairs" })
        {
            float fy = (float)geo[storey]["floor_y"];
            foreach (var r in geo[storey]["rooms"].Where(r => (string)r["kind"] != "opening"))
            {
                var xs = r["poly"].Select(q => (float)q[0]).ToList(); var zs = r["poly"].Select(q => -(float)q[1]).ToList();
                float ceil = (float)r["ceil"];
                var size = new Vector3(xs.Max() - xs.Min() + 0.14f, ceil, zs.Max() - zs.Min() + 0.14f);   // to the middle of its walls: a door leaf there is inside
                var centre = new Vector3((xs.Min() + xs.Max()) / 2, fy + ceil / 2, (zs.Min() + zs.Max()) / 2);
                var rp = new GameObject("Probe_" + (string)r["name"]).AddComponent<ReflectionProbe>();
                rp.transform.position = centre;
                var hd = rp.gameObject.AddComponent<HDAdditionalReflectionData>();
                rp.mode = UnityEngine.Rendering.ReflectionProbeMode.Baked; hd.mode = ProbeSettings.Mode.Baked;
                hd.influenceVolume.shape = InfluenceShape.Box; hd.influenceVolume.boxSize = size;
                hd.influenceVolume.boxBlendDistancePositive = Vector3.one * 0.15f; hd.influenceVolume.boxBlendDistanceNegative = Vector3.one * 0.15f;
                probes++;
            }
        }
        Debug.Log($"BakeLighting: {probes} room reflection probes");

        // no sky in the bake, by design: the bounce light is the sun's and the lamps' only. With the blue sky baked in, rooms lit through
        // windows turned blue (Oct 16); the sun-only bounce is the look the user rated right. (HDRP left the sky out by accident before,
        // "Static Lighting Sky is not ready"; now it is explicit)
        foreach (var sky in Object.FindObjectsByType<StaticLightingSky>(FindObjectsSortMode.None)) Object.DestroyImmediate(sky);

        var ls = new LightingSettings { bakedGI = true, realtimeGI = false, lightmapper = LightingSettings.Lightmapper.ProgressiveGPU,
            mixedBakeMode = MixedLightingMode.IndirectOnly, maxBounces = 4, directSampleCount = 32, indirectSampleCount = 256 };
        AssetDatabase.DeleteAsset("Assets/Settings/HouseLighting.lighting");
        AssetDatabase.CreateAsset(ls, "Assets/Settings/HouseLighting.lighting");
        Lightmapping.lightingSettings = ls;

        Debug.Log($"BakeLighting: probe volume {house.center} size {pv.size}");
        var mode = Object.FindFirstObjectByType<HouseNightMode>();
        void Use(string scenario)   // the first bake creates the set; the active scenario field is internal
        {
            var set = AssetDatabase.FindAssets("t:ProbeVolumeBakingSet", new[] { "Assets/Scenes/House_WallGrid" })
                .Select(g => AssetDatabase.LoadAssetAtPath<ProbeVolumeBakingSet>(AssetDatabase.GUIDToAssetPath(g))).FirstOrDefault();
            if (set == null) return;
            set.TryAddScenario(scenario);
            typeof(ProbeVolumeBakingSet).GetField("lightingScenario", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).SetValue(set, scenario);
            EditorUtility.SetDirty(set);
        }
        void Run(string scenario, bool night)
        {
            mode.nightLayer.SetActive(night); mode.dayLayer.SetActive(!night);
            Use(scenario);
            var t = System.Diagnostics.Stopwatch.StartNew();
            bool ok = Lightmapping.Bake();
            Debug.Log($"BakeLighting {scenario}: {(ok ? "done" : "FAILED")} in {t.Elapsed.TotalSeconds:F0} s");
        }
        Run("Default", false);
        Run("Night", true);
        Use("Default"); mode.nightLayer.SetActive(false); mode.dayLayer.SetActive(true);   // the scene opens in day
        AssetDatabase.SaveAssets();
        EditorSceneManager.SaveScene(scene);
    }
}
