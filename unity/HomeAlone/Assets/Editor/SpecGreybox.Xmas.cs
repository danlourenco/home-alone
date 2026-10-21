using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;
using UnityEditor;
using Object = UnityEngine.Object;

// THE CHRISTMAS LIGHTS BAKE-OFF SET (Oct 21; docs/XMAS-LIGHTS.md, .claude/skills/xmas-lights). Builds the new look BESIDE today's and
// leaves today's on: Scripts/XmasLights.cs switches them live (PerfProbe xmas=old|A|B|C, xdecal=0, xpool=0, xinst=1). Default: old.
//  - bulbs: C7s (3.0 cm glass on a 1.6 cm green socket, lathed here: a Blender model adds nothing at 2 cm) at the film's 0.21 m on the
//    window loops (tools/house/xmas_strands.py -> spec/dressing/xmas.json) and at today's shrub points (ExteriorPlants -> XmasYard),
//    chunked on a 4 m grid per storey, LODGroup per chunk (LOD0 ~70 tris/bulb, LOD1 12), 3 shared materials (bright, dim, socket)
//  - wire: per chunk, the loops' sagging polylines (the shrubs' bulbs hide their wire in the leaves, as today)
//  - glow cards: per chunk, 4 vertices per bulb (Shaders/XmasGlowCard.shader), low-resolution transparent queue
//  - pool: 24 unshadowed Point lights on the exterior rendering layer, clusters = each window loop and each yard chunk
//  - decals: an emissive soft ring (HDRP/Decal, Affect Emission only) behind each window loop
// Upper-storey chunks join HouseSplit.skinUpper (hidden upstairs, like the GLB's U_XmasBulbs).
public static partial class SpecGreybox
{
    static readonly List<(Vector3 p, float size, int tint)> XmasYard = new();   // ExteriorPlants' mini-light points (world), tint 0/1 bright, 2 dim
    const float XmasLmPerBulb = 10f, XmasYardLmPerBulb = 2f, XmasPoolMaxLm = 400f;   // C7 5 W = 10 lm (docs S12); calibration knobs for the bake-off
    static readonly Color XmasFilm = new Color(1f, 0.53f, 0.32f);   // film 5545 halo shoulder, linear (xmas_lights_check.py --film-extra)

    static void BuildXmasLights(GameObject ext, float gy)
    {
        var jp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/xmas.json"));
        if (!File.Exists(jp)) { Debug.LogWarning("XmasLights: spec/dressing/xmas.json missing (tools/house/xmas_strands.py), bake-off set not built"); return; }
        var J = JObject.Parse(File.ReadAllText(jp));
        var root = new GameObject("XmasLights"); root.transform.SetParent(ext.transform, false);
        var bright = XmasBulb("HiFi_XmasC7", XmasFilm, 1600f); var dim = XmasBulb("HiFi_XmasC7Dim", XmasFilm, 900f);
        var socket = Mat("HiFi_XmasC7Socket", new Color(0.03f, 0.09f, 0.035f)); var wireMat = Mat("HiFi_ExtWire", new Color(0.012f, 0.025f, 0.012f));
        var cardMat = CardMat();

        // ---- every bulb: (position, axis, tint 0 bright / 1 dim, storey U/L, strand index or -1)
        var bulbs = new List<(Vector3 p, Vector3 ax, int tint, string st, int strand)>(); var rnd = new System.Random(5545);
        var strands = J["strands"].ToList(); var wires = new List<(List<Vector3> pts, string st)>();
        for (int si = 0; si < strands.Count; si++)
        {
            var s = strands[si]; var n = new Vector3((float)s["normal"][0], (float)s["normal"][1], (float)s["normal"][2]); string st = (string)s["storey"];
            foreach (var b in s["bulbs"])   // a C7 on a window clip points out and up
                bulbs.Add((new Vector3((float)b[0], (float)b[1], (float)b[2]), (Vector3.up + 0.7f * n).normalized, rnd.NextDouble() < 0.2 ? 1 : 0, st, si));
            wires.Add((s["wire"].Select(w => new Vector3((float)w[0], (float)w[1], (float)w[2])).ToList(), st));
        }
        foreach (var (p, _, t) in XmasYard)
        {
            var ax = new Vector3((float)rnd.NextDouble() - 0.5f, 1f, (float)rnd.NextDouble() - 0.5f).normalized;
            bulbs.Add((p, ax, t == 2 ? 1 : 0, "L", -1));
        }
        // the generator stays in its box (AGENTS.md: assert each piece stays in its spec box): the house, the yard and the beds
        var bad = bulbs.Where(b => float.IsNaN(b.p.x) || b.p.x < -15f || b.p.x > 30f || b.p.z < -40f || b.p.z > 10f || b.p.y < -6f || b.p.y > 12f).ToList();
        if (bad.Count > 0) throw new System.Exception($"XmasLights: {bad.Count} bulbs outside the lot, first {bad[0].p}");

        // ---- chunks: a 4 m grid per storey
        string Key(Vector3 p, string st) => $"{st}_{Mathf.FloorToInt(p.x / 4f)}_{Mathf.FloorToInt(-p.z / 4f)}";
        var chunks = bulbs.GroupBy(b => Key(b.p, b.st)).ToList();
        var bulbR = new List<Renderer>(); var cardR = new List<Renderer>(); var upperR = new List<Renderer>();
        var clusters = new List<(Vector3 c, float lm, float range)>(); long tris0 = 0, tris1 = 0;
        foreach (var ch in chunks)
        {
            var list = ch.ToList(); var o = new Vector3(list.Average(b => b.p.x), list.Average(b => b.p.y), list.Average(b => b.p.z));
            var g = new GameObject("XmasC7_" + ch.Key); g.transform.SetParent(root.transform, false); g.transform.position = o; g.isStatic = true;
            var l0 = XmasChunk(g, "XmasC7_" + ch.Key + "_LOD0", list, o, true, bright, dim, socket); var l1 = XmasChunk(g, "XmasC7_" + ch.Key + "_LOD1", list, o, false, bright, dim, socket);
            tris0 += l0.GetComponent<MeshFilter>().sharedMesh.triangles.Length / 3; tris1 += l1.GetComponent<MeshFilter>().sharedMesh.triangles.Length / 3;
            var lg = g.AddComponent<LODGroup>(); lg.fadeMode = LODFadeMode.None;
            lg.SetLODs(new[] { new LOD(0.08f, new Renderer[] { l0 }), new LOD(0.004f, new Renderer[] { l1 }) }); lg.RecalculateBounds();
            var cr = XmasCards(g, "XmasCard_" + ch.Key, list, o, cardMat);
            bulbR.Add(l0); bulbR.Add(l1); cardR.Add(cr);
            if (ch.Key.StartsWith("U_")) upperR.AddRange(new Renderer[] { l0, l1, cr });
            if (list[0].strand < 0)   // a yard chunk is one pool cluster
            {
                var ext2 = list.Max(b => (b.p - o).magnitude);
                clusters.Add((o + Vector3.up * 0.3f, Mathf.Min(XmasPoolMaxLm, list.Count * XmasYardLmPerBulb), Mathf.Clamp(ext2 + 1f, 1.6f, 2.5f)));
            }
        }
        // the loops' wire, per strand (a loop is one cluster: its centre 0.35 m out from the wall)
        for (int si = 0; si < wires.Count; si++)
        {
            var (pts, st) = wires[si]; var seg = new List<Vector3>(); for (int k = 0; k + 1 < pts.Count; k++) { seg.Add(pts[k]); seg.Add(pts[k + 1]); }
            var w = Strand(root, $"XmasC7Wire_{st}_{si}", seg, 0.0015f, wireMat); var wr = w.GetComponent<MeshRenderer>(); wr.renderingLayerMask = LayerHouse | LayerOutside;
            bulbR.Add(wr); if (st == "U") upperR.Add(wr);
            var s = strands[si]; var n = new Vector3((float)s["normal"][0], (float)s["normal"][1], (float)s["normal"][2]);
            var c = new Vector3(pts.Average(p => p.x), pts.Average(p => p.y), pts.Average(p => p.z)); float half = pts.Max(p => (p - c).magnitude);
            clusters.Add((c + n * 0.35f, Mathf.Min(XmasPoolMaxLm, s["bulbs"].Count() * XmasLmPerBulb), Mathf.Clamp(half + 1f, 1.6f, 2.5f)));
            XmasDecal(root, c, n, pts);
        }
        foreach (var r in bulbR.Where(r => r.sharedMaterial != wireMat)) ShellGlow.Add(r);   // glass by day (HouseNightMode darkens the emission)

        // ---- the pool: 24 unshadowed lights on the exterior layer, off until XmasLights picks clusters (night, xmas=C)
        var pool = new List<Light>();
        for (int k = 0; k < 24; k++)
        {
            var l = NightLight(root, $"XmasPool_{k}", root.transform.position, 0f, 2f); l.color = XmasFilm; l.renderingLayerMask = (int)LayerOutside;
            var hd = l.GetComponent<HDAdditionalLightData>(); hd.affectsVolumetric = false; l.enabled = false; pool.Add(l); ShellLights.Add(l);
        }

        // ---- today's set (the base) and the switch
        var hifi = ext.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == "Exterior_HiFi");
        var oldR = Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include)
            .Where(r => r.name.StartsWith("XmasBulbs_Yard") || r.name.StartsWith("XmasWire_Yard") ||
                        (hifi != null && r.transform.IsChildOf(hifi) && (r.name.StartsWith("U_Xmas") || r.name.StartsWith("L_Xmas")))).ToArray();
        var oldL = ShellLights.Where(l => l != null && l.name == "ShrubGlow").ToArray();
        var x = root.AddComponent<XmasLights>();
        x.oldRenderers = oldR; x.oldLights = oldL; x.bulbs = bulbR.ToArray(); x.cards = cardR.ToArray(); x.pool = pool.ToArray();
        x.decalRoot = root.transform.Find("XmasDecals")?.gameObject;
        x.clusterPos = clusters.Select(c => c.c).ToArray(); x.clusterLumens = clusters.Select(c => c.lm).ToArray(); x.clusterRange = clusters.Select(c => c.range).ToArray();
        // xinst=1: one LOD1 bulb at the origin and every bulb's transform; instanced copies of the two glass materials
        x.instMesh = XmasBulbMesh(false); x.instMats = new[] { XmasInst(bright), XmasInst(dim) };
        x.instXf = bulbs.Select(b => Matrix4x4.TRS(b.p, Quaternion.FromToRotation(Vector3.up, b.ax), Vector3.one)).ToArray(); x.instMat = bulbs.Select(b => b.tint).ToArray();
        foreach (var r in bulbR.Concat(cardR)) r.forceRenderingOff = true;   // the base is today's look: the new set waits for xmas=A|B|C
        if (x.decalRoot) x.decalRoot.SetActive(false);
        var split = Object.FindAnyObjectByType<HouseSplit>(); if (split) split.skinUpper = split.skinUpper.Concat(upperR).ToArray();
        Debug.Log($"XmasLights: {bulbs.Count} C7s ({bulbs.Count(b => b.strand >= 0)} on {wires.Count} window loops at {(float)J["pitch"]} m, {XmasYard.Count} in the yard), " +
                  $"{chunks.Count} chunks ({upperR.Count / 3} upper), LOD0 {tris0} / LOD1 {tris1} tris, {cardR.Count} card meshes, {clusters.Count} pool clusters, " +
                  $"materials: bulbs 3 (HiFi_XmasC7, HiFi_XmasC7Dim, HiFi_XmasC7Socket), cards 1; old set {oldR.Length} renderers + {oldL.Length} ShrubGlow lights (base: old)");
    }

    // one C7, its axis along +y: lathed glass (a teardrop 3.0 cm long, 2.2 cm wide) on a 1.6 cm socket. LOD0: 8 sides, 5 rings, socket;
    // LOD1: 4 sides, 2 rings, no socket. Returns (vertices, normals, per-submesh triangles: glass, socket)
    static (List<Vector3> v, List<Vector3> n, List<int> glass, List<int> sock) XmasC7Shape(bool hi)
    {
        var v = new List<Vector3>(); var n = new List<Vector3>(); var glass = new List<int>(); var sock = new List<int>();
        int sides = hi ? 8 : 4;
        var prof = hi ? new[] { (0.000f, 0.0060f), (0.004f, 0.0100f), (0.011f, 0.0110f), (0.020f, 0.0092f), (0.027f, 0.0050f), (0.030f, 0f) }
                      : new[] { (0.000f, 0.0080f), (0.012f, 0.0110f), (0.030f, 0f) };
        void Lathe((float y, float r)[] pr, List<int> tris)
        {
            int b = v.Count;
            for (int i = 0; i < pr.Length; i++)
            {
                float dy = pr[Mathf.Min(i + 1, pr.Length - 1)].y - pr[Mathf.Max(i - 1, 0)].y, dr = pr[Mathf.Min(i + 1, pr.Length - 1)].r - pr[Mathf.Max(i - 1, 0)].r;
                for (int j = 0; j < sides; j++)
                {
                    float a = j * Mathf.PI * 2f / sides; var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    v.Add(dir * pr[i].r + Vector3.up * pr[i].y); n.Add((dir * dy - Vector3.up * dr).normalized);
                }
            }
            for (int i = 0; i + 1 < pr.Length; i++)
                for (int j = 0; j < sides; j++)
                {
                    int a0 = b + i * sides + j, a1 = b + i * sides + (j + 1) % sides, c0 = a0 + sides, c1 = a1 + sides;
                    if (pr[i + 1].r > 0f) tris.AddRange(new[] { a0, c0, a1, a1, c0, c1 }); else tris.AddRange(new[] { a0, c0, a1 });
                }
        }
        Lathe(prof, glass);
        if (hi) Lathe(new[] { (-0.016f, 0.0075f), (-0.004f, 0.0080f), (0.000f, 0.0060f) }, sock);
        return (v, n, glass, sock);
    }

    static Mesh XmasBulbMesh(bool hi)
    {
        var (v, n, g, _) = XmasC7Shape(hi);
        var m = new Mesh { name = "XmasC7_" + (hi ? "LOD0" : "LOD1") }; m.SetVertices(v); m.SetNormals(n); m.SetTriangles(g, 0); m.RecalculateBounds(); return m;
    }

    // a chunk's bulbs as one static mesh: submeshes bright glass, dim glass (and the sockets at LOD0), vertices in the chunk's frame
    static MeshRenderer XmasChunk(GameObject parent, string name, List<(Vector3 p, Vector3 ax, int tint, string st, int strand)> list, Vector3 o, bool hi, Material bright, Material dim, Material socket)
    {
        var (sv, sn, sg, ss) = XmasC7Shape(hi);
        var vs = new List<Vector3>(); var ns = new List<Vector3>(); var sub = new[] { new List<int>(), new List<int>(), new List<int>() };
        foreach (var b in list)
        {
            var q = Quaternion.FromToRotation(Vector3.up, b.ax); int baseI = vs.Count;
            for (int i = 0; i < sv.Count; i++) { vs.Add(b.p - o + q * sv[i]); ns.Add(q * sn[i]); }
            sub[b.tint].AddRange(sg.Select(i => i + baseI)); sub[2].AddRange(ss.Select(i => i + baseI));
        }
        var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 }; mesh.SetVertices(vs); mesh.SetNormals(ns);
        int nsub = hi ? 3 : 2; mesh.subMeshCount = nsub; for (int k = 0; k < nsub; k++) mesh.SetTriangles(sub[k], k); mesh.RecalculateBounds();
        var g = new GameObject(name); g.transform.SetParent(parent.transform, false); g.isStatic = true;
        g.AddComponent<MeshFilter>().sharedMesh = mesh; var r = g.AddComponent<MeshRenderer>();
        r.sharedMaterials = hi ? new[] { bright, dim, socket } : new[] { bright, dim };
        r.shadowCastingMode = ShadowCastingMode.Off; r.renderingLayerMask = LayerHouse | LayerOutside; return r;
    }

    // a chunk's glow cards: 4 vertices per bulb at its centre, UV0 the corner, colour = film tint x intensity (dim bulbs 0.55)
    static MeshRenderer XmasCards(GameObject parent, string name, List<(Vector3 p, Vector3 ax, int tint, string st, int strand)> list, Vector3 o, Material m)
    {
        var vs = new List<Vector3>(); var uv = new List<Vector2>(); var col = new List<Color>(); var tris = new List<int>();
        var corners = new[] { new Vector2(-1, -1), new Vector2(1, -1), new Vector2(1, 1), new Vector2(-1, 1) };
        foreach (var b in list)
        {
            int baseI = vs.Count; var c = b.p - o + b.ax * 0.015f;   // the glass's centre
            var tint = XmasFilm; tint.a = b.tint == 1 ? 0.55f : 1f;
            foreach (var k in corners) { vs.Add(c); uv.Add(k); col.Add(tint); }
            tris.AddRange(new[] { baseI, baseI + 1, baseI + 2, baseI, baseI + 2, baseI + 3 });
        }
        var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 }; mesh.SetVertices(vs); mesh.SetUVs(0, uv); mesh.SetColors(col); mesh.SetTriangles(tris, 0);
        mesh.RecalculateBounds(); var bb = mesh.bounds; bb.Expand(1.0f); mesh.bounds = bb;   // the vertex shader moves the corners up to ~0.5 m: never culled early
        var g = new GameObject(name); g.transform.SetParent(parent.transform, false); g.isStatic = false;   // not static-batched: the batch would drop the inflated bounds
        g.AddComponent<MeshFilter>().sharedMesh = mesh; var r = g.AddComponent<MeshRenderer>(); r.sharedMaterial = m;
        r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off;
        r.renderingLayerMask = LayerHouse | LayerOutside; return r;
    }

    static Material CardMat()
    {
        const string path = "Assets/Materials/Greybox/XmasGlowCard.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        var sh = Shader.Find("HomeAlone/XmasGlowCard"); if (sh == null) throw new System.Exception("XmasLights: Shaders/XmasGlowCard.shader did not import");
        if (m == null) { m = new Material(sh); AssetDatabase.CreateAsset(m, path); } else m.shader = sh;
        m.renderQueue = 3400;   // HDRenderQueue.Priority.LowTransparent (internal): HDRP's low-resolution transparent pass (quarter pixels, depth-aware upsample)
        EditorUtility.SetDirty(m); return m;
    }

    static Material XmasInst(Material src)
    {
        string path = $"Assets/Materials/Greybox/{src.name}_Inst.mat"; AssetDatabase.DeleteAsset(path);
        var m = new Material(src) { enableInstancing = true }; AssetDatabase.CreateAsset(m, path); return m;
    }

    // behind a window loop: the brick's warm rim (film 5545: R/B 2.1 under the strands). An emissive-only HDRP decal with a soft ring
    // texture (generated once), projected onto the wall; exposure-weighted nits so it behaves as light from the bulbs
    static void XmasDecal(GameObject root, Vector3 c, Vector3 n, List<Vector3> loop)
    {
        var holder = root.transform.Find("XmasDecals")?.gameObject; if (holder == null) { holder = new GameObject("XmasDecals"); holder.transform.SetParent(root.transform, false); }
        const string path = "Assets/Materials/Greybox/HiFi_XmasSpillDecal.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("HDRP/Decal")); AssetDatabase.CreateAsset(m, path); }
        m.SetFloat("_AffectAlbedo", 0f); m.SetFloat("_AffectNormal", 0f); m.SetFloat("_AffectSmoothness", 0f); m.SetFloat("_AffectAO", 0f); m.SetFloat("_AffectMetal", 0f);
        m.SetFloat("_AffectEmission", 1f); m.SetTexture("_EmissiveColorMap", XmasRingTex()); m.SetColor("_EmissiveColor", XmasFilm * 6f);   // ~6 nits x film tint: tuned in the bake-off
        m.SetFloat("_EmissiveExposureWeight", 1f); HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m);
        var right = Vector3.Cross(Vector3.up, n).normalized; float w = 0, h = 0;
        foreach (var p in loop) { w = Mathf.Max(w, Mathf.Abs(Vector3.Dot(p - c, right))); h = Mathf.Max(h, Mathf.Abs(p.y - c.y)); }
        var g = new GameObject("XmasSpill"); g.transform.SetParent(holder.transform, false);
        g.transform.SetPositionAndRotation(c + n * 0.15f, Quaternion.LookRotation(-n));
        var dp = g.AddComponent<DecalProjector>(); dp.material = m; /* practices: ok (DecalProjector.material is its asset slot) */ dp.size = new Vector3(2 * w + 0.6f, 2 * h + 0.6f, 0.4f); dp.pivot = new Vector3(0, 0, 0.2f);
        dp.startAngleFade = 40f; dp.endAngleFade = 70f;
    }

    // a 128x128 soft rectangular ring (bright just outside a loop, falling off over ~0.3 m), saved once as a PNG asset
    static Texture2D XmasRingTex()
    {
        const string path = "Assets/Textures/Exterior/xmas_spill_ring.png"; var t = AssetDatabase.LoadAssetAtPath<Texture2D>(path); if (t != null) return t;
        const int N = 128; var tex = new Texture2D(N, N, TextureFormat.RGBA32, true, false);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {   // distance to the loop's rectangle (inset 0.3 of the half size: the decal is the loop + 0.3 m a side)
                float u = Mathf.Abs((x + 0.5f) / N * 2f - 1f), v = Mathf.Abs((y + 0.5f) / N * 2f - 1f);
                float d = Mathf.Max(u, v) - 0.7f; float a = Mathf.Exp(-(d * d) / (2f * 0.08f * 0.08f)) * Mathf.Clamp01((1f - Mathf.Max(u, v)) / 0.08f);
                tex.SetPixel(x, y, new Color(a, a, a, a));
            }
        Directory.CreateDirectory(Path.GetDirectoryName(path)); File.WriteAllBytes(path, tex.EncodeToPNG()); Object.DestroyImmediate(tex);
        AssetDatabase.ImportAsset(path);
        if (AssetImporter.GetAtPath(path) is TextureImporter ti) { ti.wrapMode = TextureWrapMode.Clamp; ti.sRGBTexture = false; ti.maxTextureSize = 128; ti.SaveAndReimport(); }
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }
}
