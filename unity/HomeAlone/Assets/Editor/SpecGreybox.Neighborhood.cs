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
            var rc = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Textures/Neighborhood/room_cards.png");
            if (name == "NB_GlassLit" && rc != null)   // step 3: lit rooms behind the windows (nb_textures.room_cards; the GLB's window UVs pick a quadrant)
            {
                if (AssetImporter.GetAtPath("Assets/Textures/Neighborhood/room_cards.png") is TextureImporter ri && ri.wrapMode != TextureWrapMode.Clamp) { ri.wrapMode = TextureWrapMode.Clamp; ri.SaveAndReimport(); }
                m.SetColor("_BaseColor", Color.white); m.SetTexture("_BaseColorMap", rc); m.SetTexture("_EmissiveColorMap", rc);
                m.SetColor("_EmissiveColor", new Color(1f, 0.92f, 0.82f) * 300f); m.SetTextureScale("_BaseColorMap", Vector2.one);
            }
        }
        else if (name.StartsWith("NB_car_"))   // step 3 street life: gloss car paint, chrome, tyres, lamps (nb_life.py); plain colours, no maps
        {
            var col = name.Substring(7); var rgb = pal[col] as JArray; var c = rgb != null ? new Color((float)rgb[0], (float)rgb[1], (float)rgb[2]) : Color.grey;
            m.SetColor("_BaseColor", c); m.SetFloat("_Smoothness", col == "tyre" ? 0.25f : col == "chrome" ? 0.9f : 0.78f); m.SetFloat("_Metallic", col == "chrome" ? 1f : 0f);
        }
        else if (name == "NB_Beacon")   // the police cars' red beacon domes (film 11581), night only (ShellGlow)
        { var c = new Color(1f, 0.06f, 0.03f); m.SetColor("_BaseColor", c); m.SetColor("_EmissiveColor", c * 3000f); m.SetFloat("_Smoothness", 0.7f); }
        else if (name == "NB_TreeCard")   // Tier 4 treeline: alpha-clipped bare-tree silhouettes (nb_textures.tree_cards), both sides
        {
            string tp = "Assets/Textures/Neighborhood/tree_cards.png";
            if (AssetImporter.GetAtPath(tp) is TextureImporter ti && (!ti.alphaIsTransparency || ti.wrapMode != TextureWrapMode.Clamp)) { ti.alphaIsTransparency = true; ti.wrapMode = TextureWrapMode.Clamp; ti.mipmapEnabled = true; ti.SaveAndReimport(); }
            m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tp)); m.SetColor("_BaseColor", new Color(0.8f, 0.8f, 0.82f));
            m.SetFloat("_AlphaCutoffEnable", 1f); m.SetFloat("_AlphaCutoff", 0.35f); m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_Smoothness", 0.1f);
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

    // The walk boundary (user, Oct 20): invisible walls along life_layout.json "boundary" (our lot, the stretch of Lincoln in front of
    // Marley's, ours and the Murphys', their front yards and porches), 8 m tall, 0.3 m thick; NOT under the Neighborhood root, so K's
    // property view does not drop it. Then the boundary check: a capsule (r 0.3, 0.6-1.6 m over the ground) cast outward across the
    // middle of every edge from 1.5 m inside must hit within 3 m (BLOCKED, as it should be), and every hero stays reachable (the LINCOLN,
    // OUR SIDEWALK and B SIDEWALK walk-test routes).
    static void WalkBoundary(GameObject ext, float gy, JObject ll)
    {
        var B = ((JArray)ll["boundary"]).Select(q => new Vector2((float)q[0], (float)q[1])).ToList(); if (B.Count < 3) return;
        var root = new GameObject("Walk boundary (neighbourhood)"); root.transform.SetParent(ext.transform, true);
        float area = 0; for (int i = 0; i < B.Count; i++) { var a = B[i]; var b = B[(i + 1) % B.Count]; area += a.x * b.y - b.x * a.y; }
        for (int i = 0; i < B.Count; i++)
        {
            var a = B[i]; var b = B[(i + 1) % B.Count]; var m = (a + b) / 2f; var d = b - a;
            var w = new GameObject($"Walk boundary {i}"); w.transform.SetParent(root.transform, false);
            w.transform.SetPositionAndRotation(new Vector3(m.x, gy, -m.y), Quaternion.LookRotation(new Vector3(d.x, 0, -d.y).normalized, Vector3.up));
            var bc = w.AddComponent<BoxCollider>(); bc.size = new Vector3(0.3f, 12f, d.magnitude + 0.3f); w.isStatic = true;
        }
        Physics.SyncTransforms(); int blocked = 0; var leaks = new List<string>();
        for (int i = 0; i < B.Count; i++)
        {
            var a = B[i]; var b = B[(i + 1) % B.Count]; var d = (b - a).normalized; var nOut = area > 0 ? new Vector2(d.y, -d.x) : new Vector2(-d.y, d.x);   // spec frame
            foreach (float t in new[] { 0.25f, 0.5f, 0.75f })
            {
                var p = Vector2.Lerp(a, b, t) - nOut * 1.5f; var start = new Vector3(p.x, gy + 20f, -p.y);
                if (!Physics.Raycast(start, Vector3.down, out var g, 40f)) { leaks.Add($"edge {i} t {t}: no ground inside"); continue; }
                if (g.collider.name.EndsWith("_Collider")) { blocked++; continue; }   // inside a hero house's walls: nobody stands there
                var dir = new Vector3(nOut.x, 0, -nOut.y);
                if (Physics.CapsuleCast(g.point + Vector3.up * 0.6f, g.point + Vector3.up * 1.6f, 0.3f, dir, out var hit, 3f)) blocked++;
                else leaks.Add($"edge {i} at ({p.x:F1}, {p.y:F1})");
            }
        }
        Debug.Log($"Neighborhood boundary check: {B.Count} edges, {blocked} of {3 * B.Count} outward legs BLOCKED{(leaks.Count > 0 ? "; OPEN: " + string.Join("; ", leaks) : " (all, as they must be)")}");
        if (leaks.Count > 0) Debug.LogError("Neighborhood boundary check FAIL: " + string.Join("; ", leaks));
    }

    // the beds' boxwood scan (tools/house/scan_shrubs.py -> the gitignored Assets/Purchased/Sketchfab/ScanShrubs, CC-BY, CREDITS.md):
    // its three lumpy variants (one mesh each: GPU instancing on the shared leaf + snow-card materials SpecGreybox.Shell makes), each plant
    // sized w x d x h and turned, an LODGroup culling it under 0.5 % of the screen; without the download, nothing (logged)
    static void ScanShrubRow(GameObject root, List<(Vector3 p, float sx, float sz, float h, string lot)> plants)
    {
        const string SS = "Assets/Purchased/Sketchfab/ScanShrubs/";
        var sa = AssetDatabase.LoadAssetAtPath<GameObject>(SS + "ScanShrubs.glb");
        if (sa == null || plants.Count == 0) { Debug.Log($"Neighborhood: scan shrubs {(sa == null ? "not present (download)" : "none")}"); return; }
        var meshes = sa.GetComponentsInChildren<MeshFilter>(true).Select(f => f.sharedMesh).Distinct().ToList();
        var leaf = LeafMat("HiFi_ExtShrubBoxwood", Color.white, SS, "bux_albedo.png", "bux_normal.png", "bux_mask.png");
        var snow = LeafMat("HiFi_ExtShrubBoxwoodSnow", Color.white, SS, "bux_albedo_snow.png", "bux_normal.png", "bux_mask.png");
        leaf.enableInstancing = true; snow.enableInstancing = true;
        var holder = new GameObject("Scan shrubs (boxwood)"); holder.transform.SetParent(root.transform, false);
        var rnd = new System.Random(11581); int k = 0;
        foreach (var (p, sx, sz2, h, lot) in plants)
        {
            var m = meshes[k++ % meshes.Count]; var sz = m.bounds.size; float aspect = sz.y / Mathf.Max(0.01f, (sz.x + sz.z) / 2f);
            var g = new GameObject($"Shrub {lot}"); g.transform.SetParent(holder.transform, false);
            g.transform.SetPositionAndRotation(p + Vector3.down * 0.03f, Quaternion.Euler(0, ((float)rnd.NextDouble() - 0.5f) * 20f, 0));   // +-10 deg: the sizes stay on their axes (the bulbs ride the kit's ellipsoid)
            g.transform.localScale = new Vector3(sx / Mathf.Max(0.01f, sz.x), h / Mathf.Max(0.01f, sz.y), sz2 / Mathf.Max(0.01f, sz.z));
            g.AddComponent<MeshFilter>().sharedMesh = m; var r = g.AddComponent<MeshRenderer>(); r.sharedMaterials = new[] { leaf, snow };
            var lg = g.AddComponent<LODGroup>(); lg.fadeMode = LODFadeMode.None; lg.SetLODs(new[] { new LOD(0.005f, new Renderer[] { r }) }); g.isStatic = true;
        }
        Debug.Log($"Neighborhood: {plants.Count} scan shrubs ({meshes.Count} variants, instanced)");
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
        int houses = 0, glows = 0; long tris2 = 0, tris3 = 0; var scanShrubs = new List<(Vector3 p, float sx, float sz, float h, string lot)>(); var allBulbs = Enumerable.Range(0, 5).Select(_ => new List<Vector3>()).ToArray();   // scanShrubs: world x / z sizes

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
            foreach (var r in Part("_Collider")) { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; if (tier > 2 || e["walkable"]?.Value<bool>() != true) Object.DestroyImmediate(mc); Object.DestroyImmediate(r); }   // step 3: only the heroes (Marley's, the Murphys') collide; the backdrop sits past the walk boundary
            foreach (var r in Part("_NightGlow")) { r.shadowCastingMode = ShadowCastingMode.Off; ShellGlow.Add(r); glows++; }
            var lg = h.AddComponent<LODGroup>(); lg.fadeMode = LODFadeMode.CrossFade; lg.animateCrossFading = true;
            bool hero = e["walkable"]?.Value<bool>() == true;   // backdrop kit houses (lot_A-1, B-1, B+1) drop to their stand-in sooner
            lg.SetLODs(tier <= 2 && l0.Length > 0 ? new[] { new LOD(hero ? 0.10f : 0.25f, l0), new LOD(0.004f, l1) } : new[] { new LOD(0.004f, l1) });
            lg.RecalculateBounds();
            foreach (var r in l0) tris2 += r.GetComponent<MeshFilter>().sharedMesh.triangles.Length / 3;
            foreach (var r in tier <= 2 ? new Renderer[0] : l1) tris3 += r.GetComponent<MeshFilter>().sharedMesh.triangles.Length / 3;
            foreach (var t in h.GetComponentsInChildren<Transform>(true)) t.gameObject.isStatic = !t.name.EndsWith("_NightGlow");
            // the kit's night lights (the Murphys' porch lamp, porch ceiling, the strands' glow on the facade: film 11581), unshadowed, night layer
            if (e["kit"]?["night_lights"] is JArray nls)
                foreach (JObject nl in nls)
                    ShellLights.Add(NightLight(h, $"NightLight_{id}", new Vector3((float)nl["x"], gy + g0 + (float)nl["y"], -(float)nl["z"]), (float)nl["lm"], (float)nl["range"]));
            // shrubs from the beds' boxwood scan: the kit's lit foundation shrubs (scan_shrubs) and plain foundation shrubs
            var kitObj = (e["kit"] ?? e["kit_auto"]) as JObject;
            if (kitObj?["scan_shrubs"]?.Value<bool>() == true && kitObj["xmas"]?["shrubs"] is JArray ks)
                foreach (JObject q in ks) scanShrubs.Add((new Vector3((float)q["x"], gy + g0, -(float)q["z"]), 2f * (float)q["rx"], 2f * (float)q["rz"], (float)q["h"], id));
            if (kitObj?["foundation_shrubs"] is JArray fs)
                foreach (JObject q in fs) scanShrubs.Add((new Vector3((float)q["x"], gy + g0, -(float)q["z"]), 2f * (float)q["rx"], 2f * (float)q["rz"], (float)q["h"], id));
            // the C7 strings (film 11581: red, green, amber, blue, white), night only
            var xp = Path.Combine(Application.dataPath, $"Models/Neighborhood/{id}_xmas.json");
            if (File.Exists(xp))
            {
                var bl = (JArray)JObject.Parse(File.ReadAllText(xp))["bulbs"];
                Color[] cs = { new Color(1f, 0.10f, 0.05f), new Color(0.15f, 0.9f, 0.2f), new Color(1f, 0.5f, 0.08f), new Color(0.2f, 0.35f, 1f), new Color(1f, 0.85f, 0.65f) };
                for (int c = 0; c < 5; c++)   // collected for every lot, one mesh per colour below (5 draws for the whole street)
                    allBulbs[c].AddRange(bl.Where(b => (int)b[3] == c).Select(b => new Vector3((float)b[0], gy + g0 + (float)b[1], -(float)b[2])));
            }
        }
        {
            Color[] cs = { new Color(1f, 0.10f, 0.05f), new Color(0.15f, 0.9f, 0.2f), new Color(1f, 0.5f, 0.08f), new Color(0.2f, 0.35f, 1f), new Color(1f, 0.85f, 0.65f) };
            for (int c = 0; c < 5; c++)
            {
                if (allBulbs[c].Count == 0) continue;
                var go = Bulbs(root, $"XmasC7_{c}", allBulbs[c], 0.075f, XmasBulb($"NB_C7_{c}", cs[c], 7000f));   // C9-sized and bright: at 30-40 m the 5 cm / 2200-nit bulbs vanished (11581 reads them as bright strands)
                foreach (var r in go.GetComponentsInChildren<MeshRenderer>()) { r.shadowCastingMode = ShadowCastingMode.Off; ShellGlow.Add(r); }
            }
        }
        // ---- the street (walkable): mesh colliders on every surface
        var st = Inst("Street", "Street", new Vector3(0f, gy, 0f));
        if (st != null)
            foreach (var r in st.GetComponentsInChildren<MeshRenderer>(true))
            { r.gameObject.isStatic = true; var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; }
        // ---- Lincoln's road, kerbs and sidewalks follow the weather with our own drive and walk (WetGround: Sunny / Overcast / Night sets,
        //      triplanar, so the street's own UVs don't matter); by reflection: WetGround.cs is another job's script
        if (st != null)
        {
            var wgT = UnityEditor.TypeCache.GetTypesDerivedFrom<MonoBehaviour>().FirstOrDefault(t => t.Name == "WetGround");
            var wg = wgT != null ? Object.FindAnyObjectByType(wgT, FindObjectsInactive.Include) : null;
            if (wg != null)
            {
                var asph = (Material[])wgT.GetField("asphalt").GetValue(wg); var conc = (Material[])wgT.GetField("concrete").GetValue(wg);
                var regs = new List<Renderer>();
                foreach (var r in st.GetComponentsInChildren<MeshRenderer>(true))
                {
                    var ms = r.sharedMaterials; bool hit = false;
                    for (int i = 0; i < ms.Length; i++)
                        if (ms[i] == null) continue;
                        else if (ms[i].name.StartsWith("NB_asphalt")) { ms[i] = asph[0]; hit = true; }
                        else if (ms[i].name.StartsWith("NB_concrete_walk")) { ms[i] = conc[0]; hit = true; }
                    if (hit) { r.sharedMaterials = ms; regs.Add(r); }
                }
                var f = wgT.GetField("renderers"); f.SetValue(wg, ((Renderer[])f.GetValue(wg)).Concat(regs).ToArray());
                Debug.Log($"Neighborhood: {regs.Count} street renderers follow WetGround");
            }
            else Debug.LogWarning("Neighborhood: no WetGround in the scene; the street stays wet");
        }
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
                var b = r.bounds; bool streetish = new[] { "Lincoln", "sidewalk", "curb", "Sidewalk", "Neighbor", "snowy lots", "Mature bare", "Driveway", "Utility pole", "Pole crossarm", "Overhead wire" }.Any(s => r.name.Contains(s) || r.transform.parent.name.Contains(s));
                bool inside = b.center.x > -60f && b.center.x < 100f && Mathf.Abs(-b.center.z) < 150f;
                if (streetish && inside || r.name.Contains("snowy lots"))
                { r.enabled = false; foreach (var c in r.GetComponents<Collider>()) c.enabled = false; r.name += " [nb-off]"; off++; }   // [nb-off]: PerfProbe's nbold variant turns them back on
            }
        // ---- step 3: street life (nb_life.py: the film's police cars at night, the bandits' van, a parked sedan, poles + wires, hydrant,
        //      the Murphys' mailbox and yard stakes) and the Tier 4 treeline + horizon ground
        int life = 0; var lp = Path.Combine(Application.dataPath, "Models/Neighborhood/life_layout.json");
        var src = File.Exists(lp) ? Inst("StreetLife", "StreetLife (prototypes)", Vector3.zero) : null;
        if (src != null)
        {
            var ll = JObject.Parse(File.ReadAllText(lp)); var lifeRoot = new GameObject("Street life"); lifeRoot.transform.SetParent(root.transform, false);
            GameObject Proto(string n) => src.GetComponentsInChildren<MeshRenderer>(true).FirstOrDefault(r => r.name == n)?.gameObject;
            float Level(JObject it)
            {
                float x = (float)it["x"]; string y = (string)it["y"];
                if (y == "walk") return (float)lv["walk"]; if (y != null && grade[y] != null) return (float)grade[y];
                return x > 30.62f && x < 41.3f ? (float)lv["road"] : x >= 41.3f ? (float)lv["lawn_B"] : (float)lv["lawn_A"];
            }
            // the film's vehicles (spec/vehicles.json, Editor/VehiclePrefabs.cs): prefabs rebuilt from the spec, each kind's scene (night/always) from it
            var vp = Path.Combine(NbRoot, "spec/vehicles.json"); var vspec = File.Exists(vp) ? (JObject)JObject.Parse(File.ReadAllText(vp))["kinds"] : null;
            if (vspec != null) VehiclePrefabs.Build();
            foreach (JObject it in ll["items"])
            {
                string kind = (string)it["kind"]; var pr = Proto(kind); if (pr == null) { Debug.LogWarning($"Neighborhood: no prototype {kind}"); continue; }
                var hd = it["heading"] as JArray; var d = hd != null ? new Vector3((float)hd[0], 0f, -(float)hd[1]) : Vector3.back;
                var holder = new GameObject($"{kind} ({(string)it["scene"] ?? "prop"})"); holder.transform.SetParent(lifeRoot.transform, false);
                holder.transform.SetPositionAndRotation(new Vector3((float)it["x"], gy + Level(it), -(float)it["z"]), Quaternion.LookRotation(-d, Vector3.up));
                // swap hook: a bought model at Assets/Purchased/Vehicles/<kind>.prefab (root at the ground contact, facing Unity +z, metres)
                // replaces the generated proxy; the night scene's beacon light and the collider follow it (decisions list: purchases)
                var bought = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Purchased/Vehicles/{kind}.prefab");
                if (bought != null)
                {
                    var bm = (GameObject)PrefabUtility.InstantiatePrefab(bought); bm.transform.SetParent(holder.transform, false);
                    bm.transform.localPosition = Vector3.zero; bm.transform.localRotation = Quaternion.Euler(0, 180f, 0);   // the proxies face local -z
                }
                foreach (var part in (bought != null ? new GameObject[0] : new[] { pr, Proto(kind + "_Beacons") }).Where(q => q != null))
                {
                    var c = Object.Instantiate(part, holder.transform, false); c.name = part.name; c.transform.localPosition = Vector3.zero; c.transform.localRotation = Quaternion.identity;
                    if (part.name.EndsWith("_Beacons")) foreach (var r in c.GetComponentsInChildren<MeshRenderer>()) { r.shadowCastingMode = ShadowCastingMode.Off; ShellGlow.Add(r); }
                }
                var bc = holder.AddComponent<BoxCollider>(); var bb = new Bounds(holder.transform.position, Vector3.zero);
                foreach (var r in holder.GetComponentsInChildren<MeshRenderer>()) bb.Encapsulate(r.bounds);
                bc.center = holder.transform.InverseTransformPoint(bb.center); bc.size = Quaternion.Inverse(holder.transform.rotation) * bb.size; bc.size = new Vector3(Mathf.Abs(bc.size.x), Mathf.Abs(bc.size.y), Mathf.Abs(bc.size.z));
                string scene = (string)vspec?[kind]?["scene"] ?? (string)it["scene"];   // spec/vehicles.json wins (the van: night only, as the film)
                if (scene == "night")   // the film's night scenes (police 11576-11636, the van 3297/5545/9511): the night layer carries the holder
                {
                    var l = holder.AddComponent<Light>(); holder.AddComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalLightData>();
                    l.type = LightType.Point; l.shadows = LightShadows.None; l.lightmapBakeType = LightmapBakeType.Realtime; l.lightUnit = UnityEngine.Rendering.LightUnit.Lumen;
                    if (bought == null && kind.Contains("Police")) { l.color = new Color(1f, 0.08f, 0.04f); l.intensity = 500f; l.range = 14f; }   // proxy beacon glow only
                    else { l.intensity = 0f; l.enabled = false; }   // a bought car lights itself (PoliceLights); the light only carries the holder into the night layer
                    ShellLights.Add(l); holder.name = $"{kind} (night)";
                }
                else foreach (var t in holder.GetComponentsInChildren<Transform>(true)) t.gameObject.isStatic = true;
                life++;
            }
            var pole = Proto("Pole");
            foreach (JObject q in ll["poles"])
            {
                var g = Object.Instantiate(pole, lifeRoot.transform, false); g.name = "Utility pole"; g.transform.position = new Vector3((float)q["x"], gy + (float)lv["walk"], -(float)q["z"]);
                var cc = g.AddComponent<CapsuleCollider>(); cc.radius = 0.16f; cc.height = 10f; cc.center = new Vector3(0, 5f, 0); g.isStatic = true; life++;
            }
            var wires = Proto("Wires"); if (wires != null) { var w = Object.Instantiate(wires, lifeRoot.transform, false); w.name = "Overhead wires"; w.transform.position = new Vector3(0, gy, 0); w.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off; w.isStatic = true; }
            foreach (var r in lifeRoot.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.name == "Hydrant" || r.name == "Mailbox" || r.name == "YardStake")) r.shadowCastingMode = ShadowCastingMode.On;
            // the walk boundary's soft blockers: hedges and snow piles (one mesh), each piece colliding
            var bdm = Proto("BoundaryDressing");
            if (bdm != null)
            {
                var bd = Object.Instantiate(bdm, lifeRoot.transform, false); bd.name = "Boundary hedges and snow piles"; bd.transform.position = new Vector3(0, gy, 0); bd.isStatic = true;
                bd.AddComponent<MeshCollider>().sharedMesh = bd.GetComponent<MeshFilter>().sharedMesh;
            }
            Object.DestroyImmediate(src);
            // the boundary hedges: rows of the beds' boxwood scan along the heroes' side lot lines (soft blockers), a box collider per row
            foreach (JArray hz in ll["hedges"])
            {
                var a = new Vector2((float)hz[0], (float)hz[1]); var b = new Vector2((float)hz[2], (float)hz[3]); string lot = (string)hz[4];
                float y0 = gy + (grade[lot] != null ? (float)grade[lot] : (float)lv["lawn_A"]); float L = (b - a).magnitude; int n = Mathf.Max(1, Mathf.RoundToInt(L / 0.75f));
                var hr = new System.Random(lot.GetHashCode());
                for (int i = 0; i < n; i++)
                {
                    var q = Vector2.Lerp(a, b, (i + 0.5f) / n);
                    scanShrubs.Add((new Vector3(q.x, y0, -q.y), 1.05f + 0.1f * (float)hr.NextDouble(), 0.95f, 1.25f + 0.15f * (float)hr.NextDouble(), lot + "_hedge"));
                }
                var hc = new GameObject($"Hedge collider {lot}"); hc.transform.SetParent(lifeRoot.transform, false);
                var m2 = (a + b) / 2f; var d2 = b - a;
                hc.transform.SetPositionAndRotation(new Vector3(m2.x, y0 + 0.7f, -m2.y), Quaternion.LookRotation(new Vector3(d2.x, 0, -d2.y).normalized, Vector3.up));
                var hbc = hc.AddComponent<BoxCollider>(); hbc.size = new Vector3(1.0f, 1.4f, L); hc.isStatic = true;
            }
            ScanShrubRow(root, scanShrubs);
            WalkBoundary(ext, gy, ll);
        }
        var tl = Inst("TreeLine", "Tier 4 treeline", new Vector3(0f, gy, 0f));
        if (tl != null)
            foreach (var r in tl.GetComponentsInChildren<MeshRenderer>(true))
            { r.gameObject.isStatic = true; if (r.name.StartsWith("TreeLine")) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; } }
        // the old street's generated trees (SpecGreybox.Trees swapped each WinterNeighborhood stick for a "Bare winter tree") stood on the old
        // layout: off the lot they double the lidar trees placed above; our parcel and frontage (Tier 1: x < 31, z -4.5..31.2) keep theirs
        int oldTrees = 0;
        if (hood != null)
        {
            var lot = ((JArray)((JObject)man["parcels"].First(q => (string)q["id"] == "lot_A0"))["parcel_poly_spec"]).Select(q => new Vector2((float)q[0], (float)q[1])).ToList();
            foreach (var t in hood.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Bare winter tree")).ToList())
            {
                float x = t.position.x, z = -t.position.z;
                bool ours = Inside(lot, new Vector2(Mathf.Min(x, 27.0f), z)) || (x < 31f && z > -4.5f && z < 31.2f);
                if (ours || x < -60f || x > 100f || Mathf.Abs(z) > 150f) continue;
                foreach (var r in t.GetComponentsInChildren<Renderer>(true)) { r.enabled = false; r.name += " [nb-off]"; }
                foreach (var c in t.GetComponentsInChildren<Collider>(true)) c.enabled = false;
                oldTrees++;
            }
        }
        Debug.Log($"Neighborhood: {oldTrees} old street trees off (lidar trees replace them)");
        Debug.Log($"Neighborhood: step 3 street life {life} (cars, props, poles), treeline {(tl != null ? "on" : "missing")}");
        // the moon lights only rendering layer LayerOutside (SpecGreybox.Backdrop); every neighbourhood renderer joins it, the night-layer cars
        // included (they were moved out of the root above: tag them through ShellLights' holders too)
        int moonlit = 0;
        foreach (var r in root.GetComponentsInChildren<Renderer>(true).Concat(ShellLights.Where(l => l != null).SelectMany(l => l.GetComponentsInChildren<Renderer>(true))))
        { r.renderingLayerMask |= LayerOutside; moonlit++; }
        Debug.Log($"Neighborhood: {moonlit} renderers on the moon's layer (LayerOutside)");
        Debug.Log($"Neighborhood: {houses} houses (Tier 2 LOD0 {tris2} tris, Tier 3 {tris3} tris), {glows} night glows, {lamps} acorn lamps, {trees} trees, {NbMats.Count} shared materials, {off} WinterNeighborhood renderers off");
    }
}
