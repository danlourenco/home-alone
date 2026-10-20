using System;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

// Standalone macOS player of House_WallGrid: the local Mac test app and the perf probe (tools/house/perf_probe.sh; docs/PERFORMANCE.md).
//   Unity -batchmode -projectPath <copy> -executeMethod PerfBuild.Build -perfOut <dir>/HomeAlone.app [-perfDev] -quit
// Run it in a throwaway COPY of the project (it changes player settings): never the repo project. -perfDev makes a development
// player (batches/draw calls/gfx memory are counted only there, and the "Ran out of Graphics Ring Buffer space" warning is logged
// only there); its frame times are not the baseline.
// LOCAL ONLY: the player carries gitignored store assets and the unlicensed exterior GLB. Never distribute it.
public static class PerfBuild
{
    public static void Build()
    {
        var a = Environment.GetCommandLineArgs(); int i = Array.IndexOf(a, "-perfOut");
        string outPath = i >= 0 && i + 1 < a.Length ? a[i + 1] : throw new ArgumentException("PerfBuild: -perfOut <path.app> missing");
        bool dev = Array.IndexOf(a, "-perfDev") >= 0;
        const string scene = "Assets/Scenes/House_WallGrid.unity";
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(scene, true) };
        // a stable local identity with no personal data in it (the bundle id names the app's prefs and its data folder)
        PlayerSettings.companyName = "HomeAloneLocal"; PlayerSettings.productName = "HomeAlone";
        PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Standalone, "com.homealone.local");
        PlayerSettings.fullScreenMode = FullScreenMode.Windowed; PlayerSettings.resizableWindow = true;
        PlayerSettings.defaultScreenWidth = 1920; PlayerSettings.defaultScreenHeight = 1080;
        PlayerSettings.enableFrameTimingStats = true;
        PlayerSettings.runInBackground = true;   // the tour runs unattended behind other windows (a paused player never loads)
        // this install's Mac player support has IL2CPP variations only: the default (Mono) compiles against the editor's assemblies and fails
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.IL2CPP);
        UnityEditor.OSXStandalone.UserBuildSettings.architecture = UnityEditor.Build.OSArchitecture.ARM64;   // host M3 Pro
        // -perfDynRes: HDRP dynamic resolution on with STP first (a clone-only project setting; PerfProbe -perfvariants res=75 sets the
        // percentage at run time). For the resolution A/B only: the shipped app has it off
        if (Array.IndexOf(a, "-perfDynRes") >= 0)
        {
            var hdrp = AssetDatabase.LoadAssetAtPath<UnityEngine.Rendering.HighDefinition.HDRenderPipelineAsset>("Assets/Settings/HDRP.asset");
            var so = new SerializedObject(hdrp); const string d = "m_RenderPipelineSettings.dynamicResolutionSettings.";
            so.FindProperty(d + "enabled").boolValue = true; so.FindProperty(d + "minPercentage").floatValue = 50f;
            var up = so.FindProperty(d + "advancedUpscalersByPriority"); up.arraySize = 1; up.GetArrayElementAtIndex(0).intValue = 2;   // STP
            so.ApplyModifiedPropertiesWithoutUndo(); EditorUtility.SetDirty(hdrp); AssetDatabase.SaveAssets();
            Debug.Log("PerfBuild: dynamic resolution on (STP), 50-100%");
        }
        var r = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { scene },
            locationPathName = outPath, target = BuildTarget.StandaloneOSX,
            options = dev ? BuildOptions.Development : BuildOptions.None,
        });
        Debug.Log($"PerfBuild: {r.summary.result} {(dev ? "development " : "")}{r.summary.totalSize >> 20} MB in {r.summary.totalTime.TotalSeconds:F0} s -> {outPath}");
        if (r.summary.result != BuildResult.Succeeded) EditorApplication.Exit(1);
    }
}
