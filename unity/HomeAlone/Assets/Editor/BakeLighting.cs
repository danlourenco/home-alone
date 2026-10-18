using System.Collections;
using System.Collections.Generic;
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
//   Unity -projectPath ... -executeMethod BakeLighting.Bake       (no -batchmode, no -quit: it exits when done)
// Windowed, because HDRP renders the static lighting sky only in a render loop: a batch bake (or one run straight from
// -executeMethod) has no sky in it (Oct 16: the day bake came out identical with the sky on or off). Each scenario renders a camera
// SkyFrames times after its sky is set.
public static class BakeLighting
{
    const string ScenePath = "Assets/Scenes/House_WallGrid.unity";

    const int SkyFrames = 30;

    // Each scenario renders a camera SkyFrames times so HDRP renders its sky, then bakes. Refuses batch mode (no render
    // loop, so no sky: the day bake came out identical with the sky on or off, Oct 16). Launched by -executeMethod it exits when done.
    [MenuItem("HomeAlone/Bake Lighting")]
    public static void Bake()
    {
        if (Application.isBatchMode) throw new System.InvalidOperationException("BakeLighting needs a render loop for the sky: run without -batchmode");
        bool exit = System.Environment.GetCommandLineArgs().Contains("-executeMethod");
        var e = Steps();
        void Tick()
        {
            UnityEditorInternal.InternalEditorUtility.RepaintAllViews(); SceneView.RepaintAll();
            EditorApplication.QueuePlayerLoopUpdate();   // a background editor otherwise idles and the frames never come
            if (e.MoveNext()) return;
            EditorApplication.update -= Tick;
            if (exit) EditorApplication.Exit(failed ? 1 : 0);
        }
        EditorApplication.update += Tick;
    }

    static bool failed;

    // Invariant (Oct 17): every light authored Baked must come out of the bake recorded as baked in the SAVED scene. The scene keeps one
    // lighting data asset, written by the LAST bake: with Night baked last (day layer off) the 52 FilmFill lights were recorded as not baked
    // and Unity drew them in real time with soft shadows (72 M tris/frame in the foyer by day, the day-only flicker squares, and the day
    // lit twice: baked into the probes AND real time). Returns the failure lines; logs "Baked lights: N of M baked" and every light that
    // renders in real time in the scene's saved (day) state.
    public static List<string> CheckBakedLights()
    {
        var all = Object.FindObjectsByType<Light>(FindObjectsInactive.Include, FindObjectsSortMode.None);
        var baked = all.Where(l => l.lightmapBakeType == LightmapBakeType.Baked).ToList();
        var bad = baked.Where(l => !l.bakingOutput.isBaked).Select(l => "  not baked: " + l.name).ToList();
        Debug.Log($"Baked lights: {baked.Count - bad.Count} of {baked.Count} baked");
        var rt = all.Where(l => l.enabled && l.gameObject.activeInHierarchy && !(l.bakingOutput.isBaked && l.bakingOutput.lightmapBakeType == LightmapBakeType.Baked)).Select(l => l.name).ToList();
        Debug.Log($"Realtime lights in the saved state: {rt.Count} ({string.Join(", ", rt.Take(20))})");
        // Invariant (Oct 17, Buzz trial 2): no probe inside a room is invalidated. A room probe that is invalid can leave a probe cell with no
        // valid probe at all, and APV then samples the raw (outdoor) values: the overhang strip's bright/dark bands (above)
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        var hs = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.json"))));
        var rooms = SpecGreybox.EnvelopeRooms(geo, hs["attic_stair"]["boxes"], (float)geo["ground"]["floor_y"]);
        foreach (var v in Object.FindObjectsByType<ProbeAdjustmentVolume>(FindObjectsSortMode.None).Where(v => v.mode == ProbeAdjustmentVolume.Mode.InvalidateProbes))
        {
            var bb = new Bounds(v.transform.position, v.size); bb.Expand(-0.10f);   // 5 cm in from every face: the boundary is not "inside"
            bool In(Vector3 q) => rooms.Any(r => q.y > r.y0 && q.y < r.y1 && SpecGreybox.Inside(r.pts, new Vector2(q.x, q.z)));
            for (int i = 0; i < 27; i++)
            {
                var q = new Vector3(Mathf.Lerp(bb.min.x, bb.max.x, (i % 3) / 2f), Mathf.Lerp(bb.min.y, bb.max.y, (i / 3 % 3) / 2f), Mathf.Lerp(bb.min.z, bb.max.z, (i / 9) / 2f));
                if (bb.size.x > 0 && bb.size.y > 0 && bb.size.z > 0 && In(q)) { bad.Add($"  probes invalidated inside a room: {v.name} at {q}"); break; }
            }
        }
        foreach (var b in bad) Debug.LogError("BakeLighting FAIL:" + b);
        return bad;
    }

    // Unity -batchmode -projectPath <p> -executeMethod BakeLighting.VerifyBakedLights -quit -logFile -   (the saved scene, no Play)
    public static void VerifyBakedLights()
    {
        EditorSceneManager.OpenScene(ScenePath);
        if (CheckBakedLights().Count > 0 && Application.isBatchMode) EditorApplication.Exit(1);
    }

    static IEnumerator Steps()
    {
        var scene = EditorSceneManager.OpenScene(ScenePath);
        var outdoors = GameObject.Find("Exterior");
        var house = new Bounds();
        bool first = true;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
        {
            bool isOut = outdoors != null && r.transform.IsChildOf(outdoors.transform);
            if (r.GetComponentInParent<SwingDoor>() != null) continue;   // moving parts are not static scenery
            // the window backdrop dome and card (SpecGreybox.Backdrop.cs) are pictures, not scenery: as GI contributors the 9000-nit dome would
            // enclose the house, replace the sky in the bake and stretch the probe volume to 150 m
            if (r.name.StartsWith("WinterBackdrop")) { GameObjectUtility.SetStaticEditorFlags(r.gameObject, 0); continue; }
            // glass passes light: as a GI contributor the lightmapper treats it as opaque and no sky or sun entered the house in the bake
            bool clear = r.sharedMaterials.Any(m => m != null && m.HasProperty("_SurfaceType") && m.GetFloat("_SurfaceType") > 0.5f);
            // the film's flush front (SpecGreybox.FilmFront, shadows only) stands in for the upper storey's walls in the SUN's shadows while the
            // player is downstairs (StoreyShadows); it stays out of the bake. The upstairs overhang strip bakes with its own walls: until
            // Oct 17 it was the other way round, the strip baked open to the sky and its probes were invalidated, and every surface whose
            // probe cell had no valid probe left (the strip's last column beside the outside air) showed the raw outdoor light: bright
            // dithered bands by day and dark ones by night along the front rooms' walls and ceilings (walk note 18:10, Buzz; Kevin's room).
            // Checked: the ground floor's front rooms read the same (spec/captures/buzz2/lighting/)
            bool overhang = (r.renderingLayerMask & ~SpecGreybox.LayerOutside) == SpecGreybox.LayerFilmFront;   // the exterior skin's upper storey too (SpecGreybox.Shell; the backdrop adds LayerOutside)
            var flags = GameObjectUtility.GetStaticEditorFlags(r.gameObject);
            GameObjectUtility.SetStaticEditorFlags(r.gameObject, clear || overhang ? flags & ~StaticEditorFlags.ContributeGI : flags | StaticEditorFlags.ContributeGI);
            r.receiveGI = ReceiveGI.LightProbes;
            if (isOut || !r.enabled) continue;
            if (first) { house = r.bounds; first = false; } else house.Encapsulate(r.bounds);
        }
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            if (!l.name.StartsWith("FilmFill") && l.name != "Moonlight") l.lightmapBakeType = LightmapBakeType.Mixed;   // the film's fill is baked only; the backdrop's moon lights the yard only (real time)

        // probes cover the house only (a global volume would stretch over the 200 m snow plane)
        var old = GameObject.Find("HouseProbeVolume"); if (old) Object.DestroyImmediate(old);
        var pv = new GameObject("HouseProbeVolume").AddComponent<ProbeVolume>();
        pv.mode = ProbeVolume.Mode.Local; pv.transform.position = house.center; pv.size = house.size + Vector3.one;

        // a baked reflection probe in every room, sized to it (spec/geometry.json): with none, glossy surfaces reflect the default sky
        // (a swing door in the dining room read as sky, Oct 16; blue floors before).
        foreach (var o in Object.FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None)) if (o.name.StartsWith("Probe_")) Object.DestroyImmediate(o.gameObject);
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        // every room as a volume (SpecGreybox.EnvelopeRooms): the stair well runs down to the ground floor and the attic stair up its shaft.
        // The well was skipped as an "opening", and above the foyer's 2.82 m ceiling the two-storey hall reflected the blue sky (Oct 16:
        // measured live, sky reflection off -> the landing's paper came back)
        var hs = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.json"))));
        var rooms = SpecGreybox.EnvelopeRooms(geo, hs["attic_stair"]["boxes"], (float)geo["ground"]["floor_y"]);
        int probes = 0;
        foreach (var r in rooms)
        {
            float x0 = r.pts.Min(v => v.x), x1 = r.pts.Max(v => v.x), z0 = r.pts.Min(v => v.y), z1 = r.pts.Max(v => v.y);
            // to the middle of its walls (a door leaf there is inside) and 7 cm past its floor and ceiling, fading over 5 cm: every room
            // surface at full weight. With a 15 cm fade inside a 7 cm margin the walls had half weight and the floor none, and HDRP filled
            // the rest from the sky: grey-blue rooms by day (user note 11:43; measured live: sky reflection off -> red walls, wood floor)
            var size = new Vector3(x1 - x0 + 0.14f, r.y1 - r.y0 + 0.14f, z1 - z0 + 0.14f);
            var rp = new GameObject("Probe_" + r.name).AddComponent<ReflectionProbe>();
            rp.transform.position = new Vector3((x0 + x1) / 2, (r.y0 + r.y1) / 2, (z0 + z1) / 2);
            var hd = rp.gameObject.AddComponent<HDAdditionalReflectionData>();
            rp.mode = UnityEngine.Rendering.ReflectionProbeMode.Baked; hd.mode = ProbeSettings.Mode.Baked;
            // every rendering layer: the upstairs pieces past the film's front are on LayerOverhang (SpecGreybox.FilmFront) and a probe
            // lights only layer 1 by default, so Buzz's floor, chest and nightstand reflected the blue sky (navy wood by day; overnight3b)
            hd.lightLayers = UnityEngine.Rendering.HighDefinition.RenderingLayerMask.Everything;
            hd.influenceVolume.shape = InfluenceShape.Box; hd.influenceVolume.boxSize = size;
            hd.influenceVolume.boxBlendDistancePositive = Vector3.one * 0.05f; hd.influenceVolume.boxBlendDistanceNegative = Vector3.one * 0.05f;
            probes++;
        }
        Debug.Log($"BakeLighting: {probes} room reflection probes");

        // the sky is baked (each scenario its own: the day's physical sky, the night's dark gradient). Without it the day's fill came
        // from sun light leaking through the thin shell; once the envelope sealed the house (Oct 16) the rooms by day had no fill at
        // all and read grey-blue (user note 11:43). A house by day is lit by the sky and the snow through its windows.
        foreach (var sky in Object.FindObjectsByType<StaticLightingSky>(FindObjectsSortMode.None)) Object.DestroyImmediate(sky);
        var staticSky = new GameObject("StaticLightingSky").AddComponent<StaticLightingSky>();
        var daySky = AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Settings/GreyboxVolume.asset");
        var nightSky = AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Settings/NightSky.asset");

        // probes only inside the rooms: every probe outside a room's volume (above the ceilings, in the walls and floors, outdoors) is
        // invalidated. At 1 m spacing a layer of probes sat above every 2.4 m ceiling in sunlit air and the top of each room blended
        // toward it (user note 11:16: a bright band along the ceilings). The invalid region is the probe volume less the rooms
        // (SpecGreybox.EnvelopeRooms), on the grid of the rooms' own corners, merged into boxes.
        foreach (var o in Object.FindObjectsByType<ProbeAdjustmentVolume>(FindObjectsSortMode.None)) Object.DestroyImmediate(o.gameObject);
        var vb = new Bounds(pv.transform.position, pv.size);
        var gx = rooms.SelectMany(r => r.pts.Select(v => v.x)).Append(vb.min.x).Append(vb.max.x).Distinct().OrderBy(v => v).ToList();
        var gz = rooms.SelectMany(r => r.pts.Select(v => v.y)).Append(vb.min.z).Append(vb.max.z).Distinct().OrderBy(v => v).ToList();
        var gyv = rooms.SelectMany(r => new[] { r.y0, r.y1 }).Append(vb.min.y).Append(vb.max.y).Distinct().OrderBy(v => v).ToList();
        var adj = new GameObject("ProbeInvalidation"); int boxes = 0;
        for (int iy = 0; iy + 1 < gyv.Count; iy++)
        {
            float ym = (gyv[iy] + gyv[iy + 1]) / 2;
            var live = rooms.Where(r => r.y0 < ym && r.y1 > ym).ToList();
            var runs = new Dictionary<(int, int), int>();   // (x0 index, x1 index) -> first z index of an open box with that run
            void Emit(int a, int b, int k0, int k1)
            {
                var lo = new Vector3(gx[a], gyv[iy], gz[k0]); var hi = new Vector3(gx[b], gyv[iy + 1], gz[k1]);
                var g = new GameObject("Invalidate"); g.transform.SetParent(adj.transform); g.transform.position = (lo + hi) / 2;
                var v = g.AddComponent<ProbeAdjustmentVolume>(); v.shape = ProbeAdjustmentVolume.Shape.Box; v.mode = ProbeAdjustmentVolume.Mode.InvalidateProbes;
                v.size = Vector3.Max(hi - lo - Vector3.one * 0.04f, Vector3.one * 0.01f);   // 2 cm shy of every face: a probe on a room's boundary stays
                boxes++;
            }
            for (int k = 0; k + 1 <= gz.Count; k++)
            {
                var row = new List<(int, int)>();
                if (k + 1 < gz.Count)
                {
                    float zm = (gz[k] + gz[k + 1]) / 2; int start = -1;
                    for (int i = 0; i + 1 < gx.Count; i++)
                    {
                        bool open = !live.Any(r => SpecGreybox.Inside(r.pts, new Vector2((gx[i] + gx[i + 1]) / 2, zm)));
                        if (open && start < 0) start = i;
                        if (!open && start >= 0) { row.Add((start, i)); start = -1; }
                    }
                    if (start >= 0) row.Add((start, gx.Count - 1));
                }
                foreach (var key in runs.Keys.Where(q => !row.Contains(q)).ToList()) { Emit(key.Item1, key.Item2, runs[key], k); runs.Remove(key); }
                foreach (var q in row) if (!runs.ContainsKey(q)) runs[q] = k;
            }
        }
        Debug.Log($"BakeLighting: {boxes} probe invalidation boxes outside the rooms");

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
        // Night first, Default LAST: the scene's one lighting data asset records the last bake's lights, and the scene opens (and plays) in
        // day, so the day's Baked FilmFill must be the ones recorded as baked (CheckBakedLights). The night lamps are Mixed (Baked Indirect):
        // their direct light and shadows are real time either way and their bounce is in the Night probe scenario, so they need no record.
        foreach (var (scenario, night) in new[] { ("Night", true), ("Default", false) })
        {
            mode.nightLayer.SetActive(night); mode.dayLayer.SetActive(!night);
            staticSky.profile = night ? nightSky : daySky;
            staticSky.staticLightingSkyUniqueID = (int)(night ? SkyType.Gradient : SkyType.PhysicallyBased);
            Use(scenario);
            // let HDRP render the static sky: a camera rendered on the spot (a background editor ticks every few seconds, and waiting on
            // its frames took 13 minutes, Oct 16), then one editor frame
            var skyCam = new GameObject("SkyCam").AddComponent<Camera>(); skyCam.gameObject.AddComponent<HDAdditionalCameraData>();
            skyCam.transform.position = house.center + Vector3.up * 20f;
            for (int f = 0; f < SkyFrames; f++) skyCam.Render();
            Object.DestroyImmediate(skyCam.gameObject);
            yield return null;
            var t = System.Diagnostics.Stopwatch.StartNew();
            bool ok = Lightmapping.Bake();
            Debug.Log($"BakeLighting {scenario}: {(ok ? "done" : "FAILED")} in {t.Elapsed.TotalSeconds:F0} s");
            // the room probes again, now that this scenario's probe volume is baked and loaded: the images Lightmapping.Bake renders
            // see the walls without the baked FilmFill (Buzz's paper R/B 0.88 in its day probe: lit by the sky alone), and every dark
            // glossy surface showed that: Buzz's wood floor and mahogany chest read navy by day (overnight3b, Oct 18; live, a probe
            // re-rendered in Play took the floor from R/B 0.65 to 1.44). HDRP's own probe bake needs the scene saved first
            EditorSceneManager.SaveScene(scene);
            for (int f = 0; f < SkyFrames; f++) { SceneView.RepaintAll(); yield return null; }
            bool rp = UnityEditor.Experimental.Rendering.ScriptableBakedReflectionSystemSettings.system.BakeAllReflectionProbes();
            Debug.Log($"BakeLighting {scenario}: reflection probes re-rendered after the bake: {rp}");
            if (!rp) { Debug.LogError("BakeLighting FAIL: reflection probes not re-rendered"); }
            // each scenario keeps its own reflections: the probes' images are copied per scenario and HouseNightMode swaps them (one set,
            // baked in the night pass, put the lamp-lit night room into the day's reflections)
            var rps = Object.FindObjectsByType<HDAdditionalReflectionData>(FindObjectsSortMode.None).Where(q => q.name.StartsWith("Probe_")).OrderBy(q => q.name).ToArray();
            var texs = new Texture[rps.Length];
            for (int i = 0; i < rps.Length; i++)
            {
                var src = AssetDatabase.GetAssetPath(rps[i].bakedTexture);
                var dst = $"Assets/Scenes/House_WallGrid/{rps[i].name}-{scenario}.exr";
                AssetDatabase.DeleteAsset(dst); AssetDatabase.CopyAsset(src, dst); texs[i] = AssetDatabase.LoadAssetAtPath<Texture>(dst);
            }
            mode.reflectionProbes = rps; if (night) mode.nightReflections = texs; else mode.dayReflections = texs;
        }
        Use("Default"); mode.nightLayer.SetActive(false); mode.dayLayer.SetActive(true);   // the scene opens in day
        mode.ApplyReflections(false); EditorUtility.SetDirty(mode);
        AssetDatabase.SaveAssets();
        EditorSceneManager.SaveScene(scene);
        EditorSceneManager.OpenScene(ScenePath);   // check what was saved, not what is in memory
        failed = CheckBakedLights().Count > 0;
    }
}
