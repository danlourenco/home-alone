using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;

// Generated arches (artist pipeline, .claude/skills/artist-pipeline): tools/house/hifi_foyer_arch.py -> FoyerArch.glb, generated
// from the cut's own numbers (spec/geometry.json) and drawn on that cut by the openings loop (Storey). The stepped slices
// (ArchTop) stay as invisible colliders for walking. Arch fit proves the joints meet the cut and the walls by construction.
public static partial class SpecGreybox
{
    static readonly Dictionary<string, string> ArchModels = new() { ["foyer|rear_passage"] = "FoyerArch" };
    static readonly List<(GameObject g, JToken o)> ArchPlaced = new();

    // paper(x, zSpec): the wall finish of the room at that plan point (the spandrels' faces take their room's paper, triplanar
    // in world space, so it runs on from the wall boxes around them)
    static GameObject ArchModel(GameObject parent, JToken o, System.Func<float, float, Material> paper)
    {
        string key = string.Join("|", o["between"].Select(t => (string)t).OrderBy(t => t));
        if (!ArchModels.TryGetValue(key, out var asset)) return null;
        var a = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Models/Foyer/{asset}.glb");
        if (a == null) { Debug.LogWarning("ArchModel: missing " + asset); return null; }
        var g = (GameObject)Object.Instantiate(a, parent.transform); g.name = asset + "_Gen";   // _Gen: generated on its cut (the seam check leaves generated meshes to the z-fight and clash checks)
        g.transform.position = new Vector3(0, FloorY, 0);
        foreach (var c in g.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        float cc = (float)o["c"], mid = ((float)o["lo"] + (float)o["hi"]) / 2; bool ax = (string)o["axis"] == "x";
        Material Side(float s) => ax ? paper(cc + s * 0.1f, mid) : paper(mid, cc + s * 0.1f);
        // made only for the parts the model has (Oct 17: the foyer arch lost its casing; the film's arch is plain)
        var remap = new Dictionary<string, System.Func<Material>> { ["FA_PaperPos"] = () => Side(1f), ["FA_PaperNeg"] = () => Side(-1f),
                                                                    ["FA_Soffit"] = () => BakedMat(asset, "Soffit"), ["FA_Casing"] = () => BakedMat(asset, "Casing") };
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            string n = r.sharedMaterial != null ? r.sharedMaterial.name : "";
            foreach (var kv in remap) if (n.StartsWith(kv.Key)) r.sharedMaterial = kv.Value();
            r.gameObject.isStatic = true;
        }
        ArchPlaced.Add((g, o));
        return g;
    }

    // HDRP Lit on the pipeline's maps (Assets/Textures/Generated/<model>/<part>_{base,mask,normal,detail}.png + <part>.json):
    // base sRGB, mask (R metal, G AO, B detail mask, A smoothness) and detail linear, normal as a normal map; mipmaps, aniso 8
    static Material BakedMat(string model, string part)
    {
        string dir = $"Assets/Textures/Generated/{model}/{part}";
        Texture2D Tex(string map, bool srgb, bool normal = false)
        {
            string p = $"{dir}_{map}.png";
            if (AssetImporter.GetAtPath(p) is TextureImporter ti && (ti.sRGBTexture != srgb || (ti.textureType == TextureImporterType.NormalMap) != normal
                                                                    || ti.anisoLevel != 8 || !ti.mipmapEnabled || ti.maxTextureSize < 4096))
            {
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default; ti.sRGBTexture = srgb;
                ti.anisoLevel = 8; ti.mipmapEnabled = true; ti.maxTextureSize = 4096; ti.SaveAndReimport();
            }
            var t = AssetDatabase.LoadAssetAtPath<Texture2D>(p);
            if (t == null) Debug.LogWarning("BakedMat: missing " + p);
            return t;
        }
        var m = Mat($"HiFi_{model}_{part}", Color.white);
        m.SetTexture("_BaseColorMap", Tex("base", true)); m.SetTexture("_MaskMap", Tex("mask", false));
        m.SetTexture("_NormalMap", Tex("normal", false, true)); m.SetFloat("_NormalScale", 1f);
        m.SetTexture("_DetailMap", Tex("detail", false));
        var js = JObject.Parse(File.ReadAllText(Path.GetFullPath($"{dir}.json")));
        m.SetTextureScale("_DetailMap", new Vector2((float)js["detail_tiling"][0], (float)js["detail_tiling"][1]));
        m.SetFloat("_DetailAlbedoScale", 1f); m.SetFloat("_DetailNormalScale", 0.6f); m.SetFloat("_DetailSmoothnessScale", 1f);
        m.SetFloat("_MetallicRemapMin", 0f); m.SetFloat("_MetallicRemapMax", 1f); m.SetFloat("_SmoothnessRemapMin", 0f); m.SetFloat("_SmoothnessRemapMax", 1f);
        m.SetFloat("_AORemapMin", 0f); m.SetFloat("_AORemapMax", 1f);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); EditorUtility.SetDirty(m);
        return m;
    }

    // Walls touch by construction (walls-touch rule): every generated arch's soffit, papered faces and casing must sit on its cut's
    // numbers within 1 mm, and rays from inside the opening must meet the jambs where the soffit springs.
    static string ArchFitCheck()
    {
        const float h = 0.07f, tol = 0.001f; var bad = new List<string>(); float worst = 0f;
        foreach (var (g, o) in ArchPlaced)
        {
            float c = (float)o["c"], lo = (float)o["lo"], hi = (float)o["hi"], sp = (float)o["spring"], cr = (float)o["height"], fy = g.transform.position.y;
            bool ax = (string)o["axis"] == "x";
            (float along, float y, float across) Spec(Vector3 w) => ax ? (-w.z, w.y - fy, w.x) : (w.x, w.y - fy, -w.z);
            List<(float along, float y, float across)> V(string node)
            {
                var t = g.GetComponentsInChildren<MeshFilter>().FirstOrDefault(f => f.name == node);
                return t == null ? new() : t.sharedMesh.vertices.Select(v => Spec(t.transform.TransformPoint(v))).ToList();
            }
            void Joint(string what, float got, float want)
            {
                float d = Mathf.Abs(got - want); worst = Mathf.Max(worst, d);
                if (d > tol) bad.Add($"ARCH    {g.name} {what}: {got:F4} vs cut {want:F4}");
            }
            string nm = g.name.Replace("_Gen", "");
            var sof = V("Soffit_" + nm); var pp = V("Paper_" + nm + "_Pos"); var pn = V("Paper_" + nm + "_Neg"); var cas = V("Casing_" + nm);
            if (sof.Count == 0 || pp.Count == 0 || pn.Count == 0) { bad.Add($"ARCH    {g.name}: a part is missing"); continue; }   // the casing is optional
            Joint("soffit springing (lo)", sof.Min(q => q.along), lo); Joint("soffit springing (hi)", sof.Max(q => q.along), hi);
            Joint("soffit springline", sof.Min(q => q.y), sp); Joint("soffit crown", sof.Max(q => q.y), cr);
            Joint("soffit passage face", sof.Min(q => q.across), c - h); Joint("soffit foyer face", sof.Max(q => q.across), c + h);
            Joint("paper +face plane (min)", pp.Min(q => q.across), c + h); Joint("paper +face plane (max)", pp.Max(q => q.across), c + h);
            Joint("paper -face plane (min)", pn.Min(q => q.across), c - h); Joint("paper -face plane (max)", pn.Max(q => q.across), c - h);
            if (cas.Count > 0)
            {
                Joint("casing back on the wall face", cas.Min(q => q.across), c + h);
                var legs = cas.Where(q => q.y < sp - 0.01f).ToList();
                if (legs.Any(q => q.along < lo + 0.01f)) Joint("casing leg on the lo jamb", legs.Where(q => q.along < lo + 0.01f).Max(q => q.along), lo);
                if (legs.Any(q => q.along > hi - 0.01f)) Joint("casing leg on the hi jamb", legs.Where(q => q.along > hi - 0.01f).Min(q => q.along), hi);
                if (cas.Max(q => q.along) > hi + tol && !legs.Any(q => q.along > hi - 0.01f)) bad.Add($"ARCH    {g.name}: casing runs past the hi jamb with no leg there");
            }
            // the jambs (wall boxes) stand exactly where the soffit springs: a wall box holds the point 2 mm beyond each springing,
            // and none holds the point 2 mm inside the opening (10 cm under the springline)
            Vector3 W(float along, float y, float across) => ax ? new Vector3(across, y + fy, -along) : new Vector3(along, y + fy, -across);
            Physics.SyncTransforms();
            bool WallAt(Vector3 q) => Physics.OverlapSphere(q, 0.0005f, ~0, QueryTriggerInteraction.Ignore).Any(k => k.name == "Wall");
            foreach (var (end, dir) in new[] { (lo, -1f), (hi, 1f) })
            {
                // both halves of the wall's thickness (a thin wall is split down its middle where its two rooms' finishes differ)
                bool beyond = new[] { -0.035f, 0.035f }.All(t => WallAt(W(end + dir * 0.002f, sp - 0.1f, c + t)));
                bool inside = new[] { -0.035f, 0.035f }.Any(t => WallAt(W(end - dir * 0.002f, sp - 0.1f, c + t)));
                if (!beyond || inside)
                {
                    var q = W(end + dir * 0.002f, sp - 0.1f, c + 0.035f);
                    var near = Physics.OverlapSphere(q, 0.05f, ~0, QueryTriggerInteraction.Ignore).Select(k => k.name).Distinct();
                    bad.Add($"ARCH    {g.name}: the jamb wall does not end at {end:F3} (wall beyond: {beyond}, wall inside the opening: {inside}; within 5 cm of world {q}: {string.Join(", ", near)})");
                }
            }
        }
        int n = ArchPlaced.Count; ArchPlaced.Clear();
        return $"Arch fit: {n} generated arches on their cuts, {bad.Count} joints off by more than 1 mm (worst {worst * 1000f:F2} mm)\n" + string.Concat(bad.Select(b => b + "\n"));
    }
}
