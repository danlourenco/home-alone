using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Unity.Profiling;
using Unity.Profiling.LowLevel.Unsafe;   // ProfilerRecorderHandle: markers by name
using UnityEngine;

// Perf probe: frame time and render counters at the player's current view, over N frames, camera untouched.
//   PerfProbe.Run("name", 300)  -> spec/captures/perf/name.json
// Reports median / p95 / p99 frame time (CPU wall), GPU frame time when the platform reports it, and the median of the render
// counters (batches, set-pass calls, triangles, shadow casters). Started from the unity CLI (eval) during Play. In the editor the
// numbers include editor overhead and depend on the Game view size; compare runs with each other, not with a shipped build.
//
// Standalone tour (tools/house/perf_probe.sh): a player started with  -perfprobe <outdir>  disables the walk controller, visits the
// fixed POSES below, day and night, and per pose writes <outdir>/<pose>-<day|night>.json + .png, then quits. Same poses every run,
// so before/after tables compare like with like. Poses are camera position + yaw/pitch (pitch + = down), world metres.
public class PerfProbe : MonoBehaviour
{
    public static string Last = "";
    static readonly HashSet<string> MARKERS = new HashSet<string> { "RenderShadowMaps", "BlitPunctualMixedCachedShadowMaps", "BlitDirectionalMixedCachedShadowMaps",
        "UpdateReflectionProbeAtlas", "ConvolveReflectionProbe", "ConvolvePlanarReflectionProbe", "ConvertReflectionProbe", "APVCellStreamingUpdate",
        "APVDiskStreamingUpdate", "APVScenarioBlendingUpdate", "APVIndexDefragUpdate", "GC.Collect", "Gfx.WaitForPresentOnGfxThread", "Shader.CreateGPUProgram" };
    static readonly (string name, Vector3 pos, float yaw, float pitch)[] POSES =
    {
        ("street", new Vector3(34f, -2.7f, -9.7f), 270f, -7f),        // looking at the front (8, 0.5, -9.7)
        ("foyer", new Vector3(8.4f, -1.716f, -9.4f), 268f, 0f),        // flicker-test pose (feet -2.996, eye +1.28)
        ("living", new Vector3(6.5f, -1.72f, -13.8f), 180f, 0f),       // nightcheck pose, the tree in view
        ("hall", new Vector3(6.893f, 1.31f, -9.487f), 188f, 0f),       // upstairs hall arch (walk note pose)
        ("attic", new Vector3(6.556f, 3.93f, -16.95f), 351f, 0f),      // stair head facing the bed
        ("yard", new Vector3(-4f, -2.1f, -12f), 288f, -10f),           // rear yard looking at the treehouse (-12.1, -9.3)
        ("parents", new Vector3(6.745f, 1.16f, -2.895f), 276f, -14.6f), // parents' room, the bedside lamps (walk note 21:16 pose; PCSS check)
    };

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void AutoTour()
    {
        var a = System.Environment.GetCommandLineArgs(); int i = System.Array.IndexOf(a, "-perfprobe");
        if (i < 0 || i + 1 >= a.Length || Application.isEditor) return;
        var g = new GameObject("PerfProbeTour"); DontDestroyOnLoad(g); var p = g.AddComponent<PerfProbe>(); p.StartCoroutine(p.Tour(a[i + 1]));
    }

    IEnumerator Tour(string dir)
    {
        Directory.CreateDirectory(dir);
        QualitySettings.vSyncCount = 0; Application.targetFrameRate = -1;
        yield return new WaitForSeconds(3f);   // let the scene settle (APV streaming, shaders)
        var fps = FindFirstObjectByType<FpsController>(); var night = FindFirstObjectByType<HouseNightMode>();
        if (fps) { fps.enabled = false; var cc = fps.GetComponent<CharacterController>(); if (cc) cc.enabled = false; }
        var cam = Camera.main.transform;
        // The VARIANT (what the run tests), from the command line:
        //   -perfoff A,B,...  HDRP frame settings off on the camera (FrameSettingsField names: ShadowMaps, ContactShadows, SSAO, Volumetrics...)
        // (Pipeline-asset settings such as the GPU Resident Drawer cannot be switched in a running player: the setter re-creates HDRP,
        // which fails. Compare those with two builds run alternately: tools/house/perf_probe.sh ab.)
        // -perfab: every pose is sampled base, variant, base, variant (tags -A1 -B1 -A2 -B2) in the same session, so another GPU client
        // (the editor in Play) loads both sides alike; without it the whole run is the variant.
        var args = System.Environment.GetCommandLineArgs();
        string Arg(string k) { int i = System.Array.IndexOf(args, k); return i >= 0 && i + 1 < args.Length ? args[i + 1] : null; }
        var hd = Camera.main.GetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData>();
        var off = (Arg("-perfoff") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries)
            .Select(f => (UnityEngine.Rendering.HighDefinition.FrameSettingsField)System.Enum.Parse(typeof(UnityEngine.Rendering.HighDefinition.FrameSettingsField), f)).ToList();
        //   -perflightsoff P1,P2  real-time lights whose name starts with a prefix switched off ("what do these lamps cost")
        //   -perfrange F          every real-time punctual light's range times F ("what would tighter ranges save")
        bool ab = System.Array.IndexOf(args, "-perfab") >= 0;
        var prefixes = (Arg("-perflightsoff") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);
        float rangeK = float.Parse(Arg("-perfrange") ?? "1", System.Globalization.CultureInfo.InvariantCulture);
        var lamps = FindObjectsByType<Light>(FindObjectsInactive.Include).Where(l => l.type != LightType.Directional && !(l.bakingOutput.isBaked && l.bakingOutput.lightmapBakeType == LightmapBakeType.Baked))   // lightmapBakeType is editor-only
            .Select(l => (l, l.range)).ToList();
        //   -perfpcss B,F         every lamp's PCSS blocker/filter sample counts in the variant (HDRP default 24,16; punctual filtering High)
        //   -perfnoshadow P1,P2   real-time lights whose name starts with a prefix lose their shadows in the variant
        var pcss = (Arg("-perfpcss") ?? "").Split(',').Where(v => v.Length > 0).Select(int.Parse).ToArray();
        var noShadow = (Arg("-perfnoshadow") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);
        var lampHd = lamps.Select(x => (x.l, hd: x.l.GetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalLightData>(), x.l.shadows)).Where(x => x.hd != null)
            .Select(x => (x.l, x.hd, x.shadows, b: x.hd.blockerSampleCount, f: x.hd.filterSampleCount)).ToList();
        //   -perfmirror B[,V]     the foyer mirror's planar resolution: B in the base, V in the variant (e.g. 512,1024 with -perfab)
        var mirrorRes = (Arg("-perfmirror") ?? "").Split(',').Where(v => v.Length > 0).Select(int.Parse).ToArray();
        var mirror = FindObjectsByType<UnityEngine.Rendering.HighDefinition.PlanarReflectionProbe>().FirstOrDefault(m => m.name == "FoyerMirrorProbe");
        var only = (Arg("-perfposes") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);   // -perfposes foyer,hall: just those
        var switchedOff = new Dictionary<Light, bool>();   // lamp -> its state before the variant (night mode switches lamps too)
        void Apply(bool variant)
        {
            foreach (var (l, range) in lamps) l.range = variant ? range * rangeK : range;
            foreach (var (l, lhd, sh, b, f) in lampHd)
            {
                if (pcss.Length == 2) { lhd.blockerSampleCount = variant ? pcss[0] : b; lhd.filterSampleCount = variant ? pcss[1] : f; }
                if (noShadow.Any(p => l.name.StartsWith(p))) l.shadows = variant ? LightShadows.None : sh;
            }
            if (mirror && mirrorRes.Length > 0)
                mirror.settingsRaw.resolutionScalable.@override = (UnityEngine.Rendering.HighDefinition.PlanarReflectionAtlasResolution)(variant && mirrorRes.Length > 1 ? mirrorRes[1] : mirrorRes[0]);
            if (variant) { foreach (var (l, _) in lamps) if (prefixes.Any(p => l.name.StartsWith(p))) { switchedOff[l] = l.enabled; l.enabled = false; } }
            else { foreach (var kv in switchedOff) kv.Key.enabled = kv.Value; switchedOff.Clear(); }
            if (hd != null && off.Count > 0)
            {
                hd.customRenderingSettings = variant;
                foreach (var f in off) { hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)f] = true; hd.renderingPathCustomFrameSettings.SetEnabled(f, false); }
            }
        }
        foreach (var dn in new[] { false, true })
        {
            Apply(false);   // night mode switches lamps: let it see the base state, then apply the variant to what it left
            if (night) night.SetNight(dn);
            if (!ab) Apply(true);
            foreach (var (name, pos, yaw, pitch) in POSES)
            {
                if (only.Length > 0 && !only.Contains(name)) continue;
                if (fps) fps.transform.position += pos - cam.position;   // move the body so the eye lands on the pose (HouseSplit, audio follow)
                cam.SetPositionAndRotation(pos, Quaternion.Euler(pitch, yaw, 0));
                string tag = name + "-" + (dn ? "night" : "day");
                foreach (var step in ab ? new[] { "A1", "B1", "A2", "B2" } : new[] { "" })
                {
                    if (ab) Apply(step[0] == 'B');
                    for (int w = 0; w < 120; w++) yield return null;   // warm-up: streaming, cached shadows, exposure
                    string t = ab ? tag + "-" + step : tag;
                    yield return Sample(t, ab ? 150 : 300, dir);
                    if (step == "" || step == "B2" || step == "A2") { ScreenCapture.CaptureScreenshot(Path.Combine(dir, t + ".png")); yield return null; yield return null; }
                }
            }
        }
        File.WriteAllText(Path.Combine(dir, "done.txt"), "ok\n");
        Application.Quit();
    }

    public static void Run(string name, int frames)
    {
        var g = new GameObject("PerfProbe"); var p = g.AddComponent<PerfProbe>(); p.StartCoroutine(p.Sample(name, frames));
    }

    IEnumerator Sample(string name, int frames, string outDir = null)
    {
        Last = "running";
        var counters = new Dictionary<string, ProfilerRecorder>
        {
            ["batches"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count"),
            ["setpass"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "SetPass Calls Count"),
            ["triangles"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count"),
            ["shadow_casters"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Shadow Casters Count"),
            ["draw_calls"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count"),
            ["sys_mem_mb"] = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "System Used Memory"),
            ["gfx_mem_mb"] = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "Gfx Used Memory"),
            ["gpu_frame_ns"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "GPU Frame Time"),   // the profiler's GPU time (FrameTiming's is sparse on Metal)
        };
        var vals = counters.Keys.ToDictionary(k => k, k => new List<long>());
        // per-frame tags (tools/house/perf_attrib.py names each heavy frame's cause): profiler markers by name (CPU ns; HDRP's
        // ProfilingSamplers exist in development players), GC runs, ShadowRefresh map requests, reflection-camera renders (realtime
        // planar mirrors / probes), lights switched on
        var handles = new List<ProfilerRecorderHandle>(); ProfilerRecorderHandle.GetAvailable(handles);
        var markers = new Dictionary<string, ProfilerRecorder>();
        foreach (var h in handles)
        {
            var d = ProfilerRecorderHandle.GetDescription(h);
            if (MARKERS.Contains(d.Name) && !markers.ContainsKey(d.Name)) markers[d.Name] = ProfilerRecorder.StartNew(d.Category, d.Name);
        }
        var mlog = markers.Keys.ToDictionary(k => k, k => new List<long>());
        var gcLog = new List<int>(); var shLog = new List<int>(); var reflLog = new List<int>(); var lightLog = new List<int>();
        var allLights = FindObjectsByType<Light>(FindObjectsInactive.Include);
        int refl = 0; System.Action<UnityEngine.Rendering.ScriptableRenderContext, Camera> onCam = (_, c) => { if (c.cameraType == CameraType.Reflection) refl++; };
        UnityEngine.Rendering.RenderPipelineManager.beginCameraRendering += onCam;
        int gc0 = System.GC.CollectionCount(0), sh0 = ShadowRefresh.Requests;
        var cpu = new List<float>(); var gpu = new List<double>(); var main = new List<double>(); var rend = new List<double>(); var ft = new FrameTiming[1];
        for (int i = 0; i < frames; i++)
        {
            yield return null;
            cpu.Add(Time.unscaledDeltaTime * 1000f);
            int gc = System.GC.CollectionCount(0), sh = ShadowRefresh.Requests;
            gcLog.Add(gc - gc0); shLog.Add(sh - sh0); reflLog.Add(refl); gc0 = gc; sh0 = sh; refl = 0;
            int on = 0; foreach (var l in allLights) if (l && l.isActiveAndEnabled) on++; lightLog.Add(on);
            foreach (var kv in markers) mlog[kv.Key].Add(kv.Value.LastValue);
            foreach (var kv in counters) vals[kv.Key].Add(kv.Value.LastValue);
            FrameTimingManager.CaptureFrameTimings();
            if (FrameTimingManager.GetLatestTimings(1, ft) > 0)
            {
                if (ft[0].gpuFrameTime > 0) gpu.Add(ft[0].gpuFrameTime);
                main.Add(ft[0].cpuMainThreadFrameTime); rend.Add(ft[0].cpuRenderThreadFrameTime);   // busy time per thread: bound = the largest
            }
        }
        foreach (var r in counters.Values) r.Dispose();
        foreach (var r in markers.Values) r.Dispose();
        UnityEngine.Rendering.RenderPipelineManager.beginCameraRendering -= onCam;
        string Arr<T>(IEnumerable<T> l) => "[" + string.Join(",", l.Select(x => System.Convert.ToString(x, System.Globalization.CultureInfo.InvariantCulture))) + "]";
        string flog = "{\"ms\":" + Arr(cpu.Select(x => System.Math.Round(x, 1))) + ",\"gpu_ms\":" + Arr(vals["gpu_frame_ns"].Select(x => System.Math.Round(x / 1e6, 1)))
            + ",\"gc\":" + Arr(gcLog) + ",\"shadow_requests\":" + Arr(shLog) + ",\"reflection_renders\":" + Arr(reflLog) + ",\"lights_on\":" + Arr(lightLog)
            + ",\"markers_us\":{" + string.Join(",", mlog.Select(kv => $"\"{kv.Key}\":" + Arr(kv.Value.Select(v => v / 1000)))) + "}}";
        foreach (var k in new[] { "sys_mem_mb", "gfx_mem_mb" }) vals[k] = vals[k].Select(v => v >> 20).ToList();
        int rt = 0, rtShadow = 0;   // lights drawn in real time (not fully baked), and those casting shadows
        foreach (var l in FindObjectsByType<Light>())
            if (l.enabled && !(l.bakingOutput.isBaked && l.bakingOutput.lightmapBakeType == LightmapBakeType.Baked)) { rt++; if (l.shadows != LightShadows.None) rtShadow++; }
        float Pct(List<float> l, float p) { var s = l.OrderBy(x => x).ToList(); return s[Mathf.Clamp((int)(p * (s.Count - 1)), 0, s.Count - 1)]; }
        long Med(List<long> l) { var s = l.OrderBy(x => x).ToList(); return s[s.Count / 2]; }
        var cam = Camera.main ? Camera.main.transform : transform;
        // p10 beside the median: another GPU client (the editor in Play) inflates some frames; the low percentile is the uncontended cost
        var gs = gpu.OrderBy(x => x).ToList();
        string gpuS = gs.Count > 0 ? gs[gs.Count / 2].ToString("F1") : "null", gpu10 = gs.Count > 0 ? gs[gs.Count / 10].ToString("F1") : "null";
        string Q(List<double> l, float q) { if (l.Count == 0) return "null"; var s = l.OrderBy(x => x).ToList(); return s[Mathf.Clamp((int)(q * (s.Count - 1)), 0, s.Count - 1)].ToString("F1"); }
        Last = "{" + $"\"name\":\"{name}\",\"frames\":{frames},\"cpu_ms_median\":{Pct(cpu, 0.5f):F1},\"cpu_ms_p95\":{Pct(cpu, 0.95f):F1},\"cpu_ms_p99\":{Pct(cpu, 0.99f):F1},"
             + $"\"gpu_ms_median\":{gpuS},\"gpu_ms_p10\":{gpu10},\"gpu_ms_p95\":{Q(gpu, 0.95f)},\"gpu_ms_p99\":{Q(gpu, 0.99f)},\"main_ms_median\":{Q(main, 0.5f)},\"render_ms_median\":{Q(rend, 0.5f)},\"rt_lights\":{rt},\"rt_shadow_lights\":{rtShadow}," + string.Join(",", vals.Select(kv => $"\"{kv.Key}\":{Med(kv.Value)}"))
             + ",\"frame_log\":" + flog
             + $",\"screen\":\"{Screen.width}x{Screen.height}\",\"focused\":{Application.isFocused.ToString().ToLower()},\"cam\":\"{cam.position.x:F2},{cam.position.y:F2},{cam.position.z:F2} yaw {cam.eulerAngles.y:F0}\"" + "}";
        var dir = outDir ?? Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/perf")); Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, name + ".json"), Last + "\n");
        if (outDir == null) Destroy(gameObject);
    }
}
