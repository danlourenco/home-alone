using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

/// Headless HDRP setup: creates and assigns the pipeline asset so the project
/// never has to go through the HDRP wizard by hand.
/// Run: Unity -batchmode -projectPath . -executeMethod HdrpBootstrap.Setup -quit
public static class HdrpBootstrap
{
    const string AssetPath = "Assets/Settings/HDRP.asset";

    [MenuItem("HomeAlone/Setup HDRP")]
    public static void Setup()
    {
        Directory.CreateDirectory("Assets/Settings");
        var asset = AssetDatabase.LoadAssetAtPath<HDRenderPipelineAsset>(AssetPath);
        if (asset == null)
        {
            asset = ScriptableObject.CreateInstance<HDRenderPipelineAsset>();
            AssetDatabase.CreateAsset(asset, AssetPath);
        }
        GraphicsSettings.defaultRenderPipeline = asset;
        int level = QualitySettings.GetQualityLevel();
        for (int i = 0; i < QualitySettings.names.Length; i++) { QualitySettings.SetQualityLevel(i, false); QualitySettings.renderPipeline = asset; }
        QualitySettings.SetQualityLevel(level, false);
        PlayerSettings.colorSpace = ColorSpace.Linear;

        // HDRP global settings asset (default volume profiles etc.) is normally created by the
        // wizard. The type is internal, so poke it by reflection; harmless if the signature moved.
        var t = System.Type.GetType("UnityEngine.Rendering.HighDefinition.HDRenderPipelineGlobalSettings, Unity.RenderPipelines.HighDefinition.Runtime");
        var ensure = t?.GetMethod("Ensure", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
        if (ensure != null) { var ps = ensure.GetParameters(); ensure.Invoke(null, ps.Length == 1 ? new object[] { true } : new object[0]); Debug.Log("HDRP global settings ensured"); }
        else Debug.LogWarning("HDRenderPipelineGlobalSettings.Ensure not found; HDRP will create global settings on first Editor open.");

        AssetDatabase.SaveAssets();
        Debug.Log("HDRP bootstrap done: " + AssetPath);
    }
}
