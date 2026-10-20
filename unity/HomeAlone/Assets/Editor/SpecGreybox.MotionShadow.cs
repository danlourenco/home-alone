using System.IO;
using System.Linq;
using System.Text;
using UnityEditor.SceneManagement;
using UnityEngine;

// MOTION SHADOWS (Oct 20, user in the Mac app: "if i open the door or hit a paint can, the fps becomes laughable again"). Anything that
// moves asks the lamps' cached shadow maps to redraw (Scripts/ShadowRefresh.cs). This gate simulates, at night with every lamp on, 10 s
// at 60 Hz of: the front door opening (EntranceDoor.Step, E's path), and a paint can knocked at walking speed (1.4 m/s, as
// PaintCanTrap.PushByPlayer shoves it). Per run: cube faces redrawn (point lamp 6, spot 1) per frame, max and mean, the frame the
// piece came to rest and the frame the redraw queue emptied. The same runs with ShadowRefresh.Legacy (every lamp in range, every
// frame: the behaviour the user hit) are the "before". FAILS: max faces in a frame > 6 x MaxPerFrame, the queue not empty 1 s after
// rest, the door not at rest in 2 s, the can not at rest in 10 s.
// Standalone on a saved scene: -executeMethod SpecGreybox.MotionShadowCheckScene (Library/MotionShadowCheck.txt).
public static partial class SpecGreybox
{
    public static void MotionShadowCheckScene()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity", OpenSceneMode.Single);
        var r = ShadowBudgetCheck() + MotionShadowCheck();
        File.WriteAllText("Library/MotionShadowCheck.txt", r); Debug.Log(r);
    }

    // SHADOW BUDGET (perf pass 1): renderers that cast into the sun's cascades from the street pose (PerfProbe "street"): enabled by day,
    // casting, bounds within the sun's shadow distance (SunShadowDistance). Limit: the
    // static-street-casters row of docs/PERFORMANCE.md. The tour's own count (HDRP "Shadow Casters Count") is per cascade and frame.
    static string ShadowBudgetCheck()
    {
        float dist = SunShadowDistance;   // the build's GreyboxVolume override (SpecGreybox.Volume)
        var mode = Object.FindAnyObjectByType<HouseNightMode>(FindObjectsInactive.Include);
        bool wasNight = mode && mode.nightLayer && mode.nightLayer.activeSelf, wasDay = mode && mode.dayLayer && mode.dayLayer.activeSelf;
        if (mode && mode.nightLayer) mode.nightLayer.SetActive(false); if (mode && mode.dayLayer) mode.dayLayer.SetActive(true);
        var street = new Vector3(34f, -2.7f, -9.7f);
        var sunless = new System.Collections.Generic.HashSet<Renderer>(mode ? mode.sunlessCasters : new Renderer[0]);   // off by day (SunCull)
        int n = Object.FindObjectsByType<Renderer>().Count(r => !sunless.Contains(r) && r.enabled && r.gameObject.activeInHierarchy && r.shadowCastingMode != UnityEngine.Rendering.ShadowCastingMode.Off && r.bounds.SqrDistance(street) < dist * dist);
        if (mode && mode.nightLayer) mode.nightLayer.SetActive(wasNight); if (mode && mode.dayLayer) mode.dayLayer.SetActive(wasDay);
        // the repo's docs; a scratch build reaches them through its spec link (unity_pipeline.sh setup: ROOT/spec -> repo/spec)
        string Real(string p) { var ps = System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo("/usr/bin/readlink", "-f \"" + p + "\"") { RedirectStandardOutput = true, UseShellExecute = false }); var o = ps.StandardOutput.ReadToEnd().Trim(); ps.WaitForExit(); return o; }
        var mdPath = new[] { Path.Combine(RepoRoot, "docs/PERFORMANCE.md"), Path.Combine(Path.GetDirectoryName(Real(Path.Combine(RepoRoot, "spec"))) ?? "", "docs/PERFORMANCE.md") }.FirstOrDefault(File.Exists);
        if (mdPath == null) return "ShadowBudget FAIL: docs/PERFORMANCE.md not found\n";
        var md = File.ReadAllText(mdPath);
        var m = System.Text.RegularExpressions.Regex.Match(md, @"\|\s*static-street-casters\s*\|\s*(\d+)");
        int lim = m.Success ? int.Parse(m.Groups[1].Value) : int.MaxValue;
        string line = $"ShadowBudget {(n <= lim ? "ok" : "FAIL")}: {n} sun shadow casters within {dist:F0} m of the street pose (limit {lim}, docs/PERFORMANCE.md)\n";
        if (n > lim) Debug.LogError("BUDGET FAIL " + line);
        return line;
    }

    static string MotionShadowCheck()
    {
        var mode = Object.FindAnyObjectByType<HouseNightMode>(FindObjectsInactive.Include);
        var night = mode ? mode.nightLayer : null; bool wasNight = night && night.activeSelf;
        var day = mode ? mode.dayLayer : null; bool wasDay = day && day.activeSelf;
        var door = Object.FindObjectsByType<EntranceDoor>(FindObjectsInactive.Include).FirstOrDefault(d => d.label == "front door");
        var cans = Object.FindObjectsByType<PaintCanTrap>(FindObjectsInactive.Include).OrderBy(q => q.name).ToArray();
        var sb = new StringBuilder("MOTION SHADOWS (night, 10 s at 60 Hz; faces = cached shadow cube faces redrawn: point 6, spot 1)\n");
        bool fail = false;
        var simMode = Physics.simulationMode; Physics.simulationMode = SimulationMode.Script;
        try
        {
            if (night) night.SetActive(true); if (day) day.SetActive(false);
            Physics.SyncTransforms();
            foreach (var t in cans) t.Setup();
            foreach (bool legacy in new[] { true, false })
            {
                if (door) Run($"front door opens{(legacy ? " (before: legacy)" : "")}", legacy, 2f,
                    () => { door.SetInstant(false); door.SetOpen(true); }, dt => { door.Step(dt); return door.Moving; }, () => door.SetInstant(false));
                if (cans.Length > 0) Run($"paint can knocked 1.4 m/s{(legacy ? " (before: legacy)" : "")}", legacy, 10f,
                    () => { foreach (var t in cans) t.ResetRig(); Physics.SyncTransforms(); { cans[0].can.WakeUp(); cans[0].can.linearVelocity = Vector3.forward * 1.4f; }; },
                    dt => { foreach (var t in cans) t.Tick(dt); Physics.Simulate(dt); bool m = false; foreach (var t in cans) m |= t.ShadowTick(); return m; },
                    () => { foreach (var t in cans) t.ResetRig(); Physics.SyncTransforms(); });
            }
        }
        finally
        {
            Physics.simulationMode = simMode; ShadowRefresh.Legacy = false;
            if (night) night.SetActive(wasNight); if (day) day.SetActive(wasDay);
            Physics.SyncTransforms();
        }
        sb.Append(fail ? "MotionShadow FAIL (see above)\n" : "MotionShadow ok\n");
        if (fail) Debug.LogError("BUDGET FAIL motion shadows:\n" + sb);
        return sb.ToString();

        void Run(string what, bool legacy, float restBudget, System.Action start, System.Func<float, bool> step, System.Action reset)
        {
            const float dt = 1f / 60f; const int frames = 600;
            ShadowRefresh.Legacy = legacy;
            for (int f = -10; f < 0; f++) ShadowRefresh.Tick(f);   // empty the queue left by the scene
            start();
            int faces = 0, maxFaces = 0, rest = -1, empty = -1;
            var who = new System.Collections.Generic.HashSet<string>();
            var lightsByName = Object.FindObjectsByType<Light>().GroupBy(l => l.name).ToDictionary(g => g.Key, g => g.First());
            for (int f = 0; f < frames; f++)
            {
                ShadowRefresh.Drawn.Clear();
                bool moving = step(dt);
                ShadowRefresh.Tick(1000 + f);
                int n = ShadowRefresh.Drawn.Sum(x => lightsByName.TryGetValue(x, out var l) && l.type == LightType.Point ? 6 : 1);
                foreach (var x in ShadowRefresh.Drawn) who.Add(x);
                faces += n; maxFaces = Mathf.Max(maxFaces, n);
                if (moving) rest = -1; else if (rest < 0) rest = f;
                if (ShadowRefresh.Pending > 0 || moving || n > 0) empty = -1; else if (empty < 0) empty = f;
            }
            reset(); ShadowRefresh.Drawn.Clear();
            for (int f = 0; f < 60; f++) ShadowRefresh.Tick(5000 + f);
            ShadowRefresh.Legacy = false;
            bool ok = legacy || (maxFaces <= 6 * ShadowRefresh.MaxPerFrame && rest >= 0 && rest * dt <= restBudget && empty >= 0 && (empty - rest) * dt <= 1f);
            if (!ok) fail = true;
            sb.Append($"{(legacy ? "info" : ok ? "ok  " : "FAIL")} {what}: rest at {(rest < 0 ? "never (10 s)" : $"{rest * dt:F2} s")} (budget {restBudget:F0} s), queue empty at {(empty < 0 ? "never" : $"{empty * dt:F2} s")}; " +
                $"faces max {maxFaces}/frame (budget {6 * ShadowRefresh.MaxPerFrame}), mean {faces / (float)frames:F1}/frame, total {faces}; {who.Count} lamps: {string.Join(", ", who.OrderBy(x => x).Take(14))}{(who.Count > 14 ? " ..." : "")}\n");
        }
    }
}
