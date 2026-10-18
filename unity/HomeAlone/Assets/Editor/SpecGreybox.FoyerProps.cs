using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

// The foyer's furniture and decor as the film shows them (Oct 16 2026, TRIAL; changes/2026-10-16-foyer-finish.json): console,
// side chairs, pier mirror, bench, rugs, the stair gallery and the other pictures, poinsettias (tools/house/hifi_foyer_props.py ->
// FoyerProps.glb, data spec/dressing/foyer_props.json). The art and rug images ride in the .glb (public-domain works and invented
// patterns, tools/house/foyer_textures.py). The foyer dressing boxes they replace are hidden; their colliders stay the walk layer.
public static partial class SpecGreybox
{
    static void FoyerProps(GameObject root, float gy)
    {
        Material Cloth(string n, Color c) { var m = Mat(n, c); m.SetFloat("_Smoothness", 0.15f); return m; }
        Material TwoSided(string n, Color c) { var m = Mat(n, c); m.SetFloat("_DoubleSidedEnable", 1f); m.SetFloat("_CullMode", 0f); HDMaterial.ValidateMaterial(m); return m; }
        var gilt = Mat("HiFi_Gilt", new Color(0.60f, 0.45f, 0.21f)); gilt.SetFloat("_Metallic", 0.55f); gilt.SetFloat("_Smoothness", 0.42f);   // antique gilt, darker than the brass
        var glass = Mat("HiFi_MirrorGlass", new Color(0.86f, 0.86f, 0.84f)); glass.SetFloat("_Metallic", 1f); glass.SetFloat("_Smoothness", 0.96f);
        var g = PlaceHiFi(root, gy, "FoyerProps", new Dictionary<string, Material> {
            ["FP_Wood"] = TexMat("HiFi_DenWood", "cherry_veneer", new Color(0.414f, 0.29f, 0.34f), 1.0f, 0.45f),   // the den's mahogany (film 10673: very dark red-brown)
            ["FP_Red"] = Cloth("HiFi_FoyerSeat", new Color(0.42f, 0.03f, 0.045f)), ["FP_Green"] = Cloth("HiFi_FoyerVelvet", new Color(0.045f, 0.11f, 0.06f)),
            ["FP_Gilt"] = gilt, ["FP_Glass"] = glass, ["FP_Brass"] = BrassMat(), ["FP_Foil"] = FoilMat(),
            ["FP_Leaf"] = TwoSided("HiFi_DenLeaf", new Color(0.06f, 0.20f, 0.06f)), ["FP_BractRed"] = TwoSided("HiFi_DenBractRed", new Color(0.62f, 0.03f, 0.05f)),
            ["FP_BractWhite"] = TwoSided("HiFi_DenBractWhite", new Color(0.90f, 0.90f, 0.84f)), ["FP_Fringe"] = TwoSided("HiFi_RugFringe", new Color(0.80f, 0.76f, 0.66f)) });
        if (g == null) return;
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        string[] pre = { "console", "mirror_", "chair_", "bench", "runner_rug", "front_rug", "landing_painting", "picture_wall_picture" };
        int hidden = 0;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            if (r.transform.parent != null && r.transform.parent.name == "Dressing" && pre.Any(p => r.name.StartsWith(p))) { r.enabled = false; hidden++; }
        Debug.Log($"FoyerProps: placed, hid {hidden} dressing boxes");
        PurchasedPlants(root, gy);
        PurchasedRug(root, gy);
    }

    // The user's two Sketchfab rugs (mfb64, CC BY 4.0: CREDITS.md), decimated to ~32k triangles each and fitted by
    // tools/house/purchased_rugs.py into the gitignored Assets/Purchased/PurchasedRug.glb: FrontRug (the Nain) on the foyer's
    // front-rug box, LivingRug (the Heriz) on the living room's, Runner (cut from the Heriz photo) on the foyer runner's. Absent (a clone of the public repo): the generated rugs stay.
    // Runs after Living() (SpecGreybox.cs: Living is placed before FoyerProps), so both generated rugs exist to hide.
    static void PurchasedRug(GameObject root, float gy)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Purchased/PurchasedRug.glb");
        if (a == null) { Debug.Log("PurchasedRug: not present, generated rugs kept"); return; }
        var g = (GameObject)Object.Instantiate(a, root.transform); g.name = "PurchasedRug_HiFi"; g.transform.localPosition = new Vector3(0, gy, 0);
        foreach (var c in g.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        var hide = new Dictionary<string, string[]> { ["FoyerProps_HiFi"] = new[] { "Rug_RugFront", "Fringe_RugFront", "Rug_RugRunner", "Fringe_RugRunner" }, ["LivingBuiltins_HiFi"] = new[] { "Rug" } };
        int n = 0;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            for (var t = r.transform.parent; t != null; t = t.parent)
                if (hide.TryGetValue(t.name, out var names)) { if (names.Contains(r.name)) { r.enabled = false; n++; } break; }
        Debug.Log($"PurchasedRug: placed {g.GetComponentsInChildren<MeshRenderer>().Length} renderers, hid {n} generated rug renderers");
    }

    // The user's CGTrader plants (Royalty Free, no redistribution: Assets/Purchased/ is gitignored), fitted by
    // tools/house/purchased_plants.py to the measured boxes: the foyer ficus and every poinsettia in the foyer, den and living room.
    // Absent (a clone of the public repo): the generated plants stay. Present: the generated ones they replace are hidden.
    const string PurchasedPlantsPath = "Assets/Purchased/PurchasedPlants.glb";
    static void PurchasedPlants(GameObject root, float gy)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>(PurchasedPlantsPath);
        if (a == null) { Debug.Log("PurchasedPlants: not present, generated plants kept"); return; }
        var g = (GameObject)Object.Instantiate(a, root.transform); g.name = "PurchasedPlants_HiFi"; g.transform.localPosition = new Vector3(0, gy, 0);
        foreach (var c in g.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        var brass = BrassMat();
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            var ms = r.sharedMaterials;
            for (int i = 0; i < ms.Length; i++) if (ms[i] != null && ms[i].name.StartsWith("PP_Pot")) ms[i] = brass;   // the film's brass planter (2677/3888)
            r.sharedMaterials = ms; r.gameObject.isStatic = true;
        }
        // the generated plants these replace: renderer names under each model's root
        var hide = new Dictionary<string, string[]> {
            ["Tree_HiFi"] = null,                                                        // hifi_props.py: the Poly Haven tree and brass pot (all of it)
            ["FoyerDressing_HiFi"] = new[] { "Foil", "Bracts", "Leaves", "Cyathia" },   // hifi_dressing.py: the pedestal poinsettias
            ["FoyerProps_HiFi"] = new[] { "PoinFoil", "PoinLeaf", "BractRed", "BractWhite" },
            ["DenBuiltins_HiFi"] = new[] { "foil", "leaf", "bract_red", "bract_white" },   // hifi_den.py decor (the wicker pot stays: the white one sits in it)
            ["LivingBuiltins_HiFi"] = new[] { "PoinLeaf", "PoinBract" } };                 // hifi_living.py (its gold pot stays: the plant sits in it)
        int n = 0;
        foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            for (var t = r.transform.parent; t != null; t = t.parent)
                if (hide.TryGetValue(t.name, out var names))
                {
                    if (names == null || names.Any(x => r.name == x || r.name.StartsWith(x + "_") || r.name.StartsWith(x + "."))) { r.enabled = false; n++; }
                    break;
                }
        Debug.Log($"PurchasedPlants: placed {g.GetComponentsInChildren<MeshRenderer>().Length} renderers, hid {n} generated plant renderers");
    }
}
