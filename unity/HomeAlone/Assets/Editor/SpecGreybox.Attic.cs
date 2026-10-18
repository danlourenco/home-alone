using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;

// The attic shell (Oct 18 2026, TRIAL; changes/2026-10-18-attic-shell.json, DEVIATIONS 90): tools/house/hifi_attic.py -> Attic.glb
// (spec coordinates above the upper floor). The walk/envelope layer is the attic_stair boxes from reconcile.py (floor, knee and end
// walls, the dormer's cheeks and window wall, the lid, the balustrade, the bed, chimney and stove): their renderers are hidden here and
// their colliders stay (room-upgrade). The steps and the well's framing keep their grey-box look. The casement leaves are hung on
// hinges at their outer jambs and opened outward by attic.dormer.open_deg (the zipline, film 10950); the opening has no collider.
public static partial class SpecGreybox
{
    static Material AtticGlow(string n, Color c, float nits, float smooth)
    {
        var m = Mat(n, c); m.SetFloat("_Smoothness", smooth); m.SetColor("_EmissiveColor", c * nits);
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(m); return m;
    }

    static void Attic(GameObject root)
    {
        var hs = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.json"))));
        var A = hs["attic_stair"]?["attic"]; if (A == null) return;
        int hidden = 0;
        var st = root.transform.Find("AtticStair");
        if (st != null)
            foreach (Transform c in st)
                if (c.name.StartsWith("attic_") && !c.name.StartsWith("attic_step") && !c.name.StartsWith("attic_wall_") && c.GetComponent<MeshRenderer>() is MeshRenderer mr)
                { Object.DestroyImmediate(mr); hidden++; }
        var g = PlaceHiFi(root, 0f, "Attic", new Dictionary<string, Material> {
            ["AT_Boards"] = TexMat("HiFi_AtticBoards", "wood_floor", new Color(0.70f, 0.52f, 0.36f), 1.2f, 0.2f),
            ["AT_Floor"] = TexMat("HiFi_AtticFloor", "dark_wooden_planks", new Color(0.85f, 0.8f, 0.75f), 1.6f, 0.2f),
            ["AT_Rafter"] = TexMat("HiFi_AtticRafter", "oak_veneer_01", new Color(0.55f, 0.38f, 0.24f), 1.0f, 0.2f),
            ["AT_Rail"] = TexMat("HiFi_AtticRail", "oak_veneer_01", new Color(0.85f, 0.68f, 0.48f), 1.0f, 0.3f),
            ["AT_Glass"] = mGlass,
            // the bed group (Oct 18): crib and lamp table in dark stained wood, the film's lamp (1410/1418: red-orange glass base, cream drum
            // shade), and bare bulbs in porcelain holders. Shade and bulb glow at night only (HouseNightMode darkens HiFi_Shade*/HiFi_Bulb* by day)
            ["AT_Brick"] = TexMat("HiFi_AtticBrick", "red_brick_03", new Color(0.70f, 0.55f, 0.50f), 1.2f, 0.15f),   // film 1418: red-brown brick, pale mortar (the GLB's flat colour read pink)
            ["AT_Wood"] = TexMat("HiFi_AtticWood", "oak_veneer_01", new Color(0.30f, 0.17f, 0.09f), 1.0f, 0.35f),
            ["AT_LampGlass"] = AtticGlow("HiFi_AtticLampGlass", new Color(0.75f, 0.20f, 0.05f), 0f, 0.85f),
            ["AT_Shade"] = AtticGlow("HiFi_ShadeAtticCream", new Color(0.92f, 0.87f, 0.74f), 900f, 0.2f),
            ["AT_Bulb"] = AtticGlow("HiFi_BulbAttic", new Color(1f, 0.90f, 0.75f), 4000f, 0.6f),
            ["AT_Porcelain"] = AtticGlow("HiFi_AtticPorcelain", new Color(0.90f, 0.89f, 0.86f), 0f, 0.6f) });
        if (g == null) { Debug.Log("Attic: Attic.glb missing"); return; }
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        var D = A["dormer"];
        float dz = (float)D["z"], dw = (float)D["opening"][0], xo = (float)D["face_x"] - (float)A["wall_t"], deg = (float)D["open_deg"];
        foreach (var (s, hz, a) in new[] { ("L", dz - dw / 2 + 0.02f, deg), ("R", dz + dw / 2 - 0.02f, -deg) })
        {   // hinge on the outer edge of the leaf's outside face; L's leaf runs to -world z, R's to +world z: both swing to -x (outward)
            var hinge = new GameObject("CasementHinge_" + s); hinge.transform.SetParent(g.transform, false);
            hinge.transform.position = new Vector3(xo, 0f, -hz);
            foreach (var t in g.GetComponentsInChildren<Transform>().Where(t => t.name.StartsWith("Casement" + s + "_")).ToList())
            { t.SetParent(hinge.transform, true); t.gameObject.isStatic = false; }
            hinge.transform.localRotation = Quaternion.Euler(0f, a, 0f);
        }
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            string mn = r.sharedMaterial != null ? r.sharedMaterial.name : "";
            if (mn.StartsWith("HiFi_Shade") || mn.StartsWith("HiFi_Bulb")) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;   // the light sits inside
        }
        // the lights (night only: SpecGreybox.Daylight moves "Upstairs/AtticFixtures" into the night layer): the bedside lamp in its shade and
        // the two bare bulbs, 2700 K, shadowed (BakeLighting makes them Mixed for the Night scenario like the den's lamps)
        var fx = Child(root, "AtticFixtures"); float yf = (float)A["floor_y"];
        void Lamp(string n, float x, float y, float z, float lm, float k, float range)
        {
            var l = new GameObject(n).AddComponent<Light>(); l.transform.SetParent(fx.transform, false);
            l.transform.position = new Vector3(x, y, -z); l.type = LightType.Point; l.range = range;
            l.gameObject.AddComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalLightData>();   // first: adding it resets the intensity
            l.lightUnit = UnityEngine.Rendering.LightUnit.Lumen; l.intensity = lm; l.useColorTemperature = true; l.colorTemperature = k; l.shadows = LightShadows.Soft;
        }
        var Lp = A["lamp"]; var sh = Lp["shade"];
        Lamp("AtticLamp_bed", (float)Lp["at"][0], yf + 0.012f + (float)Lp["at"][1] + ((float)sh[2] + (float)sh[3]) / 2f, (float)Lp["at"][2], (float)Lp["lumens"], (float)Lp["kelvin"], 7f);
        foreach (var b in A["bulbs"]) Lamp("AtticBulb_" + (string)b["name"], (float)b["at"][0], (float)b["bulb_y"], (float)b["at"][1], (float)b["lumens"], (float)b["kelvin"], 9f);
        Debug.Log($"Attic: placed, {hidden} grey-box renderers hidden (colliders kept), casements open {deg} deg, {fx.transform.childCount} lights");
    }
}
