using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// Bare winter trees (Oct 18 2026, decoration; user: "use realistic assets or 3d models for the bare trees instead of the simple stick
// figures"): tools/house/hifi_bare_trees.py -> BareTrees.glb (oak/elm/maple/ash x 2 variants, 3 LODs each, + the treehouse's crown).
// Every stick tree of the WinterNeighborhood ("Mature bare street tree", WinnetkaNeighborhood.NeighborhoodTree) is swapped one for one:
// same base, its height (the stick mesh's world bounds), a species and turn from its position; trunk capsule kept. The treehouse's
// crown sits at its world place on the trunk hifi_treehouse.py builds up to CROWN_JOIN. Called from Exterior() after the room cull.
public static partial class SpecGreybox
{
    static readonly string[] TreeVariants = { "oakA", "oakB", "elmA", "elmB", "mapleA", "mapleB", "ashA", "ashB" };

    static Material BarkMat(string n, string id, Color tint)
    {
        string dir = $"Assets/Textures/PolyHaven/{id}";
        var ti = AssetImporter.GetAtPath(dir + "/normal.jpg") as TextureImporter;
        if (ti != null && ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; ti.SaveAndReimport(); }
        var m = Mat(n, tint);   // UV0: the generator's bark UVs run round and along every branch (~0.9 m per tile)
        m.SetTexture("_BaseColorMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dir + "/albedo.jpg"));
        m.SetTexture("_NormalMap", AssetDatabase.LoadAssetAtPath<Texture2D>(dir + "/normal.jpg")); m.SetFloat("_NormalScale", 1f);
        m.SetFloat("_UVBase", 0f); m.SetFloat("_Smoothness", 0.08f); m.enableInstancing = true;
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); EditorUtility.SetDirty(m); return m;
    }

    // a yard tree's turn that keeps its limbs off the house (the crowns spread ~8 m; a random turn put limbs through the walls):
    // the turn (30 deg steps, the hashed one first) with the most clearance between its limbs below the roof and the house's plan box.
    // ponytail: one box round the house (Unity x -9.7..12, z -23.7..3.4, y < 7.4: Exterior.glb bounds); test the room volumes if a tree must stand closer
    static float ClearYaw(Mesh m, Quaternion q0, Vector3 pos, float sc, float yaw0)
    {
        var vs = m.vertices; float best = -1f, bestYaw = yaw0;
        for (int k = 0; k < 12; k++)
        {
            float yaw = (yaw0 + 30f * k) % 360f, clear = 99f; var q = Quaternion.Euler(0, yaw, 0);
            for (int i = 0; i < vs.Length; i += 23)
            {
                var w = pos + q * (q0 * vs[i] * sc); if (w.y > 7.4f) continue;
                float dx = Mathf.Max(-9.7f - w.x, 0f, w.x - 12f), dz = Mathf.Max(-23.7f - w.z, 0f, w.z - 3.4f);
                clear = Mathf.Min(clear, Mathf.Sqrt(dx * dx + dz * dz));
            }
            if (clear > best + 0.5f) { best = clear; bestYaw = yaw; }
        }
        if (best < 1f) Debug.LogWarning($"Trees: tree at {pos} keeps only {best:F1} m from the house");
        return bestYaw;
    }

    static void Trees(GameObject ext)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/BareTrees.glb");
        if (a == null) { Debug.LogWarning("Trees: BareTrees.glb missing; stick trees kept"); return; }
        var meshes = a.GetComponentsInChildren<MeshFilter>(true).GroupBy(f => f.name).Select(q => q.First()).ToDictionary(f => f.name, f => (f.sharedMesh, a.transform.InverseTransformPoint(f.transform.position), Quaternion.Inverse(a.transform.rotation) * f.transform.rotation));
        var rough = BarkMat("HiFi_BTBarkRough", "bark_willow_02", new Color(0.62f, 0.60f, 0.58f));   // film 4382/6810: grey-brown winter bark
        var brown = BarkMat("HiFi_BTBarkBrown", "bark_brown_02", new Color(0.70f, 0.66f, 0.62f));
        var snow = Mat("HiFi_BTSnow", new Color(0.80f, 0.83f, 0.86f)); snow.SetFloat("_Smoothness", 0.25f); snow.enableInstancing = true;
        long tris0 = 0; int n = 0;

        GameObject Place(string v, Transform parent, Vector3 pos, float yaw, float scale, string name)
        {
            var g = new GameObject(name); g.transform.SetParent(parent, false);
            g.transform.SetPositionAndRotation(pos, Quaternion.Euler(0, yaw, 0)); g.transform.localScale = Vector3.one * scale;
            var lods = new LOD[3];
            float[] h = { 0.55f, 0.18f, 0.012f };   // screen height: LOD0 within ~25 m of a 15 m tree (fov 50), LOD1 to ~75 m, LOD2 beyond
            for (int l = 0; l < 3; l++)
            {
                var (mesh, p, q) = meshes[$"{v}_LOD{l}"];
                var c = new GameObject($"{v}_LOD{l}"); c.transform.SetParent(g.transform, false); c.transform.localPosition = p; c.transform.localRotation = q;
                c.AddComponent<MeshFilter>().sharedMesh = mesh;
                var r = c.AddComponent<MeshRenderer>();
                r.sharedMaterials = new[] { v.StartsWith("oak") || v.StartsWith("ash") ? rough : brown, snow };
                r.shadowCastingMode = ShadowCastingMode.On;
                c.isStatic = true; lods[l] = new LOD(h[l], new Renderer[] { r });
                if (l == 0) { for (int s = 0; s < mesh.subMeshCount; s++) tris0 += mesh.GetIndexCount(s) / 3; }
            }
            var lg = g.AddComponent<LODGroup>(); lg.SetLODs(lods); lg.RecalculateBounds(); g.isStatic = true; n++;
            return g;
        }

        var sticks = ext.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.name == "Mature bare street tree").ToList();
        var houseC = new Vector3(0f, 0f, -9.7f);   // our house's middle (Unity), for the yard trees
        foreach (var st in sticks)
        {
            var b = st.bounds; var pos = st.transform.position; var parent = st.transform.parent;
            int key = Mathf.Abs(Mathf.RoundToInt(pos.x * 7.3f + pos.z * 3.1f));
            float d = Vector3.Distance(new Vector3(pos.x, 0, pos.z), houseC);
            // the yard's own trees are big oaks (film 4382's right-hand oak, 6810); elsewhere every species in turn
            string v = d < 22f ? (key % 2 == 0 ? "oakA" : "oakB") : TreeVariants[key % TreeVariants.Length];
            float baseH = meshes[v + "_LOD0"].sharedMesh.bounds.size.y - 0.35f;   // trunk starts 0.35 below grade
            float target = Mathf.Clamp(b.size.y * 1.15f, 9f, 21f);                // stick trees read short: ~15 % taller, 9-21 m
            float sc = target / baseH, yaw = key * 47 % 360;
            if (d < 30f) yaw = ClearYaw(meshes[v + "_LOD0"].sharedMesh, meshes[v + "_LOD0"].Item3, pos, sc, yaw);
            var g = Place(v, parent, pos, yaw, sc, "Bare winter tree " + v);
            var cap = st.GetComponent<CapsuleCollider>();
            if (cap != null) { var cc = g.AddComponent<CapsuleCollider>(); float s = g.transform.localScale.x; cc.radius = 0.42f / s; cc.height = 4f / s; cc.center = new Vector3(0, 2f / s, 0); }
            Object.DestroyImmediate(st.gameObject);
        }
        // the treehouse's crown: world coordinates already (spec x, world y, z), on the trunk Treehouse.glb ends at CROWN_JOIN
        var th = GameObject.Find("Treehouse_HiFi");
        Place("TreehouseCrown", th != null ? th.transform.parent : ext.transform, Vector3.zero, 0f, 1f, "Treehouse crown");
        Debug.Log($"Trees: {sticks.Count} stick trees replaced, {n} bare trees placed (LODGroup x3), LOD0 triangles if all near {tris0}");
    }
}
