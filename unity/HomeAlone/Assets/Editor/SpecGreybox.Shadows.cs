using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// The lamps' real-time shadows (Oct 16, user: "random squares ... sometimes when the camera isn't moving"; "the shadows from the plant
// are cast on the wall, but if i move slightly, they're lost"). 38 shadowed point lamps x 6 cube faces = 228 shadow maps re-rendered
// every frame. With HDRP's 128 requests and 4096 atlas (Editor/ShadowAudit.cs, measured): 234 wanted, 128 drawn (the rest dropped, e.g.
// the plant's), and every map shrunk 1.5-1.74x, the factor changing as the camera panned (HDDynamicShadowAtlas.LayoutResize): squares.
// The house does not move, so every lamp's shadow map is CACHED: drawn once when the lamp turns on (OnDemand + render on placement)
// into its own atlas (HDRP.asset cachedPunctualLightShadowAtlas 8192), and redrawn only when something moving asks for it
// (Scripts/ShadowRefresh.cs: the swing door, the paint cans and the dummy), or when it first comes into view (HDRP's render on
// placement missed lamps placed out of view: ShadowRefresh.Warm). Per frame there is nothing left to draw or reshuffle.
//   - resolution by importance (HDRP's tiers 256/512/1024): HeroLamps 1024; the other fixture lamps and the ground-floor rooms 512; the
//     upstairs' generic room lamps (grey-box rooms) and the tree glow 256. ShadowAudit checks the sum against the atlas.
//   - no fade distance (HDRP's default): the 10 m stop-gap let a lamp 9-10 m away shine through the walls near the camera.
//   - contact shadows (screen space, per frame) on the sun and the lamps clear of walls and shelves (ContactLamps). HDRP gives them to
//     the first 24 lights on screen only (HDGpuLightsBuilder.GetContactShadowMask): 11 lights in the house have them, none can starve.
//   - the den's green banker's lamp is a downward spot: its hood is opaque (Marina f141), and as a point it lit the ceiling through it.
public static partial class SpecGreybox
{
    // contact shadows march the depth buffer, which holds the lamp shades, chimneys and bowls that are kept out of the shadow maps
    // (they pass light): a lamp whose bulb sits in one, near a wall or shelf, drew its own shade's silhouette as a dark blot (the
    // living room's console lamps, the den's urn lamp: play-mode captures, Oct 16). Only lamps clear of any surface get them.
    static readonly string[] ContactLamps = { "UnderCab_", "KitchenChandelier_Light", "Lantern_Light", "DenLamp_desk", "LivingLamp_banker" };
    static readonly string[] HeroLamps = { "DenLamp_bookcase", "DenLamp_floor", "DenLamp_tray", "LivingLamp_chest" };
    // rooms nobody can see into: behind prop doors (linen closet, under the landing) or with no opening at all (girls' A closet)
    static readonly string[] SealedRoomLamps = { "Light_linen_closet", "Light_under_landing", "Light_girls_a_closet" };
    const float UpstairsY = 0.5f;   // world y above which a lamp is upstairs (upstairs floor 0, ground floor -3.0)

    // Soft shadows (user Oct 18: "can we use HDRP's high-quality soft-shadow mode where necessitated?"): with HDRP.asset punctual filtering
    // High (PCSS; left at Medium until its night cost is measured, docs/PERFORMANCE.md) each lamp's source size sets its penumbra, as a real bulb's does: bare bulbs small, candle sconces and lanterns a little
    // larger, shaded lamps the size of the lit shade, ceiling domes and the generic room lamps (a dome fixture each) larger still.
    // -1: keep what the lamp's builder set (the parents' lamps: their shades' own sizes)
    static float SourceRadius(string n) =>
        n.StartsWith("ParentsLamp") ? -1f :
        n.Contains("Bulb") || n.StartsWith("UnderCab") ? 0.03f :
        n.Contains("Sconce") || n.StartsWith("Hurricane") || n.Contains("Lantern") || n.StartsWith("BasementDoorLamp") ? 0.04f :
        n.Contains("Chandelier") ? 0.06f :
        n.Contains("Lamp") ? 0.09f :
        n.StartsWith("Dome") || n.StartsWith("Light_") ? 0.12f : -1f;

    static void LimitShadows(GameObject root)
    {
        var all = Object.FindObjectsByType<Light>(FindObjectsInactive.Include, FindObjectsSortMode.None);
        foreach (var l in all.Where(l => SealedRoomLamps.Contains(l.name)).ToList()) Object.DestroyImmediate(l.gameObject);

        var desk = all.FirstOrDefault(l => l && l.name == "DenLamp_desk");
        if (desk != null)
        {   // the hood (hifi_den.py): a 0.12 x 0.26 box 0.30-0.36 above the base; the bulb at its open bottom shines down through it: half-angles atan(0.06/0.03) = 63 and atan(0.13/0.03) = 77 deg -> a 140 deg cone with a soft edge. The same candela as
            // the point it replaces (reflector off: HDRP counts a spot's lumens over the whole sphere, as a point's)
            desk.type = LightType.Spot; desk.enableSpotReflector = false; desk.spotAngle = 140f; desk.innerSpotAngle = 90f;
            desk.transform.rotation = Quaternion.LookRotation(Vector3.down, Vector3.forward);
        }

        int n = 0, contact = 0; long texels = 0, areaTexels = 0;
        foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Include, FindObjectsSortMode.None))
        {
            var hd = l.GetComponent<HDAdditionalLightData>(); if (hd == null) continue;
            if (l.type == LightType.Directional)
            {
                if (l.shadows != LightShadows.None) { hd.useContactShadow.useOverride = true; hd.useContactShadow.@override = true; contact++; }
                continue;
            }
            if (l.shadows == LightShadows.None || l.lightmapBakeType == LightmapBakeType.Baked) continue;   // FilmFill: baked only
            bool generic = l.name.StartsWith("Light_"), small = l.name.StartsWith("LivingTreeGlow"), hero = HeroLamps.Contains(l.name);
            int level = hero ? 2 : (generic && l.transform.position.y > UpstairsY) || small ? 0 : 1;
            hd.shadowUpdateMode = ShadowUpdateMode.OnDemand; hd.onDemandShadowRenderOnPlacement = true; hd.alwaysDrawDynamicShadows = false;
            hd.shadowFadeDistance = 10000f;
            float sr = SourceRadius(l.name); if (sr > 0f) l.shapeRadius = sr;
            hd.SetShadowResolutionOverride(false); hd.SetShadowResolutionLevel(level);
            if (ContactLamps.Any(c => l.name.StartsWith(c))) { hd.useContactShadow.useOverride = true; hd.useContactShadow.@override = true; contact++; }
            int res = 256 << level; long t = (long)(l.type == LightType.Point ? 6 : 1) * res * res; n++;
            if (l.type == LightType.Rectangle) areaTexels += t; else texels += t;
        }

        // contact shadows: the fine contact (an ornament on a table, a book on a shelf) that a 512-1024 map blurs; in the global volume
        var prof = AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Settings/GreyboxVolume.asset");
        if (prof != null && !prof.Has<ContactShadows>())
        {
            var cs = prof.Add<ContactShadows>(true);
            cs.enable.value = true; cs.length.value = 0.12f; cs.maxDistance.value = 12f; cs.fadeDistance.value = 3f;
            cs.quality.overrideState = true; cs.quality.value = (int)ScalableSettingLevelParameter.Level.High;   // 16 samples (HDRP.asset)
            AssetDatabase.AddObjectToAsset(cs, prof); EditorUtility.SetDirty(prof); AssetDatabase.SaveAssets();
        }
        Debug.Log($"LimitShadows: {n} lamps with cached shadows ({texels / 1e6:F1} M punctual + {areaTexels / 1e6:F1} M area texels), {contact} lights with contact shadows (HDRP max 24 on screen)");
        // Invariant (perf pass, Oct 18): every cached shadow map fits its atlas. Oct 18 the 47 shadowed lamps wanted 82.1 M texels of an
        // 8192^2 (67.1 M) punctual atlas: the lamps HDRP could not place kept retrying (night frame time 40-80 ms, unstable run to run).
        // Fixed Oct 18 (user: "Apply shadow space fix"): the punctual atlas is 16384^2 in HDRP.asset; over budget now FAILS the build.
        var ip = AssetDatabase.LoadAssetAtPath<HDRenderPipelineAsset>("Assets/Settings/HDRP.asset").currentPlatformRenderPipelineSettings.hdShadowInitParams;
        long pCap = (long)ip.cachedPunctualLightShadowAtlas * ip.cachedPunctualLightShadowAtlas, aCap = (long)ip.cachedAreaLightShadowAtlas * ip.cachedAreaLightShadowAtlas;
        if (texels > pCap * 0.95 || areaTexels > aCap * 0.95)   // 5% slack for packing
            throw new System.Exception($"BUDGET FAIL shadow atlas: punctual {texels / 1e6:F1} M of {pCap / 1e6:F1} M, area {areaTexels / 1e6:F1} M of {aCap / 1e6:F1} M (HDRP.asset cached*ShadowAtlas)");
    }
}
