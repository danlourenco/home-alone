using System.Collections.Generic;
using System.IO;
using UnityEditor;
using Newtonsoft.Json.Linq;
using UnityEngine.Rendering.HighDefinition;
using UnityEngine;
using UnityEngine.Rendering;

// The two upstairs bathrooms (TRIAL 1, Oct 19; changes/2026-10-19-bathrooms.json): the generated fixtures (tools/house/hifi_bathrooms.py ->
// Models/Foyer/Bathrooms.glb, static) and counter clutter (BathroomProps.glb, NOT static: movable live), the tile/carpet floors, walk
// colliders for the fixtures, the film's lamps (the parents' 4-globe bar, a downlight, the hall bath's double sconce) and a planar
// reflection on the parents' vanity mirror (the foyer mirror's approach). Positions: spec/dressing/bathrooms.json (spec metres above the
// upper floor; Unity z = -spec z). Wall finishes come from finishes.json (Storey).
public static partial class SpecGreybox
{
    static void Bathrooms(GameObject root)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/bathrooms.json"));
        if (!File.Exists(fp)) return;
        var D = JObject.Parse(File.ReadAllText(fp));
        Material M(string n, Color c, float smooth, float metal = 0f) { var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", metal); return m; }
        Material Cloth(string n, Color c)
        {   // single-sheet cloth: both faces drawn
            var m = M(n, c, 0.1f); m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_DoubleSidedNormalMode", 0f); HDMaterial.ValidateMaterial(m); return m;
        }
        Material Tile(string n, string png, Color fallback, float smooth) { var m = PaperMat(n, png, fallback); m.SetFloat("_Smoothness", smooth); HDMaterial.ValidateMaterial(m); return m; }
        Material Glow(string n, Color c, float nits)
        {
            var m = M(n, c, 0.3f); m.SetColor("_EmissiveColor", new Color(1f, 0.85f, 0.62f) * nits);
            UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); return m;
        }
        var mirror = M("HiFi_BathMirror", new Color(0.85f, 0.87f, 0.88f), 0.97f, 1f);
        var glass = M("HiFi_ShowerGlass", new Color(0.80f, 0.86f, 0.86f, 0.12f), 0.95f);
        glass.SetFloat("_SurfaceType", 1f); glass.SetFloat("_BlendMode", 0f); glass.SetFloat("_DoubleSidedEnable", 1f);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(glass);
        var porcelain = M("HiFi_Porcelain", new Color(0.93f, 0.93f, 0.90f), 0.85f);
        var brass = BrassMat();
        var remap = new Dictionary<string, Material>
        {
            ["BA_Ivory"] = M("HiFi_BathIvory", new Color(0.86f, 0.82f, 0.70f), 0.45f),                       // film 4398 drawer bank
            ["BA_Marble"] = Tile("HiFi_BathMarble", "spec/dressing/bath_marble.png", new Color(0.07f, 0.16f, 0.11f), 0.8f),   // film 4398 counter
            ["BA_BlackMarble"] = M("HiFi_BathBlackMarble", new Color(0.03f, 0.04f, 0.04f), 0.8f),
            ["BA_Brass"] = brass, ["BA_Gilt"] = brass,
            ["BA_Porcelain"] = porcelain, ["BA_MirrorGlass"] = mirror, ["BA_ShowerGlass"] = glass,
            ["BA_BlackFrame"] = M("HiFi_BathBlackFrame", new Color(0.04f, 0.04f, 0.04f), 0.5f, 0.6f),
            ["BA_Globe"] = Glow("HiFi_BathGlobe", new Color(1f, 0.97f, 0.9f), 40f),
            ["BA_Mat"] = M("HiFi_BathPrintMat", new Color(0.92f, 0.90f, 0.84f), 0.1f),
            ["BA_PrintL"] = SpecTexMat("HiFi_BathPrintL", "spec/dressing/prints/print_left.png"),
            ["BA_PrintM"] = SpecTexMat("HiFi_BathPrintM", "spec/dressing/prints/print_right.png"),
            ["BA_PrintR"] = SpecTexMat("HiFi_BathPrintR", "spec/dressing/prints/print_left.png"),
            ["BA_TowelSage"] = M("HiFi_TowelSage", new Color(0.30f, 0.52f, 0.40f), 0.05f),             // film 4398: sage/teal towel
            ["BA_TowelDark"] = M("HiFi_TowelDark", new Color(0.04f, 0.16f, 0.09f), 0.05f),
            ["BA_TowelWhite"] = M("HiFi_TowelWhite", new Color(0.92f, 0.92f, 0.89f), 0.05f),
            ["BA_Lace"] = Cloth("HiFi_BathLace", new Color(0.93f, 0.91f, 0.84f)),
            ["BA_Bin"] = M("HiFi_BathBin", new Color(0.05f, 0.05f, 0.05f), 0.5f),
            ["BA_Shadow"] = M("HiFi_BathToe", new Color(0.05f, 0.05f, 0.05f), 0.1f),
            ["BA_Subway"] = Tile("HiFi_BathSubway", "spec/dressing/bath_subway.png", new Color(0.92f, 0.92f, 0.90f), 0.8f),
            ["BA_TileBlack"] = M("HiFi_BathTileBlack", new Color(0.03f, 0.03f, 0.03f), 0.8f),
            ["BA_ShowerCurtain"] = Cloth("HiFi_BathCurtainGreen", new Color(0.08f, 0.42f, 0.22f)),
            ["BA_CurtainCream"] = Cloth("HiFi_BathCurtainCream", new Color(0.86f, 0.82f, 0.74f)),
            ["BA_WhitePaint"] = M("HiFi_BathWhitePaint", new Color(0.90f, 0.90f, 0.88f), 0.4f),
            ["BA_Wicker"] = TexMat("HiFi_BathWicker", "oak_veneer_01", new Color(1.05f, 0.85f, 0.55f), 0.25f, 0.15f),
            ["BA_Pot"] = M("HiFi_BathPot", new Color(0.36f, 0.34f, 0.31f), 0.3f),
            ["BA_Grass"] = Cloth("HiFi_BathGrass", new Color(0.20f, 0.42f, 0.16f)),
        };
        var g = PlaceHiFi(root, 0f, "Bathrooms", remap);
        if (g != null)
            foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
            {
                var n = r.sharedMaterial != null ? r.sharedMaterial.name : "";
                r.shadowCastingMode = n == "HiFi_BathGlobe" || n == "HiFi_ShowerGlass" ? ShadowCastingMode.Off : ShadowCastingMode.On;
                r.gameObject.isStatic = true;
            }
        var propRemap = new Dictionary<string, Material>
        {
            ["BA_PropAftershave"] = M("HiFi_PropAftershave", new Color(0.06f, 0.10f, 0.07f), 0.85f),   // film 4408: the dark bottle
            ["BA_PropMint"] = M("HiFi_PropMint", new Color(0.66f, 0.88f, 0.76f), 0.5f), ["BA_PropSteel"] = M("HiFi_PropSteel", new Color(0.62f, 0.62f, 0.64f), 0.6f, 1f),
            ["BA_PropWhite"] = M("HiFi_PropWhite", new Color(0.92f, 0.92f, 0.90f), 0.5f), ["BA_PropRed"] = M("HiFi_PropRed", new Color(0.78f, 0.08f, 0.10f), 0.5f),
            ["BA_PropBlack"] = M("HiFi_PropBlack", new Color(0.03f, 0.03f, 0.03f), 0.5f), ["BA_PropAmber"] = M("HiFi_PropAmber", new Color(0.60f, 0.36f, 0.10f), 0.85f),
            ["BA_PropGold"] = brass, ["BA_PropAqua"] = M("HiFi_PropAqua", new Color(0.22f, 0.60f, 0.45f), 0.5f),
            ["BA_PropCrystal"] = M("HiFi_PropCrystal", new Color(0.86f, 0.89f, 0.91f), 0.95f), ["BA_PropCotton"] = M("HiFi_PropCotton", new Color(0.96f, 0.84f, 0.90f), 0.2f),
            ["BA_PropJade"] = M("HiFi_PropJade", new Color(0.50f, 0.72f, 0.56f), 0.7f), ["BA_PropWheat"] = M("HiFi_PropWheat", new Color(0.82f, 0.68f, 0.38f), 0.2f),
            ["BA_TowelSage"] = remap["BA_TowelSage"], ["BA_TowelDark"] = remap["BA_TowelDark"], ["BA_TowelWhite"] = remap["BA_TowelWhite"],
        };
        var gp = PlaceHiFi(root, 0f, "BathroomProps", propRemap);   // loose props: left non-static so they can be nudged in Play
        if (gp != null) foreach (var t in gp.GetComponentsInChildren<Transform>()) t.gameObject.isStatic = false;

        // floors: dark green carpet in the ensuite (the set photo, Marina 165 s), white hex mosaic in the hall bath (ASSUMED: the film never shows it)
        var carpet = M("HiFi_BathCarpet", new Color(0.05f, 0.13f, 0.09f), 0.05f);
        var hex = Tile("HiFi_BathHex", "spec/dressing/bath_hex.png", new Color(0.92f, 0.92f, 0.90f), 0.6f);
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>())
        {
            if (r.name == "Floor_parents_bath") r.sharedMaterial = carpet;
            if (r.name == "Floor_hall_bath") r.sharedMaterial = hex;
        }

        // walk colliders (spec boxes): solids Kevin and the bandits walk round; the knee space and the shower stay open (Kevin's hiding spots)
        var cols = Child(root, "BathColliders"); cols.isStatic = true;
        void Col(string n, float x0, float x1, float y0, float y1, float z0, float z1)
        {
            var c = new GameObject("BathCollider_" + n); c.transform.SetParent(cols.transform, false); c.isStatic = true;
            c.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2, -(z0 + z1) / 2);
            c.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, y1 - y0, z1 - z0);
        }
        var PB = D["parents_bath"]; var V = PB["vanity"];
        float top = (float)V["top"], vz0 = (float)V["z"][0], vz1 = (float)V["z"][1], wallA = vz1 + 0.015f;   // the vanity wall face (fixtures 1.5 cm off it; z 5.17 since Oct 20)
        Col("vanity_drawers", (float)V["drawers_x"][0], (float)V["drawers_x"][1], 0f, top, vz0, vz1);
        Col("vanity_sink", (float)V["sink_x"][0], (float)V["sink_x"][1], 0f, top, vz0, vz1);
        Col("vanity_drawers_door", (float)V["drawers_door_x"][0], (float)V["drawers_door_x"][1], 0f, top, vz0, vz1);
        Col("vanity_top", 0.343f, (float)V["x"][1] + 0.02f, top - (float)V["slab"] - 0.10f, top + 0.10f, vz0 - 0.02f, wallA);
        var T = PB["tub"]; Col("tub", (float)T["x"][0], (float)T["x"][1], 0f, (float)T["rim"], (float)T["z"][0], (float)T["z"][1]);
        float tlx = (float)PB["toilet"]["wall_x"], tlz = (float)PB["toilet"]["z"];
        Col("toilet", tlx - 0.725f, tlx - 0.015f, 0f, 0.42f, tlz - 0.26f, tlz + 0.26f);
        Col("toilet_tank", tlx - 0.235f, tlx - 0.015f, 0.42f, 0.785f, tlz - 0.26f, tlz + 0.26f);
        {   // the shower's glass: one thin box per arc segment outside the door gap
            var S = PB["shower"]; float cx = (float)S["corner"][0] - 0.015f, cz = (float)S["corner"][1] + 0.015f, rr = (float)S["r"] - 0.015f;
            float d0 = (float)S["door"][0], d1 = (float)S["door"][1], h = (float)S["glass_h"] + (float)S["tray"];
            for (int k = 0; k < 24; k++)
            {
                float f = (k + 0.5f) / 24f; if (f > d0 && f < d1) continue;
                float a0 = Mathf.PI / 2 * k / 24, a1 = Mathf.PI / 2 * (k + 1) / 24;
                var p0 = new Vector2(cx - rr * Mathf.Cos(a0), cz + rr * Mathf.Sin(a0)); var p1 = new Vector2(cx - rr * Mathf.Cos(a1), cz + rr * Mathf.Sin(a1));
                var c = new GameObject("BathCollider_shower_glass"); c.transform.SetParent(cols.transform, false); c.isStatic = true;
                c.transform.position = new Vector3((p0.x + p1.x) / 2, h / 2, -(p0.y + p1.y) / 2);
                var dir = new Vector3(p1.x - p0.x, 0, -(p1.y - p0.y));
                c.transform.rotation = Quaternion.LookRotation(dir.normalized, Vector3.up);
                c.AddComponent<BoxCollider>().size = new Vector3(0.02f, h, dir.magnitude + 0.01f);
            }
        }
        var HB = D["hall_bath"]; var HT = HB["tub"];
        Col("hall_tub", (float)HT["x"][0], (float)HT["x"][1], 0f, (float)HT["rim"], (float)HT["z"][0], (float)HT["z"][1]);
        var EW = HB["tub_end_wall"]; Col("hall_tub_end", (float)EW["x"][0], (float)EW["x"][1], 0f, (float)EW["y"][1], (float)EW["z"][0], (float)EW["z"][1]);
        float htx = (float)HB["toilet"]["x"]; Col("hall_toilet", htx - 0.26f, htx + 0.26f, 0f, 0.785f, 7.793f, 8.50f);
        float skx = (float)HB["sink"]["x"]; Col("hall_sink", skx - 0.30f, skx + 0.30f, 0f, (float)HB["sink"]["rim"], 10.935f, 11.415f);
        var WS = HB["wicker_shelf"]; Col("hall_shelf", (float)WS["x"][0], (float)WS["x"][1], 0f, (float)WS["h"], (float)WS["z"][0], (float)WS["z"][1]);
        var HM = HB["hamper"]; Col("hall_hamper", (float)HM["x"][0], (float)HM["x"][1], 0f, (float)HM["h"] + 0.03f, (float)HM["z"][0], (float)HM["z"][1]);

        // lamps (2700 K, the house's AddLamp: cached shadows via LimitShadows)
        var fx = Child(root, "BathFixtures");
        var LB = PB["light_bar"];
        AddLamp(fx, "BathLamp_parents_bar", new Vector3(((float)LB["x"][0] + (float)LB["x"][1]) / 2, (float)LB["y"] - 0.10f, (float)LB["wall_z"] + 0.20f), 0f, (float)LB["lumens"], (float)LB["kelvin"]);
        var CL = PB["ceiling_lamp"]; AddLamp(fx, "BathLamp_parents_ceiling", new Vector3((float)CL["at"][0], (float)CL["at"][1] - 0.06f, (float)CL["at"][2]), 0f, (float)CL["lumens"], (float)CL["kelvin"]);
        var SC = HB["sconce"]; int si = 0;   // the double sconce (film 336): one lamp in each shade
        foreach (var ax in SC["arms"])
            AddLamp(fx, $"BathLamp_hall_sconce{si++}", new Vector3((float)ax, (float)SC["y"] + 0.03f, 11.428f - (float)SC["out"]), 0f, (float)SC["lumens"], (float)SC["kelvin"]);

        // the vanity mirror's planar reflection (as FoyerMirror): the glass is 3 cm off the vanity wall face, the room toward world +z
        var MI = PB["mirror"];
        float mx = ((float)MI["x"][0] + (float)MI["x"][1]) / 2, my = ((float)MI["y"][0] + (float)MI["y"][1]) / 2;
        var go = new GameObject("BathMirrorProbe"); go.transform.SetParent(fx.transform, false);
        go.transform.position = new Vector3(mx, my, -(wallA - 0.032f));
        go.transform.rotation = Quaternion.identity;   // local forward (+z) faces the room
        var probe = go.AddComponent<PlanarReflectionProbe>();
        probe.mode = ProbeSettings.Mode.Realtime; probe.realtimeMode = ProbeSettings.RealtimeMode.EveryFrame;
        probe.settingsRaw.resolutionScalable.useOverride = true;
        probe.settingsRaw.resolutionScalable.@override = PlanarReflectionAtlasResolution.Resolution512;
        probe.settingsRaw.proxySettings.mirrorPositionProxySpace = Vector3.zero;
        probe.settingsRaw.proxySettings.mirrorRotationProxySpace = Quaternion.identity;
        probe.influenceVolume.boxSize = new Vector3((float)MI["x"][1] - (float)MI["x"][0], (float)MI["y"][1] - (float)MI["y"][0], 0.16f);
        probe.influenceVolume.boxBlendDistancePositive = Vector3.zero; probe.influenceVolume.boxBlendDistanceNegative = Vector3.zero;
        probe.lightLayers = (UnityEngine.Rendering.HighDefinition.RenderingLayerMask)255; probe.importance = 100;
    }
}
