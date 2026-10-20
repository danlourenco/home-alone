using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;
using Debug = UnityEngine.Debug;

// The real-time shadow budget, measured (Oct 16, user: "random squares ... sometimes when the camera isn't moving"; "the shadows from
// the plant are cast on the wall, but if i move slightly, they're lost"). HDRP gives every shadowed point light 6 atlas tiles; when the
// visible lights' tiles overflow the dynamic atlas it shrinks ALL of them (HDDynamicShadowAtlas.LayoutResize, m_RcpScaleFactor < 1), and
// past maxShadowRequests it drops shadows (ReserveShadowResolutions returns -1). Cached shadow maps (SpecGreybox.Shadows.cs) live in
// their own atlas and do not take dynamic tiles. This reports, at night, from the walk-note poses:
//   - every light's shadow setup;
//   - per pose: HDRP's shadow requests (used / max), dynamic-atlas tiles and its downscale factor, cached-atlas placements and pending;
//   - a pan of +-30 deg in 2 deg steps ("when i pan left and right"): the downscale factor and request count must not change;
//   - 8 still frames at a fixed exposure: consecutive frames must be identical (max relative pixel change);
//   - a rough frame time (render + readback, batch: indicative only).
//   Unity -batchmode -projectPath <scratch> -executeMethod ShadowAudit.Run -quit -logFile -     -> spec/captures/shadow-audit.txt
[InitializeOnLoad]
public static class ShadowAudit
{
    // PLAY MODE (windowed, like BakeLighting; the batch renders above drive cam.Render() without frames advancing, and HDRP's cached
    // shadows misbehaved there: lamps unlit or blotched in one run, right in another). This enters Play in the scratch editor, as the
    // user walks: the scene's own HouseNightMode (Update -> ShadowRefresh.Warm on Camera.main), N for night, then each view held for
    // 30 frames, captured, plus two consecutive frames compared. Results: spec/captures/views/<names>.png and <-auditOut>.
    //   Unity -projectPath <scratch> -executeMethod ShadowAudit.PlayViews -views views-shadows-after.json [-legacy] -auditOut f.txt
    static ShadowAudit()
    {
        EditorApplication.playModeStateChanged += st => { if (st == PlayModeStateChange.EnteredPlayMode && SessionState.GetString("ShadowAuditPlay", "") != "") { tick = -1; pcam = null; EditorApplication.update += PlayTick; } };
    }

    public static void PlayViews()
    {
        var a = System.Environment.GetCommandLineArgs(); int vi = System.Array.IndexOf(a, "-views"), oi = System.Array.IndexOf(a, "-auditOut");
        SessionState.SetString("ShadowAuditPlay", a[vi + 1]); SessionState.SetBool("ShadowAuditLegacy", System.Array.IndexOf(a, "-legacy") >= 0);
        SessionState.SetString("ShadowAuditOut", oi >= 0 ? a[oi + 1] : "");
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity");
        EditorApplication.EnterPlaymode();
    }

    static int tick, view; static Camera pcam; static RenderTexture prt; static Newtonsoft.Json.Linq.JArray pviews; static StringBuilder psb; static Color32[] prevPx; static float dtSum; static int dtN;
    static void PlayTick()
    {
        UnityEditorInternal.InternalEditorUtility.RepaintAllViews(); EditorApplication.QueuePlayerLoopUpdate();
        if (!EditorApplication.isPlaying) return;
        int f = Time.frameCount;
        if (tick < 0) { tick = f; return; }
        if (pcam == null)
        {
            if (f - tick < 5) return;   // after the scene's own Start (HouseNightMode starts in day)
            if (SessionState.GetBool("ShadowAuditLegacy", false)) Legacy();
            var player = GameObject.Find("Player"); if (player) player.SetActive(false);
            var go = new GameObject("AuditCam"); go.tag = "MainCamera"; pcam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); pcam.nearClipPlane = 0.05f;
            prt = new RenderTexture(1920, 1080, 24); pcam.targetTexture = prt;
            Object.FindFirstObjectByType<HouseNightMode>().SetNight(true);
            var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/views"));
            pviews = Newtonsoft.Json.Linq.JArray.Parse(File.ReadAllText(Path.Combine(dir, SessionState.GetString("ShadowAuditPlay", ""))));
            psb = new StringBuilder($"PLAY-MODE SHADOW AUDIT ({(SessionState.GetBool("ShadowAuditLegacy", false) ? "legacy lamps" : "as built")}), 30 frames per view\n");
            view = 0; tick = f; Pose(); return;
        }
        int W = pviews[view]["frames"] != null ? (int)pviews[view]["frames"] : 30;   // per view: frames to settle (exposure adapts after a day/night switch)
        if (f - tick > W / 2 && f - tick < W) { dtSum += Time.unscaledDeltaTime; dtN++; }   // frame time over the settled half (editor Play: A/B only)
        if (f - tick < W) return;
        if (f - tick == W) { prevPx = Grab(out var t0); Object.DestroyImmediate(t0); return; }
        var px = Grab(out var tex);
        int changed = 0; for (int i = 0; i < px.Length; i++) if (Mathf.Abs(px[i].r - prevPx[i].r) + Mathf.Abs(px[i].g - prevPx[i].g) + Mathf.Abs(px[i].b - prevPx[i].b) > 6) changed++;
        var v = pviews[view]; var s = Stats();
        psb.AppendLine($"{(string)v["name"]}: frame {1000f * dtSum / Mathf.Max(1, dtN):F2} ms (mean of {dtN}); requests {s.used}, dynamic tiles {s.dynTiles}, atlas scale {s.scale:F3}, cached placed {s.placed} pending {s.pending}; consecutive frames: {changed} pixels differ (> 2/255 per channel)");
        var dir2 = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/views"));
        var fp = Path.Combine(dir2, (string)v["name"] + ".png"); Directory.CreateDirectory(Path.GetDirectoryName(fp)); File.WriteAllBytes(fp, tex.EncodeToPNG()); Object.DestroyImmediate(tex);
        view++;
        if (view < pviews.Count) { tick = f; Pose(); return; }
        var outp = SessionState.GetString("ShadowAuditOut", ""); if (outp != "") File.WriteAllText(outp, psb.ToString());
        Debug.Log(psb.ToString()); SessionState.EraseString("ShadowAuditPlay");
        EditorApplication.update -= PlayTick; EditorApplication.ExitPlaymode(); EditorApplication.delayCall += () => EditorApplication.Exit(0);
    }
    static void Pose()
    {
        Vector3 V(Newtonsoft.Json.Linq.JToken t) => new Vector3((float)t[0], (float)t[1], (float)t[2]);
        var v = pviews[view]; dtSum = 0f; dtN = 0;
        if (v["night"] != null) Object.FindAnyObjectByType<HouseNightMode>().SetNight((bool)v["night"]);   // per view: "night": false for a day shot
        pcam.transform.position = V(v["pos"]); pcam.transform.LookAt(V(v["look_at"])); pcam.fieldOfView = (float)v["vfov"];
    }
    static Color32[] Grab(out Texture2D tex)
    {
        RenderTexture.active = prt; tex = new Texture2D(prt.width, prt.height, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, prt.width, prt.height), 0, 0); tex.Apply(); RenderTexture.active = null; return tex.GetPixels32();
    }

    // walk-note poses (spec/feedback/feel-notes.jsonl: feet, yaw, pitch; eye = feet + 1.28) and the film night views
    static readonly (string name, Vector3 eye, float yaw, float pitch)[] Poses = {
        ("den plant 20:42", new Vector3(7.407f, -2.996f + 1.28f, -17.872f), 284.1f, 6.3f),
        ("living corner 20:41", new Vector3(4.891f, -2.996f + 1.28f, -13.316f), 300.7f, 4.2f),
        ("foyer 12:03", new Vector3(6.715f, -2.996f + 1.28f, -5.994f), 38.3f, 5.1f),
        ("foyer 11:43", new Vector3(8.958f, -2.996f + 1.28f, -5.540f), 336.1f, 5.9f),
        ("kitchen 15:06", new Vector3(-2.684f, -2.996f + 1.28f, -3.116f), 280.1f, 4.1f),
        ("upstairs landing 11:26", new Vector3(3.993f, 0.03f + 1.28f, -8.677f), 251f, 22.6f),
    };

    static object F(object o, string name)
    {
        for (var t = o.GetType(); t != null; t = t.BaseType)
        {
            var f = t.GetField(name, BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            if (f != null) return f.GetValue(o);
        }
        throw new System.MissingFieldException(o.GetType().Name, name);
    }
    static int Len(object nativeList) => (int)nativeList.GetType().GetProperty("Length").GetValue(nativeList);
    static int Count(object hashMap) => (int)hashMap.GetType().GetMethod("Count").Invoke(hashMap, null);

    // HDRP's shadow bookkeeping after the last rendered frame
    static (int used, int max, int dynTiles, float scale, int placed, int pending) Stats()
    {
        var sm = F(RenderPipelineManager.currentPipeline, "m_ShadowManager");
        var atlas = F(sm, "m_Atlas");
        var cached = F(HDCachedShadowManager.instance, "punctualShadowAtlas");
        return ((int)F(sm, "m_ShadowRequestCount"), (int)F(sm, "m_MaxShadowRequests"), Len(F(atlas, "m_ShadowResolutionRequests")),
                1f / (float)F(atlas, "m_RcpScaleFactor"), Count(F(cached, "m_PlacedShadows")), Count(F(cached, "m_RegisteredLightDataPendingPlacement")));
    }

    static string Path0(Transform t) => t.parent == null ? t.name : Path0(t.parent) + "/" + t.name;

    public static void Run()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity");
        bool legacy = System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-legacy") >= 0; if (legacy) Legacy();
        var sb = new StringBuilder($"SHADOW AUDIT (ShadowAudit.Run, House_WallGrid, night{(legacy ? ", -legacy: the lamps as before the cached-shadow pass" : "")})\n");
        var go = new GameObject("AuditCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f; cam.fieldOfView = 60f;
        var rt = new RenderTexture(960, 540, 24, RenderTextureFormat.ARGBHalf); cam.targetTexture = rt;
        cam.Render(); Object.FindFirstObjectByType<HouseNightMode>().SetNight(true);
        RenderPipelineManager.beginCameraRendering += (ctx, c) => { if (c == cam) ShadowRefresh.Warm(cam); };   // as HouseNightMode.Update does in Play
        {   // a fixed exposure, so frame-to-frame differences are the lighting's, not auto exposure adapting
            var prof = ScriptableObject.CreateInstance<VolumeProfile>(); var ex = prof.Add<Exposure>(true);
            ex.mode.value = ExposureMode.Fixed; ex.fixedExposure.value = 4f;
            var vol = new GameObject("AuditExposure").AddComponent<Volume>(); vol.isGlobal = true; vol.priority = 10000f; vol.sharedProfile = prof;
        }

        bool noFade = System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-noFade") >= 0;   // as before the 10 m stop-gap
        var lights = Object.FindObjectsByType<Light>(FindObjectsInactive.Include, FindObjectsSortMode.None).OrderBy(l => Path0(l.transform)).ToList();
        var lit = lights.Where(l => l.isActiveAndEnabled).ToList();
        var sh = lit.Where(l => l.shadows != LightShadows.None && l.lightmapBakeType != LightmapBakeType.Baked).ToList();
        if (noFade) foreach (var l in sh) l.GetComponent<HDAdditionalLightData>().shadowFadeDistance = 10000f;
        sb.AppendLine(noFade ? "(-noFade: every lamp's shadow fade distance set to 10000 m for this run)" : "");
        int Faces(Light l) => l.type == LightType.Point ? 6 : 1;
        sb.AppendLine($"lights: {lights.Count} in scene, {lit.Count} on at night, {sh.Count} real-time shadowed ({sh.Sum(Faces)} shadow maps: " +
                      string.Join(", ", sh.GroupBy(l => l.type).Select(g => $"{g.Count()} {g.Key}")) + ")");
        var ip = ((HDRenderPipelineAsset)GraphicsSettings.currentRenderPipeline).currentPlatformRenderPipelineSettings.hdShadowInitParams;
        sb.AppendLine($"HDRP: maxShadowRequests {ip.maxShadowRequests}, punctual atlas {ip.punctualLightShadowAtlas.shadowAtlasResolution} " +
                      $"(rescale {ip.punctualLightShadowAtlas.useDynamicViewportRescale}), cached punctual atlas {ip.cachedPunctualLightShadowAtlas}, area atlas {ip.areaLightShadowAtlas.shadowAtlasResolution}, cached area {ip.cachedAreaLightShadowAtlas}");
        long cachedTexels = 0;
        foreach (var l in sh)
        {
            var hd = l.GetComponent<HDAdditionalLightData>();
            var res = Mathf.Min(hd.shadowResolution.Value(ip.shadowResolutionPunctual), ip.maxPunctualShadowMapResolution);
            if (hd.shadowUpdateMode != ShadowUpdateMode.EveryFrame) cachedTexels += (long)Faces(l) * res * res;
            sb.AppendLine($"  {Path0(l.transform)}: {l.type}{(l.type == LightType.Spot ? $" {hd.spotLightShape} {l.spotAngle:F0}deg" : "")} range {l.range:F1} res {res} " +
                          $"{hd.shadowUpdateMode}{(hd.alwaysDrawDynamicShadows ? "+dynamic" : "")} fade {hd.shadowFadeDistance:F0} contact {hd.useContactShadow.@override}");
        }
        sb.AppendLine($"cached texels wanted {cachedTexels / 1e6:F1} M (punctual cached atlas holds {(long)ip.cachedPunctualLightShadowAtlas * ip.cachedPunctualLightShadowAtlas / 1e6:F1} M)");
        int dynCasters = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Count(r => r.enabled && r.shadowCastingMode != ShadowCastingMode.Off && !r.staticShadowCaster);
        sb.AppendLine($"dynamic shadow casters (not staticShadowCaster): {dynCasters}");

        int di = System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-dump"); string dumpDir = di >= 0 ? System.Environment.GetCommandLineArgs()[di + 1] : null;
        var px = new Texture2D(rt.width, rt.height, TextureFormat.RGBAHalf, false);
        Color[] Grab() { RenderTexture.active = rt; px.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); px.Apply(); RenderTexture.active = null; return px.GetPixels(); }
        foreach (var (name, eye, yaw, pitch) in Poses)
        {
            go.transform.SetPositionAndRotation(eye, Quaternion.Euler(pitch, yaw, 0));
            for (int i = 0; i < 6; i++) cam.Render();   // warm-up: cached maps place and render, history buffers fill
            var s = Stats();
            var planes = GeometryUtility.CalculateFrustumPlanes(cam);
            int wanted = sh.Where(l => GeometryUtility.TestPlanesAABB(planes, new Bounds(l.transform.position, Vector3.one * 2 * l.range))
                                       && Vector3.Distance(l.transform.position, eye) < l.GetComponent<HDAdditionalLightData>().shadowFadeDistance).Sum(Faces);
            sb.AppendLine($"{name}: requests {s.used}/{s.max} (visible lights want ~{wanted} + sun cascades), dynamic tiles {s.dynTiles}, atlas scale {s.scale:F3}, cached placed {s.placed} pending {s.pending}");
            // the pan: "when i pan left and right ... if i move slightly, they're lost"
            var scales = new List<float>(); var used = new List<int>();
            for (float d = -30; d <= 30.01f; d += 2)
            {
                go.transform.SetPositionAndRotation(eye + go.transform.right * (d * 0.0005f), Quaternion.Euler(pitch, yaw + d, 0));
                cam.Render(); var p = Stats(); scales.Add(p.scale); used.Add(p.used);
            }
            sb.AppendLine($"  pan +-30 deg: atlas scale {scales.Min():F3}..{scales.Max():F3}, requests {used.Min()}..{used.Max()}");
            // still frames
            go.transform.SetPositionAndRotation(eye, Quaternion.Euler(pitch, yaw, 0));
            for (int i = 0; i < 4; i++) cam.Render();
            Color[] prev = null; float worst = 0; int changed = 0; var t = Stopwatch.StartNew();
            for (int f = 0; f < 8; f++)
            {
                cam.Render(); var cur = Grab();
                if (prev != null)
                    for (int i = 0; i < cur.Length; i++)
                    {
                        float a = cur[i].grayscale, b = prev[i].grayscale, rel = Mathf.Abs(a - b) / Mathf.Max(Mathf.Max(a, b), 1e-3f);
                        if (rel > 0.01f) changed++;
                        worst = Mathf.Max(worst, rel);
                    }
                if (f == 7 && dumpDir != null)
                {   // the last two still frames and where they differ (white: >1%)
                    var m = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false); var mc = new Color[cur.Length];
                    for (int i = 0; i < cur.Length; i++) { float a = cur[i].grayscale, b = prev[i].grayscale; mc[i] = Mathf.Abs(a - b) / Mathf.Max(Mathf.Max(a, b), 1e-3f) > 0.01f ? Color.white : cur[i] * 0.3f; }
                    m.SetPixels(mc); m.Apply(); File.WriteAllBytes(Path.Combine(dumpDir, name.Replace(" ", "_").Replace(":", "") + "-diff.png"), m.EncodeToPNG());
                }
                prev = cur;
            }
            sb.AppendLine($"  8 still frames: max relative change {worst:F4}, pixels changed >1% {changed} (of {7 * rt.width * rt.height}); {t.Elapsed.TotalMilliseconds / 8:F1} ms/frame incl. readback");
        }
        {   // the cached atlas's placements after every pose: no two shadow maps may share texels
            var cached = F(HDCachedShadowManager.instance, "punctualShadowAtlas"); var map = F(cached, "m_PlacedShadows");
            var arr = (System.Collections.IEnumerable)map.GetType().GetMethod("GetValueArray").Invoke(map, new object[] { (Unity.Collections.AllocatorManager.AllocatorHandle)Unity.Collections.Allocator.Temp });
            var recs = new List<(int idx, Rect r)>();
            foreach (var rec in arr) { var o = (Vector4)F(rec, "offsetInAtlas"); int size = (int)F(rec, "viewportSize"); recs.Add(((int)F(rec, "shadowIndex"), new Rect(o.x, o.y, size, size))); }
            int overlaps = 0; for (int i = 0; i < recs.Count; i++) for (int j = i + 1; j < recs.Count; j++) if (recs[i].r.Overlaps(recs[j].r)) { if (overlaps < 10) sb.AppendLine($"  OVERLAP shadow {recs[i].idx} {recs[i].r} and {recs[j].idx} {recs[j].r}"); overlaps++; }
            float used = recs.Sum(q => q.r.width * q.r.height), max = recs.Count > 0 ? recs.Max(q => Mathf.Max(q.r.xMax, q.r.yMax)) : 0;
            sb.AppendLine($"cached atlas: {recs.Count} shadow maps placed, {used / 1e6:F1} M texels, furthest texel {max}, {overlaps} overlapping pairs");
        }
        RenderTexture.active = null; Object.DestroyImmediate(go); rt.Release();
        var outp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/shadow-audit.txt"));
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-auditOut") is int ai && ai >= 0) outp = System.Environment.GetCommandLineArgs()[ai + 1];
        File.WriteAllText(outp, sb.ToString());
        Debug.Log(sb.ToString());
    }

    // Night views for the before/after look (film_light_match.py), like SpecGreybox.RenderViews -night, plus "-legacy": the lamps as they
    // were before the cached-shadow pass (every frame, 512, 10 m fade, default near plane, the den banker a point, no contact shadows),
    // so before and after come from ONE build and one bake and differ only in the shadow setup. Batch only: cam.Render() bursts do not
    // advance frames, and cached shadow maps came out unlit or blotched here (Oct 16). Judge looks from PlayViews.
    //   Unity -batchmode ... -executeMethod ShadowAudit.Views -quit -views views-shadows-before.json [-legacy]
    public static void Views()
    {
        var a = System.Environment.GetCommandLineArgs(); int vi = System.Array.IndexOf(a, "-views");
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity");
        if (System.Array.IndexOf(a, "-legacy") >= 0) Legacy();
        var go = new GameObject("ViewCam"); var cam = go.AddComponent<Camera>(); go.AddComponent<HDAdditionalCameraData>(); cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt;
        cam.Render(); Object.FindFirstObjectByType<HouseNightMode>().SetNight(true);
        {   // as RenderViews: batch renders do not apply the baked room reflection probes, so the sky fallback is off
            var prof = ScriptableObject.CreateInstance<VolumeProfile>(); var ilc = prof.Add<IndirectLightingController>(true);
            ilc.reflectionLightingMultiplier.value = 0f;
            var vol = new GameObject("NoSkyReflect").AddComponent<Volume>(); vol.isGlobal = true; vol.priority = 10001f; vol.sharedProfile = prof;
        }
        var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/views"));
        foreach (var v in Newtonsoft.Json.Linq.JArray.Parse(File.ReadAllText(Path.Combine(dir, a[vi + 1]))))
        {
            Vector3 V(Newtonsoft.Json.Linq.JToken t) => new Vector3((float)t[0], (float)t[1], (float)t[2]);
            go.transform.position = V(v["pos"]); go.transform.LookAt(V(v["look_at"])); cam.fieldOfView = (float)v["vfov"];
            for (int i = 0; i < 4; i++) { ShadowRefresh.Warm(cam); cam.Render(); }   // as HouseNightMode.Update does in Play
            RenderTexture.active = rt; var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); tex.Apply(); RenderTexture.active = null;
            var fp = Path.Combine(dir, (string)v["name"] + ".png"); Directory.CreateDirectory(Path.GetDirectoryName(fp));
            File.WriteAllBytes(fp, tex.EncodeToPNG()); Object.DestroyImmediate(tex);
        }
        Object.DestroyImmediate(go); rt.Release();
    }

    static void Legacy()
    {
        var args = System.Environment.GetCommandLineArgs(); int oi = System.Array.IndexOf(args, "-only"); string only = oi >= 0 ? args[oi + 1] : null;
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Include, FindObjectsSortMode.None))
        {
            var hd = l.GetComponent<HDAdditionalLightData>(); if (hd == null) continue;
            if (only != null && l.name != only) continue;
            hd.useContactShadow.useOverride = true; hd.useContactShadow.@override = false;
            if (l.type == LightType.Directional || l.shadows == LightShadows.None || l.lightmapBakeType == LightmapBakeType.Baked) continue;
            hd.shadowUpdateMode = ShadowUpdateMode.EveryFrame; hd.SetShadowResolutionOverride(true); hd.SetShadowResolution(512);
            hd.shadowFadeDistance = 10f; hd.shadowNearPlane = 0.1f;
            if (l.name == "DenLamp_desk" && l.type == LightType.Spot) { l.type = LightType.Point; l.transform.position -= Vector3.up * 0.03f; }
        }
        Debug.Log("ShadowAudit: legacy shadow setup");
    }
}
