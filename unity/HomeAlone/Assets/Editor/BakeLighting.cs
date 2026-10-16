using System.Linq;
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

        // baked reflection probes over the foyer and vestibule (brass, gloss and glass read black with nothing to reflect)
        foreach (var o in Object.FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None)) if (o.name.StartsWith("Probe_")) Object.DestroyImmediate(o.gameObject);
        foreach (var (name, c, size) in new[] { ("Probe_Foyer", new Vector3(6.0f, -1.6f, -9.6f), new Vector3(6.2f, 2.9f, 3.8f)),
                                                ("Probe_Vestibule", new Vector3(9.6f, -1.8f, -9.6f), new Vector3(1.1f, 2.5f, 3.7f)) })
        {
            var rp = new GameObject(name).AddComponent<ReflectionProbe>(); rp.transform.position = c;
            var hd = rp.gameObject.AddComponent<HDAdditionalReflectionData>();
            rp.mode = UnityEngine.Rendering.ReflectionProbeMode.Baked; hd.mode = ProbeSettings.Mode.Baked;
            hd.influenceVolume.shape = InfluenceShape.Box; hd.influenceVolume.boxSize = size; hd.influenceVolume.boxBlendDistancePositive = Vector3.one * 0.3f; hd.influenceVolume.boxBlendDistanceNegative = Vector3.one * 0.3f;
        }

        // the sky lights the bake through the windows
        var vol = Object.FindObjectsByType<Volume>(FindObjectsSortMode.None).First(v => v.isGlobal);
        var sls = vol.GetComponent<StaticLightingSky>(); if (sls == null) sls = vol.gameObject.AddComponent<StaticLightingSky>();
        sls.profile = vol.sharedProfile; sls.staticLightingSkyUniqueID = (int)SkyType.PhysicallyBased;

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
