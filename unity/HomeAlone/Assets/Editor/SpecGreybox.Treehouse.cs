using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;

// Kevin's treehouse and the zipline (Oct 18 2026, TRIAL; changes/2026-10-18-treehouse-zipline.json): tools/house/hifi_treehouse.py ->
// Treehouse.glb (spec x, z; world y) from spec/dressing/treehouse.json. The walk layer is invisible boxes here (deck, cabin walls with
// the door gap, porch rail open at the ladder, trunk); the ladder is climbed and the rope ridden by Scripts/ZipLine.cs (E), which this
// fills with the anchors, landing and ladder points. Called from Attic(): the rope's high end is in the attic.
public static partial class SpecGreybox
{
    static void Treehouse(GameObject root)
    {
        var T = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/treehouse.json"))));
        float F(JToken t) => (float)t;
        Vector3 W(JToken p) => new Vector3(F(p[0]), F(p[1]), -F(p[2]));   // spec (x, world y, z) -> Unity
        var rope = Mat("HiFi_THRope", new Color(0.62f, 0.50f, 0.32f));
        var chrome = Mat("HiFi_THChrome", new Color(0.86f, 0.87f, 0.89f)); chrome.SetFloat("_Metallic", 1f); chrome.SetFloat("_Smoothness", 0.85f);
        var g = PlaceHiFi(root, 0f, "Treehouse", new Dictionary<string, Material> {
            ["TH_Board2"] = TexMat("HiFi_THBoardDark", "old_planks_02_h", new Color(0.62f, 0.60f, 0.56f), 1.4f, 0.1f),
            ["TH_Board"] = TexMat("HiFi_THBoard", "old_planks_02_h", new Color(0.85f, 0.83f, 0.78f), 1.4f, 0.1f),   // film 6810: grey, weathered
            ["TH_Timber"] = TexMat("HiFi_THTimber", "weathered_planks_h", new Color(1.0f, 0.95f, 0.88f), 1.2f, 0.1f),
            ["TH_Ladder"] = TexMat("HiFi_THLadder", "weathered_planks_h", new Color(0.8f, 0.72f, 0.62f), 1.2f, 0.15f),
            ["TH_Bark"] = TexMat("HiFi_THBark", "bark_brown_02", new Color(0.85f, 0.82f, 0.78f), 1.5f, 0.05f),
            ["TH_Rope"] = rope, ["TH_Chrome"] = chrome,
            ["TH_Bulb"] = AtticGlow("HiFi_BulbTreehouse", new Color(1f, 0.90f, 0.75f), 4000f, 0.6f) });
        if (g == null) { Debug.Log("Treehouse: Treehouse.glb missing"); return; }
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>()) r.gameObject.isStatic = true;
        // the trolley and the rider stand-in move: group them at the origin (their meshes are built round the rope contact there)
        var trolley = new GameObject("ZipTrolley"); trolley.transform.SetParent(g.transform, false);
        var riderG = new GameObject("ZipRider"); riderG.transform.SetParent(trolley.transform, false);
        foreach (var t in g.GetComponentsInChildren<Transform>().Where(t => t.name.StartsWith("ZipTrolley_") || t.name.StartsWith("ZipRider_")).ToList())
        { t.SetParent(t.name.StartsWith("ZipRider_") ? riderG.transform : trolley.transform, true); t.gameObject.isStatic = false; }

        var S = T["site"]; var D = T["deck"]; var C = T["cabin"]; var K = T["trunk"]; var L = T["ladder"]; var R = T["rope"]; var Rd = T["ride"];
        float cx = F(S["center"][0]), cz = F(S["center"][1]), G = F(S["grade_y"]), DY = G + F(D["top_above_grade"]);
        float X0 = cx - F(D["depth"]) / 2, X1 = cx + F(D["depth"]) / 2, Z0 = cz - F(D["width"]) / 2, Z1 = cz + F(D["width"]) / 2;
        float XB = X0 + 0.05f, XF = XB + F(C["depth"]), hb = F(C["base_w"]) / 2, HF = F(C["front_h"]), RH = F(D["rail_h"]);
        float dz0 = F(C["door"]["z"][0]), dz1 = F(C["door"]["z"][1]), lx = F(L["top"][0]), lw = F(L["w"]);
        float tx = F(K["at"][0]), tz = F(K["at"][1]), tr = F(K["r"]);
        // walk colliders (spec x, z -> Box takes Unity z = -spec z), renderers removed
        var walk = Child(root, "TreehouseWalk");
        void B(string n, float x0, float x1, float z0, float z1, float y0, float y1) => Box(walk, n, x0, x1, -z1, -z0, y0, y1, mWall);
        B("th_deck", X0, X1, Z0, Z1, DY - 0.15f, DY);
        B("th_wall_back", XB - 0.04f, XB, cz - hb, cz + hb, DY, DY + HF);
        B("th_wall_mz", XB, XF, cz - hb - 0.04f, cz - hb, DY, DY + HF);
        B("th_wall_pz", XB, XF, cz + hb, cz + hb + 0.04f, DY, DY + HF);
        B("th_wall_front_a", XF, XF + 0.04f, cz - hb, dz0, DY, DY + HF);
        B("th_wall_front_b", XF, XF + 0.04f, dz1, cz + hb, DY, DY + HF);
        B("th_rail_front", X1 - 0.07f, X1 - 0.03f, Z0, Z1, DY, DY + RH);
        B("th_rail_mz", XF + 0.03f, X1 - 0.03f, Z0 + 0.03f, Z0 + 0.07f, DY, DY + RH);
        B("th_rail_pz_a", XF + 0.03f, lx - lw / 2 - 0.08f, Z1 - 0.07f, Z1 - 0.03f, DY, DY + RH);
        B("th_rail_pz_b", lx + lw / 2 + 0.08f, X1 - 0.03f, Z1 - 0.07f, Z1 - 0.03f, DY, DY + RH);
        B("th_trunk", tx - tr, tx + tr, tz - tr, tz + tr, G - 0.2f, DY + HF + 0.3f);
        foreach (Transform c in walk.transform) Object.DestroyImmediate(c.GetComponent<MeshRenderer>());

        // the cabin's bare bulb (film 11060/11102), night only: AtticFixtures joins the night layer in Daylight()
        var fx = root.transform.Find("AtticFixtures")?.gameObject ?? Child(root, "AtticFixtures");
        var l = new GameObject("TreehouseBulb").AddComponent<Light>(); l.transform.SetParent(fx.transform, false);
        l.transform.position = new Vector3(XF - 0.25f, DY + HF - 0.35f, -(cz + 0.1f)); l.type = LightType.Point; l.range = 8f;
        l.gameObject.AddComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalLightData>();
        l.lightUnit = UnityEngine.Rendering.LightUnit.Lumen; l.intensity = 600f; l.useColorTemperature = true; l.colorTemperature = 2700f; l.shadows = LightShadows.Soft;

        // the zipline
        var z = new GameObject("ZipLine").AddComponent<ZipLine>(); z.transform.SetParent(root.transform, false);
        z.window = W(R["window"]); z.trunk = W(R["trunk"]); z.sag = F(R["sag"]); z.dormerOut = Vector3.left; z.grade = G;
        z.kidSpeed = F(Rd["kid_speed"]); z.adultSpeed = F(Rd["adult_speed"]); z.easeIn = F(Rd["ease_in_m"]); z.easeOut = F(Rd["ease_out_m"]);
        z.kidHang = F(Rd["kid_eye_below_rope"]); z.adultHang = F(Rd["adult_eye_below_rope"]); z.attachRadius = F(Rd["attach_radius"]);
        float rz = Mathf.Lerp(F(R["window"][2]), F(R["trunk"][2]), Mathf.InverseLerp(F(R["window"][0]), F(R["trunk"][0]), X1));
        z.railPoint = new Vector3(X1 - 0.05f, DY + RH, -rz);
        z.landPoint = new Vector3(X1 - 0.07f - F(Rd["land_inside_rail"]) - 0.2f, DY + 0.02f, -rz); z.landYaw = -90f;   // facing the cabin door
        float lzf = F(L["foot"][1]), lzt = F(L["top"][1]), ytop = DY + 0.7f, f = (DY - 0.3f - G) / (ytop - G);
        z.ladderBase = new Vector3(lx, G + 0.02f, -(lzf + 0.4f));
        z.ladderHigh = new Vector3(lx, DY - 0.3f, -(lzf + (lzt - lzf) * f + 0.3f));
        z.ladderDeck = new Vector3(lx, DY + 0.02f, -(Z1 - 0.5f));
        z.trolley = trolley.transform; z.rider = riderG; z.ropeMat = rope;
        Debug.Log($"Treehouse: deck top {DY:F2} (grade {G}), deck x {X0:F2}..{X1:F2} z {Z0:F2}..{Z1:F2}; zipline {Vector3.Distance(z.window, z.trunk):F2} m, " +
                  $"{walk.transform.childCount} walk colliders");
    }
}
