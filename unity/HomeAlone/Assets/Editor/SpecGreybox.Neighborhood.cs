using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// The neighbourhood, step 2 (Oct 20 2026, PREP: not yet built; RESUME section 2). Places what tools/house/nb_house.py, nb_street.py
// and nb_textures.py generate from spec/neighborhood.json:
//  - every kit house (Assets/Models/Neighborhood/<lot>.glb) at its lot grade: Tier 2 = LODGroup (LOD0 hero, LOD1 stand-in, culled
//    under 0.4 % of the screen), its NightGlow renderers switched by N, box colliders from <lot>_Collider (walkable Tier 2); Tier 3 =
//    LOD1 only, no colliders (not reachable)
//  - Street.glb (carriageway, kerbs, gutters, sidewalks, parkways, drives, walks, lawns, snow banks) with mesh colliders
//  - the film's acorn lamp posts (LampPost.glb, LODGroup) at street_layout.json "lamps", a 2700 K night light each; the two old
//    sphere-globe posts (SpecGreybox.Shell "LampPosts") are removed (walk note 2026-10-19T12:33 "style of light is wrong")
//  - parkway / lot trees (BareTrees.glb variants, as SpecGreybox.Trees) at street_layout.json "trees"
//  - the Murphys' C7 strings (<lot>_xmas.json) as SpecGreybox.Bulbs, five colours, night only
//  - hides the WinterNeighborhood's street, sidewalks, kerbs, houses and ground inside the generated extent (K still hides all of it)
// Materials are SHARED: one HDRP Lit per NB_<set>_<colour> (Assets/Materials/Neighborhood), the set's maps from
// Assets/Textures/Neighborhood/<set>/ on the GLB's metric UVs (tiling 1/tile_m), the palette colour as _BaseColor, GPU instancing on.
// OFF unless HA_NEIGHBORHOOD=1 (two other agents' builds are queued; this must not change their output).
public static partial class SpecGreybox
{
    static string NbRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "../../.."));
    static readonly Dictionary<string, Material> NbMats = new Dictionary<string, Material>();

    static Material NbMat(string name, JObject pal, JObject kt)
    {
        if (NbMats.TryGetValue(name, out var have)) return have;
        string dir = "Assets/Materials/Neighborhood"; if (!AssetDatabase.IsValidFolder(dir)) AssetDatabase.CreateFolder("Assets/Materials", "Neighborhood");
        string path = $"{dir}/{name}.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("HDRP/Lit")); AssetDatabase.CreateAsset(m, path); }
        m.enableInstancing = true;
        if (name == "NB_Glass") { m.SetColor("_BaseColor", new Color(0.02f, 0.025f, 0.03f)); m.SetFloat("_Smoothness", 0.95f); }
        else if (name == "NB_GlassLit" || name == "NB_LampGlobe")
        {
            var c = name == "NB_GlassLit" ? new Color(1f, 0.72f, 0.42f) : new Color(1f, 0.88f, 0.70f);
            m.SetColor("_BaseColor", c); m.SetColor("_EmissiveColor", c * (name == "NB_GlassLit" ? 120f : 4000f)); m.SetFloat("_Smoothness", 0.6f);
        }
        else
        {
            var k = name.Substring(3);
            var set = kt.Properties().Select(p => p.Name).OrderByDescending(s => s.Length).FirstOrDefault(s => k == s || k.StartsWith(s + "_"));
            var col = set != null && k.Length > set.Length ? k.Substring(set.Length + 1) : "";
            var rgb = pal[col] as JArray; var tint = rgb != null ? new Color((float)rgb[0], (float)rgb[1], (float)rgb[2]) : Color.white;
            if (set == "brick" && col == "red" || set == "roof_clay" || set == "asphalt") tint = Color.white;     // these scans keep their colour
            if (set == "roof_asphalt") tint = new Color(Mathf.Min(1, tint.r * 2.2f), Mathf.Min(1, tint.g * 2.2f), Mathf.Min(1, tint.b * 2.2f));
            m.SetColor("_BaseColor", tint);
            if (set != null)
            {
                string td = $"Assets/Textures/Neighborhood/{set}"; float tile = (float)kt[set]["tile_m"];
                var ni = AssetImporter.GetAtPath(td + "/normal.jpg") as TextureImporter;
                if (ni != null && ni.textureType != TextureImporterType.NormalMap) { ni.textureType = TextureImporterType.NormalMap; ni.SaveAndReimport(); }
                var mi = AssetImporter.GetAtPath(td + "/mask.png") as TextureImporter;
                if (mi != null && mi.sRGBTexture) { mi.sRGBTexture = false; mi.SaveAndReimport(); }
                m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(td + "/albedo.jpg"));
                m.SetTexture("_NormalMap", AssetDatabase.LoadAssetAtPath<Texture2D>(td + "/normal.jpg"));
                m.SetTexture("_MaskMap", AssetDatabase.LoadAssetAtPath<Texture2D>(td + "/mask.png"));
                m.SetTextureScale("_BaseColorMap", Vector2.one / tile);
                m.SetFloat("_UVBase", 0f); m.SetFloat("_Smoothness", (float)kt[set]["smooth"]);
                m.SetFloat("_SmoothnessRemapMax", name.Contains("wet") ? 0.92f : (float)kt[set]["smooth"] + 0.1f);
            }
        }
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); EditorUtility.SetDirty(m);
        NbMats[name] = m; return m;
    }

    static void Neighborhood(GameObject ext, float gy)
    {
        if (System.Environment.GetEnvironmentVariable("HA_NEIGHBORHOOD") != "1") { Debug.Log("Neighborhood: off (HA_NEIGHBORHOOD != 1)"); return; }
        string nb = "Assets/Models/Neighborhood";
        var man = JObject.Parse(File.ReadAllText(Path.Combine(NbRoot, "spec/neighborhood.json")));
        var lay = JObject.Parse(File.ReadAllText(Path.Combine(Application.dataPath, "Models/Neighborhood/street_layout.json")));
        var kt = JObject.Parse(File.ReadAllText(Path.Combine(Application.dataPath, "Textures/Neighborhood/kit_textures.json")));
        var pal = (JObject)man["kit_palette"]; var lv = (JObject)lay["levels_rel_gy"]; var grade = (JObject)lv["lot_grade"];
        var root = new GameObject("Neighborhood"); root.transform.SetParent(ext.transform, true);
        int houses = 0, glows = 0; long tris2 = 0, tris3 = 0;

        GameObject Inst(string asset, string n, Vector3 pos)
        {
            var a = AssetDatabase.LoadAssetAtPath<GameObject>($"{nb}/{asset}.glb"); if (a == null) { Debug.LogWarning($"Neighborhood: {asset}.glb missing"); return null; }
            var g = (GameObject)Object.Instantiate(a); g.name = n; g.transform.SetParent(root.transform, false); g.transform.position = pos;
            foreach (var r in g.GetComponentsInChildren<MeshRenderer>(true))
                r.sharedMaterials = r.sharedMaterials.Select(mm => mm != null && mm.name.StartsWith("NB_") ? NbMat(mm.name.Split(' ')[0], pal, kt) : mm).ToArray();
            return g;
        }

        // ---- houses
        foreach (JObject e in man["parcels"])
        {
            string id = (string)e["id"]; int tier = (int)e["tier"];
            if (id == "lot_A0" || (e["kit"] == null && e["kit_auto"] == null)) continue;
            float g0 = grade[id] != null ? (float)grade[id] : (float)grade[(string)e["side"] == "across_lincoln" ? "tier3_B" : "tier3_A"];
            var h = Inst(id, "House " + id, new Vector3(0f, gy + g0, 0f)); if (h == null) continue; houses++;
            Renderer[] Part(string suffix) => h.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.name.EndsWith(suffix)).ToArray();
            var l0 = Part("_LOD0"); var l1 = Part("_LOD1");
            foreach (var r in Part("_Collider")) { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; if (tier > 2) Object.DestroyImmediate(mc); Object.DestroyImmediate(r); }
            foreach (var r in Part("_NightGlow")) { r.shadowCastingMode = ShadowCastingMode.Off; ShellGlow.Add(r); glows++; }
            var lg = h.AddComponent<LODGroup>(); lg.fadeMode = LODFadeMode.CrossFade; lg.animateCrossFading = true;
            lg.SetLODs(tier <= 2 && l0.Length > 0 ? new[] { new LOD(0.10f, l0), new LOD(0.004f, l1) } : new[] { new LOD(0.004f, l1) });
            lg.RecalculateBounds();
            foreach (var r in l0) tris2 += r.GetComponent<MeshFilter>().sharedMesh.triangles.Length / 3;
            foreach (var r in tier <= 2 ? new Renderer[0] : l1) tris3 += r.GetComponent<MeshFilter>().sharedMesh.triangles.Length / 3;
            foreach (var t in h.GetComponentsInChildren<Transform>(true)) t.gameObject.isStatic = !t.name.EndsWith("_NightGlow");
            // the C7 strings (film 11581: red, green, amber, blue, white), night only
            var xp = Path.Combine(Application.dataPath, $"Models/Neighborhood/{id}_xmas.json");
            if (File.Exists(xp))
            {
                var bl = (JArray)JObject.Parse(File.ReadAllText(xp))["bulbs"];
                Color[] cs = { new Color(1f, 0.10f, 0.05f), new Color(0.15f, 0.9f, 0.2f), new Color(1f, 0.5f, 0.08f), new Color(0.2f, 0.35f, 1f), new Color(1f, 0.85f, 0.65f) };
                for (int c = 0; c < 5; c++)
                {
                    var pts = bl.Where(b => (int)b[3] == c).Select(b => new Vector3((float)b[0], gy + g0 + (float)b[1], -(float)b[2])).ToList();
                    if (pts.Count == 0) continue;
                    var go = Bulbs(root, $"XmasC7_{id}_{c}", pts, 0.05f, XmasBulb($"NB_C7_{c}", cs[c], 2200f));
                    foreach (var r in go.GetComponentsInChildren<MeshRenderer>()) ShellGlow.Add(r);
                }
            }
        }
        // ---- the street (walkable): mesh colliders on every surface
        var st = Inst("Street", "Street", new Vector3(0f, gy, 0f));
        if (st != null)
            foreach (var r in st.GetComponentsInChildren<MeshRenderer>(true))
            { r.gameObject.isStatic = true; var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; }
        // ---- lamp posts: the film's acorn post replaces the sphere-globe posts
        var old = ext.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == "LampPosts");
        if (old != null) { Object.DestroyImmediate(old.gameObject); ShellLights.RemoveAll(l => l == null); ShellGlow.RemoveAll(r => r == null); }
        int lamps = 0;
        foreach (JObject L in lay["lamps"])
        {
            var p = new Vector3((float)L["x"], gy + (float)lv["walk"], -(float)L["z"]);
            var g = Inst("LampPost", "Acorn lamp post", p); if (g == null) break; lamps++;
            var post = g.GetComponentsInChildren<MeshRenderer>(true);
            var lod = g.AddComponent<LODGroup>();
            lod.SetLODs(new[] { new LOD(0.06f, post.Where(r => r.name.EndsWith("LOD0")).ToArray<Renderer>()), new LOD(0.003f, post.Where(r => r.name.EndsWith("LOD1")).ToArray<Renderer>()) });
            foreach (var r in post.Where(r => r.name.Contains("Globe"))) { r.shadowCastingMode = ShadowCastingMode.Off; ShellGlow.Add(r); }
            var cap = g.AddComponent<CapsuleCollider>(); cap.radius = 0.12f; cap.height = 4.2f; cap.center = new Vector3(0, 2.1f, 0);
            ShellLights.Add(NightLight(g, "LampPostLight", p + Vector3.up * 3.85f, 2400f, 16f));
        }
        // ---- trees (BareTrees.glb, as SpecGreybox.Trees): one LODGroup each
        var ta = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/BareTrees.glb"); int trees = 0;
        if (ta != null)
        {
            var mf = ta.GetComponentsInChildren<MeshFilter>(true).GroupBy(f => f.name).ToDictionary(q => q.Key, q => q.First().sharedMesh);
            var rough = BarkMat("HiFi_BTBarkRough", "bark_willow_02", new Color(0.62f, 0.60f, 0.58f)); var brown = BarkMat("HiFi_BTBarkBrown", "bark_brown_02", new Color(0.70f, 0.66f, 0.62f));
            var snow = Mat("HiFi_BTSnow", new Color(0.80f, 0.83f, 0.86f));
            var tr = new GameObject("Neighborhood trees"); tr.transform.SetParent(root.transform, false);
            foreach (JObject t in lay["trees"])
            {
                string v = (string)t["variant"]; if (!mf.ContainsKey(v + "_LOD0")) continue;
                float x = (float)t["x"], z = (float)t["z"], y = gy + (x > 36.3f ? (float)lv["lawn_B"] : (float)lv["lawn_A"]);
                float sc = (float)t["h_m"] / Mathf.Max(1f, mf[v + "_LOD0"].bounds.size.y - 0.35f);
                var g = new GameObject("Tree " + v); g.transform.SetParent(tr.transform, false);
                g.transform.SetPositionAndRotation(new Vector3(x, y, -z), Quaternion.Euler(0, (float)t["yaw"], 0)); g.transform.localScale = Vector3.one * sc;
                var lods = new LOD[3]; float[] hh = { 0.55f, 0.18f, 0.012f };
                for (int l = 0; l < 3; l++)
                {
                    var c = new GameObject($"{v}_LOD{l}"); c.transform.SetParent(g.transform, false); c.AddComponent<MeshFilter>().sharedMesh = mf[$"{v}_LOD{l}"];
                    var r = c.AddComponent<MeshRenderer>(); r.sharedMaterials = new[] { v.StartsWith("oak") || v.StartsWith("ash") ? rough : brown, snow };
                    c.isStatic = true; lods[l] = new LOD(hh[l], new Renderer[] { r });
                }
                var lg = g.AddComponent<LODGroup>(); lg.SetLODs(lods); lg.RecalculateBounds(); g.isStatic = true; trees++;
                var cc = g.AddComponent<CapsuleCollider>(); cc.radius = 0.4f / sc; cc.height = 4f / sc; cc.center = new Vector3(0, 2f / sc, 0);
            }
        }
        // ---- the old WinterNeighborhood inside the generated extent: renderers and colliders off (K still toggles the rest)
        int off = 0; var hood = ext.transform.Find("WinterNeighborhood");
        if (hood != null)
            foreach (var r in hood.GetComponentsInChildren<Renderer>(true))
            {
                var b = r.bounds; bool streetish = new[] { "Lincoln", "sidewalk", "curb", "Sidewalk", "Neighbor", "snowy lots", "Mature bare", "Driveway" }.Any(s => r.name.Contains(s) || r.transform.parent.name.Contains(s));
                bool inside = b.center.x > -60f && b.center.x < 100f && Mathf.Abs(-b.center.z) < 150f;
                if (streetish && inside || r.name.Contains("snowy lots"))
                { r.enabled = false; foreach (var c in r.GetComponents<Collider>()) c.enabled = false; off++; }
            }
        Debug.Log($"Neighborhood: {houses} houses (Tier 2 LOD0 {tris2} tris, Tier 3 {tris3} tris), {glows} night glows, {lamps} acorn lamps, {trees} trees, {NbMats.Count} shared materials, {off} WinterNeighborhood renderers off");
    }
}
