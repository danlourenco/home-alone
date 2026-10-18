using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Unity.Profiling;
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
    static readonly (string name, Vector3 pos, float yaw, float pitch)[] POSES =
    {
        ("street", new Vector3(34f, -2.7f, -9.7f), 270f, -7f),        // looking at the front (8, 0.5, -9.7)
        ("foyer", new Vector3(8.4f, -1.716f, -9.4f), 268f, 0f),        // flicker-test pose (feet -2.996, eye +1.28)
        ("living", new Vector3(6.5f, -1.72f, -13.8f), 180f, 0f),       // nightcheck pose, the tree in view
        ("hall", new Vector3(6.893f, 1.31f, -9.487f), 188f, 0f),       // upstairs hall arch (walk note pose)
        ("attic", new Vector3(6.556f, 3.93f, -16.95f), 351f, 0f),      // stair head facing the bed
        ("yard", new Vector3(-4f, -2.1f, -12f), 288f, -10f),           // rear yard looking at the treehouse (-12.1, -9.3)
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
        var switchedOff = new Dictionary<Light, bool>();   // lamp -> its state before the variant (night mode switches lamps too)
        void Apply(bool variant)
        {
            foreach (var (l, range) in lamps) l.range = variant ? range * rangeK : range;
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
        };
        var vals = counters.Keys.ToDictionary(k => k, k => new List<long>());
        var cpu = new List<float>(); var gpu = new List<double>(); var ft = new FrameTiming[1];
        for (int i = 0; i < frames; i++)
        {
            yield return null;
            cpu.Add(Time.unscaledDeltaTime * 1000f);
            foreach (var kv in counters) vals[kv.Key].Add(kv.Value.LastValue);
            FrameTimingManager.CaptureFrameTimings();
            if (FrameTimingManager.GetLatestTimings(1, ft) > 0 && ft[0].gpuFrameTime > 0) gpu.Add(ft[0].gpuFrameTime);
        }
        foreach (var r in counters.Values) r.Dispose();
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
        Last = "{" + $"\"name\":\"{name}\",\"frames\":{frames},\"cpu_ms_median\":{Pct(cpu, 0.5f):F1},\"cpu_ms_p95\":{Pct(cpu, 0.95f):F1},\"cpu_ms_p99\":{Pct(cpu, 0.99f):F1},"
             + $"\"gpu_ms_median\":{gpuS},\"gpu_ms_p10\":{gpu10},\"rt_lights\":{rt},\"rt_shadow_lights\":{rtShadow}," + string.Join(",", vals.Select(kv => $"\"{kv.Key}\":{Med(kv.Value)}"))
             + $",\"screen\":\"{Screen.width}x{Screen.height}\",\"focused\":{Application.isFocused.ToString().ToLower()},\"cam\":\"{cam.position.x:F2},{cam.position.y:F2},{cam.position.z:F2} yaw {cam.eulerAngles.y:F0}\"" + "}";
        var dir = outDir ?? Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/perf")); Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, name + ".json"), Last + "\n");
        if (outDir == null) Destroy(gameObject);
    }
}
