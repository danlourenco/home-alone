using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;
using UnityEditor;
using Object = UnityEngine.Object;

// Exterior realism pass (Oct 18 2026, TRIAL; changes/2026-10-18-exterior-realism.json). The film stays the authority for what exists
// (4382 day, 10 night, 10162-10177 the front steps); Pietro Chiovaro's render (art/home_alone/references/pietro/) for how real it looks.
//  - surfaces: UVMat (PBR on the mesh's own UVs: mask map, parallax height) for the skin (SpecGreybox.Shell's remap, hifi_exterior.py UVs)
//  - the front steps: chamfered speckled-stone treads on brick risers, black iron railings (film 10162-10177); the old boxes keep the walk
//  - snow that sits: drifts against the house and the terrace walls, banks along the walk and the kerb (raycast onto the ground, no colliders)
//  - the yard's gaps to the neighbourhood lots filled (walk note 20:46 "edge of a cliff"; 21:05 "random steps"): a terrain skirt
//  - weathering decals (grime at the wall base, streaks under the upper sills), the street wet asphalt
//  - ExteriorLook: fog, grade, bloom and night exposure in volumes outside only (an inside volume restores the interior's values),
//    falling snow round the camera (F toggles), camera dithering (the night sky's banding)
public static partial class SpecGreybox
{
    static Texture2D PHMap(string id, string n, bool linear, bool normal = false)
    {
        string p = $"Assets/Textures/PolyHaven/{id}/{n}";
        if (AssetImporter.GetAtPath(p) is TextureImporter ti)
        {
            bool dirty = false;
            if (normal && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; dirty = true; }
            if (!normal && linear && ti.sRGBTexture) { ti.sRGBTexture = false; dirty = true; }
            if (ti.anisoLevel < 8) { ti.anisoLevel = 8; dirty = true; }
            if (dirty) ti.SaveAndReimport();
        }
        return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
    }

    // HDRP/Lit on UV0 (metres) at "tile" m per repeat: albedo x tint, normal, mask (AO + smoothness up to smoothMax), and pixel
    // displacement (POM) of pomCm when > 0. Folders from tools/house/exterior_textures.py.
    static Material UVMat(string n, string id, Color tint, float tile, float smoothMax, float pomCm, float normalScale, bool albedo = true)
    {
        var m = Mat(n, tint);
        m.SetTexture("_BaseColorMap", albedo ? PHMap(id, "albedo.jpg", false) : null);   // painted trim: flat paint colour, the set's normal + roughness only
        m.SetTexture("_NormalMap", PHMap(id, "normal.jpg", true, true)); m.SetFloat("_NormalScale", normalScale);
        m.SetTexture("_MaskMap", PHMap(id, "mask.png", true));
        m.SetFloat("_MetallicRemapMin", 0f); m.SetFloat("_MetallicRemapMax", 0f);
        m.SetFloat("_SmoothnessRemapMin", 0f); m.SetFloat("_SmoothnessRemapMax", smoothMax);
        m.SetFloat("_AORemapMin", 0.35f); m.SetFloat("_AORemapMax", 1f);
        m.SetFloat("_UVBase", 0f); m.SetVector("_UVMappingMask", new Vector4(1, 0, 0, 0));
        m.SetTextureScale("_BaseColorMap", Vector2.one / tile); m.SetTextureOffset("_BaseColorMap", Vector2.zero);
        if (pomCm > 0f)
        {
            m.SetTexture("_HeightMap", PHMap(id, "height.png", true));
            m.SetFloat("_DisplacementMode", 2f);   // pixel (parallax occlusion)
            m.SetFloat("_HeightPoMAmplitude", pomCm); m.SetFloat("_HeightAmplitude", pomCm * 0.01f); m.SetFloat("_HeightCenter", 1f);
            m.SetFloat("_PPDMinSamples", 5f); m.SetFloat("_PPDMaxSamples", 16f); m.SetFloat("_PPDLodThreshold", 4f);
            m.SetFloat("_DisplacementLockObjectScale", 0f); m.SetFloat("_DisplacementLockTilingScale", 0f);
            m.SetFloat("_InvTilingScale", 1f); m.SetVector("_InvPrimScale", Vector4.one);
        }
        else { m.SetTexture("_HeightMap", null); m.SetFloat("_DisplacementMode", 0f); }
        HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m); return m;
    }

    static Material IceMat()
    {
        var m = Mat("HiFi_ExtIce", new Color(0.78f, 0.86f, 0.93f)); m.SetFloat("_Smoothness", 0.92f); HDMaterial.ValidateMaterial(m); return m;
    }

    // a mesh from world triangles (flat-shaded if flat, else smooth normals), static, under parent
    static GameObject WorldMesh(GameObject parent, string n, List<Vector3> vs, List<int> tris, Material m, bool shadows = true, bool upFacing = false)
    {
        if (upFacing)   // ground-like sheets: every triangle faces up (Unity's front face: Cross(b - a, c - a))
            for (int i = 0; i < tris.Count; i += 3)
                if (Vector3.Cross(vs[tris[i + 1]] - vs[tris[i]], vs[tris[i + 2]] - vs[tris[i]]).y < 0) { int t = tris[i + 1]; tris[i + 1] = tris[i + 2]; tris[i + 2] = t; }
        var mesh = new Mesh { name = n, indexFormat = IndexFormat.UInt32 }; mesh.SetVertices(vs); mesh.SetTriangles(tris, 0);
        mesh.RecalculateNormals(); mesh.RecalculateBounds();
        var g = new GameObject(n); g.transform.SetParent(parent.transform, false); g.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity); g.isStatic = true;
        g.AddComponent<MeshFilter>().sharedMesh = mesh; var r = g.AddComponent<MeshRenderer>(); r.sharedMaterial = m;
        r.shadowCastingMode = shadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
        return g;
    }

    // a profile in the x-y plane (counter-clockwise seen from +z) extruded from z0 to z1, flat faces (each face its own vertices)
    static void Extrude(List<Vector3> vs, List<int> tris, Vector2[] prof, float z0, float z1)
    {
        int n = prof.Length;
        void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d) { int i = vs.Count; vs.AddRange(new[] { a, b, c, d }); tris.AddRange(new[] { i, i + 1, i + 2, i, i + 2, i + 3 }); }
        for (int k = 0; k < n; k++)
        {
            var p = prof[k]; var q = prof[(k + 1) % n];
            Quad(new Vector3(p.x, p.y, z0), new Vector3(q.x, q.y, z0), new Vector3(q.x, q.y, z1), new Vector3(p.x, p.y, z1));
        }
        for (int s = 0; s < 2; s++)
        {
            float z = s == 0 ? z1 : z0; int b = vs.Count;
            foreach (var p in prof) vs.Add(new Vector3(p.x, p.y, z));
            for (int k = 1; k + 1 < n; k++) { if (s == 0) tris.AddRange(new[] { b, b + k, b + k + 1 }); else tris.AddRange(new[] { b, b + k + 1, b + k }); }
        }
    }

    static void ExteriorRealism(GameObject ext, float gy)
    {
        float d = gy + 2.996f;
        var yard = ext.transform.Find("Yard")?.gameObject; if (yard == null) { Debug.LogWarning("ExteriorRealism: no Yard"); return; }
        var holder = new GameObject("ExteriorRealism"); holder.transform.SetParent(ext.transform, true); holder.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
        var snowM = TexMat("HiFi_ExtGroundSnow", "snow_02_x", new Color(0.95f, 0.97f, 1.0f), 2.2f, 0.40f);
        var brick = TexMat("HiFi_ExtBrick", "red_brick_03_x", new Color(0.80f, 0.60f, 0.53f), 1.90f, 0.12f);
        var tread = TexMat("HiFi_ExtStepStone", "concrete_floor_01_x", new Color(0.83f, 0.42f, 0.34f), 0.9f, 0.55f);   // film 4382 red steps; damp/frosty sheen
        var iron = Mat("HiFi_ExtIron", new Color(0.012f, 0.012f, 0.012f)); iron.SetFloat("_Metallic", 0.6f); iron.SetFloat("_Smoothness", 0.45f);
        iron.SetFloat("_DoubleSidedEnable", 1f); HDMaterial.ValidateMaterial(iron);   // the bars' winding is not checked
        int nSnow = 0;
        foreach (var r in yard.GetComponentsInChildren<MeshRenderer>(true))   // the beds' and the grade's snow: the photo set, not a flat colour
            if (r.name.StartsWith("Bed_") || r.name.StartsWith("Grade") || r.name.StartsWith("Terrace")) { r.sharedMaterial = snowM; nSnow++; }

        // ---- the front steps (film 10162-10177: iced speckled treads over brick, black iron rails either side; 4382 reads red)
        const float zc = 9.716f, sw = 0.95f, stoopX = 12.25f, riser = 0.1757f, treadW = 0.30f, nose = 0.03f, tt = 0.045f, ch = 0.012f;
        float yS = -3.09f + d, yB = -4.35f + d;
        var sv = new List<Vector3>(); var st = new List<int>(); var rv = new List<Vector3>(); var rt = new List<int>();
        int hidden = 0;
        foreach (var r in yard.GetComponentsInChildren<MeshRenderer>(true))
            if (r.name.StartsWith("Step_Front")) { r.enabled = false; hidden++; }   // colliders stay: the walk is unchanged
            else if (r.name == "Stoop_Front") r.sharedMaterial = tread;
        for (int k = 1; k <= 6; k++)
        {
            float x0 = stoopX + treadW * (k - 1), x1 = stoopX + treadW * k, top = yS - riser * k;
            // riser block (brick), set back under the nosing
            Extrude(rv, rt, new[] { new Vector2(x1, yB), new Vector2(x1, top - tt), new Vector2(x0, top - tt), new Vector2(x0, yB) }, -(zc + sw), -(zc - sw));
            // tread slab with a chamfered nosing, 1.5 cm wider than the step each side
            Extrude(sv, st, new[] { new Vector2(x0, top - tt), new Vector2(x1 + nose - ch, top - tt), new Vector2(x1 + nose, top - tt + ch),
                                     new Vector2(x1 + nose, top - ch), new Vector2(x1 + nose - ch, top), new Vector2(x0, top) }, -(zc + sw + 0.015f), -(zc - sw - 0.015f));
        }
        // the stoop's front edge gets the same nosing
        Extrude(sv, st, new[] { new Vector2(stoopX - 0.10f, yS - tt), new Vector2(stoopX + nose - ch, yS - tt), new Vector2(stoopX + nose, yS - tt + ch),
                                 new Vector2(stoopX + nose, yS - ch + 0.004f), new Vector2(stoopX + nose - ch, yS + 0.004f), new Vector2(stoopX - 0.10f, yS + 0.004f) }, -(zc + sw + 0.015f), -(zc - sw - 0.015f));
        WorldMesh(holder, "FrontSteps_Treads", sv, st, tread); WorldMesh(holder, "FrontSteps_Risers", rv, rt, brick);
        // iron railings on both step edges (film 10162/10168): square bars 16 mm at 11 cm, top and bottom rails on the nosing line,
        // newel posts at the stoop and the foot with a scroll at the foot
        var iv = new List<Vector3>(); var it = new List<int>();
        void Bar(Vector3 a, Vector3 b, float w)
        {
            var t = (b - a).normalized; var u = Mathf.Abs(t.y) > 0.9f ? Vector3.right * w : Vector3.Cross(t, Vector3.up).normalized * w; var v = Vector3.Cross(u, t).normalized * w;
            int i0 = iv.Count;
            foreach (var p in new[] { a, b }) { iv.Add(p + u + v); iv.Add(p - u + v); iv.Add(p - u - v); iv.Add(p + u - v); }
            for (int k = 0; k < 4; k++) { int k2 = (k + 1) % 4; it.AddRange(new[] { i0 + k, i0 + 4 + k, i0 + 4 + k2, i0 + k, i0 + 4 + k2, i0 + k2 }); }
            it.AddRange(new[] { i0, i0 + 2, i0 + 1, i0, i0 + 3, i0 + 2, i0 + 4, i0 + 5, i0 + 6, i0 + 4, i0 + 6, i0 + 7 });
        }
        float xTop = stoopX - 0.05f, xFoot = stoopX + treadW * 6 - 0.10f;
        float Nose(float x) => x <= stoopX ? yS : yS - riser * Mathf.Ceil((x - stoopX) / treadW - 1e-3f);   // tread top under x
        float Line(float x) => yS + (x - stoopX) * (-riser / treadW) + riser * 0.5f;                          // the pitch line over the nosings
        foreach (float zs in new[] { zc - sw + 0.04f, zc + sw - 0.04f })
        {
            float z = -zs;
            Vector3 P(float x, float y) => new Vector3(x, y, z);
            Bar(P(xTop, Nose(xTop)), P(xTop, Line(xTop) + 0.92f), 0.022f); Bar(P(xFoot, Nose(xFoot)), P(xFoot, Line(xFoot) + 0.92f), 0.022f);   // newels
            Bar(P(xTop, Line(xTop) + 0.86f), P(xFoot, Line(xFoot) + 0.86f), 0.014f);                                                         // top rail
            Bar(P(xTop, Line(xTop) + 0.10f), P(xFoot, Line(xFoot) + 0.10f), 0.010f);                                                         // bottom rail
            for (float x = xTop + 0.11f; x < xFoot - 0.05f; x += 0.11f) Bar(P(x, Line(x) + 0.10f), P(x, Line(x) + 0.86f), 0.008f);
            var c = P(xFoot + 0.12f, Nose(xFoot) + 0.30f); Vector3? last = null;   // a C-scroll at the foot
            for (int k = 0; k <= 14; k++)
            {
                float a = Mathf.Lerp(-90f, 200f, k / 14f) * Mathf.Deg2Rad, rr = 0.13f * (1f - 0.45f * k / 14f);
                var q = c + new Vector3(-Mathf.Cos(a) * rr, Mathf.Sin(a) * rr, 0f);
                if (last != null) Bar(last.Value, q, 0.007f); last = q;
            }
            Bar(P(xFoot, Nose(xFoot) + 0.17f), c + new Vector3(0, -0.13f, 0), 0.007f);
        }
        WorldMesh(holder, "FrontSteps_Railings", iv, it, iron);

        // ---- snow that sits: mounds raycast onto what is below (no colliders: the walk and its gates are unchanged)
        Physics.SyncTransforms();
        var mv = new List<Vector3>(); var mt = new List<int>(); int mounds = 0;
        // u across 0..1 (0 = against the wall / bank centre line), a along; shape(u) * hmax with noise; ends taper over 'taper' m
        void Mound(float xa0, float xa1, float za0, float za1, bool alongX, float hmax, System.Func<float, float> shape, float rayY, float taper, float cell = 0.08f)
        {
            float L = alongX ? xa1 - xa0 : za1 - za0, W = alongX ? za1 - za0 : xa1 - xa0;
            int na = Mathf.Max(2, Mathf.CeilToInt(Mathf.Abs(L) / cell)), nw = Mathf.Max(2, Mathf.CeilToInt(Mathf.Abs(W) / cell));
            int b = mv.Count;
            for (int i = 0; i <= na; i++)
                for (int j = 0; j <= nw; j++)
                {
                    float fa = i / (float)na, fw = j / (float)nw;
                    float x = alongX ? Mathf.Lerp(xa0, xa1, fa) : Mathf.Lerp(xa0, xa1, fw), z = alongX ? Mathf.Lerp(za0, za1, fw) : Mathf.Lerp(za0, za1, fa);
                    float y0 = Physics.Raycast(new Vector3(x, rayY, z), Vector3.down, out var h, 2.5f) ? h.point.y : rayY - 1f;
                    float e = Mathf.Clamp01(Mathf.Min(fa, 1 - fa) * Mathf.Abs(L) / taper); e = Mathf.Sqrt(e);
                    float nz = 0.75f + 0.5f * Mathf.PerlinNoise(x * 1.7f + 11f, z * 1.7f + 5f) + 0.15f * (Mathf.PerlinNoise(x * 6f, z * 6f) - 0.5f);
                    mv.Add(new Vector3(x, y0 + 0.012f + hmax * e * shape(fw) * nz, z));
                }
            for (int i = 0; i < na; i++)
                for (int j = 0; j < nw; j++)
                {
                    int a0 = b + i * (nw + 1) + j, a1 = a0 + 1, c0 = a0 + nw + 1, c1 = c0 + 1;
                    mt.AddRange(new[] { a0, a1, c1, a0, c1, c0 });
                }
            mounds++;
        }
        System.Func<float, float> wallDrift = u => Mathf.Pow(1f - u, 1.8f);
        System.Func<float, float> bank = u => Mathf.Pow(Mathf.Max(0f, Mathf.Sin(Mathf.PI * u)), 0.8f);   // Max: sin(pi) < 0 gave NaN vertices
        float yU = -3.45f + d, yL = -3.90f + d, yF = -4.32f + d;
        // against the house in the upper beds (spans as FrontBeds'): world z = -spec z; x from the brick face out 0.9 m
        foreach (var (z0, z1, x0) in new[] { (-1.155f, 2.864f, 10.40f), (2.864f, 8.0f, 10.37f), (11.43f, 16.21f, 10.37f), (16.21f, 20.157f, 9.506f) })
            Mound(x0, x0 + 0.9f, -z0, -z1, false, 0.26f, wallDrift, yU + 0.45f, 0.35f);
        // against the upper terrace wall in the lower beds, and against the lower wall on the front lawn
        foreach (var (z0, z1) in new[] { (-1.155f, zc - sw - 0.25f), (zc + sw + 0.25f, 20.157f) })
        {
            Mound(12.85f, 13.45f, -z0, -z1, false, 0.16f, wallDrift, yL + 0.40f, 0.3f);
            Mound(14.88f, 15.45f, -z0, -z1, false, 0.14f, wallDrift, yF + 0.40f, 0.3f);
        }
        // banked against the step cheeks on the lawn side (the shovelled snow from the steps, film 10162)
        foreach (float s in new[] { -1f, 1f })
            Mound(14.05f, 15.0f, -(zc + s * (sw + 0.02f)), -(zc + s * (sw + 0.55f)), true, 0.22f, wallDrift, yF + 0.5f, 0.25f);
        // shovelled banks along the walk to the street (film 10174, Pietro)
        foreach (float s in new[] { -1f, 1f })
            Mound(15.1f, 24.2f, -(zc + s * 0.80f), -(zc + s * 1.45f), true, 0.24f, bank, yF + 0.5f, 0.6f);
        // the kerb: plowed banks at the street's edge on the house side, open at the walk
        var road = ext.GetComponentsInChildren<MeshRenderer>(true).FirstOrDefault(r => r.name.StartsWith("Lincoln"));
        if (road != null)
        {
            var wet = TexMat("HiFi_ExtWetRoad", "asphalt_02_x", new Color(0.45f, 0.45f, 0.47f), 4.0f, 0.86f);   // dark wet asphalt (Pietro; film 10162 night)
            road.sharedMaterial = wet;
            float kx = road.bounds.min.x;
            foreach (var (za, zb) in new[] { (-38f, -10.9f), (-8.5f, 22f) })
                Mound(kx + 0.05f, kx + 0.75f, za, zb, true, 0.28f, bank, road.bounds.max.y + 1.0f, 1.0f, 0.12f);
        }
        WorldMesh(holder, "SnowDrifts", mv, mt, snowM, true, true);

        // ---- the yard's gaps (walk notes 20:46, 21:05): a terrain skirt filled between the registered parcel and the neighbourhood lots.
        // Grid over the dome; a ray down from 10 m: ground under -2.6 is known (the skirt sits 3 cm under it), higher hits are the house
        // (excluded), hits under -5 the areaway/basement (excluded); no hit = gap, solved by Laplace from its known neighbours.
        {
            const float cell = 1.0f, half = 72f; var c0 = new Vector2(3f, -8f);
            int n = Mathf.CeilToInt(2 * half / cell) + 1;
            var H = new float[n, n]; var K = new byte[n, n];   // 0 gap, 1 known, 2 excluded
            float mean = 0f; int nk = 0;
            for (int i = 0; i < n; i++)
                for (int j = 0; j < n; j++)
                {
                    float x = c0.x - half + i * cell, z = c0.y - half + j * cell;
                    if (Physics.Raycast(new Vector3(x, 10f, z), Vector3.down, out var h, 30f))
                    {
                        if (h.point.y > -2.6f || h.point.y < -5f) K[i, j] = 2;
                        else { K[i, j] = 1; H[i, j] = h.point.y - 0.03f; mean += H[i, j]; nk++; }
                    }
                }
            mean = nk > 0 ? mean / nk : -4f;
            for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) if (K[i, j] == 0) H[i, j] = mean;
            for (int it2 = 0; it2 < 500; it2++)
                for (int i = 0; i < n; i++)
                    for (int j = 0; j < n; j++)
                    {
                        if (K[i, j] != 0) continue;
                        float s = 0; int c = 0;
                        if (i > 0 && K[i - 1, j] != 2) { s += H[i - 1, j]; c++; }
                        if (i < n - 1 && K[i + 1, j] != 2) { s += H[i + 1, j]; c++; }
                        if (j > 0 && K[i, j - 1] != 2) { s += H[i, j - 1]; c++; }
                        if (j < n - 1 && K[i, j + 1] != 2) { s += H[i, j + 1]; c++; }
                        if (c > 0) H[i, j] = s / c;
                    }
            var tv = new List<Vector3>(); var tt2 = new List<int>(); var idx = new Dictionary<int, int>(); int cells = 0;
            int V(int i, int j)
            {
                int key = i * n + j; if (idx.TryGetValue(key, out var v)) return v;
                float x = c0.x - half + i * cell, z = c0.y - half + j * cell;
                float jit = K[i, j] == 0 ? 0.05f * (Mathf.PerlinNoise(x * 0.4f, z * 0.4f) - 0.5f) : 0f;
                tv.Add(new Vector3(x, H[i, j] + jit, z)); idx[key] = tv.Count - 1; return tv.Count - 1;
            }
            for (int i = 0; i + 1 < n; i++)
                for (int j = 0; j + 1 < n; j++)
                {
                    var ks = new[] { K[i, j], K[i + 1, j], K[i, j + 1], K[i + 1, j + 1] };
                    if (ks.Any(k => k == 2) || ks.All(k => k == 1)) continue;
                    float x = c0.x - half + (i + 0.5f) * cell, z = c0.y - half + (j + 0.5f) * cell;
                    if ((x - c0.x) * (x - c0.x) + (z - c0.y) * (z - c0.y) > half * half) continue;
                    int a = V(i, j), b = V(i + 1, j), c = V(i, j + 1), e = V(i + 1, j + 1);
                    tt2.AddRange(new[] { a, c, e, a, e, b }); cells++;
                }
            if (cells > 0) WorldMesh(holder, "GroundSkirt", tv, tt2, snowM, true, true);
            Debug.Log($"ExteriorRealism: ground skirt {cells} cells of {cell} m over the yard's gaps ({nk} known samples, mean {mean:F2})");
        }

        // ---- weathering decals: grime at the wall base over the beds, streaks under the upper sills (sparing; angle fade keeps them off flats)
        int decals = 0;
        Material DecalMat(string n, string tex)
        {
            string path = $"Assets/Materials/Greybox/{n}.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(Shader.Find("HDRP/Decal")); AssetDatabase.CreateAsset(m, path); }
            string tp = $"Assets/Textures/Exterior/{tex}";
            if (AssetImporter.GetAtPath(tp) is TextureImporter ti && (ti.alphaIsTransparency == false || ti.wrapMode != TextureWrapMode.Clamp)) { ti.alphaIsTransparency = true; ti.wrapMode = TextureWrapMode.Clamp; ti.SaveAndReimport(); }
            m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tp)); m.SetColor("_BaseColor", Color.white);
            m.SetFloat("_AffectAlbedo", 1f); m.SetFloat("_AffectNormal", 0f); m.SetFloat("_AffectSmoothness", 0f); m.SetFloat("_AffectAO", 0f); m.SetFloat("_AffectMetal", 0f);
            HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m); return m;
        }
        var grime = DecalMat("HiFi_DecalGrime", "grime_base.png"); var streak = DecalMat("HiFi_DecalStreak", "grime_streak.png");
        void Decal(Material m, float face, float z0, float z1, float y0, float y1, float fade = 1f)
        {   // on an x = face wall facing +x (spec z0..z1 -> world -z), projecting toward -x
            var g = new GameObject("Decal_" + m.name); g.transform.SetParent(holder.transform, false);
            g.transform.SetPositionAndRotation(new Vector3(face + 0.12f, (y0 + y1) / 2, -(z0 + z1) / 2), Quaternion.LookRotation(Vector3.left));
            var p = g.AddComponent<DecalProjector>(); p.material = m; p.size = new Vector3(z1 - z0, y1 - y0, 0.30f); p.pivot = new Vector3(0, 0, 0.15f);
            p.startAngleFade = 35f; p.endAngleFade = 60f; p.fadeFactor = fade; decals++;
        }
        foreach (var (z0, z1, x0) in new[] { (-1.155f, 2.864f, 9.647f), (2.864f, 8.0f, 10.37f), (11.43f, 16.21f, 10.37f), (16.21f, 20.157f, 9.506f) })
            for (float z = z0; z < z1 - 0.1f; z += 2.4f) Decal(grime, x0, z, Mathf.Min(z + 2.5f, z1), yU - 0.05f, yU + 0.75f, 0.8f);
        var S = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/exterior_shell.json"))));
        foreach (var w in S["upper_windows"])
        {
            string f = (string)w["face"]; if (f != "front" && f != "den_front" && f != "right_front") continue;
            float a0 = (float)w["a0"], a1 = (float)w["a1"], y0 = (float)w["y0"] - 0.075f;
            Decal(streak, (float)w["d"], a0 - 0.12f, a1 + 0.12f, y0 - 0.55f, y0, 0.6f);
        }
        Debug.Log($"ExteriorRealism: steps rebuilt ({hidden} step boxes' renderers off, colliders kept), railings {iv.Count / 8} bars, {mounds} snow mounds, {nSnow} snow surfaces retextured, {decals} decals, road {(road != null ? road.name : "MISSING")}");
    }

    // Volumes, falling snow and camera settings (after Player): the look outside changes, inside it is restored
    static void ExteriorLook(float gy)
    {
        var dayLayer = GameObject.Find("Upstairs/Daylight/DayLayer");
        var lamps = Object.FindObjectsByType<HouseNightMode>(FindObjectsInactive.Include, FindObjectsSortMode.None).FirstOrDefault()?.nightLayer;
        if (dayLayer == null || lamps == null) { Debug.LogWarning("ExteriorLook: no day/night layer"); return; }
        VolumeProfile Prof(string n) { string p = $"Assets/Settings/{n}.asset"; AssetDatabase.DeleteAsset(p); var v = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(v, p); return v; }
        T Add<T>(VolumeProfile v) where T : VolumeComponent { var c = v.Add<T>(true); AssetDatabase.AddObjectToAsset(c, v); return c; }
        void Look(VolumeProfile v, bool night)
        {
            var fog = Add<Fog>(v); fog.enabled.value = true; fog.colorMode.value = FogColorMode.SkyColor;
            fog.baseHeight.value = gy - 1.3f; fog.maximumHeight.value = night ? 14f : 30f; fog.meanFreePath.value = night ? 110f : 320f;   // distant trees fade; lights get halos at night
            fog.enableVolumetricFog.value = night; fog.albedo.value = night ? new Color(0.62f, 0.66f, 0.80f) : new Color(0.90f, 0.93f, 1f);
            fog.depthExtent.value = 45f; fog.anisotropy.value = 0.6f;
            var smh = Add<ShadowsMidtonesHighlights>(v);   // film 4382 (day): warm sunlit brick, slightly cool shade; film 10 / Pietro (night): blue-violet shadows, warm lights
            smh.shadows.value = night ? new Vector4(0.90f, 0.93f, 1.12f, -0.05f) : new Vector4(0.97f, 0.99f, 1.04f, 0f);
            smh.highlights.value = night ? new Vector4(1.10f, 1.0f, 0.88f, 0f) : new Vector4(1.03f, 1.0f, 0.96f, 0f);
            var vig = Add<Vignette>(v); vig.intensity.value = night ? 0.28f : 0.14f; vig.smoothness.value = 0.5f;
            var ssr = Add<ScreenSpaceReflection>(v); ssr.enabled.value = true; ssr.minSmoothness = 0.75f; ssr.smoothnessFadeStart = 0.8f;
            var bl = Add<Bloom>(v); bl.intensity.value = night ? 0.8f : 0.12f; bl.scatter.value = night ? 0.78f : 0.65f; bl.threshold.value = night ? 0.3f : 1f;
            if (night)
            {   // low night exposure (Pietro: the facade nearly a silhouette, the lights do the work)
                var ex = Add<Exposure>(v); ex.mode.value = ExposureMode.Automatic; ex.limitMin.value = 5.6f; ex.limitMax.value = 12f;   // tuned live against Pietro
            }
        }
        var pd = Prof("ExteriorDay"); Look(pd, false); var pn = Prof("ExteriorNight"); Look(pn, true);
        var dv = new GameObject("ExteriorLook_Day").AddComponent<Volume>(); dv.transform.SetParent(dayLayer.transform, false); dv.isGlobal = true; dv.priority = 20f; dv.sharedProfile = pd;
        var nv = new GameObject("ExteriorLook_Night").AddComponent<Volume>(); nv.transform.SetParent(lamps.transform, false); nv.isGlobal = true; nv.priority = 20f; nv.sharedProfile = pn;
        // inside the skin: the interior's own values (fog off, neutral grade, HDRP's default bloom, the house exposure), blending over 0.6 m
        var pi = Prof("InteriorRestore");
        var defs = AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/HDRPDefaultResources/DefaultSettingsVolumeProfile.asset");
        var gv = AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Settings/GreyboxVolume.asset");
        T Clone<T>(VolumeProfile src) where T : VolumeComponent
        {   // the exact component the interior already gets (HDRP's default profile, or the house's global volume), every field overridden
            T c = src != null && src.TryGet<T>(out var have) ? Object.Instantiate(have) : ScriptableObject.CreateInstance<T>();
            c.name = typeof(T).Name; c.active = true; c.SetAllOverridesTo(true); pi.components.Add(c); AssetDatabase.AddObjectToAsset(c, pi); return c;
        }
        Clone<Fog>(defs).enabled.value = false; Clone<ShadowsMidtonesHighlights>(defs); Clone<Vignette>(defs); Clone<Bloom>(defs);
        Clone<ScreenSpaceReflection>(defs).enabled.value = false;   // the interior as before (no SSR)
        Clone<Exposure>(gv != null && gv.Has<Exposure>() ? gv : defs);
        var inside = new GameObject("InteriorRestoreVolume"); inside.transform.SetParent(dayLayer.transform.root, false);
        inside.layer = 2;   // Ignore Raycast: its trigger boxes never meet a gate's or a placement's ray
        var iv = inside.AddComponent<Volume>(); iv.isGlobal = false; iv.priority = 25f; iv.blendDistance = 0.6f; iv.sharedProfile = pi;
        var S = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/exterior_shell.json"))));
        int boxes = 0;
        foreach (var q in S["roofs"])
        {   // each skin solid's wall rectangle (spec x, z) from the basement to its ridge, 0.15 m inside the brick
            var w = q["walls"]; if (w == null || w.Count() != 4) continue;
            float x0 = (float)w[0] + 0.15f, x1 = (float)w[1] - 0.15f, z0 = (float)w[2] + 0.15f, z1 = (float)w[3] - 0.15f;
            if (x1 - x0 < 0.5f || z1 - z0 < 0.5f) continue;
            float top = (float)q["eave"] + (float)q["tan"] * Mathf.Min(x1 - x0, z1 - z0) / 2f + 0.5f;
            var bc = inside.AddComponent<BoxCollider>(); bc.isTrigger = true;
            bc.center = new Vector3((x0 + x1) / 2, (gy - 3f + top) / 2, -(z0 + z1) / 2); bc.size = new Vector3(x1 - x0, top - (gy - 3f), z1 - z0); boxes++;
        }
        // interior lamps add nothing to the outside fog (they would glow through the walls; cheaper too); the yard's lights keep theirs
        var ext = GameObject.Find("Exterior"); int dimmed = 0;
        foreach (var l in Object.FindObjectsByType<HDAdditionalLightData>(FindObjectsInactive.Include, FindObjectsSortMode.None))
        {
            var lt = l.GetComponent<Light>(); if (lt == null || lt.type == LightType.Directional) continue;
            if (ext != null && l.transform.IsChildOf(ext.transform)) { l.volumetricDimmer = 0.6f; continue; }
            if (l.name.StartsWith("PorchLantern") || l.name.StartsWith("LampPost") || l.name.StartsWith("ShrubGlow")) { l.volumetricDimmer = 0.6f; continue; }
            l.volumetricDimmer = 0f; dimmed++;
        }

        // falling snow round the camera (Pietro; film 10 credits): small streaked flakes + a few large soft ones near the lens; F toggles
        var player = Object.FindObjectsByType<FpsController>(FindObjectsInactive.Include, FindObjectsSortMode.None).FirstOrDefault();
        if (player != null && player.cam != null)
        {
            var root = new GameObject("Snowfall"); root.transform.SetParent(player.cam, false);
            root.AddComponent<SnowfallGate>().house = inside.GetComponents<BoxCollider>();   // off while the camera is inside (the trigger alone let flakes show indoors)
            Material Flake(string n, string tex, float a)
            {
                string tp = $"Assets/Textures/Exterior/{tex}";
                if (AssetImporter.GetAtPath(tp) is TextureImporter ti && !ti.alphaIsTransparency) { ti.alphaIsTransparency = true; ti.wrapMode = TextureWrapMode.Clamp; ti.SaveAndReimport(); }
                var m = Mat(n, new Color(0.92f, 0.94f, 0.97f, a));
                m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tp));
                m.SetFloat("_SurfaceType", 1f); m.SetFloat("_BlendMode", 0f); m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_Smoothness", 0f);
                m.SetFloat("_TransparentWritingMotionVec", 0f); m.SetFloat("_EnableFogOnTransparent", 1f);
                HDMaterial.ValidateMaterial(m); return m;
            }
            void Sys(string n, Material m, Vector3 at, Vector3 box, float rate, float life, Vector2 size, float fall, float noise, bool streak, int max)
            {
                var g = new GameObject(n); g.transform.SetParent(root.transform, false); g.transform.localPosition = at;
                var ps = g.AddComponent<ParticleSystem>(); ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                var main = ps.main; main.loop = true; main.prewarm = true; main.duration = 5f; main.startLifetime = life; main.startSpeed = 0f;
                main.startSize = new ParticleSystem.MinMaxCurve(size.x, size.y); main.simulationSpace = ParticleSystemSimulationSpace.World; main.maxParticles = max;
                main.scalingMode = ParticleSystemScalingMode.Hierarchy;
                var em = ps.emission; em.rateOverTime = rate;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = box;
                var vel = ps.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
                vel.x = new ParticleSystem.MinMaxCurve(-0.15f, 0.25f); vel.y = new ParticleSystem.MinMaxCurve(-fall * 1.2f, -fall * 0.8f); vel.z = new ParticleSystem.MinMaxCurve(-0.2f, 0.2f);
                var nz = ps.noise; nz.enabled = true; nz.strength = noise; nz.frequency = 0.35f; nz.scrollSpeed = 0.2f;
                var col = ps.sizeOverLifetime; col.enabled = true; col.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.EaseInOut(0, 0.6f, 1, 1f));
                var trg = ps.trigger; trg.enabled = true; trg.inside = ParticleSystemOverlapAction.Kill; trg.outside = ParticleSystemOverlapAction.Ignore;
                foreach (var bc in inside.GetComponents<BoxCollider>()) trg.AddCollider(bc);   // no snow inside the house (it still falls past the windows)
                var r = g.GetComponent<ParticleSystemRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
                r.renderMode = streak ? ParticleSystemRenderMode.Stretch : ParticleSystemRenderMode.Billboard; r.velocityScale = streak ? 0.035f : 0f; r.lengthScale = 1f;
                r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off;
                ps.Play();
            }
            Sys("Flakes", Flake("HiFi_SnowFlake", "flake.png", 0.9f), new Vector3(0, 5f, 9f), new Vector3(34f, 12f, 30f), 2600f, 8f, new Vector2(0.010f, 0.022f), 1.1f, 0.45f, true, 24000);
            Sys("NearFlakes", Flake("HiFi_SnowBokeh", "bokeh.png", 0.35f), new Vector3(0, 1.5f, 2.6f), new Vector3(5f, 3.5f, 3f), 18f, 4f, new Vector2(0.04f, 0.09f), 0.7f, 0.3f, false, 120);
            var hd = player.cam.GetComponent<HDAdditionalCameraData>();
            if (hd != null)
            {
                hd.dithering = true;   // the night sky's 8-bit banding (walk note 20:46)
                hd.volumeLayerMask |= 1 << 2;   // the interior restore volume lives on Ignore Raycast (its trigger boxes must not meet the gates' rays)
                // screen-space reflections for the wet street (HDRP.asset supportSSR 1); the volumes switch them on outside only
                hd.customRenderingSettings = true;
                hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)FrameSettingsField.SSR] = true;
                hd.renderingPathCustomFrameSettings.SetEnabled(FrameSettingsField.SSR, true);
            }
        }
        Debug.Log($"ExteriorLook: day/night exterior volumes (priority 20), interior restore ({boxes} skin boxes, priority 25), {dimmed} interior lamps out of the fog, snowfall {(player != null ? "on the camera (F)" : "MISSING")}");
    }
}
