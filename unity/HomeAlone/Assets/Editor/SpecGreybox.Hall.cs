using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// The upstairs hall as the film shows it (Oct 16 2026, TRIAL; changes/2026-10-16-upstairs-hall.json, DEVIATIONS 63). Its teal paint over
// the white wainscot and its wood floor come from spec/dressing/finishes.json (tools/house/hall_walls.py); here: the generated dressing
// (tools/house/hifi_hall.py -> HallDressing.glb: runner, crown, sconces, urn stands, pictures, clock / barometer, globe, candlesticks,
// photographs, brass pot), the user's purchased plants for the hall (tools/house/hall_purchased.py -> Assets/Purchased/HallPlants.glb,
// gitignored; absent: empty urns), the sconces' lights (night layer, like the den's lamps) and the walk-layer colliders from
// spec/dressing/hall.json. The two hall tables are owned SIDE_TABLE_01s placed by StoreProps (spec/dressing/store_props.json).
public static partial class SpecGreybox
{
    public static float HallSconceScale = 1f;   // calibration knob against the film's night hall (film_light_match.py --hall-night)

    static void Hall(GameObject root)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/hall.json"));
        if (!File.Exists(fp)) return;
        var D = JObject.Parse(File.ReadAllText(fp));
        Material Glow(string n, Color c, float nits, float smooth)
        {   // HouseNightMode darkens "HiFi_Shade*" / "HiFi_Bulb*" by day
            var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetColor("_EmissiveColor", c * nits);
            UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); return m;
        }
        Material Plain(string n, Color c, float smooth, float metal = 0f) { var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", metal); return m; }
        // the runner: crimson (film 10819/2687/2296/10828: linear albedo 0.23/0.01/0.05 = sRGB 0.52/0.10/0.25; blue raised to 0.31 (lin 0.078): film_light_match.py --hall-night read our runner 1.55x too red beyond the light's own warmth) with the carpet's pile normal
        var runner = TexMat("HiFi_HallRunner", "dirty_carpet", new Color(0.52f, 0.10f, 0.31f), 0.6f, 0.05f);
        runner.SetTexture("_BaseColorMap", null); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(runner);
        var g = PlaceHiFi(root, 0f, "HallDressing", new Dictionary<string, Material> {
            ["HL_Runner"] = runner,
            ["HL_White"] = Plain("HiFi_HallCrown", new Color(0.86f, 0.86f, 0.84f), 0.45f),
            ["HL_Brass"] = BrassMat(),
            ["HL_Shade"] = Glow("HiFi_ShadeHall", new Color(0.94f, 0.91f, 0.85f), 900f, 0.35f),
            ["HL_Bulb"] = Glow("HiFi_BulbHall", new Color(1f, 0.92f, 0.80f), 4000f, 0.5f),
            ["HL_Wood"] = TexMat("HiFi_DenWood", "cherry_veneer", new Color(0.414f, 0.29f, 0.34f), 1.0f, 0.45f),   // the house's mahogany (den, foyer)
            ["HL_Black"] = Plain("HiFi_HallUrn", new Color(0.06f, 0.035f, 0.035f), 0.7f),                       // black lacquer, a little red (film 10819)
            ["HL_Soil"] = Plain("HiFi_HallSoil", new Color(0.22f, 0.16f, 0.12f), 0.05f),
            ["HL_Gilt"] = Plain("HiFi_Gilt", new Color(0.60f, 0.45f, 0.21f), 0.42f, 0.55f),
            ["HL_Mat"] = Plain("HiFi_HallMat", new Color(0.90f, 0.87f, 0.80f), 0.1f),
            ["HL_Candle"] = Plain("HiFi_HallCandle", new Color(0.70f, 0.08f, 0.09f), 0.45f) });
        if (g == null) return;
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            r.gameObject.isStatic = true;
            string mn = r.sharedMaterial != null ? r.sharedMaterial.name : "";
            if (mn.StartsWith("HiFi_Shade") || mn.StartsWith("HiFi_Bulb")) r.shadowCastingMode = ShadowCastingMode.Off;   // the sconce's light sits inside
        }
        // the purchased plants (gitignored): the poinsettias in the urns and the brass pot, the ficus in its (brass) planter
        var pa = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Purchased/HallPlants.glb");
        if (pa == null) Debug.Log("Hall: Assets/Purchased/HallPlants.glb not present: urns and pot left empty");
        else
        {
            var pg = (GameObject)Object.Instantiate(pa, root.transform); pg.name = "HallPlants_HiFi"; pg.transform.localPosition = Vector3.zero;
            foreach (var c in pg.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
            var brass = BrassMat();
            foreach (var r in pg.GetComponentsInChildren<MeshRenderer>())
            {
                var ms = r.sharedMaterials;
                for (int i = 0; i < ms.Length; i++) if (ms[i] != null && ms[i].name.StartsWith("PP_Pot")) ms[i] = brass;   // the film's ribbed brass planter (410)
                r.sharedMaterials = ms; r.gameObject.isStatic = true;
            }
        }
        // the sconces' lights: point lights at the bulbs (spec/dressing/hall.json sconces), 2700 K, shadowed like the house's lamps
        var fx = Child(root, "HallFixtures"); var sc = D["sconces"];
        float yb = (float)sc["glass_bottom"] + 0.075f; int nl = 0;
        foreach (var q in sc["at"])
        {
            var w = D["walls"][(string)q["wall"]]; float s = (float)q["s"], f = (float)w["face"], side = (float)w["room_side"];
            bool ax = (string)w["axis"] == "x"; float x = ax ? f + side * 0.13f : s, z = ax ? s : f + side * 0.13f;
            var l = new GameObject("HallSconce_" + nl++).AddComponent<Light>(); l.transform.SetParent(fx.transform, false);
            l.transform.position = new Vector3(x, yb, -z); l.type = LightType.Point; l.range = 7f;
            l.gameObject.AddComponent<HDAdditionalLightData>();
            l.lightUnit = LightUnit.Lumen; l.intensity = (float)sc["lumens"] * HallSconceScale; l.useColorTemperature = true; l.colorTemperature = (float)sc["kelvin"];
            l.shadows = LightShadows.Soft;
        }
        // no light without a fixture: the sconces replace the halls' generic ceiling lamps (as the den's lamps replaced Light_den)
        foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                     .Where(t => t.name == "Light_hall_end" || t.name == "Light_hall_corridor" || t.name == "Light_hall_corridor_south").ToList())
            Object.DestroyImmediate(t.gameObject);
        var col = Child(root, "HallColliders"); int n = 0;
        foreach (var c in D["colliders"])
        {
            float x0 = (float)c["x"][0], x1 = (float)c["x"][1], z0 = (float)c["z"][0], z1 = (float)c["z"][1], y0 = (float)c["y"][0], y1 = (float)c["y"][1];
            var o = new GameObject("HallCollider_" + (string)c["name"]); o.transform.SetParent(col.transform, false); o.isStatic = true;
            o.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2, -(z0 + z1) / 2);
            o.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, y1 - y0, z1 - z0); n++;
        }
        HallArches(root, D);
        Debug.Log($"Hall: dressing placed, {nl} sconce lights, {n} colliders");
    }

    // The hall's arches (tools/house/hifi_hall_arches.py -> HallArches.glb; changes/2026-10-17-upstairs-arches.json): B and C on their
    // cuts (the stepped grey-box slices stay as colliders, their renderers off), A the gallery's elliptical header (dressing above head
    // height). Painted faces take the hall's paint, papered ones the stair well's damask (triplanar: the pattern runs on from the walls).
    static void HallArches(GameObject root, JObject D)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/finishes.json"));
        var paint = DressMat(JObject.Parse(File.ReadAllText(fp))["rooms"]["hall_corridor"]["upper"], "Paint_hall_corridor");
        var paper = Dress != null ? Wallpaper(Dress["walls"]) : mWall;
        var g = PlaceHiFi(root, 0f, "HallArches", new Dictionary<string, Material> {
            ["AR_Paint"] = paint, ["AR_Paper"] = paper, ["AR_SoffitB"] = HallBakedMat("HallArches", "SoffitB"), ["AR_SoffitC"] = HallBakedMat("HallArches", "SoffitC") });
        if (g == null) return;
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        // the stepped slices of the two cut arches: renderers off (colliders kept for walking)
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))))["upstairs"];
        int hid = 0;
        foreach (var o in geo["openings"].Where(o => (string)o["kind"] == "arch" && o["spring"] != null && o["spring"].Type != JTokenType.Null))
        {
            float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"];
            var box = new Bounds(new Vector3((lo + hi) / 2, 2.2f, -c), new Vector3(hi - lo + 0.02f, 1.0f, 0.3f));
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>().Where(r => r.name == "Arch_Spandrel" && box.Intersects(r.bounds))) { r.enabled = false; hid++; }
            // the floor under the arch (a plain plate cell in the wall's thickness, grey between the runner's legs): the hall's wood
            var wood = root.GetComponentsInChildren<MeshRenderer>().FirstOrDefault(r => r.name == "Floor_hall_corridor")?.sharedMaterial;
            var under = new Bounds(new Vector3((lo + hi) / 2, -0.1f, -c), new Vector3(hi - lo - 0.01f, 0.1f, 0.12f));
            if (wood != null) foreach (var r in root.GetComponentsInChildren<MeshRenderer>().Where(r => r.name == "FloorPlate" && under.Intersects(r.bounds))) r.sharedMaterial = wood;
        }
        // the gallery's back wall is the stair well's (film 2085 / 2687: damask over the white wainscot), not the hall's teal
        int papered = 0; var a = D["arch_a"];
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>().Where(r => r.name == "Wall" && r.sharedMaterial == paint))
        {
            var b = r.bounds;
            if (b.min.z > -7.79f && b.max.z < -7.69f && b.max.x <= (float)a["x"][1] + 0.07f && b.min.x >= 3.8f) { r.sharedMaterial = paper; papered++; }
        }
        Debug.Log($"HallArches: placed, {hid} grey-box arch slices hidden, {papered} gallery wall pieces papered");
    }

    // HDRP Lit on the artist pipeline's maps (Assets/Textures/Generated/<model>/<part>_{base,mask,normal,detail}.png + <part>.json)
    // ponytail: a copy of the arch agent's SpecGreybox.BakedMat (not in the repo yet); use theirs once it lands
    static Material HallBakedMat(string model, string part)
    {
        string dir = $"Assets/Textures/Generated/{model}/{part}";
        Texture2D Tex(string map, bool srgb, bool normal = false)
        {
            string p = $"{dir}_{map}.png";
            if (AssetImporter.GetAtPath(p) is TextureImporter ti && (ti.sRGBTexture != srgb || (ti.textureType == TextureImporterType.NormalMap) != normal || ti.anisoLevel != 8))
            { ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default; ti.sRGBTexture = srgb; ti.anisoLevel = 8; ti.mipmapEnabled = true; ti.SaveAndReimport(); }
            var t = AssetDatabase.LoadAssetAtPath<Texture2D>(p); if (t == null) Debug.LogWarning("HallBakedMat: missing " + p); return t;
        }
        var m = Mat($"HiFi_{model}_{part}", Color.white);
        m.SetTexture("_BaseColorMap", Tex("base", true)); m.SetTexture("_MaskMap", Tex("mask", false));
        m.SetTexture("_NormalMap", Tex("normal", false, true)); m.SetFloat("_NormalScale", 1f); m.SetTexture("_DetailMap", Tex("detail", false));
        var js = JObject.Parse(File.ReadAllText(Path.GetFullPath($"{dir}.json")));
        m.SetTextureScale("_DetailMap", new Vector2((float)js["detail_tiling"][0], (float)js["detail_tiling"][1]));
        m.SetFloat("_DetailAlbedoScale", 1f); m.SetFloat("_DetailNormalScale", 0.6f); m.SetFloat("_DetailSmoothnessScale", 1f);
        m.SetFloat("_MetallicRemapMin", 0f); m.SetFloat("_MetallicRemapMax", 1f); m.SetFloat("_SmoothnessRemapMin", 0f); m.SetFloat("_SmoothnessRemapMax", 1f);
        m.SetFloat("_AORemapMin", 0f); m.SetFloat("_AORemapMax", 1f);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); EditorUtility.SetDirty(m); return m;
    }
}
