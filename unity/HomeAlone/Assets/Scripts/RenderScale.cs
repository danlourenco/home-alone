using UnityEngine;
using UnityEngine.Rendering;

// RENDER SCALE (Oct 21; docs/PERFORMANCE.md "Full screen 5K" and "fs5k-diag"): in FULL SCREEN the backbuffer itself is rendered at a
// share of the display's native pixels and macOS scales it to the panel. No HDRP dynamic resolution: on this Metal player it stalls the
// render thread for the whole frame at the heavy poses (fs5k-diag: full screen 2048x1152 at 100% ran 23-30 fps where 5K at 40%
// dynamic resolution ran 17-24, and STP was not the cause). WINDOWS always render natively (a window's backbuffer is its size).
// AUTO (0, the default; user Oct 20: "I see no difference between the high res render and the 2048x1152"): about AutoHeight pixels
// high (5K -> 2048x1152); a display at or under AutoHeight stays native. P cycles auto/100/75/50/38 (% of native, saved in PlayerPrefs).
// PerfProbe's scale=P sets it without saving; Manual (PerfProbe screen=WxH) leaves the backbuffer to the caller.
public class RenderScale : MonoBehaviour
{
    public static readonly float[] Steps = { 0f, 100f, 75f, 50f, 38f };   // 0 = auto; 5K full screen: native, 4K, 1440p, ~1080p
    public const float Default = 0f, AutoHeight = 1152f; const string Key = "RenderScale";
    public static float Mode { get; private set; } = Default;   // what the user picked (0 = auto)
    public static bool Manual, Stp;   // Stp (PerfProbe aa=stp): the camera opts into dynamic resolution, forced to 100% = STP as pure TAA
    static bool Full => Screen.fullScreenMode != FullScreenMode.Windowed;
    static Vector2Int Native { get { var d = Screen.mainWindowDisplayInfo; return d.height > 0 ? new Vector2Int(d.width, d.height) : new Vector2Int(Screen.currentResolution.width, Screen.currentResolution.height); } }
    public static float Percent => !Full ? 100f : Mode > 0f ? Mode : Mathf.Min(100f, AutoHeight / Mathf.Max(1, Native.y) * 100f);
    public static string Label => (Mode > 0f ? $"{Mode:0}%" : $"auto ({Percent:0}%)") + (Full ? "" : ", window: native");
    static float shownUntil, askedAt = -10f; static Vector2Int asked;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        var g = new GameObject("RenderScale"); DontDestroyOnLoad(g); g.AddComponent<RenderScale>();
        Set(PlayerPrefs.GetFloat(Key, Default), false);
    }

    public static void Set(float pct, bool save)
    {
        Mode = pct <= 0f ? 0f : Mathf.Clamp(pct, 33f, 100f);
        if (save) { PlayerPrefs.SetFloat(Key, Mode); PlayerPrefs.Save(); shownUntil = Time.unscaledTime + 3f; }
        askedAt = -10f; Apply();
    }

    // full screen: request the backbuffer for Percent (again at most once a second while the screen disagrees: a resize lands a few
    // frames later, and entering full screen resets it); the camera never uses dynamic resolution
    static void Apply()
    {
        var cam = Camera.main;
        if (cam && cam.allowDynamicResolution != Stp) cam.allowDynamicResolution = Stp;
        if (cam && cam.TryGetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData>(out var hd) && hd.allowDynamicResolution != Stp) hd.allowDynamicResolution = Stp;
        if (Manual || !Full) return;
        var n = Native; var t = new Vector2Int(Mathf.RoundToInt(n.x * Percent / 100f), Mathf.RoundToInt(n.y * Percent / 100f));
        if (Screen.width == t.x && Screen.height == t.y) return;
        if (t == asked && Time.unscaledTime - askedAt < 1f) return;
        asked = t; askedAt = Time.unscaledTime; Screen.SetResolution(t.x, t.y, Screen.fullScreenMode);
    }

    // Dynamic resolution settings at runtime (PerfProbe diagnostics; null = HDRP.asset's own): STP's injection point, Software/Hardware
    // dynamic resolution, and the upscaler (false = no STP: HDRP's CatmullRom filter). Through the private serialized struct: the public
    // setter calls OnValidate, which re-creates the pipeline in a player
    static GlobalDynamicResolutionSettings? dr0;
    public static string DynRes(DynamicResolutionHandler.UpsamplerScheduleType? inject, DynamicResolutionType? type = null, bool? stp = null, float? forcePct = null)
    {
        if (!(GraphicsSettings.currentRenderPipeline is UnityEngine.Rendering.HighDefinition.HDRenderPipelineAsset a)) return "no HDRP asset";
        var f = typeof(UnityEngine.Rendering.HighDefinition.HDRenderPipelineAsset).GetField("m_RenderPipelineSettings", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        if (f == null) return "m_RenderPipelineSettings not found";
        var s = (UnityEngine.Rendering.HighDefinition.RenderPipelineSettings)f.GetValue(a);
        dr0 ??= s.dynamicResolutionSettings; var d = dr0.Value;
        d.STPInjectionPoint = inject ?? d.STPInjectionPoint; d.dynResType = type ?? d.dynResType;
        if (forcePct is float fp) { d.forceResolution = true; d.forcedPercentage = fp; }
        if (stp == false) { d.advancedUpscalerNames = new System.Collections.Generic.List<string>(); d.upsampleFilter = DynamicResUpscaleFilter.CatmullRom; }
        s.dynamicResolutionSettings = d; f.SetValue(a, s);
        var r = a.currentPlatformRenderPipelineSettings.dynamicResolutionSettings;
        return $"{r.STPInjectionPoint} {r.dynResType} {(r.advancedUpscalerNames != null && r.advancedUpscalerNames.Count > 0 ? string.Join("+", r.advancedUpscalerNames) : r.upsampleFilter.ToString())}";
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
        GUI.Label(new Rect(14, 44, 1100, 30), $"Render scale {Label}: {Screen.width}x{Screen.height} of {Native.x}x{Native.y}{(Full ? ", scaled to the display" : "")}   (P cycles auto/100/75/50/38)", st);
    }
}
