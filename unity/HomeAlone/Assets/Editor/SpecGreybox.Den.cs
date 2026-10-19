using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine.Rendering.HighDefinition;
using UnityEngine;
using UnityEngine.Rendering;

// The den (Oct 16 2026, TRIAL; changes/2026-10-16-den.json, DEVIATIONS 51-53). Its paint and wood floor come from
// spec/dressing/finishes.json like the dining room's; here: the windows with their valances and drapes (tools/house/hifi_den.py ->
// DenWindows.glb; the grey-box keeps the casing round each cut and hides its glass box), the built-in bookcase (DenBuiltins.glb),
// the Poly Haven pieces (tools/house/hifi_den_props.py -> DenProps.glb), and the walk-layer colliders from spec/dressing/den.json.
// The owned pack furniture (desk, chairs, lamps, side table) is placed by StoreProps (spec/dressing/store_props.json).
public static partial class SpecGreybox
{
    static void Den(GameObject root, float gy)
    {
        var fabric = SpecTexMat("HiFi_DenFabric", "spec/dressing/den_fabric.png");   // UV-mapped at the cut's repeat (hifi_den.py)
        fabric.SetFloat("_Smoothness", 0.1f); fabric.SetFloat("_DoubleSidedEnable", 1f); fabric.SetFloat("_CullMode", 0f);
        HDMaterial.ValidateMaterial(fabric);
        var tie = Mat("HiFi_DenTie", new Color(0.12f, 0.30f, 0.17f)); tie.SetFloat("_Smoothness", 0.35f);
        var w = PlaceHiFi(root, gy, "DenWindows", new Dictionary<string, Material> {
            ["DW_Glass"] = mGlass, ["DW_Brass"] = BrassMat(), ["DW_Fabric"] = fabric, ["DW_Tie"] = tie });
        // dark mahogany (film 2877's built-in): Poly Haven cherry_veneer (mean lin 0.747/0.433/0.230) tinted to lin ~0.105/0.030/0.022
        Material Glow(string n, Color c, float nits, float smooth)
        {   // a lamp shade or bulb: its own light at night (HouseNightMode darkens "HiFi_Shade*"/"HiFi_Bulb*" by day)
            var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetColor("_EmissiveColor", c * nits);
            UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); return m;
        }
        var leafM = Mat("HiFi_DenLeaf", new Color(0.06f, 0.20f, 0.06f)); var redB = Mat("HiFi_DenBractRed", new Color(0.62f, 0.03f, 0.05f)); var whiteB = Mat("HiFi_DenBractWhite", new Color(0.90f, 0.90f, 0.84f));
        foreach (var m in new[] { leafM, redB, whiteB }) { m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_CullMode", 0f); HDMaterial.ValidateMaterial(m); }
        var b = PlaceHiFi(root, gy, "DenBuiltins", new Dictionary<string, Material> {
            ["DB_Wood"] = TexMat("HiFi_DenWood", "cherry_veneer", new Color(0.414f, 0.29f, 0.34f), 1.0f, 0.45f),
            ["DB_Labels"] = SpecTexMat("HiFi_DenLabels", "spec/dressing/den_labels.png"),   // original box and tape art (tools/house/den_textures.py)
            ["DL_Brass"] = BrassMat(), ["DB_Foil"] = FoilMat(),
            ["DB_Leaf"] = leafM, ["DB_BractRed"] = redB, ["DB_BractWhite"] = whiteB,
            ["DL_ShadeOrange"] = Glow("HiFi_ShadeDenOrange", new Color(0.80f, 0.30f, 0.08f), 600f, 0.3f),
            ["DL_ShadeCream"] = Glow("HiFi_ShadeDenCream", new Color(0.92f, 0.88f, 0.78f), 900f, 0.2f),
            ["DL_ShadeWhite"] = Glow("HiFi_ShadeDenWhite", new Color(0.94f, 0.93f, 0.90f), 900f, 0.2f),
            ["DL_ShadeGreen"] = Glow("HiFi_ShadeDenGreen", new Color(0.05f, 0.40f, 0.12f), 150f, 0.85f),
            ["DL_Bulb"] = Glow("HiFi_BulbDen", new Color(1f, 0.92f, 0.80f), 4000f, 0.5f) });
        if (b != null)
            foreach (var r in b.GetComponentsInChildren<MeshRenderer>())
            {
                string mn = r.sharedMaterial != null ? r.sharedMaterial.name : "";
                if (mn.StartsWith("HiFi_Shade") || mn.StartsWith("HiFi_Bulb")) r.shadowCastingMode = ShadowCastingMode.Off;   // the lamp's light sits inside
            }
        DenLamps(root, gy);
        var p = PlaceHiFi(root, gy, "DenProps", null);
        if (p != null)   // Kevin's movie chair: oxblood leather with a leather sheen (user Oct 18; the colour is baked by hifi_den_props.py)
            // the sheen lives on a saved copy: set on the glTF importer's own material it was lost on every reimport (user Oct 19 08:54,
            // "what happened to the leather texture ... it looked good last night")
            foreach (var r in p.GetComponentsInChildren<MeshRenderer>())
            {
                var ms = r.sharedMaterials;
                for (int i = 0; i < ms.Length; i++)
                {
                    if (ms[i] == null || !ms[i].name.StartsWith("DP_ChairBurgundy") || !ms[i].HasProperty("roughnessFactor")) continue;
                    string path = $"Assets/Materials/Greybox/{ms[i].name.Replace('.', '_')}_Leather.mat";
                    AssetDatabase.DeleteAsset(path);
                    var leather = new Material(ms[i]); leather.SetFloat("roughnessFactor", 0.45f);
                    AssetDatabase.CreateAsset(leather, path); ms[i] = leather;
                }
                r.sharedMaterials = ms;
            }
        foreach (var g in new[] { w, b, p })
            if (g != null) foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/den.json"));
        if (!File.Exists(fp)) return;
        var col = Child(root, "DenColliders"); int n = 0;
        foreach (var c in JObject.Parse(File.ReadAllText(fp))["colliders"])
        {
            float x0 = (float)c["x"][0], x1 = (float)c["x"][1], z0 = (float)c["z"][0], z1 = (float)c["z"][1], y0 = (float)c["y"][0], y1 = (float)c["y"][1];
            var o = new GameObject("DenCollider_" + (string)c["name"]); o.transform.SetParent(col.transform, false); o.isStatic = true;
            o.transform.position = new Vector3((x0 + x1) / 2, gy + (y0 + y1) / 2, -(z0 + z1) / 2);
            o.AddComponent<BoxCollider>().size = new Vector3(x1 - x0, y1 - y0, z1 - z0); n++;
        }
        Debug.Log($"Den: {n} colliders");
    }

    // the TV's screen: black glass by default; DenTV (Assets/Scripts) writes a user clip into this render texture and lights it
    const string DenTvRT = "Assets/Textures/Greybox/DenTV.renderTexture";
    static Material DenScreen()
    {
        Directory.CreateDirectory("Assets/Textures/Greybox");
        var rt = AssetDatabase.LoadAssetAtPath<RenderTexture>(DenTvRT);
        // the render texture has the SCREEN's aspect (the patch over the JVC glass, ~0.646 x 0.455), so a 4:3 clip letterboxes (VideoAspectRatio.FitInside) instead of stretching
        if (rt != null && (rt.width != 768 || rt.height != 540)) { AssetDatabase.DeleteAsset(DenTvRT); rt = null; }
        if (rt == null) { rt = new RenderTexture(768, 540, 0) { name = "DenTV" }; AssetDatabase.CreateAsset(rt, DenTvRT); }
        var m = Mat("HiFi_DenScreen", new Color(0.02f, 0.025f, 0.025f)); m.SetFloat("_Smoothness", 0.25f);   // 0.9 mirrored the den lamps as two hot spots on the picture (user, Oct 16: "why is there a glare")
        m.SetTexture("_EmissiveColorMap", rt); m.SetColor("_EmissiveColor", Color.black);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); return m;
    }

    // the den's lamps as lights from their fixtures (spec/dressing/den.json lamps: positions, lumens, kelvin), 2700 K-ish, shadowed;
    // BakeLighting makes them Mixed (Night scenario); Daylight() moves them into the night layer (off by day) and removes Light_den
    public static float DenLampScale = 1f;   // calibration knob against film 2856-2941 (film_light_match.py --den-night)
    static void DenLamps(GameObject root, float gy)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/den.json"));
        if (!File.Exists(fp)) return;
        var g = Child(root, "DenFixtures");
        foreach (var kv in (JObject)JObject.Parse(File.ReadAllText(fp))["lamps"])
        {
            var q = kv.Value; float x = (float)q["at"][0], y = (float)q["at"][1], z = (float)q["at"][2];
            float ax = q["arm"] != null ? (float)q["arm"][0] : 0f, az = q["arm"] != null ? (float)q["arm"][1] : 0f, yb;
            if (q["shade"] != null) { float s0 = (float)q["shade"][2], s1 = (float)q["shade"][3]; yb = (kv.Key == "floor" ? 0f : y) + (s0 + s1) / 2f - (kv.Key == "floor" ? 0.06f : 0.03f); }
            else yb = y + 0.30f;   // the banker's lamp: under its shade
            var l = new GameObject("DenLamp_" + kv.Key).AddComponent<Light>(); l.transform.SetParent(g.transform, false);
            l.transform.position = new Vector3(x + ax, gy + yb, -(z + az)); l.type = LightType.Point; l.range = q["range"] != null ? (float)q["range"] : 7f;   // "range": a lamp's pool kept local (user Oct 18, the side lamp)
            l.gameObject.AddComponent<HDAdditionalLightData>();
            l.lightUnit = LightUnit.Lumen; l.intensity = (float)q["lumens"] * DenLampScale; l.useColorTemperature = true; l.colorTemperature = (float)q["kelvin"];
            l.shadows = LightShadows.Soft;
        }
    }

    // The video screen on the bought JVC set (store_props.json den_tv, placed by StoreProps): OUR curved patch over its glass, built
    // from rays against the fitted model (no part of the purchased mesh is copied), 1.2 cm in front of the glass (zfight-check:
    // overlays >= 1 cm proud; the glass is recessed 1.7-4.8 cm behind the bezel's face, so the patch stays behind the bezel), UVs 0..1
    // across the glass for DenTV's render texture. The rectangle is the glass's in the model (FBX: across -0.216..0.210 of +-0.233,
    // up 0.092..0.394 of 0.415), inset 6 mm so no ray lands on the bezel.
    static void DenScreenPatch()
    {
        var tv = Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None).FirstOrDefault(t => t.name == "den_tv");
        if (tv == null) { Debug.LogWarning("DenScreenPatch: no den_tv (pack missing?): no video screen"); return; }
        var rs = tv.GetComponentsInChildren<MeshRenderer>(); if (rs.Length == 0) return;
        var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
        float k = b.size.z / 0.466f, inset = 0.006f;
        float zc = b.center.z, hw = 0.213f * k - inset, y0 = b.min.y + 0.092f * k + inset, y1 = b.min.y + 0.394f * k - inset;
        var temp = rs.Select(r => { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; return mc; }).ToList();
        Physics.SyncTransforms();
        const int NU = 24, NV = 18; var P = new Vector3[(NU + 1) * (NV + 1)]; var uv = new Vector2[P.Length]; var ok = new bool[P.Length]; float deep = 0f; int nOk = 0;
        for (int j = 0; j <= NV; j++)
            for (int i = 0; i <= NU; i++)
            {
                float u = i / (float)NU, v = j / (float)NV, z = zc + hw - 2f * hw * u, y = y0 + (y1 - y0) * v;   // seen from the room, left = +z
                int q = j * (NU + 1) + i; uv[q] = new Vector2(u, v);
                var hits = Physics.RaycastAll(new Vector3(b.max.x + 0.1f, y, z), Vector3.left, 0.5f).Where(h => temp.Contains(h.collider)).OrderBy(h => h.distance).ToArray();
                if (hits.Length > 0 && b.max.x - hits[0].point.x > 0.012f) { P[q] = hits[0].point + Vector3.right * 0.012f; ok[q] = true; deep += b.max.x - hits[0].point.x; nOk++; }
                else P[q] = new Vector3(float.NaN, y, z);
            }
        foreach (var c in temp) Object.DestroyImmediate(c);
        if (nOk == 0) { Debug.LogWarning("DenScreenPatch: no glass found"); return; }
        float mean = deep / nOk;
        for (int q = 0; q < P.Length; q++) if (!ok[q]) P[q].x = b.max.x - mean + 0.012f;   // a missed ray: the glass's mean depth
        var tris = new System.Collections.Generic.List<int>();
        for (int j = 0; j < NV; j++)
            for (int i = 0; i < NU; i++)
            {
                int a = j * (NU + 1) + i, bq = a + 1, c = a + NU + 1, d = c + 1;
                tris.AddRange(new[] { a, c, bq, bq, c, d });
            }
        var go = new GameObject("DenTV_Screen"); go.transform.SetParent(tv, false);
        var loc = P.Select(p => go.transform.InverseTransformPoint(p)).ToArray();
        var m = new Mesh { name = "DenTV_Screen", vertices = loc, uv = uv, triangles = tris.ToArray() };
        m.RecalculateNormals();
        if (go.transform.TransformDirection(m.normals[m.normals.Length / 2]).x < 0) { m.triangles = m.triangles.Reverse().ToArray(); m.RecalculateNormals(); }   // face the room (+x)
        m.RecalculateBounds();
        go.AddComponent<MeshFilter>().sharedMesh = m;
        var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterial = DenScreen(); mr.shadowCastingMode = ShadowCastingMode.Off;
        var dtv = go.AddComponent<DenTV>(); dtv.target = AssetDatabase.LoadAssetAtPath<RenderTexture>(DenTvRT);
        Debug.Log($"DenScreenPatch: {nOk}/{P.Length} rays on the glass, mean depth {mean * 100:F1} cm behind the bezel face; screen {2 * hw:F3} x {y1 - y0:F3} m");
    }
}
