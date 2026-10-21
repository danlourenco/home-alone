using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Unity.Profiling;
using Unity.Profiling.LowLevel.Unsafe;   // ProfilerRecorderHandle: markers by name
using UnityEngine;
using HDCam = UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData;

// Perf probe: frame time and render counters at the player's current view, over N frames, camera untouched.
//   PerfProbe.Run("name", 300)  -> spec/captures/perf/name.json
// Reports median / p95 / p99 frame time (CPU wall), GPU frame time when the platform reports it, and the median of the render
// counters (batches, set-pass calls, triangles, shadow casters). Started from the unity CLI (eval) during Play. In the editor the
// numbers include editor overhead and depend on the Game view size; compare runs with each other, not with a shipped build.
//
// Standalone tour (tools/house/perf_probe.sh): a player started with  -perfprobe <outdir>  disables the walk controller, visits the
// fixed POSES below, day and night, and per pose writes <outdir>/<pose>-<day|night>.json + .png, then quits. Same poses every run,
// so before/after tables compare like with like. Poses are camera position + yaw/pitch (pitch + = down), world metres.
public class PerfProbe : MonoBehaviour
{
    public static string Last = "";
    static string injectNow = "asset";
    static readonly HashSet<string> MARKERS = new HashSet<string> { "RenderShadowMaps", "BlitPunctualMixedCachedShadowMaps", "BlitDirectionalMixedCachedShadowMaps",
        "UpdateReflectionProbeAtlas", "ConvolveReflectionProbe", "ConvolvePlanarReflectionProbe", "ConvertReflectionProbe", "APVCellStreamingUpdate",
        "APVDiskStreamingUpdate", "APVScenarioBlendingUpdate", "APVIndexDefragUpdate", "GC.Collect", "Gfx.WaitForPresentOnGfxThread", "Shader.CreateGPUProgram" };
    static readonly (string name, Vector3 pos, float yaw, float pitch)[] POSES =
    {
        ("street", new Vector3(34f, -2.7f, -9.7f), 270f, -7f),        // looking at the front (8, 0.5, -9.7)
        ("foyer", new Vector3(8.4f, -1.716f, -9.4f), 268f, 0f),        // flicker-test pose (feet -2.996, eye +1.28)
        ("living", new Vector3(6.5f, -1.72f, -13.8f), 180f, 0f),       // nightcheck pose, the tree in view
        ("hall", new Vector3(6.893f, 1.31f, -9.487f), 188f, 0f),       // upstairs hall arch (walk note pose)
        ("attic", new Vector3(6.556f, 3.93f, -16.95f), 351f, 0f),      // stair head facing the bed
        ("yard", new Vector3(-4f, -2.1f, -12f), 288f, -10f),           // rear yard looking at the treehouse (-12.1, -9.3)
        ("parents", new Vector3(6.745f, 1.16f, -2.895f), 276f, -14.6f), // parents' room, the bedside lamps (walk note 21:16 pose; PCSS check)
        // Oct 20 (hall bath sconces, Buzz's lamps): -perfposes hallbath,hallbathdoor,buzz
        ("hallbath", new Vector3(8.7f, 1.31f, -10.6f), 106f, -8f),       // hall bath, just inside its door, facing the sconce over the sink (film 336)
        ("hallbathdoor", new Vector3(6.4f, 1.31f, -10.6f), 90f, 0f),     // the hall outside the bath door, looking in
        ("buzz", new Vector3(7.9f, 1.31f, -11.95f), 145f, 8f),           // Buzz's room from his door, toward the windows and the bed
        // Oct 20 (night white balance, tools/house/night_wb.py): -perfposes hallbath,buzz,foyer,living,parents,kitchen,dining,street
        ("kitchen", new Vector3(-3.4f, -1.426f, -0.9f), 115.7f, 2.8f),    // the kitchen toward the sconces and the breakfast table (film 1051/1151's side)
        ("dining", new Vector3(7.5f, -1.5f, -8.7f), 357.2f, 12.4f),       // the dining room from the foyer doorway, the table and the French doors (film 251)
        // Oct 20 (house split, walk note 20:56): -perfposes parentsdoor,street -perfvariants "split=rooms;weather=overcast;..."
        ("parentsdoor", new Vector3(6.16f, 1.31f, -5.40f), 0f, -12f),    // in the parents' bedroom doorway (hall_end side, mid-wall), looking in
        // Oct 20 (neighbourhood, SpecGreybox.Neighborhood.cs): -perfposes piers,murphys,upwindow,street (+ -perfvariants nbold for the old exterior)
        ("piers", new Vector3(29.0f, -2.58f, -9.716f), 125f, 2f),
        ("walk0645", new Vector3(32.128f, -3.182f, -9.659f), 267.3f, -1.1f), // walk note 2026-10-21T06:45:32 (Kevin's eye at the piers, facing the house): mailbox, lanterns, brick, protruding upstairs        // between our walk piers on the sidewalk, across and down Lincoln (film-left)
        ("murphys", new Vector3(28.68f, -2.63f, -21.96f), 67f, -1.5f),   // film 11581's solved camera (nb_film_camera.py; the player's FOV, not the film's 24.8 deg)
        ("upwindow", new Vector3(9.6f, 1.31f, -9.716f), 90f, 4f),        // upstairs over the front door, out the front window to the Murphys
        ("van", new Vector3(37.5f, -2.7f, -33.5f), 322.5f, 2f),          // across Lincoln toward the bandits' van by our lamp post (film 3297's side; night)
    };

    // nbold (a -perfvariants key): the exterior before the neighbourhood: its root off, the WinterNeighborhood renderers it switched off
    // (named "... [nb-off]") back on, the photo domes back at R 75 (scaled from R 320). Not exact: the old sphere-globe lamp posts are gone
    // and the renderers the R 75 dome used to disable stay enabled (behind the dome: drawn, unseen), so "old" costs a little more than it did
    static List<Renderer> nbOff; static GameObject nbRoot;
    static void NbOld(bool old)
    {
        if (nbOff == null)
        {
            nbOff = Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include).Where(r => r.name.EndsWith("[nb-off]")).ToList();
            nbRoot = Object.FindObjectsByType<Transform>(FindObjectsInactive.Include).FirstOrDefault(t => t.name == "Neighborhood")?.gameObject;
        }
        if (nbRoot == null) return;
        nbRoot.SetActive(!old); foreach (var r in nbOff) if (r) r.enabled = old;
        foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include).Where(t => t.name == "WinterBackdrop_Day" || t.name == "WinterBackdrop_Night"))
            t.localScale = Vector3.one * (old ? 75f / 320f : 1f);
    }

    // APV leak tuning (walk note 2026-10-21T06:45:32, the grey-violet centre brick: the APV leaks dark, cool light onto the facade):
    // apvnb=F normal bias, apvvb=F view bias, apvleak=none|perf|quality, apvnoise=F sampling noise,
    // apvscale=1 scale the biases with the min probe distance. Applied to every global volume's ProbeVolumesOptions (the build's own
    // values restored for the base)
    static readonly Dictionary<UnityEngine.Rendering.ProbeVolumesOptions, (float nb, float vb, UnityEngine.Rendering.APVLeakReductionMode lr, float noise, bool sc)> apv0 = new();
    static void ApvOptions(System.Func<string, string> S)
    {
        float P(string v) => float.Parse(v, System.Globalization.CultureInfo.InvariantCulture);
        foreach (var vol in Object.FindObjectsByType<UnityEngine.Rendering.Volume>(FindObjectsInactive.Include))
        {
            var prof = vol.sharedProfile; if (prof == null || !prof.TryGet<UnityEngine.Rendering.ProbeVolumesOptions>(out var o)) continue;
            if (!apv0.ContainsKey(o)) apv0[o] = (o.normalBias.value, o.viewBias.value, o.leakReductionMode.value, o.samplingNoise.value, o.scaleBiasWithMinProbeDistance.value);
            var b = apv0[o];
            o.normalBias.Override(S("apvnb") is string a1 ? P(a1) : b.nb); o.viewBias.Override(S("apvvb") is string a2 ? P(a2) : b.vb);
            o.leakReductionMode.Override(S("apvleak") switch { "none" => UnityEngine.Rendering.APVLeakReductionMode.None, "perf" => UnityEngine.Rendering.APVLeakReductionMode.Performance, "quality" => UnityEngine.Rendering.APVLeakReductionMode.Quality, _ => b.lr });
            o.samplingNoise.Override(S("apvnoise") is string a4 ? P(a4) : b.noise);
            o.scaleBiasWithMinProbeDistance.Override(S("apvscale") is string a5 ? a5 == "1" : b.sc);
        }
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void AutoTour()
    {
        var a = System.Environment.GetCommandLineArgs(); int i = System.Array.IndexOf(a, "-perfprobe");
        if (i < 0 || i + 1 >= a.Length || Application.isEditor) return;
        var g = new GameObject("PerfProbeTour"); DontDestroyOnLoad(g); var p = g.AddComponent<PerfProbe>(); p.StartCoroutine(p.Tour(a[i + 1]));
    }

    static string Arg0(string k) { var a = System.Environment.GetCommandLineArgs(); int i = System.Array.IndexOf(a, k); return i >= 0 && i + 1 < a.Length ? a[i + 1] : null; }

    IEnumerator Tour(string dir)
    {
        Directory.CreateDirectory(dir);
        QualitySettings.vSyncCount = 0; Application.targetFrameRate = -1;
        yield return new WaitForSeconds(3f);   // let the scene settle (APV streaming, shaders)
        // -perfdisplay NAME (perf_probe.sh HA_DISPLAY): full screen on that display (DisplayInfo name, e.g. "Studio Display") at the size
        // given by -screen-width/-height (the display's native pixels, detected by perf_probe.sh). display.txt records what the player got
        if (Arg0("-perfdisplay") is string dispName)
        {
            var layout = new List<DisplayInfo>(); Screen.GetDisplayLayout(layout);
            var di = layout.FirstOrDefault(x => x.name.Contains(dispName));
            if (di.name != null) { yield return Screen.MoveMainWindowTo(in di, Vector2Int.zero); yield return new WaitForSeconds(1f); }
            int sw = int.Parse(Arg0("-screen-width") ?? di.width.ToString()), sh = int.Parse(Arg0("-screen-height") ?? di.height.ToString());
            Screen.SetResolution(sw, sh, FullScreenMode.FullScreenWindow); yield return new WaitForSeconds(3f);
            File.WriteAllText(Path.Combine(dir, "display.txt"), $"requested {dispName} {sw}x{sh}\nlayout: " + string.Join("; ", layout.Select(x => $"{x.name} {x.width}x{x.height} @{x.refreshRate.value:F0}Hz"))
                + $"\nmatched: {di.name}\nScreen {Screen.width}x{Screen.height} mode {Screen.fullScreenMode} currentResolution {Screen.currentResolution.width}x{Screen.currentResolution.height}"
                + $"\nDisplay.main system {Display.main.systemWidth}x{Display.main.systemHeight} rendering {Display.main.renderingWidth}x{Display.main.renderingHeight} dpi {Screen.dpi:F0}\n");
        }
        var fps = FindFirstObjectByType<FpsController>(); var night = FindFirstObjectByType<HouseNightMode>(); var weather = FindAnyObjectByType<HouseWeather>();
        if (fps) { fps.enabled = false; var cc = fps.GetComponent<CharacterController>(); if (cc) cc.enabled = false; }
        var cam = Camera.main.transform;
        // The VARIANT (what the run tests), from the command line:
        //   -perfoff A,B,...  HDRP frame settings off on the camera (FrameSettingsField names: ShadowMaps, ContactShadows, SSAO, Volumetrics...)
        // (Pipeline-asset settings such as the GPU Resident Drawer cannot be switched in a running player: the setter re-creates HDRP,
        // which fails. Compare those with two builds run alternately: tools/house/perf_probe.sh ab.)
        // -perfab: every pose is sampled base, variant, base, variant (tags -A1 -B1 -A2 -B2) in the same session, so another GPU client
        // (the editor in Play) loads both sides alike; without it the whole run is the variant.
        var args = System.Environment.GetCommandLineArgs();
        string Arg(string k) { int i = System.Array.IndexOf(args, k); return i >= 0 && i + 1 < args.Length ? args[i + 1] : null; }
        var hd = Camera.main.GetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData>();
        var off = (Arg("-perfoff") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries)
            .Select(f => (UnityEngine.Rendering.HighDefinition.FrameSettingsField)System.Enum.Parse(typeof(UnityEngine.Rendering.HighDefinition.FrameSettingsField), f)).ToList();
        //   -perflightsoff P1,P2  real-time lights whose name starts with a prefix switched off ("what do these lamps cost")
        //   -perfrange F          every real-time punctual light's range times F ("what would tighter ranges save")
        bool ab = System.Array.IndexOf(args, "-perfab") >= 0;
        var prefixes = (Arg("-perflightsoff") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);
        float rangeK = float.Parse(Arg("-perfrange") ?? "1", System.Globalization.CultureInfo.InvariantCulture);
        var lamps = FindObjectsByType<Light>(FindObjectsInactive.Include).Where(l => l.type != LightType.Directional && !(l.bakingOutput.isBaked && l.bakingOutput.lightmapBakeType == LightmapBakeType.Baked))   // lightmapBakeType is editor-only
            .Select(l => (l, l.range)).ToList();
        //   -perfpcss B,F         every lamp's PCSS blocker/filter sample counts in the variant (HDRP default 24,16; punctual filtering High)
        //   -perfnoshadow P1,P2   real-time lights whose name starts with a prefix lose their shadows in the variant
        var pcss = (Arg("-perfpcss") ?? "").Split(',').Where(v => v.Length > 0).Select(int.Parse).ToArray();
        var noShadow = (Arg("-perfnoshadow") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);
        var lampHd = lamps.Select(x => (x.l, hd: x.l.GetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalLightData>(), x.l.shadows)).Where(x => x.hd != null)
            .Select(x => (x.l, x.hd, x.shadows, b: x.hd.blockerSampleCount, f: x.hd.filterSampleCount)).ToList();
        //   -perfmirror B[,V]     the foyer mirror's planar resolution: B in the base, V in the variant (e.g. 512,1024 with -perfab)
        var mirrorRes = (Arg("-perfmirror") ?? "").Split(',').Where(v => v.Length > 0).Select(int.Parse).ToArray();
        var mirror = FindObjectsByType<UnityEngine.Rendering.HighDefinition.PlanarReflectionProbe>().FirstOrDefault(m => m.name == "FoyerMirrorProbe");
        //   -perfshadowlegacy     the variant redraws lamp shadow maps the pre-Oct 20 way (every lamp in range, every frame of a motion)
        //   -perfshadowq M,I      the variant's ShadowRefresh throttle: M lamps per frame, each once per I frames
        bool legacyShadows = System.Array.IndexOf(args, "-perfshadowlegacy") >= 0;
        var shq = (Arg("-perfshadowq") ?? "").Split(',').Where(v => v.Length > 0).Select(int.Parse).ToArray();
        int shq0 = ShadowRefresh.MaxPerFrame, shq1 = ShadowRefresh.Interval;
        var only = (Arg("-perfposes") ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);   // -perfposes foyer,hall,street-day: just those (a pose, or one of its day/night)
        var switchedOff = new Dictionary<Light, bool>();   // lamp -> its state before the variant (night mode switches lamps too)
        //   -perfvariants "sundist=80;sundist=60 splits=0.05,0.15,0.3;nocast=props"   several variants B, C, D ... (with -perfab: every pose
        //                         sampled A1 B1 C1 .. A2 B2 C2 ..). Keys: sundist=M (sun shadow max distance), splits=a,b,c (cascade
        //                         splits), cascades=N, nocast=props|interior|exterior (those renderers stop casting shadows: an
        //                         attribution of the day shadow cost, not a look), wb=T (night interior white balance, base 0), scale=P (render
        //                         scale %, auto or adaptive; STP; base -perfbasescale, default 100 = native), inject=before|dof|after (STP's
        //                         injection point), screen=WxH (backbuffer size, e.g. 2560x1440 full screen on the 5K display).
        //                         Phase B: hide=T1,T2 (renderers with those materials off), lowres=T1,T2|all (low-res transparent pass),
        //                         fit=M (lamp range = room extent + M m). Keys of one variant: space or '+' separated.
        //                         Without it the knobs above are the one variant B.
        //   -perfdn day|night     just day or night
        var variants = (Arg("-perfvariants") ?? "").Trim('"', '\'').Split(new[] { ';' }, System.StringSplitOptions.RemoveEmptyEntries)
            .Select(v => v.Split(new[] { ' ', '+' }, System.StringSplitOptions.RemoveEmptyEntries).Select(kv => kv.Split('=')).ToDictionary(kv => kv[0], kv => kv.Length > 1 ? kv[1] : "")).ToList();   // '+' joins keys too (perf_probe.sh word-splits HA_PERF_ARGS)
        int nVar = Mathf.Max(variants.Count, 1);
        int rounds = int.Parse(Arg("-perfrounds") ?? "2");   // -perfrounds 1: each variant sampled once per pose (shorter A/B tours)
        var steps = ab ? Enumerable.Range(0, rounds).SelectMany(r => Enumerable.Range(0, nVar + 1).Select(v => (char)('A' + v) + (r + 1).ToString())).ToArray() : new[] { "" };
        var dnArg = Arg("-perfdn");
        var shadowVol = new GameObject("PerfShadowVolume").AddComponent<UnityEngine.Rendering.Volume>(); shadowVol.isGlobal = true; shadowVol.priority = 100000f;
        var shadowProf = ScriptableObject.CreateInstance<UnityEngine.Rendering.VolumeProfile>(); shadowVol.sharedProfile = shadowProf;
        var shadowSet = shadowProf.Add<UnityEngine.Rendering.HighDefinition.HDShadowSettings>(false);
        var casters = FindObjectsByType<Renderer>(FindObjectsInactive.Include).Where(r => r.shadowCastingMode != UnityEngine.Rendering.ShadowCastingMode.Off).Select(r => (r, r.shadowCastingMode)).ToList();
        string Group(Renderer r)
        {
            var t = r.transform; string root = t.root.name; bool skin = false;
            for (var q = t; q; q = q.parent) if (q.name == "HouseShell" || q.name.StartsWith("Exterior")) skin = true;
            if (root == "Exterior" || skin) return "exterior";
            if (r.shadowCastingMode == UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly) return "envelope";
            return r.bounds.size.x < 1.5f && r.bounds.size.y < 1.5f && r.bounds.size.z < 1.5f ? "props" : "interior";
        }
        var casterGroup = casters.Select(c => Group(c.r)).ToList();
        var offUsed = new Dictionary<UnityEngine.Rendering.HighDefinition.FrameSettingsField, (bool on, bool masked)>(); bool customRendering0 = hd != null && hd.customRenderingSettings;
        var link0 = lampHd.ToDictionary(x => x.hd, x => x.hd.linkShadowLayers); var mask0 = lampHd.ToDictionary(x => x.l, x => x.l.renderingLayerMask); bool zonesWereOff = false;
        var hidden = new Dictionary<Renderer, bool>(); var queue0 = new Dictionary<Material, int>(); var extent = new Dictionary<Light, float>();
        float RoomExtent(Light l)
        {
            if (extent.TryGetValue(l, out var e)) return e;
            var d = new List<float>(); var o = l.transform.position;
            for (int k = 0; k < 128; k++)   // Fibonacci sphere
            {
                float y = 1f - 2f * (k + 0.5f) / 128f, rr = Mathf.Sqrt(1f - y * y), ph = k * 2.39996323f;
                d.Add(Physics.Raycast(o, new Vector3(Mathf.Cos(ph) * rr, y, Mathf.Sin(ph) * rr), out var h, l.range, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore) ? h.distance : l.range);
            }
            d.Sort(); return extent[l] = d[(int)(0.9f * (d.Count - 1))];
        }
        (HDCam.AntialiasingMode, HDCam.TAAQualityLevel, HDCam.TAASharpenMode, float, HDCam.SMAAQualityLevel)? aa0 = null;
        string baseScale = Arg("-perfbasescale") ?? "100";   // -perfbasescale auto: the base is the shipped AUTO scale (Phase A, Oct 20)
        var screen0 = new Vector2Int(Screen.width, Screen.height); var mode0 = Screen.fullScreenMode;
        void Apply(int v) => ApplyV(v > 0, v > 0 && variants.Count > 0 ? variants[v - 1] : null);
        void ApplyV(bool variant, Dictionary<string, string> spec)
        {
            float F(string k) => float.Parse(spec[k], System.Globalization.CultureInfo.InvariantCulture);
            NbOld(variant && spec != null && spec.ContainsKey("nbold"));
            VehicleProbe.Apply(variant ? spec : null);   // police=nowash|noglass|nolamps|nobloom|nofog|fix, bloomthr=T (VehicleProbe.cs)
            shadowSet.maxShadowDistance.overrideState = spec != null && spec.ContainsKey("sundist"); if (shadowSet.maxShadowDistance.overrideState) shadowSet.maxShadowDistance.value = F("sundist");
            shadowSet.cascadeShadowSplitCount.overrideState = spec != null && spec.ContainsKey("cascades"); if (shadowSet.cascadeShadowSplitCount.overrideState) shadowSet.cascadeShadowSplitCount.value = (int)F("cascades");
            var sp = spec != null && spec.ContainsKey("splits") ? spec["splits"].Split(',').Select(x => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture)).ToArray() : new float[0];
            var split = new[] { shadowSet.cascadeShadowSplit0, shadowSet.cascadeShadowSplit1, shadowSet.cascadeShadowSplit2 };
            for (int k = 0; k < 3; k++) { split[k].overrideState = k < sp.Length; if (k < sp.Length) split[k].value = sp[k]; }
            var nocast = spec != null && spec.ContainsKey("nocast") ? spec["nocast"].Split(',') : new string[0];
            for (int k = 0; k < casters.Count; k++) if (casters[k].r) casters[k].r.shadowCastingMode = nocast.Contains(casterGroup[k]) ? UnityEngine.Rendering.ShadowCastingMode.Off : casters[k].shadowCastingMode;
            // a -perfvariants variant takes its knobs from its own keys: range=F lightsoff=P1,P2 noshadow=P1,P2 off=SSAO,Volumetrics
            // shadowq=M,I legacyshadows pcss=B,F mirror=RES; otherwise the command-line knobs above are the variant
            string S(string k) => spec != null && spec.TryGetValue(k, out var v) ? v : null;
            string[] L(string k, string[] dflt) => spec == null ? dflt : (S(k) ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);
            int[] I(string k, int[] dflt) => spec == null ? dflt : L(k, null).Select(int.Parse).ToArray();
            // wb=T: the night interior white balance (HouseNightMode.SetWhiteBalance, not saved); when any variant sets it the base is 0
            if (variants.Any(v => v.ContainsKey("wb"))) HouseNightMode.SetWhiteBalance(S("wb") is string wbs ? float.Parse(wbs, System.Globalization.CultureInfo.InvariantCulture) : 0f, false);
            // weather=sunny|morning|overcast (HouseWeather, O; the base is sunny when any variant sets it); split=rooms: HouseSplit's
            // rooms-only test (before Oct 20); apv=upstairs: the upstairs bake everywhere (before Oct 20: the strip's light on the facade)
            if (weather && variants.Any(v => v.ContainsKey("weather")))
                weather.Apply(S("weather") switch { "overcast" => HouseWeather.State.Overcast, "morning" => HouseWeather.State.Morning, _ => HouseWeather.State.Sunny });
            HouseSplit.LegacyRoomsOnly = S("split") == "rooms"; HouseSplit.ForceUpstairsBake = S("apv") == "upstairs";
            HouseSplit.ApplyScenario(night && night.night);
            ApvOptions(S);
            float rk = spec == null ? rangeK : S("range") is string rs ? float.Parse(rs, System.Globalization.CultureInfo.InvariantCulture) : 1f;
            var ns = L("noshadow", noShadow); var pf = L("lightsoff", prefixes); var pc = I("pcss", pcss); var q = I("shadowq", shq);
            var mr = spec == null ? mirrorRes : S("mirror") is string m ? new[] { mirrorRes.Length > 0 ? mirrorRes[0] : int.Parse(m), int.Parse(m) } : mirrorRes.Take(1).ToArray();
            var offV = spec == null ? off : L("off", null).Select(f => (UnityEngine.Rendering.HighDefinition.FrameSettingsField)System.Enum.Parse(typeof(UnityEngine.Rendering.HighDefinition.FrameSettingsField), f)).ToList();
            foreach (var (l, range) in lamps) l.range = variant ? range * rk : range;
            // fit=M (Phase B, lamp ranges per room): each lamp's range = its room's extent + M metres (the doorway margin), never above
            // its own range. Room extent = the 90th percentile of 128 rays' hit distances against the colliders (walls, floors, ceilings;
            // the rays that escape through doorways are the top 10%). A runtime stand-in for room bounds: measure first, then write the pick
            if (S("fit") is string fs) { float fm = float.Parse(fs, System.Globalization.CultureInfo.InvariantCulture); foreach (var (l, range) in lamps) l.range = Mathf.Min(l.range, RoomExtent(l) + fm); }
            // hide=T1,T2: renderers with a material whose name contains a token are switched off (what those transparents cost, an upper
            // bound, not a look); lowres=T1,T2|all: transparent materials whose name contains a token draw in HDRP's low-resolution
            // transparent pass (quarter pixels, depth-aware upsample: each lamp is evaluated for a quarter of the pixels). Restored in the base
            foreach (var kv in hidden) kv.Key.enabled = kv.Value; hidden.Clear();
            foreach (var kv in queue0) kv.Key.renderQueue = kv.Value; queue0.Clear();
            var hideT = L("hide", new string[0]); var lowT = L("lowres", new string[0]);
            if (hideT.Length + lowT.Length > 0)
                foreach (var r in FindObjectsByType<Renderer>(FindObjectsInactive.Include))
                    foreach (var mt in r.sharedMaterials)
                    {
                        if (!mt) continue;
                        if (hideT.Any(t => mt.name.Contains(t)) && !hidden.ContainsKey(r)) { hidden[r] = r.enabled; r.enabled = false; }
                        if (mt.renderQueue > 2500 && (lowT.Contains("all") || lowT.Any(t => mt.name.Contains(t))) && !queue0.ContainsKey(mt))
                        { queue0[mt] = mt.renderQueue; UnityEngine.Rendering.HighDefinition.HDMaterial.SetRenderingPass(mt, UnityEngine.Rendering.HighDefinition.HDMaterial.RenderingPass.LowResolution); }
                    }
            foreach (var (l, lhd, sh, b, f) in lampHd)
            {
                if (pc.Length == 2 || pcss.Length == 2) { lhd.blockerSampleCount = variant && pc.Length == 2 ? pc[0] : b; lhd.filterSampleCount = variant && pc.Length == 2 ? pc[1] : f; }
                l.shadows = variant && ns.Any(p => l.name.StartsWith(p)) ? LightShadows.None : sh;
            }
            if (mirror && mr.Length > 0)
                mirror.settingsRaw.resolutionScalable.@override = (UnityEngine.Rendering.HighDefinition.PlanarReflectionAtlasResolution)(variant && mr.Length > 1 ? mr[1] : mr[0]);
            // scale=P (alias res=P): full screen backbuffer at P% of the display (RenderScale, Oct 21; no dynamic resolution); P = auto | a percent.
            // The tour never uses the player's saved scale (PlayerPrefs): the base is -perfbasescale (default 100 = native, no STP)
            float Pct(string v) => v == "auto" ? 0f : float.Parse(v, System.Globalization.CultureInfo.InvariantCulture);
            RenderScale.Set(Pct(spec != null && (S("scale") ?? S("res")) is string rp ? rp : baseScale), false);
            // inject=before|dof|after: STP's injection point (HDRP.asset: before = post at the output size); the base is the asset's
            // dynres=soft|hard: software / hardware dynamic resolution; upscaler=none: no STP (CatmullRom). Base: the asset's
            injectNow = RenderScale.DynRes(S("inject") switch { "after" => UnityEngine.Rendering.DynamicResolutionHandler.UpsamplerScheduleType.AfterPost, "dof" => UnityEngine.Rendering.DynamicResolutionHandler.UpsamplerScheduleType.AfterDepthOfField,
                "before" => UnityEngine.Rendering.DynamicResolutionHandler.UpsamplerScheduleType.BeforePost, _ => (UnityEngine.Rendering.DynamicResolutionHandler.UpsamplerScheduleType?)null },
                S("dynres") switch { "soft" => UnityEngine.Rendering.DynamicResolutionType.Software, "hard" => UnityEngine.Rendering.DynamicResolutionType.Hardware, _ => (UnityEngine.Rendering.DynamicResolutionType?)null },
                S("upscaler") == "none" ? false : (bool?)null, S("aa") == "stp" ? 100f : (float?)null);
            // aa=none|fxaa|smaa|taa|stp (Oct 21, "still some stair stepping"): the main camera's anti-aliasing; taa = High quality, post
            // sharpen 0.5; smaa = High; stp = STP at a forced 100% (pure temporal AA, no upscale). Base: the camera's own (None)
            if (hd != null)
            {
                aa0 ??= (hd.antialiasing, hd.TAAQuality, hd.taaSharpenMode, hd.taaSharpenStrength, hd.SMAAQuality); var ab0 = aa0.Value; var aa = S("aa");
                hd.antialiasing = aa switch { "none" => HDCam.AntialiasingMode.None, "fxaa" => HDCam.AntialiasingMode.FastApproximateAntialiasing, "smaa" => HDCam.AntialiasingMode.SubpixelMorphologicalAntiAliasing,
                    "taa" => HDCam.AntialiasingMode.TemporalAntialiasing, _ => ab0.Item1 };
                hd.TAAQuality = aa == "taa" ? HDCam.TAAQualityLevel.High : ab0.Item2; hd.taaSharpenMode = aa == "taa" ? HDCam.TAASharpenMode.PostSharpen : ab0.Item3;
                hd.taaSharpenStrength = aa == "taa" ? 0.5f : ab0.Item4; hd.SMAAQuality = aa == "smaa" ? HDCam.SMAAQualityLevel.High : ab0.Item5;
                RenderScale.Stp = aa == "stp";
            }
            // screen=WxH: the backbuffer (full screen: the OS / Unity scale it to the panel, e.g. 2560x1440 = the Studio Display's "looks
            // like" size); the base is the size the tour started at. The JSON records what the player got (screen, backbuffer)
            // screen=WxHw (trailing w): windowed at that size on the same display (the NB4-style 1920x1080 window)
            var scr = S("screen") ?? $"{screen0.x}x{screen0.y}"; var mode = scr.EndsWith("w") ? FullScreenMode.Windowed : mode0;
            var wh = scr.TrimEnd('w').Split('x').Select(int.Parse).ToArray();
            RenderScale.Manual = S("screen") != null;   // otherwise RenderScale sets the backbuffer (the shipped behaviour)
            if (RenderScale.Manual && (Screen.width != wh[0] || Screen.height != wh[1] || Screen.fullScreenMode != mode)) Screen.SetResolution(wh[0], wh[1], mode);
            // sunless=on: the never-sunlit pieces (SpecGreybox.SunCull) cast into the sun's cascades again by day
            if (night && !night.night)
                for (int k = 0; k < night.sunlessCasters.Length && k < night.sunlessModes.Length; k++)
                    if (night.sunlessCasters[k]) night.sunlessCasters[k].shadowCastingMode = variant && spec != null && spec.ContainsKey("sunless") ? night.sunlessModes[k] : UnityEngine.Rendering.ShadowCastingMode.Off;
            // lampzones=off: the lamps cast every caster in range again (SpecGreybox.LampZones gave each lamp its zone's casters only)
            bool zonesOff = variant && spec != null && spec.ContainsKey("lampzones");
            if (zonesOff != zonesWereOff)
            {
                // the shadow mask itself: toggling linkShadowLayers alone at run time left the zone mask in force (motion-zones, Oct 20)
                foreach (var (l, lhd, _, _, _) in lampHd) if (!link0[lhd]) l.renderingLayerMask = zonesOff ? 1 : mask0[l];
                ShadowRefresh.Forget(); zonesWereOff = zonesOff;   // every lamp redrawn when next in view (night: HouseNightMode -> Warm)
            }
            ShadowRefresh.Legacy = variant && (spec == null ? legacyShadows : spec.ContainsKey("legacyshadows"));
            ShadowRefresh.MaxPerFrame = variant && q.Length == 2 ? q[0] : shq0; ShadowRefresh.Interval = variant && q.Length == 2 ? q[1] : shq1;
            foreach (var kv in switchedOff) kv.Key.enabled = kv.Value; switchedOff.Clear();
            if (variant) foreach (var (l, _) in lamps) if (pf.Any(p => l.name.StartsWith(p))) { switchedOff[l] = l.enabled; l.enabled = false; }
            if (hd != null)
            {
                foreach (var kv in offUsed) { hd.renderingPathCustomFrameSettings.SetEnabled(kv.Key, kv.Value.on); hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)kv.Key] = kv.Value.masked; }
                if (offUsed.Count > 0 || offV.Count > 0) hd.customRenderingSettings = customRendering0 || (variant && offV.Count > 0);
                foreach (var f in offV)
                {
                    if (!offUsed.ContainsKey(f)) offUsed[f] = (hd.renderingPathCustomFrameSettings.IsEnabled(f), hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)f]);
                    if (variant) { hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)f] = true; hd.renderingPathCustomFrameSettings.SetEnabled(f, false); }
                }
            }
        }
        //   -perfextraposes "name:x,y,z,yaw,pitch;..."   camera poses added to the tour (walk-note poses; the eye, not the feet)
        var poses = POSES.ToList();
        foreach (var ep in (Arg("-perfextraposes") ?? "").Split(new[] { ';' }, System.StringSplitOptions.RemoveEmptyEntries))
        {
            var kv = ep.Split(':'); var n = kv[1].Split(',').Select(x => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture)).ToArray();
            poses.Add((kv[0], new Vector3(n[0], n[1], n[2]), n[3], n[4]));
        }
        foreach (var dn in new[] { false, true })
        {
            if (dnArg != null && (dnArg == "night") != dn) continue;
            Apply(0);   // night mode switches lamps: let it see the base state, then apply the variant to what it left
            if (night) night.SetNight(dn);
            if (!ab) Apply(1);
            foreach (var (name, pos, yaw, pitch) in poses)
            {
                string tag = name + "-" + (dn ? "night" : "day");
                if (only.Length > 0 && !only.Contains(name) && !only.Contains(tag)) continue;
                if (fps) fps.transform.position += pos - cam.position;   // move the body so the eye lands on the pose (HouseSplit, audio follow)
                cam.SetPositionAndRotation(pos, Quaternion.Euler(pitch, yaw, 0));
                foreach (var step in steps)
                {
                    if (ab) Apply(step[0] - 'A');
                    for (int w = 0; w < 120; w++) yield return null;   // warm-up: streaming, cached shadows, exposure (and a screen= resize)
                    string t = ab ? tag + "-" + step : tag;
                    yield return Sample(t, ab ? 150 : 300, dir);
                    if (step == "" || step.EndsWith(rounds.ToString())) { ScreenCapture.CaptureScreenshot(Path.Combine(dir, t + ".png")); yield return null; yield return null; }
                    if (dn && (step == "" || step.EndsWith(rounds.ToString()))) VehicleProbe.Report(Path.Combine(dir, t + "-vehicles.txt"), Camera.main);   // what lit (or flooded) the frame
                }
            }
            // MOTION (Oct 20, user: "if i open the door or hit a paint can, the fps becomes laughable again"): from the foyer pose, 10 s
            // after the front door is opened (E's path: SetOpen), and at night 10 s after a paint can is knocked at walking speed
            // (1.4 m/s, as PaintCanTrap.PushByPlayer). Per frame: ms, the lamps whose shadow maps redrew, whether the piece still moves.
            if (only.Length == 0 || only.Contains("motion"))
            {
                var door = FindObjectsByType<EntranceDoor>(FindObjectsInactive.Include).FirstOrDefault(d => d.label == "front door");
                var cans = FindObjectsByType<PaintCanTrap>(FindObjectsInactive.Include).OrderBy(q => q.name).ToArray();
                var (_, fpos, fyaw, fpitch) = POSES[1];
                if (fps) fps.transform.position += fpos - cam.position;
                cam.SetPositionAndRotation(fpos, Quaternion.Euler(fpitch, fyaw, 0));
                string dnS = dn ? "night" : "day";
                foreach (var step in steps)
                {
                    if (ab) Apply(step[0] - 'A');
                    string suf = ab ? "-" + step : "";
                    if (door)
                    {
                        door.SetInstant(false); for (int w = 0; w < 120; w++) yield return null;
                        yield return Sample("door-" + dnS + suf, 0, dir, 10f, () => door.SetOpen(true), () => door.Moving);
                        door.SetInstant(false);
                    }
                    if (dn && cans.Length > 0)
                    {
                        foreach (var c in cans) c.ResetRig(); for (int w = 0; w < 120; w++) yield return null;
                        yield return Sample("can-" + dnS + suf, 0, dir, 10f, () => { cans[0].can.WakeUp(); cans[0].can.linearVelocity = Vector3.forward * 1.4f; }, () => cans.Any(c => c.Moving));
                        foreach (var c in cans) c.ResetRig();
                    }
                }
            }
        }
        File.WriteAllText(Path.Combine(dir, "done.txt"), "ok\n");
        Application.Quit();
    }

    // what dynamic resolution actually did (Phase A anomaly, Oct 21): the camera's pixel and scaled sizes, HDRP's camera size, the
    // handler's scale and last scaled size, the RTHandle pool's max size
    static string DynResReadout()
    {
        var c = Camera.main; if (!c) return "\"dynres\":null";
        var h = UnityEngine.Rendering.HighDefinition.HDCamera.GetOrCreate(c); var dh = UnityEngine.Rendering.DynamicResolutionHandler.instance;
        string ls = dh != null ? $"{dh.GetLastScaledSize().x}x{dh.GetLastScaledSize().y}" : "-";
        return $"\"dynres\":{{\"cam_pixel\":\"{c.pixelWidth}x{c.pixelHeight}\",\"cam_scaled\":\"{c.scaledPixelWidth}x{c.scaledPixelHeight}\",\"allow\":{c.allowDynamicResolution.ToString().ToLower()},"
            + $"\"hd_actual\":\"{h.actualWidth}x{h.actualHeight}\",\"handler_scale\":{(dh != null ? dh.GetCurrentScale() : -1f):F3},\"handler_last\":\"{ls}\",\"rthandles_max\":\"{UnityEngine.Rendering.RTHandles.maxWidth}x{UnityEngine.Rendering.RTHandles.maxHeight}\","
            + $"\"sbm\":\"{ScalableBufferManager.widthScaleFactor:F3}x{ScalableBufferManager.heightScaleFactor:F3}\"}}";
    }

    public static void Run(string name, int frames)
    {
        var g = new GameObject("PerfProbe"); var p = g.AddComponent<PerfProbe>(); p.StartCoroutine(p.Sample(name, frames));
    }

    IEnumerator Sample(string name, int frames, string outDir = null, float seconds = 0f, System.Action start = null, System.Func<bool> moving = null)
    {
        Last = "running";
        var counters = new Dictionary<string, ProfilerRecorder>
        {
            ["batches"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count"),
            ["setpass"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "SetPass Calls Count"),
            ["triangles"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count"),
            ["shadow_casters"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Shadow Casters Count"),
            ["draw_calls"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count"),
            ["sys_mem_mb"] = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "System Used Memory"),
            ["gfx_mem_mb"] = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "Gfx Used Memory"),
            ["gpu_frame_ns"] = ProfilerRecorder.StartNew(ProfilerCategory.Render, "GPU Frame Time"),   // the profiler's GPU time (FrameTiming's is sparse on Metal)
        };
        var vals = counters.Keys.ToDictionary(k => k, k => new List<long>());
        // per-frame tags (tools/house/perf_attrib.py names each heavy frame's cause): profiler markers by name (CPU ns; HDRP's
        // ProfilingSamplers exist in development players), GC runs, ShadowRefresh map requests, reflection-camera renders (realtime
        // planar mirrors / probes), lights switched on
        var handles = new List<ProfilerRecorderHandle>(); ProfilerRecorderHandle.GetAvailable(handles);
        var markers = new Dictionary<string, ProfilerRecorder>();
        foreach (var h in handles)
        {
            var d = ProfilerRecorderHandle.GetDescription(h);
            if (MARKERS.Contains(d.Name) && !markers.ContainsKey(d.Name)) markers[d.Name] = ProfilerRecorder.StartNew(d.Category, d.Name);
        }
        var mlog = markers.Keys.ToDictionary(k => k, k => new List<long>());
        var gcLog = new List<int>(); var shLog = new List<int>(); var reflLog = new List<int>(); var lightLog = new List<int>();
        var allLights = FindObjectsByType<Light>(FindObjectsInactive.Include);
        int refl = 0; System.Action<UnityEngine.Rendering.ScriptableRenderContext, Camera> onCam = (_, c) => { if (c.cameraType == CameraType.Reflection) refl++; };
        UnityEngine.Rendering.RenderPipelineManager.beginCameraRendering += onCam;
        int gc0 = System.GC.CollectionCount(0), sh0 = ShadowRefresh.Requests;
        var cpu = new List<float>(); var gpu = new List<double>(); var main = new List<double>(); var rend = new List<double>(); var ft = new FrameTiming[1];
        var scaleLog = new List<float>();
        var movLog = new List<int>(); var lampLog = new List<string>(); ShadowRefresh.Drawn.Clear();
        // the transparent materials the camera's frustum holds (Phase B: which glass / sheers a view draws), material -> renderers
        var planes = GeometryUtility.CalculateFrustumPlanes(Camera.main);
        var transp = FindObjectsByType<Renderer>().Where(r => r.enabled && GeometryUtility.TestPlanesAABB(planes, r.bounds))
            .SelectMany(r => r.sharedMaterials.Where(m => m && m.renderQueue > 2500).Select(m => m.name + (m.renderQueue >= 3300 ? " (lowres)" : ""))).GroupBy(n => n)
            .OrderByDescending(g => g.Count()).Select(g => $"\"{g.Key.Replace("\"", "'")}\":{g.Count()}");
        string transpJ = "{" + string.Join(",", transp) + "}";
        start?.Invoke(); float t0 = Time.unscaledTime;
        for (int i = 0; seconds > 0f ? Time.unscaledTime - t0 < seconds : i < frames; i++)
        {
            yield return null;
            movLog.Add(moving != null && moving() ? 1 : 0); scaleLog.Add(Mathf.Round(RenderScale.Percent));
            lampLog.Add("\"" + string.Join(" ", ShadowRefresh.Drawn) + "\""); ShadowRefresh.Drawn.Clear();
            cpu.Add(Time.unscaledDeltaTime * 1000f);
            int gc = System.GC.CollectionCount(0), sh = ShadowRefresh.Requests;
            gcLog.Add(gc - gc0); shLog.Add(sh - sh0); reflLog.Add(refl); gc0 = gc; sh0 = sh; refl = 0;
            int on = 0; foreach (var l in allLights) if (l && l.isActiveAndEnabled) on++; lightLog.Add(on);
            foreach (var kv in markers) mlog[kv.Key].Add(kv.Value.LastValue);
            foreach (var kv in counters) vals[kv.Key].Add(kv.Value.LastValue);
            FrameTimingManager.CaptureFrameTimings();
            if (FrameTimingManager.GetLatestTimings(1, ft) > 0)
            {
                if (ft[0].gpuFrameTime > 0) gpu.Add(ft[0].gpuFrameTime);
                main.Add(ft[0].cpuMainThreadFrameTime); rend.Add(ft[0].cpuRenderThreadFrameTime);   // busy time per thread: bound = the largest
            }
        }
        foreach (var r in counters.Values) r.Dispose();
        foreach (var r in markers.Values) r.Dispose();
        UnityEngine.Rendering.RenderPipelineManager.beginCameraRendering -= onCam;
        string Arr<T>(IEnumerable<T> l) => "[" + string.Join(",", l.Select(x => System.Convert.ToString(x, System.Globalization.CultureInfo.InvariantCulture))) + "]";
        string flog = "{\"ms\":" + Arr(cpu.Select(x => System.Math.Round(x, 1))) + ",\"gpu_ms\":" + Arr(vals["gpu_frame_ns"].Select(x => System.Math.Round(x / 1e6, 1)))
            + ",\"gc\":" + Arr(gcLog) + ",\"shadow_requests\":" + Arr(shLog) + ",\"reflection_renders\":" + Arr(reflLog) + ",\"lights_on\":" + Arr(lightLog)
            + ",\"moving\":" + Arr(movLog) + ",\"scale\":" + Arr(scaleLog) + ",\"shadow_lamps\":[" + string.Join(",", lampLog) + "]"
            + ",\"markers_us\":{" + string.Join(",", mlog.Select(kv => $"\"{kv.Key}\":" + Arr(kv.Value.Select(v => v / 1000)))) + "}}";
        foreach (var k in new[] { "sys_mem_mb", "gfx_mem_mb" }) vals[k] = vals[k].Select(v => v >> 20).ToList();
        int rt = 0, rtShadow = 0;   // lights drawn in real time (not fully baked), and those casting shadows
        foreach (var l in FindObjectsByType<Light>())
            if (l.enabled && !(l.bakingOutput.isBaked && l.bakingOutput.lightmapBakeType == LightmapBakeType.Baked)) { rt++; if (l.shadows != LightShadows.None) rtShadow++; }
        float Pct(List<float> l, float p) { var s = l.OrderBy(x => x).ToList(); return s[Mathf.Clamp((int)(p * (s.Count - 1)), 0, s.Count - 1)]; }
        long Med(List<long> l) { var s = l.OrderBy(x => x).ToList(); return s[s.Count / 2]; }
        var cam = Camera.main ? Camera.main.transform : transform;
        // p10 beside the median: another GPU client (the editor in Play) inflates some frames; the low percentile is the uncontended cost
        var gs = gpu.OrderBy(x => x).ToList();
        string gpuS = gs.Count > 0 ? gs[gs.Count / 2].ToString("F1") : "null", gpu10 = gs.Count > 0 ? gs[gs.Count / 10].ToString("F1") : "null";
        string Q(List<double> l, float q) { if (l.Count == 0) return "null"; var s = l.OrderBy(x => x).ToList(); return s[Mathf.Clamp((int)(q * (s.Count - 1)), 0, s.Count - 1)].ToString("F1"); }
        frames = cpu.Count;
        int restAt = movLog.Count; while (restAt > 0 && movLog[restAt - 1] == 0) restAt--;   // first frame after which nothing moves
        float restS = 0f; for (int i = 0; i < restAt; i++) restS += cpu[i] / 1000f;
        string rest = moving == null ? "null" : restAt == movLog.Count ? "-1" : restS.ToString("F2", System.Globalization.CultureInfo.InvariantCulture);
        Last = "{" + $"\"name\":\"{name}\",\"frames\":{frames},\"rest_s\":{rest},\"cpu_ms_median\":{Pct(cpu, 0.5f):F1},\"cpu_ms_p95\":{Pct(cpu, 0.95f):F1},\"cpu_ms_p99\":{Pct(cpu, 0.99f):F1},"
             + $"\"gpu_ms_median\":{gpuS},\"gpu_ms_p10\":{gpu10},\"gpu_ms_p95\":{Q(gpu, 0.95f)},\"gpu_ms_p99\":{Q(gpu, 0.99f)},\"main_ms_median\":{Q(main, 0.5f)},\"render_ms_median\":{Q(rend, 0.5f)},\"rt_lights\":{rt},\"rt_shadow_lights\":{rtShadow}," + string.Join(",", vals.Select(kv => $"\"{kv.Key}\":{Med(kv.Value)}"))
             + ",\"frame_log\":" + flog
             + $",\"screen\":\"{Screen.width}x{Screen.height}\",\"render_scale\":{RenderScale.Percent:F0},\"internal\":\"{Mathf.RoundToInt(Screen.width * ScalableBufferManager.widthScaleFactor)}x{Mathf.RoundToInt(Screen.height * ScalableBufferManager.heightScaleFactor)}\",\"backbuffer\":\"{Display.main.renderingWidth}x{Display.main.renderingHeight}\",\"mode\":\"{Screen.fullScreenMode}\",\"window_display\":\"{Screen.mainWindowDisplayInfo.name}\",\"vsync\":{QualitySettings.vSyncCount},{DynResReadout()},\"inject\":\"{injectNow}\",\"transparents\":{transpJ},\"scale_mode\":\"{RenderScale.Label}\",\"focused\":{Application.isFocused.ToString().ToLower()},\"cam\":\"{cam.position.x:F2},{cam.position.y:F2},{cam.position.z:F2} yaw {cam.eulerAngles.y:F0}\"" + "}";
        var dir = outDir ?? Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/perf")); Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, name + ".json"), Last + "\n");
        if (outDir == null) Destroy(gameObject);
    }
}
