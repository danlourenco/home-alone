using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// The basement shell (Oct 18 2026, TRIAL; changes/2026-10-18-basement-shell.json, DEVIATIONS 91). The walk/envelope layer is the
// basement + basement_areaway boxes of spec/house_spec.ground.json (tools/house/reconcile.py basement_spec): slab, foundation walls,
// the flight's solid steps and balustrade colliders, the landing behind Kevin's door, the stone areaway. Steps, rails, appliances, the
// furnace and the open door leaf keep their colliders with their renderers removed: tools/house/hifi_basement.py (Basement.glb) draws
// them (open treads, the film's furnace, the laundry, bulbs, the chute's foot, windows, the areaway door). The rest stay as boxes,
// textured here (painted block, concrete, brick, stone, beadboard). The bulbs stay on by day and night (no daylight reaches it).
public static partial class SpecGreybox
{
    static JObject GroundSpecJ() => JObject.Parse(File.ReadAllText(GroundPath));

    // the basement's room volumes (world): its storey, the slot through the plate over its stair, the areaway
    internal static IEnumerable<(string name, List<Vector2> pts, float y0, float y1)> BasementRooms(float gy)
    {
        var gj = GroundSpecJ();
        foreach (var key in new[] { "basement", "basement_areaway" })
            if (gj[key] is JObject st)
                foreach (var b in st["boxes"].Where(b => (string)b["kind"] == "room"))
                    yield return ((string)b["name"], b["poly"].Select(q => new Vector2((float)q[0], -(float)q[1])).ToList(), gy + (float)b["y"][0], gy + (float)b["y"][1]);
    }

    static List<Vector3> Basement(GameObject groot, JObject gj, float gy)
    {
        if (gj["basement"] == null) return new List<Vector3>();
        var path = Stair(groot, gj["basement"], false, "Basement", dress: false).Select(q => q + Vector3.up * gy).ToList();
        Stair(groot, gj["basement_areaway"], false, "BasementAreaway", dress: false);
        var paint = TexMat("HiFi_BasementBlock", "concrete_floor_worn_001", new Color(0.62f, 0.56f, 0.48f), 1.5f, 0.15f);   // film 2430/10104: dull grey-brown walls (painted_concrete is green)
        var slab = TexMat("HiFi_BasementSlab", "concrete_floor_worn_001", new Color(0.70f, 0.68f, 0.64f), 2.0f, 0.25f);
        var brick = TexMat("HiFi_BasementBrick", "red_brick_03", new Color(0.75f, 0.60f, 0.55f), 1.2f, 0.15f);
        var stone = TexMat("HiFi_AreawayStone", "stone_wall", new Color(0.65f, 0.63f, 0.60f), 1.6f, 0.2f);
        var bead = TexMat("HiFi_BasementBeadboard", "wood_floor", new Color(0.85f, 0.50f, 0.28f), 0.8f, 0.3f);   // film 10300: orange vertical boards
        var post = TexMat("HiFi_BasementPost", "oak_veneer_01", new Color(0.55f, 0.40f, 0.26f), 1.0f, 0.2f);
        var plank = TexMat("HiFi_BasementLanding", "dark_wooden_planks", new Color(0.8f, 0.7f, 0.6f), 1.2f, 0.2f);
        int hidden = 0;
        foreach (var name in new[] { "Basement", "BasementAreaway" })
            foreach (Transform c in groot.transform.Find(name))
            {
                var mr = c.GetComponent<MeshRenderer>(); if (mr == null) continue;
                string n = c.name;
                bool hide = n.StartsWith("bsmt_step") || n.StartsWith("bsmt_rail") || n == "bsmt_newel" || n == "bsmt_furnace" || n == "bsmt_washer" ||
                            n == "bsmt_dryer" || n == "bsmt_sink" || n == "bsmt_door_leaf" || n.StartsWith("area_rail");
                if (hide) { Object.DestroyImmediate(mr); hidden++; continue; }
                mr.sharedMaterial = n.StartsWith("bsmt_wall") ? paint : n.StartsWith("bsmt_floor") ? slab : n == "bsmt_chimney" ? brick
                    : n.StartsWith("bsmt_post") ? post : n.StartsWith("bsmt_landing") ? plank : n == "bsmt_stairwall_n" ? bead
                    : n.StartsWith("area_wall") ? stone : n.StartsWith("area_") ? slab : mr.sharedMaterial;
                c.gameObject.isStatic = true;
            }
        var glow = Mat("HiFi_FurnaceGlow", new Color(1f, 0.45f, 0.1f));
        glow.SetColor("_EmissiveColor", new Color(1f, 0.42f, 0.08f) * 40f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(glow);
        var bulbM = Mat("HiFi_BareBulb", new Color(1f, 0.92f, 0.75f));
        bulbM.SetColor("_EmissiveColor", new Color(1f, 0.8f, 0.55f) * 400f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(bulbM);
        var day = Mat("HiFi_BasementWindowLight", new Color(0.75f, 0.8f, 0.85f));
        day.SetColor("_EmissiveColor", new Color(0.7f, 0.78f, 0.9f) * 60f); UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(day);
        var green = Mat("HiFi_FurnaceGreen", new Color(0.10f, 0.19f, 0.14f)); green.SetFloat("_Smoothness", 0.45f);
        var duct = Mat("HiFi_GalvDuct", new Color(0.62f, 0.63f, 0.64f)); duct.SetFloat("_Metallic", 0.6f); duct.SetFloat("_Smoothness", 0.55f);
        var g = PlaceHiFi(groot, gy, "Basement", new Dictionary<string, Material> {
            ["BS_Joist"] = TexMat("HiFi_BasementJoist", "oak_veneer_01", new Color(0.26f, 0.17f, 0.10f), 1.0f, 0.15f),   // film 2466/10300: dark old joists
            ["BS_Tread"] = TexMat("HiFi_BasementTread", "oak_veneer_01", new Color(0.62f, 0.46f, 0.30f), 1.0f, 0.25f),
            ["BS_Rail"] = TexMat("HiFi_BasementRail", "oak_veneer_01", new Color(0.40f, 0.27f, 0.16f), 1.0f, 0.35f),
            ["BS_Shelf"] = TexMat("HiFi_BasementShelf", "oak_veneer_01", new Color(0.70f, 0.55f, 0.38f), 1.0f, 0.2f),
            ["BS_Furnace"] = green, ["BS_Duct"] = duct, ["BS_Metal"] = duct, ["BS_Brass"] = BrassMat(), ["BS_Glow"] = glow, ["BS_Bulb"] = bulbM,
            ["BS_Daylight"] = day, ["BS_Glass"] = mGlass });
        if (g == null) { Debug.Log("Basement: Basement.glb missing"); return path; }
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            r.gameObject.isStatic = true;
            if (r.name == "Bulbs" || r.name == "FurnaceFire" || r.name == "WindowGlass") r.shadowCastingMode = ShadowCastingMode.Off;
        }
        // the bulbs: the pull-cord light (film 10114-10126) and two more; 60 W (800 lm) 2700 K, on by day and night
        var B = gj["basement"]["basement"]; var L = B["light"];
        var pts = new List<(float x, float z, float y)> { ((float)L["x"], (float)L["z"], (float)L["bulb_y"]) };
        foreach (var q in L["more"]) pts.Add(((float)q[0], (float)q[1], (float)L["bulb_y"] + 0.15f));
        var lights = Child(groot, "BasementLights"); int i = 0;
        foreach (var (x, z, y) in pts)
        {
            var l = new GameObject($"BasementBulb_{i++}_Light").AddComponent<Light>(); l.transform.SetParent(lights.transform, false);
            l.transform.position = new Vector3(x, gy + y - 0.02f, -z); l.type = LightType.Point; l.range = 9f;
            l.gameObject.AddComponent<HDAdditionalLightData>();
            l.lightUnit = LightUnit.Lumen; l.intensity = 800f; l.useColorTemperature = true; l.colorTemperature = 2700f; l.shadows = LightShadows.Soft;
        }
        {   // the furnace's fire through the grate: a low orange light in front of it
            var F = B["furnace"]; float fx = ((float)F["x"][0] + (float)F["x"][1]) / 2, fz = (float)F["z"][0] - 0.25f;
            var l = new GameObject("BasementFurnaceFire_Light").AddComponent<Light>(); l.transform.SetParent(lights.transform, false);
            l.transform.position = new Vector3(fx, gy + (float)B["floor_y"] + 0.45f, -fz); l.type = LightType.Point; l.range = 4f;
            l.gameObject.AddComponent<HDAdditionalLightData>();
            l.lightUnit = LightUnit.Lumen; l.intensity = 250f; l.color = new Color(1f, 0.5f, 0.2f); l.shadows = LightShadows.None;
        }
        Debug.Log($"Basement: built, {hidden} grey-box renderers hidden (colliders kept), {pts.Count} bulbs + furnace glow");
        return path;
    }
}
