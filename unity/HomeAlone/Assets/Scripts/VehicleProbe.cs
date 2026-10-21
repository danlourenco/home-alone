using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// PerfProbe's vehicle variants and readout (Oct 21; build 9 still showed the police bars as red/blue glow balls at murphys-night, a blue
// flood at van-night and the van as a silhouette). One -perfvariants key, police=..., isolates the cause; the readout says what the
// frame was made of. Restored to the base before every sample (PerfProbe.ApplyV calls Apply for base and variant alike).
//   police=nowash    the two PoliceLights wash point lights off
//   police=noglass   the bar's lamp glass emission 0 (beacons and flashers)
//   police=nolamps   the cars' head and tail lamp emission 0 (VEH_Police_Lamps)
//   police=nocar     every PoliceLights car hidden (renderers and wash lights off): does the glow survive without the car at all?
//   police=nobloom   bloom intensity 0 (a top-priority volume; bloomthr=T instead sets only the threshold)
//   police=nofog     the night volumetric fog off (the same volume)
//   police=fix       the candidate values (FIX below; beacon=N flasher=N idle=K wash=LM washrange=M override them)
// Keys combine: "police=nowash+police2=noglass" is not supported; run one police= per variant, or several variants.
// Readout: <dir>/<pose>-<step>-vehicles.txt at every night sample: the blended volume at the camera (exposure, bloom, fog, lens flare),
// each PoliceLights' live state, the vehicles' renderers (rendering layers, probes, materials), the moon, and every punctual light within
// 25 m of a vehicle (range, unit, shadows, light layers, volumetrics), plus the bar's peak nits against the street-lamp globe's.
public static class VehicleProbe
{
    // the candidate fix: the glass a few times white at our night exposure (the build-9 1500 nits bloomed like a lamp globe), a dim
    // wash out of the fog. Placeholders until the isolation runs say which term dominates
    public static float FixBeacon = 300f, FixFlasher = 220f, FixIdle = 0.03f, FixWash = 120f, FixWashRange = 6f;

    static Volume vol; static Bloom bloom; static Fog fog;
    static readonly Dictionary<PoliceLights, (float b, float f, float i, float w, float r, bool on, bool vo)> base0 = new();
    static readonly Dictionary<Material, Color> lamp0 = new();
    static readonly Dictionary<Renderer, bool> carR0 = new();
    static VolumeStack stack;
    static readonly int EmissiveId = Shader.PropertyToID("_EmissiveColor");

    static float F(Dictionary<string, string> s, string k, float d) => s != null && s.TryGetValue(k, out var v) ? float.Parse(v, CultureInfo.InvariantCulture) : d;

    public static void Apply(Dictionary<string, string> spec)
    {
        string mode = spec != null && spec.TryGetValue("police", out var m) ? m : null;
        if (vol == null)
        {
            vol = new GameObject("VehicleProbeVolume").AddComponent<Volume>(); vol.isGlobal = true; vol.priority = 100001f;
            var p = ScriptableObject.CreateInstance<VolumeProfile>(); vol.sharedProfile = p;
            bloom = p.Add<Bloom>(false); fog = p.Add<Fog>(false);
        }
        bloom.intensity.overrideState = mode == "nobloom"; bloom.intensity.value = 0f;
        bloom.threshold.overrideState = spec != null && spec.ContainsKey("bloomthr"); bloom.threshold.value = F(spec, "bloomthr", 1f);
        fog.enableVolumetricFog.overrideState = mode == "nofog"; fog.enableVolumetricFog.value = false;

        foreach (var pl in Object.FindObjectsByType<PoliceLights>(FindObjectsInactive.Include))
        {
            if (!base0.TryGetValue(pl, out var b)) base0[pl] = b = (pl.beaconNits, pl.flasherNits, pl.idle, pl.washLumens, pl.washRange, pl.washOn, pl.washVolumetric);
            (pl.beaconNits, pl.flasherNits, pl.idle, pl.washLumens, pl.washRange, pl.washOn, pl.washVolumetric) = b;
            if (mode == "nowash") pl.washOn = false;
            if (mode == "noglass") { pl.beaconNits = 0f; pl.flasherNits = 0f; }
            if (mode == "fix")
            {
                pl.beaconNits = F(spec, "beacon", FixBeacon); pl.flasherNits = F(spec, "flasher", FixFlasher); pl.idle = F(spec, "idle", FixIdle);
                pl.washLumens = F(spec, "wash", FixWash); pl.washRange = F(spec, "washrange", FixWashRange); pl.washVolumetric = false;
            }
            pl.Retune();
            foreach (var r in pl.GetComponentsInChildren<Renderer>(true))
            {
                if (!carR0.ContainsKey(r)) carR0[r] = r.enabled;
                r.enabled = mode != "nocar" && carR0[r];
            }
            if (mode == "nocar") { pl.washOn = false; pl.Retune(); }
        }
        if (lamp0.Count == 0)
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include))
                foreach (var mt in r.sharedMaterials)
                    if (mt && mt.name.StartsWith("VEH_Police_Lamps") && mt.HasProperty(EmissiveId) && !lamp0.ContainsKey(mt)) lamp0[mt] = mt.GetColor(EmissiveId);
        foreach (var kv in lamp0) kv.Key.SetColor(EmissiveId, mode == "nolamps" ? Color.black : kv.Value);   // the player's material instance, not the asset
    }

    static string V(Vector3 v) => $"({v.x:F1}, {v.y:F1}, {v.z:F1})";
    static string C(Color c) => $"({c.r:F3}, {c.g:F3}, {c.b:F3}, {c.a:F2})";

    public static void Report(string path, Camera cam)
    {
        var sb = new StringBuilder();
        var hdc = cam.GetComponent<HDAdditionalCameraData>();
        stack ??= VolumeManager.instance.CreateStack();
        VolumeManager.instance.Update(stack, cam.transform, hdc != null ? hdc.volumeLayerMask : (LayerMask)~0);
        var ex = stack.GetComponent<Exposure>(); var bl = stack.GetComponent<Bloom>(); var fg = stack.GetComponent<Fog>(); var lf = stack.GetComponent<ScreenSpaceLensFlare>();
        sb.AppendLine($"camera {V(cam.transform.position)} yaw {cam.transform.eulerAngles.y:F1}");
        sb.AppendLine($"exposure mode {ex.mode.value} fixed {ex.fixedExposure.value:F2} compensation {ex.compensation.value:F2} limits {ex.limitMin.value:F2}..{ex.limitMax.value:F2} (EV100: white = 1.2 * 2^EV nits)");
        sb.AppendLine($"bloom intensity {bl.intensity.value:F2} scatter {bl.scatter.value:F2} threshold {bl.threshold.value:F2}");
        sb.AppendLine($"fog enabled {fg.enabled.value} volumetric {fg.enableVolumetricFog.value} meanFreePath {fg.meanFreePath.value:F0} anisotropy {fg.anisotropy.value:F2} albedo {C(fg.albedo.value)}");
        sb.AppendLine($"screen-space lens flare intensity {lf.intensity.value:F2}; LensFlareComponentSRP in scene: {Object.FindObjectsByType<LensFlareComponentSRP>(FindObjectsInactive.Exclude).Length}");
        float globe = 0f;
        foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Exclude))
            foreach (var mt in r.sharedMaterials)
                if (mt && mt.name.StartsWith("NB_LampGlobe") && mt.HasProperty(EmissiveId)) { var c = mt.GetColor(EmissiveId); globe = Mathf.Max(globe, 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b); }
        foreach (var pl in Object.FindObjectsByType<PoliceLights>(FindObjectsInactive.Exclude))
        {
            float lr = 0.2126f * pl.red.r + 0.7152f * pl.red.g + 0.0722f * pl.red.b, lb = 0.2126f * pl.blue.r + 0.7152f * pl.blue.g + 0.0722f * pl.blue.b;
            sb.AppendLine($"PoliceLights {pl.transform.parent?.name}/{pl.name} at {V(pl.transform.position)} dist {Vector3.Distance(cam.transform.position, pl.transform.position):F1} m: bar {pl.bar} beacon {pl.beaconNits:F0} flasher {pl.flasherNits:F0} idle {pl.idle:F3} rpm {pl.rpm:F0}; peak luminance red {pl.beaconNits * lr:F0} blue {pl.beaconNits * lb:F0} nits vs NB_LampGlobe {globe:F0} nits");
            for (int s = 0; s < 2; s++)
            {
                var l = pl.WashLight(s); if (!l) continue; var hd = l.GetComponent<HDAdditionalLightData>();
                sb.AppendLine($"  wash {l.name}: enabled {l.enabled && l.gameObject.activeInHierarchy} {l.intensity:F0} {l.lightUnit} range {l.range:F1} volumetric {hd.affectsVolumetric} dimmer {hd.volumetricDimmer:F2} specular {hd.affectSpecular} colour {C(l.color)}");
            }
        }
        var cars = Object.FindObjectsByType<LODGroup>(FindObjectsInactive.Exclude).Where(g => g.name.StartsWith("Car_")).ToList();
        var punctual = Object.FindObjectsByType<Light>(FindObjectsInactive.Exclude).Where(l => l.type != LightType.Directional).ToList();
        foreach (var g in cars)
        {
            var rs = g.GetComponentsInChildren<Renderer>(false);
            sb.AppendLine($"vehicle {g.transform.parent?.name}/{g.name} at {V(g.transform.position)} dist {Vector3.Distance(cam.transform.position, g.transform.position):F1} m, active {g.gameObject.activeInHierarchy}, {rs.Length} renderers");
            foreach (var grp in rs.GroupBy(r => (r.renderingLayerMask, r.lightProbeUsage, r.reflectionProbeUsage)))
                sb.AppendLine($"  renderingLayerMask {grp.Key.renderingLayerMask} (moon layer 8: {((grp.Key.renderingLayerMask & 8u) != 0)}) probes {grp.Key.lightProbeUsage} reflections {grp.Key.reflectionProbeUsage}: {grp.Count()} renderers");
            var paint = rs.SelectMany(r => r.sharedMaterials).FirstOrDefault(m => m && m.name.Contains("_Paint"));
            if (paint) sb.AppendLine($"  paint {paint.name} shader {paint.shader.name} base {C(paint.GetColor("_BaseColor"))} map {(paint.GetTexture("_BaseColorMap") ? paint.GetTexture("_BaseColorMap").name : "none")} metallic {paint.GetFloat("_Metallic"):F2} smooth {paint.GetFloat("_Smoothness"):F2} coat {paint.GetFloat("_CoatMask"):F2} mask {(paint.GetTexture("_MaskMap") ? "yes" : "no")}");
            foreach (var l in punctual.Where(l => Vector3.Distance(l.transform.position, g.transform.position) < 25f).OrderBy(l => Vector3.Distance(l.transform.position, g.transform.position)).Take(8))
            {
                var hd = l.GetComponent<HDAdditionalLightData>(); float d = Vector3.Distance(l.transform.position, g.transform.position);
                sb.AppendLine($"  light {l.name} {d:F1} m{(d > l.range ? " OUT OF RANGE" : "")}: {l.type} {l.intensity:F0} {l.lightUnit} range {l.range:F1} shadows {l.shadows} enabled {l.enabled} layers {(hd ? hd.lightlayersMask.ToString() : "-")} volumetric {(hd ? hd.affectsVolumetric.ToString() : "-")}");
            }
        }
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Include).Where(l => l.type == LightType.Directional))
        {
            var hd = l.GetComponent<HDAdditionalLightData>();
            sb.AppendLine($"directional {l.name}: active {l.gameObject.activeInHierarchy} enabled {l.enabled} {l.intensity:F2} {l.lightUnit} layers {(hd ? hd.lightlayersMask.ToString() : "-")} colour {C(l.color)}");
        }
        File.WriteAllText(path, sb.ToString());
    }
}
