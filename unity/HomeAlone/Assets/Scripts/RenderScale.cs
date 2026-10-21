using UnityEngine;
using UnityEngine.Rendering;

// RENDER SCALE (Oct 20; docs/PERFORMANCE.md "Full screen 5K"): the share of the window's pixels the house is rendered at, upscaled to the
// window by STP (HDRP dynamic resolution, HDRP.asset: enabled, hardware, STP, mip bias, 33-100%). 100 = native, no upscaler (the look
// every earlier baseline measured). P cycles the steps while walking (saved, PlayerPrefs, like the night white balance's [ ]).
// THE DEFAULT for a fresh install: Default. PerfProbe's variant scale=P sets it without saving.
// AUTO (0, the default; user Oct 20: "I see no difference between the high res render and the 2048x1152"): render at about AutoHeight
// pixels high whatever the window (5K full screen -> 40%; a 1080p window -> 100%), so a percentage never makes a small window blurry.
// ADAPTIVE (-1; Oct 20, user: "30 fps is the floor"): auto's size is the ceiling; the frame MEAN over each 0.5 s window (the real frame
// time on this GPU-bound Metal player; FrameTimingManager's GPU time is too sparse, docs/PERFORMANCE.md) over 33.3 ms steps the scale down
// 5 points, under 25 ms steps it back up (hysteresis), never below about 720 px high. A step down that doesn't cut the mean by 3% (STP's
// fixed cost: a 1080p window, PERFORMANCE.md "Resolution A/B") is undone and the scaler holds 30 s.
// DYNRES (DynRes): where STP upscales, software/hardware, STP or not. HDRP.asset STPInjectionPoint = BeforePost (post runs at the output size, 5K full screen);
// AfterPost runs post at the internal size. Set at runtime through the asset's serialized settings (the public setter re-creates HDRP).
public class RenderScale : MonoBehaviour
{
    public static readonly float[] Steps = { 0f, -1f, 100f, 75f, 50f, 38f };   // 0 = auto, -1 = adaptive; 5K window: native, ~4K, ~1440p, ~1080p internal
    public const float Default = 0f, AutoHeight = 1152f, MinHeight = 720f; const string Key = "RenderScale";
    public const float AdaptDownMs = 33.3f, AdaptUpMs = 25f, AdaptStep = 5f, AdaptWindowS = 0.5f, AdaptHoldS = 30f;
    public static float Mode { get; private set; } = Default;   // what the user picked (0 = auto, -1 = adaptive)
    static float H(float px) => Mathf.Clamp(px / Mathf.Max(1, Screen.height) * 100f, 33f, 100f);
    public static float Percent => Mode > 0f ? Mode : Mode < 0f ? (adapt < 0f ? H(AutoHeight) : Mathf.Clamp(adapt, H(MinHeight), H(AutoHeight))) : H(AutoHeight);
    public static string Label => Mode > 0f ? $"{Mode:0}%" : Mode < 0f ? $"adaptive ({Percent:0}%)" : $"auto ({Percent:0}%)";
    static float adapt = -1f, winMs, lastMean, holdUntil; static int winN; static bool stepped;
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
        Mode = pct < 0f ? -1f : pct == 0f ? 0f : Mathf.Clamp(pct, 33f, 100f);
        adapt = -1f; winMs = 0f; winN = 0; stepped = false; holdUntil = 0f;   // adaptive starts at auto's size (-1: of the screen it lands on: a resize lands a frame later)
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

    // one 0.5 s window of frame times -> at most one bounded step (see ADAPTIVE above)
    static void Adapt()
    {
        if (Mode >= 0f) return;
        winMs += Time.unscaledDeltaTime * 1000f; winN++;
        if (winMs < AdaptWindowS * 1000f) return;
        float mean = winMs / winN, p = Percent, now = Time.unscaledTime; winMs = 0f; winN = 0;
        if (now < holdUntil) return;
        if (stepped && mean > lastMean * 0.97f) { adapt = p + AdaptStep; stepped = false; holdUntil = now + AdaptHoldS; return; }   // didn't pay: undo
        stepped = false;
        if (mean > AdaptDownMs && p > H(MinHeight) + 0.5f) { adapt = p - AdaptStep; stepped = true; lastMean = mean; }
        else if (mean < AdaptUpMs && p < H(AutoHeight) - 0.5f) adapt = p + AdaptStep;
    }

    // Dynamic resolution settings at runtime (PerfProbe variants; null = HDRP.asset's own): STP's injection point, Software/Hardware
    // dynamic resolution, and the upscaler (false = no STP: HDRP's CatmullRom filter). Through the private serialized struct: the public
    // setter calls OnValidate, which re-creates the pipeline in a player
    static GlobalDynamicResolutionSettings? dr0;
    public static string DynRes(DynamicResolutionHandler.UpsamplerScheduleType? inject, DynamicResolutionType? type = null, bool? stp = null)
    {
        if (!(GraphicsSettings.currentRenderPipeline is UnityEngine.Rendering.HighDefinition.HDRenderPipelineAsset a)) return "no HDRP asset";
        var f = typeof(UnityEngine.Rendering.HighDefinition.HDRenderPipelineAsset).GetField("m_RenderPipelineSettings", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        if (f == null) return "m_RenderPipelineSettings not found";
        var s = (UnityEngine.Rendering.HighDefinition.RenderPipelineSettings)f.GetValue(a);
        dr0 ??= s.dynamicResolutionSettings; var d = dr0.Value;
        d.STPInjectionPoint = inject ?? d.STPInjectionPoint; d.dynResType = type ?? d.dynResType;
        if (stp == false) { d.advancedUpscalersByPriority = new System.Collections.Generic.List<AdvancedUpscalers>(); d.upsampleFilter = DynamicResUpscaleFilter.CatmullRom; }
        s.dynamicResolutionSettings = d; f.SetValue(a, s);
        var r = a.currentPlatformRenderPipelineSettings.dynamicResolutionSettings;
        return $"{r.STPInjectionPoint} {r.dynResType} {(r.advancedUpscalersByPriority.Count > 0 ? string.Join("+", r.advancedUpscalersByPriority) : r.upsampleFilter.ToString())}";
    }

    void Update()
    {
        Adapt();
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
        GUI.Label(new Rect(14, 44, 1000, 30), $"Render scale {Label}: {w}x{h} of {Screen.width}x{Screen.height}{(Percent < 99.5f ? ", STP upscaled" : ", native")}   (P cycles auto/adaptive/100/75/50/38)", st);
    }
}
