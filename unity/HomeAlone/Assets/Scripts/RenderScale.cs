using UnityEngine;
using UnityEngine.Rendering;

// RENDER SCALE (Oct 20; docs/PERFORMANCE.md "Full screen 5K"): the share of the window's pixels the house is rendered at, upscaled to the
// window by STP (HDRP dynamic resolution, HDRP.asset: enabled, hardware, STP, mip bias, 33-100%). 100 = native, no upscaler (the look
// every earlier baseline measured). P cycles the steps while walking (saved, PlayerPrefs, like the night white balance's [ ]).
// THE DEFAULT for a fresh install: Default. PerfProbe's variant scale=P sets it without saving.
// AUTO (0, the default; user Oct 20: "I see no difference between the high res render and the 2048x1152"): render at about AutoHeight
// pixels high whatever the window (5K full screen -> 40%; a 1080p window -> 100%), so a percentage never makes a small window blurry.
public class RenderScale : MonoBehaviour
{
    public static readonly float[] Steps = { 0f, 100f, 75f, 50f, 38f };   // 0 = auto; 5K window: native, ~4K, ~1440p, ~1080p internal
    public const float Default = 0f, AutoHeight = 1152f; const string Key = "RenderScale";
    public static float Mode { get; private set; } = Default;   // what the user picked (0 = auto)
    public static float Percent => Mode > 0f ? Mode : Mathf.Clamp(AutoHeight / Mathf.Max(1, Screen.height) * 100f, 33f, 100f);
    public static string Label => Mode > 0f ? $"{Mode:0}%" : $"auto ({Percent:0}%)";
    static float shownUntil;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        var g = new GameObject("RenderScale"); DontDestroyOnLoad(g); g.AddComponent<RenderScale>();
        DynamicResolutionHandler.SetDynamicResScaler(() => Percent, DynamicResScalePolicyType.ReturnsPercentage);
        Set(PlayerPrefs.GetFloat(Key, Default), false);
    }

    public static void Set(float pct, bool save)
    {
        Mode = pct <= 0f ? 0f : Mathf.Clamp(pct, 33f, 100f);
        if (save) { PlayerPrefs.SetFloat(Key, Mode); PlayerPrefs.Save(); shownUntil = Time.unscaledTime + 3f; }
        Apply();
    }

    // the main camera opts in below 100% (at 100% it renders exactly as before: no STP pass); re-applied each frame in case the camera changes
    static void Apply()
    {
        var cam = Camera.main; if (!cam) return;
        bool on = Percent < 99.5f;
        if (cam.allowDynamicResolution != on) cam.allowDynamicResolution = on;
        if (cam.TryGetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData>(out var hd) && hd.allowDynamicResolution != on) hd.allowDynamicResolution = on;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.P))
        {
            int i = System.Array.FindIndex(Steps, s => Mathf.Abs(s - Mode) < 0.5f);
            Set(Steps[(i + 1) % Steps.Length], true);
        }
        Apply();
    }

    void OnGUI()
    {
        if (Time.unscaledTime > shownUntil) return;
        var st = new GUIStyle(GUI.skin.label) { fontSize = 18 }; st.normal.textColor = Color.white;
        int w = Mathf.RoundToInt(Screen.width * Percent / 100f), h = Mathf.RoundToInt(Screen.height * Percent / 100f);
        GUI.Label(new Rect(14, 44, 1000, 30), $"Render scale {Label}: {w}x{h} of {Screen.width}x{Screen.height}{(Percent < 99.5f ? ", STP upscaled" : ", native")}   (P cycles auto/100/75/50/38)", st);
    }
}
