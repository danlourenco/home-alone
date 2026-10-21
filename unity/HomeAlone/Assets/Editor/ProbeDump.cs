using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// What the baked probes give the front wall (Oct 21, brick-upstairs: two fixes failed, attack the premise). For each probe scenario
// (DayFilm, NightFilm, Default, Night) it reads the APV irradiance on a +x-facing white card at points in front of (and just behind)
// the main front's brick, at the ground storey's and the upper storey's brick heights, in several columns along the front. Each card
// is read twice: on LayerOutside (the Exterior probe class the skin reads) and on LayerApvInside (the rooms' class). Every light is off,
// fog/SSAO/SSR/contact shadows off, exposure fixed (EV100 0), no tonemapping: the value is the probes' diffuse light alone, comparable
// across points and scenarios (relative numbers; same exposure everywhere). The film's flush front: upper/lower should be ~1.
//   Unity -projectPath <scratch> -executeMethod ProbeDump.Run -dumpOut <file.json> -logFile <log>   (windowed, like BakeLighting.Bake:
//   the APV streams and the camera renders only in a render loop; exits when done). Prints a table and writes the JSON.
public static class ProbeDump
{
    static readonly string[] Scenarios = { "DayFilm", "NightFilm", "Default", "Night" };
    static readonly float[] Depths = { -0.6f, 0.15f, 0.4f, 0.8f, 1.3f, 2.0f };   // metres in front of the brick (+x); -0.6 inside the skin
    static readonly float[] Columns = { -4f, -6f, -8f, -11f, -13f, -15f };          // Unity z along the main front (spec z 2.86-16.21)
    const int Frames = 12;

    public static void Run()
    {
        bool exit = System.Environment.GetCommandLineArgs().Contains("-executeMethod");
        var e = Steps();
        void Tick()
        {
            EditorApplication.QueuePlayerLoopUpdate();
            if (e.MoveNext()) return;
            EditorApplication.update -= Tick;
            if (exit) EditorApplication.Exit(0);
        }
        EditorApplication.update += Tick;
    }

    static string Arg(string k) { var a = System.Environment.GetCommandLineArgs(); int i = System.Array.IndexOf(a, k); return i >= 0 && i + 1 < a.Length ? a[i + 1] : null; }

    static IEnumerator Steps()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity");
        string spec = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/"));
        float brick = (float)JObject.Parse(File.ReadAllText(spec + "exterior_shell.json"))["front_main"];
        float gy = (float)JObject.Parse(File.ReadAllText(spec + "geometry.json"))["ground"]["floor_y"];
        // brick heights: the ground storey between its windows (gy + 1.6), the upper storey's (the skin's upper windows 0.464-1.804)
        var heights = new (string name, float y)[] { ("lower", gy + 1.6f), ("upper", 1.1f) };

        // the film's house (HouseSplit state 0: outside, ground floor): skin's upper storey drawn, inside-only pieces hidden
        var split = Object.FindAnyObjectByType<HouseSplit>(); if (split) split.ApplyFor(new Vector3(30f, gy + 1.5f, -9.6f));
        var lights = Object.FindObjectsByType<Light>(FindObjectsInactive.Include).Where(l => l.enabled).ToList();
        foreach (var l in lights) l.enabled = false;

        var vol = new GameObject("ProbeDumpVolume").AddComponent<Volume>(); vol.isGlobal = true; vol.priority = 1e7f;
        var prof = ScriptableObject.CreateInstance<VolumeProfile>(); vol.sharedProfile = prof;
        var ex = prof.Add<Exposure>(true); ex.mode.Override(ExposureMode.Fixed); ex.fixedExposure.Override(0f);
        prof.Add<Tonemapping>(true).mode.Override(TonemappingMode.None);
        prof.Add<Fog>(true).enabled.Override(false);

        var mat = new Material(Shader.Find("HDRP/Lit")); mat.SetColor("_BaseColor", Color.white); mat.SetFloat("_Smoothness", 0f);
        mat.SetFloat("_DoubleSidedEnable", 1f); mat.SetFloat("_DoubleSidedNormalMode", 0f); HDMaterial.ValidateMaterial(mat);
        var card = GameObject.CreatePrimitive(PrimitiveType.Quad); Object.DestroyImmediate(card.GetComponent<Collider>());
        card.transform.localScale = Vector3.one * 0.1f; card.transform.rotation = Quaternion.LookRotation(Vector3.right);
        var cr = card.GetComponent<MeshRenderer>(); cr.sharedMaterial = mat; cr.shadowCastingMode = ShadowCastingMode.Off;

        var cam = new GameObject("ProbeDumpCam").AddComponent<Camera>(); cam.fieldOfView = 20f; cam.nearClipPlane = 0.02f; cam.farClipPlane = 5f;
        var hd = cam.gameObject.AddComponent<HDAdditionalCameraData>(); hd.customRenderingSettings = true;
        foreach (var f in new[] { FrameSettingsField.SSAO, FrameSettingsField.SSR, FrameSettingsField.ContactShadows, FrameSettingsField.Volumetrics, FrameSettingsField.AtmosphericScattering, FrameSettingsField.MotionBlur, FrameSettingsField.DepthOfField, FrameSettingsField.Bloom })
        { hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)f] = true; hd.renderingPathCustomFrameSettings.SetEnabled(f, false); }
        var rt = new RenderTexture(32, 32, 24, RenderTextureFormat.ARGBHalf); cam.targetTexture = rt;
        var tex = new Texture2D(32, 32, TextureFormat.RGBAHalf, false);

        var apv = ProbeReferenceVolume.instance; var rows = new JArray(); var sb = new StringBuilder();
        foreach (var sc in Scenarios)
        {
            if (apv.currentBakingSet == null || !apv.currentBakingSet.lightingScenarios.Contains(sc)) { sb.AppendLine($"{sc}: not baked"); continue; }
            apv.lightingScenario = sc;
            foreach (var (layerName, mask) in new[] { ("exterior", SpecGreybox.LayerOutside), ("interior", SpecGreybox.LayerApvInside) })
            {
                cr.renderingLayerMask = mask;
                foreach (var z in Columns)
                    foreach (var (hname, y) in heights)
                        foreach (var d in Depths)
                        {
                            var p = new Vector3(brick + d, y, z);
                            card.transform.position = p; cam.transform.SetPositionAndRotation(p + Vector3.right * 0.15f, Quaternion.LookRotation(Vector3.left));
                            for (int k = 0; k < Frames; k++) cam.Render();   // the scenario's cells stream in over a few frames
                            yield return null;
                            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, 32, 32), 0, 0); tex.Apply(); RenderTexture.active = null;
                            var c = tex.GetPixel(16, 16);
                            rows.Add(new JObject { ["scenario"] = sc, ["class"] = layerName, ["z"] = z, ["storey"] = hname, ["d"] = d, ["r"] = c.r, ["g"] = c.g, ["b"] = c.b });
                        }
            }
            // the table: upper/lower luminance and R/G per column at 0.4 m out (the brick's own probes) on the Exterior class
            foreach (var z in Columns)
            {
                JObject Get(string h) => rows.Cast<JObject>().First(q => (string)q["scenario"] == sc && (string)q["class"] == "exterior" && (float)q["z"] == z && (string)q["storey"] == h && Mathf.Approximately((float)q["d"], 0.4f));
                float Lum(JObject q) => 0.2126f * (float)q["r"] + 0.7152f * (float)q["g"] + 0.0722f * (float)q["b"];
                var u = Get("upper"); var lo = Get("lower");
                sb.AppendLine($"ProbeDump {sc} z {z}: upper {Lum(u):F3} lower {Lum(lo):F3} upper/lower {Lum(u) / Mathf.Max(1e-6f, Lum(lo)):F2}, R/G {(float)u["r"] / (float)u["g"]:F2} / {(float)lo["r"] / (float)lo["g"]:F2}");
            }
        }
        foreach (var l in lights) l.enabled = true;
        Object.DestroyImmediate(card); Object.DestroyImmediate(cam.gameObject); Object.DestroyImmediate(vol.gameObject);
        var outPath = Arg("-dumpOut") ?? Path.Combine(Application.dataPath, "../probe-dump.json");
        File.WriteAllText(outPath, rows.ToString());
        Debug.Log(sb + $"ProbeDump: {rows.Count} readings -> {outPath}");
    }
}
