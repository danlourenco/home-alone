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
public class PerfProbe : MonoBehaviour
{
    public static string Last = "";

    public static void Run(string name, int frames)
    {
        var g = new GameObject("PerfProbe"); var p = g.AddComponent<PerfProbe>(); p.StartCoroutine(p.Sample(name, frames));
    }

    IEnumerator Sample(string name, int frames)
    {
        Last = "running";
        var counters = new Dictionary<string, ProfilerRecorder>
        {
            ["batches"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count"),
            ["setpass"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "SetPass Calls Count"),
            ["triangles"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count"),
            ["shadow_casters"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Shadow Casters Count"),
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
        float Pct(List<float> l, float p) { var s = l.OrderBy(x => x).ToList(); return s[Mathf.Clamp((int)(p * (s.Count - 1)), 0, s.Count - 1)]; }
        long Med(List<long> l) { var s = l.OrderBy(x => x).ToList(); return s[s.Count / 2]; }
        var cam = Camera.main ? Camera.main.transform : transform;
        string gpuS = gpu.Count > 0 ? gpu.OrderBy(x => x).ElementAt(gpu.Count / 2).ToString("F1") : "null";
        Last = "{" + $"\"name\":\"{name}\",\"frames\":{frames},\"cpu_ms_median\":{Pct(cpu, 0.5f):F1},\"cpu_ms_p95\":{Pct(cpu, 0.95f):F1},\"cpu_ms_p99\":{Pct(cpu, 0.99f):F1},"
             + $"\"gpu_ms_median\":{gpuS}," + string.Join(",", vals.Select(kv => $"\"{kv.Key}\":{Med(kv.Value)}"))
             + $",\"screen\":\"{Screen.width}x{Screen.height}\",\"focused\":{Application.isFocused.ToString().ToLower()},\"cam\":\"{cam.position.x:F2},{cam.position.y:F2},{cam.position.z:F2} yaw {cam.eulerAngles.y:F0}\"" + "}";
        var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/perf")); Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, name + ".json"), Last + "\n");
        Destroy(gameObject);
    }
}
