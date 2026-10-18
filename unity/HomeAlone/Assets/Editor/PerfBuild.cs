using System;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

// Standalone macOS player of House_WallGrid for the perf probe (tools/house/perf_probe.sh; docs/PERFORMANCE.md).
//   Unity -batchmode -projectPath <copy> -executeMethod PerfBuild.Build -perfOut <dir>/HomeAlonePerf.app -quit
// Run it in a throwaway COPY of the project (the script turns on Frame Timing Stats, which GPU frame times need): never the repo project.
public static class PerfBuild
{
    public static void Build()
    {
        var a = Environment.GetCommandLineArgs(); int i = Array.IndexOf(a, "-perfOut");
        string outPath = i >= 0 && i + 1 < a.Length ? a[i + 1] : throw new ArgumentException("PerfBuild: -perfOut <path.app> missing");
        PlayerSettings.enableFrameTimingStats = true;
        PlayerSettings.runInBackground = true;   // the tour runs unattended behind other windows (a paused player never loads)
        // this install's Mac player support has IL2CPP variations only: the default (Mono) compiles against the editor's assemblies and fails
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.IL2CPP);
        var r = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { "Assets/Scenes/House_WallGrid.unity" },
            locationPathName = outPath, target = BuildTarget.StandaloneOSX, options = BuildOptions.None,
        });
        Debug.Log($"PerfBuild: {r.summary.result} {r.summary.totalSize >> 20} MB in {r.summary.totalTime.TotalSeconds:F0} s -> {outPath}");
        if (r.summary.result != BuildResult.Succeeded) EditorApplication.Exit(1);
    }
}
